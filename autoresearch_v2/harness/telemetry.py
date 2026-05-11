"""Freddy session/iteration telemetry — slim port of v1 harness/telemetry.py.

Pushes evolution-loop events to JR's freddy backend for the web UI.
Slim from 187 → ~85 LOC. Kept: tracking_start / tracking_end /
push_iteration / push_phase_event. Dropped: compute_inner_keep_rate
(v2 reads results.tsv directly; the per-variant scores.json aggregation
this function did is gone with v1).

All functions silently no-op when `freddy` CLI isn't on PATH — telemetry
is non-blocking by design.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

_TIMEOUT_S = 30
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _freddy_available() -> bool:
    return shutil.which("freddy") is not None


def _run_silent(cmd: list[str]) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT_S)
    except Exception:
        return None


def tracking_start(client: str, session_type: str, purpose: str) -> str | None:
    """Start a freddy tracking session; return session_id or None."""
    if not _freddy_available():
        return None
    result = _run_silent([
        "freddy", "session", "start",
        "--client", client, "--type", session_type, "--purpose", purpose,
    ])
    if result is None or not result.stdout:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("id")
    except json.JSONDecodeError:
        match = _UUID_RE.search(result.stdout)
        return match.group(0) if match else None


def tracking_end(session_id: str | None, summary: str) -> None:
    if not session_id or not _freddy_available():
        return
    _run_silent([
        "freddy", "session", "end",
        "--session-id", session_id, "--summary", summary,
    ])


def push_iteration(
    session_id: str | None,
    number: int,
    session_dir: Path,
    exit_code: int,
    duration_ms: int,
    log_path: Path,
) -> None:
    if not _freddy_available():
        return
    results_file = session_dir / "results.jsonl"
    last_line = ""
    iter_type = "unknown"
    if results_file.exists():
        try:
            lines = results_file.read_text().strip().splitlines()
            if lines:
                last_line = lines[-1]
                iter_type = json.loads(last_line).get("type", "unknown")
        except (OSError, json.JSONDecodeError):
            pass

    status = "success" if exit_code == 0 else ("timeout" if exit_code == 124 else "failed")
    cmd = [
        "freddy", "iteration", "push",
        "--number", str(number), "--type", iter_type,
        "--status", status, "--exit-code", str(exit_code),
        "--duration-ms", str(duration_ms),
        "--state-file", str(session_dir / "session.md"),
        "--log-file", str(log_path),
    ]
    if last_line:
        cmd += ["--result", last_line]
    if session_id:
        cmd += ["--session-id", session_id]
    _run_silent(cmd)


def push_phase_event(
    session_id: str | None,
    number: int,
    session_dir: Path,
    raw_result_line: str,
    log_path: Path,
) -> None:
    """Push a single in-iteration phase event (used by render pipeline).
    Non-fatal — same swallowed-exception semantics as the rest of this module.
    """
    if not session_id or not _freddy_available():
        return
    _run_silent([
        "freddy", "iteration", "push",
        "--session-id", session_id,
        "--number", str(number),
        "--state-file", str(session_dir / "session.md"),
        "--log-file", str(log_path),
        "--result", raw_result_line,
        "--status", "in_progress",
    ])
