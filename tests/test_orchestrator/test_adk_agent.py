"""Tests for ADK-based agent orchestrator (PR-090).

Tests the ADK tool adapter, agent wrapper, and feature flag integration.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.billing.tiers import Tier
from src.orchestrator.adk_agent import AdkAgentWrapper
from src.orchestrator.config import AgentSettings
from src.orchestrator.tools import ToolDefinition, ToolRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dummy_handler():
    """A simple async handler for test tools."""
    async def handler(**kwargs) -> dict[str, Any]:
        return {"summary": "ok", "result": kwargs}
    return handler


@pytest.fixture
def user_id_handler():
    """Handler that expects user_id."""
    async def handler(user_id: str = "", **kwargs) -> dict[str, Any]:
        return {"summary": "ok", "user_id": user_id, **kwargs}
    return handler


@pytest.fixture
def error_handler():
    """Handler that returns an error."""
    async def handler(**kwargs) -> dict[str, Any]:
        return {"error": "something_broke", "summary": "Failed"}
    return handler


@pytest.fixture
def registry(dummy_handler, user_id_handler):
    """Registry with a mix of test tools."""
    r = ToolRegistry()
    r.register(ToolDefinition(
        name="search_content",
        description="Search for content",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=dummy_handler,
    ))
    r.register(ToolDefinition(
        name="analyze_video",
        description="Analyze a video",
        parameters={
            "video_id": {"type": "string"},
            "platform": {"type": "string"},
        },
        required_params=["video_id", "platform"],
        handler=user_id_handler,
        min_tier=Tier.PRO,
    ))
    r.register(ToolDefinition(
        name="check_usage",
        description="Check usage",
        parameters={},
        required_params=[],
        handler=dummy_handler,
    ))
    return r


# ---------------------------------------------------------------------------
# Phase 1: ADK tool adapter tests
# ---------------------------------------------------------------------------

class TestToAdkTools:
    """Tests for ToolRegistry.to_adk_tools()."""

    def test_adk_tools_count_matches_gemini_tools(self, registry):
        """to_adk_tools() produces same count as to_gemini_tools()."""
        gemini_tools = registry.to_gemini_tools()
        adk_tools = registry.to_adk_tools()

        gemini_count = len(gemini_tools[0].function_declarations)
        assert len(adk_tools) == gemini_count

    def test_adk_tool_names_match(self, registry):
        """ADK tool names match the registered tool names."""
        adk_tools = registry.to_adk_tools()
        names = {t.name for t in adk_tools}
        assert names == {"search_content", "analyze_video", "check_usage"}

    def test_adk_tool_has_correct_schema(self, registry):
        """ADK tool declarations have correct JSON Schema."""
        adk_tools = registry.to_adk_tools()
        search_tool = next(t for t in adk_tools if t.name == "search_content")
        decl = search_tool._get_declaration()

        assert decl.name == "search_content"
        assert decl.description == "Search for content"
        schema = decl.parameters_json_schema
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert schema["required"] == ["query"]

    def test_adk_tool_with_no_params(self, registry):
        """Tools with no parameters produce valid schema."""
        adk_tools = registry.to_adk_tools()
        usage_tool = next(t for t in adk_tools if t.name == "check_usage")
        decl = usage_tool._get_declaration()

        assert decl.parameters_json_schema["properties"] == {}
        assert decl.parameters_json_schema["required"] == []

    @pytest.mark.asyncio
    async def test_adk_tool_calls_registry_execute(self, registry):
        """ADK tool run_async delegates to ToolRegistry.execute()."""
        from google.adk.tools.tool_context import ToolContext

        adk_tools = registry.to_adk_tools()
        search_tool = next(t for t in adk_tools if t.name == "search_content")

        # Mock ToolContext with state
        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": None, "temp:user_tier": Tier.FREE}

        result = await search_tool.run_async(
            args={"query": "test query"},
            tool_context=mock_ctx,
        )

        assert result["summary"] == "ok"
        assert result["result"]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_adk_tool_injects_user_id(self, registry):
        """ADK tool injects user_id for tools in _USER_ID_TOOLS."""
        from google.adk.tools.tool_context import ToolContext

        uid = uuid4()
        user_id_tools = frozenset({"analyze_video"})
        adk_tools = registry.to_adk_tools(user_id_tools=user_id_tools)
        analyze_tool = next(t for t in adk_tools if t.name == "analyze_video")

        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": uid, "temp:user_tier": Tier.PRO}

        result = await analyze_tool.run_async(
            args={"video_id": "abc123", "platform": "tiktok"},
            tool_context=mock_ctx,
        )

        # user_id should have been injected into handler args
        assert result["user_id"] == str(uid)

    @pytest.mark.asyncio
    async def test_adk_tool_no_user_id_when_not_in_set(self, registry):
        """ADK tool does NOT inject user_id for tools not in _USER_ID_TOOLS."""
        from google.adk.tools.tool_context import ToolContext

        uid = uuid4()
        user_id_tools = frozenset({"analyze_video"})  # search_content NOT in set
        adk_tools = registry.to_adk_tools(user_id_tools=user_id_tools)
        search_tool = next(t for t in adk_tools if t.name == "search_content")

        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": uid, "temp:user_tier": Tier.FREE}

        result = await search_tool.run_async(
            args={"query": "test"},
            tool_context=mock_ctx,
        )

        # user_id should NOT be in the result args
        assert "user_id" not in result.get("result", {})

    @pytest.mark.asyncio
    async def test_adk_tool_tier_gating(self, registry):
        """Pro-only tools return tier_restricted for free tier users."""
        from google.adk.tools.tool_context import ToolContext

        adk_tools = registry.to_adk_tools()
        analyze_tool = next(t for t in adk_tools if t.name == "analyze_video")

        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": uuid4(), "temp:user_tier": Tier.FREE}

        result = await analyze_tool.run_async(
            args={"video_id": "abc", "platform": "tiktok"},
            tool_context=mock_ctx,
        )

        assert result["error"] == "tier_restricted"

    @pytest.mark.asyncio
    async def test_adk_tool_sanitizes_unknown_errors(self):
        """Unknown error codes are sanitized to internal_error."""
        from google.adk.tools.tool_context import ToolContext

        async def bad_handler(**kwargs) -> dict[str, Any]:
            return {"error": "some_internal_code", "summary": "internal details"}

        r = ToolRegistry()
        r.register(ToolDefinition(
            name="bad_tool",
            description="A tool that errors",
            parameters={"q": {"type": "string"}},
            required_params=["q"],
            handler=bad_handler,
        ))
        adk_tools = r.to_adk_tools()
        tool = adk_tools[0]

        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": None, "temp:user_tier": Tier.FREE}

        result = await tool.run_async(args={"q": "test"}, tool_context=mock_ctx)

        assert result["error"] == "internal_error"
        assert result["summary"] == "Tool bad_tool encountered an error"
        assert "internal details" not in str(result)

    @pytest.mark.asyncio
    async def test_adk_tool_strips_heavy_payload(self):
        """Heavy payloads are stripped when digest key is present."""
        from google.adk.tools.tool_context import ToolContext

        async def heavy_handler(**kwargs) -> dict[str, Any]:
            return {
                "digest": "summary",
                "results": [1, 2, 3],
                "top_items": [4, 5],
                "summary": "ok",
            }

        r = ToolRegistry()
        r.register(ToolDefinition(
            name="heavy_tool",
            description="A tool with heavy output",
            parameters={"q": {"type": "string"}},
            required_params=["q"],
            handler=heavy_handler,
        ))
        adk_tools = r.to_adk_tools()
        tool = adk_tools[0]

        mock_ctx = MagicMock(spec=ToolContext)
        mock_ctx.state = {"temp:user_id": None, "temp:user_tier": Tier.FREE}

        result = await tool.run_async(args={"q": "test"}, tool_context=mock_ctx)

        assert result["digest"] == "summary"
        assert result["summary"] == "ok"
        assert "results" not in result
        assert "top_items" not in result


# ---------------------------------------------------------------------------
# Phase 2: AgentSettings.use_adk flag tests
# ---------------------------------------------------------------------------

class TestAgentSettingsAdkFlag:
    """Tests for the AGENT_USE_ADK feature flag."""

    def test_default_is_true(self):
        settings = AgentSettings()
        assert settings.use_adk is True

    def test_can_enable(self):
        settings = AgentSettings(use_adk=True)
        assert settings.use_adk is True

    def test_repr_includes_use_adk(self):
        settings = AgentSettings(use_adk=True)
        assert "use_adk=True" in repr(settings)


# ---------------------------------------------------------------------------
# Phase 2-3: AdkAgentWrapper tests
# ---------------------------------------------------------------------------

class TestAdkAgentWrapper:
    """Tests for the ADK agent wrapper."""

    @pytest.fixture
    def mock_gemini_client(self):
        return MagicMock()

    @pytest.fixture
    def wrapper(self, mock_gemini_client, registry):
        return AdkAgentWrapper(
            gemini_client=mock_gemini_client,
            tool_registry=registry,
            config=AgentSettings(use_adk=True, overall_timeout_seconds=60),
            conversation_id=uuid4(),
            user_tier=Tier.PRO,
        )

    def test_wrapper_creates_adk_agent(self, wrapper):
        """Wrapper creates an ADK Agent with correct config."""
        agent = wrapper._create_adk_agent()
        assert agent.name == "freddy"
        assert agent.model == wrapper._config.model
        assert agent.instruction == wrapper._system_prompt
        assert len(agent.tools) > 0

    def test_wrapper_has_same_interface(self, wrapper):
        """Wrapper has chat() and stream_chat() methods."""
        assert hasattr(wrapper, "chat")
        assert hasattr(wrapper, "stream_chat")
        assert asyncio.iscoroutinefunction(wrapper.chat)

    def test_adk_tools_set_from_legacy_agent(self, wrapper):
        """Wrapper's _user_id_tools is populated from VideoIntelligenceAgent."""
        assert isinstance(wrapper._user_id_tools, frozenset)
        assert "analyze_video" in wrapper._user_id_tools
