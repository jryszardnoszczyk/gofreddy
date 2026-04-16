"""Competitive intelligence utilities."""

import re

_DOMAIN_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    r"\.[a-zA-Z]{2,}$"
)


def normalize_domain(domain: str) -> str:
    """Normalize and validate a domain string.

    Strips protocol, www prefix, path segments, and query strings.
    Raises ValueError for invalid domain formats.
    """
    domain = domain.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    # Strip path segments and query strings
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    domain = domain.rstrip("/")
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f"Invalid domain format: {domain}")
    return domain
