"""Tests for capture debit precedence — promo -> included -> topup."""

from uuid import uuid4

import pytest

from src.billing.credits.models import CreditLedgerEntry


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


async def _authorize_and_capture(credit_service, user_id, units, units_captured=None):
    """Helper: authorize then capture."""
    source_id = f"analysis_{uuid4().hex[:8]}"
    res = await credit_service.authorize_usage(
        user_id=user_id,
        units=units,
        source_type="analysis",
        source_id=source_id,
    )
    event = await credit_service.capture_usage(res.id, units_captured=units_captured)
    return res, event


@pytest.mark.db
class TestDebitPrecedence:
    @pytest.mark.asyncio
    async def test_capture_debits_promo_first(
        self, credit_service, credit_repo, test_user
    ):
        """User has promo + included + topup -> promo debited first."""
        await _grant_credits(
            credit_repo, test_user["id"], promo=5, included=10, topup=20
        )
        await _authorize_and_capture(credit_service, test_user["id"], units=3)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.promo_remaining == 2  # 5 - 3
        assert bal.included_remaining == 10  # untouched
        assert bal.topup_remaining == 20  # untouched

    @pytest.mark.asyncio
    async def test_capture_debits_included_second(
        self, credit_service, credit_repo, test_user
    ):
        """User has no promo, has included + topup -> included debited."""
        await _grant_credits(credit_repo, test_user["id"], included=10, topup=20)
        await _authorize_and_capture(credit_service, test_user["id"], units=3)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.promo_remaining == 0
        assert bal.included_remaining == 7  # 10 - 3
        assert bal.topup_remaining == 20  # untouched

    @pytest.mark.asyncio
    async def test_capture_debits_topup_last(
        self, credit_service, credit_repo, test_user
    ):
        """User has only topup -> topup debited."""
        await _grant_credits(credit_repo, test_user["id"], topup=20)
        await _authorize_and_capture(credit_service, test_user["id"], units=3)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.promo_remaining == 0
        assert bal.included_remaining == 0
        assert bal.topup_remaining == 17  # 20 - 3

    @pytest.mark.asyncio
    async def test_capture_spans_two_buckets(
        self, credit_service, credit_repo, test_user
    ):
        """Capture 3 credits: promo=1, included=10 -> 1 from promo, 2 from included."""
        await _grant_credits(credit_repo, test_user["id"], promo=1, included=10)
        await _authorize_and_capture(credit_service, test_user["id"], units=3)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.promo_remaining == 0  # 1 - 1
        assert bal.included_remaining == 8  # 10 - 2

    @pytest.mark.asyncio
    async def test_capture_spans_three_buckets(
        self, credit_service, credit_repo, test_user
    ):
        """Capture 6 credits: promo=2, included=2, topup=5 -> 2+2+2."""
        await _grant_credits(
            credit_repo, test_user["id"], promo=2, included=2, topup=5
        )
        await _authorize_and_capture(credit_service, test_user["id"], units=6)

        bal = await credit_repo.get_balance(test_user["id"])
        assert bal.promo_remaining == 0  # 2 - 2
        assert bal.included_remaining == 0  # 2 - 2
        assert bal.topup_remaining == 3  # 5 - 2

    @pytest.mark.asyncio
    async def test_capture_creates_ledger_entries_per_bucket(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Multi-bucket debit -> one credit_ledger entry per bucket."""
        await _grant_credits(
            credit_repo, test_user["id"], promo=1, included=1, topup=5
        )
        res, _ = await _authorize_and_capture(
            credit_service, test_user["id"], units=3
        )

        # Check ledger entries
        rows = await db_conn.fetch(
            """SELECT * FROM credit_ledger
               WHERE entry_type = 'debit' AND user_id = $1
               ORDER BY credit_bucket""",
            test_user["id"],
        )
        buckets = [r["credit_bucket"] for r in rows]
        assert "included" in buckets
        assert "promo" in buckets
        assert "topup" in buckets
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_capture_ledger_source_ids_suffixed(
        self, credit_service, credit_repo, test_user, db_conn
    ):
        """Ledger entries have source_id='{reservation_id}:promo', etc."""
        await _grant_credits(
            credit_repo, test_user["id"], promo=1, included=1, topup=5
        )
        res, _ = await _authorize_and_capture(
            credit_service, test_user["id"], units=3
        )

        rows = await db_conn.fetch(
            """SELECT source_id FROM credit_ledger
               WHERE entry_type = 'debit' AND user_id = $1""",
            test_user["id"],
        )
        source_ids = {r["source_id"] for r in rows}
        assert f"{res.id}:promo" in source_ids
        assert f"{res.id}:included" in source_ids
        assert f"{res.id}:topup" in source_ids
