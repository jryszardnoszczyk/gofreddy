"""Unit tests for the judge-system fix plan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fix 6 — compute_decision_threshold
# ---------------------------------------------------------------------------


def test_decision_threshold_8_criterion_domain():
    from session_evaluator import compute_decision_threshold

    assert compute_decision_threshold(8) == 2


def test_decision_threshold_4_criterion_per_story():
    from session_evaluator import compute_decision_threshold

    assert compute_decision_threshold(4) == 1


def test_decision_threshold_odd_counts_round_up():
    from session_evaluator import compute_decision_threshold

    assert compute_decision_threshold(5) == 2
    assert compute_decision_threshold(1) == 1


def test_hard_fail_threshold_is_half_point_five():
    from session_evaluator import HARD_FAIL_THRESHOLD

    assert HARD_FAIL_THRESHOLD == 0.5


# ---------------------------------------------------------------------------
# Fix 4 — geometric mean
# ---------------------------------------------------------------------------


def test_geometric_mean_empty_returns_zero():
    from evaluate_variant import _geometric_mean

    assert _geometric_mean([]) == 0.0


def test_geometric_mean_single_score_returns_score():
    from evaluate_variant import _geometric_mean

    assert _geometric_mean([0.6]) == pytest.approx(0.6)


def test_geometric_mean_uniform_scores():
    from evaluate_variant import _geometric_mean

    assert _geometric_mean([0.5, 0.5, 0.5]) == pytest.approx(0.5)


def test_geometric_mean_zero_is_floored_not_absorbing():
    from evaluate_variant import _geometric_mean

    # Geometric mean of [1.0, 0.0] with 0.01 floor = sqrt(1 * 0.01) = 0.1
    result = _geometric_mean([1.0, 0.0])
    assert result == pytest.approx(0.1, rel=1e-6)


def test_geometric_mean_hurts_more_than_arithmetic():
    from evaluate_variant import _geometric_mean

    scores = [0.9, 0.9, 0.9, 0.1]
    # Arithmetic mean: 0.7; Geometric (with 0.1 floor irrelevant here): < 0.7
    geo = _geometric_mean(scores)
    arithmetic = sum(scores) / len(scores)
    assert geo < arithmetic
    # ln-based sanity: (0.9*0.9*0.9*0.1) ** 0.25 = ~0.52
    assert geo == pytest.approx(0.5198, abs=1e-3)


# ---------------------------------------------------------------------------
# Fix 12 — week resolver
# ---------------------------------------------------------------------------


def test_week_resolver_passes_through_when_spec_missing():
    from evaluate_variant import _resolve_week_relative

    env = {"OTHER": "x"}
    assert _resolve_week_relative(env) is env


def test_week_resolver_monday_most_recent_complete():
    from evaluate_variant import _resolve_week_relative

    # Mon 2026-04-20. Last complete Mon-Sun: 2026-04-13 to 2026-04-19.
    r = _resolve_week_relative(
        {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
        today=date(2026, 4, 20),
    )
    assert r["AUTORESEARCH_WEEK_START"] == "2026-04-13"
    assert r["AUTORESEARCH_WEEK_END"] == "2026-04-19"


def test_week_resolver_monday_minus_one():
    from evaluate_variant import _resolve_week_relative

    r = _resolve_week_relative(
        {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete_minus_1"},
        today=date(2026, 4, 20),
    )
    assert r["AUTORESEARCH_WEEK_START"] == "2026-04-06"
    assert r["AUTORESEARCH_WEEK_END"] == "2026-04-12"


def test_week_resolver_wednesday_skips_current_week():
    from evaluate_variant import _resolve_week_relative

    # Wed 2026-04-22. Current week (Mon 4/20 - Sun 4/26) is in progress;
    # most-recent-complete is still the prior week 4/13 - 4/19.
    r = _resolve_week_relative(
        {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
        today=date(2026, 4, 22),
    )
    assert r["AUTORESEARCH_WEEK_START"] == "2026-04-13"
    assert r["AUTORESEARCH_WEEK_END"] == "2026-04-19"


def test_week_resolver_sunday_treats_current_week_as_in_progress():
    from evaluate_variant import _resolve_week_relative

    # Sun 2026-04-19. The week ending today is still mid-day; resolver is
    # defensive and returns the PRIOR complete week (4/6 - 4/12).
    r = _resolve_week_relative(
        {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
        today=date(2026, 4, 19),
    )
    assert r["AUTORESEARCH_WEEK_START"] == "2026-04-06"
    assert r["AUTORESEARCH_WEEK_END"] == "2026-04-12"


def test_week_resolver_rejects_unknown_spec():
    from evaluate_variant import _resolve_week_relative

    with pytest.raises(RuntimeError, match="AUTORESEARCH_WEEK_RELATIVE"):
        _resolve_week_relative({"AUTORESEARCH_WEEK_RELATIVE": "bogus"})


# ---------------------------------------------------------------------------
# Fix 14 — arc-pair atomic sampling
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _StubFixture:
    fixture_id: str
    anchor: bool
    env: dict

    # other fields unused by _sample_fixtures
    suite_id: str = "search-v1"
    domain: str = "monitoring"
    client: str = "stub"
    context: str = ""
    max_iter: int = 1
    timeout: int = 1


def _make_monitoring_pool() -> list:
    return [
        _StubFixture("shopify", True, {}),
        _StubFixture("notion", False, {}),  # singleton
        _StubFixture(
            "ramp-arc-t0",
            False,
            {
                "AUTORESEARCH_MONITORING_ARC_ROLE": "t0",
                "AUTORESEARCH_MONITORING_ARC_PAIR_ID": "ramp-arc-2026",
            },
        ),
        _StubFixture(
            "ramp-arc-t1",
            False,
            {
                "AUTORESEARCH_MONITORING_ARC_ROLE": "t1",
                "AUTORESEARCH_MONITORING_ARC_PAIR_ID": "ramp-arc-2026",
            },
        ),
    ]


def test_sample_fixtures_arc_pair_atomic_both_or_neither():
    """If the sampler picks an arc pair, both siblings must run together."""
    from evaluate_variant import _sample_fixtures

    pool = _make_monitoring_pool()
    rotation = {
        "strategy": "stratified",
        "anchors_per_domain": 1,
        "random_per_domain": 1,
        "seed_source": "generation",
        "cohort_size": 3,
    }

    saw_pair_together = False
    saw_singleton_alone = False
    # Try many cohort seeds — sampling is deterministic per seed, varying it
    # across cohorts should pick both outcomes.
    for cohort_id in range(20):
        with patch.dict("os.environ", {"EVOLUTION_COHORT_ID": str(cohort_id)}):
            sampled = _sample_fixtures({"monitoring": pool}, rotation, "v001")
        ids = [f.fixture_id for f in sampled["monitoring"]]
        assert "shopify" in ids, "anchor must always be sampled"
        t0 = "ramp-arc-t0" in ids
        t1 = "ramp-arc-t1" in ids
        # Atomicity: never one without the other
        assert t0 == t1, f"pair split: cohort={cohort_id} ids={ids}"
        if t0 and t1:
            saw_pair_together = True
            # t0 must precede t1 (ARC_ROLE ordering)
            assert ids.index("ramp-arc-t0") < ids.index("ramp-arc-t1")
        if "notion" in ids and not t0:
            saw_singleton_alone = True

    assert saw_pair_together, "expected pair to be sampled at least once"
    assert saw_singleton_alone, "expected singleton to be sampled at least once"


def test_sample_fixtures_cohort_seed_determinism():
    """Same cohort id → same sample; different cohort id → potentially different."""
    from evaluate_variant import _sample_fixtures

    pool = _make_monitoring_pool()
    rotation = {
        "strategy": "stratified",
        "anchors_per_domain": 1,
        "random_per_domain": 1,
        "seed_source": "generation",
        "cohort_size": 3,
    }

    with patch.dict("os.environ", {"EVOLUTION_COHORT_ID": "7"}):
        a = _sample_fixtures({"monitoring": pool}, rotation, "v042")
    with patch.dict("os.environ", {"EVOLUTION_COHORT_ID": "7"}):
        b = _sample_fixtures({"monitoring": pool}, rotation, "v999")  # variant changes
    assert [f.fixture_id for f in a["monitoring"]] == [f.fixture_id for f in b["monitoring"]]
