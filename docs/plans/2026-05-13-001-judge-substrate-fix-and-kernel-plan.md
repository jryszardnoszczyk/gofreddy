---
title: "Judge substrate fix + +5 kernel — autoresearch evolution loop"
type: refactor + feature
status: ready-to-execute
date: 2026-05-13
spec: docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec-v2.md
audit: docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md
demo-window: Klinika Melitus + DWF Poland in 1-2 months
---

# Judge substrate fix + +5 kernel

## 1. Goal

Fix the broken-substrate-pathology the audit discovered, then ship the +5 evidence-backed criterion additions that survive the audit's rejection pass. The deliverable is a working evolution-loop judge that scores per-criterion correctly and discriminates ship-eligible artifacts from junk for the Klinika + DWF demo window.

**Acceptance:** Re-run any archived monitoring fixture; per-criterion `feedback` strings differ across the 8 MON criteria (currently byte-identical). All 5 kernel criteria (MON-9, X-9, GEO-9, CI-9, MA-9) fire correctly against archived corpora with no regression to existing 52 criteria. End-to-end evolution run completes with `scores.json` containing populated `dimension_scores` and `rubric_version`.

## 2. Non-goals (explicit out of scope)

- **New lanes** (article_engine, image_engine, ad_engine) — rejected from current scope per spec; would be fresh builds with own design pass
- **Vision-judge architecture work** — only relevant if image_engine ships, which it doesn't
- **voice_persona, brand-style-guide, findings_brief abstractions** — rejected per spec
- **Compliance YAML schema** — replaced with inline trigger lists at evaluator call-site
- **Shadow-rubric 4-week parallel mode** — replaced by one-shot archive replay in Phase 2
- **Score-distribution σ invariant** — rejected (wrong-directional)
- **Score-grain migration to 1-10** — explicitly out of scope; 3-level (0/0.5/1) is the documented contract
- **Rubric prose for the 41 rejected criteria** — rejected per spec
- **`render_judge.py` work** — separate code path (HTML/PDF reports), shipped 2026-05-12
- **`judge_calibration.py` rewrite** — only extension for Principle 3 (cross-family κ on +5), not rewrite

## 3. Source — load-bearing documents

- `docs/brainstorms/2026-05-12-judge-design-deep-research/phase-d-master-spec-v2.md` — v3 spec in place
- `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md` — 5-agent audit
- Direct empirical evidence: `autoresearch/archive/v006/sessions/monitoring/Shopify/.last_eval_cache.json` (broadcast-feedback smoking gun)

## 4. Decisions (locked)

