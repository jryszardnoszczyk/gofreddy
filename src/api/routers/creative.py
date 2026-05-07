"""Creative pattern analysis endpoint."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ...common.enums import Platform
from ...creative import CreativePatternService
from ...schemas import CreativePatterns
from ...storage import VideoNotFoundError
from ..dependencies import get_current_user_id
from ..rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creative", tags=["creative"])


def _get_creative_service(request: Request) -> CreativePatternService:
    service = getattr(request.app.state, "creative_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "service_unavailable", "message": "Creative analysis service not configured"},
        )
    return service


async def _download_video(storage, analysis) -> Path:
    try:
        parts = (analysis.cache_key or "").split(":")
        platform = Platform(parts[0])
        video_id = parts[1]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "video_url_unavailable", "message": "Could not derive video location"},
        ) from exc

    try:
        return await storage.download_to_temp(platform, video_id)
    except (VideoNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "video_not_found", "message": "Video no longer available in storage"},
        ) from exc


@router.get("/{analysis_id}", response_model=CreativePatterns)
@limiter.limit("30/minute")
async def get_creative_patterns(
    request: Request,
    analysis_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: CreativePatternService = Depends(_get_creative_service),
) -> CreativePatterns:
    repo = request.app.state.analysis_repository
    if not await repo.user_has_access(analysis_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    cached = await service.get_creative_patterns(analysis_id)
    if cached is not None:
        return cached

    analysis = await repo.get_by_id(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    video_path = await _download_video(request.app.state.video_storage, analysis)
    try:
        result = await service.analyze_creative_patterns(
            video_path=str(video_path),
            video_analysis_id=analysis_id,
            video_id=str(analysis.video_id),
            force_refresh=True,
        )
        return result.patterns
    finally:
        video_path.unlink(missing_ok=True)
