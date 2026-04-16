"""OpenAI LLM judge for evaluation criteria (multi-model support)."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

from openai import AsyncOpenAI

from ...common.cost_recorder import cost_recorder
from ..exceptions import JudgeError
from ..models import ChecklistScore, DimensionResult, GradientScore, ScoringType
from . import escape_untrusted_tags, parse_judge_response

logger = logging.getLogger(__name__)

# Transient error codes worth retrying
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503}

# OpenAI pricing per million tokens (GPT 5.4 High — approximate)
_OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5.4": {"input": 5.00, "output": 15.00},
}


class OpenAIJudge:
    """LLM judge using OpenAI for structured evaluation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5.4",
        temperature: float = 0.2,
        timeout: int = 30,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        reasoning_effort: str | None = None,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        # reasoning_effort is "low" | "medium" | "high" — controls GPT-5 thinking depth.
        # When None, the parameter is omitted from the request (uses API default).
        self._reasoning_effort = reasoning_effort

    async def judge_dimension(
        self,
        criterion_id: str,
        rubric_prompt: str,
        output_text: str,
        source_text: str,
        *,
        scoring_type: str,
    ) -> DimensionResult:
        """Judge a single evaluation dimension via OpenAI."""
        is_gradient = scoring_type == ScoringType.GRADIENT.value

        schema_model = GradientScore if is_gradient else ChecklistScore
        json_schema = schema_model.model_json_schema()

        prompt = (
            f"{rubric_prompt}\n\n"
            f"## Source Data\n<untrusted_input>\n{escape_untrusted_tags(source_text)}\n</untrusted_input>\n\n"
            f"## Content to Evaluate\n<untrusted_input>\n{escape_untrusted_tags(output_text)}\n</untrusted_input>"
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                request_kwargs: dict[str, Any] = {
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self._temperature,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "evaluation",
                            "schema": json_schema,
                            "strict": True,
                        },
                    },
                }
                if self._reasoning_effort is not None:
                    request_kwargs["reasoning_effort"] = self._reasoning_effort

                response = await asyncio.wait_for(
                    self._client.chat.completions.create(**request_kwargs),
                    timeout=self._timeout,
                )

                # Cost tracking
                usage = response.usage
                if usage:
                    pricing = _OPENAI_PRICING.get(self._model, {"input": 5.0, "output": 15.0})
                    cost = (
                        (usage.prompt_tokens / 1_000_000 * pricing["input"])
                        + (usage.completion_tokens / 1_000_000 * pricing["output"])
                    )
                    await cost_recorder.record(
                        "openai", "evaluate_dimension",
                        tokens_in=usage.prompt_tokens,
                        tokens_out=usage.completion_tokens,
                        cost_usd=cost,
                        model=self._model,
                    )

                # Check finish reason
                choice = response.choices[0]
                if choice.finish_reason not in ("stop", "length"):
                    raise JudgeError(
                        "openai", criterion_id,
                        f"Bad finish_reason: {choice.finish_reason}",
                    )

                content = choice.message.content
                if not content:
                    raise JudgeError("openai", criterion_id, "Empty response")

                return parse_judge_response(
                    "openai", criterion_id, content,
                    output_text, is_gradient, self._model,
                )

            except JudgeError:
                raise
            except asyncio.TimeoutError:
                last_error = JudgeError(
                    "openai", criterion_id, f"Timeout after {self._timeout}s"
                )
            except Exception as e:
                status_code = getattr(e, "status_code", None)
                if isinstance(status_code, int) and status_code not in _RETRYABLE_STATUS_CODES:
                    raise JudgeError(
                        "openai", criterion_id,
                        f"Non-retryable error ({status_code}): {e}",
                    ) from e
                last_error = e

            if attempt < self._max_retries - 1:
                delay = self._retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.warning(
            "OpenAIJudge: all %d retries exhausted for %s: %s",
            self._max_retries, criterion_id, last_error,
        )
        return DimensionResult(
            criterion_id=criterion_id,
            scoring_type=ScoringType.GRADIENT if is_gradient else ScoringType.CHECKLIST,
            raw_score=0,
            normalized_score=0.0,
            reasoning=f"Judge failed after {self._max_retries} retries: {last_error}",
            evidence=[],
            model=self._model,
        )

    async def close(self) -> None:
        """Clean up HTTP client."""
        await self._client.close()
