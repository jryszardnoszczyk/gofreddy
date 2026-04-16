"""Session service — thin wrapper over FileSessionRepository."""

import logging
from typing import Any
from uuid import UUID

from .exceptions import SessionAlreadyCompleted, SessionNotFound
from .models import ActionRecord, IterationRecord, Session
from .repository import FileSessionRepository

logger = logging.getLogger(__name__)


class SessionService:
    """Orchestrates session operations against the file-based repository."""

    def __init__(self, repository: FileSessionRepository) -> None:
        self._repository = repository

    async def create_session(
        self,
        client_name: str = "default",
        source: str = "cli",
        session_type: str = "ad_hoc",
        purpose: str | None = None,
    ) -> Session:
        return await self._repository.create(
            client_name=client_name,
            source=source,
            session_type=session_type,
            purpose=purpose,
        )

    async def get_session(self, client_name: str, session_id: UUID) -> Session:
        session = await self._repository.get_by_id(client_name, session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session

    async def list_sessions(
        self,
        client_name: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        return await self._repository.list_sessions(
            client_name=client_name,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def complete_session(
        self,
        client_name: str,
        session_id: UUID,
        status: str = "completed",
        summary: str | None = None,
    ) -> Session:
        session = await self.get_session(client_name, session_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        result = await self._repository.complete(client_name, session_id, status, summary)
        if result is None:
            raise SessionAlreadyCompleted(session_id)
        return result

    async def log_action(
        self,
        client_name: str,
        session_id: UUID,
        tool_name: str,
        input_summary: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        cost_credits: int = 0,
        status: str = "success",
        error_code: str | None = None,
    ) -> ActionRecord:
        session = await self.get_session(client_name, session_id)
        if session.status != "running":
            raise SessionAlreadyCompleted(session_id)
        return await self._repository.log_action(
            client_name=client_name,
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
        client_name: str,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionRecord]:
        await self.get_session(client_name, session_id)
        return await self._repository.get_actions(client_name, session_id, limit, offset)

    async def log_iteration(
        self,
        client_name: str,
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
        await self.get_session(client_name, session_id)
        return await self._repository.log_iteration(
            client_name=client_name,
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
