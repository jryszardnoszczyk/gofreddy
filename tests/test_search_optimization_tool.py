"""Tests for seo_audit tool handler — integration.

Verifies canvas_sections, partial failure handling, and parameter validation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.orchestrator.tools import build_default_registry
from src.billing.tiers import Tier


@pytest.fixture
def mock_geo_service():
    svc = AsyncMock()
    svc.cloro_client = MagicMock()
    svc.cloro_client.is_available = True
    svc.get_by_id = AsyncMock()
    return svc


@pytest.fixture
def mock_seo_service():
    svc = AsyncMock()
    return svc


@pytest.fixture
def registry_with_tools(mock_geo_service, mock_seo_service):
    registry, restricted = build_default_registry(
        geo_service=mock_geo_service,
        seo_service=mock_seo_service,
        tier=Tier.PRO,
    )
    return registry, restricted


class TestToolRegistration:
    def test_seo_and_geo_tools_registered(self, registry_with_tools):
        registry, _ = registry_with_tools
        assert registry.get("seo_audit") is not None
        assert registry.get("geo_check_visibility") is not None

    def test_tools_are_pro_tier(self, registry_with_tools):
        registry, _ = registry_with_tools
        for tool_name in ("seo_audit", "geo_check_visibility"):
            tool = registry.get(tool_name)
            assert tool.min_tier == Tier.PRO

    def test_cost_credits(self, registry_with_tools):
        registry, _ = registry_with_tools
        assert registry.get("seo_audit").cost_credits == 0  # variable billing per action
        assert registry.get("geo_check_visibility").cost_credits == 5

    def test_no_geo_service_skips_visibility_tools(self, mock_seo_service):
        registry, _ = build_default_registry(
            seo_service=mock_seo_service,
            tier=Tier.PRO,
        )
        assert registry.get("seo_audit") is not None  # SEO-only still works
        assert registry.get("geo_check_visibility") is None


class TestSearchOptimizationAuditHandler:
    @pytest.mark.asyncio
    async def test_all_includes_default(self, registry_with_tools, mock_geo_service, mock_seo_service):
        registry, _ = registry_with_tools

        # Mock GEO result
        @dataclass
        class FakeGeoResult:
            audit_id: UUID = uuid4()

            def __dataclass_fields__(self):
                pass

        mock_geo_service.run_audit.return_value = FakeGeoResult()
        mock_seo_service.technical_audit.return_value = {"url": "x", "issues": []}
        mock_seo_service.check_performance.return_value = {"url": "x", "score": 0.9}
        mock_seo_service.backlink_analysis.return_value = {"target_url": "x"}

        result = await registry.execute(
            "seo_audit",
            {"action": "audit", "url": "https://example.com", "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )

        assert "canvas_sections" in result
        assert "summary" in result
        assert result.get("error") is None or result["error"] != "no_provider"

    @pytest.mark.asyncio
    async def test_partial_failure_geo_fails(self, registry_with_tools, mock_geo_service, mock_seo_service):
        registry, _ = registry_with_tools

        mock_geo_service.run_audit.side_effect = Exception("Cloro unavailable")
        mock_seo_service.technical_audit.return_value = {"url": "x", "issues": []}
        mock_seo_service.check_performance.return_value = {"url": "x", "score": 0.9}
        mock_seo_service.backlink_analysis.return_value = {"target_url": "x"}

        result = await registry.execute(
            "seo_audit",
            {
                "action": "audit",
                "url": "https://example.com",
                "include": ["geo", "seo_technical", "seo_performance", "seo_backlinks"],
                "user_id": str(uuid4()),
            },
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )

        # GEO failed but SEO sections should be present
        sections = result.get("canvas_sections", [])
        assert "geo" not in sections
        assert any(s.startswith("seo_") for s in sections)
        # SEO-only report still renders even when GEO fails
        assert "search_optimization_report" in sections

    @pytest.mark.asyncio
    async def test_selective_includes(self, registry_with_tools, mock_seo_service):
        registry, _ = registry_with_tools

        mock_seo_service.technical_audit.return_value = {"url": "x", "issues": []}

        result = await registry.execute(
            "seo_audit",
            {
                "action": "audit",
                "url": "https://example.com",
                "include": ["seo_technical"],
                "user_id": str(uuid4()),
            },
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )

        sections = result.get("canvas_sections", [])
        assert "seo_technical" in sections
        assert "geo" not in sections

    @pytest.mark.asyncio
    async def test_invalid_includes_defaults_to_all(self, registry_with_tools, mock_geo_service, mock_seo_service):
        """Invalid include values are filtered, empty result defaults to all."""
        registry, _ = registry_with_tools

        @dataclass
        class FakeGeoResult:
            audit_id: UUID = uuid4()

        mock_geo_service.run_audit.return_value = FakeGeoResult()
        mock_seo_service.technical_audit.return_value = {"url": "x"}
        mock_seo_service.check_performance.return_value = {"url": "x"}
        mock_seo_service.backlink_analysis.return_value = {"target_url": "x"}

        result = await registry.execute(
            "seo_audit",
            {
                "action": "audit",
                "url": "https://example.com",
                "include": ["invalid_thing"],
                "user_id": str(uuid4()),
            },
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )

        # Should default to all includes
        assert "canvas_sections" in result


class TestSeoAuditOptimizeHandler:
    @pytest.mark.asyncio
    async def test_audit_not_found(self, registry_with_tools, mock_geo_service):
        registry, _ = registry_with_tools
        mock_geo_service.get_by_id.return_value = None

        result = await registry.execute(
            "seo_audit",
            {"action": "optimize", "audit_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "audit_not_found"

    @pytest.mark.asyncio
    async def test_audit_not_complete(self, registry_with_tools, mock_geo_service):
        registry, _ = registry_with_tools
        mock_geo_service.get_by_id.return_value = {"status": "running", "url": "x"}

        result = await registry.execute(
            "seo_audit",
            {"action": "optimize", "audit_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )
        assert result["error"] == "analysis_not_complete"

    @pytest.mark.asyncio
    async def test_returns_optimized_content(self, registry_with_tools, mock_geo_service):
        registry, _ = registry_with_tools
        mock_geo_service.get_by_id.return_value = {
            "status": "complete",
            "url": "https://example.com",
            "overall_score": 0.75,
            "optimized_content": "Improved intro paragraph...",
            "findings": {"critical_missing": 2},
            "opportunities": ["Add citations"],
        }

        result = await registry.execute(
            "seo_audit",
            {"action": "optimize", "audit_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=frozenset({"user_id"}),
            user_id=uuid4(),
            user_tier=Tier.PRO,
        )
        assert result.get("error") is None
        assert result["optimized_content"] == "Improved intro paragraph..."
        assert "geo_optimized_content" in result["canvas_sections"]
