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
# NOTE: DOMAINS below is intentionally NOT migrated to read live LANES
# from autoresearch.lane_registry. The stub exists to isolate tests from the
# real frontier module; importing the registry would invert load ordering.
# Documented exception per
# docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md.
def _stub_entry_lane(entry):
    if not isinstance(entry, dict):
        return "core"
    raw = str(entry.get("lane") or "").strip().lower()
    return raw or "core"


def _stub_entry_active_for_lane(entry, lane):
    if not isinstance(entry, dict):
        return False
    metrics = entry.get("search_metrics")
    if isinstance(metrics, dict):
        domains = metrics.get("domains") or {}
        payload = domains.get(lane) or {}
        if isinstance(payload, dict) and payload.get("active"):
            return True
    return _stub_entry_lane(entry) == lane


_stub(
    "frontier",
    DOMAINS=("geo", "competitive", "monitoring", "storyboard", "marketing_audit"),
    has_search_metrics=lambda *a, **k: True,
    composite_score=lambda entry: 0.5,
    domain_score=lambda entry, lane: 0.5,
    entry_lane=_stub_entry_lane,
    entry_active_for_lane=_stub_entry_active_for_lane,
)
_stub(
    "lane_paths",
    WORKFLOW_LANES=(),
    normalize_lane=lambda x: x,
    path_owned_by_lane=lambda *a, **k: True,
)
