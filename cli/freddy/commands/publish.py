"""Publishing CLI commands — queue management, labels, thumbnails."""

from __future__ import annotations

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Publishing management commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command("list")
@handle_errors
def list_drafts(
    status: str = typer.Option(None, "--status", help="Filter: draft|scheduled|published|failed"),
    tag: str = typer.Option(None, "--tag", help="Filter by label"),
    limit: int = typer.Option(20, "--limit", help="Max results"),
) -> None:
    """List publish queue items."""
    client = _get_client()
    result = api_request(client, "GET", "/v1/publish/queue", params={"status": status, "tag": tag, "limit": limit})
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def approve(
    draft_id: str = typer.Argument(..., help="Draft UUID"),
) -> None:
    """Approve a draft for publishing."""
    client = _get_client()
    result = api_request(client, "POST", f"/v1/publish/drafts/{draft_id}/approve")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def schedule(
    draft_id: str = typer.Argument(..., help="Draft UUID"),
    at: str = typer.Option(..., "--at", help="ISO datetime (e.g. 2026-04-15T10:00:00)"),
) -> None:
    """Schedule a draft for future publishing."""
    from datetime import datetime as dt
    try:
        dt.fromisoformat(at)
    except ValueError:
        emit_error("invalid_input", "Invalid datetime. Use ISO format (e.g., 2026-04-15T10:00:00)")
    client = _get_client()
    result = api_request(client, "POST", f"/v1/publish/drafts/{draft_id}/schedule", json_data={"scheduled_at": at})
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def dispatch() -> None:
    """Dispatch all scheduled items ready for publishing."""
    client = _get_client()
    result = api_request(client, "POST", "/v1/publish/dispatch")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def delete(
    draft_id: str = typer.Argument(..., help="Draft UUID"),
) -> None:
    """Delete a draft from the publish queue."""
    client = _get_client()
    api_request(client, "DELETE", f"/v1/publish/drafts/{draft_id}")
    from ..main import get_state
    emit({"status": "deleted", "draft_id": draft_id}, human=get_state().human)


@app.command()
@handle_errors
def tag(
    draft_id: str = typer.Argument(..., help="Draft UUID"),
    add: list[str] = typer.Option([], "--add", help="Labels to add"),
    remove: list[str] = typer.Option([], "--remove", help="Labels to remove"),
) -> None:
    """Add or remove labels on a publish draft."""
    if not add and not remove:
        emit_error("invalid_input", "Provide --add or --remove labels.")

    client = _get_client()

    if add:
        api_request(
            client, "POST", f"/v1/publish/drafts/{draft_id}/labels",
            json_data={"add": add},
        )

    if remove:
        api_request(
            client, "POST", f"/v1/publish/drafts/{draft_id}/labels",
            json_data={"remove": remove},
        )

    from ..main import get_state
    emit(
        {"status": "ok", "draft_id": draft_id, "added": add, "removed": remove},
        human=get_state().human,
    )


@app.command("set-thumbnail")
@handle_errors
def set_thumbnail(
    draft_id: str = typer.Argument(..., help="Draft UUID"),
    url: str = typer.Option(None, "--url", help="Thumbnail URL"),
) -> None:
    """Set custom thumbnail for a video draft."""
    if not url:
        emit_error("invalid_input", "Provide --url for thumbnail.")

    client = _get_client()
    api_request(
        client, "PATCH", f"/v1/publish/drafts/{draft_id}",
        json_data={"thumbnail_url": url},
    )

    from ..main import get_state
    emit(
        {"status": "ok", "draft_id": draft_id, "thumbnail_url": url},
        human=get_state().human,
    )
