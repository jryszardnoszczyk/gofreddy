"""R2 storage for session iteration logs and state snapshots."""

import logging
import re

from ..storage.config import R2Settings
from ..storage.r2_storage import R2VideoStorage

logger = logging.getLogger(__name__)

# UUID format: 8-4-4-4-12 hex chars with hyphens
_VALID_SESSION_ID = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")


class R2SessionLogStorage:
    """Upload session logs to R2 instead of storing in PostgreSQL.

    Uses the same underlying S3 client as R2VideoStorage.
    Key format: session-logs/{session_id}/iteration-{NNN}.txt
    """

    PREFIX = "session-logs"

    def __init__(self, video_storage: R2VideoStorage, r2_config: R2Settings) -> None:
        self._storage = video_storage
        self._config = r2_config

    def _validate_session_id(self, session_id: str) -> None:
        if not _VALID_SESSION_ID.match(session_id):
            raise ValueError(f"Invalid session_id format: {session_id}")

    async def upload_log(self, session_id: str, iteration_number: int, log_content: str) -> str:
        """Upload iteration log text to R2. Returns the R2 key."""
        self._validate_session_id(session_id)
        key = f"{self.PREFIX}/{session_id}/iteration-{iteration_number:03d}.txt"
        client = await self._storage._get_client()
        await client.put_object(
            Bucket=self._config.bucket_name,
            Key=key,
            Body=log_content.encode("utf-8"),
            ContentType="text/plain",
        )
        logger.info("Uploaded iteration log to R2: %s (%d bytes)", key, len(log_content))
        return key

    async def upload_state(self, session_id: str, iteration_number: int, state_content: str) -> str:
        """Upload state snapshot to R2. Returns the R2 key."""
        self._validate_session_id(session_id)
        key = f"{self.PREFIX}/{session_id}/state-{iteration_number:03d}.md"
        client = await self._storage._get_client()
        await client.put_object(
            Bucket=self._config.bucket_name,
            Key=key,
            Body=state_content.encode("utf-8"),
            ContentType="text/markdown",
        )
        logger.info("Uploaded state snapshot to R2: %s (%d bytes)", key, len(state_content))
        return key
