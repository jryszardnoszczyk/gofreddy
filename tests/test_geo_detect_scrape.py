"""Tests for GEO detect and scrape endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.geo import router
from src.api.dependencies import get_billing_context, get_current_user_id
from src.billing.models import BillingContext


def _make_billing_context():
    """Create a mock billing context."""
    ctx = AsyncMock(spec=BillingContext)
    ctx.user = AsyncMock()
    ctx.user.id = uuid4()
    return ctx


def _make_app(geo_service=None, billing_ctx=None) -> FastAPI:
    """Create a test FastAPI app with geo router."""
    app = FastAPI()

    if geo_service is not None:
        app.state.geo_service = geo_service

    if billing_ctx is None:
        billing_ctx = _make_billing_context()

    async def mock_billing():
        return billing_ctx

    async def mock_user_id():
        return billing_ctx.user.id if billing_ctx else uuid4()

    # require_pro_geo was replaced by RequireTier(Tier.PRO, ...). Current
    # routes use get_current_user_id directly — override that instead so
    # tests don't 401 from missing JWT (cleanup 2026-05-15).
    app.dependency_overrides[get_billing_context] = mock_billing
    app.dependency_overrides[get_current_user_id] = mock_user_id
    app.include_router(router, prefix="/v1")
    return app


def _make_page_content():
    """Create a mock PageContent."""
    pc = MagicMock()
    pc.url = "https://example.com"
    pc.final_url = "https://example.com"
    pc.title = "Example"
    pc.h1 = "Welcome"
    pc.h2s = ["About", "Contact"]
    pc.meta_description = "An example site"
    pc.text = "Hello world " * 100
    pc.word_count = 200
    pc.schema_types = ["Organization"]
    pc.status_code = 200
    pc.raw_html = "<html><body>Hello</body></html>"
    return pc


def _make_fetch_result():
    """Create a mock FetchResult."""
    fr = MagicMock()
    fr.content = "<html><body>Hello</body></html>"
    fr.final_url = "https://example.com"
    fr.js_rendered = False
    fr.status_code = 200
    return fr


def _make_findings():
    """Create mock AuditFindings."""
    findings = MagicMock()
    finding = MagicMock()
    finding.factor_id = "schema_markup"
    finding.detected = True
    finding.details = "Found structured data"
    finding.count = 3
    finding.evidence = ["Organization", "WebPage"]
    findings.findings = [finding]
    return findings


class TestDetectEndpoint:

    @patch("src.geo.detector.detect_factors")
    @patch("src.geo.extraction.extract_page_content")
    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_detect_success(self, mock_validate, mock_fetch, mock_extract, mock_detect):
        """POST /v1/geo/detect returns detection results."""
        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_fetch.return_value = _make_fetch_result()
        mock_extract.return_value = _make_page_content()
        mock_detect.return_value = _make_findings()

        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/detect", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://example.com"
        assert "geo_infrastructure" in data
        assert "seo_technical" in data
        assert "schema_markup" in data["geo_infrastructure"]

    def test_detect_rejects_http(self):
        """422 when URL is not https."""
        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/detect", json={"url": "http://example.com"})
        assert resp.status_code == 422

    def test_detect_rejects_no_url(self):
        """422 when URL is missing."""
        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/detect", json={})
        assert resp.status_code == 422


class TestScrapeEndpoint:

    @patch("src.geo.extraction.extract_page_content")
    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_scrape_success(self, mock_validate, mock_fetch, mock_extract):
        """POST /v1/geo/scrape returns page content."""
        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_fetch.return_value = _make_fetch_result()
        mock_extract.return_value = _make_page_content()

        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/scrape", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://example.com"
        assert data["title"] == "Example"
        assert data["h1"] == "Welcome"
        assert data["word_count"] == 200
        assert data["status_code"] == 200

    def test_scrape_rejects_http(self):
        """422 when URL is not https."""
        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/scrape", json={"url": "http://example.com"})
        assert resp.status_code == 422

    @patch("src.geo.extraction.extract_page_content")
    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_scrape_text_truncated(self, mock_validate, mock_fetch, mock_extract):
        """Text is truncated by the route's response builder (current cap
        is 100K — was 10K when this test was first written; route bumped at
        some point and the test wasn't updated)."""
        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_fetch.return_value = _make_fetch_result()
        pc = _make_page_content()
        pc.text = "x" * 200_000  # 2x the cap so we can verify truncation fires
        mock_extract.return_value = pc

        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/scrape", json={"url": "https://example.com"})
        assert resp.status_code == 200
        assert len(resp.json()["text"]) == 100_000


# Task #100: upstream httpx errors map to 502/504, not unhandled ExceptionGroups.


class TestSafeFetchUpstreamErrors:

    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_detect_upstream_404_returns_502_not_500(self, mock_validate, mock_fetch):
        import httpx
        from unittest.mock import MagicMock

        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_fetch.side_effect = httpx.HTTPStatusError("404", request=MagicMock(), response=mock_response)

        client = TestClient(_make_app())
        resp = client.post("/v1/geo/detect", json={"url": "https://example.com/missing"})
        assert resp.status_code == 502
        body = resp.json()
        assert body["detail"]["code"] == "upstream_error"
        assert "404" in body["detail"]["message"]

    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_scrape_upstream_403_returns_502_not_500(self, mock_validate, mock_fetch):
        import httpx
        from unittest.mock import MagicMock

        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_fetch.side_effect = httpx.HTTPStatusError("403", request=MagicMock(), response=mock_response)

        client = TestClient(_make_app())
        resp = client.post("/v1/geo/scrape", json={"url": "https://canva.com"})
        assert resp.status_code == 502
        assert resp.json()["detail"]["code"] == "upstream_error"

    @patch("src.geo.fetcher.fetch_page_for_audit")
    @patch("src.common.url_validation.resolve_and_validate")
    def test_scrape_upstream_timeout_returns_504(self, mock_validate, mock_fetch):
        import httpx

        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_fetch.side_effect = httpx.TimeoutException("upstream took too long")

        client = TestClient(_make_app())
        resp = client.post("/v1/geo/scrape", json={"url": "https://slow-site.example"})
        assert resp.status_code == 504
        assert resp.json()["detail"]["code"] == "upstream_unreachable"
