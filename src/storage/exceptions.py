"""Storage-specific exceptions."""

from ..common.enums import Platform


class StorageError(Exception):
    """Base storage exception."""

    pass


class VideoNotFoundError(StorageError):
    """Video does not exist in storage."""

    def __init__(self, platform: Platform, video_id: str):
        super().__init__(f"Video not found: {platform.value}/{video_id}")
        self.platform = platform
        self.video_id = video_id


class UploadError(StorageError):
    """Failed to upload video."""

    def __init__(
        self, platform: Platform, video_id: str, cause: Exception | None = None
    ):
        msg = f"Upload failed for {platform.value}/{video_id}"
        if cause:
            msg = f"{msg}: {cause}"
        super().__init__(msg)
        self.platform = platform
        self.video_id = video_id
