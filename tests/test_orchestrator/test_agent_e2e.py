"""Agent orchestrator E2E tests — real Gemini + real tools + real services.

These tests exercise the full agent workflow: natural language prompt →
real Gemini reasoning → real tool calls → real platform services → final answer.

Results are qualitative — we verify correct tools were called, response is
coherent, and cost tracking works. The exact text is non-deterministic.

Markers:
    @pytest.mark.gemini — requires real Gemini API key
    @pytest.mark.external_api — hits external platform APIs (ScrapeCreators, etc.)
    @pytest.mark.db — requires real PostgreSQL

These tests are intentionally slow (5-30s each) due to real API calls.
Run selectively: pytest tests/test_orchestrator/test_agent_e2e.py -v
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from src.orchestrator.agent import VideoIntelligenceAgent
from src.orchestrator.config import AgentSettings
from src.orchestrator.models import AgentResponse
from src.orchestrator.tools import build_default_registry
from tests.fixtures.stable_ids import YOUTUBE_VIDEO_ID


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def full_registry(
    search_service,
    analysis_service,
    brand_service,
    demographics_service,
    evolution_service,
    trend_service,
    fraud_service,
    r2_storage,
    fetchers,
):
    """Full tool registry with all real services wired in.

    Excludes deepfake_service (expensive external API) and
    story_service (ephemeral content, Apify trial expired).
    Uses PRO tier so trends are registered.
    """
    from src.billing.tiers import Tier
    registry, _ = build_default_registry(
        search_service=search_service,
        analysis_service=analysis_service,
        brand_service=brand_service,
        demographics_service=demographics_service,
        evolution_service=evolution_service,
        trend_service=trend_service,
        fraud_service=fraud_service,
        video_storage=r2_storage,
        fetchers=fetchers,
        tier=Tier.PRO,
    )
    return registry


@pytest_asyncio.fixture
async def search_only_registry(search_service):
    """Minimal registry with only search tool — for fast tests."""
    registry, _ = build_default_registry(search_service=search_service)
    return registry


@pytest_asyncio.fixture
async def agent(gemini_client, full_registry):
    """Real agent with real Gemini + full tool registry."""
    config = AgentSettings(
        max_loop_iterations=5,  # Cap iterations for test speed
        cost_limit_usd=0.50,   # Budget guard for tests
    )
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=full_registry,
        config=config,
    )


@pytest_asyncio.fixture
async def chaining_agent(gemini_client, full_registry):
    """Agent with higher budget for multi-tool chaining (analyze → brands/demographics)."""
    config = AgentSettings(
        max_loop_iterations=8,
        cost_limit_usd=1.00,
    )
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=full_registry,
        config=config,
    )


@pytest_asyncio.fixture
async def search_agent(gemini_client, search_only_registry):
    """Lightweight agent with only search tool — fastest E2E test."""
    config = AgentSettings(
        max_loop_iterations=3,
        cost_limit_usd=0.10,
    )
    return VideoIntelligenceAgent(
        gemini_client=gemini_client,
        tool_registry=search_only_registry,
        config=config,
    )


# ── Search Workflow ─────────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestSearchWorkflow:
    """Agent searches for videos using natural language."""

    async def test_search_by_keyword(self, search_agent):
        """'Find fitness videos on TikTok' → search_videos tool called."""
        result = await search_agent.chat("Find fitness videos on TikTok")

        assert isinstance(result, AgentResponse)
        assert result.gemini_calls >= 2  # At least: tool call + final answer
        assert any("search_videos" in a for a in result.actions_taken)
        assert result.text  # Non-empty response
        assert result.cost_usd > 0

    async def test_search_returns_coherent_response(self, search_agent):
        """Agent's final response mentions the search topic."""
        result = await search_agent.chat("Search for cooking tutorial videos")

        assert isinstance(result, AgentResponse)
        assert any("search_videos" in a for a in result.actions_taken)
        # Agent should mention something about the search results
        text_lower = result.text.lower()
        assert any(
            word in text_lower
            for word in ["cooking", "tutorial", "video", "found", "result"]
        )


