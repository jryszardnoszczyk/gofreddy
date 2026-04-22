"""Competitive ad intelligence service layer."""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import re
from typing import Any, Literal, TYPE_CHECKING

foreplay_raw_count_var: contextvars.ContextVar[int] = contextvars.ContextVar("foreplay_raw_count", default=0)
from urllib.parse import urlparse

from cachetools import TTLCache

from ..evaluation.judges.sonnet_agent import SonnetAgentError, call_sonnet_json
from .exceptions import AllProvidersUnavailableError
from .utils import normalize_domain

if TYPE_CHECKING:
    from .config import CompetitiveSettings
    from .providers.foreplay import ForeplayProvider
    from .providers.adyntel import AdyntelProvider

logger = logging.getLogger(__name__)

Verdict = Literal["YES", "NO", "UNSURE"]

# Module-level cache for agent domain-disambiguation decisions (R-#38).
# Keyed on (brand, queried_domain, landing_domain) → verdict.
# Module-level because the decision is pure wrt inputs: same ad→same verdict
# regardless of which CompetitiveAdService instance asks, across a process
# lifetime. No TTL — the whole process dies before staleness becomes an issue.
_AD_DOMAIN_AGENT_CACHE: dict[tuple[str, str, str], Verdict] = {}


def _extract_image_url(body_text: str) -> str | None:
    """Extract first image URL from HTML body_text (#30)."""
    if not body_text:
        return None
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body_text)
    return match.group(1) if match else None


def _normalize_host(host: str) -> str:
    """Lowercase and strip 'www.' prefix from a hostname."""
    return host.lower().removeprefix("www.")


def _landing_host(link_url: str | None) -> str:
    """Parse link_url → normalized hostname; '' on malformed/missing input."""
    if not link_url:
        return ""
    try:
        parsed = urlparse(link_url)
    except Exception:
        return ""
    return _normalize_host(parsed.hostname or "")


def _registered_domain(host: str) -> str:
    """Return the registered-domain (eTLD+1) portion of ``host``.

    Heuristic: last two labels. Good enough for the near-miss gate — we
    don't need perfect eTLD logic here, we just want `ads.example.com`
    and `example.com` to share a registered domain. Bare TLDs and empty
    strings fall back to the input unchanged.
    """
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) < 2:
        return host
    return ".".join(parts[-2:])


def _is_near_miss(landing_host: str, queried_host: str) -> bool:
    """True when hosts differ but are related enough to be worth agent review.

    Heuristic (R-#38):
      - landing or queried is a substring of the other (covers subdomains
        like `ads.example.com` vs `example.com`), OR
      - their registered (eTLD+1) domains match (covers edge CDN/regional
        hosts sharing a parent).

    Conservative: exact-match short-circuit happens upstream so this only
    fires on true hostname mismatch. Missing landing_host (malformed URL)
    is NOT a near-miss — upstream keeps those ads unchanged.
    """
    if not landing_host or not queried_host or landing_host == queried_host:
        return False
    if queried_host in landing_host or landing_host in queried_host:
        return True
    return _registered_domain(landing_host) == _registered_domain(queried_host)


