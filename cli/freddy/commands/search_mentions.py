"""Search mentions — FTS + filtered query."""

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
def search(
    monitor_id: str = typer.Argument(..., help="Monitor UUID"),
    query: str = typer.Argument(..., help="Full-text search query"),
    source: str = typer.Option(None, "--source", help="Filter by source (e.g. reddit, twitter)"),
    sentiment: str = typer.Option(None, "--sentiment", help="positive|negative|neutral|mixed"),
    intent: str = typer.Option(None, "--intent", help="complaint|question|recommendation|purchase_signal|general_discussion"),
    date_from: str = typer.Option(None, "--date-from", help="Start date (YYYY-MM-DD)"),
    date_to: str = typer.Option(None, "--date-to", help="End date (YYYY-MM-DD)"),
) -> None:
    """Search mentions with FTS + filters. Wraps query_mentions()."""
    config = _require_config()
    client = make_client(config)

    params: dict = {
        "q": query,
        "source": source,
        "sentiment": sentiment,
        "intent": intent,
        "date_from": date_from,
        "date_to": date_to,
        "limit": 50,
    }
    result = api_request(client, "GET", f"/v1/monitors/{monitor_id}/mentions", params=params)

    # Canonicalize to {"mentions", "total"} — same shape as `freddy monitor mentions`.
    items = result.get("mentions", result.get("data", []))
    total = result.get("total", len(items))

    from ..main import get_state
    emit({"mentions": items, "total": total}, human=get_state().human)
