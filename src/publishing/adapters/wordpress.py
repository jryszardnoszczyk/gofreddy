"""WordPress REST API adapter — Application Passwords auth."""

from __future__ import annotations

import base64
import logging

import httpx

from ...common.url_validation import resolve_and_validate
from ..config import PublishingSettings
from ..exceptions import AdapterError, CredentialError
from ..models import PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)


class WordPressPublisher(BasePublisher):
    """Publish to WordPress via REST API with Application Passwords.

    Credentials dict keys: site_url, username, app_password.
    Note: Application Passwords contain spaces (xxxx xxxx xxxx xxxx) — do NOT strip.
    HTTPS is required by WordPress for Application Passwords auth.
    """

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                (self._settings or PublishingSettings()).wordpress_timeout_seconds
            ),
            follow_redirects=False,
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.WORDPRESS

    def _auth_header(self, username: str, app_password: str) -> str:
        creds = base64.b64encode(
            f"{username}:{app_password}".encode()
        ).decode()
        return f"Basic {creds}"

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        site_url = credentials.get("site_url", "").rstrip("/")
        username = credentials.get("username", "")
        app_password = credentials.get("app_password", "")

        if not all([site_url, username, app_password]):
            raise CredentialError("Missing WordPress credentials")

        # SSRF pre-flight — block private IPs
        try:
            await resolve_and_validate(site_url)
        except ValueError as e:
            raise AdapterError(f"WordPress site_url validation failed: {e}") from e

        body_text = ""
        if item.content_parts:
            body_text = item.content_parts[0].get("body", "")

        title = item.og_title or body_text[:100]

        payload: dict = {
            "title": title,
            "content": body_text,
            "status": "publish",
        }

        if item.slug:
            payload["slug"] = item.slug

        # Yoast SEO meta (silently ignored if Yoast not installed or keys not
        # registered with show_in_rest on the WP side)
        meta: dict = {}
        if item.og_title:
            meta["_yoast_wpseo_opengraph-title"] = item.og_title
        if item.og_description:
            meta["_yoast_wpseo_opengraph-description"] = item.og_description
        if item.og_image_url:
            meta["_yoast_wpseo_opengraph-image"] = item.og_image_url
        if item.canonical_url:
            meta["_yoast_wpseo_canonical"] = item.canonical_url
        if meta:
            payload["meta"] = meta

        url = f"{site_url}/wp-json/wp/v2/posts"
        headers = {"Authorization": self._auth_header(username, app_password)}

        resp = await self._client.post(url, json=payload, headers=headers)

        if resp.status_code == 401:
            raise CredentialError("WordPress authentication failed")
        if resp.status_code == 403:
            raise CredentialError("Insufficient WordPress Application Password scope")
        if resp.status_code == 404:
            raise AdapterError("WordPress REST API not found — check site_url")
        if resp.status_code >= 500:
            raise Exception(f"WordPress server error: {resp.status_code}")
        if resp.status_code >= 400:
            raise AdapterError(
                f"WordPress API error: {resp.status_code}"
            )

        data = resp.json()
        post_id = str(data.get("id", ""))
        permalink = data.get("link", "")

        return PublishResult(
            success=True,
            external_id=post_id,
            external_url=permalink,
        )

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        site_url = credentials.get("site_url", "").rstrip("/")
        username = credentials.get("username", "")
        app_password = credentials.get("app_password", "")

        if not all([site_url, username, app_password]):
            return False

        try:
            await resolve_and_validate(site_url)
        except ValueError:
            return False

        url = f"{site_url}/wp-json/wp/v2/users/me"
        headers = {"Authorization": self._auth_header(username, app_password)}

        try:
            resp = await self._client.get(url, headers=headers)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
