# Fixture Program Execution Plan (Plan B of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the infrastructure from Plan A to author `holdout-v1` (16 adversarial fixtures, out-of-repo), modestly expand `search-v1` (6-8 new fixtures filling coverage gaps), migrate existing search-v1 fixtures onto the new infrastructure, validate the whole design with an overfit-canary experiment, and enable autonomous promotion with a single-judge gate.

**Architecture:** Content-heavy work driven by a shared taxonomy matrix (6-axis grid of domain × language × geography × vertical × adversarial-axis × stressed-rubric-criteria). Every fixture lands in exactly one cell and exactly one pool. Holdout lives outside the repo at `~/.config/gofreddy/holdouts/holdout-v1.json`; search expansion lands in-repo at `autoresearch/eval_suites/search-v1.json` (version-bumped to 1.1). Autonomous promotion gate requires beating baseline on both public and holdout objectives — per-fixture win-rate condition and cross-family judge are deferred to a parallel plan.

**Tech Stack:** Plan A's `freddy fixture` CLI (`validate`, `envs`, `refresh`, `dry-run`, `checklist`), Codex/gpt-5.4 judge via `freddy evaluate`, existing `evolve.sh`. No new runtime dependencies.

**Prerequisite:** **Plan A (`2026-04-21-002-feat-fixture-infrastructure-plan.md`) Phase 10 must land before Phase 2 of this plan.** Plan B Phase 2 Steps 6 and 8 use `freddy fixture checklist` and `freddy fixture discriminate`, which are built in Plan A Phase 10. (Earlier steps use commands from Plan A Phases 1-7, so Plan A Phases 1-7 are the minimum before starting Plan B Phase 2 Steps 1-5; Phases 8-10 required before Step 6.) Phase 1 of this plan (taxonomy matrix) is pure design work and can be drafted in parallel with Plan A from day one.

**Out of scope (deferred to a separate parallel plan):** MAD confidence scoring, `lane_checks.sh` gates, lane scheduling rework, cross-family judge backend (Claude Opus 4.7), IRT benchmark-health dashboard, per-fixture win-rate ≥60% promotion condition, judge-calibration harness (MT-Bench style).

---

## File Structure

**New files (in repo):**
- `docs/plans/fixture-taxonomy-matrix.md` — 6-axis matrix with all fixtures placed
- `autoresearch/eval_suites/TAXONOMY.md` — concise living index pointing at the matrix
- `autoresearch/eval_suites/holdout-v1.json.example` — redacted reference copy of holdout manifest (NOT loaded)
- `docs/plans/overfit-canary-results.md` — experiment log from Phase 5
- Per-fixture `<fixture_id>-checklist.md` files adjacent to source manifest (via `freddy fixture checklist`)

**New files (out of repo, never committed):**
- `~/.config/gofreddy/holdouts/holdout-v1.json` — real holdout manifest (600 perms)
- `~/.local/share/gofreddy/fixture-cache/holdout-v1/...` — cache entries per holdout fixture
- `~/.local/share/gofreddy/fixture-cache/search-v1/...` — cache entries for all search fixtures (existing + expansion)
- `~/.local/share/gofreddy/holdout-runs/` — existing `EVOLUTION_PRIVATE_ARCHIVE_DIR`

**Modified files:**
- `autoresearch/eval_suites/search-v1.json` — append 6-8 new fixtures, bump manifest version to `1.1`
- `autoresearch/evolve_ops.py` — strengthen `is_promotable` to require holdout beat (Phase 6)
- `autoresearch/README.md` — document new 2-condition promotion rule
- `autoresearch/GAPS.md` — mark Gaps 2, 3, 18 as partially addressed

---

## Phase 1: Fixture Taxonomy Matrix (Design Artifact)

**Purpose:** Shared design document that drives fixture authoring for both pools. Maps the design space; every fixture placed on it. Can be drafted in parallel with Plan A.

**Files:**
- Create: `docs/plans/fixture-taxonomy-matrix.md`
- Create: `autoresearch/eval_suites/TAXONOMY.md`

- [ ] **Step 1: Define the 6 axes**

In `docs/plans/fixture-taxonomy-matrix.md`, document the axes:

1. **Domain**: geo / competitive / monitoring / storyboard
2. **Language**: en / de / fr / es / pt-BR / ja / zh / mixed
3. **Geography**: US / EU / LATAM / APAC / global
4. **Vertical**: SaaS-tech / ecommerce / CPG / finance / health / automotive / media / creator-economy / enterprise-b2b
5. **Adversarial condition**: standard / paywall / SPA / thin-content / thin-ads / regulatory / multi-segment / opaque / saturated-market / low-volume / non-verbal / cultural-distance / evolving-style
6. **Stressed rubric criteria** (per-domain subset): pick 1-3 of the 8 criteria in that domain's rubric that this fixture is specifically designed to stress

