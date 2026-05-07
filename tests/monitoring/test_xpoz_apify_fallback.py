"""Tests for XpozAdapter live_only Apify fallback (master plan §4.2 + §4.9 #11).

Validates the live-vs-indexed pattern: Xpoz pre-indexed search remains
primary; ``live_only=True`` routes Twitter queries through Apify's
twitter-scraper-lite actor as a cheap one-off fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.monitoring.adapters.xpoz import XpozAdapter
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource
from src.monitoring.config import MonitoringSettings


def _make_adapter(source: DataSource = DataSource.TWITTER) -> XpozAdapter:
    settings = MagicMock(spec=MonitoringSettings)
    settings.xpoz_api_key = MagicMock()
    settings.xpoz_api_key.get_secret_value.return_value = "test-key"
    settings.adapter_concurrency = 3
    settings.adapter_timeout_seconds = 30.0
    settings.circuit_breaker_threshold = 3
    settings.circuit_breaker_reset_seconds = 60.0
    with patch("src.monitoring.adapters.xpoz.AsyncXpozClient"):
        adapter = XpozAdapter(settings=settings, default_source=source)
    adapter._client = MagicMock()
    return adapter


@pytest.mark.asyncio
async def test_live_only_twitter_routes_through_apify(monkeypatch):
    """live_only=True for Twitter calls the Apify actor + maps items."""
    monkeypatch.setenv("APIFY_TOKEN", "test-apify-token")

    adapter = _make_adapter(source=DataSource.TWITTER)

    fake_items = [
        {
            "id": "tw-1",
            "text": "first tweet",
            "author": {"userName": "alice"},
            "createdAt": "2026-05-06T10:00:00Z",
            "url": "https://twitter.com/alice/status/tw-1",
            "likeCount": 5,
            "retweetCount": 2,
        },
    ]

    fake_run = {"status": "SUCCEEDED", "defaultDatasetId": "ds-1"}
    fake_actor = MagicMock()
    fake_actor.call = AsyncMock(return_value=fake_run)
    fake_client = MagicMock()
    fake_client.actor = MagicMock(return_value=fake_actor)

    with patch(
        "src.monitoring.adapters._common.build_apify_client", return_value=fake_client
    ), patch(
        "src.monitoring.adapters._common.parse_apify_items",
        AsyncMock(return_value=fake_items),
    ):
        mentions, cursor = await adapter._do_fetch("alice", live_only=True, limit=10)

    assert cursor is None
    assert len(mentions) == 1
    m = mentions[0]
    assert m.source_id == "tw-1"
    assert m.content == "first tweet"
    assert m.author_handle == "alice"
    assert m.source == DataSource.TWITTER
    assert m.engagement_likes == 5
    assert m.engagement_shares == 2
    assert m.metadata["_provider"] == "apify_live_fallback"
    assert m.metadata["_actor_id"] == adapter.APIFY_X_ACTOR_ID
    fake_client.actor.assert_called_once_with(adapter.APIFY_X_ACTOR_ID)


@pytest.mark.asyncio
async def test_live_only_without_apify_token_raises(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    adapter = _make_adapter(source=DataSource.TWITTER)
    with pytest.raises(MentionFetchError, match="APIFY_TOKEN"):
        await adapter._do_fetch("alice", live_only=True, limit=10)


@pytest.mark.asyncio
async def test_live_only_for_non_twitter_falls_back_to_xpoz(monkeypatch):
    """Instagram + Reddit don't have Apify fallback wired in v1 — fall back to Xpoz."""
    monkeypatch.setenv("APIFY_TOKEN", "test-apify-token")
    adapter = _make_adapter(source=DataSource.INSTAGRAM)
    adapter._search = AsyncMock(return_value=MagicMock(data=[]))
    adapter._map_post = MagicMock(return_value=MagicMock())

    mentions, cursor = await adapter._do_fetch("brand", live_only=True, limit=10)
    assert cursor is None
    adapter._search.assert_awaited_once()
