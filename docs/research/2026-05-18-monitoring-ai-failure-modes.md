---
date: 2026-05-18
type: research deliverable
status: complete
topic: LLM-specific monitoring-digest failure modes (distinct from human-monitoring failures)
parent: docs/handoffs/2026-05-18-judge-design-step1-monitoring.md
sibling_human_domain: docs/research/2026-05-15-judges-domain-monitoring.md
sibling_axis_pattern: docs/research/2026-05-18-ci-ai-failure-modes.md
---

# LLM-Specific Failure Modes in Monitoring-Digest Generation

Companion to `docs/research/2026-05-15-judges-domain-monitoring.md` (human-monitoring failure modes: alert fatigue, burying the lede, weak-signal misses) and to the locked monitoring v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md`. The human-monitoring literature gets the *interpretive ceiling* right — what an excellent comms director's Monday brief looks like. It was written assuming a human analyst writes the digest from monitoring vendor output. When an LLM authors the synthesis instead, the failure surface mutates. This deliverable catalogues the LLM-specific failure modes for monitoring digests, walks the current 5 criteria (MON-1..MON-5) against them, and recommends where AI-failure detection should live in the pipeline.

The structural pattern follows the CI deliverable (`docs/research/2026-05-18-ci-ai-failure-modes.md`) — same four-failure-mode question taxonomy, mapped to the monitoring artifact shape (digest.md + findings.md + executive_summary.md + action_items.md + stories/*.json).

---

## TL;DR (350 words)

The MON v0 spec (MON-1 baseline framing / MON-2 severity classification / MON-3 lede placement / MON-4 action items / MON-5 cross-story compound and silence-as-signal) is sharp on *interpretive quality* but silent on four LLM-specific failure modes that human analysts almost never produce — and that named production retrospectives document at measurable double-digit rates.

The four failure modes the MON v0 spec does not catch:

1. **Event / entity / source confabulation in the digest body.** The digest invents press coverage that did not happen, attributes quotes to executives who never said them, cites analyst reports that do not exist, fabricates competitor responses. Apple News withdrew its summary feature in early 2025 after fabricating event details (a named shooter, an attributed verdict, an executive quote) attached to real news stories. Documented base rate: 19.9% citation-fab for GPT-4o (Chelli et al. 2025); 37% on Perplexity for citation tasks; 14–95% entity hallucination across 13 LLMs × 40 domains (GhostCite / HalluLens). MON-1's "X% vs baseline Y%" framing rewards the *form* of a delta — the LLM can fabricate the baseline.

2. **Recency / training-cutoff distortion presented as "this week."** The LLM frames months-old or training-cutoff-era events as fresh signal. LLMLagBench (arxiv 2511.12116) finds models released February 2026 may carry behavioral cutoffs of October 2024 for some domains. Apple News specifically failed by treating training-distribution events as recent. MON-1's delta-framing requirement makes this *worse* — a fabricated baseline plus an outdated "this week" framing produces a confident-sounding non-event.

3. **False-urgency framing / severity-tier inflation.** LLMs default toward providing value, which under selection pressure compounds into tier inflation: routine items get tagged "watch" or "crisis" to populate the severity field. Pager-tier vs digest-tier escalation breaks. Alert fatigue literature documents 73% of SOC teams cite false-positives as the top detection problem (SANS 2025); a brand-monitoring digest that calls everything "crisis" trains the comms director to ignore it, same root cause.

4. **Compound-claim fabrication — invented connective tissue.** The digest stitches real event Y to invented event Z via plausible-sounding narrative ("Pinsent partner-pull + RBS regulator letter = lateral-flight contagion"). The components may be real; the *connection* is generated, not observed. MON-5 explicitly rewards cross-story compounds, which under selection pressure becomes a fabrication surface unless the connective tissue itself is testable.

**Recommendation: structural_gate is the right home for #1 (event/source confabulation), #2 (recency), and partially for #3 (tier inflation via tier-distribution check); the judge is the right home for #4 (compound-claim fabrication) and the semantic shape of #3.** Add deterministic event-and-source verifiers to `_validate_monitoring()` in `src/evaluation/structural.py:141`. Add one new judge criterion MON-6 "compound-claim evidence chain survives tracing" specifically targeting fabricated connective tissue and over-confident severity. Same shape as CI-6, justified breach of ≤5 ceiling per design-guide §5 exception clause.

---

## 1. Q1 — Event / entity / source confabulation in the digest body (~430 words)

**The failure mode.** The monitoring digest invents the events it is reporting on. Three sub-shapes — distinct from the CI brief's source-confabulation surface because monitoring is about *event flow*, not about *strategic-claim provenance*:

- **Pure event invention.** "TechCrunch covered Acme's Series C this week" — no such article exists. The vendor feed had a real Series C mention from a different outlet, or a different company's Series C, and the LLM rewrote it.
- **Mention-to-quote escalation.** A vendor feed contains a press mention; the LLM converts the mention into an attributed direct quote ("Acme's CMO said 'we're going up-market'") that no source actually contains. Apple News's specific failure profile.
- **Source-tier inflation.** A blog mention becomes a "Wall Street Journal report" in the digest; a press-release rewrite becomes "Reuters coverage." Source-tier is load-bearing for severity classification, so this propagates.

**Documented base rates from the literature.**

- **GPT-4o literature reviews: 19.9% of citations entirely fabricated** (Chelli et al. 2025 mental-health-research study, EurekAlert May 2025).
- **HalluEntity (arxiv 2502.11948):** 18,785 entity-level annotations on ChatGPT biographies; entity-level hallucination rates are domain-dependent and frequently exceed sentence-level detection thresholds, meaning a digest can read internally consistent while every other named entity is wrong.
- **Compound Deception NeurIPS 2025 incident (arxiv 2602.05930):** 100 AI-generated hallucinated citations across 53 published papers, despite 3–5 expert reviewers per paper — taxonomy of Total Fabrication 66% / Partial Attribute Corruption 27% / Identifier Hijacking 4%. The *Partial Attribute Corruption* shape is the modal monitoring-digest failure (real source, wrong claim).
- **OpenAI Deep Research 78% / Claude with search 94% / Perplexity 37% citation accuracy** (Deep Research Agent retrospectives 2025) — *even web-search-grounded systems hallucinate URLs at 6%+ rates* (arxiv 2604.03173). RAG mitigates but does not eliminate.

**Production retrospectives for monitoring-shaped artifacts specifically.**

- **Apple Intelligence news-summary withdrawal (early 2025).** BBC retrospective documented fabricated event details (a named shooter, a named verdict, an attributed quote) attached to real news stories. This is the exact monitoring-digest failure shape: real source + fabricated event attribute.
- **Sports Illustrated 2023.** Fake AI-generated author biographies with fabricated photos passed editorial review for months — entity-level confabulation surviving in a media product whose business model is content credibility.
- **Deloitte Australian-government report 2025.** $290K refund after the LLM-generated content contained hallucinated entities and citations in a regulatory-monitoring deliverable.

**Why the human-monitoring literature does not catch this.** Cision, Brandwatch, Meltwater all assume the vendor feed *is* the source of record. The analyst writing the digest may editorialize, but does not invent press coverage. The failure mode is generative, not interpretive.

**Detection patterns that work.**

- **URL HEAD-check** for every citation in digest.md, findings.md, executive_summary.md (cheap, deterministic).
- **Quote-grep against vendor-feed corpus** — every direct quote in `""` must match a retrieved mention with cosine similarity ≥ 0.85.
- **Entity-existence check** against the input fixture's entity allowlist (named competitors, named executives in the brief's scope), plus Wikidata / SEC EDGAR fallback for unknown entities.
- **Mention-to-quote escalation flag:** scan for direct quotes where the vendor-feed mention contains no quoted text — that delta is a structural failure signal.

---

## 2. Q2 — Recency / training-cutoff distortion framed as "this week" (~410 words)

**The failure mode.** The digest presents training-distribution events or months-old vendor-feed entries as fresh weekly signal. The Monday-morning reader assumes everything in the digest is from the prior week unless explicitly hedged otherwise; an LLM that quietly recycles training-era context into "this week's" frame breaks that assumption.

Three sub-shapes:

- **Training-cutoff back-projection.** The LLM has a behavioral cutoff at, say, October 2024. Asked to produce a May 2026 digest, it pads the synthesis with 2024-vintage competitive context framed as current. "Acme's recent positioning around enterprise AI" — true as of training cutoff, stale for the reader's purpose.
- **Vendor-feed staleness.** The vendor feed includes a 6-month-old mention that resurfaced due to a syndication republish. The LLM frames the original story as "this week's news" because the feed timestamp is fresh.
- **Anniversary / recurrence inflation.** A 1-year-anniversary mention of a previous crisis (a "looking back" trade-press article) becomes, in the digest, "renewed coverage of the crisis."

**Documented base rates.**

- **LLMLagBench (arxiv 2511.12116, late 2025):** systematic evaluation of temporal knowledge boundaries. Key finding: "several LLMs exhibit multiple partial cutoff points… and training cutoffs often diverge significantly from release dates." A model released in Feb 2026 might carry a behavioral cutoff of Oct 2024 for some domains.
- **"Is Your LLM Outdated?" NAACL 2025:** temporal-QA accuracy drops 23–35% when shifting from "in 2020" to "4 years ago" framings. LLMs reason about absolute dates substantially better than relative ones — and most monitoring digests use the relative framing ("this week," "recent," "in the last quarter").
- **Recency bias in LLM-based reranking (arxiv 2509.11353):** when RAG retrieval brings back N candidates, the LLM reranker overweights the most-recently-dated retrieved document rather than the most-relevant. For monitoring this means: even with grounded retrieval, the digest may surface a recent low-stakes mention over an older but more material signal.
- **ProofTeller (aclanthology 2025.ijcnlp-long.80):** explicitly documents recency bias in LLM reasoning chains — the model overweights training-distribution recent events even when retrieved context contains current signal.

**Apple News retrospective — the specific failure profile that matters here.** The 2025 withdrawal was driven by news *summaries* that combined real event context with fabricated specifics. Some of those fabricated specifics were training-distribution facts (real prior events) crossed with current event framing — the LLM treated training data as current intelligence.

**Why the human-monitoring literature does not catch this.** Analysts know what year it is and know which vendor-feed entries are fresh vs. stale because the vendor delivers timestamps. The failure mode is LLM-specific.

**Detection patterns that work.**

- **"As of [YYYY-MM-DD]" header required** in digest.md — forces the model to commit to an effective date the reader can interrogate.
- **Every claim with implicit-recency framing ("this week," "recent," "newly")** must point to a retrieved source dated within the past 14 days.
- **Per-story `evidence_dates` array required in stories/*.json** — each story carries the source dates that ground its claims; structural_gate verifies ≥1 source dated within 7 days of digest issuance for items framed as "this week."
- **Forced post-cutoff probing in the workflow:** include a step "what would have changed in this market in the last 90 days that you might not know about?" — surfaces the temporal blind spot rather than papering over it.

---

## 3. Q3 — False-urgency framing / severity-tier inflation (~440 words)

**The failure mode.** LLMs systematically inflate severity classification under selection pressure. Three sub-shapes:

- **Tier-field stuffing.** Every story carries a severity tier because the template has a field; routine items get the field populated with "watch" or higher because "noise" feels like a non-answer the rubric might penalize. This is the MON-2-specific Goodhart pathology already named in v0 §6.
- **Single-axis sentiment driving severity.** High-emotionality content (employee complaint going mildly viral) gets classified as "crisis" because the volume / sentiment axes are loud, even though the hazard axis is low. Cision React Score's whole design exists to prevent this; the LLM mimics the framework's tier output without performing the orthogonal-axis reasoning.
- **Pager-tier collapse.** In a system designed with two escalation tiers (a daily/weekly "digest tier" with action items + a real-time "pager tier" for live crises that need to wake the CEO), LLM-driven false-urgency promotes routine items to pager-equivalent framing in the digest, training the reader to ignore the urgency signal entirely.

**Documented base rates and the structural connection to sycophancy literature.**

- **"Good Arguments Against the People Pleasers" (arxiv 2603.16643):** LLMs sacrifice factual accuracy "to cater to the user's perceived beliefs or preferences." For monitoring, the "perceived preference" is *the comms director wants to find something worth flagging this week* — so the digest finds something. The LLM does not generate "nothing material happened this week" easily, because that response feels like a failure of the task.
- **BrokenMath sycophancy benchmark (arxiv 2510.04721):** even mild user-direction cues produce "rigorous-sounding but biased justifications" — for monitoring, this becomes confident-tone severity reasoning that defends an inflated classification.
- **2025 SANS Detection and Response Survey:** 73% of security teams cite false positives as their top detection challenge. The structural transfer to monitoring digests is direct: a digest that flags everything as elevated trains the reader to ignore the elevation field.
- **Anthropomimetic Uncertainty (arxiv 2507.10587):** verbalized uncertainty in LLMs is poorly calibrated — the model says "I'm not sure" in patterns that do not track its actual reliability. For monitoring this means severity-tier confidence ("HIGH" / "MEDIUM" / "LOW") does not correlate with the underlying evidence quality.
- **Eidoku (arxiv 2512.20664):** hallucination is "often a failure of structural consistency rather than low-confidence" — the model is structurally confident even when wrong. A "HIGH" classification carries no internal humility signal.

**Cross-reference to the existing rubric pathology catalogue.** The Phase 4 rollback (`698e658` → `c76f051`) was triggered partly by exactly this failure shape: judges that rewarded the *appearance* of severity classification (tier field present, defended in prose) without enforcing the orthogonal-axis reasoning behind it. The current MON-2 prose addresses the form but not the systematic LLM tendency toward tier inflation.

**Why the human-monitoring literature does not catch this fully.** Alert-fatigue literature (Vectra, Motadata, IBM, Brandwatch) names the *human-side* failure — analysts manually classifying every uptick as crisis. The LLM version is structurally similar but mechanistically different: the human is overworked and pattern-matches loosely; the LLM is sycophantically completing the template field.

**Detection patterns that work.**

- **Tier-distribution check in structural_gate:** the digest's severity-tier distribution must satisfy "at least one item classified as 'noise' or 'below-fold' per N stories" for N ≥ 5. Forces a structural floor on de-escalation.
- **Pager-tier promotion grep:** scan for "urgent / immediate / critical / crisis" framing; require an orthogonal-axis justification (hazard AND emotionality, or competence AND ethics axes) be present in the same paragraph.
- **Comparative tier-baseline:** maintain a rolling 4-week distribution of severity tiers per fixture; if this week's distribution shifts more than 2σ toward elevated tiers, structural_gate flags for review.
- **Judge-side test (MON-2 already, but tightened in MON-6):** for the top-1 elevated item, was the orthogonal-axis reasoning specifically applied, or is the reasoning a confident-tone justification for a foregone classification?

---

## 4. Q4 — Compound-claim fabrication / invented connective tissue (~430 words)

**The failure mode.** The digest connects real events through invented causal or narrative tissue. The components are real; the *connection* is generated. This is the most insidious LLM failure for monitoring specifically because MON-5 explicitly rewards cross-story compounds. Under selection pressure, MON-5 becomes a compound-fabrication surface.

Three sub-shapes:

- **Real Y + real Z + invented "because" / "leading to" / "in response to."** Pinsent partner-pull (real) + RBS regulator letter (real) + invented connective claim ("the regulator letter is RBS's response to the Pinsent expansion") — neither event causes the other; the LLM stitched them.
- **Pattern-naming without pattern evidence.** "This is the third lateral-flight cluster in Q3" — only one of the three named items is actually a lateral-flight; the others are loosely related personnel moves the model categorized as the same pattern.
- **Forward-projection extrapolation from invented compound.** "If the Pinsent-RBS dynamic continues, expect 2–3 more partner moves by end of quarter" — the projection is calibrated to a compound that never existed.

**Documented base rates.**

- **TrustJudge (arxiv 2509.21117):** Score-Comparison Inconsistency and Pairwise Transitivity Inconsistency in LLM-as-judge frameworks — the structural failure of building consistency across multi-claim reasoning chains. Maps to compound-fabrication: the LLM cannot reliably preserve evidence-chain integrity across the multiple claims a compound requires.
- **Structural Hallucination network-based eval (arxiv 2603.01341):** specifically tests whether the *graph* of claim → source → claim connections is consistent. "90% of valid references fall among the top 10% most-cited papers" — popularity bias in citation generation transfers to popularity bias in narrative-connection generation; the LLM stitches together the *most-narratively-plausible* connection, not the actual causal one.
- **FactSet 2025 retrospective:** AI-assisted reports judged as having *more comprehensive coverage* (richer language, more sources cited) but *59% higher forecast error*. The richness comes from compound-claim language ("X led to Y, which suggests Z") — the error comes from the fabricated connective tissue.
- **Eidoku (arxiv 2512.20664):** hallucination is "a failure of structural consistency" — for compound claims, the structural inconsistency is the un-evidenced linkage between provably-real components.

**Apple News's hardest failure case.** The withdrawn summaries did not only fabricate single facts — they fabricated *narrative arcs* across real events. A real shooting + a real arrest + an invented intermediate fact about motive = a confident-tone narrative thread where each component is real but the thread is generated.

**The MON-5 amplification risk specifically.** MON-5 v0 prose says: "At least one cross-story compound is named explicitly (two developments revealed as the same narrative)." Under 50-generation selection pressure, the workflow learns that compound-shaped output scores high — and (because connective tissue is the cheapest part of a compound to fabricate) learns to fabricate connections rather than detect them. The criterion as currently shaped is Goodhart-prone in a way the human-monitoring literature does not flag.

**Why the human-monitoring literature does not catch this fully.** The Ansoff weak-signal tradition and Harvard's Narrative Contradictions framework assume analysts are *missing* connections; they do not flag the LLM-specific failure of *fabricating* connections to score on a compound-rewarding rubric.

**Detection patterns that work.**

- **Connective-tissue verb grep:** "in response to," "driven by," "leading to," "as a result of," "because of" in cross-story paragraphs require explicit source-grounded backing for the causal claim — not just for each component.
- **Compound-decomposition CoT in the judge:** for each cross-story compound, the judge walks the components separately, asks "is the connection itself evidenced or generated?", and flags fabricated connective tissue as a structural failure.
- **Co-occurrence floor:** the two stories in a compound must share at least one named entity or one cited source; pure narrative-coincidence compounds get rejected.
- **Forward-projection traceability:** any projection ("expect 2–3 more X by end of quarter") must trace to either (a) historical base rate of the pattern, or (b) named upstream signal — not to a fabricated compound.

---

## 5. Cross-cutting — what MON v0 catches vs misses (~440 words)

Walk each MON v0 criterion against the 4 failure modes:

| Criterion | Q1 Event/source confab | Q2 Recency distortion | Q3 False-urgency / tier inflation | Q4 Compound-claim fabrication |
|---|---|---|---|---|
| MON-1 baseline framing | NO (delta can be fabricated) | weak (delta vs *what* baseline?) | NO | NO |
| MON-2 severity classification | NO | NO | partial (forces orthogonal axes) | NO |
| MON-3 lede placement | NO | weak partial | NO | NO |
| MON-4 action items (owner/deadline/consequence) | NO | NO | partial (forces operational specificity) | NO |
| MON-5 cross-story + silence-as-signal | NO | NO | NO | NO — actively rewards compound shape |

**What MON v0 actually catches:**

- **Q3 partial via MON-2:** MON-2 requires orthogonal-axis reasoning for severity classification (e.g., harm AND emotionality), which catches some single-axis-sentiment-driven inflation. It does *not* catch tier-distribution inflation across the digest as a whole, and it does not catch sycophancy-driven tier promotion when the LLM generates plausible orthogonal-axis prose to defend a foregone classification.
- **Q3 partial via MON-4:** MON-4's owner/deadline/consequence triple is structurally hard to fabricate convincingly — a vague "the team should monitor by ongoing for reputation reasons" scores 0. This raises the cost of urgency-inflation by forcing operationalization. Still partial: the LLM can generate concrete-sounding action items grounded in a fabricated event.

**What MON v0 does not catch at all:**

- **Q1 event / source confabulation:** Zero coverage. Structural_gate (`_validate_monitoring` in `src/evaluation/structural.py:141`) checks 13 assertions about file presence, results.jsonl shape, source count — no URL check, no event-existence verification, no quote grep against vendor feed.
- **Q2 recency distortion:** Zero coverage. No "as of" date required, no per-story `evidence_dates`, no freshness verification on "this week" claims.
- **Q3 systematic tier inflation:** Zero coverage at the digest-distribution level. MON-2 catches single-story tier defense but not the systematic shift.
- **Q4 compound-claim fabrication:** Zero coverage — and worse, MON-5 *rewards* compound shape, creating a Goodhart surface for fabricated connective tissue. This is the highest-priority gap.

**The asymmetric risk.** A monitoring digest that (a) fabricates one press mention, (b) generates a 6-week-old training-data event framed as "this week," (c) classifies it "watch" with confident orthogonal-axis prose, (d) connects it to a real regulator letter via invented narrative tissue, and (e) issues a concrete action item with owner+deadline+consequence — would score *high* under v0. MON-1 = 1 (baseline framed, even if baseline is fabricated). MON-2 = 1 (orthogonal axes invoked). MON-3 = 1 (compound positioned in lede). MON-4 = 1 (operational action item). MON-5 = 1 (compound named explicitly). 5/5. Entirely fabricated. This is the architectural gap, structurally identical to the CI v2 gap and addressed by the same intervention pattern.

**Empirical priors on which failure mode hits hardest.** Looking at the documented rates: Q1 (event/source confabulation, 19.9–37% base rate per the Chelli / Perplexity benchmarks) is most-frequent. Q4 (compound fabrication) is hardest to detect post-hoc — it requires graph-structural verification. Q3 (tier inflation) is highest-impact on reader trust because it directly breaks the pager-tier vs digest-tier system. Q2 (recency distortion) is the most-systematic — it is a property of every LLM call, not a stochastic failure.

---

## 6. Recommendation — where should AI-failure-mode detection live? (~370 words)

**Recommended split by failure mode, following the CI deliverable's pattern (`docs/research/2026-05-18-ci-ai-failure-modes.md` §8):**

| Failure mode | Best home | Why |
|---|---|---|
| Q1 Event / entity / source confabulation | `structural_gate` | Deterministic (URL HEAD, quote-grep, entity allowlist). Cheap. Binary pass/fail. Wrong fit for a judge scoring quality. |
| Q2 Recency / cutoff distortion | `structural_gate` + workflow | Structural: "as of" date required, per-story `evidence_dates`, ≥1 source within 7 days for "this week" framing. Workflow: date-filtered retrieval. |
| Q3a Tier-distribution inflation | `structural_gate` (light) + judge (MON-6) | Structural: tier-distribution check (≥1 below-fold per N items; 2σ comparative baseline). Judge: does the top-1 elevated item survive orthogonal-axis interrogation? |
| Q3b Severity confidence calibration | judge (MON-2 already; MON-6 extends) | Semantic. Cannot be done deterministically. |
| Q4 Compound-claim fabrication | judge (new criterion MON-6) | Requires semantic reasoning about evidence-chain integrity across multiple claims. Cannot be done deterministically. |

**Why this is consistent with the existing pipeline.** Per `src/evaluation/structural.py:141–270`, `_validate_monitoring` already runs 13 assertions about file presence and results.jsonl shape; it is documented as "Free, deterministic, fast" and Layer 2 of the evaluation pipeline. Adding event/source verifiers + freshness check + tier-distribution check is the natural extension. The new judge criterion lives alongside MON-1..MON-5 in the existing judge surface.

**Why a dedicated AI-failure criterion (MON-6 equivalent) is warranted.** Per design-guide §5's documented-exception clause, a 6th criterion is justified when (a) the literature documents an LLM-specific failure surface, (b) the other 5 criteria cannot catch it, and (c) the failure mode has measured effect sizes from 2024–2026 literature. All three conditions hold for compound-claim fabrication: documented in TrustJudge / Structural Hallucination / FactSet / Eidoku at 59% forecast-error rates and structural inconsistency rates; not caught by MON-1..MON-5 (in fact MON-5 *amplifies* the surface); measured effect sizes available. The CI lane established the precedent with CI-6 evidence-chain.

**Goodhart resistance for MON-6.** The risk pattern mirrors CI-6: the workflow can game the criterion by inserting *fabricated* citations to artificially deepen the evidence chain. The mitigation is the same — source-existence verification lives in structural_gate (not in MON-6); the judge assumes structurally-verified sources and tests reasoning on top.

**Why not a separate "AI-slop gate."** Same argument as CI: the failure modes split cleanly into "deterministic + cheap" (Q1, Q2, Q3a) and "semantic + judge-shaped" (Q3b, Q4). The cheap deterministic checks belong in `structural_gate` (existing infrastructure, existing pass/fail contract). The semantic checks belong in the judge prose. A new gate would be architectural duplication.

---

## 7. Concrete edits to MON v0 spec (~270 words)

**Edit 1 — Add MON-6 (judge criterion).**

```
### MON-6 — Compound-claim evidence chain survives tracing

