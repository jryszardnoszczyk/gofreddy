---
date: 2026-05-19
type: verification — x_engine v3 surgical edits against v2 spot-check findings
target: docs/handoffs/2026-05-18-judge-design-step1-x-engine.md (v3, frontmatter dated 2026-05-19)
source: docs/handoffs/2026-05-19-x-engine-v2-spot-check.md (v2 adversarial findings)
guide: docs/rubrics/judge-design-guide.md
posture: adversarial — did each surgical edit actually close the gap it claimed to close, or did it move the gap?
depth: standard — 8 surgical-edit claims to verify against 14 v2 findings + architecture-preservation checklist
---

# X Engine v3 — Verification of Surgical Edits

## Summary

Six of the eight named surgical edits land cleanly. One (§5 wrapper info-leak softening) is **partial-fix-only** — the numerals were removed from the wrapper-adjacent §5 prose but persist verbatim in §8 Q6 of the same file, so the information leak shifted location rather than closing. One (Substrate-Readiness Gate) lands as documentation but does not by itself address the underlying v2 Finding-1 concern (12-component bundle + 10 increments are research-derived without client validation) — it converts the bundle from "ship now" to "ship as substrate emits" without addressing whether the bundle shape is right for any client. Architecture-preservation claims hold: the 5-criterion ceiling is intact, X-1/X-3/X-4/X-5 prose is character-identical to v2, X-2 score-1 and score-0 anchors are unchanged outside the cold-start sub-anchor addition, the wrapper still carries no numerical weights, no AI-detector classifier was integrated, the 12-component + 10-increment architecture is preserved.

Overall verdict: **NEEDS-ONE-EDIT (Finding 8) and one DOCUMENTED-ACCEPTANCE (Finding 1).** Other six edits address the v2 finding they were targeted at.

---

## Per-finding verification

### v2 Finding 6 — X-2 voice.md HARD FLOOR cold-start interaction with Component L (PRE-REQ specified)

**Edit claimed.** Component L specified as PRE-REQ for first-engagement Component A judging; cold-start sub-anchor at X-2 score-0.5 emits "voice substrate not provisioned"; HARD FLOOR does NOT fire when voice.md absent.

**Edit verified.** Line 296 (X-2 Score 0.5): adds the explicit `Voice substrate not provisioned (NEW in v3, Component L PRE-REQ gate)` paragraph. Line 301 (X-2 Required CoT Step 3): adds the `PRE-REQ check (NEW in v3)` clause — if voice.md absent/empty, emit 0.5 + "unknown" + "voice substrate not provisioned" for the whole criterion; do NOT apply HARD FLOOR in this state. Bundle internal ordering stated explicitly: "Component L populates first, THEN Component A's 5 sample posts are judged."

**Verdict: CLOSES v2 Finding 6.** The chicken-and-egg is resolved — the workflow can no longer learn either failure mode (strip lived-work specifics OR fabricate them) because X-2 abstains when the substrate is absent. The score-0 default and score-1 default are both off the table in cold-start regime. **HIGH confidence (0.88).**

**Residual concern:** the abstention path adds a new attack surface — a workflow that learns the substrate-empty abstention path is a way to escape the HARD FLOOR's punitive scoring could attempt to ship without provisioning voice.md. Structural gate's Component L provenance check (§8 Q9) is the upstream defense against this; v3 spec does not enforce it judge-side. Acceptable as documented — the substrate-gate is structural_gate territory.

### v2 Finding 8 — §5 wrapper info-leak (QT 25× / profile-click 12× / reply-with-author-response 150×) removed

**Edit claimed.** Specific reconstructed numerals stripped from in-spec prose; direction-of-effect rationale retained.

**Edit verified — PARTIALLY.** Line 431 (§5 wrapper note): the numerals are gone. The replacement text says *"operator-community reconstructions of action-probability coefficients are not official, anchoring on them invites Goodhart template-fitting against the named numerals"* — no specific numerals. Good.

**But:** Line 500 (§8 Q6) still reads verbatim: *"v2 reaffirms strip even though comprehensive scope research surfaces additional operator reconstructions (QT 25×, profile-click 12×, reply-with-author-response 150×). Same Goodhart vector applies."* The exact information leak the v2 spot-check flagged — the enumeration of which numerical weights the criterion design refused — persists in §8 Q6 of the same spec file. A workflow ingesting this spec file gets the enumeration regardless of where in the file it lives.

