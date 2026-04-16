"""PostgreSQL CRM contacts repository."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from ...common.exceptions import PoolExhaustedError
from .models import Contact

logger = logging.getLogger(__name__)


class PostgresContactRepository:
    """PostgreSQL repository for CRM contacts."""

    ACQUIRE_TIMEOUT = 5.0

    # ── Queries ──

    _UPSERT_CONTACT = """
        INSERT INTO contacts (org_id, primary_handle, primary_platform, display_name, avatar_url, handles)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (org_id, primary_platform, primary_handle) DO UPDATE
        SET interaction_count = contacts.interaction_count + 1,
            last_seen_at     = NOW(),
            display_name     = COALESCE(EXCLUDED.display_name, contacts.display_name),
            avatar_url       = COALESCE(EXCLUDED.avatar_url, contacts.avatar_url),
            updated_at       = NOW()
        RETURNING *
    """

    _GET_CONTACTS = """
        SELECT * FROM contacts
        WHERE org_id = $1
        ORDER BY last_seen_at DESC
        LIMIT $2 OFFSET $3
    """

    _GET_CONTACTS_SEARCH = """
        SELECT * FROM contacts
        WHERE org_id = $1
          AND (primary_handle ILIKE $4 OR display_name ILIKE $4)
        ORDER BY last_seen_at DESC
        LIMIT $2 OFFSET $3
    """

    _GET_CONTACT = """
        SELECT * FROM contacts WHERE org_id = $1 AND id = $2
    """

    _UPDATE_CONTACT_NOTES = """
        UPDATE contacts SET notes = $3, updated_at = NOW()
        WHERE org_id = $1 AND id = $2
        RETURNING *
    """

    _UPDATE_CONTACT_TAGS = """
        UPDATE contacts SET tags = $3::jsonb, updated_at = NOW()
        WHERE org_id = $1 AND id = $2
        RETURNING *
    """

    _UPDATE_CONTACT_BOTH = """
        UPDATE contacts SET notes = $3, tags = $4::jsonb, updated_at = NOW()
        WHERE org_id = $1 AND id = $2
        RETURNING *
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
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

    # ── Methods ──

    async def upsert_contact(
        self,
        org_id: UUID,
        platform: str,
        handle: str,
        *,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> Contact:
        handles_json = json.dumps([{"platform": platform, "handle": handle}])
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._UPSERT_CONTACT,
                org_id, handle, platform, display_name, avatar_url, handles_json,
            )
        return Contact.from_row(row)

    async def get_contacts(
        self,
        org_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Contact]:
        async with self._acquire_connection() as conn:
            if search:
                pattern = f"%{search}%"
                rows = await conn.fetch(
                    self._GET_CONTACTS_SEARCH, org_id, limit, offset, pattern,
                )
            else:
                rows = await conn.fetch(self._GET_CONTACTS, org_id, limit, offset)
        return [Contact.from_row(r) for r in rows]

    async def get_contact(self, org_id: UUID, contact_id: UUID) -> Contact | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_CONTACT, org_id, contact_id)
        return Contact.from_row(row) if row else None

    async def update_contact(
        self,
        org_id: UUID,
        contact_id: UUID,
        *,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> Contact | None:
        async with self._acquire_connection() as conn:
            if notes is not None and tags is not None:
                row = await conn.fetchrow(
                    self._UPDATE_CONTACT_BOTH,
                    org_id, contact_id, notes, json.dumps(tags),
                )
            elif notes is not None:
                row = await conn.fetchrow(
                    self._UPDATE_CONTACT_NOTES, org_id, contact_id, notes,
                )
            elif tags is not None:
                row = await conn.fetchrow(
                    self._UPDATE_CONTACT_TAGS, org_id, contact_id, json.dumps(tags),
                )
            else:
                return await self.get_contact(org_id, contact_id)
        return Contact.from_row(row) if row else None
