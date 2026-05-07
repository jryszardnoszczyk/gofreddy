"""Tests for autoresearch/evolve_lock.py — the live-vs-evolve mutex."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from autoresearch.evolve_lock import EvolveLock, EvolveLockHeld


def test_acquire_and_release(tmp_path: Path, monkeypatch):
    """Basic context manager — acquire, file written, release."""
    monkeypatch.setattr(
        "autoresearch.evolve_lock.LOCK_PATH",
        tmp_path / "state.evolve_lock",
    )
    with EvolveLock(holder="test-1") as lock:
        assert (tmp_path / "state.evolve_lock").is_file()
        assert (tmp_path / "state.evolve_lock").read_text(encoding="utf-8") == "test-1"
    # After exit, the lock file persists (we don't delete it) but is
    # no longer flock-held; another acquisition should succeed.
    with EvolveLock(holder="test-2"):
        assert (tmp_path / "state.evolve_lock").read_text(encoding="utf-8") == "test-2"


def test_concurrent_acquire_raises(tmp_path: Path, monkeypatch):
    """Second EvolveLock in the same process raises immediately."""
    monkeypatch.setattr(
        "autoresearch.evolve_lock.LOCK_PATH",
        tmp_path / "state.evolve_lock",
    )
    with EvolveLock(holder="first"):
        with pytest.raises(EvolveLockHeld) as exc_info:
            with EvolveLock(holder="second"):
                pytest.fail("should not have acquired")
        assert "first" in str(exc_info.value)
        assert exc_info.value.holder_info == "first"


def test_lock_released_after_exit_allows_new_acquire(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "autoresearch.evolve_lock.LOCK_PATH",
        tmp_path / "state.evolve_lock",
    )
    with EvolveLock(holder="A"):
        pass
    # Should not raise.
    with EvolveLock(holder="B") as lock:
        pass


def test_lock_blocks_subprocess(tmp_path: Path, monkeypatch):
    """Cross-process: spawn a subprocess that tries to acquire while we hold the lock.
    The subprocess should observe EvolveLockHeld."""
    lock_path = tmp_path / "state.evolve_lock"
    monkeypatch.setattr("autoresearch.evolve_lock.LOCK_PATH", lock_path)

    repo_root = Path(__file__).resolve().parent.parent.parent
    code = (
        "import sys; sys.path.insert(0, "
        f"{repr(str(repo_root))}); "
        "from autoresearch import evolve_lock; "
        f"evolve_lock.LOCK_PATH = __import__('pathlib').Path({repr(str(lock_path))}); "
        "import sys\n"
        "try:\n"
        "    with evolve_lock.EvolveLock(holder='child'):\n"
        "        sys.exit(0)\n"
        "except evolve_lock.EvolveLockHeld as e:\n"
        "    sys.stdout.write(f'BLOCKED:{e.holder_info}')\n"
        "    sys.exit(7)\n"
    )

    with EvolveLock(holder="parent-pid-x"):
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=15,
        )
    assert result.returncode == 7, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "BLOCKED:" in result.stdout
    assert "parent-pid-x" in result.stdout


def test_default_holder_includes_pid(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "autoresearch.evolve_lock.LOCK_PATH",
        tmp_path / "state.evolve_lock",
    )
    with EvolveLock() as lock:
        info = (tmp_path / "state.evolve_lock").read_text(encoding="utf-8")
        assert str(os.getpid()) in info
