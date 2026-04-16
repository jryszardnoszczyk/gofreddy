"""Configuration for platform video fetchers."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class FetcherSettings(BaseSettings):
    """API credentials and settings for video fetchers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ScrapeCreators (TikTok)
    scrapecreators_api_key: SecretStr = Field(
        ...,
        description="ScrapeCreators API key for TikTok data",
    )
    scrapecreators_base_url: str = Field(
        default="https://api.scrapecreators.com",
        description="ScrapeCreators API base URL",
    )

    # Apify (Instagram)
    apify_token: SecretStr = Field(
        ...,
        description="Apify API token for Instagram scrapers",
    )

    # Influencers.club (IC)
    ic_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Influencers.club API key for creator discovery",
    )
    ic_base_url: str = Field(
        default="https://api-dashboard.influencers.club",
        description="Influencers.club API base URL",
    )

    # Timeouts and limits
    api_timeout_seconds: float = Field(default=30.0)
    download_timeout_seconds: float = Field(default=300.0)
    max_concurrent_downloads: int = Field(default=30)
    max_retry_attempts: int = Field(default=3)
    max_url_refetch_attempts: int = Field(default=1)
