"""Tests for API key management endpoints."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from src.billing.models import APIKey


@pytest.fixture
def mock_api_key() -> APIKey:
    """Mock API key."""
    return APIKey(
        id=uuid4(),
        user_id=uuid4(),
        key_prefix="vi_sk_test12",
        name="Test Key",
        created_at=datetime.now(UTC),
        last_used_at=None,
        expires_at=None,
        is_active=True,
    )


class TestCreateApiKey:
    """Tests for POST /v1/api-keys."""

    def test_create_key_success(self, client: TestClient, mock_api_key: APIKey):
        """Create key returns cleartext key with vi_sk_ prefix."""
        client.app.state.billing_repository.create_api_key_atomic = AsyncMock(
            return_value=mock_api_key
        )
        resp = client.post(
            "/v1/api-keys",
            json={"name": "My Key"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"].startswith("vi_sk_")
        assert data["key_prefix"] == mock_api_key.key_prefix
        assert data["name"] == "My Key" or data["name"] == mock_api_key.name

    def test_create_key_max_limit(self, client: TestClient):
        """11th key creation returns 400."""
        client.app.state.billing_repository.create_api_key_atomic = AsyncMock(
            return_value=None
        )
        resp = client.post(
            "/v1/api-keys",
            json={"name": "Over Limit"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        # Exception handler normalizes to {"error": {"code": ...}} envelope
        assert resp.json()["error"]["code"] == "max_keys_reached"

    def test_create_key_no_name(self, client: TestClient, mock_api_key: APIKey):
        """Create key without name succeeds."""
        client.app.state.billing_repository.create_api_key_atomic = AsyncMock(
            return_value=mock_api_key
        )
        resp = client.post(
            "/v1/api-keys",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201

    def test_create_key_no_auth(self, client: TestClient):
        """Create key without auth returns 401/403."""
        resp = client.post("/v1/api-keys", json={"name": "Test"})
        assert resp.status_code in (401, 403)


class TestListApiKeys:
    """Tests for GET /v1/api-keys."""

    def test_list_keys_success(self, client: TestClient, mock_api_key: APIKey):
        """List returns masked keys."""
        client.app.state.billing_repository.list_api_keys = AsyncMock(
            return_value=[mock_api_key]
        )
        resp = client.get(
            "/v1/api-keys",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["key_prefix"] == mock_api_key.key_prefix
        assert data[0]["is_active"] is True
        # Full key should NOT be in the response
        assert "key" not in data[0] or not data[0].get("key", "").startswith("vi_sk_")

    def test_list_keys_empty(self, client: TestClient):
        """List returns empty when no keys."""
        client.app.state.billing_repository.list_api_keys = AsyncMock(return_value=[])
        resp = client.get(
            "/v1/api-keys",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestRevokeApiKey:
    """Tests for DELETE /v1/api-keys/{key_id}."""

    def test_revoke_key_success(self, client: TestClient):
        """Revoke key returns success."""
        key_id = uuid4()
        client.app.state.billing_repository.revoke_api_key = AsyncMock(return_value=True)
        resp = client.delete(
            f"/v1/api-keys/{key_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"

    def test_revoke_nonexistent_key(self, client: TestClient):
        """Revoke nonexistent key returns 404."""
        key_id = uuid4()
        client.app.state.billing_repository.revoke_api_key = AsyncMock(return_value=False)
        client.app.state.billing_repository.list_api_keys = AsyncMock(return_value=[])
        resp = client.delete(
            f"/v1/api-keys/{key_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 404

    def test_revoke_already_revoked(self, client: TestClient, mock_api_key: APIKey):
        """Revoke already-revoked key returns success (idempotent)."""
        revoked_key = APIKey(
            id=mock_api_key.id,
            user_id=mock_api_key.user_id,
            key_prefix=mock_api_key.key_prefix,
            name=mock_api_key.name,
            created_at=mock_api_key.created_at,
            last_used_at=None,
            expires_at=None,
            is_active=False,
        )
        client.app.state.billing_repository.revoke_api_key = AsyncMock(return_value=False)
        client.app.state.billing_repository.list_api_keys = AsyncMock(return_value=[revoked_key])
        resp = client.delete(
            f"/v1/api-keys/{mock_api_key.id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"
