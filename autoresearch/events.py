"""Append-only unified events log for autoresearch-side audit trails.

Writers hold an exclusive flock across write+flush+fsync (POSIX advisory lock).
Readers hold a shared lock. On size > 100MB, log_event rotates to
``events.jsonl.<YYYYMMDD-HHMMSS>``. read_events concatenates rotated segments
(oldest first by mtime) then the current file.

## Canonical event schema (locked 2026-05-13 per
``docs/brainstorms/2026-05-13-client-portal-telemetry-design.md``)

Every record is a single JSONL line with the following canonical shape:

.. code-block:: python

    {
      "kind":            "tool_call|model_call|edit|render|"
                         "review_approve|review_reject|sla_breach|"
                         "session_start|session_end|cost|"
                         "promotion|alert|<custom>",
      "timestamp":       "2026-05-13T15:42:01.234Z",    # ISO8601 UTC, Z-suffixed
      # --- canonical optional fields (encouraged on all sources) ---
      "event_id":        "01HXYZ...",                    # ULID, K-sortable
      "session_id":      "uuid",                         # groups a run
      "parent_event_id": "ulid|null",                    # tree views: model_call inside tool_call
      "source":          "autoresearch|claude_code|codex|portal|reviewer",
      "client_id":       "klinika-melitus|dwf-poland|null",
      "actor":           "agent|human|system",
      "lane":            "marketing_audit|x_engine|site_engine|...|null",
      "variant":         "v123|null",
      "fixture":         "klinika_hero|null",
      "action":          "string",                       # short verb, human-readable
      "args":            {},
      "status":          "started|complete|failed|skipped",
      "cost_usd":        0.0123,
      "model":           "claude-opus-4-7|gpt-5.5|gemini-2.5|null",
      "tokens_in":       1234,
      "tokens_out":      567,
      "metadata":        {},                             # source-specific overflow
    }

Rules:

* ``kind`` and ``timestamp`` are MANDATORY (timestamp is injected by
  ``log_event``; callers MUST supply ``kind``).
* All other canonical fields are OPTIONAL. Callers SHOULD supply
  ``client_id``, ``actor``, ``source`` whenever known. Missing fields
  are written through to the JSON (kept absent, not nulled).
* ``client_id`` resolution: writes to a client's ``events.jsonl`` MUST
  carry the matching ``client_id``. Operator-internal autoresearch
  (L1 self-improvement, no client attribution) writes ``client_id=null``
  or omits the field entirely.
* New custom fields are encouraged in ``metadata`` first; promote to
  canonical only after ≥2 sources adopt the same field name.

## Per-tenant path resolution

``path`` overrides the default ``EVENTS_LOG`` destination, enabling
per-client telemetry isolation:

* Operator-internal:    ``~/.local/share/gofreddy/events.jsonl``     (default)
* Per-client telemetry: ``clients/<slug>/audit/<run_id>/events.jsonl``

Use ``client_events_path(slug, run_id)`` to compute the per-client path
consistently across all consumers (writers AND tail-followers).

## Consumers

* **autoresearch lanes** — emit via ``log_event`` directly (existing path).
* **cost_recorder.record** — augmented to also emit ``kind="cost"`` events
  with ``cost_usd / tokens_in / tokens_out / model``.
* **evaluate_variant._ensure_render_score** — emits ``kind="render"`` on
  completion of render-judge.
* **Claude Code hook** — POSTs to ``/v1/portal/_ingest`` which writes via
  ``log_event(source="claude_code", ...)``.
* **plan-002 U7 reviewer service** — emits ``kind="review_approve"`` /
  ``"review_reject"`` / ``"sla_breach"`` via ``log_event``, NOT a separate
  writer.
* **SSE stream endpoint** — ``/v1/portal/{slug}/stream`` tails the per-client
  JSONL via ``read_events``-equivalent follower; clients see their own
  events in near-real-time.

See: ``docs/brainstorms/2026-05-13-client-portal-telemetry-design.md``
for the full design (3 ingestion paths, SSE plumbing, frontend, phasing).
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import fcntl
import json
import os
from collections import deque
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

EVENTS_LOG = Path.home() / ".local/share/gofreddy/events.jsonl"
ROTATION_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MB

# Canonical event kinds — extend deliberately; new kinds require an entry here
# AND a corresponding consumer in the portal frontend's kind→colour mapping.
# Source: docs/brainstorms/2026-05-13-client-portal-telemetry-design.md
KNOWN_KINDS: frozenset[str] = frozenset({
    # Agent-side
    "session_start",
    "session_end",
    "tool_call",
    "model_call",
    "edit",
    "cost",
    "render",
    "promotion",
    # Human-side
    "review_approve",
    "review_reject",
    "sla_breach",
    # System-side
    "alert",
})

# Canonical optional fields — used by validators / typing helpers to detect
# typos in calling code. Unknown fields land in the record as-is (we don't
# reject) but won't be promoted to first-class portal columns until added here.
CANONICAL_FIELDS: frozenset[str] = frozenset({
    "kind",
    "timestamp",
    "event_id",
    "session_id",
    "parent_event_id",
    "source",
    "client_id",
    "actor",
    "lane",
    "variant",
    "fixture",
    "action",
    "args",
    "status",
    "cost_usd",
    "model",
    "tokens_in",
    "tokens_out",
    "metadata",
})


def client_events_path(client_id: str | None, run_id: str | None = None) -> Path:
    """Resolve the canonical per-client events.jsonl path.

    Use this helper from every writer + tail-follower to keep path layout
    consistent across producers and consumers.

    * ``client_id=None`` → operator-internal ``EVENTS_LOG``
    * ``client_id="klinika-melitus", run_id="abc123"`` →
      ``clients/klinika-melitus/audit/abc123/events.jsonl``
    * ``client_id="klinika-melitus", run_id=None`` →
      ``clients/klinika-melitus/audit/events.jsonl`` (client-wide stream,
      used by the SSE endpoint to tail across all runs for the client)
    """
    if client_id is None:
        return EVENTS_LOG
    base = Path("clients") / client_id / "audit"
    if run_id is None:
        return base / "events.jsonl"
    return base / run_id / "events.jsonl"


class EventLogCorruption(RuntimeError):
    """Raised when a non-empty events.jsonl line fails to parse as JSON."""


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _maybe_rotate(path: Path) -> None:
    if not path.exists() or path.stat().st_size < ROTATION_THRESHOLD_BYTES:
        return
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    path.rename(path.parent / f"{path.name}.{stamp}")


def log_event(kind: str, *, path: Path | None = None, **data: Any) -> None:
    """Append one ``{kind, timestamp, **data}`` record as a single JSONL line.

    Exclusive-locked to prevent torn lines under concurrent writers.
    Durability: flush + fsync after every write.

    ``path`` overrides the default ``EVENTS_LOG`` destination, enabling
    per-audit local event logs (``clients/<slug>/audit/<id>/events.jsonl``)
    while preserving the global default for autoresearch-internal call
    sites that pass no ``path``. Rotation policy + flock semantics apply
    uniformly regardless of which path is in use.
    """
    path = path if path is not None else EVENTS_LOG
    _ensure_parent(path)
    _maybe_rotate(path)
    record = {
        "kind": kind,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        **data,
    }
    with path.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_events(
    *, kind: str | None = None, path: Path | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield records from events.jsonl + rotated segments, filtered by kind.

    Shared-locked (reads can run concurrently). Malformed lines raise
    EventLogCorruption with the file + line number — never silent skip.
    Ordering: rotated segments in mtime order (oldest first), then current file.
    """
    root = path or EVENTS_LOG
    rotated = sorted(
        root.parent.glob(root.name + ".*"),
        key=lambda p: p.stat().st_mtime,
    ) if root.parent.exists() else []
    segments: list[Path] = list(rotated)
    if root.exists():
        segments.append(root)
    for segment in segments:
        with segment.open("r") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                for line_no, raw in enumerate(handle, start=1):
                    line = raw.rstrip("\n")
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise EventLogCorruption(
                            f"{segment}:{line_no}: {exc}"
                        ) from exc
                    if kind is None or record.get("kind") == kind:
                        yield record
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# SSE tail-follower (P4 portal-telemetry)
#
# tail_events_sse(path) is an async generator that yields SSE-framed strings:
#   * "data: <json>\n\n"  — one per event
#   * ": ping\n\n"        — heartbeat keepalive every `heartbeat_seconds`
#
# It is the read-side counterpart to log_event:
#   * Holds shared (LOCK_SH) flock only during the short read step — writers
#     can grab LOCK_EX between our polls, so concurrent log_event calls do
#     not stall behind a long-lived SSE connection.
#   * Detects rotation via inode comparison (events.jsonl renamed to
#     events.jsonl.<stamp> when size > 100MB). When the inode at `path` no
#     longer matches our open handle's inode, we close + reopen.
#   * Backlog is the last N events from `read_events`, capped with a deque
#     so memory stays bounded even on large rotated histories.
#
# v1 limitation: tails ONLY the path passed in. Per-run subdirectories under
# clients/<slug>/audit/<run_id>/events.jsonl are NOT followed; they are
# intentionally isolated from the wide-log stream. If a future caller wants
# per-run isolation surfaced live, give it a dedicated route or a multi-path
# follower; do not silently fan out from here.
# ---------------------------------------------------------------------------

