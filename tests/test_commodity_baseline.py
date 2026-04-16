"""Tests for commodity baseline generator — determinism and degradation cases."""

from datetime import date

import pytest

from src.monitoring.intelligence.commodity_baseline import (
    CommodityBaseline,
    InsufficientDataError,
    generate_commodity_baseline,
)


def _sample_mentions(n: int = 10) -> dict:
    return {
        "mentions": [
            {
                "source": "reddit" if i % 3 == 0 else ("twitter" if i % 3 == 1 else "newsdata"),
                "content": f"Test mention content about brand and product {i}",
                "engagement_likes": i * 10,
                "engagement_shares": i * 2,
                "engagement_comments": i,
                "url": f"https://example.com/{i}",
                "author_handle": f"user_{i % 5}",
                "reach_estimate": i * 1000,
                "language": "en" if i % 2 == 0 else "es",
                "published_at": f"2026-03-{10 + (i % 7):02d}T12:00:00Z",
            }
            for i in range(n)
        ]
    }


def _sample_sentiment() -> dict:
    return {
        "buckets": [
            {"positive_count": 15, "negative_count": 5, "neutral_count": 10, "mixed_count": 0},
            {"positive_count": 20, "negative_count": 8, "neutral_count": 12, "mixed_count": 0},
        ]
    }


def _sample_alerts() -> list[dict]:
    return [
        {"condition_summary": "volume_spike on reddit"},
        {"condition_summary": "sentiment_drop"},
    ]


def _sample_sov() -> dict:
    return {
        "entries": [
            {"brand": "OurBrand", "percentage": 45.2},
            {"brand": "CompetitorX", "percentage": 30.1},
            {"brand": "CompetitorY", "percentage": 24.7},
        ]
    }


class TestCommodityBaseline:
    def test_full_data(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(50),
            sentiment_data=_sample_sentiment(),
            sov_data=_sample_sov(),
            alerts_data=_sample_alerts(),
            period_start=date(2026, 3, 10),
            period_end=date(2026, 3, 17),
            previous_sentiment={"positive": 60.0, "neutral": 25.0, "negative": 15.0},
        )
        assert isinstance(result, CommodityBaseline)
        assert result.total_mentions == 50
        assert result.alerts_triggered == 2
        assert len(result.source_breakdown) > 0
        assert "previous week" in result.markdown
        assert "OurBrand" in result.markdown
        # G1: Enhanced statistics present
        assert len(result.daily_volumes) > 0
        assert result.engagement_per_mention > 0
        assert len(result.top_authors) > 0
        assert len(result.reach_tiers) == 3

    def test_word_frequency_topics(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(10),
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
            period_start=date(2026, 3, 10),
        )
        assert result.total_mentions == 10
        # Topics derived from word frequency
        assert len(result.top_topics) > 0
        assert "Share of voice" not in result.markdown

    def test_missing_sov(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(),
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
        )
        assert result.share_of_voice is None
        assert "Share of voice" not in result.markdown

    def test_first_week_no_previous(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(),
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
            previous_sentiment=None,
        )
        assert result.previous_sentiment is None
        assert "previous week" not in result.markdown

    def test_no_alerts(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(),
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
        )
        assert result.alerts_triggered == 0
        assert "Alerts triggered:** 0" in result.markdown

    def test_zero_mentions_raises(self):
        with pytest.raises(InsufficientDataError):
            generate_commodity_baseline(
                mentions_data={"mentions": []},
                sentiment_data={"buckets": []},
                sov_data=None,
                alerts_data=[],
            )

    def test_determinism(self):
        """Same input produces identical output."""
        kwargs = dict(
            mentions_data=_sample_mentions(20),
            sentiment_data=_sample_sentiment(),
            sov_data=_sample_sov(),
            alerts_data=_sample_alerts(),
            period_start=date(2026, 3, 10),
            period_end=date(2026, 3, 17),
        )
        result1 = generate_commodity_baseline(**kwargs)
        result2 = generate_commodity_baseline(**kwargs)
        assert result1.markdown == result2.markdown
        assert result1.total_mentions == result2.total_mentions
        assert result1.source_breakdown == result2.source_breakdown

    def test_author_concentration(self):
        """Detect when a single author dominates."""
        # Create 10 mentions, 8 from same author
        data = _sample_mentions(10)
        for m in data["mentions"][:8]:
            m["author_handle"] = "dominant_bot"
        result = generate_commodity_baseline(
            mentions_data=data,
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
        )
        assert result.author_concentration_flag is True

    def test_language_distribution(self):
        result = generate_commodity_baseline(
            mentions_data=_sample_mentions(10),
            sentiment_data=_sample_sentiment(),
            sov_data=None,
            alerts_data=[],
        )
        assert "en" in result.language_distribution
        assert "es" in result.language_distribution
