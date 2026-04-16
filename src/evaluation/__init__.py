"""Server-side evaluation module for evolution pipeline."""

from .config import EvaluationSettings
from .exceptions import EvaluationError, JudgeError, StructuralFailure
from .models import (
    ChecklistScore,
    ChecklistSubQuestion,
    DimensionResult,
    DomainResult,
    EvaluateRequest,
    EvaluateResponse,
    EvaluationDetailResponse,
    EvaluationRecord,
    EvaluationSummaryResponse,
    GradientScore,
    SessionCritiqueCriterionRequest,
    SessionCritiqueCriterionResponse,
    SessionCritiqueRequest,
    SessionCritiqueResponse,
    ScoringType,
)

__all__ = [
    # Config
    "EvaluationSettings",
    # Exceptions
    "EvaluationError",
    "JudgeError",
    "StructuralFailure",
    # Models
    "ChecklistScore",
    "ChecklistSubQuestion",
    "DimensionResult",
    "DomainResult",
    "EvaluateRequest",
    "EvaluateResponse",
    "EvaluationDetailResponse",
    "EvaluationRecord",
    "EvaluationSummaryResponse",
    "GradientScore",
    "SessionCritiqueCriterionRequest",
    "SessionCritiqueCriterionResponse",
    "SessionCritiqueRequest",
    "SessionCritiqueResponse",
    "ScoringType",
]
