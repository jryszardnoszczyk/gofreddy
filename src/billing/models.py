"""Billing domain models."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .tiers import Tier


@dataclass(frozen=True, slots=True)
class User:
    """User account."""

    id: UUID
    email: str
    stripe_customer_id: str | None
    created_at: datetime
    supabase_user_id: str | None = None


@dataclass(frozen=True, slots=True)
class APIKey:
    """API key for authentication."""

    id: UUID
    user_id: UUID
    key_prefix: str  # First 12 chars for display
    name: str | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class Subscription:
    """User subscription synced from Stripe."""

    id: UUID
    user_id: UUID
    stripe_subscription_id: str
    tier: Tier
    status: str  # active, past_due, canceled, etc.
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool


@dataclass(frozen=True, slots=True)
class UsagePeriod:
    """Usage tracking for a billing period."""

    id: UUID
    user_id: UUID
    period_start: datetime
    period_end: datetime
    videos_used: int
    videos_limit: int

    @property
    def videos_remaining(self) -> int:
        return max(0, self.videos_limit - self.videos_used)

    @property
    def usage_percent(self) -> float:
        return (self.videos_used / self.videos_limit) * 100 if self.videos_limit > 0 else 0

    @property
    def is_over_limit(self) -> bool:
        return self.videos_used >= self.videos_limit


@dataclass(frozen=True, slots=True)
class BillingContext:
    """Complete billing context for a request."""

    user: User
    tier: Tier
    usage_period: UsagePeriod
    subscription: Subscription | None

    @property
    def can_analyze(self) -> bool:
        """Check if user can perform analysis (within limits)."""
        # Free tier: hard limit
        if self.tier == Tier.FREE:
            return self.usage_period.videos_remaining > 0
        # Pro tier: always allowed (paid tier)
        return True
