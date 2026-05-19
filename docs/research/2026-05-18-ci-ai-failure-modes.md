---
date: 2026-05-18
type: research deliverable
status: complete
topic: LLM-specific CI failure modes (distinct from human-CI failures)
parent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# LLM-Specific Failure Modes in Competitive-Intelligence Generation

Companion to `docs/research/2026-05-15-judges-domain-competitive.md` (human-CI failure modes) and to the locked v2 spec at `docs/handoffs/2026-05-17-judge-design-step1-competitive.md`. The human-CI literature gets the *quality ceiling* right — what an excellent brief looks like. But it was written before LLMs were the primary author, and it does not catch the failure modes that show up when an LLM produces the brief instead of an analyst. This deliverable catalogues those LLM-specific failures, walks the current 5 criteria against them, and recommends where AI-failure detection should live in the pipeline.

---

## TL;DR (300 words)

The CI v2 spec (CI-1 action / CI-2 trajectory / CI-3 mechanism / CI-4 uncomfortable truth / CI-5 trade-off) is sharp on *strategic quality* but silent on three LLM-specific failure modes that human analysts almost never produce — and that named production systems hallucinate at measurable, double-digit rates.

The three failure modes the spec does not catch:

1. **Source confabulation** — the brief cites URLs, analyst reports, executive quotes, or "internal data" that do not exist. Documented rate: 19.9% of GPT-4o citations in literature reviews are entirely fabricated (Chelli et al. 2024 / 2025 follow-ups); 37% of Perplexity citations in one benchmark contain real URLs with fabricated attributed claims. CI v2 has no criterion or gate that fails a brief for a non-existent source.
2. **Entity / move confabulation** — the brief names a competitor, executive, board seat, customer, product launch, or M&A event that does not exist or is mis-attributed. HalluLens / HalluEntity / KGHaluBench report context-free entity hallucination rates of 14–95% across 13 models × 40 domains; "Cursor the IDE" vs "Cursor the cursor-tracker" conflations are the modal failure shape. Structural_gate currently checks shape, not entity existence.
3. **Confident strategic claim without a reasoning chain** — the brief asserts "Acme is moving up-market" or "this is a counter-positioning play" in confident analytic prose, but the chain of evidence collapses when traced. This is the LLM analogue of human single-hypothesis bias, except the LLM does not *have* a hypothesis — it generates plausible-sounding strategic language. Sycophancy + CoT-rationalization literature (BrokenMath; "Good Arguments Against the People Pleasers" 2026) shows reasoning traces increase rather than decrease this problem.

**Recommendation: structural_gate is the right home for #1 and #2; the judge is the right home for #3.** Add a deterministic citation-and-entity-existence verifier to `_validate_competitive()` (URL HEAD checks, entity-against-allowlist or Wikidata, fabricated-quote detection via grep-and-verify). Add one new judge criterion CI-6 "evidence chain survives tracing" specifically targeting confident-without-substance. One CI v2 spec edit: add CI-6, and add a "Goodhart-resistance" note to §6 covering source-confabulation gaming.

---

## 1. Q1 — Entity hallucination and confabulation (~380 words)

**The failure mode.** LLMs invent competitor names, products, executive names, board seats, customer logos, and org-structure details that do not exist. Three sub-shapes show up in CI specifically:

- **Pure invention.** A competitor "Acme Strategy Partners" appears in the brief; no such firm exists.
- **Similar-name conflation.** "Cursor" (the Anysphere IDE) gets blended with "Cursor" (an older cursor-tracking analytics tool). "Anthropic" gets blended with a non-existent "Anthropic Communications" or "Anthropic Research Foundation."
- **Real-entity attribute fabrication.** The competitor exists; the brief invents that they hired a named CRO, lost a named customer, or sit on a specific board.

