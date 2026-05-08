"""DB schema tests."""
from __future__ import annotations

import importlib
import os
import sqlite3
from pathlib import Path

import pytest

from x_engine.pipeline.db import connect, init_db, migrate_state_db


def test_db_path_env_override(tmp_path, monkeypatch):
    """X_ENGINE_DB_PATH overrides the package-relative default at import.

    Worktree experiments + multi-host setups need to point at an external
    state.db without code changes. Production cron leaves the env unset
    and uses the default (Path(__file__).parent.parent / "state.db").
    """
    target = tmp_path / "alt-state.db"
    monkeypatch.setenv("X_ENGINE_DB_PATH", str(target))
    import x_engine.pipeline.db as db_mod
    importlib.reload(db_mod)
    try:
        assert db_mod.DB_PATH == target
    finally:
        # Restore module to default so subsequent tests aren't poisoned.
        monkeypatch.delenv("X_ENGINE_DB_PATH", raising=False)
        importlib.reload(db_mod)


def test_db_path_default_when_env_unset(monkeypatch):
    """Without X_ENGINE_DB_PATH the default is package-relative state.db."""
    monkeypatch.delenv("X_ENGINE_DB_PATH", raising=False)
    import x_engine.pipeline.db as db_mod
    importlib.reload(db_mod)
    expected = Path(db_mod.__file__).parent.parent / "state.db"
    assert db_mod.DB_PATH == expected


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
    assert "draft_decisions" in tables
    assert "linkedin_posts" in tables
    assert "hand_drafts" in tables


def test_angles_has_source_text_column(isolated_db):
    with connect(isolated_db) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(angles)").fetchall()}
    assert "source_text" in cols


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


def test_migrate_state_db_adds_source_text_to_legacy_db(tmp_path):
    """v1 angles table without source_text gets ALTER-added on migration."""
    legacy_db = tmp_path / "legacy.db"
    with sqlite3.connect(legacy_db) as conn:
        conn.executescript(
            """
            CREATE TABLE angles (
                angle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                headline TEXT NOT NULL,
                claim TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_handle TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                suggested_format TEXT NOT NULL,
                voice_pillar TEXT NOT NULL,
                confidence TEXT NOT NULL,
                picked_at TEXT NOT NULL
            );
            """
        )
    migrate_state_db(legacy_db)
    with sqlite3.connect(legacy_db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(angles)").fetchall()]
    assert "source_text" in cols


def test_migrate_state_db_idempotent(isolated_db):
    """Re-running migrate must not raise sqlite3.OperationalError on duplicate column."""
    migrate_state_db(isolated_db)
    migrate_state_db(isolated_db)  # second call must be a no-op


def test_init_db_auto_migrates_legacy_db(tmp_path):
    legacy_db = tmp_path / "legacy.db"
    with sqlite3.connect(legacy_db) as conn:
        conn.executescript(
            """
            CREATE TABLE angles (
                angle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                headline TEXT NOT NULL,
                claim TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_handle TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                suggested_format TEXT NOT NULL,
                voice_pillar TEXT NOT NULL,
                confidence TEXT NOT NULL,
                picked_at TEXT NOT NULL
            );
            """
        )
    init_db(legacy_db)
    with sqlite3.connect(legacy_db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(angles)").fetchall()]
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    assert "source_text" in cols
    assert {"draft_decisions", "linkedin_posts", "hand_drafts"} <= tables


def test_draft_decisions_check_constraints(isolated_db):
    with connect(isolated_db) as conn:
        conn.execute(
            "INSERT INTO draft_decisions (draft_id, angle_id, platform, outcome, "
            "skip_reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (1, 1, "x", "ship", None, "2026-05-07T00:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO draft_decisions (draft_id, angle_id, platform, outcome, "
            "skip_reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (2, 2, "linkedin", "skip", "voice_off", "2026-05-07T00:00:01+00:00"),
        )
    with pytest.raises(sqlite3.IntegrityError):
        with connect(isolated_db) as conn:
            conn.execute(
                "INSERT INTO draft_decisions (draft_id, angle_id, platform, outcome, "
                "skip_reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (3, 3, "instagram", "ship", None, "2026-05-07T00:00:02+00:00"),
            )
    with pytest.raises(sqlite3.IntegrityError):
        with connect(isolated_db) as conn:
            conn.execute(
                "INSERT INTO draft_decisions (draft_id, angle_id, platform, outcome, "
                "skip_reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (4, 4, "x", "draft", None, "2026-05-07T00:00:03+00:00"),
            )
    with pytest.raises(sqlite3.IntegrityError):
        with connect(isolated_db) as conn:
            conn.execute(
                "INSERT INTO draft_decisions (draft_id, angle_id, platform, outcome, "
                "skip_reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (5, 5, "x", "skip", "lazy", "2026-05-07T00:00:04+00:00"),
            )


def test_linkedin_posts_pk_dedupes(isolated_db):
    with connect(isolated_db) as conn:
        for _ in range(2):
            conn.execute(
                "INSERT OR IGNORE INTO linkedin_posts "
                "(post_id, post_text, posted_at, fetched_at) VALUES (?, ?, ?, ?)",
                ("urn:li:activity:1", "post body", "2026-05-07T00:00:00+00:00",
                 "2026-05-07T00:00:00+00:00"),
            )
        rows = conn.execute("SELECT COUNT(*) FROM linkedin_posts").fetchone()
    assert rows[0] == 1


def test_hand_drafts_autoincrement_and_constraint(isolated_db):
    with connect(isolated_db) as conn:
        cur = conn.execute(
            "INSERT INTO hand_drafts (platform, body, angle_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("linkedin", "hand-written body", None, "2026-05-07T00:00:00+00:00"),
        )
        first_id = cur.lastrowid
        cur = conn.execute(
            "INSERT INTO hand_drafts (platform, body, angle_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("x", "another", 42, "2026-05-07T00:00:01+00:00"),
        )
        second_id = cur.lastrowid
    assert second_id == first_id + 1
    with pytest.raises(sqlite3.IntegrityError):
        with connect(isolated_db) as conn:
            conn.execute(
                "INSERT INTO hand_drafts (platform, body, angle_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                ("threads", "body", None, "2026-05-07T00:00:02+00:00"),
            )


def test_upsert_search_tweets(isolated_db):
    """Search-discovered tweets land in same table; PK dedupes against creator pulls."""
    from x_engine.pipeline import db as db_mod
    from x_engine.pipeline.pull import upsert_search_tweets

    # Need to monkeypatch DB_PATH for upsert_search_tweets which uses default connect()
    db_mod.DB_PATH = isolated_db
    sample = [
        {
            "id": "9001",
            "text": "Discovered via search.",
            "url": "https://x.com/discovered/status/9001",
            "createdAt": "Mon May 06 10:00:00 +0000 2026",
            "likeCount": 100,
            "retweetCount": 5,
            "replyCount": 2,
            "viewCount": 5000,
            "author": {"userName": "discovered", "followers": 5000},
        }
    ]
    n1 = upsert_search_tweets(sample, "test_label")
    n2 = upsert_search_tweets(sample, "test_label")  # same tweet, should dedupe
    assert n1 == 1
    assert n2 == 0
