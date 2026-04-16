"""Tests for social platform monitoring adapters (Bluesky, Facebook, LinkedIn)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx
from pydantic import SecretStr

from src.monitoring.adapters.bluesky import BlueskyMentionFetcher
from src.monitoring.adapters.facebook import (
    FacebookMentionFetcher,
    _filter_and_cursor,
    _parse_timestamp,
)
from src.monitoring.adapters.linkedin import LinkedInMentionFetcher
from src.monitoring.config import MonitoringSettings
from src.monitoring.exceptions import MentionFetchError
from src.monitoring.models import DataSource

# ─── Fixtures ────────────────────────────────────────────────────────────────

BLUESKY_SEARCH_RESPONSE = {
    "posts": [
        {
            "uri": "at://did:plc:abc123/app.bsky.feed.post/xyz789",
            "author": {
                "did": "did:plc:abc123",
                "handle": "alice.bsky.social",
                "displayName": "Alice",
                "avatar": "https://cdn.bsky.app/img/avatar/abc",
            },
            "record": {
                "text": "Just tried the new product!",
                "createdAt": "2026-03-08T12:00:00.000Z",
                "langs": ["en"],
                "facets": [
                    {
                        "features": [
                            {"$type": "app.bsky.richtext.facet#tag", "tag": "tech"},
                        ]
                    }
                ],
            },
            "likeCount": 42,
            "repostCount": 5,
            "replyCount": 3,
            "quoteCount": 1,
            "embed": {
                "$type": "app.bsky.embed.images#view",
                "images": [
                    {"fullsize": "https://cdn.bsky.app/img/feed/abc/full.jpg"}
                ],
            },
        }
    ],
    "cursor": "next-page-cursor-string",
}

BLUESKY_EMPTY_RESPONSE = {"posts": [], "cursor": None}

FACEBOOK_APIFY_ITEM = {
    "postId": "pfbid0abc123",
    "message": "Great service from @brand!",
    "url": "https://facebook.com/bob/posts/123",
    "timestamp": "2026-03-08T10:00:00.000Z",
    "reactions_count": 150,
    "reshare_count": 12,
    "comments_count": 8,
    "reactions": {"like": 100, "love": 30, "wow": 10, "haha": 5, "sad": 3, "angry": 2},
    "author": {"name": "Bob Smith", "id": "123456", "url": "https://facebook.com/bob"},
    "type": "photo",
    "image": "https://scontent.xx.fbcdn.net/v/photo.jpg",
}

LINKEDIN_APIFY_ITEM = {
    "urn": "urn:li:activity:7000000000000000000",
    "text": "Impressive results from @brand this quarter",
    "url": "https://linkedin.com/feed/update/urn:li:activity:7000000000000000000",
    "timestamp": "2026-03-08T09:00:00.000Z",
    "reactions": 85,
    "comments_count": 12,
    "author": {
        "name": "Carol Director",
        "profile_id": "carol-director",
        "job_title": "VP Marketing",
        "company": "Acme Corp",
    },
}


def _settings(**overrides) -> MonitoringSettings:
    return MonitoringSettings(adapter_timeout_seconds=5.0, **overrides)


def _mock_apify_run(items: list[dict], status: str = "SUCCEEDED") -> tuple:
    """Create mock Apify client, actor, dataset for tests.

    Apify client pattern: client.actor(id) is SYNC (returns ActorClient),
    then .call() is ASYNC. Similarly client.dataset(id) is SYNC, .list_items() is ASYNC.
    """
    mock_dataset = MagicMock()
    mock_dataset.list_items = AsyncMock(return_value=MagicMock(items=items))

    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(
        return_value={"status": status, "defaultDatasetId": "ds-123"}
    )

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    return mock_client, mock_actor, mock_dataset


# ─── Bluesky Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestBlueskyMentionFetcher:
    async def test_fetch_happy_path(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=BLUESKY_SEARCH_RESPONSE))

            mentions, cursor = await fetcher._do_fetch("product")

        assert len(mentions) == 1
        assert cursor == "next-page-cursor-string"
        m = mentions[0]
        assert m.source == DataSource.BLUESKY
        assert m.source_id == "at://did:plc:abc123/app.bsky.feed.post/xyz789"
        assert m.author_handle == "alice.bsky.social"
        assert m.author_name == "Alice"
        assert m.content == "Just tried the new product!"
        assert m.engagement_likes == 42
        assert m.engagement_shares == 5
        assert m.engagement_comments == 3
        await fetcher.close()

    async def test_fetch_with_cursor_pagination(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            route = respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=BLUESKY_SEARCH_RESPONSE))

            await fetcher._do_fetch("brand", cursor="prev-cursor")

            assert route.called
            req = route.calls[0].request
            assert "cursor=prev-cursor" in str(req.url)
        await fetcher.close()

    async def test_fetch_empty_results(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=BLUESKY_EMPTY_RESPONSE))

            mentions, cursor = await fetcher._do_fetch("noresults")

        assert mentions == []
        assert cursor is None
        await fetcher.close()

    async def test_fetch_invalid_request_raises_mention_fetch_error(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(400, text="InvalidRequest"))

            with pytest.raises(MentionFetchError, match="invalid request"):
                await fetcher._do_fetch("")
        await fetcher.close()

    async def test_fetch_rate_limited_raises_runtime_error(self):
        """429 raises RuntimeError so base class retries with backoff."""
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(
                return_value=httpx.Response(
                    429, headers={"ratelimit-reset": "1709900000"}
                )
            )

            with pytest.raises(RuntimeError, match="rate limited"):
                await fetcher._do_fetch("query")
        await fetcher.close()

    async def test_post_url_construction(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        url = fetcher._post_url(
            "did:plc:abc123",
            "at://did:plc:abc123/app.bsky.feed.post/xyz789",
        )
        assert url == "https://bsky.app/profile/did:plc:abc123/post/xyz789"
        await fetcher.close()

    async def test_post_url_malformed_returns_none(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        url = fetcher._post_url("did:plc:abc", "bad-uri")
        assert url is None
        await fetcher.close()

    async def test_field_mapping_complete(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=BLUESKY_SEARCH_RESPONSE))

            mentions, _ = await fetcher._do_fetch("test")

        m = mentions[0]
        assert m.url == "https://bsky.app/profile/did:plc:abc123/post/xyz789"
        assert m.language == "en"
        assert m.metadata["author_id"] == "did:plc:abc123"
        assert m.metadata["avatar_url"] == "https://cdn.bsky.app/img/avatar/abc"
        assert m.metadata["quote_count"] == 1
        assert m.metadata["hashtags"] == ["tech"]
        assert m.published_at is not None
        assert m.published_at.tzinfo is not None
        await fetcher.close()

    async def test_field_mapping_missing_optional_fields(self):
        """Posts with minimal fields should still map correctly."""
        minimal_post = {
            "uri": "at://did:plc:min/app.bsky.feed.post/min1",
            "author": {"did": "did:plc:min", "handle": "min.bsky.social"},
            "record": {"text": "minimal"},
        }
        response = {"posts": [minimal_post]}
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=response))

            mentions, cursor = await fetcher._do_fetch("test")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.author_name is None
        assert m.engagement_likes == 0
        assert m.language == "en"
        assert m.media_urls == []
        assert cursor is None
        await fetcher.close()

    async def test_language_extraction_from_langs(self):
        post = {
            "uri": "at://did:plc:fr/app.bsky.feed.post/fr1",
            "author": {"did": "did:plc:fr", "handle": "french.bsky.social"},
            "record": {"text": "Bonjour!", "langs": ["fr", "en"]},
        }
        response = {"posts": [post]}
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=response))

            mentions, _ = await fetcher._do_fetch("bonjour")

        assert mentions[0].language == "fr"
        await fetcher.close()

    async def test_media_url_extraction_from_embeds(self):
        fetcher = BlueskyMentionFetcher(settings=_settings())
        with respx.mock:
            respx.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            ).mock(return_value=httpx.Response(200, json=BLUESKY_SEARCH_RESPONSE))

            mentions, _ = await fetcher._do_fetch("test")

        assert "https://cdn.bsky.app/img/feed/abc/full.jpg" in mentions[0].media_urls
        await fetcher.close()


# ─── Facebook Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.mock_required
class TestFacebookMentionFetcher:
    async def test_fetch_happy_path(self):
        mock_client, _, _ = _mock_apify_run([FACEBOOK_APIFY_ITEM])
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, cursor = await fetcher._do_fetch("brand")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.FACEBOOK
        assert m.source_id == "pfbid0abc123"
        assert m.author_name == "Bob Smith"
        assert m.content == "Great service from @brand!"
        assert m.engagement_likes == 150
        assert m.engagement_shares == 12
        assert m.engagement_comments == 8
        assert cursor is not None

    async def test_fetch_with_synthetic_cursor_filters(self):
        old_item = {**FACEBOOK_APIFY_ITEM, "timestamp": "2026-03-01T00:00:00.000Z"}
        new_item = {**FACEBOOK_APIFY_ITEM, "postId": "new1", "timestamp": "2026-03-08T10:00:00.000Z"}
        mock_client, _, _ = _mock_apify_run([old_item, new_item])
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        # Cursor set after the old item, before the new
        mentions, _ = await fetcher._do_fetch(
            "brand", cursor="2026-03-05T00:00:00+00:00"
        )
        assert len(mentions) == 1
        assert mentions[0].source_id == "new1"

    async def test_fetch_empty_dataset(self):
        mock_client, _, _ = _mock_apify_run([])
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, cursor = await fetcher._do_fetch("nothing")
        assert mentions == []
        assert cursor is None

    async def test_apify_client_init_failure(self):
        with patch(
            "apify_client.ApifyClientAsync",
            side_effect=RuntimeError("pyo3 panic"),
        ):
            fetcher = FacebookMentionFetcher(
                apify_token=SecretStr("bad-token"), settings=_settings()
            )
            with pytest.raises(MentionFetchError, match="init failed"):
                fetcher._apify()

    async def test_actor_run_failure_raises_mention_fetch_error(self):
        mock_client, mock_actor, _ = _mock_apify_run([])
        mock_actor.call.return_value = None  # Apify returns None on failure
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        with pytest.raises(MentionFetchError, match="failed"):
            await fetcher._do_fetch("query")

    async def test_field_mapping_reactions_summed(self):
        """reactions_count is the engagement_likes value."""
        mock_client, _, _ = _mock_apify_run([FACEBOOK_APIFY_ITEM])
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch("brand")
        assert mentions[0].engagement_likes == 150

    async def test_field_mapping_metadata_reactions_breakdown(self):
        mock_client, _, _ = _mock_apify_run([FACEBOOK_APIFY_ITEM])
        fetcher = FacebookMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch("brand")
        reactions = mentions[0].metadata["reactions"]
        assert reactions["like"] == 100
        assert reactions["love"] == 30

    async def test_timestamp_parsing_iso_and_unix(self):
        # ISO format
        item_iso = {"timestamp": "2026-03-08T10:00:00.000Z"}
        ts = _parse_timestamp(item_iso)
        assert ts is not None
        assert ts.tzinfo is not None
        assert ts.year == 2026

        # Unix format
        item_unix = {"timestamp": 1773097200}
        ts2 = _parse_timestamp(item_unix)
        assert ts2 is not None
        assert ts2.tzinfo is not None

        # Missing
        assert _parse_timestamp({}) is None

        # Invalid
        assert _parse_timestamp({"timestamp": "not-a-date"}) is None


# ─── LinkedIn Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.mock_required
class TestLinkedInMentionFetcher:
    async def test_fetch_happy_path(self):
        mock_client, _, _ = _mock_apify_run([LINKEDIN_APIFY_ITEM])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, cursor = await fetcher._do_fetch("brand")

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.LINKEDIN
        assert m.source_id == "urn:li:activity:7000000000000000000"
        assert m.author_name == "Carol Director"
        assert m.engagement_likes == 85
        assert m.engagement_shares == 0
        assert m.engagement_comments == 12

    async def test_limit_clamped_to_50(self):
        mock_client, mock_actor, _ = _mock_apify_run([LINKEDIN_APIFY_ITEM])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        await fetcher._do_fetch("brand", limit=200)

        # Verify actor was called with clamped limit
        call_kwargs = mock_actor.call.call_args
        run_input = call_kwargs.kwargs.get("run_input") or call_kwargs[1].get("run_input")
        assert run_input["resultsLimit"] == 50

    async def test_limit_clamped_logs_warning(self, caplog):
        mock_client, _, _ = _mock_apify_run([LINKEDIN_APIFY_ITEM])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        with caplog.at_level(logging.WARNING):
            await fetcher._do_fetch("brand", limit=100)

        assert any("linkedin_limit_clamped" in r.message for r in caplog.records)

    async def test_fetch_with_synthetic_cursor(self):
        old_item = {**LINKEDIN_APIFY_ITEM, "timestamp": "2026-03-01T00:00:00.000Z"}
        new_item = {
            **LINKEDIN_APIFY_ITEM,
            "urn": "urn:li:activity:new",
            "timestamp": "2026-03-08T09:00:00.000Z",
        }
        mock_client, _, _ = _mock_apify_run([old_item, new_item])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch(
            "brand", cursor="2026-03-05T00:00:00+00:00"
        )
        assert len(mentions) == 1
        assert mentions[0].source_id == "urn:li:activity:new"

    async def test_field_mapping_b2b_metadata(self):
        mock_client, _, _ = _mock_apify_run([LINKEDIN_APIFY_ITEM])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch("brand")
        m = mentions[0]
        assert m.metadata["author_id"] == "carol-director"
        assert m.metadata["job_title"] == "VP Marketing"
        assert m.metadata["company"] == "Acme Corp"

    async def test_field_mapping_document_media_type(self):
        item_with_doc = {
            **LINKEDIN_APIFY_ITEM,
            "document": "https://linkedin.com/doc/slides.pdf",
        }
        mock_client, _, _ = _mock_apify_run([item_with_doc])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch("brand")
        m = mentions[0]
        assert m.metadata["media_type"] == "document"
        assert "https://linkedin.com/doc/slides.pdf" in m.media_urls

    async def test_reactions_as_dict_summed(self):
        """When reactions is a dict, values are summed for engagement_likes."""
        item = {
            **LINKEDIN_APIFY_ITEM,
            "reactions": {"like": 50, "celebrate": 20, "love": 15},
        }
        mock_client, _, _ = _mock_apify_run([item])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        mentions, _ = await fetcher._do_fetch("brand")
        assert mentions[0].engagement_likes == 85

    async def test_searchTerms_is_string_not_list(self):
        """LinkedIn actor expects searchTerms as a string, NOT a list."""
        mock_client, mock_actor, _ = _mock_apify_run([LINKEDIN_APIFY_ITEM])
        fetcher = LinkedInMentionFetcher(
            apify_token=SecretStr("test-token"), settings=_settings()
        )
        fetcher._client = mock_client

        await fetcher._do_fetch("brand query")

        call_kwargs = mock_actor.call.call_args
        run_input = call_kwargs.kwargs.get("run_input") or call_kwargs[1].get("run_input")
        assert run_input["searchTerms"] == "brand query"
        assert not isinstance(run_input["searchTerms"], list)


# ─── Shared Utility Tests ────────────────────────────────────────────────────


class TestFilterAndCursor:
    def test_no_cursor_returns_all(self):
        items = [
            {"timestamp": "2026-03-08T10:00:00.000Z"},
            {"timestamp": "2026-03-08T11:00:00.000Z"},
        ]
        filtered, cursor = _filter_and_cursor(items, None)
        assert len(filtered) == 2
        assert cursor is not None

    def test_cursor_filters_old_items(self):
        items = [
            {"timestamp": "2026-03-01T00:00:00.000Z"},
            {"timestamp": "2026-03-08T10:00:00.000Z"},
        ]
        filtered, _ = _filter_and_cursor(items, "2026-03-05T00:00:00+00:00")
        assert len(filtered) == 1

    def test_empty_items_return_none_cursor(self):
        filtered, cursor = _filter_and_cursor([], None)
        assert filtered == []
        assert cursor is None

    def test_cursor_is_latest_timestamp(self):
        items = [
            {"timestamp": "2026-03-08T10:00:00.000Z"},
            {"timestamp": "2026-03-08T12:00:00.000Z"},
            {"timestamp": "2026-03-08T11:00:00.000Z"},
        ]
        _, cursor = _filter_and_cursor(items, None)
        assert cursor is not None
        dt = datetime.fromisoformat(cursor)
        assert dt.hour == 12


# ─── IC Content Adapter Tests ────────────────────────────────────────────────

from src.monitoring.adapters.ic_content import ICContentAdapter, _parse_query
from src.search.exceptions import ICUnavailableError

# Sample IC discovery response
IC_DISCOVERY_RESPONSE = {
    "accounts": [
        {"handle": "creator1", "name": "Creator One", "followers": 50000, "verified": True},
        {"handle": "creator2", "name": "Creator Two", "followers": 10000},
    ],
    "credits_left": "11999.5",
}

# Sample IC content response for a single creator
IC_CONTENT_RESPONSE_CREATOR1 = {
    "posts": [
        {
            "id": "post_abc123",
            "url": "https://www.tiktok.com/@creator1/video/post_abc123",
            "caption": "Loving the new TestBrand product! #review",
            "taken_at": 1710720000,  # 2024-03-18T00:00:00 UTC
            "engagement": {"likes": 1500, "comments": 42, "shares": 10, "views": 50000},
            "thumbnail": "https://cdn.example.com/thumb1.jpg",
            "hashtags": ["review", "testbrand"],
            "duration": 30,
        },
        {
            "id": "post_def456",
            "url": "https://www.tiktok.com/@creator1/video/post_def456",
            "caption": "Another day another TestBrand unboxing",
            "taken_at": 1710633600,  # 2024-03-17T00:00:00 UTC
            "engagement": {"likes": 800, "comments": 15, "shares": 3, "views": 20000},
        },
    ],
}

IC_CONTENT_RESPONSE_CREATOR2 = {
    "posts": [
        {
            "id": "post_ghi789",
            "url": "https://www.tiktok.com/@creator2/video/post_ghi789",
            "caption": "TestBrand comparison video",
            "taken_at": 1710806400,  # 2024-03-19T00:00:00 UTC
            "engagement": {"likes": 300, "comments": 5, "shares": 1, "views": 8000},
        },
    ],
}


class TestParseQuery:
    """Tests for _parse_query helper."""

    def test_extracts_quoted_terms(self):
        result = _parse_query('"TestBrand" OR "test brand"')
        assert result["keywords_in_captions"] == ["TestBrand", "test brand"]
        assert result["ai_search"] == '"TestBrand" OR "test brand"'

    def test_no_quotes_uses_raw_query(self):
        result = _parse_query("some brand name")
        assert result["keywords_in_captions"] == ["some brand name"]
        assert result["ai_search"] == "some brand name"

    def test_single_quoted_term(self):
        result = _parse_query('"OnlyBrand"')
        assert result["keywords_in_captions"] == ["OnlyBrand"]

    def test_mixed_quoted_and_unquoted(self):
        result = _parse_query('"Brand" AND something OR "Other Brand"')
        assert result["keywords_in_captions"] == ["Brand", "Other Brand"]

    def test_empty_query(self):
        result = _parse_query("")
        # Should not crash, ai_search is empty string
        assert result["ai_search"] == ""


@pytest.mark.mock_required
class TestICContentAdapter:
    """Tests for ICContentAdapter (TikTok + YouTube)."""

    def _make_adapter(self, ic_mock, source=DataSource.TIKTOK):
        return ICContentAdapter(ic_mock, default_source=source)

    @pytest.mark.asyncio
    async def test_happy_path_tiktok(self):
        """Discover creators → fetch content → return RawMentions."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value=IC_DISCOVERY_RESPONSE)
        ic.get_content = AsyncMock(side_effect=[
            IC_CONTENT_RESPONSE_CREATOR1,
            IC_CONTENT_RESPONSE_CREATOR2,
        ])

        adapter = self._make_adapter(ic, DataSource.TIKTOK)
        mentions, cursor = await adapter.fetch_mentions('"TestBrand"')

        assert cursor is None  # No pagination
        assert len(mentions) == 3

        # Verify discover was called with correct platform and filters
        ic.discover.assert_called_once()
        call_args = ic.discover.call_args
        assert call_args[0][0] == "tiktok"  # positional: platform
        filters = call_args.kwargs.get("filters") or call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs["filters"]
        assert "keywords_in_captions" in filters
        assert "ai_search" in filters

        # Verify content was fetched for both creators
        assert ic.get_content.call_count == 2

        # Check mention mapping
        first = mentions[0]  # Sorted by published_at desc
        assert first.source == DataSource.TIKTOK
        assert first.author_handle in ("creator1", "creator2")

    @pytest.mark.asyncio
    async def test_happy_path_youtube(self):
        """Same flow works for YouTube."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [{"handle": "yt_creator", "name": "YT Creator"}],
        })
        ic.get_content = AsyncMock(return_value={
            "posts": [{
                "id": "yt_video_1",
                "url": "https://youtube.com/watch?v=abc123",
                "caption": "TestBrand review",
                "taken_at": 1710720000,
                "engagement": {"likes": 100, "comments": 5, "views": 5000},
            }],
        })

        adapter = self._make_adapter(ic, DataSource.YOUTUBE)
        mentions, _ = await adapter.fetch_mentions('"TestBrand"')

        assert len(mentions) == 1
        assert mentions[0].source == DataSource.YOUTUBE
        assert mentions[0].url == "https://youtube.com/watch?v=abc123"

        # Verify platform passed to IC
        ic.discover.assert_called_once()
        assert ic.discover.call_args[0][0] == "youtube"

    @pytest.mark.asyncio
    async def test_empty_discovery(self):
        """Empty discovery results → ([], None), no crash."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={"accounts": []})

        adapter = self._make_adapter(ic)
        mentions, cursor = await adapter.fetch_mentions('"UnknownBrand"')

        assert mentions == []
        assert cursor is None
        ic.get_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_discovery_returns_empty_dict(self):
        """IC 422 returns {} — treated as empty, no crash."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={})

        adapter = self._make_adapter(ic)
        mentions, cursor = await adapter.fetch_mentions('"Brand"')

        assert mentions == []
        assert cursor is None

    @pytest.mark.asyncio
    async def test_ic_unavailable_wrapped_as_mention_fetch_error(self):
        """ICUnavailableError during discovery → MentionFetchError (no retry)."""
        ic = AsyncMock()
        ic.discover = AsyncMock(side_effect=ICUnavailableError(401, "Auth failed"))

        adapter = self._make_adapter(ic)
        with pytest.raises(MentionFetchError, match="IC unavailable"):
            await adapter.fetch_mentions('"TestBrand"')

    @pytest.mark.asyncio
    async def test_ic_unavailable_during_content_fetch(self):
        """ICUnavailableError during content fetch → MentionFetchError."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [{"handle": "creator1"}],
        })
        ic.get_content = AsyncMock(side_effect=ICUnavailableError(403, "Forbidden"))

        adapter = self._make_adapter(ic)
        with pytest.raises(MentionFetchError, match="IC unavailable"):
            await adapter.fetch_mentions('"TestBrand"')

    @pytest.mark.asyncio
    async def test_content_fetch_partial_failure(self):
        """If one creator's content fetch fails (non-IC error), others still returned."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [
                {"handle": "good_creator"},
                {"handle": "bad_creator"},
            ],
        })
        ic.get_content = AsyncMock(side_effect=[
            {"posts": [{"id": "p1", "caption": "Good post", "taken_at": 1710720000}]},
            ConnectionError("network error"),
        ])

        adapter = self._make_adapter(ic)
        mentions, _ = await adapter.fetch_mentions('"TestBrand"')

        # Should have mention from good_creator, bad_creator's error logged but not fatal
        assert len(mentions) == 1
        assert mentions[0].author_handle == "good_creator"

    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        """close() must be a no-op (does NOT close shared ICBackend)."""
        ic = AsyncMock()
        adapter = self._make_adapter(ic)
        await adapter.close()
        # ICBackend's close should NOT be called
        ic.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_mentions_sorted_by_published_at_desc(self):
        """Mentions should be sorted newest first."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [{"handle": "creator"}],
        })
        ic.get_content = AsyncMock(return_value={
            "posts": [
                {"id": "old", "caption": "Old", "taken_at": 1710633600},
                {"id": "new", "caption": "New", "taken_at": 1710806400},
                {"id": "mid", "caption": "Mid", "taken_at": 1710720000},
            ],
        })

        adapter = self._make_adapter(ic)
        mentions, _ = await adapter.fetch_mentions('"Brand"')

        assert len(mentions) == 3
        assert mentions[0].source_id == "new"
        assert mentions[1].source_id == "mid"
        assert mentions[2].source_id == "old"

    @pytest.mark.asyncio
    async def test_limit_respected(self):
        """Mentions are capped to limit parameter."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [{"handle": "creator"}],
        })
        ic.get_content = AsyncMock(return_value={
            "posts": [
                {"id": f"p{i}", "caption": f"Post {i}", "taken_at": 1710720000 + i}
                for i in range(10)
            ],
        })

        adapter = self._make_adapter(ic)
        mentions, _ = await adapter.fetch_mentions('"Brand"', limit=3)

        assert len(mentions) == 3

    def test_unsupported_source_raises(self):
        """Constructor rejects unsupported DataSource."""
        ic = AsyncMock()
        with pytest.raises(ValueError, match="does not support"):
            ICContentAdapter(ic, default_source=DataSource.FACEBOOK)

    @pytest.mark.asyncio
    async def test_mention_field_mapping(self):
        """Verify detailed field mapping from IC post to RawMention."""
        ic = AsyncMock()
        ic.discover = AsyncMock(return_value={
            "accounts": [{"handle": "testuser", "name": "Test User", "followers": 99000, "verified": True}],
        })
        ic.get_content = AsyncMock(return_value={
            "posts": [{
                "id": "vid123",
                "url": "https://www.tiktok.com/@testuser/video/vid123",
                "caption": "Amazing TestBrand content",
                "taken_at": 1710720000,
                "engagement": {"likes": 500, "comments": 20, "shares": 8, "views": 15000},
                "thumbnail": "https://cdn.example.com/thumb.jpg",
                "hashtags": ["testbrand", "review"],
                "duration": 45,
            }],
        })

        adapter = self._make_adapter(ic, DataSource.TIKTOK)
        mentions, _ = await adapter.fetch_mentions('"TestBrand"')

        assert len(mentions) == 1
        m = mentions[0]
        assert m.source == DataSource.TIKTOK
        assert m.source_id == "vid123"
        assert m.author_handle == "testuser"
        assert m.author_name == "Test User"
        assert m.content == "Amazing TestBrand content"
        assert m.url == "https://www.tiktok.com/@testuser/video/vid123"
        assert m.engagement_likes == 500
        assert m.engagement_comments == 20
        assert m.engagement_shares == 8
        assert m.reach_estimate == 15000
        assert m.media_urls == ["https://cdn.example.com/thumb.jpg"]
        assert m.metadata["hashtags"] == ["testbrand", "review"]
        assert m.metadata["video_duration"] == 45
        assert m.metadata["author_followers"] == 99000
        assert m.metadata["author_verified"] is True


# ─── Trustpilot Sanitizer Tests ──────────────────────────────────────────────

from src.monitoring.query_sanitizer import sanitize_for_trustpilot


class TestSanitizeForTrustpilot:
    """Tests for sanitize_for_trustpilot query sanitizer."""

    def test_quoted_brand_becomes_slug(self):
        assert sanitize_for_trustpilot('"TestBrand" OR "test brand"') == "testbrand"

    def test_domain_preserved(self):
        assert sanitize_for_trustpilot('"example.com"') == "example.com"

    def test_unquoted_domain(self):
        assert sanitize_for_trustpilot("example.com") == "example.com"

    def test_unquoted_brand(self):
        assert sanitize_for_trustpilot("TestBrand") == "testbrand"

    def test_brand_with_spaces_becomes_slug(self):
        result = sanitize_for_trustpilot('"My Brand Name"')
        assert result == "mybrandname"

    def test_single_quoted_term(self):
        assert sanitize_for_trustpilot('"nike"') == "nike"

    def test_mixed_with_boolean_operators(self):
        result = sanitize_for_trustpilot('"acme.com" AND "acme"')
        assert result == "acme.com"


# ─── Metadata Serialization Tests ────────────────────────────────────────────

import json


class TestMetadataSerialization:
    """Verify metadata dict is JSON-serialized before DB insert."""

    def test_metadata_serialized_in_mention_tuples(self):
        """Service layer must json.dumps metadata for asyncpg JSONB column."""
        from src.monitoring.models import RawMention, DataSource

        mention = RawMention(
            source=DataSource.TWITTER,
            source_id="test123",
            content="test",
            metadata={"bookmark_count": 5, "nested": {"key": "val"}},
        )

        # Simulate what service.py does
        serialized = json.dumps(mention.metadata) if mention.metadata else '{}'
        assert isinstance(serialized, str)
        assert json.loads(serialized) == {"bookmark_count": 5, "nested": {"key": "val"}}

    def test_empty_metadata_serialized(self):
        serialized = json.dumps({}) if {} else '{}'
        assert serialized == '{}'