**Documented rates.** HalluLens (Bang et al., arxiv 2504.17550) explicitly tests *Nonsense* — non-existent entity handling — alongside long-form generation and PreciseQA. HalluEntity (arxiv 2502.11948) provides 18,785 entity-level annotations for ChatGPT biographies; entity-level hallucination rates are domain-dependent and frequently exceed sentence-level detection thresholds. KGHaluBench (arxiv 2602.19643) and GhostCite report entity-existence hallucination rates of 14–95% across 13 LLMs × 40 domains. Closer to the CI use case: the FinanceBench / FAITH benchmark (arxiv 2508.05201) explicitly tests fabricated financial-entity statements; intrinsic hallucination rates in finance are high enough that a December 2025 paper ("Detecting AI Hallucinations in Finance," arxiv 2512.03107) reports an information-theoretic detector cutting them by 92%.

**Production retrospectives.** Sports Illustrated 2023 (fake AI-generated author biographies with fabricated photos); Apple News withdrew the LLM-summary feature in early 2025 after fabricated event details; Deloitte refunded part of a $290K Australian-government report in 2025 after LLM-generated content contained hallucinated entities and citations. None of these are CI specifically, but the failure shape transfers directly.

**Detection / mitigation patterns that work.**
- **Entity allowlist.** For a known target market, run named-entity-recognition over the brief and reject any competitor / product / person not on the input fixture's allowlist.
- **Wikidata / Crunchbase / SEC EDGAR lookup.** Cheap, deterministic, catches pure invention.
- **Similar-name disambiguation.** When two entities share a name token, require a disambiguating attribute (URL, founder, founding year) in the brief.
- **Source-grounded generation.** RAG with an explicit source-attribution requirement, then verify each named entity appears in at least one retrieved source (Lewis et al. follow-ups; FinDER arxiv 2504.15800).

**Why human-CI literature does not catch this.** Analysts know who the named competitors are; they do not invent companies. The failure mode is LLM-specific.

---

## 2. Q2 — Hallucinated competitive moves (~390 words)

**The failure mode.** LLMs invent plausible-sounding competitor moves: product launches that did not happen, pricing changes that were not announced, M&A activity, partnership announcements, earnings-call language, customer wins. The shape is dangerous specifically because the *category* of move is plausible (Acme is the kind of company that would launch this), the *timing* is plausible (Q3 launches are common), and the *details* sound like real press-release language. Three named sub-shapes:

- **"Reportedly" / "according to" framing without a real source.** "Acme is reportedly preparing a Q3 EU expansion" — no underlying source, but the hedge ("reportedly") manufactures epistemic comfort.
- **Fabricated press-release excerpts.** A direct or paraphrased quote attributed to a named exec; the exec exists, the quote does not.
- **Plausible earnings-call paraphrase.** "Their Q3 earnings emphasized cost discipline three times" — neither verifiable nor verifiable-as-false from the brief, but the LLM did not actually read the earnings call.

**Documented rates and retrospectives.** Bloomberg's deficiency study (arxiv 2311.15548 — pre-2024 but still the canonical financial-LLM hallucination paper) documents *fabricated financial news* as a distinct category, with the canonical example being "an LLM incorrectly reporting that a non-existent company missed its quarterly earnings target based on a non-existent press release." BloombergGPT itself was explicitly designed with grounded summarization to mitigate this, but the 2025 Bloomberg AI Summaries rollout retrospective notes that "no one has really solved the hallucination problem." The FactSet 2025 adoption study (replicated in arxiv 2512.19705 "Generative AI for Analysts") found that AI-assisted equity research reports have **59% higher forecast errors** than analyst-only reports — not because the LLM invented obvious falsehoods, but because the breadth of information surfaced included un-vetted plausible-sounding signal.

**Production retrospectives.** Apple Intelligence withdrew its news-summary feature in early 2025 after a BBC retrospective documented fabricated event details (a named shooter, a named verdict, an attributed quote) attached to real news stories. CB Insights and Crayon's "Sparks" AI feature (Crayon 2026 launch) are explicit that human-analyst review remains in the loop precisely because the move-summarization step is unreliable.

