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

import datetime as _dt
import fcntl
import json
import os
from pathlib import Path
from typing import Any, Iterator

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
