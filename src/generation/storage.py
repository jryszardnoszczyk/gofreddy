"""R2 storage for generated video content."""

import logging
import re
from uuid import UUID

from ..storage.config import R2Settings
from ..storage.r2_storage import R2VideoStorage

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_FILENAME_RE = re.compile(r"^(cadre_\d+|final)\.mp4$|^frame_\d+\.png$")
_PREVIEW_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.png$")

GENERATION_PREFIX = "generated"
PREVIEW_PREFIX = "previews"
MAX_GENERATION_SIZE = 500 * 1024 * 1024  # 500MB
PRESIGNED_URL_EXPIRY = 3600  # 1 hour


class R2GenerationStorage:
    """R2 storage for generated video content.

    Key structure: generated/{user_id}/{generation_id}/{filename}
    where filename matches ^(cadre_\\d+|final)\\.mp4$
    """

    def __init__(self, video_storage: R2VideoStorage, settings: R2Settings) -> None:
        self._video_storage = video_storage
        self._settings = settings

    def _generation_key(self, user_id: UUID, generation_id: UUID, filename: str) -> str:
        uid = str(user_id)
        gid = str(generation_id)
        if not _UUID_RE.match(uid) or not _UUID_RE.match(gid):
            raise ValueError("Invalid UUID format in storage key")
        if not _FILENAME_RE.match(filename):
            raise ValueError(f"Invalid filename: {filename}")
        return f"{GENERATION_PREFIX}/{uid}/{gid}/{filename}"

    async def upload_video(
        self, user_id: UUID, generation_id: UUID, filename: str, data: bytes
    ) -> str:
        key = self._generation_key(user_id, generation_id, filename)
        s3_client = await self._video_storage._get_client()
        content_type = "image/png" if filename.endswith(".png") else "video/mp4"
        await s3_client.put_object(
            Bucket=self._settings.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    async def get_presigned_url(
        self,
        r2_key: str,
        expiry: int = PRESIGNED_URL_EXPIRY,
    ) -> str:
        s3_client = await self._video_storage._get_client()
        return await s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._settings.bucket_name, "Key": r2_key},
            ExpiresIn=min(expiry, 7 * 24 * 3600),
        )

    def preview_key(self, user_id: UUID, filename: str) -> str:
        uid = str(user_id)
        if not _UUID_RE.match(uid):
            raise ValueError("Invalid UUID format in storage key")
        if not _PREVIEW_FILENAME_RE.match(filename):
            raise ValueError(f"Invalid preview filename: {filename}")
        return f"{PREVIEW_PREFIX}/{uid}/{filename}"

    async def upload_preview(self, user_id: UUID, filename: str, data: bytes) -> str:
        key = self.preview_key(user_id, filename)
        s3_client = await self._video_storage._get_client()
        await s3_client.put_object(
            Bucket=self._settings.bucket_name,
            Key=key,
            Body=data,
            ContentType="image/png",
        )
        return key

    async def get_preview_url(self, r2_key: str, expiry: int = PRESIGNED_URL_EXPIRY) -> str:
        return await self.get_presigned_url(r2_key, expiry)

    async def download_preview(self, r2_key: str) -> bytes:
        """Download preview image bytes from R2 by key."""
        s3_client = await self._video_storage._get_client()
        response = await s3_client.get_object(
            Bucket=self._settings.bucket_name, Key=r2_key
        )
        body = response["Body"]
        try:
            return await body.read()
        finally:
            body.close()

    async def delete_generation(self, user_id: UUID, generation_id: UUID) -> None:
        """Delete all files for a generation (cadres + final)."""
        uid, gid = str(user_id), str(generation_id)
        if not _UUID_RE.match(uid) or not _UUID_RE.match(gid):
            raise ValueError("Invalid UUID format in storage key")
        prefix = f"{GENERATION_PREFIX}/{uid}/{gid}/"
        s3_client = await self._video_storage._get_client()
        response = await s3_client.list_objects_v2(
            Bucket=self._settings.bucket_name,
            Prefix=prefix,
            MaxKeys=20,
        )
        contents = response.get("Contents", [])
        if len(contents) >= 20:
            logger.warning("Unexpectedly many objects under %s", prefix)
        for obj in contents:
            await s3_client.delete_object(
                Bucket=self._settings.bucket_name, Key=obj["Key"]
            )