_DEFAULT_BACKLOG = 50
_DEFAULT_HEARTBEAT_SECONDS = 15.0
_DEFAULT_POLL_FAST_SECONDS = 0.25
_DEFAULT_POLL_SLOW_SECONDS = 1.0
_DEFAULT_BACKOFF_AFTER_SECONDS = 30.0


def _parse_jsonl_bytes(data: bytes) -> Iterator[dict[str, Any]]:
    """Yield parsed records from a JSONL byte chunk, skipping blanks + corrupt
    lines silently. Used for backlog assembly where one bad line must not
    prevent serving the rest of the history to a fresh SSE client.
    """
    for raw in data.split(b"\n"):
        raw = raw.strip()
        if not raw:
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue


def _open_at_eof_under_shared_lock(
    path: Path,
) -> tuple[Any, int, bytes]:
    """Open `path` rb, read all current bytes under LOCK_SH, return (handle, inode, data).

    Atomicity guarantee: the returned `data` is the file's content as of the
    moment LOCK_SH was held, and `handle.read()` left the file pointer at EOF
    of that same snapshot. Subsequent reads from `handle` will therefore see
    only bytes appended AFTER the snapshot — no overlap with `data`, no gap.

    Caller is responsible for closing `handle` (typically in a `finally`).
    """
    handle = path.open("rb")
    inode = os.fstat(handle.fileno()).st_ino
    fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
    try:
        data = handle.read()
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return handle, inode, data


