"""Competitive intelligence domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CompetitiveBrief:
    """Stored competitive brief."""

    id: UUID
    client_id: UUID
    org_id: UUID | None
    date_range: str
    schema_version: int
    brief_data: dict[str, Any]
    idempotency_key: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> CompetitiveBrief:
        import json as _json

        raw = row["brief_data"]
        brief_data = _json.loads(raw) if isinstance(raw, str) else dict(raw)
        return cls(
            id=row["id"],
            client_id=row["client_id"],
            org_id=row["org_id"],
            date_range=row["date_range"],
            schema_version=row["schema_version"],
            brief_data=brief_data,
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "org_id": str(self.org_id) if self.org_id else None,
            "date_range": self.date_range,
            "schema_version": self.schema_version,
            "brief_data": self.brief_data,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class PartnershipAlert:
    """Detected partnership between a brand and creator."""

    brand: str
    creator: str
    platform: str
    mention_count: int
    is_new: bool
    is_escalation: bool


@dataclass(frozen=True, slots=True)
class BrandCreatorRelationship:
    """Stored brand-creator partnership record."""

    id: UUID
    client_id: UUID
    brand_name: str
    creator_username: str
    platform: str
    mention_count: int
    first_seen_at: datetime
    last_seen_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> BrandCreatorRelationship:
        return cls(
            id=row["id"],
            client_id=row["client_id"],
            brand_name=row["brand_name"],
            creator_username=row["creator_username"],
            platform=row["platform"],
            mention_count=row["mention_count"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
        )
