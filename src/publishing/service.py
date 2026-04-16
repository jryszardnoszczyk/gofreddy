"""Publishing service — orchestrates credential management and publish workflow."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from .config import PublishingSettings
from .encryption import decrypt_token, derive_key, encrypt_token
from .exceptions import (
    ConnectionNotFoundError,
    CredentialError,
    QueueItemNotFoundError,
    QueueLimitExceededError,
)
from .models import (
    PlatformConnection,
    PublishPlatform,
    PublishResult,
    QueueItem,
)
from .publisher_protocol import PublishAdapter
from .repository import PostgresPublishingRepository

logger = logging.getLogger(__name__)


class PublishingService:
    def __init__(
        self,
        repository: PostgresPublishingRepository,
        settings: PublishingSettings | None = None,
        *,
        publishers: dict[PublishPlatform, PublishAdapter] | None = None,
    ) -> None:
        self._repo = repository
        self._settings = settings or PublishingSettings()
        self._publishers = publishers or {}
        self._encryption_key = derive_key(
            self._settings.encryption_secret.get_secret_value()
        )
        self._encryption_key_v2: bytes | None = None
        if self._settings.encryption_secret_v2:
            self._encryption_key_v2 = derive_key(
                self._settings.encryption_secret_v2.get_secret_value()
            )

    def _get_key_for_version(self, version: int) -> bytes:
        if version == 2 and self._encryption_key_v2:
            return self._encryption_key_v2
        if version == 1:
            return self._encryption_key
        raise CredentialError(
            f"Encryption key version {version} not available"
        )

    @property
    def _current_key_version(self) -> int:
        return 2 if self._encryption_key_v2 else 1

    @property
    def _current_key(self) -> bytes:
        return self._get_key_for_version(self._current_key_version)

    # ── Connection Management ─────────────────────────────────────────────

    async def connect_platform(
        self,
        org_id: UUID,
        platform: str,
        auth_type: str,
        credentials: dict[str, str],
        account_id: str,
        account_name: str = "",
    ) -> PlatformConnection:
        # Encrypt credentials as JSON blob
        cred_json = json.dumps(credentials)
        credential_enc = encrypt_token(cred_json, self._current_key)

        connection = await self._repo.create_connection(
            org_id=org_id,
            platform=platform,
            auth_type=auth_type,
            account_id=account_id,
            account_name=account_name,
            credential_enc=credential_enc,
            key_version=self._current_key_version,
        )
        return connection

    async def list_connections(self, org_id: UUID) -> list[PlatformConnection]:
        return await self._repo.list_connections(org_id)

    async def disconnect_platform(
        self, connection_id: UUID, org_id: UUID
    ) -> bool:
        return await self._repo.deactivate_connection(connection_id, org_id)

    async def test_connection(
        self, connection_id: UUID, org_id: UUID
    ) -> bool:
        connection = await self._repo.get_connection(connection_id, org_id)
        if not connection:
            raise ConnectionNotFoundError("Connection not found")

        credentials = await self._decrypt_credentials(connection_id, org_id, connection.key_version)
        adapter = self._publishers.get(connection.platform)
        if not adapter:
            return False

        return await adapter.validate_credentials(credentials)

    async def _decrypt_credentials(
        self, connection_id: UUID, org_id: UUID, key_version: int
    ) -> dict[str, str]:
        raw = await self._repo.get_connection_credentials(connection_id, org_id)
        if not raw:
            raise ConnectionNotFoundError("Connection credentials not found")

        key = self._get_key_for_version(key_version)
        cred_enc = raw.get("credential_enc")
        if cred_enc:
            plaintext = decrypt_token(cred_enc, key)
            return json.loads(plaintext)

        # OAuth2 tokens
        result: dict[str, str] = {}
        if raw.get("access_token_enc"):
            result["access_token"] = decrypt_token(raw["access_token_enc"], key)
        if raw.get("refresh_token_enc"):
            result["refresh_token"] = decrypt_token(raw["refresh_token_enc"], key)
        return result

    # ── Queue Management ──────────────────────────────────────────────────

    async def create_draft(
        self,
        org_id: UUID,
        platform: str,
        connection_id: UUID,
        content_parts: list[dict[str, Any]],
        **kwargs: Any,
    ) -> QueueItem:
        # Quota enforcement
        count = await self._repo.count_queue_items(org_id)
        if count >= self._settings.max_queue_items_per_org:
            raise QueueLimitExceededError(
                f"Queue limit of {self._settings.max_queue_items_per_org} reached"
            )

        # Validate connection exists, is active, and belongs to org
        connection = await self._repo.get_connection(connection_id, org_id)
        if not connection or not connection.is_active:
            raise ConnectionNotFoundError("Connection not found or inactive")

        return await self._repo.create_queue_item(
            org_id=org_id,
            platform=platform,
            connection_id=connection_id,
            content_parts=content_parts,
            **kwargs,
        )

    async def update_draft(
        self, item_id: UUID, org_id: UUID, **fields: Any
    ) -> QueueItem:
        item = await self._repo.update_queue_item(item_id, org_id, **fields)
        if not item:
            raise QueueItemNotFoundError("Draft not found or not in draft status")
        return item

    async def delete_draft(self, item_id: UUID, org_id: UUID) -> bool:
        deleted = await self._repo.delete_queue_item(item_id, org_id)
        if not deleted:
            raise QueueItemNotFoundError(
                "Item not found or not in deletable status"
            )
        return True

    async def approve(
        self, item_id: UUID, org_id: UUID, approved_by: UUID
    ) -> QueueItem:
        item = await self._repo.approve_item(item_id, org_id, approved_by)
        if not item:
            raise QueueItemNotFoundError("Item not found")
        return item

    async def schedule(
        self, item_id: UUID, org_id: UUID, scheduled_at: datetime
    ) -> QueueItem:
        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("scheduled_at must be in the future")

        item = await self._repo.schedule_item(item_id, org_id, scheduled_at)
        if not item:
            raise QueueItemNotFoundError(
                "Item not found, not in schedulable status, or not approved"
            )
        return item

    async def cancel(self, item_id: UUID, org_id: UUID) -> QueueItem:
        item = await self._repo.cancel_item(item_id, org_id)
        if not item:
            raise QueueItemNotFoundError(
                "Item not found or not in cancellable status"
            )
        return item

    async def get_queue_item(
        self, item_id: UUID, org_id: UUID
    ) -> QueueItem:
        item = await self._repo.get_queue_item(item_id, org_id)
        if not item:
            raise QueueItemNotFoundError("Queue item not found")
        return item

    async def list_queue(
        self,
        org_id: UUID,
        *,
        status: str | None = None,
        platform: str | None = None,
        label: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QueueItem]:
        return await self._repo.list_queue_items(
            org_id, status=status, platform=platform, label=label,
            limit=limit, offset=offset,
        )

    # ── Publishing Execution ──────────────────────────────────────────────

    async def publish_item(self, item_id: UUID) -> PublishResult:
        """Core publish flow — called by dispatcher after claim."""
        # Load queue item (must be in publishing status — set by claim)
        item = await self._repo.get_publishing_item(item_id)
        if not item:
            return PublishResult(
                success=False, error_message="Item not in publishing status"
            )

        # Load connection
        connection = await self._repo.get_active_connection(item.connection_id)
        if not connection:
            await self._repo.mark_failed(item_id, "Connection not found or inactive")
            return PublishResult(
                success=False, error_message="Connection not found"
            )

        # Decrypt credentials (org_id scoped for IDOR safety)
        try:
            credentials = await self._decrypt_credentials(
                connection.id, item.org_id, connection.key_version
            )
        except CredentialError as e:
            await self._repo.mark_failed(item_id, "Credential decryption failed")
            return PublishResult(success=False, error_message=str(e))

        # Get adapter
        adapter = self._publishers.get(connection.platform)
        if not adapter:
            await self._repo.mark_failed(
                item_id, f"No adapter for {connection.platform.value}"
            )
            return PublishResult(
                success=False,
                error_message=f"No adapter for {connection.platform.value}",
            )

        # Publish
        result = await adapter.publish(item, credentials)

        if result.success:
            await self._repo.mark_published(
                item_id, result.external_id, result.external_url
            )
            await self._repo.update_last_used(connection.id)
        else:
            await self._repo.mark_failed(item_id, result.error_message or "Unknown error")

        return result

    # ── Key Rotation ──────────────────────────────────────────────────────

    async def rotate_encryption_keys(
        self, batch_size: int = 100
    ) -> dict[str, int]:
        current_version = self._current_key_version
        rows = await self._repo.get_connections_for_rotation(
            current_version, batch_size
        )

        rotated = 0
        for row in rows:
            old_key = self._get_key_for_version(row["key_version"])
            new_key = self._current_key

            new_cred = None
            if row["credential_enc"]:
                plaintext = decrypt_token(row["credential_enc"], old_key)
                new_cred = encrypt_token(plaintext, new_key)

            new_access = None
            if row["access_token_enc"]:
                plaintext = decrypt_token(row["access_token_enc"], old_key)
                new_access = encrypt_token(plaintext, new_key)

            new_refresh = None
            if row["refresh_token_enc"]:
                plaintext = decrypt_token(row["refresh_token_enc"], old_key)
                new_refresh = encrypt_token(plaintext, new_key)

            await self._repo.update_key_version(
                row["id"], new_cred, new_access, new_refresh, current_version
            )
            rotated += 1

        remaining = await self._repo.count_connections_for_rotation(
            current_version
        )
        return {"rotated": rotated, "remaining": remaining}

    # ── OAuth Token Management ────────────────────────────────────────────

    async def store_oauth_tokens(
        self,
        org_id: UUID,
        platform: str,
        auth_type: str,
        access_token: str,
        refresh_token: str | None = None,
        token_expires_at: datetime | None = None,
        scopes: list[str] | None = None,
        account_id: str | None = None,
        account_name: str | None = None,
    ) -> UUID:
        """Encrypt and store OAuth tokens via connect_platform."""
        credentials: dict[str, str] = {"access_token": access_token}
        if refresh_token:
            credentials["refresh_token"] = refresh_token

        connection = await self.connect_platform(
            org_id=org_id,
            platform=platform,
            auth_type=auth_type,
            credentials=credentials,
            account_id=account_id or "",
            account_name=account_name or "",
        )
        # Update token_expires_at and scopes if provided
        if token_expires_at or scopes:
            await self._repo.update_connection_token_metadata(
                connection.id, token_expires_at, scopes,
            )
        return connection.id

    async def get_expiring_tokens(
        self, within_minutes: int = 60
    ) -> list[PlatformConnection]:
        """Connections where token_expires_at < now() + interval. For proactive refresh."""
        return await self._repo.get_expiring_connections(within_minutes)

    async def refresh_connection_tokens(
        self,
        connection_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        token_expires_at: datetime | None = None,
    ) -> None:
        """Re-encrypt and update tokens after refresh."""
        credentials: dict[str, str] = {"access_token": access_token}
        if refresh_token:
            credentials["refresh_token"] = refresh_token

        cred_json = json.dumps(credentials)
        credential_enc = encrypt_token(cred_json, self._current_key)

        await self._repo.update_connection_credentials(
            connection_id,
            credential_enc=credential_enc,
            key_version=self._current_key_version,
            token_expires_at=token_expires_at,
        )

    # ── Label Management ──────────────────────────────────────────────────

    async def add_labels(
        self, item_id: UUID, org_id: UUID, labels: list[str]
    ) -> list[str]:
        """Add labels to a queue item. Max 20 per item, 50 chars each."""
        cleaned = [l.strip().lower()[:50] for l in labels if l.strip()]
        if not cleaned:
            return []
        return await self._repo.add_labels(item_id, org_id, cleaned)

    async def remove_labels(
        self, item_id: UUID, org_id: UUID, labels: list[str]
    ) -> list[str]:
        return await self._repo.remove_labels(item_id, org_id, labels)

    async def list_items_by_label(
        self, org_id: UUID, label: str, limit: int = 50
    ) -> list[QueueItem]:
        return await self._repo.list_items_by_label(org_id, label, limit)

    async def get_distinct_labels(self, org_id: UUID) -> list[str]:
        return await self._repo.get_distinct_labels(org_id)

    # ── Thumbnail Management ──────────────────────────────────────────────

    async def set_thumbnail(
        self, item_id: UUID, org_id: UUID, thumbnail_url: str
    ) -> None:
        """Set custom thumbnail for a publish queue item."""
        from ..common.url_validation import resolve_and_validate

        await resolve_and_validate(thumbnail_url)
        await self._repo.update_queue_item(
            item_id, org_id, thumbnail_url=thumbnail_url,
        )

    # ── Auto-Repost ───────────────────────────────────────────────────────

    async def mark_for_repost(
        self, item_id: UUID, org_id: UUID, interval_days: int, max_reposts: int = 3
    ) -> None:
        schedule = {"interval_days": interval_days, "max_reposts": max_reposts, "reposts_done": 0}
        await self._repo.mark_for_repost(item_id, org_id, schedule)

    async def process_reposts(self) -> int:
        """Create new draft items for pending reposts. Called by cron."""
        items = await self._repo.get_pending_reposts()
        created = 0
        for item in items:
            repost_schedule = (item.metadata or {}).get("repost_schedule", {})
            reposts_done = repost_schedule.get("reposts_done", 0)
            max_reposts = repost_schedule.get("max_reposts", 3)
            if reposts_done >= max_reposts:
                continue

            await self._repo.create_queue_item(
                org_id=item.org_id,
                platform=item.platform,
                connection_id=item.connection_id,
                content_parts=item.content_parts,
                group_id=item.group_id or item.id,
                metadata={"reposted_from": str(item.id)},
            )
            await self._repo.increment_repost_count(item.id)
            created += 1
        return created
