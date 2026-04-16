"""Tests for sitemap parser."""

import gzip
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.geo.sitemap import SitemapEntry, SitemapInventory, SitemapParser


class TestSitemapEntry:
    def test_basic_entry(self):
        entry = SitemapEntry(url="https://example.com/page")
        assert entry.url == "https://example.com/page"
        assert entry.lastmod is None

    def test_full_entry(self):
        entry = SitemapEntry(
            url="https://example.com/page",
            lastmod="2026-01-15",
            changefreq="weekly",
            priority=0.8,
        )
        assert entry.priority == 0.8


class TestSitemapInventory:
    def test_empty_inventory(self):
        inv = SitemapInventory()
        assert len(inv.entries) == 0
        assert inv.sitemaps_parsed == 0


ROBOTS_TXT = """User-agent: *
Disallow: /admin/
Sitemap: https://example.com/sitemap.xml
"""

SIMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/page1</loc><lastmod>2026-01-01</lastmod><priority>0.8</priority></url>
  <url><loc>https://example.com/page2</loc></url>
  <url><loc>https://example.com/page3</loc><changefreq>weekly</changefreq></url>
</urlset>"""

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""

POSTS_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/blog/post1</loc></url>
  <url><loc>https://example.com/blog/post2</loc></url>
</urlset>"""

PAGES_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/about</loc></url>
</urlset>"""


def _mock_response(content: str | bytes, status_code: int = 200, content_type: str = "text/xml"):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    if isinstance(content, bytes):
        resp.content = content
        resp.text = content.decode("utf-8", errors="replace")
    else:
        resp.text = content
        resp.content = content.encode()
    resp.headers = {"content-type": content_type}
    return resp


class TestSitemapParser:
    @pytest.mark.asyncio
    async def test_simple_sitemap_from_robots(self):
        """Parse a simple sitemap discovered via robots.txt."""
        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response(ROBOTS_TXT, content_type="text/plain")
            if "sitemap.xml" in url:
                return _mock_response(SIMPLE_SITEMAP)
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 3
            assert inventory.entries[0].url == "https://example.com/page1"
            assert inventory.entries[0].lastmod == "2026-01-01"
            assert inventory.entries[0].priority == 0.8
            assert inventory.entries[1].url == "https://example.com/page2"
            assert inventory.sitemaps_parsed == 1

    @pytest.mark.asyncio
    async def test_sitemap_index_recursion(self):
        """Parse a sitemap index that references child sitemaps."""
        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response(ROBOTS_TXT.replace("sitemap.xml", "sitemap-index.xml"), content_type="text/plain")
            if "sitemap-index.xml" in url:
                return _mock_response(SITEMAP_INDEX)
            if "sitemap-posts.xml" in url:
                return _mock_response(POSTS_SITEMAP)
            if "sitemap-pages.xml" in url:
                return _mock_response(PAGES_SITEMAP)
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 3  # 2 posts + 1 page
            urls = {e.url for e in inventory.entries}
            assert "https://example.com/blog/post1" in urls
            assert "https://example.com/about" in urls
            assert inventory.sitemaps_parsed == 3  # index + 2 children

    @pytest.mark.asyncio
    async def test_fallback_to_sitemap_xml(self):
        """When robots.txt has no Sitemap directive, fall back to /sitemap.xml."""
        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response("User-agent: *\nDisallow: /admin/\n", content_type="text/plain")
            if url.endswith("/sitemap.xml"):
                return _mock_response(SIMPLE_SITEMAP)
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 3

    @pytest.mark.asyncio
    async def test_gzipped_sitemap(self):
        """Handle gzipped sitemap files."""
        gz_content = gzip.compress(SIMPLE_SITEMAP.encode())

        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response(
                    "Sitemap: https://example.com/sitemap.xml.gz\n",
                    content_type="text/plain",
                )
            if "sitemap.xml.gz" in url:
                return _mock_response(gz_content, content_type="application/x-gzip")
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 3

    @pytest.mark.asyncio
    async def test_http_error_recorded(self):
        """HTTP errors are recorded but don't crash the parser."""
        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response("", status_code=404)
            if "sitemap.xml" in url:
                return _mock_response("", status_code=500)
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 0
            assert len(inventory.errors) >= 1

    @pytest.mark.asyncio
    async def test_malformed_xml(self):
        """Malformed XML is recorded as error."""
        async def mock_get(url, **kwargs):
            if "robots.txt" in url:
                return _mock_response("Sitemap: https://example.com/sitemap.xml\n", content_type="text/plain")
            if "sitemap.xml" in url:
                return _mock_response("<not valid xml>><<<")
            return _mock_response("", status_code=404)

        with patch("src.geo.sitemap.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = mock_get
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            parser = SitemapParser()
            inventory = await parser.parse("https://example.com")

            assert len(inventory.entries) == 0
            assert any("XML" in e or "parse" in e.lower() for e in inventory.errors)
