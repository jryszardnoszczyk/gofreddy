"""LIPINC lip-sync detection via managed hosting (Replicate)."""

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
from .models import Confidence, LipSyncResult

# SSRF protection: only allow our R2 presigned URLs
ALLOWED_URL_PATTERNS = [
    r"^https://[a-zA-Z0-9-]+\.r2\.cloudflarestorage\.com/",
]


class LIPINCAnalyzer:
    """LIPINC lip-sync detection via managed hosting (Replicate).

    LIPINC detects deepfakes by identifying temporal inconsistencies
    in mouth movements. Score of 1.0 = authentic, 0.0 = manipulated.
    """

    # Cost per analysis via Replicate (fallback estimate)
    COST_PER_ANALYSIS_CENTS = 15
    # Replicate GPU rate: Nvidia T4 = $0.000225/sec (see replicate.com/pricing)
    _GPU_RATE_PER_SEC = 0.000225

    def __init__(self, config: DeepfakeConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._last_predict_time: float | None = None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self._config.lipinc_base_url,
            headers={
                "Authorization": f"Token {self._config.lipinc_api_key.get_secret_value()}",
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

    @property
    def last_cost_usd(self) -> float | None:
        """Actual cost of the last analysis from Replicate GPU metrics."""
        if self._last_predict_time is not None:
            return round(self._last_predict_time * self._GPU_RATE_PER_SEC, 6)
        return None

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

    async def analyze(self, video_url: str) -> LipSyncResult:
        """Analyze video for lip-sync manipulation."""
        self._validate_video_url(video_url)  # SSRF protection
        start_time = time.monotonic()

        for attempt in range(self._config.max_retries):
            try:
                # Submit to Replicate
                response = await self._client.post(
                    "/predictions",
                    json={
                        "version": self._config.lipinc_model_version,
                        "input": {"video_url": video_url},
                    },
                )

                if response.status_code == 429:
                    if attempt < self._config.max_retries - 1:
                        await asyncio.sleep(
                            self._config.base_delay_seconds * (2**attempt)
                        )
                        continue
                    raise DeepfakeRateLimitError("LIPINC rate limited")

                response.raise_for_status()
                prediction = response.json()

                # Poll for result with exponential backoff
                prediction_data = await self._poll_for_result(prediction["id"])
                result = prediction_data.get("output") or {}

                # Extract actual GPU time for cost tracking
                metrics = prediction_data.get("metrics") or {}
                self._last_predict_time = metrics.get("predict_time")

                processing_time = int((time.monotonic() - start_time) * 1000)

                # Handle no-face case
                if result.get("no_face_detected"):
                    return LipSyncResult(
                        score=None,
                        anomaly_detected=False,
                        confidence=None,
                        error="no_face_detected",
                        processing_time_ms=processing_time,
                    )

                score = result.get("authenticity_score", 0.5)
                anomaly = score < (1 - self._config.deepfake_threshold)

                return LipSyncResult(
                    score=score,
                    anomaly_detected=anomaly,
                    confidence=self._score_to_confidence(score),
                    processing_time_ms=processing_time,
                )

            except httpx.TimeoutException:
                if attempt < self._config.max_retries - 1:
                    await asyncio.sleep(
                        self._config.base_delay_seconds * (2**attempt)
                    )
                    continue
                raise DeepfakeTimeoutError("LIPINC request timeout")

            except httpx.HTTPStatusError as e:
                if (
                    e.response.status_code >= 500
                    and attempt < self._config.max_retries - 1
                ):
                    await asyncio.sleep(
                        self._config.base_delay_seconds * (2**attempt)
                    )
                    continue
                raise DeepfakeAPIError(f"LIPINC API error: {e}")

        raise DeepfakeAPIError("Max retries exceeded")

    async def _poll_for_result(self, prediction_id: str) -> dict:
        """Poll Replicate for prediction completion with exponential backoff."""
        # Exponential backoff: 0.5s, 0.5s, 1s, 1s, 2s, 2s, 3s, 3s, 5s, 5s, then 10s...
        intervals = [0.5, 0.5, 1, 1, 2, 2, 3, 3, 5, 5]
        max_time = self._config.api_timeout_seconds
        elapsed = 0.0

        while elapsed < max_time:
            idx = min(len(intervals) - 1, int(elapsed / 5))
            interval = intervals[idx] if idx < len(intervals) else 10.0
            await asyncio.sleep(interval)
            elapsed += interval

            response = await self._client.get(f"/predictions/{prediction_id}")
            response.raise_for_status()
            data = response.json()

            if data["status"] == "succeeded":
                return data

            if data["status"] == "failed":
                raise DeepfakeAPIError(data.get("error", "LIPINC analysis failed"))

        raise DeepfakeTimeoutError("LIPINC polling timeout")

    def _score_to_confidence(self, score: float) -> Confidence:
        """Map score to confidence level."""
        # Score is authenticity (1.0 = authentic)
        certainty = abs(score - 0.5) * 2  # Distance from uncertainty
        if certainty >= 0.7:
            return Confidence.HIGH
        elif certainty >= 0.4:
            return Confidence.MEDIUM
        return Confidence.LOW
