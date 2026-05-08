"""Mutex between live audit runs and evolve runs.

Per origin Key Decisions §R16: a live ``freddy audit run`` and an
``autoresearch evolve --lane marketing_audit`` must not run concurrently
— evolve mutates the materialized variant directory that live audits
read at runtime, and a partial mutation mid-audit would silently
corrupt deliverables.

Uses ``fcntl.flock`` with ``LOCK_EX | LOCK_NB`` on a single lock file at
``~/.local/share/gofreddy/state.evolve_lock``. Acquisition is non-blocking
— if held by another process, ``__enter__`` raises ``EvolveLockHeld``
immediately. The lock file's contents are descriptive (caller name +
PID) for operator debugging; the lock itself is the file descriptor's
``flock`` state, not file presence.

Caller pattern::

    with EvolveLock(holder="freddy audit run a-001"):
        run_audit()  # evolve will EvolveLockHeld until this exits

The lock is released automatically on ``__exit__`` and on process exit
(the kernel drops flocks when the holding fd closes).
"""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
from types import TracebackType


# Lock file lives next to autoresearch's events log so both share
# ~/.local/share/gofreddy/ as the per-user state root.
LOCK_PATH: Path = Path.home() / ".local/share/gofreddy/state.evolve_lock"


class EvolveLockHeld(RuntimeError):
    """Raised when ``EvolveLock`` cannot acquire because another process
    already holds the mutex.

    Carries ``holder_info`` (the file's contents, typically caller name +
    PID) so the operator can identify what's running.

    Lives in this module rather than ``src.audit.exceptions`` because it
    must also be raisable from autoresearch-side callers (``evolve.py``)
    that don't depend on ``src/audit/``. Re-exported by
    ``src.audit.exceptions`` for symmetry with other audit-side errors.
    """

    def __init__(self, holder_info: str = "") -> None:
        self.holder_info = holder_info
        super().__init__(
            f"evolve lock at {LOCK_PATH} is already held: {holder_info or 'unknown'}"
        )


class EvolveLock:
    """Non-blocking exclusive lock context manager.

    Holder strings are written to the lock file at acquisition so other
    processes can read them on conflict. The file descriptor is kept open
    for the duration of the context — the kernel releases the flock when
    the fd closes (on ``__exit__`` or process exit)."""

    def __init__(self, *, holder: str = "") -> None:
        self.holder = holder or f"pid={os.getpid()}"
        self._fd: int | None = None

    def __enter__(self) -> EvolveLock:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Open RW so we can read the prior holder's info on conflict and
        # overwrite it on success. O_CREAT so the file exists; we never
        # delete it (just rewrite the contents).
        fd = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Read whatever the prior holder wrote (best-effort — may be
            # empty or stale; not load-bearing for correctness).
            try:
                holder_info = os.read(fd, 256).decode("utf-8", errors="replace").strip()
            except OSError:
                holder_info = ""
            os.close(fd)
            raise EvolveLockHeld(holder_info)
        # Truncate + write our holder string.
        os.ftruncate(fd, 0)
        os.write(fd, self.holder.encode("utf-8"))
        os.fsync(fd)
        self._fd = fd
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._fd is None:
            return
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(self._fd)
        self._fd = None
