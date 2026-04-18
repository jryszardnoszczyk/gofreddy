"""Tests for harness.prompts — prompt rendering and assembly logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.config import Config
from harness.prompts import (
    render_attempt_tracker_block,
    render_eval_prompt,
    render_fixer_prompt,
    render_grade_delta_block,
    render_scope_block,
    render_scope_override_banner,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides) -> Config:
    """Build a Config with test-friendly defaults, applying overrides."""
    defaults = dict(
        max_cycles=5,
        dry_run=False,
        engine="claude",
        eval_only=False,
        only=[],
        phase="all",
        skip=[],
        resume_branch="",
        resume_cycle=1,
        frontend_url="http://localhost:3001",
        backend_url="http://localhost:8080",
        max_fix_attempts=2,
    )
    defaults.update(overrides)
    return Config(**defaults)


# ---------------------------------------------------------------------------
# render_eval_prompt — cycle 1
# ---------------------------------------------------------------------------


class TestRenderEvalPromptCycle1:
    """Cycle 1 evaluator prompt assembly."""

    def test_contains_track_assignment(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "You are Evaluator Track A. Cycle: 1." in text

    def test_contains_scorecard_path(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Your scorecard path: /tmp/sc.md" in text

    def test_contains_base_prompt_content(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        # Check for known content from evaluator-base.md
        assert "You are a HOSTILE QA engineer" in text

    def test_contains_track_prompt_content(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        # Check for known content from evaluator-track-a.md
        assert "Track a Assignment" in text

    def test_contains_track_assignment_separator(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "--- YOUR TRACK ASSIGNMENT ---" in text

    def test_contains_frontend_url(self, tmp_path):
        config = _make_config(frontend_url="http://localhost:3010")
        prompt = render_eval_prompt("b", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Frontend URL: http://localhost:3010" in text
        assert "http://localhost:3010/dashboard?__e2e_auth=1" in text

    def test_contains_playwright_session_name(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("c", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Playwright session name: track-c" in text
        assert "-s=track-c" in text

    def test_scope_banner_present_when_phase_set(self, tmp_path):
        config = _make_config(phase="1")
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "MANDATORY SCOPE OVERRIDE" in text
        assert "TRACK A" in text

    def test_scope_block_present_when_only_set(self, tmp_path):
        config = _make_config(only=["A-1", "A-2"])
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "CAPABILITIES IN SCOPE" in text
        assert "HARNESS_ONLY" in text

    def test_returns_path_in_run_dir(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        assert prompt.parent == tmp_path
        assert prompt.suffix == ".md"


# ---------------------------------------------------------------------------
# render_eval_prompt — cycle 2+
# ---------------------------------------------------------------------------


class TestRenderEvalPromptCycle2:
    """Cycle 2+ re-evaluation prompt assembly."""

    def test_contains_reevaluation_header(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Cycle 2" in text
        assert "Re-evaluation" in text

    def test_contains_continuing_track(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("b", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "You are continuing as Evaluator Track B." in text

    def test_contains_previous_fixes_when_present(self, tmp_path):
        config = _make_config()
        # Place a mock fixes report in run_dir
        fixes = tmp_path / "fixes-1.md"
        fixes.write_text("Mock fixer report content\n", encoding="utf-8")
        prompt = render_eval_prompt("a", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "The fixer applied changes" in text
        assert "Mock fixer report content" in text

    def test_no_fixer_report_message_when_absent(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "No fixer report found for cycle 1." in text

    def test_contains_previous_scorecard_when_present(self, tmp_path):
        config = _make_config()
        sc = tmp_path / "scorecard-1-track-a.md"
        sc.write_text("Previous scorecard yaml\n", encoding="utf-8")
        prompt = render_eval_prompt("a", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Your previous scorecard" in text
        assert "Previous scorecard yaml" in text

    def test_contains_retest_instructions(self, tmp_path):
        config = _make_config()
        prompt = render_eval_prompt("a", 2, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "Re-test ALL capabilities" in text
        assert "FAIL or PARTIAL" in text
        assert "no regressions" in text
        assert "BLOCKED" in text


# ---------------------------------------------------------------------------
# render_fixer_prompt
# ---------------------------------------------------------------------------


class TestRenderFixerPrompt:
    """Fixer prompt assembly."""

    def test_contains_cycle_and_paths(self, tmp_path):
        config = _make_config()
        prompt = render_fixer_prompt(
            1, "/tmp/merged.md", "/tmp/fixes.md", config, tmp_path
        )
        text = prompt.read_text(encoding="utf-8")
        assert "Cycle: 1" in text
        assert "Merged scorecard: /tmp/merged.md" in text
        assert "Fixes report path: /tmp/fixes.md" in text

    def test_contains_fixer_prompt_content(self, tmp_path):
        config = _make_config()
        prompt = render_fixer_prompt(
            1, "/tmp/merged.md", "/tmp/fixes.md", config, tmp_path
        )
        text = prompt.read_text(encoding="utf-8")
        # Check for known content from fixer.md
        assert "QA Fixer Agent" in text

    def test_first_cycle_note(self, tmp_path):
        config = _make_config()
        prompt = render_fixer_prompt(
            1, "/tmp/merged.md", "/tmp/fixes.md", config, tmp_path
        )
        text = prompt.read_text(encoding="utf-8")
        assert "first cycle" in text

    def test_previous_fixes_referenced_cycle2(self, tmp_path):
        config = _make_config()
        # Place a cycle-1 fixes report
        fixes1 = tmp_path / "fixes-1.md"
        fixes1.write_text(
            "---\ncycle: 1\nfindings_addressed: [A-1]\n---\n",
            encoding="utf-8",
        )
        prompt = render_fixer_prompt(
            2, "/tmp/merged.md", "/tmp/fixes.md", config, tmp_path
        )
        text = prompt.read_text(encoding="utf-8")
        assert "Previous cycle fixes report:" in text
        assert str(fixes1) in text

    def test_grade_delta_present_when_prev_merged_exists(self, tmp_path):
        config = _make_config()
        # Create previous and current merged scorecards
        prev = tmp_path / "scorecard-1-merged.md"
        prev.write_text(
            "---\ncycle: 1\npass: 1\npartial: 0\nfail: 1\nblocked: 0\n"
            "findings:\n"
            "  - id: A-1\n    capability: test\n    grade: PASS\n"
            "    summary: ok\n"
            "  - id: A-2\n    capability: test2\n    grade: FAIL\n"
            "    summary: broken\n"
            "---\n",
            encoding="utf-8",
        )
        curr = tmp_path / "scorecard-2-merged.md"
        curr.write_text(
            "---\ncycle: 2\npass: 2\npartial: 0\nfail: 0\nblocked: 0\n"
            "findings:\n"
            "  - id: A-1\n    capability: test\n    grade: PASS\n"
            "    summary: ok\n"
            "  - id: A-2\n    capability: test2\n    grade: PASS\n"
            "    summary: fixed\n"
            "---\n",
            encoding="utf-8",
        )
        # Also need a fixes-1 so cycle 2 has something to parse
        (tmp_path / "fixes-1.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-2]\n---\n",
            encoding="utf-8",
        )

        prompt = render_fixer_prompt(
            2,
            str(curr),
            "/tmp/fixes-2.md",
            config,
            tmp_path,
            full_merged_path=str(curr),
        )
        text = prompt.read_text(encoding="utf-8")
        assert "Grade Delta" in text
        assert "IMPROVED" in text

    def test_full_merged_path_shown_when_different(self, tmp_path):
        config = _make_config()
        prompt = render_fixer_prompt(
            1,
            "/tmp/capped.md",
            "/tmp/fixes.md",
            config,
            tmp_path,
            full_merged_path="/tmp/full-merged.md",
        )
        text = prompt.read_text(encoding="utf-8")
        assert "Full merged scorecard (READ ONLY): /tmp/full-merged.md" in text

    def test_scoped_fixer_header(self, tmp_path):
        config = _make_config()
        prompt = render_fixer_prompt(
            1,
            "/tmp/merged.md",
            "/tmp/fixes.md",
            config,
            tmp_path,
            scope_ids="A-1,A-2",
        )
        text = prompt.read_text(encoding="utf-8")
        assert "SCOPED FIXER" in text
        assert "A-1,A-2" in text


# ---------------------------------------------------------------------------
# render_scope_block
# ---------------------------------------------------------------------------


class TestRenderScopeBlock:
    """Scope block rendering."""

    def test_all_phase_no_skip_no_only_returns_empty(self):
        config = _make_config(phase="all", skip=[], only=[])
        assert render_scope_block(config) == ""

    def test_phase_set_includes_caps(self):
        config = _make_config(phase="1")
        block = render_scope_block(config)
        assert "CAPABILITIES IN SCOPE" in block
        assert "PHASE=1" in block
        # Phase 1 from test-matrix.md: [A1, A12, B1, B16, C7, C12]
        assert "A-1" in block

    def test_only_set_includes_ids(self):
        config = _make_config(only=["A-5", "B-4"])
        block = render_scope_block(config)
        assert "HARNESS_ONLY=A-5,B-4" in block
        assert "test ONLY" in block

    def test_skip_set_includes_skip_ids(self):
        config = _make_config(skip=["A-1"], phase="1")
        block = render_scope_block(config)
        assert "HARNESS_SKIP=A-1" in block
        assert "do NOT test these IDs" in block


# ---------------------------------------------------------------------------
# render_scope_override_banner
# ---------------------------------------------------------------------------


class TestRenderScopeOverrideBanner:
    """Scope override banner rendering."""

    def test_no_scope_returns_empty(self):
        config = _make_config()
        assert render_scope_override_banner("a", config) == ""

    def test_includes_track_letter(self):
        config = _make_config(phase="1")
        banner = render_scope_override_banner("a", config)
        assert "TRACK A" in banner

    def test_includes_scope_source(self):
        config = _make_config(phase="1")
        banner = render_scope_override_banner("a", config)
        assert "PHASE=1" in banner

    def test_only_scope_source(self):
        config = _make_config(only=["A-1"])
        banner = render_scope_override_banner("a", config)
        assert "HARNESS_ONLY=A-1" in banner

    def test_skip_included_in_banner(self):
        config = _make_config(phase="1", skip=["A-1"])
        banner = render_scope_override_banner("a", config)
        assert "HARNESS_SKIP=A-1" in banner

    def test_zero_caps_track(self):
        """Track with zero in-scope caps gets empty-scorecard message."""
        # Phase 1 is [A1, A12, B1, B16, C7, C12] — track b has [A5..A11],
        # none of which are in phase 1
        config = _make_config(phase="1")
        banner = render_scope_override_banner("b", config)
        assert "TRACK B" in banner
        assert "ZERO in-scope caps" in banner


# ---------------------------------------------------------------------------
# render_grade_delta_block
# ---------------------------------------------------------------------------


class TestRenderGradeDeltaBlock:
    """Grade delta table rendering."""

    def test_both_files_missing_returns_empty(self, tmp_path):
        result = render_grade_delta_block(
            tmp_path / "nonexistent1.md",
            tmp_path / "nonexistent2.md",
        )
        assert result == ""

    def test_prev_missing_returns_empty(self, tmp_path):
        curr = tmp_path / "curr.md"
        curr.write_text(
            "---\ncycle: 2\nfindings:\n  - id: A-1\n    capability: t\n"
            "    grade: PASS\n    summary: ok\n---\n",
            encoding="utf-8",
        )
        result = render_grade_delta_block(tmp_path / "nope.md", curr)
        assert result == ""

    def test_improved_finding(self, tmp_path):
        prev = tmp_path / "prev.md"
        prev.write_text(
            "---\ncycle: 1\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: FAIL\n    summary: bad\n"
            "---\n",
            encoding="utf-8",
        )
        curr = tmp_path / "curr.md"
        curr.write_text(
            "---\ncycle: 2\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "---\n",
            encoding="utf-8",
        )
        result = render_grade_delta_block(prev, curr)
        assert "IMPROVED" in result
        assert "A-1" in result
        assert "Grade Delta" in result

    def test_regressed_finding(self, tmp_path):
        prev = tmp_path / "prev.md"
        prev.write_text(
            "---\ncycle: 1\nfindings:\n"
            "  - id: B-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "---\n",
            encoding="utf-8",
        )
        curr = tmp_path / "curr.md"
        curr.write_text(
            "---\ncycle: 2\nfindings:\n"
            "  - id: B-1\n    capability: t\n    grade: FAIL\n    summary: broke\n"
            "---\n",
            encoding="utf-8",
        )
        result = render_grade_delta_block(prev, curr)
        assert "REGRESSED" in result

    def test_unchanged_finding(self, tmp_path):
        prev = tmp_path / "prev.md"
        prev.write_text(
            "---\ncycle: 1\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "---\n",
            encoding="utf-8",
        )
        curr = tmp_path / "curr.md"
        curr.write_text(
            "---\ncycle: 2\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "---\n",
            encoding="utf-8",
        )
        result = render_grade_delta_block(prev, curr)
        assert "unchanged" in result

    def test_new_finding(self, tmp_path):
        prev = tmp_path / "prev.md"
        prev.write_text(
            "---\ncycle: 1\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "---\n",
            encoding="utf-8",
        )
        curr = tmp_path / "curr.md"
        curr.write_text(
            "---\ncycle: 2\nfindings:\n"
            "  - id: A-1\n    capability: t\n    grade: PASS\n    summary: ok\n"
            "  - id: B-1\n    capability: t2\n    grade: FAIL\n    summary: new\n"
            "---\n",
            encoding="utf-8",
        )
        result = render_grade_delta_block(prev, curr)
        assert "NEW" in result
        assert "B-1" in result


# ---------------------------------------------------------------------------
# render_attempt_tracker_block
# ---------------------------------------------------------------------------


class TestRenderAttemptTrackerBlock:
    """Attempt tracker block rendering."""

    def test_cycle_1_returns_empty(self, tmp_path):
        assert render_attempt_tracker_block(1, tmp_path, 2) == ""

    def test_no_previous_fixes_returns_empty(self, tmp_path):
        assert render_attempt_tracker_block(2, tmp_path, 2) == ""

    def test_single_attempt_shows_attempt_count(self, tmp_path):
        # Create fixes-1.md
        (tmp_path / "fixes-1.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-1, B-2]\n---\n",
            encoding="utf-8",
        )
        result = render_attempt_tracker_block(2, tmp_path, 2)
        assert "Finding attempt tracker" in result
        assert "`A-1`" in result
        assert "`B-2`" in result
        assert "attempt 2 of 2" in result

    def test_escalated_finding(self, tmp_path):
        # Finding attempted in cycles 1 and 2 → escalated at cycle 3
        (tmp_path / "fixes-1.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-8]\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "fixes-2.md").write_text(
            "---\ncycle: 2\nfindings_addressed: [A-8]\n---\n",
            encoding="utf-8",
        )
        result = render_attempt_tracker_block(3, tmp_path, 2)
        assert "ALREADY ESCALATED" in result
        assert "`A-8`" in result

    def test_mixed_escalated_and_active(self, tmp_path):
        (tmp_path / "fixes-1.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-1, B-2]\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "fixes-2.md").write_text(
            "---\ncycle: 2\nfindings_addressed: [A-1]\n---\n",
            encoding="utf-8",
        )
        result = render_attempt_tracker_block(3, tmp_path, 2)
        # A-1 attempted 2 times → escalated
        assert "ALREADY ESCALATED" in result
        # B-2 attempted 1 time → attempt 2 of 2
        assert "attempt 2 of 2" in result

    def test_max_fix_attempts_respected(self, tmp_path):
        """With max_attempts=3, 2 attempts is NOT escalated."""
        (tmp_path / "fixes-1.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-1]\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "fixes-2.md").write_text(
            "---\ncycle: 2\nfindings_addressed: [A-1]\n---\n",
            encoding="utf-8",
        )
        result = render_attempt_tracker_block(3, tmp_path, max_attempts=3)
        assert "ALREADY ESCALATED" not in result
        assert "attempt 3 of 3" in result

    def test_uses_fixture_files(self):
        """Test with real fixture files from tests/harness/fixtures/."""
        result = render_attempt_tracker_block(3, FIXTURES, 2)
        # fixes-1.md: [A-8, A-6, B-2], fixes-2.md: [A-8, B-2]
        # A-8: 2 attempts → escalated
        # B-2: 2 attempts → escalated
        # A-6: 1 attempt → attempt 2 of 2
        assert "ALREADY ESCALATED" in result
        assert "`A-8`" in result
        assert "`B-2`" in result
        assert "`A-6`" in result


# ---------------------------------------------------------------------------
# DRY_RUN integration
# ---------------------------------------------------------------------------


class TestDryRun:
    """DRY_RUN mode prompt rendering."""

    def test_dry_run_track_a_has_override(self, tmp_path):
        config = _make_config(dry_run=True)
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "DRY RUN OVERRIDE" in text
        assert "Test ONLY capability A-1" in text

    def test_dry_run_override_appears_twice_cycle1(self, tmp_path):
        """DRY_RUN override appears both at top and bottom of cycle 1."""
        config = _make_config(dry_run=True)
        prompt = render_eval_prompt("a", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        # Should appear in the header area and in the "--- DRY RUN OVERRIDE ---" block
        assert text.count("DRY RUN OVERRIDE") >= 2

    def test_dry_run_track_b_no_override(self, tmp_path):
        """DRY_RUN override only applies to track a."""
        config = _make_config(dry_run=True)
        prompt = render_eval_prompt("b", 1, "/tmp/sc.md", config, tmp_path)
        text = prompt.read_text(encoding="utf-8")
        assert "DRY RUN OVERRIDE" not in text
