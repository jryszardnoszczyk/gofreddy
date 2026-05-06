"""DataForSEO API provider — thin async wrapper.

The DataForSEO SDK is synchronous (urllib3-based).
ALL calls are wrapped in asyncio.to_thread() to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ...common.cost_recorder import cost_recorder as _cost_recorder
from ..exceptions import DataForSeoError
from ..models import (
    BacklinkData,
    BacklinkSnapshot,
    DomainRankSnapshot,
    GbpHours,
    GbpResult,
    GbpSearchResult,
    HistoricalRankPoint,
    HistoricalRankResult,
    KeywordAnalysisResult,
    KeywordData,
    SerpFeature,
    SerpFeaturesResult,
    TechnicalAuditResult,
    TechnicalIssue,
)

logger = logging.getLogger(__name__)

# DataForSEO cost estimates (per-request) for cost recording
DATAFORSEO_COST_ONPAGE = 0.01
DATAFORSEO_COST_KEYWORDS = 0.05
DATAFORSEO_COST_BACKLINKS = 0.02
DATAFORSEO_COST_DOMAIN_RANK = 0.02
DATAFORSEO_COST_SERP_FEATURES = 0.0025  # serp/google/organic/live (advanced)
DATAFORSEO_COST_HISTORICAL_RANK = 0.05  # backlinks/history/live
DATAFORSEO_COST_GBP_LIVE = 0.05  # business_data/google/my_business_info/live


def _format_gbp_day(day_raw: Any) -> str | None:
    """Coerce DataForSEO's per-day hours format into a human-readable string.

    Their schema is a list of {"open": {"hour":H,"minute":M}, "close": {...}}
    or simply ``[]`` for closed-all-day. Returns ``"closed"`` for closed,
    ``None`` for missing-data, or ``"HH:MM-HH:MM"`` for open."""
    if day_raw is None:
        return None
    if not day_raw:
        return "closed"
    try:
        slots = []
        for entry in day_raw:
            o = entry.get("open", {})
            c = entry.get("close", {})
            slots.append(
                f"{o.get('hour', 0):02d}:{o.get('minute', 0):02d}-"
                f"{c.get('hour', 0):02d}:{c.get('minute', 0):02d}"
            )
        return ",".join(slots)
    except (AttributeError, TypeError):
        return None


class DataForSeoProvider:
    """Async wrapper around DataForSEO REST API.

    Uses asyncio.to_thread() since the SDK is synchronous.
    Supports sandbox mode (server_index=1) for CI/testing.
    """

    def __init__(
        self,
        login: str,
        password: str,
        *,
        sandbox: bool = False,
        timeout: float = 60.0,
    ) -> None:
        self._login = login
        self._password = password
        self._sandbox = sandbox
        self._timeout = timeout
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the SDK client (synchronous, so done in thread)."""
        if self._client is None:
            from dataforseo_client import RestClient

            self._client = RestClient(self._login, self._password)
            if self._sandbox:
                # Sandbox mode: set server_index to 1
                self._client.sandbox = True
        return self._client

    async def technical_audit(self, url: str) -> TechnicalAuditResult:
        """Run on-page SEO audit for a URL."""

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            post_data = [{"url": url, "enable_javascript_rendering": False}]
            response = client.post(
                "/v3/on_page/instant_pages", post_data
            )
            return response

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"Technical audit timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"Technical audit failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "on_page_audit", cost_usd=DATAFORSEO_COST_ONPAGE
        )

        return self._parse_technical_result(url, raw)

    async def keyword_analysis(
        self, keywords: list[str], location_code: int = 2840, language_code: str = "en"
    ) -> KeywordAnalysisResult:
        """Get keyword search volume and metrics."""

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            post_data = [
                {
                    "keywords": keywords[:100],  # API limit
                    "location_code": location_code,
                    "language_code": language_code,
                }
            ]
            response = client.post(
                "/v3/keywords_data/google_ads/search_volume/live", post_data
            )
            return response

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"Keyword analysis timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"Keyword analysis failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "keyword_analysis", cost_usd=DATAFORSEO_COST_KEYWORDS
        )

        return self._parse_keyword_result(raw, location_code, language_code)

    async def backlink_analysis(self, url: str) -> BacklinkSnapshot:
        """Get backlink profile for a URL."""

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            post_data = [{"target": url, "limit": 50, "order_by": ["rank,desc"]}]
            response = client.post("/v3/backlinks/backlinks/live", post_data)
            return response

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"Backlink analysis timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"Backlink analysis failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "backlink_analysis", cost_usd=DATAFORSEO_COST_BACKLINKS
        )

        return self._parse_backlink_result(url, raw)

    async def snapshot_domain_rank(self, domain: str) -> DomainRankSnapshot:
        """Get domain-level rank metrics via backlinks/summary endpoint."""
        from datetime import date

        def _sync_call() -> dict:
            client = self._get_client()
            post_data = [{"target": domain, "internal_list_limit": 0, "backlinks_status_type": "live"}]
            response = client.post("/v3/backlinks/summary/live", post_data)
            return response

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"Domain rank snapshot timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"Domain rank snapshot failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "domain_rank_snapshot", cost_usd=DATAFORSEO_COST_DOMAIN_RANK
        )

        return self._parse_domain_rank(domain, raw)

    # --- L2 marketing-audit additions (master plan §4.9 work item #5) -------

    async def serp_features(
        self,
        keyword: str,
        *,
        location_code: int = 2840,
        language_code: str = "en",
    ) -> SerpFeaturesResult:
        """SERP feature inventory for a keyword (answer box, PAA, snippets, etc).

        Hits ``/v3/serp/google/organic/live/advanced`` which returns the full
        SERP including non-organic items (answer_box, knowledge_graph,
        people_also_ask, featured_snippet, image_pack, local_pack, etc.).
        We surface the distinct feature types in ``features_present`` so
        downstream lenses can quickly answer "does this query trigger an AI
        Overview / People-Also-Ask / Featured Snippet?".
        """

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            post_data = [
                {
                    "keyword": keyword,
                    "location_code": location_code,
                    "language_code": language_code,
                    "depth": 100,
                }
            ]
            return client.post("/v3/serp/google/organic/live/advanced", post_data)

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"SERP features query timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"SERP features query failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "serp_features", cost_usd=DATAFORSEO_COST_SERP_FEATURES
        )

        return self._parse_serp_features(keyword, location_code, language_code, raw)

    async def historical_rank(
        self,
        target: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> HistoricalRankResult:
        """Domain-level historical rank time series.

        Hits ``/v3/backlinks/history/live`` (monthly resolution). Used by
        Findability lenses to assess organic-trajectory health (improving /
        flat / decaying) over the last 12 months by default.
        """

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            req: dict[str, Any] = {"target": target}
            if date_from:
                req["date_from"] = date_from
            if date_to:
                req["date_to"] = date_to
            return client.post("/v3/backlinks/history/live", [req])

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"Historical rank query timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"Historical rank query failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "historical_rank", cost_usd=DATAFORSEO_COST_HISTORICAL_RANK
        )

        return self._parse_historical_rank(target, date_from, date_to, raw)

    async def business_data_gbp(
        self,
        keyword: str,
        *,
        location_code: int = 2840,
        language_code: str = "en",
    ) -> GbpSearchResult:
        """Google Business Profile entries matching ``keyword`` + location.

        Hits ``/v3/business_data/google/my_business_info/live``. Returns the
        full GBP record including hours, categories, claim status, lat/lon,
        rating + count. Used by geo-bundle lenses for local-SEO completeness.
        """

        def _sync_call() -> dict[str, Any]:
            client = self._get_client()
            post_data = [
                {
                    "keyword": keyword,
                    "location_code": location_code,
                    "language_code": language_code,
                }
            ]
            return client.post(
                "/v3/business_data/google/my_business_info/live", post_data
            )

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise DataForSeoError(f"GBP query timed out after {self._timeout}s")
        except Exception as e:
            raise DataForSeoError(f"GBP query failed: {e}")

        self._check_response(raw)
        await _cost_recorder.record(
            "dataforseo", "business_data_gbp", cost_usd=DATAFORSEO_COST_GBP_LIVE
        )

        return self._parse_gbp_result(keyword, location_code, raw)

    @staticmethod
    def _parse_serp_features(
        keyword: str, location_code: int, language_code: str, raw: dict
    ) -> SerpFeaturesResult:
        tasks = raw.get("tasks", [])
        if not tasks:
            return SerpFeaturesResult(
                keyword=keyword, location_code=location_code, language_code=language_code
            )
        result_blocks = (tasks[0].get("result") or [{}])
        if not result_blocks:
            return SerpFeaturesResult(
                keyword=keyword, location_code=location_code, language_code=language_code
            )
        result = result_blocks[0]
        items_raw = result.get("items") or []
        features: list[SerpFeature] = []
        seen_types: set[str] = set()
        for item in items_raw:
            ftype = item.get("type") or "unknown"
            seen_types.add(ftype)
            features.append(SerpFeature(
                feature_type=ftype,
                rank=item.get("rank_absolute") or item.get("rank_group"),
                url=item.get("url"),
                domain=item.get("domain"),
                title=item.get("title"),
                description=item.get("description") or item.get("snippet"),
            ))
        return SerpFeaturesResult(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code,
            features_present=tuple(sorted(seen_types)),
            items=tuple(features),
            total_count=result.get("items_count") or len(features),
        )

    @staticmethod
    def _parse_historical_rank(
        target: str, date_from: str | None, date_to: str | None, raw: dict
    ) -> HistoricalRankResult:
        tasks = raw.get("tasks", [])
        if not tasks:
            return HistoricalRankResult(target=target, date_from=date_from, date_to=date_to)
        result_blocks = (tasks[0].get("result") or [{}])
        if not result_blocks:
            return HistoricalRankResult(target=target, date_from=date_from, date_to=date_to)
        result = result_blocks[0]
        items_raw = result.get("items") or []
        points: list[HistoricalRankPoint] = []
        for item in items_raw:
            # DataForSEO returns "date" (YYYY-MM-DD) per row.
            period = item.get("date") or item.get("period") or ""
            points.append(HistoricalRankPoint(
                period=period,
                rank=item.get("rank"),
                backlinks=item.get("backlinks"),
                referring_domains=item.get("referring_domains"),
            ))
        return HistoricalRankResult(
            target=target,
            points=tuple(points),
            date_from=date_from,
            date_to=date_to,
        )

    @staticmethod
    def _parse_gbp_result(keyword: str, location_code: int, raw: dict) -> GbpSearchResult:
        tasks = raw.get("tasks", [])
        if not tasks:
            return GbpSearchResult(keyword=keyword, location_code=location_code)
        result_blocks = (tasks[0].get("result") or [{}])
        if not result_blocks:
            return GbpSearchResult(keyword=keyword, location_code=location_code)
        result = result_blocks[0]
        items_raw = result.get("items") or []
        gbps: list[GbpResult] = []
        for item in items_raw:
            hours_raw = item.get("work_hours") or {}
            hours_obj = None
            if isinstance(hours_raw, dict) and hours_raw:
                wt = hours_raw.get("work_time") or {}
                hours_obj = GbpHours(
                    monday=_format_gbp_day(wt.get("monday")),
                    tuesday=_format_gbp_day(wt.get("tuesday")),
                    wednesday=_format_gbp_day(wt.get("wednesday")),
                    thursday=_format_gbp_day(wt.get("thursday")),
                    friday=_format_gbp_day(wt.get("friday")),
                    saturday=_format_gbp_day(wt.get("saturday")),
                    sunday=_format_gbp_day(wt.get("sunday")),
                )
            rating = item.get("rating") or {}
            gbps.append(GbpResult(
                name=item.get("title") or item.get("name") or "",
                place_id=item.get("place_id"),
                cid=item.get("cid"),
                address=item.get("address"),
                domain=item.get("domain"),
                phone=item.get("phone"),
                rating_value=rating.get("value"),
                rating_count=rating.get("votes_count"),
                category=item.get("category"),
                additional_categories=tuple(item.get("additional_categories") or ()),
                latitude=item.get("latitude"),
                longitude=item.get("longitude"),
                url=item.get("url"),
                is_claimed=item.get("is_claimed"),
                hours=hours_obj,
                attributes=tuple(item.get("attributes") or ()),
            ))
        return GbpSearchResult(
            keyword=keyword,
            location_code=location_code,
            items=tuple(gbps),
            total_count=result.get("items_count") or len(gbps),
        )

    # --- Original helpers below ------------------------------------------------

    @staticmethod
    def _parse_domain_rank(domain: str, raw: dict) -> DomainRankSnapshot:
        """Parse backlinks/summary response into DomainRankSnapshot."""
        from datetime import date

        tasks = raw.get("tasks", [])
        if not tasks:
            return DomainRankSnapshot(domain=domain, snapshot_date=date.today())

        result_data = (tasks[0].get("result") or [{}])[0] if tasks[0].get("result") else {}

        return DomainRankSnapshot(
            domain=domain,
            rank=result_data.get("rank"),
            backlinks_total=result_data.get("backlinks", 0) or 0,
            referring_domains=result_data.get("referring_domains", 0) or 0,
            snapshot_date=date.today(),
        )

    @staticmethod
    def _check_response(raw: dict[str, Any]) -> None:
        """Check both HTTP-level and task-level error codes."""
        status_code = raw.get("status_code", 0)
        if status_code and status_code >= 40000:
            msg = raw.get("status_message", "Unknown error")
            raise DataForSeoError(msg, status_code=status_code)

        # Check task-level errors (40xxx/50xxx)
        tasks = raw.get("tasks", [])
        for task in tasks:
            task_code = task.get("status_code", 0)
            if task_code and task_code >= 40000:
                msg = task.get("status_message", "Task error")
                raise DataForSeoError(msg, status_code=task_code)

    @staticmethod
    def _parse_technical_result(url: str, raw: dict) -> TechnicalAuditResult:
        """Parse on-page audit response."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return TechnicalAuditResult(url=url)

        result_data = (tasks[0].get("result") or [{}])[0] if tasks[0].get("result") else {}
        items = result_data.get("items", [])
        page = items[0] if items else {}
        meta = page.get("meta", {})
        checks = page.get("checks", {})

        issues: list[TechnicalIssue] = []
        # Map DataForSEO checks to issues
        issue_map = {
            "no_title": ("meta_tags", "critical", "Page has no title tag"),
            "no_description": ("meta_tags", "warning", "Page has no meta description"),
            "no_h1_tag": ("headings", "warning", "Page has no H1 tag"),
            "is_noindex": ("indexability", "critical", "Page is marked as noindex"),
            "no_content_encoding": ("performance", "info", "No content encoding (gzip/br)"),
            "is_redirect": ("indexability", "warning", "Page is a redirect"),
            "no_favicon": ("meta_tags", "info", "No favicon found"),
            "has_render_blocking_resources": ("performance", "warning", "Has render-blocking resources"),
        }
        for check_key, (cat, sev, desc) in issue_map.items():
            if checks.get(check_key):
                issues.append(TechnicalIssue(
                    category=cat, severity=sev, description=desc
                ))

        return TechnicalAuditResult(
            url=url,
            status_code=page.get("status_code"),
            title=meta.get("title"),
            description=meta.get("description"),
            h1=meta.get("htags", {}).get("h1", [None])[0] if isinstance(meta.get("htags", {}).get("h1"), list) else None,
            canonical=page.get("canonical"),
            is_indexable=not checks.get("is_noindex", False),
            issues=tuple(issues),
        )

    @staticmethod
    def _parse_keyword_result(
        raw: dict, location_code: int, language_code: str
    ) -> KeywordAnalysisResult:
        """Parse keyword search volume response."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return KeywordAnalysisResult(
                location_code=location_code, language_code=language_code
            )

        result_items = (tasks[0].get("result") or [])
        keywords: list[KeywordData] = []
        for item in result_items:
            trend_values = ()
            monthly_searches = item.get("monthly_searches")
            if isinstance(monthly_searches, list):
                trend_values = tuple(
                    m.get("search_volume", 0) or 0 for m in monthly_searches[-12:]
                )

            keywords.append(KeywordData(
                keyword=item.get("keyword", ""),
                search_volume=item.get("search_volume"),
                cpc=item.get("cpc"),
                competition=item.get("competition"),
                difficulty=item.get("keyword_difficulty"),
                trend=trend_values,
            ))

        return KeywordAnalysisResult(
            keywords=tuple(keywords),
            location_code=location_code,
            language_code=language_code,
        )

    @staticmethod
    def _parse_backlink_result(url: str, raw: dict) -> BacklinkSnapshot:
        """Parse backlink analysis response."""
        tasks = raw.get("tasks", [])
        if not tasks:
            return BacklinkSnapshot(target_url=url)

        result_data = (tasks[0].get("result") or [{}])[0] if tasks[0].get("result") else {}
        items = result_data.get("items", [])

        backlinks: list[BacklinkData] = []
        for item in items[:50]:
            backlinks.append(BacklinkData(
                source_url=item.get("url_from", ""),
                target_url=item.get("url_to", url),
                anchor=item.get("anchor"),
                domain_rank=item.get("domain_from_rank"),
                is_dofollow=item.get("dofollow", True),
            ))

        dofollow = sum(1 for b in backlinks if b.is_dofollow)

        return BacklinkSnapshot(
            target_url=url,
            total_backlinks=result_data.get("total_count", len(backlinks)),
            referring_domains=result_data.get("referring_domains", 0),
            dofollow_count=dofollow,
            nofollow_count=len(backlinks) - dofollow,
            top_backlinks=tuple(backlinks),
        )
