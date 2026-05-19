"""Findings-brief schema + emitter + reader unit tests (U4).

Test policy:
- Schema-level tests live here alongside emitter + reader unit tests.
- End-to-end lifecycle integration lives in test_brief_lifecycle.py
  per the plan U4 file list.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.briefs.emitter import emit_brief
from src.briefs.reader import read_briefs
from src.briefs.schema import FindingsBrief, priority_sort_key


# ---------------------------------------------------------------------------
# Schema validators
# ---------------------------------------------------------------------------


def _minimal_brief_dict(**overrides) -> dict:
    base = {
        "brief_id": "geo-fixture-topic-20260518",
        "source_lane": "geo",
        "priority": "high",
        "topic_title": "Schrems-II implications for SaaS data transfers",
        "topic_summary": "EDPB published clarifying guidance.",
        "target_lanes": ["article_engine"],
        "target_formats": {"article_engine": "blog"},
        "source_pointers": [],
        "success_notes": "1500-2200 words; cite the EDPB guidelines.",
        "produced_at": "2026-05-18T10:00:00+00:00",
    }
    base.update(overrides)
    return base


def test_minimal_brief_constructs() -> None:
    brief = FindingsBrief.model_validate(_minimal_brief_dict())
    assert brief.brief_id == "geo-fixture-topic-20260518"
    assert brief.source_lane == "geo"
    assert brief.priority == "high"
    assert brief.target_lanes == ["article_engine"]
    assert brief.voice_persona_ref is None
    assert brief.valid_until is None
    # Per the 4-agent review (AC-4 T2-C): schema_version defaults to 1
    # so future v1.5+ readers can detect shape-stale briefs.
    assert brief.schema_version == 1


def test_brief_is_frozen() -> None:
    brief = FindingsBrief.model_validate(_minimal_brief_dict())
    with pytest.raises(ValidationError):
        brief.brief_id = "different"  # type: ignore[misc]


def test_brief_id_rejects_whitespace_and_empty() -> None:
    with pytest.raises(ValidationError):
        FindingsBrief.model_validate(_minimal_brief_dict(brief_id="has space"))
    with pytest.raises(ValidationError):
        FindingsBrief.model_validate(_minimal_brief_dict(brief_id=""))


def test_brief_priority_must_be_literal() -> None:
    with pytest.raises(ValidationError):
        FindingsBrief.model_validate(_minimal_brief_dict(priority="urgent"))


def test_brief_missing_required_field_raises() -> None:
    payload = _minimal_brief_dict()
    del payload["topic_title"]
    with pytest.raises(ValidationError) as exc:
        FindingsBrief.model_validate(payload)
    assert "topic_title" in str(exc.value)


def test_brief_priority_sort_key_orders_high_first() -> None:
    high = FindingsBrief.model_validate(_minimal_brief_dict(brief_id="a", priority="high"))
    medium = FindingsBrief.model_validate(_minimal_brief_dict(brief_id="b", priority="medium"))
    low = FindingsBrief.model_validate(_minimal_brief_dict(brief_id="c", priority="low"))

    sorted_briefs = sorted([low, medium, high], key=priority_sort_key)
    assert [b.priority for b in sorted_briefs] == ["high", "medium", "low"]


def test_brief_priority_sort_key_breaks_ties_by_produced_at() -> None:
    earlier = FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="a", priority="high", produced_at="2026-05-10T10:00:00+00:00",
    ))
    later = FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="b", priority="high", produced_at="2026-05-12T10:00:00+00:00",
    ))
    sorted_briefs = sorted([later, earlier], key=priority_sort_key)
    assert sorted_briefs[0].brief_id == "a"


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------


def test_emit_brief_writes_to_briefs_subdirectory(tmp_path: Path) -> None:
    brief = FindingsBrief.model_validate(_minimal_brief_dict())
    archive_root = tmp_path / "archive_geo" / "v042"

    written = emit_brief(brief, archive_root)

    assert written == archive_root / "briefs" / "geo-fixture-topic-20260518.json"
    assert written.is_file()
    payload = json.loads(written.read_text())
    assert payload["brief_id"] == brief.brief_id
    assert payload["priority"] == "high"


def test_emit_brief_creates_archive_root_if_missing(tmp_path: Path) -> None:
    brief = FindingsBrief.model_validate(_minimal_brief_dict())
    new_root = tmp_path / "does-not-exist-yet" / "v042"
    emit_brief(brief, new_root)
    assert (new_root / "briefs").is_dir()


def test_emit_brief_refuses_to_overwrite(tmp_path: Path) -> None:
    """D8 invariant: re-emitting the same brief_id indicates a callsite
    bug, not a legitimate update."""
    brief = FindingsBrief.model_validate(_minimal_brief_dict())
    archive_root = tmp_path / "archive_geo" / "v042"
    emit_brief(brief, archive_root)

    with pytest.raises(FileExistsError):
        emit_brief(brief, archive_root)


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------


def test_reader_returns_empty_for_missing_briefs_directory(tmp_path: Path) -> None:
    """Per D9 graceful degradation: consumer falls back to standalone."""
    archive_root = tmp_path / "archive_geo" / "v042"
    archive_root.mkdir(parents=True)
    result = read_briefs("geo", archive_root)
    assert result == []


def test_reader_returns_empty_for_empty_briefs_directory(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_geo" / "v042"
    (archive_root / "briefs").mkdir(parents=True)
    result = read_briefs("geo", archive_root)
    assert result == []


def test_reader_returns_priority_sorted(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_geo" / "v042"
    for priority in ["low", "high", "medium"]:
        brief = FindingsBrief.model_validate(_minimal_brief_dict(
            brief_id=f"geo-{priority}", priority=priority,
        ))
        emit_brief(brief, archive_root)

    result = read_briefs("geo", archive_root)
    assert [b.priority for b in result] == ["high", "medium", "low"]


def test_reader_skips_stale_briefs(tmp_path: Path) -> None:
    """Per D9: stale briefs (valid_until < now) logged + skipped."""
    archive_root = tmp_path / "archive_geo" / "v042"
    stale = FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="geo-stale",
        valid_until=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    ))
    fresh = FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="geo-fresh",
        valid_until=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    ))
    emit_brief(stale, archive_root)
    emit_brief(fresh, archive_root)

    result = read_briefs("geo", archive_root)
    assert [b.brief_id for b in result] == ["geo-fresh"]


def test_reader_keeps_briefs_without_valid_until_forever(tmp_path: Path) -> None:
    """Per D9: valid_until=None means the brief never stales."""
    archive_root = tmp_path / "archive_geo" / "v042"
    brief = FindingsBrief.model_validate(_minimal_brief_dict(brief_id="geo-eternal"))
    assert brief.valid_until is None
    emit_brief(brief, archive_root)
    result = read_briefs("geo", archive_root)
    assert len(result) == 1


def test_reader_skips_malformed_json_with_log(tmp_path: Path, caplog) -> None:
    archive_root = tmp_path / "archive_geo" / "v042"
    briefs_dir = archive_root / "briefs"
    briefs_dir.mkdir(parents=True)
    (briefs_dir / "broken.json").write_text("{ not valid json")

    valid = FindingsBrief.model_validate(_minimal_brief_dict(brief_id="geo-valid"))
    emit_brief(valid, archive_root)

    result = read_briefs("geo", archive_root)
    assert [b.brief_id for b in result] == ["geo-valid"]
    # Log warning is emitted but result is non-empty (graceful degradation)
    assert any("malformed brief" in rec.message for rec in caplog.records)


def test_reader_skips_briefs_missing_required_fields(tmp_path: Path, caplog) -> None:
    archive_root = tmp_path / "archive_geo" / "v042"
    briefs_dir = archive_root / "briefs"
    briefs_dir.mkdir(parents=True)
    # Brief payload with required fields missing.
    (briefs_dir / "incomplete.json").write_text(json.dumps({
        "brief_id": "geo-incomplete",
        "source_lane": "geo",
        # missing topic_title, topic_summary, target_lanes, priority, produced_at
    }))

    result = read_briefs("geo", archive_root)
    assert result == []
    assert any("schema violation" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Multi-source consumer pattern (no shared API surface per TD-56)
# ---------------------------------------------------------------------------


def test_consumer_unions_multiple_sources_via_priority_sort_key(tmp_path: Path) -> None:
    """Per TD-56: when a consumer needs >1 source lane, it calls
    read_briefs() twice and unions via priority_sort_key — no
    read_briefs_merged() shared infra. Test pins the consumer pattern
    so future callers (U15b site_engine) follow the right shape."""
    geo_root = tmp_path / "archive_geo" / "v042"
    audit_root = tmp_path / "archive_marketing_audit" / "v007"

    emit_brief(FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="geo-1", source_lane="geo", priority="medium",
    )), geo_root)
    emit_brief(FindingsBrief.model_validate(_minimal_brief_dict(
        brief_id="audit-1", source_lane="marketing_audit",
        priority="high", target_lanes=["site_engine"],
    )), audit_root)

    geo_briefs = read_briefs("geo", geo_root)
    audit_briefs = read_briefs("marketing_audit", audit_root)
    merged = sorted([*geo_briefs, *audit_briefs], key=priority_sort_key)

    # marketing_audit's high beats geo's medium
    assert [b.brief_id for b in merged] == ["audit-1", "geo-1"]
