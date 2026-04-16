"""HTTP router tests for story endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_current_user_id, verify_supabase_token
from src.api.exceptions import register_exception_handlers
from src.api.rate_limit import limiter
from src.api.routers.stories import router
from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier


def _billing_context(tier: Tier) -> BillingContext:
    """Build billing context with the requested tier."""
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        email="stories@test.com",
        stripe_customer_id=None if tier == Tier.FREE else "cus_pro",
        created_at=now,
    )
    usage = UsagePeriod(
        id=uuid4(),
        user_id=user.id,
        period_start=now,
        period_end=now,
        videos_used=0,
        videos_limit=100 if tier == Tier.FREE else 50000,
    )
    return BillingContext(user=user, tier=tier, usage_period=usage, subscription=None)


@pytest.fixture
def valid_api_key() -> str:
    return "stories_test_key"


@pytest.fixture
def app():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/v1")
    limiter.enabled = False

    # Auth — bypass JWT but keep HTTPBearer presence check
    _test_user_id = uuid4()
    _test_claims = {"sub": "test-stories-user", "email": "stories@test.com", "aud": "authenticated"}
    _security = HTTPBearer()

    async def _mock_verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> dict:
        return _test_claims

    async def _mock_get_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> UUID:
        return _test_user_id

    app.dependency_overrides[verify_supabase_token] = _mock_verify_token
    app.dependency_overrides[get_current_user_id] = _mock_get_user_id
    app.state.billing_service = MagicMock()
    app.state.story_service = MagicMock()
    try:
        yield app
    finally:
        limiter.enabled = True


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.mock_required
class TestCaptureStoriesHTTP:
    """Tests for POST /v1/stories/{platform}/{username}/capture."""

    def test_requires_authentication(self, client: TestClient) -> None:
        response = client.post("/v1/stories/instagram/testuser/capture")
        assert response.status_code in (401, 403)

    def test_free_tier_returns_contract_error(
        self, client: TestClient, app, valid_api_key: str
    ) -> None:
        app.dependency_overrides[get_billing_context] = lambda: _billing_context(Tier.FREE)

        response = client.post(
            "/v1/stories/instagram/testuser/capture",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["required_tier"] == "pro"
        assert error["current_tier"] == "free"
        assert error["feature"] == "stories_capture"
        assert "upgrade_url" not in error

    def test_capture_returns_501_temporarily_unavailable(
        self, client: TestClient, app, valid_api_key: str
    ) -> None:
        """Stories capture disabled — Apify actor discontinued Feb 2026."""
        app.dependency_overrides[get_billing_context] = lambda: _billing_context(Tier.PRO)

        response = client.post(
            "/v1/stories/instagram/testuser/capture",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 501
        assert response.json()["error"]["code"] == "stories_temporarily_unavailable"


@pytest.mark.mock_required
class TestGetStoriesHTTP:
    """Tests for GET /v1/stories/{platform}/{username}."""

    def test_free_tier_returns_contract_error(
        self, client: TestClient, app, valid_api_key: str
    ) -> None:
        app.dependency_overrides[get_billing_context] = lambda: _billing_context(Tier.FREE)

        response = client.get(
            "/v1/stories/instagram/testuser",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["required_tier"] == "pro"
        assert error["current_tier"] == "free"
        assert error["feature"] == "stories_access"
        assert "upgrade_url" not in error

    def test_get_stories_success(
        self, client: TestClient, app, valid_api_key: str
    ) -> None:
        now = datetime.now(timezone.utc)
        app.dependency_overrides[get_billing_context] = lambda: _billing_context(Tier.PRO)
        app.state.story_service.get_captured_stories = AsyncMock(
            return_value=[
                {
                    "id": uuid4(),
                    "story_id": "ig_456",
                    "platform": "instagram",
                    "creator_username": "testuser",
                    "media_type": "image",
                    "media_url": "https://r2/presigned-image",
                    "duration_seconds": None,
                    "original_posted_at": now,
                    "original_expires_at": now,
                    "captured_at": now,
                }
            ]
        )

        response = client.get(
            "/v1/stories/instagram/testuser",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        stories = response.json()
        assert len(stories) == 1
        assert stories[0]["story_id"] == "ig_456"
        app.state.story_service.get_captured_stories.assert_awaited_once()
