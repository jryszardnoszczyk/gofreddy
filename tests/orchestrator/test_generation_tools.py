"""Tests for generation-related agent tool handlers (consolidated tools)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.billing.tiers import Tier
from src.generation.exceptions import (
    GenerationConcurrentLimitExceeded,
    GenerationDailySpendLimitExceeded,
    IdeationError,
)
from src.generation.models import Cadre, CompositionSpec
from src.orchestrator.tools import build_default_registry
from src.schemas import CreativePatterns

_PASSTHROUGH = frozenset({"user_id"})


def _make_patterns(**overrides) -> CreativePatterns:
    defaults = {
        "hook_type": "question",
        "narrative_structure": "tutorial",
        "cta_type": "follow",
        "cta_placement": "end",
        "pacing": "fast_cut",
        "music_usage": "trending_audio",
        "text_overlay_density": "moderate",
        "transcript_summary": "Test transcript",
        "story_arc": "Setup then resolution",
        "emotional_journey": "curiosity to satisfaction",
        "protagonist": "Test subject",
        "theme": "Test theme",
        "visual_style": "Close-up shots",
        "audio_style": "Clear voiceover",
        "scene_beat_map": "(1) HOOK 0-3s: close_up static",
    }
    defaults.update(overrides)
    return CreativePatterns(**defaults)


def _make_spec(n_cadres=3, duration=5) -> CompositionSpec:
    return CompositionSpec(
        cadres=[
            Cadre(index=i, prompt=f"Shot {i}: dynamic content", duration_seconds=duration)
            for i in range(n_cadres)
        ],
        resolution="720p",
    )


@pytest.fixture
def mock_generation_service():
    svc = MagicMock()
    svc.submit_job = AsyncMock(return_value={
        "job_id": uuid4(),
        "status": "pending",
        "cadre_count": 3,
        "estimated_cost_cents": 15,
    })
    svc.get_job_status = AsyncMock(return_value={
        "job_id": uuid4(),
        "status": "generating",
        "current_cadre": 1,
        "total_cadres": 3,
        "video_url": None,
        "error": None,
        "cadre_statuses": [],
        "cost_cents": 5,
    })
    svc.cancel_job = AsyncMock(return_value={
        "job_id": uuid4(),
        "status": "cancelled",
    })
    svc.list_jobs = AsyncMock(return_value={
        "jobs": [{"job_id": str(uuid4()), "status": "completed"}],
        "total": 1,
    })
    return svc


@pytest.fixture
def mock_idea_service():
    svc = MagicMock()
    svc.generate_spec = AsyncMock(return_value=_make_spec())
    svc.build_spec_summary = MagicMock(return_value="3-shot cut: question hook -> follow CTA")
    return svc


@pytest.fixture
def mock_creative_service():
    svc = MagicMock()
    svc.get_creative_patterns = AsyncMock(return_value=_make_patterns())
    return svc


def _build_registry(
    generation_service,
    idea_service,
    creative_service,
    tier=Tier.PRO,
):
    registry, restricted = build_default_registry(
        generation_service=generation_service,
        idea_service=idea_service,
        creative_service=creative_service,
        tier=tier,
    )
    return registry, restricted


class TestRegistration:
    def test_pro_tier_registers_tools(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service, Tier.PRO)
        assert "video_project" in registry.names
        assert "manage_generation_jobs" not in registry.names  # absorbed into manage_video_project

    def test_free_tier_restricts_tools(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, restricted = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service, Tier.FREE)
        assert "video_project" not in registry.names
        assert "video_project" in restricted

    def test_none_services_skips_tools(self):
        registry, restricted = build_default_registry(
            generation_service=None,
            idea_service=None,
            tier=Tier.PRO,
        )
        assert "video_project" not in registry.names
        assert "video_project" not in restricted


class TestGenerateVideoHandler:
    @pytest.mark.asyncio
    async def test_success(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)
        analysis_id = str(uuid4())
        user_id = str(uuid4())

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": analysis_id, "topic": "cooking tutorial", "style": "cinematic", "user_id": user_id},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "job_id" in result
        assert result["status"] == "pending"
        assert "spec_summary" in result
        mock_creative_service.get_creative_patterns.assert_awaited_once()
        mock_idea_service.generate_spec.assert_awaited_once()
        mock_generation_service.submit_job.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_multiple_analysis_ids(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)
        ids = f"{uuid4()},{uuid4()},{uuid4()}"
        user_id = str(uuid4())

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": ids, "topic": "fitness", "style": "vlog", "user_id": user_id},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "job_id" in result
        assert mock_creative_service.get_creative_patterns.await_count == 3

    @pytest.mark.asyncio
    async def test_no_patterns_found(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_creative_service.get_creative_patterns = AsyncMock(return_value=None)
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": str(uuid4()), "topic": "test", "style": "test", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "patterns_not_found"
        mock_idea_service.generate_spec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_direct_prompt_without_analysis_ids(
        self, mock_generation_service, mock_idea_service, mock_creative_service
    ):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "topic": "sunrise over mountains", "style": "cinematic", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "job_id" in result
        assert result["generation_mode"] == "direct_prompt"
        mock_creative_service.get_creative_patterns.assert_not_awaited()
        mock_idea_service.generate_spec.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_too_many_ids(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)
        ids = ",".join(str(uuid4()) for _ in range(11))

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": ids, "topic": "test", "style": "test", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "analysis_error"

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_generation_service.submit_job = AsyncMock(
            side_effect=GenerationConcurrentLimitExceeded("limit")
        )
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": str(uuid4()), "topic": "test", "style": "test", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "generation_quota_exceeded"

    @pytest.mark.asyncio
    async def test_daily_spend_limit(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_generation_service.submit_job = AsyncMock(
            side_effect=GenerationDailySpendLimitExceeded("limit")
        )
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": str(uuid4()), "topic": "test", "style": "test", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "daily_spend_limit"

    @pytest.mark.asyncio
    async def test_ideation_error(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_idea_service.generate_spec = AsyncMock(
            side_effect=IdeationError("bad patterns")
        )
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": str(uuid4()), "topic": "test", "style": "test", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "ideation_failed"

    @pytest.mark.asyncio
    async def test_no_user_id(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "generate", "analysis_ids": str(uuid4()), "topic": "test", "style": "test"},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "internal_error"


class TestGenerationStatusHandler:
    @pytest.mark.asyncio
    async def test_success(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)
        job_id = str(uuid4())

        result = await registry.execute(
            "video_project",
            {"action": "job_status", "job_id": job_id, "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["status"] == "generating"
        assert result["current_cadre"] == 1

    @pytest.mark.asyncio
    async def test_stringifies_video_project_id(self, mock_generation_service, mock_idea_service, mock_creative_service):
        project_id = uuid4()
        mock_generation_service.get_job_status = AsyncMock(return_value={
            "job_id": uuid4(),
            "status": "generating",
            "current_cadre": 1,
            "total_cadres": 3,
            "video_project_id": project_id,
            "video_url": None,
            "error": None,
            "cadre_statuses": [],
            "cost_cents": 5,
        })
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_status", "job_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["video_project_id"] == str(project_id)

    @pytest.mark.asyncio
    async def test_not_found(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_generation_service.get_job_status = AsyncMock(return_value=None)
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_status", "job_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "not_found"

    @pytest.mark.asyncio
    async def test_invalid_uuid(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_status", "job_id": "not-a-uuid", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "analysis_error"


class TestCancelGenerationHandler:
    @pytest.mark.asyncio
    async def test_success(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_cancel", "job_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["cancelled"] is True

    @pytest.mark.asyncio
    async def test_already_terminal(self, mock_generation_service, mock_idea_service, mock_creative_service):
        mock_generation_service.cancel_job = AsyncMock(return_value=None)
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_cancel", "job_id": str(uuid4()), "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "job_already_terminal"


class TestListGenerationJobsHandler:
    @pytest.mark.asyncio
    async def test_success(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_list", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["total"] == 1
        assert len(result["jobs"]) == 1

    @pytest.mark.asyncio
    async def test_with_status_filter(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_list", "status": "completed", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert "total" in result
        mock_generation_service.list_jobs.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_status(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        result = await registry.execute(
            "video_project",
            {"action": "job_list", "status": "invalid_status", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        assert result["error"] == "analysis_error"

    @pytest.mark.asyncio
    async def test_limit_clamped(self, mock_generation_service, mock_idea_service, mock_creative_service):
        registry, _ = _build_registry(mock_generation_service, mock_idea_service, mock_creative_service)

        await registry.execute(
            "video_project",
            {"action": "job_list", "limit": "100", "user_id": str(uuid4())},
            _passthrough=_PASSTHROUGH,
            user_tier=Tier.PRO,
        )

        # Verify limit was clamped to 20
        call_args = mock_generation_service.list_jobs.call_args
        assert call_args[0][2] == 20  # third positional arg is limit