**Detection / mitigation patterns.**
- **Source-grounded date-stamped retrieval.** Every named move must trace to a retrieved source dated after the event.
- **Forbidden weasel-word list.** "Reportedly," "according to industry sources," "in a recent statement" without a citation = structural failure.
- **Quote-verification grep.** Direct or near-verbatim quotes must appear in at least one retrieved source (string-similarity > 0.85).
- **Move-claim ledger.** Each claimed competitive move gets logged with claimed-date + claimed-source; a post-generation pass checks both.

**Why human-CI literature does not catch this.** Klue's 7 mistakes, Heuer's biases, McKinsey's competitor-neglect all assume the analyst is *under-investigating* real moves, not *fabricating* plausible ones. The LLM failure mode is generative, not investigative.

---

## 3. Q3 — Plausible strategic claims without underlying analysis (~400 words)

**The failure mode.** LLMs assert "Acme is moving up-market," "this is a counter-positioning play," "their advantage is process power" — the prose sounds like a competent strategy memo, but the chain of evidence collapses under scrutiny. Three sub-shapes:

- **Strategic verb without object.** "Acme is doubling down on enterprise" — what defines doubling-down here? What would falsify the claim?
- **Framework name without mechanism.** "This is a counter-positioning play" — Helmer's specific structural test (incumbent can't replicate because of cannibalization economics) is asserted by name only, not by mechanism. This is the exact failure mode the v2 spec §3b catalogues as "Helmer-power name-drops" — but §3b frames it as Goodhart collapse from evolution, not as a *baseline* LLM tendency that shows up even pre-evolution.
- **Confident-tone synthesis.** Three plausible-sounding paragraphs that read as analysis but cannot be traced back to a specific evidence chain. Sycophancy and CoT-rationalization research (BrokenMath, arxiv 2510.04721; "Good Arguments Against the People Pleasers," arxiv 2603.16643) show that LLMs reliably produce "rigorous-sounding but biased justifications" when given even mild user-direction cues — and competitive briefs are commissioned with an implicit direction (the requester wants strategic insight).

**Why this is distinct from human single-hypothesis bias.** The human analyst with confirmation bias *has* a hypothesis they are confirming. The LLM does not have a hypothesis; it generates plausible strategic language from the latent space of strategy-memo writing. The output looks identical at first read; the difference shows up when you ask "what would falsify this claim?" — the human can usually answer, the LLM often cannot because the claim was never grounded in a falsifiable proposition.

**Documented evidence.**
- Sycophancy + CoT literature: LLMs sacrifice factual accuracy "to cater to the user's perceived beliefs or preferences" (Wei et al. 2023 follow-ups; "Good Arguments Against the People Pleasers" 2026); CoT *masks* this rather than mitigating it, because the rationale gets generated to defend the conclusion.
- Eidoku (arxiv 2512.20664) reframes the problem: "LLMs frequently produce hallucinated statements assigned high likelihood by the model itself, suggesting hallucination is often a failure of structural consistency rather than low-confidence." High confidence does not correlate with correctness on strategic claims.
- FactSet 2025 retrospective: AI-assisted reports were judged as having *more comprehensive coverage* (richer language, more sources cited) but *59% higher forecast error* — the analytic gloss outran the analytic substance.

**Detection / mitigation patterns.** Forced multi-hypothesis prompting; explicit "what would falsify this?" prompt; chain-of-thought *with* a verifier that traces each strategic claim back to its source; the v2 spec's CI-3 "structural mechanism" criterion catches this partially — but only for the *advantage*-shaped claims, not the *trajectory* or *positioning* claims.

---

## 4. Q4 — Recency bias and training-cutoff distortion (~340 words)

**The failure mode.** The LLM projects the competitive landscape of its training cutoff into the present. "Recent" launches are 6–18 months old; competitive shifts that happened after training cutoff are invisible. For a May 2026 brief: the LLM might frame the AI-agent platform market as it stood in mid-2024 (the OpenAI assistants-API era), missing the 2025–2026 shifts in agent-platform consolidation, the regulatory shifts post-EU-AI-Act phase-2, and the post-ChatGPT enterprise market settling.

