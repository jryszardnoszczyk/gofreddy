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
from .repository import PostgresFraudRepository
from .service import FraudDetectionService

__all__ = [
    # Config
    "FraudDetectionConfig",
    "PlatformThresholds",
    # Models
    "AQSGrade",
    "AQSResult",
    "BotCommentAnalysis",
    "EngagementAnomaly",
    "FraudAnalysisRecord",
    "FraudRiskLevel",
    "InsufficientDataError",
    # Analyzers
    "EngagementAnalyzer",
    "FollowerAnalyzer",
    # Repository
    "PostgresFraudRepository",
    # Service
    "FraudDetectionService",
]
