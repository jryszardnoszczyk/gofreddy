---
date: 2026-05-18
type: research deliverable
status: complete
topic: LLM-specific marketing-audit failure modes (distinct from human-consultant failures)
parent: docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md
siblings:
  - docs/research/2026-05-18-judges-domain-marketing-audit.md (human-MA domain research)
  - docs/research/2026-05-18-ci-ai-failure-modes.md (LLM-specific CI failure modes — sibling axis)
guide: docs/rubrics/judge-design-guide.md
---

# LLM-Specific Failure Modes in Marketing-Audit Generation

Companion to `docs/research/2026-05-18-judges-domain-marketing-audit.md` (human-MA practitioner methodology — what an excellent audit looks like) and to the draft v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md`. The human-MA literature got the *quality ceiling* right — binding-constraint diagnosis, stage-appropriate prescription, revenue-chain tracing, upstream-problem surfacing. But the practitioner playbooks (Kalungi, Bell Curve, Demand Curve, Sean Ellis, Brian Balfour, Patrick Campbell, Lenny Rachitsky, Peep Laja) were written for human consultants who *know what they don't know*. They do not catch the failure modes that show up when an LLM produces the audit instead of an analyst.

This deliverable catalogues those LLM-specific marketing-audit failures, measures them against published rates, walks the draft MA-1..MA-5 criteria against them, and recommends where AI-failure detection should live in the pipeline.

---

## TL;DR (320 words)

The MA v0 spec (MA-1 binding constraint / MA-2 30-day experiment / MA-3 revenue chain / MA-4 stage map / MA-5 upstream problem) is sharp on *audit quality and reader-effect* but silent on five LLM-specific failure modes that human auditors almost never produce — and that named production systems exhibit at measurable, double-digit rates.

The five failure modes the spec does not catch:

1. **Financial-metric confabulation** — the audit invents CAC, LTV, NRR, MRR, ARR, payback, churn, or trial-to-paid numbers that do not exist in the source data. FAITH (arxiv 2508.05201) reports 17–46% intrinsic hallucination rates on financial-entity numerical statements in tabular finance; "Detecting AI Hallucinations in Finance" (arxiv 2512.03107) reports a 92% reduction is *possible* with information-theoretic detection, which by inverse implies a substantial baseline.
2. **Channel-claim fabrication** — the LLM asserts "LinkedIn ads are working" / "their SEO is the dominant channel" / "they ran a TikTok campaign" without evidence. Production retrospective: Sports Illustrated 2023 fabricated author biographies; FactSet 2025 reports AI-assisted analyst output exhibits 59% higher forecast error specifically from un-vetted plausible-sounding signal.
3. **Competitor-data confabulation** — pricing tiers, positioning claims, customer logos, executive moves on competitors that don't exist or are misattributed. HalluLens / KGHaluBench / HalluEntity document context-free entity hallucination rates of 14–95% across 13 models × 40 domains.
4. **Marketing-misdiagnosis bias** — measurable LLM tendency to over-blame marketing when the root cause is product / pricing / positioning / sales. This is the AI analogue of the practitioner-named "marketing-as-default-explanation" pathology — and the LLM bias appears stronger than the human bias because LLMs are trained on marketing-blog content where marketing is *always* the answer.
5. **Recommendation hallucination** — recommending channels, tactics, or playbooks that don't apply to the client's stage / vertical / ARR band / sales motion. LLMLagBench (arxiv 2511.12116) plus the practitioner-named "wrong-stage best-practices" failure compound here.

**Recommendation: structural_gate handles #1, #2, #3, and the deterministic parts of #5; the judge handles #4 and the semantic parts of #5.** Add 5 deterministic checks to `_validate_marketing_audit()`. Consider adding a justified-breach 6th criterion MA-6 "Diagnosis survives blame-attribution check" specifically targeting marketing-misdiagnosis bias if redundancy check confirms it doesn't collapse into MA-5.

---

## 1. Key Research Questions

1. **Financial-metric confabulation rates** — when an LLM generates audit-grade analysis citing CAC, LTV, NRR, MRR, ARR, payback, churn, what fraction of the numbers are fabricated, transposed, or borrowed from a different company / time period?
2. **Channel-claim fabrication** — at what rate does an LLM assert specific competitor channel-mix or channel-performance claims ("they're winning on LinkedIn", "their content engine is the moat") without evidence?
3. **Competitor-data confabulation** — at what rate does an LLM invent pricing tiers, packaging, positioning statements, customer wins, or executive moves on real or invented competitors?
4. **Marketing-misdiagnosis bias** — is there a measurable LLM tendency to over-attribute pipeline / revenue problems to marketing causes (channel mix, message, demand-gen budget) when the actual root cause is product / pricing / positioning / sales / PMF?
5. **Recommendation hallucination** — at what rate does an LLM recommend tactics (ABM tooling, paid-LinkedIn pilots, product-led growth motions, demand-gen programmes) that don't fit the client's stage / vertical / ARR band / sales motion?
6. **What deterministic checks belong in `structural_gate`?** — metric-citation grep, channel-claim source check, competitor-claim source check, stage-applicability gate, hallucinated-tactic detection.
7. **Does MA warrant a dedicated AI-failure criterion?** — if the deterministic gates catch most of the surface failures, do we still need a judge criterion specifically targeting marketing-misdiagnosis bias (the bias that can't be deterministically caught)?

---

## 2. Q1 — Financial-metric confabulation (~430 words)

**The failure mode.** An LLM-generated marketing audit references specific quantified metrics — "your CAC payback is 18 months," "your trial-to-paid is 1.8%," "your monthly churn is 6.4%," "your NRR is 91%," "your ARR is $2.4M with 12% MoM growth" — that do not exist in the source materials the audit was generated from. Three sub-shapes show up:

- **Pure invention.** No CAC payback number was in the brief; the LLM generated "your CAC payback is 18 months" from priors about pre-Series-B SaaS.
- **Source-substitution.** A real CAC number from a *different* fixture or a *different* time window gets paired with the current client.
- **Aggregation invention.** The LLM "computes" a metric from partially-available inputs without showing the math, then asserts it confidently ("your blended CAC is $1,247" derived from values the LLM does not have access to).

**Documented rates — strong signal in finance domain.**

- **FAITH (arxiv 2508.05201)** — Financial-Answering benchmark; intrinsic hallucination rates of 17–46% on financial-entity *numerical* statements depending on model and task framing.
- **Bloomberg's deficiency study (arxiv 2311.15548)** — "an LLM incorrectly reporting that a non-existent company missed its quarterly earnings target based on a non-existent press release" is documented as the canonical failure category. The same shape transfers to audit metrics: a non-existent CAC payback "result" gets attributed to a real company.
- **FactSet 2025 adoption study (Institutional Investor 2025, replicated in arxiv 2512.19705)** — AI-assisted equity research reports exhibit **59% higher forecast errors than analyst-only reports**. The mechanism is not obvious lying; it is the LLM citing more numbers (each with non-zero hallucination probability) and the errors compounding through the forecast.
- **HaluBench (Ravi et al. 2024)** — 15K samples across finance / medical / general; finance domain hallucination rates persistently exceed general-purpose QA hallucination rates.
- **"Detecting AI Hallucinations in Finance" (arxiv 2512.03107)** — information-theoretic detector reports a 92% reduction in financial-claim hallucinations; the *baseline* before detection that the 92% reduction is computed against is therefore non-trivial.

**Why human consultants don't do this.** A Bell Curve or Kalungi auditor pulls metrics from the client's actual GA/Stripe/HubSpot/PostHog data; the metric either exists or it doesn't. They flag "we don't have this number" rather than generating a plausible one. The LLM failure mode is generative-fluency: when the audit "needs" a number to be complete, the LLM produces one that fits the priors of pre-Series-B SaaS.

**The asymmetric risk for marketing audits specifically.** Marketing audits more than CI briefs depend on *quantified* claims. MA-1 (binding constraint) and MA-3 (revenue chain) both reward briefs that name specific numbers. An LLM that confabulates "your trial-to-paid is 1.8% vs SaaS median 6%" gets MA-1=1 (constraint named with evidence) and MA-3=1 (chain traced through to revenue) — *exactly because the spec rewards quantification*. The judge cannot tell the number is fabricated. This is the architectural gap.

**Detection patterns that work.**
- **Metric-citation grep** — any number formatted as percentage, dollar amount, multiple, or ratio in the audit body must have an inline source attribution that points to a real input artifact.
- **Source-corpus numerical match** — for each cited metric, the exact number (with ±5% tolerance for rounding) must appear in at least one source document the workflow had access to.
- **Forbidden weasel formulations** — "industry-standard," "typical SaaS," "based on benchmarks" without a named primary source = structural failure.
- **Aggregation-without-math flag** — any "your blended" / "your effective" / "your adjusted" metric without a visible derivation gets flagged.

---

## 3. Q2 — Channel-claim fabrication (~390 words)

**The failure mode.** The LLM asserts specific channel-performance claims about the client's marketing — "LinkedIn ads are working for you," "your SEO is the dominant channel," "outbound has stalled" — or about competitors — "they're winning on TikTok," "their content engine is the moat," "they ran a six-figure paid-LinkedIn pilot in Q3." The shape is dangerous because the *category* of channel claim is plausible for the company's stage, the *direction* of the claim is plausible (LinkedIn for B2B SaaS), and the prose tracks like marketing-blog content.

Three sub-shapes:

- **Source-free channel attribution.** "Your strongest channel is content marketing" — no underlying analytics, no Gong calls, no UTM analysis.
- **Competitor-channel-mix invention.** "Acme is doubling down on partnerships" — no press release, no LinkedIn post, no investor-day language to back it.
- **Stage-prior projection.** The LLM applies a pre-Series-B SaaS prior ("content + SEO is the dominant channel") to every audit, regardless of the client's actual signal.

**Documented rates and retrospectives.**

- **Sports Illustrated 2023 retrospective** (Futurism, multiple sources) — fabricated AI-generated author biographies with fabricated headshots. Not marketing-audit-specific, but the failure shape transfers: plausible-sounding-author becomes plausible-sounding-channel-claim.
- **FactSet 2025 retrospective** — the 59% forecast-error finding is rooted in "comprehensive coverage" (more channels cited, more signals surfaced) outrunning "comprehensive substance." The LLM cites more channels because the latent strategy-memo style cites multiple channels.
- **Apple Intelligence news-summary withdrawal (BBC retrospective, 2025)** — fabricated event details attached to real news stories. The structural analogue for marketing audits: fabricated channel-performance claims attached to a real company.
- **CB Insights / Crayon retrospectives (2026)** — human-analyst review retained in the loop precisely because the move-summarization and channel-attribution steps are unreliable.
- **Marketing-blog prior contamination.** This is the LLM-specific structural factor: the training corpus for marketing-channel claims is heavily weighted toward marketing-blog content where "LinkedIn ads are working" / "content + SEO is the moat" is the modal claim regardless of company specifics. The LLM has a latent prior that B2B SaaS = content + SEO, and a separate prior that B2C = paid social + influencer. These priors fire even when the actual data points elsewhere.

**Why human consultants don't do this.** A Bell Curve or Demand Curve auditor traces channel claims to UTM-tagged spend data, attribution-model output, Gong-call transcripts, or named campaign reports. The channel claim either has data behind it or gets flagged as "we lack visibility on channel X." The LLM failure mode is the priors-fill-the-gap: when channel data is absent, the LLM generates a plausible-looking channel-mix claim from latent space rather than flagging the absence.

**Detection patterns.**
- **Channel-claim source check** — every channel-performance claim must cite a specific source (analytics screenshot, Gong-call transcript ID, campaign report, ad-platform export). Bare channel claims fail.
- **Forbidden formulations** — "their dominant channel is," "their go-to-market is," "they're winning on" without an inline citation = structural failure.
- **Stage-prior detection** — if the audit's channel mix recommendation for a $2M ARR B2B SaaS matches the canonical "content + SEO" prior verbatim, flag for human review.

---

## 4. Q3 — Competitor-data confabulation (~410 words)

**The failure mode.** Marketing audits frequently reference competitors — pricing tiers, positioning statements, packaging, customer wins, channel mix, recent moves. The LLM invents these in three sub-shapes that match the CI domain's documented entity-hallucination shapes:

- **Pricing invention.** "Acme is at $79/seat/mo; you're priced 25% above on a feature-equivalent tier" — no Acme pricing page was retrieved; the $79 was generated.
- **Positioning fabrication.** "Their positioning is the 'no-code-first' workflow tool for ops teams" — no positioning audit was conducted; the claim was synthesized from the company name and the LLM's prior.
- **Customer-logo / executive-move invention.** "Their recent customer wins include Stripe and Notion" — neither customer has any public association with the named competitor.

**Documented rates — borrowed from the CI domain and applicable here.**

- **HalluLens (arxiv 2504.17550), HalluEntity (arxiv 2502.11948), KGHaluBench (arxiv 2602.19643), GhostCite** — entity-existence hallucination rates 14–95% across 13 LLMs × 40 domains.
- **HaluBench finance domain rates** persistently exceed general-purpose rates, which matters because marketing-audit competitor analysis sits at the intersection of business-entity facts and quantified claims (pricing, ARR, customer count).
- **FAITH (arxiv 2508.05201) financial-entity numerical statements** — the same 17–46% intrinsic hallucination rate applies when the audit cites competitor pricing or ARR.
- **NeurIPS 2025 100-citation incident (arxiv 2602.05930)** — 100 AI-generated hallucinated citations in 53 published papers; Total Fabrication 66%, Partial Attribute Corruption 27%, Identifier Hijacking 4%. The "Partial Attribute Corruption" shape — real entity, fabricated attribute — is the most dangerous for marketing audits because it survives surface-level fact-checking (the competitor exists; just the cited attribute doesn't).

**Production retrospectives.**

- **Apple Intelligence news-summaries withdrawal (early 2025)** — the structural analogue: a real company gets a fabricated attribute (a named shooter, a verdict, a quote). Marketing-audit translation: a real competitor gets a fabricated pricing tier or customer logo.
- **Deloitte $290K Australian-government report (2025)** — partial refund after LLM-generated content contained hallucinated entities and citations. Reputational cost of letting these through is well-documented now.

**Why human consultants don't do this at the same rate.** Competitor pricing pages can be fetched; positioning gets read from the competitor's actual landing page; customer logos appear in case-study pages. Human auditors either verify or flag. The LLM failure mode is again the priors-fill-the-gap: when competitor data is absent, plausible-sounding values get generated.

**Detection patterns.**
- **Competitor-claim source check** — every competitor pricing, positioning, customer-logo, or channel claim must have an inline citation pointing to a retrieved competitor source (URL, screenshot, press release).
- **URL HEAD-check on competitor sources** — same pattern as the CI lane: cited competitor URLs must resolve.
- **Entity-existence verification on competitor names** — Wikidata / Crunchbase / SEC EDGAR lookup for any competitor named in the audit.
- **"According to" / "reportedly" / "industry-standard" pattern grep** — same forbidden-weasel-word list as the CI lane.

---

## 5. Q4 — Marketing-misdiagnosis bias: over-blaming marketing when the root cause is upstream (~420 words)

**The failure mode.** When the actual binding constraint on growth is product, pricing, positioning, sales motion, or PMF, the LLM defaults to marketing-shaped diagnosis ("you need more inbound," "your funnel needs a paid-acquisition layer," "your demand-gen mix should diversify"). The LLM analogue of Sean Ellis's "the bottleneck isn't marketing" failure mode — but stronger.

**Why the LLM bias is *stronger* than the human bias.** Human consultants have two anti-marketing-bias forces: (1) Bell Curve / Kalungi / Sean Ellis / Brian Balfour are explicitly in the literature saying "check upstream first"; (2) a human marketing consultant who recommends pausing their own engagement is conceding billable work. The first force is in the human's reasoning toolkit; the second is in their (perverse but useful) economic incentive to not say "we should engage someone else."

The LLM's training corpus is dominated by marketing-blog content where marketing is *always* the answer. Marketing-blog content does not survive selection if the conclusion is "this isn't a marketing problem." So the LLM's priors are skewed toward marketing-shaped explanations by training-data construction.

**The structural-consistency frame.** Eidoku (arxiv 2512.20664) reframes hallucination: "LLMs frequently produce hallucinated statements assigned high likelihood by the model itself, suggesting hallucination is often a failure of structural consistency rather than low-confidence." Marketing-misdiagnosis bias is structural-consistency-driven: the audit is a marketing audit, so the natural completion is a marketing-shaped recommendation regardless of upstream signal.

**Sycophancy and CoT-rationalization compound this.** "Good Arguments Against the People Pleasers" (arxiv 2603.16643) and BrokenMath (arxiv 2510.04721) show CoT *increases* this failure mode — the LLM commits to marketing-as-diagnosis early, then generates rigorous-sounding reasoning to defend the commitment. Forcing chain-of-thought before scoring (which the design guide §6 prescribes) helps the judge but does not necessarily help the LLM author. The author's CoT defends the marketing diagnosis; the judge's CoT must independently verify whether upstream evidence was engaged.

**Documented evidence is thin in the literature.** No paper has specifically measured "marketing-misdiagnosis bias rate" — this gap is genuinely open. But the structural ingredients are well-documented:

- **Training-corpus skew toward marketing-as-answer** (general industry observation; no direct citation).
- **Sycophancy + CoT-rationalization (arxiv 2603.16643, 2510.04721)** — LLMs generate rigorous-sounding justifications for the early commitment.
- **Domain-specific bias in finance (FAITH, arxiv 2508.05201; FactSet 2025 retrospective)** — analogous "stay in domain" priors over-extend to specific quantified claims; the same shape extends to marketing-audit domain.
- **Eidoku (arxiv 2512.20664)** — structural-consistency-driven hallucination.

**Why MA-5 (upstream problem) catches this — partially.** MA-5 ("when the binding constraint is upstream, does the audit say so plainly") is the design guide's defense. Score 1 requires the audit to name an upstream constraint and sequence behind it. Score 0 is "the audit always recommends more marketing."

**But MA-5 is insufficient on its own because:**
- The judge has to *recognize* upstream signal from the artifact alone. If the LLM author confabulates the upstream signal away ("retention is fine, churn is 2.4%" when actual churn is 6.4%), MA-5 scores 1 on the wrong basis.
- MA-5 is binary-permissive: an audit that engages upstream-vs-marketing for *one* dimension but defaults to marketing on the other four can still score 1.
- MA-5 does not catch the *subtle* misdiagnosis — recommending "improve onboarding messaging" when the actual constraint is product onboarding UX (a positioning-vs-product distinction the audit can blur).

**Detection patterns.** This is the failure mode that *cannot* be fully deterministic — root-cause attribution requires semantic judgment. Possible mitigations:

- **Forced-anti-marketing-hypothesis prompting.** Workflow-side: every audit generation must engage "what if the binding constraint is NOT marketing?" as an explicit alternative.
- **Upstream-signal-grep in `structural_gate`** — the audit must contain at least one explicit consideration of retention / PMF / pricing / sales / product as a candidate constraint, even if the conclusion is "marketing is still the binding constraint, and here's why."
- **Justified-breach 6th criterion MA-6 "Diagnosis survives blame-attribution check"** — see §8 below.

---

## 6. Q5 — Recommendation hallucination: wrong-stage / wrong-vertical tactics (~330 words)

**The failure mode.** The LLM recommends tactics that don't apply to the client's stage / vertical / ARR band / sales motion. This is the LLM analogue of the practitioner-named "wrong-stage best practices" failure mode (Kalungi SaaS-growth-stages; Brian Balfour four-fits; Reforge premature scaling) — but at higher rate and harder to detect because the LLM's recommendations are usually *named* correctly (ABM tooling does exist; paid-LinkedIn pilots are a thing; product-led growth motions are real) — they just don't fit.

**Three sub-shapes:**

- **Stage mismatch.** ABM tooling recommended to a $1.8M ARR company (too early — ICP signal too noisy to target accounts at scale). Or paid-acquisition diversification recommended at $20M ARR when the company is still single-channel and the right move is to deepen the working channel.
- **Vertical mismatch.** SaaS-style PLG tactics recommended to a healthcare-services or legal-services firm where the buyer journey is committee-mediated. B2C influencer playbook recommended to a B2B SaaS.
- **Sales-motion mismatch.** Product-led growth tactics recommended to a sales-led company; enterprise ABM recommended to a self-serve SMB.

**Documented evidence.**

- **LLMLagBench (arxiv 2511.12116)** — temporal cutoffs cause LLMs to reason from older market priors; a 2024-cutoff model recommending ABM-tooling-as-2024-best-practice projects that into a 2026 context where the tactic has shifted.
- **"Is Your LLM Outdated?" NAACL 2025** — 23–35% accuracy drop on relative-date reasoning.
- **Practitioner literature** — Reforge "premature scaling" pattern; Kalungi's named "applying earlier-stage logic at scale is the most common strategic mistake"; Brian Balfour's four-fits ecosystem framing.

**Why the LLM does this at higher rate than humans.** Human consultants have the client's actual ARR / vertical / sales motion in front of them; recommendations are constructed around those facts. The LLM has access to those facts in the input but its priors push toward "well-known SaaS playbook" regardless. The latent-space gradient for "B2B SaaS audit" recommends the modal B2B-SaaS playbook even when the actual ARR or vertical breaks the modal assumptions.

**Detection patterns — deterministic part lives in `structural_gate`.**

- **Stage-applicability gate.** From the input fixture, extract the client's ARR band, vertical, and sales motion. Maintain a per-stage / per-vertical recommendation allowlist + denylist. Reject audit recommendations that hit the denylist for the client's stage. (Example: ABM tooling on the denylist for sub-$5M ARR; B2C influencer playbook on the denylist for B2B SaaS.)
- **"Sales motion conflict" detection.** If the audit recommends product-led growth tactics AND the input names a sales-led motion (named SDR/AE team, named outbound process), flag.

**Semantic part lives in the judge — MA-4 already covers this.** MA-4 score-0: "applies the same playbook regardless of stage." This is the right criterion home for the *semantic* version of the failure mode. The deterministic gates filter the worst surface-level wrong-stage tactics; MA-4 handles the subtle cases.

---

## 7. Cross-cutting — what MA v0 catches vs misses (~430 words)

Walk each MA v0 criterion against the 5 failure modes:

| Criterion | Q1 Financial-metric | Q2 Channel-claim | Q3 Competitor-data | Q4 Misdiagnosis | Q5 Wrong-stage tactic |
|---|---|---|---|---|---|
| MA-1 binding constraint | partial | partial | NO | partial | NO |
| MA-2 30-day experiment | NO | NO | NO | NO | partial |
| MA-3 revenue chain | partial | partial | NO | NO | NO |
| MA-4 stage map | NO | NO | NO | NO | YES (semantic) |
| MA-5 upstream problem | NO | NO | NO | partial | NO |

**What MA v0 actually catches:**

- **Q5 wrong-stage tactic (semantic level):** MA-4 ("locates company on stage map + refuses wrong-stage best practices") directly targets this. Score 1 requires explicit stage-grounded refusal of at least one tactic. Score 0 is "applies the same playbook regardless of stage." This is well-designed.
- **Q4 misdiagnosis (partial):** MA-5 targets the upstream-vs-marketing question — but only at the macro level (retention, PMF, ICP, pricing, sales motion as candidate non-marketing constraints). It does not catch the subtler within-marketing misdiagnosis (positioning vs message vs channel mix).
- **Q1 financial-metric (partial):** MA-1 requires "at least two evidence sources." A judge might catch a single-source confabulated metric. But the judge cannot verify the source actually contains the cited number — that's structural_gate's job.
- **Q2 channel-claim (partial):** MA-1's evidence-source requirement applies; same caveat — the judge can't verify the source.

**What MA v0 does not catch at all:**

- **Q1 Financial-metric confabulation (deterministic part):** zero coverage in `structural_gate`. No metric-citation grep, no source-corpus numerical match, no aggregation-without-math flag.
- **Q3 Competitor-data confabulation:** zero coverage. No competitor-URL HEAD-check, no entity-existence lookup, no pricing-source verification.
- **Q2 Channel-claim fabrication (deterministic part):** zero coverage. No channel-claim source check.

**The asymmetric risk for MA specifically.** A marketing audit that confabulates the client's CAC payback, invents three plausible channel-performance claims, names a fabricated competitor pricing tier, and over-blames marketing for an upstream-pricing problem can still score *high* under MA v0:

- MA-1 = 1 (constraint named with "evidence" — judge can't verify the confabulated metric).
- MA-2 = 1 (concrete 30-day experiment, owner, budget, metric tied to fabricated baseline).
- MA-3 = 1 (revenue chain runs through fabricated metric to fabricated forecast).
- MA-4 = 1 (stage named, recommendation refused on stage grounds — independent of the fabrications).
- MA-5 = 0.5 or 1 (depends on whether the LLM confabulates *away* the upstream signal).

Worst case: 4-5/5 score on an audit that's structurally fabricated. This is the architectural gap.

**Compared to CI:** the MA architectural gap is *worse* than the CI gap on financial-metric confabulation specifically — marketing audits are quantitative-by-construction in a way CI briefs are not. CAC, LTV, payback, churn, NRR, trial-to-paid are the dominant claim shape in MA. Each cited metric is a fabrication-surface.

---

## 8. Recommendation — where should AI-failure detection live? (~420 words)

**Recommended split — by failure mode:**

| Failure mode | Best home | Why |
|---|---|---|
| Q1 Financial-metric confabulation | `structural_gate` | Deterministic: metric-citation grep, source-corpus numerical match (±5% tolerance), aggregation-without-math flag, forbidden-weasel-formulation grep. Cheap. Binary pass/fail. |
| Q2 Channel-claim fabrication | `structural_gate` | Deterministic: channel-claim source check (inline citation to analytics / Gong / campaign report required for any channel-performance claim). Forbidden-formulation grep. |
| Q3 Competitor-data confabulation | `structural_gate` | Deterministic: competitor-URL HEAD-check, entity-existence lookup (Wikidata / Crunchbase / SEC EDGAR), pricing-source verification, "Partial Attribute Corruption" detection (real competitor + cited attribute must trace to real source). |
| Q4 Marketing-misdiagnosis bias | judge (MA-5 + possible MA-6) + workflow | Semantic — requires reasoning about whether the audit *engaged* upstream evidence on the merits. Deterministic gate can require *presence* of an upstream-vs-marketing consideration (`upstream-signal-grep`); judge tests whether the consideration was substantive. |
| Q5 Wrong-stage tactic | `structural_gate` (denylist) + judge MA-4 (semantic) | Worst surface-level cases filtered by per-stage / per-vertical denylist; MA-4 catches the subtler cases. |

**Concrete `structural_gate` edits for `_validate_marketing_audit()`:**

1. **Metric-citation grep.** Any number formatted as `\d+(\.\d+)?%`, `\$\d`, `\d+x`, `\d+ months`, or `\d+:\d+ ratio` in the audit body must be followed within 200 chars by an inline citation (URL, "(source: ...)", or footnote marker). Bare numbers fail.
2. **Source-corpus numerical match (cohort-A).** Phase 1: for each cited metric with a source attribution, verify the exact number (±5% tolerance) appears in the named source document. Stretch goal — implement after Phase 1 has measured the prevalence.
3. **Channel-claim source check.** Any channel-performance claim ("X is your dominant channel," "Y is working," "Z has stalled") must cite a specific source artifact. Forbidden formulations: "industry-standard," "typical SaaS," "we see this often" without inline citation.
4. **Competitor-URL HEAD-check.** Any cited competitor URL must resolve. Any competitor named without a URL or supporting source fails.
5. **Stage-applicability denylist.** Maintain `~/docs/rubrics/ma-stage-denylist.yaml` mapping ARR-band × vertical × sales-motion to a list of denied recommendations. Reject audits that hit the denylist.

**Concrete judge edit — consider justified-breach MA-6:**

**MA-6 — Diagnosis survives blame-attribution check (CANDIDATE, pending redundancy verification).**

Outcome question: Does the audit's diagnosis survive the test that *if marketing were not the constraint*, the audit would still recommend the same primary action? Or does it default to marketing-shaped recommendations because the audit is a marketing audit?

Score 1 (yes): The audit engages at least one non-marketing alternative on the merits — naming a specific upstream signal (retention cohort, PMF survey score, pricing-model conflict, sales-motion misalignment) and either confirming marketing IS the constraint with evidence OR sequencing behind the upstream fix with named specific cost.

Score 0 (no): Audit treats marketing as the default explanation. No engagement with upstream signal. Or engages upstream signal at surface level then dismisses it ("retention is fine") without evidence.

Score 0.5 (unknown): Upstream signal acknowledged but the evidence to commit to marketing-vs-upstream is missing from the audit alone.

**Whether to ship MA-6:** This depends on the redundancy check. If MA-6 correlates >0.7 with MA-5 across re-runs on the calibration set, drop MA-6 and tighten MA-5 prose to capture the bias explicitly. If MA-5 correlates <0.7 with MA-6 (i.e., they catch different audit failures), retain MA-6 as a justified breach per design guide §5. **Expected outcome:** likely correlated with MA-5, so MA-6 probably absorbs. But ship the redundancy check to find out empirically rather than assuming.

**Why not put any of these in a new "AI-slop gate":** same architectural argument as the CI deliverable — the failure modes split cleanly into "deterministic + cheap" (Q1, Q2, Q3, deterministic part of Q5) and "semantic + judge-shaped" (Q4, subtle part of Q5). The deterministic checks belong in `_validate_marketing_audit()`; the semantic checks belong in the judge.

---

## 9. Concrete edits to MA v0 spec (~310 words)

**Edit 1 — Expand `structural_gate` requirements in §8 open questions:**

```
4. `structural_gate` expansion before spec ships:

   Anti-hallucination checks (each defends a documented LLM failure rate):
   - Metric-citation grep — any percentage / dollar / multiple / ratio
     in audit body must be followed by inline citation within 200 chars
     (defends Q1 financial-metric confabulation; FAITH 17–46% rate)
   - Channel-claim source check — any channel-performance claim must
     cite analytics / Gong / campaign report (defends Q2 channel-claim
     fabrication)
   - Competitor-URL HEAD resolution — any cited competitor URL must
     resolve (defends Q3 competitor-data confabulation)
   - Entity-existence lookup on competitors (Wikidata / Crunchbase /
     SEC EDGAR) — defends Q3
   - "As of" date requirement — forces freshness signaling, catches
     post-cutoff blind spots (defends Q5 wrong-stage tactic from
     LLMLagBench)
   - Forbidden-formulation grep — "industry-standard," "typical SaaS,"
     "reportedly," "according to industry sources" without inline
     citation = structural failure

   Shape-conformance checks (enforce artifact-shape if/when locked):
   - Day-30/60/90 sequencing structure present
   - Top-3-recommendations vs full-list separation
   - Stage anchor present (ARR band, retention signal, channel-fit
     signal)

   Recommendation denylist:
   - Per-stage × per-vertical × per-sales-motion denied tactics list
     (defends Q5 wrong-stage tactic at surface)
