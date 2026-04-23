# Automated Rollback (Plan B Phase 6 Step 6 — deferred)

**Status:** stub created 2026-04-23 as a target for the MVP carve-out deferral of Plan B Phase 6 Step 6. Do NOT start until the trigger conditions below are met.

## What this plan ships

Agent-driven rollback: after each promotion, score the post-promotion trajectory; if the `rollback_agent` returns `rollback`, revert the lane head to the prior variant via `evolve.sh promote --undo --lane <lane>`.

- `autoresearch/evolve_ops.py::check_and_rollback_regressions` (~40 lines)
- `autoresearch/evolve_ops.py::record_head_score` (~10 lines)
- `kind="head_score"` event in the unified events log
- Cooldown (3 post-promotion cycles between rollbacks) + dry-run-mode window tuning
- `tests/autoresearch/test_rollback_rule.py` (~8 tests)

## Why it was deferred

Three reasons from the 2026-04-23 multi-persona review:

1. **Untuned prompt.** The plan itself admits the rollback prompt is not tuned against observed bad-promotion data at MVP ("expect to refine the prompt after the first 1-2 observed rollbacks").
2. **Calendar-gated write access is not an audit-gated safety rail.** The original plan had `ROLLBACK_DRY_RUN_UNTIL_ISO = "2026-05-15T00:00:00Z"` — write access turns on regardless of whether any dry-run decisions were audited. Clock-skew sensitive, too.
3. **Compound-risk chain.** Review identified: judge-unreachable → silent reject in `is_promotable` → no post-promotion `head_score` events → cooldown counted in head_score events → rollback silently disabled during judge outages. Two individually-survivable faults combine.

## Trigger conditions — when to start this plan

Start when ALL three are true:

1. **MVP has produced real post-promotion trajectories.** At least 3–5 promotions have fired on the geo lane via the MVP `is_promotable`, with their `kind="promotion_decision"` records + candidate vs baseline score summaries in `events.jsonl`.
2. **At least 1 observed regression.** One of those promotions was wrong in hindsight (holdout score regressed over the subsequent cycles), so the rollback prompt has real data to be tuned against.
3. **Judge service uptime ≥ 99% over the last month** (or the compound-risk chain has a separate mitigation — e.g., a circuit breaker in `is_promotable` that HALTs the outer loop on N consecutive `judge_unreachable` events, rather than silently rejecting).

## What to copy from the deferred Plan B material

`docs/plans/2026-04-21-003-feat-fixture-program-execution-plan.md` Phase 6 Step 6 contains the full spec (code block + rationale). Read that section; then re-evaluate against the trigger conditions before copying verbatim — the review noted several issues that need to be fixed in flight:

- Change cooldown to measure wall-clock, not post-promotion `head_score` events (to break the compound-risk chain).
- Replace the hardcoded `ROLLBACK_DRY_RUN_UNTIL_ISO` with an audit-evidence gate (N dry-run decisions reviewed, signed off in a commit).
- Add `prompt_version` to `PromotionVerdict` so the autoresearch audit log can correlate rollback verdicts against the judge-side prompt version.
- Consider a rollback-on-rollback guard (what if the rollback decision agent itself abstains?).

## Acceptance

- One full observed rollback cycle: bad promotion → rollback_agent returns `rollback` → `evolve.sh promote --undo` runs → next cycle's proposer sees the restored head → lineage + events log both record the rollback chain cleanly.
- No silent "pipeline stuck at 0 promotions" regime during judge outages (test this by killing the judge service mid-cycle and asserting the outer loop HALTs, not silently-idles).