Each fixture gets one value on axes 1-5 and 1-3 criteria on axis 6.

- [ ] **Step 2: Place all 23 existing search-v1 fixtures on the matrix**

Go through `autoresearch/eval_suites/search-v1.json` fixture-by-fixture. For each, determine the axis values based on the fixture's actual content (look at the context URL, client, env vars).

Output: a markdown table in the matrix doc, one row per fixture:

```markdown
| Fixture ID | Pool | Domain | Lang | Geo | Vertical | Adversarial | Stressed Criteria |
|---|---|---|---|---|---|---|---|
| geo-semrush-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-5 |
| geo-ahrefs-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-7 |
| ... (23 rows) |
```

Expected finding: existing coverage is heavily concentrated in `(en, US, SaaS-tech, standard)`. Most cells are empty.

- [ ] **Step 3: Identify coverage gaps**

In the matrix doc, enumerate:
- **Empty cells** (combinations with zero fixtures)
- **Sparse cells** (only 1 fixture)
- **Rubric criteria covered by ≤1 fixture total** (high risk of un-tested criteria)

- [ ] **Step 4: Propose fills and pool assignments**

For each empty/sparse cell worth filling, propose a fixture and tag it `→ search-v1` or `→ holdout-v1` based on the heuristic:

- **search-v1**: "This represents realistic agency work we want the system to do well on." Variants will be evaluated on this fixture during evolution.
- **holdout-v1**: "This is an adversarial probe designed to catch overfitting that wouldn't show up on search-v1." Variants are never evaluated on this during proposer iteration.

Rule: no cell appears in both pools. One fixture per cell, assigned to exactly one pool.

Target: ~6-8 new search fixtures + 16 holdout fixtures proposed.

- [ ] **Step 5: Rubric-coverage matrix**

Separately, construct a (criterion × fixture) matrix across both pools. Each domain has 8 criteria; 8 × 4 = 32 criteria total. Verify every criterion is stressed by at least 2 fixtures in the combined pool. Where gaps remain, adjust fixture proposals to close them.

- [ ] **Step 6: Create concise TAXONOMY.md living index**

Create `autoresearch/eval_suites/TAXONOMY.md` — short markdown (~100 lines) pointing at the full matrix doc, summarizing:
- Current search-v1 coverage at a glance
- Current holdout-v1 coverage at a glance
- Latest matrix version

This stays in-repo as operator-facing documentation. The full matrix stays in `docs/plans/`.

- [ ] **Step 7: Review and commit**

Read through the matrix as if you'd never seen it. Check:
- Is every existing fixture placed?
- Are proposed fills realistic (data feasibility from the data-dependency audit)?
- Does every criterion have ≥2 stressors?
- Are pool assignments defensible?

```bash
git add docs/plans/fixture-taxonomy-matrix.md autoresearch/eval_suites/TAXONOMY.md
git commit -m "docs(fixture): add taxonomy matrix + rubric coverage matrix

Maps existing 23 search-v1 fixtures against the 6-axis design space.
Identifies coverage gaps. Proposes 6-8 search expansions and 16 holdout
fixtures to fill gaps and stress every rubric criterion at least twice."
```

---

## Phase 2: Holdout-v1 Fixture Authoring (16 fixtures)

**Purpose:** Author the real holdout manifest. Uses Plan A's infrastructure end-to-end. Each fixture goes through the full per-fixture process before being committed to the manifest.

**Files:**
- Create: `~/.config/gofreddy/holdouts/holdout-v1.json` (out of repo)
- Create: `autoresearch/eval_suites/holdout-v1.json.example` (in repo, redacted reference)
- Create: per-fixture `<fixture_id>-checklist.md` (alongside the out-of-repo manifest)
- Populate: cache at `~/.local/share/gofreddy/fixture-cache/holdout-v1/...`

**16-fixture composition (finalized from Phase 1 taxonomy):**

