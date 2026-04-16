"""Tests for TTSService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import SecretStr

from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError
from src.generation.tts_service import TTSService
from src.generation.tts_providers import TTSResult


@pytest.fixture
def settings():
    return GenerationSettings(
        generation_enabled=True,
        tts_enabled=True,
        tts_default_provider="kokoro",
        tts_max_text_length=5000,
    )


@pytest.fixture
def disabled_settings():
    return GenerationSettings(
        generation_enabled=True,
        tts_enabled=False,
    )


class TestTTSService:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_feature_flag_disabled(self, disabled_settings):
        service = TTSService(disabled_settings)
        with pytest.raises(GenerationError, match="not currently available"):
            await service.synthesize("Hello world")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_text_length_limit(self, settings):
        service = TTSService(settings)
        long_text = "x" * 6000
        with pytest.raises(GenerationError, match="exceeds TTS limit"):
            await service.synthesize(long_text)

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_kokoro_success(self, settings):
        service = TTSService(settings)
        mock_result = TTSResult(
            audio_url="https://fal.media/test.mp3",
            duration_seconds=5.0,
            cost_usd=0.01,
            provider="kokoro",
        )
        with patch.object(
            service._providers["kokoro"], "synthesize",
            new_callable=AsyncMock, return_value=mock_result,
        ):
            result = await service.synthesize("Hello world")
            assert result.provider == "kokoro"
            assert result.audio_url == "https://fal.media/test.mp3"

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_fallback_chain(self, settings):
        settings_fish = GenerationSettings(
            generation_enabled=True,
            tts_enabled=True,
            tts_default_provider="fish_audio",
            fish_audio_api_key=SecretStr("test-key"),
        )
        service = TTSService(settings_fish)

        fallback_result = TTSResult(
            audio_url="https://fal.media/fallback.mp3",
            duration_seconds=3.0,
            cost_usd=0.01,
            provider="kokoro",
        )
        with patch.object(
            service._providers["fish_audio"], "synthesize",
            new_callable=AsyncMock, side_effect=GenerationError("Fish down"),
        ), patch.object(
            service._providers["kokoro"], "synthesize",
            new_callable=AsyncMock, return_value=fallback_result,
        ):
            result = await service.synthesize("Test fallback")
            assert result.provider == "kokoro"

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_all_providers_fail(self, settings):
        service = TTSService(settings)
        with patch.object(
            service._providers["kokoro"], "synthesize",
            new_callable=AsyncMock, side_effect=GenerationError("down"),
        ):
            with pytest.raises(GenerationError, match="All TTS providers failed"):
                await service.synthesize("Test all fail")
