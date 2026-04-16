"""CRM contact domain models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Contact:
    id: UUID
    org_id: UUID
    primary_handle: str
    primary_platform: str
    display_name: str | None
    avatar_url: str | None
    handles: list[dict]
    interaction_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    notes: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> Contact:
        raw_handles = row["handles"]
        if isinstance(raw_handles, str):
            handles = json.loads(raw_handles)
        else:
            handles = raw_handles or []
        raw_tags = row["tags"]
        if isinstance(raw_tags, str):
            tags = json.loads(raw_tags)
        else:
            tags = list(raw_tags or [])
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            primary_handle=row["primary_handle"],
            primary_platform=row["primary_platform"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            handles=handles,
            interaction_count=row["interaction_count"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            notes=row["notes"],
            tags=tags,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
