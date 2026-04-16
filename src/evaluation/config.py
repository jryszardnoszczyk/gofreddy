"""Evaluation service configuration."""

from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..common.gemini_models import GEMINI_PRO


class EvaluationSettings(BaseSettings):
    """Server-side evaluation configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Judge API keys
    gemini_api_key: SecretStr = Field(..., description="Gemini API key")
    openai_api_key: SecretStr = Field(default=SecretStr(""), description="OpenAI API key (optional, multi-model only)")

    # Multi-model ensemble config.
    #
    # Each entry is a dict with at minimum {provider, model}. Optional keys:
    #   - reasoning_effort: "low" | "medium" | "high" (OpenAI GPT-5 thinking control)
    #   - temperature: per-model override of judge_temperature
    #
    # Default ensemble: 2× Gemini Pro + 2× GPT-5.4 high-thinking, median of 4 per
    # criterion. This catches both sampling noise (intra-model replication) and
    # systematic rubric-interpretation bias (cross-model coverage). Selection
    # signal stability matters more than cost; see Hyperagents §D and the
    # fixpack plan for rationale. If openai_api_key is unset at runtime, the
    # OpenAI entries are skipped with a warning and Gemini-only is used.
    judge_models: list[dict[str, Any]] = Field(
        default_factory=lambda: [
            {"provider": "gemini", "model": GEMINI_PRO},
            {"provider": "openai", "model": "gpt-5.4", "reasoning_effort": "high"},
        ],
        description="Multi-model ensemble composition — list of per-judge dicts with provider, model, and optional parameters",
    )
    judge_replicates_per_model: int = Field(
        default=2,
        description="Number of times each model in judge_models is called per criterion. Total calls per criterion = len(judge_models) × judge_replicates_per_model. Median of all samples becomes the canonical score.",
    )
    judge_temperature: float = Field(default=0.2, description="Judge temperature (Rating Roulette EMNLP 2025)")
    judge_timeout: int = Field(default=60, description="Per-judge call timeout in seconds")

    # Retry config
    judge_max_retries: int = Field(default=3, description="Max retries per judge call")
    judge_retry_base_delay: float = Field(default=1.0, description="Base delay for exponential backoff")
