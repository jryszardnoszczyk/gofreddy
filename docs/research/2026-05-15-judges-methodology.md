# LLM-as-Judge Methodology Survey 2023–2026: Evidence-Based Recommendations for Autoresearch Evolution Loop

Date: 2026-05-15
Author: research sub-agent (parent: judge-design RESET trilogy, `docs/handoffs/2026-05-15-judge-design-reset-and-plan.md`)
Scope: single-judge absolute-gradient 0/0.5/1 scoring on long-form marketing artifacts at N=5–30 fixtures per lane, inside an evolution loop.

## Executive summary

The published literature 2023–2026 converges on a hard, uncomfortable claim that aligns with our own empirical floor (`2ce99bb` 2026-05-08 — claude+codex ~2-pt per-draft noise):

1. **Single-judge absolute scoring on small N for long-form artifacts is, in the literature, the least reliable common pattern.** Krippendorff α has been measured <0.8 on identical inputs across runs (Haldar & Hockenmaier 2025, "Rating Roulette"), and 23–37% of pairwise comparisons disagree with the pointwise ranks the same judge produced (Wang et al. 2025, "TrustJudge").
2. **The single most reproducible variance-reduction lever is not prompt tightening — it is sample averaging across multiple judge calls and/or a diverse-family panel.** The 5–10 papers reviewed below all show prompt-side mitigations yield single-digit gains; ensemble methods yield 10–30 pt gains and ~7–8× cost reduction simultaneously when shifting from one GPT-4-class judge to a panel of cheaper diverse models (Verga et al. 2024, "Replacing Judges with Juries").
3. **Within an evolution loop specifically, all of the literature on reward-model overoptimization (Gao et al. 2022; Pan et al. 2024 ICRH; AI Safety II review 2025) warns that any single learned proxy becomes the wrong target once selection pressure is applied for many generations.** Goodhart effects are visible after surprisingly few iterations — this isn't a "scale up later" risk, it's a "your variant promotion is selecting for judge idiosyncrasies right now" risk.
4. **The prose-tightening posture we have been correctly avoiding since `2ce99bb`** is, in the literature, the most-cited theatrical mitigation. "Empirical findings reveal no significant trend between prompt/response lengths and bias metrics after controlling for quality gap" (Judging the Judges 2024, arxiv 2604.23178). Tightening prose to widen σ on N=5–8 is, per the same body of work, overfitting to the noise floor.

The recommendation in §9 is a targeted three-piece intervention — not a paradigm rewrite — grounded in those four points.

---

## 1. Pairwise vs absolute scoring

### What the literature actually says

The historical narrative ("pairwise is more reliable than absolute for subjective tasks") is now contested by a 2025 paper that ran the experiment carefully:

- **Liusie et al. 2025 (arxiv 2504.14716, COLM 2025), "Pairwise or Pointwise?":** Pairwise preferences flip in **~35% of cases** when an adversarial generator inserts spurious distractor features; absolute scores flip in only **~9%** under the same attack. Pairwise judges are exploitable along axes generators can learn (length, tone, formatting), and any evolution loop is exactly the setup that lets a generator learn to exploit them. Recommendation in the paper itself: "absolute scoring is more robust to manipulation, producing judgments that better reflect response quality" for evaluation tasks where there's a defined quality concept.
- **Wang et al. 2025 (arxiv 2509.21117), "TrustJudge":** Documents two inconsistencies that argue *against* trusting either paradigm naively. **Score-Comparison Inconsistency** — where the judge gives item A a higher pointwise score but picks B in pairwise — ranges from 23.32% (Llama-3.1-70B) to 36.65% (Llama-3.2-3B), with GPT-4o at 27.95%. **Pairwise Transitivity Inconsistency** (A>B>C>A circular preferences) ranges 15–55%. Their finding: increasing the discrete scoring scale from 5 to 100 points **consistently reduces** Score-Comparison Inconsistency. Both paradigms are unstable; the pairwise pathology is more catastrophic for ranked selection because circular preferences make top-K selection ambiguous.
- **Eugene Yan's production survey (eugeneyan.com/writing/llm-evaluators):** Distinguishes objective (factuality, structural facts — pointwise works) from subjective (style, helpfulness — pairwise gives stabler human-correlation). On factual consistency the pairwise vs direct gap was tiny: **0.47 vs 0.46** correlation. So the "pairwise is better" claim only buys ~1 correlation point on objective dimensions.
- **LMSYS Chatbot Arena (Zheng et al. 2023, arxiv 2306.05685; Bradley-Terry transition 2024 arxiv 2403.04132):** *The production benchmark that actually runs at scale uses pairwise* — but the relevant pattern is they aggregate **thousands of votes per model** through Bradley-Terry MLE, *not* trust any single pairwise verdict. The number that makes pairwise work in production is the count of comparisons (10⁴–10⁶), not the comparison primitive itself.

