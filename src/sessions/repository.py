"""PostgreSQL session repository."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from .models import ActionRecord, IterationRecord, Session

logger = logging.getLogger(__name__)


class PostgresSessionRepository:
    """PostgreSQL repository for agent sessions and action logs."""

    ACQUIRE_TIMEOUT = 5.0

    _CREATE = """
        INSERT INTO agent_sessions (org_id, client_id, client_name, source, session_type, purpose)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    _GET_RUNNING_FOR_ORG = """
        SELECT * FROM agent_sessions
        WHERE org_id = $1 AND client_name = $2 AND status = 'running'
        ORDER BY started_at DESC
        LIMIT 1
    """

    _GET_BY_ID = """
        SELECT * FROM agent_sessions WHERE id = $1
    """

    _LIST = """
        SELECT * FROM agent_sessions
        WHERE ($1::uuid IS NULL OR org_id = $1)
          AND ($2::text IS NULL OR client_name = $2)
          AND ($3::text IS NULL OR status = $3)
        ORDER BY started_at DESC
        LIMIT $4 OFFSET $5
    """

    _LIST_FOR_CLIENT_IDS = """
        SELECT * FROM agent_sessions
        WHERE client_id = ANY($1::uuid[])
          AND ($2::text IS NULL OR client_name = $2)
          AND ($3::text IS NULL OR status = $3)
        ORDER BY started_at DESC
        LIMIT $4 OFFSET $5
    """

    _COMPLETE = """
        UPDATE agent_sessions
        SET status = $2, summary = $3, completed_at = now()
        WHERE id = $1 AND status = 'running'
        RETURNING *
    """

    _SET_TRANSCRIPT = """
        UPDATE agent_sessions SET transcript = $2
        WHERE id = $1 AND org_id = $3
        RETURNING id
    """

    _LOG_ACTION = """
        INSERT INTO action_log (session_id, tool_name, input_summary, output_summary,
                                duration_ms, cost_credits, status, error_code)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    _INCREMENT_COUNTERS = """
        UPDATE agent_sessions
        SET action_count = action_count + 1,
            total_credits = total_credits + GREATEST(0, $2)
        WHERE id = $1
    """

    _GET_ACTIONS = """
        SELECT * FROM action_log
        WHERE session_id = $1
        ORDER BY created_at ASC
        LIMIT $2 OFFSET $3
    """

    _LOG_ITERATION = """
        INSERT INTO iteration_log (session_id, iteration_number, iteration_type,
                                   status, exit_code, duration_ms, state_snapshot,
                                   result_entry, log_output)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """

    _GET_ITERATIONS = """
        SELECT * FROM iteration_log
        WHERE session_id = $1
        ORDER BY iteration_number ASC
        LIMIT $2 OFFSET $3
    """

    _GET_ITERATION = """
        SELECT * FROM iteration_log
        WHERE session_id = $1 AND iteration_number = $2
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
            raise asyncpg.InterfaceError("Connection pool exhausted")
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def create(
        self,
        org_id: UUID,
        client_name: str,
        source: str = "cli",
        session_type: str = "ad_hoc",
        purpose: str | None = None,
        client_id: UUID | None = None,
    ) -> Session:
        """Create a new session."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._CREATE, org_id, client_id, client_name, source, session_type, purpose
            )
            return Session.from_row(row)

    async def get_running_for_org(
        self, org_id: UUID, client_name: str
    ) -> Session | None:
        """Get the running session for an org+client combo."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_RUNNING_FOR_ORG, org_id, client_name
            )
            return Session.from_row(row) if row else None

    async def get_by_id(self, session_id: UUID) -> Session | None:
        """Fetch session by ID. Returns None if not found."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._GET_BY_ID, session_id)
            return Session.from_row(row) if row else None

    async def list_sessions(
        self,
        org_id: UUID | None = None,
        client_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List sessions, optionally filtered by org_id. Pass None for all."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._LIST, org_id, client_name, status, limit, offset
            )
            return [Session.from_row(r) for r in rows]

    async def list_sessions_for_client_ids(
        self,
        client_ids: list[UUID],
        client_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List sessions whose client_id is in the given set (tenant-scoped)."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                self._LIST_FOR_CLIENT_IDS,
                client_ids, client_name, status, limit, offset,
            )
            return [Session.from_row(r) for r in rows]

    async def complete(
        self,
        session_id: UUID,
        status: str = "completed",
        summary: str | None = None,
    ) -> Session | None:
        """Complete a running session. Returns None if not running."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(self._COMPLETE, session_id, status, summary)
            return Session.from_row(row) if row else None

    async def set_transcript(
        self, session_id: UUID, org_id: UUID, transcript: str
    ) -> bool:
        """Set transcript on a session. Returns True if updated."""
        async with self._acquire_connection() as conn:
            result = await conn.fetchval(
                self._SET_TRANSCRIPT, session_id, transcript, org_id
            )
            return result is not None

    async def log_action(
        self,
        session_id: UUID,
        tool_name: str,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        cost_credits: int = 0,
        status: str = "success",
        error_code: str | None = None,
    ) -> ActionRecord:
        """Log an action and atomically increment session counters."""
        async with self._acquire_connection() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    self._LOG_ACTION,
                    session_id,
                    tool_name,
                    json.dumps(input_summary) if input_summary else None,
                    json.dumps(output_summary) if output_summary else None,
                    duration_ms,
                    cost_credits,
                    status,
                    error_code,
                )
                await conn.execute(
                    self._INCREMENT_COUNTERS, session_id, cost_credits
                )
            return ActionRecord.from_row(row)

    async def get_actions(
        self, session_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[ActionRecord]:
        """Get actions for a session in chronological order."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_ACTIONS, session_id, limit, offset)
            return [ActionRecord.from_row(r) for r in rows]

    async def log_iteration(
        self,
        session_id: UUID,
        iteration_number: int,
        iteration_type: str | None = None,
        status: str = "success",
        exit_code: int | None = None,
        duration_ms: int | None = None,
        state_snapshot: str | None = None,
        result_entry: dict[str, Any] | None = None,
        log_output: str | None = None,
    ) -> IterationRecord:
        """Log an iteration for an autoresearch session."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._LOG_ITERATION,
                session_id,
                iteration_number,
                iteration_type,
                status,
                exit_code,
                duration_ms,
                state_snapshot,
                json.dumps(result_entry) if result_entry else None,
                log_output,
            )
            return IterationRecord.from_row(row)

    async def get_iterations(
        self, session_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[IterationRecord]:
        """Get iterations for a session in order."""
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(self._GET_ITERATIONS, session_id, limit, offset)
            return [IterationRecord.from_row(r) for r in rows]

    async def get_iteration(
        self, session_id: UUID, iteration_number: int
    ) -> IterationRecord | None:
        """Get a specific iteration by number. Returns None if not found."""
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                self._GET_ITERATION, session_id, iteration_number
            )
            return IterationRecord.from_row(row) if row else None