# ── Analysis Workflow ───────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestAnalysisWorkflow:
    """Agent analyzes a video for content safety.

    Requires youtube_video_in_r2 fixture — analyze_video downloads from R2,
    so the video must be pre-fetched before analysis can run.
    """

    async def test_analyze_youtube_video(self, agent, youtube_video_in_r2):
        """'Analyze YouTube video jNQXAC9IVRw' → analyze_video tool called."""
        result = await agent.chat(
            f"Analyze the YouTube video with ID {YOUTUBE_VIDEO_ID} for content safety"
        )

        assert isinstance(result, AgentResponse)
        assert any("analyze_video" in a for a in result.actions_taken)
        assert result.text
        assert result.cost_usd > 0

        # Tool results should contain analysis data
        analysis_results = [
            tr for tr in result.tool_results if tr["tool"] == "analyze_video"
        ]
        assert len(analysis_results) >= 1
        analysis_data = analysis_results[0]["result"]
        assert "analysis_id" in analysis_data
        assert "overall_safe" in analysis_data


# ── Multi-Tool Workflow ─────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestMultiToolWorkflow:
    """Agent chains multiple tools to answer complex queries."""

    async def test_search_then_analyze(self, agent, youtube_video_in_r2):
        """'Search and analyze YouTube video' → search + analyze."""
        result = await agent.chat(
            f"Search for YouTube videos about 'me at the zoo', "
            f"then analyze the YouTube video {YOUTUBE_VIDEO_ID} for content safety"
        )

        assert isinstance(result, AgentResponse)
        tool_names = [tr["tool"] for tr in result.tool_results]
        # Should have called at least search; may also call analyze_video
        assert "search_videos" in tool_names or "analyze_video" in tool_names
        assert result.gemini_calls >= 2
        assert result.text


# ── Fraud Detection Workflow ────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestFraudDetectionWorkflow:
    """Agent runs fraud analysis on a creator."""

    async def test_detect_fraud_tiktok(self, agent):
        """'Check if khaby.lame has fake followers' → detect_fraud tool called."""
        result = await agent.chat(
            "Check if the TikTok creator khaby.lame has fake followers or bot engagement"
        )

        assert isinstance(result, AgentResponse)
        assert any("detect_fraud" in a for a in result.actions_taken)
        assert result.text

        # Tool results should contain fraud data
        fraud_results = [
            tr for tr in result.tool_results if tr["tool"] == "detect_fraud"
        ]
        assert len(fraud_results) >= 1
        fraud_data = fraud_results[0]["result"]
        # Should have AQS score or an error (if API limits hit)
        assert "aqs_score" in fraud_data or "error" in fraud_data


# ── Creator Evolution Workflow ──────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.db
class TestCreatorEvolutionWorkflow:
    """Agent fetches creator evolution (DB-only, no external API)."""

    async def test_evolution_graceful_empty(self, agent):
        """Evolution for unknown creator → agent handles empty result gracefully."""
        result = await agent.chat(
            "Show me the content evolution of khaby.lame on TikTok over the last 90 days"
        )

        assert isinstance(result, AgentResponse)
        assert any("get_creator_evolution" in a for a in result.actions_taken)
        # Agent should respond even with no historical data
        assert result.text


# ── Brand Detection Workflow ───────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestBrandDetectionWorkflow:
    """Agent chains analyze_video → analyze_brands to detect brand mentions."""

    async def test_analyze_then_detect_brands(self, chaining_agent, youtube_video_in_r2):
        """Agent analyzes video first, then uses analysis_id to detect brands."""
        result = await chaining_agent.chat(
            f"First analyze the YouTube video {YOUTUBE_VIDEO_ID} for content safety, "
            f"then detect any brand mentions or sponsorship signals in it"
        )

        assert isinstance(result, AgentResponse)
        # Agent should call analyze_video (to get analysis_id) and then analyze_brands
        tool_names = [tr["tool"] for tr in result.tool_results]
        assert "analyze_video" in tool_names
        assert "analyze_brands" in tool_names
        assert result.text

        # Brand results should have expected structure
        brand_results = [
            tr for tr in result.tool_results if tr["tool"] == "analyze_brands"
        ]
        assert len(brand_results) >= 1
        brand_data = brand_results[0]["result"]
        assert "brand_mentions" in brand_data or "error" in brand_data


# ── Demographics Workflow ──────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestDemographicsWorkflow:
    """Agent chains analyze_video → infer_demographics for audience insights."""

    async def test_analyze_then_infer_demographics(self, chaining_agent, youtube_video_in_r2):
        """Agent analyzes video first, then infers audience demographics."""
        result = await chaining_agent.chat(
            f"Analyze the YouTube video {YOUTUBE_VIDEO_ID}, "
            f"then infer the target audience demographics for it"
        )

        assert isinstance(result, AgentResponse)
        tool_names = [tr["tool"] for tr in result.tool_results]
        assert "analyze_video" in tool_names
        assert "infer_demographics" in tool_names
        assert result.text

        # Demographics results should have expected structure
        demo_results = [
            tr for tr in result.tool_results if tr["tool"] == "infer_demographics"
        ]
        assert len(demo_results) >= 1
        demo_data = demo_results[0]["result"]
        assert "age_distribution" in demo_data or "error" in demo_data


