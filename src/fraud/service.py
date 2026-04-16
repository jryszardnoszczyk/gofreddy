"""Fraud detection service orchestrator with Gemini bot detection."""

from __future__ import annotations

import asyncio
import html
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from google import genai
from google.genai import errors, types

from ..common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..common.sanitize import escape_braces
from .analyzers import EngagementAnalyzer, FollowerAnalyzer
from .config import FraudDetectionConfig
from .models import (
    AQSResult,
    BotCommentAnalysis,
    FraudAnalysisRecord,
    InsufficientDataError,
)
from .repository import PostgresFraudRepository

if TYPE_CHECKING:
    from ..fetcher.models import CommentData, CreatorStats, FollowerProfile


BOT_COMMENT_DETECTION_PROMPT = """
Analyze these comments from a social media video for bot/spam indicators.

VIDEO CONTEXT:
- Title: {video_title}
- Content type: {content_type}
- View count: {view_count}

COMMENTS TO ANALYZE:
{comments_json}

For each comment, identify these bot/spam indicators:
1. Generic praise without specific content reference ("Great!", "Love it!", "Amazing!")
2. Emoji-only comments with no text
3. Promotional links or @mentions unrelated to video
4. Repetitive patterns (same phrasing across comments)
5. Completely irrelevant to video content
6. Broken grammar typical of bot-generated text

Return JSON with this exact structure:
{{
  "total_analyzed": <int>,
  "bot_like_count": <int>,
  "bot_ratio": <float 0.0-1.0>,
  "confidence": "low" | "medium" | "high",
  "patterns_detected": ["list of pattern types found"],
  "suspicious_examples": [
    {{"text": "comment text", "reason": "why suspicious"}}
  ]
}}

Focus on accuracy over recall - only flag comments with clear bot indicators.
"""


@dataclass(frozen=True, slots=True)
class FraudAnalysisResult:
    """Result from fraud detection service."""

    record: FraudAnalysisRecord
    cached: bool


