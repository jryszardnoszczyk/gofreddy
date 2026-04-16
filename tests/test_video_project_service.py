"""Tests for VideoProjectService: get_transcript, delete_scene, clean_transcript."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.video_projects.exceptions import (
    VideoProjectInvalidStateError,
    VideoProjectNotFoundError,
)
from src.video_projects.models import (
    VideoProjectRecord,
    VideoProjectSceneRecord,
    VideoProjectSnapshot,
)
from src.video_projects.service import VideoProjectService


def _make_service(repo: AsyncMock) -> VideoProjectService:
    return VideoProjectService(
        repository=repo,
        generation_service=MagicMock(),
        generation_storage=None,
        generation_settings=MagicMock(),
        idea_service=None,
    )


def _make_project(
    *,
    project_id=None,
    anchor_scene_id=None,
    revision=1,
) -> VideoProjectRecord:
    return VideoProjectRecord(
        id=project_id or uuid4(),
        conversation_id=uuid4(),
        title="Test Project",
        status="draft",
        revision=revision,
        source_analysis_ids=[],
        style_brief_summary="",
        aspect_ratio="16:9",
        resolution="1080p",
        anchor_scene_id=anchor_scene_id,
        last_error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_scene(
    *,
    scene_id=None,
    project_id=None,
    position=0,
    duration_seconds=5,
    caption="Hello world",
    title="Scene",
) -> VideoProjectSceneRecord:
    return VideoProjectSceneRecord(
        id=scene_id or uuid4(),
        project_id=project_id or uuid4(),
        position=position,
        title=title,
        summary="summary",
        prompt="prompt",
        duration_seconds=duration_seconds,
        transition="fade",
        caption=caption,
        preview_status="pending",
        preview_storage_key=None,
        preview_qa_score=None,
        preview_qa_feedback=None,
        preview_scene_score=None,
        preview_style_score=None,
        preview_improvement_suggestion=None,
        preview_approved=False,
        last_error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── get_transcript ──────────────────────────────────────────────────


class TestGetTranscript:
    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = AsyncMock()
        repo.get_project = AsyncMock(return_value=None)
        svc = _make_service(repo)
        with pytest.raises(VideoProjectNotFoundError):
            await svc.get_transcript(project_id=uuid4(), user_id=uuid4())

    @pytest.mark.asyncio
    async def test_cumulative_timing(self):
        pid = uuid4()
        scenes = [
            _make_scene(project_id=pid, position=0, duration_seconds=5, caption="A"),
            _make_scene(project_id=pid, position=1, duration_seconds=3, caption="B"),
            _make_scene(project_id=pid, position=2, duration_seconds=7, caption="C"),
        ]
        project = _make_project(project_id=pid)
        snapshot = VideoProjectSnapshot(project=project, scenes=scenes, references=[])

        repo = AsyncMock()
        repo.get_project = AsyncMock(return_value=snapshot)
        svc = _make_service(repo)

        result = await svc.get_transcript(project_id=pid, user_id=uuid4())

        assert result["scene_count"] == 3
        assert result["total_duration_seconds"] == 15

        t = result["transcript"]
        # Scene 0: 0-5
        assert t[0]["start_seconds"] == 0
        assert t[0]["end_seconds"] == 5
        # Scene 1: 5-8
        assert t[1]["start_seconds"] == 5
        assert t[1]["end_seconds"] == 8
        # Scene 2: 8-15
        assert t[2]["start_seconds"] == 8
        assert t[2]["end_seconds"] == 15


# ── delete_scene ────────────────────────────────────────────────────


class TestDeleteScene:
    @pytest.mark.asyncio
    async def test_not_found(self):
        repo = AsyncMock()
        # _lock_project_for_update calls repo.lock_project — return None to trigger not-found
        repo.lock_project = AsyncMock(return_value=None)
        # _acquire_connection must yield a mock connection with transaction support
        conn = AsyncMock()
        conn.transaction = MagicMock(return_value=AsyncMock())
        repo._acquire_connection = MagicMock(return_value=_AsyncCtx(conn))
        svc = _make_service(repo)

        with pytest.raises(VideoProjectNotFoundError):
            await svc.delete_scene(
                project_id=uuid4(),
                scene_id=uuid4(),
                user_id=uuid4(),
                expected_revision=1,
            )

    @pytest.mark.asyncio
    async def test_last_scene_rejected(self):
        pid = uuid4()
        project = _make_project(project_id=pid, revision=1)

        repo = AsyncMock()
        repo.lock_project = AsyncMock(return_value=project)
        repo.count_scenes = AsyncMock(return_value=1)
        conn = AsyncMock()
        conn.transaction = MagicMock(return_value=AsyncMock())
        repo._acquire_connection = MagicMock(return_value=_AsyncCtx(conn))
        svc = _make_service(repo)

        with pytest.raises(VideoProjectInvalidStateError):
            await svc.delete_scene(
                project_id=pid,
                scene_id=uuid4(),
                user_id=uuid4(),
                expected_revision=1,
            )

    @pytest.mark.asyncio
    async def test_anchor_reassigned(self):
        pid = uuid4()
        anchor_id = uuid4()
        new_first_id = uuid4()
        project = _make_project(project_id=pid, anchor_scene_id=anchor_id, revision=1)
        new_first_scene = _make_scene(scene_id=new_first_id, project_id=pid, position=0)
        updated_project = _make_project(project_id=pid, anchor_scene_id=new_first_id, revision=2)
        snapshot = VideoProjectSnapshot(project=updated_project, scenes=[new_first_scene], references=[])

        repo = AsyncMock()
        repo.lock_project = AsyncMock(return_value=project)
        repo.count_scenes = AsyncMock(return_value=3)
        repo.delete_scene = AsyncMock(return_value=True)
        repo.recompact_positions = AsyncMock()
        repo.get_scene_by_position = AsyncMock(return_value=new_first_scene)
        repo.update_project = AsyncMock(return_value=updated_project)
        repo._load_snapshot = AsyncMock(return_value=snapshot)
        conn = AsyncMock()
        conn.transaction = MagicMock(return_value=AsyncMock())
        repo._acquire_connection = MagicMock(return_value=_AsyncCtx(conn))
        svc = _make_service(repo)
        # Mock _serialize_snapshot to avoid complex serialization
        svc._serialize_snapshot = AsyncMock(return_value={"anchor_scene_id": str(new_first_id)})

        result = await svc.delete_scene(
            project_id=pid,
            scene_id=anchor_id,
            user_id=uuid4(),
            expected_revision=1,
        )

        # Verify update_project was called with the new anchor
        repo.update_project.assert_called_once()
        call_kwargs = repo.update_project.call_args
        assert call_kwargs.kwargs.get("anchor_scene_id") == new_first_id


# ── clean_transcript ────────────────────────────────────────────────


class TestCleanTranscript:
    @pytest.mark.asyncio
    async def test_removes_fillers(self):
        pid = uuid4()
        scene_id = uuid4()
        project = _make_project(project_id=pid, revision=1)
        scene = _make_scene(
            scene_id=scene_id,
            project_id=pid,
            caption="Um, like, the product is great",
        )
        updated_project = _make_project(project_id=pid, revision=2)
        snapshot = VideoProjectSnapshot(project=updated_project, scenes=[scene], references=[])

        repo = AsyncMock()
        repo.lock_project = AsyncMock(return_value=project)
        repo.list_scenes = AsyncMock(return_value=[scene])
        repo.update_scene = AsyncMock()
        repo.update_project = AsyncMock(return_value=updated_project)
        repo._load_snapshot = AsyncMock(return_value=snapshot)
        conn = AsyncMock()
        conn.transaction = MagicMock(return_value=AsyncMock())
        repo._acquire_connection = MagicMock(return_value=_AsyncCtx(conn))
        svc = _make_service(repo)
        svc._serialize_snapshot = AsyncMock(return_value={"status": "draft"})

        result = await svc.clean_transcript(
            project_id=pid,
            user_id=uuid4(),
            expected_revision=1,
        )

        # Filler removal info is appended to result
        assert result["filler_removal"]["scenes_cleaned"] == 1
        change = result["filler_removal"]["changes"][0]
        assert "Um" in change["before"] or "um" in change["before"].lower()
        assert "um" not in change["after"].lower()
        assert "like" not in change["after"].lower()

    @pytest.mark.asyncio
    async def test_skips_empty_captions(self):
        pid = uuid4()
        project = _make_project(project_id=pid, revision=1)
        scenes = [
            _make_scene(project_id=pid, position=0, caption=None),
            _make_scene(project_id=pid, position=1, caption=""),
            _make_scene(project_id=pid, position=2, caption="Good content here"),
        ]
        updated_project = _make_project(project_id=pid, revision=2)
        snapshot = VideoProjectSnapshot(project=updated_project, scenes=scenes, references=[])

        repo = AsyncMock()
        repo.lock_project = AsyncMock(return_value=project)
        repo.list_scenes = AsyncMock(return_value=scenes)
        repo.update_scene = AsyncMock()
        repo.update_project = AsyncMock(return_value=updated_project)
        repo._load_snapshot = AsyncMock(return_value=snapshot)
        conn = AsyncMock()
        conn.transaction = MagicMock(return_value=AsyncMock())
        repo._acquire_connection = MagicMock(return_value=_AsyncCtx(conn))
        svc = _make_service(repo)
        svc._serialize_snapshot = AsyncMock(return_value={"status": "draft"})

        result = await svc.clean_transcript(
            project_id=pid,
            user_id=uuid4(),
            expected_revision=1,
        )

        # None and empty captions are skipped; "Good content here" has no fillers
        assert result["filler_removal"]["scenes_cleaned"] == 0
        assert result["filler_removal"]["changes"] == []


# ── Helpers ─────────────────────────────────────────────────────────


class _AsyncCtx:
    """Minimal async context manager wrapping a value."""

    def __init__(self, value: object) -> None:
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *args):
        pass
