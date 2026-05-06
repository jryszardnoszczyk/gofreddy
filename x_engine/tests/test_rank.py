"""Rank tests — resonance scoring + dedupe + DB queries."""
from __future__ import annotations

import datetime as dt

import pytest

from x_engine.pipeline import rank
from x_engine.pipeline.db import connect


class TestResonance:
    def test_zero_engagement_zero_score(self):
        tweet = {"likes": 0, "retweets": 0, "replies": 0, "views": 100, "author_followers": 1000}
        assert rank.resonance_score(tweet) == 0.0

    def test_high_engagement_low_views(self):
        # 100 likes on 200 views = strong signal
        tweet = {"likes": 100, "retweets": 0, "replies": 0, "views": 200, "author_followers": 1000}
        score = rank.resonance_score(tweet)
        # 100 / sqrt(200) ≈ 7.07
        assert 6 < score < 8

    def test_replies_weighted_3x(self):
        # 10 replies × 3 = 30 numerator vs 10 likes × 1 = 10 numerator
        a = {"likes": 0, "retweets": 0, "replies": 10, "views": 100, "author_followers": 1000}
        b = {"likes": 10, "retweets": 0, "replies": 0, "views": 100, "author_followers": 1000}
        assert rank.resonance_score(a) > rank.resonance_score(b)

    def test_no_views_falls_back_to_followers(self):
        tweet = {"likes": 50, "retweets": 5, "replies": 2, "views": 0, "author_followers": 10000}
        score = rank.resonance_score(tweet)
        # (50 + 10 + 6) / sqrt(10000) = 66/100 = 0.66
        assert 0.5 < score < 0.8

    def test_no_views_no_followers_uses_baseline(self):
        tweet = {"likes": 50, "retweets": 0, "replies": 0, "views": 0, "author_followers": 0}
        score = rank.resonance_score(tweet)
        # baseline floor 1000 → 50/sqrt(1000) ≈ 1.58
        assert 1.0 < score < 2.5


class TestDedupe:
    def test_drops_existing_hashes(self):
        items = [
            {"dedupe_hash": "a", "text": "a"},
            {"dedupe_hash": "b", "text": "b"},
            {"dedupe_hash": "a", "text": "a"},  # dup
            {"dedupe_hash": "c", "text": "c"},
        ]
        result = rank.dedupe_hashes(items, existing_hashes=set())
        assert len(result) == 3  # a, b, c (one a)

    def test_pre_seeded_hashes_filtered(self):
        items = [{"dedupe_hash": "a", "text": "a"}, {"dedupe_hash": "b", "text": "b"}]
        result = rank.dedupe_hashes(items, existing_hashes={"a"})
        assert len(result) == 1
        assert result[0]["dedupe_hash"] == "b"


class TestUpdateScores:
    def test_scores_updated(self, isolated_db):
        with connect(isolated_db) as conn:
            conn.execute(
                """INSERT INTO tweets
                (tweet_id, source_url, source_handle, text, likes, retweets, replies, views,
                 author_followers, created_at, fetched_at, dedupe_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("t1", "u", "h", "txt", 100, 10, 5, 1000, 5000, "2026-05-06T10:00:00+00:00",
                 "2026-05-06T11:00:00+00:00", "h1"),
            )

        n = rank.update_scores(db_path=isolated_db)
        assert n == 1

        with connect(isolated_db) as conn:
            row = conn.execute("SELECT resonance_score FROM tweets WHERE tweet_id='t1'").fetchone()
        # (100 + 20 + 15) / sqrt(1000) ≈ 4.27
        assert 4 < row["resonance_score"] < 5


class TestTopNRanked:
    def test_returns_top_by_score(self, isolated_db):
        now = dt.datetime.now(dt.UTC)
        recent = (now - dt.timedelta(hours=1)).isoformat()
        with connect(isolated_db) as conn:
            for i, score in enumerate([0.5, 5.0, 2.0, 1.0]):
                conn.execute(
                    """INSERT INTO tweets
                    (tweet_id, source_url, source_handle, text, likes, retweets, replies,
                     views, author_followers, created_at, fetched_at, dedupe_hash, resonance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f"t{i}", "u", "h", "t", 30, 0, 0, 100, 1000, recent, recent, f"h{i}", score),
                )

        top = rank.top_n_ranked(n=2, min_likes=20, freshness_hours=24, db_path=isolated_db)
        assert len(top) == 2
        assert top[0]["resonance_score"] == 5.0  # highest first
        assert top[1]["resonance_score"] == 2.0

    def test_filters_by_min_likes(self, isolated_db):
        now_iso = dt.datetime.now(dt.UTC).isoformat()
        with connect(isolated_db) as conn:
            conn.execute(
                """INSERT INTO tweets
                (tweet_id, source_url, source_handle, text, likes, retweets, replies, views,
                 author_followers, created_at, fetched_at, dedupe_hash, resonance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("t1", "u", "h", "t", 5, 0, 0, 100, 1000, now_iso, now_iso, "h1", 1.0),
            )

        top = rank.top_n_ranked(n=10, min_likes=20, freshness_hours=24, db_path=isolated_db)
        assert len(top) == 0  # 5 likes filtered out

    def test_filters_by_freshness(self, isolated_db):
        old = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=72)).isoformat()
        with connect(isolated_db) as conn:
            conn.execute(
                """INSERT INTO tweets
                (tweet_id, source_url, source_handle, text, likes, retweets, replies, views,
                 author_followers, created_at, fetched_at, dedupe_hash, resonance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("t1", "u", "h", "t", 100, 0, 0, 100, 1000, old, old, "h1", 5.0),
            )

        top = rank.top_n_ranked(n=10, min_likes=20, freshness_hours=24, db_path=isolated_db)
        assert len(top) == 0  # 72h old, freshness=24
