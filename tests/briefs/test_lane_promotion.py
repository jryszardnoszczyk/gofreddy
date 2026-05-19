"""Promote-time brief emission for geo / monitoring / marketing_audit
(U9 / U10 / U10b).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.briefs.emitter import emit_brief
from src.briefs.lane_promotion import (
    emit_briefs_from_variant,
    make_brief_emitting_promote,
)
from src.briefs.reader import read_briefs
from src.briefs.schema import FindingsBrief, priority_sort_key


def _write_candidate(
    archive_dir: Path,
    variant_id: str,
    source_lane: str,
    client: str,
    candidates: list[dict],
) -> Path:
    """Write a synthetic brief_candidates.jsonl file at the expected path."""
    target = (
        archive_dir / variant_id / "sessions" / source_lane
        / client / "brief_candidates.jsonl"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(c) for c in candidates) + "\n")
    return target


def _ok_candidate(brief_id: str, source_lane: str = "geo") -> dict:
    return {
        "brief_id": brief_id,
        "source_lane": source_lane,
        "priority": "high",
        "topic_title": f"Topic for {brief_id}",
        "topic_summary": "Two-sentence test summary.",
        "target_lanes": ["article_engine"],
        "target_formats": {"article_engine": "blog"},
        "source_pointers": [f"sessions/{source_lane}/example"],
        "success_notes": "1500-word article with citations.",
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_emit_briefs_from_variant_round_trip(tmp_path: Path) -> None:
    """Per U9 happy path: agent writes candidates → custom_promote emits →
    reader sees them."""
    _write_candidate(
        tmp_path, "v042", "geo", "fixture-client",
        [_ok_candidate("geo-topic-001"), _ok_candidate("geo-topic-002")],
    )
    count = emit_briefs_from_variant(tmp_path, "v042", "geo")
    assert count == 2

    # Consumer reads from current_runtime/briefs (per D8 + the reader's
    # archive_root convention).
    briefs = read_briefs("geo", tmp_path / "current_runtime")
    assert len(briefs) == 2
    assert {b.brief_id for b in briefs} == {"geo-topic-001", "geo-topic-002"}


def test_no_candidate_file_returns_zero(tmp_path: Path) -> None:
    """Per U9 edge case: variant produced 0 brief-candidates → no briefs
    emitted, no error."""
    count = emit_briefs_from_variant(tmp_path, "v042", "geo")
    assert count == 0


def test_malformed_jsonl_lines_skipped(tmp_path: Path, caplog) -> None:
    """Per U9 edge case + D9 graceful degradation: malformed brief
    candidate JSONL is skipped with a log warning; promotion proceeds."""
    target = tmp_path / "v042" / "sessions" / "geo" / "client" / "brief_candidates.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(_ok_candidate("geo-good")) + "\n"
        "{not valid json\n"
        + json.dumps(_ok_candidate("geo-good-2")) + "\n"
    )
    import logging
    caplog.set_level(logging.WARNING)
    count = emit_briefs_from_variant(tmp_path, "v042", "geo")
    assert count == 2  # 2 valid; 1 malformed skipped
    assert any("malformed brief candidate" in rec.message for rec in caplog.records)


def test_schema_violation_skipped(tmp_path: Path, caplog) -> None:
    """Per U9 error path: candidate missing required field → skipped with
    log warning, not raised."""
    bad = _ok_candidate("geo-bad")
    del bad["topic_title"]  # required field
    _write_candidate(tmp_path, "v042", "geo", "client", [
        _ok_candidate("geo-good"),
        bad,
    ])
    import logging
    caplog.set_level(logging.WARNING)
    count = emit_briefs_from_variant(tmp_path, "v042", "geo")
    assert count == 1
    assert any("schema validation" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Multi-client variant (fixture sweep)
# ---------------------------------------------------------------------------


def test_emit_briefs_across_multiple_clients(tmp_path: Path) -> None:
    """A single variant may have run multiple fixtures in one sweep —
    each client's session dir contributes its own brief_candidates.jsonl."""
    _write_candidate(
        tmp_path, "v042", "geo", "klinika-melitus",
        [_ok_candidate("geo-klinika-1")],
    )
    _write_candidate(
        tmp_path, "v042", "geo", "dwf-poland",
        [_ok_candidate("geo-dwf-1")],
    )
    count = emit_briefs_from_variant(tmp_path, "v042", "geo")
    assert count == 2


