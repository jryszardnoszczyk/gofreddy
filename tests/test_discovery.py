"""Tests for discover_mentions fan-out function."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.monitoring.discovery import discover_mentions
from src.monitoring.models import DataSource, RawMention


def _make_adapter(mentions=None, error=None):
    """Create a mock adapter that returns mentions or raises."""
    adapter = AsyncMock()
    if error:
        adapter.fetch_mentions = AsyncMock(side_effect=error)
    else:
        adapter.fetch_mentions = AsyncMock(return_value=(mentions or [], None))
    return adapter


def _make_mention(source, source_id="1", published_at=None):
    return RawMention(
        source=source,
        source_id=source_id,
        content="test content",
        published_at=published_at or datetime.now(timezone.utc),
    )


class TestDiscoverMentions:
    @pytest.mark.asyncio
    async def test_empty_sources(self):
        result = await discover_mentions(
            query="test", sources=[], adapters={},
        )
        assert result.mentions == []
        assert result.sources_searched == []

    @pytest.mark.asyncio
    async def test_single_source_success(self):
        mentions = [_make_mention(DataSource.TWITTER)]
        adapter = _make_adapter(mentions=mentions)

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER],
            adapters={DataSource.TWITTER: adapter},
        )
        assert len(result.mentions) == 1
        assert "twitter" in result.sources_searched
        assert result.sources_failed == []

    @pytest.mark.asyncio
    async def test_multiple_sources_fan_out(self):
        tw_mentions = [_make_mention(DataSource.TWITTER, "tw1")]
        rd_mentions = [_make_mention(DataSource.REDDIT, "rd1")]

        adapters = {
            DataSource.TWITTER: _make_adapter(mentions=tw_mentions),
            DataSource.REDDIT: _make_adapter(mentions=rd_mentions),
        }

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER, DataSource.REDDIT],
            adapters=adapters,
        )
        assert len(result.mentions) == 2
        assert set(result.sources_searched) == {"twitter", "reddit"}

    @pytest.mark.asyncio
    async def test_unavailable_source(self):
        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER, DataSource.FACEBOOK],
            adapters={DataSource.TWITTER: _make_adapter(mentions=[])},
        )
        assert "facebook" in result.sources_unavailable
        assert "twitter" in result.sources_searched

    @pytest.mark.asyncio
    async def test_adapter_error_captured(self):
        adapters = {
            DataSource.TWITTER: _make_adapter(error=RuntimeError("API down")),
        }

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER],
            adapters=adapters,
        )
        assert len(result.sources_failed) == 1
        assert result.sources_failed[0].source == "twitter"
        assert "API down" in result.sources_failed[0].reason
        assert result.mentions == []

    @pytest.mark.asyncio
    async def test_adapter_timeout_captured(self):
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(100)
            return [], None

        adapter = AsyncMock()
        adapter.fetch_mentions = slow_fetch

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER],
            adapters={DataSource.TWITTER: adapter},
            adapter_timeout=0.01,
        )
        assert len(result.sources_failed) == 1
        assert result.sources_failed[0].reason == "timeout"

    @pytest.mark.asyncio
    async def test_results_sorted_by_date_descending(self):
        old = _make_mention(DataSource.TWITTER, "old",
                            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        new = _make_mention(DataSource.REDDIT, "new",
                            published_at=datetime(2026, 3, 1, tzinfo=timezone.utc))

        adapters = {
            DataSource.TWITTER: _make_adapter(mentions=[old]),
            DataSource.REDDIT: _make_adapter(mentions=[new]),
        }

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER, DataSource.REDDIT],
            adapters=adapters,
        )
        assert result.mentions[0].source_id == "new"
        assert result.mentions[1].source_id == "old"

    @pytest.mark.asyncio
    async def test_results_capped_at_limit(self):
        mentions = [_make_mention(DataSource.TWITTER, str(i)) for i in range(10)]
        adapter = _make_adapter(mentions=mentions)

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER],
            adapters={DataSource.TWITTER: adapter},
            limit=3,
        )
        assert len(result.mentions) == 3

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        """One adapter succeeds, one fails — results from successful adapter returned."""
        mentions = [_make_mention(DataSource.TWITTER)]
        adapters = {
            DataSource.TWITTER: _make_adapter(mentions=mentions),
            DataSource.REDDIT: _make_adapter(error=RuntimeError("500")),
        }

        result = await discover_mentions(
            query="brand",
            sources=[DataSource.TWITTER, DataSource.REDDIT],
            adapters=adapters,
        )
        assert len(result.mentions) == 1
        assert "twitter" in result.sources_searched
        assert len(result.sources_failed) == 1
        assert result.sources_failed[0].source == "reddit"
