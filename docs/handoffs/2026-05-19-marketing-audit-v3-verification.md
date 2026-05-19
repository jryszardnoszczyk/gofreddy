---
date: 2026-05-19
type: adversarial verification of v3 surgical edits against v2 spot-check findings
target: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md (v3 — 696 lines, ~9,800 words)
parent: docs/handoffs/2026-05-19-marketing-audit-v2-spot-check.md (v2 findings)
reviewer-role: MA lane adversarial verification reviewer (highest-stakes — v2 had verifiable substrate gap, 1/4 client sessions emit required files)
status: complete
---

# Marketing Audit v3 verification — did the surgical edits actually address the v2 spot-check?

## Summary verdict

**LANDED with one residual epistemological concern + two cosmetic-but-load-bearing leaks.** Of the 9 v2 findings, **7 are cleanly addressed**, **1 is partially addressed** (the 9-section / 12-axis dual-schema), and **1 is addressed at the criterion-prose layer but leaks into the §5 shared judge-prompt wrapper** (the realigned word-count band). Architecture preservation checks all pass: 5-criterion ceiling held, MA-1 / MA-2 / MA-3 / MA-5 prose unchanged outside the dedup + 6-class consistency touches, MA-4 cleanly reduced from 4 to 3 elements, all 9 v1 surgical-restoration folds (F1–F9) preserved verbatim, 149-lens / 12-macro-axis framing intact.

This is a materially safer v3 than v2 was. The substrate-readiness gate is the load-bearing correction and it lands honestly — judge scopes to `findings.md` only, with the multi-file deliverable explicitly held as SPEC TARGET pending substrate-build prerequisite closure. The remaining concerns are cleanup-scope, not re-design-scope.

---

## Per-finding verification

### 1. Cluster A/B/C reborn at MA-4 + §1 commissioning-context routing — DROPPED? **YES, cleanly.**

v2's §1 carried three "commissioning shapes" (personnel / operational / strategic) that mapped to per-criterion emphasis in MA-4 element 4. The v2 spot-check named this as "cluster routing implemented as a per-fixture context flag rather than a per-fixture artifact-shape flag." v3 §1 now contains an explicit "Commissioning-context routing DROPPED in v3" paragraph (line 40) that names the spot-check finding and removes the routing entirely: "the comprehensive audit is invariant of commissioning context." MA-4's §4 prose (line 369–394) is reduced from 4 elements to 3 — stage diagnostic + Phase-0 9-meta-frame integration + wrong-stage refusal — with the v3 NOTE block (line 371) explicitly citing the Phase-4 pathology rationale. MA-4's "Do not score" line (line 394) adds "commissioning context (DROPPED in v3 as judge-imagined classification)." §6 Goodhart-resistance verification (line 524) carries the drop forward: "v3: commissioning-context emphasis match DROPPED — it was judge-imagined classification (Phase-4 pathology)." §8 item 8 (sibling-fork triggers, line 649) explicitly closes the door on a personnel-verdict fork being smuggled back in via subcluster fork.

**Residual:** none. The drop is complete and the rationale chain (v1 cluster A/B/C → v2 commissioning-context emphasis → v3 dropped) is documented in three places (§1, MA-4 v3 NOTE, §6, §8 item 8, end notes).

### 2. Substrate-readiness gap — addressed via §1.5 gate (judging `findings.md` only, structural_gate doesn't block on missing files)? **YES, load-bearing and well-anchored.**

v2 spot-check showed 4-client empirical state: findings 4/4, gap_report 3/4, proposal 1/4, roadmap 0/4, cuts_reduces_adds 0/4. v3 §1.5 carries a dedicated "Substrate-readiness gate (LOAD-BEARING — empirically verified 2026-05-19)" subsection (lines 119–132) that names the empirical state verbatim and inverts the locking sequence: "**v3 ships JUDGING `findings.md` only.** The structural_gate validates the other files EXIST when substrate emits them, does NOT block on their absence." §8 item 0 (lines 551–564) elevates the substrate-build prerequisite to "HIGHEST priority" as an open question and quantifies the path forward ("2–4 sprint-weeks of workflow code work before v3 can ship against the full multi-file bundle"). §8 item 1 (line 568) carries the substrate-readiness note into the multi-file structural_gate spec: "Until §8 item 0 (substrate-build prerequisite) closes... the structural_gate per §1.5 substrate-readiness gate validates only the files that substrate currently emits."

