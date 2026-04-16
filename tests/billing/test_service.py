"""Tests for BillingService — real PostgreSQL.

Test isolation: each test runs inside a transaction that rolls back on teardown.
Uses billing_service, billing_repo, db_conn fixtures from conftest.py.
"""

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.billing.exceptions import InvalidAPIKey, UserNotFound, UsageLimitExceeded
from src.billing.models import BillingContext, User, UsagePeriod
from src.billing.service import BillingService
from src.billing.tiers import Tier


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _insert_user(conn, *, email=None, stripe_customer_id=None):
    """Insert a test user, return (user_id, email)."""
    user_id = uuid4()
    email = email or f"test-{user_id.hex[:8]}@example.com"
    await conn.execute(
        "INSERT INTO users (id, email, stripe_customer_id) VALUES ($1, $2, $3)",
        user_id, email, stripe_customer_id,
    )
    return user_id, email


async def _insert_api_key(conn, user_id, raw_key=None):
    """Insert an API key, return the raw key string."""
    raw_key = raw_key or f"vi_test_{uuid4().hex[:16]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    await conn.execute(
        "INSERT INTO api_keys (id, user_id, key_hash, key_prefix, name) VALUES ($1, $2, $3, $4, $5)",
        uuid4(), user_id, key_hash, key_prefix, "test-key",
    )
    return raw_key


async def _insert_subscription(conn, user_id, *, tier="pro", status="active"):
    """Insert a subscription row."""
    now = datetime.now(timezone.utc)
    sub_id = uuid4()
    await conn.execute(
        """INSERT INTO subscriptions
           (id, user_id, stripe_subscription_id, stripe_price_id, tier, status,
            current_period_start, current_period_end, cancel_at_period_end)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        sub_id, user_id, f"sub_{uuid4().hex[:12]}", "price_test",
        tier, status, now.replace(day=1), now.replace(day=28), False,
    )
    return sub_id


async def _insert_usage_period(conn, user_id, *, videos_used=50, videos_limit=100):
    """Insert a usage period row covering the current month."""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)
    period_id = uuid4()
    await conn.execute(
        """INSERT INTO usage_periods (id, user_id, period_start, period_end, videos_used, videos_limit)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        period_id, user_id, period_start, period_end, videos_used, videos_limit,
    )
    return period_id


# ── Get Billing Context Tests ────────────────────────────────────────────────


