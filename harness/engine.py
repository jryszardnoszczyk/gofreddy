"""Engine abstraction for the QA eval-fix harness.

Replaces the unified ``run_evaluator()`` and ``run_fixer()`` bash functions
with a Python class that handles both claude and codex CLI invocation,
retry/resume/error logic, and failure scorecard generation.
"""

from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from harness.config import Config

logger = logging.getLogger(__name__)

# Grace period (seconds) between SIGTERM and SIGKILL on timeout.
_KILL_GRACE_SECONDS = 5


def _supports_process_groups() -> bool:
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def _terminate_process(process: subprocess.Popen, grace_seconds: int = _KILL_GRACE_SECONDS) -> None:
    """SIGTERM the process group, wait, then SIGKILL if still alive."""
    if process.poll() is not None:
        return
    try:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        if _supports_process_groups():
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


class Engine:
    """Drives evaluator and fixer sessions for a single engine type.

    Supports ``"claude"`` and ``"codex"`` engines with engine-specific
    CLI flag construction and log parsing.  Uses if-branching, not
    class hierarchy (plan decision: only 2 engines).
    """

    def __init__(self, name: str) -> None:
        if name not in ("claude", "codex"):
            raise ValueError(f"Unknown engine: {name!r}")
        self.name = name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        track: str,
        cycle: int,
        prompt_path: Path,
        config: Config,
        run_dir: Path,
    ) -> Path:
        """Run the evaluator for *track* and return the scorecard path.

        Handles retry loop, session management, and writes a failure
        scorecard if the evaluator did not produce one.
        """
        scorecard = run_dir / f"scorecard-{cycle}-track-{track}.md"
        logfile = run_dir / f"eval-{cycle}-track-{track}.log"

        session_id = self._read_session_id(run_dir, f".session-eval-{track}")
        if not session_id and self.name == "claude":
            session_id = str(uuid.uuid4())

        resume = cycle > 1 and bool(session_id)

        attempt = 0
        last_exit_code = 0

        while attempt < config.max_retries:
            attempt += 1
            logger.info(
                "Evaluator %s (engine=%s, cycle %d, attempt %d/%d)",
                track.upper(), self.name, cycle, attempt, config.max_retries,
            )
            last_exit_code = 0

            cmd = self._build_eval_command(
                track, cycle, prompt_path, session_id, resume, config,
            )
            last_exit_code = self._run_subprocess(
                cmd, logfile, prompt_path, is_claude=(self.name == "claude"),
            )

            # On codex first success, capture thread_id for future resume.
            if last_exit_code == 0 and self.name == "codex" and not resume:
                tid = self._extract_codex_thread_id(logfile)
                if tid:
                    session_id = tid

            if last_exit_code == 0:
                break

            # Rate limit (claude only).
            if self.name == "claude" and self._detect_rate_limit(logfile):
                logger.warning("Track %s hit CLAUDE RATE LIMIT", track.upper())
                (run_dir / ".rate-limit-hit").touch()
                break

            # Transient error — retry with delay.
            if self._detect_transient_error(logfile) and attempt < config.max_retries:
                logger.warning(
                    "Track %s transient error (attempt %d/%d)",
                    track.upper(), attempt, config.max_retries,
                )
                time.sleep(config.retry_delay)
                continue

            # Resume failure — fall back to fresh session.
            if resume and self._detect_resume_failure(logfile):
                logger.warning("Track %s resume failed — fresh session", track.upper())
                if self.name == "codex":
                    session_id = ""
                else:
                    session_id = str(uuid.uuid4())
                resume = False
                continue

            # Non-recoverable error.
            break

        # Persist session state.
        self._write_session_id(run_dir, f".session-eval-{track}", session_id)

        # Write failure scorecard if the evaluator didn't produce one.
        if not scorecard.exists():
            capped_attempts = min(attempt, config.max_retries)
            self._write_failure_scorecard(
                track, cycle, logfile, capped_attempts, last_exit_code, run_dir,
            )

        return scorecard

    def fix(
        self,
        cycle: int,
        prompt_path: Path,
        config: Config,
        run_dir: Path,
        *,
        domain_suffix: str = "",
        cwd: Path | None = None,
    ) -> Path:
        """Run the fixer and return the log path.

        Same retry/resume/error logic as evaluate but with fixer-specific
        config and no scorecard generation.

        *domain_suffix* isolates per-domain artifacts (log, session file).
        *cwd* sets the working directory for the subprocess.
        """
        suffix = f"-{domain_suffix}" if domain_suffix else ""
        logfile = run_dir / f"fixer-{cycle}{suffix}.log"
        session_file = f".session-fixer{suffix}"

        session_id = self._read_session_id(run_dir, session_file)
        if not session_id and self.name == "claude":
            session_id = str(uuid.uuid4())

        resume = cycle > 1 and bool(session_id)

        attempt = 0
        last_exit_code = 0

        while attempt < config.max_retries:
            attempt += 1
            logger.info(
                "Fixer (engine=%s, cycle %d%s, attempt %d/%d)",
                self.name, cycle,
                f", domain={domain_suffix}" if domain_suffix else "",
                attempt, config.max_retries,
            )
            last_exit_code = 0

            cmd = self._build_fix_command(
                cycle, prompt_path, session_id, resume, config,
            )
            last_exit_code = self._run_subprocess(
                cmd, logfile, prompt_path,
                is_claude=(self.name == "claude"),
                cwd=cwd,
            )

            # Codex first success — capture thread_id.
            if last_exit_code == 0 and self.name == "codex" and not resume:
                tid = self._extract_codex_thread_id(logfile)
                if tid:
                    session_id = tid

            if last_exit_code == 0:
                break

            # Rate limit (claude only).
            if self.name == "claude" and self._detect_rate_limit(logfile):
                logger.warning("Fixer hit CLAUDE RATE LIMIT")
                (run_dir / ".rate-limit-hit").touch()
                break

            # Transient error — retry.
            if self._detect_transient_error(logfile) and attempt < config.max_retries:
                logger.warning(
                    "Fixer transient error (attempt %d/%d)",
                    attempt, config.max_retries,
                )
                time.sleep(config.retry_delay)
                continue

            # Resume failure — fresh session.
            if resume and self._detect_resume_failure(logfile):
                logger.warning("Fixer resume failed — fresh session")
                if self.name == "codex":
                    session_id = ""
                else:
                    session_id = str(uuid.uuid4())
                resume = False
                continue

            break

        self._write_session_id(run_dir, session_file, session_id)
        return logfile

    def verify(
        self,
        cycle: int,
        prompt_path: Path,
        config: Config,
        run_dir: Path,
        *,
        domain_suffix: str,
        cwd: Path | None = None,
    ) -> Path:
        """Run the verifier for one domain and return the log path.

        Single-shot, no retries, fresh session every cycle (the verifier's
        anti-bias rule — a mid-run verifier must not share state with a
        prior cycle). If the subprocess crashes or times out, the caller
        treats a missing/unparseable verdict file as FAILED and forces
        rollback, which is safer than a partial success.
        """
        if not domain_suffix:
            raise ValueError("verify() requires a non-empty domain_suffix")

        logfile = run_dir / f"verifier-{cycle}-{domain_suffix}.log"

        logger.info(
            "Verifier (engine=%s, cycle %d, domain=%s)",
            self.name, cycle, domain_suffix,
        )

        cmd = self._build_verify_command(prompt_path, config)
        self._run_subprocess(
            cmd, logfile, prompt_path,
            is_claude=(self.name == "claude"),
            cwd=cwd,
        )

        return logfile

    # ------------------------------------------------------------------
    # Command construction
    # ------------------------------------------------------------------

    def _build_eval_command(
        self,
        track: str,
        cycle: int,
        prompt_path: Path,
        session_id: str,
        resume: bool,
        config: Config,
    ) -> list[str]:
        """Build the CLI argument list for an evaluator invocation."""
        if self.name == "claude":
            content = prompt_path.read_text(encoding="utf-8")
            cmd = ["claude", "-p", content,
                   "--output-format", "stream-json",
                   "--include-partial-messages", "--verbose"]
            if resume and session_id:
                cmd += ["--resume", session_id]
            elif session_id:
                cmd += ["--session-id", session_id]
            cmd += ["--model", config.eval_model,
                    "--dangerously-skip-permissions"]
            return cmd

        # codex
        if resume and session_id:
            return [
                "codex", "exec", "resume", "--json",
                "-c", 'sandbox_mode="danger-full-access"',
                "-c", 'approval_policy="never"',
                "-c", 'shell_environment_policy.inherit="all"',
                session_id, "-",
            ]

        cmd = ["codex", "exec", "--json", "--profile", config.codex_eval_profile]
        if config.codex_eval_model:
            cmd += ["-m", config.codex_eval_model]
        cmd.append("-")
        return cmd

    def _build_fix_command(
        self,
        cycle: int,
        prompt_path: Path,
        session_id: str,
        resume: bool,
        config: Config,
    ) -> list[str]:
        """Build the CLI argument list for a fixer invocation."""
        if self.name == "claude":
            content = prompt_path.read_text(encoding="utf-8")
            cmd = ["claude", "-p", content,
                   "--output-format", "stream-json",
                   "--include-partial-messages", "--verbose"]
            if resume and session_id:
                cmd += ["--resume", session_id]
            elif session_id:
                cmd += ["--session-id", session_id]
            cmd += ["--model", config.fixer_model,
                    "--dangerously-skip-permissions"]
            return cmd

        # codex
        if resume and session_id:
            return [
                "codex", "exec", "resume", "--json",
                "-c", 'sandbox_mode="danger-full-access"',
                "-c", 'approval_policy="never"',
                "-c", 'shell_environment_policy.inherit="all"',
                session_id, "-",
            ]

        cmd = ["codex", "exec", "--json", "--profile", config.codex_fixer_profile]
        if config.codex_fixer_model:
            cmd += ["-m", config.codex_fixer_model]
        cmd.append("-")
        return cmd

    def _build_verify_command(
        self,
        prompt_path: Path,
        config: Config,
    ) -> list[str]:
        """Build the CLI argument list for a verifier invocation.

        Always starts a fresh session (never resumes) — the verifier must
        not carry state across cycles. Uses a minimal ``Bash``-only tool
        surface on claude because the verifier touches only
        ``playwright-cli`` and the pristine test matrix, never product
        code. Codex model falls back to the fixer model when no explicit
        verifier model is configured.
        """
        if self.name == "claude":
            content = prompt_path.read_text(encoding="utf-8")
            cmd = ["claude", "-p", content,
                   "--output-format", "stream-json",
                   "--include-partial-messages", "--verbose",
                   "--model", config.fixer_model,
                   "--dangerously-skip-permissions"]
            return cmd

        # codex — always fresh session (no resume branch)
        model = config.codex_verifier_model or config.codex_fixer_model
        cmd = ["codex", "exec", "--json", "--profile", config.codex_verifier_profile]
        if model:
            cmd += ["-m", model]
        cmd.append("-")
        return cmd

    # ------------------------------------------------------------------
    # Log detection helpers
    # ------------------------------------------------------------------

    def _detect_rate_limit(self, logfile: Path) -> bool:
        """Claude 5-hour rate limit (NOT transient). Only claude engine."""
        if self.name != "claude":
            return False
        if not logfile.exists():
            return False
        text = logfile.read_text(encoding="utf-8", errors="replace")
        return '"status":"rejected"' in text or "hit your limit" in text

    def _detect_transient_error(self, logfile: Path) -> bool:
        """Engine-specific transient error patterns."""
        if not logfile.exists():
            return False
        text = logfile.read_text(encoding="utf-8", errors="replace")
        if self.name == "claude":
            return bool(re.search(
                r"API Error: 5|API Error: 429|overloaded|Internal server error",
                text,
            ))
        # codex
        return bool(re.search(
            r'"type":"error"|429|50[0-9]|overloaded|Internal server error|Reconnecting|stream disconnected|rate limit',
            text,
            re.IGNORECASE,
        ))

    def _detect_resume_failure(self, logfile: Path) -> bool:
        """Detect that a session resume failed (session/thread not found)."""
        if not logfile.exists():
            return False
        text = logfile.read_text(encoding="utf-8", errors="replace")
        if self.name == "claude":
            return bool(re.search(
                r"session.*not found|invalid session|no session",
                text,
                re.IGNORECASE,
            ))
        return bool(re.search(
            r"thread.*not found|session.*not found|unknown thread|invalid session|no session",
            text,
            re.IGNORECASE,
        ))

    def _extract_codex_thread_id(self, logfile: Path) -> str | None:
        """Extract thread_id from a codex ``thread.started`` JSON event."""
        if not logfile.exists():
            return None
        text = logfile.read_text(encoding="utf-8", errors="replace")
        # Match the JSON pattern: "type":"thread.started" ... "thread_id":"<id>"
        m = re.search(r'"type"\s*:\s*"thread\.started"[^}]*"thread_id"\s*:\s*"([^"]+)"', text)
        return m.group(1) if m else None

    def _extract_rate_limit_reset(self, logfile: Path) -> int | None:
        """Extract ``resetsAt`` epoch from a claude rate-limit log."""
        if not logfile.exists():
            return None
        text = logfile.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'"resetsAt":(\d+)', text)
        return int(m.group(1)) if m else None

    # ------------------------------------------------------------------
    # Subprocess lifecycle
    # ------------------------------------------------------------------

    def _run_subprocess(
        self,
        cmd: list[str],
        logfile: Path,
        prompt_path: Path,
        *,
        is_claude: bool,
        cwd: Path | None = None,
    ) -> int:
        """Run *cmd*, stream output to *logfile*, return exit code.

        For claude: stdout/stderr go to logfile, no stdin.
        For codex: stdin comes from prompt_path, stdout/stderr go to logfile.

        *cwd* sets the working directory for the subprocess.

        The outer HARNESS_MAX_WALLTIME watchdog is the only backstop — this
        helper waits for the agent to finish on its own.
        """
        use_pg = _supports_process_groups()
        stdin_handle = None
        log_handle = open(logfile, "w", encoding="utf-8")  # noqa: SIM115

        # Prepend worktree's .venv/bin to PATH so the evaluator's shell can
        # resolve `freddy` (and any other entry points installed by the
        # project) without relying on external shims.
        env = os.environ.copy()
        if cwd is not None:
            venv_bin = Path(cwd) / ".venv" / "bin"
            if venv_bin.exists():
                env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

        try:
            if not is_claude:
                stdin_handle = open(prompt_path, "r", encoding="utf-8")  # noqa: SIM115

            process = subprocess.Popen(
                cmd,
                stdin=stdin_handle,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=use_pg,
                cwd=cwd,
                env=env,
            )

            process.wait()
            return process.returncode

        finally:
            log_handle.close()
            if stdin_handle is not None:
                stdin_handle.close()

    # ------------------------------------------------------------------
    # Session state persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _read_session_id(run_dir: Path, filename: str) -> str:
        """Read a session ID from a dotfile, or return empty string."""
        path = run_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return ""

    @staticmethod
    def _write_session_id(run_dir: Path, filename: str, session_id: str) -> None:
        """Persist a session ID to a dotfile."""
        (run_dir / filename).write_text(session_id, encoding="utf-8")

    # ------------------------------------------------------------------
    # Failure scorecard
    # ------------------------------------------------------------------

    def _write_failure_scorecard(
        self,
        track: str,
        cycle: int,
        logfile: Path,
        attempts: int,
        exit_code: int,
        run_dir: Path,
    ) -> None:
        """Write a synthetic failure scorecard with ``evaluator_failed: true``."""
        scorecard_path = run_dir / f"scorecard-{cycle}-track-{track}.md"

        category = self._classify_failure(logfile, exit_code)
        reason = self._extract_failure_reason(logfile)

        # YAML single-quote doubling (matches bash line 936).
        reason_q = reason.replace("'", "''")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.warning(
            "Track %s failed after %d attempt(s): %s exit=%d",
            track.upper(), attempts, category, exit_code,
        )

        frontmatter = (
            f"---\n"
            f"track: {track}\n"
            f"cycle: {cycle}\n"
            f"timestamp: {timestamp}\n"
            f"pass: 0\n"
            f"partial: 0\n"
            f"fail: 0\n"
            f"blocked: 0\n"
            f"evaluator_failed: true\n"
            f"evaluator_failure_category: '{category}'\n"
            f"evaluator_failure_reason: '{reason_q}'\n"
            f"evaluator_exit_code: {exit_code}\n"
            f"findings: []\n"
            f"---\n"
        )

        body = (
            f"## Track {track.upper()} — Evaluator Failed ({category})\n"
            f"\n"
            f"- **Category**: {category}\n"
            f"- **Attempts**: {attempts}\n"
            f"- **Exit code**: {exit_code}\n"
            f"- **Reason**: {reason}\n"
        )

        scorecard_path.write_text(frontmatter + body, encoding="utf-8")

    def _classify_failure(self, logfile: Path, exit_code: int) -> str:
        """Determine failure category from exit code and log content."""
        if exit_code == 2:
            return "HARNESS_BUG"

        if not logfile.exists():
            return "TRACK_FAILED"

        text = logfile.read_text(encoding="utf-8", errors="replace")
        if self.name == "claude" and "API Error" in text:
            return "API_ERROR"
        if self.name == "codex" and '"type":"error"' in text:
            return "AGENT_ERROR"

        return "TRACK_FAILED"

    @staticmethod
    def _extract_failure_reason(logfile: Path) -> str:
        """Extract the first error line from the log, truncated to 240 chars."""
        if not logfile.exists():
            return "no error line matched in log"
        text = logfile.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if re.search(r"Error|error|ERROR", line):
                return line[:240]
        return "no error line matched in log"
