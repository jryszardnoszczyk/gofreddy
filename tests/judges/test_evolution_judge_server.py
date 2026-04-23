"""Evolution-mode judge-service tests.

Mocks the CLI wrappers. Verifies:

- all 6 system_health roles reachable at /invoke/system_health/{role};
- /invoke/decide/promotion returns {decision, reasoning, confidence, concerns};
- no /admin/* or tune-prompt routes exist on the service;
- session endpoints are NOT registered on the evolution app.
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from judges.server import create_app


TOKEN = "evo-test-token"


@pytest.fixture
def evo_app(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    monkeypatch.setenv("HOME", str(tmp_path))
    app = create_app(mode="evolution", invoke_token=TOKEN)
    return TestClient(app)


def _patch_cli(monkeypatch: pytest.MonkeyPatch, response_json: Any) -> None:
    body = "```json\n" + json.dumps(response_json) + "\n```"

    async def _fake(prompt: str, **kwargs: Any) -> str:
        return body

    # Patch the agent-module imports so both primary+secondary callers hit the fake.
    monkeypatch.setattr("judges.invoke_cli.invoke_claude", _fake)
    monkeypatch.setattr("judges.invoke_cli.invoke_codex", _fake)
    for name in (
        "judges.evolution.agents.variant_scorer.invoke_claude",
        "judges.evolution.agents.variant_scorer.invoke_codex",
        "judges.evolution.agents.promotion_agent.invoke_claude",
        "judges.evolution.agents.rollback_agent.invoke_claude",
        "judges.evolution.agents.canary_agent.invoke_claude",
        "judges.evolution.agents.system_health_agent.invoke_claude",
    ):
        monkeypatch.setattr(name, _fake, raising=False)


def test_score_endpoint(evo_app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_cli(
        monkeypatch,
        {
            "fixture_id": "F1",
            "per_criterion": [],
            "aggregate_score": 7.5,
            "structural_passed": True,
            "grounding_passed": True,
        },
    )
    r = evo_app.post(
        "/invoke/score",
        json={"domain": "geo", "fixture": {"id": "F1"}, "session_ref": "s1", "lane": "core", "seeds": 10},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "primary" in body and "secondary" in body and "aggregate" in body
    assert body["aggregate"]["aggregate_score"] == 7.5


def test_decide_promotion_shape(evo_app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_cli(
        monkeypatch,
        {
            "decision": "promote",
            "reasoning": "candidate beats head on 5/6 fixtures",
            "confidence": 0.83,
            "concerns": ["F1-2: marginal regression"],
        },
    )
    r = evo_app.post(
        "/invoke/decide/promotion",
        json={"candidate_scores": {}, "head_scores": {}, "lane": "core"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "promote"
    assert "reasoning" in body
    assert "confidence" in body
    assert isinstance(body["concerns"], list)


def test_decide_rollback(evo_app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_cli(
        monkeypatch,
        {"decision": "hold", "reasoning": "r", "confidence": 0.5, "concerns": []},
    )
    r = evo_app.post(
        "/invoke/decide/rollback",
        json={"head_trajectory": {}, "previous_head": {}, "lane": "core"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "hold"


def test_decide_canary(evo_app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_cli(
        monkeypatch,
        {"decision": "go", "reasoning": "r", "confidence": 0.9, "concerns": []},
    )
    r = evo_app.post(
        "/invoke/decide/canary",
        json={"canary_checkpoints": {}, "variant_id": "v7"},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "go"


@pytest.mark.parametrize(
    "role", [
        "saturation", "content_drift", "discriminability",
        "fixture_quality", "calibration_drift", "noise_escalation",
    ],
)
def test_all_six_system_health_roles(
    evo_app: TestClient, monkeypatch: pytest.MonkeyPatch, role: str,
) -> None:
    _patch_cli(
        monkeypatch,
        {"verdict": "fine", "rationale": "nothing flagged", "confidence": 0.6},
    )
    r = evo_app.post(
        f"/invoke/system_health/{role}",
        json={"item": {"anything": "ok"}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 200, r.text
    assert "verdict" in r.json()


def test_unknown_system_health_role_is_404(
    evo_app: TestClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_cli(monkeypatch, {"verdict": "fine"})
    r = evo_app.post(
        "/invoke/system_health/not_a_role",
        json={"item": {}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert r.status_code == 404


def test_no_admin_or_tune_prompt_routes(evo_app: TestClient) -> None:
    """Judge services never expose runtime mutation endpoints."""
    for route in evo_app.app.routes:
        path = getattr(route, "path", "")
        assert not path.startswith("/admin"), f"unexpected admin route: {path}"
        assert "tune" not in path, f"unexpected tune route: {path}"
        assert "prompt" not in path, f"unexpected prompt route: {path}"


def test_session_endpoints_absent_in_evolution_mode(evo_app: TestClient) -> None:
    for path in ("/invoke/review", "/invoke/critique"):
        r = evo_app.post(
            path, json={}, headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert r.status_code == 404, path


def test_missing_token_rejected_on_evolution(evo_app: TestClient) -> None:
    r = evo_app.post("/invoke/score", json={})
    assert r.status_code == 401
