"""Audit-scoped wrapper around ``harness.sessions.SessionsFile``.

The harness primitive is generic — it persists ``session_id`` + ``status``
per ``agent_key`` to a JSON file, with a ``threading.Lock`` and atomic
rename for safe concurrent writes. The audit pipeline reuses it directly,
scoped to ``<audit_dir>/sessions.json`` with ``agent_key`` values like
``"stage_0"``, ``"stage_1b"``, ``"stage_2_lens_L-A-01"``.

Direct-import fit per plan §Relevant Code (harness/sessions.py:56). This
module exists only to anchor the audit-specific path convention so callers
don't repeat ``audit_dir / "sessions.json"`` everywhere.
"""
from __future__ import annotations

from pathlib import Path

from harness.sessions import SessionsFile


def open_audit_sessions(audit_dir: Path) -> SessionsFile:
    """Open or create the per-audit sessions file at ``<audit_dir>/sessions.json``.

    ``SessionsFile`` lazy-loads on init (empty dict if file is missing) and
    creates parent directories on first write, so passing a fresh
    ``audit_dir`` is safe."""
    return SessionsFile(audit_dir / "sessions.json")
