"""TTSService — multi-tier text-to-speech with provider fallback."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..common.cost_recorder import cost_recorder as _cost_recorder
from .config import GenerationSettings
from .exceptions import GenerationError
from .tts_providers import (
    DiaFalProvider,
    FishAudioProvider,
    KokoroFalProvider,
    TTSResult,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TTSService:
    """Multi-tier TTS with automatic fallback.

    Provider selection:
    - primary (fish_audio): Voice cloning, highest quality
    - budget (kokoro): Built-in voices, cheapest
    - dialogue (dia): Multi-speaker dialogue support
    """

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._providers = {
            "fish_audio": FishAudioProvider(settings),
            "kokoro": KokoroFalProvider(settings),
            "dia": DiaFalProvider(settings),
        }

    async def synthesize(
        self,
        text: str,
        voice_id: str = "af_heart",
        *,
        provider: str | None = None,
        language: str = "en",
        emotion: str | None = None,
    ) -> TTSResult:
        """Synthesize speech with automatic provider fallback.

        Args:
            text: Text to synthesize.
            voice_id: Voice identifier (provider-specific).
            provider: Force specific provider. None = use default with fallback.
            language: Language code.
            emotion: Emotion tag (Fish Audio only).

        Returns:
            TTSResult with audio URL and metadata. Note: Fish Audio returns
            raw bytes (audio_bytes set, audio_url empty). Callers should
            upload audio_bytes to R2 and use the resulting URL.
        """
        if not self._settings.tts_enabled:
            raise GenerationError("TTS is not currently available")

        if len(text) > self._settings.tts_max_text_length:
            raise GenerationError(
                f"Text exceeds TTS limit ({len(text)} > {self._settings.tts_max_text_length})"
            )

        # Determine provider chain
        if provider:
            chain = [provider]
        else:
            default = self._settings.tts_default_provider
            # Fallback chain: primary -> budget
            fallback_chains = {
                "fish_audio": ["fish_audio", "kokoro"],
                "kokoro": ["kokoro"],
                "dia": ["dia", "kokoro"],
            }
            chain = fallback_chains.get(default, [default, "kokoro"])

        last_error: Exception | None = None
        for provider_name in chain:
            prov = self._providers.get(provider_name)
            if not prov:
                continue

            try:
                result = await prov.synthesize(
                    text, voice_id, language=language, emotion=emotion
                )
                # Record cost
                await _cost_recorder.record(
                    "tts",
                    "synthesis",
                    cost_usd=result.cost_usd,
                    model=provider_name,
                    metadata={"duration": result.duration_seconds, "text_length": len(text)},
                )
                logger.info(
                    "tts_synthesized provider=%s duration=%.1fs cost=$%.4f",
                    provider_name, result.duration_seconds, result.cost_usd,
                )
                return result
            except GenerationError as e:
                last_error = e
                logger.warning("TTS provider %s failed, trying next: %s", provider_name, str(e)[:200])
                continue

        raise GenerationError(
            f"All TTS providers failed. Last error: {last_error}"
        )
