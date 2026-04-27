# Fred → GoFreddy Port-Gaps: Ports-only Checklist

**Date:** 2026-04-27
**Branch:** `feat/fred-port-gaps`
**Status:** active. Single source of truth for this branch. (Earlier 5-round inventory + design lived at `2026-04-26-001-*` and `2026-04-26-002-*`; deleted in commit after git `cbed80f` once the round-5 reframe rendered them obsolete. Git history preserves them if needed for archaeology.)
**Source-of-truth:** `freddy` repo @ commit `50602a2`
**Target:** `gofreddy/main` @ `feaacf7`

---

## Framing

GoFreddy's `autoresearch/` is the orchestration system — lanes, variants, evolution, programs-as-skills, judges. Per `docs/plans/2026-04-23-003-agency-integration-plan.md` Decision #1, **Path B (programs-only extension) is locked**; freddy's `src/orchestrator/` is *not* ported. Re-evaluate gate: paying client demanding chat UI with capability pills (until then, locked).

This branch's purpose: **port missing functionality from freddy that meaningfully helps autoresearch or its consumers**. Strict port-only scope. Greenfield audit-engine work belongs to the next branch (`feat/audit-engine-implementation`) following `2026-04-24-003-audit-engine-implementation-design.md`.

5 rounds of survey rationale lives in the superseded inventory + design docs. Nothing else from those docs is active scope.

---

## The 5 ports

Each is small (S) and independent. Single PR off this branch. Estimate: 2–3 working days.

### P-1 — `src/clients/models.py` subset
- **Source:** `freddy/src/clients/models.py` (50 LOC)
- **Target:** `gofreddy/src/clients/models.py`
- **Subset:** keep `name`, `slug`, `domain`, optional `enrichments: dict`, optional `fit_signals: dict`, `created_at`. Drop billing/membership/workspace fields (SaaS-coupled).
- **Acceptance:** Pydantic model loads; JSON roundtrip test passes; no asyncpg/Supabase imports.

### P-2 — `src/extraction/asset_extractor.py`
- **Source:** `freddy/src/extraction/content_extractor.py` (562 LOC — subset only)
- **Target:** `gofreddy/src/extraction/asset_extractor.py`
- **Subset:** PDF/PPTX text-extraction helpers only. Drop URL/video paths (those are Bundle C, rejected per decision log).
- **Acceptance:** `extract_pdf(path) -> str` and `extract_pptx(path) -> str` work against fixture files in `tests/fixtures/extraction/`. Imports `pdfplumber` + `python-pptx` (already in `pyproject.toml` deps).

