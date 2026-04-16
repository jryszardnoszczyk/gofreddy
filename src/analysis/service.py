"""Analysis service with tiered caching."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from ..common.enums import Platform
from ..prompts import BRAND_SAFETY_PROMPT, SYSTEM_INSTRUCTION
from ..schemas import ModerationDetection, VideoAnalysis
from ..storage.r2_storage import VideoStorage
from .compliance import _reset_compliance_fields, compute_compliance
from .config import LaneRoutingSettings
from .exceptions import VideoProcessingError
from .gemini_analyzer import GeminiVideoAnalyzer
from .lane_selector import AnalysisLane, score_transcript_quality, select_lane
from .models import VideoAnalysisRecord
from .repository import PostgresAnalysisRepository

logger = logging.getLogger(__name__)

VALID_VIDEO_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

# Compute once at module level (both are module-level constants).
# Hash BOTH prompts: SYSTEM_INSTRUCTION controls behavioral framing,
# BRAND_SAFETY_PROMPT contains the actual moderation taxonomy (80 GARM classes,
# sponsored detection rules, etc.) which is far more likely to change.
_PROMPT_HASH = hashlib.sha256(
    (SYSTEM_INSTRUCTION + BRAND_SAFETY_PROMPT).encode()
).hexdigest()[:8]

# Core 21 classes that all tiers receive (original PR-009 classes)
CORE_MODERATION_CLASSES = frozenset([
    "adult_sexual",
    "nudity",
    "violence_graphic",
    "violence_mild",
    "gore",
    "hate_speech",
    "discrimination",
    "harassment",
    "profanity_strong",
    "profanity_mild",
    "drugs_illegal",
    "alcohol_excessive",
    "tobacco",
    "terrorism",
    "self_harm",
    "child_safety",
    "political",
    "controversial",
    "misinformation",
    "dangerous_activities",
    "spam",
])


def filter_moderation_for_tier(
    moderation_flags: list[ModerationDetection],
    tier_moderation_count: int,
) -> list[ModerationDetection]:
    """Filter moderation flags based on tier's allowed class count.

    Args:
        moderation_flags: Full 80-class moderation results
        tier_moderation_count: Number of classes tier can access (21 or 80)

    Returns:
        Filtered list for tier (core 21 or full 80)
    """
    if tier_moderation_count >= 80:
        return moderation_flags

    # Filter to core 21 classes
    return [
        flag
        for flag in moderation_flags
        if flag.moderation_class.value in CORE_MODERATION_CLASSES
    ]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Immutable result from analysis service."""

    analysis: VideoAnalysis
    cached: bool
    cost_usd: float
    record_id: UUID
    lane: AnalysisLane | None = None  # None for cached results


