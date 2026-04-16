"""Tests for Evolution calculations module (PR-016)."""

from datetime import date

import pytest

from src.evolution.calculations import (
    _classify_shift,
    _cosine_similarity,
    _linear_regression_slope,
    _normalize,
    calculate_risk_trajectory,
    calculate_topic_shift,
)


class TestCosineSimilarity:
    """Tests for _cosine_similarity function."""

    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        vec = {"a": 0.5, "b": 0.3, "c": 0.2}
        result = _cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """Test cosine similarity of completely different vectors."""
        vec1 = {"a": 1.0}
        vec2 = {"b": 1.0}
        result = _cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0)

    def test_similar_vectors(self):
        """Test cosine similarity of similar vectors."""
        vec1 = {"fitness": 0.6, "lifestyle": 0.4}
        vec2 = {"fitness": 0.5, "lifestyle": 0.4, "travel": 0.1}
        result = _cosine_similarity(vec1, vec2)
        # Should be high but not 1.0
        assert result > 0.8
        assert result < 1.0

    def test_empty_vectors(self):
        """Test cosine similarity with empty vectors."""
        result = _cosine_similarity({}, {})
        assert result == 0.0

    def test_one_empty_vector(self):
        """Test cosine similarity when one vector is empty."""
        vec = {"a": 1.0}
        result = _cosine_similarity(vec, {})
        assert result == 0.0


class TestNormalize:
    """Tests for _normalize function."""

    def test_basic_normalization(self):
        """Test basic count normalization."""
        counts = {"a": 50, "b": 30, "c": 20}
        result = _normalize(counts)
        assert result["a"] == pytest.approx(0.5)
        assert result["b"] == pytest.approx(0.3)
        assert result["c"] == pytest.approx(0.2)

    def test_empty_dict(self):
        """Test normalization of empty dict."""
        result = _normalize({})
        assert result == {}

    def test_single_item(self):
        """Test normalization of single item."""
        result = _normalize({"only": 100})
        assert result["only"] == 1.0

    def test_all_zeros(self):
        """Test normalization when all values are zero."""
        result = _normalize({"a": 0, "b": 0})
        assert result["a"] == 0.0
        assert result["b"] == 0.0


class TestClassifyShift:
    """Tests for _classify_shift function."""

    def test_significant_pivot(self):
        """Test significant pivot classification."""
        # Similarity between 0.5 and 0.7 is significant pivot
        result = _classify_shift(0.6)
        assert result == "significant_pivot"

        result = _classify_shift(0.5)
        assert result == "significant_pivot"

    def test_complete_rebrand(self):
        """Test complete rebrand classification."""
        # Similarity below 0.5 is complete rebrand
        result = _classify_shift(0.4)
        assert result == "complete_rebrand"

        result = _classify_shift(0.0)
        assert result == "complete_rebrand"


class TestLinearRegressionSlope:
    """Tests for _linear_regression_slope function."""

    def test_increasing_values(self):
        """Test slope of increasing values."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _linear_regression_slope(values)
        assert result == pytest.approx(1.0)

    def test_decreasing_values(self):
        """Test slope of decreasing values."""
        values = [5.0, 4.0, 3.0, 2.0, 1.0]
        result = _linear_regression_slope(values)
        assert result == pytest.approx(-1.0)

    def test_flat_values(self):
        """Test slope of constant values."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = _linear_regression_slope(values)
        assert result == pytest.approx(0.0)

    def test_single_value(self):
        """Test slope with single value."""
        result = _linear_regression_slope([5.0])
        assert result == 0.0

    def test_empty_list(self):
        """Test slope with empty list."""
        result = _linear_regression_slope([])
        assert result == 0.0

    def test_two_values(self):
        """Test slope with exactly two values."""
        result = _linear_regression_slope([1.0, 3.0])
        assert result == pytest.approx(2.0)


