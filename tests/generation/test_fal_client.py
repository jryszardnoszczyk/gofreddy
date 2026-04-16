"""Tests for FalPlatformClient."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.generation.config import FAL_MODELS
from src.generation.exceptions import (
    GenerationError,
    GenerationTimeoutError,
    ModerationBlockedError,
    ProviderUnavailableError,
)
from src.generation.fal_client import FalPlatformClient, _map_resolution, _round_to_even


# ─── Duration rounding ────────────────────────────────────────────────


class TestRoundToEven:
    def test_even_number_unchanged(self):
        assert _round_to_even(6) == 6
        assert _round_to_even(10) == 10
        assert _round_to_even(20) == 20

    def test_odd_rounds_up(self):
        assert _round_to_even(5) == 6
        assert _round_to_even(7) == 8
        assert _round_to_even(11) == 12
        assert _round_to_even(19) == 20

    def test_minimum_is_6(self):
        assert _round_to_even(1) == 6
        assert _round_to_even(2) == 6
        assert _round_to_even(3) == 6
        assert _round_to_even(4) == 6
        assert _round_to_even(5) == 6

    def test_clamped_to_max(self):
        assert _round_to_even(21, max_duration=20) == 20
        assert _round_to_even(30, max_duration=20) == 20

    def test_custom_max(self):
        assert _round_to_even(9, max_duration=10) == 10
        assert _round_to_even(11, max_duration=10) == 10


# ─── Resolution mapping ──────────────────────────────────────────────


class TestMapResolution:
    def test_480p_maps_to_1080p(self):
        assert _map_resolution("480p") == "1080p"

    def test_720p_maps_to_1080p(self):
        assert _map_resolution("720p") == "1080p"

    def test_1080p_unchanged(self):
        assert _map_resolution("1080p") == "1080p"

    def test_1440p_unchanged(self):
        assert _map_resolution("1440p") == "1440p"

    def test_2160p_unchanged(self):
        assert _map_resolution("2160p") == "2160p"

    def test_unknown_defaults_to_1080p(self):
        assert _map_resolution("4K") == "1080p"
        assert _map_resolution("") == "1080p"


# ─── FalPlatformClient ───────────────────────────────────────────────


def _make_settings(**overrides):
    """Create GenerationSettings with fal.ai config."""
    from pydantic import SecretStr
    from src.generation.config import GenerationSettings

    defaults = {
        "fal_api_key": SecretStr("test-fal-key"),
        "generation_provider": "fal",
        "fal_default_video_model": "ltx-fast",
        "fal_default_image_model": "flux-pro",
        "fal_client_timeout": 30.0,
    }
    defaults.update(overrides)
    return GenerationSettings(**defaults)


def _make_client(settings=None):
    """Create FalPlatformClient with test settings."""
    return FalPlatformClient(settings or _make_settings())


class TestGenerateClip:
    @pytest.mark.asyncio
    async def test_success_i2v(self):
        """Image-to-video with seed image — calls subscribe_async correctly."""
        client = _make_client()

        mock_result = {
            "video": {
                "url": "https://v3.fal.media/files/test/output.mp4",
                "duration": 6.0,
                "width": 1920,
                "height": 1080,
                "file_size": 1234567,
            },
            "request_id": "req-123",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result):
            clip = await client.generate_clip(
                prompt="A cat walks across a table",
                duration=5,
                resolution="720p",
                image_url="https://example.com/frame.png",
            )

        assert clip.url == "https://v3.fal.media/files/test/output.mp4"
        assert clip.request_id == "req-123"

    @pytest.mark.asyncio
    async def test_duration_rounded(self):
        """Odd duration is rounded to even for LTX."""
        client = _make_client()

        mock_result = {
            "video": {"url": "https://fal.media/test.mp4", "duration": 8.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-456",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result) as mock_sub:
            await client.generate_clip(prompt="test", duration=7, resolution="1080p")

            # Should have rounded 7 → 8
            call_args = mock_sub.call_args
            assert call_args[1]["arguments"]["duration"] == 8

    @pytest.mark.asyncio
    async def test_resolution_mapped(self):
        """480p resolution is mapped to 1080p for fal.ai."""
        client = _make_client()

        mock_result = {
            "video": {"url": "https://fal.media/test.mp4", "duration": 6.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-789",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result) as mock_sub:
            await client.generate_clip(prompt="test", duration=6, resolution="480p")

            call_args = mock_sub.call_args
            assert call_args[1]["arguments"]["resolution"] == "1080p"

    @pytest.mark.asyncio
    async def test_timeout_raises_timeout_error(self):
        """Timeout from fal_client raises GenerationTimeoutError."""
        client = _make_client()

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, side_effect=Exception("timed out waiting")):
            with pytest.raises(GenerationTimeoutError):
                await client.generate_clip(prompt="test", duration=6, resolution="1080p")

    @pytest.mark.asyncio
    async def test_moderation_raises_moderation_error(self):
        """Moderation block from fal.ai raises ModerationBlockedError."""
        client = _make_client()

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, side_effect=Exception("content policy violation: moderation")):
            with pytest.raises(ModerationBlockedError):
                await client.generate_clip(prompt="test", duration=6, resolution="1080p")

    @pytest.mark.asyncio
    async def test_no_video_url_raises(self):
        """Empty video result raises GenerationError."""
        client = _make_client()

        mock_result = {"video": {}, "request_id": "req-bad"}

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result):
            with pytest.raises(GenerationError, match="no video URL"):
                await client.generate_clip(prompt="test", duration=6, resolution="1080p")


class TestGenerateImage:
    @pytest.mark.asyncio
    async def test_success(self):
        """Successful image generation returns ImageResult."""
        client = _make_client()

        mock_result = {
            "images": [{"url": "https://fal.media/test-image.png", "width": 1080, "height": 1920}],
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result):
            result = await client.generate_image(prompt="A sunset over mountains", aspect_ratio="9:16")

        assert result.url == "https://fal.media/test-image.png"

    @pytest.mark.asyncio
    async def test_no_images_raises(self):
        """Empty images list raises GenerationError."""
        client = _make_client()

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value={"images": []}):
            with pytest.raises(GenerationError, match="no images"):
                await client.generate_image(prompt="test")


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_trips_after_threshold(self):
        """Circuit breaker trips after 3 consecutive failures."""
        client = _make_client()

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, side_effect=Exception("server error")):
            for _ in range(3):
                with pytest.raises(GenerationError):
                    await client.generate_clip(prompt="test", duration=6, resolution="1080p")

            # 4th call should raise ProviderUnavailableError
            with pytest.raises(ProviderUnavailableError):
                await client.generate_clip(prompt="test", duration=6, resolution="1080p")

    @pytest.mark.asyncio
    async def test_resets_on_success(self):
        """Circuit breaker resets after a successful call."""
        client = _make_client()
        client._consecutive_failures = 2  # One more would trip

        mock_result = {
            "video": {"url": "https://fal.media/ok.mp4", "duration": 6.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-ok",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result):
            clip = await client.generate_clip(prompt="test", duration=6, resolution="1080p")

        assert client._consecutive_failures == 0
        assert clip.url == "https://fal.media/ok.mp4"


class TestCostRecording:
    @pytest.mark.asyncio
    async def test_clip_cost_recorded(self):
        """generate_clip records cost to cost_recorder."""
        client = _make_client()

        mock_result = {
            "video": {"url": "https://fal.media/test.mp4", "duration": 6.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-cost",
        }

        with (
            patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result),
            patch("src.generation.fal_client._cost_recorder") as mock_recorder,
        ):
            mock_recorder.record = AsyncMock()
            await client.generate_clip(prompt="test", duration=5, resolution="1080p")

            mock_recorder.record.assert_called_once()
            call_kwargs = mock_recorder.record.call_args
            assert call_kwargs[0] == ("fal", "clip_gen")
            # 5s rounded to 6s × $0.04/s = $0.24
            assert call_kwargs[1]["cost_usd"] == pytest.approx(0.24)
            assert "ltx-2.3" in call_kwargs[1]["model"]


class TestT2VFallback:
    @pytest.mark.asyncio
    async def test_i2v_without_image_falls_back_to_t2v(self):
        """I2V endpoint with no image_url falls back to T2V endpoint."""
        client = _make_client()

        mock_result = {
            "video": {"url": "https://v3.fal.media/test.mp4", "duration": 6.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-t2v",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result) as mock_sub:
            await client.generate_clip(prompt="test", duration=6, resolution="1080p", image_url=None)

            # Should have used T2V endpoint, not I2V
            call_args = mock_sub.call_args
            endpoint_used = call_args[0][0]
            assert "text-to-video" in endpoint_used
            assert "image-to-video" not in endpoint_used

    @pytest.mark.asyncio
    async def test_i2v_with_image_stays_on_i2v(self):
        """I2V endpoint with image_url stays on I2V."""
        client = _make_client()

        mock_result = {
            "video": {"url": "https://v3.fal.media/test.mp4", "duration": 6.0, "width": 1920, "height": 1080, "file_size": 100},
            "request_id": "req-i2v",
        }

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_result) as mock_sub:
            await client.generate_clip(prompt="test", duration=6, resolution="1080p", image_url="https://example.com/img.png")

            call_args = mock_sub.call_args
            endpoint_used = call_args[0][0]
            assert "image-to-video" in endpoint_used


class TestDownloadValidation:
    @pytest.mark.asyncio
    async def test_rejects_http_url(self):
        """HTTP (non-HTTPS) URLs are rejected."""
        client = _make_client()
        async with client:
            with pytest.raises(GenerationError, match="Insecure URL"):
                await client.download_video("http://evil.com/video.mp4", Path("/tmp/test.mp4"))

    @pytest.mark.asyncio
    async def test_rejects_unknown_domain(self):
        """Non-fal.ai domains are rejected."""
        client = _make_client()
        async with client:
            with pytest.raises(GenerationError, match="not in allowlist"):
                await client.download_video("https://evil.com/video.mp4", Path("/tmp/test.mp4"))

    @pytest.mark.asyncio
    async def test_allows_fal_media_domain(self):
        """v3.fal.media URLs are accepted (requires actual download to succeed)."""
        from src.generation.fal_client import FalPlatformClient
        client = _make_client()
        # Just test the URL validation passes — the actual download would fail
        # since we don't have a real server. The domain check is what matters.
        async with client:
            # This will fail at httpx level (no real server) but NOT at domain validation
            with pytest.raises(GenerationError, match="download failed|zero bytes"):
                await client.download_video("https://v3.fal.media/files/test/video.mp4", Path("/tmp/test-dl.mp4"))


class TestModerationDoesNotTripCircuitBreaker:
    @pytest.mark.asyncio
    async def test_moderation_does_not_increment_failures(self):
        """Moderation errors should NOT count toward circuit breaker."""
        client = _make_client()

        # Generate 3 moderation errors
        with patch("fal_client.subscribe_async", new_callable=AsyncMock, side_effect=Exception("content policy moderation violation")):
            for _ in range(5):
                with pytest.raises(ModerationBlockedError):
                    await client.generate_clip(prompt="test", duration=6, resolution="1080p")

        # Circuit breaker should NOT be tripped — failures counter should be 0
        assert client._consecutive_failures == 0


class TestModelRegistry:
    def test_ltx_fast_has_required_fields(self):
        model = FAL_MODELS["ltx-fast"]
        assert "endpoint" in model
        assert "cost_per_second" in model
        assert "durations" in model
        assert 6 in model["durations"]
        assert 20 in model["durations"]

    def test_flux_pro_has_required_fields(self):
        model = FAL_MODELS["flux-pro"]
        assert "endpoint" in model
        assert "cost_per_megapixel" in model
