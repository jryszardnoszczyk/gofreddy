"""ANALYZE step: Query cited page patterns and identify content gaps.

Adapted from Freddy: Supabase replaced with asyncpg, uses Freddy's
model_router and CircuitBreaker.
"""

import asyncio
import logging
import re
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

from google import genai
from google.genai import errors, types

from ..common.circuit_breaker import CircuitBreaker
from ..common.cost_recorder import cost_recorder as _cost_recorder, extract_gemini_usage
from ..common.model_router import get_model_for_task
from ..common.sanitize import escape_braces
from .models import (
    AnalyzeResult,
    AuditFindings,
    CitedPageData,
    ContentGap,
    PageContent,
    PatternGaps,
    TopicExtractionResult,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

MIN_CITED_PAGES = 5
MAX_CITED_PAGES = 50
MAX_CONCURRENT_LLM_CALLS = 10
GAP_THRESHOLD_PCT = 50.0
CITATION_AGE_WARNING_DAYS = 30
IMPORTANCE_CRITICAL_THRESHOLD = 75.0
IMPORTANCE_IMPORTANT_THRESHOLD = 60.0
MAX_HEADING_LENGTH = 200
MAX_HEADINGS_PER_BATCH = 100

GENERIC_HEADINGS = frozenset({
    "introduction", "conclusion", "summary", "overview", "background",
    "references", "about", "contact", "about us", "contact us",
    "get started", "next steps",
})


# =============================================================================
# Heading Sanitization (Security)
# =============================================================================


def sanitize_headings(headings: list[str]) -> list[str]:
    """Sanitize H2 headings before LLM prompt inclusion."""
    sanitized = []
    for h in headings[:MAX_HEADINGS_PER_BATCH]:
        h = h[:MAX_HEADING_LENGTH]
        h = re.sub(r"<[^>]+>", "", h)
        h = re.sub(r"\b(ignore|disregard|forget|instead)\b", "", h, flags=re.IGNORECASE)
        h = " ".join(h.split())
        if h and len(h) >= 2:
            sanitized.append(h)
    return sanitized


# =============================================================================
# Pattern Gaps Calculation
# =============================================================================


def calculate_pattern_gaps(
    cited_pages: list[CitedPageData],
    user_page: PageContent,
) -> PatternGaps:
    """Calculate pattern gaps between user page and cited pages (deterministic)."""
    if not cited_pages:
        return PatternGaps()

    total = len(cited_pages)

    has_schema = sum(1 for p in cited_pages if p.schema_types)
    has_faqpage = sum(1 for p in cited_pages if "FAQPage" in p.schema_types)
    has_faq_section = sum(
        1 for p in cited_pages
        if any("faq" in h.lower() or "question" in h.lower() for h in p.h2_texts)
    )
    has_comparison_table = sum(1 for p in cited_pages if p.has_comparison_table)

    today = date.today()
    content_ages = []
    for p in cited_pages:
        content_date = p.last_modified or p.publish_date
        if content_date:
            age_days = (today - content_date).days
            if age_days >= 0:
                content_ages.append(age_days)

    cited_median_age = int(statistics.median(content_ages)) if content_ages else None

    return PatternGaps(
        schema_pct=round((has_schema / total) * 100, 1),
        faqpage_schema_pct=round((has_faqpage / total) * 100, 1),
        faq_section_pct=round((has_faq_section / total) * 100, 1),
        comparison_table_pct=round((has_comparison_table / total) * 100, 1),
        cited_median_age_days=cited_median_age,
        user_content_age_days=None,
    )


# =============================================================================
# Topic Extraction
# =============================================================================

TOPIC_EXTRACTION_PROMPT = """<instructions>
Extract distinct topics from these web page headings.
Normalize similar topics to canonical names (e.g., "Pricing Plans" and "Cost Information" both become "pricing").
Skip generic headings like "Introduction", "Conclusion", "Summary".
Return only the normalized topic names.
</instructions>

<headings>
{headings_list}
</headings>

Return JSON only with normalized topic names."""

STRUCTURE_ANALYSIS_PROMPT = """<instructions>
Identify content formats and structural patterns suggested by these page headings.
Look for indicators of: FAQ sections, comparison tables, step-by-step guides, how-to tutorials,
listicles, data tables, pros/cons lists, checklists, timelines, glossaries.
Normalize to canonical format names.
Only include formats clearly indicated by the headings.
</instructions>

<headings>
{headings_list}
</headings>

Return JSON only with normalized content format names."""

DEPTH_ANALYSIS_PROMPT = """<instructions>
Identify depth and authority indicators suggested by these page headings.
Look for indicators of: expert analysis, research data, statistics, benchmarks, case studies,
methodology breakdowns, implementation guides, best practices, common mistakes,
advanced techniques, real-world examples, tool comparisons, industry standards.
Normalize to canonical indicator names.
Only include indicators clearly suggested by the headings.
</instructions>

<headings>
{headings_list}
</headings>

Return JSON only with normalized depth indicator names."""


# Module-level circuit breaker for topic extraction
_topic_breaker = CircuitBreaker(
    failure_threshold=3,
    reset_timeout=300.0,
    name="gemini_topic_extraction",
)


@dataclass
class TopicExtractionAgent:
    """Agent for extracting topics from page headings via LLM."""

    api_key: str = field(repr=False)
    model: str = ""

    def __post_init__(self):
        if not self.model:
            self.model = get_model_for_task("gap_analysis")

    @property
    def is_available(self) -> bool:
        return _topic_breaker.allow_request()

    async def extract_topics(
        self,
        headings: list[str],
        prompt_template: str = TOPIC_EXTRACTION_PROMPT,
    ) -> TopicExtractionResult | None:
        """Extract topics from headings using LLM."""
        if not self.is_available:
            logger.warning("Circuit breaker open for topic extraction — returning empty result")
            return TopicExtractionResult(topics=(), primary_topic="unknown")

        safe_headings = sanitize_headings(headings)
        if not safe_headings:
            return TopicExtractionResult(topics=(), primary_topic="unknown")

        try:
            return await self._extract(safe_headings, prompt_template)
        except Exception as e:
            _topic_breaker.record_failure()
            logger.error(
                "Topic extraction failed",
                extra={"headings_count": len(headings), "error": str(e)},
            )
            return None

    async def _extract(
        self,
        safe_headings: list[str],
        prompt_template: str,
    ) -> TopicExtractionResult:
        """Extract topics with Gemini."""
        prompt = prompt_template.format(
            headings_list="\n".join(f"- {escape_braces(h)}" for h in safe_headings)
        )

        client = genai.Client(api_key=self.api_key)

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TopicExtractionResult,
                    ),
                ),
                timeout=30,
            )
            t_in, t_out, c = extract_gemini_usage(response, self.model)
            await _cost_recorder.record(
                "gemini", "geo_topic_extraction",
                tokens_in=t_in, tokens_out=t_out, cost_usd=c, model=self.model,
            )

            result = response.parsed
            _topic_breaker.record_success()
            return result

        except errors.APIError as e:
            if e.code == 429 or (e.code and e.code >= 500):
                _topic_breaker.record_failure()
            raise


