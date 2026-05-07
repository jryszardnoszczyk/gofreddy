"""Creative pattern analysis service."""

import logging
from dataclasses import dataclass
from uuid import UUID

from ..analysis.exceptions import VideoProcessingError
from ..analysis.gemini_analyzer import GeminiVideoAnalyzer
from ..schemas import CreativePatterns
from .repository import PostgresCreativePatternRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreativePatternAnalysisResult:
    """Immutable result from creative pattern service."""

    patterns: CreativePatterns
    cached: bool


class CreativePatternService:
    """Service for creative pattern analysis."""

    def __init__(
        self,
        analyzer: GeminiVideoAnalyzer,
        repository: PostgresCreativePatternRepository,
    ) -> None:
        self._analyzer = analyzer
        self._repository = repository

    async def get_creative_patterns(
        self, video_analysis_id: UUID
    ) -> CreativePatterns | None:
        """Read-only getter - returns cached patterns or None. No Gemini call.

        Used by router for cache-check-before-download and by PR-049 agent tool.
        """
        return await self._repository.get_by_analysis_id(video_analysis_id)

    async def analyze_creative_patterns(
        self,
        video_path: str,
        video_analysis_id: UUID,
        video_id: str,
        *,
        force_refresh: bool = False,
        pre_extracted_transcript: str | None = None,
    ) -> CreativePatternAnalysisResult:
        """Cache-first creative pattern analysis."""
        # 1. Check cache (unless force_refresh)
        if not force_refresh:
            cached = await self._repository.get_by_analysis_id(video_analysis_id)
            if cached is not None:
                logger.info("Creative patterns cache hit for %s", video_analysis_id)
                return CreativePatternAnalysisResult(patterns=cached, cached=True)

        # 2. Call Gemini
        logger.info("Running creative pattern analysis for video %s", video_id)
        try:
            patterns = await self._analyzer.analyze_creative_patterns(
                video_path, video_id,
                pre_extracted_transcript=pre_extracted_transcript,
            )
        except VideoProcessingError as e:
            sentinel = CreativePatterns(
                error=str(e),
                transcript_summary="Not available",
                story_arc="Not available",
                emotional_journey="Not available",
                protagonist="Not available",
                theme="Not available",
                visual_style="Not available",
                audio_style="Not available",
                scene_beat_map="Not available",
            )
            try:
                await self._repository.save(sentinel, video_analysis_id)
            except Exception:
                logger.warning("Failed to persist sentinel error record for %s", video_analysis_id, exc_info=True)
            return CreativePatternAnalysisResult(patterns=sentinel, cached=False)

        # 3. Save to repository - CHECK RETURN VALUE (brands pattern)
        saved = await self._repository.save(patterns, video_analysis_id)
        if not saved:
            logger.warning(
                "video_analysis deleted during creative pattern inference",
                extra={"video_analysis_id": str(video_analysis_id)},
            )
            # Preserve original Gemini results but annotate with error
            patterns = patterns.model_copy(
                update={"error": "orphaned_result: video_analysis deleted during inference"}
            )

        return CreativePatternAnalysisResult(patterns=patterns, cached=False)
