"""Search competitor ads via REST API.

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
def search_ads_command(
    domain: str = typer.Argument(..., help="Competitor domain to search"),
    limit: int = typer.Option(50, "--limit", help="Max ads to return"),
) -> None:
    """Search competitor ads via Foreplay + Adyntel."""
    cached = try_read_cache("foreplay", "ads", domain)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        return

    client = make_client(config)

    start_time = time.monotonic()
    result = api_request(client, "POST", "/v1/competitive/ads/search", json_data={
        "domain": domain,
        "limit": limit,
    })
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "search_ads",
            input_summary={"domain": domain, "limit": limit},
            output_summary={"ad_count": result.get("ad_count", 0)},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
