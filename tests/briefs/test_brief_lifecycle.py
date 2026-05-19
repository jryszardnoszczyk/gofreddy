"""End-to-end findings-brief lifecycle integration (U4).

Per plan U4 file list: test_brief_lifecycle.py covers the emit → read
round trip + multi-source consumer pattern in a single integration
harness, separate from the schema/emitter/reader unit tests in
test_emitter_reader.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.briefs.emitter import emit_brief
from src.briefs.reader import read_briefs
from src.briefs.schema import FindingsBrief, priority_sort_key


def _build_brief(
    brief_id: str,
    source_lane: str,
    priority: str,
    target_lanes: list[str],
) -> FindingsBrief:
    return FindingsBrief.model_validate({
        "brief_id": brief_id,
        "source_lane": source_lane,
        "priority": priority,
        "topic_title": f"{source_lane.upper()} fixture topic {brief_id}",
        "topic_summary": "Two-sentence summary for the consumer.",
        "target_lanes": target_lanes,
        "source_pointers": [f"autoresearch/archive_{source_lane}/v042/sessions/{brief_id}"],
        "success_notes": "1500-word article; cite source pointer.",
        "produced_at": datetime.now(timezone.utc).isoformat(),
    })


def test_emit_then_read_round_trip(tmp_path: Path) -> None:
    """Plan U4 happy path: emit brief → file exists in expected path →
    read returns identical brief."""
    archive_root = tmp_path / "archive_geo" / "v042"

    original = _build_brief(
        brief_id="geo-schrems-ii-saas",
        source_lane="geo",
        priority="high",
        target_lanes=["article_engine"],
    )

    written_path = emit_brief(original, archive_root)
    assert written_path.is_file()

    result = read_briefs("geo", archive_root)
    assert len(result) == 1
    roundtrip = result[0]

    assert roundtrip.brief_id == original.brief_id
    assert roundtrip.priority == original.priority
    assert roundtrip.target_lanes == original.target_lanes
    assert roundtrip.topic_title == original.topic_title
    assert roundtrip.source_pointers == original.source_pointers


def test_emit_5_briefs_mixed_priorities_read_returns_priority_sorted(
    tmp_path: Path,
) -> None:
    """Plan U4 happy path: emit 5 briefs with mixed priorities → reader
    returns them sorted high → medium → low."""
    archive_root = tmp_path / "archive_geo" / "v042"

    priorities = ["low", "high", "medium", "low", "high"]
    for i, prio in enumerate(priorities):
        emit_brief(
            _build_brief(
                brief_id=f"geo-{i}", source_lane="geo",
                priority=prio, target_lanes=["article_engine"],
            ),
            archive_root,
        )

    result = read_briefs("geo", archive_root)
    assert [b.priority for b in result] == ["high", "high", "medium", "low", "low"]


def test_two_source_lanes_consumer_pattern(tmp_path: Path) -> None:
    """Plan U4 integration: two source lanes (geo + monitoring) both
    emit; consumer reads from both, merges by priority.

    Per TD-56: the consumer's merge is a 5-line call site, NOT a
    shared `read_briefs_merged()` API. This test pins the pattern."""
    geo_root = tmp_path / "archive_geo" / "v042"
    monitoring_root = tmp_path / "archive_monitoring" / "v007"

    emit_brief(_build_brief(
        brief_id="geo-seo-1", source_lane="geo",
        priority="medium", target_lanes=["article_engine"],
    ), geo_root)
    emit_brief(_build_brief(
        brief_id="monitoring-regulatory-1", source_lane="monitoring",
        priority="high", target_lanes=["article_engine"],
    ), monitoring_root)
    emit_brief(_build_brief(
        brief_id="monitoring-news-2", source_lane="monitoring",
        priority="low", target_lanes=["article_engine"],
    ), monitoring_root)

    # Consumer pattern (~5 lines, no shared API):
    geo_briefs = read_briefs("geo", geo_root)
    monitoring_briefs = read_briefs("monitoring", monitoring_root)
    merged = sorted([*geo_briefs, *monitoring_briefs], key=priority_sort_key)

    assert [b.brief_id for b in merged] == [
        "monitoring-regulatory-1",  # high
        "geo-seo-1",                # medium
        "monitoring-news-2",        # low
    ]


def test_consumer_top_k_filter_applies_after_merge(tmp_path: Path) -> None:
    """Plan U4 integration: top-K filter applied by consumer (article_engine
    reads ClientConfig.brief_consumption.top_k_per_run). Test pins the
    consumer-side top-K shape."""
    archive_root = tmp_path / "archive_geo" / "v042"

    for i in range(10):
        emit_brief(_build_brief(
            brief_id=f"geo-{i:02d}", source_lane="geo",
            priority="high" if i < 5 else "medium",
            target_lanes=["article_engine"],
        ), archive_root)

    all_briefs = read_briefs("geo", archive_root)
    assert len(all_briefs) == 10

    top_k = all_briefs[:3]
    assert all(b.priority == "high" for b in top_k)
