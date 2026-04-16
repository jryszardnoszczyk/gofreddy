"""Pydantic models for deepfake detection."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level for deepfake detection."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionMethod(str, Enum):
    """Detection method used for analysis."""

    LIPINC_ONLY = "lipinc_only"
    REALITY_DEFENDER_ONLY = "reality_defender_only"
    ENSEMBLE = "ensemble"


class Confidence(str, Enum):
    """Confidence level for detection."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(str, Enum):
    """Verdict from deepfake analysis."""

    AUTHENTIC = "authentic"
    MANIPULATED = "manipulated"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class LipSyncResult:
    """Result from LIPINC lip-sync analysis."""

    score: float | None  # 0.0-1.0 (1.0 = authentic)
    anomaly_detected: bool
    confidence: Confidence | None
    error: str | None = None
    processing_time_ms: int = 0


@dataclass(frozen=True, slots=True)
class RealityDefenderResult:
    """Result from Reality Defender API."""

    score: float | None  # 0.0-1.0 (1.0 = manipulated)
    verdict: Verdict | None
    indicators: list[str]
    error: str | None = None
    processing_time_ms: int = 0
    cost_cents: int = 0


@dataclass(frozen=True, slots=True)
class DeepfakeAnalysisRecord:
    """Database record for deepfake analysis."""

    id: UUID
    video_analysis_id: UUID
    lip_sync_score: float | None
    lip_sync_anomaly_detected: bool | None
    lip_sync_confidence: Confidence | None
    lip_sync_error: str | None
    reality_defender_score: float | None
    reality_defender_verdict: Verdict | None
    reality_defender_indicators: list[str]
    reality_defender_error: str | None
    combined_score: float
    is_deepfake: bool
    risk_level: RiskLevel
    detection_method: DetectionMethod
    limitations: list[str]
    processing_time_ms: int
    cost_cents: int
    analyzed_at: datetime


# API Request/Response models
class DeepfakeAnalyzeRequest(BaseModel):
    """Request to analyze video for deepfakes."""

    video_id: str = Field(..., description="Video ID to analyze")
    force_refresh: bool = Field(default=False, description="Bypass cache")


class DeepfakeAnalysisResponse(BaseModel):
    """Response from deepfake analysis."""

    video_id: str
    is_deepfake: bool
    risk_level: RiskLevel
    combined_score: float = Field(..., ge=0.0, le=1.0)

    # Individual signal details
    lip_sync: dict | None = Field(None, description="LIPINC results")
    reality_defender: dict | None = Field(None, description="Reality Defender results")

    # Explainability
    detection_method: DetectionMethod
    limitations: list[str]
    indicators: list[str]

    # Metadata
    processing_time_ms: int
    cost_cents: int
    analyzed_at: datetime
    cached: bool = False
