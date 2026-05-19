---
date: 2026-05-18
type: research deliverable
status: complete
topic: site_engine — `docs/rubrics/site-quality.md` retirement plan
axis: SITE-QUALITY.MD RETIREMENT (1 of 29 parallel dispatches)
parent: docs/rubrics/judge-design-guide.md
companions:
  - docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
  - docs/research/2026-05-18-judges-domain-site-engine.md
  - docs/handoffs/2026-05-17-judge-design-step1-competitive.md
under_review: docs/rubrics/site-quality.md (v1, 346 lines, authored 2026-05-13)
---

# Site Quality Rubric — Retirement Triage

## TL;DR

The legacy `docs/rubrics/site-quality.md` SE-1..SE-8 rubric, authored 2026-05-13 as the side-product of the gofreddy.ai landing-page rebuild, predates the design guide. Triaged against the v2.1 guide it carries **three structural anti-patterns** (1/3/5 scale, anti-gaming clauses on every axis, 8 criteria > the ≤5 ceiling) and **routes verifiables through the judge** that should live in `structural_gate` (axe-core a11y, Lighthouse perf, brand-token equality, schema.org markup).

Per-axis triage outcome:

- **CUT (feature-check) — 2 axes:** SE-5 (brand-token equality is a deterministic check) and SE-7 (Lighthouse metrics are deterministic). Move to `structural_gate`. They are not judge work.
- **CUT (a11y-feature-check) — 1 axis:** SE-6 (axe-core run + WCAG checks). Move to `structural_gate`. The semantic-HTML "expresses what visual implies" sliver that *is* outcome-shaped is small; per the existing Pass-5 YAGNI audit it's already operator-hand-graded, so the judge layer has no remaining outcome question worth its own criterion.
- **MERGE — 2 axes into SE-A (human CTA commit):** SE-1 (visual hierarchy + CTA prominence) and SE-2 (copy clarity + plain-English) both describe the same outcome — "would a human visitor commit to the primary CTA in ~10 seconds." The new SE-A subsumes both as one outcome question.
- **KEEP-as-transform — 1 axis into SE-C (proposition specificity):** SE-3 (claim honesty + anti-overselling) maps cleanly to the design guide's outcome-question form ("would a hostile reader force a retreat to 'we meant that loosely'?").
- **REASSIGN — 1 axis to brand-voice lane:** SE-4 (voice persona fit) is real but lives outside site_engine's dual-audience scope; route to the brand-voice / `voice_persona` lane infrastructure (already exists per `ClientConfig.voice_persona`).
- **TRANSFORM — 1 axis into SE-B (AI-engine citation):** SE-8 (anti-slop) is two things wrapped together: a feature-check checklist of dated 2025-26 AI-template signals, AND a real outcome ("does it look like a human cared"). Cut the feature-checklist half (lime+purple palette, three-icon trio, gradient-mesh hero — these date as templates evolve). Fold the outcome half into SE-B's entity-grounding + third-party-validation tests where AI engines empirically penalize the same template-y patterns the human-anti-slop test catches.
- **NET-NEW — 3 criteria the legacy rubric lacks:** SE-B (AI engine cites a passage — Q1 2026 Ahrefs 12% citation/ranking overlap means AI engines need their own criterion), SE-D (commits to a specific reader — implicit in legacy but never named as discriminator), SE-E (freshness + entity stability — absent entirely).

**Final v1 criterion set: 5 criteria (SE-A..SE-E).** No documented breach of the ≤5 ceiling. Dual-audience covered: SE-A+SE-C+SE-D target the human; SE-B+SE-E target the AI engine. Redundancy check may compress to 3–4 (SE-A↔SE-D and SE-B↔SE-E both plausible merge candidates).

