"""Platform-specific exceptions for video fetchers."""

from ..common.enums import Platform


class FetcherError(Exception):
    """Base exception for fetcher operations."""

    def __init__(self, platform: Platform, message: str) -> None:
        super().__init__(f"[{platform.value}] {message}")
        self.platform = platform


class VideoUnavailableError(FetcherError):
    """Video does not exist, is private, or cannot be accessed."""

    def __init__(self, platform: Platform, video_id: str) -> None:
        super().__init__(platform, f"Video unavailable: {video_id}")
        self.video_id = video_id


class CreatorNotFoundError(FetcherError):
    """Creator/channel does not exist."""

    def __init__(self, platform: Platform, handle: str) -> None:
        super().__init__(platform, f"Creator not found: {handle}")
        self.handle = handle


class RateLimitError(FetcherError):
    """API rate limit exceeded."""

    def __init__(
        self,
        platform: Platform,
        retry_after_seconds: int | None = None,
    ) -> None:
        msg = "Rate limit exceeded"
        if retry_after_seconds:
            msg += f" (retry after {retry_after_seconds}s)"
        super().__init__(platform, msg)
        self.retry_after_seconds = retry_after_seconds


class UrlExpiredError(FetcherError):
    """Video download URL has expired."""

    def __init__(self, platform: Platform, video_id: str) -> None:
        super().__init__(platform, f"Download URL expired for: {video_id}")
        self.video_id = video_id


class DownloadError(FetcherError):
    """Failed to download video content."""

    def __init__(self, platform: Platform, video_id: str, cause: str) -> None:
        super().__init__(platform, f"Download failed for {video_id}: {cause}")
        self.video_id = video_id
