"""SEO service — thin facade over DataForSEO provider.

Wires the keyword-discovery and domain-rank consumers in
``src/api/routers/geo.py`` to the existing ``DataForSeoProvider``.
The router checks ``request.app.state.seo_service`` and returns 503
``seo_unavailable`` when it is None; ``main.py`` constructs this when
DataForSEO credentials are present.
"""

from __future__ import annotations

from typing import Any

from .providers.dataforseo import DataForSeoProvider


class SeoService:
    """Async facade over DataForSEO with router-friendly return shapes."""

    def __init__(self, provider: DataForSeoProvider) -> None:
        self._provider = provider

    async def keyword_analysis(
        self,
        keywords: list[str],
        location_code: int | None = None,
        language_code: str = "en",
    ) -> dict[str, Any]:
        # router passes location_code=None when caller omits --location;
        # DataForSEO rejects null location_code, so default to US (2840).
        result = await self._provider.keyword_analysis(
            keywords=keywords,
            location_code=location_code if location_code is not None else 2840,
            language_code=language_code,
        )
        return {
            "location_code": result.location_code,
            "language_code": result.language_code,
            "keywords": [
                {
                    "keyword": k.keyword,
                    "search_volume": k.search_volume,
                    "cpc": k.cpc,
                    "competition": k.competition,
                    "difficulty": k.difficulty,
                    "trend": list(k.trend),
                }
                for k in result.keywords
            ],
        }

    async def get_domain_rank_history(
        self,
        *,
        domain: str,
        org_id: Any | None = None,  # accepted for router parity; unused (no persistence)
        days: int = 90,
    ) -> list[dict[str, Any]]:
        snapshot = await self._provider.snapshot_domain_rank(domain)
        return [
            {
                "domain": snapshot.domain,
                "rank": snapshot.rank,
                "backlinks_total": snapshot.backlinks_total,
                "referring_domains": snapshot.referring_domains,
                "snapshot_date": (
                    snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else None
                ),
            }
        ]
