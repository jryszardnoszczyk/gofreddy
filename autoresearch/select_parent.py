#!/usr/bin/env python3
"""Handcrafted score-child-prop parent selection for autoresearch evolution."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from archive_index import ordered_latest_entries
from frontier import composite_score, domain_score, has_search_metrics
from lane_paths import normalize_lane


TOP_K_MIDPOINT = 3
SIGMOID_LAMBDA = 10.0


def _objective_score(entry: dict, lane: str) -> float:
    if lane == "core":
        return float(composite_score(entry) or 0.0)
    return float(domain_score(entry, lane) or 0.0)


def _selection_weight(entry: dict, midpoint: float, lane: str) -> float:
    score = _objective_score(entry, lane)
    children = int(entry.get("children", 0) or 0)
    sigmoid = 1.0 / (1.0 + math.exp(-SIGMOID_LAMBDA * (score - midpoint)))
    novelty = math.exp(-((children / 8.0) ** 3))
    return sigmoid * novelty


def _entry_lane(entry: dict) -> str:
    return str(entry.get("lane") or "").strip().lower() or "core"


def select_parent(archive_dir: str, suite_id: str | None = None, lane: str = "core") -> str:
    archive_root = Path(archive_dir).resolve()
    lane = normalize_lane(lane)
    all_eligible = [
        entry
        for entry in ordered_latest_entries(archive_root)
        if entry.get("status") != "discarded" and has_search_metrics(entry, suite_id=suite_id)
    ]
    lane_entries = [entry for entry in all_eligible if _entry_lane(entry) == lane]
    eligible = lane_entries or all_eligible
    if not eligible:
        # R10: baseline seed fallback — pick the earliest entry instead of dying
        all_entries = ordered_latest_entries(archive_root)
        lane_all = [e for e in all_entries if _entry_lane(e) == lane]
        fallback_pool = lane_all or list(all_entries)
        if not fallback_pool:
            raise SystemExit("No entries at all in lineage.jsonl")
        seed = fallback_pool[0]  # earliest by timestamp
        seed["composite_score"] = 0.0
        print(
            f"WARNING: no searchable variants for lane={lane!r}; "
            f"seeding from earliest entry {seed.get('id')!r} at score 0.0",
            file=sys.stderr,
        )
        return str(archive_root / seed["id"])

    top_scores = sorted((_objective_score(entry, lane) for entry in eligible), reverse=True)[:TOP_K_MIDPOINT]
    midpoint = sum(top_scores) / len(top_scores) if top_scores else 0.0
    weights = [_selection_weight(entry, midpoint, lane) for entry in eligible]
    if sum(weights) <= 0:
        weights = [1.0] * len(eligible)

    selected = random.choices(eligible, weights=weights, k=1)[0]
    return str(archive_root / selected["id"])


if __name__ == "__main__":
    if len(sys.argv) not in {2, 3, 4}:
        print(f"Usage: {sys.argv[0]} <archive_dir> [suite_id] [lane]", file=sys.stderr)
        raise SystemExit(1)
    print(
        select_parent(
            sys.argv[1],
            suite_id=sys.argv[2] if len(sys.argv) >= 3 else None,
            lane=sys.argv[3] if len(sys.argv) == 4 else "core",
        )
    )
