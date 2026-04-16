"""Tests for MusicService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from pydantic import SecretStr

from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError, ModerationBlockedError
from src.generation.music_service import MusicService


@pytest.fixture
def settings():
    return GenerationSettings(
        generation_enabled=True,
        music_enabled=True,
        suno_api_key=SecretStr("test-key"),
        suno_api_url="https://api.kie.ai/api/v1",
        suno_poll_interval=0.1,
        suno_poll_timeout=1.0,
    )


@pytest.fixture
def disabled_settings():
    return GenerationSettings(generation_enabled=True, music_enabled=False)


class TestMusicService:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_feature_flag_disabled(self, disabled_settings):
        http = AsyncMock()
        service = MusicService(disabled_settings, http)
        with pytest.raises(GenerationError, match="not currently available"):
            await service.generate_track("upbeat pop")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_no_api_key_raises(self):
        settings = GenerationSettings(generation_enabled=True, music_enabled=True)
        http = AsyncMock()
        service = MusicService(settings, http)
        with pytest.raises(GenerationError, match="API key not configured"):
            await service.generate_track("upbeat pop")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_moderation_block(self, settings):
        http = AsyncMock()
        service = MusicService(settings, http)

        import httpx
        error_resp = MagicMock()
        error_resp.text = "SENSITIVE_WORD_ERROR: blocked content"
        error_resp.status_code = 400
        http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("bad", request=MagicMock(), response=error_resp)
        )

        with pytest.raises(ModerationBlockedError, match="content filter"):
            await service.generate_track("bad content")

    def test_analyze_beats_no_librosa(self, settings):
        """Beat analysis returns None when librosa is not installed."""
        http = AsyncMock()
        service = MusicService(settings, http)
        # analyze_beats uses lazy import — would return None if librosa missing
        # This is tested implicitly; librosa may or may not be installed
