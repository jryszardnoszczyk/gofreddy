"""Tests for engagement prediction with cold-start tiers."""

from datetime import date

from src.monitoring.intelligence.engagement_predictor import predict_engagement
from src.monitoring.intelligence.models_analytics import EngagementPrediction, PerformancePatterns


def _make_patterns(total_posts: int = 25) -> PerformancePatterns:
    return PerformancePatterns(
        avg_engagement_rate=0.05,
        top_posts=[],
        worst_posts=[],
        content_type_breakdown={"text": 15, "video": 8, "image": 2},
        best_posting_hours=[9, 12, 15, 17, 20],
        best_posting_days=[1, 2, 3],
        follower_growth=500.0,
        engagement_trend="stable",
        engagement_spikes=[],
        velocity_flags=[],
        date_gaps=[],
        posting_frequency=3.5,
        avg_post_length=180.0,
        engagement_by_length_bucket={"short": 0.03, "medium": 0.05, "long": 0.04},
        total_posts=total_posts,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 25),
        markdown="test markdown",
    )


class TestPredictEngagement:
    def test_full_data_high_confidence(self):
        patterns = _make_patterns(25)
        result = predict_engagement(
            {"content_length": 180, "posting_hour": 9, "media_type": "text"},
            patterns,
        )
        assert isinstance(result, EngagementPrediction)
        assert result.confidence == "high"
        assert result.likely_performance in ("strong", "average", "weak")
        assert result.comparison_baseline == "personal_20+"

    def test_cold_start_zero_data(self):
        result = predict_engagement(
            {"content_length": 100, "posting_hour": 12},
            None,
            platform="twitter",
        )
        assert result.confidence == "low"
        assert result.likely_performance == "average"
        assert result.comparison_baseline == "platform_defaults"
        assert any("no personal data" in f for f in result.contributing_factors)

    def test_cold_start_partial(self):
        patterns = _make_patterns(10)
        result = predict_engagement(
            {"content_length": 100, "posting_hour": 9},
            patterns,
            platform="twitter",
        )
        assert result.confidence == "medium"
        assert result.comparison_baseline == "personal_<20"

    def test_optimal_features_strong(self):
        patterns = _make_patterns(25)
        result = predict_engagement(
            {"content_length": 180, "posting_hour": 9, "media_type": "text"},
            patterns,
        )
        # Best hour + avg length + most-used media type → should be strong
        assert result.likely_performance == "strong"

    def test_weak_features(self):
        patterns = _make_patterns(25)
        result = predict_engagement(
            {"content_length": 10, "posting_hour": 3, "media_type": "carousel"},
            patterns,
        )
        # Below avg length + bad hour + unused media type → weak
        assert result.likely_performance == "weak"

    def test_contributing_factors_human_readable(self):
        patterns = _make_patterns(25)
        result = predict_engagement(
            {"content_length": 200, "posting_hour": 9, "media_type": "text"},
            patterns,
        )
        assert len(result.contributing_factors) > 0
        for factor in result.contributing_factors:
            assert isinstance(factor, str)
            assert len(factor) > 10

    def test_cold_start_few_posts(self):
        patterns = _make_patterns(3)
        result = predict_engagement(
            {"content_length": 100, "posting_hour": 12},
            patterns,
            platform="instagram",
        )
        assert result.confidence == "low"
        assert result.comparison_baseline == "personal_<20"
