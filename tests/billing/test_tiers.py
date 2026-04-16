"""Tests for billing tiers module."""

import pytest

from src.billing.tiers import Tier, TierConfig, TIER_CONFIGS, get_tier_config, is_paid_tier


class TestTier:
    """Tests for Tier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert Tier.FREE.value == "free"
        assert Tier.PRO.value == "pro"

    def test_tier_from_string(self):
        """Test creating tier from string value."""
        assert Tier("free") == Tier.FREE
        assert Tier("pro") == Tier.PRO

    def test_tier_invalid_value(self):
        """Test invalid tier raises error."""
        with pytest.raises(ValueError):
            Tier("invalid")


class TestTierConfig:
    """Tests for TierConfig dataclass."""

    def test_free_tier_config(self):
        """Test free tier configuration."""
        config = TIER_CONFIGS[Tier.FREE]
        assert config.tier == Tier.FREE
        assert config.videos_per_month == 100
        assert config.rate_limit_per_minute == 30
        assert config.is_paid_tier is False
        assert config.moderation_class_count == 21  # Core classes only
        assert config.agent_messages_per_day == 20
        assert config.max_batch_size == 5
        assert config.max_search_results == 200

    def test_pro_tier_config(self):
        """Test pro tier configuration."""
        config = TIER_CONFIGS[Tier.PRO]
        assert config.tier == Tier.PRO
        assert config.videos_per_month == 50_000
        assert config.rate_limit_per_minute == 300
        assert config.is_paid_tier is True
        assert config.moderation_class_count == 80  # Full 80-class GARM taxonomy
        assert config.agent_messages_per_day == 1_000
        assert config.max_batch_size == 200
        assert config.max_search_results == 2000

    def test_tier_config_frozen(self):
        """Test tier config is immutable."""
        config = TIER_CONFIGS[Tier.FREE]
        with pytest.raises(AttributeError):
            config.videos_per_month = 999  # type: ignore

    def test_tier_config_slots(self):
        """Test tier config uses slots."""
        config = TIER_CONFIGS[Tier.FREE]
        with pytest.raises(AttributeError):
            config.__dict__

    def test_moderation_class_count_tiers(self):
        """Test moderation class count is correct for each tier (PR-014)."""
        free_config = TIER_CONFIGS[Tier.FREE]
        pro_config = TIER_CONFIGS[Tier.PRO]

        # FREE tier gets 21 core classes
        assert free_config.moderation_class_count == 21

        # PRO tier gets full 80-class GARM taxonomy
        assert pro_config.moderation_class_count == 80

        # PRO has more moderation classes than FREE
        assert pro_config.moderation_class_count > free_config.moderation_class_count


class TestGetTierConfig:
    """Tests for get_tier_config function."""

    def test_get_free_tier(self):
        """Test getting free tier config."""
        config = get_tier_config(Tier.FREE)
        assert config.tier == Tier.FREE
        assert config.videos_per_month == 100

    def test_get_pro_tier(self):
        """Test getting pro tier config."""
        config = get_tier_config(Tier.PRO)
        assert config.tier == Tier.PRO
        assert config.videos_per_month == 50_000


class TestIsPaidTier:
    """Tests for is_paid_tier function."""

    def test_free_is_not_paid(self):
        """Test free tier is not paid."""
        assert is_paid_tier(Tier.FREE) is False

    def test_pro_is_paid(self):
        """Test pro tier is paid."""
        assert is_paid_tier(Tier.PRO) is True
