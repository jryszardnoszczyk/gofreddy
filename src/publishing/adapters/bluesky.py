"""Bluesky publishing via AT Protocol (XRPC).

Auth: App password stored in credential_enc (not OAuth).
No app review required. Generous rate limits: 5000 points/hour.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from ..config import PublishingSettings
from ..exceptions import AdapterError, CredentialError
from ..models import PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)

# Facet patterns for rich text
_URL_PATTERN = re.compile(r"https?://[^\s\])<>]+")
_HASHTAG_PATTERN = re.compile(r"#(\w+)")


class BlueskyPublisher(BasePublisher):
    """Bluesky AT Protocol publisher.

    Uses app passwords — the officially recommended auth method for
    third-party apps. AT Protocol OAuth (DPoP-based) is still a draft spec.
    """

    PLATFORM = PublishPlatform.BLUESKY
    MAX_TEXT_GRAPHEMES = 300
    MAX_IMAGES = 4
    MAX_IMAGE_SIZE_BYTES = 1_000_000
    PDS_BASE = "https://bsky.social"

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.adapter_timeout_seconds),
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.BLUESKY

    async def _create_session(
        self, handle: str, app_password: str
    ) -> dict[str, str]:
        """Authenticate and return session tokens."""
        try:
            resp = await self._http.post(
                f"{self.PDS_BASE}/xrpc/com.atproto.server.createSession",
                json={"identifier": handle, "password": app_password},
            )
        except httpx.HTTPError as exc:
            raise AdapterError("Bluesky session creation failed") from exc

        if resp.status_code == 401:
            raise CredentialError("Invalid Bluesky handle or app password")
        if resp.status_code >= 400:
            raise AdapterError(f"Bluesky auth error {resp.status_code}")

        data = resp.json()
        return {
            "accessJwt": data["accessJwt"],
            "refreshJwt": data["refreshJwt"],
            "did": data["did"],
            "handle": data.get("handle", handle),
        }

    def _build_facets(self, text: str) -> list[dict]:
        """Build rich text facets with correct UTF-8 byte indices."""
        facets = []

        for match in _URL_PATTERN.finditer(text):
            start = len(text[: match.start()].encode("utf-8"))
            end = len(text[: match.end()].encode("utf-8"))
            facets.append(
                {
                    "index": {"byteStart": start, "byteEnd": end},
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#link",
                            "uri": match.group(),
                        }
                    ],
                }
            )

        for match in _HASHTAG_PATTERN.finditer(text):
            start = len(text[: match.start()].encode("utf-8"))
            end = len(text[: match.end()].encode("utf-8"))
            facets.append(
                {
                    "index": {"byteStart": start, "byteEnd": end},
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#tag",
                            "tag": match.group(1),
                        }
                    ],
                }
            )

        return facets

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        handle = credentials.get("handle", "")
        app_password = credentials.get("app_password", "")
        if not handle or not app_password:
            raise CredentialError("Missing Bluesky handle or app_password")

        session = await self._create_session(handle, app_password)
        access_jwt = session["accessJwt"]
        did = session["did"]

        # Build post text from content_parts
        text = ""
        if item.content_parts:
            text = (item.content_parts[0].get("body", "") or "")[
                : self.MAX_TEXT_GRAPHEMES
            ]

        record: dict = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        facets = self._build_facets(text)
        if facets:
            record["facets"] = facets

        # External link embed
        link_url = item.content_parts[0].get("url") if item.content_parts else None
        if link_url:
            record["embed"] = {
                "$type": "app.bsky.embed.external",
                "external": {
                    "uri": link_url,
                    "title": item.og_title or "",
                    "description": item.og_description or "",
                },
            }

        try:
            resp = await self._http.post(
                f"{self.PDS_BASE}/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {access_jwt}"},
                json={
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": record,
                },
            )
        except httpx.HTTPError as exc:
            raise AdapterError("Bluesky post creation failed") from exc

        if resp.status_code >= 400:
            raise AdapterError(f"Bluesky API error {resp.status_code}")

        data = resp.json()
        post_uri = data.get("uri", "")
        post_cid = data.get("cid", "")

        # Construct web URL from URI
        # URI format: at://did:plc:xxx/app.bsky.feed.post/rkey
        rkey = post_uri.split("/")[-1] if post_uri else ""
        post_url = (
            f"https://bsky.app/profile/{session['handle']}/post/{rkey}"
            if rkey
            else None
        )

        # First comment as reply
        if item.first_comment and post_uri and post_cid:
            await self._post_first_comment(
                post_uri, post_cid, did, item.first_comment, access_jwt
            )

        return PublishResult(
            success=True,
            external_id=post_uri,
            external_url=post_url,
        )

    async def _post_first_comment(
        self,
        parent_uri: str,
        parent_cid: str,
        did: str,
        comment: str,
        access_jwt: str,
    ) -> str | None:
        """Post a reply to the just-published post. Non-fatal on failure."""
        try:
            reply_record = {
                "$type": "app.bsky.feed.post",
                "text": comment[: self.MAX_TEXT_GRAPHEMES],
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "reply": {
                    "root": {"uri": parent_uri, "cid": parent_cid},
                    "parent": {"uri": parent_uri, "cid": parent_cid},
                },
            }
            resp = await self._http.post(
                f"{self.PDS_BASE}/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {access_jwt}"},
                json={
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": reply_record,
                },
            )
            if resp.status_code < 300:
                logger.info(
                    "first_comment_posted",
                    extra={"parent_uri": parent_uri},
                )
                return resp.json().get("uri")
        except Exception:
            logger.warning(
                "first_comment_failed",
                extra={"parent_uri": parent_uri},
                exc_info=True,
            )
        return None

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        handle = credentials.get("handle", "")
        app_password = credentials.get("app_password", "")
        if not handle or not app_password:
            return False
        try:
            session = await self._create_session(handle, app_password)
            return bool(session.get("did"))
        except (CredentialError, AdapterError):
            return False

    async def close(self) -> None:
        await self._http.aclose()
