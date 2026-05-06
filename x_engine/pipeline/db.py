"""SQLite state for x_engine. Single-file DB at x_engine/state.db."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(__file__).parent.parent / "state.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tweets (
    tweet_id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_handle TEXT NOT NULL,
    text TEXT NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    retweets INTEGER NOT NULL DEFAULT 0,
    replies INTEGER NOT NULL DEFAULT 0,
    views INTEGER NOT NULL DEFAULT 0,
    author_followers INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    resonance_score REAL NOT NULL DEFAULT 0,
    dedupe_hash TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tweets_resonance ON tweets(resonance_score DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_fetched ON tweets(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_handle ON tweets(source_handle);

CREATE TABLE IF NOT EXISTS releases (
    release_id TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    name TEXT NOT NULL,
    body TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_releases_published ON releases(published_at DESC);

CREATE TABLE IF NOT EXISTS rss_items (
    rss_id TEXT PRIMARY KEY,
    source_label TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rss_published ON rss_items(published_at DESC);

CREATE TABLE IF NOT EXISTS angles (
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

CREATE INDEX IF NOT EXISTS idx_angles_run ON angles(run_date);

CREATE TABLE IF NOT EXISTS drafts (
    draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
    angle_id INTEGER NOT NULL,
    variant_id INTEGER NOT NULL,
    format TEXT NOT NULL,
    hook TEXT NOT NULL,
    text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    length_bracket TEXT NOT NULL DEFAULT 'build',
    first_reply_text TEXT NOT NULL DEFAULT '',
    char_count INTEGER NOT NULL DEFAULT 0,
    score_voice REAL NOT NULL DEFAULT 0,
    score_factual REAL NOT NULL DEFAULT 0,
    score_hook REAL NOT NULL DEFAULT 0,
    score_slop REAL NOT NULL DEFAULT 0,
    score_richness REAL NOT NULL DEFAULT 0,
    score_avg REAL NOT NULL DEFAULT 0,
    has_specific_number INTEGER NOT NULL DEFAULT 0,
    has_attribution INTEGER NOT NULL DEFAULT 0,
    ship INTEGER NOT NULL DEFAULT 0,
    factual_veto INTEGER NOT NULL DEFAULT 0,
    revised INTEGER NOT NULL DEFAULT 0,
    slop_blocked INTEGER NOT NULL DEFAULT 0,
    slop_flags TEXT NOT NULL DEFAULT '',
    critic_concerns TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(angle_id) REFERENCES angles(angle_id)
);

CREATE INDEX IF NOT EXISTS idx_drafts_angle ON drafts(angle_id);
CREATE INDEX IF NOT EXISTS idx_drafts_ship ON drafts(ship DESC, score_avg DESC);

CREATE TABLE IF NOT EXISTS recent_posted (
    posted_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    posted_at TEXT NOT NULL,
    draft_id INTEGER,
    angle_id INTEGER,
    pillar TEXT,
    tweet_url TEXT,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    last_synced_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_posted_at ON recent_posted(posted_at DESC);
"""


def init_db(db_path=None) -> None:
    """Create schema if not present. Idempotent.

    db_path defaults to module-level DB_PATH at CALL time, not import time.
    """
    path = db_path if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def connect(db_path=None) -> Iterator[sqlite3.Connection]:
    """Yield a sqlite3 connection with row_factory set to Row."""
    path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
