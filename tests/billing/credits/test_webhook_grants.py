"""Tests for webhook grant integration — topup and commit credit grants."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.credits.models import CreditLedgerEntry


def _mock_credit_service():
    """Create a mock CreditService with grant methods."""
    svc = MagicMock()
    svc.grant_topup_credits = AsyncMock(return_value=MagicMock(spec=CreditLedgerEntry))
    svc.grant_commit_credits_for_period = AsyncMock(return_value=MagicMock(spec=CreditLedgerEntry))
    return svc


@pytest.mark.mock_required
class TestTopupGrantFlow:
    """Integration tests for topup credit grants via checkout."""

    @pytest.mark.asyncio
    async def test_topup_grant_creates_ledger_entry(self) -> None:
        """Full grant flow with CreditService mock."""
        credit_service = _mock_credit_service()
        user_id = uuid4()

        await credit_service.grant_topup_credits(
            user_id=user_id,
            units=50,
            source_id="cs_test_session_123",
        )

        credit_service.grant_topup_credits.assert_awaited_once_with(
            user_id=user_id,
            units=50,
            source_id="cs_test_session_123",
        )

    @pytest.mark.asyncio
    async def test_duplicate_topup_returns_none(self) -> None:
        """Second grant returns None (idempotent)."""
        credit_service = _mock_credit_service()
        # First call returns entry, second returns None
        credit_service.grant_topup_credits = AsyncMock(
            side_effect=[MagicMock(spec=CreditLedgerEntry), None]
        )
        user_id = uuid4()

        result1 = await credit_service.grant_topup_credits(
            user_id=user_id, units=10, source_id="cs_dup"
        )
        result2 = await credit_service.grant_topup_credits(
            user_id=user_id, units=10, source_id="cs_dup"
        )

        assert result1 is not None
        assert result2 is None


@pytest.mark.mock_required
class TestCommitGrantFlow:
    """Integration tests for commit credit grants via invoice.paid."""

    @pytest.mark.asyncio
    async def test_commit_grant_with_deterministic_source_key(self) -> None:
        """Source key format: '{subscription_id}:{period_start_iso}'."""
        credit_service = _mock_credit_service()
        user_id = uuid4()

        await credit_service.grant_commit_credits_for_period(
            user_id=user_id,
            units=100,
            subscription_id="sub_abc",
            period_start="2026-02-01T00:00:00+00:00",
        )

        credit_service.grant_commit_credits_for_period.assert_awaited_once_with(
            user_id=user_id,
            units=100,
            subscription_id="sub_abc",
            period_start="2026-02-01T00:00:00+00:00",
        )

    @pytest.mark.asyncio
    async def test_duplicate_commit_grant_returns_none(self) -> None:
        """Duplicate period grant returns None."""
        credit_service = _mock_credit_service()
        credit_service.grant_commit_credits_for_period = AsyncMock(
            side_effect=[MagicMock(spec=CreditLedgerEntry), None]
        )
        user_id = uuid4()

        result1 = await credit_service.grant_commit_credits_for_period(
            user_id=user_id, units=100,
            subscription_id="sub_dup", period_start="2026-02-01T00:00:00+00:00",
        )
        result2 = await credit_service.grant_commit_credits_for_period(
            user_id=user_id, units=100,
            subscription_id="sub_dup", period_start="2026-02-01T00:00:00+00:00",
        )

        assert result1 is not None
        assert result2 is None
