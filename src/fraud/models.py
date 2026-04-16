"""Fraud detection data models and exceptions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Self
from uuid import UUID, uuid4


class FraudRiskLevel(str, Enum):
    """Fraud risk levels for database enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AQSGrade(str, Enum):
    """Audience Quality Score grades."""

    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    POOR = "poor"
    CRITICAL = "critical"


# ─── Exceptions ─────────────────────────────────────────────────────────────


class InsufficientDataError(Exception):
    """Raised when insufficient data is available for analysis."""

    def __init__(self, component: str, required: int, available: int) -> None:
        self.component = component
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient data for {component}: required {required}, got {available}"
        )


# ─── Analysis Models ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class EngagementAnomaly:
    """Detected engagement anomaly."""

    type: Literal["suspiciously_low", "suspiciously_high"]
    severity: Literal["low", "medium", "high"]
    evidence: str


@dataclass(frozen=True, slots=True)
class BotCommentAnalysis:
    """Results of bot comment detection via Gemini."""

    total_analyzed: int
    bot_like_count: int
    bot_ratio: float
    confidence: Literal["low", "medium", "high"]
    patterns_detected: list[str]
    suspicious_examples: list[dict[str, str]]


@dataclass(frozen=True, slots=True)
class AQSResult:
    """Audience Quality Score calculation result."""

    score: float
    grade: AQSGrade
    components: dict[str, float]

    @classmethod
    def calculate(
        cls,
        engagement_score: float,
        audience_quality_score: float,
        comment_authenticity_score: float,
    ) -> Self:
        """Calculate AQS from component scores.

        AQS = (engagement × 0.30) + (audience × 0.35) +
              (comment × 0.35)

        Grades:
        - 90+: Excellent (very high quality audience)
        - 80-89: Very Good
        - 60-79: Good (acceptable)
        - 40-59: Poor
        - <40: Significant fraud risk
        """
        aqs = (
            engagement_score * 0.30
            + audience_quality_score * 0.35
            + comment_authenticity_score * 0.35
        )

        grade = (
            AQSGrade.EXCELLENT
            if aqs >= 90
            else AQSGrade.VERY_GOOD
            if aqs >= 80
            else AQSGrade.GOOD
            if aqs >= 60
            else AQSGrade.POOR
            if aqs >= 40
            else AQSGrade.CRITICAL
        )

        return cls(
            score=round(aqs, 2),
            grade=grade,
            components={
                "engagement": round(engagement_score, 2),
                "audience_quality": round(audience_quality_score, 2),
                "comment_authenticity": round(comment_authenticity_score, 2),
            },
        )


@dataclass(frozen=True, slots=True)
class FollowerAnalysisResult:
    """Result of follower analysis."""

    fake_follower_percentage: float
    sample_size: int
    confidence: Literal["low", "medium", "high"]
    suspicious_signals: dict[str, int]  # Signal name -> count


# ─── Database Record ────────────────────────────────────────────────────────


@dataclass
class FraudAnalysisRecord:
    """Database record for fraud analysis results."""

    id: UUID
    creator_id: UUID | None
    platform: str
    username: str
    cache_key: str

    # Fake follower analysis
    fake_follower_percentage: float | None
    fake_follower_confidence: str | None
    follower_sample_size: int | None

    # Engagement analysis
    engagement_rate: float | None
    engagement_tier: str | None
    engagement_anomaly: str | None

    # Bot comment analysis
    bot_comment_ratio: float | None
    comments_analyzed: int | None
    bot_patterns_detected: list[str]

    # AQS Score
    aqs_score: float | None
    aqs_grade: str | None
    aqs_components: dict[str, float]
    growth_data_available: bool

    # Overall assessment
    fraud_risk_level: FraudRiskLevel
    fraud_risk_score: int

    # Metadata
    analyzed_at: datetime | None = None
    expires_at: datetime | None = None
    model_version: str | None = None

    @classmethod
    def create(
        cls,
        *,
        platform: str,
        username: str,
        cache_key: str,
        aqs: AQSResult,
        follower_result: FollowerAnalysisResult | None = None,
        engagement_rate: float | None = None,
        engagement_tier: str | None = None,
        engagement_anomaly: EngagementAnomaly | None = None,
        bot_analysis: BotCommentAnalysis | None = None,
        creator_id: UUID | None = None,
        model_version: str | None = None,
        cache_ttl_days: int = 7,
    ) -> Self:
        """Create a new fraud analysis record."""
        from datetime import timedelta

        # Determine risk level from AQS
        if aqs.score >= 80:
            risk_level = FraudRiskLevel.LOW
        elif aqs.score >= 60:
            risk_level = FraudRiskLevel.MEDIUM
        elif aqs.score >= 40:
            risk_level = FraudRiskLevel.HIGH
        else:
            risk_level = FraudRiskLevel.CRITICAL

        # Risk score is inverse of AQS (high AQS = low risk)
        risk_score = max(0, min(100, int(100 - aqs.score)))

        now = datetime.now(timezone.utc)

        return cls(
            id=uuid4(),
            creator_id=creator_id,
            platform=platform,
            username=username,
            cache_key=cache_key,
            fake_follower_percentage=follower_result.fake_follower_percentage if follower_result else None,
            fake_follower_confidence=follower_result.confidence if follower_result else None,
            follower_sample_size=follower_result.sample_size if follower_result else None,
            engagement_rate=engagement_rate,
            engagement_tier=engagement_tier,
            engagement_anomaly=engagement_anomaly.type if engagement_anomaly else None,
            bot_comment_ratio=bot_analysis.bot_ratio if bot_analysis else None,
            comments_analyzed=bot_analysis.total_analyzed if bot_analysis else None,
            bot_patterns_detected=bot_analysis.patterns_detected if bot_analysis else [],
            aqs_score=aqs.score,
            aqs_grade=aqs.grade.value,
            aqs_components=aqs.components,
            growth_data_available=False,
            fraud_risk_level=risk_level,
            fraud_risk_score=risk_score,
            analyzed_at=now,
            expires_at=now + timedelta(days=cache_ttl_days),
            model_version=model_version,
        )

    @classmethod
    def from_row(cls, row: Any) -> Self:
        """Create record from database row."""
        data = dict(row)
        # Convert enum string to FraudRiskLevel
        if isinstance(data.get("fraud_risk_level"), str):
            data["fraud_risk_level"] = FraudRiskLevel(data["fraud_risk_level"])
        return cls(**data)

    def to_row(self) -> tuple:
        """Convert to database row values."""
        import json

        return (
            self.id,
            self.creator_id,
            self.platform,
            self.username,
            self.cache_key,
            self.fake_follower_percentage,
            self.fake_follower_confidence,
            self.follower_sample_size,
            self.engagement_rate,
            self.engagement_tier,
            self.engagement_anomaly,
            self.bot_comment_ratio,
            self.comments_analyzed,
            json.dumps(self.bot_patterns_detected),
            self.aqs_score,
            self.aqs_grade,
            json.dumps(self.aqs_components),
            self.growth_data_available,
            self.fraud_risk_level.value,
            self.fraud_risk_score,
            self.analyzed_at,
            self.expires_at,
            self.model_version,
        )
