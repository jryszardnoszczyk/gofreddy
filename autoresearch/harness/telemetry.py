"""Freddy tracking -- push session and iteration events to the backend."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HARNESS_DIR = Path(__file__).resolve().parent
AUTORESEARCH_DIR = HARNESS_DIR.parent
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import harness  # noqa: F401,E402  # ensure package-level path setup runs

# watchdog (the autoresearch-internal one under archive/current_runtime/scripts)
# is used only by push_phase_event.  Importing it eagerly is fragile: the pip
# package `watchdog` (filesystem watcher) shadows the internal module during
# test runs where site-packages is on sys.path.  Import lazily so compute_inner_keep_rate
# — which has no watchdog dependency — is usable from any context.


def tracking_start(client: str, session_type: str, purpose: str) -> str | None:
    """Start freddy tracking session. Returns session_id or None."""
    if not shutil.which("freddy"):
        return None
    try:
        result = subprocess.run(
            ["freddy", "session", "start", "--client", client, "--type", session_type, "--purpose", purpose],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                return data.get("id")
            except json.JSONDecodeError:
                match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", result.stdout)
                return match.group(0) if match else None
    except Exception:
        pass
    return None


def tracking_end(session_id: str | None, summary: str):
    """End freddy tracking session."""
    if not session_id:
        return
    try:
        subprocess.run(
            ["freddy", "session", "end", "--session-id", session_id, "--summary", summary],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        pass


def push_iteration(session_id: str | None, number: int, session_dir: Path,
                   exit_code: int, duration_ms: int, log_path: Path):
    """Push iteration data to freddy backend. Non-fatal."""
    if not shutil.which("freddy"):
        return
    try:
        results_file = session_dir / "results.jsonl"
        last_line = ""
        if results_file.exists():
            lines = results_file.read_text().strip().splitlines()
            if lines:
                last_line = lines[-1]

        iter_type = "unknown"
        if last_line:
            try:
                iter_type = json.loads(last_line).get("type", "unknown")
            except json.JSONDecodeError:
                pass

        if exit_code == 0:
            status = "success"
        elif exit_code == 124:
            status = "timeout"
        else:
            status = "failed"

        cmd = ["freddy", "iteration", "push",
               "--number", str(number), "--type", iter_type,
               "--status", status, "--exit-code", str(exit_code),
               "--duration-ms", str(duration_ms),
               "--state-file", str(session_dir / "session.md"),
               "--log-file", str(log_path)]
        if last_line:
            cmd += ["--result", last_line]
        if session_id:
            cmd += ["--session-id", session_id]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def compute_inner_keep_rate(variant_dir: Path) -> dict[str, dict[str, Any]]:
    """Count inner-loop KEEP / REWORK / DISCARD decisions per session dir.

    Reads every `.last_eval_cache.json` under `sessions/*/*/` and aggregates the
    ``decision`` field across cached evaluations. The result feeds the outer
    ``inner_metrics`` block in scores.json and is the input for cross-generation
    inner-outer correlation tracking.

    Parse failures are counted and surfaced via stderr so silent cache-format
    drift doesn't quietly zero the keep_rate — that's exactly the failure mode
    this metric exists to catch.
    """
    rates: dict[str, dict[str, Any]] = {}
    for session_dir in variant_dir.glob("sessions/*/*"):
        if not session_dir.is_dir():
            continue
        cache_file = session_dir / ".last_eval_cache.json"
        if not cache_file.exists():
            continue
        try:
            cache = json.loads(cache_file.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  warning: cannot read {cache_file}: {exc}", file=sys.stderr)
            continue
        if not isinstance(cache, dict):
            continue
        decisions: list[str] = []
        parse_errors = 0
        for entry in cache.values():
            stdout = entry.get("stdout") if isinstance(entry, dict) else None
            if not stdout:
                continue
            try:
                decoded = json.loads(stdout)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            decision = decoded.get("decision") if isinstance(decoded, dict) else None
            if decision is None:
                parse_errors += 1
                continue
            decisions.append(decision)
        if parse_errors:
            rel = session_dir.relative_to(variant_dir)
            print(
                f"  warning: {parse_errors} unparseable cache entries in {rel}",
                file=sys.stderr,
            )
        total = len(decisions)
        if not total:
            continue
        keeps = sum(1 for d in decisions if d == "KEEP")
        reworks = sum(1 for d in decisions if d == "REWORK")
        discards = sum(1 for d in decisions if d == "DISCARD")
        rates[str(session_dir.relative_to(variant_dir))] = {
            "keeps": keeps,
            "reworks": reworks,
            "discards": discards,
            "total": total,
            "keep_rate": round(keeps / total, 3),
        }
    return rates


def push_phase_event(session_id: str | None, number: int, session_dir: Path, raw_result_line: str,
                     result_entry: dict, duration_ms: int, log_path: Path, exit_code: int = 0):
    """Push one multi-turn phase event to freddy backend. Non-fatal."""
    if not shutil.which("freddy"):
        return
    try:
        from watchdog import phase_type, tracking_status_from_entry  # type: ignore
        cmd = ["freddy", "iteration", "push",
               "--number", str(number),
               "--type", phase_type(result_entry),
               "--status", tracking_status_from_entry(result_entry),
               "--exit-code", str(exit_code),
               "--duration-ms", str(duration_ms),
               "--state-file", str(session_dir / "session.md"),
               "--log-file", str(log_path),
               "--result", raw_result_line]
        if session_id:
            cmd += ["--session-id", session_id]
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception:
        pass
