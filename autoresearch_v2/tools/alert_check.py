"""autoresearch_v2/tools/alert_check.py — LLM alert agent over results.tsv trajectory.

Port of v1's compute_metrics.py alert agent (the part that produced the only
real catches in alerts.jsonl: v176/v177 collapse). Slim by ~60%: drops the
Pearson/keep-rate/per-generation aggregation pipeline; KEEPS the last-N-rows
trajectory context in the prompt — that IS what made the v176/v177 catch work
(per audit 2026-05-11 #4).

The agent reads the last N rows from `lanes/<lane>/results.tsv` (trajectory),
asks an LLM whether anything is worth flagging, validates the response shape,
and appends severity≥medium alerts to `autoresearch_v2/alerts.jsonl`.

Exit code is always 0 — alerts are informational, not blocking.

Stream A Bug 3 integration: alert prompt includes
`variant_output_failure_rate_last_N`, computed from rows where status ∈
{crash, checks_failed}. Agent is instructed to flag
`code=generation_failure, severity=high` when rate > 0.30.

Env:
    AUTORESEARCH_ALERT_BACKEND  claude (default) | codex | opencode
    AUTORESEARCH_ALERT_MODEL    explicit override
    AUTORESEARCH_ALERT_TIMEOUT  agent subprocess timeout (default 120s)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

# --- constants (ported from v1) ---------------------------------------------

_VALID_ALERT_CODES = frozenset({
    "inner_outer_drift",
    "uneven_generalization",
    "plateau",
    "collapse",
    "overfitting",
    "novelty_exhausted",
    "regression",
    "generation_failure",  # new: Stream A Bug 3 class
})
_VALID_SEVERITIES = frozenset({"low", "medium", "high"})
_ALERT_MAX_COUNT = 3
_ALERT_RECENT_WINDOW = 10  # rows from results.tsv to feed as trajectory
_ALERT_AGENT_TIMEOUT_DEFAULT = 120
_GENERATION_FAILURE_THRESHOLD = 0.30  # > 30% crash+checks_failed in last N

_TSV_COLUMNS = (
    "timestamp", "commit", "composite", "wall_time_s",
    "status", "description", "asi_json",
)


# --- pathing ----------------------------------------------------------------


def _repo_root() -> Path:
    override = os.environ.get("AUTORESEARCH_V2_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _tsv_path(lane: str) -> Path:
    return _repo_root() / "autoresearch_v2" / "lanes" / lane / "results.tsv"


def _alerts_path() -> Path:
    return _repo_root() / "autoresearch_v2" / "alerts.jsonl"


# --- trajectory loading -----------------------------------------------------


def read_trajectory(lane: str, n: int = _ALERT_RECENT_WINDOW) -> list[dict]:
    path = _tsv_path(lane)
    if not path.is_file():
        return []
    rows: list[dict] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        cells = cells + [""] * (len(header) - len(cells))
        row = dict(zip(header, cells, strict=False))
        rows.append(row)
    return rows[-n:]


def _to_float(s: str) -> float | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def variant_output_failure_rate(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    failures = sum(1 for r in rows if r.get("status") in {"crash", "checks_failed"})
    return failures / len(rows)


# --- prompt building --------------------------------------------------------


_ALERT_PROMPT_TEMPLATE = """You are a drift / overfitting / collapse monitor for autoresearch evolution.

Lane: {lane}
Variant-output-failure rate (last {window} rows): {failure_rate:.2f}
  (> 0.30 is a strong generation_failure signal — Stream A Bug 3 class)

Recent trajectory (last {window} attempts, oldest -> newest):
{trajectory}

Decide whether any drift / collapse / plateau / generation-failure signal is
worth flagging. Your judgment STANDS — no threshold backstop runs alongside
you. Under-flag and real regressions land silently; over-flag and the
operator stops trusting alerts.

