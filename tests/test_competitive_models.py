"""Tests for competitive domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.competitive.models import (
    BrandCreatorRelationship,
    CompetitiveBrief,
    PartnershipAlert,
)


def test_competitive_brief_from_row():
    """CompetitiveBrief.from_row parses asyncpg row."""
    import json

    row = {
        "id": uuid4(),
        "client_id": uuid4(),
        "org_id": uuid4(),
        "date_range": "7d",
        "schema_version": 1,
        "brief_data": json.dumps({"sections": [], "summary": "test"}),
        "idempotency_key": "weekly-123",
        "created_at": datetime.now(timezone.utc),
    }

    brief = CompetitiveBrief.from_row(row)
    assert brief.date_range == "7d"
    assert brief.brief_data["summary"] == "test"
    assert brief.idempotency_key == "weekly-123"


def test_competitive_brief_to_dict():
    """CompetitiveBrief.to_dict serializes correctly."""
    brief = CompetitiveBrief(
        id=uuid4(),
        client_id=uuid4(),
        org_id=uuid4(),
        date_range="14d",
        schema_version=1,
        brief_data={"key": "val"},
        idempotency_key=None,
        created_at=datetime.now(timezone.utc),
    )
    d = brief.to_dict()
    assert d["date_range"] == "14d"
    assert "pdf_url" not in d


def test_partnership_alert_frozen():
    """PartnershipAlert is immutable."""
    alert = PartnershipAlert(
        brand="nike",
        creator="@runner",
        platform="tiktok",
        mention_count=5,
        is_new=True,
        is_escalation=False,
    )
    assert alert.brand == "nike"
    assert alert.is_new is True


def test_brand_creator_relationship_from_row():
    """BrandCreatorRelationship.from_row parses asyncpg row."""
    row = {
        "id": uuid4(),
        "client_id": uuid4(),
        "brand_name": "nike",
        "creator_username": "@runner",
        "platform": "instagram",
        "mention_count": 10,
        "first_seen_at": datetime.now(timezone.utc),
        "last_seen_at": datetime.now(timezone.utc),
    }
    rel = BrandCreatorRelationship.from_row(row)
    assert rel.brand_name == "nike"
    assert rel.mention_count == 10
