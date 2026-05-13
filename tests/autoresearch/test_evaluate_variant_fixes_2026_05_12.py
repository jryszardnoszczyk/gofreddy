"""Tests for the 4 fixes that landed 2026-05-12:

1. Cache-skip refuses to re-use prior session deliverables when the prior
   results.jsonl ended in structural_gate=fail (Fix #1)
2. _extract_inner_pass_rate reads canonical session-judge JSON verdicts first,
   falls back to results.jsonl (Fix #2a)
3. _outer_pass_from_score no longer forces 0.0 on structural_passed=False (Fix #2b)
4. Suite manifests have raised random_per_domain=2 for geo/competitive/storyboard/marketing_audit (Fix #4)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from evaluate_variant import (
    _extract_inner_pass_rate,
    _outer_pass_from_score,
    _prior_results_failed_structural_gate,
)


# ---------------------------------------------------------------------------
# Fix #1 — _prior_results_failed_structural_gate
# ---------------------------------------------------------------------------


def _write_results(session_dir: Path, rows: list[dict]) -> None:
    """Write results.jsonl with the given rows."""
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "results.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n"
    )


def test_prior_failed_structural_gate_detects_fail(tmp_path: Path) -> None:
    """Last structural_gate row with status=fail should return True."""
    _write_results(tmp_path, [
        {"type": "select_mentions", "status": "complete"},
        {"type": "synthesize", "status": "kept"},
        {"type": "structural_gate", "status": "fail"},
    ])
    assert _prior_results_failed_structural_gate(tmp_path) is True


def test_prior_failed_structural_gate_returns_false_on_pass(tmp_path: Path) -> None:
    _write_results(tmp_path, [
        {"type": "synthesize", "status": "kept"},
        {"type": "structural_gate", "status": "pass"},
    ])
    assert _prior_results_failed_structural_gate(tmp_path) is False


def test_prior_failed_structural_gate_returns_false_when_no_gate_row(tmp_path: Path) -> None:
    """No structural_gate row at all → False (preserves cleanly-completed sessions)."""
    _write_results(tmp_path, [
        {"type": "synthesize", "status": "kept"},
        {"type": "verify", "status": "complete"},
    ])
    assert _prior_results_failed_structural_gate(tmp_path) is False


def test_prior_failed_structural_gate_walks_back_to_last_gate(tmp_path: Path) -> None:
    """Multiple structural_gate rows: only the LAST one matters."""
    _write_results(tmp_path, [
        {"type": "structural_gate", "status": "fail"},
        {"type": "synthesize", "status": "rework"},
        {"type": "structural_gate", "status": "pass"},
    ])
    assert _prior_results_failed_structural_gate(tmp_path) is False


def test_prior_failed_structural_gate_returns_false_on_missing_file(tmp_path: Path) -> None:
    assert _prior_results_failed_structural_gate(tmp_path) is False


def test_prior_failed_structural_gate_skips_malformed_lines(tmp_path: Path) -> None:
    """Garbage line shouldn't crash; should still find the structural_gate fail."""
    session_dir = tmp_path
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "results.jsonl").write_text(
        "this is not json\n"
        + json.dumps({"type": "structural_gate", "status": "fail"}) + "\n"
    )
    assert _prior_results_failed_structural_gate(session_dir) is True


# ---------------------------------------------------------------------------
# Fix #2a — _extract_inner_pass_rate canonical-JSON path
# ---------------------------------------------------------------------------


def test_inner_pass_rate_reads_monitoring_digest_eval(tmp_path: Path) -> None:
    """Monitoring writes digest_eval.json with {decision, results: [{passes, ...}]}."""
    session_dir = tmp_path / "monitoring" / "Lululemon"
    session_dir.mkdir(parents=True)
    (session_dir / "digest_eval.json").write_text(json.dumps({
        "decision": "KEEP",
        "results": [
            {"criterion": "MON-1", "passes": True, "score": 1.0},
            {"criterion": "MON-2", "passes": True, "score": 1.0},
            {"criterion": "MON-3", "passes": True, "score": 1.0},
            {"criterion": "MON-4", "passes": False, "score": 0.0},
        ],
    }))
    result = _extract_inner_pass_rate(session_dir)
    assert result["inner_pass_rate"] == 0.75
    assert result["keeps"] == 3
    assert result["reworks"] == 1


def test_inner_pass_rate_reads_competitive_eval_feedback(tmp_path: Path) -> None:
    """Competitive/storyboard write eval_feedback.json with same schema."""
    session_dir = tmp_path / "competitive" / "epic"
    session_dir.mkdir(parents=True)
    (session_dir / "eval_feedback.json").write_text(json.dumps({
        "decision": "KEEP",
        "results": [
            {"criterion": "CI-1", "passes": True},
            {"criterion": "CI-2", "passes": True},
            {"criterion": "CI-3", "passes": True},
            {"criterion": "CI-4", "passes": True},
            {"criterion": "CI-5", "passes": True},
            {"criterion": "CI-6", "passes": True},
            {"criterion": "CI-7", "passes": True},
            {"criterion": "CI-8", "passes": True},
        ],
    }))
    result = _extract_inner_pass_rate(session_dir)
    assert result["inner_pass_rate"] == 1.0
    assert result["keeps"] == 8
    assert result["reworks"] == 0


