"""Competitive intelligence API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from ...competitive.exceptions import AllProvidersUnavailableError
from ..rate_limit import limiter
from ..schemas import (
    CompetitiveAdSearchRequest,
    CompetitiveAdSearchResponse,
    CreatorSearchRequest,
    CreatorSearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competitive", tags=["competitive"])


def _get_ad_service(request: Request):
    """Get CompetitiveAdService from app state, or raise 503."""
    service = getattr(request.app.state, "ad_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Ad search service not configured"},
        )
    return service


def _get_creator_search_service(request: Request):
    """Get CreatorSearchService from app state, or raise 503."""
    service = getattr(request.app.state, "creator_search_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Creator search service not configured"},
        )
    return service


@router.post(
    "/ads/search",
    response_model=CompetitiveAdSearchResponse,
    summary="Search competitor ads by domain",
    responses={
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Ad service not configured"},
    },
)
@limiter.limit("10/minute")
async def search_ads(
    request: Request,
    body: CompetitiveAdSearchRequest,
) -> CompetitiveAdSearchResponse:
    """Search competitor ads across Foreplay and Adyntel."""
    ad_service = _get_ad_service(request)

    try:
        ads = await ad_service.search_ads(
            body.domain, platform=body.platform, limit=body.limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_domain", "message": str(e)},
        )
    except AllProvidersUnavailableError as e:
        logger.warning("Ad search providers unavailable for %s: %s", body.domain, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": str(e) or "Ad providers unavailable"},
        )
    except Exception as e:
        logger.error("Ad search failed for %s: %s: %s", body.domain, type(e).__name__, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "search_error", "message": f"Ad search failed: {type(e).__name__}"},
        )

    from ...competitive.service import foreplay_raw_count_var
    return CompetitiveAdSearchResponse(
        domain=body.domain,
        ad_count=len(ads),
        ads=ads,
        raw_foreplay_ads_count=foreplay_raw_count_var.get(),
    )


@router.post(
    "/creators/search",
    response_model=CreatorSearchResponse,
    summary="Search for competitor-affiliated creators",
    responses={
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Creator search service not configured"},
    },
)
@limiter.limit("10/minute")
async def search_creators(
    request: Request,
    body: CreatorSearchRequest,
) -> CreatorSearchResponse:
    """Search for creators across TikTok, YouTube, and content platforms."""
    service = _get_creator_search_service(request)

    try:
        result = await service.search_creators(
            body.query,
            platforms=body.platforms,
            limit=body.limit,
        )
    except Exception as e:
        logger.error("Creator search failed for %s: %s", body.query, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "search_error", "message": f"Creator search failed: {type(e).__name__}"},
        )

    return CreatorSearchResponse(
        query=body.query,
        creator_count=len(result.creators),
        creators=[
            {
                "username": c.username,
                "platform": c.platform,
                "display_name": c.display_name,
                "follower_count": c.follower_count,
                "bio": c.bio,
                "content_type": c.content_type,
                "relevance_signal": c.relevance_signal,
                "profile_url": c.profile_url,
                "source": c.source,
            }
            for c in result.creators
        ],
        platforms_searched=result.platforms_searched,
        errors=result.errors,
    )
