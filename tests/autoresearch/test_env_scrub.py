"""Verify autoresearch/evaluate_variant.py::_score_env scrubs tokens.

Evolution-scoped + provider-API-key env vars must NOT be inherited by
untrusted variant subprocesses. SESSION_INVOKE_TOKEN must survive —
variants need it to call the session-judge-service.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Start from a known state; the test sets the full fake env.
    for key in (
        "SESSION_INVOKE_TOKEN",
        "EVOLUTION_INVOKE_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "CODEX_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


def _score_env() -> dict[str, str]:
    from evaluate_variant import _score_env as fn  # autoresearch/ on sys.path via conftest

    return fn()


def test_evolution_token_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "secret-evo")
    env = _score_env()
    assert "EVOLUTION_INVOKE_TOKEN" not in env


def test_provider_keys_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-y")
    monkeypatch.setenv("CLAUDE_API_KEY", "sk-z")
    monkeypatch.setenv("CODEX_API_KEY", "sk-w")
    env = _score_env()
    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "CLAUDE_API_KEY" not in env
    assert "CODEX_API_KEY" not in env


def test_session_token_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_INVOKE_TOKEN", "session-preserve")
    env = _score_env()
    assert env.get("SESSION_INVOKE_TOKEN") == "session-preserve"


def test_pythonpath_still_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Scrub must not wipe the PYTHONPATH setup that the old function did."""
    monkeypatch.setenv("EVOLUTION_INVOKE_TOKEN", "x")
    env = _score_env()
    assert "cli" in env.get("PYTHONPATH", ""), "cli/ should be added to PYTHONPATH"
