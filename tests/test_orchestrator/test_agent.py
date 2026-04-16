"""Tests for CostTracker, VideoIntelligenceAgent, and _execute_tool.

CostTracker tests are pure math (no external services).
All other tests use real Gemini + real services.

Markers:
    @pytest.mark.gemini — requires real Gemini API key
    @pytest.mark.external_api — hits external platform APIs
    @pytest.mark.db — requires real PostgreSQL
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio

from src.orchestrator.agent import CostTracker, VideoIntelligenceAgent, _MAX_HISTORY_PAIRS, _prepare_for_llm
from src.orchestrator.config import AgentSettings
from src.orchestrator.models import AgentResponse
from src.orchestrator.tools import ToolDefinition, ToolRegistry, build_default_registry


# ── Real-Service Fixtures ────────────────────────────────────


@pytest_asyncio.fixture
async def real_search_registry(search_service):
    """Registry with real search tool for agent tests."""
    registry, _ = build_default_registry(search_service=search_service)
    return registry


@pytest_asyncio.fixture
async def real_agent(gemini_client, real_search_registry):
    """Real agent with real Gemini + real search tool."""
    config = AgentSettings(max_loop_iterations=3, cost_limit_usd=0.10)
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=real_search_registry,
        config=config,
    )


# ── CostTracker Tests (Pure Math) ────────────────────────────


class TestCostTracker:
    def test_record_response_splits_input_output_tokens(self):
        """Verify prompt_token_count and candidates_token_count tracked separately."""
        cost = CostTracker()
        response = SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=100, candidates_token_count=50),
        )
        cost.record_response(response)

        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_tokens == 150
        assert cost.gemini_calls == 1

    def test_record_response_handles_missing_metadata(self):
        """No crash on None usage_metadata."""
        cost = CostTracker()
        response = SimpleNamespace(usage_metadata=None)
        cost.record_response(response)

        assert cost.total_tokens == 0
        assert cost.gemini_calls == 1

    def test_record_downstream_cost_from_flat_dict(self):
        """Verify reads cost_usd at top level."""
        cost = CostTracker()
        cost.record_downstream_cost({"cost_usd": 0.005, "summary": "done"})

        assert cost._downstream_usd == pytest.approx(0.005)

    def test_record_downstream_cost_from_cost_cents(self):
        """Verify cost_cents / 100 conversion."""
        cost = CostTracker()
        cost.record_downstream_cost({"cost_cents": 50, "summary": "done"})

        assert cost._downstream_usd == pytest.approx(0.50)

    def test_estimated_cost_uses_split_rates(self):
        """Input at $0.50/M + output at $3.00/M + downstream."""
        cost = CostTracker(input_rate_per_million=0.50, output_rate_per_million=3.00)
        response = SimpleNamespace(
            usage_metadata=SimpleNamespace(prompt_token_count=1_000_000, candidates_token_count=100_000),
        )
        cost.record_response(response)
        cost.record_downstream_cost({"cost_usd": 0.1})

        # 1M input * $0.50/M + 100K output * $3.00/M + $0.10 downstream
        # = $0.50 + $0.30 + $0.10 = $0.90
        assert cost.estimated_cost_usd == pytest.approx(0.90)

    def test_default_rates_match_gemini_3_flash(self):
        """Default rates should be Gemini 3 Flash pricing."""
        cost = CostTracker()
        assert cost._input_rate == 0.50
        assert cost._output_rate == 3.00


# ── _prepare_for_llm Tests ─────────────────────────────────────


class TestPrepareForLlm:
    def test_with_digest_strips_results_and_top_items(self):
        """When digest is present, results/top_items/canvas_results/stats are stripped."""
        data = {
            "summary": "Found 19 videos",
            "digest": {"total": 19, "platform_breakdown": {"tiktok": 10}},
            "results": [{"video_id": "a"}, {"video_id": "b"}],
            "top_items": [{"id": "1"}],
            "canvas_results": [{"id": "2"}],
            "stats": {"view_distribution": {}},
            "workspace": {"action": "created"},
            "expansion": {"has_more": True},
        }
        out = _prepare_for_llm(data)
        assert "digest" in out
        assert "results" not in out
        assert "top_items" not in out
        assert "canvas_results" not in out
        assert "stats" not in out
        assert "workspace" not in out
        assert out["summary"] == "Found 19 videos"
        assert out["expansion"] == {"has_more": True}

    def test_without_digest_preserves_results(self):
        """When no digest, only workspace is stripped."""
        data = {
            "summary": "Analysis complete",
            "results": {"score": 95},
            "workspace": {"action": "stored"},
        }
        out = _prepare_for_llm(data)
        assert out["results"] == {"score": 95}
        assert "workspace" not in out

    def test_never_mutates_input(self):
        """Input dict must not be modified."""
        data = {
            "summary": "test",
            "digest": {"total": 5},
            "results": [1, 2, 3],
            "workspace": {"action": "x"},
        }
        original_keys = set(data.keys())
        _prepare_for_llm(data)
        assert set(data.keys()) == original_keys
        assert data["results"] == [1, 2, 3]

    def test_passthrough_small_results(self):
        """Small results without digest pass through (minus workspace)."""
        data = {"summary": "ok", "results": [1]}
        out = _prepare_for_llm(data)
        assert out == {"summary": "ok", "results": [1]}


# ── _build_contents Sliding Window Tests ──────────────────────


class TestBuildContents:
    """Tests for history sliding window in _build_contents(). Pure unit tests."""

    def _make_agent(self):
        """Minimal agent for _build_contents testing (Gemini not called)."""
        registry = ToolRegistry()
        return VideoIntelligenceAgent(
            gemini_client=SimpleNamespace(),  # Not called
            tool_registry=registry,
        )

    def test_build_contents_sliding_window_truncates(self):
        """60 history entries → only last 40 kept."""
        agent = self._make_agent()
        history = [
            {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg {i}"}]}
            for i in range(60)
        ]
        contents = agent._build_contents("new message", history=history)
        # 40 from truncated history + 1 for current message
        assert len(contents) == _MAX_HISTORY_PAIRS * 2 + 1

    def test_build_contents_under_limit_no_truncation(self):
        """10 entries → all preserved."""
        agent = self._make_agent()
        history = [
            {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg {i}"}]}
            for i in range(10)
        ]
        contents = agent._build_contents("new message", history=history)
        assert len(contents) == 11  # 10 history + 1 current

    def test_build_contents_exact_boundary(self):
        """Exactly 40 entries → all preserved (no off-by-one)."""
        agent = self._make_agent()
        history = [
            {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg {i}"}]}
            for i in range(_MAX_HISTORY_PAIRS * 2)
        ]
        contents = agent._build_contents("new message", history=history)
        assert len(contents) == _MAX_HISTORY_PAIRS * 2 + 1

    def test_build_contents_empty_history(self):
        """None and [] → only user message in output."""
        agent = self._make_agent()
        contents_none = agent._build_contents("hello", history=None)
        contents_empty = agent._build_contents("hello", history=[])
        assert len(contents_none) == 1
        assert len(contents_empty) == 1
        assert contents_none[0].role == "user"

    def test_build_contents_odd_length_drops_model_first(self):
        """41 entries starting with model after slice → first model entry dropped."""
        agent = self._make_agent()
        # Create 41 entries where after truncation the first would be model
        history = [
            {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg {i}"}]}
            for i in range(41)
        ]
        # After slicing last 40 from 41, entry at index 1 (model) becomes first
        contents = agent._build_contents("new message", history=history)
        # First content should be user (the current message is appended last)
        assert contents[0].role == "user"


# ── Agent Chat Tests (Real Gemini) ───────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestAgentChat:
    """Agent chat tests with real Gemini + real services."""

    async def test_chat_returns_text_on_no_function_calls(self, real_agent):
        """Simple question → text-only response, no tool calls."""
        result = await real_agent.chat("What can you help me with?")

        assert isinstance(result, AgentResponse)
        assert result.text
        assert result.gemini_calls >= 1

    async def test_chat_executes_tool_and_feeds_back(self, real_agent):
        """Search request → real search tool called → coherent final text."""
        result = await real_agent.chat("Find cooking videos on TikTok")

        assert isinstance(result, AgentResponse)
        assert any("search_videos" in a for a in result.actions_taken)
        assert result.text
        assert result.gemini_calls >= 2

    async def test_chat_with_history(self, real_agent):
        """History entries prepended → agent uses context."""
        history = [
            {"role": "user", "parts": [{"text": "I'm interested in fitness videos"}]},
            {"role": "model", "parts": [{"text": "I can help you find fitness content!"}]},
        ]
        result = await real_agent.chat(
            "Search for what I'm interested in", history=history,
        )

        assert isinstance(result, AgentResponse)
        assert result.text
        assert result.gemini_calls >= 1

    async def test_budget_prevents_runaway(self, gemini_client, real_search_registry):
        """Very low budget should stop the agent early."""
        config = AgentSettings(max_loop_iterations=10, cost_limit_usd=0.01)
        agent = VideoIntelligenceAgent(
            gemini_client=gemini_client,
            tool_registry=real_search_registry,
            config=config,
        )

        result = await agent.chat("Search for 50 different types of videos")

        assert isinstance(result, AgentResponse)
        # Should have stopped due to budget (not run all 10 iterations)
        assert result.gemini_calls < 10


# ── _execute_tool Tests (Real Search Service) ────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestExecuteToolWithRealSearch:
    """_execute_tool tests that call real search service."""

    async def test_strips_unexpected_args(self, gemini_client, search_service):
        """Only schema params passed — LLM-injected args stripped."""
        registry, _ = build_default_registry(search_service=search_service)
        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)

        part = SimpleNamespace(
            function_call=SimpleNamespace(
                name="search_videos",
                args={"query": "test", "injected_param": "malicious"},
            ),
        )
        _name, args, _result = await agent._execute_tool(part, None)

        assert "injected_param" not in args
        assert "query" in args

    async def test_no_user_id_for_search(self, gemini_client, search_service):
        """user_id NOT injected for search_videos."""
        registry, _ = build_default_registry(search_service=search_service)
        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        user_id = uuid4()

        part = SimpleNamespace(
            function_call=SimpleNamespace(name="search_videos", args={"query": "test"}),
        )
        _name, args, _result = await agent._execute_tool(part, user_id)

        assert "user_id" not in args


# ── _execute_tool Tests (Internal Wiring) ────────────────────


class TestExecuteToolInternal:
    """_execute_tool tests for user_id injection, error sanitization, and timeout.

    Uses real ToolRegistry with simple handler functions (not mocks).
    gemini_client is passed to the constructor but not called.
    """

    async def test_injects_user_id_for_creator_profile(self, gemini_client):
        """creator_profile receives user_id via forced override (stories absorbed)."""
        async def handler(**kwargs):
            return {"summary": "captured", "received_user_id": kwargs.get("user_id")}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="creator_profile",
            description="Creator profile with stories",
            parameters={
                "platform": {"type": "string"},
                "username": {"type": "string"},
                "action": {"type": "string"},
                "user_id": {"type": "string"},
            },
            required_params=["platform", "username"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        user_id = uuid4()

        part = SimpleNamespace(
            function_call=SimpleNamespace(
                name="creator_profile",
                args={"platform": "instagram", "username": "testuser", "action": "capture_stories"},
            ),
        )
        _name, args, _result = await agent._execute_tool(part, user_id)

        assert args.get("user_id") == str(user_id)

    async def test_injects_user_id_for_analyze_video(self, gemini_client):
        """analyze_video receives user_id via forced override (deepfake absorbed)."""
        async def handler(**kwargs):
            return {"summary": "analyzed"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="analyze_video",
            description="Analyze video",
            parameters={
                "platform": {"type": "string"},
                "video_id": {"type": "string"},
                "action": {"type": "string"},
                "user_id": {"type": "string"},
            },
            required_params=["platform", "video_id"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        user_id = uuid4()

        part = SimpleNamespace(
            function_call=SimpleNamespace(
                name="analyze_video",
                args={"platform": "youtube", "video_id": "abc"},
            ),
        )
        _name, args, _result = await agent._execute_tool(part, user_id)

        assert args.get("user_id") == str(user_id)

    async def test_sanitizes_error_messages(self, gemini_client):
        """Error messages sanitized before feeding to Gemini."""
        async def failing_handler(**kwargs):
            raise RuntimeError("Connection to postgres://secret:password@db:5432 failed")

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="failing_tool",
            description="A tool that fails",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=failing_handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)

        part = SimpleNamespace(
            function_call=SimpleNamespace(name="failing_tool", args={"query": "test"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        # Error should be sanitized — no connection strings exposed
        assert "postgres" not in str(result)
        assert "password" not in str(result)
        assert result["error"] == "internal_error"

    async def test_execute_tool_timeout(self, gemini_client):
        """Per-tool timeout returns error dict."""
        async def slow_handler(**kwargs):
            await asyncio.sleep(100)
            return {"summary": "never"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="slow_tool",
            description="A slow tool",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=slow_handler,
            timeout_seconds=1,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)

        part = SimpleNamespace(
            function_call=SimpleNamespace(name="slow_tool", args={"query": "test"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result.get("error") == "timeout"


# ── Streaming Tests (Real Gemini) ─────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestStreamingLoop:
    """Streaming tests with real Gemini."""

    async def test_streaming_loop_yields_done_on_completion(self, real_agent):
        """Last event is always done with finish_reason."""
        events = []
        async for event_type, data in real_agent.stream_chat("What can you help me with?"):
            events.append((event_type, data))

        assert len(events) >= 1
        last = events[-1]
        assert last[0] == "done"
        assert last[1]["finish_reason"] in ("complete", "budget_exceeded", "max_iterations")
        assert "cost_usd" in last[1]

    async def test_streaming_with_tool_calls(self, real_agent):
        """Stream yields tool_call, tool_result, and done events."""
        events = []
        async for event_type, data in real_agent.stream_chat("Find cooking videos"):
            events.append((event_type, data))

        event_types = [e[0] for e in events]
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "done" in event_types

    async def test_chat_unchanged_after_streaming_addition(self, real_agent):
        """Backwards compatibility: chat() still returns AgentResponse."""
        result = await real_agent.chat("What can you help me with?")

        assert isinstance(result, AgentResponse)
        assert result.text


# ── PR-034: Error Passthrough Whitelist Tests ─────────────────


class TestErrorPassthrough:
    """Whitelisted error codes pass through to LLM; unknown errors are sanitized."""

    async def test_whitelisted_error_passes_through(self, gemini_client):
        """batch_limit_exceeded error passes through without sanitization."""
        async def handler(**kwargs):
            return {
                "summary": "Batch limit exceeded: requested 50 items, max is 5 on your tier",
                "error": "batch_limit_exceeded",
                "limit": 5,
                "requested": 50,
            }

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="analyze_batch",
            description="Batch analysis",
            parameters={"collection_id": {"type": "string"}},
            required_params=["collection_id"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        part = SimpleNamespace(
            function_call=SimpleNamespace(name="analyze_batch", args={"collection_id": "abc"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result["error"] == "batch_limit_exceeded"
        assert result["limit"] == 5
        assert result["requested"] == 50
        assert "Batch limit exceeded" in result["summary"]

    async def test_providers_unavailable_passes_through(self, gemini_client):
        """providers_unavailable error passes through."""
        async def handler(**kwargs):
            return {"summary": "All providers are down", "error": "providers_unavailable"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="detect_deepfake",
            description="Deepfake detection",
            parameters={"video_id": {"type": "string"}, "user_id": {"type": "string"}},
            required_params=["video_id"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        part = SimpleNamespace(
            function_call=SimpleNamespace(name="detect_deepfake", args={"video_id": "abc"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result["error"] == "providers_unavailable"
        assert result["summary"] == "All providers are down"

    async def test_unknown_error_sanitized(self, gemini_client):
        """Unknown error code is sanitized to internal_error."""
        async def handler(**kwargs):
            return {"summary": "SECRET DB info leaked", "error": "database_connection_failed"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="some_tool",
            description="A tool",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        part = SimpleNamespace(
            function_call=SimpleNamespace(name="some_tool", args={"query": "test"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result["error"] == "internal_error"
        assert "SECRET" not in result["summary"]

    async def test_tier_required_passes_through(self, gemini_client):
        """tier_required error passes through."""
        async def handler(**kwargs):
            return {"summary": "Pro tier required", "error": "tier_required", "required_tier": "pro"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="detect_deepfake",
            description="Deepfake detection",
            parameters={"video_id": {"type": "string"}, "user_id": {"type": "string"}},
            required_params=["video_id"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        part = SimpleNamespace(
            function_call=SimpleNamespace(name="detect_deepfake", args={"video_id": "abc"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result["error"] == "tier_required"
        assert result["required_tier"] == "pro"

    async def test_daily_limit_reached_passes_through(self, gemini_client):
        """daily_limit_reached error passes through."""
        async def handler(**kwargs):
            return {"summary": "Daily limit reached", "error": "daily_limit_reached"}

        registry = ToolRegistry()
        registry.register(ToolDefinition(
            name="some_tool",
            description="A tool",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=handler,
        ))

        agent = VideoIntelligenceAgent(gemini_client=gemini_client, tool_registry=registry)
        part = SimpleNamespace(
            function_call=SimpleNamespace(name="some_tool", args={"query": "test"}),
        )
        _name, _args, result = await agent._execute_tool(part, None)

        assert result["error"] == "daily_limit_reached"
