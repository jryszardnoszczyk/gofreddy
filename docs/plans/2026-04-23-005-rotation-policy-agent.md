# Rotation Policy Agent (Plan B Phase 2 Step 0b)

**STATUS: SHIPPED 2026-04-23** as `docs/agent-tasks/rotation-policy.md` task spec. Operator invokes monthly via `claude --print --input-file docs/agent-tasks/rotation-policy.md ...`. Agent's output is only useful with ≥3 months of `saturation_cycle` data; the spec explicitly says to exit 1 on insufficient data.

---

**Original scope was:** stub for MVP carve-out deferral. The caveats below are still accurate operational guidance.

## What this plan ships

Monthly operator-dispatched agent task (`docs/agent-tasks/rotation-policy.md`) that:

1. Reads per-fixture saturation history from `events.jsonl` (`kind="saturation_cycle"`).
2. Reads per-fixture discriminability verdicts from prior `freddy fixture discriminate` runs.
3. Reads the current anchor/rotating partition from the manifest.
4. POSTs to `/invoke/system_health/saturation` with `mode=rotation_proposal`.
5. Emits a diff proposal to `docs/plans/rotation-policy-log.md`.
6. Operator reviews + commits the new partition (manual).

## Why deferred (per 2026-04-23 review)

The plan itself admits: *"the agent's output is only useful when ≥3 months of saturation events have accumulated. Before that, the initial Phase 1 taxonomy partition is authoritative — skip monthly runs for the first 90 days post-MVP."*

That's a 90-day no-op on ship. Building it before the data exists is premature framework-ahead-of-need.

## What's already shipped toward this

- The static Phase 1 taxonomy partition (`docs/plans/fixture-taxonomy-matrix.md`) names all anchor/rotating assignments.
- `autoresearch/judges/quality_judge.py::call_quality_judge` already supports `role="saturation"` — the `mode=rotation_proposal` branch is a judge-service prompt extension, not autoresearch-side code.

## Trigger conditions — when to start

1. **≥90 days have passed since Plan B MVP shipped** (so saturation events have accumulated).
2. **At least one domain's rotation set has shown a stable saturation pattern** — that is, specific fixtures consistently saturate while others retain discrimination. Without this, there's no signal for the agent to reason about.

## What to copy from the deferred Plan B material

`docs/plans/2026-04-21-003-feat-fixture-program-execution-plan.md` Phase 2 Step 0b final paragraph + the embedded `docs/agent-tasks/rotation-policy.md` spec. Copy after resolving:

- Define exactly how the agent's proposed diff is reviewed: diff format, reviewer approval flow, what triggers auto-commit vs hand-edit.
- Decide whether the rotation happens in holdout-v1 (requires operator to manually edit the out-of-repo manifest) or a pool-scoped partition file.

## Acceptance

- One full monthly cycle: agent runs → proposal diff lands in `rotation-policy-log.md` → operator reviews and commits → holdout-v1 partition updated → next saturation cycle reads the new partition.
- False-positive rotation proposal rate: the agent proposes "no change" when observed data genuinely warrants no change (measured by stable saturation patterns across 2–3 consecutive runs).
