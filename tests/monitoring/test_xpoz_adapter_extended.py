"""Comprehensive tests for XpozAdapter — user search, profiles, connections,
posts, viral tracking, comments, subreddits, analytics, and error handling.

All tests mock the Xpoz SDK client via unittest.mock.AsyncMock.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.monitoring.adapters.xpoz import XpozAdapter
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource, RawMention, XpozComment, XpozSubreddit, XpozUser

pytestmark = pytest.mark.mock_required


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_paginated(items: list) -> MagicMock:
    """Mimic Xpoz AsyncPaginatedResult with .data attribute."""
    result = MagicMock()
    result.data = items
    return result


def make_twitter_user(**overrides) -> MagicMock:
    user = MagicMock()
    user.id = overrides.get("id", "tw_123")
    user.username = overrides.get("username", "testuser")
    user.name = overrides.get("name", "Test User")
    user.description = overrides.get("description", "A bio")
    user.location = overrides.get("location", "NYC")
    user.verified = overrides.get("verified", True)
    user.followers_count = overrides.get("followers_count", 5000)
    user.following_count = overrides.get("following_count", 200)
    user.tweet_count = overrides.get("tweet_count", 1200)
    user.profile_image_url = overrides.get("profile_image_url", "https://img.example.com/tw.jpg")
    user.is_inauthentic = overrides.get("is_inauthentic", None)
    user.is_inauthentic_prob_score = overrides.get("is_inauthentic_prob_score", None)
    user.agg_relevance = overrides.get("agg_relevance", 0.85)
    user.relevant_tweets_count = overrides.get("relevant_tweets_count", 42)
    user.relevant_tweets_impressions_sum = overrides.get("relevant_tweets_impressions_sum", 100_000)
    user.relevant_tweets_likes_sum = overrides.get("relevant_tweets_likes_sum", 500)
    user.relevant_tweets_quotes_sum = overrides.get("relevant_tweets_quotes_sum", 50)
    user.relevant_tweets_replies_sum = overrides.get("relevant_tweets_replies_sum", 100)
    user.relevant_tweets_retweets_sum = overrides.get("relevant_tweets_retweets_sum", 200)
    user.created_at = overrides.get("created_at", datetime(2020, 1, 15))
    return user


def make_instagram_user(**overrides) -> MagicMock:
    user = MagicMock()
    user.id = overrides.get("id", "ig_456")
    user.username = overrides.get("username", "instauser")
    user.full_name = overrides.get("full_name", "Insta User")
    user.biography = overrides.get("biography", "IG bio")
    user.is_private = overrides.get("is_private", False)
    user.is_verified = overrides.get("is_verified", True)
    user.follower_count = overrides.get("follower_count", 10_000)
    user.following_count = overrides.get("following_count", 300)
    user.media_count = overrides.get("media_count", 500)
    user.profile_pic_url = overrides.get("profile_pic_url", "https://img.example.com/ig.jpg")
    user.profile_url = overrides.get("profile_url", "https://instagram.com/instauser")
    user.external_url = overrides.get("external_url", "https://example.com")
    user.agg_relevance = overrides.get("agg_relevance", 0.72)
    user.relevant_posts_count = overrides.get("relevant_posts_count", 15)
    user.relevant_posts_likes_sum = overrides.get("relevant_posts_likes_sum", 3000)
    user.relevant_posts_comments_sum = overrides.get("relevant_posts_comments_sum", 400)
    user.relevant_posts_reshares_sum = overrides.get("relevant_posts_reshares_sum", 100)
    user.relevant_posts_video_plays_sum = overrides.get("relevant_posts_video_plays_sum", 25_000)
    return user


def make_reddit_user(**overrides) -> MagicMock:
    user = MagicMock()
    user.id = overrides.get("id", "rd_789")
    user.username = overrides.get("username", "redditor")
    user.profile_url = overrides.get("profile_url", "https://reddit.com/u/redditor")
    user.profile_pic_url = overrides.get("profile_pic_url", "https://img.example.com/rd.jpg")
    user.link_karma = overrides.get("link_karma", 12_000)
    user.comment_karma = overrides.get("comment_karma", 8_000)
    user.total_karma = overrides.get("total_karma", 20_000)
    user.is_gold = overrides.get("is_gold", False)
    user.is_mod = overrides.get("is_mod", False)
    user.has_verified_email = overrides.get("has_verified_email", True)
    user.profile_description = overrides.get("profile_description", "Reddit bio")
    user.created_at = overrides.get("created_at", datetime(2019, 6, 1))
    user.agg_relevance = overrides.get("agg_relevance", 0.65)
    user.relevant_posts_count = overrides.get("relevant_posts_count", 10)
    user.relevant_posts_upvotes_sum = overrides.get("relevant_posts_upvotes_sum", 2000)
    user.relevant_posts_comments_count_sum = overrides.get("relevant_posts_comments_count_sum", 300)
    return user


def make_twitter_post(**overrides) -> MagicMock:
    post = MagicMock()
    post.id = overrides.get("id", "tweet_1")
    post.text = overrides.get("text", "Hello Twitter!")
    post.author_username = overrides.get("author_username", "tweetauthor")
    post.like_count = overrides.get("like_count", 42)
    post.retweet_count = overrides.get("retweet_count", 10)
    post.reply_count = overrides.get("reply_count", 5)
    post.quote_count = overrides.get("quote_count", 3)
    post.impression_count = overrides.get("impression_count", 9000)
    post.bookmark_count = overrides.get("bookmark_count", 2)
    post.hashtags = overrides.get("hashtags", ["#test"])
    post.mentions = overrides.get("mentions", ["@someone"])
    post.media_urls = overrides.get("media_urls", ["https://pic.example.com/1.jpg"])
    post.country = overrides.get("country", "US")
    post.region = overrides.get("region", "CA")
    post.city = overrides.get("city", "San Francisco")
    post.lang = overrides.get("lang", "en")
    post.created_at = overrides.get("created_at", datetime(2025, 1, 10))
    post.is_retweet = overrides.get("is_retweet", False)
    return post


def make_instagram_post(**overrides) -> MagicMock:
    post = MagicMock()
    post.id = overrides.get("id", "ig_post_1")
    post.caption = overrides.get("caption", "Instagram caption")
    post.username = overrides.get("username", "igposter")
    post.like_count = overrides.get("like_count", 100)
    post.comment_count = overrides.get("comment_count", 20)
    post.reshare_count = overrides.get("reshare_count", 5)
    post.video_play_count = overrides.get("video_play_count", 3000)
    post.image_url = overrides.get("image_url", "https://img.example.com/post.jpg")
    post.video_url = overrides.get("video_url", None)
    post.media_type = overrides.get("media_type", "image")
    post.location = overrides.get("location", "Brooklyn, NY")
    post.created_at = overrides.get("created_at", datetime(2025, 2, 14))
    return post


def make_reddit_post(**overrides) -> MagicMock:
    post = MagicMock()
    post.id = overrides.get("id", "rd_post_1")
    post.title = overrides.get("title", "Reddit Title")
    post.selftext = overrides.get("selftext", "Post body text")
    post.author_username = overrides.get("author_username", "rdauthor")
    post.subreddit_name = overrides.get("subreddit_name", "r/test")
    post.score = overrides.get("score", 150)
    post.upvotes = overrides.get("upvotes", 180)
    post.downvotes = overrides.get("downvotes", 30)
    post.upvote_ratio = overrides.get("upvote_ratio", 0.85)
    post.comments_count = overrides.get("comments_count", 45)
    post.is_video = overrides.get("is_video", False)
    post.permalink = overrides.get("permalink", "/r/test/comments/abc123/reddit_title")
    post.created_at = overrides.get("created_at", datetime(2025, 3, 1))
    return post


def make_twitter_comment(**overrides) -> MagicMock:
    comment = MagicMock()
    comment.id = overrides.get("id", "tc_1")
    comment.text = overrides.get("text", "A reply")
    comment.author_username = overrides.get("author_username", "replier")
    comment.like_count = overrides.get("like_count", 7)
    comment.retweet_count = overrides.get("retweet_count", 1)
    comment.reply_count = overrides.get("reply_count", 0)
    comment.reply_to_tweet_id = overrides.get("reply_to_tweet_id", "tweet_parent")
    comment.conversation_id = overrides.get("conversation_id", "convo_1")
    comment.created_at = overrides.get("created_at", datetime(2025, 1, 11))
    return comment


def make_instagram_comment(**overrides) -> MagicMock:
    comment = MagicMock()
    comment.id = overrides.get("id", "ic_1")
    comment.text = overrides.get("text", "Nice post!")
    comment.parent_post_id = overrides.get("parent_post_id", "ig_post_1")
    comment.parent_post_user_id = overrides.get("parent_post_user_id", "poster_id")
    comment.type = overrides.get("type", "comment")
    comment.parent_comment_id = overrides.get("parent_comment_id", None)
    comment.child_comment_count = overrides.get("child_comment_count", 0)
    comment.user_id = overrides.get("user_id", "commenter_id")
    comment.username = overrides.get("username", "igcommenter")
    comment.full_name = overrides.get("full_name", "IG Commenter")
    comment.like_count = overrides.get("like_count", 3)
    comment.status = overrides.get("status", "active")
    comment.is_spam = overrides.get("is_spam", False)
    comment.created_at = overrides.get("created_at", datetime(2025, 2, 15))
    return comment


def make_reddit_comment(**overrides) -> MagicMock:
    comment = MagicMock()
    comment.id = overrides.get("id", "rc_1")
    comment.body = overrides.get("body", "A reddit comment")
    comment.parent_post_id = overrides.get("parent_post_id", "rd_post_1")
    comment.parent_id = overrides.get("parent_id", "t3_rd_post_1")
    comment.author_id = overrides.get("author_id", "author_rd_1")
    comment.author_username = overrides.get("author_username", "rdcommenter")
    comment.post_subreddit_name = overrides.get("post_subreddit_name", "r/test")
    comment.score = overrides.get("score", 25)
    comment.upvotes = overrides.get("upvotes", 30)
    comment.downvotes = overrides.get("downvotes", 5)
    comment.controversiality = overrides.get("controversiality", 0)
    comment.depth = overrides.get("depth", 0)
    comment.is_submitter = overrides.get("is_submitter", False)
    comment.stickied = overrides.get("stickied", False)
    comment.collapsed = overrides.get("collapsed", False)
    comment.distinguished = overrides.get("distinguished", None)
    comment.created_at = overrides.get("created_at", datetime(2025, 3, 2))
    return comment


def make_subreddit(**overrides) -> MagicMock:
    sub = MagicMock()
    sub.display_name = overrides.get("display_name", "test")
    sub.title = overrides.get("title", "Test Subreddit")
    sub.public_description = overrides.get("public_description", "A test subreddit")
    sub.description = overrides.get("description", "Full description of test subreddit")
    sub.subscribers_count = overrides.get("subscribers_count", 50_000)
    sub.active_user_count = overrides.get("active_user_count", 1200)
    sub.subreddit_type = overrides.get("subreddit_type", "public")
    sub.over18 = overrides.get("over18", False)
    sub.lang = overrides.get("lang", "en")
    sub.url = overrides.get("url", "/r/test")
    sub.subreddit_url = overrides.get("subreddit_url", "https://reddit.com/r/test")
    sub.icon_img = overrides.get("icon_img", "https://img.example.com/icon.png")
    sub.agg_relevance = overrides.get("agg_relevance", 0.9)
    sub.relevant_posts_count = overrides.get("relevant_posts_count", 30)
    sub.relevant_posts_upvotes_sum = overrides.get("relevant_posts_upvotes_sum", 5000)
    sub.relevant_posts_comments_count_sum = overrides.get("relevant_posts_comments_count_sum", 800)
    return sub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_xpoz_client():
    """Create a mock AsyncXpozClient with twitter/instagram/reddit namespaces."""
    client = AsyncMock()
    client.twitter = AsyncMock()
    client.instagram = AsyncMock()
    client.reddit = AsyncMock()
    return client


@pytest.fixture
def mock_settings():
    """Create a minimal MonitoringSettings mock."""
    settings = MagicMock(spec=MonitoringSettings)
    settings.xpoz_api_key = MagicMock()
    settings.xpoz_api_key.get_secret_value.return_value = "test-api-key"
    settings.adapter_concurrency = 3
    settings.adapter_timeout_seconds = 30.0
    settings.circuit_breaker_threshold = 3
    settings.circuit_breaker_reset_seconds = 60.0
    return settings


@pytest.fixture
async def adapter(mock_xpoz_client, mock_settings):
    """Create XpozAdapter with mocked client (Twitter default)."""
    with patch("src.monitoring.adapters.xpoz.AsyncXpozClient"):
        a = XpozAdapter(settings=mock_settings, default_source=DataSource.TWITTER)
        a._client = mock_xpoz_client
        yield a


@pytest.fixture
async def adapter_instagram(mock_xpoz_client, mock_settings):
    """Create XpozAdapter with Instagram as default source."""
    with patch("src.monitoring.adapters.xpoz.AsyncXpozClient"):
        a = XpozAdapter(settings=mock_settings, default_source=DataSource.INSTAGRAM)
        a._client = mock_xpoz_client
        yield a


@pytest.fixture
async def adapter_reddit(mock_xpoz_client, mock_settings):
    """Create XpozAdapter with Reddit as default source."""
    with patch("src.monitoring.adapters.xpoz.AsyncXpozClient"):
        a = XpozAdapter(settings=mock_settings, default_source=DataSource.REDDIT)
        a._client = mock_xpoz_client
        yield a


# ===========================================================================
# 1. TestSearchUsersByKeywords
# ===========================================================================

class TestSearchUsersByKeywords:
    """Test search_users_by_keywords across all platforms."""

    async def test_twitter_search_calls_correct_method(self, adapter, mock_xpoz_client):
        users = [make_twitter_user(), make_twitter_user(id="tw_999", username="other")]
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated(users)

        result = await adapter.search_users_by_keywords(
            "AI startups", platform=DataSource.TWITTER
        )

        mock_xpoz_client.twitter.get_users_by_keywords.assert_called_once()
        call_args = mock_xpoz_client.twitter.get_users_by_keywords.call_args
        assert call_args[0][0] == "AI startups"
        assert "fields" in call_args[1]
        assert len(result) == 2
        assert all(isinstance(u, XpozUser) for u in result)

    async def test_twitter_search_xpoz_user_fields(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(
            id="tw_42", username="alice", name="Alice W",
            description="Data scientist", location="London",
            followers_count=8000, following_count=500,
            tweet_count=3000, verified=True,
            agg_relevance=0.92, relevant_tweets_count=55,
        )
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("ML", platform=DataSource.TWITTER)

        u = result[0]
        assert u.platform == DataSource.TWITTER
        assert u.user_id == "tw_42"
        assert u.username == "alice"
        assert u.display_name == "Alice W"
        assert u.bio == "Data scientist"
        assert u.follower_count == 8000
        assert u.following_count == 500
        assert u.post_count == 3000
        assert u.is_verified is True
        assert u.relevance_score == 0.92
        assert u.relevant_posts_count == 55
        assert u.metadata.get("location") == "London"

    async def test_twitter_search_engagement_sum(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(
            relevant_tweets_likes_sum=100,
            relevant_tweets_quotes_sum=20,
            relevant_tweets_replies_sum=30,
            relevant_tweets_retweets_sum=50,
        )
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.TWITTER)
        assert result[0].relevant_engagement_sum == 200  # 100+20+30+50

    async def test_instagram_search(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user()
        mock_xpoz_client.instagram.get_users_by_keywords.return_value = make_paginated([ig_user])

        result = await adapter.search_users_by_keywords("fashion", platform=DataSource.INSTAGRAM)

        mock_xpoz_client.instagram.get_users_by_keywords.assert_called_once()
        assert len(result) == 1
        u = result[0]
        assert u.platform == DataSource.INSTAGRAM
        assert u.username == "instauser"
        assert u.display_name == "Insta User"
        assert u.bio == "IG bio"
        assert u.follower_count == 10_000
        assert u.post_count == 500
        assert u.is_inauthentic is None  # Instagram has no bot detection
        assert u.inauthentic_prob_score is None

    async def test_instagram_engagement_sum(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user(
            relevant_posts_likes_sum=2000,
            relevant_posts_comments_sum=300,
            relevant_posts_reshares_sum=100,
        )
        mock_xpoz_client.instagram.get_users_by_keywords.return_value = make_paginated([ig_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.INSTAGRAM)
        assert result[0].relevant_engagement_sum == 2400  # 2000+300+100

    async def test_instagram_metadata_private_and_external_url(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user(
            is_private=True,
            external_url="https://mysite.com",
            profile_url="https://instagram.com/instauser",
            relevant_posts_video_plays_sum=50_000,
        )
        mock_xpoz_client.instagram.get_users_by_keywords.return_value = make_paginated([ig_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.INSTAGRAM)
        meta = result[0].metadata
        assert meta["is_private"] is True
        assert meta["external_url"] == "https://mysite.com"
        assert meta["profile_url"] == "https://instagram.com/instauser"
        assert meta["relevant_video_plays"] == 50_000

    async def test_reddit_search_with_subreddit_filter(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user()
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords(
            "python", platform=DataSource.REDDIT, subreddit="r/programming"
        )

        call_kwargs = mock_xpoz_client.reddit.get_users_by_keywords.call_args[1]
        assert call_kwargs["subreddit"] == "r/programming"
        assert len(result) == 1
        assert result[0].platform == DataSource.REDDIT
        assert result[0].username == "redditor"

    async def test_reddit_user_fields(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user(
            id="rd_42", username="pythondev",
            has_verified_email=True, is_gold=True, is_mod=True,
            total_karma=50_000, link_karma=30_000, comment_karma=20_000,
        )
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords("python", platform=DataSource.REDDIT)
        u = result[0]
        assert u.user_id == "rd_42"
        assert u.is_verified is True  # has_verified_email maps to is_verified
        assert u.display_name is None  # Reddit has no display_name
        assert u.follower_count is None
        assert u.following_count is None
        assert u.post_count is None
        assert u.metadata["total_karma"] == 50_000
        assert u.metadata["link_karma"] == 30_000
        assert u.metadata["is_gold"] is True
        assert u.metadata["is_mod"] is True

    async def test_reddit_engagement_sum(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user(
            relevant_posts_upvotes_sum=1500,
            relevant_posts_comments_count_sum=200,
        )
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.REDDIT)
        assert result[0].relevant_engagement_sum == 1700  # 1500+200

    async def test_returns_empty_on_not_found(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = None
        # _safe_xpoz_call returns None for NotFoundError, but here we simulate
        # the result being None directly (safe_xpoz_call returns None)
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.search_users_by_keywords("nope", platform=DataSource.TWITTER)
        assert result == []

    async def test_respects_limit(self, adapter, mock_xpoz_client):
        users = [make_twitter_user(id=f"tw_{i}") for i in range(10)]
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated(users)

        result = await adapter.search_users_by_keywords("test", platform=DataSource.TWITTER, limit=3)
        assert len(result) == 3

    async def test_twitter_language_filter_passed(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([])

        await adapter.search_users_by_keywords(
            "test", platform=DataSource.TWITTER, language="es"
        )

        call_kwargs = mock_xpoz_client.twitter.get_users_by_keywords.call_args[1]
        assert call_kwargs["language"] == "es"

    async def test_date_filters_passed(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 6, 1)

        await adapter.search_users_by_keywords(
            "test", platform=DataSource.TWITTER, start_date=start, end_date=end
        )

        call_kwargs = mock_xpoz_client.twitter.get_users_by_keywords.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end


# ===========================================================================
# 2. TestGetUserProfile
# ===========================================================================

class TestGetUserProfile:
    """Test get_user_profile across platforms."""

    async def test_twitter_profile(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(
            is_inauthentic=True, is_inauthentic_prob_score=0.87,
        )
        mock_xpoz_client.twitter.get_user.return_value = tw_user

        result = await adapter.get_user_profile("testuser", platform=DataSource.TWITTER)

        mock_xpoz_client.twitter.get_user.assert_called_once()
        call_args = mock_xpoz_client.twitter.get_user.call_args
        assert call_args[0][0] == "testuser"
        assert call_args[1]["identifier_type"] == "username"
        assert isinstance(result, XpozUser)
        assert result.platform == DataSource.TWITTER
        assert result.is_inauthentic is True
        assert result.inauthentic_prob_score == 0.87

    async def test_twitter_profile_by_id(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user()
        mock_xpoz_client.twitter.get_user.return_value = tw_user

        await adapter.get_user_profile("12345", platform=DataSource.TWITTER, identifier_type="id")

        call_kwargs = mock_xpoz_client.twitter.get_user.call_args[1]
        assert call_kwargs["identifier_type"] == "id"

    async def test_instagram_profile(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user()
        mock_xpoz_client.instagram.get_user.return_value = ig_user

        result = await adapter.get_user_profile("instauser", platform=DataSource.INSTAGRAM)

        assert isinstance(result, XpozUser)
        assert result.platform == DataSource.INSTAGRAM
        assert result.display_name == "Insta User"
        assert result.profile_image_url == "https://img.example.com/ig.jpg"

    async def test_reddit_profile_no_identifier_type(self, adapter, mock_xpoz_client):
        """Reddit get_user takes username only (no identifier_type param)."""
        rd_user = make_reddit_user(has_verified_email=True)
        mock_xpoz_client.reddit.get_user.return_value = rd_user

        result = await adapter.get_user_profile("redditor", platform=DataSource.REDDIT)

        # Reddit does NOT pass identifier_type
        call_args = mock_xpoz_client.reddit.get_user.call_args
        assert "identifier_type" not in call_args[1]
        assert result.is_verified is True  # has_verified_email -> is_verified

    async def test_not_found_returns_none(self, adapter, mock_xpoz_client):
        """NotFoundError is caught by _safe_xpoz_call and returns None."""
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_user_profile("nobody", platform=DataSource.TWITTER)
        assert result is None


# ===========================================================================
# 3. TestGetUserConnections
# ===========================================================================

class TestGetUserConnections:
    """Test get_user_connections — Twitter/Instagram only."""

    async def test_twitter_followers(self, adapter, mock_xpoz_client):
        users = [make_twitter_user(id=f"tw_{i}") for i in range(3)]
        mock_xpoz_client.twitter.get_user_connections.return_value = make_paginated(users)

        result = await adapter.get_user_connections(
            "testuser", platform=DataSource.TWITTER, connection_type="followers"
        )

        mock_xpoz_client.twitter.get_user_connections.assert_called_once_with(
            "testuser", "followers", fields=mock_xpoz_client.twitter.get_user_connections.call_args[1]["fields"],
        )
        assert len(result) == 3
        assert all(isinstance(u, XpozUser) for u in result)

    async def test_instagram_following(self, adapter, mock_xpoz_client):
        users = [make_instagram_user()]
        mock_xpoz_client.instagram.get_user_connections.return_value = make_paginated(users)

        result = await adapter.get_user_connections(
            "instauser", platform=DataSource.INSTAGRAM, connection_type="following"
        )

        assert len(result) == 1
        assert result[0].platform == DataSource.INSTAGRAM

    async def test_reddit_raises_error(self, adapter, mock_xpoz_client):
        with pytest.raises(MentionFetchError, match="Reddit does not support user connections"):
            await adapter.get_user_connections("redditor", platform=DataSource.REDDIT)

    async def test_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_user_connections("nobody", platform=DataSource.TWITTER)
        assert result == []

    async def test_respects_limit(self, adapter, mock_xpoz_client):
        users = [make_twitter_user(id=f"tw_{i}") for i in range(10)]
        mock_xpoz_client.twitter.get_user_connections.return_value = make_paginated(users)

        result = await adapter.get_user_connections(
            "testuser", platform=DataSource.TWITTER, limit=5
        )
        assert len(result) == 5


# ===========================================================================
# 4. TestGetPostsById
# ===========================================================================

class TestGetPostsById:
    """Test get_posts_by_ids — Twitter + Instagram only."""

    async def test_twitter_returns_raw_mentions(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post(id="t1"), make_twitter_post(id="t2")]
        mock_xpoz_client.twitter.get_posts_by_ids.return_value = posts

        result = await adapter.get_posts_by_ids(["t1", "t2"], platform=DataSource.TWITTER)

        mock_xpoz_client.twitter.get_posts_by_ids.assert_called_once()
        assert len(result) == 2
        assert all(isinstance(m, RawMention) for m in result)
        assert result[0].source == DataSource.TWITTER
        assert result[0].source_id == "t1"

    async def test_instagram_returns_raw_mentions(self, adapter, mock_xpoz_client):
        posts = [make_instagram_post()]
        mock_xpoz_client.instagram.get_posts_by_ids.return_value = posts

        result = await adapter.get_posts_by_ids(["ig_post_1"], platform=DataSource.INSTAGRAM)

        assert len(result) == 1
        assert result[0].source == DataSource.INSTAGRAM
        assert result[0].content == "Instagram caption"

    async def test_reddit_raises_error(self, adapter, mock_xpoz_client):
        with pytest.raises(MentionFetchError, match="Reddit get_posts_by_ids not supported"):
            await adapter.get_posts_by_ids(["rd1"], platform=DataSource.REDDIT)

    async def test_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_posts_by_ids(["missing"], platform=DataSource.TWITTER)
        assert result == []


# ===========================================================================
# 5. TestGetPostsByAuthor
# ===========================================================================

class TestGetPostsByAuthor:
    """Test get_posts_by_author — Twitter + Instagram only."""

    async def test_twitter_uses_get_posts_by_author(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post()]
        mock_xpoz_client.twitter.get_posts_by_author.return_value = make_paginated(posts)

        result = await adapter.get_posts_by_author("elonmusk", platform=DataSource.TWITTER)

        mock_xpoz_client.twitter.get_posts_by_author.assert_called_once()
        call_args = mock_xpoz_client.twitter.get_posts_by_author.call_args
        assert call_args[0][0] == "elonmusk"
        assert len(result) == 1
        assert result[0].source == DataSource.TWITTER

    async def test_instagram_uses_get_posts_by_user(self, adapter, mock_xpoz_client):
        posts = [make_instagram_post()]
        mock_xpoz_client.instagram.get_posts_by_user.return_value = make_paginated(posts)

        result = await adapter.get_posts_by_author("igcreator", platform=DataSource.INSTAGRAM)

        mock_xpoz_client.instagram.get_posts_by_user.assert_called_once()
        assert len(result) == 1
        assert result[0].source == DataSource.INSTAGRAM

    async def test_twitter_date_filters_passed(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.get_posts_by_author.return_value = make_paginated([])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 6, 1)

        await adapter.get_posts_by_author(
            "user", platform=DataSource.TWITTER, start_date=start, end_date=end
        )

        call_kwargs = mock_xpoz_client.twitter.get_posts_by_author.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end

    async def test_reddit_raises_error(self, adapter, mock_xpoz_client):
        with pytest.raises(MentionFetchError, match="Reddit get_posts_by_author not supported"):
            await adapter.get_posts_by_author("redditor", platform=DataSource.REDDIT)

    async def test_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_posts_by_author("nobody", platform=DataSource.TWITTER)
        assert result == []

    async def test_respects_limit(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post(id=f"t_{i}") for i in range(10)]
        mock_xpoz_client.twitter.get_posts_by_author.return_value = make_paginated(posts)

        result = await adapter.get_posts_by_author(
            "user", platform=DataSource.TWITTER, limit=4
        )
        assert len(result) == 4


# ===========================================================================
# 6. TestViralTracking
# ===========================================================================

class TestViralTracking:
    """Test get_retweets and get_quotes — Twitter only."""

    async def test_get_retweets(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post(id="rt_1", is_retweet=True)]
        mock_xpoz_client.twitter.get_retweets.return_value = make_paginated(posts)

        result = await adapter.get_retweets("original_tweet_id")

        mock_xpoz_client.twitter.get_retweets.assert_called_once()
        assert len(result) == 1
        assert isinstance(result[0], RawMention)
        assert result[0].source == DataSource.TWITTER

    async def test_get_quotes(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post(id="qt_1"), make_twitter_post(id="qt_2")]
        mock_xpoz_client.twitter.get_quotes.return_value = make_paginated(posts)

        result = await adapter.get_quotes("original_tweet_id")

        mock_xpoz_client.twitter.get_quotes.assert_called_once()
        assert len(result) == 2

    async def test_retweets_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_retweets("nonexistent")
        assert result == []

    async def test_quotes_respects_limit(self, adapter, mock_xpoz_client):
        posts = [make_twitter_post(id=f"qt_{i}") for i in range(10)]
        mock_xpoz_client.twitter.get_quotes.return_value = make_paginated(posts)

        result = await adapter.get_quotes("tweet_id", limit=3)
        assert len(result) == 3


# ===========================================================================
# 7. TestPostComments
# ===========================================================================

class TestPostComments:
    """Test get_post_comments across platforms."""

    async def test_twitter_comments(self, adapter, mock_xpoz_client):
        comments = [
            make_twitter_comment(id="tc_1", text="Reply 1"),
            make_twitter_comment(id="tc_2", text="Reply 2"),
        ]
        mock_xpoz_client.twitter.get_comments.return_value = make_paginated(comments)

        result = await adapter.get_post_comments("tweet_1", platform=DataSource.TWITTER)

        assert len(result) == 2
        assert all(isinstance(c, XpozComment) for c in result)
        c = result[0]
        assert c.platform == DataSource.TWITTER
        assert c.comment_id == "tc_1"
        assert c.content == "Reply 1"
        assert c.post_id == "tweet_parent"
        assert c.author_username == "replier"
        assert c.is_spam is None
        assert c.controversiality is None

    async def test_twitter_comment_metadata(self, adapter, mock_xpoz_client):
        comment = make_twitter_comment(retweet_count=5, reply_count=2)
        mock_xpoz_client.twitter.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("tweet_1", platform=DataSource.TWITTER)
        assert result[0].metadata["retweet_count"] == 5
        assert result[0].metadata["reply_count"] == 2

    async def test_twitter_comment_fallback_to_conversation_id(self, adapter, mock_xpoz_client):
        """When reply_to_tweet_id is None, post_id should use conversation_id."""
        comment = make_twitter_comment(reply_to_tweet_id=None, conversation_id="convo_99")
        mock_xpoz_client.twitter.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("tweet_1", platform=DataSource.TWITTER)
        assert result[0].post_id == "convo_99"

    async def test_instagram_comments_with_spam(self, adapter, mock_xpoz_client):
        comment = make_instagram_comment(is_spam=True, text="Buy followers!")
        mock_xpoz_client.instagram.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("ig_post_1", platform=DataSource.INSTAGRAM)

        assert len(result) == 1
        c = result[0]
        assert c.platform == DataSource.INSTAGRAM
        assert c.is_spam is True
        assert c.author_username == "igcommenter"
        assert c.content == "Buy followers!"

    async def test_instagram_comment_metadata(self, adapter, mock_xpoz_client):
        comment = make_instagram_comment(
            type="reply",
            parent_comment_id="parent_ic",
            child_comment_count=3,
            full_name="Full Name",
        )
        mock_xpoz_client.instagram.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("ig_post_1", platform=DataSource.INSTAGRAM)
        meta = result[0].metadata
        assert meta["type"] == "reply"
        assert meta["parent_comment_id"] == "parent_ic"
        assert meta["child_comment_count"] == 3
        assert meta["full_name"] == "Full Name"

    async def test_reddit_comments(self, adapter, mock_xpoz_client):
        comments = [make_reddit_comment(body="Great post!")]
        post_with_comments = MagicMock()
        post_with_comments.comments = comments
        mock_xpoz_client.reddit.get_post_with_comments.return_value = post_with_comments

        result = await adapter.get_post_comments("rd_post_1", platform=DataSource.REDDIT)

        assert len(result) == 1
        c = result[0]
        assert c.platform == DataSource.REDDIT
        assert c.content == "Great post!"
        assert c.author_username == "rdcommenter"

    async def test_reddit_comment_metadata(self, adapter, mock_xpoz_client):
        comment = make_reddit_comment(
            score=50, upvotes=60, downvotes=10, post_subreddit_name="r/python"
        )
        post_with_comments = MagicMock()
        post_with_comments.comments = [comment]
        mock_xpoz_client.reddit.get_post_with_comments.return_value = post_with_comments

        result = await adapter.get_post_comments("rd_post_1", platform=DataSource.REDDIT)
        meta = result[0].metadata
        assert meta["score"] == 50
        assert meta["upvotes"] == 60
        assert meta["downvotes"] == 10
        assert meta["subreddit"] == "r/python"

    async def test_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_post_comments("missing", platform=DataSource.TWITTER)
        assert result == []


# ===========================================================================
# 8. TestRedditCommunity
# ===========================================================================

class TestRedditCommunity:
    """Test Reddit-specific subreddit methods."""

    async def test_search_subreddits(self, adapter, mock_xpoz_client):
        subs = [make_subreddit(display_name="python"), make_subreddit(display_name="programming")]
        # search_subreddits returns a list (not paginated)
        mock_xpoz_client.reddit.search_subreddits.return_value = subs

        result = await adapter.search_subreddits("programming")

        mock_xpoz_client.reddit.search_subreddits.assert_called_once()
        assert len(result) == 2
        assert all(isinstance(s, XpozSubreddit) for s in result)
        assert result[0].name == "python"
        assert result[1].name == "programming"

    async def test_search_subreddits_fields(self, adapter, mock_xpoz_client):
        sub = make_subreddit(
            display_name="datascience",
            title="Data Science",
            public_description="DS community",
            subscribers_count=800_000,
            active_user_count=3000,
            subreddit_type="public",
            over18=False,
            lang="en",
            subreddit_url="https://reddit.com/r/datascience",
            agg_relevance=0.95,
            relevant_posts_count=120,
        )
        mock_xpoz_client.reddit.search_subreddits.return_value = [sub]

        result = await adapter.search_subreddits("data science")
        s = result[0]
        assert s.name == "datascience"
        assert s.title == "Data Science"
        assert s.description == "DS community"
        assert s.subscribers_count == 800_000
        assert s.active_users_count == 3000
        assert s.subreddit_type == "public"
        assert s.over18 is False
        assert s.language == "en"
        assert s.url == "https://reddit.com/r/datascience"
        assert s.relevance_score == 0.95
        assert s.relevant_posts_count == 120

    async def test_subreddit_metadata(self, adapter, mock_xpoz_client):
        sub = make_subreddit(
            icon_img="https://icon.example.com/icon.png",
            relevant_posts_upvotes_sum=10_000,
            relevant_posts_comments_count_sum=2000,
        )
        mock_xpoz_client.reddit.search_subreddits.return_value = [sub]

        result = await adapter.search_subreddits("test")
        meta = result[0].metadata
        assert meta["icon_img"] == "https://icon.example.com/icon.png"
        assert meta["relevant_posts_upvotes_sum"] == 10_000
        assert meta["relevant_posts_comments_count_sum"] == 2000

    async def test_get_subreddit_with_posts(self, adapter, mock_xpoz_client):
        sub_obj = make_subreddit(display_name="python")
        posts = [make_reddit_post(id="rd_p1"), make_reddit_post(id="rd_p2")]
        result_obj = MagicMock()
        result_obj.subreddit = sub_obj
        result_obj.posts = posts
        mock_xpoz_client.reddit.get_subreddit_with_posts.return_value = result_obj

        sub, post_list = await adapter.get_subreddit_with_posts("python")

        assert isinstance(sub, XpozSubreddit)
        assert sub.name == "python"
        assert len(post_list) == 2
        assert all(isinstance(p, RawMention) for p in post_list)
        assert post_list[0].source == DataSource.REDDIT

    async def test_get_subreddit_with_posts_not_found(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            with pytest.raises(MentionFetchError, match="not found"):
                await adapter.get_subreddit_with_posts("nonexistent")

    async def test_get_subreddit_with_posts_no_subreddit_data(self, adapter, mock_xpoz_client):
        result_obj = MagicMock()
        result_obj.subreddit = None
        result_obj.posts = []
        mock_xpoz_client.reddit.get_subreddit_with_posts.return_value = result_obj

        with pytest.raises(MentionFetchError, match="no subreddit data"):
            await adapter.get_subreddit_with_posts("broken")

    async def test_get_subreddits_by_keywords(self, adapter, mock_xpoz_client):
        subs = [make_subreddit(display_name="machinelearning")]
        mock_xpoz_client.reddit.get_subreddits_by_keywords.return_value = make_paginated(subs)

        result = await adapter.get_subreddits_by_keywords("ML")

        assert len(result) == 1
        assert result[0].name == "machinelearning"

    async def test_get_subreddits_by_keywords_date_filters(self, adapter, mock_xpoz_client):
        mock_xpoz_client.reddit.get_subreddits_by_keywords.return_value = make_paginated([])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 6, 1)

        await adapter.get_subreddits_by_keywords("test", start_date=start, end_date=end)

        call_kwargs = mock_xpoz_client.reddit.get_subreddits_by_keywords.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end

    async def test_get_subreddits_by_keywords_not_found(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_subreddits_by_keywords("obscure")
        assert result == []


# ===========================================================================
# 9. TestCountPosts
# ===========================================================================

class TestCountPosts:
    """Test count_posts — Twitter only."""

    async def test_returns_integer_count(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.count_posts.return_value = 42

        result = await adapter.count_posts("AI agents")

        mock_xpoz_client.twitter.count_posts.assert_called_once()
        assert result == 42

    async def test_with_date_filters(self, adapter, mock_xpoz_client):
        mock_xpoz_client.twitter.count_posts.return_value = 100
        start = datetime(2025, 1, 1)
        end = datetime(2025, 3, 1)

        result = await adapter.count_posts("test", start_date=start, end_date=end)

        call_kwargs = mock_xpoz_client.twitter.count_posts.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end
        assert result == 100

    async def test_not_found_returns_zero(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.count_posts("nonexistent")
        assert result == 0


# ===========================================================================
# 10. TestSafeXpozCall
# ===========================================================================

class TestSafeXpozCall:
    """Test _safe_xpoz_call resilience wrapper."""

    async def test_timeout_error_raises_mention_fetch_error(self, adapter):
        from xpoz import OperationTimeoutError

        err = OperationTimeoutError.__new__(OperationTimeoutError)
        err.elapsed_seconds = 25.0

        async def boom():
            raise err

        with pytest.raises(MentionFetchError, match="Xpoz timeout after 25.0s"):
            await adapter._safe_xpoz_call(boom())

    async def test_authentication_error_reraises(self, adapter):
        from xpoz import AuthenticationError

        async def boom():
            raise AuthenticationError("bad key")

        with pytest.raises(AuthenticationError):
            await adapter._safe_xpoz_call(boom())

    async def test_not_found_error_returns_none(self, adapter):
        from xpoz import NotFoundError

        async def boom():
            raise NotFoundError("gone")

        result = await adapter._safe_xpoz_call(boom())
        assert result is None

    async def test_transient_xpoz_error_propagates(self, adapter):
        from xpoz import XpozError

        async def boom():
            raise XpozError("server error")

        with pytest.raises(XpozError):
            await adapter._safe_xpoz_call(boom())

    async def test_success_records_success(self, adapter):
        async def ok():
            return "data"

        result = await adapter._safe_xpoz_call(ok())
        assert result == "data"
        # Circuit breaker should be closed after success
        assert adapter._xpoz_cb.allow_request() is True

    async def test_circuit_breaker_open_raises(self, adapter):
        """When CB is open, calls are rejected immediately."""
        adapter._xpoz_cb._state = __import__("src.common.circuit_breaker", fromlist=["CircuitState"]).CircuitState.OPEN
        adapter._xpoz_cb._last_failure_time = __import__("time").monotonic()

        async def ok():
            return "data"

        with pytest.raises(MentionFetchError, match="circuit breaker open"):
            await adapter._safe_xpoz_call(ok())

    async def test_timeout_records_failure(self, adapter):
        from xpoz import OperationTimeoutError

        err = OperationTimeoutError.__new__(OperationTimeoutError)
        err.elapsed_seconds = 30.0

        initial_failures = adapter._xpoz_cb._failure_count

        async def boom():
            raise err

        with pytest.raises(MentionFetchError):
            await adapter._safe_xpoz_call(boom())

        assert adapter._xpoz_cb._failure_count > initial_failures

    async def test_not_found_records_success(self, adapter):
        """NotFoundError is not a failure — records success on circuit breaker."""
        from xpoz import NotFoundError

        async def boom():
            raise NotFoundError("gone")

        await adapter._safe_xpoz_call(boom())
        assert adapter._xpoz_cb._failure_count == 0


# ===========================================================================
# 11. TestBotDetection
# ===========================================================================

class TestBotDetection:
    """Test bot detection fields on Twitter users."""

    async def test_inauthentic_user(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(
            is_inauthentic=True, is_inauthentic_prob_score=0.87,
        )
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("spam", platform=DataSource.TWITTER)
        u = result[0]
        assert u.is_inauthentic is True
        assert u.inauthentic_prob_score == 0.87

    async def test_authentic_user(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(
            is_inauthentic=False, is_inauthentic_prob_score=0.05,
        )
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("legit", platform=DataSource.TWITTER)
        u = result[0]
        assert u.is_inauthentic is False
        assert u.inauthentic_prob_score == 0.05

    async def test_no_bot_detection_on_instagram(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user()
        mock_xpoz_client.instagram.get_users_by_keywords.return_value = make_paginated([ig_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.INSTAGRAM)
        assert result[0].is_inauthentic is None
        assert result[0].inauthentic_prob_score is None

    async def test_no_bot_detection_on_reddit(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user()
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.REDDIT)
        assert result[0].is_inauthentic is None
        assert result[0].inauthentic_prob_score is None


# ===========================================================================
# 12. TestRedditDiscussionQuality
# ===========================================================================

class TestRedditDiscussionQuality:
    """Test Reddit-specific comment fields: controversiality, depth, distinguished."""

    async def test_controversial_deep_mod_comment(self, adapter, mock_xpoz_client):
        comment = make_reddit_comment(
            controversiality=1, depth=3, distinguished="moderator",
            is_submitter=True,
        )
        post_with_comments = MagicMock()
        post_with_comments.comments = [comment]
        mock_xpoz_client.reddit.get_post_with_comments.return_value = post_with_comments

        result = await adapter.get_post_comments("rd_post_1", platform=DataSource.REDDIT)
        c = result[0]
        assert c.controversiality == 1
        assert c.depth == 3
        assert c.distinguished == "moderator"
        assert c.is_submitter is True

    async def test_normal_top_level_comment(self, adapter, mock_xpoz_client):
        comment = make_reddit_comment(
            controversiality=0, depth=0, distinguished=None,
            is_submitter=False,
        )
        post_with_comments = MagicMock()
        post_with_comments.comments = [comment]
        mock_xpoz_client.reddit.get_post_with_comments.return_value = post_with_comments

        result = await adapter.get_post_comments("rd_post_1", platform=DataSource.REDDIT)
        c = result[0]
        assert c.controversiality == 0
        assert c.depth == 0
        assert c.distinguished is None
        assert c.is_submitter is False

    async def test_twitter_comment_has_no_discussion_quality_fields(self, adapter, mock_xpoz_client):
        comment = make_twitter_comment()
        mock_xpoz_client.twitter.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("tweet_1", platform=DataSource.TWITTER)
        c = result[0]
        assert c.controversiality is None
        assert c.depth is None
        assert c.distinguished is None
        assert c.is_submitter is None

    async def test_instagram_comment_has_no_discussion_quality_fields(self, adapter, mock_xpoz_client):
        comment = make_instagram_comment()
        mock_xpoz_client.instagram.get_comments.return_value = make_paginated([comment])

        result = await adapter.get_post_comments("ig_post_1", platform=DataSource.INSTAGRAM)
        c = result[0]
        assert c.controversiality is None
        assert c.depth is None
        assert c.distinguished is None
        assert c.is_submitter is None


# ===========================================================================
# 13. TestEnhancedSearch
# ===========================================================================

class TestEnhancedSearch:
    """Test _search() passes through filters correctly."""

    async def test_twitter_search_with_all_filters(self, adapter, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = []
        paginated.has_next_page.return_value = False
        mock_xpoz_client.twitter.search_posts.return_value = paginated

        start = datetime(2025, 1, 1)
        end = datetime(2025, 6, 1)

        await adapter._search(
            "test query",
            start_date=start,
            end_date=end,
            language="fr",
            author_username="someone",
        )

        call_kwargs = mock_xpoz_client.twitter.search_posts.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end
        assert call_kwargs["language"] == "fr"
        assert call_kwargs["author_username"] == "someone"

    async def test_instagram_search_date_filters(self, adapter_instagram, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = []
        paginated.has_next_page.return_value = False
        mock_xpoz_client.instagram.search_posts.return_value = paginated

        start = datetime(2025, 2, 1)
        end = datetime(2025, 5, 1)

        await adapter_instagram._search("beauty", start_date=start, end_date=end)

        call_kwargs = mock_xpoz_client.instagram.search_posts.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end

    async def test_reddit_search_subreddit_filter(self, adapter_reddit, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = []
        paginated.has_next_page.return_value = False
        mock_xpoz_client.reddit.search_posts.return_value = paginated

        await adapter_reddit._search("python", subreddit="r/programming")

        call_kwargs = mock_xpoz_client.reddit.search_posts.call_args[1]
        assert call_kwargs["subreddit"] == "r/programming"

    async def test_reddit_search_date_filters(self, adapter_reddit, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = []
        paginated.has_next_page.return_value = False
        mock_xpoz_client.reddit.search_posts.return_value = paginated

        start = datetime(2025, 3, 1)
        end = datetime(2025, 4, 1)

        await adapter_reddit._search("test", start_date=start, end_date=end)

        call_kwargs = mock_xpoz_client.reddit.search_posts.call_args[1]
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end

    async def test_cursor_pagination(self, adapter, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = [make_twitter_post()]
        paginated.has_next_page.return_value = False

        page2 = MagicMock()
        page2.data = [make_twitter_post(id="page2_tweet")]
        paginated.get_page = AsyncMock(return_value=page2)

        mock_xpoz_client.twitter.search_posts.return_value = paginated

        result = await adapter._search("test", cursor="2")

        paginated.get_page.assert_called_once_with(2)

    async def test_invalid_cursor_raises_error(self, adapter, mock_xpoz_client):
        paginated = MagicMock()
        paginated.data = []
        paginated.get_page = AsyncMock(side_effect=ValueError("bad"))
        mock_xpoz_client.twitter.search_posts.return_value = paginated

        with pytest.raises(MentionFetchError, match="Invalid cursor value"):
            await adapter._search("test", cursor="abc")

    async def test_client_not_initialized_raises(self, adapter):
        adapter._client = None

        with pytest.raises(MentionFetchError, match="not initialized"):
            await adapter._search("test")


# ===========================================================================
# Additional coverage: _get_namespace, _map_post, edge cases
# ===========================================================================

class TestGetNamespace:
    """Test _get_namespace helper."""

    async def test_twitter_namespace(self, adapter, mock_xpoz_client):
        ns = adapter._get_namespace(DataSource.TWITTER)
        assert ns is mock_xpoz_client.twitter

    async def test_instagram_namespace(self, adapter, mock_xpoz_client):
        ns = adapter._get_namespace(DataSource.INSTAGRAM)
        assert ns is mock_xpoz_client.instagram

    async def test_reddit_namespace(self, adapter, mock_xpoz_client):
        ns = adapter._get_namespace(DataSource.REDDIT)
        assert ns is mock_xpoz_client.reddit

    async def test_unsupported_platform_raises(self, adapter, mock_xpoz_client):
        with pytest.raises(MentionFetchError, match="Unsupported Xpoz platform"):
            adapter._get_namespace(DataSource.TIKTOK)

    async def test_client_none_raises(self, adapter):
        adapter._client = None
        with pytest.raises(MentionFetchError, match="not initialized"):
            adapter._get_namespace(DataSource.TWITTER)


class TestPostMapping:
    """Test _map_post and platform-specific post mappers."""

    def test_twitter_post_mapping(self, adapter):
        post = make_twitter_post(
            id="tw_p1", text="Hello world", author_username="alice",
            like_count=100, retweet_count=20, reply_count=5,
            impression_count=5000, lang="en", country="US",
            quote_count=3, bookmark_count=1,
            hashtags=["#ai"], mentions=["@bob"],
            media_urls=["https://pic.example.com/1.jpg"],
            region="CA", city="LA",
        )

        result = adapter._map_twitter(post)

        assert isinstance(result, RawMention)
        assert result.source == DataSource.TWITTER
        assert result.source_id == "tw_p1"
        assert result.content == "Hello world"
        assert result.author_handle == "alice"
        assert result.engagement_likes == 100
        assert result.engagement_shares == 20
        assert result.engagement_comments == 5
        assert result.reach_estimate == 5000
        assert result.language == "en"
        assert result.geo_country == "US"
        assert result.metadata["quote_count"] == 3
        assert result.metadata["hashtags"] == ["#ai"]
        assert result.metadata["region"] == "CA"
        assert result.metadata["city"] == "LA"

    def test_instagram_post_mapping(self, adapter):
        post = make_instagram_post(
            id="ig_p1", caption="Beautiful", username="photographer",
            like_count=500, comment_count=30, reshare_count=10,
            video_play_count=8000, image_url="https://img.example.com/photo.jpg",
            video_url="https://vid.example.com/reel.mp4",
            media_type="video", location="Paris",
        )

        result = adapter._map_instagram(post)

        assert result.source == DataSource.INSTAGRAM
        assert result.content == "Beautiful"
        assert result.engagement_likes == 500
        assert result.engagement_shares == 10
        assert result.engagement_comments == 30
        assert result.reach_estimate == 8000
        assert len(result.media_urls) == 2
        assert result.metadata["media_type"] == "video"
        assert result.metadata["city"] == "Paris"

    def test_reddit_post_mapping(self, adapter):
        post = make_reddit_post(
            id="rd_p1", title="TIL", selftext="Something interesting",
            author_username="user42", subreddit_name="r/todayilearned",
            score=1500, upvotes=1700, downvotes=200, upvote_ratio=0.89,
            comments_count=120, is_video=True,
            permalink="/r/todayilearned/comments/xyz/til",
        )

        result = adapter._map_reddit(post)

        assert result.source == DataSource.REDDIT
        assert result.source_id == "rd_p1"
        assert "TIL" in result.content
        assert "Something interesting" in result.content
        assert result.engagement_likes == 1500
        assert result.engagement_comments == 120
        assert result.url == "https://reddit.com/r/todayilearned/comments/xyz/til"
        assert result.metadata["subreddit"] == "r/todayilearned"
        assert result.metadata["media_type"] == "video"
        assert result.metadata["engagement_extra"]["upvotes"] == 1700

    def test_reddit_post_no_selftext(self, adapter):
        post = make_reddit_post(selftext=None)
        result = adapter._map_reddit(post)
        assert result.content == "Reddit Title"

    def test_reddit_post_no_permalink(self, adapter):
        post = make_reddit_post(permalink=None)
        result = adapter._map_reddit(post)
        assert result.url is None

    def test_instagram_post_no_video(self, adapter):
        post = make_instagram_post(video_url=None)
        result = adapter._map_instagram(post)
        assert len(result.media_urls) == 1

    def test_instagram_post_no_image_no_video(self, adapter):
        post = make_instagram_post(image_url=None, video_url=None)
        result = adapter._map_instagram(post)
        assert result.media_urls == []


class TestSearchComments:
    """Test search_comments (Reddit only)."""

    async def test_search_comments_basic(self, adapter, mock_xpoz_client):
        comments = [make_reddit_comment(body="found it")]
        mock_xpoz_client.reddit.search_comments.return_value = make_paginated(comments)

        result = await adapter.search_comments("query")

        assert len(result) == 1
        assert result[0].content == "found it"
        assert result[0].platform == DataSource.REDDIT

    async def test_search_comments_with_filters(self, adapter, mock_xpoz_client):
        mock_xpoz_client.reddit.search_comments.return_value = make_paginated([])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 6, 1)

        await adapter.search_comments(
            "test", subreddit="r/python", start_date=start, end_date=end
        )

        call_kwargs = mock_xpoz_client.reddit.search_comments.call_args[1]
        assert call_kwargs["subreddit"] == "r/python"
        assert call_kwargs["start_date"] == start
        assert call_kwargs["end_date"] == end

    async def test_search_comments_not_found(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.search_comments("nothing")
        assert result == []


class TestGetPostWithComments:
    """Test get_post_with_comments (Reddit only)."""

    async def test_returns_tuple(self, adapter, mock_xpoz_client):
        post = make_reddit_post(id="rd_42")
        comments = [make_reddit_comment(body="comment 1"), make_reddit_comment(body="comment 2")]
        result_obj = MagicMock()
        result_obj.post = post
        result_obj.comments = comments
        mock_xpoz_client.reddit.get_post_with_comments.return_value = result_obj

        mention, comment_list = await adapter.get_post_with_comments("rd_42")

        assert isinstance(mention, RawMention)
        assert mention.source_id == "rd_42"
        assert len(comment_list) == 2
        assert all(isinstance(c, XpozComment) for c in comment_list)

    async def test_not_found_raises(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            with pytest.raises(MentionFetchError, match="not found"):
                await adapter.get_post_with_comments("missing")

    async def test_no_post_data_raises(self, adapter, mock_xpoz_client):
        result_obj = MagicMock()
        result_obj.post = None
        result_obj.comments = []
        mock_xpoz_client.reddit.get_post_with_comments.return_value = result_obj

        with pytest.raises(MentionFetchError, match="no post data"):
            await adapter.get_post_with_comments("broken")


class TestPostInteractingUsers:
    """Test get_post_interacting_users."""

    async def test_twitter_liking_users(self, adapter, mock_xpoz_client):
        users = [make_twitter_user(id="liker_1")]
        mock_xpoz_client.twitter.get_post_interacting_users.return_value = make_paginated(users)

        result = await adapter.get_post_interacting_users(
            "tweet_1", platform=DataSource.TWITTER, interaction_type="liking_users"
        )

        assert len(result) == 1
        assert result[0].user_id == "liker_1"

    async def test_instagram_liking_users(self, adapter, mock_xpoz_client):
        users = [make_instagram_user()]
        mock_xpoz_client.instagram.get_post_interacting_users.return_value = make_paginated(users)

        result = await adapter.get_post_interacting_users(
            "ig_post_1", platform=DataSource.INSTAGRAM
        )
        assert len(result) == 1

    async def test_reddit_raises_error(self, adapter, mock_xpoz_client):
        with pytest.raises(MentionFetchError, match="Reddit does not support post interacting"):
            await adapter.get_post_interacting_users("rd_1", platform=DataSource.REDDIT)

    async def test_not_found_returns_empty(self, adapter, mock_xpoz_client):
        with patch.object(adapter, "_safe_xpoz_call", return_value=None):
            result = await adapter.get_post_interacting_users("missing", platform=DataSource.TWITTER)
        assert result == []


class TestDoFetch:
    """Test _do_fetch pagination path."""

    async def test_basic_fetch(self, adapter, mock_xpoz_client):
        post = make_twitter_post()
        paginated = MagicMock()
        paginated.data = [post]
        paginated.has_next_page.return_value = False
        mock_xpoz_client.twitter.search_posts.return_value = paginated

        mentions, next_cursor = await adapter._do_fetch("query")

        assert len(mentions) == 1
        assert isinstance(mentions[0], RawMention)
        assert next_cursor is None

    async def test_fetch_with_pagination(self, adapter, mock_xpoz_client):
        post = make_twitter_post()
        paginated = MagicMock()
        paginated.data = [post]
        paginated.has_next_page.return_value = True
        paginated.pagination = MagicMock()
        paginated.pagination.page_number = 1
        mock_xpoz_client.twitter.search_posts.return_value = paginated

        mentions, next_cursor = await adapter._do_fetch("query")

        assert next_cursor == "2"

    async def test_fetch_client_not_initialized(self, adapter):
        adapter._client = None

        with pytest.raises(MentionFetchError, match="not initialized"):
            await adapter._do_fetch("query")

    async def test_fetch_timeout_raises(self, adapter):
        from xpoz import OperationTimeoutError

        err = OperationTimeoutError.__new__(OperationTimeoutError)
        err.elapsed_seconds = 30.0

        with patch.object(adapter, "_search", side_effect=err):
            with pytest.raises(MentionFetchError, match="Xpoz timeout"):
                await adapter._do_fetch("query")


class TestAdapterSource:
    """Test source property."""

    async def test_default_source_twitter(self, adapter):
        assert adapter.source == DataSource.TWITTER

    async def test_default_source_instagram(self, adapter_instagram):
        assert adapter_instagram.source == DataSource.INSTAGRAM

    async def test_default_source_reddit(self, adapter_reddit):
        assert adapter_reddit.source == DataSource.REDDIT


class TestContextManager:
    """Test __aenter__ and __aexit__."""

    async def test_aexit_sets_client_none(self, adapter, mock_xpoz_client):
        mock_xpoz_client.__aexit__ = AsyncMock()
        adapter._client = mock_xpoz_client

        await adapter.__aexit__(None, None, None)

        assert adapter._client is None

    async def test_aexit_handles_runtime_error(self, adapter, mock_xpoz_client):
        mock_xpoz_client.__aexit__ = AsyncMock(side_effect=RuntimeError("event loop closed"))
        adapter._client = mock_xpoz_client

        # Should not raise
        await adapter.__aexit__(None, None, None)
        assert adapter._client is None

    async def test_aexit_with_no_client(self, adapter):
        adapter._client = None
        # Should not raise
        await adapter.__aexit__(None, None, None)


class TestFetchAllMentions:
    """Test fetch_all_mentions pagination loop."""

    async def test_single_page(self, adapter, mock_xpoz_client):
        """Single page with no next page returns all results."""
        post = make_twitter_post()
        paginated = MagicMock()
        paginated.data = [post]
        paginated.has_next_page.return_value = False
        mock_xpoz_client.twitter.search_posts.return_value = paginated

        results = await adapter.fetch_all_mentions("query", max_results=500)

        assert len(results) == 1
        assert isinstance(results[0], RawMention)

    async def test_multi_page_collects_all(self, adapter, mock_xpoz_client):
        """Multiple pages are collected until has_next_page is False."""
        post1 = make_twitter_post(id="p1")
        post2 = make_twitter_post(id="p2")
        post3 = make_twitter_post(id="p3")

        page2 = MagicMock()
        page2.data = [post2]
        page2.has_next_page.return_value = True
        page2.next_page = AsyncMock(return_value=MagicMock(
            data=[post3], has_next_page=MagicMock(return_value=False),
        ))

        page1 = MagicMock()
        page1.data = [post1]
        page1.has_next_page.return_value = True
        page1.next_page = AsyncMock(return_value=page2)

        mock_xpoz_client.twitter.search_posts.return_value = page1

        results = await adapter.fetch_all_mentions("query", max_results=500)

        assert len(results) == 3

    async def test_respects_max_results(self, adapter, mock_xpoz_client):
        """Stops when max_results is reached."""
        posts = [make_twitter_post(id=f"p{i}") for i in range(5)]

        page2 = MagicMock()
        page2.data = posts[3:]
        page2.has_next_page.return_value = False

        page1 = MagicMock()
        page1.data = posts[:3]
        page1.has_next_page.return_value = True
        page1.next_page = AsyncMock(return_value=page2)

        mock_xpoz_client.twitter.search_posts.return_value = page1

        results = await adapter.fetch_all_mentions("query", max_results=2)

        assert len(results) == 2

    async def test_passes_sort_and_time_range(self, adapter_reddit, mock_xpoz_client):
        """Sort and time_range kwargs are forwarded to Reddit search."""
        post = make_reddit_post()
        paginated = MagicMock()
        paginated.data = [post]
        paginated.has_next_page.return_value = False
        mock_xpoz_client.reddit.search_posts.return_value = paginated

        await adapter_reddit.fetch_all_mentions(
            "query", sort="top", time_range="week",
        )

        call_kwargs = mock_xpoz_client.reddit.search_posts.call_args
        assert call_kwargs[1].get("sort") == "top"
        assert call_kwargs[1].get("time") == "week"

    async def test_pagination_error_stops_gracefully(self, adapter, mock_xpoz_client):
        """Pagination error on next_page stops but returns what was collected."""
        post = make_twitter_post()
        page1 = MagicMock()
        page1.data = [post]
        page1.has_next_page.return_value = True
        page1.next_page = AsyncMock(side_effect=RuntimeError("SDK error"))

        mock_xpoz_client.twitter.search_posts.return_value = page1

        results = await adapter.fetch_all_mentions("query", max_results=500)

        assert len(results) == 1  # Got page 1 results despite page 2 failure


class TestUserEngagementEdgeCases:
    """Test engagement sum edge cases."""

    async def test_twitter_engagement_all_none(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user()
        tw_user.relevant_tweets_likes_sum = None
        tw_user.relevant_tweets_quotes_sum = None
        tw_user.relevant_tweets_replies_sum = None
        tw_user.relevant_tweets_retweets_sum = None
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.TWITTER)
        assert result[0].relevant_engagement_sum is None

    async def test_twitter_engagement_partial(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user()
        tw_user.relevant_tweets_likes_sum = 100
        tw_user.relevant_tweets_quotes_sum = None
        tw_user.relevant_tweets_replies_sum = 50
        tw_user.relevant_tweets_retweets_sum = None
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.TWITTER)
        assert result[0].relevant_engagement_sum == 150  # 100 + 50, None skipped

    async def test_instagram_engagement_all_none(self, adapter, mock_xpoz_client):
        ig_user = make_instagram_user()
        ig_user.relevant_posts_likes_sum = None
        ig_user.relevant_posts_comments_sum = None
        ig_user.relevant_posts_reshares_sum = None
        mock_xpoz_client.instagram.get_users_by_keywords.return_value = make_paginated([ig_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.INSTAGRAM)
        assert result[0].relevant_engagement_sum is None

    async def test_reddit_engagement_all_none(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user()
        rd_user.relevant_posts_upvotes_sum = None
        rd_user.relevant_posts_comments_count_sum = None
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.REDDIT)
        assert result[0].relevant_engagement_sum is None

    async def test_twitter_metadata_no_location(self, adapter, mock_xpoz_client):
        tw_user = make_twitter_user(location=None)
        tw_user.relevant_tweets_impressions_sum = None
        tw_user.created_at = None
        mock_xpoz_client.twitter.get_users_by_keywords.return_value = make_paginated([tw_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.TWITTER)
        assert "location" not in result[0].metadata
        assert "relevant_impressions" not in result[0].metadata
        assert "created_at" not in result[0].metadata

    async def test_reddit_metadata_no_karma(self, adapter, mock_xpoz_client):
        rd_user = make_reddit_user()
        rd_user.total_karma = None
        rd_user.link_karma = None
        rd_user.comment_karma = None
        rd_user.is_gold = False
        rd_user.is_mod = False
        rd_user.created_at = None
        mock_xpoz_client.reddit.get_users_by_keywords.return_value = make_paginated([rd_user])

        result = await adapter.search_users_by_keywords("test", platform=DataSource.REDDIT)
        meta = result[0].metadata
        assert "total_karma" not in meta
        assert "link_karma" not in meta
        assert "comment_karma" not in meta
        assert "is_gold" not in meta
        assert "is_mod" not in meta
        assert "created_at" not in meta
