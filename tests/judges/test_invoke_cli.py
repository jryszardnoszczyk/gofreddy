"""Tests for judges.invoke_cli — mocks asyncio.create_subprocess_exec.

Verifies:
- successful stdout is returned decoded;
- non-zero exit raises RuntimeError with stderr preview;
- timeout raises RuntimeError and kills the process;
- the semaphore caps concurrency at CLAUDE_POOL_SIZE / CODEX_POOL_SIZE.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from judges import invoke_cli


class _FakeProc:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
        hang: float = 0.0,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self._hang = hang
        self.killed = False

    async def communicate(self, input=None) -> tuple[bytes, bytes]:
        if self._hang:
            await asyncio.sleep(self._hang)
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.killed = True


def _patch_exec(monkeypatch: pytest.MonkeyPatch, factory) -> None:
    async def _fake_exec(*args: Any, **kwargs: Any) -> _FakeProc:
        return factory()

    monkeypatch.setattr(
        asyncio, "create_subprocess_exec", _fake_exec,
    )


def test_invoke_claude_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_exec(
        monkeypatch,
        lambda: _FakeProc(stdout=b"hello from claude", returncode=0),
    )
    out = asyncio.run(invoke_cli.invoke_claude("hi"))
    assert out == "hello from claude"


def test_invoke_claude_nonzero_exit_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_exec(
        monkeypatch,
        lambda: _FakeProc(stderr=b"boom", returncode=7),
    )
    with pytest.raises(RuntimeError, match="exit 7"):
        asyncio.run(invoke_cli.invoke_claude("hi"))


def test_invoke_claude_timeout_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    procs: list[_FakeProc] = []

    def _factory() -> _FakeProc:
        p = _FakeProc(hang=2.0)
        procs.append(p)
        return p

    _patch_exec(monkeypatch, _factory)

    with pytest.raises(RuntimeError, match="timeout"):
        asyncio.run(invoke_cli.invoke_claude("hi", timeout=1))
    assert procs and procs[0].killed


def test_invoke_codex_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_exec(
        monkeypatch,
        lambda: _FakeProc(stdout=b"codex out", returncode=0),
    )
    out = asyncio.run(invoke_cli.invoke_codex("hi"))
    assert out == "codex out"


def test_invoke_codex_nonzero_exit_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_exec(
        monkeypatch,
        lambda: _FakeProc(stderr=b"nope", returncode=3),
    )
    with pytest.raises(RuntimeError, match="exit 3"):
        asyncio.run(invoke_cli.invoke_codex("hi"))


def test_claude_semaphore_caps_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLAUDE_POOL_SIZE concurrent calls; a (N+1)th call must wait."""
    pool_size = invoke_cli.CLAUDE_POOL_SIZE  # expected 3

    in_flight = 0
    peak = 0
    lock = asyncio.Lock()

    class _TrackingProc(_FakeProc):
        async def communicate(self, input=None) -> tuple[bytes, bytes]:
            nonlocal in_flight, peak
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            await asyncio.sleep(0.05)
            async with lock:
                in_flight -= 1
            return b"out", b""

    _patch_exec(monkeypatch, lambda: _TrackingProc(returncode=0))

    async def _driver() -> None:
        # Reset the semaphore so prior tests in the same process don't
        # leave it drained.
        invoke_cli._claude_sem = asyncio.Semaphore(pool_size)
        tasks = [invoke_cli.invoke_claude(f"p{i}") for i in range(pool_size * 2)]
        await asyncio.gather(*tasks)

    asyncio.run(_driver())
    assert peak <= pool_size, f"concurrency {peak} exceeded pool {pool_size}"


def _patch_opencode_helpers(monkeypatch: pytest.MonkeyPatch, *, transient_check=lambda _s: False) -> None:
    """Stub the bare-module ``opencode_jsonl`` helpers used by invoke_opencode.

    PR #34 adds ``stdout_has_transient_error`` to autoresearch/harness/. Once
    that lands and our branch rebases, this stub becomes redundant — the real
    helper kicks in. Until then, tests need a fake module so the import
    succeeds.
    """
    import sys as _sys
    import types
    from pathlib import Path as _Path

    fake = types.ModuleType("opencode_jsonl")

    class _Summary:
        def __init__(self, final_answer):
            self.final_answer = final_answer

    def _parse_session(log_path: _Path) -> _Summary:
        # Minimal final_answer extraction matching the real parser's contract.
        import json as _json
        last_text = None
        final_answer = None
        for line in log_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            if event.get("type") == "text":
                part = event.get("part") or {}
                text = part.get("text")
                if isinstance(text, str):
                    last_text = text
                    meta = (part.get("metadata") or {}).get("openai") or {}
                    if meta.get("phase") == "final_answer":
                        final_answer = text
            elif event.get("type") == "step_finish":
                part = event.get("part") or {}
                if part.get("reason") == "stop" and last_text is not None and final_answer is None:
                    final_answer = last_text
        return _Summary(final_answer)

    fake.parse_session = _parse_session
    fake.stdout_has_transient_error = transient_check
    monkeypatch.setitem(_sys.modules, "opencode_jsonl", fake)