def _ad_domain_matches(ad: dict[str, Any], queried_domain: str) -> bool:
    """Fast-path exact-hostname match for an ad's ``link_url``.

    Returns True for:
      - Ads with no link_url (we can't validate → keep).
      - Ads whose landing hostname equals the queried domain (ignoring
        ``www.`` and case).

    All other cases return False. Near-miss recovery via the Sonnet
    agent happens in :func:`_agent_recover_near_misses`, invoked by
    :meth:`CompetitiveAdService.search_ads` after this filter.
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


def _build_agent_prompt(brand: str, queried_domain: str, candidates: list[dict[str, Any]]) -> str:
    """Build the batched Sonnet prompt for ad-domain disambiguation (R-#38)."""
    items = []
    for idx, ad in enumerate(candidates):
        items.append({
            "id": f"a{idx}",
            "landing_domain": _landing_host(ad.get("link_url")),
            "link_url": ad.get("link_url") or "",
            "headline": (ad.get("headline") or "")[:200],
            "body_text": (ad.get("body_text") or "")[:500],
            "image_url": ad.get("image_url") or "",
        })
    payload = json.dumps(
        {"brand": brand, "queried_domain": queried_domain, "ads": items},
        ensure_ascii=False,
    )
    return (
        "You are disambiguating whether paid ads genuinely belong to a "
        "specific brand. The queried brand domain is the ground truth. "
        "Ads were fetched by a third-party scraper and the landing domain "
        "may differ due to tracking redirects, CDNs, subdomains, regional "
        "storefronts, or multi-domain brands.\n\n"
        "For each ad, answer YES (genuinely this brand's ad), NO (different "
        "advertiser that happened to mention the brand or share a substring), "
        "or UNSURE (insufficient signal).\n\n"
        f"Input:\n{payload}\n\n"
        'Output ONLY a single JSON object: {"verdicts": [{"id": "a0", "verdict": "YES"}, ...]}. '
        "No prose, no markdown fencing."
    )


async def _agent_recover_near_misses(
    brand: str,
    queried_domain: str,
    candidates: list[dict[str, Any]],
) -> dict[int, Verdict]:
    """Batched Sonnet call → {candidate_index: verdict}. Cache-aware.

    Batching rationale: one subprocess amortizes CLI startup across all
    near-miss ads for a single `search_ads` call. Typical drop counts are
    small (single-digit) so per-ad latency is dominated by the shared
    Claude round-trip. Per-ad calls would multiply that cost linearly.

    Cache hits short-circuit before the subprocess is spawned. If every
    candidate is cached, no agent call is made.
    """
    verdicts: dict[int, Verdict] = {}
    uncached: list[tuple[int, dict[str, Any]]] = []
    q = _normalize_host(queried_domain)
    for idx, ad in enumerate(candidates):
        key = (brand, q, _landing_host(ad.get("link_url")))
        cached = _AD_DOMAIN_AGENT_CACHE.get(key)
        if cached is not None:
            verdicts[idx] = cached
        else:
            uncached.append((idx, ad))

    if not uncached:
        return verdicts

    uncached_ads = [ad for _, ad in uncached]
    prompt = _build_agent_prompt(brand, queried_domain, uncached_ads)
    try:
        data = await call_sonnet_json(prompt, operation="ad_domain_disambiguation")
    except SonnetAgentError as e:
        logger.warning("ad_domain_agent_failed: %s — treating all near-misses as NO", e)
        for idx, _ in uncached:
            verdicts[idx] = "NO"
        return verdicts

    raw_verdicts = data.get("verdicts") or []
    by_id: dict[str, Verdict] = {}
    for item in raw_verdicts:
        if not isinstance(item, dict):
            continue
        aid = item.get("id")
        v = item.get("verdict")
        if isinstance(aid, str) and v in ("YES", "NO", "UNSURE"):
            by_id[aid] = v  # type: ignore[assignment]

    for local_idx, (idx, ad) in enumerate(uncached):
        v = by_id.get(f"a{local_idx}", "UNSURE")
        verdicts[idx] = v
        _AD_DOMAIN_AGENT_CACHE[(brand, q, _landing_host(ad.get("link_url")))] = v

    return verdicts


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
        #
        # Fast-path exact match keeps the ad without any agent call. Hostnames
        # that *look* related (subdomain, shared registered-domain) are sent
        # as a batch to the Sonnet agent for YES/NO/UNSURE adjudication
        # (R-#38). UNSURE is treated as NO for the downstream filter — we'd
        # rather drop a genuine ad than attribute a rival's ad to the brand.
        pre_filter_count = len(results)
        exact_keep: list[dict[str, Any]] = []
        near_miss: list[dict[str, Any]] = []
        hard_drop = 0
        q_host = _normalize_host(domain)
        for ad in results:
            if _ad_domain_matches(ad, domain):
                exact_keep.append(ad)
                continue
            landing = _landing_host(ad.get("link_url"))
            if _is_near_miss(landing, q_host):
                near_miss.append(ad)
            else:
                hard_drop += 1

        recovered = 0
        if near_miss:
            verdicts = await _agent_recover_near_misses(domain, domain, near_miss)
            for idx, ad in enumerate(near_miss):
                if verdicts.get(idx) == "YES":
                    exact_keep.append(ad)
                    recovered += 1

        results = exact_keep
        filtered_count = pre_filter_count - len(results)
        if filtered_count or recovered:
            logger.warning(
                "ad_domain_filter: removed %d/%d ads for domain=%s "
                "(hard_drop=%d, near_miss=%d, recovered=%d)",
                filtered_count,
                pre_filter_count,
                domain,
                hard_drop,
                len(near_miss),
                recovered,
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
