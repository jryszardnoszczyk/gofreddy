"""Content commands — search."""

import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session

app = typer.Typer(help="Content search commands.", no_args_is_help=True)


@app.command()
@handle_errors
def search(
    platform: str = typer.Option(..., "--platform", help="Platform: tiktok, instagram, youtube"),
    query: str = typer.Option(..., "--query", help="Search query"),
) -> None:
    """Search for content on a platform."""
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")

    client = make_client(config)

    params = {"platform": platform, "query": query}

    start_time = time.monotonic()
    result = api_request(client, "GET", "/v1/search", params=params)
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "content.search",
            input_summary={"platform": platform, "query": query},
            output_summary={"status": "ok", "count": len(result.get("results", []))},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