**Residual concern (MODERATE, 0.65):** the §5 shared judge-prompt wrapper (lines 437–513) still describes the multi-file deliverable as if it were live ("The artifact is a multi-file deliverable: findings.md — the strategic spine (5,000–9,000 words)..."). Two leakages: (a) the wrapper still cites the v2 band 5,000–9,000 instead of the v3-realigned 2,000–9,000, and (b) the wrapper lists `roadmap.md`, `proposal.md`, `cuts_reduces_adds.md`, `gap_report.md`, `vertical_overlay.md`, `geo_overlay.md` as present without qualifying that judge-core scopes to `findings.md` only per §1.5. A panel-judge reading the wrapper prose before §1.5's substrate-readiness gate could plausibly downscore a one-file submission for "missing" the other files because the wrapper describes them as present. The judge sees the wrapper at score time, not §1.5. **Fix:** re-prose the wrapper's artifact description to match the substrate-readiness reality: "The judge scores findings.md against MA-1..MA-5; multi-file deliverable is SPEC TARGET pending substrate-build (see §1.5)." This is a 2-line edit, not a redesign.

### 3. 9-section vs 12-axis dual-schema — addressed? **PARTIALLY. The handwave persists; the resolution does not.**

v2 spot-check called this out as "F8's 'both coexist' is the architectural duplication" and demanded a pick-one resolution. v3 §1.5 does not resolve it; v3 §8 item 1 carries the same 9-section deliverable-shell check + the 12-axis structure language verbatim from v2 ("Both structures coexist: the 9-section shell organizes the deliverable surface area the agency engagement covers; the 12-axis structure organizes the reader-facing strategic argument. Live code's STRUCTURAL_DOC_FACTS tuple already encodes the 9-section check; preserve"). F8 in §8 item 10 (line 666) explicitly preserves the dual-schema as a v1 surgical-restoration fold without further resolution.

**Residual concern (HIGH, 0.80):** the v2 spot-check's core argument was that under 50-generation selection pressure, the workflow's stable point is to render the same diagnostic twice — once under one of the 9 sections, once under one of the 12 axes — and the judge will read repetition as comprehensiveness. v3 has not closed this attack surface. The pragmatic reason is honest — the 9-section live code substrate is shipped and the 12-axis framing is research-driven — but the spot-check's specific question ("how does the workflow synthesize 12 axes FROM 9 sections without producing internally-repetitive output?") remains unanswered. The honest v3 disclosure would be either (a) explicitly mark this as a known organizational duplication held over from v2 pending Stream B-style substrate work, or (b) commit a §8-item-anchored decision (similar to §8 item 0's substrate-build prerequisite) that resolves the schema before propagation. As written, the spec carries the duplication forward and the variance-instrumentation pattern from design guide §11.5 will only catch it after several generations of co-adapted output.

### 4. Word-count band aspirational (5,000–9,000 vs reality ~2,200) → realigned to 2,000–9,000? **YES at §1.5 + §8 + §3; LEAKS at §5 wrapper.**

v2 spot-check showed real findings.md word counts of 1042 (Anthropic), 1868 (Perplexity), 2639 (DWF), 6156 (Stripe) — median ~2,200. v2's 5,000-word floor would have failed 3 of 4 production sessions structurally. v3 §1.5 line 79 says "**File 1 — `findings.md` — the strategic spine. 2,000–9,000 words (v3-realigned to live structural_gate; see "Word-count band" subsection below for rationale).**" v3 §1.5 carries a dedicated "Word-count band — realigned to live structural_gate (v3)" subsection (lines 134–136) that names the median (~2,200), the upper bound rationale (matches live structural_gate cap of 8,000 with 1,000-word headroom), and the diagnostic-quality invariance ("a 2,200-word audit that synthesizes 12 axes into ONE strategic narrative still scores 1 on MA-1; a 12,000-word audit that lists 25 disconnected ParentFindings still scores 0"). §8 item 1 carries the realigned band into the structural_gate spec (line 573: "`findings.md` **2,000–9,000**"). §3c (shape-drift Goodhart defenses, line 159) updates the audit-bloat-drift defense to cite the realigned band.

**Residual:** the §5 shared judge-prompt wrapper (line 441) still cites the v2 band 5,000–9,000. Same leakage as finding #2 above; one fix lands both. The live code's hard cap is 8,000 (`session_eval_marketing_audit.py:163-164`); the v3 9,000 upper bound is consistent with the design intent (1,000-word headroom for comprehensive synthesis above the structural_gate cap) but the wrapper prose lags the substrate-aware band by one cycle.

