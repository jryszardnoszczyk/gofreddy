"""Citation verification (AE-3 / TD-44).

`verify_citation(claim, url, *, fetch_url, call_claude, cache)`
returns a `CitationVerification` answering "does the URL's content
substantiate the claim?". Used by article_engine post-generation on
every claim with a `[N]` reference + URL.

Failure modes (404 / paywalled / JS-heavy / network timeout / claude
parse failure) return a degraded result with `degraded=True` instead
of raising — the lane's session_eval can flag the variant for human
review without failing the entire run on transient errors.

Per JR's U13 decision (2026-05-19, "build now"): the verifier ships
in v1 with a dependency-injected `call_claude` callable, since the
codebase doesn't depend on the Anthropic SDK directly (the existing
pattern subprocesses the claude CLI). U18 wires the production
backend when Klinika + DWF onboard. v1 ships the contract + cache +
URL fetch + extraction; production verification fires when U18 wires
the call_claude default.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Callable

from src.verification.citation_cache import CitationCache

logger = logging.getLogger(__name__)


# Cap on extracted body text passed to the claude prompt — keeps
# per-citation token cost bounded even for very long source URLs.
_MAX_EXTRACTED_CHARS = 12_000


class CitationFetchError(Exception):
    """Raised when URL fetch fails in a way the caller MUST handle
    (e.g., malformed URL). 404 / timeout / paywalled return a
    `degraded=True` result instead, since those are operationally
    common."""


@dataclass(frozen=True)
class CitationVerification:
    """Outcome of one (claim, url) verification call."""

    verified: bool
    confidence: float  # 0.0–1.0
    rationale: str
    degraded: bool = False
    """True when the verifier couldn't complete the check (404,
    paywall, parse failure). The lane should flag these for human
    review instead of treating `verified=False` as a hard fail."""


def _default_fetch_url(url: str) -> str:
    """Default URL fetcher: synchronous httpx GET with a 10s timeout.

    Returns the response body as text on 2xx. Raises on connection
    error or non-2xx; the verifier wraps in degraded-result.
    """
    import httpx

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        response = client.get(
            url,
            headers={
                # Some publishers gate on User-Agent; mimic a reasonable
                # browser shape rather than the default httpx string.
                "User-Agent": (
                    "Mozilla/5.0 (compatible; gofreddy-citation-verifier; "
                    "+https://gofreddy.ai/about)"
                ),
            },
        )
        response.raise_for_status()
        return response.text


def _strip_html(raw: str) -> str:
    """Strip script/style/noscript and return visible text. Falls back
    through bs4 parsers like the source-material loader."""
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(raw, "lxml")
    except Exception:
        soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n").strip()


def _build_verifier_prompt(claim: str, url: str, body_text: str) -> str:
    """Compose the claude/opus prompt. The verifier answers with a
    JSON object the caller parses; instructions force JSON-only
    output so parsing is deterministic."""
    return (
        "You are a citation verifier. Given a CLAIM and the page content "
        "at a URL, answer ONLY in valid JSON whether the page's content "
        "substantiates the claim.\n\n"
        f"CLAIM: {claim}\n\n"
        f"URL: {url}\n\n"
        f"PAGE CONTENT (truncated to {_MAX_EXTRACTED_CHARS} chars):\n"
        f"---\n{body_text[:_MAX_EXTRACTED_CHARS]}\n---\n\n"
        "Respond with this exact JSON shape and nothing else:\n"
        '{"verified": <bool>, "confidence": <float 0..1>, "rationale": '
        '"<one-sentence explanation>"}\n\n'
        "Set verified=true ONLY when the page directly supports the claim. "
        "Indirect support (page mentions a related topic but not the "
        "specific claim) is verified=false. Confidence reflects how "
        "explicit the support is."
    )


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_claude_response(raw: str) -> dict:
    """Extract the first JSON object from claude's response. Claude
    sometimes wraps JSON in markdown fences (```json ... ```) or
    prefixes with explanatory prose; regex-extract the object so we
    tolerate both."""
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        raise ValueError(f"no JSON object found in claude response: {raw[:200]!r}")
    return json.loads(match.group(0))


def verify_citation(
    claim: str,
    url: str,
    *,
    fetch_url: Callable[[str], str] | None = None,
    call_claude: Callable[[str], str] | None = None,
    cache: CitationCache | None = None,
) -> CitationVerification:
    """Verify whether `url` substantiates `claim`.

    Args:
        claim: the text being cited.
        url: the URL it cites.
        fetch_url: callable returning the URL body as text. Defaults
            to a synchronous httpx GET with browser-like UA + 10s
            timeout + redirect-following.
        call_claude: callable taking a prompt and returning claude's
            text response. REQUIRED — no default until U18 wires the
            production backend. Tests inject a fake.
        cache: optional `CitationCache`. When provided, cache hits
            short-circuit the URL fetch + claude call.

    Returns:
        `CitationVerification` with `verified` / `confidence` /
        `rationale` / `degraded`.

    Failure handling:
        - URL fetch failure (network / 4xx / 5xx) → degraded result.
        - HTML strip failure → degraded result.
        - claude call exception → degraded result.
        - claude response parse failure → degraded result.

    `CitationFetchError` is reserved for malformed inputs the caller
    must fix (e.g., empty URL). Operational failures are degraded,
    not raised.
    """
    if not claim or not claim.strip():
        raise CitationFetchError("claim must be non-empty")
    if not url or not url.strip():
        raise CitationFetchError("url must be non-empty")
    if call_claude is None:
        raise CitationFetchError(
            "call_claude is required — pass a callable that takes a prompt "
            "string and returns claude's text response. Until U18 wires the "
            "default backend, the article_engine lane that triggers "
            "verification must inject one."
        )

    if cache is not None:
        cached = cache.get(claim, url)
        if cached is not None:
            return CitationVerification(
                verified=bool(cached.get("verified", False)),
                confidence=float(cached.get("confidence", 0.0)),
                rationale=str(cached.get("rationale", "")),
                degraded=bool(cached.get("degraded", False)),
            )

    result = _compute_verification(claim, url, fetch_url, call_claude)
    if cache is not None:
        # Cache degraded results too — operators clear with `--fresh`
        # when a 404'd publisher restores the URL. Re-fetching every
        # call burns claude tokens + bandwidth on permanently dead
        # references.
        cache.set(claim, url, {
            "verified": result.verified,
            "confidence": result.confidence,
            "rationale": result.rationale,
            "degraded": result.degraded,
        })
    return result


def _compute_verification(
    claim: str,
    url: str,
    fetch_url: Callable[[str], str] | None,
    call_claude: Callable[[str], str],
) -> CitationVerification:
    """Inner: pure compute, no cache. Splits out so the caching layer
    can wrap a single return path uniformly."""
    fetch_impl = fetch_url or _default_fetch_url
    try:
        raw_html = fetch_impl(url)
    except Exception as exc:
        logger.warning(
            "citation_verifier: URL fetch failed for %s (%s); returning degraded",
            url, exc,
        )
        return CitationVerification(
            verified=False, confidence=0.0,
            rationale=f"URL fetch failed: {exc}",
            degraded=True,
        )

    try:
        body_text = _strip_html(raw_html)
    except Exception as exc:
        logger.warning(
            "citation_verifier: HTML strip failed for %s (%s); returning degraded",
            url, exc,
        )
        return CitationVerification(
            verified=False, confidence=0.0,
            rationale=f"HTML parse failed: {exc}",
            degraded=True,
        )

    prompt = _build_verifier_prompt(claim, url, body_text)
    try:
        raw_response = call_claude(prompt)
    except Exception as exc:
        logger.warning(
            "citation_verifier: claude call failed for %s (%s); returning degraded",
            url, exc,
        )
        return CitationVerification(
            verified=False, confidence=0.0,
            rationale=f"claude call failed: {exc}",
            degraded=True,
        )

    try:
        parsed = _parse_claude_response(raw_response)
        return CitationVerification(
            verified=bool(parsed.get("verified", False)),
            confidence=float(parsed.get("confidence", 0.0)),
            rationale=str(parsed.get("rationale", "")),
            degraded=False,
        )
    except (ValueError, KeyError, TypeError) as exc:
        logger.warning(
            "citation_verifier: claude response unparseable for %s (%s); "
            "returning degraded",
            url, exc,
        )
        return CitationVerification(
            verified=False, confidence=0.0,
            rationale=f"claude response unparseable: {exc}",
            degraded=True,
        )
