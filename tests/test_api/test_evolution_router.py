"""Tests for Evolution API router (PR-016)."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_evolution_service
from src.api.exceptions import register_exception_handlers
from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier
from src.common.enums import Platform
from src.evolution.models import (
    EvolutionResponse,
    RiskPoint,
    RiskTrajectory,
    TopicShift,
)


class TestEvolutionResponseFormat:
    """Tests for evolution response format validation."""

    @pytest.fixture
    def sample_evolution_response(self):
        """Create a sample evolution response."""
        return EvolutionResponse(
            creator_username="fitnessjen",
            platform=Platform.TIKTOK,
            period_days=90,
            topic_shifts=[
                TopicShift(
                    detected_at=date(2026, 2, 1),
                    from_topics={"fitness": 0.7, "health": 0.3},
                    to_topics={"lifestyle": 0.5, "fitness": 0.3, "travel": 0.2},
                    similarity_score=0.45,
                    shift_type="significant_pivot",
                )
            ],
            risk_trajectory=RiskTrajectory(
                direction="stable",
                current_score=0.15,
                moving_average_30d=0.18,
                trend_slope=-0.02,
                data_points=[
                    RiskPoint(
                        date=date(2026, 1, 15),
                        risk_score=0.2,
                        videos_in_window=5,
                        moderation_flags_count=1,
                    ),
                    RiskPoint(
                        date=date(2026, 2, 1),
                        risk_score=0.15,
                        videos_in_window=8,
                        moderation_flags_count=0,
                    ),
                ],
            ),
            current_topics={"lifestyle": 0.5, "fitness": 0.3, "travel": 0.2},
            current_risk_level="low",
            videos_analyzed=25,
            date_range_start=date(2025, 11, 5),
            date_range_end=date(2026, 2, 5),
            confidence_level="medium",
            warnings=[],
        )

    @pytest.fixture
    def pro_billing_context(self):
        """Create a Pro tier billing context."""
        user = User(
            id=uuid4(),
            email="pro@example.com",
            stripe_customer_id="cus_pro123",
            created_at=datetime(2026, 1, 1),
        )
        usage = UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime(2026, 2, 1),
            period_end=datetime(2026, 2, 28),
            videos_used=100,
            videos_limit=50000,
        )
        return BillingContext(
            user=user,
            tier=Tier.PRO,
            usage_period=usage,
            subscription=None,
        )

    @pytest.fixture
    def free_billing_context(self):
        """Create a Free tier billing context."""
        user = User(
            id=uuid4(),
            email="free@example.com",
            stripe_customer_id=None,
            created_at=datetime(2026, 1, 1),
        )
        usage = UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime(2026, 2, 1),
            period_end=datetime(2026, 2, 28),
            videos_used=50,
            videos_limit=100,
        )
        return BillingContext(
            user=user,
            tier=Tier.FREE,
            usage_period=usage,
            subscription=None,
        )

    def test_response_includes_topic_shifts(self, sample_evolution_response):
        """Test that response includes topic shifts."""
        data = sample_evolution_response.model_dump()
        assert "topic_shifts" in data
        assert len(data["topic_shifts"]) == 1
        assert data["topic_shifts"][0]["shift_type"] == "significant_pivot"

    def test_response_includes_risk_trajectory(self, sample_evolution_response):
        """Test that response includes risk trajectory."""
        data = sample_evolution_response.model_dump()
        assert "risk_trajectory" in data
        assert data["risk_trajectory"]["direction"] == "stable"
        assert data["risk_trajectory"]["current_score"] == 0.15

    def test_response_includes_current_state(self, sample_evolution_response):
        """Test that response includes current state summary."""
        data = sample_evolution_response.model_dump()
        assert "current_topics" in data
        assert "current_risk_level" in data
        assert data["current_risk_level"] == "low"
        assert "lifestyle" in data["current_topics"]

    def test_response_includes_confidence_level(self, sample_evolution_response):
        """Test that response includes confidence level."""
        assert sample_evolution_response.confidence_level == "medium"

    def test_response_includes_date_range(self, sample_evolution_response):
        """Test that response includes date range."""
        assert sample_evolution_response.date_range_start == date(2025, 11, 5)
        assert sample_evolution_response.date_range_end == date(2026, 2, 5)

    def test_response_serialization(self, sample_evolution_response):
        """Test that response serializes correctly to JSON."""
        json_data = sample_evolution_response.model_dump_json()
        assert "fitnessjen" in json_data
        assert "lifestyle" in json_data
        assert "stable" in json_data
        assert "medium" in json_data

    def test_pro_tier_has_access(self, pro_billing_context):
        """Test Pro tier billing context has correct tier."""
        assert pro_billing_context.tier == Tier.PRO
        assert pro_billing_context.tier != Tier.FREE

    def test_free_tier_denied_access(self, free_billing_context):
        """Test Free tier billing context has correct tier."""
        assert free_billing_context.tier == Tier.FREE
        assert free_billing_context.tier != Tier.PRO


class TestEvolutionResponseEdgeCases:
    """Tests for evolution response edge cases."""

    def test_response_with_warnings(self):
        """Test response with data quality warnings."""
        response = EvolutionResponse(
            creator_username="newcreator",
            platform=Platform.INSTAGRAM,
            period_days=30,
            videos_analyzed=7,
            confidence_level="low",
            warnings=["Topic shift detection requires 10+ videos, only 7 available"],
        )
        assert len(response.warnings) == 1
        assert "10+" in response.warnings[0]

    def test_response_with_no_shifts(self):
        """Test response when no topic shifts detected."""
        response = EvolutionResponse(
            creator_username="consistent",
            platform=Platform.YOUTUBE,
            period_days=90,
            topic_shifts=[],
            risk_trajectory=RiskTrajectory(
                direction="stable",
                current_score=0.1,
                trend_slope=0.0,
            ),
            current_topics={"gaming": 0.9, "tech": 0.1},
            current_risk_level="low",
            videos_analyzed=50,
            confidence_level="high",
        )
        assert response.topic_shifts == []

    def test_response_all_platforms(self):
        """Test evolution responses can be created for all platforms."""
        for platform in Platform:
            response = EvolutionResponse(
                creator_username="creator",
                platform=platform,
                period_days=90,
                videos_analyzed=10,
                confidence_level="medium",
            )
            assert response.platform == platform

    def test_response_all_period_options(self):
        """Test evolution responses for all period options."""
        for period_days in [30, 90, 180, 365]:
            response = EvolutionResponse(
                creator_username="creator",
                platform=Platform.TIKTOK,
                period_days=period_days,
                videos_analyzed=10,
                confidence_level="medium",
            )
            assert response.period_days == period_days

    def test_response_all_risk_levels(self):
        """Test evolution responses for all risk levels."""
        for level in ["low", "medium", "high", "critical"]:
            response = EvolutionResponse(
                creator_username="creator",
                platform=Platform.TIKTOK,
                period_days=90,
                videos_analyzed=10,
                confidence_level="medium",
                current_risk_level=level,
            )
            assert response.current_risk_level == level

    def test_response_all_trajectory_directions(self):
        """Test evolution responses for all trajectory directions."""
        for direction in ["improving", "stable", "deteriorating"]:
            response = EvolutionResponse(
                creator_username="creator",
                platform=Platform.TIKTOK,
                period_days=90,
                risk_trajectory=RiskTrajectory(
                    direction=direction,
                    current_score=0.5,
                    trend_slope=0.0,
                ),
                videos_analyzed=10,
                confidence_level="medium",
            )
            assert response.risk_trajectory.direction == direction

    def test_response_all_shift_types(self):
        """Test topic shifts with all shift types."""
        for shift_type in ["minor_expansion", "significant_pivot", "complete_rebrand"]:
            shift = TopicShift(
                detected_at=date(2026, 2, 1),
                from_topics={"old": 1.0},
                to_topics={"new": 1.0},
                similarity_score=0.3,
                shift_type=shift_type,
            )
            response = EvolutionResponse(
                creator_username="creator",
                platform=Platform.TIKTOK,
                period_days=90,
                topic_shifts=[shift],
                videos_analyzed=20,
                confidence_level="medium",
            )
            assert response.topic_shifts[0].shift_type == shift_type


class TestEvolutionTierGating:
    """Tests for evolution endpoint tier gating logic."""

    def test_tier_comparison_pro(self):
        """Test that Pro tier is correctly identified."""
        assert Tier.PRO != Tier.FREE

    def test_tier_comparison_non_pro(self):
        """Test that non-Pro tiers are correctly identified."""
        # Current v1 only has FREE and PRO tiers
        non_pro_tiers = [Tier.FREE]
        for tier in non_pro_tiers:
            assert tier != Tier.PRO

    def test_tier_value_for_error_response(self):
        """Test tier values are available for error response."""
        assert Tier.FREE.value == "free"
        assert Tier.PRO.value == "pro"


class TestEvolutionPathParameters:
    """Tests for evolution endpoint path parameters."""

    def test_valid_username_patterns(self):
        """Test valid username patterns match regex."""
        import re
        pattern = r"^[a-zA-Z0-9._-]+$"

        valid_usernames = [
            "fitnessjen",
            "user123",
            "john.doe",
            "jane_doe",
            "test-user",
            "A1B2C3",
            "user.name_123-test",
        ]

        for username in valid_usernames:
            assert re.match(pattern, username), f"Valid username rejected: {username}"

    def test_invalid_username_patterns(self):
        """Test invalid username patterns don't match regex."""
        import re
        pattern = r"^[a-zA-Z0-9._-]+$"
        invalid_usernames = [
            "",
            "user name",  # space
            "user@name",  # @
            "user!name",  # !
            "user/name",  # /
            "user\\name",  # backslash
        ]

        for username in invalid_usernames:
            assert not re.match(pattern, username), f"Invalid username accepted: {username}"


