"""Sentiment classification — batched mention-sentiment classifier via Claude CLI.

Mirrors `IntentClassifier` exactly (same constructor signature, same
batch shape) so DI / tests can swap one for the other. Replaced the
Gemini Flash-Lite implementation 2026-05-06 along with the rest of the
text-side Gemini calls.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ...evaluation.judges.sonnet_agent import (
    SONNET_MODEL,
    SonnetAgentError,
    call_sonnet_json,
)
from ..models import Mention

if TYPE_CHECKING:
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

Return a SINGLE JSON object (no prose, no markdown fences) of the form:
{"verdicts": [{"id": "<mention_id>", "sentiment": "<sentiment>"}, ...]}

Return exactly one entry per mention, preserving the provided ids.
"""


class SentimentClassifier:
    """Classifies mention sentiment using Claude (via the `claude -p` CLI).

    Args:
        client: Accepted for interface parity with the prior Gemini-based
            classifier; ignored. Pass `None` from new code.
        settings: MonitoringSettings — only `sentiment_batch_size` is used.
    """

    def __init__(
        self,
        client: Any,  # noqa: ARG002 — kept for backward-compatible call sites
        settings: MonitoringSettings,
    ) -> None:
        self._client = None
        self._batch_size = settings.sentiment_batch_size

    async def classify_batch(
        self,
        mentions: list[Mention],
    ) -> dict[UUID, str]:
        """Classify sentiment for a batch of mentions.

        Returns mapping of mention_id → sentiment string. Partial failures:
        successfully classified mentions are returned, failed batches are
        logged and skipped.
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
        """Classify a single batch of mentions via Claude CLI."""
        mention_inputs = [
            {"id": str(m.id), "text": (m.content or "")[:1000]}
            for m in batch
        ]
        prompt = (
            f"{_SYSTEM_INSTRUCTION}\n\n"
            f"Mentions:\n{json.dumps(mention_inputs, ensure_ascii=False, indent=2)}\n"
        )

        try:
            data = await call_sonnet_json(
                prompt,
                operation="sentiment_classify",
                model=SONNET_MODEL,
                timeout=60.0,
            )
        except SonnetAgentError:
            logger.exception("sentiment_classify Claude call failed")
            return {}

        return self._parse_response(data, batch)

    def _parse_response(
        self,
        payload: dict[str, Any] | str,
        batch: list[Mention],
    ) -> dict[UUID, str]:
        """Parse Claude JSON response into mention_id → sentiment mapping.

        Accepts either the structured dict from `call_sonnet_json` (production
        path) or a raw string (legacy test fixtures).
        """
        valid_ids = {str(m.id) for m in batch}
        results: dict[UUID, str] = {}

        items: list[Any] | None = None
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning("Failed to parse sentiment classification JSON response")
                return {}
            if isinstance(parsed, list):
                items = parsed
            elif isinstance(parsed, dict):
                items = parsed.get("verdicts") or parsed.get("sentiments")
        elif isinstance(payload, dict):
            items = payload.get("verdicts") or payload.get("sentiments")
        elif isinstance(payload, list):
            items = payload

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
        Caller provides deadline for timeout enforcement. Implementation
        depends on repository method to fetch unclassified mentions and
        update_mention_sentiments to persist results. Wired via internal.py
        endpoint.
        """
        raise NotImplementedError("Wire via /internal/run-sentiment-classification endpoint")