Outcome question (binary):
For each cross-story compound, forward projection, and elevated-
tier severity classification in the digest, can the reader trace
the evidence chain — the named events, the cited sources, the
actual co-occurring entities — without the chain collapsing into
"the digest says so"?

Score 1 (yes) — Every compound is built from components that share
at least one named entity or one cited source; the connective tissue
("led to," "in response to," "driven by") is itself source-grounded,
not generated. Every forward projection traces to historical base
rate OR a named upstream signal. Every elevated-tier classification
survives orthogonal-axis interrogation, not just orthogonal-axis prose.

Score 0 (no) — At least one compound stitches real components with
invented connective tissue. Or a forward projection rests on a
fabricated compound. Or an elevated-tier classification rests on
confident-tone orthogonal-axis defense without underlying axis
evidence.

Score 0.5 (unknown) — Evidence chain partially traces but one of
the top-3 compounds / projections / elevated classifications has
insufficient supporting detail in the digest to evaluate.

CoT:
- Step 1: List the top-3 compounds, projections, elevated tiers.
- Step 2: For each, walk the evidence chain (components → connective
  tissue → claim). Flag any chain where the connective tissue is not
  source-grounded.
- Step 3: Flag any event confabulation, recency distortion, or
  systematic tier inflation passed through from structural_gate.
