"""Phase 2 (Unit 4): per-lane scalar selection helpers in frontier.py.

The 3-objective Pareto machinery (`pareto_frontier`, `compute_frontiers`,
`frontier_membership_map`, `finalist_shortlist`, `FrontierSnapshot`) was
deleted. Selection within each lane is now `max(by objective_score)` via
`best_variant_in_lane`. Lane scoping is preserved — selection happens
WITHIN a lane, not across lanes.

`select_parent.py` (Hyperagents §A.2 sigmoid+novelty) is intentionally
unaffected and is verified by file hash in
`test_select_parent_unchanged_after_phase2`.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import frontier  # type: ignore
from frontier import (  # type: ignore
    LANES,
    best_variant_in_lane,
    composite_score,
    domain_score,
    entries_for_lane,
    has_search_metrics,
    objective_score,
)


# ── Test fixtures ───────────────────────────────────────────────────────────


def _entry(
    variant_id: str,
    lane: str,
    *,
    composite: float | None = None,
    geo: float | None = None,
    competitive: float | None = None,
    monitoring: float | None = None,
    storyboard: float | None = None,
    suite_id: str = "search-v1",
    status: str | None = None,
) -> dict:
    domains = {}
    for name, score in (
        ("geo", geo),
        ("competitive", competitive),
        ("monitoring", monitoring),
        ("storyboard", storyboard),
    ):
        domains[name] = {"score": score if score is not None else 0.0}
    entry: dict = {
        "id": variant_id,
        "lane": lane,
        "search_metrics": {
            "suite_id": suite_id,
            "composite": composite if composite is not None else 0.0,
            "domains": domains,
        },
    }
    if status:
        entry["status"] = status
    return entry


# ── entries_for_lane ────────────────────────────────────────────────────────


def test_entries_for_lane_filters_to_lane_and_drops_discarded() -> None:
    entries = [
        _entry("v001", "core", composite=0.5),
        _entry("v002", "geo", geo=0.7),
        _entry("v003", "geo", geo=0.6, status="discarded"),
        _entry("v004", "competitive", competitive=0.8),
    ]
    geo_only = entries_for_lane(entries, "geo")
    assert [e["id"] for e in geo_only] == ["v002"]
    core_only = entries_for_lane(entries, "core")
    assert [e["id"] for e in core_only] == ["v001"]


def test_entries_for_lane_defaults_to_core_for_missing_lane_field() -> None:
    entries = [{"id": "v001", "search_metrics": {"composite": 0.5}}]  # no lane field
    assert [e["id"] for e in entries_for_lane(entries, "core")] == ["v001"]


# ── best_variant_in_lane ────────────────────────────────────────────────────


def test_best_variant_in_lane_returns_max_by_domain_score_in_workflow_lane() -> None:
    """Geo lane ranks by geo domain score, NOT by composite."""
    entries = [
        _entry("v001", "geo", composite=0.9, geo=0.20),  # high composite, low geo
        _entry("v002", "geo", composite=0.4, geo=0.80),  # low composite, high geo
        _entry("v003", "geo", composite=0.5, geo=0.50),
    ]
    best = best_variant_in_lane(entries, "geo")
    assert best is not None
    assert best["id"] == "v002"


def test_best_variant_in_lane_returns_max_by_composite_in_core_lane() -> None:
    entries = [
        _entry("v001", "core", composite=0.30),
        _entry("v002", "core", composite=0.80),
        _entry("v003", "core", composite=0.55),
    ]
    best = best_variant_in_lane(entries, "core")
    assert best is not None
    assert best["id"] == "v002"


def test_best_variant_in_lane_filters_other_lanes() -> None:
    """Entries from other lanes do not participate in the selection."""
    entries = [
        _entry("v001", "core", composite=0.99, geo=0.99),
        _entry("v002", "geo", composite=0.10, geo=0.20),
        _entry("v003", "geo", composite=0.10, geo=0.50),
    ]
    best_geo = best_variant_in_lane(entries, "geo")
    assert best_geo is not None
    assert best_geo["id"] == "v003"  # not v001 even though v001 has geo=0.99


def test_best_variant_in_lane_returns_none_for_empty_lane() -> None:
    entries = [_entry("v001", "geo", geo=0.5)]
    assert best_variant_in_lane(entries, "competitive") is None


def test_best_variant_in_lane_returns_none_when_all_discarded() -> None:
    entries = [
        _entry("v001", "geo", geo=0.5, status="discarded"),
        _entry("v002", "geo", geo=0.7, status="discarded"),
    ]
    assert best_variant_in_lane(entries, "geo") is None


def test_best_variant_in_lane_filters_by_suite_id_when_provided() -> None:
    entries = [
        _entry("v001", "geo", geo=0.50, suite_id="search-v0"),
        _entry("v002", "geo", geo=0.30, suite_id="search-v1"),
    ]
    best = best_variant_in_lane(entries, "geo", suite_id="search-v1")
    assert best is not None
    assert best["id"] == "v002"


def test_best_variant_in_lane_skips_entries_missing_search_metrics() -> None:
    entries = [
        {"id": "v001", "lane": "geo"},  # no search_metrics
        _entry("v002", "geo", geo=0.5),
    ]
    best = best_variant_in_lane(entries, "geo")
    assert best is not None
    assert best["id"] == "v002"


# ── objective_score wiring (already existed; this locks in semantics) ──────


def test_objective_score_resolves_to_composite_for_core_lane() -> None:
    e = _entry("v001", "core", composite=0.42, geo=0.99)
    assert objective_score(e) == 0.42


def test_objective_score_resolves_to_domain_score_for_workflow_lane() -> None:
    e = _entry("v001", "competitive", composite=0.99, competitive=0.42)
    assert objective_score(e) == 0.42


# ── Pareto removal — module-level deletions ────────────────────────────────


def test_frontier_module_no_longer_exposes_pareto_machinery() -> None:
    """Phase 2 deletes these symbols. Future code must not re-import them."""
    deleted = (
        "FrontierSnapshot",
        "pareto_frontier",
        "compute_frontiers",
        "finalist_shortlist",
        "frontier_membership_map",
        "_dominates",
        "_compare",
        "_sorted_frontier",
    )
    for symbol in deleted:
        assert not hasattr(frontier, symbol), (
            f"frontier.{symbol} should have been deleted in Phase 2"
        )


def test_frontier_module_still_exposes_lane_helpers() -> None:
    """The accessors used by select_parent.py and the archive CLI remain."""
    required = (
        "DOMAINS",
        "LANES",
        "composite_score",
        "domain_score",
        "has_search_metrics",
        "entry_lane",
        "objective_score",
        "entries_for_lane",
        "best_variant_in_lane",
        "api_cost_estimate",
        "wall_time_seconds",
    )
    for symbol in required:
        assert hasattr(frontier, symbol), f"frontier.{symbol} must remain"


# ── select_parent.py untouched (Hyperagents §A.2 verbatim) ─────────────────

# Recorded immediately before Phase 2 changes landed. If select_parent.py is
# edited at any point, this hash must be updated alongside an explicit
# acknowledgment that the meta-harness paper's prescription is being deviated
# from. Phase 2 must NOT change select_parent.py.
SELECT_PARENT_HASH_PRE_PHASE2 = (
    "2a882db65dd0e4b7b1d140ed50cedde7c3ccfba25405dd3beb1fbd0837c4b12a"
)


def test_select_parent_unchanged_after_phase2() -> None:
    contents = (AUTORESEARCH_DIR / "select_parent.py").read_bytes()
    actual = hashlib.sha256(contents).hexdigest()
    assert actual == SELECT_PARENT_HASH_PRE_PHASE2, (
        "select_parent.py must remain byte-identical through Phase 2 — "
        "Hyperagents §A.2 + §7 prescribe that the parent-selection machinery "
        "stays fixed. If you intentionally edited it, update the recorded "
        "hash AND document the deviation in the plan."
    )


def test_select_parent_still_imports_required_frontier_helpers() -> None:
    """select_parent.py imports composite_score, domain_score, has_search_metrics."""
    sys.path.insert(0, str(AUTORESEARCH_DIR))
    import select_parent  # type: ignore  # noqa: F401  (import is the assertion)
    # Verify the functions it relies on still resolve at the call site:
    assert callable(composite_score)
    assert callable(domain_score)
    assert callable(has_search_metrics)
