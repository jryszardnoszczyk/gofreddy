"""Session-id helpers for claude/codex resume — slim port of v1 sessions.py.

v1's sessions.py (201 LOC) included a `SessionsFile` class for per-variant
on-disk session tracking (0 production resume hits per audit). v2 drops the
whole forensic-tracking layer and keeps only the two helpers that callers
outside autoresearch actually need:

  - claude_session_jsonl(wt, sid) — where claude-CLI stores rollout JSONL
  - viable_resume_id(engine, sid, wt) — None if rollout JSONL is missing

Also exposes the v2 NO_OP_SHIM `ensure_materialized_runtime(lane)` so
`cli/freddy/fixture/dryrun.py`'s existing import keeps working after U13
repoints the namespace (per U0 operator-script audit).
"""

from __future__ import annotations

from pathlib import Path


def claude_session_jsonl(wt_path: Path, session_id: str) -> Path:
    """Path where claude-CLI stores this session's rollout JSONL.

    Claude maps cwd → projects/ subdir by replacing `/` with `-`. If the
    file doesn't exist, the session was never successfully created.
    """
    encoded = str(wt_path).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded / f"{session_id}.jsonl"


def codex_session_jsonl(session_id: str) -> Path | None:
    """Path where codex-CLI stores this session's rollout JSONL, or None.

    Codex stores at ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl.
    """
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.is_dir():
        return None
    matches = list(sessions_root.rglob(f"rollout-*-{session_id}.jsonl"))
    return matches[0] if matches else None


def viable_resume_id(engine: str, session_id: str, wt_path: Path | None = None) -> str | None:
    """Return session_id if the engine's local rollout/JSONL exists, else None.

    v1 took a SessionRecord; v2 takes the (engine, session_id) pair directly
    since SessionsFile is gone. Opencode lacks a stable resume mechanism so
    always returns None for that engine.
    """
    if engine == "claude":
        if wt_path is None:
            return None
        return session_id if claude_session_jsonl(wt_path, session_id).is_file() else None
    if engine == "codex":
        return session_id if codex_session_jsonl(session_id) is not None else None
    return None


def ensure_materialized_runtime(lane: str) -> Path:
    """v2 NO_OP_SHIM (per U0 audit). v2 has no per-variant materialization;
    returns the lane prose dir directly. Keeps `cli/freddy/fixture/dryrun.py`'s
    import working post-U13 namespace repoint.
    """
    import os
    root = os.environ.get("AUTORESEARCH_V2_ROOT")
    base = Path(root) if root else Path(__file__).resolve().parent.parent.parent
    return base / "autoresearch_v2" / "lanes" / lane
