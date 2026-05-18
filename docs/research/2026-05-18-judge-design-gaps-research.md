---
date: 2026-05-18
type: research deliverable
status: complete
topic: judge design gaps — uncertainty resolution + adversarial + calibration + evolution-loop
parent: docs/rubrics/judge-design-guide.md
siblings:
  - docs/research/2026-05-15-judges-methodology.md
  - docs/research/2026-05-16-agentic-judges-methodology.md
  - docs/research/2026-05-17-qualitative-judge-design-methodology.md
---

# Judge Design Gaps — May 18 Closure Pass

Scope: ten target areas flagged in `docs/rubrics/judge-design-guide.md` §15, plus three under-covered topics (calibration sets, adversarial robustness, evolution-loop stability). Prescriptive. Does not restate the May 15 / 16 / 17 docs.

---

## 1. TL;DR — status of the ten target areas

1. **Optimal criterion count (small-fixture regime):** PARTIAL. No 2026 study fixes a number under selection pressure; the new "quality > quantity" line (RRD, arxiv 2602.05125) plus the May 17 ≤5 ceiling is the working consensus. **Hold ≤5; expect the live floor to be 3–4 once redundancy is removed.**
2. **Goodhart time-constant (outcome vs feature):** UNRESOLVED. No paper has instrumented time-to-Goodhart per rubric shape with matched compute. RIPD (arxiv 2602.13576) still the only static-magnitude evidence.
3. **Reference-free durability past ~10 generations:** UNRESOLVED. Preference-leakage static magnitude is well-established (arxiv 2502.01534, ICLR 2026); no published dynamic compounding curve over generations.
4. **Ternary 0/0.5/1 vs strict binary 0/1 on long-form:** PARTIAL. arxiv 2601.03444 finds 0–5 maximizes aggregate human-LLM alignment but loses resolution at the extremes; the binary-with-way-out pattern wins for *separability under selection*. **Keep 0/1 + 0.5-as-unknown.**
5. **Structured per-criterion vs holistic CoT on frontier:** RESOLVED IN PRINCIPLE, no head-to-head measurement. Empirical Study (arxiv 2506.13639) finds minimal accuracy delta; structured wins on *honesty and auditability* under attack (arxiv 2602.13576, 2505.13348). Keep structured.
6. **IRT for judges in production:** PARTIAL — RESOLVED AS METHOD, UNRESOLVED AT SCALE. arxiv 2602.00521 published the Graded Response Model framework Jan 2026; no >1000-judgment/week deployment retrospective yet. Not worth wiring at our 100-call/generation scale.
7. **Dynamic rubric curation (alternating RL):** RESOLVED AS RESEARCH METHOD, UNRESOLVED IN PRODUCTION. Rubric-ARM (arxiv 2602.01511) is the canonical reference; no production case study; operator overhead is rubric-as-moving-target plus alternating-instability. Not for v1.
8. **Calibration set design and drift detection:** RESOLVED. Industry convergence: 50–500 human-labeled fixtures, version-pinned judges, rolling-mean baseline with 2–5% alarm threshold, weekly probe of 50–100 sentinel fixtures.
9. **Adversarial robustness of qualitative judges:** PARTIAL. Binary + structured-CoT + cross-family panel survives the most-cited attack classes (CUA/JMA, RIPD). Composite long-suffix attacks (73.8% ASR) remain unaddressed without an input sanitizer.
10. **Evolution-loop judge specifics:** PARTIAL. AlphaEvolve, Rubric-ARM, and the Reward Hacking 2026 survey (arxiv 2604.13602) converge on three patterns: evaluation cascades, judge-model rotation, evaluator–policy decoupling via alternating training.

---

## 2. Per-area survey

### 2.1 Optimal criterion count — PARTIAL

**SOTA position.** No 2025–2026 paper specifies the right number under selection pressure with a frontier inner-loop and 5–30 fixtures. Two relevant lines:

