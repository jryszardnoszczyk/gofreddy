"""Extended brand schemas with timestamp_end for validation spike."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas import (
    BrandContext,
    BrandDetectionSource,
    BrandSentiment,
    Confidence,
)


class ExtendedBrandMention(BaseModel):
    """BrandMention with timestamp_end added for exposure duration validation."""

    brand_name: str = Field(max_length=100)
    detection_source: BrandDetectionSource
    confidence: Confidence
    timestamp_start: str | None = Field(
        default=None, description="M:SS format — when brand first appears"
    )
    timestamp_end: str | None = Field(
        default=None, description="M:SS format — when brand disappears"
    )
    sentiment: BrandSentiment
    context: BrandContext
    evidence: str = Field(max_length=500)
    is_competitor: bool = False


class ExtendedBrandAnalysis(BaseModel):
    """BrandAnalysis using ExtendedBrandMention with timestamp_end."""

    video_id: str
    brand_mentions: list[ExtendedBrandMention] = Field(
        default_factory=list, max_length=50
    )
    primary_brand: str | None = None
    overall_sentiment: BrandSentiment | None = None
    has_sponsorship_signals: bool = False
    sponsoring_brand: str | None = None
    overall_confidence: Confidence
    processing_time_seconds: float = 0.0
    token_count: int = 0
    error: str | None = None