| # | Fixture ID | Domain | Tier | Primary axes |
|---|---|---|---|---|
| 1 | geo-bmw-ev-de | geo | anchor | lang=de, vertical=auto, geo=EU |
| 2 | geo-nubank-br-pix | geo | rotating | lang=pt-BR, vertical=fintech, geo=LATAM |
| 3 | geo-stripe-docs-gated | geo | rotating | adversarial=paywall |
| 4 | geo-rakuten-travel-spa | geo | anchor | adversarial=SPA, lang=ja, geo=APAC |
| 5 | competitive-toyota-vs-byd-ev | competitive | rotating | vertical=auto, adversarial=thin-ads |
| 6 | competitive-nubank-vs-latam-banks | competitive | rotating | lang=multi, geo=LATAM, vertical=fintech |
| 7 | competitive-opaque-private-b2b | competitive | anchor | adversarial=opaque |
| 8 | competitive-axios-vs-semafor | competitive | anchor | vertical=media, adversarial=saturated |
| 9 | monitoring-unilever-cpg | monitoring | rotating | vertical=CPG |
| 10 | monitoring-deutsche-bank | monitoring | rotating | geo=EU, vertical=finance, regulatory |
| 11 | monitoring-twitch-low-volume | monitoring | anchor | adversarial=low-volume |
| 12 | monitoring-tsmc-apac | monitoring | anchor | lang=zh+en, geo=APAC, vertical=hardware |
| 13 | storyboard-tokyo-creative-ja | storyboard | anchor | lang=ja, adversarial=cultural-distance |
| 14 | storyboard-amixem-fr | storyboard | rotating | lang=fr |
| 15 | storyboard-music-creator-nonverbal | storyboard | anchor | adversarial=non-verbal |
| 16 | storyboard-pivoting-creator | storyboard | rotating | adversarial=evolving-style |

**Data-feasibility reminder from the data-dependency audit:** use `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` for ALL monitoring fixtures. Pinned historical fixtures are NOT viable — source retention is 30-90 days. Pinned-history support is deferred to a holdout-v2 bump after a snapshot cache is built in the parallel plan.

**Per-fixture process (repeated 16 times):**

- [ ] **Step 1: Write fixture spec**

Draft the JSON entry in a scratch file (e.g. `/tmp/fixture-draft.json`) as a minimal one-fixture manifest:

```json
{
  "suite_id": "holdout-v1",
  "version": "1.0",
  "domains": {
    "geo": [{
      "fixture_id": "geo-bmw-ev-de",
      "client": "bmw",
      "context": "https://www.bmw.de/de/topics/faszination-bmw/bmw-i/elektromobilitaet.html",
      "version": "1.0",
      "max_iter": 15,
      "timeout": 1200,
      "anchor": true,
      "env": {}
    }]
  }
}
```

- [ ] **Step 2: Validate**

Run: `freddy fixture validate /tmp/fixture-draft.json`
Expected: PASS.

- [ ] **Step 3: Check env vars**

Run: `freddy fixture envs /tmp/fixture-draft.json --missing`
Expected: no output (all env vars already set) OR a list of env vars that need to be provisioned. If latter: provision before continuing.

- [ ] **Step 4: Refresh cache (dry-run first for cost check)**

Run: `freddy fixture refresh <fixture_id> --manifest /tmp/fixture-draft.json --pool holdout-v1 --dry-run`
Expected: print of fetch plan + estimated sources.

Then actually refresh:

Run: `freddy fixture refresh <fixture_id> --manifest /tmp/fixture-draft.json --pool holdout-v1`
Expected: successful fetch, cache written at `~/.local/share/gofreddy/fixture-cache/holdout-v1/<fixture_id>/v1.0/`

- [ ] **Step 5: Dry-run against v006 baseline**

Run: `freddy fixture dry-run <fixture_id> --manifest /tmp/fixture-draft.json --pool holdout-v1 --baseline v006 --seeds 3`

Expected outcomes and responses:

| Dry-run output | Response |
|---|---|
| `saturated=true` (median ≥ 0.9) | Fixture is too easy for current baseline. Either accept it as anchor showing current ceiling OR revise to harder variant. |
| `degenerate=true` (median < 0.1) | Fixture is broken or unsolvable by current variants. Revise context/env; may need to simplify. |
| `unstable=true` (MAD > 0.15) | Judge disagrees with itself too much. Usually means rubric doesn't apply cleanly. Refine fixture or add clarifying env vars. |
| All flags false, median in 0.3–0.8 | Healthy. Proceed. |

Revise and retry until the fixture is healthy.

- [ ] **Step 6: Generate rubric checklist**

Run: `freddy fixture checklist <fixture_id> --manifest /tmp/fixture-draft.json --pool holdout-v1`
Expected: 5-10 item checklist written to `<fixture_id>-checklist.md`. Read it; confirm items are fixture-specific, not generic rubric restatement.

- [ ] **Step 7: Append to holdout-v1.json**

Add the validated fixture entry to `~/.config/gofreddy/holdouts/holdout-v1.json`. Maintain anchor/rotating split per the table above (7 anchors + 9 rotating).

