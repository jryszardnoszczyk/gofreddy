"""Shared fixtures for API router tests.

These tests exercise the HTTP router layer: validation, auth gates, error
response shapes.  Services are mocked — service-level logic is tested by
the service-level tests (tests/test_analysis_service.py, etc.).
"""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

from src.analysis.models import VideoAnalysisRecord
from src.api.dependencies import (
    AuthPrincipal,
    get_auth_principal,
    get_current_user_id,
    verify_supabase_token,
)
from src.api.main import create_app
from src.api.rate_limit import limiter
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.service import BillingService
from src.billing.tiers import Tier
from src.common.enums import Platform
from src.jobs.models import AnalysisJob, JobStatus
from src.jobs.service import JobSubmission
from src.schemas import VideoAnalysis


# ── Shared mock fixtures ──────────────────────────────────────


@pytest.fixture
def valid_api_key() -> str:
    """Test API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_db_pool() -> MagicMock:
    """Mock database pool with acquire context manager."""
    pool = MagicMock()
    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    pool.acquire = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return pool


@pytest.fixture
def mock_analysis_record() -> VideoAnalysisRecord:
    """Mock analysis record."""
    return VideoAnalysisRecord(
        id=uuid4(),
        video_id=uuid4(),
        cache_key="tiktok:123456:v1",
        overall_safe=True,
        overall_confidence=0.95,
        risks_detected=[],
        summary="Test summary",
        content_categories=[],
        moderation_flags=[],
        sponsored_content=None,
        processing_time_seconds=1.5,
        token_count=1000,
        error=None,
        model_version="1",
        analyzed_at=datetime.now(UTC),
        analysis_cost_usd=0.001,
    )


@pytest.fixture
def mock_analysis_service(mock_analysis_record: VideoAnalysisRecord) -> MagicMock:
    """Mock analysis service."""
    service = MagicMock()
    service.analyze = AsyncMock()
    service.get_by_id = AsyncMock(return_value=mock_analysis_record)
    service.get_cached = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_video_result() -> MagicMock:
    """Mock video result from fetcher."""
    result = MagicMock()
    result.uuid = uuid4()
    result.video_id = "123456789"
    result.platform = Platform.TIKTOK
    return result


@pytest.fixture
def mock_batch_result(mock_video_result: MagicMock) -> MagicMock:
    """Mock batch fetch result."""
    batch = MagicMock()
    batch.successes = [mock_video_result]
    batch.errors = []
    return batch


@pytest.fixture
def mock_fetcher(mock_video_result: MagicMock, mock_batch_result: MagicMock) -> MagicMock:
    """Mock video fetcher."""
    fetcher = MagicMock()
    fetcher.fetch_video = AsyncMock(return_value=mock_video_result)
    fetcher.fetch_creator_videos = AsyncMock(return_value=mock_batch_result)
    fetcher.close = AsyncMock()
    return fetcher


@pytest.fixture
def mock_fetchers(mock_fetcher: MagicMock) -> dict:
    """Mock fetchers dictionary (all platforms share one mock)."""
    return {
        Platform.TIKTOK: mock_fetcher,
        Platform.INSTAGRAM: mock_fetcher,
        Platform.YOUTUBE: mock_fetcher,
    }


@pytest.fixture
def mock_storage() -> MagicMock:
    """Mock video storage."""
    storage = MagicMock()
    storage.download_to_temp = AsyncMock(return_value="/tmp/test.mp4")
    storage.close = AsyncMock()
    return storage


@pytest.fixture
def mock_analyzer() -> MagicMock:
    """Mock Gemini analyzer."""
    analyzer = MagicMock()
    analyzer.analyze_video = AsyncMock(
        return_value=VideoAnalysis(
            video_id="test",
            overall_safe=True,
            overall_confidence=0.95,
            risks_detected=[],
            summary="No risks detected",
        )
    )
    analyzer.close = AsyncMock()
    return analyzer


@pytest.fixture
def mock_search_service() -> MagicMock:
    """Mock search service with a default success response."""
    service = MagicMock()
    service.search = AsyncMock(
        return_value={
            "interpretation": {
                "scope": "videos",
                "platforms": ["tiktok"],
                "search_type": "keyword",
                "filters": {"query": "fitness"},
                "confidence": 0.9,
                "confidence_level": "high",
            },
            "confidence": "high",
            "results": [
                {
                    "platform": "tiktok",
                    "video_id": "123",
                    "creator_handle": "fitness_user",
                    "title": "Fitness video",
                    "view_count": 1000,
                    "like_count": 100,
                    "relevance_score": 0.8,
                }
            ],
            "total": 1,
            "platforms_searched": ["tiktok"],
            "platforms_failed": [],
            "errors": [],
        }
    )
    return service


@pytest.fixture
def mock_analysis_job() -> AnalysisJob:
    """Mock analysis job model."""
    return AnalysisJob(
        id=uuid4(),
        user_id=uuid4(),
        status=JobStatus.RUNNING,
        total_videos=3,
        completed_videos=1,
        force_refresh=False,
        idempotency_key=None,
        cancellation_requested=False,
        cloud_task_name=None,
        failure_reason=None,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        completed_at=None,
    )


@pytest.fixture
def mock_job_service(mock_analysis_job: AnalysisJob) -> MagicMock:
    """Mock job service with sane defaults for API tests."""
    service = MagicMock()
    service.submit_job = AsyncMock(
        return_value=JobSubmission(job_id=mock_analysis_job.id, status=JobStatus.PENDING)
    )
    service.list_jobs = AsyncMock(return_value=([mock_analysis_job], 1))
    service.get_job_status = AsyncMock(return_value=mock_analysis_job)
    service.cancel_job = AsyncMock(return_value=mock_analysis_job)
    service.get_video_results = AsyncMock(return_value=[])
    service.get_completed_videos = AsyncMock(return_value=[])
    return service


# ── Test client ───────────────────────────────────────────────


@pytest.fixture
def client(
    mock_db_pool: MagicMock,
    mock_analysis_service: MagicMock,
    mock_fetchers: dict,
    mock_storage: MagicMock,
    mock_analyzer: MagicMock,
    mock_search_service: MagicMock,
    mock_job_service: MagicMock,
) -> Generator[TestClient]:
    """Test client with fully mocked app state.

    Rate limiter is disabled to avoid 429s in tests.
    All app.state attributes are mocked so any router can handle requests.
    """
    app = create_app()

    limiter.enabled = False

    # Auth — bypass JWT verification but keep HTTPBearer presence check
    _test_user_id = uuid4()
    _test_claims = {"sub": "test-supabase-user-id", "email": "test@test.com", "aud": "authenticated"}
    _security = HTTPBearer()

    async def _mock_verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> dict:
        return _test_claims

    async def _mock_get_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> UUID:
        return _test_user_id

    async def _mock_get_auth_principal(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AuthPrincipal:
        return AuthPrincipal(
            user_id=_test_user_id,
            credential_type="jwt",
            claims=_test_claims,
        )

    app.dependency_overrides[verify_supabase_token] = _mock_verify_token
    app.dependency_overrides[get_current_user_id] = _mock_get_user_id
    app.dependency_overrides[get_auth_principal] = _mock_get_auth_principal

    # Core
    app.state.db_pool = mock_db_pool
    app.state.video_storage = mock_storage
    app.state.analyzer = mock_analyzer
    app.state.fetchers = mock_fetchers
    app.state.environment = "test"
    app.state.externals_mode = "fake"
    app.state.task_client_mode = "mock"

    # Analysis — user_has_access must be async for IDOR checks
    mock_analysis_repo = MagicMock()
    mock_analysis_repo.user_has_access = AsyncMock(return_value=True)
    app.state.analysis_service = mock_analysis_service
    app.state.analysis_repository = mock_analysis_repo

    # Search
    app.state.search_service = mock_search_service

    # Fraud
    app.state.fraud_service = MagicMock()
    app.state.fraud_service.close = AsyncMock()
    app.state.fraud_repository = MagicMock()

    # Demographics / Brands
    app.state.demographics_service = MagicMock()
    app.state.demographics_repository = MagicMock()
    app.state.brand_service = MagicMock()
    app.state.brand_repository = MagicMock()

    # Billing — mock must support `await get_billing_context(...)` and `await record_usage(...)`
    _now = datetime.now(UTC)
    _mock_billing_ctx = BillingContext(
        user=User(id=_test_user_id, email="test@test.com", stripe_customer_id=None, created_at=_now),
        tier=Tier.PRO,
        usage_period=UsagePeriod(
            id=uuid4(), user_id=_test_user_id,
            period_start=_now, period_end=_now,
            videos_used=0, videos_limit=50000,
        ),
        subscription=None,
    )
    mock_billing = MagicMock(spec=BillingService)
    mock_billing.get_billing_context = AsyncMock(return_value=_mock_billing_ctx)
    mock_billing.check_can_analyze = AsyncMock()
    mock_billing.record_usage = AsyncMock()
    mock_billing.get_billing_context_for_user = AsyncMock(return_value=_mock_billing_ctx)
    app.state.billing_service = mock_billing
    app.state.billing_repository = MagicMock()

    # Credits / Stripe
    mock_credit_service = MagicMock()
    mock_credit_service.get_billing_summary = AsyncMock(return_value=MagicMock(
        promo_remaining=5,
        included_remaining=100,
        topup_remaining=50,
        reserved_total=10,
        available=145,
    ))
    mock_credit_service.authorize_usage = AsyncMock(return_value=MagicMock(
        id="00000000-0000-0000-0000-000000000001",
        units_reserved=4,
    ))
    mock_credit_service.capture_usage = AsyncMock(return_value=MagicMock())
    mock_credit_service.void_usage = AsyncMock(return_value=None)
    app.state.credit_service = mock_credit_service
    mock_credit_settings = MagicMock()
    mock_credit_settings.pack_catalog = {
        "starter_100": (100, 999),
        "growth_500": (500, 3999),
        "scale_2000": (2000, 14999),
    }
    mock_credit_settings.frontend_base_url = "http://localhost:5173"
    app.state.credit_settings = mock_credit_settings

    mock_billing_flags = MagicMock()
    mock_billing_flags.hybrid_read_enabled = False
    app.state.billing_flags = mock_billing_flags

    app.state.stripe_client = None

    # Jobs
    app.state.job_service = mock_job_service
    app.state.job_repository = MagicMock()
    app.state.task_client = MagicMock()
    app.state.job_worker = MagicMock()

    # Trends / Evolution
    app.state.trend_service = MagicMock()
    app.state.trend_repository = MagicMock()
    app.state.evolution_service = MagicMock()
    mock_evolution_repo = MagicMock()
    mock_evolution_repo.get_creator_profile = AsyncMock(return_value=None)
    mock_evolution_repo.get_or_create_creator = AsyncMock(return_value=uuid4())
    mock_evolution_repo.upsert_creator_profile = AsyncMock()
    app.state.evolution_repository = mock_evolution_repo

    # Deepfake
    app.state.deepfake_service = MagicMock()
    app.state.deepfake_repository = MagicMock()

    # Stories
    app.state.story_service = MagicMock()
    app.state.story_repository = MagicMock()
    app.state.story_storage = MagicMock()

    # Monitoring service
    mock_monitoring = MagicMock()
    mock_monitoring.check_monitor_quota = AsyncMock()
    mock_monitoring.check_discover_quota = AsyncMock()
    mock_monitoring.create_monitor = AsyncMock()
    mock_monitoring.list_monitors = AsyncMock(return_value=[])
    mock_monitoring.list_monitors_enriched = AsyncMock(return_value=[])
    mock_monitoring.get_monitor_with_stats = AsyncMock()
    mock_monitoring.update_monitor = AsyncMock()
    mock_monitoring.delete_monitor = AsyncMock(return_value=True)
    mock_monitoring.get_mentions = AsyncMock(return_value=[])
    mock_monitoring.search_mentions = AsyncMock(return_value=([], 0))
    mock_monitoring.query_mentions = AsyncMock(return_value=([], 0))
    mock_monitoring.enqueue_run = AsyncMock()
    app.state.monitoring_service = mock_monitoring
    app.state.mention_fetchers = {}

    # Workspace service
    mock_workspace_service = MagicMock()
    mock_workspace_service.store_tool_result = AsyncMock()
    app.state.workspace_service = mock_workspace_service

    # Agent orchestrator
    app.state.orchestrator = MagicMock()

    # Conversation service (for usage endpoint agent message count + ownership checks)
    mock_conversation_service = MagicMock()
    mock_conversation_service.get_daily_count = AsyncMock(return_value=0)
    mock_conversation_service.get_conversation = AsyncMock(return_value=MagicMock())
    app.state.conversation_service = mock_conversation_service

    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        limiter.enabled = True
