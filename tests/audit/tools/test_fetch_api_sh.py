"""Integration-style tests for cli/scripts/fetch_api.sh.

Uses a localhost HTTP server (Python ``http.server``) so we exercise the real
script without hitting real APIs. Runs serially by design — port collisions
across parallel pytest workers would be flaky. ``serial`` marker keeps it
visible to operators.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "cli" / "scripts" / "fetch_api.sh"
)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _MockHandler(BaseHTTPRequestHandler):
    """Configurable per-test handler. Subclasses override ``responses``."""

    responses: list[dict] = []
    captured_requests: list[dict] = []

    def log_message(self, fmt: str, *args) -> None:  # silence stderr
        pass

    def _serve(self) -> None:
        if not self.responses:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"no response queued")
            return
        spec = self.responses.pop(0)
        # Capture request for assertions.
        self.__class__.captured_requests.append({
            "path": self.path,
            "method": self.command,
            "headers": dict(self.headers),
        })
        self.send_response(spec.get("status", 200))
        for k, v in spec.get("headers", {}).items():
            self.send_header(k, v)
        body = spec.get("body", b"")
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._serve()

    def do_POST(self) -> None:
        self._serve()


@pytest.fixture
def mock_server():
    """Spin up a fresh ThreadingHTTPServer with reset response queue."""
    _MockHandler.responses = []
    _MockHandler.captured_requests = []
    port = _free_port()
    srv = ThreadingHTTPServer(("127.0.0.1", port), _MockHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield {
            "url": f"http://127.0.0.1:{port}",
            "responses": _MockHandler.responses,
            "captured": _MockHandler.captured_requests,
        }
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2)


def _run(url: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    cmd = ["bash", str(SCRIPT_PATH), *args, url]
    full_env = os.environ.copy()
    full_env["PACE_MS"] = "0"  # tests don't need to wait
    if env:
        full_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=full_env)


def test_fetch_returns_2xx_body(mock_server) -> None:
    mock_server["responses"].append({"status": 200, "body": '{"ok": true}'})
    out = _run(mock_server["url"] + "/x")
    assert out.returncode == 0
    assert out.stdout.strip() == '{"ok": true}'


def test_fetch_user_agent_is_set(mock_server) -> None:
    mock_server["responses"].append({"status": 200, "body": "ok"})
    _run(mock_server["url"] + "/y")
    captured = mock_server["captured"]
    assert len(captured) == 1
    ua = captured[0]["headers"].get("User-Agent", "")
    assert "GoFreddy-Audit" in ua
    assert "jryszardn@gmail.com" in ua


def test_fetch_retries_on_5xx(mock_server) -> None:
    """500 → 502 → 200; final body wins."""
    mock_server["responses"].extend([
        {"status": 500, "body": "fail-1"},
        {"status": 502, "body": "fail-2"},
        {"status": 200, "body": '{"final": true}'},
    ])
    # Override sleep budget to keep test fast.
    out = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--max-retries", "5",
         mock_server["url"] + "/retry"],
        capture_output=True, text=True, timeout=30,
        # Skip the host-pacing sleep entirely by passing PACE_MS=0 isn't enough
        # for the in-script `sleep $((2**attempt))` — we tolerate ~6s wait.
    )
    assert out.returncode == 0, out.stderr
    assert "final" in out.stdout


def test_fetch_no_retry_on_4xx(mock_server) -> None:
    mock_server["responses"].append({"status": 404, "body": "not found"})
    out = _run(mock_server["url"] + "/z")
    assert out.returncode == 2
    assert len(mock_server["captured"]) == 1, "404 must NOT retry"


def test_fetch_pagination_follows_link_header(mock_server) -> None:
    """3 pages, Link header points to next; after 3rd page no Link → stop."""
    base = mock_server["url"]
    mock_server["responses"].extend([
        {"status": 200, "body": '{"page":1}',
         "headers": {"Link": f'<{base}/p2>; rel="next", <{base}/last>; rel="last"'}},
        {"status": 200, "body": '{"page":2}',
         "headers": {"Link": f'<{base}/p3>; rel="next"'}},
        {"status": 200, "body": '{"page":3}'},
    ])
    out = _run(mock_server["url"] + "/p1", "--paginate", "--max-pages", "10")
    assert out.returncode == 0, out.stderr
    assert '"page":1' in out.stdout
    assert '"page":2' in out.stdout
    assert '"page":3' in out.stdout
    assert len(mock_server["captured"]) == 3


def test_fetch_pagination_capped_by_max_pages(mock_server) -> None:
    base = mock_server["url"]
    # Always-next, so we'd go forever without the cap.
    for i in range(10):
        mock_server["responses"].append({
            "status": 200, "body": f'{{"i":{i}}}',
            "headers": {"Link": f'<{base}/p>; rel="next"'},
        })
    out = _run(mock_server["url"] + "/p", "--paginate", "--max-pages", "2")
    assert out.returncode == 0
    assert len(mock_server["captured"]) == 2


def test_fetch_help_flag() -> None:
    out = subprocess.run(["bash", str(SCRIPT_PATH), "--help"],
                         capture_output=True, text=True, timeout=5)
    assert out.returncode == 0
    assert "Usage:" in out.stderr or "Usage:" in out.stdout


def test_fetch_no_url_exits_4() -> None:
    out = subprocess.run(["bash", str(SCRIPT_PATH)],
                         capture_output=True, text=True, timeout=5)
    assert out.returncode == 4
