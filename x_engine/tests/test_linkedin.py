"""LinkedIn pipeline tests — Apify async pattern, normalizers, ranking,
Bright Data scaffold gate. Per master plan v13 §3.4 + §7.3.

HTTP traffic mocked via respx so the suite runs offline without an
APIFY_TOKEN. The poll-loop's time.sleep is monkey-patched to a no-op so
the SUCCEEDED path doesn't waste 3s per test."""
from __future__ import annotations

import datetime as dt
import math

import httpx
import pytest
import respx

from x_engine.pipeline import linkedin
from x_engine.pipeline.db import connect


# ---------- Helpers ----------

@pytest.fixture
def with_token(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test-token")


@pytest.fixture
def fast_poll(monkeypatch):
    """Skip the 3-second poll interval in tests."""
    monkeypatch.setattr(linkedin.time, "sleep", lambda _s: None)


# ---------- _apify_token ----------

def test_apify_token_missing_raises(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    with pytest.raises(linkedin.ApifyError):
        linkedin._apify_token()


def test_apify_token_present(with_token):
    assert linkedin._apify_token() == "test-token"


# ---------- Normalizers ----------

class TestNormalizeApimaestro:
    def test_dropped_when_no_post_id(self):
        items = [{"text": "no urn here"}]
        assert linkedin._normalize_apimaestro(items, "search:foo") == []

    def test_camelcase_keys_accepted(self):
        items = [{
            "post_url": "urn:li:activity:1",
            "authorName": "Alice",
            "authorProfileUrl": "https://linkedin.com/in/alice",
            "text": "hello world",
            "likeCount": 12,
            "commentCount": 3,
            "repostCount": 1,
            "postedAt": "2026-05-07T10:00:00Z",
        }]
        out = linkedin._normalize_apimaestro(items, "search:foo")
        assert len(out) == 1
        assert out[0] == {
            "post_id": "urn:li:activity:1",
            "author_name": "Alice",
            "author_profile_url": "https://linkedin.com/in/alice",
            "post_text": "hello world",
            "reactions": 12,
            "comments": 3,
            "shares": 1,
            "posted_at": "2026-05-07T10:00:00Z",
            "source_query": "search:foo",
        }

    def test_snake_case_keys_accepted(self):
        items = [{
            "post_id": "urn:li:activity:2",
            "author_name": "Bob",
            "post_text": "snake case",
            "reactions": 5,
            "comments": 0,
            "shares": 0,
            "posted_at": "2026-05-07T10:00:00Z",
        }]
        out = linkedin._normalize_apimaestro(items, "search:foo")
        assert out[0]["post_id"] == "urn:li:activity:2"
        assert out[0]["reactions"] == 5

    def test_garbage_int_fields_coerce_to_zero(self):
        items = [{
            "post_id": "urn:li:activity:3",
            "post_text": "x",
            "likeCount": "not a number",
        }]
        out = linkedin._normalize_apimaestro(items, "src")
        assert out[0]["reactions"] == 0


class TestNormalizeHarvestapi:
    def test_profile_url_becomes_source_query(self):
        items = [{
            "urn": "urn:li:activity:99",
            "authorName": "Carol",
            "text": "from profile",
            "reactions": 50,
            "commentCount": 4,
            "postedAt": "2026-05-07T10:00:00Z",
        }]
        out = linkedin._normalize_harvestapi(
            items, "https://linkedin.com/in/carol"
        )
        assert len(out) == 1
        assert out[0]["author_profile_url"] == "https://linkedin.com/in/carol"
        assert out[0]["source_query"] == "https://linkedin.com/in/carol"
        assert out[0]["reactions"] == 50

    def test_dropped_without_urn_or_url(self):
        items = [{"authorName": "no id"}]
        assert linkedin._normalize_harvestapi(items, "x") == []


# ---------- upsert_linkedin_posts ----------

def test_upsert_linkedin_posts_pk_dedupes(isolated_db):
    items = [
        {
            "post_id": "urn:li:activity:1",
            "author_name": "A",
            "author_profile_url": "",
            "post_text": "x",
            "reactions": 1,
            "comments": 0,
            "shares": 0,
            "posted_at": "2026-05-07T10:00:00Z",
            "source_query": "search:t",
        }
    ]
    n1 = linkedin.upsert_linkedin_posts(items)
    n2 = linkedin.upsert_linkedin_posts(items)  # same PK, should ignore
    assert n1 == 1
    assert n2 == 0
    with connect(isolated_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM linkedin_posts").fetchone()[0]
    assert count == 1


# ---------- _start_run / _poll_run / _fetch_dataset (Apify async pattern) ----------

@respx.mock
def test_start_run_returns_data(with_token):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs"
    ).mock(return_value=httpx.Response(
        201, json={"data": {"id": "run-1", "status": "READY"}}
    ))
    run = linkedin._start_run(linkedin.SEARCH_ACTOR, {"keyword": "x"}, "test-token")
    assert run["id"] == "run-1"


@respx.mock
def test_poll_run_succeeded(with_token, fast_poll):
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/run-1"
    ).mock(return_value=httpx.Response(
        200,
        json={
            "data": {
                "id": "run-1",
                "status": "SUCCEEDED",
                "defaultDatasetId": "ds-1",
                "usage": {"ACTOR_COMPUTE_UNITS": 12.5},
            }
        },
    ))
    run = linkedin._poll_run(linkedin.SEARCH_ACTOR, "run-1", "test-token", max_cu=50.0)
    assert run["defaultDatasetId"] == "ds-1"


@respx.mock
def test_poll_run_aborts_on_cost_cap(with_token, fast_poll):
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/run-2"
    ).mock(return_value=httpx.Response(
        200,
        json={
            "data": {
                "id": "run-2",
                "status": "RUNNING",
                "usage": {"ACTOR_COMPUTE_UNITS": 75.0},
            }
        },
    ))
    abort_route = respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/run-2/abort"
    ).mock(return_value=httpx.Response(200, json={"data": {"status": "ABORTED"}}))
    with pytest.raises(linkedin.ApifyCostCapExceeded):
        linkedin._poll_run(linkedin.SEARCH_ACTOR, "run-2", "test-token", max_cu=50.0)
    assert abort_route.called


