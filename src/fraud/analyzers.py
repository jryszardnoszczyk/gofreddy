"""Fraud detection analyzers for follower and engagement analysis."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from .config import (
    ENGAGEMENT_BENCHMARKS,
    PlatformThresholds,
    get_tier,
)
from .models import (
    EngagementAnomaly,
    FollowerAnalysisResult,
    InsufficientDataError,
)

if TYPE_CHECKING:
    from ..fetcher.models import FollowerProfile


class FollowerAnalyzer:
    """Analyze followers for fake/bot indicators.

    Uses platform-calibrated thresholds validated at 100% accuracy
    on authentic accounts.
    """

    # Pattern for detecting random-looking usernames
    RANDOM_USERNAME_PATTERN = re.compile(
        r"^[a-z]{2,6}\d{5,}$|"  # Letters followed by many numbers
        r"^user\d{6,}$|"  # Generic "user" prefix
        r"^\d{8,}$|"  # All numbers
        r"^[a-z]{10,}$"  # Very long lowercase only (no breaks)
    )

    def __init__(self, min_sample_size: int = 50) -> None:
        self._min_sample_size = min_sample_size

    def analyze(
        self,
        followers: list[FollowerProfile],
        platform: Literal["tiktok", "instagram", "youtube"],
    ) -> FollowerAnalysisResult:
        """Analyze a sample of followers for fraud indicators.

        Args:
            followers: List of follower profiles to analyze
            platform: Platform for threshold calibration

        Returns:
            FollowerAnalysisResult with fake percentage and confidence

        Raises:
            InsufficientDataError: If sample size is below minimum
        """
        sample_size = len(followers)

        if sample_size < self._min_sample_size:
            raise InsufficientDataError(
                component="follower_analysis",
                required=self._min_sample_size,
                available=sample_size,
            )

        thresholds = PlatformThresholds.get(platform)
        suspicious_count = 0
        signals: dict[str, int] = {
            "no_profile_pic": 0,
            "random_username": 0,
            "empty_bio": 0,
            "zero_posts": 0,
            "suspicious_ratio": 0,
        }

        for follower in followers:
            score = self._score_follower(follower, thresholds.weights, signals)
            if score >= thresholds.suspicious_threshold:
                suspicious_count += 1

        fake_percentage = (suspicious_count / sample_size) * 100

        # Confidence based on sample size
        if sample_size >= 150:
            confidence: Literal["low", "medium", "high"] = "high"
        elif sample_size >= 100:
            confidence = "medium"
        else:
            confidence = "low"

        return FollowerAnalysisResult(
            fake_follower_percentage=round(fake_percentage, 2),
            sample_size=sample_size,
            confidence=confidence,
            suspicious_signals=signals,
        )

    def _score_follower(
        self,
        follower: FollowerProfile,
        weights: dict[str, float],
        signals: dict[str, int],
    ) -> float:
        """Calculate suspicion score for a single follower."""
        score = 0.0

        # No profile picture
        if not follower.has_profile_pic:
            score += weights["no_profile_pic"]
            signals["no_profile_pic"] += 1

        # Random-looking username
        if self._is_random_username(follower.username):
            score += weights["random_username"]
            signals["random_username"] += 1

        # Empty bio
        if not follower.bio or len(follower.bio.strip()) == 0:
            score += weights["empty_bio"]
            signals["empty_bio"] += 1

        # Zero posts
        if follower.post_count == 0:
            score += weights["zero_posts"]
            signals["zero_posts"] += 1

        # Suspicious following/follower ratio (following many, few followers)
        if follower.following_count and follower.follower_count is not None:
            if follower.following_count > 500 and follower.follower_count < 50:
                score += weights["suspicious_ratio"]
                signals["suspicious_ratio"] += 1

        return score

    def _is_random_username(self, username: str) -> bool:
        """Detect random-looking usernames typical of bot accounts."""
        if not username:
            return False
        return bool(self.RANDOM_USERNAME_PATTERN.match(username.lower()))


class EngagementAnalyzer:
    """Analyze engagement patterns for anomalies.

    Detects suspiciously high or low engagement relative to
    platform-specific benchmarks.
    """

    def analyze(
        self,
        engagement_rate: float,
        follower_count: int,
        platform: Literal["tiktok", "instagram", "youtube"],
    ) -> tuple[str, EngagementAnomaly | None]:
        """Analyze engagement rate for anomalies.

        Args:
            engagement_rate: Calculated engagement rate as percentage
            follower_count: Creator's follower count
            platform: Platform for benchmark lookup

        Returns:
            Tuple of (tier, anomaly or None)
        """
        tier = get_tier(follower_count)
        benchmarks = ENGAGEMENT_BENCHMARKS.get(platform, ENGAGEMENT_BENCHMARKS["instagram"])
        expected = benchmarks.get(tier, benchmarks["micro"])
        min_expected, max_expected = expected

        # Check for suspiciously low engagement
        if engagement_rate < min_expected * 0.5:
            return tier, EngagementAnomaly(
                type="suspiciously_low",
                severity="high",
                evidence=f"ER {engagement_rate:.2f}% is <50% of expected minimum {min_expected}%",
            )

        # Check for suspiciously high engagement
        if engagement_rate > max_expected * 3:
            return tier, EngagementAnomaly(
                type="suspiciously_high",
                severity="high",
                evidence=f"ER {engagement_rate:.2f}% is >3x expected maximum {max_expected}%",
            )

        return tier, None

    def calculate_engagement_score(
        self,
        engagement_rate: float,
        follower_count: int,
        platform: Literal["tiktok", "instagram", "youtube"],
    ) -> float:
        """Calculate engagement score (0-100) relative to benchmarks.

        Score interpretation:
        - 100: At or above expected max for tier
        - 50: At expected minimum for tier
        - 0: Zero engagement or anomalously low
        """
        tier = get_tier(follower_count)
        benchmarks = ENGAGEMENT_BENCHMARKS.get(platform, ENGAGEMENT_BENCHMARKS["instagram"])
        expected = benchmarks.get(tier, benchmarks["micro"])
        min_expected, max_expected = expected

        if engagement_rate <= 0:
            return 0.0

        # Linear scale from min to max benchmark
        if engagement_rate < min_expected:
            # Below minimum: scale 0-50
            return (engagement_rate / min_expected) * 50
        elif engagement_rate <= max_expected:
            # Within expected: scale 50-100
            range_size = max_expected - min_expected
            if range_size > 0:
                return 50 + ((engagement_rate - min_expected) / range_size) * 50
            return 75.0  # Default if min == max
        else:
            # Above maximum: cap at 100 (not penalized for high engagement)
            return 100.0
