"""Supabase authentication configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupabaseSettings(BaseSettings):
    """Supabase project configuration for JWT-based auth."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = Field(..., min_length=1, description="Supabase project URL")
    supabase_anon_key: str = Field(..., min_length=1, description="Supabase anon/public key")
    supabase_jwt_secret: SecretStr = Field(
        ..., min_length=1, description="JWT secret for token verification"
    )
