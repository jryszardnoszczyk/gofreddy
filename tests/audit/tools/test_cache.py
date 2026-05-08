"""Tests for src/audit/tools/cache — hash-dedup wrapper, sync + async paths.

Covers F6 self-review: cost-recording side effects fire on miss only, never
on hit. We assert that explicitly via a counter inside the test fn.
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.audit.tools import cache as cache_mod


@pytest.fixture(autouse=True)
def _reset_stats() -> None:
    cache_mod.reset_stats()
    yield
    cache_mod.reset_stats()


def test_hash_args_is_stable_across_dict_ordering() -> None:
    a = cache_mod._hash_args({"url": "https://example.com", "depth": 2})
    b = cache_mod._hash_args({"depth": 2, "url": "https://example.com"})
    assert a == b
    assert len(a) == cache_mod.HASH_PREFIX_LEN


def test_hash_args_handles_non_json_values() -> None:
    """Path / datetime should not raise — sane fallback via default=str."""
    h = cache_mod._hash_args({"path": Path("/tmp/foo"), "when": datetime(2026, 5, 6)})
    assert isinstance(h, str)
    assert len(h) == cache_mod.HASH_PREFIX_LEN


def test_cache_or_call_miss_then_hit_sync(tmp_path: Path) -> None:
    """First call invokes fn; second call with same args reads cache."""
    counter = {"n": 0}

    def _fn(url: str) -> dict:
        counter["n"] += 1
        return {"url": url, "status": 200}

    args = {"url": "https://example.com"}
    r1 = cache_mod.cache_or_call("test.fetch", args, _fn, cache_dir=tmp_path)
    assert r1 == {"url": "https://example.com", "status": 200}
    assert counter["n"] == 1

    # Cache file landed.
    files = list(tmp_path.glob("test.fetch_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text())
    assert payload["tool_name"] == "test.fetch"
    assert payload["result"]["status"] == 200

    # Second call — fn must NOT fire.
    r2 = cache_mod.cache_or_call("test.fetch", args, _fn, cache_dir=tmp_path)
    assert r2 == r1
    assert counter["n"] == 1, "F6: cache hit must not invoke fn"

    stats = cache_mod.get_stats()
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.writes == 1


def test_cache_or_call_async(tmp_path: Path) -> None:
    counter = {"n": 0}

    async def _fn(q: str) -> dict:
        counter["n"] += 1
        await asyncio.sleep(0)
        return {"q": q, "n": counter["n"]}

    async def _runner() -> tuple:
        a = await cache_mod.cache_or_call("test.async", {"q": "hi"}, _fn, cache_dir=tmp_path)
        b = await cache_mod.cache_or_call("test.async", {"q": "hi"}, _fn, cache_dir=tmp_path)
        return a, b

    a, b = asyncio.run(_runner())
    assert a == b
    assert counter["n"] == 1, "async hit must not re-invoke fn"


def test_cache_or_call_distinct_args_distinct_files(tmp_path: Path) -> None:
    def _fn(x: int) -> int:
        return x * 2

    cache_mod.cache_or_call("dbl", {"x": 1}, _fn, cache_dir=tmp_path)
    cache_mod.cache_or_call("dbl", {"x": 2}, _fn, cache_dir=tmp_path)
    files = sorted(tmp_path.glob("dbl_*.json"))
    assert len(files) == 2


def test_cache_or_call_ttl_expired(tmp_path: Path) -> None:
    """Force-expire by writing a payload with a stale ``cached_at``."""
    args = {"url": "https://example.com"}
    path = cache_mod.cache_path(tmp_path, "stale", args)
    path.parent.mkdir(parents=True, exist_ok=True)
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    path.write_text(json.dumps({
        "tool_name": "stale", "args": args, "result": {"old": True},
        "cached_at": stale_ts,
    }))

    counter = {"n": 0}

    def _fn(url: str) -> dict:
        counter["n"] += 1
        return {"old": False}

    result = cache_mod.cache_or_call("stale", args, _fn, ttl_hours=24, cache_dir=tmp_path)
    assert result == {"old": False}
    assert counter["n"] == 1
    assert cache_mod.get_stats().expired == 1


def test_cache_or_call_ttl_zero_never_expires(tmp_path: Path) -> None:
    """ttl_hours=0 is the test convenience escape hatch."""
    counter = {"n": 0}

    def _fn() -> int:
        counter["n"] += 1
        return 42

    cache_mod.cache_or_call("test.zero", {}, _fn, ttl_hours=0, cache_dir=tmp_path)
    cache_mod.cache_or_call("test.zero", {}, _fn, ttl_hours=0, cache_dir=tmp_path)
    assert counter["n"] == 1


def test_cache_or_call_corrupt_file_treated_as_miss(tmp_path: Path) -> None:
    args = {"url": "https://example.com"}
    path = cache_mod.cache_path(tmp_path, "corrupt", args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not valid json {{{")

    counter = {"n": 0}

    def _fn(url: str) -> dict:
        counter["n"] += 1
        return {"ok": True}

    result = cache_mod.cache_or_call("corrupt", args, _fn, cache_dir=tmp_path)
    assert result == {"ok": True}
    assert counter["n"] == 1
    assert cache_mod.get_stats().corrupt == 1


def test_cache_or_call_propagates_fn_exceptions(tmp_path: Path) -> None:
    """Failure path: do not write a cache entry on fn raise."""

    def _fn() -> None:
        raise RuntimeError("upstream 500")

    with pytest.raises(RuntimeError):
        cache_mod.cache_or_call("err", {}, _fn, cache_dir=tmp_path)
    assert list(tmp_path.glob("err_*.json")) == []


def test_cache_or_call_requires_cache_dir() -> None:
    with pytest.raises(ValueError, match="cache_dir"):
        cache_mod.cache_or_call("x", {}, lambda: None, cache_dir=None)


def test_read_cache_returns_none_on_missing_file(tmp_path: Path) -> None:
    assert cache_mod.read_cache(tmp_path, "missing", {"k": "v"}) is None


def test_read_cache_returns_payload_on_fresh_hit(tmp_path: Path) -> None:
    cache_mod.write_cache(tmp_path, "tool", {"k": "v"}, {"r": 1})
    assert cache_mod.read_cache(tmp_path, "tool", {"k": "v"}) == {"r": 1}


def test_write_cache_is_atomic_no_tempfile_leak(tmp_path: Path) -> None:
    cache_mod.write_cache(tmp_path, "tool", {"k": "v"}, {"r": 1})
    # No leftover .tmp files.
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_write_cache_serializes_pydantic_model(tmp_path: Path) -> None:
    """Provider methods return Pydantic models — must serialize cleanly."""
    from pydantic import BaseModel

    class TestResult(BaseModel):
        url: str
        score: int

    result = TestResult(url="https://example.com", score=85)
    path = cache_mod.write_cache(tmp_path, "pydantic_tool", {"u": 1}, result)
    payload = json.loads(path.read_text())
    assert payload["result"] == {"url": "https://example.com", "score": 85}
