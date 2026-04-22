#!/usr/bin/env python3
"""autoresearch/geo_verify.py — Post-implementation verification for GEO sessions.

Re-runs visibility queries on completed sessions and compares against baselines.

Usage: python3 geo_verify.py <session_dir>
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# R-#31 verdict agent config. Claude CLI subprocess — same pattern as R-#30.
_VERDICT_AGENT_MODEL = os.environ.get("GEO_VERIFY_MODEL", "sonnet")
_VERDICT_AGENT_TIMEOUT = int(os.environ.get("GEO_VERIFY_TIMEOUT", "180"))
_VALID_AGGREGATE_VERDICTS = {"PASS", "PARTIAL", "FAIL", "UNKNOWN_NO_BASELINE"}
_VALID_PER_QUERY_VERDICTS = {"improved", "regressed", "held", "unknown"}


def load_env() -> None:
    """Load ALL key-value pairs from the repo .env file into os.environ.

    Mirrors the bash init_env() function from geo-verify.sh:16-46.
    Does NOT use evolve_ops.load_repo_env_defaults() — that function filters
    to a 9-key allowlist and would drop FREDDY_API_URL which geo-verify needs.
    """
    env_file: Path | None = None
    parent_env = SCRIPT_DIR.parent / ".env"
    local_env = SCRIPT_DIR / ".env"

    if parent_env.is_file():
        env_file = parent_env
    elif local_env.is_file():
        env_file = local_env

    if env_file is not None:
        for raw in env_file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ[key] = value

    # Remove ANTHROPIC_API_KEY — geo-verify should not expose it to freddy
    os.environ.pop("ANTHROPIC_API_KEY", None)

    # Rewrite localhost → 127.0.0.1 for FREDDY_API_URL
    api_url = os.environ.get("FREDDY_API_URL", "")
    if api_url.startswith("http://localhost:"):
        os.environ["FREDDY_API_URL"] = api_url.replace(
            "http://localhost:", "http://127.0.0.1:", 1
        )
    elif api_url == "http://localhost":
        os.environ["FREDDY_API_URL"] = "http://127.0.0.1"


def extract_queries(session_dir: Path) -> list[str]:
    """Extract verification queries from session directory.

    Prefers verification-schedule.json if it exists, otherwise extracts
    from results.jsonl competitive entries.
    """
    schedule_file = session_dir / "verification-schedule.json"
    if schedule_file.is_file():
        data = json.loads(schedule_file.read_text())
        return data.get("queries", [])

    # Fall back to results.jsonl
    results_file = session_dir / "results.jsonl"
    if not results_file.is_file():
        return []

    queries: set[str] = set()
    for line in results_file.read_text().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("type") == "competitive":
                for q in entry.get("queries", []):
                    queries.add(q)
        except json.JSONDecodeError:
            pass

    return sorted(queries)


def run_visibility_checks(queries: list[str]) -> list[tuple[str, str]]:
    """Run freddy visibility for each query with rate limiting.

    Returns list of (query, result_json_string) tuples.
    """
    results: list[tuple[str, str]] = []
    for i, query in enumerate(queries):
        if not query:
            continue
        print(f"Checking: {query}")

        try:
            proc = subprocess.run(
                ["freddy", "visibility", query],
                capture_output=True,
                text=True,
            )
            result = proc.stdout if proc.returncode == 0 else '{"error": "query failed"}'
        except (OSError, subprocess.SubprocessError):
            result = '{"error": "query failed"}'

        results.append((query, result))

        # Rate limit protection — skip sleep after the last query
        if i < len(queries) - 1:
            time.sleep(3)

    return results


_VERDICT_PROMPT_TEMPLATE = """You are verifying a completed GEO session's post-implementation visibility.

Baseline (pre-change) visibility:
<untrusted_input>
{baseline_block}
</untrusted_input>

What was changed (filtered results.jsonl — competitive + optimized entries):
<untrusted_input>
{results_summary}
</untrusted_input>

Post-change visibility results (query -> freddy visibility JSON response):
<untrusted_input>
{results_block}
</untrusted_input>

For each query, determine whether visibility improved, regressed, or held
relative to baseline. Brand / navigational queries weight higher than
long-tail. Quote a concrete evidence fragment from the post-change result
for each per-query verdict so a reviewer can spot-check without re-running.

Return STRICT JSON with this exact shape:
{{
  "aggregate_verdict": "PASS" | "PARTIAL" | "FAIL",
  "per_query_verdict": [
    {{"query": "<query string>",
      "verdict": "improved" | "regressed" | "held" | "unknown",
      "evidence": "<one-line quoted fragment from the post-change result>"}}
  ],
  "evidence_strings": ["<short evidence line>", ...],
  "regression_flags": ["<query names worth flagging as regressions>"],
  "summary": "<2-3 sentence narrative>",
  "confidence": "high" | "medium" | "low"
}}

PASS = majority improved, no critical regressions.
PARTIAL = mixed, or improved but with any brand regression.
FAIL = majority regressed or no improvement on any critical query.