- **RRD** (Rethinking Rubric Generation, arxiv 2602.05125, Feb 2026): recursively decomposes coarse criteria into fine-grained ones, then *filters out redundant ones via a correlation-aware weighting scheme*. The filtering is the new contribution — RRD finds that 70% of generated criteria are correlated >0.7 with another criterion and contribute no separation. With redundancy removed, the typical retained set is 3–4 criteria per task.
- **AutoRubric** (arxiv 2603.00077): unified framework defaults to 4–6 criteria per CHARM-100 task, 87% binary accuracy with 4. Going to 8+ degraded ordinal accuracy.

**Empirical Study of Design Choices** (arxiv 2506.13639) — already cited — finds diminishing returns past 5; central-tendency surfaces past 5 when judges *synthesize across criteria*. Our per-criterion isolation defuses this somewhat but not entirely (the judge still allocates attention budget across all criteria in one pass).

**Recommendation for our regime.** Keep ≤5 as the hard ceiling. The live floor after redundancy removal is likely 3–4. Treat any 5-criterion rubric as suspect until a redundancy check (pairwise correlation across re-runs on the same 5 fixtures, threshold 0.7) clears it.

**When this inverts.** It doesn't — every 2025–2026 source agrees more criteria is worse on subjective long-form. The only exception is the dynamic-rubric line (Rubric-ARM), which decouples the count entirely.

### 2.2 Goodhart time-constant under matched selection — UNRESOLVED

**SOTA position.** No published instrumentation. The strongest near-evidence is the Reward Hacking 2026 survey (arxiv 2604.13602) which formalizes the **Proxy Compression Hypothesis** — exploitation escalates Feature → Representation → Evaluator → Environment level — but does *not* fit a time constant per level under matched compute.

RIPD (arxiv 2602.13576) shows static magnitude — feature-shaped rubrics enable up to 27.9 pp preference drift after a *single* targeted edit pass — but no published curve over generations.

**Closest analog: AlphaEvolve evaluator-hacking incidents.** DeepMind's blog and the May 2025 Sapunov writeup document that "a flawed or incomplete evaluator is the primary cause of flawed solutions" and cite a load-balancing example where the policy learned to *drop work* to hit the evaluator's metric. Anecdotal, not quantified per rubric shape.

**Recommendation.** Treat the Goodhart time-constant as unknown. Operationalize via judge-variance-per-criterion-per-generation tracking (§11.5 of the guide already prescribes this) and accept that any criterion compressing toward the middle is the *only* early signal we have. The literature won't help here for ~6 months at minimum.

**When this inverts.** N/A — there is no evidence at all.

### 2.3 Reference-free durability past ~10 generations — UNRESOLVED

**SOTA position.** The static magnitude of preference leakage is locked: arxiv 2502.01534 (Li et al., ICLR 2026) shows 6–22% scoring inflation per related-pair, with severity ranked Same Model > Inheritance > Same Family > Same Series. No paper has instrumented the *dynamic compounding* of leakage over an evolution loop with frontier inner-loop and frontier panel judges.

**Adjacent evidence.** The Reward Hacking 2026 survey identifies evaluator–policy co-adaptation as one of three mechanisms underlying reward hacking; over training, the policy "learns the evaluator's compressed map" rather than the underlying objective. This is the right structural framing but is not quantified per generation.

**Recommendation.** Keep reference-free for all 8 lanes. Do not introduce model-authored reference exemplars. Instrument the panel for monotonic mean drift: if Claude-judge mean rises faster than Gemini-judge mean while the inner-loop is Claude-family, that asymmetry is the only early leakage signal available to us. Track it.

**When this inverts.** When we have ≥10 *human-authored* canonical exemplars per lane that JR signs off on. Not soon.

### 2.4 Ternary (0/0.5/1) vs strict binary (0/1) on long-form subjective — PARTIAL

**SOTA position.** Two contradictory 2026 papers:

