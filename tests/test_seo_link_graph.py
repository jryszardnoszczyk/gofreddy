"""Unit tests for SiteLinkGraph builder."""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.geo.link_graph import SiteLinkGraph, build_site_link_graph


@dataclass(frozen=True)
class MockSitemapEntry:
    url: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: float | None = None


def _make_scrape_result(url: str, internal_links_html: str = ""):
    """Create a mock ScrapeResult with page content."""
    result = MagicMock()
    result.success = True
    result.page_content = MagicMock()
    result.page_content.raw_html = f"<html><body>{internal_links_html}</body></html>"
    return result


def _make_failed_result():
    result = MagicMock()
    result.success = False
    result.page_content = None
    return result


class TestSiteLinkGraph:
    """Tests for SiteLinkGraph dataclass."""

    def test_empty_graph(self):
        graph = SiteLinkGraph()
        assert graph.total_pages == 0
        assert graph.total_links == 0
        assert graph.orphan_urls == ()
        assert graph.hub_pages == ()

    def test_graph_with_data(self):
        graph = SiteLinkGraph(
            pages={"a": {"b", "c"}, "b": {"a"}},
            orphan_urls=("c",),
            hub_pages=("a",),
            total_pages=2,
            total_links=3,
        )
        assert graph.total_pages == 2
        assert graph.total_links == 3
        assert "c" in graph.orphan_urls


class TestBuildSiteLinkGraph:
    """Tests for build_site_link_graph()."""

    @pytest.mark.asyncio
    async def test_empty_entries(self):
        graph = await build_site_link_graph([], AsyncMock(), max_pages=10)
        assert graph.total_pages == 0

    @pytest.mark.asyncio
    async def test_sorts_by_priority(self):
        entries = [
            MockSitemapEntry(url="https://example.com/low", priority=0.1),
            MockSitemapEntry(url="https://example.com/high", priority=0.9),
            MockSitemapEntry(url="https://example.com/mid", priority=0.5),
        ]

        scraped_urls = []

        async def mock_scrape(url):
            scraped_urls.append(url)
            return _make_scrape_result(url, f'<a href="/page">Link</a>')

        graph = await build_site_link_graph(entries, mock_scrape, max_pages=2)
        # Should scrape high priority first
        assert len(scraped_urls) == 2
        assert scraped_urls[0] == "https://example.com/high"

    @pytest.mark.asyncio
    async def test_identifies_hub_pages(self):
        entries = [
            MockSitemapEntry(url="https://example.com/hub"),
            MockSitemapEntry(url="https://example.com/leaf"),
        ]

        async def mock_scrape(url):
            if "hub" in url:
                # Hub page with many outbound links
                links = ''.join(f'<a href="/page-{i}">Link</a>' for i in range(10))
                return _make_scrape_result(url, links)
            return _make_scrape_result(url, '<a href="/hub">Back</a>')

        graph = await build_site_link_graph(entries, mock_scrape)
        assert "https://example.com/hub" in graph.hub_pages

    @pytest.mark.asyncio
    async def test_max_pages_cap(self):
        entries = [MockSitemapEntry(url=f"https://example.com/{i}") for i in range(100)]

        call_count = 0

        async def mock_scrape(url):
            nonlocal call_count
            call_count += 1
            return _make_scrape_result(url)

        await build_site_link_graph(entries, mock_scrape, max_pages=5)
        assert call_count <= 5

    @pytest.mark.asyncio
    async def test_handles_scrape_failures(self):
        # Need >=70% success ratio to avoid GeoAuditError.
        # 3 OK + 1 fail = 75% success — above the MIN_SUCCESS_RATIO threshold.
        entries = [
            MockSitemapEntry(url="https://example.com/ok1"),
            MockSitemapEntry(url="https://example.com/ok2"),
            MockSitemapEntry(url="https://example.com/ok3"),
            MockSitemapEntry(url="https://example.com/fail"),
        ]

        async def mock_scrape(url):
            if "fail" in url:
                return _make_failed_result()
            return _make_scrape_result(url, '<a href="/link">Link</a>')

        graph = await build_site_link_graph(entries, mock_scrape)
        assert graph.total_pages >= 1
