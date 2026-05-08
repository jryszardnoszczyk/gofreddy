"""Billing service orchestrating usage tracking and tier management."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from cachetools import TTLCache

from .exceptions import InvalidAPIKey, UserNotFound, UsageLimitExceeded
from .models import BillingContext, UsagePeriod
from .repository import BillingRepository
from .tiers import Tier, get_tier_config

if TYPE_CHECKING:
    import stripe

    from .credits.config import BillingFlags, CreditSettings
    from .credits.service import CreditService

logger = logging.getLogger(__name__)


class BillingService:
    """Service for billing operations."""

    def __init__(
        self,
        repository: BillingRepository,
        billing_flags: BillingFlags | None = None,
        credit_service: CreditService | None = None,
        credit_settings: CreditSettings | None = None,
    ) -> None:
        self._repo = repository
        self._billing_flags = billing_flags
        self._credit_service = credit_service
        self._credit_settings = credit_settings
        self._context_cache: TTLCache[str, BillingContext] = TTLCache(maxsize=256, ttl=10)

    async def get_billing_context(self, api_key: str) -> BillingContext:
        """Get complete billing context for an API request.

        Results are cached for 10s to reduce DB queries under burst traffic.
        """
        cached = self._context_cache.get(api_key)
        if cached is not None:
            return cached

        # Look up user by API key
        user = await self._repo.get_user_by_api_key(api_key)
        if not user:
            raise InvalidAPIKey("Invalid or revoked API key")

        # Get subscription (if any)
        subscription = await self._repo.get_subscription(user.id)
        tier = subscription.tier if subscription else Tier.FREE

        # Get or create usage period
        usage_period = await self._repo.get_or_create_usage_period(user.id, tier)

        context = BillingContext(
            user=user,
            tier=tier,
            usage_period=usage_period,
            subscription=subscription,
        )
        self._context_cache[api_key] = context
        return context

    async def get_billing_context_for_user(self, user_id: UUID) -> BillingContext:
        """Get billing context by user ID (for trusted internal workers)."""
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found")

        subscription = await self._repo.get_subscription(user_id)
        tier = subscription.tier if subscription else Tier.FREE
        usage_period = await self._repo.get_or_create_usage_period(user_id, tier)

        return BillingContext(
            user=user,
            tier=tier,
            usage_period=usage_period,
            subscription=subscription,
        )

    async def check_can_analyze(self, context: BillingContext, video_count: int = 1) -> None:
        """Check if user can perform analysis. Raises if not allowed.

        When hybrid flags are enabled, checks credit balance for ALL tiers.
        Otherwise falls back to legacy free-tier-only limit check.
        """
        from .credits.exceptions import InsufficientCredits

        if (
            self._billing_flags
            and (self._billing_flags.hybrid_write_enabled or self._billing_flags.hybrid_read_enabled)
            and self._credit_service
            and self._credit_settings
        ):
            balance = await self._credit_service.get_billing_summary(context.user.id)
            max_cost = self._credit_settings.l2_cost
            required = video_count * max_cost
            if balance.available < required:
                logger.warning(
                    "Insufficient credits for user %s: %d available, %d required",
                    context.user.id,
                    balance.available,
                    required,
                )
                raise InsufficientCredits(
                    "Insufficient credits for this operation"
                )
        elif context.tier == Tier.FREE:
            if context.usage_period.videos_remaining < video_count:
                raise UsageLimitExceeded(
                    f"Free tier limit reached. {context.usage_period.videos_used}/{context.usage_period.videos_limit} videos used. "
                    "Please upgrade to continue."
                )

    async def record_usage(
        self,
        context: BillingContext,
        video_count: int = 1,
        check_thresholds: bool = True,
    ) -> UsagePeriod:
        """Record usage and optionally check notification thresholds."""
        # When hybrid_read_enabled, the credit system is authoritative.
        # Callers should gate on this flag, but we enforce here as defense-in-depth.
        if self._billing_flags is not None and self._billing_flags.hybrid_read_enabled:
            return context.usage_period
        if video_count < 1:
            raise ValueError(f"video_count must be >= 1, got {video_count}")
        # Invalidate cache so next request sees updated usage.
        self._context_cache.clear()
        enforce = context.tier == Tier.FREE
        updated_period = await self._repo.increment_usage(
            context.usage_period.id, video_count, enforce_limit=enforce
        )
        if updated_period is None:
            raise UsageLimitExceeded("Usage limit exceeded (concurrent request race)")

        if check_thresholds:
            await self._check_and_notify_thresholds(updated_period)

        # Shadow metering hook (injected at construction, not per-call)
        if (
            self._billing_flags is not None
            and self._billing_flags.shadow_metering_enabled
            and self._credit_service is not None
        ):
            await self._credit_service.shadow_record_usage(
                user_id=context.user.id,
                units=video_count,
                source_type="shadow",
                source_id=f"shadow:{updated_period.id}:{video_count}",
            )

        return updated_period

    async def get_or_create_stripe_customer(
        self, user_id: UUID, stripe_client: stripe.StripeClient
    ) -> str:
        """Resolve or auto-create a Stripe customer for this user.

        Uses compare-and-swap to prevent duplicate Stripe customers
        on concurrent requests.
        """
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found")

        if user.stripe_customer_id:
            return user.stripe_customer_id

        # Auto-create Stripe customer
        customer = await asyncio.wait_for(
            stripe_client.v1.customers.create_async(
                params={
                    "email": user.email,
                    "metadata": {"user_id": str(user_id)},
                }
            ),
            timeout=10,
        )

        # Compare-and-swap: only update if still NULL
        updated = await self._repo.set_stripe_customer_if_null(user_id, customer.id)
        if not updated:
            # Another request won the race — re-read to get winner's customer_id
            user = await self._repo.get_user_by_id(user_id)
            if not user or not user.stripe_customer_id:
                raise UserNotFound(f"User {user_id} not found after CAS")
            return user.stripe_customer_id

        return customer.id

    async def get_usage_stats(self, user_id: UUID) -> dict:
        """Get usage statistics for GET /v1/usage endpoint."""
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found")

        subscription = await self._repo.get_subscription(user_id)
        tier = subscription.tier if subscription else Tier.FREE
        tier_config = get_tier_config(tier)

        usage_period = await self._repo.get_or_create_usage_period(user_id, tier)

        return {
            "tier": tier.value,
            "videos_used": usage_period.videos_used,
            "videos_limit": usage_period.videos_limit,
            "videos_remaining": usage_period.videos_remaining,
            "usage_percent": round(usage_period.usage_percent, 1),
            "billing_period_start": usage_period.period_start.isoformat(),
            "billing_period_end": usage_period.period_end.isoformat(),
            "rate_limit_per_minute": tier_config.rate_limit_per_minute,
            "subscription_status": subscription.status if subscription else None,
        }

    async def _check_and_notify_thresholds(self, usage_period: UsagePeriod) -> None:
        """Check usage threshold and send notification (single 90% threshold for v1)."""
        if usage_period.usage_percent >= 90:
            # Atomic claim prevents duplicate notifications from concurrent requests
            claimed = await self._repo.try_claim_notification(usage_period.id, 90)
            if claimed:
                await self._send_threshold_notification(usage_period, 90)

    async def _send_threshold_notification(
        self,
        usage_period: UsagePeriod,
        threshold: int,
    ) -> None:
        """Emit structured log for usage threshold (monitoring alerts pick this up)."""
        logger.warning(
            "usage_threshold_reached",
            extra={
                "user_id": str(usage_period.user_id),
                "threshold_percent": threshold,
                "videos_used": usage_period.videos_used,
                "videos_limit": usage_period.videos_limit,
                "period_id": str(usage_period.id),
            },
        )
