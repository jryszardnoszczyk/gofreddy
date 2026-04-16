"""Generation provider protocol and shared result types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VideoClip:
    """Result from a video clip generation request."""

    url: str
    request_id: str


@dataclass(frozen=True, slots=True)
class ImageResult:
    """Result from an image generation request."""

    url: str


class GenerationProvider(Protocol):
    """Protocol for video and image generation providers.

    Implementations:
    - GrokImagineClient (xai_sdk — Grok Imagine API)
    - FalPlatformClient (fal-client — fal.ai platform)
    - FakeGenerationClient (test double)
    """

    async def generate_clip(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        aspect_ratio: str = "auto",
        image_url: str | None = None,
    ) -> VideoClip:
        """Generate a video clip.

        Args:
            prompt: Scene description for the clip.
            duration: Target duration in seconds.
            resolution: Target resolution (e.g. "480p", "720p", "1080p").
            aspect_ratio: Target aspect ratio ("9:16", "16:9", "1:1", or "auto").
            image_url: Optional seed image URL for image-to-video.

        Returns:
            VideoClip with download URL and provider request ID.

        Raises:
            ModerationBlockedError: Content blocked by provider moderation.
            ProviderUnavailableError: Circuit breaker tripped.
            GenerationError: Other generation failure.
            GenerationTimeoutError: Generation exceeded deadline.
        """
        ...

    async def download_video(self, url: str, dest: Path) -> None:
        """Download a generated video to a local path.

        Args:
            url: Video URL returned by generate_clip().
            dest: Local file path to write to.

        Raises:
            GenerationError: Download or validation failure.
        """
        ...

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        image_url: str | None = None,
    ) -> ImageResult:
        """Generate a still image.

        Args:
            prompt: Scene description.
            aspect_ratio: Target aspect ratio (e.g. "9:16", "16:9", "1:1").
            image_url: Optional style reference image URL.

        Returns:
            ImageResult with image URL.

        Raises:
            ModerationBlockedError: Content blocked by provider moderation.
            GenerationError: Generation failure.
        """
        ...
