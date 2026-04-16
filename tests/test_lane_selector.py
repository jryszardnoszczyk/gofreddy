"""Tests for lane selector — pure function unit tests."""

import pytest

from src.analysis.lane_selector import AnalysisLane, score_transcript_quality, select_lane


class TestSelectLane:
    """Tests for select_lane() — all branch combinations."""

    def test_flag_disabled_always_l2(self):
        """Flag disabled: always L2 regardless of transcript."""
        assert select_lane(
            transcript_available=True,
            transcript_quality=1.0,
            quality_threshold=0.6,
            flag_enabled=False,
        ) == AnalysisLane.L2_MULTIMODAL_AUDIO

    def test_flag_enabled_high_quality_routes_l1(self):
        """Flag enabled + high quality transcript: routes L1."""
        assert select_lane(
            transcript_available=True,
            transcript_quality=0.8,
            quality_threshold=0.6,
            flag_enabled=True,
        ) == AnalysisLane.L1_TRANSCRIPT_FIRST

    def test_flag_enabled_at_threshold_routes_l1(self):
        """Flag enabled + quality exactly at threshold: routes L1."""
        assert select_lane(
            transcript_available=True,
            transcript_quality=0.6,
            quality_threshold=0.6,
            flag_enabled=True,
        ) == AnalysisLane.L1_TRANSCRIPT_FIRST

    def test_flag_enabled_below_threshold_routes_l2(self):
        """Flag enabled + quality below threshold: routes L2."""
        assert select_lane(
            transcript_available=True,
            transcript_quality=0.5,
            quality_threshold=0.6,
            flag_enabled=True,
        ) == AnalysisLane.L2_MULTIMODAL_AUDIO

    def test_flag_enabled_no_transcript_routes_l2(self):
        """Flag enabled + no transcript: routes L2."""
        assert select_lane(
            transcript_available=False,
            transcript_quality=None,
            quality_threshold=0.6,
            flag_enabled=True,
        ) == AnalysisLane.L2_MULTIMODAL_AUDIO

    def test_flag_enabled_transcript_available_quality_none_routes_l2(self):
        """Flag enabled + transcript available but quality is None: routes L2."""
        assert select_lane(
            transcript_available=True,
            transcript_quality=None,
            quality_threshold=0.6,
            flag_enabled=True,
        ) == AnalysisLane.L2_MULTIMODAL_AUDIO


class TestScoreTranscriptQuality:
    """Tests for score_transcript_quality() — edge cases."""

    def test_empty_string_returns_zero(self):
        assert score_transcript_quality("") == 0.0

    def test_none_returns_zero(self):
        assert score_transcript_quality(None) == 0.0  # type: ignore[arg-type]

    def test_whitespace_only_returns_zero(self):
        assert score_transcript_quality("   \n\t  ") == 0.0

    def test_short_text_under_20_words_returns_zero(self):
        """Fewer than 20 words: quality 0."""
        text = " ".join(["word"] * 19)
        assert score_transcript_quality(text) == 0.0

    def test_exactly_20_words(self):
        """Exactly 20 words: quality = 20/200 = 0.1."""
        text = " ".join(["word"] * 20)
        assert score_transcript_quality(text) == 0.1

    def test_200_words_gives_max_quality(self):
        """200+ words: quality capped at 1.0."""
        text = " ".join(["word"] * 200)
        assert score_transcript_quality(text) == 1.0

    def test_300_words_still_capped_at_one(self):
        """300 words: still 1.0 (capped)."""
        text = " ".join(["word"] * 300)
        assert score_transcript_quality(text) == 1.0

    def test_100_words_gives_half(self):
        """100 words: quality = 100/200 = 0.5."""
        text = " ".join(["word"] * 100)
        assert score_transcript_quality(text) == 0.5

    def test_sparse_wps_penalty(self):
        """Very sparse transcript (wps < 0.5): quality halved."""
        text = " ".join(["word"] * 100)  # 100 words, base quality = 0.5
        # 100 words / 300 seconds = 0.33 wps → penalty 0.5
        result = score_transcript_quality(text, duration_seconds=300)
        assert result == 0.25  # 0.5 * 0.5

    def test_garbled_wps_penalty(self):
        """Garbled/noisy transcript (wps > 5.0): quality reduced."""
        text = " ".join(["word"] * 200)  # 200 words, base quality = 1.0
        # 200 words / 10 seconds = 20 wps → penalty 0.7
        result = score_transcript_quality(text, duration_seconds=10)
        assert result == 0.7  # 1.0 * 0.7

    def test_normal_wps_no_penalty(self):
        """Normal wps (0.5-5.0): no penalty."""
        text = " ".join(["word"] * 200)  # 200 words, base quality = 1.0
        # 200 words / 100 seconds = 2.0 wps → no penalty
        result = score_transcript_quality(text, duration_seconds=100)
        assert result == 1.0

    def test_zero_duration_no_penalty(self):
        """Duration = 0: no wps penalty (guard against division by zero)."""
        text = " ".join(["word"] * 100)
        result = score_transcript_quality(text, duration_seconds=0)
        assert result == 0.5

    def test_none_duration_no_penalty(self):
        """Duration = None: no wps penalty."""
        text = " ".join(["word"] * 100)
        result = score_transcript_quality(text, duration_seconds=None)
        assert result == 0.5

    def test_truncation_with_max_chars(self):
        """Transcript truncated at max_chars before scoring."""
        # Each "word " = 5 chars. 50 chars = 10 "word " = 10 words (< 20) → 0.0
        text = " ".join(["word"] * 100)  # 500+ chars
        result = score_transcript_quality(text, max_chars=50)
        assert result == 0.0


class TestLaneRoutingSettings:
    """Tests for LaneRoutingSettings defaults."""

    def test_defaults(self):
        from src.analysis.config import LaneRoutingSettings
        settings = LaneRoutingSettings()
        assert settings.transcript_first_enabled is True
        assert settings.quality_threshold == 0.6
