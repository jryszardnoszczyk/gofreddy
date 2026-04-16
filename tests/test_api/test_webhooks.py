"""Tests for Stripe webhook handler — state machine, checkout routing, invoice grants, price quarantine."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.credits.exceptions import PriceQuarantined
from src.billing.models import User


def _make_user(
    *,
    email: str = "test@example.com",
    stripe_customer_id: str | None = "cus_test",
) -> User:
    from datetime import datetime, timezone

    return User(
        id=uuid4(),
        email=email,
        stripe_customer_id=stripe_customer_id,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock BillingRepository for webhook tests."""
    repo = MagicMock()
    repo.get_user_by_stripe_customer = AsyncMock(return_value=None)
    repo.create_user = AsyncMock()
    repo.get_user_by_email = AsyncMock(return_value=None)
    repo.update_user_stripe_customer = AsyncMock()
    repo.upsert_subscription = AsyncMock()
    repo.get_subscription = AsyncMock(return_value=None)
    repo.get_or_create_usage_period = AsyncMock()
    repo.cancel_subscription = AsyncMock()
    repo.claim_webhook = AsyncMock(return_value=True)
    repo.mark_webhook_processed = AsyncMock()
    repo.mark_webhook_failed = AsyncMock()
    repo.mark_webhook_quarantined = AsyncMock()
    return repo


