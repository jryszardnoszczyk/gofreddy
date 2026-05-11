#!/usr/bin/env python3
"""Lane-aware frontier helpers for autoresearch variants.

Phase 2 (Unit 4) replaced the 3-objective Pareto machinery with a single
per-lane scalar selection: each lane keeps its single best variant by
`objective_score`. The accessors below are imported by
`evolve._select_parent_deterministic` (Plan B U5 replacement for the
deleted LLM picker) and archive tooling.
"""

from __future__ import annotations

from typing import Any

from lane_registry import (
    all_lane_names,
    default_objective_score_from_entry,
    workflow_lane_names,
)

DOMAINS = workflow_lane_names()
LANES = all_lane_names()
EPSILON = 1e-9


def _as_float(value: Any) -> float | None:
    # `bool` is a subclass of `int`, so the explicit branch keeps the intent
    # visible: True/False coerce to 1.0/0.0 (existing behavior — do not
    # silently start rejecting bools).
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _search_metrics(entry: dict[str, Any]) -> dict[str, Any]:
    raw = entry.get("search_metrics")
    return raw if isinstance(raw, dict) else {}


def entry_lane(entry: dict[str, Any] | None) -> str:
    raw_lane = ""
    if isinstance(entry, dict):
        raw_lane = str(entry.get("lane") or "").strip().lower()
    return raw_lane or "core"


def entry_active_for_lane(entry: dict[str, Any] | None, lane: str) -> bool:
    """True when ``entry`` has scoring data for the requested workflow lane.

    Multi-lane scoring tags v006 ``lane=core`` and ``load_latest_lineage``
    deduplicates by id, so the last-written entry overwrites prior
    per-workflow-lane entries. A label-only match (``entry_lane(entry) == lane``)
    therefore returns False for every workflow lane and the gate falls into
    A0 first-of-lane semantics that auto-promote.

    Fix: accept any entry whose ``search_metrics.domains[lane].active`` is
    truthy — the entry was actually scored on this lane regardless of label.
    Falls back to the lane-label match for legacy entries that lack
    ``search_metrics``. Hoisted from evaluate_variant / evolve_ops on
    2026-05-07 (D1) to eliminate hand-maintained triplication; the
    third caller (select_parent.py) was deleted in Plan B U5.
    """
    if not isinstance(entry, dict):
        return False
    metrics = entry.get("search_metrics")
    if isinstance(metrics, dict):
        domains = metrics.get("domains") or {}
        payload = domains.get(lane) or {}
        if isinstance(payload, dict) and payload.get("active"):
            return True
    return entry_lane(entry) == lane


def search_suite_id(entry: dict[str, Any]) -> str | None:
    suite_id = _search_metrics(entry).get("suite_id")
    if isinstance(suite_id, str) and suite_id:
        return suite_id
    return None


def has_search_metrics(entry: dict[str, Any], suite_id: str | None = None) -> bool:
    """True when the entry has real manifest-driven search metrics."""
    entry_suite_id = search_suite_id(entry)
    if entry_suite_id is None:
        return False
    if suite_id is not None and entry_suite_id != suite_id:
        return False
    return _as_float(_search_metrics(entry).get("composite")) is not None


def composite_score(entry: dict[str, Any]) -> float | None:
    return _as_float(_search_metrics(entry).get("composite"))


def domain_score(entry: dict[str, Any], domain: str) -> float | None:
    domains = _search_metrics(entry).get("domains")
    if isinstance(domains, dict):
        payload = domains.get(domain)
        if isinstance(payload, dict):
            return _as_float(payload.get("score"))
    return None


def wall_time_seconds(entry: dict[str, Any]) -> float | None:
    """Observability only — NOT a selection input after Phase 2."""
    return _as_float(_search_metrics(entry).get("wall_time_seconds"))


def objective_score(entry: dict[str, Any]) -> float | None:
    """Per-lane single-scalar selection signal.

    Thin wrapper around ``lane_registry.default_objective_score_from_entry``;
    divergent lanes can override via ``LaneSpec.custom_objective_score_from_entry``.
    """
    return default_objective_score_from_entry(entry, entry_lane(entry))


def entries_for_lane(
    entries: list[dict[str, Any]],
    lane: str,
) -> list[dict[str, Any]]:
    """Filter entries to a single lane, dropping discarded variants."""
    target = (lane or "core").strip().lower()
    return [
        entry
        for entry in entries
        if entry_lane(entry) == target and entry.get("status") != "discarded"
    ]


def best_variant_in_lane(
    entries: list[dict[str, Any]],
    lane: str,
    suite_id: str | None = None,
) -> dict[str, Any] | None:
    """Return the single highest-`objective_score` variant in `lane`, or None.

    `suite_id`, if given, restricts to entries whose `search_metrics.suite_id`
    matches — same semantics as `has_search_metrics`. Discarded variants are
    excluded via `entries_for_lane`.
    """
    scoped = [
        entry
        for entry in entries_for_lane(entries, lane)
        if has_search_metrics(entry, suite_id=suite_id)
        and objective_score(entry) is not None
    ]
    return max(
        scoped,
        key=lambda entry: objective_score(entry) or float("-inf"),
        default=None,
    )
