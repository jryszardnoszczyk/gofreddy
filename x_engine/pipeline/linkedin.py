"""LinkedIn data layer — Apify-backed pulls + LinkedIn-engagement ranking.

Per master plan v13 §3.4 + §7.3:
- Two Apify actors handle LinkedIn data: `apimaestro/linkedin-posts-search-
  scraper-no-cookies` for keyword search and `harvestapi/linkedin-profile-
  posts` for per-creator pulls. Both are async (POST run-id → poll until
  SUCCEEDED → GET dataset items) and return DIFFERENT JSON shapes — each
  needs its own normalizer.
- LinkedIn-engagement scoring lives here, not in shared `rank.py`. Formula
  (Round-7 Gap B):
      score = (reactions × 1.0 + comments × 3.0 + shares × 5.0)
              × exp(-days_since_posted / 14)
- Bright Data fallback is pre-positioned per Round-6 #17: account +
  integration adapter scaffold + normalizer skeleton land at L1 but the
  command is feature-flagged off (`LINKEDIN_USE_BRIGHTDATA=1` activates).
  Joint Apify failure modes — both no-cookies actors hit by the same
  anti-scrape sweep — are the design point, not a 5-6d emergency rebuild.

Cost-caps fire `--exit-with-error` so daily pull budget is bounded:
- search default `--max-cu 50` (apimaestro typical 20-50 CU per query)
- user default `--max-cu 200` (harvestapi typical 5-15 CU per profile)
"""
from __future__ import annotations

import datetime as dt
import math
import os
import time
from typing import Any

import httpx

from .db import connect, init_db


APIFY_BASE = "https://api.apify.com/v2"
# Apify actor IDs use ~ as the user/actor separator in URLs.
SEARCH_ACTOR = "apimaestro~linkedin-posts-search-scraper-no-cookies"
USER_ACTOR = "harvestapi~linkedin-profile-posts"

# Hard ceiling on a single Apify run wait, regardless of cost cap. Two Apify
# actors with retry storms could hang for hours otherwise.
_RUN_DEADLINE_SECONDS = 600
_POLL_INTERVAL_SECONDS = 3


class ApifyError(Exception):
    """Base class for Apify-side failures."""


class ApifyCostCapExceeded(ApifyError):
    """Raised when an in-flight run's CU usage exceeds the configured cap."""


class ApifyActorFailed(ApifyError):
    """Raised when the actor terminates with a non-SUCCEEDED status."""


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _apify_token() -> str:
    t = os.environ.get("APIFY_TOKEN")
    if not t:
        raise ApifyError("APIFY_TOKEN not set")
    return t


def _start_run(actor_id: str, input_payload: dict[str, Any], token: str) -> dict[str, Any]:
    """Start an Apify actor run. Returns the run record. HTTP errors normalize
    to ApifyError so callers don't have to catch httpx exceptions separately
    (batch CLI commands rely on this for partial-failure reporting)."""
    url = f"{APIFY_BASE}/acts/{actor_id}/runs"
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, params={"token": token}, json=input_payload)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        raise ApifyError(f"start_run: HTTP error: {exc}") from exc
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict) or not data.get("id"):
        raise ApifyError(f"start_run: malformed response: {body!r}")
    return data


def _poll_run(actor_id: str, run_id: str, token: str, max_cu: float) -> dict[str, Any]:
    """Poll until SUCCEEDED. Aborts the run if CU exceeds `max_cu`."""
    url = f"{APIFY_BASE}/acts/{actor_id}/runs/{run_id}"
    deadline = time.monotonic() + _RUN_DEADLINE_SECONDS
    while time.monotonic() < deadline:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params={"token": token})
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            raise ApifyError(f"poll_run: HTTP error: {exc}") from exc
        run = body.get("data") if isinstance(body, dict) else {}
        status = run.get("status")
        cu = float(((run.get("usage") or {}).get("ACTOR_COMPUTE_UNITS")) or 0)
        if cu > max_cu:
            try:
                with httpx.Client(timeout=30.0) as client:
                    client.post(f"{url}/abort", params={"token": token})
            except httpx.HTTPError:
                # Best-effort abort; the cost-cap surfaces regardless.
                pass
            raise ApifyCostCapExceeded(
                f"actor={actor_id} run={run_id} consumed {cu} CU > cap {max_cu}; aborted"
            )
        if status == "SUCCEEDED":
            return run
        if status in {"FAILED", "ABORTED", "TIMED-OUT", "TIMED_OUT"}:
            raise ApifyActorFailed(
                f"actor={actor_id} run={run_id} terminated status={status} cu={cu}"
            )
        time.sleep(_POLL_INTERVAL_SECONDS)
    raise ApifyError(f"actor={actor_id} run={run_id} exceeded {_RUN_DEADLINE_SECONDS}s deadline")


