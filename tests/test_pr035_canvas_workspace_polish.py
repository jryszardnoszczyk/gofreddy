"""PR-035 Canvas & Workspace Polish — targeted unit tests.

Tests:
- Task 1.1: workspace_update SSE emitted for domain tools
- Task 1.2: UUID suffix on collection names
- Task 1.3: filter_collection sets active_collection
"""

import re
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.orchestrator.agent import VideoIntelligenceAgent, _WORKSPACE_QUERY_TOOLS
from src.orchestrator.tools import ToolDefinition, ToolRegistry
from src.workspace.models import CollectionSummary, WorkspaceCollection
from src.workspace.service import WorkspaceService

from datetime import UTC, datetime


# ── Helpers ────────────────────────────────────────────────────


def _make_agent(
    *,
    tools: list[ToolDefinition] | None = None,
    workspace_service=None,
    conversation_id=None,
):
    """Minimal agent for streaming tests with optional workspace wiring."""
    registry = ToolRegistry()
    for t in tools or []:
        registry.register(t)

    return VideoIntelligenceAgent(
        gemini_client=SimpleNamespace(),  # Not called in streaming tests
        tool_registry=registry,
        workspace_service=workspace_service,
        conversation_id=conversation_id,
    )


def _make_gemini_response(*, function_calls=None, text=None, finish_reason=None):
    """Build a mock Gemini response with optional function calls and/or text."""
    parts = []
    if function_calls:
        for name, args in function_calls:
            parts.append(SimpleNamespace(
                function_call=SimpleNamespace(name=name, args=args),
                text=None,
            ))
    if text:
        parts.append(SimpleNamespace(function_call=None, text=text))

    fr = finish_reason or SimpleNamespace()
    candidate = SimpleNamespace(
        finish_reason=fr,
        content=SimpleNamespace(parts=parts) if parts else None,
    )
    return SimpleNamespace(
        candidates=[candidate],
        usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=10),
    )


def _make_collection(**kwargs):
    return WorkspaceCollection(
        id=kwargs.get("id", uuid4()),
        conversation_id=kwargs.get("conversation_id", uuid4()),
        name=kwargs.get("name", "Test"),
        item_count=kwargs.get("item_count", 0),
        active_filters={},
        summary_stats={},
        payload_ref=None,
        is_active=kwargs.get("is_active", False),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_summary():
    return CollectionSummary(
        total_count=10,
        view_distribution={"<10k": 5, "10k-100k": 3, "100k-500k": 1, ">500k": 0, "unknown": 1},
        engagement_percentiles={"p25": 0.02, "median": 0.05, "p75": 0.1},
        top_creators=[{"handle": "alice", "count": 5}],
        platform_breakdown={"tiktok": 7, "instagram": 3},
        date_range={"earliest": "2026-01-01T00:00:00", "latest": "2026-02-01T00:00:00"},
    )


# ── Task 1.1: workspace_update emission for domain tools ──────


class TestWorkspaceUpdateEmission:
    """Streaming loop emits workspace_update for non-query domain tools."""

    async def _collect_stream_events(self, agent, message="test", user_id=None):
        events = []
        async for event_type, data in agent.stream_chat(message, user_id=user_id):
            events.append((event_type, data))
        return events

    async def test_workspace_update_emitted_for_domain_tool(self):
        """Domain tool with conversation_id → workspace_update emitted."""
        async def handler(**kwargs):
            return {"summary": "fraud analysis done"}

        tool = ToolDefinition(
            name="detect_fraud",
            description="Detect fraud",
            parameters={"platform": {"type": "string"}, "username": {"type": "string"}},
            required_params=["platform", "username"],
            handler=handler,
        )

        ws_service = AsyncMock()
        conv_id = uuid4()
        agent = _make_agent(
            tools=[tool],
            workspace_service=ws_service,
            conversation_id=conv_id,
        )

        # Mock Gemini: first call returns function_call, second returns text
        from google.genai import types as genai_types
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_gemini_response(
                    function_calls=[("detect_fraud", {"platform": "tiktok", "username": "alice"})],
                    finish_reason=genai_types.FinishReason.STOP,
                )
            return _make_gemini_response(
                text="Analysis complete.",
                finish_reason=genai_types.FinishReason.STOP,
            )

        agent._gemini = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=mock_generate)
            )
        )

        events = await self._collect_stream_events(agent)
        event_types = [e[0] for e in events]
        assert "workspace_update" in event_types

        ws_events = [(t, d) for t, d in events if t == "workspace_update"]
        assert ws_events[0][1]["tool"] == "detect_fraud"
        assert ws_events[0][1]["action"] == "tool_result_stored"

    async def test_no_workspace_update_for_query_tool(self):
        """workspace → NO workspace_update (read-only tool)."""
        async def handler(**kwargs):
            return {"summary": "workspace state", "collections": []}

        tool = ToolDefinition(
            name="workspace",
            description="Query workspace",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=handler,
        )

        conv_id = uuid4()
        agent = _make_agent(
            tools=[tool],
            workspace_service=AsyncMock(),
            conversation_id=conv_id,
        )

        from google.genai import types as genai_types
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_gemini_response(
                    function_calls=[("workspace", {"query": "show collections"})],
                    finish_reason=genai_types.FinishReason.STOP,
                )
            return _make_gemini_response(
                text="Here are your collections.",
                finish_reason=genai_types.FinishReason.STOP,
            )

        agent._gemini = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=mock_generate)
            )
        )

        events = await self._collect_stream_events(agent)
        event_types = [e[0] for e in events]
        assert "workspace_update" not in event_types

    async def test_no_workspace_update_for_errored_tool(self):
        """Domain tool returning error → NO workspace_update."""
        async def handler(**kwargs):
            return {"summary": "Provider unavailable", "error": "providers_unavailable"}

        tool = ToolDefinition(
            name="detect_deepfake",
            description="Detect deepfake",
            parameters={"platform": {"type": "string"}, "video_id": {"type": "string"}},
            required_params=["platform", "video_id"],
            handler=handler,
        )

        conv_id = uuid4()
        agent = _make_agent(
            tools=[tool],
            workspace_service=AsyncMock(),
            conversation_id=conv_id,
        )

        from google.genai import types as genai_types
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_gemini_response(
                    function_calls=[("detect_deepfake", {"platform": "youtube", "video_id": "abc"})],
                    finish_reason=genai_types.FinishReason.STOP,
                )
            return _make_gemini_response(
                text="Sorry, deepfake detection is unavailable.",
                finish_reason=genai_types.FinishReason.STOP,
            )

        agent._gemini = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=mock_generate)
            )
        )

        events = await self._collect_stream_events(agent)
        event_types = [e[0] for e in events]
        assert "workspace_update" not in event_types

    async def test_workspace_update_preserved_for_search(self):
        """search_videos returns workspace key → existing workspace_update still works."""
        async def handler(**kwargs):
            return {
                "summary": "Found 10 results",
                "workspace": {"action": "created", "collection_name": "fitness", "collection_id": "col-1"},
            }

        tool = ToolDefinition(
            name="search_videos",
            description="Search",
            parameters={"query": {"type": "string"}},
            required_params=["query"],
            handler=handler,
        )

        conv_id = uuid4()
        agent = _make_agent(
            tools=[tool],
            workspace_service=AsyncMock(),
            conversation_id=conv_id,
        )

        from google.genai import types as genai_types
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_gemini_response(
                    function_calls=[("search_videos", {"query": "fitness"})],
                    finish_reason=genai_types.FinishReason.STOP,
                )
            return _make_gemini_response(
                text="Found results.",
                finish_reason=genai_types.FinishReason.STOP,
            )

        agent._gemini = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(generate_content=mock_generate)
            )
        )

        events = await self._collect_stream_events(agent)
        ws_events = [(t, d) for t, d in events if t == "workspace_update"]
        assert len(ws_events) == 1
        assert ws_events[0][1]["action"] == "created"
        assert ws_events[0][1]["collection_name"] == "fitness"