```

**Edit 2 — Add §3b AI-specific failure surfaces** (parallel to the CI spec §3b):

```
### 3b. AI-specific failure surfaces

- Financial-metric confabulation. Audit invents CAC, LTV, NRR, MRR,
  ARR, payback, churn, trial-to-paid numbers that don't exist in
  source data. Documented at 17–46% intrinsic rates on financial-
  entity numerical statements (FAITH, arxiv 2508.05201).
- Channel-claim fabrication. LLM asserts specific channel-performance
  claims without analytics, Gong, or campaign-report evidence —
  driven by marketing-blog training-corpus priors.
- Competitor-data confabulation. Pricing tiers, positioning claims,
  customer logos, executive moves on competitors that don't exist or
  are misattributed (HalluLens 14–95% across 13 models × 40 domains).
- Marketing-misdiagnosis bias. LLM over-attributes problems to
  marketing causes because training-corpus is dominated by marketing-
  blog content where marketing is the answer. Sycophancy + CoT-
  rationalization compound (arxiv 2603.16643, 2510.04721).
- Recommendation hallucination. Wrong-stage / wrong-vertical / wrong-
  sales-motion tactic recommendations driven by latent-space gradient
  toward modal B2B-SaaS playbook regardless of input specifics.

Deterministic AI-failure checks live in `structural_gate` (§8 above).
Semantic AI-failure checks live in MA-5 (upstream-vs-marketing) and,
pending redundancy check, possibly MA-6 (blame-attribution).
```

**Edit 3 — Decide MA-6 after redundancy check.** Don't commit to a 6-criterion spec until the redundancy check on 5 fixtures × 6 criteria × 3 panel models confirms MA-6 does not correlate >0.7 with MA-5. Expected outcome is absorption; if so, tighten MA-5 prose instead of adding a criterion.

---

## 10. Open Questions

1. **MA-6 vs MA-5 redundancy.** Will MA-6 (blame-attribution) collapse into MA-5 (upstream problem) on the calibration set? Most-likely outcome: yes. But the empirical check is needed before locking. If they collapse, MA-5 prose should pull the "marketing-misdiagnosis bias" framing into it; if they don't, MA-6 is a justified breach per design guide §5 with the specific literature backing (Eidoku 2512.20664, sycophancy 2603.16643, marketing-corpus training-skew structural argument).

2. **Source-corpus numerical match feasibility.** The deterministic metric-citation grep is trivial; verifying that the cited source *contains* the cited number with ±5% tolerance is harder (requires source-corpus indexing). Phase 1 should ship the citation-presence check; Phase 2 (if metric-confabulation prevalence justifies it after measurement) ships the numerical match.

3. **Stage-applicability denylist maintenance.** A YAML file mapping (ARR-band × vertical × sales-motion) → denied tactics needs JR sign-off on the initial entries. Risk: the denylist becomes a feature checklist (a tactic gets added because it sounds bad on paper, then a legitimate use case gets blocked). Mitigation: keep entries narrow and document each with the specific failure-mode citation.

4. **Marketing-misdiagnosis bias rate measurement.** No published paper has measured this directly. Possible follow-up: instrument the lane to ask the judge "did the audit engage upstream-vs-marketing on the merits?" as a separate flag, log per-fixture results, then read the rate over 30 days. This is the missing dataset.

5. **Channel-claim source-corpus matching.** Marketing audits often cite client-internal channel data (HubSpot, GA4, Stripe). The deterministic check requires the workflow to expose those source artifacts to `structural_gate`. Workflow-side change: ensure analytics screenshots / exports are passed as named source documents to the gate.

6. **Vertical-specific MA failure modes.** Healthcare-services audits (Klinika-class) and legal-services audits (DWF-class) have different channel-mix priors than B2B SaaS. The B2B-SaaS-corpus skew documented in Q4 (marketing-misdiagnosis bias) may differ for these verticals. Re-validate when non-SaaS fixtures land.

---

## Citations with effect sizes

**Financial-metric confabulation (Q1):**
- FAITH — arxiv 2508.05201 — 17–46% intrinsic hallucination rates on financial-entity numerical statements
- "Detecting AI Hallucinations in Finance" — arxiv 2512.03107 — 92% reduction with information-theoretic detection (implies non-trivial baseline)
- BloombergGPT deficiency study — arxiv 2311.15548 — canonical "fabricated earnings against non-existent press release" shape
- FactSet 2025 retrospective (Institutional Investor 2025; arxiv 2512.19705) — **59% higher forecast error** in AI-assisted analyst reports
- HaluBench — Ravi et al. 2024 — 15K samples across finance/medical/general; finance domain rates persistently elevated

**Channel-claim and competitor-data confabulation (Q2 + Q3):**
- HalluLens — arxiv 2504.17550
- HalluEntity — arxiv 2502.11948 (18,785 entity-level annotations)
- KGHaluBench — arxiv 2602.19643 — 14–95% across 13 LLMs × 40 domains
- GhostCite — same range
- NeurIPS 2025 100-citation incident — arxiv 2602.05930 — Total Fabrication 66%, Partial Attribute Corruption 27%, Identifier Hijacking 4%
- Sports Illustrated 2023 fake author biographies (Futurism, multiple)
- Apple Intelligence news-summary withdrawal early 2025 (BBC retrospective)
- Deloitte $290K Australian-government report partial refund 2025

**Marketing-misdiagnosis bias and CoT-rationalization (Q4):**
- BrokenMath sycophancy benchmark — arxiv 2510.04721
- "Good Arguments Against the People Pleasers" — arxiv 2603.16643 — CoT generates rigorous-sounding justifications for the early commitment
- "Verbalizing LLMs' assumptions to explain and control sycophancy" — arxiv 2604.03058
- Eidoku — arxiv 2512.20664 — hallucination as failure of structural consistency rather than low-confidence
- Anthropomimetic Uncertainty — arxiv 2507.10587 — verbalized uncertainty poorly calibrated
- "Calibrating LLM Judges: Linear Probes" — arxiv 2512.22245

**Recency / training-cutoff / wrong-stage tactics (Q5):**
- LLMLagBench — arxiv 2511.12116 — empirically identifies temporal knowledge boundaries; multiple partial cutoff points per model
- ProofTeller — aclanthology 2025.ijcnlp-long.80 — recency bias in LLM reasoning
- "Is Your LLM Outdated?" NAACL 2025 — 23–35% accuracy drop on relative vs absolute date reasoning
- Recency bias in LLM-based reranking — arxiv 2509.11353 — LLM rerankers favor recent over relevant

**Detection / mitigation patterns:**
- FinDER — arxiv 2504.15800 (sentence-level source attribution)
- FinRAGBench-V — arxiv 2505.17471
- "Detecting and Correcting Reference Hallucinations" — arxiv 2604.03173 — web-search-grounded models still hallucinate 3–13% of URLs
- TrustJudge — arxiv 2509.21117
- UQ Survey KDD 2025 — arxiv 2503.15850

**Practitioner literature for upstream-vs-marketing diagnostic (Q4 anti-bias force):**
- Sean Ellis PMF survey — 40%-very-disappointed threshold; the canonical instrument for "is the bottleneck upstream of marketing?"
- Kalungi one-page marketing-readiness audit — explicit "marketing CAN succeed at current state?" gate
- Patrick Campbell / ProfitWell pricing-as-marketing-lever — pricing routinely surfaces as binding constraint
- Wynter messaging-resonance audit (Peep Laja) — surfaces positioning gap before channel work
- Brian Balfour four-fits — Market-Product / Product-Channel / Channel-Model / Model-Market as ecosystem

**Existing MA v0 spec context:**
- `docs/handoffs/2026-05-18-judge-design-step1-marketing-audit.md` (v0 DRAFT)
- `docs/research/2026-05-18-judges-domain-marketing-audit.md` (human-MA framework synthesis)
- Likely `src/evaluation/structural.py` `_validate_marketing_audit` (pattern from `_validate_competitive`, current shape-only checks)
