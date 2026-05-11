"""Tests for the dynamic-renderer path — agent reads renderer-prompt files +
session payload and writes the highlights HTML directly.

Path A (per-section briefs, fixed list) and Path B (per-lane renderer-prompt
files, agent-decided components) coexist via a fallback chain in render():
  dynamic → multi-section → legacy single-section → static composer.

Tests cover:
- _load_renderer_prompt loads _base.md + <lane>.md from
  programs/render/ — both files required, returns None on missing.
- agent_compose_dynamic_highlights: gracefully returns None when env-gated
  off, when backend is none, when prompt files missing, when agent
  returns SKIP.
- Successful path returns sanitized HTML.
- Cache hits skip the subprocess.
- SKIP responses are cached and re-fetched as None.
"""
from __future__ import annotations

import importlib.util
import json
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
        "render_report_dynamic_test", RENDER_REPORT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_dynamic_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def populated_session(tmp_path):
    sd = tmp_path / "v006" / "sessions" / "geo" / "ahrefs"
    sd.mkdir(parents=True)
    (sd / "session_summary.json").write_text(json.dumps({
        "iterations": {"total": 7}, "findings_count": 4, "status": "COMPLETE",
    }))
    (sd / "results.jsonl").write_text("")
    (sd / "findings.md").write_text("## Observations\n\n- [TAG] An observation\n")
    return sd


@pytest.fixture
def fake_extract():
    return {
        "iterations": [{
            "iteration": 1, "phase": "discover", "status": "kept",
            "reasoning_beats": [{"iteration": 1, "kind": "first_move",
                                  "text": "I'll read state.", "line_no": 1}],
            "tool_calls": ["ls"],
            "tool_call_records": [],
            "tool_count": 1, "token_count": 1.0,
        }],
        "iteration_count": 1,
        "totals": {"reasoning_beats": 1, "tool_calls": 1, "tokens": 1.0},
        "pivots": [],
    }


def _fake_run_factory(reply: str, returncode: int = 0):
    def _runner(cmd, **kwargs):
        return type("R", (), {
            "returncode": returncode,
            "stdout": reply.encode("utf-8"),
            "stderr": b"",
        })()
    return _runner


# ─── _load_renderer_prompt ──────────────────────────────────────────────────


def test_load_renderer_prompt_finds_real_files(
    render_report_module, populated_session
):
    """The shipped programs/render/_base.md + geo.md should resolve."""
    out = render_report_module._load_renderer_prompt("geo", populated_session)
    assert out is not None
    # Base file content
    assert "Renderer agent" in out
    # Lane file content
    assert "GEO lane" in out


def test_load_renderer_prompt_returns_none_on_missing_lane(
    render_report_module, populated_session
):
    out = render_report_module._load_renderer_prompt(
        "nonexistent_lane", populated_session
    )
    assert out is None


def test_load_renderer_prompt_finds_all_seven_lanes(
    render_report_module, populated_session
):
    """Every shipped lane has its own renderer prompt."""
    for lane in ("geo", "competitive", "monitoring", "storyboard",
                 "marketing_audit", "x_engine", "linkedin_engine"):
        out = render_report_module._load_renderer_prompt(lane, populated_session)
        assert out is not None, f"missing renderer prompt for lane: {lane}"
        # Each lane prompt file references its own lane name in the heading.
        assert lane.upper().replace("_", " ") in out.upper() or lane in out


# ─── agent_compose_dynamic_highlights ────────────────────────────────────────


def test_dynamic_disabled_via_env(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    monkeypatch.setenv("AUTORESEARCH_RENDER_DYNAMIC", "0")
    monkeypatch.setenv("RENDER_BACKEND", "codex")

    out = render_report_module.agent_compose_dynamic_highlights(
        "geo", "ahrefs", populated_session, fake_extract, None,
    )
    assert out is None


def test_dynamic_disabled_when_backend_none(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "none")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)
    out = render_report_module.agent_compose_dynamic_highlights(
        "geo", "ahrefs", populated_session, fake_extract, None,
    )
    assert out is None