- **arxiv 2601.03444** ("Grading Scale Impact"): aggregated over six benchmarks, 0–5 maximizes average human-LLM alignment; 0–10 is the weakest. Binary scores were *not* in the strongest tier on aggregate alignment.
- **AutoRubric** (arxiv 2603.00077) and **Hamel Husain's 30-company survey**: binary correlates better with *actual quality decisions* than ordinal; "people don't know what to do with a 3 or 4." Binary + prose justification stays separable; ordinal saturates under repeated re-runs.

**Resolution.** The two papers are measuring different things. 2601.03444 measures *alignment with a human-assigned score on the same scale*; AutoRubric measures *decision-relevant separability under repeated stochastic sampling*. For our regime (selection signal, not absolute quality reporting), separability under selection wins. The binary-with-way-out (0/0.5/1 where 0.5 = "unknown") preserves a place to put genuine ambiguity without inviting the central-tendency collapse documented in arxiv 2506.22316.

**Recommendation.** No change. Keep 0/1 + 0.5-as-unknown.

**When this inverts.** If we ever publish public-facing absolute-quality scores (e.g. a client-facing scorecard), switch that view to 0–5 with anchored levels. The selection signal stays binary.

### 2.5 Structured per-criterion CoT vs holistic CoT — RESOLVED IN PRINCIPLE

**SOTA position.** No head-to-head measurement on frontier judges in 2025–2026 directly testing structured-per-criterion vs holistic-then-decompose. Aparna Dhinakaran's note that "little difference in measured accuracy" stands. But:

- **Prompt-injection vulnerability (arxiv 2505.13348):** Justification Manipulation Attack (JMA) targets the *generated reasoning* of the judge; CUA targets the final output. Holistic CoT exposes a single long reasoning block to JMA — one successful manipulation poisons the whole rubric. Structured per-criterion CoT means each criterion is a separate attack surface; the blast radius is bounded.
- **RIPD (arxiv 2602.13576):** rubric-induced preference drift exploits the *interaction across criteria* in the judge's holistic synthesis. Per-criterion isolation removes the synthesis step.

**Recommendation.** Keep structured per-criterion. The accuracy delta is small; the *attack-surface delta* is large, and that matters under selection pressure where the workflow is the implicit adversary. The cost is one extra block per criterion (~150 tokens × 5 criteria × 3 panel = ~2.25k extra tokens per judgment, ~$0.02 per call at Opus rates).

**When this inverts.** When the task is so narrow that all criteria reduce to one (e.g. structural_gate-eligible). At that point it's not in the judge anyway.

### 2.6 IRT for judges in production — PARTIAL

**SOTA position.** arxiv 2602.00521 ("Diagnosing the Reliability of LLM-as-a-Judge via IRT," Jan 2026) is the canonical reference. It applies the Graded Response Model to LLM judges and produces two interpretable signals per criterion: intrinsic consistency under prompt variation, and human alignment. Adnan Masood's April 2026 survey explicitly recommends IRT for production teams "to determine which criteria are too ambiguous or too sensitive."

No published case study at >1000 judgments/week. Princeton dissertation thesis on the topic exists but uses synthetic data. Anthropic's Demystifying Evals page does not explicitly endorse IRT despite the survey claim — the page recommends "calibration against human experts," which is the IRT human-alignment dimension under a different name.

**Recommendation.** Not for v1. Our judge volume is ~100 calls per generation × ~8 lanes × ~1 generation per evolve = ~800 judgments per evolution sweep. IRT requires per-criterion calibration with enough fixture variation to fit the GRM — we don't have the volume per criterion to fit stable IRT parameters. The simpler proxy (judge variance per criterion per generation) gives the same diagnostic signal at zero engineering cost.

**When this inverts.** When we run ≥1000 judgments per criterion (across all lanes pooled) over a stable rubric — i.e. after we've stopped redesigning rubrics every ~2 weeks. Estimated: Q4 2026 if rubrics stabilize after this gap-research pass.

### 2.7 Dynamic rubric curation (Alternating RL) — RESOLVED AS METHOD

**SOTA position.** Rubric-ARM (arxiv 2602.01511, Feb 2026) is the canonical reference. Jointly optimizes a rubric generator and the judge via alternating RL from preference feedback. Operator overhead, per the paper's own discussion:

