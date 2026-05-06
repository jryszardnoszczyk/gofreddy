"""GEO service configuration."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default model for GEO text-side calls. Switched from Gemini Flash to Claude
# Sonnet on 2026-05-06 (Gemini removed from text/judge sites). The Claude CLI
# resolves the actual model via its own config; this string is recorded into
# generation metadata for observability + passed through `--model`.
_DEFAULT_MODEL = "claude-sonnet-4-6"


class GeoSettings(BaseSettings):
    """GEO audit service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Feature flag
    enable_geo: bool = Field(default=False, description="Enable GEO audit service")

    # API keys.
    # `gemini_api_key` is retained for backward compatibility with deployments
    # whose .env still sets GEMINI_API_KEY. As of 2026-05-06 it is not read by
    # the analyzer / generator (Claude CLI handles auth itself). Kept here so
    # existing .env files don't fail validation.
    cloro_api_key: SecretStr = Field(..., description="Cloro AI search API key")
    gemini_api_key: SecretStr = Field(default=SecretStr(""), description="Gemini API key (unused — kept for env compat)")

    # Model config — the field names are kept (gemini_model, gemini_max_retries,
    # gemini_base_delay) to avoid churning callers. The values are now Claude
    # model slugs / Claude-CLI retry knobs.
    gemini_model: str = Field(default=_DEFAULT_MODEL, description="Model name for GEO text tasks (Claude as of 2026-05-06)")
    gemini_max_retries: int = Field(default=3, description="Max retries for LLM calls")
    gemini_base_delay: float = Field(default=1.0, description="Base delay for retry backoff")

    # Pipeline config
    pipeline_timeout: float = Field(default=120.0, description="Total pipeline timeout in seconds")

    # Article generation
    article_max_word_count: int = Field(default=3000, description="Max word count for generated articles")
    article_model: str = Field(default="", description="Override model for article generation (defaults to gemini_model)")