# ---------------------------------------------------------------------------
# make_brief_emitting_promote (the custom_promote wrapper)
# ---------------------------------------------------------------------------


def test_promote_callable_returns_true_on_success(tmp_path: Path) -> None:
    """The custom_promote wrapper returns True so the substrate's
    promotion step proceeds."""
    _write_candidate(tmp_path, "v042", "geo", "client", [_ok_candidate("geo-1")])
    promote = make_brief_emitting_promote("geo")
    assert promote(tmp_path, "v042", "geo") is True


def test_promote_callable_returns_true_even_when_emission_fails(
    tmp_path: Path, monkeypatch,
) -> None:
    """Per the helper's docstring: brief-emission failure does NOT block
    promotion. A broken emitter shouldn't reject a legitimate variant."""
    def _boom(*args, **kwargs):
        raise RuntimeError("simulated emitter failure")

    monkeypatch.setattr(
        "src.briefs.lane_promotion.emit_briefs_from_variant", _boom,
    )
    promote = make_brief_emitting_promote("geo")
    assert promote(tmp_path, "v042", "geo") is True


def test_promote_callable_handles_path_or_str_archive_dir(tmp_path: Path) -> None:
    """Substrate may pass archive_dir as Path or str. The wrapper accepts
    both shapes."""
    _write_candidate(tmp_path, "v042", "geo", "client", [_ok_candidate("geo-x")])
    promote = make_brief_emitting_promote("geo")
    assert promote(str(tmp_path), "v042", "geo") is True
    # Re-emit same brief_id → second emit refused (FileExistsError → logged)
    assert promote(tmp_path, "v042", "geo") is True


# ---------------------------------------------------------------------------
# Lane registry wiring
# ---------------------------------------------------------------------------


def test_geo_monitoring_marketing_audit_have_custom_promote() -> None:
    """Per U9 + U10 + U10b: the 3 brief-emitting lanes have
    custom_promote wired by _wire_brief_emitting_lanes()."""
    from autoresearch.lane_registry import LANES
    for lane_name in ("geo", "monitoring", "marketing_audit"):
        spec = LANES[lane_name]
        assert spec.custom_promote is not None, f"{lane_name} missing custom_promote"


def test_storyboard_does_not_emit_briefs_via_promote() -> None:
    """Storyboard is a CONSUMER of briefs, not an emitter. Its
    custom_promote is the U8 format-mode reweighter (custom_score) — but
    NOT a brief-emitter."""
    from autoresearch.lane_registry import LANES
    storyboard = LANES["storyboard"]
    # custom_promote NOT wired (only the 3 source lanes get it).
    assert storyboard.custom_promote is None


# ---------------------------------------------------------------------------
# Sorted consumer pattern (full lifecycle)
# ---------------------------------------------------------------------------


def test_emit_then_priority_sort_lifecycle(tmp_path: Path) -> None:
    """End-to-end: agent writes mixed-priority candidates → emit → read
    returns priority-sorted list (high → medium → low)."""
    _write_candidate(
        tmp_path, "v042", "geo", "client",
        [
            {**_ok_candidate("geo-low"), "priority": "low"},
            {**_ok_candidate("geo-high"), "priority": "high"},
            {**_ok_candidate("geo-medium"), "priority": "medium"},
        ],
    )
    emit_briefs_from_variant(tmp_path, "v042", "geo")
    briefs = read_briefs("geo", tmp_path / "current_runtime")
    assert [b.priority for b in briefs] == ["high", "medium", "low"]
