"""GEO Audit Pipeline Orchestrator.

Chains SCRAPE → DETECT → ANALYZE → GENERATE → FORMAT with repository-based persistence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from uuid import UUID

from ..common.cost_recorder import cost_recorder as _cost_recorder
from .analyzer import analyze_gaps
from .detector import detect_factors
from .exceptions import GeoAuditError
from .extraction import detect_comparison_table, extract_dates
from .formatter import format_audit_report
from .generator import generate_improvements
from .link_graph import SiteLinkGraph, build_site_link_graph
from .sitemap import SitemapParser
from .models import (
    AnalyzeResult,
    AuditFindings,
    CitabilityScore,
    CitedPageData,
    FormatResult,
    GenerateResult,
    InfrastructureGate,
    PageContent,
)
from .providers.cloro import CloroClient, QueryRequest
from .scraper import scrape_page

if TYPE_CHECKING:
    from .repository import PostgresGeoRepository

logger = logging.getLogger(__name__)

# Pipeline timeout
PIPELINE_TIMEOUT = 120.0  # 2 minutes

ERROR_MESSAGES = {
    "FETCH_FAILED": "Could not fetch the page. Check if the URL is accessible.",
    "BLOCKED": "URL blocked by security policy.",
    "SERVER_ERROR": "The website returned an error. Try again later.",
    "PARSE_ERROR": "Could not extract content from the page.",
    "UNAVAILABLE": "Service temporarily unavailable.",
    "TIMEOUT": "Audit timed out. Try a simpler page or try again later.",
    "INTERNAL": "An unexpected error occurred.",
}


class PipelineResult:
    """All outputs from a pipeline execution."""

    __slots__ = (
        "format_result",
        "findings",
        "analyze_result",
        "generate_result",
        "citability",
        "infra_gate",
        "site_link_graph",
    )

    def __init__(
        self,
        format_result: FormatResult,
        findings: AuditFindings,
        analyze_result: AnalyzeResult | None,
        generate_result: GenerateResult | None,
        citability: CitabilityScore | None = None,
        infra_gate: InfrastructureGate | None = None,
        site_link_graph: SiteLinkGraph | None = None,
    ):
        self.format_result = format_result
        self.findings = findings
        self.analyze_result = analyze_result
        self.generate_result = generate_result
        self.citability = citability
        self.infra_gate = infra_gate
        self.site_link_graph = site_link_graph


async def run_geo_audit(
    audit_id: UUID,
    page_url: str,
    user_id: UUID,
    repository: "PostgresGeoRepository",
    gemini_api_key: str,
    keywords: list[str] | None = None,
    gemini_model: str | None = None,
    cloro_api_key: str | None = None,
) -> PipelineResult:
    """Run complete GEO audit pipeline: SCRAPE → DETECT → ANALYZE → GENERATE → FORMAT.

    Args:
        cloro_api_key: Optional Cloro API key for AI search visibility monitoring.
            When provided, queries Cloro before ANALYZE to get real cited page data.

    Returns:
        PipelineResult with all step outputs for structured access

    Raises:
        GeoAuditError: On non-recoverable failures
    """
    await repository.update_status(audit_id, "processing")

    try:
        async with asyncio.timeout(PIPELINE_TIMEOUT):
            result = await _execute_pipeline(
                audit_id=audit_id,
                page_url=page_url,
                gemini_api_key=gemini_api_key,
                keywords=keywords,
                gemini_model=gemini_model,
                cloro_api_key=cloro_api_key,
            )

            # Persist link graph if built
            if result.site_link_graph is not None:
                try:
                    import json as _json
                    graph_data = {
                        "orphan_urls": list(result.site_link_graph.orphan_urls),
                        "hub_pages": list(result.site_link_graph.hub_pages),
                        "total_pages": result.site_link_graph.total_pages,
                        "total_links": result.site_link_graph.total_links,
                    }
                    await repository.update_link_graph(
                        audit_id, _json.dumps(graph_data),
                    )
                except Exception as e:
                    logger.warning("Failed to persist link graph: %s", e)

            # Persist completed results via repository
            await repository.update_completed(
                audit_id=audit_id,
                overall_score=_calculate_score(result.format_result),
                report_md=result.format_result.report_md,
                findings=result.format_result.severity_counts,
                optimized_content=(
                    result.generate_result.model_dump_json()
                    if result.generate_result else None
                ),
            )

            return result

    except asyncio.TimeoutError:
        logger.error("Pipeline timeout for audit %s", audit_id)
        await repository.update_status(audit_id, "error", error=ERROR_MESSAGES["TIMEOUT"])
        raise GeoAuditError("TIMEOUT", ERROR_MESSAGES["TIMEOUT"])

    except GeoAuditError as e:
        logger.error("Audit failed: %s - %s", e.code, e.message)
        await repository.update_status(audit_id, "error", error=e.message)
        raise

    except Exception as e:
        logger.exception("Unexpected error in audit %s", audit_id)
        await repository.update_status(audit_id, "error", error=ERROR_MESSAGES["INTERNAL"])
        raise GeoAuditError("INTERNAL", ERROR_MESSAGES["INTERNAL"]) from e


async def _execute_pipeline(
    audit_id: UUID,
    page_url: str,
    gemini_api_key: str,
    keywords: list[str] | None,
    gemini_model: str | None = None,
    cloro_api_key: str | None = None,
) -> PipelineResult:
    """Execute the full pipeline: SCRAPE → DETECT → ANALYZE → GENERATE → FORMAT."""

    # STEP 1: SCRAPE
    scrape_result = await scrape_page(page_url)

    if not scrape_result.success:
        raise GeoAuditError(
            scrape_result.error_code or "FETCH_FAILED",
            ERROR_MESSAGES.get(
                scrape_result.error_code or "FETCH_FAILED", ERROR_MESSAGES["FETCH_FAILED"]
            ),
        )

    page_content = scrape_result.page_content
    if page_content is None:
        raise GeoAuditError("PARSE_ERROR", ERROR_MESSAGES["PARSE_ERROR"])

    # STEP 1.5: LINK GRAPH (optional — build site link graph from sitemap)
    # Collect already-scraped URLs + PageContent for reuse in enrichment (Unit 4).
    site_link_graph: SiteLinkGraph | None = None
    link_graph_scraped: dict[str, PageContent] = {}
    try:
        parser = SitemapParser()
        sitemap_inventory = await parser.parse(page_url)
        if sitemap_inventory.entries:
            site_link_graph = await build_site_link_graph(
                sitemap_entries=sitemap_inventory.entries,
                scraper_fn=scrape_page,
                max_pages=50,
            )
            logger.info(
                "link_graph_built",
                extra={
                    "audit_id": str(audit_id),
                    "pages": site_link_graph.total_pages,
                    "links": site_link_graph.total_links,
                    "orphans": len(site_link_graph.orphan_urls),
                },
            )
            # Unit 4: Collect already-scraped page contents for enrichment reuse
            link_graph_scraped = site_link_graph.page_contents

            # Unit 6: Record link graph scrape cost
            try:
                await _cost_recorder.record(
                    "geo_scrape", "link_graph",
                    cost_usd=site_link_graph.total_pages * 0.0001,
                    metadata={
                        "audit_id": str(audit_id),
                        "pages_scraped": site_link_graph.total_pages,
                        "total_links": site_link_graph.total_links,
                    },
                )
            except Exception:
                logger.warning("Cost recording failed for audit %s", audit_id)
    except Exception as e:
        logger.warning("Link graph building failed for audit %s: %s", audit_id, e)

    # STEP 2: DETECT
    findings = await detect_factors(page_content)

    # STEP 2.1: Compute citability + infrastructure gate from findings
    citability = _calculate_citability(findings)
    infra_gate = _calculate_infra_gate(findings)

    # STEP 2.5: CLORO — query AI search visibility for cited pages
    # Unit 5: Create a single CloroClient and reuse across all Cloro calls.
    cloro_client: CloroClient | None = None
    if cloro_api_key:
        cloro_client = CloroClient(api_key=cloro_api_key)
    try:
        cited_stubs = await _fetch_cloro_citations(
            cloro_client=cloro_client,
            keywords=keywords,
            page_url=page_url,
            audit_id=audit_id,
        )

        # STEP 2.6: ENRICH — scrape cited pages for real content (h2s, schema_types)
        # Unit 4: Pass already-scraped URLs from link graph to avoid double-scraping.
        cited_pages = await _enrich_cited_pages(
            cited_stubs,
            page_url=page_url,
            timeout=30.0,
            already_scraped=link_graph_scraped,
        )

        # Unit 6: Record cited page scrape cost
        try:
            await _cost_recorder.record(
                "geo_scrape", "cited_pages",
                cost_usd=len(cited_pages) * 0.0001,
                metadata={
                    "audit_id": str(audit_id),
                    "pages_enriched": len(cited_pages),
                    "stubs_received": len(cited_stubs),
                },
            )
        except Exception:
            logger.warning("Cost recording failed for audit %s", audit_id)

        # STEP 3: ANALYZE (optional — may return None)
        analyze_result: AnalyzeResult | None = None
        try:
            analyze_result = await analyze_gaps(
                page_content=page_content,
                findings=findings,
                cited_pages=cited_pages,
                gemini_api_key=gemini_api_key,
                gemini_model=gemini_model,
            )
        except Exception as e:
            logger.warning("ANALYZE step failed for audit %s: %s", audit_id, e)

        # STEP 4: GENERATE (optional — before FORMAT so report includes generated content)
        generate_result: GenerateResult | None = None
        try:
            target_query = ", ".join(keywords) if keywords else None
            generate_result = await generate_improvements(
                page_content=page_content,
                findings=findings,
                analyze_result=analyze_result,
                gemini_api_key=gemini_api_key,
                target_query=target_query,
                gemini_model=gemini_model,
                cited_pages=cited_pages,
            )
        except Exception as e:
            logger.warning("GENERATE step failed for audit %s: %s", audit_id, e)

        # STEP 5: FORMAT (receives generate_result so report includes generated content)
        format_result = format_audit_report(
            audit_id=audit_id,
            page_content=page_content,
            findings=findings,
            analyze_result=analyze_result,
            generate_result=generate_result,
            status="complete",
        )

        return PipelineResult(
            format_result=format_result,
            findings=findings,
            analyze_result=analyze_result,
            generate_result=generate_result,
            citability=citability,
            infra_gate=infra_gate,
            site_link_graph=site_link_graph,
        )
    finally:
        # Unit 5: Always close the shared CloroClient
        if cloro_client is not None:
            await cloro_client.close()


async def _fetch_cloro_citations(
    cloro_client: CloroClient | None,
    keywords: list[str] | None,
    page_url: str,
    audit_id: UUID,
) -> list[CitedPageData]:
    """Query Cloro for AI search visibility, returning cited page data.

    Accepts an externally-managed ``CloroClient`` so the caller can reuse a
    single connection across multiple Cloro-calling functions.  The caller is
    responsible for closing the client.

    Returns empty list if no client, no keywords, or on any failure.
    """
    if not cloro_client or not keywords:
        return []

    target_query = ", ".join(keywords)

    try:
        request = QueryRequest(prompt=target_query, country="US")
        query_result = await cloro_client.query(request)

        if not query_result.has_results:
            logger.info("Cloro returned no results for audit %s", audit_id)
            return []

        # Collect unique cited URLs across all platform responses,
        # preserving which AI platform cited each URL
        seen_urls: set[str] = set()
        url_platform_counts: dict[str, dict[str, int]] = {}
        cited_pages: list[CitedPageData] = []

        for platform_name, ai_response in query_result.results.items():
            for citation in ai_response.citations:
                url = citation.url.strip()
                if not url:
                    continue
                # Track platform citations for every URL
                if url not in url_platform_counts:
                    url_platform_counts[url] = {}
                url_platform_counts[url][platform_name] = (
                    url_platform_counts[url].get(platform_name, 0) + 1
                )
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Extract domain from URL
                domain = ""
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc or ""
                except Exception:
                    pass

                cited_pages.append(
                    CitedPageData(
                        url_normalized=url,
                        domain=domain,
                        h2_texts=(),
                        schema_types=(),
                        has_comparison_table=False,
                        publish_date=None,
                        last_modified=None,
                        scraped_at=datetime.now(timezone.utc),
                        query_topic=target_query,
                    )
                )

        # Attach platform citation counts to each cited page
        cited_pages = [
            p.model_copy(update={"platform_citations": url_platform_counts.get(p.url_normalized, {})})
            for p in cited_pages
        ]

        logger.info(
            "Cloro returned %d cited pages for audit %s",
            len(cited_pages),
            audit_id,
        )
        return cited_pages

    except Exception as e:
        logger.warning("Cloro query failed for audit %s: %s", audit_id, e)
        return []


async def _enrich_cited_pages(
    stubs: list[CitedPageData],
    *,
    page_url: str,
    timeout: float = 30.0,
    max_pages: int = 20,
    already_scraped: dict[str, PageContent] | None = None,
) -> list[CitedPageData]:
    """Scrape cited page URLs, return enriched CitedPageData with real content.

    When ``already_scraped`` is provided (URL -> PageContent from link graph),
    pages that were already fetched are reused instead of re-scraped
    (Unit 4 deduplication).

    Returns only successfully-scraped pages — failed scrapes are excluded
    so they don't deflate gap percentages in calculate_pattern_gaps().
    """
    if already_scraped is None:
        already_scraped = {}

    # Pre-filter: HTTPS-only, max 2048 chars, exclude user's own page
    safe_stubs = [
        s for s in stubs[:max_pages]
        if s.url_normalized.startswith("https://")
        and len(s.url_normalized) <= 2048
        and s.url_normalized != page_url
    ]
    if not safe_stubs:
        return []

    def _enrich_from_page_content(
        stub: CitedPageData, pc: PageContent,
    ) -> CitedPageData | None:
        """Build CitedPageData from an already-scraped PageContent."""
        try:
            pub_date = None
            mod_date = None
            for obj in getattr(pc, "json_ld_objects", []) or []:
                if not pub_date and obj.get("datePublished"):
                    try:
                        from datetime import date as _date
                        pub_date = _date.fromisoformat(str(obj["datePublished"])[:10])
                    except (ValueError, TypeError):
                        pass
                if not mod_date and obj.get("dateModified"):
                    try:
                        from datetime import date as _date
                        mod_date = _date.fromisoformat(str(obj["dateModified"])[:10])
                    except (ValueError, TypeError):
                        pass

            # Reuse raw_html for comparison table detection
            from bs4 import BeautifulSoup as BS
            soup = BS(pc.raw_html, "lxml") if pc.raw_html else None
            has_table = detect_comparison_table(soup) if soup else False

            return CitedPageData(
                url_normalized=stub.url_normalized,
                domain=stub.domain,
                h2_texts=tuple(h or "" for h in pc.h2s),
                schema_types=tuple(s or "" for s in pc.schema_types),
                has_comparison_table=has_table,
                publish_date=pub_date,
                last_modified=mod_date,
                scraped_at=stub.scraped_at,
                query_topic=stub.query_topic,
                platform_citations=stub.platform_citations,
            )
        except Exception:
            logger.exception(
                "cited_page_enrich_from_cache_error",
                extra={"url": stub.url_normalized},
            )
            return None

    async def _scrape_one(stub: CitedPageData) -> CitedPageData | None:
        try:
            result = await scrape_page(stub.url_normalized)
            if not result.success or result.page_content is None:
                logger.warning(
                    "cited_page_scrape_failed",
                    extra={"url": stub.url_normalized, "error_code": result.error_code},
                )
                return None
            return _enrich_from_page_content(stub, result.page_content)
        except Exception:
            logger.exception(
                "cited_page_scrape_error",
                extra={"url": stub.url_normalized},
            )
            return None

    # Unit 4: Separate stubs into already-scraped (reuse) vs need-to-scrape
    reused: list[CitedPageData] = []
    to_scrape: list[CitedPageData] = []
    seen_urls: set[str] = set()

    for stub in safe_stubs:
        if stub.url_normalized in seen_urls:
            continue
        seen_urls.add(stub.url_normalized)

        cached_pc = already_scraped.get(stub.url_normalized)
        if cached_pc is not None:
            enriched_page = _enrich_from_page_content(stub, cached_pc)
            if enriched_page is not None:
                reused.append(enriched_page)
                continue
        to_scrape.append(stub)

    if reused:
        logger.info(
            "cited_page_reused_from_link_graph",
            extra={"reused": len(reused), "to_scrape": len(to_scrape)},
        )

    tasks = [asyncio.create_task(_scrape_one(s)) for s in to_scrape]
    enriched: list[CitedPageData] = list(reused)
    try:
        async with asyncio.timeout(timeout):
            for coro in asyncio.as_completed(tasks):
                page = await coro
                if page is not None:
                    enriched.append(page)
    except TimeoutError:
        pass  # keep what we have so far
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    logger.info(
        "cited_page_scrape_summary",
        extra={
            "scraped": len(enriched) - len(reused),
            "reused": len(reused),
            "total": len(safe_stubs),
        },
    )
    return enriched


def _calculate_score(format_result: FormatResult) -> float:
    """Calculate overall GEO score (0.0-1.0) from severity counts."""
    counts = format_result.severity_counts
    total_issues = sum(counts.values())
    if total_issues == 0:
        return 1.0

    weighted = (
        counts.get("critical", 0) * 4
        + counts.get("important", 0) * 2
        + counts.get("recommended", 0) * 1
        + counts.get("optional", 0) * 0.5
    )
    max_weighted = 60.0
    score = max(0.0, 1.0 - (weighted / max_weighted))
    return round(score, 3)


def _calculate_citability(findings: AuditFindings) -> CitabilityScore:
    """Calculate deterministic citability score from content detector outputs."""
    faq_pairs = 0
    comparison_tables = 0
    statistics_count = 0
    howto_steps = 0
    self_contained = 0
    named_entities = 0

    for f in findings.findings:
        if f.factor_id == "faq_sections" and f.detected:
            faq_pairs = f.count or 0
        elif f.factor_id == "comparison_tables" and f.detected:
            comparison_tables = f.count or 1
        elif f.factor_id == "statistics_presence":
            statistics_count = f.count or 0
        elif f.factor_id == "answer_first_intro" and f.detected:
            self_contained = 1
        elif f.factor_id == "word_count":
            named_entities = min(f.count or 0, 5000)  # cap for normalization

    text_length = named_entities
    stats_density = statistics_count / max(1, text_length / 1000) if text_length > 0 else 0.0

    # Normalize to 0-1
    signals = [
        min(faq_pairs / 7, 1.0),           # 7 FAQ pairs = perfect
        min(comparison_tables, 1.0),         # 1+ table = perfect
        min(stats_density / 5, 1.0),         # 5 stats per 1000 words = perfect
        min(howto_steps / 5, 1.0),           # 5 steps = perfect
        float(self_contained),               # binary
    ]
    overall = sum(signals) / len(signals) if signals else 0.0

    return CitabilityScore(
        faq_pairs=faq_pairs,
        comparison_tables=comparison_tables,
        statistics_density=round(stats_density, 3),
        howto_steps=howto_steps,
        self_contained_answers=self_contained,
        named_entity_matches=named_entities,
        overall=round(overall, 3),
    )


def _calculate_infra_gate(findings: AuditFindings) -> InfrastructureGate:
    """Calculate pass/fail infrastructure gate from critical factors."""
    critical_ids = {"schema_markup", "https", "title_tag"}
    failed = []

    for f in findings.findings:
        if f.factor_id in critical_ids and f.detected is False:
            failed.append(f.factor_id)

    return InfrastructureGate(
        passed=len(failed) == 0,
        failed_checks=tuple(failed),
    )
