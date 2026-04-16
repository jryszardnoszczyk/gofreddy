"""Tests for billing API endpoints — GET /v1/billing/summary and POST /v1/billing/topups/checkout."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import stripe
from fastapi.testclient import TestClient

from src.billing.models import User
from src.billing.service import BillingService


class TestGetBillingSummary:
    """Tests for GET /v1/billing/summary."""

    def test_returns_credit_balance(self, client: TestClient):
        """Summary endpoint returns credit balance breakdown."""
        resp = client.get(
            "/v1/billing/summary",
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["promo_remaining"] == 5
        assert data["included_remaining"] == 100
        assert data["topup_remaining"] == 50
        assert data["reserved_total"] == 10
        assert data["available"] == 145
        assert data["billing_model_version"] == "credits_v1"

    def test_requires_auth(self, client: TestClient):
        """Summary endpoint rejects unauthenticated requests."""
        resp = client.get("/v1/billing/summary")
        assert resp.status_code in (401, 403)


class TestCreateTopupCheckout:
    """Tests for POST /v1/billing/topups/checkout."""

    def test_invalid_pack_code(self, client: TestClient):
        """Invalid pack code returns 400."""
        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "nonexistent_pack"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert "invalid_pack_code" in str(resp.json())

    def test_stripe_not_configured(self, client: TestClient):
        """Valid pack but no Stripe client returns 503."""
        # stripe_client is None by default in conftest
        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 503
        assert "payment_unavailable" in str(resp.json())

    def test_checkout_success(self, client: TestClient):
        """Valid pack + configured Stripe returns checkout URL."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/c/pay_test123"
        mock_session.id = "cs_test_abc123"

        mock_stripe = MagicMock()
        mock_stripe.v1.checkout.sessions.create_async = AsyncMock(return_value=mock_session)

        mock_billing = client.app.state.billing_service
        mock_billing.get_or_create_stripe_customer = AsyncMock(return_value="cus_test123")

        client.app.state.stripe_client = mock_stripe

        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["checkout_url"] == "https://checkout.stripe.com/c/pay_test123"
        assert data["session_id"] == "cs_test_abc123"

        # Verify Stripe was called with correct params
        call_kwargs = mock_stripe.v1.checkout.sessions.create_async.call_args
        params = call_kwargs.kwargs["params"]
        assert params["customer"] == "cus_test123"
        assert params["metadata"]["pack_code"] == "starter_100"
        assert params["metadata"]["credits"] == "100"

    def test_checkout_stripe_timeout(self, client: TestClient):
        """Stripe timeout returns 504."""
        mock_stripe = MagicMock()
        mock_stripe.v1.checkout.sessions.create_async = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        mock_billing = client.app.state.billing_service
        mock_billing.get_or_create_stripe_customer = AsyncMock(return_value="cus_test123")

        client.app.state.stripe_client = mock_stripe

        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 504

    def test_checkout_stripe_connection_error(self, client: TestClient):
        """Stripe connection error returns 503."""
        mock_stripe = MagicMock()
        mock_stripe.v1.checkout.sessions.create_async = AsyncMock(
            side_effect=stripe.APIConnectionError("Connection refused")
        )

        mock_billing = client.app.state.billing_service
        mock_billing.get_or_create_stripe_customer = AsyncMock(return_value="cus_test123")

        client.app.state.stripe_client = mock_stripe

        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "growth_500"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 503

    def test_checkout_stripe_rate_limit(self, client: TestClient):
        """Stripe rate-limit error during customer resolution returns 429."""
        mock_stripe = MagicMock()

        mock_billing = client.app.state.billing_service
        mock_billing.get_or_create_stripe_customer = AsyncMock(
            side_effect=stripe.RateLimitError(message="Rate limited")
        )

        client.app.state.stripe_client = mock_stripe

        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 429
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "payment_rate_limited"

    def test_checkout_stripe_generic_error(self, client: TestClient):
        """Generic Stripe error during customer resolution returns 502."""
        mock_stripe = MagicMock()

        mock_billing = client.app.state.billing_service
        mock_billing.get_or_create_stripe_customer = AsyncMock(
            side_effect=stripe.StripeError(message="Something went wrong")
        )

        client.app.state.stripe_client = mock_stripe

        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 502
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "payment_error"

    def test_requires_auth(self, client: TestClient):
        """Checkout endpoint rejects unauthenticated requests."""
        resp = client.post(
            "/v1/billing/topups/checkout",
            json={"pack_code": "starter_100"},
        )
        assert resp.status_code in (401, 403)


class TestGetOrCreateStripeCustomerCAS:
    """Tests for CAS (compare-and-swap) race handling in BillingService.get_or_create_stripe_customer."""

    @pytest.mark.asyncio
    async def test_checkout_cas_race(self):
        """When set_stripe_customer_if_null returns False (another request won), re-read and return existing ID."""
        user_id = uuid4()
        existing_customer_id = "cus_winner_456"
        now = datetime.now(UTC)

        # First call: user has no stripe_customer_id (triggers Stripe create)
        user_without_stripe = User(
            id=user_id, email="test@test.com", stripe_customer_id=None, created_at=now,
        )
        # Second call (after CAS fails): user now has stripe_customer_id set by the winner
        user_with_stripe = User(
            id=user_id, email="test@test.com", stripe_customer_id=existing_customer_id, created_at=now,
        )

        mock_repo = MagicMock()
        mock_repo.get_user_by_id = AsyncMock(
            side_effect=[user_without_stripe, user_with_stripe]
        )
        mock_repo.set_stripe_customer_if_null = AsyncMock(return_value=False)

        mock_stripe_customer = MagicMock()
        mock_stripe_customer.id = "cus_loser_789"

        mock_stripe_client = MagicMock()
        mock_stripe_client.v1.customers.create_async = AsyncMock(
            return_value=mock_stripe_customer
        )

        service = BillingService(repository=mock_repo)

        result = await service.get_or_create_stripe_customer(user_id, mock_stripe_client)

        # Should return the winner's customer ID, not the one we just created
        assert result == existing_customer_id

        # Verify CAS was attempted with the loser's customer ID
        mock_repo.set_stripe_customer_if_null.assert_awaited_once_with(
            user_id, "cus_loser_789"
        )

        # Verify get_user_by_id was called twice (initial + re-read after CAS failure)
        assert mock_repo.get_user_by_id.await_count == 2
