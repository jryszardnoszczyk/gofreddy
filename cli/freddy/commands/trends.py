"""Trends — Google Trends correlation."""

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@handle_errors
def trends(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    window: str = typer.Option("30d", "--window", help="Lookback window (e.g. 7d, 14d, 30d, 90d)"),
) -> None:
    """Fetch Google Trends correlation for a monitor."""
    config = _require_config()
    client = make_client(config)

    # Convert window string to days
    window_days = int(window.rstrip("d")) if window.endswith("d") else 30
    params: dict = {"window_days": window_days}
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/trends-correlation", params=params)

    from ..main import get_state
    emit(result, human=get_state().human)
