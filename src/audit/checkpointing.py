"""Atomic file read/write for audit state + per-stage checkpoints.

The audit pipeline writes state.json and per-stage output files to
`clients/<slug>/audit/`. A crash mid-write must not corrupt prior state —
resumed audits need to see either the old value (pre-write) or the new
value (post-write), never a partial file.

Strategy: write to a sibling temp file in the same directory, fsync, then
`os.replace()` onto the target path. `os.replace()` is atomic on POSIX (and
Windows ≥ Vista) when source and destination are on the same filesystem;
keeping the temp file in the same directory guarantees that.

Scope:

- Plain-JSON helpers (load/save/update). No schema knowledge — callers
  handle Pydantic validation themselves.
- No locking across processes. v1 serializes audits at the worker level
  (one audit per process per LHR design decision D3), so file-level locks
  would be premature. When/if v2 parallelizes audits per prospect, add
  `portalocker` here.

Not in scope: `state.py`'s `AuditState` Pydantic model + method surface
(`.load`, `.save`, `.record_session`, `.add_cost`, `.commit_stage`, etc.)
— that lives one layer up and uses these helpers.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable


def write_atomic(path: Path, content: str) -> None:
    """Write `content` to `path` via temp-file + os.replace. Creates parent
    directories if needed. Raises on I/O failure; never leaves a partial file
    at `path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # NamedTemporaryFile with delete=False because os.replace consumes the
    # temp file. `dir=path.parent` ensures the rename is cross-device-safe
    # (same filesystem). Suffix disambiguates concurrent writers to different
    # target paths using the same parent directory.
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, path)
    except Exception:
        # Clean up the temp file on any failure so we don't leak .tmp files.
        try:
            os.unlink(tmp.name)
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON from `path`. Returns `default` if the file doesn't exist.
    Raises `json.JSONDecodeError` on malformed content (deliberately — a
    corrupt checkpoint is a bug to surface, not paper over).
    """
    path = Path(path)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """Serialize `data` as JSON and write atomically. Sorts keys for
    reproducible diffs. Uses `default=str` so Pydantic HttpUrl / datetime
    round-trip without per-caller converters.
    """
    content = json.dumps(data, indent=indent, sort_keys=True, default=str) + "\n"
    write_atomic(Path(path), content)


def atomic_update(path: Path, mutate: Callable[[Any], Any], *, default: Any = None) -> Any:
    """Read-modify-write with atomic commit. Returns the new value.

    `mutate` receives the current value (or `default` if the file is missing)
    and returns the new value. The new value is written atomically; callers
    that need stronger isolation than "single-process, serialized" should
    reach for an actual lock.
    """
    current = read_json(path, default=default)
    new_value = mutate(current)
    write_json(path, new_value)
    return new_value
