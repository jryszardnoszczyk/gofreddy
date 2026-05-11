"""Tests for the inline-SVG chart helpers + the sanitizer-allowed SVG round-trip.

The chart helpers must produce SVG that:
  1. Is well-formed (valid XML structure).
  2. Survives the agent-HTML sanitizer unchanged in shape (i.e. an
     agent that emits the same SVG primitives passes through).
  3. Renders something visible (non-trivial content for non-empty data).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHARTS_PATH = REPO_ROOT / "autoresearch" / "archive" / "v006" / "scripts" / "charts_svg.py"
RENDER_REPORT_PATH = REPO_ROOT / "autoresearch" / "archive" / "v006" / "scripts" / "render_report.py"


@pytest.fixture(scope="module")
def charts():
    spec = importlib.util.spec_from_file_location("charts_svg_test", CHARTS_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["charts_svg_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def render_report_module():
    spec = importlib.util.spec_from_file_location(
        "render_report_for_charts", RENDER_REPORT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_report_for_charts"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_bar_chart_renders_svg(charts):
    out = charts.bar_chart([("anthropic", 9.2), ("openai", 7.8), ("google", 6.4)])
    assert out.startswith("<svg")
    assert out.endswith("</svg>")
    assert "anthropic" in out
    assert "9" in out


def test_bar_chart_handles_empty(charts):
    out = charts.bar_chart([])
    assert out.startswith("<svg") and out.endswith("</svg>")
    assert "no data" in out


def test_bar_chart_truncates_with_overflow_marker(charts):
    data = [(f"k{i}", float(i)) for i in range(20)]
    out = charts.bar_chart(data, max_bars=5)
    assert "+15 more" in out


def test_sparkline_renders(charts):
    out = charts.sparkline([1, 2, 4, 3, 8, 5, 9])
    assert out.startswith("<svg")
    assert "polyline" in out


def test_donut_renders_with_legend(charts):
    out = charts.donut([("kept", 12), ("rework", 5), ("dropped", 2)])
    assert "kept" in out
    assert "rework" in out
    assert "dropped" in out
    # Centre total
    assert ">19<" in out  # 12+5+2 = 19
    # Legend emits a tspan with %
    assert "%" in out


def test_donut_zero_skipped(charts):
    out = charts.donut([("a", 0), ("b", 0)])
    assert "no data" in out


def test_timeline_dots_renders(charts):
    out = charts.timeline_dots([("start", 0.0), ("mid", 0.5), ("end", 1.0)])
    assert "<line" in out
    assert "circle" in out
    assert "start" in out and "end" in out


def test_chart_svg_survives_sanitizer(charts, render_report_module):
    """The sanitizer must NOT strip a chart helper's output. If it does, the
    multi-section synthesis would silently lose every chart."""
    chart_html = charts.bar_chart([("a", 5.0), ("b", 7.0)], title="demo")
    cleaned = render_report_module._sanitize_agent_html(chart_html)
    assert "<svg" in cleaned
    assert "<rect" in cleaned
    assert "<text" in cleaned
    # Title and a value label survive
    assert "demo" in cleaned
    # No event handlers / scripts smuggled
    assert "onload" not in cleaned.lower()
    assert "<script" not in cleaned.lower()


def test_sanitizer_keeps_svg_wrapper_drops_inner_xss(render_report_module):
    """Sanity check: a hostile <svg> wrapping a script is reduced to an empty
    <svg></svg> rather than letting the script through."""
    raw = '<svg><script>alert(1)</script><rect width="10" height="10"/></svg>'
    cleaned = render_report_module._sanitize_agent_html(raw)
    assert "<script" not in cleaned.lower()
    assert "alert" not in cleaned.lower()
    # The inner <rect> survives because it's safe + on the allowlist
    assert "<rect" in cleaned


def test_sanitizer_drops_svg_event_handlers(render_report_module):
    raw = '<svg onload="alert(1)"><rect onclick="alert(1)" width="10" height="10"/></svg>'
    cleaned = render_report_module._sanitize_agent_html(raw)
    assert "onload" not in cleaned.lower()
    assert "onclick" not in cleaned.lower()
    assert "<rect" in cleaned  # rect survived; only its bad attr was stripped


def test_sanitizer_drops_javascript_url_in_svg_attr(render_report_module):
    raw = '<svg><rect fill="url(javascript:alert(1))" width="10" height="10"/></svg>'
    cleaned = render_report_module._sanitize_agent_html(raw)
    assert "javascript:" not in cleaned.lower()
    assert "alert" not in cleaned.lower()
