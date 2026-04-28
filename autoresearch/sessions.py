"""Per-variant session-id tracking for claude/codex --resume across evolution invocations.

Mirrors ``harness/sessions.py``. The orchestrator writes a session_id BEFORE
spawning each agent subprocess and updates its status WHEN the subprocess
completes (or is interrupted). On ``--resume-variant``, ``--resume-fixture``,
or ``--fixtures-only``, the orchestrator reads ``.session_ids.json`` and
re-invokes incomplete agents with ``claude --resume <sid>`` (or
``codex exec resume <sid>``) instead of a fresh prompt — preserving the
agent's conversation thread.

Concurrency: writes come from the orchestrator process and ThreadPoolExecutor
workers (holdout fan-out). A threading.Lock + atomic rename (tmp + os.replace)
is sufficient.

Schema (JSON object, agent_key → record)::

    {
      "meta-v013": {"session_id": "...", "status": "running",
                     "engine": "claude", "started_at": 1776866123.5},
      "fixture-geo-semrush-pricing": {"session_id": "...", "status": "complete",
                     "engine": "claude", "started_at": 1776866200.0,
                     "finished_at": 1776866500.1},
    }

Status values:
- pending:   record created, subprocess not yet spawned (reserved).
- running:   subprocess spawned; no clean completion observed. Resume uses this.
- complete:  subprocess exited cleanly. Skip on resume.
- failed:    non-transient RuntimeError; fresh retry on resume (not --resume).

Sessions file location: per-variant at ``archive/<variant_id>/.session_ids.json``.
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

log = logging.getLogger("autoresearch.sessions")

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
    """Thread-safe reader/writer for per-variant ``.session_ids.json``.

    Load on init (empty dict if file missing). Mutate via begin()/finish().
    Every update atomically rewrites the whole file — fine given the small
    record count (~30 per variant: 1 meta-agent + ~24 fixture sessions +
    a few critic spawns) and infrequent writes (once at start + once at end
    per agent).
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

    def running(self) -> dict[str, SessionRecord]:
        """All records currently marked ``running`` — used by graceful-stop hint."""
        with self._lock:
            return {k: r for k, r in self._records.items() if r.status == "running"}

    def begin(self, agent_key: str, session_id: str, engine: str = "claude") -> SessionRecord:
        """Mark an agent as running. Called before spawning the subprocess."""
        record = SessionRecord(
            agent_key=agent_key,
            session_id=session_id,
            engine=engine,
            status="running",
            started_at=time.time(),
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
        log.warning("%s corrupted (%s) — starting with empty state", path.name, exc)
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
            log.warning("%s entry %r malformed (%s) — skipping", path.name, key, exc)
    return records


def claude_session_jsonl(wt_path: Path, session_id: str) -> Path:
    """Path where claude-CLI stores this session's local JSONL.

    Claude maps cwd to a projects/ subdir by replacing ``/`` with ``-``. If the
    file doesn't exist, the session was never successfully created (e.g.
    subprocess hung before its first token, or claude rate-limited before
    creating its JSONL). ``claude --resume <id>`` on a missing JSONL errors
    out, so resume code should fall back to a fresh session instead.
    """
    encoded = str(wt_path).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded / f"{session_id}.jsonl"


def codex_session_jsonl(session_id: str) -> Path | None:
    """Path where codex-CLI stores this session's rollout JSONL, or None if not found.

    Codex stores sessions at ``~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl``.
    The session_id is appended to the filename. Returns the first matching path,
    or None if no file exists for this session_id (codex never created the
    rollout — typical for rate-limited or auth-failed spawns).
    """
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.is_dir():
        return None
    matches = list(sessions_root.rglob(f"rollout-*-{session_id}.jsonl"))
    return matches[0] if matches else None


def viable_resume_id(record: SessionRecord, wt_path: Path | None = None) -> str | None:
    """Return record.session_id if the engine's local rollout/JSONL exists, else None.

    Resume only succeeds when the CLI actually created its persistence file.
    Returns None for unknown/unsupported engines (e.g. opencode lacks a stable
    resume mechanism) so the caller falls back to fresh.
    """
    if record.engine == "claude":
        if wt_path is None:
            return None
        return record.session_id if claude_session_jsonl(wt_path, record.session_id).is_file() else None
    if record.engine == "codex":
        return record.session_id if codex_session_jsonl(record.session_id) is not None else None
    return None


def _atomic_write(path: Path, records: dict[str, SessionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {key: asdict(record) for key, record in records.items()}
    fd, tmp_name = tempfile.mkstemp(prefix=".session_ids-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)
            fp.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
