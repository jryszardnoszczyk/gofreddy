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
- **Subset:** PDF/PPTX text-extraction helpers only. Drop URL/video paths (those are Bundle C, parked).
- **Acceptance:** `extract_pdf(path) -> str` and `extract_pptx(path) -> str` work against fixture files in `tests/fixtures/extraction/`. Imports `pdfplumber` + `python-pptx` (already in `pyproject.toml` deps).

### P-3 — `tests/deepfake/test_models.py`
- **Source:** `freddy/tests/deepfake/test_models.py` (226 LOC)
- **Target:** `gofreddy/tests/deepfake/test_models.py`
- **Action:** Direct port; tests `src/deepfake/models.py` which already exists in gofreddy with zero coverage.
- **Skip:** `freddy/tests/deepfake/test_router.py` (FastAPI route tests, out of scope) and `test_service.py` (covers `src/deepfake/service.py` which doesn't exist in gofreddy — rides with future Bundle G if/when).
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

## Parallel small chore PRs (independent of this branch)

Land in any order after this branch (or alongside if no merge conflicts).

### `chore/freddy-fix-backport`
Cherry-pick 6 freddy commits (evaluation hardening fixes that touch shared files):
- `49e87a2` — exclude underscore-prefixed competitor files from structural count
- `92f6e3a` — competitive structural hardening + route brief.md only to judges
- `0a1283d` — retry judge ensemble once on all-fail before hard-zeroing
- `6e3c7e8` — split structural inputs from judge output_text
- `d2ba273` — return full SHA256 hash (drop 16-char truncation)
- `85929b6` — wrap startup generation-job reap in try/except

Skip 8 freddy autoresearch commits — gofreddy's autoresearch diverged 4× too far; cherry-picks won't apply cleanly. Effort: ~half-day.

### `chore/path-b-and-misc`
Three small things:
1. Mark all 14 `tests/orchestrator/test_*.py` with `pytest.skip(reason="Path B locked per docs/plans/2026-04-23-003-agency-integration-plan.md Decision #1")`.
2. Tighten 3 stale comments in `src/api/main.py:217,357,365` (replace "Skipped per migration plan" with "Permanently skipped — Path B locked, see docs/plans/2026-04-23-003 Decision #1").
3. One paragraph in `harness/README.md` documenting the deliberate 6→3 track scope reduction (commit `2359c7c`).

Effort: ~30 min.

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

Active scope shrank from 24 bundles to 5 ports + 2 chore PRs (this doc).

**Dropped:** Bundle A (orchestrator port — Path B rejects it), J + W (couples to A), N (`feedback_loop/` duplicates existing autoresearch infrastructure).
**Removed from this inventory's scope:** Bundle S (agency frontend strategy — belongs in its own architecture-decision doc, not a port question).
**Parked (no work; revisit only when concrete need surfaces):** C, D, E, F, G, I, M, O, R, U, X — 11 items kept implicit; consult git history at `cbed80f` if a future workflow needs to verify what was considered.
**Moved to next branch (`feat/audit-engine-implementation`):** B.3 (eval extensions for MA-1..MA-8), B.4 (marketing-audit judge), B.5 (autoresearch lane registration), B.6 (`programs/marketing_audit/` prompts) — greenfield, follows `docs/plans/2026-04-24-003`.

**Lesson recorded:** read all locked-decisions docs *before* surveying for gaps. A 5-minute scan of `docs/plans/2026-04-23-003-*` would have prevented 4 rounds of triage around a rejected premise.
