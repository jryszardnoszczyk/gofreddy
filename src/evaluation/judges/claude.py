"""Claude LLM judge for evaluation criteria.

Replaces the previous GeminiJudge for text-only rubric judging. Uses the
shared `call_sonnet_json` Claude-CLI subprocess helper (same transport as
the paraphrase + calibration sub-judges) so we have a single Claude entry
point for the evaluation module.

The public interface mirrors `OpenAIJudge` exactly — same `judge_dimension`
signature, same `close()`, same `DimensionResult` return shape — so DI in
`src/api/main.py` can swap providers via the `provider` key in
`EvaluationSettings.judge_models` with no other changes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random

from ..exceptions import JudgeError
from ..models import ChecklistScore, DimensionResult, GradientScore, ScoringType
from . import escape_untrusted_tags, parse_judge_response
from .sonnet_agent import SonnetAgentError, call_sonnet_json

logger = logging.getLogger(__name__)


class ClaudeJudge:
    """LLM judge using Claude (via the `claude -p` CLI) for structured evaluation.

    Shape mirrors OpenAIJudge:
      - `__init__(api_key, model, ...)` — `api_key` is accepted for interface
        symmetry but ignored: the `claude` CLI authenticates via its own
        config (`~/.claude/...` or `ANTHROPIC_API_KEY` env). Pass an empty
        string when constructing from settings without an explicit key.
      - `judge_dimension(...)` — same kwargs, same DimensionResult return.
      - `close()` — no-op (the CLI subprocess is one-shot per call).
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        timeout: int = 30,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> None:
        # `api_key` retained for interface parity with OpenAIJudge / former
        # GeminiJudge. The Claude CLI handles auth itself; logging would leak
        # the key, so we deliberately don't store it.
        del api_key
        self._model = model
        self._temperature = temperature
        self._timeout = float(timeout)
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
        """Judge a single evaluation dimension via Claude.

        Args:
            criterion_id: e.g. "GEO-1", "CI-3"
            rubric_prompt: The full rubric prompt for this criterion.
            output_text: The content being evaluated.
            source_text: Source/reference data for context.
            scoring_type: "gradient" or "checklist".

        Returns:
            DimensionResult with score, reasoning, evidence.

        Raises:
            JudgeError: After all retries exhausted (or non-retryable parse error).
        """
        is_gradient = scoring_type == ScoringType.GRADIENT.value
        schema_model = GradientScore if is_gradient else ChecklistScore
        json_schema = json.dumps(schema_model.model_json_schema(), indent=2)

        prompt = (
            f"{rubric_prompt}\n\n"
            f"## Source Data\n<untrusted_input>\n{escape_untrusted_tags(source_text)}\n</untrusted_input>\n\n"
            f"## Content to Evaluate\n<untrusted_input>\n{escape_untrusted_tags(output_text)}\n</untrusted_input>\n\n"
            f"Return a SINGLE JSON object (no prose, no markdown fences) matching this schema:\n"
            f"```\n{json_schema}\n```"
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                data = await call_sonnet_json(
                    prompt,
                    operation=f"evaluate_dimension::{criterion_id}",
                    model=self._model,
                    timeout=self._timeout,
                )
                # Re-serialize so the shared parser (which expects a string
                # of JSON) can validate the schema and run the paraphrase +
                # calibration sub-judges over the result.
                return await parse_judge_response(
                    "claude", criterion_id, json.dumps(data),
                    output_text, is_gradient, self._model,
                    rubric_prompt=rubric_prompt,
                )
            except JudgeError:
                # Schema validation / parse errors are not transient; bubble.
                raise
            except SonnetAgentError as e:
                last_error = e  # All CLI failures are treated as transient.
            except Exception as e:  # noqa: BLE001 — network / unknown -> retry
                last_error = e

            if attempt < self._max_retries - 1:
                delay = self._retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

        logger.warning(
            "ClaudeJudge: all %d retries exhausted for %s: %s",
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
        """No-op — the CLI subprocess has no persistent client state."""
        return None
