"""Tests for deepfake detection models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.deepfake.models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DeepfakeAnalysisResponse,
    DeepfakeAnalyzeRequest,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
    Verdict,
)


class TestLipSyncResult:
    """Tests for LipSyncResult dataclass."""

    def test_create_authentic_result(self):
        """Test creating authentic lip-sync result."""
        result = LipSyncResult(
            score=0.95,
            anomaly_detected=False,
            confidence=Confidence.HIGH,
            processing_time_ms=2000,
        )
        assert result.score == 0.95
        assert result.anomaly_detected is False
        assert result.confidence == Confidence.HIGH
        assert result.error is None

    def test_create_deepfake_result(self):
        """Test creating deepfake lip-sync result."""
        result = LipSyncResult(
            score=0.2,
            anomaly_detected=True,
            confidence=Confidence.HIGH,
            processing_time_ms=2000,
        )
        assert result.score == 0.2
        assert result.anomaly_detected is True

    def test_create_error_result(self):
        """Test creating error lip-sync result."""
        result = LipSyncResult(
            score=None,
            anomaly_detected=False,
            confidence=None,
            error="no_face_detected",
            processing_time_ms=1000,
        )
        assert result.score is None
        assert result.error == "no_face_detected"


class TestRealityDefenderResult:
    """Tests for RealityDefenderResult dataclass."""

    def test_create_authentic_result(self):
        """Test creating authentic Reality Defender result."""
        result = RealityDefenderResult(
            score=0.1,
            verdict=Verdict.AUTHENTIC,
            indicators=[],
            processing_time_ms=3000,
            cost_cents=40,
        )
        assert result.score == 0.1
        assert result.verdict == Verdict.AUTHENTIC
        assert result.cost_cents == 40

    def test_create_manipulated_result(self):
        """Test creating manipulated Reality Defender result."""
        result = RealityDefenderResult(
            score=0.85,
            verdict=Verdict.MANIPULATED,
            indicators=["lip_sync_mismatch", "face_boundary"],
            processing_time_ms=3000,
            cost_cents=40,
        )
        assert result.score == 0.85
        assert result.verdict == Verdict.MANIPULATED
        assert len(result.indicators) == 2


class TestDeepfakeAnalysisRecord:
    """Tests for DeepfakeAnalysisRecord dataclass."""

    def test_create_full_record(self):
        """Test creating full analysis record."""
        record = DeepfakeAnalysisRecord(
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
        assert record.is_deepfake is True
        assert record.risk_level == RiskLevel.HIGH
        assert record.detection_method == DetectionMethod.ENSEMBLE


class TestDeepfakeAnalyzeRequest:
    """Tests for DeepfakeAnalyzeRequest Pydantic model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = DeepfakeAnalyzeRequest(video_id="test-video-id")
        assert request.video_id == "test-video-id"
        assert request.force_refresh is False

    def test_request_with_force_refresh(self):
        """Test request with force_refresh enabled."""
        request = DeepfakeAnalyzeRequest(
            video_id="test-video-id",
            force_refresh=True,
        )
        assert request.force_refresh is True


class TestDeepfakeAnalysisResponse:
    """Tests for DeepfakeAnalysisResponse Pydantic model."""

    def test_valid_response(self):
        """Test valid response creation."""
        response = DeepfakeAnalysisResponse(
            video_id="test-video-id",
            is_deepfake=True,
            risk_level=RiskLevel.HIGH,
            combined_score=0.72,
            detection_method=DetectionMethod.ENSEMBLE,
            limitations=[],
            indicators=["lip_sync_mismatch"],
            processing_time_ms=5000,
            cost_cents=55,
            analyzed_at=datetime.now(timezone.utc),
        )
        assert response.video_id == "test-video-id"
        assert response.is_deepfake is True
        assert response.combined_score == 0.72

    def test_response_with_lip_sync(self):
        """Test response with lip_sync details."""
        response = DeepfakeAnalysisResponse(
            video_id="test-video-id",
            is_deepfake=True,
            risk_level=RiskLevel.HIGH,
            combined_score=0.72,
            lip_sync={
                "score": 0.2,
                "anomaly_detected": True,
                "confidence": "high",
            },
            detection_method=DetectionMethod.ENSEMBLE,
            limitations=[],
            indicators=[],
            processing_time_ms=5000,
            cost_cents=55,
            analyzed_at=datetime.now(timezone.utc),
        )
        assert response.lip_sync is not None
        assert response.lip_sync["score"] == 0.2

    def test_score_validation(self):
        """Test combined_score validation."""
        with pytest.raises(ValueError):
            DeepfakeAnalysisResponse(
                video_id="test-video-id",
                is_deepfake=True,
                risk_level=RiskLevel.HIGH,
                combined_score=1.5,  # Invalid: > 1.0
                detection_method=DetectionMethod.ENSEMBLE,
                limitations=[],
                indicators=[],
                processing_time_ms=5000,
                cost_cents=55,
                analyzed_at=datetime.now(timezone.utc),
            )


class TestEnums:
    """Tests for enum values."""

    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.NONE.value == "none"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_detection_method_values(self):
        """Test DetectionMethod enum values."""
        assert DetectionMethod.LIPINC_ONLY.value == "lipinc_only"
        assert DetectionMethod.REALITY_DEFENDER_ONLY.value == "reality_defender_only"
        assert DetectionMethod.ENSEMBLE.value == "ensemble"

    def test_confidence_values(self):
        """Test Confidence enum values."""
        assert Confidence.LOW.value == "low"
        assert Confidence.MEDIUM.value == "medium"
        assert Confidence.HIGH.value == "high"

    def test_verdict_values(self):
        """Test Verdict enum values."""
        assert Verdict.AUTHENTIC.value == "authentic"
        assert Verdict.MANIPULATED.value == "manipulated"
        assert Verdict.UNCERTAIN.value == "uncertain"
