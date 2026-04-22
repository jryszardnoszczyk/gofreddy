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

    async def communicate(self) -> tuple[bytes, bytes]:
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
        async def communicate(self) -> tuple[bytes, bytes]:
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


def test_codex_semaphore_caps_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    pool_size = invoke_cli.CODEX_POOL_SIZE

    in_flight = 0
    peak = 0
    lock = asyncio.Lock()

    class _TrackingProc(_FakeProc):
        async def communicate(self) -> tuple[bytes, bytes]:
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
