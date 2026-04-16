"""Fraud detection module for video intelligence platform."""

from .analyzers import EngagementAnalyzer, FollowerAnalyzer
from .config import FraudDetectionConfig, PlatformThresholds
from .models import (
    AQSGrade,
    AQSResult,
    BotCommentAnalysis,
    EngagementAnomaly,
    FraudAnalysisRecord,
    FraudRiskLevel,
    InsufficientDataError,
)

__all__ = [
    "FraudDetectionConfig",
    "PlatformThresholds",
    "AQSGrade",
    "AQSResult",
    "BotCommentAnalysis",
    "EngagementAnomaly",
    "FraudAnalysisRecord",
    "FraudRiskLevel",
    "InsufficientDataError",
    "EngagementAnalyzer",
    "FollowerAnalyzer",
]