**Verdict: PARTIAL FIX.** The information leak moved from §5 to §8 within the same file. If the workflow's substrate-loading reads the whole spec (which it would by default), the leak is unchanged in effect. The §5 prose is now clean; the §8 prose is not. **MODERATE confidence (0.75)** that this is a real partial-fix gap — confirming would require checking which sections of the spec the lane's workflow prompts actually ingest. The internal-design-notes alternative the v2 spot-check recommended (move the reconstructed numerics to a file the lane does NOT read) is referenced in the new §5 note ("Detailed rationale lives in internal design notes") but the relocation has not actually happened — §8 Q6 still carries the numerals in the same handoff file.

**Recommended additional edit:** strike "(QT 25×, profile-click 12×, reply-with-author-response 150×)" from line 500. The §8 Q6 sentence still conveys the same decision without the enumeration: *"v2 reaffirms strip even though comprehensive scope research surfaces additional operator reconstructions. Same Goodhart vector applies."*

### v2 Finding 1 — Multi-component bundle Substrate-Readiness Gate added

**Edit claimed.** Substrate-Readiness Gate added: comprehensive scope is SPEC TARGET; client-side shipping gated on substrate readiness, Component A ships at substrate-current, B-L ship as substrate emission catches up.

**Edit verified.** Line 58 (§1.5): the Substrate-Readiness Gate paragraph is present and explicit. Component A ships at substrate-current (`session_eval_x_engine.py` reliably emits 5 sample posts/threads); B ships when profile-shape extractor exists; C ships when pillar-extraction substrate exists; etc. I3 / I7 / I10 emit at sustained-engagement phase, not first-engagement.

**Verdict: ADDRESSES the CI-parallel scope-conflation concern but DOES NOT address the underlying v2 Finding 1.** The v2 Finding 1 was that the 12-component bundle + 10 per-cycle increments are research-derived without a single client-validation data point — the bundle's *shape* is what the v2 reviewer challenged, not the *timing* of when each component ships. The Substrate-Readiness Gate addresses *when* B-L ship (when substrate emits) but not *whether* B-L are the right components to ship. A workflow whose profile-shape extractor matures still ships Component B; v3 has not asked whether Component B is what a real client wants.

**The CI-parallel recommendation from v2 spot-check ("ship Component A only as production-default; treat B-L as on-demand evidence") is NOT the path v3 took.** v3 instead committed to the bundle as SPEC TARGET and deferred the question to substrate-emission timing. This is a deliberate JR-locked decision per the v3 frontmatter ("All v2 scope (12-component bundle + 10 per-cycle increments) preserved"). The decision is documented; the v2 finding's underlying premise-challenge is not closed, it is accepted-and-deferred.

**Verdict: DOCUMENTED ACCEPTANCE, not closure.** The v3 spec explicitly preserves the 12-component scope. The Substrate-Readiness Gate makes the rollout sequential rather than simultaneous but does not change the bundle's composition. **HIGH confidence (0.85)** that this is a partial response — the substrate-readiness framing is useful (it prevents shipping empty/half-baked components) but the v2 Finding 1 was about whether B-L are the right components, and that question is still open. The §1 first-cohort exemption (next finding) partially addresses one slice of this — for Polish + regulated-vertical clients, F/G/H are explicitly N/A. That is the only concrete bundle-shape edit v3 made.

### v2 Finding 3 — §1 first-cohort overfitting + Polish-regulated F/G/H exemption

**Edit claimed.** Polish + regulated-vertical first-cohort (Klinika, DWF) does NOT apply Components F (Spaces brief), G (Communities map), H (series-arc storyboard) as core deliverables.

**Edit verified.** Line 43 (§1, new paragraph after the prior overfitting watch): the exemption is explicit. Klinika (medical_pl, b2c_aesthetics) and DWF (legal_pl, b2b_regulated) get bundle composition A + B + C + D + E + I + J + K + L; F + G + H are marked N/A with per-component rationale. Component A judging applies to all clients regardless of cohort. Rationale named per component (Spaces regulatorily ambiguous; Communities off-vertical for English-language B-i-P / IndieHackers / ML Twitter; series-arc-as-public-build-in-public structurally inapplicable to clinical and partnership-track legal practices).

**Verdict: CLOSES v2 Finding 3 at the per-client bundle-manifest layer.** This is the one concrete bundle-shape edit in v3. **HIGH confidence (0.90).**

**Residual concern (not blocking):** the rationale is captured per component but the bundle architecture in §1.5.1 still ships F/G/H as table rows applicable to all clients. The exemption lives in §1 prose, not in the §1.5.1 component table. A reader of the table alone would not see the exemption. Minor doc-shape issue; not a closure failure.

### v2 Finding 5 — I3 reply-judging >50% un-judged lane output documented in §8

**Edit claimed.** I3 reply-judging deferred to v3.1; >50% lane output un-judged at criterion layer accepted for v3; observe via variance instrumentation.