class FraudDetectionService:
    """Orchestrates fraud detection analysis.

    Coordinates follower analysis, engagement analysis, and bot comment
    detection via Gemini to produce comprehensive fraud assessment.
    """

    def __init__(
        self,
        repository: PostgresFraudRepository,
        config: FraudDetectionConfig | None = None,
    ) -> None:
        self._repository = repository
        self._config = config or FraudDetectionConfig()
        self._follower_analyzer = FollowerAnalyzer(
            min_sample_size=self._config.min_follower_sample
        )
        self._engagement_analyzer = EngagementAnalyzer()

        # Initialize Gemini client
        self._gemini_client = genai.Client(
            api_key=self._config.gemini_api_key.get_secret_value(),
            http_options=types.HttpOptions(timeout=60000),  # 60s for comment analysis
        )

    async def close(self) -> None:
        """Cleanup resources."""
        # Gemini client doesn't need explicit cleanup
        pass

    async def get_by_id(self, analysis_id: UUID, user_id: UUID | None = None) -> FraudAnalysisRecord | None:
        """Retrieve fraud analysis by ID, with optional ownership check."""
        if user_id is not None:
            return await self._repository.get_by_id_and_user(analysis_id, user_id)
        return await self._repository.get_by_id(analysis_id)

    async def analyze(
        self,
        platform: Literal["tiktok", "instagram", "youtube"],
        username: str,
        followers: list[FollowerProfile],
        comments: list[CommentData],
        stats: CreatorStats,
        *,
        force_refresh: bool = False,
        creator_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> FraudAnalysisResult:
        """Perform comprehensive fraud analysis.

        Args:
            platform: Platform being analyzed
            username: Creator username
            followers: Sample of follower profiles
            comments: Recent comments to analyze
            stats: Creator profile stats
            force_refresh: Bypass cache if True
            creator_id: Optional creator UUID

        Returns:
            FraudAnalysisResult with record and cache status
        """
        cache_key = self._generate_cache_key(platform, username)

        # Check cache unless force refresh
        if not force_refresh:
            cached = await self._repository.get_by_cache_key(cache_key)
            if cached:
                return FraudAnalysisResult(record=cached, cached=True)

        # Run analyses in parallel
        follower_result, engagement_result, bot_analysis = await self._run_analyses(
            platform=platform,
            followers=followers,
            comments=comments,
            stats=stats,
        )

        # Calculate component scores
        audience_quality_score = self._calculate_audience_quality_score(follower_result)
        engagement_score = self._engagement_analyzer.calculate_engagement_score(
            engagement_rate=engagement_result[0],
            follower_count=stats.follower_count,
            platform=platform,
        )
        comment_score = self._calculate_comment_score(bot_analysis)

        # Calculate AQS (3 components: engagement, audience quality, comment authenticity)
        aqs = AQSResult.calculate(
            engagement_score=engagement_score,
            audience_quality_score=audience_quality_score,
            comment_authenticity_score=comment_score,
        )

        # Create and save record
        record = FraudAnalysisRecord.create(
            platform=platform,
            username=username,
            cache_key=cache_key,
            aqs=aqs,
            follower_result=follower_result,
            engagement_rate=engagement_result[0],
            engagement_tier=engagement_result[1],
            engagement_anomaly=engagement_result[2],
            bot_analysis=bot_analysis,
            creator_id=creator_id,
            model_version=self._config.model_version,
            cache_ttl_days=self._config.cache_ttl_days,
        )

        await self._repository.save(record, user_id=user_id)

        return FraudAnalysisResult(record=record, cached=False)

    async def _run_analyses(
        self,
        platform: Literal["tiktok", "instagram", "youtube"],
        followers: list[FollowerProfile],
        comments: list[CommentData],
        stats: CreatorStats,
    ) -> tuple:
        """Run all analyses in parallel with exception handling."""

        results = await asyncio.gather(
            self._analyze_followers(platform, followers),
            self._analyze_engagement(platform, stats),
            self._analyze_comments(comments, stats),
            return_exceptions=True,
        )

        # Handle exceptions from parallel fetches
        follower_result = results[0] if not isinstance(results[0], BaseException) else None
        engagement_result = (
            results[1]
            if not isinstance(results[1], BaseException)
            else (0.0, "unknown", None)
        )
        bot_analysis = results[2] if not isinstance(results[2], BaseException) else None

        return follower_result, engagement_result, bot_analysis

    async def _analyze_followers(
        self,
        platform: Literal["tiktok", "instagram", "youtube"],
        followers: list[FollowerProfile],
    ):
        """Analyze followers for fake indicators."""
        try:
            return self._follower_analyzer.analyze(followers, platform)
        except InsufficientDataError:
            return None

    async def _analyze_engagement(
        self,
        platform: Literal["tiktok", "instagram", "youtube"],
        stats: CreatorStats,
    ) -> tuple[float, str, object | None]:
        """Analyze engagement patterns."""
        # Calculate engagement rate
        if stats.follower_count and stats.follower_count > 0:
            avg_engagement = (stats.avg_likes or 0) + (stats.avg_comments or 0)
            engagement_rate = (avg_engagement / stats.follower_count) * 100
        else:
            engagement_rate = 0.0

        tier, anomaly = self._engagement_analyzer.analyze(
            engagement_rate=engagement_rate,
            follower_count=stats.follower_count or 0,
            platform=platform,
        )

        return engagement_rate, tier, anomaly

    async def _analyze_comments(
        self,
        comments: list[CommentData],
        stats: CreatorStats,
    ) -> BotCommentAnalysis | None:
        """Analyze comments for bot indicators using Gemini."""
        if len(comments) < self._config.min_comments_for_analysis:
            return None

        # Limit comments to analyze
        comments_to_analyze = comments[: self._config.max_comments_to_analyze]

        # Sanitize content for prompt (prevent injection)
        video_title = self._sanitize_for_prompt(stats.display_name or "Unknown")
        comments_json = self._format_comments_for_prompt(comments_to_analyze)

        prompt = BOT_COMMENT_DETECTION_PROMPT.format(
            video_title=escape_braces(video_title),
            content_type="social media video",
            view_count=stats.total_views or 0,
            comments_json=escape_braces(comments_json),
        )

        try:
            return await self._call_gemini_for_bot_analysis(prompt)
        except Exception:
            # Graceful degradation - return None if Gemini fails
            return None

    async def _call_gemini_for_bot_analysis(
        self,
        prompt: str,
    ) -> BotCommentAnalysis:
        """Call Gemini API for bot comment analysis with retry."""
        import json

        for attempt in range(self._config.gemini_max_retries):
            try:
                response = await self._gemini_client.aio.models.generate_content(
                    model=self._config.gemini_model,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                t_in, t_out, c = extract_gemini_usage(response, self._config.gemini_model)
                await _cost_recorder.record("gemini", "fraud_synthesis", tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=self._config.gemini_model)

                if response.text is None:
                    raise ValueError("Empty response from Gemini")

                data = json.loads(response.text)

                return BotCommentAnalysis(
                    total_analyzed=data.get("total_analyzed", 0),
                    bot_like_count=data.get("bot_like_count", 0),
                    bot_ratio=data.get("bot_ratio", 0.0),
                    confidence=data.get("confidence", "low"),
                    patterns_detected=data.get("patterns_detected", []),
                    suspicious_examples=data.get("suspicious_examples", []),
                )

            except errors.ClientError as e:
                if e.code == 429:
                    if attempt == self._config.gemini_max_retries - 1:
                        raise
                    delay = self._config.gemini_base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

        raise RuntimeError("Gemini bot analysis failed after retries")

    def _sanitize_for_prompt(self, text: str) -> str:
        """Sanitize text to prevent prompt injection."""
        # Escape HTML entities
        text = html.escape(text)
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        # Truncate to reasonable length
        return text[:500]

    def _format_comments_for_prompt(self, comments: list[CommentData]) -> str:
        """Format comments as JSON for prompt."""
        import json

        formatted = []
        for c in comments:
            formatted.append(
                {
                    "text": self._sanitize_for_prompt(c.text),
                    "username": self._sanitize_for_prompt(c.username),
                    "likes": c.like_count or 0,
                }
            )
        return json.dumps(formatted, indent=2)

    def _calculate_audience_quality_score(self, follower_result) -> float:
        """Calculate audience quality score from follower analysis."""
        if follower_result is None:
            return 50.0  # Default if insufficient data

        # Score is inverse of fake percentage
        return max(0.0, 100.0 - follower_result.fake_follower_percentage)

    def _calculate_comment_score(self, bot_analysis: BotCommentAnalysis | None) -> float:
        """Calculate comment authenticity score from bot analysis."""
        if bot_analysis is None:
            return 50.0  # Default if insufficient data

        # Score is inverse of bot ratio (scaled to 0-100)
        return max(0.0, (1.0 - bot_analysis.bot_ratio) * 100)

    async def is_cached(self, platform: str, username: str) -> bool:
        """Check if a fresh analysis exists in cache."""
        cache_key = self._generate_cache_key(platform, username)
        return await self._repository.get_by_cache_key(cache_key) is not None

    def _generate_cache_key(
        self, platform: Literal["tiktok", "instagram", "youtube"], username: str
    ) -> str:
        """Generate cache key for fraud analysis."""
        return f"fraud:{platform}:{username}:v{self._config.model_version}"