@respx.mock
def test_poll_run_actor_failed(with_token, fast_poll):
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/run-3"
    ).mock(return_value=httpx.Response(
        200,
        json={"data": {"id": "run-3", "status": "FAILED",
                       "usage": {"ACTOR_COMPUTE_UNITS": 5.0}}},
    ))
    with pytest.raises(linkedin.ApifyActorFailed):
        linkedin._poll_run(linkedin.SEARCH_ACTOR, "run-3", "test-token", max_cu=50.0)


@respx.mock
def test_fetch_dataset_returns_list(with_token):
    items = [{"a": 1}, {"b": 2}]
    respx.get(f"{linkedin.APIFY_BASE}/datasets/ds-1/items").mock(
        return_value=httpx.Response(200, json=items)
    )
    out = linkedin._fetch_dataset("ds-1", "test-token")
    assert out == items


# ---------- pull_linkedin_search end-to-end ----------

@respx.mock
def test_pull_linkedin_search_end_to_end(with_token, fast_poll, isolated_db):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs"
    ).mock(return_value=httpx.Response(
        201, json={"data": {"id": "run-1"}}
    ))
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.SEARCH_ACTOR}/runs/run-1"
    ).mock(return_value=httpx.Response(
        200,
        json={"data": {"id": "run-1", "status": "SUCCEEDED",
                       "defaultDatasetId": "ds-1",
                       "usage": {"ACTOR_COMPUTE_UNITS": 30.0}}},
    ))
    respx.get(f"{linkedin.APIFY_BASE}/datasets/ds-1/items").mock(
        return_value=httpx.Response(200, json=[
            {"post_id": "urn:li:activity:1", "text": "post 1",
             "likeCount": 10, "postedAt": "2026-05-07T10:00:00Z"},
            {"post_id": "urn:li:activity:2", "text": "post 2",
             "likeCount": 5, "postedAt": "2026-05-07T11:00:00Z"},
            {"text": "no urn — should drop"},  # dropped by normalizer
        ])
    )
    result = linkedin.pull_linkedin_search("ai marketing", limit=10, max_cu=50.0)
    assert result["actor"] == "apimaestro"
    assert result["fetched"] == 3
    assert result["normalized"] == 2  # one dropped
    assert result["inserted"] == 2
    assert result["compute_units"] == 30.0


# ---------- pull_linkedin_user end-to-end ----------

@respx.mock
def test_pull_linkedin_user_end_to_end(with_token, fast_poll, isolated_db):
    respx.post(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.USER_ACTOR}/runs"
    ).mock(return_value=httpx.Response(
        201, json={"data": {"id": "run-2"}}
    ))
    respx.get(
        f"{linkedin.APIFY_BASE}/acts/{linkedin.USER_ACTOR}/runs/run-2"
    ).mock(return_value=httpx.Response(
        200,
        json={"data": {"id": "run-2", "status": "SUCCEEDED",
                       "defaultDatasetId": "ds-2",
                       "usage": {"ACTOR_COMPUTE_UNITS": 8.0}}},
    ))
    respx.get(f"{linkedin.APIFY_BASE}/datasets/ds-2/items").mock(
        return_value=httpx.Response(200, json=[
            {"urn": "urn:li:activity:99", "authorName": "Carol",
             "text": "harvestapi sample", "reactions": 25,
             "commentCount": 2, "postedAt": "2026-05-07T10:00:00Z"},
        ])
    )
    result = linkedin.pull_linkedin_user(
        "https://linkedin.com/in/carol", limit=30, max_cu=200.0
    )
    assert result["actor"] == "harvestapi"
    assert result["inserted"] == 1
    with connect(isolated_db) as conn:
        row = conn.execute(
            "SELECT author_profile_url, source_query FROM linkedin_posts "
            "WHERE post_id=?",
            ("urn:li:activity:99",),
        ).fetchone()
    # Profile URL is both the author_profile_url AND the source_query
    assert row["author_profile_url"] == "https://linkedin.com/in/carol"
    assert row["source_query"] == "https://linkedin.com/in/carol"


