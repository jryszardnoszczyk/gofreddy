"""No-op session-id tracking shim.

Per Plan B U10 (2026-05-11): the real session lifecycle tracker (atomic
JSON writes, status transitions, resume hooks) was decommissioned with
the --resume-variant machinery (U2). Nothing reads
``.session_ids.json`` anymore — every consumer was either the resume
code path itself or operator-facing forensic display.

This module preserves the SessionsFile API (begin/finish kwargs in
evaluate_variant.py + evolve.py + program_prescription_critic.py) so
those call sites don't need to be touched, but every method is a
no-op. The disk file is never written or read.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

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
    """No-op shim. Constructor accepts a path for caller compatibility but
    does no IO. begin/finish accept their original kwargs and discard."""

    path: Path
    _records: dict = field(default_factory=dict, init=False, repr=False)

    def begin(
        self, agent_key: str, session_id: str, engine: str = "claude",
    ) -> None:
        return None

    def finish(self, agent_key: str, status: Status) -> None:
        return None
