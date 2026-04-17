"""User repository — thin asyncpg wrapper matching the method names used by
the auth resolvers extracted from freddy/src/api/dependencies.py.

Freddy's equivalent lives in src/billing/repository.py::BillingRepository.
We split users out so gofreddy doesn't need the billing layer.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True, slots=True)
class ApiKeyRecord:
    """API key row as returned by ApiKeyRepo. Mirrors freddy's APIKey."""

    id: UUID
    user_id: UUID
    key_prefix: str
    name: str | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool


class ApiKeyRepo:
    """Tenant-agnostic API key repo. Ported from freddy src/billing/repository.py L214-265."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_api_key_atomic(
        self, user_id: UUID, key: str, name: str | None = None, max_keys: int = 10
    ) -> ApiKeyRecord | None:
        """Create a new API key with atomic max-key enforcement.

        Returns None if the user already has max_keys active keys.
        CTE prevents TOCTOU races under concurrent creates.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12]
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                WITH active AS (
                    SELECT COUNT(*) AS cnt FROM api_keys
                    WHERE user_id = $1 AND revoked_at IS NULL
                )
                INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                SELECT $1, $2, $3, $4 FROM active WHERE cnt < $5
                RETURNING id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at
                """,
                user_id, key_hash, key_prefix, name, max_keys,
            )
        return _row_to_api_key(row) if row else None

    async def list_api_keys(self, user_id: UUID) -> list[ApiKeyRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, key_prefix, name, created_at, last_used_at, expires_at, revoked_at
                FROM api_keys
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )
        return [_row_to_api_key(r) for r in rows]

    async def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """Revoke an API key. Returns True if the row was updated (idempotent path handled by caller)."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE api_keys SET revoked_at = NOW() WHERE id = $1 AND user_id = $2",
                key_id, user_id,
            )
        return result == "UPDATE 1"


def _row_to_api_key(row: asyncpg.Record) -> ApiKeyRecord:
    return ApiKeyRecord(
        id=row["id"],
        user_id=row["user_id"],
        key_prefix=row["key_prefix"],
        name=row["name"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
        is_active=row["revoked_at"] is None,
    )
