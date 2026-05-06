"""Multi-provider CLI dispatch wrapper for Stage 1b/1c/2/3/4 agent calls.

Mirrors the pattern at ``autoresearch/evolve.py:359-405`` (claude / codex /
opencode subprocess machinery) and applies retry semantics from
``autoresearch/agent_retry.py`` per master plan §3.5 + §3.10.

Shape:
    result = await run(
        prompt="...",
        model="opus",
        session_id="...",
        backend="claude",
        cwd=audit_dir,
        max_turns=8,
    )
    # result.text — agent's final text output (last result message)
    # result.cost_usd — Anthropic's reported cost (or 0.0 when subscription)
    # result.session_id — session identifier (for resume)
    # result.duration_ms — wall-clock
    # result.transcript_path — path to streamed log file (optional)

Tests can inject a fake runner by passing ``agent_runner=`` into stage
functions; the contract is only ``await runner.run(...) -> AgentRunResult``.

L3 lands the orchestration layer + the dispatch shape. L4 wires real CLI
execution against the customer-facing pipeline; this module is the
single seam between "Python orchestration" and "subprocess CLI agent."

Cost capture: every call goes through ``cost_ledger.record(...)`` if a
ledger is supplied — bookkeeping flows through one site so per-stage
cost rollup in ``cost_actual.json`` stays consistent (master plan §3.9).
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from autoresearch import agent_retry
from src.audit import claude_subprocess
from src.audit.claude_subprocess import (
    build_cmd_meta,
    build_cmd_short_json,
    build_cmd_streaming,
    build_env,
    parse_result_message,
    parse_rate_limit,
)
from src.audit.cost_ledger import CostLedger
from src.audit.exceptions import AuditError


Backend = Literal["claude", "codex", "opencode"]


@dataclass(frozen=True)
class AgentRunResult:
    """Structured result from a single agent CLI invocation.

    ``text`` is the agent's final text output (parsed from claude's JSON
    envelope or codex/opencode stdout). ``cost_usd`` is Anthropic's
    reported cost (typically 0 on subscription); ``duration_ms`` is
    wall-clock; ``transcript_path`` points at the streamed log if one
    was captured.
    """

    text: str
    cost_usd: float
    session_id: str
    duration_ms: int
    backend: Backend
    model: str
    role: str
    transcript_path: Path | None = None
    raw_envelope: dict[str, Any] | None = None
    attempts: int = 1


class AgentRunFailed(AuditError):
    """Raised after retry exhaustion or terminal subprocess failure."""

    def __init__(self, role: str, returncode: int, stdout: str, stderr: str) -> None:
        self.role = role
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"agent CLI failed: role={role} rc={returncode} "
            f"stderr_head={stderr[:200] if stderr else '<empty>'!r}"
        )


@dataclass
class AgentRunner:
    """Default implementation that subprocesses claude / codex / opencode.

    Pattern selection mirrors ``src/audit/claude_subprocess.py`` factories:
    - ``pattern="streaming"`` → ``build_cmd_streaming`` (long-form, per-agent
      Stage 2 lens fan-outs that benefit from --resume / stream-json)
    - ``pattern="meta"`` → ``build_cmd_meta`` (Stage 1b multi-turn discovery,
      Stage 1c brief, Stage 3 synthesis, Stage 4 proposal — prompt via stdin)
    - ``pattern="short_json"`` → ``build_cmd_short_json`` (judges + critics)

    Codex / opencode dispatch uses argv-based prompts (no stdin pipe
    available for the autoresearch evolve pattern). Future Stage 2 fan-outs
    that need codex/opencode will land in v2; v1 defaults to claude.
    """

    default_backend: Backend = "claude"
    transcripts_dir: Path | None = None  # if set, log streamed output per call

    async def run(
        self,
        *,
        prompt: str,
        model: str,
        role: str,
        session_id: str | None = None,
        backend: Backend | None = None,
        cwd: Path,
        max_turns: int = 8,
        allowed_tools: str | None = None,
        ledger: CostLedger | None = None,
        metadata: dict[str, Any] | None = None,
        pattern: Literal["streaming", "meta", "short_json"] = "meta",
    ) -> AgentRunResult:
        be: Backend = backend or self.default_backend
        if not cwd.is_dir():
            raise AuditError(f"agent_runner: cwd is not a directory: {cwd}")
        sid = session_id or str(uuid.uuid4())

        attempts_used = 0
        last_returncode = 0
        last_stdout = ""
        last_stderr = ""
        max_attempts = agent_retry.max_attempts()
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            try:
                result = await self._spawn_once(
                    prompt=prompt, model=model, role=role,
                    session_id=sid, backend=be, cwd=cwd,
                    max_turns=max_turns, allowed_tools=allowed_tools,
                    ledger=ledger, metadata=metadata, pattern=pattern,
                    attempts=attempt,
                )
                return result
            except _TransientAgentFailure as exc:
                last_returncode = exc.returncode
                last_stdout = exc.stdout
                last_stderr = exc.stderr
                if attempt >= max_attempts:
                    break
                agent_retry.sleep_for_retry(attempt)

        raise AgentRunFailed(role=role, returncode=last_returncode,
                             stdout=last_stdout, stderr=last_stderr)

    async def _spawn_once(
        self,
        *,
        prompt: str,
        model: str,
        role: str,
        session_id: str,
        backend: Backend,
        cwd: Path,
        max_turns: int,
        allowed_tools: str | None,
        ledger: CostLedger | None,
        metadata: dict[str, Any] | None,
        pattern: str,
        attempts: int,
    ) -> AgentRunResult:
        """Single subprocess attempt; raises ``_TransientAgentFailure`` on a
        retryable failure or returns ``AgentRunResult`` on success / terminal
        failure handled inline."""
        env = build_env()
        cmd = self._build_cmd(
            prompt=prompt, model=model, session_id=session_id,
            backend=backend, cwd=cwd, max_turns=max_turns,
            allowed_tools=allowed_tools, pattern=pattern,
        )

        log_path: Path | None = None
        if self.transcripts_dir is not None:
            self.transcripts_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.transcripts_dir / f"{role}_{session_id}_attempt{attempts}.log"

        started = time.monotonic()

        # Run the subprocess in a worker thread so we don't block the event
        # loop. Stage 2's asyncio.gather over 4 agents needs concurrent
        # subprocesses; using asyncio.create_subprocess_exec would be ideal
        # but adds complexity — to_thread keeps the dispatch simple and is
        # good enough for the 4-agent fan-out scale.
        proc_result = await asyncio.to_thread(
            self._run_subprocess_blocking,
            cmd=cmd, prompt=prompt, env=env, cwd=cwd,
            backend=backend, pattern=pattern, log_path=log_path,
        )
        duration_ms = int((time.monotonic() - started) * 1000)

        returncode = proc_result["returncode"]
        stdout = proc_result["stdout"]
        stderr = proc_result["stderr"]

        # Rate-limit interception (claude only, streaming logs)
        if log_path is not None and backend == "claude":
            rl = parse_rate_limit(log_path)
            if rl is not None:
                # Rate limit is a terminal halt, not transient retry — propagate
                raise rl

        if returncode != 0:
            if agent_retry.is_transient_failure(backend, returncode, stdout, stderr):
                raise _TransientAgentFailure(returncode=returncode, stdout=stdout, stderr=stderr)
            # Terminal failure
            raise AgentRunFailed(role=role, returncode=returncode,
                                 stdout=stdout, stderr=stderr)

        # Parse output — claude (--output-format json) emits a JSON envelope;
        # codex / opencode emit raw text or JSON depending on flags.
        text, cost_usd, raw_envelope = self._parse_output(
            stdout=stdout, backend=backend, pattern=pattern,
        )

        if ledger is not None and raw_envelope is not None:
            try:
                rm = parse_result_message(raw_envelope)
                ledger.record(role=role, result=rm, model=model, metadata=metadata)
            except ValueError:
                # Non-claude pattern or non-result envelope: fall through with cost=0.
                pass

        return AgentRunResult(
            text=text,
            cost_usd=cost_usd,
            session_id=session_id,
            duration_ms=duration_ms,
            backend=backend,
            model=model,
            role=role,
            transcript_path=log_path,
            raw_envelope=raw_envelope,
            attempts=attempts,
        )

    def _build_cmd(
        self,
        *,
        prompt: str,
        model: str,
        session_id: str,
        backend: Backend,
        cwd: Path,
        max_turns: int,
        allowed_tools: str | None,
        pattern: str,
    ) -> list[str]:
        if backend == "claude":
            if pattern == "streaming":
                return build_cmd_streaming(
                    prompt=prompt, model=model, session_id=session_id, cwd=cwd,
                    max_turns=max_turns,
                )
            if pattern == "short_json":
                return build_cmd_short_json(
                    prompt=prompt, model=model, cwd=cwd, session_id=session_id,
                )
            # default = meta
            cmd = build_cmd_meta(
                model=model, max_turns=max_turns, cwd=cwd,
                allowed_tools=allowed_tools,
            )
            cmd += ["--session-id", session_id]
            return cmd
        if backend == "codex":
            return [
                "codex", "exec",
                "--model", model,
                "--sandbox", os.environ.get("CODEX_SANDBOX", "danger-full-access"),
                "--color", "never",
                "-c", f'approval_policy="{os.environ.get("CODEX_APPROVAL_POLICY", "never")}"',
                "-c", f'model_reasoning_effort="{os.environ.get("CODEX_REASONING_EFFORT", "high")}"',
                "-c", f'web_search="{os.environ.get("CODEX_WEB_SEARCH", "disabled")}"',
                "-C", str(cwd),
                "-",
            ]
        if backend == "opencode":
            return [
                "opencode", "run",
                "--dangerously-skip-permissions",
                "-m", model,
                "--format", "json",
                prompt,
            ]
        raise ValueError(f"unknown backend: {backend!r}")

    def _run_subprocess_blocking(
        self,
        *,
        cmd: list[str],
        prompt: str,
        env: dict[str, str],
        cwd: Path,
        backend: Backend,
        pattern: str,
        log_path: Path | None,
    ) -> dict[str, Any]:
        """Synchronous subprocess call run in a worker thread.

        Pipes ``prompt`` via stdin for claude (-p) and codex (trailing "-").
        opencode reads prompt from argv (already in ``cmd``).
        """
        stdin_handle: Any
        if backend == "opencode":
            stdin_handle = subprocess.DEVNULL
        else:
            stdin_handle = subprocess.PIPE

        try:
            proc = subprocess.Popen(
                cmd, env=env, cwd=str(cwd),
                stdin=stdin_handle,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            # CLI not installed (claude / codex / opencode missing on PATH).
            # Surface as terminal failure — caller turns this into AgentRunFailed
            # via _TransientAgentFailure path being skipped.
            return {
                "returncode": 127,
                "stdout": "",
                "stderr": f"agent CLI not found on PATH: {exc}",
            }

        if backend == "opencode":
            stdout_b, stderr_b = proc.communicate()
        else:
            stdout_b, stderr_b = proc.communicate(input=prompt.encode("utf-8"))

        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")

        if log_path is not None:
            try:
                log_path.write_text(stdout, encoding="utf-8")
            except OSError:
                pass

        return {"returncode": proc.returncode, "stdout": stdout, "stderr": stderr}

    def _parse_output(
        self,
        *,
        stdout: str,
        backend: Backend,
        pattern: str,
    ) -> tuple[str, float, dict[str, Any] | None]:
        """Best-effort extraction of (text, cost, envelope) per backend.

        - claude meta / short_json: JSON envelope on stdout → parse.
        - claude streaming: stream-json events → no single envelope; the
          text is whatever's in the log; cost defaults to 0.
        - codex: raw text on stdout; cost not exposed.
        - opencode: JSON wrapper if --format json; text under ``"output"`` key.
        """
        text = stdout
        cost_usd = 0.0
        envelope: dict[str, Any] | None = None

        if backend == "claude" and pattern in ("meta", "short_json"):
            try:
                envelope = json.loads(stdout.strip())
                if isinstance(envelope, dict):
                    text = envelope.get("result") or envelope.get("text") or stdout
                    cost_usd = float(envelope.get("total_cost_usd", 0.0) or 0.0)
            except (json.JSONDecodeError, ValueError):
                envelope = None
        elif backend == "opencode":
            try:
                envelope = json.loads(stdout.strip())
                if isinstance(envelope, dict):
                    text = envelope.get("output") or envelope.get("text") or stdout
            except (json.JSONDecodeError, ValueError):
                envelope = None

        return text, cost_usd, envelope


@dataclass
class _TransientAgentFailure(Exception):
    """Internal sentinel — raised from ``_spawn_once`` so the retry loop
    can sleep + retry."""

    returncode: int
    stdout: str
    stderr: str


__all__ = [
    "AgentRunner",
    "AgentRunFailed",
    "AgentRunResult",
    "Backend",
]
