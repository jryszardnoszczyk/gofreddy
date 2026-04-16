"""Analysis data models."""

import json
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Self
from uuid import UUID, uuid4

from ..schemas import (
    ContentCategory,
    ModerationDetection,
    RiskDetection,
    SponsoredContent,
    VideoAnalysis,
)


@dataclass(frozen=True, slots=True)
class VideoAnalysisRecord:
    """Database record for video analysis."""

    id: UUID
    video_id: UUID
    cache_key: str
    overall_safe: bool
    overall_confidence: float
    risks_detected: list[dict[str, Any]]

    # NEW fields (PR-009)
    summary: str
    content_categories: list[dict[str, Any]]
    moderation_flags: list[dict[str, Any]]
    sponsored_content: dict[str, Any] | None

    processing_time_seconds: float | None
    token_count: int | None
    error: str | None
    model_version: str
    analyzed_at: datetime | None
    analysis_cost_usd: float | None
    title: str | None = None

    @classmethod
    def from_analysis(
        cls,
        analysis: VideoAnalysis,
        *,
        video_uuid: UUID,
        cache_key: str,
        model_version: str,
        analysis_cost_usd: float | None = None,
        title: str | None = None,
    ) -> Self:
        """Create record from Pydantic analysis result."""
        return cls(
            id=uuid4(),
            video_id=video_uuid,
            cache_key=cache_key,
            overall_safe=analysis.overall_safe,
            overall_confidence=analysis.overall_confidence,
            risks_detected=[r.model_dump() for r in (analysis.risks_detected or [])],
            summary=analysis.summary,
            content_categories=[c.model_dump() for c in (analysis.content_categories or [])],
            moderation_flags=[m.model_dump() for m in (analysis.moderation_flags or [])],
            sponsored_content=analysis.sponsored_content.model_dump() if analysis.sponsored_content else None,
            title=title,
            processing_time_seconds=analysis.processing_time_seconds,
            token_count=analysis.token_count,
            error=analysis.error,
            model_version=model_version,
            analyzed_at=None,  # Set by DB DEFAULT NOW()
            analysis_cost_usd=analysis_cost_usd,
        )

    _JSONB_FIELDS = frozenset({
        "risks_detected", "content_categories", "moderation_flags", "sponsored_content",
    })

    @classmethod
    def from_row(cls, row: Any) -> Self:
        """Create record from database row."""
        known = {f.name for f in fields(cls)}
        data = {}
        for k, v in dict(row).items():
            if k not in known:
                continue
            if k in cls._JSONB_FIELDS and isinstance(v, str):
                v = json.loads(v)
            data[k] = v
        return cls(**data)

    def to_video_analysis(self) -> VideoAnalysis:
        """Convert back to Pydantic model for API responses."""
        risks = [RiskDetection(**r) for r in self.risks_detected] if self.risks_detected else []
        categories = [ContentCategory(**c) for c in self.content_categories] if self.content_categories else []
        moderation = [ModerationDetection(**m) for m in self.moderation_flags] if self.moderation_flags else []
        sponsored = SponsoredContent(**self.sponsored_content) if self.sponsored_content else None

        return VideoAnalysis(
            video_id=str(self.video_id),
            overall_safe=self.overall_safe,
            overall_confidence=self.overall_confidence,
            risks_detected=risks,
            summary=self.summary or "",
            content_categories=categories,
            moderation_flags=moderation,
            sponsored_content=sponsored,
            processing_time_seconds=self.processing_time_seconds or 0.0,
            token_count=self.token_count or 0,
            error=self.error,
        )


@dataclass(frozen=True, slots=True)
class LibraryFilters:
    """Immutable filter parameters for library queries."""

    platform: str | None = None
    search: str | None = None
    cursor_date: datetime | None = None
    cursor_id: UUID | None = None
    limit: int = 20


@dataclass(frozen=True, slots=True)
class LibraryItem:
    """Single item in library listing."""

    id: UUID
    video_id: UUID
    title: str | None
    platform: str
    overall_safe: bool
    moderation_flags: list[dict[str, Any]]
    analyzed_at: datetime
    has_brands: bool
    has_demographics: bool
    has_deepfake: bool
    has_creative: bool
    has_fraud: bool


@dataclass(frozen=True, slots=True)
class CreatorGroup:
    """A creator with aggregated analysis stats."""

    creator_id: UUID
    platform: str
    username: str
    video_count: int
    last_analyzed_at: datetime


@dataclass(frozen=True, slots=True)
class SessionGroup:
    """A conversation with analysis item counts."""

    conversation_id: UUID
    title: str | None
    item_count: int
    last_updated_at: datetime
