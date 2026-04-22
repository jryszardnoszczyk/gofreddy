"""Tests for ``evaluate_single_fixture`` — Phase 7 Step 3.

Exercises the judge-based dry-run entry point. ``_run_fixture_session`` and
``_score_session`` are stubbed via monkeypatch so the test exercises the
orchestration (N seeds, per-replicate AUTORESEARCH_SEED, aggregate shape)
without spinning up the judge service or a real variant directory.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def suite_manifest_path(tmp_path):
    def _make(suite_id="search-v1", fixture_id="geo-a", anchor=False, extra_fixtures=None):
        fixtures = [
            {
                "fixture_id": fixture_id,
                "client": "acme",
                "context": "https://acme.com",
                "version": "1.0",
                "anchor": anchor,
                "max_iter": 1,
                "timeout": 60,
            }
        ]
        if extra_fixtures:
            fixtures.extend(extra_fixtures)
        payload = {
            "suite_id": suite_id,
            "version": "1.0",
            "objective_domain": "geo",
            "eval_target": {
                "backend": "codex",
                "model": "gpt-5.4",
                "reasoning_effort": "low",
            },
            "domains": {"geo": fixtures},
        }
        path = tmp_path / "suite.json"
        path.write_text(json.dumps(payload))
        return path
    return _make


@pytest.fixture
def stubbed_eval(monkeypatch, tmp_path):
    """Replace _run_fixture_session + _score_session with in-process stubs.

    Records the per-seed AUTORESEARCH_SEED value into the returned
    ``seeds_seen`` list and returns a deterministic score per call.
    """
    from autoresearch import evaluate_variant as ev

    seeds_seen: list[str | None] = []
    scores_to_return: list[float] = [0.61, 0.58, 0.63, 0.59, 0.62]
    call_count = {"count": 0}

    def fake_run_fixture_session(variant_dir, fixture, eval_target):
        # capture the seed label the caller staged into the environment
        seeds_seen.append(os.environ.get("AUTORESEARCH_SEED"))
        return ev.SessionRun(
            fixture=fixture,
            session_dir=None,
            produced_output=True,
            runner_exit_code=0,
            wall_time_seconds=1.0,
        )

    def fake_score_session(run, *, variant_id, campaign_id):
        i = call_count["count"]
        call_count["count"] += 1
        score = scores_to_return[i % len(scores_to_return)]
        return {
            "fixture_id": run.fixture.fixture_id,
            "suite_id": run.fixture.suite_id,
            "score": score,
            "structural_passed": True,
            "produced_output": True,
            "wall_time_seconds": 1.0,
            "warnings": [],
            "dimension_scores": [score - 0.01, score + 0.01],
        }

    # Create a fake archive dir with a baseline directory so the pre-flight
    # existence check passes.
    archive = tmp_path / "archive"
    (archive / "v006").mkdir(parents=True)
    (archive / "v006" / "run.py").write_text("# stub runner\n")

    monkeypatch.setattr(ev, "_run_fixture_session", fake_run_fixture_session)
    monkeypatch.setattr(ev, "_score_session", fake_score_session)

    return {
        "seeds_seen": seeds_seen,
        "scores": scores_to_return,
        "archive": archive,
    }


def test_evaluate_single_fixture_runs_n_seeds(suite_manifest_path, stubbed_eval):
    from autoresearch.evaluate_variant import evaluate_single_fixture

    manifest_path = suite_manifest_path()
    result = evaluate_single_fixture(
        "geo-a",
        manifest_path=manifest_path,
        pool="search-v1",
        baseline="v006",
        seeds=3,
        cache_root="/tmp/unused",
        archive_root=stubbed_eval["archive"],
    )
    assert len(result["per_seed_scores"]) == 3
    assert result["per_seed_scores"] == stubbed_eval["scores"][:3]
    assert result["fixture_id"] == "geo-a"
    assert result["fixture_version"] == "1.0"
    assert result["structural_passed"] is True
    assert isinstance(result["cost_usd"], float)
    assert "duration_seconds" in result
    # Each seed should have surfaced AUTORESEARCH_SEED as a distinct label.
    labels = stubbed_eval["seeds_seen"]
    assert labels == ["0", "1", "2"]


def test_evaluate_single_fixture_fixture_not_found(suite_manifest_path, stubbed_eval):
    from autoresearch.evaluate_variant import evaluate_single_fixture

    manifest_path = suite_manifest_path()
    with pytest.raises(KeyError) as excinfo:
        evaluate_single_fixture(
            "geo-missing",
            manifest_path=manifest_path,
            pool="search-v1",
            baseline="v006",
            seeds=2,
            cache_root="/tmp/unused",
            archive_root=stubbed_eval["archive"],
        )
    assert "geo-missing" in str(excinfo.value)


def test_evaluate_single_fixture_pool_mismatch(suite_manifest_path, stubbed_eval):
    from autoresearch.evaluate_variant import evaluate_single_fixture

    manifest_path = suite_manifest_path(suite_id="search-v1")
    with pytest.raises(ValueError) as excinfo:
        evaluate_single_fixture(
            "geo-a",
            manifest_path=manifest_path,
            pool="holdout-v1",  # mismatch
            baseline="v006",
            seeds=2,
            cache_root="/tmp/unused",
            archive_root=stubbed_eval["archive"],
        )
    msg = str(excinfo.value)
    assert "holdout-v1" in msg and "search-v1" in msg


def test_evaluate_single_fixture_restores_prior_autoresearch_seed(
    suite_manifest_path, stubbed_eval, monkeypatch,
):
    """After running, AUTORESEARCH_SEED returns to its prior value."""
    from autoresearch.evaluate_variant import evaluate_single_fixture

    monkeypatch.setenv("AUTORESEARCH_SEED", "sentinel")
    manifest_path = suite_manifest_path()
    evaluate_single_fixture(
        "geo-a",
        manifest_path=manifest_path,
        pool="search-v1",
        baseline="v006",
        seeds=2,
        cache_root="/tmp/unused",
        archive_root=stubbed_eval["archive"],
    )
    assert os.environ.get("AUTORESEARCH_SEED") == "sentinel"


def test_find_one_fixture_returns_payload(suite_manifest_path, stubbed_eval):
    from autoresearch.evaluate_variant import _find_one_fixture

    suite_payload = json.loads(Path(suite_manifest_path()).read_text())
    fixture, domain = _find_one_fixture(suite_payload, "geo-a")
    assert fixture.fixture_id == "geo-a"
    assert fixture.version == "1.0"
    assert domain == "geo"


def test_find_one_fixture_raises_key_error(suite_manifest_path, stubbed_eval):
    from autoresearch.evaluate_variant import _find_one_fixture

    suite_payload = json.loads(Path(suite_manifest_path()).read_text())
    with pytest.raises(KeyError) as excinfo:
        _find_one_fixture(suite_payload, "geo-missing")
    assert "geo-missing" in str(excinfo.value)
