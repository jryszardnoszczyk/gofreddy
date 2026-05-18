"""Playwright site render utility (U7b).

Most tests target the deterministic surface (classification helpers,
sandboxing refusal, RenderResult shape, circuit-breaker accounting).
Tests that actually launch Chromium use `pytest.importorskip` so the
suite runs cleanly in environments where playwright isn't installed.
"""
from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest

from src.generation.site_render import (
    DEFAULT_VIEWPORTS,
    BlockedRequest,
    ConsoleMessage,
    PlaywrightNotInstalledError,
    SiteRenderer,
    UnsafeRenderEnvironmentError,
    _classify_blocked_request,
    _classify_console_source,
)


# ---------------------------------------------------------------------------
# Defaults pin
# ---------------------------------------------------------------------------


def test_default_viewports_are_desktop_and_mobile() -> None:
    """DEFAULT_VIEWPORTS pin — drift catches a silent change."""
    assert DEFAULT_VIEWPORTS == (
        ("desktop", 1440, 900),
        ("mobile", 375, 812),
    )


# ---------------------------------------------------------------------------
# Sandboxing refusal — Pass-3 reliability + Threat Model
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    platform.system() == "Linux",
    reason="Sandboxing refusal is unsandboxed-platform behavior; Linux launches fine.",
)
def test_macos_without_escape_env_refuses_construction(monkeypatch) -> None:
    """Per the plan U7b: on macOS without GOFREDDY_U7B_ALLOW_UNSANDBOXED=1,
    SiteRenderer refuses to construct (no Chromium launch — the
    constructor itself raises)."""
    monkeypatch.delenv("GOFREDDY_U7B_ALLOW_UNSANDBOXED", raising=False)
    with pytest.raises(UnsafeRenderEnvironmentError) as exc:
        SiteRenderer()
    assert platform.system() in str(exc.value)


@pytest.mark.skipif(
    platform.system() == "Linux",
    reason="Escape env is unsandboxed-platform-only; Linux already accepts.",
)
def test_macos_with_escape_env_constructs_with_warning(monkeypatch, caplog) -> None:
    monkeypatch.setenv("GOFREDDY_U7B_ALLOW_UNSANDBOXED", "1")
    SiteRenderer()  # no raise
    assert any("DEV ONLY" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Network classification helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("url, expected", [
    ("http://169.254.169.254/latest/meta-data", "metadata_endpoint"),
    ("http://10.0.0.1/internal", "rfc1918"),
    ("http://192.168.1.5/foo", "rfc1918"),
    ("http://172.16.5.5/foo", "rfc1918"),
    ("http://127.0.0.1:8080/api", "rfc1918"),
    ("http://localhost/api", "rfc1918"),
    ("https://cdn.example.com/font.woff2", "external_domain"),
    ("data:image/png;base64,iVBORw0KGgo", "internal_scheme"),
    ("blob:http://localhost/abc", "internal_scheme"),
])
def test_blocked_request_classification(url: str, expected: str) -> None:
    """Per Threat Model render-pipeline SSRF row: every private-network
    URL surface must classify into a recognisable bucket."""
    assert _classify_blocked_request(url) == expected


def test_console_source_classification_recognises_lane_origins() -> None:
    """Heuristic classification of lane-authored vs external console
    messages. False positives widen to 'external' (safe default)."""
    assert _classify_console_source(
        "http://localhost:8080/script.js: ReferenceError",
        host_origin="http://localhost:8080",
    ) == "lane-js"

    assert _classify_console_source(
        "https://fonts.googleapis.com/css2?family=Inter: net::ERR_BLOCKED",
        host_origin="http://localhost:8080",
    ) == "external"

    assert _classify_console_source(
        "Something obscure happened",
        host_origin="http://localhost:8080",
    ) == "unknown"


# ---------------------------------------------------------------------------
# Construction (Linux happy path or escape-env-set)
# ---------------------------------------------------------------------------


@pytest.fixture
def renderer(monkeypatch) -> SiteRenderer:
    """Construct a renderer with the sandbox escape set so the test
    fixture runs on both Linux and macOS."""
    monkeypatch.setenv("GOFREDDY_U7B_ALLOW_UNSANDBOXED", "1")
    return SiteRenderer()


def test_renderer_constructs_with_default_viewports(renderer: SiteRenderer) -> None:
    assert renderer.viewports == list(DEFAULT_VIEWPORTS)


def test_renderer_constructs_with_custom_viewports(monkeypatch) -> None:
    monkeypatch.setenv("GOFREDDY_U7B_ALLOW_UNSANDBOXED", "1")
    r = SiteRenderer(viewports=[("only", 1024, 768)])
    assert r.viewports == [("only", 1024, 768)]


# ---------------------------------------------------------------------------
# Playwright-required behavior — skipped when playwright not installed
# ---------------------------------------------------------------------------


def test_render_raises_helpful_error_when_playwright_missing(
    renderer: SiteRenderer, tmp_path: Path, monkeypatch,
) -> None:
    """When playwright isn't importable, render_section raises
    PlaywrightNotInstalledError with operator-actionable message."""
    # Force the import to fail even if installed.
    import sys
    monkeypatch.setitem(sys.modules, "playwright", None)
    with pytest.raises(PlaywrightNotInstalledError) as exc:
        renderer.render_section(
            section_html="<h1>x</h1>", section_css="", section_js="",
            brand_tokens_css="", screenshot_dir=tmp_path,
        )
    assert "playwright install chromium" in str(exc.value)


@pytest.mark.skipif(
    pytest.importorskip is not None and  # always True; trick to evaluate lazily
    True is False,
    reason="placeholder; replaced by importorskip when running with real playwright",
)
def test_render_real_chromium_when_available(
    renderer: SiteRenderer, tmp_path: Path,
) -> None:
    """Real Chromium happy path — only runs when playwright is installed."""
    pytest.importorskip("playwright")
    result = renderer.render_section(
        section_html="<h1>Hello</h1>",
        section_css="h1 { color: red; }",
        section_js="",
        brand_tokens_css=":root { --brand: blue; }",
        screenshot_dir=tmp_path,
    )
    assert "desktop" in result.screenshot_paths
    assert "mobile" in result.screenshot_paths


# ---------------------------------------------------------------------------
# RenderResult shape — pinned for downstream consumers (U15b site_engine)
# ---------------------------------------------------------------------------


def test_render_result_dataclass_shape() -> None:
    """Drift pin on the public dataclass fields so U15b doesn't break
    when the renderer evolves."""
    from src.generation.site_render import RenderResult
    fields = {f.name for f in RenderResult.__dataclass_fields__.values()}
    assert fields == {
        "screenshot_paths", "dom_snapshot", "console_errors",
        "network_blocked", "render_time_ms", "degraded", "degraded_reason",
    }


def test_blocked_request_dataclass_shape() -> None:
    fields = {f.name for f in BlockedRequest.__dataclass_fields__.values()}
    assert fields == {"url", "reason"}


def test_console_message_dataclass_shape() -> None:
    fields = {f.name for f in ConsoleMessage.__dataclass_fields__.values()}
    assert fields == {"severity", "text", "source"}
