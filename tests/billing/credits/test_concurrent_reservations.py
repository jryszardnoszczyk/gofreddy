"""Tests for concurrent reservation safety — SELECT FOR UPDATE locking."""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio

from src.billing.credits import CreditRepository, CreditService, CreditSettings
from src.billing.credits.exceptions import InsufficientCredits, InvalidReservationState


@pytest_asyncio.fixture
async def pool_user(db_pool):
    """Create a test user committed via pool (visible to all connections).

    Concurrent tests need the real pool, not SingleConnectionPool. The
    standard test_user fixture uses db_conn (rolled-back transaction)
    which is invisible to other pool connections.
    """
    user_id = uuid4()
    email = f"test-concurrent-{user_id.hex[:8]}@test.com"
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (id, email) VALUES ($1, $2)",
            user_id, email,
        )
    yield {"id": user_id, "email": email}
    # Cleanup after test — credit_ledger has immutability trigger (no DELETE),
    # so we temporarily disable triggers for the cleanup.
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SET LOCAL session_replication_role = 'replica'")
            await conn.execute("DELETE FROM billable_events WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM credit_ledger WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM usage_reservations WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM credit_balances WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest.mark.db
class TestConcurrentReservations:
    @pytest.mark.asyncio
    async def test_concurrent_authorize_one_wins(self, db_pool, pool_user):
        """Two concurrent authorizes for same user (balance=3, each wants 3).

        One succeeds, one gets InsufficientCredits. SELECT FOR UPDATE
        ensures serialization — no double-spend.
        """
        repo = CreditRepository(db_pool)
        service = CreditService(repository=repo, settings=CreditSettings())

        await repo.grant_with_balance_update(
            user_id=pool_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=3,
            source_type="test",
            source_id=f"test_top_{uuid4().hex[:8]}",
        )

        async def try_authorize(n: int):
            return await service.authorize_usage(
                user_id=pool_user["id"],
                units=3,
                source_type="analysis",
                source_id=f"concurrent_{uuid4().hex[:8]}_{n}",
            )

        results = await asyncio.gather(
            try_authorize(1),
            try_authorize(2),
            return_exceptions=True,
        )

        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, InsufficientCredits)]

        assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
        assert len(failures) == 1, f"Expected exactly 1 failure, got {len(failures)}"

        bal = await repo.get_balance(pool_user["id"])
        assert bal is not None
        assert bal.topup_remaining == 3
        assert bal.reserved_total == 3
        assert bal.available == 0

    @pytest.mark.asyncio
    async def test_concurrent_captures_dont_corrupt_balance(
        self, db_pool, pool_user
    ):
        """Two captures for different reservations, same user.

        Both succeed, balance correctly reflects both debits.
        """
        repo = CreditRepository(db_pool)
        service = CreditService(repository=repo, settings=CreditSettings())

        await repo.grant_with_balance_update(
            user_id=pool_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="test",
            source_id=f"test_top_{uuid4().hex[:8]}",
        )

        res1 = await service.authorize_usage(
            user_id=pool_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}_a",
        )
        res2 = await service.authorize_usage(
            user_id=pool_user["id"],
            units=2,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}_b",
        )

        results = await asyncio.gather(
            service.capture_usage(res1.id),
            service.capture_usage(res2.id),
        )

        assert all(r is not None for r in results)

        bal = await repo.get_balance(pool_user["id"])
        assert bal is not None
        assert bal.topup_remaining == 5  # 10 - 3 - 2
        assert bal.reserved_total == 0  # Both released

    @pytest.mark.asyncio
    async def test_cleanup_and_capture_race(self, db_pool, pool_user):
        """Cleanup expires reservation, then capture arrives.

        Capture gets InvalidReservationState (expired reservation can't be captured).
        """
        repo = CreditRepository(db_pool)
        service = CreditService(repository=repo, settings=CreditSettings())

        await repo.grant_with_balance_update(
            user_id=pool_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="test",
            source_id=f"test_top_{uuid4().hex[:8]}",
        )

        res = await service.authorize_usage(
            user_id=pool_user["id"],
            units=3,
            source_type="analysis",
            source_id=f"analysis_{uuid4().hex[:8]}",
        )

        # Force expire via raw SQL on the pool
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE usage_reservations SET expires_at = NOW() - INTERVAL '1 hour' WHERE id = $1",
                res.id,
            )

        # Run cleanup first
        await service.void_expired_reservations()

        # Now try to capture — should fail with InvalidReservationState
        with pytest.raises(InvalidReservationState, match="expired"):
            await service.capture_usage(res.id)
