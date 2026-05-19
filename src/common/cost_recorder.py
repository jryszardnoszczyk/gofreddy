"""Unified provider cost recording (file-based JSONL)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)

# Apify pricing — fallback only (primary source: run["usageTotalUsd"] from API).
# CU rate depends on plan: Free/Starter=$0.30, Scale=$0.25, Business=$0.20.
APIFY_COST_PER_CU = 0.30

# ScrapeCreators pricing — credit-based, 1 credit per request.
SCRAPECREATORS_COST_PER_REQUEST = 0.00188

# Xpoz pricing — credit formula: (Queries × 5) + (Results × 0.005). Pro $20/30K credits.
XPOZ_COST_PER_CALL = 0.0034

# NewsData.io pricing — 1 credit per request; add-on rate $0.006/credit.
NEWSDATA_COST_PER_REQUEST = 0.006

# Influencers.club pricing — Pro annual $375/mo for 12K credits.
IC_COST_PER_DISCOVERY_CREATOR = 0.01
IC_COST_PER_ENRICHMENT_FULL = 1.0
IC_COST_PER_ENRICHMENT_RAW = 0.03
IC_COST_PER_CONTENT = 0.03
IC_COST_PER_SIMILAR = 0.01
IC_COST_PER_CONNECTED_SOCIALS = 0.5
IC_COST_PER_AUDIENCE_OVERLAP = 1.0


def _gemini_rates(model: str | None) -> tuple[float, float, float]:
    from .gemini_models import GEMINI_PRICING
    if model and model in GEMINI_PRICING:
        p = GEMINI_PRICING[model]
        return p["text_input"], p.get("cached_input", p["text_input"] * 0.1), p["output"]
    return 0.50, 0.05, 3.00


# Anthropic pricing (USD per 1M tokens). Cache-read is typically 10% of input
# rate (Anthropic tier discount); cache-creation is ~1.25x input. We collapse
# those two cache types into a single "cached" rate using the read-rate (the
# more common of the two in steady-state cached prompts) — the ledger uses
# this only as a fallback when subscription billing returns total_cost_usd=0,
# so approximation is acceptable for ceiling-enforcement math.
CLAUDE_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":      {"input": 15.0, "cached": 1.50, "output": 75.0},
    "claude-opus-4-7[1m]":  {"input": 15.0, "cached": 1.50, "output": 75.0},
    "claude-opus-4-6":      {"input": 15.0, "cached": 1.50, "output": 75.0},
    "claude-sonnet-4-6":    {"input":  3.0, "cached": 0.30, "output": 15.0},
    "claude-haiku-4-5":     {"input":  1.0, "cached": 0.10, "output":  5.0},
}


def claude_rates(model: str | None) -> tuple[float, float, float]:
    """Return ``(input, cached, output)`` $/M-tokens rates for ``model``.

    Mirrors ``_gemini_rates`` shape so audit/cost_ledger fallback math is
    symmetric across providers. Unknown models return Sonnet-tier defaults
    (a deliberately conservative middle estimate so ceiling enforcement
    doesn't silently relax on a typo'd model name)."""
    if model and model in CLAUDE_PRICING:
        p = CLAUDE_PRICING[model]
        return p["input"], p["cached"], p["output"]
    return 3.0, 0.30, 15.0


def extract_gemini_usage(response: Any, model: str | None = None) -> tuple[int | None, int | None, float | None]:
    if not hasattr(response, "usage_metadata") or not response.usage_metadata:
        return None, None, None
    usage = response.usage_metadata
    t_in = getattr(usage, "prompt_token_count", 0) or 0
    t_out = getattr(usage, "candidates_token_count", 0) or 0
    t_think = getattr(usage, "thoughts_token_count", 0) or 0
    t_cached = getattr(usage, "cached_content_token_count", 0) or 0
    input_rate, cached_rate, output_rate = _gemini_rates(model)
    non_cached_in = max(0, t_in - t_cached)
    cost = (
        (non_cached_in / 1_000_000) * input_rate
        + (t_cached / 1_000_000) * cached_rate
        + ((t_out + t_think) / 1_000_000) * output_rate
    )
    return t_in, t_out, round(cost, 6)


class CostRecorder:
    def __init__(self) -> None:
        self._log_file: Path | None = None

    def init(self, log_file: Path | str) -> None:
        self._log_file = Path(log_file)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    async def record(
        self,
        provider: str,
        operation: str,
        *,
        cost_usd: float | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
        # --- canonical event schema fields (per autoresearch.events; optional) ---
        # When supplied, this call ALSO emits a kind="cost" event into the
        # canonical event log at the per-client path (or operator-internal
        # path when client_id is None). See docs/brainstorms/2026-05-13-
        # client-portal-telemetry-design.md for the full schema.
        client_id: str | None = None,
        session_id: str | None = None,
        lane: str | None = None,
        variant: str | None = None,
        fixture: str | None = None,
    ) -> None:
        if self._log_file is None:
            return
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": provider,
                "operation": operation,
                "cost_usd": cost_usd,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "model": model,
                "metadata": metadata,
            }
            async with aiofiles.open(self._log_file, "a") as f:
                await f.write(json.dumps(entry) + "\n")
        except Exception:
            logger.warning("cost_record_failed", extra={"provider": provider, "op": operation}, exc_info=True)

        # Mirror to the canonical event log (kind="cost"). Failure here must
        # NOT prevent the cost from being captured in the cost-recorder log
        # above (which is the source of truth for cost-ledger math). Lazy
        # import to avoid hard dependency on autoresearch/* in callers that
        # use only the cost_recorder.
        try:
            from autoresearch.events import log_event, client_events_path

            payload: dict[str, Any] = {
                "source": "autoresearch",
                "action": f"{provider}.{operation}",
                "status": "complete",
                "provider": provider,
                "operation": operation,
            }
            if cost_usd is not None:
                payload["cost_usd"] = cost_usd
            if tokens_in is not None:
                payload["tokens_in"] = tokens_in
            if tokens_out is not None:
                payload["tokens_out"] = tokens_out
            if model is not None:
                payload["model"] = model
            if client_id is not None:
                payload["client_id"] = client_id
            if session_id is not None:
                payload["session_id"] = session_id
            if lane is not None:
                payload["lane"] = lane
            if variant is not None:
                payload["variant"] = variant
            if fixture is not None:
                payload["fixture"] = fixture
            if metadata is not None:
                payload["metadata"] = metadata

            log_event(kind="cost", path=client_events_path(client_id), **payload)
        except Exception:
            logger.warning(
                "cost_event_emit_failed",
                extra={"provider": provider, "op": operation, "client_id": client_id},
                exc_info=True,
            )


cost_recorder = CostRecorder()
