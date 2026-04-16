"""Tests for Xpoz SDK monitoring adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.monitoring.adapters.xpoz import XpozAdapter
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource


def _make_settings() -> MonitoringSettings:
    return MonitoringSettings(
        xpoz_api_key="test-xpoz-key",  # type: ignore[arg-type]
        adapter_timeout_seconds=5.0,
    )


def _make_twitter_post(**overrides):
    post = MagicMock()
    post.id = overrides.get("id", "tw123")
    post.text = overrides.get("text", "Check out Nike shoes!")
    post.author_username = overrides.get("author_username", "sneakerhead")
    post.like_count = overrides.get("like_count", 100)
    post.retweet_count = overrides.get("retweet_count", 50)
    post.reply_count = overrides.get("reply_count", 10)
    post.quote_count = overrides.get("quote_count", 5)
    post.impression_count = overrides.get("impression_count", 5000)
    post.bookmark_count = overrides.get("bookmark_count", 20)
    post.hashtags = overrides.get("hashtags", ["nike", "sneakers"])
    post.mentions = overrides.get("mentions", ["@nike"])
    post.media_urls = overrides.get("media_urls", ["https://img.twitter.com/1.jpg"])
    post.country = overrides.get("country", "US")
    post.region = overrides.get("region", "California")
    post.city = overrides.get("city", "LA")
    post.lang = overrides.get("lang", "en")
    post.created_at = overrides.get("created_at", datetime(2026, 3, 1, tzinfo=timezone.utc))
    post.is_retweet = overrides.get("is_retweet", False)
    return post


def _make_instagram_post(**overrides):
    post = MagicMock()
    post.id = overrides.get("id", "ig456")
    post.caption = overrides.get("caption", "New Nike collection")
    post.username = overrides.get("username", "fashionista")
    post.like_count = overrides.get("like_count", 500)
    post.comment_count = overrides.get("comment_count", 30)
    post.reshare_count = overrides.get("reshare_count", 15)
    post.video_play_count = overrides.get("video_play_count", 10000)
    post.image_url = overrides.get("image_url", "https://ig.com/img.jpg")
    post.video_url = overrides.get("video_url", "https://ig.com/vid.mp4")
    post.media_type = overrides.get("media_type", "VIDEO")
    post.location = overrides.get("location", "New York")
    post.created_at = overrides.get("created_at", datetime(2026, 3, 1, tzinfo=timezone.utc))
    return post


def _make_reddit_post(**overrides):
    post = MagicMock()
    post.id = overrides.get("id", "rd789")
    post.title = overrides.get("title", "Nike Air Max review")
    post.selftext = overrides.get("selftext", "Great shoes, 10/10 comfort.")
    post.author_username = overrides.get("author_username", "sneakerfan")
    post.subreddit_name = overrides.get("subreddit_name", "Sneakers")
    post.score = overrides.get("score", 250)
    post.upvotes = overrides.get("upvotes", 300)
    post.downvotes = overrides.get("downvotes", 50)
    post.upvote_ratio = overrides.get("upvote_ratio", 0.86)
    post.comments_count = overrides.get("comments_count", 45)
    post.is_video = overrides.get("is_video", False)
    post.permalink = overrides.get("permalink", "/r/Sneakers/comments/abc/nike_review/")
    post.created_at = overrides.get("created_at", datetime(2026, 3, 1, tzinfo=timezone.utc))
    return post


def _make_paginated_result(data, has_next=False, page=1):
    result = MagicMock()
    result.data = data
    result.has_next_page.return_value = has_next
    result.pagination = MagicMock(page_number=page)
    result.get_page = AsyncMock(return_value=result)
    return result


class TestXpozAdapterSource:
    def test_source_property_twitter(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        assert adapter.source == DataSource.TWITTER

    def test_source_property_instagram(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.INSTAGRAM)
        assert adapter.source == DataSource.INSTAGRAM

    def test_source_property_reddit(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.REDDIT)
        assert adapter.source == DataSource.REDDIT


class TestXpozFetch:
    async def test_fetch_twitter_success(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        mock_client = MagicMock()
        mock_client.twitter.search_posts = AsyncMock(
            return_value=_make_paginated_result([_make_twitter_post()])
        )
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.TWITTER
        assert m.source_id == "tw123"
        assert m.author_handle == "sneakerhead"
        assert m.content == "Check out Nike shoes!"
        assert m.engagement_likes == 100
        assert m.engagement_shares == 50
        assert m.engagement_comments == 10
        assert cursor is None

    async def test_fetch_instagram_success(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.INSTAGRAM)
        mock_client = MagicMock()
        mock_client.instagram.search_posts = AsyncMock(
            return_value=_make_paginated_result([_make_instagram_post()])
        )
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.INSTAGRAM
        assert m.source_id == "ig456"
        assert m.author_handle == "fashionista"
        assert m.engagement_likes == 500

    async def test_fetch_reddit_success(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.REDDIT)
        mock_client = MagicMock()
        mock_client.reddit.search_posts = AsyncMock(
            return_value=_make_paginated_result([_make_reddit_post()])
        )
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.REDDIT
        assert m.source_id == "rd789"
        assert "Nike Air Max review" in m.content
        assert "Great shoes" in m.content


class TestXpozMapping:
    def test_map_twitter_engagement(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        adapter._client = MagicMock()  # just to pass init check
        post = _make_twitter_post()
        m = adapter._map_twitter(post)

        assert m.engagement_likes == 100
        assert m.engagement_shares == 50
        assert m.engagement_comments == 10
        assert m.reach_estimate == 5000

    def test_map_twitter_metadata(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        adapter._client = MagicMock()
        post = _make_twitter_post()
        m = adapter._map_twitter(post)

        assert m.metadata["hashtags"] == ["nike", "sneakers"]
        assert m.metadata["mentions"] == ["@nike"]
        assert m.metadata["region"] == "California"
        assert m.metadata["city"] == "LA"
        assert m.geo_country == "US"

    def test_map_instagram_media_urls(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.INSTAGRAM)
        adapter._client = MagicMock()
        post = _make_instagram_post()
        m = adapter._map_instagram(post)

        assert "https://ig.com/img.jpg" in m.media_urls
        assert "https://ig.com/vid.mp4" in m.media_urls
        assert m.reach_estimate == 10000

    def test_map_reddit_score_to_likes(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.REDDIT)
        adapter._client = MagicMock()
        post = _make_reddit_post()
        m = adapter._map_reddit(post)

        assert m.engagement_likes == 250
        assert m.engagement_comments == 45

    def test_map_reddit_upvote_ratio(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.REDDIT)
        adapter._client = MagicMock()
        post = _make_reddit_post()
        m = adapter._map_reddit(post)

        extra = m.metadata["engagement_extra"]
        assert extra["upvotes"] == 300
        assert extra["downvotes"] == 50
        assert extra["upvote_ratio"] == pytest.approx(0.86)

    def test_map_reddit_url(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.REDDIT)
        adapter._client = MagicMock()
        post = _make_reddit_post()
        m = adapter._map_reddit(post)

        assert m.url == "https://reddit.com/r/Sneakers/comments/abc/nike_review/"


class TestXpozErrors:
    async def test_xpoz_timeout(self):
        from xpoz import OperationTimeoutError

        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        mock_client = MagicMock()
        err = OperationTimeoutError(operation_id="test-op", elapsed_seconds=25.0)
        mock_client.twitter.search_posts = AsyncMock(side_effect=err)
        adapter._client = mock_client

        with pytest.raises(MentionFetchError, match="timeout"):
            await adapter._do_fetch("nike")

    async def test_xpoz_error_propagates_for_retry(self):
        """XpozError should NOT be caught by _do_fetch — it propagates so
        BaseMentionFetcher's generic Exception handler can retry it."""
        from xpoz import XpozError

        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        mock_client = MagicMock()
        mock_client.twitter.search_posts = AsyncMock(side_effect=XpozError("API down"))
        adapter._client = mock_client

        with pytest.raises(XpozError, match="API down"):
            await adapter._do_fetch("nike")

    async def test_uninitialized_client(self):
        adapter = XpozAdapter(settings=_make_settings())
        with pytest.raises(MentionFetchError, match="not initialized"):
            await adapter._do_fetch("nike")


