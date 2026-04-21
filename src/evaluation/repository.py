"""PostgreSQL evaluation results repository."""

from __future__ import annotations

import asyncio
import json
import statistics
from contextlib import asynccontextmanager, suppress
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError
from .models import EvaluationRecord


class PostgresEvaluationRepository:
    """PostgreSQL implementation for evaluation result storage."""

    ACQUIRE_TIMEOUT = 5.0

    _GET_BY_ID = """
        SELECT id, campaign_id, domain, variant_id, domain_score,
               grounding_score, structural_passed, length_factor,
               dimension_scores, rubric_version, content_hash,
               user_id, created_at
        FROM evaluation_results
        WHERE id = $1 AND (user_id = $2 OR user_id IS NULL)
    """

    _GET_BY_CONTENT_HASH = """
        SELECT id, campaign_id, domain, variant_id, domain_score,
               grounding_score, structural_passed, length_factor,
               dimension_scores, rubric_version, content_hash,
               user_id, created_at
        FROM evaluation_results
        WHERE content_hash = $1 AND rubric_version = $2
        LIMIT 1
    """

    _GET_BY_CAMPAIGN = """
        SELECT id, campaign_id, domain, variant_id, domain_score,
               grounding_score, structural_passed, length_factor,
               dimension_scores, rubric_version, content_hash,
               user_id, created_at
        FROM evaluation_results
        WHERE campaign_id = $1 AND (user_id = $2 OR user_id IS NULL)
        ORDER BY created_at ASC
    """

    _INSERT = """
        INSERT INTO evaluation_results (
            id, campaign_id, domain, variant_id, domain_score,
            grounding_score, structural_passed, length_factor,
            dimension_scores, rubric_version, content_hash,
            user_id
        ) VALUES (
            $1, $2, $3, $4, $5,
            $6, $7, $8,
            $9::jsonb, $10, $11,
            $12
        )
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
            with suppress(Exception):
                await self._pool.release(conn)

    async def get_by_id(self, evaluation_id: UUID, user_id: UUID | None = None) -> EvaluationRecord | None:
        """Fetch evaluation by ID with user ownership check."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, evaluation_id, user_id)
            if row is None:
                return None
            return self._row_to_record(row)

    async def get_by_content_hash(
        self, content_hash: str, rubric_version: str
    ) -> EvaluationRecord | None:
        """Fetch cached evaluation by content hash + rubric version."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_BY_CONTENT_HASH, content_hash, rubric_version
            )
            if row is None:
                return None
            return self._row_to_record(row)

    async def get_by_campaign(self, campaign_id: str, user_id: UUID | None = None) -> list[EvaluationRecord]:
        """Fetch all evaluations in a campaign with user ownership check."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_BY_CAMPAIGN, campaign_id, user_id)
            return [self._row_to_record(row) for row in rows]

    async def criterion_sd_for_variant(self, variant_id: str) -> dict[str, float]:
        """For each criterion, SD of per-sample normalized_score across the ensemble.

        Aggregates samples across every evaluation row for this variant and
        returns a criterion → stdev mapping. Used by cross-generation
        observability to flag rubrics where model disagreement is growing.
        """
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                "SELECT dimension_scores FROM evaluation_results WHERE variant_id = $1",
                variant_id,
            )
        per_criterion: dict[str, list[float]] = {}
        for row in rows:
            dims = row["dimension_scores"]
            if isinstance(dims, str):
                try:
                    dims = json.loads(dims)
                except Exception:
                    continue
            if not isinstance(dims, dict):
                continue
            for cid, entry in dims.items():
                if not isinstance(entry, dict):
                    continue
                samples = entry.get("samples") or []
                for sample in samples:
                    if not isinstance(sample, dict):
                        continue
                    if sample.get("error") is not None:
                        continue
                    score = sample.get("normalized_score")
                    if isinstance(score, (int, float)):
                        per_criterion.setdefault(cid, []).append(float(score))
        return {
            cid: round(statistics.stdev(vals), 3)
            for cid, vals in per_criterion.items()
            if len(vals) >= 2
        }

    async def save(self, record: EvaluationRecord) -> EvaluationRecord:
        """Persist evaluation record."""
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._INSERT,
                record.id,
                record.campaign_id,
                record.domain,
                record.variant_id,
                record.domain_score,
                record.grounding_score,
                record.structural_passed,
                record.length_factor,
                json.dumps(record.dimension_scores),
                record.rubric_version,
                record.content_hash,
                record.user_id,
            )
        return record

    @staticmethod
    def _row_to_record(row: asyncpg.Record) -> EvaluationRecord:
        """Convert database row to EvaluationRecord."""
        dimension_scores = row["dimension_scores"]
        if isinstance(dimension_scores, str):
            dimension_scores = json.loads(dimension_scores)

        return EvaluationRecord(
            id=row["id"],
            campaign_id=row["campaign_id"],
            domain=row["domain"],
            variant_id=row["variant_id"],
            domain_score=row["domain_score"],
            grounding_score=row["grounding_score"],
            structural_passed=row["structural_passed"],
            length_factor=row["length_factor"],
            dimension_scores=dimension_scores,
            rubric_version=row["rubric_version"],
            content_hash=row["content_hash"],
            user_id=row["user_id"],
            created_at=row["created_at"],
        )
