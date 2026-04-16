"""Tests for deepfake detection service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.deepfake.models import (
    Confidence,
    DeepfakeAnalysisRecord,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
    Verdict,
)
from src.deepfake.service import (
    LIPINC_WEIGHT,
    REALITY_DEFENDER_WEIGHT,
    DeepfakeAnalysisResult,
    DeepfakeService,
)


@pytest.mark.mock_required
class TestDeepfakeService:
    """Tests for DeepfakeService orchestration."""

    @pytest.mark.asyncio
    async def test_analyze_both_services_succeed(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
        authentic_lip_sync_result,
        deepfake_reality_defender_result,
    ):
        """Test analysis when both services return results."""
        # Setup
        mock_lipinc.analyze.return_value = authentic_lip_sync_result
        mock_reality_defender.analyze.return_value = deepfake_reality_defender_result

        # Create mock record for repository
        created_record = MagicMock(spec=DeepfakeAnalysisRecord)
        created_record.is_deepfake = True
        created_record.detection_method = DetectionMethod.ENSEMBLE
        mock_repository.create.return_value = created_record

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        # Execute
        video_analysis_id = uuid4()
        user_id = uuid4()
        result = await service.analyze(
            video_analysis_id=video_analysis_id,
            user_id=user_id,
            video_url="https://test-bucket.r2.cloudflarestorage.com/video.mp4",
        )

        # Assert
        assert result.cached is False
        mock_lipinc.analyze.assert_called_once()
        mock_reality_defender.analyze.assert_called_once()
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_lipinc_fails_uses_reality_only(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
        authentic_reality_defender_result,
    ):
        """Test graceful degradation when LIPINC fails."""
        # Setup - LIPINC fails
        mock_lipinc.analyze.side_effect = Exception("LIPINC unavailable")
        mock_reality_defender.analyze.return_value = authentic_reality_defender_result

        created_record = MagicMock(spec=DeepfakeAnalysisRecord)
        created_record.detection_method = DetectionMethod.REALITY_DEFENDER_ONLY
        created_record.is_deepfake = False
        mock_repository.create.return_value = created_record

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        # Execute
        result = await service.analyze(
            video_analysis_id=uuid4(),
            user_id=uuid4(),
            video_url="https://test-bucket.r2.cloudflarestorage.com/video.mp4",
        )

        # Assert
        assert result.cached is False
        # Check that limitations were passed to create
        call_kwargs = mock_repository.create.call_args[1]
        assert call_kwargs["detection_method"] == DetectionMethod.REALITY_DEFENDER_ONLY
        assert "LIPINC unavailable" in call_kwargs["limitations"]

    @pytest.mark.asyncio
    async def test_analyze_returns_cached_result(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
        sample_deepfake_record,
    ):
        """Test cache hit returns without API calls."""
        # Setup - existing cached result
        mock_repository.get_by_video_analysis_id.return_value = sample_deepfake_record

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        # Execute
        result = await service.analyze(
            video_analysis_id=sample_deepfake_record.video_analysis_id,
            user_id=uuid4(),
            video_url="https://test-bucket.r2.cloudflarestorage.com/video.mp4",
        )

        # Assert
        assert result.cached is True
        assert result.record == sample_deepfake_record
        mock_lipinc.analyze.assert_not_called()
        mock_reality_defender.analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_force_refresh_bypasses_cache(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
        sample_deepfake_record,
        authentic_lip_sync_result,
        authentic_reality_defender_result,
    ):
        """Test force_refresh bypasses cache."""
        # Setup - existing cached result but force refresh
        mock_repository.get_by_video_analysis_id.return_value = sample_deepfake_record
        mock_lipinc.analyze.return_value = authentic_lip_sync_result
        mock_reality_defender.analyze.return_value = authentic_reality_defender_result

        created_record = MagicMock(spec=DeepfakeAnalysisRecord)
        created_record.is_deepfake = False
        mock_repository.create.return_value = created_record

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        # Execute
        result = await service.analyze(
            video_analysis_id=sample_deepfake_record.video_analysis_id,
            user_id=uuid4(),
            video_url="https://test-bucket.r2.cloudflarestorage.com/video.mp4",
            force_refresh=True,
        )

        # Assert
        assert result.cached is False
        mock_lipinc.analyze.assert_called_once()
        mock_reality_defender.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_both_services_fail(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
    ):
        """Test handling when both services fail raises AllProvidersUnavailableError."""
        from src.deepfake.exceptions import AllProvidersUnavailableError

        # Setup - both fail
        mock_lipinc.analyze.side_effect = Exception("LIPINC error")
        mock_reality_defender.analyze.side_effect = Exception("RD error")

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        # Execute — should raise since no provider is available
        with pytest.raises(AllProvidersUnavailableError) as exc_info:
            await service.analyze(
                video_analysis_id=uuid4(),
                user_id=uuid4(),
                video_url="https://test-bucket.r2.cloudflarestorage.com/video.mp4",
            )

        assert "all_providers_unavailable" in exc_info.value.limitations

    @pytest.mark.asyncio
    async def test_get_user_daily_cost(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
    ):
        """Test getting user's daily cost."""
        mock_repository.get_user_daily_cost.return_value = 5500  # $55

        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        user_id = uuid4()
        cost = await service.get_user_daily_cost(user_id)

        assert cost == 5500
        mock_repository.get_user_daily_cost.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_close_closes_clients(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
    ):
        """Test close() closes both clients."""
        service = DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

        await service.close()

        mock_lipinc.close.assert_called_once()
        mock_reality_defender.close.assert_called_once()


