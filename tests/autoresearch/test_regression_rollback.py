"""Plan B Phase 6 Step 6 — automated rollback tests.

Seeds the unified events log with synthetic ``head_score`` records, mocks
``call_promotion_judge`` + ``subprocess.run``, and verifies the rollback
rule's behavior. No live judges; no live subprocess. Uses ``tmp_path`` +
``monkeypatch`` to isolate the events log from the user's real log.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoresearch.judges.promotion_judge import PromotionVerdict, JudgeUnreachable


@pytest.fixture
def events_log(tmp_path, monkeypatch):
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", p)
    return p


def _seed_head_score(lane: str, head_id: str, public: float, holdout: float | None = 0.5,
                     promoted_at: str = "2026-04-22T00:00:00Z") -> None:
    from autoresearch.evolve_ops import record_head_score
    record_head_score(
        lane=lane, head_id=head_id,
        public_score=public, holdout_score=holdout,
        promoted_at=promoted_at,
    )


def _force_past_dry_run(monkeypatch) -> None:
    """Rewind ROLLBACK_DRY_RUN_UNTIL_ISO to a past date so live rollback fires."""
    monkeypatch.setattr(
        "autoresearch.evolve_ops.ROLLBACK_DRY_RUN_UNTIL_ISO",
        "2020-01-01T00:00:00Z",
    )


# --- guard conditions ---------------------------------------------------


def test_no_rollback_when_no_events(events_log, tmp_path):
    from autoresearch.evolve_ops import check_and_rollback_regressions
    assert check_and_rollback_regressions(tmp_path, "geo") is False


def test_no_rollback_when_only_one_head_score(events_log, tmp_path):
    _seed_head_score("geo", "v006", 0.60)
    from autoresearch.evolve_ops import check_and_rollback_regressions
    assert check_and_rollback_regressions(tmp_path, "geo") is False


def test_no_rollback_when_only_current_head_scored(events_log, tmp_path):
    """No prior head means no baseline to compare against."""
    _seed_head_score("geo", "v007", 0.60)
    _seed_head_score("geo", "v007", 0.58)
    from autoresearch.evolve_ops import check_and_rollback_regressions
    assert check_and_rollback_regressions(tmp_path, "geo") is False


def test_no_rollback_when_only_one_post_sample(events_log, tmp_path):
    """Need ≥2 post-promotion samples on the current head."""
    _seed_head_score("geo", "v006", 0.65)
    _seed_head_score("geo", "v007", 0.60)  # only 1 post
    from autoresearch.evolve_ops import check_and_rollback_regressions
    assert check_and_rollback_regressions(tmp_path, "geo") is False


# --- agent decision paths -----------------------------------------------


def test_rollback_when_agent_says_rollback_post_dry_run_window(
    events_log, tmp_path, monkeypatch,
):
    """Agent says rollback + dry-run window over → subprocess.run called."""
    _force_past_dry_run(monkeypatch)
    _seed_head_score("geo", "v006", 0.65)  # prior
    _seed_head_score("geo", "v007", 0.60)  # post 1 (regression)
    _seed_head_score("geo", "v007", 0.58)  # post 2

    verdict = PromotionVerdict(
        decision="rollback",
        reasoning="monotonic decline below prior-head baseline",
        confidence=0.9, concerns=[],
    )

    from autoresearch.evolve_ops import check_and_rollback_regressions
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               return_value=verdict), \
         patch("subprocess.run") as mock_run:
        result = check_and_rollback_regressions(tmp_path, "geo")

    assert result is True
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--undo" in cmd
    assert "--lane" in cmd
    assert "geo" in cmd


def test_dry_run_logs_but_does_not_execute(events_log, tmp_path, monkeypatch):
    """Dry-run window active → decision logged, subprocess NOT called."""
    # Keep the shipped ROLLBACK_DRY_RUN_UNTIL_ISO (future date).
    _seed_head_score("geo", "v006", 0.65)
    _seed_head_score("geo", "v007", 0.60)
    _seed_head_score("geo", "v007", 0.58)

    verdict = PromotionVerdict(
        decision="rollback", reasoning="observed regression",
        confidence=0.85, concerns=[],
    )

    from autoresearch.evolve_ops import check_and_rollback_regressions
    from autoresearch.events import read_events
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               return_value=verdict), \
         patch("subprocess.run") as mock_run:
        result = check_and_rollback_regressions(tmp_path, "geo")

    assert result is False
    mock_run.assert_not_called()
    checks = list(read_events(kind="regression_check", path=events_log))
    # First log = the raw agent verdict; second log = the dry-run sentinel.
    decisions = [c.get("decision") for c in checks]
    assert "rollback" in decisions
    assert "rollback_dry_run" in decisions


def test_no_rollback_when_agent_says_hold(events_log, tmp_path, monkeypatch):
    _force_past_dry_run(monkeypatch)
    _seed_head_score("geo", "v006", 0.65)
    _seed_head_score("geo", "v007", 0.60)
    _seed_head_score("geo", "v007", 0.58)

    verdict = PromotionVerdict(
        decision="hold", reasoning="decline within expected variance",
        confidence=0.7, concerns=[],
    )

    from autoresearch.evolve_ops import check_and_rollback_regressions
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               return_value=verdict), \
         patch("subprocess.run") as mock_run:
        result = check_and_rollback_regressions(tmp_path, "geo")
    assert result is False
    mock_run.assert_not_called()


# --- cooldown + outage --------------------------------------------------


def _write_event_with_ts(events_log_path, *, timestamp: str, **kw) -> None:
    """Append a pre-formatted event to the log with an explicit timestamp.
    Bypasses ``log_event`` so tests can control event ordering in time.
    """
    import json
    record = {"timestamp": timestamp, **kw}
    with open(events_log_path, "a") as fh:
        fh.write(json.dumps(record) + "\n")


def test_cooldown_prevents_consecutive_rollbacks(events_log, tmp_path, monkeypatch):
    """Prior rollback at t3 + only 2 post-rollback head_scores → cooldown active.

    Sequence: v005 was head, v006 promoted, rollback fired, v005 restored,
    v005 scored twice more → only 2 head_scores since rollback, below the
    3-cycle cooldown threshold.
    """
    _force_past_dry_run(monkeypatch)
    # Pre-rollback: v005 → v006 transition.
    _write_event_with_ts(events_log, timestamp="2026-04-23T10:00:00Z",
                         kind="head_score", lane="geo", head_id="v006",
                         public_score=0.62, holdout_score=0.55,
                         promoted_at="2026-04-23T10:00:00Z")
    _write_event_with_ts(events_log, timestamp="2026-04-23T10:01:00Z",
                         kind="head_score", lane="geo", head_id="v006",
                         public_score=0.60, holdout_score=0.52,
                         promoted_at="2026-04-23T10:00:00Z")
    # Rollback fired at t=10:02; v005 restored.
    _write_event_with_ts(events_log, timestamp="2026-04-23T10:02:00Z",
                         kind="regression_check", lane="geo",
                         current_head="v006", decision="rollback",
                         reasoning="prior rollback")
    # Only 2 post-rollback head_scores on v005 — below the 3-cycle cooldown.
    _write_event_with_ts(events_log, timestamp="2026-04-23T10:03:00Z",
                         kind="head_score", lane="geo", head_id="v005",
                         public_score=0.55, holdout_score=0.48,
                         promoted_at="2026-04-23T10:02:30Z")
    _write_event_with_ts(events_log, timestamp="2026-04-23T10:04:00Z",
                         kind="head_score", lane="geo", head_id="v005",
                         public_score=0.54, holdout_score=0.47,
                         promoted_at="2026-04-23T10:02:30Z")

    verdict = PromotionVerdict(decision="rollback", reasoning="x",
                               confidence=0.9, concerns=[])
    from autoresearch.evolve_ops import check_and_rollback_regressions
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               return_value=verdict) as mock_judge, \
         patch("subprocess.run") as mock_run:
        result = check_and_rollback_regressions(tmp_path, "geo")
    assert result is False
    mock_judge.assert_not_called()  # cooldown short-circuits the judge call
    mock_run.assert_not_called()


def test_judge_unreachable_skips_rollback(events_log, tmp_path, monkeypatch):
    _force_past_dry_run(monkeypatch)
    _seed_head_score("geo", "v006", 0.65)
    _seed_head_score("geo", "v007", 0.60)
    _seed_head_score("geo", "v007", 0.58)

    from autoresearch.evolve_ops import check_and_rollback_regressions
    from autoresearch.events import read_events
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               side_effect=JudgeUnreachable("service down")), \
         patch("subprocess.run") as mock_run:
        result = check_and_rollback_regressions(tmp_path, "geo")
    assert result is False
    mock_run.assert_not_called()
    # regression_check event logged with decision=skip
    checks = list(read_events(kind="regression_check", path=events_log))
    assert any(c.get("decision") == "skip" and c.get("reason") == "judge_unreachable"
               for c in checks)


def test_agent_receives_full_pre_and_post_trajectory(events_log, tmp_path, monkeypatch):
    _force_past_dry_run(monkeypatch)
    _seed_head_score("geo", "v005", 0.55)
    _seed_head_score("geo", "v006", 0.65)
    _seed_head_score("geo", "v007", 0.60)
    _seed_head_score("geo", "v007", 0.58)

    verdict = PromotionVerdict(decision="hold", reasoning="x",
                               confidence=0.6, concerns=[])
    from autoresearch.evolve_ops import check_and_rollback_regressions
    with patch("autoresearch.judges.promotion_judge.call_promotion_judge",
               return_value=verdict) as mock_judge:
        check_and_rollback_regressions(tmp_path, "geo")

    payload = mock_judge.call_args[0][0]
    assert payload["role"] == "rollback"
    assert payload["lane"] == "geo"
    assert payload["current_head"] == "v007"
    assert payload["prior_head"] == "v006"  # most-recent non-current
    assert len(payload["post_promotion_trajectory"]) == 2
    assert len(payload["pre_promotion_trajectory"]) >= 2  # v005 + v006
