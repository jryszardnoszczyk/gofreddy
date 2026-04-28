"""Async wrappers around ``claude``, ``codex``, and ``opencode`` CLI binaries.

These run on the judge-service host only. Authentication lives in the CLI
tools' subscription login state — no API keys, no env-var fallback. Each
CLI has its own semaphore-bounded pool; the pool size is the conservative
starting default and is bumped via config when observation shows headroom
without throttling.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path


CLAUDE_POOL_SIZE = 3
CODEX_POOL_SIZE = 3
OPENCODE_POOL_SIZE = 3

_claude_sem = asyncio.Semaphore(CLAUDE_POOL_SIZE)
_codex_sem = asyncio.Semaphore(CODEX_POOL_SIZE)
_opencode_sem = asyncio.Semaphore(OPENCODE_POOL_SIZE)


async def invoke_claude(
    prompt: str, *, model: str = "claude-opus-4-7", timeout: int = 900,
) -> str:
    """Invoke the ``claude`` CLI; return stdout. RuntimeError on failure.

    Default timeout is 900s (15 min). Long-form session-judge critiques on
    multi-KB artifacts with high-thinking effort regularly exceed 5 min;
    300s was producing false 500s under realistic load.

    Prompt is fed via stdin, NOT as a CLI argument. Passing large prompts
    as argv hits the kernel's ARG_MAX (~256KB on macOS, ~2MB on Linux) when
    the variant_scorer packs all session artifacts into the prompt. stdin
    has no such limit.
    """
    async with _claude_sem:
        proc = await asyncio.create_subprocess_exec(
            "claude", "--model", model, "--print",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"claude CLI timeout after {timeout}s")
        if proc.returncode != 0:
            preview = stderr.decode(errors="replace")[:500]
            raise RuntimeError(
                f"claude CLI exit {proc.returncode}: {preview}"
            )
        return stdout.decode()


async def invoke_codex(
    prompt: str, *, model: str = "gpt-5.4", timeout: int = 900,
) -> str:
    """Invoke the ``codex`` CLI; return stdout. RuntimeError on failure.

    Default timeout 900s (15 min) — see invoke_claude rationale.
    Prompt fed via stdin (``codex exec -``) to avoid ARG_MAX on large
    artifact payloads.
    """
    async with _codex_sem:
        # codex exec reads from stdin when no prompt is given (its --help:
        # "instructions are read from stdin").
        proc = await asyncio.create_subprocess_exec(
            "codex", "exec", "--model", model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"codex CLI timeout after {timeout}s")
        if proc.returncode != 0:
            preview = stderr.decode(errors="replace")[:500]
            raise RuntimeError(
                f"codex CLI exit {proc.returncode}: {preview}"
            )
        return stdout.decode()


def _resolve_opencode_bin() -> str:
    """Find the opencode binary. ENV override > PATH > XDG install location."""
    explicit = os.environ.get("OPENCODE_BIN")
    if explicit:
        return explicit
    on_path = shutil.which("opencode")
    if on_path:
        return on_path
    xdg = Path.home() / ".opencode" / "bin" / "opencode"
    if xdg.exists():
        return str(xdg)
    raise RuntimeError(
        "opencode CLI not found on PATH or at ~/.opencode/bin/opencode "
        "(set OPENCODE_BIN to override)"
    )


async def invoke_opencode(
    prompt: str,
    *,
    model: str = "openrouter/deepseek/deepseek-v4-pro",
    timeout: int = 900,
) -> str:
    """Invoke the ``opencode`` CLI; return final-answer text. RuntimeError on failure.

    Default timeout 900s (15 min). The prompt is written to a temp file and
    attached via ``-f`` rather than passed as argv, since judge prompts
    routinely exceed ARG_MAX after artifact packing. The tiny positional
    message tells the model to follow the attached instructions.

    opencode emits structured JSONL on stdout when ``--format json`` is set.
    We parse it with the canonical autoresearch parser to extract the model's
    final answer text — that's the JSON verdict block the variant_scorer
    expects.
    """
    bin_path = _resolve_opencode_bin()

    # Late import: keeps judges importable on judge-only deployments where
    # autoresearch isn't installed, until opencode is actually invoked.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from autoresearch.harness.opencode_jsonl import parse_session  # noqa: E402

    async with _opencode_sem:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_path = Path(tmpdir) / "prompt.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            log_path = Path(tmpdir) / "session.jsonl"

            proc = await asyncio.create_subprocess_exec(
                bin_path, "run", "--dangerously-skip-permissions",
                "-m", model, "--format", "json",
                "-f", str(prompt_path),
                "Follow the instructions in the attached prompt file. "
                "Return ONLY the JSON verdict block requested by those instructions.",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise RuntimeError(f"opencode CLI timeout after {timeout}s")

            if proc.returncode != 0:
                preview = stderr.decode(errors="replace")[:500]
                raise RuntimeError(
                    f"opencode CLI exit {proc.returncode}: {preview}"
                )

            log_path.write_bytes(stdout)
            summary = parse_session(log_path)
            if not summary.final_answer:
                raise RuntimeError(
                    "opencode CLI returned no final_answer event in JSONL"
                )
            return summary.final_answer
