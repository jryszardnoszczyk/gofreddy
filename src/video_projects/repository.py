"""Persistence for video projects."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from uuid import UUID

import asyncpg

from .models import (
    VideoProjectGenerationJob,
    VideoProjectRecord,
    VideoProjectReferenceInput,
    VideoProjectReferenceRecord,
    VideoProjectSceneInput,
    VideoProjectSceneRecord,
    VideoProjectSnapshot,
)

UNSET = object()


class PostgresVideoProjectRepository:
    ACQUIRE_TIMEOUT = 5.0

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def _acquire_connection(self) -> AsyncIterator[Any]:
        try:
            async with asyncio.timeout(self.ACQUIRE_TIMEOUT):
                conn = await self._pool.acquire()
        except asyncio.TimeoutError as exc:
            raise RuntimeError("Video project database connection pool exhausted") from exc
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def list_projects(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[VideoProjectRecord]:
        async with self._acquire_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT vp.*
                FROM video_projects vp
                JOIN conversations c ON c.id = vp.conversation_id
                WHERE vp.conversation_id = $1
                  AND c.user_id = $2
                ORDER BY vp.updated_at DESC, vp.created_at DESC
                """,
                conversation_id,
                user_id,
            )
        return [VideoProjectRecord.from_row(row) for row in rows]

    async def lock_project(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
        user_id: UUID,
    ) -> VideoProjectRecord | None:
        row = await conn.fetchrow(
            """
            SELECT vp.*
            FROM video_projects vp
            JOIN conversations c ON c.id = vp.conversation_id
            WHERE vp.id = $1
              AND c.user_id = $2
            FOR UPDATE
            """,
            project_id,
            user_id,
        )
        return VideoProjectRecord.from_row(row) if row else None

    async def get_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> VideoProjectSnapshot | None:
        async with self._acquire_connection() as conn:
            project_row = await conn.fetchrow(
                """
                SELECT vp.*
                FROM video_projects vp
                JOIN conversations c ON c.id = vp.conversation_id
                WHERE vp.id = $1
                  AND c.user_id = $2
                """,
                project_id,
                user_id,
            )
            if not project_row:
                return None
            return await self._load_snapshot(conn, VideoProjectRecord.from_row(project_row))

    async def get_latest_project_for_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> VideoProjectSnapshot | None:
        async with self._acquire_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT vp.*
                FROM video_projects vp
                JOIN conversations c ON c.id = vp.conversation_id
                WHERE vp.conversation_id = $1
                  AND c.user_id = $2
                  AND vp.status != 'archived'
                ORDER BY vp.updated_at DESC, vp.created_at DESC
                LIMIT 1
                """,
                conversation_id,
                user_id,
            )
            if not row:
                return None
            return await self._load_snapshot(conn, VideoProjectRecord.from_row(row))

    async def create_project(
        self,
        conn: asyncpg.Connection,
        *,
        conversation_id: UUID,
        title: str,
        status: str,
        style_brief_summary: str,
        source_analysis_ids: list[UUID],
        aspect_ratio: str,
        resolution: str,
        protagonist_description: str = "",
        target_emotion_arc: str = "",
    ) -> VideoProjectRecord:
        row = await conn.fetchrow(
            """
            INSERT INTO video_projects (
                conversation_id,
                title,
                status,
                style_brief_summary,
                source_analysis_ids,
                aspect_ratio,
                resolution,
                protagonist_description,
                target_emotion_arc
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            conversation_id,
            title,
            status,
            style_brief_summary,
            source_analysis_ids,
            aspect_ratio,
            resolution,
            protagonist_description,
            target_emotion_arc,
        )
        return VideoProjectRecord.from_row(row)

    async def insert_scene(
        self,
        conn: asyncpg.Connection,
        *,
        project_id: UUID,
        position: int,
        scene: VideoProjectSceneInput,
    ) -> VideoProjectSceneRecord:
        row = await conn.fetchrow(
            """
            INSERT INTO video_project_scenes (
                project_id,
                position,
                title,
                summary,
                prompt,
                duration_seconds,
                transition,
                caption,
                audio_direction,
                shot_type,
                camera_movement,
                beat
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            """,
            project_id,
            position,
            scene.title,
            scene.summary,
            scene.prompt,
            scene.duration_seconds,
            scene.transition,
            scene.caption,
            scene.audio_direction,
            scene.shot_type,
            scene.camera_movement,
            scene.beat,
        )
        return VideoProjectSceneRecord.from_row(row)

    async def add_references(
        self,
        conn: asyncpg.Connection,
        *,
        project_id: UUID,
        references: list[VideoProjectReferenceInput],
    ) -> None:
        for reference in references:
            await conn.execute(
                """
                INSERT INTO video_project_references (
                    project_id,
                    analysis_id,
                    source_video_id,
                    platform,
                    title,
                    thumbnail_url,
                    creator_handle
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                """,
                project_id,
                reference.analysis_id,
                reference.source_video_id,
                reference.platform,
                reference.title,
                reference.thumbnail_url,
                reference.creator_handle,
            )

    async def list_scenes(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
    ) -> list[VideoProjectSceneRecord]:
        rows = await conn.fetch(
            """
            SELECT *
            FROM video_project_scenes
            WHERE project_id = $1
            ORDER BY position ASC, created_at ASC
            """,
            project_id,
        )
        return [VideoProjectSceneRecord.from_row(row) for row in rows]

    async def list_references(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
    ) -> list[VideoProjectReferenceRecord]:
        rows = await conn.fetch(
            """
            SELECT *
            FROM video_project_references
            WHERE project_id = $1
            ORDER BY created_at ASC
            """,
            project_id,
        )
        return [VideoProjectReferenceRecord.from_row(row) for row in rows]

    async def get_scene(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
        scene_id: UUID,
    ) -> VideoProjectSceneRecord | None:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM video_project_scenes
            WHERE project_id = $1
              AND id = $2
            """,
            project_id,
            scene_id,
        )
        return VideoProjectSceneRecord.from_row(row) if row else None

    async def get_scene_by_position(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
        position: int,
    ) -> VideoProjectSceneRecord | None:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM video_project_scenes
            WHERE project_id = $1
              AND position = $2
            """,
            project_id,
            position,
        )
        return VideoProjectSceneRecord.from_row(row) if row else None

    async def update_project(
        self,
        conn: asyncpg.Connection,
        *,
        project_id: UUID,
        title: str | object = UNSET,
        status: str | object = UNSET,
        revision: int | object = UNSET,
        style_brief_summary: str | object = UNSET,
        source_analysis_ids: list[UUID] | object = UNSET,
        aspect_ratio: str | object = UNSET,
        resolution: str | object = UNSET,
        anchor_scene_id: UUID | None | object = UNSET,
        last_error: str | None | object = UNSET,
        protagonist_description: str | object = UNSET,
        target_emotion_arc: str | object = UNSET,
    ) -> VideoProjectRecord:
        assignments: list[str] = []
        values: list[Any] = [project_id]
        self._append_assignment(assignments, values, "title", title)
        self._append_assignment(assignments, values, "status", status)
        self._append_assignment(assignments, values, "revision", revision)
        self._append_assignment(assignments, values, "style_brief_summary", style_brief_summary)
        self._append_assignment(assignments, values, "source_analysis_ids", source_analysis_ids)
        self._append_assignment(assignments, values, "aspect_ratio", aspect_ratio)
        self._append_assignment(assignments, values, "resolution", resolution)
        self._append_assignment(assignments, values, "anchor_scene_id", anchor_scene_id)
        self._append_assignment(assignments, values, "last_error", last_error)
        self._append_assignment(assignments, values, "protagonist_description", protagonist_description)
        self._append_assignment(assignments, values, "target_emotion_arc", target_emotion_arc)

        if not assignments:
            row = await conn.fetchrow("SELECT * FROM video_projects WHERE id = $1", project_id)
            return VideoProjectRecord.from_row(row)

        assignments.append("updated_at = NOW()")
        row = await conn.fetchrow(
            f"""
            UPDATE video_projects
            SET {", ".join(assignments)}
            WHERE id = $1
            RETURNING *
            """,
            *values,
        )
        return VideoProjectRecord.from_row(row)

    async def update_scene(
        self,
        conn: asyncpg.Connection,
        *,
        scene_id: UUID,
        title: str | object = UNSET,
        summary: str | object = UNSET,
        prompt: str | object = UNSET,
        duration_seconds: int | object = UNSET,
        transition: str | object = UNSET,
        caption: str | object = UNSET,
        audio_direction: str | object = UNSET,
        shot_type: str | object = UNSET,
        camera_movement: str | object = UNSET,
        beat: str | object = UNSET,
        preview_status: str | object = UNSET,
        preview_storage_key: str | None | object = UNSET,
        preview_qa_score: int | None | object = UNSET,
        preview_qa_feedback: str | None | object = UNSET,
        preview_approved: bool | object = UNSET,
        preview_scene_score: int | None | object = UNSET,
        preview_style_score: int | None | object = UNSET,
        preview_improvement_suggestion: str | None | object = UNSET,
        last_error: str | None | object = UNSET,
        position: int | object = UNSET,
    ) -> VideoProjectSceneRecord:
        assignments: list[str] = []
        values: list[Any] = [scene_id]
        self._append_assignment(assignments, values, "position", position)
        self._append_assignment(assignments, values, "title", title)
        self._append_assignment(assignments, values, "summary", summary)
        self._append_assignment(assignments, values, "prompt", prompt)
        self._append_assignment(assignments, values, "duration_seconds", duration_seconds)
        self._append_assignment(assignments, values, "transition", transition)
        self._append_assignment(assignments, values, "caption", caption)
        self._append_assignment(assignments, values, "audio_direction", audio_direction)
        self._append_assignment(assignments, values, "shot_type", shot_type)
        self._append_assignment(assignments, values, "camera_movement", camera_movement)
        self._append_assignment(assignments, values, "beat", beat)
        self._append_assignment(assignments, values, "preview_status", preview_status)
        self._append_assignment(assignments, values, "preview_storage_key", preview_storage_key)
        self._append_assignment(assignments, values, "preview_qa_score", preview_qa_score)
        self._append_assignment(assignments, values, "preview_qa_feedback", preview_qa_feedback)
        self._append_assignment(assignments, values, "preview_approved", preview_approved)
        self._append_assignment(assignments, values, "preview_scene_score", preview_scene_score)
        self._append_assignment(assignments, values, "preview_style_score", preview_style_score)
        self._append_assignment(assignments, values, "preview_improvement_suggestion", preview_improvement_suggestion)
        self._append_assignment(assignments, values, "last_error", last_error)

        if not assignments:
            row = await conn.fetchrow("SELECT * FROM video_project_scenes WHERE id = $1", scene_id)
            return VideoProjectSceneRecord.from_row(row)

        assignments.append("updated_at = NOW()")
        row = await conn.fetchrow(
            f"""
            UPDATE video_project_scenes
            SET {", ".join(assignments)}
            WHERE id = $1
            RETURNING *
            """,
            *values,
        )
        return VideoProjectSceneRecord.from_row(row)

    async def delete_scene(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
        scene_id: UUID,
    ) -> VideoProjectSceneRecord | None:
        row = await conn.fetchrow(
            """
            DELETE FROM video_project_scenes
            WHERE project_id = $1
              AND id = $2
            RETURNING *
            """,
            project_id,
            scene_id,
        )
        return VideoProjectSceneRecord.from_row(row) if row else None

    async def recompact_positions(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
    ) -> None:
        await conn.execute(
            """
            UPDATE video_project_scenes AS s
            SET position = sub.new_pos
            FROM (
                SELECT id, ROW_NUMBER() OVER (ORDER BY position) - 1 AS new_pos
                FROM video_project_scenes
                WHERE project_id = $1
            ) sub
            WHERE s.id = sub.id AND s.position != sub.new_pos
            """,
            project_id,
        )

    async def count_scenes(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
    ) -> int:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM video_project_scenes WHERE project_id = $1",
            project_id,
        )
        return int(result)

    async def latest_generation_job(
        self,
        conn: asyncpg.Connection,
        project_id: UUID,
    ) -> VideoProjectGenerationJob | None:
        row = await conn.fetchrow(
            """
            SELECT id, status, project_revision, r2_key, error, created_at, updated_at
            FROM generation_jobs
            WHERE video_project_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            project_id,
        )
        return VideoProjectGenerationJob.from_row(row) if row else None

    async def _load_snapshot(
        self,
        conn: asyncpg.Connection,
        project: VideoProjectRecord,
    ) -> VideoProjectSnapshot:
        scenes = await self.list_scenes(conn, project.id)
        references = await self.list_references(conn, project.id)
        job = await self.latest_generation_job(conn, project.id)
        return VideoProjectSnapshot(project=project, scenes=scenes, references=references, generation_job=job)

    @staticmethod
    def _append_assignment(
        assignments: list[str],
        values: list[Any],
        column: str,
        value: Any,
    ) -> None:
        if value is UNSET:
            return
        values.append(value)
        assignments.append(f"{column} = ${len(values)}")
