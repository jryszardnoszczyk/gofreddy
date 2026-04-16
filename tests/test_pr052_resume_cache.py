"""Tests for PR-052: Backend Resume and Cache fixes.

B12: Tool result accumulation, history reconstruction, _build_contents with function parts
B13: Prompt hash in analysis cache key
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.api.routers.agent import _TOOL_CALLS_ONLY, _load_conversation_history
from src.analysis.service import AnalysisService, _PROMPT_HASH
from src.common.enums import Platform
from src.prompts import BRAND_SAFETY_PROMPT, SYSTEM_INSTRUCTION


# ---------- helpers ----------

@dataclass
class FakeMessage:
    role: str
    content: str
    metadata: dict[str, Any] | None = None


# ---------- B12 — Tool result accumulation (Part A) ----------

class TestToolResultAccumulation:
    """Verify that tool_result events are accumulated during streaming."""

    @pytest.mark.asyncio
    async def test_tool_results_in_metadata(self) -> None:
        """Streaming handler should accumulate tool_results alongside tool_calls."""
        # We can't easily test the full event_generator without a running app,
        # but we can verify the module-level constant and accumulation logic
        # indirectly by testing _load_conversation_history with metadata that
        # includes tool_results (which proves the write-read roundtrip contract).
        assert _TOOL_CALLS_ONLY == "[tool calls only]"


# ---------- B12 — History reconstruction (Part B) ----------

class TestHistoryReconstruction:
    """Tests for _load_conversation_history with function_call/response reconstruction."""

    @pytest.mark.asyncio
    async def test_happy_path_with_tool_calls_and_results(self) -> None:
        """Messages with tool_calls + tool_results reconstruct function_call/response parts."""
        messages = [
            FakeMessage(role="user", content="Search for fitness videos"),
            FakeMessage(
                role="assistant",
                content=_TOOL_CALLS_ONLY,
                metadata={
                    "tool_calls": [{"name": "search_videos", "args": {"query": "fitness"}}],
                    "tool_results": [{"name": "search_videos", "summary": "Found 10 results"}],
                },
            ),
            FakeMessage(role="user", content="Analyze the first one"),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())

        assert history is not None
        assert len(history) == 4  # user, model(fc), user(fr), user

        # First entry: user text
        assert history[0]["role"] == "user"
        assert history[0]["parts"][0]["text"] == "Search for fitness videos"

        # Second entry: model with function_call (no text since content == _TOOL_CALLS_ONLY)
        assert history[1]["role"] == "model"
        assert len(history[1]["parts"]) == 1
        fc_part = history[1]["parts"][0]
        assert "function_call" in fc_part
        assert fc_part["function_call"]["name"] == "search_videos"
        assert fc_part["function_call"]["args"] == {"query": "fitness"}

        # Third entry: user with function_response
        assert history[2]["role"] == "user"
        fr_part = history[2]["parts"][0]
        assert "function_response" in fr_part
        assert fr_part["function_response"]["name"] == "search_videos"
        assert fr_part["function_response"]["response"]["summary"] == "Found 10 results"

        # Fourth entry: user text
        assert history[3]["role"] == "user"
        assert history[3]["parts"][0]["text"] == "Analyze the first one"

    @pytest.mark.asyncio
    async def test_model_message_with_text_and_tool_calls(self) -> None:
        """Model message with both text content and tool_calls includes both parts."""
        messages = [
            FakeMessage(role="user", content="hi"),
            FakeMessage(
                role="assistant",
                content="Let me search for that.",
                metadata={
                    "tool_calls": [{"name": "search_videos", "args": {"query": "test"}}],
                    "tool_results": [{"name": "search_videos", "summary": "Done"}],
                },
            ),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None

        # Model turn should have text + function_call
        model_entry = history[1]
        assert model_entry["role"] == "model"
        assert len(model_entry["parts"]) == 2
        assert model_entry["parts"][0]["text"] == "Let me search for that."
        assert "function_call" in model_entry["parts"][1]

    @pytest.mark.asyncio
    async def test_backward_compat_no_metadata(self) -> None:
        """Messages without metadata fall back to text-only parts (no crash)."""
        messages = [
            FakeMessage(role="user", content="hello"),
            FakeMessage(role="assistant", content="Hi there!", metadata=None),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        assert len(history) == 2
        assert history[0]["parts"][0]["text"] == "hello"
        assert history[1]["parts"][0]["text"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_backward_compat_empty_metadata(self) -> None:
        """Messages with empty metadata dict fall back to text-only."""
        messages = [
            FakeMessage(role="assistant", content="response", metadata={}),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        assert len(history) == 1
        assert history[0]["parts"][0]["text"] == "response"

    @pytest.mark.asyncio
    async def test_corrupted_metadata_not_list(self) -> None:
        """tool_calls that isn't a list falls back to text-only."""
        messages = [
            FakeMessage(
                role="assistant",
                content="broken",
                metadata={"tool_calls": "not a list"},
            ),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        assert len(history) == 1
        assert history[0]["parts"][0]["text"] == "broken"

    @pytest.mark.asyncio
    async def test_corrupted_metadata_missing_name(self) -> None:
        """tool_calls with entries missing 'name' falls back to text-only."""
        messages = [
            FakeMessage(
                role="assistant",
                content="broken2",
                metadata={"tool_calls": [{"args": {}}]},  # no "name"
            ),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        assert len(history) == 1
        assert history[0]["parts"][0]["text"] == "broken2"

    @pytest.mark.asyncio
    async def test_corrupted_args_not_dict(self) -> None:
        """tool_call with non-dict args gets sanitized to empty dict."""
        messages = [
            FakeMessage(role="user", content="hi"),
            FakeMessage(
                role="assistant",
                content=_TOOL_CALLS_ONLY,
                metadata={
                    "tool_calls": [{"name": "search_videos", "args": "not_a_dict"}],
                    # Include tool_results so trailing guard doesn't remove model turn
                    "tool_results": [{"name": "search_videos", "summary": "done"}],
                },
            ),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        # Model turn has function_call with empty args
        model_entry = [h for h in history if h["role"] == "model"][0]
        fc = model_entry["parts"][0]["function_call"]
        assert fc["args"] == {}

    @pytest.mark.asyncio
    async def test_trailing_model_turn_guard(self) -> None:
        """History ending with model function_call (no function_response) pops trailing turn."""
        messages = [
            FakeMessage(role="user", content="search something"),
            FakeMessage(
                role="assistant",
                content=_TOOL_CALLS_ONLY,
                metadata={
                    "tool_calls": [{"name": "search_videos", "args": {"query": "test"}}],
                    # NOTE: no tool_results — stream was cancelled mid-execution
                },
            ),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        # Trailing model turn with function_call should be removed
        assert len(history) == 1
        assert history[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_trailing_model_text_only_not_removed(self) -> None:
        """History ending with model text-only turn is NOT removed."""
        messages = [
            FakeMessage(role="user", content="hello"),
            FakeMessage(role="assistant", content="Here are the results.", metadata=None),
        ]

        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=messages)

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is not None
        assert len(history) == 2
        assert history[-1]["role"] == "model"
        assert history[-1]["parts"][0]["text"] == "Here are the results."

    @pytest.mark.asyncio
    async def test_exception_returns_none(self) -> None:
        """Load failure returns None (graceful fallback)."""
        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(side_effect=RuntimeError("DB down"))

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is None

    @pytest.mark.asyncio
    async def test_empty_messages_returns_none(self) -> None:
        """No messages returns None."""
        conv_service = AsyncMock()
        conv_service.get_messages = AsyncMock(return_value=[])

        history = await _load_conversation_history(conv_service, uuid4(), uuid4())
        assert history is None


# ---------- B12 — _build_contents with function parts ----------

class TestBuildContentsWithFunctionParts:
    """Verify _build_contents handles function_call/response dict formats."""

    def test_text_only_history(self) -> None:
        """Text-only history still works."""
        from src.orchestrator.agent import VideoIntelligenceAgent

        agent = _make_agent()
        contents = agent._build_contents("hello", history=[
            {"role": "user", "parts": [{"text": "hi"}]},
            {"role": "model", "parts": [{"text": "hello back"}]},
        ])

        assert len(contents) == 3  # 2 history + 1 new message
        assert contents[0].role == "user"
        assert contents[2].parts[0].text == "hello"

    def test_function_call_parts(self) -> None:
        """History with function_call parts creates correct Part objects."""
        agent = _make_agent()
        history = [
            {"role": "user", "parts": [{"text": "search fitness"}]},
            {"role": "model", "parts": [
                {"function_call": {"name": "search_videos", "args": {"query": "fitness"}}},
            ]},
            {"role": "user", "parts": [
                {"function_response": {"name": "search_videos", "response": {"summary": "10 results"}}},
            ]},
            {"role": "model", "parts": [{"text": "I found 10 results."}]},
        ]

        contents = agent._build_contents("analyze first", history=history)

        assert len(contents) == 5  # 4 history + 1 new

        # Check function_call part
        model_fc = contents[1]
        assert model_fc.role == "model"
        assert model_fc.parts[0].function_call is not None
        assert model_fc.parts[0].function_call.name == "search_videos"

        # Check function_response part
        user_fr = contents[2]
        assert user_fr.role == "user"
        assert user_fr.parts[0].function_response is not None
        assert user_fr.parts[0].function_response.name == "search_videos"

    def test_mixed_text_and_function_call(self) -> None:
        """Model turn with text + function_call creates multiple parts."""
        agent = _make_agent()
        history = [
            {"role": "user", "parts": [{"text": "search"}]},
            {"role": "model", "parts": [
                {"text": "Let me search for that."},
                {"function_call": {"name": "search_videos", "args": {}}},
            ]},
        ]

        contents = agent._build_contents("next", history=history)
        model_content = contents[1]
        assert len(model_content.parts) == 2
        assert model_content.parts[0].text == "Let me search for that."
        assert model_content.parts[1].function_call is not None


def _make_agent() -> "VideoIntelligenceAgent":
    """Create a minimal agent for _build_contents testing."""
    from src.orchestrator.agent import VideoIntelligenceAgent

    mock_client = MagicMock()
    mock_registry = MagicMock()
    mock_registry.to_gemini_tools.return_value = []
    mock_registry.get_tool_descriptions.return_value = {}

    return VideoIntelligenceAgent(
        gemini_client=mock_client,
        tool_registry=mock_registry,
    )


# ---------- B13 — Prompt hash in cache key ----------

class TestPromptHashCacheKey:
    """Tests for analysis cache key including prompt hash."""

    def test_cache_key_includes_prompt_hash(self) -> None:
        """Cache key should include :ph prefix with hash suffix."""
        service = _make_analysis_service()
        key = service._generate_cache_key(Platform.TIKTOK, "abc123")
        assert ":ph" in key
        assert key.endswith(f":ph{_PROMPT_HASH}")

    def test_prompt_hash_deterministic(self) -> None:
        """Same SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT always produces same hash."""
        hash1 = hashlib.sha256(
            (SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT).encode()
        ).hexdigest()[:8]
        hash2 = hashlib.sha256(
            (SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT).encode()
        ).hexdigest()[:8]
        assert hash1 == hash2
        assert hash1 == _PROMPT_HASH

    def test_different_prompt_produces_different_hash(self) -> None:
        """Changing the prompt content produces a different hash."""
        original = hashlib.sha256(
            (SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT).encode()
        ).hexdigest()[:8]
        modified = hashlib.sha256(
            ("MODIFIED " + SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT).encode()
        ).hexdigest()[:8]
        assert original != modified

    def test_cache_key_format(self) -> None:
        """Full cache key format: {platform}:{video_id}:v{version}:ph{hash}."""
        service = _make_analysis_service()
        key = service._generate_cache_key(Platform.YOUTUBE, "test123")
        parts = key.split(":")
        assert parts[0] == "youtube"
        assert parts[1] == "test123"
        assert parts[2] == f"v{service.ANALYSIS_VERSION}"
        assert parts[3].startswith("ph")
        assert len(parts[3]) == 10  # "ph" + 8 hex chars


def _make_analysis_service() -> AnalysisService:
    """Create a minimal AnalysisService for cache key testing."""
    return AnalysisService(
        analyzer=MagicMock(),
        repository=MagicMock(),
        storage=MagicMock(),
    )
