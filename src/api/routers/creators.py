"""Creator video listing and creator-level analysis endpoints."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field

from ...common.enums import Platform
from ...fetcher import CreatorNotFoundError, FetcherError
from ..dependencies import get_current_user_id
from ..rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["creators"])


class AnalyzeCreatorRequest(BaseModel):
    platform: Platform
    username: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)
    force_refresh: bool = False


class VideoStatsResponse(BaseModel):
    video_id: str
    play_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    posted_at: datetime | None = None
    title: str | None = None
    duration_seconds: int | None = None


def _get_fetcher(request: Request, platform: Platform):
    fetcher = getattr(request.app.state, "fetchers", {}).get(platform)
    if fetcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "provider_unavailable", "message": f"No fetcher for {platform.value}"},
        )
    return fetcher


def _get_analysis_service(request: Request):
    service = getattr(request.app.state, "analysis_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Analysis service not configured"},
        )
    return service


def _analysis_payload(platform: Platform, video_id: str, result) -> dict:
    payload = result.analysis.model_dump(mode="json")
    return {
        "video_id": video_id,
        "platform": platform.value,
        "analysis_id": str(result.record_id),
        "overall_safe": payload.get("overall_safe"),
        "overall_confidence": payload.get("overall_confidence"),
        "risks_detected": payload.get("risks_detected", []),
        "summary": payload.get("summary", ""),
        "content_categories": payload.get("content_categories", []),
        "moderation_flags": payload.get("moderation_flags", []),
        "sponsored_content": payload.get("sponsored_content"),
        "analyzed_at": datetime.now(UTC).isoformat(),
        "cached": result.cached,
        "cost_usd": result.cost_usd,
    }


@router.get(
    "/creators/{site}/{handle}/videos",
    response_model=list[VideoStatsResponse],
    summary="List a creator's recent videos with stats",
)
@limiter.limit("30/minute")
async def list_creator_videos(
    request: Request,
    site: Platform = Path(..., description="Social media platform"),
    handle: str = Path(..., min_length=1, max_length=100),
    limit: int = Query(default=30, ge=1, le=100),
    _user_id: UUID = Depends(get_current_user_id),
) -> list[VideoStatsResponse]:
    fetcher = _get_fetcher(request, site)
    try:
        videos = await fetcher._list_creator_videos(handle, limit)
    except CreatorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "creator_not_found", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.warning("creator_video_list_failed platform=%s handle=%s", site.value, handle, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "provider_error", "message": type(exc).__name__},
        ) from exc
    return [
        VideoStatsResponse(
            video_id=v.video_id,
            play_count=v.play_count,
            like_count=v.like_count,
            comment_count=v.comment_count,
            share_count=v.share_count,
            posted_at=v.posted_at,
            title=v.title,
            duration_seconds=v.duration_seconds,
        )
        for v in videos
    ]


@router.post("/analyze/creator", summary="Analyze a creator's recent videos")
@limiter.limit("30/minute")
async def analyze_creator(
    request: Request,
    body: AnalyzeCreatorRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> dict:
    fetcher = _get_fetcher(request, body.platform)
    service = _get_analysis_service(request)

    try:
        batch = await fetcher.fetch_creator_videos(
            platform=body.platform,
            creator_handle=body.username,
            limit=body.limit,
        )
    except CreatorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "creator_not_found", "message": str(exc)},
        ) from exc

    semaphore = asyncio.Semaphore(getattr(request.app.state, "max_concurrent_analysis", 5))

    async def analyze_one(video):
        async with semaphore:
            try:
                video_uuid = uuid5(NAMESPACE_URL, f"{body.platform.value}:{video.video_id}")
                result = await service.analyze(
                    platform=body.platform,
                    video_id=video.video_id,
                    video_uuid=video_uuid,
                    force_refresh=body.force_refresh,
                    user_id=user_id,
                    transcript_text=video.transcript_text,
                    duration_seconds=video.duration_seconds,
                    title=video.title,
                )
                return _analysis_payload(body.platform, video.video_id, result)
            except FetcherError as exc:
                return {"video_id": video.video_id, "error_code": type(exc).__name__, "error_message": str(exc)}
            except Exception:
                logger.exception("creator_video_analysis_failed video_id=%s", video.video_id)
                return {"video_id": video.video_id, "error_code": "analysis_failed", "error_message": "Analysis failed"}

    outcomes = await asyncio.gather(*[analyze_one(v) for v in batch.results])
    results = [item for item in outcomes if "analysis_id" in item]
    errors = [
        {
            "video_id": err.video_id,
            "platform": err.platform.value,
            "error_code": err.error_type.value,
            "error_message": err.message,
            "retryable": err.retryable,
            "retry_after_seconds": err.retry_after_seconds,
            "alternative_action": err.alternative_action,
        }
        for err in batch.errors
    ]
    errors.extend(item for item in outcomes if "analysis_id" not in item)
    total = len(results) + len(errors)
    return {
        "creator_username": body.username,
        "platform": body.platform.value,
        "videos_analyzed": len(results),
        "results": results,
        "errors": errors,
        "aggregate_risk_score": (
            sum(1 for item in results if not item.get("overall_safe")) / len(results)
            if results else 0.0
        ),
        "success_rate": len(results) / total if total else 1.0,
    }
