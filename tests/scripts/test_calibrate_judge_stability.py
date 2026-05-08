"""Tests for scripts/calibrate_judge_stability.py.

The script is loaded via importlib because scripts/ is not a package on
sys.path. Tests use a fake post_fn so no live judge service is required.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "calibrate_judge_stability.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "calibrate_judge_stability", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load calibrate_judge_stability.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


calibrate_mod = _load_script_module()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_x_drafts(root: Path, count: int = 2) -> Path:
    drafts_dir = root / "x_engine"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    body_filler = (
        "21 priority creators, 50 search queries, 22 GitHub repos, 7 RSS feeds. "
        "x_engine pulls 375 tweets a day at zero dollars per run via codex CLI. "
        "Most AI content engines I have tested charge fifty dollars a month for "
        "half that surface area and ship slop drafts."
    )
    for i in range(count):
        (drafts_dir / f"draft-{i}.md").write_text(
            f"---\ndraft_id: cal-{i}\nplatform: x\nlength_bracket: sharp\n"
            f"voice_pillar: harness-engineering\n---\n\n[BODY]\n{body_filler}\n[/BODY]\n",
            encoding="utf-8",
        )
    return drafts_dir


def _make_response(
    primary_per_criterion: dict[str, float],
    secondary_per_criterion: dict[str, float] | None = None,
    *,
    primary_aggregate: float = 7.0,
    secondary_aggregate: float = 7.0,
) -> dict[str, Any]:
    """Build a judge-service-shaped response with the given per-criterion scores."""
    if secondary_per_criterion is None:
        secondary_per_criterion = primary_per_criterion
    return {
        "primary": {
            "per_criterion": [
                {"criterion": cid, "score": s, "rationale": "test"}
                for cid, s in primary_per_criterion.items()
            ],
            "aggregate_score": primary_aggregate,
        },
        "secondary": {
            "per_criterion": [
                {"criterion": cid, "score": s, "rationale": "test"}
                for cid, s in secondary_per_criterion.items()
            ],
            "aggregate_score": secondary_aggregate,
        },
        "aggregate": {
            "aggregate_score": (primary_aggregate + secondary_aggregate) / 2.0,
            "structural_passed": True,
            "grounding_passed": True,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_per_dimension_variance_simple():
    """For two runs, variance per dimension is range (max - min)."""
    runs = [
        {"X-1": 5.0, "X-2": 7.0},
        {"X-1": 4.0, "X-2": 7.0},
    ]
    out = calibrate_mod._per_dimension_variance(runs)
    assert out["X-1"] == pytest.approx(1.0)
    assert out["X-2"] == pytest.approx(0.0)


def test_per_dimension_variance_handles_missing():
    """If any run lacks a score, variance for that dimension is None."""
    runs = [
        {"X-1": 5.0, "X-2": 7.0},
        {"X-1": None, "X-2": 7.0},
    ]
    out = calibrate_mod._per_dimension_variance(runs)
    assert out["X-1"] is None
    assert out["X-2"] == pytest.approx(0.0)


def test_extract_scores_accepts_criterion_or_criterion_id():
    """The judge prompt uses 'criterion'; tolerate 'criterion_id' for safety."""
    response_a = {"per_criterion": [{"criterion": "X-1", "score": 6.5}]}
    response_b = {"per_criterion": [{"criterion_id": "X-2", "score": 4.0}]}
    dims = ("X-1", "X-2", "X-3")
    a = calibrate_mod._extract_scores(response_a, dims)
    b = calibrate_mod._extract_scores(response_b, dims)
    assert a["X-1"] == pytest.approx(6.5)
    assert a["X-2"] is None
    assert b["X-2"] == pytest.approx(4.0)


def test_calibrate_pass_when_all_dims_low_variance(tmp_path):
    """All dimensions ≤ 1.5 max variance → all_pass = True."""
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    stable = {f"X-{i}": 7.0 for i in range(1, 7)}

    def fake_post(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        return _make_response(stable)

    report = calibrate_mod.calibrate(
        domain="x_engine",
        drafts_dir=drafts_dir,
        runs=2,
        judge_url="http://fake",
        token="",
        post_fn=fake_post,
    )
    assert report["all_pass"] is True
    assert report["failed_dims"] == []
    assert report["draft_count"] == 2


def test_calibrate_fails_when_any_dim_above_threshold(tmp_path):
    """Variance ≥ 2.0 on any dim → exit code 1 path (all_pass = False, failed_dims populated)."""
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    high = {"X-1": 8.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    low = {"X-1": 5.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    state = {"call": 0}

    def fake_post(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        # alternate so each draft sees one high then one low → variance 3.0 on X-1
        idx = state["call"] % 2
        state["call"] += 1
        return _make_response(high if idx == 0 else low)

    report = calibrate_mod.calibrate(
        domain="x_engine",
        drafts_dir=drafts_dir,
        runs=2,
        judge_url="http://fake",
        token="",
        post_fn=fake_post,
    )
    assert report["all_pass"] is False
    assert "X-1" in report["failed_dims"]
    assert report["dim_variance"]["X-1"]["max"] == pytest.approx(3.0)


def test_cross_item_dim_excluded_from_verdict(tmp_path):
    """X-6 / LI-6 are cross-item; they should NOT trip FAIL even with high
    per-draft swing. Their semantic axis is cohort spread, not per-draft."""
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    high = {"X-1": 7.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 9.0}
    low = {"X-1": 7.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 2.0}
    state = {"call": 0}

    def fake_post(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        idx = state["call"] % 2
        state["call"] += 1
        # X-6 swings 9->2 = variance 7 per draft. Pre-fix this would FAIL.
        # Post-fix, X-6 is excluded from per-draft variance scoring.
        return _make_response(high if idx == 0 else low)

    report = calibrate_mod.calibrate(
        domain="x_engine",
        drafts_dir=drafts_dir,
        runs=2,
        judge_url="http://fake",
        token="",
        post_fn=fake_post,
    )
    assert "X-6" not in report["failed_dims"]
    assert report["dim_variance"]["X-6"].get("excluded") is not None
    assert report["all_pass"] is True
    # cohort summary captures the cross-item axis separately
    assert report["cohort_variance"]["dimension"] == "X-6"


def test_calibrate_warn_for_borderline_variance(tmp_path):
    """Variance between 1.5 and 2.0 → not pass, not failed (warn)."""
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    high = {"X-1": 7.7, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    low = {"X-1": 6.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    state = {"call": 0}

    def fake_post(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        idx = state["call"] % 2
        state["call"] += 1
        return _make_response(high if idx == 0 else low)

    report = calibrate_mod.calibrate(
        domain="x_engine",
        drafts_dir=drafts_dir,
        runs=2,
        judge_url="http://fake",
        token="",
        post_fn=fake_post,
    )
    assert report["failed_dims"] == []
    assert "X-1" in report["warn_dims"]
    assert report["all_pass"] is False


def test_render_markdown_contains_three_tables(tmp_path):
    """The markdown report has all 3 required sections."""
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    stable = {f"X-{i}": 7.0 for i in range(1, 7)}

    def fake_post(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        return _make_response(stable, primary_aggregate=7.0, secondary_aggregate=6.5)

    report = calibrate_mod.calibrate(
        domain="x_engine",
        drafts_dir=drafts_dir,
        runs=2,
        judge_url="http://fake",
        token="",
        post_fn=fake_post,
    )
    md = calibrate_mod.render_markdown(report)
    assert "## Per-dimension variance (primary judge)" in md
    assert "## Cohort-fit spread (X-6)" in md
    assert "## Judge-family agreement" in md
    # Verdict line
    assert "**Verdict: PASS**" in md
    # Judge agreement absolute diff (7.0 vs 6.5 = 0.5)
    assert "0.50" in md


def test_calibrate_rejects_runs_below_two(tmp_path):
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    with pytest.raises(calibrate_mod.CalibrationError):
        calibrate_mod.calibrate(
            domain="x_engine",
            drafts_dir=drafts_dir,
            runs=1,
            judge_url="http://fake",
            token="",
            post_fn=lambda _u, _b: _make_response({"X-1": 7.0}),
        )


def test_calibrate_rejects_unknown_domain(tmp_path):
    drafts_dir = _write_x_drafts(tmp_path, count=1)
    with pytest.raises(calibrate_mod.CalibrationError):
        calibrate_mod.calibrate(
            domain="unknown",
            drafts_dir=drafts_dir,
            runs=2,
            judge_url="http://fake",
            token="",
            post_fn=lambda _u, _b: {},
        )


def test_calibrate_errors_on_empty_drafts_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(calibrate_mod.CalibrationError):
        calibrate_mod.calibrate(
            domain="x_engine",
            drafts_dir=empty,
            runs=2,
            judge_url="http://fake",
            token="",
            post_fn=lambda _u, _b: {},
        )


def test_main_exits_zero_on_pass(tmp_path, capsys, monkeypatch):
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    stable = {f"X-{i}": 7.0 for i in range(1, 7)}

    def fake_post(_url: str, _body: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return _make_response(stable)

    monkeypatch.setattr(calibrate_mod, "_default_post", fake_post)
    monkeypatch.delenv("EVOLUTION_JUDGE_URL", raising=False)
    monkeypatch.delenv("EVOLUTION_INVOKE_TOKEN", raising=False)

    rc = calibrate_mod.main(
        ["--domain", "x_engine", "--drafts-dir", str(drafts_dir), "--runs", "2"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Verdict: PASS" in out


def test_main_exits_one_on_fail(tmp_path, capsys, monkeypatch):
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    high = {"X-1": 9.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    low = {"X-1": 4.0, "X-2": 7.0, "X-3": 7.0, "X-4": 7.0, "X-5": 7.0, "X-6": 7.0}
    state = {"call": 0}

    def fake_post(_url: str, _body: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        idx = state["call"] % 2
        state["call"] += 1
        return _make_response(high if idx == 0 else low)

    monkeypatch.setattr(calibrate_mod, "_default_post", fake_post)
    monkeypatch.delenv("EVOLUTION_JUDGE_URL", raising=False)
    monkeypatch.delenv("EVOLUTION_INVOKE_TOKEN", raising=False)

    rc = calibrate_mod.main(
        ["--domain", "x_engine", "--drafts-dir", str(drafts_dir), "--runs", "2"]
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "Verdict: FAIL" in out


def test_main_writes_output_file(tmp_path, monkeypatch):
    drafts_dir = _write_x_drafts(tmp_path, count=2)
    stable = {f"X-{i}": 7.0 for i in range(1, 7)}

    def fake_post(_url: str, _body: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return _make_response(stable)

    monkeypatch.setattr(calibrate_mod, "_default_post", fake_post)
    monkeypatch.delenv("EVOLUTION_JUDGE_URL", raising=False)
    monkeypatch.delenv("EVOLUTION_INVOKE_TOKEN", raising=False)

    out_path = tmp_path / "report.md"
    rc = calibrate_mod.main(
        [
            "--domain", "x_engine",
            "--drafts-dir", str(drafts_dir),
            "--runs", "2",
            "--output", str(out_path),
        ]
    )
    assert rc == 0
    assert out_path.exists()
    body = out_path.read_text(encoding="utf-8")
    assert "## Per-dimension variance" in body


def test_committed_fixtures_load(tmp_path, monkeypatch):
    """The 6 committed sample fixtures are real .md files the script can read."""
    stable = {f"X-{i}": 7.0 for i in range(1, 7)}
    li_stable = {f"LI-{i}": 7.0 for i in range(1, 7)}

    def fake_x(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        return _make_response(stable)

    def fake_li(_url: str, _body: dict[str, Any]) -> dict[str, Any]:
        return _make_response(li_stable)

    x_dir = REPO_ROOT / "tests" / "fixtures" / "calibration" / "x_engine"
    li_dir = REPO_ROOT / "tests" / "fixtures" / "calibration" / "linkedin_engine"

    x_report = calibrate_mod.calibrate(
        "x_engine", x_dir, runs=2, judge_url="x", token="", post_fn=fake_x
    )
    assert x_report["draft_count"] == 3

    li_report = calibrate_mod.calibrate(
        "linkedin_engine", li_dir, runs=2, judge_url="x", token="", post_fn=fake_li
    )
    assert li_report["draft_count"] == 3
