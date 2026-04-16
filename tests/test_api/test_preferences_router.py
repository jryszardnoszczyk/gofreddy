"""Tests for preferences router."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier
from src.common.gemini_models import GEMINI_FLASH, GEMINI_FLASH_LITE, GEMINI_PRO


def _assert_error_envelope(payload: dict) -> None:
    assert "error" in payload
    assert isinstance(payload["error"], dict)
    assert "code" in payload["error"]
    assert "message" in payload["error"]


@pytest.mark.mock_required
class TestGetPreferences:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.get("/v1/preferences")
        assert response.status_code == 401

    def test_returns_default_preferences(self, client: TestClient, valid_api_key: str) -> None:
        client.app.state.billing_repository.get_preferences = AsyncMock(return_value={})
        response = client.get(
            "/v1/preferences",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["agent_model"] == GEMINI_FLASH

    def test_returns_stored_preferences(self, client: TestClient, valid_api_key: str) -> None:
        client.app.state.billing_repository.get_preferences = AsyncMock(
            return_value={"agent_model": GEMINI_PRO}
        )
        response = client.get(
            "/v1/preferences",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["agent_model"] == GEMINI_PRO


@pytest.mark.mock_required
class TestPatchPreferences:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.patch("/v1/preferences", json={"agent_model": GEMINI_FLASH})
        assert response.status_code == 401

    def test_pro_user_can_set_pro_model(self, client: TestClient, valid_api_key: str) -> None:
        client.app.state.billing_repository.update_preferences = AsyncMock(
            return_value={"agent_model": GEMINI_PRO}
        )
        response = client.patch(
            "/v1/preferences",
            json={"agent_model": GEMINI_PRO},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["agent_model"] == GEMINI_PRO

    def test_rejects_invalid_model(self, client: TestClient, valid_api_key: str) -> None:
        response = client.patch(
            "/v1/preferences",
            json={"agent_model": "gemini-unknown"},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 422

    def test_free_user_cannot_set_pro_model(self, client: TestClient, valid_api_key: str) -> None:
        _now = datetime.now(UTC)
        _uid = uuid4()
        free_ctx = BillingContext(
            user=User(id=_uid, email="free@test.com", stripe_customer_id=None, created_at=_now),
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(),
                user_id=_uid,
                period_start=_now,
                period_end=_now,
                videos_used=0,
                videos_limit=100,
            ),
            subscription=None,
        )
        client.app.state.billing_service.get_billing_context_for_user = AsyncMock(
            return_value=free_ctx
        )

        response = client.patch(
            "/v1/preferences",
            json={"agent_model": GEMINI_PRO},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 403
        payload = response.json()
        _assert_error_envelope(payload)
        assert payload["error"]["code"] == "pro_required"

    def test_free_user_can_set_flash_model(self, client: TestClient, valid_api_key: str) -> None:
        _now = datetime.now(UTC)
        _uid = uuid4()
        free_ctx = BillingContext(
            user=User(id=_uid, email="free@test.com", stripe_customer_id=None, created_at=_now),
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(),
                user_id=_uid,
                period_start=_now,
                period_end=_now,
                videos_used=0,
                videos_limit=100,
            ),
            subscription=None,
        )
        client.app.state.billing_service.get_billing_context_for_user = AsyncMock(
            return_value=free_ctx
        )
        client.app.state.billing_repository.update_preferences = AsyncMock(
            return_value={"agent_model": GEMINI_FLASH}
        )

        response = client.patch(
            "/v1/preferences",
            json={"agent_model": GEMINI_FLASH},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["agent_model"] == GEMINI_FLASH

    def test_free_user_can_set_flash_lite_model(self, client: TestClient, valid_api_key: str) -> None:
        _now = datetime.now(UTC)
        _uid = uuid4()
        free_ctx = BillingContext(
            user=User(id=_uid, email="free@test.com", stripe_customer_id=None, created_at=_now),
            tier=Tier.FREE,
            usage_period=UsagePeriod(
                id=uuid4(),
                user_id=_uid,
                period_start=_now,
                period_end=_now,
                videos_used=0,
                videos_limit=100,
            ),
            subscription=None,
        )
        client.app.state.billing_service.get_billing_context_for_user = AsyncMock(
            return_value=free_ctx
        )
        client.app.state.billing_repository.update_preferences = AsyncMock(
            return_value={"agent_model": GEMINI_FLASH_LITE}
        )

        response = client.patch(
            "/v1/preferences",
            json={"agent_model": GEMINI_FLASH_LITE},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["agent_model"] == GEMINI_FLASH_LITE

    def test_empty_update_returns_current(self, client: TestClient, valid_api_key: str) -> None:
        client.app.state.billing_repository.get_preferences = AsyncMock(
            return_value={"agent_model": GEMINI_PRO}
        )
        response = client.patch(
            "/v1/preferences",
            json={},
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["agent_model"] == GEMINI_PRO
