"""Ad-hoc discovery search — fan-out to multiple adapters without persistence."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

from .models import DataSource, DiscoverResult, DiscoverSourceError, RawMention
from .fetcher_protocol import MentionFetcher

logger = logging.getLogger(__name__)

_ADAPTER_SEMAPHORE = asyncio.Semaphore(10)


async def discover_mentions(
    query: str,
    sources: list[DataSource],
    adapters: dict[DataSource, MentionFetcher],
    *,
    limit: int = 25,
    adapter_timeout: float = 25.0,
    gather_timeout: float = 30.0,
) -> DiscoverResult:
    """Ad-hoc discovery search — no persistence, no monitor lookup."""
    available = {s: adapters[s] for s in sources if s in adapters}
    unavailable = [s for s in sources if s not in adapters]

    # Let each adapter return more than the final limit — we merge & sort across sources.
    per_adapter_limit = min(limit * 2, 500)

    async def _fetch_one(
        source: DataSource, adapter: MentionFetcher,
    ) -> tuple[DataSource, list[RawMention], DiscoverSourceError | None]:
        async with _ADAPTER_SEMAPHORE:
            try:
                raw, _ = await asyncio.wait_for(
                    adapter.fetch_mentions(query, limit=per_adapter_limit),
                    timeout=adapter_timeout,
                )
                return source, raw, None
            except asyncio.TimeoutError:
                return source, [], DiscoverSourceError(
                    source=source.value, reason="timeout",
                )
            except Exception as e:
                logger.warning("discover_adapter_error", extra={"source": source.value, "error": str(e)[:500]})
                return source, [], DiscoverSourceError(
                    source=source.value, reason="adapter_error",
                )

    tasks = [_fetch_one(s, a) for s, a in available.items()]
    if not tasks:
        return DiscoverResult(
            mentions=[],
            sources_searched=[],
            sources_failed=[],
            sources_unavailable=[s.value for s in unavailable],
        )

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=gather_timeout,
        )
    except asyncio.TimeoutError:
        results = []

    all_mentions: list[RawMention] = []
    sources_ok: list[str] = []
    sources_failed: list[DiscoverSourceError] = []
    for item in results:
        if isinstance(item, BaseException):
            continue
        source, mentions, error = item
        if error:
            sources_failed.append(error)
        else:
            sources_ok.append(source.value)
            all_mentions.extend(mentions)

    _EPOCH = datetime.min.replace(tzinfo=timezone.utc)

    def _sort_key(m: RawMention) -> datetime:
        ts = m.published_at
        if ts is None:
            return _EPOCH
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return _EPOCH
        # Normalize naive datetimes to UTC
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    # Fair per-source distribution: each source gets at least floor(limit/N)
    # slots, then remaining slots go to top results by timestamp.
    by_source: dict[str, list[RawMention]] = defaultdict(list)
    for m in all_mentions:
        key = m.source.value if hasattr(m.source, "value") else str(m.source)
        by_source[key].append(m)

    # Sort each source's results by date (newest first)
    for mentions_list in by_source.values():
        mentions_list.sort(key=_sort_key, reverse=True)

    n_sources = len(by_source)
    if n_sources == 0 or len(all_mentions) <= limit:
        # No need for fair distribution if under limit
        all_mentions.sort(key=_sort_key, reverse=True)
        capped = all_mentions[:limit]
    else:
        per_source_min = limit // n_sources
        capped: list[RawMention] = []
        overflow: list[RawMention] = []
        for src_mentions in by_source.values():
            capped.extend(src_mentions[:per_source_min])
            overflow.extend(src_mentions[per_source_min:])
        # Fill remaining slots from overflow sorted by date
        remaining = limit - len(capped)
        if remaining > 0:
            overflow.sort(key=_sort_key, reverse=True)
            capped.extend(overflow[:remaining])
        # Final sort by date for display
        capped.sort(key=_sort_key, reverse=True)

    return DiscoverResult(
        mentions=capped,
        sources_searched=sources_ok,
        sources_failed=sources_failed,
        sources_unavailable=[s.value for s in unavailable],
    )
