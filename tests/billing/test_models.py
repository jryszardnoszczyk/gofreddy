"""Tests for billing models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.billing.models import APIKey, BillingContext, Subscription, UsagePeriod, User
from src.billing.tiers import Tier


class TestUser:
    """Tests for User model."""

    def test_user_creation(self):
        """Test creating user model."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            stripe_customer_id="cus_123",
            created_at=datetime.now(timezone.utc),
        )
        assert user.email == "test@example.com"
        assert user.stripe_customer_id == "cus_123"

    def test_user_no_stripe_customer(self):
        """Test user without Stripe customer ID."""
        user = User(
            id=uuid4(),
            email="free@example.com",
            stripe_customer_id=None,
            created_at=datetime.now(timezone.utc),
        )
        assert user.stripe_customer_id is None

    def test_user_frozen(self):
        """Test user is immutable."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            stripe_customer_id=None,
            created_at=datetime.now(timezone.utc),
        )
        with pytest.raises(AttributeError):
            user.email = "new@example.com"  # type: ignore


class TestAPIKey:
    """Tests for APIKey model."""

    def test_api_key_creation(self):
        """Test creating API key model."""
        key = APIKey(
            id=uuid4(),
            user_id=uuid4(),
            key_prefix="vi_sk_test",
            name="Test Key",
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            expires_at=None,
            is_active=True,
        )
        assert key.key_prefix == "vi_sk_test"
        assert key.is_active is True

    def test_api_key_revoked(self):
        """Test revoked API key."""
        key = APIKey(
            id=uuid4(),
            user_id=uuid4(),
            key_prefix="vi_sk_rev",
            name="Revoked Key",
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            expires_at=None,
            is_active=False,
        )
        assert key.is_active is False


class TestSubscription:
    """Tests for Subscription model."""

    def test_subscription_creation(self):
        """Test creating subscription model."""
        sub = Subscription(
            id=uuid4(),
            user_id=uuid4(),
            stripe_subscription_id="sub_123",
            tier=Tier.PRO,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
            cancel_at_period_end=False,
        )
        assert sub.tier == Tier.PRO
        assert sub.status == "active"


class TestUsagePeriod:
    """Tests for UsagePeriod model."""

    def test_usage_period_creation(self):
        """Test creating usage period model."""
        period = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=50,
            videos_limit=100,
        )
        assert period.videos_used == 50
        assert period.videos_limit == 100

    def test_videos_remaining(self):
        """Test videos_remaining property."""
        period = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=30,
            videos_limit=100,
        )
        assert period.videos_remaining == 70

    def test_videos_remaining_over_limit(self):
        """Test videos_remaining when over limit."""
        period = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=150,
            videos_limit=100,
        )
        assert period.videos_remaining == 0

    def test_usage_percent(self):
        """Test usage_percent property."""
        period = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=50,
            videos_limit=100,
        )
        assert period.usage_percent == 50.0

    def test_usage_percent_over_100(self):
        """Test usage_percent when over limit."""
        period = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=150,
            videos_limit=100,
        )
        assert period.usage_percent == 150.0

    def test_is_over_limit(self):
        """Test is_over_limit property."""
        under = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=50,
            videos_limit=100,
        )
        assert under.is_over_limit is False

        at_limit = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=100,
            videos_limit=100,
        )
        assert at_limit.is_over_limit is True

        over = UsagePeriod(
            id=uuid4(),
            user_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=150,
            videos_limit=100,
        )
        assert over.is_over_limit is True


class TestBillingContext:
    """Tests for BillingContext model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User(
            id=uuid4(),
            email="test@example.com",
            stripe_customer_id=None,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def usage_period_under(self, user):
        """Create usage period under limit."""
        return UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=50,
            videos_limit=100,
        )

    @pytest.fixture
    def usage_period_at_limit(self, user):
        """Create usage period at limit."""
        return UsagePeriod(
            id=uuid4(),
            user_id=user.id,
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            videos_used=100,
            videos_limit=100,
        )

    def test_free_tier_can_analyze_under_limit(self, user, usage_period_under):
        """Test free tier user can analyze when under limit."""
        context = BillingContext(
            user=user,
            tier=Tier.FREE,
            usage_period=usage_period_under,
            subscription=None,
        )
        assert context.can_analyze is True

    def test_free_tier_cannot_analyze_at_limit(self, user, usage_period_at_limit):
        """Test free tier user cannot analyze when at limit."""
        context = BillingContext(
            user=user,
            tier=Tier.FREE,
            usage_period=usage_period_at_limit,
            subscription=None,
        )
        assert context.can_analyze is False

    def test_pro_tier_can_always_analyze(self, user, usage_period_at_limit):
        """Test pro tier can always analyze."""
        context = BillingContext(
            user=user,
            tier=Tier.PRO,
            usage_period=usage_period_at_limit,
            subscription=None,
        )
        assert context.can_analyze is True
