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


class RateLimitHit(AuditError):
    """Raised by ``src/audit/claude_subprocess.parse_rate_limit`` when a
    ``"type": "rate_limit_event"`` is observed in claude's stream-json
    output. Carries the resets_at timestamp so the caller can decide
    whether to wait or halt."""


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
