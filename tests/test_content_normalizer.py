"""Tests for content_normalizer pure functions."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.monitoring.models import DataSource, SentimentLabel
from src.orchestrator.content_normalizer import (
    dedup_content,
    filter_content,
    normalize_raw_mention,
    relevance_sort_key,
)


def _fake_mention(**overrides):
    """Create a fake RawMention-like object using SimpleNamespace."""
    defaults = {
        "source": DataSource.TWITTER,
        "source_id": "tw123",
        "author_handle": "@alice",
        "author_name": "Alice",
        "content": "Hello world",
        "url": "https://twitter.com/alice/status/123",
        "published_at": datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc),
        "engagement_likes": 100,
        "engagement_shares": 20,
        "engagement_comments": 5,
        "sentiment_label": SentimentLabel.POSITIVE,
        "language": "en",
        "media_urls": [],
        "metadata": {},
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestNormalizeRawMention:
    def test_basic_normalization(self):
        m = _fake_mention()
        result = normalize_raw_mention(m)

        assert result["content_type"] == "social_post"
        assert result["source_id"] == "tw123"
        assert result["platform"] == "twitter"
        assert result["author_handle"] == "@alice"
        assert result["engagement"]["likes"] == 100
        assert result["sentiment"] == "positive"

    def test_video_content_type(self):
        m = _fake_mention(source=DataSource.TIKTOK)
        result = normalize_raw_mention(m)
        assert result["content_type"] == "video"

    def test_news_content_type(self):
        m = _fake_mention(source=DataSource.NEWSDATA)
        result = normalize_raw_mention(m)
        assert result["content_type"] == "news"

    def test_podcast_content_type(self):
        m = _fake_mention(source=DataSource.PODCAST)
        result = normalize_raw_mention(m)
        assert result["content_type"] == "podcast"

    def test_none_source(self):
        m = _fake_mention(source=None)
        result = normalize_raw_mention(m)
        assert result["platform"] == "unknown"
        assert result["content_type"] == "social_post"

    def test_missing_published_at(self):
        m = _fake_mention(published_at=None)
        result = normalize_raw_mention(m)
        assert result["published_at"] is None

    def test_sentiment_none(self):
        m = _fake_mention(sentiment_label=None)
        result = normalize_raw_mention(m)
        assert result["sentiment"] is None


class TestDedupContent:
    def test_no_duplicates(self):
        items = [
            {"platform": "twitter", "source_id": "1", "engagement": {"likes": 10, "shares": 0, "comments": 0, "views": 0}},
            {"platform": "instagram", "source_id": "2", "engagement": {"likes": 20, "shares": 0, "comments": 0, "views": 0}},
        ]
        result = dedup_content(items)
        assert len(result) == 2

    def test_duplicate_keeps_higher_engagement(self):
        items = [
            {"platform": "tiktok", "source_id": "v1", "engagement": {"likes": 10, "shares": 0, "comments": 0, "views": 100}, "sentiment": "positive"},
            {"platform": "tiktok", "source_id": "v1", "engagement": {"likes": 50, "shares": 5, "comments": 3, "views": 500}, "sentiment": None},
        ]
        result = dedup_content(items)
        assert len(result) == 1
        # Higher engagement wins
        assert result[0]["engagement"]["likes"] == 50
        # Sentiment preserved from first item (Xpoz wins sentiment)
        assert result[0]["sentiment"] == "positive"

    def test_duplicate_xpoz_sentiment_wins(self):
        items = [
            {"platform": "tiktok", "source_id": "v1", "engagement": {"likes": 100, "shares": 0, "comments": 0, "views": 0}, "sentiment": None},
            {"platform": "tiktok", "source_id": "v1", "engagement": {"likes": 10, "shares": 0, "comments": 0, "views": 0}, "sentiment": "negative"},
        ]
        result = dedup_content(items)
        assert len(result) == 1
        # First item has higher engagement (kept), but gets sentiment from second
        assert result[0]["engagement"]["likes"] == 100
        assert result[0]["sentiment"] == "negative"

    def test_empty_source_id_kept(self):
        items = [
            {"platform": "twitter", "source_id": "", "engagement": {"likes": 1, "shares": 0, "comments": 0, "views": 0}},
            {"platform": "twitter", "source_id": "", "engagement": {"likes": 2, "shares": 0, "comments": 0, "views": 0}},
        ]
        result = dedup_content(items)
        assert len(result) == 2  # Both kept since no source_id


class TestRelevanceSortKey:
    def test_basic_scoring(self):
        item = {"engagement": {"likes": 100, "shares": 50, "comments": 20, "views": 10000}}
        score = relevance_sort_key(item)
        # 100 + 50*2 + 20*1.5 + 10000*0.001 = 100 + 100 + 30 + 10 = 240.0
        assert score == pytest.approx(240.0)

    def test_empty_engagement(self):
        assert relevance_sort_key({}) == 0.0
        assert relevance_sort_key({"engagement": {}}) == 0.0

    def test_sorting_order(self):
        items = [
            {"engagement": {"likes": 10, "shares": 0, "comments": 0, "views": 0}},
            {"engagement": {"likes": 100, "shares": 50, "comments": 20, "views": 10000}},
            {"engagement": {"likes": 50, "shares": 10, "comments": 5, "views": 1000}},
        ]
        items.sort(key=relevance_sort_key, reverse=True)
        assert items[0]["engagement"]["likes"] == 100
        assert items[2]["engagement"]["likes"] == 10


class TestFilterContent:
    def _items(self):
        return [
            {"platform": "tiktok", "engagement": {"views": 500_000, "likes": 50_000, "comments": 1000, "shares": 5000}, "duration": 30},
            {"platform": "youtube", "engagement": {"views": 1_000_000, "likes": 10_000, "comments": 500, "shares": 200}, "duration": 600},
            {"platform": "instagram", "engagement": {"views": 50_000, "likes": 5000, "comments": 200, "shares": 100}, "duration": 15},
            {"platform": "twitter", "engagement": {"views": 0, "likes": 20, "comments": 5, "shares": 3}, "duration": None},
        ]

    def test_no_filters_returns_all(self):
        items = self._items()
        assert len(filter_content(items)) == 4

    def test_min_views_filters(self):
        result = filter_content(self._items(), min_views=100_000)
        assert len(result) == 2
        assert all(r["engagement"]["views"] >= 100_000 for r in result)

    def test_min_views_zero_views_excluded(self):
        result = filter_content(self._items(), min_views=1)
        platforms = {r["platform"] for r in result}
        assert "twitter" not in platforms  # 0 views

    def test_min_engagement_rate(self):
        # tiktok: (50000+1000+5000)/500000 = 0.112
        # youtube: (10000+500+200)/1000000 = 0.0107
        # instagram: (5000+200+100)/50000 = 0.106
        # twitter: (20+5+3)/1 = 28.0 (views=0 → max(0,1)=1)
        result = filter_content(self._items(), min_engagement_rate=0.1)
        platforms = {r["platform"] for r in result}
        assert "tiktok" in platforms
        assert "instagram" in platforms
        assert "twitter" in platforms  # high rate due to 0 views
        assert "youtube" not in platforms

    def test_content_format_short(self):
        result = filter_content(self._items(), content_format="short")
        # tiktok, instagram, twitter are short-form platforms; youtube 600s excluded
        platforms = {r["platform"] for r in result}
        assert "tiktok" in platforms
        assert "instagram" in platforms
        assert "twitter" in platforms
        assert "youtube" not in platforms

    def test_content_format_long(self):
        result = filter_content(self._items(), content_format="long")
        # youtube always long; others have duration < 180
        platforms = {r["platform"] for r in result}
        assert "youtube" in platforms
        assert len(result) == 1

    def test_combined_filters(self):
        result = filter_content(
            self._items(), min_views=100_000, content_format="short",
        )
        # Only tiktok has views >= 100K AND is short-form
        assert len(result) == 1
        assert result[0]["platform"] == "tiktok"

    def test_empty_input(self):
        assert filter_content([]) == []

    def test_all_filtered_out(self):
        assert filter_content(self._items(), min_views=10_000_000) == []
