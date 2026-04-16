"""Cloudflare R2 storage for media assets (images, audio, documents)."""

from __future__ import annotations

import asyncio
import logging
import re
from uuid import UUID

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import R2Settings

logger = logging.getLogger(__name__)

VALID_FILENAME = re.compile(r"^[a-zA-Z0-9._-]{1,255}$")


class R2MediaStorage:
    """R2 storage for media assets — presigned-URL upload/download, head, delete."""

    MAX_MEDIA_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_PRESIGNED_EXPIRATION = 604800  # 7 days (R2 limit)

    def __init__(self, session: aioboto3.Session, config: R2Settings) -> None:
        self._session = session
        self._config = config
        self._client_config = Config(
            max_pool_connections=50,
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 3, "mode": "adaptive"},
            signature_version="s3v4",
        )
        self._client = None
        self._client_lock = asyncio.Lock()

    # ── helpers ──

    def _validate_filename(self, filename: str) -> None:
        """Validate filename to prevent path traversal."""
        if not VALID_FILENAME.match(filename):
            raise ValueError(f"Invalid filename: {filename}")

    def _media_key(self, org_id: UUID, asset_id: UUID, filename: str) -> str:
        """Generate R2 key for a media asset."""
        self._validate_filename(filename)
        return f"media/{org_id}/{asset_id}/{filename}"

    # ── client lifecycle ──

    async def _get_client(self):
        """Get or create a reusable S3 client (thread-safe)."""
        if self._client is not None:
            return self._client
        async with self._client_lock:
            if self._client is None:
                self._client = await self._session.client(
                    "s3",
                    endpoint_url=self._config.endpoint_url,
                    region_name="auto",
                    aws_access_key_id=self._config.access_key_id,
                    aws_secret_access_key=self._config.secret_access_key.get_secret_value(),
                    config=self._client_config,
                ).__aenter__()
        return self._client

    async def close(self) -> None:
        """Close the client connection pool."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    # ── presigned URLs ──

    async def generate_upload_url(
        self,
        org_id: UUID,
        asset_id: UUID,
        filename: str,
        content_type: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a presigned PUT URL for client-side upload."""
        key = self._media_key(org_id, asset_id, filename)
        client = await self._get_client()
        url = await client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._config.bucket_name,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=min(expires_in_seconds, self.MAX_PRESIGNED_EXPIRATION),
        )
        return url

    async def generate_download_url(
        self,
        org_id: UUID,
        asset_id: UUID,
        filename: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a presigned GET URL for client-side download."""
        key = self._media_key(org_id, asset_id, filename)
        client = await self._get_client()
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._config.bucket_name, "Key": key},
            ExpiresIn=min(expires_in_seconds, self.MAX_PRESIGNED_EXPIRATION),
        )

    # ── object operations ──

    async def head(
        self, org_id: UUID, asset_id: UUID, filename: str
    ) -> dict | None:
        """Return object metadata or None if not found."""
        key = self._media_key(org_id, asset_id, filename)
        client = await self._get_client()
        try:
            resp = await client.head_object(
                Bucket=self._config.bucket_name, Key=key
            )
            return {
                "size_bytes": resp["ContentLength"],
                "content_type": resp["ContentType"],
                "last_modified": resp["LastModified"],
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            raise

    async def delete(
        self, org_id: UUID, asset_id: UUID, filename: str
    ) -> bool:
        """Delete a media object. Returns True on success, False on error."""
        key = self._media_key(org_id, asset_id, filename)
        client = await self._get_client()
        try:
            await client.delete_object(
                Bucket=self._config.bucket_name, Key=key
            )
            return True
        except ClientError:
            logger.exception("Failed to delete media object %s", key)
            return False
