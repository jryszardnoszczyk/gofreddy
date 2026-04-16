"""Intent classification — Gemini Flash-Lite batch classification of mentions."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ...common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..models import IntentLabel, Mention

if TYPE_CHECKING:
    from google.genai import Client as GenaiClient

    from ..config import MonitoringSettings

logger = logging.getLogger(__name__)

_VALID_INTENTS = {e.value for e in IntentLabel}

_SYSTEM_INSTRUCTION = """You are a mention intent classifier. For each mention, classify the author's intent.

Valid intents: complaint, question, recommendation, purchase_signal, general_discussion

Rules:
- complaint: expressing dissatisfaction, reporting issues, negative feedback
- question: asking for information, seeking help, inquiry
- recommendation: suggesting, endorsing, positive advocacy
- purchase_signal: expressing intent to buy, comparing products, asking for pricing
- general_discussion: neutral conversation, sharing information, news

Respond with JSON array: [{"id": "<mention_id>", "intent": "<intent>"}]
"""


class IntentClassifier:
    """Classifies mention intents using Gemini Flash-Lite."""

    def __init__(
        self,
        client: GenaiClient,
        settings: MonitoringSettings,
    ) -> None:
        self._client = client
        self._batch_size = settings.intent_batch_size

    async def classify_batch(
        self,
        mentions: list[Mention],
    ) -> dict[UUID, str]:
        """Classify intents for a batch of mentions.

        Returns mapping of mention_id → intent string.
        Partial failures: successfully classified mentions are returned,
        failed batches are logged and skipped.
        """
        if not mentions:
            return {}

        results: dict[UUID, str] = {}

        # Process in batches
        for i in range(0, len(mentions), self._batch_size):
            batch = mentions[i : i + self._batch_size]
            try:
                batch_results = await self._classify_single_batch(batch)
                results.update(batch_results)
            except Exception:
                logger.exception(
                    "Intent classification failed for batch %d-%d",
                    i,
                    i + len(batch),
                )
                # Continue with next batch — partial failure is acceptable

        return results

    async def _classify_single_batch(
        self,
        batch: list[Mention],
    ) -> dict[UUID, str]:
        """Classify a single batch of mentions via Gemini."""
        from google.genai import types as genai_types

        from ...common.model_router import get_model_for_task

        _model = get_model_for_task("intent_classification")

        # Build input: list of {id, text} for the LLM
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
        await _cost_recorder.record("gemini", "intent_classify", tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=_model)

        # Check finish_reason before parsing
        if response.candidates and response.candidates[0].finish_reason not in (
            None,
            "STOP",
        ):
            logger.warning(
                "Gemini intent classification terminated: %s",
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
        """Parse Gemini JSON response into mention_id → intent mapping."""
        valid_ids = {str(m.id) for m in batch}
        results: dict[UUID, str] = {}

        try:
            items: list[dict[str, Any]] = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse intent classification JSON response")
            return {}

        if not isinstance(items, list):
            return {}

        for item in items:
            if not isinstance(item, dict):
                continue
            mid = item.get("id", "")
            intent = item.get("intent", "")
            if mid in valid_ids and intent in _VALID_INTENTS:
                try:
                    results[UUID(mid)] = intent
                except ValueError:
                    continue

        return results