- [ ] **Step 8: Discriminability check (anchors only)**

For anchor fixtures, verify the fixture separates variants of meaningfully different capability:

Run: `freddy fixture discriminate <fixture_id> --manifest ~/.config/gofreddy/holdouts/holdout-v1.json --pool holdout-v1 --variants v001,v006 --seeds 3`
Expected: `separable: true` with non-overlapping 95% CIs on at least one variant pair.

Rotating fixtures can skip this check at MVP.

- [ ] **Step 9: Create redacted example file**

After all 16 fixtures are in `holdout-v1.json`, create `autoresearch/eval_suites/holdout-v1.json.example` as a redacted copy. Remove or mask anything that could leak to the meta agent (specific brand names if they're sensitive, private URLs). This file is reference-only and is NEVER loaded by the evolution harness.

- [ ] **Step 10: Set env wiring**

Add to your shell profile (`~/.zshrc` or equivalent):

```bash
export EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/holdouts/holdout-v1.json
export EVOLUTION_PRIVATE_ARCHIVE_DIR=~/.local/share/gofreddy/holdout-runs
```

Set permissions: `chmod 600 ~/.config/gofreddy/holdouts/holdout-v1.json`

- [ ] **Step 11: Verify holdout loads end-to-end**

Run: `python -c "from autoresearch.evaluate_variant import _load_holdout_manifest; import os; m = _load_holdout_manifest(dict(os.environ)); print(m['suite_id'], len(sum((m['domains'].get(d, []) for d in ['geo','competitive','monitoring','storyboard']), [])))"`
Expected: `holdout-v1 16`

- [ ] **Step 12: Commit the example file (real manifest NEVER committed)**

```bash
git add autoresearch/eval_suites/holdout-v1.json.example
git commit -m "feat(holdout-v1): add redacted example holdout manifest

Real holdout-v1.json lives outside the repo at
~/.config/gofreddy/holdouts/. This example is reference-only and is
NEVER loaded by the evolution harness."
```

---

## Phase 3: Search-v1 Modest Expansion (6-8 fixtures)

**Purpose:** Fill search-v1 coverage gaps from Phase 1 with fixtures representing realistic agency work (NOT adversarial probes — those are in holdout).

**Files:**
- Modify: `autoresearch/eval_suites/search-v1.json` (append new fixtures, bump manifest version 1.0 → 1.1)

**Suggested targets** (exact fill depends on Phase 1 taxonomy output):

| Candidate | Domain | Gap filled |
|---|---|---|
| geo-airbnb-es | geo | lang=es, vertical=travel |
| geo-tesla-model-y-us | geo | vertical=auto (US version — pairs with holdout German BMW) |
| competitive-wise-vs-remitly | competitive | vertical=fintech, global money transfer |
| competitive-hellofresh-vs-home-chef | competitive | vertical=CPG/DTC |
| monitoring-netflix | monitoring | vertical=media, US but non-SaaS |
| monitoring-maersk | monitoring | vertical=shipping, geo=EU |
| storyboard-dude-perfect | storyboard | sports creator, underrepresented genre |
| storyboard-kurzgesagt-de | storyboard | educational, lang=de |

Pick 6-8 from this list (or equivalents identified in Phase 1). Each must fill a genuine gap on the taxonomy matrix.

**Per-fixture process** (the authoring loop from Phase 2 Steps 1-8, executed for each search expansion fixture with `--pool search-v1` and in-repo manifest):

- [ ] **Step 1-8: Per-fixture authoring loop**

For each of the 6-8 search expansion fixtures, execute the per-fixture process exactly as in Phase 2 Steps 1-8:

1. Write fixture spec to a scratch manifest
2. `freddy fixture validate <scratch>`
3. `freddy fixture envs <scratch> --missing`
4. `freddy fixture refresh <fixture_id> --dry-run` then without dry-run
5. `freddy fixture dry-run <fixture_id> --baseline v006 --seeds 3` (revise and retry until healthy)
6. `freddy fixture checklist <fixture_id>` (review for fixture-specificity)
7. Append to `autoresearch/eval_suites/search-v1.json` (NOT holdout-v1.json)
8. `freddy fixture discriminate` (optional for search; anchors in holdout only)

Substitute `--pool search-v1` everywhere and commit to the in-repo manifest.

One commit per fixture is fine — small commits make review easier:

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): add geo-airbnb-es fixture

