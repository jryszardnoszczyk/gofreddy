"""Tests for expired reservation cleanup — batch processing and status transitions."""

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


async def _create_expired_reservation(credit_service, db_conn, user_id, units=1):
    """Create a reservation then force-expire it via DB."""
    res = await credit_service.authorize_usage(
        user_id=user_id,
        units=units,
        source_type="analysis",
        source_id=f"analysis_{uuid4().hex[:8]}",
    )
    await db_conn.execute(
        "UPDATE usage_reservations SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = $1",
        res.id,
    )
    return res


@pytest.mark.db
class TestCleanupJob:
    @pytest.mark.asyncio
    async def test_cleanup_expires_stale_reservations(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Reservations past expires_at -> status='expired', reserved_total decremented."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await _create_expired_reservation(
            credit_service, db_conn, test_user["id"], units=3
        )

        count = await credit_service.void_expired_reservations()
        assert count == 1

        reservation = await credit_repo.get_reservation(res.id)
        assert reservation.status == "expired"

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.reserved_total == 0
        assert bal.topup_remaining == 10  # Credits released, not debited

    @pytest.mark.asyncio
    async def test_cleanup_skips_non_expired(
        self, credit_service, credit_repo, test_user
    ):
        """Future expires_at -> not touched."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )

        count = await credit_service.void_expired_reservations()
        assert count == 0

        reservation = await credit_repo.get_reservation(res.id)
        assert reservation.status == "reserved"

    @pytest.mark.asyncio
    async def test_cleanup_skips_captured_and_voided(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Already terminal reservations are not touched."""
        await _grant_credits(credit_repo, test_user["id"], topup=20)

        # Create and capture one
        res_captured = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=2,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.capture_usage(res_captured.id)

        # Create and void one
        res_voided = await credit_service.authorize_usage(
            user_id=test_user["id"],
            units=2,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )
        await credit_service.void_usage(res_voided.id)

        # Force-expire both (should be ignored since they're terminal)
        await db_conn.execute(
            "UPDATE usage_reservations SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = ANY($1)",
            [res_captured.id, res_voided.id],
        )

        count = await credit_service.void_expired_reservations()
        assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_batch_limit(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """batch_size limits processing — only 100 per run."""
        await _grant_credits(credit_repo, test_user["id"], topup=200)

        # Create 5 expired reservations, run with batch_size=3
        for _ in range(5):
            await _create_expired_reservation(
                credit_service, db_conn, test_user["id"], units=1
            )

        # Call repo directly to test batch_size param
        count = await credit_repo.expire_stale_reservations(batch_size=3)
        assert count == 3

        # Run again — picks up remaining 2
        count2 = await credit_repo.expire_stale_reservations(batch_size=3)
        assert count2 == 2

    @pytest.mark.asyncio
    async def test_cleanup_returns_count(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Return value matches number of expired reservations."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        for _ in range(3):
            await _create_expired_reservation(
                credit_service, db_conn, test_user["id"], units=1
            )

        count = await credit_service.void_expired_reservations()
        assert count == 3

    @pytest.mark.asyncio
    async def test_cleanup_sets_expired_not_voided(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Status after cleanup is 'expired' (not 'voided') for audit distinction."""
        await _grant_credits(credit_repo, test_user["id"], topup=10)

        res = await _create_expired_reservation(
            credit_service, db_conn, test_user["id"], units=2
        )

        await credit_service.void_expired_reservations()

        reservation = await credit_repo.get_reservation(res.id)
        assert reservation.status == "expired"
        # voided_at should NOT be set (expired != voided)
        assert reservation.voided_at is None
