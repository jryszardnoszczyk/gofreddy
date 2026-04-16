from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import lane_runtime


def test_resolve_runtime_dir_falls_back_to_legacy_current(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    legacy_dir = archive_dir / "v001"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "run.py").write_text("print('legacy')\n")
    (archive_dir / "current").symlink_to("v001")

    assert lane_runtime.resolve_runtime_dir(archive_dir) == legacy_dir.resolve()


def test_ensure_materialized_runtime_overlays_lane_heads_and_preserves_runtime_state(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    legacy_dir = archive_dir / "v001"
    (legacy_dir / "sessions" / "geo" / "semrush").mkdir(parents=True)
    (legacy_dir / "sessions" / "geo" / "semrush" / "session.md").write_text("legacy state\n")
    (legacy_dir / "run.py").write_text("print('legacy run')\n")
    (archive_dir / "current").symlink_to("v001")

    core_dir = archive_dir / "c001"
    geo_dir = archive_dir / "g001"
    core_dir.mkdir(parents=True)
    geo_dir.mkdir(parents=True)
    (core_dir / "run.py").write_text("print('core run')\n")
    (core_dir / "programs").mkdir()
    (core_dir / "programs" / "geo-session.md").write_text("core geo\n")
    (geo_dir / "programs").mkdir()
    (geo_dir / "programs" / "geo-session.md").write_text("workflow geo\n")
    (geo_dir / "geo-findings.md").write_text("geo findings\n")

    manifest = {
        "core": "c001",
        "geo": "g001",
        "competitive": "",
        "monitoring": "",
        "storyboard": "",
    }
    (archive_dir / "current.json").write_text(json.dumps(manifest) + "\n")

    runtime_dir = lane_runtime.ensure_materialized_runtime(archive_dir)

    assert runtime_dir == archive_dir / lane_runtime.MATERIALIZED_DIRNAME
    assert (runtime_dir / "run.py").read_text() == "print('core run')\n"
    assert (runtime_dir / "programs" / "geo-session.md").read_text() == "workflow geo\n"
    assert (runtime_dir / "geo-findings.md").read_text() == "geo findings\n"
    assert (runtime_dir / "sessions" / "geo" / "semrush" / "session.md").read_text() == "legacy state\n"


def test_initialize_current_heads_points_all_lanes_at_legacy_head_without_cloning(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    legacy_dir = archive_dir / "v001"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "run.py").write_text("print('legacy')\n")
    (archive_dir / "current").symlink_to("v001")
    (archive_dir / "lineage.jsonl").write_text(
        json.dumps(
            {
                "id": "v001",
                "timestamp": "2026-04-01T00:00:00+00:00",
                "scores": {"geo": 0.1, "competitive": 0.2, "monitoring": 0.3, "storyboard": 0.4, "composite": 0.25},
                "search_metrics": {
                    "suite_id": "search-v1",
                    "composite": 0.25,
                    "domains": {
                        "geo": {"score": 0.1},
                        "competitive": {"score": 0.2},
                        "monitoring": {"score": 0.3},
                        "storyboard": {"score": 0.4},
                    },
                },
            }
        )
        + "\n"
    )

    manifest = lane_runtime.initialize_current_heads(archive_dir)

    assert manifest["core"] == "v001"
    assert manifest["geo"] == "v001"
    assert manifest["competitive"] == "v001"
    assert manifest["monitoring"] == "v001"
    assert manifest["storyboard"] == "v001"
    assert not (archive_dir / "v002").exists()
    assert json.loads((archive_dir / "current.json").read_text())["core"] == "v001"
