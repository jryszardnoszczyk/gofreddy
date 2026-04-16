"""HTTP tests for operational endpoints (webhooks/internal/usage)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_billing_context, get_stripe_client
from src.api.exceptions import register_exception_handlers
from src.api.rate_limit import limiter
from src.api.routers.internal import router as internal_router
from src.api.routers.usage import router as usage_router
from src.api.routers.webhooks import router as webhooks_router
from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.tiers import Tier


def _pro_context() -> BillingContext:
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        email="pro@videointel.test",
        stripe_customer_id="cus_test",
        created_at=now,
    )
    usage = UsagePeriod(
        id=uuid4(),
        user_id=user.id,
        period_start=now,
        period_end=now,
        videos_used=25,
        videos_limit=50000,
    )
    return BillingContext(user=user, tier=Tier.PRO, usage_period=usage, subscription=None)


@pytest.fixture
def valid_api_key() -> str:
    return "operational_test_key"


@pytest.fixture
def app():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(webhooks_router)
    app.include_router(internal_router)
    app.include_router(usage_router, prefix="/v1")
    limiter.enabled = False
    app.state.billing_service = MagicMock()
    app.state.billing_repository = MagicMock()
    mock_billing_flags = MagicMock()
    mock_billing_flags.hybrid_read_enabled = False
    app.state.billing_flags = mock_billing_flags
    app.state.credit_service = MagicMock()
    mock_conv_service = MagicMock()
    mock_conv_service.get_daily_count = AsyncMock(return_value=0)
    app.state.conversation_service = mock_conv_service
    app.state.job_worker = MagicMock()
    app.state.job_worker.process_job = AsyncMock(return_value=None)
    try:
        yield app
    finally:
        limiter.enabled = True


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.mock_required
class TestStripeWebhook:
    """Required test cases for /webhooks/stripe."""

    def test_stripe_not_configured_returns_503(self, app, client: TestClient) -> None:
        app.dependency_overrides[get_stripe_client] = lambda: None

        response = client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=fake"},
        )
        assert response.status_code == 503
        error = response.json()["error"]
        assert error["code"] == "stripe_not_configured"
        assert "message" in error

    def test_missing_signature_header_returns_422(self, client: TestClient) -> None:
        response = client.post("/webhooks/stripe", content=b"{}")
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "validation_error"
        assert "message" in error

    def test_invalid_signature_payload_returns_400(self, app, client: TestClient) -> None:
        mock_client = MagicMock()
        mock_client.construct_event.side_effect = ValueError("bad payload")
        app.dependency_overrides[get_stripe_client] = lambda: mock_client
        app.state.stripe_settings = MagicMock()
        app.state.stripe_settings.webhook_secret.get_secret_value.return_value = "whsec_test"

        response = client.post(
            "/webhooks/stripe",
            content=b"{not-json",
            headers={"stripe-signature": "t=1,v1=bad"},
        )

        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "webhook_error"
        assert error["message"] == "Webhook error"

    def test_error_envelope_consistency_across_failures(
        self, app, client: TestClient
    ) -> None:
        app.dependency_overrides[get_stripe_client] = lambda: None
        not_configured = client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=fake"},
        )
        app.dependency_overrides.clear()

        missing_sig = client.post("/webhooks/stripe", content=b"{}")

        mock_client = MagicMock()
        mock_client.construct_event.side_effect = ValueError("bad payload")
        app.dependency_overrides[get_stripe_client] = lambda: mock_client
        app.state.stripe_settings = MagicMock()
        app.state.stripe_settings.webhook_secret.get_secret_value.return_value = "whsec_test"

        invalid_sig = client.post(
            "/webhooks/stripe",
            content=b"{bad",
            headers={"stripe-signature": "t=1,v1=bad"},
        )

        for response in (not_configured, missing_sig, invalid_sig):
            body = response.json()
            assert "error" in body
            assert isinstance(body["error"], dict)
            assert "code" in body["error"]
            assert "message" in body["error"]


@pytest.mark.mock_required
class TestInternalProcessJob:
    """Required auth test cases for /internal/process-job."""

    def test_missing_oidc_returns_401(self, client: TestClient) -> None:
        response = client.post("/internal/process-job", json={"job_id": str(uuid4())})
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Missing OIDC token"

    def test_malformed_bearer_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/internal/process-job",
            json={"job_id": str(uuid4())},
            headers={"Authorization": "Token bad"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Invalid authorization format"

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            side_effect=ValueError("invalid"),
        ):
            response = client.post(
                "/internal/process-job",
                json={"job_id": str(uuid4())},
                headers={"Authorization": "Bearer invalid-token"},
            )
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Invalid OIDC token"

    def test_unauthorized_service_account_returns_403(self, app, client: TestClient, monkeypatch) -> None:
        import src.api.routers.internal as internal

        # Require a specific service account email.
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setattr(internal, "ALLOWED_SERVICE_ACCOUNTS", ["allowed@service.test"])

        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={"email": "not-allowed@service.test"},
        ):
            response = client.post(
                "/internal/process-job",
                json={"job_id": str(uuid4())},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 403
        assert response.json()["error"]["message"] == "Unauthorized service account"
        app.state.job_worker.process_job.assert_not_called()

    def test_valid_token_allows_allowed_service_account(self, app, client: TestClient, monkeypatch) -> None:
        import src.api.routers.internal as internal

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setattr(internal, "ALLOWED_SERVICE_ACCOUNTS", ["allowed@service.test"])

        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={"email": "allowed@service.test"},
        ):
            response = client.post(
                "/internal/process-job",
                json={"job_id": str(uuid4())},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        app.state.job_worker.process_job.assert_awaited_once()

    def test_development_bypass_allows_request(self, app, client: TestClient, monkeypatch) -> None:
        import src.api.routers.internal as internal_router

        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setattr(internal_router, "_is_development", True)
        monkeypatch.setattr(internal_router, "ALLOWED_SERVICE_ACCOUNTS", [])

        response = client.post("/internal/process-job", json={"job_id": str(uuid4())})
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        app.state.job_worker.process_job.assert_awaited_once()


@pytest.mark.mock_required
class TestUsageEndpoint:
    """Coverage for /v1/usage endpoint."""

    def test_usage_returns_expected_payload(
        self, app, client: TestClient, valid_api_key: str
    ) -> None:
        context = _pro_context()
        app.dependency_overrides[get_billing_context] = lambda: context
        app.state.billing_service.get_usage_stats = AsyncMock(
            return_value={
                "tier": "pro",
                "videos_used": 25,
                "videos_limit": 50000,
                "videos_remaining": 49975,
                "usage_percent": 0.1,
                "billing_period_start": "2026-02-01T00:00:00+00:00",
                "billing_period_end": "2026-02-28T23:59:59+00:00",
                "rate_limit_per_minute": 300,
                "subscription_status": "active",
            }
        )

        response = client.get(
            "/v1/usage",
            headers={"Authorization": f"Bearer {valid_api_key}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["tier"] == "pro"
        assert body["rate_limit_per_minute"] == 300
