"""CLI smoke tests for the LinkedIn-specific commands. Verifies wiring +
exit-code policy. Pipeline-layer behavior is covered in test_linkedin.py."""
from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from x_engine.cli import app
from x_engine.pipeline import linkedin
from x_engine.pipeline.db import connect

runner = CliRunner()


@pytest.fixture
def with_token_and_fast_poll(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test-token")
    monkeypatch.setattr(linkedin.time, "sleep", lambda _s: None)


@respx.mock
def test_pull_linkedin_search_succeeds(with_token_and_fast_poll, isolated_db):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs"
    ).mock(return_value=httpx.Response(201, json={"data": {"id": "r1"}}))
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/r1"
    ).mock(return_value=httpx.Response(
        200, json={"data": {"id": "r1", "status": "SUCCEEDED",
                            "defaultDatasetId": "ds-1",
                            "usage": {"ACTOR_COMPUTE_UNITS": 25.0}}}
    ))
    respx.get(f"{linkedin.APIFY_BASE}/datasets/ds-1/items").mock(
        return_value=httpx.Response(200, json=[
            {"post_id": "urn:li:activity:1", "text": "ai marketing wins",
             "likeCount": 10, "postedAt": "2026-05-07T10:00:00Z"},
        ])
    )
    result = runner.invoke(app, ["pull-linkedin-search", "ai marketing"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["actor"] == "apimaestro"
    assert payload["inserted"] == 1


@respx.mock
def test_pull_linkedin_search_cost_cap_exits_3(with_token_and_fast_poll, isolated_db):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs"
    ).mock(return_value=httpx.Response(201, json={"data": {"id": "r2"}}))
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/r2"
    ).mock(return_value=httpx.Response(
        200, json={"data": {"id": "r2", "status": "RUNNING",
                            "usage": {"ACTOR_COMPUTE_UNITS": 75.0}}}
    ))
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/r2/abort"
    ).mock(return_value=httpx.Response(200, json={"data": {"status": "ABORTED"}}))
    result = runner.invoke(
        app, ["pull-linkedin-search", "ai marketing", "--max-cu", "50"]
    )
    assert result.exit_code == 3, result.stdout


def test_pull_linkedin_search_missing_token_exits_2(monkeypatch, isolated_db):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    result = runner.invoke(app, ["pull-linkedin-search", "ai marketing"])
    assert result.exit_code == 2


@respx.mock
def test_pull_linkedin_user_succeeds(with_token_and_fast_poll, isolated_db):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.USER_ACTOR}/runs"
    ).mock(return_value=httpx.Response(201, json={"data": {"id": "r5"}}))
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.USER_ACTOR}/runs/r5"
    ).mock(return_value=httpx.Response(
        200, json={"data": {"id": "r5", "status": "SUCCEEDED",
                            "defaultDatasetId": "ds-5",
                            "usage": {"ACTOR_COMPUTE_UNITS": 10.0}}}
    ))
    respx.get(f"{linkedin.APIFY_BASE}/datasets/ds-5/items").mock(
        return_value=httpx.Response(200, json=[
            {"urn": "urn:li:activity:7", "authorName": "Carol",
             "text": "post", "reactions": 30,
             "postedAt": "2026-05-07T10:00:00Z"},
        ])
    )
    result = runner.invoke(
        app, ["pull-linkedin-user", "https://linkedin.com/in/carol"]
    )
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["actor"] == "harvestapi"


def test_pull_linkedin_brightdata_disabled_by_default_exits_2(monkeypatch, isolated_db):
    monkeypatch.delenv("LINKEDIN_USE_BRIGHTDATA", raising=False)
    result = runner.invoke(app, ["pull-linkedin-brightdata", "x"])
    assert result.exit_code == 2
    assert "disabled" in (result.stdout + (result.stderr or "")).lower()


def test_top_linkedin_smoke(isolated_db):
    """Empty table → empty list, exit 0."""
    result = runner.invoke(app, ["top-linkedin"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_top_linkedin_returns_seeded_rows(isolated_db):
    with connect(isolated_db) as conn:
        conn.execute(
            "INSERT INTO linkedin_posts (post_id, author_name, "
            "author_profile_url, post_text, reactions, comments, shares, "
            "posted_at, fetched_at, source_query) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("urn:li:activity:42", "A", "u", "body", 10, 1, 0,
             "2026-05-07T10:00:00+00:00", "2026-05-07T11:00:00+00:00",
             "search:t"),
        )
    result = runner.invoke(app, ["top-linkedin"])
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["post_id"] == "urn:li:activity:42"
    assert "resonance_score" in payload[0]
