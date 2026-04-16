"""Xpoz SDK adapter — Twitter, Instagram, Reddit via pre-indexed search."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Self

from xpoz import (
    AsyncXpozClient,
    AuthenticationError,
    NotFoundError,
    OperationTimeoutError,
    XpozError,
)

from ...common.circuit_breaker import CircuitBreaker
from ...common.cost_recorder import XPOZ_COST_PER_CALL, cost_recorder as _cost_recorder
from ..config import MonitoringSettings
from ..exceptions import MentionFetchError
from ..fetcher_protocol import BaseMentionFetcher
from ..models import DataSource, RawMention, XpozComment, XpozSubreddit, XpozUser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Xpoz SDK 0.2.0 bug workaround: async codepath returns created_at as int
# (Unix timestamp) but Pydantic models declare it as str | None.
# We patch the model_fields annotation to accept int | str | None.
# ---------------------------------------------------------------------------
try:
    from xpoz.types.twitter import TwitterPost as _TwPost, TwitterUser as _TwUser
    from xpoz.types.instagram import InstagramPost as _IgPost
    from xpoz.types.reddit import RedditPost as _RdPost

    # SDK source patched to accept int|str|None for timestamp fields.
    # Runtime model_rebuild ensures Pydantic core schema matches.
    for _Model in (_TwPost, _IgPost, _RdPost, _TwUser):
        _field = _Model.model_fields.get("created_at")
        if _field and _field.annotation is not None and int not in (getattr(_field.annotation, "__args__", ()) or ()):
            _field.annotation = int | str | None  # type: ignore[assignment]
            _Model.model_rebuild(force=True)
    logger.debug("xpoz_sdk_patch: created_at int|str|None verified")
except Exception:
    logger.warning("xpoz_sdk_patch: failed — async search may fail with int created_at", exc_info=True)

# ---------------------------------------------------------------------------
# Field list constants — posts (existing)
# ---------------------------------------------------------------------------
_SEARCH_FIELDS_TWITTER = [
    "id", "text", "author_username", "like_count", "retweet_count",
    "reply_count", "quote_count", "impression_count", "bookmark_count",
    "hashtags", "mentions", "media_urls", "country", "region", "city",
    "lang", "created_at", "is_retweet",
]
_SEARCH_FIELDS_INSTAGRAM = [
    "id", "caption", "username", "full_name", "profile_pic_url",
    "like_count", "comment_count", "reshare_count", "video_play_count",
    "image_url", "video_url", "media_type", "video_duration",
    "location", "created_at",
]
_SEARCH_FIELDS_REDDIT = [
    "id", "title", "selftext", "author_username", "subreddit_name",
    "score", "upvotes", "downvotes", "upvote_ratio", "comments_count",
    "is_video", "permalink", "thumbnail", "url", "post_hint",
    "link_flair_text", "created_at",
]

# ---------------------------------------------------------------------------
# Field list constants — users (A.2)
# ---------------------------------------------------------------------------
_SEARCH_USER_FIELDS_TWITTER = [
    "id", "username", "name", "description", "location", "verified",
    "followers_count", "following_count", "tweet_count", "profile_image_url",
    "is_inauthentic", "is_inauthentic_prob_score",
    "agg_relevance", "relevant_tweets_count",
    "relevant_tweets_impressions_sum", "relevant_tweets_likes_sum",
    "relevant_tweets_quotes_sum", "relevant_tweets_replies_sum",
    "relevant_tweets_retweets_sum",
    "created_at",
]
_SEARCH_USER_FIELDS_INSTAGRAM = [
    "id", "username", "full_name", "biography", "is_private", "is_verified",
    "follower_count", "following_count", "media_count",
    "profile_pic_url", "profile_url", "external_url",
    "agg_relevance", "relevant_posts_count",
    "relevant_posts_likes_sum", "relevant_posts_comments_sum",
    "relevant_posts_reshares_sum", "relevant_posts_video_plays_sum",
]
_SEARCH_USER_FIELDS_REDDIT = [
    "id", "username", "profile_url", "profile_pic_url",
    "link_karma", "comment_karma", "total_karma",
    "is_gold", "is_mod", "has_verified_email",
    "profile_description", "created_at",
    "agg_relevance", "relevant_posts_count",
    "relevant_posts_upvotes_sum", "relevant_posts_comments_count_sum",
]

# ---------------------------------------------------------------------------
# Field list constants — comments (A.2)
# ---------------------------------------------------------------------------
_COMMENT_FIELDS_TWITTER = [
    "id", "text", "author_username", "like_count", "retweet_count",
    "reply_count", "reply_to_tweet_id", "conversation_id",
    "created_at",
]
_COMMENT_FIELDS_INSTAGRAM = [
    "id", "text", "parent_post_id", "parent_post_user_id", "type",
    "parent_comment_id", "child_comment_count", "user_id", "username",
    "full_name", "like_count", "status", "is_spam",
    "created_at",
]
_COMMENT_FIELDS_REDDIT = [
    "id", "body", "parent_post_id", "parent_id", "author_id",
    "author_username", "post_subreddit_name", "score", "upvotes",
    "downvotes", "controversiality", "depth", "is_submitter",
    "stickied", "collapsed", "distinguished",
    "created_at",
]

# ---------------------------------------------------------------------------
# Field list constants — subreddits (A.2)
# ---------------------------------------------------------------------------
_SUBREDDIT_FIELDS = [
    "id", "display_name", "title", "public_description", "description",
    "subscribers_count", "active_user_count", "subreddit_type", "over18",
    "lang", "url", "subreddit_url", "icon_img",
    "agg_relevance", "relevant_posts_count",
    "relevant_posts_upvotes_sum", "relevant_posts_comments_count_sum",
]


class XpozAdapter(BaseMentionFetcher):
    """Xpoz SDK adapter — Twitter, Instagram, Reddit via pre-indexed search."""

    SUPPORTED_SOURCES = frozenset({DataSource.TWITTER, DataSource.INSTAGRAM, DataSource.REDDIT})

    def __init__(
        self,
        settings: MonitoringSettings | None = None,
        *,
        default_source: DataSource = DataSource.TWITTER,
    ) -> None:
        self._default_source = default_source  # Must be set before super().__init__ (accesses self.source)
        super().__init__(settings)
        self._api_key = self._settings.xpoz_api_key.get_secret_value()
        self._client: AsyncXpozClient | None = None
        self._xpoz_cb = CircuitBreaker(failure_threshold=3, reset_timeout=120, name="xpoz")

    @property
    def source(self) -> DataSource:
        return self._default_source

    async def __aenter__(self) -> Self:
        self._client = AsyncXpozClient(api_key=self._api_key, timeout=25.0)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            try:
                await self._client.__aexit__(*args)
            except RuntimeError:
                pass
            self._client = None

    # -----------------------------------------------------------------------
    # Helper methods (A.13)
    # -----------------------------------------------------------------------

    def _get_namespace(self, platform: DataSource) -> Any:
        """Return the correct Xpoz SDK namespace for the given platform."""
        if self._client is None:
            raise MentionFetchError("adapter not initialized — call __aenter__ first")
        if platform == DataSource.TWITTER:
            return self._client.twitter
        elif platform == DataSource.INSTAGRAM:
            return self._client.instagram
        elif platform == DataSource.REDDIT:
            return self._client.reddit
        raise MentionFetchError(f"Unsupported Xpoz platform: {platform}")

    async def _safe_xpoz_call(self, coro: Any) -> Any:
        """Resilience wrapper for Xpoz SDK calls.

        - OperationTimeoutError → MentionFetchError (unrecoverable)
        - AuthenticationError → log + re-raise
        - NotFoundError → return None
        - XpozError → propagate for retry by caller / BaseMentionFetcher
        """
        if not self._xpoz_cb.allow_request():
            raise MentionFetchError("Xpoz circuit breaker open")

        try:
            result = await coro
            self._xpoz_cb.record_success()
            await _cost_recorder.record("xpoz", "api_call", cost_usd=XPOZ_COST_PER_CALL)
            return result
        except OperationTimeoutError as e:
            self._xpoz_cb.record_failure()
            raise MentionFetchError(f"Xpoz timeout after {e.elapsed_seconds}s") from e
        except AuthenticationError:
            self._xpoz_cb.record_failure()
            logger.error("xpoz_authentication_failed")
            raise
        except NotFoundError:
            self._xpoz_cb.record_success()
            return None
        except XpozError:
            self._xpoz_cb.record_failure()
            raise

    def _get_user_fields(self, platform: DataSource) -> list[str]:
        """Return the user field list constant for the given platform."""
        if platform == DataSource.TWITTER:
            return _SEARCH_USER_FIELDS_TWITTER
        elif platform == DataSource.INSTAGRAM:
            return _SEARCH_USER_FIELDS_INSTAGRAM
        elif platform == DataSource.REDDIT:
            return _SEARCH_USER_FIELDS_REDDIT
        raise MentionFetchError(f"No user fields for platform: {platform}")

    # -----------------------------------------------------------------------
    # User mapping functions (A.3)
    # -----------------------------------------------------------------------

    @staticmethod
    def _map_twitter_user(user: Any) -> XpozUser:
        """Map TwitterUser SDK object to XpozUser."""
        # Build relevant engagement sum from individual engagement fields
        engagement_sum: int | None = None
        likes = getattr(user, "relevant_tweets_likes_sum", None)
        quotes = getattr(user, "relevant_tweets_quotes_sum", None)
        replies = getattr(user, "relevant_tweets_replies_sum", None)
        retweets = getattr(user, "relevant_tweets_retweets_sum", None)
        parts = [v for v in (likes, quotes, replies, retweets) if v is not None]
        if parts:
            engagement_sum = sum(parts)

        metadata: dict[str, Any] = {}
        location = getattr(user, "location", None)
        if location:
            metadata["location"] = location
        impressions = getattr(user, "relevant_tweets_impressions_sum", None)
        if impressions is not None:
            metadata["relevant_impressions"] = impressions
        created = getattr(user, "created_at", None)
        if created:
            metadata["created_at"] = str(created)

        return XpozUser(
            platform=DataSource.TWITTER,
            user_id=str(user.id),
            username=user.username or "",
            display_name=getattr(user, "name", None),
            bio=getattr(user, "description", None),
            follower_count=getattr(user, "followers_count", None),
            following_count=getattr(user, "following_count", None),
            post_count=getattr(user, "tweet_count", None),
            is_verified=bool(getattr(user, "verified", False)),
            profile_image_url=getattr(user, "profile_image_url", None),
            is_inauthentic=getattr(user, "is_inauthentic", None),
            inauthentic_prob_score=getattr(user, "is_inauthentic_prob_score", None),
            relevance_score=getattr(user, "agg_relevance", None),
            relevant_posts_count=getattr(user, "relevant_tweets_count", None),
            relevant_engagement_sum=engagement_sum,
            metadata=metadata,
        )

    @staticmethod
    def _map_instagram_user(user: Any) -> XpozUser:
        """Map InstagramUser SDK object to XpozUser."""
        engagement_sum: int | None = None
        likes = getattr(user, "relevant_posts_likes_sum", None)
        comments = getattr(user, "relevant_posts_comments_sum", None)
        reshares = getattr(user, "relevant_posts_reshares_sum", None)
        parts = [v for v in (likes, comments, reshares) if v is not None]
        if parts:
            engagement_sum = sum(parts)

        metadata: dict[str, Any] = {}
        if getattr(user, "is_private", None):
            metadata["is_private"] = True
        ext_url = getattr(user, "external_url", None)
        if ext_url:
            metadata["external_url"] = ext_url
        profile_url = getattr(user, "profile_url", None)
        if profile_url:
            metadata["profile_url"] = profile_url
        plays = getattr(user, "relevant_posts_video_plays_sum", None)
        if plays is not None:
            metadata["relevant_video_plays"] = plays

        return XpozUser(
            platform=DataSource.INSTAGRAM,
            user_id=str(user.id),
            username=user.username or "",
            display_name=getattr(user, "full_name", None),
            bio=getattr(user, "biography", None),
            follower_count=getattr(user, "follower_count", None),
            following_count=getattr(user, "following_count", None),
            post_count=getattr(user, "media_count", None),
            is_verified=bool(getattr(user, "is_verified", False)),
            profile_image_url=getattr(user, "profile_pic_url", None),
            is_inauthentic=None,
            inauthentic_prob_score=None,
            relevance_score=getattr(user, "agg_relevance", None),
            relevant_posts_count=getattr(user, "relevant_posts_count", None),
            relevant_engagement_sum=engagement_sum,
            metadata=metadata,
        )

    @staticmethod
    def _map_reddit_user(user: Any) -> XpozUser:
        """Map RedditUser SDK object to XpozUser."""
        engagement_sum: int | None = None
        upvotes = getattr(user, "relevant_posts_upvotes_sum", None)
        comments_sum = getattr(user, "relevant_posts_comments_count_sum", None)
        parts = [v for v in (upvotes, comments_sum) if v is not None]
        if parts:
            engagement_sum = sum(parts)

        metadata: dict[str, Any] = {}
        link_karma = getattr(user, "link_karma", None)
        comment_karma = getattr(user, "comment_karma", None)
        total_karma = getattr(user, "total_karma", None)
        if total_karma is not None:
            metadata["total_karma"] = total_karma
        if link_karma is not None:
            metadata["link_karma"] = link_karma
        if comment_karma is not None:
            metadata["comment_karma"] = comment_karma
        if getattr(user, "is_gold", None):
            metadata["is_gold"] = True
        if getattr(user, "is_mod", None):
            metadata["is_mod"] = True
        created = getattr(user, "created_at", None)
        if created:
            metadata["created_at"] = str(created)
        profile_desc = getattr(user, "profile_description", None)

        return XpozUser(
            platform=DataSource.REDDIT,
            user_id=str(user.id),
            username=user.username or "",
            display_name=None,
            bio=profile_desc,
            follower_count=None,
            following_count=None,
            post_count=None,
            is_verified=bool(getattr(user, "has_verified_email", False)),
            profile_image_url=getattr(user, "profile_pic_url", None),
            is_inauthentic=None,
            inauthentic_prob_score=None,
            relevance_score=getattr(user, "agg_relevance", None),
            relevant_posts_count=getattr(user, "relevant_posts_count", None),
            relevant_engagement_sum=engagement_sum,
            metadata=metadata,
        )

    # -----------------------------------------------------------------------
    # Comment mapping functions (A.4)
    # -----------------------------------------------------------------------

    @staticmethod
    def _map_twitter_comment(comment: Any) -> XpozComment:
        """Map a TwitterPost (reply) to XpozComment."""
        metadata: dict[str, Any] = {}
        retweet_count = getattr(comment, "retweet_count", None)
        if retweet_count:
            metadata["retweet_count"] = retweet_count
        reply_count = getattr(comment, "reply_count", None)
        if reply_count:
            metadata["reply_count"] = reply_count

        return XpozComment(
            comment_id=str(comment.id),
            post_id=str(
                getattr(comment, "reply_to_tweet_id", None)
                or getattr(comment, "conversation_id", None)
                or ""
            ),
            platform=DataSource.TWITTER,
            author_username=getattr(comment, "author_username", None),
            content=getattr(comment, "text", None) or "",
            like_count=getattr(comment, "like_count", None) or 0,
            is_spam=None,
            controversiality=None,
            is_submitter=None,
            distinguished=None,
            depth=None,
            published_at=getattr(comment, "created_at", None),
            metadata=metadata,
        )

    @staticmethod
    def _map_instagram_comment(comment: Any) -> XpozComment:
        """Map InstagramComment SDK object to XpozComment."""
        metadata: dict[str, Any] = {}
        comment_type = getattr(comment, "type", None)
        if comment_type:
            metadata["type"] = comment_type
        parent_comment_id = getattr(comment, "parent_comment_id", None)
        if parent_comment_id:
            metadata["parent_comment_id"] = str(parent_comment_id)
        child_count = getattr(comment, "child_comment_count", None)
        if child_count:
            metadata["child_comment_count"] = child_count
        full_name = getattr(comment, "full_name", None)
        if full_name:
            metadata["full_name"] = full_name

        return XpozComment(
            comment_id=str(comment.id),
            post_id=str(getattr(comment, "parent_post_id", None) or ""),
            platform=DataSource.INSTAGRAM,
            author_username=getattr(comment, "username", None),
            content=getattr(comment, "text", None) or "",
            like_count=getattr(comment, "like_count", None) or 0,
            is_spam=getattr(comment, "is_spam", None),
            controversiality=None,
            is_submitter=None,
            distinguished=None,
            depth=None,
            published_at=getattr(comment, "created_at", None),
            metadata=metadata,
        )

    @staticmethod
    def _map_reddit_comment(comment: Any) -> XpozComment:
        """Map RedditComment SDK object to XpozComment."""
        metadata: dict[str, Any] = {}
        score = getattr(comment, "score", None)
        if score is not None:
            metadata["score"] = score
        upvotes = getattr(comment, "upvotes", None)
        if upvotes is not None:
            metadata["upvotes"] = upvotes
        downvotes = getattr(comment, "downvotes", None)
        if downvotes is not None:
            metadata["downvotes"] = downvotes
        subreddit = getattr(comment, "post_subreddit_name", None)
        if subreddit:
            metadata["subreddit"] = subreddit

        return XpozComment(
            comment_id=str(comment.id),
            post_id=str(getattr(comment, "parent_post_id", None) or ""),
            platform=DataSource.REDDIT,
            author_username=getattr(comment, "author_username", None),
            content=getattr(comment, "body", None) or "",
            like_count=getattr(comment, "score", None) or 0,
            is_spam=None,
            controversiality=getattr(comment, "controversiality", None),
            is_submitter=getattr(comment, "is_submitter", None),
            distinguished=getattr(comment, "distinguished", None),
            depth=getattr(comment, "depth", None),
            published_at=getattr(comment, "created_at", None),
            metadata=metadata,
        )

    # -----------------------------------------------------------------------
    # Subreddit mapping (A.5)
    # -----------------------------------------------------------------------

    @staticmethod
    def _map_subreddit(sub: Any) -> XpozSubreddit:
        """Map RedditSubreddit SDK object to XpozSubreddit."""
        metadata: dict[str, Any] = {}
        icon = getattr(sub, "icon_img", None)
        if icon:
            metadata["icon_img"] = icon
        upvotes_sum = getattr(sub, "relevant_posts_upvotes_sum", None)
        if upvotes_sum is not None:
            metadata["relevant_posts_upvotes_sum"] = upvotes_sum
        comments_sum = getattr(sub, "relevant_posts_comments_count_sum", None)
        if comments_sum is not None:
            metadata["relevant_posts_comments_count_sum"] = comments_sum

        return XpozSubreddit(
            name=getattr(sub, "display_name", None) or "",
            title=getattr(sub, "title", None),
            description=getattr(sub, "public_description", None) or getattr(sub, "description", None),
            subscribers_count=getattr(sub, "subscribers_count", None),
            active_users_count=getattr(sub, "active_user_count", None),
            subreddit_type=getattr(sub, "subreddit_type", None),
            over18=bool(getattr(sub, "over18", False)),
            language=getattr(sub, "lang", None),
            url=getattr(sub, "subreddit_url", None) or getattr(sub, "url", None),
            relevance_score=getattr(sub, "agg_relevance", None),
            relevant_posts_count=getattr(sub, "relevant_posts_count", None),
            metadata=metadata,
        )

    # -----------------------------------------------------------------------
    # Existing fetch / search / map methods (unchanged)
    # -----------------------------------------------------------------------

    async def _do_fetch(
        self,
        query: str,
        *,
        cursor: str | None = None,
        limit: int = 100,
    ) -> tuple[list[RawMention], str | None]:
        if self._client is None:
            raise MentionFetchError("adapter not initialized — call __aenter__ first")

        try:
            result = await self._search(query, cursor=cursor, force_latest=True)
        except OperationTimeoutError as e:
            raise MentionFetchError(f"Xpoz timeout after {e.elapsed_seconds}s") from e
        # XpozError intentionally NOT caught here — let it propagate
        # so BaseMentionFetcher retries transient SDK errors

        mentions = [self._map_post(post) for post in result.data]

        # Cursor = page number for Xpoz pagination
        next_cursor = None
        if result.has_next_page():
            next_cursor = str(result.pagination.page_number + 1)

        # Xpoz returns up to 300 per page from pre-indexed data.
        # Let the caller (discover_mentions) handle the final cap.
        return mentions[:limit], next_cursor

    async def fetch_all_mentions(
        self,
        query: str,
        *,
        max_results: int = 500,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        language: str | None = None,
        author_username: str | None = None,
        subreddit: str | None = None,
        sort: str | None = None,
        time_range: str | None = None,
        force_latest: bool = True,
    ) -> list[RawMention]:
        """Paginated fetch — collects up to max_results across multiple pages.

        Safety caps: 5 pages max, 15-second deadline.
        Backward compat: fetch_mentions() is unchanged (monitoring system uses it).
        """
        deadline = time.monotonic() + 15.0
        max_pages = 5
        all_mentions: list[RawMention] = []

        result = await self._search(
            query,
            start_date=start_date,
            end_date=end_date,
            language=language,
            author_username=author_username,
            subreddit=subreddit,
            sort=sort,
            time_range=time_range,
            force_latest=force_latest,
        )

        all_mentions.extend(self._map_post(post) for post in result.data)

        pages_fetched = 1
        while (
            result.has_next_page()
            and len(all_mentions) < max_results
            and pages_fetched < max_pages
            and time.monotonic() < deadline
        ):
            try:
                result = await result.next_page()
            except Exception:
                logger.warning("fetch_all_mentions: pagination stopped after %d pages", pages_fetched)
                break
            all_mentions.extend(self._map_post(post) for post in result.data)
            pages_fetched += 1

        logger.info(
            "fetch_all_mentions: pages=%d total=%d query=%s",
            pages_fetched, len(all_mentions), query[:50],
        )
        return all_mentions[:max_results]

    async def _search(
        self,
        query: str,
        *,
        cursor: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        language: str | None = None,
        author_username: str | None = None,
        subreddit: str | None = None,
        sort: str | None = None,
        time_range: str | None = None,
        force_latest: bool | None = None,
    ) -> Any:  # PaginatedResult
        """Dispatch search to the correct Xpoz namespace."""
        if self._client is None:
            raise MentionFetchError("adapter not initialized — call __aenter__ first")
        if self._default_source == DataSource.TWITTER:
            kwargs: dict[str, Any] = {"fields": _SEARCH_FIELDS_TWITTER}
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if language:
                kwargs["language"] = language
            if author_username:
                kwargs["author_username"] = author_username
            if force_latest is not None:
                kwargs["force_latest"] = force_latest
            result = await self._client.twitter.search_posts(query, **kwargs)
        elif self._default_source == DataSource.INSTAGRAM:
            kwargs = {"fields": _SEARCH_FIELDS_INSTAGRAM}
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if force_latest is not None:
                kwargs["force_latest"] = force_latest
            result = await self._client.instagram.search_posts(query, **kwargs)
        elif self._default_source == DataSource.REDDIT:
            kwargs = {"fields": _SEARCH_FIELDS_REDDIT}
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if subreddit:
                kwargs["subreddit"] = subreddit
            if sort:
                kwargs["sort"] = sort
            if time_range:
                kwargs["time"] = time_range
            if force_latest is not None:
                kwargs["force_latest"] = force_latest
            result = await self._client.reddit.search_posts(query, **kwargs)
        else:
            raise MentionFetchError(f"Unsupported Xpoz source: {self._default_source}")

        # If cursor provided, jump to that page
        if cursor:
            try:
                result = await result.get_page(int(cursor))
            except (ValueError, TypeError) as e:
                raise MentionFetchError(f"Invalid cursor value: {cursor}") from e

        return result

    def _map_post(self, post: Any) -> RawMention:
        if self._default_source == DataSource.TWITTER:
            return self._map_twitter(post)
        elif self._default_source == DataSource.INSTAGRAM:
            return self._map_instagram(post)
        elif self._default_source == DataSource.REDDIT:
            return self._map_reddit(post)
        raise MentionFetchError(f"No mapper for {self._default_source}")

    @staticmethod
    def _parse_created_at(value: Any) -> datetime | None:
        """Coerce Xpoz SDK created_at (str, int/float, or datetime) → datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _map_post_for_platform(self, post: Any, platform: DataSource) -> RawMention:
        """Map a post to RawMention using the specified platform's mapper."""
        if platform == DataSource.TWITTER:
            return self._map_twitter(post)
        elif platform == DataSource.INSTAGRAM:
            return self._map_instagram(post)
        elif platform == DataSource.REDDIT:
            return self._map_reddit(post)
        raise MentionFetchError(f"No mapper for {platform}")

    def _map_twitter(self, post: Any) -> RawMention:
        metadata: dict[str, Any] = {}
        if post.quote_count:
            metadata["quote_count"] = post.quote_count
        if post.bookmark_count:
            metadata["bookmark_count"] = post.bookmark_count
        if post.hashtags:
            metadata["hashtags"] = post.hashtags
        if post.mentions:
            metadata["mentions"] = post.mentions
        if post.media_urls:
            metadata["media_urls_extra"] = post.media_urls
        if post.region:
            metadata["region"] = post.region
        if post.city:
            metadata["city"] = post.city
        if getattr(post, "is_retweet", False):
            metadata["is_retweet"] = True

        return RawMention(
            source=DataSource.TWITTER,
            source_id=str(post.id),
            author_handle=post.author_username,
            content=post.text or "",
            published_at=self._parse_created_at(post.created_at),
            engagement_likes=post.like_count or 0,
            engagement_shares=post.retweet_count or 0,
            engagement_comments=post.reply_count or 0,
            reach_estimate=post.impression_count,
            language=post.lang or "en",
            geo_country=post.country,
            media_urls=post.media_urls or [],
            metadata=metadata,
        )

    def _map_instagram(self, post: Any) -> RawMention:
        media_urls = []
        if post.image_url:
            media_urls.append(post.image_url)
        if post.video_url:
            media_urls.append(post.video_url)

        metadata: dict[str, Any] = {}
        if post.media_type:
            metadata["media_type"] = post.media_type
        if hasattr(post, "location") and post.location:
            metadata["city"] = post.location
        if getattr(post, "full_name", None):
            metadata["full_name"] = post.full_name
        if getattr(post, "profile_pic_url", None):
            metadata["avatar_url"] = post.profile_pic_url
        if getattr(post, "video_duration", None):
            metadata["duration"] = post.video_duration

        return RawMention(
            source=DataSource.INSTAGRAM,
            source_id=str(post.id),
            author_handle=post.username,
            author_name=getattr(post, "full_name", None),
            content=post.caption or "",
            published_at=self._parse_created_at(post.created_at),
            engagement_likes=post.like_count or 0,
            engagement_shares=post.reshare_count or 0,
            engagement_comments=post.comment_count or 0,
            reach_estimate=post.video_play_count,
            media_urls=media_urls,
            metadata=metadata,
        )

    def _map_reddit(self, post: Any) -> RawMention:
        content = post.title or ""
        if post.selftext:
            content = f"{content}\n\n{post.selftext}" if content else post.selftext

        metadata: dict[str, Any] = {}
        if post.subreddit_name:
            metadata["subreddit"] = post.subreddit_name
        if post.upvotes is not None and post.downvotes is not None:
            metadata["engagement_extra"] = {
                "upvotes": post.upvotes,
                "downvotes": post.downvotes,
                "upvote_ratio": post.upvote_ratio,
            }
        if post.is_video:
            metadata["media_type"] = "video"
        if post.permalink:
            metadata["permalink"] = post.permalink
        if getattr(post, "link_flair_text", None):
            metadata["flair"] = post.link_flair_text
        if getattr(post, "post_hint", None):
            metadata["post_hint"] = post.post_hint

        # Extract thumbnail — Reddit provides thumbnail URLs for link/image posts
        media_urls: list[str] = []
        thumb = getattr(post, "thumbnail", None)
        if thumb and thumb not in ("self", "default", "nsfw", "spoiler", "image", ""):
            media_urls.append(thumb)
        # Also use the linked URL for image posts (post_hint: "image")
        post_hint = getattr(post, "post_hint", None)
        linked_url = getattr(post, "url", None)
        if post_hint == "image" and linked_url:
            media_urls.append(linked_url)

        return RawMention(
            source=DataSource.REDDIT,
            source_id=str(post.id),
            author_handle=post.author_username,
            content=content,
            url=f"https://reddit.com{post.permalink}" if post.permalink else None,
            published_at=self._parse_created_at(post.created_at),
            engagement_likes=post.score or 0,
            engagement_comments=post.comments_count or 0,
            media_urls=media_urls,
            metadata=metadata,
        )

    # -----------------------------------------------------------------------
    # Creator/user discovery (A.6)
    # -----------------------------------------------------------------------

    async def search_users_by_keywords(
        self,
        query: str,
        *,
        platform: DataSource,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        language: str | None = None,
        subreddit: str | None = None,
        limit: int = 50,
    ) -> list[XpozUser]:
        """Search for users/creators by keyword across a platform."""
        ns = self._get_namespace(platform)
        fields = self._get_user_fields(platform)

        kwargs: dict[str, Any] = {"fields": fields}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if platform == DataSource.TWITTER and language:
            kwargs["language"] = language
        if platform == DataSource.REDDIT and subreddit:
            kwargs["subreddit"] = subreddit

        result = await self._safe_xpoz_call(ns.get_users_by_keywords(query, **kwargs))
        if result is None:
            return []

        mapper = {
            DataSource.TWITTER: self._map_twitter_user,
            DataSource.INSTAGRAM: self._map_instagram_user,
            DataSource.REDDIT: self._map_reddit_user,
        }[platform]

        return [mapper(u) for u in result.data[:limit]]

    async def get_user_profile(
        self,
        identifier: str,
        *,
        platform: DataSource,
        identifier_type: str = "username",
    ) -> XpozUser | None:
        """Get a single user profile by username or ID."""
        ns = self._get_namespace(platform)
        fields = self._get_user_fields(platform)

        if platform == DataSource.REDDIT:
            # Reddit get_user takes username only (no identifier_type)
            user = await self._safe_xpoz_call(ns.get_user(identifier, fields=fields))
        else:
            user = await self._safe_xpoz_call(
                ns.get_user(identifier, identifier_type=identifier_type, fields=fields)
            )

        if user is None:
            return None

        mapper = {
            DataSource.TWITTER: self._map_twitter_user,
            DataSource.INSTAGRAM: self._map_instagram_user,
            DataSource.REDDIT: self._map_reddit_user,
        }[platform]

        return mapper(user)

    # -----------------------------------------------------------------------
    # Social graph (A.7)
    # -----------------------------------------------------------------------

    async def get_user_connections(
        self,
        username: str,
        *,
        platform: DataSource,
        connection_type: str = "followers",
        limit: int = 50,
    ) -> list[XpozUser]:
        """Get followers/following for a user. Twitter + Instagram only."""
        if platform == DataSource.REDDIT:
            raise MentionFetchError("Reddit does not support user connections via Xpoz")

        ns = self._get_namespace(platform)
        fields = self._get_user_fields(platform)

        result = await self._safe_xpoz_call(
            ns.get_user_connections(username, connection_type, fields=fields)
        )
        if result is None:
            return []

        mapper = {
            DataSource.TWITTER: self._map_twitter_user,
            DataSource.INSTAGRAM: self._map_instagram_user,
        }[platform]

        return [mapper(u) for u in result.data[:limit]]

    async def get_post_interacting_users(
        self,
        post_id: str,
        *,
        platform: DataSource,
        interaction_type: str = "liking_users",
        limit: int = 50,
    ) -> list[XpozUser]:
        """Get users who interacted with a post. Twitter + Instagram only."""
        if platform == DataSource.REDDIT:
            raise MentionFetchError("Reddit does not support post interacting users via Xpoz")

        ns = self._get_namespace(platform)
        fields = self._get_user_fields(platform)

        result = await self._safe_xpoz_call(
            ns.get_post_interacting_users(post_id, interaction_type, fields=fields)
        )
        if result is None:
            return []

        mapper = {
            DataSource.TWITTER: self._map_twitter_user,
            DataSource.INSTAGRAM: self._map_instagram_user,
        }[platform]

        return [mapper(u) for u in result.data[:limit]]

    # -----------------------------------------------------------------------
    # Enhanced post search (A.8)
    # -----------------------------------------------------------------------

    async def get_posts_by_ids(
        self,
        post_ids: list[str],
        *,
        platform: DataSource,
    ) -> list[RawMention]:
        """Get posts by their IDs. Twitter + Instagram only."""
        if platform == DataSource.REDDIT:
            raise MentionFetchError("Reddit get_posts_by_ids not supported — use get_post_with_comments")

        ns = self._get_namespace(platform)
        fields = (
            _SEARCH_FIELDS_TWITTER if platform == DataSource.TWITTER
            else _SEARCH_FIELDS_INSTAGRAM
        )

        posts = await self._safe_xpoz_call(ns.get_posts_by_ids(post_ids, fields=fields))
        if posts is None:
            return []

        return [self._map_post_for_platform(p, platform) for p in posts]

    async def get_posts_by_author(
        self,
        identifier: str,
        *,
        platform: DataSource,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
    ) -> list[RawMention]:
        """Get posts by a specific author. Twitter + Instagram only."""
        if platform == DataSource.REDDIT:
            raise MentionFetchError("Reddit get_posts_by_author not supported via Xpoz")

        ns = self._get_namespace(platform)

        kwargs: dict[str, Any] = {}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        if platform == DataSource.TWITTER:
            kwargs["fields"] = _SEARCH_FIELDS_TWITTER
            result = await self._safe_xpoz_call(
                ns.get_posts_by_author(identifier, **kwargs)
            )
        else:
            # Instagram uses get_posts_by_user
            kwargs["fields"] = _SEARCH_FIELDS_INSTAGRAM
            result = await self._safe_xpoz_call(
                ns.get_posts_by_user(identifier, **kwargs)
            )

        if result is None:
            return []

        return [self._map_post_for_platform(p, platform) for p in result.data[:limit]]

    # -----------------------------------------------------------------------
    # Viral tracking (A.9) — Twitter only
    # -----------------------------------------------------------------------

    async def get_retweets(
        self,
        post_id: str,
        *,
        limit: int = 50,
    ) -> list[RawMention]:
        """Get retweets of a Twitter post."""
        ns = self._get_namespace(DataSource.TWITTER)

        result = await self._safe_xpoz_call(
            ns.get_retweets(post_id, fields=_SEARCH_FIELDS_TWITTER)
        )
        if result is None:
            return []

        return [self._map_twitter(p) for p in result.data[:limit]]

    async def get_quotes(
        self,
        post_id: str,
        *,
        limit: int = 50,
    ) -> list[RawMention]:
        """Get quote tweets of a Twitter post."""
        ns = self._get_namespace(DataSource.TWITTER)

        result = await self._safe_xpoz_call(
            ns.get_quotes(post_id, fields=_SEARCH_FIELDS_TWITTER)
        )
        if result is None:
            return []

        return [self._map_twitter(p) for p in result.data[:limit]]

    # -----------------------------------------------------------------------
    # Comments / discussions (A.10)
    # -----------------------------------------------------------------------

    async def get_post_comments(
        self,
        post_id: str,
        *,
        platform: DataSource,
        limit: int = 50,
    ) -> list[XpozComment]:
        """Get comments on a post across platforms."""
        ns = self._get_namespace(platform)

        if platform == DataSource.TWITTER:
            result = await self._safe_xpoz_call(
                ns.get_comments(post_id, fields=_COMMENT_FIELDS_TWITTER)
            )
            if result is None:
                return []
            return [self._map_twitter_comment(c) for c in result.data[:limit]]

        elif platform == DataSource.INSTAGRAM:
            result = await self._safe_xpoz_call(
                ns.get_comments(post_id, fields=_COMMENT_FIELDS_INSTAGRAM)
            )
            if result is None:
                return []
            return [self._map_instagram_comment(c) for c in result.data[:limit]]

        elif platform == DataSource.REDDIT:
            # Reddit uses get_post_with_comments — extract comments
            result = await self._safe_xpoz_call(
                ns.get_post_with_comments(post_id, comment_fields=_COMMENT_FIELDS_REDDIT)
            )
            if result is None:
                return []
            comments = getattr(result, "comments", None) or []
            return [self._map_reddit_comment(c) for c in comments[:limit]]

        raise MentionFetchError(f"Unsupported platform for comments: {platform}")

    async def search_comments(
        self,
        query: str,
        *,
        subreddit: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
    ) -> list[XpozComment]:
        """Search Reddit comments by keyword. Reddit only."""
        ns = self._get_namespace(DataSource.REDDIT)

        kwargs: dict[str, Any] = {"fields": _COMMENT_FIELDS_REDDIT}
        if subreddit:
            kwargs["subreddit"] = subreddit
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        result = await self._safe_xpoz_call(ns.search_comments(query, **kwargs))
        if result is None:
            return []

        return [self._map_reddit_comment(c) for c in result.data[:limit]]

    async def get_post_with_comments(
        self,
        post_id: str,
    ) -> tuple[RawMention, list[XpozComment]]:
        """Get a Reddit post with its comments. Reddit only."""
        ns = self._get_namespace(DataSource.REDDIT)

        result = await self._safe_xpoz_call(
            ns.get_post_with_comments(
                post_id,
                post_fields=_SEARCH_FIELDS_REDDIT,
                comment_fields=_COMMENT_FIELDS_REDDIT,
            )
        )
        if result is None:
            raise MentionFetchError(f"Reddit post {post_id} not found")

        post = getattr(result, "post", None)
        if post is None:
            raise MentionFetchError(f"Reddit post {post_id} has no post data")

        mention = self._map_reddit(post)
        comments_raw = getattr(result, "comments", None) or []
        comments = [self._map_reddit_comment(c) for c in comments_raw]

        return mention, comments

    # -----------------------------------------------------------------------
    # Reddit community (A.11)
    # -----------------------------------------------------------------------

    async def search_subreddits(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[XpozSubreddit]:
        """Search subreddits by name/description. Reddit only."""
        ns = self._get_namespace(DataSource.REDDIT)

        result = await self._safe_xpoz_call(
            ns.search_subreddits(query, limit=limit, fields=_SUBREDDIT_FIELDS)
        )
        if result is None:
            return []

        # search_subreddits returns list (not paginated)
        return [self._map_subreddit(s) for s in result[:limit]]

    async def get_subreddit_with_posts(
        self,
        subreddit_name: str,
        *,
        limit: int = 20,
    ) -> tuple[XpozSubreddit, list[RawMention]]:
        """Get a subreddit and its posts. Reddit only."""
        ns = self._get_namespace(DataSource.REDDIT)

        result = await self._safe_xpoz_call(
            ns.get_subreddit_with_posts(
                subreddit_name,
                subreddit_fields=_SUBREDDIT_FIELDS,
                post_fields=_SEARCH_FIELDS_REDDIT,
            )
        )
        if result is None:
            raise MentionFetchError(f"Subreddit '{subreddit_name}' not found")

        subreddit_obj = getattr(result, "subreddit", None)
        if subreddit_obj is None:
            raise MentionFetchError(f"Subreddit '{subreddit_name}' has no subreddit data")

        sub = self._map_subreddit(subreddit_obj)
        posts_raw = getattr(result, "posts", None) or []
        posts = [self._map_reddit(p) for p in posts_raw[:limit]]

        return sub, posts

    async def get_subreddits_by_keywords(
        self,
        query: str,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 20,
    ) -> list[XpozSubreddit]:
        """Search subreddits by keyword relevance. Reddit only."""
        ns = self._get_namespace(DataSource.REDDIT)

        kwargs: dict[str, Any] = {"fields": _SUBREDDIT_FIELDS}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        result = await self._safe_xpoz_call(
            ns.get_subreddits_by_keywords(query, **kwargs)
        )
        if result is None:
            return []

        return [self._map_subreddit(s) for s in result.data[:limit]]

    # -----------------------------------------------------------------------
    # Analytics (A.12) — Twitter only
    # -----------------------------------------------------------------------

    async def count_posts(
        self,
        phrase: str,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count posts matching a phrase. Twitter only."""
        ns = self._get_namespace(DataSource.TWITTER)

        kwargs: dict[str, Any] = {}
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date

        result = await self._safe_xpoz_call(ns.count_posts(phrase, **kwargs))
        if result is None:
            return 0

        return result
