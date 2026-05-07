"""Regression tests for agent_calls._model_locks_temperature + the
temperature-omission branch in _call_openai_json.

Pre-fix (commit d00d6ff, 2026-05-06): the call sent ``temperature=0.2``
on every request. After bumping the production model to gpt-5.5 every
parent-selection call started crashing with HTTP 400 (gpt-5+ rejects
explicit non-default temperature). The fix detects gpt-5+ family slugs
and omits the kwarg entirely.

Reference: ``autoresearch/agent_calls.py:124-181``.
"""

from __future__ import annotations

import pytest

# agent_calls imports openai + pydantic at module top — skip if the venv
# lacks either dep (matches the test_select_parent.py pattern).
pytest.importorskip("openai")
pytest.importorskip("pydantic")

import agent_calls


# ---------------------------------------------------------------------------
# _model_locks_temperature: pure-string predicate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model",
    [
        "gpt-5",
        "gpt-5.5",
        "gpt-5.6",
        "gpt-5-codex",
        "gpt-5-turbo",
        "GPT-5.5",  # case-insensitive
        "  gpt-5.5  ",  # whitespace-tolerant
        "openai/gpt-5.5",  # OpenRouter prefix
        "openrouter/openai/gpt-5.5",  # nested provider prefix
    ],
)
def test_model_locks_temperature_gpt5_family(model):
    assert agent_calls._model_locks_temperature(model)


@pytest.mark.parametrize(
    "model",
    [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4.1",
        "gpt-3.5-turbo",
        "openai/gpt-4o",
        "openrouter/anthropic/claude-3-opus",
        "deepseek/deepseek-v3",
        "",
    ],
)
def test_model_locks_temperature_pre_gpt5_returns_false(model):
    assert not agent_calls._model_locks_temperature(model)


def test_model_locks_temperature_handles_none_safely():
    # Defensive: production passes a string, but treat None gracefully.
    assert not agent_calls._model_locks_temperature(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _call_openai_json: temperature kwarg gating end-to-end
# ---------------------------------------------------------------------------


class _FakeChoice:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})()
        self.finish_reason = "stop"


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeChatCompletions:
    def __init__(self, captured):
        self.captured = captured

    async def create(self, **kwargs):
        self.captured.update(kwargs)
        return _FakeResponse('{"ok": true}')


class _FakeChat:
    def __init__(self, captured):
        self.completions = _FakeChatCompletions(captured)


class _FakeAsyncOpenAI:
    last_captured: dict = {}

    def __init__(self, *args, **kwargs):
        type(self).last_captured.clear()
        self.chat = _FakeChat(type(self).last_captured)

    async def close(self):
        pass


def _patch_async_openai(monkeypatch):
    monkeypatch.setattr(agent_calls, "AsyncOpenAI", _FakeAsyncOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    # Clear potentially-set provider routing so we exercise the bare model path.
    monkeypatch.delenv("AUTORESEARCH_PARENT_BASE_URL", raising=False)
    monkeypatch.delenv("AUTORESEARCH_PARENT_API_KEY", raising=False)
    monkeypatch.delenv("AUTORESEARCH_PARENT_MODEL", raising=False)


def test_call_openai_json_omits_temperature_for_gpt5(monkeypatch):
    """gpt-5.5 path: ``temperature`` must NOT appear in the create kwargs."""
    import asyncio
    _patch_async_openai(monkeypatch)
    asyncio.run(agent_calls._call_openai_json("test prompt", model="gpt-5.5"))
    captured = _FakeAsyncOpenAI.last_captured
    assert captured["model"] == "gpt-5.5"
    assert "temperature" not in captured, (
        f"temperature must be absent for gpt-5.5; got kwargs={list(captured)}"
    )


def test_call_openai_json_includes_temperature_for_gpt4(monkeypatch):
    """gpt-4o path: ``temperature=0.2`` should be sent."""
    import asyncio
    _patch_async_openai(monkeypatch)
    asyncio.run(agent_calls._call_openai_json("test prompt", model="gpt-4o"))
    captured = _FakeAsyncOpenAI.last_captured
    assert captured.get("temperature") == 0.2


def test_call_openai_json_omits_temperature_for_routed_gpt5(monkeypatch):
    """OpenRouter prefix ``openai/gpt-5.5`` (set via AUTORESEARCH_PARENT_MODEL
    env var) must also drop temperature.
    """
    import asyncio
    _patch_async_openai(monkeypatch)
    monkeypatch.setenv("AUTORESEARCH_PARENT_MODEL", "openai/gpt-5.5")
    asyncio.run(agent_calls._call_openai_json("test prompt", model="gpt-4o"))
    captured = _FakeAsyncOpenAI.last_captured
    # AUTORESEARCH_PARENT_MODEL overrides the function arg, and the resolved
    # name still matches gpt-5+ family → drop temperature.
    assert captured["model"] == "openai/gpt-5.5"
    assert "temperature" not in captured