### Recommendation for our use case

For our long-form marketing artifacts at N=5–30 with one variant per generation evaluated against an implicit baseline, **stay on absolute scoring as the surviving anchor for the digest/snapshot, but adopt pairwise as the *promotion gate* primitive** for variant-vs-current.json comparisons.

Reasoning: we are not trying to produce a leaderboard (where pairwise wins via volume). We are trying to make one decision per generation — "is variant V better than current C." That single decision is exactly where pairwise has the cleanest production evidence (Eugene Yan, AlpacaEval 2.0 Length-Controlled, LMSYS). And by using pairwise *only* at promotion time, not for the absolute storyboard/geo/marketing digest displayed to operators, we avoid the 23–37% Score-Comparison-Inconsistency trap that would corrupt our archived history.

This is a small-surface change: keep the absolute scorer, *add* a pairwise gate at promotion. It does not require rewriting `score_variant.py` or any archived `scores.json`.

---

## 2. Few-shot anchoring

### What works, citation-grounded

- **G-Eval (Liu et al. 2023, arxiv 2303.16634):** Chain-of-thought-derived evaluation steps + form-filling at scoring time achieved 0.514 Spearman correlation with human on summarization, the strongest non-finetuned result at the time. Critically, they did *not* use few-shot exemplars — they used auto-generated CoT evaluation steps. This is evidence that the gain is from explicit per-criterion sub-questions, not from anchor examples.
- **Prometheus 2 (Kim et al. 2024, arxiv 2405.01535):** Fine-tuned 8x7B judge model trained on 100K direct-assessment + 200K pairwise rubrics. Hits Pearson 0.897 vs GPT-4's 0.882 on 45 customized rubrics. Their *training* used few-shot-style rubric anchors, but at *inference* time the model takes only a rubric + reference answer + response. Implication: anchor examples are valuable for *training* the judge calibration, less so for ad-hoc prompt-time scoring.
- **Empirical Study of Design Choices (arxiv 2506.13639, 2025):** **Removing the evaluation criteria dropped GPT-4o human correlation from 0.666 to 0.591.** But — relevant for context-bloat — they found that *providing descriptions only for extreme scores (1 and 5)* yielded results comparable to full Likert anchor sets. Mid-scale anchors are unnecessary overhead. They also found chain-of-thought reasoning provided "minimal gains when clear evaluation criteria exist."
- **LangSmith Align Evals & Evidently AI guidance:** Production teams converge on **~50 human-labeled instances** as the calibration starting point — used to *write* the rubric anchors, not to dump them all into the prompt.
- **Central tendency bias on broad scales (arxiv 2506.22316, 2025):** Likert rubrics without exemplars collapse toward central scores because "judges do not share the same latent image of what a '3' versus a '5' means." **Narrow scales (3–5 levels) with behavioral anchors outperform broad-scale anchorless rubrics.** This is direct evidence for our existing 0/0.5/1 structure being closer to right than wrong.

### Recommendation: when worth it, what shape, what to avoid

For us specifically:

- **Worth it** for the *0 vs 0.5 boundary and 0.5 vs 1 boundary*. Two anchors per criterion — what a 0 looks like, what a 1 looks like. Skip the 0.5 anchor (the "give judge a way out / unknown" pattern in the Anthropic Demystifying Evals post handles ambiguous middle cases without needing an anchor for them).
- **Shape:** behavioral, not topical. "Score 1 = digest cites a specific named entity + a specific numeric finding + a specific outcome (e.g., 'Pinsent Masons May 2026 raid pulled 6 partners')". "Score 0 = digest is unspecific marketing prose." Not: an example digest, which costs ~300 tokens, drifts the judge toward stylistic mimicry, and counts as preference-leakage exposure if drawn from the same model that generates variants.
- **Avoid:** dumping 3+ examples per criterion. The Empirical Study of Design Choices showed diminishing returns past extreme anchors; we'd be paying ~1K tokens per criterion for sub-1pp gains. Avoid: anchors that are themselves marketing artifacts from earlier promoted variants — that's the most direct preference-leakage path (Li et al. 2025, arxiv 2502.01534).

