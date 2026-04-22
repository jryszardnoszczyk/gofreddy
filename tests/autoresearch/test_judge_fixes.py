"""Unit tests for the judge-system fix plan."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
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


def test_hard_fail_threshold_double_weights_marginal_failures():
    """A failure at exactly 0.5 - eps is hard (weight 2); 0.51 is soft (weight 1).

    This asserts behaviour, not the constant value — a refactor that flips
    the threshold and the comparison together would slip past a constant-check.
    """
    from session_evaluator import compute_weighted_failure_count

    hard_fail = {"score": 0.49}
    borderline_pass_scored_as_fail = {"score": 0.51}
    # Both items are in the "failed" list; weighting differs based on score.
    assert compute_weighted_failure_count([hard_fail]) == 2
    assert compute_weighted_failure_count([borderline_pass_scored_as_fail]) == 1
    assert compute_weighted_failure_count([hard_fail, borderline_pass_scored_as_fail]) == 3


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

    with pytest.raises(ValueError, match="AUTORESEARCH_WEEK_RELATIVE"):
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


def test_sample_fixtures_fallback_derives_cohort_from_variant_id(monkeypatch):
    """When EVOLUTION_COHORT_ID is unset, standalone invocation derives the
    cohort from variant_id using (n - 1) // cohort_size — matching evolve.py's
    1-indexed mapping, so v001..v003 land in cohort 0, v004..v006 in cohort 1."""
    from evaluate_variant import _sample_fixtures

    pool = _make_monitoring_pool()
    rotation = {"strategy": "stratified", "random_per_domain": 1, "seed_source": "generation", "cohort_size": 3}

    monkeypatch.delenv("EVOLUTION_COHORT_ID", raising=False)
    v001 = _sample_fixtures({"monitoring": pool}, rotation, "v001")
    v002 = _sample_fixtures({"monitoring": pool}, rotation, "v002")
    v003 = _sample_fixtures({"monitoring": pool}, rotation, "v003")
    v004 = _sample_fixtures({"monitoring": pool}, rotation, "v004")
    # v001-v003 are cohort 0 → identical derived seed → identical sample.
    assert [f.fixture_id for f in v001["monitoring"]] == [f.fixture_id for f in v002["monitoring"]]
    assert [f.fixture_id for f in v002["monitoring"]] == [f.fixture_id for f in v003["monitoring"]]
    # v004 is cohort 1 → different derived seed → sample may differ.  Don't
    # assert inequality (the seeds could coincidentally pick the same sample);
    # just verify the seed string computation by hitting a different cohort.


def test_sample_fixtures_fallback_handles_non_v_prefixed_ids(monkeypatch):
    """When variant_id doesn't parse as int, fall through to variant-seeded sample."""
    from evaluate_variant import _sample_fixtures

    pool = _make_monitoring_pool()
    rotation = {"strategy": "stratified", "random_per_domain": 1, "seed_source": "generation", "cohort_size": 3}

    monkeypatch.delenv("EVOLUTION_COHORT_ID", raising=False)
    # Should not raise; takes seed = variant_id branch.
    sampled = _sample_fixtures({"monitoring": pool}, rotation, "custom-id")
    assert "shopify" in [f.fixture_id for f in sampled["monitoring"]]


# ---------------------------------------------------------------------------
# Fix 8 + 9 — compute_metrics (_pearson, compute_generation_metrics, check_alerts)
# ---------------------------------------------------------------------------


