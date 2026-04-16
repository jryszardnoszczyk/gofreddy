"""Tests for creative pattern analysis API router."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_current_user_id
from src.api.exceptions import register_exception_handlers
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.tiers import Tier
from src.creative.service import CreativePatternAnalysisResult
from src.schemas import CreativePatterns


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_billing_context_pro(user_id):
    user = User(
        id=user_id,
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
def mock_billing_context_free(user_id):
    user = User(
        id=user_id,
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
def sample_creative_patterns():
    return CreativePatterns(
        hook_type="question",
        hook_duration_seconds=3,
        narrative_structure="tutorial",
        cta_type="link_in_bio",
        cta_placement="end",
        pacing="fast_cut",
        music_usage="trending_audio",
        text_overlay_density="moderate",
        hook_confidence=0.92,
        narrative_confidence=0.85,
        cta_confidence=0.78,
        pacing_confidence=0.90,
        music_confidence=0.88,
        text_overlay_confidence=0.75,
        transcript_summary="Test transcript",
        story_arc="Setup then resolution",
        emotional_journey="curiosity to satisfaction",
        protagonist="Test subject in frame",
        theme="Tutorial on topic",
        visual_style="Standard close-up shots",
        audio_style="Clear voiceover",
        scene_beat_map="(1) HOOK 0-3s: close_up static",
        processing_time_seconds=2.1,
        token_count=1200,
    )


@pytest.fixture
def mock_creative_service():
    service = MagicMock()
    service.get_creative_patterns = AsyncMock(return_value=None)
    service.analyze_creative_patterns = AsyncMock()
    return service


@pytest.fixture
def mock_billing_service():
    service = MagicMock()
    service.record_usage = AsyncMock()
    return service


def _create_app(
    user_id,
    billing_context,
    creative_service,
    billing_service,
    analysis_repo=None,
    video_storage=None,
):
    """Helper to build a test FastAPI app with creative router."""
    from src.api.routers.creative import router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")

    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_billing_context] = lambda: billing_context

    app.state.creative_service = creative_service
    app.state.billing_service = billing_service

    if analysis_repo is not None:
        app.state.analysis_repository = analysis_repo
    if video_storage is not None:
        app.state.video_storage = video_storage

    return app


@pytest.mark.mock_required
class TestCreativeCacheHit:
    """Test cache hit returns patterns without downloading video."""

    def test_cached_no_download(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
        sample_creative_patterns,
    ):
        """Cache hit returns immediately without R2 download."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_creative_service.get_creative_patterns.return_value = sample_creative_patterns

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
        )
        client = TestClient(app)
        response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["hook_type"] == "question"
        assert data["narrative_structure"] == "tutorial"
        # No video download or analyze call
        mock_creative_service.analyze_creative_patterns.assert_not_awaited()


@pytest.mark.mock_required
class TestCreativeAnalysisOnMiss:
    """Test cache miss triggers analysis."""

    def test_analysis_on_miss(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
        sample_creative_patterns,
    ):
        """Cache miss triggers Gemini analysis and returns patterns."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        video_analysis = MagicMock()
        video_analysis.id = analysis_id
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.video_id = "1234567890"
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)

        mock_storage = MagicMock()
        tmp_path = Path("/tmp/test_video.mp4")
        mock_storage.download_to_temp = AsyncMock(return_value=tmp_path)

        mock_creative_service.get_creative_patterns.return_value = None
        mock_creative_service.analyze_creative_patterns.return_value = (
            CreativePatternAnalysisResult(patterns=sample_creative_patterns, cached=False)
        )

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
            video_storage=mock_storage,
        )
        client = TestClient(app)

        with patch.object(Path, "unlink"):
            response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["hook_type"] == "question"
        mock_creative_service.analyze_creative_patterns.assert_awaited_once()


@pytest.mark.mock_required
class TestCreativeTierGating:
    """Test tier gating on creative endpoint."""

    def test_rejects_free_tier(
        self,
        user_id,
        mock_billing_context_free,
        mock_creative_service,
        mock_billing_service,
    ):
        """Free tier users get 403 with tier_required error."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        app = _create_app(
            user_id,
            mock_billing_context_free,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
        )
        client = TestClient(app)
        response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"]["code"] == "tier_required"
        assert data["error"]["required_tier"] == "pro"
        assert data["error"]["current_tier"] == "free"
        assert data["error"]["feature"] == "creative_patterns"


@pytest.mark.mock_required
class TestCreativeOwnership:
    """Test IDOR protection."""

    def test_rejects_unauthorized(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
    ):
        """Users cannot access other users' analyses (returns 404, not 403)."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=False)

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
        )
        client = TestClient(app)
        response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.mock_required
class TestCreativeBilling:
    """Test billing integration."""

    def test_records_usage_on_analysis(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
        sample_creative_patterns,
    ):
        """New analysis records billing usage."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        video_analysis = MagicMock()
        video_analysis.id = analysis_id
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.video_id = "1234567890"
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)

        mock_storage = MagicMock()
        tmp_path = Path("/tmp/test_video.mp4")
        mock_storage.download_to_temp = AsyncMock(return_value=tmp_path)

        mock_creative_service.get_creative_patterns.return_value = None
        mock_creative_service.analyze_creative_patterns.return_value = (
            CreativePatternAnalysisResult(patterns=sample_creative_patterns, cached=False)
        )

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
            video_storage=mock_storage,
        )
        client = TestClient(app)

        with patch.object(Path, "unlink"):
            response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        mock_billing_service.record_usage.assert_awaited_once()

    def test_skips_usage_on_cache_hit(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
        sample_creative_patterns,
    ):
        """Cache hit does NOT record billing usage."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        mock_creative_service.get_creative_patterns.return_value = sample_creative_patterns

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
        )
        client = TestClient(app)
        response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        mock_billing_service.record_usage.assert_not_awaited()


@pytest.mark.mock_required
class TestCreativeTempFileCleanup:
    """Test temp file cleanup."""

    def test_cleans_temp_file(
        self,
        user_id,
        mock_billing_context_pro,
        mock_creative_service,
        mock_billing_service,
        sample_creative_patterns,
    ):
        """Temp file is cleaned up after analysis."""
        analysis_id = uuid4()

        mock_analysis_repo = MagicMock()
        mock_analysis_repo.user_has_access = AsyncMock(return_value=True)

        video_analysis = MagicMock()
        video_analysis.id = analysis_id
        video_analysis.cache_key = "tiktok:1234567890:v2"
        video_analysis.video_id = "1234567890"
        mock_analysis_repo.get_by_id = AsyncMock(return_value=video_analysis)

        mock_storage = MagicMock()
        tmp_path = MagicMock(spec=Path)
        mock_storage.download_to_temp = AsyncMock(return_value=tmp_path)

        mock_creative_service.get_creative_patterns.return_value = None
        mock_creative_service.analyze_creative_patterns.return_value = (
            CreativePatternAnalysisResult(patterns=sample_creative_patterns, cached=False)
        )

        app = _create_app(
            user_id,
            mock_billing_context_pro,
            mock_creative_service,
            mock_billing_service,
            analysis_repo=mock_analysis_repo,
            video_storage=mock_storage,
        )
        client = TestClient(app)
        response = client.get(f"/v1/creative/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        tmp_path.unlink.assert_called_once_with(missing_ok=True)
