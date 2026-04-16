"""Tests for evaluate_policy agent tool."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.analysis.models import VideoAnalysisRecord
from src.billing.tiers import Tier
from src.orchestrator.tools import build_default_registry
from src.policies.models import BrandPolicyResponse, PolicyRule
from src.policies.service import PolicyNotFoundError
from src.schemas import ModerationClass, Severity


def _make_analysis_record(**overrides):
    defaults = {
        "id": uuid4(),
        "video_id": uuid4(),
        "cache_key": "tiktok:123456:v1",
        "overall_safe": True,
        "overall_confidence": 0.95,
        "risks_detected": [],
        "summary": "Test summary",
        "content_categories": [],
        "moderation_flags": [
            {
                "moderation_class": "hate_speech",
                "severity": "high",
                "confidence": 0.9,
                "timestamp_start": None,
                "timestamp_end": None,
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


def _make_policy(user_id=None, name="Test Policy", rules=None):
    return BrandPolicyResponse(
        id=uuid4(),
        user_id=user_id,
        policy_name=name,
        rules=rules or [
            PolicyRule(
                moderation_class=ModerationClass.HATE_SPEECH,
                max_severity=Severity.NONE,
                action="block",
            )
        ],
        is_preset=user_id is None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_analysis_repository():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=_make_analysis_record())
    repo.user_has_access = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_policy_service():
    service = MagicMock()
    service.get_policy = AsyncMock(return_value=_make_policy())
    return service


@pytest.fixture
def mock_analysis_service():
    return MagicMock()


def _build_registry(mock_analysis_repository, mock_policy_service, mock_analysis_service=None):
    registry, _ = build_default_registry(
        analysis_service=mock_analysis_service or MagicMock(),
        tier=Tier.PRO,
        analysis_repository=mock_analysis_repository,
        policy_service=mock_policy_service,
    )
    return registry


@pytest.mark.asyncio
class TestEvaluatePolicyTool:
    async def test_successful_evaluation(
        self, mock_analysis_repository, mock_policy_service, mock_analysis_service
    ):
        """Happy path: returns compact summary with verdict."""
        registry = _build_registry(mock_analysis_repository, mock_policy_service, mock_analysis_service)
        tool = registry.get("analyze_video")
        assert tool is not None

        record = _make_analysis_record()
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert "summary" in result
        assert result["overall_verdict"] == "block"  # hate_speech high > none threshold
        assert result["total_rules"] == 1
        assert len(result["failed_rules"]) == 1
        assert result["disclaimer"]

    async def test_analysis_not_found(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict, not exception."""
        mock_analysis_repository.get_by_id = AsyncMock(return_value=None)
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(uuid4()),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "not_found"

    async def test_policy_not_found(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict for missing policy."""
        mock_policy_service.get_policy = AsyncMock(side_effect=PolicyNotFoundError())
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        record = _make_analysis_record()
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "not_found"

    async def test_no_access(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict for unauthorized analysis."""
        mock_analysis_repository.user_has_access = AsyncMock(return_value=False)
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(uuid4()),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "not_found"

    async def test_errored_analysis(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict for analysis with error field set."""
        record = _make_analysis_record(error="gemini_timeout")
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "analysis_errored"

    async def test_incomplete_analysis(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict for analysis with analyzed_at=None."""
        record = _make_analysis_record(analyzed_at=None)
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "analysis_not_complete"

    async def test_missing_user_id(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Returns error dict when user_id not injected."""
        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(uuid4()),
            policy_id=str(uuid4()),
        )
        assert result["error"] == "internal_error"

    async def test_compact_summary_format(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Summary includes policy name, verdict, failed count."""
        policy = _make_policy(name="Brand Safety v2")
        mock_policy_service.get_policy = AsyncMock(return_value=policy)
        record = _make_analysis_record()
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)

        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(policy.id),
            user_id=str(uuid4()),
        )
        assert "Brand Safety v2" in result["summary"]
        assert "block" in result["summary"]
        assert result["policy_name"] == "Brand Safety v2"

    async def test_preset_policy_evaluation(
        self, mock_analysis_repository, mock_policy_service
    ):
        """Preset policy (user_id=NULL) usable by any authenticated user."""
        preset = _make_policy(user_id=None, name="Family Safe Preset")
        mock_policy_service.get_policy = AsyncMock(return_value=preset)
        record = _make_analysis_record()
        mock_analysis_repository.get_by_id = AsyncMock(return_value=record)

        registry = _build_registry(mock_analysis_repository, mock_policy_service)
        tool = registry.get("analyze_video")

        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(record.id),
            policy_id=str(preset.id),
            user_id=str(uuid4()),
        )
        assert "error" not in result
        assert result["overall_verdict"] in ("pass", "flag", "block")

    async def test_policy_unavailable_without_policy_service(
        self, mock_analysis_repository
    ):
        """Returns service_unavailable when policy_service is None."""
        registry, _ = build_default_registry(
            analysis_service=MagicMock(),
            tier=Tier.PRO,
            analysis_repository=mock_analysis_repository,
            # policy_service=None (default)
        )
        tool = registry.get("analyze_video")
        assert tool is not None
        result = await tool.handler(
            action="get_report",
            report_type="policy",
            analysis_id=str(uuid4()),
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
        )
        assert result["error"] == "service_unavailable"
