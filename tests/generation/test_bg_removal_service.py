"""Tests for BackgroundRemovalService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.generation.bg_removal_service import BackgroundRemovalService, _validate_url_domain
from src.generation.config import GenerationSettings
from src.generation.exceptions import GenerationError


@pytest.fixture
def settings():
    return GenerationSettings(generation_enabled=True, bg_removal_enabled=True)


@pytest.fixture
def disabled_settings():
    return GenerationSettings(generation_enabled=True, bg_removal_enabled=False)


class TestBGRemovalService:
    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_image_feature_flag_disabled(self, disabled_settings):
        fal = MagicMock()
        service = BackgroundRemovalService(fal_client=fal, settings=disabled_settings)
        with pytest.raises(GenerationError, match="not currently available"):
            await service.remove_bg_image("https://v3.fal.media/test.jpg")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_video_feature_flag_disabled(self, disabled_settings):
        fal = MagicMock()
        service = BackgroundRemovalService(fal_client=fal, settings=disabled_settings)
        with pytest.raises(GenerationError, match="not currently available"):
            await service.remove_bg_video("https://v3.fal.media/test.mp4")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_ssrf_rejection(self, settings):
        fal = MagicMock()
        service = BackgroundRemovalService(fal_client=fal, settings=settings)
        with pytest.raises(GenerationError, match="domain not allowed"):
            await service.remove_bg_image("https://evil.com/test.jpg")

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_image_removal_success(self, settings):
        import sys
        fal = MagicMock()
        service = BackgroundRemovalService(fal_client=fal, settings=settings)
        mock_fal = MagicMock()
        mock_fal.subscribe_async = AsyncMock(return_value={
            "image": {"url": "https://v3.fal.media/output.png"},
        })
        with patch.dict(sys.modules, {"fal_client": mock_fal}):
            result = await service.remove_bg_image("https://v3.fal.media/test.jpg")
            assert result.output_url == "https://v3.fal.media/output.png"
            assert result.cost_usd == pytest.approx(0.018)

    @pytest.mark.asyncio
    @pytest.mark.mock_required
    async def test_video_removal_success(self, settings):
        import sys
        fal = MagicMock()
        service = BackgroundRemovalService(fal_client=fal, settings=settings)
        mock_fal = MagicMock()
        mock_fal.subscribe_async = AsyncMock(return_value={
            "video": {"url": "https://v3.fal.media/output.mp4"},
        })
        with patch.dict(sys.modules, {"fal_client": mock_fal}):
            result = await service.remove_bg_video("https://v3.fal.media/test.mp4")
            assert result.output_url == "https://v3.fal.media/output.mp4"
