"""Analytics — own-account performance and engagement prediction."""

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Own-account analytics and engagement prediction.")


def _require_config():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
    return config


@app.command()
@handle_errors
def sync(
    platform: str = typer.Argument(..., help="Platform: twitter, instagram, tiktok, youtube"),
    username: str = typer.Argument(..., help="Account username"),
) -> None:
    """Trigger post sync + snapshot for an account."""
    config = _require_config()
    client = make_client(config)
    result = api_request(client, "POST", f"/v1/analytics/{platform}/{username}/sync")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def dashboard(
    platform: str = typer.Argument(..., help="Platform: twitter, instagram, tiktok, youtube"),
    username: str = typer.Argument(..., help="Account username"),
) -> None:
    """Show own-account performance dashboard."""
    config = _require_config()
    client = make_client(config)
    result = api_request(client, "GET", f"/v1/analytics/{platform}/{username}/dashboard")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def heatmap(
    platform: str = typer.Argument(..., help="Platform: twitter, instagram, tiktok, youtube"),
    username: str = typer.Argument(..., help="Account username"),
) -> None:
    """Show posting time heatmap."""
    config = _require_config()
    client = make_client(config)
    result = api_request(client, "GET", f"/v1/analytics/{platform}/{username}/heatmap")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def patterns(
    platform: str = typer.Argument(..., help="Platform: twitter, instagram, tiktok, youtube"),
    username: str = typer.Argument(..., help="Account username"),
    recompute: bool = typer.Option(False, "--recompute", help="Force recomputation from fresh data"),
) -> None:
    """Show or recompute performance patterns."""
    config = _require_config()
    client = make_client(config)
    if recompute:
        result = api_request(client, "POST", f"/v1/analytics/{platform}/{username}/patterns/recompute")
    else:
        result = api_request(client, "GET", f"/v1/analytics/{platform}/{username}/patterns")
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def predict(
    platform: str = typer.Option(..., "--platform", "-p", help="Platform"),
    username: str = typer.Option(..., "--username", "-u", help="Account username"),
    content: str = typer.Option(..., "--content", "-c", help="Draft post content"),
    hour: int = typer.Option(12, "--hour", help="Posting hour (0-23)"),
    day: int = typer.Option(0, "--day", help="Posting day (0=Mon, 6=Sun)"),
    media_type: str = typer.Option("text", "--media-type", help="Media type"),
) -> None:
    """Predict engagement for a draft post."""
    config = _require_config()
    client = make_client(config)
    body = {
        "platform": platform,
        "username": username,
        "content": content,
        "posting_hour": hour,
        "posting_day": day,
        "media_type": media_type,
        "hashtag_count": content.count("#"),
    }
    result = api_request(client, "POST", "/v1/analytics/predict-engagement", json_data=body)
    from ..main import get_state
    emit(result, human=get_state().human)
