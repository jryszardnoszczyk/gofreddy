"""Reality Defender API client for deepfake detection."""

import asyncio
import re
import time
from typing import Self
from urllib.parse import urlparse

import httpx

from .config import DeepfakeConfig
from .exceptions import (
    DeepfakeAPIError,
    DeepfakeRateLimitError,
    DeepfakeTimeoutError,
)
from .models import RealityDefenderResult, Verdict

# SSRF protection: only allow our R2 presigned URLs
ALLOWED_URL_PATTERNS = [
    r"^https://[a-zA-Z0-9-]+\.r2\.cloudflarestorage\.com/",
]


class RealityDefenderClient:
    """Reality Defender API client for deepfake detection."""

    # Cost per analysis in cents (Developer tier: $399/1000 scans = $0.40/scan)
    COST_PER_SCAN_CENTS = 40

    def __init__(self, config: DeepfakeConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self._config.reality_defender_base_url,
            headers={
                "Authorization": f"Bearer {self._config.reality_defender_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(
                connect=10.0,
                read=self._config.api_timeout_seconds,
                write=self._config.upload_timeout_seconds,
                pool=10.0,
            ),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            ),
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.__aexit__(None, None, None)

    def _validate_video_url(self, video_url: str) -> None:
        """SSRF protection: only allow presigned URLs from our storage."""
        parsed = urlparse(video_url)
        if parsed.scheme != "https":
            raise DeepfakeAPIError("Video URL must use HTTPS")
        if not any(re.match(pattern, video_url) for pattern in ALLOWED_URL_PATTERNS):
            raise DeepfakeAPIError(
                "Video URL must be a presigned URL from our storage"
            )

    async def analyze(self, video_url: str) -> RealityDefenderResult:
        """Analyze video for deepfakes via Reality Defender API."""
        self._validate_video_url(video_url)  # SSRF protection
        start_time = time.monotonic()

        for attempt in range(self._config.max_retries):
            try:
                # Submit for analysis
                response = await self._client.post(
                    "/detect/video", json={"url": video_url}
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise DeepfakeRateLimitError("Rate limited", retry_after)

                response.raise_for_status()
                job_data = response.json()
                request_id = job_data["request_id"]

                # Poll for results with exponential backoff
                result = await self._poll_for_result(request_id)

                processing_time = int((time.monotonic() - start_time) * 1000)

                return RealityDefenderResult(
                    score=result.get("manipulation_probability"),
                    verdict=self._map_verdict(result.get("verdict")),
                    indicators=result.get("indicators", []),
                    processing_time_ms=processing_time,
                    cost_cents=self.COST_PER_SCAN_CENTS,
                )

            except httpx.TimeoutException:
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(
                        self._config.base_delay_seconds * (2**attempt)
                    )
                    continue
                raise DeepfakeTimeoutError("Reality Defender request timeout")

            except httpx.HTTPStatusError as e:
                if (
                    e.response.status_code >= 500
                    and attempt < self._config.max_retries - 1
                ):
                    await asyncio.sleep(
                        self._config.base_delay_seconds * (2**attempt)
                    )
                    continue
                raise DeepfakeAPIError(f"Reality Defender API error: {e}")

        raise DeepfakeAPIError("Max retries exceeded")

    async def _poll_for_result(self, request_id: str) -> dict:
        """Poll for analysis completion with exponential backoff."""
        # Exponential backoff: 0.5s, 0.5s, 1s, 1s, 2s, 2s, 3s, 3s, 5s, 5s, then 10s...
        intervals = [0.5, 0.5, 1, 1, 2, 2, 3, 3, 5, 5]
        max_time = self._config.api_timeout_seconds
        elapsed = 0.0

        while elapsed < max_time:
            idx = min(len(intervals) - 1, int(elapsed / 5))
            interval = intervals[idx] if idx < len(intervals) else 10.0
            await asyncio.sleep(interval)
            elapsed += interval

            response = await self._client.get(f"/detect/status/{request_id}")
            response.raise_for_status()
            data = response.json()

            if data["status"] == "completed":
                return data["result"]

            if data["status"] == "failed":
                raise DeepfakeAPIError(data.get("error", "Analysis failed"))

        raise DeepfakeTimeoutError("Polling timeout")

    @staticmethod
    def _map_verdict(verdict: str | None) -> Verdict | None:
        """Map API verdict to our enum."""
        if verdict is None:
            return None
        mapping = {
            "real": Verdict.AUTHENTIC,
            "fake": Verdict.MANIPULATED,
            "uncertain": Verdict.UNCERTAIN,
        }
        return mapping.get(verdict.lower(), Verdict.UNCERTAIN)