**Edit verified.** Line 571 (§8 Q21): new open question added. Explicitly states: *"I3 substantive replies (10-20/week steady-state) are NOT judged at criterion layer; structural_gate validates shape only. Combined with I4 (1-3 QTs/week, also structural-only), this means >50% of the lane's steady-state output volume is un-judged at criterion layer."* Path forward: defer to v3.1 (reply-adapted 5-criterion judge per research §1.6) or fork x_replies sibling lane if reply-discovery becomes load-bearing. Trigger: variance instrumentation divergence between judge means and real-world engagement.

**Verdict: CLOSES v2 Finding 5 as documentation.** The concern is named, the deferral is explicit, the trigger for v3.1 / sibling-fork is specified. This is acceptance-with-instrumentation, not resolution — exactly the path the v2 finding's "documented acceptance" path would have endorsed. **HIGH confidence (0.85).**

**Residual concern:** the variance-instrumentation signal (judge means vs real-world engagement) requires real-world engagement data to compute. Until the lane ships to real clients with measurable engagement, the divergence signal is unmeasurable. Same deferral-without-measurement pattern v2 Finding 9 flagged for BC-1..BC-5. Not addressed.

### v2 Finding 10 — X-6 90% catch-rate threshold reframed to falsifiable variance trigger

**Edit claimed.** X-6 90% threshold reframed to falsifiable variance trigger (Axis C variance vs design-guide §11.5 redesign threshold).

**Edit verified.** Line 490 (§8 Q1 — REFRAMED in v3): two independent decision rules now. (a) *"if X-1 + X-2 + structural_gate combined catch <90% of seeded clickbait test fixtures across 3 generations"* — the original 90% threshold preserved as one rule, but now joined with "across 3 generations" (smoothing single-run noise). (b) *"OR if X-1's Axis C anchor shows variance exceeding judge-design §11.5 redesign threshold"* — the variance trigger uses the design-guide's standing redesign threshold rather than a lane-local invention.

**Verdict: CLOSES v2 Finding 10.** The OR-joined two-rule structure addresses the v2 spot-check's specific concern that a single 90% threshold was performative precision. Either rule firing promotes X-6. Axis C variance is independently measurable from the lane's own per-generation telemetry without requiring the seeded-clickbait fixture set to exist. **HIGH confidence (0.85).**

**Residual concern:** the seeded-clickbait fixture set still doesn't exist (§8 Q8 names fixture-validation but no seeding methodology). Until the fixture set exists, only rule (b) — Axis C variance — can fire. Rule (a) is gated on infrastructure that doesn't ship with v3. Acceptable: rule (b) alone is a falsifiable trigger.

### v2 Finding 2 — §3 modern-lever lane-DNA framing note added

**Edit claimed.** §3 modern-lever framing note added: CUTS/ADDS are LANE PRODUCT DNA expressing failure/success modes, not roadmap items.

**Edit verified.** Line 192 (§3b, new "Framing note (NEW in v3 per spot-check audit)" paragraph): explicit reframe. *"The 20 CUTS and 24 ADDS below are LANE PRODUCT DNA, not roadmap items. They appear in score-0 (CUTS) and score-1 (ADDS) anchors via the verifiable failure/success modes they describe, NOT as roadmap aspirations."* CUTS routed to structural_gate are deterministic shape-checks; CUTS absorbed into outcome criteria (X-2/X-3/X-4/X-5) are failure shapes those criteria score against; ADDS that are product/strategy decisions inform bundle structural-gate shape checks, not judge prose.

**Verdict: ADDRESSES v2 Finding 2 at the framing layer but DOES NOT remove the 20 CUTS + 24 ADDS prose itself.** The v2 spot-check's specific recommendation was that §3c (20 CUTS) and §3d (24 ADDS) be removed from the judge spec — ~1700 words of product-roadmap material relocated to a separate `docs/plans/<date>-x-engine-lane-roadmap.md`. v3 instead added a framing note in front of the same content. The judge still sees the 20 CUTS and 24 ADDS at scoring time; the framing note tells the judge how to interpret them but does not remove the prose density.

**Verdict: DOCUMENTED REFRAME, not removal.** A deliberate scope decision: v3 frontmatter says "No scope reductions" — the framing note is the surgical edit, not relocation. The v2 finding's underlying concern (rubric prose density growth past design-guide budget, attention surface bloat) is not closed; it is reframed as "this content is DNA, not roadmap" so the judge has a different interpretive frame. **MODERATE confidence (0.75)** that the underlying attention-surface concern persists — the spec body is still ~9000-10000 words per §7's own admission. Acceptable as a JR-locked decision; the v2 finding's specific recommendation was not adopted.

### v2 Finding 4 — X-1 3-axis CoT attack-surface concentration

