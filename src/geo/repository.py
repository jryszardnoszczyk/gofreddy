"""PostgreSQL GEO audit repository."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager, suppress
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError


class PostgresGeoRepository:
    """PostgreSQL implementation for GEO audit storage."""

    ACQUIRE_TIMEOUT = 5.0

    _INSERT = """
        INSERT INTO geo_audits (
            id, user_id, url, status, keywords
        ) VALUES ($1, $2, $3, 'pending', $4)
        RETURNING id
    """

    _GET_BY_ID = """
        SELECT id, user_id, url, status, overall_score, report_md,
               findings, citations, opportunities, optimized_content,
               keywords, error, cost_usd, created_at, updated_at
        FROM geo_audits
        WHERE id = $1
    """

    _GET_BY_ID_AND_USER = """
        SELECT id, user_id, url, status, overall_score, report_md,
               findings, citations, opportunities, optimized_content,
               keywords, error, cost_usd, created_at, updated_at
        FROM geo_audits
        WHERE id = $1 AND user_id = $2
    """

    _LIST_BY_USER = """
        SELECT id, url, status, overall_score, keywords, error,
               created_at, updated_at
        FROM geo_audits
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """

    _UPDATE_STATUS = """
        UPDATE geo_audits
        SET status = $1, error = $2, updated_at = NOW()
        WHERE id = $3
    """

    _UPDATE_COMPLETED = """
        UPDATE geo_audits
        SET status = 'complete',
            overall_score = $1,
            report_md = $2,
            findings = $3::jsonb,
            citations = $4::jsonb,
            opportunities = $5::jsonb,
            optimized_content = $6,
            cost_usd = $7,
            updated_at = NOW()
        WHERE id = $8
    """

    _UPDATE_LINK_GRAPH = """
        UPDATE geo_audits
        SET site_link_graph = $1::jsonb,
            updated_at = NOW()
        WHERE id = $2
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

    async def create(
        self,
        audit_id: UUID,
        user_id: UUID,
        url: str,
        keywords: list[str] | None = None,
    ) -> UUID:
        """Create a new pending audit record."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._INSERT,
                audit_id,
                user_id,
                url,
                keywords,
            )
            return row["id"]

    async def get_by_id(self, audit_id: UUID) -> dict[str, Any] | None:
        """Fetch audit by ID (no ownership check)."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, audit_id)
            if row is None:
                return None
            return self._row_to_dict(row)

    async def get_by_id_and_user(
        self, audit_id: UUID, user_id: UUID
    ) -> dict[str, Any] | None:
        """Fetch audit by ID with ownership check."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID_AND_USER, audit_id, user_id)
            if row is None:
                return None
            return self._row_to_dict(row)

    async def list_by_user(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List audits for a user, newest first."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_BY_USER, user_id, limit, offset)
            return [dict(r) for r in rows]

    async def update_status(
        self, audit_id: UUID, status: str, error: str | None = None
    ) -> None:
        """Update audit status."""
        async with self._acquire_connection() as conn:
            await conn.execute(self._UPDATE_STATUS, status, error, audit_id)

    async def update_completed(
        self,
        audit_id: UUID,
        overall_score: float,
        report_md: str,
        findings: dict | None = None,
        citations: dict | None = None,
        opportunities: dict | None = None,
        optimized_content: str | None = None,
        cost_usd: float | None = None,
    ) -> None:
        """Update audit with completed results."""
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._UPDATE_COMPLETED,
                overall_score,
                report_md,
                json.dumps(findings) if findings else None,
                json.dumps(citations) if citations else None,
                json.dumps(opportunities) if opportunities else None,
                optimized_content,
                cost_usd,
                audit_id,
            )

    async def update_link_graph(
        self, audit_id: UUID, link_graph_json: str,
    ) -> None:
        """Store site link graph JSON for an audit."""
        async with self._acquire_connection() as conn:
            await conn.execute(self._UPDATE_LINK_GRAPH, link_graph_json, audit_id)

    def _row_to_dict(self, row: asyncpg.Record) -> dict[str, Any]:
        """Convert database row to dict with JSONB parsing."""
        result = dict(row)

        # Parse JSONB fields
        for field in ("findings", "citations", "opportunities"):
            if result.get(field) and isinstance(result[field], str):
                result[field] = json.loads(result[field])

        return result
