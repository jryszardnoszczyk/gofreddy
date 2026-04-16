"""Monitor dispatch — fans out due monitors to Cloud Tasks."""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..jobs.task_client import MonitorTaskClient

from .repository import PostgresMonitoringRepository

logger = logging.getLogger(__name__)

MAX_DISPATCH_PER_CYCLE = 50
STALE_RUN_THRESHOLD_MINUTES = 45
MAX_JITTER_SECONDS = 600
DEADLINE_SECONDS = 240  # Leave 60s buffer below Cloud Run 300s limit


class MonitorDispatcher:
    """Queries due monitors and fans out execution tasks."""

    def __init__(
        self,
        repository: PostgresMonitoringRepository,
        task_client: MonitorTaskClient,
    ) -> None:
        self._repo = repository
        self._task_client = task_client

    async def dispatch(self) -> dict:
        """Main dispatch loop. Returns summary dict."""
        deadline = time.monotonic() + DEADLINE_SECONDS

        # 1. Mark stale runs as failed (>45 min running)
        stale_count = await self._repo.mark_stale_runs_failed(
            threshold_minutes=STALE_RUN_THRESHOLD_MINUTES
        )
        if stale_count:
            logger.warning("Marked %d stale monitor runs as failed", stale_count)

        # 2. Query due monitors (next_run_at <= NOW(), is_active, ordered oldest first)
        due_monitors = await self._repo.get_due_monitors(
            limit=MAX_DISPATCH_PER_CYCLE
        )

        dispatched = 0
        skipped = 0

        for monitor in due_monitors:
            if time.monotonic() > deadline:
                logger.warning(
                    "Dispatch deadline reached after %d monitors", dispatched
                )
                break

            # 3. Attempt to create a 'running' row (partial unique index prevents dups)
            created = await self._repo.try_create_run(monitor.id)
            if not created:
                skipped += 1  # Already running
                continue

            # 4. Enqueue Cloud Task with jitter
            jitter = random.randint(0, MAX_JITTER_SECONDS)
            try:
                await self._task_client.enqueue_monitor_run(
                    monitor_id=monitor.id, delay_seconds=jitter
                )
                dispatched += 1
            except Exception:
                logger.exception(
                    "Failed to enqueue task for monitor %s", monitor.id
                )
                # Clean up the run we just created
                await self._repo.fail_run(monitor.id, error="task_enqueue_failed")
                skipped += 1

        return {
            "dispatched": dispatched,
            "skipped": skipped,
            "stale_recovered": stale_count,
            "total_due": len(due_monitors),
        }
