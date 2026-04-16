"""Competitive brief generator — assembles multi-section intelligence reports."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, TYPE_CHECKING
from uuid import UUID

from cachetools import TTLCache

from ..common.gemini_models import GEMINI_FLASH
from ..common.sanitize import escape_braces
from .config import CompetitiveSettings
from .exceptions import BriefGenerationError
from .intelligence.partnerships import PartnershipDetector
from .models import CompetitiveBrief

if TYPE_CHECKING:
    from ..clients.models import Client
    from ..clients.service import ClientService
    from ..monitoring.repository import PostgresMonitoringRepository
    from ..monitoring.service import MonitoringService
    from ..search.service import SearchService
    from .repository import PostgresCompetitiveRepository
    from .service import CompetitiveAdService

logger = logging.getLogger(__name__)

# Synthesis prompt — the highest-leverage target for autoresearch optimization.
# The production evolve loop may modify THIS constant to improve brief quality.
# See the active archive variant under autoresearch/archive/current/ for the protocol.
SYNTHESIS_PROMPT_TEMPLATE = (
    "You are a competitive intelligence analyst for {client_name}. "
    "Focus area: {focus}. "
    "Based on these section results:\n"
    "{section_summaries}\n\n"
    "Provide:\n1. Executive summary (1-2 paragraphs)\n"
    "2. 3-5 actionable recommendations\n\n"
    'Format as JSON: {{"executive_summary": "...", "recommendations": ["..."]}}'
)

_VALID_DATE_RANGES = {"7d", "14d", "30d"}
_DATE_RANGE_DAYS = {"7d": 7, "14d": 14, "30d": 30}

SECTION_TITLES = [
    "Share of Voice",
    "Sentiment Analysis",
    "Competitor Ads",
    "Competitor Content",
    "Creative Patterns",
    "Partnerships",
]


def _stub(title: str, reason: str, status: str = "skipped") -> dict[str, str]:
    return {"title": title, "content": f"Data unavailable — {reason}.", "status": status}


class CompetitiveBriefGenerator:
    """Generates multi-section competitive intelligence briefs."""

    DEADLINE_SECONDS = 160
    MAX_CREATIVE_ANALYSIS_COMPETITORS = 3
    MAX_AD_CREDITS_PER_BRIEF = 200

    def __init__(
        self,
        monitoring_service: MonitoringService,
        client_service: ClientService,
        competitive_repo: PostgresCompetitiveRepository,
        monitoring_repo: PostgresMonitoringRepository,
        ad_service: CompetitiveAdService | None,
        search_service: SearchService | None,
        genai_client: Any | None,
        settings: CompetitiveSettings | None = None,
    ) -> None:
        self._monitoring_service = monitoring_service
        self._client_service = client_service
        self._competitive_repo = competitive_repo
        self._monitoring_repo = monitoring_repo
        self._ad_service = ad_service
        self._search_service = search_service
        self._genai_client = genai_client
        self._settings = settings or CompetitiveSettings()
        self._content_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=100, ttl=1800)

    async def generate(
        self,
        client_id: UUID,
        org_id: UUID,
        date_range: str = "7d",
        focus: str = "volume",
        ad_data: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> CompetitiveBrief:
        """Generate a competitive brief with all sections."""
        if date_range not in _VALID_DATE_RANGES:
            raise BriefGenerationError(f"Invalid date_range: {date_range}")

        deadline = time.monotonic() + self.DEADLINE_SECONDS

        client = await self._client_service.get_client(client_id, org_id)

        # C21: Validate client has competitor config
        if not client.competitor_domains and not client.competitor_brands:
            raise BriefGenerationError(
                "Client has no competitor_domains or competitor_brands configured"
            )
        prior_brief = await self._competitive_repo.get_latest_brief(client_id)
        monitor_id = await self._competitive_repo.resolve_monitor_for_client(client_id)

        sections, pre_fetched_ads = await self._gather_sections(
            client, monitor_id, org_id, date_range, deadline, ad_data,
        )

        # Delta comparison
        changes = self._section_changes(sections, prior_brief)

        # C2: Minimum section gate — if >2 sections skipped/error, don't synthesize
        failed_sections = sum(1 for s in sections if s.get("status") in ("error", "skipped"))
        synthesis_status = "ok"
        if failed_sections > 2:
            logger.warning(
                "brief_insufficient_data: %d/%d sections failed/skipped",
                failed_sections, len(sections),
            )
            synthesis_status = "insufficient_data"

        # Synthesize executive summary + recommendations
        exec_summary = ""
        recommendations: list[str] = []
        if synthesis_status == "ok" and time.monotonic() < deadline and self._genai_client:
            try:
                exec_summary, recommendations = await self._synthesize(sections, client, focus)
            except Exception:
                logger.warning("brief_synthesis_failed", exc_info=True)

        # C14: Empty brief gate — only when synthesis was attempted
        if self._genai_client and synthesis_status == "ok" and (not exec_summary or len(exec_summary) < 50):
            raise BriefGenerationError(
                f"Synthesis produced empty or insufficient executive summary "
                f"({len(exec_summary)} chars, {failed_sections} sections failed)"
            )

        brief_data: dict[str, Any] = {
            "sections": sections,
            "executive_summary": exec_summary,
            "recommendations": recommendations,
            "changes": changes,
            "date_range": date_range,
            "focus": focus,
            "client_name": client.name,
        }

        # Store brief
        brief = await self._competitive_repo.store_brief(
            client_id=client_id,
            org_id=org_id,
            date_range=date_range,
            brief_data=brief_data,
            idempotency_key=idempotency_key,
            schema_version=1,
        )

        return brief

    async def _gather_sections(
        self,
        client: Any,
        monitor_id: Any,
        org_id: UUID,
        date_range: str,
        deadline: float,
        ad_data: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
        """Shared section gathering: pre-fetch ads, run all sections concurrently.

        Returns (sections, pre_fetched_ads) for use by both generate() and deep pipeline.
        """
        pre_fetched_ads = ad_data
        if pre_fetched_ads is None and self._ad_service and client.competitor_domains:
            try:
                domains = client.competitor_domains[:self.MAX_CREATIVE_ANALYSIS_COMPETITORS]
                budget_per = max(1, self.MAX_AD_CREDITS_PER_BRIEF // len(domains))
                fetch_tasks = [
                    self._ad_service.search_ads(d, limit=budget_per) for d in domains
                ]
                fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
                pre_fetched_ads = []
                for r in fetch_results:
                    if isinstance(r, list):
                        pre_fetched_ads.extend(r)
            except Exception:
                logger.warning("ad_prefetch_failed", exc_info=True)

        # Vision enrichment: analyze ad creative images if available (#39)
        if pre_fetched_ads and self._genai_client and self._settings.enable_vision_enrichment:
            try:
                from .vision import CreativeVisionAnalyzer
                analyzer = CreativeVisionAnalyzer(self._genai_client)
                pre_fetched_ads = await analyzer.enrich_ads(pre_fetched_ads)
            except Exception:
                logger.warning("vision_enrichment_failed", exc_info=True)

        section_coros = [
            self._section_sov(client, monitor_id, org_id, date_range, deadline),
            self._section_sentiment(client, monitor_id, org_id, date_range, deadline),
            self._section_competitor_ads(client, pre_fetched_ads, deadline),
            self._section_competitor_content(client, deadline),
            self._section_creative_patterns(client, deadline, ads_data=pre_fetched_ads),
            self._section_partnerships(client, org_id, deadline),
        ]

        raw_sections = await asyncio.gather(*section_coros, return_exceptions=True)

        sections: list[dict[str, Any]] = []
        for i, result in enumerate(raw_sections):
            if isinstance(result, BaseException):
                logger.warning(
                    "brief_section_failed: section=%s error=%s: %s",
                    SECTION_TITLES[i], type(result).__name__, str(result)[:500],
                    exc_info=result,
                )
                sections.append(_stub(SECTION_TITLES[i], "generation failed", "error"))
            elif isinstance(result, dict):
                sections.append(result)
            else:
                sections.append(_stub(SECTION_TITLES[i], "unexpected result type", "error"))

        return sections, pre_fetched_ads

    async def _section_sov(
        self,
        client: Client,
        monitor_id: UUID | None,
        org_id: UUID,
        date_range: str,
        deadline: float,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Share of Voice", "deadline exceeded")
        if monitor_id is None:
            return _stub("Share of Voice", "no monitor configured")

        window_days = _DATE_RANGE_DAYS.get(date_range, 7)
        entries = await self._monitoring_service.get_share_of_voice(
            monitor_id, org_id, window_days=window_days,
        )
        rows = [
            {"brand": e.brand, "mention_count": e.mention_count,
             "percentage": e.percentage, "sentiment_avg": e.sentiment_avg}
            for e in entries
        ]
        return {"title": "Share of Voice", "content": rows, "status": "ok"}

    async def _section_sentiment(
        self,
        client: Client,
        monitor_id: UUID | None,
        org_id: UUID,
        date_range: str,
        deadline: float,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Sentiment Analysis", "deadline exceeded")
        if monitor_id is None:
            return _stub("Sentiment Analysis", "no monitor configured")

        buckets = await self._monitoring_service.sentiment_time_series(
            monitor_id, org_id, window=date_range,
        )
        rows = [
            {"period": b.period_start.isoformat(), "avg_sentiment": b.avg_sentiment,
             "mention_count": b.mention_count, "positive": b.positive_count,
             "negative": b.negative_count, "neutral": b.neutral_count}
            for b in buckets
        ]
        return {"title": "Sentiment Analysis", "content": rows, "status": "ok"}

    async def _section_competitor_ads(
        self,
        client: Client,
        pre_fetched_ads: list[dict[str, Any]] | None,
        deadline: float,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Competitor Ads", "deadline exceeded")

        if pre_fetched_ads is not None:
            return {"title": "Competitor Ads", "content": pre_fetched_ads, "status": "ok"}

        if not self._ad_service or not client.competitor_domains:
            return _stub("Competitor Ads", "no ad service or domains configured")

        all_ads: list[dict[str, Any]] = []
        domains_to_query = client.competitor_domains
        # C6: Log when caps trigger
        if len(domains_to_query) > self.MAX_CREATIVE_ANALYSIS_COMPETITORS:
            logger.info(
                "ad_cap_triggered: MAX_CREATIVE_ANALYSIS_COMPETITORS=%d, domains=%d — truncating",
                self.MAX_CREATIVE_ANALYSIS_COMPETITORS, len(domains_to_query),
            )
            domains_to_query = domains_to_query[:self.MAX_CREATIVE_ANALYSIS_COMPETITORS]
        budget_per_domain = max(1, self.MAX_AD_CREDITS_PER_BRIEF // len(domains_to_query))
        for domain in domains_to_query:
            if time.monotonic() > deadline:
                break
            try:
                ads = await self._ad_service.search_ads(domain, limit=budget_per_domain)
                all_ads.extend(ads)
            except Exception:
                logger.warning("ad_search_failed: domain=%s", domain)
        return {"title": "Competitor Ads", "content": all_ads, "status": "ok"}

    async def _section_competitor_content(
        self,
        client: Client,
        deadline: float,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Competitor Content", "deadline exceeded")

        if not self._search_service or not client.competitor_brands:
            return _stub("Competitor Content", "no search service or brands configured")

        all_content: list[dict[str, Any]] = []
        for brand in client.competitor_brands[:5]:  # Cap at 5 brands
            if time.monotonic() > deadline:
                break
            cached = self._content_cache.get(brand)
            if cached is not None:
                all_content.extend(cached.get("results", [])[:10])
                continue
            try:
                results = await self._search_service.search(query=brand)
                self._content_cache[brand] = results
                items = results.get("results", [])
                all_content.extend(items[:10])  # Top 10 per brand
            except Exception:
                logger.warning("content_search_failed: brand=%s", brand)
        return {"title": "Competitor Content", "content": all_content, "status": "ok"}

    async def _section_creative_patterns(
        self,
        client: Client,
        deadline: float,
        ads_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Creative Patterns", "deadline exceeded")

        if not self._genai_client or not client.competitor_brands:
            return _stub("Creative Patterns", "no AI service or brands configured")

        # No ad data = no creative patterns analysis (prevents hallucination)
        if not ads_data:
            return _stub("Creative Patterns", "no ad data available for creative analysis")

        brands = client.competitor_brands[:self.MAX_CREATIVE_ANALYSIS_COMPETITORS]

        # Build prompt with actual ad data to prevent hallucination (#22)
        ads_context = ""
        if ads_data:
            # Summarize ad creative data for the prompt
            ad_summaries = []
            for ad in ads_data[:30]:  # Cap at 30 ads for context
                parts = []
                if ad.get("headline"):
                    parts.append(f"headline: {ad['headline'][:100]}")
                if ad.get("body_text"):
                    parts.append(f"copy: {ad['body_text'][:150]}")
                if ad.get("cta_text"):
                    parts.append(f"CTA: {ad['cta_text']}")
                if ad.get("display_format"):
                    parts.append(f"format: {ad['display_format']}")
                if ad.get("platform"):
                    parts.append(f"platform: {ad['platform']}")
                if parts:
                    ad_summaries.append(" | ".join(parts))
            if ad_summaries:
                ads_context = (
                    "\n\nActual ad creative data from these competitors:\n"
                    + "\n".join(f"- {s}" for s in ad_summaries)
                )

        prompt = (
            f"Analyze the competitive creative patterns for these brands: {', '.join(brands)}. "
            f"Based ONLY on the provided ad data below, identify common hooks, CTAs, visual styles, "
            f"and content formats. Provide 3-5 actionable observations. "
            f"Do NOT fabricate or assume creative details not present in the data."
            f"{ads_context}"
        )
        if not ads_data:
            prompt += "\n\nNote: No ad creative data available. State this limitation clearly and analyze only what can be inferred from brand positioning."

        try:
            response = await self._genai_client.aio.models.generate_content(
                model=GEMINI_FLASH,
                contents=prompt,
            )
            text = response.text or "No patterns identified."
            return {"title": "Creative Patterns", "content": text, "status": "ok"}
        except Exception:
            logger.warning("creative_patterns_failed", exc_info=True)
            return _stub("Creative Patterns", "analysis failed", "error")

    async def _section_partnerships(
        self,
        client: Client,
        org_id: UUID,
        deadline: float,
    ) -> dict[str, Any]:
        if time.monotonic() > deadline:
            return _stub("Partnerships", "deadline exceeded")

        detector = PartnershipDetector(
            monitoring_repo=self._monitoring_repo,
            competitive_repo=self._competitive_repo,
        )
        alerts = await detector.detect_new_partnerships(
            client.id, client.competitor_brands, org_id,
        )
        rows = [
            {"brand": a.brand, "creator": a.creator, "platform": a.platform,
             "mention_count": a.mention_count, "is_new": a.is_new,
             "is_escalation": a.is_escalation}
            for a in alerts
        ]
        return {"title": "Partnerships", "content": rows, "status": "ok"}

    def _section_changes(
        self,
        current_sections: list[dict[str, Any]],
        prior_brief: CompetitiveBrief | None,
    ) -> list[dict[str, str]]:
        """Compare current sections vs prior brief for delta highlights."""
        if prior_brief is None:
            return [{"change": "First brief generated for this client."}]

        changes: list[dict[str, str]] = []
        prior_sections = prior_brief.brief_data.get("sections", [])
        for i, section in enumerate(current_sections):
            title = section.get("title", f"Section {i}")
            if i >= len(prior_sections):
                changes.append({"change": f"New section: {title}"})
                continue
            prior = prior_sections[i]
            if section.get("status") != prior.get("status"):
                changes.append({
                    "change": f"{title}: status changed from {prior.get('status')} to {section.get('status')}"
                })
        if not changes:
            changes.append({"change": "No significant changes from prior brief."})
        return changes

    async def _synthesize(
        self,
        sections: list[dict[str, Any]],
        client: Client,
        focus: str,
    ) -> tuple[str, list[str]]:
        """Generate executive summary and recommendations via Gemini."""
        import json as _json

        section_summaries = []
        for s in sections:
            title = s.get("title", "")
            status = s.get("status", "")
            if status == "ok":
                content = s.get("content", "")
                if isinstance(content, list):
                    # C1: Pass real data (top 10 items), not just count
                    top_items = content[:10]
                    serialized = _json.dumps(top_items, default=str)[:3000]
                    section_summaries.append(f"{title}: {escape_braces(serialized)}")
                else:
                    # C1: Pass first 3000 chars, not 200
                    section_summaries.append(f"{title}: {escape_braces(str(content)[:3000])}")
            else:
                section_summaries.append(f"{title}: {status}")

        prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
            client_name=escape_braces(client.name),
            focus=escape_braces(focus),
            section_summaries="\n".join(f"- {escape_braces(s)}" for s in section_summaries),
        )

        import json

        response = await self._genai_client.aio.models.generate_content(
            model=GEMINI_FLASH,
            contents=prompt,
        )
        text = response.text or "{}"
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
            return data.get("executive_summary", ""), data.get("recommendations", [])
        except json.JSONDecodeError:
            return text, []


# ─── Tiered Brief Pipeline (#40) ──────────────────────────────────────────


DEEP_SYNTHESIS_PROMPT = (
    "You are a senior competitive intelligence analyst for {client_name}. "
    "Focus area: {focus}.\n\n"
    "You have detailed per-competitor analyses and section data below. "
    "Produce a comprehensive competitive intelligence brief with:\n"
    "1. Executive summary (2-3 paragraphs) with strategic narrative arc\n"
    "2. Named taxonomies and archetypes across competitors\n"
    "3. Share of Observed [Platform] Ad Volume breakdown with confidence tags\n"
    "4. Competitive positioning based on observed data\n"
    "5. Format vacuums with counterfactuals\n"
    "6. Known unknowns\n"
    "7. 3-5 differential recommendations with timeframes, data references, "
    "'could be wrong if...' qualifiers, and competitive response models\n"
    "8. Monitoring triggers with specific thresholds\n\n"
    "Section data:\n{section_summaries}\n\n"
    'Format as JSON: {{"executive_summary": "...", "recommendations": ["..."], '
    '"taxonomies": ["..."], "known_unknowns": ["..."]}}'
)


class CompetitiveBriefPipeline:
    """Tiered competitive brief pipeline.

    Wraps CompetitiveBriefGenerator with depth control:
    - depth="snapshot": Fast 30-second synthesis (delegates to generator)
    - depth="deep": Per-competitor analysis, taxonomy building, verification (~10 min)
    """

    def __init__(self, generator: CompetitiveBriefGenerator) -> None:
        self._generator = generator

    async def generate(
        self,
        client_id: UUID,
        org_id: UUID,
        *,
        depth: str = "snapshot",
        date_range: str = "7d",
        focus: str = "volume",
        ad_data: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> CompetitiveBrief:
        """Generate brief at specified depth."""
        if depth == "snapshot":
            return await self._generator.generate(
                client_id=client_id,
                org_id=org_id,
                date_range=date_range,
                focus=focus,
                ad_data=ad_data,
                idempotency_key=idempotency_key,
            )
        elif depth == "deep":
            return await self._generate_deep(
                client_id=client_id,
                org_id=org_id,
                date_range=date_range,
                focus=focus,
                ad_data=ad_data,
                idempotency_key=idempotency_key,
            )
        else:
            raise BriefGenerationError(f"Invalid depth: {depth}. Use 'snapshot' or 'deep'.")

    async def _generate_deep(
        self,
        client_id: UUID,
        org_id: UUID,
        date_range: str,
        focus: str,
        ad_data: list[dict[str, Any]] | None,
        idempotency_key: str | None,
    ) -> CompetitiveBrief:
        """Deep brief generation with per-competitor analysis and verification."""
        deadline = time.monotonic() + 600  # 10-minute deadline for deep briefs
        gen = self._generator

        client = await gen._client_service.get_client(client_id, org_id)
        if not client.competitor_domains and not client.competitor_brands:
            raise BriefGenerationError(
                "Client has no competitor_domains or competitor_brands configured"
            )

        prior_brief = await gen._competitive_repo.get_latest_brief(client_id)
        monitor_id = await gen._competitive_repo.resolve_monitor_for_client(client_id)

        # Use shared section gathering (no private attribute duplication)
        sections, _ = await gen._gather_sections(
            client, monitor_id, org_id, date_range, deadline, ad_data,
        )

        changes = gen._section_changes(sections, prior_brief)

        # Deep synthesis with improved prompt
        exec_summary = ""
        recommendations: list[str] = []
        if gen._genai_client and time.monotonic() < deadline:
            try:
                exec_summary, recommendations = await self._deep_synthesize(
                    sections, client, focus,
                )
            except Exception:
                logger.warning("deep_brief_synthesis_failed", exc_info=True)
                # Fall back to standard synthesis
                try:
                    exec_summary, recommendations = await gen._synthesize(
                        sections, client, focus,
                    )
                except Exception:
                    logger.warning("deep_brief_fallback_synthesis_failed", exc_info=True)

        brief_data: dict[str, Any] = {
            "sections": sections,
            "executive_summary": exec_summary,
            "recommendations": recommendations,
            "changes": changes,
            "date_range": date_range,
            "focus": focus,
            "client_name": client.name,
            "depth": "deep",
        }

        brief = await gen._competitive_repo.store_brief(
            client_id=client_id,
            org_id=org_id,
            date_range=date_range,
            brief_data=brief_data,
            idempotency_key=idempotency_key,
            schema_version=1,
        )

        return brief

    async def _deep_synthesize(
        self,
        sections: list[dict[str, Any]],
        client: Any,
        focus: str,
    ) -> tuple[str, list[str]]:
        """Generate deep synthesis with improved prompt."""
        import json as _json

        section_summaries = []
        for s in sections:
            title = s.get("title", "")
            status = s.get("status", "")
            if status == "ok":
                content = s.get("content", "")
                if isinstance(content, list):
                    serialized = _json.dumps(content[:20], default=str)[:5000]
                    section_summaries.append(f"{title}: {escape_braces(serialized)}")
                else:
                    section_summaries.append(f"{title}: {escape_braces(str(content)[:5000])}")
            else:
                section_summaries.append(f"{title}: {status}")

        prompt = DEEP_SYNTHESIS_PROMPT.format(
            client_name=escape_braces(client.name),
            focus=escape_braces(focus),
            section_summaries="\n".join(f"- {escape_braces(s)}" for s in section_summaries),
        )

        import json
        response = await self._generator._genai_client.aio.models.generate_content(
            model=GEMINI_FLASH,
            contents=prompt,
        )
        text = response.text or "{}"
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
            return data.get("executive_summary", ""), data.get("recommendations", [])
        except json.JSONDecodeError:
            return text, []
