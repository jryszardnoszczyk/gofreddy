---
title: Harness — fixer self-verify (drop AI verifier) + evaluator prompt rebalance
type: refactor
status: active
date: 2026-04-29
---

# Harness — fixer self-verify (drop AI verifier) + evaluator prompt rebalance

## Overview

Two related harness improvements confirmed after PR #37 (`run-20260428-105643`) showed both architectural and discovery-quality issues:

- **Drop the AI verifier loop.** The verifier costs ~50min/cycle wallclock + ~$50/run in tokens, catches ~3 real partial-fix issues per cycle, and misses what code-review catches anyway. The fixer already has full knowledge of what the verifier checks (see `harness/prompts/fixer.md` "Anticipate the verifier" — lines 107-118 enumerate 6 probes). Move probe execution into the fixer's own session, in-process, before commit. Keep `surface_check` as the deterministic post-commit gate.
- **Rebalance the evaluator prompt** away from static-reading bias. PR #37 was ~25% real-debugging + ~75% sibling-symmetry/static-reading. The five categories (crash, 5xx, console-error, self-inconsistency, dead-reference) structurally favor categories 4-5 because they're cheap to find by reading code; categories 1-3 require running things and observing failure. Reframe so debugging-driven findings dominate.

## Problem Frame

**The verifier-loop architecture is wasteful.** The current flow:
1. Fixer commits a fix on a worker branch.
2. Cherry-pick onto staging.
3. Separate verifier session (Opus, ~5min) runs 6 probes against staging.
4. Verdict YAML written; revert if failed.

