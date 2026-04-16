"""Sentiment classification — Gemini Flash-Lite batch classification of mentions.

Matches IntentClassifier interface exactly (GenaiClient, get_model_for_task, list[Mention]).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ...common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..models import Mention

if TYPE_CHECKING:
    from google.genai import Client as GenaiClient

    from ..config import MonitoringSettings

logger = logging.getLogger(__name__)

_VALID_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}

_SYSTEM_INSTRUCTION = """You are a mention sentiment classifier. For each mention, classify the sentiment.

Valid sentiments: positive, negative, neutral, mixed

Rules:
- positive: expressing satisfaction, praise, excitement, endorsement
- negative: expressing dissatisfaction, criticism, frustration, complaints
- neutral: factual reporting, objective discussion, informational
- mixed: contains both positive and negative elements

Respond with JSON array: [{"id": "<mention_id>", "sentiment": "<sentiment>"}]
"""


class SentimentClassifier:
    """Classifies mention sentiment using Gemini Flash-Lite."""

    def __init__(
        self,
        client: GenaiClient,
        settings: MonitoringSettings,
    ) -> None:
        self._client = client
        self._batch_size = settings.sentiment_batch_size

    async def classify_batch(
        self,
        mentions: list[Mention],
    ) -> dict[UUID, str]:
        """Classify sentiment for a batch of mentions.

        Returns mapping of mention_id → sentiment string.
        Partial failures: successfully classified mentions are returned,
        failed batches are logged and skipped.
        """
        if not mentions:
            return {}

        results: dict[UUID, str] = {}

        for i in range(0, len(mentions), self._batch_size):
            batch = mentions[i : i + self._batch_size]
            try:
                batch_results = await self._classify_single_batch(batch)
                results.update(batch_results)
            except Exception:
                logger.exception(
                    "Sentiment classification failed for batch %d-%d",
                    i,
                    i + len(batch),
                )

        return results

    async def _classify_single_batch(
        self,
        batch: list[Mention],
    ) -> dict[UUID, str]:
        """Classify a single batch of mentions via Gemini."""
        from google.genai import types as genai_types

        from ...common.model_router import get_model_for_task

        _model = get_model_for_task("sentiment_classification")

        mention_inputs = [
            {"id": str(m.id), "text": (m.content or "")[:1000]}
            for m in batch
        ]

        content = json.dumps(mention_inputs, ensure_ascii=False)

        config = genai_types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0.1,
        )

        response = await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=_model,
                contents=content,
                config=config,
            ),
            timeout=30,
        )
        t_in, t_out, c = extract_gemini_usage(response, _model)
        await _cost_recorder.record(
            "gemini", "sentiment_classify",
            tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=_model,
        )

        if response.candidates and response.candidates[0].finish_reason not in (
            None,
            "STOP",
        ):
            logger.warning(
                "Gemini sentiment classification terminated: %s",
                response.candidates[0].finish_reason,
            )
            return {}

        if not response.text:
            return {}

        return self._parse_response(response.text, batch)

    def _parse_response(
        self,
        text: str,
        batch: list[Mention],
    ) -> dict[UUID, str]:
        """Parse Gemini JSON response into mention_id → sentiment mapping."""
        valid_ids = {str(m.id) for m in batch}
        results: dict[UUID, str] = {}

        try:
            items: list[dict[str, Any]] = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse sentiment classification JSON response")
            return {}

        if not isinstance(items, list):
            return {}

        for item in items:
            if not isinstance(item, dict):
                continue
            mid = item.get("id", "")
            sentiment = item.get("sentiment", "")
            if mid in valid_ids and sentiment in _VALID_SENTIMENTS:
                try:
                    results[UUID(mid)] = sentiment
                except ValueError:
                    continue

        return results

    async def run_daily_job(self, deadline: float | None = None) -> dict:
        """Batch job runner — classify unclassified mentions.

        Following PostIngestionAnalyzer.run_analysis_job pattern.
        Caller provides deadline for timeout enforcement.
        """
        # Implementation depends on repository method to fetch unclassified mentions
        # and update_mention_sentiments to persist results.
        # Wired via internal.py endpoint.
        raise NotImplementedError("Wire via /internal/run-sentiment-classification endpoint")