def test_inner_pass_rate_reads_geo_per_artifact_evals(tmp_path: Path) -> None:
    """Geo writes evals/<artifact>.json (one per optimized page) — aggregate across them."""
    session_dir = tmp_path / "geo" / "mayoclinic"
    evals = session_dir / "evals"
    evals.mkdir(parents=True)
    (evals / "page-1.json").write_text(json.dumps({
        "decision": "KEEP",
        "results": [
            {"criterion": "GEO-1", "passes": True},
            {"criterion": "GEO-2", "passes": True},
        ],
    }))
    (evals / "page-2.json").write_text(json.dumps({
        "decision": "REWORK",
        "results": [
            {"criterion": "GEO-1", "passes": False},
            {"criterion": "GEO-2", "passes": True},
        ],
    }))
    result = _extract_inner_pass_rate(session_dir)
    # 3 passes (true) + 1 fail = 0.75
    assert result["inner_pass_rate"] == 0.75
    assert result["keeps"] == 3
    assert result["reworks"] == 1


def test_inner_pass_rate_falls_back_to_decision_on_empty_results(tmp_path: Path) -> None:
    """Geo's structural-gate-failed evals have empty results — fall back to decision."""
    session_dir = tmp_path / "geo" / "semrush"
    evals = session_dir / "evals"
    evals.mkdir(parents=True)
    (evals / "page-1.json").write_text(json.dumps({
        "decision": "DISCARD",
        "reason": "structural_gate_failed",
        "results": [],
    }))
    result = _extract_inner_pass_rate(session_dir)
    assert result["inner_pass_rate"] == 0.0
    assert result["reworks"] == 1


def test_inner_pass_rate_falls_back_to_results_jsonl_when_canonical_missing(tmp_path: Path) -> None:
    """When no canonical JSON exists, fall back to the original status-token scan."""
    _write_results(tmp_path, [
        {"type": "synthesize", "status": "kept"},
        {"type": "synthesize", "status": "kept"},
        {"type": "structural_gate", "status": "fail"},
    ])
    result = _extract_inner_pass_rate(tmp_path)
    # 2 keeps + 1 fail = 0.667
    assert result["inner_pass_rate"] == 0.6667
    assert result["keeps"] == 2
    assert result["reworks"] == 1


def test_inner_pass_rate_returns_none_for_empty_session_dir(tmp_path: Path) -> None:
    result = _extract_inner_pass_rate(tmp_path)
    assert result["inner_pass_rate"] is None


# ---------------------------------------------------------------------------
# Fix #2b — _outer_pass_from_score no longer zeroes on structural fail
# ---------------------------------------------------------------------------


def test_outer_pass_continuous_when_structural_passes() -> None:
    assert _outer_pass_from_score(8.5, structural_passed=True) == 0.85


def test_outer_pass_continuous_when_structural_fails() -> None:
    """KEY FIX: pre-2026-05-12, this returned 0.0; now returns the score-derived value."""
    assert _outer_pass_from_score(7.85, structural_passed=False) == pytest.approx(0.785)


def test_outer_pass_clamped_to_unit_interval() -> None:
    assert _outer_pass_from_score(15.0, structural_passed=True) == 1.0
    assert _outer_pass_from_score(-1.0, structural_passed=True) == 0.0


def test_outer_pass_zero_score_returns_zero_regardless_of_structural() -> None:
    assert _outer_pass_from_score(0.0, structural_passed=True) == 0.0
    assert _outer_pass_from_score(0.0, structural_passed=False) == 0.0


# ---------------------------------------------------------------------------
# Fix #4 — fixture rotation random_per_domain=2 for at-risk lanes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("suite", [
    "search-v1.json",
    "search-v1-claude-opus.json",
    "search-v1-claude-sonnet.json",
    "search-v1-claude-haiku.json",
])
@pytest.mark.parametrize("lane", ["geo", "competitive", "storyboard", "marketing_audit"])
def test_suite_has_random_per_domain_2_for_at_risk_lanes(suite: str, lane: str) -> None:
    """All 4 at-risk lanes have N=4 cohort (2 anchors + 2 random) to absorb single-fixture failures."""
    suite_path = (
        Path(__file__).resolve().parents[2]
        / "autoresearch" / "eval_suites" / suite
    )
    data = json.loads(suite_path.read_text())
    per_domain = data.get("rotation", {}).get("per_domain", {})
    assert lane in per_domain, f"{suite} missing per_domain override for {lane}"
    assert per_domain[lane]["random_per_domain"] == 2, (
        f"{suite}/{lane} should have random_per_domain=2 (got "
        f"{per_domain[lane].get('random_per_domain')})"
    )


@pytest.mark.parametrize("suite", [
    "search-v1.json",
    "search-v1-claude-opus.json",
    "search-v1-claude-sonnet.json",
    "search-v1-claude-haiku.json",
])
def test_x_engine_linkedin_engine_unchanged(suite: str) -> None:
    """x_engine + linkedin_engine should still be at random_per_domain=3 (untouched by Fix #4)."""
    suite_path = (
        Path(__file__).resolve().parents[2]
        / "autoresearch" / "eval_suites" / suite
    )
    data = json.loads(suite_path.read_text())
    per_domain = data.get("rotation", {}).get("per_domain", {})
    assert per_domain["x_engine"]["random_per_domain"] == 3
    assert per_domain["linkedin_engine"]["random_per_domain"] == 3
