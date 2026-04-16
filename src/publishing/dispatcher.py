"""Publish dispatcher — claims scheduled items and publishes them."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from .config import PublishingSettings
from .repository import PostgresPublishingRepository
from .service import PublishingService

logger = logging.getLogger(__name__)

STALE_THRESHOLD_MINUTES = 15


class PublishDispatcher:
    """Claims scheduled items and publishes them. Called by Cloud Scheduler cron."""

    def __init__(
        self,
        service: PublishingService,
        repository: PostgresPublishingRepository,
        settings: PublishingSettings | None = None,
    ) -> None:
        self._service = service
        self._repo = repository
        self._settings = settings or PublishingSettings()

    async def dispatch(self) -> dict:
        """Main dispatch loop. Returns summary dict."""
        deadline = time.monotonic() + self._settings.dispatch_deadline_seconds
        now = datetime.now(timezone.utc)

        # 0. Reap stale items stuck in 'publishing' (Cloud Run crash recovery)
        reaped = await self._repo.reap_stale_publishing_items(
            threshold_minutes=STALE_THRESHOLD_MINUTES, now=now
        )
        if reaped:
            logger.warning("publish_dispatch_reaped_stale: count=%d", reaped)

        # 1. Claim batch of scheduled + retryable items (FOR UPDATE SKIP LOCKED)
        items = await self._repo.claim_scheduled_items(
            batch_size=self._settings.dispatch_batch_size, now=now
        )

        published = 0
        failed = 0

        for item in items:
            if time.monotonic() > deadline:
                logger.warning(
                    "publish_dispatch_deadline: published=%d, failed=%d, remaining=%d",
                    published, failed, len(items) - published - failed,
                )
                break

            try:
                result = await self._service.publish_item(item.id)
                if result.success:
                    published += 1
                else:
                    failed += 1
            except Exception:
                logger.warning(
                    "publish_dispatch_error: item_id=%s",
                    item.id,
                    exc_info=True,
                )
                await self._repo.mark_failed(item.id, "Dispatch error")
                failed += 1

        return {
            "dispatched": len(items),
            "published": published,
            "failed": failed,
        }
