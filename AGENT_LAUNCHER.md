# X + LinkedIn Port — Agent Launcher

Paste the prompt below into a fresh Claude Code session. Run it from anywhere — the prompt directs the agent to `cd` into this worktree and read its briefing.

---

## Launcher prompt (copy-paste into a fresh Claude Code session)

```
You are the implementing agent for the X + LinkedIn → autoresearch port.

Working directory: /Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/x-engine-linkedin-port
Branch: feat/x-engine-linkedin-port
Base: main HEAD 9f8eb03 (Q2 = Option B locked; no deferrals remain)

Your full briefing — read it cover-to-cover before doing anything else — is at:

    docs/plans/2026-05-07-001-x-engine-port-agent-briefing.md

That file references the master plan (744 lines), the rubric companion (29 lines), and the project memory pickup memo. Read all three in the order the briefing specifies, then start.

Hard rules (binding, do not improvise):
- v13 plan is final. 9 review rounds done. Do not start v14. Ask JR if something looks wrong.
- 5 pre-L0 operator tasks are JR's; surface and wait if blocked.
- No mid-build pushes to main. Stay on the worktree branch until first-runnable.
- JR — not you — opens the PR.
- Bare `import concurrency` in production (not dotted form) — singleton coherence.
- All open questions are resolved. Q1 = binary holdout. Q2 = Option B (fresh archive/v007-curated/). Q3 = one shared voice substrate.

Work autonomously through L0 → L1 → L2 to first-runnable. When you hit an operator gate, surface clearly and wait. When you reach first-runnable, push the branch, do NOT open the PR, surface to JR.

Begin by cd-ing into the worktree and reading the briefing.
```

---

## What this gets you

A fresh agent that:

1. Reads `docs/plans/2026-05-07-001-x-engine-port-agent-briefing.md` (156 lines — the implementer briefing).
2. Reads `docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md` (744 lines — the locked plan).
3. Reads `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` (29 lines — companion).
4. Reads `~/.claude/.../memory/project-x-engine-port-l0-pickup.md` (memory pickup memo with DO-NOT list).
5. Verifies L0 rows 7+8 (already shipped on main as `77f536d`) still pass.
6. Surfaces the 5 pre-L0 operator gates to you (Apify + Bright Data subscriptions, F4 rubric, etc.) and waits if any are not done.
7. Walks L0 rows 1–6 → L1 → L2 to first-runnable, committing as it goes, no mid-build pushes.
8. Pushes branch + surfaces to you for PR + dogfood validation when first-runnable hits.

## Q2 lock status

Q2 (seed-baseline variant: extend `archive/v007/` vs. branch fresh `archive/v007-curated/`) is **LOCKED = Option B** as of commit `9f8eb03` on main. The plan file is updated; there are no deferred decisions. The agent does not need to revisit this.

## Operator gates the agent will surface

These are yours; the agent cannot proceed past them:

1. F4 rubric anchor work (companion file may already cover this — check)
2. External triangulation
3. Cold-start commitment to 14d X-dogfood + open-ended LinkedIn-bootstrap
4. L0 smoke against the two-template scorer dispatch
5. Apify (apimaestro keyword + harvestapi per-creator) + Bright Data subscriptions

If the agent surfaces "blocked on operator task #N", you do that task, then tell the agent to resume.

## Estimated timeline

- L0 rows 1–6: ~2 engineer-days (rows 7+8 already shipped)
- L1: ~6.75 engineer-days + 14 calendar days X-dogfood (engineer waits during dogfood)
- L2: ~16–18 engineer-days, ~25–30 calendar days
- Realistic total: 8–10 weeks

## When the agent finishes

It will push `feat/x-engine-linkedin-port` and stop. You then:

1. Review the diff.
2. Open the PR yourself (`gh pr create …`).
3. Run the dogfood validation (you've been running daily X drafts the whole time per L1 day-0 cron revival).
4. Merge when D12 ROI thresholds clear.
