#!/usr/bin/env python3
"""Produce session_summary.json from session artifacts.

Called by the archive runner at the end of each domain session.

Usage:
    python3 summarize_session.py <session_dir> <domain> <client>
"""

import json
import os
import shutil
import sys
import re
from pathlib import Path
from datetime import datetime, timezone

ARCHIVE_ROOT = Path(__file__).resolve().parent.parent
if str(ARCHIVE_ROOT) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_ROOT))

from workflows import get_workflow_spec


def _extract_score(val):
    """Extract a single score from flat number or nested dict."""
    if isinstance(val, dict):
        values = [v for v in val.values() if isinstance(v, (int, float))]
        if not values:
            return None
        return sum(values) / len(values)
    if isinstance(val, (int, float)):
        return float(val)
    return None


def summarize(session_dir: str, domain: str, client: str) -> dict:
    session_path = Path(session_dir)

    # Parse results.jsonl
    results_file = session_path / "results.jsonl"
    results = []
    if results_file.exists():
        for line in results_file.read_text().strip().split("\n"):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Parse session.md for status. Recognize BLOCKED alongside COMPLETE /
    # IN_PROGRESS — the original version silently mapped BLOCKED to
    # "UNKNOWN", which propagated corrupted state into every downstream
    # report consumer (4 generate_report.py scripts + report_base.py +
    # archive_index.py).
    session_md = session_path / "session.md"
    status = "UNKNOWN"
    if session_md.exists():
        text = session_md.read_text()
        if "## Status: COMPLETE" in text:
            status = "COMPLETE"
        elif "## Status: BLOCKED" in text:
            status = "BLOCKED"
        elif "## Status: IN_PROGRESS" in text or "## Status: RUNNING" in text:
            status = "IN_PROGRESS"

    # Count iterations by status. `total` counts DISTINCT iteration numbers
    # (not results.jsonl lines) because a single iteration can write multiple
    # phase entries (e.g., storyboard iter 4 writes 3 rows for one blocked
    # iteration). Agent statuses in the wild include `done`, `error`,
    # `complete`, `kept`, `blocked`, `failed`, and `skipped` — the original
    # map only handled the last five, silently dropping `done`/`error` and
    # breaking arithmetic reconciliation downstream. Any unrecognized status
    # is counted in `uncategorized` so the arithmetic still reconciles.
    distinct_iters = {r.get("iteration") for r in results if r.get("iteration") is not None}
    iterations = {
        "total": len(distinct_iters) if distinct_iters else len(results),
        "productive": 0,
        "blocked": 0,
        "failed": 0,
        "skipped": 0,
        "uncategorized": 0,
    }
    errors: dict[str, dict] = {}
    for r in results:
        s = r.get("status", "")
        if s in ("complete", "kept", "done"):
            iterations["productive"] += 1
        elif s == "blocked":
            iterations["blocked"] += 1
        elif s in ("failed", "error"):
            iterations["failed"] += 1
        elif s == "skipped":
            iterations["skipped"] += 1
        else:
            iterations["uncategorized"] += 1

        # Aggregate errors
        err = r.get("error")
        if err and isinstance(err, dict):
            key = f"{err.get('category', 'UNKNOWN')}:{err.get('code', err.get('message', 'unknown'))}"
            if key not in errors:
                errors[key] = {**err, "count": 0}
            errors[key]["count"] += err.get("repeat_count", 1)

    # Count findings
    findings_file = session_path / "findings.md"
    findings_count = 0
    if findings_file.exists():
        findings_count = len(re.findall(r"^### \[", findings_file.read_text(), re.MULTILINE))

    deliverables = get_workflow_spec(domain).list_deliverables(session_path)

    # Quality metrics from before/after deltas (handles nested dict scores)
    befores = [_extract_score(r["before"]) for r in results if r.get("before") is not None]
    afters = [_extract_score(r["after"]) for r in results if r.get("after") is not None]
    deltas_raw = [r.get("delta") for r in results if r.get("delta") is not None]
    deltas = [_extract_score(d) if isinstance(d, dict) else d for d in deltas_raw]

    # Filter out None values from failed extraction
    befores = [b for b in befores if b is not None]
    afters = [a for a in afters if a is not None]
    deltas = [d for d in deltas if d is not None]

    quality_metrics: dict = {
        "avg_before": round(sum(befores) / len(befores), 3) if befores else None,
        "avg_after": round(sum(afters) / len(afters), 3) if afters else None,
        "avg_delta": round(sum(deltas) / len(deltas), 3) if deltas else None,
    }

    get_workflow_spec(domain).augment_quality_metrics(results, quality_metrics)

    return {
        "domain": domain,
        "client": client,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "iterations": iterations,
        "exit_reason": status,
        "errors": list(errors.values()),
        "deliverables": deliverables,
        "findings_count": findings_count,
        "quality_metrics": quality_metrics,
    }


