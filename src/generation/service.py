"""Generation service — thin orchestration layer."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

import asyncpg

from ..billing.tiers import Tier, TierConfig

from .config import GenerationSettings
from .exceptions import (
    GenerationConcurrentLimitExceeded,
    GenerationDailySpendLimitExceeded,
    GenerationError,
)
from .models import CompositionSpec
from .repository import PostgresGenerationRepository
from .storage import R2GenerationStorage, PRESIGNED_URL_EXPIRY

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(
        self,
        repository: PostgresGenerationRepository,
        storage: R2GenerationStorage | None,
        config: GenerationSettings,
        tier_config_fn: Callable[[Tier], TierConfig],
        dispatch_fn: Callable[[UUID], Any] | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._config = config
        self._tier_config_fn = tier_config_fn
        self._dispatch_fn = dispatch_fn

    async def submit_job(
        self,
        user_id: UUID,
        composition_spec: CompositionSpec,
        tier: Tier,
        *,
        video_project_id: UUID | None = None,
        project_revision: int | None = None,
        conn: asyncpg.Connection | None = None,
        dispatch: bool = True,
    ) -> dict:
        """Submit a new generation job.

        1. Check feature flag
        2. Check tier (Pro only)
        3. SELECT FOR UPDATE on credit_balances: check active count
        4. Check daily spend limit
        5. Create DB records (job + cadres)
        6. Return job_id + estimated_cost
        """
        if not self._config.generation_enabled:
            raise GenerationError("Video generation is not currently available")

        tier_config = self._tier_config_fn(tier)
        if tier_config.max_concurrent_generation == 0:
            raise GenerationConcurrentLimitExceeded(
                "Video generation requires Pro tier"
            )

        # Estimate cost
        cost_per_sec = (
            self._config.cost_per_second_cents_480p
            if composition_spec.resolution == "480p"
            else self._config.cost_per_second_cents_720p
        )
        total_duration = sum(c.duration_seconds for c in composition_spec.cadres)
        estimated_cost = total_duration * cost_per_sec

        # Check daily spend limit
        daily_cost = await self._repo.get_user_daily_generation_cost(user_id)
        remaining_budget = self._config.daily_spend_limit_cents - daily_cost
        if estimated_cost > remaining_budget:
            raise GenerationDailySpendLimitExceeded(
                f"Estimated cost {estimated_cost}c exceeds remaining daily budget {remaining_budget}c"
            )

        # Concurrent limit check with FOR UPDATE lock
        if conn is not None and dispatch:
            raise ValueError(
                "dispatch=True is not supported with caller-managed connections; "
                "submit with dispatch=False and call dispatch_job() after commit"
            )

        cadres_data = [
            {
                "index": c.index,
                "prompt": c.prompt,
                "duration_seconds": c.duration_seconds,
                "transition": c.transition,
                "seed_image_storage_key": c.seed_image_storage_key,
            }
            for c in composition_spec.cadres
        ]

        async def _create_job(active_conn: asyncpg.Connection) -> UUID:
            # Lock user's credit_balances row to serialize concurrent submissions
            await active_conn.fetchval(
                "SELECT 1 FROM credit_balances WHERE user_id = $1 FOR UPDATE",
                user_id,
            )
            active_count = await self._repo.get_active_job_count(active_conn, user_id)
            if active_count >= tier_config.max_concurrent_generation:
                raise GenerationConcurrentLimitExceeded(
                    f"Max {tier_config.max_concurrent_generation} concurrent generation jobs"
                )
            return await self._repo.create_job(
                conn=active_conn,
                user_id=user_id,
                composition_spec=composition_spec.model_dump(mode="json"),
                total_cadres=len(composition_spec.cadres),
                cadres=cadres_data,
                video_project_id=video_project_id,
                project_revision=project_revision,
            )

        if conn is not None:
            job_id = await _create_job(conn)
        else:
            async with self._repo._acquire_connection() as managed_conn:
                async with managed_conn.transaction():
                    job_id = await _create_job(managed_conn)

        if dispatch:
            await self.dispatch_job(job_id)

        return {
            "job_id": job_id,
            "status": "pending",
            "cadre_count": len(composition_spec.cadres),
            "estimated_cost_cents": estimated_cost,
        }

    async def get_job_status(self, user_id: UUID, job_id: UUID) -> dict | None:
        """Get job status with cadre details. Returns None on IDOR."""
        data = await self._repo.get_job(job_id, user_id)
        if not data:
            return None

        job = data["job"]
        cadres = data["cadres"]

        video_url = None
        video_url_expires_at = None
        if job.get("r2_key") and job["status"] == "completed" and self._storage is not None:
            video_url = await self._storage.get_presigned_url(job["r2_key"])
            video_url_expires_at = datetime.now(timezone.utc) + timedelta(seconds=PRESIGNED_URL_EXPIRY)

        completed_cadres = sum(1 for c in cadres if c["status"] == "completed")
        total_cost = sum(c.get("cost_cents") or 0 for c in cadres if c["status"] != "failed")

        thumbnail_urls: list[str | None] = []
        if self._storage is not None:
            thumbnail_urls = await asyncio.gather(*[
                self._get_optional_presigned_url(c.get("frame_r2_key"))
                if c.get("frame_r2_key")
                else asyncio.sleep(0, result=None)
                for c in cadres
            ])
        else:
            thumbnail_urls = [None for _ in cadres]

        return {
            "job_id": job["id"],
            "status": job["status"],
            "current_cadre": completed_cadres,
            "total_cadres": job["total_cadres"],
            "video_project_id": job.get("video_project_id"),
            "video_url": video_url,
            "video_url_expires_at": video_url_expires_at,
            "cost_cents": total_cost,
            "cadre_statuses": [
                {
                    "index": c["cadre_index"],
                    "status": c["status"],
                    "error": c.get("error"),
                    "thumbnail_url": thumbnail_urls[idx],
                }
                for idx, c in enumerate(cadres)
            ],
            "error": job.get("error"),
        }

    async def list_jobs(
        self,
        user_id: UUID,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List user's generation jobs."""
        jobs, total = await self._repo.list_jobs(user_id, status_filter, limit, offset)
        return {
            "jobs": [
                {
                    "id": j["id"],
                    "status": j["status"],
                    "created_at": j["created_at"],
                    "cadre_count": j["total_cadres"],
                    "video_url": None,
                }
                for j in jobs
            ],
            "total": total,
        }

    async def cancel_job(self, user_id: UUID, job_id: UUID) -> dict | None:
        """Request job cancellation. Returns None on IDOR."""
        row = await self._repo.request_cancellation(job_id, user_id)
        if not row:
            return None
        return {
            "job_id": row["id"],
            "status": row["status"],
            "cancellation_requested": True,
        }

    async def dispatch_job(self, job_id: UUID) -> None:
        logger.info("dispatch_job called for %s, dispatch_fn=%s", job_id, self._dispatch_fn)
        if self._dispatch_fn is None:
            logger.warning("Generation job %s created but dispatch is not configured", job_id)
            return
        try:
            result = self._dispatch_fn(job_id)
            if asyncio.iscoroutine(result):
                await result
            logger.info("dispatch_job completed for %s", job_id)
        except Exception:
            logger.exception("Failed to dispatch generation job %s — job created but will not process", job_id)

    async def _get_optional_presigned_url(self, r2_key: str | None) -> str | None:
        if not r2_key or self._storage is None:
            return None
        try:
            return await self._storage.get_presigned_url(r2_key)
        except Exception:
            logger.warning("Failed to presign generation asset: %s", r2_key, exc_info=True)
            return None
