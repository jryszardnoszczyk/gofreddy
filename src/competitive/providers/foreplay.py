"""Foreplay API provider for Meta, TikTok, and LinkedIn ad intelligence."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx

from ...common.circuit_breaker import CircuitBreaker
from ...common.cost_recorder import cost_recorder as _cost_recorder
from ..exceptions import ForeplayError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class ForeplayProvider:
    """Async client for the Foreplay public API.

    Supports domain-based brand lookup and ad retrieval across
    Meta, TikTok, and LinkedIn platforms.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: int = 30,
        daily_credit_limit: int = 5000,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._daily_credit_limit = daily_credit_limit
        self._client: httpx.AsyncClient | None = None
        self._breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60, name="foreplay")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://public.api.foreplay.co",
                headers={"Authorization": self._api_key},
                timeout=httpx.Timeout(self._timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def search_ads_by_domain(
        self,
        domain: str,
        *,
        limit: int = 50,
        live_only: bool = False,
        display_format: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search ads by domain: resolve brand ID, then fetch ads."""
        if not self._breaker.allow_request():
            raise ProviderUnavailableError("Foreplay circuit open")

        client = self._get_client()

        # Step 1: Resolve domain to brand ID
        try:
            brand_resp = await client.get(
                "/api/brand/getBrandsByDomain",
                params={"domain": domain, "limit": 10, "order": "most_ranked"},
            )
            brand_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
            return []  # unreachable, _handle_http_error always raises
        except httpx.TimeoutException as e:
            self._breaker.record_failure()
            raise ForeplayError("Timeout") from e

        self._breaker.record_success()
        body = brand_resp.json()
        brands = body.get("data", body) if isinstance(body, dict) else body
        if not brands or not isinstance(brands, list):
            return []

        # Validate that the top brand's domain matches the queried domain.
        # Foreplay uses substring matching ("sketch" → "mangasketch.com"),
        # so we must reject mismatches to avoid contamination (#11).
        matched_brand = None
        for brand in brands:
            brand_domain = (brand.get("domain") or "").strip().lower()
            brand_domain = brand_domain.removeprefix("www.")
            if brand_domain == domain.strip().lower().removeprefix("www."):
                matched_brand = brand
                break

        if matched_brand is None:
            brand_domains = [b.get("domain", "?") for b in brands[:5]]
            logger.warning(
                "foreplay_brand_domain_mismatch: queried=%s, got=%s",
                domain,
                brand_domains,
            )
            return []

        brand_id = matched_brand.get("id")
        if not brand_id:
            return []

        # Step 2: Fetch ads by brand ID
        try:
            params: dict[str, Any] = {"brand_ids": brand_id, "limit": min(limit, 250)}
            if live_only:
                params["live"] = True
            if display_format:
                params["display_format"] = display_format

            ads_resp = await client.get("/api/brand/getAdsByBrandId", params=params)
            ads_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
            return []
        except httpx.TimeoutException as e:
            self._breaker.record_failure()
            raise ForeplayError("Timeout") from e

        self._breaker.record_success()
        raw = ads_resp.json()
        if isinstance(raw, dict):
            ads = raw.get("data", raw.get("ads", []))
        elif isinstance(raw, list):
            ads = raw
        else:
            ads = []
        if not isinstance(ads, list):
            ads = []

        # Track credits
        self._track_credits(ads_resp, len(ads))

        await _cost_recorder.record(
            "foreplay",
            "search_ads",
            cost_usd=len(ads) * 0.001,
            metadata={
                "ads_returned": len(ads),
                "domain": domain,
                "session_id": os.environ.get("FREDDY_SESSION_ID"),
            },
        )

        return ads

    def _handle_http_error(self, e: httpx.HTTPStatusError) -> None:
        """Classify HTTP errors and update circuit breaker."""
        status_code = e.response.status_code
        if status_code == 401:
            raise ForeplayError("Invalid API key") from e
        if status_code == 402:
            raise ForeplayError("Out of credits") from e
        if status_code == 429:
            self._breaker.record_failure()
            raise ForeplayError("Rate limited") from e
        self._breaker.record_failure()
        raise ForeplayError("API error") from e

    def _track_credits(self, response: httpx.Response, ads_count: int) -> None:
        """Log credit consumption from response headers."""
        credits_remaining = response.headers.get("X-Credits-Remaining")
        if credits_remaining is None:
            return

        try:
            remaining = int(credits_remaining)
        except (ValueError, TypeError):
            return

        budget = self._daily_credit_limit
        if remaining < budget * 0.05:
            logger.warning(
                "foreplay_credits_critical",
                extra={"remaining": remaining, "budget": budget},
            )
        elif remaining < budget * 0.20:
            logger.warning(
                "foreplay_credits_low",
                extra={"remaining": remaining, "budget": budget},
            )
        elif remaining < budget * 0.50:
            logger.info(
                "foreplay_credits_half",
                extra={"remaining": remaining, "budget": budget},
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
