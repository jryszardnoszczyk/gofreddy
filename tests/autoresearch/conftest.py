"""Shared path setup so autoresearch/* is importable from tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_AUTORESEARCH = _REPO_ROOT / "autoresearch"

for path in (_AUTORESEARCH, _AUTORESEARCH / "harness"):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)


def _stub(name: str, **attrs: object) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


# Minimal stubs so evaluate_variant can import without the full archive_index /
# frontier / lane_paths runtime.
_stub(
    "archive_index",
    append_lineage_entries=lambda *a, **k: None,
    append_lineage_entry=lambda *a, **k: None,
    current_variant_id=lambda *a, **k: None,
    load_json=lambda *a, **k: {},
    load_latest_lineage=lambda *a, **k: {},
    ordered_latest_entries=lambda *a, **k: [],
    refresh_archive_outputs=lambda *a, **k: None,
    summarize_variant_diff=lambda *a, **k: {},
)
_stub(
    "frontier",
    DOMAINS=("geo", "competitive", "monitoring", "storyboard"),
    has_search_metrics=lambda *a, **k: True,
    composite_score=lambda entry: 0.5,
    domain_score=lambda entry, lane: 0.5,
)
_stub(
    "lane_paths",
    WORKFLOW_LANES=(),
    normalize_lane=lambda x: x,
    path_owned_by_lane=lambda *a, **k: True,
)
