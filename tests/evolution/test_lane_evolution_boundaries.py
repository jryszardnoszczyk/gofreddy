from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import archive_index
import select_parent
from lane_paths import path_owned_by_lane


def test_sync_variant_workspace_only_applies_owned_lane_paths(tmp_path: Path) -> None:
    source_variant_dir = tmp_path / "source"
    target_variant_dir = tmp_path / "target"
    (source_variant_dir / "programs").mkdir(parents=True)
    (source_variant_dir / "templates" / "geo").mkdir(parents=True)
    (target_variant_dir / "programs").mkdir(parents=True)
    (target_variant_dir / "templates" / "geo").mkdir(parents=True)

    (source_variant_dir / "programs" / "geo-session.md").write_text("new geo prompt\n")
    (source_variant_dir / "run.py").write_text("print('new core')\n")
    (target_variant_dir / "programs" / "geo-session.md").write_text("old geo prompt\n")
    (target_variant_dir / "run.py").write_text("print('old core')\n")

    archive_index.sync_variant_workspace(source_variant_dir, target_variant_dir, lane="geo")

    assert (target_variant_dir / "programs" / "geo-session.md").read_text() == "new geo prompt\n"
    assert (target_variant_dir / "run.py").read_text() == "print('old core')\n"


def test_select_parent_prefers_lane_local_entries_when_available(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "lineage.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "v001",
                        "lane": "core",
                        "search_metrics": {
                            "suite_id": "search-v1",
                            "composite": 0.8,
                            "domains": {
                                "geo": {"score": 0.2},
                                "competitive": {"score": 0.8},
                                "monitoring": {"score": 0.8},
                                "storyboard": {"score": 0.8},
                            },
                        },
                    }
                ),
                json.dumps(
                    {
                        "id": "v002",
                        "lane": "geo",
                        "search_metrics": {
                            "suite_id": "search-v1",
                            "composite": 0.4,
                            "domains": {
                                "geo": {"score": 0.9},
                                "competitive": {"score": 0.1},
                                "monitoring": {"score": 0.1},
                                "storyboard": {"score": 0.1},
                            },
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    parent_path = select_parent.select_parent(str(archive_dir), suite_id="search-v1", lane="geo")

    assert Path(parent_path).name == "v002"


def test_lane_ownership_includes_workflow_session_evaluator_modules() -> None:
    assert path_owned_by_lane("workflows/session_eval_geo.py", "geo") is True
    assert path_owned_by_lane("workflows/session_eval_competitive.py", "competitive") is True
    assert path_owned_by_lane("workflows/session_eval_monitoring.py", "monitoring") is True
    assert path_owned_by_lane("workflows/session_eval_storyboard.py", "storyboard") is True
    assert path_owned_by_lane("workflows/session_eval_geo.py", "core") is False
