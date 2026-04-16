"""Generation module configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.gemini_models import GEMINI_FLASH, GEMINI_FLASH_IMAGE, GEMINI_FLASH_LITE


class GenerationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="GENERATION_"
    )

    xai_api_key: SecretStr | None = Field(
        default=None,
        description="Grok Imagine API key (required by PR-061 worker, not PR-060)",
    )
    xai_video_model: str = Field(
        default="grok-imagine-video",
        min_length=1,
        description="xAI video model passed to AsyncClient.video.start",
    )
    generation_enabled: bool = Field(default=False, description="Feature flag kill-switch")
    default_aspect_ratio: str = Field(default="9:16")
    max_cadres_per_video: int = Field(default=20)
    max_clip_duration_seconds: int = Field(default=30)
    daily_spend_limit_cents: int = Field(default=5000, description="$50/day safety cap")
    cost_per_second_cents_480p: int = Field(default=5)
    cost_per_second_cents_720p: int = Field(default=7)
    # Worker-only config (consumed by PR-061, defined here for single config source):
    reservation_ttl_seconds: int = Field(default=1260, description="Auto-void after 21 min (>= generation deadline + buffer)")
    poll_interval_seconds: float = Field(default=5.0)
    poll_timeout_seconds: float = Field(default=600.0)
    max_generation_deadline_seconds: int = Field(
        default=1200, description="60s headroom before Cloud Run kill (raised for 10-scene)"
    )
    # IdeaService settings (PR-062)
    idea_model: str = GEMINI_FLASH
    idea_temperature: float = 0.7
    idea_max_total_duration: int = 120
    # Preview settings (storyboard pipeline)
    preview_enabled: bool = Field(default=False, description="Enable image preview generation")
    preview_mock_enabled: bool = Field(
        default=False,
        description=(
            "Force FakeImagePreviewService even when EXTERNALS_MODE=real. "
            "Use for autoresearch optimization runs where real image credits "
            "would be wasted since the scorer reads agent-written storyboards/*.json, "
            "not the actual rendered images. The fake service still uploads a "
            "deterministic ~1KB PNG to real R2 and updates the real DB — only "
            "the FAL/Gemini image-gen call is skipped."
        ),
    )
    preview_model: str = Field(default=GEMINI_FLASH_IMAGE, description="Gemini model for image gen (Nano Banana 2)")
    preview_model_imagen: str = Field(default="imagen-4.0-generate-001", description="Imagen 4 model (cheaper alternative)")
    preview_model_grok: str = Field(default="grok-imagine-image", description="Grok Imagine model for image gen")
    preview_verifier_model: str = Field(default=GEMINI_FLASH_LITE, description="Gemini model for QA verification (cheap, fast)")
    # fal.ai platform settings
    fal_api_key: SecretStr | None = Field(default=None, description="fal.ai API key (FAL_KEY)")
    generation_provider: str = Field(default="fal", description="Primary generation provider: 'fal' or 'grok'")
    fal_default_video_model: str = Field(default="ltx-fast", description="Default fal.ai video model key")
    fal_default_image_model: str = Field(default="flux-pro", description="Default fal.ai image model key")
    fal_client_timeout: float = Field(default=120.0, description="fal.ai subscribe_async client_timeout")
    cost_per_second_cents_1080p: int = Field(default=4, description="fal.ai LTX Fast cost per second at 1080p")
    ltx_generate_audio: bool = Field(default=True, description="Enable LTX audio generation")
    # Storyboard evaluator (Phase 5 quality gate)
    storyboard_evaluator_enabled: bool = Field(default=True, description="Enable storyboard draft evaluation before persisting")
    storyboard_evaluator_model: str = Field(default=GEMINI_FLASH_LITE, description="Gemini model for storyboard evaluation (cheap, fast)")
    storyboard_evaluator_threshold: float = Field(default=6.0, description="Minimum overall score to accept a storyboard draft")
    # TTS settings (PR-100)
    fish_audio_api_key: SecretStr | None = Field(default=None, description="Fish Audio API key")
    tts_default_provider: str = Field(default="fish_audio", description="Default TTS: fish_audio|kokoro|dia")
    tts_max_text_length: int = Field(default=5000, description="Max chars per TTS call")
    tts_enabled: bool = Field(default=False, description="Feature flag for TTS")
    # Avatar settings (PR-100)
    avatar_enabled: bool = Field(default=False, description="Feature flag for avatar generation")
    # Background removal settings (PR-100)
    bg_removal_enabled: bool = Field(default=False, description="Feature flag for background removal")
    # Music settings (PR-100)
    suno_api_key: SecretStr | None = Field(default=None, description="Suno/kie.ai API key")
    suno_api_url: str = Field(default="https://api.kie.ai/api/v1", description="Suno API base URL")
    music_enabled: bool = Field(default=False, description="Feature flag for music generation")
    suno_poll_interval: float = Field(default=30.0, description="Suno poll interval in seconds")
    suno_poll_timeout: float = Field(default=120.0, description="Suno max wait before timeout")


# fal.ai model registry — endpoint + pricing for deterministic cost tracking.
# MVP: ltx-fast (video) and flux-pro (image). Others for config-only switching.
FAL_MODELS: dict[str, dict] = {
    # Video I2V
    "ltx-fast": {
        "endpoint": "fal-ai/ltx-2.3/image-to-video/fast",
        "cost_per_second": 0.04,
        "min_resolution": "1080p",
        "durations": [6, 8, 10, 12, 14, 16, 18, 20],
    },
    "ltx-pro": {
        "endpoint": "fal-ai/ltx-2.3/image-to-video",
        "cost_per_second": 0.06,
        "min_resolution": "1080p",
        "durations": [6, 8, 10],
    },
    # Video T2V
    "ltx-fast-t2v": {
        "endpoint": "fal-ai/ltx-2.3/text-to-video/fast",
        "cost_per_second": 0.04,
        "min_resolution": "1080p",
        "durations": [6, 8, 10, 12, 14, 16, 18, 20],
    },
    # Image
    "flux-pro": {
        "endpoint": "fal-ai/flux-2-pro",
        "cost_per_megapixel": 0.03,
    },
    "flux-schnell": {
        "endpoint": "fal-ai/flux/schnell",
        "cost_per_megapixel": 0.003,
    },
    # TTS models (PR-100)
    "kokoro-en": {
        "endpoint": "fal-ai/kokoro/american-english",
        "cost_per_second": 0.001,
    },
    "dia-tts": {
        "endpoint": "fal-ai/dia-tts",
        "cost_per_second": 0.002,
    },
    # Avatar (PR-100)
    "kling-avatar-standard": {
        "endpoint": "fal-ai/kling-avatar/v2",
        "cost_per_second": 0.056,
    },
    # Background removal (PR-100)
    "bria-rmbg": {
        "endpoint": "fal-ai/bria/background/remove",
        "cost_per_image": 0.018,
    },
    "veed-video-bg-removal": {
        "endpoint": "fal-ai/veed/video-bg-removal",
        "cost_per_30_frames": 0.010,
    },
}
