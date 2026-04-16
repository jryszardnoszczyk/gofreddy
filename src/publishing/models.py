"""Publishing domain models — all frozen dataclasses."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


class PublishPlatform(str, enum.Enum):
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WORDPRESS = "wordpress"
    GHOST = "ghost"
    BLUESKY = "bluesky"
    X = "x"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WEBHOOK = "webhook"
    WEBFLOW = "webflow"
    SHOPIFY = "shopify"


class AuthType(str, enum.Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    APP_PASSWORD = "app_password"


class PublishStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class PlatformConnection:
    id: UUID
    org_id: UUID
    platform: PublishPlatform
    auth_type: AuthType
    account_id: str
    account_name: str
    is_active: bool
    scopes: list[str]
    key_version: int
    token_expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Decrypted tokens NOT stored on the model — fetched on-demand via repository


@dataclass(frozen=True, slots=True)
class QueueItem:
    id: UUID
    org_id: UUID
    client_id: UUID | None
    platform: str
    connection_id: UUID
    content_parts: list[dict[str, Any]]
    media: list[dict[str, Any]]
    first_comment: str | None
    thumbnail_url: str | None
    og_title: str | None
    og_description: str | None
    og_image_url: str | None
    twitter_card_type: str | None
    canonical_url: str | None
    slug: str | None
    labels: list[str]
    group_id: UUID | None
    newsletter_subject: str | None
    newsletter_segment: str | None
    status: PublishStatus
    approved_at: datetime | None
    approved_by: UUID | None
    scheduled_at: datetime | None
    external_id: str | None
    external_url: str | None
    error_message: str | None
    retry_count: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PublishResult:
    """Returned by adapter after attempting to publish."""

    success: bool
    external_id: str | None = None
    external_url: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    scopes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DeviceFlowInit:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int


@dataclass(frozen=True, slots=True)
class DeviceFlowResult:
    status: str  # "pending", "complete", "expired"
    connection_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    upload_url: str
    public_url: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class CarouselSlide:
    body: str
    title: str | None = None
    image_url: str | None = None
    bg_color: str | None = None  # hex color override


@dataclass(frozen=True, slots=True)
class RepostSchedule:
    interval_days: int  # repost every N days
    max_reposts: int = 3  # stop after N reposts
    reposts_done: int = 0


@dataclass(frozen=True, slots=True)
class FeedEntry:
    title: str
    url: str
    summary: str
    published_at: datetime | None
    author: str | None = None
    content_html: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FeedConfig:
    feed_url: str
    target_platforms: list[str]
    org_id: UUID
    connection_ids: dict[str, UUID] = field(default_factory=dict)
    check_interval_minutes: int = 60
    last_checked_at: datetime | None = None