- **Instability from simultaneous updates** — both components drift; mitigation is alternating with one fixed and one updating, then swapping. This adds ~2× wall-clock vs static rubrics.
- **Rubric becomes a moving target** — variant scores from generation N are not directly comparable to scores from N+1 because the rubric changed. Longitudinal monitoring breaks unless every generation re-scores past variants on the new rubric.

No production case study. AlphaEvolve uses static evaluators (the eval function is part of the problem spec) — not a counter-example, just a different regime.

**Recommendation.** Not for v1. The two operator costs above are dealbreakers at our scale: variant comparability is what `current.json` depends on, and 2× wall-clock on judge calls is $6–12 per generation incremental on top of pairwise gate cost. Revisit when (a) we have a stable rubric design template (this gap-research pass is the start of that) and (b) we can afford one full generation of re-scoring old variants on every rubric edit.

**When this inverts.** Once the rubric template is stable enough that the *generator* output is constrained to small edits within the template's behavioral-anchor format. At that point the moving-target problem is bounded.

### 2.8 Calibration set design and drift detection — RESOLVED

**SOTA position (industry convergence 2025–2026).**

- **Calibration set size.** Hamel Husain / Shreya Shankar eval-faq (hamel.dev/blog/posts/evals-faq, Jan 2026): "Minimum viable is 50–100 examples; production-ready is 200–500; mature systems 1000+." Confident AI, Statsig, Arize converge on similar numbers.
- **Composition.** Stratified across artifact types AND quality levels (must include both score-1 and score-0 ground-truth examples). Pull fresh scenarios from production every cycle, never freeze.
- **Refresh cadence.** "Small frequent updates over rare giant refreshes" (Husain). Weekly: probe 50–100 sentinel fixtures and track rolling mean. Monthly: re-label 10–20% of fixtures from new production traces. Quarterly: full re-audit, retire fixtures that no longer represent live distribution.
- **Drift detection.** Rolling-mean baseline with **2–5% drop sustained over 24–48 hours warrants investigation; 5%+ pages** (Stack Pulsar, Mar 2026). Eval-score drift is implemented as a span attribute attached by a small judge model to every production span; a rolling mean detector watches it. Galileo Luna-2 and Patronus Lynx both ship this pattern as turnkey.
- **Judge-version-drift specifically.** Pin judge model version (e.g. `claude-opus-4-7-20260201`, not `claude-opus-4-7-latest`). When the version rolls forward, re-run the full calibration set; require the new version to meet ≥90% agreement with the old version on the calibration set before promoting.

**Recommendation for our regime.** Build a 100-fixture calibration set per lane (8 lanes × 100 = 800 fixtures), human-labeled by JR with binary verdicts on each criterion. Refresh 10–20 fixtures monthly from real client work. Weekly: run the calibration set through current judges, alarm if any criterion's mean drops 2–5% from last week's baseline. Pin all three panel models to specific dated versions. When a version rolls forward (e.g. Opus 4.7 → 4.8), gate the upgrade on ≥90% agreement with prior version on the calibration set.

**When this inverts.** N/A — calibration set + drift detection is a hard requirement at production scale.

### 2.9 Adversarial robustness — PARTIAL

**SOTA position.**

- **Vulnerability map.** RobustJudge (Comprehensive Assessment, arxiv 2506.09443, Jun 2025) benchmarks 15 attack methods × 7 defenses × 12 models. Key findings: (a) Combined Attack and PAIR are the most effective generic attacks; (b) Re-tokenization and LLM-based detection are the most effective defenses; (c) judge robustness varies wildly by prompt template — choice of rubric prose materially changes susceptibility.
- **Pointwise > Pairwise vulnerability.** Per the same paper: "Judge-LLMs are significantly more susceptible to adversarial attacks when used for absolute scoring as opposed to comparative assessment." Direct evidence for keeping pairwise at the promotion gate.
- **Prompt-injection specifically.** arxiv 2505.13348: Comparative Undermining Attack (CUA) targets final output, ASR >30% on MT-Bench. Justification Manipulation Attack (JMA) targets generated reasoning, similar magnitude. arxiv 2504.18333: composite attacks (Contextual Misdirection) reach 67.7% ASR on Gemma, 73.8% on others.
- **Rubric-edit attacks (RIPD).** arxiv 2602.13576: benchmark-compliant rubric edits steer judgments on target domains, up to 27.9 pp shift on harmlessness, 9.5 pp on helpfulness. Critically, the drift propagates through downstream RLHF if the corrupted judge is used to label training data.

