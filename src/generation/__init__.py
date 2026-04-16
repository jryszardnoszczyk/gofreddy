"""Video generation pipeline — domain shell."""

from .config import GenerationSettings
from .composition import CompositionService
from .exceptions import (
    GenerationConcurrentLimitExceeded,
    GenerationDailySpendLimitExceeded,
    GenerationError,
    GenerationTimeoutError,
    IdeationError,
    PreviewError,
)
from .exceptions import (
    GrokAPIUnavailableError,
    GrokModerationBlockedError,
    ModerationBlockedError,
    ProviderUnavailableError,
)
from .fake import FakeGenerationClient, FakeGrokClient, FakeIdeaService, FakeImagePreviewService
from .fake_storage import FakeGenerationAssetStorage
from .grok_client import ClipResult, GrokImagineClient
from .providers import GenerationProvider, ImageResult, VideoClip
from .idea_service import IdeaService
from .image_preview_service import ImagePreviewService
from .models import Cadre, Caption, CompositionSpec, GenerationResult, PreviewResult
from .prompt_utils import sanitize_prompt
from .storage import R2GenerationStorage

__all__ = [
    "Cadre",
    "Caption",
    "ClipResult",
    "CompositionService",
    "CompositionSpec",
    "FakeGenerationClient",
    "FakeGrokClient",
    "FakeGenerationAssetStorage",
    "FakeIdeaService",
    "FakeImagePreviewService",
    "GenerationConcurrentLimitExceeded",
    "GenerationDailySpendLimitExceeded",
    "GenerationError",
    "GenerationProvider",
    "GenerationResult",
    "GenerationSettings",
    "GenerationTimeoutError",
    "GrokAPIUnavailableError",
    "GrokImagineClient",
    "GrokModerationBlockedError",
    "IdeaService",
    "IdeationError",
    "ImageResult",
    "ImagePreviewService",
    "ModerationBlockedError",
    "PreviewError",
    "PreviewResult",
    "ProviderUnavailableError",
    "R2GenerationStorage",
    "VideoClip",
    "sanitize_prompt",
]
