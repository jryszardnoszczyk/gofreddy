"""Iteration commands — push iteration data to session tracking."""

import json
import os
import sys

import httpx
import typer

from ..config import load_config
from ..session import get_active_session

app = typer.Typer(help="Iteration tracking for autoresearch sessions.", no_args_is_help=True)

_LOG_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)

_VALID_ITERATION_STATUSES = {"success", "timeout", "failed"}
_VALID_ITERATION_TYPES = {
    "DISCOVER",
    "COMPETITIVE",
    "SEO_BASELINE",
    "OPTIMIZE",
    "REFINE",
    "ANALYZE",
    "SYNTHESIZE",
    "VERIFY",
    "REPORT",
    "COMPLETE",
}


@app.command()
def push(
    session_id: str = typer.Option(None, "--session-id", help="Session ID (falls back to active session)"),
    number: str = typer.Option(..., "--number", help="Iteration number (1-based)"),
    iteration_type: str = typer.Option("DISCOVER", "--type", help=f"Iteration type. One of: {', '.join(sorted(_VALID_ITERATION_TYPES))}"),
    status: str = typer.Option("success", "--status", help=f"Iteration status. One of: {', '.join(sorted(_VALID_ITERATION_STATUSES))}"),
    exit_code: str = typer.Option(None, "--exit-code", help="Process exit code"),
    duration_ms: str = typer.Option(None, "--duration-ms", help="Duration in milliseconds"),
    state_file: str = typer.Option(None, "--state-file", help="Path to session.md state file"),
    result: str = typer.Option(None, "--result", help="JSON string for result_entry"),
    log_file: str = typer.Option(None, "--log-file", help="Path to iteration log file"),
) -> None:
    """Push iteration data to the tracking API. Non-fatal — exits 0 on any error."""
    # Honor the "exits 0 on any error" contract: pre-flight validation must
    # report the user error to stderr but still exit 0 so launcher hooks
    # never halt on a typo. Integer flags are declared as str so that a
    # malformed value (empty string, "abc", unset env-var expansion) is parsed
    # here instead of being rejected by Typer's argument parser with exit 2.
    # Same pattern as transcript.upload's missing-flag branch
    # (cli/freddy/commands/transcript.py).
    number_int = _parse_int_or_exit("number", number, allow_none=False)
    exit_code_int = _parse_int_or_exit("exit_code", exit_code, allow_none=True)
    duration_ms_int = _parse_int_or_exit("duration_ms", duration_ms, allow_none=True)
    if iteration_type not in _VALID_ITERATION_TYPES:
        json.dump(
            {"error": {"code": "invalid_type",
                       "message": f"Must be one of: {', '.join(sorted(_VALID_ITERATION_TYPES))}"}},
            sys.stderr,
        )
        sys.stderr.write("\n")
        raise SystemExit(0)
    if status not in _VALID_ITERATION_STATUSES:
        json.dump(
            {"error": {"code": "invalid_status",
                       "message": f"Must be one of: {', '.join(sorted(_VALID_ITERATION_STATUSES))}"}},
            sys.stderr,
        )
        sys.stderr.write("\n")
        raise SystemExit(0)
    try:
        _push_iteration(
            session_id=session_id,
            number=number_int,
            iteration_type=iteration_type,
            status=status,
            exit_code=exit_code_int,
            duration_ms=duration_ms_int,
            state_file=state_file,
            result=result,
            log_file=log_file,
        )
    except Exception:
        # Non-fatal — never let iteration tracking break the launcher
        raise SystemExit(0)


def _parse_int_or_exit(field: str, raw: str | None, *, allow_none: bool) -> int | None:
    """Parse an int flag in-body so a malformed value reports + exits 0
    instead of triggering Typer's exit-2 argument-parser banner."""
    if raw is None or (allow_none and raw == ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        json.dump(
            {"error": {"code": f"invalid_{field}",
                       "message": f"--{field.replace('_', '-')} must be an integer"}},
            sys.stderr,
        )
        sys.stderr.write("\n")
        raise SystemExit(0)


def _push_iteration(
    *,
    session_id: str | None,
    number: int,
    iteration_type: str,
    status: str,
    exit_code: int | None,
    duration_ms: int | None,
    state_file: str | None,
    result: str | None,
    log_file: str | None,
) -> None:
    """Build payload and POST to /v1/sessions/{id}/iterations."""
    # Resolve session ID: explicit arg > env var > shared file
    if not session_id:
        session_id = os.environ.get("FREDDY_SESSION_ID")
    if not session_id:
        active = get_active_session()
        if not active:
            _warn("No session ID provided and no active session")
            return
        session_id = active.session_id

    # Load config
    config = load_config()
    if not config:
        _warn("No API key configured")
        return

    # Build payload
    payload: dict = {
        "iteration_number": number,
        "iteration_type": iteration_type,
        "status": status,
    }
    if exit_code is not None:
        payload["exit_code"] = exit_code
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms

    # Read state snapshot from file
    if state_file and os.path.isfile(state_file):
        try:
            with open(state_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2_000_000)  # Max 2MB (uploaded to R2)
            payload["state_snapshot"] = content
        except OSError:
            pass

    # Parse result JSON
    if result:
        try:
            payload["result_entry"] = json.loads(result)
        except json.JSONDecodeError:
            _warn("Invalid JSON in --result, skipping")

    # Read log output from file
    if log_file and os.path.isfile(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(5_000_000)  # Max 5MB (uploaded to R2)
            payload["log_output"] = content
        except OSError:
            pass

    # POST to API
    try:
        client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            headers={
                "X-API-Key": config.api_key,
                "Content-Type": "application/json",
                "User-Agent": "freddy-cli/0.1",
            },
            timeout=_LOG_TIMEOUT,
            follow_redirects=False,
        )
        resp = client.post(
            f"/v1/sessions/{session_id}/iterations",
            json=payload,
        )
        if resp.status_code < 400:
            _warn(f"Iteration {number} logged ({iteration_type}, {status})")
        else:
            _warn(f"Iteration logging failed: HTTP {resp.status_code}")
    except httpx.HTTPError as exc:
        _warn(f"Iteration logging failed: {type(exc).__name__}")


def _warn(message: str) -> None:
    json.dump({"info": message}, sys.stderr)
    sys.stderr.write("\n")
