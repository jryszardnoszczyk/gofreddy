"""Tests for deepfake router billing guard — cached results skip record_usage."""

from dataclasses import dataclass
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
from src.deepfake.models import DeepfakeAnalysisRecord, RiskLevel


def _make_billing_context(*, tier=Tier.PRO):
    user = User(
        id=uuid4(),
        email="test@example.com",
        stripe_customer_id="cus_test",
        created_at=datetime.now(timezone.utc),
    )
    return BillingContext(
        user=user,
        tier=tier,
        usage_period=UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=10,
            videos_limit=50000,
        ),
        subscription=None,
    )


def _make_deepfake_record():
    """Create a mock DeepfakeAnalysisRecord."""
    record = MagicMock(spec=DeepfakeAnalysisRecord)
    record.id = uuid4()
    record.is_deepfake = False
    record.risk_level = RiskLevel.LOW
    record.combined_score = 0.15
    record.lip_sync_score = 0.1
    record.lip_sync_anomaly_detected = False
    record.lip_sync_confidence = None
    record.lip_sync_error = None
    record.reality_defender_score = 0.2
    record.reality_defender_verdict = None
    record.reality_defender_indicators = []
    record.reality_defender_error = None
    record.detection_method = "ensemble"
    record.limitations = []
    record.processing_time_ms = 1500
    record.cost_cents = 5
    record.analyzed_at = datetime.now(timezone.utc)
    return record


@dataclass(frozen=True, slots=True)
class _FakeDeepfakeResult:
    record: object
    cached: bool


def _build_app(*, billing_context, mock_billing_service, deepfake_service):
    from src.api.routers.deepfake import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")

    app.dependency_overrides[get_billing_context] = lambda: billing_context
    app.dependency_overrides[get_billing_service] = lambda: mock_billing_service

    app.state.deepfake_service = deepfake_service

    # Mock analysis repo + storage for _get_video_analysis and _get_video_url
    analysis_repo = MagicMock()
    analysis_mock = MagicMock()
    analysis_mock.id = uuid4()
    analysis_mock.user_id = billing_context.user.id
    analysis_mock.storage_key = "videos/test/video.mp4"
    analysis_mock.cache_key = "tiktok:12345:v1"
    analysis_repo.get_by_id = AsyncMock(return_value=analysis_mock)
    analysis_repo.user_has_access = AsyncMock(return_value=True)
    app.state.analysis_repository = analysis_repo

    storage = MagicMock()
    storage.generate_presigned_url = AsyncMock(return_value="https://r2.example.com/video.mp4")
    app.state.video_storage = storage

    return app


@pytest.fixture
def mock_billing_service():
    service = MagicMock(spec=BillingService)
    service.record_usage = AsyncMock()
    return service


@pytest.fixture
def billing_context():
    return _make_billing_context()


@pytest.mark.mock_required
class TestDeepfakeBillingGuard:
    """Tests for billing guard on deepfake analysis (cached vs non-cached)."""

    def test_cached_result_skips_record_usage(self, billing_context, mock_billing_service):
        """Cached deepfake result does NOT call record_usage."""
        deepfake_service = MagicMock()
        deepfake_service.is_cached = AsyncMock(return_value=True)
        deepfake_service.get_user_daily_cost = AsyncMock(return_value=0)
        deepfake_service.config = MagicMock()
        deepfake_service.config.daily_spend_limit_cents = 1000
        deepfake_service.analyze = AsyncMock(
            return_value=_FakeDeepfakeResult(
                record=_make_deepfake_record(),
                cached=True,
            )
        )

        app = _build_app(
            billing_context=billing_context,
            mock_billing_service=mock_billing_service,
            deepfake_service=deepfake_service,
        )

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(uuid4())},
        )

        assert response.status_code == 200
        mock_billing_service.record_usage.assert_not_awaited()

    def test_new_result_calls_record_usage(self, billing_context, mock_billing_service):
        """Non-cached deepfake result calls record_usage."""
        deepfake_service = MagicMock()
        deepfake_service.is_cached = AsyncMock(return_value=False)
        deepfake_service.get_user_daily_cost = AsyncMock(return_value=0)
        deepfake_service.config = MagicMock()
        deepfake_service.config.daily_spend_limit_cents = 1000
        deepfake_service.analyze = AsyncMock(
            return_value=_FakeDeepfakeResult(
                record=_make_deepfake_record(),
                cached=False,
            )
        )

        app = _build_app(
            billing_context=billing_context,
            mock_billing_service=mock_billing_service,
            deepfake_service=deepfake_service,
        )

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(uuid4())},
        )

        assert response.status_code == 200
        mock_billing_service.record_usage.assert_awaited_once()
