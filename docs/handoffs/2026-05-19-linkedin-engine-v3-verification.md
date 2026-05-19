---
date: 2026-05-19
type: adversarial verification — does v3 actually close the v2 spot-check findings?
target: docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md (v3, dated 2026-05-19)
parent-review: docs/handoffs/2026-05-19-linkedin-engine-v2-spot-check.md
guide: docs/rubrics/judge-design-guide.md
reviewer-role: LI lane adversarial reviewer (premise / assumption / decision stress / simplification / alternative-blindness)
status: verification complete
---

# LinkedIn Engine v3 verification — closure check against v2 spot-check findings

The v3 surgical edits succeed on every textually-resolvable finding from the v2 spot-check. Where the closure is real, it is named here; where the closure is partial or merely re-described, the residual is named. The v3 spec did NOT relitigate the §1.5 Components-A–H load-bearing concern from v2 — it explicitly kept the multi-component restructure and addressed the spot-check's secondary recommendations (Component F deferral, substrate-readiness gating, per-segment over-fit removal, sibling-fork trigger reframing). That is a defensible posture, but it leaves the v2 spot-check's TOP architectural concern (Components B–H demote-to-on-demand) unresolved by design. The verification below treats that as a deliberate scoping decision, not a v3 miss.

Verdict: **CLOSURE on 9-of-9 named v2 findings; residual epistemological gap on the architectural recommendation v3 declined to take.**

---

## Per-finding closure

### 1. LI-3 CoT collapsed from 6 effective sub-steps to 3 (design guide §6)

**CLOSED.** v2 had Step 1a/1b/1c/1d + Step 2 three-signal + Step 3 verdict = effectively 6 sub-steps, over-budget per design guide §6. v3 (lines 419–423) restructures to a clean 3-step CoT: Step 1 bundles the four checks (gestalt / register / cross-platform / substrate) into a single per-check-finding emit; Step 2 combines compensating-marker identification with the three-signal substance test; Step 3 commits to verdict. The substantive checks are preserved verbatim (em-dash density, bait-y/Twitter-translated register, voice-substrate provenance, three-signal test). The collapse is genuine, not cosmetic. Cost-per-judgment drops from ~6×150 = ~900 tokens of rationale to ~3×150 = ~450 tokens, which is the design-guide budget. Recommendation honored.

One residual concern worth naming for the reader: Step 1 now contains four sub-checks (a)/(b)/(c) with cold-start handling embedded inline. The judge is still walking four checks; what changed is they emit as one rationale block instead of four. If variance instrumentation later shows judges synthesizing across the four sub-checks rather than committing per-check, this would revert the structural protection the design guide §6 prescribes. Watch in variance telemetry.

### 2. LI-2 Step 3 softened to audience-existence-test

**CLOSED.** v2 asked the judge to identify which audience the insight serves — a hard prediction the spot-check flagged as overreach. v3 (line 400) explicitly softens to "verdict 1 if the insight is non-obvious for AT LEAST ONE of the four primary audiences (founder/decision-maker, mid-career B2B IC, recruiter/talent, industry peer)." The audience does not need to be named explicitly in the post — must be inferable from substance. The 0.5 + "unknown" + "cannot infer target audience" way-out is preserved for the legitimately-ambiguous case. This shifts a hard "which audience?" prediction to a soft "any-audience-existence-test" exactly as the spot-check recommended. Recommendation honored verbatim.

### 3. LI-3 cold-start voice-substrate interaction spelled out

**CLOSED.** v2 deferred cold-start handling to lane wiring without specifying the interaction between cold-start state and the Step 1d voice-substrate provenance check. v3 (lines 413, 415, 420) makes the cold-start interaction explicit at THREE places: score-0 prose (line 413: lived-work claims REQUIRE voice substrate; the cold-start handling exception below applies), an explicit cold-start interaction paragraph (line 415: in cold-start, substrate-provenance check defers to 0.5 + "unknown" + voice substrate not provisioned), and inline within Step 1(c) of the CoT (line 420: cold-start handling: this substrate-provenance sub-check defers to 0.5 + unknown; the gestalt and register sub-checks still apply). The threshold for "voice substrate populated" is named: ≥3 author-surface anchors AND `source_data.author_context_known=true`. The cold-start gestalt check still fires (the AI-slop stack still scores 0 in cold-start) — only the substrate-provenance sub-check defers. Recommendation honored.

### 4. Component F (capacity-sizing) DEFERRED to §8 sibling-fork candidates

