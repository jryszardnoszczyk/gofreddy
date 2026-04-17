"""Client access resolution — the single chokepoint for portal authorization.

Every portal route calls `resolve_client_access(pool, user_id, slug)` before
rendering. Admin role on any membership grants access to every client.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import asyncpg


@dataclass(frozen=True)
class Membership:
    client_id: UUID
    slug: str
    role: str


async def resolve_client_access(
    pool: asyncpg.Pool, user_id: UUID, slug: str
) -> str | None:
    """Return the user's effective role for this client slug, or None if no access.

    Admin on any client == admin on every client.
    """
    async with pool.acquire() as conn:
        is_admin = await conn.fetchval(
            "SELECT TRUE FROM user_client_memberships WHERE user_id = $1 AND role = 'admin' LIMIT 1",
            user_id,
        )
        if is_admin:
            return "admin"

        return await conn.fetchval(
            """
            SELECT m.role
              FROM user_client_memberships m
              JOIN clients c ON c.id = m.client_id
             WHERE m.user_id = $1 AND c.slug = $2
            """,
            user_id,
            slug,
        )


async def list_client_memberships(
    pool: asyncpg.Pool, user_id: UUID
) -> list[Membership]:
    """List all (client, role) the user can access. Admin sees every client."""
    async with pool.acquire() as conn:
        is_admin = await conn.fetchval(
            "SELECT TRUE FROM user_client_memberships WHERE user_id = $1 AND role = 'admin' LIMIT 1",
            user_id,
        )
        if is_admin:
            rows = await conn.fetch(
                "SELECT id, slug FROM clients ORDER BY created_at ASC"
            )
            return [Membership(client_id=r["id"], slug=r["slug"], role="admin") for r in rows]

        rows = await conn.fetch(
            """
            SELECT c.id, c.slug, m.role
              FROM user_client_memberships m
              JOIN clients c ON c.id = m.client_id
             WHERE m.user_id = $1
             ORDER BY c.created_at ASC
            """,
            user_id,
        )
    return [Membership(client_id=r["id"], slug=r["slug"], role=r["role"]) for r in rows]
