"""Tests for src/audit/tools/rendered_fetcher — Playwright wrapper.

Network-free: uses an in-process ThreadingHTTPServer to serve canned HTML +
exercises real Chromium rendering against localhost. Skipped if Playwright
or Chromium binary is unavailable on this runner.
"""
from __future__ import annotations

import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from src.audit.tools.rendered_fetcher import RenderedFetcher, RenderResult


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        from playwright.async_api import async_playwright  # noqa: F401
        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not _playwright_available(),
    reason="playwright not installed (optional 'audit' extra)",
)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Handler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, str, str]] = {}  # path → (status, content_type, body)

    def log_message(self, fmt, *a) -> None:
        pass

    def do_GET(self) -> None:
        spec = self.routes.get(self.path)
        if spec is None:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        status, ctype, body = spec
        body_bytes = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)


@pytest.fixture
def http_server():
    _Handler.routes = {}
    port = _free_port()
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield {
            "url": f"http://127.0.0.1:{port}",
            "routes": _Handler.routes,
        }
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


def test_fetch_basic_page(http_server) -> None:
    http_server["routes"]["/"] = (
        200, "text/html",
        '<!doctype html><html><head><title>Test Title</title></head>'
        '<body><h1>Hello</h1></body></html>',
    )

    async def _run() -> RenderResult:
        async with RenderedFetcher() as f:
            return await f.fetch(http_server["url"] + "/")

    result = asyncio.run(_run())
    assert result.degraded is False, result.degraded_reason
    assert result.status == 200
    assert "Hello" in result.html
    assert result.title == "Test Title"
    assert result.timing_ms["total"] > 0


def test_fetch_404_does_not_degrade(http_server) -> None:
    """4xx is captured in status; not a degraded state."""

    async def _run() -> RenderResult:
        async with RenderedFetcher() as f:
            return await f.fetch(http_server["url"] + "/missing")

    result = asyncio.run(_run())
    assert result.degraded is False
    assert result.status == 404


def test_fetch_screenshot_written(http_server, tmp_path: Path) -> None:
    http_server["routes"]["/"] = (
        200, "text/html",
        "<html><body><div style='width:100px;height:100px;background:red'>x</div></body></html>",
    )

    async def _run() -> RenderResult:
        async with RenderedFetcher() as f:
            return await f.fetch(http_server["url"] + "/", screenshot_dir=tmp_path)

    result = asyncio.run(_run())
    assert result.degraded is False
    assert result.screenshot_path is not None
    assert result.screenshot_path.exists()
    assert result.screenshot_path.stat().st_size > 0
    # PNG magic.
    with result.screenshot_path.open("rb") as fh:
        assert fh.read(4) == b"\x89PNG"


def test_fetch_console_errors_captured(http_server) -> None:
    http_server["routes"]["/"] = (
        200, "text/html",
        """<html><body><script>
        console.error('oops 1');
        console.warn('warn 1');
        console.error('oops 2');
        </script></body></html>""",
    )

    async def _run() -> RenderResult:
        async with RenderedFetcher() as f:
            return await f.fetch(http_server["url"] + "/", wait_after_ms=200)

    result = asyncio.run(_run())
    assert result.degraded is False
    assert any("oops 1" in e for e in result.console_errors)
    assert any("oops 2" in e for e in result.console_errors)
    assert any("warn 1" in w for w in result.console_warnings)


def test_fetch_network_log_records_subresources(http_server) -> None:
    http_server["routes"]["/"] = (
        200, "text/html",
        f"""<html><body>
        <img src="{http_server['url']}/img.png" />
        </body></html>""",
    )
    http_server["routes"]["/img.png"] = (200, "image/png", "fake")

    async def _run() -> RenderResult:
        async with RenderedFetcher() as f:
            return await f.fetch(http_server["url"] + "/")

    result = asyncio.run(_run())
    assert result.degraded is False
    urls = [r.url for r in result.network_log]
    assert any("/img.png" in u for u in urls), urls


def test_shared_context_across_multiple_fetches(http_server) -> None:
    """Two ``fetch()`` calls in the same context don't relaunch Chromium."""
    http_server["routes"]["/a"] = (200, "text/html", "<html><body>A</body></html>")
    http_server["routes"]["/b"] = (200, "text/html", "<html><body>B</body></html>")

    async def _run() -> tuple[RenderResult, RenderResult]:
        async with RenderedFetcher() as f:
            r1 = await f.fetch(http_server["url"] + "/a")
            r2 = await f.fetch(http_server["url"] + "/b")
            return r1, r2

    r1, r2 = asyncio.run(_run())
    assert r1.degraded is False and r2.degraded is False
    assert "A" in r1.html and "B" in r2.html


def test_fetch_returns_degraded_when_not_started() -> None:
    """A bare instance without start() -> fetch returns degraded."""
    f = RenderedFetcher()

    async def _run() -> RenderResult:
        return await f.fetch("https://example.com")

    result = asyncio.run(_run())
    assert result.degraded is True
    assert "playwright unavailable" in result.degraded_reason


def test_render_result_to_dict_is_jsonable() -> None:
    """to_dict() yields a structure that round-trips through json.dumps."""
    import json
    rr = RenderResult(url="https://x", final_url="https://x/y",
                      fetched_at="2026-05-06T00:00:00+00:00", status=200,
                      html="<html/>", title="t",
                      console_errors=["e1"], console_warnings=["w1"],
                      timing_ms={"total": 123.4})
    s = json.dumps(rr.to_dict())
    parsed = json.loads(s)
    assert parsed["title"] == "t"
    assert parsed["console_errors"] == ["e1"]
