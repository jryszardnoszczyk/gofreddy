"""Cross-variant evolution metrics (Fix 8 + 9).

Aggregates per-variant ``scores.json`` outputs into generation-level rows so we
can watch inner-outer correlation and variant fixture-SD drift without
depending on the archived (meta-visible) state.

Outputs live under ``autoresearch/metrics/`` (outside the archive) so they are
NOT copied into the proposer's meta workspace. This keeps the evolutionary
feedback loop blind to its own diagnostic instrumentation.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


AUTORESEARCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = AUTORESEARCH_DIR.parent
ARCHIVE_DIR = AUTORESEARCH_DIR / "archive"
METRICS_DIR = AUTORESEARCH_DIR / "metrics"

# Put autoresearch/harness/ on sys.path so transient-error helpers can
# be imported without going through the ``harness`` package — which can
# resolve to a different ``harness/`` package at the repo root depending
# on pytest's rootdir discovery order.
_HARNESS_DIR = AUTORESEARCH_DIR / "harness"
if _HARNESS_DIR.is_dir() and str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

_GENERATIONS_LOG = METRICS_DIR / "generations.jsonl"
_ALERTS_LOG = METRICS_DIR / "alerts.jsonl"

# R-#30 alert agent config. Backend selection lives in _run_alert_agent_json.
_ALERT_AGENT_TIMEOUT = int(os.environ.get("AUTORESEARCH_ALERT_TIMEOUT", "120"))


_OPENCODE_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))


def _alert_agent_model() -> str:
    """Resolve the alert-agent model with per-backend defaults.

    Looked up at call time (not module import) so tests + operators can vary
    AUTORESEARCH_ALERT_BACKEND between calls. When the operator sets
    AUTORESEARCH_ALERT_MODEL explicitly, that wins. Otherwise the default
    matches the resolved backend: ``sonnet`` for claude, ``gpt-5.4`` for
    codex (matches evolve.py's codex meta-default), the OpenCode default
    model for opencode (matches harness/backend.py:default_session_model).
    """
    explicit = os.environ.get("AUTORESEARCH_ALERT_MODEL")
    if explicit:
        return explicit
    backend = os.environ.get("AUTORESEARCH_ALERT_BACKEND", "").strip().lower() or "claude"
    if backend == "opencode":
        return os.environ.get(
            "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
            "openrouter/deepseek/deepseek-v4-pro",
        )
    if backend == "codex":
        return "gpt-5.4"
    return "sonnet"
_ALERT_RECENT_WINDOW = 5
_ALERT_MAX_COUNT = 3  # agent may emit up to this many alerts per gen — hard cap enforced downstream
_VALID_ALERT_CODES = {
    "inner_outer_drift",
    "uneven_generalization",
    "plateau",
    "collapse",
    "overfitting",
    "novelty_exhausted",
}
_VALID_SEVERITIES = {"low", "medium", "high"}


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3 or len(ys) != n:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / denom, 3) if denom else None


def _load_variant_scores(variant_id: str) -> dict[str, Any] | None:
    path = ARCHIVE_DIR / variant_id / "scores.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"compute_metrics: failed to read {path}: {exc}", file=sys.stderr)
        return None


def _extract_variant_row(variant_id: str, data: dict[str, Any]) -> dict[str, Any]:
    keep_rates = [
        entry.get("keep_rate")
        for entry in (data.get("inner_metrics") or {}).values()
        if isinstance(entry, dict) and isinstance(entry.get("keep_rate"), (int, float))
    ]
    mean_keep = statistics.mean(keep_rates) if keep_rates else None
    domain_sds = [
        float(info.get("fixture_sd"))
        for info in (data.get("domains") or {}).values()
        if isinstance(info, dict) and isinstance(info.get("fixture_sd"), (int, float))
    ]
    max_fixture_sd = max(domain_sds) if domain_sds else 0.0
    composite = float(data.get("composite", 0.0) or 0.0)
    return {
        "variant_id": variant_id,
        "keep_rate": mean_keep,
        "composite": composite,
        "max_fixture_sd": round(max_fixture_sd, 4),
    }


def compute_generation_metrics(
    lane: str,
    gen_id: int,
    variant_ids: list[str],
) -> dict[str, Any]:
    """Build a generation-level metrics row."""
    rows: list[dict[str, Any]] = []
    for vid in variant_ids:
        data = _load_variant_scores(vid)
        if data is None:
            continue
        rows.append(_extract_variant_row(vid, data))

    all_composites = [r["composite"] for r in rows]
    keep_pairs = [(r["keep_rate"], r["composite"]) for r in rows if r["keep_rate"] is not None]
    keeps_for_corr = [k for k, _ in keep_pairs]
    composites_for_corr = [c for _, c in keep_pairs]

    return {
        "lane": lane,
        "gen_id": gen_id,
        "n": len(rows),
        "inner_outer_corr": _pearson(keeps_for_corr, composites_for_corr),
        "mean_keep": round(statistics.mean(keeps_for_corr), 3) if keeps_for_corr else None,
        "mean_composite": round(statistics.mean(all_composites), 3) if all_composites else None,
        "rows": rows,
    }


def _ensure_metrics_dir() -> None:
    METRICS_DIR.mkdir(exist_ok=True)


def append_generation_row(row: dict[str, Any]) -> None:
    _ensure_metrics_dir()
    with _GENERATIONS_LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def _recent_rows(lane: str, limit: int = _ALERT_RECENT_WINDOW) -> list[dict[str, Any]]:
    if not _GENERATIONS_LOG.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in _GENERATIONS_LOG.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"compute_metrics: skipping malformed line in generations.jsonl: {exc}", file=sys.stderr)
            continue
        if entry.get("lane") == lane:
            rows.append(entry)
    return rows[-limit:]


def _emit_alert(alert: dict[str, Any]) -> None:
    _ensure_metrics_dir()
    try:
        with _ALERTS_LOG.open("a") as fh:
            fh.write(json.dumps(alert) + "\n")
    except OSError as exc:
        print(f"compute_metrics: failed to write alert to {_ALERTS_LOG}: {exc}", file=sys.stderr)
    detail = alert.get("detail", "(no detail)")
    print(f"METRIC ALERT: {alert.get('code')} — {detail}", file=sys.stderr)


_ALERT_PROMPT_TEMPLATE = """You are a drift / overfitting monitor for autoresearch evolution.

Current generation {gen_id} (lane={lane}):
  n={n} variants
  mean_composite={mean_composite}
  mean_keep={mean_keep}
  inner_outer_corr={inner_outer_corr}
  per_variant: {per_variant}

Recent trajectory (last {recent_n} generations, oldest -> newest):
{trajectory}

Decide whether any drift or uneven-generalization signal is worth flagging.
Your judgment STANDS — there is no threshold backstop running alongside
you; under-flag and real regressions land silently, over-flag and the
operator stops trusting alerts. Be decisive, not conservative-by-default.

Flag drift only when clearly non-noise (e.g. corr fell AND mean_composite
or mean_keep regressed). Flag uneven_generalization only when
max_fixture_sd is high AND accompanied by implausibly high composite
(fixture saturation). Return [] if nothing worth flagging — empty is a
valid, expected answer most generations.

Return STRICT JSON: a JSON array (0 to {max_alerts} items) of alert
objects with this exact shape:
[
  {{"code": "inner_outer_drift" | "uneven_generalization" | "plateau" |
           "collapse" | "overfitting" | "novelty_exhausted",
    "severity": "low" | "medium" | "high",
    "variant_id": "<variant id or null>",
    "detail": "<1-2 sentence plain-English explanation>",
    "confidence": "high" | "medium" | "low"}}
]

Return ONLY the JSON array with no surrounding prose or code fences.
"""


def _build_alert_prompt(row: dict[str, Any], recent: list[dict[str, Any]]) -> str:
    per_variant = [
        {
            "id": r.get("variant_id"),
            "composite": r.get("composite"),
            "max_fixture_sd": r.get("max_fixture_sd"),
            "keep_rate": r.get("keep_rate"),
        }
        for r in row.get("rows", [])
    ]
    trajectory_lines = [
        f"  gen_id={t.get('gen_id')} mean_composite={t.get('mean_composite')} "
        f"mean_keep={t.get('mean_keep')} inner_outer_corr={t.get('inner_outer_corr')}"
        for t in recent
    ]
    trajectory = "\n".join(trajectory_lines) if trajectory_lines else "  (no prior rows for this lane)"
    return _ALERT_PROMPT_TEMPLATE.format(
        gen_id=row.get("gen_id"),
        lane=row.get("lane"),
        n=row.get("n"),
        mean_composite=row.get("mean_composite"),
        mean_keep=row.get("mean_keep"),
        inner_outer_corr=row.get("inner_outer_corr"),
        per_variant=json.dumps(per_variant),
        recent_n=len(recent),
        trajectory=trajectory,
        max_alerts=_ALERT_MAX_COUNT,
    )


def _build_alert_cmd(backend: str, model: str, prompt: str) -> list[str]:
    """Build the subprocess argv for the chosen alert backend.

    Three-way interchangeable: claude/codex/opencode share the alert agent
    contract (single-shot prompt, JSON-array text response). claude wraps
    its output in a ``{"result": ...}`` envelope; opencode emits JSONL with
    a ``final_answer`` text event; codex prints its assistant text directly
    to stdout.
    """
    if backend == "opencode":
        return [
            "opencode", "run",
            "--dangerously-skip-permissions",
            "-m", model,
            "--format", "json",
            prompt,
        ]
    if backend == "claude":
        return [
            "claude",
            "-p", prompt,
            "--output-format", "json",
            "--session-id", str(uuid.uuid4()),
            "--model", model,
            "--dangerously-skip-permissions",
        ]
    if backend == "codex":
        # Mirrors evolve.py / harness/agent.py codex flags: ephemeral run
        # with otel disabled, sandbox = read-only since the alert agent
        # does no file I/O. Prompt is passed via stdin so codex's
        # ``--last-message`` (when present) can be used by the parser.
        return [
            "codex", "exec",
            "--model", model,
            "--sandbox", "read-only",
            "--color", "never",
            "--ephemeral",
            "-c", "approval_policy=\"never\"",
            "-c", "otel.exporter=\"none\"",
            "-c", "otel.trace_exporter=\"none\"",
            "-c", "otel.metrics_exporter=\"none\"",
            prompt,
        ]
    raise RuntimeError(
        f"AUTORESEARCH_ALERT_BACKEND={backend!r} not supported (must be claude, codex, or opencode)"
    )


def _extract_alert_text(backend: str, stdout: str) -> str:
    """Pull the assistant's JSON-array text out of the backend's stdout shape."""
    if backend == "opencode":
        # JSONL: walk events, find final-answer text or last text before stop.
        last_text: str | None = None
        final_answer: str | None = None
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            part = event.get("part") or {}
            if etype == "text":
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    meta = (part.get("metadata") or {}).get("openai") or {}
                    if meta.get("phase") == "final_answer":
                        final_answer = text
            elif etype == "step_finish" and part.get("reason") == "stop":
                if final_answer is None and last_text is not None:
                    final_answer = last_text
        return final_answer if final_answer is not None else stdout

    if backend == "claude":
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError:
            return stdout
        if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
            return envelope["result"]
        return stdout

    # codex prints raw assistant text. Downstream _parse_alerts already
    # strips ``` fences and tolerates wrapper prose, so return as-is.
    return stdout


def _run_alert_agent_json(prompt: str, *, model: str, timeout: int) -> str:
    """Invoke the alert agent CLI with JSON-mode output; return the assistant text.

    Backend selection (in order):
      1. AUTORESEARCH_ALERT_BACKEND env var: "claude", "codex", or "opencode"
      2. Fallback: "claude" (preserves prior default)

    For opencode, retries on transient upstream errors (rate_limit,
    provider_overloaded, 504 timeout) up to OPENCODE_MAX_RETRIES (default 3)
    times — same policy harness/agent.py and evolve.py apply. Detection
    walks the captured stdout (no log file at this layer) via
    harness.opencode_jsonl.stdout_has_transient_error.
    """
    from opencode_jsonl import stdout_has_transient_error  # noqa: E402  # autoresearch/harness/ added to sys.path at module init

    backend = os.environ.get("AUTORESEARCH_ALERT_BACKEND", "").strip().lower() or "claude"
    cmd = _build_alert_cmd(backend, model, prompt)

    env = os.environ.copy()
    if backend == "opencode":
        config_path = REPO_ROOT / "opencode.json"
        if config_path.is_file() and not env.get("OPENCODE_CONFIG"):
            env["OPENCODE_CONFIG"] = str(config_path)

    attempts = _OPENCODE_MAX_ATTEMPTS if backend == "opencode" else 1
    proc = None
    for attempt in range(1, attempts + 1):
        proc = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=timeout,
            env=env,
        )
        if backend != "opencode" or attempt == attempts:
            break
        # opencode usually exits 0 even on upstream errors — detect via JSONL
        if proc.returncode == 0 and not stdout_has_transient_error(proc.stdout):
            break
        print(
            f"alert agent opencode attempt {attempt}/{attempts} hit transient error "
            f"(exit={proc.returncode}); retrying",
            file=sys.stderr,
        )

    if proc.returncode != 0:
        raise RuntimeError(
            f"{backend} CLI exited {proc.returncode}: {(proc.stderr or proc.stdout or '')[:400]}"
        )

    return _extract_alert_text(backend, proc.stdout)


def _parse_alerts(raw: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse the agent's JSON-array response into validated alert dicts.

    Malformed entries are dropped (logged to stderr); shape-valid entries are
    stamped with the row's ``lane`` + ``gen_id`` and a ``source`` tag.
    """
    text = raw.strip()
    # Strip code fences if the agent wrapped output despite the prompt.
    if text.startswith("```"):
        text = text.strip("`")
        # remove possible language tag
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"compute_metrics: alert agent returned non-JSON: {exc}", file=sys.stderr)
        return []
    if not isinstance(parsed, list):
        print(f"compute_metrics: alert agent returned non-list: {type(parsed).__name__}", file=sys.stderr)
        return []

    known_variant_ids = {r.get("variant_id") for r in row.get("rows", [])}
    alerts: list[dict[str, Any]] = []
    for item in parsed[:_ALERT_MAX_COUNT]:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        severity = item.get("severity", "medium")
        if code not in _VALID_ALERT_CODES:
            print(f"compute_metrics: dropping alert with unknown code={code!r}", file=sys.stderr)
            continue
        if severity not in _VALID_SEVERITIES:
            severity = "medium"
        variant_id = item.get("variant_id")
        # Drop hallucinated variant ids; keep alert as lane-level instead.
        if variant_id is not None and variant_id not in known_variant_ids:
            variant_id = None
        detail = str(item.get("detail", "")).strip()
        confidence = item.get("confidence", "medium")
        if confidence not in _VALID_SEVERITIES:
            confidence = "medium"
        alerts.append({
            "code": code,
            "severity": severity,
            "lane": row.get("lane"),
            "gen_id": row.get("gen_id"),
            "variant_id": variant_id,
            "detail": detail or f"agent flagged {code}",
            "confidence": confidence,
            "source": "agent",
        })
    return alerts


