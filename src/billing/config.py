"""Billing configuration with Stripe settings."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class StripeSettings(BaseSettings):
    """Stripe API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="STRIPE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: SecretStr = Field(..., description="Stripe secret API key")
    webhook_secret: SecretStr = Field(..., description="Stripe webhook signing secret")
    publishable_key: str = Field(..., description="Stripe publishable key")

    # Price IDs (configured in Stripe Dashboard) - simplified for 2-tier v1
    price_pro: str = Field(..., description="Pro tier price ID")
