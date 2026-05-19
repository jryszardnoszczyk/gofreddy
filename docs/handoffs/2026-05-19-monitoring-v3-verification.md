---
date: 2026-05-19
type: adversarial verification — MON v3 surgical-edits closure check against v2 spot-check findings
target: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md (v3 surgical edits)
inputs:
  - docs/handoffs/2026-05-19-monitoring-v2-spot-check.md (v2 findings)
  - docs/rubrics/judge-design-guide.md (canonical conformance reference)
reviewer-mode: adversarial — verify each surgical edit closes the v2 finding it claims to close; flag residual gaps
verdict-summary: MOSTLY-CLOSED with two PARTIAL findings and one explicit aspiration. Architecture preserved cleanly; the four hardest v2 risks are addressed honestly (PATH-A choices, not concealment). Two findings remain — substitute-reader validation and Component-C judge-vs-structural-gate tension — are openly aspirational rather than resolved.
depth: standard (verifying ~10 named v2 findings against ~5 surgical-edit clauses in v3)
---

# §1. Reader

The reader is JR (or a future judge-design engineer) deciding whether the v3 surgical edits are sufficient to lock the MON spec at the same maturity bar as CI v3.4, or whether residual risks from the v2 spot-check still block lock. The reader is reading to make a binary decision: does v3 close the v2 audit, or are there findings still requiring a v4 pass?

Secondary reader: any future agent picking up MON-lane work after the spec ships into the v006 evolution loop. They need to know which v2 risks were *resolved* vs which were *consciously deferred with explicit posture*, since deferred-with-posture is acceptable for ship but resolved-as-claimed is not the same epistemic standard.

# §1.5. Artifact under review

`docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` at v3 (2026-05-19). The v3 changes are explicitly scoped to surgical edits per the v2 spot-check audit — five named edits in the revision history, with criterion prose (MON-1..MON-6), multi-component architecture, §3 catalogs, §5 wrapper, and v1 surgical restorations all explicitly preserved unchanged.

The v3 revision history names the audit-closure commitments: (1) MON-5 PATH-A evidence-strengthening via BrokenMath citation; (2) Component C scope conflation resolved via structural_gate-target reframing; (3) §1.5 substrate-readiness gate clause added; (4) §1 first-cohort overfitting posture made explicit; (5) sibling-fork thresholds reframed from "3+ clients" round number to relative-revenue + multi-quarter gate. The v3 verdict depends on whether these five edits actually close their respective v2 findings.

---

# §4. Per-finding verification

## Finding 1 — MON-5 documented-exception evidence (BrokenMath citation)

**v2 claim:** the §5 documented-exception clause requires "measured effect sizes from 2024–2026 literature"; MON-5 cited literature refs but no measured rate; Tetlock GJP is human-superforecaster capability, not LLM failure rate; 2603.16643 is general sycophancy, not absence-fabrication specifically.

**v3 state:** BrokenMath (arxiv 2510.04721, Oct 2025) cited in §7 as the "closest published measurement to an absence-fabrication rate the 2024–2026 literature currently offers" — measuring LLM behavior on problems with no solution / contradictory premises / removed-information inputs across GPT-4o / Claude / Gemini families. The v3 prose explicitly acknowledges this is *the closest analog*, not an identical substrate, and preserves the §8 #2 redundancy-check absorption prediction as honest provisional posture rather than treating BrokenMath as a definitive lock.

**Verdict: PASS** (with honest scope caveat baked in). The v3 evidence is genuinely stronger than v2 — BrokenMath IS a measured-rate paper across frontier families on a structurally-analogous failure shape. The remaining gap (no paper measures weekly-digest absence-fabrication directly) is *named* in the spec ("Honest disclosure" subsection at §7), not concealed. This is the right posture: ship on the closest-analog measurement, name the residual gap, predict the redundancy-check outcome.

The edit does what the v2 finding required. Confidence HIGH (0.85+).

## Finding 2 — MON-5 ↔ MON-1 absorption epistemic incoherence

**v2 claim:** v2 §8 #2 predicted MON-5 ↔ MON-1 absorption while §7 doubled down on MON-5 as a documented exception — "you either have evidence the criterion is structurally distinct, in which case it earns the breach, or you predict it'll absorb, in which case the breach is provisional and probably wrong. Pick one."

**v3 state:** PATH A explicitly chosen in revision history. v3 §7 §1.5 inserts an "Honest disclosure" subsection stating that ship-with-measured-rate-evidence AND ship-with-absorption-prediction are "both honest, not contradictory": MON-5 ships on BrokenMath as the strongest available evidence; if the §8 #2 redundancy check fires, MON-5's CoT step ("verify absence claims have named corpus-anchored baseline") survives as a CoT addition to MON-1, not a standalone criterion, and the live count drops to 5. That outcome is explicitly framed as acceptable and predicted, not as a v3 failure.

