"""Visibility command — query AI engine visibility via REST API.

Data-only tool for autoresearch sessions. No LLM calls.
"""

import json
import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session
from cli.freddy.fixture.cache_integration import try_read_cache


@handle_errors
def visibility_command(
    brand: str = typer.Option(..., "--brand", help="Brand name to check for mentions"),
    keywords: str = typer.Option(None, "--keywords", help="Comma-separated keywords"),
    country: str = typer.Option("US", "--country", help="ISO 3166-1 alpha-2 country code"),
) -> None:
    """Check brand visibility across AI search platforms."""
    cached = try_read_cache("freddy-visibility", "visibility", brand)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        return

    client = make_client(config)

    keyword_list = [kw.strip() for kw in keywords.split(",")] if keywords else []

    start_time = time.monotonic()
    result = api_request(client, "POST", "/v1/geo/visibility", json_data={
        "brand": brand,
        "keywords": keyword_list,
        "country": country,
    })
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        platform_count = result.get("platforms_checked", [])
        log_action_to_session(
            client, session.session_id, "visibility",
            input_summary={"brand": brand, "keywords": keyword_list},
            output_summary={"platforms": len(platform_count) if isinstance(platform_count, list) else 0},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
