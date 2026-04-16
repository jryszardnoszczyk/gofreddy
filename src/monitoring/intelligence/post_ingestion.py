"""Post-ingestion analysis — AI-driven monitor refinement based on real mention data."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ...common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..models import Refinement

if TYPE_CHECKING:
    from google.genai import Client as GenaiClient

    from ..config import MonitoringSettings
    from ..models import Mention, Monitor
    from ..repository import PostgresMonitoringRepository

logger = logging.getLogger(__name__)

DEADLINE_SECONDS = 840  # Cloud Run timeout is 900s

_SYSTEM_INSTRUCTION = """You are a monitoring quality analyst. Analyze the provided mention data for a brand monitor and suggest refinements to improve signal quality.

The monitor's current configuration is provided along with a sample of recent mentions.

Analyze for:
1. **Noise patterns**: Identify irrelevant mentions that slip through the current query. Suggest NOT exclusion terms.
2. **Missing keywords**: Find high-frequency relevant terms not in the current query. Suggest additions.
3. **Source quality**: Rank sources by signal-to-noise ratio based on the mention sample.
4. **Volume baseline**: Estimate normal mention rate for alert threshold calibration.
5. **Competitor detection**: Identify brands frequently co-mentioned that could be tracked as competitors.

For each suggested refinement, provide:
- `change_type`: one of "noise_exclusion", "keyword_expansion", "threshold_calibration", "source_rebalance", "competitor_detected", "scope_change"
- `field`: the monitor config field to change (e.g., "boolean_query", "sources", "competitor_brands")
- `old_value`: current value (string representation)
- `new_value`: proposed new value (string representation)
- `rationale`: 1-2 sentence explanation
- `autonomy_level`: "auto" for safe/reversible changes (noise exclusion, keyword expansion, threshold), "notify" for applied-but-highlighted changes (source rebalance), "ask" for changes needing user approval (new competitor, scope change)
- `confidence`: 0.0-1.0