---

## 3. Calibration sets

### What the literature converges on

- **Hopkins et al. 2026 (arxiv 2601.20913), "Noisy but Valid":** Provides the formal framework for using a *small* human-labeled calibration set to estimate judge TPR/FPR, then statistically correct downstream eval-batch results. They varied n_M from 25 to 100 and observed standard-deviation behavior consistent with O(1/√n_M). **Type-I error bound is ≤ ζ + O(n_J^-½ + n_M1^-½ + n_M0^-½)** — explicitly, calibration uncertainty enters the bound, meaning the framework remains valid (just more conservative) when calibration is scarce. This is the closest the literature gets to a "minimum viable calibration set" answer: **25–50 labels per judge per criterion gives usable corrections; 100 stabilizes them.**
- **Fiedler 2026 (arxiv 2605.06939, J/ΔJ paper):** Defines **Youden's J = sensitivity + specificity − 1** as the judge-quality scalar. Shows **bias-correction variance scales as 1/J²** — so when J is low, calibration buys you very little. **Shared-calibration across compared models is severely unreliable when |ΔJ| confidence interval excludes zero** — i.e., if a judge is differently-good at scoring model-A vs model-B outputs, you cannot use the same calibration constants for both. *This is directly relevant to evolution loops where successive generations drift in style.*
- **Anthropic, "Demystifying Evals for AI Agents" (anthropic.com, 2024):** Explicit production guidance — "LLM-as-judge graders should be closely calibrated with human experts" + "Once the system is robust, it's sufficient to use human review only occasionally." Anthropic doesn't publish their N, but their recommendation pattern is per-dimension isolated judges, each closely calibrated, each rebuilt as the artifact distribution drifts.
- **LangSmith Align Evals & GoDaddy Calibrating Scores blog:** Both use **~50 human-labeled instances** as the working number for calibration cycles. The pattern is iterative: label, run judge, find disagreements, edit rubric, re-run, re-disagree. The 50 is small enough to re-label after rubric edits.

### Recommendation: minimum viable, labeling protocol, drift detection

- **Minimum viable size: 30–50 labels per lane.** Below 30 the standard-deviation behavior O(1/√n) is too loose; above 50 you stop getting per-label-marginal information. We can stop at 30 if every label is read by a human-and-codex-and-claude triad (high-info per label).
- **Labeling protocol:** JR labels 30 in one sitting per lane (not split — single-sitting reduces Mon-vs-Fri drift, which the Comet/Evidently posts both call out). Score 0/0.5/1. *Then* the rubric anchor text is derived from disagreements between JR and current judge, not vice versa.
- **Drift detection:** Re-score the calibration set after every rubric edit *and* after every meta-agent mutation that touches judge prompts. The condition for "drift detected" is: any single label flips between rubric versions. The literature has no published threshold for "X% drift = stop"; given Fiedler's |ΔJ| warning, the conservative posture is *any* unexplained flip pauses promotion until a rubric explanation is found.
- **What's not worth it:** dynamic re-calibration every run. The Fiedler J/ΔJ paper's central warning is that bias-correction estimates *themselves* become unstable when the judge quality is low — we'd be adding noise on top of noise. Calibrate at version boundaries, not at every fixture-batch.

---

## 4. Bias mitigations: what works in production, what is theatrical

Ranked by production evidence:

### Validated (cite, deploy):

1. **Cross-family judge.** Self-preference is well-documented (arxiv 2508.06709 "Play Favorites" + Li et al. 2025 "Preference Leakage" arxiv 2502.01534). Magnitude: **6–22% scoring inflation** for own-family outputs; the bias "nearly disappears when models do not know the authorship." Concrete: if variants are generated by Claude (via codex/opus inner-loop), the judge should not be Claude. We already partially do this — opus outer + codex secondary. The literature supports keeping the cross-family split.
2. **Position randomization in pairwise.** Zheng et al. 2023 documented win-rate shifts **from 2.5% to 82.5%** based on output position alone in raw pairwise. Standard mitigation: run both orderings, accept only if both agree. Production-cost: 2× per pairwise call. *Only relevant if we add the pairwise promotion gate per §1.*
3. **Sample averaging across N≥3 judge calls.** Empirical Study of Design Choices (arxiv 2506.13639): non-deterministic sampling with mean aggregation **outperforms greedy decoding consistently** and exceeded the no-CoT baseline. Specifically GPT-4o moved from 0.635 → 0.666 correlation with 5-sample averaging. This is the cheapest variance reduction that exists in the literature.
4. **Panel of cheap diverse judges (PoLL).** Verga et al. 2024 (arxiv 2404.18796): three-model panel (Command R + Claude Haiku + GPT-3.5) hit Cohen κ=0.763 on Natural Questions vs single GPT-4's 0.627. Standard deviation across judges dropped from σ=6.1 (GPT-3.5 alone) to **σ=2.2** for the panel. **Cost: ~7–8× cheaper than one GPT-4 call.** Best documented win in the field.
5. **Provide a "way out."** Anthropic's recommendation: give the judge the explicit option to return "Unknown" / "insufficient information." Reduces hallucinated confidence directly; trivially deployable.

