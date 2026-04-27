"""Digest commands — persist, list, check weekly digests."""

import json
from pathlib import Path

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Digest management commands.", no_args_is_help=True)


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@app.command()
@handle_errors
def persist(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    file: str = typer.Option(..., "--file", help="Path to digest metadata JSON file"),
) -> None:
    """Persist digest metadata to weekly_digests table via REST API."""
    config = _require_config()
    client = make_client(config)

    # F-a-5-6: precheck file path so missing/unreadable inputs surface as a
    # typed error instead of being swallowed by @handle_errors and reported
    # as the generic unexpected_error (which is also the code the server emits).
    from pathlib import Path
    file_path = Path(file)
    if not file_path.is_file():
        emit_error("file_not_found", f"Digest metadata file not found: {file}")
    try:
        with file_path.open() as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        emit_error("invalid_json", f"Digest metadata is not valid JSON: {exc}")

    result = api_request(
        client, "POST", f"/v1/monitors/{monitor_id}/digests",
        json_data=payload,
    )

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command(name="list")
@handle_errors
def list_digests(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    limit: int = typer.Option(4, "--limit", help="Number of recent digests"),
) -> None:
    """List recent weekly digests for a monitor."""
    config = _require_config()
    client = make_client(config)

    result = api_request(
        client, "GET", f"/v1/monitors/{monitor_id}/digests",
        params={"limit": limit},
    )

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command(deprecated=True)
@handle_errors
def check(
    session_dir: str = typer.Argument(..., help="Session directory path"),
) -> None:
    """[Deprecated] Absorbed into server-side evaluation. Use `freddy evaluate variant monitoring`."""
    emit_error("deprecated", "digest check has been absorbed into server-side evaluation. "
               "Use: freddy evaluate variant monitoring <session_dir>")
