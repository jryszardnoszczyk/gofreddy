"""Analysis module configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.gemini_models import GEMINI_FLASH_LITE


class AnalysisSettings(BaseSettings):
    """Gemini analysis configuration."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: SecretStr = Field(..., description="Gemini API key")
    model: str = Field(default=GEMINI_FLASH_LITE, description="Gemini model name")
    max_retries: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=10.0, ge=1.0, le=60.0)
    max_concurrent: int = Field(default=50, ge=1, le=200)

    def __repr__(self) -> str:
        """Hide secrets in repr."""
        return f"AnalysisSettings(model='{self.model}')"


class DatabaseSettings(BaseSettings):
    """Database configuration for analysis repository."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr = Field(..., alias="DATABASE_URL", description="PostgreSQL connection string")
    pool_min_size: int = Field(default=5, ge=1, le=20)
    pool_max_size: int = Field(default=20, ge=2, le=100)
    command_timeout: float = Field(default=60.0, ge=5.0, le=300.0)

    def __repr__(self) -> str:
        """Hide connection string in repr."""
        return f"DatabaseSettings(pool_min={self.pool_min_size}, pool_max={self.pool_max_size})"


class LaneRoutingSettings(BaseSettings):
    """Transcript-first lane routing configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LANE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    transcript_first_enabled: bool = True  # L1 for quality transcripts, L2 fallback
    quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
