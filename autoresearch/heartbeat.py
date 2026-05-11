"""Liveness heartbeat for the autoresearch evolve loop (Stream C C16).

Pairs with ``scripts/sentinel.sh`` (vendored from AutoResearchClaw). The
sentinel watches for a stale ``heartbeat.json`` + dead pipeline PID +
no active child processes (3-of-3 gate) and restarts the evolve loop
when all three fire.

This module provides:
- ``write_heartbeat(path)`` — atomic JSON write with an ISO-8601 UTC ts
- ``write_pid(path)`` — writes the current process's PID to ``path``
- ``start_heartbeat_thread(archive_dir, interval=30.0)`` — spawns a daemon
  thread that emits the heartbeat every ``interval`` seconds; returns a
  ``threading.Event`` callers ``.set()`` to stop the thread.

The thread is daemon=True so an unhandled exception or SIGKILL in the
main thread doesn't leave it spinning. ``start_heartbeat_thread`` also
returns the thread itself so tests can ``.join(timeout=...)`` and assert
clean shutdown.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_heartbeat(path: Path) -> None:
    """Atomically write ``{"timestamp": "<iso8601>"}`` to ``path``.

    Atomic via tmp-file + ``os.replace`` so the sentinel never reads a
    half-written JSON during a process kill.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps({"timestamp": _now_iso()}))
    os.replace(tmp, path)


def write_pid(path: Path, pid: int | None = None) -> None:
    """Write the current process's PID (or ``pid`` when supplied) to
    ``path``. Used by sentinel.sh's ``pid_alive`` check."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(pid if pid is not None else os.getpid()))


def start_heartbeat_thread(
    archive_dir: Path,
    *,
    interval: float = 30.0,
    heartbeat_name: str = "heartbeat.json",
    pid_name: str = "pipeline.pid",
) -> tuple[threading.Event, threading.Thread]:
    """Spawn a daemon thread that writes a heartbeat every ``interval``
    seconds under ``archive_dir``. Returns ``(stop_event, thread)``.

    Callers should ``stop_event.set()`` in a ``finally:`` block so the
    thread exits cleanly. Daemon=True so a hard process exit doesn't
    strand the loop.
    """
    archive_dir = Path(archive_dir)
    hb_path = archive_dir / heartbeat_name
    pid_path = archive_dir / pid_name
    stop_event = threading.Event()

    # Write the PID + first heartbeat synchronously so the sentinel can
    # see liveness immediately — otherwise it would wait one ``interval``
    # before deciding the freshly-started process is alive.
    write_pid(pid_path)
    write_heartbeat(hb_path)

    def _loop() -> None:
        while not stop_event.wait(interval):
            try:
                write_heartbeat(hb_path)
            except OSError:
                # Disk pressure or permission flap — don't crash the
                # daemon thread, just skip this heartbeat and let the
                # sentinel decide on the next stale-threshold tick.
                continue

    thread = threading.Thread(target=_loop, name="autoresearch-heartbeat", daemon=True)
    thread.start()
    return stop_event, thread
