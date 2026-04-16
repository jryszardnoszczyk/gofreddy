"""Partnership detection from monitoring data."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ...monitoring.repository import PostgresMonitoringRepository
    from ..repository import PostgresCompetitiveRepository

from ..models import PartnershipAlert

logger = logging.getLogger(__name__)

# Thresholds
_MIN_MENTIONS_FOR_PARTNERSHIP = 3
_MAX_MENTIONS_PER_MONITOR = 500


class PartnershipDetector:
    """Detects new and escalating brand-creator partnerships."""

    def __init__(
        self,
        monitoring_repo: PostgresMonitoringRepository,
        competitive_repo: PostgresCompetitiveRepository,
    ) -> None:
        self._monitoring_repo = monitoring_repo
        self._competitive_repo = competitive_repo

    async def detect_new_partnerships(
        self,
        client_id: UUID,
        competitor_brands: list[str],
        org_id: UUID,
    ) -> list[PartnershipAlert]:
        """Scan monitoring mentions for brand-creator partnerships.

        Returns alerts for new or escalating partnerships only.
        """
        if not competitor_brands:
            return []

        monitor_id = await self._competitive_repo.resolve_monitor_for_client(client_id)
        if monitor_id is None:
            logger.info("no_monitor_for_client: client_id=%s", client_id)
            return []

        # Collect mentions mentioning competitor brands
        brand_creator_pairs: dict[tuple[str, str, str], int] = {}  # (brand, creator, platform) -> count
        sponsored_pairs: set[tuple[str, str, str]] = set()

        for brand in competitor_brands:
            brand_lower = brand.casefold()
            try:
                mentions, _ = await self._monitoring_repo.search_mentions(
                    org_id,
                    monitor_id,
                    brand,
                    limit=_MAX_MENTIONS_PER_MONITOR,
                )
            except Exception:
                logger.warning("partnership_search_failed: brand=%s", brand_lower)
                continue

            for mention in mentions:
                creator = (mention.author_handle or "").strip()
                if not creator:
                    continue
                platform = mention.source.value if hasattr(mention.source, "value") else str(mention.source)
                key = (brand_lower, creator.casefold(), platform)
                brand_creator_pairs[key] = brand_creator_pairs.get(key, 0) + 1

                # Check for sponsored content indicators in metadata
                meta = mention.metadata or {}
                if meta.get("is_sponsored"):
                    sponsored_pairs.add(key)

        # Filter to noteworthy partnerships
        alerts: list[PartnershipAlert] = []
        for (brand, creator, platform), count in brand_creator_pairs.items():
            if count < _MIN_MENTIONS_FOR_PARTNERSHIP and (brand, creator, platform) not in sponsored_pairs:
                continue

            # Check existing relationship
            existing = await self._competitive_repo.get_relationship_history(
                client_id, brand, creator
            )

            is_new = existing is None
            is_escalation = False
            if existing and existing.mention_count > 0:
                is_escalation = count > existing.mention_count  # increased activity

            if not is_new and not is_escalation:
                continue

            # Upsert the relationship
            await self._competitive_repo.upsert_relationship(
                client_id, brand, creator, platform, mention_count=count,
            )

            alerts.append(PartnershipAlert(
                brand=brand,
                creator=creator,
                platform=platform,
                mention_count=count,
                is_new=is_new,
                is_escalation=is_escalation,
            ))

        logger.info(
            "partnership_detection_complete: client_id=%s alerts=%d",
            client_id, len(alerts),
        )
        return alerts
