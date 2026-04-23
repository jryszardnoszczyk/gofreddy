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
from datetime import datetime, timezone
from pathlib import Path

import httpx
import typer
import yaml

app = typer.Typer(help="Evaluate content quality.", no_args_is_help=True)


def _emit_error(code: str, message: str, extra: dict | None = None) -> None:
    """Emit a structured error to stdout and exit 1.

    Shape matches the canonical `{"error": {"code", "message"}}` used by
    `cli.freddy.output.emit_error` and `cli.freddy.api._emit_error` so agents
    and scripts can parse CLI error output uniformly across commands. Extra
    sidecar fields (e.g. `fallback`, `domain_score`) are kept alongside the
    error object rather than inside it.
    """
    payload: dict = {"error": {"code": code, "message": message}}
    if extra:
        payload.update(extra)
    typer.echo(json.dumps(payload))
    raise typer.Exit(1)

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


# ─── Producer-owned evaluation scope for variant subcommand ────────────────
#
# Each domain's scored-artifact set is defined in
# ``<programs_dir>/<domain>-evaluation-scope.yaml`` — co-located with the
# agent's own ``<domain>-session.md`` prompt. Producers (the session agents)
# own the list, so when a prompt starts emitting a new artifact type the
# author updates the YAML in the same diff and the scorer picks it up.
#
# Historical context: this replaced a hardcoded ``_DOMAIN_FILE_PATTERNS``
# dispatch table in this module. That table repeatedly went stale — the
# "run #6 I.14 invisibility bug" is the canonical example (a new
# ``storyboards/*.json`` artifact was silently ignored by the scorer because
# the dispatch wasn't updated). Producer-owned YAML closes that drift path.


def _load_evaluation_scope(domain: str, session_dir: Path) -> dict:
    """Load evaluation-scope YAML for ``domain`` from the variant's programs/ dir.

    Walks up from ``session_dir`` to the variant root (the directory that
    contains both ``programs/`` and ``sessions/``) and reads
    ``programs/<domain>-evaluation-scope.yaml``. Fails loud if the YAML is
    missing — there is no fallback. If the loader can't find the file, the
    producer shipped a session without updating their scope declaration, and
    the scorer should refuse to run rather than silently evaluate a
    mis-specified artifact set.

    Returns the parsed dict with at minimum ``domain``, ``outputs``,
    ``source_data`` keys.
    """
    current = session_dir.resolve()
    yaml_name = f"{domain}-evaluation-scope.yaml"
    # Walk up until we find a programs/<domain>-evaluation-scope.yaml.
    for candidate in [current, *current.parents]:
        yaml_path = candidate / "programs" / yaml_name
        if yaml_path.is_file():
            with yaml_path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh)
    raise FileNotFoundError(
        f"evaluation-scope YAML missing for domain {domain} "
        f"(searched programs/{yaml_name} from {session_dir} upward)"
    )


