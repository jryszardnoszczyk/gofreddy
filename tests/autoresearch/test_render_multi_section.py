"""Tests for the multi-section dynamic synthesis orchestrator + chart-
directive substitution.

The orchestrator spawns N agent CLI calls (one per _MULTI_SECTION_BRIEFS
entry); we mock subprocess.run to avoid spawning real `codex` / `claude` /
`opencode` while still verifying:

- Each section is requested with its specific brief.
- Cache hits short-circuit subsequent runs.
- SKIP responses are recorded but not rendered.
- Chart directives are substituted with valid SVG before sanitization.
- AUTORESEARCH_RENDER_MULTI_SECTION=0 returns empty (legacy path).
- RENDER_BACKEND=none returns empty.
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
        "render_report_multi_section_test", RENDER_REPORT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_multi_section_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def session_dir(tmp_path):
    sd = tmp_path / "sd"
    sd.mkdir()
    (sd / "results.jsonl").write_text("")
    return sd


@pytest.fixture
def fake_extract():
    return {
        "iterations": [{
            "iteration": 1, "phase": "discover", "status": "kept",
            "reasoning_beats": [{"iteration": 1, "kind": "first_move",
                                  "text": "ok", "line_no": 1}],
            "tool_calls": ["ls"],
            "tool_call_records": [{"iteration": 1, "index": 0,
                "kind": "shell", "command": "ls", "output": "",
                "line_no": 1, "succeeded": True, "duration_ms": 1,
                "paths_read": []}],
            "tool_count": 1, "token_count": 1.0,
        }],
        "iteration_count": 1,
        "totals": {"reasoning_beats": 1, "tool_calls": 1, "tokens": 1.0},
        "pivots": [],
    }


# ─── chart directive substitution ────────────────────────────────────────────


def test_chart_directive_bar_renders_svg(render_report_module):
    raw = '<div class="rprt-chart">[[chart:bar:anthropic=9.2,openai=7.8|title=Score]]</div>'
    out = render_report_module._substitute_chart_directives(raw)
    assert "<svg" in out
    assert "anthropic" in out
    assert "Score" in out
    # Original directive text should be gone
    assert "[[chart" not in out


def test_chart_directive_donut_renders(render_report_module):
    raw = "[[chart:donut:kept=12,rework=5,dropped=2|title=Decisions]]"
    out = render_report_module._substitute_chart_directives(raw)
    assert "<svg" in out
    assert "Decisions" in out
    assert "kept" in out


def test_chart_directive_sparkline_handles_no_labels(render_report_module):
    # Sparkline doesn't use labels; just numeric values
    raw = "[[chart:sparkline:a=1,b=2,c=4,d=3,e=8]]"
    out = render_report_module._substitute_chart_directives(raw)
    assert "<svg" in out
    assert "polyline" in out


def test_chart_directive_malformed_drops_silently(render_report_module):
    raw = "<p>before</p>[[chart:bar:no-equals]]<p>after</p>"
    out = render_report_module._substitute_chart_directives(raw)
    # Empty SVG produced (no usable pairs); directive removed
    assert "[[chart" not in out
    assert "<p>before</p>" in out
    assert "<p>after</p>" in out


def test_chart_directive_unknown_kind_removed(render_report_module):
    raw = "[[chart:scatter:a=1]]"
    # The regex only matches known kinds, so unknown directives stay as text
    # — that's the safer failure mode (visible to operator, no surprise).
    out = render_report_module._substitute_chart_directives(raw)
    assert "[[chart:scatter:a=1]]" in out


# ─── orchestrator wiring ─────────────────────────────────────────────────────


def _fake_run_factory(per_section_html: dict[str, str]):
    """Returns a subprocess.run replacement that maps section_id (parsed
    from prompt) to the agent's reply."""
    def _fake_run(cmd, **kwargs):
        prompt = kwargs.get("input") or ""
        if isinstance(prompt, bytes):
            prompt = prompt.decode("utf-8", errors="replace")
        # Section id is on the "Lane: ... · Section: <id>" line
        sec_id = "unknown"
        for line in prompt.splitlines():
            if "Section:" in line:
                sec_id = line.rsplit("Section:", 1)[-1].strip()
                break
        reply = per_section_html.get(sec_id, "SKIP")
        result = type("R", (), {
            "returncode": 0,
            "stdout": reply.encode("utf-8"),
            "stderr": b"",
        })()
        return result
    return _fake_run


