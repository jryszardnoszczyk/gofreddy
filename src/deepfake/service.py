"""Deepfake detection service orchestration."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from ..common.cost_recorder import cost_recorder as _cost_recorder
from .config import DeepfakeConfig
from .exceptions import AllProvidersUnavailableError, DailySpendLimitExceeded
from .lipinc import LIPINCAnalyzer
from .models import (
    DeepfakeAnalysisRecord,
    DetectionMethod,
    LipSyncResult,
    RealityDefenderResult,
    RiskLevel,
)
from .reality_defender import RealityDefenderClient
from .repository import PostgresDeepfakeRepository

# Hardcoded ensemble weights (YAGNI: no need for runtime configuration)
LIPINC_WEIGHT = 0.4
REALITY_DEFENDER_WEIGHT = 0.6


@dataclass(frozen=True, slots=True)
class DeepfakeAnalysisResult:
    """Result from deepfake detection service."""

    record: DeepfakeAnalysisRecord
    cached: bool


class DeepfakeService:
    """Orchestrates deepfake detection using LIPINC and Reality Defender."""

    def __init__(
        self,
        repository: PostgresDeepfakeRepository,
        lipinc: LIPINCAnalyzer,
        reality_defender: RealityDefenderClient,
        config: DeepfakeConfig | None = None,
    ) -> None:
        self._repository = repository
        self._lipinc = lipinc
        self._reality_defender = reality_defender
        self._config = config or DeepfakeConfig()

    @property
    def config(self) -> DeepfakeConfig:
        """Expose config for router to check daily limits."""
        return self._config

    async def get_user_daily_cost(self, user_id: UUID) -> int:
        """Get user's deepfake detection spend today in cents."""
        return await self._repository.get_user_daily_cost(user_id)

    async def close(self) -> None:
        """Cleanup clients."""
        await self._lipinc.close()
        await self._reality_defender.close()

    async def is_cached(self, video_analysis_id: UUID, user_id: UUID) -> bool:
        """Check if a valid cached deepfake analysis exists."""
        cached = await self._repository.get_by_video_analysis_id(video_analysis_id, user_id)
        return cached is not None and self._is_cache_valid(cached.analyzed_at)

    async def analyze(
        self,
        video_analysis_id: UUID,
        user_id: UUID,
        video_url: str,
        force_refresh: bool = False,
    ) -> DeepfakeAnalysisResult:
        """Analyze video for deepfakes.

        Args:
            video_analysis_id: ID of the video_analysis record
            video_url: Presigned URL to the video
            force_refresh: Skip cache and re-analyze

        Returns:
            DeepfakeAnalysisResult with detection results
        """
        # Check cache
        if not force_refresh:
            cached = await self._repository.get_by_video_analysis_id(video_analysis_id, user_id)
            if cached and self._is_cache_valid(cached.analyzed_at):
                return DeepfakeAnalysisResult(record=cached, cached=True)

        # Cache miss — check spend limit before expensive work
        daily_cost = await self._repository.get_user_daily_cost(user_id)
        if daily_cost >= self._config.daily_spend_limit_cents:
            raise DailySpendLimitExceeded(daily_cost, self._config.daily_spend_limit_cents)

        # Run analyses in parallel
        lipinc_result, reality_result = await asyncio.gather(
            self._run_lipinc(video_url),
            self._run_reality_defender(video_url),
            return_exceptions=True,
        )

        # Handle exceptions
        lipinc_error = None
        reality_error = None

        if isinstance(lipinc_result, Exception):
            lipinc_error = str(lipinc_result)
            lipinc_result = LipSyncResult(
                score=None,
                anomaly_detected=False,
                confidence=None,
                error=lipinc_error,
            )

        if isinstance(reality_result, Exception):
            reality_error = str(reality_result)
            reality_result = RealityDefenderResult(
                score=None,
                verdict=None,
                indicators=[],
                error=reality_error,
            )

        # Compute ensemble score
        combined_score, detection_method, limitations = self._compute_ensemble(
            lipinc_result, reality_result
        )

        # Fail fast when every provider is down
        if "all_providers_unavailable" in limitations:
            raise AllProvidersUnavailableError(limitations)

        # Determine verdict
        is_deepfake = combined_score >= self._config.deepfake_threshold
        risk_level = self._score_to_risk_level(combined_score)

        # Calculate total cost and time
        total_cost = (
            RealityDefenderClient.COST_PER_SCAN_CENTS
            if reality_result.score is not None
            else 0
        ) + (
            LIPINCAnalyzer.COST_PER_ANALYSIS_CENTS
            if lipinc_result.score is not None
            else 0
        )
        total_time = lipinc_result.processing_time_ms + reality_result.processing_time_ms

        # Persist results
        record = await self._repository.create(
            video_analysis_id=video_analysis_id,
            user_id=user_id,
            lip_sync_score=lipinc_result.score,
            lip_sync_anomaly_detected=lipinc_result.anomaly_detected,
            lip_sync_confidence=lipinc_result.confidence,
            lip_sync_error=lipinc_error,
            reality_defender_score=reality_result.score,
            reality_defender_verdict=reality_result.verdict,
            reality_defender_indicators=reality_result.indicators,
            reality_defender_error=reality_error,
            combined_score=combined_score,
            is_deepfake=is_deepfake,
            risk_level=risk_level,
            detection_method=detection_method,
            limitations=limitations,
            processing_time_ms=total_time,
            cost_cents=total_cost,
        )

        if reality_result.score is not None:
            await _cost_recorder.record("reality_defender", "deepfake_scan", cost_usd=RealityDefenderClient.COST_PER_SCAN_CENTS / 100)
        if lipinc_result.score is not None:
            # Prefer actual GPU-time cost from Replicate metrics; fall back to estimate
            lipinc_cost = self._lipinc.last_cost_usd or (LIPINCAnalyzer.COST_PER_ANALYSIS_CENTS / 100)
            await _cost_recorder.record("replicate", "lipinc_analysis", cost_usd=lipinc_cost)

        return DeepfakeAnalysisResult(record=record, cached=False)

    async def _run_lipinc(self, video_url: str) -> LipSyncResult:
        """Run LIPINC analysis with error handling."""
        if not self._config.lipinc_enabled:
            return LipSyncResult(
                score=None,
                anomaly_detected=False,
                confidence=None,
                error="lipinc_disabled",
            )
        return await self._lipinc.analyze(video_url)

    async def _run_reality_defender(self, video_url: str) -> RealityDefenderResult:
        """Run Reality Defender analysis with error handling."""
        if not self._config.reality_defender_enabled:
            return RealityDefenderResult(
                score=None,
                verdict=None,
                indicators=[],
                error="reality_defender_disabled",
            )
        return await self._reality_defender.analyze(video_url)

    def _compute_ensemble(
        self,
        lipinc: LipSyncResult,
        reality: RealityDefenderResult,
    ) -> tuple[float, DetectionMethod, list[str]]:
        """Compute weighted ensemble score.

        LIPINC score: 1.0 = authentic, 0.0 = manipulated
        Reality Defender score: 1.0 = manipulated, 0.0 = authentic

        We normalize to: 1.0 = manipulated, 0.0 = authentic
        """
        limitations = []
        scores = []
        weights = []

        # Add LIPINC score (inverted: lower authenticity = higher manipulation)
        if lipinc.score is not None:
            manipulation_score = 1.0 - lipinc.score
            scores.append(manipulation_score)
            weights.append(LIPINC_WEIGHT)
        else:
            limitations.append(lipinc.error or "lipinc_unavailable")

        # Add Reality Defender score
        if reality.score is not None:
            scores.append(reality.score)
            weights.append(REALITY_DEFENDER_WEIGHT)
        else:
            limitations.append(reality.error or "reality_defender_unavailable")

        # Compute weighted average
        if not scores:
            return 0.5, DetectionMethod.ENSEMBLE, limitations + ["all_providers_unavailable"]

        if len(scores) == 1:
            method = (
                DetectionMethod.LIPINC_ONLY
                if lipinc.score is not None
                else DetectionMethod.REALITY_DEFENDER_ONLY
            )
            return scores[0], method, limitations

        total_weight = sum(weights)
        combined = sum(s * w for s, w in zip(scores, weights)) / total_weight

        return combined, DetectionMethod.ENSEMBLE, limitations

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert manipulation score to risk level."""
        if score >= 0.85:
            return RiskLevel.CRITICAL
        elif score >= 0.70:
            return RiskLevel.HIGH
        elif score >= 0.50:
            return RiskLevel.MEDIUM
        elif score >= 0.30:
            return RiskLevel.LOW
        return RiskLevel.NONE

    def _is_cache_valid(self, analyzed_at: datetime) -> bool:
        """Check if cached result is still valid."""
        ttl = timedelta(days=self._config.cache_ttl_days)
        return datetime.now(timezone.utc) - analyzed_at < ttl
