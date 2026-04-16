"""Video fetcher implementations for social media platforms."""

from .base import BaseFetcher
from .config import FetcherSettings
from .exceptions import (
    CreatorNotFoundError,
    DownloadError,
    FetcherError,
    RateLimitError,
    UrlExpiredError,
    VideoUnavailableError,
)
from .instagram import InstagramFetcher
from .models import BatchFetchResult, FetchError, FetchErrorType, VideoResult
from .protocols import VideoFetcher
from .tiktok import TikTokFetcher
from .youtube import YouTubeFetcher

__all__ = [
    # Protocol
    "VideoFetcher",
    # Base
    "BaseFetcher",
    # Implementations
    "TikTokFetcher",
    "InstagramFetcher",
    "YouTubeFetcher",
    # Models
    "VideoResult",
    "FetchError",
    "FetchErrorType",
    "BatchFetchResult",
    # Config
    "FetcherSettings",
    # Exceptions
    "FetcherError",
    "VideoUnavailableError",
    "CreatorNotFoundError",
    "RateLimitError",
    "UrlExpiredError",
    "DownloadError",
]
