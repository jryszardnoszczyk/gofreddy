---
status: complete
created: 2026-05-11
author: claude opus 4.7 (U0a pre-flight agent)
purpose: Plan B U0a — deliberate-but-stale degradation audit
companion: docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md
---

# Autoresearch stale-degradation audit

Targeted sweep for the bug class Stream A's PR #60 named: a code comment
declares a degradation "deliberate / temporary / reverted / one-shot" but the
revert never landed and the degraded path is still hot.

## 1. Summary

| Class | Count |
|---|---|
| **STILL_LIVE** (degradation active, comment understates risk, candidate for v2 refusal) | **4** |
| **SUPERSEDED** (comment is stale; revert/migration partially or fully landed; delete or update doc) | **3** |
| **BENIGN** (comment accurately documents an intentional design choice) | 11 |

### STILL_LIVE priority queue (highest → lowest)

1. **`autoresearch/evaluate_variant.py:560-565` — grace-manifest unconditional bypass.** Any variant manifest with `{"grace": true}` skips all critique-prompt hash enforcement. The docstring at line 527 calls this "intended for one-shot backfill via `rebuild_manifests.py`" — but it is the only signed-off path through L1 for *anything* that writes `grace=true`, including future hand-written / agent-tampered manifests. This is the exact "comment says one-shot, code is permanent backdoor" pattern. **Stream A class. Should be a small dedicated fix plan, not absorbed into U1.**
2. **`cli/freddy/commands/evaluate.py:128-232` — `_handle_legacy_batch_critique` axis-collapse is still default.** Stream A's PR #60 added the per-criterion fix but gated it behind `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=1`. Without that env-var, every v006-style batch critique still collapses 8 distinct axes to one verdict broadcast as identical scores. Documented in the docstring as "Granularity is lost" — the comment is honest but the default has not been flipped. **Already on Stream A's queue; flag for v2 inheritance refusal until flipped.**
3. **`autoresearch/evaluate_variant.py:2534-2548` — "Temporary compatibility aliases" with no scheduled removal.** Comment says "removed when evolve.sh heredocs migrate to evolve_ops.py (Unit 11 / R15)". The heredoc migration appears complete (`grep` finds no `_load_private_finalize_result` callers in `evolve.sh`), but `evolve_ops.py:987,990` still imports the aliases. Renaming the 2 call sites would let the aliases be deleted. Comment promises "Temporary"; in practice this is a permanent indirection layer.
4. **`autoresearch/evolve.py:260-269 + 2549-2556` — `--force-undo` CLI flag is a no-op but help text still claims behavior.** The `--undo` gate was simplified (commit f39a7de3, 2026-05-06): `previous_promoted_variant` raises `SystemExit` itself when no eligible target, so the operator override is dead. Inline comment at 2555-2556 admits "`--force-undo` is preserved as a no-op for backward compat with operator scripts", but the argparse help at 263-268 still describes it as "Allow --undo to roll back to a non-promotable variant. Default off — A6 ... gates undo on is_promotable. Operator override only." That help is now lying. Either delete the flag or rewrite the help.

---

## 2. STILL_LIVE findings (detail)

### S1. Grace-manifest bypass — `autoresearch/evaluate_variant.py:560-565`

```python
527:     for one-shot backfill via ``autoresearch/scripts/rebuild_manifests.py``;
528:     fresh clones written by ``evolve.py`` always carry a strict manifest.
...
560:     if bundled.get("grace") is True:
561:         # Grace manifest: pre-Unit-7-era variant backfilled by
562:         # rebuild_manifests.py. Pass through without enforcement; we
563:         # explicitly do not attempt to detect retroactive tampering of
564:         # variants that were already on disk before R-#13 landed.
565:         return True
```

Blame: `9a2d808e` J Ryszard Noszczyk 2026-04-22 22:43 (squash-merge of plan 007).

**Recommended action:** dedicated Stream-A-style fix plan. Either (a) gate the
grace path behind a positive env-var (`AUTORESEARCH_ALLOW_GRACE_MANIFEST=1`)
defaulting OFF, so production paths fail-loud on grace manifests; or (b) bind
the grace exception to a specific allow-list of pre-Unit-7 variant IDs
(stored alongside the manifest schema). The docstring's "one-shot backfill"
framing made it sound bounded, but in code it's an open door — any future
variant that lands on disk with `{"grace": true}` (whether legitimately
backfilled or hand-written by an agent / operator running
`rebuild_manifests.py --force-grace` later) passes L1 with zero hash check.

