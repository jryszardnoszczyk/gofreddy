"""Async Gemini video analyzer."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import httpx
from google import genai
from google.genai import errors, types

from ..prompts import (
    BRAND_DETECTION_PROMPT,
    BRAND_DETECTION_SYSTEM,
    BRAND_SAFETY_PROMPT,
    CREATIVE_PATTERN_PROMPT,
    CREATIVE_PATTERN_SYSTEM,
    DEMOGRAPHICS_INFERENCE_PROMPT,
    DEMOGRAPHICS_SYSTEM_INSTRUCTION,
    SYSTEM_INSTRUCTION,
)
from ..common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..common.gemini_models import GEMINI_FLASH_LITE
from ..schemas import AudienceDemographics, BrandAnalysis, CreativePatterns, VideoAnalysis
from .compliance import _reset_compliance_fields, compute_compliance
from .exceptions import GeminiRateLimitError, VideoProcessingError

# Keys that cause Gemini "too many states" or "unsupported" errors.
_GEMINI_STRIP_KEYS = frozenset({
    "additionalProperties",
    "maxLength",
    "minLength",
    "maxItems",
    "minItems",
    "exclusiveMaximum",
    "exclusiveMinimum",
})

logger = logging.getLogger(__name__)

# All narrative fields checked after pattern extraction — reject if 3+ are empty.
_NARRATIVE_FIELDS = (
    "transcript_summary", "story_arc", "emotional_journey",
    "protagonist", "theme", "visual_style", "audio_style", "scene_beat_map",
)


def _clean_schema_for_gemini(schema: dict) -> dict:
    """Strip Pydantic JSON-schema keys that the Gemini API rejects.

    Gemini response_schema doesn't support additionalProperties and
    explodes with "too many states" when maxLength/maxItems are large.
    Pydantic still validates constraints after parsing the response.

    Also flattens ``anyOf`` from ``Optional[Literal[...]]`` into
    ``{"enum": [...], "nullable": true}`` which Gemini accepts.
    The anyOf check MUST run before the recursive dict comprehension
    so the pattern is caught intact.
    """
    if isinstance(schema, dict):
        # ── anyOf flattening (BEFORE recursive traversal) ──
        if "anyOf" in schema and len(schema["anyOf"]) == 2:
            types = schema["anyOf"]
            null_type = next((t for t in types if t.get("type") == "null"), None)
            real_type = next((t for t in types if t.get("type") != "null"), None)
            if null_type and real_type:
                result = _clean_schema_for_gemini(real_type)
                result["nullable"] = True
                return result
        elif "anyOf" in schema:
            logger.warning(
                "Unexpected anyOf with %d branches in schema",
                len(schema["anyOf"]),
            )

        return {
            k: _clean_schema_for_gemini(v)
            for k, v in schema.items()
            if k not in _GEMINI_STRIP_KEYS
        }
    if isinstance(schema, list):
        return [_clean_schema_for_gemini(item) for item in schema]
    return schema


class GeminiVideoAnalyzer:
    """Async video analyzer using native Gemini SDK async support."""

    def __init__(
        self,
        api_key: str,
        model: str = GEMINI_FLASH_LITE,
        max_retries: int = 3,
        base_delay: float = 10.0,
        max_concurrent: int = 50,
        db_pool: Any | None = None,
    ) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=300000,  # 5 minutes in ms
            ),
        )
        self._model = model
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._cleanup_tasks: set[asyncio.Task[None]] = set()
        # Lazy-initialized context caches (one per system instruction)
        self._caches: dict[str, str] = {}  # cache_key -> cached_content name
        self._db_pool = db_pool  # for versioned prompt loading

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit - cleanup resources."""
        await self._drain_cleanup_tasks()

    async def close(self) -> None:
        """Explicit close method for non-context-manager usage."""
        await self.__aexit__(None, None, None)

    def _get_or_create_cache(self, cache_key: str, system_instruction: str) -> str | None:
        """Get or create a Gemini context cache for a static system instruction.

        Returns the cache name for use in generate_content, or None on failure.
        Caches are lazily created on first use and reused for the TTL (1 hour).
        """
        caches = getattr(self, "_caches", None)
        if caches is None:
            return None
        if cache_key in caches:
            return caches[cache_key]
        try:
            cached = self._client.caches.create(
                model=self._model,
                config=types.CreateCachedContentConfig(
                    system_instruction=system_instruction,
                    ttl="3600s",
                ),
            )
            if cached and cached.name:
                self._caches[cache_key] = cached.name
                logger.info("context_cache_created key=%s name=%s", cache_key, cached.name)
                return cached.name
        except Exception:
            logger.debug("context_cache_failed key=%s", cache_key, exc_info=True)
        return None

    async def _get_system_instruction(self, prompt_name: str, fallback: str) -> str:
        """Load active prompt version from DB, fall back to static string."""
        if not os.environ.get("ENABLE_VERSIONED_PROMPTS"):
            return fallback
        if not getattr(self, "_db_pool", None):
            return fallback
        try:
            row = await self._db_pool.fetchrow(
                "SELECT content FROM prompt_versions WHERE prompt_name = $1 AND is_active = true",
                prompt_name,
            )
            if row:
                return row["content"]
        except Exception:
            logger.warning("prompt_version_load_failed", extra={"prompt": prompt_name})
        return fallback

    async def analyze_video(self, video_path: str, video_id: str) -> VideoAnalysis:
        """Full async analysis flow with semaphore only gating generation."""
        video_file = await self._upload_with_retry(Path(video_path))
        try:
            video_file = await self._wait_for_active(video_file)
            async with self._semaphore:
                return await self._generate_analysis(video_file, video_id)
        finally:
            self._schedule_cleanup(video_file)

    async def _upload_with_retry(self, path: Path) -> types.File:
        """Upload video with retry handling."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._client.aio.files.upload(file=str(path))
            except errors.ClientError as e:
                last_error = e
                if e.code == 429:
                    if attempt == self._max_retries - 1:
                        raise GeminiRateLimitError(f"Rate limited during upload after {self._max_retries} attempts")
                    max_delay = self._base_delay * (2**attempt)
                    delay = max(self._base_delay, random.uniform(0, max_delay))
                    await asyncio.sleep(delay)
                else:
                    raise VideoProcessingError(f"Upload failed: {type(e).__name__}")
            except (BrokenPipeError, ConnectionError, OSError) as e:
                last_error = e
                logger.warning(
                    "upload_pipe_error attempt=%d/%d: %s",
                    attempt + 1, self._max_retries, e,
                )
                if attempt == self._max_retries - 1:
                    raise VideoProcessingError(f"Upload failed after {self._max_retries} attempts: {type(e).__name__}: {e}")
                max_delay = self._base_delay * (2**attempt)
                delay = max(self._base_delay, random.uniform(0, max_delay))
                await asyncio.sleep(delay)
        raise VideoProcessingError(f"Upload failed: {last_error}")

    async def _wait_for_active(
        self,
        video_file: types.File,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
    ) -> types.File:
        """Poll for video processing completion."""
        elapsed = 0.0
        while video_file.state != types.FileState.ACTIVE:
            if video_file.state == types.FileState.FAILED:
                raise VideoProcessingError(f"Video processing failed: {video_file.name}")
            if elapsed >= timeout:
                raise VideoProcessingError(f"Processing timeout after {timeout}s")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if video_file.name:
                video_file = await self._client.aio.files.get(name=video_file.name)

        return video_file

    async def _generate_with_retry(
        self,
        contents: list[Any],
        video_id: str,
    ) -> VideoAnalysis:
        """Shared retry loop for video and transcript analysis."""
        system_instruction = await self._get_system_instruction("video_analysis", SYSTEM_INSTRUCTION)
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                cache_name = self._get_or_create_cache("analysis", system_instruction)
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_clean_schema_for_gemini(VideoAnalysis.model_json_schema()),
                )
                if cache_name:
                    config.cached_content = cache_name
                else:
                    config.system_instruction = system_instruction
                if GEMINI_FLASH_LITE in self._model:
                    config.thinking_config = types.ThinkingConfig(thinking_level="HIGH")
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=config,
                )
                _t_in, _t_out, _c = extract_gemini_usage(response, self._model)
                await _cost_recorder.record("gemini", "analyze_video", tokens_in=_t_in, tokens_out=_t_out, cost_usd=_c, model=self._model)

                if response.text is None:
                    raise VideoProcessingError("Empty response from Gemini")
                result = VideoAnalysis.model_validate_json(response.text)
                result.video_id = video_id
                if response.usage_metadata and response.usage_metadata.total_token_count:
                    result.token_count = response.usage_metadata.total_token_count
                return result

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "Analysis parse failure for %s (attempt %d/%d): %s",
                    video_id, attempt + 1, self._max_retries, str(e),
                )
                continue

            except errors.ClientError as e:
                last_error = e
                if e.code == 429:
                    if attempt == self._max_retries - 1:
                        raise GeminiRateLimitError(f"Rate limited during generation after {self._max_retries} attempts")
                    max_delay = self._base_delay * (2**attempt)
                    delay = max(self._base_delay, random.uniform(0, max_delay))
                    await asyncio.sleep(delay)
                else:
                    logger.warning("gemini_client_error", extra={"code": e.code, "error": str(e)})
                    raise VideoProcessingError(f"Analysis failed: {type(e).__name__}")

        if isinstance(last_error, (json.JSONDecodeError, ValueError)):
            raise VideoProcessingError(f"Analysis parse failed after {self._max_retries} attempts: {last_error}")
        raise VideoProcessingError(f"Generation failed: {last_error}")

    async def _generate_analysis(
        self,
        video_file: types.File,
        video_id: str,
    ) -> VideoAnalysis:
        """Generate analysis with structured JSON output."""
        return await self._generate_with_retry([video_file, BRAND_SAFETY_PROMPT], video_id)

    async def analyze_transcript(
        self, transcript_text: str, video_id: str, max_chars: int = 50_000
    ) -> VideoAnalysis:
        """L1: Analyze video from transcript text only (no video upload)."""
        truncated = transcript_text[:max_chars]
        contents = [
            BRAND_SAFETY_PROMPT,
            "<transcript>\n" + truncated + "\n</transcript>",
        ]
        async with self._semaphore:
            return await self._generate_with_retry(contents, video_id)

    async def start_batch_analysis(
        self,
        videos: list[dict[str, Any]],
    ) -> str:
        """Upload videos and start a Gemini Batch Job."""
        requests = []
        
        # 1. Upload all videos concurrently (limited by semaphore)
        async def _upload_and_prepare(video: dict[str, Any]) -> dict[str, Any]:
            async with self._semaphore:
                video_file = await self._upload_with_retry(Path(video["local_path"]))
                video_file = await self._wait_for_active(video_file)
                return {
                    "contents": [video_file, BRAND_SAFETY_PROMPT],
                    "config": {
                        "response_mime_type": "application/json",
                        "response_schema": _clean_schema_for_gemini(VideoAnalysis.model_json_schema()),
                        "system_instruction": SYSTEM_INSTRUCTION,
                    },
                    "metadata": {
                        "video_index": str(video["video_index"]),
                        "video_id": str(video["video_id"]),
                    }
                }

        tasks = [_upload_and_prepare(v) for v in videos]
        requests = await asyncio.gather(*tasks)

        # 2. Submit batch
        try:
            batch = await self._client.aio.batches.create(
                model=self._model,
                src=requests
            )
            if not batch.name:
                raise VideoProcessingError("Batch creation returned no job name")
            return batch.name
        except errors.ClientError as e:
            raise VideoProcessingError(f"Batch creation failed: {e}")

    async def poll_batch_analysis(self, batch_job_id: str) -> dict[str, Any]:
        """Poll a running Batch Job. Returns state and results if done."""
        try:
            batch = await self._client.aio.batches.get(name=batch_job_id)
            state_str = str(batch.state)
            
            result: dict[str, Any] = {"state": state_str, "error": None, "results": []}

            if "FAILED" in state_str.upper():
                result["error"] = batch.error.message if getattr(batch, "error", None) else "Batch failed."
            elif "SUCCEEDED" in state_str.upper():
                output_uri = getattr(batch, "output_uri", None)
                if output_uri:
                    if not output_uri.startswith("https://storage.googleapis.com/"):
                        raise VideoProcessingError("Unexpected batch output URI domain")
                    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as http_client:
                        response = await http_client.get(output_uri)
                        response.raise_for_status()

                        for line in response.text.strip().split("\n"):
                            if not line.strip():
                                continue
                            data = json.loads(line)

                            metadata = data.get("request", {}).get("metadata", {})
                            video_index = int(metadata.get("video_index", -1))
                            video_id = metadata.get("video_id", "")

                            response_body = data.get("response", {}).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

                            if response_body:
                                try:
                                    parsed = VideoAnalysis.model_validate_json(response_body)
                                    parsed.video_id = video_id
                                    # Compute compliance scores for batch items
                                    if parsed.sponsored_content:
                                        try:
                                            compute_compliance(parsed.sponsored_content)
                                        except Exception:
                                            logger.warning("Compliance scoring failed for batch item", exc_info=True)
                                            _reset_compliance_fields(parsed.sponsored_content)
                                    result["results"].append({
                                        "video_index": video_index,
                                        "status": "complete",
                                        "result": parsed.model_dump(),
                                        "cached": False,
                                        "cost_usd": 0.0,  # Batch cost calculated from token_count at settlement
                                        "token_count": data.get("response", {}).get("usageMetadata", {}).get("totalTokenCount", 0)
                                    })
                                except Exception as e:
                                    logger.error("Batch output parse failed: %s", e)
                                    result["results"].append({
                                        "video_index": video_index,
                                        "status": "failed",
                                        "error": "Failed to parse analysis output"
                                    })
                            else:
                                result["results"].append({
                                    "video_index": video_index,
                                    "status": "failed",
                                    "error": "Empty response body"
                                })
            return result
        except Exception as e:
            raise VideoProcessingError(f"Failed to poll batch: {e}")

    async def _cleanup_file(self, video_file: types.File) -> None:
        """Delete uploaded file from Gemini storage."""
        if video_file.name:
            try:
                await self._client.aio.files.delete(name=video_file.name)
            except errors.APIError:
                pass  # Gemini auto-cleans after 48h

    async def analyze_demographics(
        self, video_path: str, video_id: str
    ) -> AudienceDemographics:
        """Analyze video for audience demographics inference.

        Args:
            video_path: Path to video file (local path or GCS URI)
            video_id: Unique identifier for the video

        Returns:
            AudienceDemographics with five dimensions and confidence scores
        """
        import time

        start_time = time.time()
        video_file = await self._upload_with_retry(Path(video_path))
        try:
            video_file = await self._wait_for_active(video_file)
            async with self._semaphore:
                result = await self._generate_demographics(video_file, video_id)
            result.processing_time_seconds = time.time() - start_time
            return result
        finally:
            self._schedule_cleanup(video_file)

    async def _generate_demographics(
        self,
        video_file: types.File,
        video_id: str,
    ) -> AudienceDemographics:
        """Generate demographics analysis with structured JSON output."""
        system_instruction = await self._get_system_instruction("demographics", DEMOGRAPHICS_SYSTEM_INSTRUCTION)
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                cache_name = self._get_or_create_cache("demographics", system_instruction)
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_clean_schema_for_gemini(AudienceDemographics.model_json_schema()),
                )
                if cache_name:
                    config.cached_content = cache_name
                else:
                    config.system_instruction = system_instruction
                if GEMINI_FLASH_LITE in self._model:
                    config.thinking_config = types.ThinkingConfig(thinking_level="HIGH")
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=[video_file, DEMOGRAPHICS_INFERENCE_PROMPT],
                    config=config,
                )
                _t_in, _t_out, _c = extract_gemini_usage(response, self._model)
                await _cost_recorder.record("gemini", "infer_demographics", tokens_in=_t_in, tokens_out=_t_out, cost_usd=_c, model=self._model)

                if response.text is None:
                    raise VideoProcessingError("Empty response from Gemini")
                result = AudienceDemographics.model_validate_json(response.text)
                result = AudienceDemographics(
                    video_id=video_id,
                    interests=result.interests,
                    age_distribution=result.age_distribution,
                    gender_distribution=result.gender_distribution,
                    geography=result.geography,
                    income_level=result.income_level,
                    overall_confidence=result.overall_confidence,
                    processing_time_seconds=result.processing_time_seconds,
                    token_count=(
                        response.usage_metadata.total_token_count
                        if response.usage_metadata and response.usage_metadata.total_token_count
                        else 0
                    ),
                    error=result.error,
                )
                return result

            except errors.ClientError as e:
                last_error = e
                if e.code == 429:
                    if attempt == self._max_retries - 1:
                        raise GeminiRateLimitError(
                            f"Rate limited during demographics generation after {self._max_retries} attempts"
                        )
                    max_delay = self._base_delay * (2**attempt)
                    delay = max(self._base_delay, random.uniform(0, max_delay))
                    await asyncio.sleep(delay)
                else:
                    raise VideoProcessingError(f"Demographics generation failed: {type(e).__name__}")

        raise VideoProcessingError(f"Demographics generation failed: {last_error}")

    async def analyze_brands(self, video_path: str, video_id: str) -> BrandAnalysis:
        """Analyze video for brand mentions and sentiment.

        Args:
            video_path: Path to video file (local path or GCS URI)
            video_id: Unique identifier for the video

        Returns:
            BrandAnalysis with brand mentions, sentiment, and confidence scores
        """
        import time

        start_time = time.time()
        video_file = await self._upload_with_retry(Path(video_path))
        try:
            video_file = await self._wait_for_active(video_file)
            async with self._semaphore:
                result = await self._generate_brand_analysis(video_file, video_id)
            result = BrandAnalysis(
                video_id=video_id,
                brand_mentions=result.brand_mentions,
                primary_brand=result.primary_brand,
                overall_sentiment=result.overall_sentiment,
                has_sponsorship_signals=result.has_sponsorship_signals,
                sponsoring_brand=result.sponsoring_brand,
                overall_confidence=result.overall_confidence,
                processing_time_seconds=time.time() - start_time,
                token_count=result.token_count,
                error=result.error,
            )
            return result
        finally:
            self._schedule_cleanup(video_file)

    def _schedule_cleanup(self, video_file: types.File) -> None:
        """Run Gemini file deletion in background and track task lifecycle."""
        task = asyncio.create_task(self._cleanup_file(video_file))
        self._cleanup_tasks.add(task)

        def _drop_task(done_task: asyncio.Task[None]) -> None:
            self._cleanup_tasks.discard(done_task)

        task.add_done_callback(_drop_task)

    async def _drain_cleanup_tasks(self) -> None:
        """Await any pending background cleanup tasks."""
        if not self._cleanup_tasks:
            return
        tasks = list(self._cleanup_tasks)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _generate_brand_analysis(
        self,
        video_file: types.File,
        video_id: str,
    ) -> BrandAnalysis:
        """Generate brand analysis with structured JSON output."""
        system_instruction = await self._get_system_instruction("brand_detection", BRAND_DETECTION_SYSTEM)
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                cache_name = self._get_or_create_cache("brand_detection", system_instruction)
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_clean_schema_for_gemini(BrandAnalysis.model_json_schema()),
                )
                if cache_name:
                    config.cached_content = cache_name
                else:
                    config.system_instruction = system_instruction
                if GEMINI_FLASH_LITE in self._model:
                    config.thinking_config = types.ThinkingConfig(thinking_level="MINIMAL")
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=[video_file, BRAND_DETECTION_PROMPT],
                    config=config,
                )
                _t_in, _t_out, _c = extract_gemini_usage(response, self._model)
                await _cost_recorder.record("gemini", "analyze_brands", tokens_in=_t_in, tokens_out=_t_out, cost_usd=_c, model=self._model)

                if response.text is None:
                    raise VideoProcessingError("Empty response from Gemini")
                result = BrandAnalysis.model_validate_json(response.text)
                if response.usage_metadata and response.usage_metadata.total_token_count:
                    result = BrandAnalysis(
                        **{
                            **result.model_dump(),
                            "token_count": response.usage_metadata.total_token_count,
                        }
                    )
                return result

            except errors.ClientError as e:
                last_error = e
                if e.code == 429:
                    if attempt == self._max_retries - 1:
                        raise GeminiRateLimitError(
                            f"Rate limited during brand analysis after {self._max_retries} attempts"
                        )
                    max_delay = self._base_delay * (2**attempt)
                    delay = max(self._base_delay, random.uniform(0, max_delay))
                    await asyncio.sleep(delay)
                else:
                    raise VideoProcessingError(f"Brand analysis failed: {type(e).__name__}")

        raise VideoProcessingError(f"Brand analysis failed: {last_error}")

    async def analyze_creative_patterns(
        self,
        video_path: str,
        video_id: str,
        *,
        creator_context: list[CreativePatterns] | None = None,
        pre_extracted_transcript: str | None = None,
    ) -> CreativePatterns:
        """Analyze video for creative patterns (hook, narrative, CTA, pacing, music, text).

        Args:
            video_path: Path to video file (local path or GCS URI)
            video_id: Unique identifier for the video
            creator_context: Existing patterns from other videos by the same creator, used to guide extraction
            pre_extracted_transcript: Optional transcript text (e.g. from yt-dlp auto-subs) to supplement audio analysis

        Returns:
            CreativePatterns with pattern classification and confidence scores
        """
        import time

        start_time = time.time()
        video_file = await self._upload_with_retry(Path(video_path))
        try:
            video_file = await self._wait_for_active(video_file)
            async with self._semaphore:
                result = await self._generate_creative_patterns(
                    video_file, video_id,
                    creator_context=creator_context,
                    pre_extracted_transcript=pre_extracted_transcript,
                )

            # Check all 8 narrative fields — reject if 3+ are empty
            empty_fields = [f for f in _NARRATIVE_FIELDS if getattr(result, f, "") in ("", "Not available")]
            if len(empty_fields) >= 3:
                logger.warning(
                    "Pattern extraction for %s has %d/8 empty narrative fields (%s) — rejecting",
                    video_id, len(empty_fields), ", ".join(empty_fields),
                )
                raise VideoProcessingError(
                    f"Pattern extraction for {video_id}: {len(empty_fields)}/8 narrative fields empty"
                )

            result = CreativePatterns(
                **{
                    **result.model_dump(),
                    "processing_time_seconds": time.time() - start_time,
                    "token_count": result.token_count,
                }
            )
            return result
        finally:
            self._schedule_cleanup(video_file)

    async def _generate_creative_patterns(
        self,
        video_file: types.File,
        video_id: str,
        *,
        creator_context: list[CreativePatterns] | None = None,
        pre_extracted_transcript: str | None = None,
    ) -> CreativePatterns:
        """Generate creative pattern analysis with structured JSON output."""
        system_instruction = await self._get_system_instruction("creative_patterns", CREATIVE_PATTERN_SYSTEM)
        last_error: Exception | None = None

        # Build prompt with optional creator context and pre-extracted transcript
        prompt_parts: list = [video_file]
        if pre_extracted_transcript:
            prompt_parts.append(
                f"## Pre-extracted Transcript\n{pre_extracted_transcript[:5000]}\n\n"
                "Use this to supplement your audio analysis.\n"
            )
        if creator_context:
            context_summary = "\n".join(
                f"- Video: visual_style={p.visual_style or 'N/A'}, audio_style={p.audio_style or 'N/A'}"
                for p in creator_context
            )
            prompt_parts.append(f"## Creator Context (other videos by this creator)\n{context_summary}\n\n")
        prompt_parts.append(CREATIVE_PATTERN_PROMPT)

        for attempt in range(self._max_retries):
            try:
                cache_name = self._get_or_create_cache("creative_patterns", system_instruction)
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_clean_schema_for_gemini(CreativePatterns.model_json_schema()),
                )
                if cache_name:
                    config.cached_content = cache_name
                else:
                    config.system_instruction = system_instruction
                if GEMINI_FLASH_LITE in self._model:
                    config.thinking_config = types.ThinkingConfig(thinking_level="MINIMAL")
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=prompt_parts,
                    config=config,
                )
                _t_in, _t_out, _c = extract_gemini_usage(response, self._model)
                await _cost_recorder.record("gemini", "analyze_creative_patterns", tokens_in=_t_in, tokens_out=_t_out, cost_usd=_c, model=self._model)

                if response.text is None:
                    raise VideoProcessingError("Empty response from Gemini")

                result = CreativePatterns.model_validate_json(response.text)
                if response.usage_metadata and response.usage_metadata.total_token_count:
                    result = CreativePatterns(
                        **{
                            **result.model_dump(),
                            "token_count": response.usage_metadata.total_token_count,
                        }
                    )
                return result

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "Creative patterns parse failure for %s (attempt %d/%d): %s",
                    video_id,
                    attempt + 1,
                    self._max_retries,
                    str(e),
                )
                continue

            except errors.ClientError as e:
                last_error = e
                if e.code == 429:
                    if attempt == self._max_retries - 1:
                        raise GeminiRateLimitError(
                            f"Rate limited during creative analysis after {self._max_retries} attempts"
                        )
                    max_delay = self._base_delay * (2**attempt)
                    delay = max(self._base_delay, random.uniform(0, max_delay))
                    await asyncio.sleep(delay)
                else:
                    raise VideoProcessingError(f"Creative analysis failed: {type(e).__name__}")

        # All retries exhausted — raise instead of returning broken fallback
        if isinstance(last_error, (json.JSONDecodeError, ValueError)):
            raise VideoProcessingError(f"Creative pattern extraction failed after retries: {last_error}")
        raise VideoProcessingError(f"Creative analysis failed: {last_error}")

    def __repr__(self) -> str:
        """Hide sensitive info in repr."""
        return f"GeminiVideoAnalyzer(model='{self._model}')"
