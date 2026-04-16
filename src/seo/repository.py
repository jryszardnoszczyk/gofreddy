"""PostgreSQL SEO audit repository."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager, suppress
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ..common.exceptions import PoolExhaustedError


class PostgresSeoRepository:
    """PostgreSQL implementation for SEO audit storage."""

    ACQUIRE_TIMEOUT = 5.0

    _INSERT = """
        INSERT INTO seo_audits (
            id, user_id, url, status
        ) VALUES ($1, $2, $3, 'pending')
        RETURNING id
    """

    _UPDATE_STATUS = """
        UPDATE seo_audits
        SET status = $1, error = $2, updated_at = NOW()
        WHERE id = $3
    """

    _UPDATE_COMPLETED = """
        UPDATE seo_audits
        SET status = 'complete',
            overall_score = $1,
            technical_issues = $2::jsonb,
            keywords = $3::jsonb,
            performance = $4::jsonb,
            backlinks = $5::jsonb,
            content_analysis = $6::jsonb,
            cost_usd = $7,
            updated_at = NOW()
        WHERE id = $8
    """

    _INSERT_DOMAIN_RANK = """
        INSERT INTO domain_rank_snapshots (
            domain, rank, backlinks_total, referring_domains, org_id
        ) VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (domain, snapshot_date, org_id)
        DO UPDATE SET
            rank = EXCLUDED.rank,
            backlinks_total = EXCLUDED.backlinks_total,
            referring_domains = EXCLUDED.referring_domains,
            updated_at = NOW()
        RETURNING id
    """

    _INSERT_DOMAIN_RANK_NO_ORG = """
        INSERT INTO domain_rank_snapshots (
            domain, rank, backlinks_total, referring_domains
        ) VALUES ($1, $2, $3, $4)
        ON CONFLICT (domain, snapshot_date) WHERE org_id IS NULL
        DO UPDATE SET
            rank = EXCLUDED.rank,
            backlinks_total = EXCLUDED.backlinks_total,
            referring_domains = EXCLUDED.referring_domains,
            updated_at = NOW()
        RETURNING id
    """

    _GET_DOMAIN_RANK_HISTORY = """
        SELECT domain, rank, backlinks_total, referring_domains,
               snapshot_date, org_id, created_at
        FROM domain_rank_snapshots
        WHERE domain = $1
          AND ($2::uuid IS NULL OR org_id = $2)
          AND snapshot_date >= CURRENT_DATE - ($3 || ' days')::interval
        ORDER BY snapshot_date DESC
    """

    _GET_LATEST_DOMAIN_RANK = """
        SELECT domain, rank, backlinks_total, referring_domains,
               snapshot_date, org_id, created_at
        FROM domain_rank_snapshots
        WHERE domain = $1
          AND ($2::uuid IS NULL OR org_id = $2)
        ORDER BY snapshot_date DESC
        LIMIT 1
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
    ) -> UUID:
        """Create a new pending audit record."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._INSERT,
                audit_id,
                user_id,
                url,
            )
            return row["id"]

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
        technical_issues: dict | None = None,
        keywords: dict | None = None,
        performance: dict | None = None,
        backlinks: dict | None = None,
        content_analysis: dict | None = None,
        cost_usd: float | None = None,
    ) -> None:
        """Update audit with completed results."""
        async with self._acquire_connection() as conn:
            await conn.execute(
                self._UPDATE_COMPLETED,
                overall_score,
                json.dumps(technical_issues) if technical_issues else None,
                json.dumps(keywords) if keywords else None,
                json.dumps(performance) if performance else None,
                json.dumps(backlinks) if backlinks else None,
                json.dumps(content_analysis) if content_analysis else None,
                cost_usd,
                audit_id,
            )

    async def insert_domain_rank_snapshot(
        self,
        domain: str,
        rank: int | None = None,
        backlinks_total: int = 0,
        referring_domains: int = 0,
        org_id: UUID | None = None,
    ) -> UUID:
        """Insert or update a domain rank snapshot for today.

        Uses a separate query for NULL org_id because PostgreSQL treats
        NULLs as distinct in UNIQUE constraints, so ``ON CONFLICT``
        against the composite ``(domain, snapshot_date, org_id)`` never
        matches when org_id is NULL.  A partial unique index
        ``uq_domain_rank_no_org`` covers that case.
        """
        async with self._acquire_connection() as conn:
            if org_id is None:
                row = await conn.fetchrow(
                    self._INSERT_DOMAIN_RANK_NO_ORG,
                    domain, rank, backlinks_total, referring_domains,
                )
            else:
                row = await conn.fetchrow(
                    self._INSERT_DOMAIN_RANK,
                    domain, rank, backlinks_total, referring_domains, org_id,
                )
            return row["id"]

    async def get_domain_rank_history(
        self, domain: str, org_id: UUID | None = None, days: int = 90,
    ) -> list[dict]:
        """Get domain rank history for the last N days."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._GET_DOMAIN_RANK_HISTORY, domain, org_id, str(days),
            )
            return [dict(r) for r in rows]

    async def get_latest_domain_rank(
        self, domain: str, org_id: UUID | None = None,
    ) -> dict | None:
        """Get the most recent domain rank snapshot."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_LATEST_DOMAIN_RANK, domain, org_id,
            )
            return dict(row) if row else None
