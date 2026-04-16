"""Per-API query sanitization for monitoring adapters."""

import re

MAX_QUERY_LENGTH = 512


class QueryValidationError(ValueError):
    """Raised when query fails shared validation."""


def _shared_validate(query: str) -> str:
    """Shared validation: length, null bytes, control chars."""
    if not query or not query.strip():
        raise QueryValidationError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise QueryValidationError(f"Query exceeds {MAX_QUERY_LENGTH} characters")
    if "\x00" in query:
        raise QueryValidationError("Query contains null bytes")
    # Strip control chars except whitespace
    cleaned = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    return cleaned.strip()


def sanitize_for_newsdata(query: str) -> str:
    """NewsData.io: strip control chars, enforce 256 char limit, escape operators."""
    cleaned = _shared_validate(query)
    if len(cleaned) > 256:
        cleaned = cleaned[:256]
    # Escape NewsData boolean operators that users might accidentally type
    cleaned = cleaned.replace(" AND ", " ").replace(" OR ", " ").replace(" NOT ", " ")
    return cleaned


def sanitize_for_xpoz(query: str) -> str:
    """Xpoz SDK: strip control chars, pass through (SDK handles escaping)."""
    return _shared_validate(query)


def sanitize_for_apify(query: str) -> str:
    """Apify scrapers: strip control chars, pass through."""
    return _shared_validate(query)


# Regex to extract first quoted term from boolean query
_QUOTED_RE = re.compile(r'"([^"]+)"')


def sanitize_for_trustpilot(query: str) -> str:
    """Trustpilot: extract domain or brand slug from boolean query.

    Trustpilot URLs follow ``/review/{domain_or_slug}``.
    Extracts the first quoted term (or full query if no quotes),
    lowercases, strips non-alphanumeric chars (except dots/hyphens).
    """
    cleaned = _shared_validate(query)
    # Extract first quoted term if present
    match = _QUOTED_RE.search(cleaned)
    term = match.group(1) if match else cleaned
    # Strip boolean operators
    for op in (" OR ", " AND ", " NOT "):
        term = term.split(op)[0]
    term = term.strip().lower()
    # If it looks like a domain (has dot), keep as-is
    if "." in term:
        return term
    # Otherwise: brand slug — strip everything except alphanumeric and hyphens
    slug = re.sub(r"[^a-z0-9-]", "", term)
    return slug or cleaned.lower()
