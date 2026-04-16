"""Tests for auth router HTTP behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient


def _assert_error_envelope(payload: dict) -> None:
    assert "error" in payload
    assert isinstance(payload["error"], dict)
    assert "code" in payload["error"]
    assert "message" in payload["error"]


@pytest.mark.mock_required
class TestAuthRouter:
    """Router-level tests for /v1/auth endpoints."""

    def test_get_me_requires_auth(self, client: TestClient) -> None:
        response = client.get("/v1/auth/me")
        assert response.status_code == 401
        _assert_error_envelope(response.json())

    def test_get_me_with_auth_returns_profile_shape(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200

        payload = response.json()
        assert "user_id" in payload
        UUID(payload["user_id"])
        assert payload["email"] == "test@test.com"
        assert payload["tier"] == "pro"
        assert payload["subscription_status"] is None

    def test_get_me_service_failure_returns_503_envelope(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        client.app.state.billing_service.get_billing_context_for_user = AsyncMock(
            side_effect=Exception("forced billing failure")
        )

        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 503
        payload = response.json()
        _assert_error_envelope(payload)
        assert payload["error"]["code"] == "service_unavailable"

    def test_logout_requires_auth(self, client: TestClient) -> None:
        response = client.post("/v1/auth/logout")
        assert response.status_code == 401
        _assert_error_envelope(response.json())

    def test_logout_with_auth_returns_204_no_content(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        response = client.post(
            "/v1/auth/logout",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 204
        assert response.content == b""
