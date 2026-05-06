"""Intent classification — batched mention-intent classifier via Claude CLI.

Replaces the prior Gemini Flash-Lite classifier (removed 2026-05-06 along
with the rest of the text-side Gemini calls). Uses the same `call_sonnet_json`
subprocess helper as the evaluation paraphrase + calibration judges so we
have one Claude entry-point across the codebase.

The public interface is preserved exactly so DI in `src/api/main.py` and
the `/classify-intent` route both keep working — the constructor still
accepts a `client` kwarg for backward compatibility, but it is now ignored
(the Claude CLI authenticates itself, so no shared client is required).
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
from ..models import IntentLabel, Mention

if TYPE_CHECKING:
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

Return a SINGLE JSON object (no prose, no markdown fences) of the form:
{"verdicts": [{"id": "<mention_id>", "intent": "<intent>"}, ...]}

Return exactly one entry per mention, preserving the provided ids.
"""


class IntentClassifier:
    """Classifies mention intents using Claude (via the `claude -p` CLI).

    Args:
        client: Accepted for interface parity with the prior Gemini-based
            classifier; ignored. Pass `None` from new code.
        settings: MonitoringSettings — only `intent_batch_size` is used.
    """

    def __init__(
        self,
        client: Any,  # noqa: ARG002 — kept for backward-compatible call sites
        settings: MonitoringSettings,
    ) -> None:
        self._client = None  # Reserved; Claude CLI is per-batch subprocess.
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
                operation="intent_classify",
                model=SONNET_MODEL,
                timeout=60.0,
            )
        except SonnetAgentError:
            logger.exception("intent_classify Claude call failed")
            return {}

        return self._parse_response(data, batch)

    def _parse_response(
        self,
        payload: dict[str, Any] | str,
        batch: list[Mention],
    ) -> dict[UUID, str]:
        """Parse Claude JSON response into mention_id → intent mapping.

        Accepts either the structured dict from `call_sonnet_json` (production
        path) or a raw string (for backward-compatible test fixtures that
        replay legacy Gemini-style stdout).
        """
        valid_ids = {str(m.id) for m in batch}
        results: dict[UUID, str] = {}

        items: list[Any] | None = None
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning("Failed to parse intent classification JSON response")
                return {}
            if isinstance(parsed, list):
                items = parsed
            elif isinstance(parsed, dict):
                items = parsed.get("verdicts") or parsed.get("intents")
        elif isinstance(payload, dict):
            items = payload.get("verdicts") or payload.get("intents")
        elif isinstance(payload, list):
            items = payload

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
