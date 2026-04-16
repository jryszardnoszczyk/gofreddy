"""Tests for IdeaService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.common.gemini_models import GEMINI_FLASH
from src.generation.config import GenerationSettings
from src.generation.exceptions import IdeationError
from src.generation.idea_service import IdeaService
from src.generation.models import Cadre, CompositionSpec
from src.schemas import CreativePatterns


def _make_patterns(**overrides) -> CreativePatterns:
    defaults = {
        "hook_type": "question",
        "narrative_structure": "tutorial",
        "cta_type": "follow",
        "cta_placement": "end",
        "pacing": "fast_cut",
        "music_usage": "trending_audio",
        "text_overlay_density": "moderate",
        "transcript_summary": "Test transcript summary",
        "story_arc": "Setup leads to conflict then resolution",
        "emotional_journey": "curiosity → tension → satisfaction",
        "protagonist": "Test protagonist in casual clothing",
        "theme": "Testing creative patterns",
        "visual_style": "Close-up shots with warm lighting",
        "audio_style": "Upbeat voiceover with background music",
        "scene_beat_map": "(1) HOOK 0-3s: close_up static — opening",
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
def settings():
    return GenerationSettings(
        generation_enabled=True,
        idea_model=GEMINI_FLASH,
        idea_temperature=0.7,
        idea_max_total_duration=60,
    )


def _make_response(text: str) -> MagicMock:
    """Create a mock Gemini response with proper candidates structure."""
    candidate = MagicMock()
    candidate.finish_reason = "STOP"
    resp = MagicMock()
    resp.text = text
    resp.candidates = [candidate]
    resp.usage_metadata.prompt_token_count = 100
    resp.usage_metadata.candidates_token_count = 50
    resp.usage_metadata.cached_content_token_count = 0
    return resp


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client, settings):
    return IdeaService(client=mock_client, settings=settings)


class TestGenerateSpec:
    @pytest.mark.asyncio
    async def test_success(self, service, mock_client):
        spec = _make_spec(3, 5)
        mock_response = _make_response(spec.model_dump_json())

        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        patterns = [_make_patterns()]
        result = await service.generate_spec(patterns, "cooking tutorial", "cinematic")

        assert isinstance(result, CompositionSpec)
        assert len(result.cadres) == 3
        mock_client.aio.models.generate_content.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_patterns_uses_generic_instruction(self, service, mock_client):
        spec = _make_spec(3, 5)
        mock_response = _make_response(spec.model_dump_json())
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await service.generate_spec([], "topic", "style")
        assert isinstance(result, CompositionSpec)

        # Verify system instruction includes the no-patterns suffix
        call_kwargs = mock_client.aio.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert "NO CREATOR PATTERNS AVAILABLE" in config.system_instruction

    @pytest.mark.asyncio
    async def test_accepts_many_patterns(self, service, mock_client):
        spec = _make_spec(2, 8)
        mock_response = _make_response(spec.model_dump_json())
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        patterns = [_make_patterns() for _ in range(15)]
        await service.generate_spec(patterns, "topic", "style")

        # All patterns are sent through (no cap)
        mock_client.aio.models.generate_content.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_response_raises(self, service, mock_client):
        mock_response = _make_response("")
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="Empty response"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self, service, mock_client):
        mock_response = _make_response("not valid json")
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="Invalid composition spec"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_duration_too_short_raises(self, service, mock_client):
        spec = _make_spec(1, 2)  # 2s total, below 15s min
        mock_response = _make_response(spec.model_dump_json())
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="outside allowed range"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_duration_too_long_raises(self, service, mock_client, settings):
        spec = _make_spec(6, 15)  # 90s total, above 60s max
        mock_response = _make_response(spec.model_dump_json())
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="outside allowed range"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_empty_cadre_prompt_raises(self, service, mock_client):
        spec = CompositionSpec(
            cadres=[
                Cadre(index=0, prompt="valid prompt", duration_seconds=8),
                Cadre(index=1, prompt="   ", duration_seconds=8),
            ],
            resolution="720p",
        )
        mock_response = _make_response(spec.model_dump_json())
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="Empty cadre prompt"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_safety_finish_reason_raises(self, service, mock_client):
        mock_response = _make_response('{"cadres": []}')
        mock_response.candidates[0].finish_reason = "SAFETY"
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with pytest.raises(IdeationError, match="Gemini response terminated: SAFETY"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_gemini_timeout_raises(self, service, mock_client):
        import asyncio

        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        with pytest.raises(IdeationError, match="timed out"):
            await service.generate_spec([_make_patterns()], "topic", "style")

    @pytest.mark.asyncio
    async def test_gemini_error_raises(self, service, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=RuntimeError("API error")
        )

        with pytest.raises(IdeationError, match="Gemini call failed"):
            await service.generate_spec([_make_patterns()], "topic", "style")


class TestSanitizePrompt:
    def test_strips_control_chars(self):
        from src.generation.prompt_utils import sanitize_prompt
        assert sanitize_prompt("hello\x00world\x1b") == "helloworld"

    def test_truncates_when_max_length_given(self):
        from src.generation.prompt_utils import sanitize_prompt
        assert sanitize_prompt("a" * 200, 50) == "a" * 50

    def test_no_truncation_without_max_length(self):
        from src.generation.prompt_utils import sanitize_prompt
        assert sanitize_prompt("a" * 200) == "a" * 200

    def test_empty_string(self):
        from src.generation.prompt_utils import sanitize_prompt
        assert sanitize_prompt("") == ""


class TestBuildSpecSummary:
    def test_basic_summary(self):
        spec = _make_spec(3, 5)
        patterns = [_make_patterns(hook_type="question", cta_type="follow")]
        result = IdeaService.build_spec_summary(spec, patterns)
        assert "3-shot" in result
        assert "question" in result
        assert "follow" in result

    def test_empty_patterns_fallback(self):
        spec = _make_spec(2, 5)
        result = IdeaService.build_spec_summary(spec, [])
        assert "unknown" in result
