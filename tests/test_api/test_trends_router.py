"""Tests for Trends API router (PR-015)."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_trend_service
from src.api.exceptions import register_exception_handlers
from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier
from src.common.enums import Platform
from src.trends.models import TrendingHashtag, TrendResponse, TrendSnapshot


class TestTrendResponseFormat:
    """Tests for trend response format validation."""

    @pytest.fixture
    def sample_snapshot(self):
        """Create a sample trend snapshot."""
        return TrendSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 5),
            platform=Platform.TIKTOK,
            trending_hashtags=[
                TrendingHashtag(
                    hashtag="#fitness",
                    volume=1250,
                    growth_rate=0.52,
                    unique_creators=340,
                ),
                TrendingHashtag(
                    hashtag="#homeworkout",
                    volume=890,
                    growth_rate=0.37,
                    unique_creators=210,
                ),
            ],
            emerging_creators=[],
            brand_mention_volumes={"Nike": 450, "Adidas": 320, "Lululemon": 180},
            sample_size=1250,
            confidence_level="high",
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

    def test_response_includes_share_of_voice(self, sample_snapshot):
        """Test that response includes calculated share of voice."""
        response = TrendResponse(
            snapshot=sample_snapshot,
            share_of_voice={"Nike": 47.37, "Adidas": 33.68, "Lululemon": 18.95},
        )

        # Verify structure
        assert "snapshot" in response.model_dump()
        assert "share_of_voice" in response.model_dump()
        assert response.share_of_voice["Nike"] == 47.37

    def test_response_includes_confidence_level(self):
        """Test that response includes confidence level."""
        snapshot = TrendSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 5),
            platform=Platform.TIKTOK,
            sample_size=50,
            confidence_level="medium",
        )
        response = TrendResponse(snapshot=snapshot, share_of_voice={})

        assert response.snapshot.confidence_level == "medium"

    def test_response_serialization(self, sample_snapshot):
        """Test that response serializes correctly to JSON."""
        response = TrendResponse(
            snapshot=sample_snapshot,
            share_of_voice={"Nike": 47.37, "Adidas": 33.68, "Lululemon": 18.95},
        )

        # Should serialize without errors
        json_data = response.model_dump_json()
        assert "#fitness" in json_data
        assert "Nike" in json_data
        assert "high" in json_data

    def test_pro_tier_has_access(self, pro_billing_context):
        """Test Pro tier billing context has correct tier."""
        assert pro_billing_context.tier == Tier.PRO
        assert pro_billing_context.tier != Tier.FREE

    def test_free_tier_denied_access(self, free_billing_context):
        """Test Free tier billing context has correct tier."""
        assert free_billing_context.tier == Tier.FREE
        assert free_billing_context.tier != Tier.PRO

    def test_snapshot_all_platforms(self):
        """Test snapshots can be created for all platforms."""
        for platform in Platform:
            snapshot = TrendSnapshot(
                id=uuid4(),
                snapshot_date=date(2026, 2, 5),
                platform=platform,
                sample_size=100,
                confidence_level="high",
            )
            assert snapshot.platform == platform

    def test_snapshot_with_trending_hashtags(self, sample_snapshot):
        """Test snapshot contains trending hashtags."""
        assert len(sample_snapshot.trending_hashtags) == 2
        assert sample_snapshot.trending_hashtags[0].hashtag == "#fitness"
        assert sample_snapshot.trending_hashtags[0].volume == 1250
        assert sample_snapshot.trending_hashtags[0].growth_rate == 0.52

    def test_snapshot_with_brand_mentions(self, sample_snapshot):
        """Test snapshot contains brand mentions."""
        assert "Nike" in sample_snapshot.brand_mention_volumes
        assert sample_snapshot.brand_mention_volumes["Nike"] == 450
        assert sample_snapshot.brand_mention_volumes["Adidas"] == 320

    def test_share_of_voice_calculation(self, sample_snapshot):
        """Test share of voice is calculated correctly."""
        total = sum(sample_snapshot.brand_mention_volumes.values())
        nike_sov = (sample_snapshot.brand_mention_volumes["Nike"] / total) * 100

        # Nike: 450 / 950 = 47.37%
        assert nike_sov == pytest.approx(47.37, rel=0.01)


@pytest.mark.mock_required
class TestTrendsTierGateHTTP:
    """HTTP tests for GET /v1/trends tier contract."""

    def _free_context(self) -> BillingContext:
        now = datetime(2026, 2, 10)
        user = User(
            id=uuid4(),
            email="free@trend.test",
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
            email="pro@trend.test",
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
        from src.api.routers.trends import router

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")

        mock_service = MagicMock()
        mock_service.get_trends = AsyncMock()
        app.dependency_overrides[get_billing_context] = lambda: self._free_context()
        app.dependency_overrides[get_trend_service] = lambda: mock_service

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/trends?platform=tiktok")
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["required_tier"] == "pro"
        assert error["current_tier"] == "free"
        assert error["feature"] == "trend_intelligence"
        assert "upgrade_url" not in error

    def test_pro_tier_passes_to_service(self) -> None:
        from src.api.routers.trends import router

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")

        snapshot = TrendSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 5),
            platform=Platform.TIKTOK,
            sample_size=50,
            confidence_level="medium",
        )
        mock_service = MagicMock()
        mock_service.get_trends = AsyncMock(
            return_value=TrendResponse(snapshot=snapshot, share_of_voice={})
        )
        app.dependency_overrides[get_billing_context] = lambda: self._pro_context()
        app.dependency_overrides[get_trend_service] = lambda: mock_service

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/trends?platform=tiktok")
        assert response.status_code == 200
        assert response.json()["snapshot"]["platform"] == "tiktok"
