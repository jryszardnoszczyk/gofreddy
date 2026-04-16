"""Article post-processing: external link validation and YouTube embed resolution."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Security
_URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
LINK_TIMEOUT = 5.0
MAX_CONCURRENT_CHECKS = 10


async def validate_external_links(
    links: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Validate external links via async HEAD requests with SSRF protection.

    Filters out:
    - Dead links (non-2xx HEAD response)
    - SSRF-blocked URLs (private IPs, localhost)
    - Non-HTTPS URLs

    Args:
        links: Tuple of ExternalLink objects with .url attribute.

    Returns:
        Filtered tuple of valid ExternalLink objects.
    """
    from ..common.url_validation import resolve_and_validate

    if not links:
        return ()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

    async with httpx.AsyncClient(
        timeout=LINK_TIMEOUT, follow_redirects=False,
    ) as client:

        async def _check_one(link: Any) -> Any | None:
            url = link.url
            if not url.startswith("https://"):
                return None

            # SSRF check
            try:
                await resolve_and_validate(url)
            except (ValueError, Exception):
                logger.debug("external_link_ssrf_blocked: url=%s", url)
                return None

            # HEAD request — do NOT follow redirects (per project convention)
            async with semaphore:
                try:
                    resp = await client.head(url)
                    if 200 <= resp.status_code < 300:
                        return link
                    logger.debug(
                        "external_link_dead: url=%s status=%d", url, resp.status_code,
                    )
                    return None
                except (httpx.HTTPError, Exception):
                    logger.debug("external_link_error: url=%s", url)
                    return None

        tasks = [_check_one(link) for link in links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    valid = [r for r in results if r is not None and not isinstance(r, Exception)]
    return tuple(valid)


async def resolve_youtube_embeds(
    embeds: tuple[Any, ...],
) -> list[dict[str, Any]]:
    """Resolve YouTube embed search queries to actual video URLs via yt-dlp.

    Uses extract_flat for search-only (faster, skips per-video extraction).
    Filters by duration presence to exclude channels.
    Sanitizes search queries to prevent SSRF.

    Args:
        embeds: Tuple of YouTubeEmbed objects with .search_query attribute.

    Returns:
        List of dicts: {search_query, video_url, video_id, title} or None per embed.
    """
    if not embeds:
        return []

    async def _search_one(embed: Any) -> dict[str, Any] | None:
        query = embed.search_query
        # Reject queries containing URL patterns (SSRF prevention)
        if _URL_PATTERN.search(query):
            logger.warning("youtube_search_ssrf_blocked: query=%s", query)
            return None

        try:
            import yt_dlp

            ydl_opts: dict[str, Any] = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "default_search": "ytsearch3",
            }

            def _extract() -> dict[str, Any] | None:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                    result: dict[str, Any] | None = ydl.extract_info(f"ytsearch3:{query}", download=False)  # type: ignore[assignment]
                    if not result or "entries" not in result:
                        return None

                    # Filter entries with duration (excludes channels)
                    entries: list[Any] = result["entries"]
                    videos = [
                        e for e in entries
                        if e and e.get("duration") is not None
                    ]
                    if not videos:
                        return None

                    # Pick top result by view count
                    best = max(
                        videos,
                        key=lambda v: v.get("view_count", 0) or 0,
                    )
                    return {
                        "search_query": query,
                        "video_url": best.get("url") or f"https://www.youtube.com/watch?v={best.get('id', '')}",
                        "video_id": best.get("id", ""),
                        "title": best.get("title", ""),
                    }

            return await asyncio.to_thread(_extract)
        except Exception as e:
            logger.debug("youtube_search_failed: query=%s error=%s", query, e)
            return None

    raw_results = await asyncio.gather(
        *[_search_one(embed) for embed in embeds],
        return_exceptions=True,
    )

    valid: list[dict[str, Any]] = [
        r for r in raw_results  # type: ignore[misc]
        if isinstance(r, dict)
    ]
    return valid
