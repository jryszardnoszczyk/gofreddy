"""Billing module for usage tracking and subscription management."""

from .config import StripeSettings
from .exceptions import (
    BillingError,
    FeatureNotAvailable,
    InvalidAPIKey,
    UserNotFound,
    UsageLimitExceeded,
)
from .models import APIKey, BillingContext, Subscription, UsagePeriod, User
from .repository import BillingRepository
from .service import BillingService
# credits/ subdir not ported in gofreddy — storyboard lane doesn't use it.
from .tiers import Tier, TierConfig, get_tier_config, is_paid_tier

__all__ = [
    # Config
    "StripeSettings",
    # Tiers
    "Tier",
    "TierConfig",
    "get_tier_config",
    "is_paid_tier",
    # Models
    "User",
    "APIKey",
    "Subscription",
    "UsagePeriod",
    "BillingContext",
    # Repository
    "BillingRepository",
    # Service
    "BillingService",
    # Exceptions
    "BillingError",
    "InvalidAPIKey",
    "UserNotFound",
    "UsageLimitExceeded",
    "FeatureNotAvailable",
]
