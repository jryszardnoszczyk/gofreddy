"""Checkpointing atomicity + basic read/write semantics."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import pytest

from src.audit.checkpointing import (
    atomic_update,
    read_json,
    write_atomic,
    write_json,
)


class TestWriteAtomic:
    def test_writes_content_to_path(self, tmp_path: Path) -> None:
        target = tmp_path / "state.json"
        write_atomic(target, '{"foo": 1}')
        assert target.read_text() == '{"foo": 1}'

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        target = tmp_path / "clients" / "acme" / "audit" / "state.json"
        write_atomic(target, "x")
        assert target.exists()
        assert target.read_text() == "x"

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        target.write_text("old")
        write_atomic(target, "new")
        assert target.read_text() == "new"

    def test_no_tmp_file_leaks_after_success(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        write_atomic(target, "x")
        # Only the target file should remain — no .tmp stragglers.
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == ["s.json"]

    def test_no_tmp_file_leaks_after_write_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        target = tmp_path / "s.json"

        def boom(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise OSError("disk full")

        # Make os.replace fail after the temp is written — simulates the
        # worst-case: temp was written, rename fails, must not leak.
        monkeypatch.setattr("src.audit.checkpointing.os.replace", lambda *a, **kw: (_ for _ in ()).throw(OSError("rename failed")))

        with pytest.raises(OSError):
            write_atomic(target, "x")
        # Target should not exist, and no .tmp file should remain.
        assert not target.exists()
        assert list(tmp_path.iterdir()) == []


class TestReadJson:
    def test_missing_file_returns_default(self, tmp_path: Path) -> None:
        assert read_json(tmp_path / "absent.json", default={}) == {}
        assert read_json(tmp_path / "absent.json", default=None) is None

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        target.write_text('{"a": [1, 2, 3]}')
        assert read_json(target) == {"a": [1, 2, 3]}

    def test_raises_on_corrupt_json(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        target.write_text("{not json")
        with pytest.raises(json.JSONDecodeError):
            read_json(target)


class TestWriteJson:
    def test_roundtrip(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        data = {"stage": "stage_2", "cost_usd": 12.5, "sessions": {"findability": "sess-1"}}
        write_json(target, data)
        assert read_json(target) == data

    def test_sorts_keys(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        write_json(target, {"b": 2, "a": 1})
        content = target.read_text()
        # Sorted keys → "a" appears before "b" in the serialized form.
        assert content.index('"a"') < content.index('"b"')

    def test_coerces_non_json_types_via_default_str(self, tmp_path: Path) -> None:
        # Pydantic HttpUrl-like objects serialize via str().
        from datetime import datetime
        target = tmp_path / "s.json"
        write_json(target, {"ts": datetime(2026, 4, 23, 12, 0, 0)})
        loaded = read_json(target)
        assert loaded == {"ts": "2026-04-23 12:00:00"}


class TestAtomicUpdate:
    def test_creates_when_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        result = atomic_update(target, lambda cur: {"count": 1}, default=None)
        assert result == {"count": 1}
        assert read_json(target) == {"count": 1}

    def test_increments_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "s.json"
        write_json(target, {"count": 5})
        result = atomic_update(target, lambda cur: {**cur, "count": cur["count"] + 1}, default={})
        assert result == {"count": 6}
        assert read_json(target) == {"count": 6}

    def test_serialized_updates_no_write_loss(self, tmp_path: Path) -> None:
        """Two-thread update via a lock — the helper itself is single-process;
        this just verifies that `atomic_update` doesn't clobber when callers
        serialize access."""
        target = tmp_path / "s.json"
        write_json(target, {"count": 0})
        lock = threading.Lock()

        def worker() -> None:
            for _ in range(50):
                with lock:
                    atomic_update(target, lambda cur: {"count": cur["count"] + 1})

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert read_json(target) == {"count": 200}