Triage: the function name `_check_critique_manifest` advertises strict
verification; the grace branch silently subverts it. This is the
**worst-of-pattern**: the docstring calls the exception "one-shot" but the
gate is general, and no schema-level enforcement prevents arbitrary future
manifests from claiming grace. **v2 wrappers should refuse this path** —
either inherit the strict check only, or carry the allow-list. Distinct from
the U2/U3 grease-removal work because it's a security-shaped invariant, not
a substrate-simplification.

### S2. Legacy batch-critique axis-collapse is still default — `cli/freddy/commands/evaluate.py:128-232`

```python
128: def _handle_legacy_batch_critique(criteria: list[dict]) -> None:
...
141:     Granularity is lost (no per-criterion scoring) but session completes,
142:     structural gates pass, and we avoid timeout cascades. A future
143:     /invoke/critique-batch endpoint could restore per-criterion scoring.
...
215:     # Stream A axis-collapse fix (gated by AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE).
216:     # When the judge returns a `per_criterion` array covering every criterion_id,
217:     # build distinct per-criterion scores from it. Otherwise fall back to the
218:     # legacy single-verdict broadcast so older judge deployments keep working.
219:     per_criterion_results = _per_criterion_results(verdict, criterion_ids) if _axis_collapse_fix_enabled() else None
```

Blame: `f3738399` jryszardnoszczyk 2026-04-25 (original handler); axis-collapse
gate added by Stream A PR #60.

**Recommended action:** flip the default once Stream A's calibration sweep
confirms no regression, OR keep the env-gate but make it loud — emit a stderr
warning every time the broadcast path runs without the fix flag. Currently
the default behavior silently broadcasts the same score to all criteria, and
the operator only sees it if they go grep-hunting in evaluate.py.

Triage: this is **the canonical Stream A finding** — the comment at 141
acknowledges "Granularity is lost" but every evaluation cycle still loses it
by default. The fix exists in the same file. v2 wrappers that consume
`per_criterion` rows from evaluate.py output must explicitly set
`AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=1` or they inherit collapsed scores. The
Plan B U1 wrapper should either (a) bake the env-var into its launcher or
(b) refuse to call the legacy batch handler at all and only emit
single-criterion requests.

### S3. "Temporary compatibility aliases" with no migration date — `autoresearch/evaluate_variant.py:2534-2548`

```python
2534: # ---------------------------------------------------------------------------
2535: # Temporary compatibility aliases — removed when evolve.sh heredocs migrate
2536: # to evolve_ops.py (Unit 11 / R15).  These allow evolve.sh to keep calling
2537: # the old names until the heredoc migration lands.
2538: # ---------------------------------------------------------------------------
2539:
2540: def _load_private_finalize_result(
2541:     variant_id: str, suite_id: str, lane: str = "core",
2542: ) -> dict[str, Any] | None:
2543:     return _load_private_result(variant_id, "finalize", suite_id, lane=lane)
2544:
2545: def _private_finalized_shortlist_path(suite_id: str, lane: str = "core") -> Path | None:
2546:     return _private_result_path(suite_id, "shortlist", lane)
2547:
2548: _write_private_finalized_shortlist = _write_finalized_shortlist
```

Blame: `b69690ae` J Ryszard Noszczyk 2026-04-18 (initial copy of module).

Active callers (now `evolve_ops.py`, **not** the named target `evolve.sh`):
- `autoresearch/evolve_ops.py:987` — `evaluate_variant._load_private_finalize_result(...)`
- `autoresearch/evolve_ops.py:990` — `evaluate_variant._write_private_finalized_shortlist(...)`

`grep` on `evolve.sh` finds zero references — the heredoc migration the
comment references appears to have happened. But `evolve_ops.py` simply
inherited the aliased names instead of being rewritten to call the canonical
`_load_private_result(..., "finalize", ...)` and `_write_finalized_shortlist`.

**Recommended action:** mechanical rename of the 2 evolve_ops.py call sites
to use canonical names, then delete the 3-symbol alias block. Could ride on
any open evolve_ops touch in Plan B (U2/U3) — would shrink the public API of
evaluate_variant.py by 3 names. Low risk, easy win.

Triage: this is the SUPERSEDED-leaning end of STILL_LIVE — the original
motivation is gone but the comment hasn't been updated and the migration
hasn't been finished. It's a small grease-spot; flagging it for v2 wrapper
authors so they don't accidentally import the alias names.

