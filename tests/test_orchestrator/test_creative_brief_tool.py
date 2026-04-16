"""Tests for generate_content agent tool."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.tiers import Tier
from src.orchestrator.tools import build_default_registry
from src.workspace.exceptions import CollectionNotFoundError
from src.workspace.models import WorkspaceCollection, WorkspaceItem, WorkspaceToolResult


def _make_collection(**overrides):
    defaults = {
        "id": uuid4(),
        "conversation_id": uuid4(),
        "name": "skincare competitors",
        "item_count": 5,
        "active_filters": {},
        "summary_stats": {},
        "payload_ref": None,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return WorkspaceCollection(**defaults)


def _make_item(**overrides):
    defaults = {
        "id": uuid4(),
        "collection_id": uuid4(),
        "source_id": "abc123",
        "platform": "tiktok",
        "title": "Best skincare routine",
        "creator_handle": "skincareguru",
        "views": 100000,
        "engagement_rate": 5.2,
        "risk_score": None,
        "analysis_results": None,
        "payload_json": {"description": "Amazing skincare tips"},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return WorkspaceItem(**defaults)


def _make_tool_result(**overrides):
    defaults = {
        "id": uuid4(),
        "conversation_id": uuid4(),
        "tool_name": "analyze_creative_patterns",
        "input_args": {},
        "result_data": {
            "hook_type": "question",
            "narrative_structure": "problem-solution",
            "cta_type": "direct",
            "cta_placement": "end",
            "pacing": "fast",
            "music_usage": "trending",
        },
        "workspace_item_id": None,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return WorkspaceToolResult(**defaults)


CONV_ID = str(uuid4())


@pytest.fixture
def mock_workspace():
    ws = AsyncMock()
    ws.find_collection_by_name = AsyncMock(return_value=_make_collection())
    ws.get_items = AsyncMock(return_value=[_make_item() for _ in range(3)])
    ws.get_tool_results = AsyncMock(return_value=[])
    return ws


@pytest.fixture
def mock_gemini_client():
    client = MagicMock()
    response = MagicMock()
    response.text = '{"vertical": "skincare", "competitors_analyzed": 3, "top_hooks": [], "narrative_patterns": [], "recommended_angles": []}'
    response.usage_metadata.prompt_token_count = 100
    response.usage_metadata.candidates_token_count = 50
    response.usage_metadata.cached_content_token_count = 0
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


def _build_registry(mock_workspace, mock_gemini_client, tier=Tier.PRO):
    registry, restricted = build_default_registry(
        analysis_service=MagicMock(),
        tier=tier,
        workspace_service=mock_workspace,
        gemini_client=mock_gemini_client,
        conversation_id=CONV_ID,
    )
    return registry, restricted


@pytest.mark.asyncio
@pytest.mark.mock_required
class TestGenerateCreativeBriefTool:
    async def test_registered_for_pro(self, mock_workspace, mock_gemini_client):
        """Tool registered when Pro tier + workspace + gemini."""
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")
        assert tool is not None

    async def test_not_registered_for_free(self, mock_workspace, mock_gemini_client):
        """Tool NOT registered for free tier; appears in restricted."""
        registry, restricted = _build_registry(mock_workspace, mock_gemini_client, tier=Tier.FREE)
        tool = registry.get("generate_content")
        assert tool is None
        assert "generate_content" in restricted

    async def test_not_registered_without_workspace(self, mock_gemini_client):
        """Tool NOT registered when workspace_service is None."""
        registry, _ = build_default_registry(
            analysis_service=MagicMock(),
            tier=Tier.PRO,
            gemini_client=mock_gemini_client,
            conversation_id=CONV_ID,
        )
        tool = registry.get("generate_content")
        assert tool is None

    async def test_not_registered_without_gemini(self, mock_workspace):
        """Tool NOT registered when gemini_client is None."""
        registry, _ = build_default_registry(
            analysis_service=MagicMock(),
            tier=Tier.PRO,
            workspace_service=mock_workspace,
            conversation_id=CONV_ID,
        )
        tool = registry.get("generate_content")
        assert tool is None

    async def test_successful_brief_generation(self, mock_workspace, mock_gemini_client):
        """Happy path: returns brief with summary."""
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="skincare competitors",
            client_vertical="organic skincare",
            user_id=str(uuid4()),
        )
        assert "error" not in result
        assert "brief" in result
        assert result["brief"]["vertical"] == "skincare"
        assert result["videos_in_collection"] == 3
        assert "organic skincare" in result["summary"]

    async def test_registry_execute_uses_default_synthesize_action(self, mock_workspace, mock_gemini_client):
        """Registry accepts creative brief calls without explicitly passing action."""
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)

        result = await registry.execute(
            "generate_content",
            {
                "collection_name": "skincare competitors",
                "client_vertical": "organic skincare",
            },
            user_tier=Tier.PRO,
        )

        assert "error" not in result
        assert result["brief"]["vertical"] == "skincare"

    async def test_collection_not_found(self, mock_workspace, mock_gemini_client):
        """Returns error when collection doesn't exist."""
        mock_workspace.find_collection_by_name = AsyncMock(
            side_effect=CollectionNotFoundError("not found"),
        )
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="nonexistent",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )
        assert result["error"] == "collection_not_found"

    async def test_empty_collection(self, mock_workspace, mock_gemini_client):
        """Returns error when collection has no items."""
        mock_workspace.get_items = AsyncMock(return_value=[])
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )
        assert result["error"] == "empty_collection"

    async def test_with_creative_patterns(self, mock_workspace, mock_gemini_client):
        """Includes pattern context when available."""
        mock_workspace.get_tool_results = AsyncMock(
            side_effect=lambda _conv_id, tool_name: (
                [_make_tool_result()] if tool_name == "analyze_creative_patterns" else []
            ),
        )
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )
        assert "error" not in result
        assert result["patterns_available"] == 1

    async def test_gemini_invalid_json(self, mock_workspace, mock_gemini_client):
        """Handles invalid JSON from Gemini gracefully."""
        response = MagicMock()
        response.text = "not valid json {{"
        response.usage_metadata.prompt_token_count = 100
        response.usage_metadata.candidates_token_count = 50
        response.usage_metadata.cached_content_token_count = 0
        mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=response)
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )
        assert "error" not in result
        assert "raw_response" in result["brief"]

    async def test_gemini_error_returns_analysis_error(self, mock_workspace, mock_gemini_client):
        """Returns analysis_error on Gemini failure."""
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("Gemini down"),
        )
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        result = await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )
        assert result["error"] == "analysis_error"

    async def test_focus_areas_passed(self, mock_workspace, mock_gemini_client):
        """Focus areas included in Gemini prompt."""
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            focus_areas="hooks and CTAs",
            user_id=str(uuid4()),
        )

        # Verify the prompt included focus areas
        call_args = mock_gemini_client.aio.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents") or call_args[1].get("contents", "")
        assert "hooks and CTAs" in prompt

    async def test_payload_sanitization(self, mock_workspace, mock_gemini_client):
        """Payload text truncated to 500 chars and triple backticks stripped."""
        long_desc = "A" * 1000
        backtick_title = "Title with ```code blocks```"
        item = _make_item(
            title=backtick_title,
            payload_json={"description": long_desc},
        )
        mock_workspace.get_items = AsyncMock(return_value=[item])
        registry, _ = _build_registry(mock_workspace, mock_gemini_client)
        tool = registry.get("generate_content")

        await tool.handler(
            collection_name="skincare competitors",
            client_vertical="skincare",
            user_id=str(uuid4()),
        )

        call_args = mock_gemini_client.aio.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents") or call_args[1].get("contents", "")
        # Description truncated to 500
        assert "A" * 501 not in prompt
        # Triple backticks stripped
        assert "```" not in prompt
