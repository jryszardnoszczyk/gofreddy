"""CRM contacts service."""

from __future__ import annotations

import logging
from uuid import UUID

from .models import Contact
from .repository import PostgresContactRepository

logger = logging.getLogger(__name__)


class ContactService:
    """Orchestrates CRM contact operations."""

    def __init__(self, repository: PostgresContactRepository) -> None:
        self._repo = repository

    async def record_interaction(
        self,
        user_id: UUID,
        platform: str,
        handle: str,
        *,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> Contact:
        return await self._repo.upsert_contact(
            user_id, platform, handle,
            display_name=display_name, avatar_url=avatar_url,
        )

    async def list_contacts(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Contact]:
        return await self._repo.get_contacts(
            user_id, limit=limit, offset=offset, search=search,
        )

    async def get_contact(
        self,
        user_id: UUID,
        contact_id: UUID,
    ) -> Contact:
        """Get a single contact by ID, verifying ownership."""
        result = await self._repo.get_contact(user_id, contact_id)
        if result is None:
            raise ValueError(f"Contact {contact_id} not found")
        return result

    async def update_contact(
        self,
        user_id: UUID,
        contact_id: UUID,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> Contact:
        result = await self._repo.update_contact(
            user_id, contact_id, notes=notes, tags=tags,
        )
        if result is None:
            raise ValueError(f"Contact {contact_id} not found")
        return result
