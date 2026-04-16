"""Session tracking configuration."""

from pydantic_settings import BaseSettings


class SessionSettings(BaseSettings):
    """Settings for session tracking."""

    model_config = {"env_prefix": "SESSION_"}

    max_transcript_bytes: int = 15 * 1024 * 1024  # 15MB
