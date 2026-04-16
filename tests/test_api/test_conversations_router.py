"""Tests for the conversations REST router.

Service is mocked -- we test HTTP status codes, response shapes, error
envelopes, and request validation.
"""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

from src.api.dependencies import (
    AuthPrincipal,
    get_auth_principal,
    get_current_user_id,
    verify_supabase_token,
)
from src.api.main import create_app
from src.api.rate_limit import limiter
from src.billing.models import BillingContext, UsagePeriod, User
from src.billing.service import BillingService
from src.billing.tiers import Tier
from src.conversations.exceptions import ConversationNotFoundError
from src.conversations.models import Conversation, ConversationMessage
from src.conversations.service import ConversationService


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_conversation(user_id, **kwargs):
    return Conversation(
        id=kwargs.get("id", uuid4()),
        user_id=user_id,
        title=kwargs.get("title", "Test Chat"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )


def _make_billing_context(user_id):
    now = datetime.now(UTC)
    return BillingContext(
        user=User(
            id=user_id,
            email="test@test.com",
            stripe_customer_id=None,
            created_at=now,
        ),
        tier=Tier.FREE,
        usage_period=UsagePeriod(
            id=uuid4(),
            user_id=user_id,
            period_start=now,
            period_end=now + timedelta(days=30),
            videos_used=0,
            videos_limit=100,
        ),
        subscription=None,
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_conversation_service():
    return AsyncMock(spec=ConversationService)


@pytest.fixture
def test_user_id():
    return uuid4()


@pytest.fixture
def app(mock_conversation_service, test_user_id):
    app = create_app()

    limiter.enabled = False

    # Inject conversation service (reads from app.state in router dependency)
    app.state.conversation_service = mock_conversation_service

    # Stub workspace_service so workspace router doesn't crash
    app.state.workspace_service = MagicMock()

    # Auth overrides
    _security = HTTPBearer()
    _test_claims = {
        "sub": "test-supabase-user-id",
        "email": "test@test.com",
        "aud": "authenticated",
    }

    async def _mock_verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> dict:
        return _test_claims

    async def _mock_get_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> UUID:
        return test_user_id

    async def _mock_get_auth_principal(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AuthPrincipal:
        return AuthPrincipal(
            user_id=test_user_id,
            credential_type="api_key",
            claims=None,
        )

    app.dependency_overrides[verify_supabase_token] = _mock_verify_token
    app.dependency_overrides[get_current_user_id] = _mock_get_user_id
    app.dependency_overrides[get_auth_principal] = _mock_get_auth_principal

    # Billing override for create endpoint
    from src.api.dependencies import get_billing_context

    billing_ctx = _make_billing_context(test_user_id)
    mock_billing = MagicMock(spec=BillingService)
    mock_billing.get_billing_context_for_user = AsyncMock(return_value=billing_ctx)
    mock_billing.check_can_analyze = AsyncMock()
    mock_billing.record_usage = AsyncMock()
    app.state.billing_service = mock_billing

    async def _override_billing(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> BillingContext:
        return billing_ctx

    app.dependency_overrides[get_billing_context] = _override_billing

    # Stubs for other app.state attributes that lifespan normally sets
    app.state.db_pool = MagicMock()
    app.state.video_storage = MagicMock()
    app.state.analyzer = MagicMock()
    app.state.fetchers = {}
    app.state.environment = "test"
    app.state.externals_mode = "fake"
    app.state.task_client_mode = "mock"

    mock_analysis_repo = MagicMock()
    mock_analysis_repo.user_has_access = AsyncMock(return_value=True)
    app.state.analysis_service = MagicMock()
    app.state.analysis_repository = mock_analysis_repo
    app.state.search_service = MagicMock()
    app.state.fraud_service = MagicMock()
    app.state.fraud_service.close = AsyncMock()
    app.state.fraud_repository = MagicMock()
    app.state.demographics_service = MagicMock()
    app.state.demographics_repository = MagicMock()
    app.state.brand_service = MagicMock()
    app.state.brand_repository = MagicMock()
    app.state.billing_repository = MagicMock()
    app.state.job_service = MagicMock()
    app.state.job_repository = MagicMock()
    app.state.task_client = MagicMock()
    app.state.job_worker = MagicMock()
    app.state.trend_service = MagicMock()
    app.state.trend_repository = MagicMock()
    app.state.evolution_service = MagicMock()
    app.state.evolution_repository = MagicMock()
    app.state.deepfake_service = MagicMock()
    app.state.deepfake_repository = MagicMock()
    app.state.story_service = MagicMock()
    app.state.story_repository = MagicMock()
    app.state.story_storage = MagicMock()
    app.state.orchestrator = MagicMock()

    yield app

    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestConversationsRouter:

    def test_create_conversation_201(
        self, client, mock_conversation_service, test_user_id
    ):
        """POST /v1/conversations returns 201 with conversation data."""
        conv = _make_conversation(test_user_id)
        mock_conversation_service.create_conversation.return_value = conv

        resp = client.post(
            "/v1/conversations",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "created_at" in data
        assert "expires_at" in data

    def test_list_conversations_200(
        self, client, mock_conversation_service, test_user_id
    ):
        """GET /v1/conversations returns paginated list."""
        convs = [_make_conversation(test_user_id, title=f"Conv {i}") for i in range(3)]
        mock_conversation_service.list_conversations.return_value = convs

        resp = client.get(
            "/v1/conversations?limit=10&offset=0",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 3
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_get_conversation_200(
        self, client, mock_conversation_service, test_user_id
    ):
        """GET /v1/conversations/{id} returns conversation when found."""
        conv = _make_conversation(test_user_id)
        mock_conversation_service.get_conversation.return_value = conv

        resp = client.get(
            f"/v1/conversations/{conv.id}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(conv.id)
        assert data["title"] == "Test Chat"

    def test_get_conversation_not_found_404(
        self, client, mock_conversation_service
    ):
        """GET /v1/conversations/{id} returns 404 when not found."""
        conv_id = uuid4()
        mock_conversation_service.get_conversation.side_effect = ConversationNotFoundError(conv_id)

        resp = client.get(
            f"/v1/conversations/{conv_id}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"

    def test_get_messages_200(
        self, client, mock_conversation_service, test_user_id
    ):
        """GET /v1/conversations/{id}/messages returns paginated messages."""
        conv_id = uuid4()
        messages = [
            ConversationMessage(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content=f"Msg {i}",
                metadata={},
                created_at=datetime.now(UTC),
            )
            for i in range(3)
        ]
        mock_conversation_service.get_messages.return_value = messages

        resp = client.get(
            f"/v1/conversations/{conv_id}/messages",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 3
        assert data["data"][0]["role"] == "user"

    def test_get_messages_not_found_404(
        self, client, mock_conversation_service
    ):
        """GET /v1/conversations/{id}/messages returns 404 for unknown conversation."""
        conv_id = uuid4()
        mock_conversation_service.get_messages.side_effect = ConversationNotFoundError(conv_id)

        resp = client.get(
            f"/v1/conversations/{conv_id}/messages",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"

    def test_rename_conversation_200(
        self, client, mock_conversation_service, test_user_id
    ):
        """PATCH /v1/conversations/{id} renames conversation."""
        conv_id = uuid4()
        renamed = _make_conversation(test_user_id, id=conv_id, title="Renamed")
        mock_conversation_service.rename_conversation.return_value = renamed

        resp = client.patch(
            f"/v1/conversations/{conv_id}",
            json={"title": "Renamed"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_rename_conversation_empty_title_422(self, client):
        """PATCH /v1/conversations/{id} rejects empty title."""
        resp = client.patch(
            f"/v1/conversations/{uuid4()}",
            json={"title": ""},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 422

    def test_rename_conversation_not_found_404(
        self, client, mock_conversation_service
    ):
        """PATCH /v1/conversations/{id} returns 404 when conversation not found."""
        conv_id = uuid4()
        mock_conversation_service.rename_conversation.side_effect = ConversationNotFoundError(conv_id)

        resp = client.patch(
            f"/v1/conversations/{conv_id}",
            json={"title": "New Title"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"

    def test_delete_conversation_204(
        self, client, mock_conversation_service, test_user_id
    ):
        """DELETE /v1/conversations/{id} returns 204."""
        conv_id = uuid4()
        mock_conversation_service.delete_conversation.return_value = None

        resp = client.delete(
            f"/v1/conversations/{conv_id}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 204

    def test_delete_conversation_not_found_404(
        self, client, mock_conversation_service
    ):
        """DELETE /v1/conversations/{id} returns 404 when not found."""
        conv_id = uuid4()
        mock_conversation_service.delete_conversation.side_effect = ConversationNotFoundError(conv_id)

        resp = client.delete(
            f"/v1/conversations/{conv_id}",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "conversation_not_found"

    def test_unauthenticated_returns_401_or_403(self, app):
        """Requests without auth header are rejected."""
        # Use a fresh client without the auth override
        clean_app = create_app()
        limiter.enabled = False
        # Don't override auth -- let real auth reject
        clean_app.state.conversation_service = MagicMock()
        clean_app.state.workspace_service = MagicMock()
        client = TestClient(clean_app, raise_server_exceptions=False)

        resp = client.get("/v1/conversations")
        # FastAPI's HTTPBearer returns 403 when no credentials provided
        assert resp.status_code in (401, 403)
        limiter.enabled = True