def _fetch_dataset(dataset_id: str, token: str) -> list[dict[str, Any]]:
    """GET items from an Apify dataset. HTTP errors normalize to ApifyError."""
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items"
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(url, params={"token": token})
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        raise ApifyError(f"fetch_dataset: HTTP error: {exc}") from exc
    if not isinstance(body, list):
        raise ApifyError(f"fetch_dataset: expected list, got {type(body).__name__}")
    return body


def _coerce_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _normalize_apimaestro(items: list[dict[str, Any]], source_query: str) -> list[dict[str, Any]]:
    """Normalize `apimaestro/linkedin-posts-search-scraper-no-cookies` items.

    The actor returns a flat list of post dicts. Field names vary by version
    (camelCase or snake_case); we accept either. Discards any item without a
    URN/URL we can use as the primary key.
    """
    out: list[dict[str, Any]] = []
    for item in items:
        post_id = (
            item.get("post_id")
            or item.get("urn")
            or item.get("post_url")
            or item.get("url")
        )
        if not post_id:
            continue
        out.append(
            {
                "post_id": str(post_id),
                "author_name": item.get("author_name") or item.get("authorName") or "",
                "author_profile_url": (
                    item.get("author_profile_url") or item.get("authorProfileUrl")
                    or item.get("author_url") or ""
                ),
                "post_text": item.get("text") or item.get("post_text") or item.get("content") or "",
                "reactions": _coerce_int(
                    item.get("reactions") or item.get("likeCount")
                    or item.get("reactionsCount") or 0
                ),
                "comments": _coerce_int(
                    item.get("comments") or item.get("commentCount")
                    or item.get("commentsCount") or 0
                ),
                "shares": _coerce_int(
                    item.get("shares") or item.get("repostCount")
                    or item.get("sharesCount") or 0
                ),
                "posted_at": item.get("posted_at") or item.get("postedAt")
                    or item.get("publishedAt") or "",
                "source_query": source_query,
            }
        )
    return out


def _normalize_harvestapi(
    items: list[dict[str, Any]], source_query: str
) -> list[dict[str, Any]]:
    """Normalize `harvestapi/linkedin-profile-posts` items.

    The actor's per-creator output uses different keys than apimaestro.
    `source_query` here is the profile URL.
    """
    out: list[dict[str, Any]] = []
    for item in items:
        post_id = item.get("urn") or item.get("postUrl") or item.get("url")
        if not post_id:
            continue
        out.append(
            {
                "post_id": str(post_id),
                "author_name": item.get("authorName") or item.get("author_name") or "",
                "author_profile_url": source_query,
                "post_text": item.get("text") or item.get("postText") or "",
                "reactions": _coerce_int(
                    item.get("reactions") or item.get("reactionsCount") or 0
                ),
                "comments": _coerce_int(
                    item.get("commentCount") or item.get("comments") or 0
                ),
                "shares": _coerce_int(
                    item.get("shares") or item.get("repostsCount") or 0
                ),
                "posted_at": item.get("postedAt") or item.get("createdAt") or "",
                "source_query": source_query,
            }
        )
    return out


def upsert_linkedin_posts(items: list[dict[str, Any]]) -> int:
    """INSERT OR IGNORE on post_id PK. Returns count of new rows inserted."""
    init_db()
    inserted = 0
    now = _now_iso()
    with connect() as conn:
        for item in items:
            cur = conn.execute(
                "INSERT OR IGNORE INTO linkedin_posts "
                "(post_id, author_name, author_profile_url, post_text, "
                " reactions, comments, shares, posted_at, fetched_at, "
                " source_query) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item["post_id"], item["author_name"], item["author_profile_url"],
                    item["post_text"], item["reactions"], item["comments"],
                    item["shares"], item["posted_at"], now, item["source_query"],
                ),
            )
            if cur.rowcount:
                inserted += 1
    return inserted


def pull_linkedin_search(keyword: str, *, limit: int = 50, max_cu: float = 50.0) -> dict[str, Any]:
    """End-to-end search pull: start run → poll → fetch → normalize → persist."""
    token = _apify_token()
    run = _start_run(SEARCH_ACTOR, {"keyword": keyword, "limit": limit}, token)
    completed = _poll_run(SEARCH_ACTOR, run["id"], token, max_cu)
    items = _fetch_dataset(completed["defaultDatasetId"], token)
    normalized = _normalize_apimaestro(items, source_query=f"search:{keyword}")
    inserted = upsert_linkedin_posts(normalized)
    return {
        "actor": "apimaestro",
        "keyword": keyword,
        "fetched": len(items),
        "normalized": len(normalized),
        "inserted": inserted,
        "compute_units": float(((completed.get("usage") or {}).get("ACTOR_COMPUTE_UNITS")) or 0),
    }


