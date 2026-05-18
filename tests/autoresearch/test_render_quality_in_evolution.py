"""Tests for render quality wiring into the evolution composite.

Covers:
- _aggregate_render_quality reads render_score.json across fixtures and
  averages aggregates (excluding 0-stub fallbacks).
- Returns None when no scores are available.
- All 7 lanes have render_rubric_ids set on their LaneSpec — without
  this the post-session render_judge.py call is a no-op.
- The default-on / opt-out env-gate semantics (the renderer-evolution
  wiring landed on 2026-05-08).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALUATE_VARIANT_PATH = REPO_ROOT / "autoresearch" / "evaluate_variant.py"
LANE_REGISTRY_PATH = REPO_ROOT / "autoresearch" / "lane_registry.py"


@pytest.fixture(scope="module")
def evaluate_variant():
    spec = importlib.util.spec_from_file_location(
        "evaluate_variant_under_test", EVALUATE_VARIANT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["evaluate_variant_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lane_registry():
    spec = importlib.util.spec_from_file_location(
        "lane_registry_under_test", LANE_REGISTRY_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lane_registry_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── lane registry coverage ──────────────────────────────────────────────────


def test_all_seven_lanes_have_render_rubric_ids(lane_registry):
    """Every lane the renderer can compose for must have at least one
    rubric ID set, otherwise render_judge.py post-render is a no-op and
    that lane never contributes to render_quality."""
    expected = {
        "geo", "competitive", "monitoring", "storyboard",
        "marketing_audit", "x_engine", "linkedin_engine",
    }
    for lane_name in expected:
        spec = lane_registry.LANES.get(lane_name)
        assert spec is not None, f"missing LaneSpec for {lane_name}"
        assert getattr(spec, "render_rubric_ids", None), (
            f"lane {lane_name} has no render_rubric_ids — render_judge "
            f"will skip the post-session screenshot grade"
        )


# ─── _aggregate_render_quality ───────────────────────────────────────────────


def _make_score_file(path: Path, aggregate: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "aggregate": aggregate,
        "per_criterion": [
            {"criterion": "RND-1", "score": aggregate, "rationale": "fixture"},
        ],
    }))


def test_aggregate_render_quality_averages_across_fixtures(
    evaluate_variant, tmp_path
):
    sessions_root = tmp_path / "sessions"
    _make_score_file(sessions_root / "geo" / "ahrefs" / "render_score.json", 4.0)
    _make_score_file(sessions_root / "geo" / "semrush" / "render_score.json", 3.0)
    _make_score_file(sessions_root / "competitive" / "figma" / "render_score.json", 5.0)

    scored_fixtures = {
        "geo": [{"fixture_id": "ahrefs"}, {"fixture_id": "semrush"}],
        "competitive": [{"fixture_id": "figma"}],
    }
    result = evaluate_variant._aggregate_render_quality(
        scored_fixtures, tmp_path,
    )
    assert result == round((4.0 + 3.0 + 5.0) / 3, 4)


def test_aggregate_render_quality_excludes_zero_stubs(
    evaluate_variant, tmp_path
):
    """Stub scores (aggregate=0.0 from missing GEMINI_API_KEY) must NOT
    dilute the average — they're filtered before averaging."""
    sessions_root = tmp_path / "sessions"
    _make_score_file(sessions_root / "geo" / "real" / "render_score.json", 4.0)
    _make_score_file(sessions_root / "geo" / "stub" / "render_score.json", 0.0)

    scored_fixtures = {
        "geo": [{"fixture_id": "real"}, {"fixture_id": "stub"}],
    }
    result = evaluate_variant._aggregate_render_quality(
        scored_fixtures, tmp_path,
    )
    # Only the real score contributes
    assert result == 4.0


def test_aggregate_render_quality_returns_none_when_no_scores(
    evaluate_variant, tmp_path
):
    """When no fixture wrote a render_score.json (e.g. lane has no
    render_rubric_ids OR Gemini was unavailable for every render), the
    helper returns None so the caller can decide to skip the dimension
    entirely rather than blend in nothing."""
    scored_fixtures = {"geo": [{"fixture_id": "ahrefs"}]}
    # No file written — no score, no dir
    result = evaluate_variant._aggregate_render_quality(
        scored_fixtures, tmp_path,
    )
    assert result is None


def test_aggregate_render_quality_handles_malformed_json(
    evaluate_variant, tmp_path
):
    sessions_root = tmp_path / "sessions" / "geo" / "ahrefs"
    sessions_root.mkdir(parents=True)
    (sessions_root / "render_score.json").write_text("{not json")

    scored_fixtures = {"geo": [{"fixture_id": "ahrefs"}]}
    # Helper swallows JSONDecodeError; aggregate from the malformed file
    # is silently skipped.
    result = evaluate_variant._aggregate_render_quality(
        scored_fixtures, tmp_path,
    )
    assert result is None


def test_aggregate_render_quality_reads_by_client_when_client_differs_from_fid(
    evaluate_variant, tmp_path
):
    """Reader uses client-keyed path (matches writer); legacy reader used fid."""
    sessions_root = tmp_path / "sessions"
    _make_score_file(sessions_root / "geo" / "nubank" / "render_score.json", 4.0)
    _make_score_file(sessions_root / "x_engine" / "jr" / "render_score.json", 3.5)
    scored_fixtures = {
        "geo": [{"fixture_id": "geo-nubank-br-conta", "client": "nubank"}],
        "x_engine": [{"fixture_id": "x_engine-angle-121", "client": "jr"}],
    }
    result = evaluate_variant._aggregate_render_quality(scored_fixtures, tmp_path)
    assert result == round((4.0 + 3.5) / 2, 4)


