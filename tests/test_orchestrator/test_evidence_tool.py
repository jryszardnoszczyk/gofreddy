"""Tests for get_evidence_timeline agent tool."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.analysis.models import VideoAnalysisRecord
from src.orchestrator.tools import build_default_registry
from src.billing.tiers import Tier
from datetime import UTC, datetime


def _make_analysis_record(**overrides):
    defaults = {
        "id": uuid4(),
        "video_id": uuid4(),
        "cache_key": "tiktok:123456:v1",
        "overall_safe": True,
        "overall_confidence": 0.95,
        "risks_detected": [
            {
                "category": "violence",
                "severity": "high",
                "confidence": 0.9,
                "timestamp_start": "1:00",
                "timestamp_end": "1:30",
                "description": "Violence detected",
                "evidence": "Violent scene",
            }
        ],
        "summary": "Test summary",
        "content_categories": [],
        "moderation_flags": [
            {
                "moderation_class": "hate_speech",
                "severity": "medium",
                "confidence": 0.8,
                "timestamp_start": "2:00",
                "timestamp_end": "2:30",
                "description": "Hate speech",
                "evidence": "Offensive language",
            }
        ],
        "sponsored_content": None,
        "processing_time_seconds": 1.5,
        "token_count": 1000,
        "error": None,
        "model_version": "1",
        "analyzed_at": datetime.now(UTC),
        "analysis_cost_usd": 0.001,
    }
    defaults.update(overrides)
    return VideoAnalysisRecord(**defaults)


@pytest.fixture
def mock_analysis_service():
    service = MagicMock()
    service.get_by_id = AsyncMock(return_value=_make_analysis_record())
    return service


@pytest.fixture
def mock_analysis_repository():
    repo = MagicMock()
    repo.user_has_access = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_brand_service():
    service = MagicMock()
    service.get_brand_analysis = AsyncMock(return_value=None)
    return service


@pytest.mark.asyncio
class TestEvidenceToolHappyPath:
    async def test_returns_top_findings(
        self, mock_analysis_service, mock_analysis_repository, mock_brand_service
    ):
        registry, _ = build_default_registry(
            analysis_service=mock_analysis_service,
            brand_service=mock_brand_service,
            tier=Tier.PRO,
            analysis_repository=mock_analysis_repository,
        )
        tool = registry.get("analyze_video")
        assert tool is not None

        record = _make_analysis_record()
        mock_analysis_service.get_by_id = AsyncMock(return_value=record)

        result = await tool.handler(
            action="get_report",
            report_type="evidence_timeline",
            analysis_id=str(record.id),
            user_id=str(uuid4()),
        )
        assert "summary" in result
        assert result["total_groups"] > 0
        assert "top_findings" in result
        assert len(result["top_findings"]) <= 10

    async def test_not_found(
        self, mock_analysis_service, mock_analysis_repository, mock_brand_service
    ):
        mock_analysis_service.get_by_id = AsyncMock(return_value=None)
        registry, _ = build_default_registry(
            analysis_service=mock_analysis_service,
            brand_service=mock_brand_service,
            tier=Tier.PRO,
            analysis_repository=mock_analysis_repository,
        )
        tool = registry.get("analyze_video")
        result = await tool.handler(
            action="get_report",
            report_type="evidence_timeline",
            analysis_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "not_found"

    async def test_no_access(
        self, mock_analysis_service, mock_analysis_repository, mock_brand_service
    ):
        mock_analysis_repository.user_has_access = AsyncMock(return_value=False)
        registry, _ = build_default_registry(
            analysis_service=mock_analysis_service,
            brand_service=mock_brand_service,
            tier=Tier.PRO,
            analysis_repository=mock_analysis_repository,
        )
        tool = registry.get("analyze_video")
        result = await tool.handler(
            action="get_report",
            report_type="evidence_timeline",
            analysis_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "not_found"

    async def test_severity_sorting(
        self, mock_analysis_service, mock_analysis_repository, mock_brand_service
    ):
        """Critical findings should be ranked above high, medium, low."""
        record = _make_analysis_record(
            risks_detected=[
                {
                    "category": "violence",
                    "severity": "low",
                    "confidence": 0.9,
                    "timestamp_start": "0:10",
                    "timestamp_end": None,
                    "description": "Low severity",
                    "evidence": "Minor",
                },
                {
                    "category": "violence",
                    "severity": "critical",
                    "confidence": 0.95,
                    "timestamp_start": "0:20",
                    "timestamp_end": None,
                    "description": "Critical severity",
                    "evidence": "Major",
                },
            ],
            moderation_flags=[],
        )
        mock_analysis_service.get_by_id = AsyncMock(return_value=record)

        registry, _ = build_default_registry(
            analysis_service=mock_analysis_service,
            brand_service=mock_brand_service,
            tier=Tier.PRO,
            analysis_repository=mock_analysis_repository,
        )
        tool = registry.get("analyze_video")
        result = await tool.handler(
            action="get_report",
            report_type="evidence_timeline",
            analysis_id=str(record.id),
            user_id=str(uuid4()),
        )
        findings = result["top_findings"]
        assert len(findings) == 2
        assert findings[0]["severity"] == "critical"
        assert findings[1]["severity"] == "low"

    async def test_get_report_unavailable_without_repository(
        self, mock_analysis_service, mock_brand_service
    ):
        """get_report action returns service_unavailable when analysis_repository is None."""
        registry, _ = build_default_registry(
            analysis_service=mock_analysis_service,
            brand_service=mock_brand_service,
            tier=Tier.PRO,
            # No analysis_repository
        )
        tool = registry.get("analyze_video")
        assert tool is not None  # analyze_video is always registered
        result = await tool.handler(
            action="get_report",
            report_type="evidence_timeline",
            analysis_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "service_unavailable"
