"""CLI tests for the lane-port shared commands: angle-show, angle-list,
holdout-export. Per master plan v13 §5.2-§5.3."""
from __future__ import annotations

import datetime as dt
import json
import stat
from pathlib import Path

from typer.testing import CliRunner

from x_engine.cli import app
from x_engine.pipeline.db import connect

runner = CliRunner()


def _seed_angle(db_path, *, angle_id: int | None = None,
                pillar: str = "harness-eng", picked_at: str | None = None,
                source_text: str | None = None) -> int:
    picked_at = picked_at or dt.datetime.now(dt.UTC).isoformat()
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO angles (run_date, headline, claim, source_url, "
            "source_handle, why_it_matters, suggested_format, voice_pillar, "
            "confidence, picked_at, source_text) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-07", "headline", "claim", "https://x.com/u/status/1",
             "@u", "why", "single", pillar, "high", picked_at, source_text),
        )
        return cur.lastrowid


def _seed_decision(db_path, *, draft_id: int, angle_id: int | None,
                   platform: str, outcome: str, skip_reason: str | None,
                   created_at: str = "2026-05-07T12:00:00+00:00") -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO draft_decisions "
            "(draft_id, angle_id, platform, outcome, skip_reason, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (draft_id, angle_id, platform, outcome, skip_reason, created_at),
        )


# ---------- angle-show ----------

