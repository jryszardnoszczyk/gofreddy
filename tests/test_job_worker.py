"""Tests for JobWorker — real PostgreSQL for repo operations.

Test isolation: each test runs inside a transaction that rolls back on teardown.
AnalysisService remains mocked (real Gemini is Phase 5).
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.jobs.config import JobsConfig
from src.jobs.models import JobStatus, VideoInfo
from src.jobs.worker import JobWorker, is_shutdown_requested, reset_shutdown_state


# ── Helpers ──────────────────────────────────────────────────────────────────


def _mock_analysis_service(*, succeed=True):
    """Create mock AnalysisService (real Gemini deferred to Phase 5)."""
    service = MagicMock()
    if succeed:
        analysis_result = MagicMock()
        analysis_result.analysis.model_dump.return_value = {"test": "result"}
        analysis_result.cached = False
        analysis_result.cost_usd = 0.01
        service.analyze = AsyncMock(return_value=analysis_result)
    else:
        service.analyze = AsyncMock(side_effect=Exception("Analysis failed"))
    return service


async def _create_job_with_videos(job_repo, *, user_id=None, video_count=2, platforms=None):
    """Create a job with videos in real DB, return the job."""
    user_id = user_id or uuid4()
    async with job_repo._pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, email, supabase_user_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO NOTHING
            """,
            user_id,
            f"job-worker-{user_id.hex[:8]}@example.com",
            f"supa_{user_id.hex[:16]}",
        )
    platforms = platforms or ["tiktok"] * video_count
    videos = [
        VideoInfo(platform=platforms[i], video_id=str(i))
        for i in range(video_count)
    ]
    job = await job_repo.create_job_with_videos(
        user_id=user_id,
        videos=videos,
    )
    return job


# ── Process Job Tests (real DB, mock AnalysisService) ────────────────────────