# ---------- top_linkedin (engagement formula) ----------

def _seed_linkedin_post(db_path, *, post_id: str, reactions: int, comments: int,
                       shares: int, posted_at: str) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO linkedin_posts "
            "(post_id, author_name, author_profile_url, post_text, "
            " reactions, comments, shares, posted_at, fetched_at, source_query) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (post_id, "Author", "https://x.com/a", "body", reactions, comments,
             shares, posted_at, "2026-05-07T00:00:00+00:00", "search:t"),
        )


def test_top_linkedin_orders_by_score_desc(isolated_db):
    now = dt.datetime.now(dt.UTC)
    today_iso = now.isoformat()
    _seed_linkedin_post(isolated_db, post_id="low",
                       reactions=5, comments=1, shares=0, posted_at=today_iso)
    _seed_linkedin_post(isolated_db, post_id="high",
                       reactions=100, comments=20, shares=5, posted_at=today_iso)
    _seed_linkedin_post(isolated_db, post_id="mid",
                       reactions=50, comments=5, shares=2, posted_at=today_iso)
    rows = linkedin.top_linkedin(days=14, limit=10)
    assert [r["post_id"] for r in rows] == ["high", "mid", "low"]


def test_top_linkedin_decay_weights_recent_higher(isolated_db):
    """A 1-day-old post outranks a 14-day-old post with identical raw counts."""
    now = dt.datetime.now(dt.UTC)
    one_day = (now - dt.timedelta(days=1)).isoformat()
    fourteen_day = (now - dt.timedelta(days=14)).isoformat()
    _seed_linkedin_post(isolated_db, post_id="old",
                       reactions=100, comments=10, shares=2, posted_at=fourteen_day)
    _seed_linkedin_post(isolated_db, post_id="new",
                       reactions=100, comments=10, shares=2, posted_at=one_day)
    rows = linkedin.top_linkedin(days=30, limit=10)
    ids = [r["post_id"] for r in rows]
    assert ids[0] == "new"
    assert ids[1] == "old"
    # Sanity: scores follow the formula
    raw = 100 * 1 + 10 * 3 + 2 * 5
    expected_new = raw * math.exp(-1 / 14)
    expected_old = raw * math.exp(-14 / 14)
    assert rows[0]["resonance_score"] == pytest.approx(expected_new, rel=0.01)
    assert rows[1]["resonance_score"] == pytest.approx(expected_old, rel=0.01)


def test_top_linkedin_skips_unparseable_posted_at(isolated_db):
    _seed_linkedin_post(isolated_db, post_id="bad",
                       reactions=999, comments=999, shares=999,
                       posted_at="not-a-date")
    rows = linkedin.top_linkedin(days=14, limit=10)
    # Filtered out before scoring (cutoff comparison + parse-failure skip).
    assert all(r["post_id"] != "bad" for r in rows)


def test_top_linkedin_filters_by_days(isolated_db):
    now = dt.datetime.now(dt.UTC)
    fresh = (now - dt.timedelta(days=2)).isoformat()
    stale = (now - dt.timedelta(days=30)).isoformat()
    _seed_linkedin_post(isolated_db, post_id="fresh",
                       reactions=10, comments=1, shares=0, posted_at=fresh)
    _seed_linkedin_post(isolated_db, post_id="stale",
                       reactions=999, comments=99, shares=9, posted_at=stale)
    rows = linkedin.top_linkedin(days=14, limit=10)
    assert [r["post_id"] for r in rows] == ["fresh"]


# ---------- Bright Data scaffold ----------

def test_brightdata_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LINKEDIN_USE_BRIGHTDATA", raising=False)
    with pytest.raises(linkedin.BrightDataDisabledError):
        linkedin.pull_linkedin_brightdata("ai marketing")


def test_brightdata_disabled_without_token(monkeypatch):
    monkeypatch.setenv("LINKEDIN_USE_BRIGHTDATA", "1")
    monkeypatch.delenv("BRIGHTDATA_TOKEN", raising=False)
    with pytest.raises(linkedin.BrightDataDisabledError):
        linkedin.pull_linkedin_brightdata("ai marketing")


def test_brightdata_not_implemented_when_fully_enabled(monkeypatch):
    """Pre-positioned scaffold per Round-6 #17; live network call deferred."""
    monkeypatch.setenv("LINKEDIN_USE_BRIGHTDATA", "1")
    monkeypatch.setenv("BRIGHTDATA_TOKEN", "test-bd-token")
    with pytest.raises(NotImplementedError):
        linkedin.pull_linkedin_brightdata("ai marketing")