### Partially validated (deploy with caveat):

6. **Length controls.** AlpacaEval 2.0 length-controlled debiasing (arxiv 2404.04475): a linear regression mediator with length difference as covariate moved Chatbot-Arena Spearman from 0.94 → 0.98. But Judging the Judges (arxiv 2604.23178, 2026) found "no significant trend between prompt/response lengths and bias metrics after controlling for quality gap." So: length bias is real but smaller than commonly stated; the AlpacaEval-style regression is cheap insurance, but length-normalization-in-the-rubric is theatrical (it just teaches the judge to obey a new instruction without solving the bias).

### Mostly theatrical (skip):

7. **Prose tightening to widen σ on small N.** The Krippendorff α<0.8 result (Rating Roulette, arxiv 2510.27106) and our own `2ce99bb` empirical observation both say the per-draft noise floor is inherent. Spending tokens on tighter rubric prose past a basic anchor cannot break the floor. The Empirical Study (arxiv 2506.13639) found CoT additions yielded "minimal gains when clear evaluation criteria exist." This is the trap we've already correctly identified.
8. **Anti-gaming clauses.** "Do not be biased toward longer outputs" types of negative instructions. No production paper validates these meaningfully reducing the biases they name; they primarily perturb the score distribution without changing rank order. Theatrical.
9. **Score-scale broadening from 0/0.5/1 to 1–10 because "wider scales widen σ."** This *does* reduce score-comparison inconsistency per TrustJudge (5→100 scale helps). But the published gain is on inconsistency-rate, not on rank-stability for variant promotion. Given our N=5–30 and our small evolution-loop selection step, the central-tendency-bias literature actively warns *against* broad scales. **0/0.5/1 with behavioral anchors is the right structure for our N.**

---

## 5. Failure modes at small N (5–30)

This is the section the literature is thinnest on, because most published judge benchmarks operate at N=200–10,000. The findings that do exist:

- **Sample-size sensitivity:** "Misjudging sample sizes can shift performance metrics by up to 10% and rankings by 5 positions" in LLM eval contexts, particularly when LLM-output correlations violate the standard independence assumptions (Latitude blog 2025, citing internal benchmarks). For N=5–30 with non-independent variant lineages, this is essentially saying: rank instability is the default, not the exception.
- **Statistical power baseline:** From general power-analysis literature (Lakens 2022; Statistics by Jim) — for an effect of d=0.5 (a reasonable "real improvement" effect), N=10 gives ~24% power, N=30 gives ~49% power at α=0.05. **Below ~64 samples you cannot detect a "medium" effect even with a perfect noiseless measurement.** Our judge is not noiseless. So statistical detection of true variant improvements at our N is implausible regardless of judge methodology.
- **AI2 Signal-to-Noise framework (Allen Institute, 2025):** Provides the cleanest small-N framing — define signal as max score-dispersion across distinct quality levels, noise as σ across re-runs at one quality level. SNR predicted decision accuracy R²=0.626 and scaling-law-prediction R²=0.471 across many benchmarks. **Their concrete advice for low-N benchmarks: prefer fewer high-SNR sub-tasks over many low-SNR ones.** For us this maps cleanly: a 0/0.5/1 score on 5 strong fixtures with high-SNR criteria beats a 5-point Likert on 30 mediocre fixtures. The AI2 MMLU example — 16 of 57 subtasks beat the full 57-subtask set — is directly relevant; this is the "evaluate-fewer-better-things" pattern.
- **Hopkins et al. 2026 "Noisy but Valid":** Provides Type-I error bounds that grow as the calibration set shrinks. For N=5–30 with calibration of 30–50, the corrected bound is loose but valid. The framework's value at our N is *honest uncertainty quantification* — we know we can't reject the null tightly, but we can know exactly how loose the rejection is.

