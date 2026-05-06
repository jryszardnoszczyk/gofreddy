"""Apify SimilarWeb scraper actor wiring — Phase-0 traffic + channel mix.

Master plan §4.7 + §4.9 work item #8 (post-vendor-swap 2026-05-06).
SimilarWeb subscription was DROPPED in favor of an Apify scraper actor —
pay-per-call (~$1-5/audit), no contract.

Provides traffic-mix data for Phase-0 frames W5 (Traffic-mix ratio) and W9
(Engagement tier proxies). Used by Stage 1a cache-warmup; consumed by every
Stage 2 agent's reading guide.

Public surface
--------------

    fetcher = ApifySimilarWebFetcher(apify_token=...)
    result = await fetcher.fetch("example.com")
    # result["estimated_traffic"], ["channels"], ["geo"], ["engagement"]

Fail-soft: returns ``{"degraded": True, "reason": ...}`` on any Apify
failure so the Phase-0 brief proceeds with the other 7 meta-frames. Real
SimilarWeb pages remain customer-self-verifiable on similarweb.com.

Actor selection
---------------
Two viable actors at time of writing (2026-05-06):
  - ``tri_angle/similarweb-scraper`` — actively maintained, handles
    estimated_traffic + channel breakdown + geo + engagement.
  - ``apify/similarweb-scraper`` — official, narrower output.

Default = ``tri_angle/similarweb-scraper``. Override via ``actor_id`` ctor
arg. JR may swap if pricing/quality shifts.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ACTOR_ID = "tri_angle/similarweb-scraper"
DEFAULT_TIMEOUT_S = 180


class ApifySimilarWebFetcher:
    """Thin wrapper around an Apify SimilarWeb scraper actor.

    Constructor:
        apify_token: Apify API token (defaults to ``APIFY_TOKEN`` env var).
        actor_id: Apify actor ID (default ``tri_angle/similarweb-scraper``).
        timeout_s: Per-actor-run timeout (default 180s).
    """

    def __init__(
        self,
        *,
        apify_token: str | None = None,
        actor_id: str = DEFAULT_ACTOR_ID,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._token = apify_token or os.environ.get("APIFY_TOKEN", "")
        self._actor_id = actor_id
        self._timeout_s = timeout_s
        self._client: Any = None

    async def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        # Re-use the monitoring adapter common helper so we share the
        # ApifyClientAsync codepath with the 5 other adapters in repo.
        from src.monitoring.adapters._common import build_apify_client
        self._client = build_apify_client(self._token)
        return self._client

    async def fetch(self, domain: str) -> dict[str, Any]:
        """Run the actor for a single domain → traffic + channel + geo.

        Returns a dict with keys (always present, possibly null):
          - domain, fetched_at, actor_id
          - degraded, degraded_reason
          - estimated_traffic: total / monthly_visits / unique_visitors
          - channels: {direct, organic, paid, social, referral, email, display}
            (each as float 0.0-1.0 share of total)
          - engagement: {bounce_rate, avg_session_duration_s, pages_per_visit}
          - geo: {country_code: share, ...}
          - top_keywords: [{keyword, position}]
          - raw: untransformed actor output (for debugging)
        """
        base = self._empty_result(domain)

        if not self._token:
            base["degraded"] = True
            base["degraded_reason"] = "APIFY_TOKEN not configured"
            return base

        try:
            client = await self._ensure_client()
        except ImportError as e:  # apify_client not installed in this env
            base["degraded"] = True
            base["degraded_reason"] = f"apify_client unavailable: {e}"
            return base
        except Exception as e:  # noqa: BLE001
            base["degraded"] = True
            base["degraded_reason"] = f"client init failed: {type(e).__name__}: {e}"
            return base

        run_input = {
            # tri_angle/similarweb-scraper accepts an array of websites.
            "websites": [domain],
            # Common opt-ins that improve the output shape.
            "includeChannels": True,
            "includeGeography": True,
            "includeEngagement": True,
            "includeTopKeywords": True,
            "maxResults": 1,
        }

        try:
            run = await client.actor(self._actor_id).call(
                run_input=run_input,
                timeout_secs=self._timeout_s,
            )
        except Exception as e:  # noqa: BLE001
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                base["degraded"] = True
                base["degraded_reason"] = f"actor not found: {self._actor_id}: {e}"
                return base
            base["degraded"] = True
            base["degraded_reason"] = f"actor.call failed: {type(e).__name__}: {e}"
            return base

        try:
            from src.monitoring.adapters._common import parse_apify_items
            items = await parse_apify_items(run, client)
        except Exception as e:  # noqa: BLE001
            base["degraded"] = True
            base["degraded_reason"] = f"parse_apify_items failed: {type(e).__name__}: {e}"
            return base

        if not items:
            base["degraded"] = True
            base["degraded_reason"] = "actor returned no dataset items"
            return base

        # tri_angle/similarweb-scraper returns one item per requested domain.
        item = items[0]
        return self._project_actor_output(domain, item)

    # --- helpers -------------------------------------------------------------

    def _empty_result(self, domain: str) -> dict[str, Any]:
        return {
            "domain": domain,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": self._actor_id,
            "degraded": False,
            "degraded_reason": "",
            "estimated_traffic": {
                "monthly_visits": None,
                "unique_visitors": None,
                "monthly_visits_change_pct": None,
            },
            "channels": {
                "direct": None, "organic": None, "paid": None, "social": None,
                "referral": None, "email": None, "display": None,
            },
            "engagement": {
                "bounce_rate": None,
                "avg_session_duration_s": None,
                "pages_per_visit": None,
            },
            "geo": {},
            "top_keywords": [],
            "raw": None,
        }

    def _project_actor_output(self, domain: str, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a tri_angle/similarweb-scraper-style item into our shape.

        Tolerant of schema variation across actor versions — every field
        defaults to None and we never raise.
        """
        out = self._empty_result(domain)
        out["raw"] = item

        # Estimated traffic.
        traffic_raw = item.get("estimatedMonthlyVisits") or item.get("traffic") or {}
        if isinstance(traffic_raw, dict):
            out["estimated_traffic"]["monthly_visits"] = (
                traffic_raw.get("total") or item.get("monthlyVisits")
            )
            out["estimated_traffic"]["unique_visitors"] = (
                traffic_raw.get("uniqueVisitors")
            )
            out["estimated_traffic"]["monthly_visits_change_pct"] = (
                traffic_raw.get("changePct") or traffic_raw.get("change")
            )
        elif isinstance(traffic_raw, (int, float)):
            out["estimated_traffic"]["monthly_visits"] = traffic_raw

        # Channels — map known synonyms.
        channels_raw = item.get("trafficSources") or item.get("channels") or {}
        if isinstance(channels_raw, dict):
            cmap = {
                "direct": ["direct"],
                "organic": ["search", "organic", "organic_search"],
                "paid": ["paidSearch", "paid_search", "paid"],
                "social": ["social"],
                "referral": ["referrals", "referral"],
                "email": ["mail", "email"],
                "display": ["display", "displayAds", "display_ads"],
            }
            for canonical, aliases in cmap.items():
                for alias in aliases:
                    if alias in channels_raw:
                        out["channels"][canonical] = _to_float(channels_raw[alias])
                        break

        # Engagement metrics.
        eng_raw = item.get("engagement") or item.get("engagements") or {}
        if isinstance(eng_raw, dict):
            out["engagement"]["bounce_rate"] = _to_float(
                eng_raw.get("bounceRate") or eng_raw.get("bounce_rate")
            )
            out["engagement"]["avg_session_duration_s"] = _to_float(
                eng_raw.get("avgVisitDuration")
                or eng_raw.get("avg_visit_duration")
                or eng_raw.get("avgSessionDuration")
            )
            out["engagement"]["pages_per_visit"] = _to_float(
                eng_raw.get("pagesPerVisit") or eng_raw.get("pages_per_visit")
            )

        # Geo split.
        geo_raw = item.get("topCountries") or item.get("geo") or item.get("countries") or []
        if isinstance(geo_raw, list):
            for entry in geo_raw[:25]:
                if isinstance(entry, dict):
                    code = (entry.get("countryCode") or entry.get("code")
                            or entry.get("country") or "").upper()
                    share = _to_float(entry.get("share") or entry.get("trafficShare"))
                    if code and share is not None:
                        out["geo"][code] = share

        # Top keywords.
        kw_raw = item.get("topKeywords") or item.get("keywords") or []
        if isinstance(kw_raw, list):
            kws = []
            for entry in kw_raw[:25]:
                if isinstance(entry, dict):
                    kws.append({
                        "keyword": entry.get("keyword") or entry.get("term") or "",
                        "position": entry.get("position") or entry.get("rank"),
                    })
            out["top_keywords"] = kws

        return out


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = ["ApifySimilarWebFetcher", "DEFAULT_ACTOR_ID"]
