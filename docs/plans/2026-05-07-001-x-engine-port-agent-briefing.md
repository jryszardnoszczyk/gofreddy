---
title: "X + LinkedIn → Autoresearch Port — Implementing Agent Briefing"
type: agent-briefing
status: ready
date: 2026-05-07
plan: docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md
companion: docs/plans/2026-05-07-001-x-engine-rubric-anchors.md
worktree: /Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/x-engine-linkedin-port
branch: feat/x-engine-linkedin-port
base_commit: 9f8eb03  # main HEAD with Q2 = Option B locked
---

# X + LinkedIn → Autoresearch Port — Implementing Agent Briefing

You are the implementing agent for the X + LinkedIn → autoresearch port. Your job is to ship the plan to first-runnable in this worktree, end to end. Do not stop, do not defer, do not propose alternative approaches. The plan has been through 9 review rounds and is locked at v13. All open questions have been resolved (Q2 = Option B, locked 2026-05-07). Your job is execution.

## Read first (in this order, then start)

1. **Master plan:** `docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md` (744 lines). Read all of it. The plan is the contract. Do not re-litigate.
2. **Rubric companion:** `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` (29 lines, X-1..X-6 + LI-1..LI-6 anchor prose). Use these as the source of truth for `SessionEvalSpec.rubric_anchors`.
3. **Pickup memo (project memory):** `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/project-x-engine-port-l0-pickup.md`. The "DO-NOT" list is binding. The 5 pre-L0 operator tasks list is what JR owns; you do NOT do those — you surface them to JR when blocked.
4. **Lane registry contract:** `autoresearch/lane_registry.py` (frozen `LaneSpec` dataclass at lines 22–46). Follow the precedent of how the 4 existing lanes (geo, competitive, monitoring, storyboard) registered.
5. **WorkflowSpec contract:** `autoresearch/archive/v007/workflows/specs.py:32-44` (11 fields, not 8 — confirmed by Round-8 audit). Mirror **`competitive.py` not `geo.py`** for WorkflowSpec — geo's `pre_summary_hooks` runs scripts that don't apply here.
6. **SessionEvalSpec contract:** `autoresearch/archive/v007/workflows/session_eval_common.py:17-25`.
7. **Concrete reference for evolvable agent prompt:** `autoresearch/archive/v007/programs/geo-session.md`.
8. **In-session evaluator pattern:** `autoresearch/archive/v007/scripts/evaluate_session.py`.
9. **Final-scoring judge prompt:** `judges/evolution/prompts/scorer.md` (note: L0 row 7+8 already shipped on main — `77f536d` — two-template scorer dispatch is in place).
10. **Agent subprocess invocation pattern:** `autoresearch/evaluate_variant.py:836-933`.
11. **Judge call shape:** `autoresearch/evaluate_variant.py:1101-1184`.

## Hard rules (binding)

