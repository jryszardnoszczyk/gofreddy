"""Tests for YouTubePublisher adapter — mock HTTP with respx."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
import respx

from src.publishing.adapters.youtube import YouTubePublisher
from src.publishing.config import PublishingSettings
from src.publishing.exceptions import CredentialError, QuotaExhaustedError
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
        platform="youtube",
        connection_id=uuid4(),
        content_parts=[{"body": "My YouTube video description", "title": "My Video"}],
        media=[{"type": "video", "url": "https://r2.example.com/video.mp4"}],
        first_comment=None,
        thumbnail_url=None,
        og_title=None,
        og_description=None,
        og_image_url=None,
        twitter_card_type=None,
        canonical_url=None,
        slug=None,
        labels=["tech", "tutorial"],
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


CREDENTIALS = {"access_token": "ya29.youtube-test-token"}

UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadId=abc"
VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_BYTES = b"fake-video-content-bytes"


def _mock_video_download():
    """Mock downloading the video from R2."""
    respx.get("https://r2.example.com/video.mp4").mock(
        return_value=httpx.Response(200, content=VIDEO_BYTES)
    )


def _mock_resumable_init(status: int = 200, headers: dict | None = None, json_body: dict | None = None):
    """Mock the resumable upload init POST."""
    resp_headers = headers or {"Location": UPLOAD_URL}
    return respx.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
    ).mock(
        return_value=httpx.Response(
            status,
            headers=resp_headers,
            json=json_body or {},
        )
    )


def _mock_resumable_upload():
    """Mock the PUT to the resumable upload URL."""
    return respx.put(UPLOAD_URL).mock(
        return_value=httpx.Response(
            200,
            json={"id": VIDEO_ID, "snippet": {"title": "My Video"}},
        )
    )


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_video_resumable():
    """Mock init (returns Location header) + PUT upload, verify video metadata."""
    init_route = _mock_resumable_init()
    _mock_resumable_upload()
    _mock_video_download()

    publisher = YouTubePublisher(_settings())
    item = _make_queue_item()
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert result.external_id == VIDEO_ID
    assert result.external_url == f"https://youtu.be/{VIDEO_ID}"

    # Verify init request contains correct metadata
    import json

    init_body = json.loads(init_route.calls.last.request.content)
    assert init_body["snippet"]["title"] == "My Video"
    assert init_body["snippet"]["description"] == "My YouTube video description"
    assert "tech" in init_body["snippet"]["tags"]
    assert init_body["status"]["privacyStatus"] == "public"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_scheduled():
    """privacyStatus=private and publishAt set when scheduled_at is present."""
    init_route = _mock_resumable_init()
    _mock_resumable_upload()
    _mock_video_download()

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=7)
    publisher = YouTubePublisher(_settings())
    item = _make_queue_item(scheduled_at=scheduled_time)
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True

    import json

    init_body = json.loads(init_route.calls.last.request.content)
    assert init_body["status"]["privacyStatus"] == "private"
    assert init_body["status"]["publishAt"] == scheduled_time.isoformat()

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_quota_exceeded_403():
    """QuotaExhaustedError when 403 with quotaExceeded reason."""
    _mock_resumable_init(
        status=403,
        headers={},
        json_body={
            "error": {
                "errors": [{"reason": "quotaExceeded", "domain": "youtube.quota"}],
                "code": 403,
                "message": "The request cannot be completed because you have exceeded your quota.",
            }
        },
    )
    _mock_video_download()

    publisher = YouTubePublisher(_settings())
    item = _make_queue_item()

    with pytest.raises(QuotaExhaustedError, match="daily upload limit"):
        await publisher._do_publish(item, CREDENTIALS)

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_first_comment():
    """Mock commentThreads endpoint after successful upload."""
    _mock_resumable_init()
    _mock_resumable_upload()
    _mock_video_download()

    comment_route = respx.post(
        "https://www.googleapis.com/youtube/v3/commentThreads"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"id": "comment-thread-123"},
        )
    )

    publisher = YouTubePublisher(_settings())
    item = _make_queue_item(first_comment="First comment on my video!")
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert comment_route.called

    import json

    comment_body = json.loads(comment_route.calls.last.request.content)
    snippet = comment_body["snippet"]
    assert snippet["videoId"] == VIDEO_ID
    assert snippet["topLevelComment"]["snippet"]["textOriginal"] == "First comment on my video!"

    await publisher.close()
