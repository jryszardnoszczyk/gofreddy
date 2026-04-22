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
    re.compile(r"(?i)\b(?:bearer\s+)?eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}"),  # GitHub tokens (ghp_, ghs_, gho_, ghu_, ghr_)
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key IDs
    re.compile(r"\b(?:sk|pk|rk)_(?:test|live)_[A-Za-z0-9]{16,}"),  # Stripe keys
    re.compile(r"\b(?:postgres|postgresql|mongodb|mysql|redis)://[^\s:@]+:[^\s@]+@\S+"),  # db URLs with creds
    re.compile(r"(?i)\b[A-Za-z0-9+/=]{40,}\b"),
    re.compile(r"(?i)(api[_-]?key|secret|token)[=:\s\"]+[A-Za-z0-9_\-]{16,}"),
)


def scrub(text: str) -> str:
    """Replace every secret-pattern match in ``text`` with ``[redacted]``."""
    for pat in SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    return text
