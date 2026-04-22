"""Competitive intelligence CLI commands — briefs and analysis."""

from __future__ import annotations

import httpx
import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Competitive intelligence commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def brief(
    domain: str = typer.Option(..., "--domain", help="Competitor domain to analyze"),
) -> None:
    """Generate a competitive intelligence brief."""
    client = _get_client()
    client.timeout = httpx.Timeout(connect=5.0, read=120.0, write=5.0, pool=5.0)
    result = api_request(
        client, "POST", "/v1/competitive/ads/search",
        json_data={"domain": domain},
    )
    from ..main import get_state
    emit(result, human=get_state().human)