Respond with a JSON array of refinements. Return empty array [] if the monitor is performing well and no changes are needed.
"""


class PostIngestionAnalyzer:
    """Analyzes monitor mention data and suggests refinements using Gemini."""

    def __init__(
        self,
        client: GenaiClient,
        settings: MonitoringSettings,
        repository: PostgresMonitoringRepository,
    ) -> None:
        self._client = client
        self._settings = settings
        self._repo = repository

    async def run_analysis_job(self, deadline: float | None = None) -> dict[str, int]:
        """Run post-ingestion analysis for all eligible monitors.

        Returns: {"processed": N, "skipped": N, "failed": N}
        """
        if deadline is None:
            deadline = time.monotonic() + DEADLINE_SECONDS

        monitors = await self._repo.get_active_monitors()
        now = datetime.now(tz=timezone.utc)
        min_age = timedelta(hours=24)

        processed = 0
        skipped = 0
        failed = 0

        for monitor in monitors:
            if time.monotonic() > deadline:
                logger.warning(
                    "Post-ingestion analysis deadline exceeded after %d monitors",
                    processed + skipped + failed,
                )
                break

            # Skip monitors younger than 24h
            if now - monitor.created_at < min_age:
                skipped += 1
                continue

            # Skip monitors with insufficient mentions
            mention_count = await self._repo.count_mentions(monitor.id)
            if mention_count < self._settings.analysis_min_mentions:
                skipped += 1
                continue

            try:
                refinements = await self.analyze_monitor(monitor.id)
                if refinements:
                    await self._execute_refinements(monitor.id, refinements)
                    processed += 1
                else:
                    skipped += 1
            except Exception:
                logger.exception(
                    "Post-ingestion analysis failed for monitor %s", monitor.id
                )
                failed += 1

        return {"processed": processed, "skipped": skipped, "failed": failed}

    async def analyze_monitor(self, monitor_id: UUID) -> list[Refinement]:
        """Analyze a single monitor and return suggested refinements."""
        monitor = await self._repo.get_monitor_by_id_system(monitor_id)
        if monitor is None:
            logger.warning("Monitor %s not found for analysis", monitor_id)
            return []

        # Fetch recent mentions using monitor's user_id for IDOR-safe query
        mentions, _total = await self._repo.query_mentions(
            monitor_id=monitor.id,
            user_id=monitor.user_id,
            limit=self._settings.analysis_max_mentions,
            sort_by="published_at",
        )

        if len(mentions) < self._settings.analysis_min_mentions:
            return []

        return await self._call_gemini(mentions, monitor)

    async def _call_gemini(
        self,
        mentions: list[Mention],
        monitor: Monitor,
    ) -> list[Refinement]:
        """Call Gemini to analyze mentions and suggest refinements."""
        from google.genai import types as genai_types

        from ...common.gemini_models import GEMINI_FLASH_LITE

        # Prepare mention data for analysis
        mention_inputs = [
            {
                "id": str(m.id),
                "text": (m.content or "")[:500],
                "source": m.source.value if m.source else "unknown",
                "sentiment": m.sentiment_score,
                "engagement": m.engagement_likes + m.engagement_shares + m.engagement_comments,
            }
            for m in mentions
        ]

        # Prepare monitor config context
        monitor_config = {
            "name": monitor.name,
            "keywords": monitor.keywords,
            "boolean_query": monitor.boolean_query,
            "sources": [s.value for s in monitor.sources],
            "competitor_brands": monitor.competitor_brands or [],
        }

        content = json.dumps({
            "monitor_config": monitor_config,
            "mentions_sample": mention_inputs,
        }, ensure_ascii=False)

        config = genai_types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0.3,
        )

        response = await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=GEMINI_FLASH_LITE,
                contents=content,
                config=config,
            ),
            timeout=60,
        )
        t_in, t_out, c = extract_gemini_usage(response, GEMINI_FLASH_LITE)
        await _cost_recorder.record(
            "gemini", "post_ingestion_analysis",
            tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=GEMINI_FLASH_LITE,
        )

        # Update last_analysis_at
        await self._repo.system_update_monitor(
            monitor.id,
            last_analysis_at=datetime.now(tz=timezone.utc),
        )

        # Check finish_reason
        if response.candidates and response.candidates[0].finish_reason not in (
            None, "STOP",
        ):
            logger.warning(
                "Gemini post-ingestion analysis terminated: %s",
                response.candidates[0].finish_reason,
            )
            return []

        if not response.text:
            return []

        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse post-ingestion analysis JSON response")
            return []

        if not isinstance(result, list):
            return []

        # Validate each refinement
        valid: list[Refinement] = []
        for item in result:
            if not isinstance(item, dict):
                continue
            change_type = item.get("change_type", "")
            field = item.get("field", "")
            rationale = item.get("rationale", "")
            autonomy = item.get("autonomy_level", "ask")
            confidence = item.get("confidence", 0.0)

            if not change_type or not field or not rationale:
                continue

            valid.append(Refinement(
                change_type=str(change_type),
                field=str(field),
                old_value=item.get("old_value"),
                new_value=item.get("new_value"),
                rationale=str(rationale)[:500],
                autonomy_level=str(autonomy) if autonomy in ("auto", "notify", "ask") else "ask",
                confidence=min(1.0, max(0.0, float(confidence))) if isinstance(confidence, (int, float)) else 0.0,
            ))

        return valid

    async def _execute_refinements(
        self,
        monitor_id: UUID,
        refinements: list[Refinement],
    ) -> None:
        """Apply refinements based on autonomy level. Write all to changelog."""
        monitor = await self._repo.get_monitor_by_id_system(monitor_id)
        if monitor is None:
            return

        analysis_run_id = uuid4()

        # Check rate limit: max N auto-refinements per monitor per 24h
        auto_count = await self._repo.count_changelog_entries(
            monitor_id, status="applied", hours=24,
        )

        for refinement in refinements:
            # Determine whether to auto-apply
            should_apply = False
            entry_status = "pending"

            if refinement.autonomy_level == "auto" and refinement.confidence >= 0.8:
                # Check rate limit
                if auto_count < self._settings.analysis_max_refinements_per_day:
                    # Check user edit protection: skip if user edited this field within 24h
                    if not self._user_recently_edited(monitor):
                        should_apply = True
                        entry_status = "applied"
                        auto_count += 1
            elif refinement.autonomy_level == "notify":
                # Applied but highlighted — same rate limit applies
                if auto_count < self._settings.analysis_max_refinements_per_day:
                    if not self._user_recently_edited(monitor):
                        should_apply = True
                        entry_status = "applied"
                        auto_count += 1

            # Write changelog entry
            await self._repo.insert_changelog_entry(
                monitor_id=monitor_id,
                change_type=refinement.change_type,
                change_detail={
                    "field": refinement.field,
                    "old_value": refinement.old_value,
                    "new_value": refinement.new_value,
                },
                rationale=refinement.rationale,
                autonomy_level=refinement.autonomy_level,
                status=entry_status,
                applied_by="system",
                analysis_run_id=analysis_run_id,
            )

            # Apply the change if approved
            if should_apply:
                await self._apply_refinement(monitor_id, refinement)

    def _user_recently_edited(self, monitor: Monitor) -> bool:
        """Check if the user edited the monitor within the last 24h (any field)."""
        if monitor.last_user_edit_at is None:
            return False
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        return monitor.last_user_edit_at > cutoff

    async def _apply_refinement(
        self,
        monitor_id: UUID,
        refinement: Refinement,
    ) -> None:
        """Apply a single refinement to the monitor via system_update_monitor."""
        field = refinement.field
        new_value = refinement.new_value

        if field not in ("boolean_query", "keywords", "sources", "competitor_brands"):
            logger.warning("Unsupported refinement field: %s", field)
            return

        # Validate type matches expected field type (LLM output can be unpredictable)
        if field == "boolean_query" and not isinstance(new_value, str):
            logger.warning("Unexpected type for boolean_query refinement: %s", type(new_value))
            return
        if field in ("keywords", "sources", "competitor_brands") and not isinstance(new_value, list):
            logger.warning("Unexpected type for %s refinement: %s", field, type(new_value))
            return

        update_fields: dict[str, Any] = {field: new_value}
        await self._repo.system_update_monitor(monitor_id, **update_fields)

        # Reset cursors if boolean_query changed (mentions need re-fetching)
        if field == "boolean_query":
            await self._repo.delete_cursors_for_monitor(monitor_id)