**Documented evidence.**
- **LLMLagBench** (arxiv 2511.12116, late 2025) — benchmark that "empirically identifies temporal knowledge boundaries in LLMs through systematic evaluation." Key finding: "several LLMs exhibit multiple partial cutoff points, possibly corresponding to distinct training stages, and training cutoffs often diverge significantly from release dates." A model released in Feb 2026 might have a *behavioral* cutoff of Oct 2024 for finance-domain facts.
- **ProofTeller** (aclanthology 2025.ijcnlp-long.80) explicitly documents recency bias in LLM reasoning — the model overweights training-distribution recent events.
- **Temporal QA accuracy degradation** (NAACL 2025 "Is Your LLM Outdated?"): accuracy drops 23–35% when shifting from "in 2020" to "4 years ago"; LLMs reason about absolute dates better than relative ones, and most CI briefs use relative framing.
- **Recency bias in reranking** (arxiv 2509.11353): LLM-based reranking favors more recently dated content within the retrieved set — which means RAG mitigates training-cutoff bias only partly, because the reranker overweights the most-recent retrieved doc rather than the most-*relevant* one.

**Specific 2024 → 2026 shifts a CI brief would miss.** Post-ChatGPT enterprise market settling (the "we'll just use OpenAI" assumption broke in 2025 with Anthropic enterprise wins); AI-agent platform consolidation (LangChain, CrewAI, AutoGen positions shifted significantly 2025–2026); EU AI Act phase-2 compliance shifts (Aug 2025 enforcement); post-rate-hike SaaS pricing realignment.

**Mitigations.**
- **Date-stamped retrieval** — every retrieved source carries a date; brief must cite ≥1 source from within the last 90 days for each forward-looking claim.
- **"As of [date]" framing requirement** — the brief must declare the effective-as-of date, and any claim sourced from training data must be flagged "(from training, ≤[cutoff])".
- **Forced post-cutoff probing** — the workflow includes a step that asks the LLM "what would have changed in this market in the last 6 months that you might not know about?" — surfacing the temporal blind spot rather than papering over it.

**Why human-CI literature does not catch this.** Analysts know what year it is. The failure mode is LLM-specific.

---

## 5. Q5 — Source confabulation (~390 words)

**The failure mode, with sub-shapes.**

- **Non-existent URL.** A footnote points to `https://acme.com/press/2025/q3-earnings` — 404, never existed.
- **Real URL, wrong content.** The footnote points to a real Acme press page, but the claim attributed to it ("they announced 40% EMEA growth") is not in that page. This is Perplexity's specific failure profile.
- **Plausible-but-non-existent paper.** "(Chen et al., 2024)" — neither Chen nor the paper exist, but the citation looks real.
- **Misattributed quote.** A quote that exists, but spoken by someone else, in a different context, in a different year.
- **Invented "internal data" or "industry research."** "Our analysis of industry data shows…" — no analysis was conducted; the language manufactures epistemic authority.

**Documented rates — strong signal.**

- **GPT-4o literature reviews: 19.9% of citations entirely fabricated** (Chelli et al., 2025 mental-health-research study, EurekAlert 2025).
- **Computer-science reference titles: 47% (GPT-4) → 77% (Llama 2 7B) hallucinated** (Chen et al. follow-ups, surveyed in GhostCite).
- **Citation-existence rates of 40–50% for LLM-generated references** (Structural Hallucination paper, arxiv 2603.01341); "90% of valid references fall among the top 10% most-cited papers" — popularity bias in citation generation.
- **Web-search-grounded models still hallucinate 3–13% of URLs** (Detecting and Correcting Reference Hallucinations, arxiv 2604.03173) — RAG mitigates but does not eliminate.
- **OpenAI Deep Research citation accuracy: 78%. Perplexity: 37% hallucination on citation tasks** (Deep Research Agent retrospectives, 2025). Claude with search: 94% (best of the named commercial systems). Best academic system: 65% citation quality / 68% factual accuracy.
- **NeurIPS 2025 incident: 100 AI-generated hallucinated citations in 53 published papers** (~1% of accepted papers, despite 3–5 expert reviewers per paper) — taxonomy: Total Fabrication 66%, Partial Attribute Corruption 27%, Identifier Hijacking 4% (arxiv 2602.05930).

