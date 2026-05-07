"""Video analysis endpoints used by storyboard autoresearch."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...common.enums import Platform
from ...fetcher import FetcherError
from ..dependencies import get_current_user_id
from ..rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])

ALLOWED_DOMAINS: dict[str, Platform] = {
    "tiktok.com": Platform.TIKTOK,
    "www.tiktok.com": Platform.TIKTOK,
    "vm.tiktok.com": Platform.TIKTOK,
    "youtube.com": Platform.YOUTUBE,
    "www.youtube.com": Platform.YOUTUBE,
    "youtu.be": Platform.YOUTUBE,
    "instagram.com": Platform.INSTAGRAM,
    "www.instagram.com": Platform.INSTAGRAM,
}


class AnalyzeVideosRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)
    force_refresh: bool = False


def parse_video_url(url: str) -> tuple[Platform, str]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(f"Unsupported or blocked domain: {domain}")

    platform = ALLOWED_DOMAINS[domain]
    parts = [p for p in parsed.path.split("/") if p]

    if platform == Platform.TIKTOK:
        if "video" in parts:
            idx = parts.index("video")
            if idx + 1 < len(parts):
                video_id = parts[idx + 1].split("?")[0]
                if re.match(r"^\d{1,19}$", video_id):
                    return platform, video_id
        raise ValueError("Invalid TikTok URL format")

    if platform == Platform.INSTAGRAM:
        if parts and parts[0] in ("reel", "p") and len(parts) > 1:
            video_id = parts[1].split("?")[0]
            if re.match(r"^[A-Za-z0-9_-]{10,12}$", video_id):
                return platform, video_id
        raise ValueError("Invalid Instagram URL format")

    if platform == Platform.YOUTUBE:
        if domain == "youtu.be":
            video_id = parsed.path.strip("/").split("?")[0]
        else:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        if video_id and re.match(r"^[A-Za-z0-9_-]{11}$", video_id):
            return platform, video_id
        raise ValueError("Invalid YouTube URL format")

    raise ValueError(f"Cannot parse video URL: {url}")


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


@router.post("/videos", summary="Analyze specific video URLs")
@limiter.limit("30/minute")
async def analyze_videos(
    request: Request,
    body: AnalyzeVideosRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> dict:
    service = _get_analysis_service(request)
    semaphore = asyncio.Semaphore(5)

    async def process(url: str) -> dict:
        async with semaphore:
            try:
                platform, video_id = parse_video_url(url)
                video_uuid = uuid5(NAMESPACE_URL, f"{platform.value}:{video_id}")
                cached = None if body.force_refresh else await service.get_cached(platform, video_id, video_uuid)
                if cached is not None:
                    return _analysis_payload(platform, video_id, cached)

                fetcher = _get_fetcher(request, platform)
                fetched = await fetcher.fetch_video(platform, video_id)
                result = await service.analyze(
                    platform=platform,
                    video_id=video_id,
                    video_uuid=video_uuid,
                    force_refresh=body.force_refresh,
                    user_id=user_id,
                    transcript_text=fetched.transcript_text,
                    duration_seconds=fetched.duration_seconds,
                    title=fetched.title,
                )
                return _analysis_payload(platform, video_id, result)
            except ValueError as exc:
                return {"url": url, "error": str(exc), "error_type": "ValidationError"}
            except FetcherError as exc:
                return {"url": url, "error": str(exc), "error_type": type(exc).__name__}
            except Exception as exc:
                logger.exception("video_analysis_failed url=%s", url)
                return {"url": url, "error": "Analysis failed", "error_type": type(exc).__name__}

    try:
        outcomes = await asyncio.wait_for(
            asyncio.gather(*[process(url) for url in body.urls]),
            timeout=240,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "analysis_timeout", "message": "Analysis timed out after 240 seconds"},
        ) from exc

    results = [item for item in outcomes if "analysis_id" in item]
    errors = [item for item in outcomes if "analysis_id" not in item]
    return {
        "results": results,
        "errors": errors,
        "success_rate": len(results) / len(body.urls) if body.urls else 0.0,
    }
