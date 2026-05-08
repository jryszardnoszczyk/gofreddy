"""Tier definitions and feature matrix."""

from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    """Simplified 2-tier system for v1 launch."""

    FREE = "free"
    PRO = "pro"


@dataclass(frozen=True, slots=True)
class TierConfig:
    """Configuration for a subscription tier."""

    tier: Tier
    videos_per_month: int
    rate_limit_per_minute: int
    moderation_class_count: int  # 21 for FREE (core), 80 for PRO (full GARM taxonomy)
    agent_messages_per_day: int
    max_batch_size: int
    max_search_results: int
    max_generation_jobs_per_day: int
    max_concurrent_generation: int
    max_monitors: int = 3
    max_mentions_per_month: int = 5_000
    max_sources_per_monitor: int = 5
    max_alert_rules_per_monitor: int = 3

    @property
    def is_paid_tier(self) -> bool:
        """Check if this is a paid tier (has access to all features)."""
        return self.tier != Tier.FREE


# Tier configurations - simplified for v1
TIER_CONFIGS: dict[Tier, TierConfig] = {
    Tier.FREE: TierConfig(
        tier=Tier.FREE,
        videos_per_month=100,
        rate_limit_per_minute=30,
        moderation_class_count=21,  # Core classes only
        agent_messages_per_day=20,
        max_batch_size=5,
        max_search_results=200,
        max_generation_jobs_per_day=0,
        max_concurrent_generation=0,
    ),
    Tier.PRO: TierConfig(
        tier=Tier.PRO,
        videos_per_month=50_000,
        rate_limit_per_minute=300,
        moderation_class_count=80,  # Full 80-class GARM taxonomy
        agent_messages_per_day=1_000,
        max_batch_size=200,
        max_search_results=2000,
        max_generation_jobs_per_day=10,
        max_concurrent_generation=2,
        max_monitors=20,
        max_mentions_per_month=500_000,
        max_sources_per_monitor=10,
        max_alert_rules_per_monitor=10,
    ),
}


def get_tier_config(tier: Tier) -> TierConfig:
    """Get configuration for a tier."""
    return TIER_CONFIGS[tier]


def is_paid_tier(tier: Tier) -> bool:
    """Check if tier has access to all features."""
    return tier != Tier.FREE
