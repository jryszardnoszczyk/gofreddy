"""Tests for GEO service — service tests with mocked Cloro client."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from src.geo.config import GeoSettings
from src.geo.exceptions import GeoAuditError
from src.geo.models import FormatResult
from src.geo.orchestrator import PipelineResult
from src.geo.service import GeoAuditResult, GeoService


@pytest.mark.db
class TestGeoService:
    """Service-level tests with real DB, mocked external providers."""

    @pytest.fixture
    def settings(self):
        """GEO settings with test API keys."""
        return GeoSettings(
            enable_geo=True,
            cloro_api_key="test-cloro-key",
            gemini_api_key="test-gemini-key",
        )

    @pytest.fixture
    async def service(self, pool, settings):
        """Create GeoService with test pool."""
        from src.geo.repository import PostgresGeoRepository

        repository = PostgresGeoRepository(pool)
        return GeoService(repository=repository, settings=settings)

    @pytest.mark.asyncio
    async def test_service_disabled(self, service):
        """Service raises when disabled."""
        service._settings = GeoSettings(
            enable_geo=False,
            cloro_api_key="test",
            gemini_api_key="test",
        )
        with pytest.raises(GeoAuditError) as exc_info:
            await service.run_audit("https://example.com", uuid4())
        assert exc_info.value.code == "DISABLED"

    @pytest.mark.asyncio
    async def test_get_nonexistent_audit(self, service):
        """Get nonexistent audit returns None."""
        result = await service.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_audits_empty(self, service):
        """List audits for user with no audits."""
        result = await service.list_audits(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_cloro_client_accessible(self, service):
        """Cloro client is accessible via property."""
        assert service.cloro_client is not None
        assert service.cloro_client.is_available is True

    @pytest.mark.asyncio
    @patch("src.geo.service.run_geo_audit")
    async def test_run_audit_creates_record(self, mock_run, service, pool):
        """run_audit creates a pending record and invokes pipeline."""
        format_result = FormatResult(
            report_md="# Test Report\n\n" + "x" * 100,
            severity_counts={"critical": 0, "important": 1, "recommended": 0, "optional": 0},
            word_count=50,
        )
        mock_run.return_value = PipelineResult(
            format_result=format_result,
            findings=None,
            analyze_result=None,
            generate_result=None,
        )

        user_id = uuid4()
        result = await service.run_audit(
            url="https://example.com/test",
            user_id=user_id,
            keywords=["test"],
        )

        assert isinstance(result, GeoAuditResult)
        assert result.report.report_md.startswith("# Test Report")
        assert result.findings is None  # Mocked pipeline returned None
        assert result.analysis is None
        assert result.generated is None

        # Verify record was created in DB
        audit = await service.get_by_id(result.audit_id)
        assert audit is not None
        assert audit["url"] == "https://example.com/test"
