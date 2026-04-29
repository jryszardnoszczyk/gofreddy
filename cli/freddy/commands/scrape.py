"""Scrape command — fetch page content and extract text via REST API.

Data-only tool for autoresearch sessions. No LLM calls.
"""

import json
import time
from urllib.parse import urlparse

import typer

from ..api import api_request, handle_errors, log_action_to_session, make_client
from ..config import load_config
from ..output import emit, emit_error
from ..session import get_active_session
from cli.freddy.fixture.cache_integration import try_read_cache

# See cli/freddy/commands/detect.py for the rationale behind this list.
_PLAINTEXT_PORTS = frozenset({21, 23, 25, 80, 110, 143})


@handle_errors
def scrape_command(
    url: str = typer.Argument(..., help="URL to scrape"),
) -> None:
    """Fetch page content and extract text as JSON."""
    try:
        parsed = urlparse(url)
    except ValueError:
        emit_error("invalid_url", "URL validation failed")
    if parsed.scheme == "https" and parsed.port in _PLAINTEXT_PORTS:
        emit_error("invalid_url", "URL validation failed")

    cached = try_read_cache("freddy-scrape", "page", url)
    if cached is not None:
        typer.echo(json.dumps(cached))
        return
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        return

    client = make_client(config)

    start_time = time.monotonic()
    result = api_request(client, "POST", "/v1/geo/scrape", json_data={"url": url})
    duration_ms = int((time.monotonic() - start_time) * 1000)

    session = get_active_session()
    if session:
        log_action_to_session(
            client, session.session_id, "scrape",
            input_summary={"url": url},
            output_summary={"word_count": result.get("word_count", 0)},
            duration_ms=duration_ms,
        )

    from ..main import get_state
    emit(result, human=get_state().human)
