"""Graceful-stop primitives for the audit pipeline.

Surface is intentionally minimal — three functions wrapping the
``graceful_stop_requested`` + ``graceful_stop_reason`` fields on
``AuditState``. The pipeline runner checks ``is_stop_requested()`` between
stages (and inside Stage-2 fan-out) and breaks cleanly when the flag is
set.

Set-True paths in v1:
- cost_ledger on R10/R29 breach (after raising the typed error so the
  caller can also choose to retry mid-stage)
- external SIGTERM handler in cleanup.py (sets the flag, lets the next
  inter-stage checkpoint break the loop)

The flag is dict-based (lives in ``AuditState``) so resume after stop
sees the prior reason and can either ``clear_stop`` and re-run, or honor
it and stay paused. There is no SIGTERM hook on the main process
implicitly — the audit runs under the operator's terminal."""
from __future__ import annotations

from dataclasses import replace

from src.audit.state import AuditStateFile


def request_stop(state_file: AuditStateFile, *, reason: str) -> None:
    """Set ``graceful_stop_requested=True`` and persist ``reason``. Idempotent
    — repeated calls overwrite ``graceful_stop_reason`` so the most recent
    reason wins (callers that need to preserve the first reason should
    check ``is_stop_requested`` before calling)."""
    state_file.mutate(
        lambda s: replace(s, graceful_stop_requested=True, graceful_stop_reason=reason)
    )


def is_stop_requested(state_file: AuditStateFile) -> bool:
    """Read the flag from disk. Used by the pipeline runner between stages."""
    return state_file.load().graceful_stop_requested


def clear_stop(state_file: AuditStateFile) -> None:
    """Reset the flag + reason to defaults. Called by ``freddy audit resume``
    after the operator has resolved whatever set it."""
    state_file.mutate(
        lambda s: replace(s, graceful_stop_requested=False, graceful_stop_reason="")
    )
