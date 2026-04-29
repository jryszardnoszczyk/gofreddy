"""Typed errors raised across the audit pipeline.

Flat hierarchy: every typed error inherits from ``AuditError`` so callers
can catch all audit-specific failures with a single ``except AuditError``
clause without sweeping up unrelated stdlib exceptions.

Each docstring names the pipeline stage / module that raises the error so
the implementer can grep from raise-site to definition without reading
prose.
"""
from __future__ import annotations


class AuditError(Exception):
    """Base for all audit-pipeline errors. Catch this to handle any typed
    failure raised by ``src/audit/`` modules without catching unrelated
    stdlib exceptions."""


class CostCeilingReached(AuditError):
    """Raised by ``src/audit/cost_ledger.CostLedger.record`` when the
    hard breaker fires (audit mode: $150 cumulative; scan mode: $2). Caller
    persists state with ``pause_reason='cost_ceiling'`` and exits cleanly so
    ``freddy audit resume`` can pick up later."""


class SubscriptionWindowExceeded(AuditError):
    """Raised by ``src/audit/cost_ledger.CostLedger.record`` when R29 SLA
    hard breaker fires (50% of 5h subscription window in API-time, i.e. 90
    min of ``duration_api_ms``). Caller sets
    ``pause_reason='subscription_window_ceiling'`` and exits; resume waits
    for the next window."""


class RateLimitHit(AuditError):
    """Raised when ``src/audit/claude_subprocess.parse_rate_limit`` observes a
    ``"type": "rate_limit_event"`` with ``status=rejected`` in claude's
    stream-json output. Carries the resets_at unix timestamp so the caller
    can decide whether to wait for window reset or halt the audit.

    Shape mirrors ``harness/engine.RateLimitHit`` so a single port pattern
    handles both the harness-borrowed parser and audit-side raising."""

    def __init__(
        self,
        resets_at: int = 0,
        rate_limit_type: str = "",
        overage_disabled_reason: str = "",
    ) -> None:
        self.resets_at = resets_at
        self.rate_limit_type = rate_limit_type
        self.overage_disabled_reason = overage_disabled_reason
        suffix = f" overage={overage_disabled_reason}" if overage_disabled_reason else ""
        super().__init__(
            f"rate limit hit (type={rate_limit_type}, resetsAt={resets_at}){suffix}"
        )


class ViableResumeFailed(AuditError):
    """Raised by ``src/audit/resume.build_resume_plan`` when a session_id
    is recorded in state.json but the corresponding claude projects JSONL
    is missing from ``~/.claude/projects/<encoded-audit-dir>/<sid>.jsonl``
    (claude silent-hung before its first token), OR when ``audit_dir``
    itself is missing on a ``freddy audit resume <id>`` call."""


class MalformedSubSignalError(AuditError):
    """Raised by Stage 2 lens runner when a lens agent emits JSON that does
    not validate against ``src/audit/agent_models.SubSignal`` schema. The
    offending lens is recorded in ``state.failed_lenses`` and excluded from
    the geometric-mean aggregation per cluster-5 F5.3 institutional
    learning."""


class LaneRegistrationError(AuditError):
    """Raised by Stage ABC ``_load_prompt(name)`` when the requested stage
    prompt file is missing under
    ``programs/marketing_audit/prompts/<name>.md`` in the materialized
    variant directory. Fail-loud at module load surface, not silent skip."""


class EvolveLockHeld(AuditError):
    """Raised by ``autoresearch/evolve_lock.EvolveLock.__enter__`` when the
    mutex at ``~/.local/share/gofreddy/state.evolve_lock`` is already held
    (live audit running while evolve attempts to start, or vice versa).
    R16 mutex between live and evolve modes."""


class MissingSubscriptionToken(AuditError):
    """Raised by ``src/audit/cost_ledger.CostLedger`` at audit-start if
    ``CLAUDE_CODE_OAUTH_TOKEN`` is not set in the environment.
    Subscription-only billing is the v1 default per Key Decision §Execution
    model — this is the policy enforcement point, not the env allowlist."""
