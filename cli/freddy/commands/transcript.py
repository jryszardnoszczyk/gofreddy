"""Transcript commands — upload (hook-only infrastructure command)."""

import json
import os
import sys

import httpx
import typer

from ..config import load_config
from ..session import get_active_session

app = typer.Typer(help="Transcript management (infrastructure).", no_args_is_help=True)

_MAX_TRANSCRIPT_BYTES = 15 * 1024 * 1024  # 15MB — matches server limit


@app.command()
def upload(
    from_hook: bool = typer.Option(False, "--from-hook", help="Read hook payload from stdin"),
) -> None:
    """Upload session transcript. Designed for SessionEnd hook use.

    Reads JSON from stdin with transcript_path and optional session_id.
    Non-fatal — always exits 0.
    """
    if not from_hook:
        print(json.dumps({"error": {"code": "missing_flag", "message": "Use --from-hook (hook infrastructure only)"}}))
        raise SystemExit(0)

    try:
        _upload_from_hook()
    except Exception:
        # Non-fatal — never let transcript upload break anything
        raise SystemExit(0)


def _upload_from_hook() -> None:
    """Process hook payload and upload transcript."""
    # Read hook payload from stdin
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        payload = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path or not os.path.isfile(transcript_path):
        return

    # Check file size guard
    file_size = os.path.getsize(transcript_path)
    if file_size > _MAX_TRANSCRIPT_BYTES:
        _warn(f"Transcript too large: {file_size} bytes (max {_MAX_TRANSCRIPT_BYTES})")
        return

    # Determine session ID — from payload or local state
    session_id = payload.get("session_id", "")
    if not session_id:
        session = get_active_session()
        if not session:
            return
        session_id = session.session_id

    # Load config
    config = load_config()
    if not config:
        return

    # Read and upload transcript
    with open(transcript_path, "rb") as f:
        transcript_data = f.read()

    try:
        client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            headers={
                "X-API-Key": config.api_key,
                "Content-Type": "text/plain",
                "User-Agent": "freddy-cli/0.1",
            },
            timeout=httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0),
            follow_redirects=False,
        )
        resp = client.post(f"/v1/sessions/{session_id}/transcript", content=transcript_data)
        if resp.status_code < 400:
            _warn(f"Transcript uploaded: {file_size} bytes")
    except httpx.HTTPError:
        pass  # Non-fatal


def _warn(message: str) -> None:
    json.dump({"info": message}, sys.stderr)
    sys.stderr.write("\n")
