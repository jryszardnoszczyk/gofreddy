"""Content generation CLI commands — create drafts from digests and reports."""

from __future__ import annotations

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Content generation commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command("from-digest")
@handle_errors
def from_digest(
    monitor_id: str = typer.Option(..., "--monitor-id", help="Monitor UUID"),
    platforms: str = typer.Option(..., "--platforms", help="Comma-separated platforms (e.g. linkedin,x)"),
    draft_only: bool = typer.Option(True, "--draft-only/--publish", help="Create as draft only"),
) -> None:
    """Generate content from a monitoring digest."""
    client = _get_client()
    result = api_request(
        client, "POST", "/v1/content/generate",
        json_data={
            "action": "synthesize",
            "source": "monitoring",
            "monitor_id": monitor_id,
            "platforms": [p.strip() for p in platforms.split(",")],
            "draft_only": draft_only,
        },
    )
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command("from-report")
@handle_errors
def from_report(
    session_dir: str = typer.Option(..., "--session-dir", help="Path to session directory"),
    report_type: str = typer.Option(..., "--type", help="Report type (e.g. seo_recommendations)"),
    draft_only: bool = typer.Option(True, "--draft-only/--publish", help="Create as draft only"),
) -> None:
    """Generate content from a research report."""
    client = _get_client()
    result = api_request(
        client, "POST", "/v1/content/generate",
        json_data={
            "action": "synthesize",
            "source": "report",
            "session_dir": session_dir,
            "report_type": report_type,
            "draft_only": draft_only,
        },
    )
    from ..main import get_state
    emit(result, human=get_state().human)