### 5. MA-5 5-vs-6 upstream class disagreement → resolved to 6 consistently? **YES, cleanly.**

v2 spot-check named this as a literal contradiction inside the score-1 anchor (triage walked 5 vs anchor enumerated 6). v3 MA-5's outcome question (line 399) opens with "one of the 6 upstream classes: retention/PMF, ICP, positioning, pricing, sales motion, marketing-internal." The score-1 anchor (line 401) closes the loop: "**6-class triage sequence** is walked in order — retention/PMF → ICP → positioning → pricing → sales motion → marketing-internal." The "Positioning treated as a load-bearing 6th upstream class" subsection (line 403) explicitly names positioning as the 6th. §1.5 line 84 and the end notes (line 690) re-anchor the 6-class triage. The v2 inconsistency ("ICP/positioning" grouped vs "ICP, positioning" enumerated separately) is fully resolved: positioning is the 6th, listed separately, walked in fixed order between ICP and pricing.

**Residual:** none. The 6-class resolution is consistent across §1.5, §4 MA-5 score-1, §4 MA-5 CoT Step 1, §6, and end notes.

### 6. Duplicate cuts #2 and #5 broetry-LinkedIn — deduplicated? **YES, with a usable replacement.**

v2 spot-check called out the literal duplication: "#2 broetry-LinkedIn and #5 broetry-LinkedIn-carryover are the same item." v3 §3a (line 217) replaces #5 with "**Engagement-pod participation as primary growth lever** — LinkedIn-specific gaming via reciprocal-comment / pod-coordinated likes; 2026 algorithm penalizes coordinated inauthentic engagement; reader recognizes as gamed-distribution that does not compound. (Distinct from #2 broetry-LinkedIn — broetry is FORMAT gaming; engagement-pods are DISTRIBUTION gaming.)" The new #5 is materially distinct (format gaming vs distribution gaming), is grounded in 2026 LinkedIn algorithm behavior, and the parenthetical explicitly disambiguates against #2. MA-2's CoT Step 3 (line 327) lists all 12 items including "engagement-pod participation" in the proper position. The 12 → 12 distinct count is restored without changing the structural-gate `MA_BANNED_PHRASES` blocklist (which is a separate 12-corporate-jargon list in live code — verified at `session_eval_marketing_audit.py:37-50`).

**Residual:** none.

### 7. MA-2 ↔ MA-3 redundancy watch added to §8? **YES, with a stronger framing than the v2 spot-check required.**

v2 spot-check argued that MA-2 ↔ MA-3 is "the more likely collapse, not MA-1 ↔ MA-4" because both score against recommendation completeness and revenue-traceability. v3 §8 item 5 (lines 625–631) now runs BOTH pairs ("**Run BOTH pairs.**"). The MA-2 ↔ MA-3 framing is sharper than v2's spot-check requested: "Spot-check audit flagged this as the MORE-likely collapse pair than MA-1↔MA-4: both criteria reward 'names the metric the recommendation moves'... if MA-2↔MA-3 exceeds the 0.7 threshold, MA-3 carries the revenue-chain semantic and MA-2 carries the agency-engagement-pitch / capability-tier-mapping semantic — they should remain separable on those distinct surfaces, but the redundancy check verifies empirically." The fallback resolution if the pair collapses is named (MA-3 carries revenue, MA-2 carries pitch/tier) — that's a stronger v3 disclosure than the v2 ask.

**Residual:** none.

### 8. §8 substrate-build prerequisite documented as HIGHEST-priority? **YES, item 0 (highest position).**

v3 §8 item 0 (line 551, "**0. Substrate-build prerequisite (HIGHEST priority — empirically verified gap)**") opens the §8 list. It carries the 4-client empirical state verbatim, names the path forward (workflow team builds emission infrastructure for the 3 missing files, verify against 5+ client sessions, lift gate via v3.1 spec edit), and quantifies the cost ("2–4 sprint-weeks of workflow code work"). It explicitly subordinates the other §8 items: "every other §8 item (calibration weighting, multi-file structural_gate expansion, fixture coverage, token-cost envelope) is downstream of this prerequisite closing."

**Residual:** none. The HIGHEST-priority elevation is structural (item 0, opens the list) and prose-anchored (explicit subordination of items 1–10).

### 9. First-cohort overfitting posture added? **YES, with explicit CI v3.4 precedent inheritance.**