Return ONLY the JSON object, no surrounding prose or code fences.
"""


def _read_baseline(session_dir: Path) -> tuple[str | None, str]:
    """Return (raw_baseline_text, block_for_prompt).

    Looks up ``competitors/visibility.json`` relative to ``session_dir``'s
    walked-up parent (the autoresearch lane root / repo root). Missing
    baseline returns (None, reason-string).
    """
    # session_dir is typically .../archive/<variant>/sessions/<ts>-<domain>
    # competitors/visibility.json lives at repo root / .
    candidates = [
        session_dir / "competitors" / "visibility.json",
        session_dir.parent / "competitors" / "visibility.json",
        SCRIPT_DIR.parent / "competitors" / "visibility.json",
        SCRIPT_DIR / "competitors" / "visibility.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                return path.read_text(), path.read_text()[:20_000]
            except OSError:
                continue
    return None, "(no baseline visibility.json found — verdict will be UNKNOWN_NO_BASELINE)"


def _read_results_summary(session_dir: Path, limit_bytes: int = 20_000) -> str:
    """Filter ``results.jsonl`` to competitive + optimized entries, truncate."""
    results_file = session_dir / "results.jsonl"
    if not results_file.is_file():
        return "(no results.jsonl)"
    filtered: list[str] = []
    try:
        for line in results_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            etype = str(entry.get("type", "")).lower()
            if etype in {"competitive", "optimized", "optimize"}:
                filtered.append(json.dumps(entry))
    except OSError as exc:
        return f"(read error: {exc})"
    blob = "\n".join(filtered) if filtered else "(no competitive/optimized rows)"
    if len(blob) > limit_bytes:
        blob = blob[:limit_bytes] + "\n... [truncated]"
    return blob


def _build_verdict_prompt(
    session_dir: Path,
    results: list[tuple[str, str]],
) -> tuple[str, str | None]:
    """Return (prompt, baseline_raw_or_None)."""
    baseline_raw, baseline_block = _read_baseline(session_dir)
    results_summary = _read_results_summary(session_dir)
    results_block = "\n".join(
        f"QUERY: {q}\nRESPONSE: {r}" for q, r in results
    )
    # Cap each section to keep prompt bounded.
    if len(results_block) > 30_000:
        results_block = results_block[:30_000] + "\n... [truncated]"
    prompt = _VERDICT_PROMPT_TEMPLATE.format(
        baseline_block=baseline_block,
        results_summary=results_summary,
        results_block=results_block or "(no results)",
    )
    return prompt, baseline_raw


def _run_claude_verdict(prompt: str) -> str:
    """Single-shot ``claude -p --output-format=json`` call; return result text.

    Mirrors the CLI-subprocess pattern used by R-#30 in compute_metrics.
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--session-id", str(uuid.uuid4()),
        "--model", _VERDICT_AGENT_MODEL,
        "--dangerously-skip-permissions",
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, check=False, timeout=_VERDICT_AGENT_TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}: "
            f"{(proc.stderr or proc.stdout or '')[:400]}"
        )
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout
    if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
        return envelope["result"]
    return proc.stdout