def test_aggregate_render_quality_falls_back_to_fid_when_client_path_missing(
    evaluate_variant, tmp_path
):
    """Backwards-compat: legacy fid-keyed archives still load via fallback."""
    _make_score_file(tmp_path / "sessions" / "geo" / "geo-ahrefs" / "render_score.json", 4.0)
    scored_fixtures = {"geo": [{"fixture_id": "geo-ahrefs", "client": "ahrefs"}]}
    result = evaluate_variant._aggregate_render_quality(scored_fixtures, tmp_path)
    assert result == 4.0


def test_aggregate_render_quality_does_not_double_count_when_both_paths_exist(
    evaluate_variant, tmp_path
):
    """One fixture contributes once even when both client + fid paths exist."""
    sessions_root = tmp_path / "sessions"
    _make_score_file(sessions_root / "geo" / "nubank" / "render_score.json", 4.0)
    _make_score_file(sessions_root / "geo" / "geo-nubank-br" / "render_score.json", 2.0)
    scored_fixtures = {"geo": [{"fixture_id": "geo-nubank-br", "client": "nubank"}]}
    result = evaluate_variant._aggregate_render_quality(scored_fixtures, tmp_path)
    assert result == 4.0  # client-keyed wins; legacy ignored


# ─── _ensure_render_score (substrate-side fallback) ──────────────────────────


def _png_stub(path: Path) -> None:
    """Minimal placeholder file so screenshot.exists() == True."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_ensure_render_score_idempotent_when_score_exists(
    evaluate_variant, tmp_path, monkeypatch
):
    """If the variant's own post_session already wrote render_score.json,
    the substrate fallback must be a no-op — no subprocess invocation,
    no overwrite. Lets variants that DO wire it up keep their results."""
    session = tmp_path / "sessions" / "geo" / "ahrefs"
    _png_stub(session / "report-screenshot.png")
    (session / "render_score.json").write_text('{"aggregate": 4.2}')
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    called: list[tuple] = []
    monkeypatch.setattr(
        evaluate_variant.subprocess, "run",
        lambda *a, **kw: called.append((a, kw)),
    )
    evaluate_variant._ensure_render_score(session, "geo")
    assert called == []
    # File preserved.
    assert json.loads((session / "render_score.json").read_text())["aggregate"] == 4.2


def test_ensure_render_score_skips_lane_without_rubric_ids(
    evaluate_variant, tmp_path, monkeypatch
):
    """Lanes that opt out (no render_rubric_ids on LaneSpec — e.g. core)
    must not trigger render_judge even when a screenshot is present."""
    session = tmp_path / "sessions" / "core" / "client"
    _png_stub(session / "report-screenshot.png")
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    called: list[tuple] = []
    monkeypatch.setattr(
        evaluate_variant.subprocess, "run",
        lambda *a, **kw: called.append((a, kw)),
    )
    evaluate_variant._ensure_render_score(session, "core")
    assert called == []
    assert not (session / "render_score.json").exists()


def test_ensure_render_score_skips_when_gemini_key_missing(
    evaluate_variant, tmp_path, monkeypatch, capsys
):
    """No GEMINI_API_KEY → skip invocation AND surface a warning. The
    alternative (let render_judge.py write a stub) silently drops render
    quality from the composite because _aggregate_render_quality filters
    aggregate=0.0 — operators would never see the missing key."""
    session = tmp_path / "sessions" / "geo" / "ahrefs"
    _png_stub(session / "report-screenshot.png")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    called: list[tuple] = []
    monkeypatch.setattr(
        evaluate_variant.subprocess, "run",
        lambda *a, **kw: called.append((a, kw)),
    )
    evaluate_variant._ensure_render_score(session, "geo")
    assert called == []
    assert not (session / "render_score.json").exists()
    captured = capsys.readouterr()
    assert "GEMINI_API_KEY" in captured.err
    assert "geo/ahrefs" in captured.err


def test_ensure_render_score_skips_when_screenshot_missing(
    evaluate_variant, tmp_path, monkeypatch
):
    """If render_report failed (no screenshot), there's nothing to grade.
    The substrate fallback must not invoke render_judge against a missing
    PNG (Gemini would error AND we'd waste an API call)."""
    session = tmp_path / "sessions" / "geo" / "ahrefs"
    session.mkdir(parents=True)
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    called: list[tuple] = []
    monkeypatch.setattr(
        evaluate_variant.subprocess, "run",
        lambda *a, **kw: called.append((a, kw)),
    )
    evaluate_variant._ensure_render_score(session, "geo")
    assert called == []


def test_ensure_render_score_invokes_render_judge_when_gap_present(
    evaluate_variant, tmp_path, monkeypatch
):
    """The happy path: screenshot present + no render_score.json + lane
    opt-in + GEMINI_API_KEY set → invoke render_judge.py via subprocess
    with the canonical v006 script + rubric paths."""
    session = tmp_path / "sessions" / "geo" / "ahrefs"
    _png_stub(session / "report-screenshot.png")
    monkeypatch.setenv("GEMINI_API_KEY", "x")

    invocations: list[list] = []
    monkeypatch.setattr(
        evaluate_variant.subprocess, "run",
        lambda cmd, **kw: invocations.append(cmd),
    )
    evaluate_variant._ensure_render_score(session, "geo")
    assert len(invocations) == 1
    cmd = invocations[0]
    # render_judge.py + screenshot + rubric + output path are all in argv.
    assert any("render_judge.py" in str(c) for c in cmd)
    assert any("report-screenshot.png" in str(c) for c in cmd)
    assert any("render-rubric.md" in str(c) for c in cmd)
    assert any("render_score.json" in str(c) for c in cmd)
