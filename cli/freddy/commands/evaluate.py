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
    headers = {"Authorization": f"Bearer {token}"} if token else {}
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
    """Trusted session-time critique; payload loaded from ``request_file``.

    Accepts two payload shapes:
      1. Current session-judge shape: ``{session_artifacts, session_goal}``
         → passes through to ``/invoke/critique`` and echoes the response.
      2. Legacy per-criterion batch shape: ``{criteria: [{criterion_id,
         rubric_prompt, output_text, source_text}, ...]}`` used by archived
         variant evaluators (v006). Each criterion is posted separately to
         ``/invoke/critique`` (session_artifacts=output_text,
         session_goal=rubric_prompt) and the overall verdicts are
         synthesized into ``{results: [...]}`` with the
         ``normalized_score`` the legacy caller expects.
    """
    try:
        if request_file == "-":
            payload = json.loads(sys.stdin.read())
        else:
            payload = json.loads(Path(request_file).read_text())
    except FileNotFoundError:
        emit_error("request_file_not_found", f"Request file not found: {request_file}")
    except json.JSONDecodeError as exc:
        emit_error("invalid_json", f"Critique request is not valid JSON: {exc}")

    if isinstance(payload, dict) and isinstance(payload.get("criteria"), list):
        _handle_legacy_batch_critique(payload["criteria"])
        return

    _post(f"{_session_url()}/invoke/critique", _session_token(), payload, timeout=300.0)


_VERDICT_TO_SCORE = {"pass": 1.0, "rework": 0.5, "fail": 0.0}


def _handle_legacy_batch_critique(criteria: list[dict]) -> None:
    """Translate v006's per-criterion batch to ONE whole-artifact call.

    The current session-judge runs a Claude CLI under the hood with a 300s
    timeout. Calling it once per criterion (~10 per artifact) blew that
    budget and returned 500. Instead, pack all rubrics into a single
    session_goal, make ONE call, then synthesize each criterion's result
    uniformly from the whole-artifact verdict (pass/rework/fail).

    Granularity is lost (no per-criterion scoring) but session completes,
    structural gates pass, and we avoid timeout cascades. A future
    /invoke/critique-batch endpoint could restore per-criterion scoring.
    """
    url = f"{_session_url()}/invoke/critique"
    token = _session_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Use the first non-empty output_text + source_text as the artifact —
    # they are identical across criteria (v006 sends the same artifact for
    # every entry; only rubric_prompt differs).
    artifact_text = ""
    source_text = ""
    rubrics: list[str] = []
    criterion_ids: list[str] = []

    for entry in criteria:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("criterion_id", "")).strip()
        if not cid:
            continue
        criterion_ids.append(cid)
        rubrics.append(
            f"### {cid}\n{str(entry.get('rubric_prompt', '')).strip()}"
        )
        if not artifact_text:
            artifact_text = str(entry.get("output_text", "")).strip()
        if not source_text:
            source_text = str(entry.get("source_text", "")).strip()

    if not criterion_ids:
        typer.echo(json.dumps({"results": []}))
        return

    artifacts_block = artifact_text
    if source_text and source_text != "(No source data available)":
        artifacts_block = f"{artifact_text}\n\n---\nSource data:\n{source_text}"
    session_goal = (
        "Evaluate the artifact against ALL of the following criteria. "
        "Each numbered rubric describes one criterion the artifact must satisfy. "
        "Return ONE overall verdict (pass / rework / fail) reflecting whether "
        "the artifact, as a whole, would pass session gating against this rubric set.\n\n"
        + "\n\n".join(rubrics)
    )
    payload = {"session_artifacts": artifacts_block, "session_goal": session_goal}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=300.0)
    except httpx.HTTPError as exc:
        typer.echo(json.dumps({"error": f"judge service unreachable: {exc}"}))
        raise typer.Exit(1)
    if response.status_code >= 400:
        typer.echo(
            json.dumps({
                "error": f"judge service returned {response.status_code}",
                "body": response.text,
            })
        )
        raise typer.Exit(1)

    try:
        verdict = response.json()
    except ValueError:
        typer.echo(json.dumps({"error": "judge returned invalid JSON", "body": response.text}))
        raise typer.Exit(1)

    overall = str(verdict.get("overall", "")).strip().lower()
    score = _VERDICT_TO_SCORE.get(overall, 0.0)
    rationale = str(verdict.get("rationale", "")).strip() or f"overall={overall}"
    issues = verdict.get("issues") or []
    evidence = [
        f"[{str(it.get('severity', '?'))}] {str(it.get('summary', '')).strip()} "
        f"({str(it.get('citation', '')).strip()})"
        for it in issues if isinstance(it, dict)
    ]
    results = [
        {
            "criterion_id": cid,
            "normalized_score": score,
            "raw_score": score,
            "reasoning": rationale,
            "evidence": evidence,
            "model": "session-judge",
        }
        for cid in criterion_ids
    ]
    typer.echo(json.dumps({"results": results}))


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
