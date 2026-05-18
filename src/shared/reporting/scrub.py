"""Secret-redaction primitives for outbound reports.

Lifted verbatim from ``harness/review.py`` (the only pre-promotion home).
The harness regex set was the stronger of the two candidate locations;
``autoresearch/report_base.py`` did not previously ship a ``scrub`` —
its outputs were treated as trusted. With ``review.md`` / ``pr-body.md``
escaping the harness boundary, the harness set is the canonical one.

Patterns target high-confidence secret shapes only — JWTs, vendor token
prefixes (GitHub, AWS, Stripe), DB-URLs with embedded credentials, plus
two coarse fallbacks for high-entropy base64 strings and ``api_key=…``
assignments. False-positive policy: punt until a real one shows up; the
``[redacted]`` placeholder is loud enough to catch in review.

Public API:
- ``SECRET_PATTERNS`` — tuple of compiled ``re.Pattern`` objects.
- ``NAMED_SECRET_PATTERNS`` — tuple of ``(name, compiled re.Pattern)`` pairs;
  source of truth. ``SECRET_PATTERNS`` is derived from this for backward
  compatibility with consumers that iterate patterns directly.
- ``scrub(text)`` — returns ``text`` with every match replaced by
  ``[redacted]``. Idempotent on already-scrubbed input. Preserves the
  legacy ``[redacted]`` marker so existing callers don't break.
- ``scrub_with_records(text)`` — returns ``(redacted_text, records)`` where
  ``records`` is a list of ``ScrubRecord(kind, original_length)``. The
  redacted text uses per-pattern ``<redacted:KIND>`` markers (richer than
  the legacy ``[redacted]``) so the portal redaction layer can surface
  what was caught without leaking the original value.

The portal redaction layer (``src/portal/redaction.py``) uses
``scrub_with_records`` so each ``RedactionRecord`` it logs carries the
pattern kind for cardinality without ever storing the original value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# (name, pattern) — name appears in <redacted:NAME> markers emitted by
# scrub_with_records and in ScrubRecord.kind. Order matters: earlier
# patterns replace first, so put high-specificity patterns ahead of the
# coarse base64 fallback.
NAMED_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # JWTs (incl. Bearer-prefixed). Catches Supabase service_role keys
    # too — they ARE JWTs (eyJ... three-part). Verified by test.
    ("jwt", re.compile(r"(?i)\b(?:bearer\s+)?eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+")),
    # GitHub tokens (ghp_, ghs_, gho_, ghu_, ghr_)
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}")),
    # AWS access key IDs
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # Stripe live/test secret + publishable + restricted keys
    ("stripe_key", re.compile(r"\b(?:sk|pk|rk)_(?:test|live)_[A-Za-z0-9]{16,}")),
    # Stripe webhook secrets (added per 2026-05-08 review)
    ("stripe_webhook", re.compile(r"\bwhsec_[A-Za-z0-9]{16,}")),
    # Anthropic API keys (sk-ant-* — 2026-05-08 review)
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}")),
    # OpenAI project keys + legacy key prefix (2026-05-08 review)
    ("openai_project_key", re.compile(r"\bsk-proj-[A-Za-z0-9\-_]{20,}")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    # Slack tokens (xoxb / xoxa / xoxp / xoxr / xoxs / xoxe)
    ("slack_token", re.compile(r"\bxox[abeprs]-[A-Za-z0-9-]{10,}")),
    # Google API keys (AIza..., 39 chars)
    ("google_api_key", re.compile(r"\bAIza[A-Za-z0-9_\-]{35}\b")),
    # PEM-encoded private keys (RSA / EC / OpenSSH / generic)
    (
        "pem_private_key",
        re.compile(
            r"(?is)-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED |PGP )?PRIVATE KEY-----"
            r".*?-----END (?:RSA |EC |OPENSSH |DSA |ENCRYPTED |PGP )?PRIVATE KEY-----"
        ),
    ),
    # GCP service-account JSON's `private_key` field
    ("gcp_private_key", re.compile(r'(?i)"private_key"\s*:\s*"[^"]+"')),
    # DB URLs with embedded creds (covers DATABASE_URL=postgresql://user:pass@host/db)
    (
        "db_url",
        re.compile(
            r"\b(?:postgres|postgresql|mongodb|mysql|redis)://[^\s:@]+:[^\s@]+@\S+"
        ),
    ),
    # password=<...> literal (NEW — Unit 5). Placed BEFORE the header-shaped
    # regex so inline `password=hunter2` matches the more specific shape.
    # Catches password=, PASSWORD=, password : value, etc. Length floor of 4
    # rejects e.g. `password=` empty assignments without secrets.
    (
        "password",
        re.compile(r"(?i)\bpassword\s*[=:]\s*\S{4,}"),
    ),
    # Env-var assignments like ANYTHING_API_KEY=... or *_KEY=... (NEW — Unit 5).
    # Matches OPENAI_API_KEY=sk-proj-abc123, SUPABASE_KEY=xxx, etc. Length
    # floor of 8 on value rejects `KEY=short`. Anchored so it captures the
    # whole assignment including the value.
    (
        "env_var_key",
        re.compile(r"\b[A-Z][A-Z0-9_]*_(?:API_)?KEY\s*=\s*\S{8,}"),
    ),
    # Header-shaped credentials (Authorization / Cookie / Set-Cookie /
    # X-Api-Key / password / client_secret) — captures opaque bearer
    # tokens that aren't JWT-shaped
    (
        "header_credential",
        re.compile(
            r"(?im)^\s*(?:authorization|cookie|set-cookie|x-api-key|"
            r"client_secret|password)\s*[:=]\s*\S{8,}.*$"
        ),
    ),
    # Inline Bearer/Basic/Token headers anywhere in a line (broader than the
    # JWT-only pattern at the top — catches opaque session tokens).
    ("inline_bearer", re.compile(r"(?i)\b(?:bearer|basic|token)\s+[A-Za-z0-9._\-+/=]{16,}")),
    # Coarse high-entropy base64 fallback (≥40 chars).
    ("base64_blob", re.compile(r"(?i)\b[A-Za-z0-9+/=]{40,}\b")),
    # `api_key=…` / `secret=…` / `token=…` assignments
    ("api_key", re.compile(r"(?i)(api[_-]?key|secret|token)[=:\s\"]+[A-Za-z0-9_\-]{16,}")),
)

# Backward-compat: existing callers iterate SECRET_PATTERNS as a tuple of
# compiled patterns. Derive it from the named tuple so the two never drift.
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = tuple(p for _, p in NAMED_SECRET_PATTERNS)


@dataclass(frozen=True)
class ScrubRecord:
    """One redaction event surfaced by ``scrub_with_records``.

    Carries the pattern ``kind`` (matches ``<redacted:KIND>`` marker in the
    returned text) and ``original_length`` — never the original value, for
    audit-log cardinality without leaking the secret content itself.
    """

    kind: str
    original_length: int


def scrub(text: str) -> str:
    """Replace every secret-pattern match in ``text`` with ``[redacted]``.

    Legacy API preserved verbatim — used by report_base.py (HTML+PDF reports)
    and harness/review.py (pr-body.md scrubbing). New portal code should use
    ``scrub_with_records`` instead.
    """
    for _, pat in NAMED_SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text


def scrub_with_records(text: str) -> tuple[str, list[ScrubRecord]]:
    """Replace every secret-pattern match with ``<redacted:KIND>`` and surface a record per match.

    Returns ``(redacted_text, records)``. Each record carries the pattern
    kind and the length of the original match (for cardinality), never the
    original value. Idempotent on already-scrubbed input — the marker
    ``<redacted:...>`` is not itself matched by any pattern.

    Markers use ``<redacted:KIND>`` (not the legacy ``[redacted]``) so the
    portal layer can distinguish redacted regions from the agent's own
    literal usage of the string ``[redacted]`` in transcripts.
    """
    records: list[ScrubRecord] = []
    for name, pat in NAMED_SECRET_PATTERNS:
        marker = f"<redacted:{name}>"

        def _replace(match: re.Match[str], _name: str = name) -> str:
            records.append(ScrubRecord(kind=_name, original_length=len(match.group(0))))
            return marker

        text = pat.sub(_replace, text)
    return text, records
