"""Monitor execution worker — processes sources and ingests mentions."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import TYPE_CHECKING, Callable
from uuid import UUID

from .exceptions import MentionFetchError
from .models import DataSource, Monitor, RawMention
from .query_builder import build_monitor_query
from .query_sanitizer import (
    QueryValidationError,
    sanitize_for_apify,
    sanitize_for_newsdata,
    sanitize_for_trustpilot,
    sanitize_for_xpoz,
)

if TYPE_CHECKING:
    from ..billing.repository import BillingRepository

    from .alerts.evaluator import AlertEvaluator
    from .repository import PostgresMonitoringRepository
    from .service import MonitoringService

logger = logging.getLogger(__name__)

DEADLINE_SECONDS = 240  # Leave 60s buffer below Cloud Run 300s
MENTIONS_PER_PAGE = 100

# Map DataSource → sanitizer function (only adapters that exist today)
_SANITIZERS: dict[DataSource, Callable[[str], str]] = {
    DataSource.NEWSDATA: sanitize_for_newsdata,
    DataSource.TWITTER: sanitize_for_xpoz,
    DataSource.INSTAGRAM: sanitize_for_xpoz,
    DataSource.REDDIT: sanitize_for_xpoz,
    DataSource.TIKTOK: sanitize_for_xpoz,
    DataSource.YOUTUBE: sanitize_for_xpoz,
    DataSource.TRUSTPILOT: sanitize_for_trustpilot,
    DataSource.APP_STORE: sanitize_for_apify,
    DataSource.PLAY_STORE: sanitize_for_apify,
    DataSource.GOOGLE_TRENDS: sanitize_for_apify,
}

# Hard cap: even on billing failure, don't allow runaway ingestion.
# Matches FREE tier limit so fail-safe never exceeds unpaid quota.
_HARD_CAP_MENTIONS = 5_000


def _classify_error(exc: BaseException) -> str:
    """Map an exception to a safe, user-facing error code.

    Full exception details are logged server-side; only the code is stored
    in ``monitor_runs.error_details`` to avoid leaking internal information.
    """
    if isinstance(exc, TimeoutError):
        return "source_timeout"
    if isinstance(exc, ConnectionError):
        return "connection_error"
    if "rate limit" in str(exc).lower():
        return "rate_limited"
    if isinstance(exc, MentionFetchError):
        return "fetch_error"
    if isinstance(exc, QueryValidationError):
        return "invalid_query"
    return "source_error"


class MonitorWorker:
    """Processes all sources for a single monitor."""

    def __init__(
        self,
        repository: PostgresMonitoringRepository,
        service: MonitoringService,
        adapters: dict,
        billing_repo: BillingRepository | None = None,
        evaluator: AlertEvaluator | None = None,
    ) -> None:
        self._repo = repository
        self._service = service
        self._adapters = adapters
        self._billing_repo = billing_repo
        self._evaluator = evaluator

    async def process_monitor(self, monitor_id: UUID) -> dict:
        """Process all sources for a monitor. Returns run summary."""
        deadline = time.monotonic() + DEADLINE_SECONDS

        # 1. Load monitor (system-level, no user_id check)
        monitor = await self._repo.get_monitor_by_id_system(monitor_id)
        if monitor is None:
            logger.warning("Monitor %s not found (deleted?)", monitor_id)
            await self._repo.fail_run(monitor_id, error="monitor_not_found")
            return {"status": "skipped", "reason": "not_found"}

        if not monitor.is_active:
            logger.info("Monitor %s is inactive, skipping", monitor_id)
            await self._repo.fail_run(monitor_id, error="monitor_inactive")
            return {"status": "skipped", "reason": "inactive"}

        # 2. Check billing quota (advisory)
        quota_ok = await self._check_mention_quota(monitor.user_id)
        if not quota_ok:
            logger.info(
                "Monitor %s user %s at mention limit", monitor_id, monitor.user_id
            )
            await self._repo.complete_run_and_advance(
                monitor_id, 0, 0, 0,
                error_details={"reason": "mention_quota_exceeded"},
            )
            return {"status": "skipped", "reason": "quota_exceeded"}

        # 3. Filter sources to those with available adapters
        sources = [s for s in monitor.sources if s in self._adapters]
        if not sources:
            logger.warning("Monitor %s has no available adapters", monitor_id)
            await self._repo.complete_run_and_advance(monitor_id, 0, 0, 0)
            return {"status": "completed", "reason": "no_sources"}

        # 4. Process sources in parallel with failure isolation
        tasks = [
            self._process_source(monitor, source, deadline) for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Aggregate results
        total_mentions = 0
        succeeded = 0
        failed = 0
        errors: dict[str, str] = {}

        for source, result in zip(sources, results):
            if isinstance(result, BaseException):
                failed += 1
                errors[source.value] = _classify_error(result)
                logger.error(
                    "Source %s failed for monitor %s: %s",
                    source.value,
                    monitor_id,
                    result,
                )
            else:
                succeeded += 1
                total_mentions += result

        # 6. Complete run + advance next_run_at (single transaction)
        await self._repo.complete_run_and_advance(
            monitor_id,
            total_mentions,
            succeeded,
            failed,
            error_details=errors if errors else None,
        )

        result_summary = {
            "status": "completed",
            "mentions_ingested": total_mentions,
            "sources_succeeded": succeeded,
            "sources_failed": failed,
        }

        # 7. Evaluate alert rules (fire-and-forget, don't block run completion)
        if total_mentions > 0 and self._evaluator is not None:
            try:
                alerts_fired = await self._evaluator.evaluate_monitor(
                    monitor_id, result_summary
                )
                if alerts_fired > 0:
                    logger.info(
                        "Fired %d alerts for monitor %s", alerts_fired, monitor_id
                    )
                # Await all delivery tasks before returning (Cloud Run may kill container)
                await self._evaluator.wait_pending_deliveries()
            except Exception:
                logger.exception("Alert evaluation failed for monitor %s", monitor_id)

        return result_summary

    async def _process_source(
        self,
        monitor: Monitor,
        source: DataSource,
        deadline: float,
    ) -> int:
        """Process a single source. Returns count of ingested mentions."""
        if time.monotonic() > deadline:
            raise TimeoutError("Worker deadline exceeded")

        adapter = self._adapters[source]

        # Sanitize query for this API
        sanitizer = _SANITIZERS.get(source, sanitize_for_apify)
        raw_query = build_monitor_query(monitor)
        sanitized_query = sanitizer(raw_query)

        # Load cursor
        cursor = await self._repo.get_cursor(monitor.id, source)
        cursor_value = cursor.cursor_value if cursor else None

        # Fetch mentions with pagination
        total_ingested = 0
        current_cursor = cursor_value

        while True:
            if time.monotonic() > deadline:
                logger.warning(
                    "Deadline during pagination for %s/%s",
                    monitor.id,
                    source.value,
                )
                break

            raw_mentions, next_cursor = await adapter.fetch_mentions(
                query=sanitized_query,
                cursor=current_cursor,
                limit=MENTIONS_PER_PAGE,
            )

            if not raw_mentions:
                break

            # Pre-persistence: extract video URLs from mentions (PR-071)
            from .bridge import enrich_mentions_with_video_urls

            enrich_mentions_with_video_urls(raw_mentions)

            # EF5: Filter retweets, exact dupes, short content before ingestion
            raw_mentions = self._filter_mentions(raw_mentions)

            # Ingest batch (service handles dedup + insert + cursor advance)
            count = await self._service.ingest_mentions(
                monitor_id=monitor.id,
                raw_mentions=raw_mentions,
                source=source,
                cursor_value=next_cursor,
            )
            total_ingested += count

            if not next_cursor or next_cursor == current_cursor:
                break
            current_cursor = next_cursor

        return total_ingested

    @staticmethod
    def _filter_mentions(mentions: list[RawMention]) -> list[RawMention]:
        """Drop retweets, exact duplicates, too-short content."""
        seen_hashes: set[str] = set()
        kept: list[RawMention] = []
        retweets = dupes = short = 0
        for m in mentions:
            if m.metadata and m.metadata.get("is_retweet"):
                retweets += 1
                continue
            if len(m.content or "") < 10:
                short += 1
                continue
            h = hashlib.sha256((m.content or "")[:200].encode()).hexdigest()
            if h in seen_hashes:
                dupes += 1
                continue
            seen_hashes.add(h)
            kept.append(m)
        if retweets or dupes or short:
            logger.info(
                "Filtered %d mentions: %d retweets, %d dupes, %d short",
                retweets + dupes + short, retweets, dupes, short,
            )
        return kept

    async def _check_mention_quota(self, user_id: UUID) -> bool:
        """Advisory quota check — returns False if user at mention limit.

        Looks up the user's actual subscription tier so Pro users get their
        500K mention/month quota.  On any failure (DB error, missing billing
        repo) falls back to ``_HARD_CAP_MENTIONS`` (FREE-tier limit) using
        the already-fetched count — never re-calls the DB in the except block.
        """
        from ..billing.tiers import Tier, get_tier_config

        # 1. Fetch current mention count *once* — reused in both paths.
        count = await self._repo.count_mentions_this_month(user_id)

        # 2. Try to resolve the user's actual tier.
        try:
            if self._billing_repo is not None:
                subscription = await self._billing_repo.get_subscription(user_id)
                tier = subscription.tier if subscription else Tier.FREE
            else:
                tier = Tier.FREE
            tier_config = get_tier_config(tier)
            return count < tier_config.max_mentions_per_month
        except Exception:
            logger.warning(
                "Tier lookup failed for user %s, using hard cap", user_id
            )
            return count < _HARD_CAP_MENTIONS
