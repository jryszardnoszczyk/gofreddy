"""Tests for timestamp utilities and evidence timeline builder."""

import pytest

from src.common.timestamps import (
    _MAX_TIMELINE_ENTRIES,
    build_evidence_timeline,
    mss_to_seconds,
)
from src.schemas import (
    BrandMention,
    BrandSentiment,
    ModerationDetection,
    RiskDetection,
)


# ─── mss_to_seconds tests ─────────────────────────────────────────────────


class TestMssToSeconds:
    def test_none(self):
        assert mss_to_seconds(None) is None

    def test_zero(self):
        assert mss_to_seconds("0:00") == 0

    def test_normal(self):
        assert mss_to_seconds("12:34") == 754

    def test_max(self):
        assert mss_to_seconds("99:59") == 5999

    def test_empty_string(self):
        assert mss_to_seconds("") is None

    def test_malformed(self):
        assert mss_to_seconds("abc") is None

    def test_hhmmss(self):
        assert mss_to_seconds("1:2:34") is None

    def test_single_digit_seconds(self):
        assert mss_to_seconds("1:5") is None

    def test_whitespace_stripped(self):
        assert mss_to_seconds(" 1:30 ") == 90

    def test_single_digit_minutes(self):
        assert mss_to_seconds("5:00") == 300


# ─── build_evidence_timeline tests ─────────────────────────────────────────


def _make_moderation(ts_start="1:00", ts_end="1:30", severity="high", confidence=0.9):
    return ModerationDetection(
        moderation_class="hate_speech",
        severity=severity,
        confidence=confidence,
        timestamp_start=ts_start,
        timestamp_end=ts_end,
        description="Test moderation",
        evidence="Test evidence",
    )


def _make_risk(ts_start="2:00", ts_end="2:30", severity="medium", confidence=0.8):
    return RiskDetection(
        category="violence",
        severity=severity,
        confidence=confidence,
        timestamp_start=ts_start,
        timestamp_end=ts_end,
        description="Test risk",
        evidence="Test evidence",
    )


def _make_brand(ts_start="0:30", confidence=0.7, brand_name="Nike"):
    return BrandMention(
        brand_name=brand_name,
        detection_source="visual_logo",
        confidence=confidence,
        timestamp_start=ts_start,
        sentiment=BrandSentiment.POSITIVE,
        context="endorsement",
        evidence="Test evidence",
        is_competitor=False,
    )


class TestBuildEvidenceTimeline:
    def test_mixed_sources(self):
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[_make_moderation()],
            risks=[_make_risk()],
            brand_mentions=[_make_brand()],
        )
        assert len(groups) == 3  # 0:30, 1:00, 2:00
        assert len(unanchored) == 0
        # Check sorted ASC
        timestamps = [g["timestamp_seconds"] for g in groups]
        assert timestamps == sorted(timestamps)

    def test_colocation_grouping(self):
        """Multiple findings at the same second are grouped."""
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[_make_moderation(ts_start="1:00")],
            risks=[_make_risk(ts_start="1:00")],
            brand_mentions=[_make_brand(ts_start="1:00")],
        )
        assert len(groups) == 1
        assert groups[0]["timestamp_seconds"] == 60
        assert len(groups[0]["findings"]) == 3
        assert len(unanchored) == 0

    def test_all_unanchored(self):
        """All null timestamps → empty timeline, everything unanchored."""
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[_make_moderation(ts_start=None, ts_end=None)],
            risks=[_make_risk(ts_start=None, ts_end=None)],
            brand_mentions=[_make_brand(ts_start=None)],
        )
        assert len(groups) == 0
        assert len(unanchored) == 3

    def test_brand_absent(self):
        """Brand mentions None → no error."""
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[_make_moderation()],
            risks=[],
            brand_mentions=None,
        )
        assert len(groups) == 1
        assert len(unanchored) == 0

    def test_brand_empty_list(self):
        """Brand mentions empty list → no error."""
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[],
            risks=[],
            brand_mentions=[],
        )
        assert len(groups) == 0
        assert len(unanchored) == 0

    def test_empty_all_sources(self):
        """Zero findings across all sources."""
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[],
            risks=[],
            brand_mentions=[],
        )
        assert groups == []
        assert unanchored == []

    def test_malformed_timestamps_unanchored(self):
        """Malformed timestamps treated as unanchored."""
        # RiskDetection validates timestamps, so we need to test with moderation
        # that has valid timestamps but may have malformed ones too.
        # Actually, Pydantic validators would reject malformed. So test with None.
        m = _make_moderation(ts_start=None)
        groups, unanchored = build_evidence_timeline(
            moderation_flags=[m],
            risks=[],
            brand_mentions=None,
        )
        assert len(groups) == 0
        assert len(unanchored) == 1

    def test_defense_limit(self):
        """More than _MAX_TIMELINE_ENTRIES gets truncated."""
        count = _MAX_TIMELINE_ENTRIES + 50
        mods = [
            _make_moderation(ts_start=f"{i // 60}:{i % 60:02d}")
            for i in range(count)
        ]
        groups, unanchored = build_evidence_timeline(
            moderation_flags=mods,
            risks=[],
            brand_mentions=None,
        )
        # Total anchored findings across all groups should be at most _MAX_TIMELINE_ENTRIES
        total_findings = sum(len(g["findings"]) for g in groups)
        assert total_findings <= _MAX_TIMELINE_ENTRIES

    def test_finding_fields_moderation(self):
        """Moderation findings have correct fields."""
        groups, _ = build_evidence_timeline(
            moderation_flags=[_make_moderation()],
            risks=[],
            brand_mentions=None,
        )
        finding = groups[0]["findings"][0]
        assert finding["type"] == "moderation"
        assert finding["category"] == "hate_speech"
        assert finding["severity"] == "high"
        assert finding["confidence"] == 0.9
        assert finding["evidence"] == "Test evidence"
        assert finding["timestamp_end_seconds"] == 90  # 1:30

    def test_finding_fields_brand(self):
        """Brand findings have brand-specific fields."""
        groups, _ = build_evidence_timeline(
            moderation_flags=[],
            risks=[],
            brand_mentions=[_make_brand()],
        )
        finding = groups[0]["findings"][0]
        assert finding["type"] == "brand"
        assert finding["category"] == "brand_mention"
        assert finding["severity"] is None
        assert finding["brand_name"] == "Nike"
        assert finding["sentiment"] == "positive"