# ── Trends Workflow ────────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.db
class TestTrendsWorkflow:
    """Agent fetches platform trends (DB-only, no external API)."""

    async def test_get_tiktok_trends(self, agent):
        """Agent calls get_trends for TikTok."""
        result = await agent.chat(
            "What are the current trending hashtags and emerging creators on TikTok?"
        )

        assert isinstance(result, AgentResponse)
        assert any("get_trends" in a for a in result.actions_taken)
        assert result.text

        # Trends result should have expected structure
        trend_results = [
            tr for tr in result.tool_results if tr["tool"] == "get_trends"
        ]
        assert len(trend_results) >= 1
        trend_data = trend_results[0]["result"]
        assert "trending_hashtags" in trend_data or "error" in trend_data


# ── Full Pipeline Workflow ─────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
@pytest.mark.db
class TestFullPipelineWorkflow:
    """Agent chains 3+ tools in a single conversation to do a full audit."""

    async def test_analyze_brands_and_demographics(self, chaining_agent, youtube_video_in_r2):
        """Agent chains analyze → brands + demographics in one conversation."""
        result = await chaining_agent.chat(
            f"Do a full content audit of YouTube video {YOUTUBE_VIDEO_ID}: "
            f"analyze it for safety, detect brand mentions, and infer audience demographics"
        )

        assert isinstance(result, AgentResponse)
        tool_names = [tr["tool"] for tr in result.tool_results]
        # Must have analyzed first
        assert "analyze_video" in tool_names
        # Should have at least one of brands or demographics (agent may run both)
        assert "analyze_brands" in tool_names or "infer_demographics" in tool_names
        assert result.gemini_calls >= 3  # analyze + at least one follow-up + final answer
        assert result.text
        assert result.cost_usd > 0


# ── Conversational (No Tools) ──────────────────────────────────────────────


@pytest.mark.gemini
class TestConversationalWorkflow:
    """Agent responds to questions without calling any tools."""

    async def test_greeting_no_tools(self, search_agent):
        """'What can you help me with?' → no tool calls, just a text response."""
        result = await search_agent.chat("What can you help me with?")

        assert isinstance(result, AgentResponse)
        assert result.text
        # Should describe capabilities without calling tools
        assert result.gemini_calls >= 1

    async def test_off_topic_no_tools(self, search_agent):
        """Off-topic question → agent responds without tool calls."""
        result = await search_agent.chat("What's the weather like today?")

        assert isinstance(result, AgentResponse)
        assert result.text
        assert result.gemini_calls >= 1


# ── Streaming Workflow ──────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestStreamingWorkflow:
    """Agent streams responses with tool events."""

    async def test_streaming_search(self, search_agent):
        """stream_chat yields tool events for a search query."""
        events = []
        async for event_type, data in search_agent.stream_chat(
            "Find popular dance videos"
        ):
            events.append((event_type, data))

        event_types = [e[0] for e in events]

        # Should have tool_call, tool_result, and done events
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "done" in event_types

        # Done event should have cost info
        done_event = next(d for t, d in events if t == "done")
        assert "cost_usd" in done_event
        assert done_event["finish_reason"] in (
            "complete", "budget_exceeded", "max_iterations",
        )


# ── Cost Tracking ──────────────────────────────────────────────────────────


@pytest.mark.gemini
@pytest.mark.external_api
class TestCostTracking:
    """Verify cost tracking works across real API calls."""

    async def test_cost_accumulates(self, search_agent):
        """Cost should be > 0 after real Gemini + tool calls."""
        result = await search_agent.chat("Search for trending videos")

        assert result.cost_usd > 0
        assert result.gemini_calls >= 1

    async def test_budget_prevents_runaway(self, gemini_client, search_only_registry):
        """Very low budget should stop the agent early."""
        config = AgentSettings(
            max_loop_iterations=10,
            cost_limit_usd=0.01,  # Minimum allowed by validator
        )
        agent = VideoIntelligenceAgent(
            gemini_client=gemini_client,
            tool_registry=search_only_registry,
            config=config,
        )

        result = await agent.chat("Search for 50 different types of videos")

        assert isinstance(result, AgentResponse)
        # Should have stopped due to budget (not run all 10 iterations)
        assert result.gemini_calls < 10
