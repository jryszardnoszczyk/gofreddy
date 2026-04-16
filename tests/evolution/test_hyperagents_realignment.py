from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTORESEARCH_DIR = REPO_ROOT / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

import select_parent


def _write_lineage(archive_dir: Path, entries: list[dict]) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(entry) for entry in entries) + "\n"
    (archive_dir / "lineage.jsonl").write_text(payload)


def test_select_parent_samples_only_searchable_nondiscarded_variants(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_lineage(
        archive_dir,
        [
            {
                "id": "v001",
                "timestamp": "2026-04-01T00:00:00+00:00",
                "children": 0,
                "search_metrics": {"suite_id": "search-v1", "composite": 0.41},
            },
            {
                "id": "v002",
                "timestamp": "2026-04-01T01:00:00+00:00",
                "status": "discarded",
                "search_metrics": {"suite_id": "search-v1", "composite": 0.99},
            },
            {
                "id": "v003",
                "timestamp": "2026-04-01T02:00:00+00:00",
                "search_metrics": {"suite_id": "", "composite": 0.75},
            },
            {
                "id": "v004",
                "timestamp": "2026-04-01T03:00:00+00:00",
                "children": 3,
                "search_metrics": {"suite_id": "search-v1", "composite": 0.33},
            },
        ],
    )

    with patch("select_parent.random.choices", side_effect=lambda entries, weights, k: [entries[-1]]) as mock_choice:
        selected = select_parent.select_parent(str(archive_dir))

    assert selected == str(archive_dir / "v004")
    eligible_ids = [entry["id"] for entry in mock_choice.call_args.args[0]]
    assert eligible_ids == ["v001", "v004"]
    weights = mock_choice.call_args.kwargs["weights"]
    midpoint = (0.41 + 0.33) / 2
    expected_v001 = (1.0 / (1.0 + math.exp(-10.0 * (0.41 - midpoint)))) * 1.0
    expected_v004 = (1.0 / (1.0 + math.exp(-10.0 * (0.33 - midpoint)))) * (1.0 / 4.0)
    assert weights[0] == expected_v001
    assert weights[1] == expected_v004
    assert weights[0] > weights[1]


def test_select_parent_filters_to_active_search_suite(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    _write_lineage(
        archive_dir,
        [
            {
                "id": "v001",
                "timestamp": "2026-04-01T00:00:00+00:00",
                "children": 0,
                "search_metrics": {"suite_id": "search-v1", "composite": 0.41},
            },
            {
                "id": "v002",
                "timestamp": "2026-04-01T01:00:00+00:00",
                "children": 0,
                "search_metrics": {"suite_id": "search-v0", "composite": 0.99},
            },
        ],
    )

    with patch("select_parent.random.choices", side_effect=lambda entries, weights, k: [entries[0]]) as mock_choice:
        selected = select_parent.select_parent(str(archive_dir), suite_id="search-v1")

    assert selected == str(archive_dir / "v001")
    eligible_ids = [entry["id"] for entry in mock_choice.call_args.args[0]]
    assert eligible_ids == ["v001"]
