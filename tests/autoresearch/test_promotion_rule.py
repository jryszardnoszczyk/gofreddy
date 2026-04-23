"""Plan B Phase 6 Steps 1-5 — promotion-rule tests.

Mocks ``call_promotion_judge`` to return specific verdicts, asserts
``is_promotable`` propagates them. Exercises:
- Wrong-lane short-circuit (invariant, not judgment)
- Promote/reject propagation
- Abstain path (decision != {promote, reject}) → False
- Blocking-severity concerns → False (belt + suspenders with abstain)
- JudgeUnreachable → False + events log record
- First-of-lane (no baseline)

MVP carve-out: Step 6 auto-rollback + secondary per-fixture re-scoring
infrastructure is deferred to a follow-up plan. Tests here cover only the
is_promotable shim's direct path.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from autoresearch.judges.promotion_judge import PromotionVerdict, JudgeUnreachable


def _entry(variant_id: str, public_score: float, *, secondary_public: float | None = None) -> dict:
    """Minimum lineage-entry shape ``is_promotable`` reads."""
    entry = {
        "id": variant_id,
        "lane": "geo",
        "scores": {"composite": public_score, "geo": public_score},
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": public_score,
            "domains": {
                "geo": {
                    "score": public_score,
                    "active": True,
                    "fixtures": {"geo-a": {"score": public_score}},
                },
            },
        },
        "promotion_summary": {
            "eligible_for_promotion": True,
            "holdout_composite": public_score - 0.05,
        },
    }
    if secondary_public is not None:
        entry["secondary_scores"] = {"composite": secondary_public, "geo": secondary_public}
        entry["promotion_summary"]["secondary_holdout_composite"] = secondary_public - 0.05
        entry["search_metrics"]["domains"]["geo"]["fixtures"]["geo-a"]["secondary_score"] = secondary_public
    return entry


def _verdict(decision: str, reasoning: str = "mock", *, confidence: float = 0.9, concerns=None) -> PromotionVerdict:
    return PromotionVerdict(
        decision=decision, reasoning=reasoning, confidence=confidence,
        concerns=list(concerns or []),
    )


@pytest.fixture
def events_log(tmp_path, monkeypatch):
    """Point the events log at a tmp path so tests don't clobber the user's log."""
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", p)
    return p


def _run(lineage, baseline, variant_id, archive_dir, *, verdict=None, raise_unreachable=False):
    """Invoke ``is_promotable`` with lineage + baseline + verdict mocked.

    Imports inside the function so the module reload (below) happens AFTER
    the events.EVENTS_LOG patch has landed.
    """
    from autoresearch.evolve_ops import is_promotable

    def _fake_lineage(_archive_dir):
        return lineage

    if raise_unreachable:
        call = patch(
            "autoresearch.judges.promotion_judge.call_promotion_judge",
            side_effect=JudgeUnreachable("service down"),
        )
    else:
        call = patch(
            "autoresearch.judges.promotion_judge.call_promotion_judge",
            return_value=verdict,
        )

    # Patch targets use the unprefixed `evaluate_variant` import path that
    # ``is_promotable`` uses (autoresearch/ is on sys.path via conftest; the
    # unprefixed module object is distinct from autoresearch.evaluate_variant
    # in sys.modules, so patch targets must match the caller's import form).
    with patch("autoresearch.evolve_ops._load_latest_lineage", side_effect=_fake_lineage), \
         patch("evaluate_variant._promotion_baseline", return_value=baseline), \
         patch(
             "evaluate_variant._refresh_monitoring_scores_for_baseline",
             side_effect=lambda entry, lane, archive_root: entry,
         ), \
         call as mock_judge:
        result = is_promotable(archive_dir, variant_id, "geo")
    return result, mock_judge


# --- happy paths ---------------------------------------------------------


def test_promotes_when_judge_says_promote(tmp_path, events_log):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict("promote"),
    )
    assert result is True


def test_rejects_when_judge_says_reject(tmp_path, events_log):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict("reject"),
    )
    assert result is False


def test_promotes_first_of_lane_when_judge_approves(tmp_path, events_log):
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v007": candidate}, None, "v007", tmp_path,
        verdict=_verdict("promote"),
    )
    assert result is True


def test_rejects_first_of_lane_when_judge_rejects(tmp_path, events_log):
    candidate = _entry("v007", 0.15, secondary_public=0.13)
    result, _ = _run(
        {"v007": candidate}, None, "v007", tmp_path,
        verdict=_verdict("reject"),
    )
    assert result is False


# --- invariant -----------------------------------------------------------


def test_wrong_lane_short_circuits_judge(tmp_path, events_log):
    """Wrong-lane is an invariant guard — judge never invoked."""
    candidate = dict(_entry("v007", 0.65), lane="core")  # lane ≠ "geo"
    from autoresearch.evolve_ops import is_promotable
    with patch("autoresearch.evolve_ops._load_latest_lineage", return_value={"v007": candidate}), \
         patch("autoresearch.judges.promotion_judge.call_promotion_judge") as mock_judge:
        result = is_promotable(tmp_path, "v007", "geo")
    assert result is False
    mock_judge.assert_not_called()


# --- abstain / blocking-concerns -----------------------------------------


def test_abstain_verdict_returns_false(tmp_path, events_log):
    """Decision != {promote, reject} → False (don't promote on incomplete signal)."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict("abstain", reasoning="too close to call"),
    )
    assert result is False


