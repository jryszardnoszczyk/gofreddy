"""Base fetcher with shared functionality."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Awaitable, Callable, Self
from urllib.parse import urlparse

import httpx

from ..common.enums import Platform
from .config import FetcherSettings
from .exceptions import DownloadError, UrlExpiredError
from .models import BatchFetchResult, FetchError, FetchErrorType, VideoResult, VideoStats

if TYPE_CHECKING:
    from ..storage import R2VideoStorage

logger = logging.getLogger(__name__)

# Handle validation pattern
HANDLE_PATTERN = re.compile(r"^[a-zA-Z0-9_.]{1,30}$")

# Private IP ranges for SSRF protection
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
]


class BaseFetcher(ABC):
    """Base class for platform video fetchers."""

    def __init__(
        self,
        storage: R2VideoStorage,
        settings: FetcherSettings | None = None,
    ) -> None:
        self.storage = storage
        self.settings = settings or FetcherSettings()
        self._semaphore = asyncio.Semaphore(
            self.settings.max_concurrent_downloads
        )
        self._http_client: httpx.AsyncClient | None = None

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Return the platform this fetcher handles."""
        ...

    async def __aenter__(self) -> Self:
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=self.settings.download_timeout_seconds,
                write=30.0,
                pool=10.0,
            )
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._http_client:
            try:
                await self._http_client.aclose()
            except RuntimeError as e:
                # Can happen during test teardown if loop is already closed.
                if "Event loop is closed" not in str(e):
                    raise
                logger.warning("fetcher_client_close_skipped_event_loop_closed")
            finally:
                self._http_client = None

    def _validate_handle(self, handle: str) -> None:
        """Validate creator handle format for security."""
        if not HANDLE_PATTERN.match(handle):
            raise ValueError(
                f"Invalid handle '{handle}': must be 1-30 alphanumeric characters, underscores, or periods"
            )

    def _validate_download_url(self, url: str) -> None:
        """Validate download URL to prevent SSRF attacks."""
        parsed = urlparse(url)

        # Must be HTTPS
        if parsed.scheme != "https":
            raise DownloadError(
                self.platform, "unknown",
                f"Download URL must be HTTPS, got: {parsed.scheme}"
            )

        # Resolve hostname and check for private IPs
        try:
            hostname = parsed.netloc.split(":")[0]
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            for private_range in PRIVATE_IP_RANGES:
                if ip in private_range:
                    raise DownloadError(
                        self.platform, "unknown",
                        f"Download URL resolves to private IP: {ip_str}"
                    )
        except socket.gaierror:
            pass  # Allow DNS failures - let download fail naturally

    async def fetch_video(
        self,
        platform: Platform,
        video_id: str,
    ) -> VideoResult:
        """Fetch a single video, using cache if available."""
        # Check R2 cache first
        r2_key = f"videos/{platform.value}/{video_id}.mp4"
        if await self.storage.exists(platform, video_id):
            metadata = await self.storage.get_metadata(platform, video_id)
            return VideoResult(
                video_id=video_id,
                platform=platform,
                r2_key=r2_key,
                file_size_bytes=metadata.size_bytes if metadata else None,
                fetched_at=datetime.now(timezone.utc),
            )

        # Fetch from platform
        async with self._semaphore:
            return await self._fetch_and_store(video_id)

    async def fetch_creator_videos(
        self,
        platform: Platform,
        creator_handle: str,
        limit: int = 50,
    ) -> BatchFetchResult:
        """Fetch videos from a creator's profile."""
        # Validate handle before any API calls (security)
        self._validate_handle(creator_handle)

        # Cap limit at 100 per protocol spec
        limit = min(limit, 100)

        # Get list of video stats from platform
        video_stats = await self._list_creator_videos(creator_handle, limit)
        video_ids = [vs.video_id for vs in video_stats]

        # Fetch concurrently with semaphore
        results: list[VideoResult] = []
        errors: list[FetchError] = []

        async def fetch_one(vid: str) -> VideoResult | FetchError:
            try:
                return await self.fetch_video(self.platform, vid)
            except Exception as e:
                return self._exception_to_fetch_error(vid, e)

        tasks = [fetch_one(vid) for vid in video_ids]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        for outcome in outcomes:
            if isinstance(outcome, VideoResult):
                results.append(outcome)
            elif isinstance(outcome, FetchError):
                errors.append(outcome)
            elif isinstance(outcome, Exception):
                # Unexpected exception
                errors.append(
                    FetchError(
                        video_id="unknown",
                        platform=self.platform,
                        error_type=FetchErrorType.PLATFORM_ERROR,
                        message=str(outcome),
                    )
                )

        return BatchFetchResult(results=results, errors=errors)

    @abstractmethod
    async def _fetch_and_store(self, video_id: str) -> VideoResult:
        """Platform-specific: fetch video and store to R2."""
        ...

    @abstractmethod
    async def _list_creator_videos(
        self, handle: str, limit: int
    ) -> list[VideoStats]:
        """Platform-specific: list video IDs and per-video stats for a creator."""
        ...

    async def _download_with_retry(
        self,
        video_id: str,
        url: str,
        get_fresh_url: Callable[[], Awaitable[str]],
    ) -> Path:
        """Download video with URL expiration handling.

        Uses httpx streaming for memory-efficient downloads.
        Returns path to temp file - caller is responsible for cleanup.
        """
        # Validate URL before download (SSRF prevention)
        self._validate_download_url(url)

        # Use NamedTemporaryFile for explicit lifecycle control
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        for attempt in range(self.settings.max_url_refetch_attempts + 1):
            current_url = url if attempt == 0 else await get_fresh_url()
            if attempt > 0:
                self._validate_download_url(current_url)

            try:
                async with self._http_client.stream("GET", current_url) as response:
                    if response.status_code in (403, 404, 410):
                        if attempt < self.settings.max_url_refetch_attempts:
                            continue  # Try with fresh URL
                        raise UrlExpiredError(self.platform, video_id)

                    response.raise_for_status()

                    # Stream to file in chunks (memory-efficient)
                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)

                    return temp_path

            except (httpx.HTTPError, asyncio.TimeoutError) as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise DownloadError(self.platform, video_id, str(e)) from e

        raise UrlExpiredError(self.platform, video_id)

    def _exception_to_fetch_error(
        self, video_id: str, exc: Exception
    ) -> FetchError:
        """Convert exception to FetchError for batch results."""
        from .exceptions import (
            RateLimitError,
            VideoUnavailableError,
        )

        if isinstance(exc, VideoUnavailableError):
            return FetchError(
                video_id=video_id,
                platform=self.platform,
                error_type=FetchErrorType.NOT_FOUND,
                message=str(exc),
            )
        if isinstance(exc, RateLimitError):
            return FetchError(
                video_id=video_id,
                platform=self.platform,
                error_type=FetchErrorType.RATE_LIMITED,
                message=str(exc),
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        return FetchError(
            video_id=video_id,
            platform=self.platform,
            error_type=FetchErrorType.PLATFORM_ERROR,
            message=str(exc),
        )
