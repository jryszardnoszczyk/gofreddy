"""Tests for CI prompt section in build_system_prompt."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.billing.tiers import Tier
from src.orchestrator.prompts import _ALL_CHAINS, build_system_prompt
from src.orchestrator.tools import ToolDefinition, ToolRegistry, build_default_registry


def _make_registry_with_tools(*tool_names: str) -> ToolRegistry:
    """Create a registry with named dummy tools."""
    registry = ToolRegistry()
    for name in tool_names:
        registry.register(ToolDefinition(
            name=name,
            description=f"Test {name}",
            parameters={},
            required_params=[],
            handler=AsyncMock(),
        ))
    return registry


def test_ci_section_included_when_manage_client_registered():
    """CI workflow section should appear when manage_client is registered."""
    registry = _make_registry_with_tools("manage_client", "search")
    prompt = build_system_prompt(registry)

    assert "Competitive Intelligence Workflows" in prompt
    assert "manage_client" in prompt


def test_ci_section_excluded_when_manage_client_not_registered():
    """CI workflow section should not appear without manage_client."""
    registry = _make_registry_with_tools("search", "analyze_video")
    prompt = build_system_prompt(registry)

    assert "Competitive Intelligence Workflows" not in prompt


def test_ci_chain_in_all_chains():
    """Verify the CI chain tuple exists in _ALL_CHAINS."""
    ci_chain_tools = {"manage_client", "manage_monitor", "query_monitor", "search", "analyze_video"}

    found = any(
        required == ci_chain_tools
        for required, _ in _ALL_CHAINS
    )

    assert found, f"CI chain not found in _ALL_CHAINS. Available: {[req for req, _ in _ALL_CHAINS]}"


def test_chain_filtered_when_tools_missing():
    """Chain should be excluded when not all required tools are registered."""
    # Only register manage_client, not the other CI chain tools
    registry = _make_registry_with_tools("manage_client")
    prompt = build_system_prompt(registry)

    # The CI chain description should NOT appear because
    # manage_monitor, query_monitor, etc. are missing
    assert "Full competitive analysis:" not in prompt


def test_chain_included_when_all_tools_registered():
    """Chain should be included when all required tools are registered."""
    registry = _make_registry_with_tools(
        "manage_client", "manage_monitor", "query_monitor",
        "search", "analyze_video"
    )
    prompt = build_system_prompt(registry)

    assert "Full competitive analysis:" in prompt


def test_manage_client_tool_registered_pro_tier():
    """manage_client should be registered when client_service provided and tier is PRO."""
    mock_service = AsyncMock()
    registry, restricted = build_default_registry(
        client_service=mock_service, tier=Tier.PRO
    )
    assert "manage_client" in registry.names


def test_manage_client_tool_not_registered_without_service():
    """manage_client should not be registered when client_service is None."""
    registry, _ = build_default_registry(client_service=None, tier=Tier.PRO)
    assert "manage_client" not in registry.names
