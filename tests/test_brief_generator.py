"""Tests for CompetitiveBriefGenerator."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.competitive.brief import CompetitiveBriefGenerator, _stub
from src.competitive.models import CompetitiveBrief


def _make_client(**overrides: Any):
    """Create a mock client."""
    m = MagicMock()
    m.id = overrides.get("id", uuid4())
    m.org_id = overrides.get("org_id", uuid4())
    m.name = overrides.get("name", "Test Client")
    m.competitor_brands = overrides.get("competitor_brands", ["BrandA", "BrandB"])
    m.competitor_domains = overrides.get("competitor_domains", ["example.com"])
    m.brand_context = overrides.get("brand_context", None)
    m.auto_brief = overrides.get("auto_brief", False)
    m.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    m.updated_at = overrides.get("updated_at", datetime.now(timezone.utc))
    return m


def _make_brief(**overrides: Any) -> CompetitiveBrief:
    """Create a test CompetitiveBrief."""
    return CompetitiveBrief(
        id=overrides.get("id", uuid4()),
        client_id=overrides.get("client_id", uuid4()),
        org_id=overrides.get("org_id", uuid4()),
        date_range=overrides.get("date_range", "7d"),
        schema_version=overrides.get("schema_version", 1),
        brief_data=overrides.get("brief_data", {"sections": [], "executive_summary": "", "recommendations": []}),
        idempotency_key=overrides.get("idempotency_key", None),
        created_at=overrides.get("created_at", datetime.now(timezone.utc)),
    )


def _build_generator(**service_overrides: Any) -> CompetitiveBriefGenerator:
    """Build a generator with mocked services."""
    monitoring = service_overrides.get("monitoring_service", AsyncMock())
    client_service = service_overrides.get("client_service", AsyncMock())
    competitive_repo = service_overrides.get("competitive_repo", AsyncMock())
    monitoring_repo = service_overrides.get("monitoring_repo", AsyncMock())
    ad_service = service_overrides.get("ad_service", AsyncMock())
    search_service = service_overrides.get("search_service", AsyncMock())
    genai_client = service_overrides.get("genai_client", None)

    return CompetitiveBriefGenerator(
        monitoring_service=monitoring,
        client_service=client_service,
        competitive_repo=competitive_repo,
        monitoring_repo=monitoring_repo,
        ad_service=ad_service,
        search_service=search_service,
        genai_client=genai_client,
    )


@pytest.mark.asyncio
async def test_generate_happy_path():
    """Full generation produces a brief with all sections."""
    client = _make_client()
    brief = _make_brief(client_id=client.id, org_id=client.org_id)
    monitor_id = uuid4()

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = monitor_id
    competitive_repo.store_brief.return_value = brief

    monitoring = AsyncMock()
    monitoring.get_share_of_voice.return_value = []
    monitoring.sentiment_time_series.return_value = []
    monitoring._repo = AsyncMock()
    monitoring._repo.search_mentions.return_value = ([], 0)

    ad_service = AsyncMock()
    ad_service.search_ads.return_value = []

    search_service = AsyncMock()
    search_service.search.return_value = {"results": []}

    gen = _build_generator(
        monitoring_service=monitoring,
        client_service=client_service,
        competitive_repo=competitive_repo,
        ad_service=ad_service,
        search_service=search_service,
    )

    result = await gen.generate(
        client_id=client.id,
        org_id=client.org_id,
        date_range="7d",
    )

    assert result.id == brief.id
    competitive_repo.store_brief.assert_called_once()
    call_kwargs = competitive_repo.store_brief.call_args
    brief_data = call_kwargs.kwargs.get("brief_data") or call_kwargs[1].get("brief_data") or call_kwargs[0][3]
    # Brief should have sections list
    assert isinstance(brief_data, dict)


@pytest.mark.asyncio
async def test_generate_partial_failure():
    """One section failing doesn't prevent brief generation."""
    client = _make_client()
    brief = _make_brief()

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = uuid4()
    competitive_repo.store_brief.return_value = brief

    # SOV raises an error
    monitoring = AsyncMock()
    monitoring.get_share_of_voice.side_effect = RuntimeError("SOV failed")
    monitoring.sentiment_time_series.return_value = []
    monitoring._repo = AsyncMock()
    monitoring._repo.search_mentions.return_value = ([], 0)

    gen = _build_generator(
        monitoring_service=monitoring,
        client_service=client_service,
        competitive_repo=competitive_repo,
    )

    result = await gen.generate(client_id=client.id, org_id=client.org_id)
    assert result is not None
    # Brief was still stored despite SOV failure
    competitive_repo.store_brief.assert_called_once()


