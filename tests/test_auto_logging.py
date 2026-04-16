"""Tests for auto-logging in ToolRegistry."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.tiers import Tier
from src.orchestrator.tools import ToolDefinition, ToolRegistry


async def _dummy_handler(**kwargs):
    return {"summary": "Done", "result": "ok"}


async def _error_handler(**kwargs):
    return {"summary": "Failed", "error": "some_error"}


def _make_registry_with_tool() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=_dummy_handler,
        timeout_seconds=30,
    ))
    return registry


def _make_registry_with_error_tool() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="error_tool",
        description="A tool that returns errors",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=_error_handler,
        timeout_seconds=30,
    ))
    return registry


@pytest.mark.asyncio
async def test_log_action_called_on_success():
    """Verify fire-and-forget log is called when session context is set."""
    registry = _make_registry_with_tool()
    mock_repo = AsyncMock()
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    result = await registry.execute("test_tool", {"query": "hello"})

    # Wait for fire-and-forget task to complete
    if registry._pending_logs:
        await asyncio.wait(registry._pending_logs, timeout=2.0)

    assert result["summary"] == "Done"
    mock_repo.log_action.assert_called_once()
    call_kwargs = mock_repo.log_action.call_args
    assert call_kwargs.kwargs["tool_name"] == "test_tool"
    assert call_kwargs.kwargs["status"] == "success"
    assert call_kwargs.kwargs["error_code"] is None


@pytest.mark.asyncio
async def test_log_action_not_called_without_session():
    """No session context = no logging."""
    registry = _make_registry_with_tool()
    # Don't set session context

    result = await registry.execute("test_tool", {"query": "hello"})

    assert result["summary"] == "Done"
    assert len(registry._pending_logs) == 0


@pytest.mark.asyncio
async def test_log_failure_does_not_block():
    """Exception in logging doesn't break tool result."""
    registry = _make_registry_with_tool()
    mock_repo = AsyncMock()
    mock_repo.log_action.side_effect = Exception("DB down")
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    result = await registry.execute("test_tool", {"query": "hello"})

    # Wait for fire-and-forget to complete
    if registry._pending_logs:
        await asyncio.wait(registry._pending_logs, timeout=2.0)

    # Tool result should still be returned
    assert result["summary"] == "Done"


@pytest.mark.asyncio
async def test_flush_pending_logs():
    """Verify flush_pending_logs awaits pending tasks."""
    registry = _make_registry_with_tool()
    mock_repo = AsyncMock()
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    await registry.execute("test_tool", {"query": "hello"})

    # There should be pending logs
    assert len(registry._pending_logs) > 0 or mock_repo.log_action.called

    await registry.flush_pending_logs(timeout=2.0)

    mock_repo.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_flush_pending_logs_empty():
    """flush_pending_logs with no pending tasks should not crash."""
    registry = _make_registry_with_tool()
    await registry.flush_pending_logs(timeout=1.0)  # Should not raise


@pytest.mark.asyncio
async def test_duration_ms_captured():
    """Verify timing is measured and passed to log_action."""
    registry = _make_registry_with_tool()
    mock_repo = AsyncMock()
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    await registry.execute("test_tool", {"query": "hello"})

    if registry._pending_logs:
        await asyncio.wait(registry._pending_logs, timeout=2.0)

    call_kwargs = mock_repo.log_action.call_args.kwargs
    assert "duration_ms" in call_kwargs
    assert isinstance(call_kwargs["duration_ms"], int)
    assert call_kwargs["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_summary_truncated_to_500():
    """Verify summary is truncated to 500 chars."""
    async def long_summary_handler(**kwargs):
        return {"summary": "x" * 1000, "result": "ok"}

    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="long_tool",
        description="Tool with long output",
        parameters={"query": {"type": "string"}},
        required_params=["query"],
        handler=long_summary_handler,
        timeout_seconds=30,
    ))
    mock_repo = AsyncMock()
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    await registry.execute("long_tool", {"query": "hello"})

    if registry._pending_logs:
        await asyncio.wait(registry._pending_logs, timeout=2.0)

    call_kwargs = mock_repo.log_action.call_args.kwargs
    summary = call_kwargs["output_summary"]["summary"]
    assert len(summary) <= 500


@pytest.mark.asyncio
async def test_error_status_on_tool_failure():
    """Verify status='error' when result has error key."""
    registry = _make_registry_with_error_tool()
    mock_repo = AsyncMock()
    registry._session_repository = mock_repo
    registry._session_id = uuid4()
    registry._org_id = uuid4()

    await registry.execute("error_tool", {"query": "hello"})

    if registry._pending_logs:
        await asyncio.wait(registry._pending_logs, timeout=2.0)

    call_kwargs = mock_repo.log_action.call_args.kwargs
    assert call_kwargs["status"] == "error"
    assert call_kwargs["error_code"] == "some_error"
