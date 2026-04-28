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


# Repo root + autoresearch/harness/ on sys.path so opencode helpers
# resolve as bare modules. Mirrors the pattern PR #34 establishes in
# autoresearch/{compute_metrics,evolve,program_prescription_critic}.py
# — going through the ``autoresearch.harness`` package can resolve to a
# different ``harness/`` at the repo root depending on pytest's rootdir
# discovery order. Bare-module import via sys.path sidesteps it.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_HARNESS_DIR = _REPO_ROOT / "autoresearch" / "harness"
if _HARNESS_DIR.is_dir() and str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))


CLAUDE_POOL_SIZE = 3
CODEX_POOL_SIZE = 3
OPENCODE_POOL_SIZE = 3

_claude_sem = asyncio.Semaphore(CLAUDE_POOL_SIZE)
_codex_sem = asyncio.Semaphore(CODEX_POOL_SIZE)
_opencode_sem = asyncio.Semaphore(OPENCODE_POOL_SIZE)


# Mirrors autoresearch/harness/agent.py and PR #34's other dispatch sites.
# OpenRouter upstream provider hiccups manifest as error events in opencode's
# JSONL while the subprocess exits 0. Retry up to N total attempts.
_OPENCODE_MAX_ATTEMPTS = max(1, int(os.environ.get("OPENCODE_MAX_RETRIES", "3")))


def _opencode_default_model() -> str:
    """Resolve opencode's default model. Mirrors PR #34's pattern.

    ``AUTORESEARCH_OPENCODE_DEFAULT_MODEL`` env wins; otherwise
    ``openrouter/deepseek/deepseek-v4-pro`` (PR #33-pinned slug).
    """
    return os.environ.get(
        "AUTORESEARCH_OPENCODE_DEFAULT_MODEL",
        "openrouter/deepseek/deepseek-v4-pro",
    )


def _opencode_subprocess_env() -> dict[str, str]:
    """Subprocess env with OPENCODE_CONFIG pinned to the repo's opencode.json.

    Without this pin, OpenRouter routes deepseek-v4-pro across 6 upstream
    providers and the 3 that don't support tool-calling (Novita / GMICloud
    / SiliconFlow) silently 504 mid-judge. Repo's opencode.json constrains
    to deepseek/together/io-net. Mirrors harness/agent.py and PR #34's
    other dispatch sites.
    """
    env = os.environ.copy()
    config_path = _REPO_ROOT / "opencode.json"
    if config_path.is_file() and not env.get("OPENCODE_CONFIG"):
        env["OPENCODE_CONFIG"] = str(config_path)
    return env


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


async def _invoke_opencode_once(
    bin_path: str,
    prompt: str,
    *,
    model: str,
    timeout: int,
    env: dict[str, str],
) -> tuple[int, bytes, bytes]:
    """Single opencode subprocess attempt — no retry. Caller wraps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = Path(tmpdir) / "prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        proc = await asyncio.create_subprocess_exec(
            bin_path, "run", "--dangerously-skip-permissions",
            "-m", model, "--format", "json",
            "-f", str(prompt_path),
            "Follow the instructions in the attached prompt file. "
            "Return ONLY the JSON verdict block requested by those instructions.",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"opencode CLI timeout after {timeout}s")
        return proc.returncode, stdout, stderr


async def invoke_opencode(
    prompt: str,
    *,
    model: str | None = None,
    timeout: int = 900,
) -> str:
    """Invoke the ``opencode`` CLI; return final-answer text. RuntimeError on failure.

    Default timeout 900s (15 min). The prompt is written to a temp file and
    attached via ``-f`` rather than passed as argv, since judge prompts
    routinely exceed ARG_MAX after artifact packing. The tiny positional
    message tells the model to follow the attached instructions.

    opencode emits structured JSONL on stdout when ``--format json`` is set.
    We parse it with the canonical autoresearch parser to extract the
    model's final-answer text — that's the JSON verdict block the
    variant_scorer expects.

    On transient OpenRouter upstream errors (rate_limit_exceeded,
    provider_overloaded, timeout — opencode exits 0 even on these) we
    retry up to ``OPENCODE_MAX_RETRIES`` (default 3) total attempts.
    Detection via ``stdout_has_transient_error`` from
    ``autoresearch/harness/opencode_jsonl.py``. Mirrors PR #34's policy
    in autoresearch/{compute_metrics,evolve,program_prescription_critic}.

    The subprocess env pins ``OPENCODE_CONFIG`` to the repo's
    ``opencode.json`` so OpenRouter routes to tools-supporting upstreams
    (deepseek/together/io-net) and not the silently-504-ing ones.
    """
    bin_path = _resolve_opencode_bin()
    resolved_model = model or _opencode_default_model()
    env = _opencode_subprocess_env()

    # Bare-module import: autoresearch/harness/ is added to sys.path at
    # module init. Late import so judge-only deployments that don't have
    # autoresearch checked out can still import this module without
    # opencode wired up — only fails if invoke_opencode is actually called.
    from opencode_jsonl import parse_session, stdout_has_transient_error  # noqa: E402

    async with _opencode_sem:
        last_returncode = 0
        last_stdout = b""
        last_stderr = b""
        for attempt in range(1, _OPENCODE_MAX_ATTEMPTS + 1):
            last_returncode, last_stdout, last_stderr = await _invoke_opencode_once(
                bin_path, prompt, model=resolved_model, timeout=timeout, env=env,
            )
            if last_returncode != 0:
                # Hard exit — don't retry; mirrors PR #34's policy
                # (retries only target transient JSONL errors on exit 0).
                preview = last_stderr.decode(errors="replace")[:500]
                raise RuntimeError(
                    f"opencode CLI exit {last_returncode}: {preview}"
                )
            stdout_text = last_stdout.decode(errors="replace")
            if not stdout_has_transient_error(stdout_text):
                break
            if attempt < _OPENCODE_MAX_ATTEMPTS:
                print(
                    f"[invoke_opencode] attempt {attempt}/{_OPENCODE_MAX_ATTEMPTS} "
                    f"hit transient OpenRouter error; retrying",
                    file=sys.stderr,
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "session.jsonl"
            log_path.write_bytes(last_stdout)
            summary = parse_session(log_path)
        if not summary.final_answer:
            raise RuntimeError(
                "opencode CLI returned no final_answer event in JSONL"
            )
        return summary.final_answer
