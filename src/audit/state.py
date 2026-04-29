"""Persistent audit state.

``AuditState`` is a frozen dataclass — a snapshot of the audit's status,
cost, completed-lenses, sessions, and graceful-stop flags. Mutate via
``AuditStateFile.mutate(fn)`` which serializes read-modify-write under a
threading.Lock and commits with ``checkpointing.atomic_update`` semantics
(temp + os.replace).

v1 single-process per LHR D3 — file-level cross-process locking is NOT
provided here. If v2 ever runs parallel audits per prospect, layer
``portalocker`` into ``checkpointing`` (see comment there) and audit's
mutate path picks up the new behavior automatically.

The frozen-dataclass + ``replace()`` convention mirrors
``harness.sessions.SessionRecord`` and ``src/audit/agent_models.py``.
"""
from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.audit import checkpointing


@dataclass(frozen=True)
class AuditState:
    """Frozen snapshot of audit state.

    Required fields (set at audit-start): ``audit_id``, ``client_slug``,
    ``prospect_domain``. Everything else has a default suitable for the
    initial state.

    Tuple-typed fields (``completed_lenses``, ``failed_lenses``,
    ``bundles_activated``, ``stage2_pids``) are immutable so accidental
    in-place mutation in stage runners doesn't silently corrupt the
    snapshot. Callers add via ``replace(s, completed_lenses=s.completed_lenses + (new_id,))``.
    """

    audit_id: str
    client_slug: str
    prospect_domain: str
    status: str = "pending"
    total_cost_usd: float = 0.0
    graceful_stop_requested: bool = False
    graceful_stop_reason: str = ""
    completed_lenses: tuple[str, ...] = ()
    failed_lenses: tuple[str, ...] = ()
    bundles_activated: tuple[str, ...] = ()
    pause_reason: str = ""
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    stage2_pids: tuple[int, ...] = ()


@dataclass
class AuditStateFile:
    """Thread-safe persistent wrapper for ``AuditState`` at
    ``<audit_dir>/state.json``.

    Mutation via ``mutate(fn)`` holds an in-process ``threading.Lock`` for
    the read-modify-write cycle; the on-disk write itself is atomic via
    ``checkpointing.write_json`` (temp file + ``os.replace``). Concurrent
    threads see a serialized order; concurrent processes are out of scope
    in v1 (LHR D3).

    Use ``save`` for the initial commit (or any unconditional overwrite),
    ``load`` for a fresh disk read, and ``mutate`` for any read-modify-write
    flow that must serialize against other threads.
    """

    path: Path
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def load(self) -> AuditState:
        """Read the on-disk state. Raises ``FileNotFoundError`` if the file
        does not exist; raises ``json.JSONDecodeError`` on corrupt content
        (the corrupt file is left untouched on disk so an operator can
        recover it manually)."""
        data = checkpointing.read_json(self.path, default=None)
        if data is None:
            raise FileNotFoundError(f"audit state.json not found at {self.path}")
        return _from_dict(data)

    def save(self, state: AuditState) -> None:
        """Atomic overwrite. Creates parent directories if needed."""
        checkpointing.write_json(self.path, asdict(state))

    def mutate(self, fn: Callable[[AuditState], AuditState]) -> AuditState:
        """Read-modify-write under the in-process lock. ``fn`` receives the
        current state and returns a new ``AuditState`` (typically via
        ``dataclasses.replace``). Returns the new state."""
        with self._lock:
            current = self.load()
            new_state = fn(current)
            self.save(new_state)
            return new_state


def _from_dict(data: dict[str, Any]) -> AuditState:
    """Build an ``AuditState`` from a dict read off disk.

    JSON has no tuple type — list values for tuple-typed fields are coerced
    back. Extra keys in the dict are silently ignored (forward-compat with
    older snapshots that lack newer fields)."""
    return AuditState(
        audit_id=data["audit_id"],
        client_slug=data["client_slug"],
        prospect_domain=data["prospect_domain"],
        status=data.get("status", "pending"),
        total_cost_usd=float(data.get("total_cost_usd", 0.0)),
        graceful_stop_requested=bool(data.get("graceful_stop_requested", False)),
        graceful_stop_reason=data.get("graceful_stop_reason", ""),
        completed_lenses=tuple(data.get("completed_lenses", ())),
        failed_lenses=tuple(data.get("failed_lenses", ())),
        bundles_activated=tuple(data.get("bundles_activated", ())),
        pause_reason=data.get("pause_reason", ""),
        sessions=dict(data.get("sessions", {})),
        stage2_pids=tuple(data.get("stage2_pids", ())),
    )
