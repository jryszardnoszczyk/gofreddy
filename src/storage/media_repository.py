"""PostgreSQL repository for media assets."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MediaAsset:
    """Immutable media-asset row."""

    id: UUID
    org_id: UUID
    r2_key: str
    filename: str
    content_type: str
    asset_type: str
    source: str
    size_bytes: int | None
    status: str
    metadata: dict[str, Any]
    source_generation_id: UUID | None
    source_project_id: UUID | None
    source_scene_id: UUID | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: asyncpg.Record) -> MediaAsset:
        raw_meta = row["metadata"]
        if isinstance(raw_meta, str):
            meta = json.loads(raw_meta)
        else:
            meta = raw_meta or {}
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            r2_key=row["r2_key"],
            filename=row["filename"],
            content_type=row["content_type"],
            asset_type=row["asset_type"],
            source=row["source"],
            size_bytes=row["size_bytes"],
            status=row["status"],
            metadata=meta,
            source_generation_id=row.get("source_generation_id"),
            source_project_id=row.get("source_project_id"),
            source_scene_id=row.get("source_scene_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class PostgresMediaAssetRepository:
    """PostgreSQL repository for media assets."""

    ACQUIRE_TIMEOUT = 5.0

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[asyncpg.Connection]:
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise PoolExhaustedError(
                pool_size=self._pool.get_size(),
                timeout_seconds=self.ACQUIRE_TIMEOUT,
            )
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    # ── create ──

    async def create_asset(
        self,
        org_id: UUID,
        r2_key: str,
        filename: str,
        content_type: str,
        asset_type: str,
        source: str,
        size_bytes: int | None = None,
    ) -> MediaAsset:
        """Insert a new asset in 'pending' status."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO media_assets
                    (org_id, r2_key, filename, content_type, asset_type, source, size_bytes, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending', '{}')
                RETURNING *
                """,
                org_id, r2_key, filename, content_type, asset_type, source, size_bytes,
            )
            return MediaAsset.from_row(row)

    # ── confirm upload ──

    async def confirm_asset(
        self, asset_id: UUID, org_id: UUID, size_bytes: int
    ) -> MediaAsset | None:
        """Transition asset from 'pending' to 'ready'."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE media_assets
                SET status = 'ready', size_bytes = $3, updated_at = NOW()
                WHERE id = $1 AND org_id = $2 AND status = 'pending' AND deleted_at IS NULL
                RETURNING *
                """,
                asset_id, org_id, size_bytes,
            )
            return MediaAsset.from_row(row) if row else None

    # ── read ──

    async def get_asset(self, asset_id: UUID, org_id: UUID) -> MediaAsset | None:
        """Get a single asset, excluding soft-deleted rows."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM media_assets
                WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL
                """,
                asset_id, org_id,
            )
            return MediaAsset.from_row(row) if row else None

    async def list_assets(
        self,
        org_id: UUID,
        *,
        asset_type: str | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MediaAsset]:
        """List assets with optional filters."""
        conditions = ["org_id = $1", "deleted_at IS NULL"]
        params: list[Any] = [org_id]
        idx = 2

        if asset_type is not None:
            conditions.append(f"asset_type = ${idx}")
            params.append(asset_type)
            idx += 1

        if source is not None:
            conditions.append(f"source = ${idx}")
            params.append(source)
            idx += 1

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        query = f"""
            SELECT * FROM media_assets
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """

        async with self._acquire_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [MediaAsset.from_row(r) for r in rows]

    # ── soft delete ──

    async def soft_delete(self, asset_id: UUID, org_id: UUID) -> bool:
        """Soft-delete an asset. Returns True if a row was updated."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(
                """
                UPDATE media_assets SET deleted_at = NOW(), updated_at = NOW()
                WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL
                """,
                asset_id, org_id,
            )
            return result == "UPDATE 1"

    # ── cleanup ──

    async def cleanup_pending(self, max_age_hours: int = 24) -> int:
        """Hard-delete assets stuck in 'pending' longer than max_age_hours."""
        async with self._acquire_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM media_assets
                WHERE status = 'pending'
                  AND created_at < NOW() - make_interval(hours => $1)
                """,
                max_age_hours,
            )
            # result is e.g. "DELETE 5"
            return int(result.split()[-1])

    # ── generation-linked creation ──

    async def create_from_generation(
        self,
        org_id: UUID,
        r2_key: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        source_generation_id: UUID,
        source_project_id: UUID,
        source_scene_id: UUID | None = None,
    ) -> MediaAsset:
        """Create a 'ready' asset linked to a generation pipeline."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO media_assets
                    (org_id, r2_key, filename, content_type, asset_type, source,
                     size_bytes, status, metadata,
                     source_generation_id, source_project_id, source_scene_id)
                VALUES ($1, $2, $3, $4, 'generated', 'generation',
                        $5, 'ready', '{}',
                        $6, $7, $8)
                RETURNING *
                """,
                org_id, r2_key, filename, content_type,
                size_bytes,
                source_generation_id, source_project_id, source_scene_id,
            )
            return MediaAsset.from_row(row)

    # ── counts ──

    async def count_pending(self, org_id: UUID) -> int:
        """Count pending uploads for an org (for per-user cap enforcement)."""
        async with self._acquire_connection() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM media_assets
                WHERE org_id = $1 AND status = 'pending' AND deleted_at IS NULL
                """,
                org_id,
            )
