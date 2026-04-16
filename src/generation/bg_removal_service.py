"""BackgroundRemovalService — image and video background removal via fal.ai."""

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
class BGRemovalResult:
    """Result from background removal."""

    output_url: str
    cost_usd: float


class BackgroundRemovalService:
    """Image and video background removal via fal.ai (Bria RMBG 2.0 + VEED)."""

    def __init__(
        self,
        fal_client: FalPlatformClient,
        settings: GenerationSettings,
    ) -> None:
        self._fal = fal_client
        self._settings = settings

    async def remove_bg_image(self, image_url: str) -> BGRemovalResult:
        """Remove background from a single image via Bria RMBG 2.0."""
        if not self._settings.bg_removal_enabled:
            raise GenerationError("Background removal is not currently available")

        try:
            validate_fal_url_domain(image_url)
        except ValueError as exc:
            raise GenerationError(str(exc)) from exc

        import fal_client as _fal_sdk

        endpoint = "fal-ai/bria/background/remove"
        try:
            result = await _fal_sdk.subscribe_async(
                endpoint,
                arguments={"image_url": image_url},
                with_logs=True,
                client_timeout=60.0,
            )
        except Exception as e:
            raise GenerationError(f"Image BG removal failed: {str(e)[:200]}") from e

        image = result.get("image", {})
        output_url = image.get("url", "")
        if not output_url:
            raise GenerationError("BG removal returned no output URL")

        cost_usd = 0.018

        await _cost_recorder.record(
            "fal", "bg_removal_image", cost_usd=cost_usd, model=endpoint,
        )

        logger.info("bg_removed_image cost=$%.3f", cost_usd)
        return BGRemovalResult(output_url=output_url, cost_usd=cost_usd)

    async def remove_bg_video(
        self, video_url: str, *, fps: int = 1
    ) -> BGRemovalResult:
        """Remove background from video via VEED Video BG Removal."""
        if not self._settings.bg_removal_enabled:
            raise GenerationError("Background removal is not currently available")

        try:
            validate_fal_url_domain(video_url)
        except ValueError as exc:
            raise GenerationError(str(exc)) from exc

        import fal_client as _fal_sdk

        endpoint = "fal-ai/veed/video-bg-removal"
        try:
            result = await _fal_sdk.subscribe_async(
                endpoint,
                arguments={"video_url": video_url},
                with_logs=True,
                client_timeout=120.0,
            )
        except Exception as e:
            raise GenerationError(f"Video BG removal failed: {str(e)[:200]}") from e

        video = result.get("video", {})
        output_url = video.get("url", "")
        if not output_url:
            raise GenerationError("Video BG removal returned no output URL")

        cost_usd = 0.010  # avg for 30 frames

        await _cost_recorder.record(
            "fal", "bg_removal_video", cost_usd=cost_usd, model=endpoint,
        )

        logger.info("bg_removed_video cost=$%.3f", cost_usd)
        return BGRemovalResult(output_url=output_url, cost_usd=cost_usd)
