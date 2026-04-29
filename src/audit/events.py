"""Per-audit + global event logging.

Thin wrapper around ``autoresearch.events.log_event`` (which now accepts
an optional ``path=`` argument). The audit pipeline writes operational
events (stage_start, stage_end, lens_complete, cost_warn, etc.) to two
destinations:

- ``<audit_dir>/events.jsonl`` — per-audit local log; replays stage flow
  for resume + post-mortem
- ``~/.local/share/gofreddy/events.jsonl`` — global default; receives
  audit-lifecycle events (audit_start, audit_end, audit_paused) so the
  operator can grep across all audits

Per-audit events are isolated to the audit directory; global events are
shared with autoresearch's evolve loop telemetry. Callers choose the
destination explicitly via ``log_to_audit`` vs ``log_global``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from autoresearch.events import log_event as _log_event


def log_to_audit(audit_dir: Path, kind: str, /, **data: Any) -> None:
    """Append an event to ``<audit_dir>/events.jsonl``. Inherits flock +
    rotation behavior from ``autoresearch.events.log_event`` — same 100 MB
    rotation threshold, same exclusive-lock-on-write."""
    _log_event(kind, path=audit_dir / "events.jsonl", **data)


def log_global(kind: str, /, **data: Any) -> None:
    """Append an event to the autoresearch default
    (``~/.local/share/gofreddy/events.jsonl``). Use for audit-lifecycle
    events that should be cross-audit greppable."""
    _log_event(kind, **data)