### Bottom line at N=5–30

**Single-judge absolute-gradient scoring at our N produces ranks that are stable enough for "is the variant catastrophically worse" (the floor decision) and unstable for "is the variant marginally better" (the ceiling decision).** The literature is unanimous that single-shot single-judge at small N cannot reliably identify small improvements. The promotion gate has to accept this: gate-out catastrophic regressions hard, gate-in marginal improvements conservatively (e.g., require multi-fixture coherent improvement, not single-fixture).

---

## 6. Production patterns from real deployments

What we can verify from public sources:

- **Anthropic (Constitutional AI arxiv 2212.08073; RLAIF; "Demystifying Evals for AI Agents" engineering post):** Uses constitution-based AI feedback for harmlessness training. For eval grading specifically, the production pattern they publish is: per-dimension *isolated* judges, each with structured rubrics, each calibrated against human experts, each maintained as a "living artifact" — and they re-read transcripts to catch unfair grading. Notable absence: no published "single magic prompt" — the recommendation is structural (per-dimension isolation), not prompt-text.
- **LMSYS Chatbot Arena (arxiv 2306.05685; Bradley-Terry transition 2024):** Pairwise crowd-sourced at volume. Bradley-Terry MLE for ranking, **not** single-pairwise verdicts. Confidence intervals reported. Has been demonstrated gameable by vote-rigging (arxiv 2501.17858, 2025) and overoptimized-for via prompt-style tuning (Llama 4 Maverick Elo-rating controversy, April 2025). The lesson: even at N=10⁵ pairwise comparisons, optimization pressure produces Goodhart effects.
- **OpenAI Evals (github.com/openai/evals + "Evaluation best practices" docs):** Model-graded evals are framed as a *tool*, not the primary scoring mechanism. OpenAI's published guidance: prefer programmatic graders where possible; use model graders for subjective dims; calibrate per-rubric; rate on small integer scales 1–4 or 1–5 with description. They warn against ungrounded model grading and explicitly recommend reasoning-before-score.
- **Hugging Face Evaluation Guidebook (huggingface.co/spaces/OpenEvals/evaluation-guidebook):** Three-way taxonomy — generalist LLMs, specialized judge models (Prometheus, JudgeLM), trained custom judges. Their production-pattern recommendation: small integer scales (1–4 / 1–5), structured output (JSON Evaluation + Total rating), and explicit Evaluation field before the rating. Aligns with G-Eval CoT-before-score finding.
- **Allen Institute / AI2 (signal-and-noise blog + arxiv 2501 paper):** Production-grade benchmark engineering — they advocate selecting subtasks for SNR, not coverage, for any decision context (model selection, scaling laws).
- **DeepMind AlphaEvolve / FunSearch:** The closest published precedent to our autoresearch loop. *Key difference*: AlphaEvolve uses **automated evaluators that verify correctness** (numerical/algorithmic correctness checks), not subjective LLM-as-judge for the inner gate. They use LLM-as-judge only for the *outer* program-quality dimension. This is a strong signal that for evolution loops the literature recommends *splitting* objective (verifiable) signal from subjective (LLM-judged) signal — not stacking everything into the same judge.

---

## 7. Evolution-loop-specific considerations

This is the section that distinguishes our problem from the bulk of LLM-judge literature, and where the most specific warnings exist:

- **Gao et al. 2022 (arxiv 2210.10760), "Scaling Laws for Reward Model Overoptimization":** *The* foundational paper. Optimizing against an imperfect proxy reward model **decreases ground-truth performance past a critical KL budget**, per Goodhart's Law. Functional form matches best-of-n sampling and RL differently. Direct relevance: each evolution generation is an optimization step against the judge proxy; the question is not *whether* Goodhart happens but *at which generation count*.
- **Pan et al. 2024 (arxiv 2402.06627), "Feedback Loops With Language Models Drive In-Context Reward Hacking":** Specifically about feedback loops where LLM output influences subsequent LLM-input distributions. **Two mechanisms documented: output-refinement (mutator games the judge through stylistic drift) and policy-refinement (the evolved population's distribution shifts the judge's effective decision boundary).** Their finding: scaling model size **worsens** ICRH; improving prompt specification is **insufficient** to eliminate it. Static eval datasets miss feedback effects — meaning evolution-loop pathology is invisible to one-shot eval.
- **AI Safety II review (synthesis.ai, May 2025):** Catalogs the Llama 4 Maverick Elo-rating controversy (Apr 2025) and the Stockfish-chess-shell-exploit example as concrete 2025 Goodhart manifestations. Their recommendation: assume reward hacking, design for it, monitor for it.
- **Zhang et al. 2025 (arxiv 2511.19489), "Evolution without an Oracle":** **The closest published study to our exact setup.** Drives evolution purely via subjective LLM evaluation. Their key finding: **decompose the high-noise eval into multiple low-noise sub-tasks**, then aggregate. They document four specific failure modes — judge inconsistency, reward hacking, computational cost, alignment drift — and recommend iterative filtering with threshold-gates rather than score-maximization. *Their decomposition pattern maps to our criterion-vector — we already do this. The validation is that it's necessary, not optional.*
- **AlphaEvolve / FunSearch precedent:** Uses **verifiable correctness checks as the inner gate**, LLM judgment only outer. This is the published-and-working pattern for evolution loops; subjective-judge-as-inner-gate is, in the literature, a known-fragile approach.