- Step 4: Emit verdict + one-sentence justification.

Do not score: number of compounds (count is MON-5's job), citation
density (structural_gate), tier-vocabulary choice.
```

**Edit 2 — Add §6 Goodhart-resistance note for MON-6:** "MON-6 catches fabricated connective tissue, but the workflow can game it by inserting fabricated citations to artificially deepen the evidence chain. Event-existence and source-existence verification lives in `structural_gate`, not here — the judge assumes structurally-verified events and sources and tests reasoning integrity on top."

**Edit 3 — Add §8 open question (replacing or augmenting existing #3 about `_persist_monitoring_dqs_score`):** "Event/source confabulation, recency-distortion, and tier-distribution checks need to land in `_validate_monitoring()` (see `2026-05-18-monitoring-ai-failure-modes.md` §6). MON-6 is conditioned on those passing. Specifically: URL HEAD-check, quote-grep against vendor-feed corpus, entity-existence allowlist, `evidence_dates` array per story, ≥1 source within 7 days for 'this week' framing, tier-distribution floor (≥1 'noise' / 'below-fold' per 5 stories)."

---

## 8. Open questions

1. **Tier inflation comparative baseline.** A 4-week rolling tier-distribution per fixture is the cleanest signal for systematic inflation, but requires monitoring-lineage persistence. The existing `digest-meta.json` sidecar from `_persist_monitoring_dqs_score` already provides a hook; whether to extend it for tier-distribution tracking is an ops integration question.

2. **Silence-as-signal verification.** MON-5 rewards silence-as-signal flagging ("expected analyst-day coverage did not materialize"). Verifying *expected-vs-actual* requires either (a) a per-fixture expectations file (high-effort), or (b) the judge inferring expectation from prior digests (Goodhart-prone). Defer to MON v1 or v2.

3. **Compound-decomposition cost in judge CoT.** MON-6's per-compound evidence-chain walk adds ~250 tokens × 3 compounds × 3 panel models = ~2.25k extra tokens per judgment, ~$0.02 per call at Opus rates. Acceptable.

4. **Redundancy check between MON-5 and MON-6.** MON-5 rewards compound-naming; MON-6 tests the evidence chain of compounds. They are tightly related and may correlate >0.7 on the design-guide §5 redundancy check. If so, MON-6 absorbs into MON-5 (forced to include evidence-chain testing in MON-5's prose) and the live floor stays at 5. Run the empirical check on 5 fixtures × 6 criteria × 3 panel models before locking the 6th-criterion exception.

5. **Vendor-feed corpus availability for quote-grep.** The structural quote-verification check assumes the vendor-feed corpus is accessible at evaluation time. Verify this against the current monitoring lane's data flow before committing to the structural_gate edit.

6. **Cross-failure-mode interaction.** Q1 (event confabulation) + Q4 (compound fabrication) compound: an entirely-fabricated compound built from entirely-fabricated events would pass MON-6's evidence-chain test (the chain internally references the fabricated events) unless structural_gate's event-existence check fires first. The structural-gate-before-judge ordering is load-bearing for this defense.

---

## Citations with effect sizes

**Entity / event / source confabulation:**

- HalluLens — arxiv 2504.17550 — non-existent entity handling, long-form generation, PreciseQA testing
- HalluEntity — arxiv 2502.11948 — 18,785 entity-level annotations; entity-level rates exceed sentence-level detection thresholds
- KGHaluBench / GhostCite — arxiv 2602.19643 — 14–95% entity-existence hallucination across 13 LLMs × 40 domains
- Chelli et al. 2025 (EurekAlert May 2025) — **19.9% of GPT-4o citations in literature reviews entirely fabricated**
- Perplexity Deep Research — **37% citation hallucination + real-URL-fabricated-claim profile** (2025 retrospectives)
- OpenAI Deep Research 78% / Claude with search 94% citation accuracy (2025 benchmarks)
- Compound Deception (NeurIPS 2025) — arxiv 2602.05930 — 100 hallucinated citations / 53 papers; **66% Total Fabrication, 27% Partial Attribute Corruption, 4% Identifier Hijacking**
- Detecting and Correcting Reference Hallucinations in Commercial LLMs — arxiv 2604.03173 — **3–13% URL hallucination even in web-search-grounded systems**
- Structural Hallucination — arxiv 2603.01341 — citation-existence rates 40–50% for LLM-generated references; popularity bias (90% of valid refs in top-10% most-cited)

**Recency / training-cutoff:**

- LLMLagBench — arxiv 2511.12116 (late 2025) — multiple partial cutoff points per model; training cutoffs diverge from release dates
- "Is Your LLM Outdated?" — NAACL 2025 — **23–35% accuracy drop** when shifting from absolute to relative temporal framings
- Recency bias in LLM-based reranking — arxiv 2509.11353 — reranker overweights most-recent retrieved doc
- ProofTeller — aclanthology 2025.ijcnlp-long.80 — recency bias in LLM reasoning

**Confidence / sycophancy / tier inflation:**

- "Good Arguments Against the People Pleasers" — arxiv 2603.16643 — LLMs sacrifice factual accuracy for perceived user preference
- BrokenMath sycophancy benchmark — arxiv 2510.04721 — mild user-direction cues produce rigorous-sounding biased justifications
- Anthropomimetic Uncertainty — arxiv 2507.10587 — verbalized uncertainty poorly calibrated
- Eidoku — arxiv 2512.20664 — hallucination is "failure of structural consistency rather than low-confidence"
- TrustJudge — arxiv 2509.21117 — Score-Comparison Inconsistency, Pairwise Transitivity Inconsistency
- 2025 SANS Detection and Response Survey — **73% of SOC teams cite false-positives as top detection challenge**

**Compound-claim / structural consistency:**

- Structural Hallucination network-based eval — arxiv 2603.01341
- FactSet 2025 adoption study (Institutional Investor 2025; arxiv 2512.19705) — **AI-assisted equity reports have 59% higher forecast error** than analyst-only
- Eidoku neuro-symbolic verification — arxiv 2512.20664
- UQ Survey KDD 2025 — arxiv 2503.15850

**Production retrospectives — monitoring-shaped artifacts:**

- Apple Intelligence news-summary withdrawal (early 2025) — BBC retrospective; named shooter, named verdict, attributed quote fabricated on real news stories
- Sports Illustrated 2023 fake AI biographies — Futurism / multiple
- Deloitte $290K Australian-government report partial refund 2025 — multiple

**Existing MON v0 context:**

- `docs/handoffs/2026-05-18-judge-design-step1-monitoring.md` (MON v0)
- `docs/research/2026-05-15-judges-domain-monitoring.md` (human-monitoring framework synthesis: Cision React Score, Coombs SCCT, Benoit, Sandman, AMEC, FAA AD format, PDB precedent, Dezenhall Glass Jaw)
- `src/evaluation/structural.py:141–270` (`_validate_monitoring`, current 13 assertions, shape-only)
- `src/evaluation/service.py:121–148` (pipeline: cache → structural gate → LLM judges → aggregate)
- `docs/research/2026-05-18-ci-ai-failure-modes.md` (sibling CI deliverable — same axis pattern, mapped to CI artifact shape)
- `docs/rubrics/judge-design-guide.md` §5 (documented-exception clause for AI-specific failure-surface criteria)