def _read_rotated_segments(path: Path) -> Iterator[dict[str, Any]]:
    """Yield records from rotated `events.jsonl.<stamp>` segments in mtime order.

    Each segment is read under its own shared lock so a concurrent writer
    rotating again mid-iteration cannot tear our reads. Corrupt segments
    yield nothing (silent) rather than aborting backlog assembly.
    """
    if not path.parent.exists():
        return
    rotated = sorted(
        path.parent.glob(path.name + ".*"),
        key=lambda p: p.stat().st_mtime,
    )
    for segment in rotated:
        try:
            with segment.open("rb") as fh:
                fcntl.flock(fh.fileno(), fcntl.LOCK_SH)
                try:
                    seg_data = fh.read()
                finally:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            continue
        yield from _parse_jsonl_bytes(seg_data)


def _format_sse(record: dict[str, Any]) -> str:
    """Frame one event as a single SSE message.

    `data:` followed by a single-line JSON, then a blank line. JSON is dumped
    with `default=str` so unexpected non-JSON-native values (datetime, Path)
    coerce instead of raising — defensive against future writer changes.
    """
    return f"data: {json.dumps(record, default=str)}\n\n"


async def tail_events_sse(
    path: Path,
    *,
    backlog: int = _DEFAULT_BACKLOG,
    heartbeat_seconds: float = _DEFAULT_HEARTBEAT_SECONDS,
    poll_fast_seconds: float = _DEFAULT_POLL_FAST_SECONDS,
    poll_slow_seconds: float = _DEFAULT_POLL_SLOW_SECONDS,
    backoff_after_seconds: float = _DEFAULT_BACKOFF_AFTER_SECONDS,
) -> AsyncIterator[str]:
    """Yield SSE-framed strings: backlog first, then live tail with heartbeats.

    Rotation handling: log_event renames the current file to
    ``events.jsonl.<YYYYMMDD-HHMMSS>`` when size > 100MB, then the next write
    creates a fresh empty file at the same path. We detect this via inode
    comparison (the rotated-away file's inode stays in our handle; the path
    points to a new inode) and reopen. Without this, SSE clients would stay
    bound to the rotated-away file forever and never see new events.

    Polling backs off from `poll_fast_seconds` (250ms by default) to
    `poll_slow_seconds` (1s) after `backoff_after_seconds` (30s) of silence.
    On any new event, resets to fast. Keeps responsiveness during bursts
    without burning CPU on idle clients.

    Heartbeat (`: ping\\n\\n`) is emitted every `heartbeat_seconds` regardless
    of event activity — required to keep proxies (nginx, Cloudflare, Fly's
    edge) from closing connections that look idle.

    Cancellation: when the consumer (e.g. a disconnected SSE client) cancels
    the iteration, we close the open file handle in `finally`. The
    `CancelledError` propagates so StreamingResponse can finalize cleanly.
    """
    loop = asyncio.get_event_loop()

    # --- atomic snapshot: open current file + drain bytes under shared lock,
    # so the handle ends positioned at EOF of the same snapshot used for
    # backlog. No overlap (no duplicate events on tail) and no gap (no events
    # missed in the race between backlog and tail-start).
    handle = None
    inode: int | None = None
    current_data = b""
    if path.exists():
        handle, inode, current_data = _open_at_eof_under_shared_lock(path)

    # --- backlog: last N records from rotated segments + snapshot, capped
    # by deque so a 100MB rotated history doesn't load into memory.
    window: deque[dict[str, Any]] = deque(maxlen=backlog)
    for record in _read_rotated_segments(path):
        window.append(record)
    for record in _parse_jsonl_bytes(current_data):
        window.append(record)
    for record in window:
        yield _format_sse(record)

    buffer = b""
    now = loop.time()
    last_event_at = now
    last_heartbeat_at = now

    try:
        while True:
            now = loop.time()

            # --- rotation + lazy-open detection -----------------------------
            try:
                current_inode: int | None = os.stat(path).st_ino
            except FileNotFoundError:
                current_inode = None

            if handle is None and current_inode is not None:
                # Path appeared after we started (fresh client emitting its
                # first event). Read from start — backlog was empty so no
                # duplicate risk.
                handle = path.open("rb")
                inode = current_inode
            elif (
                handle is not None
                and current_inode is not None
                and current_inode != inode
            ):
                # Rotation: path now points to a new inode (events.jsonl was
                # renamed and recreated). Close the rotated-away handle and
                # read the new file from start.
                handle.close()
                handle = path.open("rb")
                inode = current_inode
                buffer = b""  # any partial line in the rotated-away file is gone

            # --- read any new bytes under shared lock -----------------------
            if handle is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
                try:
                    chunk = handle.read()
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                if chunk:
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            # Torn lines should be impossible under flock, but
                            # if a corrupt segment is mid-stream we skip the
                            # line rather than tear down the connection.
                            continue
                        yield _format_sse(record)
                        last_event_at = now
                        last_heartbeat_at = now

            # --- heartbeat --------------------------------------------------
            if now - last_heartbeat_at >= heartbeat_seconds:
                yield ": ping\n\n"
                last_heartbeat_at = now

            # --- adaptive poll interval -------------------------------------
            silence = now - last_event_at
            interval = (
                poll_slow_seconds
                if silence > backoff_after_seconds
                else poll_fast_seconds
            )
            await asyncio.sleep(interval)
    finally:
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