def test_pearson_returns_none_for_small_n():
    from compute_metrics import _pearson

    assert _pearson([], []) is None
    assert _pearson([1.0, 2.0], [1.0, 2.0]) is None  # n=2 < 3
    # n=3 minimum required.
    assert _pearson([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0


def test_pearson_perfect_inverse_correlation():
    from compute_metrics import _pearson

    r = _pearson([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0])
    assert r == -1.0


def test_pearson_zero_variance_returns_none():
    from compute_metrics import _pearson

    # Zero denominator (all xs identical) → undefined correlation.
    assert _pearson([0.5, 0.5, 0.5, 0.5], [0.1, 0.2, 0.3, 0.4]) is None


def test_compute_generation_metrics_mean_composite_uses_all_rows(tmp_path, monkeypatch):
    """mean_composite must aggregate over every loaded row, not only those
    with inner keep_rate.  Filtering by keep_rate applies only to the
    inner-outer correlation pair."""
    import compute_metrics

    # Redirect ARCHIVE_DIR to tmp and seed three variants with mixed keep_rate.
    monkeypatch.setattr(compute_metrics, "ARCHIVE_DIR", tmp_path)
    _seed_scores(tmp_path / "v001", composite=0.8, keep_rate=0.9)
    _seed_scores(tmp_path / "v002", composite=0.6, keep_rate=None)  # no inner metrics
    _seed_scores(tmp_path / "v003", composite=0.7, keep_rate=0.8)

    row = compute_metrics.compute_generation_metrics("core", 1, ["v001", "v002", "v003"])
    # mean_composite averages ALL three composites: (0.8 + 0.6 + 0.7) / 3 = 0.7
    assert row["mean_composite"] == pytest.approx(0.7, abs=1e-3)
    # mean_keep averages only the rows with inner keep_rate: (0.9 + 0.8) / 2 = 0.85
    assert row["mean_keep"] == pytest.approx(0.85, abs=1e-3)
    assert row["n"] == 3


# NOTE: the previous threshold-based alert tests
# (`test_check_alerts_inner_outer_drift_requires_two_consecutive_gens`,
# `test_check_alerts_uneven_generalization_fires_on_threshold_crossing`)
# were removed in Unit 10 (R-#30). The fixed thresholds they exercised no
# longer exist — alerts are now agent-driven with no threshold backstop.
# Coverage of the new path lives in
# `tests/autoresearch/test_compute_metrics_alerts.py`.


# ---------------------------------------------------------------------------
# Fix 12 — compute_inner_keep_rate
# ---------------------------------------------------------------------------


def test_compute_inner_keep_rate_empty_variant_dir(tmp_path):
    from telemetry import compute_inner_keep_rate  # autoresearch/harness is on sys.path

    assert compute_inner_keep_rate(tmp_path) == {}


def test_compute_inner_keep_rate_counts_decisions(tmp_path):
    from telemetry import compute_inner_keep_rate  # autoresearch/harness is on sys.path

    session_dir = tmp_path / "sessions" / "geo" / "acme"
    session_dir.mkdir(parents=True)
    (session_dir / ".last_eval_cache.json").write_text(json.dumps({
        "k1": {"hash": "x", "stdout": json.dumps({"decision": "KEEP"})},
        "k2": {"hash": "y", "stdout": json.dumps({"decision": "KEEP"})},
        "k3": {"hash": "z", "stdout": json.dumps({"decision": "REWORK"})},
        "k4": {"hash": "w", "stdout": json.dumps({"decision": "DISCARD"})},
    }))
    result = compute_inner_keep_rate(tmp_path)
    assert "sessions/geo/acme" in result
    entry = result["sessions/geo/acme"]
    assert entry["total"] == 4
    assert entry["keeps"] == 2
    assert entry["reworks"] == 1
    assert entry["discards"] == 1
    assert entry["keep_rate"] == 0.5


def test_compute_inner_keep_rate_filters_none_decisions_from_total(tmp_path, capsys):
    """A cache entry whose stdout is valid JSON but missing 'decision' must NOT
    inflate `total` — otherwise keep_rate is under-reported."""
    from telemetry import compute_inner_keep_rate  # autoresearch/harness is on sys.path

    session_dir = tmp_path / "sessions" / "geo" / "acme"
    session_dir.mkdir(parents=True)
    (session_dir / ".last_eval_cache.json").write_text(json.dumps({
        "k1": {"hash": "x", "stdout": json.dumps({"decision": "KEEP"})},
        "k2": {"hash": "y", "stdout": json.dumps({"no_decision_key": True})},  # None decision
        "k3": {"hash": "z", "stdout": "not-valid-json{"},  # parse error
    }))
    result = compute_inner_keep_rate(tmp_path)
    entry = result["sessions/geo/acme"]
    # Only the KEEP decision counts; others are dropped + surfaced.
    assert entry["total"] == 1
    assert entry["keeps"] == 1
    assert entry["keep_rate"] == 1.0
    err = capsys.readouterr().err
    assert "unparseable cache entries" in err


def test_compute_inner_keep_rate_malformed_cache_file_surfaces_warning(tmp_path, capsys):
    from telemetry import compute_inner_keep_rate  # autoresearch/harness is on sys.path

    session_dir = tmp_path / "sessions" / "geo" / "acme"
    session_dir.mkdir(parents=True)
    (session_dir / ".last_eval_cache.json").write_text("not-json[")
    result = compute_inner_keep_rate(tmp_path)
    assert result == {}
    err = capsys.readouterr().err
    assert "cannot read" in err


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_scores(variant_dir: Path, *, composite: float, keep_rate: float | None) -> None:
    variant_dir.mkdir(parents=True, exist_ok=True)
    inner_metrics = (
        {"sessions/geo/acme": {"keep_rate": keep_rate, "total": 4, "keeps": int(keep_rate * 4)}}
        if keep_rate is not None
        else {}
    )
    payload = {
        "composite": composite,
        "domains": {"geo": {"score": composite, "fixture_sd": 0.05}},
        "inner_metrics": inner_metrics,
    }
    (variant_dir / "scores.json").write_text(json.dumps(payload))
