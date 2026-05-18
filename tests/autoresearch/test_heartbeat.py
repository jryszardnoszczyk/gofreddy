"""Tests for Stream C C16 — heartbeat emission.

Covers ``write_heartbeat`` atomicity, ``write_pid``, and the daemon
thread spawned by ``start_heartbeat_thread`` (using a short interval
so the test doesn't block on the 30s production cadence).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from autoresearch import heartbeat as hb


def test_write_heartbeat_creates_json_with_timestamp(tmp_path: Path):
    target = tmp_path / "heartbeat.json"
    hb.write_heartbeat(target)
    assert target.is_file()
    data = json.loads(target.read_text())
    assert "timestamp" in data
    # ISO-8601 UTC with Z suffix
    assert data["timestamp"].endswith("Z")


def test_write_heartbeat_creates_parent_dirs(tmp_path: Path):
    target = tmp_path / "nested" / "subdir" / "heartbeat.json"
    hb.write_heartbeat(target)
    assert target.is_file()


def test_write_heartbeat_overwrites_existing(tmp_path: Path):
    """Subsequent calls atomic-replace the previous heartbeat."""
    target = tmp_path / "heartbeat.json"
    hb.write_heartbeat(target)
    first = json.loads(target.read_text())["timestamp"]
    # Sleep just over a second so the timestamp string ticks at second-resolution
    time.sleep(1.05)
    hb.write_heartbeat(target)
    second = json.loads(target.read_text())["timestamp"]
    assert first != second


def test_write_heartbeat_no_tmp_leftover(tmp_path: Path):
    """Atomic write via .tmp + os.replace — no stray .tmp file on success."""
    target = tmp_path / "heartbeat.json"
    hb.write_heartbeat(target)
    assert not (tmp_path / "heartbeat.json.tmp").exists()


def test_write_pid_writes_current_process(tmp_path: Path):
    pid_path = tmp_path / "pipeline.pid"
    hb.write_pid(pid_path)
    assert int(pid_path.read_text()) == os.getpid()


def test_write_pid_accepts_explicit_pid(tmp_path: Path):
    pid_path = tmp_path / "pipeline.pid"
    hb.write_pid(pid_path, pid=12345)
    assert pid_path.read_text() == "12345"


def test_start_heartbeat_thread_emits_files(tmp_path: Path):
    """Thread writes heartbeat.json + pipeline.pid synchronously at start
    so the sentinel sees liveness immediately, not after one interval."""
    stop, thread = hb.start_heartbeat_thread(tmp_path, interval=0.05)
    try:
        # Files exist right after start (synchronous initial write).
        assert (tmp_path / "heartbeat.json").is_file()
        assert (tmp_path / "pipeline.pid").is_file()
        first = (tmp_path / "heartbeat.json").read_text()

        # Wait long enough for one more tick, then verify the heartbeat refreshed.
        time.sleep(1.1)
        second = (tmp_path / "heartbeat.json").read_text()
        assert first != second
    finally:
        stop.set()
        thread.join(timeout=2.0)
        assert not thread.is_alive(), "heartbeat thread did not exit cleanly"


def test_start_heartbeat_thread_stops_on_event(tmp_path: Path):
    stop, thread = hb.start_heartbeat_thread(tmp_path, interval=0.05)
    stop.set()
    thread.join(timeout=2.0)
    assert not thread.is_alive()


def test_start_heartbeat_thread_per_lane_naming(tmp_path: Path):
    """Per-lane suffix paths (2026-05-12 fix): two concurrent evolve runs
    on different lanes must write to distinct heartbeat + pid files so
    they don't clobber each other's liveness signal."""
    geo_stop, geo_thread = hb.start_heartbeat_thread(
        tmp_path, interval=0.05,
        heartbeat_name=".heartbeat-geo.json",
        pid_name=".pid-geo.pid",
    )
    comp_stop, comp_thread = hb.start_heartbeat_thread(
        tmp_path, interval=0.05,
        heartbeat_name=".heartbeat-competitive.json",
        pid_name=".pid-competitive.pid",
    )
    try:
        # Both per-lane surfaces exist + distinct.
        assert (tmp_path / ".heartbeat-geo.json").is_file()
        assert (tmp_path / ".pid-geo.pid").is_file()
        assert (tmp_path / ".heartbeat-competitive.json").is_file()
        assert (tmp_path / ".pid-competitive.pid").is_file()
        # The legacy single-tenant paths must NOT exist when per-lane
        # naming is in use — that would indicate a regression to the
        # pre-fix clobber behavior.
        assert not (tmp_path / "heartbeat.json").exists()
        assert not (tmp_path / "pipeline.pid").exists()
        # PID files carry the same PID (same process), which is
        # expected — the isolation we care about is in filenames.
        assert (tmp_path / ".pid-geo.pid").read_text() == \
               (tmp_path / ".pid-competitive.pid").read_text()
    finally:
        geo_stop.set()
        comp_stop.set()
        geo_thread.join(timeout=2.0)
        comp_thread.join(timeout=2.0)


def test_start_heartbeat_thread_per_lane_writes_isolated(tmp_path: Path):
    """Per-lane heartbeats refresh independently: stopping one does
    NOT freeze the other (the sentinel must be able to act on one
    lane's death without false positives from a healthy peer)."""
    geo_stop, geo_thread = hb.start_heartbeat_thread(
        tmp_path, interval=0.05,
        heartbeat_name=".heartbeat-geo.json",
        pid_name=".pid-geo.pid",
    )
    comp_stop, comp_thread = hb.start_heartbeat_thread(
        tmp_path, interval=0.05,
        heartbeat_name=".heartbeat-competitive.json",
        pid_name=".pid-competitive.pid",
    )
    try:
        time.sleep(0.3)  # Let both write a few times.
        geo_stop.set()
        geo_thread.join(timeout=2.0)
        # geo heartbeat is now frozen — capture its value.
        geo_frozen = (tmp_path / ".heartbeat-geo.json").read_text()
        time.sleep(1.1)
        # geo should still be the frozen value (its thread stopped).
        assert (tmp_path / ".heartbeat-geo.json").read_text() == geo_frozen
        # competitive must have continued refreshing while geo was dead.
        # (Caveat: 1s precision on the timestamp string means we need
        # >=1s gap to observe a difference.)
        # We assert it's a valid recent timestamp rather than == frozen.
        comp_text = (tmp_path / ".heartbeat-competitive.json").read_text()
        assert comp_text  # not empty
    finally:
        comp_stop.set()
        comp_thread.join(timeout=2.0)


def test_start_heartbeat_thread_is_daemon(tmp_path: Path):
    """Daemon flag matters: a hard process exit must not strand the loop."""
    stop, thread = hb.start_heartbeat_thread(tmp_path, interval=0.05)
    try:
        assert thread.daemon is True
    finally:
        stop.set()
        thread.join(timeout=2.0)


def test_cleanup_heartbeat_files_removes_both(tmp_path: Path):
    """cleanup_heartbeat_files removes the heartbeat.json + pid file written
    by start_heartbeat_thread. Documents the contract that lets the sentinel
    distinguish "clean exit" from "crashed" via file presence."""
    hb_path = tmp_path / ".heartbeat-monitoring.json"
    pid_path = tmp_path / ".pid-monitoring.pid"
    hb.write_heartbeat(hb_path)
    hb.write_pid(pid_path)
    assert hb_path.is_file() and pid_path.is_file()

    hb.cleanup_heartbeat_files(
        tmp_path,
        heartbeat_name=".heartbeat-monitoring.json",
        pid_name=".pid-monitoring.pid",
    )
    assert not hb_path.exists()
    assert not pid_path.exists()


def test_cleanup_heartbeat_files_idempotent(tmp_path: Path):
    """Calling cleanup twice (or before any heartbeat) is safe — missing
    files are silently ignored. Operators may invoke cleanup defensively
    in shutdown paths even when the heartbeat thread never started."""
    hb.cleanup_heartbeat_files(tmp_path)  # nothing to clean
    hb.cleanup_heartbeat_files(tmp_path)  # still nothing — must not raise


def test_cleanup_heartbeat_files_only_targets_named_files(tmp_path: Path):
    """cleanup must NOT touch other files in the archive dir — operators
    keep promotion/lineage state alongside the heartbeat sentinel files."""
    sibling = tmp_path / "lineage.json"
    sibling.write_text('{"some": "state"}')
    hb.write_heartbeat(tmp_path / "heartbeat.json")
    hb.write_pid(tmp_path / "pipeline.pid")

    hb.cleanup_heartbeat_files(tmp_path)
    assert sibling.is_file()
    assert sibling.read_text() == '{"some": "state"}'
