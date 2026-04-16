"""Detect command — run GEO infrastructure + SEO technical checks via REST API.

Data-only tool for autoresearch sessions. No LLM calls.
Basic mode: free (DOM/HTTP checks only).
--full mode: adds DataForSEO technical audit + PageSpeed Core Web Vitals.
"""

import time

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session


@handle_errors
def detect_command(
    url: str = typer.Argument(..., help="URL to check"),
    full: bool = typer.Option(False, "--full", help="Include DataForSEO + PageSpeed (paid)"),
) -> None:
    """Run GEO + SEO infrastructure checks on a page."""
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        return

    client = make_client(config)

    start_time = time.monotonic()
    result = api_request(client, "POST", "/v1/geo/detect", json_data={
        "url": url,
        "full": full,
    })
    duration_ms = int((time.monotonic() - start_time) * 1000)

    factors = len(result.get("geo_infrastructure", {})) + len(result.get("seo_technical", {}))

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "detect",
            input_summary={"url": url, "full": full},
            output_summary={"factors_checked": factors},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
