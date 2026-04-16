"""Protocol definitions for video fetching."""

from typing import Protocol

from ..common.enums import Platform
from .models import BatchFetchResult, VideoResult


class VideoFetcher(Protocol):
    """
    Protocol for fetching videos from social platforms.

    Implementations should:
    - Check R2 cache before fetching from platform
    - Download videos immediately (platform URLs expire)
    - Store to R2 after download
    - Handle partial failures in batch operations
    """

    async def fetch_video(
        self,
        platform: Platform,
        video_id: str,
    ) -> VideoResult:
        """
        Fetch a single video by ID.

        Raises:
            VideoNotFoundError: Video does not exist
            PlatformError: Platform API error
        """
        ...

    async def fetch_creator_videos(
        self,
        platform: Platform,
        creator_handle: str,
        limit: int = 50,
    ) -> BatchFetchResult:
        """
        Fetch recent videos from a creator.

        Returns partial results if some videos fail.
        Limit capped at 100 videos per request.
        Uses concurrent downloads with semaphore (max 5 parallel).
        """
        ...
