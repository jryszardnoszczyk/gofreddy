"""Tests for GEO detect and scrape endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.geo import router
from src.api.dependencies import get_billing_context, require_pro_geo
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

    async def mock_pro_billing():
        return billing_ctx

    app.dependency_overrides[get_billing_context] = mock_billing
    app.dependency_overrides[require_pro_geo] = mock_pro_billing
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
        """Text is truncated to 10,000 chars."""
        mock_validate.return_value = ("example.com", "93.184.216.34")
        mock_fetch.return_value = _make_fetch_result()
        pc = _make_page_content()
        pc.text = "x" * 20_000
        mock_extract.return_value = pc

        app = _make_app()
        client = TestClient(app)

        resp = client.post("/v1/geo/scrape", json={"url": "https://example.com"})
        assert resp.status_code == 200
        assert len(resp.json()["text"]) == 10_000
