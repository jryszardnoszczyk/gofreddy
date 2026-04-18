"""Freddy tracking -- push session and iteration events to the backend."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from watchdog import phase_type, tracking_status_from_entry  # type: ignore  # noqa: E402


def tracking_start(client: str, session_type: str, purpose: str) -> str | None:
    """Start freddy tracking session. Returns session_id or None."""
    if not shutil.which("freddy"):
        return None
    try:
        result = subprocess.run(
            ["freddy", "session", "start", "--client", client, "--type", session_type, "--purpose", purpose],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                return data.get("id")
            except json.JSONDecodeError:
                match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", result.stdout)
                return match.group(0) if match else None
    except Exception:
        pass
    return None


def tracking_end(session_id: str | None, summary: str):
    """End freddy tracking session."""
    if not session_id:
        return
    try:
        subprocess.run(
            ["freddy", "session", "end", "--session-id", session_id, "--summary", summary],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        pass


def push_iteration(session_id: str | None, number: int, session_dir: Path,
                   exit_code: int, duration_ms: int, log_path: Path):
    """Push iteration data to freddy backend. Non-fatal."""
    if not shutil.which("freddy"):
        return
    try:
        results_file = session_dir / "results.jsonl"
        last_line = ""
        if results_file.exists():
            lines = results_file.read_text().strip().splitlines()
            if lines:
                last_line = lines[-1]

        iter_type = "unknown"
        if last_line:
            try:
                iter_type = json.loads(last_line).get("type", "unknown")
            except json.JSONDecodeError:
                pass

        if exit_code == 0:
            status = "success"
        elif exit_code == 124:
            status = "timeout"
        else:
            status = "failed"

        cmd = ["freddy", "iteration", "push",
               "--number", str(number), "--type", iter_type,
               "--status", status, "--exit-code", str(exit_code),
               "--duration-ms", str(duration_ms),
               "--state-file", str(session_dir / "session.md"),
               "--log-file", str(log_path)]
        if last_line:
            cmd += ["--result", last_line]
        if session_id:
            cmd += ["--session-id", session_id]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def push_phase_event(session_id: str | None, number: int, session_dir: Path, raw_result_line: str,
                     result_entry: dict, duration_ms: int, log_path: Path, exit_code: int = 0):
    """Push one multi-turn phase event to freddy backend. Non-fatal."""
    if not shutil.which("freddy"):
        return
    try:
        cmd = ["freddy", "iteration", "push",
               "--number", str(number),
               "--type", phase_type(result_entry),
               "--status", tracking_status_from_entry(result_entry),
               "--exit-code", str(exit_code),
               "--duration-ms", str(duration_ms),
               "--state-file", str(session_dir / "session.md"),
               "--log-file", str(log_path),
               "--result", raw_result_line]
        if session_id:
            cmd += ["--session-id", session_id]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass
