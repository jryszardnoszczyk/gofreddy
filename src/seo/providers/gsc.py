"""Google Search Console API provider — lightweight search analytics client.

Uses google-auth + google-api-python-client with service account auth.
Provides search analytics data (position, impressions, clicks, CTR) per page.

Env var: GSC_SERVICE_ACCOUNT_PATH — path to the service account JSON key file.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Cost is zero — GSC API is free.
GSC_COST_PER_QUERY = 0.0


class PageSearchMetrics(BaseModel):
    """Search analytics metrics for a single page."""

    model_config = ConfigDict(frozen=True)

    page: str = Field(..., description="Page URL")
    clicks: float = Field(default=0.0, ge=0)
    impressions: float = Field(default=0.0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0, le=1.0, description="Click-through rate 0-1")
    position: float = Field(default=0.0, ge=0.0, description="Average position")


class SearchAnalyticsResult(BaseModel):
    """Result from search analytics query."""

    model_config = ConfigDict(frozen=True)

    site_url: str
    start_date: str
    end_date: str
    rows: list[PageSearchMetrics] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)


class GSCError(Exception):
    """Google Search Console API error."""
    pass


@dataclass
class GSCClient:
    """Google Search Console search analytics client.

    Auth: service account JSON key file, path from GSC_SERVICE_ACCOUNT_PATH env var.

    Usage::

        client = GSCClient.from_env()
        result = await client.get_search_analytics(
            site_url="https://example.com",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )
    """

    service_account_path: str = field(repr=False)
    _service: Any = field(default=None, repr=False, init=False)

    @classmethod
    def from_env(cls) -> GSCClient:
        """Create client from GSC_SERVICE_ACCOUNT_PATH env var."""
        path = os.environ.get("GSC_SERVICE_ACCOUNT_PATH", "")
        if not path:
            raise GSCError("GSC_SERVICE_ACCOUNT_PATH environment variable not set")
        if not os.path.isfile(path):
            raise GSCError(f"Service account file not found: {path}")
        return cls(service_account_path=path)

    def _get_service(self) -> Any:
        """Lazy-initialize the Search Console service (synchronous)."""
        if self._service is not None:
            return self._service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as e:
            raise GSCError(
                "google-auth and google-api-python-client are required. "
                "Install with: pip install google-auth google-api-python-client"
            ) from e

        scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path, scopes=scopes
            )
            self._service = build("searchconsole", "v1", credentials=credentials)
        except Exception as e:
            raise GSCError(f"Failed to initialize GSC service: {e}") from e

        return self._service

    async def get_search_analytics(
        self,
        site_url: str,
        start_date: date,
        end_date: date,
        *,
        pages: list[str] | None = None,
        row_limit: int = 1000,
    ) -> SearchAnalyticsResult:
        """Query search analytics for a site, optionally filtered by pages.

        Args:
            site_url: Verified site property URL (e.g. "https://example.com" or "sc-domain:example.com")
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            pages: Optional list of page URLs to filter by
            row_limit: Max rows to return (default 1000, GSC max 25000)

        Returns:
            SearchAnalyticsResult with per-page metrics
        """
        body: dict[str, Any] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["page"],
            "rowLimit": min(row_limit, 25000),
        }

        if pages:
            # Use dimension filter to restrict to specific pages
            filters = []
            for page_url in pages:
                filters.append({
                    "dimension": "page",
                    "operator": "equals",
                    "expression": page_url,
                })
            # GSC API: when multiple filters on same dimension, use OR group
            if len(filters) == 1:
                body["dimensionFilterGroups"] = [{"filters": filters}]
            else:
                # For multiple pages, we need separate filter groups combined with OR
                # GSC doesn't support OR within a group, so we use regex
                escaped = [_escape_regex(p) for p in pages]
                body["dimensionFilterGroups"] = [{
                    "filters": [{
                        "dimension": "page",
                        "operator": "includingRegex",
                        "expression": "|".join(escaped),
                    }]
                }]

        def _sync_query() -> dict[str, Any]:
            service = self._get_service()
            request = service.searchanalytics().query(
                siteUrl=site_url, body=body
            )
            return request.execute()

        try:
            raw = await asyncio.to_thread(_sync_query)
        except GSCError:
            raise
        except Exception as e:
            raise GSCError(f"Search analytics query failed: {e}") from e

        return self._parse_response(site_url, start_date, end_date, raw)

    @staticmethod
    def _parse_response(
        site_url: str,
        start_date: date,
        end_date: date,
        raw: dict[str, Any],
    ) -> SearchAnalyticsResult:
        """Parse GSC search analytics response."""
        rows_data = raw.get("rows", [])
        rows = []
        for row in rows_data:
            keys = row.get("keys", [])
            if not keys:
                continue
            page_url = keys[0]
            rows.append(PageSearchMetrics(
                page=page_url,
                clicks=row.get("clicks", 0.0),
                impressions=row.get("impressions", 0.0),
                ctr=row.get("ctr", 0.0),
                position=row.get("position", 0.0),
            ))

        return SearchAnalyticsResult(
            site_url=site_url,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            rows=rows,
            row_count=len(rows),
        )


def _escape_regex(url: str) -> str:
    """Escape special regex characters in a URL for GSC regex filter."""
    special = r"\.+*?^${}()|[]\\"
    escaped = []
    for char in url:
        if char in special:
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)
