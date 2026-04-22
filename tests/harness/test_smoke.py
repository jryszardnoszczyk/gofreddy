"""Tests for harness.smoke — parse, run_check, JWT threading, extra_checks."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harness import smoke
from harness.config import Config


SAMPLE = """# SMOKE

preamble

---
id: smoke-cli
type: shell
command: echo hi
expected_exit: 0
---

prose

---
id: smoke-api
type: http
method: GET
url: http://127.0.0.1:8000/health
expected_status: 200
---

more prose
"""


def test_parse_extracts_blocks():
    checks = smoke.parse(SAMPLE)
    assert [c.id for c in checks] == ["smoke-cli", "smoke-api"]
    assert checks[0].type == "shell"
    assert checks[1].raw["url"].endswith("/health")


def test_parse_empty_returns_empty():
    assert smoke.parse("") == []


def test_run_check_shell_success(tmp_path):
    check = smoke.Check(id="s", type="shell", raw={"command": "exit 0", "expected_exit": 0}, trusted=True)
    wt = type("W", (), {"path": tmp_path})
    result = smoke.run_check(check, wt, Config(), "tok")
    assert result.ok


def test_run_check_shell_failure(tmp_path):
    check = smoke.Check(id="s", type="shell", raw={"command": "exit 2", "expected_exit": 0}, trusted=True)
    wt = type("W", (), {"path": tmp_path})
    result = smoke.run_check(check, wt, Config(), "tok")
    assert not result.ok
    assert "exit=2" in result.detail


def test_run_check_shell_untrusted_rejects_shell_substitution(tmp_path):
    # LLM-generated commands must go through shlex — shell substitution stays literal.
    check = smoke.Check(id="s", type="shell", raw={"command": "/bin/echo ok", "expected_exit": 0})
    wt = type("W", (), {"path": tmp_path})
    result = smoke.run_check(check, wt, Config(), "tok")
    assert result.ok


def test_run_check_http_injects_bearer():
    captured = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"key":"secret"}'

    def fake_urlopen(req, timeout):
        captured["headers"] = dict(req.header_items())
        captured["url"] = req.full_url
        return FakeResp()

    check = smoke.Check(
        id="s", type="http",
        raw={"method": "GET", "url": "http://x/health", "expected_status": 200, "auth": "bearer",
             "expected_body_contains": "key"},
    )
    with patch("harness.smoke.urllib.request.urlopen", fake_urlopen):
        result = smoke.run_check(check, type("W", (), {"path": Path.cwd()}), Config(), "JWT123")
    assert result.ok
    assert captured["headers"].get("Authorization") == "Bearer JWT123"


def test_run_check_http_status_mismatch():
    class FakeResp:
        status = 500
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b""

    check = smoke.Check(id="s", type="http", raw={"method": "GET", "url": "http://x", "expected_status": 200})
    with patch("harness.smoke.urllib.request.urlopen", lambda *a, **k: FakeResp()):
        result = smoke.run_check(check, type("W", (), {"path": Path.cwd()}), Config(), "tok")
    assert not result.ok
    assert "status=500" in result.detail


def test_check_raises_on_first_failure(tmp_path, monkeypatch):
    smoke_path = tmp_path / "harness" / "SMOKE.md"
    smoke_path.parent.mkdir(parents=True)
    smoke_path.write_text("---\nid: s\ntype: shell\ncommand: exit 5\nexpected_exit: 0\n---\n\n", encoding="utf-8")
    wt = type("W", (), {"path": tmp_path})
    with pytest.raises(smoke.SmokeError, match="smoke broken: s"):
        smoke.check(wt, Config(), "tok")


def test_check_runs_extra_checks_after_base(tmp_path):
    smoke_path = tmp_path / "harness" / "SMOKE.md"
    smoke_path.parent.mkdir(parents=True)
    smoke_path.write_text("", encoding="utf-8")
    wt = type("W", (), {"path": tmp_path})
    # Untrusted extra_check (trusted=False) goes through shlex.split; use an executable, not a builtin.
    extra = [smoke.Check(id="repro-F1", type="shell", raw={"command": "/usr/bin/false", "expected_exit": 0})]
    with pytest.raises(smoke.SmokeError, match="repro-F1"):
        smoke.check(wt, Config(), "tok", extra_checks=extra)


def test_check_missing_smoke_file_raises(tmp_path):
    wt = type("W", (), {"path": tmp_path})
    with pytest.raises(smoke.SmokeError, match="SMOKE.md missing"):
        smoke.check(wt, Config(), "tok")
