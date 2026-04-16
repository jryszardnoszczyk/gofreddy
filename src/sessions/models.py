"""Session domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Session:
    """Agent session record."""

    id: UUID
    client_name: str
    source: str
    session_type: str
    purpose: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    updated_at: datetime
    summary: str | None
    action_count: int
    total_credits: int
    transcript: str | None
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "client_name": self.client_name,
            "source": self.source,
            "session_type": self.session_type,
            "purpose": self.purpose,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "summary": self.summary,
            "action_count": self.action_count,
            "total_credits": self.total_credits,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class ActionRecord:
    """Action log entry."""

    id: UUID
    session_id: UUID
    tool_name: str
    input_summary: dict[str, Any] | None
    output_summary: dict[str, Any] | None
    duration_ms: int | None
    cost_credits: int
    status: str
    error_code: str | None
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "tool_name": self.tool_name,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
            "cost_credits": self.cost_credits,
            "status": self.status,
            "error_code": self.error_code,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class IterationRecord:
    """Iteration log entry for autoresearch sessions."""

    id: UUID
    session_id: UUID
    iteration_number: int
    iteration_type: str | None
    status: str
    exit_code: int | None
    duration_ms: int | None
    state_snapshot: str | None
    result_entry: dict[str, Any] | None
    log_output: str | None
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "iteration_number": self.iteration_number,
            "iteration_type": self.iteration_type,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "state_snapshot": self.state_snapshot,
            "result_entry": self.result_entry,
            "log_output": self.log_output,
            "created_at": self.created_at.isoformat(),
        }
