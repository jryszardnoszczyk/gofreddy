"""Cloudflare R2 storage configuration."""

import re

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class R2Settings(BaseSettings):
    """Cloudflare R2 storage configuration."""

    model_config = SettingsConfigDict(
        env_prefix="R2_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    account_id: str = Field(..., min_length=1, description="Cloudflare account ID")
    access_key_id: str = Field(..., min_length=1, description="R2 API access key ID")
    secret_access_key: SecretStr = Field(..., description="R2 API secret access key")
    bucket_name: str = Field(default="freddy", min_length=1)

    @field_validator("account_id")
    @classmethod
    def validate_account_id(cls, v: str) -> str:
        """Validate Cloudflare account ID format (32 hex chars)."""
        if not re.match(r"^[a-f0-9]{32}$", v):
            raise ValueError("account_id must be a 32-character hex string")
        return v

    @property
    def endpoint_url(self) -> str:
        """R2 S3-compatible endpoint."""
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    def __repr__(self) -> str:
        """Hide secrets in repr."""
        return f"R2Settings(account_id='{self.account_id}', bucket_name='{self.bucket_name}')"
