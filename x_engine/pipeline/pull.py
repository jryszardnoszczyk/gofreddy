"""twitterapi.io + GitHub releases + RSS pullers. Writes to state.db."""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

from .db import connect, init_db

TWITTERAPI_BASE = "https://api.twitterapi.io"
GITHUB_BASE = "https://api.github.com"


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _parse_twitter_created_at(s: str) -> dt.datetime:
    """Twitter's createdAt format: 'Sun Feb 08 12:00:00 +0000 2026'."""
    try:
        return parsedate_to_datetime(s).astimezone(dt.UTC)
    except (TypeError, ValueError):
        # Fallback: try ISO format
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.UTC)


def _dedupe_hash(text: str) -> str:
    """Normalize text for dedupe — lowercase, strip whitespace, hash."""
    norm = " ".join(text.lower().split())[:200]
    return hashlib.sha1(norm.encode()).hexdigest()


def _twitterapi_get(path: str, params: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Single GET to twitterapi.io. Returns parsed JSON; raises on HTTP error."""
    url = f"{TWITTERAPI_BASE}{path}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url, params=params, headers={"X-API-Key": api_key})
        resp.raise_for_status()
        return resp.json()


def pull_user_timeline(
    username: str,
    *,
    api_key: str,
    max_tweets: int = 30,
    freshness_hours: int = 36,
) -> list[dict[str, Any]]:
    """Pull last N tweets from a user, filter to fresh ones. Excludes RTs."""
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(hours=freshness_hours)
    params = {"userName": username}
    try:
        data = _twitterapi_get("/twitter/user/last_tweets", params, api_key)
    except httpx.HTTPError as e:
        print(f"[pull] {username} failed: {e}")
        return []

    raw_tweets = (data.get("data", {}) or {}).get("tweets") or data.get("tweets") or []
    fresh: list[dict[str, Any]] = []
    for t in raw_tweets[:max_tweets]:
        text = t.get("text") or ""
        if not text or text.startswith("RT @"):
            continue
        created = _parse_twitter_created_at(t.get("createdAt", ""))
        if created < cutoff:
            continue
        fresh.append(t)
    return fresh


def upsert_tweets(tweets: list[dict[str, Any]], handle: str) -> int:
    """Insert tweets into state.db. Returns count actually inserted (new only)."""
    init_db()
    inserted = 0
    now = _now_iso()
    with connect() as conn:
        for t in tweets:
            tid = str(t.get("id") or "")
            if not tid:
                continue
            text = t.get("text") or ""
            url = t.get("url") or f"https://x.com/{handle}/status/{tid}"
            author = t.get("author") or {}
            row = {
                "tweet_id": tid,
                "source_url": url,
                "source_handle": handle,
                "text": text,
                "likes": int(t.get("likeCount") or 0),
                "retweets": int(t.get("retweetCount") or 0),
                "replies": int(t.get("replyCount") or 0),
                "views": int(t.get("viewCount") or 0),
                "author_followers": int(author.get("followers") or 0),
                "created_at": _parse_twitter_created_at(t.get("createdAt", "")).isoformat(),
                "fetched_at": now,
                "dedupe_hash": _dedupe_hash(text),
            }
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO tweets
                  (tweet_id, source_url, source_handle, text, likes, retweets,
                   replies, views, author_followers, created_at, fetched_at, dedupe_hash)
                VALUES (:tweet_id, :source_url, :source_handle, :text, :likes, :retweets,
                        :replies, :views, :author_followers, :created_at, :fetched_at, :dedupe_hash)
                """,
                row,
            )
            inserted += cur.rowcount
    return inserted


