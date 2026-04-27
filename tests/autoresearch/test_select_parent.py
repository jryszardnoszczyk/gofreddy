"""Contract tests for ``autoresearch.select_parent`` + ``agent_calls`` (R-#29).

Per plan: schema-valid Pydantic model, picked parent in top-K eligibility
set, non-empty rationale. Mock the LLM call with canned responses; no
behavioral mocks.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

from agent_calls import (
    DEFAULT_MODEL,
    ParentSelection,
    build_select_parent_prompt,
    select_parent_agent,
)


def test_parent_selection_pydantic_requires_nonempty_rationale() -> None:
    with pytest.raises(ValidationError):
        ParentSelection(parent_id="v-0001", rationale="   ", confidence="high")


def test_parent_selection_pydantic_rejects_bad_confidence() -> None:
    with pytest.raises(ValidationError):
        ParentSelection(parent_id="v-0001", rationale="ok", confidence="meh")  # type: ignore[arg-type]


def test_parent_selection_pydantic_happy_path() -> None:
    m = ParentSelection(
        parent_id="v-0007",
        rationale="Exploration pressure was low (4 plateau children); swapping to v-0007 introduces novel prompt space.",
        confidence="medium",
    )
    assert m.parent_id == "v-0007"
    assert m.confidence in {"high", "medium", "low"}
    assert len(m.rationale.strip()) > 0


def test_build_prompt_carries_exploration_vs_exploitation_intent() -> None:
    prompt = build_select_parent_prompt(
        candidates=[{"id": "v-0001", "score": 0.7, "children": 2}],
        gen_rows=[{"gen_id": 12, "mean_composite": 0.68}],
        lane="core",
    )
    # Contract: prompt MUST name the exploration-vs-exploitation balance
    # explicitly — without this the loop risks mode collapse.
    assert "exploration" in prompt.lower()
    assert "exploitation" in prompt.lower()
    assert "balance" in prompt.lower()


def test_build_prompt_handles_cold_start_trajectory() -> None:
    prompt = build_select_parent_prompt(
        candidates=[{"id": "v-0001", "score": 0.7, "children": 0}],
        gen_rows=[],
        lane="core",
    )
    assert "cold start" in prompt.lower()


def _canned_openai_response(content: str) -> mock.MagicMock:
    resp = mock.MagicMock()
    choice = mock.MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    resp.choices = [choice]
    return resp


def test_select_parent_agent_returns_validated_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")

    canned = _canned_openai_response(
        json.dumps({
            "parent_id": "v-0003",
            "rationale": "v-0003 has rising trajectory (mean_composite +0.04) and low children count — exploration-leaning pick to avoid plateau on v-0001.",
            "confidence": "high",
        })
    )

    async def fake_create(**kwargs: object) -> mock.MagicMock:
        return canned

    fake_client = mock.MagicMock()
    fake_client.chat.completions.create = fake_create
    fake_client.close = mock.AsyncMock()

    with mock.patch("agent_calls.AsyncOpenAI", return_value=fake_client):
        result = asyncio.run(
            select_parent_agent(
                candidates=[
                    {"id": "v-0001", "score": 0.72, "children": 4, "status": "plateau"},
                    {"id": "v-0003", "score": 0.68, "children": 1, "status": "new"},
                ],
                gen_rows=[{"gen_id": 10, "mean_composite": 0.65}],
                lane="core",
            )
        )

    assert isinstance(result, ParentSelection)
    assert result.parent_id == "v-0003"
    assert len(result.rationale.strip()) > 0


def test_select_parent_agent_raises_on_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")
    canned = _canned_openai_response("not-json-at-all{")

    async def fake_create(**kwargs: object) -> mock.MagicMock:
        return canned

    fake_client = mock.MagicMock()
    fake_client.chat.completions.create = fake_create
    fake_client.close = mock.AsyncMock()

    with mock.patch("agent_calls.AsyncOpenAI", return_value=fake_client):
        with pytest.raises(ValueError):
            asyncio.run(
                select_parent_agent(
                    candidates=[{"id": "v-0001", "score": 0.7, "children": 0}],
                    gen_rows=[],
                    lane="core",
                )
            )


def test_select_parent_agent_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        asyncio.run(
            select_parent_agent(
                candidates=[{"id": "v-0001", "score": 0.7, "children": 0}],
                gen_rows=[],
                lane="core",
            )
        )


# ---- select_parent.select_parent integration (agent mocked, archive stubbed) ----


def test_select_parent_picks_from_topk_eligibility_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contract: the parent the agent picks MUST be in the top-K candidate set.

    Enforced by ``_pick_parent_via_agent`` — if the agent hallucinates an id
    not in the shown candidates, a ``ValueError`` is raised (generation fail).
    """
    import select_parent as sp

    entries = [
        {"id": "v-0001", "lane": "core", "children": 0, "status": "active",
         "domains": {}, "inner_metrics": {}},
        {"id": "v-0002", "lane": "core", "children": 2, "status": "active",
         "domains": {}, "inner_metrics": {}},
        {"id": "v-0003", "lane": "core", "children": 1, "status": "active",
         "domains": {}, "inner_metrics": {}},
    ]
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    for e in entries:
        (archive_dir / e["id"]).mkdir()

    monkeypatch.setattr(sp, "ordered_latest_entries", lambda _root: list(entries))
    monkeypatch.setattr(sp, "has_search_metrics", lambda _e, suite_id=None: True)
    monkeypatch.setattr(sp, "composite_score", lambda e: 0.7)
    monkeypatch.setattr(sp, "domain_score", lambda e, lane: 0.7)
    monkeypatch.setattr(sp, "normalize_lane", lambda lane: lane)

    eligible_ids_seen: list[str] = []

    async def fake_agent(candidates, gen_rows, lane, **_kwargs):
        eligible_ids_seen.extend(c["id"] for c in candidates)
        # Deliberately pick one of the presented candidates
        return ParentSelection(
            parent_id=candidates[-1]["id"],
            rationale="exploration-leaning pick to diversify from plateau candidates",
            confidence="medium",
        )

    monkeypatch.setattr("agent_calls.select_parent_agent", fake_agent)

    path, rationale = sp.select_parent(
        str(archive_dir), lane="core", return_rationale=True,
    )
    picked_id = Path(path).name
    assert picked_id in eligible_ids_seen
    assert rationale is not None and len(rationale.strip()) > 0


