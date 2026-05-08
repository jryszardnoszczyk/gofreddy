"""Calibration warning when inner-vs-outer pass-rate delta exceeds ±0.15.

Pi v007 audit surfaced pass_rate_delta=+0.317 (inner judge said 68% pass,
outer judge said 100%) — a real divergence that operators were missing
because the signal lived only in scores.json after-the-fact. The warning
prints to stderr at the end of search-suite scoring so it lands in the
operator's tail-and-report log."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

# Path-bootstrap matches sibling tests
_repo_root = Path(__file__).resolve().parents[2]
_autoresearch_dir = _repo_root / "autoresearch"
if str(_autoresearch_dir) in sys.path:
    sys.path.remove(str(_autoresearch_dir))
sys.path.insert(0, str(_autoresearch_dir))
for _mod in [m for m in list(sys.modules) if m == "harness" or m.startswith("harness.")]:
    file_attr = getattr(sys.modules[_mod], "__file__", None) or ""
    if not file_attr.startswith(str(_autoresearch_dir)):
        del sys.modules[_mod]

import evaluate_variant  # noqa: E402


def _build_scored_fixtures(deltas, inner_values, outer_values):
    """Return scored_fixtures shape that _aggregate_suite_results consumes."""
    items = []
    for delta, inner, outer in zip(deltas, inner_values, outer_values):
        items.append({
            "fixture_id": "f-x",
            "suite_id": "search-v1",
            "client": "x",
            "context": "u",
            "score": 0.5,
            "dimension_scores": [],
            "grounding_passed": True,
            "structural_passed": True,
            "pass_rate_delta": delta,
            "inner_pass_rate": inner,
            "outer_pass_rate": outer,
            "produced_output": True,
            "wall_time_seconds": 1.0,
            "max_iter": 1,
            "timeout": 10,
        })
    return {"geo": items, "competitive": [], "monitoring": [], "storyboard": []}


def test_calibration_warning_fires_when_delta_exceeds_threshold():
    fixtures_by_domain = {"geo": [], "competitive": [], "monitoring": [], "storyboard": [], "marketing_audit": []}
    scored = _build_scored_fixtures(
        deltas=[0.30, 0.35, 0.32],
        inner_values=[0.60, 0.65, 0.68],
        outer_values=[0.90, 1.00, 1.00],
    )
    suite_manifest = {"suite_id": "search-v1"}
    err = io.StringIO()
    with redirect_stderr(err):
        evaluate_variant._aggregate_suite_results(suite_manifest, fixtures_by_domain, scored)
    out = err.getvalue()
    assert "calibration drift" in out
    assert "|delta|>0.15" in out


def test_calibration_warning_silent_within_threshold():
    fixtures_by_domain = {"geo": [], "competitive": [], "monitoring": [], "storyboard": [], "marketing_audit": []}
    scored = _build_scored_fixtures(
        deltas=[0.05, -0.10, 0.08],
        inner_values=[0.85, 0.90, 0.88],
        outer_values=[0.90, 0.80, 0.96],
    )
    suite_manifest = {"suite_id": "search-v1"}
    err = io.StringIO()
    with redirect_stderr(err):
        evaluate_variant._aggregate_suite_results(suite_manifest, fixtures_by_domain, scored)
    out = err.getvalue()
    assert "calibration drift" not in out


def test_calibration_warning_silent_when_no_delta_data():
    """All-None deltas (e.g. fixtures with no results.jsonl rows) → no warning."""
    fixtures_by_domain = {"geo": [], "competitive": [], "monitoring": [], "storyboard": [], "marketing_audit": []}
    scored = _build_scored_fixtures(
        deltas=[None, None, None],
        inner_values=[None, None, None],
        outer_values=[None, None, None],
    )
    suite_manifest = {"suite_id": "search-v1"}
    err = io.StringIO()
    with redirect_stderr(err):
        evaluate_variant._aggregate_suite_results(suite_manifest, fixtures_by_domain, scored)
    out = err.getvalue()
    assert "calibration drift" not in out


def test_calibration_warning_negative_drift():
    """Negative pass_rate_delta (inner > outer) trips the same warning."""
    fixtures_by_domain = {"geo": [], "competitive": [], "monitoring": [], "storyboard": [], "marketing_audit": []}
    scored = _build_scored_fixtures(
        deltas=[-0.20, -0.25, -0.18],
        inner_values=[0.95, 1.00, 0.95],
        outer_values=[0.75, 0.75, 0.77],
    )
    suite_manifest = {"suite_id": "search-v1"}
    err = io.StringIO()
    with redirect_stderr(err):
        evaluate_variant._aggregate_suite_results(suite_manifest, fixtures_by_domain, scored)
    out = err.getvalue()
    assert "calibration drift" in out