**Production-system specifics that matter for CI.** Perplexity's failure is the most dangerous shape for CI specifically: the URL is real, the cited entity is real, the quoted exec is real — and the *attributed claim* is fabricated. A human reviewer who clicks the URL sees a real Acme press page and trusts the citation; only a careful read reveals the claim is not in the page.

**Detection / mitigation patterns.**
- **URL HEAD-check** for every footnote (cheap, deterministic, catches non-existent URLs).
- **Quote-string-match against retrieved corpus** — any direct quote (string in `""`) must match a retrieved source with cosine similarity > 0.85.
- **Citation-existence check via DOI / arxiv / SEC-EDGAR lookup** for papers and filings.
- **"Internal data" / "industry research" pattern grep** — these phrases without a named primary source are structural failures.
- **Source-grounded generation with mandatory attribution at sentence level** (FinDER arxiv 2504.15800; FinRAGBench-V arxiv 2505.17471).

---

## 6. Q6 — Confidence without calibrated uncertainty (~360 words)

**The failure mode.** The LLM asserts "Acme will likely launch in Q3" or "this is the dominant retention risk" without a hedge, scenario branch, or flagged unknown. Distinct from human single-hypothesis bias: the human analyst with high confidence has usually considered alternatives and chosen one; the LLM did not consider alternatives because it does not reason about them — it generates the most-likely next token under the strategy-memo language model.

**The CoT-makes-it-worse trap.** Forcing chain-of-thought reasoning often *increases* this failure mode rather than decreasing it. The "Good Arguments Against the People Pleasers" paper (arxiv 2603.16643) and BrokenMath (arxiv 2510.04721) both find that CoT lets the model generate rigorous-sounding justifications *for the wrong answer* — the reasoning trace defends the conclusion rather than producing it. For CI specifically: the LLM commits to a strategic claim, then generates a confident reasoning chain that survives surface scrutiny but rests on the original unvetted commitment.

**Documented evidence.**
- **TrustJudge** (arxiv 2509.21117, not 2510.27106 as the prompt suggested — confirming actual arxiv ID): identifies *Score-Comparison Inconsistency* and *Pairwise Transitivity Inconsistency* in LLM-as-judge frameworks. Uses distribution-sensitive scoring + perplexity-based confidence to capture uncertainty that discrete scoring discards.
- **Uncertainty Quantification Survey** (arxiv 2503.15850, KDD 2025): "LLMs introduce unique uncertainty sources, such as input ambiguity, reasoning path divergence, and decoding stochasticity, that extend beyond classical aleatoric and epistemic uncertainty." Token-level entropy + multiple-sample consistency are the dominant approaches.
- **Anthropomimetic Uncertainty** (arxiv 2507.10587): verbalized uncertainty in LLMs is poorly calibrated — models say "I'm not sure" in patterns that do not track their actual reliability.
- **Eidoku** (arxiv 2512.20664): hallucination is "often a failure of structural consistency rather than low-confidence" — the model is structurally confident even when wrong.

**Why human-CI literature does not catch this.** Heuer & Pherson's Analysis of Competing Hypotheses (ACH) *does* address this in the human case — the discipline forces enumeration of alternatives. But ACH in an LLM-generated brief is the v2 spec's named pathology (§3b "ACH alternative-hypothesis strawmen") — the LLM mimics the section structure without performing the disconfirmation.