def test_select_parent_raises_when_agent_picks_out_of_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contract: out-of-set picks hard-fail (no sigmoid fallback, per plan)."""
    import select_parent as sp

    entries = [
        {"id": "v-0001", "lane": "core", "children": 0, "status": "active",
         "domains": {}, "inner_metrics": {}},
    ]
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "v-0001").mkdir()

    monkeypatch.setattr(sp, "ordered_latest_entries", lambda _root: list(entries))
    monkeypatch.setattr(sp, "has_search_metrics", lambda _e, suite_id=None: True)
    monkeypatch.setattr(sp, "composite_score", lambda e: 0.7)
    monkeypatch.setattr(sp, "domain_score", lambda e, lane: 0.7)
    monkeypatch.setattr(sp, "normalize_lane", lambda lane: lane)

    async def fake_agent(candidates, gen_rows, lane, **_kwargs):
        return ParentSelection(
            parent_id="v-NONEXISTENT",
            rationale="hallucinated id",
            confidence="low",
        )

    monkeypatch.setattr("agent_calls.select_parent_agent", fake_agent)

    with pytest.raises(ValueError, match="not in"):
        sp.select_parent(str(archive_dir), lane="core", return_rationale=True)


def test_default_model_is_defined() -> None:
    # Schema-only sanity: something is set. Actual routing is tested in call sites.
    assert isinstance(DEFAULT_MODEL, str) and DEFAULT_MODEL


def test_call_openai_json_uses_parent_base_url_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_call_openai_json passes AUTORESEARCH_PARENT_BASE_URL to AsyncOpenAI."""
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = self  # so .chat.completions.create works
            self.completions = self

        async def create(self, **kwargs):
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.setenv("AUTORESEARCH_PARENT_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("AUTORESEARCH_PARENT_API_KEY", "or-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "should-be-overridden")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    asyncio.run(agent_calls._call_openai_json(prompt="x", model="openrouter/deepseek/deepseek-v3"))

    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["api_key"] == "or-test-key"


def test_call_openai_json_default_no_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTORESEARCH_PARENT_BASE_URL unset, base_url is None (default OpenAI)."""
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.delenv("AUTORESEARCH_PARENT_BASE_URL", raising=False)
    monkeypatch.delenv("AUTORESEARCH_PARENT_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "default-key")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    asyncio.run(agent_calls._call_openai_json(prompt="x", model="gpt-5.4"))

    assert captured["base_url"] is None
    assert captured["api_key"] == "default-key"


def test_call_openai_json_uses_parent_model_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AUTORESEARCH_PARENT_MODEL overrides the function's default model arg.

    Necessary for OpenRouter routing — OpenRouter requires qualified slugs
    like ``openai/gpt-5.4``, not the bare DEFAULT_MODEL value ``gpt-5.4``.
    Without this, every parent-selection call 404s on the documented setup.
    """
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            captured["model"] = kwargs.get("model")
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.setenv("AUTORESEARCH_PARENT_MODEL", "openai/gpt-5.4")
    monkeypatch.setenv("OPENAI_API_KEY", "default-key")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    # Caller passes the bare default; env var should override
    asyncio.run(agent_calls._call_openai_json(prompt="x", model=agent_calls.DEFAULT_MODEL))

    assert captured["model"] == "openai/gpt-5.4"


def test_call_openai_json_no_parent_model_env_uses_caller_arg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When AUTORESEARCH_PARENT_MODEL unset, caller's model arg is used."""
    captured: dict = {}

    class FakeClient:
        def __init__(self, *, api_key: str, base_url: str | None = None) -> None:
            self.chat = self
            self.completions = self

        async def create(self, **kwargs):
            captured["model"] = kwargs.get("model")
            class _Choice:
                finish_reason = "stop"
                class message:
                    content = '{"parent_id": "v-1", "rationale": "ok", "confidence": "high"}'
            class _Resp:
                choices = [_Choice()]
            return _Resp()

        async def close(self) -> None:
            pass

    monkeypatch.delenv("AUTORESEARCH_PARENT_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "default-key")
    monkeypatch.setattr("agent_calls.AsyncOpenAI", FakeClient)

    import agent_calls
    asyncio.run(agent_calls._call_openai_json(prompt="x", model="gpt-5.4"))

    assert captured["model"] == "gpt-5.4"
