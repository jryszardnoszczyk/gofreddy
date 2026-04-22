"""Safety primitives for the three legitimate operating tiers across pipelines.

Three pipelines already operate at three different safety tiers; this package
names them explicitly and publishes one sub-module per tier. Each pipeline
imports from the single tier it operates at; the tier-named import (e.g.
``from src.shared.safety.tier_c import check_scope``) makes the safety model
impossible to misread.

Tier A — read-only / capability-restricted (audit-plan agents).
    Mechanism: scoped MCP toolbelts that *positively* limit the tool surface
    (``permission_mode="default"`` + ``disallowed_tools=[...]`` + a small
    allowlist of observation-only ``mcp__*`` tools). Per-action human confirm
    for irrecoverable operations. Threat: an agent with WebFetch/Bash/Write
    could click destructive buttons, submit forms, leak PII, or violate
    prospect ToS. The destructive capability is positively absent from the
    toolbelt — there is no path to invoke it even under prompt injection.
    Primitives live in :mod:`src.shared.safety.tier_a`.

Tier B — sandboxed-write (autoresearch evolver).
    Mechanism: lane-scoped filesystem writes inside a sandboxed runtime
    directory; honor-system "Hard Rules" in agent prompts; no git mutation.
    Threat: a workflow-lane agent edits files owned by a different lane and
    contaminates shared state across the evolution loop. The lane-ownership
    check filters every read/write at sync time so cross-lane contamination
    cannot land. Primitives live in :mod:`src.shared.safety.tier_b`.

Tier C — repo-write + post-hoc verification (harness fixer).
    Mechanism: scope-allowlist regex per track + post-fix scope check + leak
    check + rollback. The fixer must Write code; capability restriction is
    impossible because the job is mutation. Threat: a fixer touches files
    outside its assigned track or leaks edits into the main repo from the
    worktree. Post-hoc checks gate every commit; rollback restores the tree
    when scope is breached. Primitives live in :mod:`src.shared.safety.tier_c`.

The ``SafetyTier`` Literal and ``SAFETY_TIER`` per-pipeline constants are
deliberately omitted. Nothing in any pipeline dispatches on tier; adding the
type alias and constants would be naming ceremony with no caller. Re-introduce
when (and only when) a real dispatcher needs them.
"""
