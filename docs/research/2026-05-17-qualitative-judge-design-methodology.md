---
date: 2026-05-17
type: research deliverable
status: complete
topic: optimal single-shot qualitative LLM-judge design — 2025–2026 SOTA
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
sibling: docs/research/2026-05-16-agentic-judges-methodology.md
---

# Optimal Single-Shot Qualitative LLM-Judge Design — 2025–2026 SOTA

Scope: prescriptive design choices for the rubric prose, anchor format, judge prompt, and panel structure of our 8 single-shot evolution-loop judges. Distinct from `2026-05-15-judges-methodology.md` (selection paradigms, calibration, ensemble math) and `2026-05-16-agentic-judges-methodology.md` (tool-using / verify-then-judge). This pass focuses on the *shape of the prose* and the *load-bearing premise* under selection pressure.

---

## 1. TL;DR — design choices, evidence-backed

**Adopt: binary pass/fail per criterion with detailed written critique.** Hamel Husain's 30-company production survey (hamel.dev/blog/posts/llm-judge) and Arize's 2025 retest on Claude Opus 4 / GPT-5-nano / o3 / Qwen3-235B both converge: numeric scales saturate ("plateau quickly… scores collapse into narrow bands") while binary judgments stay separable and actionable. AutoRubric (arxiv 2603.00077, validated on CHARM-100) reports **87% binary accuracy** vs degraded ordinal accuracy on heterogeneous criterion types. Move our 0/0.5/1 to **0/1 with required prose justification**; reserve 0.5 only as an explicit "way out" anchor per Anthropic Demystifying Evals.

**Adopt: reason-first CoT, but conditional.** Reasoning before the score is the Anthropic / OpenAI grader convention (anthropic.com/engineering/demystifying-evals-for-ai-agents; OpenAI Cookbook RFT graders). The Empirical Study of Design Choices (arxiv 2506.13639) reports CoT gives "minimal gains when clear evaluation criteria exist" — but it also moves GPT-4o from 0.635→0.666 correlation with 5-sample averaging. Net: CoT is cheap insurance and *forces* the judge to commit to a binary verdict that the rationale supports. Skip CoT only for the structural_gate, which is already deterministic.

**Adopt: pointwise primary, pairwise *only* at the promotion gate.** Already-locked decision from the May 15 doc; the new 2025 evidence (arxiv 2602.02219 "Am I More Pointwise or Pairwise?" + arxiv 2603.12520 "When LLM Judge Scores Look Good but Best-of-N Decisions Fail") confirms that pointwise scores correlate well with absolute quality but degrade at the *selection* step under reward-hacking pressure. Use pointwise for the digest, pairwise for variant-vs-current.

**Adopt: cross-family panel of three (Opus 4.7 + GPT-5.5 + Gemini 3 Flash) for pointwise; same panel with position-swap for pairwise.** Li et al. preference-leakage (arxiv 2502.01534, **accepted ICLR 2026**) makes same-family panels structurally indefensible inside an evolution loop where the inner-loop model is also frontier.

**On the load-bearing question — "outcome questions, not feature checks":** the literature *partially* supports our intuition. The strongest direct evidence is "Rubrics as an Attack Surface" (arxiv 2602.13576), which documents that feature-shaped criteria — even neutrally-phrased ones — enable preference drift of **up to 27.9 pp on target domains** while preserving benchmark performance. RaR (arxiv 2507.17746) and OpenRubrics (arxiv 2510.07743) both formalize a distinction between "hard rules" (verifiable features, belong in structural_gate) and "principles" (outcome-shaped questions, belong in the judge); RaR gets **+31% on HealthBench** with this split. *Nuance:* "outcome questions" must still be discriminative — vague outcome prose (e.g. "is this useful?") produces central-tendency-bias collapse per arxiv 2506.22316. Our intuition is correct in direction; it must be paired with binary anchors and behavioral specificity, or we get a different failure mode.

---

## 2. Per-question survey

### Q1. Anchor design: binary vs Likert vs reference-based vs free-text-with-derived-score

**SOTA position:** binary with prose justification wins on subjective long-form. Three independent strands of 2025–2026 evidence:

