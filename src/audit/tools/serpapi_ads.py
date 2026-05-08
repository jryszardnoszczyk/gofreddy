"""SerpAPI Google Ads Transparency wrapper — Adyntel live fallback.

Master plan §4.7 + §4.9 work item #10 (L2). Live fallback for one-off
advertiser lookups when the maintained Adyntel index is too expensive or
overkill (per the live-vs-indexed pattern in §4.2). Pay-per-call via
SerpAPI; key in ``SERPAPI_KEY`` env var.

Public surface
--------------

    client = SerpApiAdsClient(api_key=...)
    result = await client.advertiser_lookup(advertiser_id="...")
    # or:
    result = await client.search_ads_by_domain("competitor.com")

Returns ``degraded=True`` on any failure. Index providers (Adyntel) remain
primary for exhaustive ad-corpus coverage; this wrapper is for cheap
one-off sanity checks where live data is enough.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search.json"
DEFAULT_TIMEOUT_S = 30.0


class SerpApiAdsClient:
    """Async wrapper around SerpAPI's Google Ads Transparency engine.

    SerpAPI engine = ``google_ads_transparency_center``. Pay-per-call;
    pricing varies by plan tier ($75-$2500/mo for indexed access; $5/1K
    queries pay-as-you-go is the typical fallback we use here).
    """

    DEFAULT_ENGINE = "google_ads_transparency_center"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._api_key = api_key or os.environ.get("SERPAPI_KEY", "")
        self._timeout = timeout

    async def advertiser_lookup(
        self,
        *,
        advertiser_id: str,
        region: str = "US",
    ) -> dict[str, Any]:
        """Look up an advertiser by Google's advertiser_id.

        Returns the advertiser's ad inventory (with creative metadata) +
        verification status + start dates.
        """
        params = {
            "engine": self.DEFAULT_ENGINE,
            "advertiser_id": advertiser_id,
            "region": region,
        }
        return await self._request(params, query_label=f"advertiser:{advertiser_id}")

    async def search_ads_by_domain(
        self,
        domain: str,
        *,
        region: str = "US",
    ) -> dict[str, Any]:
        """Search the Google Ads Transparency Center for ads from a domain.

        ``q`` parameter accepts a domain or advertiser-name search term.
        Returns the ranked list of advertisers + their ad inventory hint.
        """
        params = {
            "engine": self.DEFAULT_ENGINE,
            "q": domain,
            "region": region,
        }
        return await self._request(params, query_label=f"domain:{domain}")

    # --- internals -----------------------------------------------------------

    async def _request(self, params: dict[str, Any], *, query_label: str) -> dict[str, Any]:
        base = self._empty_result(query_label)
        if not self._api_key:
            base["degraded"] = True
            base["degraded_reason"] = "SERPAPI_KEY not configured"
            return base

        params = {**params, "api_key": self._api_key, "no_cache": "false"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                response = await http.get(SERPAPI_BASE_URL, params=params)
        except httpx.TimeoutException as e:
            base["degraded"] = True
            base["degraded_reason"] = f"timeout: {e}"
            return base
        except httpx.HTTPError as e:
            base["degraded"] = True
            base["degraded_reason"] = f"network: {type(e).__name__}: {e}"
            return base

        base["http_status"] = response.status_code
        if response.status_code != 200:
            base["degraded"] = True
            base["degraded_reason"] = (
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return base

        try:
            payload = response.json()
        except ValueError as e:
            base["degraded"] = True
            base["degraded_reason"] = f"non-JSON response: {e}"
            return base

        # SerpAPI surfaces logical errors via the "error" key even on HTTP 200.
        if isinstance(payload, dict) and payload.get("error"):
            base["degraded"] = True
            base["degraded_reason"] = f"serpapi error: {payload.get('error')}"
            base["raw"] = payload
            return base

        return self._project_payload(query_label, params, payload)

    def _empty_result(self, query_label: str) -> dict[str, Any]:
        return {
            "query": query_label,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "engine": self.DEFAULT_ENGINE,
            "degraded": False,
            "degraded_reason": "",
            "http_status": None,
            "advertisers": [],
            "ad_creatives": [],
            "raw": None,
        }

    def _project_payload(
        self, query_label: str, params: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        out = self._empty_result(query_label)
        out["http_status"] = 200
        out["raw"] = payload

        # SerpAPI's google_ads_transparency_center returns either
        # advertiser-search results or ad-creative lookups.
        for adv in payload.get("advertisers", []) or []:
            out["advertisers"].append({
                "advertiser_id": adv.get("advertiser_id"),
                "name": adv.get("name"),
                "domain": adv.get("domain"),
                "verified": adv.get("verified"),
                "region": adv.get("region"),
                "url": adv.get("link") or adv.get("url"),
            })

        for ad in payload.get("ad_creatives", []) or payload.get("ads", []) or []:
            out["ad_creatives"].append({
                "creative_id": ad.get("creative_id") or ad.get("ad_id"),
                "format": ad.get("format") or ad.get("ad_format"),
                "first_seen": ad.get("first_seen") or ad.get("date_started"),
                "last_seen": ad.get("last_seen") or ad.get("date_ended"),
                "domain": ad.get("domain") or ad.get("destination_url"),
                "preview_url": ad.get("preview_url") or ad.get("ad_url"),
                "destination_url": ad.get("destination_url"),
                "advertiser_id": ad.get("advertiser_id"),
            })

        return out


__all__ = ["SerpApiAdsClient", "SERPAPI_BASE_URL"]
