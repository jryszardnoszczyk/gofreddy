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
    # Sibling --sentiment / --intent / --source enum filters return
    # validation_error from the API on bogus input. The FTS `q` query param
    # has no min_length on the API side, so an empty positional argument
    # silently produces an empty result set instead of the same validation
    # envelope — reject pre-flight to match the siblings.
    if not query:
        emit_error(
            "validation_error",
            "Request validation failed: query.q: String should have at least 1 character",
        )
    # date_from > date_to is a no-op SQL filter (zero rows). API doesn't
    # enforce the range invariant, so reject pre-flight to match the
    # validation_error contract used by the enum filters.
    if date_from and date_to and date_from > date_to:
        emit_error(
            "validation_error",
            "Request validation failed: query.date_to: Must be on or after date_from",
        )

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