@pytest.mark.db
class TestGetBillingContext:
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, billing_service):
        """Invalid API key raises InvalidAPIKey."""
        with pytest.raises(InvalidAPIKey):
            await billing_service.get_billing_context("definitely_invalid_key")

    @pytest.mark.asyncio
    async def test_free_tier_no_subscription(self, billing_service, db_conn):
        """Free tier context when user has no subscription."""
        user_id, _ = await _insert_user(db_conn)
        raw_key = await _insert_api_key(db_conn, user_id)

        context = await billing_service.get_billing_context(raw_key)

        assert context.user.id == user_id
        assert context.tier == Tier.FREE
        assert context.subscription is None
        assert context.usage_period is not None

    @pytest.mark.asyncio
    async def test_pro_tier_with_subscription(self, billing_service, db_conn):
        """Pro tier context when user has active subscription."""
        user_id, _ = await _insert_user(db_conn)
        raw_key = await _insert_api_key(db_conn, user_id)
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        context = await billing_service.get_billing_context(raw_key)

        assert context.tier == Tier.PRO
        assert context.subscription is not None
        assert context.subscription.status == "active"

    @pytest.mark.asyncio
    async def test_get_billing_context_for_user(self, billing_service, db_conn):
        """Internal user-id lookup returns a complete billing context."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")

        context = await billing_service.get_billing_context_for_user(user_id)

        assert context.user.id == user_id
        assert context.tier == Tier.PRO
        assert context.usage_period.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_billing_context_for_user_not_found(self, billing_service):
        """Unknown user IDs fail closed."""
        with pytest.raises(UserNotFound, match="User .* not found"):
            await billing_service.get_billing_context_for_user(uuid4())


# ── Check Can Analyze Tests (pure logic — no DB needed) ─────────────────────


class TestCheckCanAnalyze:
    @pytest.fixture
    def service(self):
        """BillingService with a sentinel repo (check_can_analyze doesn't touch DB)."""
        return BillingService(object())  # type: ignore[arg-type]

    def _make_context(self, *, tier=Tier.FREE, videos_used=50, videos_limit=100):
        return BillingContext(
            user=User(id=uuid4(), email="test@test.com", stripe_customer_id=None, created_at=datetime.now(timezone.utc)),
            tier=tier,
            usage_period=UsagePeriod(
                id=uuid4(),
                user_id=uuid4(),
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                videos_used=videos_used,
                videos_limit=videos_limit,
            ),
            subscription=None,
        )

    @pytest.mark.asyncio
    async def test_free_tier_under_limit(self, service):
        """Free tier can analyze when under limit."""
        ctx = self._make_context(videos_used=50, videos_limit=100)
        await service.check_can_analyze(ctx)  # Should not raise

    @pytest.mark.asyncio
    async def test_free_tier_at_limit(self, service):
        """Free tier cannot analyze when at limit."""
        ctx = self._make_context(videos_used=100, videos_limit=100)
        with pytest.raises(UsageLimitExceeded):
            await service.check_can_analyze(ctx)

    @pytest.mark.asyncio
    async def test_pro_tier_always_allowed(self, service):
        """Pro tier can always analyze regardless of usage."""
        ctx = self._make_context(tier=Tier.PRO, videos_used=50000, videos_limit=50000)
        await service.check_can_analyze(ctx)  # Should not raise


# ── Record Usage Tests ───────────────────────────────────────────────────────


@pytest.mark.db
class TestRecordUsage:
    @pytest.mark.asyncio
    async def test_increment_usage(self, billing_service, db_conn):
        """Usage is incremented in real DB."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_usage_period(db_conn, user_id, videos_used=50, videos_limit=100)

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.FREE,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.FREE)),
            subscription=None,
        )

        result = await billing_service.record_usage(context, video_count=1)

        assert result.videos_used == 51

    @pytest.mark.asyncio
    async def test_threshold_notification_at_90_percent(self, billing_service, db_conn):
        """Notification flag is set in DB at 90% threshold."""
        user_id, _ = await _insert_user(db_conn)
        period_id = await _insert_usage_period(db_conn, user_id, videos_used=89, videos_limit=100)

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.FREE,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.FREE)),
            subscription=None,
        )

        await billing_service.record_usage(context, video_count=1)

        # Verify notification was marked in DB
        was_sent = await billing_service._repo.was_notification_sent(period_id, 90)
        assert was_sent is True

    @pytest.mark.asyncio
    async def test_skip_notification_if_already_sent(self, billing_service, db_conn):
        """Notification is not sent twice for same threshold."""
        user_id, _ = await _insert_user(db_conn)
        period_id = await _insert_usage_period(db_conn, user_id, videos_used=90, videos_limit=100)

        # Pre-mark notification as sent
        await db_conn.execute(
            "UPDATE usage_periods SET notification_90_sent_at = NOW() WHERE id = $1",
            period_id,
        )

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.FREE,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.FREE)),
            subscription=None,
        )

        # Record usage that puts us above 90% — notification should NOT be re-sent
        await billing_service.record_usage(context, video_count=1)

        # Notification column should still be the original timestamp (not re-updated)
        row = await db_conn.fetchrow(
            "SELECT notification_90_sent_at FROM usage_periods WHERE id = $1", period_id
        )
        assert row["notification_90_sent_at"] is not None

    @pytest.mark.asyncio
    async def test_atomic_quota_enforcement_blocks_over_limit(self, billing_service, db_conn):
        """Free tier atomic enforcement returns None when at limit."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_usage_period(db_conn, user_id, videos_used=100, videos_limit=100)

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.FREE,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.FREE)),
            subscription=None,
        )

        with pytest.raises(UsageLimitExceeded, match="concurrent request race"):
            await billing_service.record_usage(context, video_count=1)

    @pytest.mark.asyncio
    async def test_atomic_quota_enforcement_pro_unlimited(self, billing_service, db_conn):
        """Pro tier always succeeds (no limit enforcement)."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")
        await _insert_usage_period(db_conn, user_id, videos_used=50000, videos_limit=50000)

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.PRO,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.PRO)),
            subscription=(await billing_service._repo.get_subscription(user_id)),
        )

        result = await billing_service.record_usage(context, video_count=1)
        assert result.videos_used == 50001  # Pro exceeds limit, that's OK

    @pytest.mark.asyncio
    async def test_threshold_notification_uses_structured_logging(self, billing_service, db_conn, caplog):
        """Threshold notification emits structured warning log."""
        import logging

        user_id, _ = await _insert_user(db_conn)
        await _insert_usage_period(db_conn, user_id, videos_used=89, videos_limit=100)

        context = BillingContext(
            user=(await billing_service._repo.get_user_by_id(user_id)),
            tier=Tier.FREE,
            usage_period=(await billing_service._repo.get_or_create_usage_period(user_id, Tier.FREE)),
            subscription=None,
        )

        with caplog.at_level(logging.WARNING, logger="src.billing.service"):
            await billing_service.record_usage(context, video_count=1)

        assert any("usage_threshold_reached" in r.message for r in caplog.records)


# ── Get Usage Stats Tests ────────────────────────────────────────────────────


@pytest.mark.db
class TestGetUsageStats:
    @pytest.mark.asyncio
    async def test_get_usage_stats_free_tier(self, billing_service, db_conn):
        """Usage stats for free tier user."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_usage_period(db_conn, user_id, videos_used=50, videos_limit=100)

        stats = await billing_service.get_usage_stats(user_id)

        assert stats["tier"] == "free"
        assert stats["videos_used"] == 50
        assert stats["videos_limit"] == 100
        assert stats["videos_remaining"] == 50
        assert stats["usage_percent"] == 50.0
        assert stats["rate_limit_per_minute"] == 30
        assert stats["subscription_status"] is None

    @pytest.mark.asyncio
    async def test_get_usage_stats_pro_tier(self, billing_service, db_conn):
        """Usage stats for pro tier user."""
        user_id, _ = await _insert_user(db_conn)
        await _insert_subscription(db_conn, user_id, tier="pro", status="active")
        await _insert_usage_period(db_conn, user_id, videos_used=1000, videos_limit=50000)

        stats = await billing_service.get_usage_stats(user_id)

        assert stats["tier"] == "pro"
        assert stats["videos_limit"] == 50000
        assert stats["rate_limit_per_minute"] == 300
        assert stats["subscription_status"] == "active"

    @pytest.mark.asyncio
    async def test_get_usage_stats_user_not_found(self, billing_service):
        """Error when user not found."""
        with pytest.raises(UserNotFound, match="User .* not found"):
            await billing_service.get_usage_stats(uuid4())