def pull_search_query(
    query: str,
    *,
    api_key: str,
    max_tweets: int = 30,
) -> list[dict[str, Any]]:
    """Run one twitterapi.io advanced_search query. Returns one page (~7-16 tweets).

    Pagination on advanced_search is broken (March 2026 platform degradation).
    Use `within_time:Nh` in the query string for freshness; `since:` is degraded.

    The query string itself supplies all filters (min_faves, lang, -is:retweet, etc.).
    """
    params = {"query": query, "queryType": "Top"}
    try:
        data = _twitterapi_get("/twitter/tweet/advanced_search", params, api_key)
    except httpx.HTTPError as e:
        print(f"[pull] search '{query[:60]}' failed: {e}")
        return []
    raw_tweets = data.get("tweets") or []
    out: list[dict[str, Any]] = []
    for t in raw_tweets[:max_tweets]:
        text = t.get("text") or ""
        if not text or text.startswith("RT @"):
            continue
        out.append(t)
    return out


def upsert_search_tweets(tweets: list[dict[str, Any]], search_label: str) -> int:
    """Insert tweets discovered via search. The 'source_handle' is the original tweet author,
    not our search label — `tweets` PK dedupes if the same tweet was already inserted via
    a creator pull.
    """
    init_db()
    inserted = 0
    now = _now_iso()
    with connect() as conn:
        for t in tweets:
            tid = str(t.get("id") or "")
            if not tid:
                continue
            author = t.get("author") or {}
            handle = author.get("userName") or ""
            text = t.get("text") or ""
            url = t.get("url") or f"https://x.com/{handle}/status/{tid}"
            row = {
                "tweet_id": tid,
                "source_url": url,
                "source_handle": handle,
                "text": text,
                "likes": int(t.get("likeCount") or 0),
                "retweets": int(t.get("retweetCount") or 0),
                "replies": int(t.get("replyCount") or 0),
                "views": int(t.get("viewCount") or 0),
                "author_followers": int(author.get("followers") or 0),
                "created_at": _parse_twitter_created_at(t.get("createdAt", "")).isoformat(),
                "fetched_at": now,
                "dedupe_hash": _dedupe_hash(text),
            }
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO tweets
                  (tweet_id, source_url, source_handle, text, likes, retweets,
                   replies, views, author_followers, created_at, fetched_at, dedupe_hash)
                VALUES (:tweet_id, :source_url, :source_handle, :text, :likes, :retweets,
                        :replies, :views, :author_followers, :created_at, :fetched_at, :dedupe_hash)
                """,
                row,
            )
            inserted += cur.rowcount
    return inserted


def pull_github_releases(repo: str, *, days: int = 7) -> list[dict[str, Any]]:
    """Pull recent releases for a repo. No auth required for public repos (60/hr unauth)."""
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    url = f"{GITHUB_BASE}/repos/{repo}/releases"
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers, params={"per_page": 10})
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        print(f"[pull] github {repo} failed: {e}")
        return []

    fresh = []
    for r in data:
        published = r.get("published_at")
        if not published:
            continue
        published_dt = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
        if published_dt < cutoff:
            continue
        fresh.append(r)
    return fresh


def upsert_releases(releases: list[dict[str, Any]], repo: str) -> int:
    init_db()
    inserted = 0
    now = _now_iso()
    with connect() as conn:
        for r in releases:
            rid = f"{repo}#{r.get('id')}"
            row = {
                "release_id": rid,
                "repo": repo,
                "name": r.get("name") or r.get("tag_name") or "",
                "body": (r.get("body") or "")[:5000],
                "url": r.get("html_url") or "",
                "published_at": r.get("published_at") or "",
                "fetched_at": now,
            }
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO releases
                  (release_id, repo, name, body, url, published_at, fetched_at)
                VALUES (:release_id, :repo, :name, :body, :url, :published_at, :fetched_at)
                """,
                row,
            )
            inserted += cur.rowcount
    return inserted


