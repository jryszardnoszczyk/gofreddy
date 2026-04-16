"""Internal link graph builder for hub-and-spoke analysis."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine
from urllib.parse import urlparse

from .extraction import extract_internal_links

logger = logging.getLogger(__name__)

# Limits
MAX_PAGES_DEFAULT = 50
SEMAPHORE_LIMIT = 10
PER_PAGE_TIMEOUT = 15.0
OVERALL_DEADLINE = 120.0
MIN_SUCCESS_RATIO = 0.7


@dataclass(frozen=True, slots=True)
class SiteLinkGraph:
    """Site-wide internal link structure built from sitemap + scraped pages."""

    pages: dict[str, set[str]] = field(default_factory=dict)
    orphan_urls: tuple[str, ...] = ()
    hub_pages: tuple[str, ...] = ()
    total_pages: int = 0
    total_links: int = 0
    # URL -> PageContent for pages successfully scraped during graph building.
    # Allows downstream enrichment to reuse content without re-scraping.
    page_contents: dict[str, "Any"] = field(default_factory=dict)


async def build_site_link_graph(
    sitemap_entries: list[Any],
    scraper_fn: Callable[[str], Coroutine[Any, Any, Any]],
    max_pages: int = MAX_PAGES_DEFAULT,
) -> SiteLinkGraph:
    """Scrape top N pages by sitemap priority and build link graph.

    Only scrapes top 50-100 pages (full-site crawl is impractical).
    Uses existing scrape_page() from src/geo/scraper.py.

    Args:
        sitemap_entries: List of SitemapEntry objects with url and priority fields.
        scraper_fn: Async callable that takes a URL string and returns a ScrapeResult.
        max_pages: Maximum pages to scrape (default 50).

    Returns:
        SiteLinkGraph with page adjacency, orphans, and hub pages.

    Raises:
        GeoAuditError: If <70% of pages succeed.
    """
    from .exceptions import GeoAuditError

    # Sort by priority descending, fall back to original order
    sorted_entries = sorted(
        sitemap_entries,
        key=lambda e: e.priority if e.priority is not None else 0.0,
        reverse=True,
    )[:max_pages]

    if not sorted_entries:
        return SiteLinkGraph()

    sitemap_urls = {e.url for e in sorted_entries}
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    deadline = time.monotonic() + OVERALL_DEADLINE

    # url -> set of internal URLs it links to (content-area only)
    pages: dict[str, set[str]] = {}
    # url -> PageContent for successfully scraped pages (for downstream reuse)
    scraped_contents: dict[str, Any] = {}
    succeeded = 0
    failed = 0

    async def _scrape_one(url: str) -> tuple[str, set[str], Any] | None:
        nonlocal succeeded, failed

        if time.monotonic() > deadline:
            return None

        async with semaphore:
            try:
                result = await asyncio.wait_for(
                    scraper_fn(url), timeout=PER_PAGE_TIMEOUT,
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.debug("link_graph_scrape_failed: url=%s error=%s", url, e)
                failed += 1
                return None

        # ScrapeResult has .success and .page_content
        if not result.success or result.page_content is None:
            failed += 1
            return None

        # Extract internal links from raw HTML
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.page_content.raw_html, "lxml")
            links = extract_internal_links(soup, url)
        except Exception:
            logger.debug("link_graph_extract_failed: url=%s", url)
            failed += 1
            return None

        # Only content-area links
        outbound = set()
        for link in links:
            if link.get("in_content_area"):
                href = link["href"]
                # Normalize relative URLs
                if href.startswith("/"):
                    parsed = urlparse(url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                outbound.add(href)

        succeeded += 1
        return url, outbound, result.page_content

    tasks = [asyncio.create_task(_scrape_one(entry.url)) for entry in sorted_entries]

    results: list[tuple[str, set[str], Any]] = []
    try:
        for coro in asyncio.as_completed(tasks):
            if time.monotonic() > deadline:
                break
            result = await coro
            if result is not None:
                results.append(result)
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    total_attempted = succeeded + failed
    if total_attempted > 0 and succeeded / total_attempted < MIN_SUCCESS_RATIO:
        # Build partial graph anyway but raise
        pass  # Continue to build, will raise after

    # Build adjacency map and collect page contents
    for url, outbound, pc in results:
        pages[url] = outbound
        scraped_contents[url] = pc

    # Find orphans: sitemap URLs with zero content-area inbound links from scraped pages
    all_inbound: set[str] = set()
    for outbound in pages.values():
        all_inbound.update(outbound)

    orphan_urls = tuple(
        url for url in sitemap_urls
        if url not in all_inbound and url in pages  # Only consider scraped pages
    )

    # Hub pages: top 10 by outbound link count
    sorted_by_outbound = sorted(
        pages.items(), key=lambda kv: len(kv[1]), reverse=True,
    )
    hub_pages = tuple(url for url, _ in sorted_by_outbound[:10])

    total_links = sum(len(outbound) for outbound in pages.values())

    graph = SiteLinkGraph(
        pages=pages,
        orphan_urls=orphan_urls,
        hub_pages=hub_pages,
        total_pages=len(pages),
        total_links=total_links,
        page_contents=scraped_contents,
    )

    if total_attempted > 0 and succeeded / total_attempted < MIN_SUCCESS_RATIO:
        raise GeoAuditError(
            "LINK_GRAPH_PARTIAL",
            f"Only {succeeded}/{total_attempted} pages scraped successfully (<70%)",
        )

    return graph
