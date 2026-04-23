"""Save data to session directory — local file I/O.

Data-only tool for autoresearch sessions. No API calls.
"""

import json
from pathlib import Path

import typer

from ..config import load_config
from ..output import emit, emit_error


def save_command(
    client: str = typer.Argument(..., help="Client name"),
    key: str = typer.Argument(..., help="Data key (becomes filename, e.g. 'competitors/Nike')"),
    data: str = typer.Argument(..., help="JSON data to save"),
) -> None:
    """Save data to session directory."""
    cfg = load_config()
    if cfg is None or cfg.clients_dir is None:
        raise typer.BadParameter(
            "No clients_dir configured. Run `freddy setup` or set FREDDY_CLIENTS_DIR."
        )
    if not (cfg.clients_dir / client).exists():
        emit_error("client_not_found", f"Client '{client}' not found")
        raise SystemExit(1)

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
