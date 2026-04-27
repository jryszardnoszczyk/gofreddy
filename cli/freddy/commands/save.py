"""Save data to session directory — local file I/O.

Data-only tool for autoresearch sessions. No API calls.
"""

import json
import re
from pathlib import Path

import typer

from ..output import emit, emit_error

# Reject keys that produce hidden files (".json"), bare dot names ("..json"),
# or otherwise non-descriptive filenames. Path-traversal escapes are caught
# separately by the resolve() check below — this rule covers what stays
# inside the session dir but still creates pathological filenames (F-a-5-2).
_INVALID_KEY_RE = re.compile(r"^\.*$")


def save_command(
    client: str = typer.Argument(..., help="Client name"),
    key: str = typer.Argument(..., help="Data key (becomes filename, e.g. 'competitors/Nike')"),
    data: str = typer.Argument(..., help="JSON data to save"),
) -> None:
    """Save data to session directory."""
    if _INVALID_KEY_RE.match(key.strip()) or "/" not in key and not key.strip():
        emit_error(
            "invalid_key",
            f"Key {key!r} is empty or only dots; pick a non-empty descriptive key",
        )
    # Each path segment of `key` must be non-empty and non-dot-only.
    for segment in key.split("/"):
        if _INVALID_KEY_RE.match(segment):
            emit_error(
                "invalid_key",
                f"Key segment {segment!r} (in {key!r}) is empty or only dots",
            )

    session_dir = Path("sessions/competitive") / client

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        emit_error("invalid_json", "Data argument must be valid JSON")
        return

    # Resolve path safely — prevent directory traversal
    target = (session_dir / f"{key}.json").resolve()
    if not str(target).startswith(str(session_dir.resolve())):
        emit_error("path_traversal", "Key must not escape session directory")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parsed, indent=2, default=str))

    from ..main import get_state
    emit({"saved": str(target), "key": key, "client": client}, human=get_state().human)