### S4. `--force-undo` CLI flag is a no-op but help text claims active behavior — `autoresearch/evolve.py:260-269 + 2549-2556`

```python
# CLI declaration (260-269) — describes active behavior:
260:         "--force-undo",
261:         action="store_true",
262:         default=False,
263:         help=(
264:             "Allow --undo to roll back to a non-promotable variant. "
265:             "Default off — A6 (plan 2026-05-06-001) gates undo on "
266:             "is_promotable so we don't roll back to a variant that "
267:             "never passed holdout. Operator override only."
268:         ),
269:     )

# Implementation (2549-2556) — confesses no-op:
2549:         # LLM-based ``is_promotable`` which (a) cost $0.50-$2 per undo,
2550:         # (b) was non-deterministic (judge could flip on the same
2551:         # input), and (c) could block legitimate rollbacks during a
2552:         # judge-service outage. Trust the stored ``promoted_at``;
2553:         # ``previous_promoted_variant`` raises ``SystemExit`` itself if
2554:         # there's no eligible target. ``--force-undo`` is preserved as
2555:         # a no-op for backward compat with operator scripts.
```

Blame:
- 260-269 (CLI declaration): `d128a5c7` J Ryszard Noszczyk 2026-05-06 12:24
- 2549-2556 (no-op confession): `f39a7de3` J Ryszard Noszczyk 2026-05-06 15:12

Both commits same day. The help text was written *with* the no-op in mind
but reads as if `--force-undo` is still a meaningful operator override.

**Recommended action:** either (a) rewrite the `--force-undo` help to say
"deprecated, kept as a no-op for operator-script compatibility — has no
effect, will be removed in a future release", or (b) delete the flag
entirely. Option (b) cleaner but breaks any operator script that still
passes it; option (a) is the conservative path.

Triage: this is a smaller-stakes example of the same Stream A pattern — a
comment that admits a no-op coexisting with a flag declaration that doesn't.
Lowest urgency of the 4 STILL_LIVE findings (the no-op is *truly* a no-op,
not a silent footgun), but it's the exact comment-vs-help drift pattern v2
should refuse to inherit verbatim. If v2 keeps a `promote --undo` surface at
all, it should drop `--force-undo`.

---

## 3. SUPERSEDED findings

### Sup1. `autoresearch/evolve_ops.py:574-578` — `ROLLBACK_DRY_RUN_UNTIL_ISO` constant superseded by `_auto_rollback_enabled()` but still exported

```python
574: ROLLBACK_DRY_RUN_UNTIL_ISO = "2026-05-15T00:00:00Z"
575: """LEGACY constant — kept for backwards compat with anything that imports it.
576: The actual gate is now ``_auto_rollback_enabled()`` below, which defaults to
577: DRY-RUN regardless of date. Operator must explicitly opt in via
578: ``AUTORESEARCH_AUTO_ROLLBACK=1``."""
```

The 2026-05-15 ISO date no longer affects behavior. The accompanying comment is
honest and accurate, but the constant itself is now dead — no caller depends
on it, and the date is 4 days from now. **DELETE THE STALE CONSTANT** (or
replace with a comment-only stub) on the next evolve_ops touch. Recently
authored (`905eb98e` 2026-05-06) so deletion is uncontroversial.

### Sup2. `autoresearch/archive/v007-curated/README.md:33` — "geo.py is intentionally absent" no longer true

```markdown
33: The 4 files marked ✅ above, copied verbatim from Pi `archive/v007/`.
    `workflows/geo.py` is intentionally absent — its v007 version contains
    the regressions; the next variant should keep v006's `geo.py` (or evolve
    it from there with explicit rationale).
```

Reality: `autoresearch/archive/v007-curated/workflows/geo.py` exists (4219
bytes), added by commit `71d0dd1` (X+LinkedIn port, 2026-05-08) **after** the
README was written (`4f9a30f8`, 2026-05-06). The README also lists only
`session_eval_geo.py` under `workflows/` but the directory now contains 17
files including all v007 workflow code.

**DELETE STALE README CLAIM** — and decide whether the file tree section
needs a full rewrite or just deletion. This is "deliberately disabled
comment, but the disable was later undone elsewhere" almost verbatim — same
shape as the Stream A PR #60 finding, just lower stakes because v007-curated
is a notes folder not a production hot path.

