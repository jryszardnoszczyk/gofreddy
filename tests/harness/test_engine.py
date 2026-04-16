"""Tests for harness.engine — CLI command construction, retry/resume, failure scorecards."""

from __future__ import annotations

import os
import re
import signal
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from harness.config import Config
from harness.engine import Engine, _supports_process_groups, _terminate_process


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_run_dir(tmp_path: Path) -> Path:
    """Temporary run directory for engine tests."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    return run_dir


@pytest.fixture()
def prompt_file(tmp_path: Path) -> Path:
    """A temporary prompt file with known content."""
    p = tmp_path / "eval-prompt.md"
    p.write_text("You are an evaluator. Grade the following capabilities.", encoding="utf-8")
    return p


@pytest.fixture()
def default_config() -> Config:
    """Config with all defaults — no CLI args, no env overrides."""
    return Config()


@pytest.fixture()
def codex_config() -> Config:
    """Config for codex engine."""
    return Config(engine="codex", codex_eval_model="o3")


@pytest.fixture()
def claude_engine() -> Engine:
    return Engine("claude")


@pytest.fixture()
def codex_engine() -> Engine:
    return Engine("codex")


# ---------------------------------------------------------------------------
# Engine construction
# ---------------------------------------------------------------------------


class TestEngineInit:
    def test_valid_claude(self):
        e = Engine("claude")
        assert e.name == "claude"

    def test_valid_codex(self):
        e = Engine("codex")
        assert e.name == "codex"

    def test_invalid_engine(self):
        with pytest.raises(ValueError, match="Unknown engine"):
            Engine("gpt")


# ---------------------------------------------------------------------------
# _build_eval_command
# ---------------------------------------------------------------------------


class TestBuildEvalCommand:
    """Happy path: correct flags for each engine."""

    def test_claude_fresh_session(self, claude_engine, prompt_file, default_config):
        session_id = "abc-123"
        cmd = claude_engine._build_eval_command(
            track="a", cycle=1, prompt_path=prompt_file,
            session_id=session_id, resume=False, config=default_config,
        )
        assert cmd[0] == "claude"
        assert cmd[1] == "-p"
        # Prompt content is argument 2
        assert "evaluator" in cmd[2].lower()
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--include-partial-messages" in cmd
        assert "--verbose" in cmd
        # Fresh session: --session-id, NOT --resume
        assert "--session-id" in cmd
        assert session_id in cmd
        assert "--resume" not in cmd
        assert "--model" in cmd
        idx_model = cmd.index("--model")
        assert cmd[idx_model + 1] == default_config.eval_model
        assert "--dangerously-skip-permissions" in cmd
        assert "--allowedTools" not in cmd
        assert "--max-turns" not in cmd

    def test_claude_resume_session(self, claude_engine, prompt_file, default_config):
        session_id = "abc-123"
        cmd = claude_engine._build_eval_command(
            track="b", cycle=2, prompt_path=prompt_file,
            session_id=session_id, resume=True, config=default_config,
        )
        assert "--resume" in cmd
        assert session_id in cmd
        assert "--session-id" not in cmd

    def test_codex_fresh(self, codex_engine, prompt_file, codex_config):
        cmd = codex_engine._build_eval_command(
            track="a", cycle=1, prompt_path=prompt_file,
            session_id="", resume=False, config=codex_config,
        )
        assert cmd[:3] == ["codex", "exec", "--json"]
        assert "--profile" in cmd
        idx_profile = cmd.index("--profile")
        assert cmd[idx_profile + 1] == codex_config.codex_eval_profile
        # Has model flag since codex_eval_model is set
        assert "-m" in cmd
        idx_m = cmd.index("-m")
        assert cmd[idx_m + 1] == "o3"
        # Ends with - for stdin
        assert cmd[-1] == "-"
        # No resume flags
        assert "resume" not in cmd

    def test_codex_fresh_no_model(self, codex_engine, prompt_file, default_config):
        """When codex_eval_model is empty, -m flag should be omitted."""
        cmd = codex_engine._build_eval_command(
            track="a", cycle=1, prompt_path=prompt_file,
            session_id="", resume=False, config=default_config,
        )
        assert "-m" not in cmd
        assert "--profile" in cmd

    def test_codex_resume(self, codex_engine, prompt_file, codex_config):
        session_id = "thread-xyz"
        cmd = codex_engine._build_eval_command(
            track="a", cycle=2, prompt_path=prompt_file,
            session_id=session_id, resume=True, config=codex_config,
        )
        assert cmd[:4] == ["codex", "exec", "resume", "--json"]
        # Resume: NO --profile, NO -m
        assert "--profile" not in cmd
        assert "-m" not in cmd
        # Has -c overrides
        assert "-c" in cmd
        c_indices = [i for i, x in enumerate(cmd) if x == "-c"]
        c_values = [cmd[i + 1] for i in c_indices]
        assert 'sandbox_mode="danger-full-access"' in c_values
        assert 'approval_policy="never"' in c_values
        assert 'shell_environment_policy.inherit="all"' in c_values
        # Has session_id and stdin marker
        assert session_id in cmd
        assert cmd[-1] == "-"


# ---------------------------------------------------------------------------
# _build_fix_command
# ---------------------------------------------------------------------------


class TestBuildFixCommand:

    def test_claude_fresh(self, claude_engine, prompt_file, default_config):
        session_id = "fix-session-1"
        cmd = claude_engine._build_fix_command(
            cycle=1, prompt_path=prompt_file,
            session_id=session_id, resume=False, config=default_config,
        )
        assert cmd[0] == "claude"
        assert "--session-id" in cmd
        assert session_id in cmd
        idx_model = cmd.index("--model")
        assert cmd[idx_model + 1] == default_config.fixer_model
        assert "--allowedTools" not in cmd
        assert "--max-turns" not in cmd

    def test_codex_resume_no_profile_no_model(self, codex_engine, prompt_file, codex_config):
        """Codex resume: omit --profile and -m, re-assert -c overrides."""
        session_id = "thread-abc"
        cmd = codex_engine._build_fix_command(
            cycle=2, prompt_path=prompt_file,
            session_id=session_id, resume=True, config=codex_config,
        )
        assert cmd[:4] == ["codex", "exec", "resume", "--json"]
        assert "--profile" not in cmd
        assert "-m" not in cmd
        c_indices = [i for i, x in enumerate(cmd) if x == "-c"]
        c_values = [cmd[i + 1] for i in c_indices]
        assert 'sandbox_mode="danger-full-access"' in c_values
        assert 'approval_policy="never"' in c_values
        assert 'shell_environment_policy.inherit="all"' in c_values

    def test_codex_fresh_with_model(self, codex_engine, prompt_file):
        """Codex fresh fixer with explicit model."""
        cfg = Config(engine="codex", codex_fixer_model="gpt-4.1")
        cmd = codex_engine._build_fix_command(
            cycle=1, prompt_path=prompt_file,
            session_id="", resume=False, config=cfg,
        )
        assert "--profile" in cmd
        idx_profile = cmd.index("--profile")
        assert cmd[idx_profile + 1] == cfg.codex_fixer_profile
        assert "-m" in cmd
        idx_m = cmd.index("-m")
        assert cmd[idx_m + 1] == "gpt-4.1"


# ---------------------------------------------------------------------------
# Log detection helpers
# ---------------------------------------------------------------------------


class TestDetectRateLimit:

    def test_claude_rejected(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"status":"rejected","reason":"rate limit"}', encoding="utf-8")
        assert claude_engine._detect_rate_limit(log) is True

    def test_claude_hit_your_limit(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("You have hit your limit for this window", encoding="utf-8")
        assert claude_engine._detect_rate_limit(log) is True

    def test_claude_no_rate_limit(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"status":"allowed"}', encoding="utf-8")
        assert claude_engine._detect_rate_limit(log) is False

    def test_codex_always_false(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"status":"rejected"}', encoding="utf-8")
        assert codex_engine._detect_rate_limit(log) is False

    def test_missing_logfile(self, claude_engine, tmp_path):
        log = tmp_path / "nonexistent.log"
        assert claude_engine._detect_rate_limit(log) is False


class TestDetectTransientError:

    def test_claude_api_error_5xx(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("API Error: 500 - internal error", encoding="utf-8")
        assert claude_engine._detect_transient_error(log) is True

    def test_claude_429(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("API Error: 429 - too many requests", encoding="utf-8")
        assert claude_engine._detect_transient_error(log) is True

    def test_codex_reconnecting(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("Reconnecting to stream...", encoding="utf-8")
        assert codex_engine._detect_transient_error(log) is True

    def test_clean_log(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("All checks passed.", encoding="utf-8")
        assert claude_engine._detect_transient_error(log) is False


class TestDetectResumeFailure:

    def test_claude_session_not_found(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("Error: session abc-123 not found", encoding="utf-8")
        assert claude_engine._detect_resume_failure(log) is True

    def test_codex_thread_not_found(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"error":"thread xyz not found"}', encoding="utf-8")
        assert codex_engine._detect_resume_failure(log) is True

    def test_codex_unknown_thread(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("unknown thread ID provided", encoding="utf-8")
        assert codex_engine._detect_resume_failure(log) is True

    def test_no_failure(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("Session resumed successfully", encoding="utf-8")
        assert claude_engine._detect_resume_failure(log) is False


class TestExtractCodexThreadId:

    def test_extracts_thread_id(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text(
            '{"type":"thread.started","thread_id":"thread_abc123","ts":1234567890}\n',
            encoding="utf-8",
        )
        assert codex_engine._extract_codex_thread_id(log) == "thread_abc123"

    def test_no_thread_started(self, codex_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"type":"message","content":"hello"}\n', encoding="utf-8")
        assert codex_engine._extract_codex_thread_id(log) is None

    def test_missing_log(self, codex_engine, tmp_path):
        log = tmp_path / "nonexistent.log"
        assert codex_engine._extract_codex_thread_id(log) is None


class TestExtractRateLimitReset:

    def test_extracts_epoch(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"resetsAt":1712345678,"other":"data"}', encoding="utf-8")
        assert claude_engine._extract_rate_limit_reset(log) == 1712345678

    def test_no_reset(self, claude_engine, tmp_path):
        log = tmp_path / "test.log"
        log.write_text('{"status":"rejected"}', encoding="utf-8")
        assert claude_engine._extract_rate_limit_reset(log) is None


# ---------------------------------------------------------------------------
# Session state persistence
# ---------------------------------------------------------------------------


class TestSessionState:

    def test_write_and_read(self, tmp_run_dir):
        Engine._write_session_id(tmp_run_dir, ".session-eval-a", "sess-123")
        assert Engine._read_session_id(tmp_run_dir, ".session-eval-a") == "sess-123"

    def test_read_missing(self, tmp_run_dir):
        assert Engine._read_session_id(tmp_run_dir, ".session-eval-z") == ""


# ---------------------------------------------------------------------------
# Failure scorecard generation
# ---------------------------------------------------------------------------


class TestWriteFailureScorecard:

    def test_api_error_category_claude(self, claude_engine, tmp_run_dir):
        logfile = tmp_run_dir / "eval-2-track-b.log"
        logfile.write_text("API Error: 500 internal server error\n", encoding="utf-8")

        claude_engine._write_failure_scorecard(
            track="b", cycle=2, logfile=logfile,
            attempts=2, exit_code=1, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-2-track-b.md"
        parts = scorecard.read_text(encoding="utf-8").split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failure_category"] == "API_ERROR"

    def test_agent_error_category_codex(self, codex_engine, tmp_run_dir):
        logfile = tmp_run_dir / "eval-1-track-c.log"
        logfile.write_text('{"type":"error","message":"sandbox denied"}\n', encoding="utf-8")

        codex_engine._write_failure_scorecard(
            track="c", cycle=1, logfile=logfile,
            attempts=1, exit_code=1, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-1-track-c.md"
        parts = scorecard.read_text(encoding="utf-8").split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failure_category"] == "AGENT_ERROR"

    def test_harness_bug_category(self, claude_engine, tmp_run_dir):
        logfile = tmp_run_dir / "eval-1-track-d.log"
        logfile.write_text("some error\n", encoding="utf-8")

        claude_engine._write_failure_scorecard(
            track="d", cycle=1, logfile=logfile,
            attempts=1, exit_code=2, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-1-track-d.md"
        parts = scorecard.read_text(encoding="utf-8").split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failure_category"] == "HARNESS_BUG"

    def test_track_failed_default(self, claude_engine, tmp_run_dir):
        logfile = tmp_run_dir / "eval-1-track-e.log"
        logfile.write_text("something went wrong but no error keyword\n", encoding="utf-8")

        claude_engine._write_failure_scorecard(
            track="e", cycle=1, logfile=logfile,
            attempts=1, exit_code=1, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-1-track-e.md"
        parts = scorecard.read_text(encoding="utf-8").split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failure_category"] == "TRACK_FAILED"

    def test_yaml_single_quote_escaping(self, claude_engine, tmp_run_dir):
        """Failure reason with single quotes is properly YAML-escaped."""
        logfile = tmp_run_dir / "eval-1-track-f.log"
        logfile.write_text("Error: can't parse 'malformed' input\n", encoding="utf-8")

        claude_engine._write_failure_scorecard(
            track="f", cycle=1, logfile=logfile,
            attempts=1, exit_code=1, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-1-track-f.md"
        text = scorecard.read_text(encoding="utf-8")
        # The YAML must be parseable (single quotes doubled inside single-quoted value).
        parts = text.split("---", 2)
        data = yaml.safe_load(parts[1])
        # The parsed value should contain the original single quotes.
        assert "can't" in data["evaluator_failure_reason"]
        assert "'malformed'" in data["evaluator_failure_reason"]

    def test_missing_logfile(self, claude_engine, tmp_run_dir):
        logfile = tmp_run_dir / "nonexistent.log"

        claude_engine._write_failure_scorecard(
            track="a", cycle=1, logfile=logfile,
            attempts=1, exit_code=1, run_dir=tmp_run_dir,
        )

        scorecard = tmp_run_dir / "scorecard-1-track-a.md"
        parts = scorecard.read_text(encoding="utf-8").split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failure_reason"] == "no error line matched in log"


# ---------------------------------------------------------------------------
# Full evaluate() flow — mocked subprocess
# ---------------------------------------------------------------------------


class TestEvaluateFlow:

    def _mock_popen(self, returncode=0, log_content=""):
        """Create a mock Popen that writes to the log file and exits."""
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = returncode
            mock_proc.poll.return_value = returncode
            mock_proc.wait.return_value = returncode
            # Write log content to the stdout file handle
            stdout = kwargs.get("stdout")
            if stdout and log_content:
                stdout.write(log_content)
                stdout.flush()
            return mock_proc
        return popen_side_effect

    @patch("harness.engine.subprocess.Popen")
    def test_happy_path_produces_scorecard_path(
        self, mock_popen_cls, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        """Successful evaluator run — returns scorecard path (even if file doesn't exist yet)."""
        # Simulate the evaluator producing the scorecard file
        scorecard_path = tmp_run_dir / "scorecard-1-track-a.md"
        scorecard_path.write_text("---\ncycle: 1\ntrack: a\nfindings: []\n---\n", encoding="utf-8")

        mock_popen_cls.side_effect = self._mock_popen(returncode=0)

        result = claude_engine.evaluate(
            track="a", cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        assert result == scorecard_path
        # Session state persisted
        session_file = tmp_run_dir / ".session-eval-a"
        assert session_file.exists()

    @patch("harness.engine.subprocess.Popen")
    def test_crash_writes_failure_scorecard(
        self, mock_popen_cls, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        """Evaluator crashes (exit code 1, no scorecard) -> failure scorecard written."""
        mock_popen_cls.side_effect = self._mock_popen(
            returncode=1, log_content="Fatal Error: something broke\n",
        )

        result = claude_engine.evaluate(
            track="a", cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        assert result == tmp_run_dir / "scorecard-1-track-a.md"
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        data = yaml.safe_load(parts[1])
        assert data["evaluator_failed"] is True

    @patch("harness.engine.time.sleep")
    @patch("harness.engine.subprocess.Popen")
    def test_rate_limit_writes_sentinel(
        self, mock_popen_cls, mock_sleep, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        """Rate-limit detected -> writes .rate-limit-hit sentinel, no retry."""
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 1
            mock_proc.poll.return_value = 1
            mock_proc.wait.return_value = 1
            stdout = kwargs.get("stdout")
            if stdout:
                stdout.write('{"status":"rejected","reason":"rate limit"}\n')
                stdout.flush()
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        claude_engine.evaluate(
            track="a", cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        assert (tmp_run_dir / ".rate-limit-hit").exists()
        # Only 1 call — no retries
        assert mock_popen_cls.call_count == 1

    @patch("harness.engine.time.sleep")
    @patch("harness.engine.subprocess.Popen")
    def test_resume_failure_falls_back(
        self, mock_popen_cls, mock_sleep, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        """Resume failure detected -> falls back to fresh session on next attempt."""
        # Write a pre-existing session to trigger resume mode
        (tmp_run_dir / ".session-eval-a").write_text("old-session-id", encoding="utf-8")

        call_count = 0

        def popen_side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            stdout = kwargs.get("stdout")
            if call_count == 1:
                # First call: resume fails
                mock_proc.returncode = 1
                mock_proc.poll.return_value = 1
                mock_proc.wait.return_value = 1
                if stdout:
                    stdout.write("Error: session old-session-id not found\n")
                    stdout.flush()
            else:
                # Second call: fresh session succeeds, write scorecard
                mock_proc.returncode = 0
                mock_proc.poll.return_value = 0
                mock_proc.wait.return_value = 0
                # Simulate evaluator producing a scorecard
                sc = tmp_run_dir / "scorecard-2-track-a.md"
                sc.write_text("---\ncycle: 2\ntrack: a\nfindings: []\n---\n", encoding="utf-8")
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        result = claude_engine.evaluate(
            track="a", cycle=2, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        # Should have retried
        assert call_count == 2
        # First call used --resume, second used --session-id
        first_call_cmd = mock_popen_cls.call_args_list[0][0][0]
        second_call_cmd = mock_popen_cls.call_args_list[1][0][0]
        assert "--resume" in first_call_cmd
        assert "--session-id" in second_call_cmd
        assert "--resume" not in second_call_cmd

    @patch("harness.engine.subprocess.Popen")
    def test_codex_extracts_thread_id(
        self, mock_popen_cls, codex_engine, prompt_file, tmp_run_dir,
    ):
        """Codex first run: extracts thread_id from log on success."""
        config = Config(engine="codex")

        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.poll.return_value = 0
            mock_proc.wait.return_value = 0
            stdout = kwargs.get("stdout")
            if stdout:
                stdout.write('{"type":"thread.started","thread_id":"thread_new_xyz"}\n')
                stdout.flush()
            # Simulate scorecard creation
            sc = tmp_run_dir / "scorecard-1-track-a.md"
            sc.write_text("---\ncycle: 1\ntrack: a\nfindings: []\n---\n", encoding="utf-8")
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        codex_engine.evaluate(
            track="a", cycle=1, prompt_path=prompt_file,
            config=config, run_dir=tmp_run_dir,
        )
        # Session file should contain the extracted thread_id
        session = (tmp_run_dir / ".session-eval-a").read_text(encoding="utf-8").strip()
        assert session == "thread_new_xyz"

    @patch("harness.engine.time.sleep")
    @patch("harness.engine.subprocess.Popen")
    def test_transient_error_retries(
        self, mock_popen_cls, mock_sleep, claude_engine, prompt_file, tmp_run_dir,
    ):
        """Transient error triggers retry with delay."""
        config = Config(max_retries=3, retry_delay=5)
        call_count = 0

        def popen_side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            stdout = kwargs.get("stdout")
            if call_count <= 2:
                mock_proc.returncode = 1
                mock_proc.poll.return_value = 1
                mock_proc.wait.return_value = 1
                if stdout:
                    stdout.write("API Error: 500 - Internal server error\n")
                    stdout.flush()
            else:
                mock_proc.returncode = 0
                mock_proc.poll.return_value = 0
                mock_proc.wait.return_value = 0
                sc = tmp_run_dir / "scorecard-1-track-a.md"
                sc.write_text("---\ncycle: 1\ntrack: a\nfindings: []\n---\n", encoding="utf-8")
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        result = claude_engine.evaluate(
            track="a", cycle=1, prompt_path=prompt_file,
            config=config, run_dir=tmp_run_dir,
        )
        assert call_count == 3
        # sleep called twice (after attempt 1 and 2)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(5)


# ---------------------------------------------------------------------------
# Full fix() flow — mocked subprocess
# ---------------------------------------------------------------------------


class TestFixFlow:

    @patch("harness.engine.subprocess.Popen")
    def test_happy_path_returns_logfile(
        self, mock_popen_cls, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.poll.return_value = 0
            mock_proc.wait.return_value = 0
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        result = claude_engine.fix(
            cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        assert result == tmp_run_dir / "fixer-1.log"
        assert (tmp_run_dir / ".session-fixer").exists()

    @patch("harness.engine.time.sleep")
    @patch("harness.engine.subprocess.Popen")
    def test_rate_limit_writes_sentinel(
        self, mock_popen_cls, mock_sleep, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 1
            mock_proc.poll.return_value = 1
            mock_proc.wait.return_value = 1
            stdout = kwargs.get("stdout")
            if stdout:
                stdout.write("hit your limit\n")
                stdout.flush()
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        claude_engine.fix(
            cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
        )
        assert (tmp_run_dir / ".rate-limit-hit").exists()
        assert mock_popen_cls.call_count == 1

    @patch("harness.engine.subprocess.Popen")
    def test_domain_suffix_isolates_artifacts(
        self, mock_popen_cls, claude_engine, prompt_file, default_config, tmp_run_dir,
    ):
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.poll.return_value = 0
            mock_proc.wait.return_value = 0
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        result = claude_engine.fix(
            cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
            domain_suffix="a",
        )
        assert result == tmp_run_dir / "fixer-1-a.log"
        assert (tmp_run_dir / ".session-fixer-a").exists()
        assert not (tmp_run_dir / ".session-fixer").exists()

    @patch("harness.engine.subprocess.Popen")
    def test_cwd_passed_to_popen(
        self, mock_popen_cls, claude_engine, prompt_file, default_config, tmp_run_dir, tmp_path,
    ):
        def popen_side_effect(cmd, **kwargs):
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.returncode = 0
            mock_proc.poll.return_value = 0
            mock_proc.wait.return_value = 0
            return mock_proc

        mock_popen_cls.side_effect = popen_side_effect

        worktree = tmp_path / "wt"
        worktree.mkdir()
        claude_engine.fix(
            cycle=1, prompt_path=prompt_file,
            config=default_config, run_dir=tmp_run_dir,
            cwd=worktree,
        )
        _, kwargs = mock_popen_cls.call_args
        assert kwargs["cwd"] == worktree



# ---------------------------------------------------------------------------
# _terminate_process
# ---------------------------------------------------------------------------


class TestTerminateProcess:

    def test_already_exited(self):
        proc = MagicMock()
        proc.poll.return_value = 0
        _terminate_process(proc)
        proc.terminate.assert_not_called()

    @patch("harness.engine._supports_process_groups", return_value=True)
    @patch("harness.engine.os.killpg")
    def test_sigterm_then_exit(self, mock_killpg, mock_pg):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.pid = 999
        proc.wait.return_value = 0
        _terminate_process(proc)
        mock_killpg.assert_called_once_with(999, signal.SIGTERM)

    @patch("harness.engine._supports_process_groups", return_value=True)
    @patch("harness.engine.os.killpg")
    def test_sigterm_timeout_then_sigkill(self, mock_killpg, mock_pg):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.pid = 999
        proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), 0]
        _terminate_process(proc)
        assert mock_killpg.call_count == 2
        mock_killpg.assert_any_call(999, signal.SIGTERM)
        mock_killpg.assert_any_call(999, signal.SIGKILL)

    @patch("harness.engine._supports_process_groups", return_value=False)
    def test_fallback_terminate(self, mock_pg):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.wait.return_value = 0
        _terminate_process(proc)
        proc.terminate.assert_called_once()
