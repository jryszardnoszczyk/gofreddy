"""Tests for PR-070: Data Expansion — Reviews + Podcasts + Google Trends."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.monitoring.adapters._common import parse_apify_items, rating_to_sentiment
from src.monitoring.adapters.google_trends import GoogleTrendsAdapter
from src.monitoring.adapters.podcasts import PodEngineAdapter
from src.monitoring.adapters.reviews import (
    AppStoreAdapter,
    PlayStoreAdapter,
    TrustpilotAdapter,
)
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource, SentimentLabel

pytestmark = pytest.mark.mock_required


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_settings() -> MonitoringSettings:
    """Create test settings with short timeouts."""
    return MonitoringSettings(
        enabled=True,
        adapter_timeout_seconds=5.0,
        circuit_breaker_threshold=10,  # High to avoid tripping in tests
    )


def _make_apify_run(
    status: str = "SUCCEEDED",
    dataset_id: str = "test-dataset-123",
) -> dict[str, Any]:
    return {
        "status": status,
        "defaultDatasetId": dataset_id,
        "statusMessage": "",
    }


def _make_trustpilot_item(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": "tp-review-001",
        "text": "Great product, fast shipping!",
        "title": "Excellent service",
        "rating": 5,
        "isVerified": True,
        "likes": 3,
        "url": "https://www.trustpilot.com/reviews/tp-review-001",
        "consumer": {
            "displayName": "John D.",
            "countryCode": "US",
            "numberOfReviews": 12,
        },
        "dates": {
            "publishedDate": "2026-03-01T10:00:00Z",
        },
        "reply": {
            "message": "Thanks for the review!",
            "publishedDate": "2026-03-02T09:00:00Z",
        },
    }
    item.update(overrides)
    return item


def _make_appstore_item(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": "appstore-001",
        "review": "Works perfectly on my iPhone.",
        "title": "Best app ever",
        "score": 4,
        "userName": "iUser42",
        "date": "2026-03-01",
        "version": "2.1.0",
        "voteCount": 7,
    }
    item.update(overrides)
    return item


def _make_playstore_item(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "reviewId": "gp-review-001",
        "text": "Battery drain is horrible.",
        "score": 2,
        "userName": "AndroidFan",
        "date": "2026-02-28",
        "appVersion": "3.0.1",
        "deviceType": "Pixel 7",
        "thumbsUpCount": 15,
        "replyText": "We're working on fixing this.",
        "replyDate": "2026-03-01",
    }
    item.update(overrides)
    return item


def _make_trends_item(**overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "searchTerm": "brand-name",
        "date": "2026-03-01",
        "geo": "US",
        "value": 75,
        "relatedQueries": {"rising": ["brand review"], "top": ["brand coupon"]},
        "relatedTopics": {"rising": [], "top": []},
        "interestByRegion": [{"geo": "US-CA", "location": "California", "value": 90}],
    }
    item.update(overrides)
    return item


def _make_podcast_result(**overrides: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "episode_id": "pod-ep-001",
        "matched_text": "This brand has been growing rapidly in the market.",
        "show_name": "Tech Review Podcast",
        "host_name": "Jane Smith",
        "episode_url": "https://example.com/episode/001",
        "published_date": "2026-03-01",
        "start_time": 125.5,
        "end_time": 142.0,
        "speaker": "host",
        "is_sponsored": False,
        "episode_title": "Brand Review 2026",
        "duration_seconds": 3600,
    }
    result.update(overrides)
    return result


def _mock_apify_actor(items: list[dict], run: dict | None = None):
    """Create a mock Apify client that returns given items.

    Apify client methods: .actor() is sync (returns ActorClient),
    .actor().call() is async, .dataset() is sync, .dataset().list_items() is async.
    """
    mock_client = MagicMock()
    mock_run = run or _make_apify_run()

    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=mock_run)
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_items_result = MagicMock()
    mock_items_result.items = items
    mock_dataset.list_items = AsyncMock(return_value=mock_items_result)
    mock_client.dataset.return_value = mock_dataset

    return mock_client


# ---------------------------------------------------------------------------
# TestRatingToSentiment
# ---------------------------------------------------------------------------

class TestRatingToSentiment:
    """Rating→sentiment mapping edge cases."""

    def test_rating_1_negative(self):
        score, label = rating_to_sentiment(1)
        assert score == -0.8
        assert label == SentimentLabel.NEGATIVE

    def test_rating_2_negative(self):
        score, label = rating_to_sentiment(2)
        assert score == -0.8
        assert label == SentimentLabel.NEGATIVE

    def test_rating_3_neutral(self):
        score, label = rating_to_sentiment(3)
        assert score == 0.0
        assert label == SentimentLabel.NEUTRAL

    def test_rating_4_positive(self):
        score, label = rating_to_sentiment(4)
        assert score == 0.8
        assert label == SentimentLabel.POSITIVE

    def test_rating_5_positive(self):
        score, label = rating_to_sentiment(5)
        assert score == 0.8
        assert label == SentimentLabel.POSITIVE

    def test_rating_none(self):
        score, label = rating_to_sentiment(None)
        assert score is None
        assert label is None

    def test_rating_zero(self):
        score, label = rating_to_sentiment(0)
        assert score is None
        assert label is None

    def test_rating_3_5_floors_to_neutral(self):
        score, label = rating_to_sentiment(3.5)
        assert score == 0.0
        assert label == SentimentLabel.NEUTRAL

    def test_rating_4_7_floors_to_positive(self):
        score, label = rating_to_sentiment(4.7)
        assert score == 0.8
        assert label == SentimentLabel.POSITIVE

    def test_rating_7_clamped_to_5(self):
        score, label = rating_to_sentiment(7)
        assert score == 0.8
        assert label == SentimentLabel.POSITIVE

    def test_rating_10_clamped_to_5(self):
        score, label = rating_to_sentiment(10)
        assert score == 0.8
        assert label == SentimentLabel.POSITIVE

    def test_rating_negative_invalid(self):
        score, label = rating_to_sentiment(-1)
        assert score is None
        assert label is None


# ---------------------------------------------------------------------------
# TestParseApifyItems
# ---------------------------------------------------------------------------

class TestParseApifyItems:
    """Shared Apify item parsing tests."""

    @pytest.mark.asyncio
    async def test_none_run_raises(self):
        with pytest.raises(MentionFetchError, match="Actor returned no run"):
            await parse_apify_items(None, AsyncMock())

    @pytest.mark.asyncio
    async def test_failed_run_raises(self):
        run = _make_apify_run(status="FAILED")
        with pytest.raises(MentionFetchError, match="FAILED"):
            await parse_apify_items(run, AsyncMock())

    @pytest.mark.asyncio
    async def test_timed_out_run_raises(self):
        run = _make_apify_run(status="TIMED-OUT")
        with pytest.raises(MentionFetchError, match="TIMED-OUT"):
            await parse_apify_items(run, AsyncMock())

    @pytest.mark.asyncio
    async def test_missing_dataset_returns_empty(self):
        run = {"status": "SUCCEEDED", "defaultDatasetId": ""}
        result = await parse_apify_items(run, AsyncMock())
        assert result == []

    @pytest.mark.asyncio
    async def test_successful_parse(self):
        mock_client = MagicMock()
        mock_items = MagicMock()
        mock_items.items = [{"id": "1"}, {"id": "2"}]
        mock_dataset = MagicMock()
        mock_dataset.list_items = AsyncMock(return_value=mock_items)
        mock_client.dataset.return_value = mock_dataset

        result = await parse_apify_items(_make_apify_run(), mock_client)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# TestGoogleTrendsAdapter
# ---------------------------------------------------------------------------

class TestGoogleTrendsAdapter:
    """Google Trends adapter tests."""

    def test_source_property(self):
        adapter = GoogleTrendsAdapter("token", settings=_make_settings())
        assert adapter.source == DataSource.GOOGLE_TRENDS

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_trends_item()])
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("brand-name")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.GOOGLE_TRENDS
        assert m.content == "brand-name"
        assert m.sentiment_score is None
        assert m.sentiment_label is None
        assert m.metadata["interest_score"] == 75
        assert cursor is None

    @pytest.mark.asyncio
    async def test_source_id_deterministic(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        item = _make_trends_item(searchTerm="test", date="2026-03-01", geo="US")
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions1, _ = await adapter._do_fetch("test")
        mentions2, _ = await adapter._do_fetch("test")

        assert mentions1[0].source_id == mentions2[0].source_id
        assert mentions1[0].source_id == "test:2026-03-01:US"

    @pytest.mark.asyncio
    async def test_breakout_string_handling(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        item = _make_trends_item(value=">5000%")
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("brand")
        assert mentions[0].metadata["breakout"] is True
        assert mentions[0].metadata["interest_score"] == 5000

    @pytest.mark.asyncio
    async def test_interest_score_zero_valid(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        item = _make_trends_item(value=0)
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("brand")
        assert len(mentions) == 1
        assert mentions[0].metadata["interest_score"] == 0

    @pytest.mark.asyncio
    async def test_empty_results(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([])
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("brand")
        assert mentions == []
        assert cursor is None

    @pytest.mark.asyncio
    async def test_malformed_item_skipped(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        items = [
            "not-a-dict",  # malformed
            _make_trends_item(),  # valid
        ]
        mock_client = _mock_apify_actor(items)
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("brand")
        assert len(mentions) == 1  # Only valid item processed

    @pytest.mark.asyncio
    async def test_actor_not_found(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        mock_client = MagicMock()
        mock_actor = MagicMock()
        mock_actor.call = AsyncMock(side_effect=Exception("404 Actor not found"))
        mock_client.actor.return_value = mock_actor
        adapter._client = mock_client

        with pytest.raises(MentionFetchError, match="not found"):
            await adapter._do_fetch("brand")

    @pytest.mark.asyncio
    async def test_run_status_failed(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        run = _make_apify_run(status="FAILED")
        mock_client = _mock_apify_actor([], run=run)
        adapter._client = mock_client

        with pytest.raises(MentionFetchError, match="FAILED"):
            await adapter._do_fetch("brand")

    @pytest.mark.asyncio
    async def test_metadata_structure(self):
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_trends_item()])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("brand")
        meta = mentions[0].metadata
        assert "interest_score" in meta
        assert "related_queries" in meta
        assert "geo_data" in meta
        assert "breakout" in meta

    @pytest.mark.asyncio
    async def test_source_id_date_fallback(self):
        """Uses current date when item has no date, not static 'latest'."""
        adapter = GoogleTrendsAdapter("test-token", settings=_make_settings())
        item = _make_trends_item()
        item.pop("date")  # No date
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("brand")
        source_id = mentions[0].source_id
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        assert today in source_id
        assert "latest" not in source_id

    @pytest.mark.asyncio
    async def test_empty_token_raises(self):
        adapter = GoogleTrendsAdapter("", settings=_make_settings())
        with pytest.raises(MentionFetchError, match="APIFY_TOKEN not configured"):
            await adapter._do_fetch("brand")


# ---------------------------------------------------------------------------
# TestTrustpilotAdapter
# ---------------------------------------------------------------------------

class TestTrustpilotAdapter:
    """Trustpilot adapter tests."""

    def test_source_property(self):
        adapter = TrustpilotAdapter("token", settings=_make_settings())
        assert adapter.source == DataSource.TRUSTPILOT

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        adapter = TrustpilotAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_trustpilot_item()])
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("example.com")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.TRUSTPILOT
        assert m.source_id == "tp-review-001"
        assert m.content == "Great product, fast shipping!"
        assert m.author_handle == "John D."
        assert m.sentiment_score == 0.8
        assert m.sentiment_label == SentimentLabel.POSITIVE
        assert m.geo_country == "US"
        assert cursor is None

    @pytest.mark.asyncio
    async def test_business_reply_included(self):
        adapter = TrustpilotAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_trustpilot_item()])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("example.com")
        meta = mentions[0].metadata
        assert meta["business_reply"] == "Thanks for the review!"
        assert meta["business_reply_date"] == "2026-03-02T09:00:00Z"

    @pytest.mark.asyncio
    async def test_missing_rating(self):
        adapter = TrustpilotAdapter("test-token", settings=_make_settings())
        item = _make_trustpilot_item(rating=None)
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("example.com")
        assert mentions[0].sentiment_score is None
        assert mentions[0].sentiment_label is None

    @pytest.mark.asyncio
    async def test_verified_flag(self):
        adapter = TrustpilotAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_trustpilot_item(isVerified=True)])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("example.com")
        assert mentions[0].metadata["verified"] is True


# ---------------------------------------------------------------------------
# TestAppStoreAdapter
# ---------------------------------------------------------------------------

class TestAppStoreAdapter:
    """App Store adapter tests."""

    def test_source_property(self):
        adapter = AppStoreAdapter("token", settings=_make_settings())
        assert adapter.source == DataSource.APP_STORE

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        adapter = AppStoreAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_appstore_item()])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("https://apps.apple.com/app/id123")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.APP_STORE
        assert m.source_id == "appstore-001"
        assert m.content == "Works perfectly on my iPhone."
        assert m.sentiment_score == 0.8
        assert m.sentiment_label == SentimentLabel.POSITIVE
        assert m.metadata["app_version"] == "2.1.0"

    @pytest.mark.asyncio
    async def test_fallback_source_id(self):
        adapter = AppStoreAdapter("test-token", settings=_make_settings())
        item = _make_appstore_item()
        del item["id"]
        mock_client = _mock_apify_actor([item])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("https://apps.apple.com/app/id123")
        assert mentions[0].source_id.startswith("appstore:")


# ---------------------------------------------------------------------------
# TestPlayStoreAdapter
# ---------------------------------------------------------------------------

class TestPlayStoreAdapter:
    """Play Store adapter tests."""

    def test_source_property(self):
        adapter = PlayStoreAdapter("token", settings=_make_settings())
        assert adapter.source == DataSource.PLAY_STORE

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        adapter = PlayStoreAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_playstore_item()])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("https://play.google.com/store/apps/details?id=com.example")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.PLAY_STORE
        assert m.source_id == "gp-review-001"
        assert m.content == "Battery drain is horrible."
        assert m.sentiment_score == -0.8
        assert m.sentiment_label == SentimentLabel.NEGATIVE
        assert m.metadata["device_type"] == "Pixel 7"

    @pytest.mark.asyncio
    async def test_developer_reply(self):
        adapter = PlayStoreAdapter("test-token", settings=_make_settings())
        mock_client = _mock_apify_actor([_make_playstore_item()])
        adapter._client = mock_client

        mentions, _ = await adapter._do_fetch("https://play.google.com/store/apps/details?id=com.example")
        meta = mentions[0].metadata
        assert meta["business_reply"] == "We're working on fixing this."
        assert meta["business_reply_date"] == "2026-03-01"


# ---------------------------------------------------------------------------
# TestPodEngineAdapter
# ---------------------------------------------------------------------------

class TestPodEngineAdapter:
    """Pod Engine adapter tests."""

    def test_source_property(self):
        adapter = PodEngineAdapter("key", settings=_make_settings())
        assert adapter.source == DataSource.PODCAST

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())

        response_data = {
            "results": [_make_podcast_result()],
            "total": 1,
        }
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        mentions, cursor = await adapter._do_fetch("brand-name")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.PODCAST
        assert m.source_id == "pod-ep-001"
        assert m.content == "This brand has been growing rapidly in the market."
        assert m.author_handle == "Tech Review Podcast"
        assert m.url == "https://example.com/episode/001"
        assert cursor is None  # total=1, offset=0, 1 result → no more

    @pytest.mark.asyncio
    async def test_content_truncation(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())
        long_text = "x" * 3000
        result = _make_podcast_result(matched_text=long_text)
        response_data = {"results": [result], "total": 1}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        mentions, _ = await adapter._do_fetch("brand")
        assert len(mentions[0].content) == 2000

    @pytest.mark.asyncio
    async def test_ad_segment_flag(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())
        result = _make_podcast_result(is_sponsored=True)
        response_data = {"results": [result], "total": 1}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        mentions, _ = await adapter._do_fetch("brand")
        assert mentions[0].metadata["is_ad_segment"] is True

    @pytest.mark.asyncio
    async def test_rate_limit_429(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        with pytest.raises(MentionFetchError, match="rate limit"):
            await adapter._do_fetch("brand")

    @pytest.mark.asyncio
    async def test_auth_failure_401(self):
        adapter = PodEngineAdapter("bad-key", settings=_make_settings())

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        with pytest.raises(MentionFetchError, match="Invalid POD_ENGINE_API_KEY"):
            await adapter._do_fetch("brand")

    @pytest.mark.asyncio
    async def test_pagination_cursor(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())
        results = [_make_podcast_result(episode_id=f"ep-{i}") for i in range(5)]
        response_data = {"results": results, "total": 20}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.get = AsyncMock(return_value=mock_response)
        adapter._http_client = mock_http

        mentions, cursor = await adapter._do_fetch("brand")
        assert len(mentions) == 5
        assert cursor == "5"  # offset 0 + 5 results = next offset 5

    @pytest.mark.asyncio
    async def test_empty_api_key_raises(self):
        adapter = PodEngineAdapter("", settings=_make_settings())
        with pytest.raises(MentionFetchError, match="POD_ENGINE_API_KEY not configured"):
            await adapter._do_fetch("brand")

    @pytest.mark.asyncio
    async def test_httpx_client_lifecycle(self):
        adapter = PodEngineAdapter("test-key", settings=_make_settings())
        assert adapter._http_client is None

        # After close, client should be None
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        adapter._http_client = mock_http
        await adapter.close()
        assert adapter._http_client is None
        mock_http.aclose.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestAdapterTimeout
# ---------------------------------------------------------------------------

class TestAdapterTimeout:
    """Verify timeout_override mechanism."""

    def test_google_trends_timeout_override(self):
        adapter = GoogleTrendsAdapter("token", settings=_make_settings())
        assert adapter._timeout_override == 150

    def test_review_adapter_timeout_override(self):
        for cls in (TrustpilotAdapter, AppStoreAdapter, PlayStoreAdapter):
            adapter = cls("token", settings=_make_settings())
            assert adapter._timeout_override == 200

    def test_pod_engine_timeout_override(self):
        adapter = PodEngineAdapter("key", settings=_make_settings())
        assert adapter._timeout_override == 45

    def test_default_timeout_without_override(self):
        """BaseMentionFetcher with no override uses settings default."""
        from src.monitoring.fetcher_protocol import BaseMentionFetcher

        class TestAdapter(BaseMentionFetcher):
            @property
            def source(self) -> DataSource:
                return DataSource.TWITTER

            async def _do_fetch(self, query, *, cursor=None, limit=100):
                return ([], None)

        settings = _make_settings()
        adapter = TestAdapter(settings=settings)
        assert adapter._timeout_override is None
        # The effective timeout should be the settings default
        effective = adapter._timeout_override or settings.adapter_timeout_seconds
        assert effective == settings.adapter_timeout_seconds


# ---------------------------------------------------------------------------
# TestDataSourceEnum
# ---------------------------------------------------------------------------

class TestDataSourceEnum:
    """Verify PODCAST added to DataSource."""

    def test_podcast_in_enum(self):
        assert DataSource.PODCAST == "podcast"
        assert DataSource.PODCAST.value == "podcast"

    def test_all_sources_count(self):
        # 13 existing + PODCAST = 14 (THREADS is commented out)
        assert len(DataSource) == 14
