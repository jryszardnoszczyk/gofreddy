"""PostgreSQL fraud analysis repository."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager, suppress
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError  # noqa: F401
from .models import FraudAnalysisRecord


class PostgresFraudRepository:
    """PostgreSQL implementation for fraud analysis storage."""

    ACQUIRE_TIMEOUT = 5.0

    _GET_BY_CACHE_KEY = """
        SELECT id, creator_id, platform, username, cache_key,
               fake_follower_percentage, fake_follower_confidence, follower_sample_size,
               engagement_rate, engagement_tier, engagement_anomaly,
               bot_comment_ratio, comments_analyzed, bot_patterns_detected,
               aqs_score, aqs_grade, aqs_components, growth_data_available,
               fraud_risk_level, fraud_risk_score,
               analyzed_at, expires_at, model_version
        FROM creator_fraud_analysis
        WHERE cache_key = $1 AND expires_at > NOW()
        LIMIT 1
    """

    _GET_BY_ID = """
        SELECT id, creator_id, platform, username, cache_key,
               fake_follower_percentage, fake_follower_confidence, follower_sample_size,
               engagement_rate, engagement_tier, engagement_anomaly,
               bot_comment_ratio, comments_analyzed, bot_patterns_detected,
               aqs_score, aqs_grade, aqs_components, growth_data_available,
               fraud_risk_level, fraud_risk_score,
               analyzed_at, expires_at, model_version
        FROM creator_fraud_analysis
        WHERE id = $1
        LIMIT 1
    """

    _GET_BY_ID_AND_USER = """
        SELECT id, creator_id, platform, username, cache_key,
               fake_follower_percentage, fake_follower_confidence, follower_sample_size,
               engagement_rate, engagement_tier, engagement_anomaly,
               bot_comment_ratio, comments_analyzed, bot_patterns_detected,
               aqs_score, aqs_grade, aqs_components, growth_data_available,
               fraud_risk_level, fraud_risk_score,
               analyzed_at, expires_at, model_version
        FROM creator_fraud_analysis
        WHERE id = $1 AND (user_id = $2 OR user_id IS NULL)
        LIMIT 1
    """

    _INSERT = """
        INSERT INTO creator_fraud_analysis (
            id, creator_id, platform, username, cache_key,
            fake_follower_percentage, fake_follower_confidence, follower_sample_size,
            engagement_rate, engagement_tier, engagement_anomaly,
            bot_comment_ratio, comments_analyzed, bot_patterns_detected,
            aqs_score, aqs_grade, aqs_components, growth_data_available,
            fraud_risk_level, fraud_risk_score,
            analyzed_at, expires_at, model_version, user_id
        ) VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8,
            $9, $10, $11,
            $12, $13, $14,
            $15, $16, $17, $18,
            $19, $20,
            $21, $22, $23, $24
        )
    """

    _DELETE_STALE = """
        DELETE FROM creator_fraud_analysis WHERE cache_key = $1
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
            # Be defensive during teardown/error paths so release issues
            # don't mask the original exception.
            with suppress(Exception):
                await self._pool.release(conn)

    async def get_by_cache_key(self, cache_key: str) -> FraudAnalysisRecord | None:
        """Fetch non-expired analysis by cache key."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_CACHE_KEY, cache_key)
            if row is None:
                return None

            return self._row_to_record(row)

    async def get_by_id(self, analysis_id: UUID) -> FraudAnalysisRecord | None:
        """Fetch analysis by ID (no ownership check)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, analysis_id)
            if row is None:
                return None

            return self._row_to_record(row)

    async def get_by_id_and_user(self, analysis_id: UUID, user_id: UUID) -> FraudAnalysisRecord | None:
        """Fetch analysis by ID with ownership check. Allows legacy rows (user_id IS NULL)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID_AND_USER, analysis_id, user_id)
            if row is None:
                return None

            return self._row_to_record(row)

    async def save(self, record: FraudAnalysisRecord, user_id: UUID | None = None) -> FraudAnalysisRecord:
        """Save fraud analysis record.

        Uses transaction to delete stale entry before insert (cache invalidation).
        """
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                # Delete stale entry if exists (force refresh)
                await conn.execute(self._DELETE_STALE, record.cache_key)

                # Insert new entry
                await conn.execute(
                    self._INSERT,
                    record.id,
                    record.creator_id,
                    record.platform,
                    record.username,
                    record.cache_key,
                    record.fake_follower_percentage,
                    record.fake_follower_confidence,
                    record.follower_sample_size,
                    record.engagement_rate,
                    record.engagement_tier,
                    record.engagement_anomaly,
                    record.bot_comment_ratio,
                    record.comments_analyzed,
                    json.dumps(record.bot_patterns_detected),
                    record.aqs_score,
                    record.aqs_grade,
                    json.dumps(record.aqs_components),
                    record.growth_data_available,
                    record.fraud_risk_level.value,
                    record.fraud_risk_score,
                    record.analyzed_at,
                    record.expires_at,
                    record.model_version,
                    user_id,
                )

        return record

    def _row_to_record(self, row: asyncpg.Record) -> FraudAnalysisRecord:
        """Convert database row to FraudAnalysisRecord."""
        from .models import FraudRiskLevel

        # Parse JSONB fields
        bot_patterns = row["bot_patterns_detected"]
        if isinstance(bot_patterns, str):
            bot_patterns = json.loads(bot_patterns)

        aqs_components = row["aqs_components"]
        if isinstance(aqs_components, str):
            aqs_components = json.loads(aqs_components)

        return FraudAnalysisRecord(
            id=row["id"],
            creator_id=row["creator_id"],
            platform=row["platform"],
            username=row["username"],
            cache_key=row["cache_key"],
            fake_follower_percentage=row["fake_follower_percentage"],
            fake_follower_confidence=row["fake_follower_confidence"],
            follower_sample_size=row["follower_sample_size"],
            engagement_rate=row["engagement_rate"],
            engagement_tier=row["engagement_tier"],
            engagement_anomaly=row["engagement_anomaly"],
            bot_comment_ratio=row["bot_comment_ratio"],
            comments_analyzed=row["comments_analyzed"],
            bot_patterns_detected=bot_patterns or [],
            aqs_score=row["aqs_score"],
            aqs_grade=row["aqs_grade"],
            aqs_components=aqs_components or {},
            growth_data_available=row["growth_data_available"],
            fraud_risk_level=FraudRiskLevel(row["fraud_risk_level"]),
            fraud_risk_score=row["fraud_risk_score"],
            analyzed_at=row["analyzed_at"],
            expires_at=row["expires_at"],
            model_version=row["model_version"],
        )
