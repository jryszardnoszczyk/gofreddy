"""Competitive intelligence configuration."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class CompetitiveSettings(BaseSettings):
    """Configuration for competitive ad intelligence providers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="COMPETITIVE_",
    )

    foreplay_api_key: SecretStr = SecretStr("")
    foreplay_timeout_seconds: int = 30
    adyntel_api_key: SecretStr = SecretStr("")
    adyntel_email: str = ""
    adyntel_timeout_seconds: int = 30
    adyntel_max_pages: int = 1
    foreplay_daily_credit_limit: int = 5000
    enable_vision_enrichment: bool = True
