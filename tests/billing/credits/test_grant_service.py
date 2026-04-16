"""Tests for CreditService grant methods — DB integration tests."""

from uuid import uuid4

import pytest

from src.billing.credits.models import CreditBalance, CreditLedgerEntry


@pytest.mark.db
class TestGrantTopupCredits:
    @pytest.mark.asyncio
    async def test_grant_creates_ledger_entry(self, credit_service, test_user):
        entry = await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=50,
            source_id=f"cs_{uuid4().hex[:12]}",
        )
        assert entry is not None
        assert isinstance(entry, CreditLedgerEntry)
        assert entry.entry_type == "grant"
        assert entry.credit_bucket == "topup"
        assert entry.units == 50
        assert entry.source_type == "stripe_checkout"

    @pytest.mark.asyncio
    async def test_grant_updates_balance(self, credit_service, test_user):
        await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=25,
            source_id=f"cs_{uuid4().hex[:12]}",
        )
        summary = await credit_service.get_billing_summary(test_user["id"])
        assert summary.topup_remaining == 25

    @pytest.mark.asyncio
    async def test_grant_idempotent_duplicate(self, credit_service, test_user):
        source_id = f"cs_{uuid4().hex[:12]}"
        entry1 = await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=50,
            source_id=source_id,
        )
        assert entry1 is not None

        # Duplicate: same source_id
        entry2 = await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=50,
            source_id=source_id,
        )
        assert entry2 is None

        # Balance only reflects first grant
        summary = await credit_service.get_billing_summary(test_user["id"])
        assert summary.topup_remaining == 50

    @pytest.mark.asyncio
    async def test_grant_atomic_ledger_and_balance(self, credit_service, test_user):
        """Both ledger entry and balance update happen atomically."""
        entry = await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=100,
            source_id=f"cs_{uuid4().hex[:12]}",
        )
        assert entry is not None

        summary = await credit_service.get_billing_summary(test_user["id"])
        assert summary.topup_remaining == 100
        assert summary.available == 100

    @pytest.mark.asyncio
    async def test_grant_rejects_negative_units(self, credit_service):
        with pytest.raises(ValueError, match="units must be >= 1"):
            await credit_service.grant_topup_credits(
                user_id=uuid4(),
                units=-5,
                source_id="cs_test",
            )

    @pytest.mark.asyncio
    async def test_grant_rejects_zero_units(self, credit_service):
        with pytest.raises(ValueError, match="units must be >= 1"):
            await credit_service.grant_topup_credits(
                user_id=uuid4(),
                units=0,
                source_id="cs_test",
            )


@pytest.mark.db
class TestGrantCommitCreditsForPeriod:
    @pytest.mark.asyncio
    async def test_grant_creates_ledger_entry(self, credit_service, test_user):
        entry = await credit_service.grant_commit_credits_for_period(
            user_id=test_user["id"],
            units=200,
            subscription_id="sub_test_123",
            period_start="2026-02-01T00:00:00Z",
        )
        assert entry is not None
        assert entry.entry_type == "grant"
        assert entry.credit_bucket == "included"
        assert entry.units == 200
        assert entry.source_type == "subscription_period"

    @pytest.mark.asyncio
    async def test_grant_idempotent_duplicate(self, credit_service, test_user):
        kwargs = {
            "user_id": test_user["id"],
            "units": 200,
            "subscription_id": "sub_test_123",
            "period_start": "2026-02-01T00:00:00Z",
        }
        entry1 = await credit_service.grant_commit_credits_for_period(**kwargs)
        assert entry1 is not None

        entry2 = await credit_service.grant_commit_credits_for_period(**kwargs)
        assert entry2 is None

    @pytest.mark.asyncio
    async def test_source_key_format(self, credit_service, test_user):
        entry = await credit_service.grant_commit_credits_for_period(
            user_id=test_user["id"],
            units=100,
            subscription_id="sub_abc",
            period_start="2026-03-01",
        )
        assert entry is not None
        assert entry.source_id == "sub_abc:2026-03-01"

    @pytest.mark.asyncio
    async def test_grant_rejects_zero_units(self, credit_service):
        with pytest.raises(ValueError, match="units must be >= 1"):
            await credit_service.grant_commit_credits_for_period(
                user_id=uuid4(),
                units=0,
                subscription_id="sub_test",
                period_start="2026-01-01",
            )


@pytest.mark.db
class TestGetBillingSummary:
    @pytest.mark.asyncio
    async def test_returns_balance(self, credit_service, test_user):
        await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=75,
            source_id=f"cs_{uuid4().hex[:12]}",
        )
        summary = await credit_service.get_billing_summary(test_user["id"])
        assert isinstance(summary, CreditBalance)
        assert summary.topup_remaining == 75

    @pytest.mark.asyncio
    async def test_returns_zero_balance_for_new_user(self, credit_service):
        uid = uuid4()
        summary = await credit_service.get_billing_summary(uid)
        assert summary.user_id == uid
        assert summary.promo_remaining == 0
        assert summary.included_remaining == 0
        assert summary.topup_remaining == 0
        assert summary.reserved_total == 0
        assert summary.available == 0

    @pytest.mark.asyncio
    async def test_never_cached(self, credit_service, test_user):
        """Two calls always read from DB — no stale cache."""
        summary1 = await credit_service.get_billing_summary(test_user["id"])
        assert summary1.topup_remaining == 0

        await credit_service.grant_topup_credits(
            user_id=test_user["id"],
            units=42,
            source_id=f"cs_{uuid4().hex[:12]}",
        )

        summary2 = await credit_service.get_billing_summary(test_user["id"])
        assert summary2.topup_remaining == 42
