"""SingleConnectionPool adapter for test isolation.

Wraps a single asyncpg.Connection (inside a transaction) so repositories
can use their normal pool.acquire() pattern while all writes are rolled
back at the end of each test.

Handles both usage patterns found in the codebase:
  - async with pool.acquire() as conn:   (billing, stories repos)
  - conn = await pool.acquire()           (analysis repo via _acquire_connection)
"""

from __future__ import annotations

from typing import Any

import asyncpg


class _AcquireContext:
    """Dual-purpose object: works as both awaitable and async context manager.

    Mirrors asyncpg.pool.PoolAcquireContext behavior.
    """

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    def __await__(self):
        async def _return_conn():
            return self._conn
        return _return_conn().__await__()

    async def __aenter__(self) -> asyncpg.Connection:
        return self._conn

    async def __aexit__(self, *args: Any) -> None:
        pass  # no-op: connection stays alive for the transaction


class SingleConnectionPool:
    """Minimal pool adapter that always returns the same transactional connection.

    Repositories call pool.acquire() in various ways — this adapter ensures
    they all get the shared connection that's inside a test transaction.
    """

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    def acquire(self, *, timeout: float | None = None) -> _AcquireContext:
        """Return a dual-purpose acquire context (async CM + awaitable)."""
        return _AcquireContext(self._conn)

    async def release(self, conn: asyncpg.Connection, *, timeout: float | None = None) -> None:
        """No-op release — connection stays alive for the transaction."""

    def get_size(self) -> int:
        return 1

    def get_idle_size(self) -> int:
        return 1

    def get_min_size(self) -> int:
        return 1

    def get_max_size(self) -> int:
        return 1
