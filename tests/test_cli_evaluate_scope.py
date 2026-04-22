"""Tests for ``freddy evaluate variant`` — thin-client Phase 0c contract.

Producer-owned YAML loading used to live in this module's CLI code; it
now lives inside the evolution-judge-service. The autoresearch-side CLI
only POSTs ``{domain, session_dir, campaign_id, variant_id}`` to
``{EVOLUTION_JUDGE_URL}/invoke/score`` — so these tests are HTTP-client
contract tests, not YAML loading tests.

Historical note: the deleted tests asserted that the CLI walked up from
``session_dir`` to find ``programs/<domain>-evaluation-scope.yaml``.
That walk now happens on the judge-service host. See
``docs/plans/2026-04-21-002-feat-fixture-infrastructure-plan.md`` Phase 0c.
"""
from __future__ import annotations

import json
from pathlib import Path
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
    monkeypatch.setenv("EVOLUTION_JUDGE_URL", "http://127.0.0.1:7200")
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "evo-tok")


def _capture_post(
    monkeypatch: pytest.MonkeyPatch, response: _FakeResponse,
) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def _fake_post(url: str, *, json=None, headers=None, timeout=None, **kwargs: Any):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return response

    monkeypatch.setattr(httpx, "post", _fake_post)
    return captured


def _ok_body() -> dict[str, Any]:
    return {
        "primary": {"aggregate_score": 7.0},
        "secondary": {"aggregate_score": 6.5},
        "aggregate": {
            "aggregate_score": 6.75,
            "structural_passed": True,
            "grounding_passed": True,
        },
    }


def test_variant_posts_to_evolution_judge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "sessions" / "geo" / "client-x"
    session.mkdir(parents=True)
    captured = _capture_post(monkeypatch, _FakeResponse(200, _ok_body()))

    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code == 0, result.stdout
    assert captured["url"] == "http://127.0.0.1:7200/invoke/score"


def test_variant_uses_bearer_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "session"
    session.mkdir()
    captured = _capture_post(monkeypatch, _FakeResponse(200, _ok_body()))

    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code == 0
    assert captured["headers"]["Authorization"] == "Bearer evo-tok"


def test_variant_forwards_session_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI no longer reads files — it POSTs the session_dir reference."""
    session = tmp_path / "v007" / "sessions" / "competitive" / "client-x"
    session.mkdir(parents=True)
    captured = _capture_post(monkeypatch, _FakeResponse(200, _ok_body()))

    result = runner.invoke(app, ["evaluate", "variant", "competitive", str(session)])
    assert result.exit_code == 0
    assert captured["json"]["session_dir"] == str(session)
    assert captured["json"]["domain"] == "competitive"


def test_variant_forwards_campaign_and_variant_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "session"
    session.mkdir()
    captured = _capture_post(monkeypatch, _FakeResponse(200, _ok_body()))

    result = runner.invoke(
        app,
        [
            "evaluate", "variant", "storyboard", str(session),
            "--campaign-id", "C-42",
            "--variant-id", "V-007",
        ],
    )
    assert result.exit_code == 0
    assert captured["json"]["campaign_id"] == "C-42"
    assert captured["json"]["variant_id"] == "V-007"


def test_variant_does_not_require_scope_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No programs/ dir, no YAML — the CLI still succeeds because the
    producer-owned YAML walk now happens on the judge-service side."""
    session = tmp_path / "empty" / "sessions" / "geo"
    session.mkdir(parents=True)
    captured = _capture_post(monkeypatch, _FakeResponse(200, _ok_body()))

    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code == 0, result.stdout
    assert captured["json"]["session_dir"] == str(session)


def test_variant_surfaces_500_as_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "session"
    session.mkdir()
    _capture_post(monkeypatch, _FakeResponse(500, {"detail": "judge exploded"}))
    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code != 0
    body = json.loads(result.stdout.strip())
    assert "error" in body
    assert "500" in body["error"]


def test_variant_surfaces_connection_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "session"
    session.mkdir()

    def _fake_post(*args: Any, **kwargs: Any):
        raise httpx.ConnectError("no judge")

    monkeypatch.setattr(httpx, "post", _fake_post)
    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code != 0
    body = json.loads(result.stdout.strip())
    assert "unreachable" in body["error"].lower()


def test_variant_echoes_response_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = tmp_path / "session"
    session.mkdir()
    payload = _ok_body()
    _capture_post(monkeypatch, _FakeResponse(200, payload))
    result = runner.invoke(app, ["evaluate", "variant", "geo", str(session)])
    assert result.exit_code == 0
    echoed = json.loads(result.stdout.strip())
    assert echoed == payload
