"""Persistent video project API."""

from __future__ import annotations

import logging
import shelve
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ...billing.models import BillingContext
from ...conversations.exceptions import ConversationNotFoundError
from ...video_projects import (
    VideoProjectInvalidStateError,
    VideoProjectNotFoundError,
    VideoProjectReferenceInput,
    VideoProjectRevisionConflictError,
    VideoProjectSceneNotFoundError,
)
from ...video_projects.repository import UNSET
from ...video_projects.service import VideoProjectService
from ..dependencies import (
    get_conversation_service,
    get_current_user_id,
    require_pro_generation,
)
from ..rate_limit import limiter

router = APIRouter(prefix="/video-projects", tags=["video-projects"])


class VideoProjectSummaryResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    title: str
    status: str
    revision: int
    updated_at: datetime
    created_at: datetime


class VideoProjectReferenceRequest(BaseModel):
    analysis_id: UUID | None = None
    source_video_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=32)
    title: str = Field(min_length=1, max_length=300)
    thumbnail_url: str | None = Field(default=None, max_length=2000)
    creator_handle: str | None = Field(default=None, max_length=255)

    def to_service_model(self) -> VideoProjectReferenceInput:
        return VideoProjectReferenceInput(
            analysis_id=self.analysis_id,
            source_video_id=self.source_video_id,
            platform=self.platform,
            title=self.title,
            thumbnail_url=self.thumbnail_url,
            creator_handle=self.creator_handle,
        )


class VideoProjectPreviewResponse(BaseModel):
    status: Literal["idle", "generating", "verifying", "ready", "failed"]
    image_url: str | None = None
    storage_key: str | None = None
    qa_score: int | None = None
    qa_feedback: str | None = None
    scene_score: int | None = None
    style_score: int | None = None
    improvement_suggestion: str | None = None
    approved: bool
    error: str | None = None


class VideoProjectSceneResponse(BaseModel):
    id: UUID
    index: int
    title: str
    summary: str
    prompt: str
    duration_seconds: int
    transition: Literal["fade", "cut", "dissolve", "wipe"]
    caption: str
    audio_direction: str = ""
    shot_type: str = "medium"
    camera_movement: str = "static"
    beat: str = "setup"
    preview: VideoProjectPreviewResponse


class VideoProjectReferenceResponse(BaseModel):
    id: UUID
    analysis_id: UUID | None = None
    source_video_id: str | None = None
    platform: str | None = None
    title: str
    thumbnail_url: str | None = None
    creator_handle: str | None = None


class VideoProjectSnapshotResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    title: str
    status: str
    revision: int
    source_analysis_ids: list[UUID]
    anchor_scene_id: UUID | None = None
    references: list[VideoProjectReferenceResponse]
    style_brief_summary: str
    aspect_ratio: Literal["9:16", "16:9", "1:1"]
    resolution: Literal["480p", "720p", "1080p"]
    protagonist_description: str = ""
    target_emotion_arc: str = ""
    anchor_scene_index: int | None = None
    anchor_preview_image_url: str | None = None
    anchor_preview_storage_key: str | None = None
    render_job_id: UUID | None = None
    render_job_status: str | None = None
    render_is_stale: bool
    render_project_revision: int | None = None
    final_video_url: str | None = None
    final_video_url_expires_at: datetime | None = None
    last_error: str | None = None
    scenes: list[VideoProjectSceneResponse]
    created_at: datetime
    updated_at: datetime


class CreateVideoProjectRequest(BaseModel):
    conversation_id: UUID
    title: str = Field(default="Untitled project", max_length=200)
    references: list[VideoProjectReferenceRequest] = Field(default_factory=list, max_length=100)
    source_analysis_ids: list[UUID] = Field(default_factory=list, max_length=100)


class UpdateVideoProjectRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    title: str | None = Field(default=None, max_length=200)
    style_brief_summary: str | None = Field(default=None, max_length=2000)
    anchor_scene_id: UUID | None = None
    protagonist_description: str | None = Field(default=None, max_length=2000)
    target_emotion_arc: str | None = Field(default=None, max_length=200)


class UpdateVideoProjectSceneRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    title: str | None = Field(default=None, max_length=80)
    summary: str | None = Field(default=None, max_length=240)
    prompt: str | None = Field(default=None, max_length=2000)
    duration_seconds: int | None = Field(default=None, ge=1, le=15)
    transition: Literal["fade", "cut", "dissolve", "wipe"] | None = None
    caption: str | None = Field(default=None, max_length=200)
    audio_direction: str | None = Field(default=None, max_length=2000)
    shot_type: Literal[
        "extreme_close_up", "close_up", "medium_close_up",
        "medium", "medium_wide", "wide", "extreme_wide",
        "over_shoulder", "pov",
    ] | None = None
    camera_movement: Literal[
        "static", "pan", "dolly", "tracking", "handheld", "zoom",
    ] | None = None
    beat: Literal["hook", "setup", "rising", "climax", "resolution", "cta"] | None = None
    preview_approved: bool | None = None


class AddVideoProjectReferencesRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    references: list[VideoProjectReferenceRequest] = Field(min_length=1, max_length=100)


class VideoProjectRevisionRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    model: str | None = Field(default=None, description="Image model: gemini, grok, or imagen")


class ReorderVideoProjectScenesRequest(BaseModel):
    expected_revision: int = Field(ge=0)
    scene_ids: list[UUID] = Field(min_length=1, max_length=10)


def _get_video_project_service(request: Request) -> VideoProjectService:
    return request.app.state.video_project_service


def _require_preview_enabled(request: Request) -> None:
    config = request.app.state.generation_config
    if not config.preview_enabled or getattr(request.app.state, "image_preview_service", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "preview_unavailable",
                    "message": "Preview generation is not currently available",
                }
            },
        )


def _require_generation_enabled(request: Request) -> None:
    config = request.app.state.generation_config
    if not config.generation_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "generation_unavailable",
                    "message": "Video generation is not currently available",
                }
            },
        )


async def _ensure_conversation_access(request: Request, conversation_id: UUID, user_id: UUID) -> None:
    conversation_service = get_conversation_service(request)
    try:
        await conversation_service.get_conversation(conversation_id, user_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "conversation_not_found", "message": "Conversation not found"}},
        ) from exc


async def _raise_conflict(
    service: VideoProjectService,
    project_id: UUID,
    user_id: UUID,
    exc: VideoProjectRevisionConflictError,
) -> None:
    latest_snapshot: dict[str, Any] | None = None
    try:
        latest_snapshot = await service.get_project(project_id, user_id)
    except VideoProjectNotFoundError:
        latest_snapshot = None
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "error": {
                "code": "revision_conflict",
                "message": "Video project was updated elsewhere",
                "expected_revision": exc.expected_revision,
                "actual_revision": exc.actual_revision,
                "latest_snapshot": latest_snapshot,
            }
        },
    )


def _map_project_error(exc: Exception) -> HTTPException:
    from ...generation.exceptions import (
        GenerationConcurrentLimitExceeded,
        GenerationDailySpendLimitExceeded,
        GenerationError,
    )

    if isinstance(exc, VideoProjectNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": str(exc)}},
        )
    if isinstance(exc, VideoProjectSceneNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "scene_not_found", "message": str(exc)}},
        )
    if isinstance(exc, VideoProjectInvalidStateError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_state", "message": str(exc)}},
        )
    if isinstance(exc, GenerationConcurrentLimitExceeded):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": {"code": "generation_limit_exceeded", "message": str(exc)}},
        )
    if isinstance(exc, GenerationDailySpendLimitExceeded):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "budget_exceeded", "message": str(exc)}},
        )
    if isinstance(exc, GenerationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "generation_error", "message": str(exc)}},
        )
    logger.exception("Unhandled error in video project endpoint: %s", exc)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error": {"code": "internal_error", "message": "Video project request failed"}},
    )


