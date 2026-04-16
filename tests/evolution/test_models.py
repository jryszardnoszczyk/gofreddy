"""Tests for Evolution models module (PR-016)."""

from datetime import date

import pytest
from pydantic import ValidationError

from src.common.enums import Platform
from src.evolution.models import (
    ConfidenceLevel,
    EvolutionResponse,
    RiskLevel,
    RiskPoint,
    RiskTrajectory,
    TopicShift,
    TrendDirection,
    get_evolution_confidence,
)


class TestConfidenceLevelCalculation:
    """Tests for get_evolution_confidence function."""

    def test_confidence_low(self):
        """Test low confidence with sample < 10."""
        assert get_evolution_confidence(0) == "low"
        assert get_evolution_confidence(5) == "low"
        assert get_evolution_confidence(9) == "low"

    def test_confidence_medium(self):
        """Test medium confidence with sample 10-29."""
        assert get_evolution_confidence(10) == "medium"
        assert get_evolution_confidence(20) == "medium"
        assert get_evolution_confidence(29) == "medium"

    def test_confidence_high(self):
        """Test high confidence with sample >= 30."""
        assert get_evolution_confidence(30) == "high"
        assert get_evolution_confidence(100) == "high"
        assert get_evolution_confidence(1000) == "high"


class TestTopicShiftModel:
    """Tests for TopicShift model."""

    def test_valid_topic_shift(self):
        """Test creating a valid topic shift."""
        shift = TopicShift(
            detected_at=date(2026, 2, 5),
            from_topics={"fitness": 0.6, "lifestyle": 0.4},
            to_topics={"travel": 0.7, "food": 0.3},
            similarity_score=0.3,
            shift_type="significant_pivot",
        )
        assert shift.detected_at == date(2026, 2, 5)
        assert shift.from_topics["fitness"] == 0.6
        assert shift.to_topics["travel"] == 0.7
        assert shift.similarity_score == 0.3
        assert shift.shift_type == "significant_pivot"

    def test_similarity_score_bounds(self):
        """Test that similarity score must be between 0 and 1."""
        # Valid at bounds
        TopicShift(
            detected_at=date(2026, 1, 1),
            from_topics={"a": 1.0},
            to_topics={"b": 1.0},
            similarity_score=0.0,
            shift_type="complete_rebrand",
        )
        TopicShift(
            detected_at=date(2026, 1, 1),
            from_topics={"a": 1.0},
            to_topics={"b": 1.0},
            similarity_score=1.0,
            shift_type="minor_expansion",
        )

        # Invalid below 0
        with pytest.raises(ValidationError):
            TopicShift(
                detected_at=date(2026, 1, 1),
                from_topics={},
                to_topics={},
                similarity_score=-0.1,
                shift_type="significant_pivot",
            )

        # Invalid above 1
        with pytest.raises(ValidationError):
            TopicShift(
                detected_at=date(2026, 1, 1),
                from_topics={},
                to_topics={},
                similarity_score=1.1,
                shift_type="significant_pivot",
            )

    def test_shift_types(self):
        """Test all valid shift types."""
        for shift_type in ["minor_expansion", "significant_pivot", "complete_rebrand"]:
            shift = TopicShift(
                detected_at=date(2026, 1, 1),
                from_topics={"a": 1.0},
                to_topics={"b": 1.0},
                similarity_score=0.5,
                shift_type=shift_type,
            )
            assert shift.shift_type == shift_type


