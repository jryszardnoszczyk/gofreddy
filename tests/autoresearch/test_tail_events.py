"""Unit tests for tail_events_sse — the P4 SSE tail-follower.

These tests exercise the async tailer in isolation (no FastAPI, no Supabase).
Route-level auth + membership tests live in tests/test_api/test_portal_stream.py.

Test poll/heartbeat values are tuned small (50ms / 100ms) so the suite runs
in <2s. Production defaults are 250ms / 15s — see autoresearch/events.py.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from autoresearch.events import log_event, tail_events_sse

# --- helpers ---------------------------------------------------------------


def _parse_sse_data(msg: str) -> dict:
    """Parse a 'data: <json>\\n\\n' SSE frame into the JSON payload."""
    assert msg.startswith("data: "), f"not an SSE data frame: {msg!r}"
    assert msg.endswith("\n\n"), f"missing SSE terminator: {msg!r}"
    return json.loads(msg[len("data: "):-2])


async def _take(gen, n, *, timeout: float = 2.0) -> list[str]:
    """Pull exactly n messages from an async generator or fail the test."""
    out: list[str] = []

    async def _pull() -> None:
        async for msg in gen:
            out.append(msg)
            if len(out) >= n:
                return

    try:
        await asyncio.wait_for(_pull(), timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(
            f"tail_events_sse did not produce {n} messages within {timeout}s "
            f"(got {len(out)}: {out!r})"
        )
    return out


# --- backlog --------------------------------------------------------------


@pytest.mark.asyncio
async def test_backlog_emits_existing_events_in_order(tmp_path):
    """First B yields are the LAST B events in file order."""
    path = tmp_path / "events.jsonl"
    for i in range(3):
        log_event(kind="cost", path=path, cost_usd=float(i))

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    msgs = await _take(gen, 3)
    await gen.aclose()

    costs = [_parse_sse_data(m)["cost_usd"] for m in msgs]
    assert costs == [0.0, 1.0, 2.0]


@pytest.mark.asyncio
async def test_backlog_caps_at_limit(tmp_path):
    """When the file has more events than `backlog`, only the last N appear."""
    path = tmp_path / "events.jsonl"
    for i in range(10):
        log_event(kind="cost", path=path, cost_usd=float(i))

    gen = tail_events_sse(
        path, backlog=3, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    msgs = await _take(gen, 3)
    await gen.aclose()

    costs = [_parse_sse_data(m)["cost_usd"] for m in msgs]
    assert costs == [7.0, 8.0, 9.0]


@pytest.mark.asyncio
async def test_backlog_includes_rotated_segments(tmp_path):
    """Last-N spans rotated segments + current file (history-aware)."""
    path = tmp_path / "events.jsonl"
    rotated = tmp_path / "events.jsonl.20260101-120000"
    # Two records in a rotated segment, two in the current file.
    rotated.write_text(
        json.dumps({"kind": "cost", "cost_usd": 0.1, "timestamp": "t"}) + "\n"
        + json.dumps({"kind": "cost", "cost_usd": 0.2, "timestamp": "t"}) + "\n"
    )
    log_event(kind="cost", path=path, cost_usd=0.3)
    log_event(kind="cost", path=path, cost_usd=0.4)

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    msgs = await _take(gen, 4)
    await gen.aclose()

    costs = [_parse_sse_data(m)["cost_usd"] for m in msgs]
    assert costs == [0.1, 0.2, 0.3, 0.4]


@pytest.mark.asyncio
async def test_empty_path_emits_no_backlog(tmp_path):
    """No file + no rotated segments → backlog is empty; first message is a
    new event landing during the tail loop."""
    path = tmp_path / "events.jsonl"  # does not exist
    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )

    async def append_after_delay() -> None:
        await asyncio.sleep(0.05)
        log_event(kind="cost", path=path, cost_usd=9.99)

    task = asyncio.create_task(append_after_delay())
    msgs = await _take(gen, 1)
    await task
    await gen.aclose()

    assert _parse_sse_data(msgs[0])["cost_usd"] == 9.99


# --- live tail ------------------------------------------------------------


@pytest.mark.asyncio
async def test_new_event_after_backlog_appears_in_tail(tmp_path):
    """Events written AFTER the backlog snapshot land in the live tail."""
    path = tmp_path / "events.jsonl"
    log_event(kind="cost", path=path, cost_usd=1.0)

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    # Drain backlog
    backlog_msgs = await _take(gen, 1)
    assert _parse_sse_data(backlog_msgs[0])["cost_usd"] == 1.0

    # New event after backlog
    log_event(kind="cost", path=path, cost_usd=2.0)
    tail_msgs = await _take(gen, 1)
    await gen.aclose()

    assert _parse_sse_data(tail_msgs[0])["cost_usd"] == 2.0


@pytest.mark.asyncio
async def test_tail_does_not_re_emit_backlog(tmp_path):
    """After backlog, the tail emits ONLY new events — no duplicate replay.

    This is the snapshot-atomicity invariant: backlog reads + handle seek
    happen under the same shared lock so the cutoff is a single point.
    """
    path = tmp_path / "events.jsonl"
    log_event(kind="cost", path=path, cost_usd=1.0)
    log_event(kind="cost", path=path, cost_usd=2.0)

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    backlog_msgs = await _take(gen, 2)
    assert [_parse_sse_data(m)["cost_usd"] for m in backlog_msgs] == [1.0, 2.0]

    log_event(kind="cost", path=path, cost_usd=3.0)
    tail_msgs = await _take(gen, 1)
    await gen.aclose()

    # Must be the NEW event, not a replay of the last backlog item.
    assert _parse_sse_data(tail_msgs[0])["cost_usd"] == 3.0


# --- rotation -------------------------------------------------------------


@pytest.mark.asyncio
async def test_rotation_detected_and_new_file_followed(tmp_path):
    """When events.py rotates the file (rename + new file), the tailer
    detects the inode change, reopens the new current file, and continues."""
    path = tmp_path / "events.jsonl"
    log_event(kind="cost", path=path, cost_usd=1.0)

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    # Drain backlog
    msgs = await _take(gen, 1)
    assert _parse_sse_data(msgs[0])["cost_usd"] == 1.0

    # Simulate events.py rotation: rename current → rotated stamp, then write
    # a new event which creates a fresh events.jsonl at the original path.
    rotated = tmp_path / "events.jsonl.20260513-120000"
    path.rename(rotated)
    # Give the tail loop one poll to notice the rotation before the new write.
    await asyncio.sleep(0.05)
    log_event(kind="cost", path=path, cost_usd=2.0)

    tail_msgs = await _take(gen, 1, timeout=3.0)
    await gen.aclose()

    assert _parse_sse_data(tail_msgs[0])["cost_usd"] == 2.0


# --- heartbeat ------------------------------------------------------------


@pytest.mark.asyncio
async def test_heartbeat_emitted_during_idle(tmp_path):
    """No new events → the next yield is `: ping\\n\\n` within heartbeat window."""
    path = tmp_path / "events.jsonl"
    log_event(kind="cost", path=path, cost_usd=0.5)

    gen = tail_events_sse(
        path, backlog=1, poll_fast_seconds=0.02, heartbeat_seconds=0.1
    )
    msgs = await _take(gen, 1)
    assert _parse_sse_data(msgs[0])["cost_usd"] == 0.5

    # The next message should be a heartbeat (no new events written).
    async def _next() -> str:
        async for msg in gen:
            return msg
        pytest.fail("generator exhausted unexpectedly")  # pragma: no cover

    msg = await asyncio.wait_for(_next(), timeout=2.0)
    await gen.aclose()

    assert msg == ": ping\n\n"


# --- error tolerance ------------------------------------------------------


@pytest.mark.asyncio
async def test_corrupt_history_does_not_break_stream(tmp_path):
    """A bad line in the file's history is silently skipped — connection
    survives so live events still reach the client."""
    path = tmp_path / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"kind": "cost", "cost_usd": 7.0, "timestamp": "t"}) + "\n"
        + "this-is-not-json\n"
        + json.dumps({"kind": "cost", "cost_usd": 8.0, "timestamp": "t"}) + "\n"
    )

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    # We should see the two parseable events, skipping the corrupt line.
    msgs = await _take(gen, 2)
    await gen.aclose()

    costs = [_parse_sse_data(m)["cost_usd"] for m in msgs]
    assert costs == [7.0, 8.0]


# --- cancellation ---------------------------------------------------------


@pytest.mark.asyncio
async def test_cancellation_releases_resources_cleanly(tmp_path):
    """`aclose()` on the generator does not raise and runs the finally
    block — proxy for "client disconnect doesn't leak file handles"."""
    path = tmp_path / "events.jsonl"
    log_event(kind="cost", path=path, cost_usd=0.01)

    gen = tail_events_sse(
        path, backlog=10, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )
    msgs = await _take(gen, 1)
    assert _parse_sse_data(msgs[0])["cost_usd"] == 0.01

    # Should not raise. The generator's finally block closes the handle.
    await gen.aclose()


# --- concurrent writers ---------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_writes_during_tail_do_not_tear(tmp_path):
    """Tail under load: multiple writers append while we tail; every line we
    receive parses cleanly (no torn JSON from flock-protected writes)."""
    path = tmp_path / "events.jsonl"

    gen = tail_events_sse(
        path, backlog=0, poll_fast_seconds=0.02, heartbeat_seconds=10.0
    )

    async def writer(n: int) -> None:
        # log_event is sync; run in default executor to avoid blocking the loop
        loop = asyncio.get_event_loop()
        for i in range(20):
            await loop.run_in_executor(
                None,
                lambda i=i, n=n: log_event(
                    kind="cost", path=path, cost_usd=float(i), writer_id=n
                ),
            )

    # Fire writers in parallel
    writer_task = asyncio.gather(*(writer(n) for n in range(3)))

    # Drain 60 events from the tail (3 writers × 20)
    out: list[str] = []

    async def _pull():
        async for msg in gen:
            if msg.startswith("data: "):
                out.append(msg)
                if len(out) >= 60:
                    return

    await asyncio.wait_for(_pull(), timeout=5.0)
    await writer_task
    await gen.aclose()

    # Every received frame must parse cleanly — torn writes would crash here.
    for msg in out:
        record = _parse_sse_data(msg)
        assert record["kind"] == "cost"
        assert "writer_id" in record
