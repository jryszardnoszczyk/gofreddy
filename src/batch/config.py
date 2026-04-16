"""Batch processing configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BatchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BATCH_")

    concurrency: int = 50
    rate_limit_per_sec: int = 50
    max_retries: int = 3
    claim_timeout_seconds: int = 300
    backoff_base: float = 1.0
    deadline_seconds: int = 540
