"""Video project domain models."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Self
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VideoProjectRecord:
    id: UUID
    conversation_id: UUID
    title: str
    status: str
    revision: int
    source_analysis_ids: list[UUID]
    style_brief_summary: str
    aspect_ratio: str
    resolution: str
    anchor_scene_id: UUID | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    protagonist_description: str = ""
    target_emotion_arc: str = ""

    @classmethod
    def from_row(cls, row: Any) -> Self:
        data = dict(row)
        ids = data.get("source_analysis_ids") or []
        data["source_analysis_ids"] = [value if isinstance(value, UUID) else UUID(str(value)) for value in ids]
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True, slots=True)
class VideoProjectSceneRecord:
    id: UUID
    project_id: UUID
    position: int
    title: str
    summary: str
    prompt: str
    duration_seconds: int
    transition: str
    caption: str
    preview_status: str
    preview_storage_key: str | None
    preview_qa_score: int | None
    preview_qa_feedback: str | None
    preview_scene_score: int | None
    preview_style_score: int | None
    preview_improvement_suggestion: str | None
    preview_approved: bool
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    audio_direction: str = ""
    shot_type: str = "medium"
    camera_movement: str = "static"
    beat: str = "setup"

    @classmethod
    def from_row(cls, row: Any) -> Self:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in dict(row).items() if k in known})


@dataclass(frozen=True, slots=True)
class VideoProjectReferenceRecord:
    id: UUID
    project_id: UUID
    analysis_id: UUID | None
    source_video_id: str | None
    platform: str | None
    title: str
    thumbnail_url: str | None
    creator_handle: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> Self:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in dict(row).items() if k in known})


@dataclass(frozen=True, slots=True)
class VideoProjectGenerationJob:
    id: UUID
    status: str
    project_revision: int | None
    r2_key: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> Self:
        keys = {"id", "status", "project_revision", "r2_key", "error", "created_at", "updated_at"}
        return cls(**{k: v for k, v in dict(row).items() if k in keys})


@dataclass(frozen=True, slots=True)
class VideoProjectSnapshot:
    project: VideoProjectRecord
    scenes: list[VideoProjectSceneRecord]
    references: list[VideoProjectReferenceRecord]
    generation_job: VideoProjectGenerationJob | None = None


@dataclass(frozen=True, slots=True)
class VideoProjectReferenceInput:
    analysis_id: UUID | None
    source_video_id: str | None
    platform: str | None
    title: str
    thumbnail_url: str | None
    creator_handle: str | None


@dataclass(frozen=True, slots=True)
class VideoProjectSceneInput:
    title: str
    summary: str
    prompt: str
    duration_seconds: int
    transition: str
    caption: str = ""
    audio_direction: str = ""
    shot_type: str = "medium"
    camera_movement: str = "static"
    beat: str = "setup"
