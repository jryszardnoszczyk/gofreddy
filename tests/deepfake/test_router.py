"""Tests for deepfake detection API router."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_billing_service
from src.api.exceptions import register_exception_handlers
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.service import BillingService
from src.billing.tiers import Tier
from src.deepfake.service import DeepfakeAnalysisResult


@pytest.fixture
def mock_billing_context_pro():
    """Create Pro tier billing context."""
    user = User(
        id=uuid4(),
        email="pro@test.com",
        stripe_customer_id="cus_test",
        created_at=datetime.now(timezone.utc),
    )
    usage_period = UsagePeriod(
        id=uuid4(),
        user_id=user.id,
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        videos_used=100,
        videos_limit=50000,
    )
    return BillingContext(
        user=user,
        tier=Tier.PRO,
        usage_period=usage_period,
        subscription=None,
    )


@pytest.fixture
def mock_billing_context_free():
    """Create Free tier billing context."""
    user = User(
        id=uuid4(),
        email="free@test.com",
        stripe_customer_id=None,
        created_at=datetime.now(timezone.utc),
    )
    usage_period = UsagePeriod(
        id=uuid4(),
        user_id=user.id,
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        videos_used=50,
        videos_limit=100,
    )
    return BillingContext(
        user=user,
        tier=Tier.FREE,
        usage_period=usage_period,
        subscription=None,
    )


@pytest.fixture
def mock_billing_service():
    """Create mock billing service."""
    service = MagicMock(spec=BillingService)
    service.record_usage = AsyncMock()
    return service


@pytest.fixture
def mock_deepfake_service():
    """Create mock deepfake service."""
    service = MagicMock()
    service.get_user_daily_cost = AsyncMock(return_value=0)
    service.config.daily_spend_limit_cents = 10000
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def mock_video_analysis():
    """Create mock video analysis record."""
    analysis = MagicMock()
    analysis.id = uuid4()
    analysis.cache_key = "tiktok:1234567890:v2"
    analysis.user_id = None  # Will be set per test
    return analysis


@pytest.fixture
def app_with_free_tier(mock_billing_context_free, mock_deepfake_service, mock_billing_service):
    """Create test app with free tier billing context."""
    from src.api.routers.deepfake import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")

    # Override dependencies
    app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_free
    app.dependency_overrides[get_billing_service] = lambda: mock_billing_service

    # Set app state
    app.state.deepfake_service = mock_deepfake_service

    return app


@pytest.fixture
def app_with_pro_tier(mock_billing_context_pro, mock_deepfake_service, mock_billing_service):
    """Create test app with pro tier billing context."""
    from src.api.routers.deepfake import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")

    # Override dependencies
    app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
    app.dependency_overrides[get_billing_service] = lambda: mock_billing_service

    # Set app state
    app.state.deepfake_service = mock_deepfake_service

    return app


@pytest.mark.mock_required
class TestTierGating:
    """Tests for tier gating on deepfake endpoints."""

    def test_analyze_requires_pro_tier(self, app_with_free_tier):
        """Test that analyze endpoint requires Pro tier."""
        client = TestClient(app_with_free_tier)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(uuid4())},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"]["code"] == "tier_required"
        assert data["error"]["required_tier"] == "pro"
        assert data["error"]["current_tier"] == "free"
        assert data["error"]["feature"] == "deepfake_detection"
        assert "upgrade_url" not in data["error"]

    def test_get_analysis_requires_pro_tier(self, app_with_free_tier):
        """Test that get analysis endpoint requires Pro tier."""
        client = TestClient(app_with_free_tier)
        response = client.get(f"/v1/deepfake/{uuid4()}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"]["code"] == "tier_required"
        assert data["error"]["required_tier"] == "pro"
        assert data["error"]["current_tier"] == "free"
        assert data["error"]["feature"] == "deepfake_detection"
        assert "upgrade_url" not in data["error"]


@pytest.mark.mock_required
class TestDailySpendLimit:
    """Tests for daily spend limit enforcement (enforced in service, mapped in router)."""

    def test_daily_limit_reached_returns_429(
        self,
        mock_billing_context_pro,
        mock_billing_service,
    ):
        """Test that daily limit returns 429."""
        from src.deepfake.exceptions import DailySpendLimitExceeded
        from src.api.routers.deepfake import router

        # Service raises DailySpendLimitExceeded (limit enforced in service layer)
        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.analyze = AsyncMock(
            side_effect=DailySpendLimitExceeded(current=10000, limit=10000)
        )

        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.user_id = mock_billing_context_pro.user.id

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_storage = MagicMock()
        mock_storage.generate_download_url = AsyncMock(
            return_value="https://test.r2.cloudflarestorage.com/video.mp4"
        )

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo
        app.state.video_storage = mock_storage

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(video_analysis.id)},
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert data["error"]["code"] == "daily_limit_reached"


@pytest.mark.mock_required
class TestAnalyzeEndpoint:
    """Tests for POST /v1/deepfake/analyze endpoint."""

    def test_analyze_success(
        self,
        mock_billing_context_pro,
        mock_billing_service,
        sample_deepfake_record,
    ):
        """Test successful analysis."""
        from src.api.routers.deepfake import router

        # Set user ownership
        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.user_id = mock_billing_context_pro.user.id

        # Create services/repos
        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.get_user_daily_cost = AsyncMock(return_value=0)
        mock_service.config.daily_spend_limit_cents = 10000
        mock_service.analyze = AsyncMock(
            return_value=DeepfakeAnalysisResult(
                record=sample_deepfake_record,
                cached=False,
            )
        )

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_storage = MagicMock()
        mock_storage.generate_download_url = AsyncMock(
            return_value="https://test.r2.cloudflarestorage.com/video.mp4"
        )

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo
        app.state.video_storage = mock_storage

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(video_analysis.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["video_id"] == str(video_analysis.id)
        assert data["is_deepfake"] == sample_deepfake_record.is_deepfake

    def test_analyze_video_not_found(
        self,
        mock_billing_context_pro,
        mock_billing_service,
    ):
        """Test analysis with non-existent video."""
        from src.api.routers.deepfake import router

        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.get_user_daily_cost = AsyncMock(return_value=0)
        mock_service.config.daily_spend_limit_cents = 10000

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=None)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=False)

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(uuid4())},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.mock_required
class TestGetAnalysisEndpoint:
    """Tests for GET /v1/deepfake/{video_id} endpoint."""

    def test_get_analysis_not_found(
        self,
        mock_billing_context_pro,
    ):
        """Test get analysis with non-existent deepfake analysis."""
        from src.api.routers.deepfake import router

        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.user_id = mock_billing_context_pro.user.id

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_deepfake_repo = MagicMock()
        mock_deepfake_repo.get_by_video_analysis_id = AsyncMock(return_value=None)

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.state.analysis_repository = mock_analysis_repo
        app.state.deepfake_repository = mock_deepfake_repo

        client = TestClient(app)
        response = client.get(f"/v1/deepfake/{video_analysis.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.mock_required
class TestOwnershipVerification:
    """Tests for IDOR protection via ownership verification."""

    def test_cannot_access_other_users_analysis(
        self,
        mock_billing_context_pro,
        mock_billing_service,
    ):
        """Test that users cannot access other users' analyses."""
        from src.api.routers.deepfake import router

        # Video belongs to different user
        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.user_id = uuid4()  # Different user

        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.get_user_daily_cost = AsyncMock(return_value=0)
        mock_service.config.daily_spend_limit_cents = 10000

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=False)

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(video_analysis.id)},
        )

        # Should return 404 (not 403) to avoid information disclosure
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.mock_required
class TestDeepfakeBilling:
    """Tests for deepfake billing integration (record_usage calls)."""

    def test_new_analysis_calls_record_usage(
        self,
        mock_billing_context_pro,
        mock_billing_service,
        sample_deepfake_record,
    ):
        """Non-cached deepfake analysis calls record_usage."""
        from src.api.routers.deepfake import router

        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.user_id = mock_billing_context_pro.user.id

        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.get_user_daily_cost = AsyncMock(return_value=0)
        mock_service.config.daily_spend_limit_cents = 10000
        mock_service.analyze = AsyncMock(
            return_value=DeepfakeAnalysisResult(
                record=sample_deepfake_record,
                cached=False,
            )
        )

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_storage = MagicMock()
        mock_storage.generate_download_url = AsyncMock(
            return_value="https://test.r2.cloudflarestorage.com/video.mp4"
        )

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo
        app.state.video_storage = mock_storage

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(video_analysis.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        mock_billing_service.record_usage.assert_awaited_once()

    def test_cached_analysis_skips_record_usage(
        self,
        mock_billing_context_pro,
        mock_billing_service,
        sample_deepfake_record,
    ):
        """Cached deepfake analysis does NOT call record_usage."""
        from src.api.routers.deepfake import router

        video_analysis = MagicMock()
        video_analysis.id = uuid4()
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.user_id = mock_billing_context_pro.user.id

        mock_service = MagicMock()
        mock_service.is_cached = AsyncMock(return_value=False)
        mock_service.get_user_daily_cost = AsyncMock(return_value=0)
        mock_service.config.daily_spend_limit_cents = 10000
        mock_service.analyze = AsyncMock(
            return_value=DeepfakeAnalysisResult(
                record=sample_deepfake_record,
                cached=True,
            )
        )

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_storage = MagicMock()
        mock_storage.generate_download_url = AsyncMock(
            return_value="https://test.r2.cloudflarestorage.com/video.mp4"
        )

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router, prefix="/v1")
        app.dependency_overrides[get_billing_context] = lambda: mock_billing_context_pro
        app.dependency_overrides[get_billing_service] = lambda: mock_billing_service
        app.state.deepfake_service = mock_service
        app.state.analysis_repository = mock_analysis_repo
        app.state.video_storage = mock_storage

        client = TestClient(app)
        response = client.post(
            "/v1/deepfake/analyze",
            json={"video_id": str(video_analysis.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        mock_billing_service.record_usage.assert_not_awaited()
