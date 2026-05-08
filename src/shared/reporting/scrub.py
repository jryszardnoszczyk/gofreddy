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
- ``scrub(text)`` — returns ``text`` with every match replaced by
  ``[redacted]``. Idempotent on already-scrubbed input.
"""

from __future__ import annotations

import re

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # JWTs (incl. Bearer-prefixed)
    re.compile(r"(?i)\b(?:bearer\s+)?eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    # GitHub tokens (ghp_, ghs_, gho_, ghu_, ghr_)
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}"),
    # AWS access key IDs
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Stripe live/test secret + publishable + restricted keys
    re.compile(r"\b(?:sk|pk|rk)_(?:test|live)_[A-Za-z0-9]{16,}"),
    # Stripe webhook secrets (added per 2026-05-08 review)
    re.compile(r"\bwhsec_[A-Za-z0-9]{16,}"),
    # Anthropic API keys (sk-ant-* — 2026-05-08 review)
    re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}"),
    # OpenAI project keys + legacy key prefix (2026-05-08 review)
    re.compile(r"\bsk-proj-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
    # Slack tokens (xoxb / xoxa / xoxp / xoxr / xoxs / xoxe)
    re.compile(r"\bxox[abeprs]-[A-Za-z0-9-]{10,}"),
    # Google API keys (AIza..., 39 chars)
    re.compile(r"\bAIza[A-Za-z0-9_\-]{35}\b"),
    # PEM-encoded private keys (RSA / EC / OpenSSH / generic)
    re.compile(
        r"(?is)-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED |PGP )?PRIVATE KEY-----"
        r".*?-----END (?:RSA |EC |OPENSSH |DSA |ENCRYPTED |PGP )?PRIVATE KEY-----"
    ),
    # GCP service-account JSON's `private_key` field
    re.compile(r'(?i)"private_key"\s*:\s*"[^"]+"'),
    # DB URLs with embedded creds
    re.compile(
        r"\b(?:postgres|postgresql|mongodb|mysql|redis)://[^\s:@]+:[^\s@]+@\S+"
    ),
    # Header-shaped credentials (Authorization / Cookie / Set-Cookie /
    # X-Api-Key / password / client_secret) — captures opaque bearer
    # tokens that aren't JWT-shaped
    re.compile(
        r"(?im)^\s*(?:authorization|cookie|set-cookie|x-api-key|"
        r"client_secret|password)\s*[:=]\s*\S{8,}.*$"
    ),
    # Inline Bearer/Basic/Token headers anywhere in a line (broader than the
    # JWT-only pattern at the top — catches opaque session tokens).
    re.compile(r"(?i)\b(?:bearer|basic|token)\s+[A-Za-z0-9._\-+/=]{16,}"),
    # Coarse high-entropy base64 fallback (≥40 chars).
    re.compile(r"(?i)\b[A-Za-z0-9+/=]{40,}\b"),
    # `api_key=…` / `secret=…` / `token=…` assignments
    re.compile(r"(?i)(api[_-]?key|secret|token)[=:\s\"]+[A-Za-z0-9_\-]{16,}"),
)


def scrub(text: str) -> str:
    """Replace every secret-pattern match in ``text`` with ``[redacted]``."""
    for pat in SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text
