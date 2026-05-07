"""Tests for src/audit/cleanup — terminate_subprocess + exit handlers."""
from __future__ import annotations

import subprocess
import sys
import time

import pytest

from src.audit.cleanup import (
    cleanup_on_exit,
    register_subprocess,
    terminate_subprocess,
    unregister_subprocess,
)


def _spawn_sleeper(duration_s: int = 30) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep({duration_s})"],
    )


def test_terminate_subprocess_already_exited_is_noop():
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    assert proc.poll() is not None
    # No raise.
    terminate_subprocess(proc)


def test_terminate_subprocess_sigterm_path():
    proc = _spawn_sleeper(30)
    try:
        terminate_subprocess(proc, grace_seconds=2)
    finally:
        # If terminate failed to clean up, kill hard so test doesn't hang.
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.poll() is not None  # exited


def test_terminate_subprocess_escalates_to_sigkill_after_grace():
    """A process that ignores SIGTERM gets SIGKILL'd after grace_seconds."""
    # Python -c with signal-trap that ignores SIGTERM
    proc = subprocess.Popen([
        sys.executable, "-c",
        "import signal, time; signal.signal(signal.SIGTERM, lambda *a: None); time.sleep(60)",
    ])
    try:
        # Give the trap a moment to install
        time.sleep(0.3)
        start = time.monotonic()
        terminate_subprocess(proc, grace_seconds=1)
        elapsed = time.monotonic() - start
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.poll() is not None
    # SIGKILL should land within ~1s grace + small delta
    assert elapsed < 4.0


def test_register_unregister_subprocess():
    proc = _spawn_sleeper(60)
    try:
        register_subprocess(proc)
        unregister_subprocess(proc)
        # No leftover state; calling unregister twice is safe.
        unregister_subprocess(proc)
    finally:
        proc.kill()
        proc.wait()


def test_cleanup_on_exit_context_manager_terminates_proc():
    proc = _spawn_sleeper(30)
    try:
        with cleanup_on_exit(proc, grace_seconds=2):
            assert proc.poll() is None  # still running inside the with
        # On exit, proc is terminated.
        proc.wait(timeout=5)
        assert proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_cleanup_on_exit_propagates_exception_after_terminating():
    proc = _spawn_sleeper(30)
    with pytest.raises(RuntimeError, match="boom"):
        try:
            with cleanup_on_exit(proc, grace_seconds=2):
                raise RuntimeError("boom")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    assert proc.poll() is not None
