"""Per-stage cost observability hook (master plan §3.9).

L3 ships the data points only — full Slack thresholds + breaker logic is L5.
This module provides ``record_stage_cost(audit_dir, stage, cost_usd)`` which
appends to ``cost_actual.json`` per stage, recomputing ``total_so_far``.

File format (master plan §3.9):

    {
      "stage_1a_warmup": 3.42,
      "stage_1b_predischarge": 4.10,
      "stage_1c_brief": 0.85,
      "stage_2_findability": 47.20,
      "stage_2_narrative": 31.50,
      "stage_2_acquisition": 38.10,
      "stage_2_experience": 62.30,
      "stage_3_synthesis": 12.40,
      "stage_4_proposal": 7.05,
      "total_so_far": 206.92
    }

Calls accumulate within a stage (multiple calls per stage just add); the
``total_so_far`` is recomputed on each write so a partial-fail leaves a
consistent file. No locking — single-process v1 contract (LHR D3).

L5 will read this file in ``stages.run_pipeline`` to fire the $200 / $400
Slack thresholds (master plan §5.7); L4's first-runnable test only verifies
the file exists with the expected per-stage keys after a dry run.
"""
from __future__ import annotations

import json
from pathlib import Path

COST_FILE_NAME = "cost_actual.json"


def cost_file_path(audit_dir: Path) -> Path:
    """Resolve the cost ledger path relative to an audit directory."""
    return Path(audit_dir) / COST_FILE_NAME


def read_cost_actual(audit_dir: Path) -> dict[str, float]:
    """Read the current per-stage cost map. Returns ``{}`` if absent or
    corrupt (callers can write without pre-checking existence)."""
    path = cost_file_path(audit_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def record_stage_cost(
    audit_dir: Path,
    stage: str,
    cost_usd: float,
    *,
    accumulate: bool = True,
) -> dict[str, float]:
    """Record a per-stage cost data point.

    By default the call **adds** to any existing value for ``stage`` —
    mirrors the natural pattern where Stage 2's 4 sub-agents each record
    their own slice (e.g. ``stage_2_findability``) AND a Stage-2 wrapper
    might also write a ``stage_2`` aggregate. With ``accumulate=False``
    the prior value is overwritten — useful for callers that want a
    single authoritative number per stage.

    Returns the on-disk dict after the write so callers can log + assert.
    """
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    path = cost_file_path(audit_dir)
    current = read_cost_actual(audit_dir)
    cost_clean = float(cost_usd) if cost_usd > 0 else 0.0

    if accumulate and stage in current:
        current[stage] = round(current[stage] + cost_clean, 4)
    else:
        current[stage] = round(cost_clean, 4)

    # Recompute total_so_far across all stage keys (excluding the total itself).
    total = sum(v for k, v in current.items() if k != "total_so_far")
    current["total_so_far"] = round(total, 4)

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    return current


__all__ = ["cost_file_path", "read_cost_actual", "record_stage_cost"]
