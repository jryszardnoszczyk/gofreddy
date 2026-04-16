"""Service layer for persistent video projects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from uuid import UUID

from ..analysis.repository import PostgresAnalysisRepository
from ..billing.tiers import Tier
from ..creative import CreativePatternService
from ..generation.config import GenerationSettings
from ..generation.idea_service import IdeaService
from ..generation.models import CAPTION_SAFE_RE, CompositionSpec
from ..generation.prompt_utils import sanitize_prompt
from ..generation.text_utils import strip_fillers
from ..generation.service import GenerationService
from ..generation.storyboard_evaluator import StoryboardEvaluator
from ..generation.storage import PRESIGNED_URL_EXPIRY, R2GenerationStorage
from .exceptions import (
    VideoProjectInvalidStateError,
    VideoProjectNotFoundError,
    VideoProjectRevisionConflictError,
    VideoProjectSceneNotFoundError,
)
from .models import (
    VideoProjectRecord,
    VideoProjectReferenceInput,
    VideoProjectSceneInput,
    VideoProjectSnapshot,
)
from .repository import PostgresVideoProjectRepository, UNSET

_CAPTION_SAFE = CAPTION_SAFE_RE  # unified import from generation.models


class VideoProjectService:
    def __init__(
        self,
        repository: PostgresVideoProjectRepository,
        generation_service: GenerationService,
        generation_storage: R2GenerationStorage | None,
        generation_settings: GenerationSettings,
        idea_service: IdeaService | None,
        analysis_repository: PostgresAnalysisRepository | None = None,
        creative_service: CreativePatternService | None = None,
        image_preview_service: Any | None = None,
        storyboard_evaluator: StoryboardEvaluator | None = None,
    ) -> None:
        self._repository = repository
        self._generation_service = generation_service
        self._generation_storage = generation_storage
        self._generation_settings = generation_settings
        self._idea_service = idea_service
        self._analysis_repository = analysis_repository
        self._creative_service = creative_service
        self._image_preview_service = image_preview_service
        self._storyboard_evaluator = storyboard_evaluator

    async def list_projects(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[dict[str, Any]]:
        records = await self._repository.list_projects(conversation_id, user_id)
        return [
            {
                "id": str(record.id),
                "conversation_id": str(record.conversation_id),
                "title": record.title,
                "status": record.status,
                "revision": record.revision,
                "updated_at": record.updated_at.isoformat(),
                "created_at": record.created_at.isoformat(),
            }
            for record in records
        ]

    async def get_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        snapshot = await self._repository.get_project(project_id, user_id)
        if snapshot is None:
            raise VideoProjectNotFoundError(project_id)
        return await self._serialize_snapshot(snapshot)

    async def get_latest_project(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        snapshot = await self._repository.get_latest_project_for_conversation(conversation_id, user_id)
        if snapshot is None:
            return None
        return await self._serialize_snapshot(snapshot)

    async def create_draft_project(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        title: str,
        references: list[VideoProjectReferenceInput],
        source_analysis_ids: list[UUID] | None = None,
    ) -> dict[str, Any]:
        analysis_ids = source_analysis_ids or [
            reference.analysis_id
            for reference in references
            if reference.analysis_id is not None
        ]
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._repository.create_project(
                    conn,
                    conversation_id=conversation_id,
                    title=title.strip() or "Untitled project",
                    status="draft",
                    style_brief_summary="",
                    source_analysis_ids=sorted(set(analysis_ids), key=str),
                    aspect_ratio=self._generation_settings.default_aspect_ratio,
                    resolution="720p",
                )
                if references:
                    await self._repository.add_references(
                        conn,
                        project_id=project.id,
                        references=references,
                    )
                snapshot = await self._repository._load_snapshot(conn, project)
        return await self._serialize_snapshot(snapshot)

    async def create_storyboard_project(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        analysis_ids: list[UUID],
        topic: str,
        style: str,
        title: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        import logging as _logging
        _log = _logging.getLogger(__name__)

        if self._idea_service is None:
            return await self._create_brief_storyboard_project(
                conversation_id=conversation_id,
                user_id=user_id,
                analysis_ids=analysis_ids,
                topic=topic,
                style=style,
                title=title,
            )
        if analysis_ids and self._creative_service is None:
            raise VideoProjectInvalidStateError("Storyboard ideation is unavailable")
        patterns = await self._load_creative_patterns(analysis_ids) if analysis_ids else []
        if analysis_ids and not patterns:
            raise VideoProjectInvalidStateError(
                "No creative patterns found for the provided analyses. Run creative pattern analysis first."
            )
        storyboard_context = context
        if not storyboard_context or len(storyboard_context.strip()) < 100:
            storyboard_context = (
                f"Create a 30-second storyboard for {topic.strip() or 'the requested product demo'}. "
                f"Style: {style.strip() or 'polished app demo'}. Include a hook, product value, "
                "three to five concise scenes, captions, camera direction, and a final call to action."
            )

        # Generate and evaluate storyboard draft with quality gate
        threshold = self._generation_settings.storyboard_evaluator_threshold
        best_draft = None
        best_score = 0.0
        max_eval_attempts = 3
        draft = None  # set in loop; guaranteed by max_eval_attempts > 0

        for attempt in range(1, max_eval_attempts + 1):
            draft = await self._idea_service.generate_storyboard_draft(
                creative_patterns=patterns,
                topic=topic,
                style=style,
                context=storyboard_context,
            )

            if self._storyboard_evaluator:
                eval_result = await self._storyboard_evaluator.evaluate(draft, context=storyboard_context)
                if eval_result:
                    _log.info(
                        "Storyboard evaluation attempt %d/%d: overall=%.2f (%s)",
                        attempt, max_eval_attempts, eval_result.overall_score, eval_result.feedback,
                    )
                    if eval_result.overall_score > best_score:
                        best_draft = draft
                        best_score = eval_result.overall_score
                    if eval_result.overall_score >= threshold:
                        break
                    if attempt < max_eval_attempts:
                        _log.info("Score %.2f < threshold %.1f, retrying...", eval_result.overall_score, threshold)
                        continue
                    # All retries exhausted — use best draft (never discard all work)
                    _log.warning(
                        "All %d attempts scored below %.1f (best: %.2f). Using best draft.",
                        max_eval_attempts, threshold, best_score,
                    )
                    draft = best_draft or draft
                else:
                    break  # Evaluation failed non-blocking — keep draft
            else:
                break  # No evaluator — keep draft

        scene_inputs = [
            VideoProjectSceneInput(
                title=scene.title,
                summary=scene.summary,
                prompt=scene.prompt,
                duration_seconds=scene.duration_seconds,
                transition=scene.transition,
                caption=scene.caption,
                audio_direction=scene.audio_direction,
                shot_type=scene.shot_type,
                camera_movement=scene.camera_movement,
                beat=scene.beat,
            )
            for scene in draft.scenes
        ]
        reference_inputs = await self._build_analysis_references(analysis_ids)
        project_title = title or topic.strip() or "Untitled project"

        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._repository.create_project(
                    conn,
                    conversation_id=conversation_id,
                    title=project_title,
                    status="draft",
                    style_brief_summary=self._build_style_summary(style, analysis_ids),
                    source_analysis_ids=analysis_ids,
                    aspect_ratio=draft.aspect_ratio,
                    resolution=draft.resolution,
                    protagonist_description=draft.protagonist_description,
                    target_emotion_arc=draft.target_emotion_arc,
                )
                for index, scene in enumerate(scene_inputs):
                    created = await self._repository.insert_scene(
                        conn,
                        project_id=project.id,
                        position=index,
                        scene=scene,
                    )
                    if index == 0:
                        project = await self._repository.update_project(
                            conn,
                            project_id=project.id,
                            anchor_scene_id=created.id,
                        )
                if reference_inputs:
                    await self._repository.add_references(
                        conn,
                        project_id=project.id,
                        references=reference_inputs,
                    )
                snapshot = await self._repository._load_snapshot(conn, project)
        return await self._serialize_snapshot(snapshot)

    async def _create_brief_storyboard_project(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        analysis_ids: list[UUID],
        topic: str,
        style: str,
        title: str | None = None,
    ) -> dict[str, Any]:
        project_title = title or topic.strip() or "Untitled project"
        topic_text = sanitize_prompt(topic).strip() or "the requested product demo"
        style_text = sanitize_prompt(style).strip() or "polished app demo"
        scene_inputs = [
            VideoProjectSceneInput(
                title="Hook",
                summary=f"Open with the core problem {topic_text} solves.",
                prompt=f"{style_text} opening shot: a busy user checks their phone, sees a clear fitness goal, and starts the app with one tap.",
                duration_seconds=5,
                transition="cut",
                caption="Fit progress into any day.",
                audio_direction="Upbeat intro hit, quick app tap.",
                shot_type="close-up",
                camera_movement="push-in",
                beat="hook",
            ),
            VideoProjectSceneInput(
                title="Plan",
                summary="Show the app building a personal workout plan.",
                prompt=f"{style_text} app UI sequence showing personalized workout recommendations, time filters, and coach guidance for {topic_text}.",
                duration_seconds=6,
                transition="cut",
                caption="A plan built around your schedule.",
                audio_direction="Confident beat with light UI clicks.",
                shot_type="screen insert",
                camera_movement="smooth pan",
                beat="setup",
            ),
            VideoProjectSceneInput(
                title="Workout",
                summary="Demonstrate the user completing a guided session.",
                prompt=f"{style_text} home workout scene with timer, movement cues, and encouraging progress feedback from the fitness app.",
                duration_seconds=7,
                transition="cut",
                caption="Guided workouts wherever you are.",
                audio_direction="Beat lifts, subtle exercise sounds.",
                shot_type="medium",
                camera_movement="tracking",
                beat="demo",
            ),
            VideoProjectSceneInput(
                title="Progress",
                summary="Highlight tracking, streaks, and community momentum.",
                prompt=f"{style_text} montage of progress rings, streak badges, and a community challenge leaderboard proving the app keeps users motivated.",
                duration_seconds=6,
                transition="dissolve",
                caption="Track every win and keep going.",
                audio_direction="Rising synth pulse.",
                shot_type="montage",
                camera_movement="fast cuts",
                beat="proof",
            ),
            VideoProjectSceneInput(
                title="Call to Action",
                summary="Close with a simple product promise and download cue.",
                prompt=f"{style_text} hero end card with the fitness app dashboard, app icon, and confident download call to action.",
                duration_seconds=6,
                transition="fade",
                caption="Start your first 30 seconds today.",
                audio_direction="Resolved final hit.",
                shot_type="hero",
                camera_movement="static",
                beat="cta",
            ),
        ]

        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._repository.create_project(
                    conn,
                    conversation_id=conversation_id,
                    title=project_title,
                    status="draft",
                    style_brief_summary=f"Brief-based storyboard. Style: {style_text}.",
                    source_analysis_ids=analysis_ids,
                    aspect_ratio=self._generation_settings.default_aspect_ratio,
                    resolution="720p",
                    protagonist_description="A motivated app user fitting a workout into a busy day.",
                    target_emotion_arc="From time pressure to confident momentum.",
                )
                for index, scene in enumerate(scene_inputs):
                    created = await self._repository.insert_scene(
                        conn,
                        project_id=project.id,
                        position=index,
                        scene=scene,
                    )
                    if index == 0:
                        project = await self._repository.update_project(
                            conn,
                            project_id=project.id,
                            anchor_scene_id=created.id,
                        )
                snapshot = await self._repository._load_snapshot(conn, project)
        return await self._serialize_snapshot(snapshot)

    async def generate_from_inspiration(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        tier: Tier,
        analysis_ids: list[UUID],
        topic: str,
        style: str,
        title: str | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        if self._idea_service is None or self._creative_service is None:
            raise VideoProjectInvalidStateError("Storyboard ideation is unavailable")
        patterns = await self._load_creative_patterns(analysis_ids)
        if not patterns:
            raise VideoProjectInvalidStateError(
                "No creative patterns found for the provided analyses. Run creative pattern analysis first."
            )
        draft = await self._idea_service.generate_storyboard_draft(
            creative_patterns=patterns,
            topic=topic,
            style=style,
            context=context,
        )
        scene_inputs = [
            VideoProjectSceneInput(
                title=scene.title,
                summary=scene.summary,
                prompt=scene.prompt,
                duration_seconds=scene.duration_seconds,
                transition=scene.transition,
                caption=scene.caption,
                audio_direction=scene.audio_direction,
                shot_type=scene.shot_type,
                camera_movement=scene.camera_movement,
                beat=scene.beat,
            )
            for scene in draft.scenes
        ]
        reference_inputs = await self._build_analysis_references(analysis_ids)
        project_title = title or topic.strip() or "Untitled project"
        job_id: UUID | None = None

        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._repository.create_project(
                    conn,
                    conversation_id=conversation_id,
                    title=project_title,
                    status="draft",
                    style_brief_summary=self._build_style_summary(style, analysis_ids),
                    source_analysis_ids=analysis_ids,
                    aspect_ratio=draft.aspect_ratio,
                    resolution=draft.resolution,
                    protagonist_description=draft.protagonist_description,
                    target_emotion_arc=draft.target_emotion_arc,
                )
                for index, scene in enumerate(scene_inputs):
                    created = await self._repository.insert_scene(
                        conn,
                        project_id=project.id,
                        position=index,
                        scene=scene,
                    )
                    if index == 0:
                        project = await self._repository.update_project(
                            conn,
                            project_id=project.id,
                            anchor_scene_id=created.id,
                        )
                if reference_inputs:
                    await self._repository.add_references(
                        conn,
                        project_id=project.id,
                        references=reference_inputs,
                    )
                scenes = await self._repository.list_scenes(conn, project.id)
                next_revision = project.revision + 1
                result = await self._generation_service.submit_job(
                    user_id,
                    self._build_composition_spec(project, scenes),
                    tier,
                    video_project_id=project.id,
                    project_revision=next_revision,
                    conn=conn,
                    dispatch=False,
                )
                job_id = result["job_id"]
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status="rendering",
                    last_error=None,
                    revision=next_revision,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)

        if job_id is not None:
            await self._generation_service.dispatch_job(job_id)
        return await self._serialize_snapshot(snapshot)

    async def update_project(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
        title: str | None = None,
        style_brief_summary: str | None = None,
        anchor_scene_id: UUID | None | object = UNSET,
        protagonist_description: str | None = None,
        target_emotion_arc: str | None = None,
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                if anchor_scene_id is not UNSET and anchor_scene_id is not None:
                    anchor_scene = await self._repository.get_scene(conn, project.id, anchor_scene_id)
                    if anchor_scene is None:
                        raise VideoProjectSceneNotFoundError(anchor_scene_id)
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    title=title if title is not None else UNSET,
                    style_brief_summary=style_brief_summary if style_brief_summary is not None else UNSET,
                    anchor_scene_id=anchor_scene_id,
                    protagonist_description=protagonist_description if protagonist_description is not None else UNSET,
                    target_emotion_arc=target_emotion_arc if target_emotion_arc is not None else UNSET,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def update_scene(
        self,
        *,
        project_id: UUID,
        scene_id: UUID,
        user_id: UUID,
        expected_revision: int,
        title: str | None = None,
        summary: str | None = None,
        prompt: str | None = None,
        duration_seconds: int | None = None,
        transition: str | None = None,
        caption: str | None = None,
        audio_direction: str | None = None,
        shot_type: str | None = None,
        camera_movement: str | None = None,
        beat: str | None = None,
        preview_approved: bool | None = None,
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scene = await self._repository.get_scene(conn, project_id, scene_id)
                if scene is None:
                    raise VideoProjectSceneNotFoundError(scene_id)
                prompt_value = sanitize_prompt(prompt) if prompt is not None else None
                caption_value = self._validate_caption(strip_fillers(caption)) if caption is not None else None
                if audio_direction is not None:
                    audio_direction = sanitize_prompt(audio_direction)
                if preview_approved and (scene.preview_status != "ready" or not scene.preview_storage_key):
                    raise VideoProjectInvalidStateError("Scene preview must be ready before it can be approved")
                invalidates_preview = any(
                    value is not None
                    for value in (prompt_value, duration_seconds, transition)
                )
                await self._repository.update_scene(
                    conn,
                    scene_id=scene.id,
                    title=title if title is not None else UNSET,
                    summary=summary if summary is not None else UNSET,
                    prompt=prompt_value if prompt is not None else UNSET,
                    duration_seconds=duration_seconds if duration_seconds is not None else UNSET,
                    transition=transition if transition is not None else UNSET,
                    caption=caption_value if caption is not None else UNSET,
                    audio_direction=audio_direction if audio_direction is not None else UNSET,
                    shot_type=shot_type if shot_type is not None else UNSET,
                    camera_movement=camera_movement if camera_movement is not None else UNSET,
                    beat=beat if beat is not None else UNSET,
                    preview_approved=(
                        preview_approved
                        if preview_approved is not None and not invalidates_preview
                        else (False if invalidates_preview else UNSET)
                    ),
                    preview_status="idle" if invalidates_preview else UNSET,
                    preview_storage_key=None if invalidates_preview else UNSET,
                    preview_qa_score=None if invalidates_preview else UNSET,
                    preview_qa_feedback=None if invalidates_preview else UNSET,
                    preview_scene_score=None if invalidates_preview else UNSET,
                    preview_style_score=None if invalidates_preview else UNSET,
                    preview_improvement_suggestion=None if invalidates_preview else UNSET,
                    last_error=None if invalidates_preview else UNSET,
                )
                scenes = await self._repository.list_scenes(conn, project.id)
                job = await self._repository.latest_generation_job(conn, project.id)
                render_status = job.status if job else None
                render_is_stale = bool(job and job.project_revision is not None and job.project_revision < project.revision + 1)
                next_status = self._derive_project_status(
                    current_status=project.status,
                    scenes=scenes,
                    render_status=render_status,
                    render_is_stale=render_is_stale,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status=next_status,
                    last_error=None,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def get_transcript(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        snapshot = await self._repository.get_project(project_id, user_id)
        if snapshot is None:
            raise VideoProjectNotFoundError(project_id)
        scenes = sorted(snapshot.scenes, key=lambda s: s.position)
        transcript: list[dict[str, Any]] = []
        cumulative = 0.0
        for scene in scenes:
            dur = scene.duration_seconds
            transcript.append({
                "scene_index": scene.position,
                "scene_id": str(scene.id),
                "title": scene.title,
                "caption": scene.caption or "",
                "start_seconds": round(cumulative, 2),
                "end_seconds": round(cumulative + dur, 2),
                "duration_seconds": dur,
            })
            cumulative += dur
        return {
            "project_id": str(project_id),
            "total_duration_seconds": round(cumulative, 2),
            "scene_count": len(scenes),
            "transcript": transcript,
        }

    async def delete_scene(
        self,
        *,
        project_id: UUID,
        scene_id: UUID,
        user_id: UUID,
        expected_revision: int,
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scene_count = await self._repository.count_scenes(conn, project.id)
                if scene_count <= 1:
                    raise VideoProjectInvalidStateError("Cannot delete the last scene in a project")
                deleted = await self._repository.delete_scene(conn, project.id, scene_id)
                if deleted is None:
                    raise VideoProjectSceneNotFoundError(scene_id)
                await self._repository.recompact_positions(conn, project.id)
                # Reassign anchor if deleted scene was the anchor
                new_anchor = project.anchor_scene_id
                if project.anchor_scene_id == scene_id:
                    first_scene = await self._repository.get_scene_by_position(conn, project.id, 0)
                    new_anchor = first_scene.id if first_scene else None
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    anchor_scene_id=new_anchor,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def clean_transcript(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scenes = await self._repository.list_scenes(conn, project.id)
                changes: list[dict[str, str]] = []
                for scene in scenes:
                    if not scene.caption:
                        continue
                    cleaned = strip_fillers(scene.caption)
                    if cleaned != scene.caption:
                        changes.append({
                            "scene_id": str(scene.id),
                            "before": scene.caption,
                            "after": cleaned,
                        })
                        await self._repository.update_scene(
                            conn, scene_id=scene.id, caption=cleaned,
                        )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        result = await self._serialize_snapshot(snapshot)
        result["filler_removal"] = {
            "scenes_cleaned": len(changes),
            "changes": changes,
        }
        return result

    async def add_references(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
        references: list[VideoProjectReferenceInput],
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                await self._repository.add_references(conn, project_id=project.id, references=references)
                source_analysis_ids = sorted(
                    {
                        *project.source_analysis_ids,
                        *[ref.analysis_id for ref in references if ref.analysis_id is not None],
                    },
                    key=str,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    source_analysis_ids=source_analysis_ids,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def reorder_scenes(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
        scene_ids: list[UUID],
    ) -> dict[str, Any]:
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scenes = await self._repository.list_scenes(conn, project.id)
                by_id = {scene.id: scene for scene in scenes}
                if set(scene_ids) != set(by_id):
                    raise VideoProjectInvalidStateError("Scene reorder payload must include every scene exactly once")
                for position, scene_id in enumerate(scene_ids):
                    await self._repository.update_scene(conn, scene_id=scene_id, position=position)
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    revision=project.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def preview_anchor(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
        model: str = "gemini",
    ) -> dict[str, Any]:
        if not self._generation_settings.preview_enabled or self._image_preview_service is None:
            raise VideoProjectInvalidStateError("Preview generation is not available")
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                if project.anchor_scene_id is None:
                    raise VideoProjectInvalidStateError("Project does not have an anchor scene")
                anchor_scene = await self._repository.get_scene(conn, project.id, project.anchor_scene_id)
                if anchor_scene is None:
                    raise VideoProjectSceneNotFoundError(project.anchor_scene_id)
                await self._repository.update_scene(
                    conn,
                    scene_id=anchor_scene.id,
                    preview_status="generating",
                    last_error=None,
                )
            result = await self._image_preview_service.generate_preview(
                user_id,
                anchor_scene.prompt,
                aspect_ratio=project.aspect_ratio,
                model=model,
            )
            async with conn.transaction():
                locked = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                await self._repository.update_scene(
                    conn,
                    scene_id=anchor_scene.id,
                    preview_status="ready",
                    preview_storage_key=result.r2_key,
                    preview_qa_score=result.qa_score,
                    preview_qa_feedback=result.qa_feedback,
                    preview_approved=False,
                    last_error=None,
                )
                scenes = await self._repository.list_scenes(conn, project.id)
                next_status = self._derive_project_status(
                    current_status="previewing_anchor",
                    scenes=scenes,
                    render_status=None,
                    render_is_stale=True,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status=next_status,
                    last_error=None,
                    revision=locked.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def preview_scenes(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
        model: str = "gemini",
    ) -> dict[str, Any]:
        if not self._generation_settings.preview_enabled or self._image_preview_service is None:
            raise VideoProjectInvalidStateError("Preview generation is not available")
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                if project.anchor_scene_id is None:
                    raise VideoProjectInvalidStateError("Project does not have an anchor scene")
                scenes = await self._repository.list_scenes(conn, project.id)
                anchor_scene = next((scene for scene in scenes if scene.id == project.anchor_scene_id), None)
                if anchor_scene is None or not anchor_scene.preview_storage_key:
                    raise VideoProjectInvalidStateError("Anchor preview must exist before previewing remaining scenes")
                targets = [scene for scene in scenes if scene.id != anchor_scene.id]
                if not targets:
                    raise VideoProjectInvalidStateError("No remaining scenes to preview")
                for scene in targets:
                    await self._repository.update_scene(conn, scene_id=scene.id, preview_status="generating", last_error=None)
            results = await self._image_preview_service.generate_batch(
                user_id,
                [scene.prompt for scene in targets],
                style_ref_path=anchor_scene.preview_storage_key,
                aspect_ratio=project.aspect_ratio,
                model=model,
            )
            async with conn.transaction():
                locked = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                for scene, result in zip(targets, results):
                    if result is None:
                        await self._repository.update_scene(
                            conn,
                            scene_id=scene.id,
                            preview_status="failed",
                            preview_storage_key=None,
                            preview_qa_score=None,
                            preview_qa_feedback="Preview generation failed",
                            preview_approved=False,
                            last_error="preview_failed",
                        )
                        continue
                    await self._repository.update_scene(
                        conn,
                        scene_id=scene.id,
                        preview_status="ready",
                        preview_storage_key=result.r2_key,
                        preview_qa_score=result.qa_score,
                        preview_qa_feedback=result.qa_feedback,
                        preview_approved=False,
                        last_error=None,
                    )
                scenes = await self._repository.list_scenes(conn, project.id)
                next_status = self._derive_project_status(
                    current_status="previewing_scenes",
                    scenes=scenes,
                    render_status=None,
                    render_is_stale=True,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status=next_status,
                    last_error=None,
                    revision=locked.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def regenerate_scene(
        self,
        *,
        project_id: UUID,
        scene_id: UUID,
        user_id: UUID,
        expected_revision: int,
    ) -> dict[str, Any]:
        if not self._generation_settings.preview_enabled or self._image_preview_service is None:
            raise VideoProjectInvalidStateError("Preview generation is not available")
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scene = await self._repository.get_scene(conn, project.id, scene_id)
                if scene is None:
                    raise VideoProjectSceneNotFoundError(scene_id)
                anchor_scene = None
                if project.anchor_scene_id is not None:
                    anchor_scene = await self._repository.get_scene(conn, project.id, project.anchor_scene_id)
                style_ref = anchor_scene.preview_storage_key if anchor_scene and anchor_scene.id != scene.id else None
                await self._repository.update_scene(
                    conn,
                    scene_id=scene.id,
                    preview_status="generating",
                    preview_approved=False,
                    last_error=None,
                )
            result = await self._image_preview_service.generate_preview(
                user_id,
                scene.prompt,
                aspect_ratio=project.aspect_ratio,
                style_ref_path=style_ref,
            )
            async with conn.transaction():
                locked = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                await self._repository.update_scene(
                    conn,
                    scene_id=scene.id,
                    preview_status="ready",
                    preview_storage_key=result.r2_key,
                    preview_qa_score=result.qa_score,
                    preview_qa_feedback=result.qa_feedback,
                    preview_approved=False,
                    last_error=None,
                )
                scenes = await self._repository.list_scenes(conn, project.id)
                next_status = self._derive_project_status(
                    current_status="draft",
                    scenes=scenes,
                    render_status=None,
                    render_is_stale=True,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status=next_status,
                    last_error=None,
                    revision=locked.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def verify_scene(
        self,
        *,
        project_id: UUID,
        scene_id: UUID,
        user_id: UUID,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Run structured verification on an existing scene preview."""
        if not self._generation_settings.preview_enabled or self._image_preview_service is None:
            raise VideoProjectInvalidStateError("Preview verification is not available")
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scene = await self._repository.get_scene(conn, project.id, scene_id)
                if scene is None:
                    raise VideoProjectSceneNotFoundError(scene_id)
                if scene.preview_status != "ready" or not scene.preview_storage_key:
                    raise VideoProjectInvalidStateError("Scene must have a ready preview before verification")
                # Resolve anchor for style comparison
                anchor_scene = None
                if project.anchor_scene_id is not None:
                    anchor_scene = await self._repository.get_scene(conn, project.id, project.anchor_scene_id)
                style_ref = anchor_scene.preview_storage_key if anchor_scene and anchor_scene.id != scene.id else None
                await self._repository.update_scene(
                    conn,
                    scene_id=scene.id,
                    preview_status="verifying",
                )
            try:
                result = await self._image_preview_service.verify_preview(
                    scene.prompt,
                    scene.preview_storage_key,
                    style_ref_path=style_ref,
                )
            except Exception:
                # Verification failed — reset to ready (image still exists)
                async with conn.transaction():
                    await self._repository.update_scene(
                        conn,
                        scene_id=scene.id,
                        preview_status="ready",
                    )
                raise
            async with conn.transaction():
                locked = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                await self._repository.update_scene(
                    conn,
                    scene_id=scene.id,
                    preview_status="ready",
                    preview_qa_score=result.overall_score,
                    preview_qa_feedback=result.feedback,
                    preview_scene_score=result.scene_score,
                    preview_style_score=result.style_score,
                    preview_improvement_suggestion=result.improvement_suggestion,
                )
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    revision=locked.revision + 1,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        return await self._serialize_snapshot(snapshot)

    async def render_project(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        tier: Tier,
        expected_revision: int,
    ) -> dict[str, Any]:
        return await self._submit_render(project_id=project_id, user_id=user_id, tier=tier, expected_revision=expected_revision)

    async def recompose_project(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        tier: Tier,
        expected_revision: int,
    ) -> dict[str, Any]:
        return await self._submit_render(project_id=project_id, user_id=user_id, tier=tier, expected_revision=expected_revision)

    async def _submit_render(  # noqa: C901
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        tier: Tier,
        expected_revision: int,
    ) -> dict[str, Any]:
        job_id: UUID | None = None
        async with self._repository._acquire_connection() as conn:
            async with conn.transaction():
                project = await self._lock_project_for_update(conn, project_id, user_id, expected_revision)
                scenes = await self._repository.list_scenes(conn, project.id)
                if not scenes:
                    raise VideoProjectInvalidStateError("Project must have scenes before rendering")
                if any(scene.preview_status != "ready" or not scene.preview_approved for scene in scenes):
                    raise VideoProjectInvalidStateError("All scenes must have approved previews before rendering")
                next_revision = project.revision + 1
                spec = self._build_composition_spec(project, scenes)
                result = await self._generation_service.submit_job(
                    user_id,
                    spec,
                    tier,
                    video_project_id=project.id,
                    project_revision=next_revision,
                    conn=conn,
                    dispatch=False,
                )
                job_id = result["job_id"]
                updated = await self._repository.update_project(
                    conn,
                    project_id=project.id,
                    status="rendering",
                    last_error=None,
                    revision=next_revision,
                )
                snapshot = await self._repository._load_snapshot(conn, updated)
        if job_id is not None:
            await self._generation_service.dispatch_job(job_id)
        return await self._serialize_snapshot(snapshot)

    async def _lock_project_for_update(
        self,
        conn: Any,
        project_id: UUID,
        user_id: UUID,
        expected_revision: int,
    ) -> VideoProjectRecord:
        project = await self._repository.lock_project(conn, project_id, user_id)
        if project is None:
            raise VideoProjectNotFoundError(project_id)
        if project.revision != expected_revision:
            raise VideoProjectRevisionConflictError(
                project_id=project.id,
                expected_revision=expected_revision,
                actual_revision=project.revision,
            )
        return project

    async def _serialize_snapshot(self, snapshot: VideoProjectSnapshot) -> dict[str, Any]:
        project = snapshot.project
        scenes = snapshot.scenes
        refs = snapshot.references
        job = snapshot.generation_job
        render_is_stale = bool(job and job.project_revision is not None and job.project_revision < project.revision)
        final_video_url = None
        final_video_expires_at = None
        if job and job.status == "completed" and job.r2_key and self._generation_storage is not None and not render_is_stale:
            final_video_url = await self._generation_storage.get_presigned_url(job.r2_key)
            final_video_expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=PRESIGNED_URL_EXPIRY)
            ).replace(microsecond=0).isoformat()
        scene_payloads = []
        for scene in scenes:
            image_url = None
            if scene.preview_storage_key and self._generation_storage is not None:
                image_url = await self._generation_storage.get_preview_url(scene.preview_storage_key)
            scene_payloads.append({
                "id": str(scene.id),
                "index": scene.position,
                "title": scene.title,
                "summary": scene.summary,
                "prompt": scene.prompt,
                "duration_seconds": scene.duration_seconds,
                "transition": scene.transition,
                "caption": scene.caption,
                "audio_direction": scene.audio_direction,
                "shot_type": scene.shot_type,
                "camera_movement": scene.camera_movement,
                "beat": scene.beat,
                "preview": {
                    "status": scene.preview_status,
                    "image_url": image_url,
                    "storage_key": scene.preview_storage_key,
                    "qa_score": scene.preview_qa_score,
                    "qa_feedback": scene.preview_qa_feedback,
                    "scene_score": scene.preview_scene_score,
                    "style_score": scene.preview_style_score,
                    "improvement_suggestion": scene.preview_improvement_suggestion,
                    "approved": scene.preview_approved,
                    "error": scene.last_error,
                },
            })
        anchor_index = next((scene.position for scene in scenes if scene.id == project.anchor_scene_id), None)
        anchor_scene = next((scene for scene in scenes if scene.id == project.anchor_scene_id), None)
        anchor_image_url = None
        if anchor_scene and anchor_scene.preview_storage_key and self._generation_storage is not None:
            anchor_image_url = await self._generation_storage.get_preview_url(anchor_scene.preview_storage_key)
        return {
            "id": str(project.id),
            "conversation_id": str(project.conversation_id),
            "title": project.title,
            "status": project.status,
            "revision": project.revision,
            "source_analysis_ids": [str(value) for value in project.source_analysis_ids],
            "anchor_scene_id": str(project.anchor_scene_id) if project.anchor_scene_id else None,
            "references": [
                {
                    "id": str(reference.id),
                    "analysis_id": str(reference.analysis_id) if reference.analysis_id else None,
                    "source_video_id": reference.source_video_id,
                    "platform": reference.platform,
                    "title": reference.title,
                    "thumbnail_url": reference.thumbnail_url,
                    "creator_handle": reference.creator_handle,
                }
                for reference in refs
            ],
            "style_brief_summary": project.style_brief_summary,
            "aspect_ratio": project.aspect_ratio,
            "resolution": project.resolution,
            "protagonist_description": project.protagonist_description,
            "target_emotion_arc": project.target_emotion_arc,
            "anchor_scene_index": anchor_index,
            "anchor_preview_image_url": anchor_image_url,
            "anchor_preview_storage_key": anchor_scene.preview_storage_key if anchor_scene else None,
            "render_job_id": str(job.id) if job else None,
            "render_job_status": job.status if job else None,
            "render_is_stale": render_is_stale,
            "render_project_revision": job.project_revision if job else None,
            "final_video_url": final_video_url,
            "final_video_url_expires_at": final_video_expires_at,
            "last_error": project.last_error,
            "scenes": scene_payloads,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

    def _build_composition_spec(
        self,
        project: VideoProjectRecord,
        scenes: Iterable[Any],
    ) -> CompositionSpec:
        from ..generation.prompt_utils import BEAT_COMPOSITION, CAMERA_TO_COMPOSITION

        ordered = sorted(scenes, key=lambda scene: scene.position)
        cadres = []
        for scene in ordered:
            # Build prompt parts in priority order (most important first survives truncation)
            parts: list[str] = []
            if project.protagonist_description:
                parts.append(f"[PROTAGONIST: {project.protagonist_description}]")
            if scene.title:
                parts.append(f"[SCENE: {scene.title}]")
            elif scene.summary:
                parts.append(f"[SCENE: {scene.summary}]")
            parts.append(scene.prompt)  # core content
            if hasattr(scene, "beat") and scene.beat and scene.beat in BEAT_COMPOSITION:
                parts.append(BEAT_COMPOSITION[scene.beat])
            if scene.shot_type and scene.shot_type != "medium":
                parts.append(f"Shot type: {scene.shot_type}.")
            if scene.camera_movement and scene.camera_movement != "static":
                comp = CAMERA_TO_COMPOSITION.get(scene.camera_movement, "")
                if comp:
                    parts.append(comp)
            if scene.audio_direction:
                parts.append(f"Audio: {scene.audio_direction}")
            enriched_prompt = sanitize_prompt(" ".join(p for p in parts if p), 2000)
            cadres.append({
                "index": scene.position,
                "prompt": enriched_prompt,
                "duration_seconds": scene.duration_seconds,
                "transition": scene.transition,
                "seed_image_storage_key": (
                    scene.preview_storage_key
                    if scene.preview_status == "ready" and scene.preview_approved
                    else None
                ),
            })
        # Captions disabled — dialogue shown in PDF report only, not burned onto video
        return CompositionSpec(
            cadres=cadres,
            captions=[],
            source_analysis_ids=project.source_analysis_ids,
            aspect_ratio=project.aspect_ratio,
            resolution=project.resolution,
        )

    def _derive_project_status(
        self,
        *,
        current_status: str,
        scenes: list[Any],
        render_status: str | None,
        render_is_stale: bool,
    ) -> str:
        if render_status in {"pending", "generating", "composing", "cancelling"}:
            return "rendering"
        if render_status == "completed" and not render_is_stale:
            return "render_complete"
        if render_status in {"partial", "failed", "cancelled"}:
            return "failed"
        if not scenes:
            return "draft"
        if any(scene.preview_status == "generating" for scene in scenes):
            return "previewing_scenes"
        if all(scene.preview_status == "ready" and scene.preview_approved for scene in scenes):
            return "ready_to_render"
        return current_status if current_status in {"previewing_anchor", "previewing_scenes"} else "draft"

    def _validate_caption(self, caption: str) -> str:
        import unicodedata
        caption = unicodedata.normalize("NFKC", caption)
        if len(caption) > 200:
            raise VideoProjectInvalidStateError("Caption must be 200 characters or fewer")
        if caption and not _CAPTION_SAFE.match(caption):
            raise VideoProjectInvalidStateError("Caption contains unsupported characters")
        return caption

    async def _build_analysis_references(
        self,
        analysis_ids: list[UUID],
    ) -> list[VideoProjectReferenceInput]:
        references: list[VideoProjectReferenceInput] = []
        if self._analysis_repository is None:
            return references
        for analysis_id in analysis_ids:
            record = await self._analysis_repository.get_by_id(analysis_id)
            title = record.title if record and record.title else f"Analysis {analysis_id}"
            references.append(VideoProjectReferenceInput(
                analysis_id=analysis_id,
                source_video_id=None,
                platform=None,
                title=title,
                thumbnail_url=None,
                creator_handle=None,
            ))
        return references

    def _build_style_summary(self, style: str, analysis_ids: list[UUID]) -> str:
        count = len(analysis_ids)
        return f"Derived from {count} analyzed reference video(s). Requested style: {style.strip()}."

    async def _load_creative_patterns(self, analysis_ids: list[UUID]) -> list[Any]:
        if self._creative_service is None:
            return []
        patterns: list[Any] = []
        for analysis_id in analysis_ids:
            pattern = await self._creative_service.get_creative_patterns(analysis_id)
            if pattern is not None and pattern.error is None:
                patterns.append(pattern)
        return patterns
