"""Tests for ensure_free_tier_credits in CreditService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.credits.models import CreditBalance, CreditLedgerEntry
from src.billing.credits.service import CreditService
from src.billing.tiers import Tier


def _make_credit_service(*, balance_available: int = 0, grant_returns=None):
    """Create a CreditService with mocked repository."""
    repo = AsyncMock()
    repo.get_balance.return_value = CreditBalance(
        user_id=uuid4(),
        promo_remaining=0,
        included_remaining=balance_available,
        topup_remaining=0,
        reserved_total=0,
        updated_at=datetime.now(timezone.utc),
    ) if balance_available > 0 else None
    repo.grant_with_balance_update.return_value = grant_returns

    settings = MagicMock()
    settings.sync_reservation_ttl_minutes = 15
    settings.free_tier_credits_per_period = 200

    return CreditService(repository=repo, settings=settings), repo


@pytest.mark.mock_required
class TestEnsureFreeTierCredits:
    @pytest.mark.asyncio
    async def test_grants_credits_for_free_user_with_zero_balance(self):
        service, repo = _make_credit_service(balance_available=0)
        mock_entry = MagicMock(spec=CreditLedgerEntry)
        repo.grant_with_balance_update.return_value = mock_entry

        result = await service.ensure_free_tier_credits(uuid4(), Tier.FREE)
        assert result is mock_entry
        repo.grant_with_balance_update.assert_awaited_once()
        call_kwargs = repo.grant_with_balance_update.call_args.kwargs
        assert call_kwargs["units"] == 200
        assert call_kwargs["credit_bucket"] == "included"
        assert call_kwargs["source_type"] == "free_tier_monthly"

    @pytest.mark.asyncio
    async def test_skips_pro_users(self):
        service, repo = _make_credit_service(balance_available=0)
        result = await service.ensure_free_tier_credits(uuid4(), Tier.PRO)
        assert result is None
        repo.grant_with_balance_update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_users_with_existing_balance(self):
        service, repo = _make_credit_service(balance_available=100)
        result = await service.ensure_free_tier_credits(uuid4(), Tier.FREE)
        assert result is None
        repo.grant_with_balance_update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_idempotent_via_source_id(self):
        service, repo = _make_credit_service(balance_available=0)
        repo.grant_with_balance_update.return_value = None  # Duplicate = None

        result = await service.ensure_free_tier_credits(uuid4(), Tier.FREE)
        assert result is None  # Duplicate grant returns None
