"""CLI tests for `xeng search-v1-sync` (M5: fixture/angle drift fix).

Per master plan v13 §A "Adjacent": x_engine + linkedin_engine fixtures
use angle_id as `context`. This command keeps search-v1 fixture contexts
in sync with the rolling top-N of the live angles table.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from typer.testing import CliRunner

from x_engine.cli import app
from x_engine.pipeline.db import connect

runner = CliRunner()


def _seed_angles(db_path: Path, n: int) -> list[int]:
    """Seed N angles with monotonically increasing picked_at."""
    ids: list[int] = []
    base = dt.datetime(2026, 5, 1, tzinfo=dt.UTC)
    with connect(db_path) as conn:
        for i in range(n):
            picked_at = (base + dt.timedelta(hours=i)).isoformat()
            cur = conn.execute(
                "INSERT INTO angles (run_date, headline, claim, source_url, "
                "source_handle, why_it_matters, suggested_format, voice_pillar, "
                "confidence, picked_at, source_text) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("2026-05-07", f"head{i}", f"claim{i}", f"https://x.com/{i}",
                 "@u", "why", "single", "harness-eng", "high", picked_at, None),
            )
            ids.append(cur.lastrowid)
    return ids


def _make_manifest(path: Path) -> None:
    """Write a search-v1.json with placeholder x_engine + linkedin_engine
    entries that the sync command should replace."""
    payload = {
        "suite_id": "search-v1",
        "version": "1.0",
        "domains": {
            "geo": [
                {"fixture_id": "geo-stable", "client": "semrush",
                 "context": "https://semrush.com", "max_iter": 15,
                 "timeout": 1200, "anchor": True, "version": "1.0"},
            ],
            "x_engine": [
                {"fixture_id": "x_engine-angle-1", "client": "jr",
                 "context": "1", "max_iter": 1, "timeout": 1800,
                 "anchor": False, "version": "1.0"},
            ],
            "linkedin_engine": [
                {"fixture_id": "linkedin_engine-angle-1", "client": "jr",
                 "context": "1", "max_iter": 1, "timeout": 1800,
                 "anchor": False, "version": "1.0"},
            ],
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_search_v1_sync_writes_top_n_for_both_lanes(isolated_db, tmp_path):
    """Default flow: top 5 by picked_at desc, both lanes synced."""
    angle_ids = _seed_angles(isolated_db, n=8)
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)

    result = runner.invoke(
        app, ["search-v1-sync", "--manifest", str(manifest), "--top", "5"]
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(manifest.read_text())
    # x_engine + linkedin_engine each got 5 fixtures
    assert len(payload["domains"]["x_engine"]) == 5
    assert len(payload["domains"]["linkedin_engine"]) == 5
    # Most-recent-first: contexts are the last 5 angle IDs in descending order
    expected = [str(aid) for aid in sorted(angle_ids[-5:], reverse=True)]
    actual_x = [f["context"] for f in payload["domains"]["x_engine"]]
    assert actual_x == expected, f"got {actual_x}, want {expected}"
    # geo (other lane) untouched
    assert payload["domains"]["geo"][0]["fixture_id"] == "geo-stable"


def test_search_v1_sync_x_only(isolated_db, tmp_path):
    """--platforms x synces only x_engine; linkedin_engine untouched."""
    _seed_angles(isolated_db, n=3)
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)

    result = runner.invoke(
        app,
        ["search-v1-sync", "--manifest", str(manifest), "--platforms", "x"],
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(manifest.read_text())
    assert len(payload["domains"]["x_engine"]) == 3
    # linkedin_engine retained the placeholder
    assert payload["domains"]["linkedin_engine"][0]["context"] == "1"


def test_search_v1_sync_handles_empty_angles_table(isolated_db, tmp_path):
    """Empty angles table → 0 fixtures, manifest written with empty lists.
    No crash; LaunchAgent can run before the angle-pick cron."""
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)

    result = runner.invoke(
        app, ["search-v1-sync", "--manifest", str(manifest), "--top", "5"]
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(manifest.read_text())
    assert payload["domains"]["x_engine"] == []
    assert payload["domains"]["linkedin_engine"] == []


def test_search_v1_sync_dry_run_does_not_write(isolated_db, tmp_path):
    """--dry-run prints fixture lists but leaves manifest untouched."""
    _seed_angles(isolated_db, n=3)
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)
    pre_text = manifest.read_text()

    result = runner.invoke(
        app, ["search-v1-sync", "--manifest", str(manifest), "--dry-run"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "fixtures" in payload
    assert len(payload["fixtures"]["x_engine"]) == 3

    # Manifest unchanged on disk
    assert manifest.read_text() == pre_text


def test_search_v1_sync_atomic_rewrite(isolated_db, tmp_path):
    """Atomic rename: tmp file should NOT linger after the run."""
    _seed_angles(isolated_db, n=2)
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)

    result = runner.invoke(app, ["search-v1-sync", "--manifest", str(manifest)])
    assert result.exit_code == 0
    assert not (tmp_path / "search-v1.json.tmp").exists()


def test_search_v1_sync_rejects_unknown_platform(isolated_db, tmp_path):
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)
    result = runner.invoke(
        app,
        ["search-v1-sync", "--manifest", str(manifest), "--platforms", "tiktok"],
    )
    assert result.exit_code == 2
    assert "tiktok" in result.stdout or "tiktok" in (result.stderr or "")


def test_search_v1_sync_rejects_top_zero(isolated_db, tmp_path):
    manifest = tmp_path / "search-v1.json"
    _make_manifest(manifest)
    result = runner.invoke(
        app, ["search-v1-sync", "--manifest", str(manifest), "--top", "0"]
    )
    assert result.exit_code == 2


def test_search_v1_sync_missing_manifest_errors(isolated_db, tmp_path):
    result = runner.invoke(
        app,
        ["search-v1-sync", "--manifest", str(tmp_path / "nope.json")],
    )
    assert result.exit_code == 2
