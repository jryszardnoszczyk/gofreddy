"""Video-mention bridge — extract video URLs from mention content/metadata."""

from __future__ import annotations

import logging
import re
from typing import Any

from .models import RawMention

logger = logging.getLogger(__name__)

# Compiled regex patterns for video URL extraction
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # TikTok
    ("tiktok", re.compile(r"https?://(?:www\.)?tiktok\.com/@[\w.]+/video/(\d+)", re.I)),
    ("tiktok", re.compile(r"https?://(?:vm|m)\.tiktok\.com/([\w]+)", re.I)),
    ("tiktok", re.compile(r"https?://(?:www\.)?tiktok\.com/t/([\w]+)", re.I)),
    # Instagram
    ("instagram", re.compile(r"https?://(?:www\.)?instagram\.com/reel/([\w-]+)", re.I)),
    ("instagram", re.compile(r"https?://(?:www\.)?instagram\.com/p/([\w-]+)", re.I)),
    # YouTube
    ("youtube", re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=([\w-]+)", re.I)),
    ("youtube", re.compile(r"https?://youtu\.be/([\w-]+)", re.I)),
    ("youtube", re.compile(r"https?://(?:www\.)?youtube\.com/shorts/([\w-]+)", re.I)),
]


def extract_video_urls(mention: RawMention) -> list[dict[str, str]]:
    """Extract video URLs from mention content and metadata.

    Returns list of {"platform": "...", "video_id": "...", "url": "..."}.
    Deduplicates by (platform, video_id).
    """
    # Collect all text sources to search
    texts: list[str] = []
    if mention.content:
        texts.append(mention.content)
    if mention.url:
        texts.append(mention.url)

    # Also check metadata fields
    metadata = mention.metadata or {}
    for key in ("urls_in_text", "media_urls", "video_urls"):
        val = metadata.get(key, [])
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    texts.append(item)

    # Search for video URLs
    seen: set[tuple[str, str]] = set()
    results: list[dict[str, str]] = []

    combined_text = " ".join(texts)
    for platform, pattern in _PATTERNS:
        for match in pattern.finditer(combined_text):
            video_id = match.group(1)
            url = match.group(0)
            key = (platform, video_id)
            if key not in seen:
                seen.add(key)
                results.append({
                    "platform": platform,
                    "video_id": video_id,
                    "url": url,
                })

    return results


def enrich_mentions_with_video_urls(mentions: list[RawMention]) -> None:
    """Pre-persistence enrichment: extract video URLs and store in metadata.

    Per-mention error isolation — regex crash on one mention doesn't block others.
    """
    for mention in mentions:
        try:
            video_urls = extract_video_urls(mention)
            if video_urls:
                mention.metadata.setdefault("video_urls", [])
                # Merge without duplicates
                existing = {
                    (v["platform"], v["video_id"])
                    for v in mention.metadata["video_urls"]
                    if isinstance(v, dict)
                }
                for v in video_urls:
                    if (v["platform"], v["video_id"]) not in existing:
                        mention.metadata["video_urls"].append(v)
        except Exception:
            logger.warning(
                "Video URL extraction failed for mention %s",
                mention.source_id,
                exc_info=True,
            )
