"""Auth commands — login, whoami, logout."""

import os

import typer

from ..api import api_request, handle_errors, make_client
from ..config import delete_config, load_config, save_config
from ..output import emit, emit_error
from ..session import get_active_session

app = typer.Typer(help="Authentication commands.", no_args_is_help=True)


@app.command()
@handle_errors
def login(
    api_key: str = typer.Option(..., "--api-key", help="API key (vi_sk_...)"),
    base_url: str = typer.Option("https://api.freddy.example", "--base-url", help="API base URL"),
) -> None:
    """Store API key for future use."""
    save_config(api_key=api_key, base_url=base_url)

    from ..main import get_state
    emit({"status": "ok", "message": "API key saved to ~/.freddy/config.json"}, human=get_state().human)


@app.command()
@handle_errors
def whoami() -> None:
    """Show current user and active session."""
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")

    client = make_client(config)
    result = api_request(client, "GET", "/v1/auth/me")

    session = get_active_session()
    output = {
        "user": result,
        "active_session": {
            "session_id": session.session_id,
            "client_name": session.client_name,
        } if session else None,
    }

    from ..main import get_state
    emit(output, human=get_state().human)


@app.command()
@handle_errors
def logout() -> None:
    """Remove stored API key."""
    deleted = delete_config()
    env_key_active = bool(os.environ.get("FREDDY_API_KEY"))

    from ..main import get_state
    if deleted:
        message = "API key removed"
    else:
        message = "No config file found"

    output: dict = {"status": "ok", "message": message}
    if env_key_active:
        output["warning"] = (
            "FREDDY_API_KEY env var is still set — unset it to fully log out "
            "(otherwise `freddy auth whoami` will continue to authenticate)."
        )

    emit(output, human=get_state().human)