def test_multi_section_renders_each_brief(
    render_report_module, session_dir, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_MULTI_SECTION", raising=False)

    per_section = {
        "executive_summary": (
            '<p><strong>Verdict:</strong> kept across the board.</p>'
            '<p>Two specific deltas grounded the conclusion: '
            'page coverage rose 32% iteration over iteration, and '
            'measured citation count climbed from 4 to 19 in three engines.</p>'
        ),
        "top_finding_spotlight": '<div class="rprt-spotlight"><strong>Top finding</strong>'
            '<div class="rprt-pull-quote"><div class="qtext">x</div>'
            '<div class="qattr">y</div></div></div>',
        "chart_view": '<div class="rprt-chart">[[chart:bar:a=10,b=20|title=Demo]]</div>'
            '<p>chart shows distribution.</p>',
        "what_changed": "SKIP",
        "recommendations": '<div class="rprt-action-list">'
            '<div class="rprt-action-row"><div class="priority">1</div>'
            '<div>Do thing.</div></div></div>',
    }

    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run_factory(per_section)
    ):
        out = render_report_module.agent_compose_multi_section(
            "geo", "ahrefs", session_dir, fake_extract, "## Findings\n",
        )

    section_ids = [sid for sid, _ in out]
    assert "executive_summary" in section_ids
    assert "top_finding_spotlight" in section_ids
    assert "chart_view" in section_ids
    assert "recommendations" in section_ids
    # SKIP'd section is not in output
    assert "what_changed" not in section_ids

    # Chart directive was substituted with SVG
    chart_html = dict(out)["chart_view"]
    assert "<svg" in chart_html
    assert "Demo" in chart_html


def test_multi_section_caches_per_section(
    render_report_module, session_dir, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_MULTI_SECTION", raising=False)

    per_section = {
        "executive_summary": (
            '<p>cached_sentinel_string_xyz with enough body content '
            'to clear the 60-char minimum threshold the sanitizer-floor '
            'rejects below.</p>'
        ),
        "top_finding_spotlight": "SKIP",
        "chart_view": "SKIP",
        "what_changed": "SKIP",
        "recommendations": "SKIP",
    }
    fake_run = _fake_run_factory(per_section)

    # First pass: spawn happens
    with patch.object(render_report_module.subprocess, "run", side_effect=fake_run) as m1:
        out1 = render_report_module.agent_compose_multi_section(
            "geo", "ahrefs", session_dir, fake_extract, "## Findings\n",
        )
    first_call_count = m1.call_count
    assert first_call_count == 5  # all 5 briefs spawned
    assert any("cached_sentinel_string_xyz" in html for _, html in out1)

    # Second pass: cache hits short-circuit subprocess.run for the cached
    # section (executive_summary). The 4 SKIP sections also cache "SKIP" so
    # they don't re-run either.
    with patch.object(render_report_module.subprocess, "run", side_effect=fake_run) as m2:
        out2 = render_report_module.agent_compose_multi_section(
            "geo", "ahrefs", session_dir, fake_extract, "## Findings\n",
        )
    assert m2.call_count == 0, "all sections should have been cached"
    assert any("cached_sentinel_string_xyz" in html for _, html in out2)


def test_multi_section_disabled_via_env(
    render_report_module, session_dir, fake_extract, monkeypatch
):
    monkeypatch.setenv("AUTORESEARCH_RENDER_MULTI_SECTION", "0")
    monkeypatch.setenv("RENDER_BACKEND", "codex")

    out = render_report_module.agent_compose_multi_section(
        "geo", "ahrefs", session_dir, fake_extract, None,
    )
    assert out == []


def test_multi_section_disabled_when_backend_none(
    render_report_module, session_dir, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "none")
    monkeypatch.delenv("AUTORESEARCH_RENDER_MULTI_SECTION", raising=False)

    out = render_report_module.agent_compose_multi_section(
        "geo", "ahrefs", session_dir, fake_extract, None,
    )
    assert out == []


def test_multi_section_skip_text_not_rendered(
    render_report_module, session_dir, fake_extract, monkeypatch
):
    """SKIP must NOT leak into the report as literal text."""
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_MULTI_SECTION", raising=False)

    per_section = {sid: "SKIP" for sid, _ in render_report_module._MULTI_SECTION_BRIEFS}

    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run_factory(per_section),
    ):
        out = render_report_module.agent_compose_multi_section(
            "geo", "ahrefs", session_dir, fake_extract, None,
        )
    assert out == []
