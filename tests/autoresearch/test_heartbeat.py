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


def test_start_heartbeat_thread_is_daemon(tmp_path: Path):
    """Daemon flag matters: a hard process exit must not strand the loop."""
    stop, thread = hb.start_heartbeat_thread(tmp_path, interval=0.05)
    try:
        assert thread.daemon is True
    finally:
        stop.set()
        thread.join(timeout=2.0)
