"""Auth commands — login, whoami, logout."""

import os
from urllib.parse import urlparse

import typer

from ..api import api_request, handle_errors, make_client
from ..config import Config, delete_config, load_config, save_config
from ..output import emit, emit_error
from ..session import get_active_session

app = typer.Typer(help="Authentication commands.", no_args_is_help=True)


@app.command()
@handle_errors
def login(
    api_key: str = typer.Option(..., "--api-key", help="API key (vi_sk_...)"),
    base_url: str = typer.Option("http://127.0.0.1:8000", "--base-url", help="API base URL"),
) -> None:
    """Store API key for future use."""
    if not api_key or not api_key.startswith("vi_sk_"):
        emit_error("invalid_api_key", "API key must start with 'vi_sk_'")

    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        emit_error("invalid_base_url", "--base-url must be a valid http(s) URL")

    # Live verify the credentials against the target backend before persisting:
    # connection / 401 surfaces here as connection_error / invalid_api_key instead
    # of a deferred failure on the next CLI call.
    probe_client = make_client(Config(api_key=api_key, base_url=base_url))
    api_request(probe_client, "GET", "/v1/auth/me")

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
