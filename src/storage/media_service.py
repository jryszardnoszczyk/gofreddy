"""Thin orchestration layer over R2MediaStorage + PostgresMediaAssetRepository."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Any
from uuid import UUID

from .media_repository import MediaAsset, PostgresMediaAssetRepository
from .r2_media_storage import R2MediaStorage

logger = logging.getLogger(__name__)

_UPLOAD_URL_EXPIRY = 3600  # 1 hour
_DOWNLOAD_URL_EXPIRY = 3600  # 1 hour


class MediaService:
    """Composes R2 storage + Postgres repository for media asset operations."""

    def __init__(
        self,
        storage: R2MediaStorage,
        repository: PostgresMediaAssetRepository,
    ) -> None:
        self._storage = storage
        self._repo = repository

    # ── helpers ──

    @staticmethod
    def _asset_to_dict(asset: MediaAsset, download_url: str | None = None) -> dict[str, Any]:
        """Convert a MediaAsset dataclass to a JSON-friendly dict."""
        data = asdict(asset)
        if download_url:
            data["download_url"] = download_url
        return data

    # ── public API (matches router call signatures) ──

    async def count_pending(self, user_id: UUID) -> int:
        """Count pending uploads for a user/org."""
        return await self._repo.count_pending(org_id=user_id)

    async def create_upload(
        self,
        user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> dict[str, Any]:
        """Create a pending DB record and generate a presigned upload URL."""
        asset_id = uuid.uuid4()
        # Sanitise filename for R2 key (replace spaces/special chars)
        safe_filename = filename.replace(" ", "_")

        asset = await self._repo.create_asset(
            org_id=user_id,
            r2_key=f"media/{user_id}/{asset_id}/{safe_filename}",
            filename=filename,
            content_type=content_type,
            asset_type=content_type.split("/")[0],  # image, video, audio
            source="upload",
            size_bytes=size_bytes,
        )

        upload_url = await self._storage.generate_upload_url(
            org_id=user_id,
            asset_id=asset.id,
            filename=safe_filename,
            content_type=content_type,
            expires_in_seconds=_UPLOAD_URL_EXPIRY,
        )

        return {
            "asset_id": str(asset.id),
            "upload_url": upload_url,
            "expires_in": _UPLOAD_URL_EXPIRY,
        }

    async def confirm_upload(
        self, user_id: UUID, asset_id: UUID,
    ) -> dict[str, Any]:
        """HEAD-check on R2 then confirm the asset in the DB."""
        # Fetch the pending asset first
        asset = await self._repo.get_asset(asset_id, org_id=user_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found")
        if asset.status != "pending":
            raise ValueError(f"Asset {asset_id} is not pending (status={asset.status})")

        # Sanitise filename for R2 key lookup
        safe_filename = asset.filename.replace(" ", "_")

        # HEAD check on R2
        head = await self._storage.head(
            org_id=user_id, asset_id=asset_id, filename=safe_filename,
        )
        if head is None:
            raise ValueError(f"Asset {asset_id} not found in storage — upload may not have completed")

        actual_size = head["size_bytes"]

        confirmed = await self._repo.confirm_asset(
            asset_id=asset_id, org_id=user_id, size_bytes=actual_size,
        )
        if confirmed is None:
            raise ValueError(f"Failed to confirm asset {asset_id}")

        return self._asset_to_dict(confirmed)

    async def list_assets(
        self,
        user_id: UUID,
        asset_type: str | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List assets with optional filters, attaching download URLs."""
        assets = await self._repo.list_assets(
            org_id=user_id,
            asset_type=asset_type,
            source=source,
            limit=limit,
            offset=offset,
        )
        results = []
        for asset in assets:
            if asset.status == "ready":
                safe_filename = asset.filename.replace(" ", "_")
                url = await self._storage.generate_download_url(
                    org_id=user_id,
                    asset_id=asset.id,
                    filename=safe_filename,
                    expires_in_seconds=_DOWNLOAD_URL_EXPIRY,
                )
                results.append(self._asset_to_dict(asset, download_url=url))
            else:
                results.append(self._asset_to_dict(asset))
        return results

    async def get_asset(
        self, user_id: UUID, asset_id: UUID,
    ) -> dict[str, Any]:
        """Get a single asset with download URL."""
        asset = await self._repo.get_asset(asset_id, org_id=user_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found")

        download_url = None
        if asset.status == "ready":
            safe_filename = asset.filename.replace(" ", "_")
            download_url = await self._storage.generate_download_url(
                org_id=user_id,
                asset_id=asset.id,
                filename=safe_filename,
                expires_in_seconds=_DOWNLOAD_URL_EXPIRY,
            )
        return self._asset_to_dict(asset, download_url=download_url)

    async def delete_asset(
        self, user_id: UUID, asset_id: UUID,
    ) -> bool:
        """Soft-delete an asset."""
        deleted = await self._repo.soft_delete(asset_id, org_id=user_id)
        if not deleted:
            raise ValueError(f"Asset {asset_id} not found")
        return True

    async def get_download_url(
        self, user_id: UUID, asset_id: UUID,
    ) -> str:
        """Generate a presigned download URL for an asset."""
        asset = await self._repo.get_asset(asset_id, org_id=user_id)
        if asset is None:
            raise ValueError(f"Asset {asset_id} not found")
        if asset.status != "ready":
            raise ValueError(f"Asset {asset_id} is not ready (status={asset.status})")

        safe_filename = asset.filename.replace(" ", "_")
        return await self._storage.generate_download_url(
            org_id=user_id,
            asset_id=asset.id,
            filename=safe_filename,
            expires_in_seconds=_DOWNLOAD_URL_EXPIRY,
        )
