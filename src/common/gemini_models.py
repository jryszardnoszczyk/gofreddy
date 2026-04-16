"""Gemini model constants and pricing — single source of truth."""

from typing import Literal

GEMINI_FLASH_LITE = "gemini-3.1-flash-lite-preview"
GEMINI_FLASH = "gemini-3-flash-preview"
GEMINI_FLASH_IMAGE = "gemini-3.1-flash-image-preview"
GEMINI_PRO = "gemini-3.1-pro-preview"

GeminiModelLiteral = Literal[
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]

# Per-million-token pricing (March 2026, see https://ai.google.dev/gemini-api/docs/pricing)
# cached_input: 90% discount on text_input rate
GEMINI_PRICING: dict[str, dict[str, float]] = {
    GEMINI_FLASH_LITE: {"text_input": 0.25, "cached_input": 0.025, "audio_input": 0.50, "output": 1.50},
    GEMINI_FLASH: {"text_input": 0.50, "cached_input": 0.05, "audio_input": 1.00, "output": 3.00},
    GEMINI_PRO: {"text_input": 2.00, "cached_input": 0.20, "audio_input": 2.00, "output": 12.00},
}
