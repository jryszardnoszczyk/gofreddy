"""Evaluation API endpoints — server-side evolution evaluators."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..rate_limit import limiter
from ...evaluation.models import (
    EvaluateRequest,
    EvaluateResponse,
    EvaluationDetailResponse,
    EvaluationSummaryResponse,
    SessionCritiqueCriterionResponse,
    SessionCritiqueRequest,
    SessionCritiqueResponse,
)
from ...evaluation.service import EvaluationService
from ..dependencies import get_current_user_id

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def get_evaluation_service(request: Request) -> EvaluationService:
    """Retrieve EvaluationService from app state."""
    service = getattr(request.app.state, "evaluation_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Evaluation service not configured"},
        )
    return service


# IMPORTANT: /evaluate, /critique, and /campaign/{campaign_id} BEFORE /{evaluation_id}
# to avoid UUID capture (route ordering matters).


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Run domain evaluation (evolution pipeline)",
    responses={
        400: {"description": "Invalid domain or empty outputs"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Evaluation failed"},
    },
)
@limiter.limit("30/minute")
async def evaluate(
    request: Request,
    body: EvaluateRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluateResponse:
    """Run full 4-layer evaluation for a domain.

    Returns domain_score + numbered dimension scores (no names — anti-gaming).
    """
    if not body.outputs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "empty_outputs", "message": "outputs dict must not be empty"},
        )

    try:
        record = await service.evaluate_domain(body, user_id=user_id)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Evaluation failed for domain=%s", body.domain)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "evaluation_error", "message": "Evaluation failed. Check server logs for details."},
        )

    # Extract numbered dimension scores (no names — anti-gaming).
    dimension_scores: list[float] = []
    dim_data = record.dimension_scores
    if isinstance(dim_data, dict):
        for key in sorted(dim_data.keys()):
            if key == "failure_reason" or key == "_dqs_score":
                continue
            entry = dim_data[key]
            if isinstance(entry, dict) and "normalized_score" in entry:
                dimension_scores.append(entry["normalized_score"])
    # Pad to 8 if needed (hard failures with no judge results, e.g. structural_failure)
    while len(dimension_scores) < 8:
        dimension_scores.append(0.0)

    # Extract DQS score if present (monitoring domain only)
    dqs_score = None
    if isinstance(dim_data, dict):
        dqs_score = dim_data.get("_dqs_score")

    return EvaluateResponse(
        domain_score=record.domain_score,
        dimension_scores=dimension_scores[:8],
        grounding_passed=True,  # hardcoded for backward compatibility; grounding gate removed
        structural_passed=record.structural_passed or False,
        evaluation_id=str(record.id),
        dqs_score=dqs_score,
    )


@router.post(
    "/critique",
    response_model=SessionCritiqueResponse,
    summary="Run trusted judge execution for evolvable session critique",
    responses={
        400: {"description": "Invalid critique payload"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Critique failed"},
    },
)
@limiter.limit("30/minute")
async def critique(
    request: Request,
    body: SessionCritiqueRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: EvaluationService = Depends(get_evaluation_service),
) -> SessionCritiqueResponse:
    """Run session-time critique criteria through the trusted judge stack."""
    if not body.criteria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "empty_criteria", "message": "criteria list must not be empty"},
        )

    try:
        results = await service.critique_session(body)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Session critique failed for %d criteria", len(body.criteria))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "critique_error", "message": "Session critique failed. Check server logs for details."},
        )

    return SessionCritiqueResponse(
        results=[
            SessionCritiqueCriterionResponse(
                criterion_id=result.criterion_id,
                scoring_type=result.scoring_type,
                raw_score=result.raw_score,
                normalized_score=result.normalized_score,
                reasoning=result.reasoning,
                evidence=result.evidence,
                model=result.model,
                sub_questions=result.sub_questions,
            )
            for result in results
        ]
    )


@router.get(
    "/campaign/{campaign_id}",
    response_model=list[EvaluationSummaryResponse],
    summary="List evaluations in a campaign",
    responses={
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("60/minute")
async def get_campaign_evaluations(
    request: Request,
    campaign_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: EvaluationService = Depends(get_evaluation_service),
) -> list[EvaluationSummaryResponse]:
    """Get all evaluations for an evolution campaign."""
    records = await service.get_campaign_evaluations(campaign_id, user_id=user_id)
    return [
        EvaluationSummaryResponse(
            evaluation_id=str(r.id),
            domain=r.domain,
            domain_score=r.domain_score,
            variant_id=r.variant_id,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationDetailResponse,
    summary="Get full evaluation details (human review)",
    responses={
        404: {"description": "Evaluation not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("60/minute")
async def get_evaluation(
    request: Request,
    evaluation_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationDetailResponse:
    """Get full evaluation details including all 32 dimension scores, reasoning, evidence."""
    record = await service.get_evaluation(evaluation_id, user_id=user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Evaluation not found"},
        )

    return EvaluationDetailResponse(
        id=str(record.id),
        domain=record.domain,
        domain_score=record.domain_score,
        grounding_score=record.grounding_score,
        structural_passed=record.structural_passed,
        length_factor=record.length_factor,
        dimension_scores=record.dimension_scores,
        rubric_version=record.rubric_version,
        campaign_id=record.campaign_id,
        variant_id=record.variant_id,
        created_at=record.created_at.isoformat(),
    )
