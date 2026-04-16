"""Article CLI commands — generate, list, and track performance."""

from __future__ import annotations

import httpx
import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Article generation and tracking commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def generate(
    url: str = typer.Option(..., "--url", help="Source URL for article generation"),
    keywords: str = typer.Option(..., "--keywords", help="Comma-separated keywords"),
    language: str = typer.Option("en", "--language", help="Article language"),
) -> None:
    """Generate an article from a source URL."""
    client = _get_client()
    client.timeout = httpx.Timeout(connect=5.0, read=120.0, write=5.0, pool=5.0)
    result = api_request(
        client, "POST", "/v1/articles/generate",
        json_data={
            "source_url": url,
            "keywords": [k.strip() for k in keywords.split(",")],
            "language": language,
        },
    )
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command("list")
@handle_errors
def list_articles(
    limit: int = typer.Option(20, "--limit", help="Max results"),
) -> None:
    """List generated articles."""
    client = _get_client()
    result = api_request(client, "GET", "/v1/articles", params={"limit": limit})
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def performance(
    article_id: str = typer.Argument(..., help="Article UUID"),
) -> None:
    """Show performance metrics for an article."""
    client = _get_client()
    result = api_request(client, "GET", f"/v1/articles/{article_id}/performance")
    from ..main import get_state
    emit(result, human=get_state().human)