### Concrete warnings for our setup

1. **Selection pressure compounds Goodhart.** Each promoted variant biases future variant proposals toward whatever the judge happens to over-weight. By generation 5–10 this is non-negligible. *Detection*: monitor *what the judge weights* across generations, not just *what scores rise*.
2. **Judge prompts cannot stay frozen forever, but updating them invalidates lineage.** Any judge rewrite means old `scores.json` are not comparable to new ones. The Fiedler J/ΔJ analysis says this explicitly: shared-calibration assumptions break when judges drift. *Production posture*: version judges, mark which scores were generated by which judge version, and require a re-baseline run after any non-trivial judge change.
3. **Structural anti-gaming is more durable than rubric anti-gaming.** Per Pan et al. 2024 and AlphaEvolve's design: structural gates (artifact must include named entity X, must reference fixture-specific fact Y) compose better than rubric clauses ("avoid clichés"). Verifiable correctness checks > LLM-judged style clauses, where verifiable checks are achievable.
4. **Mode collapse.** Underdiscussed in the LLM-judge literature, well-documented in evolution-strategy literature. If the judge converges on a single high-scoring style, all variants drift toward it and within-population diversity collapses, after which the evolution loop has no exploration power. *Detection*: simple — track score variance across the population at each generation; if it drops to noise-floor for 2+ generations, you have mode collapse, not convergence.

---

## 8. What's hype vs validated

| Pattern | Status | Evidence |
|---|---|---|
| LLM-as-judge in general | **Validated, with caveats** | Zheng et al. 2023 (80%+ human agreement on chatbot tasks) — but chatbot ≠ long-form artifact |
| Single GPT-4-class judge for production scoring | **Hype** | Verga et al. 2024 — single GPT-4 underperformed a 3-model panel on every dataset tested |
| Panel of cheap diverse judges (PoLL) | **Strongly validated** | Cohen κ +13–15pts, σ from 6.1→2.2, 7–8× cheaper |
| Pairwise > pointwise universally | **Hype, contested** | Liusie et al. 2025 — 35% vs 9% flip under distractor attack favors pointwise; TrustJudge shows 23–37% disagreement between paradigms |
| Few-shot anchor examples (3+ per criterion) | **Mostly hype past extremes** | Empirical Design Choices 2025 — extreme-only anchors match full Likert anchors |
| Chain-of-thought-before-score | **Validated, modest** | G-Eval (Spearman 0.514); Empirical Design Choices ("minimal gains when clear evaluation criteria exist") |
| Sample-averaging multiple judge calls | **Strongly validated** | Empirical Design Choices — 0.635 → 0.666 correlation; Rating Roulette intra-rater inconsistency reduction |
| Cross-family judges to defeat self-preference | **Validated** | Li et al. 2025 (Preference Leakage) — 6–22% inflation, eliminated by family separation |
| Position-swap for pairwise | **Validated, necessary** | Zheng et al. 2023 — win-rate 2.5%→82.5% from position alone |
| Length-controlled debiasing | **Validated, modest** | AlpacaEval LC — Spearman 0.94→0.98; but 2026 "Judging the Judges" found length effects small after quality controls |
| Prose-tightening to widen σ on small N | **Theatrical** | Empirical Design Choices, our own `2ce99bb` finding — fundamental noise floor |
| Anti-gaming negative clauses in rubric | **Theatrical** | No production paper validates effect-size meaningful |
| Broad scoring scales (1–100) "for resolution" | **Pattern-dependent** | TrustJudge — helps inconsistency rate; central-tendency-bias literature — hurts at small N |
| Static rubric across many generations of evolution | **Hype / dangerous** | Pan et al. 2024 ICRH — feedback loops invalidate static evals |
| Subjective-LLM-judge as inner gate in evolution loop | **Documented fragile** | Zhang et al. 2025; AlphaEvolve uses verifiable inner gate by design |
| Calibration set sizes <30 | **Hype** | Hopkins et al. 2026 framework — bounds degrade rapidly below n_M=25; 50 is the converged industry number |

