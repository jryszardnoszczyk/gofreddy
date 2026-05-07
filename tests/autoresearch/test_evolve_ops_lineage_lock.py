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


def test_load_latest_lineage_skips_torn_lines_with_warning(archive_with_seed: Path, capsys):
    """A half-written line from a crashed writer must be skipped, not crash
    every subsequent reader; but a stderr warning surfaces so the operator
    can investigate the corruption rather than silently losing the variant.
    """
    lineage = archive_with_seed / "lineage.jsonl"
    # Append a torn line — simulates a writer killed mid-`write(json+\\n)`.
    with lineage.open("a") as fh:
        fh.write('{"id":"v999","prom')

    latest = evolve_ops._load_latest_lineage(archive_with_seed)
    # Original 5 seeds still load; the torn v999 is skipped.
    assert set(latest) == {f"v00{i}" for i in range(1, 6)}
    err = capsys.readouterr().err
    assert "corrupted lineage line" in err
    assert "lineage.jsonl" in err


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
    """Lock is held continuously: thread B blocks while thread A is mid-promote_atomic.

    Stronger than ordering-only — proves no other writer can sneak between
    A.mark_promoted and A.set_current_head. Without _LINEAGE_LOCK this would
    interleave as A.append, B.append, A.head, B.head and the test detects it.
    """
    archive_dir = str(archive_with_seed)
    lane = lane_runtime.LANES[0]

    real_mark = evolve_ops.mark_promoted
    real_set_head = evolve_ops.set_current_head
    inside_a_barrier = threading.Event()
    a_can_proceed = threading.Event()
    write_log: list[str] = []
    write_log_lock = threading.Lock()

    def instrumented_mark(archive_dir, variant_id, timestamp):
        with write_log_lock:
            write_log.append(f"mark:{variant_id}")
        try:
            real_mark(archive_dir, variant_id, timestamp)
        finally:
            # Always release the barrier so a future change to mark_promoted
            # that raises (e.g. "cannot promote already-promoted") doesn't
            # leave thread B blocked indefinitely on inside_a_barrier.wait().
            if variant_id == "v003":
                inside_a_barrier.set()
        if variant_id == "v003":
            assert a_can_proceed.wait(timeout=2.0), "barrier never released"

    def instrumented_set_head(archive_dir, lane, variant_id):
        with write_log_lock:
            write_log.append(f"head:{variant_id}")
        real_set_head(archive_dir, lane, variant_id)

    monkeypatch.setattr(evolve_ops, "mark_promoted", instrumented_mark)
    monkeypatch.setattr(evolve_ops, "set_current_head", instrumented_set_head)

    def thread_a():
        evolve_ops.promote_atomic(archive_dir, lane, "v003", "2026-05-07T00:00:30Z")

    def thread_b():
        assert inside_a_barrier.wait(timeout=2.0), "A never reached barrier"
        # A is mid-promote, holding _LINEAGE_LOCK. B must block on it.
        evolve_ops.promote_atomic(archive_dir, lane, "v004", "2026-05-07T00:00:31Z")

    a = threading.Thread(target=thread_a)
    b = threading.Thread(target=thread_b)
    a.start()
    b.start()

    try:
        # While A is parked, B must NOT have made any progress past lock acquisition.
        assert inside_a_barrier.wait(timeout=2.0), "A never reached barrier"
        b.join(timeout=0.3)
        assert b.is_alive(), "B should be blocked on _LINEAGE_LOCK while A holds it"
        assert write_log == ["mark:v003"], (
            f"only A's mark_promoted should have run so far, got {write_log}"
        )
    finally:
        # Always release A so threads exit cleanly even if an assertion above
        # fails — otherwise B would dangle into the next test's setup.
        a_can_proceed.set()
        a.join(timeout=2.0)
        b.join(timeout=2.0)
    assert not a.is_alive() and not b.is_alive()

    # Final write order must be A.mark, A.head, B.mark, B.head — never interleaved.
    assert write_log == ["mark:v003", "head:v003", "mark:v004", "head:v004"], (
        f"writes interleaved (lock leaked): {write_log}"
    )
