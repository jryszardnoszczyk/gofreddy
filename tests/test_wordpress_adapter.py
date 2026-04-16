"""Tests for WordPress REST API adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from src.publishing.adapters.wordpress import WordPressPublisher
from src.publishing.config import PublishingSettings
from src.publishing.exceptions import CredentialError
from src.publishing.models import PublishPlatform, PublishStatus, QueueItem


@pytest.fixture
def settings():
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
        wordpress_timeout_seconds=5.0,
    )


@pytest.fixture
def publisher(settings):
    return WordPressPublisher(settings)


def _make_item(**kwargs) -> QueueItem:
    from datetime import datetime, timezone
    defaults = dict(
        id=uuid4(), org_id=uuid4(), client_id=None, platform="wordpress",
        connection_id=uuid4(), content_parts=[{"body": "<p>Hello World</p>"}],
        media=[], first_comment=None, thumbnail_url=None,
        og_title="Test Post", og_description="A test post",
        og_image_url=None, twitter_card_type=None,
        canonical_url="https://example.com/test", slug="test-post",
        labels=[], group_id=None, newsletter_subject=None,
        newsletter_segment=None, status=PublishStatus.PUBLISHING,
        approved_at=datetime.now(timezone.utc), approved_by=uuid4(),
        scheduled_at=datetime.now(timezone.utc), external_id=None,
        external_url=None, error_message=None, retry_count=0,
        metadata={}, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return QueueItem(**defaults)


CREDENTIALS = {
    "site_url": "https://example.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx",
}


class TestWordPressPublisher:
    def test_platform(self, publisher):
        assert publisher.platform == PublishPlatform.WORDPRESS

    @pytest.mark.asyncio
    async def test_successful_publish(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            201,
            json={"id": 42, "link": "https://example.com/test-post"},
            request=httpx.Request("POST", "https://example.com/wp-json/wp/v2/posts"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        result = await publisher._do_publish(item, CREDENTIALS)

        assert result.success is True
        assert result.external_id == "42"
        assert result.external_url == "https://example.com/test-post"

    @pytest.mark.asyncio
    async def test_yoast_meta_in_request(self, publisher):
        item = _make_item(
            og_title="SEO Title",
            og_description="SEO Description",
            canonical_url="https://example.com/canonical",
        )
        mock_resp = httpx.Response(
            201,
            json={"id": 1, "link": "https://example.com/1"},
            request=httpx.Request("POST", "https://example.com/wp-json/wp/v2/posts"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        await publisher._do_publish(item, CREDENTIALS)

        call_args = publisher._client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert "meta" in payload
        assert payload["meta"]["_yoast_wpseo_opengraph-title"] == "SEO Title"
        assert payload["meta"]["_yoast_wpseo_canonical"] == "https://example.com/canonical"

    @pytest.mark.asyncio
    async def test_401_raises_credential_error(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            401,
            json={"code": "rest_not_logged_in"},
            request=httpx.Request("POST", "https://example.com/wp-json/wp/v2/posts"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(CredentialError, match="authentication failed"):
            await publisher._do_publish(item, CREDENTIALS)

    @pytest.mark.asyncio
    async def test_missing_credentials(self, publisher):
        item = _make_item()
        with pytest.raises(CredentialError, match="Missing"):
            await publisher._do_publish(item, {"site_url": "https://example.com"})

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, publisher):
        mock_resp = httpx.Response(
            200,
            json={"id": 1, "name": "admin"},
            request=httpx.Request("GET", "https://example.com/wp-json/wp/v2/users/me"),
        )
        publisher._client = AsyncMock()
        publisher._client.get = AsyncMock(return_value=mock_resp)

        result = await publisher.validate_credentials(CREDENTIALS)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_credentials_failure(self, publisher):
        mock_resp = httpx.Response(
            401,
            json={},
            request=httpx.Request("GET", "https://example.com/wp-json/wp/v2/users/me"),
        )
        publisher._client = AsyncMock()
        publisher._client.get = AsyncMock(return_value=mock_resp)

        result = await publisher.validate_credentials(CREDENTIALS)
        assert result is False
