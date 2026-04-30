# Marketing audit engine v1 — /ce:work execution handoff

> **⚠ STATUS — SUPERSEDED 2026-04-30.**
>
> This handoff dispatches against `2026-04-24-005-marketing-audit-v3-fusion-roadmap.md`,
> which has been deferred to v3 per LHR pressure-test review. **Do not
> launch this handoff.** The authoritative v1 plan is now
> `docs/plans/2026-04-30-001-marketing-audit-v1-pipeline-plan.md`; a new
> handoff against that plan will be drafted before any implementation.
>
> Phase 1 implementation done by an earlier agent under this handoff has
> been reset (HEAD `619d716`); recoverable via tag `phase-1-foundation-snapshot`
> if useful for cherry-pick during v1 implementation. Conformance work
> is preserved at `plan-conformance-only` tag.

**Created:** 2026-04-29
**Target:** implementation agent in fresh Claude Code session, opened inside a worktree
**Plan:** `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md` (1,994 lines, 20 units, 6 phases) on branch `origin/plan/audit-engine-fusion-v1` HEAD `3f1698d`
**Registry contract:** `autoresearch/lane_registry.py` (242 LoC) shipped on `main`
**Total estimate:** 7-9 weeks foundation through first paying audit (Phase 1-3); 9-11 weeks including full Bundle E
**Per-session scope (this handoff):** Phase 1 Foundation (Units 1-7, ~2 weeks). Subsequent phases land via fresh sessions or operator hand-off; this prompt sets the work context for the first session and the agent reports back when Phase 1 ships or when it hits the per-session ceiling.

## Worktree setup (do this BEFORE launching the agent)

```bash
# From the main gofreddy repo:
git fetch origin
git worktree add ../gofreddy-audit -b feat/marketing-audit-v1 main
cd ../gofreddy-audit

# Cherry-pick the plan + brainstorm + port-only checklist so the agent has them in-tree:
git cherry-pick 3f1698d  # plan/audit-engine-fusion-v1 HEAD (registry-revised plan)

# Verify:
ls docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md
ls autoresearch/lane_registry.py
git log --oneline -3
```

Then `claude` (or your fresh Claude Code launch command) inside `../gofreddy-audit` and paste everything below the `---` separator as the agent's first message.

---

## ROLE

You are an autonomous implementation agent executing /ce:work on a 1,994-line plan that ships gofreddy's v1 Marketing Audit engine — fused with `autoresearch/` as the 5th workflow lane (alongside geo, competitive, monitoring, storyboard) using multi-session `claude -p` CLI orchestration over a frozen 149-lens content catalog.

You are working in a fresh git worktree at `../gofreddy-audit` on branch `feat/marketing-audit-v1` (off main). You have full access to the plan, the live lane-registry contract, and 4 days of accumulated review/refinement work on the plan. Your job is to execute Phase 1 (Units 1-7) in this session, committing each unit as a separate commit so progress can be bisected. When you hit the per-session context ceiling or finish Phase 1, report back per the structured format and stop.

## CONTEXT — what's been done

The plan went through brainstorm + /ce:plan + auto-mode deepening + 3 document-review passes + 16 corrections + 4 simplification rollbacks + 7-gap cascade-fix audit + 6 layer-3 design specs + 15 integration-correctness fixes + a registry-revision pass against the shipped lane-registry contract. Total ~5 days of refinement before any code. The plan is now genuinely ready.

The lane-registry refactor shipped to main on 2026-04-27 (HEAD `9549500`). It consolidated 14+ enumeration sites across `autoresearch/` and `src/evaluation/` into a single `LaneSpec` registry at `autoresearch/lane_registry.py`. Adding marketing_audit becomes "1 LaneSpec entry + 4 callable wires + 2 substrate edits + 6 supporting creates" instead of the pre-refactor 18-op shape.

## REQUIRED READING (before any code edit)

Read in this order:

