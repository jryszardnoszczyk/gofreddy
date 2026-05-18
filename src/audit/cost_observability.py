"""Per-stage cost observability + threshold alerts (master plan §3.9, §5.7).

Appends to ``cost_actual.json`` per stage and recomputes ``total_so_far``
on each write. When the running total crosses $200 or $400 for the first
time in an audit, posts a Slack alert to ``SLACK_WEBHOOK_COST`` (if set)
and emits a ``moment`` event with ``moment_kind=cost_milestone`` via
``log_to_audit`` (per portal-moments plan Unit 1 / TD-56 — no wrapper).

Single-process v1 contract per LHR D3 — no locking, no atomic rename.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx

from src.audit.events import log_to_audit

COST_FILE_NAME = "cost_actual.json"
COST_THRESHOLDS_USD = (200.0, 400.0)

logger = logging.getLogger(__name__)


def cost_file_path(audit_dir: Path) -> Path:
    return Path(audit_dir) / COST_FILE_NAME


def read_cost_actual(audit_dir: Path) -> dict[str, float]:
    path = cost_file_path(audit_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def record_stage_cost(audit_dir: Path, stage: str, cost_usd: float) -> dict[str, float]:
    """Add ``cost_usd`` to ``stage``, rewrite cost_actual.json, emit events,
    and fire Slack threshold alerts if a $200/$400 boundary just crossed."""
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    current = read_cost_actual(audit_dir)
    prev_total = float(current.get("total_so_far", 0.0))
    current[stage] = round(current.get(stage, 0.0) + max(float(cost_usd), 0.0), 4)
    new_total = round(sum(v for k, v in current.items() if k != "total_so_far"), 4)
    current["total_so_far"] = new_total
    cost_file_path(audit_dir).write_text(
        json.dumps(current, indent=2, sort_keys=True), encoding="utf-8"
    )

    log_to_audit(
        audit_dir, "cost_recorded",
        stage=stage, cost_usd=float(cost_usd), total_so_far=new_total,
    )
    _check_thresholds(audit_dir, prev_total, new_total)
    return current


def _check_thresholds(audit_dir: Path, prev_total: float, new_total: float) -> None:
    for threshold in COST_THRESHOLDS_USD:
        if prev_total < threshold <= new_total:
            log_to_audit(
                audit_dir,
                "moment",
                metadata={
                    "moment_kind": "cost_milestone",
                    "title": f"Cost threshold crossed: ${threshold:.2f}",
                    "threshold_usd": threshold,
                    "total_so_far": new_total,
                },
            )
            url = os.environ.get("SLACK_WEBHOOK_COST", "").strip()
            if not url:
                continue
            try:
                httpx.post(
                    url,
                    json={"text": (
                        f"Audit `{audit_dir.name}` crossed ${int(threshold)} "
                        f"cost threshold (now ${new_total:.2f})"
                    )},
                    timeout=5.0,
                )
            except Exception:
                logger.exception("cost-threshold slack ping failed")


__all__ = ["COST_THRESHOLDS_USD", "cost_file_path", "read_cost_actual", "record_stage_cost"]
