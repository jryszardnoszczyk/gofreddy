"""PostgreSQL competitive intelligence repository."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from .exceptions import BriefNotFoundError
from .models import BrandCreatorRelationship, CompetitiveBrief

logger = logging.getLogger(__name__)


class PostgresCompetitiveRepository:
    """Repository for competitive briefs and brand-creator relationships."""

    ACQUIRE_TIMEOUT = 5.0

    _STORE_BRIEF = """
        INSERT INTO competitive_briefs
            (client_id, org_id, date_range, brief_data, idempotency_key, schema_version)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL DO NOTHING
        RETURNING *
    """

    _GET_BRIEF_WITH_OWNERSHIP = """
        SELECT b.* FROM competitive_briefs b
        JOIN clients c ON b.client_id = c.id
        WHERE b.id = $1 AND c.org_id = $2
    """

    _GET_LATEST_BRIEF = """
        SELECT * FROM competitive_briefs
        WHERE client_id = $1
        ORDER BY created_at DESC
        LIMIT 1
    """

    _LIST_BRIEFS = """
        SELECT * FROM competitive_briefs
        WHERE client_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """

    _UPSERT_RELATIONSHIP = """
        INSERT INTO brand_creator_relationships
            (client_id, brand_name, creator_username, platform, mention_count)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (client_id, brand_name, creator_username, platform)
        DO UPDATE SET
            mention_count = brand_creator_relationships.mention_count + EXCLUDED.mention_count,
            last_seen_at = now()
        RETURNING *
    """

    _GET_RELATIONSHIP_HISTORY = """
        SELECT * FROM brand_creator_relationships
        WHERE client_id = $1
          AND brand_name = $2
          AND creator_username = $3
        LIMIT 1
    """

    _RESOLVE_MONITOR = """
        SELECT id FROM monitors
        WHERE client_id = $1 AND is_active = true
        LIMIT 1
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        """Acquire connection with timeout."""
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError:
            raise asyncpg.InterfaceError("Connection pool exhausted")
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def store_brief(
        self,
        client_id: UUID,
        org_id: UUID,
        date_range: str,
        brief_data: dict[str, Any],
        idempotency_key: str | None = None,
        schema_version: int = 1,
    ) -> CompetitiveBrief:
        """Store a competitive brief. Idempotent on idempotency_key."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._STORE_BRIEF,
                client_id,
                org_id,
                date_range,
                json.dumps(brief_data),
                idempotency_key,
                schema_version,
            )
            if row is None:
                # Idempotent hit — return existing brief
                existing = await conn.fetchrow(
                    "SELECT * FROM competitive_briefs WHERE idempotency_key = $1",
                    idempotency_key,
                )
                if existing is None:
                    raise BriefNotFoundError("Failed to store or retrieve brief")
                return CompetitiveBrief.from_row(existing)
            return CompetitiveBrief.from_row(row)

    async def get_brief_with_ownership(
        self, brief_id: UUID, org_id: UUID
    ) -> CompetitiveBrief:
        """Fetch brief with ownership verification via client FK."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_BRIEF_WITH_OWNERSHIP, brief_id, org_id
            )
            if row is None:
                raise BriefNotFoundError("Brief not found")
            return CompetitiveBrief.from_row(row)

    async def get_latest_brief(self, client_id: UUID) -> CompetitiveBrief | None:
        """Get most recent brief for delta comparison."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_LATEST_BRIEF, client_id)
            return CompetitiveBrief.from_row(row) if row else None

    async def list_briefs(
        self, client_id: UUID, limit: int = 10
    ) -> list[CompetitiveBrief]:
        """List briefs for a client, newest first."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._LIST_BRIEFS, client_id, limit)
            return [CompetitiveBrief.from_row(r) for r in rows]

    async def upsert_relationship(
        self,
        client_id: UUID,
        brand_name: str,
        creator_username: str,
        platform: str,
        mention_count: int = 1,
    ) -> BrandCreatorRelationship:
        """Upsert a brand-creator relationship. Normalizes to lowercase."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._UPSERT_RELATIONSHIP,
                client_id,
                brand_name.casefold(),
                creator_username.casefold(),
                platform,
                mention_count,
            )
            return BrandCreatorRelationship.from_row(row)

    async def get_relationship_history(
        self, client_id: UUID, brand_name: str, creator_username: str
    ) -> BrandCreatorRelationship | None:
        """Lookup existing relationship for escalation detection."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_RELATIONSHIP_HISTORY,
                client_id,
                brand_name.casefold(),
                creator_username.casefold(),
            )
            return BrandCreatorRelationship.from_row(row) if row else None

    async def resolve_monitor_for_client(self, client_id: UUID) -> UUID | None:
        """Find active monitor linked to this client."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._RESOLVE_MONITOR, client_id)
            return row["id"] if row else None
