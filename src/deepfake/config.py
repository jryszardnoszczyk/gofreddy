"""Configuration for deepfake detection services."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepfakeConfig(BaseSettings):
    """Configuration for deepfake detection services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="DEEPFAKE_",
    )

    # Reality Defender API
    reality_defender_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Reality Defender API key",
    )
    reality_defender_base_url: str = Field(
        default="https://api.realitydefender.com/v1",
        description="Reality Defender API base URL",
    )
    reality_defender_enabled: bool = Field(
        default=True,
        description="Enable Reality Defender provider",
    )

    # LIPINC configuration (managed service via Replicate)
    lipinc_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="LIPINC hosted service API key",
    )
    lipinc_base_url: str = Field(
        default="https://api.replicate.com/v1",
        description="LIPINC API endpoint",
    )
    lipinc_model_version: str = Field(
        default="lipinc-v2:latest",
        description="LIPINC model version on hosting platform",
    )
    lipinc_enabled: bool = Field(
        default=True,
        description="Enable LIPINC provider",
    )

    # Processing settings
    api_timeout_seconds: float = Field(default=120.0, ge=10.0, le=600.0)
    upload_timeout_seconds: float = Field(default=300.0, ge=60.0, le=900.0)

    # Retry settings (simple retry with backoff, NO circuit breaker)
    max_retries: int = Field(default=3, ge=1, le=10)
    base_delay_seconds: float = Field(default=1.0, ge=0.5, le=10.0)

    # Scoring threshold
    deepfake_threshold: float = Field(default=0.50, ge=0.3, le=0.8)

    # Caching
    cache_ttl_days: int = Field(default=30, ge=1, le=90)

    # Cost protection
    daily_spend_limit_cents: int = Field(
        default=10000, ge=100, le=100000
    )  # $100/day default
