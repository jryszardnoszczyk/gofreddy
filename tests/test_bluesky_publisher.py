"""Tests for BlueskyPublisher adapter — mock HTTP with respx."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
import respx

from src.publishing.adapters.bluesky import BlueskyPublisher
from src.publishing.config import PublishingSettings
from src.publishing.models import PublishStatus, QueueItem


def _settings() -> PublishingSettings:
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
    )


def _make_queue_item(**kwargs) -> QueueItem:
    defaults = dict(
        id=uuid4(),
        org_id=uuid4(),
        client_id=None,
        platform="bluesky",
        connection_id=uuid4(),
        content_parts=[{"body": "Hello Bluesky"}],
        media=[],
        first_comment=None,
        thumbnail_url=None,
        og_title=None,
        og_description=None,
        og_image_url=None,
        twitter_card_type=None,
        canonical_url=None,
        slug=None,
        labels=[],
        group_id=None,
        newsletter_subject=None,
        newsletter_segment=None,
        status=PublishStatus.DRAFT,
        approved_at=None,
        approved_by=None,
        scheduled_at=None,
        external_id=None,
        external_url=None,
        error_message=None,
        retry_count=0,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return QueueItem(**defaults)


CREDENTIALS = {"handle": "test.bsky.social", "app_password": "xxxx-xxxx-xxxx"}

SESSION_RESPONSE = {
    "accessJwt": "eyJ-access-token",
    "refreshJwt": "eyJ-refresh-token",
    "did": "did:plc:abc123",
    "handle": "test.bsky.social",
}


def _mock_create_session(status: int = 200, body: dict | None = None):
    """Helper: mock the createSession XRPC call."""
    return respx.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession"
    ).mock(
        return_value=httpx.Response(
            status, json=body if body is not None else SESSION_RESPONSE
        )
    )


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_text_post():
    """createSession + createRecord produce correct post record structure."""
    _mock_create_session()

    post_uri = "at://did:plc:abc123/app.bsky.feed.post/3abc123"
    post_cid = "bafyreiabc123"
    respx.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord"
    ).mock(
        return_value=httpx.Response(
            200, json={"uri": post_uri, "cid": post_cid}
        )
    )

    publisher = BlueskyPublisher(_settings())
    item = _make_queue_item(content_parts=[{"body": "Hello Bluesky world"}])
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert result.external_id == post_uri
    assert "test.bsky.social" in (result.external_url or "")

    # Verify createRecord payload
    import json

    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["repo"] == "did:plc:abc123"
    assert body["collection"] == "app.bsky.feed.post"
    assert body["record"]["$type"] == "app.bsky.feed.post"
    assert body["record"]["text"] == "Hello Bluesky world"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
async def test_build_facets_url():
    """URL facets use UTF-8 byte offsets (not char indices).

    Uses an emoji before the URL to verify byte vs char difference.
    """
    publisher = BlueskyPublisher(_settings())
    # Emoji (4 bytes in UTF-8) followed by a space and URL
    text = "\U0001f600 https://example.com"
    facets = publisher._build_facets(text)

    assert len(facets) == 1
    facet = facets[0]
    assert facet["features"][0]["$type"] == "app.bsky.richtext.facet#link"
    assert facet["features"][0]["uri"] == "https://example.com"

    # The emoji is 4 bytes, space is 1 byte -> URL starts at byte 5
    assert facet["index"]["byteStart"] == 5
    # URL "https://example.com" is 19 bytes
    assert facet["index"]["byteEnd"] == 24

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_with_link_embed():
    """External embed structure when URL in content_parts."""
    _mock_create_session()

    post_uri = "at://did:plc:abc123/app.bsky.feed.post/3def456"
    create_record_route = respx.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord"
    ).mock(
        return_value=httpx.Response(
            200, json={"uri": post_uri, "cid": "bafyrei-cid"}
        )
    )

    publisher = BlueskyPublisher(_settings())
    item = _make_queue_item(
        content_parts=[
            {"body": "Check this article", "url": "https://example.com/post"}
        ],
        og_title="My Article",
        og_description="Article description",
    )
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True

    import json

    body = json.loads(create_record_route.calls.last.request.content)
    embed = body["record"]["embed"]
    assert embed["$type"] == "app.bsky.embed.external"
    assert embed["external"]["uri"] == "https://example.com/post"
    assert embed["external"]["title"] == "My Article"
    assert embed["external"]["description"] == "Article description"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_validate_credentials_invalid():
    """False when createSession returns 401."""
    _mock_create_session(
        status=401,
        body={"error": "AuthenticationRequired", "message": "Invalid"},
    )

    publisher = BlueskyPublisher(_settings())
    valid = await publisher.validate_credentials(CREDENTIALS)
    assert valid is False

    await publisher.close()
