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
  metadata.
- ``state.json`` (via ``AuditStateFile``) — running ``total_cost_usd`` is
  accumulated under the existing AuditState ``mutate`` lock. Crash-resume
  reads it from the snapshot.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.audit.claude_subprocess import ResultMessage
from src.audit.state import AuditStateFile


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
        analysis."""
        cost = float(result.total_cost_usd) if result.total_cost_usd > 0 else 0.0

        self._append_log(role, result, cost, model, metadata)

        self.state_file.mutate(
            lambda s: replace(s, total_cost_usd=s.total_cost_usd + cost)
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
