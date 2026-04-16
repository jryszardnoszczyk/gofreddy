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


cost_recorder = CostRecorder()
