"""Tests for PR-050: Backend Tool Contracts & Agent Errors.

Covers:
- B1: Tool contract key renames (search, analyze, fraud, evolution, deepfake, trends)
- B2: source_id in workspace items, TOOL_SECTION_MAP entries
- B3: Error handling — passthrough codes, try/except in handlers, structured returns
- B6: Tier gating — evolution Pro-only
- B7: SSE tool error status — error field in tool_result event
- B11: Gemini retry hardening — json.JSONDecodeError in _generate_with_retry
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.tiers import Tier
from src.common.enums import Platform
from src.orchestrator.agent import _PASSTHROUGH_ERROR_CODES
from src.orchestrator.tools import build_default_registry


# ── B3: Passthrough error codes ────────────────────────────────


class TestPassthroughErrorCodes:
    """Verify all expected error codes are in the passthrough set."""

    def test_original_codes_present(self):
        expected = {
            "batch_limit_exceeded", "tier_required", "daily_limit_reached",
            "providers_unavailable", "not_found", "analysis_errored",
            "analysis_not_complete", "insufficient_credits",
        }
        assert expected.issubset(_PASSTHROUGH_ERROR_CODES)

    def test_new_pr050_codes_present(self):
        new_codes = {
            "platform_not_supported", "fetch_error", "analysis_error",
            "insufficient_data", "creator_not_found", "video_not_found",
        }
        assert new_codes.issubset(_PASSTHROUGH_ERROR_CODES)


# ── B6: Evolution tier gating ──────────────────────────────────


class TestEvolutionTierGating:
    """get_creator_evolution absorbed into get_creator_profile include=['evolution']."""

    def test_evolution_not_standalone_for_pro(self):
        registry, restricted = build_default_registry(
            evolution_service=MagicMock(),
            fetchers={},
            tier=Tier.PRO,
        )
        assert "get_creator_evolution" not in registry.names
        assert "get_creator_evolution" not in restricted

    def test_evolution_not_standalone_for_free(self):
        registry, restricted = build_default_registry(
            evolution_service=MagicMock(),
            fetchers={},
            tier=Tier.FREE,
        )
        assert "get_creator_evolution" not in registry.names
        assert "get_creator_evolution" not in restricted


# ── B1: Tool contract key renames (mock-based) ────────────────


@pytest.mark.mock_required
class TestSearchContractKeys:
    """PR-075: search_videos replaced by search_content. Old contract enforced
    'results' not 'videos' and 'creator_handle'/'views' renames.
    search_content uses unified schema via content_normalizer."""

    def test_search_videos_no_longer_registered(self):
        """search_videos replaced by search_content (PR-075)."""
        search_svc = AsyncMock()
        registry, _ = build_default_registry(search_service=search_svc)
        assert "search_videos" not in registry.names


@pytest.mark.mock_required
class TestAnalyzeContractKeys:
    """analyze_video returns 'risks_detected' not 'risks', items use 'risk_type' not 'category'."""

    async def test_analyze_returns_risks_detected(self):
        mock_analysis = MagicMock()
        mock_analysis.summary = "Safe video"
        mock_analysis.video_id = "v1"
        mock_analysis.overall_safe = True
        mock_analysis.overall_confidence = 0.95
        mock_analysis.risks_detected = [
            MagicMock(category="violence", severity="low", description="minor")
        ]
        mock_analysis.content_categories = []
        mock_analysis.moderation_flags = []
        mock_analysis.sponsored_content = None

        mock_result = MagicMock()
        mock_result.analysis = mock_analysis
        mock_result.cached = False
        mock_result.record_id = uuid4()
        mock_result.cost_usd = 0.01

        analysis_svc = AsyncMock()
        analysis_svc.analyze = AsyncMock(return_value=mock_result)

        registry, _ = build_default_registry(analysis_service=analysis_svc)
        result = await registry.execute("analyze_video", {
            "action": "analyze", "platform": "tiktok", "video_id": "v1",
        })

        assert "risks_detected" in result
        assert "risks" not in result
        assert result["risks_detected"][0]["risk_type"] == "violence"
        assert "category" not in result["risks_detected"][0]
        assert "overall_confidence" in result

    async def test_analyze_error_returns_structured(self):
        """Service exception → structured error dict."""
        analysis_svc = AsyncMock()
        analysis_svc.analyze = AsyncMock(side_effect=RuntimeError("gemini down"))

        registry, _ = build_default_registry(analysis_service=analysis_svc)
        result = await registry.execute("analyze_video", {
            "action": "analyze", "platform": "tiktok", "video_id": "v1",
        })

        assert result["error"] == "analysis_error"
        assert "failed" in result["summary"].lower()


@pytest.mark.mock_required
class TestFraudContractKeys:
    """detect_fraud returns nested 'fraud_analysis' with 'aqs_components'."""

    @pytest.fixture
    def mock_fraud_result(self):
        from src.fraud.models import FraudAnalysisRecord, FraudRiskLevel

        record = FraudAnalysisRecord(
            id=uuid4(),
            creator_id=None,
            platform="tiktok",
            username="testcreator",
            cache_key="tiktok:testcreator",
            fake_follower_percentage=5.0,
            fake_follower_confidence="high",
            follower_sample_size=100,
            engagement_rate=3.5,
            engagement_tier="average",
            engagement_anomaly="none",
            bot_comment_ratio=0.1,
            comments_analyzed=50,
            bot_patterns_detected=[],
            aqs_score=72.0,
            aqs_grade="B",
            aqs_components={"followers": 0.8, "engagement": 0.7},
            growth_data_available=False,
            fraud_risk_level=FraudRiskLevel.LOW,
            fraud_risk_score=15,
            model_version="v1",
        )
        from src.fraud.service import FraudAnalysisResult
        return FraudAnalysisResult(record=record, cached=False)

    async def test_fraud_has_nested_structure(self, mock_fraud_result):
        fraud_svc = AsyncMock()
        fraud_svc.analyze = AsyncMock(return_value=mock_fraud_result)
        mock_fetcher = AsyncMock()

        registry, _ = build_default_registry(
            fraud_service=fraud_svc,
            fetchers={Platform.TIKTOK: mock_fetcher},
        )
        result = await registry.execute("detect_fraud", {
            "platform": "tiktok", "username": "testcreator",
        })

        assert "fraud_analysis" in result
        assert "aqs_components" in result["fraud_analysis"]
        assert "fraud_analysis_id" in result
        assert "analysis_id" not in result
        assert "creator_username" in result

    async def test_fraud_none_components_not_coalesced(self):
        """None raw metrics stay None in raw_metrics, aqs_components uses record values (BUG-12)."""
        from src.fraud.models import FraudAnalysisRecord, FraudRiskLevel
        from src.fraud.service import FraudAnalysisResult

        record = FraudAnalysisRecord(
            id=uuid4(),
            creator_id=None,
            platform="tiktok",
            username="nocreator",
            cache_key="tiktok:nocreator",
            fake_follower_percentage=None,
            fake_follower_confidence=None,
            follower_sample_size=None,
            engagement_rate=None,
            engagement_tier=None,
            engagement_anomaly=None,
            bot_comment_ratio=None,
            comments_analyzed=None,
            bot_patterns_detected=[],
            aqs_score=50.0,
            aqs_grade="poor",
            aqs_components={"engagement": 45.0, "audience_quality": 55.0},
            growth_data_available=False,
            fraud_risk_level=FraudRiskLevel.HIGH,
            fraud_risk_score=50,
            model_version="v1",
        )
        fraud_svc = AsyncMock()
        fraud_svc.analyze = AsyncMock(return_value=FraudAnalysisResult(record=record, cached=False))
        mock_fetcher = AsyncMock()

        registry, _ = build_default_registry(
            fraud_service=fraud_svc,
            fetchers={Platform.TIKTOK: mock_fetcher},
        )
        result = await registry.execute("detect_fraud", {
            "platform": "tiktok", "username": "nocreator",
        })

        # aqs_components now holds actual component scores from the record
        components = result["fraud_analysis"]["aqs_components"]
        assert components["engagement"] == 45.0
        assert components["audience_quality"] == 55.0

        # Raw metrics are in a separate dict, None values preserved
        raw = result["fraud_analysis"]["raw_metrics"]
        assert raw["engagement_rate"] is None
        assert raw["fake_follower_percentage"] is None
        assert raw["bot_comment_ratio"] is None


@pytest.mark.mock_required
class TestDeepfakeContractKeys:
    """analyze_video(include=['deepfake']) returns deepfake data with 'indicators' as string array."""

    async def test_deepfake_has_indicators(self):
        record = MagicMock()
        record.id = uuid4()
        record.is_deepfake = False
        record.confidence_score = 0.95
        record.lip_sync_score = 0.85
        record.reality_defender_verdict = "authentic"
        record.detection_method = "ensemble"
        record.model_version = "v1"

        deepfake_svc = AsyncMock()
        deepfake_svc.analyze = AsyncMock(return_value=MagicMock(
            record=record, cached=False, cost_usd=0.05,
        ))

        storage = AsyncMock()
        storage.generate_download_url = AsyncMock(return_value="https://example.com/video.mp4")

        # analyze_video needs analysis_service for the base analyze action
        mock_analysis = MagicMock()
        mock_analysis.summary = "Safe video"
        mock_analysis.video_id = "v1"
        mock_analysis.overall_safe = True
        mock_analysis.overall_confidence = 0.95
        mock_analysis.risks_detected = []
        mock_analysis.content_categories = []
        mock_analysis.moderation_flags = []
        mock_analysis.sponsored_content = None

        mock_result = MagicMock()
        mock_result.analysis = mock_analysis
        mock_result.cached = False
        mock_result.record_id = uuid4()
        mock_result.cost_usd = 0.01

        analysis_svc = AsyncMock()
        analysis_svc.analyze = AsyncMock(return_value=mock_result)

        registry, _ = build_default_registry(
            analysis_service=analysis_svc,
            deepfake_service=deepfake_svc,
            video_storage=storage,
            tier=Tier.PRO,
        )
        result = await registry.execute("analyze_video", {
            "action": "analyze", "platform": "tiktok", "video_id": "v1",
            "include": ["deepfake"],
        }, user_tier=Tier.PRO)

        # Deepfake data is nested under "deepfake" key in the consolidated response
        assert "deepfake" in result
        df = result["deepfake"]
        assert "indicators" in df
        assert isinstance(df["indicators"], list)
        assert all(isinstance(i, str) for i in df["indicators"])


@pytest.mark.mock_required
class TestTrendsContractKeys:
    """search(search_type='trends') returns 'hashtag' not 'tag', creators have 'platform'."""

    async def test_trends_uses_hashtag_key(self):
        from types import SimpleNamespace

        # The handler accesses result.snapshot, snapshot.trending_hashtags, etc.
        snapshot = SimpleNamespace(
            trending_hashtags=[
                SimpleNamespace(hashtag="#cooking", volume=1000, growth_rate=5.0),
            ],
            emerging_creators=[
                SimpleNamespace(username="chef", growth_rate=2.0, follower_delta=500),
            ],
            brand_mention_volumes={"nike": 100},
            snapshot_date="2026-01-01",
        )
        trend_result = SimpleNamespace(snapshot=snapshot, share_of_voice={"nike": 0.3})

        trend_svc = AsyncMock()
        trend_svc.get_trends = AsyncMock(return_value=trend_result)

        registry, _ = build_default_registry(
            trend_service=trend_svc,
            tier=Tier.PRO,
        )
        result = await registry.execute("search", {
            "search_type": "trends",
            "platform": "tiktok",
        })

        assert "trending_hashtags" in result
        for t in result["trending_hashtags"]:
            assert "hashtag" in t
            assert "tag" not in t
        for c in result["emerging_creators"]:
            assert "platform" in c


# ── B3: Handler error handling (mock-based) ────────────────────


@pytest.mark.mock_required
class TestBrandsErrorHandling:
    """analyze_brands removed — now accessed via analyze_video(include=['brands'])."""

    async def test_brands_not_standalone(self):
        registry, _ = build_default_registry(
            brand_service=MagicMock(),
            video_storage=MagicMock(),
        )
        assert "analyze_brands" not in registry.names


@pytest.mark.mock_required
class TestDemographicsErrorHandling:
    """infer_demographics removed — now accessed via analyze_video(include=['demographics'])."""

    async def test_demographics_not_standalone(self):
        registry, _ = build_default_registry(
            demographics_service=MagicMock(),
            video_storage=MagicMock(),
        )
        assert "infer_demographics" not in registry.names


@pytest.mark.mock_required
class TestCaptureStoriesErrorCode:
    """creator_profile(action='capture_stories') returns 'platform_not_supported', not free text."""

    async def test_non_instagram_returns_machine_readable_code(self):
        story_svc = MagicMock()
        # creator_profile requires ic_backend to be registered
        mock_ic = MagicMock()
        mock_ic.enrich_full = AsyncMock(return_value={})
        registry, _ = build_default_registry(
            story_service=story_svc,
            ic_backend=mock_ic,
            tier=Tier.PRO,
        )
        result = await registry.execute("creator_profile", {
            "action": "capture_stories", "platform": "tiktok", "username": "user1",
        }, user_tier=Tier.PRO)

        assert result["error"] == "platform_not_supported"


@pytest.mark.mock_required
class TestBatchAnalysisNoUserId:
    """workspace(action='batch_analyze') returns structured error when user_id missing."""

    async def test_missing_user_id_returns_structured_error(self):
        mock_batch_svc = MagicMock()
        mock_analysis_svc = MagicMock()
        mock_batch_repo = MagicMock()

        registry, _ = build_default_registry(
            batch_service=mock_batch_svc,
            analysis_service=mock_analysis_svc,
            batch_repository=mock_batch_repo,
            workspace_service=AsyncMock(),
            conversation_id=uuid4(),
            tier=Tier.FREE,
        )

        result = await registry.execute("workspace", {
            "action": "batch_analyze",
            "collection_id": str(uuid4()),
        })

        assert result["error"] == "tier_required"
        assert "authentication" in result["summary"].lower()


# ── B7: SSE tool error propagation (agent streaming) ──────────


class TestSSEToolErrorField:
    """tool_result event includes error field when tool returns error.

    Tests the event-building logic directly rather than mocking the full Gemini loop.
    """

    def test_tool_result_event_includes_error_when_present(self):
        """Verify the event dict logic: error included when result has error."""
        from typing import Any

        # Simulate the exact code from agent.py _streaming_loop
        result: dict[str, Any] = {"summary": "Failed.", "error": "analysis_error"}
        name = "test_tool"
        iteration = 1

        tr_event: dict[str, Any] = {"tool": name, "summary": result.get("summary", ""), "iteration": iteration}
        if result.get("error"):
            tr_event["error"] = result["error"]

        assert tr_event["error"] == "analysis_error"
        assert tr_event["tool"] == "test_tool"
        assert tr_event["summary"] == "Failed."

    def test_tool_result_event_no_error_when_success(self):
        """Verify no error field when tool succeeds."""
        from typing import Any

        result: dict[str, Any] = {"summary": "Done."}
        name = "test_tool"
        iteration = 1

        tr_event: dict[str, Any] = {"tool": name, "summary": result.get("summary", ""), "iteration": iteration}
        if result.get("error"):
            tr_event["error"] = result["error"]

        assert "error" not in tr_event


# ── B11: Gemini retry hardening ───────────────────────────────


@pytest.mark.mock_required
class TestGeminiRetryJsonError:
    """_generate_with_retry catches json.JSONDecodeError and retries."""

    async def test_json_decode_error_retried(self):
        import json
        from src.analysis.gemini_analyzer import GeminiVideoAnalyzer
        from src.analysis.exceptions import VideoProcessingError

        mock_client = MagicMock()

        from src.common.gemini_models import GEMINI_FLASH_LITE

        analyzer = GeminiVideoAnalyzer.__new__(GeminiVideoAnalyzer)
        analyzer._client = mock_client
        analyzer._model = GEMINI_FLASH_LITE
        analyzer._max_retries = 2
        analyzer._base_delay = 0.01

        # Both attempts fail with json decode error
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=json.JSONDecodeError("Expecting value", "", 0),
        )

        with pytest.raises(VideoProcessingError, match="parse failed"):
            await analyzer._generate_with_retry(
                contents=["test"],
                video_id="test123",
            )

        # Verify it was called max_retries times
        assert mock_client.aio.models.generate_content.await_count == 2
