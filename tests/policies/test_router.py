"""Tests for policy CRUD API endpoints."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier
from src.policies.models import BrandPolicyResponse, PolicyRule
from src.policies.repository import PolicyNameExistsError
from src.policies.service import (
    PolicyNotFoundError,
    PolicyService,
    PresetModificationError,
    TierRestrictedClassError,
)
from src.schemas import ModerationClass, Severity


# ── Test fixtures ───────────────────────────────────────────────────────────

TEST_USER_ID = uuid4()
TEST_POLICY_ID = uuid4()


def _make_billing_context(tier: Tier = Tier.PRO) -> BillingContext:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return BillingContext(
        user=User(id=TEST_USER_ID, email="test@test.com", stripe_customer_id=None, created_at=now),
        tier=tier,
        usage_period=UsagePeriod(
            id=uuid4(), user_id=TEST_USER_ID,
            period_start=now, period_end=now,
            videos_used=0, videos_limit=100,
        ),
        subscription=None,
    )


def _make_policy_response(**kwargs) -> BrandPolicyResponse:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    defaults = {
        "id": TEST_POLICY_ID,
        "user_id": TEST_USER_ID,
        "policy_name": "Test Policy",
        "rules": [PolicyRule(
            moderation_class=ModerationClass.HATE_SPEECH,
            max_severity=Severity.NONE,
            action="block",
        )],
        "is_preset": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return BrandPolicyResponse(**defaults)


@pytest.fixture
def mock_service():
    return AsyncMock(spec=PolicyService)


@pytest.fixture
def app(mock_service):
    """Create a test FastAPI app with the policies router."""
    from src.api.routers.policies import router
    from src.api.rate_limit import limiter

    from src.api.exceptions import register_exception_handlers

    test_app = FastAPI()
    test_app.state.limiter = limiter
    register_exception_handlers(test_app)

    # Wire dependencies
    async def override_user_id():
        return TEST_USER_ID

    async def override_billing_context():
        return _make_billing_context()

    async def override_policy_service():
        return mock_service

    from src.api.dependencies import get_current_user_id, get_billing_context, get_policy_service

    test_app.dependency_overrides[get_current_user_id] = override_user_id
    test_app.dependency_overrides[get_billing_context] = override_billing_context
    test_app.dependency_overrides[get_policy_service] = override_policy_service

    test_app.include_router(router, prefix="/v1")
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


# ── POST /v1/policies ──────────────────────────────────────────────────────


class TestCreatePolicy:
    def test_post_create_policy_201(self, client, mock_service):
        response = _make_policy_response()
        mock_service.create_policy.return_value = response
        resp = client.post("/v1/policies", json={
            "policy_name": "Test Policy",
            "rules": [{"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["policy_name"] == "Test Policy"
        assert data["is_preset"] is False

    def test_post_duplicate_name_409(self, client, mock_service):
        mock_service.create_policy.side_effect = PolicyNameExistsError("Dup")
        resp = client.post("/v1/policies", json={
            "policy_name": "Dup",
            "rules": [{"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "policy_name_exists"

    def test_post_invalid_moderation_class_422(self, client, mock_service):
        resp = client.post("/v1/policies", json={
            "policy_name": "Bad",
            "rules": [{"moderation_class": "totally_fake", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 422

    def test_post_too_many_rules_422(self, client, mock_service):
        rules = [
            {"moderation_class": f"hate_speech", "max_severity": "none", "action": "block"}
        ] * 31  # Over the 30 limit
        resp = client.post("/v1/policies", json={
            "policy_name": "Too Many",
            "rules": rules,
        })
        assert resp.status_code == 422

    def test_post_zero_rules_422(self, client, mock_service):
        resp = client.post("/v1/policies", json={
            "policy_name": "Empty",
            "rules": [],
        })
        assert resp.status_code == 422

    def test_post_tier_restricted_403(self, client, mock_service):
        mock_service.create_policy.side_effect = TierRestrictedClassError("nazi_symbols")
        resp = client.post("/v1/policies", json={
            "policy_name": "PRO Only",
            "rules": [{"moderation_class": "nazi_symbols", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "tier_restricted_class"


# ── GET /v1/policies ───────────────────────────────────────────────────────


class TestListPolicies:
    def test_get_list_includes_presets(self, client, mock_service):
        mock_service.list_policies.return_value = [
            _make_policy_response(user_id=None, policy_name="Family Safe", is_preset=True),
            _make_policy_response(policy_name="My Policy"),
        ]
        resp = client.get("/v1/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["is_preset"] is True
        assert data[1]["is_preset"] is False


# ── GET /v1/policies/{id} ─────────────────────────────────────────────────


class TestGetPolicy:
    def test_get_single_policy(self, client, mock_service):
        response = _make_policy_response()
        mock_service.get_policy.return_value = response
        resp = client.get(f"/v1/policies/{TEST_POLICY_ID}")
        assert resp.status_code == 200
        assert resp.json()["policy_name"] == "Test Policy"

    def test_get_single_other_users_policy_404(self, client, mock_service):
        mock_service.get_policy.side_effect = PolicyNotFoundError()
        resp = client.get(f"/v1/policies/{uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "policy_not_found"


# ── PUT /v1/policies/{id} ─────────────────────────────────────────────────


class TestUpdatePolicy:
    def test_put_update_policy(self, client, mock_service):
        response = _make_policy_response(policy_name="Updated")
        mock_service.update_policy.return_value = response
        resp = client.put(f"/v1/policies/{TEST_POLICY_ID}", json={
            "policy_name": "Updated",
            "rules": [{"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 200
        assert resp.json()["policy_name"] == "Updated"

    def test_put_preset_403(self, client, mock_service):
        mock_service.update_policy.side_effect = PresetModificationError()
        resp = client.put(f"/v1/policies/{uuid4()}", json={
            "policy_name": "Hacked",
            "rules": [{"moderation_class": "hate_speech", "max_severity": "none", "action": "block"}],
        })
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "preset_read_only"


# ── DELETE /v1/policies/{id} ──────────────────────────────────────────────


class TestDeletePolicy:
    def test_delete_policy_204(self, client, mock_service):
        mock_service.delete_policy.return_value = None
        resp = client.delete(f"/v1/policies/{TEST_POLICY_ID}")
        assert resp.status_code == 204

    def test_delete_preset_403(self, client, mock_service):
        mock_service.delete_policy.side_effect = PresetModificationError()
        resp = client.delete(f"/v1/policies/{uuid4()}")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "preset_read_only"

    def test_delete_not_found_404(self, client, mock_service):
        mock_service.delete_policy.side_effect = PolicyNotFoundError()
        resp = client.delete(f"/v1/policies/{uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "policy_not_found"
