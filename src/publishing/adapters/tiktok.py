"""TikTok publishing via Content Posting API v2.

Supports: video upload, photo carousel (4-35 images).
Requires app review for video.publish scope.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from ...common.url_validation import resolve_and_validate
from ..config import PublishingSettings
from ..exceptions import AdapterError, ContentValidationError, CredentialError
from ..models import PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)


class TikTokPublisher(BasePublisher):
    """TikTok Content Posting API v2 adapter.

    Video upload uses PULL_FROM_URL mode (preferred for R2-hosted media).
    Photo carousel uses photo_images mode (4-35 images).
    """

    PLATFORM = PublishPlatform.TIKTOK
    PUBLISH_TIMEOUT = 150.0
    POLL_INTERVAL = 5.0
    POLL_MAX_ATTEMPTS = 5
    MAX_CAPTION_LENGTH = 2200
    MAX_HASHTAGS = 5
    MAX_VIDEO_SIZE_MB = 4096
    VIDEO_DURATION_RANGE = (1, 600)
    CAROUSEL_IMAGE_RANGE = (4, 35)
    API_BASE = "https://open.tiktokapis.com/v2"

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.adapter_timeout_seconds),
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.TIKTOK

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _validate_content(self, item: QueueItem) -> None:
        """Validate content against TikTok's requirements."""
        errors = []
        if item.content_parts:
            caption = item.content_parts[0].get("body", "")
            if len(caption) > self.MAX_CAPTION_LENGTH:
                errors.append(
                    f"Caption exceeds {self.MAX_CAPTION_LENGTH} characters"
                )
            hashtag_count = caption.count("#")
            if hashtag_count > self.MAX_HASHTAGS:
                errors.append(
                    f"Too many hashtags ({hashtag_count} > {self.MAX_HASHTAGS})"
                )
        if errors:
            raise ContentValidationError(errors)

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        access_token = credentials.get("access_token", "")
        if not access_token:
            raise CredentialError("Missing TikTok access_token")

        self._validate_content(item)
        headers = self._headers(access_token)

        caption = ""
        if item.content_parts:
            caption = item.content_parts[0].get("body", "")[
                : self.MAX_CAPTION_LENGTH
            ]

        # Determine post type from media
        photo_urls: list[str] = [
            m["url"]
            for m in (item.media or [])
            if m.get("type") == "image" and m.get("url")
        ]
        video_url = next(
            (
                m.get("url")
                for m in (item.media or [])
                if m.get("type") == "video" and m.get("url")
            ),
            None,
        )

        if (
            photo_urls
            and self.CAROUSEL_IMAGE_RANGE[0]
            <= len(photo_urls)
            <= self.CAROUSEL_IMAGE_RANGE[1]
        ):
            return await self._publish_carousel(headers, caption, photo_urls)
        elif video_url:
            return await self._publish_video(
                headers, caption, video_url, item.thumbnail_url
            )
        else:
            raise AdapterError(
                "TikTok requires either a video URL or 4-35 photo URLs"
            )

    async def _publish_video(
        self,
        headers: dict[str, str],
        caption: str,
        video_url: str,
        thumbnail_url: str | None,
    ) -> PublishResult:
        """Publish video via PULL_FROM_URL mode."""
        await resolve_and_validate(video_url)
        if thumbnail_url:
            await resolve_and_validate(thumbnail_url)

        payload: dict = {
            "post_info": {
                "title": caption[:150],
                "description": caption,
                "disable_comment": False,
                "privacy_level": "SELF_ONLY",
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }
        if thumbnail_url:
            payload["source_info"]["thumbnail"] = thumbnail_url

        try:
            resp = await self._http.post(
                f"{self.API_BASE}/post/publish/video/init/",
                headers=headers,
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise AdapterError("TikTok video init failed") from exc

        if resp.status_code == 401:
            raise CredentialError("TikTok access token expired")
        if resp.status_code >= 400:
            raise AdapterError(f"TikTok API error {resp.status_code}")

        data = resp.json().get("data", {})
        publish_id = data.get("publish_id", "")

        return await self._poll_publish_status(headers, publish_id)

    async def _publish_carousel(
        self,
        headers: dict[str, str],
        caption: str,
        photo_urls: list[str],
    ) -> PublishResult:
        """Publish photo carousel (4-35 images)."""
        for url in photo_urls:
            await resolve_and_validate(url)

        payload = {
            "post_info": {
                "title": caption[:150],
                "description": caption,
                "disable_comment": False,
                "privacy_level": "SELF_ONLY",
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_images": photo_urls,
            },
        }

        try:
            resp = await self._http.post(
                f"{self.API_BASE}/post/publish/content/init/",
                headers=headers,
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise AdapterError("TikTok carousel init failed") from exc

        if resp.status_code == 401:
            raise CredentialError("TikTok access token expired")
        if resp.status_code >= 400:
            raise AdapterError(f"TikTok carousel error {resp.status_code}")

        data = resp.json().get("data", {})
        publish_id = data.get("publish_id", "")

        return await self._poll_publish_status(headers, publish_id)

    async def _poll_publish_status(
        self, headers: dict[str, str], publish_id: str
    ) -> PublishResult:
        """Poll TikTok for publish completion status."""
        for _ in range(self.POLL_MAX_ATTEMPTS):
            await asyncio.sleep(self.POLL_INTERVAL)
            try:
                resp = await self._http.post(
                    f"{self.API_BASE}/post/publish/status/fetch/",
                    headers=headers,
                    json={"publish_id": publish_id},
                )
            except httpx.HTTPError:
                logger.warning(
                    "tiktok_poll_error",
                    extra={"publish_id": publish_id},
                    exc_info=True,
                )
                continue

            if resp.status_code >= 400:
                continue

            data = resp.json().get("data", {})
            status = data.get("status", "")

            if status == "PUBLISH_COMPLETE":
                return PublishResult(
                    success=True,
                    external_id=publish_id,
                )
            if status == "FAILED":
                fail_reason = data.get("fail_reason", "unknown")
                raise AdapterError(
                    f"TikTok publish failed: {fail_reason}"
                )
            # PROCESSING_UPLOAD, SENDING_TO_USER_INBOX, etc. — keep polling

        # Exhausted attempts without terminal status
        return PublishResult(
            success=True,
            external_id=publish_id,
            error_message="TikTok publish status unknown after polling timeout",
        )

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        access_token = credentials.get("access_token", "")
        if not access_token:
            return False
        try:
            resp = await self._http.get(
                f"{self.API_BASE}/user/info/",
                headers=self._headers(access_token),
                params={"fields": "display_name"},
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self._http.aclose()
