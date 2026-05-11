---
status: complete
created: 2026-05-11
author: claude opus 4.7
purpose: 3 pre-U0 sanity checks on Plan B's most aggressive REJECTs
companion: docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md
---

# Plan B pre-U0 sanity checks

3 checks on the most aggressive REJECTs surfaced during the 2026-05-11 cross-stream review:

1. `select_parent.py` (310 LOC → "1 prompt sentence")
2. `evolve_ops.py` (1,144 LOC → "~0 LOC")
3. L1 preflight (`py_compile` + `bash -n`)

## Risk 3 — L1 preflight catches: ZERO. REJECT CONFIRMED.

Field-corrected `jq` against `autoresearch/archive/lineage.jsonl`:

```
60  canary_aborted
 0  (anything else)
```

Across 147 variants and 60 total discards, zero are L1/syntax/preflight related. The pre-Stream-A audit's claim holds post-Stream-A. **Plan B's strategy is correct: drop the `py_compile` + `bash -n` portion of L1, keep only the critique-manifest piece via `tools/verify_critique_integrity.py`.**

No code change required. Plan B is good as written.

## Risk 2 — evolve_ops.py: file deletes, functions redistribute. NEEDS MIGRATION TABLE.

**Surprise finding:** `autoresearch/archive/v006/run.py` (the file Plan B WRAPS, not rewrites) does NOT import `evolve_ops` at all. All 33 call sites are in `autoresearch/evolve.py`, which IS rejected wholesale.

This means: **v2 does not need to port evolve_ops as a module.** It needs functional equivalents for ~8 of its 32 functions inside v2's own `tools/`. The other ~24 functions either (a) are replaced by git + results.tsv operations, or (b) are theatre defenses that Plan B legitimately rejects.

**Function-by-function migration table:**

| evolve_ops.py function | v2 replacement | Notes |
|---|---|---|
| `_load_latest_lineage` | `git log --format=%H lanes/<lane>/results.tsv` + tail row | Lineage IS git in v2 |
| `_is_allowed_env_key` | `harness/backend.py` env-allowlist helper | Move; ~10 LOC |
| `load_repo_env_defaults` | `harness/backend.py` | Move; thin wrapper |
| `normalize_lane` | inline in tools that need it | One-liner |
| `load_search_config` | move to `lanes/<lane>.md` prompt (config is now declarative) | Per-lane fixtures listed in lane prose |
| `ensure_lane_heads` | `git branch <lane>` per lane | Each lane = git branch in v2 |
| `current_head_variant_id` | `git rev-parse <lane>` | Replaces variant_id-as-string with commit-SHA |
| `set_current_head` | `git update-ref refs/heads/<lane>` | Atomic via git |
| `baseline_seeded` | `git log --oneline lanes/<lane>/ \| wc -l > 0` | Trivial check |
| `holdout_configured` | env-var check in `tools/score_holdout.py` | ~5 LOC |
| `promotion_reason` | column in `results.tsv` | Append "reason=<text>" on keep |
| `variant_has_search_metrics` | `git show <sha>:lanes/<lane>/results.tsv` + grep | Trivial |
| `_holdout_composite` | `tools/score_holdout.py` returns it directly | Replaced |
| `_per_fixture_scores` | `tools/score_holdout.py` per-fixture rows | Replaced |
| `emit_saturation_cycle_events` | `tools/alert_check.py` reads last N rows | Saturation is a pattern over results.tsv |
| `is_promotable` | column in `results.tsv` | "eligible=true/false" |
| `_auto_rollback_enabled` | env var read in `tools/alert_check.py` | ~3 LOC |
| `record_head_score` | `results.tsv` append (already happens) | Trivial |
| `check_and_rollback_regressions` | `tools/alert_check.py` flags; `git reset --hard <previous-keep>` for the rollback | Alert + git, no special module |
| `_collect_report_artifacts` | `tools/render_report.py` walks `lanes/<lane>/` | Already in scope for render slim |
| `mark_promoted` | column in `results.tsv` + git commit message | Trivial |
| **`promote_atomic`** | **`git commit + git push origin <lane>`** | Atomic by git; this is the most load-bearing function and v2's design depends on git doing this correctly |
| `previous_promoted_variant` | `git log <lane> --grep="keep" -1 --format=%H` | Trivial |
| `holdout_suite_id` | constant per-lane in lane prose | Declarative |
| `finalize_candidate_ids` | not needed (sequential v2 has no cohort to finalize) | DROPPED |
| `finalize_status` | not needed (cohort) | DROPPED |
| `best_finalized_variant` | not needed (cohort) | DROPPED |
| `write_finalized_shortlist` | not needed (cohort) | DROPPED |
| **`prepare_meta_workspace`** | **DROPPED — this IS the chmod 0444 + hash check Plan B rejects** | 0 ScopeViolations in 147 variants justifies |
| `write_lane_context` | replaced by `lanes/<lane>.md` (declarative) | Static text |
| **`sync_meta_workspace`** | **DROPPED — sibling of prepare_meta_workspace** | Same justification |
| `variant_in_lineage` | `git rev-parse --verify <sha>` | Trivial |

