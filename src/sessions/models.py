"""Session domain models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Session:
    """Agent session record."""

    id: UUID
    org_id: UUID | None
    client_id: UUID | None
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

    @classmethod
    def from_row(cls, row: Any) -> Session:
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            client_id=row["client_id"],
            client_name=row["client_name"],
            source=row["source"],
            session_type=row["session_type"],
            purpose=row["purpose"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            updated_at=row["updated_at"],
            summary=row["summary"],
            action_count=row["action_count"],
            total_credits=row["total_credits"],
            transcript=row["transcript"],
            metadata=metadata if metadata else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "org_id": str(self.org_id) if self.org_id else None,
            "client_id": str(self.client_id) if self.client_id else None,
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

    @classmethod
    def from_row(cls, row: Any) -> ActionRecord:
        input_summary = row["input_summary"]
        if isinstance(input_summary, str):
            input_summary = json.loads(input_summary)
        output_summary = row["output_summary"]
        if isinstance(output_summary, str):
            output_summary = json.loads(output_summary)
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            tool_name=row["tool_name"],
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=row["duration_ms"],
            cost_credits=row["cost_credits"],
            status=row["status"],
            error_code=row["error_code"],
            created_at=row["created_at"],
        )

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

    @classmethod
    def from_row(cls, row: Any) -> IterationRecord:
        result_entry = row["result_entry"]
        if isinstance(result_entry, str):
            result_entry = json.loads(result_entry)
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            iteration_number=row["iteration_number"],
            iteration_type=row["iteration_type"],
            status=row["status"],
            exit_code=row["exit_code"],
            duration_ms=row["duration_ms"],
            state_snapshot=row["state_snapshot"],
            result_entry=result_entry,
            log_output=row["log_output"],
            created_at=row["created_at"],
        )

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