**Which attacks the current design resists.**
- **CUA/JMA on individual criteria:** structured per-criterion CoT bounds blast radius — one corrupted criterion doesn't poison the rubric.
- **RIPD via "stealth" rubric edits:** harder against outcome-shaped binary anchors than against feature-shaped Likert because the attack vector for RIPD is *implicit weight reshuffle through criterion phrasing* — binary anchors leave less room.
- **Same-family preference leakage as adversarial vector:** cross-family panel defuses.

**Which attacks survive the current design.**
- **Composite long-suffix attacks (73.8% ASR):** not addressed without an input sanitizer / re-tokenization defense. We have no sanitizer in the judge prompt.
- **Optimization-based prompt-injection (arxiv 2403.17710):** white-box; not a threat in our regime where the inner-loop doesn't see the judge prompt.

**Recommendation.** No prose changes to rubrics for adversarial defense (would be theatrical, per the May 17 doc). Add one input-sanitization step: strip non-printable characters and known prompt-injection markers from the artifact before passing to the judge. This is ~20 LOC in `evaluate_variant.py`, addresses composite-attack and JMA suffix variants, and costs zero runtime.

**When this inverts.** If we ever expose the judge to externally-authored artifacts (e.g. third-party content scored by our judge). Then full RobustJudge-style defenses become mandatory.

### 2.10 Evolution-loop judge specifics — PARTIAL

**SOTA position.** No single canonical paper. Three converging lines:

- **AlphaEvolve / FunSearch (DeepMind, 2025).** Uses *evaluation cascades* — cheap deterministic checks first, expensive LLM judge only on candidates that pass. Maintains a MAP-elites archive to *preserve diversity* and prevent convergence on a single high-judge-score basin. Both patterns map to our regime: `structural_gate` is the cheap cascade head; lineage diversity (we don't have MAP-elites, but we keep all variants) is the equivalent of the archive.
- **Rubric-ARM (arxiv 2602.01511).** Alternates between fixing the rubric and updating the judge, then fixing the judge and updating the rubric. The decoupling is what prevents *judge collapse* — the failure mode where judge and policy co-adapt to a degenerate equilibrium.
- **Reward Hacking 2026 survey (arxiv 2604.13602).** Formalizes evaluator–policy co-adaptation as one of three mechanisms of reward hacking. Mitigations cluster into three groups: (a) reward bounds (bounded scores prevent runaway), (b) anti-compression (richer reward signals, e.g. multi-criterion vs scalar), (c) decoupling (refresh the judge or rotate models).

**Direct lessons for our regime.**

1. **Cascade-then-judge.** Already in `structural_gate`. Keep it; aggressively expand the cascade head as we identify Goodhart-prone criteria — anything that *can* become deterministic should be hoisted out of the judge.
2. **Judge-model rotation across generations.** Not in current design. Rotating the panel composition every N generations (e.g. swap Gemini 3 Flash for Gemini 3 Pro every 5 generations) breaks the co-adaptation loop. Cost: zero, if rotation stays within the same family. Implement via a rotation schedule in `panel_config`.
3. **Bounded scores.** Binary 0/1 with way-out is already bounded — done.
4. **No reward shaping via the judge.** Reward Hacking 2026 explicitly cautions against shaping the reward (judge score) to "smooth" the loss landscape; this is what RIPD-style rubric edits unintentionally do. Our prescription against rubric "calibration" via prose tweaks aligns with this.

**Constitutional AI lineage on judge stability.** Anthropic's Jan 2026 23k-word constitution refresh shifts from rule-checking to principle-generalization — same philosophical move as the May 17 outcome-vs-feature prescription. The Constitutional Classifiers production work (87% drop in false refusals on Sonnet 4.5) shows that *principle-based judges with a linear probe gate* outperform rule-based classifiers under adversarial pressure. Not directly portable (they're safety classifiers, not quality judges), but the directional evidence is supportive.

