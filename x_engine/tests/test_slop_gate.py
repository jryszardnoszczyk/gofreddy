"""Slop gate tests — banned phrases, em-dashes, parallel structure, n-gram dedup."""
from __future__ import annotations

from pathlib import Path

import pytest

from x_engine.pipeline import slop_gate


class TestBannedPhrases:
    def test_clean_text_passes(self):
        text = "I shipped a Claude Code skill that ranks tweets by resonance. 5 drafts a day."
        passed, flags = slop_gate.check_text(text)
        assert passed
        assert flags == []

    def test_most_people_blocked(self):
        text = "Most people don't realize how powerful agents are."
        passed, flags = slop_gate.check_text(text)
        assert not passed
        assert any("most people" in f.lower() for f in flags)

    def test_heres_the_thing_blocked(self):
        text = "Here's the thing about agents - they're tools."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_em_dash_blocked(self):
        text = "I shipped a thing — it works great."
        passed, flags = slop_gate.check_text(text)
        assert not passed
        assert "em_dash" in flags

    def test_en_dash_blocked(self):
        text = "I shipped a thing – it works great."
        passed, flags = slop_gate.check_text(text)
        assert not passed
        assert "em_dash" in flags

    def test_bookmark_this_blocked(self):
        text = "Great strategy. Bookmark this for later."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_hot_take_blocked(self):
        text = "Hot take: agents will replace prompts."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_breaking_emoji_blocked(self):
        text = "🚨 BREAKING: New Claude skill drops."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_dives_into_blocked(self):
        text = "This thread dives into the architecture."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_game_changer_blocked(self):
        text = "Claude skills are a real game-changer."
        passed, flags = slop_gate.check_text(text)
        assert not passed

    def test_legitimate_with_use_passes(self):
        # "use" is fine; we banned "leverage" and "utilize" but not "use"
        text = "Use Claude Code skills for repeatable marketing tasks."
        passed, flags = slop_gate.check_text(text)
        assert passed


class TestParallelPatterns:
    def test_not_x_y_reversal_blocked(self):
        text = "Not luck. Discipline."
        passed, flags = slop_gate.check_text(text)
        assert not passed
        assert any("parallel" in f for f in flags)

    def test_its_not_x_its_y_blocked(self):
        text = "It's not about prompts. It's about the harness around them."
        passed, flags = slop_gate.check_text(text)
        assert not passed


class TestNgramOverlap:
    def test_no_overlap_passes(self):
        text = "completely different content here"
        corpus = "this is a different set of words entirely"
        overlap = slop_gate.ngram_overlap(text, corpus, n=5)
        assert overlap == 0.0

    def test_full_overlap(self):
        text = "the quick brown fox jumps over"
        corpus = "the quick brown fox jumps over the lazy dog"
        overlap = slop_gate.ngram_overlap(text, corpus, n=5)
        assert overlap > 0.4  # at least one 5-gram matches

    def test_short_text_returns_zero(self):
        text = "two words"
        corpus = "many words here"
        overlap = slop_gate.ngram_overlap(text, corpus, n=5)
        assert overlap == 0.0


class TestExemplarsCheck:
    def test_with_exemplars_file(self, tmp_path):
        exemplars = tmp_path / "exemplars.md"
        exemplars.write_text("the quick brown fox jumps over the lazy dog")
        passed, overlap = slop_gate.check_against_exemplars(
            "totally different content here", exemplars
        )
        assert passed
        assert overlap == 0.0

    def test_high_overlap_blocks(self, tmp_path):
        exemplars = tmp_path / "exemplars.md"
        # Make exemplar text long enough to have 5-grams
        exemplars.write_text("I write 3 tweets a day across 4 accounts and I haven't typed myself")
        passed, overlap = slop_gate.check_against_exemplars(
            "I write 3 tweets a day across 4 accounts and I haven't typed myself", exemplars,
            threshold=0.20,
        )
        assert not passed
        assert overlap > 0.5

    def test_missing_file_passes(self, tmp_path):
        passed, overlap = slop_gate.check_against_exemplars("text", tmp_path / "missing.md")
        assert passed
        assert overlap == 0.0


class TestCheckFull:
    def test_clean_text(self, tmp_path):
        result = slop_gate.check_full("Clean specific text about Claude skills.")
        assert result["passed"]
        assert result["phrase_flags"] == []
        assert not result["ngram_blocked"]

    def test_phrase_violation(self, tmp_path):
        result = slop_gate.check_full("Most people don't realize this.")
        assert not result["passed"]
        assert len(result["phrase_flags"]) > 0
