# Plan — Autoresearch evolution-loop fixes (Phase A + B)

## Context

The autoresearch evolutionary search system has burned ~$240–680 across 8 variants in two runs (Mac v001-v006, Pi v006-v008) with **0 formally validated promotions**. Three parallel diagnostic subagents found 17 distinct issues; ~half are *structurally invalidating* — they make the loop produce motion without validation, and they make scores gameable in ways the meta-agent has demonstrably exploited (Pi v007's neutered `completion_guard` + `stall_limit 5→15`).

The user has authorized fixing Phase A (structural) + Phase B (feedback wiring) together — 9 fixes total. Phases C/D (cost reduction, deeper architecture) are deferred to a later batch once A+B prove the loop is honest.

**Expected outcome:** the next evolution run produces honestly-scored variants where (a) the holdout actually validates promotion candidates, (b) the meta-agent cannot edit enforcement code to lower its own bar, (c) critic + alert + parent-selection signals reach the next mutation as feedback, and (d) crashes fail closed instead of fail open.

**Source diagnostics in this conversation:**
- 3 prior subagent reports (variant trajectory, architecture audit, cost+scoring audit)
- 2 follow-up Explore agents (edit-scope mechanics, prompt-template internals, scoring formula, crash patterns)
- Pi snapshot at `~/Documents/pi-snapshots/pi-evolution-2026-04-30/`
- Mac repo at `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy`

## Issue inventory (this batch — 10 items)

| # | Severity | Issue | Touch points |
|---|---|---|---|
| **A1** | P0 | `EVOLUTION_HOLDOUT_MANIFEST` env var unset → holdout never runs | `scripts/agent-launcher.sh:57-63`, operator's `~/.config/gofreddy/judges.env` |
| **A2** | P0 | Critic subprocess crash treated as `verdict: no-change` (fail-open) | `autoresearch/program_prescription_critic.py:296-426` (especially `:417`), `autoresearch/evolve.py:1971-1985` |
| **A5** | P0 | Meta-agent edit scope unconstrained → can mutate `workflows/*.py` enforcement code | `autoresearch/lane_registry.py:22-38` (LaneSpec), `autoresearch/archive_index.py:231-288` (`prepare_meta_workspace`) |
| **A6** | P0 | `cmd_promote --undo` path bypasses `is_promotable` gate | `autoresearch/evolve.py:2070-2082` |
| **A7** | P0 | `_outer_pass_from_score` returns binary 0/1 → `pass_rate_delta` structurally biased | `autoresearch/evaluate_variant.py:1004-1011` (and call site `:1250`) |
| **A12** | P0 | Pi `workflows/*.py` already contaminated (lost Mac-side hardening at bootstrap) | Pi `autoresearch/workflows/{geo,competitive,monitoring,storyboard}.py` |
| **B3** | P1 | Critic output (`critic_reviews.md`) is write-only — meta-agent never reads parent's critique | `autoresearch/evolve.py:1901-1916`, `autoresearch/archive/current_runtime/meta.md` |
| **B4** | P1 | Alerts (`metrics/alerts.jsonl`) are write-only — drift signal never reaches mutation | `autoresearch/evolve.py:1901-1916`, `meta.md` |
| **B9** | P1 | `EVOLUTION_SELECTION_RATIONALE` env var set but not allowlisted for claude meta-agent | `autoresearch/evolve.py:76-80` (`_CLAUDE_ENV_KEYS`), `meta.md` |
| **A0** | P0 | First-of-lane auto-promotes regardless of holdout (no baseline → eligible=True) | `autoresearch/evaluate_variant.py:2664-2665` |

---

## Implementation by fix

### A1. Wire `EVOLUTION_HOLDOUT_MANIFEST` permanently + fail-loud on missing manifest

**Problem:** `scripts/agent-launcher.sh:57-63` does `if [ -r "$judges_env" ]; then set -a; . "$judges_env"; set +a; fi` — silently skips when file missing. If operator runs `evolve.sh run ...` directly, env var is unset and `evolve.py:826-833` hard-exits (preflight catches it). But if operator inherits a partially-populated tmux env, `_load_holdout_manifest` returns None silently (`evaluate_variant.py:296-307`). Both Mac and Pi runs took this silent path.

**Fix:**
1. **`scripts/agent-launcher.sh`:** change the `[ -r ]` block to:
   - If `judges_env` file is missing/unreadable, print `ERROR: judges env not found at $judges_env — autoresearch validation gate cannot run` and `exit 1` unless `AUTORESEARCH_ALLOW_NO_JUDGES_ENV=1`.
   - After sourcing, sanity-check that `EVOLUTION_HOLDOUT_MANIFEST` is non-empty AND points to a readable file. Error if not.
2. **`~/.config/gofreddy/judges.env`** (operator-side, not in repo): ensure it `export EVOLUTION_HOLDOUT_MANIFEST=$HOME/.config/gofreddy/holdouts/holdout-v1.json` is present. Verify the file at `~/.config/gofreddy/judges.env` actually has this line (read it during implementation to confirm).
3. **`autoresearch/evaluate_variant.py:296-307`** (`_load_holdout_manifest`): when env var is set but file missing, raise `RuntimeError` instead of returning None silently.

**Why this layer:** the launcher is the operator-facing entry point. Failing loud here avoids the multi-layer silent-skip we observed. `evaluate_variant._load_holdout_manifest` is the second line of defense.

**Test:** delete `~/.config/gofreddy/judges.env` temporarily → `agent-launcher.sh` should error with the new message. Restore + run → preflight should report holdout manifest path resolved + readable.

---

### A2. Critic crash → variant rejection (fail-closed)

**Problem:** `program_prescription_critic.py:417` returns `{"verdict": "no-change", "reasoning": "Critic subprocess exited {code}"}` when subprocess crashes — i.e., critic crash is indistinguishable from critic saying "no concerns." `evolve.py:1981-1985` wraps the call in try/except that logs and continues. Pi v007's contamination slipped through this path.

**Fix:**
1. **`program_prescription_critic.py:417`** — change verdict on subprocess crash from `"no-change"` to `"error"`. Update the `_CRITIC_VERDICT_TOKENS` whitelist (line 48) to include `"error"`.
2. **`autoresearch/evolve.py:1971-1985`** — after the call:
   ```python
   critic_results = critique_all_programs(...)
   if any(r["verdict"] == "error" for r in critic_results):
       failed = [r for r in critic_results if r["verdict"] == "error"]
       # Mark variant as discarded with reason
       _mark_variant_discarded(variant_dir, reason=f"critic_unavailable: {failed[0]['reasoning'][:200]}")
       continue  # next variant or graceful exit
   ```
3. **Honor `EVOLVE_SKIP_PRESCRIPTION_CRITIC=1` escape hatch** (already exists at `evolve.py:1971`) — if set, skip the critic entirely. This is the operator-controlled bypass for known-broken-critic scenarios.

**Existing pattern reused:** the fixture-eval failure pattern at `evaluate_variant.py:1042-1054` (return structured-failure record, downstream sees the failure flag). We're adopting the same shape for critic.

**Test:** simulate a critic crash (point to a non-existent backend binary); verify that the variant gets discarded instead of proceeding.

---

### A5. Lane edit-scope: workflow enforcement code is read-only

**Problem:** Geo lane owns `workflows/geo.py` (`lane_registry.py:54`). Pi v007 mutated it: `completion_guard → return None, None` and `stall_limit 5 → 15`. Lane ownership lets the meta-agent edit anything inside the owned tree.

**Fix:**
1. **`autoresearch/lane_registry.py:22-38`** — add to `LaneSpec` dataclass:
   ```python
   readonly_subprefixes: tuple[str, ...] = ()
   # Subprefixes within the lane's owned tree that the meta-agent may
   # READ but not EDIT. Workflow enforcement code (completion_guard,
   # stall_limit, count_findings, etc.) goes here so a mutation can't
   # game the eval bar.
   ```
2. **`lane_registry.py:45-146`** — for each lane spec, set:
   ```python
   readonly_subprefixes=("workflows/{lane}.py",)  # or similar pattern
   ```
   Specifically:
   - geo: `("workflows/geo.py", "workflows/session_eval_geo.py")`
   - competitive: `("workflows/competitive.py", "workflows/session_eval_competitive.py")`
   - monitoring: `("workflows/monitoring.py", "workflows/session_eval_monitoring.py")`
   - storyboard: `("workflows/storyboard.py", "workflows/session_eval_storyboard.py")`
   - core: `()` (core is meta-only, no workflow enforcement)
3. **`autoresearch/archive_index.py:277-287`** (`prepare_meta_workspace`) — after `path_owned_by_lane()` filter, add a second filter:
   ```python
   # If path matches any readonly_subprefix, copy it but flip permissions to 0444.
   # Meta-agent's tools will still try to write but git-diff captures any change.
   for subprefix in lane_spec.readonly_subprefixes:
       if rel_path.startswith(subprefix):
           os.chmod(target, 0o444)
   ```
4. **`autoresearch/archive_index.py:303-313`** (`sync_variant_workspace`) — defense-in-depth: when syncing back, reject any change to a `readonly_subprefix` path:
   ```python
   for rel_path, source_path in source_files.items():
       for subprefix in lane_spec.readonly_subprefixes:
           if rel_path.startswith(subprefix):
               # Compare hash to original; if changed, raise
               if hash(source_path) != hash(original_target):
                   raise ScopeViolation(f"meta-agent edited readonly file: {rel_path}")
   ```

**Why both layers:** Pre-prompt (`prepare_meta_workspace`) prevents the meta-agent from writing in the first place via filesystem permissions. Post-diff (`sync_variant_workspace`) catches any case where the meta-agent worked around the chmod (it could `chmod +w` first). Defense-in-depth.

**Existing pattern reused:** `LANE_WORKSPACE_KEEP_FILES` (`archive_index.py:49`) is a similar allowlist concept; we're adding a complementary readonly-list.

**Test:** seed a meta-agent invocation that tries to edit `workflows/geo.py`; verify the change is rejected at sync time and the variant is marked as scope-violation.

---

### A6. Block `cmd_promote --undo` when target variant not promotable

**Problem:** `evolve.py:2070-2082` calls `evolve_ops.mark_promoted(...)` on the previous variant without checking `is_promotable`. So `--undo` can roll back to a variant that was never validated. The main promote path at `:2128-2135` IS gated correctly.

**Fix:**
**`autoresearch/evolve.py:2070-2082`** — before calling `mark_promoted`:
```python
if config.promote_undo:
    prev = evolve_ops.previous_promoted_variant(archive_dir)
    if prev is None:
        sys.exit("nothing to undo")
    if not evolve_ops.is_promotable(archive_dir, prev, config.lane):
        sys.exit(
            f"ERROR: cannot undo to {prev} — variant is not promotable. "
            "Run holdout against it first or pass --force."
        )
    evolve_ops.mark_promoted(archive_dir, prev, timestamp)
```

Add `--force-undo` CLI flag for operator override (rare manual interventions). Default off.

**Test:** create an artificial state where the prior variant has `eligible_for_promotion: false`; `evolve.sh promote --undo` should error.

---

### A7. Granular `_outer_pass_from_score`

**Problem:** `evaluate_variant.py:1004-1011` returns `1.0 if (structural_passed and score >= 0.5) else 0.0`. With per-fixture scores 7.65–8.10 (0-10 scale), outer_pass is always 1.0 → `mean_pass_rate_delta = outer - inner` is structurally biased to +0.2~+0.5 when inner is 0.5-0.8. The "+0.317 smoking gun" was partly real, partly structural.

**Fix:**
**`autoresearch/evaluate_variant.py:1004-1011`** — change to:
```python
def _outer_pass_from_score(score: float, structural_passed: bool, max_score: float = 10.0) -> float:
    """Continuous outer-judge pass-confidence on [0.0, 1.0].

    Was binary (1.0 if score>=0.5 else 0.0) which caused mean_pass_rate_delta
    to be structurally biased positive when fixture scores live on a 0-10
    scale. Granular form lets pass_rate_delta meaningfully detect calibration
    drift between inner critic and outer judge.
    """
    if not structural_passed:
        return 0.0
    return max(0.0, min(1.0, score / max_score))
```

**Verification of downstream:** Subagent 4 confirmed only call site is `evaluate_variant.py:1250` (`_correlation_fields`); `outer_pass_rate` is stored as a continuous metric, no `>= 0.5` thresholding downstream. Safe to change.

**Important:** old composite scores (v001-v008) become non-comparable to new ones because the metric definition changed. Document this in the lineage entry's `notes` field on the next variant. Don't try to backfill — let v009+ start a fresh comparison series with honest math.

**Test:** unit test: `_outer_pass_from_score(7.95, True) == 0.795`, `_outer_pass_from_score(0.0, True) == 0.0`, `_outer_pass_from_score(11.0, True) == 1.0` (clipping).

---

### A12. Reset Pi `workflows/*.py` to Mac-side good versions

**Problem:** Pi's `autoresearch/workflows/{geo,competitive,monitoring,storyboard}.py` already contain the neutered `completion_guard` and `stall_limit=15` — present *before* Pi v007 ran, lost during Pi bootstrap from a stale baseline. The Mac archive `v006/workflows/geo.py` has the GOOD guard with the audit comments.

**Fix:** This is preflight cleanup, not code change. Steps:
1. From Mac: `scp autoresearch/archive/v006/workflows/{geo,competitive,monitoring,storyboard}.py pi:projects/gofreddy/autoresearch/workflows/` — or equivalent rsync. (Verify these files actually exist on Mac and have the GOOD versions before copying — earlier subagent report confirmed Mac v006 has them.)
2. On Pi: verify `stall_limit=5` and `completion_guard` returns `("RUNNING", reason)` when no deliverables.
3. On Pi: `git status` should show modifications to these files. Operator decides whether to commit them or revert (depends on whether Pi tree is meant to track main).

**Alternative if Mac v006 doesn't have the good versions:** check git history for the commits that introduced `completion_guard` originally; those are the canonical source.

**Test:** on Pi, after reset, run a single dry-run variant and verify `completion_guard` actually downgrades a no-deliverables session to RUNNING.

---

### B3. Wire critic output into next-gen meta-agent prompt

**Problem:** `critic_reviews.md` is written by the critic and read by *no one*. Meta-agent's prompt never sees parent's critique. So a critic flag on cycle N has zero effect on cycle N+1's mutation.

**Fix:**
1. **`autoresearch/evolve.py:1895-1900`** (around where `eval_digest_path` is set):
   ```python
   parent_critic_path = parent_dir / "critic_reviews.md"
   parent_critic_review = (
       parent_critic_path.read_text()
       if parent_critic_path.exists()
       else "No critic review available — first variant or critic crashed."
   )
   ```
2. **`autoresearch/evolve.py:1901-1916`** — add to the placeholder substitution:
   ```python
   rendered = rendered.replace("{parent_critic_review}", parent_critic_review)
   ```
3. **`autoresearch/archive/current_runtime/meta.md`** — add a section near the top (after the lane/iteration context):
   ```markdown
   ## Parent variant's critic review

   The previous variant in this lane was reviewed by the program-prescription
   critic. Findings below — address them or explicitly justify why they don't
   apply to your mutation.

   {parent_critic_review}
   ```

**Why:** the critic does substantive analysis (Pi v008's review caught the over-prescriptive bracket-tag taxonomy that turned out to break 2/3 fixtures — verbatim quote from subagent 1). Surfacing this to the next mutation closes the feedback loop.

**Pitfall:** critic_reviews.md size — typically <10KB. Well within prompt budget. Don't add a length cap unless we hit context limits.

**Test:** seed `critic_reviews.md` with a known string; render meta-agent prompt; verify the string appears.

---

### B4. Wire alerts into next-gen meta-agent prompt

**Problem:** `compute_metrics.check_alerts` writes to `metrics/alerts.jsonl`. Meta-agent never sees these flags.

**Fix:**
1. **`autoresearch/evolve.py:1895-1900`**:
   ```python
   alerts_path = archive_dir / "metrics" / "alerts.jsonl"
   recent_alerts = ""
   if alerts_path.exists():
       lines = alerts_path.read_text().strip().splitlines()
       # Last 5 alerts for this lane
       lane_alerts = [
           line for line in lines
           if json.loads(line).get("lane") == config.lane
       ][-5:]
       recent_alerts = "\n".join(lane_alerts) or "No alerts recorded for this lane."
   else:
       recent_alerts = "No alerts file."
   ```
2. **Substitution + meta.md section** — same pattern as B3:
   ```python
   rendered = rendered.replace("{recent_alerts}", recent_alerts)
   ```
   ```markdown
   ## Recent drift / overfitting / collapse alerts (last 5 in this lane)

   {recent_alerts}
   ```

**Test:** seed alerts.jsonl with 3 entries; verify they render in the meta-agent prompt with most-recent-last.

---

### B9. Selection rationale into meta-agent prompt

**Problem:** `evolve.py:1825-1828` sets `EVOLUTION_SELECTION_RATIONALE` env var but `_CLAUDE_ENV_KEYS` (line 76-80) doesn't allowlist it for the claude meta-agent. So claude never sees it.

**Fix:**
1. **`autoresearch/evolve.py:76-80`** — add `"EVOLUTION_SELECTION_RATIONALE"` to `_CLAUDE_ENV_KEYS`.
2. **`autoresearch/evolve.py:1895-1900`** — also pass into placeholder for explicit visibility (env var is implicit; placeholder is explicit):
   ```python
   selection_rationale = os.environ.get("EVOLUTION_SELECTION_RATIONALE", "(no rationale provided)")
   ```
3. **Substitution + meta.md section:**
   ```python
   rendered = rendered.replace("{selection_rationale}", selection_rationale)
   ```
   ```markdown
   ## Why this parent was selected for mutation

   {selection_rationale}

   Read this carefully. Your mutation should respond to the rationale's hypothesis —
   if the rationale says "v006 had highest CQ-DATA but lowest GEO-3, probe whether
   stronger competitive evidence helps," then your mutation should target
   competitive evidence, not random refactoring.
   ```

**Test:** set `EVOLUTION_SELECTION_RATIONALE=test-string` in env; render meta-agent prompt; verify it appears.

---

### A0. First-of-lane should require holdout

**Problem:** `evaluate_variant.py:2664-2665` returns `eligible=True` when `baseline_entry is None`. So the very first variant in any lane auto-promotes, holdout-or-no.

**Fix:**
**`autoresearch/evaluate_variant.py:2664-2665`** — change first-of-lane bypass:
```python
if baseline_entry is None:
    # First variant in this lane: cannot auto-promote without holdout
    # validation. The holdout score IS the baseline.
    if not holdout_metrics.get("ran"):
        return False, "first_variant_holdout_required"
    if holdout_metrics.get("composite", 0.0) <= 0.0:
        return False, "first_variant_holdout_zero_score"
    return True, "first_variant_holdout_passed"
```

**Test:** force a fresh-lane scenario; verify variant is not auto-promoted before holdout.

---

## Files to modify (consolidated)

| File | Fixes touching it |
|---|---|
| `scripts/agent-launcher.sh` | A1 |
| `~/.config/gofreddy/judges.env` (operator-side) | A1 (verify content) |
| `autoresearch/program_prescription_critic.py` | A2 |
| `autoresearch/evolve.py` | A2, A6, B3, B4, B9 (lines 76-80, 1895-1916, 1971-1985, 2070-2082) |
| `autoresearch/lane_registry.py` | A5 (LaneSpec + 5 lane definitions) |
| `autoresearch/archive_index.py` | A5 (prepare_meta_workspace + sync_variant_workspace) |
| `autoresearch/evaluate_variant.py` | A1 (silent-skip), A7 (outer_pass), A0 (first-of-lane) |
| `autoresearch/archive/current_runtime/meta.md` | B3, B4, B9 (template additions) |
| Pi `~/projects/gofreddy/autoresearch/workflows/{geo,competitive,monitoring,storyboard}.py` | A12 (one-time reset) |

## Existing utilities reused

- `_load_holdout_manifest` (`evaluate_variant.py:296-307`) — extend for fail-loud (A1)
- `_call_critic` retry framework (`program_prescription_critic.py:339-399`) — leave intact; only change final-failure path (A2)
- Fixture-eval failure pattern (`evaluate_variant.py:1042-1054`) — adopt for critic-crash semantics (A2)
- `path_owned_by_lane` + `LaneSpec.path_prefixes` (existing) — extended via new field, not replaced (A5)
- `LANE_WORKSPACE_KEEP_FILES` (`archive_index.py:49`) — complemented by readonly logic (A5)
- `is_promotable` (`evolve_ops.py:328-467`) — reused as gate at undo path (A6)
- meta.md `str.replace()` substitution (`evolve.py:1901-1916`) — same mechanism, three new placeholders (B3, B4, B9)

## Sequencing & dependencies

Fixes are mostly independent. Recommended order to keep verification clean at each step:

1. **A12** (Pi reset) — preflight; ensures next test runs against clean code.
2. **A1** (holdout env var) — verifiable in isolation by running preflight only.
3. **A7** (outer_pass) — pure scoring change; unit-testable.
4. **A2** (critic fail-closed) — depends on nothing else.
5. **A5** (lane edit scope) — adds new `LaneSpec` field; touches workspace prep + sync.
6. **A6** (undo gate) + **A0** (first-of-lane gate) — pure gating logic.
7. **B3, B4, B9** (prompt wiring) — last because they're additive and safe; verifiable by rendering a meta-agent prompt and grepping for the new sections.

## Verification

End-to-end checklist before declaring fixes shipped + ready for next run:

1. **Preflight on Pi:** `evolve.sh preflight` (or equivalent) reports holdout manifest path resolved + readable. Without `EVOLUTION_HOLDOUT_MANIFEST` set, `agent-launcher.sh` errors with the new message.
2. **Unit tests** (add to `tests/autoresearch/`):
   - `test_outer_pass_from_score_granular()` — covers binary→continuous transition
   - `test_first_of_lane_requires_holdout()` — covers A0 bypass closed
   - `test_critic_crash_marks_variant_discarded()` — covers A2
   - `test_undo_blocks_when_not_promotable()` — covers A6
   - `test_lane_readonly_subprefixes_reject_workflow_edits()` — covers A5 sync-time rejection
3. **Integration test (synthetic):** craft a variant where meta-agent's diff modifies `workflows/geo.py`; verify `sync_variant_workspace` raises `ScopeViolation`.
4. **Prompt rendering test:** render a meta-agent prompt with seeded `critic_reviews.md` + `alerts.jsonl` + `EVOLUTION_SELECTION_RATIONALE`; verify all three sections appear in the rendered prompt.
5. **One-cycle dry run on Pi:** run a single variant on geo lane with `--max-generations 1`. Verify:
   - Holdout actually runs (lineage entry has `holdout_metrics.ran: true`)
   - `eligible_for_promotion` reflects the holdout outcome (not `false, reason: holdout_required`)
   - No `workflows/*.py` modifications appear in the variant diff
   - `mean_pass_rate_delta` is now in plausible range (~0.0 - 0.1) instead of structurally +0.3
   - meta-agent prompt (saved to a temp file before run) contains the new sections
6. **Cost telemetry sanity:** confirm wall_time + iteration log sizes are within expected bounds (should match prior runs; we're not changing the eval-target model in this batch).

## Rollback plan

Each fix is in a separate file or section, so individual reverts are trivial:
- A1: revert `agent-launcher.sh` and the `evaluate_variant.py:_load_holdout_manifest` change
- A2: critic_returns "no-change" semantics — single-line revert in `program_prescription_critic.py:417`
- A5: revert `LaneSpec`, all 5 lane definitions, the `prepare_meta_workspace` + `sync_variant_workspace` filters
- A6: revert single conditional block in `cmd_promote --undo`
- A7: revert `_outer_pass_from_score` to binary
- A12: re-apply the bad versions (preserved in Pi git history)
- B3/B4/B9: remove `replace()` calls and meta.md sections; remove allowlist entry

If a fix breaks the loop catastrophically, set `EVOLVE_SKIP_PRESCRIPTION_CRITIC=1` (existing escape hatch) to bypass the critic chain entirely while diagnosing.

## Out of scope (deferred to a follow-up batch)

The other 7 fixes from the diagnostic — Phase C (cost reduction) and the deeper architecture issues — are explicitly NOT in this batch:
- #10 cohort_size 3→5
- #11 token telemetry in lineage
- #13 reasoning_effort high→medium
- #14 skip outer-judge on `produced_output=False`
- #15 hardcoded ROLLBACK_DRY_RUN_UNTIL_ISO
- #16 OPENCODE_MAX_RETRIES cap
- #17 implement `custom_validate` for at least geo lane

These should be done after we have one clean cycle confirming A+B made the loop honest. Otherwise we're optimizing a system whose math we just changed.

## Critical files (paths for executor)

- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/evolve.py`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/evaluate_variant.py`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/program_prescription_critic.py`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/lane_registry.py`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/archive_index.py`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/archive/current_runtime/meta.md`
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/scripts/agent-launcher.sh`
- `/Users/jryszardnoszczyk/.config/gofreddy/judges.env` (operator-side, verify only — do not commit)
- `pi:projects/gofreddy/autoresearch/workflows/{geo,competitive,monitoring,storyboard}.py`

## Estimated effort

| Phase | Items | Hours |
|---|---|---|
| Phase A (structural) | A1, A2, A5, A6, A7, A12, A0 | ~3.5 |
| Phase B (feedback wiring) | B3, B4, B9 | ~1.5 |
| Tests + verification | All above | ~1.5 |
| **Total** | 10 fixes | **~6.5 hours** |