class AnalysisService:
    """Video analysis with caching."""

    ANALYSIS_VERSION = 2  # Bumped for 80-class moderation expansion

    def __init__(
        self,
        analyzer: GeminiVideoAnalyzer,
        repository: PostgresAnalysisRepository,
        storage: VideoStorage,
        lane_settings: LaneRoutingSettings | None = None,
        *,
        skip_persistence: bool = False,
        supabase: Any | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._repository = repository
        self._storage = storage
        self._lane_settings = lane_settings or LaneRoutingSettings()
        self._skip_persistence = skip_persistence
        self._supabase = supabase

    async def get_by_id(self, analysis_id: UUID) -> VideoAnalysisRecord | None:
        """Retrieve analysis by ID."""
        return await self._repository.get_by_id(analysis_id)

    async def analyze(
        self,
        platform: Platform,
        video_id: str,
        video_uuid: UUID,
        force_refresh: bool = False,
        user_id: UUID | None = None,
        transcript_text: str | None = None,
        duration_seconds: int | None = None,
        title: str | None = None,
    ) -> AnalysisResult:
        """Analyze video with cache check."""
        self._validate_video_id(video_id)
        cache_key = self._generate_cache_key(platform, video_id)

        if not force_refresh and not self._skip_persistence:
            cached = await self._repository.get_by_cache_key(cache_key)
            if cached:
                if user_id is not None:
                    await self._repository.grant_user_access(cached.id, user_id)
                return AnalysisResult(
                    analysis=cached.to_video_analysis(),
                    cached=True,
                    cost_usd=0.0,
                    record_id=cached.id,
                )

        return await self._perform_analysis(
            platform=platform,
            video_id=video_id,
            video_uuid=video_uuid,
            cache_key=cache_key,
            user_id=user_id,
            transcript_text=transcript_text,
            duration_seconds=duration_seconds,
            title=title,
        )

    async def _perform_analysis(
        self,
        platform: Platform,
        video_id: str,
        video_uuid: UUID,
        cache_key: str,
        user_id: UUID | None = None,
        transcript_text: str | None = None,
        duration_seconds: int | None = None,
        title: str | None = None,
    ) -> AnalysisResult:
        """Execute Gemini analysis via L1 (transcript) or L2 (video) lane."""
        # 1. Lane decision (before any I/O)
        transcript_quality = (
            score_transcript_quality(transcript_text, duration_seconds)
            if transcript_text
            else None
        )

        lane = select_lane(
            transcript_available=transcript_text is not None,
            transcript_quality=transcript_quality,
            quality_threshold=self._lane_settings.quality_threshold,
            flag_enabled=self._lane_settings.transcript_first_enabled,
        )

        # 2. Log lane decision for observability
        logger.info(
            "lane_decision",
            extra={
                "platform": platform.value,
                "video_id": video_id,
                "lane": lane.value,
                "transcript_available": transcript_text is not None,
                "transcript_quality": transcript_quality,
                "quality_threshold": self._lane_settings.quality_threshold,
                "flag_enabled": self._lane_settings.transcript_first_enabled,
            },
        )

        # 3. Execute analysis via selected lane
        if lane == AnalysisLane.L1_TRANSCRIPT_FIRST:
            if transcript_text is None:
                raise VideoProcessingError("L1 lane selected but transcript_text is None")
            analysis = await self._analyzer.analyze_transcript(
                transcript_text, video_id
            )
        else:
            temp_path = await self._storage.download_to_temp(platform, video_id)
            try:
                analysis = await self._analyzer.analyze_video(
                    str(temp_path), video_id
                )
            finally:
                Path(temp_path).unlink(missing_ok=True)

        # 4. Compliance scoring (unchanged)
        if analysis.sponsored_content:
            try:
                compute_compliance(analysis.sponsored_content)
            except Exception:
                logger.warning(
                    "Compliance scoring failed for %s:%s, resetting fields to null",
                    platform, video_id, exc_info=True,
                )
                _reset_compliance_fields(analysis.sponsored_content)

        cost = self._estimate_cost(analysis)

        # Emit quality signals for low-confidence or inconsistent results
        if self._supabase and user_id:
            import asyncio
            from ..feedback import record_error_signal

            if hasattr(analysis, "overall_confidence") and analysis.overall_confidence is not None:
                if analysis.overall_confidence < 0.4:
                    asyncio.create_task(record_error_signal(
                        self._supabase, tenant_id=user_id, signal_type="low_confidence",
                        text=f"Analysis confidence {analysis.overall_confidence:.2f} for {platform.value}:{video_id}",
                        context={"confidence": analysis.overall_confidence, "platform": platform.value},
                    ))
            if (
                analysis.moderation_flags is not None
                and len(analysis.moderation_flags) == 0
                and hasattr(analysis, "overall_safe")
                and analysis.overall_safe is False
            ):
                asyncio.create_task(record_error_signal(
                    self._supabase, tenant_id=user_id, signal_type="inconsistent_result",
                    text=f"No moderation flags but overall_safe=False for {platform.value}:{video_id}",
                ))

        if self._skip_persistence:
            from uuid import NAMESPACE_URL, uuid5

            return AnalysisResult(
                analysis=analysis,
                cached=False,
                cost_usd=0.0,
                record_id=uuid5(NAMESPACE_URL, cache_key),
                lane=lane,
            )

        record = VideoAnalysisRecord.from_analysis(
            analysis=analysis,
            video_uuid=video_uuid,
            cache_key=cache_key,
            model_version=str(self.ANALYSIS_VERSION),
            analysis_cost_usd=cost,
            title=title,
        )
        record = await self._repository.save(record)
        if user_id is not None:
            await self._repository.grant_user_access(record.id, user_id)

        return AnalysisResult(
            analysis=analysis,
            cached=False,
            cost_usd=cost,
            record_id=record.id,
            lane=lane,
        )

    def _validate_video_id(self, video_id: str) -> None:
        """Validate video_id format to prevent injection."""
        if not VALID_VIDEO_ID.match(video_id):
            raise ValueError(f"Invalid video_id format: {video_id}")

    async def get_cached(self, platform: Platform, video_id: str, video_uuid: "UUID") -> "AnalysisResult | None":
        """Check cache and return cached result if available."""
        if self._skip_persistence:
            return None
        self._validate_video_id(video_id)
        cache_key = self._generate_cache_key(platform, video_id)
        cached = await self._repository.get_by_cache_key(cache_key)
        if cached:
            return AnalysisResult(
                analysis=cached.to_video_analysis(),
                cached=True,
                cost_usd=0.0,
                record_id=cached.id,
            )
        return None

    def _generate_cache_key(self, platform: Platform, video_id: str) -> str:
        """Generate cache key with version and prompt hash for invalidation."""
        return f"{platform.value}:{video_id}:v{self.ANALYSIS_VERSION}:ph{_PROMPT_HASH}"

    def _estimate_cost(self, analysis: VideoAnalysis) -> float:
        """Estimate cost from token count (Gemini 3 Flash pricing).

        Uses total_token_count with a weighted blended rate. For video analysis
        calls, input tokens (video frames) vastly dominate output (~85-90% input),
        so the blended rate skews toward the input rate.

        Gemini 3 Flash rates (March 2026):
        - Input (text/image/video): $0.50/M tokens
        - Output (incl. thinking):  $3.00/M tokens
        - Blended estimate:         $0.875/M tokens (~85% input, 15% output)
        """
        if not analysis.token_count:
            return 0.0
        # Blended rate: 0.85 * $0.50 + 0.15 * $3.00 = $0.875/M
        return (analysis.token_count / 1_000_000) * 0.875

    async def start_batch(self, videos: list[dict[str, Any]]) -> str:
        """Upload videos and start batch job."""
        prepared_videos = []
        for v in videos:
            platform = Platform(v["platform"])
            temp_path = await self._storage.download_to_temp(platform, v["video_id"])
            prepared_videos.append({
                "local_path": str(temp_path),
                "video_id": v["video_id"],
                "video_index": v["video_index"],
            })
            
        try:
            return await self._analyzer.start_batch_analysis(prepared_videos)
        finally:
            for p in prepared_videos:
                Path(p["local_path"]).unlink(missing_ok=True)

    async def poll_batch(self, batch_job_id: str) -> dict[str, Any]:
        """Poll Gemini for batch job status and retrieve results if complete."""
        return await self._analyzer.poll_batch_analysis(batch_job_id)