1. **The plan itself**: `docs/plans/2026-04-24-005-marketing-audit-v3-fusion-roadmap.md` end-to-end. Pay particular attention to:
   - Overview + Problem Frame + Requirements Trace + Scope Boundaries (lines 12-65) — what's in/out of v1
   - Key Technical Decisions (lines 124-180) — 14 locked architectural choices
   - High-Level Technical Design (lines 216-280) — Mermaid + lane-shape asymmetry framing
   - **All 20 Implementation Units** — your work plan
   - Risks & Dependencies (lines 1324-1380) — what can break
2. **The origin requirements brainstorm**: `docs/brainstorms/2026-04-24-audit-engine-fusion-requirements.md` — 13 locked Key Decisions trace to here
3. **The live registry contract**: `autoresearch/lane_registry.py` end-to-end. The 9 data fields + 5 optional callables + 3 manifest utilities are the contract you slot into.
4. **The registry plan**: `docs/plans/2026-04-27-002-feat-autoresearch-lane-registry-plan.md` §"Known Divergence Points" — the 7 axes future divergent lanes resolve. 5 of 7 are pre-resolved for marketing_audit (see `## LOCKED DIVERGENCE POINT PICKS` below).
5. **The registry architecture doc**: `docs/architecture/lane-registry.md` — field reference + worked example for "Adding a divergent lane" (the marketing_audit illustrative example IS the contract Unit 17 instantiates).
6. **The port-only checklist**: `docs/plans/2026-04-24-002-port-only-extraction-checklist.md` — what's portable from `feat/fixture-infrastructure` branch (14 existing files Unit 1 reconciles).
7. **Existing 4 lanes' programs**: `autoresearch/archive/current_runtime/programs/{geo,competitive,monitoring,storyboard}-session.md` — read at least one in detail (geo) to understand the session.md program shape.

## WHERE TO START — Unit 1 (Branch reconciliation)

**Goal:** Establish the working-branch baseline. Merge or cherry-pick existing audit files from `feat/fixture-infrastructure` (14 files: agent_models.py, checkpointing.py, preflight/runner.py and friends), verify deps, confirm no drift from the plan.

**Verify first:**
```bash
git fetch origin feat/fixture-infrastructure
git log --oneline -5 origin/feat/fixture-infrastructure
git diff main..origin/feat/fixture-infrastructure --stat | head -20
```

The plan's Unit 1 spec describes the expected reconciliation. Execute per the plan; commit when green.

After Unit 1 ships clean, work through Units 2-7 in dependency order per the plan:
- **Unit 2:** state.py + exceptions
- **Unit 3:** claude_subprocess.py with cwd=audit_dir factories (3 patterns: A/B/C)
- **Unit 4:** cost_ledger.py with R29 SLA via duration_api_ms
- **Unit 5:** graceful_stop / resume / cleanup ports from harness
- **Unit 6:** events wrapper + autoresearch/evolve_lock.py + Stage ABC `_load_prompt` (no standalone prompts_loader module)
- **Unit 7:** preflight retrofit

End of Phase 1 = primitives that everything else imports from. No user-visible functionality, but unblocks all subsequent phases. Test suite must pass at end of each unit.

## LOCKED DIVERGENCE POINT PICKS (do not re-derive)

5 of the 7 Known Divergence Points from the registry plan are pre-resolved for marketing_audit. Do not re-litigate these — apply per pick:

