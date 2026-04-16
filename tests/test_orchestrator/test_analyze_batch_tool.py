"""Tests for the workspace(action='batch_analyze') tool handler in build_default_registry.

Pure mock tests — no DB, no external APIs, no Gemini needed.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.batch.models import BatchJob, BatchStatus
from src.orchestrator.tools import build_default_registry


# ── Helpers ──────────────────────────────────────────────────


def _make_batch(**kwargs: Any) -> BatchJob:
    defaults = {
        "id": uuid4(),
        "conversation_id": uuid4(),
        "collection_id": uuid4(),
        "user_id": uuid4(),
        "status": BatchStatus.PENDING,
        "total_items": 5,
        "completed_items": 0,
        "failed_items": 0,
        "flagged_items": 0,
        "analysis_types": ["brand_safety"],
        "idempotency_key": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return BatchJob(**defaults)


def _build_registry_with_batch(
    *,
    batch_service: Any = None,
    analysis_service: Any = None,
    batch_repository: Any = None,
    workspace_service: Any = None,
    workspace_repository: Any = None,
    batch_settings: Any = None,
    billing_service: Any = None,
    conversation_id: UUID | None = None,
):
    """Build a registry with batch-related deps filled in.

    workspace_service is required because analyze_batch is now absorbed
    into the workspace tool (action='batch_analyze').
    """
    return build_default_registry(
        analysis_service=analysis_service or AsyncMock(),
        billing_service=billing_service,
        batch_service=batch_service or AsyncMock(),
        batch_repository=batch_repository or AsyncMock(),
        workspace_service=workspace_service or AsyncMock(),
        workspace_repository=workspace_repository or AsyncMock(),
        batch_settings=batch_settings,
        conversation_id=conversation_id or uuid4(),
    )


# ── Tests ────────────────────────────────────────────────────


class TestAnalyzeBatchRegistration:
    def test_workspace_registered_when_deps_present(self):
        """workspace tool appears in registry when batch_service, analysis_service,
        workspace_service, and conversation_id are all provided."""
        registry, _ = _build_registry_with_batch()
        assert "workspace" in registry.names
        # analyze_batch absorbed into workspace(action="batch_analyze")
        assert "analyze_batch" not in registry.names

    def test_workspace_not_registered_without_workspace_service(self):
        """workspace tool not registered when workspace_service is None."""
        registry, _ = build_default_registry(
            analysis_service=AsyncMock(),
            conversation_id=uuid4(),
            batch_service=None,
        )
        assert "analyze_batch" not in registry.names


class TestAnalyzeBatchHandler:
    @pytest.mark.asyncio
    async def test_analyze_batch_happy_path(self):
        """Pending batch with 5 items returns correct summary and workspace keys."""
        coll_id = uuid4()
        batch_id = uuid4()
        batch = _make_batch(
            id=batch_id,
            collection_id=coll_id,
            total_items=5,
            status=BatchStatus.PENDING,
        )

        batch_svc = AsyncMock()
        batch_svc.create_batch = AsyncMock(return_value=batch)

        registry, _ = _build_registry_with_batch(batch_service=batch_svc)
        tool = registry.get("workspace")
        assert tool is not None
        handler = tool.handler

        mock_task = MagicMock(spec=asyncio.Task)
        with patch("src.batch.worker.BatchWorker"), \
             patch("asyncio.create_task", return_value=mock_task):
            result = await handler(
                action="batch_analyze",
                collection_id=str(coll_id),
                user_id=str(uuid4()),
            )

        assert "summary" in result
        assert "workspace" in result
        assert "5 videos" in result["summary"]
        assert result["workspace"]["batch_id"] == str(batch_id)
        assert result["workspace"]["total_items"] == 5
        assert result["workspace"]["action"] == "batch_started"

    @pytest.mark.asyncio
    async def test_analyze_batch_empty_collection(self):
        """Completed batch with 0 items returns empty-collection message."""
        coll_id = uuid4()
        batch = _make_batch(
            collection_id=coll_id,
            total_items=0,
            status=BatchStatus.COMPLETED,
        )

        batch_svc = AsyncMock()
        batch_svc.create_batch = AsyncMock(return_value=batch)

        registry, _ = _build_registry_with_batch(batch_service=batch_svc)
        tool = registry.get("workspace")
        assert tool is not None
        handler = tool.handler

        result = await handler(action="batch_analyze", collection_id=str(coll_id), user_id=str(uuid4()))

        assert "empty" in result["summary"].lower()
        assert result["workspace"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_analyze_batch_defaults_analysis_types(self):
        """When analysis_types is None, create_batch receives ['brand_safety']."""
        batch = _make_batch(status=BatchStatus.COMPLETED, total_items=0)

        batch_svc = AsyncMock()
        batch_svc.create_batch = AsyncMock(return_value=batch)

        registry, _ = _build_registry_with_batch(batch_service=batch_svc)
        tool = registry.get("workspace")
        assert tool is not None
        handler = tool.handler

        await handler(action="batch_analyze", collection_id=str(uuid4()), analysis_types=None, user_id=str(uuid4()))

        call_kwargs = batch_svc.create_batch.call_args.kwargs
        assert call_kwargs["analysis_types"] == ["brand_safety"]

    @pytest.mark.asyncio
    async def test_analyze_batch_user_id_injected(self):
        """Handler accepts user_id as str (from _execute_tool) and converts to UUID for create_batch."""
        user_id = uuid4()
        batch = _make_batch(status=BatchStatus.COMPLETED, total_items=0)

        batch_svc = AsyncMock()
        batch_svc.create_batch = AsyncMock(return_value=batch)

        registry, _ = _build_registry_with_batch(batch_service=batch_svc)
        tool = registry.get("workspace")
        assert tool is not None
        handler = tool.handler

        await handler(action="batch_analyze", collection_id=str(uuid4()), user_id=str(user_id))

        call_kwargs = batch_svc.create_batch.call_args.kwargs
        assert call_kwargs["user_id"] == user_id
        assert isinstance(call_kwargs["user_id"], UUID)
