from __future__ import annotations

from uuid import uuid4

import pytest

from src.api.fake_externals import _BoundFakeOrchestrator


def _fake_orchestrator() -> _BoundFakeOrchestrator:
    return _BoundFakeOrchestrator(
        conversation_id=uuid4(),
        analysis_repository=None,
        workspace_service=None,
        video_project_service=object(),
        tier=None,
    )


@pytest.mark.asyncio
async def test_plan_prefers_approve_over_preview_keyword() -> None:
    orchestrator = _fake_orchestrator()

    plan = await orchestrator._plan("Approve all previews", uuid4())

    assert plan == ("edit_cadre", {"mode": "approve_all"})


@pytest.mark.asyncio
async def test_plan_prefers_recompose_over_generate_keyword() -> None:
    orchestrator = _fake_orchestrator()

    plan = await orchestrator._plan("Recompose the video", uuid4())

    assert plan == ("generate_video_from_inspiration", {"mode": "recompose"})
