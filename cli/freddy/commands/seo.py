"""SEO CLI commands — keyword discovery and page optimization."""

from __future__ import annotations

import httpx
import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="SEO analysis commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def keywords(
    seed: str = typer.Option(..., "--seed", help="Seed keyword for discovery"),
    location: str = typer.Option(None, "--location", help="Location code (default: US)"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
) -> None:
    """Discover related keywords from a seed keyword."""
    client = _get_client()
    body: dict = {"seed_keyword": seed, "limit": limit}
    if location:
        body["location_code"] = location
    result = api_request(client, "POST", "/v1/geo/keywords", json_data=body)
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def optimize(
    url: str = typer.Option(..., "--url", help="Page URL to optimize"),
    query: str = typer.Option(..., "--query", help="Target search query"),
) -> None:
    """Get SEO optimization recommendations for a page."""
    client = _get_client()
    client.timeout = httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)
    result = api_request(
        client, "POST", "/v1/geo/audit",
        json_data={"action": "optimize", "url": url, "query": query, "keywords": [query]},
    )
    from ..main import get_state
    emit(result, human=get_state().human)