def pull_linkedin_user(
    profile_url: str, *, limit: int = 30, max_cu: float = 200.0
) -> dict[str, Any]:
    """End-to-end profile pull: start run → poll → fetch → normalize → persist."""
    token = _apify_token()
    run = _start_run(USER_ACTOR, {"profileUrl": profile_url, "limit": limit}, token)
    completed = _poll_run(USER_ACTOR, run["id"], token, max_cu)
    items = _fetch_dataset(completed["defaultDatasetId"], token)
    normalized = _normalize_harvestapi(items, source_query=profile_url)
    inserted = upsert_linkedin_posts(normalized)
    return {
        "actor": "harvestapi",
        "profile_url": profile_url,
        "fetched": len(items),
        "normalized": len(normalized),
        "inserted": inserted,
        "compute_units": float(((completed.get("usage") or {}).get("ACTOR_COMPUTE_UNITS")) or 0),
    }


def top_linkedin(days: int = 14, limit: int = 50) -> list[dict[str, Any]]:
    """Rank `linkedin_posts` by LinkedIn-engagement formula (decay-weighted).

    Per master plan v13 §3.4 (Round-7 Gap B):
        score = (reactions × 1.0 + comments × 3.0 + shares × 5.0)
                × exp(-days_since_posted / 14)

    Returns top-N rows ordered by score desc. Rows with unparseable
    `posted_at` are excluded — they shouldn't be ranked.
    """
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT post_id, author_name, author_profile_url, post_text, "
            "reactions, comments, shares, posted_at "
            "FROM linkedin_posts WHERE posted_at >= ?",
            (cutoff,),
        ).fetchall()

    now = dt.datetime.now(dt.UTC)
    scored: list[dict[str, Any]] = []
    for row in rows:
        posted_raw = row["posted_at"]
        if not posted_raw:
            continue
        try:
            posted = dt.datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=dt.UTC)
        else:
            posted = posted.astimezone(dt.UTC)
        days_ago = max(0.0, (now - posted).total_seconds() / 86400)
        decay = math.exp(-days_ago / 14)
        score = (row["reactions"] * 1.0 + row["comments"] * 3.0
                 + row["shares"] * 5.0) * decay
        entry = dict(row)
        entry["resonance_score"] = round(score, 4)
        scored.append(entry)

    scored.sort(key=lambda r: r["resonance_score"], reverse=True)
    return scored[:limit]


# ----------------------------------------------------------------------------
# Bright Data fallback scaffold (Round-6 #17 pre-positioned, feature-flagged
# off via LINKEDIN_USE_BRIGHTDATA=1).
#
# Activated when both Apify actors zero in the same anti-scrape sweep (R5).
# Plan §7.6 R5: 30-min env-var flip, not a 5-6d emergency rebuild. The
# adapter shell, normalizer skeleton, and CLI command land at L1 to make
# the flip viable; the live network call is intentionally not implemented
# in v1 — JR activates per the L2-day-30 risk-fire procedure.
# ----------------------------------------------------------------------------


class BrightDataDisabledError(RuntimeError):
    """Raised when the Bright Data path is invoked without the feature flag set."""


def pull_linkedin_brightdata(keyword: str, *, limit: int = 50) -> dict[str, Any]:
    """Bright Data LinkedIn fallback. Requires:
        LINKEDIN_USE_BRIGHTDATA=1     # feature flag (off by default)
        BRIGHTDATA_TOKEN              # account API token

    Plan §7.6 R5: pre-positioned but intentionally not wired in v1. Calling
    without the flag raises BrightDataDisabledError with a pointer to the
    activation procedure.
    """
    if os.environ.get("LINKEDIN_USE_BRIGHTDATA") != "1":
        raise BrightDataDisabledError(
            "Bright Data fallback is feature-flagged off. Activate per "
            "plan §7.6 R5: set LINKEDIN_USE_BRIGHTDATA=1 + BRIGHTDATA_TOKEN, "
            "then re-run."
        )
    token = os.environ.get("BRIGHTDATA_TOKEN")
    if not token:
        raise BrightDataDisabledError("BRIGHTDATA_TOKEN not set")
    raise NotImplementedError(
        "Bright Data adapter scaffolded but not wired. Activate at "
        "L2-day-30 risk-fire-time per plan §7.6 R5; expected ~30-min "
        "implementation lift on the existing skeleton."
    )