Fills lang=es, vertical=travel cell in taxonomy matrix.
Dry-run vs v006 baseline: median 0.52, MAD 0.04, all flags false.
Checklist in geo-airbnb-es-checklist.md."
```

- [ ] **Step 9: Bump manifest version to 1.1**

After all new fixtures are added, bump the suite-level `version` in `autoresearch/eval_suites/search-v1.json` from `"1.0"` to `"1.1"`.

Run: `freddy fixture validate autoresearch/eval_suites/search-v1.json`
Expected: PASS with `search-v1@1.1: N fixture(s)` where N = 23 + (number added).

- [ ] **Step 10: Commit version bump**

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): bump manifest version to 1.1

search-v1 grows to ~30 fixtures via targeted coverage fills from the
taxonomy matrix. Per LM-Eval-Harness versioning policy, scores on v1.1
are NOT comparable to scores on v1.0 — variants must be rescored on
v1.1 for apples-to-apples comparison (handled in Phase 4)."
```

---

## Phase 4: Migration — Existing search-v1 Onto New Infrastructure

**Purpose:** Every existing search-v1 fixture needs a cache entry and a baseline dry-run record. This is mechanical work but must happen before Phase 5 (canary) can run with cache-backed evaluation.

**Files:**
- Populate: `~/.local/share/gofreddy/fixture-cache/search-v1/...` for all ~30 fixtures
- Create: `docs/plans/search-v1-migration-scores.md` — table of baseline scores per fixture

- [ ] **Step 1: Batch refresh all search-v1 fixtures**

Run: `freddy fixture refresh --all-stale --manifest autoresearch/eval_suites/search-v1.json --pool search-v1 --cache-root ~/.local/share/gofreddy/fixture-cache`

Since no cache exists yet, all fixtures will be refreshed. Log total cost; this is a one-time upfront cost (~$50-150 depending on TikTok monitoring quantity).

Expected: all ~30 cache entries created.

Verify: `freddy fixture staleness --pool search-v1`
Expected: every fixture shows `fresh`.

- [ ] **Step 2: Dry-run every fixture against v006**

For each of the ~30 fixtures:

Run: `freddy fixture dry-run <fixture_id> --manifest autoresearch/eval_suites/search-v1.json --pool search-v1 --baseline v006 --seeds 3`

Record the results in `docs/plans/search-v1-migration-scores.md`:

```markdown
| Fixture ID | Median | MAD | Flags |
|---|---|---|---|
| geo-semrush-pricing | 0.64 | 0.03 | — |
| geo-ahrefs-pricing | 0.58 | 0.05 | — |
| monitoring-shopify-2026w12 | 0.71 | 0.02 | — |
| ... |
```

Flag any fixture that shows `saturated`, `degenerate`, or `unstable` — these are existing fixtures that may warrant rotation out in a future search-v1 bump (not now, just note them).

**Saturation rotation trigger policy** (from the external research, Dynabench precedent): a fixture is a rotation candidate if promoted variants beat baseline on it in ≥85% of the last 10 evolution cycles — i.e., the fixture has saturated and no longer discriminates. Persistent-saturation detection is implemented as part of the migration artifact: after each finalize cycle, append `(cycle_id, fixture_id, baseline_beat: bool)` tuples to `~/.local/share/gofreddy/saturation-log.jsonl`. When any fixture crosses the 85% threshold on its last 10 recorded cycles, print it in the next `freddy fixture staleness` invocation with a `SATURATED` tag. This is data-gathering only in this plan — actual rotation (manifest bump to v1.2) happens in a future operator-triggered pass once evidence accumulates.

- [ ] **Step 3: Run autoresearch test suite**

Run: `pytest tests/autoresearch/ -x -q`
Expected: all pass. (Any canary-dependent tests should have been updated in Plan A Phase 11.)

- [ ] **Step 4: Run full evolution cycle against v006 end-to-end**

Run: `./autoresearch/evolve.sh score-current --lane core`
Expected: v006 scores on `search-v1@1.1` with cache-first behavior. Score should be in the same ballpark as v006's pre-migration score (± judge noise).

If score drifts significantly: investigate cache integration (Plan A Phase 8) before proceeding.

- [ ] **Step 5: Commit migration record**

```bash
git add docs/plans/search-v1-migration-scores.md autoresearch/GAPS.md
git commit -m "chore(migration): search-v1 fully onboarded to fixture infrastructure

All ~30 fixtures have:
- Cache entries at ~/.local/share/gofreddy/fixture-cache/search-v1/
- Recorded baseline scores in docs/plans/search-v1-migration-scores.md
- Passing end-to-end evolution cycle verified

Marks GAPS 2/3/18 as partially addressed (eval digest / fixture pool
expansion / variance handling)."
```

---

## Phase 5: Overfit Canary Experiment

