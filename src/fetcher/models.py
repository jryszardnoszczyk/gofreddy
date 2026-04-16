"""Data models for video fetching operations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ..common.enums import Platform


@dataclass(frozen=True)
class AudioTrackInfo:
    """Audio track metadata (primarily TikTok)."""

    title: str | None = None
    artist: str | None = None
    is_original: bool | None = None


@dataclass(frozen=True)
class VideoResult:
    """Result of fetching a video."""

    video_id: str
    platform: Platform
    r2_key: str
    title: str | None = None
    description: str | None = None
    creator_username: str | None = None
    creator_id: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    posted_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_size_bytes: int | None = None
    transcript_text: str | None = None
    thumbnail_url: str | None = None
    share_count: int | None = None
    hashtags: list[str] | None = None
    mentions: list[str] | None = None
    audio_track: AudioTrackInfo | None = None


class FetchErrorType(str, Enum):
    """Types of fetch errors."""

    NOT_FOUND = "not_found"
    PRIVATE = "private"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    PLATFORM_ERROR = "platform_error"


@dataclass(frozen=True)
class FetchError:
    """Error during video fetch with recovery guidance."""

    video_id: str
    platform: Platform
    error_type: FetchErrorType
    message: str
    retryable: bool = False
    retry_after_seconds: int | None = None
    alternative_action: str | None = None

    def to_agent_message(self) -> str:
        """Format for agent consumption."""
        msg = f"{self.error_type.value}: {self.message}"
        if self.retryable and self.retry_after_seconds:
            msg += f" (retry after {self.retry_after_seconds}s)"
        if self.alternative_action:
            msg += f" Suggestion: {self.alternative_action}"
        return msg


@dataclass
class BatchFetchResult:
    """Result of batch fetch operation."""

    results: list[VideoResult]
    errors: list[FetchError]

    @property
    def success_rate(self) -> float:
        """Calculate success rate of batch operation."""
        total = len(self.results) + len(self.errors)
        return len(self.results) / total if total > 0 else 0.0


# ─── Fraud Detection Models ─────────────────────────────────────────────────


@dataclass(frozen=True)
class FollowerProfile:
    """Profile data for a follower (fraud detection)."""

    username: str
    has_profile_pic: bool = True
    bio: str | None = None
    post_count: int = 0
    follower_count: int | None = None
    following_count: int | None = None


@dataclass(frozen=True)
class CommentData:
    """Comment data for bot detection analysis."""

    text: str
    username: str
    like_count: int | None = None
    posted_at: datetime | None = None
    reply_count: int | None = None
    display_name: str | None = None


@dataclass(frozen=True)
class CreatorStats:
    """Creator profile statistics for fraud analysis."""

    username: str
    platform: Platform
    follower_count: int | None = None
    following_count: int | None = None
    video_count: int | None = None
    total_likes: int | None = None
    total_views: int | None = None
    avg_likes: float | None = None
    avg_comments: float | None = None
    display_name: str | None = None
    bio: str | None = None
    is_verified: bool = False


@dataclass(frozen=True)
class VideoStats:
    """Per-video statistics from creator video listing."""

    video_id: str
    play_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    posted_at: datetime | None = None
    title: str | None = None
    duration_seconds: int | None = None
