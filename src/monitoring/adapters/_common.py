"""Shared utilities for monitoring adapters."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from apify_client import ApifyClientAsync

from ...common.cost_recorder import APIFY_COST_PER_CU, cost_recorder as _cost_recorder
from ..exceptions import MentionFetchError
from ..models import SentimentLabel

logger = logging.getLogger(__name__)


def rating_to_sentiment(
    rating: float | int | None,
) -> tuple[float | None, SentimentLabel | None]:
    """Map a review rating to sentiment score and label.

    - None or 0 → (None, None)
    - Negative values → (None, None) (invalid data)
    - 1-2 → (-0.8, NEGATIVE)
    - 3 → (0.0, NEUTRAL)
    - 4-5 → (0.8, POSITIVE)
    - Values >5 clamped to 5 (handles 10-point scales)
    - Fractional values floored to integer before mapping
    """
    if rating is None or rating <= 0:
        return (None, None)

    clamped = max(1, min(5, int(rating)))
    if clamped <= 2:
        return (-0.8, SentimentLabel.NEGATIVE)
    if clamped == 3:
        return (0.0, SentimentLabel.NEUTRAL)
    return (0.8, SentimentLabel.POSITIVE)


def build_apify_client(token: str) -> ApifyClientAsync:
    """Shared Apify client factory."""
    return ApifyClientAsync(token=token)


async def parse_apify_items(
    run: dict[str, Any] | None,
    client: ApifyClientAsync,
) -> list[dict[str, Any]]:
    """Extract dataset items from an Apify actor run.

    Raises MentionFetchError on failed/timed-out runs or missing run data.
    Returns empty list on missing dataset.
    """
    if run is None:
        raise MentionFetchError("Actor returned no run")

    status = run.get("status", "")
    if status in ("FAILED", "TIMED-OUT"):
        raise MentionFetchError(f"Actor run {status}: {run.get('statusMessage', '')}")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        return []

    # Record Apify cost — prefer actual billing data from API response
    actual_cost = run.get("usageTotalUsd")
    if actual_cost is not None:
        cost_usd = float(actual_cost)
    else:
        compute_units = run.get("stats", {}).get("computeUnits", 0) if run else 0
        cost_usd = (compute_units * APIFY_COST_PER_CU) if compute_units else None
    await _cost_recorder.record(
        "apify", run.get("actId") or "unknown",
        cost_usd=cost_usd,
        model=run.get("actId"),
        metadata={"run_id": run.get("id")} if run else None,
    )

    try:
        items = await client.dataset(dataset_id).list_items()
        return items.items if items and items.items else []
    except Exception as e:
        err_str = str(e).lower()
        # Unrecoverable Apify errors
        if "404" in err_str or "not found" in err_str:
            raise MentionFetchError(f"Actor not found: {e}") from e
        if "402" in err_str or "payment" in err_str:
            raise MentionFetchError(f"Apify payment required: {e}") from e
        # Transient — let base class retry
        raise


def parse_date(
    date_str: str | None,
    *,
    fallback_to_now: bool = False,
) -> datetime | None:
    """Parse various date string formats into a timezone-aware datetime.

    Supports ISO 8601, ``%Y-%m-%d``, ``%Y-%m-%dT%H:%M:%S``, and ``%b %d, %Y``.
    Also handles values that are already ``datetime`` instances.

    When *fallback_to_now* is ``True`` and the input is ``None`` or unparseable,
    ``datetime.now(tz=timezone.utc)`` is returned instead of ``None``.
    """
    _now = datetime.now(tz=timezone.utc) if fallback_to_now else None

    if not date_str:
        return _now
    if isinstance(date_str, datetime):
        return date_str  # type: ignore[unreachable]
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return _now
