#!/usr/bin/env python3
"""Lane-aware frontier helpers for autoresearch variants.

Phase 2 (Unit 4) replaced the 3-objective Pareto machinery with a single
per-lane scalar selection: each lane keeps its single best variant by
`objective_score`. The accessors below are still imported by
`select_parent.py` (Hyperagents §A.2 sigmoid+novelty selector) and the
archive tooling, so renames are intentionally avoided.
"""

from __future__ import annotations

from typing import Any

DOMAINS = ("geo", "competitive", "monitoring", "storyboard")
LANES = ("core", *DOMAINS)
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


def entry_lane(entry: dict[str, Any]) -> str:
    raw_lane = str(entry.get("lane") or "").strip().lower()
    return raw_lane or "core"


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

    `core` lane ranks by composite; workflow lanes rank by their domain score.
    This is the canonical "best in lane" ordering used by `best_variant_in_lane`
    and the archive CLI.
    """
    lane = entry_lane(entry)
    if lane == "core":
        return composite_score(entry)
    return domain_score(entry, lane)


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
