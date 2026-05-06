"""DB schema tests."""
from __future__ import annotations

from x_engine.pipeline.db import connect, init_db


def test_init_creates_schema(isolated_db):
    with connect(isolated_db) as conn:
        tables = {
            r["name"]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    assert "tweets" in tables
    assert "releases" in tables
    assert "rss_items" in tables
    assert "angles" in tables
    assert "drafts" in tables
    assert "recent_posted" in tables


def test_init_idempotent(isolated_db):
    init_db(isolated_db)
    init_db(isolated_db)  # should not raise


def test_tweets_pk_dedupes(isolated_db):
    with connect(isolated_db) as conn:
        for _ in range(2):
            conn.execute(
                """INSERT OR IGNORE INTO tweets
                (tweet_id, source_url, source_handle, text, created_at, fetched_at, dedupe_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("t1", "u", "h", "t", "2026-05-06T00:00:00+00:00",
                 "2026-05-06T00:00:00+00:00", "h"),
            )
        rows = conn.execute("SELECT COUNT(*) FROM tweets").fetchone()
    assert rows[0] == 1


def test_drafts_foreign_key_relation(isolated_db):
    with connect(isolated_db) as conn:
        cur = conn.execute(
            """INSERT INTO angles
            (run_date, headline, claim, source_url, source_handle, why_it_matters,
             suggested_format, voice_pillar, confidence, picked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("2026-05-06", "h", "c", "u", "@h", "w", "single", "p", "high",
             "2026-05-06T00:00:00+00:00"),
        )
        angle_id = cur.lastrowid

        conn.execute(
            """INSERT INTO drafts
            (angle_id, variant_id, format, hook, text, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (angle_id, 1, "single", "hook", "text", "rationale",
             "2026-05-06T00:00:00+00:00"),
        )

        rows = conn.execute(
            "SELECT angle_id FROM drafts WHERE variant_id=1"
        ).fetchall()
    assert rows[0]["angle_id"] == angle_id
