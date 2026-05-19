"""Per-audit cost ledger — claude envelope parsing + cumulative accounting.

Net-new capability the codebase doesn't have: extract ``total_cost_usd`` +
``duration_ms`` from every ``ResultMessage``, accumulate per-audit. v1
ships **observability without enforcement** per master plan §1 Goal 6 +
§3.9 — costs are recorded, no breakers fire. First 5 paid audits
calibrate the empirical baseline; ceilings are revisited post-audit-5.

R29 subscription-window SLA + cost-ceiling enforcement (CostCeilingReached
/ SubscriptionWindowExceeded / MissingSubscriptionToken) were dropped in
the L1 rebase off ``phase-1-foundation-snapshot`` — fusion-only constructs
per master plan §1 Non-goals 5 + 6.

Persistence:
- ``cost_log.jsonl`` — append-only JSONL, one row per ``record()`` call,
  in the audit directory next to ``state.json``. Each row carries timestamp,
  role, model, total_cost_usd, duration_ms, token counts, and arbitrary
  metadata. **This file is the source of truth for cost-ledger math.**
- ``state.json`` (via ``AuditStateFile``) — running ``total_cost_usd`` is
  accumulated under the existing AuditState ``mutate`` lock. Crash-resume
  reads it from the snapshot.
- Per-client wide events log (portal visibility) — when ``log_path`` is
  under ``clients/<slug>/audit/<audit_id>/``, ``record()`` also emits a
  canonical ``kind="cost"`` event so the portal's cost rollup includes
  claude subprocess costs (the biggest dollar line in any audit).
  Mirror is best-effort — a failure here is logged but never propagates,
  so cost-ledger writes remain unaffected.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.audit.claude_subprocess import ResultMessage
from src.audit.state import AuditStateFile

logger = logging.getLogger(__name__)


def _wide_log_for(log_path: Path) -> tuple[str, Path] | None:
    """Return ``(slug, wide_log_path)`` when ``log_path`` is under
    ``<root>/clients/<slug>/audit/<audit_id>/...``, else None.

    Wide log lands at ``<root>/clients/<slug>/audit/events.jsonl``,
    derived from the SAME root the caller passed (cwd-independent — the
    audit pipeline can launch from any working directory). Mirrors the
    rule used by ``src.audit.events._wide_log_for`` so the two writers
    agree on what counts as a per-tenant audit.
    """
    parts = log_path.parts
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


Mode = Literal["audit", "scan"]


@dataclass
class CostLedger:
    """Per-audit ledger of claude subprocess invocations.

    Holds a reference to the audit's ``AuditStateFile`` (for cumulative
    accounting under the existing mutate lock) plus a path to the per-audit
    ``cost_log.jsonl``. ``mode`` is preserved for downstream observability
    callers that want to differentiate audit vs scan invocations even
    though no breaker logic uses it in v1.
    """

    state_file: AuditStateFile
    mode: Mode
    log_path: Path

    def record(
        self,
        role: str,
        result: ResultMessage,
        *,
        model: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a row to ``cost_log.jsonl`` and accumulate cost into
        ``AuditState.total_cost_usd``. No ceilings enforced in v1.

        ``role`` identifies the calling stage / lens (e.g. ``"stage_1b"``,
        ``"stage_2_lens_L-A-01"``, ``"stage_4_proposal"``). ``metadata`` is
        free-form — preserved verbatim in the JSONL for downstream
        analysis.

        When ``log_path`` is shaped ``clients/<slug>/audit/<audit_id>/...``,
        also emits a canonical ``kind="cost"`` event so the portal's cost
        rollup includes claude subprocess costs. Mirror failure is logged
        but never propagates — cost_log.jsonl + state.json remain the
        source of truth.
        """
        cost = float(result.total_cost_usd) if result.total_cost_usd > 0 else 0.0

        self._append_log(role, result, cost, model, metadata)

        self.state_file.mutate(
            lambda s: replace(s, total_cost_usd=s.total_cost_usd + cost)
        )

        self._mirror_to_canonical_events(role, result, cost, model, metadata)

    def _mirror_to_canonical_events(
        self,
        role: str,
        result: ResultMessage,
        cost: float,
        model: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        """Emit ``kind="cost"`` on the per-client wide log when this ledger
        is bound to a per-tenant audit dir. Skips silently for non-tenant
        audits (operator-internal work, test fixtures).
        """
        found = _wide_log_for(self.log_path)
        if found is None:
            return
        slug, wide_log_path = found
        try:
            from autoresearch.events import log_event

            audit_id = self.log_path.parent.name
            payload: dict[str, Any] = {
                "source": "audit",
                "action": f"claude.{role}",
                "status": "failed" if result.is_error else "complete",
                "actor": "agent",
                "client_id": slug,
                "audit_id": audit_id,
                "session_id": result.session_id,
                "cost_usd": cost,
                "duration_ms": result.duration_ms,
                "tokens_in": result.input_tokens,
                "tokens_out": result.output_tokens,
                "metadata": {
                    "mode": self.mode,
                    "role": role,
                    "cache_creation_input_tokens": result.cache_creation_input_tokens,
                    "cache_read_input_tokens": result.cache_read_input_tokens,
                    "num_turns": result.num_turns,
                    "stop_reason": result.stop_reason,
                    **(metadata or {}),
                },
            }
            if model:
                payload["model"] = model
            log_event(kind="cost", path=wide_log_path, **payload)
        except Exception:
            logger.warning(
                "cost_ledger_event_mirror_failed",
                extra={"role": role, "slug": slug, "log_path": str(self.log_path)},
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _append_log(
        self,
        role: str,
        result: ResultMessage,
        cost: float,
        model: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "model": model,
            "subtype": result.subtype,
            "session_id": result.session_id,
            "is_error": result.is_error,
            "total_cost_usd": cost,
            "duration_ms": result.duration_ms,
            "duration_api_ms": result.duration_api_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cache_creation_input_tokens": result.cache_creation_input_tokens,
            "cache_read_input_tokens": result.cache_read_input_tokens,
            "num_turns": result.num_turns,
            "stop_reason": result.stop_reason,
            "metadata": metadata or {},
        }
        # Append in a single write — atomic at the OS-syscall level on POSIX
        # for buffer-sized payloads. cost_log entries are tiny (<2KB).
        line = json.dumps(row, default=str) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as fp:
            fp.write(line)