| # | Point | Pick | Effect |
|---|---|---|---|
| **#1** | `plateau_threshold` | (c) normalize to [0,1] in `custom_score` via `weighted_rubric_raw / 10.0` | No `select_parent.py:97` substrate edit; threshold stays calibrated |
| **#2** | snapshot-at-clone trigger | (c) `custom_validate` re-runs `verify_manifest` per-variant against baseline `marketing_audit_manifest.json` | No standalone manifest module; no `_check_critique_manifest` extension |
| **#3** | `structural.py:38-46` if-branch | (a) 1-line dispatch entry retained | Async asymmetry of `_validate_monitoring` rules out data-driven dispatch |
| **#6** | `_INNER_PHASE_TAGS` extension | (a) 1-line allowlist edit | Simpler than per-LaneSpec field for single-lane addition |
| **#7** | inner/outer pass-rate telemetry | (b) emit from `custom_score` output | Substrate aggregator at `evaluate_variant.py:1180-1202` (`mean_inner_pass_rate / mean_outer_pass_rate / mean_pass_rate_delta`) is bypassed (custom_score replaces `_score_variant_search` wholesale); marketing_audit must independently emit these keys into `search_metrics` so downstream consumers (eval_digest, drift telemetry) see non-null values |

**#4 (HARNESS_PREFIXES carve-out) and #5 (holdout_suite_id env var)** are NOT marketing_audit's concerns — they belong to the harness_fixer plan downstream.

## LOCKED LANESPEC SHAPE (Unit 17 wiring)

When Unit 17 lands (Phase 5), the LaneSpec entry is:

```python
LANES["marketing_audit"] = LaneSpec(
    name="marketing_audit",
    is_workflow_lane=True,
    rubric_ids=("MA-1", "MA-2", "MA-3", "MA-4", "MA-5", "MA-6", "MA-7", "MA-8"),
    path_prefixes=(
        "marketing_audit-findings.md",
        "programs/marketing_audit-session.md",
        "programs/marketing_audit/prompts/",
        "templates/marketing_audit",
        "workflows/marketing_audit.py",
        "workflows/session_eval_marketing_audit.py",
    ),
    session_md_filename="marketing_audit-session.md",
    deliverables=("findings.md", "report.md", "report.json", "report.html", "report.pdf"),
    intermediate_artifacts=("stage2_subsignals/L*_*.json",),
    structural_doc_facts=(...),       # auto-derived to STRUCTURAL_DOC_FACTS["marketing_audit"]
    structural_gate_functions=(...),  # auto-derived to STRUCTURAL_GATE_FUNCTIONS["marketing_audit"]
    custom_score=src.audit.score.marketing_audit_score,
    custom_validate=src.audit.validate.marketing_audit_validate,
    custom_promote=src.audit.promote.marketing_audit_promote,
    custom_objective_score_from_entry=src.audit.score.marketing_audit_objective_score,
    # custom_mutate=None  → uses default meta-agent
)
```

**4 of 5 callables wired; custom_mutate stays None.** The callables live in `src/audit/{score,validate,promote}.py` (Units 16 + 18 own those files). Unit 17 also adds: 1-line `structural.py` dispatch, `_INNER_PHASE_TAGS` extension, RUBRICS assertion bump (`== 32` → `== 40`), 6 supporting creates, tests.

## LOCKED FITNESS FUNCTION

```python
# Variant-time (custom_score):
weighted_rubric_raw = (
    0.15 * MA_1_score + 0.20 * MA_2_score + 0.10 * MA_3_score
  + 0.10 * (MA_4_raw * 2)  # MA-4 raw 0-5, ×2 → normalized 0-10
  + 0.10 * MA_5_score + 0.10 * MA_6_score
  + 0.15 * MA_7_score + 0.10 * MA_8_score
)  # max = 10.0
normalized = weighted_rubric_raw / 10.0  # → [0, 1]
variant_score = (
    normalized
  − cost_penalty * max(0, normalized_token_cost − 1.0)   # cost_penalty = 0.0 in v1
  − latency_penalty * normalized_wall_clock              # latency_penalty = 0.0 in v1
)

# Selection-time (custom_objective_score_from_entry):
ENGAGEMENT_TARGET_USD = 5000
def engagement_weight(generation, audits_aged_past_60d):
    if generation < 3 or audits_aged_past_60d < 6: return 0.0
    gen_ramp = min(1.0, (generation - 3) / 3)
    audit_ramp = min(1.0, (audits_aged_past_60d - 6) / 14)
    return 0.05 * gen_ramp * audit_ramp  # max contribution = 0.05 in [0,1] space

normalized_engagement = min(1.0, mean_signed_usd / ENGAGEMENT_TARGET_USD)
final_score = variant_score + engagement_weight × normalized_engagement
```