The fixer prompt **already tells the fixer to think through these 6 probes before stopping** (lines 107-118 of `harness/prompts/fixer.md`). The fixer is not currently required to *execute* them — only to "anticipate." Empirically, the fixer often handles probes 1, 5 (defect gone, surface preserved) and the verifier catches partial scope on probes 2-4, 6. But the verifier also misses real architectural issues (per PR #37 review: F-a-9-3 live-probe regression, F-b-8-13 service-bypass + race) that only an external code reviewer catches. The verifier sits at a bad point in the cost/value curve: more expensive than a static check, less rigorous than a code review.

**The evaluator prompt biases toward what's cheap.** When a category is easy to find by reading code (sibling-symmetry, dead-references), the agent gravitates there because that's the lower-effort path within the time budget. The evaluator's categorical structure (5 equally-weighted defect types, no quota) makes this a structural feature rather than a bug.

## Requirements Trace

- **R1.** Fixer-self-verify replaces `_verify_phase` + `engine.verify`. The fixer runs the 6 probes from `fixer.md` lines 107-118 and writes a verdict YAML before committing.
- **R2.** Resume + revert logic stays unchanged at the orchestration layer — verdict YAMLs at the same `verdicts/<track>/<id>.yaml` path with the same `Verdict` schema continue working.
- **R3.** `surface_check` (deterministic, microseconds) stays. `_revert_phase` stays for surface_check failures and fixer-reported failures.
- **R4.** The evaluator prompt produces ≥60% findings in categories 1-3 (crash, 5xx, console-error) over a typical run. Measured by classifying findings post-run, not enforced by hard quota inside the agent.
- **R5.** No `ce:review` agent in the loop. No new evaluator categories. No scope creep into other open harness issues (sleep-detection false-positives, stash-list growth, NO-OP filter bug — those are separate follow-ups per memory `project-harness-improvement-direction.md`).
- **R6.** Smoke-runnable: a small fixture or single-finding test must demonstrate the new flow end-to-end before the next full harness run.

## Scope Boundaries

**In scope:**
- `harness/run.py` — drop `_verify_phase`, `_verify_one`, `_verify_backend_parallel`; thin `_revert_phase` to surface_check + fixer-fail revert; remove verify-phase calls from `_cycle_loop` and `_fixers_only_pass`.
- `harness/engine.py` — drop `engine.verify` function; keep `Verdict` dataclass + `parse()` (read by `_revert_phase`).
- `harness/prompts/fixer.md` — replace "Anticipate the verifier" section with "Self-verify before stopping" that mandates writing a verdict YAML.
- `harness/prompts/evaluator-base.md` — reframe category prioritization toward debugging.
- `harness/prompts/verifier.md` — delete (no longer invoked).
- `tests/harness/test_run.py` — drop the 8 parallel-verify tests + their helpers; add new tests for the thin revert path.

**Out of scope (explicit):**
- Sleep-detection false-positives during long verify phases (PR #29 walltime improvement). Already a known gap; separate follow-up.
- Stash-list growth across cycles. Separate follow-up.
- F-c-6-1 NO-OP filter miss in `pr-body.md` generation. Separate follow-up.
- Adding a `ce:review` step to the loop. Explicitly rejected.
- Changing the 5 evaluator categories themselves (only their framing).
- Track-specific evaluator overrides (track-c is already Playwright-driven). Will reassess if the rebalance under-corrects after the smoke run.

## Context & Research

### Relevant Code and Patterns

- `harness/run.py:770-892` — current `_verify_phase` (~120 lines) + `_verify_one` + `_verify_backend_parallel`.
- `harness/run.py:894-1000` — current `_revert_phase`. Currently reverts on (a) surface_check fail (verdict YAML pre-written by `_verify_phase`) and (b) AI verifier fail. After this change: only (a) and (c) fixer-reported fail.
- `harness/run.py:551-643` (`_cycle_loop`), `harness/run.py:645-702` (`_fixers_only_pass`) — call `_verify_phase` after fix-phase drains. Both call sites need `_verify_phase` removed.
- `harness/engine.py:108-180` — `Verdict` dataclass + `parse()`. Keep `parse()`; `_revert_phase` reads verdicts via this.
- `harness/engine.py:195-225` — `engine.verify()`. Delete entirely.
- `harness/prompts.py:50-69` — `render_fixer()`. The fixer prompt template gets the `{prior_reverts}` field; we'll add a `{verdict_path}` field so the fixer knows where to write its self-verdict.
- `harness/prompts/fixer.md:107-118` — "Anticipate the verifier" section already enumerates the 6 probes. Replace with "Self-verify before stopping" that requires the fixer to write a YAML verdict file.
- `harness/safety.py` — `surface_check()` is unchanged. It runs in `_verify_phase` today; needs to move to `_process_finding` post-fixer (call site reorg, no logic change).
- `tests/harness/test_run.py:633-921` — the 8 parallel-verify tests added in commit `7449b58`. All deleted.

### Institutional Learnings

- `feedback-harness-evaluator-bias-and-verifier-roi.md`: PR #37 surfaced both issues. ~10/39 fixes from real debugging vs ~15 sibling-symmetry vs ~14 hybrid.
- `project-harness-improvement-direction.md`: JR confirmed direction 2026-04-29 — fixer-self-verify, surface_check stays, no ce:review, evaluator rebalance toward debugging.
- `feedback-merge-only-after-explicit-review-go.md`: PR #25 had 5 P0 bugs after merge despite verifier approving. Reinforces that the AI verifier is not the rigorous safety net it was sold as. Strengthens the case for replacing it.
- `feedback-trust-agent-drop-regex-guards.md`: Don't propose brittle regex/allowlist containment when prompt + architecture already keep agents in lane. Applies here: surface_check (deterministic git diff) is the right kind of guard; AI verifier was the brittle one.

### External References

None — this is a harness-internal architectural change.

## Key Technical Decisions

**D1. The fixer self-verifies in its own session, not a separate subprocess.**
- *Rationale*: The fixer already has the worktree state, the diff, the finding context, and the reproduction. Spawning a fresh subprocess to re-verify duplicates 30k+ tokens of preamble + re-discovery of context. Self-verify is ~1-2k extra tokens at the end of an existing session.
- *Trade-off*: Confirmation bias — the fixer designed its repro and may rationalize that the fix passes. Mitigated by the 6-probe protocol that explicitly forces the fixer to vary inputs (probe 2), exercise siblings (probe 3), test adversarial state (probe 4), check symmetric surfaces (probe 6). The protocol is what catches confirmation bias, not session separation.

**D2. Fixer writes the same `verdicts/<track>/<id>.yaml` file the AI verifier wrote.**
- *Rationale*: Resume logic, `_revert_phase`, `pr-body.md` generation all read this path. Keeping the schema means the orchestration layer is unchanged.
- *Trade-off*: None meaningful. The schema (`verdict: passed|failed`, `reason`, `adjacent_checked`) maps cleanly to what the fixer can produce.

**D3. Verdict YAML write is the LAST action of the fixer session, after the commit.**
- *Rationale*: We want the fixer's self-verdict to reflect the actual committed state, not in-flight work that might still be reverted. The fixer commits, writes the verdict YAML, then exits.
- *Trade-off*: If the fixer crashes between commit and verdict-write, resume sees a commit with no verdict and re-dispatches the fixer. The fixer's commit-skip logic (already at `harness/run.py:1167`) detects the existing commit and skips re-fixing; the verdict-write is the only thing that re-runs. Acceptable.

**D4. Surface_check moves from `_verify_phase` to `_process_finding`, runs immediately after fixer commit.**
- *Rationale*: Surface_check is microseconds and deterministic. Running it inline during fix-phase means scope-creep deletes are caught BEFORE cherry-pick onto staging — saving the cherry-pick + revert round-trip.
- *Trade-off*: Slight reordering of `_process_finding`. No risk to other callers since it's a leaf operation.

**D5. Evaluator rebalance is prose reframing, not hard quotas.**
- *Rationale*: Hard quotas inside an agent prompt produce gaming behavior (the agent contrives "crash" findings to hit the threshold). Prose reframing changes the agent's prioritization without forcing a numerical lie.
- *Trade-off*: Less measurable up-front. Mitigated by post-run classification — we measure category 1-3 ratio after each run and tune the prose if it's not hitting ~60%.

**D6. Specific reframing: lead with "what fails when a user actually runs the app", reorder categories, and add a downgrade rule.**
- The five categories stay the same.
- Reorder presentation: 1. crash, 2. 5xx, 3. console-error (top of list); 4. self-inconsistency, 5. dead-reference (still listed, lower priority).
- Add: "Before reporting a self-inconsistency or dead-reference, ask: would a user notice this in the next 5 minutes of using the app? If no, downgrade to doc-drift or low-confidence."
- Add: "Spend at least half your time-budget exercising flows (running CLI commands, hitting endpoints, loading frontend pages) before code-reading. Findings from running > findings from reading."

**D7. No track-specific tuning in v1.**
- *Rationale*: Track-c (frontend) is already Playwright-driven and naturally debug-heavy. Track-b (API) is the worst offender for static-reading bias, but the base prompt change applies to all tracks. If post-run measurement shows track-b under-corrected, we'll add a track-b override in a follow-up.
- *Trade-off*: One more variable in the smoke-run measurement.

**D8. Smoke test uses a 1-cycle, 1-track, 1-finding harness invocation.**
- *Rationale*: The full harness flow (cycle 1 → eval → fix → commit → surface_check → verdict) needs to work end-to-end. A 1-finding smoke proves the orchestration without burning a 5h Anthropic bucket. Existing smoke infra (`harness/smoke.py`, `harness/SMOKE.md`) supports this.
- *Trade-off*: A 1-finding run can't validate the rebalance (need many findings to measure category ratio). The rebalance gets a separate measurement: run a fresh harness post-merge and classify findings.

## Open Questions

### Resolved During Planning

**Q1. What does the fixer verify?** → Resolved (D1, D2): the existing 6-probe protocol from `fixer.md` lines 107-118. Fixer writes a `Verdict`-schema YAML.

**Q2. Where does this sit in the fixer's flow?** → Resolved (D3): final step of the fixer session, after commit, before exit.

**Q3. How does failure report?** → Resolved (D2): same `verdicts/<track>/<id>.yaml` path + same Verdict schema. `_revert_phase` reads the same way.

**Q4. Behavior when fixer says "I verified my fix" — trust + commit, or static check?** → Resolved (D4): trust the fixer's verdict; surface_check is the additional deterministic gate that runs whether the fixer says pass or fail. No `pytest -x` in the loop.

**Q5. Hard quota or soft prioritization?** → Resolved (D5): soft prioritization in prose. Measure post-run.

**Q6. Reframe categories themselves or just framing?** → Resolved (D6): keep the 5 categories, reorder + add downgrade rule + add running-vs-reading rule.

**Q7. Track-specific tuning?** → Resolved (D7): no v1; reassess after smoke.

**Q8. What does the fixer do if its self-verify fails?** → It commits anyway, writes a `verdict: failed` YAML, and exits. `_revert_phase` will then revert that commit. Same outcome as today's "verifier rejected" path.

### Deferred to Implementation

**DI1. Exact test file refactor** — `tests/harness/test_run.py` has 8 parallel-verify tests that get deleted. The replacement tests (revert-on-surface-fail, revert-on-fixer-fail) need actual fixture work. Plan specifies what scenarios to cover; implementation specifies how to fixture them.

**DI2. Whether the fixer needs a new `{verdict_path}` template variable in `prompts.py`** — likely yes, since the fixer needs to know where to write. Resolves at implementation when editing `render_fixer()`.

**DI3. How to migrate in-flight runs** — does an existing graceful-stopped run resume cleanly with the new code? Likely yes (resume reads verdict YAMLs from disk; new code reads the same shape). Smoke this on resume of a tiny test run before assuming.

**DI4. Whether `engine.Verdict.parse()` needs any change** — possibly relax the `_FAILED_TOKENS` list since the fixer is more likely to write `failed` than the AI verifier's synonyms (`rejected`, `blocked`). Inspect at implementation.

## Implementation Units

- [ ] **Unit 1: Move surface_check inline into fix-phase**

**Goal:** Run `surface_check` immediately after the fixer commits, so scope-creep deletes are caught before cherry-pick onto staging — and so this gate exists independently of the verify-phase that's about to be deleted.

**Requirements:** R3, R6

**Dependencies:** None — surface_check exists; this is a call-site move.

**Files:**
- Modify: `harness/run.py` (`_process_finding` near commit step, ~30 lines)
- Test: `tests/harness/test_run.py` (new test for inline surface_check)

**Approach:**
- After fixer commits its fix on the worker branch (current `_commit_fix` at `harness/run.py:1583`), call `safety.surface_check(worker_wt.path, f"{commit_sha}^", commit_sha)`.
- If violations: write `verdict: failed` YAML to `verdicts/<track>/<id>.yaml` with `surface_changes_detected: True` (same shape `_verify_phase` writes today). Skip the cherry-pick onto staging for this finding. Log warning.
- If clean: proceed to cherry-pick (existing path).
- This change is INDEPENDENT of removing `_verify_phase` — surface_check still runs in `_verify_phase` today, this just moves it earlier so verify-phase removal doesn't lose the gate.
- IMPORTANT: keep `_verify_phase`'s surface_check call for now (Unit 1 doesn't delete it). Unit 2 deletes the surrounding verify-phase code.

**Patterns to follow:**
- Existing `_commit_fix` flow at `harness/run.py:1583` — surface_check fits between commit and cherry-pick.

**Test scenarios:**
- Happy path: fixer makes a normal change → surface_check passes → cherry-pick proceeds → verdict YAML NOT written by Unit 1 (left for fixer self-verify in Unit 3).
- Error path: fixer removes an exported symbol → surface_check fails → verdict YAML written with `verdict: failed, surface_changes_detected: True` → cherry-pick skipped → finding logged as scope violation.
- Edge case: surface_check raises (transient git failure) → log warning, treat as no violations (current `_verify_phase` does this at `harness/run.py:833-835`), proceed.

**Verification:**
- Existing 8 parallel-verify tests still pass (unchanged in this unit).
- New test: scope-creep delete on a fixture worker branch → verdict YAML at expected path with expected fields → cherry-pick was not attempted.

---

- [ ] **Unit 2: Drop `_verify_phase` + `engine.verify` + parallel-verify infrastructure**

**Goal:** Remove the AI verifier loop entirely. Verdict YAMLs are now written by Unit 1 (surface_check fail) or Unit 3 (fixer self-verify). `_revert_phase` continues reading those YAMLs unchanged.

**Requirements:** R1, R2, R3

**Dependencies:** Unit 1 (surface_check must already run in fix-phase before verify-phase is deleted).

**Files:**
- Modify: `harness/run.py` — delete `_verify_phase` (lines 770-892, ~120 lines), `_verify_one` (~50 lines), `_verify_backend_parallel` (~75 lines). Remove call sites at `_cycle_loop` (line 619) and `_fixers_only_pass` (line 698). Net deletion ~270 lines.
- Modify: `harness/engine.py` — delete `engine.verify()` function (lines 195-225, ~30 lines). Keep `Verdict` dataclass + `parse()` (read by `_revert_phase`). Keep `RateLimitHit` + `EngineExhausted` exceptions (used by fixer flow).
- Delete: `harness/prompts/verifier.md` (~64 lines).
- Modify: `tests/harness/test_run.py` — delete the 8 parallel-verify tests (`test_verify_phase_*`) and their helpers (`_commit`, `_verdict_pass`, `_stub_verify_phase_io`). ~280 lines.

**Approach:**
- Delete in this order: tests first (so test suite still passes after each subsequent deletion), then `_verify_phase` + helpers, then call sites in `_cycle_loop` + `_fixers_only_pass`, then `engine.verify`, then `verifier.md`.
- After deletion, the cycle flow is: evaluate → fix-phase (process_findings_parallel, which now includes inline surface_check from Unit 1) → revert-phase (now only reverts surface_check fails + fixer-fails from Unit 3) → next cycle.

**Patterns to follow:**
- The deletions remove infrastructure I added 24 hours ago in commit `7449b58`. The diff is roughly the inverse of that commit, plus removing the older serial `_verify_phase` it replaced.

**Test scenarios:**
- Test expectation: existing test suite still passes. The 8 parallel-verify tests are deleted (their fixtures and helpers go too); no replacement tests in Unit 2 (Unit 3 adds new ones).
- Specifically verify after deletion: `_cycle_loop` no longer calls `_verify_phase`; `_fixers_only_pass` no longer calls `_verify_phase`; `engine` module exports no longer include `verify`.

**Verification:**
- `python -m pytest tests/harness/ -q` → all remaining tests pass.
- `python -c "from harness import run; assert not hasattr(run, '_verify_phase')"` → confirms deletion.
- `python -c "from harness import engine; assert not hasattr(engine, 'verify')"` → confirms deletion.

---

- [ ] **Unit 3: Fixer self-verify — prompt + verdict-write contract**

**Goal:** The fixer writes a verdict YAML at the end of its session, asserting it ran the 6 probes and reporting outcomes. `_revert_phase` reads this verdict to decide whether to revert.

**Requirements:** R1, R2

**Dependencies:** Unit 2 (verifier loop must be gone first; otherwise we'd write the verdict twice).

**Files:**
- Modify: `harness/prompts/fixer.md` — replace "Anticipate the verifier" section (lines 107-118) with "Self-verify before stopping". Update "When you are done" section. Add `{verdict_path}` template variable usage.
- Modify: `harness/prompts.py` — `render_fixer()` adds `verdict_path` substitution (the path the fixer writes to: `{run_dir}/verdicts/{track}/{id}.yaml`).
- Modify: `harness/run.py` — `_process_finding` reads the fixer-written verdict YAML after the fix subprocess exits. If verdict missing or `failed`, mark for revert (existing `_revert_phase` flow handles this — Unit 2 left it intact). If `passed`, proceed.
- Test: `tests/harness/test_run.py` — new tests for fixer-verdict-passed, fixer-verdict-failed, fixer-verdict-missing.

**Approach:**

The new fixer.md section reads roughly:

> ## [STABLE] Self-verify before stopping
>
> Before exiting, run all six probes below and write a verdict YAML to `{verdict_path}`. The verdict drives whether your commit ships or rolls back. Be honest — a `failed` verdict that gets reverted is cheaper than a `passed` verdict that ships a regression.
>
> 1. **Defect gone** — re-run the reproduction. Pass = the failure is gone.
> 2. **Paraphrase defense** — re-run with a different input than the literal repro string. Pass = the structural fix works, not just the literal test value.
> 3. **Adjacent intact** — exercise 2-3 sibling capabilities (same command group / same router prefix / same component tree). Pass = no neighbor crashes / 5xx / console errors.
> 4. **Adversarial state** — run the repro in a state that SHOULD fail (disabled flag, missing config, expired token, legacy-shape payload). Pass = error envelope is appropriate, not silent success.
> 5. **Surface preserved** — review your diff: no removed exports, no changed function signatures, no renamed CLI flags or endpoint paths unless the finding required it.
> 6. **Symmetric surface** — if you added a guard, validation, or flag-check, grep CRUD/test/history/schedule siblings of the same resource. Pass = sibling has same guard OR you wrote `harness/blocked-<finding_id>.md` documenting why not.
>
> ### Writing the verdict YAML
>
> Write to `{verdict_path}` exactly:
> ```yaml
> verdict: passed   # or failed
> reason: |
>   <one or two sentences. for failed: WHICH probe failed and why.>
> adjacent_checked:
>   - <sibling 1 you exercised>
>   - <sibling 2 you exercised>
> ```
>
> If you cannot run a probe (no Playwright available for a frontend finding, no shell access for a CLI finding), write `verdict: failed` with `reason: blocked-<probe_name>`. Do NOT write `passed` for a probe you skipped.

- `render_fixer()` change: add `verdict_path` to the format dict, computed as `run_dir / "verdicts" / track / f"{finding_id}.yaml"`.
- `_process_finding` change: after fixer subprocess exits, check verdict YAML. Use `engine.Verdict.parse()` (kept from Unit 2). If verdict missing → treat as `failed` with reason "fixer did not write verdict YAML" (`_revert_phase` will revert).
- `_revert_phase` (~`harness/run.py:894-1000`) is unchanged in logic — it still reads `verdicts/<track>/<id>.yaml` and reverts non-passed commits. Unit 2 + Unit 3 just changed who writes the YAML.

**Patterns to follow:**
- Existing `render_fixer` template-variable substitution at `harness/prompts.py:50`.
- Existing `engine.Verdict.parse` at `harness/engine.py:114-150` for read-side.
- Existing `_revert_phase` at `harness/run.py:894`.

**Test scenarios:**
- Happy path: fixer writes `verdict: passed` YAML → `_process_finding` proceeds → cherry-pick onto staging → `_revert_phase` finds passed verdict → no revert.
- Error path: fixer writes `verdict: failed` YAML → cherry-pick still happens (commit lands on staging for audit trail) → `_revert_phase` finds failed verdict → reverts commit.
- Edge case: fixer subprocess exits without writing the verdict YAML → `_process_finding` synthesizes a failed verdict with reason "no verdict file" → revert path same as above.
- Integration: full happy-path on a fixture worker branch — fixer writes verdict, cherry-pick lands, revert-phase finds passed, commit stays on staging.

**Verification:**
- All four scenarios green in test suite.
- Single-finding smoke run (Unit 4) shows verdict YAML exists at expected path with expected schema.

---

- [ ] **Unit 4: Smoke run + measurement**

**Goal:** Validate the new flow end-to-end against a real (small) harness invocation before the next full run.

**Requirements:** R6

**Dependencies:** Units 1-3 complete + tests green.

**Files:**
- No code changes. Operator-side smoke invocation + report.

**Approach:**
- Run a 1-cycle, 1-track harness invocation against a small fixture finding. Use `--max-walltime 1800` (30min cap), `--max-workers 1`, `--engine claude`. Pick track-a as the smoke track since CLI fixes are the simplest.
- Verify: backend up, fixer runs, surface_check runs inline, verdict YAML written by fixer at expected path with expected schema, cherry-pick onto staging happens, revert-phase finds passed verdict and does nothing.
- Run a second 1-cycle smoke with a deliberately broken fix (e.g., remove an exported symbol) → surface_check should write the failed verdict and skip cherry-pick.
- Run a third 1-cycle smoke where the fixer writes `verdict: failed` → cherry-pick happens, revert-phase reverts.
- Document each smoke result in `harness/runs/<smoke-id>/smoke-report.md`.

**Test scenarios:**
- Smoke 1 (happy path): 1 finding → verdict passed → commit on main.
- Smoke 2 (surface_check fail): 1 finding with scope-creep delete → verdict failed → no commit.
- Smoke 3 (fixer-self-fail): 1 finding where fixer writes failed → commit + revert.

**Verification:**
- All 3 smoke scenarios behave as expected.
- Run dir contains expected files.
- Resume from each scenario picks up cleanly (run with `--resume-branch` after killing mid-run).

---

- [ ] **Unit 5: Evaluator prompt rebalance**

**Goal:** Shift the evaluator's prioritization from static-reading-friendly categories (4-5) toward debugging-driven categories (1-3) without changing the categorical structure.

**Requirements:** R4, R5

**Dependencies:** None — independent of Units 1-4.

**Files:**
- Modify: `harness/prompts/evaluator-base.md` (lines 13-23 — "Five defect categories" section; line 27 — "Time budget" section).
- No track-specific overrides in v1 (per D7).

**Approach:**

Edit the "Five defect categories only" section (lines 13-23) to:

1. **Reorder presentation** — keep the 5 categories but lead with categories 1-3:
   - **crash** — process exits non-zero, unhandled exception, UI freezes, hard error
   - **5xx** — backend returns 500/502/503/504 for a request a user would make
   - **console-error** — frontend logs an error during normal flow
   - **self-inconsistency** — two parts disagree (lower priority)
   - **dead-reference** — link/import/route/CLI command points at nothing (lower priority)

2. **Add a downgrade rule** before the "Anything else" line:
   > **Before reporting a self-inconsistency or dead-reference, ask: would a user notice this in the next 5 minutes of using the app? If no, downgrade to doc-drift or low-confidence.** Two endpoints disagreeing on a 200-vs-201 status code probably never reaches a user; one route 404ing the link the homepage shows them does.

3. **Edit the "Time budget" section (line 27)** to add:
   > **Spend at least half your budget exercising flows** — running CLI commands, hitting endpoints, loading frontend pages — before code-reading. Findings from running > findings from reading. A bug you observed firsthand is worth two bugs you inferred from comparing two files.

4. **Add a new short paragraph** between the categories and the time budget:
   > **The categories above are listed in priority order**: crashes and 5xx errors are what break a user's flow today; self-inconsistency and dead-reference are forms of API hygiene that become noticeable later. When you find one of each in your time budget, the crash-class finding is more valuable.

**Patterns to follow:**
- Existing prose style in `evaluator-base.md` — direct, second-person, no bullet-point overload.
- Existing terminology — keep "preservation-first" framing, keep category names exactly.

**Test scenarios:**
- Test expectation: none — this is a prompt-text change. No unit test possible. Validation comes from Unit 6 (post-merge full-run measurement).

**Verification:**
- After Unit 5 ships, the next full harness run (Unit 6) classifies findings post-hoc by category. Target: ≥60% of findings in categories 1-3 (was ~25% in PR #37). If under-target, revisit prose for v2.

---

- [ ] **Unit 6: Post-merge measurement + memory update**

**Goal:** After Units 1-5 ship and a fresh harness run completes, measure category 1-3 ratio + average cycle wallclock to validate the changes worked.

**Requirements:** R4, R6

**Dependencies:** Units 1-5 merged + 1 full harness run completed against the new code.

**Files:**
- No code. Measurement + memory update.
- Update: `feedback-harness-evaluator-bias-and-verifier-roi.md` (memory) — add post-rebalance measurement.

**Approach:**
- After the next full harness run on the new code, classify all findings produced by category. Compute % in cats 1-3 vs cats 4-5.
- Compute average cycle wallclock pre-rebalance (PR #37: ~50min/cycle for verify alone) vs post-rebalance (target: <15min/cycle, no separate verify-phase).
- If category ratio hits ≥60% — declare success, update memory.
- If category ratio is still <50% — file a follow-up plan to either tune track-b prompt (D7) or strengthen the downgrade rule (D6).

**Test scenarios:**
- Test expectation: none — this is post-hoc measurement.

**Verification:**
- Memory updated with measurement.
- Either success declared OR follow-up plan filed.

## System-Wide Impact

- **Interaction graph:** The fixer subprocess now writes one extra YAML file per finding before exiting. The orchestration layer reads it via existing `engine.Verdict.parse()`. No new IPC, no new shared state.
- **Error propagation:** Fixer-written `verdict: failed` flows through the same `_revert_phase` that handled AI-verifier `verdict: failed`. Same error class, same revert mechanism. RateLimitHit / EngineExhausted from the fixer's API calls flow as today.
- **State lifecycle risks:** Verdict YAML is written atomically (Python file write). Resume reads it via existing `engine.Verdict.parse()` which retries once on YAML parse error (`harness/engine.py:124-133`). If a fixer crashes between commit and verdict-write, resume re-dispatches the fixer; the existing commit-skip logic at `harness/run.py:1167` detects the existing commit and skips re-fixing — only the verdict-write gets re-run. Same shape as today's resume-after-mid-verify-crash.
- **API surface parity:** `engine.Verdict` schema unchanged. `_revert_phase` unchanged. `pr-body.md` generation reads verdicts the same way. No external API breaks.
- **Integration coverage:** Unit 4 (smoke run) is the integration coverage. Mocks aren't sufficient because the failure modes (verdict YAML write race, surface_check inline timing, revert-phase reading new schema) are real-environment.
- **Unchanged invariants:** `surface_check` semantics, `_revert_phase` revert mechanics, `Verdict` YAML schema, resume logic at `harness/run.py:182-220`, worker-pool isolation, parallel fix-phase. Only changes: WHO writes the verdict YAML (fixer self-verifies, was AI verifier), and WHEN surface_check runs (inline post-commit, was during separate verify-phase).

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Fixer rationalizes a passed verdict on a broken fix (confirmation bias) | The 6-probe protocol forces input variation, sibling exercise, adversarial state. `surface_check` catches scope-creep deletes regardless of verdict. Post-merge, code reviews on harness PRs catch what the fixer missed (this is what caught PR #37 review-fix issues). |
| Fixer skips probes and writes `passed` anyway | Prompt explicitly says "Be honest — a failed verdict that gets reverted is cheaper than a passed verdict that ships a regression." Mitigation is honesty-by-prompt; no programmatic guard possible. Post-merge measurement catches systemic dishonesty (regression rate goes up). |
| Resume of an in-flight pre-change run breaks | Run a resume smoke before assuming. If broken, resume code can be patched to handle "verdict YAML missing for committed finding" by either re-dispatching fixer OR treating as failed. Probably already handles it (DI3). |
| Rebalance under-corrects (cat 1-3 stays <50%) | Unit 6 measures + files a follow-up if needed. Track-b override is the obvious next lever. |
| Rebalance over-corrects (evaluator misses real self-inconsistency bugs) | Mitigated by keeping all 5 categories — agents can still file them, just at lower priority. PR #37's high-value sibling-symmetry finds (F-b-6-1 cache leak, F-b-7-4 auth-after-validation) would still surface because the bugs are real and noticeable; they just won't dominate. |
| Fixer-written verdicts have different YAML shape variance than verifier's | `engine.Verdict.parse()` already handles synonyms (`_VERIFIED_TOKENS = {"verified", "pass", "passed", "ok", "yes", "true", "confirmed"}`) and unknown tokens (warns + treats as failed). Inherits the existing tolerance. |
| Tests delete + add mid-flow leaves coverage gap | Implementation order (Unit 1 → 2 → 3) keeps surface_check tested throughout; Unit 3's new tests replace Unit 2's deletions. Net coverage stays ≥ pre-change. |

## Documentation / Operational Notes

- Update `harness/INVENTORY.md` if it lists `engine.verify` as a current symbol (verify before merge).
- Update `harness/SMOKE.md` with Unit 4's three smoke scenarios.
- Memory updates after Unit 6: append measurement to `feedback-harness-evaluator-bias-and-verifier-roi.md`. Mark `project-harness-improvement-direction.md` as completed and supersede.
- No external doc updates (harness is internal to this repo).

## Smoke-Test Plan

Per Unit 4, three smoke scenarios on a 1-cycle, 1-track, 1-finding fixture:
1. **Happy path** — verdict passed → commit lands on main → revert-phase no-op
2. **Surface_check fail** — fixer removes an exported symbol → inline surface_check writes failed verdict → cherry-pick skipped
3. **Fixer-self-fail** — fixer writes `verdict: failed` → cherry-pick happens (audit trail) → revert-phase reverts

Plus one resume scenario: kill smoke-1 mid-fix, resume with `--resume-branch`, verify it picks up cleanly with new code.

## Rollback Plan

If smoke runs uncover unrecoverable issues:

1. **Revert the merge commit** on main — single-commit revert via `git revert <merge-sha>` since this lands as one or two PRs (Units 1-4 as one PR, Unit 5 as a second). Restores AI verifier loop.
2. **Drop verdict YAMLs from any in-flight runs** — `find harness/runs -path "*/verdicts/*.yaml" -newer <merge-ts> -delete` clears any partial fixer-written verdicts. Re-run from `--resume-branch`.
3. **No DB migration, no config change, no external dependency** — rollback is git-only.

If only Unit 5 (evaluator rebalance) is the problem, that's a single prompt file revert (`git checkout <pre-merge-sha> -- harness/prompts/evaluator-base.md`).

## Sources & References

- **Memory:** `feedback-harness-evaluator-bias-and-verifier-roi.md` — observation that prompted this work.
- **Memory:** `project-harness-improvement-direction.md` — JR's confirmed direction (4 points: fixer-self-verify, surface_check stays, no ce:review, evaluator rebalance).
- **Memory:** `feedback-merge-only-after-explicit-review-go.md` — PR #25 had 5 P0 bugs after merge despite verifier approving (case for replacing AI verifier).
- **Memory:** `feedback-trust-agent-drop-regex-guards.md` — surface_check (deterministic) is the right kind of guard; AI verifier was the brittle one.
- **Code:** `harness/run.py:770-892` (verify phase to delete), `:894-1000` (revert phase to keep), `:1583` (fixer commit hook).
- **Code:** `harness/prompts/fixer.md:107-118` ("Anticipate the verifier" — the 6 probes).
- **Code:** `harness/engine.py:107-180` (Verdict — keep); `:195-225` (verify — delete).
- **Code:** `harness/safety.py` — surface_check (unchanged, just relocated call site).
- **PR:** #37 (`harness/run-20260428-105643`) — squash-merged as `dedb25d` on 2026-04-29; the run that surfaced both issues.
