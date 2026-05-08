"""α7 unit tests for detect_meta_patterns.py.

Builds a tiny 2-lane fixture with known overlapping reasoning beats and
asserts the clusterer surfaces them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_DIR))

import detect_meta_patterns as dmp  # type: ignore  # noqa: E402


def _make_fake_session(
    session_dir: Path, *, iter_n: int, beats: list[tuple[str, str]]
) -> None:
    """Create a minimal session dir extract_reasoning can parse.

    extract_reasoning expects bare ``codex`` and ``exec`` markers on a line
    by themselves followed by the beat text on the next non-empty line.
    """
    logs = session_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    err = logs / f"iteration_{iter_n:03d}.log.err"
    lines: list[str] = []
    for _kind, text in beats:
        lines.append("codex")
        lines.append("")
        lines.append(text)
        lines.append("")
    err.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # extract_iteration also expects iteration_<n>.log (companion file)
    (logs / f"iteration_{iter_n:03d}.log").write_text("", encoding="utf-8")
    # Minimal results.jsonl so detect_meta_patterns considers the session.
    (session_dir / "results.jsonl").write_text(
        json.dumps({"iteration": iter_n, "type": "first_move", "status": "ok"}) + "\n",
        encoding="utf-8",
    )


def test_cluster_finds_overlap_across_lanes(tmp_path):
    """A repeated beat across 2 lanes/fixtures surfaces as a meta-pattern."""
    archive_root = tmp_path / "archive"
    # Mock ARCHIVE_ROOT so find_recent_session_dirs walks our fake tree
    dmp.ARCHIVE_ROOT = archive_root

    # Build v007/sessions/geo/mayoclinic + v007/sessions/competitive/sap
    # both containing the same recurring beat.
    common_beat = "I'll read the persisted session state before deciding"
    geo_dir = archive_root / "v007" / "sessions" / "geo" / "mayoclinic"
    comp_dir = archive_root / "v007" / "sessions" / "competitive" / "sap"

    _make_fake_session(geo_dir, iter_n=1, beats=[
        ("first_move", common_beat),
        ("decide", "I'll fetch the citation visibility delta"),
    ])
    _make_fake_session(comp_dir, iter_n=1, beats=[
        ("first_move", common_beat + " on this lane"),
        ("decide", "I'll inspect the competitor brief structure"),
    ])

    result = dmp.find_meta_patterns(
        [geo_dir, comp_dir], min_fixtures=2, min_lanes=2,
    )

    assert "meta_patterns" in result
    assert "stats" in result
    assert result["stats"]["sessions"] == 2

    # The common beat should surface as a cross-lane meta-pattern.
    cross_lane = [
        p for p in result["meta_patterns"]
        if p["distinct_lanes"] >= 2 and p["distinct_fixtures"] >= 2
    ]
    assert len(cross_lane) >= 1, (
        f"Expected ≥1 cross-lane pattern, got {len(cross_lane)}. "
        f"Patterns: {result['meta_patterns']}"
    )

    # The representative text should mention "session state" (the common phrase)
    matched = any("session state" in p["representative_text"].lower()
                  for p in cross_lane)
    assert matched, (
        f"Expected the recurring 'session state' beat to surface; "
        f"got: {[p['representative_text'] for p in cross_lane]}"
    )


def test_no_clusters_when_beats_are_distinct(tmp_path):
    """Wholly distinct beats produce no meta-patterns."""
    archive_root = tmp_path / "archive"
    dmp.ARCHIVE_ROOT = archive_root

    geo_dir = archive_root / "v007" / "sessions" / "geo" / "mayoclinic"
    comp_dir = archive_root / "v007" / "sessions" / "competitive" / "sap"

    _make_fake_session(geo_dir, iter_n=1, beats=[
        ("first_move", "I'll process the GEO landing page schema"),
    ])
    _make_fake_session(comp_dir, iter_n=1, beats=[
        ("first_move", "I'll diff the pricing matrix across competitors"),
    ])

    result = dmp.find_meta_patterns(
        [geo_dir, comp_dir], min_fixtures=2, min_lanes=2,
    )

    # Either no patterns OR no cross-lane patterns
    cross_lane = [
        p for p in result["meta_patterns"]
        if p["distinct_lanes"] >= 2
    ]
    assert len(cross_lane) == 0, (
        f"Expected no cross-lane patterns from distinct beats, "
        f"got: {cross_lane}"
    )
