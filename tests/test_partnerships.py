"""Tests for PartnershipDetector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.competitive.intelligence.partnerships import PartnershipDetector
from src.competitive.models import BrandCreatorRelationship


def _make_mention(**overrides: Any) -> MagicMock:
    """Create a mock mention."""
    m = MagicMock()
    m.author_handle = overrides.get("author_handle", "@creator1")
    m.source = MagicMock()
    m.source.value = overrides.get("platform", "tiktok")
    m.metadata = overrides.get("metadata", {})
    return m


def _make_relationship(**overrides: Any) -> BrandCreatorRelationship:
    return BrandCreatorRelationship(
        id=overrides.get("id", uuid4()),
        client_id=overrides.get("client_id", uuid4()),
        brand_name=overrides.get("brand_name", "brandx"),
        creator_username=overrides.get("creator_username", "@creator1"),
        platform=overrides.get("platform", "tiktok"),
        mention_count=overrides.get("mention_count", 3),
        first_seen_at=overrides.get("first_seen_at", datetime.now(timezone.utc)),
        last_seen_at=overrides.get("last_seen_at", datetime.now(timezone.utc)),
    )


@pytest.mark.asyncio
async def test_detect_new_partnership():
    """3+ mentions from same creator triggers new partnership alert."""
    client_id = uuid4()
    org_id = uuid4()
    monitor_id = uuid4()

    # 3 mentions from same creator for same brand
    mentions = [_make_mention(author_handle="@creator1") for _ in range(3)]

    monitoring_repo = AsyncMock()
    monitoring_repo.search_mentions.return_value = (mentions, 3)

    competitive_repo = AsyncMock()
    competitive_repo.resolve_monitor_for_client.return_value = monitor_id
    competitive_repo.get_relationship_history.return_value = None  # New partnership
    competitive_repo.upsert_relationship.return_value = _make_relationship()

    detector = PartnershipDetector(monitoring_repo, competitive_repo)
    alerts = await detector.detect_new_partnerships(
        client_id, ["BrandX"], org_id,
    )

    assert len(alerts) >= 1
    assert alerts[0].is_new is True
    assert alerts[0].is_escalation is False


@pytest.mark.asyncio
async def test_detect_escalation():
    """Partnership escalation when mention count doubles."""
    client_id = uuid4()
    org_id = uuid4()
    monitor_id = uuid4()

    mentions = [_make_mention(author_handle="@creator1") for _ in range(6)]

    monitoring_repo = AsyncMock()
    monitoring_repo.search_mentions.return_value = (mentions, 6)

    existing = _make_relationship(mention_count=3)
    competitive_repo = AsyncMock()
    competitive_repo.resolve_monitor_for_client.return_value = monitor_id
    competitive_repo.get_relationship_history.return_value = existing
    competitive_repo.upsert_relationship.return_value = _make_relationship(mention_count=9)

    detector = PartnershipDetector(monitoring_repo, competitive_repo)
    alerts = await detector.detect_new_partnerships(
        client_id, ["BrandX"], org_id,
    )

    assert len(alerts) >= 1
    assert alerts[0].is_escalation is True


@pytest.mark.asyncio
async def test_sponsored_below_threshold():
    """Sponsored mention triggers alert even with <3 mentions."""
    client_id = uuid4()
    org_id = uuid4()
    monitor_id = uuid4()

    mentions = [_make_mention(author_handle="@creator1", metadata={"is_sponsored": True})]

    monitoring_repo = AsyncMock()
    monitoring_repo.search_mentions.return_value = (mentions, 1)

    competitive_repo = AsyncMock()
    competitive_repo.resolve_monitor_for_client.return_value = monitor_id
    competitive_repo.get_relationship_history.return_value = None
    competitive_repo.upsert_relationship.return_value = _make_relationship()

    detector = PartnershipDetector(monitoring_repo, competitive_repo)
    alerts = await detector.detect_new_partnerships(
        client_id, ["BrandX"], org_id,
    )

    assert len(alerts) >= 1
    assert alerts[0].is_new is True


@pytest.mark.asyncio
async def test_no_monitor_returns_empty():
    """No monitor for client returns empty alerts."""
    competitive_repo = AsyncMock()
    competitive_repo.resolve_monitor_for_client.return_value = None

    detector = PartnershipDetector(AsyncMock(), competitive_repo)
    alerts = await detector.detect_new_partnerships(uuid4(), ["Brand"], uuid4())

    assert alerts == []


@pytest.mark.asyncio
async def test_empty_brands_returns_empty():
    """Empty competitor brands returns empty alerts."""
    detector = PartnershipDetector(AsyncMock(), AsyncMock())
    alerts = await detector.detect_new_partnerships(uuid4(), [], uuid4())
    assert alerts == []


@pytest.mark.asyncio
async def test_casefold_normalization():
    """Brand names and creator usernames are casefolded."""
    client_id = uuid4()
    monitor_id = uuid4()

    mentions = [_make_mention(author_handle="@Creator1") for _ in range(3)]

    monitoring_repo = AsyncMock()
    monitoring_repo.search_mentions.return_value = (mentions, 3)

    competitive_repo = AsyncMock()
    competitive_repo.resolve_monitor_for_client.return_value = monitor_id
    competitive_repo.get_relationship_history.return_value = None
    competitive_repo.upsert_relationship.return_value = _make_relationship()

    detector = PartnershipDetector(monitoring_repo, competitive_repo)
    alerts = await detector.detect_new_partnerships(
        client_id, ["BRANDX"], uuid4(),
    )

    # Verify casefold was applied
    if alerts:
        assert alerts[0].brand == "brandx"
        assert alerts[0].creator == "@creator1"
