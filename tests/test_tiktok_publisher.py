"""Tests for TikTokPublisher adapter — mock HTTP with respx."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
import respx

from src.publishing.adapters.tiktok import TikTokPublisher
from src.publishing.config import PublishingSettings
from src.publishing.exceptions import ContentValidationError
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
        platform="tiktok",
        connection_id=uuid4(),
        content_parts=[{"body": "TikTok caption"}],
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


CREDENTIALS = {"access_token": "tiktok_tok_test"}


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_video():
    """Mock video init endpoint, verify PULL_FROM_URL payload."""
    publish_id = "pub_video_123"
    video_init_route = respx.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"publish_id": publish_id}},
        )
    )

    publisher = TikTokPublisher(_settings())
    item = _make_queue_item(
        content_parts=[{"body": "My cool video #fyp"}],
        media=[{"type": "video", "url": "https://r2.example.com/video.mp4"}],
    )
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert result.external_id == publish_id

    import json

    body = json.loads(video_init_route.calls.last.request.content)
    assert body["source_info"]["source"] == "PULL_FROM_URL"
    assert body["source_info"]["video_url"] == "https://r2.example.com/video.mp4"
    assert body["post_info"]["description"] == "My cool video #fyp"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_carousel():
    """Mock content init endpoint with photo_images."""
    publish_id = "pub_carousel_456"
    carousel_route = respx.post(
        "https://open.tiktokapis.com/v2/post/publish/content/init/"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"publish_id": publish_id}},
        )
    )

    # TikTok carousel requires 4-35 images
    photo_urls = [f"https://r2.example.com/img{i}.jpg" for i in range(5)]
    publisher = TikTokPublisher(_settings())
    item = _make_queue_item(
        content_parts=[{"body": "Photo carousel #travel"}],
        media=[{"type": "image", "url": url} for url in photo_urls],
    )
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert result.external_id == publish_id

    import json

    body = json.loads(carousel_route.calls.last.request.content)
    assert body["source_info"]["source"] == "PULL_FROM_URL"
    assert body["source_info"]["photo_images"] == photo_urls
    assert body["post_info"]["description"] == "Photo carousel #travel"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
async def test_content_validation_long_caption():
    """ContentValidationError for caption > 2200 characters."""
    publisher = TikTokPublisher(_settings())
    long_caption = "x" * 2201
    item = _make_queue_item(
        content_parts=[{"body": long_caption}],
        media=[{"type": "video", "url": "https://r2.example.com/video.mp4"}],
    )

    with pytest.raises(ContentValidationError, match="2200"):
        await publisher._do_publish(item, CREDENTIALS)

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_validate_credentials():
    """Mock user info endpoint, verify True on 200."""
    respx.get("https://open.tiktokapis.com/v2/user/info/").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"user": {"display_name": "TestUser"}}},
        )
    )

    publisher = TikTokPublisher(_settings())
    valid = await publisher.validate_credentials(CREDENTIALS)
    assert valid is True

    await publisher.close()