1. **Score grain stays 3-level (0 / 0.5 / 1).** Rubric prose declares "gradient" but session-judge has always emitted 3 levels; honest documentation > prompt rewrite. Composite is 0-10 derived from weighted mean × 10.
2. **Phase 0 (substrate) blocks Phase 1.** No criterion ships against the broken substrate. Phase 1's first PR is gated on Phase 0 acceptance.
3. **Compliance is inline, not abstracted.** `MEDICAL_PL_TRIGGERS` / `LEGAL_PL_TRIGGERS` are Python module-level lists at the relevant `evaluate_session.py` call-sites. No `configs/compliance/` directory.
4. **No deferrals.** Each item in the spec is either ACCEPTED (this plan) or REJECTED (cut for cause; not a future revival queue).
5. **Phase 0.1 investigates root cause before fixing.** Don't assume the bug location. The per-criterion-prompt builder at `evaluate_session.py:308` LOOKS correct; the issue may be in the judge-service backend (port 7200, code outside this repo) or in response parsing. Investigation precedes patch.
6. **Per-lane PR per criterion in Phase 1.** Atomic shipping; each PR contains rubric prose + tests + one-shot replay validation against archive.
7. **GEO-9 ships with floor-compression accepted.** Every archived geo variant currently fails (institutional citations only). Expected behavior: ~10 evolution generations of floor-stuck scores until substrate learns named-expert citation. Pair with substrate hint in `autoresearch/archive/v006/programs/geo/meta.md` (or equivalent latest-version meta-prompt) so evolution has direction.
8. **MA-9 ships with explicit anchors only.** No promotion until anchor table is in rubric prose distinguishing decision-changing / governance / descriptive (audit's mandatory pre-ship gate).
9. **MON-9 ships with seeded fixtures only.** All current archived monitoring fixtures are zero-mention; MON-9 cannot fire. Seed 3 populated fixtures (Lululemon, Ramp, Shopify-real-mentions) as part of MON-9's unit.

## 5. Units

### Phase 0 — Substrate fix (blocks Phase 1)

| Unit | Title | LOC est | Reversibility |
|---|---|---|---|
| U0.1 | Per-criterion scoring verification + regression test (fix already shipped 2026-05-11) | 30-80 | full (git revert) |
| U0.2 | Persist `dimension_scores` + `rubric_version` to autoresearch archive | 50-100 | full |
| U0.3 | Document score-grain as 3-level in `rubrics.py` + `score_holdout.py` | 20-50 | full |

### Phase 1 — +5 kernel (gated on Phase 0)

| Unit | Title | LOC est | Reversibility |
|---|---|---|---|
| U1.1 | MON-9 fabrication AUTO-CAP + seed 3 populated fixtures | 100-150 | full |
| U1.2 | X-9 algorithmic-citizenship AUTO-CAP (regex) | 50-80 | full |
| U1.3 | GEO-9 named-expert quoted attribution + substrate hint | 80-120 | full |
| U1.4 | CI-9 triangulation depth (gradient) | 60-100 | full |
| U1.5 | MA-9 decision-changing insight density + anchor table | 100-150 | full |

### Phase 2 — Validation (gated on Phase 1 all-green)

| Unit | Title | LOC est | Reversibility |
|---|---|---|---|
| U2.1 | One-shot archive replay (kernel vs no-kernel composite distributions) | 100-150 | n/a (read-only sweep) |
| U2.2 | Negative-control fixtures for MON-9 + X-9 | 50-80 | full |
| U2.3 | Cross-family κ extension to `judge_calibration.py` for +5 only | 80-120 | full |
| U2.4 | Policy Invariance Score telemetry (free upgrade from arXiv 2605.06161) | 100-150 | full |

### Grand totals

| Phase | LOC est | Days est |
|---|---|---|
| Phase 0 | 100-230 | 1-2 (was 3-5; U0.1 already shipped) |
| Phase 1 | 390-600 | 5-7 |
| Phase 2 | 330-500 | 2-3 |
| **Total** | **~820-1330** | **~8-12 working days** |

## 6. Unit detail

### U0.1 — Per-criterion scoring verification + regression test

**STATUS UPDATE (post-investigation 2026-05-13):** The broadcast pathology has **already been fixed**. PR #60 (commit `3b97b3d`) on 2026-05-11 shipped the Stream A axis-collapse fix — CLI side at `cli/freddy/commands/evaluate.py:215-285` reads `per_criterion` array from judge response (env-gated, on-by-default); judge prompt at `judges/session/prompts/critique.md:29` instructs *"Do not back-fill identical verdicts across rubrics."* Verified working: post-fix geo eval cache (`autoresearch/archive/v006/sessions/geo/mayoclinic/.last_eval_cache.json`, mtime May 12) shows 8/8 unique feedback strings and 2 distinct scores. The audit's broadcast finding came from May 8 caches generated 3 days BEFORE the fix.

**Remaining work for U0.1:**

1. **Verify fix coverage across all 7 lanes.** Re-run one fixture per lane post-fix; confirm `.last_eval_cache.json` has per-criterion distinct feedback. Lanes: geo, monitoring, competitive, storyboard, marketing_audit, x_engine, linkedin_engine. Some pre-fix archived caches may still show broadcast — that's expected; only newly-generated caches must show per-criterion.

2. **Add regression test.** `tests/autoresearch/test_per_criterion_scoring.py` — hashes per-criterion `feedback` strings on a sample eval; fails if any 2+ criteria share an identical hash on a session with ≥4 criteria. CI gate to prevent regression.

3. **Document the fix flag.** Note in `autoresearch/README.md` (or equivalent) that `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE` env var controls the broadcast-vs-per-criterion behavior; default is on.

**Acceptance:**
- Per-criterion distinct feedback verified on at least 1 fixture per lane (post-fix run)
- Regression test added; passes on geo cache; would fail on pre-fix monitoring cache (positive control)

**Estimate:** ~1 day (was 3-5).

**Files touched:**
- New: `tests/autoresearch/test_per_criterion_scoring.py`
- `autoresearch/README.md` (env var documentation)

### U0.2 — Persist `dimension_scores` + `rubric_version` to autoresearch archive

**Current state:** Audit found `scores.json` rows with empty `dimension_scores` arrays. `RUBRIC_VERSION` constant exists at `src/evaluation/rubrics.py:1516` but isn't written to autoresearch score rows. Per-criterion data lives only in `.last_eval_cache.json` (session-keyed, easily overwritten, ~50% of variants missing).

**Implementation:**

1. Identify the score-write path. Likely: `autoresearch/archive/v006/scripts/evaluate_variant.py` or wherever `scores.json` is written.
2. After running session evaluation, aggregate `.last_eval_cache.json` per-criterion entries into `dimension_scores: {criterion_id: score}` and write to `scores.json` alongside the composite.
3. Write `rubric_version` (string, from `src/evaluation/rubrics.py:1516`) to every score row.
4. Same fields to `autoresearch/metrics/<lane>.jsonl` entries.

**Acceptance:**
- Run any v006 evolution generation
- `autoresearch/archive/v006/scores.json` rows have populated `dimension_scores` arrays and `rubric_version` field
- `autoresearch/metrics/<lane>.jsonl` entries have same
- Re-run with rubric edit; `rubric_version` hash changes; old + new rows distinguishable

**Files touched:**
- `autoresearch/archive/v006/scripts/evaluate_variant.py`
- `autoresearch/archive/v006/scripts/promotion_judge.py` (if it writes scores)
- New: `tests/autoresearch/test_score_persistence.py`

### U0.3 — Document score-grain as 3-level

**Current state:** Rubric definitions in `src/evaluation/rubrics.py:1391-1502` declare scoring as `"gradient"` (1-10 implied); session-judge has always emitted {0, 0.5, 1}.

**Implementation:**

1. Replace `"gradient"` with `"three_level"` (or similar) in rubric definitions where applicable.
2. Update docstrings to reflect: scores are {0, 0.5, 1}; composite is 0-10 from weighted mean × 10.
3. Update `score_holdout.py` if it assumes 1-10 grain.
4. Update any spec / docs that reference "1-10 gradient."

**Acceptance:**
- Grep for `"1-10"` or `"1.0..5.0"` in `src/evaluation/` and `autoresearch/` — zero false claims remain
- `rubrics.py` is internally consistent with what the judge actually produces

**Files touched:**
- `src/evaluation/rubrics.py`
- `autoresearch/archive/v006/scripts/score_holdout.py`
- Possibly `src/evaluation/models.py`

### U1.1 — MON-9 fabrication AUTO-CAP + seed 3 populated fixtures

**Criterion definition:**
> MON-9 (fabrication AUTO-CAP): Every numeric claim, named entity, or attributed quote in the digest must be substring-present in `mentions/<week>.json` (the source data). If any claim is unattested in source data, score = 0 (AUTO-CAP). Otherwise score = 1.

**Implementation:**

1. Add MON-9 to `src/evaluation/rubrics.py` MONITORING rubric.
2. Write deterministic check in `autoresearch/archive/v006/scripts/evaluate_session.py` (or wherever MON criteria evaluate):
   ```python
   def check_mon_9_fabrication(digest_text: str, mentions_json: dict) -> dict:
       claims = extract_claims(digest_text)  # numeric, named, quoted
       source_text = json.dumps(mentions_json)
       failed = [c for c in claims if c.normalized not in source_text]
       return {"score": 0.0 if failed else 1.0, "auto_cap": bool(failed), "failed_claims": failed}
   ```
3. Seed 3 populated fixtures:
   - `autoresearch/fixtures/monitoring/Lululemon-real-2026-05-13.json` (with real Mention data + corresponding digest)
   - `autoresearch/fixtures/monitoring/Ramp-real-2026-05-13.json` (same)
   - `autoresearch/fixtures/monitoring/Shopify-populated-2026-05-13.json` (Shopify with actual mentions, not the zero-mention archived fixture)
4. Write injection test: clean fixture → MON-9 passes; injected fabrication fixture → MON-9 fires AUTO-CAP.

**Acceptance:**
- 3 seeded fixtures exist + are documented
- MON-9 unit test passes (clean → 1.0; fabricated → 0.0 + AUTO-CAP flag)
- One-shot replay against all archived monitoring fixtures: no false positives (all archived digests should score 1.0 since they all honestly report zero-mention)

**Files touched:**
- `src/evaluation/rubrics.py` (MONITORING rubric)
- `autoresearch/archive/v006/scripts/evaluate_session.py`
- New: `autoresearch/fixtures/monitoring/{Lululemon,Ramp,Shopify}-real-2026-05-13.json`
- New: `tests/autoresearch/test_mon_9_fabrication.py`

### U1.2 — X-9 algorithmic-citizenship AUTO-CAP

**Criterion definition:**
> X-9 (algorithmic-citizenship): External URLs in the `[BODY]` block of an X post or in `[REPLY]` blocks AUTO-CAP score to 0. Reason: Buffer 18.8M-post analysis shows median engagement ~0% for non-Premium link posts since March 2025; X's open-sourced `TweetUrlMultiplier` confirms 30-50% multiplier penalty in algorithm code.

**Implementation:**

1. Add X-9 to `src/evaluation/rubrics.py` X_ENGINE rubric.
2. Regex check in `autoresearch/archive/v006/scripts/evaluate_session.py` (or `programs/x_engine/scripts/`):
   ```python
   _URL_RX = re.compile(r"https?://\S+")
   def check_x_9(draft_text: str) -> dict:
       body_block = extract_block(draft_text, "[BODY]")
       reply_blocks = extract_blocks(draft_text, "[REPLY]")
       has_url = bool(_URL_RX.search(body_block)) or any(_URL_RX.search(b) for b in reply_blocks)
       return {"score": 0.0 if has_url else 1.0, "auto_cap": has_url}
   ```
3. Validation against archive: run the 3 archived 2026-05-12 x_engine drafts; all 3 should AUTO-CAP (audit confirmed all 3 violate).

**Acceptance:**
- X-9 unit test: clean draft (no URLs) scores 1.0; draft with URL in body or reply scores 0.0 + AUTO-CAP
- Archive validation: 3 archived 2026-05-12 drafts all AUTO-CAP

**Files touched:**
- `src/evaluation/rubrics.py` (X_ENGINE rubric)
- `autoresearch/archive/v006/scripts/evaluate_session.py` or `programs/x_engine/scripts/`
- New: `tests/autoresearch/test_x_9_algorithmic_citizenship.py`

### U1.3 — GEO-9 named-expert quoted attribution + substrate hint

**Criterion definition:**
> GEO-9 (named-expert quoted attribution): Score 1.0 if artifact cites at least one named individual (first + last name) in `"..."` quoted form with explicit credential or institutional role nearby. Score 0.5 if institutional attribution only (e.g., "Mayo Clinic states"). Score 0.0 if no attribution at all. NOT an AUTO-CAP. Optional sub-question: does the artifact emphasize the source institution in the leading sentence ("Source Emphasis" tactic per KDD 2024 +115% lift)?

**Implementation:**

1. Add GEO-9 to `src/evaluation/rubrics.py` GEO rubric with explicit prose anchors.
2. Rubric prompt (3-level gradient) — judge call, not deterministic. Anchor examples in prompt.
3. Substrate hint: edit `autoresearch/archive/v006/programs/geo/meta.md` (or latest version's meta-prompt) to instruct evolution to learn named-expert quoted attribution. Add example:
   > Strong GEO artifacts cite named experts in quoted form: 'Dr. Sarah Liu, Mayo Clinic electrophysiologist, says "atrial fibrillation risk doubles after 65."' Weak artifacts cite only institutions: 'Mayo Clinic says atrial fibrillation risk doubles after 65.' Aim for the former.

**Acceptance:**
- GEO-9 unit test: artifact with named-expert quote → 1.0; institutional-only → 0.5; no attribution → 0.0
- Re-rate 5 archived geo variants (v007, v008, v016, v175, v182); all current variants score 0.5 or below (audit confirmed)
- Substrate hint visible in `meta.md`

**Files touched:**
- `src/evaluation/rubrics.py` (GEO rubric)
- `autoresearch/archive/v006/programs/geo/meta.md`
- New: `tests/autoresearch/test_geo_9_named_expert.py`

### U1.4 — CI-9 triangulation depth

**Criterion definition:**
> CI-9 (triangulation depth): For each major insight in the brief, score the source diversity. 1.0 = ≥2 independent source classes (e.g., scraped competitor page + earnings call + third-party analysis); 0.5 = 2 sources but same class (e.g., two landing pages); 0.0 = single source.

**Implementation:**

1. Add CI-9 to `src/evaluation/rubrics.py` COMPETITIVE rubric with prose anchors.
2. Source-class taxonomy in rubric prose: { landing-pages, earnings-calls, third-party-analysis, social-signals, product-changelogs, customer-reviews }.
3. Judge call (gradient).

**Acceptance:**
- CI-9 unit test: brief with diverse-source insights → 1.0; same-class duplication → 0.5; single-source → 0.0
- Re-rate 4 archived competitive variants (v006, v010, v018, v095); σ across 4 variants ≥ 1.5 (audit found σ=2.2)

**Files touched:**
- `src/evaluation/rubrics.py` (COMPETITIVE rubric)
- New: `tests/autoresearch/test_ci_9_triangulation.py`

### U1.5 — MA-9 decision-changing insight density + anchor table

**Criterion definition:**
> MA-9 (decision-changing insight density): Fraction of audit findings that would force a marketing decision change vs descriptive observations or governance/process recommendations. 1.0 = >50% decision-changing; 0.5 = 25-50%; 0.0 = <25%.

**Anchor table (mandatory rubric prose):**

| Category | Example | Score contribution |
|---|---|---|
| Decision-changing | "Stripe should split state-of-business messaging by buyer stage" | +1 to numerator |
| Governance | "Create a canonical proof register before claims are reused" | excluded from numerator |
| Descriptive | "Anthropic's homepage emphasizes safety" | excluded from numerator |

**Implementation:**

1. Add MA-9 to `src/evaluation/rubrics.py` MARKETING_AUDIT rubric.
2. Embed anchor table in rubric prose (judge prompt sees the table).
3. Judge call (3-level gradient).

**Acceptance:**
- Re-rate 4 v006 audit variants (Stripe, DWF, Anthropic, Perplexity); σ across 4 ≥ 1.0 (audit found σ≈1.0)
- Operator spot-check: 2 randomly sampled findings per variant categorized correctly per anchors

**Files touched:**
- `src/evaluation/rubrics.py` (MARKETING_AUDIT rubric)
- New: `tests/autoresearch/test_ma_9_decision_density.py`

### U2.1 — One-shot archive replay

**Goal:** Replace v2's 4-week shadow-rubric mode. Single sweep: run kernel against all archived artifacts; produce a report comparing composite distributions with vs without the +5 kernel.

**Implementation:**

1. New CLI: `freddy autoresearch replay-kernel --lanes monitoring,geo,competitive,marketing_audit,x_engine --output reports/2026-05-13-kernel-replay.md`
2. For each archived variant in `autoresearch/archive/v*/`:
   - Re-evaluate using both old rubric (current 52) and new rubric (52 + kernel applicable to lane)
   - Compute per-criterion deltas and composite delta
3. Output table: per-lane mean/median/σ delta; per-criterion fire rate; identified variants where verdict changed (KEEP→REJECT or vice versa)

**Acceptance:**
- Report generated at `reports/2026-05-13-kernel-replay.md`
- Operator can identify: which variants now AUTO-CAP that didn't before? Which composites moved >0.5?

**Files touched:**
- New: `src/cli/replay_kernel.py` or extension of existing CLI
- New: `reports/2026-05-13-kernel-replay.md` (output)

### U2.2 — Negative-control fixtures for MON-9 + X-9

**Goal:** Cap false-positive rate ≤ 5%.

**Implementation:**

1. Create 5 "definitely clean" monitoring fixtures (real mention data, digest faithful to source) — MON-9 must NOT fire.
2. Create 5 "definitely clean" x_engine drafts (no external URLs, well-formed) — X-9 must NOT fire.
3. Wire into `tests/autoresearch/test_negative_controls.py`.

**Acceptance:**
- All 10 negative controls pass (no AUTO-CAP fires)

**Files touched:**
- New: 10 fixture files under `autoresearch/fixtures/negative_controls/`
- New: `tests/autoresearch/test_negative_controls.py`

### U2.3 — Cross-family κ extension to `judge_calibration.py`

**Goal:** Implement Principle 3 (cross-family agreement) on the +5 kernel only.

**Implementation:**

1. Extend `autoresearch/judge_calibration.py` to score each kernel criterion under Claude + Codex (+ optionally Gemini) families on a calibration set.
2. Compute Cohen's κ per criterion across families.
3. Flag criteria with κ < 0.4 for demotion to "informational" (no composite weight).
4. Cite Rating Roulette (arXiv 2510.27106) + Preference Leakage (arXiv 2502.01534) in docstrings (NOT J/ΔJ — see audit findings).

**Acceptance:**
- `judge_calibration.py` outputs per-criterion κ for MON-9, X-9, GEO-9, CI-9, MA-9
- Any criterion with κ < 0.4 documented; operator decides demote-or-keep

**Files touched:**
- `autoresearch/judge_calibration.py`
- New: `tests/autoresearch/test_cross_family_kappa.py`

### U2.4 — Policy Invariance Score telemetry

**Goal:** Free upgrade from arXiv 2605.06161. Score every kernel criterion under 2-3 meaning-preserving rubric-prose rewordings; track verdict-flip rate.

**Implementation:**

1. For each of MON-9, X-9, GEO-9, CI-9, MA-9: write 2 paraphrased versions of the rubric prose that preserve intent.
2. On every evolution run, judge each artifact under all 3 versions (original + 2 paraphrases).
3. Track Policy Invariance Score = 1 - (verdict-flip rate). Log to `autoresearch/metrics/policy_invariance.jsonl`.
4. Flag any criterion with PIS < 0.9 (verdict-flip rate > 10%) for revision.

**Acceptance:**
- `metrics/policy_invariance.jsonl` populates after one evolution run
- PIS for each kernel criterion logged
- Documentation cites arXiv 2605.06161

**Files touched:**
- New: `autoresearch/policy_invariance.py`
- `autoresearch/archive/v006/scripts/evaluate_session.py` (hook in)
- New: `tests/autoresearch/test_policy_invariance.py`

## 7. Phases

| Phase | Units | Sequencing |
|---|---|---|
| Phase 0 | U0.1 → U0.2 → U0.3 | sequential; each blocks the next |
| Phase 1 | U1.1, U1.2, U1.3, U1.4, U1.5 | parallel (5 PRs); ship in any order after Phase 0 |
| Phase 2 | U2.1 (after all of Phase 1), then U2.2, U2.3, U2.4 in parallel | gated on Phase 1 |

## 8. Hard gates

1. **G0 (after Phase 0):** Re-run any archived monitoring fixture; per-criterion `feedback` strings differ. `scores.json` has populated `dimension_scores` + `rubric_version`. **Without this, Phase 1 does not start.**
2. **G1 (after each Phase 1 unit):** Unit test passes + archive re-rating consistent with audit findings (σ ≥ audit-reported σ for that criterion).
3. **G1.5 (after all Phase 1 units):** End-to-end evolution generation completes; all 5 kernel criteria fire correctly; no regression on existing 52 criteria.
4. **G2 (after U2.1):** One-shot replay report shows discrimination on at least 1 variant per lane (the kernel changes a verdict somewhere).
5. **G2.5 (after U2.3):** No kernel criterion has κ < 0.4 across Claude/Codex families. If any does: revise rubric prose before Phase 4.

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| ~~Phase 0.1 root cause is in judge-service backend~~ | RESOLVED | — | Investigation 2026-05-13 confirmed fix already shipped in PR #60 on 2026-05-11. Judge prompts are in-repo at `judges/session/prompts/critique.md` + `judges/evolution/prompts/scorer.md`. |
| Audit's "ceiling-bound rubrics" finding is also stale (analyzed May 8 pre-fix data) | MODERATE | LOW (delays Phase 1 promotion confidence) | Re-run discrimination analysis on post-fix archive (May 12+ caches) before declaring Phase 1 criteria load-bearing. Specifically: collect dimension_scores across post-fix sessions; recompute σ per existing criterion. If MON/CI/SB remain ceiling-bound on post-fix data, the audit's prescription holds. If they show variance now, fewer kernel criteria may be needed. |
| MON-9 false positives on legitimate digests that paraphrase source | MODERATE | MEDIUM (false caps reject good variants) | Use fuzzy substring match (token-level), not exact; tune threshold against 5 negative-control fixtures |
| GEO-9 floor-compression for too many generations | LOW | LOW (expected per spec) | If still floor-stuck after 15 generations, strengthen substrate hint or accept gradual learning |
| Score-grain stays 3-level but rubric prose disagrees | LOW | LOW | U0.3 audit fixes; CI grep test prevents regression |
| Cross-family κ < 0.4 on a kernel criterion | MODERATE | MEDIUM (demote that criterion) | Demote to informational; ship 4 kernel + 1 informational rather than fail-stop |
| Archived `.last_eval_cache.json` parsing is brittle (~50% of variants have no cache) | LOW | MEDIUM (limits U2.1 sample) | One-shot replay re-evaluates rather than reading cache; cache absence is expected |
| Investigation in U0.1 takes longer than 5 days | MODERATE | HIGH (delays everything) | After 5 days, escalate to JR with current findings; consider scope reduction (parser fix only, accept that judge-service backend stays broken) |

## 10. Reversibility per unit

- All units are git-revert reversible.
- No data migrations.
- No schema changes (DB schema already has `dimension_scores` + `rubric_version` columns; this plan only starts writing them).
- No external API changes.
- Negative controls + seeded fixtures are additive (new files; no deletion of existing data).
- Rubric prose edits in `src/evaluation/rubrics.py` are versioned via `RUBRIC_VERSION` hash; old rubric remains in git history.

## 11. Open questions (operator)

1. **Score grain confirmation.** v3 spec recommends keeping 3-level (0/0.5/1). Confirm before U0.3 lands.
2. **Compliance trigger phrases.** ~10 medical_pl + ~10 legal_pl. Need JR + legal-review owner for content. **Not blocking this plan** (compliance is hardcoded inline at evaluator call-site only when fixture lane needs it — first Klinika storyboard fixture); flag as separate operator task.
3. **Judge-service backend access.** If U0.1 traces root cause to port-7200 service code, do we have repo access? If not, what's the workaround acceptance?

## 12. After this plan ships

Phase 4 (real-world validation) runs against Klinika + DWF deliverables once those arrive. On observed kernel-miss: ship a single new criterion targeting the specific observed failure mode. Not a batch revival; not a v1.5 program. One observed failure → one criterion.

If Klinika or DWF commit to articles, images, or ads through autoresearch (currently not in scope), that triggers a fresh design pass for the relevant lane — not a continuation of this plan.