**Verdict: PASS.** The epistemic incoherence is dissolved by reframing the two positions as a sequential decision: (a) ship-time evidence threshold met → 6-criterion lock OK; (b) post-redundancy-check measured outcome → absorb if absorption empirically fires. This is the right epistemic move — the v2 critique was correct that you can't claim *both* "structurally distinct" and "likely to absorb" simultaneously; v3 separates the two claims by time-horizon (ship-time vs post-check). Confidence HIGH (0.85+).

Caveat: the v3 prose still leans hard on "MON-1..MON-4 + MON-6 cannot catch fabricated absences" — this is the original v2 claim that the spot-check stress-tested. The spot-check argued MON-1's "Step 2: identify whether a baseline / comparator / delta is named with its source" would catch a fabricated absence the same way it catches a fabricated delta. v3 doesn't refute this directly; it instead concedes via the redundancy-check absorption prediction. That concession is honest. The PATH-A choice means: don't relitigate the structural-distinctness claim now; let the redundancy check decide. Acceptable.

## Finding 3 — Component C scope conflation (structural_gate target framing)

**v2 claim:** v2 named Component C as "the single highest-leverage 2026 modernization" but treated it as structural_gate-only, not judge-scored. This created tension: "if this is the highest-leverage modernization, why is the judge layer not testing its semantic quality?"

**v3 state:** explicit scope-separation clarification at §1.5 Component C ("Scope-separation clarification (v3, per spot-check audit)"). The "highest-leverage 2026 modernization" framing is preserved as a *structural_gate validation target* ("Component C exists in the bundle and contains AI-engine-citation tracking across at least 3 engines with the required content fields"), NOT a judge-criterion target. The judge scopes Component A; structural_gate validates Component C exists + has minimum-shape content. The v2 marketing-rhetoric tension is resolved by making the framing operationally precise: high-leverage at the *lane* level, structural-gate-validated at the *judge-design* level.

**Verdict: PASS.** The reframing closes the v2 tension cleanly without dropping the architectural claim that Component C matters. This is the right move: "highest-leverage" is a *product* claim about the lane's portfolio; the judge-spec's job is to be precise about *which layer scores what*. v3 does both. Confidence HIGH (0.80+).

Residual: the deeper v2 concern — that vendor tooling drift within months may make Component C's underlying telemetry unstable on a quarterly horizon — is still acknowledged at v3 §8 #12 (the v2-pass methodology-drift open question) but not closed. This is acceptable since the v2 finding flagged it as MODERATE (0.65) rather than HIGH severity. Treat as: explicit deferral, not pretend-resolution.

## Finding 4 — Substrate-readiness gap (§1.5 gate)

**v2 claim (Risk 1 + Risk 2):** MON-5 / MON-6 require multi-week corpus; Components B–E require infrastructure (watchlist persistence, cross-lane acknowledgment, prompt-corpus tooling) not documented as built. Without a substrate-readiness checklist, v3 lock risks Phase-4 pathology repeat.

**v3 state:** explicit "Substrate-readiness gate" paragraph inserted at §1.5 — names the comprehensive workflow target (A + B + C + D + E), names that Component A ships at substrate-current, enumerates per-component substrate prerequisites for B–E (B = watchlist persistence layer; C = per-engine citation-tracking tooling; D = CI-lane MON-handoff schema lock; E = multi-week corpus context wired — "the single largest substrate prerequisite per research §6"), and explicitly states "until each component's substrate emits, structural-gate fails if v3 ships against the full bundle. Comprehensive scope is the SPEC TARGET; client-side shipping is gated on substrate readiness."

**Verdict: PASS.** The clause does what the v2 risks demanded — separates spec target from shipping target, enumerates substrate prerequisites per component, gates client-side shipping on substrate emission. This is the cleanest of the v3 surgical edits and addresses both Risk 1 and Risk 2 from the v2 spot-check simultaneously. Confidence HIGH (0.85+).

Minor caveat: the clause does not include a *standalone* checklist artifact (e.g., a separate "Substrate Readiness Checklist for MON v3" document). The v2 spot-check recommendation phrased it as "publish a substrate-readiness checklist." v3 inlined the prerequisites in the §1.5 paragraph rather than externalizing them. For ship purposes this is functionally equivalent; for ops execution a separate checklist would be cleaner. Not a v3-blocking gap.

## Finding 5 — Sibling-fork thresholds (round-number → relative-revenue)

**v2 claim:** "3+ clients" round-number heuristic for mon_pager / mon_aeo_citation / mon_quarterly forks misfires either direction depending on agency size. v2 recommended converting to "≥X% of retainer revenue attributed to the sibling demand."

