"""Session commands — start, end, status."""

import json
import sys

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import LocalSession, clear_session, get_active_session, save_session

app = typer.Typer(help="Session management commands.", no_args_is_help=True)


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@app.command()
@handle_errors
def start(
    client_name: str = typer.Option("default", "--client", help="Client name"),
    session_type: str = typer.Option("ad_hoc", "--type", help="Session type"),
    purpose: str = typer.Option(None, "--purpose", help="Session purpose"),
) -> None:
    """Start a new tracking session."""
    config = _require_config()

    # Warn if session already active — close the old one
    existing = get_active_session()
    if existing:
        json.dump(
            {"warning": f"Closing existing session {existing.session_id} for {existing.client_name}"},
            sys.stderr,
        )
        sys.stderr.write("\n")
        # End the old session on the server
        client = make_client(config)
        try:
            api_request(client, "PATCH", f"/v1/sessions/{existing.session_id}", json_data={
                "status": "completed",
                "summary": "Auto-closed: new session started",
            })
        except SystemExit:
            pass  # Non-fatal — old session may already be completed
        clear_session()

    client = make_client(config)
    payload = {"client_name": client_name, "session_type": session_type}
    if purpose:
        payload["purpose"] = purpose

    result = api_request(client, "POST", "/v1/sessions", json_data=payload)

    save_session(LocalSession(
        session_id=result["id"],
        client_name=result["client_name"],
        session_type=result["session_type"],
        purpose=result.get("purpose"),
    ))

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def end(
    session_id: str = typer.Option(None, "--session-id", help="Session ID (falls back to active session)"),
    summary: str = typer.Option(None, "--summary", help="Session summary"),
) -> None:
    """End a session. Uses --session-id if provided, otherwise active session."""
    config = _require_config()

    # Resolve session ID: explicit arg > active session file
    sid = session_id
    if not sid:
        active = get_active_session()
        if not active:
            emit_error("no_active_session", "No session ID provided and no active session to end")
        sid = active.session_id

    client = make_client(config)
    payload: dict = {"status": "completed"}
    if summary:
        payload["summary"] = summary

    result = api_request(client, "PATCH", f"/v1/sessions/{sid}", json_data=payload)
    # Only clear the shared file if we used it (no explicit session_id)
    if not session_id:
        clear_session()

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def status() -> None:
    """Show current session status."""
    active = get_active_session()
    if not active:
        from ..main import get_state
        emit({"status": "no_active_session"}, human=get_state().human)
        return

    # Optionally fetch live status from server
    config = load_config()
    if config:
        client = make_client(config)
        try:
            result = api_request(client, "GET", f"/v1/sessions/{active.session_id}")
            from ..main import get_state
            emit(result, human=get_state().human)
            return
        except SystemExit:
            pass  # Fallback to local state

    from ..main import get_state
    emit({
        "session_id": active.session_id,
        "client_name": active.client_name,
        "session_type": active.session_type,
        "purpose": active.purpose,
        "source": "local_cache",
    }, human=get_state().human)
