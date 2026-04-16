"""SEO service configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SeoSettings(BaseSettings):
    """SEO audit service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Feature flag
    enable_seo: bool = Field(default=False, description="Enable SEO audit service")

    # DataForSEO credentials
    dataforseo_login: str = Field(default="", description="DataForSEO API login")
    dataforseo_password: SecretStr = Field(
        default=SecretStr(""), description="DataForSEO API password"
    )

    # PageSpeed Insights (free, no key required for basic usage)
    pagespeed_api_key: SecretStr = Field(
        default=SecretStr(""), description="Google PageSpeed Insights API key (optional)"
    )

    # DataForSEO sandbox mode for CI/testing
    dataforseo_sandbox: bool = Field(
        default=False, description="Use DataForSEO sandbox (server_index=1)"
    )

    # Timeouts
    dataforseo_timeout: float = Field(
        default=60.0, description="DataForSEO request timeout in seconds"
    )
    pagespeed_timeout: float = Field(
        default=30.0, description="PageSpeed Insights timeout in seconds"
    )

    # Domain rank tracking
    domain_rank_polling_enabled: bool = Field(
        default=False, description="Enable weekly domain rank polling"
    )
