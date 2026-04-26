"""GEO/SEO audit API endpoints."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.geo.exceptions import GeoAuditError

from ..dependencies import get_current_user_id
from ..rate_limit import limiter
from ..schemas import (
    GeoAuditListItem,
    GeoAuditListResponse,
    GeoAuditRequest,
    GeoAuditResponse,
    GeoDetectRequest,
    GeoDetectResponse,
    GeoOptimizeRequest,
    GeoOptimizeResponse,
    GeoScrapeRequest,
    GeoScrapeResponse,
    GeoVisibilityRequest,
    GeoVisibilityResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geo", tags=["seo"])

# F-a-3-1: GeoAuditError code → HTTP status. The pipeline raises distinct
# error codes for client-actionable failures (TIMEOUT means upstream Gemini
# stalled; CIRCUIT_OPEN means we tripped a breaker; PARSE_FAILED means the
# provider returned malformed data). Mapping each to the right HTTP code
# lets clients distinguish retry-now (5xx transient) from
# don't-bother-retrying (5xx permanent) instead of the generic 500
# audit_error that previously hid all of them.
_GEO_AUDIT_ERROR_STATUS: dict[str, int] = {
    "TIMEOUT": status.HTTP_504_GATEWAY_TIMEOUT,
    "DISABLED": status.HTTP_503_SERVICE_UNAVAILABLE,
    "CIRCUIT_OPEN": status.HTTP_503_SERVICE_UNAVAILABLE,
    "GENERATION_FAILED": status.HTTP_502_BAD_GATEWAY,
    "NO_CANDIDATES": status.HTTP_502_BAD_GATEWAY,
    "PARSE_ERROR": status.HTTP_502_BAD_GATEWAY,
    "PARSE_FAILED": status.HTTP_502_BAD_GATEWAY,
    "INTERNAL": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def _get_geo_service(request: Request):
    """Get GeoService from app state, or None."""
    return getattr(request.app.state, "geo_service", None)


def _build_audit_response(record: dict[str, Any]) -> GeoAuditResponse:
    """Build GeoAuditResponse from a repository record dict."""
    return GeoAuditResponse(
        audit_id=record["id"],
        url=record["url"],
        status=record["status"],
        overall_score=record.get("overall_score"),
        report_md=record.get("report_md"),
        findings=record.get("findings"),
        opportunities=record.get("opportunities"),
        keywords=record.get("keywords"),
        created_at=record["created_at"],
        updated_at=record.get("updated_at"),
    )


@router.post(
    "/audit",
    response_model=GeoAuditResponse,
    summary="Run a GEO audit on a URL",
    responses={
        400: {"description": "Invalid URL"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "GEO service not configured"},
    },
)
@limiter.limit("10/minute")
async def run_audit(
    request: Request,
    body: GeoAuditRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoAuditResponse:
    """Run a comprehensive GEO audit combining AI search visibility and SEO analysis."""
    from ...common.url_validation import resolve_and_validate

    geo_service = _get_geo_service(request)
    if geo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "geo_unavailable", "message": "GEO service is not configured"},
        )

    try:
        await resolve_and_validate(body.url)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_url", "message": "URL validation failed"},
        )

    try:
        result = await geo_service.run_audit(
            url=body.url,
            user_id=user_id,
            keywords=body.keywords,
        )
    except GeoAuditError as e:
        # Map structured pipeline errors to specific HTTP codes (F-a-3-1).
        # Previously these were all swallowed by the blanket except below
        # and surfaced as a generic 500 `audit_error`, leaving clients
        # unable to distinguish "Gemini timed out — retry" from "your URL
        # is unparseable — don't retry".
        logger.error("GEO audit failed code=%s: %s", e.code, e.message)
        raise HTTPException(
            status_code=_GEO_AUDIT_ERROR_STATUS.get(
                e.code, status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            detail={"code": e.code.lower(), "message": e.message},
        )
    except Exception as e:
        logger.error("GEO audit failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "audit_error", "message": "GEO audit failed"},
        )

    # Fetch the persisted record to get full response shape
    record = await geo_service.get_by_id(result.audit_id, user_id=user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "audit_error", "message": "Audit completed but record not found"},
        )

    return _build_audit_response(record)


@router.get(
    "/audits",
    response_model=GeoAuditListResponse,
    summary="List GEO audits for the current user",
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("30/minute")
async def list_audits(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
) -> GeoAuditListResponse:
    """List GEO audits for the authenticated user."""
    geo_service = _get_geo_service(request)
    if geo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "geo_unavailable", "message": "GEO service is not configured"},
        )

    records = await geo_service.list_audits(
        user_id=user_id, limit=limit, offset=offset,
    )

    return GeoAuditListResponse(
        audits=[
            GeoAuditListItem(
                id=r["id"],
                url=r["url"],
                status=r["status"],
                overall_score=r.get("overall_score"),
                keywords=r.get("keywords"),
                created_at=r["created_at"],
            )
            for r in records
        ],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit/{audit_id}",
    response_model=GeoAuditResponse,
    summary="Get GEO audit result by ID",
    responses={
        404: {"description": "Audit not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("30/minute")
async def get_audit(
    request: Request,
    audit_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoAuditResponse:
    """Retrieve a GEO audit result by ID. Returns 404 if not found or not owned."""
    geo_service = _get_geo_service(request)
    if geo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "geo_unavailable", "message": "GEO service is not configured"},
        )

    record = await geo_service.get_by_id(audit_id, user_id=user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Audit {audit_id} not found"},
        )

    return _build_audit_response(record)


@router.post(
    "/visibility",
    response_model=GeoVisibilityResponse,
    summary="Check brand visibility across AI search platforms",
    responses={
        429: {"description": "Rate limit exceeded"},
        503: {"description": "GEO service not configured"},
    },
)
@limiter.limit("10/minute")
async def check_visibility(
    request: Request,
    body: GeoVisibilityRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoVisibilityResponse:
    """Check brand mentions and citations across AI search platforms."""
    geo_service = _get_geo_service(request)
    if geo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "geo_unavailable", "message": "GEO service is not configured"},
        )

    try:
        result = await geo_service.check_visibility(
            brand=body.brand,
            keywords=body.keywords,
            platforms=body.platforms,
            country=body.country,
        )
    except Exception as e:
        logger.error("Visibility check failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "visibility_error", "message": "Visibility check failed"},
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": result["error"], "message": result.get("summary", "Service unavailable")},
        )

    return GeoVisibilityResponse(**result)


@router.post(
    "/optimize",
    response_model=GeoOptimizeResponse,
    summary="Get optimized content from a completed GEO audit",
    responses={
        400: {"description": "Audit not complete"},
        404: {"description": "Audit not found"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "GEO service not configured"},
    },
)
@limiter.limit("10/minute")
async def get_optimized_content(
    request: Request,
    body: GeoOptimizeRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoOptimizeResponse:
    """Retrieve optimized content generated from a completed GEO audit."""
    geo_service = _get_geo_service(request)
    if geo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "geo_unavailable", "message": "GEO service is not configured"},
        )

    record = await geo_service.get_by_id(body.audit_id, user_id=user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Audit {body.audit_id} not found"},
        )

    if record.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "audit_not_complete",
                "message": f"Audit is '{record.get('status')}', not 'complete'. Wait for completion or re-run.",
            },
        )

    return GeoOptimizeResponse(
        audit_id=record["id"],
        url=record["url"],
        status=record["status"],
        overall_score=record.get("overall_score"),
        optimized_content=record.get("opportunities"),
        findings_summary=record.get("findings"),
    )


@router.post(
    "/detect",
    response_model=GeoDetectResponse,
    summary="Detect GEO infrastructure + SEO technical factors",
    responses={
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def detect_url(
    request: Request,
    body: GeoDetectRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoDetectResponse:
    """Run deterministic GEO infrastructure + SEO technical checks on a URL."""
    import httpx

    from ...common.url_validation import resolve_and_validate
    from ...geo.detector import detect_factors
    from ...geo.extraction import extract_page_content
    from ...geo.fetcher import fetch_page_for_audit

    try:
        await resolve_and_validate(body.url)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_url", "message": "URL validation failed"},
        )

    fetch_result = await fetch_page_for_audit(body.url)

    page_content = extract_page_content(
        html=fetch_result.content,
        url=body.url,
        final_url=fetch_result.final_url,
        js_rendered=fetch_result.js_rendered,
        status_code=fetch_result.status_code,
        fetch_duration_ms=0,
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        findings = await detect_factors(page_content, http_client=client)

    result: dict[str, Any] = {
        "url": page_content.url,
        "final_url": page_content.final_url,
        "geo_infrastructure": {},
        "seo_technical": {},
        "seo_full": None,
    }

    geo_infra_ids = {"schema_markup", "ssr_issues", "ai_bot_access", "llms_txt"}
    for finding in findings.findings:
        entry: dict[str, Any] = {
            "detected": finding.detected,
            "details": finding.details,
        }
        if finding.count is not None:
            entry["count"] = finding.count
        if finding.evidence:
            entry["evidence"] = list(finding.evidence)

        if finding.factor_id in geo_infra_ids:
            result["geo_infrastructure"][finding.factor_id] = entry
        else:
            result["seo_technical"][finding.factor_id] = entry

    if body.full:
        seo_full: dict[str, Any] = {}
        try:
            dataforseo = getattr(request.app.state, "dataforseo_provider", None)
            if dataforseo:
                audit_result = await dataforseo.technical_audit(body.url)
                seo_full["dataforseo"] = audit_result
            else:
                seo_full["dataforseo_error"] = "provider_unavailable"
        except Exception:
            seo_full["dataforseo_error"] = "provider_unavailable"

        try:
            pagespeed = getattr(request.app.state, "pagespeed_provider", None)
            if pagespeed:
                perf_result = await pagespeed.check_performance(body.url)
                seo_full["pagespeed"] = perf_result
            else:
                import os

                from ...seo.providers.pagespeed import check_performance

                pagespeed_key = os.environ.get("PAGESPEED_API_KEY", "")
                perf_result = await check_performance(body.url, api_key=pagespeed_key)
                seo_full["pagespeed"] = perf_result
        except Exception:
            seo_full["pagespeed_error"] = "provider_unavailable"

        result["seo_full"] = seo_full

    return GeoDetectResponse(**result)


@router.post(
    "/scrape",
    response_model=GeoScrapeResponse,
    summary="Scrape page content and extract text",
    responses={
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def scrape_url(
    request: Request,
    body: GeoScrapeRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GeoScrapeResponse:
    """Fetch page content and extract structured text."""
    from ...common.url_validation import resolve_and_validate
    from ...geo.extraction import extract_page_content
    from ...geo.fetcher import fetch_page_for_audit

    try:
        await resolve_and_validate(body.url)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_url", "message": "URL validation failed"},
        )

    fetch_result = await fetch_page_for_audit(body.url)

    page_content = extract_page_content(
        html=fetch_result.content,
        url=body.url,
        final_url=fetch_result.final_url,
        js_rendered=fetch_result.js_rendered,
        status_code=fetch_result.status_code,
        fetch_duration_ms=0,
    )

    return GeoScrapeResponse(
        url=page_content.url,
        final_url=page_content.final_url,
        title=page_content.title,
        h1=page_content.h1,
        h2s=page_content.h2s,
        meta_description=page_content.meta_description,
        text=page_content.text[:100_000],
        text_truncated=len(page_content.text) >= 100_000,
        word_count=page_content.word_count,
        schema_types=page_content.schema_types,
        status_code=page_content.status_code,
    )


# =============================================================================
# SEO Domain Rank + Keywords (PR-102)
# =============================================================================

import re

_DOMAIN_REGEX = re.compile(r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")


def _validate_domain(domain: str) -> str:
    """Validate and normalize domain format."""
    domain = domain.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    if len(domain) > 253 or not _DOMAIN_REGEX.match(domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_domain", "message": "Invalid domain format"},
        )
    return domain


def _get_seo_service(request: Request):
    """Get SeoService from app state."""
    return getattr(request.app.state, "seo_service", None)


@router.get(
    "/rank/snapshots",
    summary="Get latest domain rank snapshot",
    tags=["seo"],
    responses={
        400: {"description": "Invalid domain"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "SEO service not configured"},
    },
)
@limiter.limit("30/minute")
async def get_rank_snapshot(
    request: Request,
    domain: str = Query(..., max_length=253, description="Domain to check"),
    user_id: UUID = Depends(get_current_user_id),
) -> dict:
    """Get the latest domain rank snapshot."""
    domain = _validate_domain(domain)
    seo_service = _get_seo_service(request)
    if seo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "seo_unavailable", "message": "SEO service is not configured"},
        )

    result = await seo_service.get_domain_rank_history(
        domain=domain, org_id=None, days=1,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"No rank data for {domain}"},
        )
    return result[0]


@router.get(
    "/rank/history",
    summary="Get domain rank history",
    tags=["seo"],
    responses={
        400: {"description": "Invalid domain"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "SEO service not configured"},
    },
)
@limiter.limit("30/minute")
async def get_rank_history(
    request: Request,
    domain: str = Query(..., max_length=253, description="Domain to check"),
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    user_id: UUID = Depends(get_current_user_id),
) -> dict:
    """Get domain rank history as time series."""
    domain = _validate_domain(domain)
    seo_service = _get_seo_service(request)
    if seo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "seo_unavailable", "message": "SEO service is not configured"},
        )

    snapshots = await seo_service.get_domain_rank_history(
        domain=domain, org_id=None, days=days,
    )
    return {"domain": domain, "days": days, "snapshots": snapshots}


from pydantic import BaseModel as _BaseModel, Field as _Field


class KeywordRequest(_BaseModel):
    seed_keyword: str = _Field(..., max_length=200)
    location_code: int | None = _Field(default=None)


@router.post(
    "/keywords",
    summary="Keyword discovery",
    tags=["seo"],
    responses={
        429: {"description": "Rate limit exceeded"},
        503: {"description": "SEO service not configured"},
    },
)
@limiter.limit("5/minute")
async def keyword_discovery(
    request: Request,
    body: KeywordRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> dict:
    """Discover keyword suggestions with volume and difficulty metrics."""
    seo_service = _get_seo_service(request)
    if seo_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "seo_unavailable", "message": "SEO service is not configured"},
        )

    try:
        result = await seo_service.keyword_analysis(
            keywords=[body.seed_keyword],
            location_code=body.location_code,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "seo_provider_error", "message": str(exc)},
        ) from exc
    return result
