"""LinkedIn Publishing via REST API (versioned API, restli 2.0).

Supports: text posts, article shares (URL + commentary), image posts,
PDF carousel documents. No app review required for personal posts.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ._carousel import render_carousel_pdf
from ..config import PublishingSettings
from ..exceptions import AdapterError, CredentialError
from ..models import CarouselSlide, PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)


class LinkedInPublisher(BasePublisher):
    """LinkedIn Marketing API adapter.

    Uses versioned REST API with restli 2.0.0 protocol.

    Credentials dict keys: access_token, member_id.
    """

    PLATFORM = PublishPlatform.LINKEDIN
    MAX_TEXT_LENGTH = 3000
    MAX_IMAGES = 9
    API_BASE = "https://api.linkedin.com"
    API_VERSION = "202602"

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.adapter_timeout_seconds),
            follow_redirects=False,
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.LINKEDIN

    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": self.API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        access_token = credentials.get("access_token", "")
        member_id = credentials.get("member_id", "")
        if not access_token or not member_id:
            raise CredentialError("Missing access_token or member_id")

        author = f"urn:li:person:{member_id}"
        headers = self._headers(access_token)

        # Carousel detection — branch early before text/article logic
        carousel_slides = self._extract_carousel_slides(item)
        if carousel_slides:
            body_text = ""
            if item.content_parts:
                body_text = item.content_parts[0].get("body", "")[
                    : self.MAX_TEXT_LENGTH
                ]
            return await self._publish_carousel(
                headers, author, body_text, carousel_slides
            )

        # Build post body from content_parts
        body_text = ""
        article_url = None
        if item.content_parts:
            first = item.content_parts[0]
            body_text = first.get("body", "")[:self.MAX_TEXT_LENGTH]
            article_url = first.get("url")

        post_body: dict[str, Any] = {
            "author": author,
            "commentary": body_text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        # Article share — attach URL with OG metadata
        if article_url:
            post_body["content"] = {
                "article": {
                    "source": article_url,
                    "title": item.og_title or "",
                    "description": item.og_description or "",
                }
            }

        try:
            resp = await self._http.post(
                f"{self.API_BASE}/rest/posts",
                headers=headers,
                json=post_body,
            )
        except httpx.HTTPError as exc:
            raise AdapterError("LinkedIn API request failed") from exc

        if resp.status_code == 401:
            raise CredentialError("LinkedIn access token expired or invalid")
        if resp.status_code == 403:
            raise CredentialError("LinkedIn insufficient permissions")
        if resp.status_code >= 400:
            raise AdapterError(
                f"LinkedIn API error {resp.status_code}"
            )

        # LinkedIn returns post URN in x-restli-id header
        post_urn = resp.headers.get("x-restli-id", "")
        post_url = (
            f"https://www.linkedin.com/feed/update/{post_urn}"
            if post_urn
            else None
        )

        # First comment (non-fatal)
        if item.first_comment and post_urn:
            await self._post_first_comment(
                post_urn, author, item.first_comment, access_token
            )

        return PublishResult(
            success=True,
            external_id=post_urn,
            external_url=post_url,
        )

    def _extract_carousel_slides(self, item: QueueItem) -> list[CarouselSlide]:
        """Return CarouselSlide list if item is a carousel post, else empty list."""
        if not (item.metadata or {}).get("post_type") == "carousel":
            return []
        slides: list[CarouselSlide] = []
        for part in item.content_parts or []:
            slides.append(
                CarouselSlide(
                    body=part.get("body", ""),
                    title=part.get("title"),
                    image_url=part.get("image_url"),
                    bg_color=part.get("bg_color"),
                )
            )
        return slides

    async def _publish_carousel(
        self,
        headers: dict[str, str],
        author: str,
        body_text: str,
        slides: list[CarouselSlide],
    ) -> PublishResult:
        """Publish a PDF carousel document to LinkedIn."""
        pdf_bytes = await render_carousel_pdf(slides)

        # Initialize document upload
        try:
            init_resp = await self._http.post(
                f"{self.API_BASE}/rest/documents?action=initializeUpload",
                headers=headers,
                json={
                    "initializeUploadRequest": {
                        "owner": author,
                    }
                },
            )
        except httpx.HTTPError as exc:
            raise AdapterError("LinkedIn document upload init failed") from exc

        if init_resp.status_code >= 400:
            raise AdapterError(
                f"LinkedIn document init error {init_resp.status_code}"
            )

        init_data = init_resp.json().get("value", {})
        doc_upload_url = init_data.get("uploadUrl", "")
        document_urn = init_data.get("document", "")
        if not doc_upload_url or not document_urn:
            raise AdapterError("LinkedIn did not return document upload URL/URN")

        # Upload PDF bytes
        try:
            put_resp = await self._http.put(
                doc_upload_url,
                content=pdf_bytes,
                headers={
                    **headers,
                    "Content-Type": "application/pdf",
                },
            )
        except httpx.HTTPError as exc:
            raise AdapterError("LinkedIn PDF upload failed") from exc

        if put_resp.status_code >= 400:
            raise AdapterError(
                f"LinkedIn PDF upload error {put_resp.status_code}"
            )

        # Create post with document
        post_body: dict[str, Any] = {
            "author": author,
            "commentary": body_text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "content": {
                "media": {
                    "id": document_urn,
                    "title": "Carousel",
                }
            },
        }

        try:
            resp = await self._http.post(
                f"{self.API_BASE}/rest/posts",
                headers=headers,
                json=post_body,
            )
        except httpx.HTTPError as exc:
            raise AdapterError("LinkedIn carousel post failed") from exc

        if resp.status_code == 401:
            raise CredentialError("LinkedIn access token expired or invalid")
        if resp.status_code >= 400:
            raise AdapterError(f"LinkedIn carousel error {resp.status_code}")

        post_urn = resp.headers.get("x-restli-id", "")
        post_url = (
            f"https://www.linkedin.com/feed/update/{post_urn}"
            if post_urn
            else None
        )

        return PublishResult(
            success=True,
            external_id=post_urn,
            external_url=post_url,
        )

    async def _post_first_comment(
        self,
        post_urn: str,
        author: str,
        comment: str,
        access_token: str,
    ) -> str | None:
        """Post a first comment on a LinkedIn post. Non-fatal on failure."""
        try:
            resp = await self._http.post(
                f"{self.API_BASE}/rest/socialActions/{post_urn}/comments",
                headers=self._headers(access_token),
                json={
                    "actor": author,
                    "message": {"text": comment[:self.MAX_TEXT_LENGTH]},
                },
            )
            if resp.status_code < 300:
                logger.info(
                    "first_comment_posted",
                    extra={"post_urn": post_urn},
                )
                return resp.headers.get("x-restli-id")
        except Exception:
            logger.warning(
                "first_comment_failed",
                extra={"post_urn": post_urn},
                exc_info=True,
            )
        return None

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        """Validate token against LinkedIn userinfo endpoint."""
        access_token = credentials.get("access_token", "")
        if not access_token:
            return False
        try:
            resp = await self._http.get(
                f"{self.API_BASE}/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self._http.aclose()
