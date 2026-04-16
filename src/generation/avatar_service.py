"""AvatarService — talking avatar generation via Kling Avatar v2."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..common.cost_recorder import cost_recorder as _cost_recorder
from ..common.url_validation import validate_fal_url_domain
from .exceptions import GenerationError

if TYPE_CHECKING:
    from .config import GenerationSettings
    from .fal_client import FalPlatformClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AvatarResult:
    """Result from talking avatar generation."""

    video_url: str
    duration_seconds: float
    cost_usd: float


class AvatarService:
    """Talking avatar generation via Kling Avatar v2 Standard on fal.ai."""

    def __init__(
        self,
        fal_client: FalPlatformClient,
        settings: GenerationSettings,
    ) -> None:
        self._fal = fal_client
        self._settings = settings

    async def generate_talking_video(
        self,
        image_url: str,
        audio_url: str,
        *,
        duration_seconds: int | None = None,
    ) -> AvatarResult:
        """Generate a talking avatar video from face image + audio.

        Args:
            image_url: URL to face/avatar image (must be from allowed domain).
            audio_url: URL to narration audio (must be from allowed domain).
            duration_seconds: Optional duration hint.

        Returns:
            AvatarResult with video URL and cost.
        """
        if not self._settings.avatar_enabled:
            raise GenerationError("Avatar generation is not currently available")

        # SSRF validation
        try:
            validate_fal_url_domain(image_url)
            validate_fal_url_domain(audio_url)
        except ValueError as exc:
            raise GenerationError(str(exc)) from exc

        import fal_client as _fal_sdk

        endpoint = "fal-ai/kling-avatar/v2"
        arguments: dict = {
            "face_image_url": image_url,
            "audio_url": audio_url,
        }

        try:
            result = await _fal_sdk.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=True,
                client_timeout=self._settings.fal_client_timeout,
            )
        except Exception as e:
            raise GenerationError(f"Avatar generation failed: {str(e)[:200]}") from e

        video = result.get("video", {})
        video_url = video.get("url", "")
        if not video_url:
            raise GenerationError("Avatar generation returned no video URL")

        # Cost: $0.056/second
        actual_duration = float(duration_seconds or 10)
        cost_usd = actual_duration * 0.056

        await _cost_recorder.record(
            "fal",
            "avatar_gen",
            cost_usd=cost_usd,
            model=endpoint,
            metadata={"duration": actual_duration},
        )

        logger.info(
            "avatar_generated duration=%.1fs cost=$%.3f",
            actual_duration, cost_usd,
        )

        return AvatarResult(
            video_url=video_url,
            duration_seconds=actual_duration,
            cost_usd=cost_usd,
        )