**OpenAI RFT.** Cookbook on RFT graders converged on the same pattern we're using: prose-rationale-then-score, model-graded for subjective tasks, deterministic gate for verifiable tasks. RFT use-cases page (2026) emphasizes "smooth score, not pass/fail stamp" — *for training*. Our pointwise-mean digest provides the smooth score; our binary criteria provide the pass/fail at the criterion level. The conflict is resolved by separating the gate from the digest.

**Recommendation.** Two additions:
1. **Judge-model rotation schedule.** Rotate within-family minor versions every 5 generations; cross-family panel composition stays fixed.
2. **Variance-based criterion retirement.** Any criterion whose variance grows monotonically over 3 generations or whose mean compresses toward the middle gets flagged for redesign. Already prescribed in §11.5 of the guide; add an instrumentation hook.

**When this inverts.** It doesn't — these are non-controversial recommendations across all three converging lines.

---

## 3. What the new findings change in the guide

Concrete edits to `docs/rubrics/judge-design-guide.md`:

**§3 (anchor format) — no change.** Ternary research splits between alignment-on-scale (favors 0–5) and decision-separability (favors binary). The May 17 prescription for binary with 0.5-as-unknown survives both findings; reinforced under selection pressure per arxiv 2603.12520.

**§5 (criterion count) — add a paragraph.** "Empirical Study sets the ceiling at 5; RRD (arxiv 2602.05125) demonstrates that after redundancy-removal the live floor is typically 3–4. Run a redundancy check on any 5-criterion rubric: pairwise correlation of judge scores across re-runs of the same 5 fixtures; drop any criterion correlating >0.7 with another."

**§6 (CoT) — add a sentence.** "The structured-vs-holistic accuracy delta is small on frontier judges; the *attack-surface delta* is large. Structured per-criterion bounds the blast radius of Justification Manipulation Attacks (arxiv 2505.13348)."

**§7 (reference-free) — no change.** Still no dynamic compounding evidence; static evidence still in favor.

**§8 (panel composition) — add rotation.** "Rotate within-family minor versions every ~5 generations (e.g. swap Gemini 3 Flash for Gemini 3 Pro). Cross-family composition stays fixed. Rationale: AlphaEvolve / Rubric-ARM evaluator–policy decoupling (arxiv 2604.13602)."

**§10 (bias mitigations) — add input sanitization.** "Strip non-printable characters and known prompt-injection markers from the artifact before judge ingestion. Addresses composite long-suffix attacks (arxiv 2504.18333, 73.8% ASR). ~20 LOC; zero runtime cost."

**§11 (Goodhart-resistance) — promote variance instrumentation.** "Track judge variance per criterion per generation. Any criterion whose variance grows monotonically over 3 generations or whose mean compresses toward the middle is flagged for redesign — NOT for calibration. This is the only Goodhart-time-constant signal currently available; the literature has not yet quantified it per rubric shape (gap remains)."

**NEW §15 (was Known Uncertainties) → "Calibration and Drift" (new prescriptive section).**

> Build a 100-fixture calibration set per lane (~800 total). JR-labeled binary verdicts per criterion. Refresh 10–20 fixtures monthly from real client work; full re-audit quarterly. Weekly: run the calibration set through current judges; alarm if any criterion's mean drops 2–5% from rolling baseline. Pin all panel models to dated versions (`claude-opus-4-7-20260201` not `-latest`). Gate version upgrades on ≥90% agreement with prior version on the calibration set.