# =============================================================================
# Content Gaps Calculation
# =============================================================================


def calculate_content_gaps(
    cited_topics: Counter[str],
    user_topics: set[str],
    total_pages: int,
    source: str | None = None,
) -> tuple[ContentGap, ...]:
    """Calculate content gaps with 50% threshold."""
    if total_pages == 0:
        return ()

    gaps = []
    for topic, count in cited_topics.most_common():
        coverage_pct = (count / total_pages) * 100

        if coverage_pct >= GAP_THRESHOLD_PCT and topic.lower() not in {
            t.lower() for t in user_topics
        }:
            if coverage_pct >= IMPORTANCE_CRITICAL_THRESHOLD:
                importance: Literal["critical", "important", "recommended"] = "critical"
            elif coverage_pct >= IMPORTANCE_IMPORTANT_THRESHOLD:
                importance = "important"
            else:
                importance = "recommended"

            gaps.append(
                ContentGap(
                    topic_name=topic,
                    coverage_pct=round(coverage_pct, 1),
                    importance=importance,
                    source=source,
                )
            )

    return tuple(gaps)


# =============================================================================
# Multi-Perspective Helpers
# =============================================================================

_IMPORTANCE_RANK = {"critical": 3, "important": 2, "recommended": 1}


def _normalize_topic(topic: str) -> str:
    return topic.lower().strip()


