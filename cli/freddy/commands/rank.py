"""Rank tracking CLI commands — domain rank snapshots and history."""

from __future__ import annotations

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Domain rank tracking commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def snapshot(
    domain: str = typer.Option(None, "--domain", help="Domain to check (default: org primary)"),
) -> None:
    """Take a domain rank snapshot."""
    client = _get_client()
    body: dict = {}
    if domain:
        body["domain"] = domain
    result = api_request(client, "POST", "/v1/seo/rank/snapshot", json_data=body)
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def history(
    domain: str = typer.Option(None, "--domain", help="Domain (default: org primary)"),
    days: int = typer.Option(90, "--days", help="Lookback period in days"),
) -> None:
    """View domain rank history."""
    client = _get_client()
    result = api_request(client, "GET", "/v1/seo/rank/history", params={"domain": domain, "days": days})
    from ..main import get_state
    emit(result, human=get_state().human)
