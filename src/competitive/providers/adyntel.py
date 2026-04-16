"""Adyntel API provider for Google Ads intelligence."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from ...common.circuit_breaker import CircuitBreaker
from ...common.cost_recorder import cost_recorder as _cost_recorder
from ..exceptions import AdyntelError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class AdyntelProvider:
    """Async client for the Adyntel Google Ads API.

    Uses POST-body authentication (api_key + email in request body).
    """

    def __init__(
        self,
        api_key: str,
        email: str,
        *,
        timeout: int = 30,
    ) -> None:
        self._api_key = api_key
        self._email = email
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60, name="adyntel")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.adyntel.com",
                timeout=httpx.Timeout(self._timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def search_google_ads(
        self,
        *,
        domain: str,
        media_type: str | None = None,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        """Search Google Ads for a domain with pagination."""
        if not self._breaker.allow_request():
            raise ProviderUnavailableError("Adyntel circuit open")

        client = self._get_client()

        all_ads: list[dict[str, Any]] = []
        continuation_token: str | None = None
        pages_fetched = 0

        for _ in range(max_pages):
            body: dict[str, Any] = {
                "api_key": self._api_key,
                "email": self._email,
                "company_domain": domain,
            }
            if media_type:
                body["media_type"] = media_type
            if continuation_token:
                body["continuation_token"] = continuation_token

            try:
                resp = await client.post("/google", json=body)
                # 204 = no data found, no credits charged
                if resp.status_code == 204:
                    break
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                self._handle_http_error(e)
                break  # unreachable
            except httpx.TimeoutException as e:
                self._breaker.record_failure()
                raise AdyntelError("Timeout") from e

            self._breaker.record_success()
            pages_fetched += 1

            data = resp.json()
            ads = data.get("ads", [])
            all_ads.extend(ads)

            continuation_token = data.get("continuation_token")
            if not continuation_token:
                break

        if pages_fetched > 0:
            await _cost_recorder.record(
                "adyntel",
                "search_google_ads",
                cost_usd=0.0088 * pages_fetched,
                metadata={
                    "pages": pages_fetched,
                    "domain": domain,
                    "session_id": os.environ.get("FREDDY_SESSION_ID"),
                },
            )

        return all_ads

    def _handle_http_error(self, e: httpx.HTTPStatusError) -> None:
        """Classify HTTP errors and update circuit breaker."""
        status_code = e.response.status_code
        if status_code == 401:
            raise AdyntelError("Invalid credentials") from e
        if status_code == 429:
            self._breaker.record_failure()
            raise AdyntelError("Rate limited") from e
        self._breaker.record_failure()
        raise AdyntelError("API error") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
