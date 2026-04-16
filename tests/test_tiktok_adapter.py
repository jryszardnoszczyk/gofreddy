"""Tests for TikTok Apify monitoring adapter."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest
import respx

from src.monitoring.adapters.tiktok import TikTokAdapter, _parse_unix_timestamp, _safe_int
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource

SAMPLE_TIKTOK_ITEM = {
    "id": "7123456789",
    "text": "Check out Nike's new drop",
    "createTime": 1709290000,
    "authorMeta": {
        "name": "creator1",
        "nickname": "Creator One",
        "fans": 50000,
        "verified": True,
        "id": "u123",
    },
    "diggCount": 15000,
    "commentCount": 340,
    "shareCount": 890,
    "playCount": 250000,
    "hashtags": [{"name": "nike"}, {"name": "sneakers"}],
    "videoMeta": {"coverUrl": "https://p.tiktok.com/cover.jpg", "duration": 30},
    "musicMeta": {"musicName": "Original Sound", "musicAuthor": "creator1"},
}

APIFY_RUN_RESPONSE = {
    "data": {
        "id": "run123",
        "defaultDatasetId": "ds456",
        "status": "SUCCEEDED",
    }
}


def _make_settings() -> MonitoringSettings:
    return MonitoringSettings(
        apify_token="test-apify-token",  # type: ignore[arg-type]
        adapter_timeout_seconds=150.0,
    )


class TestTikTokAdapter:
    def test_source_property(self):
        adapter = TikTokAdapter(settings=_make_settings())
        assert adapter.source == DataSource.TIKTOK

    def test_adapter_timeout_override(self):
        adapter = TikTokAdapter()
        assert adapter._settings.adapter_timeout_seconds == 150.0

    @respx.mock
    async def test_fetch_success(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[SAMPLE_TIKTOK_ITEM])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, cursor = await adapter._do_fetch("nike")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.TIKTOK
        assert m.source_id == "7123456789"
        assert m.author_handle == "creator1"
        assert m.author_name == "Creator One"
        assert m.content == "Check out Nike's new drop"
        assert cursor is None  # Apify has no pagination cursor

    @respx.mock
    async def test_field_mapping_engagement(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[SAMPLE_TIKTOK_ITEM])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        m = mentions[0]
        assert m.engagement_likes == 15000
        assert m.engagement_comments == 340
        assert m.engagement_shares == 890
        assert m.reach_estimate == 250000

    @respx.mock
    async def test_field_mapping_hashtags(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        # Test both dict and string hashtag formats
        item = {**SAMPLE_TIKTOK_ITEM, "hashtags": [{"name": "nike"}, "sneakers"]}
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[item])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert mentions[0].metadata["hashtags"] == ["nike", "sneakers"]

    @respx.mock
    async def test_field_mapping_author(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[SAMPLE_TIKTOK_ITEM])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        m = mentions[0]
        assert m.author_handle == "creator1"
        assert m.author_name == "Creator One"
        assert m.metadata["author_followers"] == 50000
        assert m.metadata["author_verified"] is True
        assert m.metadata["author_id"] == "u123"

    @respx.mock
    async def test_field_mapping_music(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[SAMPLE_TIKTOK_ITEM])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert mentions[0].metadata["music"] == "Original Sound — creator1"

    @respx.mock
    async def test_field_mapping_paid_content(self):
        item = {**SAMPLE_TIKTOK_ITEM, "isPaidPartnership": True}
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[item])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert mentions[0].metadata["is_paid"] is True

    @respx.mock
    async def test_field_mapping_subtitles(self):
        item = {**SAMPLE_TIKTOK_ITEM, "subtitleInfos": [{"lang": "en", "text": "hi"}]}
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[item])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert mentions[0].metadata["subtitles"] == [{"lang": "en", "text": "hi"}]

    @respx.mock
    async def test_missing_dataset_id(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, cursor = await adapter._do_fetch("nike")

        assert mentions == []
        assert cursor is None

    @respx.mock
    async def test_insufficient_credits_402(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(402)
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            with pytest.raises(MentionFetchError, match="insufficient credits"):
                await adapter._do_fetch("nike")

    @respx.mock
    async def test_auth_error_401(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(401)
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            with pytest.raises(MentionFetchError, match="invalid token"):
                await adapter._do_fetch("nike")

    async def test_uninitialized_client(self):
        adapter = TikTokAdapter(settings=_make_settings())
        with pytest.raises(MentionFetchError, match="not initialized"):
            await adapter._do_fetch("nike")

    @respx.mock
    async def test_cursor_always_none(self):
        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[SAMPLE_TIKTOK_ITEM])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            _, cursor = await adapter._do_fetch("nike")

        assert cursor is None

    @respx.mock
    async def test_stats_dict_format(self):
        """Test engagement extraction from stats dict format."""
        item = {
            **SAMPLE_TIKTOK_ITEM,
            "stats": {"diggCount": 999, "commentCount": 88, "shareCount": 77, "playCount": 5555},
        }
        # Remove flat keys so stats dict is used
        item.pop("diggCount")
        item.pop("commentCount")
        item.pop("shareCount")
        item.pop("playCount")

        respx.post("https://api.apify.com/v2/acts/clockworks/tiktok-scraper/runs").mock(
            return_value=httpx.Response(200, json=APIFY_RUN_RESPONSE)
        )
        respx.get("https://api.apify.com/v2/datasets/ds456/items").mock(
            return_value=httpx.Response(200, json=[item])
        )

        adapter = TikTokAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        m = mentions[0]
        assert m.engagement_likes == 999
        assert m.engagement_comments == 88
        assert m.engagement_shares == 77
        assert m.reach_estimate == 5555


class TestHelpers:
    def test_parse_unix_timestamp_valid(self):
        dt = _parse_unix_timestamp(1709290000)
        assert dt is not None
        assert dt.tzinfo == timezone.utc
        assert dt.year == 2024

    def test_parse_unix_timestamp_none(self):
        assert _parse_unix_timestamp(None) is None

    def test_parse_unix_timestamp_invalid(self):
        assert _parse_unix_timestamp("not-a-number") is None

    def test_safe_int_valid(self):
        assert _safe_int(42) == 42
        assert _safe_int("100") == 100

    def test_safe_int_none(self):
        assert _safe_int(None) == 0

    def test_safe_int_invalid(self):
        assert _safe_int("abc") == 0
