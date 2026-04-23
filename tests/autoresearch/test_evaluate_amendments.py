"""Tests for Phase 7 Step 2.5 additive amendments to evaluate_variant.py.

Covers:
  (a) ``_aggregate_suite_results`` emits ``fixtures_detail`` alongside the
      unchanged ``fixtures: int`` field.
  (b) ``_search_promotion_summary`` emits ``holdout_composite`` +
      ``secondary_holdout_composite`` (None when holdout was not run).
  (c) ``_sample_fixtures`` with a fixed ``EVOLUTION_COHORT_ID`` returns a
      deterministic subset, and no-op when rotation config is empty.
  (d) ``_refresh_monitoring_scores_for_baseline`` updates only monitoring
      fixtures' scores, leaving non-monitoring scores untouched.
"""
from __future__ import annotations

import pytest

from autoresearch import evaluate_variant as ev


def _make_suite_manifest(fixture_ids):
    return {
        "suite_id": "search-v1",
        "version": "1.0",
        "objective_domain": "geo",
        "active_domains": ["geo"],
        "domains": {
            "geo": [
                {
                    "fixture_id": fid,
                    "client": "acme",
                    "context": "https://acme.com",
                    "version": "1.0",
                    "max_iter": 1,
                    "timeout": 60,
                }
                for fid in fixture_ids
            ],
        },
    }


def _scored_fixture(fid, score, secondary_scores=None):
    return {
        "fixture_id": fid,
        "suite_id": "search-v1",
        "score": score,
        "structural_passed": True,
        "produced_output": True,
        "wall_time_seconds": 1.0,
        "dimension_scores": secondary_scores or [score, score],
    }


# --- (a) fixtures_detail additive field -------------------------------------


def test_aggregate_suite_results_emits_fixtures_detail():
    suite_manifest = _make_suite_manifest(["geo-a", "geo-b", "geo-c"])
    fixtures_by_domain = {
        d: [] for d in ev.DOMAINS
    }
    # Build Fixture dataclasses so the aggregator's domain map is honest.
    fixtures_by_domain["geo"] = [
        ev._fixture_from_payload(
            "search-v1", "geo", payload,
        )
        for payload in suite_manifest["domains"]["geo"]
    ]
    for other in ev.DOMAINS:
        if other != "geo":
            fixtures_by_domain[other] = []

    scored_fixtures = {d: [] for d in ev.DOMAINS}
    scored_fixtures["geo"] = [
        _scored_fixture("geo-a", 0.6, [0.55, 0.65]),
        _scored_fixture("geo-b", 0.7, [0.68, 0.72]),
        _scored_fixture("geo-c", 0.5),
    ]

    scores, aggregated = ev._aggregate_suite_results(
        suite_manifest, fixtures_by_domain, scored_fixtures,
    )
    geo_metrics = aggregated["domains"]["geo"]

    # Legacy `fixtures: int` must stay unchanged.
    assert geo_metrics["fixtures"] == 3
    assert isinstance(geo_metrics["fixtures"], int)

    # New additive `fixtures_detail`: one entry per fixture with score + secondary.
    detail = geo_metrics["fixtures_detail"]
    assert set(detail.keys()) == {"geo-a", "geo-b", "geo-c"}
    for fid, expected in (("geo-a", 0.6), ("geo-b", 0.7), ("geo-c", 0.5)):
        row = detail[fid]
        assert row["score"] == pytest.approx(expected)
        assert isinstance(row["secondary_score"], float)
    # secondary_score = mean of dimension_scores
    assert detail["geo-a"]["secondary_score"] == pytest.approx((0.55 + 0.65) / 2)


def test_aggregate_suite_results_empty_domain_still_safe():
    suite_manifest = _make_suite_manifest([])
    fixtures_by_domain = {d: [] for d in ev.DOMAINS}
    scored_fixtures = {d: [] for d in ev.DOMAINS}
    _scores, aggregated = ev._aggregate_suite_results(
        suite_manifest, fixtures_by_domain, scored_fixtures,
    )
    for domain in ev.DOMAINS:
        meta = aggregated["domains"][domain]
        assert meta["fixtures"] == 0
        assert meta["fixtures_detail"] == {}


# --- (b) promotion summary additive fields ----------------------------------


def test_search_promotion_summary_emits_none_when_holdout_not_run():
    summary = ev._search_promotion_summary(
        variant_entry={"id": "v010", "scores": {"composite": 0.5}},
        baseline_entry=None,
        search_suite_manifest={"suite_id": "search-v1"},
        require_holdout=False,
    )
    assert summary["eligible_for_promotion"] is True
    assert summary["reason"] == "search_scored"
    assert summary["holdout_composite"] is None
    assert summary["secondary_holdout_composite"] is None


def test_search_promotion_summary_emits_floats_when_holdout_ran():
    summary = ev._search_promotion_summary(
        variant_entry={"id": "v010", "scores": {"composite": 0.5}},
        baseline_entry={"id": "v009"},
        search_suite_manifest={"suite_id": "search-v1"},
        require_holdout=False,
        holdout_scores={"composite": 0.71, "geo": 0.8},
        secondary_holdout_scores={"composite": 0.68},
    )
    assert summary["eligible_for_promotion"] is True
    assert summary["holdout_composite"] == pytest.approx(0.71)
    assert summary["secondary_holdout_composite"] == pytest.approx(0.68)


