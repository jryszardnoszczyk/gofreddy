"""LLM judge implementations for evaluation criteria."""

from __future__ import annotations

import json
import logging
import math
from typing import Any, Protocol

from ..exceptions import JudgeError
from ..models import (
    ChecklistScore,
    DimensionResult,
    GradientScore,
    ScoringType,
)

logger = logging.getLogger(__name__)


class JudgeProtocol(Protocol):
    """Protocol for LLM judges."""

    async def judge_dimension(
        self,
        criterion_id: str,
        rubric_prompt: str,
        output_text: str,
        source_text: str,
        *,
        scoring_type: str,
    ) -> DimensionResult: ...

    async def close(self) -> None: ...


def normalize_gradient(score: int) -> float:
    """Normalize gradient score (1-5) to 0.0-1.0."""
    return (score - 1) / 4


def normalize_checklist(passed_count: int, total: int = 4) -> float:
    """Normalize checklist score (0-4 passed) to 0.0-1.0."""
    return passed_count / total


def geometric_mean(scores: list[float], *, floor: float = 0.01) -> float:
    """Compute geometric mean of scores with floor to prevent zero-domination.

    A single zero no longer kills the entire score. Instead, zeros are
    floored to 0.01, which still heavily penalizes weak dimensions
    (pulling score to ~0.1-0.3 range) without making all variants score 0.
    """
    if not scores:
        return 0.0
    floored = [max(s, floor) for s in scores]
    product = math.prod(floored)
    if product <= 0:
        return 0.0
    return product ** (1 / len(floored))


# ─── Shared parsing + evidence verification ──────────────────────────────


def escape_untrusted_tags(text: str) -> str:
    """Escape </untrusted_input> in content to prevent tag boundary escape."""
    return text.replace("</untrusted_input>", "&lt;/untrusted_input&gt;")


def fuzzy_match(quote: str, text: str, threshold: float = 0.8) -> bool:
    """Token overlap matching for evidence verification."""
    quote_tokens = set(quote.lower().split())
    text_tokens = set(text.lower().split())
    if not quote_tokens:
        return False
    overlap = len(quote_tokens & text_tokens) / len(quote_tokens)
    return overlap >= threshold


def parse_judge_response(
    judge_name: str,
    criterion_id: str,
    response_text: str,
    output_text: str,
    is_gradient: bool,
    model: str,
) -> DimensionResult:
    """Parse and validate LLM judge response with evidence gates.

    Shared between GeminiJudge and OpenAIJudge.
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise JudgeError(judge_name, criterion_id, f"Invalid JSON: {e}") from e

    if is_gradient:
        return _parse_gradient(criterion_id, data, output_text, model)
    return _parse_checklist(criterion_id, data, output_text, model)


def _parse_gradient(
    criterion_id: str,
    data: dict[str, Any],
    output_text: str,
    model: str,
) -> DimensionResult:
    """Parse gradient (1-5) response with evidence gate."""
    parsed = GradientScore.model_validate(data)
    score = max(1, min(5, parsed.score))

    verified_evidence = [
        e for e in parsed.evidence if fuzzy_match(e, output_text)
    ]

    # Evidence gate: high score with insufficient evidence → cap at 3
    if len(verified_evidence) < 2 and score > 3:
        logger.info(
            "Evidence gate: %s score %d capped to 3 (only %d verified evidence)",
            criterion_id, score, len(verified_evidence),
        )
        score = 3

    normalized = (score - 1) / 4

    return DimensionResult(
        criterion_id=criterion_id,
        scoring_type=ScoringType.GRADIENT,
        raw_score=score,
        normalized_score=normalized,
        reasoning=parsed.reasoning,
        evidence=verified_evidence,
        model=model,
    )


def _parse_checklist(
    criterion_id: str,
    data: dict[str, Any],
    output_text: str,
    model: str,
) -> DimensionResult:
    """Parse checklist (4 sub-questions) response with evidence gate."""
    parsed = ChecklistScore.model_validate(data)
    sub_results: list[dict[str, Any]] = []
    passed_count = 0

    for sq in parsed.sub_questions[:4]:
        verified = fuzzy_match(sq.evidence, output_text)
        actually_passed = sq.passed and verified

        if sq.passed and not verified:
            logger.info(
                "Evidence gate: %s sub-question flipped to fail (fabricated evidence)",
                criterion_id,
            )

        if actually_passed:
            passed_count += 1

        sub_results.append({
            "question": sq.question,
            "passed": actually_passed,
            "evidence": sq.evidence,
            "evidence_verified": verified,
        })

    normalized = passed_count / 4

    return DimensionResult(
        criterion_id=criterion_id,
        scoring_type=ScoringType.CHECKLIST,
        raw_score=passed_count,
        normalized_score=normalized,
        reasoning=parsed.reasoning,
        evidence=[sq.evidence for sq in parsed.sub_questions if sq.evidence],
        model=model,
        sub_questions=sub_results,
    )