**Purpose:** Validate that holdout actually catches overfitting before enabling autonomous promotion. This is the go/no-go experiment.

**Files:**
- Create: `docs/plans/overfit-canary-results.md`

- [ ] **Step 1: Freeze both suites**

Record: `search-v1@1.1`, `holdout-v1@1.0`. No fixture changes during the experiment.

- [ ] **Step 2: Select lane**

Pick `geo` (highest OOD coverage in holdout-v1 per the taxonomy).

- [ ] **Step 3: Run 20 evolution iterations on geo lane**

Run: `./autoresearch/evolve.sh --lane geo --iterations 20 --candidates-per-iteration 3`
Expected: ~20 new variants produced. Watch for divergence in evolve.sh output. Total wall-clock: many hours to days depending on session timeouts.

- [ ] **Step 4: Score checkpoints on both public and holdout**

At iterations 1, 5, 10, 15, 20: take the current `geo` lane head and score it on both suites.

For each checkpoint:

Run: `python autoresearch/evaluate_variant.py --variant <geo-lane-head-id> --manifest autoresearch/eval_suites/search-v1.json --lane geo`
Record `composite` and `domains.geo.score`.

Run: `python autoresearch/evaluate_variant.py --variant <geo-lane-head-id> --manifest $EVOLUTION_HOLDOUT_MANIFEST --lane geo`
Record `composite` and `domains.geo.score`.

- [ ] **Step 5: Construct divergence table**

Build the table in `docs/plans/overfit-canary-results.md`:

```markdown
| Iter | Variant | Public score (geo) | Holdout score (geo) | Divergence |
|---|---|---|---|---|
| 1 | v007 | 0.50 | 0.45 | 0.05 |
| 5 | v011 | 0.58 | 0.47 | 0.11 |
| 10 | v016 | 0.65 | 0.48 | 0.17 |
| 15 | v022 | 0.70 | 0.49 | 0.21 |
| 20 | v028 | 0.75 | 0.48 | 0.27 |
```

- [ ] **Step 6: Interpret signature**

Expected (holdout working): public climbs, holdout plateaus or grows slower. Divergence grows monotonically or steadily.

Failure modes and actions:
- **Holdout tracks public 1:1** (divergence flat near zero) → holdout too similar to public. Action: swap 3-4 rotating holdout fixtures with harder/more-divergent variants; bump holdout-v1 → holdout-v1.1 and rerun canary.
- **Holdout rises faster than public** → holdout fixtures too easy. Action: replace easiest holdout fixtures; bump holdout-v1.1.
- **Both curves flat** → proposer isn't improving anything. Action: investigate meta agent separately (out of scope for this plan); do NOT enable autonomous promotion.

- [ ] **Step 7: Document verdict**

Append to `docs/plans/overfit-canary-results.md`:

```markdown
## Verdict

**Status:** [GO | NO-GO]

**Reasoning:** [Free-form paragraph describing what the divergence pattern showed.]

**Next step:** [If GO: proceed to Phase 6 and enable autonomous promotion with the 2-condition gate. If NO-GO: revise holdout and rerun canary.]
```

- [ ] **Step 8: Commit** (fill in verdict before committing)

Replace the bracketed placeholder with the actual verdict recorded in Step 7.

```bash
# Example after GO verdict — replace with actual finding:
git add docs/plans/overfit-canary-results.md
git commit -m "docs(validation): overfit canary GO — holdout catches fixture overfit

20-iteration geo-lane evolution. Public climbed 0.50→0.75 while holdout
plateaued 0.45→0.48 (divergence 0.27 by iter 20). Signature matches
expected overfit pattern; proceeding to Phase 6."

# OR after NO-GO:
# git add docs/plans/overfit-canary-results.md
# git commit -m "docs(validation): overfit canary NO-GO — holdout tracks public
#
# Divergence flat at 0.05 through all checkpoints. Holdout too similar to
# public suite. Returning to Phase 2 to revise holdout-v1 → holdout-v1.1
# with more orthogonal fixtures."
```

**If NO-GO, this plan stops here. Return to Phase 2 with holdout-v1.1 revisions.**

---

## Phase 6: Enable Autonomous Promotion (Single-Judge Gate)

**Purpose:** With holdout validated, turn on autonomous promotion using a 2-condition gate: candidate must beat baseline on both public and holdout objectives. Per-fixture win-rate ≥60% and cross-family judge conditions are deferred to the parallel plan.

**Files:**
- Modify: `autoresearch/evolve_ops.py` — strengthen `is_promotable`
- Modify: `autoresearch/README.md` — document new rule
- Create: `tests/autoresearch/test_promotion_rule.py`