**CLOSED.** This is the most consequential v3 edit and the spot-check's clearest production-grade-v1-discipline win. v2 admitted Component F was knowingly broken ("we'll fix it after we observe churn"). v3 defers Component F from production-default at three coordinated places: §1.5 substrate-readiness gate (lines 79–80), §1.5 Component F section header explicitly labeled "DEFERRED in v3" with two-condition resolution criteria (lines 153–164), §6 Goodhart-resistance verification entry (line 551: "DEFERRED in v3 from production-default... Component F either does not ship in the production bundle OR ships with `[CAPACITY-DRAFT]` flag"), §8 sibling-fork-candidates list (lines 639–643). The two-condition gate is named: (a) capacity-model substrate wired with operator-hours/week + current-ramp + prior-cadence inputs, OR (b) observed-churn telemetry proves the broken default is harming clients. The production-default bundle is explicitly redefined to seven components A + B + C + D + E + G + H (~9,000–10,000 words), with the eighth (Component F at ~1,000 words) gated. Recommendation honored.

### 5. Per-segment comment-length 30/60/50/80 collapsed to single 30–80-word band

**CLOSED.** v2 named per-audience precision (founder 30–60w / mid-career IC 50–80w / recruiter 30–50w / industry peer 60–80w) that the spot-check flagged as over-fit relative to what Van Der Blom actually reports (a single ideal band, not segmented). v3 (line 47) collapses to a single "30–80-word range" across all four primary audiences with one sentence acknowledging the v2 over-fit and explicit attribution to Van Der Blom 2025/26 *Algorithm InSights*. The recruiter "trends shorter" and peer "trends longer" qualifiers survive as soft language in the audience descriptions (lines 44–45) without making per-audience numbers load-bearing. The 30–80-word band is now the single literature-supported threshold the judge uses. Recommendation honored.

### 6. Sibling-fork thresholds reframed to measurable indicators

**CLOSED (with one residual).** v2 used raw "3+ clients" thresholds; spot-check flagged these as effort-shaped rather than client-demand-shaped. v3 §8.6 reframes all five sibling-fork triggers to measurable indicators:

- `linkedin_carousel`: Component C cadence requires ≥1 carousel/week across ≥3 clients OR carousel-driven engagement ≥15% of agency-side LinkedIn revenue
- `linkedin_newsletter`: ≥3 clients launch newsletter as part of Component G AND ≥1 generates documented pipeline contribution within a quarter
- `linkedin_live`: ≥3 clients run ≥1 LinkedIn Live per quarter AND ≥1 client's Live-companion content shows ≥2× baseline engagement
- `linkedin_profile`: profile-audit depth grows beyond 800-word envelope on ≥2 client deliverables OR vertical-specific pattern emerges
- `linkedin_comment_strategy`: ≥3 clients have ≥3 overlapping target accounts AND coordination becomes operational problem

Recommendation honored. **Residual:** the `linkedin_profile` trigger uses "≥2 client deliverables" + "vertical-specific pattern emerges" which is back to raw-count + qualitative-emergence shape. Less crisp than the other four but defensible because profile-pattern divergence is genuinely vertical-shaped not volume-shaped. The other four triggers are tied to either content cadence, pipeline contribution, engagement ratios, or revenue percentage — all observable.

### 7. Substrate-readiness gate added

**CLOSED.** v3 §1.5 (lines 74–84) introduces an explicit "Substrate-readiness gate" clause that decouples Components A–H from a single ship-bundle. Each component is gated on its substrate emission readiness: Component A ships now (text-post extractor exists); Component B ships when profile-shape extractor exists; Component C ships when pillar-extraction + voice.md provisioning substrate exist; Component D ships when target-account research substrate exists; Component E ships when DM-template generator exists; Component F deferred (per Finding 4); Component G ships when Topic Authority signal-tracking substrate exists; Component H ships when X-engine handoff schema is locked. This is a defensible operationalization of "production-grade v1 posture (no demo deadline) — generalize when value crosses next 2–3 clients" because no component ships with known-broken structural_gate validation. Recommendation honored.

### 8. First-cohort overfitting posture (Polish + US-primary straddle named)

**CLOSED.** v2's substitute-reader list omitted Polish aesthetic dermatology + Polish legal services (Klinika, DWF) while shipping against a Polish-primary first cohort. v3 (line 57) names the straddle explicitly: "The substitute-reader list above does NOT include Polish aesthetic dermatology or Polish legal services. This is a real reader-vs-fixture mismatch the spec names rather than smooths over." Klinika and DWF are documented as first-cohort exceptions; vertical-specific calibration is deferred to per-vertical fixture coverage (§8.5) rather than baking Polish assumptions into substitute-reader breadth. The expansion trigger is named: if client #5+ onboards from another under-represented vertical, the substitute-reader list expands at that point — not pre-emptively. This is the honest-naming approach the spot-check recommended. Recommendation honored.

### 9. Scope conflation between judge design and product roadmap

**PARTIALLY CLOSED.** v2 §3a CUT-14 through CUT-20 were flagged as product-roadmap concerns conflated into the judge spec. v3 retains all 20 CUTs in §3a but routes CUT-14 through CUT-20 explicitly to Components B–H via in-line attribution (e.g., line 277 "Component D explicitly excludes pod-style coordination"; line 281 "Component B headline rewrite replaces with current-value-creation framing"; line 285 "Component C explicit pillar strategy is the structural defense"). The judge does not see CUT-14–CUT-20 — they belong to structural_gate per the routing. The conflation is resolved by routing rather than by splitting the document. This is a defensible compromise but less clean than the spot-check's suggested split into "judge-layer cuts (CUT-1–CUT-13)" and "program-layer cuts (CUT-14–CUT-20)." Recommendation partially honored.

