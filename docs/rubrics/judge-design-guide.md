---
date: 2026-05-18
status: living document (update as research lands)
type: prescriptive design guide
applies_to: all single-shot qualitative LLM judges in the autoresearch evolution loop
synthesis_of:
  - docs/research/2026-05-15-judges-methodology.md
  - docs/research/2026-05-16-agentic-judges-methodology.md
  - docs/research/2026-05-17-qualitative-judge-design-methodology.md
  - docs/research/2026-05-18-judge-design-gaps-research.md
companion: per-workflow optimal-output specs in docs/handoffs/2026-05-1*-judge-design-step1-*.md
revision_history:
  - 2026-05-17 v1 — initial synthesis from May 15/16/17 research
  - 2026-05-18 v2 — gap-closure pass: 6 section edits (§5 redundancy check, §6 attack-surface rationale, §8 version rotation, §10 input sanitization, §11 variance instrumentation prescribed, new §15 Calibration and Drift). 7 of 10 May-17 uncertainties graduated to prescriptions; 3 remain genuinely open.
  - 2026-05-18 v2.1 — §5 amended to document the justified-breach exception (allow 6th criterion when literature documents an LLM-specific failure surface the other 5 can't catch); first documented exception is CI lane's CI-6 "Evidence chain survives tracing" — see `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7.
---

# LLM Judge Design Guide

Canonical reference for designing single-shot qualitative LLM judges in the gofreddy autoresearch evolution loop. When designing a new judge, revising an existing one, or reviewing rubric edits — follow this guide. Per-workflow specs (CI, MON, etc.) are downstream artifacts that conform to this format.

This is a synthesis. Specific citations live in the three research deliverables named in frontmatter. Project incidents are named to make the patterns concrete.

---

## 1. Core design philosophy — three load-bearing principles

**1.1 Outcome questions, not feature checks.** The judge tests whether the artifact achieves a specific effect on a specific reader. The judge does NOT count surface features, check for named frameworks, or tally section headers. Feature-shaped criteria enable up to 27.9 pp preference drift on target domains under selection pressure (Rubrics-as-Attack-Surface, arxiv 2602.13576). This explains the Phase 4 prose rollback at HEAD `c76f051`.

**1.2 Hard Rules → `structural_gate`. Principles → judge.** (OpenRubrics, arxiv 2510.07743.) Verifiable requirements (file presence, JSON validity, structural facts, citation counts, schema validation, length bands) live in the workflow's `structural_gate` callable. Subjective qualities (strategic insight, voice, reader-effect) live in the LLM judge. Routing verifiables through the judge wastes attention and adds drift surface.

**1.3 Binary verdicts with behavioral anchors.** Score 0 / Score 1 with concrete behavioral descriptions — not "low quality" / "high quality." The 0.5 anchor is ONLY for "can't tell from the artifact" (Anthropic Demystifying Evals "way out" pattern). Vague outcome prose without binary anchors collapses to central-tendency bias (arxiv 2506.22316). Outcome question + behavioral binary anchor is the combined prescription, not either alone.

---

## 2. What the judge sees vs `structural_gate`

`structural_gate` (the workflow's deterministic pre-check) handles:

- File presence (session.md exists, results.jsonl non-empty, stories/*.json present)
- Parseability (JSON validates, scenes array non-empty)
- Structural facts from `STRUCTURAL_DOC_FACTS` tuples
- Length bands (word count within target range)
- Citation counts, URL resolves, schema validation, freshness checks (for GEO / site_engine)
- Mandatory section presence (executive_summary.md, action_items.md for monitoring)

The LLM judge sees the artifact only after `structural_gate` passes. The judge's criteria are about outcome quality, never artifact compliance.

This split is the OpenRubrics "Hard Rules vs Principles" formalization (arxiv 2510.07743). Don't blend them. A judge criterion that says "the brief has at least 3 sections" is a Hard Rule misrouted to the judge — move it.

---

## 3. Anchor format — binary with mandatory prose justification

**Binary 0/1.** Score 1 = artifact achieves the outcome described in the score-1 anchor. Score 0 = artifact does not.

**0.5 as "unknown" way-out ONLY.** If the artifact doesn't contain enough information to commit to 0 or 1, the judge emits 0.5 with the word "unknown" and one sentence on what's missing. The 0.5 is never "medium quality."

Why binary:

- Hamel Husain 30-company production survey: "domain expert pass/fail judgments correlate better with actual quality than granular numeric scores. People don't know what to do with a 3 or 4."
- Arize 2025 retest on Claude Opus 4 / GPT-5-nano / Qwen3-235B: numeric scales saturate ("plateau quickly… scores collapse into narrow bands"); categorical formats stay separable.
- AutoRubric (arxiv 2603.00077, Stanford SCALE 2026): 87% binary accuracy on CHARM-100 vs degraded ordinal accuracy.

When binary inverts: truly continuous criteria (e.g. progressive shades of journalistic-vs-marketing voice). Then ternary 0/0.5/1 with concrete behavioral anchors at extremes — but only if 0.5 has a *behavioral* anchor (not an "uncertain" anchor).

Anti-patterns:

- Likert 1-5 with described levels → central-tendency collapse (arxiv 2506.22316). "Judges do not share the same latent image of what a '3' versus a '5' means."
- Free-text-with-derived-score → judge rationalizes any score it's nudged toward.
- 0.5 as "medium quality" → central-tendency bias compounded by way-out availability.

---

## 4. Criterion shape — outcome question with behavioral anchor

Each criterion has three required parts:

**(a) Outcome question.** What the artifact must achieve for its specific reader. Phrased as a question, not a description.

- Bad: "The brief contains a strategic recommendation."
- Good: "After reading, would a senior partner change one upcoming client conversation based on a specific named claim in the brief?"

**(b) Score-1 anchor.** Concrete behavioral description of what success looks like, optionally with one named example. **Hedge the example** with "do not optimize toward this" — keeps the anchor concrete without inviting the workflow to adopt it as a feature checklist.

- Bad: "High strategic insight."
- Good: "Contains at least two items where (a) a named entity is paired with a numeric or dated finding, AND (b) the finding implies a different action than the reader would have taken without reading it."

**(c) Score-0 anchor.** Concrete behavioral description of failure.

- Bad: "Low quality."
- Good: "Every claim is either unnamed, undated, or actionable only at the strategic-posture level — no specific upcoming conversation changes."

Prose budget: ~150 words per criterion total. No framework names. No anti-gaming clauses. No "don't be biased toward X" instructions.

---

## 5. Criterion count and isolation

**≤5 criteria per lane.** Empirical Study of Design Choices (arxiv 2506.13639) finds diminishing returns past 5. Central-tendency bias surfaces at >5 per artifact when judges synthesize across criteria.

**Live floor is typically 3–4 after redundancy removal.** RRD (Rethinking Rubric Generation, arxiv 2602.05125, Feb 2026) finds that ~70% of generated criteria correlate >0.7 with another criterion and contribute no separation. **Run a redundancy check on any 5-criterion rubric:** pairwise correlation of judge scores across re-runs of the same 5 fixtures; drop any criterion correlating >0.7 with another. Final ceiling stays 5, but expect to ship 3–4.

**Documented exception: justified breach of ≤5 ceiling for AI-specific failure surfaces.** When a lane's artifact has a documented LLM-specific failure surface that the other 5 criteria cannot catch (e.g., entity confabulation at 19.9% GPT-4o citation-fab rate, source confabulation at 37% Perplexity failure shape, recency-cutoff distortion per LLMLagBench), a 6th criterion targeting that surface is permitted as a documented exception. Required documentation: the failure mode must be cited from 2024–2026 literature with measured effect sizes; the spec must include the citation. The redundancy check still applies — if the 6th correlates >0.7 with another criterion across re-runs, the redundant criterion gets dropped to restore 5. **Pattern:** prefer fewer well-discriminating criteria; allow a 6th only when literature documents a failure mode the other 5 cannot catch. First documented exception: CI lane's CI-6 "Evidence chain survives tracing" per `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` §7.

**Per-criterion isolation.** The judge scores each criterion independently with its own rationale block. Don't blend criteria into a single holistic score. Vendor consensus across Promptfoo, DeepEval, Galileo, Patronus, Ragas: per-criterion isolated is the production default.

Anti-pattern: holistic prose where analytic was needed. Cohen's κ drops 0.60 → 0.41 between analytic and holistic in both human and LLM raters (arxiv 2604.00259, PMC11359436).

---

## 6. Chain-of-thought — structured, per criterion

**Mandatory structured CoT per criterion.** One rationale block per criterion, score emitted AFTER rationale. Anthropic Demystifying Evals + OpenAI RFT graders both treat this as default.

**Structured, not free-form.** Don't write "think step by step." Specify the steps the judge must walk:

- Step 1: List the named entities / claims / dimensions in the artifact relevant to this criterion.
- Step 2: Map each to the score-1 anchor's requirements.
- Step 3: Commit to a verdict + one-sentence justification.

The specific steps vary per criterion. The constraint is: the steps must force the judge to commit to evidence before committing to a score.

Why structured: unstructured CoT enables the Rubrics-as-Attack-Surface drift (arxiv 2602.13576) — the judge invents its own rubric and ignores ours. Aparna Dhinakaran's review 2026 explicitly notes: reason-before-score works only when the score is committed AFTER the reason, not when the score is the prompt target and the reasoning is post-hoc.

**Why structured per-criterion specifically — the load-bearing reason is attack-surface, not accuracy.** On frontier judges the structured-vs-holistic accuracy delta is small (Empirical Study arxiv 2506.13639: "minimal gains when clear evaluation criteria exist"). The *attack-surface delta* is large: holistic CoT exposes one long reasoning block to Justification Manipulation Attack (arxiv 2505.13348) — one successful manipulation poisons the whole rubric. Structured per-criterion CoT bounds blast radius — each criterion is a separate, smaller attack surface. Under selection pressure where the workflow is the implicit adversary, attack-surface containment matters more than the accuracy delta.

Cost: one extra rationale block per criterion (~150 tokens × 5 criteria × 3 panel ≈ 2.25k extra tokens per judgment, ~$0.02 per call at Opus rates). Worth it.

---

## 7. Reference-free vs reference-based

**Reference-free for all 8 evolution-loop judges.** No model-authored exemplars used as scoring anchors.

Why: in an evolution loop with frontier inner-loop, reference-based scoring with model-authored references creates preference-leakage compounding across generations (Li et al. arxiv 2502.01534, ICLR 2026 — 6–22% scoring inflation per related-pair). The loop converges on the reference's style, not the underlying quality dimension.

Re-evaluate per lane if and when ≥10 JR-authored canonical exemplars exist per lane. Not the case today.

When reference-based wins (not us): clear-correct-answer tasks where references are objectively curated (REVISEVAL ICLR 2025; Reference-Guided Verdict arxiv 2408.09235).

Anti-pattern: reference exemplars from same model family. Preference-leakage amplification across generations. The hedge: any score-1 anchor that includes a concrete example must be tagged with "do not optimize toward this" — that's the lightest possible mitigation against using the anchor as a target.

---

## 8. Panel composition — cross-family three-model

**Three frontier families, one model each:**

- Anthropic: Claude Opus 4.7
- OpenAI: GPT-5.5 (codex)
- Google: Gemini 3 Flash

Aggregate by mean for pointwise digest. Aggregate by 2-of-3 majority for pairwise promotion gate.

Why three families: Li et al. preference-leakage (arxiv 2502.01534, ICLR 2026) — same-family panels have 6–22% scoring inflation. Three families span the major frontier providers; panel composition must be invariant to inner-loop choice because the workflow could mutate to a different inner-backend mid-run.

Why not single-frontier: same-family preference leakage when inner-loop is also Anthropic-family.

Why not 7-model cheap-diverse PoLL (Verga's design, May 15 doc): PoLL's cost savings come from *cheap diverse models*; our regime has 5–30 fixtures per lane and the absolute cost is already low. Frontier-diverse-three is cleaner per call and stays auditable.

**Rotate within-family minor versions every ~5 generations.** Swap e.g. Gemini 3 Flash for Gemini 3 Pro on a rotation schedule; cross-family composition (Anthropic + OpenAI + Google) stays fixed. Rationale: AlphaEvolve and Rubric-ARM both treat evaluator–policy decoupling as the primary defense against judge–workflow co-adaptation (Reward Hacking 2026 survey, arxiv 2604.13602). Cost: zero, if rotation stays within-family. Implement via a rotation schedule in `panel_config`. Pin each rotated version to a dated model ID (not `-latest`) so the rotation is auditable.

Anti-pattern: same-family panels for "redundancy." Adds compute without independence.

---

## 9. Pointwise vs pairwise — selection paradigm

**Pointwise primary (the digest). Pairwise at the promotion gate only.**

- **Pointwise:** each variant scored 0–1 against rubric criteria, mean across the 3-model panel. Goes into `current.json`'s `search_metrics.domains.<lane>.score`. Drives the digest, the leaderboard, longitudinal monitoring.
- **Pairwise:** at promotion time, the variant vs `current.json` head compared head-to-head with position swap. Promote only if both orderings agree on the variant being better.

Why split:

- Pointwise scores correlate with absolute quality but degrade at SELECTION step under reward-hacking pressure. arxiv 2603.12520 "When LLM Judge Scores Look Good but Best-of-N Decisions Fail" (Mar 2026): best-of-N selection accuracy as low as random under selection pressure even when pointwise correlates 0.85+ with humans.
- Pairwise with position swap gives +13.0 pp Claude debiasing per arxiv 2510.12462. Standard pattern: run both orderings; accept only if both agree.

Cost: pairwise doubles judge calls per promotion check. For 8 lanes × 3-model panel at the gate (per generation, not per fixture), incremental cost is +~$3–6/generation. Acceptable as gate; not as digest engine.

Anti-pattern: pointwise alone for promotion. Anti-pattern: pairwise without position swap.

---

## 10. Bias mitigations

**Position swap on pairwise: MANDATORY both-must-agree gate.**

**Position bias on pointwise** (which criterion the judge attends to first): structurally mitigated by per-criterion isolation. Each criterion has its own rationale block; the judge doesn't synthesize across criteria.

**Style bias > position bias on frontier models.** Justice or Prejudice? (arxiv 2410.02736): style bias 0.76–0.92, position bias ≤0.04 — style bias is ~20× larger. Don't over-engineer position; do engineer style-neutrality through behavioral anchors that target outcomes, not voice.

**Length bias:** weaker on frontier than commonly stated. arxiv 2604.23178 "Judging the Judges": no significant trend after controlling for quality gap. Length-band guidance lives in `structural_gate`, not in the judge.

**Verbosity:** newer paradoxical finding — frontier judges now prefer concise responses. Conciseness preference is a *new* bias that can penalize well-supported long-form briefs. Don't include "prefer concise" instructions; the bias is already there.

**Anti-bias clauses in rubric prose:** theatrical. arxiv 2506.13639 + Eugene Yan: "primarily perturb the score distribution without changing rank order." Don't include them.

**Input sanitization before judge ingestion: MANDATORY.** Strip non-printable characters and known prompt-injection markers from the artifact before passing to the judge. Addresses composite long-suffix attacks at 73.8% ASR (arxiv 2504.18333; arxiv 2505.13348 Comparative Undermining + Justification Manipulation; RobustJudge benchmark arxiv 2506.09443). ~20 LOC in `evaluate_variant.py`, zero runtime cost. RobustJudge's headline finding: pointwise judges are "significantly more susceptible to adversarial attacks than pairwise" — additional structural argument for the pointwise-digest + pairwise-gate split in §9.

---

## 11. Goodhart-resistance under selection pressure

The judge IS the selection signal. Anything it rewards, workflows will optimize toward.

**11.1 Outcome questions are more Goodhart-resistant than feature checks** — but not Goodhart-immune. RaR (arxiv 2507.17746, +31% HealthBench). Rubrics-as-Attack-Surface (arxiv 2602.13576, feature-shaped → 27.9 pp drift). The design target is *time-to-Goodhart*, not Goodhart-immunity.

**11.2 The judge's job is to imagine the reader, not check the artifact.** Frame every criterion as "would [specific reader] [do specific thing] after consuming this artifact?" The judge reasons about the reader; it doesn't tally features.

**11.3 Reward hacking is inevitable, not a misconfiguration.** "Inference-Time Reward Hacking" (arxiv 2506.19248) proves it's a property of any sufficiently optimized loop. Plan for it.

**11.4 Proxy Compression Hypothesis** (Reward Hacking in the Era of Large Models, arxiv 2604.13602): exploitation escalates Feature-level → Representation-level → Evaluator-level → Environment-level. Feature-level is the entry point — outcome-shaped criteria push the workflow past this level before drift sets in.

**11.5 Variance instrumentation: PRESCRIBED.** Track judge variance per criterion per generation. **Any criterion whose variance grows monotonically over 3 generations, or whose mean compresses toward the middle, is flagged for redesign — NOT for calibration.** Calibration via prose tweaks is the wrong response at this layer (it is the pathology we burned three times: `2ce99bb`, `ca4a256`, `698e658`).

This is the ONLY Goodhart-time-constant signal currently available to us. The literature has not yet quantified time-to-Goodhart per rubric shape — the May 18 gap-research pass confirms no paper has fit a curve to time-to-reward-hacking under matched compute. Expect a 6–12 month wait for the literature to close this; meanwhile, the variance-per-criterion-per-generation telemetry IS the early-warning system.

Other patterns (supporting, not load-bearing):

- **Cascade-then-judge.** Hoist anything that *can* become deterministic out of the judge into `structural_gate`. AlphaEvolve's evaluation-cascade pattern — already partly in our architecture; expand it aggressively as Goodhart-prone criteria are identified.
- **Meta-criterion veto.** A separate top-level "does this response look gamed?" check run as final pass. Suggestive in the literature; no published effect size yet.
- **Dynamic rubric curation** (Alternating RL, arxiv 2602.01511 Rubric-ARM): regenerate rubrics from preferred-vs-rejected contrasts as the policy evolves. Goodhart-resistant by construction; cost: rubric becomes a moving target, variant scores no longer comparable across generations. **Not for v1** per May 18 deliverable; revisit when the rubric template is stable enough to constrain regeneration to within-template edits.

---

## 12. Anti-patterns catalogue

Each: anti-pattern → failure mode → project incident if applicable.

1. **Feature-checking criteria** ("Does the brief mention X?"). Workflow learns to plant X without quality. Incident: Phase 4 rollback at `c76f051`.
2. **Framework-name embedding** ("Does this follow Helmer / FAA-AD / MrBeast?"). Special case of #1. Same incident.
3. **Anti-gaming clauses** ("do not prefer long outputs"). Redistributes bias without removing. Incident: J1–J4 commit `2ce99bb`.
4. **Broad-scale anchorless rubrics** (1–10 with no behavioral anchors). Central-tendency collapse. Incident: pre-Phase-1 rubric drift.
5. **Implicit-weight reshuffle.** Stealth preference drift even from well-intentioned edits. Every rubric edit since `ca4a256` is a potential drift vector if not re-calibrated.
6. **Holistic prose where analytic was needed.** κ 0.60 → 0.41.
7. **σ-widening as goal.** Trades information for variance. Can't beat inherent per-draft noise floor. Incident: `2ce99bb`.
8. **Contract-prose** ("judge SHALL emit JSON in this exact format…"). Meta-task replaces substantive task in judge attention.
9. **Reference exemplars from same model family.** Preference-leakage amplification.
10. **Mid-anchor 0.5 = "medium quality."** Central-tendency bias compounded by way-out availability. 0.5 is ONLY "unknown."
11. **Free-text-with-derived-score** (judge writes prose, then assigns score). Judge rationalizes any score it's nudged toward.
12. **In-prompt anti-bias instructions** ("don't be biased toward longer outputs"). Theatrical. The bias is structural, not addressable through prose nudges.

---

## 13. Specimen criterion template

```
CRITERION X-N — <Outcome name>

Outcome question (binary):
<Question phrased as "would [specific reader] [do specific thing]
 after reading?">

Score 1 (yes) — <Concrete behavioral description of success.>
  Example (do not optimize toward this): "<one concrete real-world
  example, hedged>"

Score 0 (no) — <Concrete behavioral description of failure.>

Score 0.5 (unknown) — Use only when the artifact does not contain
  enough information to commit to 0 or 1. Emit 0.5 + the word
  "unknown" + one sentence on what would have to be present to
  commit to 1.

Required CoT:
- Step 1: <List relevant entities / claims / dimensions in artifact>
- Step 2: <Map each to score-1 anchor requirements>
- Step 3: Emit verdict + one-sentence justification.

Do not score: <List structural / verifiable items routed to
structural_gate — visual polish, citation count, length, presence
of section headers, etc.>
```

**Shared judge-prompt wrapper** (applied across all criteria in the lane):

```
You are scoring a <lane> artifact for <specific reader>. You see
the artifact and the rubric. Score each criterion independently
with 0, 0.5, or 1 plus a one-sentence rationale. Do not blend
criteria. Do not infer criteria not stated. If a criterion's
condition is ambiguous from the artifact alone, emit 0.5 +
"unknown" + one sentence on what would have to be present to
commit to 1.

Emit per-criterion JSON:
{"criterion_id": "...", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 14. Process: designing a new judge (or revising one)

1. **Write the optimal-output spec first.** Reader (who, when, with what context, what do they do after) + success + failure + adversarial Goodhart-collapse check. Save under `docs/handoffs/2026-MM-DD-judge-design-step1-<lane>.md`.
2. **Draft ≤5 criteria as outcome questions.** Each asks "would the reader [do specific thing] after reading?" — never "does the artifact contain X?"
3. **Add behavioral score-0 and score-1 anchors** per criterion. Concrete, not abstract.
4. **Hedge any score-1 examples** with "do not optimize toward this."
5. **Add structured CoT (3 steps) per criterion.** The steps must force evidence-before-score.
6. **Route verifiables to `structural_gate`** — don't fold them into the judge.
7. **Validate by eyeballing rationales** on 5–10 existing fixtures. If the judge's rationales don't match human reasoning about quality, the criterion prose is wrong.
8. **Lock the version. Watch variance over 3–5 generations** before promoting any variant optimized against it.
9. **When variance grows or scores compress** on a criterion, redesign — don't "calibrate." Calibration is the wrong move at this layer.

---

## 15. Calibration set and drift detection

**Build a 100-fixture calibration set per lane** (~800 fixtures total across 8 lanes). JR-labeled binary verdicts per criterion. Stratified across artifact types AND quality levels — must include both score-1 and score-0 ground-truth examples so the judge can be measured at both poles.

**Refresh cadence:**

- **Weekly:** run the calibration set through current judges. Alarm if any criterion's rolling-mean drops 2–5% from last week's baseline. Sustained 2–5% drop over 24–48 hours warrants investigation; 5%+ pages immediately. (Stack Pulsar Mar 2026; Galileo Luna-2 / Patronus Lynx ship this pattern turnkey.)
- **Monthly:** re-label 10–20 fixtures from real client work to keep the set distribution-aligned with live traffic.
- **Quarterly:** full re-audit; retire fixtures that no longer represent live distribution.

Calibration set size convergence (Hamel Husain / Shreya Shankar eval-faq Jan 2026, Confident AI, Statsig, Arize): "Minimum viable is 50–100 examples; production-ready is 200–500; mature systems 1000+." Our 100/lane sits at the production-ready floor.

**Pin all panel models to dated versions.** `claude-opus-4-7-20260201`, not `claude-opus-4-7-latest`. When a version rolls forward (e.g. Opus 4.7 → 4.8), gate the upgrade on ≥90% agreement with prior version on the calibration set before promoting.

**Goal:** the calibration set + weekly probe + version-pinning together give us a closed-loop drift detector. Judge variance per criterion per generation (§11.5) is the Goodhart early-warning; calibration drift is the judge-stability early-warning. Both are necessary; neither replaces the other.

---

## 16. Known uncertainties

After three research passes, three uncertainties remain genuinely open. The May 18 gap-research pass graduated seven other uncertainties to prescriptions (sections 3, 5, 6, 8, 10, 11, 15 above).

- **Goodhart time-constant: outcome-shaped vs feature-shaped under matched selection pressure.** No paper has fit a curve to time-to-reward-hacking per rubric shape. Proxy Compression Hypothesis (arxiv 2604.13602) gives the structural framing — Feature → Representation → Evaluator → Environment level — but no compute-matched measurements. Only mitigation available: §11.5 variance instrumentation as a lagging indicator. Likely 6–12 months before the literature closes this.
- **Reference-free durability past ~10 generations with frontier inner-loop.** Static preference-leakage magnitudes well-established (Li et al. arxiv 2502.01534, ICLR 2026: 6–22% per related-pair). Dynamic compounding curve over generations is not. Only available signal: asymmetric panel drift — if Claude-judge mean rises faster than Gemini-judge mean while inner is Claude-family, that asymmetry is the leakage tell. Track it.
- **IRT for judges at our 100-call-per-generation scale.** Method canonical (arxiv 2602.00521, Graded Response Model, Jan 2026); no production case study below ~1000 judgments per criterion. Our judgment volume per criterion is below the threshold to fit stable GRM parameters. The simpler proxy (judge variance per criterion per generation) gives ~80% of the diagnostic value at zero engineering cost. Revisit Q4 2026 if/when rubric prose stabilizes for ≥1 month and judgment volume per criterion ≥1000.

---

## References

All citations from:

- `docs/research/2026-05-15-judges-methodology.md` — single-shot fundamentals: PoLL, calibration math, pointwise vs pairwise, TrustJudge, Evolution-without-Oracle
- `docs/research/2026-05-16-agentic-judges-methodology.md` — agentic patterns (collapses to "stay single-shot, route verifiables to existing structural_gate" for our case)
- `docs/research/2026-05-17-qualitative-judge-design-methodology.md` — prescriptive design SOTA, anti-pattern catalogue, specimen template
- `docs/research/2026-05-18-judge-design-gaps-research.md` — gap-closure pass: calibration + drift, adversarial defense, evolution-loop patterns, redundancy check, version rotation; 7 of 10 May-17 uncertainties graduated to prescriptions

Project incidents named:

- `2ce99bb` (J1–J4 σ-widening prose, rolled back)
- `ca4a256` (v2 contract-prose, rolled back)
- `698e658` → `c76f051` (Phase 4 feature-checking, rolled back — the most recent rollback and the one that prompted this guide)
- `fc99d64` (14 judge rewrites — the currently-live rubric prose under the Phase 4 revert)