- **No re-review of the plan.** v13 is final. 9 rounds of pressure-test happened pre-handoff. If something looks wrong to you, ask JR directly — do not start a v14.
- **No re-exploration of vendors.** D11 locked Apify primary + Bright Data fallback. Do not propose Twitter API, RapidAPI, etc.
- **No pivot back to single-platform.** D10 locked: both lanes ship simultaneously in v1. LinkedIn is sibling not optional.
- **No pivot to 3-template scorer or per-lane voice substrates.** Two-template scorer dispatch (L0 row 7+8) shipped. D4 locked one shared voice substrate.
- **`pick-angles` does NOT move to a shared upstream module.** It stays in the X lane only; LinkedIn consumes the X-derived angles via `xeng top-linkedin` (D13).
- **Do NOT add `runtime/<lane>.py` files.** The 4 existing lanes don't have those; the 5th and 6th won't either. Follow `WorkflowSpec` registration only.
- **No mid-build pushes to main.** Stay on `feat/x-engine-linkedin-port` until first-runnable. Per JR feedback: agent-built single-run plans stay on worktree until first-runnable; don't propose push/PR after each layer.
- **All work-tree-local until first-runnable.** Then surface to JR for review. JR — not you — opens the PR.
- **Commit before launching any subprocess that reads from disk.** Per memory `feedback-commit-before-harness-run.md`: harness/agent worktrees are cut from HEAD; uncommitted main-repo edits are invisible.
- **Tests pass after each unit.** Per AGENTS.md and ce-work skill: run the autoresearch suite before every commit.
- **Bare-import convention for `concurrency`.** `import concurrency` not `from autoresearch.concurrency import …` (production sites and tests must agree on canonical name; otherwise singleton splits — caught and documented in PR #44).

## Pre-L0 operator gates (NOT yours — surface and wait)

These five tasks are JR's. You CANNOT proceed past L0 row 1 until they're confirmed done. Surface clearly and wait if blocked:

1. **F4 rubric anchor work** — JR-reviewed prose for X-1..X-6 + LI-1..LI-6 in the companion file. (May already be done — check the file.)
2. **External triangulation** — JR's pull from external mentor / industry context.
3. **Cold-start commitment** — JR's commitment to the 14-day X-dogfood + open-ended LinkedIn-bootstrap.
4. **L0 smoke** — small validation that the two-template scorer dispatch (already shipped as L0 row 7+8) actually runs on a real fixture.
5. **Apify + Bright Data subscriptions** — paid accounts in JR's name, API keys placed in env per D11.

If any of these are not done when you reach a gating point: STOP, surface to JR with a clear "blocked on operator task #N", and wait.

## The build sequence

Three layers: **L0** (~2d engineer-days, partially shipped), **L1** (~6.75d engineer-days + 14d X-dogfood calendar wait), **L2** (~16-18d engineer-days, ~25-30d calendar-days).

### L0 — judge-service criteria infra (~2 engineer-days; row 7+8 ALREADY SHIPPED)

Per §7.2 of the plan. Two-template scorer dispatch shipped on main as commit `77f536d`. Verify:
- `judges/evolution/prompts/scorer.md` exists and dispatches between X / LinkedIn templates correctly. If yes, mark L0 row 7+8 done.
- L0 rows 1–6 (per plan): write the X scorer template, write the LinkedIn scorer template, wire dispatch in `evaluate_variant.py`'s `_invoke_judge_with_retry`, plumb the `lane` argument through.
- L0 smoke (operator gate #4): JR runs a small fixture against both templates, confirms scoring works.

After L0: commit, run autoresearch suite (must pass), proceed to L1.

### L1 — X holdout signal + v1 X cron revival + Apify + LinkedIn-CLI (~6.75d + 14d X-dogfood)

Per §7.3 of the plan + §5 (Holdout Infrastructure). The L1 sequence:

1. **Day 0:** revive v1 X cron (per D9 — `launchctl load` the existing `.plist` at `x_engine/com.jryszardnoszczyk.x-engine.plist`). Daily X drafts must produce from day 0 — the 14-day dogfood clock starts now.
2. **Days 1–2:** `xeng holdout` CLI + new DB tables (per §5.2). Migration script per §5.3. NEW `hand_drafts` table for cold-start (per memory).
3. **Days 3–4:** Apify subscription wiring (operator gate #5 — surface and wait if not done). Daily 06:35 keyword pull `--max-cu 50`. Weekly Sun 07:00 creator pull `--max-cu 200`.
4. **Day 5:** Bright Data fallback scaffold (~2d, feature-flagged off per D11).
5. **Day 6:** LinkedIn-specific CLI (`xeng top-linkedin`, `xeng linkedin-evidence`, etc. per §5.2).
6. **Day 6.75:** LinkedIn pull cadence wiring (Gap C — verify by §4.2 row).
7. **Days 7–20 (calendar):** 14-day X-dogfood window. JR posts hand-written X drafts daily; engagement formula `(reactions×1 + comments×3 + shares×5) × exp(-days/14)` accumulates real-world signal. **You wait** — engineering is parked. Use this time to prepare L2 materials but do NOT start L2 production code.

After L1: commit, run suite, surface to JR for X-day-7 verdict gate.

### L2 — seed cull + lane scaffolds + first iterations (~16-18d engineer + 25-30d calendar)

Per §7.4–§7.6 of the plan + §3 (Seed Architecture) + §4 (Lane Architecture).

1. **Day 0:** seed cull per §3.1 — fresh `archive/v007-curated/` per Q2 = Option B. Don't extend `v007/`. Strip x_engine artifacts; carry only the seed code paths the new lanes need. Per §3.2: net LOC budget ~250 lines per lane.
2. **Day 0:** Q2 dispatch verification (sanity check). Push a non-seed variant through the lane registry; confirm the 5 hardcoded `domain == "X"` branches in `run.py` / `runtime/` / `scripts/` still fall through gracefully (audited, no edits expected). If KeyError: STOP, surface to JR — Round-8 audit assumed wrong.
3. **Days 1–4:** §4.1 — register `LaneSpec` entries for X and LinkedIn. Two new entries in `LANES`. Update lane registry header comment (already done by parallelism PR — `lane_registry.py` notes auto-inheritance; X and LinkedIn inherit critic-domain / finalist / fixture-fan-out parallelism for free).
4. **Days 5–8:** §4.2 drift gate — 9 surfaces (both lanes). Walk every gate; verify no drift.
5. **Days 9–12:** §4.3 — WorkflowSpec for X (~80 LOC). Mirror **competitive.py** not geo.py.
6. **Days 13–16:** §4.3 — WorkflowSpec for LinkedIn (~80 LOC).
7. **Days 17–18:** §4.4 — SessionEvalSpec for both lanes. Per-platform rubric anchors from companion file.
8. **Days 19–20 (engineer):** §4.5 — variant backfill into the `v007-curated` seed only (per D8). Older variants pre-date lanes; per-lane frontiers start at the seed.
9. **Day 21:** `xeng test-structural-doc-facts` — NEW pytest.skip per memory (no precedent for this kind of assertion file; the test is a placeholder until structural doc facts are real).
10. **Day 22+:** Mark-posted critical-path before dogfood (per memory). Findings_promotion title = "Global Findings: <Lane>" (per memory).
11. **Days 23–30 (calendar):** first iteration cycles. X day-7 verdict gate at week 1 of L2. LinkedIn drift checks at week 4 (Gap D). **D12 ROI verdict at L2 week-8:** if LinkedIn fails to clear ≥3 ship-eligible/wk + judge ≥6.5, pause LinkedIn lane by week-12. X lane proceeds regardless.

After L2 first-runnable: STOP, surface to JR. JR opens the PR. Do not push, do not auto-merge.

## Drift gate (do not skip)

§4.2 of the plan: 9 surfaces that drift between X and LinkedIn. Per-lane WorkflowSpec implementations must each pass the gate. The gate is intentionally redundant with the build sequence work-items in §7 — the build-sequence is summarized at layer level; the drift gate is the per-row contract.

## Parallelism inheritance (free, do not re-implement)

The parallelism framework (PR #44, plan `2026-05-07-002`) shipped 3 parallel paths:
- **Critic domains** parallel under `claude` semaphore.
- **Holdout finalists** parallel under `judge_http` semaphore.
- **Fixture fan-out** parallel under backend-derived resource (claude/codex/opencode).

When you register the X and LinkedIn `LaneSpec` entries, they inherit all 3 dimensions for free. Do not add `parallel_for` calls in the lane modules.

**Cross-lane parallelism (`run_all_lanes`) is intentionally NOT enabled** — `cmd_run` is not thread-safe (signal handlers in workers, `os.environ` mutation, shared `archive_dir`). Run the 6 lanes serially; per-lane work parallelizes within. See `docs/architecture/concurrency.md` for the full known-limitations list.

## Quality gates per commit

- All units' tests green: `pytest tests/autoresearch/ -v`. Use the bundled venv: `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.venv/bin/python -m pytest`.
- Cross-package suites green: `pytest tests/harness/ tests/freddy/fixture/test_refresh_*.py tests/freddy/fixture/test_staleness_*.py -q`.
- 4 archive symlinks pre-staged in worktree (`autoresearch/archive/{current_runtime,v008,v009,v010}` → main repo's). The parallelism worktree had to add these manually; this worktree may need the same. If `from harness.stall import …` fails, that's the cause — symlink and continue.
- Conventional-commit messages (`feat(autoresearch): …`, `fix(autoresearch): …`, `refactor(autoresearch): …`, `docs(autoresearch): …`).
- No `Co-Authored-By` attribution on incremental commits — only on the final PR-creation commit (per ce-work skill).

## When you finish

L2 first-runnable = a successful end-to-end iteration of one X variant AND one LinkedIn variant through search + holdout + judge + promotion. When that happens:

1. Run full suite + cross-package suites.
2. Commit any final cleanup.
3. Push the branch (`git push -u origin feat/x-engine-linkedin-port`).
4. **Stop. Do not open the PR.** Surface to JR with: branch URL, commit count, files changed, any operator gates still open, and a single sentence on what you observed in the first end-to-end run.

JR reviews, opens the PR, runs the operator-coordinated dogfood validation, and decides on merge.

## Escalation paths

- **Plan ambiguity:** ask JR directly. Do NOT improvise a v14.
- **Pre-L0 operator gate not done:** STOP, surface, wait. Do not bypass.
- **Test failure that you can't diagnose in 30 minutes:** spawn a `general-purpose` subagent for root-cause analysis (per memory: "verify diagnoses with investigator agents"). Don't pattern-match from log summaries.
- **Memory says X but plan says Y:** plan wins. Memories are time-stamped; plans are versioned. v13 is canonical.
- **You feel the urge to revert/rebase/force-push:** STOP. Surface to JR. Per memory `feedback-no-mid-build-pushes-on-agent-built-runs` and `feedback-stay-on-main-or-worktree`: destructive actions on shared branches need explicit JR approval.

## Reference: plan structure (read for navigation)

| Section | Topic | Lines |
|---|---|---|
| §1 | Goals, non-goals, north star, D1–D13 | 23–82 |
| §2 | Deliverable shape (per-fixture session, draft markdown, fixture context, search/holdout split, scoring path) | 84–252 |
| §3 | Seed architecture (cull, LOC budget, agent prompts, CLI surface, parallel-run, X-derived angles) | 253–334 |
| §4 | Lane architecture (LaneSpec, drift gate, WorkflowSpec, SessionEvalSpec, backfill, fixture pools) | 335–508 |
| §5 | Holdout infrastructure (the L1 prerequisite — bar, CLI, migration, dogfood, why X-before-scaffold) | 509–573 |
| §6 | Evolution loop wiring (per lane, independent tracks) | 574–588 |
| §7 | Build sequence, first-runnable, risks (layers L0/L1/L2) | 589–end |

Now read the plan, then start with L0 row 1 (or verify L0 rows 7+8 still pass and proceed).
