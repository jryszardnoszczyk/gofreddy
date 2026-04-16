"""SCRAPE step orchestrator for GEO audit pipeline."""

import logging
import time

import httpx

from ..common.url_validation import resolve_and_validate
from .extraction import extract_page_content
from .fetcher import fetch_page_for_audit
from .models import ScrapeResult

logger = logging.getLogger(__name__)


async def scrape_page(url: str) -> ScrapeResult:
    """SCRAPE step: Fetch and extract content from a URL.

    Flow:
        1. Validate URL (SSRF protection via Freddy's url_validation)
        2. Fetch page (httpx with JS detection heuristics)
        3. Extract structured content
        4. Return ScrapeResult
    """
    start_time = time.monotonic()

    # Step 1: Validate URL using Freddy's SSRF protection
    try:
        await resolve_and_validate(url)
    except ValueError as e:
        logger.warning(
            "scrape_url_validation_failed",
            extra={"url": url, "error": str(e)},
        )
        return ScrapeResult(
            success=False,
            error_code="BLOCKED",
            error_message=_user_friendly_error("BLOCKED"),
        )

    # Step 2: Fetch page
    try:
        fetch_result = await fetch_page_for_audit(url)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
        logger.warning("scrape_network_error", extra={"url": url, "error": type(e).__name__})
        return ScrapeResult(
            success=False,
            error_code="FETCH_FAILED",
            error_message=_user_friendly_error("FETCH_FAILED"),
        )
    except httpx.HTTPStatusError as e:
        logger.warning(
            "scrape_http_error",
            extra={"url": url, "status": e.response.status_code},
        )
        return ScrapeResult(
            success=False,
            error_code="SERVER_ERROR",
            error_message=_user_friendly_error("SERVER_ERROR", e.response.status_code),
        )
    except ValueError as e:
        # SSRF blocked during redirect chain
        logger.warning("scrape_blocked", extra={"url": url, "error": str(e)})
        return ScrapeResult(
            success=False,
            error_code="BLOCKED",
            error_message=_user_friendly_error("BLOCKED"),
        )

    # Step 3: Extract structured content
    fetch_duration_ms = int((time.monotonic() - start_time) * 1000)

    try:
        page_content = extract_page_content(
            html=fetch_result.content,
            url=url,
            final_url=fetch_result.final_url,
            js_rendered=fetch_result.js_rendered,
            status_code=fetch_result.status_code,
            fetch_duration_ms=fetch_duration_ms,
        )
    except Exception:
        logger.exception("scrape_extraction_failed", extra={"url": url})
        return ScrapeResult(
            success=False,
            error_code="PARSE_ERROR",
            error_message=_user_friendly_error("PARSE_ERROR"),
        )

    logger.info(
        "scrape_success",
        extra={
            "url": url,
            "final_url": page_content.final_url,
            "word_count": page_content.word_count,
            "js_rendered": page_content.js_rendered,
            "duration_ms": fetch_duration_ms,
            "schema_types": page_content.schema_types,
        },
    )

    return ScrapeResult(success=True, page_content=page_content)


def _user_friendly_error(code: str, detail: str | int | None = None) -> str:
    messages = {
        "FETCH_FAILED": "Could not fetch the page. Check if the URL is correct and the site is online.",
        "BLOCKED": "This URL cannot be accessed for security reasons. Only public HTTPS URLs are allowed.",
        "PARSE_ERROR": "Could not extract content from the page.",
        "UNAVAILABLE": "Our service is temporarily busy. Please try again in a moment.",
    }

    if code == "SERVER_ERROR" and isinstance(detail, int):
        if detail in (401, 403):
            return "Page requires authentication or is blocked. Make sure the page is publicly accessible."
        if detail == 404:
            return "Page not found. Check if the URL is correct."
        if detail == 429:
            return "Server is rate limiting requests. Try again later."
        if detail >= 500:
            return "The website is having issues. Try again later."
        return f"Server returned error {detail}."

    return messages.get(code, "An unexpected error occurred.")
