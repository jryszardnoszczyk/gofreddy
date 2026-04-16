"""Tests for JobService — real PostgreSQL.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses job_repo, db_conn fixtures from conftest.py.

Cloud Tasks enqueue is the only mock — no local emulator available.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.jobs.config import JobsConfig
from src.jobs.exceptions import JobLimitExceeded, JobNotFoundError
from src.jobs.models import AnalysisJob, JobStatus, VideoInfo
from src.jobs.service import JobService, JobSubmission


# ── Helpers ──────────────────────────────────────────────────────────────────


def _mock_task_client(task_name="projects/test/tasks/task-1"):
    """Create a mock TaskClient (Cloud Tasks has no local emulator)."""
    client = MagicMock()
    client.enqueue_job = AsyncMock(return_value=task_name)
    return client


def _make_service(job_repo, task_client=None, config=None):
    """Create JobService with real repo and optional mock task client."""
    return JobService(
        repository=job_repo,
        task_client=task_client or _mock_task_client(),
        config=config or JobsConfig(),
    )


async def _create_test_user(db_conn):
    """Insert a real user row so FK-constrained job creation succeeds."""
    user_id = uuid4()
    await db_conn.execute(
        """
        INSERT INTO users (id, email, supabase_user_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO NOTHING
        """,
        user_id,
        f"job-service-{user_id.hex[:8]}@example.com",
        f"supa_{user_id.hex[:16]}",
    )
    return user_id


# ── Submit Job Tests ─────────────────────────────────────────────────────────


@pytest.mark.db
class TestSubmitJob:
    @pytest.mark.asyncio
    async def test_submit_new_job(self, job_repo, db_conn):
        """New job is created in DB and enqueued to Cloud Tasks."""
        task_client = _mock_task_client()
        service = _make_service(job_repo, task_client)
        user_id = await _create_test_user(db_conn)
        videos = [
            VideoInfo(platform="tiktok", video_id="123"),
            VideoInfo(platform="youtube", video_id="abc"),
        ]

        result = await service.submit_job(user_id=user_id, videos=videos)

        assert isinstance(result, JobSubmission)
        assert result.status == JobStatus.PENDING

        # Verify job exists in real DB
        job = await job_repo.get_by_id(result.job_id)
        assert job is not None
        assert job.user_id == user_id
        assert job.total_videos == 2
        assert job.status == JobStatus.PENDING

        # Cloud Tasks enqueue was called
        task_client.enqueue_job.assert_called_once_with(result.job_id)

    @pytest.mark.asyncio
    async def test_submit_with_idempotency_key_returns_existing(self, job_repo, db_conn):
        """Existing job is returned when idempotency key matches."""
        task_client = _mock_task_client()
        service = _make_service(job_repo, task_client)
        user_id = await _create_test_user(db_conn)
        videos = [VideoInfo(platform="tiktok", video_id="123")]

        # First submission
        result1 = await service.submit_job(
            user_id=user_id, videos=videos, idempotency_key="test-key"
        )

        # Reset mock to verify second submission doesn't enqueue
        task_client.enqueue_job.reset_mock()

        # Second submission with same key
        result2 = await service.submit_job(
            user_id=user_id, videos=videos, idempotency_key="test-key"
        )

        assert result2.job_id == result1.job_id
        task_client.enqueue_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_exceeds_job_limit(self, job_repo, db_conn):
        """Job limit is enforced via real DB count."""
        config = JobsConfig()
        service = _make_service(job_repo, config=config)
        user_id = await _create_test_user(db_conn)

        # Create max_concurrent_jobs_per_user active jobs
        for i in range(config.max_concurrent_jobs_per_user):
            videos = [VideoInfo(platform="tiktok", video_id=str(i))]
            await service.submit_job(user_id=user_id, videos=videos)

        # Next should fail
        with pytest.raises(JobLimitExceeded):
            await service.submit_job(
                user_id=user_id,
                videos=[VideoInfo(platform="tiktok", video_id="overflow")],
            )

    @pytest.mark.asyncio
    async def test_idempotent_submit_blocked_at_limit_with_new_key(self, job_repo, db_conn):
        """Idempotent submission with a NEW key is blocked when at the limit."""
        config = JobsConfig()
        service = _make_service(job_repo, config=config)
        user_id = await _create_test_user(db_conn)

        # Fill up to the limit using idempotency keys
        for i in range(config.max_concurrent_jobs_per_user):
            videos = [VideoInfo(platform="tiktok", video_id=str(i))]
            await service.submit_job(
                user_id=user_id, videos=videos, idempotency_key=f"key-{i}"
            )

        # New idempotency key should be rejected
        with pytest.raises(JobLimitExceeded):
            await service.submit_job(
                user_id=user_id,
                videos=[VideoInfo(platform="tiktok", video_id="overflow")],
                idempotency_key="brand-new-key",
            )

    @pytest.mark.asyncio
    async def test_idempotent_retry_allowed_at_limit(self, job_repo, db_conn):
        """Retry of an EXISTING idempotency key succeeds even at the limit."""
        config = JobsConfig()
        service = _make_service(job_repo, config=config)
        user_id = await _create_test_user(db_conn)

        # Submit first job with idempotency key
        videos = [VideoInfo(platform="tiktok", video_id="0")]
        result1 = await service.submit_job(
            user_id=user_id, videos=videos, idempotency_key="retry-key"
        )

        # Fill remaining slots
        for i in range(1, config.max_concurrent_jobs_per_user):
            await service.submit_job(
                user_id=user_id,
                videos=[VideoInfo(platform="tiktok", video_id=str(i))],
            )

        # Retry the same idempotency key — should succeed (not raise)
        result2 = await service.submit_job(
            user_id=user_id, videos=videos, idempotency_key="retry-key"
        )

        assert result2.job_id == result1.job_id


# ── Get Job Status Tests ─────────────────────────────────────────────────────


@pytest.mark.db
class TestGetJobStatus:
    @pytest.mark.asyncio
    async def test_get_existing_job(self, job_repo, db_conn):
        """Get status of a real job from DB."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)
        videos = [VideoInfo(platform="tiktok", video_id="123")]

        submission = await service.submit_job(user_id=user_id, videos=videos)

        result = await service.get_job_status(submission.job_id, user_id)

        assert isinstance(result, AnalysisJob)
        assert result.id == submission.job_id
        assert result.user_id == user_id
        assert result.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, job_repo, db_conn):
        """JobNotFoundError raised for nonexistent job."""
        service = _make_service(job_repo)
        with pytest.raises(JobNotFoundError):
            await service.get_job_status(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_get_job_wrong_user(self, job_repo, db_conn):
        """JobNotFoundError raised when user doesn't own the job."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)
        other_user = uuid4()
        videos = [VideoInfo(platform="tiktok", video_id="123")]

        submission = await service.submit_job(user_id=user_id, videos=videos)

        with pytest.raises(JobNotFoundError):
            await service.get_job_status(submission.job_id, other_user)


# ── Cancel Job Tests ─────────────────────────────────────────────────────────


@pytest.mark.db
class TestCancelJob:
    @pytest.mark.asyncio
    async def test_cancel_pending_job(self, job_repo, db_conn):
        """Cancel a pending job — directly sets status to cancelled."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)
        videos = [VideoInfo(platform="tiktok", video_id="123")]

        submission = await service.submit_job(user_id=user_id, videos=videos)

        result = await service.cancel_job(submission.job_id, user_id)

        assert result.id == submission.job_id
        assert result.status == JobStatus.CANCELLED

        # Verify in DB
        job = await job_repo.get_by_id(submission.job_id)
        assert job.status == JobStatus.CANCELLED
        assert job.failure_reason == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, job_repo, db_conn):
        """JobNotFoundError raised for nonexistent job."""
        service = _make_service(job_repo)
        with pytest.raises(JobNotFoundError):
            await service.cancel_job(uuid4(), uuid4())