def test_search_promotion_summary_require_holdout_still_additive():
    summary = ev._search_promotion_summary(
        variant_entry={"id": "v010"},
        baseline_entry=None,
        search_suite_manifest={"suite_id": "search-v1"},
        require_holdout=True,
    )
    assert summary["eligible_for_promotion"] is False
    assert summary["reason"] == "holdout_required"
    assert summary["holdout_composite"] is None
    assert summary["secondary_holdout_composite"] is None


# --- (c) _sample_fixtures rotation gate -------------------------------------


def _build_fixtures_for_sampling(n_per_domain=6):
    out: dict[str, list[ev.Fixture]] = {d: [] for d in ev.DOMAINS}
    for d in ev.DOMAINS:
        for i in range(n_per_domain):
            payload = {
                "fixture_id": f"{d}-{i}",
                "client": "acme",
                "context": "https://acme.com",
                "version": "1.0",
                "anchor": i == 0,
                "max_iter": 1,
                "timeout": 60,
            }
            out[d].append(ev._fixture_from_payload("search-v1", d, payload))
    return out


def test_sample_fixtures_deterministic_with_cohort_id(monkeypatch):
    fixtures = _build_fixtures_for_sampling(n_per_domain=6)
    rotation_config = {
        "strategy": "stratified",
        "seed_source": "generation",
        "random_per_domain": 2,
        "cohort_size": 3,
    }
    monkeypatch.setenv("EVOLUTION_COHORT_ID", "cohort-A")
    pick1 = ev._sample_fixtures(fixtures, rotation_config, "v010")
    pick2 = ev._sample_fixtures(fixtures, rotation_config, "v011")  # different variant_id
    for domain in ev.DOMAINS:
        ids1 = [f.fixture_id for f in pick1[domain]]
        ids2 = [f.fixture_id for f in pick2[domain]]
        assert ids1 == ids2, f"cohort-scoped sampling drifted for {domain}"


def test_sample_fixtures_variant_seed_drifts_across_variants(monkeypatch):
    fixtures = _build_fixtures_for_sampling(n_per_domain=6)
    rotation_config = {
        "strategy": "stratified",
        "seed_source": "variant_id",
        "random_per_domain": 2,
    }
    monkeypatch.delenv("EVOLUTION_COHORT_ID", raising=False)
    pick_a = ev._sample_fixtures(fixtures, rotation_config, "v010")
    pick_b = ev._sample_fixtures(fixtures, rotation_config, "v123")
    # At least one domain should differ when each variant is its own seed.
    differs = any(
        [f.fixture_id for f in pick_a[d]] != [f.fixture_id for f in pick_b[d]]
        for d in ev.DOMAINS
    )
    assert differs


# --- (d) _refresh_monitoring_scores_for_baseline ---------------------------


def _baseline_entry_with_detail(monitoring_env=True):
    env = {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"} if monitoring_env else {}
    return {
        "id": "v006",
        "search_metrics": {
            "domains": {
                "monitoring": {
                    "fixtures_detail": {
                        "mon-a": {"score": 0.4, "secondary_score": 0.4, "fixture_env": env},
                    },
                },
                "geo": {
                    "fixtures_detail": {
                        "geo-a": {"score": 0.6, "secondary_score": 0.6},
                    },
                },
            },
        },
    }


def test_refresh_monitoring_scores_for_baseline_no_rescorer_returns_clone(tmp_path):
    entry = _baseline_entry_with_detail()
    cloned = ev._refresh_monitoring_scores_for_baseline(
        entry, lane="core", archive_root=tmp_path,
    )
    # Deep clone — mutating the result must not touch the original.
    cloned["search_metrics"]["domains"]["monitoring"]["fixtures_detail"]["mon-a"]["score"] = 0.99
    assert entry["search_metrics"]["domains"]["monitoring"]["fixtures_detail"]["mon-a"]["score"] == 0.4


def test_refresh_monitoring_scores_for_baseline_updates_only_monitoring(tmp_path):
    entry = _baseline_entry_with_detail()
    suite_manifest = {
        "suite_id": "search-v1",
        "domains": {
            "monitoring": [
                {
                    "fixture_id": "mon-a",
                    "client": "acme",
                    "context": "https://acme.com",
                    "version": "1.0",
                    "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"},
                }
            ],
            "geo": [
                {
                    "fixture_id": "geo-a",
                    "client": "acme",
                    "context": "https://acme.com",
                    "version": "1.0",
                }
            ],
        },
    }

    def fake_rescore(baseline, fid, lane, archive_root):
        if fid == "mon-a":
            return {"score": 0.95, "secondary_score": 0.93}
        raise AssertionError(f"rescore_fn should only be called for monitoring fixtures, got {fid!r}")

    result = ev._refresh_monitoring_scores_for_baseline(
        entry, lane="core", archive_root=tmp_path,
        suite_manifest=suite_manifest,
        rescore_fn=fake_rescore,
    )
    # Monitoring fixture updated:
    mon_detail = result["search_metrics"]["domains"]["monitoring"]["fixtures_detail"]["mon-a"]
    assert mon_detail["score"] == pytest.approx(0.95)
    assert mon_detail["secondary_score"] == pytest.approx(0.93)
    # Non-monitoring fixture untouched:
    geo_detail = result["search_metrics"]["domains"]["geo"]["fixtures_detail"]["geo-a"]
    assert geo_detail["score"] == pytest.approx(0.6)
    # Original entry still intact (deep clone contract):
    orig_mon = entry["search_metrics"]["domains"]["monitoring"]["fixtures_detail"]["mon-a"]
    assert orig_mon["score"] == pytest.approx(0.4)
