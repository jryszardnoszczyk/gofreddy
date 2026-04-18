"""Tests for convergence checking, escalation tracking, and Flow 4 exclusion."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from harness.scorecard import (
    Finding,
    Scorecard,
    check_convergence,
    compute_escalated_findings,
    count_escalated_non_pass,
    count_finding_attempts,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Convergence
# ---------------------------------------------------------------------------


class TestConvergence:
    """check_convergence tests."""

    def test_identical_grades_converged(self):
        """Same grades in both cycles → converged."""
        current = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="PASS", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="PASS", summary="s"),
            ],
        )
        assert check_convergence(current, previous, set(), set()) is True

    def test_different_grades_not_converged(self):
        current = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="PASS", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, set(), set()) is False

    def test_flow4_finding_change_still_converged(self):
        """Flow 4 grade changes are excluded → convergence still holds."""
        flow4_ids = {"A-9"}
        current = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="A-9", capability="c2", grade="PASS", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="A-9", capability="c2", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, flow4_ids, set()) is True

    def test_escalated_finding_change_still_converged(self):
        """Escalated grade changes are excluded → convergence still holds."""
        escalated = {"B-2"}
        current = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="PARTIAL", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, set(), escalated) is True

    def test_both_flow4_and_escalated_excluded(self):
        """Both Flow 4 and escalated changes excluded simultaneously."""
        flow4_ids = {"A-9"}
        escalated = {"B-2"}
        current = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="PASS", summary="s"),
                Finding(id="A-9", capability="c3", grade="PASS", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-2", capability="c2", grade="FAIL", summary="s"),
                Finding(id="A-9", capability="c3", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, flow4_ids, escalated) is True

    def test_empty_current_not_converged(self):
        """Empty current grades → not converged (matching bash behavior)."""
        current = Scorecard(cycle=2, track=None, findings=[])
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, set(), set()) is False

    def test_all_findings_excluded_not_converged(self):
        """If every finding is excluded, nothing to compare → not converged."""
        flow4_ids = {"A-1"}
        current = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, flow4_ids, set()) is False

    def test_new_finding_in_current_not_converged(self):
        """A finding present in current but not previous → different dicts."""
        current = Scorecard(
            cycle=2,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
                Finding(id="A-2", capability="c2", grade="FAIL", summary="s"),
            ],
        )
        previous = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        assert check_convergence(current, previous, set(), set()) is False


# ---------------------------------------------------------------------------
# Escalation tracking
# ---------------------------------------------------------------------------


class TestEscalation:
    """count_finding_attempts and compute_escalated_findings tests."""

    def test_count_attempts_from_fixtures(self, tmp_path):
        """Parse fixes-1.md and fixes-2.md → correct attempt counts."""
        # Copy fixture fixes into a temp run dir
        for name in ("fixes-1.md", "fixes-2.md"):
            shutil.copy(FIXTURES / name, tmp_path / name)

        counts = count_finding_attempts(tmp_path, current_cycle=3)
        assert counts["A-3"] == 2  # addressed in cycle 1 and cycle 2
        assert counts["A-6"] == 1  # addressed in cycle 1 only
        assert counts["B-3"] == 2  # addressed in cycle 1 and cycle 2

    def test_count_attempts_cycle_1_returns_empty(self, tmp_path):
        """At cycle 1 there are no prior fixes → empty dict."""
        counts = count_finding_attempts(tmp_path, current_cycle=1)
        assert counts == {}

    def test_count_attempts_missing_fixes_file(self, tmp_path):
        """Missing fixes file for a cycle is silently skipped."""
        # Only have fixes-1.md, asking for cycle=3 (should look for 1 and 2)
        shutil.copy(FIXTURES / "fixes-1.md", tmp_path / "fixes-1.md")
        counts = count_finding_attempts(tmp_path, current_cycle=3)
        assert counts["A-3"] == 1
        assert counts["A-6"] == 1
        assert counts["B-3"] == 1

    def test_compute_escalated_findings(self, tmp_path):
        """Findings attempted >= max_attempts are escalated."""
        for name in ("fixes-1.md", "fixes-2.md"):
            shutil.copy(FIXTURES / name, tmp_path / name)

        escalated = compute_escalated_findings(tmp_path, cycle=3, max_attempts=2)
        assert "A-3" in escalated
        assert "B-3" in escalated
        assert "A-6" not in escalated  # only 1 attempt

    def test_compute_escalated_max_attempts_3(self, tmp_path):
        """With max_attempts=3, nothing is escalated after 2 cycles."""
        for name in ("fixes-1.md", "fixes-2.md"):
            shutil.copy(FIXTURES / name, tmp_path / name)

        escalated = compute_escalated_findings(tmp_path, cycle=3, max_attempts=3)
        assert len(escalated) == 0


# ---------------------------------------------------------------------------
# Escalated non-PASS count
# ---------------------------------------------------------------------------


class TestEscalatedNonPass:
    """count_escalated_non_pass tests."""

    def test_basic_count(self):
        merged = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-3", capability="c1", grade="FAIL", summary="s"),
                Finding(id="B-3", capability="c2", grade="PASS", summary="s"),
                Finding(id="A-6", capability="c3", grade="FAIL", summary="s"),
            ],
        )
        escalated = {"A-3", "B-3"}
        # A-3 is escalated + FAIL → count. B-3 is escalated + PASS → skip.
        assert count_escalated_non_pass(merged, escalated) == 1

    def test_no_escalated(self):
        merged = Scorecard(
            cycle=1,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="FAIL", summary="s"),
            ],
        )
        assert count_escalated_non_pass(merged, set()) == 0

    def test_all_escalated_pass(self):
        merged = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="PASS", summary="s"),
                Finding(id="B-2", capability="c2", grade="PASS", summary="s"),
            ],
        )
        assert count_escalated_non_pass(merged, {"A-1", "B-2"}) == 0

    def test_escalated_partial_counts(self):
        merged = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-1", capability="c1", grade="PARTIAL", summary="s"),
            ],
        )
        assert count_escalated_non_pass(merged, {"A-1"}) == 1
