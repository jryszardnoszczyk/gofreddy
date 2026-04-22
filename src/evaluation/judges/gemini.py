"""Gemini LLM judge for evaluation criteria."""

from __future__ import annotations

import asyncio
import functools
import logging
import random

from google import genai
from google.genai import types as genai_types

from ...common.cost_recorder import cost_recorder, extract_gemini_usage
from ..exceptions import JudgeError
from ..models import ChecklistScore, DimensionResult, GradientScore, ScoringType
from . import escape_untrusted_tags, parse_judge_response

logger = logging.getLogger(__name__)

# Gemini rejects these Pydantic JSON-schema keys
_GEMINI_STRIP_KEYS = frozenset({
    "additionalProperties", "title", "default", "maxLength",
    "minLength", "maxItems", "minItems", "$defs",
})

# Transient error codes worth retrying
_RETRYABLE_STATUS_CODES = {429, 500, 503}


def _resolve_refs(schema: dict, defs: dict) -> dict:
    """Inline $ref references using $defs before Gemini cleaning."""
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_path = schema["$ref"]  # e.g. "#/$defs/ChecklistSubQuestion"
            ref_name = ref_path.rsplit("/", 1)[-1]
            resolved = defs.get(ref_name, schema)
            return _resolve_refs(resolved, defs)
        return {k: _resolve_refs(v, defs) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_resolve_refs(item, defs) for item in schema]
    return schema


def _clean_schema_for_gemini(schema: dict) -> dict:
    """Strip Pydantic JSON-schema keys that the Gemini API rejects."""
    if not isinstance(schema, dict):
        if isinstance(schema, list):
            return [_clean_schema_for_gemini(item) for item in schema]
        return schema

    # First resolve $ref references so we can safely strip $defs (top-level only)
    defs = schema.get("$defs", {})
    if defs:
        schema = _resolve_refs(schema, defs)

    if isinstance(schema, dict):
        if "anyOf" in schema and len(schema["anyOf"]) == 2:
            types = schema["anyOf"]
            null_type = next((t for t in types if t.get("type") == "null"), None)
            real_type = next((t for t in types if t.get("type") != "null"), None)
            if null_type and real_type:
                result = _clean_schema_for_gemini(real_type)
                result["nullable"] = True
                return result
        return {
            k: _clean_schema_for_gemini(v)
            for k, v in schema.items()
            if k not in _GEMINI_STRIP_KEYS
        }
    if isinstance(schema, list):
        return [_clean_schema_for_gemini(item) for item in schema]
    return schema


@functools.lru_cache(maxsize=8)
def _get_gradient_schema() -> dict:
    return _clean_schema_for_gemini(GradientScore.model_json_schema())


@functools.lru_cache(maxsize=8)
def _get_checklist_schema() -> dict:
    return _clean_schema_for_gemini(ChecklistScore.model_json_schema())


class GeminiJudge:
    """LLM judge using Gemini for structured evaluation."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        timeout: int = 30,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=genai_types.HttpOptions(api_version="v1alpha"),
        )
        self._model = model
        self._temperature = temperature
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay

    async def judge_dimension(
        self,
        criterion_id: str,
        rubric_prompt: str,
        output_text: str,
        source_text: str,
        *,
        scoring_type: str,
    ) -> DimensionResult:
        """Judge a single evaluation dimension.

        Args:
            criterion_id: e.g. "GEO-1", "CI-3"
            rubric_prompt: The full rubric prompt for this criterion.
            output_text: The content being evaluated.
            source_text: Source/reference data for context.
            scoring_type: "gradient" or "checklist".

        Returns:
            DimensionResult with score, reasoning, evidence.

        Raises:
            JudgeError: After all retries exhausted.
        """
        is_gradient = scoring_type == ScoringType.GRADIENT.value

        schema = _get_gradient_schema() if is_gradient else _get_checklist_schema()

        prompt = (
            f"{rubric_prompt}\n\n"
            f"## Source Data\n<untrusted_input>\n{escape_untrusted_tags(source_text)}\n</untrusted_input>\n\n"
            f"## Content to Evaluate\n<untrusted_input>\n{escape_untrusted_tags(output_text)}\n</untrusted_input>"
        )

        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=self._temperature,
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    ),
                    timeout=self._timeout,
                )

                # Cost tracking
                t_in, t_out, cost = extract_gemini_usage(response, self._model)
                await cost_recorder.record(
                    "gemini", "evaluate_dimension",
                    tokens_in=t_in, tokens_out=t_out,
                    cost_usd=cost, model=self._model,
                )

                # Guard empty candidates
                if not response.candidates:
                    raise JudgeError(
                        "gemini", criterion_id, "Empty candidates in response"
                    )

                # Check finish_reason
                finish = response.candidates[0].finish_reason
                if finish not in (None, genai_types.FinishReason.STOP):
                    raise JudgeError(
                        "gemini", criterion_id, f"Bad finish_reason: {finish}"
                    )

                if not response.text:
                    raise JudgeError(
                        "gemini", criterion_id, "Empty response text"
                    )

                return await parse_judge_response(
                    "gemini", criterion_id, response.text,
                    output_text, is_gradient, self._model,
                    rubric_prompt=rubric_prompt,
                )

            except JudgeError:
                raise  # Non-retryable parse errors
            except asyncio.TimeoutError:
                last_error = JudgeError(
                    "gemini", criterion_id, f"Timeout after {self._timeout}s"
                )
            except Exception as e:
                # Check if retryable
                status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
                if isinstance(status_code, int) and status_code not in _RETRYABLE_STATUS_CODES:
                    raise JudgeError(
                        "gemini", criterion_id, f"Non-retryable error ({status_code}): {e}"
                    ) from e
                last_error = e

            # Exponential backoff
            if attempt < self._max_retries - 1:
                delay = self._retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

        # All retries exhausted — dimension scores 0.0
        logger.warning(
            "GeminiJudge: all %d retries exhausted for %s: %s",
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
        """Clean up resources."""
        pass  # genai.Client doesn't require explicit cleanup