**Edit claimed (implicit).** v3 frontmatter does not list this as a v3 surgical edit. v3 lists 7 surgical edits; X-1 3-axis CoT attack-surface is not among them.

**Edit verified.** X-1 prose (lines 260–281) is character-identical to v2. The 3-axis CoT structure is preserved. No sub-axis variance instrumentation added at §6.

**Verdict: NOT ADDRESSED in v3.** This v2 finding was HIGH 0.85 confidence in the spot-check, citing the design guide's §6 attack-surface rationale (*"the load-bearing reason is attack-surface, not accuracy"*). v3 explicitly preserves X-1's 3-axis CoT and does not add sub-axis variance instrumentation. The §6 telemetry signals (Grok-tone proxy, reply-bait CTA detector, AI-slop signature density) measure cross-criterion drift, not sub-axis-within-X-1 drift.

**Verdict: ACCEPTED-AS-IS without explicit acknowledgment.** v3 frontmatter's list of preserved-without-change items includes "3-axis CoT preserved" — the choice is explicit. The v2 spot-check's specific recommendation (sub-axis variance instrumentation) was not adopted. **HIGH confidence (0.82)** that the X-1 attack surface concentration remains the strongest single-criterion Goodhart attack surface in the lane, unchanged from v2.

---

## Architecture-preservation verification

| Preservation claim | Verified | Notes |
|---|---|---|
| 5-criterion ceiling (X-6 deferred) | YES | §7 line 469: "5-criterion ceiling held; no documented exception." |
| X-1 prose unchanged | YES | Lines 260–281 identical to v2 |
| X-3 prose unchanged | YES | Lines 306–326 identical to v2 |
| X-4 prose unchanged | YES | Lines 328–348 identical to v2 |
| X-5 prose unchanged | YES | Lines 350–375 identical to v2 (including jargon-gloss + regime-aware cold-start) |
| X-2 score-1 unchanged outside cold-start fix | YES | Line 288 score-1 anchor identical to v2 |
| X-2 score-0 unchanged outside cold-start fix | YES | Line 294 HARD FLOOR prose identical; line 296 score-0.5 adds the cold-start abstention; line 301 CoT Step 3 adds the PRE-REQ check |
| Numerical weights stripped from §5 wrapper | YES | Wrapper text lines 381–429 carries no numerals; §5 wrapper note line 431 carries no numerals |
| AI-detector classifier NOT integrated | YES | §3e line 250 + §4 X-5 line 375 "Do not score: ... AI-detector classifier output" preserved; §8 Q9 line 532 "AI-detector classifier output is NOT added" preserved |
| 12-component bundle preserved | YES | §1.5.1 table lines 64–77 unchanged |
| 10-increment architecture preserved | YES | §1.5.2 table lines 83–94 unchanged |

All architecture-preservation claims hold.

---

## Overall verdict

**NEEDS-ONE-EDIT (Finding 8 §8 Q6 numeral strip).** Strike "(QT 25×, profile-click 12×, reply-with-author-response 150×)" from line 500 — the §5 wrapper note was cleaned but the same numerals persist in §8 Q6 of the same spec file. The information leak relocated rather than closed. Single-line edit.

**DOCUMENTED-ACCEPTANCE of Findings 1, 2, 4.** v3 explicitly preserves the 12-component bundle architecture (Finding 1 acceptance via Substrate-Readiness Gate sequencing), the 20 CUTS + 24 ADDS prose in §3c/d (Finding 2 acceptance via lane-DNA framing reframe), and the X-1 3-axis CoT concentration (Finding 4 silent acceptance, no v3 edit). These are JR-locked decisions per the v3 frontmatter ("No scope reductions"). The v2 finding's specific recommendation in each case was not adopted; the v3 spec documents the decision.

**Five other surgical edits land cleanly.** Voice substrate PRE-REQ gate (Finding 6), Polish-regulated F/G/H exemption (Finding 3), I3 reply-judging deferral to v3.1 (Finding 5), X-6 promotion as variance trigger (Finding 10), §3 lane-DNA framing note (Finding 2) — each address the named v2 finding at the location and shape claimed in the v3 frontmatter.

**The substrate-readiness gate is the most significant architectural addition.** It converts the 12-component bundle from a "ship-now" surface to a "ship-as-substrate-emits" surface — even if it doesn't change the bundle's composition, it gates client-side delivery on substrate readiness, which buys time for Finding 1's underlying scope question to surface from real production data before all 12 components ship.

**Files referenced in this verification:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-18-judge-design-step1-x-engine.md` (v3 target, line citations above)
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/handoffs/2026-05-19-x-engine-v2-spot-check.md` (v2 findings source)
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/docs/rubrics/judge-design-guide.md` (design-guide §5 documented-exception path, §11.5 redesign threshold, §6 attack-surface rationale)
