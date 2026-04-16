"""Tests for results.jsonl caching in monitoring evaluator (Unit 2)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from autoresearch.archive.v001.workflows.session_eval_monitoring import (
    _get_results,
    _results_cache,
    clear_results_cache,
    structural_gate,
)


class TestResultsCache:
    def setup_method(self) -> None:
        clear_results_cache()

    def test_results_parsed_once(self, tmp_path: Path) -> None:
        """Multiple calls to _get_results for same session_dir return cached list."""
        results_file = tmp_path / "results.jsonl"
        results_file.write_text(
            json.dumps({"type": "select_mentions", "mentions_loaded": 50}) + "\n"
            + json.dumps({"type": "cluster_stories"}) + "\n"
        )

        first = _get_results(tmp_path)
        assert len(first) == 2

        # Modify file — cached result should still be returned
        results_file.write_text("")
        second = _get_results(tmp_path)
        assert second is first  # Same object reference

    def test_clear_cache(self, tmp_path: Path) -> None:
        """clear_results_cache removes entries."""
        results_file = tmp_path / "results.jsonl"
        results_file.write_text(json.dumps({"type": "test"}) + "\n")

        _get_results(tmp_path)
        assert str(tmp_path.resolve()) in _results_cache

        clear_results_cache(tmp_path)
        assert str(tmp_path.resolve()) not in _results_cache

    def test_empty_results(self, tmp_path: Path) -> None:
        """Empty results.jsonl returns empty list."""
        (tmp_path / "results.jsonl").write_text("")
        assert _get_results(tmp_path) == []

    def test_missing_file(self, tmp_path: Path) -> None:
        """Missing results.jsonl returns empty list."""
        assert _get_results(tmp_path) == []


class TestStructuralGateSinglePass:
    def setup_method(self) -> None:
        clear_results_cache()

    def test_grouped_by_type(self, tmp_path: Path) -> None:
        """Structural gate uses single-pass grouping and produces correct failures."""
        session_dir = tmp_path
        (session_dir / "session.md").write_text("## Status: COMPLETE")
        (session_dir / "digest.md").write_text("# Digest")
        (session_dir / "findings.md").write_text("# Findings")
        rec_dir = session_dir / "recommendations"
        rec_dir.mkdir()

        results_file = session_dir / "results.jsonl"
        results_file.write_text(
            json.dumps({"type": "select_mentions", "mentions_loaded": 100, "sources": 3}) + "\n"
            + json.dumps({"type": "cluster_stories"}) + "\n"
            + json.dumps({"type": "synthesize", "attempt": 1}) + "\n"
            + json.dumps({"type": "recommend", "status": "kept"}) + "\n"
        )

        # Create matching stories/synthesized
        stories_dir = session_dir / "stories"
        stories_dir.mkdir()
        (stories_dir / "story-1.json").write_text("{}")
        synth_dir = session_dir / "synthesized"
        synth_dir.mkdir()
        (synth_dir / "1.md").write_text("synth")

        # Recommendations required since has_rec=True
        (rec_dir / "executive_summary.md").write_text("summary")
        (rec_dir / "action_items.md").write_text("items")

        failures = structural_gate("full", session_dir / "digest.md", session_dir)
        assert failures == []

    def test_per_story_mode(self, tmp_path: Path) -> None:
        """Per-story mode does not touch results.jsonl."""
        artifact = tmp_path / "story.md"
        artifact.write_text("# Story content here")
        failures = structural_gate("per-story", artifact, tmp_path)
        assert failures == []
