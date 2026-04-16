"""Query monitoring analytics — SOV, sentiment via REST API.

Data-only tool for autoresearch sessions. No LLM calls.
"""

from __future__ import annotations

import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session

_VALID_METRICS = {"sov", "sentiment"}

_METRIC_ENDPOINTS = {
    "sov": "/v1/monitors/{monitor_id}/share-of-voice",
    "sentiment": "/v1/monitors/{monitor_id}/sentiment",
}

_VALID_WINDOWS = {"7d", "14d", "30d", "90d"}


@handle_errors
def query_monitor_command(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    metric: str = typer.Option("sov", "--metric", help="Metric: sov|sentiment"),
    window: str = typer.Option("7d", "--window", help="Time window: 7d|14d|30d|90d"),
) -> None:
    """Query monitoring analytics for a monitor."""
    if metric not in _VALID_METRICS:
        emit_error("invalid_metric", f"Must be one of: {', '.join(sorted(_VALID_METRICS))}")
        return

    if window not in _VALID_WINDOWS:
        emit_error("invalid_window", f"Must be one of: {', '.join(sorted(_VALID_WINDOWS))}")
        return

    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        return

    client = make_client(config)

    endpoint = _METRIC_ENDPOINTS[metric].format(monitor_id=monitor_id)

    start_time = time.monotonic()
    result = api_request(client, "GET", endpoint, params={"window": window})
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "query_monitor",
            input_summary={"monitor_id": monitor_id, "metric": metric, "window": window},
            output_summary={"status": "ok"},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
