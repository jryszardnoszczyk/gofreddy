"""Tests for freddy evaluate CLI — thin HTTP-client shape (Phase 0c).

The evaluate command group used to call Gemini directly with an embedded
``EVALUATE_PROMPT`` and read files itself. Phase 0c moved all of that to
``judges/session/*`` and ``judges/evolution/*``. The CLI is now a dumb
shim that POSTs to the role-locked judge service.

These tests exercise the shim via ``typer.testing.CliRunner`` and mock
``httpx.post`` so we don't stand up the real service.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from cli.freddy.main import app


runner = CliRunner()


class _FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body)

    def json(self) -> dict[str, Any]:
        return self._body


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_JUDGE_URL", "http://127.0.0.1:7100")
    monkeypatch.setenv("SESSION_INVOKE_TOKEN", "session-tok")
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://127.0.0.1:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "evo-tok")


def _capture_post(monkeypatch: pytest.MonkeyPatch, response: _FakeResponse) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, json=None, headers=None, timeout=None, **kwargs: Any):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return response

    monkeypatch.setattr(httpx, "post", _fake_post)
    return captured


def test_review_posts_to_session_judge(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    captured = _capture_post(
        monkeypatch,
        _FakeResponse(
            200,
            {
                "decision": "KEEP",
                "confidence": 0.8,
                "weaknesses": ["w1", "w2", "w3"],
                "rationale": "ok",
            },
        ),
    )
    result = runner.invoke(app, ["evaluate", "review", str(session_dir)])
    assert result.exit_code == 0, result.stdout
    assert captured["url"] == "http://127.0.0.1:7100/invoke/review"
    assert captured["headers"]["Authorization"] == "Bearer session-tok"
    assert captured["json"]["session_dir"] == str(session_dir)
    # The CLI echoes the response body verbatim.
    assert "KEEP" in result.stdout


def test_critique_reads_request_file_and_posts(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    req_file = tmp_path / "req.json"
    req_file.write_text(json.dumps({"session_artifacts": "x", "session_goal": "y"}))
    captured = _capture_post(
        monkeypatch,
        _FakeResponse(200, {"overall": "pass", "confidence": 0.9, "issues": [], "rationale": "ok"}),
    )
    result = runner.invoke(app, ["evaluate", "critique", str(req_file)])
    assert result.exit_code == 0
    assert captured["url"] == "http://127.0.0.1:7100/invoke/critique"
    assert captured["json"]["session_goal"] == "y"
    assert "pass" in result.stdout


def test_variant_posts_to_evolution_judge(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    captured = _capture_post(
        monkeypatch,
        _FakeResponse(
            200,
            {
                "primary": {"aggregate_score": 8.0},
                "secondary": {"aggregate_score": 7.5},
                "aggregate": {"aggregate_score": 7.75, "structural_passed": True, "grounding_passed": True},
            },
        ),
    )
    result = runner.invoke(
        app,
        [
            "evaluate", "variant", "geo", str(session_dir),
            "--campaign-id", "c1", "--variant-id", "v42",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert captured["url"] == "http://127.0.0.1:7200/invoke/score"
    assert captured["headers"]["Authorization"] == "Bearer evo-tok"
    body = captured["json"]
    assert body["domain"] == "geo"
    assert body["session_dir"] == str(session_dir)
    assert body["campaign_id"] == "c1"
    assert body["variant_id"] == "v42"


def test_review_surfaces_judge_error_status(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    _capture_post(monkeypatch, _FakeResponse(503, {"detail": "overloaded"}))
    result = runner.invoke(app, ["evaluate", "review", str(session_dir)])
    assert result.exit_code != 0
    body = json.loads(result.stderr.strip())
    assert body["error"]["code"] == "judge_error"
    assert "503" in body["error"]["message"]


def test_review_surfaces_connection_error(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    def _fake_post(*args: Any, **kwargs: Any):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", _fake_post)
    result = runner.invoke(app, ["evaluate", "review", str(session_dir)])
    assert result.exit_code != 0
    body = json.loads(result.stderr.strip())
    assert body["error"]["code"] == "judge_unreachable"
    assert "unreachable" in body["error"]["message"].lower()


def test_critique_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture_post(
        monkeypatch,
        _FakeResponse(200, {"overall": "pass"}),
    )
    payload = json.dumps({"session_artifacts": "stdin", "session_goal": "g"})
    result = runner.invoke(app, ["evaluate", "critique", "-"], input=payload)
    assert result.exit_code == 0, result.stdout
    assert captured["json"]["session_artifacts"] == "stdin"


def test_critique_missing_request_file(tmp_path) -> None:
    missing = tmp_path / "nope.json"
    result = runner.invoke(app, ["evaluate", "critique", str(missing)])
    assert result.exit_code != 0
    body = json.loads(result.stderr.strip())
    assert body["error"]["code"] == "request_file_not_found"
    assert "not found" in body["error"]["message"].lower()


def test_critique_malformed_request_file(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    result = runner.invoke(app, ["evaluate", "critique", str(bad)])
    assert result.exit_code != 0
    body = json.loads(result.stderr.strip())
    assert body["error"]["code"] == "invalid_json"
    assert "valid json" in body["error"]["message"].lower()