def _find_substring_match(key: str, existing_keys: dict[str, ContentGap]) -> str | None:
    for existing_key in existing_keys:
        if key in existing_key or existing_key in key:
            return existing_key
    return None


def reinforce_content_gaps(
    perspective_gaps: list[tuple[ContentGap, ...]],
) -> tuple[ContentGap, ...]:
    """Merge content gaps from multiple perspectives, deduplicating."""
    if not perspective_gaps:
        return ()

    seen: dict[str, ContentGap] = {}

    for gaps in perspective_gaps:
        for gap in gaps:
            key = _normalize_topic(gap.topic_name)

            if key in seen:
                existing = seen[key]
                if _IMPORTANCE_RANK.get(gap.importance, 0) > _IMPORTANCE_RANK.get(
                    existing.importance, 0
                ):
                    seen[key] = gap
                elif (
                    gap.importance == existing.importance
                    and gap.coverage_pct > existing.coverage_pct
                ):
                    seen[key] = gap
            else:
                dup_key = _find_substring_match(key, seen)
                if dup_key:
                    existing = seen[dup_key]
                    if _IMPORTANCE_RANK.get(gap.importance, 0) > _IMPORTANCE_RANK.get(
                        existing.importance, 0
                    ):
                        canonical = key if len(key) <= len(dup_key) else dup_key
                        del seen[dup_key]
                        seen[canonical] = ContentGap(
                            topic_name=gap.topic_name if len(key) <= len(dup_key) else existing.topic_name,
                            coverage_pct=max(gap.coverage_pct, existing.coverage_pct),
                            importance=gap.importance,
                            source=gap.source,
                        )
                    elif (
                        gap.importance == existing.importance
                        and gap.coverage_pct > existing.coverage_pct
                    ):
                        canonical = key if len(key) <= len(dup_key) else dup_key
                        del seen[dup_key]
                        seen[canonical] = ContentGap(
                            topic_name=gap.topic_name if len(key) <= len(dup_key) else existing.topic_name,
                            coverage_pct=gap.coverage_pct,
                            importance=gap.importance,
                            source=gap.source,
                        )
                else:
                    seen[key] = gap

    return tuple(
        sorted(
            seen.values(),
            key=lambda g: (-_IMPORTANCE_RANK.get(g.importance, 0), -g.coverage_pct),
        )
    )


async def _run_per_page_perspective(
    agent: TopicExtractionAgent,
    page_headings_list: list[list[str]],
    user_headings: list[str],
    total_pages: int,
    prompt_template: str,
    source: str,
    sem: asyncio.Semaphore,
) -> tuple[tuple[ContentGap, ...], set[str]]:
    """Run per-page topic extraction with frequency counting."""
    cited_topics: Counter[str] = Counter()

    async def _limited_extract(headings: list[str]) -> TopicExtractionResult | None:
        async with sem:
            return await agent.extract_topics(headings, prompt_template)

    tasks = [_limited_extract(h) for h in page_headings_list]
    tasks.append(_limited_extract(user_headings))
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    for page_result in all_results[:-1]:
        if isinstance(page_result, Exception) or page_result is None:
            continue
        for topic in page_result.topics:
            cited_topics[topic] += 1

    user_result = all_results[-1]
    user_topics: set[str] = set()
    if not isinstance(user_result, Exception) and user_result is not None:
        user_topics = set(user_result.topics)

    gaps = calculate_content_gaps(cited_topics, user_topics, total_pages, source=source)
    return gaps, user_topics


