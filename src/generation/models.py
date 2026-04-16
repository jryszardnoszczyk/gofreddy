"""Generation domain models."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# FFmpeg-safe caption regex — Unicode-aware denylist blocking injection vectors:
# ALL control chars (\x00-\x1f, \x7f), backslash, semicolons, percent, curly braces,
# square brackets, backtick, dollar, pipe, hash (FFmpeg/shell injection vectors).
# Unicode letters, digits, accented chars, CJK, Cyrillic, Arabic, and standard punctuation pass.
CAPTION_SAFE_RE = re.compile(r"^[^\x00-\x1f\x7f\\;%{}\[\]`$|#]+$")


class Cadre(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=0, lt=20)
    prompt: str
    duration_seconds: int = Field(ge=1, le=30)
    transition: Literal["fade", "cut", "dissolve", "wipe"] = "fade"
    seed_image_storage_key: str | None = None


class Caption(BaseModel):
    text: str = Field(max_length=200)
    start_seconds: float
    end_seconds: float
    position: Literal["top", "center", "bottom"] = "bottom"

    @field_validator("text")
    @classmethod
    def validate_ffmpeg_safe(cls, v: str) -> str:
        v = unicodedata.normalize("NFKC", v)
        if not CAPTION_SAFE_RE.match(v):
            msg = "Caption contains unsafe characters for FFmpeg"
            raise ValueError(msg)
        return v


class CompositionSpec(BaseModel):
    cadres: list[Cadre] = Field(min_length=1, max_length=20)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    resolution: Literal["480p", "720p", "1080p"] = "720p"
    caption_preset: Literal["default", "hormozi", "minimal", "elegant", "cinematic", "neon"] = "default"
    captions: list[Caption] = Field(default_factory=list)
    source_analysis_ids: list[UUID] = Field(default_factory=list, max_length=25)


class StoryboardSceneDraft(BaseModel):
    index: int = Field(ge=0, lt=20)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    audio_direction: str = Field(min_length=1)
    caption: str = Field(default="", max_length=200, description="Dialogue or narration text for subtitles (max 200 characters, ASCII only)")
    shot_type: Literal[
        "extreme_close_up", "close_up", "medium_close_up",
        "medium", "medium_wide", "wide", "extreme_wide",
        "over_shoulder", "pov",
    ] = "medium"
    camera_movement: Literal[
        "static", "pan", "dolly", "tracking", "handheld", "zoom",
    ] = "static"
    beat: Literal["hook", "setup", "rising", "climax", "resolution", "cta"] = "setup"
    duration_seconds: int = Field(ge=1, le=30)
    transition: Literal["fade", "cut", "dissolve", "wipe"] = "fade"

    @field_validator("audio_direction", mode="before")
    @classmethod
    def _coerce_empty_audio(cls, v: str | None) -> str:
        """Convert empty to sentinel for backward compat with old storyboard data."""
        if not v:
            return "Not specified"
        return v


class StoryboardDraft(BaseModel):
    scenes: list[StoryboardSceneDraft] = Field(min_length=1, max_length=20)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    resolution: Literal["480p", "720p", "1080p"] = "720p"
    protagonist_description: str = Field(min_length=1)
    target_emotion_arc: str = Field(min_length=1)

    @field_validator("protagonist_description", "target_emotion_arc", mode="before")
    @classmethod
    def _coerce_empty_story_fields(cls, v: str | None) -> str:
        """Convert empty to sentinel for backward compat with old storyboard data."""
        if not v:
            return "Not specified"
        return v


@dataclass(frozen=True, slots=True)
class CaptionStyle:
    """Immutable caption style preset for FFmpeg ASS/SRT rendering."""
    name: str
    font_name: str = "Arial"
    font_size: int = 24
    primary_colour: str = "&H00FFFFFF"  # ASS hex AABBGGRR
    outline_colour: str = "&H00000000"
    back_colour: str = "&H80000000"
    border_style: int = 3  # 3 = opaque box behind text
    outline_width: int = 2
    shadow_depth: int = 0
    bold: bool = False
    italic: bool = False
    alignment: int = 2  # ASS: 2=bottom-center, 6=top-center, 10=middle-center
    margin_v: int = 30


@dataclass(frozen=True, slots=True)
class PreviewResult:
    image_url: str
    r2_key: str
    local_path: str
    qa_score: int | None = None
    qa_feedback: str | None = None
    model_used: str = "gemini"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    scene_score: int          # 1-10: does image match scene description?
    style_score: int          # 1-10: does image match frame 1 style?
    overall_score: int        # min(scene_score, style_score)
    feedback: str             # one-sentence weakest aspect
    improvement_suggestion: str  # actionable prompt refinement


@dataclass(frozen=True, slots=True)
class GenerationResult:
    generation_id: UUID
    video_url: str | None
    video_url_expires_at: datetime | None
    duration_seconds: int
    cost_cents: int
    cadre_count: int