v3 §1 carries a "First-cohort overfitting posture (load-bearing — same pattern as CI v3.4)" subsection (lines 61–63) that names the architectural posture: US-primary across 6 verticals as design surface; Polish first-cohort (Klinika, DWF) as validation surface only; drift watch trigger named ("if score-1 anchors begin to anchor against Polish-vertical-specific patterns... re-pass §4 and surface to JR as a re-validation trigger"). §8 item 7 (line 638) carries the watch forward with a concrete re-validation trigger ("any fixture from a vertical not in {B2B SaaS, AI lab, agency, service firm, finance, e-commerce, legal, aesthetic medicine}").

**Residual:** none.

---

## Architecture-preservation checks

- **5-criterion ceiling held:** YES. MA-1 through MA-5; no MA-6 introduced. §7 verification line 535 explicitly re-asserts "**5 (at ceiling, no documented exception breach)**" and names the research-predicted MA-6/MA-7 candidates absorbed into MA-1 / MA-4 / MA-5.
- **MA-1 / MA-2 / MA-3 / MA-5 score-1 / score-0 prose unchanged outside dedup + 6-class consistency:** YES. MA-1 (lines 272–296) is verbatim v2. MA-2 (lines 297–331) carries only the dedup edit at CoT Step 3 (engagement-pod replacing broetry-LinkedIn-carryover). MA-3 (lines 333–367) is verbatim v2. MA-5 (lines 396–432) carries only the 6-class consistency edits at outcome question + score-1 anchor + CoT Step 1.
- **MA-4 reduced to 3 elements (commissioning-context dropped):** YES. v3 NOTE block (line 371) explicitly names the drop. Outcome question (line 374) tests stage + Phase-0 + refusal only. Score-1 anchor (line 376) carries the 3-element shape. CoT (lines 388–392) has 4 steps (the 4th is verdict emission, not a 4th content element). "Do not score" line names the drop.
- **9 v1 surgical-restoration folds preserved verbatim (F1–F9):** YES. §8 item 10 (lines 657–667) lists all 9 folds: MA_BANNED_PHRASES (F1), Phase-0 9-meta-frames (F2), capability_registry (F3), severity calibration (F4), voice quality (F5), gap honesty (F6), engagement-fit (F7), 9-section deliverable shell (F8), lens_id traceability (F9). All preserved with original folding-into-criterion mapping intact.
- **149-lens / 12-macro-axis framing:** YES. §1.5 (line 73) carries "comprehensive 149-lens diagnostic across 12 reader-shaped macro-axes" verbatim. §3.b axis enumeration and §8 item 1 structural_gate references all align.

---

## Top 2 residual risks for v3 ship

1. **§5 shared judge-prompt wrapper lags the v3 substrate-readiness reality + word-count realignment (MODERATE, 0.65).** The wrapper prose (lines 437–513) describes the multi-file deliverable as if all 5–7 files were live and cites the v2 5,000–9,000 band instead of the v3-realigned 2,000–9,000. The judge reads the wrapper at score time, not §1.5. A panel-judge could plausibly downscore a one-file submission for "missing" files the wrapper describes as present, or downscore a 2,200-word submission against a 5,000-word floor. **Fix:** 2-line edit to the wrapper artifact description + word-count band. Not a redesign.

2. **9-section / 12-axis dual-schema persists as architectural duplication (HIGH, 0.80).** The v2 spot-check's specific question ("how does the workflow synthesize 12 axes FROM 9 sections without producing internally-repetitive output?") remains unanswered in v3. F8 explicitly preserves both. Under 50-generation selection pressure, the workflow's stable point is to render the same diagnostic twice and the judge will read repetition as comprehensiveness. **Fix options:** (a) explicit §8 item naming this as known-duplication-pending-substrate-work, parallel to item 0's substrate-build prerequisite framing; or (b) propagate the design guide §11.5 variance-instrumentation pattern to track MA-1 ↔ structural_gate-9-section variance specifically.

---

## Bottom line

v3 surgical edits LANDED on 7 of 9 v2 findings cleanly + 1 partially (dual-schema) + 1 with a wrapper-prose leak (word-count + multi-file framing). Architecture preservation is clean across all 9 v1 surgical-restoration folds + the 5-criterion ceiling + the 149-lens / 12-macro-axis framing. The substrate-readiness gate is the load-bearing correction and it is well-anchored at §1.5 + §8 item 0. The two residual concerns are cleanup-scope (wrapper prose) and known-architectural-debt-scope (dual-schema), not redesign-scope. v3 is materially safer to ship than v2 was; the wrapper-prose leak should close in this revision before §8 item 0 substrate-build work begins.