def test_angle_show_returns_full_row(isolated_db):
    angle_id = _seed_angle(isolated_db, source_text="full source body text")
    result = runner.invoke(app, ["angle-show", str(angle_id)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["angle_id"] == angle_id
    assert payload["headline"] == "headline"
    assert payload["voice_pillar"] == "harness-eng"
    assert payload["source_text"] == "full source body text"


def test_angle_show_null_source_text_for_legacy_angle(isolated_db):
    """Pre-ALTER angles return source_text=null; agent prompts tolerate."""
    angle_id = _seed_angle(isolated_db, source_text=None)
    result = runner.invoke(app, ["angle-show", str(angle_id)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_text"] is None


def test_angle_show_unknown_id_exits_2(isolated_db):
    result = runner.invoke(app, ["angle-show", "99999"])
    assert result.exit_code == 2


# ---------- angle-list ----------

def test_angle_list_orders_by_picked_at_desc(isolated_db):
    older = _seed_angle(isolated_db, picked_at="2026-05-01T00:00:00+00:00")
    newer = _seed_angle(isolated_db, picked_at="2026-05-07T00:00:00+00:00")
    result = runner.invoke(app, ["angle-list", "--days", "30"])
    assert result.exit_code == 0, result.stdout
    rows = json.loads(result.stdout)
    ids = [r["angle_id"] for r in rows]
    assert ids[0] == newer
    assert ids[1] == older


def test_angle_list_filters_by_days(isolated_db):
    long_ago = (dt.datetime.now(dt.UTC) - dt.timedelta(days=90)).isoformat()
    fresh = (dt.datetime.now(dt.UTC) - dt.timedelta(days=1)).isoformat()
    _seed_angle(isolated_db, picked_at=long_ago)
    fresh_id = _seed_angle(isolated_db, picked_at=fresh)
    result = runner.invoke(app, ["angle-list", "--days", "7"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert [r["angle_id"] for r in rows] == [fresh_id]


def test_angle_list_respects_limit(isolated_db):
    for _ in range(5):
        _seed_angle(isolated_db)
    result = runner.invoke(app, ["angle-list", "--days", "30", "--limit", "2"])
    rows = json.loads(result.stdout)
    assert len(rows) == 2


# ---------- holdout-export ----------

def test_holdout_export_partitions_by_platform(isolated_db):
    a1 = _seed_angle(isolated_db)
    a2 = _seed_angle(isolated_db)
    _seed_decision(isolated_db, draft_id=174, angle_id=a1,
                   platform="x", outcome="ship", skip_reason=None)
    _seed_decision(isolated_db, draft_id=9001, angle_id=a2,
                   platform="linkedin", outcome="skip",
                   skip_reason="off_pillar")

    result = runner.invoke(app, ["holdout-export"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert set(payload["domains"]) == {"x_engine", "linkedin_engine"}
    assert len(payload["domains"]["x_engine"]) == 1
    assert len(payload["domains"]["linkedin_engine"]) == 1


def test_holdout_export_filters_no_time_rows(isolated_db):
    a1 = _seed_angle(isolated_db)
    _seed_decision(isolated_db, draft_id=1, angle_id=a1, platform="x",
                   outcome="skip", skip_reason="no_time")
    _seed_decision(isolated_db, draft_id=2, angle_id=a1, platform="x",
                   outcome="skip", skip_reason="voice_off")
    result = runner.invoke(app, ["holdout-export"])
    payload = json.loads(result.stdout)
    fixture_ids = {f["fixture_id"]
                   for f in payload["domains"]["x_engine"]}
    assert any("d2" in fid for fid in fixture_ids)
    assert not any("d1" in fid for fid in fixture_ids)


def test_holdout_export_fixture_shape_matches_schema(isolated_db):
    a1 = _seed_angle(isolated_db)
    _seed_decision(isolated_db, draft_id=42, angle_id=a1, platform="x",
                   outcome="ship", skip_reason=None,
                   created_at="2026-05-07T18:30:00+00:00")
    result = runner.invoke(app, ["holdout-export"])
    payload = json.loads(result.stdout)
    entry = payload["domains"]["x_engine"][0]
    assert entry == {
        "fixture_id": f"jr-2026-05-07-x-d42",
        "client": "jr",
        "context": str(a1),
        "version": "1.0",
        "max_iter": 1,
        "timeout": 600,
        "anchor": True,
        "env": {
            "JR_GROUND_TRUTH": "ship",
            "SKIP_REASON": "",
            "PLATFORM": "x",
        },
    }


def test_holdout_export_skip_reason_propagated_to_env(isolated_db):
    a1 = _seed_angle(isolated_db)
    _seed_decision(isolated_db, draft_id=5, angle_id=a1, platform="linkedin",
                   outcome="skip", skip_reason="duplicate")
    result = runner.invoke(app, ["holdout-export"])
    payload = json.loads(result.stdout)
    entry = payload["domains"]["linkedin_engine"][0]
    assert entry["env"]["JR_GROUND_TRUTH"] == "skip"
    assert entry["env"]["SKIP_REASON"] == "duplicate"
    assert entry["env"]["PLATFORM"] == "linkedin"


def test_holdout_export_writes_file_at_mode_600(isolated_db, tmp_path):
    a1 = _seed_angle(isolated_db)
    _seed_decision(isolated_db, draft_id=7, angle_id=a1, platform="x",
                   outcome="ship", skip_reason=None)
    out = tmp_path / "holdouts" / "lane-port.json"
    result = runner.invoke(app, ["holdout-export", "--output", str(out)])
    assert result.exit_code == 0, result.stdout

    assert out.exists()
    mode = stat.S_IMODE(out.stat().st_mode)
    assert mode == 0o600

    contents = json.loads(out.read_text())
    assert "domains" in contents
    assert len(contents["domains"]["x_engine"]) == 1

    summary = json.loads(result.stdout)
    assert summary["x_engine"] == 1
    assert summary["linkedin_engine"] == 0
    assert summary["output"] == str(out)


def test_holdout_export_handles_null_angle_id(isolated_db):
    """Cold-start hand_drafts with angle_id=NULL still export — context becomes ''."""
    _seed_decision(isolated_db, draft_id=300, angle_id=None,
                   platform="linkedin", outcome="ship", skip_reason=None)
    result = runner.invoke(app, ["holdout-export"])
    payload = json.loads(result.stdout)
    entry = payload["domains"]["linkedin_engine"][0]
    assert entry["context"] == ""
