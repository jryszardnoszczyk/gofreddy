"""Brief reader — single-source per TD-56.

Consumers call `read_briefs(source_lane, archive_root)` once per source
lane they need to consume. When a consumer needs >1 source lane (U15b
site_engine reads from marketing_audit + geo), it calls twice and
unions the result with `priority_sort_key` — ~5 lines at the call site,
no shared-infra API surface for multi-source merge.

Per D8 + D9:
- Briefs at the source lane's *current_runtime* archive are visible.
- Stale briefs (`valid_until < now`) are skipped with a log warning.
- Malformed JSON / missing required fields are skipped with a log
  warning, not raised — graceful degradation lets consumers degrade
  to standalone if every brief is broken.

Returned list is sorted by priority (high → medium → low) then by
`produced_at` (older within a bucket); consumer applies its own top-K
filter from `ClientConfig.brief_consumption.top_k_per_run`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.briefs.schema import FindingsBrief, priority_sort_key

logger = logging.getLogger(__name__)


def read_briefs(source_lane: str, archive_root: Path) -> list[FindingsBrief]:
    """Read all visible briefs from `<archive_root>/briefs/*.json`,
    filter stale + malformed, return priority-sorted list.

    Args:
        source_lane: name of the source lane (used in log warnings).
            The caller is responsible for selecting the right
            `archive_root` — typically `autoresearch/archive_<lane>/
            current_runtime/` for the reader-visible head.
        archive_root: directory containing the `briefs/` subdirectory.

    Returns:
        List of FindingsBrief objects sorted by priority then produced_at.
        Empty list when no briefs directory exists or all entries are
        skipped (per D9 graceful degradation — consumer falls back to
        standalone operation).
    """
    briefs_dir = archive_root / "briefs"
    if not briefs_dir.is_dir():
        logger.debug(
            "no briefs directory at %s for source_lane=%s; "
            "returning empty list (consumer degrades to standalone)",
            briefs_dir, source_lane,
        )
        return []

    now = datetime.now(timezone.utc)
    briefs: list[FindingsBrief] = []
    for json_path in sorted(briefs_dir.glob("*.json")):
        try:
            payload = json.loads(json_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "skipping malformed brief at %s for source_lane=%s: %s",
                json_path, source_lane, exc,
            )
            continue

        try:
            brief = FindingsBrief.model_validate(payload)
        except ValidationError as exc:
            logger.warning(
                "skipping brief at %s for source_lane=%s with schema "
                "violation: %s",
                json_path, source_lane, exc.error_count(),
            )
            continue

        if brief.valid_until is not None:
            # Normalize tz-naive valid_until to UTC for safe comparison.
            cutoff = brief.valid_until
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            if cutoff < now:
                logger.info(
                    "skipping stale brief %s (valid_until=%s, now=%s)",
                    brief.brief_id, cutoff, now,
                )
                continue

        briefs.append(brief)

    briefs.sort(key=priority_sort_key)
    return briefs


__all__ = ["read_briefs"]