class TestRiskPointModel:
    """Tests for RiskPoint model."""

    def test_valid_risk_point(self):
        """Test creating a valid risk point."""
        point = RiskPoint(
            date=date(2026, 2, 5),
            risk_score=0.65,
            videos_in_window=10,
            moderation_flags_count=3,
        )
        assert point.date == date(2026, 2, 5)
        assert point.risk_score == 0.65
        assert point.videos_in_window == 10
        assert point.moderation_flags_count == 3

    def test_risk_score_bounds(self):
        """Test that risk score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            RiskPoint(
                date=date(2026, 1, 1),
                risk_score=-0.1,
                videos_in_window=1,
            )

        with pytest.raises(ValidationError):
            RiskPoint(
                date=date(2026, 1, 1),
                risk_score=1.1,
                videos_in_window=1,
            )

    def test_default_moderation_flags(self):
        """Test default value for moderation_flags_count."""
        point = RiskPoint(
            date=date(2026, 1, 1),
            risk_score=0.5,
            videos_in_window=1,
        )
        assert point.moderation_flags_count == 0


class TestRiskTrajectoryModel:
    """Tests for RiskTrajectory model."""

    def test_valid_risk_trajectory(self):
        """Test creating a valid risk trajectory."""
        trajectory = RiskTrajectory(
            direction="deteriorating",
            current_score=0.7,
            moving_average_30d=0.65,
            trend_slope=0.08,
            data_points=[
                RiskPoint(date=date(2026, 1, 1), risk_score=0.5, videos_in_window=5),
                RiskPoint(date=date(2026, 2, 1), risk_score=0.7, videos_in_window=8),
            ],
        )
        assert trajectory.direction == "deteriorating"
        assert trajectory.current_score == 0.7
        assert trajectory.moving_average_30d == 0.65
        assert trajectory.trend_slope == 0.08
        assert len(trajectory.data_points) == 2

    def test_trajectory_directions(self):
        """Test all valid trajectory directions."""
        for direction in ["improving", "stable", "deteriorating"]:
            trajectory = RiskTrajectory(
                direction=direction,
                current_score=0.5,
                trend_slope=0.0,
            )
            assert trajectory.direction == direction

    def test_default_values(self):
        """Test default values for optional fields."""
        trajectory = RiskTrajectory(
            direction="stable",
            current_score=0.5,
            trend_slope=0.0,
        )
        assert trajectory.moving_average_30d is None
        assert trajectory.data_points == []


class TestEvolutionResponseModel:
    """Tests for EvolutionResponse model."""

    def test_valid_evolution_response(self):
        """Test creating a valid evolution response."""
        response = EvolutionResponse(
            creator_username="fitnessjen",
            platform=Platform.TIKTOK,
            period_days=90,
            topic_shifts=[
                TopicShift(
                    detected_at=date(2026, 2, 1),
                    from_topics={"fitness": 0.8},
                    to_topics={"lifestyle": 0.7},
                    similarity_score=0.4,
                    shift_type="significant_pivot",
                )
            ],
            risk_trajectory=RiskTrajectory(
                direction="stable",
                current_score=0.2,
                trend_slope=0.01,
            ),
            current_topics={"lifestyle": 0.6, "fitness": 0.4},
            current_risk_level="low",
            videos_analyzed=25,
            date_range_start=date(2025, 11, 1),
            date_range_end=date(2026, 2, 1),
            confidence_level="medium",
            warnings=[],
        )
        assert response.creator_username == "fitnessjen"
        assert response.platform == Platform.TIKTOK
        assert response.period_days == 90
        assert len(response.topic_shifts) == 1
        assert response.risk_trajectory is not None
        assert response.videos_analyzed == 25
        assert response.confidence_level == "medium"

    def test_response_with_warnings(self):
        """Test response with data quality warnings."""
        response = EvolutionResponse(
            creator_username="newcreator",
            platform=Platform.INSTAGRAM,
            period_days=30,
            videos_analyzed=7,
            confidence_level="low",
            warnings=[
                "Topic shift detection requires 10+ videos, only 7 available"
            ],
        )
        assert len(response.warnings) == 1
        assert "10+" in response.warnings[0]

    def test_response_default_values(self):
        """Test default values for optional fields."""
        response = EvolutionResponse(
            creator_username="test",
            platform=Platform.YOUTUBE,
            period_days=90,
            videos_analyzed=5,
            confidence_level="low",
        )
        assert response.topic_shifts == []
        assert response.risk_trajectory is None
        assert response.current_topics == {}
        assert response.current_risk_level is None
        assert response.date_range_start is None
        assert response.date_range_end is None
        assert response.warnings == []

    def test_all_risk_levels(self):
        """Test all valid risk levels."""
        for level in ["low", "medium", "high", "critical"]:
            response = EvolutionResponse(
                creator_username="test",
                platform=Platform.TIKTOK,
                period_days=90,
                videos_analyzed=10,
                confidence_level="medium",
                current_risk_level=level,
            )
            assert response.current_risk_level == level
