"""Generic webhook/HTTP POST adapter with HMAC-SHA256 signing."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx

from ...common.url_validation import resolve_and_validate
from ..config import PublishingSettings
from ..exceptions import AdapterError, CredentialError
from ..models import PublishPlatform, PublishResult, QueueItem
from ..publisher_protocol import BasePublisher

logger = logging.getLogger(__name__)


class WebhookPublisher(BasePublisher):
    """Generic HTTP POST adapter for custom webhook receivers.

    Credentials dict keys: webhook_url, signing_secret (optional).
    Signing secret is per-connection — not a global config value.
    """

    def __init__(self, settings: PublishingSettings | None = None) -> None:
        super().__init__(settings)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                (self._settings or PublishingSettings()).webhook_timeout_seconds
            ),
            follow_redirects=False,  # Prevent redirect-based SSRF bypass
        )

    @property
    def platform(self) -> PublishPlatform:
        return PublishPlatform.WEBHOOK

    @staticmethod
    def _compute_signature(body_bytes: bytes, secret: str) -> str:
        return hmac.new(
            secret.encode("utf-8"), body_bytes, hashlib.sha256
        ).hexdigest()

    async def _do_publish(
        self, item: QueueItem, credentials: dict[str, str]
    ) -> PublishResult:
        webhook_url = credentials.get("webhook_url", "")
        signing_secret = credentials.get("signing_secret", "")

        if not webhook_url:
            raise CredentialError("Missing webhook_url")

        # SSRF pre-flight check — validates IP, requires HTTPS
        try:
            await resolve_and_validate(webhook_url)
        except ValueError as e:
            raise AdapterError(f"Webhook URL validation failed: {e}") from e

        body_text = ""
        if item.content_parts:
            body_text = item.content_parts[0].get("body", "")

        payload = {
            "id": str(item.id),
            "idempotency_key": str(item.id),
            "platform": item.platform,
            "content_parts": item.content_parts,
            "media": item.media,
            "html": body_text,
            "markdown": body_text,
            "metadata": {
                "og_title": item.og_title,
                "og_description": item.og_description,
                "og_image_url": item.og_image_url,
                "canonical_url": item.canonical_url,
                "slug": item.slug,
                "twitter_card_type": item.twitter_card_type,
                "labels": item.labels,
            },
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        body_bytes = json.dumps(payload, default=str).encode("utf-8")

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(item.id),
        }
        if signing_secret:
            sig = self._compute_signature(body_bytes, signing_secret)
            headers["X-Signature-256"] = f"sha256={sig}"

        # POST to original hostname (not resolved IP — breaks TLS SNI)
        resp = await self._client.post(
            webhook_url, content=body_bytes, headers=headers
        )

        if resp.status_code < 200 or resp.status_code >= 300:
            raise AdapterError(f"Webhook returned {resp.status_code}")

        # Parse optional external_id/external_url from response
        external_id = None
        external_url = None
        try:
            resp_data = resp.json()
            external_id = resp_data.get("external_id")
            external_url = resp_data.get("external_url")
        except Exception:
            pass

        return PublishResult(
            success=True,
            external_id=external_id,
            external_url=external_url,
        )

    async def validate_credentials(self, credentials: dict[str, str]) -> bool:
        webhook_url = credentials.get("webhook_url", "")
        signing_secret = credentials.get("signing_secret", "")

        if not webhook_url:
            return False

        try:
            await resolve_and_validate(webhook_url)
        except ValueError:
            return False

        test_payload = {
            "event": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        body_bytes = json.dumps(test_payload).encode("utf-8")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if signing_secret:
            sig = self._compute_signature(body_bytes, signing_secret)
            headers["X-Signature-256"] = f"sha256={sig}"

        try:
            resp = await self._client.post(
                webhook_url, content=body_bytes, headers=headers
            )
            return 200 <= resp.status_code < 300
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
