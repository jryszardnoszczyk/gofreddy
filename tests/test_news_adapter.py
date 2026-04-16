"""Tests for NewsData.io monitoring adapter."""

import pytest
import httpx
import respx

from src.monitoring.adapters.news import NewsDataAdapter, _first_or_none, _join_text, _parse_datetime
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource, SentimentLabel

SAMPLE_ARTICLE = {
    "article_id": "abc123",
    "title": "Nike Q1 Earnings Beat",
    "description": "Nike reported strong earnings...",
    "content": "Full article text with details about Nike earnings.",
    "link": "https://example.com/article",
    "creator": ["John Doe"],
    "pubDate": "2026-03-01T10:00:00Z",
    "sentiment": "positive",
    "sentiment_stats": {"positive": 0.8, "neutral": 0.15, "negative": 0.05},
    "ai_tag": ["earnings", "sportswear"],
    "ai_org": ["Nike Inc"],
    "ai_region": ["North America"],
    "source_id": "example_news",
    "source_url": "https://example.com",
    "source_icon": "https://example.com/icon.png",
    "source_priority": 1234,
    "language": "en",
    "country": ["us"],
    "category": ["business"],
    "image_url": "https://example.com/img.jpg",
    "keywords": ["nike", "earnings"],
}

SAMPLE_RESPONSE = {
    "status": "success",
    "totalResults": 1,
    "results": [SAMPLE_ARTICLE],
    "nextPage": "page2token",
}


def _make_settings() -> MonitoringSettings:
    return MonitoringSettings(
        newsdata_api_key="test-key",  # type: ignore[arg-type]
        adapter_timeout_seconds=5.0,
    )


class TestNewsDataAdapter:
    def test_source_property(self):
        adapter = NewsDataAdapter(settings=_make_settings())
        assert adapter.source == DataSource.NEWSDATA

    @respx.mock
    async def test_fetch_latest_success(self):
        route = respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, cursor = await adapter._do_fetch("nike")

        assert route.called
        assert len(mentions) == 1
        assert mentions[0].source == DataSource.NEWSDATA
        assert mentions[0].source_id == "abc123"
        assert mentions[0].author_name == "John Doe"
        assert "Nike Q1 Earnings Beat" in mentions[0].content
        assert mentions[0].url == "https://example.com/article"
        assert cursor == "page2token"

    @respx.mock
    async def test_fetch_with_pagination(self):
        route = respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json={
                "status": "success",
                "results": [SAMPLE_ARTICLE],
                "nextPage": None,
            })
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, cursor = await adapter._do_fetch("nike", cursor="page2token")

        assert route.called
        req = route.calls[0].request
        assert "page=page2token" in str(req.url)
        assert cursor is None

    @respx.mock
    async def test_field_mapping_sentiment(self):
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        m = mentions[0]
        assert m.sentiment_label == SentimentLabel.POSITIVE
        assert m.sentiment_score == pytest.approx(0.75, abs=0.01)

    @respx.mock
    async def test_field_mapping_ai_tags(self):
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        meta = mentions[0].metadata
        assert meta["ai_tag"] == ["earnings", "sportswear"]
        assert meta["ai_org"] == ["Nike Inc"]
        assert meta["ai_region"] == ["North America"]

    @respx.mock
    async def test_field_mapping_media_urls(self):
        article = {**SAMPLE_ARTICLE, "video_url": "https://example.com/video.mp4"}
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json={"results": [article]})
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert "https://example.com/img.jpg" in mentions[0].media_urls
        assert "https://example.com/video.mp4" in mentions[0].media_urls

    @respx.mock
    async def test_field_mapping_missing_fields(self):
        minimal = {"article_id": "min1"}
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json={"results": [minimal]})
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("test")

        m = mentions[0]
        assert m.source_id == "min1"
        assert m.author_name is None
        assert m.sentiment_label is None
        assert m.sentiment_score is None
        assert m.content == ""
        assert m.media_urls == []

    @respx.mock
    async def test_duplicate_article_flagged(self):
        article = {**SAMPLE_ARTICLE, "duplicate": True}
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(200, json={"results": [article]})
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, _ = await adapter._do_fetch("nike")

        assert mentions[0].metadata["is_duplicate"] is True

    @respx.mock
    async def test_rate_limit_429_retried(self):
        """429 should raise httpx.HTTPStatusError (retried by BaseMentionFetcher)."""
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "60"})
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            with pytest.raises(httpx.HTTPStatusError):
                await adapter._do_fetch("nike")

    @respx.mock
    async def test_bad_request_422(self):
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(422, text="Invalid query")
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            mentions, cursor = await adapter._do_fetch("bad query")

        assert mentions == []
        assert cursor is None

    @respx.mock
    async def test_auth_error_401(self):
        respx.get("https://newsdata.io/api/1/latest").mock(
            return_value=httpx.Response(401)
        )
        adapter = NewsDataAdapter(settings=_make_settings())
        async with adapter:
            with pytest.raises(MentionFetchError, match="invalid API key"):
                await adapter._do_fetch("nike")

    async def test_uninitialized_client(self):
        adapter = NewsDataAdapter(settings=_make_settings())
        with pytest.raises(MentionFetchError, match="not initialized"):
            await adapter._do_fetch("nike")


class TestHelpers:
    def test_first_or_none_list(self):
        assert _first_or_none(["a", "b"]) == "a"

    def test_first_or_none_string(self):
        assert _first_or_none("hello") == "hello"

    def test_first_or_none_empty(self):
        assert _first_or_none([]) is None
        assert _first_or_none(None) is None

    def test_join_text(self):
        assert _join_text("a", None, "b") == "a\n\nb"
        assert _join_text(None, None) == ""

    def test_parse_datetime_valid(self):
        dt = _parse_datetime("2026-03-01T10:00:00Z")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_datetime_invalid(self):
        assert _parse_datetime("not-a-date") is None
        assert _parse_datetime(None) is None


class TestSentimentScore:
    def test_positive_dominant(self):
        score = NewsDataAdapter._compute_sentiment_score({"positive": 0.8, "negative": 0.1})
        assert score == pytest.approx(0.7, abs=0.01)

    def test_negative_dominant(self):
        score = NewsDataAdapter._compute_sentiment_score({"positive": 0.1, "negative": 0.8})
        assert score == pytest.approx(-0.7, abs=0.01)

    def test_zero_returns_none(self):
        score = NewsDataAdapter._compute_sentiment_score({})
        assert score is None
