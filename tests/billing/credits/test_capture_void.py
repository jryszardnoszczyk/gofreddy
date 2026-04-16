"""Tests for capture and void — state transitions and idempotency."""

from uuid import uuid4

import pytest

from src.billing.credits.exceptions import InvalidReservationState
from src.billing.credits.models import BillableEvent


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
class TestCaptureUsage:
    @pytest.mark.asyncio
    async def test_capture_happy_path(self, credit_service, credit_repo, test_user):
        """Authorize -> capture -> reservation='captured', balance decremented."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        event = await credit_service.capture_usage(res.id)

        assert isinstance(event, BillableEvent)
        assert event.units == 3
        assert event.user_id == test_user["id"]
        assert event.reservation_id == res.id

        # Balance should be debited and reserved_total cleared
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.topup_remaining == 7  # 10 - 3
        assert bal.reserved_total == 0

    @pytest.mark.asyncio
    async def test_capture_partial(self, credit_service, credit_repo, test_user):
        """Reserve 4, capture 1 -> debit 1, reserved_total decremented by 4."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=4,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        event = await credit_service.capture_usage(res.id, units_captured=1)

        assert event.units == 1

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.topup_remaining == 9  # 10 - 1
        assert bal.reserved_total == 0  # released 4 from reserved

    @pytest.mark.asyncio
    async def test_capture_defaults_to_units_reserved(
        self, credit_service, credit_repo, test_user
    ):
        """units_captured=None -> captures full reserved amount."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=5,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        event = await credit_service.capture_usage(res.id, units_captured=None)

        assert event.units == 5
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.topup_remaining == 5

    @pytest.mark.asyncio
    async def test_capture_idempotent(self, credit_service, credit_repo, test_user):
        """Double capture -> second returns None (idempotent no-op)."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        event1 = await credit_service.capture_usage(res.id)
        event2 = await credit_service.capture_usage(res.id)

        assert event1 is not None
        # Second capture returns the existing event (idempotent)
        assert event2 is not None
        assert event2.id == event1.id

    @pytest.mark.asyncio
    async def test_capture_voided_reservation_raises(
        self, credit_service, credit_repo, test_user
    ):
        """Capture after void -> InvalidReservationState."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.void_usage(res.id)

        with pytest.raises(InvalidReservationState, match="voided"):
            await credit_service.capture_usage(res.id)

    @pytest.mark.asyncio
    async def test_capture_expired_reservation_raises(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Capture after cleanup expiry -> InvalidReservationState."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        # Force expire by setting expires_at in the past
        await db_conn.execute(
            "UPDATE usage_reservations SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = $1",
            res.id,
        )
        await credit_service.void_expired_reservations()

        with pytest.raises(InvalidReservationState, match="expired"):
            await credit_service.capture_usage(res.id)

    @pytest.mark.asyncio
    async def test_capture_units_exceeds_reserved_raises(
        self, credit_service, credit_repo, test_user
    ):
        """units_captured > units_reserved -> ValueError."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        with pytest.raises(ValueError, match="units_captured"):
            await credit_service.capture_usage(res.id, units_captured=5)


@pytest.mark.db
class TestVoidUsage:
    @pytest.mark.asyncio
    async def test_void_happy_path(self, credit_service, credit_repo, test_user):
        """Authorize -> void -> reservation='voided', reserved_total decremented."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.void_usage(res.id)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.topup_remaining == 10  # untouched
        assert bal.reserved_total == 0

        # Verify reservation status
        reservation = await credit_repo.get_reservation(res.id)
        assert reservation.status == "voided"
        assert reservation.voided_at is not None

    @pytest.mark.asyncio
    async def test_void_idempotent(self, credit_service, credit_repo, test_user):
        """Double void -> second is no-op (no exception, no balance change)."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.void_usage(res.id)
        # Second void — no exception
        await credit_service.void_usage(res.id)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.reserved_total == 0

    @pytest.mark.asyncio
    async def test_void_captured_raises(self, credit_service, credit_repo, test_user):
        """Void after capture -> InvalidReservationState."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.capture_usage(res.id)

        with pytest.raises(InvalidReservationState, match="captured"):
            await credit_service.void_usage(res.id)

    @pytest.mark.asyncio
    async def test_void_expired_raises(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Void after cleanup expiry -> InvalidReservationState."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        # Force expire
        await db_conn.execute(
            "UPDATE usage_reservations SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = $1",
            res.id,
        )
        await credit_service.void_expired_reservations()

        with pytest.raises(InvalidReservationState, match="expired"):
            await credit_service.void_usage(res.id)
