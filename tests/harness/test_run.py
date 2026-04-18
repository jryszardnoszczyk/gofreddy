"""Tests for harness.run -- core cycle loop and summary generation.

Integration tests mock the external boundaries (preflight, engine, worktree)
and verify the cycle loop's 11 break conditions, evaluator dispatch,
fixer gating, and summary output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.config import Config
from harness.run import _merge_fix_reports, attribute_file, run, write_summary
from harness.scorecard import Finding, Scorecard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.fakesig"
_MOCK_USER_ID = "harness-test-user-id"


def _make_scorecard_text(
    cycle: int,
    track: str,
    findings: list[tuple[str, str, str, str]],
    *,
    evaluator_failed: bool = False,
    failure_reason: str = "",
) -> str:
    """Build a scorecard markdown string from (id, capability, grade, summary) tuples."""
    p = sum(1 for _, _, g, _ in findings if g == "PASS")
    pa = sum(1 for _, _, g, _ in findings if g == "PARTIAL")
    f = sum(1 for _, _, g, _ in findings if g == "FAIL")
    b = sum(1 for _, _, g, _ in findings if g == "BLOCKED")

    lines = [
        "---",
        f"cycle: {cycle}",
        f"track: {track}",
        f"pass: {p}",
        f"partial: {pa}",
        f"fail: {f}",
        f"blocked: {b}",
    ]
    if evaluator_failed:
        lines.append("evaluator_failed: true")
        if failure_reason:
            lines.append(f'evaluator_failure_reason: "{failure_reason}"')
    lines.append("findings:")
    if not findings:
        lines.append("  []")
    else:
        for fid, cap, grade, summary in findings:
            lines.append(f"  - id: {fid}")
            lines.append(f"    capability: {cap}")
            lines.append(f"    grade: {grade}")
            lines.append(f"    summary: {summary}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _write_scorecard(run_dir: Path, cycle: int, track: str, text: str) -> Path:
    """Write a scorecard file and return its path."""
    p = run_dir / f"scorecard-{cycle}-track-{track}.md"
    p.write_text(text, encoding="utf-8")
    return p


def _make_config(tmp_path: Path, **overrides) -> Config:
    """Build a Config with test-friendly defaults."""
    defaults = dict(
        max_cycles=5,
        dry_run=False,
        engine="claude",
        eval_only=False,
        tracks=["a"],
        max_retries=1,
        max_walltime=14400,
        max_fix_attempts=2,
        staging_root=str(tmp_path),
    )
    defaults.update(overrides)
    return Config(**defaults)


def _find_run_dir(tmp_path: Path) -> Path:
    """Find the single timestamped run directory created by run()."""
    runs_dir = tmp_path / "harness" / "runs"
    dirs = [d for d in runs_dir.iterdir() if d.is_dir()] if runs_dir.exists() else []
    assert len(dirs) == 1, f"Expected exactly 1 run dir, found {len(dirs)}: {dirs}"
    return dirs[0]


def _read_summary(tmp_path: Path) -> str:
    """Read the summary.md from the run directory."""
    rd = _find_run_dir(tmp_path)
    return (rd / "summary.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------

_P_PREFLIGHT = "harness.run.run_preflight"
_P_CREATE_WT = "harness.run.create_staging_worktree"
_P_CLEANUP_WT = "harness.run.cleanup_staging_worktree"
_P_STACK_HEALTH = "harness.run.check_stack_health"
_P_CLEANUP_STATE = "harness.run.cleanup_harness_state"
_P_JWT_EXPIRY = "harness.run.check_jwt_expiry"
_P_JWT_FRESHNESS = "harness.run.check_vite_jwt_freshness"
_P_REFRESH_JWT = "harness.run.refresh_vite_jwt"
_P_EVAL_PROMPT = "harness.run.render_eval_prompt"
_P_FIXER_PROMPT = "harness.run.render_fixer_prompt"
_P_VERIFIER_PROMPT = "harness.run.render_verifier_prompt"
_P_DISPATCH_VERIFIERS = "harness.run._dispatch_verifiers"
_P_CAPTURE_SHA = "harness.run._capture_git_sha"
_P_COMMIT_OR_ROLLBACK = "harness.run._commit_or_rollback"
_P_SNAP_BACKEND = "harness.run.snapshot_backend_tree"
_P_DETECT_CHANGES = "harness.run.detect_backend_changes"
_P_SNAP_PROTECTED = "harness.run.snapshot_protected_files"
_P_VERIFY_PROTECTED = "harness.run.verify_and_restore_protected_files"
_P_RESTART_BACKEND = "harness.run.restart_backend"
_P_ENGINE_CLASS = "harness.run.Engine"
_P_PROCESS_TRACKER = "harness.run.ProcessTracker"
_P_REPO_ROOT = "harness.run._REPO_ROOT"
_P_MATRIX_PATH = "harness.run._MATRIX_PATH"
_P_TIME_SLEEP = "harness.run.time.sleep"
_P_TIME_MONOTONIC = "harness.run.time.monotonic"


class _MockPreflightResult:
    def __init__(self):
        self.jwt_token = _MOCK_TOKEN
        self.harness_user_id = _MOCK_USER_ID


def _standard_patches(tmp_path: Path):
    """Return a dict of patch targets -> mock values for the standard harness mocks.

    ``_REPO_ROOT`` is set to *tmp_path* so ``run()`` creates its run
    directory at ``tmp_path / "harness" / "runs" / <timestamp>``.
    """
    tracker_mock = MagicMock()
    tracker_mock.__enter__ = MagicMock(return_value=tracker_mock)
    tracker_mock.__exit__ = MagicMock(return_value=False)

    return {
        _P_PREFLIGHT: MagicMock(return_value=_MockPreflightResult()),
        _P_CREATE_WT: MagicMock(return_value=(tmp_path / "worktree", "staging-branch")),
        _P_CLEANUP_WT: MagicMock(),
        _P_STACK_HEALTH: MagicMock(),
        _P_CLEANUP_STATE: MagicMock(),
        _P_JWT_EXPIRY: MagicMock(return_value=9999),
        _P_JWT_FRESHNESS: MagicMock(return_value=9999),
        _P_REFRESH_JWT: MagicMock(return_value=_MOCK_TOKEN),
        _P_EVAL_PROMPT: MagicMock(return_value=tmp_path / "prompt.md"),
        _P_FIXER_PROMPT: MagicMock(return_value=tmp_path / "fixer-prompt.md"),
        _P_VERIFIER_PROMPT: MagicMock(return_value=tmp_path / "verifier-prompt.md"),
        _P_DISPATCH_VERIFIERS: MagicMock(return_value={}),
        _P_CAPTURE_SHA: MagicMock(return_value="abc123def456"),
        _P_COMMIT_OR_ROLLBACK: MagicMock(return_value=None),
        _P_SNAP_BACKEND: MagicMock(return_value={}),
        _P_DETECT_CHANGES: MagicMock(return_value=[]),
        _P_SNAP_PROTECTED: MagicMock(return_value=tmp_path / "backup"),
        _P_VERIFY_PROTECTED: MagicMock(return_value=0),
        _P_RESTART_BACKEND: MagicMock(),
        _P_PROCESS_TRACKER: MagicMock(return_value=tracker_mock),
        _P_REPO_ROOT: tmp_path,
        _P_MATRIX_PATH: tmp_path / "test-matrix.md",
        _P_TIME_SLEEP: MagicMock(),
        _P_TIME_MONOTONIC: MagicMock(side_effect=lambda: 0.0),
    }


def _apply_patches(patches: dict):
    """Apply all patches and return (patchers_list, mocks_dict)."""
    patchers = []
    mocks = {}
    for target, mock_val in patches.items():
        p = patch(target, mock_val)
        mocks[target] = p.start()
        patchers.append(p)
    return patchers, mocks


def _stop_patches(patchers):
    for p in patchers:
        p.stop()


def _run_with_mocks(tmp_path, config, mock_evaluate, mock_fix=None, extra_patches=None):
    """Convenience: set up standard mocks, inject engine, run(), return summary text."""
    patches = _standard_patches(tmp_path)

    engine_mock = MagicMock()
    engine_mock.evaluate = MagicMock(side_effect=mock_evaluate)
    if mock_fix is not None:
        engine_mock.fix = MagicMock(side_effect=mock_fix)
    else:
        engine_mock.fix = MagicMock(side_effect=lambda c, p, cfg, rd, **kwargs: rd / f"fixer-{c}.log")
    patches[_P_ENGINE_CLASS] = MagicMock(return_value=engine_mock)

    if extra_patches:
        patches.update(extra_patches)

    patchers, mocks = _apply_patches(patches)
    try:
        run(config)
        summary = _read_summary(tmp_path)
        return summary, engine_mock, mocks
    finally:
        _stop_patches(patchers)


# ---------------------------------------------------------------------------
# Integration: 2-cycle run, FAIL -> PASS -> ALL PASS
# ---------------------------------------------------------------------------


class TestAllPassExit:
    """Cycle 1 produces FAIL findings, cycle 2 produces PASS -> ALL PASS."""

    def test_all_pass_after_fix(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=5, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if cycle == 1:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search TikTok", "FAIL", "Search broken"),
                    ("A-2", "Filter results", "FAIL", "Filter broken"),
                ])
            else:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search TikTok", "PASS", "Search works"),
                    ("A-2", "Filter results", "PASS", "Filter works"),
                ])
            return _write_scorecard(rd, cycle, track, text)

        summary, engine_mock, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "ALL PASS" in summary
        assert "Cycles completed**: 2" in summary


# ---------------------------------------------------------------------------
# Integration: regression brake
# ---------------------------------------------------------------------------


class TestRegressionBrake:
    """Cycle 2 pass count drops -> regression brake fires."""

    def test_regression_exits(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=5, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if cycle == 1:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                    ("A-2", "Filter", "PASS", "OK"),
                    ("A-3", "Sort", "FAIL", "Broken"),
                ])
            else:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                    ("A-2", "Filter", "FAIL", "Regressed"),
                    ("A-3", "Sort", "FAIL", "Still broken"),
                ])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "net regression" in summary


# ---------------------------------------------------------------------------
# Integration: convergence exit
# ---------------------------------------------------------------------------


class TestConvergenceExit:
    """Grades unchanged between cycles -> converged."""

    def test_convergence_stops(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=5, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "PASS", "OK"),
                ("A-2", "Filter", "FAIL", "Broken"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "converged" in summary


# ---------------------------------------------------------------------------
# Integration: evaluator failure scorecard -> merge still works
# ---------------------------------------------------------------------------


class TestEvaluatorCrash:
    """Evaluator writes a failure scorecard (zero counts) -> all evaluators failed."""

    def test_crash_produces_failure_and_exits(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=2, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(
                cycle, track, [],
                evaluator_failed=True,
                failure_reason="Evaluator crashed",
            )
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "all evaluators failed" in summary


# ---------------------------------------------------------------------------
# Integration: eval_only -> fixer skipped
# ---------------------------------------------------------------------------


class TestEvalOnly:
    """eval_only=True -> fixer skipped, exits after one cycle."""

    def test_eval_only_skips_fixer(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=5, eval_only=True, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "PASS", "OK"),
                ("A-2", "Filter", "FAIL", "Broken"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, engine_mock, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "eval-only" in summary
        engine_mock.fix.assert_not_called()
        assert "Cycles completed**: 1" in summary


# ---------------------------------------------------------------------------
# Edge case: all evaluators fail (zero counts)
# ---------------------------------------------------------------------------


class TestAllEvaluatorsFail:
    """Zero findings from all evaluators -> specific exit reason."""

    def test_zero_counts_exits(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=3, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(
                cycle, track, [],
                evaluator_failed=True,
                failure_reason="Timeout",
            )
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "all evaluators failed" in summary


# ---------------------------------------------------------------------------
# Edge case: resume from cycle 2
# ---------------------------------------------------------------------------


class TestResumeCycle:
    """Resume from cycle 2 -> completed_cycles pre-seeded, backend restarted."""

    def test_resume_preseeds_cycles(self, tmp_path: Path):
        config = _make_config(
            tmp_path,
            max_cycles=3,
            tracks=["a"],
            resume_cycle=2,
            resume_branch="harness/run-test",
        )

        call_cycles = []

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            call_cycles.append(cycle)
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "PASS", "OK"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, mocks = _run_with_mocks(tmp_path, config, mock_evaluate)

        # Backend should have been restarted for resume
        mocks[_P_RESTART_BACKEND].assert_called_once()
        # completed_cycles = pre-seed (1) + 1 executed = 2
        assert "Cycles completed**: 2" in summary
        assert "ALL PASS" in summary
        # Should start from cycle 2, not cycle 1
        assert call_cycles == [2]


# ---------------------------------------------------------------------------
# Edge case: evaluator raises Python exception -> logged, merge continues
# ---------------------------------------------------------------------------


class TestEvaluatorException:
    """Evaluator raises a Python exception -> logged, merge still works."""

    def test_exception_in_evaluator_thread(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=2, tracks=["a", "b"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if track == "a":
                raise RuntimeError("Track A exploded")
            text = _make_scorecard_text(cycle, track, [
                ("B-1", "Monitor", "PASS", "OK"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        # Track B PASS should yield ALL PASS
        assert "ALL PASS" in summary


# ---------------------------------------------------------------------------
# Summary: write_summary correctness
# ---------------------------------------------------------------------------


class TestWriteSummary:
    """Verify write_summary produces correct content."""

    def test_summary_basic_fields(self, tmp_path: Path):
        run_dir = tmp_path / "20260412-120000"
        run_dir.mkdir()
        config = _make_config(tmp_path, max_cycles=5, engine="claude")

        merged = Scorecard(
            cycle=3,
            track=None,
            findings=[
                Finding(id="A-1", capability="Search", grade="PASS", summary="OK"),
                Finding(id="A-2", capability="Filter", grade="FAIL", summary="Broken"),
            ],
        )

        path = write_summary(
            run_dir, config, merged, 3, "ALL PASS",
            "staging-branch", set(),
        )

        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "# Harness Run Summary" in text
        assert "20260412-120000" in text
        assert "claude" in text
        assert "3 / 5" in text
        assert "ALL PASS" in text
        assert "None." in text  # no escalated

    def test_summary_with_escalated(self, tmp_path: Path):
        run_dir = tmp_path / "20260412-120000"
        run_dir.mkdir()
        config = _make_config(tmp_path, max_cycles=5)

        merged = Scorecard(cycle=2, track=None, findings=[])

        path = write_summary(
            run_dir, config, merged, 2, "converged",
            "staging-branch", {"A-3", "B-1"},
        )

        text = path.read_text(encoding="utf-8")
        assert "A-3" in text
        assert "B-1" in text
        assert "auto-escalated" in text
        assert "Human review required" in text

    def test_summary_no_merged(self, tmp_path: Path):
        run_dir = tmp_path / "20260412-120000"
        run_dir.mkdir()
        config = _make_config(tmp_path)

        path = write_summary(
            run_dir, config, None, 0, "all evaluators failed",
            "", set(),
        )

        text = path.read_text(encoding="utf-8")
        assert "No merged scorecard was produced" in text
        assert "No staging branch (legacy mode)" in text

    def test_summary_dry_run_scope(self, tmp_path: Path):
        run_dir = tmp_path / "20260412-120000"
        run_dir.mkdir()
        config = _make_config(tmp_path, dry_run=True)

        merged = Scorecard(cycle=1, track=None, findings=[
            Finding(id="A-1", capability="Search", grade="PASS", summary="OK"),
        ])

        path = write_summary(
            run_dir, config, merged, 1, "DRY RUN PASS",
            "staging-branch", set(),
        )

        text = path.read_text(encoding="utf-8")
        assert "Track A / capability A1 only" in text
        assert "DRY RUN PASS" in text

    def test_summary_lists_artifacts(self, tmp_path: Path):
        run_dir = tmp_path / "20260412-120000"
        run_dir.mkdir()
        (run_dir / "scorecard-1-merged.md").write_text("test", encoding="utf-8")
        (run_dir / "fixes-1.md").write_text("test", encoding="utf-8")
        config = _make_config(tmp_path)

        merged = Scorecard(cycle=1, track=None, findings=[])
        path = write_summary(
            run_dir, config, merged, 1, "test",
            "", set(),
        )

        text = path.read_text(encoding="utf-8")
        assert "scorecard-1-merged.md" in text
        assert "fixes-1.md" in text

    def test_summary_no_overlap_no_section(self, tmp_path: Path):
        """No overlap logs → no Overlap Warnings section."""
        run_dir = tmp_path / "20260413-120000"
        run_dir.mkdir()
        config = _make_config(tmp_path)
        merged = Scorecard(cycle=1, track=None, findings=[])

        path = write_summary(run_dir, config, merged, 1, "test", "", set())
        text = path.read_text(encoding="utf-8")
        assert "## Overlap Warnings" not in text

    def test_summary_with_overlap_has_section(self, tmp_path: Path):
        """Overlap log present → Overlap Warnings section appears."""
        run_dir = tmp_path / "20260413-120000"
        run_dir.mkdir()
        (run_dir / ".fixer-overlap-1.log").write_text(
            "Cycle 1 overlap report\n"
            "Active domains: A, B\n"
            "Shared files modified (1):\n"
            "  src/orchestrator/tool_handlers/_helpers.py\n",
            encoding="utf-8",
        )
        config = _make_config(tmp_path)
        merged = Scorecard(cycle=1, track=None, findings=[])

        path = write_summary(run_dir, config, merged, 1, "test", "", set())
        text = path.read_text(encoding="utf-8")
        assert "## Overlap Warnings" in text
        assert "_helpers.py" in text


# ---------------------------------------------------------------------------
# Integration: dry run only runs track A
# ---------------------------------------------------------------------------


class TestDryRun:
    """dry_run=True dispatches only track A."""

    def test_dry_run_single_track(self, tmp_path: Path):
        config = _make_config(
            tmp_path,
            max_cycles=2,
            dry_run=True,
            tracks=["a", "b", "c"],
        )

        evaluated_tracks = []

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            evaluated_tracks.append(track)
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "PASS", "OK"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert evaluated_tracks == ["a"]
        assert "DRY RUN PASS" in summary


# ---------------------------------------------------------------------------
# Integration: rate-limit sentinel
# ---------------------------------------------------------------------------


class TestRateLimitSentinel:
    """Rate-limit sentinel file -> specific exit reason."""

    def test_rate_limit_detected(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=2, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            (rd / ".rate-limit-hit").touch()
            text = _make_scorecard_text(
                cycle, track, [],
                evaluator_failed=True,
                failure_reason="Rate limited",
            )
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "rate_limit" in summary


# ---------------------------------------------------------------------------
# Integration: evaluation incomplete
# ---------------------------------------------------------------------------


class TestEvaluationIncomplete:
    """evaluator_failed=True with some PASS findings -> evaluation incomplete."""

    def test_incomplete_eval_refused(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=2, tracks=["a", "b"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if track == "a":
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                ])
            else:
                text = _make_scorecard_text(
                    cycle, track, [],
                    evaluator_failed=True,
                    failure_reason="Track B crashed",
                )
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "evaluation incomplete" in summary


# ---------------------------------------------------------------------------
# Integration: wall-time cap
# ---------------------------------------------------------------------------


class TestWallTimeCap:
    """Wall-time cap reached -> break with appropriate message."""

    def test_walltime_cap_fires(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=10, max_walltime=100, tracks=["a"])

        # monotonic: first call (start) returns 0, second (loop check) returns 200
        time_values = iter([0.0, 200.0])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            # Should never be called
            text = _make_scorecard_text(cycle, track, [("A-1", "X", "PASS", "Y")])
            return _write_scorecard(rd, cycle, track, text)

        summary, engine_mock, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate,
            extra_patches={
                _P_TIME_MONOTONIC: MagicMock(side_effect=lambda: next(time_values)),
            },
        )

        assert "wall-time cap" in summary
        engine_mock.evaluate.assert_not_called()


# ---------------------------------------------------------------------------
# Integration: fixer is called between cycles
# ---------------------------------------------------------------------------


class TestFixerCalled:
    """Verify fixer runs between cycles when there are failures."""

    def test_fixer_invoked(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=4, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if cycle == 1:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                    ("A-2", "Filter", "FAIL", "Broken"),
                ])
            elif cycle == 2:
                # Improve A-2 from FAIL to PARTIAL to avoid convergence
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                    ("A-2", "Filter", "PARTIAL", "Getting better"),
                ])
            else:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                    ("A-2", "Filter", "PASS", "Fixed"),
                ])
            return _write_scorecard(rd, cycle, track, text)

        summary, engine_mock, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert engine_mock.fix.call_count >= 1
        assert "ALL PASS" in summary


# ---------------------------------------------------------------------------
# Max cycles exhausted
# ---------------------------------------------------------------------------


class TestMaxCyclesExhausted:
    """Loop runs all cycles without hitting a break -> default exit reason."""

    def test_max_cycles_exit(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=2, tracks=["a"])

        # Findings that change between cycles to avoid convergence
        cycle_findings = [
            [("A-1", "Search", "PASS", "OK"), ("A-2", "Filter", "FAIL", "Broken")],
            [("A-1", "Search", "PASS", "OK"), ("A-2", "Filter", "PARTIAL", "Better")],
        ]

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            idx = min(cycle - 1, len(cycle_findings) - 1)
            text = _make_scorecard_text(cycle, track, cycle_findings[idx])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)

        assert "max cycles reached" in summary
        assert "Cycles completed**: 2" in summary


# ---------------------------------------------------------------------------
# Stack-unhealthy exit
# ---------------------------------------------------------------------------


class TestStackUnhealthy:
    """Stack health check fails twice -> break with stack unhealthy."""

    def test_stack_unhealthy_exits(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=3, tracks=["a"])

        # Findings that change between cycles to avoid convergence
        cycle_findings = [
            [("A-1", "Search", "FAIL", "Broken")],
            [("A-1", "Search", "PARTIAL", "Better")],
        ]

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            idx = min(cycle - 1, len(cycle_findings) - 1)
            text = _make_scorecard_text(cycle, track, cycle_findings[idx])
            return _write_scorecard(rd, cycle, track, text)

        # Stack health fails on cycle 3 (both attempts)
        call_count = [0]
        def stack_health_side_effect(cfg):
            call_count[0] += 1
            # First 2 calls (cycles 1 and 2) succeed, cycle 3 fails twice
            if call_count[0] >= 3:
                raise RuntimeError("backend unreachable")

        summary, _, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate,
            extra_patches={_P_STACK_HEALTH: MagicMock(side_effect=stack_health_side_effect)},
        )

        assert "stack unhealthy" in summary
        assert "Cycles completed**: 2" in summary


# ---------------------------------------------------------------------------
# JWT auto-refresh mid-run
# ---------------------------------------------------------------------------


class TestJwtAutoRefresh:
    """JWT near expiry triggers refresh, failure aborts."""

    def test_jwt_refresh_success(self, tmp_path: Path):
        """JWT freshness < 600 triggers refresh, run continues."""
        config = _make_config(tmp_path, max_cycles=2, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            if cycle == 1:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "FAIL", "Broken"),
                ])
            else:
                text = _make_scorecard_text(cycle, track, [
                    ("A-1", "Search", "PASS", "OK"),
                ])
            return _write_scorecard(rd, cycle, track, text)

        # Freshness returns 300 (below 600 threshold) — triggers refresh
        # This is called before cycle 2 (cycle > 1 check in run.py)
        summary, _, mocks = _run_with_mocks(
            tmp_path, config, mock_evaluate,
            extra_patches={_P_JWT_FRESHNESS: MagicMock(return_value=300)},
        )

        # Should have refreshed but continued to ALL PASS
        assert "ALL PASS" in summary
        assert mocks[_P_REFRESH_JWT].called

    def test_jwt_refresh_failure_aborts(self, tmp_path: Path):
        """JWT refresh failure aborts the run."""
        config = _make_config(tmp_path, max_cycles=3, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "FAIL", "Broken"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        # Freshness returns expired (-100), refresh throws
        def refresh_side_effect(cfg):
            raise RuntimeError("vite restart failed")

        summary, _, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate,
            extra_patches={
                _P_JWT_FRESHNESS: MagicMock(return_value=-100),
                _P_REFRESH_JWT: MagicMock(side_effect=refresh_side_effect),
            },
        )

        assert "auto-refresh failed" in summary
        assert "Cycles completed**: 1" in summary


# ---------------------------------------------------------------------------
# Backend restart after fixer
# ---------------------------------------------------------------------------


class TestBackendRestart:
    """Backend file changes trigger restart between cycles."""

    def test_backend_restart_called_on_changes(self, tmp_path: Path):
        """Fixer changes backend files -> restart_backend called."""
        config = _make_config(tmp_path, max_cycles=2, tracks=["a"])

        cycle_findings = [
            [("A-1", "Search", "FAIL", "Broken")],
            [("A-1", "Search", "PASS", "Fixed")],
        ]

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            idx = min(cycle - 1, len(cycle_findings) - 1)
            text = _make_scorecard_text(cycle, track, cycle_findings[idx])
            return _write_scorecard(rd, cycle, track, text)

        # detect_backend_changes returns a changed file after cycle 1 fixer
        change_call = [0]
        def detect_changes_side_effect(before, after):
            change_call[0] += 1
            if change_call[0] == 1:
                return ["src/api/main.py"]
            return []

        summary, _, mocks = _run_with_mocks(
            tmp_path, config, mock_evaluate,
            extra_patches={_P_DETECT_CHANGES: MagicMock(side_effect=detect_changes_side_effect)},
        )

        assert "ALL PASS" in summary
        assert mocks[_P_RESTART_BACKEND].called


# ---------------------------------------------------------------------------
# Summary dry_run casing
# ---------------------------------------------------------------------------


class TestSummaryDryRunCasing:
    """Verify dry_run renders as lowercase true/false in summary."""

    def test_dry_run_true_lowercase(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=1, eval_only=True, dry_run=True, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [("A-1", "Search", "PASS", "OK")])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)
        assert "**Dry run**: true" in summary
        assert "**Dry run**: True" not in summary

    def test_dry_run_false_lowercase(self, tmp_path: Path):
        config = _make_config(tmp_path, max_cycles=1, eval_only=True, tracks=["a"])

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [("A-1", "Search", "PASS", "OK")])
            return _write_scorecard(rd, cycle, track, text)

        summary, _, _ = _run_with_mocks(tmp_path, config, mock_evaluate)
        assert "**Dry run**: false" in summary
        assert "**Dry run**: False" not in summary


# ---------------------------------------------------------------------------
# attribute_file
# ---------------------------------------------------------------------------


class TestAttributeFile:
    """Unit tests for the attribute_file helper."""

    def test_search_handler_is_a(self):
        assert attribute_file("src/orchestrator/tool_handlers/search.py") == "A"

    def test_manage_monitor_is_b(self):
        assert attribute_file("src/orchestrator/tool_handlers/manage_monitor.py") == "B"

    def test_video_project_is_c(self):
        assert attribute_file("src/orchestrator/tool_handlers/video_project.py") == "C"

    def test_helpers_is_shared(self):
        assert attribute_file("src/orchestrator/tool_handlers/_helpers.py") == "SHARED"

    def test_workspace_is_shared(self):
        assert attribute_file("src/orchestrator/tool_handlers/workspace.py") == "SHARED"

    def test_outside_tool_handlers_is_none(self):
        assert attribute_file("tests/test_x.py") is None

    def test_api_file_is_none(self):
        assert attribute_file("src/api/dependencies.py") is None

    def test_unknown_handler_is_none(self):
        assert attribute_file("src/orchestrator/tool_handlers/unknown_handler.py") is None


# ---------------------------------------------------------------------------
# Parallel fixer dispatch
# ---------------------------------------------------------------------------


class TestParallelFixerDispatch:
    """Integration tests for parallel fixer dispatch (fixer_workers > 1)."""

    @staticmethod
    def _mock_subprocess_run_factory(sha="abc123"):
        """Return a side_effect for subprocess.run that handles all harness subprocess calls."""
        def _mock_run(cmd, *args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            if isinstance(cmd, list):
                if cmd[0] == "git":
                    result.stdout = sha + "\n"
                    if "diff" in cmd:
                        result.stdout = ""  # no changed files
                else:
                    # npx vitest, npx tsc, pytest, etc.
                    result.stdout = ""
            else:
                result.stdout = ""
            return result
        return _mock_run

    def test_parallel_dispatch_calls_engine_per_domain(self, tmp_path: Path):
        """fixer_workers=3 with 3 active domains → 3 engine.fix calls."""
        config = _make_config(
            tmp_path, max_cycles=1, tracks=["a", "b", "c"],
            fixer_workers=3, fixer_domains=["A", "B", "C"],
        )

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            findings_by_track = {
                "a": [("A-1", "Search", "FAIL", "Broken")],
                "b": [("B-1", "Monitor", "FAIL", "Broken")],
                "c": [("C-1", "Video", "FAIL", "Broken")],
            }
            text = _make_scorecard_text(cycle, track, findings_by_track.get(track, []))
            return _write_scorecard(rd, cycle, track, text)

        fix_calls = []

        def mock_fix(c, p, cfg, rd, **kwargs):
            fix_calls.append(kwargs.get("domain_suffix", ""))
            return rd / f"fixer-{c}-{kwargs.get('domain_suffix', '')}.log"

        summary, engine_mock, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate, mock_fix=mock_fix,
            extra_patches={"harness.run.subprocess.run": self._mock_subprocess_run_factory()},
        )
        # 3 parallel calls
        assert len(fix_calls) == 3
        assert set(fix_calls) == {"a", "b", "c"}

    def test_parallel_skips_empty_domains(self, tmp_path: Path):
        """fixer_workers=3 with findings only in A → 1 call."""
        config = _make_config(
            tmp_path, max_cycles=1, tracks=["a"],
            fixer_workers=3, fixer_domains=["A", "B", "C"],
        )

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "FAIL", "Broken"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        fix_calls = []

        def mock_fix(c, p, cfg, rd, **kwargs):
            fix_calls.append(kwargs.get("domain_suffix", ""))
            return rd / f"fixer-{c}-{kwargs.get('domain_suffix', '')}.log"

        summary, _, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate, mock_fix=mock_fix,
            extra_patches={"harness.run.subprocess.run": self._mock_subprocess_run_factory()},
        )
        assert len(fix_calls) == 1
        assert fix_calls[0] == "a"

    def test_sequential_unifies_to_all_domain_with_workers_1(self, tmp_path: Path):
        """fixer_workers=1 → unified dispatch with virtual "all" domain."""
        config = _make_config(
            tmp_path, max_cycles=1, tracks=["a"],
            fixer_workers=1,
        )

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            text = _make_scorecard_text(cycle, track, [
                ("A-1", "Search", "FAIL", "Broken"),
                ("A-2", "Filter", "PASS", "OK"),
            ])
            return _write_scorecard(rd, cycle, track, text)

        summary, engine_mock, _ = _run_with_mocks(tmp_path, config, mock_evaluate)
        # Unified dispatch: fix() called with domain_suffix="all"
        fix_call = engine_mock.fix.call_args
        assert fix_call.kwargs.get("domain_suffix") == "all"

    def test_parallel_fixer_exception_logged_others_complete(self, tmp_path: Path):
        """One fixer raises → others complete, cycle continues."""
        config = _make_config(
            tmp_path, max_cycles=1, tracks=["a", "b"],
            fixer_workers=3, fixer_domains=["A", "B"],
        )

        def mock_evaluate(track, cycle, prompt_path, cfg, rd):
            findings = {
                "a": [("A-1", "Search", "FAIL", "Broken")],
                "b": [("B-1", "Monitor", "FAIL", "Broken")],
            }
            text = _make_scorecard_text(cycle, track, findings.get(track, []))
            return _write_scorecard(rd, cycle, track, text)

        def mock_fix(c, p, cfg, rd, **kwargs):
            if kwargs.get("domain_suffix") == "a":
                raise RuntimeError("Domain A fixer crashed")
            return rd / f"fixer-{c}-{kwargs.get('domain_suffix', '')}.log"

        # Should not raise — exceptions are logged, not propagated
        summary, _, _ = _run_with_mocks(
            tmp_path, config, mock_evaluate, mock_fix=mock_fix,
            extra_patches={"harness.run.subprocess.run": self._mock_subprocess_run_factory()},
        )


# ---------------------------------------------------------------------------
# _merge_fix_reports
# ---------------------------------------------------------------------------


class TestMergeFixReports:
    """Unit tests for _merge_fix_reports."""

    def test_merge_two_domain_reports(self, tmp_path: Path):
        """Two domain reports → merged with union of findings_addressed."""
        (tmp_path / "fixes-1-a.md").write_text(
            "---\ncycle: 1\nfixes_applied: 2\n"
            "findings_addressed: [A-1, A-3]\ncommit: abc\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "fixes-1-b.md").write_text(
            "---\ncycle: 1\nfixes_applied: 1\n"
            "findings_addressed: [B-2]\ncommit: abc\n---\n",
            encoding="utf-8",
        )

        active = {
            "A": Scorecard(cycle=1, track=None, findings=[]),
            "B": Scorecard(cycle=1, track=None, findings=[]),
        }

        path = _merge_fix_reports(1, active, tmp_path, "sha123")

        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "A-1" in text
        assert "A-3" in text
        assert "B-2" in text
        assert "sha123" in text

    def test_merge_missing_report_skipped(self, tmp_path: Path):
        """Missing domain report → skipped gracefully."""
        (tmp_path / "fixes-1-a.md").write_text(
            "---\ncycle: 1\nfindings_addressed: [A-1]\ncommit: abc\n---\n",
            encoding="utf-8",
        )
        # No fixes-1-b.md
        active = {
            "A": Scorecard(cycle=1, track=None, findings=[]),
            "B": Scorecard(cycle=1, track=None, findings=[]),
        }

        path = _merge_fix_reports(1, active, tmp_path, "sha123")
        text = path.read_text(encoding="utf-8")
        assert "A-1" in text