def test_blocking_concern_overrides_promote_verdict(tmp_path, events_log):
    """Belt + suspenders: dict-shaped concern with severity='blocking' blocks promote."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict(
            "promote",
            concerns=[{"severity": "blocking", "description": "holdout regression on 3/4 fixtures"}],
        ),
    )
    assert result is False


def test_advisory_concern_does_not_block_promote(tmp_path, events_log):
    """Only 'blocking' severity triggers the belt-and-suspenders override."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict(
            "promote",
            concerns=[{"severity": "advisory", "description": "minor variance increase"}],
        ),
    )
    assert result is True


# --- judge outage --------------------------------------------------------


def test_judge_unreachable_returns_false_and_logs_event(tmp_path, events_log):
    """JudgeUnreachable → False + kind=promotion_decision reason=judge_unreachable."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        raise_unreachable=True,
    )
    assert result is False
    # verify event logged
    from autoresearch.events import read_events
    records = list(read_events(kind="promotion_decision", path=events_log))
    assert len(records) == 1
    assert records[0]["decision"] == "reject"
    assert records[0]["reason"] == "judge_unreachable"


def test_decision_logged_with_reasoning(tmp_path, events_log):
    """promote/reject decisions land in events log with reasoning intact."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    result, _ = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict("reject", reasoning="insufficient holdout signal"),
    )
    assert result is False
    from autoresearch.events import read_events
    records = list(read_events(kind="promotion_decision", path=events_log))
    assert len(records) == 1
    assert records[0]["decision"] == "reject"
    assert "insufficient holdout signal" in records[0]["reasoning"]


# --- payload shape -------------------------------------------------------


def test_per_fixture_scores_handles_int_fixtures_shape(tmp_path, events_log):
    """Regression: real lineage has `fixtures: <int>` (count), not `fixtures: {...}`.

    ``_aggregate_suite_results`` doesn't preserve per-fixture records yet —
    until that lands, ``_per_fixture_scores`` must gracefully degrade to
    an empty dict rather than raise AttributeError (discovered via live
    is_promotable('v006', 'competitive') call 2026-04-23).
    """
    from autoresearch.evolve_ops import _per_fixture_scores

    entry = {
        "id": "v006",
        "search_metrics": {
            "domains": {
                "geo": {"score": 0.2, "fixtures": 3},  # int, not dict
                "competitive": {"score": 0.1, "fixtures": 0},
            },
        },
    }
    # Must not raise; returns {} because no per-fixture detail available.
    assert _per_fixture_scores(entry) == {}
    assert _per_fixture_scores(entry, key="secondary_score") == {}


def test_payload_contains_primary_and_secondary_scores(tmp_path, events_log):
    """Judge receives complete cross-family + per-fixture data."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    _, mock_judge = _run(
        {"v006": baseline, "v007": candidate}, baseline, "v007", tmp_path,
        verdict=_verdict("promote"),
    )
    payload = mock_judge.call_args[0][0]
    assert payload["role"] == "promotion"
    assert payload["candidate_id"] == "v007"
    assert payload["baseline_id"] == "v006"
    assert payload["lane"] == "geo"
    assert payload["candidate"]["secondary_public_score"] is not None
    assert payload["baseline"]["secondary_public_score"] is not None
    assert "geo-a" in payload["candidate"]["per_fixture_primary"]
    assert "geo-a" in payload["candidate"]["per_fixture_secondary"]
