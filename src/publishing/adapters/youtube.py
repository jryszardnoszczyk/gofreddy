"""YouTube publishing via YouTube Data API v3.

Supports: video upload (resumable), thumbnail.set, scheduled publish.
Standard quota: 10,000 units/day. videos.insert = 1,600 units (~6 uploads/day).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ...common.url_validation import resolve_and_validate
from ..config import PublishingSettings
from ..exceptions import AdapterError, CredentialError, QuotaExhaustedError
from ..models import PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)


class YouTubePublisher(BasePublisher):
    """YouTube Data API v3 adapter with resumable upload.

    Daily quota: 10,000 units. videos.insert costs 1,600 units (~6/day).
    """

    PLATFORM = PublishPlatform.YOUTUBE
    PUBLISH_TIMEOUT = 600.0
    CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_TOTAL_CHARS = 500
    DAILY_QUOTA_UNITS = 10000
    UPLOAD_COST_UNITS = 1600
    MAX_DAILY_UPLOADS = 6
    API_BASE = "https://www.googleapis.com"

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),  # YouTube uploads need more time
            follow_redirects=False,
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.YOUTUBE

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        access_token = credentials.get("access_token", "")
        if not access_token:
            raise CredentialError("Missing YouTube access_token")

        # Build video metadata from content_parts
        title = ""
        description = ""
        tags: list[str] = []
        if item.content_parts:
            first = item.content_parts[0]
            title = (first.get("title") or first.get("body", ""))[
                : self.MAX_TITLE_LENGTH
            ]
            description = first.get("body", "")[: self.MAX_DESCRIPTION_LENGTH]

        if item.labels:
            tags = [l for l in item.labels if len(l) <= 30][:20]

        # Privacy and scheduling
        privacy = "public"
        publish_at = None
        if item.scheduled_at:
            privacy = "private"
            publish_at = item.scheduled_at.isoformat()

        category_id = (item.metadata or {}).get("youtube_category", "22")

        metadata: dict[str, Any] = {
            "snippet": {
                "title": title or "Untitled",
                "description": description,
                "tags": tags,
                "categoryId": str(category_id),
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        if publish_at:
            metadata["status"]["publishAt"] = publish_at

        # Get video URL from media
        video_url = next(
            (
                m.get("url")
                for m in (item.media or [])
                if m.get("type") == "video" and m.get("url")
            ),
            None,
        )
        if not video_url:
            raise AdapterError("YouTube requires a video URL in media")

        # Step 1: Init resumable upload
        try:
            init_resp = await self._http.post(
                f"{self.API_BASE}/upload/youtube/v3/videos",
                params={
                    "uploadType": "resumable",
                    "part": "snippet,status",
                    "notifySubscribers": "false",
                },
                headers={
                    **self._headers(access_token),
                    "X-Upload-Content-Type": "video/*",
                },
                json=metadata,
            )
        except httpx.HTTPError as exc:
            raise AdapterError("YouTube upload init failed") from exc

        if init_resp.status_code == 401:
            raise CredentialError("YouTube access token expired")
        if init_resp.status_code == 403:
            error_reason = (
                init_resp.json()
                .get("error", {})
                .get("errors", [{}])[0]
                .get("reason", "")
            )
            if error_reason == "quotaExceeded":
                raise QuotaExhaustedError(
                    "YouTube daily upload limit reached. "
                    "Try again tomorrow or upload manually at studio.youtube.com."
                )
            raise AdapterError(f"YouTube forbidden: {error_reason}")
        if init_resp.status_code >= 400:
            raise AdapterError(f"YouTube API error {init_resp.status_code}")

        upload_url = init_resp.headers.get("Location", "")
        if not upload_url:
            raise AdapterError("YouTube did not return resumable upload URL")

        # Step 2: Stream-download video and upload in chunks to YouTube
        MAX_VIDEO_BYTES = 5_368_709_120  # 5 GB
        await resolve_and_validate(video_url)
        try:
            async with self._http.stream("GET", video_url) as video_stream:
                cl_header = video_stream.headers.get("content-length")
                if not cl_header:
                    raise AdapterError(
                        "Video source did not return Content-Length header"
                    )
                total_size = int(cl_header)
                if total_size > MAX_VIDEO_BYTES:
                    raise AdapterError(
                        f"Video exceeds maximum size ({total_size} bytes > {MAX_VIDEO_BYTES})"
                    )

                buffer = bytearray()
                bytes_sent = 0

                async for raw_chunk in video_stream.aiter_bytes(self.CHUNK_SIZE):
                    buffer.extend(raw_chunk)

                    while len(buffer) >= self.CHUNK_SIZE:
                        chunk = bytes(buffer[: self.CHUNK_SIZE])
                        del buffer[: self.CHUNK_SIZE]
                        start = bytes_sent
                        end = bytes_sent + len(chunk) - 1
                        resp = await self._http.put(
                            upload_url,
                            content=chunk,
                            headers={
                                "Authorization": f"Bearer {access_token}",
                                "Content-Type": "video/*",
                                "Content-Range": f"bytes {start}-{end}/{total_size}",
                            },
                        )
                        if resp.status_code not in (200, 201, 308):
                            raise AdapterError(
                                f"YouTube chunk upload error {resp.status_code}"
                            )
                        bytes_sent += len(chunk)

                # Final chunk (remaining buffer)
                if buffer:
                    chunk = bytes(buffer)
                    start = bytes_sent
                    end = bytes_sent + len(chunk) - 1
                    upload_resp = await self._http.put(
                        upload_url,
                        content=chunk,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "video/*",
                            "Content-Range": f"bytes {start}-{end}/{total_size}",
                        },
                    )
                    if upload_resp.status_code not in (200, 201):
                        raise AdapterError(
                            f"YouTube final chunk upload error {upload_resp.status_code}"
                        )
                else:
                    # Edge case: exact multiple of CHUNK_SIZE, last PUT already
                    # returned 200/201 — we need that response for video data.
                    upload_resp = resp  # type: ignore[possibly-undefined]

        except AdapterError:
            raise
        except httpx.HTTPError as exc:
            raise AdapterError("YouTube chunked upload failed") from exc

        video_data = upload_resp.json()
        video_id = video_data.get("id", "")
        video_url_result = f"https://youtu.be/{video_id}" if video_id else None

        # Custom thumbnail
        if item.thumbnail_url and video_id:
            await self._set_thumbnail(video_id, item.thumbnail_url, access_token)

        # First comment
        if item.first_comment and video_id:
            await self._post_first_comment(
                video_id, item.first_comment, access_token
            )

        return PublishResult(
            success=True,
            external_id=video_id,
            external_url=video_url_result,
        )

    async def _set_thumbnail(
        self, video_id: str, thumbnail_url: str, access_token: str
    ) -> bool:
        """Upload custom thumbnail. Non-fatal on failure."""
        try:
            await resolve_and_validate(thumbnail_url)
            async with self._http.stream("GET", thumbnail_url) as stream:
                thumb_bytes = await stream.aread()

            resp = await self._http.post(
                f"{self.API_BASE}/upload/youtube/v3/thumbnails/set",
                params={"videoId": video_id},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "image/jpeg",
                },
                content=thumb_bytes,
            )
            return resp.status_code == 200
        except Exception:
            logger.warning(
                "thumbnail_set_failed",
                extra={"video_id": video_id},
                exc_info=True,
            )
            return False

    async def _post_first_comment(
        self, video_id: str, comment: str, access_token: str
    ) -> str | None:
        """Post first comment on video. Non-fatal on failure."""
        try:
            resp = await self._http.post(
                f"{self.API_BASE}/youtube/v3/commentThreads",
                params={"part": "snippet"},
                headers=self._headers(access_token),
                json={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {"textOriginal": comment}
                        },
                    }
                },
            )
            if resp.status_code < 300:
                logger.info(
                    "first_comment_posted", extra={"video_id": video_id}
                )
                return resp.json().get("id")
        except Exception:
            logger.warning(
                "first_comment_failed",
                extra={"video_id": video_id},
                exc_info=True,
            )
        return None

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        access_token = credentials.get("access_token", "")
        if not access_token:
            return False
        try:
            resp = await self._http.get(
                f"{self.API_BASE}/youtube/v3/channels",
                params={"part": "id", "mine": "true"},
                headers=self._headers(access_token),
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self._http.aclose()
