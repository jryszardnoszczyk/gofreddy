"""Creator commands — search, profile, fraud."""

import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session

app = typer.Typer(help="Creator research commands.", no_args_is_help=True)


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


def _maybe_log_action(client, tool_name: str, input_data: dict, result: dict, duration_ms: int) -> None:
    """Log action if session is active. Non-fatal."""
    session = get_active_session()
    if session:
        # Truncate output for logging
        output_summary = {"status": "ok"}
        if "data" in result:
            output_summary["count"] = len(result["data"]) if isinstance(result["data"], list) else 1
        log_action_to_session(
            client, session.session_id, tool_name,
            input_summary=input_data, output_summary=output_summary, duration_ms=duration_ms,
        )


@app.command()
@handle_errors
def search(
    platform: str = typer.Option(..., "--platform", help="Platform: tiktok, instagram, youtube"),
    query: str = typer.Option(None, "--query", help="Search query"),
    min_followers: int = typer.Option(None, "--min-followers", help="Minimum follower count"),
) -> None:
    """Search for creators on a platform."""
    config = _require_config()
    client = make_client(config)

    params: dict = {"platform": platform}
    if query:
        params["query"] = query
    if min_followers is not None:
        params["min_followers"] = min_followers

    start_time = time.monotonic()
    result = api_request(client, "GET", "/v1/search", params=params)
    duration_ms = int((time.monotonic() - start_time) * 1000)

    _maybe_log_action(client, "creator.search", {"platform": platform, "query": query}, result, duration_ms)

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def profile(
    platform: str = typer.Option(..., "--platform", help="Platform: tiktok, instagram, youtube"),
    username: str = typer.Option(..., "--username", help="Creator username"),
) -> None:
    """Get creator profile details."""
    config = _require_config()
    client = make_client(config)

    start_time = time.monotonic()
    result = api_request(client, "GET", f"/v1/creators/{platform}/{username}")
    duration_ms = int((time.monotonic() - start_time) * 1000)

    _maybe_log_action(client, "creator.profile", {"platform": platform, "username": username}, result, duration_ms)

    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def fraud(
    platform: str = typer.Option(..., "--platform", help="Platform: tiktok, instagram, youtube"),
    username: str = typer.Option(..., "--username", help="Creator username"),
) -> None:
    """Run fraud analysis on a creator."""
    config = _require_config()
    client = make_client(config)

    start_time = time.monotonic()
    result = api_request(client, "POST", f"/v1/fraud/analyze", json_data={"platform": platform, "username": username})
    duration_ms = int((time.monotonic() - start_time) * 1000)

    _maybe_log_action(client, "creator.fraud", {"platform": platform, "username": username}, result, duration_ms)

    from ..main import get_state
    emit(result, human=get_state().human)
