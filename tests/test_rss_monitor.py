"""Tests for RSS/Atom feed monitor."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from src.publishing.exceptions import PublishError
from src.publishing.rss_monitor import RSSMonitor

_SAMPLE_RSS = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Blog</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/first-post</link>
      <description>A test post summary</description>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

_SAMPLE_ATOM = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Blog</title>
  <entry>
    <title>Atom Post</title>
    <link href="https://example.com/atom-post"/>
    <summary>An atom post summary</summary>
    <updated>2024-01-01T00:00:00Z</updated>
  </entry>
</feed>
"""

_FEED_URL = "https://example.com/feed.xml"


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.mark.asyncio
@pytest.mark.mock_required
@respx.mock
async def test_parse_rss_feed(mock_repo: AsyncMock):
    """Mock httpx GET to return sample RSS XML and verify FeedEntry fields."""
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, text=_SAMPLE_RSS)
    )

    async with httpx.AsyncClient() as client:
        monitor = RSSMonitor(http=client, repository=mock_repo)
        with patch(
            "src.common.url_validation.resolve_and_validate",
            new_callable=AsyncMock,
        ):
            entries = await monitor.parse_feed(_FEED_URL)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "First Post"
    assert entry.url == "https://example.com/first-post"
    assert entry.summary == "A test post summary"
    assert entry.published_at is not None
    assert entry.published_at.year == 2024


@pytest.mark.asyncio
@pytest.mark.mock_required
@respx.mock
async def test_parse_atom_feed(mock_repo: AsyncMock):
    """Mock httpx GET to return sample Atom XML and verify parsing."""
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, text=_SAMPLE_ATOM)
    )

    async with httpx.AsyncClient() as client:
        monitor = RSSMonitor(http=client, repository=mock_repo)
        with patch(
            "src.common.url_validation.resolve_and_validate",
            new_callable=AsyncMock,
        ):
            entries = await monitor.parse_feed(_FEED_URL)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "Atom Post"
    assert entry.url == "https://example.com/atom-post"
    assert entry.summary == "An atom post summary"


@pytest.mark.asyncio
@pytest.mark.mock_required
@respx.mock
async def test_feed_size_limit(mock_repo: AsyncMock):
    """Verify PublishError when feed content exceeds 1MB."""
    # Create a response whose content exceeds the 1MB limit
    oversized_body = "x" * (1_048_576 + 1)
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, text=oversized_body)
    )

    async with httpx.AsyncClient() as client:
        monitor = RSSMonitor(http=client, repository=mock_repo)
        with patch(
            "src.common.url_validation.resolve_and_validate",
            new_callable=AsyncMock,
        ):
            with pytest.raises(PublishError, match="1MB size limit"):
                await monitor.parse_feed(_FEED_URL)
