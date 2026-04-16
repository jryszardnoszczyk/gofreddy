"""Batch vision enrichment for competitive ad creatives.

Uses Gemini Flash vision to analyze ad creative images/videos during GATHER,
adding visual analysis metadata to each ad.
"""

from __future__ import annotations

import asyncio
import base64
import ipaddress
import json
import logging
from urllib.parse import urlparse
from typing import Any

import httpx

from ..common.cost_recorder import cost_recorder as _cost_recorder
from ..common.gemini_models import GEMINI_FLASH

logger = logging.getLogger(__name__)

VISION_PROMPT = """Analyze this ad creative image. Return a JSON object with:
{
    "creative_type": "product_shot|lifestyle|text_overlay|logo|infographic|screenshot|other",
    "visual_tone": "premium|casual|professional|playful|urgent|minimal",
    "dominant_colors": ["color1", "color2", "color3"],
    "production_quality": "high|medium|low",
    "text_present": true/false,
    "text_content": "any visible text",
    "people_present": true/false,
    "brand_visible": true/false,
    "call_to_action_visible": true/false
}
Return ONLY valid JSON, no explanation."""

MAX_IMAGE_BYTES = 2_000_000  # 2MB


def _validate_image_url(url: str) -> None:
    """Reject URLs that could cause SSRF or fetch non-image content."""
    parsed = urlparse(url)

    # Must be HTTPS (or HTTP for known CDNs)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    hostname = parsed.hostname or ""

    # Block cloud metadata endpoints
    blocked_hosts = {"169.254.169.254", "metadata.google.internal", "metadata.google.com"}
    if hostname in blocked_hosts:
        raise ValueError(f"Blocked host: {hostname}")

    # Block private/reserved IPs
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return  # hostname is a domain name, not an IP — that's fine
    if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
        raise ValueError(f"Private/reserved IP: {hostname}")


class CreativeVisionAnalyzer:
    """Analyze ad creative images using Gemini Flash vision."""

    MAX_CONCURRENT = 10
    MAX_IMAGES_PER_BATCH = 150
    COST_PER_IMAGE = 0.001  # ~$0.001 per Gemini Flash vision call

    def __init__(self, genai_client: Any) -> None:
        self._client = genai_client
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

    async def enrich_ads(
        self,
        ads: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Add visual_analysis field to ads that have image URLs.

        Returns the same list with visual_analysis added where possible.
        Cost: ~$0.15 for 150 images.
        """
        analyzable = [
            (i, ad) for i, ad in enumerate(ads)
            if ad.get("image_url") and not ad.get("visual_analysis")
        ]

        if not analyzable:
            return ads

        analyzable = analyzable[:self.MAX_IMAGES_PER_BATCH]

        # Shared HTTP client for connection pooling
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10, connect=5),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=self.MAX_CONCURRENT),
        ) as http:
            tasks = [
                self._analyze_single(http, ad["image_url"])
                for _, ad in analyzable
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        analyzed_count = 0
        for (idx, _), result in zip(analyzable, results):
            if isinstance(result, dict):
                ads[idx]["visual_analysis"] = result
                analyzed_count += 1
            elif isinstance(result, Exception):
                logger.debug("vision_analysis_failed: %s", result)

        await _cost_recorder.record(
            "gemini_vision",
            "enrich_ads",
            cost_usd=self.COST_PER_IMAGE * analyzed_count,
            metadata={"analyzed": analyzed_count, "total": len(ads)},
        )

        return ads

    async def _analyze_single(self, http: httpx.AsyncClient, image_url: str) -> dict[str, Any]:
        """Download image and analyze via Gemini Flash with inline base64."""
        async with self._semaphore:
            try:
                _validate_image_url(image_url)

                resp = await http.get(image_url)
                resp.raise_for_status()

                # Enforce size limit
                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > MAX_IMAGE_BYTES:
                    raise ValueError(f"Image too large: {content_length} bytes")
                if len(resp.content) > MAX_IMAGE_BYTES:
                    raise ValueError(f"Image response exceeds {MAX_IMAGE_BYTES} byte limit")

                content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                if content_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
                    content_type = "image/jpeg"

                b64_data = base64.b64encode(resp.content).decode()

                response = await self._client.aio.models.generate_content(
                    model=GEMINI_FLASH,
                    contents=[
                        {"text": VISION_PROMPT},
                        {"inline_data": {"mime_type": content_type, "data": b64_data}},
                    ],
                    config={"temperature": 0.2},
                )
                text = (response.text or "{}").strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]

                return json.loads(text.strip())
            except Exception as e:
                raise RuntimeError(f"Vision analysis failed for {image_url[:80]}: {e}") from e
