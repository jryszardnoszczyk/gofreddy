"""Tests for brand exposure analytics — interval-merge and aggregation.

Tests the pure computation functions in src/brands/exposure.py:
- merge_intervals: overlapping, adjacent, contained, disjoint intervals
- compute_brand_exposure: screen time, source/sentiment/context breakdown
- aggregate_multi_video: cross-video aggregation, sentiment trends
"""

from src.brands.exposure import (
    aggregate_multi_video,
    compute_brand_exposure,
    merge_intervals,
)
from src.schemas import (
    BrandAnalysis,
    BrandContext,
    BrandDetectionSource,
    BrandExposureSummary,
    BrandMention,
    BrandSentiment,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _mention(
    brand: str = "Nike",
    source: BrandDetectionSource = BrandDetectionSource.SPEECH,
    sentiment: BrandSentiment = BrandSentiment.POSITIVE,
    context: BrandContext = BrandContext.ENDORSEMENT,
    start: str | None = "0:10",
    end: str | None = "0:20",
    is_competitor: bool = False,
) -> BrandMention:
    return BrandMention(
        brand_name=brand,
        detection_source=source,
        confidence=0.9,
        timestamp_start=start,
        timestamp_end=end,
        sentiment=sentiment,
        context=context,
        evidence="test evidence",
        is_competitor=is_competitor,
    )


def _analysis(*mentions: BrandMention) -> BrandAnalysis:
    return BrandAnalysis(
        video_id="test_video",
        brand_mentions=list(mentions),
        overall_confidence=0.9,
    )


# ── merge_intervals tests ───────────────────────────────────────────────────


class TestMergeIntervals:
    def test_empty_input(self):
        assert merge_intervals([]) == []

    def test_single_interval(self):
        assert merge_intervals([(0, 10)]) == [(0, 10)]

    def test_non_overlapping(self):
        result = merge_intervals([(0, 5), (10, 15)])
        assert result == [(0, 5), (10, 15)]

    def test_overlapping(self):
        result = merge_intervals([(0, 10), (5, 15)])
        assert result == [(0, 15)]

    def test_fully_contained(self):
        result = merge_intervals([(0, 20), (5, 10)])
        assert result == [(0, 20)]

    def test_adjacent(self):
        """Adjacent intervals (end == start of next) should merge."""
        result = merge_intervals([(0, 5), (5, 10)])
        assert result == [(0, 10)]

    def test_unsorted_input(self):
        result = merge_intervals([(10, 15), (0, 5), (3, 8)])
        assert result == [(0, 8), (10, 15)]

    def test_multiple_overlapping(self):
        result = merge_intervals([(0, 3), (2, 6), (5, 9), (15, 20)])
        assert result == [(0, 9), (15, 20)]


# ── compute_brand_exposure tests ─────────────────────────────────────────────


class TestComputeBrandExposure:
    def test_no_mentions(self):
        analysis = _analysis()
        result = compute_brand_exposure(analysis)
        assert result == {}

    def test_single_mention_with_timestamps(self):
        m = _mention(start="0:10", end="0:20")
        result = compute_brand_exposure(_analysis(m))
        assert "Nike" in result
        exposure = result["Nike"]
        assert exposure.total_mentions == 1
        assert exposure.total_screen_time_seconds == 10
        assert exposure.source_breakdown == {"speech": 1}
        assert exposure.sentiment_distribution == {"positive": 1.0}
        assert exposure.context_distribution == {"endorsement": 1}
        assert exposure.is_competitor is False

    def test_null_timestamps_point_event(self):
        """Null timestamps → point event at 0:00 with 1s duration."""
        m = _mention(start=None, end=None)
        result = compute_brand_exposure(_analysis(m))
        assert result["Nike"].total_screen_time_seconds == 1

    def test_null_end_timestamp(self):
        """Null timestamp_end → 1s point event from start."""
        m = _mention(start="1:00", end=None)
        result = compute_brand_exposure(_analysis(m))
        assert result["Nike"].total_screen_time_seconds == 1

    def test_overlapping_mentions_no_double_counting(self):
        m1 = _mention(start="0:10", end="0:30")
        m2 = _mention(start="0:20", end="0:40")
        result = compute_brand_exposure(_analysis(m1, m2))
        assert result["Nike"].total_screen_time_seconds == 30  # 0:10 to 0:40
        assert result["Nike"].total_mentions == 2

    def test_multiple_brands_separate(self):
        m1 = _mention(brand="Nike", start="0:10", end="0:20")
        m2 = _mention(brand="Adidas", start="0:30", end="0:40")
        result = compute_brand_exposure(_analysis(m1, m2))
        assert "Nike" in result
        assert "Adidas" in result
        assert result["Nike"].total_screen_time_seconds == 10
        assert result["Adidas"].total_screen_time_seconds == 10

    def test_case_insensitive_brand_grouping(self):
        """'Nike' and 'nike' should group together."""
        m1 = _mention(brand="Nike", start="0:10", end="0:20")
        m2 = _mention(brand="nike", start="0:30", end="0:40")
        result = compute_brand_exposure(_analysis(m1, m2))
        # Should be one brand entry (using first mention's casing)
        assert len(result) == 1
        assert "Nike" in result
        assert result["Nike"].total_mentions == 2
        assert result["Nike"].total_screen_time_seconds == 20

    def test_is_competitor_propagation(self):
        """Any mention with is_competitor=True → summary is_competitor=True."""
        m1 = _mention(is_competitor=False)
        m2 = _mention(is_competitor=True)
        result = compute_brand_exposure(_analysis(m1, m2))
        assert result["Nike"].is_competitor is True

    def test_source_breakdown_counts(self):
        m1 = _mention(source=BrandDetectionSource.SPEECH)
        m2 = _mention(source=BrandDetectionSource.SPEECH)
        m3 = _mention(source=BrandDetectionSource.VISUAL_LOGO)
        result = compute_brand_exposure(_analysis(m1, m2, m3))
        assert result["Nike"].source_breakdown == {"speech": 2, "visual_logo": 1}

    def test_sentiment_distribution_ratios(self):
        m1 = _mention(sentiment=BrandSentiment.POSITIVE)
        m2 = _mention(sentiment=BrandSentiment.POSITIVE)
        m3 = _mention(sentiment=BrandSentiment.NEUTRAL)
        result = compute_brand_exposure(_analysis(m1, m2, m3))
        dist = result["Nike"].sentiment_distribution
        assert abs(dist["positive"] - 0.67) < 0.01
        assert abs(dist["neutral"] - 0.33) < 0.01

    def test_context_distribution_counts(self):
        m1 = _mention(context=BrandContext.ENDORSEMENT)
        m2 = _mention(context=BrandContext.BACKGROUND)
        m3 = _mention(context=BrandContext.ENDORSEMENT)
        result = compute_brand_exposure(_analysis(m1, m2, m3))
        assert result["Nike"].context_distribution == {"endorsement": 2, "background": 1}


# ── aggregate_multi_video tests ──────────────────────────────────────────────


class TestAggregateMultiVideo:
    def test_empty_input(self):
        result = aggregate_multi_video([])
        assert result == {}

    def test_single_video(self):
        exposure = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=3,
                total_screen_time_seconds=30,
                source_breakdown={"speech": 2, "visual_logo": 1},
                sentiment_distribution={"positive": 0.67, "neutral": 0.33},
                context_distribution={"endorsement": 2, "background": 1},
                is_competitor=False,
            )
        }
        result = aggregate_multi_video([("aid-1", exposure)])
        assert "Nike" in result
        assert result["Nike"].total_mentions == 3
        assert result["Nike"].total_screen_time_seconds == 30
        assert result["Nike"].average_screen_time_per_video == 30.0
        assert result["Nike"].videos_appearing_in == 1

    def test_multi_video_aggregation(self):
        exp1 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=2,
                total_screen_time_seconds=20,
                source_breakdown={"speech": 2},
                sentiment_distribution={"positive": 1.0},
                context_distribution={"endorsement": 2},
                is_competitor=False,
            )
        }
        exp2 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=1,
                total_screen_time_seconds=10,
                source_breakdown={"visual_logo": 1},
                sentiment_distribution={"neutral": 1.0},
                context_distribution={"background": 1},
                is_competitor=False,
            )
        }
        result = aggregate_multi_video([("aid-1", exp1), ("aid-2", exp2)])
        nike = result["Nike"]
        assert nike.total_mentions == 3
        assert nike.total_screen_time_seconds == 30
        assert nike.average_screen_time_per_video == 15.0
        assert nike.videos_appearing_in == 2
        assert nike.source_breakdown == {"speech": 2, "visual_logo": 1}

    def test_sentiment_trend_chronological(self):
        exp1 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=1,
                total_screen_time_seconds=10,
                source_breakdown={"speech": 1},
                sentiment_distribution={"positive": 1.0},
                context_distribution={"endorsement": 1},
                is_competitor=False,
            )
        }
        exp2 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=1,
                total_screen_time_seconds=5,
                source_breakdown={"speech": 1},
                sentiment_distribution={"negative": 1.0},
                context_distribution={"criticism": 1},
                is_competitor=False,
            )
        }
        result = aggregate_multi_video([("aid-1", exp1), ("aid-2", exp2)])
        assert result["Nike"].sentiment_trend == {"aid-1": "positive", "aid-2": "negative"}

    def test_is_competitor_cross_video(self):
        exp1 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=1,
                total_screen_time_seconds=10,
                source_breakdown={"speech": 1},
                sentiment_distribution={"positive": 1.0},
                context_distribution={"endorsement": 1},
                is_competitor=False,
            )
        }
        exp2 = {
            "Nike": BrandExposureSummary(
                brand_name="Nike",
                total_mentions=1,
                total_screen_time_seconds=5,
                source_breakdown={"speech": 1},
                sentiment_distribution={"positive": 1.0},
                context_distribution={"endorsement": 1},
                is_competitor=True,
            )
        }
        result = aggregate_multi_video([("aid-1", exp1), ("aid-2", exp2)])
        assert result["Nike"].is_competitor is True
