"""Pytest fixtures for deepfake detection tests."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.deepfake.config import DeepfakeConfig
from src.deepfake.models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
    Verdict,
)


@pytest.fixture
def mock_config() -> DeepfakeConfig:
    """Create test configuration."""
    return DeepfakeConfig(
        reality_defender_api_key="test-rd-key",
        lipinc_api_key="test-lipinc-key",
        lipinc_enabled=True,
        reality_defender_enabled=True,
        deepfake_threshold=0.5,
        daily_spend_limit_cents=10000,
        cache_ttl_days=30,
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock repository."""
    repo = AsyncMock()
    repo.get_by_video_analysis_id.return_value = None
    repo.get_user_daily_cost.return_value = 0
    return repo


@pytest.fixture
def mock_lipinc() -> AsyncMock:
    """Create mock LIPINC analyzer."""
    analyzer = AsyncMock()
    analyzer.close = AsyncMock()
    return analyzer


@pytest.fixture
def mock_reality_defender() -> AsyncMock:
    """Create mock Reality Defender client."""
    client = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def authentic_lip_sync_result() -> LipSyncResult:
    """Create authentic lip-sync result."""
    return LipSyncResult(
        score=0.95,
        anomaly_detected=False,
        confidence=Confidence.HIGH,
        processing_time_ms=2000,
    )


@pytest.fixture
def deepfake_lip_sync_result() -> LipSyncResult:
    """Create deepfake lip-sync result."""
    return LipSyncResult(
        score=0.2,
        anomaly_detected=True,
        confidence=Confidence.HIGH,
        processing_time_ms=2000,
    )


@pytest.fixture
def no_face_lip_sync_result() -> LipSyncResult:
    """Create no-face lip-sync result."""
    return LipSyncResult(
        score=None,
        anomaly_detected=False,
        confidence=None,
        error="no_face_detected",
        processing_time_ms=1000,
    )


@pytest.fixture
def authentic_reality_defender_result() -> RealityDefenderResult:
    """Create authentic Reality Defender result."""
    return RealityDefenderResult(
        score=0.1,
        verdict=Verdict.AUTHENTIC,
        indicators=[],
        processing_time_ms=3000,
        cost_cents=40,
    )


@pytest.fixture
def deepfake_reality_defender_result() -> RealityDefenderResult:
    """Create deepfake Reality Defender result."""
    return RealityDefenderResult(
        score=0.85,
        verdict=Verdict.MANIPULATED,
        indicators=["lip_sync_mismatch", "face_boundary_artifacts"],
        processing_time_ms=3000,
        cost_cents=40,
    )


@pytest.fixture
def uncertain_reality_defender_result() -> RealityDefenderResult:
    """Create uncertain Reality Defender result."""
    return RealityDefenderResult(
        score=0.5,
        verdict=Verdict.UNCERTAIN,
        indicators=["low_quality_source"],
        processing_time_ms=3000,
        cost_cents=40,
    )


@pytest.fixture
def sample_deepfake_record() -> DeepfakeAnalysisRecord:
    """Create sample deepfake analysis record."""
    return DeepfakeAnalysisRecord(
        id=uuid4(),
        video_analysis_id=uuid4(),
        lip_sync_score=0.2,
        lip_sync_anomaly_detected=True,
        lip_sync_confidence=Confidence.HIGH,
        lip_sync_error=None,
        reality_defender_score=0.85,
        reality_defender_verdict=Verdict.MANIPULATED,
        reality_defender_indicators=["lip_sync_mismatch"],
        reality_defender_error=None,
        combined_score=0.72,
        is_deepfake=True,
        risk_level=RiskLevel.HIGH,
        detection_method=DetectionMethod.ENSEMBLE,
        limitations=[],
        processing_time_ms=5000,
        cost_cents=55,
        analyzed_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_authentic_record() -> DeepfakeAnalysisRecord:
    """Create sample authentic analysis record."""
    return DeepfakeAnalysisRecord(
        id=uuid4(),
        video_analysis_id=uuid4(),
        lip_sync_score=0.95,
        lip_sync_anomaly_detected=False,
        lip_sync_confidence=Confidence.HIGH,
        lip_sync_error=None,
        reality_defender_score=0.1,
        reality_defender_verdict=Verdict.AUTHENTIC,
        reality_defender_indicators=[],
        reality_defender_error=None,
        combined_score=0.08,
        is_deepfake=False,
        risk_level=RiskLevel.NONE,
        detection_method=DetectionMethod.ENSEMBLE,
        limitations=[],
        processing_time_ms=5000,
        cost_cents=55,
        analyzed_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def valid_video_url() -> str:
    """Create valid R2 presigned URL."""
    return "https://test-bucket.r2.cloudflarestorage.com/videos/test-video.mp4?X-Amz-Signature=abc123"
