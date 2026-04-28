"""Pydantic output models for Gemini structured generation.

All models use ConfigDict(frozen=True). Fields must NOT have default values
(Gemini rejects schemas with defaults). No dict types — use explicit fields.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SocialPost(BaseModel):
    model_config = ConfigDict(frozen=True)

    platform: str
    body: str
    hashtags: list[str]
    suggested_media_type: str | None
    character_count: int


class NewsletterContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str
    preview_text: str
    body_html: str


class ScriptSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    heading: str
    content: str
    duration_seconds: int


class VideoScript(BaseModel):
    model_config = ConfigDict(frozen=True)

    hook: str
    body_sections: list[ScriptSection]
    cta: str
    total_duration_estimate: int
    shot_suggestions: list[str]


class AdCopyVariant(BaseModel):
    model_config = ConfigDict(frozen=True)

    platform: str
    headline: str
    body: str
    cta: str
    display_url: str | None


class RewriteVariant(BaseModel):
    model_config = ConfigDict(frozen=True)

    tone: str
    content: str
    target_platform: str | None
    character_count: int
