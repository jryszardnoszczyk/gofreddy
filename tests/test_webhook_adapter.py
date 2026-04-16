"""Tests for webhook/HTTP POST adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from src.publishing.adapters.webhook import WebhookPublisher
from src.publishing.config import PublishingSettings
from src.publishing.exceptions import AdapterError
from src.publishing.models import PublishPlatform, PublishStatus, QueueItem


@pytest.fixture
def settings():
    return PublishingSettings(
        enabled=True,
        encryption_secret="test-secret-key-for-publishing",
        webhook_timeout_seconds=5.0,
    )


@pytest.fixture
def publisher(settings):
    return WebhookPublisher(settings)


def _make_item(**kwargs) -> QueueItem:
    from datetime import datetime, timezone
    defaults = dict(
        id=uuid4(), org_id=uuid4(), client_id=None, platform="webhook",
        connection_id=uuid4(), content_parts=[{"body": "Hello World"}],
        media=[], first_comment=None, thumbnail_url=None,
        og_title="Test", og_description=None, og_image_url=None,
        twitter_card_type=None, canonical_url=None, slug=None,
        labels=["tag1"], group_id=None, newsletter_subject=None,
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
    "webhook_url": "https://hooks.example.com/publish",
    "signing_secret": "whsec_test123",
}


class TestWebhookPublisher:
    def test_platform(self, publisher):
        assert publisher.platform == PublishPlatform.WEBHOOK

    def test_hmac_signature_computation(self, publisher):
        body = b'{"test": true}'
        secret = "my-secret"
        sig = publisher._compute_signature(body, secret)
        expected = hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        assert sig == expected

    @pytest.mark.asyncio
    async def test_successful_publish(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            200,
            json={"external_id": "ext-123"},
            request=httpx.Request("POST", "https://hooks.example.com/publish"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.return_value = ("93.184.216.34", "hooks.example.com")
            result = await publisher._do_publish(item, CREDENTIALS)

        assert result.success is True
        assert result.external_id == "ext-123"

    @pytest.mark.asyncio
    async def test_idempotency_key_header(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            200, json={},
            request=httpx.Request("POST", "https://hooks.example.com/publish"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.return_value = ("93.184.216.34", "hooks.example.com")
            await publisher._do_publish(item, CREDENTIALS)

        call_kwargs = publisher._client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["X-Idempotency-Key"] == str(item.id)

    @pytest.mark.asyncio
    async def test_signature_header_present(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            200, json={},
            request=httpx.Request("POST", "https://hooks.example.com/publish"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.return_value = ("93.184.216.34", "hooks.example.com")
            await publisher._do_publish(item, CREDENTIALS)

        call_kwargs = publisher._client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert "X-Signature-256" in headers
        assert headers["X-Signature-256"].startswith("sha256=")

    @pytest.mark.asyncio
    async def test_ssrf_rejection(self, publisher):
        item = _make_item()
        creds = {"webhook_url": "https://169.254.169.254/latest/meta-data/"}

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.side_effect = ValueError("Blocked private IP")
            with pytest.raises(AdapterError, match="validation failed"):
                await publisher._do_publish(item, creds)

    @pytest.mark.asyncio
    async def test_non_2xx_raises(self, publisher):
        item = _make_item()
        mock_resp = httpx.Response(
            500, text="Internal Server Error",
            request=httpx.Request("POST", "https://hooks.example.com/publish"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.return_value = ("93.184.216.34", "hooks.example.com")
            with pytest.raises(AdapterError, match="500"):
                await publisher._do_publish(item, CREDENTIALS)

    @pytest.mark.asyncio
    async def test_payload_contains_html_and_markdown(self, publisher):
        item = _make_item(content_parts=[{"body": "# Hello"}])
        mock_resp = httpx.Response(
            200, json={},
            request=httpx.Request("POST", "https://hooks.example.com/publish"),
        )
        publisher._client = AsyncMock()
        publisher._client.post = AsyncMock(return_value=mock_resp)

        with patch("src.publishing.adapters.webhook.resolve_and_validate", new_callable=AsyncMock) as mock_ssrf:
            mock_ssrf.return_value = ("93.184.216.34", "hooks.example.com")
            await publisher._do_publish(item, CREDENTIALS)

        call_kwargs = publisher._client.post.call_args
        body_bytes = call_kwargs.kwargs.get("content") or call_kwargs[1].get("content")
        payload = json.loads(body_bytes)
        assert "html" in payload
        assert "markdown" in payload
        assert payload["html"] == "# Hello"
        assert payload["markdown"] == "# Hello"