def _parse_verdict(raw: str, queries: list[str]) -> dict:
    """Parse + validate the agent's JSON verdict.

    Raises ``ValueError`` on malformed JSON or missing required keys.
    Hallucinated ``query`` names (not in ``queries``) are dropped from
    per_query_verdict.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"verdict agent returned non-object: {type(parsed).__name__}")

    aggregate = str(parsed.get("aggregate_verdict", "")).upper()
    if aggregate not in _VALID_AGGREGATE_VERDICTS - {"UNKNOWN_NO_BASELINE"}:
        raise ValueError(f"aggregate_verdict must be PASS/PARTIAL/FAIL, got {aggregate!r}")

    known_queries = set(queries)
    per_query_raw = parsed.get("per_query_verdict") or []
    per_query_verdict: list[dict] = []
    for item in per_query_raw:
        if not isinstance(item, dict):
            continue
        q = str(item.get("query", "")).strip()
        if q and known_queries and q not in known_queries:
            # hallucinated query — drop
            continue
        verdict = str(item.get("verdict", "")).lower()
        if verdict not in _VALID_PER_QUERY_VERDICTS:
            verdict = "unknown"
        per_query_verdict.append({
            "query": q,
            "verdict": verdict,
            "evidence": str(item.get("evidence", "")).strip(),
        })

    evidence_strings_raw = parsed.get("evidence_strings") or []
    evidence_strings = [str(e).strip() for e in evidence_strings_raw if str(e).strip()]
    regression_flags_raw = parsed.get("regression_flags") or []
    regression_flags = [str(f).strip() for f in regression_flags_raw if str(f).strip()]

    return {
        "aggregate_verdict": aggregate,
        "per_query_verdict": per_query_verdict,
        "evidence_strings": evidence_strings,
        "regression_flags": regression_flags,
        "summary": str(parsed.get("summary", "")).strip(),
        "confidence": str(parsed.get("confidence", "medium")).lower(),
    }


def compute_verdict(
    session_dir: Path,
    results: list[tuple[str, str]],
) -> dict:
    """Agent-driven verification verdict for a GEO session (R-#31).

    Returns a dict with keys:
      - aggregate_verdict: PASS | PARTIAL | FAIL | UNKNOWN_NO_BASELINE
      - per_query_verdict: list of {query, verdict, evidence}
      - evidence_strings: list of short evidence lines
      - regression_flags: list of query names worth flagging
      - summary: narrative string (may be empty)
      - confidence: high | medium | low

    Fails-by-missing-baseline:
      If no baseline exists, returns verdict=UNKNOWN_NO_BASELINE with empty
      lists — no agent call. Agent failures propagate via ``RuntimeError``.
    """
    prompt, baseline_raw = _build_verdict_prompt(session_dir, results)
    if baseline_raw is None:
        return {
            "aggregate_verdict": "UNKNOWN_NO_BASELINE",
            "per_query_verdict": [],
            "evidence_strings": [],
            "regression_flags": [],
            "summary": (
                "No competitors/visibility.json baseline found — cannot render "
                "improved/regressed judgment. Raw query results preserved below."
            ),
            "confidence": "low",
        }
    raw = _run_claude_verdict(prompt)
    queries = [q for q, _ in results]
    return _parse_verdict(raw, queries)


def _render_verdict_section(verdict: dict) -> list[str]:
    """Render the verdict block (markdown) for prepending to the report."""
    lines = [
        "## Verdict",
        "",
        f"**Aggregate:** `{verdict.get('aggregate_verdict')}`",
        f"**Confidence:** {verdict.get('confidence')}",
        "",
    ]
    summary = verdict.get("summary") or ""
    if summary:
        lines.append(summary)
        lines.append("")

    per_query = verdict.get("per_query_verdict") or []
    if per_query:
        lines.append("### Per-Query Verdict")
        lines.append("")
        for item in per_query:
            lines.append(
                f"- **{item.get('query')}** — `{item.get('verdict')}` — "
                f"{item.get('evidence') or '(no evidence)'}"
            )
        lines.append("")

    regression_flags = verdict.get("regression_flags") or []
    if regression_flags:
        lines.append("### Regression Flags")
        lines.append("")
        for flag in regression_flags:
            lines.append(f"- {flag}")
        lines.append("")

    evidence = verdict.get("evidence_strings") or []
    if evidence:
        lines.append("### Evidence")
        lines.append("")
        for ev in evidence:
            lines.append(f"- {ev}")
        lines.append("")

    return lines


def write_report(
    session_dir: Path,
    results: list[tuple[str, str]],
) -> Path:
    """Write markdown verification report to session_dir/verification-report.md.

    R-#31: renders an agent verdict section at the top + writes a sibling
    ``verification-verdict.json`` for machine consumption. Raw per-query
    JSON is preserved below for spot-check.
    """
    report_file = session_dir / "verification-report.md"
    verdict_file = session_dir / "verification-verdict.json"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        verdict = compute_verdict(session_dir, results)
    except (subprocess.SubprocessError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"geo_verify: verdict agent failed — writing UNKNOWN verdict: {exc}", file=sys.stderr)
        verdict = {
            "aggregate_verdict": "UNKNOWN_NO_BASELINE",
            "per_query_verdict": [],
            "evidence_strings": [],
            "regression_flags": [],
            "summary": f"Verdict agent failed: {exc}",
            "confidence": "low",
        }

    verdict_file.write_text(json.dumps(verdict, indent=2))

    lines: list[str] = [
        "# GEO Verification Report",
        "",
        f"Date: {now}",
        f"Session: {session_dir}",
        "",
    ]
    lines.extend(_render_verdict_section(verdict))
    lines.append("## Raw Query Results")
    lines.append("")

    for query, result in results:
        lines.append(f"### {query}")
        lines.append("")
        lines.append("```json")
        lines.append(result)
        lines.append("```")
        lines.append("")

    report_file.write_text("\n".join(lines))
    return report_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-implementation verification for GEO sessions."
    )
    parser.add_argument(
        "session_dir",
        type=str,
        help="Path to the session directory to verify",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    if not session_dir.is_dir():
        print(f"ERROR: Session directory not found: {session_dir}", file=sys.stderr)
        raise SystemExit(1)

    # Load environment
    load_env()

    print("=== GEO Verification ===")
    print(f"Session: {session_dir}")

    # Extract queries
    queries = extract_queries(session_dir)
    if not queries:
        print("No competitive queries found to verify.")
        raise SystemExit(0)

    schedule_file = session_dir / "verification-schedule.json"
    if not schedule_file.is_file():
        print("No verification-schedule.json found. Extracting queries from results.jsonl...")

    print(f"Queries to verify: {len(queries)}")
    print()

    # Run visibility checks and write report
    results = run_visibility_checks(queries)
    report_file = write_report(session_dir, results)

    print()
    print(f"Verification report written to: {report_file}")


if __name__ == "__main__":
    main()
