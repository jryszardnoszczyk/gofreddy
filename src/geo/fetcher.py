"""GEO Audit Pipeline page fetcher.

Implements httpx-only fetching strategy with JS detection heuristics.
Browserless/Playwright integration deferred to V1.5.
"""

import logging
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..common.url_validation import resolve_and_validate

logger = logging.getLogger(__name__)

# Max response body size to prevent memory exhaustion from malicious servers
MAX_RESPONSE_BYTES = 5_242_880  # 5MB


@dataclass(slots=True, frozen=True)
class FetchResult:
    """Result of page fetch attempt."""

    content: str
    js_rendered: bool
    status_code: int
    final_url: str


# Module-level client with connection limits
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create connection-pooled HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            follow_redirects=False,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
            headers={
                "User-Agent": "ClairBot/1.0 (GEO Audit; compatible)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )
    return _http_client


async def close_http_client() -> None:
    """Close the HTTP client (for cleanup)."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def _is_js_dependent(html: str) -> bool:
    """Detect if page requires JavaScript rendering."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")

    if not body:
        return True

    text_content = body.get_text(strip=True)

    if len(text_content) < 100:
        return True

    # Check semantic main-content elements
    main_selectors = [
        body.find("main"),
        body.find("article"),
        body.find(attrs={"role": "main"}),
    ]
    main_elements = [el for el in main_selectors if el is not None]

    if main_elements:
        main_text = main_elements[0].get_text(strip=True)
        if len(main_text) < 50 and len(text_content) > 100:
            return True

    # Check for <noscript> with substantial content
    noscript = body.find("noscript")
    if noscript and len(noscript.get_text(strip=True)) > 200:
        return True

    # Check for SPA patterns
    SPA_ROOTS = {"root", "app", "__next", "___gatsby", "svelte", "nuxt"}
    for root_id in SPA_ROOTS:
        root_elem = body.find(id=root_id)
        if root_elem:
            root_text = root_elem.get_text(strip=True)
            outside_text = len(text_content) - len(root_text)
            if len(root_text) < 100 and outside_text < 50:
                return True

    return False


async def _fetch_with_redirect_validation(
    client: httpx.AsyncClient,
    initial_url: str,
    max_redirects: int = 5,
) -> tuple[str, str]:
    """Fetch URL with manual redirect validation via Freddy's url_validation.

    Returns: (content, final_url)
    Raises: ValueError if redirect target is blocked
    """
    current_url = initial_url
    redirect_count = 0

    while redirect_count < max_redirects:
        response = await client.get(current_url, follow_redirects=False)

        if response.status_code not in (301, 302, 303, 307, 308):
            response.raise_for_status()
            # Enforce size limit to prevent memory exhaustion
            content = response.text
            if len(content.encode("utf-8", errors="replace")) > MAX_RESPONSE_BYTES:
                content = content[:MAX_RESPONSE_BYTES]
            return content, current_url

        location = response.headers.get("location")
        if not location:
            raise ValueError("Redirect without Location header")

        # Handle relative redirects
        if not location.startswith(("http://", "https://")):
            location = urljoin(current_url, location)

        # Validate redirect target using Freddy's SSRF protection
        await resolve_and_validate(location)

        current_url = location
        redirect_count += 1

    raise ValueError(f"Exceeded {max_redirects} redirects")


async def fetch_page_for_audit(url: str) -> FetchResult:
    """Fetch page content with SSRF protection.

    Strategy:
    1. Fetch via httpx with redirect validation
    2. Check if JS-dependent (heuristic only — no Browserless in V1)
    3. Return content with js_rendered flag for DETECT step awareness
    """
    client = get_http_client()

    httpx_content, final_url = await _fetch_with_redirect_validation(client, url)

    js_dependent = _is_js_dependent(httpx_content)

    if js_dependent:
        logger.info(
            "geo_js_dependent_page",
            extra={"url": url, "note": "Browserless deferred to V1.5, using httpx content"},
        )

    return FetchResult(
        content=httpx_content,
        js_rendered=False,  # V1: no JS rendering
        status_code=200,
        final_url=final_url,
    )
