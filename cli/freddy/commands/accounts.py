"""Manage connected social platform accounts."""

from __future__ import annotations

import sys
import time
import webbrowser

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Manage connected social platform accounts.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def connect(
    platform: str = typer.Argument(..., help="Platform: linkedin, bluesky, tiktok, youtube"),
) -> None:
    """Connect a social platform account via OAuth device flow."""
    client = _get_client()

    if platform == "bluesky":
        # Bluesky uses app password, not OAuth
        handle = typer.prompt("Bluesky handle (e.g. user.bsky.social)")
        app_password = typer.prompt("App password", hide_input=True)
        result = api_request(
            client, "POST", "/v1/accounts/connect/bluesky",
            json_data={"handle": handle, "app_password": app_password},
        )
        from ..main import get_state
        emit({"status": "connected", "account_name": result.get("account_name")}, human=get_state().human)
        return

    # OAuth device flow for linkedin, tiktok, youtube
    data = api_request(
        client, "POST", "/v1/accounts/oauth/device-init",
        json_data={"platform": platform},
    )

    typer.echo(f"\nVisit: {data['verification_uri']}")
    typer.echo(f"Enter code: {data['user_code']}\n")

    # Try to open browser
    try:
        url = data.get("verification_uri_complete") or data["verification_uri"]
        webbrowser.open(url)
    except Exception:
        pass

    interval = data.get("interval", 5)
    typer.echo("Waiting for authorization...")

    for _ in range(data.get("expires_in", 300) // interval):
        time.sleep(interval)
        result = api_request(
            client, "POST", "/v1/accounts/oauth/device-verify",
            json_data={"device_code": data["device_code"]},
        )

        if result["status"] == "complete":
            from ..main import get_state
            emit({"status": "connected", "platform": platform}, human=get_state().human)
            return
        elif result["status"] == "expired":
            emit_error("auth_expired", "Authorization expired. Please try again.")

    typer.echo("Timed out waiting for authorization.", err=True)
    sys.exit(1)


@app.command("list")
@handle_errors
def list_accounts() -> None:
    """List all connected platform accounts."""
    client = _get_client()
    data = api_request(client, "GET", "/v1/accounts/connections")

    from ..main import get_state
    connections = data.get("connections", [])
    if get_state().human:
        if not connections:
            typer.echo("No connected accounts.")
            return
        for c in connections:
            status = "active" if c.get("is_active") else "inactive"
            typer.echo(f"  {c['platform']:12s} {c.get('account_name', 'N/A'):20s} [{status}]  {c['id']}")
    else:
        emit(data, human=False)


@app.command()
@handle_errors
def disconnect(
    connection_id: str = typer.Argument(..., help="Connection UUID to disconnect"),
) -> None:
    """Disconnect a platform account."""
    client = _get_client()
    api_request(client, "DELETE", f"/v1/accounts/connections/{connection_id}")

    from ..main import get_state
    emit({"status": "disconnected", "connection_id": connection_id}, human=get_state().human)