async def _run_aggregate_perspective(
    agent: TopicExtractionAgent,
    all_cited_headings: list[str],
    user_headings: list[str],
    prompt_template: str,
    source: str,
    sem: asyncio.Semaphore,
    *,
    page_headings_list: list[list[str]] | None = None,
    pre_extracted_cited: TopicExtractionResult | None = None,
) -> tuple[tuple[ContentGap, ...], set[str]]:
    """Run aggregate analysis perspective with frequency estimation.

    When ``page_headings_list`` is provided, estimates ``coverage_pct`` for
    each topic by counting how many cited pages' headings mention it (simple
    string matching).  This replaces the fixed 50% and preserves the
    critical (>=75%) / important (>=60%) / recommended threshold logic
    without any additional LLM calls.

    When ``pre_extracted_cited`` is provided, reuses that result instead of
    making a redundant LLM call for cited-heading extraction (deduplicates
    the gate check call).
    """

    async def _limited_extract(headings: list[str]) -> TopicExtractionResult | None:
        async with sem:
            return await agent.extract_topics(headings, prompt_template)

    # Reuse pre-extracted cited topics if available (avoids duplicate LLM call)
    if pre_extracted_cited is not None and prompt_template == TOPIC_EXTRACTION_PROMPT:
        cited_result = pre_extracted_cited
        user_result = await _limited_extract(user_headings)
    else:
        cited_result, user_result = await asyncio.gather(
            _limited_extract(all_cited_headings),
            _limited_extract(user_headings),
        )

    cited_topics = set(cited_result.topics) if cited_result else set()
    user_topics = set(user_result.topics) if user_result else set()

    user_lower = {t.lower() for t in user_topics}

    # --- Frequency estimation via string matching against per-page headings ---
    if page_headings_list and cited_topics:
        total_pages = len(page_headings_list)
        gap_list: list[ContentGap] = []
        for topic in sorted(cited_topics):
            if topic.lower() in user_lower:
                continue
            topic_lower = topic.lower()
            mention_count = sum(
                1 for page_hdgs in page_headings_list
                if any(topic_lower in h.lower() for h in page_hdgs)
            )
            coverage_pct = (mention_count / total_pages) * 100 if total_pages > 0 else 0.0
            if coverage_pct < GAP_THRESHOLD_PCT:
                continue

            if coverage_pct >= IMPORTANCE_CRITICAL_THRESHOLD:
                importance: Literal["critical", "important", "recommended"] = "critical"
            elif coverage_pct >= IMPORTANCE_IMPORTANT_THRESHOLD:
                importance = "important"
            else:
                importance = "recommended"

            gap_list.append(
                ContentGap(
                    topic_name=topic,
                    coverage_pct=round(coverage_pct, 1),
                    importance=importance,
                    source=source,
                )
            )
        gaps = tuple(gap_list)
    else:
        # Fallback: no per-page headings → fixed 50% (legacy behaviour)
        gaps = tuple(
            ContentGap(
                topic_name=topic,
                coverage_pct=50.0,
                importance="recommended",
                source=source,
            )
            for topic in sorted(cited_topics)
            if topic.lower() not in user_lower
        )

    return gaps, user_topics


# =============================================================================
# Main Orchestrator
# =============================================================================