**Mitigations.**
- **Forced multi-hypothesis prompting** — the brief must enumerate ≥2 hypotheses for each major strategic claim, with disconfirming evidence engaged for the rejected one.
- **Inverse-confidence calibration** — verbalized confidence ("high"/"medium"/"low") calibrated against retrieval-grounding (high requires ≥3 independent sources).
- **Sample-consistency check** — generate the same brief 3× with different seeds; flag any strategic claim that does not appear in all 3 as "low-confidence."
- **Explicit unknowns section** — the brief must surface ≥1 named open question the reader should commission as follow-up intel.

---

## 7. Cross-cutting — what CI v2 catches vs misses (~430 words)

Walk each criterion against the 6 failure modes:

| Criterion | Q1 Entity | Q2 Moves | Q3 Plausible-strategic | Q4 Recency | Q5 Source | Q6 Confidence |
|---|---|---|---|---|---|---|
| CI-1 action | partial | partial | NO | NO | NO | NO |
| CI-2 trajectory | NO | partial | NO | weak partial | NO | partial |
| CI-3 mechanism | NO | NO | YES (for advantage claims) | NO | NO | NO |
| CI-4 uncomfortable | NO | NO | partial | NO | NO | NO |
| CI-5 trade-off | NO | NO | partial (forces cost-naming) | NO | NO | NO |

**What CI v2 actually catches:**

- **Q3 partial (plausible-strategic claims):** CI-3 ("structural mechanism of advantage") forces the brief to identify the structural reason a competitor can't or won't replicate. This catches Helmer name-drops *for advantage claims* — but it does not catch plausible-strategic claims about *trajectory* (CI-2 requires only 2+ signals, not signal-quality verification), *positioning* (not directly tested), or *recommendation rationale* (CI-1 tests for concreteness, not evidence chain).
- **Q2 partial (hallucinated moves):** CI-2 requires 2+ independent signals for a trajectory claim. A fully fabricated move would have to survive the signal-naming test — but the LLM can fabricate the signals too. Partial mitigation.
- **Q1 partial (entity confabulation):** CI-1 requires a "specific target" (named competitor / category / initiative / person / role / question). A judge that knows the fixture's allowlist *might* catch invented entities — but the rubric does not instruct the judge to verify entity existence, and the judge does not have the allowlist.

**What CI v2 does not catch at all:**

- **Q5 source confabulation:** Zero coverage. Structural_gate (`_validate_competitive` in `src/evaluation/structural.py`) checks brief exists + at least one `competitors/*.json` parses. No URL check, no citation verification, no quote grep.
- **Q4 recency / training-cutoff distortion:** Zero coverage. No "as of" date required, no recency window on cited sources, no post-cutoff probing.
- **Q6 confidence without calibration:** Zero coverage. The 0.5=unknown design forces the *judge* to express uncertainty, but it does not force the *brief* to express calibrated uncertainty. The brief can confidently assert "Acme will launch in Q3" and CI-1 would score it 1 if the action is concrete.
- **Q1 entity confabulation:** No direct coverage. The judge would have to *happen to know* the entities are real.
- **Q2 hallucinated moves:** Indirect partial coverage only. CI-2 catches "1 signal restated 3 ways" but not "3 fabricated independent signals."

**The asymmetric risk.** A brief that hallucinates a competitor, fabricates a press-release excerpt, and cites a non-existent analyst report can score *high* under v2 — it would name a concrete action (CI-1=1), reference multiple signals (CI-2=1), name a mechanism (CI-3=1), challenge a prior (CI-4=1), and pair the bet with a trade-off (CI-5=1). Perfect 5/5. Strategically empty. This is the architectural gap.

---

## 8. Recommendation — where should AI-failure-mode detection live? (~340 words)

**Three plausible homes:**

1. **In the judge** as new criteria.
2. **In structural_gate** as deterministic checks.
3. **In the workflow** as post-generation verification steps.
4. **In a new "AI-slop gate"** sibling to structural_gate.

**Recommended split — by failure mode:**