def test_invoke_opencode_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """opencode wrapper parses JSONL stdout and returns final_answer."""
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    _patch_opencode_helpers(monkeypatch)
    final_answer = '```json\n{"score": 5}\n```'
    jsonl = (
        '{"type":"text","part":{"text":"thinking..."}}\n'
        '{"type":"text","part":{"text":"' + final_answer.replace('\n', '\\n').replace('"', '\\"') + '","metadata":{"openai":{"phase":"final_answer"}}}}\n'
        '{"type":"step_finish","part":{"reason":"stop","cost":0.001}}\n'
    )
    _patch_exec(monkeypatch, lambda: _FakeProc(stdout=jsonl.encode(), returncode=0))
    out = asyncio.run(invoke_cli.invoke_opencode("hi"))
    assert out == final_answer


def test_invoke_opencode_nonzero_exit_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    _patch_opencode_helpers(monkeypatch)
    _patch_exec(monkeypatch, lambda: _FakeProc(stderr=b"upstream 503", returncode=2))
    with pytest.raises(RuntimeError, match="exit 2"):
        asyncio.run(invoke_cli.invoke_opencode("hi"))


def test_invoke_opencode_no_final_answer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """JSONL with no final_answer event must raise — we never silently return ''."""
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    _patch_opencode_helpers(monkeypatch)
    jsonl = '{"type":"step_start","part":{}}\n'
    _patch_exec(monkeypatch, lambda: _FakeProc(stdout=jsonl.encode(), returncode=0))
    with pytest.raises(RuntimeError, match="no final_answer"):
        asyncio.run(invoke_cli.invoke_opencode("hi"))


def test_invoke_opencode_retries_on_transient(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transient OpenRouter error in JSONL → retry until clean (or attempts exhausted)."""
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    monkeypatch.setattr(invoke_cli, "_OPENCODE_MAX_ATTEMPTS", 3)

    final_answer = '{"score": 5}'
    success_jsonl = (
        '{"type":"text","part":{"text":"' + final_answer.replace('"', '\\"') +
        '","metadata":{"openai":{"phase":"final_answer"}}}}\n'
    )
    transient_jsonl = '{"type":"error","error":{"data":{"message":"rate_limit_exceeded"}}}\n'

    call_count = [0]
    transient_marker = "rate_limit_exceeded"

    def _factory() -> _FakeProc:
        call_count[0] += 1
        # First two attempts: transient. Third: clean.
        body = transient_jsonl if call_count[0] < 3 else success_jsonl
        return _FakeProc(stdout=body.encode(), returncode=0)

    _patch_exec(monkeypatch, _factory)
    _patch_opencode_helpers(
        monkeypatch,
        transient_check=lambda s: transient_marker in s,
    )

    out = asyncio.run(invoke_cli.invoke_opencode("hi"))
    assert call_count[0] == 3, "should have retried twice before success"
    assert out == final_answer


def test_invoke_opencode_pins_opencode_config(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """OPENCODE_CONFIG is pinned to repo's opencode.json when present."""
    fake_config = tmp_path / "opencode.json"
    fake_config.write_text("{}")
    monkeypatch.setattr(invoke_cli, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)
    _patch_opencode_helpers(monkeypatch)

    captured_env: dict = {}

    async def _fake_exec(*args, env=None, **kwargs):
        captured_env.update(env or {})
        return _FakeProc(stdout=b'{"type":"text","part":{"text":"ok","metadata":{"openai":{"phase":"final_answer"}}}}\n', returncode=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    asyncio.run(invoke_cli.invoke_opencode("hi"))
    assert captured_env.get("OPENCODE_CONFIG") == str(fake_config)


def test_invoke_opencode_uses_env_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """AUTORESEARCH_OPENCODE_DEFAULT_MODEL env wins over the literal fallback."""
    monkeypatch.setenv("AUTORESEARCH_OPENCODE_DEFAULT_MODEL", "openrouter/qwen/qwen3-coder")
    monkeypatch.setattr(invoke_cli, "_resolve_opencode_bin", lambda: "/usr/local/bin/opencode")
    _patch_opencode_helpers(monkeypatch)

    captured_argv: list = []

    async def _fake_exec(*args, env=None, **kwargs):
        captured_argv.extend(args)
        return _FakeProc(stdout=b'{"type":"text","part":{"text":"ok","metadata":{"openai":{"phase":"final_answer"}}}}\n', returncode=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    asyncio.run(invoke_cli.invoke_opencode("hi"))
    assert "openrouter/qwen/qwen3-coder" in captured_argv


def test_codex_semaphore_caps_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    pool_size = invoke_cli.CODEX_POOL_SIZE

    in_flight = 0
    peak = 0
    lock = asyncio.Lock()

    class _TrackingProc(_FakeProc):
        async def communicate(self, input=None) -> tuple[bytes, bytes]:
            nonlocal in_flight, peak
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            await asyncio.sleep(0.05)
            async with lock:
                in_flight -= 1
            return b"out", b""

    _patch_exec(monkeypatch, lambda: _TrackingProc(returncode=0))

    async def _driver() -> None:
        invoke_cli._codex_sem = asyncio.Semaphore(pool_size)
        tasks = [invoke_cli.invoke_codex(f"p{i}") for i in range(pool_size * 2)]
        await asyncio.gather(*tasks)

    asyncio.run(_driver())
    assert peak <= pool_size
