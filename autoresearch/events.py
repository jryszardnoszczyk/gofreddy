"""Append-only unified events log for autoresearch-side audit trails.

Writers hold an exclusive flock across write+flush+fsync (POSIX advisory lock).
Readers hold a shared lock. On size > 100MB, log_event rotates to
``events.jsonl.<YYYYMMDD-HHMMSS>``. read_events concatenates rotated segments
(oldest first by mtime) then the current file.
"""
from __future__ import annotations

import datetime as _dt
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Iterator

EVENTS_LOG = Path.home() / ".local/share/gofreddy/events.jsonl"
ROTATION_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MB


class EventLogCorruption(RuntimeError):
    """Raised when a non-empty events.jsonl line fails to parse as JSON."""


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _maybe_rotate(path: Path) -> None:
    if not path.exists() or path.stat().st_size < ROTATION_THRESHOLD_BYTES:
        return
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    path.rename(path.parent / f"{path.name}.{stamp}")


def log_event(kind: str, **data: Any) -> None:
    """Append one ``{kind, timestamp, **data}`` record as a single JSONL line.

    Exclusive-locked to prevent torn lines under concurrent writers.
    Durability: flush + fsync after every write.
    """
    path = EVENTS_LOG
    _ensure_parent(path)
    _maybe_rotate(path)
    record = {
        "kind": kind,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        **data,
    }
    with path.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_events(
    *, kind: str | None = None, path: Path | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield records from events.jsonl + rotated segments, filtered by kind.

    Shared-locked (reads can run concurrently). Malformed lines raise
    EventLogCorruption with the file + line number — never silent skip.
    Ordering: rotated segments in mtime order (oldest first), then current file.
    """
    root = path or EVENTS_LOG
    rotated = sorted(
        root.parent.glob(root.name + ".*"),
        key=lambda p: p.stat().st_mtime,
    ) if root.parent.exists() else []
    segments: list[Path] = list(rotated)
    if root.exists():
        segments.append(root)
    for segment in segments:
        with segment.open("r") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                for line_no, raw in enumerate(handle, start=1):
                    line = raw.rstrip("\n")
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise EventLogCorruption(
                            f"{segment}:{line_no}: {exc}"
                        ) from exc
                    if kind is None or record.get("kind") == kind:
                        yield record
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
