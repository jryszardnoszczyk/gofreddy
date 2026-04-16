"""Evaluate content quality.

Subcommands:
  review  — Quick adversarial review (session-level, inner loop). Local Gemini call.
  critique — Trusted judge execution for evolvable session-time critique.
  variant — Comprehensive domain evaluation via backend (evolution-level, outer loop).
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
import typer

app = typer.Typer(help="Evaluate content quality.", no_args_is_help=True)

MAX_CONTENT_CHARS = 30_000
MAX_COMPETITIVE_CHARS = 10_000

EVALUATE_PROMPT = """You are an adversarial reviewer of GEO (Generative Engine Optimization) improvements.

Your job is to find reasons to DISCARD these proposed changes. You must provide at least 3 specific weaknesses.

For citability assessment: identify the single strongest competitor page for this query and explain whether the proposed content would be cited OVER it by an AI engine.

<original_content>
{original_content}
</original_content>

<proposed_changes>
{proposed_changes}
</proposed_changes>

<competitive_context>
{competitive_context}
</competitive_context>

Respond with JSON:
{{
  "decision": "KEEP" or "DISCARD",
  "confidence": 0.0-1.0,
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "strongest_competitor": "URL or name",
  "would_be_cited_over_competitor": true/false,
  "rationale": "1-2 sentence summary"
}}
"""

EVALUATE_MODEL = "gemini-2.0-flash"


# ─── Domain-specific file discovery for variant subcommand ────────────────

_DOMAIN_FILE_PATTERNS: dict[str, dict[str, list[str]]] = {
    "geo": {
        "outputs": ["optimized/*.md"],
        "source_data": ["pages/*.json", "competitors/visibility.json"],
    },
    "competitive": {
        "outputs": ["brief.md"],
        "source_data": ["competitors/*.json", "competitors/_client_baseline.json", "session.md"],
    },
    "monitoring": {
        "outputs": ["digest.md", "findings.md", "session.md", "results.jsonl",
                     "stories/*.json", "synthesized/*.md",
                     "recommendations/executive_summary.md",
                     "recommendations/action_items.md"],
        # source_data: real external inputs the agent reads (fed to LLM judges
        # as reference context). Agent-generated outputs live in "outputs" above.
        "source_data": ["mentions/*.json"],
    },
    "storyboard": {
        # stories/*.json comes from PLAN_STORY; storyboards/*.json comes from
        # IDEATE. Both must be visible to the variant-level scorer, otherwise
        # a successful IDEATE phase writes artifacts the scorer silently
        # ignores (this was the run #6 I.14 invisibility bug).
        "outputs": ["stories/*.json", "storyboards/*.json"],
        "source_data": ["patterns/*.json", "session.md"],
    },
}


def _read_files(session_dir: Path, patterns: list[str]) -> dict[str, str]:
    """Read files matching patterns from session directory.

    The underscore-skip rule in the glob branch drops transient work files
    like ``competitors/_ads_scratch.json``, but carves out an exception for
    ``competitors/_client_baseline.json`` — the client's own Foreplay ad
    baseline is legitimate source_data for the LLM judge context.
    """
    result: dict[str, str] = {}
    for pattern in patterns:
        if "*" in pattern:
            # Glob pattern
            for filepath in sorted(session_dir.glob(pattern)):
                if filepath.is_file():
                    rel = str(filepath.relative_to(session_dir))
                    # Skip underscore-prefixed files for competitive source_data,
                    # except the client baseline (it IS real source data).
                    if rel.startswith("competitors/_") and rel != "competitors/_client_baseline.json":
                        continue
                    result[rel] = filepath.read_text()
        else:
            # Exact path
            filepath = session_dir / pattern
            if filepath.is_file():
                result[pattern] = filepath.read_text()
    return result


# ─── Review subcommand (unchanged from original evaluate_command) ────────


@app.command("review")
def review_command(
    optimized_file: str = typer.Argument(..., help="Path to optimized/*.md file to evaluate"),
    page_cache: str = typer.Option(None, "--page-cache", help="Path to cached page JSON (pages/{slug}.json)"),
    competitive_data: str = typer.Option(None, "--competitive", help="Path to competitors/visibility.json"),
) -> None:
    """Quick adversarial review (session-level, inner loop). Unchanged."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        typer.echo(json.dumps({"error": "GEMINI_API_KEY not set"}))
        raise typer.Exit(1)

    optimized_path = Path(optimized_file)
    if not optimized_path.exists():
        typer.echo(json.dumps({"error": f"File not found: {optimized_file}"}))
        raise typer.Exit(1)

    proposed_changes = optimized_path.read_text()

    # Load original content from page cache if available
    original_content = ""
    if page_cache is not None:
        cache_path = Path(page_cache)
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                original_content = data.get("text", "")[:MAX_CONTENT_CHARS]
            except (json.JSONDecodeError, KeyError):
                pass

    # Load competitive context if available
    competitive_context = "No competitive data available."
    if competitive_data is not None:
        comp_path = Path(competitive_data)
        if comp_path.exists():
            try:
                competitive_context = comp_path.read_text()[:MAX_COMPETITIVE_CHARS]
            except Exception:
                pass

    # Sanitize external content before prompt injection
    try:
        from src.common.sanitize import sanitize_external
        proposed_changes = sanitize_external(proposed_changes, MAX_CONTENT_CHARS)
        if original_content:
            original_content = sanitize_external(original_content, MAX_CONTENT_CHARS)
        competitive_context = sanitize_external(competitive_context, MAX_COMPETITIVE_CHARS)
    except ImportError:
        # sanitize_external not available — truncate only
        proposed_changes = proposed_changes[:MAX_CONTENT_CHARS]
        if original_content:
            original_content = original_content[:MAX_CONTENT_CHARS]

    # Build prompt
    prompt = EVALUATE_PROMPT.format(
        original_content=original_content if original_content else "Original content not available.",
        proposed_changes=proposed_changes,
        competitive_context=competitive_context,
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=EVALUATE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        # Record cost
        try:
            from src.common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
            t_in, t_out, c = extract_gemini_usage(response, EVALUATE_MODEL)
            asyncio.run(_cost_recorder.record(
                "gemini", "geo_evaluate",
                tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=EVALUATE_MODEL,
            ))
        except Exception:
            pass  # Cost recording is non-fatal

        result_text = response.text
        typer.echo(result_text)

    except ImportError:
        typer.echo(json.dumps({"error": "google-genai package not installed"}))
        raise typer.Exit(1)
    except Exception:
        typer.echo(json.dumps({"error": "Evaluation failed", "fallback": "self-evaluate"}))
        raise typer.Exit(1)


# ─── Variant subcommand (new — calls backend) ───────────────────────────


@app.command("critique")
def critique_command(
    request_file: str = typer.Argument(..., help="Path to critique request JSON, or '-' to read from stdin"),
) -> None:
    """Trusted judge execution for evolvable session-time critique."""
    from ..config import load_config
    from ..api import make_client

    try:
        if request_file == "-":
            request_body = json.loads(sys.stdin.read())
        else:
            request_body = json.loads(Path(request_file).read_text())
    except FileNotFoundError:
        typer.echo(json.dumps({"error": f"Request file not found: {request_file}"}))
        raise typer.Exit(1)
    except json.JSONDecodeError as exc:
        typer.echo(json.dumps({"error": f"Critique request is not valid JSON: {exc}"}))
        raise typer.Exit(1)

    config = load_config()
    client = make_client(config)

    try:
        response = client.request(
            "POST",
            "/v1/evaluation/critique",
            json=request_body,
            timeout=httpx.Timeout(connect=5.0, read=360.0, write=10.0, pool=5.0),
        )

        if response.status_code >= 400:
            try:
                error_body = response.json()
                error = error_body.get("error", error_body.get("detail", {}))
                if isinstance(error, dict):
                    msg = error.get("message", response.text)
                else:
                    msg = str(error)
            except Exception:
                msg = response.text
            typer.echo(json.dumps({"error": msg}))
            raise typer.Exit(1)

        typer.echo(json.dumps(response.json()))

    except httpx.TimeoutException:
        typer.echo(json.dumps({"error": "Critique backend timeout"}))
        raise typer.Exit(1)
    except SystemExit:
        raise
    except Exception as e:
        typer.echo(json.dumps({"error": str(e)}))
        raise typer.Exit(1)


@app.command("variant")
def variant_command(
    domain: str = typer.Argument(..., help="Domain: geo, competitive, monitoring, storyboard"),
    session_dir: str = typer.Argument(..., help="Session directory with outputs"),
    campaign_id: str = typer.Option(None, "--campaign-id", help="Evolution campaign ID"),
    variant_id: str = typer.Option(None, "--variant-id", help="Variant ID for tracking"),
) -> None:
    """Comprehensive domain evaluation via backend (evolution-level, outer loop)."""
    from ..config import load_config
    from ..api import make_client

    valid_domains = {"geo", "competitive", "monitoring", "storyboard"}
    if domain not in valid_domains:
        typer.echo(json.dumps({"error": f"Invalid domain: {domain}. Must be one of {valid_domains}"}))
        raise typer.Exit(1)

    sd = Path(session_dir)
    if not sd.is_dir():
        typer.echo(json.dumps({"error": f"Session directory not found: {session_dir}"}))
        raise typer.Exit(1)

    # Read domain-specific files
    patterns = _DOMAIN_FILE_PATTERNS.get(domain)
    if patterns is None:
        typer.echo(json.dumps({"error": f"No file patterns defined for domain: {domain}"}))
        raise typer.Exit(1)

    outputs = _read_files(sd, patterns["outputs"])
    source_data = _read_files(sd, patterns["source_data"])

    if not outputs:
        typer.echo(json.dumps({"error": f"No output files found in {session_dir} for domain {domain}"}))
        raise typer.Exit(1)

    # Build request
    request_body: dict = {
        "domain": domain,
        "outputs": outputs,
        "source_data": source_data,
    }
    if campaign_id is not None:
        request_body["campaign_id"] = campaign_id
    if variant_id is not None:
        request_body["variant_id"] = variant_id

    # Call backend with extended timeout (judges can take up to 5 minutes total)
    config = load_config()
    client = make_client(config)

    try:
        response = client.request(
            "POST",
            "/v1/evaluation/evaluate",
            json=request_body,
            timeout=httpx.Timeout(connect=5.0, read=360.0, write=10.0, pool=5.0),
        )

        if response.status_code >= 400:
            try:
                error_body = response.json()
                error = error_body.get("error", error_body.get("detail", {}))
                if isinstance(error, dict):
                    msg = error.get("message", response.text)
                else:
                    msg = str(error)
            except Exception:
                msg = response.text
            typer.echo(json.dumps({"error": msg, "domain_score": 0}))
            raise typer.Exit(1)

        result = response.json()
        typer.echo(json.dumps(result))

    except httpx.TimeoutException:
        typer.echo(json.dumps({"error": "Backend timeout (120s)", "domain_score": 0}))
        raise typer.Exit(1)
    except SystemExit:
        raise
    except Exception as e:
        typer.echo(json.dumps({"error": str(e), "domain_score": 0}))
        raise typer.Exit(1)
