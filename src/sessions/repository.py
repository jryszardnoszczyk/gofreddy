"""File-based session repository.

Stores per-client sessions as JSON files under:

    <clients_dir>/<client_name>/sessions/<session_id>/meta.json
    <clients_dir>/<client_name>/sessions/<session_id>/actions.jsonl
    <clients_dir>/<client_name>/sessions/<session_id>/iterations.jsonl
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import aiofiles

from .models import ActionRecord, IterationRecord, Session

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _session_from_meta(data: dict[str, Any]) -> Session:
    return Session(
        id=UUID(data["id"]),
        client_name=data["client_name"],
        source=data.get("source", "cli"),
        session_type=data.get("session_type", "ad_hoc"),
        purpose=data.get("purpose"),
        status=data.get("status", "running"),
        started_at=_parse_datetime(data["started_at"]),
        completed_at=_parse_datetime(data["completed_at"]) if data.get("completed_at") else None,
        updated_at=_parse_datetime(data.get("updated_at", data["started_at"])),
        summary=data.get("summary"),
        action_count=int(data.get("action_count", 0)),
        total_credits=int(data.get("total_credits", 0)),
        transcript=data.get("transcript"),
        metadata=data.get("metadata") or {},
    )


def _action_from_row(session_id: UUID, row: dict[str, Any]) -> ActionRecord:
    return ActionRecord(
        id=UUID(row["id"]),
        session_id=session_id,
        tool_name=row["tool_name"],
        input_summary=row.get("input_summary"),
        output_summary=row.get("output_summary"),
        duration_ms=row.get("duration_ms"),
        cost_credits=int(row.get("cost_credits", 0)),
        status=row.get("status", "success"),
        error_code=row.get("error_code"),
        created_at=_parse_datetime(row["created_at"]),
    )


def _iteration_from_row(session_id: UUID, row: dict[str, Any]) -> IterationRecord:
    return IterationRecord(
        id=UUID(row["id"]),
        session_id=session_id,
        iteration_number=int(row["iteration_number"]),
        iteration_type=row.get("iteration_type"),
        status=row.get("status", "success"),
        exit_code=row.get("exit_code"),
        duration_ms=row.get("duration_ms"),
        state_snapshot=row.get("state_snapshot"),
        result_entry=row.get("result_entry"),
        log_output=row.get("log_output"),
        created_at=_parse_datetime(row["created_at"]),
    )


class FileSessionRepository:
    """File-based session repository, one directory per session."""

    def __init__(self, clients_dir: Path) -> None:
        self._clients_dir = Path(clients_dir)

    def _session_dir(self, client_name: str, session_id: UUID) -> Path:
        return self._clients_dir / client_name / "sessions" / str(session_id)

    def _sessions_root(self, client_name: str) -> Path:
        return self._clients_dir / client_name / "sessions"

    async def _read_meta(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        async with aiofiles.open(path, "r") as f:
            raw = await f.read()
        if not raw.strip():
            return None
        return json.loads(raw)

    async def _write_meta(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def create(
        self,
        client_name: str,
        source: str = "cli",
        session_type: str = "ad_hoc",
        purpose: str | None = None,
    ) -> Session:
        session_id = uuid4()
        now = _utcnow()
        session_dir = self._session_dir(client_name, session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "id": str(session_id),
            "client_name": client_name,
            "source": source,
            "session_type": session_type,
            "purpose": purpose,
            "status": "running",
            "started_at": now.isoformat(),
            "completed_at": None,
            "updated_at": now.isoformat(),
            "summary": None,
            "action_count": 0,
            "total_credits": 0,
            "transcript": None,
            "metadata": {},
        }
        await self._write_meta(session_dir / "meta.json", meta)
        return _session_from_meta(meta)

    async def get_by_id(self, client_name: str, session_id: UUID) -> Session | None:
        meta = await self._read_meta(self._session_dir(client_name, session_id) / "meta.json")
        return _session_from_meta(meta) if meta else None

    async def list_sessions(
        self,
        client_name: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        root = self._sessions_root(client_name)
        if not root.exists():
            return []
        sessions: list[Session] = []
        entries = sorted(
            (p for p in root.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for entry in entries:
            meta = await self._read_meta(entry / "meta.json")
            if meta is None:
                continue
            if status and meta.get("status") != status:
                continue
            sessions.append(_session_from_meta(meta))
        return sessions[offset : offset + limit]

    async def complete(
        self,
        client_name: str,
        session_id: UUID,
        status: str = "completed",
        summary: str | None = None,
    ) -> Session | None:
        meta_path = self._session_dir(client_name, session_id) / "meta.json"
        meta = await self._read_meta(meta_path)
        if meta is None or meta.get("status") != "running":
            return None
        now = _utcnow()
        meta["status"] = status
        meta["summary"] = summary
        meta["completed_at"] = now.isoformat()
        meta["updated_at"] = now.isoformat()
        await self._write_meta(meta_path, meta)
        return _session_from_meta(meta)

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
        session_dir = self._session_dir(client_name, session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        action = {
            "id": str(uuid4()),
            "session_id": str(session_id),
            "tool_name": tool_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "duration_ms": duration_ms,
            "cost_credits": cost_credits,
            "status": status,
            "error_code": error_code,
            "created_at": _utcnow().isoformat(),
        }
        async with aiofiles.open(session_dir / "actions.jsonl", "a") as f:
            await f.write(json.dumps(action) + "\n")
        meta_path = session_dir / "meta.json"
        meta = await self._read_meta(meta_path)
        if meta is not None:
            meta["action_count"] = int(meta.get("action_count", 0)) + 1
            meta["total_credits"] = int(meta.get("total_credits", 0)) + max(0, cost_credits)
            meta["updated_at"] = _utcnow().isoformat()
            await self._write_meta(meta_path, meta)
        return _action_from_row(session_id, action)

    async def get_actions(
        self,
        client_name: str,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionRecord]:
        path = self._session_dir(client_name, session_id) / "actions.jsonl"
        if not path.exists():
            return []
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        rows: list[ActionRecord] = []
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                rows.append(_action_from_row(session_id, json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                continue
        return rows[offset : offset + limit]

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
        session_dir = self._session_dir(client_name, session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "id": str(uuid4()),
            "session_id": str(session_id),
            "iteration_number": iteration_number,
            "iteration_type": iteration_type,
            "status": status,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "state_snapshot": state_snapshot,
            "result_entry": result_entry,
            "log_output": log_output,
            "created_at": _utcnow().isoformat(),
        }
        async with aiofiles.open(session_dir / "iterations.jsonl", "a") as f:
            await f.write(json.dumps(row) + "\n")
        return _iteration_from_row(session_id, row)
