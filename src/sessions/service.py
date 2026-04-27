"""Session service with ownership enforcement and business rules."""

import logging
from typing import Any
from uuid import UUID

from .exceptions import SessionAlreadyCompleted, SessionNotFound
from .models import ActionRecord, IterationRecord, Session
from .repository import PostgresSessionRepository

logger = logging.getLogger(__name__)


class SessionService:
    """Orchestrates session operations with ownership enforcement."""

    def __init__(self, repository: PostgresSessionRepository) -> None:
        self._repository = repository

    async def create_or_return_existing(
        self,
        org_id: UUID,
        client_name: str = "default",
        source: str = "cli",
        session_type: str = "ad_hoc",
        purpose: str | None = None,
        client_id: UUID | None = None,
    ) -> Session:
        """Create a session or return existing running session for org+client.

        Dedup: if org already has a running session for same client_name, return it.
        """
        existing = await self._repository.get_running_for_org(
            org_id, client_name
        )
        if existing:
            return existing
        return await self._repository.create(
            org_id, client_name, source, session_type, purpose, client_id=client_id
        )

    async def get_by_id(self, session_id: UUID) -> Session | None:
        """Unscoped fetch — callers are responsible for authorization."""
        return await self._repository.get_by_id(session_id)

    async def get_session(
        self, session_id: UUID, org_id: UUID
    ) -> Session:
        """Get session, enforcing ownership. Raises SessionNotFound."""
        session = await self._repository.get_by_id(session_id)
        if session is None or session.org_id != org_id:
            raise SessionNotFound(session_id)
        return session

    async def list_sessions(
        self,
        org_id: UUID | None = None,
        client_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List sessions with optional filters. org_id=None lists all (admin)."""
        return await self._repository.list_sessions(
            org_id, client_name, status, limit, offset
        )

    async def list_sessions_for_client_ids(
        self,
        client_ids: list[UUID],
        client_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List sessions scoped to a tenant's accessible client_ids."""
        return await self._repository.list_sessions_for_client_ids(
            client_ids, client_name, status, limit, offset
        )

    async def complete_session(
        self,
        session_id: UUID,
        org_id: UUID,
        status: str = "completed",
        summary: str | None = None,
    ) -> Session:
        """Complete a running session. Enforces ownership."""
        session = await self.get_session(session_id, org_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        result = await self._repository.complete(session_id, status, summary)
        if result is None:
            raise SessionAlreadyCompleted(session_id)
        return result

    async def log_action(
        self,
        session_id: UUID,
        org_id: UUID,
        tool_name: str,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        cost_credits: int = 0,
        status: str = "success",
        error_code: str | None = None,
    ) -> ActionRecord:
        """Log an action to a session. Enforces ownership and running status."""
        session = await self.get_session(session_id, org_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        return await self._repository.log_action(
            session_id=session_id,
            tool_name=tool_name,
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=duration_ms,
            cost_credits=cost_credits,
            status=status,
            error_code=error_code,
        )

    async def get_actions(
        self,
        session_id: UUID,
        org_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionRecord]:
        """Get actions for a session. Enforces ownership."""
        await self.get_session(session_id, org_id)
        return await self._repository.get_actions(session_id, limit, offset)

    async def log_iteration(
        self,
        session_id: UUID,
        org_id: UUID,
        iteration_number: int,
        iteration_type: str | None = None,
        status: str = "success",
        exit_code: int | None = None,
        duration_ms: int | None = None,
        state_snapshot: str | None = None,
        result_entry: dict[str, Any] | None = None,
        log_output: str | None = None,
    ) -> IterationRecord:
        """Log an iteration to a session. Enforces ownership and running status."""
        session = await self.get_session(session_id, org_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        return await self._repository.log_iteration(
            session_id=session_id,
            iteration_number=iteration_number,
            iteration_type=iteration_type,
            status=status,
            exit_code=exit_code,
            duration_ms=duration_ms,
            state_snapshot=state_snapshot,
            result_entry=result_entry,
            log_output=log_output,
        )

    async def get_iterations(
        self,
        session_id: UUID,
        org_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IterationRecord]:
        """Get iterations for a session. Enforces ownership."""
        await self.get_session(session_id, org_id)
        return await self._repository.get_iterations(session_id, limit, offset)

    async def set_transcript(
        self, session_id: UUID, org_id: UUID, transcript: str
    ) -> bool:
        """Set transcript on a session. Enforces ownership and running status."""
        session = await self.get_session(session_id, org_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        return await self._repository.set_transcript(
            session_id, org_id, transcript
        )
