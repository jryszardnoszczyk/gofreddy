"""GEO service configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.gemini_models import GEMINI_FLASH


class GeoSettings(BaseSettings):
    """GEO audit service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Feature flag
    enable_geo: bool = Field(default=False, description="Enable GEO audit service")

    # API keys
    cloro_api_key: SecretStr = Field(..., description="Cloro AI search API key")
    gemini_api_key: SecretStr = Field(..., description="Gemini API key for analysis/generation")

    # Gemini config
    gemini_model: str = Field(default=GEMINI_FLASH, description="Gemini model for GEO tasks")
    gemini_max_retries: int = Field(default=3, description="Max retries for Gemini calls")
    gemini_base_delay: float = Field(default=1.0, description="Base delay for retry backoff")

    # Pipeline config
    pipeline_timeout: float = Field(default=120.0, description="Total pipeline timeout in seconds")

    # Article generation
    article_max_word_count: int = Field(default=3000, description="Max word count for generated articles")
    article_model: str = Field(default="", description="Override model for article generation (defaults to gemini_model)")
