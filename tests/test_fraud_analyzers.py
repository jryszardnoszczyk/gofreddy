"""Tests for fraud detection analyzers."""

import pytest

from src.fetcher.models import FollowerProfile
from src.fraud.analyzers import EngagementAnalyzer, FollowerAnalyzer
from src.fraud.models import InsufficientDataError


class TestFollowerAnalyzer:
    """Tests for FollowerAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with default settings."""
        return FollowerAnalyzer(min_sample_size=50)

    @pytest.fixture
    def authentic_followers(self) -> list[FollowerProfile]:
        """Create a list of authentic-looking followers."""
        return [
            FollowerProfile(
                username=f"real_user_{i}",
                has_profile_pic=True,
                bio=f"I love content creation! #{i}",
                post_count=50 + i,
                follower_count=200 + i * 10,
                following_count=150 + i * 5,
            )
            for i in range(100)
        ]

    @pytest.fixture
    def fake_followers(self) -> list[FollowerProfile]:
        """Create a list of suspicious-looking followers."""
        return [
            FollowerProfile(
                username=f"user{12345678 + i}",  # Random username pattern
                has_profile_pic=False,
                bio="",
                post_count=0,
                follower_count=5,
                following_count=1000,  # Following many, few followers
            )
            for i in range(100)
        ]

    def test_analyze_authentic_followers(self, analyzer, authentic_followers):
        """Test that authentic followers have low fake percentage."""
        result = analyzer.analyze(authentic_followers, "tiktok")

        assert result.fake_follower_percentage < 20.0
        assert result.sample_size == 100
        assert result.confidence in ("low", "medium", "high")

    def test_analyze_fake_followers(self, analyzer, fake_followers):
        """Test that fake followers have high fake percentage."""
        result = analyzer.analyze(fake_followers, "tiktok")

        assert result.fake_follower_percentage > 50.0
        assert result.sample_size == 100

    def test_insufficient_data_raises(self, analyzer):
        """Test that too few followers raises error."""
        followers = [
            FollowerProfile(username=f"user_{i}", has_profile_pic=True)
            for i in range(10)
        ]

        with pytest.raises(InsufficientDataError) as exc_info:
            analyzer.analyze(followers, "tiktok")

        assert exc_info.value.component == "follower_analysis"
        assert exc_info.value.required == 50
        assert exc_info.value.available == 10

    def test_platform_calibration_tiktok(self, analyzer, fake_followers):
        """Test TikTok has higher threshold (more lenient)."""
        tiktok_result = analyzer.analyze(fake_followers, "tiktok")
        instagram_result = analyzer.analyze(fake_followers, "instagram")

        # TikTok should flag fewer as fake (higher threshold)
        assert tiktok_result.fake_follower_percentage <= instagram_result.fake_follower_percentage

    def test_confidence_based_on_sample_size(self, analyzer, authentic_followers):
        """Test confidence increases with sample size."""
        small_sample = authentic_followers[:60]
        medium_sample = authentic_followers[:110]
        large_sample = authentic_followers[:100] + [
            FollowerProfile(username=f"extra_{i}", has_profile_pic=True)
            for i in range(60)
        ]

        small_result = analyzer.analyze(small_sample, "tiktok")
        medium_result = analyzer.analyze(medium_sample, "tiktok")
        large_result = analyzer.analyze(large_sample, "tiktok")

        assert small_result.confidence == "low"
        assert medium_result.confidence == "medium"
        assert large_result.confidence == "high"

    def test_random_username_detection(self, analyzer):
        """Test detection of random-looking usernames."""
        assert analyzer._is_random_username("ab12345678") is True
        assert analyzer._is_random_username("user123456") is True
        assert analyzer._is_random_username("12345678") is True
        assert analyzer._is_random_username("abcdefghijklmnop") is True
        assert analyzer._is_random_username("john_doe") is False
        assert analyzer._is_random_username("creative_content_creator") is False

    def test_suspicious_signals_tracked(self, analyzer, fake_followers):
        """Test that suspicious signals are counted."""
        result = analyzer.analyze(fake_followers, "tiktok")

        assert "no_profile_pic" in result.suspicious_signals
        assert "random_username" in result.suspicious_signals
        assert "empty_bio" in result.suspicious_signals
        assert "zero_posts" in result.suspicious_signals
        assert "suspicious_ratio" in result.suspicious_signals


