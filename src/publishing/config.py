"""Publishing module configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PublishingSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="PUBLISHING_"
    )

    enabled: bool = Field(default=False, description="Feature flag for publishing")
    encryption_secret: SecretStr = Field(
        ..., description="AES-256-GCM key for token encryption (key version 1)"
    )
    encryption_secret_v2: SecretStr | None = Field(
        default=None,
        description="Rotation key (key version 2) — set during rotation",
    )

    # Queue limits
    max_queue_items_per_org: int = Field(
        default=500, description="Max draft+scheduled items per org"
    )
    # Dispatch
    dispatch_batch_size: int = Field(
        default=25, description="Max items per dispatch cycle"
    )
    dispatch_deadline_seconds: int = Field(
        default=200, description="Dispatch deadline (< 240s Cloud Run)"
    )

    # Adapter resilience
    adapter_timeout_seconds: float = Field(
        default=30.0, description="Per-adapter publish timeout"
    )
    adapter_concurrency: int = Field(
        default=3, description="Semaphore limit for parallel publishes"
    )
    circuit_breaker_threshold: int = Field(
        default=3, description="Failures before circuit opens"
    )
    circuit_breaker_reset_seconds: float = Field(
        default=60.0, description="Seconds before half-open probe"
    )

    # WordPress
    wordpress_timeout_seconds: float = Field(
        default=30.0, description="WordPress REST API timeout"
    )

    # Webhook (signing secret is per-connection, stored in credential_enc)
    webhook_timeout_seconds: float = Field(
        default=10.0, description="Webhook delivery timeout"
    )

    # Platform OAuth credentials (for device flow)
    linkedin_client_id: str = ""
    linkedin_client_secret: SecretStr | None = None
    tiktok_client_key: str = ""
    tiktok_client_secret: SecretStr | None = None
    youtube_client_id: str = ""
    youtube_client_secret: SecretStr | None = None