- **Arize 2025 retest** on Opus 4 / GPT-5-nano / Qwen3-235B / o3 (arize.com/blog/testing-binary-vs-score-llm-evals-on-the-latest-models): on spelling-error corruption, "GPT-5-nano, Claude Opus, and Qwen3 all plateaued quickly… scores saturating and collapsing into narrow bands." A–E rubric narrowed variance but lost resolution; categorical formats produced "narrow, separated bands" of stability vs numeric "wide or saturated bands."
- **Husain production survey** (hamel.dev/blog/posts/llm-judge): across 30+ companies, "domain expert pass/fail judgments correlate better with actual quality than granular numeric scores. People don't know what to do with a 3 or 4." Hard prescription against multi-point scales.
- **AutoRubric** (arxiv 2603.00077, Stanford SCALE 2026): unified framework defaults to binary/ordinal/nominal criteria with **87% binary accuracy** on CHARM-100, validated against ground-truth labels. Ordinal scales required few-shot calibration to reach 80% (RiceChem).

**Reference-based anchoring** wins where references *exist* (REVISEVAL ICLR 2025, arxiv 2408.09235 Reference-Guided Verdict): "reference makes this approach well-suited for tasks with clear correct answers, helps reduce judgment variability… for nuanced criteria like factual correctness." But: **reference-free can have higher agreement than reference-based on subjective tasks** per arxiv 2503.05061 ("No Free Labels"); and "reference-free evaluations have inherent biases that limit their usefulness, strongly favoring outputs from the underlying generative model" — direct preference-leakage exposure.

**When the SOTA inverts:** when the criterion is *truly* continuous (e.g. progressive shades of journalistic vs marketing voice). Then ternary (0/0.5/1) with prose anchors at extremes only — the **2026 long-form rubric paper** (cited in Adnan Masood Medium survey, Apr 2026) recommends ternary specifically for "long-form research answers with partial credit." Our 0/0.5/1 is defensible if 0.5 has a *behavioral* anchor (not a "uncertain" anchor).

**Failure modes if misapplied:** Likert with mid-anchors → central-tendency collapse (arxiv 2506.22316). Reference-based with same-family reference → preference-leakage amplification. Binary on *truly* continuous criteria → 50/50 information loss. Free-text-with-derived-score → judge re-rationalizes for any score the prompt nudges toward.

**Prescription for us:** binary 0/1 with mandatory prose critique; 0.5 only where behavioral midpoint is concretely defined; no reference exemplars (cross-fold preference-leakage risk inside evolution loop).

### Q2. Chain-of-thought: reason-first vs direct score

**SOTA position:** reason-first, *but* the gain has shrunk on frontier models. Sources:

- **Anthropic Demystifying Evals (2024, refreshed 2026):** judges produce rationale before score; rubrics are "isolated per dimension, regularly calibrated against human experts."
- **OpenAI RFT graders** (cookbook.openai.com/examples/reinforcement_fine_tuning): "the format queries the model not just for the numeric result… but also provides the model some space to think through the reasoning behind the score."
- **Empirical Study of Design Choices** (arxiv 2506.13639): "CoT additions yielded minimal gains when clear evaluation criteria exist." 5-sample stochastic averaging beat single-CoT (0.666 vs 0.635 Pearson on GPT-4o).
- **arxiv 2308 / Aparna Dhinakaran review:** "rationale prior to score ensures the final score is supported by the explanation… one controlled comparison showed little difference, though putting the explanation first means the score is generated in the context of the reasoning, rather than the reasoning being shaped to fit a predetermined score."

