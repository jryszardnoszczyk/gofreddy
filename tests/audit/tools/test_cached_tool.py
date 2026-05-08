"""Tests for src/audit/tools/cached_tool — decorator + thread-local scope."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.audit.tools import cache as cache_mod
from src.audit.tools.cached_tool import (
    cached_tool,
    get_audit_cache_dir,
    set_audit_cache_dir,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    cache_mod.reset_stats()
    set_audit_cache_dir(None)
    yield
    set_audit_cache_dir(None)


def test_cached_tool_uses_thread_local_cache_dir(tmp_path: Path) -> None:
    counter = {"n": 0}

    class Provider:
        @cached_tool("test_provider.fetch")
        def fetch(self, url: str) -> dict:
            counter["n"] += 1
            return {"url": url}

    p = Provider()
    set_audit_cache_dir(tmp_path)

    p.fetch(url="https://example.com")
    p.fetch(url="https://example.com")
    assert counter["n"] == 1, "second call should hit cache"


def test_cached_tool_passes_through_when_no_cache_dir() -> None:
    """Non-audit callers (no thread-local set) bypass caching entirely."""
    counter = {"n": 0}

    class Provider:
        @cached_tool("test_provider.fetch")
        def fetch(self, x: int) -> int:
            counter["n"] += 1
            return x * 2

    p = Provider()
    assert p.fetch(x=5) == 10
    assert p.fetch(x=5) == 10
    assert counter["n"] == 2, "no cache_dir → no caching → fn called twice"


def test_cached_tool_async_method(tmp_path: Path) -> None:
    counter = {"n": 0}

    class AsyncProvider:
        @cached_tool("async_provider.fetch")
        async def fetch(self, q: str) -> dict:
            counter["n"] += 1
            await asyncio.sleep(0)
            return {"q": q}

    p = AsyncProvider()
    set_audit_cache_dir(tmp_path)

    async def _runner() -> None:
        await p.fetch(q="hello")
        await p.fetch(q="hello")

    asyncio.run(_runner())
    assert counter["n"] == 1


def test_cached_tool_distinct_args_no_collision(tmp_path: Path) -> None:
    class Provider:
        @cached_tool("provider.fn")
        def fn(self, x: int) -> int:
            return x

    p = Provider()
    set_audit_cache_dir(tmp_path)

    p.fn(x=1)
    p.fn(x=2)
    files = sorted(tmp_path.glob("provider.fn_*.json"))
    assert len(files) == 2


def test_cached_tool_skip_self_means_cross_instance_share(tmp_path: Path) -> None:
    """Two provider instances should share cache entries (skip_self=True)."""
    counter = {"n": 0}

    class Provider:
        def __init__(self, name: str) -> None:
            self.name = name

        @cached_tool("p.fetch")
        def fetch(self, q: str) -> str:
            counter["n"] += 1
            return f"{self.name}:{q}"

    a = Provider("a")
    b = Provider("b")
    set_audit_cache_dir(tmp_path)

    r_a = a.fetch(q="x")
    r_b = b.fetch(q="x")
    assert counter["n"] == 1, "second instance reused first's cache"
    assert r_a == r_b  # both return "a:x" because b's call hit a's cached payload


def test_cached_tool_explicit_cache_dir_kwarg_overrides_threadlocal(tmp_path: Path) -> None:
    """Per-call ``cache_dir=`` kwarg wins over the thread-local."""
    other_dir = tmp_path / "other"
    other_dir.mkdir()

    counter = {"n": 0}

    class Provider:
        @cached_tool("p.x")
        def fetch(self, *, q: str) -> dict:
            counter["n"] += 1
            return {"q": q}

    set_audit_cache_dir(tmp_path)
    p = Provider()
    p.fetch(q="hi", cache_dir=other_dir)
    files = list(other_dir.glob("p.x_*.json"))
    assert len(files) == 1
    # And the thread-local dir got nothing.
    assert list(tmp_path.glob("p.x_*.json")) == []


def test_set_audit_cache_dir_clears_with_none(tmp_path: Path) -> None:
    set_audit_cache_dir(tmp_path)
    assert get_audit_cache_dir() == tmp_path
    set_audit_cache_dir(None)
    assert get_audit_cache_dir() is None
