"""PostgreSQL analysis repository."""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import replace
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from .exceptions import IntegrityError, PoolExhaustedError
from .models import CreatorGroup, LibraryFilters, LibraryItem, SessionGroup, VideoAnalysisRecord


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards to prevent injection."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class PostgresAnalysisRepository:
    """PostgreSQL implementation using asyncpg with UPSERT."""

    ACQUIRE_TIMEOUT = 5.0

    _GET_BY_CACHE_KEY = """
        SELECT * FROM video_analysis WHERE cache_key = $1 LIMIT 1
    """

    _GET_BY_ID = """
        SELECT * FROM video_analysis WHERE id = $1 LIMIT 1
    """

    _GRANT_USER_ACCESS = """
        INSERT INTO video_analysis_access (video_analysis_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT (video_analysis_id, user_id) DO NOTHING
    """

    _USER_HAS_ACCESS = """
        SELECT EXISTS (
            SELECT 1
            FROM video_analysis_access
            WHERE video_analysis_id = $1 AND user_id = $2
        )
    """

    _BATCH_USER_ACCESS = """
        SELECT video_analysis_id FROM video_analysis_access
        WHERE video_analysis_id = ANY($1) AND user_id = $2
    """

    _LINK_TO_CREATOR = """
        UPDATE video_analysis
        SET creator_id = $1
        WHERE cache_key = ANY($2::text[])
          AND creator_id IS NULL
    """

    _UPSERT = """
        INSERT INTO video_analysis (
            id, video_id, cache_key, overall_safe, overall_confidence,
            risks_detected, summary, content_categories, moderation_flags, sponsored_content,
            processing_time_seconds, token_count,
            error, model_version, analyzed_at, analysis_cost_usd, title
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), $15, $16)
        ON CONFLICT (cache_key) DO UPDATE SET
            overall_safe = EXCLUDED.overall_safe,
            overall_confidence = EXCLUDED.overall_confidence,
            risks_detected = EXCLUDED.risks_detected,
            summary = EXCLUDED.summary,
            content_categories = EXCLUDED.content_categories,
            moderation_flags = EXCLUDED.moderation_flags,
            sponsored_content = EXCLUDED.sponsored_content,
            processing_time_seconds = EXCLUDED.processing_time_seconds,
            token_count = EXCLUDED.token_count,
            error = EXCLUDED.error,
            analyzed_at = NOW(),
            analysis_cost_usd = EXCLUDED.analysis_cost_usd,
            title = COALESCE(EXCLUDED.title, video_analysis.title)
        RETURNING id
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        """Acquire connection with proper error handling."""
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

    async def get_by_cache_key(self, cache_key: str) -> VideoAnalysisRecord | None:
        """Fetch analysis by cache key."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_CACHE_KEY, cache_key)
            return VideoAnalysisRecord.from_row(row) if row else None

    async def get_by_id(self, analysis_id: UUID) -> VideoAnalysisRecord | None:
        """Fetch analysis by ID."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, analysis_id)
            return VideoAnalysisRecord.from_row(row) if row else None

    async def grant_user_access(self, analysis_id: UUID, user_id: UUID) -> None:
        """Grant a user access to a video analysis record."""
        async with self._acquire_connection() as conn:
            await conn.execute(self._GRANT_USER_ACCESS, analysis_id, user_id)

    async def user_has_access(self, analysis_id: UUID, user_id: UUID) -> bool:
        """Check whether a user has access to a video analysis record."""
        async with self._acquire_connection() as conn:
            has_access = await conn.fetchval(self._USER_HAS_ACCESS, analysis_id, user_id)
            return bool(has_access)

    async def batch_user_has_access(self, analysis_ids: list[UUID], user_id: UUID) -> set[UUID]:
        """Batch check user access to multiple analyses. Returns set of authorized IDs."""
        if not analysis_ids:
            return set()
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._BATCH_USER_ACCESS, analysis_ids, user_id)
            return {row["video_analysis_id"] for row in rows}

    async def link_to_creator(self, creator_id: UUID, cache_keys: list[str]) -> int:
        """Link video_analysis records to a creator by cache key.

        Returns the number of rows updated.
        """
        if not cache_keys:
            return 0
        async with self._acquire_connection() as conn:
            result = await conn.execute(self._LINK_TO_CREATOR, creator_id, cache_keys)
            # asyncpg returns e.g. "UPDATE 3"
            return int(result.split()[-1]) if result else 0

    _LIST_FOR_USER = """
        SELECT va.id, va.video_id, va.title, va.platform,
          va.overall_safe, va.moderation_flags, va.analyzed_at,
          EXISTS(SELECT 1 FROM brand_video_analysis WHERE video_analysis_id = va.id) AS has_brands,
          EXISTS(SELECT 1 FROM audience_demographics WHERE video_analysis_id = va.id) AS has_demographics,
          EXISTS(SELECT 1 FROM deepfake_analysis WHERE video_analysis_id = va.id) AS has_deepfake,
          EXISTS(SELECT 1 FROM creative_patterns WHERE video_analysis_id = va.id) AS has_creative,
          EXISTS(
            SELECT 1 FROM creator_fraud_analysis cfa
            WHERE cfa.creator_id = va.creator_id
              AND cfa.user_id = $1
          ) AS has_fraud
        FROM video_analysis va
        JOIN video_analysis_access vaa ON va.id = vaa.video_analysis_id
        WHERE vaa.user_id = $1
          AND ($2::text IS NULL OR va.platform = $2)
          AND ($3::text IS NULL OR va.title ILIKE $3)
          AND (($4::timestamptz IS NULL) OR (va.analyzed_at, va.id) < ($4, $5::uuid))
        ORDER BY va.analyzed_at DESC, va.id DESC
        LIMIT $6
    """

    _LIST_BY_CREATOR = """
        SELECT c.id AS creator_id, c.platform, c.username,
          COUNT(va.id) AS video_count,
          MAX(va.analyzed_at) AS last_analyzed_at
        FROM creators c
        JOIN video_analysis va ON va.creator_id = c.id
        JOIN video_analysis_access vaa ON vaa.video_analysis_id = va.id
        WHERE vaa.user_id = $1
        GROUP BY c.id, c.platform, c.username
        ORDER BY last_analyzed_at DESC
        LIMIT $2
        OFFSET $3
    """

    _LIST_BY_SESSION = """
        SELECT conv.id AS conversation_id, conv.title,
          COALESCE(SUM(wc.item_count), 0)::int AS item_count,
          GREATEST(conv.updated_at, MAX(wc.updated_at)) AS last_updated_at
        FROM conversations conv
        JOIN workspace_collections wc ON wc.conversation_id = conv.id
        WHERE conv.user_id = $1
          AND wc.item_count > 0
        GROUP BY conv.id, conv.title, conv.updated_at
        ORDER BY last_updated_at DESC
        LIMIT $2
        OFFSET $3
    """

    async def list_for_user(
        self,
        user_id: UUID,
        filters: LibraryFilters,
    ) -> tuple[list[LibraryItem], bool]:
        """List analyses accessible to user with filters.

        Returns (items, has_more). Fetches limit+1 to determine has_more.
        Uses keyset pagination on (analyzed_at, id).
        """
        # Prepare search param with escaped wildcards
        search_param = None
        if filters.search:
            search_param = f"%{_escape_like(filters.search)}%"

        fetch_limit = filters.limit + 1
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._LIST_FOR_USER,
                user_id,
                filters.platform,
                search_param,
                filters.cursor_date,
                filters.cursor_id,
                fetch_limit,
            )

        has_more = len(rows) > filters.limit
        result_rows = rows[: filters.limit]

        items = []
        for row in result_rows:
            mflags = row["moderation_flags"]
            if isinstance(mflags, str):
                mflags = json.loads(mflags)
            items.append(LibraryItem(
                id=row["id"],
                video_id=row["video_id"],
                title=row["title"],
                platform=row["platform"],
                overall_safe=row["overall_safe"],
                moderation_flags=mflags or [],
                analyzed_at=row["analyzed_at"],
                has_brands=row["has_brands"],
                has_demographics=row["has_demographics"],
                has_deepfake=row["has_deepfake"],
                has_creative=row["has_creative"],
                has_fraud=row["has_fraud"],
            ))

        return items, has_more

    async def save(self, record: VideoAnalysisRecord) -> VideoAnalysisRecord:
        """Save or update analysis record using UPSERT."""

        try:
            async with self._acquire_connection() as conn:
                persisted_id = await conn.fetchval(
                    self._UPSERT,
                    record.id,
                    record.video_id,
                    record.cache_key,
                    record.overall_safe,
                    record.overall_confidence,
                    json.dumps(record.risks_detected),
                    record.summary,
                    json.dumps(record.content_categories),
                    json.dumps(record.moderation_flags),
                    json.dumps(record.sponsored_content) if record.sponsored_content else None,
                    record.processing_time_seconds,
                    record.token_count,
                    record.error,
                    record.model_version,
                    record.analysis_cost_usd,
                    record.title,
                )
                if isinstance(persisted_id, UUID) and persisted_id != record.id:
                    return replace(record, id=persisted_id)
                return record
        except asyncpg.ForeignKeyViolationError:
            raise IntegrityError(
                constraint="video_analysis_video_id_fkey",
                detail=f"Video does not exist: {record.video_id}",
            )

    async def list_by_creator(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CreatorGroup]:
        """List analyses grouped by creator for a user."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_BY_CREATOR, user_id, limit, offset)

        return [
            CreatorGroup(
                creator_id=row["creator_id"],
                platform=row["platform"],
                username=row["username"],
                video_count=row["video_count"],
                last_analyzed_at=row["last_analyzed_at"],
            )
            for row in rows
        ]

    async def list_by_session(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SessionGroup]:
        """List analyses grouped by conversation/session for a user."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_BY_SESSION, user_id, limit, offset)

        return [
            SessionGroup(
                conversation_id=row["conversation_id"],
                title=row["title"],
                item_count=row["item_count"],
                last_updated_at=row["last_updated_at"],
            )
            for row in rows
        ]
