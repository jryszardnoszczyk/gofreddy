"""Batch processing worker with bounded concurrency and rate limiting."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid as _uuid
from typing import TYPE_CHECKING, Any, Awaitable, Callable
from uuid import UUID

from aiolimiter import AsyncLimiter

from ..analysis.exceptions import GeminiRateLimitError
from ..common.enums import Platform
from ..fetcher.exceptions import FetcherError, RateLimitError, VideoUnavailableError
from .config import BatchSettings
from .models import BatchItem, BatchJob, BatchStatus, ItemStatus

if TYPE_CHECKING:
    from ..analysis.service import AnalysisService
    from ..billing.credits.config import BillingFlags, CreditSettings
    from ..billing.credits.service import CreditService
    from ..billing.service import BillingService
    from ..fetcher import VideoFetcher
    from ..workspace.repository import PostgresWorkspaceRepository
    from .repository import PostgresBatchRepository

logger = logging.getLogger(__name__)

# Module-level dict for background task lifecycle management
_active_workers: dict[UUID, asyncio.Task] = {}

# Transient errors that should be retried with exponential backoff
# Only genuinely transient errors — VideoProcessingError (bad video, parse failure)
# and IntegrityError are permanent and should NOT be retried.
_TRANSIENT_ERRORS = (
    GeminiRateLimitError,
    RateLimitError,
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
)

# Permanent errors that mark items FAILED/SKIPPED immediately
_PERMANENT_SKIP = (VideoUnavailableError,)

# Lazy import alias for billing exception (catch before generic Exception)
try:
    from ..billing.credits.exceptions import InsufficientCredits as _InsufficientCredits
except ImportError:  # billing module not installed
    _InsufficientCredits = type(None)  # type: ignore[assignment,misc]

# Fixed namespace for deterministic uuid5 (same video → same UUID across collections)
_BATCH_NS = _uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _handle_worker_done(batch_id: UUID, task: asyncio.Task) -> None:
    """Callback for worker task completion -- cleanup and crash logging."""
    _active_workers.pop(batch_id, None)
    if task.cancelled():
        logger.warning("batch_worker_cancelled", extra={"batch_id": str(batch_id)})
    elif exc := task.exception():
        logger.error(
            "batch_worker_crashed",
            extra={"batch_id": str(batch_id), "error": str(exc)},
        )


class BatchWorker:
    """Processes batch items with bounded concurrency and rate limiting.

    Runs as an asyncio.Task in the same process (not Cloud Tasks).
    Uses N independent workers (bounded by settings.concurrency) and
    AsyncLimiter for per-second rate limiting.
    """

    def __init__(
        self,
        batch_repository: "PostgresBatchRepository",
        analysis_service: AnalysisService,
        workspace_repository: PostgresWorkspaceRepository,
        billing_service: BillingService | None = None,
        settings: BatchSettings | None = None,
        credit_service: CreditService | None = None,
        credit_settings: CreditSettings | None = None,
        billing_flags: BillingFlags | None = None,
        fetchers: dict[Platform, "VideoFetcher"] | None = None,
    ) -> None:
        self._repo = batch_repository
        self._analysis = analysis_service
        self._ws_repo = workspace_repository
        self._billing = billing_service
        self._fetchers = fetchers
        self._settings = settings or BatchSettings()
        self._rate_limiter = AsyncLimiter(self._settings.rate_limit_per_sec, 1)
        self._credit_service = credit_service
        self._credit_settings = credit_settings
        self._billing_flags = billing_flags
        self._hybrid_enabled = bool(
            billing_flags
            and (billing_flags.hybrid_write_enabled or billing_flags.hybrid_read_enabled)
            and credit_service
            and credit_settings
        )

    # ── Main entry point ───────────────────────────────────────────────────

    async def process_batch(self, batch_id: UUID, user_id: UUID | None = None) -> BatchJob:
        """Main entry point. Continuous worker pool processes items until none remain.

        Uses N independent workers that each claim-process-repeat, so fast items
        don't wait for slow ones (no round-gating).
        """
        batch = await self._repo.update_batch_status(batch_id, BatchStatus.PROCESSING)
        if batch is None:
            logger.warning("batch_not_found_on_start", extra={"batch_id": str(batch_id)})
            raise RuntimeError(f"Batch {batch_id} not found")

        try:
            deadline = time.monotonic() + self._settings.deadline_seconds
            done_event = asyncio.Event()

            async def _worker() -> None:
                """Single worker: claim one item, process it, repeat."""
                while not done_event.is_set():
                    if time.monotonic() > deadline:
                        done_event.set()
                        return

                    items = await self._repo.claim_pending_items(
                        batch_id,
                        limit=1,
                        claim_timeout_seconds=self._settings.claim_timeout_seconds,
                    )
                    if not items:
                        done_event.set()
                        return

                    item = items[0]
                    try:
                        await self._process_item(item, batch_id, user_id)
                    except Exception as exc:
                        logger.error(
                            "batch_item_exception",
                            extra={
                                "batch_id": str(batch_id),
                                "item_id": str(item.id),
                                "error": str(exc),
                            },
                        )

            workers = [
                asyncio.create_task(_worker(), name=f"batch-worker-{i}")
                for i in range(self._settings.concurrency)
            ]
            await asyncio.gather(*workers)

            # Fail any remaining pending items if deadline was hit
            if time.monotonic() > deadline:
                logger.warning(
                    "batch_deadline_exceeded",
                    extra={"batch_id": str(batch_id)},
                )
                await self._repo.fail_pending_items(batch_id, "deadline exceeded")

            # Determine terminal status: CANCELLED if any items were cancelled,
            # otherwise COMPLETED (handles cancel_batch racing with worker loop)
            cancelled_items = await self._repo.get_items_by_status(batch_id, ItemStatus.CANCELLED)
            terminal_status = BatchStatus.CANCELLED if cancelled_items else BatchStatus.COMPLETED
            final = await self._repo.update_batch_status(batch_id, terminal_status)
            return final or batch

        except asyncio.CancelledError:
            logger.warning("batch_worker_cancelled", extra={"batch_id": str(batch_id)})
            # Mark remaining pending items as cancelled
            try:
                await self._repo.cancel_pending_items(batch_id)
                final = await self._repo.update_batch_status(batch_id, BatchStatus.CANCELLED)
                return final or batch
            except Exception:
                logger.exception("batch_cancel_cleanup_failed")
                return batch

        except Exception:
            logger.exception("batch_worker_error", extra={"batch_id": str(batch_id)})
            try:
                final = await self._repo.update_batch_status(batch_id, BatchStatus.FAILED)
                return final or batch
            except Exception:
                logger.exception("batch_fail_status_update_failed")
                return batch

    # ── Per-item processing ────────────────────────────────────────────────

    async def _process_item(
        self,
        item: BatchItem,
        batch_id: UUID,
        user_id: UUID | None,
    ) -> ItemStatus:
        """Process single item with rate limiter (concurrency bounded by worker count)."""
        await self._rate_limiter.acquire()

        try:
            result = await self._retry_with_backoff(
                self._analyze_item, item, user_id,
            )
            flagged = result.get("flagged", False)

            completed = await self._repo.complete_item_and_increment(
                item.id, batch_id, ItemStatus.SUCCEEDED,
                flagged=flagged,
                workspace_update={
                    "item_id": item.workspace_item_id,
                    "risk_score": result.get("risk_score", 0.0),
                    "analysis_results": json.dumps({
                        "analysis_id": result["record_id"],
                        "overall_safe": not flagged,
                    }),
                },
            )
            if completed is None:
                logger.warning(
                    "batch_item_cascade_deleted",
                    extra={"item_id": str(item.id), "batch_id": str(batch_id)},
                )

            return ItemStatus.SUCCEEDED

        except _TRANSIENT_ERRORS as e:
            # Already exhausted retries
            error_msg = f"Transient error after max retries: {type(e).__name__}: {str(e)[:200]}"
            await self._safe_complete_item(item.id, batch_id, ItemStatus.FAILED, error_msg)
            return ItemStatus.FAILED

        except _PERMANENT_SKIP as e:
            # Video unavailable -- platform issue, not user error
            error_msg = f"Video unavailable: {str(e)[:300]}"
            await self._safe_complete_item(item.id, batch_id, ItemStatus.SKIPPED, error_msg)
            return ItemStatus.SKIPPED

        except FetcherError as e:
            # Other fetcher errors (unsupported platform, etc.) -- skip
            error_msg = f"{type(e).__name__}: {str(e)[:300]}"
            await self._safe_complete_item(item.id, batch_id, ItemStatus.SKIPPED, error_msg)
            return ItemStatus.SKIPPED

        except _InsufficientCredits:
            # Billing error — not transient, not retried
            await self._safe_complete_item(
                item.id, batch_id, ItemStatus.FAILED, "Insufficient credits for analysis",
            )
            return ItemStatus.FAILED

        except Exception as e:
            # Unknown permanent error
            error_msg = f"{type(e).__name__}: {str(e)[:500]}"
            await self._safe_complete_item(item.id, batch_id, ItemStatus.FAILED, error_msg)
            return ItemStatus.FAILED

    async def _analyze_item(self, item: BatchItem, user_id: UUID | None) -> dict[str, Any]:
        """Analyze a single workspace item by looking up its details from the DB."""
        if item.workspace_item_id is None:
            raise ValueError("Workspace item ID is None")

        # Look up workspace item details via public method (not private _acquire_connection)
        source = await self._ws_repo.get_item_source(item.workspace_item_id)
        if source is None:
            raise ValueError(f"Workspace item {item.workspace_item_id} not found")

        video_id, platform_str = source
        platform = Platform(platform_str)

        # Fetch video to R2 before analysis (same as handle_analyze in tools.py)
        transcript_text = None
        duration_seconds = None
        video_title = None
        if self._fetchers:
            fetcher = self._fetchers.get(platform)
            if fetcher:
                video_result = await fetcher.fetch_video(platform, video_id)
                transcript_text = video_result.transcript_text
                duration_seconds = video_result.duration_seconds
                video_title = video_result.title

        # Deterministic UUID: same video shares analysis cache across collections
        video_uuid = _uuid.uuid5(_BATCH_NS, f"{platform.value}:{video_id}")

        result = await self._analysis.analyze(
            platform=platform,
            video_id=video_id,
            video_uuid=video_uuid,
            user_id=user_id,
            transcript_text=transcript_text,
            duration_seconds=duration_seconds,
            title=video_title,
        )

        # Per-item credit billing (fail-closed, DD-4: cache-then-reserve)
        if not result.cached and user_id and self._hybrid_enabled:
            from ..billing.credits.exceptions import InvalidReservationState
            from ..billing.credits.helpers import determine_actual_cost

            reservation = await self._credit_service.authorize_usage(
                user_id=user_id,
                units=self._credit_settings.l2_cost,
                source_type="batch_analysis",
                source_id=f"batch:{item.batch_id}:{item.id}",
                ttl_minutes=self._credit_settings.async_reservation_ttl_minutes,
            )
            try:
                actual_cost = determine_actual_cost(self._credit_settings)
                await self._credit_service.capture_usage(reservation.id, units_captured=actual_cost)
            except InvalidReservationState:
                logger.error("capture_failed_reservation_expired", extra={"reservation_id": str(reservation.id)})
                raise
            except Exception:
                try:
                    await self._credit_service.void_usage(reservation.id)
                except Exception:
                    logger.error("void_usage_failed", extra={"reservation_id": str(reservation.id)}, exc_info=True)
                raise

        # Legacy billing (skipped when hybrid_read_enabled)
        if (
            not result.cached
            and self._billing
            and user_id
            and not (self._billing_flags and self._billing_flags.hybrid_read_enabled)
        ):
            try:
                ctx = await self._billing.get_billing_context_for_user(user_id)
                await self._billing.record_usage(ctx, video_count=1, check_thresholds=False)
            except Exception:
                logger.warning(
                    "batch_billing_failed",
                    extra={"item_id": str(item.id), "user_id": str(user_id)},
                )

        analysis = result.analysis
        flagged = not analysis.overall_safe
        risk_score = 1.0 - analysis.overall_confidence if flagged else 0.0

        return {
            "cached": result.cached,
            "cost_usd": result.cost_usd,
            "record_id": str(result.record_id),
            "flagged": flagged,
            "risk_score": risk_score,
        }

    # ── Helpers ─────────────────────────────────────────────────────────────

    async def _safe_complete_item(
        self,
        item_id: UUID,
        batch_id: UUID,
        status: ItemStatus,
        error_message: str,
    ) -> None:
        """Complete item with CASCADE safety -- handle 0-row UPDATE gracefully."""
        completed = await self._repo.complete_item_and_increment(
            item_id, batch_id, status, error_message=error_message,
        )
        if completed is None:
            logger.warning(
                "batch_item_cascade_deleted",
                extra={"item_id": str(item_id), "batch_id": str(batch_id)},
            )

    # ── Retry logic ────────────────────────────────────────────────────────

    async def _retry_with_backoff(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        max_retries: int | None = None,
    ) -> Any:
        """Exponential backoff: base*1, base*2, base*4 with jitter.

        Only retries _TRANSIENT_ERRORS. All other exceptions propagate
        immediately.
        """
        retries = max_retries if max_retries is not None else self._settings.max_retries
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                return await func(*args)
            except _TRANSIENT_ERRORS as e:
                last_error = e
                if attempt < retries:
                    delay = self._settings.backoff_base * (2 ** attempt)
                    jitter = random.uniform(0, delay * 0.1)
                    await asyncio.sleep(delay + jitter)
                    logger.warning(
                        "batch_item_retry",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": retries,
                            "error": str(e)[:200],
                        },
                    )
                continue
            # Non-transient errors propagate immediately

        if last_error:
            raise last_error
        raise RuntimeError("Retry loop exited without result")
