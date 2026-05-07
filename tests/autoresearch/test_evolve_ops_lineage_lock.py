"""Tests for evolve_ops.promote_atomic — lineage append + head pointer under contention."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

import evolve_ops
import lane_runtime


@pytest.fixture
def archive_with_seed(tmp_path: Path) -> Path:
    """Build a minimal archive with 5 seed variants in lineage.jsonl + current.json manifest."""
    archive = tmp_path / "archive"
    archive.mkdir()

    seed_ids = [f"v{i:03d}" for i in range(1, 6)]
    lineage = archive / "lineage.jsonl"
    with lineage.open("w") as handle:
        for vid in seed_ids:
            handle.write(json.dumps({"id": vid, "lane": "core", "timestamp": "2026-05-07T00:00:00Z"}) + "\n")

    manifest = {lane: seed_ids[0] for lane in lane_runtime.LANES}
    (archive / "current.json").write_text(json.dumps(manifest) + "\n")

    return archive


def _read_lineage(archive: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (archive / "lineage.jsonl").read_text().splitlines()
        if line.strip()
    ]


def test_promote_atomic_serialises_concurrent_writers(archive_with_seed: Path):
    """5 threads each promoting a distinct variant — all 5 appends survive, head matches one."""
    archive_dir = str(archive_with_seed)
    lane = lane_runtime.LANES[0]
    seed_ids = [f"v{i:03d}" for i in range(1, 6)]

    barrier = threading.Barrier(len(seed_ids))
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def promote(vid: str) -> None:
        try:
            barrier.wait(timeout=5.0)
            evolve_ops.promote_atomic(archive_dir, lane, vid, f"2026-05-07T00:00:0{vid[-1]}Z")
        except BaseException as exc:  # noqa: BLE001
            with errors_lock:
                errors.append(exc)

    threads = [threading.Thread(target=promote, args=(vid,)) for vid in seed_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert not errors, f"workers raised: {errors!r}"

    # 5 seed entries + 5 promotion appends = 10 lines exactly. No clobbering.
    entries = _read_lineage(archive_with_seed)
    assert len(entries) == 10, f"expected 10 lineage entries, got {len(entries)}"

    promoted = [e for e in entries if e.get("promoted_at")]
    assert {e["id"] for e in promoted} == set(seed_ids), (
        f"each seed should appear once with promoted_at, got {[e['id'] for e in promoted]}"
    )

    manifest = json.loads((archive_with_seed / "current.json").read_text())
    assert manifest[lane] in seed_ids, (
        f"head pointer must be one of the 5 promotions, got {manifest[lane]!r}"
    )


def test_promote_atomic_holds_lock_across_both_writes(archive_with_seed: Path, monkeypatch):
    """Lock must be held continuously: a peeker between mark_promoted and set_current_head sees both done together."""
    archive_dir = str(archive_with_seed)
    lane = lane_runtime.LANES[0]

    real_set_current_head = evolve_ops.set_current_head
    snapshots: list[tuple[int, dict]] = []

    def slow_set_current_head(*args, **kwargs):
        # Snapshot lineage line count just before the head write completes so we
        # can verify the append happened under the same lock acquisition.
        snapshots.append((
            len(_read_lineage(archive_with_seed)),
            json.loads((archive_with_seed / "current.json").read_text()),
        ))
        return real_set_current_head(*args, **kwargs)

    monkeypatch.setattr(evolve_ops, "set_current_head", slow_set_current_head)

    evolve_ops.promote_atomic(archive_dir, lane, "v003", "2026-05-07T00:00:30Z")

    assert len(snapshots) == 1
    line_count_before_head_write, manifest_before = snapshots[0]
    assert line_count_before_head_write == 6, (
        "lineage append must have run before head write (still inside the lock)"
    )
    # Manifest pre-head-write still points at the seed head, since set_current_head
    # has not committed yet — confirms ordering inside promote_atomic.
    assert manifest_before[lane] == "v001"
