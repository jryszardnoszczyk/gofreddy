"""CRITIQUE_BACKEND/CRITIQUE_MODEL dispatch coverage for session-time judges.

Per-step model split (2026-05-13): both critique_agent and review_agent
should default to codex/gpt-5.5 (off the Claude Max pool) and honor
CRITIQUE_BACKEND=claude as an opt-back-in. Sibling test in
tests/autoresearch/test_per_step_model_split.py covers the inner-target
resolution chain that runs before these critique calls.

This file lives in tests/judges/ (not tests/autoresearch/) because
autoresearch/judges/__init__.py shadows the top-level judges/ package
once autoresearch/ is on sys.path — see that file's path bootstrap.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from judges.session.agents import critique_agent, review_agent


_OK_JSON = '```json\n{"overall": "ok", "confidence": 0.5, "issues": [], "rationale": ""}\n```'
_OK_REVIEW_JSON = '```json\n{"decision": "approve", "confidence": 0.5, "weaknesses": [], "rationale": ""}\n```'


def _capture_dispatch(agent_module, ok_json: str) -> dict[str, object]:
    captured: dict[str, object] = {}

    async def fake_codex(prompt: str, *, model: str = "gpt-5.5", timeout: int = 900) -> str:
        captured["backend"] = "codex"
        captured["model"] = model
        return ok_json

    async def fake_claude(prompt: str, *, model: str = "claude-opus-4-7", timeout: int = 900) -> str:
        captured["backend"] = "claude"
        captured["model"] = model
        return ok_json

    captured["_codex"] = fake_codex
    captured["_claude"] = fake_claude
    return captured


def test_critique_defaults_to_codex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRITIQUE_BACKEND", raising=False)
    monkeypatch.delenv("CRITIQUE_MODEL", raising=False)
    cap = _capture_dispatch(critique_agent, _OK_JSON)
    with patch.object(critique_agent, "invoke_codex", cap["_codex"]), \
         patch.object(critique_agent, "invoke_claude", cap["_claude"]):
        asyncio.run(critique_agent.critique({"session_artifacts": "x", "session_goal": "y"}))
    assert cap["backend"] == "codex"
    assert cap["model"] == "gpt-5.5"


def test_critique_respects_claude_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRITIQUE_BACKEND", "claude")
    monkeypatch.setenv("CRITIQUE_MODEL", "claude-sonnet-4-6")
    cap = _capture_dispatch(critique_agent, _OK_JSON)
    with patch.object(critique_agent, "invoke_codex", cap["_codex"]), \
         patch.object(critique_agent, "invoke_claude", cap["_claude"]):
        asyncio.run(critique_agent.critique({"session_artifacts": "x", "session_goal": "y"}))
    assert cap["backend"] == "claude"
    assert cap["model"] == "claude-sonnet-4-6"


def test_review_defaults_to_codex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRITIQUE_BACKEND", raising=False)
    monkeypatch.delenv("CRITIQUE_MODEL", raising=False)
    cap = _capture_dispatch(review_agent, _OK_REVIEW_JSON)
    with patch.object(review_agent, "invoke_codex", cap["_codex"]), \
         patch.object(review_agent, "invoke_claude", cap["_claude"]):
        asyncio.run(review_agent.review({
            "original_content": "a", "proposed_changes": "b", "competitive_context": "c",
        }))
    assert cap["backend"] == "codex"


def test_review_respects_claude_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRITIQUE_BACKEND", "claude")
    monkeypatch.delenv("CRITIQUE_MODEL", raising=False)
    cap = _capture_dispatch(review_agent, _OK_REVIEW_JSON)
    with patch.object(review_agent, "invoke_codex", cap["_codex"]), \
         patch.object(review_agent, "invoke_claude", cap["_claude"]):
        asyncio.run(review_agent.review({
            "original_content": "a", "proposed_changes": "b", "competitive_context": "c",
        }))
    assert cap["backend"] == "claude"
    assert cap["model"] == "claude-opus-4-7"  # default fallback when CRITIQUE_MODEL unset
