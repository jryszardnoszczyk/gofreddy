"""Evaluation data models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ─── Enums ─────────────────────────────────────────────────────────────────


class ScoringType(str, Enum):
    """Type of scoring for a criterion."""

    GRADIENT = "gradient"
    CHECKLIST = "checklist"


# ─── Judge Response Models (structured output from LLM) ───────────────────


class GradientScore(BaseModel):
    """LLM judge response for gradient-scored criteria (1-5 scale)."""

    reasoning: str
    score: int  # 1-5
    evidence: list[str]  # Direct quotes from output


class ChecklistSubQuestion(BaseModel):
    """Single sub-question result in a checklist criterion."""

    question: str
    passed: bool
    evidence: str


class ChecklistScore(BaseModel):
    """LLM judge response for checklist-scored criteria (4 sub-questions)."""

    reasoning: str
    sub_questions: list[ChecklistSubQuestion]  # Exactly 4


# ─── Dimension Result (internal, per-criterion) ──────────────────────────


@dataclass(frozen=True, slots=True)
class DimensionResult:
    """Result for a single evaluation dimension (criterion)."""

    criterion_id: str  # e.g. "GEO-1", "CI-3"
    scoring_type: ScoringType
    raw_score: float  # 1-5 for gradient, 0-4 for checklist (count of passed)
    normalized_score: float  # 0.0-1.0 (median of samples when multi-replicate)
    reasoning: str
    evidence: list[str]
    model: str  # Which model produced this score (or "ensemble:median" for multi-model)
    sub_questions: list[dict[str, Any]] | None = None  # For checklist type
    # Raw per-call samples for the multi-model ensemble. None for single-call mode.
    # Each entry: {"model": str, "normalized_score": float, "reasoning": str, "error": str | None}.
    # Meta-agent inspects this via filesystem search to see variance patterns and per-model bias.
    samples: list[dict[str, Any]] | None = None


# ─── Domain Result (aggregate of 8 dimensions) ───────────────────────────


@dataclass(frozen=True, slots=True)
class DomainResult:
    """Aggregate result for a single domain (8 criteria)."""

    domain: str
    domain_score: float  # Geometric mean of 8 normalized scores
    structural_passed: bool
    length_factor: float  # Length normalization multiplier
    dimensions: list[DimensionResult]  # 8 dimension results
    content_hash: str
    rubric_version: str


# ─── Evaluation Record (persisted to DB) ──────────────────────────────────


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    """Full evaluation record persisted to PostgreSQL."""

    id: UUID
    domain: str
    domain_score: float
    grounding_score: float | None
    structural_passed: bool | None
    length_factor: float | None
    dimension_scores: dict[str, Any]  # JSONB: {criterion_id: {score, reasoning, evidence, ...}}
    rubric_version: str
    content_hash: str
    campaign_id: str | None = None
    variant_id: str | None = None
    user_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_domain_result(
        cls,
        result: DomainResult,
        *,
        campaign_id: str | None = None,
        variant_id: str | None = None,
        user_id: UUID | None = None,
        dqs_score: float | None = None,
    ) -> "EvaluationRecord":
        """Create record from domain result for persistence."""
        dimension_data: dict[str, Any] = {}
        for dim in result.dimensions:
            dimension_data[dim.criterion_id] = {
                "scoring_type": dim.scoring_type.value,
                "raw_score": dim.raw_score,
                "normalized_score": dim.normalized_score,
                "reasoning": dim.reasoning,
                "evidence": dim.evidence,
                "model": dim.model,
            }
            if dim.sub_questions:
                dimension_data[dim.criterion_id]["sub_questions"] = dim.sub_questions
            # Persist raw per-sample data for the multi-model ensemble so the
            # meta-agent can inspect variance patterns via filesystem search.
            if dim.samples:
                dimension_data[dim.criterion_id]["samples"] = dim.samples

        # DQS side effect: monitoring structural gate produces dqs_score
        if dqs_score is not None:
            dimension_data["_dqs_score"] = dqs_score

        return cls(
            id=uuid4(),
            domain=result.domain,
            domain_score=result.domain_score,
            grounding_score=None,
            structural_passed=result.structural_passed,
            length_factor=result.length_factor,
            dimension_scores=dimension_data,
            rubric_version=result.rubric_version,
            content_hash=result.content_hash,
            campaign_id=campaign_id,
            variant_id=variant_id,
            user_id=user_id,
        )


# ─── API Request/Response Models ─────────────────────────────────────────


class EvaluateRequest(BaseModel):
    """Request body for POST /v1/evaluation/evaluate."""

    domain: Literal["geo", "competitive", "monitoring", "storyboard"]
    outputs: dict[str, str] = Field(max_length=50)  # Max 50 files
    source_data: dict[str, str] = Field(default_factory=dict, max_length=50)
    campaign_id: str | None = Field(default=None, max_length=200)
    variant_id: str | None = Field(default=None, max_length=200)


class SessionCritiqueCriterionRequest(BaseModel):
    """One session-time critique criterion for trusted judge execution."""

    criterion_id: str = Field(min_length=1, max_length=200)
    rubric_prompt: str = Field(min_length=1, max_length=40_000)
    output_text: str = Field(min_length=1, max_length=80_000)
    source_text: str = Field(default="", max_length=80_000)
    scoring_type: Literal["gradient", "checklist"] = "gradient"


class SessionCritiqueRequest(BaseModel):
    """Request body for POST /v1/evaluation/critique."""

    criteria: list[SessionCritiqueCriterionRequest] = Field(min_length=1, max_length=32)


class EvaluateResponse(BaseModel):
    """Response for POST /v1/evaluation/evaluate (anti-gaming: no dimension names)."""

    domain_score: float
    dimension_scores: list[float]  # 8 normalized floats, numbered by index
    grounding_passed: bool
    structural_passed: bool
    dqs_score: float | None = None  # Monitoring only: Digest Quality Score from structural gate
    evaluation_id: str


class SessionCritiqueCriterionResponse(BaseModel):
    """One trusted judge result returned to the evolvable session critique layer."""

    criterion_id: str
    scoring_type: ScoringType
    raw_score: float
    normalized_score: float
    reasoning: str
    evidence: list[str]
    model: str
    sub_questions: list[dict[str, Any]] | None = None


class SessionCritiqueResponse(BaseModel):
    """Response for POST /v1/evaluation/critique."""

    results: list[SessionCritiqueCriterionResponse]


class EvaluationDetailResponse(BaseModel):
    """Full evaluation details for human review (GET /{id})."""

    id: str
    domain: str
    domain_score: float
    grounding_score: float | None
    structural_passed: bool | None
    length_factor: float | None
    dimension_scores: dict[str, Any]  # Full details with reasoning + evidence
    rubric_version: str
    campaign_id: str | None
    variant_id: str | None
    created_at: str


class EvaluationSummaryResponse(BaseModel):
    """Summary for campaign listing (GET /campaign/{id})."""

    evaluation_id: str
    domain: str
    domain_score: float
    variant_id: str | None
    created_at: str
