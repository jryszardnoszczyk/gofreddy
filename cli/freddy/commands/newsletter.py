"""Newsletter CLI commands — subscriber management and sending."""

from __future__ import annotations

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Newsletter management commands.", no_args_is_help=True)


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def subscribe(
    email: str = typer.Option(..., "--email", help="Subscriber email"),
    name: str = typer.Option(..., "--name", help="Subscriber name"),
    segment: str = typer.Option(None, "--segment", help="Subscriber segment"),
) -> None:
    """Add a newsletter subscriber."""
    client = _get_client()
    result = api_request(
        client, "POST", "/v1/newsletters/subscribe",
        json_data={"email": email, "name": name, "segment": segment},
    )
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def send(
    segment: str = typer.Option(None, "--segment", help="Target segment"),
    subject: str = typer.Option(None, "--subject", help="Email subject"),
    html_file: str = typer.Option(None, "--html-file", help="Path to HTML body file"),
    from_digest: bool = typer.Option(False, "--from-digest", help="Generate from monitoring digest"),
    monitor_id: str = typer.Option(None, "--monitor-id", help="Monitor UUID (with --from-digest)"),
) -> None:
    """Send a newsletter. Use --segment/--subject/--html-file OR --from-digest/--monitor-id."""
    explicit = all(v is not None for v in [segment, subject, html_file])
    digest_mode = from_digest and monitor_id is not None

    if not explicit and not digest_mode:
        emit_error("invalid_input", "Provide either --segment/--subject/--html-file OR --from-digest/--monitor-id")

    if explicit and digest_mode:
        emit_error("invalid_input", "Provide either --segment/--subject/--html-file OR --from-digest/--monitor-id")

    client = _get_client()

    if digest_mode:
        body: dict = {"from_digest": True, "monitor_id": monitor_id}
    else:
        from pathlib import Path
        path = Path(html_file)  # type: ignore[arg-type]
        if not path.is_file():
            emit_error("invalid_input", f"HTML file not found: {html_file}")
        html_body = path.read_text()
        body = {"segment": segment, "subject": subject, "html_body": html_body}

    result = api_request(client, "POST", "/v1/newsletters/send", json_data=body)
    from ..main import get_state
    emit(result, human=get_state().human)
