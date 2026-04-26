---
title: Port-only extraction checklist — agency integration plan
date: 2026-04-24
status: working-doc (pre-extraction)
source: docs/plans/2026-04-23-003-agency-integration-plan.md
companion: docs/plans/2026-04-23-002-agency-integration-research-record.md
purpose: Complete map of what goes into a port-only extracted plan, what gets dropped, what needs rewriting. Built before writing the extracted doc so we do it correctly in one pass.
---

# Port-only extraction checklist

## Source

Bulk plan: `docs/plans/2026-04-23-003-agency-integration-plan.md` (1,777 lines, 19 sections, committed 2026-04-23 as part of `4d497ad`).

Greenfield counterparts that must be cross-referenced (not duplicated):
- `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` — Bundle 9 design
- Bundle 10 design lives only inside bulk plan §7 (no standalone doc)

## Extraction target

New file: `docs/plans/2026-04-24-002-agency-integration-port-plan.md`

## Section-by-section disposition

| § | Title | Disposition | Notes |
|---|---|---|---|
| Frontmatter | title/date/status/companion/scope | Rewrite | New title, date 2026-04-24, `source:` pointer, `greenfield_counterpart:` pointer |
| 0 | Executive summary | Rewrite | Re-frame for restoration-only scope (drop "first revenue audit ~6–8 weeks" line — that's Bundle 9) |
| 1 | Locked decisions (10) | Filter | Keep #1, 2, 3, 4, 5, 8, 9, 10 · Drop #6 (lens registry), #7 (LHR placement) |
| 2 | Bundle sequence + dependency graph | Rewrite | Remove Bundle 9+10 nodes from graph; note them as external prerequisite handoff points |
| 3 | Bundle 0 — Pre-flight | Verbatim | §3.1–3.5 keep all |
| 4 | Bundle 1 — Analytical uplift | Verbatim | §4.1–4.5 keep all |
| 5 | Bundle 2 — Client platform (lite) | Verbatim | §5.1–5.6 keep all |
| 6 | Bundle 9 — Audit engine | DROP | Greenfield; cross-ref to plan 2026-04-20-002 |
| 7 | Bundle 10 — LHR autoresearch lane | DROP | Greenfield; cross-ref to bulk plan §7 |
| 8 | Bundle 7 — Workers MVP | Verbatim | §8.1–8.7 keep all |
| 9 | Bundle 3 — CI triangle | Verbatim | §9.1–9.9 keep all |
| 10 | Bundle 4 — Creator ops | Verbatim | §10.1–10.11 keep all |
| 11 | Bundle 5 — Content factory | Verbatim | §11.1–11.9 keep all |
| 12 | Bundle 6 — Video studio (deferred) | Verbatim | §12.1–12.2 (short) |
| 13 | Bundle 8 — Workspace + skills (deferred) | Verbatim | §13.1–13.2 (short) |
| 14 | Execution checkpoints | Filter table | Keep C1, C2, C5, C6, C7, C8 · Drop C3 (Bundle 9), C4 (Bundle 10) |
| 15 | Appendix A — DB migrations | Filter table | Drop Bundle 9 row (no migration anyway) |
| 16 | Appendix B — Env vars | Filter table | Drop Bundle 9 row |
| 17 | Appendix C — Python deps | Filter table | Drop Bundle 9 row (`playwright`). Keep "explicitly skipped" list verbatim (explains Path B + locked decisions) |
| 18 | Appendix D — Risk register | Filter table | Drop "Audit cost ceiling" (Bundle 9) + "Autoresearch variants degrade" (Bundle 10). Keep 5 of 7 rows |
| 19 | End of plan / next actions | Rewrite | Current next-actions assume greenfield-first order; rewrite for port-only sequencing choices |

## Locked-decision classification (verified)

| # | Decision | Port-relevant? | Cited in port bundles |
|---|---|---|---|
| 1 | Path B programs-only | **Keep** | §10.1 (Bundle 4 creator ops), §13.1/§13.2 (Bundle 8), §3.1 (14 orchestrator tests permanent-xfail) |
| 2 | Stay on Fly.io | **Keep** | §8.1 (Bundle 7 infra) |
| 3 | CLI-first | **Keep** | Cross-cutting — why no web UI in port bundles |
| 4 | Skip Stripe phase 1 | **Keep** | Phase-1 scope for Bundle 3 + Bundle 5 |
| 5 | Orphaned tests = xfail | **Keep** | §3.1 core policy |
| 6 | Lens registry shape | **Drop** | Bundle 9 only |
| 7 | LHR placement | **Drop** | Bundle 10 only |
| 8 | Regenerate large repos | **Keep** | §12.1 (Bundle 6 video_projects 17k LOC) |
| 9 | Workers MVP = 2 workers | **Keep** | §8.1, §8.7 explicit-defer list |
| 10 | Build order audit-first | **Keep with note** | This is *why* port bundles wait; reframe as "external prerequisite" |

## Cross-bundle dependencies into greenfield (must not break)

1. **Bundle 0 xfail table** (§3.1) — 4 test-file rows reference Bundle 9 or Bundle 8 as the restorer. Those tests stay xfail'd in port-only scope. Preserve rows as-is, add footnote: "rows citing Bundle 9 or Bundle 8 remain xfail until those bundles ship (Bundle 9 greenfield; Bundle 8 deferred under Path B)."
2. **Bundle 9 pulls from port** (§6 header): `Depends on: Bundles 0, 1, 2`. Port-only doc should note: "Bundle 1 + 2 feed both greenfield Bundle 9 and downstream port bundles — they're dual-purpose preparation work."
3. **Bulk plan sequence** has Bundles 7→3→4→5 *after* Bundle 9+10. But technical dependencies are only:
   - Bundle 7 → Bundle 2 (clients for auto-brief)
   - Bundle 3 → Bundles 2, 7
   - Bundle 4 → Bundle 2
   - Bundle 5 → Bundles 2, 7
   - **None of 3/4/5/7 technically depend on Bundle 9 output.** The "after Bundle 9" sequencing is the "ship moat first" priority rule (decision #10), not a tech dep.
   - Port-only doc should surface this as a parallel-track option: "once Bundles 0+1+2 ship, port bundles 3/4/5/7 could run parallel with greenfield Bundle 9+10 if priorities shift."

## Corrections to my earlier verbal claims

1. ✗ "Bundle 0's dep list is bloated — 8 deps, most unneeded given locked decisions."
   ✓ Bulk plan actually scopes Bundle 0 to **5 deps** (resend, weasyprint, mistune, nh3, jinja2). The 8-dep list is from the research record inventory, not the plan. Appendix C explicitly lists the 6 skipped packages (stripe, cloud-tasks, dspy, supabase, svix, redis-in-B0) with rationale. **Withdraw the "bloated" critique.**

2. ✗ "Locked decisions: 6 apply to port, drop 4."
   ✓ Correct count: **8 apply, drop 2** (#6, #7). Verified above.

3. ✗ "~10–12 months sequential for port work."
   ✓ Bulk plan §2 states "Total to last executed bundle (5): ~22–26 weeks sequential, ~14–18 weeks parallel." That's ~5–6 months sequential, ~3.5–4.5 months parallel **for the non-deferred port bundles** (0, 1, 2, 7, 3, 4, 5). Bundles 6+8 are indefinitely deferred. My 10–12mo figure conflated the research record's raw-restoration total (11 bundles) with the already-triaged plan's executed-bundle count (7).

## Content I originally missed in my outline summary

- Frontmatter `companion:` field (need to carry over to new doc)
- "Explicitly deferred" and "Explicitly included" subsections inside Bundles 2 and 9
- Appendix D — Risk register (I only said "A–D" without detail)
- §19 "End of plan / next actions" (separate from appendices)
- Permanent-xfail cohort: 14 `tests/orchestrator/test_*.py` files under Path B decision #1
- The §3.1 xfail mapping table covers 17 test files with per-bundle restore pointers
- PublishDispatcher "enabled: False" caveat in §8.4 — deploy Bundle 7 infra now, wire Bundle 5 later
- §8.5 auto-brief trigger — Bundle 7 hooks Bundle 3 (port-to-port dep)
- §9.1 splits monitoring/intelligence/ across Bundle 1 (5 files) vs Bundle 3 (8 files)

## Rewritten bundle sequence (port-only)

```
Bundle 0 (3–4 days)  — unblocks everything
       ↓
   ┌───┴───┐
Bundle 1   Bundle 2   (parallel, 1 week)
(analytical) (client-lite)
   └───┬───┘
       ↓
[EXTERNAL: Bundle 9 greenfield audit engine + Bundle 10 LHR — 
 see docs/plans/2026-04-20-002 and bulk plan §7]
       ↓
Bundle 7 (2–3 weeks)  — workers MVP
       ↓
Bundle 3 (3–4 weeks)  — CI triangle
       ↓
Bundle 4 (3 weeks)    — creator ops
       ↓
Bundle 5 (5 weeks)    — content factory
       ↓
[INDEFINITELY DEFERRED]
Bundle 6 — video studio
Bundle 8 — full workspace + Path A orchestrator
```

Alternative parallel-track sequencing (surfaced in port-only doc §2 as option):
- After Bundles 0+1+2 ship, greenfield (9+10) and port downstream (7/3/4/5) could run parallel on independent tracks, since port bundles 3/4/5/7 have no technical dep on audit-engine output. Requires priority call: stick with "moat first" (decision #10) or allow parallel.

## Rewritten exec summary draft (for the new doc)

> This document is the port-only subset of the agency integration plan. It restores agency capability from the `freddy` repo to `gofreddy`: worker infrastructure, client data model, content generation + multi-platform publishing, creator fraud + deepfake vetting, and the weekly competitive brief deliverable.
>
> It excludes the greenfield **audit engine** (Bundle 9) and **LHR autoresearch lane** (Bundle 10), which are `gofreddy`-native designs. Those are gofreddy's differentiated product and live in `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` and the bulk plan §7 respectively.
>
> Effort: **~14–18 weeks parallel, ~22–26 weeks sequential** for Bundles 0, 1, 2, 7, 3, 4, 5. Bundles 6 (video studio) and 8 (full workspace) are indefinitely deferred.
>
> **Everything past Bundle 2 is customer-conditional.** The bulk plan's build-order decision (#10, audit engine before weekly brief) means port bundles 7/3/4/5 wait on greenfield Bundle 9+10 unless priorities shift. Bundle 0 (pre-flight) is the only unconditional pre-work: it unblocks honest CI. Bundles 1+2 are strongly recommended early because they feed both greenfield and downstream port work.
>
> Full research inventory lives in the companion doc at `docs/plans/2026-04-23-002-agency-integration-research-record.md`. Source of this extraction: `docs/plans/2026-04-23-003-agency-integration-plan.md`.

## Open decisions for JR (before executing extraction)

1. **Parallel-track framing:** surface it as an explicit option in §2, or keep the bulk plan's sequential "moat first" ordering as the only visualized path?
2. **Bundle 6 + Bundle 8 deferred sections:** keep short verbatim (25–30 lines each) or compress further to 2-line "see bulk plan" pointers? (Recommend keep short — they already are short and the rationale carries value.)
3. **New filename:** `2026-04-24-002-agency-integration-port-plan.md` (matches date-nnn-slug convention)? Or a different slug?
4. **Appendix C "explicitly skipped" list:** keep verbatim (clarifies Path B scope, not Bundle 9-specific) — recommend keep.
5. **§3.1 xfail table footnote:** the table references Bundle 9 and Bundle 8 as restorers for 4 test rows. Add a footnote "rows citing Bundle 9 or Bundle 8 remain xfail until those bundles ship" — confirm OK.

## Execution plan (post-compaction)

1. Read this checklist.
2. Read `docs/plans/2026-04-23-003-agency-integration-plan.md` source sections to copy.
3. Write new file `docs/plans/2026-04-24-002-agency-integration-port-plan.md` following the disposition table above.
4. Cross-check: every "verbatim" section matches source; filtered tables dropped the correct rows; rewrites reference the right anchor docs.
5. Commit with message referencing this checklist and source doc.