| Failure mode | Best home | Why |
|---|---|---|
| Q1 Entity confabulation | structural_gate | Deterministic (allowlist lookup, NER + Wikidata). Cheap. Binary pass/fail. Wrong fit for a judge that is supposed to score quality. |
| Q2 Hallucinated moves | structural_gate + workflow | Deterministic part = quote-grep + URL HEAD-check. Workflow part = source-grounded retrieval requirement at generation time. |
| Q3 Plausible-strategic claims | judge (new criterion CI-6) | Requires semantic reasoning about evidence chain. Cannot be done deterministically. |
| Q4 Recency / cutoff | structural_gate + workflow | Deterministic part = "as of" date present + ≥1 cited source within 90 days for each forward claim. Workflow part = retrieval with date-filter. |
| Q5 Source confabulation | structural_gate | URL HEAD-check, DOI/arxiv lookup, quote-grep — all deterministic. |
| Q6 Confidence calibration | judge (extends CI-2 + CI-3) + workflow | Judge can test "are alternatives engaged?" Workflow can do sample-consistency. |

**Why I would not put any of these directly in a new "AI-slop gate":** the failure modes split cleanly into "deterministic + cheap" (Q1, Q2-part, Q4-part, Q5) and "semantic + judge-shaped" (Q3, Q6). The cheap deterministic checks belong in structural_gate (existing infrastructure, existing pass/fail contract, runs before the judge anyway). The semantic checks belong in the judge prose (where evidence-chain reasoning is already what the judge does). A new gate would be an architectural duplicate.

**Why this is consistent with the existing pipeline.** Per `src/evaluation/service.py:148`, the pipeline already runs `structural → judge → aggregate → persist`. Adding citation-and-entity-existence verifiers to `_validate_competitive` is the natural extension point — the structural module is documented as "Free, deterministic, fast" and Layer 2 of the evaluation pipeline. The new judge criterion lives in the existing judge surface alongside CI-1 through CI-5.

**Why not "just trust the workflow to not hallucinate."** Documented rates above. Even Claude with search hallucinates 6% of URLs; even Perplexity Deep Research cites real URLs with fabricated claims 37% of the time. Workflow-side mitigation reduces but does not eliminate; verification on the eval side is the backstop.

---

## 9. Concrete edits to CI v2 spec (~250 words)

**Edit 1 — Add CI-6 (judge criterion).**

```
### CI-6 — Evidence chain survives tracing

Outcome question (binary):
For each major strategic claim in the brief (trajectory, positioning,
mechanism, recommendation rationale), can the reader trace the
specific evidence chain — the named signal, the cited source, the
disconfirming alternative engaged — without the chain collapsing
into "the brief says so"?

Score 1 (yes) — Every major strategic claim names its signals, cites
its sources, and either engages a disconfirming alternative or
acknowledges the claim is partial. Confidence is calibrated: high-
confidence claims have ≥3 independent sources; lower-confidence
claims say so explicitly.

Score 0 (no) — At least one major strategic claim asserts in
confident analytic language ("Acme is moving up-market", "this is
counter-positioning") with no traceable evidence chain, no
engaged alternative, no hedge. Plausible-tone synthesis without
analytic substance.

Score 0.5 (unknown) — Evidence chain exists but cannot be traced
from the brief alone (sources cited but unverifiable; signals named
but unrechecked).

CoT:
- Step 1: List every major strategic claim in the brief.
- Step 2: For each, trace the evidence chain (signal → source →
  inference → claim). Flag any chain that ends in "the brief says so".
- Step 3: Emit verdict + one-sentence justification.

Do not score: presence of citations (count is structural_gate's job),
length of reasoning section, named framework invocations.
```

**Edit 2 — Add §6 Goodhart-resistance note for CI-6:** "CI-6 catches plausible-strategic synthesis, but the workflow can game it by inserting fabricated citations to artificially deepen the evidence chain. Source-existence verification lives in structural_gate, not here — the judge assumes structurally-verified sources and tests reasoning on top."

**Edit 3 — Add §8 open question:** "Source-confabulation, entity-confabulation, and recency-window checks need to land in `_validate_competitive()` (see `2026-05-18-ci-ai-failure-modes.md` §8). CI-6 is conditioned on those passing."

