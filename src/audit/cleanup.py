"""Subprocess cleanup — SIGTERM→wait→SIGKILL escalation + exit handlers.

Per LHR D3 the audit pipeline runs ONE ``claude -p`` subprocess at a
time per stage call (Stage 2's fan-out is concurrent but each lens is
its own subprocess), so the cleanup primitive operates per-Popen, not on
a process group. Caller pattern: spawn → ``with cleanup_on_exit(proc):``
→ work → exit (the with-block terminates the proc on its way out).

Exit handlers (atexit + SIGTERM + SIGINT) drain a global registry of
live subprocesses on interpreter shutdown so a Ctrl-C or kill signal
doesn't leak a claude subprocess into the operator's session.

Ports the SIGTERM→5s→SIGKILL pattern from ``harness/worktree.py:349-379``
and the ``_install_exit_handlers`` shape from
``harness/worktree.py:396-414`` — both adapted to per-Popen scope (no
process group, no port-killing — audit doesn't run a backend server).
"""
from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import threading
from contextlib import contextmanager
from typing import Iterator

# Global registry of live subprocesses + a lock to serialize register/unregister
# during signal-handler reentrance. Module-private — callers go through the
# public API.
_LIVE: set[subprocess.Popen] = set()
_LOCK = threading.Lock()
_HANDLERS_INSTALLED = False


def terminate_subprocess(
    proc: subprocess.Popen, *, reason: str = "", grace_seconds: int = 5
) -> None:
    """SIGTERM → wait ``grace_seconds`` → SIGKILL escalation. No-op if the
    process has already exited. Port of
    ``harness/worktree.py:_terminate_backend`` simplified: no process group
    (audit's claude subprocess is single-process)."""
    if proc.poll() is not None:
        return
    if reason:
        print(f"[cleanup] terminating subprocess pid={proc.pid} reason={reason}", file=sys.stderr)
    try:
        proc.terminate()
    except (ProcessLookupError, PermissionError):
        return
    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            # Process is wedged; give up. Caller's `with` block has logged
            # the situation — best-effort beyond this is OS responsibility.
            pass


def register_subprocess(proc: subprocess.Popen) -> None:
    """Add ``proc`` to the global cleanup registry. Idempotent."""
    with _LOCK:
        _LIVE.add(proc)


def unregister_subprocess(proc: subprocess.Popen) -> None:
    """Remove ``proc`` from the registry. Idempotent — safe to call after
    the caller has already cleaned up via its ``with`` block."""
    with _LOCK:
        _LIVE.discard(proc)


@contextmanager
def cleanup_on_exit(
    proc: subprocess.Popen, *, grace_seconds: int = 5
) -> Iterator[subprocess.Popen]:
    """Register ``proc`` for cleanup on context exit AND on
    interpreter-level exit handlers. Terminates the process on the way
    out via ``terminate_subprocess``. Exceptions inside the with-block
    propagate after termination."""
    register_subprocess(proc)
    try:
        yield proc
    finally:
        try:
            terminate_subprocess(proc, grace_seconds=grace_seconds)
        finally:
            unregister_subprocess(proc)


def install_exit_handlers() -> None:
    """Idempotently register atexit + SIGTERM + SIGINT handlers that drain
    the cleanup registry. Call once at audit-runner startup (or rely on
    ``cleanup_on_exit`` callers to spawn under an already-installed
    handler)."""
    global _HANDLERS_INSTALLED
    if _HANDLERS_INSTALLED:
        return

    def _drain(*_: object) -> None:
        with _LOCK:
            procs = list(_LIVE)
            _LIVE.clear()
        for proc in procs:
            try:
                terminate_subprocess(proc, grace_seconds=5)
            except Exception:  # noqa: BLE001 — best effort during shutdown
                pass

    atexit.register(_drain)
    signal.signal(signal.SIGTERM, lambda *_: (_drain(), os._exit(143)))
    signal.signal(signal.SIGINT, lambda *_: (_drain(), os._exit(130)))
    _HANDLERS_INSTALLED = True
