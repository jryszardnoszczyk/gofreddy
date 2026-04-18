"""Shared utilities -- locks, subprocess helpers, JSON loading, timeout defaults."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

from workflows import get_workflow_spec  # type: ignore  # noqa: E402

SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR


def _lock_path(domain: str, client: str, fixture_id: str | None = None) -> Path:
    fixture_id = fixture_id or os.environ.get("AUTORESEARCH_FIXTURE_ID")
    if fixture_id:
        lock_name = f"{domain}-session-{client}-{fixture_id}.lock"
    else:
        lock_name = f"{domain}-session-{client}.lock"
    return Path(tempfile.gettempdir()) / lock_name


def acquire_lock(domain: str, client: str, fixture_id: str | None = None) -> int | None:
    """Acquire per-client file lock. Returns fd or None on failure.

    When *fixture_id* is provided (or set via ``AUTORESEARCH_FIXTURE_ID``),
    the lock is keyed per-fixture so parallel fixture runs don't collide.
    Callers MUST release via release_lock(fd, domain, client, fixture_id)
    on normal and exceptional exits.
    """
    lock_path = _lock_path(domain, client, fixture_id)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (OSError, IOError):
        print(f"Session already running for {client} ({domain})")
        return None


def release_lock(fd: int | None, domain: str, client: str, fixture_id: str | None = None) -> None:
    """Release the lock acquired via acquire_lock. Safe to call with fd=None."""
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        _lock_path(domain, client, fixture_id).unlink(missing_ok=True)
    except OSError:
        pass


def default_timeout_for_strategy(domain: str, strategy: str) -> int:
    cfg = get_workflow_spec(domain).config
    if strategy == "multiturn":
        return cfg.multiturn_timeout or max(cfg.default_timeout, 7200)
    return cfg.default_timeout


def _load_json_output(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def _run_script(script_name: str, *args, stdout_file: Path | None = None):
    """Run a script from SCRIPT_DIR/scripts/. Non-fatal."""
    script = SCRIPT_DIR / "scripts" / script_name
    if not script.exists():
        return
    try:
        cmd = ["python3", str(script)] + list(args)
        if stdout_file:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            stdout_file.write_text(result.stdout)
        else:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"WARNING: {script_name} failed: {e}")


def _run_subprocess(cmd: list[str]):
    """Run arbitrary subprocess. Non-fatal."""
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"WARNING: {cmd[0]} failed: {e}")
