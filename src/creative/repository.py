"""PostgreSQL creative pattern repository - JSONB approach."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID, uuid4

import asyncpg

from ..analysis.exceptions import PoolExhaustedError
from ..schemas import CreativePatterns

logger = logging.getLogger(__name__)


class PostgresCreativePatternRepository:
    """PostgreSQL implementation for creative pattern storage using JSONB."""

    ACQUIRE_TIMEOUT = 5.0

    _GET_BY_ANALYSIS_ID = """
        SELECT patterns FROM creative_patterns WHERE video_analysis_id = $1 LIMIT 1
    """

    _UPSERT = """
        INSERT INTO creative_patterns (id, video_analysis_id, patterns)
        VALUES ($1, $2, $3)
        ON CONFLICT (video_analysis_id)
        DO UPDATE SET patterns = EXCLUDED.patterns, updated_at = NOW()
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

    async def get_by_analysis_id(self, video_analysis_id: UUID) -> CreativePatterns | None:
        """Return cached creative patterns or None."""
        async with self._acquire_connection() as conn:
            row: asyncpg.Record | None = await conn.fetchrow(
                self._GET_BY_ANALYSIS_ID, video_analysis_id
            )
            if row and row["patterns"]:
                return CreativePatterns.model_validate_json(row["patterns"])
            return None

    async def save(self, patterns: CreativePatterns, video_analysis_id: UUID) -> bool:
        """Insert or update creative patterns. Returns False on FK violation."""
        try:
            async with self._acquire_connection() as conn:
                await conn.execute(
                    self._UPSERT,
                    uuid4(),
                    video_analysis_id,
                    patterns.model_dump_json(),
                )
                return True
        except asyncpg.ForeignKeyViolationError:
            logger.warning(
                "Video analysis %s not found, cannot save creative patterns",
                video_analysis_id,
            )
            return False
