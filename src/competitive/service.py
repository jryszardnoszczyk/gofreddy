"""Competitive ad intelligence service layer."""

from __future__ import annotations

import asyncio
import contextvars
import logging
import re
from typing import Any, TYPE_CHECKING

foreplay_raw_count_var: contextvars.ContextVar[int] = contextvars.ContextVar("foreplay_raw_count", default=0)
from urllib.parse import urlparse

from cachetools import TTLCache

from .exceptions import AllProvidersUnavailableError
from .utils import normalize_domain

if TYPE_CHECKING:
    from .config import CompetitiveSettings
    from .providers.foreplay import ForeplayProvider
    from .providers.adyntel import AdyntelProvider

logger = logging.getLogger(__name__)


def _extract_image_url(body_text: str) -> str | None:
    """Extract first image URL from HTML body_text (#30)."""
    if not body_text:
        return None
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body_text)
    return match.group(1) if match else None


def _normalize_host(host: str) -> str:
    """Lowercase and strip 'www.' prefix from a hostname."""
    return host.lower().removeprefix("www.")


def _ad_domain_matches(ad: dict[str, Any], queried_domain: str) -> bool:
    """Check whether an ad's link_url domain matches the queried domain.

    Ads with no ``link_url`` are kept (we can't validate them).
    """
    link_url = ad.get("link_url")
    if not link_url:
        return True
    try:
        parsed = urlparse(link_url)
        host = parsed.hostname or ""
    except Exception:
        return True  # Malformed URL — keep rather than silently drop
    return _normalize_host(host) == _normalize_host(queried_domain)


class CompetitiveAdService:
    """Unified ad intelligence service aggregating Foreplay and Adyntel."""

    def __init__(
        self,
        foreplay_provider: ForeplayProvider | None,
        adyntel_provider: AdyntelProvider | None,
        settings: CompetitiveSettings,
    ) -> None:
        self._foreplay = foreplay_provider
        self._adyntel = adyntel_provider
        self._settings = settings
        # Cache stores (results, fetch_limit) so we know whether a larger request needs re-fetch
        self._cache: TTLCache[str, tuple[list[dict[str, Any]], int]] = TTLCache(maxsize=200, ttl=1800)

    async def search_ads(
        self,
        domain: str,
        platform: str = "all",
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Search for competitor ads across configured providers.

        Runs Foreplay and Adyntel in parallel when platform="all".
        Gracefully degrades if one provider fails.
        Results are cached by domain+platform for 30 minutes.
        """
        domain = normalize_domain(domain)
        limit = min(limit, 100)

        cache_key = f"{domain}:{platform}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            cached_results, fetch_limit = cached
            if fetch_limit >= limit:
                return cached_results[:limit]

        tasks: list[Any] = []
        task_labels: list[str] = []

        if platform in ("meta", "tiktok", "linkedin", "all") and self._foreplay:
            tasks.append(self._foreplay.search_ads_by_domain(domain, limit=limit))
            task_labels.append("foreplay")

        if platform in ("google", "all") and self._adyntel:
            # adyntel_max_pages is a process-level setting; if it ever becomes
            # per-request, the cache key must include it.
            tasks.append(self._adyntel.search_google_ads(
                domain=domain, max_pages=self._settings.adyntel_max_pages,
            ))
            task_labels.append("adyntel")

        if not tasks:
            raise AllProvidersUnavailableError(
                "No ad providers configured for requested platforms"
            )

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[dict[str, Any]] = []
        failures = 0
        for label, raw in zip(task_labels, raw_results):
            if isinstance(raw, Exception):
                logger.warning(
                    "ad_provider_failed: %s: %s", label, raw.__class__.__name__
                )
                failures += 1
                continue
            if label == "foreplay":
                foreplay_raw_count_var.set(len(raw) if isinstance(raw, list) else 0)
                results.extend(self._normalize_foreplay(raw))
            elif label == "adyntel":
                results.extend(self._normalize_adyntel(raw))

        if failures == len(tasks) and not results:
            raise AllProvidersUnavailableError("All ad providers failed")

        # Filter out ads whose link_url domain doesn't match the queried
        # domain.  Foreplay uses substring matching on brand names, so e.g.
        # querying "sketch.com" can return ads for "mangasketch.com" (#11).
        pre_filter_count = len(results)
        results = [ad for ad in results if _ad_domain_matches(ad, domain)]
        filtered_count = pre_filter_count - len(results)
        if filtered_count:
            logger.warning(
                "ad_domain_filter: removed %d/%d ads with mismatched link_url for domain=%s",
                filtered_count,
                pre_filter_count,
                domain,
            )

        self._cache[cache_key] = (results, limit)
        return results[:limit]

    def _normalize_foreplay(self, ads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Foreplay ad response to unified shape.

        DPA/DCO ads have empty top-level headline/description/image/video —
        the real creative content lives inside ``cards[]``. We fall through
        to the first card when top-level fields are blank.
        """
        normalized = []
        for ad in ads:
            # First card carries creative content for DPA/DCO ads
            card = (ad.get("cards") or [{}])[0] if ad.get("cards") else {}

            normalized.append({
                "provider": "foreplay",
                "platform": ad.get("publisher_platform") or "meta",
                "headline": ad.get("headline") or card.get("headline") or "",
                "body_text": ad.get("description") or card.get("description") or "",
                "cta_text": ad.get("cta_title") or card.get("cta_text") or "",
                "link_url": ad.get("link_url"),
                "image_url": ad.get("image") or ad.get("thumbnail") or card.get("image"),
                "video_url": ad.get("video") or card.get("video"),
                "is_active": bool(ad.get("live")),
                "started_at": ad.get("started_running"),
                "transcription": ad.get("full_transcription"),
                "persona": ad.get("persona"),
                "emotional_drivers": ad.get("emotional_drivers"),
                # Rich metadata
                "ad_type": ad.get("type"),
                "display_format": ad.get("display_format"),
                "categories": ad.get("categories"),
                "niches": ad.get("niches"),
                "creative_targeting": ad.get("creative_targeting"),
                "market_target": ad.get("market_target"),
                "product_category": ad.get("product_category"),
                "languages": ad.get("languages"),
                "running_duration": ad.get("running_duration"),
                "card_count": len(ad.get("cards") or []),
                "data_quality": "rich",  # Foreplay provides full creative data (#34)
            })
        return normalized

    def _normalize_adyntel(self, ads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize Adyntel ad response to unified shape."""
        normalized = []
        for ad in ads:
            # Extract content from first variant if available
            variants = ad.get("variants") or []
            content = variants[0].get("content", "") if variants else ""

            # Extract image_url from HTML body_text (#30)
            image_url = _extract_image_url(content)

            # Determine data_quality tier (#34)
            has_body = bool(content and content.strip())
            quality = "metadata_only" if has_body else "entity_only"

            normalized.append({
                "provider": "adyntel",
                "platform": "google",
                "headline": ad.get("advertiser_name") or "",
                "body_text": content,
                "cta_text": "",
                "link_url": ad.get("original_url"),
                "image_url": image_url,
                "video_url": None,
                "is_active": True,  # Adyntel returns active ads
                "started_at": ad.get("start"),
                "transcription": None,
                "persona": None,
                "emotional_drivers": None,
                "data_quality": quality,
            })
        return normalized
