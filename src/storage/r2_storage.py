"""Cloudflare R2 storage implementation."""

import asyncio
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import aiofiles
import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from ..common.enums import Platform
from .config import R2Settings
from .exceptions import StorageError, UploadError, VideoNotFoundError

# Input validation
VALID_VIDEO_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Immutable metadata for a stored video."""

    key: str
    platform: Platform
    video_id: str
    size_bytes: int
    last_modified: datetime


@dataclass(frozen=True)
class VideoListResult:
    """Paginated list of videos in storage."""

    videos: list[VideoMetadata]
    total_count: int
    has_more: bool
    next_cursor: str | None


class VideoStorage(Protocol):
    """Protocol for video storage operations."""

    async def upload(
        self,
        local_path: Path,
        platform: Platform,
        video_id: str,
    ) -> VideoMetadata:
        """Upload video file to storage."""
        ...

    async def download_to_temp(
        self,
        platform: Platform,
        video_id: str,
    ) -> Path:
        """Download video to temp file, return path."""
        ...

    async def get_metadata(
        self,
        platform: Platform,
        video_id: str,
    ) -> VideoMetadata | None:
        """Get video metadata without downloading."""
        ...

    async def exists(self, platform: Platform, video_id: str) -> bool:
        """Check if video exists in storage."""
        ...

    async def delete(self, platform: Platform, video_id: str) -> bool:
        """Delete video. Returns True if deleted, False if not found."""
        ...

    async def generate_download_url(
        self,
        platform: Platform,
        video_id: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate presigned URL for download (max 7 days for R2). Returns URL string."""
        ...

    async def list_videos(
        self,
        platform: Platform | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> VideoListResult:
        """List videos with optional platform filter."""
        ...


class R2VideoStorage:
    """Cloudflare R2 implementation of VideoStorage protocol."""

    DOWNLOAD_CHUNK_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_PRESIGNED_EXPIRATION = 604800  # 7 days (R2 limit)
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB limit

    def __init__(self, session: aioboto3.Session, config: R2Settings):
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

    def _validate_video_id(self, video_id: str) -> None:
        """Validate video_id to prevent path traversal."""
        if not VALID_VIDEO_ID.match(video_id):
            raise ValueError(f"Invalid video_id format: {video_id}")

    def _video_key(self, platform: Platform, video_id: str) -> str:
        """Generate R2 key for video file with validation."""
        self._validate_video_id(video_id)
        return f"videos/{platform.value}/{video_id}.mp4"

    def _parse_key(self, key: str) -> tuple[Platform, str] | None:
        """Parse R2 key to extract platform and video_id."""
        parts = key.split("/")
        if len(parts) != 3 or parts[0] != "videos":
            return None
        try:
            platform = Platform(parts[1])
            video_id = parts[2].removesuffix(".mp4")
            return platform, video_id
        except ValueError:
            return None

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

    async def close(self):
        """Close the client connection pool."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def upload(
        self,
        local_path: Path,
        platform: Platform,
        video_id: str,
    ) -> VideoMetadata:
        """Upload video file to storage."""
        key = self._video_key(platform, video_id)

        if not local_path.exists():
            raise UploadError(platform, video_id, FileNotFoundError(str(local_path)))

        file_size = local_path.stat().st_size
        if file_size > self.MAX_VIDEO_SIZE:
            raise UploadError(
                platform,
                video_id,
                ValueError(f"File too large: {file_size} > {self.MAX_VIDEO_SIZE}"),
            )

        client = await self._get_client()
        try:
            await client.upload_file(
                str(local_path),
                self._config.bucket_name,
                key,
                ExtraArgs={"ContentType": "video/mp4"},
            )
        except ClientError as e:
            raise UploadError(platform, video_id, e) from e

        return VideoMetadata(
            key=key,
            platform=platform,
            video_id=video_id,
            size_bytes=file_size,
            last_modified=datetime.now(timezone.utc),
        )

    async def download_to_temp(
        self,
        platform: Platform,
        video_id: str,
    ) -> Path:
        """Download video to temp file, return path.

        Enforces MAX_VIDEO_SIZE byte limit. Caller must unlink returned path.
        """
        key = self._video_key(platform, video_id)
        client = await self._get_client()

        try:
            response = await client.get_object(
                Bucket=self._config.bucket_name, Key=key
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise VideoNotFoundError(platform, video_id) from e
            raise StorageError(f"Download failed: {e}") from e

        # Fast reject via declared content-length (same atomic response)
        content_length = response.get("ContentLength", 0)
        if content_length and content_length > self.MAX_VIDEO_SIZE:
            response["Body"].close()
            raise StorageError(
                f"Object too large: {content_length} > {self.MAX_VIDEO_SIZE}"
            )

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp4", prefix=f"{platform.value}_{video_id}_", delete=False
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        body = response["Body"]
        try:
            bytes_downloaded = 0
            async with aiofiles.open(temp_path, "wb") as f:
                async for chunk in body.iter_chunks(self.DOWNLOAD_CHUNK_SIZE):
                    bytes_downloaded += len(chunk)
                    if bytes_downloaded > self.MAX_VIDEO_SIZE:
                        raise StorageError(
                            f"Download aborted: exceeded {self.MAX_VIDEO_SIZE} bytes "
                            f"({bytes_downloaded} downloaded so far)"
                        )
                    await f.write(chunk)
        except Exception:
            # Clean up temp file on ANY failure (size limit, IO error, etc.)
            temp_path.unlink(missing_ok=True)
            raise
        finally:
            body.close()

        return temp_path

    async def get_metadata(
        self,
        platform: Platform,
        video_id: str,
    ) -> VideoMetadata | None:
        """Get video metadata without downloading."""
        key = self._video_key(platform, video_id)
        client = await self._get_client()

        try:
            response = await client.head_object(
                Bucket=self._config.bucket_name, Key=key
            )
            return VideoMetadata(
                key=key,
                platform=platform,
                video_id=video_id,
                size_bytes=response["ContentLength"],
                last_modified=response["LastModified"],
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise StorageError(f"Failed to get metadata: {e}") from e

    async def exists(self, platform: Platform, video_id: str) -> bool:
        """Check if video exists in storage."""
        return await self.get_metadata(platform, video_id) is not None

    async def delete(self, platform: Platform, video_id: str) -> bool:
        """Delete video. Returns True if deleted, False if not found."""
        key = self._video_key(platform, video_id)
        client = await self._get_client()

        exists = await self.exists(platform, video_id)
        if not exists:
            return False

        try:
            await client.delete_object(Bucket=self._config.bucket_name, Key=key)
            return True
        except ClientError as e:
            raise StorageError(f"Delete failed: {e}") from e

    async def generate_download_url(
        self,
        platform: Platform,
        video_id: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate presigned URL for download (max 7 days for R2)."""
        key = self._video_key(platform, video_id)
        client = await self._get_client()

        expires_in_seconds = min(expires_in_seconds, self.MAX_PRESIGNED_EXPIRATION)

        try:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._config.bucket_name, "Key": key},
                ExpiresIn=expires_in_seconds,
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned URL: {e}") from e

    async def list_videos(
        self,
        platform: Platform | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> VideoListResult:
        """List videos with optional platform filter."""
        client = await self._get_client()
        prefix = f"videos/{platform.value}/" if platform else "videos/"

        params = {
            "Bucket": self._config.bucket_name,
            "Prefix": prefix,
            "MaxKeys": limit,
        }
        if cursor:
            params["ContinuationToken"] = cursor

        try:
            response = await client.list_objects_v2(**params)
        except ClientError as e:
            raise StorageError(f"List failed: {e}") from e

        videos = []
        for obj in response.get("Contents", []):
            parsed = self._parse_key(obj["Key"])
            if parsed:
                plat, vid_id = parsed
                videos.append(
                    VideoMetadata(
                        key=obj["Key"],
                        platform=plat,
                        video_id=vid_id,
                        size_bytes=obj["Size"],
                        last_modified=obj["LastModified"],
                    )
                )

        return VideoListResult(
            videos=videos,
            total_count=len(videos),
            has_more=response.get("IsTruncated", False),
            next_cursor=response.get("NextContinuationToken"),
        )