**When CoT inverts:** Eugene Yan cites the "Finding Blind Spots" result where "direct scoring with CoT outperformed more advanced strategies that involved rules and rubrics" — i.e. on tasks the judge can solve in one shot, structured rubric-CoT can over-reason. Frontier judges (Opus 4.7, GPT-5.5) are most prone to "over-reasoning and injecting too much background knowledge" (Yan's diagnosis of GPT-4 initial underperformance).

**Failure mode:** if CoT is unstructured ("think step by step"), the judge invents its own rubric and ignores ours — directly enabling the Rubrics-as-Attack-Surface drift (arxiv 2602.13576). Mitigation: structured CoT — the judge must produce a per-criterion verdict before the aggregated score.

**Prescription:** mandatory CoT, *structured per criterion* (one rationale block per binary criterion, not a free-form essay), score emitted after rationale.

### Q3. Pointwise vs pairwise vs ranking

May 15 doc covered Liusie + TrustJudge. New 2025–2026 evidence:

- **"Am I More Pointwise or Pairwise?"** (arxiv 2602.02219, Feb 2026): position bias in rubric-based judges differs by paradigm — pointwise judges with rubrics carry latent positional preferences in *which criterion they emphasize first*; pairwise judges carry positional preference in candidate order. Both need swap mitigation.
- **"When LLM Judge Scores Look Good but Best-of-N Decisions Fail"** (arxiv 2603.12520, Mar 2026): pointwise judges that report 0.85+ Pearson with humans on absolute scoring still produce **best-of-N selection accuracy as low as random** under selection pressure. Direct evidence for our hypothesis that the evolution loop's selection step needs a different primitive than the digest's absolute score.
- **Unified Pairwise Framework** (arxiv 2504.04950): pairwise reward models outperform pointwise on both IID and OOD on RewardBench; "pairwise reward models' average accuracy across front and back evaluations consistently surpasses individual front and back accuracies."

**Cost/latency:** pairwise doubles judge calls (swap). For our 8 lanes × 3-model panel × 5–30 fixtures, this is +~$3–6/generation incremental; acceptable as a promotion gate but not as the digest engine.

**When pointwise wins:** monitoring/observability (Yan: "longitudinal monitoring"), absolute-quality alerts, anything where there's no current.json baseline.

**When pairwise wins:** the single decision "is variant V better than current C" — exactly our promotion gate.

**Prescription** (unchanged from May 15 + reinforced): pointwise pointwise digest, pairwise promotion gate with position swap.

### Q4. Position / verbosity / length bias mitigations

**SOTA on frontier models 2025–2026:**

- **Style bias dominates** (Justice or Prejudice? arxiv 2410.02736 + Adaline 2025 follow-up): style bias 0.76–0.92 across all frontier models, position bias ≤0.04 — i.e. **position bias is ~20× smaller than style bias** on frontier models. Don't over-engineer position swap; do engineer style-neutrality.
- **Length normalization** (LC-AlpacaEval, arxiv 2404.04475): linear-regression mediator moved Chatbot-Arena Spearman from 0.94→0.98 (+4 pts). But: **arxiv 2604.23178 ("Judging the Judges") finds "no significant trend between prompt/response lengths and bias metrics after controlling for quality gap"** — i.e. length bias is real but smaller than commonly stated. AlpacaEval-style regression is cheap; in-prompt "don't be biased toward longer outputs" is theatrical.
- **Position swap on pairwise:** Brenndoerfer 2026 + arxiv 2025.ijcnlp-long.18 — "accuracy shifts exceeding 10% in pairwise code judging when simply swapping response order." Standard mitigation: run both orderings, accept only if both agree. Production cost: 2× per pairwise call; debiasing yields **+13.0 pp accuracy for Claude** per arxiv 2510.12462.
- **Verbosity:** newer paradoxical finding — "all models prefer concise responses over padded alternatives." Frontier judges have largely fixed naive verbosity bias; **conciseness preference is now a *new* bias** that penalizes well-supported long-form briefs.

**Prescription:** (a) position swap on pairwise — mandatory, both-must-agree gate. (b) Skip explicit anti-verbosity prose; instead include a length-band guideline in the structural_gate. (c) Skip in-prompt "be unbiased" instructions; theatrical per the Empirical Study.

**Failure modes if misapplied:** in-rubric anti-bias clauses redistribute the bias without removing it (Empirical Study, arxiv 2506.13639); over-aggressive length normalization compresses legitimate quality variance (briefs that *should* be longer than 200 words to be high-quality get penalized).

### Q5. Reference-based vs reference-free for subjective evolution-loop artifacts

**SOTA position:** reference-free with strong anchored rubric for our case. Reasoning:

- The Reference-Guided Verdict paper (arxiv 2408.09235, ACL 2025 reprint) shows reference-based wins on free-form QA *where references can be objectively curated*. For competitive briefs / monitoring digests / marketing audits, no such curated reference exists; constructing one (e.g. "the best CI brief we promoted in v0.4") introduces a self-reinforcing preference-leakage loop that biases toward stylistic mimicry of past winners.
- **REVISEVAL** (ICLR 2025) generates a "response-adapted reference" — i.e. the judge first revises the output into what *would* be a better answer, then scores against that. This is essentially agentic and falls under the May 16 doc's scope; the *base mechanism* still preference-leaks if the reviser is in the same family as the inner-loop generator.
- **"No Free Labels"** (arxiv 2503.05061): reference-free metrics can have *higher* agreement with human annotators than reference-based on subjective tasks; the trade-off is variance.

**When the SOTA inverts:** if a workflow ever has a hand-curated gold exemplar that's *human-authored and stable* (e.g. a JR-written CI brief we trust as canonical), reference-based scoring on similarity-of-outcome (not similarity-of-prose) outperforms reference-free.

**Prescription:** reference-free for the 8 evolution-loop judges. Re-evaluate per lane only if/when we accumulate ≥10 JR-authored canonical exemplars per lane — not the case today.

**Failure mode if misapplied:** reference-based with a model-authored reference compounds preference leakage exponentially over generations — the evolution loop converges on the reference's style, not the underlying quality dimension.

### Q6. Panel composition and preference leakage

- **Li et al. preference leakage** (arxiv 2502.01534, ICLR 2026): three relatednesses cause leakage — same model, inheritance, same family. Bias quantified across Arena-Hard and AlpacaEval 2.0 with a novel "preference leakage score." Followup: "Who's your judge? On the detectability of LLM-generated judgments" (arxiv 2509.25154, 2025) — leakage is detectable from judgment text alone, meaning leaked judges have a recognizable fingerprint we could screen against.
- **PoLL / Verga** (May 15 doc): three-model cheap-diverse panel beats single-frontier at 1/7th–1/8th cost, σ from 6.1→2.2.
- **Cross-family is the dominant mitigation** in the new 2026 literature; the magnitude has not changed (6–22% scoring inflation for own-family) but the recommendation is harder than 2024 because the modern inner-loop *is* a frontier model.

**Prescription:** Opus 4.7 + GPT-5.5 + Gemini 3 Flash; aggregate by mean for pointwise digest, by 2-of-3 majority for pairwise promotion gate. **Never use Opus 4.7 alone** when the inner-loop is also Anthropic-family. If we run codex/GPT-5.5 inner-loop (per the evolution redesign), the judge panel must still include all three families because the workflow could mutate to a different inner-backend mid-run.

**Failure mode:** same-family panels for cost savings — the 7–8× PoLL savings come from *cheap diverse models*, not *cheap same-family models*; the latter has zero leakage benefit.

### Q7. Rubric prose anti-patterns (the most important question)

The literature names six distinct anti-patterns relevant to us. **All six match a Phase 4 rollback failure mode** the project has already hit at least once:

1. **Feature-checking criteria** ("Does the brief mention X named entity?"). Documented in Rubrics-as-Attack-Surface (arxiv 2602.13576): feature-shaped criteria enable **preference drift up to 27.9 pp on target domains** while benchmark scores stay stable. Workflows learn to plant the feature without the underlying quality. *This is the Phase 4 pathology we rolled back at HEAD c76f051.*
2. **Framework-name embedding** (e.g. "Does this follow the Helmer / FAA-AD / MrBeast framework?"). No paper names this directly but it is a special case of #1 — the framework name *is* the feature.
3. **Anti-gaming clauses** ("Do not be biased toward longer outputs"). Empirical Study of Design Choices (arxiv 2506.13639) + Eugene Yan: "primarily perturb the score distribution without changing rank order." Theatrical.
4. **Calibration prose ("a 1 means…")** with too many intermediate anchors. Central-tendency-bias paper (arxiv 2506.22316): "judges do not share the same latent image of what a '3' versus a '5' means" — broad scales without behavioral anchors collapse toward the middle.
5. **Stealth-drift-prone rubrics** (arxiv 2602.13576): rubrics with implicit weight reshuffling between criteria — "preserve benchmark performance while inducing systematic drift… up to 27.9% in harmlessness tasks." Editing rubric prose without re-running calibration is a direct attack vector even from well-intentioned authors.
6. **Holistic prose where analytic was needed.** PMC11359436 (medical-research education 2024) + arxiv 2604.00259 (LLM essay scoring 2026): analytic rubrics give Cohen's κ 0.60 vs holistic κ 0.41 — analytic structurally beats holistic on inter-rater reliability for both human and LLM raters.

Two additional anti-patterns we've hit empirically that the literature *doesn't* name explicitly:

7. **σ-widening as a goal** ("rewrite to spread scores"). May 15 doc + Rating Roulette: the noise floor is inherent; spreading scores past basic anchors trades information for variance. Theatrical.
8. **Contract-prose** ("the judge SHALL emit…"). Forcing format compliance via prose creates a meta-task the judge attends to *instead of* the substantive quality question.

### Q8. Goodhart-resistance under selection pressure

**The load-bearing question.** The literature has a clearer answer than I expected:

- **"Reward Hacking in the Era of Large Models"** (arxiv 2604.13602, Apr 2026): proposes the **Proxy Compression Hypothesis (PCH)** — exploitation escalates Feature-level → Representation-level → Evaluator-level → Environment-level. Feature-level is the entry point. **Direct support for outcome-shaped criteria:** the entire taxonomy is built on the claim that feature-shaped proxies degrade fastest under optimization pressure.
- **"Inference-Time Reward Hacking in LLMs"** (arxiv 2506.19248): theoretical proof of *inevitability* — reward hacking is not a misconfiguration, it's a property of any sufficiently optimized loop. Mitigation: **Best-of-Poisson sampling + HedgeTune** algorithm; the latter is a *sampling* fix not a *rubric* fix, but the framing matters — even the best rubric will be gamed eventually, so the design target is *time-to-Goodhart* not *Goodhart-immunity*.
- **Rubrics as Rewards** (arxiv 2507.17746, OpenReview Oct 2025): the cleanest empirical support for outcome-questions-not-feature-checks in our exact setting. RaR's "rubrics composed of modular, interpretable subgoals" beat "direct Likert-based rewards" by **+31% on HealthBench, +7% on GPQA-Diamond.** The subgoals are explicitly outcome-shaped ("does the response address the patient's actual concern?") not feature-shaped ("does the response mention diabetes type 2?").
- **OpenRubrics** (arxiv 2510.07743): formalizes the split — **Hard Rules** = "explicit, objective requirements stated directly in the user prompt, such as length limits, specific formats, or mandatory content elements" (these belong in our structural_gate); **Principles** = "implicit qualities" derived contrastively from preferred-vs-rejected pairs (these belong in our judge). +8.4% over size-matched baselines on RewardBench-type benchmarks.

**Additional patterns the literature supports:**

- **Dynamic rubric curation** (arxiv 2602.01511 Alternating RL): regenerate rubrics from preferred-vs-rejected contrasts as the policy evolves. Goodhart-resistant by construction; cost: rubric becomes a moving target, hard for humans to track.
- **Meta-criteria / veto rubrics** (mentioned across Confident AI + Comet writeups 2025–2026): a separate top-level question "does this response look gamed?" run as a final check. No published effect size; treat as suggestive.
- **High-variance rubric filtering** (Adnan Masood Medium 2026): drop criteria where judge variance across re-runs exceeds threshold — i.e. the criterion is too ambiguous to be load-bearing.

**Counter-position:** the literature does *not* universally endorse outcome-questions. Anthropic Demystifying Evals shows a concrete feature-check example ("The answer should always mention 'Acme Inc.' in the first sentence") as a *positive* pattern — but this is a structural/hard-rule check, which we are already routing to structural_gate. The Anthropic guidance is consistent with the OpenRubrics split, not contradictory.

**Prescription:** outcome questions for the 8 judges; hard-rule feature checks for structural_gate; *both* must change versions in lockstep when we edit the workflow surface.

### Q9. Anthropic / OpenAI / DeepMind published guidance

- **Anthropic Demystifying Evals + Claude 4.7 model card eval methodology** (2024–2026): isolated judges per dimension, rationale-before-score, regular calibration against human experts (~50 labels working number), explicit "give the judge a way out" option, combine groundedness + coverage + source-quality checks for agentic tasks. Latest 2026 update explicitly recommends pairing **rubrics with Item Response Theory** to identify which criteria are too ambiguous or too sensitive — psychometric judge evaluation is now Anthropic-published guidance.
- **OpenAI RFT graders** (cookbook.openai.com 2025): graders return 0–1 scalar; rubric structure shows scoring categories with explicit weights ("exact lexical match +0.15, clinical synonyms +0.35, same disease family +0.35"); reasoning space before final score; "evaluated on a subset of base model predictions, with domain expert reviewers verifying that model assigned scores reflect preferred answer orderings."
- **DeepMind AlphaEvolve** (DeepMind blog May 2025, Wikipedia, arxiv 2510.06056): **AlphaEvolve's evaluation function is machine-gradeable scalar metrics, not LLM-judge prose.** The system "tackles problems with machine-gradeable solutions" — user must specify an evaluation function that maps a solution to scalar metrics. Implication: AlphaEvolve does *not* use the design we're working on; its success doesn't directly support our LLM-judge approach. The lesson is *inverse* — DeepMind chose to avoid the LLM-judge problem entirely by scoping AlphaEvolve to verifiable domains. We can't follow that path because our artifacts are inherently subjective.

### Q10. Production observability vendor defaults

**Promptfoo:** `llm-rubric` is its default, supports binary pass/fail and rubric scoring; position swap available for pairwise. Encourages criterion-per-eval not blended rubrics.

**DeepEval (Confident AI):** ships **DAG metric** — structures the rubric as a decision tree of binary sub-decisions; G-Eval default is direct scoring; explicit guidance to "use CoT chain that has 3-5 steps" for non-trivial criteria. Production consensus visible: their default *is* the binary-with-CoT pattern.

**Langfuse / Galileo / Patronus / Ragas:** all ship default rubrics structured as **per-dimension isolated judges**, not blended. Galileo Luna-2 ships sub-200ms judges for production — drives them toward small/fast single-shot, which is our regime. Ragas's RAG metrics (context precision, faithfulness, answer relevancy) are all binary-derived under the hood despite reporting continuous-looking scores.

**Vendor-bias caveat:** all six want you to use their framework; defaults skew toward what's easy to ship in their abstractions, not necessarily what's optimal. The signal is the *convergence* — five independent vendor codebases ship the same pattern: per-criterion isolated binary judge with CoT.

**Prescription:** match the vendor consensus on per-criterion isolated binary judge with structured CoT. Don't blend criteria into a single holistic score.

---

## 3. Anti-pattern catalogue

Each entry: anti-pattern, failure mode it produces, strongest published evidence, project incident it explains.

- **Feature-checking criteria** ("Does X mention Y?"). Failure: workflow learns to plant Y without producing the underlying quality. Evidence: Rubrics-as-Attack-Surface (arxiv 2602.13576) — up to 27.9 pp drift on target domains. Project incident: Phase 4 prose rollback at HEAD c76f051 (Helmer-power-name-check, FAA-AD-slot-fill, MrBeast pacing-check).
- **Framework-name embedding** in rubric prose. Special case of feature-checking; the framework name is the feature. No standalone paper; same evidence as #1.
- **Anti-gaming clauses** ("do not prefer long outputs"). Failure: redistributes bias without removing it; theatrical. Evidence: Empirical Study (arxiv 2506.13639) + Eugene Yan production survey.
- **Broad-scale anchorless rubrics** (1–10 with no behavioral anchors). Failure: central-tendency collapse. Evidence: arxiv 2506.22316 — "judges do not share the same latent image of what a '3' versus a '5' means."
- **Implicit-weight reshuffle** rubrics. Failure: stealthy preference drift even from well-intentioned edits. Evidence: arxiv 2602.13576 — population-based search over natural-language rubric variants induces drift through "the rubric decision interface." Project relevance: every rubric edit since `ca4a256` is a potential drift vector if not re-calibrated.
- **Holistic prose where analytic was needed.** Failure: Cohen's κ drops from 0.60 → 0.41 between analytic and holistic in human raters; LLM raters show same pattern. Evidence: arxiv 2604.00259, PMC11359436.
- **σ-widening as goal.** Failure: trades information for variance; can't beat inherent per-draft noise floor. Evidence: Rating Roulette (arxiv 2510.27106) + our own `2ce99bb` empirical observation.
- **Contract-prose** ("judge SHALL emit JSON…"). Failure: meta-task replaces substantive task in judge attention. No direct paper; consistent with arxiv 2506.13639's finding that prose-side mitigations yield single-digit gains while moving cognitive load away from the criterion.
- **Reference exemplars from same model family.** Failure: preference-leakage amplification across generations. Evidence: Li et al. (arxiv 2502.01534, ICLR 2026) — 6–22% scoring inflation per related-pair.
- **Mid-anchor specifications for 0.5.** Failure: judges hide ambiguity in the middle; central-tendency bias compounded by "way out" availability without behavioral specificity. Evidence: arxiv 2506.22316 + Anthropic Demystifying Evals (way-out is meant for *unknown*, not for *medium*).
- **Free-text-with-derived-score.** Failure: judge rationalizes any score it's nudged toward; rationale is post-hoc justification, not pre-commitment. Evidence: Aparna Dhinakaran 2026 review — reason-before-score works only when score is committed after reason, not when score is the prompt target.

---

## 4. Recommended specimen template — competitive intelligence lane

Below is a concrete rubric block + judge prompt for one criterion in the **competitive** lane. This is the shape every criterion across the 8 judges should match.

```
CRITERION C-1 — Strategic insight density

Outcome question (binary):
Would a senior partner reading this brief change one upcoming
client conversation based on a specific named claim in the brief?

Score 1 (yes) — the brief contains at least two specific items where
  (a) a named entity is paired with a numeric or dated finding, AND
  (b) the finding implies a different action than the partner would
  have taken without reading it.
  Example (do not optimize toward this): "Pinsent Masons pulled 6
  partners from 4 firms in May 2026, including 2 from Dentons RES
  practice → triggers DWF retention-conversation prioritization
  for senior RES team this week."

Score 0 (no) — every claim is either (a) unnamed, (b) undated, or
  (c) actionable only at the strategic-posture level (no specific
  upcoming conversation changes).

Required CoT (one rationale block per criterion):
- Step 1: List every named entity + numeric/dated claim in the brief.
- Step 2: For each, identify the specific conversation it would change.
- Step 3: Emit final 0 or 1 with one-sentence justification.

Do not score: visual polish, citation count, length, presence of any
named framework, executive-summary structure, follow-up calendar.
Those belong to the structural_gate; the judge does not see them.
```

**Judge prompt wrapper** (shared across all criteria in the lane):

```
You are scoring a competitive intelligence brief for a B2B law firm
client. You will see the brief and the rubric. You score each
criterion independently with a binary 0 or 1 and a one-sentence
rationale. Do not blend criteria. Do not infer criteria not stated.
If a criterion's condition is genuinely ambiguous from the brief
alone, emit 0.5 + the word "unknown" + one sentence on what would
have to be present to commit to 1.

Emit per-criterion JSON: {"criterion_id": "...", "rationale": "...",
"score": 0 | 0.5 | 1}.
```

Five criteria per lane (not eight, not three — the Empirical Study finds diminishing returns past 5 binary criteria; central-tendency bias starts to surface at >5 per artifact). Each criterion is an outcome question with behavioral 0-anchor and 1-anchor. Total prose budget per criterion: ~150 words including anchors. No framework names. No anti-gaming clauses. No reference exemplars (the "do not optimize toward this" hedge on the 1-anchor is the lightest possible mitigation against using the anchor as a target).

**Why this shape:** binary maps to Husain + AutoRubric + Arize evidence; CoT maps to Anthropic + OpenAI grader convention; outcome question with behavioral anchor maps to RaR principles + OpenRubrics CRG; 0.5 = unknown maps to Anthropic "way out"; cross-criterion isolation maps to vendor consensus (Promptfoo, DeepEval, Galileo, Patronus, Ragas).

---

## 5. What's still uncertain

Honest list of open questions where 2025–2026 literature is split or absent:

- **Optimal criterion count per lane.** Vendor defaults vary 3–8. Empirical Study suggests diminishing returns past ~5; AutoRubric's CHARM-100 used 100 criteria per item but is a benchmark, not a production setup. No published study targets the specific 5–8-criterion regime under evolution-loop selection pressure.
- **How fast Goodhart fires on outcome-question rubrics.** The literature establishes outcome-shaped is *more resistant* than feature-shaped, but no published study measures *time-to-Goodhart* across the two shapes under matched selection pressure. We will need to instrument this ourselves.
- **Whether reference-free is durable past ~10 generations** when the inner-loop is itself frontier. Preference-leakage literature establishes the *static* magnitude; the dynamic compounding rate over evolution generations is unstudied.
- **Whether ternary (0/0.5/1) with a behavioral middle anchor outperforms strict binary** on long-form subjective artifacts. The 2026 long-form rubric paper recommends ternary; AutoRubric's CHARM-100 shows binary wins on chatbot eval; neither directly tests our regime.
- **Whether structured CoT (per-criterion rationale) is meaningfully different from holistic CoT.** Aparna Dhinakaran's review notes "little difference in measured accuracy" between reason-first and score-first orderings. We assume structured > holistic; the literature does not test this directly.
- **IRT for judges in production.** Anthropic's 2026 guidance recommends it; no published case study from a production operator at our scale. Treat as suggestive.
- **Dynamic rubric curation** (Alternating RL, arxiv 2602.01511): theoretically attractive, but every published implementation is research-scale. Production cost/benefit unknown.

---

## Summary

- **Word count:** ~3300 words.
- **Top-5 prescriptions:** (1) binary 0/1 with mandatory per-criterion CoT — Hamel hamel.dev + Arize 2025 + AutoRubric arxiv 2603.00077 (87% binary accuracy); (2) outcome questions with behavioral anchors, not feature checks — RaR arxiv 2507.17746 (+31% HealthBench) + OpenRubrics arxiv 2510.07743 (+8.4% RewardBench) + Rubrics-as-Attack-Surface arxiv 2602.13576 (27.9pp drift on feature-shaped); (3) cross-family three-model panel Opus 4.7 + GPT-5.5 + Gemini 3 Flash — Li et al. arxiv 2502.01534 (ICLR 2026); (4) pointwise digest + pairwise promotion gate with position swap — arxiv 2603.12520 (best-of-N selection failure) + arxiv 2602.02219 (rubric-pointwise position bias) + arxiv 2510.12462 (+13.0pp Claude debiasing); (5) ≤5 criteria per lane, isolated per criterion, ~150 words each, no framework names, no anti-gaming clauses — Empirical Study arxiv 2506.13639 + vendor consensus (Promptfoo / DeepEval / Galileo / Patronus / Ragas).
- **Top-3 anti-patterns:** (1) feature-checking criteria — explains the Phase 4 rollback; (2) implicit-weight reshuffle / framework-name embedding — direct attack surface per arxiv 2602.13576; (3) broad-scale anchorless rubrics or σ-widening — central-tendency collapse per arxiv 2506.22316.
- **Load-bearing question answer:** **"outcome questions, not feature checks" is supported by the literature, with caveats.** Strongest evidence: RaR (arxiv 2507.17746, +31% HealthBench), OpenRubrics (arxiv 2510.07743, formalized Hard-Rule/Principle split, +8.4% RewardBench), Rubrics-as-Attack-Surface (arxiv 2602.13576, 27.9pp drift on feature-shaped under selection). Caveat: vague outcome prose produces central-tendency collapse (arxiv 2506.22316); the prescription is *outcome question + behavioral binary anchor*, not outcome question alone. DeepMind AlphaEvolve does *not* support the design (it uses machine-gradeable scalar metrics instead of LLM judges).
- **Uncertainties flagged:** optimal criterion count under our 5–30 fixture regime; Goodhart time-constant under outcome-shaped vs feature-shaped rubrics; reference-free durability past ~10 generations; ternary-vs-binary on long-form subjective; structured-vs-holistic CoT; IRT-for-judges at production scale; dynamic rubric curation cost/benefit.
