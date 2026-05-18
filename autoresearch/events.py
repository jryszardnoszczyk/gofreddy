"""Append-only unified events log for autoresearch-side audit trails.

Writers hold an exclusive flock across write+flush+fsync (POSIX advisory lock).
Readers hold a shared lock. On size > 100MB, log_event rotates to
``events.jsonl.<YYYYMMDD-HHMMSS>``. read_events concatenates rotated segments
(oldest first by mtime) then the current file.
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


# Repo-root anchor for per-client event log resolution. Two `.parent` calls
# from `autoresearch/events.py` land on the repo root regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent


# Portal-coordinated event kinds (Content Engine v1 U6b).
#
# This is the canonical registry — additive, not enforced. Existing call
# sites with kinds outside this set continue to log fine; removing a
# listed kind would un-block portal features that depend on it. Drift
# tests in tests/autoresearch/test_events.py pin the registry so a
# silent removal is caught by CI.
KNOWN_KINDS: frozenset[str] = frozenset({
    # Original autoresearch-internal kinds (pre-Content Engine v1).
    "judge_unreachable",
    "judge_abstain",
    "judge_audit",
    "judge_batch_fallback",
    "judge_raw",
    "head_score",
    # Portal moments timeline (Content Engine v1 U6b — R-Schema-1 / R-Lane-2).
    # Lanes call log_event(kind="moment", client_id=<slug>, metadata={...})
    # directly — no emit_moment wrapper per TD-56.
    "moment",
    # Pre-publish review service (Content Engine v1 U7 — D14 + portal R-Schema-1).
    # review_required emitted at submit; review_approve / review_reject at
    # reviewer decision; sla_escalation when secondary reviewer is paged
    # per TD-2 revised; sla_breach at 2× SLA auto-pause per TD-9.
    "review_required",
    "review_approve",
    "review_reject",
    "sla_escalation",
    "sla_breach",
})


# Portal-coordinated event field names (Content Engine v1 U6b — R-Schema-3).
#
# Canonical semantics: every event implicitly carries `kind` + `timestamp`;
# portal-coordinated fields below carry stable semantics across kinds so
# the portal timeline can render without per-kind transformation.
CANONICAL_FIELDS: frozenset[str] = frozenset({
    # Always present on every event (set by log_event):
    "kind",
    "timestamp",
    # Common across kinds, set by callers when relevant:
    "client_id",        # Routes the event to per-client log + portal scope.
    "actor",            # "human" | "agent" | "system" — provenance.
    "action",           # Verb describing the event (e.g. "submit_for_review").
    "metadata",         # Free-form per-kind payload.
    # Moment-specific (R-Schema-3):
    "moment_kind",      # session_start | deliverable_ready | session_completed | ...
    "source_event_ids", # Upstream events that triggered this moment.
    "title",            # Operator-readable title (≤120 chars).
    "body",             # Optional longer-form prose for the timeline.
})


def client_events_path(slug: str) -> Path:
    """Return the per-client event log path for ``slug``.

    Convention: ``clients/<slug>/audit/events.jsonl``. Mirrors the
    audit pipeline's per-client workspace + lets U7 + lane authors
    route events to a single, scopable log per client. Same rotation
    + flock semantics as the global log when passed via
    ``log_event(path=client_events_path(slug), ...)``.
    """
    return _REPO_ROOT / "clients" / slug / "audit" / "events.jsonl"


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
