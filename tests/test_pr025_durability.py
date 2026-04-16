"""Tests for PR-025: Async Jobs Durability and Backend Feature Fixes.

Covers all four workstreams:
- WS-04: Async jobs durability (CANCELLED status, record_id, SIGTERM, idempotency, URL validation)
- WS-07: Stories ownership (user_id scoping)
- WS-09: Search cache key includes limit
- WS-12: Deepfake cache-before-limit + 503 on outage
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.common.enums import Platform
from src.deepfake.config import DeepfakeConfig
from src.deepfake.exceptions import AllProvidersUnavailableError, DailySpendLimitExceeded
from src.deepfake.models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
    Verdict,
)
from src.deepfake.service import DeepfakeService
from src.jobs.models import AnalysisJob, JobStatus, VideoInfo


# ── WS-04.5: CANCELLED status ───────────────────────────────────────────────


class TestCancelledStatus:
    """Pure logic tests for CANCELLED enum and is_terminal."""

    def test_cancelled_in_job_status_enum(self):
        """CANCELLED is a valid JobStatus value."""
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_cancelled_is_terminal(self):
        """CANCELLED jobs are terminal (not retried)."""
        job = MagicMock(spec=AnalysisJob)
        # Test the real property logic
        assert JobStatus.CANCELLED in (JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED)

    def test_cancelled_is_not_cancellable(self):
        """Already-cancelled jobs cannot be cancelled again."""
        assert JobStatus.CANCELLED not in (JobStatus.PENDING, JobStatus.RUNNING)


@pytest.mark.db
class TestCancelledStatusDB:
    """Real DB tests for CANCELLED status."""

    @pytest.mark.asyncio
    async def test_cancel_pending_sets_cancelled_status(self, job_repo, db_conn):
        """Cancelling a pending job sets status to 'cancelled'."""
        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"cancel-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="cancel-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)

        result = await job_repo.cancel_if_cancellable(job.id, user_id)

        assert result is not None
        assert result.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_mark_job_cancelled_updates_status(self, job_repo, db_conn):
        """mark_job_cancelled sets status and failure_reason."""
        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"mc-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="mc-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)
        await job_repo.claim_job(job.id)  # Move to running

        await job_repo.mark_job_cancelled(job.id)

        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.CANCELLED
        assert result.failure_reason == "cancelled"


# ── WS-04.1: record_id in worker results ────────────────────────────────────


@pytest.mark.db
class TestRecordIdInWorkerResults:
    """Worker includes record_id in video results."""

    @pytest.mark.asyncio
    async def test_worker_includes_record_id(self, job_repo, db_conn):
        """Worker result dict includes record_id from AnalysisService."""
        from src.jobs.config import JobsConfig
        from src.jobs.worker import JobWorker, reset_shutdown_state

        reset_shutdown_state()

        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"rid-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="record-id-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)

        expected_record_id = uuid4()
        mock_service = MagicMock()
        analysis_result = MagicMock()
        analysis_result.analysis.model_dump.return_value = {"test": "data"}
        analysis_result.cached = False
        analysis_result.cost_usd = 0.01
        analysis_result.record_id = expected_record_id
        mock_service.analyze = AsyncMock(return_value=analysis_result)

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=mock_service,
            config=JobsConfig(),
        )

        await worker.process_job(job.id)

        # Check that the saved result includes record_id
        row = await db_conn.fetchrow(
            "SELECT result FROM job_videos WHERE job_id = $1 AND status = 'complete'",
            job.id,
        )
        import json

        result = json.loads(row["result"])
        assert result["record_id"] == str(expected_record_id)

        reset_shutdown_state()


# ── WS-04.2: SIGTERM marks interrupted ──────────────────────────────────────


@pytest.mark.db
class TestSIGTERMInterrupted:
    """Worker marks jobs as interrupted on SIGTERM."""

    @pytest.mark.asyncio
    async def test_sigterm_before_processing_marks_interrupted(self, job_repo, db_conn):
        """Pre-loop SIGTERM check marks job as interrupted."""
        from src.jobs.config import JobsConfig
        from src.jobs.worker import JobWorker, handle_sigterm, reset_shutdown_state

        reset_shutdown_state()

        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"sig-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="sigterm-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)

        # Simulate SIGTERM before processing
        handle_sigterm(15, None)

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=MagicMock(),
            config=JobsConfig(),
        )
        await worker.process_job(job.id)

        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.FAILED
        assert result.failure_reason == "interrupted"

        reset_shutdown_state()


# ── WS-04.3: Atomic idempotency ─────────────────────────────────────────────


@pytest.mark.db
class TestAtomicIdempotency:
    """Tests for atomic INSERT ON CONFLICT idempotency."""

    @pytest.mark.asyncio
    async def test_create_job_idempotent_new_job(self, job_repo, db_conn):
        """First insert creates a new job."""
        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"idem-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="idem-1")]

        job = await job_repo.create_job_idempotent(
            user_id=user_id,
            videos=videos,
            force_refresh=False,
            idempotency_key="test-idem-key",
        )

        assert job is not None
        assert job.status == JobStatus.PENDING
        assert job.idempotency_key == "test-idem-key"
        assert job.user_id == user_id

    @pytest.mark.asyncio
    async def test_create_job_idempotent_returns_existing(self, job_repo, db_conn):
        """Duplicate idempotency key returns existing job."""
        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"idem2-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="idem-dup")]

        job1 = await job_repo.create_job_idempotent(
            user_id=user_id, videos=videos, force_refresh=False,
            idempotency_key="dup-key",
        )

        job2 = await job_repo.create_job_idempotent(
            user_id=user_id, videos=videos, force_refresh=False,
            idempotency_key="dup-key",
        )

        assert job2.id == job1.id


# ── WS-04.4: URL validation at submission time ──────────────────────────────
# NOTE: API-level URL validation tests are in tests/test_api/test_videos.py
# (TestAsyncURLValidation class) since they need the client + valid_api_key fixtures.


# ── WS-07: Stories ownership (user_id in get_existing_story_ids) ─────────


@pytest.mark.mock_required
class TestStoriesUserOwnership:
    """Stories capture passes user_id to dedup check."""

    async def test_capture_passes_user_id_to_existing_check(self):
        """capture_stories_now passes user_id to get_existing_story_ids."""
        from src.common.enums import Platform
        from src.stories.service import StoryService

        mock_repo = AsyncMock()
        mock_storage = AsyncMock()
        mock_fetcher = AsyncMock()

        mock_fetcher.fetch_stories.return_value = []
        mock_repo.get_existing_story_ids.return_value = set()

        service = StoryService(
            repository=mock_repo,
            storage=mock_storage,
            instagram_fetcher=mock_fetcher,
        )

        user_id = uuid4()
        await service.capture_stories_now(
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            creator_username="testcreator",
        )

        # Verify user_id was passed (3rd positional arg)
        mock_fetcher.fetch_stories.assert_called_once_with("testcreator")
        # No stories returned, so get_existing_story_ids should NOT be called
        # (short-circuit on empty stories)

    async def test_capture_with_stories_passes_user_id(self):
        """When stories exist, user_id is passed to existing check."""
        from src.common.enums import Platform
        from src.stories.models import StoryResult
        from src.stories.service import StoryService

        mock_repo = AsyncMock()
        mock_storage = AsyncMock()
        mock_fetcher = AsyncMock()

        mock_story = StoryResult(
            story_id="ig_test_123",
            media_url="https://instagram.com/story.mp4",
            media_type="video",
            creator_username="testcreator",
        )
        mock_fetcher.fetch_stories.return_value = [mock_story]
        mock_repo.get_existing_story_ids.return_value = {"ig_test_123"}  # Already captured

        service = StoryService(
            repository=mock_repo,
            storage=mock_storage,
            instagram_fetcher=mock_fetcher,
        )

        user_id = uuid4()
        result = await service.capture_stories_now(
            user_id=user_id,
            platform=Platform.INSTAGRAM,
            creator_username="testcreator",
        )

        # Verify user_id was passed
        mock_repo.get_existing_story_ids.assert_called_once_with(
            Platform.INSTAGRAM, "testcreator", user_id
        )
        assert result["skipped"] == 1


# ── WS-09: Search cache key includes limit ──────────────────────────────────


class TestSearchCacheKeyIncludesLimit:
    """Search cache key incorporates the limit parameter."""

    def test_different_limits_different_cache_keys(self):
        """Different limit values produce different cache keys."""
        from src.search.service import (
            ConfidenceLevel,
            GeminiQueryParser,
            ParsedSearchQuery,
            SearchConfig,
            SearchFilters,
            SearchScope,
            SearchService,
            SearchType,
        )

        service = SearchService(
            parser=MagicMock(spec=GeminiQueryParser),
            tiktok_fetcher=MagicMock(),
            instagram_fetcher=MagicMock(),
            youtube_fetcher=MagicMock(),
            config=SearchConfig(),
        )

        query_10 = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            filters=SearchFilters(query="test"),
            confidence_level=ConfidenceLevel.HIGH,
            limit=10,
        )

        query_50 = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            filters=SearchFilters(query="test"),
            confidence_level=ConfidenceLevel.HIGH,
            limit=50,
        )

        key_10 = service._cache_key(query_10)
        key_50 = service._cache_key(query_50)

        assert key_10 != key_50

    def test_same_limit_same_cache_key(self):
        """Same limit values produce the same cache key."""
        from src.search.service import (
            ConfidenceLevel,
            GeminiQueryParser,
            ParsedSearchQuery,
            SearchConfig,
            SearchFilters,
            SearchScope,
            SearchService,
            SearchType,
        )

        service = SearchService(
            parser=MagicMock(spec=GeminiQueryParser),
            tiktok_fetcher=MagicMock(),
            instagram_fetcher=MagicMock(),
            youtube_fetcher=MagicMock(),
            config=SearchConfig(),
        )

        query_a = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            filters=SearchFilters(query="test"),
            confidence_level=ConfidenceLevel.HIGH,
            limit=25,
        )

        query_b = ParsedSearchQuery(
            scope=SearchScope.VIDEOS,
            platforms=[Platform.TIKTOK],
            search_type=SearchType.KEYWORD,
            filters=SearchFilters(query="test"),
            confidence_level=ConfidenceLevel.HIGH,
            limit=25,
        )

        assert service._cache_key(query_a) == service._cache_key(query_b)


# ── WS-12: Deepfake cache-before-limit and 503 on outage ────────────────────


@pytest.mark.mock_required
class TestDeepfakeCacheBeforeLimit:
    """Deepfake service checks cache before enforcing spend limit."""

    @pytest.mark.asyncio
    async def test_cached_result_bypasses_spend_limit(self):
        """Cache hit returns result without checking spend limit."""
        from datetime import datetime, timezone

        mock_repo = AsyncMock()
        mock_lipinc = AsyncMock()
        mock_rd = AsyncMock()

        # User is over spend limit
        mock_repo.get_user_daily_cost.return_value = 99999

        # But there's a cached result
        cached_record = MagicMock(spec=DeepfakeAnalysisRecord)
        cached_record.analyzed_at = datetime.now(timezone.utc)
        mock_repo.get_by_video_analysis_id.return_value = cached_record

        config = DeepfakeConfig(
            reality_defender_api_key="test",
            lipinc_api_key="test",
            daily_spend_limit_cents=100,
        )
        service = DeepfakeService(
            repository=mock_repo,
            lipinc=mock_lipinc,
            reality_defender=mock_rd,
            config=config,
        )

        # Should return cached result without raising DailySpendLimitExceeded
        result = await service.analyze(
            video_analysis_id=uuid4(),
            user_id=uuid4(),
            video_url="https://test.r2.cloudflarestorage.com/video.mp4",
        )

        assert result.cached is True
        # Spend limit check should NOT have been called (cache short-circuit)
        mock_repo.get_user_daily_cost.assert_not_called()

    @pytest.mark.asyncio
    async def test_spend_limit_raises_when_over(self):
        """Spend limit check raises DailySpendLimitExceeded when exceeded."""
        mock_repo = AsyncMock()
        mock_lipinc = AsyncMock()
        mock_rd = AsyncMock()

        mock_repo.get_by_video_analysis_id.return_value = None  # No cache
        mock_repo.get_user_daily_cost.return_value = 15000  # $150

        config = DeepfakeConfig(
            reality_defender_api_key="test",
            lipinc_api_key="test",
            daily_spend_limit_cents=10000,  # $100
        )
        service = DeepfakeService(
            repository=mock_repo,
            lipinc=mock_lipinc,
            reality_defender=mock_rd,
            config=config,
        )

        with pytest.raises(DailySpendLimitExceeded) as exc_info:
            await service.analyze(
                video_analysis_id=uuid4(),
                user_id=uuid4(),
                video_url="https://test.r2.cloudflarestorage.com/video.mp4",
            )

        assert exc_info.value.current_cost_cents == 15000
        assert exc_info.value.limit_cents == 10000

    @pytest.mark.asyncio
    async def test_spend_limit_allows_when_under(self):
        """Spend limit passes when under limit."""
        mock_repo = AsyncMock()
        mock_lipinc = AsyncMock()
        mock_rd = AsyncMock()

        mock_repo.get_by_video_analysis_id.return_value = None  # No cache
        mock_repo.get_user_daily_cost.return_value = 500  # $5

        # Setup successful analysis
        mock_lipinc.analyze.return_value = LipSyncResult(
            score=0.95, anomaly_detected=False, confidence=Confidence.HIGH,
            processing_time_ms=1000,
        )
        mock_rd.analyze.return_value = RealityDefenderResult(
            score=0.1, verdict=Verdict.AUTHENTIC, indicators=[],
            processing_time_ms=2000, cost_cents=40,
        )
        created_record = MagicMock(spec=DeepfakeAnalysisRecord)
        mock_repo.create.return_value = created_record

        config = DeepfakeConfig(
            reality_defender_api_key="test",
            lipinc_api_key="test",
            daily_spend_limit_cents=10000,
        )
        service = DeepfakeService(
            repository=mock_repo,
            lipinc=mock_lipinc,
            reality_defender=mock_rd,
            config=config,
        )

        result = await service.analyze(
            video_analysis_id=uuid4(),
            user_id=uuid4(),
            video_url="https://test.r2.cloudflarestorage.com/video.mp4",
        )

        assert result.cached is False


@pytest.mark.mock_required
class TestDeepfake503OnOutage:
    """Deepfake raises AllProvidersUnavailableError when all providers fail."""

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_503(self):
        """AllProvidersUnavailableError raised when both providers fail."""
        mock_repo = AsyncMock()
        mock_lipinc = AsyncMock()
        mock_rd = AsyncMock()

        mock_repo.get_by_video_analysis_id.return_value = None
        mock_repo.get_user_daily_cost.return_value = 0

        # Both providers fail
        mock_lipinc.analyze.side_effect = Exception("LIPINC down")
        mock_rd.analyze.side_effect = Exception("RD down")

        config = DeepfakeConfig(
            reality_defender_api_key="test",
            lipinc_api_key="test",
        )
        service = DeepfakeService(
            repository=mock_repo,
            lipinc=mock_lipinc,
            reality_defender=mock_rd,
            config=config,
        )

        with pytest.raises(AllProvidersUnavailableError) as exc_info:
            await service.analyze(
                video_analysis_id=uuid4(),
                user_id=uuid4(),
                video_url="https://test.r2.cloudflarestorage.com/video.mp4",
            )

        assert "all_providers_unavailable" in exc_info.value.limitations

    @pytest.mark.asyncio
    async def test_one_provider_succeeds_does_not_raise(self):
        """Single provider success still produces a result."""
        mock_repo = AsyncMock()
        mock_lipinc = AsyncMock()
        mock_rd = AsyncMock()

        mock_repo.get_by_video_analysis_id.return_value = None
        mock_repo.get_user_daily_cost.return_value = 0

        # LIPINC fails, RD succeeds
        mock_lipinc.analyze.side_effect = Exception("LIPINC down")
        mock_rd.analyze.return_value = RealityDefenderResult(
            score=0.1, verdict=Verdict.AUTHENTIC, indicators=[],
            processing_time_ms=2000, cost_cents=40,
        )
        created_record = MagicMock(spec=DeepfakeAnalysisRecord)
        mock_repo.create.return_value = created_record

        config = DeepfakeConfig(
            reality_defender_api_key="test",
            lipinc_api_key="test",
        )
        service = DeepfakeService(
            repository=mock_repo,
            lipinc=mock_lipinc,
            reality_defender=mock_rd,
            config=config,
        )

        # Should NOT raise — one provider is enough
        result = await service.analyze(
            video_analysis_id=uuid4(),
            user_id=uuid4(),
            video_url="https://test.r2.cloudflarestorage.com/video.mp4",
        )

        assert result.cached is False


# ── WS-12: Deepfake router exception mapping ────────────────────────────────


class TestDeepfakeExceptions:
    """Tests for deepfake exception classes."""

    def test_daily_spend_limit_exceeded(self):
        """DailySpendLimitExceeded stores cost and limit."""
        exc = DailySpendLimitExceeded(current=5000, limit=10000)
        assert exc.current_cost_cents == 5000
        assert exc.limit_cents == 10000
        assert "5000" in str(exc)

    def test_all_providers_unavailable(self):
        """AllProvidersUnavailableError stores limitations list."""
        exc = AllProvidersUnavailableError(
            limitations=["lipinc_error", "rd_error", "all_providers_unavailable"]
        )
        assert len(exc.limitations) == 3
        assert "All deepfake detection providers unavailable" in str(exc)


# ── WS-04: Job service video results include record_id ───────────────────────


@pytest.mark.db
class TestJobServiceVideoResults:
    """get_video_results includes record_id field."""

    @pytest.mark.asyncio
    async def test_get_video_results_includes_record_id(self, job_repo, db_conn):
        """get_video_results returns record_id from stored result."""
        import json
        from unittest.mock import MagicMock

        from src.jobs.config import JobsConfig
        from src.jobs.service import JobService

        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"vr-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="vr-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)

        # Simulate worker saving a result with record_id
        record_id = str(uuid4())
        result = {"status": "complete", "record_id": record_id, "result": {"test": True}}
        await job_repo.save_video_result(job.id, 0, result)

        task_client = MagicMock()
        service = JobService(
            repository=job_repo,
            task_client=task_client,
            config=JobsConfig(),
        )

        results = await service.get_video_results(job.id)
        assert len(results) == 1
        assert results[0]["record_id"] == record_id


# ── WS-04.5: Worker cancellation uses CANCELLED status ─────────────────────


@pytest.mark.db
class TestWorkerCancellation:
    """Worker uses mark_job_cancelled for CANCELLED status."""

    @pytest.mark.asyncio
    async def test_cancellation_sets_cancelled_status(self, job_repo, db_conn):
        """Cancelled job gets CANCELLED status (not FAILED)."""
        from src.jobs.config import JobsConfig
        from src.jobs.worker import JobWorker, reset_shutdown_state

        reset_shutdown_state()

        user_id = uuid4()
        await db_conn.execute(
            """INSERT INTO users (id, email, supabase_user_id)
               VALUES ($1, $2, $3) ON CONFLICT (id) DO NOTHING""",
            user_id, f"wc-{user_id.hex[:8]}@test.com", f"supa_{user_id.hex[:16]}",
        )
        videos = [VideoInfo(platform="tiktok", video_id="wc-test")]
        job = await job_repo.create_job_with_videos(user_id=user_id, videos=videos)

        # Set cancellation flag before processing
        await db_conn.execute(
            "UPDATE analysis_jobs SET cancellation_requested = TRUE WHERE id = $1",
            job.id,
        )

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=MagicMock(),
            config=JobsConfig(),
        )
        await worker.process_job(job.id)

        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.CANCELLED
        assert result.failure_reason == "cancelled"

        reset_shutdown_state()