class TestXpozPagination:
    async def test_pagination_cursor(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        result_page1 = _make_paginated_result(
            [_make_twitter_post()], has_next=True, page=1
        )
        mock_client = MagicMock()
        mock_client.twitter.search_posts = AsyncMock(return_value=result_page1)
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike")

        assert cursor == "2"  # page_number + 1

    async def test_pagination_exhausted(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        result = _make_paginated_result([_make_twitter_post()], has_next=False)
        mock_client = MagicMock()
        mock_client.twitter.search_posts = AsyncMock(return_value=result)
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike")

        assert cursor is None

    async def test_pagination_with_cursor_jumps_to_page(self):
        adapter = XpozAdapter(settings=_make_settings(), default_source=DataSource.TWITTER)
        page2_result = _make_paginated_result(
            [_make_twitter_post(id="tw_page2")], has_next=False, page=2
        )
        initial_result = MagicMock()
        initial_result.data = [_make_twitter_post()]
        initial_result.get_page = AsyncMock(return_value=page2_result)
        initial_result.has_next_page = MagicMock(return_value=False)
        initial_result.pagination = MagicMock(page_number=1)

        mock_client = MagicMock()
        mock_client.twitter.search_posts = AsyncMock(return_value=initial_result)
        adapter._client = mock_client

        mentions, cursor = await adapter._do_fetch("nike", cursor="2")

        initial_result.get_page.assert_called_once_with(2)
        assert mentions[0].source_id == "tw_page2"