def test_dynamic_returns_none_on_skip(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)

    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run_factory("SKIP"),
    ):
        out = render_report_module.agent_compose_dynamic_highlights(
            "geo", "ahrefs", populated_session, fake_extract, None,
        )
    assert out is None
    # SKIP is cached so a second call also returns None — without spawning
    cache_dir = populated_session / ".render_synthesis_cache"
    skip_files = list(cache_dir.glob("dyn-*.html"))
    assert len(skip_files) == 1
    assert skip_files[0].read_text() == "SKIP"


def test_dynamic_returns_sanitized_html_on_success(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)

    reply = (
        '<div class="rprt-meta-pattern">'
        '<div class="label">↳ exec</div>'
        '<p>Specific 42 finding from session with proper-noun Anthropic '
        'and citation count 7 across 3 engines.</p>'
        '</div>'
        '<div class="rprt-chart">'
        '[[chart:bar:chatgpt=12,perplexity=4,gemini=8|title=Citations]]'
        '<p>ChatGPT leads at 12 per-engine citations.</p>'
        '</div>'
    )
    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run_factory(reply),
    ):
        out = render_report_module.agent_compose_dynamic_highlights(
            "geo", "ahrefs", populated_session, fake_extract,
            "## Findings\n\n- [TAG] thing\n",
        )

    assert out is not None
    assert "rprt-meta-pattern" in out
    assert "Anthropic" in out
    # Chart directive substituted into SVG
    assert "<svg" in out
    assert "Citations" in out  # title rendered
    # Cache populated
    cache_dir = populated_session / ".render_synthesis_cache"
    assert any(f.suffix == ".html" for f in cache_dir.glob("dyn-*.html"))


def test_dynamic_cache_short_circuits_subprocess(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)

    reply = (
        '<div class="rprt-meta-pattern">'
        '<p>cache_sentinel_xyz with enough body to clear the 200-char '
        'sanitize floor and contain digits 42 and proper-noun Anthropic '
        'so heuristics pass cleanly on first inspection.</p>'
        '</div>'
    )
    fake = _fake_run_factory(reply)

    # First pass spawns
    with patch.object(render_report_module.subprocess, "run", side_effect=fake) as m1:
        out1 = render_report_module.agent_compose_dynamic_highlights(
            "geo", "ahrefs", populated_session, fake_extract, None,
        )
    assert out1 is not None
    assert m1.call_count == 1

    # Second pass: cache hit — no subprocess
    with patch.object(render_report_module.subprocess, "run", side_effect=fake) as m2:
        out2 = render_report_module.agent_compose_dynamic_highlights(
            "geo", "ahrefs", populated_session, fake_extract, None,
        )
    assert out2 is not None
    assert "cache_sentinel_xyz" in out2
    assert m2.call_count == 0


def test_dynamic_returns_none_when_prompt_files_missing(
    render_report_module, fake_extract, tmp_path, monkeypatch
):
    """When programs/render/ doesn't exist (e.g. variant cloned without
    the prompts), the helper returns None so the orchestrator falls back."""
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)

    # session_dir at a path with NO programs/render/ ancestor — the
    # _renderer_prompt_root fallback to v006/programs/render WILL find
    # the real shipped files. To simulate "missing", pass a domain that
    # has no shipped lane file.
    sd = tmp_path / "v006" / "sessions" / "no_such_lane" / "x"
    sd.mkdir(parents=True)
    out = render_report_module.agent_compose_dynamic_highlights(
        "no_such_lane", "x", sd, fake_extract, None,
    )
    assert out is None


def test_dynamic_too_short_falls_back(
    render_report_module, populated_session, fake_extract, monkeypatch
):
    """Sanitize-floor for dynamic is 200 chars. Anything shorter triggers
    fallback (returns None)."""
    monkeypatch.setenv("RENDER_BACKEND", "codex")
    monkeypatch.delenv("AUTORESEARCH_RENDER_DYNAMIC", raising=False)

    with patch.object(
        render_report_module.subprocess, "run",
        side_effect=_fake_run_factory("<p>too brief</p>"),
    ):
        out = render_report_module.agent_compose_dynamic_highlights(
            "geo", "ahrefs", populated_session, fake_extract, None,
        )
    assert out is None