### P-3 — `tests/deepfake/test_models.py`
- **Source:** `freddy/tests/deepfake/test_models.py` (226 LOC)
- **Target:** `gofreddy/tests/deepfake/test_models.py`
- **Action:** Direct port; tests `src/deepfake/models.py` which already exists in gofreddy with zero coverage.
- **Skip:** `freddy/tests/deepfake/test_router.py` (FastAPI route tests, out of scope) and `test_service.py` (covers `src/deepfake/service.py` which doesn't exist in gofreddy; Bundle G rejected per decision log).
- **Acceptance:** `pytest tests/deepfake/test_models.py` passes.

### P-4 — `docs/from-fred/` snapshot
- **Source:** 10 files from `freddy/docs/research/` and `freddy/docs/plans/`
- **Target:** `gofreddy/docs/from-fred/` (new directory) + a top-level `README.md` explaining frozen status
- **Files to copy:**
  1. `docs/research/2026-04-17-workflow-failure-root-causes.md`
  2. `docs/research/2026-04-13-autoresearch-session-loop-audit.md`
  3. `docs/research/2026-04-11-autoresearch-evaluation-infrastructure-audit.md`
  4. `docs/research/2026-04-11-autoresearch-prompt-audit.md`
  5. `docs/research/2026-04-14-autoresearch-run2-audit.md`
  6. `docs/research/2026-04-16-storyboard-mock-removal-and-evolution-readiness.md`
  7. `docs/plans/2026-04-18-001-migrate-autoresearch-to-gofreddy-plan.md`
  8. `docs/plans/2026-04-14-004-refactor-harness-unconstrained-loop-plan.md`
  9. `docs/plans/2026-04-08-001-fix-harness-round1-findings-plan.md`
  10. `docs/superpowers/specs/2026-04-16-freddy-distribution-engineering-agency-design.md`
- **README content:** "Frozen reference material from `freddy@50602a2`. Not actively maintained. Read for context only — do not port code from these. The most directly applicable is `2026-04-17-workflow-failure-root-causes.md` (31 documented autoresearch failures with fixes)."
- **Acceptance:** all 11 files exist; relative paths inside the markdown files are not rewritten (broken intra-doc links acceptable).

### P-5 — `autoresearch/archive_cli.py`
- **Source:** `freddy/autoresearch/archive_cli.py` (182 LOC)
- **Target:** `gofreddy/autoresearch/archive_cli.py`
- **Action:** Direct port; provides `frontier`, `topk`, `show`, `diff`, `regressions`, `stats` subcommands over the autoresearch variant archive. Operator inspection tool.
- **Adjustments needed at port time:** verify import paths point to `gofreddy/autoresearch/archive_index.py` + `frontier.py` (likely identical surface; check before port).
- **Acceptance:** `python -m autoresearch.archive_cli frontier` runs against current archive without error; smoke test for each subcommand.

---

## Branch hygiene

- **No commits should reference Bundle A or freddy's `src/orchestrator/`.** Both inventory + design have superseded headers; the active reference is this checklist.
- **Run baseline tests** after each port lands: `uv run --extra dev pytest tests/test_query_builder.py tests/test_cli_evaluate_scope.py tests/deepfake/test_models.py -q`.
- **PR description** cites Decision #1 + Path B and links to this checklist.

---

## Cleanup units (folded into this branch — single PR)

Two cleanup tracks formerly framed as parallel chore PRs ride on this branch as additional units. Total scope is **5 ports + 2 cleanup bundles = 7 units in one PR**.

### C-1 — Freddy evaluation-fix backport — **NO-OP (verified 2026-04-27)**
Cherry-pick attempt for 6 freddy commits (evaluation hardening fixes that touch shared files):
- `49e87a2` (underscore-prefixed competitor exclusion) — **already in gofreddy** (cherry-pick no-op)
- `92f6e3a` (competitive structural hardening + brief.md routing) — **already in gofreddy** (`_JUDGE_PRIMARY_DELIVERABLE` includes `"competitive": ("brief.md",)`; structural.py has the 500-char + competitor-JSON parse checks)
- `0a1283d` (retry judge ensemble on all-fail) — **already in gofreddy** (cherry-pick no-op)
- `6e3c7e8` (split structural inputs from judge output_text) — **already in gofreddy** (`_JUDGE_PRIMARY_DELIVERABLE` map + `_build_judge_output_text` function present)
- `d2ba273` (full SHA256 hash, drop 16-char truncation) — **already in gofreddy** (cherry-pick no-op)
- `85929b6` (startup generation-job reap try/except) — **inapplicable to gofreddy** — the SaaS startup lifespan with `generation_repo.reap_stale_jobs()` was stripped; the bug condition doesn't exist here

Result: all 6 fixes either landed via prior maintenance or target paths gofreddy doesn't have. No commit needed. Skip 8 freddy autoresearch commits as before — gofreddy's autoresearch diverged 4× too far; cherry-picks won't apply cleanly. Effort: ~30 min audit (instead of half-day cherry-pick).

### C-2 — Path B housekeeping
Three small things plus the broken-test cleanup discovered during this branch:

1. ~~Mark all 14 `tests/orchestrator/test_*.py` with `pytest.skip(...)`~~ — **NO-OP**: gofreddy stripped `tests/orchestrator/` entirely; no files exist to mark. (15 unrelated `tests/test_*.py` files import `src.orchestrator` and fail collection — that's part of the broader 33+ orphaned-test problem named in `docs/plans/2026-04-23-003-agency-integration-plan.md` §3.1, which is its own task, not C-2.)
2. **Tighten 3 stale comments in `src/api/main.py`** (lines 216-219 block + 356-358 block + 365). Replace "Skipped per migration plan" / "not ported" wording with "Permanently skipped — Path B locked, see docs/plans/2026-04-23-003 Decision #1".
3. **Add a `## Scope: three tracks by design` paragraph to `harness/README.md`** documenting the deliberate 6→3 track reduction (commit `2359c7c`, 2026-04-18) so readers don't try to add D/E/F back.
4. **Delete 3 collection-blocking test files for unported services:**
   - `tests/test_clients_service.py` (imports `src.clients.{exceptions,service}` — only `src.clients.models` exists from P-1)
   - `tests/deepfake/test_router.py` (imports FastAPI + `src.billing` — billing stripped)
   - `tests/deepfake/test_service.py` (imports `src.deepfake.service` — Bundle G rejected)

Effort: ~30 min (orchestrator item turned into a no-op audit; broader 33-file orphan-test xfail pass remains separately scoped).

---

## Next branch (after this one)

`feat/audit-engine-implementation` — implements `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`. Greenfield extension to autoresearch:
- Builds `src/audit/` (state, sessions, cost_ledger, graceful_stop, agent_runner)
- Adds MA-1..MA-8 evaluation domain to `src/evaluation/`
- Marketing-audit judge (HTTP client following `judges/quality_judge.py` pattern)
- Registers `marketing_audit` lane in `autoresearch/`
- Creates `autoresearch/.../programs/marketing_audit/` with 4 agent prompts + critique manifest

Multi-week. Use formal brainstorm → writing-plans flow when starting that branch.

P-1 (clients schema) and P-2 (asset extractor) are prerequisites used by this next branch; they're ports here so the next branch can consume them.

---

## Decision log

**2026-04-26 (rounds 1–4):** 5-round parallel-agent survey produced a 24-bundle inventory + 501-line design centered on Bundle A (porting freddy's `src/orchestrator/`). Both committed at `cbed80f` and then deleted — git history preserves the audit trail.

**2026-04-27 (round 5 reframe):** Pressure-test surfaced two corrections:
1. **Path B is locked** in `docs/plans/2026-04-23-003-agency-integration-plan.md` Decision #1 (2026-04-23): "programs-only extension. gofreddy's programs-as-skills already beats freddy's orchestrator for autoresearch use case. Saves 6–8 weeks." The 14 `tests/orchestrator/test_*.py` files are marked xfail-permanent in that plan. The 5-round survey missed reading it.
2. **GoFreddy's `autoresearch/` *is* the orchestration system.** Lanes, variants, evolution, programs-as-skills, judges. Bundle A's framing treated autoresearch and "the orchestrator" as separate things; they are the same thing.

Active scope shrank from 24 bundles to 5 ports + 2 cleanup bundles (this doc).

**Dropped:** Bundle A (orchestrator port — Path B rejects it), J + W (couples to A), N (`feedback_loop/` duplicates existing autoresearch infrastructure).
**Removed from this inventory's scope:** Bundle S (agency frontend strategy — belongs in its own architecture-decision doc, not a port question).
**Moved to next branch (`feat/audit-engine-implementation`):** B.3 (eval extensions for MA-1..MA-8), B.4 (marketing-audit judge), B.5 (autoresearch lane registration), B.6 (`programs/marketing_audit/` prompts) — greenfield, follows `docs/plans/2026-04-24-003`.

**2026-04-27 (final no-deferrals pass):** Per the rule "either fix or reject, no deferrals," 11 previously-parked bundles converted to explicit rejections with one-line reasoning each:
- **C** (content_gen + full extractor): not used by autoresearch; speculative agency capability with no client validation
- **D** (publish/media/rank/seo_audit CLIs): no client demanding distribution; aspirational
- **E** (brands + monitoring intelligence + comments): SaaS coupling (asyncpg.Pool injected, IDOR enforcement on every method) makes "drop Postgres" framing wrong
- **F** (`generation/service.py` + `worker.py`): module docstring is "Cloud Tasks generation worker"; XL Cloud-Run-shaped (R2 + Tier + credit holds + 21-min stale-claim recovery), not a clean port
- **G** (6 service files): `publishing/service.py` is a token-vault (AES + OAuth + Cloud Scheduler `FOR UPDATE SKIP LOCKED`); `competitive/brief.py` requires `org_id: UUID` + 5-service fan-out; `search/service.py` depends on ICBackend + 3 platform fetchers; effort estimates were 2-3× optimistic
- **I** (3 evaluate flags): additive QoL, no operator pain
- **M** (env vars + Dockerfile): gofreddy hygiene, not a port from freddy
- **O** (5 router extractions): coupled to dropped Bundle A or no-tier features
- **R** (Gemini batches/caching, OpenAI reasoning, httpx tuning): performance pass, apply opportunistically inside any future service ports
- **U** (harness scorecard/convergence/escalation): gofreddy harness in active iteration (PRs #21–25); restoration would conflict with intentional simplification
- **X** (cost hard-cap): depends on dropped Bundle A's CostTracker; freddy doesn't have it either, so it's gofreddy hardening, not a port

**2026-04-27 (scope expansion pressure-test):** User asked to reconsider scope through an agency-needs lens (~30 units, 6-8 weeks). Four parallel reviewers (scope-guardian, product-lens, architecture-coupling, audit-engine-boundary) converged on rejection:
1. **Audit-engine plan never imports** `clients/models.py`, `asset_extractor.py`, or `competitive/brief.py` — true freddy dependency surface is essentially empty. P-1/P-2 are courtesy ports, not gates. The biggest stated reason for expansion (unblock audit-engine) doesn't hold.
2. **Bundle G files have hidden SaaS coupling** (see above) that invalidates the "drop Postgres, replace with file-based" framing for `publishing`, `generation`, `competitive/brief`, `search`, `monitoring/comments`.
3. **Strategic premise wrong:** "agency would need this" is speculative without paying-client validation; expansion would delay the only deliverable (`feat/audit-engine-implementation`) actually tied to business outcome.
4. **Repeats lesson recorded as `feedback-read-locked-decisions-before-surveying`** — surveying for gaps without grounding in locked decisions.

Held the 5-port + 2-cleanup-bundle scope. Re-evaluate individual rejected bundles only when a concrete pull surfaces (paying client demand, audit-engine surfaces a need, etc.).

**Lesson recorded:** read all locked-decisions docs *before* surveying for gaps. A 5-minute scan of `docs/plans/2026-04-23-003-*` would have prevented 4 rounds of triage around a rejected premise.
