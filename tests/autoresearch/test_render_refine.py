"""Tests for the self-refinement loop on multi-section synthesis.

Covers:
- _section_quality_signals heuristics fire on each section_id's specific
  brief promises (numbers, pull-quote shape, action-row count, SVG
  presence).
- _spawn_refine_section spawns a second CLI call when issues fire,
  caches the refined output, and falls back to the original when refine
  doesn't actually improve quality signals.
- AUTORESEARCH_RENDER_REFINE=0 disables the loop.
- KEEP response from agent skips the refine result.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER_REPORT_PATH = (
    REPO_ROOT
    / "autoresearch"
    / "archive"
    / "v006"
    / "scripts"
    / "render_report.py"
)


@pytest.fixture(scope="module")
def render_report_module():
    spec = importlib.util.spec_from_file_location(
        "render_report_refine_test", RENDER_REPORT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_refine_test"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── _section_quality_signals heuristics ─────────────────────────────────────


def test_signals_executive_summary_no_digits(render_report_module):
    issues = render_report_module._section_quality_signals(
        "executive_summary",
        "<p>" + ("words " * 60) + "</p>",  # > 200 chars but no digits
    )
    assert any("digit" in i.lower() or "number" in i.lower() for i in issues)


def test_signals_executive_summary_with_digits_passes(render_report_module):
    body = "<p>" + ("Specific 42 finding " * 20) + "</p>"
    issues = render_report_module._section_quality_signals("executive_summary", body)
    # Has digits + length > 200 — should be clean
    assert issues == []


def test_signals_top_finding_missing_pullquote(render_report_module):
    body = (
        "<div class='rprt-spotlight'><p>"
        + ("Specific 42 finding " * 20)  # >200 chars + has digit
        + "</p></div>"
    )
    issues = render_report_module._section_quality_signals(
        "top_finding_spotlight", body
    )
    assert any("rprt-pull-quote" in i for i in issues)


def test_signals_top_finding_complete(render_report_module):
    body = (
        "<div class='rprt-spotlight'>"
        "<strong>Headline 1 with 42 number</strong>"
        "<div class='rprt-pull-quote'>"
        "<div class='qtext'>" + ("quoted text " * 20) + "</div>"
        "<div class='qattr'>source</div></div>"
        "<p>Interpretation paragraph with 7 specific numbers.</p>"
        "</div>"
    )
    issues = render_report_module._section_quality_signals(
        "top_finding_spotlight", body
    )
    assert issues == []


def test_signals_chart_missing_svg(render_report_module):
    body = "<div class='rprt-chart'>"+ ("words " * 50) + "</div>"
    issues = render_report_module._section_quality_signals("chart_view", body)
    assert any("svg" in i.lower() for i in issues)


def test_signals_recommendations_too_few(render_report_module):
    body = (
        "<div class='rprt-action-list'>"
        "<div class='rprt-action-row'><div class='priority'>1</div>"
        "<div>Specific action 5</div></div>"
        + (" filler text " * 30)
        + "</div>"
    )
    issues = render_report_module._section_quality_signals(
        "recommendations", body
    )
    assert any("3-5" in i for i in issues)


def test_signals_what_changed_missing_evidence_row(render_report_module):
    body = "<p>" + ("words 42 " * 30) + "</p>"
    issues = render_report_module._section_quality_signals("what_changed", body)
    assert any("evidence-row" in i for i in issues)


def test_signals_too_short(render_report_module):
    issues = render_report_module._section_quality_signals(
        "executive_summary", "<p>tiny 1</p>"
    )
    assert any("brief" in i.lower() for i in issues)


# ─── _spawn_refine_section ───────────────────────────────────────────────────


def _fake_run(stdout_text: str, returncode: int = 0):
    def _runner(cmd, **kwargs):
        return type("R", (), {
            "returncode": returncode,
            "stdout": stdout_text.encode("utf-8"),
            "stderr": b"",
        })()
    return _runner


def test_refine_returns_improved_html(render_report_module, tmp_path):
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    issues = ["Output is too brief (50 chars rendered).",
              "Brief required SPECIFIC numbers; output had no digits."]
    original = "<p>too brief no nums</p>"

    refined_html = (
        "<p>Now substantially longer with 42 specific numbers like 99% "
        "and proper nouns like Anthropic, generating 1.4x rendered length.</p>"
    )
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run(refined_html),
    ):
        result = render_report_module._spawn_refine_section(
            backend="codex",
            section_id="executive_summary",
            section_brief="brief",
            domain="geo",
            client="ahrefs",
            payload="data",
            original_html=original,
            issues=issues,
            sig="abc123",
            cache_dir=cache_dir,
        )
    assert result is not None
    assert "42" in result
    assert "Anthropic" in result
    # Refine output cached
    assert (cache_dir / "sec-executive_summary-abc123-r1.html").is_file()


def test_refine_returns_none_when_keep(render_report_module, tmp_path):
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run("KEEP"),
    ):
        result = render_report_module._spawn_refine_section(
            backend="codex",
            section_id="executive_summary",
            section_brief="brief",
            domain="geo",
            client="ahrefs",
            payload="data",
            original_html="<p>orig</p>",
            issues=["something"],
            sig="abc123",
            cache_dir=cache_dir,
        )
    assert result is None
    assert (cache_dir / "sec-executive_summary-abc123-r1.html").read_text() == "KEEP"


def test_refine_falls_back_when_quality_does_not_improve(
    render_report_module, tmp_path
):
    """If the refine output has the SAME or MORE quality issues than the
    original, the function returns None so the orchestrator keeps the
    original."""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    issues = ["Output is too brief (50 chars rendered).",
              "Brief required SPECIFIC numbers; output had no digits."]
    # Refined output STILL too brief and STILL no digits → 2 issues remain
    bad_refined = "<p>still too brief and still no digits</p>"
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run(bad_refined),
    ):
        result = render_report_module._spawn_refine_section(
            backend="codex",
            section_id="executive_summary",
            section_brief="brief",
            domain="geo",
            client="ahrefs",
            payload="data",
            original_html="<p>orig</p>",
            issues=issues,
            sig="abc123",
            cache_dir=cache_dir,
        )
    assert result is None


def test_refine_uses_cache_on_second_call(render_report_module, tmp_path):
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    refined_html = (
        "<p>Refined with 42 numbers and proper nouns Anthropic and "
        "OpenAI — clearly longer than the 200 char minimum threshold "
        "the heuristic gate enforces. Adding a second sentence with "
        "another number (99) and another proper noun (Stripe) ensures "
        "the signals come back clean for executive_summary.</p>"
    )
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run(refined_html),
    ) as m1:
        result1 = render_report_module._spawn_refine_section(
            backend="codex",
            section_id="executive_summary",
            section_brief="brief",
            domain="geo",
            client="ahrefs",
            payload="data",
            original_html="<p>orig</p>",
            issues=["x"],
            sig="abc123",
            cache_dir=cache_dir,
        )
    assert result1 is not None
    assert m1.call_count == 1

    # Second call should hit cache, not spawn subprocess
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run("should_not_be_called"),
    ) as m2:
        result2 = render_report_module._spawn_refine_section(
            backend="codex",
            section_id="executive_summary",
            section_brief="brief",
            domain="geo",
            client="ahrefs",
            payload="data",
            original_html="<p>orig</p>",
            issues=["x"],
            sig="abc123",
            cache_dir=cache_dir,
        )
    assert result2 is not None
    assert "Refined" in result2  # Same refined content
    assert m2.call_count == 0


# ─── orchestrator integration ────────────────────────────────────────────────


def test_orchestrator_skips_refine_when_disabled(
    render_report_module, tmp_path, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.setenv("AUTORESEARCH_RENDER_REFINE", "0")

    sd = tmp_path / "sd"
    sd.mkdir()
    (sd / "results.jsonl").write_text("")

    extract = {
        "iterations": [], "iteration_count": 0,
        "totals": {"reasoning_beats": 0, "tool_calls": 0, "tokens": 0},
        "pivots": [],
    }

    # Initial output is intentionally low-quality (too short, no digits)
    bad_output = "<p>bad</p>"
    refined_output = (
        "<p>This refine call should NOT happen because the env-gate "
        "is off; if you see this string, the test is wrong with 42.</p>"
    )

    def _runner(cmd, **kwargs):
        # Always return the bad output — we should NOT see the refine call.
        return type("R", (), {
            "returncode": 0,
            "stdout": bad_output.encode("utf-8"),
            "stderr": b"",
        })()

    with patch.object(
        render_report_module.subprocess, "run", side_effect=_runner,
    ) as m:
        # The bad output is < 60 chars after sanitize → orchestrator
        # skips it, so it won't end up in `out`. We don't actually
        # need to inspect `out` here; we verify that the refine
        # subprocess was NOT spawned (call_count would be N synth
        # calls + 0 refine calls = N).
        out = render_report_module.agent_compose_multi_section(
            "geo", "ahrefs", sd, extract, None,
        )
    # Number of subprocess.run calls equals number of section briefs
    # (5) — no refine calls because env-gate disabled.
    assert m.call_count == len(render_report_module._MULTI_SECTION_BRIEFS)