### Sup3. `autoresearch/lane_paths.py:38-41` — `TODO-MIGRATE-LANE-PATHS-2026-05-21` deadline is 10 days out

```python
34: # P1 audit: deprecation noise was masking real warnings in preflight logs
35: # (every run emitted this DeprecationWarning even though the shim is doing
36: # real bridging work — converting tier_b's parameter-injection API to the
37: # autoresearch positional convenience API). Silenced here; full migration
38: # tracked at TODO-MIGRATE-LANE-PATHS-2026-05-21 — by that date, the 6 call
39: # sites in autoresearch/ should be rewritten to import directly from
40: # src.shared.safety.tier_b + lane_registry, then this shim deleted.
```

Not strictly SUPERSEDED — the migration hasn't happened yet, the deadline is
10 days away. **Flagging because the deadline arrives during Plan B's
execution window.** Either (a) finish the migration as part of Plan B U2/U3
(it's 6 call sites in autoresearch/, all replaceable mechanically), or
(b) push the deadline in the comment to a realistic Plan B post-completion
date. Status today is "honest doc, but the doc is going to be wrong in 10
days unless action is taken".

---

## 4. BENIGN findings (no action)

| Location | Reason |
|---|---|
| `autoresearch/evolve.py:774,783` "deliberately-nonexistent endpoint" / "deliberately use HEAD" | Probe-token validation logic — correct intentional behavior. |
| `autoresearch/evolve.py:1585` "Variant_dir intentionally preserved for resume" | Resume-mode invariant; correct. |
| `autoresearch/evolve.py:2497` "Skip emission … regardless of whether THIS variant was discarded" | Cohort-metric correctness fix; well-documented. |
| `autoresearch/lane_registry.py:10` "lane parallelism in `run_all_lanes` is intentionally NOT enabled" | References `docs/architecture/concurrency.md`; deliberate architectural choice with reverted Unit 3 lineage (per MEMORY.md). |
| `autoresearch/evaluate_variant.py:2112` "Plan B's holdout-v1 deliberately omits `rotation`" | Accurate description of holdout-v1 manifest; gate correctly no-ops. |
| `autoresearch/evaluate_variant.py:1166` "do not backfill" | Explicit instruction not to retroactively repair v001-v008 binary-form composite scores. |
| `autoresearch/program_prescription_critic.py:19,35,39,331` "intentional" / "silently coerced … placeholder" | Describes the gate's behavior on bad backend output; well-rationalized. |
| `autoresearch/report_base.py:8` "will be removed 4 weeks after Phase 3" | Real pending migration with 4 live callers under `configs/{seo,competitive,monitoring,storyboard}/scripts/generate_report.py`. Pending TODO, not stale. |
| `autoresearch/archive/v006/v007/v007-curated/v009/workflows/*.py` "P1 audit: reverted from silent v006 raise (15)…" | Comment + `stall_limit=5` value both consistent with v001 baseline. The revert DID land (`b69690a..d5b69df`). Honest archeology, not aspirational. |
| `src/evaluation/service.py:64-81` "R-#34 … `compute_length_factor` + `_WORD_RANGES` were removed" | Documents a real, intentional removal with watch-list of what to do if regression appears. |
| `src/evaluation/service.py:124` "programmatic grounding gate was removed as a deliberate architectural decision" | Documents a real, well-rationalized architectural choice. |

(11 entries shown; ~25 other "intentional"/"deliberate" hits in archive
docstrings, content fixtures, and `programs/references/*.md` are
content-prose statements about marketing-audit best practices, not code
behavior — not relevant to this audit.)

---

## 5. Methodology

### Search regions

- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/` — top-level + subdirs except per-task: skip `autoresearch/archive/v0XX/` numbered version dirs (376 dirs) **except** `v006/`, `v007/`, `v007-curated/`, `v009/`.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/judges/` — 2 Python files (promotion_judge.py + quality_judge.py); nothing matched on any pattern.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/cli/freddy/commands/evaluate.py` + adjacent `cli/freddy/` files (52 files).
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/src/evaluation/` — 7 Python files + `judges/` subdir.

Also excluded `archived_sessions/`, `programs/references/*.md`, `runs/`,
`sessions/`, `templates/`, `metrics/`, `-findings.md` files (data/content,
not code logic). After filtering: **293 in-scope files**.

### Patterns scanned (grep -E, case-insensitive)

1. `(deliberate|intentional)(ly)?` near `(loss|disabled|degraded|skip|stale|reverted)` — pattern 1.
2. `temporar(il)?y` within line + 5 surrounding lines for context — pattern 2a.
3. `temp(orarily)?\s+(disabled|until|skip|removed|revert)` — pattern 2b.
4. `(TODO|FIXME|XXX|HACK)\b` + `(restore|reenable|re-enable|revert|back\s+(in|on)|disable)` — pattern 2c.
5. `(reverted (from|back)|rolled? back (from|to))` — pattern 3.
6. `(one-?shot|one-?time).*(migration|backfill)` and `back-?fill` near control flow — pattern 4/4b.
7. `silent(ly)?\s+(skip|disabl|ignor|swallow|raise|continue|fail)` — pattern 5.
8. Bonus widenings: `stub`, `placeholder`, `no-?op`, `not\s+implemented`, `legacy`, `kept\s+for\s+(backward|compatibility)`, `will\s+be\s+removed`, `(was|is|were)\s+(supposed|meant|intended)\s+to`, `not\s+yet\s+(re-?enabled|implemented|restored)`, `known\s+(issue|bug|problem|limitation)`.

For every candidate match: read 5-10 lines of surrounding context, run
`git blame -L <line>,<line>` for author+date+SHA, and classify by reading
both the comment text AND the actual code state (does the value match the
claim? does the path the comment guards actually run?). Where current code
contradicted the comment, classified as STILL_LIVE or SUPERSEDED depending
on whether the gap is dangerous or merely doc-stale.

### Effort

~50 min — pattern scan + context reads + blames + 4 cross-version diffs
(stall_limit, geo.py existence in v007-curated, etc.) + write-up.

---

## 6. Plan B impact

### For v2 wrapper authors

These 4 STILL_LIVE findings are inheritance hazards. v2 wrappers should:

- **Refuse to inherit the grace-manifest bypass (S1).** The v2 manifest
  enforcement layer should either omit the grace path entirely (refuse any
  manifest with `{"grace": true}`) or carry an explicit allow-list of
  pre-Unit-7 variant IDs. Until then, v2 should NOT delegate L1 hash check
  to autoresearch's `_check_critique_manifest`.
- **Force the axis-collapse fix on (S2).** v2's launch shim should set
  `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=1` in the environment passed to the
  judge subprocess, OR avoid the legacy batch path by emitting per-criterion
  requests directly.
- **Use canonical names, not the temp aliases (S3).** When v2 calls into
  `autoresearch.evaluate_variant`, import `_load_private_result` /
  `_write_finalized_shortlist` directly and pass the `"finalize"` kind
  explicitly — do not import `_load_private_finalize_result` etc.
- **Drop `--force-undo` (S4).** If v2 implements its own `promote --undo`
  surface, do not preserve the `--force-undo` flag for backward compat —
  it's already a no-op and carrying it forward propagates the lie.

### For Plan B U0 / U1 sequencing

None of these block U0 or U1 startup. They are **inheritance traps for U2/U3
wrapper work** (which is where v2 starts calling into the v6 substrate). Add
to the U2/U3 wrapper-author briefing.

### For deletion candidates

If Plan B's "v2 wrapper-only" phase rewrites these surfaces, the natural
cleanup order is:

- **U1 / pre-flight:** delete `ROLLBACK_DRY_RUN_UNTIL_ISO` constant (Sup1),
  fix v007-curated README (Sup2), rename evolve_ops.py call sites and delete
  the alias block (S3 / part of Sup-ish).
- **U2/U3 (wrapper layer):** the v2 launch shim sets axis-collapse env var
  (S2) and refuses grace manifests (S1).
- **U4+ (substrate cleanup):** address `--force-undo` (S4) and `lane_paths.py`
  shim removal (Sup3) — both are bigger-touch and ride with whatever lane
  registry / promote-command refactor happens.

Net code change to fix all 4 STILL_LIVE + 3 SUPERSEDED:
- ~10 LOC deletion (Sup1, Sup3 once migration is done)
- ~15-20 LOC modification (S1 gate hardening, S2 env-var default flip, S3 call-site rename + alias deletion, S4 help-text rewrite or flag deletion)
- ~30 LOC README rewrite (Sup2 — but it's a notes folder, not user-facing)

Total <100 LOC across all 7 findings. None require a multi-day effort. The
biggest decision is **S1's policy choice** (gate behind env-var vs.
allow-list) — that's a 15-minute call for JR, not a 2-day debate.
