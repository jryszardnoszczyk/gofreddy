"""No-op session-id tracking shim.

Per Plan B U10 (2026-05-11): the real session lifecycle tracker (atomic
JSON writes, status transitions, resume hooks) was decommissioned with
the --resume-variant machinery (U2). Nothing reads ``.session_ids.json``
anymore — every consumer was either the resume code path itself or
operator-facing forensic display.

This module preserves the SessionsFile API (begin/finish/get) for the
3 surviving call sites (evolve.py + evaluate_variant.py +
program_prescription_critic.py) so they don't need to be touched, but
every method is a no-op and ``get()`` always returns None — the cache-
skip path in evaluate_variant.py:_run_and_score_fixture relies on
``prior is None`` falling through to the mtime-based 24h check.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SessionsFile:
    """No-op shim. Constructor accepts a path for caller compatibility but
    does no IO."""

    path: Path

    def begin(self, agent_key: str, session_id: str, engine: str = "claude") -> None:
        return None

    def finish(self, agent_key: str, status: str) -> None:
        return None

    def get(self, agent_key: str) -> None:
        """Always returns None — see module docstring for cache-skip semantics."""
        return None
