"""Plan B Phase 4 Step 3b — judge calibration drift tests.

Mocks ``call_quality_judge`` + writes a synthetic calibration-pairs config
to a tmp path. Verifies ``check()`` returns 0 on stable, 1 on any drift
verdict, 2 on missing/malformed config.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoresearch.judges.quality_judge import QualityVerdict


@pytest.fixture
def pairs_path(tmp_path, monkeypatch):
    p = tmp_path / "calibration-pairs.json"
    monkeypatch.setattr("autoresearch.judge_calibration.CALIBRATION_PAIRS_PATH", p)
    return p


@pytest.fixture
def events_log(tmp_path, monkeypatch):
    p = tmp_path / "events.jsonl"
    monkeypatch.setattr("autoresearch.events.EVENTS_LOG", p)
    return p


def _write_pairs(pairs_path: Path, pairs: list) -> None:
    import json
    pairs_path.write_text(json.dumps({"pairs": pairs}))


def _mock_verdict(verdict: str, reasoning: str = "mock reasoning",
                  confidence: float = 0.8) -> QualityVerdict:
    return QualityVerdict(
        verdict=verdict, reasoning=reasoning,
        confidence=confidence, recommended_action=None,
    )


def test_check_returns_0_when_stable(pairs_path, events_log):
    _write_pairs(pairs_path, [{"variant": "v001", "fixture": "geo-moz-homepage"}])
    from autoresearch.judge_calibration import check
    from autoresearch.events import read_events

    with patch(
        "autoresearch.judges.quality_judge.call_quality_judge",
        return_value=_mock_verdict("stable"),
    ):
        rc = check()
    assert rc == 0
    records = list(read_events(kind="judge_drift", path=events_log))
    assert len(records) == 1
    assert records[0]["verdict"] == "stable"


@pytest.mark.parametrize("drift_verdict", [
    "magnitude_drift", "variance_drift", "reasoning_drift", "mixed",
])
def test_check_returns_1_on_drift(pairs_path, events_log, drift_verdict):
    _write_pairs(pairs_path, [{"variant": "v001", "fixture": "geo-moz-homepage"}])
    from autoresearch.judge_calibration import check

    with patch(
        "autoresearch.judges.quality_judge.call_quality_judge",
        return_value=_mock_verdict(drift_verdict),
    ):
        rc = check()
    assert rc == 1


def test_check_returns_2_when_pairs_missing(pairs_path, events_log):
    """CALIBRATION_PAIRS_PATH doesn't exist → exit 2, no judge call."""
    from autoresearch.judge_calibration import check
    with patch("autoresearch.judges.quality_judge.call_quality_judge") as mock_judge:
        rc = check()
    assert rc == 2
    mock_judge.assert_not_called()


def test_check_returns_2_when_pairs_malformed(pairs_path, events_log):
    pairs_path.write_text("{not valid json}")
    from autoresearch.judge_calibration import check
    with patch("autoresearch.judges.quality_judge.call_quality_judge") as mock_judge:
        rc = check()
    assert rc == 2
    mock_judge.assert_not_called()


def test_check_returns_2_when_pairs_empty(pairs_path, events_log):
    _write_pairs(pairs_path, [])
    from autoresearch.judge_calibration import check
    with patch("autoresearch.judges.quality_judge.call_quality_judge") as mock_judge:
        rc = check()
    assert rc == 2
    mock_judge.assert_not_called()


def test_main_cli_dispatches_to_check(pairs_path, events_log):
    _write_pairs(pairs_path, [{"variant": "v001", "fixture": "geo-moz-homepage"}])
    from autoresearch.judge_calibration import main
    with patch(
        "autoresearch.judges.quality_judge.call_quality_judge",
        return_value=_mock_verdict("stable"),
    ):
        rc = main(["--check"])
    assert rc == 0


def test_main_cli_usage_on_unknown_args(pairs_path, events_log):
    from autoresearch.judge_calibration import main
    assert main([]) == 2
    assert main(["--unknown"]) == 2
