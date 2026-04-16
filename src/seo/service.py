"""SEO audit service orchestrator."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any
from uuid import UUID

from .config import SeoSettings
from .exceptions import SeoAuditError
from .providers.dataforseo import DataForSeoProvider
from .providers.pagespeed import check_performance
from .repository import PostgresSeoRepository

logger = logging.getLogger(__name__)


class SeoService:
    """Orchestrates SEO audit sub-analyses.

    Methods correspond to the include parameter of search_optimization_audit:
    - technical_audit(url) → dict
    - keyword_analysis(keywords) → dict
    - check_performance(url) → dict
    - backlink_analysis(url) → dict
    """

    def __init__(
        self,
        repository: PostgresSeoRepository,
        settings: SeoSettings,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._provider: DataForSeoProvider | None = None
        if settings.dataforseo_login and settings.dataforseo_password.get_secret_value():
            self._provider = DataForSeoProvider(
                login=settings.dataforseo_login,
                password=settings.dataforseo_password.get_secret_value(),
                sandbox=settings.dataforseo_sandbox,
                timeout=settings.dataforseo_timeout,
            )

    async def technical_audit(self, url: str) -> dict[str, Any]:
        """Run technical SEO audit via DataForSEO."""
        if not self._provider:
            return {"status": "unavailable", "reason": "DataForSEO credentials not configured"}
        result = await self._provider.technical_audit(url)
        return asdict(result)

    async def keyword_analysis(
        self,
        keywords: list[str],
        location_code: int | None = None,
    ) -> dict[str, Any]:
        """Analyze keyword metrics via DataForSEO."""
        if not self._provider:
            return {"status": "unavailable", "reason": "DataForSEO credentials not configured"}
        kwargs: dict[str, Any] = {"keywords": keywords}
        if location_code is not None:
            kwargs["location_code"] = location_code
        result = await self._provider.keyword_analysis(**kwargs)
        return asdict(result)

    async def check_performance(self, url: str) -> dict[str, Any]:
        """Check page performance via PageSpeed Insights."""
        result = await check_performance(
            url,
            api_key=self._settings.pagespeed_api_key.get_secret_value(),
            timeout=self._settings.pagespeed_timeout,
        )
        return asdict(result)

    async def backlink_analysis(self, url: str) -> dict[str, Any]:
        """Get backlink profile via DataForSEO."""
        if not self._provider:
            return {"status": "unavailable", "reason": "DataForSEO credentials not configured"}
        result = await self._provider.backlink_analysis(url)
        return asdict(result)

    async def snapshot_domain_rank(
        self, domain: str, org_id: "UUID | None" = None,
    ) -> dict[str, Any]:
        """Snapshot domain rank via DataForSEO and persist."""
        if not self._provider:
            return {"status": "unavailable", "reason": "DataForSEO credentials not configured"}
        snapshot = await self._provider.snapshot_domain_rank(domain)
        # Persist to database
        await self._repository.insert_domain_rank_snapshot(
            domain=snapshot.domain,
            rank=snapshot.rank,
            backlinks_total=snapshot.backlinks_total,
            referring_domains=snapshot.referring_domains,
            org_id=org_id,
        )
        return asdict(snapshot)

    async def get_domain_rank_history(
        self, domain: str, org_id: "UUID | None" = None, days: int = 90,
    ) -> list[dict[str, Any]]:
        """Query domain rank snapshots for time-series display."""
        return await self._repository.get_domain_rank_history(
            domain=domain, org_id=org_id, days=days,
        )
