"""CLI tests for the lane-port decision commands: mark-posted (extended)
and skip-draft (new). Critical-path per master plan v13 §5.2 — these MUST
land before L1 day-1 dogfood, otherwise marks land in `recent_posted` only
and `holdout-export` produces zero rows."""
from __future__ import annotations

import datetime as dt
import json

import pytest
from typer.testing import CliRunner

from x_engine.cli import app
from x_engine.pipeline.db import connect

runner = CliRunner()


def _seed_drafts_row(db_path, draft_id: int = 174) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO angles (run_date, headline, claim, source_url, "
            "source_handle, why_it_matters, suggested_format, voice_pillar, "
            "confidence, picked_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-07", "h", "c", "u", "@h", "w", "single", "harness-eng",
             "high", "2026-05-07T00:00:00+00:00"),
        )
        angle_id = cur.lastrowid
        conn.execute(
            "INSERT INTO drafts (draft_id, angle_id, variant_id, format, hook, "
            "text, rationale, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (draft_id, angle_id, 1, "single", "hook", "draft body", "r",
             "2026-05-07T00:00:00+00:00"),
        )
    return angle_id


def _seed_hand_drafts_row(db_path, draft_id: int = 9001) -> int | None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO hand_drafts (draft_id, platform, body, angle_id, "
            "created_at) VALUES (?, ?, ?, ?, ?)",
            (draft_id, "linkedin", "hand-written body", None,
             "2026-05-07T00:00:00+00:00"),
        )
    return None


# ---------- mark-posted ----------

def test_mark_posted_x_default_writes_both_tables(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(app, ["mark-posted", "174"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "draft_id": 174,
        "platform": "x",
        "outcome": "ship",
        "marked_posted_at": payload["marked_posted_at"],
        "tweet_url": "",
        "source": "drafts",
    }
    with connect(isolated_db) as conn:
        decisions = conn.execute(
            "SELECT platform, outcome, skip_reason FROM draft_decisions "
            "WHERE draft_id=?",
            (174,),
        ).fetchall()
        posted = conn.execute(
            "SELECT draft_id FROM recent_posted WHERE draft_id=?",
            (174,),
        ).fetchall()
    assert len(decisions) == 1
    assert tuple(decisions[0]) == ("x", "ship", None)
    assert len(posted) == 1


def test_mark_posted_linkedin_writes_decisions_only(isolated_db):
    _seed_hand_drafts_row(isolated_db, draft_id=9001)
    result = runner.invoke(app, ["mark-posted", "9001", "--platform", "linkedin"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["platform"] == "linkedin"
    assert payload["source"] == "hand_drafts"
    with connect(isolated_db) as conn:
        decisions = conn.execute(
            "SELECT platform, outcome FROM draft_decisions WHERE draft_id=?",
            (9001,),
        ).fetchall()
        posted = conn.execute(
            "SELECT draft_id FROM recent_posted WHERE draft_id=?",
            (9001,),
        ).fetchall()
    assert len(decisions) == 1
    assert tuple(decisions[0]) == ("linkedin", "ship")
    assert posted == []  # LinkedIn engagement-sync deferred to v2


def test_mark_posted_unknown_draft_exits_2(isolated_db):
    result = runner.invoke(app, ["mark-posted", "99999"])
    assert result.exit_code == 2
    assert "not found in drafts or hand_drafts" in result.stdout + (result.stderr or "")


def test_mark_posted_invalid_platform_exits_2(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(app, ["mark-posted", "174", "--platform", "threads"])
    assert result.exit_code == 2


def test_mark_posted_with_tweet_url_persists_to_recent_posted(isolated_db):
    _seed_drafts_row(isolated_db)
    url = "https://x.com/jr/status/12345"
    result = runner.invoke(app, ["mark-posted", "174", "--tweet-url", url])
    assert result.exit_code == 0, result.stdout
    with connect(isolated_db) as conn:
        row = conn.execute(
            "SELECT tweet_url FROM recent_posted WHERE draft_id=?",
            (174,),
        ).fetchone()
    assert row["tweet_url"] == url


# ---------- skip-draft ----------

def test_skip_draft_writes_decisions_with_reason(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(
        app, ["skip-draft", "174", "--reason", "voice_off"]
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["outcome"] == "skip"
    assert payload["skip_reason"] == "voice_off"
    assert payload["platform"] == "x"
    with connect(isolated_db) as conn:
        row = conn.execute(
            "SELECT platform, outcome, skip_reason FROM draft_decisions "
            "WHERE draft_id=?",
            (174,),
        ).fetchone()
    assert tuple(row) == ("x", "skip", "voice_off")


def test_skip_draft_linkedin_with_off_pillar(isolated_db):
    _seed_hand_drafts_row(isolated_db, draft_id=9002)
    result = runner.invoke(
        app,
        ["skip-draft", "9002", "--platform", "linkedin", "--reason", "off_pillar"],
    )
    assert result.exit_code == 0, result.stdout
    with connect(isolated_db) as conn:
        row = conn.execute(
            "SELECT platform, outcome, skip_reason FROM draft_decisions "
            "WHERE draft_id=?",
            (9002,),
        ).fetchone()
    assert tuple(row) == ("linkedin", "skip", "off_pillar")


@pytest.mark.parametrize(
    "reason",
    ["voice_off", "factual_unverifiable", "off_pillar",
     "duplicate", "no_time", "other"],
)
def test_skip_draft_accepts_all_enum_reasons(isolated_db, reason):
    _seed_drafts_row(isolated_db, draft_id=200 + hash(reason) % 1000)
    draft_id = 200 + hash(reason) % 1000
    result = runner.invoke(
        app, ["skip-draft", str(draft_id), "--reason", reason]
    )
    assert result.exit_code == 0, result.stdout


def test_skip_draft_rejects_unknown_reason(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(
        app, ["skip-draft", "174", "--reason", "looked_lazy"]
    )
    assert result.exit_code == 2


def test_skip_draft_missing_reason_exits_2(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(app, ["skip-draft", "174"])
    assert result.exit_code == 2


def test_skip_draft_unknown_draft_id_exits_2(isolated_db):
    result = runner.invoke(
        app, ["skip-draft", "99999", "--reason", "other"]
    )
    assert result.exit_code == 2


def test_skip_draft_invalid_platform_exits_2(isolated_db):
    _seed_drafts_row(isolated_db)
    result = runner.invoke(
        app, ["skip-draft", "174", "--platform", "threads", "--reason", "other"]
    )
    assert result.exit_code == 2
