"""Tests for GenerationService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.billing.tiers import Tier, TierConfig
from src.generation.config import GenerationSettings
from src.generation.exceptions import (
    GenerationConcurrentLimitExceeded,
    GenerationDailySpendLimitExceeded,
    GenerationError,
)
from src.generation.models import Cadre, CompositionSpec
from src.generation.service import GenerationService


def _pro_config(tier: Tier) -> TierConfig:
    return TierConfig(
        tier=tier,
        videos_per_month=50000,
        rate_limit_per_minute=300,
        moderation_class_count=80,
        agent_messages_per_day=1000,
        max_batch_size=200,
        max_search_results=200,
        max_generation_jobs_per_day=10,
        max_concurrent_generation=2,
    )


def _free_config(tier: Tier) -> TierConfig:
    return TierConfig(
        tier=tier,
        videos_per_month=100,
        rate_limit_per_minute=30,
        moderation_class_count=21,
        agent_messages_per_day=20,
        max_batch_size=5,
        max_search_results=50,
        max_generation_jobs_per_day=0,
        max_concurrent_generation=0,
    )


def _make_spec(n_cadres=2, resolution="720p"):
    return CompositionSpec(
        cadres=[Cadre(index=i, prompt=f"cadre {i}", duration_seconds=5) for i in range(n_cadres)],
        resolution=resolution,
    )


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_user_daily_generation_cost = AsyncMock(return_value=0)
    repo.get_active_job_count = AsyncMock(return_value=0)
    repo.create_job = AsyncMock(return_value=uuid4())

    # Mock _acquire_connection as an async context manager
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.transaction = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=None),
        __aexit__=AsyncMock(return_value=False),
    ))

    repo._acquire_connection = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_conn),
        __aexit__=AsyncMock(return_value=False),
    ))

    return repo, mock_conn


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.get_presigned_url = AsyncMock(return_value="https://example.com/signed")
    return storage


@pytest.fixture
def enabled_config(monkeypatch):
    monkeypatch.setenv("GENERATION_GENERATION_ENABLED", "true")
    return GenerationSettings(_env_file=None, generation_enabled=True)


@pytest.fixture
def disabled_config():
    return GenerationSettings(_env_file=None, generation_enabled=False)


class TestSubmitJob:
    @pytest.mark.asyncio
    async def test_submit_job_success(self, mock_repo, mock_storage, enabled_config):
        repo, conn = mock_repo
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)
        user_id = uuid4()
        spec = _make_spec(n_cadres=2, resolution="720p")

        result = await service.submit_job(user_id, spec, Tier.PRO)

        assert result["status"] == "pending"
        assert result["cadre_count"] == 2
        assert result["estimated_cost_cents"] == 10 * 7  # 2 cadres * 5s * 7c/s
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_submit_job_480p_cost(self, mock_repo, mock_storage, enabled_config):
        repo, conn = mock_repo
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)
        spec = _make_spec(n_cadres=1, resolution="480p")

        result = await service.submit_job(uuid4(), spec, Tier.PRO)

        assert result["estimated_cost_cents"] == 5 * 5  # 1 cadre * 5s * 5c/s

    @pytest.mark.asyncio
    async def test_submit_job_preserves_seed_image_storage_keys(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)
        seed_key = "previews/user-id/seed.png"
        spec = CompositionSpec(
            cadres=[
                Cadre(
                    index=0,
                    prompt="cadre 0",
                    duration_seconds=5,
                    seed_image_storage_key=seed_key,
                )
            ],
            resolution="720p",
        )

        await service.submit_job(uuid4(), spec, Tier.PRO)

        cadres = repo.create_job.await_args.kwargs["cadres"]
        assert cadres == [
            {
                "index": 0,
                "prompt": "cadre 0",
                "duration_seconds": 5,
                "transition": "fade",
                "seed_image_storage_key": seed_key,
            }
        ]

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, mock_repo, mock_storage, disabled_config):
        repo, conn = mock_repo
        service = GenerationService(repo, mock_storage, disabled_config, _pro_config)

        with pytest.raises(GenerationError, match="not currently available"):
            await service.submit_job(uuid4(), _make_spec(), Tier.PRO)

    @pytest.mark.asyncio
    async def test_free_tier_rejected(self, mock_repo, mock_storage, enabled_config):
        repo, conn = mock_repo
        service = GenerationService(repo, mock_storage, enabled_config, _free_config)

        with pytest.raises(GenerationConcurrentLimitExceeded, match="Pro tier"):
            await service.submit_job(uuid4(), _make_spec(), Tier.FREE)

    @pytest.mark.asyncio
    async def test_daily_spend_limit_exceeded(self, mock_repo, mock_storage, enabled_config):
        repo, conn = mock_repo
        repo.get_user_daily_generation_cost = AsyncMock(return_value=4990)
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)
        spec = _make_spec(n_cadres=2, resolution="720p")  # cost = 70

        with pytest.raises(GenerationDailySpendLimitExceeded, match="daily budget"):
            await service.submit_job(uuid4(), spec, Tier.PRO)

    @pytest.mark.asyncio
    async def test_concurrent_limit_exceeded(self, mock_repo, mock_storage, enabled_config):
        repo, conn = mock_repo
        repo.get_active_job_count = AsyncMock(return_value=2)
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        with pytest.raises(GenerationConcurrentLimitExceeded, match="Max 2"):
            await service.submit_job(uuid4(), _make_spec(), Tier.PRO)


class TestGetJobStatus:
    @pytest.mark.asyncio
    async def test_returns_none_on_idor(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        repo.get_job = AsyncMock(return_value=None)
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.get_job_status(uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_completed_job_with_presigned_url(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        job_id = uuid4()
        repo.get_job = AsyncMock(return_value={
            "job": {
                "id": job_id,
                "status": "completed",
                "r2_key": "generated/uid/gid/final.mp4",
                "total_cadres": 2,
                "error": None,
            },
            "cadres": [
                {"cadre_index": 0, "status": "completed", "cost_cents": 35},
                {"cadre_index": 1, "status": "completed", "cost_cents": 35},
            ],
        })
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.get_job_status(uuid4(), job_id)

        assert result["status"] == "completed"
        assert result["video_url"] == "https://example.com/signed"
        assert result["video_url_expires_at"] is not None
        assert result["cost_cents"] == 70
        assert result["current_cadre"] == 2

    @pytest.mark.asyncio
    async def test_pending_job_no_url(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        job_id = uuid4()
        repo.get_job = AsyncMock(return_value={
            "job": {
                "id": job_id,
                "status": "pending",
                "r2_key": None,
                "total_cadres": 2,
                "error": None,
            },
            "cadres": [
                {"cadre_index": 0, "status": "pending", "cost_cents": None},
                {"cadre_index": 1, "status": "pending", "cost_cents": None},
            ],
        })
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.get_job_status(uuid4(), job_id)

        assert result["video_url"] is None
        assert result["video_url_expires_at"] is None
        assert result["cost_cents"] == 0

    @pytest.mark.asyncio
    async def test_status_includes_project_and_cadre_diagnostics(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        job_id = uuid4()
        project_id = uuid4()
        repo.get_job = AsyncMock(return_value={
            "job": {
                "id": job_id,
                "status": "partial",
                "video_project_id": project_id,
                "r2_key": None,
                "total_cadres": 2,
                "error": "some_cadres_failed",
            },
            "cadres": [
                {
                    "cadre_index": 0,
                    "status": "completed",
                    "cost_cents": 35,
                    "frame_r2_key": "generated/user/job/frame_0.png",
                    "error": None,
                },
                {
                    "cadre_index": 1,
                    "status": "failed",
                    "cost_cents": 0,
                    "frame_r2_key": None,
                    "error": "timed out",
                },
            ],
        })
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.get_job_status(uuid4(), job_id)

        assert result["video_project_id"] == project_id
        assert result["cadre_statuses"][0]["thumbnail_url"] == "https://example.com/signed"
        assert result["cadre_statuses"][1]["error"] == "timed out"


class TestListJobs:
    @pytest.mark.asyncio
    async def test_list_jobs(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        job_id = uuid4()
        from datetime import datetime, timezone
        repo.list_jobs = AsyncMock(return_value=(
            [{"id": job_id, "status": "pending", "created_at": datetime.now(timezone.utc), "total_cadres": 2}],
            1,
        ))
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.list_jobs(uuid4())

        assert result["total"] == 1
        assert len(result["jobs"]) == 1
        assert result["jobs"][0]["video_url"] is None


class TestCancelJob:
    @pytest.mark.asyncio
    async def test_cancel_success(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        job_id = uuid4()
        repo.request_cancellation = AsyncMock(return_value={
            "id": job_id, "status": "pending"
        })
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.cancel_job(uuid4(), job_id)

        assert result["cancellation_requested"] is True
        assert result["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_cancel_idor(self, mock_repo, mock_storage, enabled_config):
        repo, _ = mock_repo
        repo.request_cancellation = AsyncMock(return_value=None)
        service = GenerationService(repo, mock_storage, enabled_config, _pro_config)

        result = await service.cancel_job(uuid4(), uuid4())
        assert result is None
