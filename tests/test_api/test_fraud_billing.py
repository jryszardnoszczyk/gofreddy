"""Tests for fraud router billing guard and PR-024 billing correctness."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_billing_service
from src.api.exceptions import register_exception_handlers
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.service import BillingService
from src.billing.tiers import Tier
from src.common.enums import Platform
from src.billing.exceptions import UsageLimitExceeded
from src.fraud.models import FraudRiskLevel
from src.fraud.service import FraudAnalysisResult


def _make_billing_context():
    user = User(
        id=uuid4(),
        email="test@example.com",
        stripe_customer_id="cus_test",
        created_at=datetime.now(timezone.utc),
    )
    return BillingContext(
        user=user,
        tier=Tier.FREE,
        usage_period=UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=10,
            videos_limit=100,
        ),
        subscription=None,
    )


def _make_fraud_record_mock():
    """Create a mock FraudAnalysisRecord with all required attributes."""
    record = MagicMock()
    record.id = uuid4()
    record.username = "testuser"
    record.aqs_score = 85.0
    record.aqs_grade = "good"
    record.aqs_components = {"engagement": 80.0, "audience": 90.0}
    record.fake_follower_percentage = 5.0
    record.follower_sample_size = 100
    record.fake_follower_confidence = "high"
    record.engagement_rate = 5.0
    record.engagement_anomaly = None
    record.bot_comment_ratio = 0.1
    record.comments_analyzed = 50
    record.growth_data_available = True
    record.fraud_risk_level = FraudRiskLevel.LOW
    record.fraud_risk_score = 15
    record.analyzed_at = datetime.now(timezone.utc)
    record.model_version = "v1"
    return record


@pytest.fixture
def mock_billing_service():
    service = MagicMock(spec=BillingService)
    service.record_usage = AsyncMock()
    return service


@pytest.fixture
def billing_context():
    return _make_billing_context()


def _build_app(*, billing_context, mock_billing_service, fraud_service, fetcher):
    from src.api.routers.fraud import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")

    app.dependency_overrides[get_billing_context] = lambda: billing_context
    app.dependency_overrides[get_billing_service] = lambda: mock_billing_service

    app.state.fraud_service = fraud_service
    app.state.fetchers = {Platform.TIKTOK: fetcher}

    return app


def _make_fetcher_mock():
    fetcher = MagicMock()
    fetcher.fetch_followers = AsyncMock(return_value=[])
    fetcher.fetch_profile_stats = AsyncMock(return_value=MagicMock(
        username="testuser",
        platform=Platform.TIKTOK,
    ))
    fetcher._list_creator_videos = AsyncMock(return_value=[])
    return fetcher


@pytest.mark.mock_required
class TestFraudBillingGuard:
    """Tests for billing guard on fraud analysis (cached vs non-cached)."""

    def test_cached_result_skips_record_usage(self, billing_context, mock_billing_service):
        """Cached fraud result does NOT call record_usage."""
        fraud_service = MagicMock()
        fraud_service.is_cached = AsyncMock(return_value=True)
        fraud_service.analyze = AsyncMock(
            return_value=FraudAnalysisResult(
                record=_make_fraud_record_mock(),
                cached=True,
            )
        )

        app = _build_app(
            billing_context=billing_context,
            mock_billing_service=mock_billing_service,
            fraud_service=fraud_service,
            fetcher=_make_fetcher_mock(),
        )

        client = TestClient(app)
        response = client.post(
            "/v1/fraud/analyze",
            json={"platform": "tiktok", "username": "testuser"},
        )

        assert response.status_code == 200
        mock_billing_service.record_usage.assert_not_awaited()

    def test_new_result_calls_record_usage(self, billing_context, mock_billing_service):
        """Non-cached fraud result calls record_usage."""
        fraud_service = MagicMock()
        fraud_service.is_cached = AsyncMock(return_value=False)
        fraud_service.analyze = AsyncMock(
            return_value=FraudAnalysisResult(
                record=_make_fraud_record_mock(),
                cached=False,
            )
        )

        app = _build_app(
            billing_context=billing_context,
            mock_billing_service=mock_billing_service,
            fraud_service=fraud_service,
            fetcher=_make_fetcher_mock(),
        )

        client = TestClient(app)
        response = client.post(
            "/v1/fraud/analyze",
            json={"platform": "tiktok", "username": "testuser"},
        )

        assert response.status_code == 200
        mock_billing_service.record_usage.assert_awaited_once()

    def test_over_quota_returns_402(self, mock_billing_service):
        """Free-tier user over quota gets 402 before expensive work starts."""
        # Create over-quota billing context
        user = User(
            id=uuid4(),
            email="test@example.com",
            stripe_customer_id="cus_test",
            created_at=datetime.now(timezone.utc),
        )
        over_quota_context = BillingContext(
            user=user,
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(),
                user_id=user.id,
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                videos_used=100,
                videos_limit=100,
            ),
            subscription=None,
        )

        mock_billing_service.check_can_analyze = AsyncMock(
            side_effect=UsageLimitExceeded("Free tier limit reached")
        )

        fraud_service = MagicMock()
        app = _build_app(
            billing_context=over_quota_context,
            mock_billing_service=mock_billing_service,
            fraud_service=fraud_service,
            fetcher=_make_fetcher_mock(),
        )

        client = TestClient(app)
        response = client.post(
            "/v1/fraud/analyze",
            json={"platform": "tiktok", "username": "testuser"},
        )

        assert response.status_code == 402
        body = response.json()
        assert body["error"]["code"] == "usage_limit_exceeded"
        # Fraud service should NOT have been called (pre-flight blocked it)
        fraud_service.analyze.assert_not_called()
