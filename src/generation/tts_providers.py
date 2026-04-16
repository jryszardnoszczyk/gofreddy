"""TTS provider implementations — Fish Audio, Kokoro (fal.ai), Dia (fal.ai)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from ..common.circuit_breaker import CircuitBreaker
from .exceptions import GenerationError, ModerationBlockedError, ProviderUnavailableError

if TYPE_CHECKING:
    from .config import GenerationSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TTSResult:
    """Result from TTS synthesis."""

    audio_url: str
    duration_seconds: float
    cost_usd: float
    provider: str
    audio_bytes: bytes | None = None


@runtime_checkable
class TTSProvider(Protocol):
    """Protocol for TTS providers."""

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        *,
        language: str = "en",
        emotion: str | None = None,
    ) -> TTSResult: ...


class FishAudioProvider:
    """Fish Audio S2 Pro TTS provider.

    Primary provider with voice cloning support.
    Cost: ~$0.008/video.
    """

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._cb = CircuitBreaker(failure_threshold=3, reset_timeout=60.0, name="fish_audio")

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        *,
        language: str = "en",
        emotion: str | None = None,
    ) -> TTSResult:
        if not self._cb.allow_request():
            raise ProviderUnavailableError("Fish Audio circuit breaker open")

        api_key = self._settings.fish_audio_api_key
        if not api_key:
            raise GenerationError("Fish Audio API key not configured")

        import httpx

        # Apply emotion via inline text tags (Fish Audio convention)
        synth_text = text
        if emotion:
            synth_text = f"({emotion}) {text}"

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=30, read=60),
            ) as client:
                resp = await client.post(
                    "https://api.fish.audio/v1/tts",
                    headers={
                        "Authorization": f"Bearer {api_key.get_secret_value()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": synth_text,
                        "reference_id": voice_id,
                        "format": "mp3",
                        "language": language,
                    },
                )
                resp.raise_for_status()
        except httpx.TimeoutException as e:
            self._cb.record_failure()
            raise GenerationError(f"Fish Audio timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            error_text = str(e.response.text)[:200] if e.response else ""
            if e.response and e.response.status_code in (503, 502, 429):
                self._cb.record_failure()
                raise GenerationError(f"Fish Audio unavailable: {error_text}") from e
            if "moderation" in error_text.lower() or "content" in error_text.lower():
                raise ModerationBlockedError(f"Fish Audio moderation: {error_text}") from e
            self._cb.record_failure()
            raise GenerationError(f"Fish Audio error: {error_text}") from e

        self._cb.record_success()

        # Fish Audio returns raw audio bytes (mp3) — no hosted URL.
        # Duration estimation: ~150 words/minute for English speech
        word_count = len(text.split())
        estimated_duration = max(1.0, (word_count / 150) * 60)
        cost = 0.008  # flat rate per synthesis

        return TTSResult(
            audio_url="",
            duration_seconds=estimated_duration,
            cost_usd=cost,
            provider="fish_audio",
            audio_bytes=resp.content,
        )


class KokoroFalProvider:
    """Kokoro TTS via fal.ai — budget provider.

    19 built-in voices, no cloning. Cost: ~$0.01/video.
    """

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._cb = CircuitBreaker(failure_threshold=3, reset_timeout=60.0, name="kokoro")

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        *,
        language: str = "en",
        emotion: str | None = None,
    ) -> TTSResult:
        if not self._cb.allow_request():
            raise ProviderUnavailableError("Kokoro circuit breaker open")

        import fal_client

        endpoint = "fal-ai/kokoro/american-english"
        arguments: dict[str, Any] = {
            "text": text,
            "voice": voice_id or "af_heart",
        }

        try:
            result = await fal_client.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=True,
                client_timeout=self._settings.fal_client_timeout,
            )
        except Exception as e:
            self._cb.record_failure()
            raise GenerationError(f"Kokoro TTS failed: {str(e)[:200]}") from e

        self._cb.record_success()

        audio = result.get("audio", {})
        audio_url = audio.get("url", "")
        duration = audio.get("duration", 0.0)

        if not audio_url:
            raise GenerationError("Kokoro returned no audio URL")

        return TTSResult(
            audio_url=audio_url,
            duration_seconds=float(duration),
            cost_usd=0.01,
            provider="kokoro",
        )


class DiaFalProvider:
    """Dia TTS via fal.ai — multi-speaker dialogue.

    Supports [speaker1]/[speaker2] tags. Cost: ~$0.02/video.
    """

    def __init__(self, settings: GenerationSettings) -> None:
        self._settings = settings
        self._cb = CircuitBreaker(failure_threshold=3, reset_timeout=60.0, name="dia")

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        *,
        language: str = "en",
        emotion: str | None = None,
    ) -> TTSResult:
        if not self._cb.allow_request():
            raise ProviderUnavailableError("Dia circuit breaker open")

        import fal_client

        endpoint = "fal-ai/dia-tts"
        arguments: dict[str, Any] = {"text": text}
        if voice_id:
            from ..common.url_validation import validate_fal_url_domain

            try:
                validate_fal_url_domain(voice_id)
            except ValueError as exc:
                raise GenerationError(str(exc)) from exc
            arguments["audio_url"] = voice_id  # Voice cloning via audio reference

        try:
            result = await fal_client.subscribe_async(
                endpoint,
                arguments=arguments,
                with_logs=True,
                client_timeout=self._settings.fal_client_timeout,
            )
        except Exception as e:
            self._cb.record_failure()
            raise GenerationError(f"Dia TTS failed: {str(e)[:200]}") from e

        self._cb.record_success()

        audio = result.get("audio", {})
        audio_url = audio.get("url", "")
        duration = audio.get("duration", 0.0)

        if not audio_url:
            raise GenerationError("Dia returned no audio URL")

        return TTSResult(
            audio_url=audio_url,
            duration_seconds=float(duration),
            cost_usd=0.02,
            provider="dia",
        )