class TestCalculateTopicShift:
    """Tests for calculate_topic_shift function."""

    def test_no_shift_similar_topics(self):
        """Test that similar topics don't trigger a shift."""
        old = {"fitness": 50, "lifestyle": 30, "health": 20}
        new = {"fitness": 45, "lifestyle": 35, "health": 20}
        result = calculate_topic_shift(old, new, date(2026, 2, 1))
        # High similarity should return None
        assert result is None

    def test_significant_pivot(self):
        """Test significant pivot detection."""
        old = {"fitness": 80, "health": 20}
        new = {"fitness": 30, "lifestyle": 50, "travel": 20}
        result = calculate_topic_shift(old, new, date(2026, 2, 1))
        assert result is not None
        assert result.shift_type in ["significant_pivot", "complete_rebrand"]
        assert result.detected_at == date(2026, 2, 1)
        assert result.similarity_score < 0.7

    def test_complete_rebrand(self):
        """Test complete rebrand detection."""
        old = {"fitness": 100}
        new = {"travel": 50, "food": 50}
        result = calculate_topic_shift(old, new, date(2026, 2, 1))
        assert result is not None
        assert result.shift_type == "complete_rebrand"
        assert result.similarity_score < 0.5

    def test_empty_old_topics(self):
        """Test with empty old topics."""
        result = calculate_topic_shift({}, {"fitness": 100}, date(2026, 2, 1))
        assert result is None

    def test_empty_new_topics(self):
        """Test with empty new topics."""
        result = calculate_topic_shift({"fitness": 100}, {}, date(2026, 2, 1))
        assert result is None

    def test_custom_threshold(self):
        """Test with custom threshold."""
        old = {"fitness": 60, "lifestyle": 40}
        new = {"fitness": 50, "lifestyle": 30, "travel": 20}

        # With default threshold (0.7), no shift
        result_default = calculate_topic_shift(old, new, date(2026, 2, 1))

        # With stricter threshold (0.95), shift detected
        result_strict = calculate_topic_shift(old, new, date(2026, 2, 1), threshold=0.95)
        assert result_strict is not None


class TestCalculateRiskTrajectory:
    """Tests for calculate_risk_trajectory function."""

    def test_deteriorating_trajectory(self):
        """Test deteriorating risk trajectory."""
        risk_scores = [
            (date(2026, 1, 1), 0.1, 5),
            (date(2026, 1, 15), 0.3, 6),
            (date(2026, 2, 1), 0.5, 7),
            (date(2026, 2, 15), 0.7, 8),
        ]
        result = calculate_risk_trajectory(risk_scores)
        assert result.direction == "deteriorating"
        assert result.current_score == 0.7
        assert result.trend_slope > 0.05
        assert len(result.data_points) == 4

    def test_improving_trajectory(self):
        """Test improving risk trajectory."""
        risk_scores = [
            (date(2026, 1, 1), 0.8, 5),
            (date(2026, 1, 15), 0.6, 6),
            (date(2026, 2, 1), 0.4, 7),
            (date(2026, 2, 15), 0.2, 8),
        ]
        result = calculate_risk_trajectory(risk_scores)
        assert result.direction == "improving"
        assert result.current_score == 0.2
        assert result.trend_slope < -0.05

    def test_stable_trajectory(self):
        """Test stable risk trajectory."""
        risk_scores = [
            (date(2026, 1, 1), 0.5, 5),
            (date(2026, 1, 15), 0.52, 5),
            (date(2026, 2, 1), 0.48, 5),
            (date(2026, 2, 15), 0.51, 5),
        ]
        result = calculate_risk_trajectory(risk_scores)
        assert result.direction == "stable"
        assert abs(result.trend_slope) <= 0.05

    def test_single_data_point(self):
        """Test with single data point."""
        risk_scores = [(date(2026, 2, 1), 0.5, 10)]
        result = calculate_risk_trajectory(risk_scores)
        assert result.direction == "stable"
        assert result.current_score == 0.5
        assert result.trend_slope == 0.0
        assert len(result.data_points) == 1

    def test_empty_data(self):
        """Test with empty data."""
        result = calculate_risk_trajectory([])
        assert result.direction == "stable"
        assert result.current_score == 0.0
        assert result.trend_slope == 0.0
        assert result.data_points == []

    def test_moving_average(self):
        """Test moving average calculation with sufficient data."""
        risk_scores = [
            (date(2026, 1, 1 + i), 0.5, 1) for i in range(10)
        ]
        result = calculate_risk_trajectory(risk_scores)
        # With 10 data points, moving average should be calculated
        assert result.moving_average_30d is not None
        assert result.moving_average_30d == pytest.approx(0.5)

    def test_no_moving_average_insufficient_data(self):
        """Test no moving average with insufficient data."""
        risk_scores = [
            (date(2026, 1, 1), 0.3, 1),
            (date(2026, 1, 2), 0.4, 1),
            (date(2026, 1, 3), 0.5, 1),
        ]
        result = calculate_risk_trajectory(risk_scores)
        # With only 3 data points, no moving average
        assert result.moving_average_30d is None