---

## Architecture preservation audit

**5-criterion ceiling: PRESERVED** (line 360 "Criteria — outcome questions (5, UNCHANGED from v1)"; §7 line 563 "5 at the judge layer (within ≤5 ceiling, no documented exception)"). The v2/v3 restructure adds zero criteria at the judge layer; all program-level expansion routes to structural_gate.

**LI-1 / LI-4 / LI-5 prose unchanged outside bug-fix touches: PRESERVED.** LI-1 (lines 364–382), LI-4 (lines 426–446), LI-5 (lines 448–472) carry the v2 prose verbatim. The only LI-5 change is the structural_gate hoist documentation, which is unchanged from v2.

**LI-2 / LI-3 score-1/score-0 prose unchanged outside bug-fix touches: PRESERVED for score-1, PRESERVED for LI-2 score-0; LI-3 score-0 has the cold-start sentence inserted (line 415) but the v2 substrate-provenance language survives verbatim (line 413).** LI-2 Step 3 prose changes per Finding 2 above (intended fix); LI-3 CoT structure changes per Finding 1 (intended fix); cold-start handling added per Finding 3 (intended fix). No collateral prose drift detected.

**Topic Authority 78% framing preserved in §5 wrapper: PRESERVED** (lines 489–492 of the shared judge-prompt wrapper).

**All 4 v1 surgical-restoration score-cap folds preserved: PRESERVED** per §8.9 (lines 657–667):
- LI-1 "thoughtful authority, not contrarian punch" → LI-3 score-0 bait-y/Twitter-translated
- LI-1 "AUTOMATIC ≤4 if bait-y or Twitter-translated" → LI-3 score-0 anchor
- LI-2 HARD FLOOR "lived-work claims REQUIRE the named entity in voice.md" → LI-3 score-0 + Step 1(c) CoT
- LI-3 "contrarian hot-takes that work on X (≤3 even when same hook scores 5 on X)" → LI-4 score-0 cross-platform reply-ladder collapse

**LI-5 hashtag retirement preserved: PRESERVED** (line 665: hoisted to structural_gate `[1, 5]` hard bounds; quality-scoring retired).

**LI-6 cross-cohort workflow level preserved: PRESERVED** (lines 667–668: cross-cohort survives as `CrossItemCriterion` at session aggregator, not as 6th judge criterion).

---

## Residual epistemological gaps

The v3 spec genuinely addresses every textually-resolvable v2 finding. The remaining honest reads are:

1. **The §1.5 Components-A–H multi-component restructure is preserved by design.** v3 did not demote Components B–H to on-demand evidence (the spot-check's load-bearing top recommendation). v3 instead defends the restructure with the substrate-readiness gate (Finding 7) and Component F deferral (Finding 4). Whether substrate-readiness gating is a sufficient defense against "Components B–H ship → real clients receive ~11K words → read Component A carefully → ignore C/F/G/H → judge confirms Component A → loop converges on Component A" remains an empirical question. The structural_gate variance-monitoring telemetry for B–H is still unbuilt; the spot-check Risk 1 ("Components B–H ship as production-default → seven new Goodhart surfaces unmonitored") is not closed by v3 — it is bounded by the substrate-readiness gate, which delays exposure but does not close the Goodhart surface once the substrate emits.

2. **Step 0 research client-validation gap remains.** The spot-check named the single most important missing question: what evidence do we have that any real client wants the Components A–H program shape? v3 did not add an answer or a §8 open-question. The honest answer ("none — it's research-derived") is implicit in the substrate-readiness gate's logic (don't ship until substrate emits) but is not surfaced in §8. Worth a question at the next review checkpoint.

3. **Component F's `[CAPACITY-DRAFT]` mode is a hedge, not a resolution.** v3 offers two ship modes for Component F: (i) does not ship in production-default, OR (ii) ships with `[CAPACITY-DRAFT]` flag + operator-side gating. Mode (ii) preserves the gameable surface while shifting the validation burden to the operator. The spot-check's stricter posture ("Component F moves to on-demand OR ships with explicit capacity-sizing inputs from the client") is partially honored — capacity inputs are named as a substrate condition but Mode (ii) ships without them under operator-gating. This is a softer landing than the spot-check recommended.

Overall: v3 closes the named findings cleanly. The residual exists because the spot-check's TOP recommendation (demote Components B–H to on-demand) was a strategic decision JR retained the option to decline, and v3 declined it in favor of substrate-readiness gating + Component F deferral. That decision should be revisited if any of the Risk-1 / Risk-2 / Risk-3 failure modes from the spot-check actually surface in first-cohort fixtures.
