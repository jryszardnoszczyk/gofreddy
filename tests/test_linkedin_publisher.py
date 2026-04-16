"""Tests for LinkedInPublisher adapter — mock HTTP with respx."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest
import respx

from src.publishing.adapters.linkedin import LinkedInPublisher
from src.publishing.config import PublishingSettings
from src.publishing.exceptions import CredentialError
from src.publishing.models import PublishPlatform, PublishStatus, QueueItem


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
        platform="linkedin",
        connection_id=uuid4(),
        content_parts=[{"body": "Hello LinkedIn world"}],
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


CREDENTIALS = {"access_token": "tok_test_123", "member_id": "abc123"}


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_text_post():
    """POST /rest/posts with correct commentary and author URN."""
    post_urn = "urn:li:share:7000000000000000000"
    respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(
            201,
            headers={"x-restli-id": post_urn},
        )
    )

    publisher = LinkedInPublisher(_settings())
    item = _make_queue_item(content_parts=[{"body": "Test post body"}])
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert result.external_id == post_urn
    assert post_urn in (result.external_url or "")

    # Verify request payload
    req = respx.calls.last.request
    import json

    body = json.loads(req.content)
    assert body["author"] == "urn:li:person:abc123"
    assert body["commentary"] == "Test post body"
    assert body["visibility"] == "PUBLIC"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_article_share():
    """content.article.source is set when URL present in content_parts."""
    post_urn = "urn:li:share:7000000000000000001"
    route = respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(
            201,
            headers={"x-restli-id": post_urn},
        )
    )

    publisher = LinkedInPublisher(_settings())
    item = _make_queue_item(
        content_parts=[
            {"body": "Check this out", "url": "https://example.com/article"}
        ],
        og_title="Example Article",
        og_description="A great article",
    )
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True

    import json

    body = json.loads(route.calls.last.request.content)
    assert body["content"]["article"]["source"] == "https://example.com/article"
    assert body["content"]["article"]["title"] == "Example Article"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_first_comment():
    """first_comment triggers POST to socialActions comments endpoint."""
    post_urn = "urn:li:share:7000000000000000002"
    respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(
            201,
            headers={"x-restli-id": post_urn},
        )
    )
    comment_route = respx.post(
        f"https://api.linkedin.com/rest/socialActions/{post_urn}/comments"
    ).mock(
        return_value=httpx.Response(
            201,
            headers={"x-restli-id": "comment-urn-123"},
        )
    )

    publisher = LinkedInPublisher(_settings())
    item = _make_queue_item(first_comment="Great first comment!")
    result = await publisher._do_publish(item, CREDENTIALS)

    assert result.success is True
    assert comment_route.called

    import json

    comment_body = json.loads(comment_route.calls.last.request.content)
    assert comment_body["message"]["text"] == "Great first comment!"
    assert comment_body["actor"] == "urn:li:person:abc123"

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_publish_401_raises_credential_error():
    """401 response raises CredentialError."""
    respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )

    publisher = LinkedInPublisher(_settings())
    item = _make_queue_item()

    with pytest.raises(CredentialError, match="expired or invalid"):
        await publisher._do_publish(item, CREDENTIALS)

    await publisher.close()


@pytest.mark.mock_required
@pytest.mark.asyncio
@respx.mock
async def test_validate_credentials():
    """GET /v2/userinfo returns 200 -> True."""
    respx.get("https://api.linkedin.com/v2/userinfo").mock(
        return_value=httpx.Response(200, json={"sub": "abc123"})
    )

    publisher = LinkedInPublisher(_settings())
    valid = await publisher.validate_credentials(CREDENTIALS)
    assert valid is True

    await publisher.close()
