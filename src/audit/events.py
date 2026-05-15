"""Per-audit + global event logging.

Thin wrapper around ``autoresearch.events.log_event`` (which now accepts
an optional ``path=`` argument). The audit pipeline writes operational
events (stage_start, stage_end, lens_complete, cost_warn, etc.) to three
destinations:

- ``<audit_dir>/events.jsonl`` — per-audit local log; replays stage flow
  for resume + post-mortem (always written; source of truth)
- ``clients/<slug>/audit/events.jsonl`` — per-client WIDE log; mirrored
  automatically when ``audit_dir`` is under ``clients/<slug>/audit/<id>/``.
  This is the log the portal SSE endpoint tails, so without this mirror
  audit-pipeline events would be invisible to clients (only provider
  costs from cost_recorder + render-judge completions would show).
- ``~/.local/share/gofreddy/events.jsonl`` — operator-internal global;
  receives audit-lifecycle events (audit_start, audit_end, audit_paused)
  via ``log_global`` so the operator can grep across every audit.

Per-audit events stay isolated to the audit dir for resume; per-client
mirroring is a portal-visibility concern and must not regress the per-
audit write (mirror failures are swallowed with a warning).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from autoresearch.events import log_event as _log_event

logger = logging.getLogger(__name__)


def _wide_log_for(audit_dir: Path) -> tuple[str, Path] | None:
    """Return ``(slug, wide_log_path)`` if ``audit_dir`` is shaped
    ``<root>/clients/<slug>/audit/<audit_id>(/...)?``, else None.

    The wide log lands at ``<root>/clients/<slug>/audit/events.jsonl``,
    derived from the SAME root the caller passed — we do not rely on
    ``cwd`` or on ``autoresearch.events.client_events_path`` (which
    returns a relative path). This is the only correct derivation when
    the audit process can be launched from any working directory.

    Requires the audit_id segment to exist so we don't mirror the wide
    log back to itself when a caller passes ``clients/<slug>/audit/``
    directly (that path IS the wide log).
    """
    parts = audit_dir.parts
    for i, part in enumerate(parts):
        if (
            part == "clients"
            and i + 3 < len(parts)
            and parts[i + 2] == "audit"
        ):
            slug = parts[i + 1]
            wide_log = Path(*parts[: i + 3]) / "events.jsonl"
            return slug, wide_log
    return None


def _slug_from_audit_dir(audit_dir: Path) -> str | None:
    """Backwards-compat shim — return just the slug. Prefer ``_wide_log_for``
    for new callers that need the wide-log path too."""
    found = _wide_log_for(audit_dir)
    return None if found is None else found[0]


def log_to_audit(audit_dir: Path, kind: str, /, **data: Any) -> None:
    """Append an event to ``<audit_dir>/events.jsonl`` (source of truth)
    and, when ``audit_dir`` is a per-client audit subdir, also mirror to
    the per-client wide log so portal subscribers see the event live.

    Inherits flock + rotation from ``autoresearch.events.log_event`` —
    same 100 MB rotation threshold, same exclusive-lock-on-write. The
    mirror is a best-effort write; a failure there is logged but never
    propagates, so audit-pipeline behavior is unchanged when the wide
    log is unavailable (disk full on the clients/ tree, permissions,
    etc.).
    """
    audit_dir = Path(audit_dir)
    # Source of truth — must not be skipped under any condition.
    _log_event(kind, path=audit_dir / "events.jsonl", **data)

    # Mirror to per-client wide log if audit_dir matches the tenant layout.
    found = _wide_log_for(audit_dir)
    if found is None:
        return
    slug, wide_log_path = found
    try:
        mirror_data: dict[str, Any] = dict(data)
        mirror_data.setdefault("client_id", slug)
        mirror_data.setdefault("audit_id", audit_dir.name)
        _log_event(kind, path=wide_log_path, **mirror_data)
    except Exception:
        logger.warning(
            "audit_event_wide_log_mirror_failed",
            extra={"slug": slug, "audit_dir": str(audit_dir), "kind": kind},
            exc_info=True,
        )


def log_global(kind: str, /, **data: Any) -> None:
    """Append an event to the autoresearch default
    (``~/.local/share/gofreddy/events.jsonl``). Use for audit-lifecycle
    events that should be cross-audit greppable."""
    _log_event(kind, **data)