@router.get("")
@limiter.limit("60/minute")
async def list_video_projects(
    request: Request,
    conversation_id: UUID = Query(...),
    user_id: UUID = Depends(get_current_user_id),
) -> list[VideoProjectSummaryResponse]:
    await _ensure_conversation_access(request, conversation_id, user_id)
    service = _get_video_project_service(request)
    results = await service.list_projects(conversation_id, user_id)
    return [VideoProjectSummaryResponse(**item) for item in results]


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_video_project(
    request: Request,
    body: CreateVideoProjectRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    await _ensure_conversation_access(request, body.conversation_id, user_id)
    service = _get_video_project_service(request)
    try:
        snapshot = await service.create_draft_project(
            conversation_id=body.conversation_id,
            user_id=user_id,
            title=body.title,
            references=[reference.to_service_model() for reference in body.references],
            source_analysis_ids=body.source_analysis_ids,
        )
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


class CreateStoryboardRequest(BaseModel):
    conversation_id: UUID
    analysis_ids: list[UUID] = Field(min_length=1, max_length=20)
    topic: str = Field(max_length=2000)
    style: str = Field(max_length=2000)
    context: str | None = Field(None, max_length=15000, description="Full creative brief for ideation")


_MOCK_STORYBOARD_CACHE = shelve.open("/tmp/freddy_mock.db", flag="c", writeback=False)


def _mock_storyboard_snapshot(
    body: "CreateStoryboardRequest", user_id: UUID
) -> VideoProjectSnapshotResponse:
    """Return a deterministic stub storyboard snapshot for TASK_CLIENT_MODE=mock.

    The autoresearch storyboard canary runs under TASK_CLIENT_MODE=mock for
    cost control. The scorer only reads agent-written ``storyboards/*.json``
    files — the backend response just needs to return a valid shape so the
    IDEATE phase can proceed past the endpoint call. This stub bypasses
    ``create_storyboard_project`` (which requires ``idea_service`` +
    ``creative_service`` + persisted creative patterns) and returns a
    minimal but well-formed snapshot.

    The resulting snapshot is cached in ``_MOCK_STORYBOARD_CACHE`` so that
    subsequent ``GET /v1/video-projects/{project_id}`` calls in mock mode
    can read back the project the agent just created. The cache is
    process-local and cleared on restart, which is fine for the mock
    testing use case — we explicitly do NOT persist to the real
    ``video_projects`` table because it has a ``conversation_id NOT NULL
    REFERENCES conversations`` constraint and mock mode uses synthetic
    conversation IDs that do not exist in the DB.
    """
    from uuid import uuid4
    import json as _json

    now = datetime.now()
    project_id = uuid4()

    try:
        ctx = _json.loads(body.context) if body.context else {}
    except (ValueError, TypeError):
        ctx = {}
    raw_scenes = (ctx.get("scenes") if isinstance(ctx, dict) else None) or [
        {"scene": 1, "prompt": f"{body.topic or 'Untitled'}. {body.style or 'creator-native'}.", "time_seconds": "0-5", "transition_out": "fade"}
    ]

    trans_map = {"hard cut": "cut", "cut": "cut", "fade": "fade", "dissolve": "dissolve", "wipe": "wipe"}
    scenes_list = []
    for i, raw in enumerate(raw_scenes):
        try:
            a, b = str(raw.get("time_seconds", "0-5")).split("-", 1)
            dur = max(1, int(b.strip()) - int(a.strip()))
        except (ValueError, AttributeError):
            dur = 5
        scenes_list.append(VideoProjectSceneResponse(
            id=uuid4(),
            index=i,
            title=f"Scene {i+1}",
            summary=(raw.get("prompt") or "")[:240],
            prompt=raw.get("prompt") or "",
            duration_seconds=dur,
            transition=trans_map.get(str(raw.get("transition_out", "cut")).strip().lower(), "cut"),
            caption="",
            audio_direction="",
            shot_type="medium",
            camera_movement=raw.get("camera") or "static",
            beat=raw.get("beat") or "setup",
            preview=VideoProjectPreviewResponse(status="idle", approved=False),
        ))

    snapshot = VideoProjectSnapshotResponse(
        id=project_id,
        conversation_id=body.conversation_id,
        title=(body.topic or "Untitled project")[:200],
        status="draft",
        revision=0,
        source_analysis_ids=list(body.analysis_ids),
        anchor_scene_id=scenes_list[0].id,
        references=[],
        style_brief_summary=body.style[:200] if body.style else "",
        aspect_ratio="9:16",
        resolution="720p",
        protagonist_description="",
        target_emotion_arc="",
        anchor_scene_index=0,
        anchor_preview_image_url=None,
        anchor_preview_storage_key=None,
        render_job_id=None,
        render_job_status=None,
        render_is_stale=True,
        render_project_revision=None,
        final_video_url=None,
        final_video_url_expires_at=None,
        last_error=None,
        scenes=scenes_list,
        created_at=now,
        updated_at=now,
    )
    _MOCK_STORYBOARD_CACHE[str(project_id)] = snapshot.model_dump_json()
    _MOCK_STORYBOARD_CACHE.sync()
    return snapshot


@router.post("/storyboard", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_storyboard(
    request: Request,
    body: CreateStoryboardRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    """Create a storyboard project from creative pattern analyses."""
    # TASK_CLIENT_MODE=mock short-circuit (A3 fix plan Unit 12): return a
    # deterministic stub so the autoresearch storyboard canary can proceed
    # past IDEATE without requiring GENERATION_GENERATION_ENABLED, persisted
    # creative patterns, or a real Gemini client. The scorer only reads the
    # agent-written storyboards/*.json files, not this response body.
    task_client_mode = getattr(request.app.state, "task_client_mode", None)
    if task_client_mode == "mock":
        return _mock_storyboard_snapshot(body, user_id)

    await _ensure_conversation_access(request, body.conversation_id, user_id)
    service = _get_video_project_service(request)
    try:
        snapshot = await service.create_storyboard_project(
            conversation_id=body.conversation_id,
            user_id=user_id,
            analysis_ids=body.analysis_ids,
            topic=body.topic,
            style=body.style,
            context=body.context,
        )
    except Exception as exc:
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.get("/{project_id}")
@limiter.limit("60/minute")
async def get_video_project(
    request: Request,
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    # Mock-mode readback: autoresearch storyboard canary runs with
    # TASK_CLIENT_MODE=mock and creates projects via create_storyboard's
    # in-memory cache. Check the cache first so GENERATE_FRAMES can read
    # back the project it just created without hitting the real DB
    # (which would fail on the synthetic conversation_id FK).
    task_client_mode = getattr(request.app.state, "task_client_mode", None)
    if task_client_mode == "mock":
        cached = _MOCK_STORYBOARD_CACHE.get(str(project_id))
        if cached is not None:
            return VideoProjectSnapshotResponse.model_validate_json(cached)

    service = _get_video_project_service(request)
    try:
        snapshot = await service.get_project(project_id, user_id)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.patch("/{project_id}")
@limiter.limit("30/minute")
async def update_video_project(
    request: Request,
    project_id: UUID,
    body: UpdateVideoProjectRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    update_data = body.model_dump(exclude_unset=True)
    try:
        snapshot = await service.update_project(
            project_id=project_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            title=update_data.get("title"),
            style_brief_summary=update_data.get("style_brief_summary"),
            anchor_scene_id=update_data.get("anchor_scene_id", UNSET),
            protagonist_description=update_data.get("protagonist_description"),
            target_emotion_arc=update_data.get("target_emotion_arc"),
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.patch("/{project_id}/scenes/{scene_id}")
@limiter.limit("30/minute")
async def update_video_project_scene(
    request: Request,
    project_id: UUID,
    scene_id: UUID,
    body: UpdateVideoProjectSceneRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.update_scene(
            project_id=project_id,
            scene_id=scene_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            title=body.title,
            summary=body.summary,
            prompt=body.prompt,
            duration_seconds=body.duration_seconds,
            transition=body.transition,
            caption=body.caption,
            audio_direction=body.audio_direction,
            shot_type=body.shot_type,
            camera_movement=body.camera_movement,
            beat=body.beat,
            preview_approved=body.preview_approved,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/references")
@limiter.limit("30/minute")
async def add_video_project_references(
    request: Request,
    project_id: UUID,
    body: AddVideoProjectReferencesRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.add_references(
            project_id=project_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            references=[reference.to_service_model() for reference in body.references],
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/preview-anchor")
@limiter.limit("10/minute")
async def preview_video_project_anchor(
    request: Request,
    project_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),  # noqa: ARG001
    _preview_enabled: None = Depends(_require_preview_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.preview_anchor(
            project_id=project_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            **({"model": body.model} if body.model else {}),
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/preview-scenes")
@limiter.limit("10/minute")
async def preview_video_project_scenes(
    request: Request,
    project_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),  # noqa: ARG001
    _preview_enabled: None = Depends(_require_preview_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.preview_scenes(
            project_id=project_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            **({"model": body.model} if body.model else {}),
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/render")
@limiter.limit("10/minute")
async def render_video_project(
    request: Request,
    project_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),
    _generation_enabled: None = Depends(_require_generation_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.render_project(
            project_id=project_id,
            user_id=user_id,
            tier=billing.tier,
            expected_revision=body.expected_revision,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/recompose")
@limiter.limit("10/minute")
async def recompose_video_project(
    request: Request,
    project_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),
    _generation_enabled: None = Depends(_require_generation_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.recompose_project(
            project_id=project_id,
            user_id=user_id,
            tier=billing.tier,
            expected_revision=body.expected_revision,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/scenes/{scene_id}/verify")
@limiter.limit("30/minute")
async def verify_video_project_scene(
    request: Request,
    project_id: UUID,
    scene_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),  # noqa: ARG001
    _preview_enabled: None = Depends(_require_preview_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.verify_scene(
            project_id=project_id,
            scene_id=scene_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/scenes/reorder")
@limiter.limit("30/minute")
async def reorder_video_project_scenes(
    request: Request,
    project_id: UUID,
    body: ReorderVideoProjectScenesRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.reorder_scenes(
            project_id=project_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
            scene_ids=body.scene_ids,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)


@router.post("/{project_id}/scenes/{scene_id}/regenerate")
@limiter.limit("10/minute")
async def regenerate_video_project_scene(
    request: Request,
    project_id: UUID,
    scene_id: UUID,
    body: VideoProjectRevisionRequest,
    user_id: UUID = Depends(get_current_user_id),
    billing: BillingContext = Depends(require_pro_generation),  # noqa: ARG001
    _preview_enabled: None = Depends(_require_preview_enabled),  # noqa: ARG001
) -> VideoProjectSnapshotResponse:
    service = _get_video_project_service(request)
    try:
        snapshot = await service.regenerate_scene(
            project_id=project_id,
            scene_id=scene_id,
            user_id=user_id,
            expected_revision=body.expected_revision,
        )
    except VideoProjectRevisionConflictError as exc:
        await _raise_conflict(service, project_id, user_id, exc)
    except Exception as exc:  # pragma: no cover - mapped branches covered by tests
        raise _map_project_error(exc) from exc
    return VideoProjectSnapshotResponse(**snapshot)
