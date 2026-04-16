"""Tests for SessionService business logic.

Repository is mocked — we test ownership enforcement, dedup, status transitions,
and action logging orchestration.
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from src.sessions.exceptions import SessionAlreadyCompleted, SessionNotFound
from src.sessions.models import ActionRecord, Session
from src.sessions.service import SessionService


def _make_session(org_id=None, status="running", **kwargs):
    return Session(
        id=kwargs.get("id", uuid4()),
        org_id=org_id or uuid4(),
        client_name=kwargs.get("client_name", "test-client"),
        source="cli",
        session_type="ad_hoc",
        purpose=kwargs.get("purpose"),
        status=status,
        started_at=datetime.now(UTC),
        completed_at=None,
        updated_at=datetime.now(UTC),
        summary=kwargs.get("summary"),
        action_count=kwargs.get("action_count", 0),
        total_credits=kwargs.get("total_credits", 0),
        transcript=None,
        metadata={},
    )


def _make_action(session_id=None, **kwargs):
    return ActionRecord(
        id=uuid4(),
        session_id=session_id or uuid4(),
        tool_name=kwargs.get("tool_name", "creator.search"),
        input_summary=kwargs.get("input_summary"),
        output_summary=kwargs.get("output_summary"),
        duration_ms=kwargs.get("duration_ms", 150),
        cost_credits=kwargs.get("cost_credits", 0),
        status="success",
        error_code=None,
        created_at=datetime.now(UTC),
    )


class TestSessionService:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return SessionService(repository=mock_repo)

    # ── Create / Dedup ──────────────────────────────────────────────────

    async def test_create_new_session(self, service, mock_repo):
        org_id = uuid4()
        mock_repo.get_running_for_org.return_value = None
        new_session = _make_session(org_id)
        mock_repo.create.return_value = new_session

        result = await service.create_or_return_existing(org_id, "acme")
        assert result.id == new_session.id
        mock_repo.create.assert_called_once()

    async def test_create_returns_existing_running_session(self, service, mock_repo):
        """Dedup: returns existing running session for same org+client."""
        org_id = uuid4()
        existing = _make_session(org_id, client_name="acme")
        mock_repo.get_running_for_org.return_value = existing

        result = await service.create_or_return_existing(org_id, "acme")
        assert result.id == existing.id
        mock_repo.create.assert_not_called()

    # ── Get (ownership) ─────────────────────────────────────────────────

    async def test_get_session_enforces_ownership(self, service, mock_repo):
        org_a = uuid4()
        org_b = uuid4()
        session = _make_session(org_a)
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionNotFound):
            await service.get_session(session.id, org_b)

    async def test_get_session_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SessionNotFound):
            await service.get_session(uuid4(), uuid4())

    async def test_get_session_success(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id)
        mock_repo.get_by_id.return_value = session

        result = await service.get_session(session.id, org_id)
        assert result.id == session.id

    # ── Complete ─────────────────────────────────────────────────────────

    async def test_complete_session(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id)
        completed = _make_session(org_id, status="completed", summary="Done")
        mock_repo.get_by_id.return_value = session
        mock_repo.complete.return_value = completed

        result = await service.complete_session(session.id, org_id, summary="Done")
        assert result.status == "completed"

    async def test_complete_already_completed_raises(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id, status="completed")
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionAlreadyCompleted):
            await service.complete_session(session.id, org_id)

    async def test_complete_wrong_owner_raises(self, service, mock_repo):
        org_a = uuid4()
        org_b = uuid4()
        session = _make_session(org_a)
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionNotFound):
            await service.complete_session(session.id, org_b)

    # ── Log Action ───────────────────────────────────────────────────────

    async def test_log_action_success(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id)
        action = _make_action(session.id)
        mock_repo.get_by_id.return_value = session
        mock_repo.log_action.return_value = action

        result = await service.log_action(
            session.id, org_id, "creator.search",
            input_summary={"query": "fitness"},
        )
        assert result.tool_name == "creator.search"

    async def test_log_action_to_completed_session_raises(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id, status="completed")
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionAlreadyCompleted):
            await service.log_action(session.id, org_id, "creator.search")

    async def test_log_action_wrong_owner_raises(self, service, mock_repo):
        org_a = uuid4()
        org_b = uuid4()
        session = _make_session(org_a)
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionNotFound):
            await service.log_action(session.id, org_b, "creator.search")

    # ── Get Actions ──────────────────────────────────────────────────────

    async def test_get_actions_enforces_ownership(self, service, mock_repo):
        org_a = uuid4()
        org_b = uuid4()
        session = _make_session(org_a)
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionNotFound):
            await service.get_actions(session.id, org_b)

    async def test_get_actions_success(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id)
        actions = [_make_action(session.id) for _ in range(3)]
        mock_repo.get_by_id.return_value = session
        mock_repo.get_actions.return_value = actions

        result = await service.get_actions(session.id, org_id)
        assert len(result) == 3

    # ── Transcript ───────────────────────────────────────────────────────

    async def test_set_transcript_enforces_ownership(self, service, mock_repo):
        org_a = uuid4()
        org_b = uuid4()
        session = _make_session(org_a)
        mock_repo.get_by_id.return_value = session

        with pytest.raises(SessionNotFound):
            await service.set_transcript(session.id, org_b, "transcript data")

    async def test_set_transcript_success(self, service, mock_repo):
        org_id = uuid4()
        session = _make_session(org_id)
        mock_repo.get_by_id.return_value = session
        mock_repo.set_transcript.return_value = True

        result = await service.set_transcript(session.id, org_id, "transcript data")
        assert result is True

    # ── List ─────────────────────────────────────────────────────────────

    async def test_list_sessions(self, service, mock_repo):
        org_id = uuid4()
        sessions = [_make_session(org_id) for _ in range(5)]
        mock_repo.list_sessions.return_value = sessions

        result = await service.list_sessions(org_id)
        assert len(result) == 5
        mock_repo.list_sessions.assert_called_once_with(
            org_id, None, None, 50, 0
        )
