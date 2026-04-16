"""Creative pattern taxonomy schemas for validation spike."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreativePatterns(BaseModel):
    """Creative DNA extraction — the proposed taxonomy to validate."""

    # Hook (first few seconds)
    hook_type: Literal[
        "question",
        "shock_curiosity",
        "trend_audio",
        "storytelling",
        "product_reveal",
        "challenge",
        "none",
    ]
    hook_duration_seconds: int | None = Field(
        default=None,
        description="Seconds until first content shift after hook",
    )

    # Narrative structure
    narrative_structure: Literal[
        "tutorial",
        "review",
        "unboxing",
        "day_in_life",
        "transformation",
        "comparison",
        "listicle",
        "skit",
        "vlog",
        "other",
    ]

    # Call to action
    cta_type: Literal["follow", "like", "comment", "link_in_bio", "shop", "none"]
    cta_placement: Literal["early", "middle", "end", "repeated", "none"]

    # Production style
    pacing: Literal["fast_cut", "moderate", "slow_cinematic", "single_take"]
    music_usage: Literal["trending_audio", "original", "none", "voiceover_only"]
    text_overlay_density: Literal["none", "minimal", "moderate", "heavy"]

    # Confidence scores per attribute (0.0-1.0)
    hook_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    narrative_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    cta_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    pacing_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    music_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    text_overlay_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CreativePatternAnalysis(BaseModel):
    """Wrapper for Gemini structured output."""

    video_id: str
    patterns: CreativePatterns
    processing_time_seconds: float = 0.0
    token_count: int = 0
    error: str | None = None
