"""Plan B Phase 0 plumbing smoke-test (folded in per MVP carve-out 2026-04-23).

Plan B originally specified Phase 0 as a standalone phase verifying Plan A
Phase 7's --single-fixture subprocess path. The MVP review folded this into
a single pytest file.

This test pins the full return-shape contract of ``evaluate_single_fixture``
so Plan B's downstream phases (Phase 2 Step A dry-run, Phase 5 canary
checkpoint scoring, Phase 6 is_promotable plumbing) can rely on every key
being present with the documented type.
"""
from __future__ import annotations

import json
import os

import pytest


@pytest.fixture
def fake_session_layer(monkeypatch, tmp_path):
    """Stub the session-running + scoring layer so the smoke-test does not
    require the judge service or a real baseline variant to be running.
    """
    from autoresearch import evaluate_variant as ev

    seen_seeds: list[str | None] = []
    scores = [0.61, 0.58, 0.63, 0.59, 0.62]

    def fake_run_fixture_session(variant_dir, fixture, eval_target):
        seen_seeds.append(os.environ.get("AUTORESEARCH_SEED"))
        return ev.SessionRun(
            fixture=fixture,
            session_dir=None,
            produced_output=True,
            runner_exit_code=0,
            wall_time_seconds=1.0,
        )

    counter = {"i": 0}

    def fake_score_session(run, *, variant_id, campaign_id):
        i = counter["i"]
        counter["i"] += 1
        return {
            "fixture_id": run.fixture.fixture_id,
            "suite_id": run.fixture.suite_id,
            "score": scores[i % len(scores)],
            "structural_passed": True,
            "produced_output": True,
            "wall_time_seconds": 1.0,
            "warnings": [],
            "dimension_scores": [],
        }

    archive = tmp_path / "archive"
    (archive / "v006").mkdir(parents=True)
    (archive / "v006" / "run.py").write_text("# stub\n")

    monkeypatch.setattr(ev, "_run_fixture_session", fake_run_fixture_session)
    monkeypatch.setattr(ev, "_score_session", fake_score_session)
    return {"seen_seeds": seen_seeds, "scores": scores, "archive": archive}


@pytest.fixture
def suite_manifest_path(tmp_path):
    payload = {
        "suite_id": "search-v1",
        "version": "1.0",
        "objective_domain": "geo",
        "eval_target": {"backend": "codex", "model": "gpt-5.4", "reasoning_effort": "low"},
        "domains": {
            "geo": [{
                "fixture_id": "geo-smoke",
                "client": "smoketest",
                "context": "https://example.com",
                "version": "1.0",
                "anchor": False,
                "max_iter": 1,
                "timeout": 60,
            }],
        },
    }
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(payload))
    return path


def test_phase0_return_shape_contract(fake_session_layer, suite_manifest_path):
    """All keys documented in SCHEMA.md + evaluate_single_fixture's docstring
    must be present with the documented type — these are the keys Plan B's
    downstream phases read.
    """
    from autoresearch.evaluate_variant import evaluate_single_fixture

    result = evaluate_single_fixture(
        "geo-smoke",
        manifest_path=suite_manifest_path,
        pool="search-v1",
        baseline="v006",
        seeds=3,
        cache_root="/tmp/unused",
        archive_root=fake_session_layer["archive"],
    )

    # Required keys
    assert set(result.keys()) >= {
        "fixture_id", "fixture_version", "domain",
        "per_seed_scores", "structural_passed",
        "cost_usd", "duration_seconds", "warnings",
    }

    # Types
    assert isinstance(result["fixture_id"], str)
    assert isinstance(result["fixture_version"], str)
    assert isinstance(result["domain"], str)
    assert isinstance(result["per_seed_scores"], list)
    assert all(isinstance(s, float) for s in result["per_seed_scores"])
    assert isinstance(result["structural_passed"], bool)
    assert isinstance(result["cost_usd"], float)
    assert isinstance(result["duration_seconds"], int)
    assert result["duration_seconds"] >= 0
    assert isinstance(result["warnings"], list)

    # Requested seed count honored
    assert len(result["per_seed_scores"]) == 3


def test_phase0_autoresearch_seed_is_distinct_per_replicate(
    fake_session_layer, suite_manifest_path,
):
    """Plan B Phase 0 asserts AUTORESEARCH_SEED is set as a distinct
    per-replicate label (for log/artifact naming). SCHEMA.md pins semantics:
    the variant sampler does not read it; variance comes from LLM
    nondeterminism.
    """
    from autoresearch.evaluate_variant import evaluate_single_fixture

    evaluate_single_fixture(
        "geo-smoke",
        manifest_path=suite_manifest_path,
        pool="search-v1",
        baseline="v006",
        seeds=5,
        cache_root="/tmp/unused",
        archive_root=fake_session_layer["archive"],
    )
    assert fake_session_layer["seen_seeds"] == ["0", "1", "2", "3", "4"]


def test_phase0_pool_and_suite_id_must_agree(fake_session_layer, suite_manifest_path):
    """Mismatch between `--pool` and `manifest.suite_id` must raise ValueError.
    Plan A Phase 1 invariant; Plan B relies on this to prevent cross-pool
    reads."""
    from autoresearch.evaluate_variant import evaluate_single_fixture

    with pytest.raises(ValueError) as excinfo:
        evaluate_single_fixture(
            "geo-smoke",
            manifest_path=suite_manifest_path,
            pool="holdout-v1",
            baseline="v006",
            seeds=1,
            cache_root="/tmp/unused",
            archive_root=fake_session_layer["archive"],
        )
    assert "holdout-v1" in str(excinfo.value)
    assert "search-v1" in str(excinfo.value)
