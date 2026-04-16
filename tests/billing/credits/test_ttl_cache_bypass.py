"""Tests verifying CreditService balance reads bypass BillingService TTLCache."""

from uuid import uuid4

import pytest


async def _grant_credits(credit_repo, user_id, *, topup=0):
    if topup > 0:
        await credit_repo.grant_with_balance_update(
            user_id=user_id,
            entry_type="grant",
            credit_bucket="topup",
            units=topup,
            source_type="test",
            source_id=f"test_top_{uuid4().hex[:8]}",
        )


@pytest.mark.db
class TestTTLCacheBypass:
    @pytest.mark.asyncio
    async def test_credit_service_reads_bypass_billing_cache(
        self, credit_service, credit_repo, test_user
    ):
        """CreditService.get_billing_summary reads from DB, not TTLCache.

        Verify by: insert credits, read via CreditService (fresh),
        insert more, read again (still fresh, no stale cache).
        """
        user_id = test_user["id"]

        # Start with no credits
        bal1 = await credit_service.get_billing_summary(user_id)
        assert bal1.topup_remaining == 0

        # Grant 5 credits
        await _grant_credits(credit_repo, user_id, topup=5)

        # CreditService should see the update immediately (no TTL stale read)
        bal2 = await credit_service.get_billing_summary(user_id)
        assert bal2.topup_remaining == 5

        # Grant 3 more
        await _grant_credits(credit_repo, user_id, topup=3)

        # Still fresh
        bal3 = await credit_service.get_billing_summary(user_id)
        assert bal3.topup_remaining == 8