**Summary:**
- 8 functions need a real v2 implementation (in `harness/` or `tools/`), totaling ~50 LOC across v2's tools
- 18 functions become git/jq one-liners or column reads (~0-5 LOC each)
- 4 functions DROPPED (cohort logic, theatre defenses)
- 2 functions inline as helpers

**Total real v2 LOC absorbing evolve_ops's substance: ~50-80 LOC.** Plan B's "evolve_ops.py → ~0 LOC" is accurate at the file level, ~50 LOC at the substance level.

**Recommended Plan B addition:** add this table to U13 or as an inline note in U2-U4 (the tools that absorb the most substance). Without it, an implementer reading "evolve_ops.py → 0" could wrongly delete the substance.

## Risk 1 — select_parent.py: prompt-sentence drafted + dry-run

**Plan B's claim:** 310 LOC of `select_parent.py` → 1 prompt sentence in `autoresearch.md`.

**Audit evidence (2026-05-11):**
- v071 (composite 0.0) picked as parent ONCE; cost ~18h compute + $200-300 in regression cascade. Anti-drift floor (commit `7469dcd`) was shipped to prevent recurrence.
- v175, v176, v177 all picked v007 (top-1) post-fix.

**Draft prompt sentence (v1, ~80 words):**

> *To pick the next parent: read the last 10 rows of `lanes/<current-lane>/results.tsv`. (1) Only consider variants whose composite ≥ (top-1 composite × 0.7) — that's the anti-drift floor. (2) Prefer the highest composite. (3) If the top-1 has been picked as parent 3+ times in the last 5 iterations and the resulting mutations didn't beat top-1's composite, fall to the second-highest as an exploration probe. (4) Tiebreak by recency. Write the picked variant's SHA + your one-line rationale to `attempts/<timestamp>-parent.txt`.*

**Dry-run against v071 incident (the bug `7469dcd` fixed):**
- Top-1 = v007 (composite 7.82). v071 had composite 0.0.
- Anti-drift floor: 7.82 × 0.7 = 5.47. v071's 0.0 is below floor. **REJECTED. ✓**
- The 310 LOC bug is closed by one clause.

**Dry-run against v175/v176/v177 (post-fix):**
- v175 picks v007 ✓ (highest composite, picked 0 times so far)
- v176 picks v007 ✓ (highest composite, picked 1 time so far)
- v177 picks v007 ✓ (highest composite, picked 2 times so far)
- v178 (hypothetical): if v007 picked 3 times AND none of v175-v177 beat v007 → exploration probe = v009. **This is a slight divergence from current code** (which would keep picking v007). It's probably good — forces exploration when exploitation is plateauing. But worth noting as a behavioral diff.

**Open questions on the prompt sentence:**

1. **Hard-coded numerics** (0.7 floor, 3-picks-in-5, etc.) — these are magic numbers. Should v2 expose them as env vars (e.g., `AUTORESEARCH_ANTI_DRIFT_FLOOR=0.7`) or bake them into prose? Recommend: bake into prose for v1; promote to env vars only if U10 spike reveals tuning need.

2. **"Rationale" output** — the current code stores rationale in `meta.md` template. The prompt sentence asks the LLM to write rationale to `attempts/<timestamp>-parent.txt`. This is per karpathy pattern (`autoresearch.jsonl`'s `asi` field). Good fit.

3. **LLM might mis-count "3 picks in 5 iterations"** — counting is exactly the kind of thing LLMs sometimes miss. v2 could pre-compute the count in `results.tsv` (column: `parent_picks_in_last_5_iters`) so the prompt just reads it.

**Recommendation:** ship the prompt sentence as drafted; verify in U9 (geo lane prose). If U10 spike shows the LLM mis-picks parents, add a `parent_picks` column to `results.tsv` (~5 LOC change in `tools/log_experiment.py`). Don't pre-emptively engineer for it.

**Verdict: REJECT confirmed.** 310 LOC of select_parent.py legitimately reduces to ~80 words of prompt + 1 column in results.tsv (if needed). Risk: LLM mis-counts; mitigated by U10 catching the error.

## Summary

| Risk | Status | Action needed |
|---|---|---|
| 1. select_parent → 1 prompt sentence | ✅ Drafted + dry-run passes | Optional: add `parent_picks_in_last_5` column to `results.tsv` IF U10 surfaces miscounts |
| 2. evolve_ops → ~0 LOC | ⚠️ File deletes, substance redistributes | **Add the function migration table above to Plan B U13** (or as inline note in U2-U4) |
| 3. L1 preflight drop | ✅ Verified: 0 catches in 147 variants | No action |

**Net pre-U0 effort:** ~15 min to add the evolve_ops migration table to Plan B. Then U0 is clear to start.
