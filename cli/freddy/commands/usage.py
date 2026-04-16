"""Usage commands — check."""

import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Usage and billing commands.", no_args_is_help=True)


@app.command()
@handle_errors
def check() -> None:
    """Check current usage and credit balance."""
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")

    client = make_client(config)
    result = api_request(client, "GET", "/v1/usage")

    from ..main import get_state
    emit(result, human=get_state().human)
