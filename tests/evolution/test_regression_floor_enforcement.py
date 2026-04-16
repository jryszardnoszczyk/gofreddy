"""Unit 3: regression-floor enforcement wiring in evaluate_variant.evaluate_search.

`_check_regression_floors` existed at the start of this change but was never
wired into the promotion gate — regressions were logged to failures.log but
the lineage entry still landed as a normal (promotable) variant.

This test suite locks in the fix:

1. `_check_regression_floors` uses an **inclusive** boundary (`<=`). A variant
   that drops exactly by `regression_floor` is treated as a regression.
2. `_rerun_specific_fixtures` re-scores only the offending fixtures (not the
   full suite) and returns results in the same shape as `scored_fixtures`.
3. The lineage entry emitted by `evaluate_search` carries
   `status == "discarded"` and `reason == "regression_floor"` when a
   regression is confirmed by the retry.
4. Flake handling (P1-5): if the first run flags a regression but the rerun
   does not, the lineage entry is NOT marked `discarded` (false-positive
   suppression).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import evaluate_variant  # type: ignore
from evaluate_variant import (  # type: ignore
    _check_regression_floors,
    _rerun_specific_fixtures,
)


def _fix(fid: str, score: float, floor: float = 0.20) -> dict[str, Any]:
    return {"fixture_id": fid, "score": score, "regression_floor": floor}


# ── _check_regression_floors behavior ──────────────────────────────────────


def test_check_regression_floors_no_parent_returns_empty() -> None:
    assert _check_regression_floors({"geo": [_fix("g1", 0.5)]}, None) == []


def test_check_regression_floors_improvement_returns_empty() -> None:
    parent = {"geo": [_fix("g1", 0.50)]}
    child = {"geo": [_fix("g1", 0.60)]}
    assert _check_regression_floors(child, parent) == []


def test_check_regression_floors_small_drop_below_floor_passes() -> None:
    """5% drop with 20% floor is allowed."""
    parent = {"geo": [_fix("g1", 0.50)]}
    child = {"geo": [_fix("g1", 0.45)]}  # -0.05
    assert _check_regression_floors(child, parent) == []


def test_check_regression_floors_large_drop_triggers() -> None:
    """25% drop with 20% floor is flagged."""
    parent = {"geo": [_fix("g1", 0.50)]}
    child = {"geo": [_fix("g1", 0.25)]}  # -0.25
    regressions = _check_regression_floors(child, parent)
    assert len(regressions) == 1
    reg = regressions[0]
    assert reg["domain"] == "geo"
    assert reg["fixture"] == "g1"
    assert reg["delta"] == -0.25
    assert reg["floor"] == 0.20


def test_check_regression_floors_exact_boundary_inclusive() -> None:
    """Exactly at the floor triggers the block (inclusive boundary)."""
    parent = {"geo": [_fix("g1", 0.50)]}
    child = {"geo": [_fix("g1", 0.30)]}  # -0.20 exactly
    assert len(_check_regression_floors(child, parent)) == 1


def test_check_regression_floors_just_below_boundary_passes() -> None:
    """19.9% drop does not trigger; 20% floor is the inclusive boundary."""
    parent = {"geo": [_fix("g1", 0.500)]}
    child = {"geo": [_fix("g1", 0.301)]}  # -0.199
    assert _check_regression_floors(child, parent) == []


def test_check_regression_floors_missing_parent_fixture_is_skipped() -> None:
    """A fixture that does not exist in the parent scores cannot regress."""
    parent = {"geo": [_fix("g1", 0.50)]}
    child = {"geo": [_fix("g1", 0.50), _fix("g2", 0.10)]}
    assert _check_regression_floors(child, parent) == []


# ── _rerun_specific_fixtures behavior ──────────────────────────────────────


@dataclass
class _FakeFixture:
    fixture_id: str
    domain: str
    client: str
    context: str
    max_iter: int = 1
    timeout: int = 60
    regression_floor: float = 0.20
    tags: tuple[str, ...] = ()
    env: dict[str, str] | None = None
    input_mode: str = "live"
    anchor: bool = False


@dataclass
class _FakeEvalTarget:
    backend: str = "codex"
    model: str = "gpt-5.4"
    reasoning_effort: str = "high"


def test_rerun_specific_fixtures_runs_only_the_offending_subset(monkeypatch, tmp_path) -> None:
    """The helper must call _run_fixture_session only for offending (domain, fixture_id) pairs."""
    fixtures_by_domain = {
        "geo": [
            _FakeFixture("g1", "geo", "c1", "ctx1"),
            _FakeFixture("g2", "geo", "c2", "ctx2"),
            _FakeFixture("g3", "geo", "c3", "ctx3"),
        ],
        "competitive": [
            _FakeFixture("co1", "competitive", "c1", "ctx1"),
        ],
    }

    called: list[str] = []

    def fake_run_fixture_session(variant_dir: Path, fixture, eval_target):
        called.append(fixture.fixture_id)

        class _FakeRun:
            produced_output = True

        return _FakeRun()

    def fake_score_session(run, *, variant_id, campaign_id):
        return {
            "fixture_id": run.__class__.__name__,  # not used; overwrite below
            "score": 0.50,
            "regression_floor": 0.20,
        }

    def fake_score_session_by_fixture(run, *, variant_id, campaign_id):
        fid = called[-1]
        return {"fixture_id": fid, "score": 0.50, "regression_floor": 0.20}

    monkeypatch.setattr(evaluate_variant, "_run_fixture_session", fake_run_fixture_session)
    monkeypatch.setattr(evaluate_variant, "_score_session", fake_score_session_by_fixture)

    offending = {("geo", "g2"), ("competitive", "co1")}
    rerun = _rerun_specific_fixtures(
        offending,
        fixtures_by_domain,
        variant_dir=tmp_path,
        eval_target=_FakeEvalTarget(),
        variant_id="v002",
        search_campaign_id="search-v1:v002",
    )

    # Only the offending fixtures were run
    assert sorted(called) == ["co1", "g2"]

    # Shape: same dict[domain, list[scored_dict]] format as scored_fixtures
    assert "geo" in rerun
    assert "competitive" in rerun
    assert [r["fixture_id"] for r in rerun["geo"]] == ["g2"]
    assert [r["fixture_id"] for r in rerun["competitive"]] == ["co1"]


def test_rerun_specific_fixtures_empty_offending_set_returns_empty(monkeypatch, tmp_path) -> None:
    calls: list[Any] = []
    monkeypatch.setattr(
        evaluate_variant,
        "_run_fixture_session",
        lambda *a, **k: calls.append(a) or None,  # type: ignore
    )
    monkeypatch.setattr(
        evaluate_variant,
        "_score_session",
        lambda *a, **k: {"fixture_id": "x", "score": 0.0, "regression_floor": 0.20},
    )

    result = _rerun_specific_fixtures(
        set(),
        {"geo": [_FakeFixture("g1", "geo", "c1", "ctx1")]},
        variant_dir=tmp_path,
        eval_target=_FakeEvalTarget(),
        variant_id="v002",
        search_campaign_id="search-v1:v002",
    )

    assert result == {}
    assert calls == []


# ── Flake-confirmed regression → discarded lineage entry ──────────────────


def test_flake_retry_drops_false_positive() -> None:
    """First run flags a regression; retry does not; final regressions list is empty."""
    parent = {"geo": [_fix("g1", 0.50), _fix("g2", 0.40)]}
    first_run = {
        "geo": [_fix("g1", 0.25), _fix("g2", 0.40)],  # g1 drops 25% (regression)
    }
    regressions = _check_regression_floors(first_run, parent)
    assert len(regressions) == 1

    # Simulate the retry seeing only a 10% drop (noise recovered)
    rerun_scores = {"geo": [_fix("g1", 0.40)]}  # only -0.10
    confirmed = _check_regression_floors(rerun_scores, parent)
    assert confirmed == []

    # Intersection of original and confirmed is empty → no block
    confirmed_keys = {(r["domain"], r["fixture"]) for r in confirmed}
    final = [r for r in regressions if (r["domain"], r["fixture"]) in confirmed_keys]
    assert final == []


def test_flake_retry_confirms_real_regression() -> None:
    """First run flags a regression; retry confirms it; final regressions list is non-empty."""
    parent = {"geo": [_fix("g1", 0.50)]}
    first_run = {"geo": [_fix("g1", 0.20)]}  # -0.30 drop
    regressions = _check_regression_floors(first_run, parent)
    assert len(regressions) == 1

    rerun_scores = {"geo": [_fix("g1", 0.22)]}  # -0.28 drop, still below floor
    confirmed = _check_regression_floors(rerun_scores, parent)
    assert len(confirmed) == 1

    confirmed_keys = {(r["domain"], r["fixture"]) for r in confirmed}
    final = [r for r in regressions if (r["domain"], r["fixture"]) in confirmed_keys]
    assert len(final) == 1
    assert final[0]["domain"] == "geo"
    assert final[0]["fixture"] == "g1"


# ── Source-level wiring guard in evaluate_search ───────────────────────────


def _read_evaluate_variant() -> str:
    return (AUTORESEARCH_DIR / "evaluate_variant.py").read_text(encoding="utf-8")


def test_evaluate_search_marks_lineage_entry_as_discarded_on_confirmed_regression() -> None:
    """The wiring must mutate the lineage entry so frontier readers filter it out."""
    source = _read_evaluate_variant()

    # The discarded-status mutation must exist in the source somewhere.
    assert '"status"' in source or "entry['status']" in source or 'entry["status"]' in source
    assert '"regression_floor"' in source
    assert '"discarded"' in source

    # Specifically: the mutation must sit BETWEEN the regression check and the
    # append_lineage_entry call, so it's the lineage row that lands on disk.
    regression_idx = source.find("_check_regression_floors(scored_fixtures")
    append_idx = source.find("append_lineage_entry(archive_dir, entry)")
    assert regression_idx != -1, "_check_regression_floors call must be present"
    assert append_idx != -1, "append_lineage_entry call must be present"
    assert regression_idx < append_idx, (
        "regression check must precede the lineage append"
    )
    between = source[regression_idx:append_idx]
    assert "discarded" in between, (
        "the regression-floor wiring must mark the lineage entry as discarded "
        "between the regression check and the lineage append"
    )
    assert "regression_floor" in between


def test_evaluate_search_uses_rerun_retry_for_regressions() -> None:
    """The flake mitigation (P1-5) must be in the source."""
    source = _read_evaluate_variant()
    assert "_rerun_specific_fixtures(" in source, (
        "the one-shot retry helper must be called from evaluate_search"
    )


# ── search-v1.json has the 20% floors ─────────────────────────────────────


def test_search_v1_all_fixtures_have_twenty_percent_regression_floor() -> None:
    import json

    suite_path = AUTORESEARCH_DIR / "eval_suites" / "search-v1.json"
    suite = json.loads(suite_path.read_text(encoding="utf-8"))

    fixture_count = 0
    for domain_name, fixtures in suite["domains"].items():
        for fixture in fixtures:
            fixture_count += 1
            assert fixture["regression_floor"] == 0.20, (
                f"{domain_name}/{fixture['fixture_id']} regression_floor "
                f"is {fixture['regression_floor']}, expected 0.20"
            )
    # Safety: make sure we actually saw all 12 fixtures
    assert fixture_count == 12, f"expected 12 fixtures, saw {fixture_count}"