@pytest.mark.mock_required
class TestEvolutionTierGateHTTP:
    """HTTP tests for GET /v1/creators/{platform}/{username}/evolution."""

    def _free_context(self) -> BillingContext:
        now = datetime(2026, 2, 10)
        user = User(
            id=uuid4(),
            email="free@evo.test",
            stripe_customer_id=None,
            created_at=now,
        )
        usage = UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=now,
            period_end=now,
            videos_used=10,
            videos_limit=100,
        )
        return BillingContext(user=user, tier=Tier.FREE, usage_period=usage, subscription=None)

    def _pro_context(self) -> BillingContext:
        now = datetime(2026, 2, 10)
        user = User(
            id=uuid4(),
            email="pro@evo.test",
            stripe_customer_id="cus_pro",
            created_at=now,
        )
        usage = UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=now,
            period_end=now,
            videos_used=10,
            videos_limit=50000,
        )
        return BillingContext(user=user, tier=Tier.PRO, usage_period=usage, subscription=None)

    def test_free_tier_error_includes_full_contract(self) -> None:
        from src.api.routers.evolution import router

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")

        mock_service = MagicMock()
        mock_service.get_evolution = AsyncMock()
        app.dependency_overrides[get_billing_context] = lambda: self._free_context()
        app.dependency_overrides[get_evolution_service] = lambda: mock_service

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/creators/tiktok/testuser/evolution?period=90d")
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["required_tier"] == "pro"
        assert error["current_tier"] == "free"
        assert error["feature"] == "evolution_tracking"
        assert "upgrade_url" not in error

    def test_pro_tier_passes_to_service(self) -> None:
        from src.api.routers.evolution import router

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")

        mock_service = MagicMock()
        mock_service.get_evolution = AsyncMock(
            return_value=EvolutionResponse(
                creator_username="testuser",
                platform=Platform.TIKTOK,
                period_days=90,
                videos_analyzed=12,
                confidence_level="medium",
            )
        )
        app.dependency_overrides[get_billing_context] = lambda: self._pro_context()
        app.dependency_overrides[get_evolution_service] = lambda: mock_service

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/creators/tiktok/testuser/evolution?period=90d")
        assert response.status_code == 200
        assert response.json()["creator_username"] == "testuser"