def judge_alerts(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Call the alert agent and return validated alerts (possibly empty).

    Separate from ``check_alerts`` so callers / tests can stub the subprocess
    without re-implementing alert emission. Callers MUST pass validated alerts
    to ``_emit_alert`` — ``judge_alerts`` does not write to ``alerts.jsonl``.
    """
    recent = _recent_rows(row.get("lane", ""))
    prompt = _build_alert_prompt(row, recent)
    try:
        raw = _run_alert_agent_json(prompt, model=_alert_agent_model(), timeout=_ALERT_AGENT_TIMEOUT)
    except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
        print(f"compute_metrics: alert agent call failed — skipping: {exc}", file=sys.stderr)
        return []
    return _parse_alerts(raw, row)


def check_alerts(row: dict[str, Any]) -> None:
    """Ask the alert agent for any alerts worth flagging, emit them to stderr
    and ``alerts.jsonl``.

    R-#30: no threshold backstop — the agent's judgment stands.
    """
    for alert in judge_alerts(row):
        _emit_alert(alert)


def record_generation(
    lane: str,
    gen_id: int,
    variant_ids: list[str],
) -> dict[str, Any]:
    """Top-level entry used from evolve.py after each generation completes."""
    row = compute_generation_metrics(lane, gen_id, variant_ids)
    append_generation_row(row)
    check_alerts(row)
    return row
