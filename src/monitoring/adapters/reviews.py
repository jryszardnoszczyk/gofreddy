"""Review platform adapters — Trustpilot, App Store, Play Store."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from apify_client import ApifyClientAsync

from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention
from ._common import build_apify_client, parse_apify_items, parse_date, rating_to_sentiment

logger = logging.getLogger(__name__)

_APP_STORE_URL_RE = re.compile(r"^https://apps\.apple\.com/")
_PLAY_STORE_URL_RE = re.compile(r"^https://play\.google\.com/store/apps/")
_TRUSTPILOT_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


class TrustpilotAdapter(BaseMentionFetcher):
    """Apify trustpilot-reviews-scraper → mentions with source=TRUSTPILOT."""

    ACTOR_ID = "apify/trustpilot-reviews-scraper"
    TIMEOUT_SECONDS = 200  # Review scrapes can take 2-3 min

    def __init__(
        self,
        apify_token: str,
        *,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings=settings, timeout_override=self.TIMEOUT_SECONDS)
        self._token = apify_token
        self._client: ApifyClientAsync | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.TRUSTPILOT

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if not self._token:
            raise MentionFetchError("APIFY_TOKEN not configured")

        if self._client is None:
            self._client = build_apify_client(self._token)

        if not _TRUSTPILOT_DOMAIN_RE.match(query):
            raise MentionFetchError(f"Invalid Trustpilot domain: {query!r}")

        run_input: dict[str, Any] = {
            "startUrls": [{"url": f"https://www.trustpilot.com/review/{query}"}],
            "maxReviews": limit,
        }

        try:
            run = await self._client.actor(self.ACTOR_ID).call(
                run_input=run_input,
                timeout_secs=180,
            )
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                raise MentionFetchError(f"Trustpilot actor not found: {e}") from e
            raise

        items = await parse_apify_items(run, self._client)
        mentions: list[RawMention] = []

        for item in items:
            try:
                mentions.append(self._parse_item(item))
            except Exception:
                logger.warning(
                    "trustpilot_item_parse_error",
                    extra={"item_id": item.get("id", "unknown")},
                    exc_info=True,
                )

        return (mentions, None)  # No cursor for v1

    def _parse_item(self, item: dict[str, Any]) -> RawMention:
        """Parse a single Trustpilot review into a RawMention."""
        score, label = rating_to_sentiment(item.get("rating"))

        consumer = item.get("consumer", {}) or {}
        reply = item.get("reply", {}) or {}
        dates = item.get("dates", {}) or {}

        return RawMention(
            source=DataSource.TRUSTPILOT,
            source_id=str(item.get("id", "")),
            content=item.get("text", ""),
            author_handle=consumer.get("displayName"),
            url=item.get("url"),
            published_at=parse_date(dates.get("publishedDate")),
            sentiment_score=score,
            sentiment_label=label,
            engagement_likes=item.get("likes", 0) or 0,
            geo_country=consumer.get("countryCode"),
            metadata={
                "title": item.get("title"),
                "rating": item.get("rating"),
                "verified": item.get("isVerified", False),
                "business_reply": reply.get("message"),
                "business_reply_date": reply.get("publishedDate"),
                "reviewer_review_count": consumer.get("numberOfReviews"),
                "engagement_extra": {"helpful": item.get("likes", 0) or 0},
            },
        )

    async def close(self) -> None:
        self._client = None


class AppStoreAdapter(BaseMentionFetcher):
    """Apify app store scraper → mentions with source=APP_STORE."""

    ACTOR_ID = "epctex/appstore-scraper"
    TIMEOUT_SECONDS = 200

    def __init__(
        self,
        apify_token: str,
        *,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings=settings, timeout_override=self.TIMEOUT_SECONDS)
        self._token = apify_token
        self._client: ApifyClientAsync | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.APP_STORE

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if not self._token:
            raise MentionFetchError("APIFY_TOKEN not configured")

        if self._client is None:
            self._client = build_apify_client(self._token)

        if not _APP_STORE_URL_RE.match(query):
            raise MentionFetchError(f"Invalid App Store URL: {query!r}")

        run_input: dict[str, Any] = {
            "startUrls": [{"url": query}],
            "maxReviews": limit,
        }

        try:
            run = await self._client.actor(self.ACTOR_ID).call(
                run_input=run_input,
                timeout_secs=180,
            )
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                raise MentionFetchError(f"App Store actor not found: {e}") from e
            raise

        items = await parse_apify_items(run, self._client)
        mentions: list[RawMention] = []

        for item in items:
            try:
                mentions.append(self._parse_item(item))
            except Exception:
                logger.warning(
                    "appstore_item_parse_error",
                    extra={"item_id": item.get("id", "unknown")},
                    exc_info=True,
                )

        return (mentions, None)

    def _parse_item(self, item: dict[str, Any]) -> RawMention:
        """Parse a single App Store review into a RawMention."""
        rating = item.get("score") or item.get("rating")
        score, label = rating_to_sentiment(rating)

        # source_id: use id if available, else hash-based fallback
        source_id = item.get("id")
        if not source_id:
            content = item.get('text', '') or item.get('review', '')
            source_id = f"appstore:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
        source_id = str(source_id)

        content = item.get("review", "") or item.get("text", "")

        return RawMention(
            source=DataSource.APP_STORE,
            source_id=source_id,
            content=content,
            author_handle=item.get("userName"),
            published_at=parse_date(item.get("date")),
            sentiment_score=score,
            sentiment_label=label,
            metadata={
                "title": item.get("title"),
                "rating": rating,
                "app_version": item.get("version"),
                "engagement_extra": {"helpful": item.get("voteCount", 0) or 0},
            },
        )

    async def close(self) -> None:
        self._client = None


class PlayStoreAdapter(BaseMentionFetcher):
    """Apify Play Store reviews scraper → mentions with source=PLAY_STORE."""

    ACTOR_ID = "neatrat/google-play-store-reviews-scraper"
    TIMEOUT_SECONDS = 200

    def __init__(
        self,
        apify_token: str,
        *,
        settings: MonitoringSettings | None = None,
    ) -> None:
        super().__init__(settings=settings, timeout_override=self.TIMEOUT_SECONDS)
        self._token = apify_token
        self._client: ApifyClientAsync | None = None

    @property
    def source(self) -> DataSource:
        return DataSource.PLAY_STORE

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if not self._token:
            raise MentionFetchError("APIFY_TOKEN not configured")

        if self._client is None:
            self._client = build_apify_client(self._token)

        if not _PLAY_STORE_URL_RE.match(query):
            raise MentionFetchError(f"Invalid Play Store URL: {query!r}")

        run_input: dict[str, Any] = {
            "startUrls": [{"url": query}],
            "maxReviews": limit,
        }

        try:
            run = await self._client.actor(self.ACTOR_ID).call(
                run_input=run_input,
                timeout_secs=180,
            )
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                raise MentionFetchError(f"Play Store actor not found: {e}") from e
            raise

        items = await parse_apify_items(run, self._client)
        mentions: list[RawMention] = []

        for item in items:
            try:
                mentions.append(self._parse_item(item))
            except Exception:
                logger.warning(
                    "playstore_item_parse_error",
                    extra={"item_id": item.get("reviewId", "unknown")},
                    exc_info=True,
                )

        return (mentions, None)

    def _parse_item(self, item: dict[str, Any]) -> RawMention:
        """Parse a single Play Store review into a RawMention."""
        rating = item.get("score") or item.get("stars")
        score, label = rating_to_sentiment(rating)

        source_id = str(item.get("reviewId") or item.get("id", ""))

        return RawMention(
            source=DataSource.PLAY_STORE,
            source_id=source_id,
            content=item.get("text", ""),
            author_handle=item.get("userName"),
            published_at=parse_date(item.get("date")),
            sentiment_score=score,
            sentiment_label=label,
            metadata={
                "rating": rating,
                "app_version": item.get("appVersion"),
                "device_type": item.get("deviceType"),
                "business_reply": item.get("replyText"),
                "business_reply_date": item.get("replyDate"),
                "engagement_extra": {"helpful": item.get("thumbsUpCount", 0) or 0},
            },
        )

    async def close(self) -> None:
        self._client = None
