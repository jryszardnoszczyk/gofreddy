"""Per-stage cost observability hook (master plan §3.9).

Appends to ``cost_actual.json`` per stage; recomputes ``total_so_far`` on
each write. Single-process v1 contract per LHR D3 — no locking, no atomic
rename. L5 will read this file in ``stages.run_pipeline`` to fire $200/$400
Slack thresholds; L4's first-runnable test only verifies the file exists
with the expected per-stage keys after a dry run.
"""
from __future__ import annotations

import json
from pathlib import Path

COST_FILE_NAME = "cost_actual.json"


def cost_file_path(audit_dir: Path) -> Path:
    return Path(audit_dir) / COST_FILE_NAME


def read_cost_actual(audit_dir: Path) -> dict[str, float]:
    path = cost_file_path(audit_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def record_stage_cost(audit_dir: Path, stage: str, cost_usd: float) -> dict[str, float]:
    """Add ``cost_usd`` to ``stage`` and rewrite the file (recomputes total)."""
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    current = read_cost_actual(audit_dir)
    current[stage] = round(current.get(stage, 0.0) + max(float(cost_usd), 0.0), 4)
    current["total_so_far"] = round(sum(v for k, v in current.items() if k != "total_so_far"), 4)
    cost_file_path(audit_dir).write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    return current


__all__ = ["cost_file_path", "read_cost_actual", "record_stage_cost"]
