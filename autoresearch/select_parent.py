#!/usr/bin/env python3
"""Agent-driven parent selection for autoresearch evolution (R-#29).

Replaces the hand-tuned ``sigmoid(lambda*(score-midpoint)) * exp(-(children/8)^3)``
scoring with an AsyncOpenAI + Pydantic call that picks the parent from the
top-K eligible variants + trajectory context. Per plan: no sigmoid fallback —
agent failure = generation failure, and the meta-agent retries on the next
cycle. The agent's rationale lands in ``lineage.jsonl`` on the child entry
(``selection_rationale`` field, wired by ``evolve.py``).
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from archive_index import ordered_latest_entries
from frontier import composite_score, domain_score, has_search_metrics
from lane_paths import normalize_lane


# Top-K eligible variants shown to the agent. Current eligible pool is rarely
# larger than 8 post-discard (see cluster-4 doc).
TOP_K_CANDIDATES = 8

# Recent generation rows shown to the agent as trajectory context.
TRAJECTORY_WINDOW = 3


def _objective_score(entry: dict, lane: str) -> float:
    if lane == "core":
        return float(composite_score(entry) or 0.0)
    return float(domain_score(entry, lane) or 0.0)


def _entry_lane(entry: dict) -> str:
    return str(entry.get("lane") or "").strip().lower() or "core"


def _safe_mean(values: list[float]) -> float | None:
    vals = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.mean(vals), 4) if vals else None


def _build_candidate_row(entry: dict, lane: str, latest: dict[str, dict]) -> dict[str, Any]:
    """Build the compact per-candidate summary the agent reasons over.

    ``latest`` is the archive-wide latest-lineage map, used to surface children
    deltas + best-child score. Only uses fields already present on lineage
    entries, so no new disk reads are required.
    """
    entry_id = str(entry.get("id"))
    score = _objective_score(entry, lane)
    children = int(entry.get("children", 0) or 0)

    inner = entry.get("inner_metrics") or {}
    mean_keep_vals = [
        float(v.get("keep_rate"))
        for v in inner.values()
        if isinstance(v, dict) and isinstance(v.get("keep_rate"), (int, float))
    ]
    mean_keep = round(statistics.mean(mean_keep_vals), 4) if mean_keep_vals else None

    fixture_sds = [
        float(v.get("fixture_sd"))
        for v in (entry.get("domains") or {}).values()
        if isinstance(v, dict) and isinstance(v.get("fixture_sd"), (int, float))
    ]
    max_fixture_sd = round(max(fixture_sds), 4) if fixture_sds else 0.0

    # Children composite deltas vs. this parent + best child score.
    children_deltas: list[float] = []
    best_child_score: float | None = None
    for other in latest.values():
        if str(other.get("parent")) != entry_id:
            continue
        child_score = _objective_score(other, lane)
        if best_child_score is None or child_score > best_child_score:
            best_child_score = child_score
        children_deltas.append(round(child_score - score, 4))

    # Status hint for the agent (used by the prompt to mark plateau vs. new vs. exploited).
    if children == 0:
        status = "new"
    elif children_deltas and statistics.pstdev(children_deltas) < 0.01 and len(children_deltas) >= 4:
        status = "plateau"
    elif best_child_score is not None and best_child_score > score:
        status = "exploited"
    else:
        status = "stalled"

    return {
        "id": entry_id,
        "score": round(score, 4),
        "children": children,
        "mean_keep": mean_keep,
        "max_fixture_sd": max_fixture_sd,
        "children_deltas": children_deltas,
        "best_child_score": round(best_child_score, 4) if best_child_score is not None else None,
        "status": status,
    }


def _load_recent_gen_rows(lane: str, window: int = TRAJECTORY_WINDOW) -> list[dict[str, Any]]:
    """Load the last N rows from ``metrics/generations.jsonl`` for this lane.

    Returns an empty list on cold start so the agent's prompt degrades
    gracefully. Failures to read are non-fatal (empty list).
    """
    metrics_path = SCRIPT_DIR / "metrics" / "generations.jsonl"
    if not metrics_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in metrics_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lane") == lane:
                # Strip the verbose per-variant rows — the agent only needs
                # aggregate trajectory signal.
                rows.append({
                    "gen_id": entry.get("gen_id"),
                    "mean_composite": entry.get("mean_composite"),
                    "mean_keep": entry.get("mean_keep"),
                    "inner_outer_corr": entry.get("inner_outer_corr"),
                })
    except OSError:
        return []
    return rows[-window:]


def _pick_parent_via_agent(
    candidates: list[dict[str, Any]],
    gen_rows: list[dict[str, Any]],
    lane: str,
) -> tuple[str, str]:
    """Call the AsyncOpenAI agent and return ``(parent_id, rationale)``.

    No fallback — any exception propagates up to the caller.
    """
    from agent_calls import select_parent_agent

    result = asyncio.run(select_parent_agent(candidates, gen_rows, lane))
    eligible_ids = {c["id"] for c in candidates}
    if result.parent_id not in eligible_ids:
        raise ValueError(
            f"agent picked parent_id={result.parent_id!r} which is not in "
            f"the top-{len(candidates)} eligibility set {sorted(eligible_ids)!r}"
        )
    return result.parent_id, result.rationale


def select_parent(
    archive_dir: str,
    suite_id: str | None = None,
    lane: str = "core",
    *,
    return_rationale: bool = False,
) -> str | tuple[str, str | None]:
    """Pick a parent variant for the next evolution generation.

    With ``return_rationale=False`` (default, backwards-compatible), returns
    the parent path string. With ``return_rationale=True``, returns
    ``(parent_path, rationale_or_none)`` — rationale is ``None`` on the
    zero-eligible baseline-seed fallback path.
    """
    archive_root = Path(archive_dir).resolve()
    lane = normalize_lane(lane)
    all_entries = ordered_latest_entries(archive_root)
    all_eligible = [
        entry
        for entry in all_entries
        if entry.get("status") != "discarded" and has_search_metrics(entry, suite_id=suite_id)
    ]
    lane_entries = [entry for entry in all_eligible if _entry_lane(entry) == lane]
    eligible = lane_entries or all_eligible

    if not eligible:
        # Zero-eligible lane: fall through to the baseline-seed path from R10.
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
        parent_path = str(archive_root / seed["id"])
        return (parent_path, None) if return_rationale else parent_path

    # Rank by objective score, take top-K.
    eligible_sorted = sorted(
        eligible, key=lambda e: _objective_score(e, lane), reverse=True,
    )
    top_k = eligible_sorted[:TOP_K_CANDIDATES]

    latest_map = {str(e.get("id")): e for e in all_entries if e.get("id")}
    candidates = [_build_candidate_row(entry, lane, latest_map) for entry in top_k]
    gen_rows = _load_recent_gen_rows(lane)

    parent_id, rationale = _pick_parent_via_agent(candidates, gen_rows, lane)
    parent_path = str(archive_root / parent_id)
    return (parent_path, rationale) if return_rationale else parent_path


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
