"""fal.ai platform client for video and image generation."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Self

import httpx

from ..common.cost_recorder import cost_recorder as _cost_recorder
from .config import FAL_MODELS, GenerationSettings
from .exceptions import (
    GenerationError,
    GenerationTimeoutError,
    ModerationBlockedError,
    ProviderUnavailableError,
)
from .providers import ImageResult, VideoClip

logger = logging.getLogger(__name__)

def _round_to_even(duration: int, max_duration: int = 20) -> int:
    """Round duration up to the nearest even number for LTX-2.3.

    LTX-2.3 only accepts even durations: 6, 8, 10, 12, 14, 16, 18, 20.
    Minimum is 6 (the model's minimum).
    """
    rounded = duration if duration % 2 == 0 else duration + 1
    return max(6, min(rounded, max_duration))


def _map_resolution(resolution: str) -> str:
    """Map any resolution to fal.ai-supported resolution.

    LTX-2.3 minimum is 1080p — no 480p/720p support.
    """
    if resolution in ("480p", "720p"):
        return "1080p"
    if resolution in ("1080p", "1440p", "2160p"):
        return resolution
    return "1080p"


class FalPlatformClient:
    """Async client for fal.ai platform — video and image generation.

    Uses fal-client SDK to access LTX-2.3 (video) and FLUX.2 Pro (image)
    endpoints. Implements the GenerationProvider protocol.
    """

    _CIRCUIT_BREAKER_THRESHOLD = 3

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._http: httpx.AsyncClient | None = None
        self._consecutive_failures = 0

        # Set FAL_KEY for the fal-client SDK (reads from env)
        if settings.fal_api_key:
            os.environ["FAL_KEY"] = settings.fal_api_key.get_secret_value()

    async def __aenter__(self) -> Self:
        self._http = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, read=120.0),
        )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    def reset_circuit_breaker(self) -> None:
        self._consecutive_failures = 0

    def _check_circuit_breaker(self) -> None:
        if self._consecutive_failures >= self._CIRCUIT_BREAKER_THRESHOLD:
            raise ProviderUnavailableError(
                f"fal.ai circuit breaker open after {self._consecutive_failures} consecutive failures"
            )

    def _get_model_config(self, model_key: str) -> dict:
        """Look up model config from FAL_MODELS registry."""
        config = FAL_MODELS.get(model_key)
        if not config:
            raise GenerationError(f"Unknown fal.ai model: {model_key}")
        return config

    async def generate_clip(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        aspect_ratio: str = "auto",
        image_url: str | None = None,
    ) -> VideoClip:
        """Generate a video clip via fal.ai LTX-2.3."""
        import fal_client

        self._check_circuit_breaker()

        model_key = self._settings.fal_default_video_model
        model_config = self._get_model_config(model_key)
        endpoint = model_config["endpoint"]

        # Duration rounding for LTX (even numbers only)
        max_dur = max(model_config.get("durations", [20]))
        rounded_duration = _round_to_even(duration, max_dur)

        # Resolution mapping (480p/720p → 1080p)
        mapped_resolution = _map_resolution(resolution)

        # Map aspect ratio to LTX-2.3 values (no 1:1 support — use "auto")
        mapped_aspect = {"9:16": "9:16", "16:9": "16:9", "1:1": "auto"}.get(aspect_ratio, "auto")

        # Build arguments
        arguments: dict[str, Any] = {
            "prompt": prompt,
            "duration": rounded_duration,
            "resolution": mapped_resolution,
            "aspect_ratio": mapped_aspect,
            "fps": 25,
            "generate_audio": self._settings.ltx_generate_audio,
        }

        # Image-to-video vs text-to-video
        if image_url:
            arguments["image_url"] = image_url
        elif "image-to-video" in endpoint:
            # I2V endpoint requires an image — switch to T2V fallback
            _T2V_FALLBACK = {"ltx-fast": "ltx-fast-t2v", "ltx-pro": "ltx-fast-t2v"}
            t2v_key = _T2V_FALLBACK.get(model_key)
            if t2v_key:
                t2v_config = FAL_MODELS.get(t2v_key)
                if t2v_config:
                    endpoint = t2v_config["endpoint"]
                    model_config = t2v_config

        start = time.monotonic()
        try:
            result = await fal_client.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=True,
                client_timeout=self._settings.fal_client_timeout,
            )
        except Exception as e:
            error_str = str(e).lower()

            # Moderation blocks are NOT infrastructure failures — don't count toward circuit breaker
            if "moderation" in error_str or "safety" in error_str or "content policy" in error_str:
                raise ModerationBlockedError(f"fal.ai content moderation: {str(e)[:200]}") from e

            # Timeouts count toward circuit breaker
            self._consecutive_failures += 1

            if "timeout" in error_str or "timed out" in error_str:
                raise GenerationTimeoutError(
                    f"fal.ai generation timed out after {self._settings.fal_client_timeout}s"
                ) from e

            self._check_circuit_breaker()
            raise GenerationError(f"fal.ai generation failed: {str(e)[:200]}") from e

        elapsed = time.monotonic() - start

        # Extract video result
        video = result.get("video", {})
        video_url = video.get("url")
        if not video_url:
            self._consecutive_failures += 1
            raise GenerationError("fal.ai returned no video URL")

        # Success — reset circuit breaker
        self._consecutive_failures = 0

        # Record cost (deterministic from pricing table)
        cost_per_second = model_config.get("cost_per_second", 0.04)
        cost_usd = rounded_duration * cost_per_second
        await _cost_recorder.record(
            "fal",
            "clip_gen",
            cost_usd=cost_usd,
            model=endpoint,
            metadata={
                "duration_requested": duration,
                "duration_rounded": rounded_duration,
                "resolution": mapped_resolution,
                "aspect_ratio": mapped_aspect,
                "elapsed_seconds": round(elapsed, 1),
            },
        )

        request_id = result.get("request_id", "unknown")
        logger.info(
            "fal_clip_generated endpoint=%s duration=%ds resolution=%s elapsed=%.1fs cost=$%.3f",
            endpoint, rounded_duration, mapped_resolution, elapsed, cost_usd,
        )

        return VideoClip(url=video_url, request_id=request_id)

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        image_url: str | None = None,
    ) -> ImageResult:
        """Generate a still image via fal.ai FLUX.2 Pro."""
        import fal_client

        self._check_circuit_breaker()

        model_key = self._settings.fal_default_image_model
        model_config = self._get_model_config(model_key)
        endpoint = model_config["endpoint"]

        # Map aspect ratio to the supported fal.ai image_size aliases.
        size_map = {
            "9:16": "portrait_16_9",   # tall portrait (1080x1920)
            "16:9": "landscape_16_9",  # wide landscape (1920x1080)
            "1:1": "square_hd",        # square (1024x1024)
        }
        image_size = size_map.get(aspect_ratio, "portrait_16_9")

        arguments: dict[str, Any] = {
            "prompt": prompt,
            "image_size": image_size,
        }
        if image_url:
            arguments["image_url"] = image_url

        start = time.monotonic()
        try:
            result = await fal_client.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=True,
                client_timeout=60.0,
            )
        except Exception as e:
            error_str = str(e).lower()

            # Moderation blocks are NOT infrastructure failures — don't count toward circuit breaker
            if "moderation" in error_str or "safety" in error_str:
                raise ModerationBlockedError(f"fal.ai image moderation: {str(e)[:200]}") from e

            self._consecutive_failures += 1
            self._check_circuit_breaker()
            raise GenerationError(f"fal.ai image generation failed: {str(e)[:200]}") from e

        elapsed = time.monotonic() - start

        # Extract image URL
        images = result.get("images", [])
        if not images:
            self._consecutive_failures += 1
            raise GenerationError("fal.ai returned no images")

        img_url = images[0].get("url", "")
        if not img_url:
            self._consecutive_failures += 1
            raise GenerationError("fal.ai returned empty image URL")

        self._consecutive_failures = 0

        # Record cost — compute megapixels from actual response dimensions if available
        cost_per_mp = model_config.get("cost_per_megapixel", 0.03)
        img_w = images[0].get("width", 0)
        img_h = images[0].get("height", 0)
        if img_w > 0 and img_h > 0:
            megapixels = (img_w * img_h) / 1_000_000
        else:
            # Fallback: estimate from image_size request
            mp_estimates = {"portrait_16_9": 2.07, "landscape_16_9": 2.07, "square_hd": 1.05}
            megapixels = mp_estimates.get(image_size, 2.0)
        cost_usd = cost_per_mp * megapixels
        await _cost_recorder.record(
            "fal",
            "image_gen",
            cost_usd=cost_usd,
            model=endpoint,
            metadata={"aspect_ratio": aspect_ratio, "megapixels": round(megapixels, 2), "elapsed_seconds": round(elapsed, 1)},
        )

        logger.info(
            "fal_image_generated endpoint=%s aspect_ratio=%s elapsed=%.1fs cost=$%.4f",
            endpoint, aspect_ratio, elapsed, cost_usd,
        )

        return ImageResult(url=img_url)

    # Known fal.ai CDN domains for download validation
    _ALLOWED_DOMAINS = ("v3.fal.media", "fal.media", "fal.run", "storage.googleapis.com")

    async def download_video(self, url: str, dest: Path) -> None:
        """Download generated video from fal.ai CDN.

        fal CDN URLs are public and time-limited (~24h). We validate the
        domain against a known allowlist as defense-in-depth.
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise GenerationError(f"Insecure URL for video download: {url[:100]}")

        domain = parsed.hostname or ""
        if not any(domain == d or domain.endswith(f".{d}") for d in self._ALLOWED_DOMAINS):
            raise GenerationError(f"fal.ai download URL domain not in allowlist: {domain}")

        if self._http is None:
            raise GenerationError("Client not initialized — use async with")

        try:
            async with self._http.stream("GET", url) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(8192):
                        f.write(chunk)
        except httpx.HTTPError as e:
            raise GenerationError(f"fal.ai video download failed: {str(e)[:200]}") from e

        if dest.stat().st_size == 0:
            dest.unlink(missing_ok=True)
            raise GenerationError("Downloaded zero bytes from fal.ai")

    async def upload_image_bytes(self, data: bytes, mime_type: str = "image/png") -> str:
        """Upload raw image bytes to fal CDN and return the URL.

        Use this when fal.ai can't access the source URL directly (e.g. R2 presigned URLs).
        """
        import fal_client
        return await fal_client.upload_async(data, mime_type)
