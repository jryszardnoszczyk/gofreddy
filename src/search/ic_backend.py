"""Influencers.club (IC) search backend for creator discovery and enrichment."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Self

import httpx
from aiolimiter import AsyncLimiter

from ..common.circuit_breaker import CircuitBreaker
from ..common.cost_recorder import (
    IC_COST_PER_AUDIENCE_OVERLAP,
    IC_COST_PER_CONNECTED_SOCIALS,
    IC_COST_PER_CONTENT,
    IC_COST_PER_DISCOVERY_CREATOR,
    IC_COST_PER_ENRICHMENT_FULL,
    IC_COST_PER_ENRICHMENT_RAW,
    IC_COST_PER_SIMILAR,
    cost_recorder as _cost_recorder,
)
from .exceptions import ICUnavailableError

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = frozenset({429, 500, 502, 503})
_UNAVAILABLE_CODES = frozenset({401, 403})

# Supported discovery platforms (IC docs §1)
_DISCOVERY_PLATFORMS = frozenset({"instagram", "youtube", "tiktok", "twitch", "twitter", "onlyfans"})

# Enrichment supports more platforms (11 total) but we only validate discovery for now
_ENRICHMENT_PLATFORMS = frozenset({
    "instagram", "youtube", "tiktok", "onlyfans", "twitter",
    "snapchat", "discord", "pinterest", "facebook", "linkedin", "twitch",
})

# Content API platforms
_CONTENT_PLATFORMS = frozenset({"instagram", "tiktok", "youtube"})

# Validate user_id / handle format to prevent path traversal
_SAFE_HANDLE_RE = re.compile(r"^[a-zA-Z0-9._@-]{1,200}$")

# Validate email format (defense-in-depth — prevents burning credits on garbage)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Cost map for request logging
_ENDPOINT_COSTS: dict[str, float] = {
    "/public/v1/discovery/": IC_COST_PER_DISCOVERY_CREATOR,
    "/public/v1/discovery/creators/similar/": IC_COST_PER_SIMILAR,
    "/public/v1/creators/enrich/handle/full/": IC_COST_PER_ENRICHMENT_FULL,
    "/public/v1/creators/enrich/handle/raw/": IC_COST_PER_ENRICHMENT_RAW,
    "/public/v1/creators/content/posts/": IC_COST_PER_CONTENT,
    "/public/v1/creators/content/details/": IC_COST_PER_CONTENT,
    "/public/v1/creators/socials/": IC_COST_PER_CONNECTED_SOCIALS,
    "/public/v1/creators/audience/overlap/": IC_COST_PER_AUDIENCE_OVERLAP,
}


class ICBackend:
    """Influencers.club API client with circuit breaker, retry, and rate limiting.

    Lifecycle: Use __aenter__/__aexit__.
    Create in lifespan startup, close in cleanup. NEVER use ``async with`` elsewhere.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api-dashboard.influencers.club",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("IC API key is required")
        if not base_url.startswith("https://"):
            raise ValueError("IC base URL must use HTTPS (Bearer token over HTTP leaks credentials)")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=60, name="ic")
        # 300 requests per 60 seconds (IC rate limit)
        self._rate_limiter = AsyncLimiter(300, 60)

    async def __aenter__(self) -> Self:
        self._semaphore = asyncio.Semaphore(10)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(connect=5.0, read=self._timeout, write=5.0, pool=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=30.0),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            follow_redirects=False,
        )
        # Health check via credits endpoint (non-blocking)
        try:
            credits = await self.get_credits()
            credits_left = credits.get("credits_left", "?")
            logger.info("ic_health_check: ok, credits_left=%s", credits_left)
        except Exception:
            logger.warning("ic_health_check: failed (non-blocking)", exc_info=True)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.__aexit__(None, None, None)

    # ── Creator Discovery ─────────────────────────────────────────

    async def discover(
        self,
        platform: str,
        filters: dict[str, Any] | None = None,
        *,
        page: int = 0,
        limit: int = 50,
        sort_by: str = "relevancy",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """POST /public/v1/discovery/ — 0.01 credit/creator returned."""
        self._validate_platform(platform, _DISCOVERY_PLATFORMS)
        body: dict[str, Any] = {
            "platform": platform,
            "paging": {"limit": min(limit, 50), "page": page},
            "sort": {"sort_by": sort_by, "sort_order": sort_order},
        }
        if filters:
            body["filters"] = filters
        return await self._request("POST", "/public/v1/discovery/", body=body)

    async def find_similar(
        self,
        platform: str,
        handle: str,
        *,
        limit: int = 20,
    ) -> dict[str, Any]:
        """POST /public/v1/discovery/creators/similar/ — 0.01/creator."""
        self._validate_platform(platform, _DISCOVERY_PLATFORMS)
        self._validate_handle(handle)
        body = {
            "platform": platform,
            "handle": handle,
            "paging": {"limit": min(limit, 50)},
        }
        return await self._request("POST", "/public/v1/discovery/creators/similar/", body=body)

    async def audience_overlap(
        self,
        platform: str,
        handles: list[str],
    ) -> dict[str, Any]:
        """POST /public/v1/creators/audience/overlap/ — 1.0 credit."""
        self._validate_platform(platform, _DISCOVERY_PLATFORMS)
        for h in handles:
            self._validate_handle(h)
        if len(handles) < 2 or len(handles) > 10:
            raise ValueError("audience_overlap requires 2-10 handles")
        body = {"platform": platform, "handles": handles}
        return await self._request("POST", "/public/v1/creators/audience/overlap/", body=body)

    # ── Creator Enrichment ────────────────────────────────────────

    async def enrich_full(
        self,
        platform: str,
        handle: str,
        *,
        include_audience_data: bool = True,
    ) -> dict[str, Any]:
        """POST /public/v1/creators/enrich/handle/full/ — 1.0 credit."""
        self._validate_platform(platform, _ENRICHMENT_PLATFORMS)
        self._validate_handle(handle)
        body: dict[str, Any] = {"platform": platform, "handle": handle}
        if include_audience_data:
            body["include_audience_data"] = True
        return await self._request("POST", "/public/v1/creators/enrich/handle/full/", body=body)

    async def enrich_raw(
        self,
        platform: str,
        handle: str,
    ) -> dict[str, Any]:
        """POST /public/v1/creators/enrich/handle/raw/ — 0.03 credit."""
        self._validate_platform(platform, _ENRICHMENT_PLATFORMS)
        self._validate_handle(handle)
        body = {"platform": platform, "handle": handle}
        return await self._request("POST", "/public/v1/creators/enrich/handle/raw/", body=body)

    async def enrich_email(
        self,
        email: str,
        *,
        enrich_type: str = "advanced",
    ) -> dict[str, Any]:
        """POST /public/v1/creators/enrich/email/{type}/ — 0.1-2.0 credits."""
        if enrich_type not in ("basic", "advanced"):
            raise ValueError(f"Invalid enrich_type: {enrich_type}")
        if not _EMAIL_RE.match(email):
            raise ValueError(f"Invalid email format: {email!r}")
        body = {"email": email}
        path = f"/public/v1/creators/enrich/email/{enrich_type}/"
        if enrich_type == "basic":
            path = "/public/v1/creators/enrich/email/"
        return await self._request("POST", path, body=body)

    async def connected_socials(
        self,
        platform: str,
        handle: str,
    ) -> dict[str, Any]:
        """POST /public/v1/creators/socials/ — 0.5 credit."""
        self._validate_platform(platform, _ENRICHMENT_PLATFORMS)
        self._validate_handle(handle)
        body = {"platform": platform, "handle": handle}
        return await self._request("POST", "/public/v1/creators/socials/", body=body)

    # ── Creator Content ───────────────────────────────────────────

    async def get_content(
        self,
        platform: str,
        handle: str,
        *,
        page: int = 0,
    ) -> dict[str, Any]:
        """POST /public/v1/creators/content/posts/ — 0.03 credit."""
        self._validate_platform(platform, _CONTENT_PLATFORMS)
        self._validate_handle(handle)
        body: dict[str, Any] = {
            "platform": platform,
            "handle": handle,
            "paging": {"page": page},
        }
        return await self._request("POST", "/public/v1/creators/content/posts/", body=body)

    async def get_post_details(
        self,
        platform: str,
        handle: str,
        post_url: str,
        *,
        content_type: str = "data",
    ) -> dict[str, Any]:
        """POST /public/v1/creators/content/details/ — 0.03 credit."""
        self._validate_platform(platform, _CONTENT_PLATFORMS)
        self._validate_handle(handle)
        if content_type not in ("data", "comments", "transcript", "audio"):
            raise ValueError(f"Invalid content_type: {content_type}")
        body = {
            "platform": platform,
            "handle": handle,
            "url": post_url,
            "type": content_type,
        }
        return await self._request("POST", "/public/v1/creators/content/details/", body=body)

    # ── Account Info ──────────────────────────────────────────────

    async def get_credits(self) -> dict[str, Any]:
        """GET /public/v1/accounts/credits/ — free."""
        return await self._request("GET", "/public/v1/accounts/credits/")

    async def get_classifier(
        self,
        classifier_type: str,
        *,
        platform: str | None = None,
    ) -> Any:
        """GET /public/v1/discovery/classifier/{type}/ — free.

        classifier_type: languages, locations, brands, yt-topics, games,
                         audience-brand-categories, audience-brand-names,
                         audience-interests, audience-locations
        """
        valid_types = {
            "languages", "locations", "brands", "yt-topics", "games",
            "audience-brand-categories", "audience-brand-names",
            "audience-interests", "audience-locations",
        }
        if classifier_type not in valid_types:
            raise ValueError(f"Invalid classifier_type: {classifier_type}")
        path = f"/public/v1/discovery/classifier/{classifier_type}/"
        if platform:
            self._validate_platform(platform, _DISCOVERY_PLATFORMS)
            path = f"/public/v1/discovery/classifier/{classifier_type}/{platform}/"
        return await self._request("GET", path)

    # ── Internal Request Handling ─────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> Any:
        """HTTP request with circuit breaker, rate limiter, semaphore, retry, cost tracking."""
        if self._circuit_breaker.is_open():
            raise ICUnavailableError(0, "Circuit breaker open — IC temporarily disabled")

        if self._client is None or self._semaphore is None:
            raise RuntimeError("ICBackend not initialized — call __aenter__() first")

        last_error: httpx.HTTPStatusError | None = None

        for attempt in range(max_retries):
            start = time.monotonic()
            try:
                # Rate limiter BEFORE semaphore (as specified in plan)
                await self._rate_limiter.acquire()
                async with self._semaphore:
                    if method.upper() == "GET":
                        resp = await self._client.get(path, params=params)
                    elif method.upper() == "POST":
                        resp = await self._client.post(path, json=body)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                latency_ms = (time.monotonic() - start) * 1000
                resp.raise_for_status()
                self._circuit_breaker.record_success()

                data = resp.json()

                # Parse and log credits_left (IC returns it as a string)
                # Classifier endpoints return lists, not dicts
                credits_left_float: float | None = None
                if isinstance(data, dict):
                    credits_left = data.get("credits_left")
                    if credits_left is not None:
                        try:
                            credits_left_float = float(str(credits_left))
                        except (ValueError, TypeError):
                            pass

                logger.info(
                    "ic_call: method=%s path=%s status=%d latency_ms=%.0f credits_left=%s",
                    method, path, resp.status_code, latency_ms,
                    credits_left_float if credits_left_float is not None else "?",
                )

                # Record cost
                cost = _ENDPOINT_COSTS.get(path, 0.0)
                if cost > 0:
                    # For discovery, cost is per-creator returned
                    if isinstance(data, dict) and path == "/public/v1/discovery/" and isinstance(data.get("accounts"), list):
                        cost = cost * len(data["accounts"])
                    await _cost_recorder.record("ic", path, cost_usd=cost or None)

                return data

            except httpx.HTTPStatusError as e:
                latency_ms = (time.monotonic() - start) * 1000
                self._circuit_breaker.record_failure()
                logger.warning(
                    "ic_error: method=%s path=%s status=%d latency_ms=%.0f attempt=%d",
                    method, path, e.response.status_code, latency_ms, attempt + 1,
                )

                if e.response.status_code in _UNAVAILABLE_CODES:
                    detail = (
                        "Authentication failed" if e.response.status_code == 401
                        else "Access forbidden"
                    )
                    raise ICUnavailableError(e.response.status_code, detail) from e

                if e.response.status_code == 422:
                    log_body_keys = list(body.keys()) if body else []
                    logger.error(
                        "ic_bad_request: path=%s keys=%s response=%s",
                        path, log_body_keys, e.response.text[:200],
                    )
                    return {}

                if e.response.status_code in _RETRYABLE_CODES and attempt < max_retries - 1:
                    retry_after = e.response.headers.get("Retry-After")
                    try:
                        delay = min(float(retry_after), 30.0) if retry_after else 2 ** attempt
                    except (ValueError, TypeError):
                        delay = 2 ** attempt
                    await asyncio.sleep(delay)
                    last_error = e
                    continue

                if e.response.status_code == 400:
                    logger.warning(
                        "ic_bad_request_400: path=%s body_keys=%s response=%s",
                        path, list((body or {}).keys()), e.response.text[:500],
                    )
                logger.warning("ic_unhandled_status: path=%s status=%d", path, e.response.status_code)
                last_error = e
                break

            except httpx.HTTPError as e:
                latency_ms = (time.monotonic() - start) * 1000
                self._circuit_breaker.record_failure()
                logger.warning(
                    "ic_network_error: method=%s path=%s latency_ms=%.0f attempt=%d",
                    method, path, latency_ms, attempt + 1,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ICUnavailableError(0, "Network error connecting to IC") from e

        if last_error:
            status = last_error.response.status_code
            if status in _RETRYABLE_CODES:
                raise ICUnavailableError(status, f"IC returned {status} after {max_retries} retries")
        return {}

    # ── Validation Helpers ────────────────────────────────────────

    @staticmethod
    def _validate_platform(platform: str, valid: frozenset[str]) -> None:
        """Validate platform string against allowed set."""
        if platform not in valid:
            raise ValueError(f"Unsupported platform: {platform} (valid: {sorted(valid)})")

    @staticmethod
    def _validate_handle(handle: str) -> None:
        """Validate handle format to prevent path traversal / injection."""
        if not _SAFE_HANDLE_RE.match(handle):
            raise ValueError(f"Invalid handle format: {handle!r}")