**Architectural note:** The existing `is_promotable` in `autoresearch/evolve_ops.py` (around line 241) reads a precomputed `promotion_summary.eligible_for_promotion` flag that is set by the holdout evaluation path in `evaluate_variant.py` (around lines 1643-1660). That flag already encodes the holdout-beat-baseline check. What's missing is an additional strict public-beat-baseline check, which this phase adds.

- [ ] **Step 1: Write failing test for new promotion rule**

Create `tests/autoresearch/test_promotion_rule.py`:

```python
from unittest.mock import patch

from autoresearch.evolve_ops import is_promotable


def _entry(variant_id, public_score, holdout_eligible=True):
    return {
        "id": variant_id,
        "lane": "geo",
        "search_metrics": {
            "suite_id": "search-v1",
            "composite": public_score,
            "domains": {"geo": {"score": public_score, "active": True}},
            "objective_score": public_score,
        },
        "promotion_summary": {
            # set by the holdout eval path — already encodes holdout-beat-baseline
            "eligible_for_promotion": holdout_eligible,
        },
    }


def _with_lineage(lineage_dict):
    def _fake_load(_archive_dir):
        return lineage_dict
    return patch("autoresearch.evolve_ops._load_latest_lineage",
                 side_effect=_fake_load)


def test_promotes_when_holdout_eligible_and_beats_public(tmp_path):
    lineage = {
        "v006": _entry("v006", 0.60, holdout_eligible=False),  # current head
        "v007": _entry("v007", 0.65, holdout_eligible=True),
    }
    with _with_lineage(lineage), \
         patch("autoresearch.evolve_ops._current_lane_head", return_value="v006"):
        assert is_promotable(tmp_path, "v007", "geo") is True


def test_rejects_when_holdout_not_eligible(tmp_path):
    lineage = {
        "v006": _entry("v006", 0.60, holdout_eligible=False),
        "v007": _entry("v007", 0.65, holdout_eligible=False),  # failed holdout
    }
    with _with_lineage(lineage), \
         patch("autoresearch.evolve_ops._current_lane_head", return_value="v006"):
        assert is_promotable(tmp_path, "v007", "geo") is False


def test_rejects_when_ties_on_public(tmp_path):
    lineage = {
        "v006": _entry("v006", 0.60, holdout_eligible=False),
        "v007": _entry("v007", 0.60, holdout_eligible=True),  # holdout OK, public tied
    }
    with _with_lineage(lineage), \
         patch("autoresearch.evolve_ops._current_lane_head", return_value="v006"):
        assert is_promotable(tmp_path, "v007", "geo") is False


def test_rejects_when_regresses_on_public(tmp_path):
    lineage = {
        "v006": _entry("v006", 0.60, holdout_eligible=False),
        "v007": _entry("v007", 0.58, holdout_eligible=True),  # holdout OK, public down
    }
    with _with_lineage(lineage), \
         patch("autoresearch.evolve_ops._current_lane_head", return_value="v006"):
        assert is_promotable(tmp_path, "v007", "geo") is False
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: FAIL — `_current_lane_head` doesn't exist yet and the existing `is_promotable` doesn't check public score.

- [ ] **Step 3: Strengthen is_promotable**

Modify `autoresearch/evolve_ops.py` `is_promotable` function (currently around line 241). Current logic reads `eligible_for_promotion` (which encodes the holdout check). New logic adds a strict public-beat requirement on top.

```python
def is_promotable(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Check if a variant is eligible for promotion.

    Two conditions must hold:
    1. `promotion_summary.eligible_for_promotion` is True (set by the holdout
       evaluation path — encodes the holdout-beat-baseline check).
    2. The candidate strictly beats the current lane head on the public
       `objective_score` for this lane.

    Per-fixture win-rate >=60% condition and cross-family judge condition
    are deferred to the parallel plan; this is the 2-condition MVP gate.
    """
    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id)
    if str((entry or {}).get("lane") or "").strip().lower() != lane:
        return False
    summary = (entry or {}).get("promotion_summary") or {}
    if not summary.get("eligible_for_promotion"):
        return False

    baseline_id = _current_lane_head(archive_dir, lane)
    baseline = latest.get(baseline_id) or {}
    cand_public = _public_objective_score(entry, lane)
    base_public = _public_objective_score(baseline, lane)
    if cand_public is None or base_public is None:
        return False
    return cand_public > base_public


def _current_lane_head(archive_dir: str | Path, lane: str) -> str:
    """Return the currently promoted variant id for a lane from archive/current.json."""
    current = json.loads((Path(archive_dir) / "current.json").read_text())
    return str(current.get(lane) or "")


def _public_objective_score(entry: dict, lane: str) -> float | None:
    """Return the public (search-v1) objective_score for the given lane, or None.

    Named `_public_objective_score` (not `_objective_score`) to avoid colliding
    with `select_parent._objective_score` which has different semantics.
    """
    search = entry.get("search_metrics") or {}
    if lane == "core":
        value = search.get("composite")
    else:
        value = (search.get("domains") or {}).get(lane, {}).get("score")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
```

- [ ] **Step 4: Verify tests pass**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: all 4 PASS.

Run: `pytest tests/autoresearch/ tests/freddy/ -x -q`
Expected: full suite still passes.

- [ ] **Step 5: Manual verification on geo lane**

Run: `./autoresearch/evolve.sh finalize --lane geo`
Expected: command completes without error. Either promotes a candidate or reports no promotion due to the new holdout condition.

Spot-check the output manually: is the promotion decision defensible given the scores? If yes, ship. If no, investigate before enabling on other lanes.

- [ ] **Step 6: Document new rule**

Update `autoresearch/README.md` "Evolution Loop" section. Document the 2-condition promotion rule. Explicitly note that stronger conditions (per-fixture win-rate, cross-family judge) are planned in a parallel work stream.

- [ ] **Step 7: Commit**

```bash
git add autoresearch/evolve_ops.py autoresearch/README.md \
        tests/autoresearch/test_promotion_rule.py
git commit -m "feat(evolve): enable autonomous promotion with 2-condition holdout gate

is_promotable now requires candidate beat baseline on both public and
holdout objectives. Per-fixture win-rate condition (>=60%) and
cross-family judge gate (Claude Opus 4.7) deferred to the parallel
plan (MAD + lane_checks + scheduling + cross-family judge)."
```

---

## Self-Review

- [x] **Spec coverage**: every goal objective (taxonomy, holdout-v1, search-v1 expansion, migration, canary, autonomous promotion) has a phase
- [x] **No placeholders**: every phase has concrete acceptance criteria and commands
- [x] **Type consistency**: `search-v1@1.1`, `holdout-v1@1.0`, `v006` used consistently
- [x] **Cross-plan dependency**: Plan A Phase 7 dependency called out at top of document
- [x] **Go/no-go gate**: Phase 5 canary explicitly blocks Phase 6 on validation

---

## Acceptance Criteria (done = all hold)

- `docs/plans/fixture-taxonomy-matrix.md` exists with all ~30 existing + 16 proposed fixtures placed
- `~/.config/gofreddy/holdouts/holdout-v1.json` exists with 16 fixtures, permissions `600`
- `autoresearch/eval_suites/holdout-v1.json.example` exists in-repo, redacted
- `autoresearch/eval_suites/search-v1.json` bumped to version `1.1` with 6-8 new fixtures
- `freddy fixture staleness --pool holdout-v1` shows all 16 as `fresh`
- `freddy fixture staleness --pool search-v1` shows all ~30 as `fresh`
- `docs/plans/search-v1-migration-scores.md` has baseline dry-run scores for every search-v1 fixture
- `docs/plans/overfit-canary-results.md` exists with 20-iteration checkpoints and a clear GO/NO-GO verdict
- If GO: `./autoresearch/evolve.sh finalize` enforces the 2-condition promotion rule (verified by tests)
- If NO-GO: plan explicitly stopped at Phase 5, holdout-v1 revised to holdout-v1.1, Phase 5 rerun

---

## Execution Options

**Plan complete.** This is Plan B of 2 — content authoring, migration, validation, autonomous promotion.

**Prerequisite:** Plan A Phase 7 (`freddy fixture dry-run`) must have landed before starting Phase 2 of this plan. Phase 1 (taxonomy matrix) can be drafted in parallel with Plan A.

1. **Subagent-Driven (recommended for Phases 2-3 fixture authoring)** — per-fixture loops benefit from fresh-subagent-per-phase review to catch design drift. Uses `superpowers:subagent-driven-development`.
2. **Inline Execution (fine for Phases 1, 4, 5, 6)** — taxonomy, migration, canary, and promotion-rule phases are more mechanical and can be batched. Uses `superpowers:executing-plans`.

Hybrid is reasonable: inline for Phases 1/4/5/6, subagent-driven for Phases 2-3 (the fixture authoring phases).

**After Plan B lands:** execute the parallel plan (to be written) covering MAD confidence scoring, `lane_checks.sh`, lane scheduling rework, cross-family judge backend (Claude Opus 4.7), and the IRT benchmark-health dashboard. The promotion rule's 4-condition extension lives there.