**Migration path:** archive `docs/rubrics/site-quality.md` under git history; preserve as `docs/rubrics/archive/site-quality-v1.md` for the 2026-05-13 calibration prose (still useful as anti-slop *training data*, not as rubric anchors); do NOT re-score historical fixtures (per legacy revision policy + design guide §15 calibration is per-version anyway, historical scores remain attributable to the old `rubric_version`); ship the v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` as the canonical replacement and update the 8 cross-references in plans / handoffs.

---

## Per-SE-N triage table

| SE-N | Legacy criterion | Verdict | Target layer | Reasoning |
|------|------------------|---------|--------------|-----------|
| **SE-1** | Visual hierarchy + CTA prominence | **MERGE → SE-A** | LLM judge | Tests the same outcome SE-A v0 tests: would a human visitor click the primary CTA. The "3-reader eye-flow test" falsifiability lives as the score-1 anchor for SE-A. Anti-gaming clause ("cannot be earned by making CTA huge or neon") and the 1/3/5 scale both go. |
| **SE-2** | Copy clarity + plain-English | **MERGE → SE-A** | LLM judge | Plain-English readability and CTA prominence are the same outcome split two ways. A page with clear hierarchy but jargon copy fails SE-A; a page with plain copy but a missing CTA also fails SE-A. The "non-domain reader paraphrase" test is the score-1 behavioral anchor inside SE-A's CoT Step 2 (does the visible hero answer "what / who / why different"). |
| **SE-3** | Claim honesty + anti-overselling | **KEEP-as-transform → SE-C** | LLM judge | SE-3's substance is the outcome question SE-C v0 already names: "if a hostile reader interrogated each claim, would specific claims survive?" Direct mapping. Drop the 1/3/5 scale + anti-gaming clause; lift the "produce the artifact within 24h" falsifiability into SE-C's score-1 anchor. |
| **SE-4** | Voice persona fit | **REASSIGN → brand-voice infra** | NOT site_engine judge | Voice fidelity to client voice corpus is a cross-lane concern (article_engine, ad_engine, image_engine, linkedin_engine, x_engine all consume the same `ClientConfig.voice_persona`). It's not site_engine-specific — a site-engine variant that fails SE-4 fails the same way an article_engine variant fails. Belongs in the shared voice-persona framework (U3 in plan-002), not in the site_engine judge. |
| **SE-5** | Brand-token + aesthetic-fit | **CUT (feature-check) → `structural_gate`** | `structural_gate` deterministic check | This is verbatim a deterministic check: extract colors from rendered output, compare to `client_config.brand_tokens` set membership; extract font-family, compare to token list; extract spacing values, compare to token grid. Zero subjective judgment. Routes through the OpenRubrics "Hard Rules → structural_gate" rule (design guide §1.2 + §2). The judge has nothing to add here. |
| **SE-6** | Accessibility + semantic structure | **CUT (feature-check) → `structural_gate`** | `structural_gate` + operator hand-grade | axe-core violation count, WCAG AA contrast ratio, keyboard-focus reachability, semantic-tag/role agreement are all deterministic. Plan-002's Pass-5 audit already cut the axe-core toolchain (U7c) and hand-graded SE-6 for v1. The hand-grade work IS structural_gate work (binary pass/fail per check), not LLM-judge work. No outcome-shaped sliver remains worth a judge criterion. |
| **SE-7** | Performance | **CUT (feature-check) → `structural_gate`** | `structural_gate` + operator hand-grade | FCP < 1.5s, CLS < 0.05, TBT < 200ms, payload-KB-budget are deterministic Lighthouse metrics. Same Pass-5 cut as SE-6: hand-graded against U7b's screenshot + console output per a brief checklist (payload reasonable for section type). Not judge work. |
| **SE-8** | Anti-slop (does it look generated) | **TRANSFORM (split) → SE-B partial + cut feature-checklist** | LLM judge (partial) + retired | SE-8 is a feature-check catalog wrapped around a real outcome. The feature-checklist half ("lime+purple+dark gradient palette", "three-icon trio with generic gradients", "We help you... pattern", "stock testimonial-card grid") is exactly the pattern the design guide §12.1 + §11.4 names as the Feature-level Proxy Compression risk — workflow learns to swap palette and icon-count to pass. Cut it. The outcome half ("does this look like a human cared", "does this feel specific to THIS client") is real but is already covered by SE-B's entity-grounding + third-party-validation test (AI engines empirically discount template-y pages — same signal, outcome-shaped, no checklist). Hand-touch-detection adds no separation that SE-B doesn't already deliver. |

---

## Anti-pattern summary (against design guide §12)

Three global anti-patterns hit ALL 8 legacy axes:

1. **1/3/5 scale with described levels** (§12.4 + arxiv 2506.22316) → central-tendency collapse. Present on every SE-N.
2. **Anti-gaming clauses on every axis** (§12.12 + §10 + arxiv 2506.13639) → theatrical, redistribute bias without removing rank order. Present on every SE-N.
3. **8 criteria exceeds ≤5 ceiling** (§5 + arxiv 2506.13639). Global count violation.

Additional per-axis anti-patterns: SE-5/6/7 are pure feature-checks (§12.1) — color set membership / axe count / Lighthouse metrics are deterministic, not outcome judgments. SE-8 is a feature-check disguised as outcome — the "does it look generated" framing collapses to a six-pattern checklist (lime+purple palette, three-icon trio, gradient mesh, etc.) the workflow learns to swap markers against. SE-4 is an outcome but cross-lane (voice fidelity applies identically to article_engine, ad_engine, image_engine, linkedin_engine, x_engine).

SE-1, SE-2, SE-3 are the only axes whose outcome framing survives the design-guide test — they need binary anchors + drop 1/3/5 + drop anti-gaming, but the outcomes themselves are sound. SE-1 and SE-2 collapse to one outcome (the 3-reader eye-flow test and the non-domain-reader paraphrase test both fail when the hero block doesn't answer "what / who / why different" in declarative register with a visually dominant CTA). SE-3 carries through as SE-C.

In aggregate: the legacy rubric is a textbook case of pre-design-guide drift surface. The rebuild is genuine, not in-place fixable.

---

## Documented failure-mode coverage check

Each retained / merged / transformed criterion in the v0 spec is a documented failure mode in landing-page or AEO literature (per `docs/research/2026-05-18-judges-domain-site-engine.md` §2 FM-1..FM-8):

| v0 criterion | Failure modes it discriminates | Lit anchor |
|--------------|-------------------------------|-----------|
| SE-A (human CTA commit) | FM-2 generic SaaS template copy; FM-3 hero claim inflation; FM-4 vague benefit copy; FM-8 buried answer | CXL Hero Audit; Wynter user-testing; Marketing Examples teardowns; Profound 44% top-third citation finding |
| SE-B (AI citation) | FM-1 AI-generated landing-page slop; FM-5 logo-walled social proof; FM-6 fake FAQ | Aggarwal KDD 2024 evidence-injection; Profound 10K-passage study; Ahrefs Q1 2026 citation-overlap divergence |
| SE-C (proposition specificity) | FM-3 hero claim inflation; FM-4 vague benefit copy | Dunford positioning; CXL hero claim-inflation A/B data; Aggarwal "unsubstantiated comparatives correlate negatively with AI citation" |
| SE-D (commits to specific reader) | FM-2 generic SaaS template copy; FM-7 pricing-pages-hide-the-price | Dunford competitive-alternatives-including-do-nothing; Balfour positioning-first; Wynter user-testing on category-placement inference |
| SE-E (freshness + entity stability) | FM-5 logo-walled (no entity context); recency-cutoff distortion for AI engines | Search Engine Land 8K-citation study (44% current-year); Kalicube Semantic Triple; LLMLagBench-equivalent for visible date signals |

The retired axes' coverage migration:

| Retired axis | Failure mode it addressed | Where coverage moves |
|--------------|---------------------------|---------------------|
| SE-1 visual hierarchy | Eye doesn't land at CTA | SE-A score-1 anchor (visually dominant primary CTA) |
| SE-2 plain-English | Reader can't paraphrase | SE-A CoT step 2 (declarative register check) |
| SE-3 claim honesty | Hedged / unsubstantiated claims | SE-C (whole criterion) |
| SE-4 voice fit | Off-voice copy | Shared `voice_persona` framework (cross-lane) |
| SE-5 brand-token | Off-brand color / font / spacing | `structural_gate` deterministic check |
| SE-6 a11y | axe violations, contrast failures | `structural_gate` + operator hand-grade |
| SE-7 performance | Heavy payloads, layout shift | `structural_gate` + operator hand-grade |
| SE-8 anti-slop | Generic-AI template signals | SE-B entity-grounding test catches the AI-engine-detectable subset; rest retired (template-pattern checklists are perishable per plan-002 §307 + drift with each new generic-AI default cycle) |

Every documented failure mode is still discriminable under the v1 5-criterion set. No coverage gap.

---

## Justification for the proposed 5-criterion set (no documented exception)

The CI lane's 6th-criterion exception (CI-6 evidence-chain) is justified by an LLM-specific failure surface the other 5 can't catch — entity confabulation at 19.9% GPT-4o citation-fab rate, source confabulation at 37% Perplexity failure shape, recency-cutoff distortion per LLMLagBench. The artifact in CI is text-based and AI-authored end-to-end; the 6th criterion defends the text-evidence chain.

Site_engine's artifact is a rendered landing-page surface, not pure prose. Its LLM-failure surfaces map differently:

- **Entity confabulation** → absorbed by `structural_gate` (URL HEAD resolution on cited customer names; named-entity existence lookup). Semantic residue (a plausible-sounding customer quote with no verifiable name) falls to SE-B's evidence-injection test.
- **Recency-cutoff distortion** → absorbed by SE-E (freshness + entity stability) by construction.
- **Source confabulation** → site_engine pages typically ARE the source. Fabricated customer quotes are caught by SE-B; cited URL resolution by `structural_gate`.

The CI-6-shape pattern doesn't carry over cleanly because the landing-page evidence chain is largely a `structural_gate` problem (URL resolves? named customer exists? schema validates?) rather than a semantic-judgment problem. The semantic part fits inside SE-B.

**Therefore: 5 criteria, no documented breach.** SE-A..SE-E as authored in the v0 spec §4.

Redundancy-check expectations (per design guide §5 — pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models, ~75 calls):

- **Most-likely-to-merge pair: SE-A ↔ SE-D.** Both test human reader fit; a page that fails to commit to a specific reader (SE-D) typically also fails to convert that reader (SE-A).
- **Second-likely: SE-B ↔ SE-E.** Both test AI-engine readability; selection signals may correlate.
- **Live floor expectation: 3–4 criteria after redundancy check.** If both pairs merge, floor is 3 (SE-A+D, SE-B+E, SE-C). The §5 ceiling is preserved either way.

---

## Migration plan

### Step 1 — Archive the legacy rubric (preserve calibration data)

Move `docs/rubrics/site-quality.md` to `docs/rubrics/archive/site-quality-v1.md` and add a frontmatter banner: "archived 2026-05-18, superseded by the design-guide-conforming spec at `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md`. Retained for historical scored variants (whose `rubric_version: site-quality-v1` field references this file) AND as anti-slop calibration training data (the 2026-05-13 landing-page session prose is still useful as workflow training material, just not as judge anchors). Do NOT consume this file from any new lane or judge code path."

Why archive rather than delete: per the legacy rubric's own revision policy (line 330-333), historical scored variants stay attributable to their `rubric_version` field. Deleting the file orphans those scores. Archival preserves traceability.

### Step 2 — Promote the v0 spec to lane source-of-truth

The v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` becomes the canonical site_engine criterion spec. Either:

