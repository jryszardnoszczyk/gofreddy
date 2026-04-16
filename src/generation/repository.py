"""PostgreSQL repository for video generation jobs."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import asyncpg

from .exceptions import GenerationError

logger = logging.getLogger(__name__)

ACQUIRE_TIMEOUT = 5.0


class PostgresGenerationRepository:
    """PostgreSQL repository for generation jobs and cadres."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        try:
            async with asyncio.timeout(ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise GenerationError("Database connection pool exhausted")
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def create_job(
        self,
        conn: asyncpg.Connection,
        user_id: UUID,
        composition_spec: dict,
        total_cadres: int,
        cadres: list[dict],
        *,
        video_project_id: UUID | None = None,
        project_revision: int | None = None,
    ) -> UUID:
        """Create job + cadres in a single transaction (caller owns txn)."""
        job_id = await conn.fetchval(
            """INSERT INTO generation_jobs
                (user_id, composition_spec, total_cadres, status, video_project_id, project_revision)
               VALUES ($1, $2::jsonb, $3, 'pending', $4, $5)
               RETURNING id""",
            user_id,
            json.dumps(composition_spec),
            total_cadres,
            video_project_id,
            project_revision,
        )
        for cadre in cadres:
            await conn.execute(
                """INSERT INTO generation_cadres
                    (job_id, cadre_index, prompt, duration_seconds, transition, seed_image_storage_key, status)
                   VALUES ($1, $2, $3, $4, $5, $6, 'pending')""",
                job_id,
                cadre["index"],
                cadre["prompt"],
                cadre["duration_seconds"],
                cadre.get("transition", "fade"),
                cadre.get("seed_image_storage_key"),
            )
        return job_id

    async def get_job(self, job_id: UUID, user_id: UUID) -> dict | None:
        """Get job with cadres. Returns None if not found or IDOR."""
        async with self._acquire_connection() as conn:
            job_row = await conn.fetchrow(
                "SELECT * FROM generation_jobs WHERE id = $1 AND user_id = $2",
                job_id,
                user_id,
            )
            if not job_row:
                return None
            cadre_rows = await conn.fetch(
                "SELECT * FROM generation_cadres WHERE job_id = $1 ORDER BY cadre_index",
                job_id,
            )
            return {
                "job": dict(job_row),
                "cadres": [dict(r) for r in cadre_rows],
            }

    async def list_jobs(
        self,
        user_id: UUID,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """List jobs for user. Returns (jobs, total_count)."""
        async with self._acquire_connection() as conn:
            if status_filter:
                rows = await conn.fetch(
                    """SELECT * FROM generation_jobs
                       WHERE user_id = $1 AND status = $2
                       ORDER BY created_at DESC
                       LIMIT $3 OFFSET $4""",
                    user_id,
                    status_filter,
                    limit,
                    offset,
                )
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM generation_jobs WHERE user_id = $1 AND status = $2",
                    user_id,
                    status_filter,
                )
            else:
                rows = await conn.fetch(
                    """SELECT * FROM generation_jobs
                       WHERE user_id = $1
                       ORDER BY created_at DESC
                       LIMIT $2 OFFSET $3""",
                    user_id,
                    limit,
                    offset,
                )
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM generation_jobs WHERE user_id = $1",
                    user_id,
                )
            return [dict(r) for r in rows], int(total or 0)

    async def request_cancellation(self, job_id: UUID, user_id: UUID) -> dict | None:
        """Set cancellation_requested=TRUE. Returns updated job or None (IDOR)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """UPDATE generation_jobs
                   SET cancellation_requested = TRUE,
                       status = CASE WHEN status = 'pending' THEN 'cancelled' ELSE status END,
                       updated_at = NOW()
                   WHERE id = $1 AND user_id = $2
                     AND status IN ('pending', 'generating', 'composing')
                   RETURNING *""",
                job_id,
                user_id,
            )
            return dict(row) if row else None

    async def check_cancellation(self, job_id: UUID) -> bool:
        async with self._acquire_connection() as conn:
            return bool(
                await conn.fetchval(
                    "SELECT cancellation_requested FROM generation_jobs WHERE id = $1",
                    job_id,
                )
            )

    async def get_active_job_count(self, conn: asyncpg.Connection, user_id: UUID) -> int:
        """Count active jobs. Must be called within a transaction with FOR UPDATE lock."""
        count = await conn.fetchval(
            """SELECT COUNT(*) FROM generation_jobs
               WHERE user_id = $1
                 AND status IN ('pending', 'generating', 'composing')
                 AND cancellation_requested = FALSE""",
            user_id,
        )
        return int(count or 0)

    async def get_user_daily_generation_cost(self, user_id: UUID) -> int:
        """Sum cost_cents for today's non-failed cadres."""
        async with self._acquire_connection() as conn:
            cost = await conn.fetchval(
                """SELECT COALESCE(SUM(gc.cost_cents), 0)
                   FROM generation_cadres gc
                   JOIN generation_jobs gj ON gc.job_id = gj.id
                   WHERE gj.user_id = $1
                     AND gc.created_at >= CURRENT_DATE
                     AND gc.status != 'failed'""",
                user_id,
            )
            return int(cost or 0)

    async def update_job_status(
        self,
        job_id: UUID,
        status: str,
        error: str | None = None,
        r2_key: str | None = None,
    ) -> None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """UPDATE generation_jobs
                   SET status = $2, error = $3, r2_key = $4, updated_at = NOW()
                   WHERE id = $1
                   RETURNING video_project_id, project_revision""",
                job_id,
                status,
                error[:500] if error else None,
                r2_key,
            )
            if not row or row["video_project_id"] is None:
                return

            project_id = row["video_project_id"]
            project_revision = row["project_revision"]
            current_revision = await conn.fetchval(
                "SELECT revision FROM video_projects WHERE id = $1",
                project_id,
            )
            if current_revision is None or project_revision != current_revision:
                return

            if status in {"pending", "generating", "composing", "cancelling"}:
                project_status = "rendering"
                project_error = None
            elif status == "completed":
                project_status = "render_complete"
                project_error = None
            elif status == "cancelled":
                project_status = "failed"
                project_error = "cancelled"
            else:
                project_status = "failed"
                project_error = error[:500] if error else status

            await conn.execute(
                """UPDATE video_projects
                   SET status = $2, last_error = $3, updated_at = NOW()
                   WHERE id = $1""",
                project_id,
                project_status,
                project_error,
            )

            if status == "completed":
                await self._backfill_project_scene_previews(
                    conn,
                    job_id=job_id,
                    project_id=project_id,
                    project_revision=project_revision,
                )

    async def update_cadre_status(
        self,
        cadre_id: UUID,
        status: str,
        grok_request_id: str | None = None,
        r2_key: str | None = None,
        error: str | None = None,
        frame_r2_key: str | None = None,
        cost_cents: int | None = None,
        reservation_id: UUID | None = None,
    ) -> None:
        async with self._acquire_connection() as conn:
            await conn.execute(
                """UPDATE generation_cadres
                   SET status = $2, grok_request_id = $3, r2_key = $4,
                       error = $5, frame_r2_key = $6, cost_cents = $7,
                       reservation_id = $8, updated_at = NOW()
                   WHERE id = $1""",
                cadre_id,
                status,
                grok_request_id,
                r2_key,
                error[:500] if error else None,
                frame_r2_key,
                cost_cents,
                reservation_id,
            )

    async def reap_stale_jobs(self, max_age_minutes: int = 30) -> int:
        """Mark stale 'generating' jobs as failed on startup.

        Also updates linked video_projects to 'failed' so they don't stay
        stuck in 'rendering' status.
        """
        async with self._acquire_connection() as conn:
            # Find and fail stale jobs, returning their IDs for project cleanup
            reaped = await conn.fetch(
                """UPDATE generation_jobs SET status = 'failed', error = 'stale_reap'
                   WHERE status = 'generating'
                   AND claimed_at < NOW() - INTERVAL '1 minute' * $1
                   RETURNING id, video_project_id""",
                max_age_minutes,
            )
            # Update linked video_projects to failed
            for row in reaped:
                if row["video_project_id"]:
                    await conn.execute(
                        """UPDATE video_projects SET status = 'failed'
                           WHERE id = $1 AND status = 'rendering'""",
                        row["video_project_id"],
                    )
            return len(reaped)

    async def _backfill_project_scene_previews(
        self,
        conn: asyncpg.Connection,
        *,
        job_id: UUID,
        project_id: UUID,
        project_revision: int | None,
    ) -> None:
        current_revision = await conn.fetchval(
            "SELECT revision FROM video_projects WHERE id = $1",
            project_id,
        )
        if current_revision is None or project_revision != current_revision:
            return

        cadre_rows = await conn.fetch(
            """
            SELECT cadre_index, frame_r2_key
            FROM generation_cadres
            WHERE job_id = $1
              AND status = 'completed'
              AND frame_r2_key IS NOT NULL
            ORDER BY cadre_index ASC
            """,
            job_id,
        )
        for row in cadre_rows:
            await conn.execute(
                """
                UPDATE video_project_scenes
                SET preview_status = CASE
                        WHEN preview_storage_key IS NULL THEN 'ready'
                        ELSE preview_status
                    END,
                    preview_storage_key = COALESCE(preview_storage_key, $3),
                    preview_approved = CASE
                        WHEN preview_storage_key IS NULL THEN TRUE
                        ELSE preview_approved
                    END,
                    last_error = CASE
                        WHEN preview_storage_key IS NULL THEN NULL
                        ELSE last_error
                    END,
                    updated_at = NOW()
                WHERE project_id = $1
                  AND position = $2
                """,
                project_id,
                row["cadre_index"],
                row["frame_r2_key"],
            )
