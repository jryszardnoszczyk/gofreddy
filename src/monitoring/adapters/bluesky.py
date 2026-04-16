"""Bluesky mention fetcher via AT Protocol public search API."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention

logger = logging.getLogger(__name__)


class BlueskyMentionFetcher(BaseMentionFetcher):
    """Fetch mentions from Bluesky via AT Protocol public search API.

    Uses unauthenticated XRPC endpoint — no API key required.
    Rate limit: 3000 req/5min per IP (generous for polling).
    """

    SEARCH_PATH = "/xrpc/app.bsky.feed.searchPosts"

    def __init__(
        self,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings)
        s = self._settings
        self._client = httpx.AsyncClient(
            base_url=s.bluesky_base_url,
            timeout=httpx.Timeout(connect=5.0, read=25.0, write=5.0, pool=10.0),
        )

    @property
    def source(self) -> DataSource:
        return DataSource.BLUESKY

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        params: dict[str, str | int] = {
            "q": query,
            "limit": max(1, min(limit, 100)),
            "sort": "latest",
        }
        if cursor:
            params["cursor"] = cursor

        resp = await self._client.get(self.SEARCH_PATH, params=params)

        if resp.status_code == 400:
            raise MentionFetchError(
                f"Bluesky invalid request: {resp.text[:200]}"
            )
        if resp.status_code == 401:
            raise MentionFetchError("Bluesky auth required (unexpected)")
        if resp.status_code == 429:
            reset = resp.headers.get("ratelimit-reset", "unknown")
            logger.warning(
                "bluesky_rate_limited",
                extra={"ratelimit_reset": reset},
            )
            raise RuntimeError("Bluesky rate limited")  # Let base class retry
        if resp.status_code >= 500:
            raise RuntimeError(f"Bluesky server error: {resp.status_code}")

        resp.raise_for_status()
        data = resp.json()

        mentions: list[RawMention] = []
        for post in data.get("posts", []):
            mention = self._map_post(post)
            if mention is not None:
                mentions.append(mention)

        next_cursor = data.get("cursor")
        return mentions, next_cursor

    def _map_post(self, post: dict) -> RawMention | None:
        """Map an AT Protocol PostView to RawMention."""
        uri = post.get("uri", "")
        author = post.get("author", {})
        record = post.get("record", {})

        source_id = uri
        if not source_id:
            return None

        did = author.get("did", "")
        url = self._post_url(did, uri)

        # Language: first entry in langs list, default "en"
        langs = record.get("langs", [])
        language = langs[0] if langs else "en"

        # Media URLs from embeds
        media_urls = self._extract_media_urls(post.get("embed"))

        # Extract hashtags and mentioned users from facets
        metadata: dict = {}
        metadata["author_id"] = did
        if author.get("avatar"):
            metadata["avatar_url"] = author["avatar"]
        if post.get("quoteCount"):
            metadata["quote_count"] = post["quoteCount"]

        embed = post.get("embed", {})
        if embed and embed.get("$type") == "app.bsky.embed.external#view":
            external = embed.get("external", {})
            if external.get("uri"):
                metadata["link_preview"] = external["uri"]

        facets = record.get("facets", [])
        if facets:
            hashtags = []
            mentioned_users = []
            for facet in facets:
                for feature in facet.get("features", []):
                    ftype = feature.get("$type", "")
                    if ftype == "app.bsky.richtext.facet#tag":
                        hashtags.append(feature.get("tag", ""))
                    elif ftype == "app.bsky.richtext.facet#mention":
                        mentioned_users.append(feature.get("did", ""))
            if hashtags:
                metadata["hashtags"] = hashtags
            if mentioned_users:
                metadata["mentioned_users"] = mentioned_users

        labels = post.get("labels", [])
        if labels:
            metadata["content_labels"] = [
                lbl.get("val", "") for lbl in labels if isinstance(lbl, dict)
            ]

        # Parse published_at
        published_at = None
        created_at_str = record.get("createdAt")
        if created_at_str:
            try:
                published_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        return RawMention(
            source=DataSource.BLUESKY,
            source_id=source_id,
            author_handle=author.get("handle"),
            author_name=author.get("displayName"),
            content=record.get("text", ""),
            url=url,
            published_at=published_at,
            engagement_likes=post.get("likeCount", 0),
            engagement_shares=post.get("repostCount", 0),
            engagement_comments=post.get("replyCount", 0),
            language=language,
            media_urls=media_urls,
            metadata=metadata,
        )

    def _post_url(self, did: str, uri: str) -> str | None:
        """Construct bsky.app permalink from DID and AT URI."""
        if not uri.startswith("at://"):
            logger.warning("bluesky_malformed_uri", extra={"uri": uri})
            return None
        rkey = uri.rsplit("/", 1)[-1]
        return f"https://bsky.app/profile/{did}/post/{rkey}"

    def _extract_media_urls(self, embed: dict | None) -> list[str]:
        """Extract media URLs from embed object."""
        if not embed:
            return []
        urls: list[str] = []
        embed_type = embed.get("$type", "")
        if embed_type == "app.bsky.embed.images#view":
            for img in embed.get("images", []):
                fullsize = img.get("fullsize")
                if fullsize:
                    urls.append(fullsize)
        elif embed_type == "app.bsky.embed.video#view":
            playlist = embed.get("playlist")
            if playlist:
                urls.append(playlist)
        return urls

    async def close(self) -> None:
        """Close the httpx client."""
        await self._client.aclose()