**v3 state:** all three fork triggers (§8 #5 mon_pager; §8 #6 mon_aeo_citation; §1.5-E + §6b mon_quarterly) reframed to "≥15% of agency-side revenue from monitoring engagements OR ≥3 clients consistently request it for 2+ consecutive quarters, whichever comes first." The threshold rationale paragraph at §8 #5 explicitly names the v2 failure-mode framing: "absolute client-count alone misfires either direction (3 clients at 2-client-base = 150% of book; 3 clients at 30-client-base = 10% of book); relative-revenue threshold scales as the agency grows; the 2+ consecutive quarters gate prevents one-off demand spikes triggering a sibling-lane fork."

**Verdict: PASS.** This is the most rigorous of the v3 edits — picks up the v2 finding verbatim, makes the threshold OR-of-two-conditions to handle both early-stage and late-stage failure modes, adds the temporal stability gate (2+ consecutive quarters) to prevent one-off-demand triggering. The 15% number itself is unsourced (could be 10% or 20%), but the *structural* fix is correct and consistent across all three fork triggers. Confidence HIGH (0.80+).

## Finding 6 — First-cohort overfitting posture

**v2 claim (Risk 3):** v2 broadened to 9 substitute readers without per-persona fixture validation; risked "looks generic enough" rather than "actually serves the modal client." v2 recommended dropping substitute readers until each has a fixture.

**v3 state:** explicit "First-cohort overfitting — explicit posture" subsection at §1, naming both directions of failure: (a) overfitting to current first-cohort (DWF + Klinika + AI-lab) inheriting decision-shape biases; (b) underfitting via broadened substitute-reader list optimizing for "looks generic enough." Mitigation paragraph: "the spec explicitly does NOT claim those personas are served until per-persona fixtures land … §8 #4 + §8 #8 are explicit re-validation triggers when new-vertical fixtures land. Until those fixtures land, the spec treats the substitute-reader list as a design-aspiration scaffold, not a validated coverage claim."

**Verdict: PASS.** The v2 finding required *posture explicitness* on a known-unresolvable problem (fixtures don't exist yet). v3 delivers that explicit posture — names the risk, names that mitigation depends on fixtures the spec doesn't have, marks the substitute-reader list as scaffold-not-coverage-claim, schedules re-validation when fixtures land. This conforms to CI v3.4 + GEO precedent for first-cohort discipline. Confidence HIGH (0.85+).

## Finding 7 — Substitute-reader breadth without validation

**v2 claim:** the 9 substitute readers + 3 decision_shapes + 7 verticals cross-product is "aspirational generality, not demonstrated generality."

**v3 state:** partially addressed by Finding 6's posture clause. The 9 substitute readers remain listed; the v3 edit reframes them as "design-aspiration scaffold" rather than dropping them.

**Verdict: PARTIAL.** v3 closes this finding via *honest reframing* rather than via *fixture validation*. This is acceptable for ship but it's distinctly weaker than the v2 spot-check's stricter recommendation (drop until each has a fixture). The honest-reframing approach is consistent with the rest of the spec's risk posture, and the §8 #4 + §8 #8 re-validation triggers are explicit. Treat as: openly-aspirational scaffold with explicit fixture-trigger gates. Confidence MODERATE (0.70) that this is acceptable for ship; HIGH (0.85) that it's NOT a concealed gap — v3 is honest about the residual.

## Finding 8 — Component C vendor naming risk (~9 vendors)

**v2 claim:** ~9 vendors named (Profound, AthenaHQ, Daydream, Otterly, Peec, Scrunch, Bluefish AI, Goodie) as "2026 dedicated entrants" — fragile within months per spec's own §8 #12 admission. v2 recommended naming measurement axes, treating vendors as substitutable.

**v3 state:** §1.5 Component C "Background context (preserved from v2)" subsection retains vendor names but adds: "Vendor names appear here as context, NOT as locked structural_gate prose — they are substitutable; the structural_gate validates measurement axes (per-engine citation frequency, citation tier, sentiment, drift), not vendor identity."

**Verdict: PASS.** The v3 edit closes the v2 finding's *substantive* concern — the structural_gate is now explicitly axis-based not vendor-based — while preserving the contextual prose for readability. This is the right move; vendor names as background context are fine, vendor names baked into structural_gate prose are fragile. Confidence HIGH (0.80+).

## Finding 9 — Scope conflation between judge design and product roadmap

**v2 claim:** the spec was doing both judge-criterion design AND lane-scope/product-roadmap work, with the lane-scope half importing product claims ("moat surface," "highest-leverage modernization") that don't earn the structural-gate prose they drive.

**v3 state:** partially addressed by Finding 3's Component C scope-separation. The "moat surface" framing at §1.5 Component D is unchanged in v3 (the revision history names Component C scope-separation but not Component D moat framing). v3 §1.5 D still says "the handoff manifest IS the moat surface."

**Verdict: PARTIAL.** The Component-C half of this v2 finding is closed (Finding 3 above). The Component-D moat-framing half is NOT explicitly closed — v3 surgical edits did not name Component D as a target. This is the most surgical-edit-bounded of the v3 verdicts: the v3 author appears to have chosen to close the *load-bearing* scope-conflation (Component C, where it actually drives criterion design) and leave the *Component-D moat-framing* as preserved-v2-prose since it doesn't bleed into judge criterion prose. Defensible but a residual gap. Confidence MODERATE (0.65) that this matters less than Component C; HIGH (0.80) that v3 didn't address it.

---

# §5. Architecture preservation verification

The v3 revision history claims: "MON-1 / MON-2 / MON-3 / MON-4 / MON-6 criterion prose UNCHANGED. Multi-component program architecture UNCHANGED. §3 modern-lever CUTS / ADDS catalogs UNCHANGED. §5 wrapper UNCHANGED. v1 surgical restorations UNCHANGED."

Cross-checked against the v3 file:

- **6 criteria with TWO documented exceptions (MON-5 + MON-6) — PRESERVED.** §4 contains MON-1..MON-6 unchanged; §7 retains "TWO documented exceptions" framing; MON-5's "Note on the ≤5 ceiling" + MON-6's "Note on the ≤5 ceiling" both present.
- **MON-1..MON-6 prose — PRESERVED.** Spot-checked each criterion's outcome question, score-1 anchor, score-0 anchor, score-0.5 anchor, and CoT steps; all match v1.1 + v2.
- **Multi-component program — PRESERVED.** §1.5 retains Components A–E structure; Component C scope-clarification subsection added inline without restructuring; Substrate-readiness gate paragraph added inline at top of §1.5 without restructuring.
- **§5 wrapper — PRESERVED.** decision_shape-aware (a/b/c cadence) + editorial-restraint prose discipline both present unchanged.
- **§3a/§3b CUTS/ADDS catalogs — PRESERVED.** 22 CUTS + 22 ADDS present unchanged from v2.
- **v1 surgical restorations — PRESERVED.** §8 #14 "Live-code prose restorations applied 2026-05-18" retained verbatim from v2; the five folds (a)–(e) all named.

**Verdict: PASS.** The v3 surgical-edit claim of preservation holds. Confidence HIGH (0.85+).

---

# §6. Overall verdict

**MOSTLY-CLOSED.** v3 is genuinely a surgical-edits pass over v2, not a stealth rewrite. Of the nine v2 findings verified:

- **PASS (7 findings):** MON-5 evidence strengthening (BrokenMath PATH A), MON-5↔MON-1 epistemic incoherence (PATH-A separation by time-horizon), Component C scope conflation (structural_gate target reframing), substrate-readiness gate (§1.5 paragraph), sibling-fork thresholds (relative-revenue + 2+ consecutive quarters), first-cohort overfitting posture (§1 explicit clause), vendor-naming-as-context-not-locked-prose.
- **PARTIAL (2 findings):** substitute-reader breadth (closed via honest reframing rather than fixture validation; defensible for ship but explicitly aspirational); scope conflation between judge design and product roadmap (closed for Component C, NOT closed for Component D moat framing).

The v2 spot-check's top three risks are addressed:

- **Risk 1 (MON-5/MON-6 ship before substrate supports):** addressed via §1.5 substrate-readiness gate paragraph naming per-component prerequisites and gating client-side shipping on substrate emission.
- **Risk 2 (multi-component lane scope outruns evolution-loop selection pressure):** addressed via same §1.5 gate + Component C scope-separation + the explicit "structural-gate fails if v3 ships against the full bundle before substrate emits" clause.
- **Risk 3 (first-cohort overfit through substitute-reader proliferation):** addressed via §1 explicit overfitting/underfitting posture; substitute-reader list reframed as design-aspiration scaffold with §8 #4 / §8 #8 re-validation triggers.

**Recommendation:** v3 is ship-ready at CI v3.4 maturity bar. The two PARTIAL findings (substitute-reader fixture validation, Component D moat framing) are openly aspirational rather than concealed, and the spec's posture on both is explicit. Lock v3. Defer the Component D moat-framing scope-conflation to a future v4 if/when CI/GEO/marketing_audit cross-lane acknowledgment infrastructure lands and Component D moves from aspirational to operational.

**Do not propagate to GEO / marketing_audit / SB / X / LI / site_engine until:** (a) v3 redundancy check fires (§8 #2 — predicted MON-1↔MON-5 absorption); (b) multi-week corpus prerequisite ships (§8 #1 — gates MON-6 functional testing); (c) at least one non-first-cohort fixture from financial-services / regulated-industries / DTC e-commerce lands and is validated against the spec. The v3 substrate-readiness gate is a closure not an excuse to skip these.