@pytest.mark.mock_required
class TestEnsembleScoring:
    """Tests for ensemble scoring logic."""

    @pytest.fixture
    def service(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
    ):
        """Create service for testing."""
        return DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

    def test_ensemble_weights_are_correct(self):
        """Test that ensemble weights sum to 1.0."""
        assert LIPINC_WEIGHT + REALITY_DEFENDER_WEIGHT == 1.0

    def test_compute_ensemble_both_authentic(self, service):
        """Test ensemble scoring with both authentic results."""
        lipinc = LipSyncResult(
            score=0.95,  # Authentic
            anomaly_detected=False,
            confidence=Confidence.HIGH,
        )
        reality = RealityDefenderResult(
            score=0.1,  # Authentic
            verdict=Verdict.AUTHENTIC,
            indicators=[],
        )

        combined, method, limitations = service._compute_ensemble(lipinc, reality)

        # LIPINC: 1.0 - 0.95 = 0.05 manipulation score
        # RD: 0.1 manipulation score
        # Ensemble: 0.05 * 0.4 + 0.1 * 0.6 = 0.02 + 0.06 = 0.08
        assert combined == pytest.approx(0.08, rel=0.01)
        assert method == DetectionMethod.ENSEMBLE
        assert len(limitations) == 0

    def test_compute_ensemble_both_deepfake(self, service):
        """Test ensemble scoring with both deepfake results."""
        lipinc = LipSyncResult(
            score=0.2,  # Deepfake (low authenticity)
            anomaly_detected=True,
            confidence=Confidence.HIGH,
        )
        reality = RealityDefenderResult(
            score=0.85,  # Deepfake
            verdict=Verdict.MANIPULATED,
            indicators=["lip_sync_mismatch"],
        )

        combined, method, limitations = service._compute_ensemble(lipinc, reality)

        # LIPINC: 1.0 - 0.2 = 0.8 manipulation score
        # RD: 0.85 manipulation score
        # Ensemble: 0.8 * 0.4 + 0.85 * 0.6 = 0.32 + 0.51 = 0.83
        assert combined == pytest.approx(0.83, rel=0.01)
        assert method == DetectionMethod.ENSEMBLE
        assert len(limitations) == 0

    def test_compute_ensemble_lipinc_only(self, service):
        """Test scoring with only LIPINC result."""
        lipinc = LipSyncResult(
            score=0.3,
            anomaly_detected=True,
            confidence=Confidence.HIGH,
        )
        reality = RealityDefenderResult(
            score=None,
            verdict=None,
            indicators=[],
            error="service_unavailable",
        )

        combined, method, limitations = service._compute_ensemble(lipinc, reality)

        # LIPINC only: 1.0 - 0.3 = 0.7 manipulation score
        assert combined == pytest.approx(0.7, rel=0.01)
        assert method == DetectionMethod.LIPINC_ONLY
        assert "service_unavailable" in limitations

    def test_compute_ensemble_reality_only(self, service):
        """Test scoring with only Reality Defender result."""
        lipinc = LipSyncResult(
            score=None,
            anomaly_detected=False,
            confidence=None,
            error="no_face_detected",
        )
        reality = RealityDefenderResult(
            score=0.6,
            verdict=Verdict.UNCERTAIN,
            indicators=["partial_face"],
        )

        combined, method, limitations = service._compute_ensemble(lipinc, reality)

        assert combined == pytest.approx(0.6, rel=0.01)
        assert method == DetectionMethod.REALITY_DEFENDER_ONLY
        assert "no_face_detected" in limitations

    def test_compute_ensemble_neither_available(self, service):
        """Test scoring with no results available."""
        lipinc = LipSyncResult(
            score=None,
            anomaly_detected=False,
            confidence=None,
            error="lipinc_error",
        )
        reality = RealityDefenderResult(
            score=None,
            verdict=None,
            indicators=[],
            error="rd_error",
        )

        combined, method, limitations = service._compute_ensemble(lipinc, reality)

        assert combined == 0.5  # Uncertain
        assert method == DetectionMethod.ENSEMBLE
        assert "all_providers_unavailable" in limitations


@pytest.mark.mock_required
class TestRiskLevelMapping:
    """Tests for risk level mapping."""

    @pytest.fixture
    def service(
        self,
        mock_repository,
        mock_lipinc,
        mock_reality_defender,
        mock_config,
    ):
        """Create service for testing."""
        return DeepfakeService(
            repository=mock_repository,
            lipinc=mock_lipinc,
            reality_defender=mock_reality_defender,
            config=mock_config,
        )

    def test_score_to_risk_critical(self, service):
        """Test critical risk level."""
        assert service._score_to_risk_level(0.85) == RiskLevel.CRITICAL
        assert service._score_to_risk_level(0.95) == RiskLevel.CRITICAL
        assert service._score_to_risk_level(1.0) == RiskLevel.CRITICAL

    def test_score_to_risk_high(self, service):
        """Test high risk level."""
        assert service._score_to_risk_level(0.70) == RiskLevel.HIGH
        assert service._score_to_risk_level(0.84) == RiskLevel.HIGH

    def test_score_to_risk_medium(self, service):
        """Test medium risk level."""
        assert service._score_to_risk_level(0.50) == RiskLevel.MEDIUM
        assert service._score_to_risk_level(0.69) == RiskLevel.MEDIUM

    def test_score_to_risk_low(self, service):
        """Test low risk level."""
        assert service._score_to_risk_level(0.30) == RiskLevel.LOW
        assert service._score_to_risk_level(0.49) == RiskLevel.LOW

    def test_score_to_risk_none(self, service):
        """Test none risk level."""
        assert service._score_to_risk_level(0.0) == RiskLevel.NONE
        assert service._score_to_risk_level(0.29) == RiskLevel.NONE
