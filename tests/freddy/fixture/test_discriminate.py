"""Phase 10: freddy fixture discriminate.

The agent receives RAW per-variant score distributions and decides
separability. No thresholds live in the CLI — tests assert the payload
shape and the verdict-to-report wiring, not any p-value boundary.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.freddy.commands.fixture import app as fixture_app
from cli.freddy.fixture.dryrun import QualityVerdict, run_discriminability_check


def _eval_side_effect(mapping: dict[str, list[float]]):
    """Build a side_effect honoring _run_single_fixture_eval(fid, mp, pool, variant, seeds, root)."""
    def _side(_fid, _mp, _pool, variant, _seeds, _root):
        return {"per_seed_scores": mapping[variant], "structural_passed": True, "cost_usd": 0.0}
    return _side


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_separable_when_agent_says_so(mock_eval, mock_judge, manifest_file):
    mock_eval.side_effect = _eval_side_effect({
        "v_low": [0.10, 0.12, 0.09, 0.11, 0.13],
        "v_high": [0.82, 0.85, 0.80, 0.83, 0.86],
    })
    mock_judge.return_value = QualityVerdict(
        verdict="separable",
        reasoning="clear separation between distributions",
        confidence=0.95,
    )
    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_low", "v_high"], seeds=10,
    )
    assert report.verdict == "separable"
    call_payload = mock_judge.call_args.args[0]
    assert call_payload["role"] == "discriminability"
    assert "variant_scores" in call_payload
    assert call_payload["variant_scores"]["v_low"] == [0.10, 0.12, 0.09, 0.11, 0.13]
    assert call_payload["variant_scores"]["v_high"] == [0.82, 0.85, 0.80, 0.83, 0.86]


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_not_separable_when_agent_says_so(mock_eval, mock_judge, manifest_file):
    mock_eval.side_effect = _eval_side_effect({
        "v_a": [0.50, 0.52, 0.48, 0.51, 0.49],
        "v_b": [0.51, 0.49, 0.52, 0.50, 0.48],
    })
    mock_judge.return_value = QualityVerdict(
        verdict="not_separable",
        reasoning="distributions overlap substantially",
        confidence=0.88,
    )
    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_a", "v_b"], seeds=10,
    )
    assert report.verdict == "not_separable"


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_insufficient_data_when_agent_says_so(mock_eval, mock_judge, manifest_file):
    mock_eval.side_effect = _eval_side_effect({
        "v_a": [0.40, 0.60],
        "v_b": [0.50, 0.55],
    })
    mock_judge.return_value = QualityVerdict(
        verdict="insufficient_data",
        reasoning="only 2 seeds per variant — cannot judge from this few samples",
        confidence=0.40,
    )
    report = run_discriminability_check(
        fixture_id="geo-a", pool="search-v1",
        manifest_path=Path(manifest_file()),
        variants=["v_a", "v_b"], seeds=2,
    )
    assert report.verdict == "insufficient_data"


def test_rejects_single_variant(manifest_file):
    with pytest.raises(ValueError, match="at least two"):
        run_discriminability_check(
            fixture_id="geo-a", pool="search-v1",
            manifest_path=Path(manifest_file()),
            variants=["v_a"], seeds=10,
        )


def test_rejects_pool_manifest_mismatch(manifest_file):
    with pytest.raises(ValueError, match="cross-pool"):
        run_discriminability_check(
            fixture_id="geo-a", pool="holdout-v1",
            manifest_path=Path(manifest_file()),  # default suite_id="search-v1"
            variants=["v_a", "v_b"], seeds=10,
        )


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_cli_discriminate_exits_nonzero_on_not_separable(
    mock_eval, mock_judge, manifest_file,
):
    mock_eval.side_effect = _eval_side_effect({
        "v_a": [0.50, 0.51, 0.49],
        "v_b": [0.50, 0.51, 0.49],
    })
    mock_judge.return_value = QualityVerdict(
        verdict="not_separable", reasoning="identical distributions", confidence=0.99,
    )
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "discriminate", "geo-a",
        "--manifest", manifest_file(),
        "--pool", "search-v1",
        "--variants", "v_a,v_b",
        "--seeds", "3",
    ])
    assert result.exit_code != 0
    assert "not_separable" in result.output


@patch("cli.freddy.fixture.dryrun.call_quality_judge")
@patch("cli.freddy.fixture.dryrun._run_single_fixture_eval")
def test_cli_discriminate_exits_zero_on_separable(
    mock_eval, mock_judge, manifest_file,
):
    mock_eval.side_effect = _eval_side_effect({
        "v_a": [0.10, 0.12, 0.11],
        "v_b": [0.85, 0.87, 0.86],
    })
    mock_judge.return_value = QualityVerdict(
        verdict="separable", reasoning="clear split", confidence=0.95,
    )
    runner = CliRunner()
    result = runner.invoke(fixture_app, [
        "discriminate", "geo-a",
        "--manifest", manifest_file(),
        "--pool", "search-v1",
        "--variants", "v_a,v_b",
        "--seeds", "3",
    ])
    assert result.exit_code == 0
    assert "separable" in result.output
