"""Tests for ``freddy fixture dry-run`` — Phase 7 of Plan A.

Covers the five explicit verdict paths (healthy / saturated / degenerate /
unstable / cost_excess), the abstention path (``unclear`` → exit 2 +
``judge_abstain`` event), and the judge-unreachable path (raises).
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app
from cli.freddy.fixture.dryrun import JudgeUnreachable, QualityVerdict


@pytest.mark.parametrize(
    "per_seed_scores,cost_usd,mock_verdict,expected_exit",
    [
        ([0.50, 0.52, 0.48, 0.51, 0.49], 0.10, "healthy", 0),
        ([0.92, 0.91, 0.93, 0.90, 0.92], 0.10, "saturated", 1),
        ([0.05, 0.06, 0.04, 0.05, 0.07], 0.10, "degenerate", 1),
        ([0.50, 0.85, 0.15, 0.65, 0.35], 0.10, "unstable", 1),
        ([0.50, 0.52, 0.48, 0.51, 0.49], 2.50, "cost_excess", 1),
    ],
)
@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_delegates_to_quality_judge(
    mock_eval, mock_judge,
    per_seed_scores, cost_usd, mock_verdict, expected_exit,
    manifest_file, tmp_path,
):
    mock_eval.return_value = {
        "per_seed_scores": per_seed_scores,
        "structural_passed": True,
        "cost_usd": cost_usd,
        "duration_seconds": 12,
        "warnings": [],
    }
    mock_judge.return_value = QualityVerdict(
        verdict=mock_verdict,
        reasoning=f"Mocked verdict: {mock_verdict}",
        confidence=0.85,
        recommended_action=None,
    )
    runner = CliRunner()
    result = runner.invoke(
        fixture_app,
        [
            "dry-run", "geo-a",
            "--manifest", manifest_file(),
            "--pool", "search-v1",
            "--baseline", "v006",
            "--seeds", str(len(per_seed_scores)),
            "--cache-root", str(tmp_path / "cache"),
        ],
    )
    assert result.exit_code == expected_exit, result.output
    # The verdict string is in the JSON report that's echoed to stdout.
    assert mock_verdict in result.output.lower()

    # Verify the payload passed to the judge carries the raw stats —
    # there must be no thresholding inside dryrun.py.
    judge_payload = mock_judge.call_args[0][0]
    assert judge_payload["role"] == "fixture_quality"
    assert judge_payload["stats"]["per_seed_scores"] == per_seed_scores
    assert judge_payload["stats"]["cost_usd"] == cost_usd
    assert "median" in judge_payload["stats"]
    assert "mad" in judge_payload["stats"]
    assert judge_payload["fixture_metadata"]["fixture_id"] == "geo-a"


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_unclear_verdict_logs_judge_abstain(
    mock_eval, mock_judge, manifest_file, tmp_path, monkeypatch,
):
    """An ``unclear`` verdict exits 2 and appends a ``judge_abstain`` event."""
    import autoresearch.events as events

    log_path = tmp_path / ".local/share/gofreddy/events.jsonl"
    monkeypatch.setattr(events, "EVENTS_LOG", log_path)

    mock_eval.return_value = {
        "per_seed_scores": [0.4, 0.5, 0.6],
        "structural_passed": True,
        "cost_usd": 0.1,
        "duration_seconds": 10,
        "warnings": [],
    }
    mock_judge.return_value = QualityVerdict(
        verdict="unclear",
        reasoning="Contradictory signal across seeds.",
        confidence=0.3,
        recommended_action="re-run with more seeds",
    )
    runner = CliRunner()
    result = runner.invoke(
        fixture_app,
        [
            "dry-run", "geo-a",
            "--manifest", manifest_file(),
            "--pool", "search-v1",
            "--seeds", "3",
            "--cache-root", str(tmp_path / "cache"),
        ],
    )
    assert result.exit_code == 2, result.output
    assert "unclear" in result.output.lower() or "abstained" in result.output.lower()

    assert log_path.exists(), "judge_abstain event was not persisted"
    lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    abstains = [json.loads(line) for line in lines if json.loads(line).get("kind") == "judge_abstain"]
    assert len(abstains) == 1
    record = abstains[0]
    assert record["fixture_id"] == "geo-a"
    assert record["pool"] == "search-v1"
    assert record["verdict"]["verdict"] == "unclear"
    assert record["per_seed_scores"] == [0.4, 0.5, 0.6]


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_judge_unreachable_fails_cli(
    mock_eval, mock_judge, manifest_file, tmp_path,
):
    """When the judge HTTP call raises, the CLI reports a clean error (exit 1)."""
    mock_eval.return_value = {
        "per_seed_scores": [0.5, 0.5, 0.5],
        "structural_passed": True,
        "cost_usd": 0.1,
        "duration_seconds": 8,
        "warnings": [],
    }
    mock_judge.side_effect = JudgeUnreachable("fixture_quality endpoint down")
    runner = CliRunner()
    result = runner.invoke(
        fixture_app,
        [
            "dry-run", "geo-a",
            "--manifest", manifest_file(),
            "--pool", "search-v1",
            "--seeds", "3",
            "--cache-root", str(tmp_path / "cache"),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "quality judge unreachable" in result.output.lower()


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_unknown_fixture_fails_cli(
    mock_eval, mock_judge, manifest_file, tmp_path,
):
    runner = CliRunner()
    result = runner.invoke(
        fixture_app,
        [
            "dry-run", "geo-nonexistent",
            "--manifest", manifest_file(),
            "--pool", "search-v1",
            "--seeds", "3",
            "--cache-root", str(tmp_path / "cache"),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "not found" in result.output.lower()
    mock_eval.assert_not_called()
    mock_judge.assert_not_called()


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_dryrun_pool_mismatch_fails_cli(
    mock_eval, mock_judge, manifest_file, tmp_path,
):
    runner = CliRunner()
    result = runner.invoke(
        fixture_app,
        [
            "dry-run", "geo-a",
            "--manifest", manifest_file(suite_id="search-v1"),
            "--pool", "holdout-v1",  # mismatch
            "--seeds", "3",
            "--cache-root", str(tmp_path / "cache"),
        ],
    )
    assert result.exit_code == 1, result.output
    assert "pool" in result.output.lower() and "suite_id" in result.output.lower()
    mock_eval.assert_not_called()
    mock_judge.assert_not_called()
