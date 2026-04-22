"""Save data to session directory — local file I/O.

Data-only tool for autoresearch sessions. No API calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session


def save_command(
    client: str = typer.Argument(..., help="Client name"),
    key: str = typer.Argument(..., help="Data key (becomes filename, e.g. 'competitors/Nike')"),
    data: str = typer.Argument(..., help="JSON data to save"),
) -> None:
    """Save data to session directory."""
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        emit_error("invalid_json", "Data argument must be valid JSON")
        return

    cfg = load_config()
    if cfg is None or cfg.clients_dir is None:
        emit_error(
            "no_clients_dir",
            "No clients_dir configured. Run `freddy setup` or set FREDDY_CLIENTS_DIR.",
        )
        return

    active = get_active_session()
    session_name = active.session_id if active and active.client_name == client else "ad-hoc"
    session_dir = cfg.clients_dir / client / "sessions" / session_name

    # Resolve path safely — prevent directory traversal
    target = (session_dir / f"{key}.json").resolve()
    if not str(target).startswith(str(session_dir.resolve())):
        emit_error("path_traversal", "Key must not escape session directory")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(parsed, indent=2, default=str))

    action = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool_name": "save",
        "status": "success",
        "input_summary": {"key": key},
        "output_summary": {"path": str(target)},
    }
    with (session_dir / "actions.jsonl").open("a") as f:
        f.write(json.dumps(action) + "\n")

    from ..main import get_state
    emit({"saved": str(target), "key": key, "client": client}, human=get_state().human)
