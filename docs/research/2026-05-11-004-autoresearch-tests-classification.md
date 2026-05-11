---
status: complete
created: 2026-05-11
author: claude opus 4.7 (U13a)
purpose: Plan B U13a — tests/autoresearch/ classification for U14 git-mv recipe
companion: docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md
---

# tests/autoresearch/ classification — U13a

Sweep of `tests/autoresearch/` (60 files, 13,958 LOC) to label each as
(a) **PORT** to `tests/autoresearch_v2/`, (b) **DELETE_WITH_V1** when
`autoresearch/legacy/` deletes in U15, or (c) **KEEP_FOR_JUDGES** (judge-
side tests that survive substrate decommissioning since judges are out of
Plan B's scope).

Methodology: classified by inspecting each file's top-level imports and
matching against the v1 modules Plan B deletes / keeps / slims.

---

## 1. Summary

| Verdict | Files | LOC | Notes |
|---|---:|---:|---|
| **PORT** to tests/autoresearch_v2/ | 14 | ~2,300 | Contract tests for v2-preserved behavior |
| **DELETE_WITH_V1** | 30 | ~9,200 | Test v1 internals v2 doesn't have |
| **KEEP_FOR_JUDGES** | 9 | ~1,800 | Judge-side tests; not Plan B's scope |
| **AMBIGUOUS / split** | 7 | ~660 | Mixed; per-test triage required during U14 |
| **Total** | 60 | ~13,958 | |

Expected post-U14 v2 test surface: ~3,000-4,000 LOC (60-70% deletion ratio,
matching plan estimate).

---

## 2. PORT — contract tests for v2-preserved behavior (14 files)

These assert on contracts v2 honors. Migrate to `tests/autoresearch_v2/`
adapting imports.

| File | LOC | Why PORT | Target v2 file |
|---|---:|---|---|
| `test_events.py` | 76 | events.py kept verbatim (U8) | `test_harness.py` (already covers) — DROP this file |
| `test_critique_manifest.py` | 109 | U5 ports the hash-check logic | `test_verify_critique_integrity.py` (already covers) — DROP |
| `test_compute_metrics_alerts.py` | 339 | U6 keeps the alert-agent path | `test_alert_check.py` (already covers) — DROP |
| `test_concurrency.py` | 258 | U8 slims to MAX_PARALLEL_AGENTS sem | `test_harness.py` (covers) — DROP |
| `test_backend_selection.py` | 108 | U8 keeps backend.py | `test_harness.py` (covers) — DROP |
| `test_opencode_jsonl.py` | 128 | U8 keeps verbatim | `test_harness.py` (covers) — DROP |
| `test_judge_calibration.py` | 116 | U8 keeps verbatim | port as `test_judge_calibration_v2.py` |
| `test_holdout_lineage_invariant.py` | 183 | Stream A 16 tests — Plan B mandates port | port as `test_holdout_lineage_invariant_v2.py` |
| `test_fragile_fixtures.py` | 135 | Stream A — Plan B mandates port | port as `test_fragile_fixtures_v2.py` |
| `test_x_engine_substrate.py` | 125 | Plan-mode plan U2 → Plan B U11/U12 surface | port as `test_x_engine_substrate_v2.py` |
| `test_linkedin_engine_substrate.py` | 102 | Same | port as `test_linkedin_engine_substrate_v2.py` |
| `test_marketing_audit_driver.py` | 203 | Driver loop is preserved in v2 lane prose | port as `test_marketing_audit_driver_v2.py` |
| `test_lane_registry.py` | 293 | Used by src/evaluation per U0 audit | port — lane_registry kept while wrapping v006 |
| `test_lane_registry_lifecycle_wraps.py` | 180 | Same | port |
| `test_structural_doc_facts.py` | 215 | Validates structural facts inlined in v2 lane prose | port |

**Note:** 6 of these (events, critique_manifest, compute_metrics_alerts,
concurrency, backend_selection, opencode_jsonl) are already redundantly
covered by `tests/autoresearch_v2/test_harness.py` + the per-tool test
files. The v1 ones are DELETE_WITH_V1 once their content has been verified
to be subsumed.

**Net new ports needed: ~8 files × ~150 LOC = ~1,200 LOC of v2 test code.**

---

## 3. DELETE_WITH_V1 — implementation-detail tests (30 files)

These assert against v1 private internals that v2 doesn't have. Die with
the substrate at U14.

| File | LOC | What it tests (v1) | Why v2 doesn't have it |
|---|---:|---|---|
| `test_evolution_fixes_2026_05_06.py` | 1,806 | `evaluate_variant._outer_pass_from_score`, `lane_registry.path_is_readonly` | v2 has no _outer_pass; scope safety via prose, not predicate |
| `test_resume_evolve.py` | 1,020 | `--resume-variant` machinery | 0 production uses; machinery deleted |
| `test_evolve_preflight.py` | 961 | L1 `py_compile` + `bash -n` preflight | 0 catches; L1 dropped |
| `test_select_parent.py` | 558 | `select_parent.py` 310 LOC | Replaced by prompt sentence in autoresearch.md |
| `test_program_prescription_critic.py` | 493 | v1 program-prescription path | substrate gone |
| `test_judge_fixes.py` | 440 | Judge-loop fixes for the v1 evaluate path | judges/ side has own tests (KEEP_FOR_JUDGES list) |
| `test_promotion_rule.py` | 363 | Promotion rule via v1 evolve_ops | promotion_judge tests stay; v1 rule plumbing dies |
| `test_evaluate_amendments.py` | 335 | v1 evaluate_variant amendments | substrate gone |
| `test_geo_verify.py` | 303 | Geo workflow via v1 evolve loop | v2 wraps v006/workflows/geo.py; this tests v1 evolve glue |
| `test_prompt_builder_isolation.py` | 284 | `harness/prompt_builder_entrypoint.py` | DELETE per U8 fate-table |
| `test_render_dynamic.py` | 277 | Render pipeline v1 integration | render kept; this tests v1-side glue specifically |
| `test_render_x_linkedin_composers.py` | 260 | Same — v1 glue | composers preserved; v1 glue dies |
| `test_render_session_bundle.py` | 259 | Same | |
| `test_a5_scope_violation.py` | 247 | ScopeViolation defense in v1 evaluate path | 0 ScopeViolations in 147 variants; substrate gone |
| `test_evaluate_amendments.py` | 335 | (listed above) | |
| `test_agent_retry.py` | 200 | `autoresearch.agent_retry` module | likely DELETE per audit (consumed by src/audit/agent_runner) |
| `test_marketing_audit_driver.py` | 203 | (PORT — listed in §2) | |
| `test_evaluate_single_fixture.py` | 201 | `evaluate_variant.evaluate_single_fixture` API | v2 doesn't have this exact API; cli/freddy/fixture/dryrun.py needs U13 adapter |
| `test_single_fixture_cli.py` | 181 | Same — fixture dryrun CLI integration | needs U13 |
| `test_judges.py` | 180 | (KEEP_FOR_JUDGES — listed in §4) | |
| `test_lane_registry_lifecycle_wraps.py` | 180 | (PORT) | |
| `test_evolve_ops_lineage_lock.py` | 171 | `evolve_ops.promote_atomic` locking | evolve_ops deleted; git replaces |
| `test_phase0_plumbing_smoke.py` | 168 | Phase 0 plumbing of v1 multi-candidate cohort | cohort dropped |
| `test_agent_calls_temperature.py` | 153 | `agent_calls.py` (221 LOC, DELETE per audit) | substrate gone |
| `test_render_quality_in_evolution.py` | 146 | v1 evolve loop integrating render quality | wraps via v2; this glue specifically dies |
| `test_evolve_ops_env_loader.py` | 145 | `evolve_ops.load_repo_env_defaults` | evolve_ops deleted; helper moved to U8 backend.py |
| `test_charts_svg.py` | 129 | Chart SVG rendering | render side; some may KEEP_FOR_JUDGES |
| `test_stall_state_changed.py` | 127 | `harness/stall.py` (165 LOC, DELETE per U8) | replaced by timeout |
| `test_finalists_parallel.py` | 125 | Cohort finalists machinery | cohort dropped |
| `test_holdout_pythonpath.py` | 123 | v1 holdout subprocess PYTHONPATH plumbing | v2 holdout pipeline is in-process |
| `test_scores_fixture_cohort.py` | 112 | Cohort-aware scoring | cohort dropped |
| `test_calibration_warning.py` | 114 | judge_calibration.py warning path | (Could PORT; small; skip for now) |
| `test_layer1_validate.py` | 105 | L1 validation gate | dropped |
| `test_evolve_config.py` | 106 | v1 evolve config | substrate gone |
| `test_archive_index_tool_health.py` | 91 | `archive_index.py` tool-health checks | archive_index gone; replaced by results.tsv |
| `test_regen_lane_scope.py` | 87 | `regen_program_docs.py` (caused #115) | DELETED per plan |
| `test_harness_session_lock.py` | 99 | Per-fixture session lock | 0 collisions; lock gone |
| `test_holdout_sentinel.py` | 76 | v1 holdout sentinel | v2 has no equivalent sentinel; alert agent replaces |
| `test_variant_identity_manifest.py` | 68 | `variant_manifest.json` (caused #114) | manifest gone; commit-sha replaces |
| `test_env_scrub.py` | 62 | `_score_env` token scrubbing | logic moves into U8 backend.py if at all |
| `test_evaluate_client.py` | 53 | v1 evaluate_variant client integration | substrate gone |
| `test_evaluate_variant_backend_resource.py` | 40 | v1 backend resource selection in evaluate | U2 ports the relevant slice |
| `test_evaluate_variant_target.py` | 41 | v1 evaluate target selection | same |
| `test_post_session_auto_render_gate.py` | 61 | Auto-render after session | render preserved; v1 gate plumbing dies |
| `test_opencode_smoke.py` | 117 | Live opencode invocation smoke | infrastructure smoke; may move to scripts/ |

---

## 4. KEEP_FOR_JUDGES — judge-side tests (9 files)

These test `judges/*` or `autoresearch/judges/*` — explicitly out of Plan
B scope. They stay wherever they are (or move to `tests/judges/`).

| File | LOC | What it tests |
|---|---:|---|
| `test_judges.py` | 180 | call_quality_judge, promotion_judge invocation |
| `test_judge_fixes.py` | 440 | Judge-side fixes (Stream A patched here) |
| `test_judge_calibration.py` | 116 | judge_calibration.py |
| `test_promotion_rule.py` | 363 | promotion_judge contract |
| `test_regression_rollback.py` | 422 | promotion_judge regression detection |
| `test_render_dynamic.py` | 277 | Render judges (RND-1..5) integration |
| `test_charts_svg.py` | 129 | Chart rendering for render judges |
| `test_render_session_bundle.py` | 259 | Render bundle assembly |
| `test_render_x_linkedin_composers.py` | 260 | Render composers for X/LinkedIn lanes |

Note: 4 of these (test_render_*) were also listed in DELETE_WITH_V1
because the v1-side glue dies. **Per-test triage at U14**: tests that
exercise judges directly stay; tests that exercise judges via v1 evolve
loop die.

---

## 5. AMBIGUOUS / split — per-test triage (7 files)

Files where some tests PORT, others DELETE.

| File | LOC | Split rationale |
|---|---:|---|
| `test_holdout_lineage_invariant.py` | 183 | 16 Stream A tests PORT; plus any v1-only invariant checks may DELETE |
| `test_render_dynamic.py` | 277 | Vision-judge contract PORTs; v1-evolve integration DELETEs |
| `test_charts_svg.py` | 129 | SVG-rendering primitives PORT (judges read them); v1-pipeline glue DELETEs |
| `test_evaluate_single_fixture.py` | 201 | The dryrun CLI surface needs an adapter; some tests PORT against the adapter |
| `test_single_fixture_cli.py` | 181 | Same — depends on U13 adapter shape |
| `test_calibration_warning.py` | 114 | Small; warning path may KEEP if judge_calibration verbatim port |
| `test_archive_index_tool_health.py` | 91 | If U7 `tools/inspect.py` covers, port the contract; else DELETE |

---

## 6. U14 git-mv recipe

When U14 fires (`git mv autoresearch/ autoresearch/legacy/`), perform the
matching test moves:

```bash
# Stage 1: PORT — copy contract content into tests/autoresearch_v2/
#  (Files in §2 — most already covered by existing v2 tests; ~8 net new ports)

# Stage 2: KEEP_FOR_JUDGES — move judge-side tests to tests/judges/
git mv tests/autoresearch/test_judges.py tests/judges/
git mv tests/autoresearch/test_judge_fixes.py tests/judges/
git mv tests/autoresearch/test_judge_calibration.py tests/judges/
git mv tests/autoresearch/test_promotion_rule.py tests/judges/
git mv tests/autoresearch/test_regression_rollback.py tests/judges/
# (render-judge subset of test_render_*.py — split during U14)

# Stage 3: DELETE_WITH_V1 — move with autoresearch/ to legacy/
git mv tests/autoresearch tests/autoresearch_legacy

# Stage 4: AMBIGUOUS — split per-test (manual triage during U14)
```

Post-U14 test surface estimate:
- `tests/autoresearch_v2/`: ~3,000-4,000 LOC (current 2,000 + 1,000-2,000 ports)
- `tests/judges/`: ~1,800 LOC (unchanged content, moved)
- `tests/autoresearch_legacy/`: ~9,200 LOC (deletes with v1 in U15 after 30-day retention)

**60-70% deletion ratio** — matches plan estimate.

---

## 7. Risks / unknowns

- **`test_evaluate_single_fixture.py` + `test_single_fixture_cli.py`** —
  depend on the U13 adapter for cli/freddy/fixture/dryrun.py. If U13
  resolves by adding an `autoresearch_v2.tools.evaluate_single_fixture`
  shim, these PORT; if U13 deletes the dryrun command entirely, they
  DELETE. Decision deferred to U13 execution.

- **Render-side tests** — `test_render_*.py` files mix judge-contract
  testing with v1-pipeline glue. Need per-test inspection at U14. Estimate
  50/50 split.

- **`test_lane_registry.py`** — v2 keeps `lane_registry.py` (used by
  src/evaluation per U0 audit). The PORT target should be
  `tests/lane_registry/` (top-level) not `tests/autoresearch_v2/` since
  it survives U14 unchanged.

- **`test_calibration_warning.py`** — small file (114 LOC). Either
  PORT or KEEP_FOR_JUDGES. Inspect during U14.

---

## 8. What this audit does NOT do

- Does not modify any code. Pure classification.
- Does not run the tests to verify which still pass after Stream A.
- Does not handle the `tests/autoresearch_v2/` reverse case (no v1 tests
  there to classify).
- Does not address `tests/audit/`, `tests/judges/`, `tests/freddy/` —
  scope-restricted to `tests/autoresearch/` per Plan B U13a.
