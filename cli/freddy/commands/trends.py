"""Trends — Google Trends correlation."""

import json

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error
from cli.freddy.fixture.cache_integration import try_read_cache


_VALID_WINDOWS = {"7d", "14d", "30d", "90d"}


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@handle_errors
def trends(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    window: str = typer.Option("30d", "--window", help="Lookback window: 7d|14d|30d|90d"),
) -> None:
    """Fetch Google Trends correlation for a monitor."""
    if window not in _VALID_WINDOWS:
        emit_error(
            "invalid_window",
            f"Must be one of: {', '.join(sorted(_VALID_WINDOWS))}",
        )
        return
    window_days = int(window[:-1])

    cached = try_read_cache(
        "freddy-trends", "correlation", monitor_id, shape_flags={"window": window},
    )
    if cached is not None:
        typer.echo(json.dumps(cached))
        return

    config = _require_config()
    client = make_client(config)

    params: dict = {"window_days": window_days}
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/trends-correlation", params=params)

    from ..main import get_state
    emit(result, human=get_state().human)
