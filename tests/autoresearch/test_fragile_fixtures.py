"""Stream A A5 — fragile-fixture exclusion gate.

Background: Stream A plan §6.A5 — seven fixtures swing > 2σ across the
archive (e.g. `monitoring-ramp-arc-t1` sd=2.47). With the env flag
``AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES`` set, the lane composite
excludes those fixtures while still recording their scores in
``fixtures_detail`` for observability.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from autoresearch.lane_registry import (  # noqa: E402
    FRAGILE_FIXTURES,
    fragile_fixtures_filter_enabled,
    is_fragile_fixture,
)


def test_fragile_fixtures_set_is_non_empty_and_strings_only() -> None:
    assert FRAGILE_FIXTURES, "fragile set should not be empty — Stream A A5 audit shipped"
    for fid in FRAGILE_FIXTURES:
        assert isinstance(fid, str) and fid, fid


def test_monitoring_ramp_arc_t1_is_marked_fragile() -> None:
    """Plan §6.A5 explicitly names this fixture as the canonical fragile case."""
    assert "monitoring-ramp-arc-t1" in FRAGILE_FIXTURES


def test_filter_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES", raising=False)
    assert fragile_fixtures_filter_enabled() is False
    # Even a known-fragile id should NOT be filtered when the flag is off.
    assert is_fragile_fixture("monitoring-ramp-arc-t1") is False


@pytest.mark.parametrize("value", ["1", "on", "true", "yes", "ON"])
def test_filter_enabled_for_truthy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES", value)
    assert fragile_fixtures_filter_enabled() is True
    assert is_fragile_fixture("monitoring-ramp-arc-t1") is True
    # Healthy sibling stays included.
    assert is_fragile_fixture("monitoring-ramp-arc-t0") is False


@pytest.mark.parametrize("value", ["0", "off", "false", "no", ""])
def test_filter_disabled_for_falsy_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES", value)
    assert fragile_fixtures_filter_enabled() is False


def test_aggregate_excludes_fragile_when_flag_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: with the flag set, `_aggregate_suite_results` drops the
    fragile fixture from composite computation while keeping it in
    `fixtures_detail`."""
    monkeypatch.setenv("AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES", "on")

    import autoresearch.evaluate_variant as ev

    scored_fixtures = {
        "monitoring": [
            {"fixture_id": "monitoring-ramp-arc-t0", "score": 8.0, "dimension_scores": []},
            {"fixture_id": "monitoring-ramp-arc-t1", "score": 1.5,  "dimension_scores": []},  # fragile
            {"fixture_id": "monitoring-rippling-firstweek", "score": 8.2, "dimension_scores": []},
            {"fixture_id": "monitoring-shopify-2026w12", "score": 8.0, "dimension_scores": []},
        ],
        "geo": [], "competitive": [], "storyboard": [],
        "marketing_audit": [], "x_engine": [], "linkedin_engine": [],
    }
    fixtures_by_domain = {k: list(v) for k, v in scored_fixtures.items()}
    suite_manifest = {
        "suite_id": "search-v1",
        "active_domains": ["monitoring"],
        "objective_domain": "monitoring",
    }
    _domain_scores, aggregated = ev._aggregate_suite_results(
        suite_manifest=suite_manifest,
        fixtures_by_domain=fixtures_by_domain,
        scored_fixtures=scored_fixtures,
    )

    mon = aggregated["domains"]["monitoring"]
    assert "monitoring-ramp-arc-t1" in mon["fixtures_detail"], (
        "fragile fixture must still appear in fixtures_detail for observability"
    )
    # Composite computed from the three healthy fixtures only — the t1 1.5
    # outlier would have pulled the geometric mean far below ~8.0.
    assert mon["score"] > 7.5, (
        f"composite should reflect the 3 healthy fixtures (got {mon['score']}); "
        "the fragile fixture's 1.5 outlier must be excluded"
    )


def test_aggregate_includes_fragile_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reversibility: with the flag unset, composite includes every fixture
    — preserving the historical baseline for comparison."""
    monkeypatch.delenv("AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES", raising=False)

    import autoresearch.evaluate_variant as ev

    scored_fixtures = {
        "monitoring": [
            {"fixture_id": "monitoring-ramp-arc-t0", "score": 8.0, "dimension_scores": []},
            {"fixture_id": "monitoring-ramp-arc-t1", "score": 1.5,  "dimension_scores": []},
            {"fixture_id": "monitoring-rippling-firstweek", "score": 8.2, "dimension_scores": []},
            {"fixture_id": "monitoring-shopify-2026w12", "score": 8.0, "dimension_scores": []},
        ],
        "geo": [], "competitive": [], "storyboard": [],
        "marketing_audit": [], "x_engine": [], "linkedin_engine": [],
    }
    fixtures_by_domain = {k: list(v) for k, v in scored_fixtures.items()}
    suite_manifest = {
        "suite_id": "search-v1",
        "active_domains": ["monitoring"],
        "objective_domain": "monitoring",
    }
    _domain_scores, aggregated = ev._aggregate_suite_results(
        suite_manifest=suite_manifest,
        fixtures_by_domain=fixtures_by_domain,
        scored_fixtures=scored_fixtures,
    )

    mon = aggregated["domains"]["monitoring"]
    # Including the 1.5 fixture, the geometric mean is pulled lower.
    assert mon["score"] < 6.0, (
        f"with fragile fixture included, composite should be ≲ 6 (got {mon['score']})"
    )
