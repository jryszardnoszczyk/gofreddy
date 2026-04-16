"""Lane routing for transcript-first analysis."""

from enum import Enum


class AnalysisLane(str, Enum):
    """Analysis lane determining processing path."""

    L1_TRANSCRIPT_FIRST = "L1_TRANSCRIPT_FIRST"
    L2_MULTIMODAL_AUDIO = "L2_MULTIMODAL_AUDIO"


def select_lane(
    transcript_available: bool,
    transcript_quality: float | None,
    quality_threshold: float,
    flag_enabled: bool,
) -> AnalysisLane:
    """Determine analysis lane. Pure function, no side effects."""
    if not flag_enabled:
        return AnalysisLane.L2_MULTIMODAL_AUDIO
    if (
        transcript_available
        and transcript_quality is not None
        and transcript_quality >= quality_threshold
    ):
        return AnalysisLane.L1_TRANSCRIPT_FIRST
    return AnalysisLane.L2_MULTIMODAL_AUDIO


def score_transcript_quality(
    transcript_text: str,
    duration_seconds: int | None = None,
    max_chars: int = 50_000,
) -> float:
    """Score transcript quality from 0.0 to 1.0. Deterministic."""
    if not transcript_text or not transcript_text.strip():
        return 0.0
    # Truncate before processing to prevent memory waste on pathological input
    text = transcript_text[:max_chars]
    words = text.split()
    word_count = len(words)
    if word_count < 20:
        return 0.0
    # Base quality: 200+ words -> 1.0
    quality = min(1.0, word_count / 200)
    # Words-per-second penalty if duration available
    if duration_seconds and duration_seconds > 0:
        wps = word_count / duration_seconds
        if wps < 0.5:  # Very sparse transcript
            quality *= 0.5
        elif wps > 5.0:  # Likely garbled/noisy
            quality *= 0.7
    return round(quality, 2)