# ── Task 1.2: UUID suffix on collection names ──────────────────


class TestCollectionNameUUIDSuffix:
    """Collection names get UUID suffix to prevent duplicate conflicts."""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return WorkspaceService(repository=mock_repo)

    async def test_collection_name_has_uuid_suffix(self, service, mock_repo):
        coll = _make_collection(item_count=1)
        summary = _make_summary()
        mock_repo.create_collection_with_items.return_value = (coll, summary)

        await service.create_collection_from_search(
            uuid4(), "fitness", [{"source_id": "v1", "platform": "tiktok"}]
        )

        call_args = mock_repo.create_collection_with_items.call_args
        name = call_args.kwargs["name"]
        assert re.match(r"fitness-[0-9a-f]{8}$", name), f"Expected UUID suffix, got: {name}"

    async def test_duplicate_search_creates_two_collections(self, service, mock_repo):
        coll = _make_collection(item_count=1)
        summary = _make_summary()
        mock_repo.create_collection_with_items.return_value = (coll, summary)

        await service.create_collection_from_search(
            uuid4(), "fitness", [{"source_id": "v1", "platform": "tiktok"}]
        )
        await service.create_collection_from_search(
            uuid4(), "fitness", [{"source_id": "v2", "platform": "tiktok"}]
        )

        assert mock_repo.create_collection_with_items.call_count == 2
        name1 = mock_repo.create_collection_with_items.call_args_list[0].kwargs["name"]
        name2 = mock_repo.create_collection_with_items.call_args_list[1].kwargs["name"]
        assert name1 != name2  # Different UUID suffixes

    async def test_uuid_suffix_with_max_length_name(self, service, mock_repo):
        coll = _make_collection(item_count=1)
        summary = _make_summary()
        mock_repo.create_collection_with_items.return_value = (coll, summary)

        long_name = "a" * 50
        await service.create_collection_from_search(
            uuid4(), long_name, [{"source_id": "v1", "platform": "tiktok"}]
        )

        call_args = mock_repo.create_collection_with_items.call_args
        name = call_args.kwargs["name"]
        # 50 chars + dash + 8 hex = 59
        assert len(name) == 59


# ── Task 1.3: filter_collection sets active_collection ──────────


class TestFilterSetsActive:
    """filter_collection() now calls set_active() on the repository."""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return WorkspaceService(repository=mock_repo)

    async def test_filter_collection_sets_active(self, service, mock_repo):
        conv_id = uuid4()
        coll_id = uuid4()
        coll = _make_collection(id=coll_id, conversation_id=conv_id, item_count=10)
        summary = _make_summary()
        mock_repo.update_filters.return_value = coll
        mock_repo.aggregate.return_value = summary
        mock_repo.update_summary.return_value = coll

        await service.filter_collection(coll_id, {"platform": "tiktok"})

        mock_repo.set_active.assert_called_once_with(conv_id, coll_id)