Flag generation_failure ONLY when failure_rate > 0.30 (severity=high).
Flag collapse only when composite dropped sharply across consecutive keeps
(>= 30% drop is the v176/v177 class).
Flag plateau when the last 5 keep-composites are within 5% of each other.
Return [] when nothing is worth flagging — empty is the expected answer
most of the time.

Return STRICT JSON: an array (0 to {max_alerts} items) of alert objects:
[
  {{"code": "collapse" | "regression" | "drift" | "plateau" | "overfitting"
           | "novelty_exhausted" | "generation_failure" | "inner_outer_drift"
           | "uneven_generalization",
    "severity": "low" | "medium" | "high",
    "variant_id": "<commit sha or null>",
    "detail": "<1-2 sentence plain English>",
    "confidence": "low" | "medium" | "high"}}
]

Return ONLY the JSON array with no surrounding prose or code fences.
"""


def _build_alert_prompt(lane: str, rows: list[dict]) -> str:
    """Build the alert-agent prompt. Trajectory-only context — NO Pearson,
    keep-rate, or per-generation aggregation fields (per v2 plan U6)."""
    failure_rate = variant_output_failure_rate(rows)
    trajectory_lines = [
        f"  ts={r.get('timestamp')} sha={r.get('commit', '')[:8]} "
        f"composite={r.get('composite') or '-'} status={r.get('status')} "
        f"desc=\"{(r.get('description') or '')[:80]}\""
        for r in rows
    ]
    trajectory = "\n".join(trajectory_lines) if trajectory_lines else "  (no prior rows for this lane)"
    return _ALERT_PROMPT_TEMPLATE.format(
        lane=lane,
        window=len(rows),
        failure_rate=failure_rate,
        trajectory=trajectory,
        max_alerts=_ALERT_MAX_COUNT,
    )


# --- agent invocation -------------------------------------------------------


def _alert_agent_model() -> str:
    explicit = os.environ.get("AUTORESEARCH_ALERT_MODEL")
    if explicit:
        return explicit
    backend = (os.environ.get("AUTORESEARCH_ALERT_BACKEND") or "claude").strip().lower()
    if backend == "opencode":
        return os.environ.get(
            "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
            "openrouter/deepseek/deepseek-v4-pro",
        )
    if backend == "codex":
        return "gpt-5.5"
    return "sonnet"


def _build_alert_cmd(backend: str, model: str, prompt: str) -> list[str]:
    if backend == "opencode":
        return ["opencode", "run", "--dangerously-skip-permissions",
                "-m", model, "--format", "json", prompt]
    if backend == "claude":
        return ["claude", "-p", prompt, "--output-format", "json",
                "--session-id", str(uuid.uuid4()),
                "--model", model, "--dangerously-skip-permissions"]
    if backend == "codex":
        return ["codex", "exec", "--model", model, "--sandbox", "read-only",
                "--color", "never", "--ephemeral",
                "-c", 'approval_policy="never"',
                "-c", 'otel.exporter="none"',
                prompt]
    raise RuntimeError(
        f"AUTORESEARCH_ALERT_BACKEND={backend!r} not supported "
        f"(must be claude, codex, or opencode)"
    )


def _extract_json_array(text: str) -> list[dict]:
    """Pull the JSON array out of an LLM response. Tolerates leading/trailing
    prose despite the prompt asking for JSON only."""
    text = text.strip()
    if text.startswith("```"):
        # Strip fenced code blocks
        first_nl = text.find("\n")
        text = text[first_nl + 1 :] if first_nl != -1 else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON array found in response: {text[:200]!r}")
    blob = text[start : end + 1]
    try:
        data = json.loads(blob)
    except json.JSONDecodeError as e:
        raise ValueError(f"malformed JSON array: {e}") from e
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array, got {type(data).__name__}")
    return data


def _validate_alert(item: Any) -> dict | None:
    """Return a normalised alert dict or None if invalid."""
    if not isinstance(item, dict):
        return None
    code = item.get("code")
    severity = item.get("severity")
    if code not in _VALID_ALERT_CODES or severity not in _VALID_SEVERITIES:
        return None
    detail = item.get("detail")
    if not isinstance(detail, str) or not detail.strip():
        return None
    confidence = item.get("confidence") if item.get("confidence") in _VALID_SEVERITIES else "medium"
    return {
        "code": code,
        "severity": severity,
        "variant_id": item.get("variant_id"),
        "detail": detail.strip(),
        "confidence": confidence,
        "source": "agent",
    }


def _run_alert_agent_subprocess(prompt: str, *, model: str, timeout: int, backend: str) -> str:
    cmd = _build_alert_cmd(backend, model, prompt)
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"alert agent exit={proc.returncode}: {(proc.stderr or '')[:400]}")
    out = proc.stdout or ""
    if backend == "claude":
        try:
            envelope = json.loads(out)
            return envelope.get("result", out) if isinstance(envelope, dict) else out
        except json.JSONDecodeError:
            return out
    if backend == "opencode":
        last_text = ""
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            part = event.get("part") or {}
            text = part.get("text") if isinstance(part, dict) else None
            if isinstance(text, str):
                last_text = text
        return last_text or out
    return out


# --- main entry -------------------------------------------------------------


def alert_check(
    *,
    lane: str,
    agent_caller: Callable[[str], str] | None = None,
    write_alerts: bool = True,
) -> dict[str, Any]:
    """Run the alert agent over the last N rows for `lane`.
    `agent_caller(prompt)` returns the raw assistant response (test injection).
    """
    rows = read_trajectory(lane)
    if len(rows) < 3:
        return {
            "lane": lane,
            "rows_seen": len(rows),
            "alerts": [],
            "skipped": "insufficient_trajectory (<3 rows)",
        }

    prompt = _build_alert_prompt(lane, rows)

    if agent_caller is None:
        backend = (os.environ.get("AUTORESEARCH_ALERT_BACKEND") or "claude").strip().lower()
        model = _alert_agent_model()
        timeout = int(os.environ.get("AUTORESEARCH_ALERT_TIMEOUT", _ALERT_AGENT_TIMEOUT_DEFAULT))
        def agent_caller(p: str) -> str:
            return _run_alert_agent_subprocess(p, model=model, timeout=timeout, backend=backend)

    try:
        raw = agent_caller(prompt)
    except Exception as exc:
        sys.stderr.write(f"alert_check: agent call failed: {exc}\n")
        return {"lane": lane, "rows_seen": len(rows), "alerts": [], "error": str(exc)[:300]}

    try:
        parsed = _extract_json_array(raw)
    except ValueError as exc:
        sys.stderr.write(f"alert_check: malformed agent response: {exc}\n")
        return {"lane": lane, "rows_seen": len(rows), "alerts": [], "error": str(exc)[:300]}

    valid: list[dict] = []
    for item in parsed[:_ALERT_MAX_COUNT]:
        norm = _validate_alert(item)
        if norm is None:
            continue
        norm["lane"] = lane
        norm["timestamp"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        valid.append(norm)

    if write_alerts:
        for alert in valid:
            if alert["severity"] in {"medium", "high"}:
                _append_alert(alert)

    return {"lane": lane, "rows_seen": len(rows), "alerts": valid}


def _append_alert(alert: dict) -> None:
    path = _alerts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, separators=(",", ":")) + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="LLM alert agent over results.tsv trajectory")
    p.add_argument("--lane", required=True)
    p.add_argument("--no-write", action="store_true",
                   help="Don't append alerts to alerts.jsonl")
    args = p.parse_args(argv)

    result = alert_check(lane=args.lane, write_alerts=not args.no_write)
    print(json.dumps(result, indent=2))
    return 0  # always exit 0 — alerts are informational


if __name__ == "__main__":
    sys.exit(main())
