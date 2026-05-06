"""LLM provider wrapper. v1: OpenAI gpt-4.1.

Provider-agnostic interface so swapping to Anthropic / Gemini is one file edit.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

DEFAULT_WRITER_MODEL = os.environ.get("X_ENGINE_WRITER_MODEL", "gpt-4.1")
DEFAULT_CRITIC_MODEL = os.environ.get("X_ENGINE_CRITIC_MODEL", "gpt-4.1")
DEFAULT_TOPIC_MODEL = os.environ.get("X_ENGINE_TOPIC_MODEL", "gpt-4.1")


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def cost_usd(self) -> float:
        # gpt-4.1 pricing as of May 2026: $3/M in, $12/M out
        # (override for other models if we add them)
        in_rate = {"gpt-4.1": 3.0, "gpt-4.1-mini": 0.4, "gpt-4o": 2.5}.get(self.model, 3.0)
        out_rate = {"gpt-4.1": 12.0, "gpt-4.1-mini": 1.6, "gpt-4o": 10.0}.get(self.model, 12.0)
        return (self.input_tokens * in_rate + self.output_tokens * out_rate) / 1_000_000


class LLM:
    """Thin wrapper around OpenAI Responses API for sync calls returning JSON."""

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        self.client = OpenAI(api_key=key)

    def call_json(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_output_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Call LLM expecting a JSON response. Returns (parsed_dict, raw_response).

        Raises ValueError if the model returns invalid JSON.
        """
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=max_output_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or "{}"
        usage = resp.usage
        llm_resp = LLMResponse(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=model,
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw: {text[:500]}") from e
        return parsed, llm_resp
