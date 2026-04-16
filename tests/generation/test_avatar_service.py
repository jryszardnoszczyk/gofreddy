"""Tests for AvatarService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.generation.avatar_service import AvatarService, _validate_url_domain
from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError


@pytest.fixture
def settings():
    return GenerationSettings(generation_enabled=True, avatar_enabled=True)


@pytest.fixture
def disabled_settings():
    return GenerationSettings(generation_enabled=True, avatar_enabled=False)


class TestURLValidation:
    def test_allowed_domain(self):
        _validate_url_domain("https://v3.fal.media/files/test.mp4")

    def test_blocked_domain(self):
        with pytest.raises(GenerationError, match="domain not allowed"):
            _validate_url_domain("https://evil.com/test.mp4")

    def test_insecure_scheme(self):
        with pytest.raises(GenerationError, match="Insecure URL"):
            _validate_url_domain("http://v3.fal.media/test.mp4")


class TestAvatarService:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_feature_flag_disabled(self, disabled_settings):
        fal = MagicMock()
        service = AvatarService(fal_client=fal, settings=disabled_settings)
        with pytest.raises(GenerationError, match="not currently available"):
            await service.generate_talking_video(
                "https://v3.fal.media/face.jpg",
                "https://v3.fal.media/audio.mp3",
            )

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_ssrf_rejection(self, settings):
        fal = MagicMock()
        service = AvatarService(fal_client=fal, settings=settings)
        with pytest.raises(GenerationError, match="domain not allowed"):
            await service.generate_talking_video(
                "https://evil.com/face.jpg",
                "https://v3.fal.media/audio.mp3",
            )

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_success(self, settings):
        import sys
        mock_fal = MagicMock()
        mock_fal.subscribe_async = AsyncMock(return_value={
            "video": {"url": "https://v3.fal.media/result.mp4"},
        })
        fal = MagicMock()
        service = AvatarService(fal_client=fal, settings=settings)
        with patch.dict(sys.modules, {"fal_client": mock_fal}):
            result = await service.generate_talking_video(
                "https://v3.fal.media/face.jpg",
                "https://v3.fal.media/audio.mp3",
                duration_seconds=10,
            )
            assert result.video_url == "https://v3.fal.media/result.mp4"
            assert result.cost_usd == pytest.approx(0.56)
