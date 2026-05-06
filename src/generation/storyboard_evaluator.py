"""StoryboardEvaluator — score storyboard drafts before persisting.

Switched from Gemini Flash Lite to Claude (via the shared `call_sonnet_json`
CLI helper) on 2026-05-06. The constructor still accepts a `client` arg so
existing callers/tests don't break — it is no longer used.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..evaluation.judges.sonnet_agent import (
    SONNET_MODEL,
    SonnetAgentError,
    call_sonnet_json,
)
from .config import GenerationSettings

if TYPE_CHECKING:
    from .models import StoryboardDraft

logger = logging.getLogger(__name__)

_EVALUATION_PROMPT = (
    "You are a strict storyboard quality evaluator. Score this storyboard draft on 7 signals, "
    "each 1-10:\n\n"
    "1. **coherence_score**: Does the story flow logically from scene to scene?\n"
    "2. **character_score**: Is the protagonist visually described consistently across scenes?\n"
    "3. **emotion_score**: Do the scenes progress through a compelling emotional journey?\n"
    "4. **prompt_quality_score**: Does each scene prompt include subject + camera + lighting + mood?\n"
    "5. **dialogue_score**: Are audio directions and dialogue natural and character-appropriate?\n"
    "6. **audio_score**: Is audio direction consistent in tone and style across scenes?\n"
    "7. **pacing_score**: Are scene durations and transitions well-paced for short-form content?\n\n"
    "Also provide:\n"
    "- **feedback**: One sentence summary of the biggest weakness\n"
    "- **improvement_suggestion**: One actionable suggestion to improve the draft\n\n"
    "Return a SINGLE JSON object (no prose, no markdown fences) with these 9 fields."
)


@dataclass(frozen=True, slots=True)
class StoryboardEvaluationResult:
    coherence_score: int
    character_score: int
    emotion_score: int
    prompt_quality_score: int
    dialogue_score: int
    audio_score: int
    pacing_score: int
    overall_score: float
    feedback: str
    improvement_suggestion: str


class StoryboardEvaluator:
    """Score storyboard drafts using Claude (CLI subprocess).

    Non-blocking: returns None on failure (caller keeps draft with warning).
    """

    def __init__(self, client: Any, settings: GenerationSettings) -> None:
        # `client` accepted for backward compatibility (was a Gemini
        # genai.Client). Kept on the instance to preserve attribute lookups
        # but unused otherwise; the Claude CLI replaces it.
        self._client = client
        self._model = settings.storyboard_evaluator_model or SONNET_MODEL
        self._enabled = settings.storyboard_evaluator_enabled

    async def evaluate(
        self,
        draft: StoryboardDraft,
        context: str | None = None,
    ) -> StoryboardEvaluationResult | None:
        """Score a storyboard draft on 7 signals.

        Returns None on failure (non-blocking — caller keeps draft with warning).
        """
        if not self._enabled:
            return None

        draft_json = draft.model_dump_json(indent=2)
        parts = [f"## Storyboard Draft\n{draft_json}\n"]
        if context:
            parts.append(f"## Story Context\n{context[:5000]}\n")
        parts.append(_EVALUATION_PROMPT)
        prompt = "\n".join(parts)

        try:
            data = await call_sonnet_json(
                prompt,
                operation="evaluate_storyboard",
                model=self._model,
                timeout=60.0,
            )
        except SonnetAgentError:
            logger.debug("Storyboard evaluation failed (CLI error)", exc_info=True)
            return None
        except Exception:
            logger.debug("Storyboard evaluation failed (unexpected)", exc_info=True)
            return None

        if not isinstance(data, dict):
            return None

        try:
            scores = {
                "coherence_score": _clamp(data.get("coherence_score", 0)),
                "character_score": _clamp(data.get("character_score", 0)),
                "emotion_score": _clamp(data.get("emotion_score", 0)),
                "prompt_quality_score": _clamp(data.get("prompt_quality_score", 0)),
                "dialogue_score": _clamp(data.get("dialogue_score", 0)),
                "audio_score": _clamp(data.get("audio_score", 0)),
                "pacing_score": _clamp(data.get("pacing_score", 0)),
            }
            overall = sum(scores.values()) / len(scores)

            return StoryboardEvaluationResult(
                **scores,
                overall_score=round(overall, 2),
                feedback=str(data.get("feedback", ""))[:200],
                improvement_suggestion=str(data.get("improvement_suggestion", ""))[:200],
            )
        except Exception:
            logger.debug("Storyboard evaluation parse failed", exc_info=True)
            return None


def _clamp(value: int | float | str, lo: int = 1, hi: int = 10) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return lo