- **Option A (preferred):** Lift the criteria into a new `docs/rubrics/site-engine.md` file once the redundancy check + fixture validation passes; keep the spec in handoffs as the design-decision record.
- **Option B:** Leave the spec in handoffs and have `RubricTemplate.prose_ref` (per plan-002 D27) point at the handoff path. Marginally less clean but avoids a duplication step.

Recommendation: Option A after first fixture validation pass (~2 weeks of fixture iteration); Option B in the interim so the spec is live without blocking on a stable file path.

### Step 3 — `structural_gate` expansion (BEFORE the judge spec ships to v006)

Items moving from judge to `structural_gate` (per plan-002 D26 + Pass-5 audit):

- **Brand-token validity** — extract colors at full opacity, compare to `client_config.brand_tokens.colors`; font-family vs token list; spacing vs token grid.
- **axe-core a11y violations** — zero violations of severity ≥ "moderate"; hand-graded in v1 per plan-002 §1138; toolchain reintroduction deferred to v1.5.
- **Lighthouse perf metrics** — FCP < 1.5s, CLS < 0.05, TBT < 200ms, payload ≤ section-type budget; hand-graded in v1.
- **Schema.org markup validity** — validate Organization / Product / FAQPage / BreadcrumbList if present.
- **URL HEAD resolution** on cited customer / case-study links.
- **Visible-date presence check** — date surfaced within prior 12 months (SE-E's underlying signal as deterministic check).
- **Entity-name consistency** — regex / token match across hero, footer, structured data; flag drift ("Acme Pay" / "AcmePay" / "Acme Payments").
- **Image alt-text presence** on `<img>` elements (semantic SE-6 residue).

The judge sees the artifact only after structural_gate passes (design guide §2).

### Step 4 — Update cross-references (see full list in next section)

No source-code references to the legacy `SE-1..SE-8` strings exist yet — U15b hasn't shipped — so the migration is documentation-side only at this stage. Archive references in `autoresearch/archive/*/` are historical-fixture outputs and are untouched (sessions retain their original `rubric_version` field for attribution).

### Step 5 — Historical fixture re-scoring (do NOT)

**No re-scoring under the new spec.** Per legacy revision policy AND design guide §15 (calibration is per-version): scored variants whose `rubric_version: site-quality-v1` field references the archived rubric stay valid against their original anchors. Re-scoring is an explicit re-calibration cycle, triggered only after the new spec stabilizes through ≥1 month of variant iteration on ≥3 fixtures AND longitudinal monitoring shows scores tracking the underlying quality dimension. Otherwise leave historical scores alone — they're attributable to their own rubric version.

### Step 6 — Calibration set construction

Per design guide §15: 100 fixtures × 5 criteria = 500 JR-labeled binary verdicts. Stratify across artifact types (hero / value_prop / social_proof / faq / cta / pricing per plan-002 §1620), quality levels (both score-1 and score-0 ground-truth), and archetypes (b2b_saas canonical, b2b_regulated DWF, b2c_aesthetics Klinika, b2b_tech U19). Seed ~20 fixtures from the 2026-05-13 landing-page session (JR's hand-graded teardowns relabeled against the new outcome questions). Weekly probe + monthly re-label per §15 cadence.

---

## Cross-reference cleanup list

Documentation files mentioning `site-quality.md` or `SE-[1-8]` that need updating once the new spec is locked:

| File | Reference count | Action |
|------|----------------|--------|
| `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md` | ~20 | Heavy revision of TD-30, R29-R34, D26, D27, U15b prose, operational-notes calibration-data row. Bundle into a single plan-002 patch commit. |
| `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` | self | Promote to source-of-truth; add status: locked once v0 review passes. |
| `docs/research/2026-05-18-judges-domain-site-engine.md` | 1 | Add "implemented in [link]" footer. |
| `docs/handoffs/2026-05-18-judge-design-next-session-brief.md` | 1 | Update reference. |
| `docs/handoffs/2026-05-15-judge-design-next-session-brief.md` | 1+ | Update reference. |
| `docs/handoffs/2026-05-18-judge-design-7-lanes-research-dispatch.md` | 1+ | Update reference. |
| `docs/research/2026-05-18-geo-dual-audience-tension.md` | 1 | Update reference. |
| `docs/rubrics/site-quality.md` itself | self | Move to `docs/rubrics/archive/site-quality-v1.md` with frontmatter banner. |

Code files (none yet — U15b hasn't shipped). When U15b lands:

| File | Reference | Action |
|------|-----------|--------|
| `src/evaluation/rubrics.py` | future `RubricTemplate.prose_ref` entries for SE-A..SE-E | Point at new spec path (or inline in `rubrics.py` if the inline pattern wins over file-anchor refs). |
| `tests/test_site_engine_substrate.py` | future test scaffolding | New criterion IDs SE-A..SE-E, not SE-1..SE-8. Update before U15b ships. |

The legacy `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` reference in `site-quality.md` line 345 ("sibling rubric file ... same anchor-design convention") is a back-reference into a sibling file — that file should get its own design-guide retirement triage as a separate dispatch (x_engine has its own X-1..X-6 axes).

No `compound-engineering:site-improvement` skill exists in `.claude/skills/` or `~/.claude/skills/` per a 2026-05-18 search — the legacy `site-quality.md` frontmatter line 9 ("Consumed by ... the `compound-engineering:site-improvement` Claude Code skill") was speculative and is already noted as such in plan-002 D27 ("dual-consumer rationale dropped per Pass-5 audit — that skill is unconfirmed"). No skill-side cleanup needed.

---

## Open questions

1. **SE-D vs SE-A redundancy.** SE-A tests "would persona click"; SE-D tests "can a marketer name persona + alternatives + decision." Pre-empirical hypothesis: different angles on reader-fit; >0.7 correlation plausible. Redundancy check answers empirically.

2. **Voice persona — strict reassignment or partial retention?** SE-4 routes cleanly to shared voice-persona infrastructure, but landing-page copy has voice-fit signals (e.g., "Powered by AI" boilerplate on a manifestly anti-AI-slop brand) other lanes don't surface as cleanly. Consider keeping voice-fit as a `structural_gate` check (corpus-distance threshold per legacy SE-4 falsifiability) rather than fully cross-lane. Defer to first fixture pass.

3. **SE-B empirical validation.** The new AI-engine-citation criterion is the most novel addition; the legacy rubric never tested it. Calibration construction should over-sample SE-B fixtures in the first 25 — ≥10 fixtures with JR's independent evidence of how AI engines actually treat them (Perplexity logs, ChatGPT search citation, Profound/Yext data). Without grounding, SE-B is theory-anchored rather than fixture-anchored.

4. **First-cohort overfitting.** CI lane's v3.3 added a §1.5 Empirical-validation-scope note; site_engine v0 doesn't yet. Worth adding: site_engine criteria are research-grounded against b2b_saas (gofreddy canonical) + the 2026-05-13 calibration session. b2c_aesthetics (Klinika) may need different "primary CTA" expectations (book-consultation, not book-demo); b2b_regulated (DWF) may need stronger SE-C anchors per legal-marketing compliance.

5. **`rubric_version` — no compat shim needed.** Legacy `rubric_version: site-quality-v1` persists in historical scores; new spec ships as "site-engine-v1." Version is a label, not a contract — historical records stay attributable, new records start fresh.

6. **Single-page vs full-site artifact (from v0 spec §9.1).** Fixtures currently scope section-level per plan-002 TD-28. Full-site expansion later may need SE-D / SE-E aggregate variants. Defer.

7. **Anti-slop calibration freshness (from plan-002 §307).** SE-8's retired feature-checklist remains useful as workflow-side meta-agent training material ("do not produce content matching `docs/rubrics/archive/site-quality-v1.md` §SE-8") without being judge-side scoring criteria. Clean separation: workflow-side anti-pattern awareness ≠ judge-side feature-checking. Confirm the workflow-side incorporation doesn't drift back into judge prose.

---

## Summary verdict

The legacy `docs/rubrics/site-quality.md` SE-1..SE-8 rubric is comprehensively retired under the v0 spec. Two axes (SE-5, SE-7) and most of one more (SE-6) are pure deterministic checks that route to `structural_gate`. Two axes (SE-1, SE-2) merge into a single human-conversion outcome question. One axis (SE-3) carries through as the proposition-specificity criterion. One axis (SE-4) reassigns to shared voice-persona infrastructure. One axis (SE-8) splits — the feature-check checklist half cuts entirely (perishable; design-guide §12.1 anti-pattern), the genuine outcome half folds into the AI-citation criterion. The legacy rubric lacks two of the v0 spec's five criteria (SE-B AI-engine citation; SE-E freshness + entity stability) — both addressing Q1 2026 reality the 2026-05-13 calibration session predates.

Final v1: 5 criteria, no exception, no documented breach of the design guide's ≤5 ceiling. Migration is documentation-side only (no live code consumes the legacy rubric yet — U15b hasn't shipped). Historical scored variants stay attributable to their existing `rubric_version` field; no re-scoring required.

The retirement is clean. The substantive work is now (a) the redundancy check on the 5 v0 criteria against 5 fixtures × 3 panel models, (b) the structural_gate expansion to absorb SE-5/6/7 deterministic checks, and (c) the calibration-set construction per design guide §15. None of these is blocked by the retirement decision itself.
