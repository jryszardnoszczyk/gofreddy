"""Task-based model routing — route to appropriate Gemini model by task complexity."""

from __future__ import annotations

from .gemini_models import GEMINI_FLASH, GEMINI_FLASH_LITE

# Map task names to the cheapest model that delivers acceptable quality.
# Simple extraction/classification → Flash Lite (10x cheaper)
# Core analysis / complex reasoning → Flash
TASK_MODEL_MAP: dict[str, str] = {
    # Simple extraction/classification — use cheapest model
    "query_parsing": GEMINI_FLASH_LITE,
    "auto_title": GEMINI_FLASH_LITE,
    "intent_classification": GEMINI_FLASH_LITE,
    "sentiment_classification": GEMINI_FLASH_LITE,
    "comment_classification": GEMINI_FLASH_LITE,
    # Core analysis — use standard model
    "video_analysis": GEMINI_FLASH,
    "brand_detection": GEMINI_FLASH,
    "creative_patterns": GEMINI_FLASH,
    # Complex reasoning — use best available non-Pro model
    "demographics_inference": GEMINI_FLASH,
    "agent_reasoning": GEMINI_FLASH,
    "fraud_bot_detection": GEMINI_FLASH,
    # GEO tasks — standard model
    "gap_analysis": GEMINI_FLASH,
    "content_rewriting": GEMINI_FLASH,
}


def get_model_for_task(task: str) -> str:
    """Route to the appropriate model for a given task.

    Returns the mapped model or GEMINI_FLASH as default.
    Future: query provider_cost_log for accuracy per model per task
    and auto-promote if cheap model quality drops below threshold.
    """
    return TASK_MODEL_MAP.get(task, GEMINI_FLASH)
