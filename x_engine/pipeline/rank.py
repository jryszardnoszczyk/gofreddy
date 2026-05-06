"""Resonance scoring + dedupe for ranked feed."""
from __future__ import annotations

import math
from typing import Any

from .db import connect


def resonance_score(tweet: dict[str, Any]) -> float:
    """Engagement weighted by author baseline. Higher = more resonance.

    Formula: (likes + 2*RT + 3*replies) / sqrt(max(views, 1))
    Falls back to (likes + 2*RT + 3*replies) / sqrt(max(followers, 1000)) when views=0.
    """
    likes = int(tweet.get("likes") or 0)
    rts = int(tweet.get("retweets") or 0)
    replies = int(tweet.get("replies") or 0)
    views = int(tweet.get("views") or 0)
    followers = int(tweet.get("author_followers") or 0)

    engagement = likes + 2 * rts + 3 * replies
    if engagement == 0:
        return 0.0

    if views > 0:
        denom = math.sqrt(views)
    else:
        denom = math.sqrt(max(followers, 1000))
    return engagement / denom


def update_scores(db_path=None) -> int:
    """Compute resonance_score for every tweet in DB. Returns rows updated."""
    updated = 0
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT tweet_id, likes, retweets, replies, views, author_followers FROM tweets"
        ).fetchall()
        for row in rows:
            score = resonance_score(dict(row))
            conn.execute(
                "UPDATE tweets SET resonance_score = ? WHERE tweet_id = ?",
                (score, row["tweet_id"]),
            )
            updated += 1
    return updated


def dedupe_hashes(items: list[dict[str, Any]], existing_hashes: set[str]) -> list[dict[str, Any]]:
    """Keep only items whose dedupe_hash is not in existing_hashes."""
    seen = set(existing_hashes)
    out = []
    for item in items:
        h = item.get("dedupe_hash") or ""
        if h and h in seen:
            continue
        seen.add(h)
        out.append(item)
    return out


def top_n_ranked(n: int = 50, min_likes: int = 20, freshness_hours: int = 36, db_path=None) -> list[dict[str, Any]]:
    """Return top-N tweets by resonance, filtered by freshness + min_likes."""
    import datetime as dt

    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=freshness_hours)).isoformat()
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT tweet_id, source_url, source_handle, text, likes, retweets, replies,
                   views, author_followers, created_at, resonance_score
            FROM tweets
            WHERE created_at >= ? AND likes >= ?
            ORDER BY resonance_score DESC, likes DESC
            LIMIT ?
            """,
            (cutoff, min_likes, n),
        ).fetchall()
    return [dict(r) for r in rows]


def recent_releases(days: int = 7, limit: int = 20, db_path=None) -> list[dict[str, Any]]:
    import datetime as dt

    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT release_id, repo, name, body, url, published_at
            FROM releases
            WHERE published_at >= ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (cutoff, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def recent_rss(days: int = 7, limit: int = 30, db_path=None) -> list[dict[str, Any]]:
    import datetime as dt

    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).isoformat()
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT rss_id, source_label, title, summary, url, published_at
            FROM rss_items
            WHERE published_at >= ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (cutoff, limit),
        ).fetchall()
    return [dict(r) for r in rows]
