"""Media library CLI commands — upload, list, search, delete, get URL."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import httpx
import typer

from ..api import api_request, handle_errors, make_client
from ..config import load_config
from ..output import emit, emit_error

app = typer.Typer(help="Media asset management commands.", no_args_is_help=True)

_MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100MB


def _get_client():
    config = load_config()
    if not config:
        emit_error("not_authenticated", "No API key configured. Run: freddy auth login --api-key <key>")
        raise SystemExit(1)
    return make_client(config)


@app.command()
@handle_errors
def upload(
    file: str = typer.Argument(..., help="Path to file to upload"),
) -> None:
    """Upload a media asset."""
    path = Path(file)
    if not path.is_file():
        emit_error("invalid_input", f"File not found: {file}")

    if path.stat().st_size > _MAX_UPLOAD_BYTES:
        emit_error("invalid_input", "File exceeds 100MB limit")

    content_type = mimetypes.guess_type(file)[0] or "application/octet-stream"

    client = _get_client()
    client.timeout = httpx.Timeout(connect=5.0, read=30.0, write=60.0, pool=5.0)

    with open(file, "rb") as f:
        response = client.post(
            "/v1/media/upload",
            files={"file": (path.name, f, content_type)},
        )

    if response.status_code >= 400:
        try:
            body = response.json()
            error = body.get("error", body.get("detail", {}))
            if isinstance(error, dict):
                code = error.get("code", f"http_{response.status_code}")
                message = error.get("message", response.text)
            else:
                code = f"http_{response.status_code}"
                message = str(error)
        except (json.JSONDecodeError, ValueError):
            code = f"http_{response.status_code}"
            message = response.text
        emit_error(code, message)

    from ..main import get_state
    emit(response.json(), human=get_state().human)


@app.command("list")
@handle_errors
def list_assets(
    content_type: str = typer.Option(None, "--type", help="Filter by MIME type (e.g. image/png)"),
    limit: int = typer.Option(20, "--limit", help="Max results"),
) -> None:
    """List media assets."""
    client = _get_client()
    result = api_request(client, "GET", "/v1/media", params={"content_type": content_type, "limit": limit})
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def search(
    tag: str = typer.Option(..., "--tag", help="Tag to search for"),
) -> None:
    """Search media assets by tag."""
    client = _get_client()
    result = api_request(client, "GET", "/v1/media/search", params={"tag": tag})
    from ..main import get_state
    emit(result, human=get_state().human)


@app.command()
@handle_errors
def delete(
    asset_id: str = typer.Argument(..., help="Media asset UUID"),
) -> None:
    """Delete a media asset."""
    client = _get_client()
    api_request(client, "DELETE", f"/v1/media/{asset_id}")
    from ..main import get_state
    emit({"status": "deleted", "asset_id": asset_id}, human=get_state().human)


@app.command()
@handle_errors
def url(
    asset_id: str = typer.Argument(..., help="Media asset UUID"),
) -> None:
    """Get a download URL for a media asset."""
    client = _get_client()
    result = api_request(client, "GET", f"/v1/media/{asset_id}/url")
    from ..main import get_state
    emit(result, human=get_state().human)
