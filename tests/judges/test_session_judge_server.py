"""Session-mode judge-service tests.

Mocks ``invoke_claude`` to avoid touching the real CLI. Verifies:

- /invoke/review and /invoke/critique return verdict-shaped JSON;
- missing/bad bearer token returns 401;
- evolution-only endpoints are NOT registered on the session app
  (a session-mode app does not expose ``/invoke/score``).
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from judges.server import create_app


TOKEN = "session-test-token"


@pytest.fixture
def session_app(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    # Route events log to a throwaway path so test runs don't pollute ~/.
    monkeypatch.setenv("HOME", str(tmp_path))
    app = create_app(mode="session", invoke_token=TOKEN)
    return TestClient(app)


def _patch_claude(monkeypatch: pytest.MonkeyPatch, response_json: dict[str, Any]) -> None:
    body = "```json\n" + json.dumps(response_json) + "\n```"

    async def _fake(prompt: str, **kwargs: Any) -> str:
        return body

    # Patch at both the shared module and the agent re-exports.
    monkeypatch.setattr("judges.invoke_cli.invoke_claude", _fake)
    monkeypatch.setattr("judges.session.agents.review_agent.invoke_claude", _fake)
    monkeypatch.setattr("judges.session.agents.critique_agent.invoke_claude", _fake)


def test_review_endpoint_returns_verdict(
    session_app: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_claude(
        monkeypatch,
        {
            "decision": "KEEP",
            "confidence": 0.8,
            "weaknesses": ["w1", "w2", "w3"],
            "rationale": "ok",
        },
    )
    r = session_app.post(
        "/invoke/review",
        json={"original_content": "o", "proposed_changes": "p", "competitive_context": "c"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["decision"] == "KEEP"
    assert body["weaknesses"] == ["w1", "w2", "w3"]
    assert body["confidence"] == 0.8
    assert "rationale" in body


def test_critique_endpoint_returns_verdict(
    session_app: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_claude(
        monkeypatch,
        {
            "overall": "pass",
            "confidence": 0.7,
            "issues": [],
            "rationale": "looks fine",
        },
    )
    r = session_app.post(
        "/invoke/critique",
        json={"session_artifacts": "x", "session_goal": "y"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["overall"] == "pass"


def test_missing_token_rejected(session_app: TestClient) -> None:
    r = session_app.post(
        "/invoke/review",
        json={"original_content": "o"},
    )
    assert r.status_code == 401


def test_bad_token_rejected(session_app: TestClient) -> None:
    r = session_app.post(
        "/invoke/review",
        json={"original_content": "o"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert r.status_code == 401


def test_session_app_does_not_expose_evolution_endpoints(
    session_app: TestClient,
) -> None:
    """Session mode must refuse /invoke/score — that's the evolution service."""
    r = session_app.post(
        "/invoke/score",
        json={},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 404


def test_session_app_does_not_expose_decision_endpoints(
    session_app: TestClient,
) -> None:
    for path in (
        "/invoke/decide/promotion",
        "/invoke/decide/rollback",
        "/invoke/decide/canary",
        "/invoke/system_health/saturation",
    ):
        r = session_app.post(
            path, json={}, headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert r.status_code == 404, path
