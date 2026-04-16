"""Shared fixtures for validation spikes."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pytest
from google.genai import types
from pydantic import BaseModel

from src.analysis.gemini_analyzer import _clean_schema_for_gemini

logger = logging.getLogger(__name__)


class SpikeRunner:
    """Lightweight wrapper around GeminiVideoAnalyzer for spike tests.

    Reuses the analyzer's client, upload, wait, and cleanup infrastructure
    but allows custom prompts and schemas for validation spikes.
    """

    def __init__(self, analyzer: Any) -> None:
        self._analyzer = analyzer

    async def run_video(
        self,
        video_path: Path,
        prompt: str,
        system: str,
        schema_cls: type[BaseModel],
        temperature: float = 0.3,
    ) -> tuple[BaseModel, dict[str, Any]]:
        """Upload video and run a custom prompt with structured output.

        Returns:
            (parsed_result, metadata_dict) where metadata contains
            token_count, raw_text, and processing_time_seconds.
        """
        start = time.time()
        async with self._analyzer._semaphore:
            video_file = await self._analyzer._upload_with_retry(video_path)
            try:
                video_file = await self._analyzer._wait_for_active(video_file)
                response = await self._analyzer._client.aio.models.generate_content(
                    model=self._analyzer._model,
                    contents=[video_file, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=_clean_schema_for_gemini(
                            schema_cls.model_json_schema()
                        ),
                        temperature=temperature,
                        system_instruction=system,
                    ),
                )

                if response.text is None:
                    raise ValueError("Empty response from Gemini")

                result = schema_cls.model_validate_json(response.text)
                token_count = 0
                if (
                    response.usage_metadata
                    and response.usage_metadata.total_token_count
                ):
                    token_count = response.usage_metadata.total_token_count

                elapsed = time.time() - start
                metadata = {
                    "token_count": token_count,
                    "raw_text": response.text,
                    "processing_time_seconds": round(elapsed, 2),
                }
                return result, metadata
            finally:
                self._analyzer._schedule_cleanup(video_file)

    async def run_video_n_times(
        self,
        video_path: Path,
        prompt: str,
        system: str,
        schema_cls: type[BaseModel],
        n: int = 3,
        temperature: float = 0.3,
    ) -> list[tuple[BaseModel, dict[str, Any]]]:
        """Run the same prompt N times for self-consistency measurement.

        All N runs execute in parallel, bounded by the analyzer's semaphore.
        """
        import asyncio

        async def _single_run(i: int) -> tuple[BaseModel, dict[str, Any]]:
            logger.info("Run %d/%d for %s", i + 1, n, video_path.name)
            return await self.run_video(
                video_path, prompt, system, schema_cls, temperature
            )

        return list(await asyncio.gather(*[_single_run(i) for i in range(n)]))


@pytest.fixture(scope="session")
def spike_runner(gemini_analyzer):
    """SpikeRunner wrapping the real GeminiVideoAnalyzer."""
    return SpikeRunner(gemini_analyzer)


def write_spike_report(path: Path, data: dict[str, Any]) -> None:
    """Write spike results to JSON file for later analysis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Spike report written to %s", path)
