"""Citation verification primitives (AE-3 / TD-44).

article_engine fires `verify_citation` post-generation on every claim
with a URL reference. The verifier confirms the URL's content
substantiates the claim; failures (404 / paywalled / JS-heavy) mark
the variant `citation_verification_degraded` for human review.

The verifier accepts a dependency-injected `call_claude` callable so
the contract is testable without binding to a specific SDK or CLI
subprocess shape — production wiring lands in U18 alongside the
operator's claude invocation pattern.
"""

from src.verification.citation_cache import CitationCache
from src.verification.citation_verifier import (
    CitationFetchError,
    CitationVerification,
    verify_citation,
)

__all__ = [
    "CitationCache",
    "CitationFetchError",
    "CitationVerification",
    "verify_citation",
]