# ── List Jobs Tests ──────────────────────────────────────────────────────────


@pytest.mark.db
class TestListJobs:
    @pytest.mark.asyncio
    async def test_list_all_jobs(self, job_repo, db_conn):
        """List all jobs for a user from real DB."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)

        # Create 3 jobs
        for i in range(3):
            videos = [VideoInfo(platform="tiktok", video_id=str(i))]
            await service.submit_job(user_id=user_id, videos=videos)

        jobs, total = await service.list_jobs(user_id)

        assert total == 3
        assert len(jobs) == 3
        assert all(isinstance(j, AnalysisJob) for j in jobs)

    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(self, job_repo, db_conn):
        """Filter jobs by status via real DB query."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)

        # Create 2 jobs (both pending)
        for i in range(2):
            videos = [VideoInfo(platform="tiktok", video_id=str(i))]
            await service.submit_job(user_id=user_id, videos=videos)

        # Filter for running (should be 0)
        jobs, total = await service.list_jobs(
            user_id, status_filter=[JobStatus.RUNNING]
        )
        assert total == 0
        assert len(jobs) == 0

        # Filter for pending (should be 2)
        jobs, total = await service.list_jobs(
            user_id, status_filter=[JobStatus.PENDING]
        )
        assert total == 2

    @pytest.mark.asyncio
    async def test_list_jobs_with_pagination(self, job_repo, db_conn):
        """Pagination via real DB LIMIT/OFFSET."""
        service = _make_service(job_repo)
        user_id = await _create_test_user(db_conn)

        # Create 5 jobs
        for i in range(5):
            videos = [VideoInfo(platform="tiktok", video_id=str(i))]
            await service.submit_job(user_id=user_id, videos=videos)

        # Page 1: limit=2, offset=0
        jobs_p1, total = await service.list_jobs(user_id, limit=2, offset=0)
        assert total == 5
        assert len(jobs_p1) == 2

        # Page 2: limit=2, offset=2
        jobs_p2, total = await service.list_jobs(user_id, limit=2, offset=2)
        assert total == 5
        assert len(jobs_p2) == 2

        # No overlap
        ids_p1 = {j.id for j in jobs_p1}
        ids_p2 = {j.id for j in jobs_p2}
        assert ids_p1.isdisjoint(ids_p2)

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, job_repo, db_conn):
        """Empty list for user with no jobs."""
        service = _make_service(job_repo)
        jobs, total = await service.list_jobs(uuid4())
        assert total == 0
        assert jobs == []
