"""Monitoring module configuration."""

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MonitoringSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="MONITORING_"
    )

    enabled: bool = Field(default=False, description="Feature flag for monitoring")
    max_monitors_per_user: int = Field(default=10, description="Monitor quota per user")
    max_sources_per_monitor: int = Field(default=5, description="Sources per monitor")
    max_mentions_per_ingest: int = Field(default=1000, description="Batch size cap")
    adapter_timeout_seconds: float = Field(
        default=30.0, description="Per-adapter fetch timeout"
    )
    adapter_concurrency: int = Field(
        default=3, description="Semaphore limit for parallel source fetches"
    )
    circuit_breaker_threshold: int = Field(
        default=3, description="Failures before circuit opens"
    )
    circuit_breaker_reset_seconds: float = Field(
        default=60.0, description="Seconds before half-open probe"
    )
    # Bluesky AT Protocol (free, no auth required for search)
    bluesky_base_url: str = Field(
        default="https://api.bsky.app",
        description="Bluesky public API base URL",
    )
    # Apify-based adapters need longer timeouts (actor spin-up + scrape)
    apify_adapter_timeout_seconds: float = Field(
        default=120.0, description="Timeout for Apify actor runs (Facebook, LinkedIn)"
    )
    pod_engine_api_key: str = Field(default="", description="Pod Engine API key")

    # Alerting (PR-068)
    webhook_signing_secret: SecretStr = Field(
        default=SecretStr(""), description="HMAC-SHA256 signing secret for webhooks"
    )
    max_alert_rules_per_monitor: int = Field(
        default=5, description="Alert rules per monitor"
    )
    webhook_timeout_seconds: float = Field(
        default=10.0, description="Webhook delivery timeout"
    )
    webhook_circuit_breaker_threshold: int = Field(
        default=10, description="Consecutive failures before disabling webhook"
    )

    # Adapter API keys
    newsdata_api_key: SecretStr = Field(
        default=SecretStr(""), description="NewsData.io API key"
    )
    xpoz_api_key: SecretStr = Field(
        default=SecretStr(""), description="Xpoz API key"
    )
    apify_token: SecretStr = Field(
        default=SecretStr(""),
        description="Apify API token for TikTok scraper",
        # Apify is a single shared service across the whole app — the
        # non-prefixed APIFY_TOKEN env var is the canonical source. We
        # also accept the MONITORING_APIFY_TOKEN prefixed form so
        # existing deployments that copied the value under the prefixed
        # name keep working. Either variable resolves; there is no
        # reason to set both.
        validation_alias=AliasChoices("APIFY_TOKEN", "MONITORING_APIFY_TOKEN"),
    )
    cloro_api_key: SecretStr = Field(
        default=SecretStr(""), description="Cloro API key for AI search monitoring"
    )

    # Scheduling (PR-067)
    gcp_project: str = Field(default="", description="GCP project ID for Cloud Tasks")
    gcp_location: str = Field(default="europe-west1", description="GCP location")
    service_url: str = Field(default="", description="Cloud Run service URL")
    service_account_email: str = Field(
        default="", description="Service account for OIDC"
    )
    dispatch_deadline_seconds: int = Field(
        default=900, description="Cloud Tasks dispatch deadline"
    )

    # Intelligence layer (PR-071)
    intent_batch_size: int = Field(
        default=20, description="Mentions per Gemini intent classification call"
    )
    intent_daily_cap: int = Field(
        default=1000, description="Max intent classifications per monitor per day"
    )
    sentiment_batch_size: int = Field(
        default=20, description="Mentions per Gemini sentiment classification call"
    )
    max_competitors: int = Field(
        default=10, description="Max competitor brands per monitor for SOV"
    )
    workspace_save_max: int = Field(
        default=2000, description="Max mentions per workspace save"
    )

    # Anomaly correlation (digest agent Layer 1+2)
    anomaly_volume_spike_pct: float = Field(
        default=1.5, description="Volume spike: mention count > N× 7-day rolling avg"
    )
    anomaly_sentiment_shift: float = Field(
        default=0.15, description="Sentiment shift threshold on -1/+1 scale"
    )
    anomaly_min_sources: int = Field(
        default=3, description="Minimum independent sources for high-confidence cross-signal"
    )

    # Post-ingestion analysis (V2)
    analysis_min_mentions: int = Field(
        default=50, description="Min mentions to trigger post-ingestion analysis"
    )
    analysis_max_mentions: int = Field(
        default=200, description="Max mentions sampled for analysis"
    )
    analysis_max_refinements_per_day: int = Field(
        default=3, description="Max auto-refinements per monitor per 24h"
    )