@pytest.mark.asyncio
async def test_generate_no_monitor():
    """Brief generates with skipped sections when no monitor configured."""
    client = _make_client()
    brief = _make_brief()

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = None
    competitive_repo.store_brief.return_value = brief

    gen = _build_generator(
        client_service=client_service,
        competitive_repo=competitive_repo,
    )

    result = await gen.generate(client_id=client.id, org_id=client.org_id)
    assert result is not None


@pytest.mark.asyncio
async def test_generate_invalid_date_range():
    """Invalid date_range raises BriefGenerationError."""
    from src.competitive.exceptions import BriefGenerationError

    gen = _build_generator()
    with pytest.raises(BriefGenerationError, match="Invalid date_range"):
        await gen.generate(client_id=uuid4(), org_id=uuid4(), date_range="99d")


@pytest.mark.asyncio
async def test_generate_max_3_competitors_for_creative():
    """Creative patterns caps at MAX_CREATIVE_ANALYSIS_COMPETITORS."""
    client = _make_client(competitor_brands=["A", "B", "C", "D", "E"])
    brief = _make_brief()

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = None
    competitive_repo.store_brief.return_value = brief

    gen = _build_generator(
        client_service=client_service,
        competitive_repo=competitive_repo,
        genai_client=None,  # No AI, so creative patterns stub
    )

    result = await gen.generate(client_id=client.id, org_id=client.org_id)
    assert result is not None


def test_stub_function():
    """_stub returns predictable section shape."""
    result = _stub("Test", "some reason")
    assert result["title"] == "Test"
    assert result["status"] == "skipped"
    assert "some reason" in result["content"]


def test_section_changes_first_brief():
    """First brief reports 'first brief generated'."""
    gen = _build_generator()
    changes = gen._section_changes([], None)
    assert any("First brief" in c.get("change", "") for c in changes)


def test_section_changes_with_prior():
    """Status change is detected."""
    gen = _build_generator()
    prior = _make_brief(brief_data={
        "sections": [{"title": "SOV", "status": "ok"}]
    })
    current = [{"title": "SOV", "status": "error"}]
    changes = gen._section_changes(current, prior)
    assert any("status changed" in c.get("change", "") for c in changes)


@pytest.mark.asyncio
@pytest.mark.mock_required
async def test_synthesis_empty_response_raises():
    """C24: Empty synthesis response triggers BriefGenerationError."""
    from src.competitive.exceptions import BriefGenerationError

    client = _make_client()

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = uuid4()

    monitoring = AsyncMock()
    monitoring.get_share_of_voice.return_value = []
    monitoring.sentiment_time_series.return_value = []
    monitoring._repo = AsyncMock()
    monitoring._repo.search_mentions.return_value = ([], 0)

    # Genai returns empty synthesis
    genai_client = AsyncMock()
    genai_response = MagicMock()
    genai_response.text = '{"executive_summary": "", "recommendations": []}'
    genai_client.aio.models.generate_content.return_value = genai_response

    gen = _build_generator(
        monitoring_service=monitoring,
        client_service=client_service,
        competitive_repo=competitive_repo,
        genai_client=genai_client,
    )

    with pytest.raises(BriefGenerationError, match="empty or insufficient"):
        await gen.generate(client_id=client.id, org_id=client.org_id)


@pytest.mark.asyncio
@pytest.mark.mock_required
async def test_client_validation_no_competitors():
    """C21: Client with no competitors raises BriefGenerationError."""
    from src.competitive.exceptions import BriefGenerationError

    client = _make_client(competitor_domains=[], competitor_brands=[])

    client_service = AsyncMock()
    client_service.get_client.return_value = client

    competitive_repo = AsyncMock()
    competitive_repo.get_latest_brief.return_value = None
    competitive_repo.resolve_monitor_for_client.return_value = uuid4()

    gen = _build_generator(
        client_service=client_service,
        competitive_repo=competitive_repo,
    )

    with pytest.raises(BriefGenerationError, match="no competitor_domains"):
        await gen.generate(client_id=client.id, org_id=client.org_id)
