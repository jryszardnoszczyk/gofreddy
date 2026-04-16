"""Calendar CLI commands — view scheduled content."""

from __future__ import annotations

import calendar as cal
from datetime import datetime

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Content calendar commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def view(
    month: str = typer.Option(None, "--month", help="Month to view (YYYY-MM, default: current)"),
) -> None:
    """View scheduled content for a given month."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    try:
        dt = datetime.strptime(month, "%Y-%m")
    except ValueError:
        emit_error("invalid_input", "Invalid month format. Use YYYY-MM (e.g., 2026-04)")
        return  # unreachable — emit_error raises SystemExit

    last_day = cal.monthrange(dt.year, dt.month)[1]
    scheduled_after = f"{month}-01T00:00:00Z"
    scheduled_before = f"{month}-{last_day:02d}T23:59:59Z"

    client = _get_client()
    result = api_request(
        client, "GET", "/v1/publish/queue",
        params={
            "status": "scheduled",
            "scheduled_after": scheduled_after,
            "scheduled_before": scheduled_before,
            "limit": 100,
        },
    )
    from ..main import get_state
    emit(result, human=get_state().human)
