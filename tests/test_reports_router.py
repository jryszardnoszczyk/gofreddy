"""Tests for reports router (PDF download)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.competitive.exceptions import BriefNotFoundError
from src.competitive.models import CompetitiveBrief


def _make_app(competitive_repo=None, current_user_id=None) -> FastAPI:
    """Create a test FastAPI app with reports router."""
    from src.api.routers.reports import router, _get_competitive_repo
    from src.api.dependencies import get_current_user_id

    app = FastAPI()

    # Override the competitive repo dependency
    if competitive_repo is not None:
        app.state.competitive_repo = competitive_repo

    if current_user_id:
        async def mock_user_id():
            return current_user_id
        app.dependency_overrides[get_current_user_id] = mock_user_id

    app.include_router(router, prefix="/v1")
    return app


def _make_brief(**overrides) -> CompetitiveBrief:
    return CompetitiveBrief(
        id=overrides.get("id", uuid4()),
        client_id=overrides.get("client_id", uuid4()),
        org_id=overrides.get("org_id", uuid4()),
        date_range="7d",
        schema_version=1,
        brief_data=overrides.get("brief_data", {
            "client_name": "TestCo",
            "sections": [],
            "executive_summary": "Test",
            "recommendations": [],
        }),
        idempotency_key=None,
        created_at=datetime.now(timezone.utc),
    )


def test_download_pdf_not_found():
    """404 when brief not found."""
    user_id = uuid4()
    repo = AsyncMock()
    repo.get_brief_with_ownership.side_effect = BriefNotFoundError("not found")

    app = _make_app(competitive_repo=repo, current_user_id=user_id)
    client = TestClient(app)

    resp = client.get(f"/v1/reports/{uuid4()}/pdf")
    assert resp.status_code == 404


def test_download_pdf_service_unavailable():
    """503 when competitive repo not configured."""
    app = _make_app(competitive_repo=None, current_user_id=uuid4())
    client = TestClient(app)

    resp = client.get(f"/v1/reports/{uuid4()}/pdf")
    assert resp.status_code == 503


@patch("src.competitive.pdf.render_brief_pdf")
@patch("src.competitive.markdown.render_brief_markdown")
def test_download_pdf_success(mock_md, mock_pdf):
    """Successful PDF download returns correct content type."""
    user_id = uuid4()
    brief = _make_brief(org_id=user_id)

    repo = AsyncMock()
    repo.get_brief_with_ownership.return_value = brief

    mock_md.return_value = "# Test Brief"
    mock_pdf.return_value = b"%PDF-1.4 test content"

    app = _make_app(competitive_repo=repo, current_user_id=user_id)
    client = TestClient(app)

    resp = client.get(f"/v1/reports/{brief.id}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "content-disposition" in resp.headers
    assert b"%PDF" in resp.content
