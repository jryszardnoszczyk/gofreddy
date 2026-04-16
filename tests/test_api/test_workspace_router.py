import pytest
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_principal, get_current_user_id, AuthPrincipal
from src.api.main import create_app
from src.api.rate_limit import limiter
from src.conversations.exceptions import ConversationNotFoundError
from src.conversations.models import Conversation
from src.workspace.exceptions import CollectionNotFoundError
from src.workspace.models import CollectionSummary, WorkspaceCollection, WorkspaceToolResult


@pytest.fixture
def test_user_id():
    return uuid4()


@pytest.fixture
def mock_conv_service():
    return AsyncMock()


@pytest.fixture
def mock_ws_service():
    return AsyncMock()


@pytest.fixture
def app(mock_conv_service, mock_ws_service, test_user_id):
    app = create_app()
    app.state.conversation_service = mock_conv_service
    app.state.workspace_service = mock_ws_service

    async def override_user_id():
        return test_user_id

    async def override_auth():
        return AuthPrincipal(user_id=test_user_id, credential_type="jwt", claims=None)

    app.dependency_overrides[get_current_user_id] = override_user_id
    app.dependency_overrides[get_auth_principal] = override_auth
    limiter.enabled = False
    yield app
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _make_conversation(user_id, **kwargs):
    return Conversation(
        id=kwargs.get("id", uuid4()),
        user_id=user_id,
        title="Test",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )


def _make_collection(**kwargs):
    return WorkspaceCollection(
        id=kwargs.get("id", uuid4()),
        conversation_id=kwargs.get("conversation_id", uuid4()),
        name=kwargs.get("name", "Results"),
        item_count=10,
        active_filters={},
        summary_stats={},
        payload_ref=None,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_summary():
    return CollectionSummary(
        total_count=10,
        view_distribution={"<10k": 5, "10k-100k": 3, "100k-500k": 1, ">500k": 0, "unknown": 1},
        engagement_percentiles={"p25": 0.02, "median": 0.05, "p75": 0.1},
        top_creators=[{"handle": "alice", "count": 5}],
        platform_breakdown={"tiktok": 7, "instagram": 3},
        date_range=None,
    )


class TestWorkspaceRouter:

    def test_get_collections_validates_ownership(self, client, mock_conv_service, test_user_id):
        conv_id = uuid4()
        mock_conv_service.get_conversation.side_effect = ConversationNotFoundError(conv_id)
        resp = client.get(f"/v1/workspace/collections?conversation_id={conv_id}")
        assert resp.status_code == 404

    def test_get_collections_success(self, client, mock_conv_service, mock_ws_service, test_user_id):
        conv_id = uuid4()
        mock_conv_service.get_conversation.return_value = _make_conversation(test_user_id, id=conv_id)
        coll = _make_collection(conversation_id=conv_id)
        mock_ws_service.get_collections_for_canvas.return_value = [coll]
        resp = client.get(f"/v1/workspace/collections?conversation_id={conv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1

    def test_update_filters_returns_summary(self, client, mock_conv_service, mock_ws_service, test_user_id):
        conv_id = uuid4()
        coll_id = uuid4()
        mock_conv_service.get_conversation.return_value = _make_conversation(test_user_id, id=conv_id)
        coll = _make_collection(id=coll_id, conversation_id=conv_id)
        mock_ws_service.validate_ownership.return_value = coll
        mock_ws_service.filter_collection.return_value = (coll, _make_summary())
        resp = client.patch(
            f"/v1/workspace/collections/{coll_id}/filters?conversation_id={conv_id}",
            json={"filters": {"platform": "tiktok"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "collection" in data

    def test_get_tool_results_with_filter(self, client, mock_conv_service, mock_ws_service, test_user_id):
        conv_id = uuid4()
        mock_conv_service.get_conversation.return_value = _make_conversation(test_user_id, id=conv_id)
        tr = WorkspaceToolResult(
            id=uuid4(), conversation_id=conv_id, tool_name="search_videos",
            input_args={}, result_data={"r": 1}, workspace_item_id=None,
            created_at=datetime.now(UTC),
        )
        mock_ws_service.get_tool_results.return_value = [tr]
        resp = client.get(f"/v1/workspace/tool-results?conversation_id={conv_id}&tool_name=search_videos")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["tool_name"] == "search_videos"

    def test_get_tool_results_without_filter(self, client, mock_conv_service, mock_ws_service, test_user_id):
        conv_id = uuid4()
        mock_conv_service.get_conversation.return_value = _make_conversation(test_user_id, id=conv_id)
        mock_ws_service.get_tool_results.return_value = []
        resp = client.get(f"/v1/workspace/tool-results?conversation_id={conv_id}")
        assert resp.status_code == 200
