"""Tests for CreditRepository — DB integration tests."""

from uuid import uuid4

import asyncpg
import pytest

from src.billing.credits.models import CreditBalance, CreditLedgerEntry
from src.billing.credits.repository import CreditRepository


@pytest.mark.db
class TestCreditRepository:
    @pytest.mark.asyncio
    async def test_insert_ledger_entry(self, credit_repo, test_user):
        entry = await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=50,
            source_type="stripe_checkout",
            source_id=f"cs_{uuid4().hex[:12]}",
        )
        assert entry is not None
        assert isinstance(entry, CreditLedgerEntry)
        assert entry.user_id == test_user["id"]
        assert entry.entry_type == "grant"
        assert entry.credit_bucket == "topup"
        assert entry.units == 50

    @pytest.mark.asyncio
    async def test_insert_duplicate_is_noop(self, credit_repo, test_user):
        source_id = f"cs_{uuid4().hex[:12]}"
        entry1 = await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=50,
            source_type="stripe_checkout",
            source_id=source_id,
        )
        assert entry1 is not None

        # Same source_id -> no-op
        entry2 = await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=100,  # different amount, same key
            source_type="stripe_checkout",
            source_id=source_id,
        )
        assert entry2 is None

    @pytest.mark.asyncio
    async def test_upsert_balance_creates_row(self, credit_repo, test_user):
        # Before grant, no balance row
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal is None

        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=25,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal is not None
        assert bal.topup_remaining == 25
        assert bal.promo_remaining == 0
        assert bal.included_remaining == 0

    @pytest.mark.asyncio
    async def test_upsert_balance_increments(self, credit_repo, test_user):
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=20,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal is not None
        assert bal.topup_remaining == 30

    @pytest.mark.asyncio
    async def test_get_balance_returns_none_for_new_user(self, credit_repo):
        bal = await credit_repo.get_balance(uuid4())
        assert bal is None

    @pytest.mark.asyncio
    async def test_get_balance_returns_row(self, credit_repo, test_user):
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="included",
            units=100,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )
        bal = await credit_repo.get_balance(test_user["id"])
        assert bal is not None
        assert isinstance(bal, CreditBalance)
        assert bal.included_remaining == 100
        assert bal.user_id == test_user["id"]

    @pytest.mark.asyncio
    async def test_ledger_immutability_rejects_update(self, credit_repo, test_user, db_conn):
        entry = await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )
        assert entry is not None

        with pytest.raises(asyncpg.RaiseError, match="append-only"):
            await db_conn.execute(
                "UPDATE credit_ledger SET units = 999 WHERE id = $1",
                entry.id,
            )

    @pytest.mark.asyncio
    async def test_ledger_immutability_rejects_delete(self, credit_repo, test_user, db_conn):
        entry = await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="test",
            source_id=f"test_{uuid4().hex[:8]}",
        )
        assert entry is not None

        with pytest.raises(asyncpg.RaiseError, match="append-only"):
            await db_conn.execute(
                "DELETE FROM credit_ledger WHERE id = $1",
                entry.id,
            )

    @pytest.mark.asyncio
    async def test_invalid_bucket_raises(self, credit_repo, test_user):
        with pytest.raises(ValueError, match="Invalid credit_bucket"):
            await credit_repo.grant_with_balance_update(
                user_id=test_user["id"],
                entry_type="grant",
                credit_bucket="invalid",
                units=10,
                source_type="test",
                source_id=f"test_{uuid4().hex[:8]}",
            )

    @pytest.mark.asyncio
    async def test_get_ledger_entry_by_source(self, credit_repo, test_user):
        source_id = f"cs_{uuid4().hex[:12]}"
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=50,
            source_type="stripe_checkout",
            source_id=source_id,
        )

        entry = await credit_repo.get_ledger_entry_by_source(
            source_type="stripe_checkout",
            source_id=source_id,
        )
        assert entry is not None
        assert entry.source_id == source_id
        assert entry.units == 50

    @pytest.mark.asyncio
    async def test_get_ledger_entry_by_source_not_found(self, credit_repo):
        entry = await credit_repo.get_ledger_entry_by_source(
            source_type="nonexistent",
            source_id="nope",
        )
        assert entry is None

    @pytest.mark.asyncio
    async def test_multiple_buckets_tracked_separately(self, credit_repo, test_user):
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="promo",
            units=5,
            source_type="test",
            source_id=f"test_promo_{uuid4().hex[:8]}",
        )
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="included",
            units=100,
            source_type="test",
            source_id=f"test_incl_{uuid4().hex[:8]}",
        )
        await credit_repo.grant_with_balance_update(
            user_id=test_user["id"],
            entry_type="grant",
            credit_bucket="topup",
            units=50,
            source_type="test",
            source_id=f"test_top_{uuid4().hex[:8]}",
        )

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal is not None
        assert bal.promo_remaining == 5
        assert bal.included_remaining == 100
        assert bal.topup_remaining == 50
        assert bal.available == 155