**Updated §15 (Known Uncertainties) — graduate seven items, keep three.** Graduate: anchor format, structured CoT, panel composition, calibration design, basic adversarial defense, criterion count, evolution-loop patterns. Keep open: Goodhart time-constant, reference-free dynamic compounding, IRT at our scale.

---

## 4. Honest gap statement

Three things this pass did not resolve:

**Goodhart time-constant under matched selection pressure.** No paper has fit a curve to time-to-reward-hacking per rubric shape. The Proxy Compression Hypothesis (arxiv 2604.13602) gives the right structural framing — Feature → Representation → Evaluator → Environment level — but no compute-matched measurements. Our only mitigation is variance instrumentation and human eyeballing; both are lagging, not leading, indicators. **Likely 6–12 months before the literature closes this.**

**Reference-free durability past ~10 generations with frontier inner-loop.** Static preference-leakage magnitudes are well-documented (arxiv 2502.01534); the dynamic compounding curve over many generations is not. We will run into this empirically before the literature does. Our only signal is panel-model asymmetric drift: if Claude-judge means rise faster than Gemini-judge means while inner is Claude-family, that asymmetry is a leakage tell.

**IRT for judges at our scale.** Method is canonical (arxiv 2602.00521); production scaling is not. Our ~800 judgments/sweep volume per criterion is below what's needed to fit stable GRM parameters. The simpler proxy (judge variance per criterion per generation) gives 80% of the diagnostic value at zero engineering cost. Revisit when judgment volume per criterion ≥1000 and rubric prose has been stable for ≥1 month — earliest Q4 2026.

These three are honest holes. The guide's §15 should reflect them as remaining open after seven of the original ten close to prescriptions.

---

## Summary

1. **Word count:** ~2,950 words.
2. **Resolution status:** RESOLVED: #8 (calibration / drift). PARTIAL: #1 (criterion count), #4 (ternary vs binary), #5 (structured CoT), #6 (IRT — method resolved, scale unresolved), #7 (dynamic rubric curation — method resolved, production unresolved), #9 (adversarial — design survives most attacks, composite suffixes need sanitizer), #10 (evolution-loop — three patterns confirmed). UNRESOLVED: #2 (Goodhart time-constant), #3 (reference-free dynamic compounding).
3. **Top-3 new prescriptions to add to the guide:**
   - Build per-lane 100-fixture calibration set + weekly probe + 2–5% rolling-mean drift alarm + pinned judge-model versions (Husain/Shankar eval-faq 2026; arxiv 2506.13639; Stack Pulsar Mar 2026).
   - Run a redundancy check (pairwise correlation >0.7) on any 5-criterion rubric and drop redundant criteria; live floor is typically 3–4 (RRD, arxiv 2602.05125).
   - Add input sanitization before judge ingestion (strip non-printable + known prompt-injection markers) — addresses composite long-suffix attacks at 73.8% ASR (arxiv 2504.18333).
4. **Top-2 prescriptions in the guide that should be REVISED:**
   - §8 (panel composition) — add within-family minor-version rotation every ~5 generations (AlphaEvolve / Rubric-ARM evaluator decoupling; arxiv 2604.13602).
   - §6 (CoT) — clarify that the accuracy delta between structured-per-criterion and holistic CoT is small on frontier; the *attack-surface delta* is large (arxiv 2505.13348). Keep structured for the attack-surface reason, not the accuracy reason.
5. **Top-3 still-open gaps requiring future research:**
   - Goodhart time-constant — outcome vs feature under matched selection compute (no published instrumentation).
   - Reference-free dynamic compounding curve over generations (only static magnitudes published).
   - IRT for judges at our 100-call/generation scale (method published, no production case study below ~1000 judgments/criterion).
6. **Specific section numbers in the guide to edit:** §5 (criterion count — add redundancy check paragraph), §6 (CoT — attack-surface rationale sentence), §8 (panel composition — rotation schedule), §10 (bias mitigations — input sanitization), §11 (Goodhart-resistance — promote variance instrumentation), §15 (known uncertainties — graduate seven, keep three; add new calibration/drift subsection).