async def analyze_gaps(
    page_content: PageContent,
    findings: AuditFindings,
    cited_pages: list[CitedPageData],
    gemini_api_key: str,
    gemini_model: str | None = None,
) -> AnalyzeResult | None:
    """Multi-perspective ANALYZE step.

    Runs 3 analysis perspectives in parallel:
    1. Topic Coverage (per-page frequency)
    2. Content Structure (aggregate)
    3. Depth & Authority (aggregate)

    Args:
        page_content: User's page from SCRAPE step
        findings: Results from DETECT step
        cited_pages: Pre-fetched cited pages (from repository, not Supabase)
        gemini_api_key: Gemini API key
        gemini_model: Optional model override
    """
    start_time = time.perf_counter()

    if len(cited_pages) < MIN_CITED_PAGES:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AnalyzeResult(
            pattern_gaps=PatternGaps(),
            content_gaps=(),
            user_topics=(),
            cited_page_count=len(cited_pages),
            insufficient_data=True,
            freshness_warning=False,
            analysis_time_ms=elapsed_ms,
        )

    cited_pages = cited_pages[:MAX_CITED_PAGES]
    pattern_gaps = calculate_pattern_gaps(cited_pages, page_content)

    today = date.today()
    all_stale = all(
        (today - p.scraped_at.date()).days > CITATION_AGE_WARNING_DAYS for p in cited_pages
    )

    agent = TopicExtractionAgent(
        api_key=gemini_api_key,
        model=gemini_model or get_model_for_task("gap_analysis"),
    )

    if not agent.is_available:
        logger.warning("Topic extraction agent unavailable (circuit open)")
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AnalyzeResult(
            pattern_gaps=pattern_gaps,
            content_gaps=(),
            user_topics=(),
            cited_page_count=len(cited_pages),
            insufficient_data=False,
            freshness_warning=all_stale,
            analysis_time_ms=elapsed_ms,
            circuit_breaker_open=True,
        )

    # Pre-filter headings
    all_cited_headings: list[str] = []
    page_headings_list: list[list[str]] = []
    for p in cited_pages:
        filtered = [h for h in p.h2_texts if h.lower().strip() not in GENERIC_HEADINGS]
        all_cited_headings.extend(filtered)
        page_headings_list.append(filtered)
    user_headings = [h for h in page_content.h2s if h.lower().strip() not in GENERIC_HEADINGS]

    # Gate check
    gate_result = await agent.extract_topics(all_cited_headings)
    if gate_result is None:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AnalyzeResult(
            pattern_gaps=pattern_gaps,
            content_gaps=(),
            user_topics=(),
            cited_page_count=len(cited_pages),
            insufficient_data=False,
            freshness_warning=all_stale,
            analysis_time_ms=elapsed_ms,
            circuit_breaker_open=True,
        )

    # Fan out 3 perspectives in parallel
    sem = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)

    p1 = _run_per_page_perspective(
        agent, page_headings_list, user_headings,
        len(cited_pages), TOPIC_EXTRACTION_PROMPT, "topic_coverage", sem,
    )
    p2 = _run_aggregate_perspective(
        agent, all_cited_headings, user_headings,
        STRUCTURE_ANALYSIS_PROMPT, "content_structure", sem,
    )
    p3 = _run_aggregate_perspective(
        agent, all_cited_headings, user_headings,
        DEPTH_ANALYSIS_PROMPT, "depth_authority", sem,
    )

    results = await asyncio.gather(p1, p2, p3, return_exceptions=True)

    all_gaps: list[tuple[ContentGap, ...]] = []
    all_user_topics: set[str] = set()
    perspective_names = ["topic_coverage", "content_structure", "depth_authority"]

    perspectives_succeeded = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning("Perspective %s failed: %s", perspective_names[i], result)
            continue
        gaps, user_topics_from_perspective = result
        all_gaps.append(gaps)
        all_user_topics.update(user_topics_from_perspective)
        perspectives_succeeded += 1

    # G7: Log when extraction failures skew analysis
    if perspectives_succeeded < len(perspective_names):
        logger.warning(
            "Extraction tracking: %d/%d perspectives succeeded for %d cited pages — "
            "gap percentages may be skewed",
            perspectives_succeeded, len(perspective_names), len(cited_pages),
        )

    content_gaps = reinforce_content_gaps(all_gaps)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return AnalyzeResult(
        pattern_gaps=pattern_gaps,
        content_gaps=content_gaps,
        user_topics=tuple(all_user_topics),
        cited_page_count=len(cited_pages),
        insufficient_data=False,
        freshness_warning=all_stale,
        analysis_time_ms=elapsed_ms,
    )
