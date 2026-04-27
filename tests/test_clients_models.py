"""Tests for src.clients.models.Client."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.clients.models import Client


def _example_client(**overrides: object) -> Client:
    defaults: dict[str, object] = {
        "name": "Acme Corp",
        "slug": "acme-corp",
        "domain": "acme.com",
        "created_at": datetime(2026, 4, 27, 12, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return Client(**defaults)  # type: ignore[arg-type]


def test_minimum_fields_loads():
    client = _example_client()
    assert client.name == "Acme Corp"
    assert client.slug == "acme-corp"
    assert client.domain == "acme.com"
    assert client.enrichments == {}
    assert client.fit_signals == {}


def test_json_roundtrip_preserves_data():
    original = _example_client(
        enrichments={"audit_id": "abc-123", "score": 0.82},
        fit_signals={"icp_match": True, "industry": "saas"},
    )

    payload = original.model_dump_json()
    restored = Client.model_validate_json(payload)

    assert restored == original
    assert restored.enrichments["score"] == 0.82
    assert restored.fit_signals["icp_match"] is True


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        Client(slug="x", domain="x.com", created_at=datetime.now(tz=timezone.utc))  # type: ignore[call-arg]


def test_enrichments_default_empty_dict_is_independent_per_instance():
    a = _example_client()
    b = _example_client(slug="other", domain="other.com")
    a.enrichments["key"] = "value"
    assert b.enrichments == {}