def pull_rss(feed_url: str, label: str, *, days: int = 7) -> list[dict[str, Any]]:
    """Pull RSS feed items. Uses feedparser (already in gofreddy deps)."""
    import feedparser

    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    feed = feedparser.parse(feed_url)
    fresh = []
    for entry in feed.entries[:20]:
        published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published_struct:
            continue
        published_dt = dt.datetime(*published_struct[:6], tzinfo=dt.UTC)
        if published_dt < cutoff:
            continue
        fresh.append(
            {
                "id": entry.get("id") or entry.get("link") or "",
                "title": entry.get("title") or "",
                "summary": (entry.get("summary") or entry.get("description") or "")[:2000],
                "link": entry.get("link") or "",
                "published_at": published_dt.isoformat(),
                "label": label,
            }
        )
    return fresh


def upsert_rss(items: list[dict[str, Any]]) -> int:
    init_db()
    inserted = 0
    now = _now_iso()
    with connect() as conn:
        for item in items:
            row = {
                "rss_id": item["id"],
                "source_label": item["label"],
                "title": item["title"],
                "summary": item["summary"],
                "url": item["link"],
                "published_at": item["published_at"],
                "fetched_at": now,
            }
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO rss_items
                  (rss_id, source_label, title, summary, url, published_at, fetched_at)
                VALUES (:rss_id, :source_label, :title, :summary, :url, :published_at, :fetched_at)
                """,
                row,
            )
            inserted += cur.rowcount
    return inserted


def load_sources(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def run_pull(sources_path: Path, *, twitterapi_key: str) -> dict[str, int]:
    """Top-level pull: tweets + releases + RSS. Returns counts inserted."""
    sources = load_sources(sources_path)
    limits = sources.get("limits", {})
    per_user_max = limits.get("per_user_max", 30)
    freshness_hours = limits.get("freshness_hours", 36)
    search_max_per_query = limits.get("search_max_per_query", 30)

    counts = {
        "tweets": 0, "releases": 0, "rss": 0,
        "users_succeeded": 0, "users_failed": 0,
        "search_succeeded": 0, "search_failed": 0,
    }

    for username in sources.get("x_users", []):
        try:
            tweets = pull_user_timeline(
                username,
                api_key=twitterapi_key,
                max_tweets=per_user_max,
                freshness_hours=freshness_hours,
            )
            inserted = upsert_tweets(tweets, username)
            counts["tweets"] += inserted
            counts["users_succeeded"] += 1
            print(f"[pull] @{username}: {len(tweets)} fresh, {inserted} new")
        except Exception as e:
            print(f"[pull] @{username} error: {e}")
            counts["users_failed"] += 1
        time.sleep(1.0)  # >=1k credit tier supports 3 req/sec; 1.0s is well within  # respect free-tier 1 req / 5 sec

    for sq in sources.get("search_queries", []):
        query = sq.get("query") if isinstance(sq, dict) else sq
        label = sq.get("label", query[:30]) if isinstance(sq, dict) else query[:30]
        try:
            tweets = pull_search_query(
                query, api_key=twitterapi_key, max_tweets=search_max_per_query
            )
            inserted = upsert_search_tweets(tweets, label)
            counts["tweets"] += inserted
            counts["search_succeeded"] += 1
            print(f"[pull] search[{label}]: {len(tweets)} fresh, {inserted} new")
        except Exception as e:
            print(f"[pull] search[{label}] error: {e}")
            counts["search_failed"] += 1
        time.sleep(1.0)  # >=1k credit tier supports 3 req/sec; 1.0s is well within

    for repo in sources.get("github_repos", []):
        try:
            releases = pull_github_releases(repo)
            counts["releases"] += upsert_releases(releases, repo)
            print(f"[pull] {repo}: {len(releases)} releases")
        except Exception as e:
            print(f"[pull] {repo} error: {e}")

    for feed in sources.get("rss", []):
        try:
            items = pull_rss(feed["url"], feed.get("label", "rss"))
            counts["rss"] += upsert_rss(items)
            print(f"[pull] {feed.get('label')}: {len(items)} items")
        except Exception as e:
            print(f"[pull] rss {feed.get('url')} error: {e}")

    return counts
