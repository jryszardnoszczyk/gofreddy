"""Agent + ToolRegistry wiring integration tests.

All tests use real Gemini + real services via build_default_registry.
They verify the full pipeline: natural language prompt → real Gemini reasoning →
real tool calls → real service execution → final answer.

Markers:
    @pytest.mark.gemini — requires real Gemini API key
    @pytest.mark.external_api — hits external platform APIs
    @pytest.mark.db — requires real PostgreSQL
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from src.orchestrator.agent import VideoIntelligenceAgent
from src.orchestrator.config import AgentSettings
from src.orchestrator.models import AgentResponse
from src.orchestrator.tools import build_default_registry
from tests.fixtures.stable_ids import YOUTUBE_VIDEO_ID


# ── Real-Service Fixtures ────────────────────────────────────


@pytest_asyncio.fixture
async def search_registry(search_service):
    """Registry with real search tool."""
    registry, _ = build_default_registry(search_service=search_service)
    return registry


@pytest_asyncio.fixture
async def search_and_analysis_registry(
    search_service, analysis_service, r2_storage,
):
    """Registry with real search + analysis tools."""
    registry, _ = build_default_registry(
        search_service=search_service,
        analysis_service=analysis_service,
        video_storage=r2_storage,
    )
    return registry


@pytest_asyncio.fixture
async def wiring_agent(gemini_client, search_registry):
    """Real agent with real Gemini + search tool."""
    config = AgentSettings(max_loop_iterations=3, cost_limit_usd=0.10)
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=search_registry,
        config=config,
    )


@pytest_asyncio.fixture
async def multi_tool_agent(gemini_client, search_and_analysis_registry):
    """Real agent with real Gemini + search + analysis tools."""
    config = AgentSettings(max_loop_iterations=5, cost_limit_usd=0.50)
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=search_and_analysis_registry,
        config=config,
    )


# ── Single Tool Call Flow (Real Gemini) ──────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestSingleToolWiring:
    async def test_search_tool_wiring(self, wiring_agent):
        """Real Gemini calls search_videos → real service.search() → final text."""
        result = await wiring_agent.chat("Find cooking videos on TikTok")

        assert isinstance(result, AgentResponse)
        assert result.gemini_calls >= 2  # tool call + final answer
        assert len(result.actions_taken) >= 1
        assert any("search_videos" in a for a in result.actions_taken)
        assert result.text  # Non-empty response

    @pytest.mark.db
    async def test_analyze_tool_wiring(
        self, multi_tool_agent, youtube_video_in_r2,
    ):
        """Real Gemini calls analyze_video → real analysis_service → final text."""
        result = await multi_tool_agent.chat(
            f"Analyze the YouTube video with ID {YOUTUBE_VIDEO_ID} for content safety"
        )

        assert isinstance(result, AgentResponse)
        assert any("analyze_video" in a for a in result.actions_taken)
        assert result.text


# ── Multi-Tool Flow (Real Gemini) ────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestMultiToolWiring:
    async def test_multi_tool_calls(
        self, multi_tool_agent, youtube_video_in_r2,
    ):
        """Real Gemini chains search + analyze across turns."""
        result = await multi_tool_agent.chat(
            f"Search for YouTube videos about 'me at the zoo', "
            f"then analyze the YouTube video {YOUTUBE_VIDEO_ID} for content safety"
        )

        assert result.gemini_calls >= 2
        tool_names = [tr["tool"] for tr in result.tool_results]
        assert len(tool_names) >= 1
        assert result.text


# ── Streaming + Tools (Real Gemini) ──────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestStreamingWithTools:
    async def test_streaming_yields_tool_events(self, wiring_agent):
        """Real stream_chat yields tool_call, tool_result, and done events."""
        events = []
        async for event_type, data in wiring_agent.stream_chat("Find cooking videos"):
            events.append((event_type, data))

        event_types = [e[0] for e in events]
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "done" in event_types

        # Verify tool_call event has expected shape
        tool_calls = [(t, d) for t, d in events if t == "tool_call"]
        assert tool_calls[0][1]["tool"] == "search_videos"

        # Verify done event has expected fields
        done_events = [(t, d) for t, d in events if t == "done"]
        assert done_events[0][1]["finish_reason"] in (
            "complete", "budget_exceeded", "max_iterations",
        )
        assert "cost_usd" in done_events[0][1]
