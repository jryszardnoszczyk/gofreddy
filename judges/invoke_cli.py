"""Async wrappers around ``claude`` and ``codex`` CLI binaries.

These run on the judge-service host only. Authentication lives in the CLI
tools' subscription login state — no API keys, no env-var fallback. Each
CLI has its own semaphore-bounded pool; the pool size is the conservative
starting default and is bumped via config when observation shows headroom
without throttling.
"""
from __future__ import annotations

import asyncio


CLAUDE_POOL_SIZE = 3
CODEX_POOL_SIZE = 3

_claude_sem = asyncio.Semaphore(CLAUDE_POOL_SIZE)
_codex_sem = asyncio.Semaphore(CODEX_POOL_SIZE)


async def invoke_claude(
    prompt: str, *, model: str = "claude-opus-4-7", timeout: int = 900,
) -> str:
    """Invoke the ``claude`` CLI; return stdout. RuntimeError on failure.

    Default timeout is 900s (15 min). Long-form session-judge critiques on
    multi-KB artifacts with high-thinking effort regularly exceed 5 min;
    300s was producing false 500s under realistic load.
    """
    async with _claude_sem:
        proc = await asyncio.create_subprocess_exec(
            "claude", "--model", model, "--print", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
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
    """
    async with _codex_sem:
        proc = await asyncio.create_subprocess_exec(
            "codex", "exec", "--model", model, prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
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
