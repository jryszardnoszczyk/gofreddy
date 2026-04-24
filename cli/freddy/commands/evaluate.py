"""Evaluate content quality — thin HTTP clients to the judge services.

All model-call logic lives inside the judge services (``judges/``); this
module only marshals arguments, POSTs to the role-locked judge-service
URL with a bearer token, and echoes the raw response body.

Subcommands:
  review   → ``POST {SESSION_JUDGE_URL}/invoke/review`` (session judge)
  critique → ``POST {SESSION_JUDGE_URL}/invoke/critique`` (session judge)
  variant  → ``POST {EVOLUTION_JUDGE_URL}/invoke/score`` (evolution judge)

Environment:
  SESSION_JUDGE_URL        — defaults to ``http://localhost:7100``
  SESSION_INVOKE_TOKEN     — bearer token; scrubbed for session judge
  EVOLUTION_JUDGE_URL      — defaults to ``http://localhost:7200``
  EVOLUTION_INVOKE_TOKEN   — bearer token; scrubbed for evolution judge

No API keys. No prompts. No file-reading. If the judge service is
unreachable, the subcommand exits non-zero and echoes an error JSON —
callers are expected to surface the failure, not retry.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import typer

from ..output import emit_error

app = typer.Typer(help="Evaluate content quality (thin HTTP clients to judge services).", no_args_is_help=True)


def _session_url() -> str:
    return os.environ.get("SESSION_JUDGE_URL", "http://localhost:7100")


def _evolution_url() -> str:
    return os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")


def _session_token() -> str:
    return os.environ.get("SESSION_INVOKE_TOKEN", "")


def _evolution_token() -> str:
    return os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


def _post(url: str, token: str, payload: dict, *, timeout: float) -> None:
    """POST JSON with bearer token, echo response body, exit non-zero on error."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    except httpx.TimeoutException:
        emit_error("judge_timeout", f"judge service timeout: {url}")
    except httpx.HTTPError as exc:
        emit_error("judge_unreachable", f"judge service unreachable: {exc}")

    if response.status_code >= 400:
        body = response.text.strip()
        suffix = f": {body}" if body else ""
        emit_error(
            "judge_error",
            f"judge service returned {response.status_code}{suffix}",
        )

    typer.echo(response.text)


@app.command("review")
def review_command(
    session_dir: str = typer.Argument(..., help="Session directory the judge should read"),
) -> None:
    """Adversarial review; session-judge loads artifacts from ``session_dir``."""
    payload = {"session_dir": session_dir}
    _post(f"{_session_url()}/invoke/review", _session_token(), payload, timeout=300.0)


@app.command("critique")
def critique_command(
    request_file: str = typer.Argument(..., help="Path to critique request JSON, or '-' for stdin"),
) -> None:
    """Trusted session-time critique; payload loaded from ``request_file``."""
    try:
        if request_file == "-":
            payload = json.loads(sys.stdin.read())
        else:
            payload = json.loads(Path(request_file).read_text())
    except FileNotFoundError:
        emit_error("request_file_not_found", f"Request file not found: {request_file}")
    except json.JSONDecodeError as exc:
        emit_error("invalid_json", f"Critique request is not valid JSON: {exc}")
    _post(f"{_session_url()}/invoke/critique", _session_token(), payload, timeout=300.0)


@app.command("variant")
def variant_command(
    domain: str = typer.Argument(..., help="Domain: geo, competitive, monitoring, storyboard"),
    session_dir: str = typer.Argument(..., help="Session directory with outputs"),
    campaign_id: str = typer.Option(None, "--campaign-id", help="Evolution campaign ID"),
    variant_id: str = typer.Option(None, "--variant-id", help="Variant ID for tracking"),
) -> None:
    """Variant scoring via evolution-judge service.

    The judge-service reads artifacts from ``session_dir`` itself; the
    autoresearch side posts only the reference.
    """
    payload: dict = {"domain": domain, "session_dir": session_dir}
    if campaign_id is not None:
        payload["campaign_id"] = campaign_id
    if variant_id is not None:
        payload["variant_id"] = variant_id
    _post(f"{_evolution_url()}/invoke/score", _evolution_token(), payload, timeout=400.0)
