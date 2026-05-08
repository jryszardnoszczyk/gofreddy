"""Brave Search API wrapper — lens #157 prerequisite.

Master plan §4.7 + §4.9 work item #9 (L2). Brave Search ranking is a
prerequisite for Claude-citation visibility; DataForSEO doesn't shard Brave;
Cloro tracks AI citations not Brave SERPs.

Free tier: 2,000 queries/month. Auth: ``X-Subscription-Token`` header from
``BRAVE_API_KEY`` env var. The companion shell helper ``cli/scripts/fetch_api.sh``
already injects this header for ``api.search.brave.com`` host — agents that
prefer the prompt-driven URL-pattern path can call the script directly.
This Python wrapper exists for Stage 1a cache-warmup + tests.

Public surface
--------------

    client = BraveSearchClient(api_key=...)
    result = await client.web_search("query string", count=20)
    # result["query"], ["results"], ["mixed"], ["degraded"]

Returns ``degraded=True`` on every failure mode (no key, 401, 429, 5xx,
network) so Stage 1a fan-out continues.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

BRAVE_WEB_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_USER_AGENT = "GoFreddy-Audit/1.0 (contact: jryszardn@gmail.com)"
DEFAULT_TIMEOUT_S = 15.0


class BraveSearchClient:
    """Thin async wrapper around Brave Web Search v1.

    The wrapper deliberately skips error-raising for transient issues:
    Stage 1a needs partial signal more than a guaranteed-perfect call. Hard
    misconfig (no key) is reported via ``degraded`` rather than a raise so
    every Phase-0 fan-out path returns a homogeneous shape.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        self._timeout = timeout

    async def web_search(
        self,
        query: str,
        *,
        count: int = 20,
        country: str = "US",
        search_lang: str = "en",
        safesearch: str = "moderate",
        offset: int = 0,
    ) -> dict[str, Any]:
        """Hit ``/res/v1/web/search`` and return parsed payload.

        Parameters
        ----------
        query
            User search query (max 400 chars per Brave's spec).
        count
            Max number of web results (1-20). Brave caps at 20 per call.
        country / search_lang
            Locale + language ISO codes.
        safesearch
            ``"off"`` / ``"moderate"`` / ``"strict"``.
        offset
            Pagination offset (0-9). Each "page" is ``count`` results.
        """
        base = self._empty_result(query)

        if not self._api_key:
            base["degraded"] = True
            base["degraded_reason"] = "BRAVE_API_KEY not configured"
            return base

        params = {
            "q": query,
            "count": min(max(int(count), 1), 20),
            "country": country,
            "search_lang": search_lang,
            "safesearch": safesearch,
            "offset": min(max(int(offset), 0), 9),
        }
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": BRAVE_USER_AGENT,
            "X-Subscription-Token": self._api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                response = await http.get(
                    BRAVE_WEB_SEARCH_URL,
                    params=params,
                    headers=headers,
                )
        except httpx.TimeoutException as e:
            base["degraded"] = True
            base["degraded_reason"] = f"timeout: {e}"
            return base
        except httpx.HTTPError as e:
            base["degraded"] = True
            base["degraded_reason"] = f"network: {type(e).__name__}: {e}"
            return base

        if response.status_code != 200:
            base["degraded"] = True
            base["degraded_reason"] = (
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            base["http_status"] = response.status_code
            return base

        try:
            payload = response.json()
        except ValueError as e:
            base["degraded"] = True
            base["degraded_reason"] = f"non-JSON response: {e}"
            return base

        return self._project_payload(query, params, payload)

    # --- helpers -------------------------------------------------------------

    def _empty_result(self, query: str) -> dict[str, Any]:
        return {
            "query": query,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "degraded": False,
            "degraded_reason": "",
            "http_status": None,
            "params": {},
            "results": [],
            "mixed_results": [],
            "total_estimated": None,
        }

    def _project_payload(
        self, query: str, params: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        out = self._empty_result(query)
        out["http_status"] = 200
        out["params"] = params
        web = payload.get("web") or {}
        web_results_raw = web.get("results") or []
        results: list[dict[str, Any]] = []
        for item in web_results_raw:
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
                "language": item.get("language"),
                "is_source_local": item.get("is_source_local"),
                "is_source_both": item.get("is_source_both"),
                "page_age": item.get("page_age"),
                "profile": (item.get("profile") or {}).get("name"),
            })
        out["results"] = results

        # Mixed/aggregated panel — tells us which non-web sections (news,
        # videos, FAQ, infobox) Brave attached.
        mixed = payload.get("mixed") or {}
        out["mixed_results"] = list(mixed.get("main") or [])
        out["total_estimated"] = web.get("results_count") or len(results)
        return out


__all__ = ["BraveSearchClient", "BRAVE_WEB_SEARCH_URL"]
