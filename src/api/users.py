"""User repository — thin asyncpg wrapper matching the method names used by
the auth resolvers extracted from freddy/src/api/dependencies.py.

Freddy's equivalent lives in src/billing/repository.py::BillingRepository.
We split users out so gofreddy doesn't need the billing layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import asyncpg


@dataclass(frozen=True)
class UserRecord:
    id: UUID
    email: str
    supabase_user_id: str | None


class UserRepo:
    """Thin repository for users + api_keys tables."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_user_by_supabase_id(self, supabase_user_id: str) -> UserRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, supabase_user_id FROM users WHERE supabase_user_id = $1",
                supabase_user_id,
            )
        return _row_to_user(row)

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, supabase_user_id FROM users WHERE email = $1",
                email,
            )
        return _row_to_user(row)

    async def link_supabase_user(self, user_id: UUID, supabase_user_id: str) -> bool:
        """Link a supabase identity to an existing user. Returns False on conflict."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                   SET supabase_user_id = $2, updated_at = NOW()
                 WHERE id = $1
                   AND (supabase_user_id IS NULL OR supabase_user_id = $2)
                """,
                user_id,
                supabase_user_id,
            )
        return result == "UPDATE 1"

    async def create_user(self, email: str, supabase_user_id: str) -> UserRecord:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, supabase_user_id)
                VALUES ($1, $2)
                RETURNING id, email, supabase_user_id
                """,
                email,
                supabase_user_id,
            )
        assert row is not None
        return _row_to_user(row)  # type: ignore[return-value]

    async def get_user_by_api_key(self, api_key: str) -> UserRecord | None:
        """Look up user by raw API key — we store a SHA-256 hash."""
        import hashlib

        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT u.id, u.email, u.supabase_user_id
                  FROM users u
                  JOIN api_keys k ON k.user_id = u.id
                 WHERE k.key_hash = $1
                   AND k.revoked_at IS NULL
                   AND (k.expires_at IS NULL OR k.expires_at > NOW())
                """,
                key_hash,
            )
        return _row_to_user(row)


def _row_to_user(row: asyncpg.Record | None) -> UserRecord | None:
    if row is None:
        return None
    return UserRecord(
        id=row["id"],
        email=row["email"],
        supabase_user_id=row["supabase_user_id"],
    )
