"""Deterministic orchestrator E2E tests with fake Gemini + in-memory tools.

These tests validate chaining, streaming semantics, limits, and sanitization
without live Gemini or external APIs.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from google.genai import types as genai_types

from src.orchestrator.agent import VideoIntelligenceAgent
from src.orchestrator.config import AgentSettings
from src.orchestrator.tools import ToolDefinition, ToolRegistry


def _text_part(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, function_call=None)


def _function_part(name: str, args: dict) -> SimpleNamespace:
    return SimpleNamespace(
        text=None,
        function_call=SimpleNamespace(name=name, args=args),
    )


def _response(
    parts: list[SimpleNamespace],
    *,
    finish_reason: genai_types.FinishReason = genai_types.FinishReason.STOP,
    prompt_tokens: int = 100,
    candidate_tokens: int = 100,
) -> SimpleNamespace:
    return SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt_tokens,
            candidates_token_count=candidate_tokens,
        ),
        candidates=[
            SimpleNamespace(
                finish_reason=finish_reason,
                content=SimpleNamespace(parts=parts),
            )
        ],
    )


class _FakeModels:
    def __init__(self, responses: list[SimpleNamespace | Exception]) -> None:
        self._responses = responses

    async def generate_content(self, **kwargs) -> SimpleNamespace:
        assert self._responses, "No fake Gemini responses remaining"
        next_item = self._responses.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        return next_item


class _FakeGeminiClient:
    def __init__(self, responses: list[SimpleNamespace | Exception]) -> None:
        self.aio = SimpleNamespace(models=_FakeModels(responses))


def _registry_with_handlers() -> ToolRegistry:
    registry = ToolRegistry()

    async def search_videos(**kwargs):
        return {
            "summary": "Found videos",
            "video_ids": ["vid-1"],
        }

    async def analyze_video(**kwargs):
        return {
            "summary": "Video analyzed",
            "analysis_id": "analysis-1",
            "overall_safe": True,
        }

    async def analyze_brands(**kwargs):
        return {
            "summary": "Brands inferred",
            "brand_mentions": [{"name": "BrandX", "confidence": 0.9}],
        }

    async def infer_demographics(**kwargs):
        return {
            "summary": "Demographics inferred",
            "age_distribution": {"18-24": 0.42},
        }

    async def detect_fraud(**kwargs):
        return {
            "summary": "Fraud score calculated",
            "aqs_score": 81,
        }

    async def get_trends(**kwargs):
        return {
            "summary": "Trends fetched",
            "trending_hashtags": ["#springstyle"],
        }

    async def get_creator_evolution(**kwargs):
        return {
            "summary": "Evolution fetched",
            "timeline": [],
        }

    registry.register(ToolDefinition(
        name="search_videos",
        description="Search videos",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=search_videos,
    ))
    registry.register(ToolDefinition(
        name="analyze_video",
        description="Analyze a video",
        parameters={"platform": {"type": "string"}, "video_id": {"type": "string"}},
        required_params=["platform", "video_id"],
        handler=analyze_video,
    ))
    registry.register(ToolDefinition(
        name="analyze_brands",
        description="Analyze brands",
        parameters={"analysis_id": {"type": "string"}},
        required_params=["analysis_id"],
        handler=analyze_brands,
    ))
    registry.register(ToolDefinition(
        name="infer_demographics",
        description="Infer demographics",
        parameters={"analysis_id": {"type": "string"}},
        required_params=["analysis_id"],
        handler=infer_demographics,
    ))
    registry.register(ToolDefinition(
        name="detect_fraud",
        description="Detect fraud",
        parameters={"platform": {"type": "string"}, "username": {"type": "string"}},
        required_params=["platform", "username"],
        handler=detect_fraud,
    ))
    registry.register(ToolDefinition(
        name="get_trends",
        description="Get trends",
        parameters={"platform": {"type": "string"}},
        required_params=["platform"],
        handler=get_trends,
    ))
    registry.register(ToolDefinition(
        name="get_creator_evolution",
        description="Get creator evolution",
        parameters={"platform": {"type": "string"}, "creator_id": {"type": "string"}},
        required_params=["platform", "creator_id"],
        handler=get_creator_evolution,
    ))

    return registry


@pytest.mark.asyncio
async def test_workflow_search_then_analyze_brands_and_demographics() -> None:
    responses = [
        _response([_function_part("search_videos", {"query": "sustainable fashion"})]),
        _response([_function_part("analyze_video", {"platform": "youtube", "video_id": "vid-1"})]),
        _response([
            _function_part("analyze_brands", {"analysis_id": "analysis-1"}),
            _function_part("infer_demographics", {"analysis_id": "analysis-1"}),
        ]),
        _response([_text_part("Audit complete with brands and demographics.")]),
    ]
    agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient(responses),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=6, cost_limit_usd=5.0),
    )

    result = await agent.chat("Do a full audit")
    tools = [entry["tool"] for entry in result.tool_results]
    assert tools == ["search_videos", "analyze_video", "analyze_brands", "infer_demographics"]
    assert "Audit complete" in result.text


@pytest.mark.asyncio
async def test_workflow_detect_fraud() -> None:
    responses = [
        _response([_function_part("detect_fraud", {"platform": "tiktok", "username": "creator"})]),
        _response([_text_part("Fraud review completed.")]),
    ]
    agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient(responses),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=4, cost_limit_usd=1.0),
    )

    result = await agent.chat("Check fraud risk")
    tools = [entry["tool"] for entry in result.tool_results]
    assert tools == ["detect_fraud"]
    assert result.tool_results[0]["result"]["aqs_score"] == 81


@pytest.mark.asyncio
async def test_workflow_trends_and_evolution() -> None:
    responses = [
        _response([_function_part("get_trends", {"platform": "tiktok"})]),
        _response([_function_part("get_creator_evolution", {"platform": "tiktok", "creator_id": "khaby.lame"})]),
        _response([_text_part("Trends and evolution summary ready.")]),
    ]
    agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient(responses),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=5, cost_limit_usd=1.0),
    )

    result = await agent.chat("Show trends and creator evolution")
    tools = [entry["tool"] for entry in result.tool_results]
    assert tools == ["get_trends", "get_creator_evolution"]
    assert "summary" in result.text.lower()


@pytest.mark.asyncio
async def test_streaming_event_ordering_and_done_terminal() -> None:
    responses = [
        _response([
            _text_part("Searching now"),
            _function_part("search_videos", {"query": "fashion"}),
        ]),
        _response([_text_part("Found useful results.")]),
    ]
    agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient(responses),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=4, cost_limit_usd=1.0),
    )

    events = []
    async for event_type, data in agent.stream_chat("Search and summarize"):
        events.append((event_type, data))

    event_types = [event_type for event_type, _ in events]
    assert event_types[-1] == "done"
    assert event_types.count("done") == 1
    assert event_types.index("tool_call") < event_types.index("tool_result")
    assert event_types.index("tool_result") < event_types.index("done")


@pytest.mark.asyncio
async def test_streaming_does_not_leak_internal_tool_errors() -> None:
    async def leaky_tool(**kwargs):
        raise RuntimeError("SECRET_DB_PASSWORD")

    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="leaky_tool",
        description="Fails with internal details",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=leaky_tool,
    ))

    responses = [
        _response([_function_part("leaky_tool", {"query": "x"})]),
        _response([_text_part("Could not complete due to tool issue.")]),
    ]
    agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient(responses),
        tool_registry=registry,
        config=AgentSettings(max_loop_iterations=3, cost_limit_usd=1.0),
    )

    events = []
    async for event_type, data in agent.stream_chat("Run leaky tool"):
        events.append((event_type, data))

    tool_results = [data for event_type, data in events if event_type == "tool_result"]
    assert len(tool_results) == 1
    assert "SECRET_DB_PASSWORD" not in json.dumps(tool_results[0])
    assert tool_results[0]["summary"] == "Tool leaky_tool encountered an error"


@pytest.mark.asyncio
async def test_streaming_budget_and_iteration_limits() -> None:
    budget_agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient([
            _response([_function_part("search_videos", {"query": "x"})], prompt_tokens=30_000, candidate_tokens=30_000),
        ]),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=3, cost_limit_usd=0.01),
    )
    budget_events = []
    async for event_type, data in budget_agent.stream_chat("Trigger budget guard"):
        budget_events.append((event_type, data))

    budget_done = [d for t, d in budget_events if t == "done"][-1]
    assert budget_done["finish_reason"] == "budget_exceeded"

    iteration_agent = VideoIntelligenceAgent(
        gemini_client=_FakeGeminiClient([
            _response([_function_part("search_videos", {"query": "first"})]),
            _response([_function_part("search_videos", {"query": "second"})]),
        ]),
        tool_registry=_registry_with_handlers(),
        config=AgentSettings(max_loop_iterations=2, cost_limit_usd=1.0),
    )
    iteration_events = []
    async for event_type, data in iteration_agent.stream_chat("Trigger iteration cap"):
        iteration_events.append((event_type, data))

    iteration_done = [d for t, d in iteration_events if t == "done"][-1]
    assert iteration_done["finish_reason"] == "max_iterations"