**Engagement weight max scaled from `0.5` (in pre-refactor [0,10] space) to `0.05` (in [0,1] space)** — preserves the relative contribution exactly. Do not change.

## CONSTRAINTS — DO

- **Read the plan end-to-end before writing any code.** The plan is the contract.
- **One commit per Unit.** Each unit's tests must pass before committing.
- **TDD where the plan says "test-first":** Unit 3's `parse_result_message`, Unit 10's `subsignals.parse`, Unit 16's fitness math, Unit 18's pre-promotion smoke-test. Plan calls these out explicitly.
- **Cascade-grep after any rename/relocation.** After modifying a constant or moving a module, grep the entire repo for residual references.
- **Trust locked decisions.** The plan went through 3 review passes + a registry-revision; the design is settled. Don't redesign mid-execution.
- **Honor scope boundaries.** Plan §Scope Boundaries enumerates what v1 does NOT ship (no Stripe webhook, no Fireflies, no Slack, no web UI, no auto-fire paid pipeline, etc.). Stay inside the boundary.
- **Match the existing `WorkflowSpec` + `SessionEvalSpec` registries** at `autoresearch/archive/current_runtime/workflows/specs.py` + `session_eval_registry.py`. Add marketing_audit's entries there alongside the new `LaneSpec` (Unit 17) so all three registries stay aligned.

## CONSTRAINTS — DO NOT