@pytest.fixture
def mock_stripe_client() -> MagicMock:
    """Mock StripeClient for webhook tests."""
    client = MagicMock()
    sub_mock = MagicMock()
    sub_mock.status = "active"
    sub_mock.current_period_start = 1700000000
    sub_mock.current_period_end = 1702592000
    sub_mock.items.data = [MagicMock(price=MagicMock(id="price_pro"))]
    client.v1.subscriptions.retrieve_async = AsyncMock(return_value=sub_mock)
    return client


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock StripeSettings."""
    settings = MagicMock()
    settings.price_pro = "price_pro"
    return settings


@pytest.fixture
def mock_credit_service() -> MagicMock:
    """Mock CreditService."""
    svc = MagicMock()
    svc.grant_topup_credits = AsyncMock(return_value=None)
    svc.grant_commit_credits_for_period = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def mock_credit_settings() -> MagicMock:
    """Mock CreditSettings."""
    settings = MagicMock()
    settings.pack_catalog = {"starter_100": (100, 999), "growth_500": (500, 3999), "scale_2000": (2000, 14999)}
    settings.included_credits_per_period = 1000
    return settings


# ─── Checkout Routing Tests ─────────────────────────────────────────────────


@pytest.mark.mock_required
class TestHandleCheckoutCompleted:
    """Tests for handle_checkout_completed — subscription vs top-up routing."""

    async def _call(self, session, repo, stripe_client, settings,
                    credit_service=None, credit_settings=None):
        from src.api.routers.webhooks import handle_checkout_completed

        cs = credit_service or MagicMock()
        csets = credit_settings or MagicMock()
        await handle_checkout_completed(session, repo, stripe_client, settings, cs, csets)

    @pytest.mark.asyncio
    async def test_subscription_checkout_updates_entitlement_no_credit_grant(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Subscription checkout updates subscription, does NOT call grant_topup_credits."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "customer": "cus_123",
            "subscription": "sub_456",
            "customer_email": "user@example.com",
            "mode": "subscription",
        }

        await self._call(
            session, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        mock_repo.upsert_subscription.assert_awaited_once()
        mock_credit_service.grant_topup_credits.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_normalizes_email_to_lowercase(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """customer_email is lowercased before user creation."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "customer": "cus_123",
            "subscription": "sub_456",
            "customer_email": "User@Example.COM",
        }

        await self._call(session, mock_repo, mock_stripe_client, mock_settings)

        mock_repo.create_user.assert_awaited_once()
        assert mock_repo.create_user.call_args.kwargs["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_none_email_uses_stripe_customer_fallback(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """None customer_email falls back to {customer_id}@stripe.customer."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "customer": "cus_789",
            "subscription": "sub_abc",
            "customer_email": None,
        }

        await self._call(session, mock_repo, mock_stripe_client, mock_settings)

        mock_repo.create_user.assert_awaited_once()
        call_args = mock_repo.create_user.call_args
        email_arg = call_args.kwargs.get("email")
        assert email_arg == "cus_789@stripe.customer"

    @pytest.mark.asyncio
    async def test_unique_violation_links_existing_user(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """UniqueViolationError on create_user looks up and links existing user."""
        import asyncpg

        existing = _make_user(email="existing@example.com")
        mock_repo.create_user = AsyncMock(
            side_effect=asyncpg.UniqueViolationError("")
        )
        mock_repo.get_user_by_email = AsyncMock(return_value=existing)

        session = {
            "customer": "cus_new",
            "subscription": "sub_new",
            "customer_email": "existing@example.com",
        }

        await self._call(session, mock_repo, mock_stripe_client, mock_settings)

        mock_repo.get_user_by_email.assert_awaited_once_with("existing@example.com")
        mock_repo.update_user_stripe_customer.assert_awaited_once_with(
            existing.id, "cus_new"
        )

    @pytest.mark.asyncio
    async def test_checkout_topup_grants_credits(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """credit_topup metadata triggers grant."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "id": "cs_topup_123",
            "customer": "cus_topup",
            "subscription": None,
            "customer_email": "buyer@example.com",
            "metadata": {"type": "credit_topup", "credits": "500"},
        }

        await self._call(
            session, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        mock_credit_service.grant_topup_credits.assert_awaited_once_with(
            user_id=user.id,
            units=500,
            source_id="cs_topup_123",
        )
        # Should NOT call upsert_subscription
        mock_repo.upsert_subscription.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_checkout_topup_invalid_credits_fails(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Non-numeric metadata.credits raises ValueError."""
        session = {
            "id": "cs_bad",
            "customer": "cus_bad",
            "subscription": None,
            "customer_email": "buyer@example.com",
            "metadata": {"type": "credit_topup", "credits": "not_a_number"},
        }

        with pytest.raises(ValueError):
            await self._call(
                session, mock_repo, mock_stripe_client, mock_settings,
                mock_credit_service, mock_credit_settings,
            )

    @pytest.mark.asyncio
    async def test_checkout_topup_missing_credits_fails(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Missing metadata.credits raises ValueError."""
        session = {
            "id": "cs_missing",
            "customer": "cus_missing",
            "subscription": None,
            "customer_email": "buyer@example.com",
            "metadata": {"type": "credit_topup"},
        }

        with pytest.raises(ValueError, match="missing metadata.credits"):
            await self._call(
                session, mock_repo, mock_stripe_client, mock_settings,
                mock_credit_service, mock_credit_settings,
            )

    @pytest.mark.asyncio
    async def test_checkout_topup_credits_not_in_pack_codes_fails(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Credits value not in whitelist rejected (security)."""
        session = {
            "id": "cs_hack",
            "customer": "cus_hack",
            "subscription": None,
            "customer_email": "hacker@example.com",
            "metadata": {"type": "credit_topup", "credits": "9999"},
        }

        with pytest.raises(ValueError, match="Invalid credit pack amount"):
            await self._call(
                session, mock_repo, mock_stripe_client, mock_settings,
                mock_credit_service, mock_credit_settings,
            )

    @pytest.mark.asyncio
    async def test_checkout_unknown_type_logs_warning(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """No subscription, no topup metadata → log and proceed."""
        session = {
            "id": "cs_unknown",
            "customer": "cus_unknown",
            "subscription": None,
            "customer_email": "user@example.com",
            "metadata": {},
        }

        # Should not raise
        await self._call(
            session, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        # Should NOT call grant or upsert
        mock_credit_service.grant_topup_credits.assert_not_awaited()
        mock_repo.upsert_subscription.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_checkout_null_email_topup(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """None email with customer_id uses fallback for topup."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "id": "cs_null_email",
            "customer": "cus_null",
            "subscription": None,
            "customer_email": None,
            "metadata": {"type": "credit_topup", "credits": "100"},
        }

        await self._call(
            session, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        mock_repo.create_user.assert_awaited_once()
        assert mock_repo.create_user.call_args.kwargs["email"] == "cus_null@stripe.customer"

    @pytest.mark.asyncio
    async def test_checkout_mode_subscription_without_subscription_id(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """session.mode=subscription but no subscription_id → handled gracefully."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        session = {
            "id": "cs_mode_only",
            "customer": "cus_mode",
            "subscription": None,
            "customer_email": "user@example.com",
            "mode": "subscription",
        }

        # Should not raise
        await self._call(
            session, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        # Subscription was not retrieved because subscription_id is None
        mock_stripe_client.v1.subscriptions.retrieve_async.assert_not_awaited()


# ─── Invoice Grant Tests ────────────────────────────────────────────────────


@pytest.mark.mock_required
class TestHandleInvoicePaid:
    """Tests for handle_invoice_paid with credit grants."""

    async def _call(self, invoice, repo, credit_service, credit_settings):
        from src.api.routers.webhooks import handle_invoice_paid

        await handle_invoice_paid(invoice, repo, credit_service, credit_settings)

    @pytest.mark.asyncio
    async def test_invoice_paid_grants_commit_credits(
        self,
        mock_repo: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Invoice paid grants commit credits with correct source key."""
        user = _make_user()
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=user)
        sub = MagicMock()
        sub.tier = MagicMock()
        mock_repo.get_subscription = AsyncMock(return_value=sub)

        invoice = {
            "customer": "cus_pay",
            "subscription": "sub_pay",
            "period_start": 1700000000,
        }

        await self._call(invoice, mock_repo, mock_credit_service, mock_credit_settings)

        mock_credit_service.grant_commit_credits_for_period.assert_awaited_once()
        call_kwargs = mock_credit_service.grant_commit_credits_for_period.call_args.kwargs
        assert call_kwargs["user_id"] == user.id
        assert call_kwargs["units"] == 1000
        assert call_kwargs["subscription_id"] == "sub_pay"
        assert "1700000000" not in call_kwargs["period_start"]  # Should be ISO format

    @pytest.mark.asyncio
    async def test_invoice_paid_no_subscription_skips(
        self,
        mock_repo: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """One-time payment invoice skips grant."""
        invoice = {
            "customer": "cus_onetime",
            "subscription": None,
        }

        await self._call(invoice, mock_repo, mock_credit_service, mock_credit_settings)

        mock_credit_service.grant_commit_credits_for_period.assert_not_awaited()
        mock_repo.get_user_by_stripe_customer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invoice_paid_unknown_customer_skips(
        self,
        mock_repo: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Unknown customer logged, skipped."""
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=None)

        invoice = {
            "customer": "cus_ghost",
            "subscription": "sub_ghost",
        }

        await self._call(invoice, mock_repo, mock_credit_service, mock_credit_settings)

        mock_credit_service.grant_commit_credits_for_period.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invoice_paid_resets_usage_period(
        self,
        mock_repo: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Invoice paid also resets usage period after granting credits."""
        user = _make_user()
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=user)
        sub = MagicMock()
        sub.tier = MagicMock()
        mock_repo.get_subscription = AsyncMock(return_value=sub)

        invoice = {
            "customer": "cus_reset",
            "subscription": "sub_reset",
            "period_start": 1700000000,
        }

        await self._call(invoice, mock_repo, mock_credit_service, mock_credit_settings)

        mock_repo.get_or_create_usage_period.assert_awaited_once()


# ─── Price Quarantine Tests ─────────────────────────────────────────────────


@pytest.mark.mock_required
class TestPriceToTier:
    """Tests for _price_to_tier with quarantine behavior."""

    def test_known_price_returns_pro(self, mock_settings: MagicMock) -> None:
        """Known price maps correctly."""
        from src.api.routers.webhooks import _price_to_tier
        from src.billing.tiers import Tier

        assert _price_to_tier("price_pro", mock_settings) == Tier.PRO

    def test_unknown_price_raises_quarantined(self, mock_settings: MagicMock) -> None:
        """Unknown price raises PriceQuarantined."""
        from src.api.routers.webhooks import _price_to_tier

        with pytest.raises(PriceQuarantined):
            _price_to_tier("price_unknown_xyz", mock_settings)

    @pytest.mark.asyncio
    async def test_subscription_updated_unknown_price_quarantines(
        self,
        mock_repo: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """subscription.updated with unknown price ID raises PriceQuarantined."""
        user = _make_user()
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=user)

        subscription_data = {
            "id": "sub_unknown_price",
            "customer": "cus_test",
            "status": "active",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "items": {"data": [{"price": {"id": "price_totally_unknown"}}]},
        }

        from src.api.routers.webhooks import handle_subscription_updated

        with pytest.raises(PriceQuarantined):
            await handle_subscription_updated(subscription_data, mock_repo, mock_settings)


# ─── Payment Failed Tests ───────────────────────────────────────────────────


@pytest.mark.mock_required
class TestHandlePaymentFailed:
    """Tests for handle_payment_failed structured logging."""

    @pytest.mark.asyncio
    async def test_logs_structured_warning_with_user(
        self,
        mock_repo: MagicMock,
        caplog,
    ) -> None:
        """Payment failure logs structured warning with user details."""
        import logging

        user = _make_user(stripe_customer_id="cus_fail")
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=user)

        invoice = {
            "id": "inv_123",
            "customer": "cus_fail",
            "attempt_count": 2,
            "amount_due": 2999,
        }

        from src.api.routers.webhooks import handle_payment_failed

        with caplog.at_level(logging.WARNING, logger="src.api.routers.webhooks"):
            await handle_payment_failed(invoice, mock_repo)

        assert any("payment_failed" in r.message for r in caplog.records)
        mock_repo.get_user_by_stripe_customer.assert_awaited_once_with("cus_fail")

    @pytest.mark.asyncio
    async def test_logs_without_user_when_customer_unknown(
        self,
        mock_repo: MagicMock,
        caplog,
    ) -> None:
        """Payment failure for unknown customer still logs."""
        import logging

        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=None)

        invoice = {
            "id": "inv_456",
            "customer": "cus_unknown",
            "attempt_count": 1,
            "amount_due": 999,
        }

        from src.api.routers.webhooks import handle_payment_failed

        with caplog.at_level(logging.WARNING, logger="src.api.routers.webhooks"):
            await handle_payment_failed(invoice, mock_repo)

        assert any("payment_failed" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_handles_none_customer_id(
        self,
        mock_repo: MagicMock,
    ) -> None:
        """None customer_id does not crash."""
        invoice = {"id": "inv_789", "customer": None}

        from src.api.routers.webhooks import handle_payment_failed

        await handle_payment_failed(invoice, mock_repo)

        mock_repo.get_user_by_stripe_customer.assert_not_awaited()


# ─── State Machine Tests (process_stripe_event level) ───────────────────────


@pytest.mark.mock_required
class TestProcessStripeEvent:
    """Tests for process_stripe_event with new signature."""

    @pytest.mark.asyncio
    async def test_checkout_dispatches_with_credit_args(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """process_stripe_event passes credit_service and credit_settings to handlers."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        event = MagicMock()
        event.type = "checkout.session.completed"
        event.id = "evt_test"
        event.data.object = {
            "customer": "cus_test",
            "subscription": "sub_test",
            "customer_email": "user@example.com",
        }

        from src.api.routers.webhooks import process_stripe_event

        await process_stripe_event(
            event, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        # Should not raise
        mock_repo.upsert_subscription.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invoice_paid_dispatches_with_credit_args(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """process_stripe_event passes credit_service to invoice.paid handler."""
        user = _make_user()
        mock_repo.get_user_by_stripe_customer = AsyncMock(return_value=user)
        sub = MagicMock()
        sub.tier = MagicMock()
        mock_repo.get_subscription = AsyncMock(return_value=sub)

        event = MagicMock()
        event.type = "invoice.paid"
        event.id = "evt_inv"
        event.data.object = {
            "customer": "cus_inv",
            "subscription": "sub_inv",
            "period_start": 1700000000,
        }

        from src.api.routers.webhooks import process_stripe_event

        await process_stripe_event(
            event, mock_repo, mock_stripe_client, mock_settings,
            mock_credit_service, mock_credit_settings,
        )

        mock_credit_service.grant_commit_credits_for_period.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_price_raises_price_quarantined(
        self,
        mock_repo: MagicMock,
        mock_stripe_client: MagicMock,
        mock_settings: MagicMock,
        mock_credit_service: MagicMock,
        mock_credit_settings: MagicMock,
    ) -> None:
        """Unknown price in checkout raises PriceQuarantined through process_stripe_event."""
        user = _make_user()
        mock_repo.create_user = AsyncMock(return_value=user)

        # Make stripe return a subscription with unknown price
        sub_mock = MagicMock()
        sub_mock.status = "active"
        sub_mock.current_period_start = 1700000000
        sub_mock.current_period_end = 1702592000
        sub_mock.items.data = [MagicMock(price=MagicMock(id="price_unknown"))]
        mock_stripe_client.v1.subscriptions.retrieve_async = AsyncMock(return_value=sub_mock)

        event = MagicMock()
        event.type = "checkout.session.completed"
        event.id = "evt_quarantine"
        event.data.object = {
            "customer": "cus_q",
            "subscription": "sub_q",
            "customer_email": "user@example.com",
        }

        from src.api.routers.webhooks import process_stripe_event

        with pytest.raises(PriceQuarantined):
            await process_stripe_event(
                event, mock_repo, mock_stripe_client, mock_settings,
                mock_credit_service, mock_credit_settings,
            )
