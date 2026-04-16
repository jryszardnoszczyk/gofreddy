"""Tests for credit billing domain models."""

import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.billing.credits.models import CreditBalance, CreditLedgerEntry


class TestCreditBalance:
    def test_available_all_positive(self):
        bal = CreditBalance(
            user_id=uuid4(),
            promo_remaining=10,
            included_remaining=20,
            topup_remaining=30,
            reserved_total=0,
            updated_at=datetime.now(timezone.utc),
        )
        assert bal.available == 60

    def test_available_with_reserved(self):
        bal = CreditBalance(
            user_id=uuid4(),
            promo_remaining=10,
            included_remaining=20,
            topup_remaining=30,
            reserved_total=15,
            updated_at=datetime.now(timezone.utc),
        )
        assert bal.available == 45

    def test_available_zero_balance(self):
        bal = CreditBalance(
            user_id=uuid4(),
            promo_remaining=0,
            included_remaining=0,
            topup_remaining=0,
            reserved_total=0,
            updated_at=datetime.now(timezone.utc),
        )
        assert bal.available == 0


class TestCreditLedgerEntry:
    def test_frozen_immutable(self):
        entry = CreditLedgerEntry(
            id=uuid4(),
            user_id=uuid4(),
            entry_type="grant",
            credit_bucket="topup",
            units=10,
            source_type="stripe_checkout",
            source_id="cs_test_123",
            expires_at=None,
            metadata_json=None,
            created_at=datetime.now(timezone.utc),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            entry.units = 20  # type: ignore[misc]

    def test_all_fields(self):
        uid = uuid4()
        entry = CreditLedgerEntry(
            id=uid,
            user_id=uid,
            entry_type="grant",
            credit_bucket="promo",
            units=50,
            source_type="admin",
            source_id="promo_2026_q1",
            expires_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            metadata_json={"campaign": "launch"},
            created_at=datetime.now(timezone.utc),
        )
        assert entry.id == uid
        assert entry.entry_type == "grant"
        assert entry.credit_bucket == "promo"
        assert entry.units == 50
        assert entry.expires_at is not None
        assert entry.metadata_json == {"campaign": "launch"}