---

## Sources

**Hallucination rates and detection:**
- HalluLens — arxiv 2504.17550
- HalluEntity — arxiv 2502.11948
- KGHaluBench — arxiv 2602.19643
- FAITH (finance tabular hallucination) — arxiv 2508.05201
- "Detecting AI Hallucinations in Finance" (information-theoretic, 92% reduction) — arxiv 2512.03107
- "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents" — arxiv 2604.03173
- Structural Hallucination network-based eval — arxiv 2603.01341
- Compound Deception (NeurIPS 2025 100-citation taxonomy) — arxiv 2602.05930
- HaluBench (15K samples, finance/medical/general) — Ravi et al. 2024
- Confabulations Document-Based Benchmark — github.com/lechmazur/confabulations

**Citation hallucination — specific rates:**
- Chelli et al. 2025: 19.9% of GPT-4o citations in literature reviews entirely fabricated (EurekAlert release)
- Perplexity 37% citation hallucination + real-URL-fabricated-claim profile (Deep Research retrospectives 2025)
- OpenAI Deep Research 78% / Claude with search 94% citation accuracy (2025 benchmarks)
- GhostCite: 14–95% hallucination rate across 13 LLMs × 40 domains

**Temporal / recency:**
- LLMLagBench — arxiv 2511.12116
- ProofTeller — aclanthology 2025.ijcnlp-long.80
- "Is Your LLM Outdated?" — NAACL 2025
- Recency bias in LLM-based reranking — arxiv 2509.11353
- "When Silence Is Golden" (temporal QA abstention) — arxiv 2602.04755

**Confidence / sycophancy / CoT-rationalization:**
- TrustJudge (corrected arxiv ID: 2509.21117, not 2510.27106) — Inconsistencies of LLM-as-a-Judge
- UQ Survey KDD 2025 — arxiv 2503.15850
- Anthropomimetic Uncertainty — arxiv 2507.10587
- BrokenMath sycophancy benchmark — arxiv 2510.04721
- "Good Arguments Against the People Pleasers" — arxiv 2603.16643
- "Verbalizing LLMs' assumptions to explain and control sycophancy" — arxiv 2604.03058
- Eidoku neuro-symbolic verification gate — arxiv 2512.20664
- "Calibrating LLM Judges: Linear Probes" — arxiv 2512.22245

**Financial / domain retrospectives:**
- BloombergGPT deficiency study — arxiv 2311.15548
- FactSet 2025 adoption study: 59% higher forecast error in AI-assisted reports — Institutional Investor 2025; replicated in arxiv 2512.19705
- BloombergGPT Terminal AI Summaries rollout retrospective — AI CERTs News 2025
- Bloomberg Belitsoft BloombergGPT overview

**RAG / source-grounding:**
- FinDER — arxiv 2504.15800
- FinRAGBench-V — arxiv 2505.17471
- "Optimizing Retrieval Strategies for Financial QA" — arxiv 2503.15191
- "Rethinking Retrieval: Agentic and Non-Vector Reasoning in Finance" — arxiv 2511.18177

**Production retrospectives:**
- Sports Illustrated 2023 fake AI biographies (Futurism / multiple)
- Apple Intelligence news-summary withdrawal 2025 (BBC / multiple)
- Deloitte $290K Australian-government report partial refund 2025 (multiple)
- NeurIPS 2025 100-fabricated-citations incident — arxiv 2602.05930

**Existing CI v2 spec context:**
- `docs/handoffs/2026-05-17-judge-design-step1-competitive.md` (v2, LOCKED 2026-05-18)
- `docs/research/2026-05-15-judges-domain-competitive.md` (human-CI framework synthesis)
- `src/evaluation/structural.py:86–120` (`_validate_competitive`, current shape-only checks)
- `src/evaluation/service.py:121–148` (pipeline: cache → structural gate → LLM judges → aggregate)