class TestEngagementAnalyzer:
    """Tests for EngagementAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create engagement analyzer."""
        return EngagementAnalyzer()

    def test_normal_engagement_no_anomaly(self, analyzer):
        """Test normal engagement returns no anomaly."""
        tier, anomaly = analyzer.analyze(
            engagement_rate=6.0,  # Within nano range for TikTok
            follower_count=5000,
            platform="tiktok",
        )

        assert tier == "nano"
        assert anomaly is None

    def test_suspiciously_low_engagement(self, analyzer):
        """Test detection of suspiciously low engagement."""
        tier, anomaly = analyzer.analyze(
            engagement_rate=0.5,  # Way below expected
            follower_count=5000,
            platform="tiktok",
        )

        assert tier == "nano"
        assert anomaly is not None
        assert anomaly.type == "suspiciously_low"
        assert anomaly.severity == "high"

    def test_suspiciously_high_engagement(self, analyzer):
        """Test detection of suspiciously high engagement."""
        tier, anomaly = analyzer.analyze(
            engagement_rate=50.0,  # Way above expected
            follower_count=5000,
            platform="tiktok",
        )

        assert tier == "nano"
        assert anomaly is not None
        assert anomaly.type == "suspiciously_high"
        assert anomaly.severity == "high"

    def test_tier_detection(self, analyzer):
        """Test correct tier assignment based on followers."""
        nano_tier, _ = analyzer.analyze(5.0, 5000, "tiktok")
        micro_tier, _ = analyzer.analyze(5.0, 50000, "tiktok")
        macro_tier, _ = analyzer.analyze(3.0, 200000, "tiktok")
        mega_tier, _ = analyzer.analyze(3.0, 2000000, "tiktok")

        assert nano_tier == "nano"
        assert micro_tier == "micro"
        assert macro_tier == "macro"
        assert mega_tier == "mega"

    def test_calculate_engagement_score(self, analyzer):
        """Test engagement score calculation."""
        # Zero engagement = 0 score
        assert analyzer.calculate_engagement_score(0.0, 5000, "tiktok") == 0.0

        # Below minimum = 0-50 score
        score_low = analyzer.calculate_engagement_score(4.0, 5000, "tiktok")
        assert 0.0 < score_low < 50.0

        # At minimum = 50 score
        score_min = analyzer.calculate_engagement_score(8.0, 5000, "tiktok")
        assert score_min == 50.0

        # Above maximum = 100 score (capped)
        score_high = analyzer.calculate_engagement_score(20.0, 5000, "tiktok")
        assert score_high == 100.0

    def test_platform_specific_benchmarks(self, analyzer):
        """Test different benchmarks for different platforms."""
        # Same engagement rate, different platforms
        tiktok_tier, _ = analyzer.analyze(5.0, 50000, "tiktok")
        instagram_tier, _ = analyzer.analyze(5.0, 50000, "instagram")

        # Both should be micro tier with 50K followers
        assert tiktok_tier == "micro"
        assert instagram_tier == "micro"

        # Test anomaly detection with extreme values
        # Instagram micro max is 4%, so >12% (3x max) triggers anomaly
        _, instagram_anomaly = analyzer.analyze(15.0, 50000, "instagram")
        assert instagram_anomaly is not None
        assert instagram_anomaly.type == "suspiciously_high"

        # TikTok micro max is 10%, so >30% triggers anomaly
        # 15% is within 3x of TikTok max, so no anomaly
        _, tiktok_no_anomaly = analyzer.analyze(15.0, 50000, "tiktok")
        assert tiktok_no_anomaly is None
