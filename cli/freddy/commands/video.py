"""Video commands — analyze."""

import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session

app = typer.Typer(help="Video analysis commands.", no_args_is_help=True)


@app.command()
@handle_errors
def analyze(
    platform: str = typer.Option(..., "--platform", help="Platform: tiktok, instagram, youtube"),
    video_id: str = typer.Option(..., "--id", help="Video ID"),
    include: str = typer.Option(None, "--include", help="Comma-separated extras: brands,demographics"),
) -> None:
    """Analyze a video with optional brand/demographic analysis."""
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")

    client = make_client(config)

    payload: dict = {"platform": platform, "video_id": video_id}
    if include:
        payload["include"] = [x.strip() for x in include.split(",")]

    start_time = time.monotonic()
    result = api_request(client, "POST", "/v1/analyze/videos", json_data=payload)
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "video.analyze",
            input_summary={"platform": platform, "video_id": video_id},
            output_summary={"status": "ok"},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
