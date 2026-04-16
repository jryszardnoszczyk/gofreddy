"""Unified provider cost recording.

Module-level singleton — call ``cost_recorder.init(pool)`` once in lifespan,
then ``await cost_recorder.record(...)`` from any service.  No-ops gracefully
when the pool is not set (tests, CLI scripts).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)

_INSERT_SQL = """
INSERT INTO provider_cost_log
    (provider, operation, cost_usd, tokens_in, tokens_out, model, metadata, user_id)
VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
"""

# Apify pricing — fallback only (primary source: run["usageTotalUsd"] from API).
# CU rate depends on plan: Free/Starter=$0.30, Scale=$0.25, Business=$0.20.
# Most of our actors use Pay-Per-Result (not CU billing), so this fallback is
# rarely accurate. See https://apify.com/pricing
APIFY_COST_PER_CU = 0.30

# ScrapeCreators pricing — credit-based, 1 credit per request for endpoints we use.
# Freelance: $47/25K = $0.00188/credit, Business: $497/500K = $0.00099/credit.
# Using Freelance rate (cheapest current paid tier). See https://scrapecreators.com/
SCRAPECREATORS_COST_PER_REQUEST = 0.00188

# Xpoz pricing — credit formula: (Queries × 5) + (Results × 0.005).
# Pro plan: $20/mo for 30K credits = $0.000667/credit.
# 1 query returning ~20 results = 5.1 credits = ~$0.0034. See https://xpoz.ai/pricing
XPOZ_COST_PER_CALL = 0.0034

# NewsData.io pricing — 1 credit per API request. Add-on rate: $0.006/credit.
# See https://newsdata.io/pricing
NEWSDATA_COST_PER_REQUEST = 0.006

# Influencers.club pricing — credit-based, Pro annual $375/mo for 12K credits.
# See https://influencers.club/pricing
IC_COST_PER_DISCOVERY_CREATOR = 0.01
IC_COST_PER_ENRICHMENT_FULL = 1.0
IC_COST_PER_ENRICHMENT_RAW = 0.03
IC_COST_PER_CONTENT = 0.03
IC_COST_PER_SIMILAR = 0.01
IC_COST_PER_CONNECTED_SOCIALS = 0.5
IC_COST_PER_AUDIENCE_OVERLAP = 1.0


def _gemini_rates(model: str | None) -> tuple[float, float, float]:
    """Return (input_rate, cached_input_rate, output_rate) per million tokens.

    Uses the canonical GEMINI_PRICING table from gemini_models.py.
    Falls back to Flash rates if model is unknown.
    """
    from .gemini_models import GEMINI_PRICING

    if model and model in GEMINI_PRICING:
        p = GEMINI_PRICING[model]
        return p["text_input"], p.get("cached_input", p["text_input"] * 0.1), p["output"]
    # Fallback: Flash rates (most common model)
    return 0.50, 0.05, 3.00


def extract_gemini_usage(
    response: Any,
    model: str | None = None,
) -> tuple[int | None, int | None, float | None]:
    """Extract (tokens_in, tokens_out, cost_usd) from a Gemini response.

    Pass ``model`` for accurate per-model pricing. Without it, falls back
    to Gemini Flash rates.

    Includes ``thoughts_token_count`` (billed at output rate) and accounts
    for ``cached_content_token_count`` (billed at 90% discount per Google pricing).
    """
    if not hasattr(response, "usage_metadata") or not response.usage_metadata:
        return None, None, None
    usage = response.usage_metadata
    t_in = getattr(usage, "prompt_token_count", 0) or 0
    t_out = getattr(usage, "candidates_token_count", 0) or 0
    t_think = getattr(usage, "thoughts_token_count", 0) or 0
    t_cached = getattr(usage, "cached_content_token_count", 0) or 0
    input_rate, cached_rate, output_rate = _gemini_rates(model)
    # Non-cached input at full rate, cached at discounted rate, thinking at output rate
    non_cached_in = max(0, t_in - t_cached)
    cost = (
        (non_cached_in / 1_000_000) * input_rate
        + (t_cached / 1_000_000) * cached_rate
        + ((t_out + t_think) / 1_000_000) * output_rate
    )
    return t_in, t_out, round(cost, 6)


class CostRecorder:
    """Fire-and-forget cost logger backed by ``provider_cost_log`` table."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    def init(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

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
        user_id: UUID | None = None,
    ) -> None:
        if self._pool is None:
            return
        try:
            async with asyncio.timeout(2.0):
                await self._pool.execute(
                    _INSERT_SQL,
                    provider,
                    operation,
                    cost_usd,
                    tokens_in,
                    tokens_out,
                    model,
                    json.dumps(metadata) if metadata else None,
                    user_id,
                )
        except Exception:
            logger.warning("cost_record_failed", extra={"provider": provider, "op": operation}, exc_info=True)

    async def get_cost_by_operation(self, days: int = 30) -> list[dict[str, Any]]:
        """Query cost breakdown by operation over the last N days."""
        if self._pool is None:
            return []
        try:
            rows = await self._pool.fetch(
                """
                SELECT
                    operation,
                    model,
                    COUNT(*) AS call_count,
                    COALESCE(SUM(cost_usd), 0)::float AS total_cost_usd,
                    COALESCE(AVG(cost_usd), 0)::float AS avg_cost_usd,
                    COALESCE(SUM(tokens_in), 0)::bigint AS total_tokens_in,
                    COALESCE(SUM(tokens_out), 0)::bigint AS total_tokens_out
                FROM provider_cost_log
                WHERE created_at >= NOW() - make_interval(days => $1)
                GROUP BY operation, model
                ORDER BY total_cost_usd DESC
                """,
                days,
            )
            return [dict(r) for r in rows]
        except Exception:
            logger.warning("cost_query_failed", exc_info=True)
            return []

    async def get_cost_by_user(self, user_id: UUID, days: int = 30) -> list[dict[str, Any]]:
        """Query per-user cost breakdown over the last N days."""
        if self._pool is None:
            return []
        try:
            rows = await self._pool.fetch(
                """
                SELECT
                    operation,
                    model,
                    COUNT(*) AS call_count,
                    COALESCE(SUM(cost_usd), 0)::float AS total_cost_usd,
                    COALESCE(SUM(tokens_in), 0)::bigint AS total_tokens_in,
                    COALESCE(SUM(tokens_out), 0)::bigint AS total_tokens_out
                FROM provider_cost_log
                WHERE user_id = $1 AND created_at >= NOW() - make_interval(days => $2)
                GROUP BY operation, model
                ORDER BY total_cost_usd DESC
                """,
                user_id,
                days,
            )
            return [dict(r) for r in rows]
        except Exception:
            logger.warning("cost_query_failed", exc_info=True)
            return []


# Module-level singleton
cost_recorder = CostRecorder()
