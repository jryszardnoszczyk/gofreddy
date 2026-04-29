"""Per-audit cost ledger — claude envelope parsing + R10 ceilings + R29 SLA.

Net-new capability the codebase doesn't have: extract ``total_cost_usd`` +
``duration_api_ms`` from every ``ResultMessage``, accumulate per-audit,
enforce R10 soft/hard breakers, enforce R29 subscription-window SLA.

Persistence:
- ``cost_log.jsonl`` — append-only JSONL, one row per ``record()`` call,
  in the audit directory next to ``state.json``. Each row carries timestamp,
  role, model, total_cost_usd (or inferred), duration_ms, duration_api_ms,
  token counts, and arbitrary metadata.
- ``state.json`` (via ``AuditStateFile``) — running ``total_cost_usd`` and
  ``total_duration_api_ms`` are accumulated under the existing AuditState
  ``mutate`` lock. Crash-resume reads them from the snapshot.

Ceilings (R10):
- audit mode: soft-warn at $100 (stderr only), hard breaker at $150
  → ``CostCeilingReached``
- scan mode: hard breaker at $2 → ``CostCeilingReached``

R29 subscription-window SLA:
- Uses ``duration_api_ms`` (NOT ``duration_ms``); wall-clock is observability.
- Soft-warn at 40% of 5h API-time = 7,200,000 ms (stderr only).
- Hard breaker at 50% of 5h API-time = 9,000,000 ms
  → ``SubscriptionWindowExceeded``.
- (Plan body's parenthetical "72 min / 90 min" is arithmetically inconsistent
  with "40% / 50% of 5h"; the percentage-based reading is canonical.)

On hard breaker, state ``pause_reason`` is set so ``freddy audit resume``
can pick up cleanly after the operator resolves the underlying cause.

Subscription-billing zero-cost fallback: when ``ResultMessage.total_cost_usd``
is 0 but token counts are non-zero (typical of subscription-billed sessions
that don't surface estimated USD), the ledger infers cost via
``token_counts × claude_rates(model)``. The fallback is approximate but
sufficient for ceiling enforcement (the ceilings are coarse-grained
guardrails, not financial accounting).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.audit.checkpointing import write_atomic
from src.audit.claude_subprocess import ResultMessage
from src.audit.exceptions import (
    CostCeilingReached,
    MissingSubscriptionToken,
    SubscriptionWindowExceeded,
)
from src.audit.state import AuditStateFile
from src.common.cost_recorder import claude_rates


# ---------------------------------------------------------------------------
# R10 cost ceilings (USD)
# ---------------------------------------------------------------------------

AUDIT_SOFT_USD: float = 100.0
AUDIT_HARD_USD: float = 150.0
SCAN_HARD_USD: float = 2.0

# ---------------------------------------------------------------------------
# R29 SLA (API-time milliseconds)
# ---------------------------------------------------------------------------

# 5h subscription window in milliseconds.
_FIVE_HOURS_MS: int = 5 * 60 * 60 * 1000  # 18,000,000

R29_SOFT_API_MS: int = int(0.40 * _FIVE_HOURS_MS)  # 7,200,000 (40% of 5h)
R29_HARD_API_MS: int = int(0.50 * _FIVE_HOURS_MS)  # 9,000,000 (50% of 5h)


Mode = Literal["audit", "scan"]


@dataclass
class CostLedger:
    """Per-audit ledger of claude subprocess invocations.

    Holds a reference to the audit's ``AuditStateFile`` (for cumulative
    accounting under the existing mutate lock) plus a path to the per-audit
    ``cost_log.jsonl``. Mode discriminates the cost ceiling table.
    """

    state_file: AuditStateFile
    mode: Mode
    log_path: Path

    # Latched state — set when soft-warn fires so we don't re-warn on every
    # subsequent record(). Reset only by reconstructing the ledger.
    _cost_soft_warned: bool = field(default=False, init=False)
    _r29_soft_warned: bool = field(default=False, init=False)

    def assert_subscription_token(self) -> None:
        """At audit-start, refuse to proceed if ``CLAUDE_CODE_OAUTH_TOKEN`` is
        unset. This is the policy enforcement point per Key Decision §Execution
        model — the env allowlist (Unit 3 ``build_env``) preserves ANTHROPIC_API_KEY
        as a defensive fallback, but production runs MUST be subscription-billed."""
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            raise MissingSubscriptionToken(
                "CLAUDE_CODE_OAUTH_TOKEN is required for v1 subscription billing"
            )

    def record(
        self,
        role: str,
        result: ResultMessage,
        *,
        model: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a row to ``cost_log.jsonl``, accumulate cost + API-time into
        ``AuditState``, then enforce ceilings.

        ``role`` identifies the calling stage / lens (e.g. ``"stage_1b"``,
        ``"stage_2_lens_L-A-01"``, ``"stage_4_proposal"``). ``metadata`` is
        free-form — preserved verbatim in the JSONL for downstream analysis."""
        cost = self._effective_cost(result, model)
        api_ms = max(0, int(result.duration_api_ms))

        self._append_log(role, result, cost, model, metadata)

        new_state = self.state_file.mutate(
            lambda s: replace(
                s,
                total_cost_usd=s.total_cost_usd + cost,
                total_duration_api_ms=s.total_duration_api_ms + api_ms,
            )
        )

        self._check_cost_ceiling(new_state.total_cost_usd)
        self._check_subscription_window(new_state.total_duration_api_ms)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _effective_cost(self, result: ResultMessage, model: str) -> float:
        """Return claude's reported ``total_cost_usd`` if non-zero; otherwise
        fall back to ``tokens × claude_rates(model)`` inferred cost. The
        fallback is approximate (collapses cache_creation + cache_read into
        a single cached rate), used only for ceiling math."""
        if result.total_cost_usd > 0:
            return float(result.total_cost_usd)
        # Subscription-billing zero-cost fallback.
        input_rate, cached_rate, output_rate = claude_rates(model)
        non_cached_in = max(0, result.input_tokens - result.cache_read_input_tokens)
        cached_in = result.cache_read_input_tokens + result.cache_creation_input_tokens
        return (
            (non_cached_in / 1_000_000) * input_rate
            + (cached_in / 1_000_000) * cached_rate
            + (result.output_tokens / 1_000_000) * output_rate
        )

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

    def _check_cost_ceiling(self, total_cost_usd: float) -> None:
        if self.mode == "scan":
            if total_cost_usd > SCAN_HARD_USD:
                self._set_pause("cost_ceiling")
                raise CostCeilingReached(
                    f"scan cost ceiling reached: ${total_cost_usd:.2f} > ${SCAN_HARD_USD:.2f}"
                )
            return

        # audit mode
        if total_cost_usd > AUDIT_HARD_USD:
            self._set_pause("cost_ceiling")
            raise CostCeilingReached(
                f"audit cost ceiling reached: ${total_cost_usd:.2f} > ${AUDIT_HARD_USD:.2f}"
            )
        if total_cost_usd > AUDIT_SOFT_USD and not self._cost_soft_warned:
            self._cost_soft_warned = True
            print(
                f"[cost_ledger] soft-warn: audit cost ${total_cost_usd:.2f} crossed "
                f"${AUDIT_SOFT_USD:.2f} soft threshold; proceeding (hard at ${AUDIT_HARD_USD:.2f})",
                file=sys.stderr,
            )

    def _check_subscription_window(self, total_duration_api_ms: int) -> None:
        if total_duration_api_ms > R29_HARD_API_MS:
            self._set_pause("subscription_window_ceiling")
            raise SubscriptionWindowExceeded(
                f"R29 subscription-window hard breaker: {total_duration_api_ms} ms API-time "
                f"> {R29_HARD_API_MS} ms (50% of 5h window); halting Stage 2+ fan-out"
            )
        if total_duration_api_ms > R29_SOFT_API_MS and not self._r29_soft_warned:
            self._r29_soft_warned = True
            print(
                f"[cost_ledger] R29 soft-warn: subscription API-time {total_duration_api_ms} ms "
                f"crossed {R29_SOFT_API_MS} ms (40% of 5h); proceeding "
                f"(hard at {R29_HARD_API_MS} ms)",
                file=sys.stderr,
            )

    def _set_pause(self, reason: str) -> None:
        self.state_file.mutate(lambda s: replace(s, pause_reason=reason))