def append_metrics(summary: dict, domain: str, client: str, session_dir: str) -> None:
    """Append one JSONL line to archive-local metrics storage. Non-fatal."""
    try:
        archive_root = Path(__file__).resolve().parent.parent
        metrics_dir = archive_root / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        metrics_file = metrics_dir / f"{domain}.jsonl"
        qm = summary.get("quality_metrics", {})
        backend = os.environ.get("AUTORESEARCH_SESSION_BACKEND", "").strip().lower()
        if backend not in {"claude", "codex"}:
            backend = "codex" if shutil.which("codex") else "claude"
        default_model = os.environ.get("SESSION_MODEL", "sonnet") if backend == "claude" else "gpt-5.4"
        entry = {
            "domain": domain,
            "client": client,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "avg_delta": qm.get("avg_delta"),
            "avg_before": qm.get("avg_before"),
            "avg_after": qm.get("avg_after"),
            "avg_quality_score": qm.get("avg_quality_score"),  # #36
            "dqs_score": qm.get("dqs_score"),
            "findings_count": summary.get("findings_count", 0),
            "iterations_total": summary.get("iterations", {}).get("total", 0),
            "iterations_productive": summary.get("iterations", {}).get("productive", 0),
            "model": os.environ.get("AUTORESEARCH_SESSION_MODEL", default_model),
            "status": summary.get("status", "unknown"),
            "wall_time_seconds": summary.get("wall_time_seconds"),
            "cost_estimate": summary.get("cost_estimate"),
        }
        with open(metrics_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"WARNING: metrics append failed: {e}", file=sys.stderr)


def summarize_all(sessions_dir: str) -> None:
    """Summarize all sessions across all domains. For N: pipeline observability."""
    sessions_path = Path(sessions_dir)
    total = passed = failed = skipped = 0
    for domain_dir in sorted(sessions_path.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        domain = domain_dir.name
        for client_dir in sorted(domain_dir.iterdir()):
            if not client_dir.is_dir():
                continue
            client = client_dir.name
            total += 1
            session_md = client_dir / "session.md"
            if not session_md.exists():
                skipped += 1
                continue
            text = session_md.read_text()
            if "## Status: COMPLETE" in text:
                passed += 1
            else:
                failed += 1
                print(f"  INCOMPLETE: {domain}/{client}", file=sys.stderr)
    print(f"\nAggregate: {total} sessions, {passed} complete, {failed} incomplete, {skipped} skipped")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        summarize_all(sys.argv[2])
        sys.exit(0)

    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <session_dir> <domain> <client>", file=sys.stderr)
        print(f"       {sys.argv[0]} --all <sessions_dir>", file=sys.stderr)
        sys.exit(1)
    session_dir, domain, client = sys.argv[1], sys.argv[2], sys.argv[3]
    summary = summarize(session_dir, domain, client)
    output_path = Path(session_dir) / "session_summary.json"
    # Atomic write: write to .tmp then rename
    tmp_path = output_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(summary, indent=2) + "\n")
    tmp_path.rename(output_path)
    print(f"Written: {output_path}")
    append_metrics(summary, domain, client, session_dir)
