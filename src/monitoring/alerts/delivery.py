"""Webhook delivery — HMAC-signed, SSRF-protected, with retry and circuit breaker."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx

if TYPE_CHECKING:
    from ..config import MonitoringSettings
    from ..repository import PostgresMonitoringRepository

from ..exceptions import WebhookDeliveryError
from .models import AlertEvent, AlertRule

logger = logging.getLogger(__name__)


class WebhookDelivery:
    """HMAC-signed webhook delivery with SSRF protection and retry."""

    RETRY_DELAYS = [1, 5, 25]  # seconds

    def __init__(
        self,
        settings: MonitoringSettings,
        repository: PostgresMonitoringRepository,
    ) -> None:
        self._settings = settings
        self._repo = repository
        self._client = httpx.AsyncClient(
            verify=True,
            timeout=settings.webhook_timeout_seconds,
            follow_redirects=False,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def deliver(self, event: AlertEvent, rule: AlertRule) -> bool:
        """Deliver webhook with retries. Returns True on success."""
        for attempt in range(len(self.RETRY_DELAYS)):
            try:
                success = await self._attempt_delivery(event, rule)
                if success:
                    await self._repo.update_alert_event_status(
                        event.id, "delivered", attempt + 1
                    )
                    await self._repo.reset_consecutive_failures(rule.id)
                    return True
            except Exception:
                logger.warning(
                    "Webhook delivery attempt %d failed for event %s",
                    attempt + 1, event.id,
                )

            # Wait before retry (except after last attempt)
            if attempt < len(self.RETRY_DELAYS):
                await asyncio.sleep(self.RETRY_DELAYS[attempt])

        # All retries exhausted
        await self._repo.update_alert_event_status(
            event.id, "failed", len(self.RETRY_DELAYS)
        )
        new_count = await self._repo.increment_consecutive_failures(rule.id)

        # Circuit breaker: disable after N consecutive failures
        if new_count >= self._settings.webhook_circuit_breaker_threshold:
            await self._repo.disable_rule(rule.id)
            logger.warning(
                "Webhook disabled after %d consecutive failures: rule %s",
                new_count, rule.id,
            )
        return False

    async def _attempt_delivery(self, event: AlertEvent, rule: AlertRule) -> bool:
        """Single delivery attempt with SSRF validation and HMAC signing."""
        from ...common.url_validation import resolve_and_validate

        # 1. SSRF: validate URL on EVERY attempt (DNS can change)
        await resolve_and_validate(rule.webhook_url)

        # 2. Build signed request
        body_bytes = json.dumps(event.payload, separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        signature = self._sign(timestamp, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": timestamp,
            "X-Signature-256": signature,
            "User-Agent": "VideoIntelligence-Webhook/1.0",
        }

        response = await self._client.post(rule.webhook_url, content=body_bytes, headers=headers)
        return 200 <= response.status_code < 300

    def _sign(self, timestamp: str, body_bytes: bytes) -> str:
        """HMAC-SHA256: sign(secret, timestamp + '.' + body)."""
        secret = self._settings.webhook_signing_secret.get_secret_value()
        if not secret:
            raise WebhookDeliveryError("WEBHOOK_SIGNING_SECRET not configured")
        message = f"{timestamp}.".encode() + body_bytes
        sig = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    async def send_test(self, rule: AlertRule) -> bool:
        """Send a test webhook (bypasses cooldown, does not create event)."""
        test_event = AlertEvent(
            id=uuid4(),
            rule_id=rule.id,
            monitor_id=rule.monitor_id,
            triggered_at=datetime.now(UTC),
            condition_summary="Test webhook delivery",
            payload={
                "alert_type": "test",
                "monitor_id": str(rule.monitor_id),
                "rule_id": str(rule.id),
                "message": "This is a test webhook from Freddy.",
            },
            delivery_status="pending",
            delivery_attempts=0,
            last_delivery_at=None,
            created_at=datetime.now(UTC),
        )
        return await self._attempt_delivery(test_event, rule)
