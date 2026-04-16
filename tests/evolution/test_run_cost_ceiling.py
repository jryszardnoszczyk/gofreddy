"""Unit 1: cost-ceiling bug fix in autoresearch run.py.

The old formula `cumulative = i * DEFAULT_COST_PER_MINUTE` approximated cost by
iteration count, which falsely triggered the MAX_SESSION_COST ceiling on
sessions that completed many short iterations (e.g. 1000 iterations in 30
seconds). The fix switches to `estimate_cost_usd(time.monotonic() - start)`,
which is the existing wall-clock helper in watchdog.py.

These tests lock in the new semantics and act as a source-level regression
guard against the bug being reintroduced.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VARIANT_ROOT = REPO_ROOT / "autoresearch" / "archive" / "v001"
SCRIPTS_ROOT = VARIANT_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from watchdog import DEFAULT_COST_PER_MINUTE, estimate_cost_usd  # type: ignore


# ── Arithmetic / regression tests ──────────────────────────────────────────


def test_estimate_cost_usd_math_matches_wall_clock_rate() -> None:
    """The replacement helper must compute elapsed_seconds/60 × rate."""
    assert estimate_cost_usd(0.0) == 0.0
    assert estimate_cost_usd(60.0) == DEFAULT_COST_PER_MINUTE  # 1 minute
    assert estimate_cost_usd(30.0) == DEFAULT_COST_PER_MINUTE / 2  # 30s
    assert estimate_cost_usd(600.0) == DEFAULT_COST_PER_MINUTE * 10  # 10min


def test_many_short_iterations_do_not_false_trigger_ceiling() -> None:
    """The specific regression: 1000 iterations in 30s should NOT trip a $5 ceiling.

    The old buggy formula `i * DEFAULT_COST_PER_MINUTE` with i=1000 and
    DEFAULT_COST_PER_MINUTE=$0.10 produces $100, which is way above any
    reasonable MAX_SESSION_COST and would break any session that completes
    iterations quickly. The fix must use wall-clock elapsed time instead.
    """
    max_cost = 5.0  # $5 — plausible MAX_SESSION_COST
    elapsed_seconds = 30.0
    iteration_count = 1000

    # Buggy formula would (incorrectly) trip the ceiling
    buggy_cumulative = iteration_count * DEFAULT_COST_PER_MINUTE
    assert buggy_cumulative > max_cost, "sanity: the bug really would false-trigger"

    # Correct wall-clock formula must NOT trip the ceiling
    correct_cumulative = estimate_cost_usd(elapsed_seconds)
    assert correct_cumulative < max_cost, (
        f"wall-clock cost for 30s ({correct_cumulative}) must not exceed ${max_cost}"
    )


def test_time_based_ceiling_triggers_when_elapsed_exceeds_threshold() -> None:
    """The new formula must trip the ceiling when wall time justifies it.

    With DEFAULT_COST_PER_MINUTE=$0.10 and MAX_SESSION_COST=$5, the ceiling
    should fire at elapsed = 5 / 0.10 × 60 = 3000 seconds (50 minutes).
    """
    max_cost = 5.0
    # Just below the threshold — no trigger
    assert estimate_cost_usd(2999.0) < max_cost
    # Just above the threshold — triggers
    assert estimate_cost_usd(3001.0) > max_cost
    # Exactly at the threshold — strict `>` means no trigger at the boundary
    assert estimate_cost_usd(3000.0) == max_cost


# ── Source-level structural tests ──────────────────────────────────────────


def _read_run_py() -> str:
    return (VARIANT_ROOT / "run.py").read_text(encoding="utf-8")


def test_run_py_does_not_use_iteration_count_formula() -> None:
    """Regression guard: the buggy `i * DEFAULT_COST_PER_MINUTE` must not return."""
    source = _read_run_py()
    # The exact buggy expression:
    assert "i * DEFAULT_COST_PER_MINUTE" not in source
    # The "cumulative = i *" variant either:
    assert "cumulative = i *" not in source


def test_run_py_uses_estimate_cost_usd_for_session_ceiling() -> None:
    """The cost ceiling must call the wall-clock helper from watchdog."""
    source = _read_run_py()
    # The replacement invocation must be present.
    assert "estimate_cost_usd(" in source
    # It must be in scope of the session-cost ceiling (immediately before the
    # "Cost limit reached" log line).
    ceiling_msg_idx = source.find("Cost limit reached")
    assert ceiling_msg_idx != -1, "cost ceiling log message should still exist"
    preceding_window = source[max(0, ceiling_msg_idx - 500) : ceiling_msg_idx]
    assert "estimate_cost_usd(" in preceding_window, (
        "estimate_cost_usd must be called in the cost-ceiling check"
    )


def test_run_py_captures_session_start_before_fresh_loop() -> None:
    """The fix must capture a monotonic session start so elapsed can be computed."""
    source = _read_run_py()
    fresh_idx = source.find("def run_domain_fresh(")
    assert fresh_idx != -1, "run_domain_fresh must exist"
    loop_idx = source.find("for i in range(1, max_iter + 1):", fresh_idx)
    assert loop_idx != -1, "fresh iteration loop must exist"
    prelude = source[fresh_idx:loop_idx]
    # Some variable that captures time.monotonic() must exist before the loop.
    # We accept either `session_start` (preferred) or the existing `start_time`
    # naming scheme used elsewhere in the module.
    assert "time.monotonic()" in prelude, (
        "run_domain_fresh must capture a monotonic start time before the iteration loop"
    )