def _read_files_from_scope(
    session_dir: Path,
    patterns: list[str],
    *,
    is_source_data: bool,
) -> dict[str, str]:
    """Read files matching ``patterns`` from ``session_dir`` using glob walking.

    ``is_source_data``-only inline exception: when walking source_data for the
    competitive domain, ``competitors/_client_baseline.json`` is legitimate
    evidence (the client's own Foreplay ad baseline is the reference point,
    not scratch) and survives the underscore-prefix skip that filters other
    transient files like ``competitors/_ads_scratch.json``. This is the ONE
    exception kept from the legacy ``_DOMAIN_FILE_PATTERNS`` behavior — it is
    handled inline here rather than via a generalized mechanism.
    """
    result: dict[str, str] = {}
    for pattern in patterns:
        if "*" in pattern:
            for filepath in sorted(session_dir.glob(pattern)):
                if not filepath.is_file():
                    continue
                rel = str(filepath.relative_to(session_dir))
                # Inline one-off exception: drop underscore-prefixed
                # competitors/* files EXCEPT the client baseline. Scoped
                # to source_data reads so it doesn't affect output globs.
                if (
                    is_source_data
                    and rel.startswith("competitors/_")
                    and rel != "competitors/_client_baseline.json"
                ):
                    continue
                result[rel] = filepath.read_text()
        else:
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
        _emit_error("missing_api_key", "GEMINI_API_KEY not set")

    optimized_path = Path(optimized_file)
    if not optimized_path.exists():
        _emit_error("file_not_found", f"File not found: {optimized_file}")

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
        _emit_error("missing_dependency", "google-genai package not installed")
    except Exception:
        _emit_error(
            "evaluation_failed",
            "Evaluation failed",
            {"fallback": "self-evaluate"},
        )


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
        _emit_error("file_not_found", f"Request file not found: {request_file}")
    except json.JSONDecodeError as exc:
        _emit_error("invalid_json", f"Critique request is not valid JSON: {exc}")

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
                    code = error.get("code", f"http_{response.status_code}")
                    msg = error.get("message", response.text)
                else:
                    code = f"http_{response.status_code}"
                    msg = str(error)
            except Exception:
                code = f"http_{response.status_code}"
                msg = response.text
            _emit_error(code, msg)

        typer.echo(json.dumps(response.json()))

    except httpx.TimeoutException:
        _emit_error("timeout", "Critique backend timeout")
    except SystemExit:
        raise
    except Exception as e:
        _emit_error("unexpected_error", str(e))


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
        _emit_error(
            "invalid_domain",
            f"Invalid domain: {domain}. Must be one of {valid_domains}",
        )

    sd = Path(session_dir)
    if not sd.is_dir():
        _emit_error("session_dir_not_found", f"Session directory not found: {session_dir}")

    # Load producer-owned evaluation scope. Fail loud on missing YAML —
    # the scorer refuses to run rather than silently evaluating the wrong
    # artifact set (see _load_evaluation_scope docstring).
    try:
        scope = _load_evaluation_scope(domain, sd)
    except FileNotFoundError as exc:
        _emit_error("evaluation_scope_missing", str(exc))

    outputs = _read_files_from_scope(
        sd, scope.get("outputs", []) or [], is_source_data=False
    )
    source_data = _read_files_from_scope(
        sd, scope.get("source_data", []) or [], is_source_data=True
    )

    if not outputs:
        _emit_error(
            "no_output_files",
            f"No output files found in {session_dir} for domain {domain}",
        )

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
                    code = error.get("code", f"http_{response.status_code}")
                    msg = error.get("message", response.text)
                else:
                    code = f"http_{response.status_code}"
                    msg = str(error)
            except Exception:
                code = f"http_{response.status_code}"
                msg = response.text
            _emit_error(code, msg, {"domain_score": 0})

        result = response.json()
        typer.echo(json.dumps(result))

        _persist_adhoc_lineage(sd, domain=domain, result=result, variant_id_override=variant_id)

    except httpx.TimeoutException:
        _emit_error("timeout", "Backend timeout (120s)", {"domain_score": 0})
    except SystemExit:
        raise
    except Exception as e:
        _emit_error("unexpected_error", str(e), {"domain_score": 0})


def _persist_adhoc_lineage(
    session_dir: Path,
    *,
    domain: str,
    result: dict,
    variant_id_override: str | None,
) -> None:
    """Append an ad-hoc score entry to archive/adhoc_scores.jsonl.

    Evolution's `evaluate_variant.py` owns `archive/lineage.jsonl` and
    writes rich full-suite entries. Manual CLI scores live in a parallel
    `archive/adhoc_scores.jsonl` file so lineage stays pure (aligns with
    the Hyperagents principle: archive successful strategies separately
    from interactive inspection artifacts).
    """
    try:
        variant_dir = session_dir.resolve().parents[2]
        archive_dir = variant_dir.parent
    except IndexError:
        return

    variant_id = variant_id_override or variant_dir.name
    score = result.get("domain_score", 0)
    entry = {
        "id": variant_id,
        "lane": domain,
        "source": "adhoc_cli",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scores": {domain: score},
    }
    # Write adhoc CLI scores to a dedicated file (archive/adhoc_scores.jsonl)
    # rather than lineage.jsonl. Evolution's lineage must contain only
    # evolution-produced entries so archival-of-successful-strategies stays
    # clean; CLI scores are manual and may represent partial evaluations.
    adhoc_path = archive_dir / "adhoc_scores.jsonl"
    try:
        with adhoc_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:  # pragma: no cover - don't fail CLI on persistence error
        print(f"WARNING: could not persist adhoc score: {exc}", file=sys.stderr)
