"""Pydantic models for competitive intelligence data normalization.

These schemas coerce agent-generated competitor data into canonical forms,
preventing drift between sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class AdCreativeCore(BaseModel):
    """Normalized ad creative from any provider."""

    provider: Literal["foreplay", "adyntel", "manual"]
    platform: str = "unknown"
    data_quality: Literal["rich", "metadata_only", "entity_only"] = "entity_only"
    headline: str = ""
    body_text: str = ""
    cta_text: str = ""
    link_url: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    is_active: bool = True
    started_at: str | None = None
    format_type: Literal["video", "static_image", "rich_interactive", "dco", "unknown"] = "unknown"
    persona: str | None = None
    emotional_drivers: list[str] | None = None
    transcription: str | None = None


class VisibilityResult(BaseModel):
    """AI search visibility check result."""

    query: str
    results: list[dict[str, Any]] = Field(default_factory=list)


class DetectResult(BaseModel):
    """GEO infrastructure detection result."""

    llms_txt: str | None = None
    robots_txt: str | None = None
    ai_signals: list[str] = Field(default_factory=list)


class CompetitorProfile(BaseModel):
    """Canonical competitor data structure for a single competitor."""

    name: str
    domain: str
    data_tier: Literal["full", "partial", "scrape_only", "detect_only"] = "detect_only"
    ads: list[AdCreativeCore] = Field(default_factory=list)
    visibility: VisibilityResult | None = None
    detect: DetectResult | None = None
    scrape: dict[str, Any] = Field(default_factory=dict)
    content: dict[str, Any] = Field(default_factory=dict)
    collected_at: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    extras: dict[str, Any] = Field(default_factory=dict)  # Escape hatch for unexpected fields

    def determine_data_tier(self) -> Literal["full", "partial", "scrape_only", "detect_only"]:
        """Auto-determine data tier based on available data."""
        has_ads = len(self.ads) > 0
        has_visibility = self.visibility is not None and len(self.visibility.results) > 0
        has_scrape = bool(self.scrape)
        has_content = bool(self.content)

        if has_ads and (has_visibility or has_content) and has_scrape:
            return "full"
        elif has_ads or (has_visibility and has_scrape):
            return "partial"
        elif has_scrape or has_visibility:
            return "scrape_only"
        return "detect_only"


class AnalysisSection(BaseModel):
    """A single section in a competitor analysis."""

    title: str
    content: str
    data_sources: list[str] = Field(default_factory=list)


class CompetitorAnalysis(BaseModel):
    """Validated competitor analysis structure."""

    competitor: str
    data_tier: str
    sections: list[AnalysisSection] = Field(default_factory=list)
    quality_score: str | None = None
    strategist_test: Literal["PASS", "FAIL"] | None = None
    novelty_test: Literal["PASS", "FAIL"] | None = None
    devils_advocate: str | None = None  # Must be present for mechanical validation
