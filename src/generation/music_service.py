"""MusicService — music generation via Suno API + beat analysis."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from ..common.circuit_breaker import CircuitBreaker
from ..common.cost_recorder import cost_recorder as _cost_recorder
from .exceptions import GenerationError, ModerationBlockedError

if TYPE_CHECKING:
    from .config import GenerationSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MusicResult:
    """Result from music generation."""

    audio_url: str
    duration_seconds: float
    cost_usd: float
    beat_timestamps: list[float] = field(default_factory=list)


class MusicService:
    """Music generation via Suno API (kie.ai proxy) + beat analysis."""

    def __init__(self, settings: GenerationSettings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http
        self._cb = CircuitBreaker(failure_threshold=3, reset_timeout=60.0, name="suno")

    async def generate_track(
        self,
        description: str,
        *,
        duration_seconds: int = 30,
        instrumental: bool = True,
    ) -> MusicResult:
        """Generate a music track via Suno API.

        Args:
            description: Music style/mood description.
            duration_seconds: Target duration (Suno generates ~30-120s).
            instrumental: If True, generate instrumental only.

        Returns:
            MusicResult with audio URL and beat timestamps.
        """
        if not self._settings.music_enabled:
            raise GenerationError("Music generation is not currently available")

        if not self._cb.allow_request():
            raise GenerationError("Suno circuit breaker open")

        api_key = self._settings.suno_api_key
        if not api_key:
            raise GenerationError("Suno API key not configured")

        base_url = self._settings.suno_api_url.rstrip("/")

        # Submit generation request
        try:
            resp = await self._http.post(
                f"{base_url}/generate",
                headers={
                    "Authorization": f"Bearer {api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": description,
                    "instrumental": instrumental,
                    "model": "V4_5",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
        except httpx.TimeoutException as e:
            self._cb.record_failure()
            raise GenerationError(f"Suno API timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            error_text = str(e.response.text)[:200] if e.response else ""
            if "SENSITIVE_WORD_ERROR" in error_text:
                raise ModerationBlockedError(f"Suno content filter: {error_text}") from e
            self._cb.record_failure()
            raise GenerationError(f"Suno API error: {error_text}") from e

        result_data = resp.json()
        task_id = result_data.get("id") or result_data.get("task_id")
        if not task_id:
            raise GenerationError("Suno returned no task ID")

        # Poll for completion with deadline pattern
        deadline = time.monotonic() + self._settings.suno_poll_timeout
        audio_url = ""
        duration = 0.0

        while time.monotonic() < deadline:
            await asyncio.sleep(self._settings.suno_poll_interval)

            try:
                poll_resp = await self._http.get(
                    f"{base_url}/status/{task_id}",
                    headers={"Authorization": f"Bearer {api_key.get_secret_value()}"},
                    timeout=15.0,
                )
                poll_resp.raise_for_status()
            except Exception as e:
                logger.warning("Suno poll failed: %s", str(e)[:100])
                continue

            poll_data = poll_resp.json()
            status = poll_data.get("status", "")

            if status == "completed":
                audio_url = poll_data.get("audio_url", "")
                duration = float(poll_data.get("duration", duration_seconds))
                break
            elif status in ("failed", "error"):
                error_msg = poll_data.get("error", "Unknown error")
                if "SENSITIVE_WORD" in str(error_msg):
                    raise ModerationBlockedError(f"Suno content filter: {error_msg}")
                self._cb.record_failure()
                raise GenerationError(f"Suno generation failed: {error_msg}")

        if not audio_url:
            self._cb.record_failure()
            raise GenerationError("Suno generation timed out — no audio URL after polling")

        self._cb.record_success()
        cost_usd = 0.03  # ~$0.03/track

        await _cost_recorder.record(
            "suno",
            "music_gen",
            cost_usd=cost_usd,
            metadata={"duration": duration, "instrumental": instrumental},
        )

        logger.info(
            "music_generated duration=%.1fs cost=$%.3f",
            duration, cost_usd,
        )

        return MusicResult(
            audio_url=audio_url,
            duration_seconds=duration,
            cost_usd=cost_usd,
        )

    async def analyze_beats(self, audio_path: Path) -> list[float] | None:
        """Detect beat timestamps using librosa (optional dependency).

        Returns None if librosa is not installed.
        """
        try:
            import librosa  # Lazy import — avoids 2-3s cold start from numpy/scipy
        except ImportError:
            logger.info("librosa not installed, skipping beat analysis")
            return None

        try:
            y, sr = librosa.load(str(audio_path), sr=None)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            # librosa v0.10+: tempo is a 1D numpy array
            timestamps = librosa.frames_to_time(beat_frames, sr=sr).tolist()
            logger.info(
                "beats_analyzed tempo=%.1f beats=%d",
                float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo),
                len(timestamps),
            )
            return timestamps
        except Exception as e:
            logger.warning("Beat analysis failed: %s", str(e)[:200])
            return None
