"""Per-run session-id tracking for claude --resume across harness invocations.

The orchestrator writes a session_id to sessions.json BEFORE spawning each claude
subprocess and updates its status WHEN the subprocess completes (or is interrupted).
On `--resume-branch`, the orchestrator reads sessions.json, maps branch to run_dir,
and re-invokes incomplete agents with `claude --resume <session_id>` instead of a
fresh prompt — preserving the agent's conversation thread.

Concurrency: all writes come from the orchestrator Python process, not from claude
subprocesses. A threading.Lock + atomic rename (tmp + os.replace) is sufficient.

Schema (JSON object, agent_key → record):
    {
      "eval-a-c1":   {"session_id": "...", "status": "complete",
                      "engine": "claude", "started_at": 1776866123.5,
                      "finished_at": 1776866500.1},
      "fix-F-a-1-1": {"session_id": "...", "status": "running",
                      "engine": "claude", "started_at": 1776866502.0}
    }

Status values:
- pending:   record created, subprocess not yet spawned (reserved; current impl
             transitions directly pending → running on spawn)
- running:   subprocess spawned; no clean completion observed. Resume uses this.
- complete:  subprocess exited cleanly. Skip on resume.
- failed:    non-transient RuntimeError; fresh retry on resume (not --resume).
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Literal

log = logging.getLogger("harness.sessions")

Status = Literal["pending", "running", "complete", "failed"]


@dataclass(frozen=True)
class SessionRecord:
    agent_key: str
    session_id: str
    engine: str
    status: Status
    started_at: float
    finished_at: float | None = None


@dataclass
class SessionsFile:
    """Thread-safe reader/writer for sessions.json.

    Load on init (empty dict if file missing). Mutate via update(). Every update
    atomically rewrites the whole file — fine given the small record count (~60
    per run) and infrequent writes (once at start + once at end per agent).
    """
    path: Path
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _records: dict[str, SessionRecord] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._records = _load(self.path)

    def get(self, agent_key: str) -> SessionRecord | None:
        with self._lock:
            return self._records.get(agent_key)

    def all(self) -> dict[str, SessionRecord]:
        """Snapshot copy of all records (safe to iterate outside the lock)."""
        with self._lock:
            return dict(self._records)

    def begin(self, agent_key: str, session_id: str, engine: str) -> SessionRecord:
        """Mark an agent as running. Called before spawning the subprocess."""
        record = SessionRecord(
            agent_key=agent_key, session_id=session_id, engine=engine,
            status="running", started_at=time.time(),
        )
        self._write(record)
        return record

    def finish(self, agent_key: str, status: Status) -> None:
        """Update a running record to terminal status. No-op if record missing."""
        with self._lock:
            existing = self._records.get(agent_key)
            if existing is None:
                log.warning("finish called for unknown agent_key %s (no-op)", agent_key)
                return
            updated = replace(existing, status=status, finished_at=time.time())
            self._records[agent_key] = updated
            _atomic_write(self.path, self._records)

    def _write(self, record: SessionRecord) -> None:
        with self._lock:
            self._records[record.agent_key] = record
            _atomic_write(self.path, self._records)


def _load(path: Path) -> dict[str, SessionRecord]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning("sessions.json corrupted (%s) — starting with empty state", exc)
        return {}
    records: dict[str, SessionRecord] = {}
    for key, data in raw.items():
        try:
            records[key] = SessionRecord(
                agent_key=data["agent_key"],
                session_id=data["session_id"],
                engine=data["engine"],
                status=data["status"],
                started_at=float(data["started_at"]),
                finished_at=float(data["finished_at"]) if data.get("finished_at") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("sessions.json entry %r malformed (%s) — skipping", key, exc)
    return records


def claude_session_jsonl(wt_path: Path, session_id: str) -> Path:
    """Path where claude-CLI stores this session's local JSONL.

    Claude maps cwd to a projects/ subdir by replacing `/` with `-`. If the file
    doesn't exist, the session was never successfully created (e.g. subprocess
    hung before its first token, as happened overnight in smoke run
    20260422-224908 when all 3 fixers silent-hung on a subscription rate limit).
    `claude --resume <id>` on a missing JSONL errors out, so resume code should
    fall back to a fresh session instead.
    """
    encoded = str(wt_path).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded / f"{session_id}.jsonl"


def _atomic_write(path: Path, records: dict[str, SessionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {key: asdict(record) for key, record in records.items()}
    fd, tmp_name = tempfile.mkstemp(prefix=".sessions-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)
            fp.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        # If the write or rename fails, make sure the tmp file doesn't stick around.
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
