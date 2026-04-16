"""PageSpeed Insights API provider — async HTTP call (free tier)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..models import PerformanceResult

logger = logging.getLogger(__name__)

PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


async def check_performance(
    url: str,
    *,
    strategy: str = "mobile",
    api_key: str = "",
    timeout: float = 30.0,
) -> PerformanceResult:
    """Query Google PageSpeed Insights API.

    Free tier: 25K requests/day, no key required for basic usage.
    """
    params: dict[str, str] = {
        "url": url,
        "strategy": strategy,
        "category": "performance",
    }
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(PAGESPEED_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("PageSpeed error for %s: %s", url, e)
            return PerformanceResult(url=url, strategy=strategy)

        return _parse_response(url, resp.json(), strategy)


def _parse_response(
    url: str, data: dict[str, Any], strategy: str
) -> PerformanceResult:
    """Parse PageSpeed Insights JSON response."""
    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})

    perf_category = categories.get("performance", {})
    score = perf_category.get("score")

    def _metric_ms(audit_key: str) -> float | None:
        audit = audits.get(audit_key, {})
        val = audit.get("numericValue")
        return round(val, 1) if val is not None else None

    return PerformanceResult(
        url=url,
        performance_score=score,
        fcp_ms=_metric_ms("first-contentful-paint"),
        lcp_ms=_metric_ms("largest-contentful-paint"),
        cls=audits.get("cumulative-layout-shift", {}).get("numericValue"),
        tbt_ms=_metric_ms("total-blocking-time"),
        speed_index_ms=_metric_ms("speed-index"),
        strategy=strategy,
    )
