"""GEO audit service orchestrator."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from .config import GeoSettings
from .exceptions import GeoAuditError
from .link_graph import SiteLinkGraph
from .models import AnalyzeResult, ArticleResult, AuditFindings, FormatResult, GenerateResult
from .orchestrator import run_geo_audit
from .providers.cloro import CloroClient
from .repository import PostgresGeoRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GeoAuditResult:
    """Result from GEO audit service with all structured intermediates."""

    audit_id: UUID
    report: FormatResult
    findings: AuditFindings | None = None
    analysis: AnalyzeResult | None = None
    generated: GenerateResult | None = None


class GeoService:
    """Orchestrates GEO audit pipeline.

    Creates own Cloro client from settings (not injected from app.state).
    Follows FraudDetectionService pattern.
    """

    def __init__(
        self,
        repository: PostgresGeoRepository,
        settings: GeoSettings,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._cloro_client = CloroClient(
            api_key=settings.cloro_api_key.get_secret_value(),
            timeout=60.0,
        )

    async def close(self) -> None:
        """Cleanup resources."""
        await self._cloro_client.close()

    async def get_by_id(
        self, audit_id: UUID, user_id: UUID | None = None
    ) -> dict[str, Any] | None:
        """Retrieve audit by ID, with optional ownership check."""
        if user_id is not None:
            return await self._repository.get_by_id_and_user(audit_id, user_id)
        return await self._repository.get_by_id(audit_id)

    async def list_audits(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List audits for a user."""
        return await self._repository.list_by_user(user_id, limit, offset)

    async def run_audit(
        self,
        url: str,
        user_id: UUID,
        keywords: list[str] | None = None,
    ) -> GeoAuditResult:
        """Run a complete GEO audit.

        Args:
            url: URL to audit (must be HTTPS)
            user_id: Owner user ID
            keywords: Optional target keywords for optimization

        Returns:
            GeoAuditResult with audit ID, report, and all structured intermediates

        Raises:
            GeoAuditError: On non-recoverable failures
        """
        if not self._settings.enable_geo:
            raise GeoAuditError("DISABLED", "GEO audit service is not enabled")

        # Create pending audit record
        audit_id = uuid4()
        await self._repository.create(
            audit_id=audit_id,
            user_id=user_id,
            url=url,
            keywords=keywords,
        )

        # Run the pipeline (uses repository for status updates)
        pipeline_result = await run_geo_audit(
            audit_id=audit_id,
            page_url=url,
            user_id=user_id,
            repository=self._repository,
            gemini_api_key=self._settings.gemini_api_key.get_secret_value(),
            keywords=keywords,
            gemini_model=self._settings.gemini_model,
            cloro_api_key=self._settings.cloro_api_key.get_secret_value(),
        )

        return GeoAuditResult(
            audit_id=audit_id,
            report=pipeline_result.format_result,
            findings=pipeline_result.findings,
            analysis=pipeline_result.analyze_result,
            generated=pipeline_result.generate_result,
        )

    async def check_visibility(
        self,
        brand: str,
        keywords: list[str],
        platforms: list[str] | None = None,
        country: str | None = None,
    ) -> dict[str, Any]:
        """Check brand visibility across AI search platforms.

        Queries Cloro for each brand+keyword combo and reports citations.

        Args:
            brand: Brand name to check
            keywords: Keywords to query with the brand
            platforms: AI platforms to check (default: chatgpt, perplexity, gemini)
            country: ISO 3166-1 alpha-2 country code for geo-targeting

        Returns:
            Dict with results per query per platform, total citations, and summary
        """
        from .providers.cloro import VALID_PLATFORMS, QueryRequest

        if not self._cloro_client.is_available:
            return {"error": "geo_unavailable", "summary": "AI search service temporarily unavailable"}

        queries = [f"{brand} {kw}" for kw in keywords] if keywords else [brand]
        selected_platforms = platforms or ["chatgpt", "perplexity", "gemini"]
        selected_platforms = [p for p in selected_platforms if p in VALID_PLATFORMS]
        if not selected_platforms:
            selected_platforms = ["chatgpt", "perplexity", "gemini"]

        all_results: dict[str, Any] = {}
        total_citations = 0
        brand_lower = brand.lower()

        async def _gather_results() -> None:
            nonlocal total_citations
            for query_text in queries[:5]:
                request = QueryRequest(
                    prompt=query_text,
                    platforms=selected_platforms,
                    country=country,
                )
                result = await self._cloro_client.query(request)

                query_data: dict[str, Any] = {}
                for platform, response in result.results.items():
                    citation_count = sum(
                        1 for c in response.citations
                        if brand_lower in ((c.title or "").lower() + " " + (c.url or "").lower())
                    )
                    total_citations += citation_count
                    query_data[platform] = {
                        "mentioned_in_text": brand_lower in response.text.lower(),
                        "cited": citation_count > 0,
                        "citation_count": citation_count,
                        "citations": [
                            {"url": c.url, "title": c.title}
                            for c in response.citations
                            if brand_lower in ((c.title or "").lower() + " " + (c.url or "").lower())
                        ],
                    }
                for platform, error in result.errors.items():
                    query_data[platform] = {"error": error}

                all_results[query_text] = query_data

        try:
            await asyncio.wait_for(_gather_results(), timeout=45.0)
        except asyncio.TimeoutError:
            logger.warning(
                "visibility_timeout brand=%s completed_queries=%d/%d",
                brand, len(all_results), len(queries[:5]),
            )
            return {
                "error": "visibility_timeout",
                "summary": (
                    f"Visibility check timed out after 45s "
                    f"(partial results for {len(all_results)}/{len(queries[:5])} queries)"
                ),
                "brand": brand,
                "keywords": keywords,
                "platforms_checked": selected_platforms,
                "results": all_results,
                "total_brand_citations": total_citations,
                "partial": True,
            }

        return {
            "brand": brand,
            "keywords": keywords,
            "platforms_checked": selected_platforms,
            "results": all_results,
            "total_brand_citations": total_citations,
            "summary": (
                f"Found {total_citations} citation(s) of '{brand}' across "
                f"{len(selected_platforms)} AI platforms for {len(queries[:5])} queries"
            ),
        }

    async def generate_article(
        self,
        target_keyword: str,
        secondary_keywords: list[str] | None = None,
        site_link_graph: SiteLinkGraph | None = None,
        tone: str = "professional",
        word_count_target: int | None = None,
    ) -> ArticleResult:
        """Generate a full SEO article.

        Args:
            target_keyword: Primary keyword to target.
            secondary_keywords: Additional keywords.
            site_link_graph: Optional SiteLinkGraph for internal linking.
            tone: Writing tone.
            word_count_target: Target word count (defaults to settings).

        Returns:
            ArticleResult with complete article content.
        """
        from .generator import generate_article

        if not self._settings.enable_geo:
            raise GeoAuditError("DISABLED", "GEO service is not enabled")

        wc = word_count_target or self._settings.article_max_word_count
        model = self._settings.article_model or self._settings.gemini_model

        return await generate_article(
            target_keyword=target_keyword,
            secondary_keywords=secondary_keywords,
            site_link_graph=site_link_graph,
            tone=tone,
            word_count_target=wc,
            gemini_api_key=self._settings.gemini_api_key.get_secret_value(),
            gemini_model=model,
        )

    @property
    def cloro_client(self) -> CloroClient:
        """Expose Cloro client for visibility checks (PR 2/3)."""
        return self._cloro_client