@pytest.mark.db
class TestProcessJob:
    @pytest.fixture(autouse=True)
    def reset_shutdown(self):
        """Reset shutdown state before each test."""
        reset_shutdown_state()
        yield
        reset_shutdown_state()

    @pytest.mark.asyncio
    async def test_skip_unclaimed_job(self, job_repo, db_conn):
        """Unclaimed job (already running) is skipped."""
        # Create and claim job so second claim fails
        job = await _create_job_with_videos(job_repo, video_count=1)
        await job_repo.claim_job(job.id)  # First claim succeeds

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=_mock_analysis_service(),
            config=JobsConfig(),
        )

        # Second claim via process_job should skip (already running)
        await worker.process_job(job.id)

        # Job should still be running (not complete, since worker skipped it)
        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_process_empty_job(self, job_repo, db_conn):
        """Job with no pending videos completes immediately."""
        job = await _create_job_with_videos(job_repo, video_count=1)

        # Mark the single video as complete manually
        await db_conn.execute(
            "UPDATE job_videos SET status = 'complete' WHERE job_id = $1", job.id
        )

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=_mock_analysis_service(),
            config=JobsConfig(),
        )

        await worker.process_job(job.id)

        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.COMPLETE

    @pytest.mark.asyncio
    async def test_process_videos_successfully(self, job_repo, db_conn):
        """Videos are processed and results saved to real DB."""
        job = await _create_job_with_videos(job_repo, video_count=2)
        mock_service = _mock_analysis_service()

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=mock_service,
            config=JobsConfig(),
        )

        await worker.process_job(job.id)

        # Verify analysis service was called twice
        assert mock_service.analyze.call_count == 2

        # Verify job marked complete in DB
        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.COMPLETE

        # Verify videos have results in DB
        completed = await job_repo.get_completed_videos(job.id)
        assert len(completed) == 2

    @pytest.mark.asyncio
    async def test_checkpoint_after_interval(self, job_repo, db_conn):
        """Progress is updated in DB after checkpoint interval."""
        config = JobsConfig()
        object.__setattr__(config, "checkpoint_interval", 2)

        job = await _create_job_with_videos(job_repo, video_count=3)

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=_mock_analysis_service(),
            config=config,
        )

        await worker.process_job(job.id)

        # Verify final state in DB
        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.COMPLETE
        assert result.completed_videos == 3

    @pytest.mark.asyncio
    async def test_stop_on_cancellation(self, job_repo, db_conn):
        """Job stops when cancellation is requested."""
        job = await _create_job_with_videos(job_repo, video_count=2)

        # Set cancellation flag in DB
        await db_conn.execute(
            "UPDATE analysis_jobs SET cancellation_requested = TRUE WHERE id = $1",
            job.id,
        )

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=_mock_analysis_service(),
            config=JobsConfig(),
        )

        await worker.process_job(job.id)

        # Job should be marked cancelled
        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.CANCELLED
        assert result.failure_reason == "cancelled"

    @pytest.mark.asyncio
    async def test_handle_analysis_error(self, job_repo, db_conn):
        """Analysis errors are captured in video result, job still completes."""
        job = await _create_job_with_videos(job_repo, video_count=1)

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=_mock_analysis_service(succeed=False),
            config=JobsConfig(),
        )

        await worker.process_job(job.id)

        # Job should still complete despite video error
        result = await job_repo.get_by_id(job.id)
        assert result.status == JobStatus.COMPLETE

        # Video should have failed status in DB
        row = await db_conn.fetchrow(
            "SELECT status, error FROM job_videos WHERE job_id = $1", job.id
        )
        assert row["status"] == "failed"
        assert row["error"] is not None

    @pytest.mark.asyncio
    async def test_fetches_video_before_analysis(self, job_repo, db_conn):
        """Worker fetches each video into storage before analysis."""
        job = await _create_job_with_videos(job_repo, video_count=1)
        mock_service = _mock_analysis_service()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_video = AsyncMock()
        fetcher_factory = MagicMock(return_value=mock_fetcher)

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=mock_service,
            config=JobsConfig(),
            fetcher_factory=fetcher_factory,
        )

        await worker.process_job(job.id)

        assert mock_fetcher.fetch_video.await_count == 1
        assert mock_service.analyze.await_count == 1

    @pytest.mark.asyncio
    async def test_records_usage_for_non_cached_results(self, job_repo, db_conn):
        """Worker records usage only for successful non-cached analyses."""
        job = await _create_job_with_videos(job_repo, video_count=2)

        uncached_result = MagicMock()
        uncached_result.analysis.model_dump.return_value = {"test": "result-1"}
        uncached_result.cached = False
        uncached_result.cost_usd = 0.01

        cached_result = MagicMock()
        cached_result.analysis.model_dump.return_value = {"test": "result-2"}
        cached_result.cached = True
        cached_result.cost_usd = 0.0

        analysis_service = MagicMock()
        analysis_service.analyze = AsyncMock(side_effect=[uncached_result, cached_result])

        billing_service = MagicMock()
        billing_service.get_billing_context_for_user = AsyncMock(return_value=object())
        billing_service.record_usage = AsyncMock()

        worker = JobWorker(
            job_repo=job_repo,
            analysis_service=analysis_service,
            config=JobsConfig(),
            billing_service=billing_service,
        )

        await worker.process_job(job.id)

        billing_service.record_usage.assert_awaited_once()
        _args, kwargs = billing_service.record_usage.await_args
        assert kwargs["video_count"] == 1


# ── Sanitize Error Tests (pure logic — no DB needed) ────────────────────────


class TestSanitizeError:
    def test_sanitize_known_error(self):
        """Known error types return safe messages."""

        class VideoUnavailableError(Exception):
            pass

        error = VideoUnavailableError("Details about video")
        result = JobWorker._sanitize_error(error)
        assert result == "Video is unavailable"

    def test_sanitize_unknown_error(self):
        """Unknown error types return generic message, no leak."""
        error = Exception("Some internal error with secrets")
        result = JobWorker._sanitize_error(error)
        assert result == "Processing failed"
        assert "secrets" not in result


# ── Shutdown Handling Tests (pure logic — no DB needed) ──────────────────────


class TestShutdownHandling:
    @pytest.fixture(autouse=True)
    def reset_shutdown(self):
        """Reset shutdown state before and after tests."""
        reset_shutdown_state()
        yield
        reset_shutdown_state()

    def test_shutdown_initially_false(self):
        """Shutdown is initially not requested."""
        assert not is_shutdown_requested()

    def test_shutdown_after_signal(self):
        """Shutdown state after signal handler is called."""
        from src.jobs.worker import handle_sigterm

        handle_sigterm(15, None)  # SIGTERM = 15
        assert is_shutdown_requested()

    def test_reset_shutdown_state(self):
        """Resetting shutdown state works."""
        from src.jobs.worker import handle_sigterm

        handle_sigterm(15, None)
        assert is_shutdown_requested()
        reset_shutdown_state()
        assert not is_shutdown_requested()