---

## 9. Recommendation for our autoresearch evolution loop

The judge-design RESET handoff (`docs/handoffs/2026-05-15-judge-design-reset-and-plan.md`) already commits us to domain research per lane + literature methodology research (this document). The evidence above supports a **targeted three-piece intervention**, not a paradigm rewrite:

### Piece 1 — Keep absolute scoring as the digest/lineage scorer; add pairwise as the *promotion gate* primitive

- Variant V vs current C: ask judge "which is better and why" with position-swap. Promote only if both orderings agree V > C.
- Cost: +1 judge call per generation (the second ordering). Acceptable.
- Why: §1 evidence — pairwise is the high-signal primitive for a single-decision use case; absolute remains the right primitive for cross-lineage comparability.
- Does not invalidate any existing archived `scores.json`. The pairwise gate is *additive*.

### Piece 2 — Adopt the cheap-diverse panel pattern (PoLL) for the absolute scorer where stack supports it

- We already have opus + codex. Add one cheap third (Haiku or Gemini 2.5 Flash) for the absolute-score panel — average over the three.
- Per Verga et al. 2024, this should drop σ and improve human-correlation simultaneously. Cost is *lower* than current claude-opus-only, not higher, because the third judge is cheap.
- Cross-family requirement (Li et al. 2025) is automatically satisfied by Anthropic + OpenAI + Google split.
- Where stack does not support all three (geo's gpt-5.5 cybersecurity filter — see `project-geo-regression-root-cause-2026-05-12`), retain the two-judge fallback rather than blocking on three-judge availability.

### Piece 3 — Build the 30–50-label per-lane calibration set + drift-detection protocol

- Per §3: JR labels 30 in one sitting per lane. Score 0/0.5/1. Single-sitting is non-negotiable.
- After each rubric edit OR meta-agent mutation that touches a judge prompt, re-score the calibration set. Any single-label flip pauses promotion until explained.
- Track Cohen κ vs JR labels per judge version. This becomes our equivalent of Fiedler's J — when κ drops below the previous version, we know the judge regressed.
- This is the most labor-intensive piece but **the only piece that establishes ground truth.** Without it, the other two pieces are unverified.

### Explicit non-changes (DO-NOTs grounded in literature)

- **Do not** rewrite rubric prose to widen σ on small N. (Empirical Design Choices 2025; our own `2ce99bb`.)
- **Do not** broaden 0/0.5/1 to a 5-point or 10-point Likert. (Central tendency bias literature; AI2 SNR argues for fewer-better criteria, not more-resolution per criterion.)
- **Do not** dump 3+ exemplar artifacts per criterion into the prompt. (Empirical Design Choices — diminishing returns past extreme anchors; preference-leakage exposure.)
- **Do not** assume a static rubric is safe across many evolution generations. (Pan et al. 2024 ICRH.) Re-validate calibration at version boundaries.
- **Do not** trust any single absolute score for promotion. The pairwise gate (Piece 1) is the actual decision; the absolute score is the archived lineage measurement.

### Sequencing

These three pieces are independent and parallel-safe. Cheapest-first ordering: Piece 2 (panel) is config + one prompt change; Piece 1 (pairwise gate) is one new judge prompt + the promotion-gate logic; Piece 3 (calibration set) is JR-labor-bound and gates Piece 1's pairwise-gate from being trusted but does not gate it from being deployed. Recommended ship order: 2 → 1 → 3, with 3 unblocking Piece 1's confidence.

---

## 10. Sources cited

### Foundational LLM-as-judge

- Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," NeurIPS 2023 — https://arxiv.org/abs/2306.05685
- Liu et al. 2023, "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment" — https://arxiv.org/abs/2303.16634
- Wang et al. 2023, "PandaLM" — https://arxiv.org/abs/2306.05087
- Kim et al. 2024, "Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models" — https://arxiv.org/abs/2405.01535

### Pairwise vs absolute / inconsistencies

- Liusie et al. 2025, "Pairwise or Pointwise? Evaluating Feedback Protocols for Bias in LLM-Based Evaluation," COLM 2025 — https://arxiv.org/abs/2504.14716
- Wang et al. 2025, "TrustJudge: Inconsistencies of LLM-as-a-Judge and How to Alleviate Them," ICLR 2026 — https://arxiv.org/abs/2509.21117
- Haldar & Hockenmaier 2025, "Rating Roulette: Self-Inconsistency in LLM-As-A-Judge Frameworks," Findings of EMNLP 2025 — https://arxiv.org/abs/2510.27106

### Bias / calibration / reliability

- Li et al. 2025, "Preference Leakage: A Contamination Problem in LLM-as-a-judge" — https://arxiv.org/abs/2502.01534
- Weng et al. 2026, "Beyond Accuracy: Policy Invariance as a Reliability Test for LLM Safety Judges" — https://arxiv.org/abs/2605.06161
- Fiedler 2026 (Indeed), "Bias and Uncertainty in LLM-as-a-Judge Estimation" — https://arxiv.org/abs/2605.06939
- Empirical Study of Design Choices 2025 — https://arxiv.org/abs/2506.13639
- Hopkins et al. 2026, "Noisy but Valid: Robust Statistical Evaluation of LLMs with Imperfect Judges" — https://arxiv.org/abs/2601.20913
- Evaluating Scoring Bias in LLM-as-a-Judge 2025 — https://arxiv.org/abs/2506.22316
- Judging the Judges: A Systematic Evaluation of Bias Mitigation Strategies 2026 — https://arxiv.org/abs/2604.23178
- Grading Scale Impact on LLM-as-a-Judge 2026 — https://arxiv.org/abs/2601.03444
- Play Favorites: A Statistical Method to Measure Self-Bias 2025 — https://arxiv.org/abs/2508.06709
- AlpacaEval Length-Controlled 2024 — https://arxiv.org/abs/2404.04475

### Panels / ensembles / meta-judges

- Verga et al. 2024, "Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models" — https://arxiv.org/abs/2404.18796
- Auto-Prompt Ensemble for LLM Judge 2025 — https://arxiv.org/abs/2510.06538

### Reward hacking / Goodhart / evolution

- Gao et al. 2022, "Scaling Laws for Reward Model Overoptimization" — https://arxiv.org/abs/2210.10760
- Pan et al. 2024 (ICML), "Feedback Loops With Language Models Drive In-Context Reward Hacking" — https://arxiv.org/abs/2402.06627
- Zhang et al. 2025, "Evolution without an Oracle: Driving Effective Evolution with LLM Judges" — https://arxiv.org/abs/2511.19489
- AlphaEvolve technical report, DeepMind 2025 — https://arxiv.org/abs/2506.13131

### Constitutional AI / RLAIF

- Bai et al. 2022, "Constitutional AI: Harmlessness from AI Feedback" — https://arxiv.org/abs/2212.08073

### Production patterns / industry posts

- Anthropic Engineering, "Demystifying Evals for AI Agents" — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- LMSYS Chatbot Arena (Bradley-Terry transition) — https://arxiv.org/abs/2403.04132
- OpenAI Evals — https://github.com/openai/evals + https://developers.openai.com/api/docs/guides/evaluation-best-practices
- AI2 Signal and Noise — https://allenai.org/blog/signal-noise
- Hugging Face Evaluation Guidebook — https://huggingface.co/spaces/OpenEvals/evaluation-guidebook
- Eugene Yan, "Evaluating the Effectiveness of LLM-Evaluators (aka LLM-as-Judge)" — https://eugeneyan.com/writing/llm-evaluators/
- Cameron R. Wolfe, "Using LLMs for Evaluation" — https://cameronrwolfe.substack.com/p/llm-as-a-judge
- Evidently AI LLM-as-a-judge guide — https://www.evidentlyai.com/llm-guide/llm-as-a-judge

### Surveys

- "LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods" — https://arxiv.org/abs/2412.05579
- "A Survey on LLM-as-a-Judge" — https://arxiv.org/abs/2411.15594

---

## Cross-references

- Parent handoff: `docs/handoffs/2026-05-15-judge-design-reset-and-plan.md`
- Companion domain research: `docs/research/2026-05-15-judges-domain-geo.md` (and per-lane successors)
- Empirical noise-floor finding: commit `2ce99bb` 2026-05-08 (J1–J4 prose-tightening revert)
- Geo regression root cause (cross-family fallback rationale): memory `project-geo-regression-root-cause-2026-05-12`
