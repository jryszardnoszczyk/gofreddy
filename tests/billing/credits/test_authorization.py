"""Tests for authorize_usage — reservation creation and balance locking."""

from uuid import uuid4

import pytest

from src.billing.credits.exceptions import InsufficientCredits, InvalidReservationState
from src.billing.credits.models import UsageReservation


async def _grant_credits(credit_repo, user_id, *, promo=0, included=0, topup=0):
    """Helper: grant credits to a user across buckets."""
    if promo > 0:
        await credit_repo.grant_with_balance_update(
            user_id=user_id,
            entry_type="grant",
            credit_bucket="promo",
            units=promo,
            source_type="test",
            source_id=f"test_promo_{uuid4().hex[:8]}",
        )
    if included > 0:
        await credit_repo.grant_with_balance_update(
            user_id=user_id,
            entry_type="grant",
            credit_bucket="included",
            units=included,
            source_type="test",
            source_id=f"test_incl_{uuid4().hex[:8]}",
        )
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
class TestAuthorizeUsage:
    @pytest.mark.asyncio
    async def test_authorize_creates_reservation(self, credit_service, credit_repo, test_user):
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        reservation = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        assert isinstance(reservation, UsageReservation)
        assert reservation.status == "reserved"
        assert reservation.units_reserved == 3
        assert reservation.user_id == test_user["id"]

        # reserved_total should be incremented
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.reserved_total == 3

    @pytest.mark.asyncio
    async def test_authorize_insufficient_credits(self, credit_service, credit_repo, test_user):
        await _grant_credits(credit_repo, test_user["id"], topup=2)

        with pytest.raises(InsufficientCredits):
            await credit_service.authorize_usage(
                user_id=test_user["id"],
                units=5,
                source_type="analysis",
                source_id=f"analysis_{uuid4().hex[:8]}",
            )

    @pytest.mark.asyncio
    async def test_authorize_no_balance_row(self, credit_service, test_user):
        """User with no credit_balances row -> InsufficientCredits."""
        with pytest.raises(InsufficientCredits):
            await credit_service.authorize_usage(
                user_id=test_user["id"],
                units=1,
                source_type="analysis",
                source_id=f"analysis_{uuid4().hex[:8]}",
            )

    @pytest.mark.asyncio
    async def test_authorize_idempotent_retry(self, credit_service, credit_repo, test_user):
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        source_id = f"analysis_{uuid4().hex[:8]}"
        res1 = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=source_id,
        )
        # Same source key -> returns existing reservation
        res2 = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=source_id,
        )
        assert res1.id == res2.id
        # reserved_total should NOT double
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.reserved_total == 3

    @pytest.mark.asyncio
    async def test_authorize_idempotent_terminal_state(
        self, credit_service, credit_repo, test_user
    ):
        """Retry with source key of captured reservation -> InvalidReservationState."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        source_id = f"analysis_{uuid4().hex[:8]}"
        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=source_id,
        )
        # Capture it
        await credit_service.capture_usage(res.id)

        # Now retry authorize with same key -> InvalidReservationState
        with pytest.raises(InvalidReservationState):
            await credit_service.authorize_usage(
                user_id=test_user["id"],
                units=3,
                source_type="analysis",
                source_id=source_id,
            )

    @pytest.mark.asyncio
    async def test_authorize_validation_units_zero(self, credit_service, test_user):
        with pytest.raises(ValueError, match="units must be >= 1"):
            await credit_service.authorize_usage(
                user_id=test_user["id"],
                units=0,
                source_type="analysis",
                source_id=f"analysis_{uuid4().hex[:8]}",
            )

    @pytest.mark.asyncio
    async def test_authorize_custom_ttl(self, credit_service, credit_repo, test_user):
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        reservation = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=1,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
            ttl_minutes=30,
        )
        # Verify expires_at is roughly 30 min from now
        from datetime import datetime, timezone

        delta = reservation.expires_at - datetime.now(timezone.utc)
        assert 29 * 60 <= delta.total_seconds() <= 31 * 60

    @pytest.mark.asyncio
    async def test_authorize_default_ttl(self, credit_service, credit_repo, test_user):
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        reservation = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=1,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        # Default is sync_reservation_ttl_minutes=15
        from datetime import datetime, timezone

        delta = reservation.expires_at - datetime.now(timezone.utc)
        assert 14 * 60 <= delta.total_seconds() <= 16 * 60