- **Do NOT re-derive the 5 Divergence Point picks.** They are locked above. If you find a reason to revisit, hard-stop and escalate.
- **Do NOT add new LaneSpec fields.** The 9 data fields + 5 callables cover marketing_audit's divergence axes; if you find a 6th axis, hard-stop.
- **Do NOT modify `autoresearch/lane_registry.py` core (LaneSpec dataclass, accessors, manifest utilities).** Marketing_audit's role is to ADD a LANES entry, not change the contract.
- **Do NOT touch the existing 4 lanes' implementations** (geo/competitive/monitoring/storyboard workflows + evaluators). Use as templates, don't refactor.
- **Do NOT skip git hooks** (`--no-verify`). Fix underlying issues; if a pre-commit hook fails legitimately, escalate.
- **Do NOT add the `marketing_audit` entry to `LANES` until Unit 17.** Earlier units build the supporting code (state, subprocess factories, stages, render, CLI). The lane registration is the LAST mechanical step; doing it earlier breaks the test suite (LaneSpec construction would fail because the callable imports don't yet exist).
- **Do NOT ship content yourself.** The plan defers ~50-100h of v1-critical content authoring (8 stage prompts, 8 MA-N rubric prompts, pricing anchors yaml, 10-20 lens YAML subset) to JR-coordinated work. Stub these as placeholder files; flag in your report-back.

## HARD-STOP CONDITIONS — escalate with structured report

Stop and report (per `## REPORT BACK FORMAT`) without continuing if:

1. **A locked decision needs reconsidering.** E.g., you find concrete evidence that pick #1's score normalization breaks something the plan didn't anticipate. JR makes the override call, not the agent.
2. **`feat/fixture-infrastructure` branch is missing or has drifted.** Unit 1 depends on those 14 files; if the predecessor branch's contents don't match the plan's expectations, escalate.
3. **The plan references a file or constant that doesn't exist on main.** May indicate plan drift since 2026-04-29.
4. **Test suite is broken on main BEFORE your first edit.** Take a baseline snapshot first (`pytest --tb=no -q > /tmp/baseline.txt`); if failures, escalate.
5. **A LaneSpec field needs adding to support marketing_audit.** Per `## CONSTRAINTS — DO NOT`.
6. **Per-session context ceiling reached.** Don't push through with degrading judgment. Stop, report, let next session resume.

## REPORT BACK FORMAT

When Phase 1 ships clean OR you hit a hard-stop OR per-session ceiling, write your final message in this shape:

```markdown
## Marketing audit engine — Phase 1 progress report

### Status
[Phase 1 complete | Phase 1 partial: Unit N reached | hard-stop at <reason>]

### Units completed (commit SHA per unit)
- Unit 1: <sha> — Branch reconciliation
- Unit 2: <sha> — state.py + exceptions
- Unit 3: <sha> — claude_subprocess.py
- ... (continue per progress)

### Units NOT completed + reason
[list, with blocker per unit if any]

### Test results
[pasted output of final `pytest` run; NOT summarized]

### Cascade-grep results
[for any constants moved/renamed, the grep output showing zero stale references]

### Deviations from plan + reasoning
[list each, with rationale]

### Hard stops encountered (if any)
[for each: unit, what blocked, what you tried, what JR needs to decide]

### Next session entry point
- Resume on branch `feat/marketing-audit-v1` (worktree `../gofreddy-audit`)
- Next unit: Unit N
- JR-side content authoring blocking next phase: [list]
- Any specific notes for the next agent reading this report

### Plan-update follow-up needed
[items that warrant editing the plan post-execution]
```

## EFFORT ESTIMATE (per-session)

A single autonomous session in this worktree should realistically ship **~3-5 units of Phase 1** (~3-5 days wall-clock equivalent of work compressed into the session's context window). Phase 1 has 7 units total, so 1-2 sessions to complete Phase 1. Subsequent phases:

- **Phase 1 (Foundation, Units 1-7):** ~2 weeks
- **Phase 2 (Stages 0-4, Units 8-11):** ~2 weeks
- **Phase 3 (Deliverable + CLI, Units 12-14):** ~1-2 weeks
- **Phase 4 (Evaluation, Units 15-16):** ~1 week
- **Phase 5 (LaneSpec registration + safety rails, Units 17-19):** ~1 week
- **Phase 6 (v1 ship, Unit 20):** ~2-3 days

Total: 7-9 weeks foundation through first paying audit; 9-11 weeks including full Bundle E.

## WORKING APPROACH

1. **Baseline test snapshot:** `pytest --tb=no -q > /tmp/baseline.txt 2>&1`. If failures, escalate.
2. **Read the plan + registry contract + architecture doc.** Take notes on Unit 1 expectations, then the dependency chain through Unit 7.
3. **Verify `feat/fixture-infrastructure` branch state.** What 14 files exist there? Do they match the plan's expectations?
4. **Execute Unit 1.** Tests + commit.
5. **Execute Units 2-7 in dependency order.** One commit per unit.
6. **Run cascade-grep after any constant rename or module relocation.**
7. **Report back per format above.**

## WHAT'S NEXT AFTER PHASE 1

Phase 2 (Stages 0-4) needs JR-coordinated content authoring before Unit 10 (Stage 2) can be tested:
- 10-20 lens YAML subset (`configs/audit/lenses.yaml`) — unblocks Stage-2 dev; full 149-lens catalog gates Bundle E
- Stage prompts (8 files: `stage_0_intake.md` through `stage_4_proposal.md` + `inner_loop_critic.md` + `stage_1a_preflight.md`) — ~32-64h JR-coordinated
- Pricing anchors yaml (`configs/audit/pricing_anchors.yaml`) — Stage 4 fails with `MissingPricingAnchors` without it

Phase 4 (Evaluation) needs:
- 8 MA-N rubric prompts (`_MA_1` through `_MA_8` in `src/evaluation/rubrics.py`) — ~16-32h JR-coordinated content authoring matching `_GEO_1..._GEO_8` quality bar

Phase 5 (LaneSpec registration) requires Units 16 + 18's callables to exist. Unit 17 is the LAST mechanical step.

Document content-authoring blockers in your final report so JR knows what to start on while waiting for engineering.

End of prompt.
