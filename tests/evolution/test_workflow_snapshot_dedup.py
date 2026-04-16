"""Tests for snapshot_evaluations freshness dedup across 3 workflows (Unit 1)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from autoresearch.archive.v001.workflows.competitive import snapshot_evaluations as competitive_snapshot
from autoresearch.archive.v001.workflows.storyboard import snapshot_evaluations as storyboard_snapshot
from autoresearch.archive.v001.workflows.monitoring import snapshot_evaluations as monitoring_snapshot


# --- Competitive workflow ---

class TestCompetitiveSnapshotDedup:
    def test_fresh_eval_reused(self, tmp_path: Path) -> None:
        """eval_feedback.json newer than brief.md → evaluator NOT re-called."""
        session_dir = tmp_path
        artifact = session_dir / "brief.md"
        artifact.write_text("# Brief")
        time.sleep(0.01)  # Ensure mtime ordering
        eval_path = session_dir / "eval_feedback.json"
        eval_path.write_text(json.dumps({"decision": "KEEP", "reason": "test"}))

        evaluator = MagicMock()
        result = competitive_snapshot(session_dir, evaluator)

        evaluator.assert_not_called()
        assert result == {"brief_decision": "KEEP"}

    def test_missing_eval_runs_evaluator(self, tmp_path: Path) -> None:
        """eval_feedback.json missing → evaluator called normally."""
        session_dir = tmp_path
        (session_dir / "brief.md").write_text("# Brief")

        evaluator = MagicMock(return_value={"decision": "REWORK"})
        result = competitive_snapshot(session_dir, evaluator)

        evaluator.assert_called_once()
        assert result == {"brief_decision": "REWORK"}

    def test_stale_eval_reruns(self, tmp_path: Path) -> None:
        """Artifact regenerated after eval (rework) → eval stale → re-evaluated."""
        session_dir = tmp_path
        eval_path = session_dir / "eval_feedback.json"
        eval_path.write_text(json.dumps({"decision": "KEEP"}))
        time.sleep(0.01)
        artifact = session_dir / "brief.md"
        artifact.write_text("# Updated brief")

        evaluator = MagicMock(return_value={"decision": "REWORK"})
        result = competitive_snapshot(session_dir, evaluator)

        evaluator.assert_called_once()
        assert result == {"brief_decision": "REWORK"}

    def test_invalid_json_reruns(self, tmp_path: Path) -> None:
        """eval_feedback.json with invalid JSON → evaluator re-called."""
        session_dir = tmp_path
        artifact = session_dir / "brief.md"
        artifact.write_text("# Brief")
        time.sleep(0.01)
        eval_path = session_dir / "eval_feedback.json"
        eval_path.write_text("not valid json{{{")

        evaluator = MagicMock(return_value={"decision": "KEEP"})
        result = competitive_snapshot(session_dir, evaluator)

        evaluator.assert_called_once()

    def test_missing_decision_reruns(self, tmp_path: Path) -> None:
        """eval exists but no 'decision' field → evaluator re-called."""
        session_dir = tmp_path
        artifact = session_dir / "brief.md"
        artifact.write_text("# Brief")
        time.sleep(0.01)
        eval_path = session_dir / "eval_feedback.json"
        eval_path.write_text(json.dumps({"reason": "test", "results": []}))

        evaluator = MagicMock(return_value={"decision": "KEEP"})
        result = competitive_snapshot(session_dir, evaluator)

        evaluator.assert_called_once()


# --- Storyboard workflow ---

class TestStoryboardSnapshotDedup:
    def test_fresh_eval_skips_story(self, tmp_path: Path) -> None:
        """Fresh eval for one story, missing for another → only missing one evaluated."""
        session_dir = tmp_path
        stories_dir = session_dir / "stories"
        stories_dir.mkdir()
        eval_dir = session_dir / "evals"
        eval_dir.mkdir()

        # Story A: has fresh eval
        story_a = stories_dir / "a.json"
        story_a.write_text(json.dumps({"story": "A"}))
        time.sleep(0.01)
        eval_a = eval_dir / "story-a.json"
        eval_a.write_text(json.dumps({"decision": "KEEP"}))

        # Story B: no eval
        story_b = stories_dir / "b.json"
        story_b.write_text(json.dumps({"story": "B"}))

        evaluator = MagicMock(return_value={"decision": "REWORK"})
        result = storyboard_snapshot(session_dir, evaluator)

        # Only story B should trigger evaluator
        assert evaluator.call_count == 1
        decisions = result["story_decisions"]
        assert len(decisions) == 2
        assert decisions[0] == {"artifact": "a.json", "decision": "KEEP"}
        assert decisions[1] == {"artifact": "b.json", "decision": "REWORK"}

    def test_all_fresh_no_evaluator_calls(self, tmp_path: Path) -> None:
        """All stories have fresh evals → no evaluator calls."""
        session_dir = tmp_path
        stories_dir = session_dir / "stories"
        stories_dir.mkdir()
        eval_dir = session_dir / "evals"
        eval_dir.mkdir()

        story = stories_dir / "x.json"
        story.write_text(json.dumps({"story": "X"}))
        time.sleep(0.01)
        eval_x = eval_dir / "story-x.json"
        eval_x.write_text(json.dumps({"decision": "KEEP"}))

        evaluator = MagicMock()
        result = storyboard_snapshot(session_dir, evaluator)

        evaluator.assert_not_called()
        assert result["story_decisions"] == [{"artifact": "x.json", "decision": "KEEP"}]


# --- Monitoring workflow ---

class TestMonitoringSnapshotDedup:
    def test_fresh_story_eval_skipped(self, tmp_path: Path) -> None:
        """Fresh per-story eval + stale digest → story skipped, digest evaluated."""
        session_dir = tmp_path
        synth_dir = session_dir / "synthesized"
        synth_dir.mkdir()
        eval_dir = session_dir / "evals"
        eval_dir.mkdir()

        story = synth_dir / "s1.md"
        story.write_text("# Story 1")
        time.sleep(0.01)
        eval_s1 = eval_dir / "story-s1.json"
        eval_s1.write_text(json.dumps({"decision": "KEEP"}))

        # Digest with no eval
        digest = session_dir / "digest.md"
        digest.write_text("# Digest")

        evaluator = MagicMock(return_value={"decision": "KEEP"})
        result = monitoring_snapshot(session_dir, evaluator)

        # Only digest should trigger evaluator (per-story was fresh)
        assert evaluator.call_count == 1
        assert result["story_decisions"] == [{"artifact": "s1.md", "decision": "KEEP"}]
        assert result["digest_decision"] == "KEEP"

    def test_fresh_digest_eval_reused(self, tmp_path: Path) -> None:
        """All evals fresh → no evaluator calls at all."""
        session_dir = tmp_path
        synth_dir = session_dir / "synthesized"
        synth_dir.mkdir()
        eval_dir = session_dir / "evals"
        eval_dir.mkdir()

        story = synth_dir / "s1.md"
        story.write_text("# Story 1")
        time.sleep(0.01)
        eval_s1 = eval_dir / "story-s1.json"
        eval_s1.write_text(json.dumps({"decision": "KEEP"}))

        digest = session_dir / "digest.md"
        digest.write_text("# Digest")
        time.sleep(0.01)
        digest_eval = session_dir / "digest_eval.json"
        digest_eval.write_text(json.dumps({"decision": "KEEP"}))

        evaluator = MagicMock()
        result = monitoring_snapshot(session_dir, evaluator)

        evaluator.assert_not_called()
        assert result["digest_decision"] == "KEEP"

    def test_rework_triggers_reevaluation(self, tmp_path: Path) -> None:
        """Artifact regenerated after eval → stale eval → re-evaluated."""
        session_dir = tmp_path
        synth_dir = session_dir / "synthesized"
        synth_dir.mkdir()
        eval_dir = session_dir / "evals"
        eval_dir.mkdir()

        eval_s1 = eval_dir / "story-s1.json"
        eval_s1.write_text(json.dumps({"decision": "KEEP"}))
        time.sleep(0.01)
        story = synth_dir / "s1.md"
        story.write_text("# Regenerated story")

        digest = session_dir / "digest.md"
        digest.write_text("# Digest")

        evaluator = MagicMock(return_value={"decision": "REWORK"})
        result = monitoring_snapshot(session_dir, evaluator)

        # Both story (stale eval) and digest (no eval) should be evaluated
        assert evaluator.call_count == 2
