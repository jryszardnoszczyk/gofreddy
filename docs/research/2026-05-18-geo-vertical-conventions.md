---
date: 2026-05-18
type: research deliverable
status: complete (1 of 4 GEO axis dispatches for Path-A synthesis)
topic: GEO/AEO vertical-specific conventions (legal / healthcare / B2B SaaS / fintech / AI labs / DTC e-commerce / professional services)
parent: docs/handoffs/2026-05-18-judge-design-step1-geo.md
sibling: docs/research/2026-05-15-judges-domain-geo.md
pattern_reference: docs/research/2026-05-18-ci-vertical-conventions.md
---

# Vertical-Specific Conventions in GEO/AEO Content
## How the citation substrate, page shape, and gating regime change per vertical — what the GEO judge rubric must accommodate

**Companion to:** `2026-05-15-judges-domain-geo.md` (generalist Aggarwal / Volpini / Shepard / Profound synthesis). This pass goes vertical-specific so the GEO lane's rubric does not silently optimize for a single archetype.

**Why this exists.** The v0 spec at `docs/handoffs/2026-05-18-judge-design-step1-geo.md` assumes one reader archetype: a researcher querying ChatGPT / Perplexity / Google AI Mode about a category. The fixture cohort the lane actually grades against — DWF legal services, Anthropic / Perplexity AI-lab pages, Klinika aesthetic dermatology — is three structurally distinct evidence-substrate verticals. A page that earns 5/5 against Anthropic.com reader-intent could earn 2/5 against Klinika reader-intent (and vice versa) for reasons that are citation-source norms, regulatory gating, and query-class match, not authorship quality. If the rubric doesn't see that, a 50-generation evolution loop will overfit to whichever vertical happens to dominate the fixture set — and the failure surface is documented in the CI lane's own vertical-conventions pass.

This deliverable closes the GEO equivalent of that gap on the vertical-conventions axis. It does NOT cover artifact-taxonomy (single-page vs hub vs site), AI-specific failure modes (entity confabulation, source hallucination, recency cutoff), or dual-audience reasoning (human researcher vs engine). Those are separate dispatches.

---

## 1. TL;DR

- **The GEO evidence substrate is structurally divergent across ≥5 verticals.** Legal / healthcare / fintech enforce YMYL gating (E-E-A-T weight inflated, named-author + jurisdiction required, hallucination liability shifts citation toward government / NICE / FDA / SEC / Mayo Clinic tier). B2B SaaS routes citations through review aggregators (G2, Capterra, TrustRadius, Gartner Peer Insights) — the brand's own site competes against a structured-data fortress and almost always loses on category prompts. AI-labs route citations through arxiv / GitHub / model-cards / analyst Substacks (Interconnects, Stratechery, Latent Space) — the developer documentation IS the citation substrate. DTC e-commerce now runs through agentic-commerce protocols (ACP/UCP) where structured Product schema, Reddit reviews, and recency in unit price/availability outrank brand storytelling. Professional services (consulting/accounting) wins through head-to-head comparison editorial published on the brand's own domain.
- **The highest-leverage page shape is vertical-specific, not category-uniform.** Legal: jurisdiction-scoped FAQ + author-attributed long-form explainer with cited primary sources (statute / regulation / case). Healthcare: clinician-authored evidence-based explainer with named guideline references (NICE / USPSTF / AAD) + medical reviewer byline + last-medically-reviewed date. B2B SaaS: head-to-head comparison page with tables built on first-party product data + structured-data schema. Fintech: regulator-aligned definitional explainer + risk disclosure + named-jurisdiction scope. AI-labs: declarative reference-document register API/SDK docs + benchmark cards with reproduction methodology + dated changelog. DTC: schema-rich product page + UGC review surfacing + structured comparison + recency-stamped pricing/availability. The same workflow optimizing every fixture toward the same shape mis-fits 4 of 7 verticals.
- **YMYL gating is real and binary, not a soft preference.** Healthcare, legal, and financial-advice queries trigger different citation-confidence thresholds inside Perplexity (21+ sources per medical answer; preferential weighting of PubMed / clinical-guidelines / .gov / academic-medical-center domains), inside ChatGPT (Mayo Clinic, NICE, USPSTF cited preferentially; commercial healthcare brand citations are de-weighted unless paired with named-clinician byline), and inside Google AI Mode (AI Overviews appear on 23.6% of legal queries but with stronger reluctance to cite single-firm sources without statute attribution). A GEO rubric that scores YMYL pages the same as a B2B SaaS landing page will reward surface-marker compliance that doesn't actually earn the citation.
- **The Aggarwal et al. KDD 2024 paper's most under-cited finding is the domain-conditioning of which optimization method wins.** Statistics Addition wins for Law & Government and Opinion; Quotation Addition wins for People & Society and History; Fluency Optimization wins for Health and Business; Easy-to-Understand wins for hard-science domains. The judge's evidence-density criterion (GEO-2) currently doesn't know this — it treats stats / quotes / citations as a uniform high-density requirement, when the empirically winning tactic per vertical differs.
- **First-cohort overfit risk: real.** gofreddy's first-cohort fixture set (DWF legal, Anthropic/Perplexity AI-lab, Klinika healthcare) covers three of the divergent-evidence verticals but misses B2B SaaS, fintech, DTC, and professional services — the ones a generic AI-native agency will most likely onboard next. Three concrete recommendations below address this without breaking the design-guide §5 ≤5-criterion ceiling.

---

## 2. Key questions — verbatim restated with verdicts

**Q1: How does optimal AEO/GEO content shape vary across legal, healthcare (aesthetic medicine), B2B SaaS, fintech, AI labs, DTC e-commerce, professional services? Identify ≥5 verticals where the EVIDENCE SUBSTRATE differs structurally.**

**Verdict: ≥7 verticals are structurally distinct on the evidence-substrate axis.** Legal (statute + case + bar-association); healthcare (NICE / USPSTF / WHO / PubMed / Mayo Clinic + named-clinician byline); B2B SaaS (G2 / Capterra / TrustRadius / Gartner Peer Insights as gatekeeper aggregators); fintech (SEC / CFPB / FCA / regulator-aligned + jurisdiction-scoped + risk disclosure); AI-labs (arxiv / GitHub / model-cards / analyst Substacks); DTC e-commerce (Product schema + Reddit / YouTube reviews + agentic-commerce-protocol metadata); professional services / consulting / accounting (head-to-head competitor comparisons published on brand's own domain, e.g., Xero-vs-QuickBooks, NetSuite-vs-Sage-Intacct). Section 3 details each. See §3.1–§3.7.

**Q2: Within each vertical, what is the highest-leverage page shape for AI-engine citation?**

**Verdict: page shape varies; FAQ / how-to / comparison / glossary / hub all win in different verticals.** Legal → jurisdiction-scoped FAQ + author-attributed long-form explainer. Healthcare → clinician-authored evidence-based explainer + glossary + procedure-comparison hub. B2B SaaS → head-to-head comparison page with tables + alternatives hub. Fintech → regulator-aligned definitional explainer + risk-disclosure FAQ. AI-labs → declarative reference-document API/SDK docs + benchmark card. DTC → schema-rich product page + comparison + UGC review surfacing. Professional services → head-to-head comparison editorial + named-author insight piece. See §4.

**Q3: Are there verticals where AEO is meaningfully blocked by regulation, gating, or paywall structure (legal disclaimers, medical YMYL, financial advice)?**

**Verdict: yes — three verticals operate under hard YMYL gating with citation-confidence thresholds that materially change what content gets cited.** Healthcare (E-E-A-T inflation; Perplexity 21+ source medical answer; preferential clinical-guideline / academic-medical-center citation). Legal (jurisdiction-scoped; AI Overviews appear on 23.6% of legal queries; statute + case attribution required). Fintech / financial advice (FINRA / SEC / CFPB / FCA + multi-jurisdiction layering; AI platforms cautious about recommending specific products, prefer educational / balanced / non-promotional content). See §3 per vertical and §5 cross-vertical synthesis.

**Q4: What divergent vertical anchors should the GEO judge rubric use to avoid first-cohort overfit on DWF/Klinika/Anthropic specifically?**

**Verdict: anchor across at least 5 structurally divergent verticals in score-1 examples per criterion (legal / healthcare / B2B SaaS / fintech / AI-lab as the load-bearing set; DTC and professional services as optional 6th/7th).** First-cohort fixtures cover 3 of these (legal-DWF, healthcare-Klinika, AI-lab-Anthropic/Perplexity); B2B SaaS, fintech, DTC are likely-next-cohort verticals (a generic AI-native agency targeting tech-savvy founder/early-co clients per JR's framing). See §6 recommendations.

---

## 3. Research synthesis — vertical-by-vertical evidence substrate

### 3.1 Legal services (DWF context; expanded beyond first-cohort)

**Citation substrate.** YMYL category. AI Overviews trigger on 23.6% of legal queries; for question-style searches the rate is 57.9%, and for 7+ word high-intent queries 46.4% (Lexicon Legal Content / SEM Nexus 2026 data). When AI Overviews appear, click-through to traditional results drops 34.5%, and only 8% of users click below the AI summary (vs 15% without one). Citation-confidence threshold is elevated because hallucination liability in legal advice is high — AI platforms preferentially cite (a) primary sources: statute text, regulation, agency rule, case law (Westlaw / Lexis citations frequently); (b) bar-association resources (state bar / Law Society); (c) law firm content that is jurisdiction-scoped and attorney-attributed; (d) institutional aggregators (Nolo, FindLaw, Justia) that traditionally dominated featured snippets. The single most-cited tier is government and bar-association — Cleveland Clinic / Mayo Clinic's role in healthcare is played by .gov primary-source domains in legal.

**Highest-leverage page shape.**
- **Jurisdiction-scoped FAQ** — "Can I X in [state]?" with named-jurisdiction statute citation. Each FAQ is a single 75-150 word atomic answer block; the page hosts 5-12 of them.
- **Author-attributed long-form explainer** — 1500-3000 word piece with attorney byline, bar number where relevant, last-reviewed date, statute and case citations inline. The byline is load-bearing because YMYL E-E-A-T scoring inflates the named-author signal.
- **Comparison hub** — "Differences between X and Y" structured as a table with each row sourced to statute or case.

**Gating regime.** SRA (UK Solicitors Regulation Authority) / state-bar rules govern attorney advertising — claims of expertise without substantiation are disciplinable, "specialist" / "expert" labels often require certification. Disclaimers ("This article is for informational purposes only…") are operationally mandatory. These constraints translate directly into rubric behavior: a page that earns high citation in legal will read more conservatively than a high-citation B2B SaaS page; the rubric should not penalize that register.

**Failure modes specific to legal GEO.**
- **Generic-jurisdiction theater.** Page claims "in most states" without naming a state, or claims federal rules but cites state cases. AI engines that detect the mismatch de-rank.
- **Self-as-precedent.** Firm cites its own articles as authority; engine reads this as link farm.
- **Unattributed legal claim.** "Courts have ruled…" without naming the case is treated as marketing not law.
- **Promotional register on YMYL.** "We are the best X attorneys" reads as marketing; AI platforms preferentially cite educational / balanced over promotional in YMYL categories.

### 3.2 Healthcare / aesthetic dermatology (Klinika context; expanded with broader medical)

**Citation substrate.** YMYL category with the highest gating threshold of any vertical surveyed. Perplexity returns 21+ sources per medical answer on average (DoctorRank 2026), preferentially weighting PubMed, ClinicalTrials.gov, named clinical guidelines (NICE, USPSTF, WHO, AAD/ASDS), academic medical centers (Mayo Clinic, Cleveland Clinic, Johns Hopkins), and .gov (CDC, NIH, FDA). Mayo Clinic citation is a baseline expectation for ChatGPT / Claude / Perplexity health responses — competing on health queries against Mayo Clinic and WebMD's structural-authority moat is hard; the practical strategy is to win local-aesthetic / procedure-specific or specialty-niche queries where the institutional sources are thinner.

For aesthetic dermatology specifically (Klinika): the substrate splits into two tiers. National / procedure-defining queries ("what is Botox," "Botox vs Daxxify") are dominated by Mayo Clinic / WebMD / AAD. Local / practice-comparison queries ("best Botox clinic in Warsaw") route through Google Maps local pack (40-60% of mobile local click share), RealSelf (10M unique monthly visitors), Healthgrades, and Yelp — the AI Overview frequently surfaces the local pack as its primary citation substrate. The aesthetic-derm practitioner wins on local before national.

**Highest-leverage page shape.**
- **Clinician-authored evidence-based explainer** with medical-reviewer byline (Director of Medical Affairs, MD, FAAD), last-medically-reviewed date, named guideline references inline (USPSTF Grade B, NICE NG-X, AAD Clinical Practice Guideline), and clear disclaimer separating informational content from clinical advice.
- **Procedure-comparison glossary** — "Botox vs Dysport vs Daxxify" structured as a clinically-grounded comparison table sourced to FDA labels + AAD position statements + peer-reviewed comparative trials.
- **Local procedure page** — practice-level page with named injector, certification, before-after gallery (with consent and disclaimer), procedure-specific FAQ, and embedded local-pack metadata (NAP — Name / Address / Phone consistency across the digital footprint).

**Gating regime.** FDA off-label regulations restrict claims about medication uses; state medical board scope-of-practice rules vary (Colorado Rule 800 differs from Texas differs from California); HIPAA constrains how before/after photos and patient stories can be used; advertising of aesthetic procedures has been subject to FTC enforcement (Allergan / Botox marketing settlement precedents). These constraints mean a "high-converting" aesthetic page that wouldn't pass medical-board / FDA scrutiny is also a page AI engines preferentially de-rank.

**Failure modes specific to healthcare GEO.**
- **Commercial-brand framing on YMYL.** Page reads as marketing for a clinic rather than as patient education with clinic context.
- **Missing clinician attribution.** No named author, no review-by, no clinical credentials.
- **Stale medical-review date.** Guideline-citing pages with last-reviewed > 24 months are de-weighted (medical guidelines change; AI engines have learned to prefer fresh medical content per Perplexity's 12-18 month freshness pattern + Ahrefs medical-vertical freshness skew).
- **Treatment-as-feature-comparison without clinical context.** "Botox vs Daxxify pricing" without clinical-indication / efficacy / safety context fails healthcare E-E-A-T.
- **Local NAP drift.** Practice name / address / phone variations across Google Business Profile, RealSelf, Healthgrades, Yelp, practice website → embedding cluster fragmentation → reduced local citation.

### 3.3 B2B SaaS

**Citation substrate.** Structurally distinct from YMYL verticals — the gatekeeper is the review aggregator, not government / clinical guidelines. G2 has 4.1% citation share (the single largest source in AI answer generators for B2B software queries); Gartner holds 28.7% of organic SERP positions on B2B SaaS queries. G2's January 2026 acquisition of Capterra, GetApp, and Software Advice (formerly Gartner Digital Markets) consolidated this position — those four directories now operate as "G2 Digital Markets," structurally fortifying the aggregator moat. TrustRadius and Gartner Peer Insights weight more heavily with enterprise procurement teams; SourceForge and PeerSpot fill long-tail. As of 2026, 51% of B2B software buyers start their purchase process in an AI chatbot rather than traditional search (up from 29% a year earlier; techedgeai.com Gartner reporting), and AI answers typically pull from 3-6 domains per query vs ~10 for traditional SERPs — citation concentration is sharply higher.

The strategic implication is that a SaaS brand's own landing page almost never wins category-prompt citation against G2 / Gartner / TrustRadius. The achievable win is on (a) head-to-head comparison pages built on the brand's own domain ("Stripe vs Adyen," "Linear vs Jira," "Notion vs Coda"), (b) alternatives pages ("alternatives to Mailchimp"), and (c) integration / use-case pages where the brand has unique first-party authority.

**Highest-leverage page shape.**
- **Head-to-head comparison page** with a structured-data feature/pricing/integration table built on first-party product data + at least one verifiable benchmark or stat with a dated source.
- **Alternatives hub** — "Best alternatives to X" with 5-7 named alternatives, structured comparison, and at least one external review citation (G2 / TrustRadius score) per alternative.
- **Integration / use-case page** scoped to a narrow buyer persona ("X for HR teams," "X for designers"), with named-customer case study evidence and verifiable outcome metrics.

**Gating regime.** No YMYL gating, but procurement-stage scrutiny is high — enterprise buyers validate AI claims against analyst reports (Gartner Magic Quadrant, Forrester Wave) and peer-review platforms before trusting. Schema.org Product / SoftwareApplication markup is operationally mandatory for AI Overview / Perplexity surfacing. Recent Forrester data: AI buyers validate vendor claims against external sources before trusting them.

**Failure modes specific to B2B SaaS GEO.**
- **Category-page brand-self-puffery.** "Leading X platform," "trusted by thousands" without external proof points → de-ranked.
- **Comparison page that always wins.** Page comparing own product against competitors where the home product wins every row → AI engines have learned to detect and discount (per The Verge documentation of Google AI Mode flagging vendor-authored best-of lists).
- **Missing G2 / TrustRadius integration.** No external review-platform validation in the page → "marketing-tone only" classification.
- **Stale pricing.** Pricing page without current-year stamp, or with pricing that contradicts a current G2 listing → de-weighted.

### 3.4 Fintech / financial advice

**Citation substrate.** YMYL category with multi-jurisdiction regulatory layering (SEC, FINRA, CFPB, OCC, FDIC at US-federal; FCA in UK; MAS in Singapore; RBI / SEBI / IRDAI in India). Citation preferences favor regulator-aligned content (SEC / FINRA filings, CFPB consumer guides, FCA handbook references) and educational / explanatory / comparative content from sources demonstrating clear expertise and balanced perspectives — promotional product-marketing material is preferentially de-cited. The October 2024 OCC guidance on generative AI explicitly notes model-risk management framework (SR 11-7) applies to AI use in financial services, meaning fintech content that claims AI-driven analysis must address the model-risk framing or lose institutional credibility.

**Highest-leverage page shape.**
- **Regulator-aligned definitional explainer** — "What is X (and how is it regulated)" with named-regulator citation and jurisdiction scope.
- **Risk-disclosure FAQ** — risk-stratified questions ("What happens if X fails," "Is X insured by FDIC/FSCS/etc") with primary-regulator citation.
- **Compliance-context comparison** — comparison of products / providers / methods with explicit regulatory-license disclosure per option ("X is a registered broker-dealer with FINRA member ID Y; Z is a state-chartered trust company").

**Gating regime.** Regulator-driven, with razor-thin margin for error: an AI engine that inaccurately describes a fintech's regulatory position, misrepresents product terms, or inaccurately references a competitor's fee structure is not just a citation issue — it's a compliance issue. This means fintech pages disclose more — disclaimers, license numbers, FDIC/FSCS coverage details, multi-jurisdiction scope notes, "as of [date]" stamps — than any other vertical surveyed. The rubric should not penalize this register; pages without it are the actually-failing ones.

**Failure modes specific to fintech GEO.**
- **Cross-jurisdiction over-claim.** "We serve customers worldwide" without per-jurisdiction license / scope disclosure.
- **Performance claims without time-window.** "10% returns" without "annualized over what period, net of fees, regulated under whom."
- **AI / algorithmic transparency gap.** Claims of AI-driven advisory without addressing the model-risk framing.
- **Stale rate / pricing data.** Interest rates / fees / APYs without current-month date stamps → de-cited by AI engines on freshness (rate-change cadence shorter than for other verticals).

### 3.5 AI research labs / developer-tools (Anthropic / Perplexity context)

**Citation substrate.** Structurally unique — the developer documentation IS the citation substrate, alongside arxiv / GitHub / analyst Substacks. AI engines preferentially cite (a) the lab's own API / SDK documentation (Mintlify-built docs for Anthropic, Cursor, Perplexity now serve `llms.txt`, `llms-full.txt`, and `skill.md` files as markdown to AI agents instead of HTML — cutting token usage and improving citation extractability); (b) model cards and benchmark cards with reproducible methodology; (c) arxiv preprints and paperswithcode entries; (d) GitHub repositories (commit cadence, README, releases); (e) external analyst Substacks (Interconnects, Stratechery, Latent Space, State of AI). The CI vertical-conventions deliverable's AI-lab CI substrate analysis applies in full here.

For developer-facing queries ("how do I X with Claude," "Perplexity API rate limit"), the page is the docs site. For strategic / capability queries ("how does Claude compare to GPT-5"), the page is the model card + benchmark methodology + analyst-Substack reference. For research queries, the page is the arxiv paper.

**Highest-leverage page shape.**
- **Reference-document register API/SDK docs** — declarative ("X returns Y"), code-example-dense, version-stamped, with reproducible request/response examples. Mintlify-style markdown serving to AI agents.
- **Benchmark card with reproducible methodology** — model name + benchmark + score + methodology + date + reproduction code + comparison to prior version.
- **Dated changelog / release notes** — per-version, with breaking-change disclosure.

**Gating regime.** Not regulated, but technically demanding — AI engines (and the developer-readers of AI engines) detect inaccurate technical claims fast. Self-reported benchmark inflation (Kimi K2 50% claimed on HLE vs 29.4% independent retesting per CI vertical-conventions §3.4) is a known failure mode that has trained AI engines to preferentially cite independent-eval sources (Epoch AI, Artificial Analysis, LMSYS).

**Failure modes specific to AI-lab GEO.**
- **Self-reported benchmark without independent-eval cross-reference.**
- **Marketing register on technical content.** "Most powerful X" without methodology.
- **API docs without code examples** or with stale code examples.
- **Missing version pin / changelog.** Critical because API surfaces change; AI engines need to know what date a claim was true.

### 3.6 DTC e-commerce

**Citation substrate.** Newly bifurcated as of 2025-2026 by agentic-commerce protocols. OpenAI/Stripe's Agentic Commerce Protocol (ACP) has been live in ChatGPT since September 2025; Google's Universal Commerce Protocol (UCP) was announced January 2026 with Walmart, Target, Shopify, Etsy, and 20+ partners. AI-referred traffic to e-commerce sites grew 393% YoY in Q1 2026; visitors from ChatGPT, Perplexity, and Google AI Overviews convert 42% better than paid-search, email, or affiliate traffic (ALM Corp 2026 data). Google AI Overviews now appear on 14% of all shopping queries (5.6× increase in 4 months).

The citation substrate has three tiers: (a) structured Product schema (Product / Offer / AggregateRating / Review markup) — operationally mandatory; (b) third-party reviews on Reddit (~21-24% of AI citations on Perplexity for product queries), YouTube reviews, niche-community boards (the consumer YMYL-adjacent — health products, supplements, baby goods route through Reddit + Mom-blogs); (c) the brand's own product pages with rich first-party data. Smaller DTC brands with complete Product schema regularly outrank household-name brands with strong domain authority but thin structured data.

**Highest-leverage page shape.**
- **Schema-rich product page** — Product / Offer / Review schema; named functional attributes in product title ("Brand Model — Material — Capacity — Use Case"); unit-economics-by-cohort comparison; current-week pricing/availability stamp.
- **Comparison page** — "X vs Y vs Z" with feature table + UGC review pull-quotes (named source: Reddit r/X, YouTube review).
- **Reddit / community-traction surfacing** — embedded testimonials sourced from Reddit / niche-community boards where the brand has organic presence (NOT manufactured).

**Gating regime.** No formal YMYL gating except for supplements / cosmetics (FDA cosmetic labeling rules, FTC advertising substantiation) and health-adjacent products. Schema validation is the dominant filter — 89% of e-commerce sites implement Product schema incorrectly per ALM Corp 2026; correct implementation alone moves citation share materially.

**Failure modes specific to DTC GEO.**
- **Brand-storytelling page without unit-of-purchase specificity.** "Our story" + lifestyle photography + no functional product attributes.
- **Missing or incorrect Product schema.**
- **No UGC / Reddit surfacing.** Brand cites only its own customers; AI engines cite Reddit reviews preferentially because they read as third-party.
- **Stale pricing / availability.** Critical for shopping queries; pricing without current-week date / inventory stamp fails the agentic-commerce-protocol check.

### 3.7 Professional services / consulting / accounting

**Citation substrate.** The pattern that emerged most clearly from the 2026 Q1-Q2 accounting / consulting AI citation analysis: brands win by publishing head-to-head competitor comparison editorial on their own domain. Xero leads "QuickBooks alternative" queries by deliberate strategy of publishing dozens of head-to-head Xero-vs-QuickBooks pages over years (5W PR Agency 2026 AI Visibility Index). FreshBooks dominates freelancer/consultant/agency time-based-billing queries through similar editorial strategy. In mid-market ERP, AI answers almost exclusively compare NetSuite vs Sage Intacct — both publish extensive head-to-head content on their own domains; this comparison editorial is the dominant citation substrate for the category.

This is the inverse pattern from B2B SaaS: B2B SaaS loses to G2 / aggregators on category prompts because aggregators control the comparison surface; professional services / accounting wins on comparison prompts because the comparison surface lives on first-party domains and the aggregator presence is thinner. Consulting firm citation routes through case studies, thought leadership (Stratechery / McKinsey Quarterly / HBR for upper end), and named-author insight pieces.

**Highest-leverage page shape.**
- **Head-to-head comparison editorial** ("X vs Y") on the brand's own domain, structured as comparison table + per-feature deep-dive + use-case routing.
- **Named-author insight piece** — partner / principal byline, dated, with original analysis, named-case-study examples.
- **Case study with verifiable outcome metrics** — named-client + named-outcome + dated period.

**Gating regime.** Professional bodies (AICPA for accounting, ICAEW / CIMA in UK, IMC USA for management consulting) impose ethical advertising standards similar to but lighter than legal-vertical bar rules. No YMYL gating except for accounting-as-financial-advice adjacency.

**Failure modes specific to professional-services GEO.**
- **Generic capability-pitch.** "We help companies grow" without industry/specialization/case-study evidence.
- **No head-to-head comparison content.** Brand only describes its own service in isolation.
- **Anonymous case studies.** "A Fortune 500 client" without sector / outcome / verifiable metric.

---

## 4. Cross-vertical synthesis — what's universal vs what's vertical-specific

### Universal across all 7 verticals
1. **Answer-first declarative-document register.** Volpini's Matryoshka Paragraph principle holds across verticals — the first 40-75 words must contain a complete, citable declarative answer. (Aggarwal KDD 2024, Perplexity's 90/100-words finding, Profound 40-75 word passage sweet spot.) Survives every vertical-cut.
2. **Passage self-containment.** Every passage must work standalone — no floating pronouns, no orphan context. Volpini's chunk-complete principle. Holds across legal long-form, B2B SaaS comparison, healthcare evidence-explainer, DTC product page.
3. **Freshness signal.** Every vertical preferentially weights recent content, but the freshness window varies: fintech (current-month), DTC pricing (current-week), B2B SaaS (current-quarter), healthcare (24-month medical-review freshness), legal (last-reviewed-with-statute-version), AI-lab API docs (per-release).
4. **Entity consistency.** Same brand / product name everywhere, knowledge-graph-ingestible. Kalicube principle. Universal.

### Vertical-specific and load-bearing — 6 dimensions

1. **Citation-substrate authority tier.** Legal → .gov / bar / statute. Healthcare → clinical guidelines / academic medical centers / PubMed. B2B SaaS → G2 / Gartner / TrustRadius. Fintech → SEC / FINRA / CFPB / FCA. AI-labs → arxiv / GitHub / analyst Substacks. DTC → Reddit / YouTube + Product schema. Professional services → head-to-head editorial + named-author byline. Almost zero overlap across verticals.
2. **YMYL gating regime.** Hard gating in healthcare, legal, fintech (E-E-A-T inflation, citation-confidence threshold elevated, hallucination-liability shift). Soft / no gating in B2B SaaS, DTC (except supplements / cosmetics), AI-labs, professional services. The Aggarwal Statistics-vs-Quotation-vs-Fluency optimal-method-per-domain finding maps onto this: Statistics Addition wins in Law & Government (gated, evidence-substrate-heavy); Fluency wins in Health and Business (where readability and clarity convert better in a higher-trust threshold).
3. **Highest-leverage page shape.** FAQ + jurisdiction-scoped explainer (legal); evidence-based clinician-authored explainer + procedure-comparison glossary (healthcare); head-to-head comparison + alternatives hub (B2B SaaS, professional services, AI-lab API docs); regulator-aligned definitional explainer + risk-disclosure FAQ (fintech); reference-document API docs + benchmark card (AI-lab); schema-rich product page + UGC surfacing (DTC).
4. **Author-attribution requirement.** Hard requirement in legal (attorney + bar) and healthcare (clinician + credentials + last-medically-reviewed). Soft requirement in fintech (compliance-officer / regulator-license disclosure). Strong requirement in professional services (partner / principal byline). Light requirement in B2B SaaS, AI-labs, DTC.
5. **Aggregator / gatekeeper presence.** Heavy aggregator gatekeeping in B2B SaaS (G2 / Capterra / TrustRadius / Gartner Peer Insights) and DTC (Amazon / Reddit-driven UGC). Moderate in healthcare (RealSelf / Healthgrades on local-aesthetic; Mayo Clinic / WebMD on national-medical). Light in legal, fintech, professional services, AI-labs.
6. **Recency-window severity.** Strict: DTC pricing (week), fintech rates (month), AI-lab API versioning (release). Moderate: B2B SaaS pricing (quarter), healthcare medical-review (24 months). Loose: legal statute-citation (statute-version-bound, can be years).

### Single most important takeaway
The current GEO v0 spec's GEO-5 (format-intent match + freshness) implies a uniform format-class-to-page-shape mapping ("comparison → table; how-to → ordered steps; what-is → definition + structured detail"). That mapping holds across verticals at the surface level but breaks at the citation-substrate level: a "what is X" page in healthcare needs clinician byline + last-medically-reviewed + named-guideline citation that a "what is X" page in B2B SaaS does not need; a "X vs Y" page in legal needs jurisdiction-scoped statute citation per row that a "X vs Y" page in DTC e-commerce does not. The rubric criteria as currently written are vertical-blind on the citation-substrate axis. A 50-generation evolution loop with first-cohort fixtures dominantly legal will learn to plant attorney-byline-shaped surface markers on all fixtures regardless of vertical — and conversely if AI-lab dominates, will learn to drop the byline entirely.

---

## 5. Goodhart-collapse modes per vertical

Each vertical has a vertical-specific Goodhart-collapse mode the rubric must resist independently (per design-guide §11):

- **Legal:** "Attorney bio + jurisdiction-scope theater." Workflow learns to plant attorney byline + bar-number + jurisdiction-statement on every page regardless of whether the underlying analysis is jurisdiction-accurate or attorney-substantive.
- **Healthcare:** "USPSTF / NICE / AAD citation slot-fill." Workflow learns to drop named-guideline citations on every page regardless of whether the citation is relevant; medical-reviewer-byline is templated and not load-bearing.
- **B2B SaaS:** "Comparison-table-where-we-win." Workflow learns to produce comparison pages where the home product wins every row — already an AI-flagged pattern (Verge / Google AI Mode), so the slot-fill is self-defeating but the workflow may iterate through several before learning.
- **Fintech:** "Disclaimer / risk-disclosure prose density." Workflow learns to plant disclaimers + risk-disclosure language on every page regardless of whether the underlying analysis is regulator-aligned.
- **AI-labs:** "Benchmark table with vendor scores." Workflow learns to drop benchmark tables citing self-reported scores; AI engines have learned to de-cite, so workflow may iterate through several before learning.
- **DTC:** "Schema markup + Reddit-pull-quote slot-fill." Workflow learns to inject Product schema everywhere + plant Reddit-style quotes that aren't actually sourced; AI engines that detect the fabrication de-rank.
- **Professional services:** "Head-to-head comparison template repetition." Workflow learns the X-vs-Y format and replicates it on pages where comparison is the wrong format-intent.

Each of these is a specific Goodhart-collapse mode that score-1 anchors must defend against — by anchoring on outcomes (the page actually earns citation in the vertical's citation substrate) rather than surface markers (byline / disclaimer / benchmark table / schema present).

---

## 6. Recommendations for v1 spec — actionable input for Path-A iteration

These are recommendations on the **vertical-conventions axis only.** Path-A iteration synthesizes across this axis + artifact-taxonomy + AI-failure-modes + dual-audience — recommendations may need adjustment when other axes land.

### Recommendation 1 — Anchor across ≥5 verticals in score-1 examples per criterion

**Concrete recommendation:** the current v0 spec has one Freddy-themed example on GEO-1 (B2B-SaaS-ish), one Freddy-themed example on GEO-2 (B2B-SaaS-ish), and zero on GEO-3 / GEO-4 / GEO-5. Replace with 3 vertical examples per criterion (legal / healthcare / B2B SaaS as load-bearing) + leave 2 verticals (fintech / AI-lab) as alternates for criteria where they exemplify the criterion better. Pattern matches CI v3.3's three-anchor expansion (per `2026-05-18-ci-vertical-conventions.md` §6 Recommendation 1) which has the same first-cohort-overfit defense rationale.

Worked example for GEO-1 (Answer-first BLUF):

> Example A (do not optimize toward this): "Klinika Melitus is a Warsaw aesthetic dermatology practice, founded 2008 by Dr. Maria Noszczyk MD (FAAD-equivalent), specializing in injectable cosmetic dermatology — Botox, fillers, biostimulators — for women 35-60 in central Warsaw. We are listed on RealSelf and Healthgrades; this article was last medically reviewed in May 2026."
>
> Example B (do not optimize toward this): "Linear is a project-management tool built for software engineering teams that prefer keyboard-first interfaces, fast issue triage, and Git integration. Used by 10,000+ teams including Cash App, Vercel, and OpenAI; consistently rated 4.7+ on G2 across 800+ reviews."
>
> Example C (do not optimize toward this): "Section 230 of the Communications Decency Act (47 U.S.C. § 230) is the federal statute that provides interactive computer service operators with immunity from liability for content posted by third-party users. As of January 2026, the immunity has been narrowed by FOSTA-SESTA and is subject to two pending Supreme Court reviews; this article is current as of May 1, 2026 and is for informational purposes only, not legal advice."

Each example uses a different vertical's citation-substrate convention (healthcare → clinician + reviewed-date + RealSelf/Healthgrades; B2B SaaS → G2 + named-customer; legal → statute + dated + disclaimer). The anchor demonstrates *behavioral* characteristics (declarative, evidence-paired, freshness-stamped, entity-defined) without naming the vertical — preventing the workflow from optimizing toward "drop byline" or "cite RealSelf."

Do NOT name the vertical in rubric prose. Anchors are behavioral examples, not categorical hints. The judge prompt's `shared judge-prompt wrapper` should add one sentence: "The citation substrate the page draws from will vary by vertical — clinical guidelines / academic medical centers in healthcare; review aggregators in B2B SaaS; statute and regulator references in legal and fintech; arxiv / GitHub / analyst Substacks in AI-labs; Product schema and named-community reviews in DTC. Score the OUTCOME — would the engine in the page's vertical cite — not the surface markers."

### Recommendation 2 — Add per-vertical Goodhart-collapse modes to §6 of the spec

The current v0 §6 has 5 Goodhart-resistance verifications (one per criterion). Each is correct at the criterion-shape level. Add a complementary §6b naming the per-vertical collapse modes from §5 above (legal: attorney-bio theater; healthcare: guideline-citation slot-fill; B2B SaaS: comparison-where-we-win; fintech: disclaimer-density; AI-labs: benchmark-table-with-vendor-scores; DTC: schema + Reddit-pull-quote slot-fill; professional services: head-to-head template repetition).

This is documentation only — it does not add criteria, does not modify rubric prose. It tells Path-A which slot-fills the rubric must defend against per vertical so the redundancy check + fixture validation can probe them.

### Recommendation 3 — Generalize GEO-5's freshness window to vertical-context

Current GEO-5 prose: "Visible publication or update date within last 12-18 months." That's healthcare-medical-review-style cadence. It is wrong for DTC pricing (week), fintech rates (month), AI-lab API versioning (release), legal statute (statute-version-bound). Generalize to: "Freshness signal at the cadence the vertical's citation substrate weights — current-week for shopping queries, current-month for rate/yield queries, last 12-18 months for evergreen explainer content, statute-version-bound for legal-citation queries." Keeps the freshness-is-vertical-conditioned spirit while not penalizing a legal page citing 1998 statute with a 2024 last-reviewed stamp.

### Recommendation 4 — Vertical-specific evidence-substrate sentence in the judge-prompt wrapper

Add one sentence to the shared wrapper (per Recommendation 1): "The citation substrate varies by vertical — do not penalize evidence sources because they're unfamiliar; do penalize evidence sources that are wrong for the vertical (e.g., a healthcare page that cites only B2B-SaaS-style review aggregators; a legal page that cites only blog posts and not statute / case law)."

### Recommendation 5 — Re-validate after redundancy check on multi-vertical fixture set

Per design-guide §5 redundancy check + §14 fixture validation: when the GEO redundancy check runs (Path-A pending), ensure fixture set includes at least one of each load-bearing vertical (legal / healthcare / B2B SaaS / fintech / AI-lab). The current fixture set covers 3 (legal-DWF, healthcare-Klinika, AI-lab-Anthropic/Perplexity). Build a B2B SaaS and a fintech fixture before locking GEO criteria via empirical redundancy check. Pattern matches CI v3.3 §8 Open Question 4 (vertical fixture coverage gap).

### Recommendation 6 — Defer per-vertical sub-spec bifurcation

Don't bifurcate the spec into legal-GEO / healthcare-GEO / B2B-SaaS-GEO / fintech-GEO / AI-lab-GEO sub-rubrics. Single spec + diverse anchors is structurally cheaper and the design-guide §5 isolation principle (per-criterion analytic rationale) gives the judge enough leverage to discriminate vertical-appropriately if the anchors are right. If fixture-validation rationales come back vertical-skewed (e.g., judge produces "missing attorney byline" rationales on a B2B SaaS fixture), escalate to per-vertical sub-specs at that point. Pattern matches CI v3.3 §6 Recommendation 5 deferral.

---

## 7. Defending each recommendation against a failure mode

Per the design-guide "looks elaborate ≠ over-engineered" discipline (§3.2 of judge-design-guide.md v2.1), each recommendation here defends against a documented failure mode:

1. **Three-vertical anchor expansion (Rec 1):** Defends against first-cohort overfit, the same documented failure mode CI v3.3 named in its own vertical-conventions deliverable (Pinsent-shape Goodhart). Without it, 50 generations against legal-dominant fixtures produces healthcare/SaaS outputs with attorney bylines, and vice versa.
2. **Per-vertical Goodhart-collapse documentation (Rec 2):** Defends against the documented Phase-4 pathology pattern that already triggered three rollbacks on this lane family (`2ce99bb`, `ca4a256`, `698e658` → `c76f051`). Vertical-specific collapse modes are subtly different from the cross-vertical framework-name-checking failure; without naming them, Path-A iteration won't probe for them in fixture validation.
3. **Vertical-context freshness (Rec 3):** Defends against penalizing legal pages with 1998-statute citation, which would distort the score-1 distribution and reduce legal-fixture variance. Current 12-18 month framing comes from Perplexity's medical-vertical pattern; healthcare freshness is real, but Path-A would inherit it as universal.
4. **Wrapper sentence on evidence-substrate variation (Rec 4):** Defends against the judge confusing "unfamiliar evidence source" with "weak evidence source." A judge that reads a Mintlify-served markdown API doc as marketing-content has misread the vertical's citation substrate.
5. **Multi-vertical fixture validation (Rec 5):** Defends against the redundancy check producing single-vertical-skewed correlation results — if all 5 fixtures are legal, GEO-2 (evidence density) and GEO-4 (entity + third-party validation) will correlate >0.7 because legal evidence substrate doubles up. Single-spec works only if fixtures are diverse on the substrate axis.
6. **Defer per-vertical bifurcation (Rec 6):** Defends against premature complexity. Per-vertical sub-rubrics multiply maintenance cost without empirical proof that single-spec + diverse anchors fails. The escalation path stays open.

---

## 8. Open questions for JR (Path-A must decide before findings ship)

1. **Which 5-7 verticals are the load-bearing anchor set?** Recommendation 1 proposes legal / healthcare / B2B SaaS as load-bearing with fintech / AI-lab as alternates; DTC / professional services as optional 6th/7th. Should the set be wider (include DTC), or narrower (just legal / healthcare / SaaS)? Decision affects example budget per criterion.

2. **Build B2B SaaS and fintech fixtures before locking GEO criteria?** Current fixtures cover 3 of 5 load-bearing verticals (legal-DWF, healthcare-Klinika, AI-lab-Anthropic). Per Recommendation 5, build 1 B2B SaaS + 1 fintech fixture before locking. Cost: ~2 fixture-build days. Defer to when?

3. **GEO ≤5 criterion ceiling — is YMYL a documented exception?** Per design-guide §5 (v2.1 amendment), a justified breach of the ≤5 ceiling is permitted when literature documents an LLM-specific failure surface other criteria can't catch. CI took the breach with CI-6 (Evidence chain) for citation-fab / source-confab / recency-distortion. For GEO, the analogous question is whether YMYL gating (legal / healthcare / fintech) constitutes a separate failure surface requiring a 6th criterion (e.g., "Vertical-appropriate authority signal — for YMYL pages, named-clinician / named-attorney + verifiable credential present; for non-YMYL pages, not load-bearing"). My read: probably no — YMYL gating is already captured by GEO-2 (evidence density) + GEO-4 (entity + third-party validation) when the score-1 anchors include healthcare-clinician and legal-attorney examples. Redundancy check will resolve.

4. **Site-engine lane overlap on the vertical axis.** GEO v0 §8 already flags site-engine overlap on artifact-taxonomy. On vertical-conventions: site_engine probably needs the same vertical-anchor expansion (site-shape varies even more by vertical — legal practice areas, healthcare service lines, B2B SaaS product lines, fintech regulatory jurisdictions, DTC catalog hierarchy, AI-labs API resource hierarchy). Propagate this deliverable's vertical findings into site_engine v0? Or wait for site_engine to draft its own.

5. **First-cohort-overfit monitoring trigger.** Per CI v3.3 §8 Open Question 7, the agreed pattern is: any fixture from a vertical not in {legal-services, AI-lab, healthcare, B2B-SaaS, fintech} triggers re-validation. For GEO specifically — the same trigger holds. Any new-vertical fixture (DTC e-commerce, professional services, hospitality, marketplaces, regulated finance variants) should prompt re-validation of GEO-1..GEO-5 anchor adequacy. Confirm same trigger applies?

---

## 9. Citations

Grade A = peer-reviewed / operator-firsthand operational data; B = industry-standard secondary / aggregator research; C = vendor blog / anecdote.

**Foundational academic (grade A):**
- Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande. "GEO: Generative Engine Optimization." arXiv:2311.09735, KDD 2024. https://arxiv.org/abs/2311.09735 — domain-conditioning of optimal optimization method (Statistics for Law & Government / Opinion; Quotation for People & Society / History; Fluency for Health and Business).

**B2B SaaS citation substrate (grade B):**
- "G2's 2026 Acquisition Could Increase its AI Citation Share by 76% in BOFU Prompts" — Omniscient Digital. https://beomniscient.com/blog/g2-acquisition-ai-citation-share/ — G2 = 4.1% citation share; Gartner = 28.7% organic SERP share.
- "AI Drives Shift to Autonomous Business: Gartner" — techedgeai.com via Gartner. https://techedgeai.com/b2b-software-just-crossed-the-line-from-google-first-to-chatgpt-first-buying/ — 51% of B2B software buyers now start in AI chatbot.
- "22 Best Alternatives to G2 for B2B SaaS (2026)" — Blastra. https://blastra.io/directories/alternatives-to-g2/ — review-aggregator hierarchy (G2 / Capterra / TrustRadius / SourceForge / Gartner Peer Insights / PeerSpot).
- "8 Best AEO Agencies For B2B SaaS Companies (2026 Ranked)" — Discovered Labs. https://discoveredlabs.com/blog/6-best-aeo-agencies-for-b2b-saas-companies-2026-ranked.

**Legal services (grade B):**
- "Generative Engine Optimization: Complete 2026 Strategy Guide for Law Firms" — Lexicon Legal Content. https://www.lexiconlegalcontent.com/generative-engine-optimization-law-firms/ — AI Overviews on 23.6% of legal queries; 34.5% click reduction.
- "AEO for Lawyers: How Law Firms Can Dominate AI Search in 2026" — SEM Nexus. https://semnexus.com/aeo-for-lawyers/ — YMYL E-E-A-T inflation in legal vertical.
- "What is AEO for Law Firms?" — Lexicon Legal Content. https://www.lexiconlegalcontent.com/aeo-for-law-firms/.

**Healthcare / aesthetic dermatology (grade B):**
- "AEO for Healthcare" — Stridec. https://www.stridec.com/blog/aeo-for-healthcare/ — clinician-authored content with named-guideline references.
- "Perplexity AI for Healthcare: How to Get Your Practice Cited" — DoctorRank. https://doctorrank.com/perplexity-ai-for-healthcare — Perplexity returns 21+ sources per medical answer.
- "The YMYL Playbook for Healthcare AI Search" — upGrowth. https://upgrowth.in/ymyl-playbook-healthcare-brands-win-ai-search-trust/ — Mayo Clinic / WebMD baseline citation tier.
- "Healthcare AEO: Building Trust and Winning Patient Queries in YMYL Content" — MaximusLabs. https://www.maximuslabs.ai/answer-engine-optimizations/healthcare-aeo-trust-winning-patient-queries-ymyl.
- "Local SEO for Cosmetic Practices: The Complete 2026 Guide" — Medical Marketing Firm. https://medicalmarketingfirm.com/resources/blog/local-seo-cosmetic-practices-complete-guide/ — local pack capture 40-60% mobile share.
- "Medical Spa SEO: How to Rank and Win AI Search in 2026" — Reporter Outreach. https://www.reporteroutreach.com/blog/medical-spa-seo.

**Fintech (grade B):**
- "GEO for Regulated Industries: Fintech Compliance Playbook [2026]" — upGrowth. https://upgrowth.in/geo-regulated-industries-fintech-compliance-playbook-2026/.
- "Agentic AI for Fintech & Banking Marketing: Guide 2026" — DigitalApplied. https://www.digitalapplied.com/blog/agentic-ai-for-fintech-banking-marketing-vertical-guide — UDAAP / FINRA / SEC / OCC SR 11-7 model-risk framework.
- "The Fintech CMO's Guide to AI Search Visibility [2026 Playbook]" — upGrowth. https://upgrowth.in/fintech-cmo-guide-ai-search-visibility-2026-playbook/.
- "Fintech SEO Strategy 2026" — Vicious Marketing. https://www.viciousmarketing.net/post/fintech-seo-strategy-in-2026-why-ai-search-is-your-biggest-untapped-channel.

**AI labs / developer documentation (grade A operator + B secondary):**
- Mintlify documentation platform notes — https://www.mintlify.com/library/best-technical-documentation-software-in-2026 — Mintlify serves llms.txt / llms-full.txt / skill.md for Anthropic, Cursor, Perplexity (markdown to AI agents instead of HTML).
- "Developer docs metrics that matter Jan 2026" — Fern. https://buildwithfern.com/post/developer-documentation-metrics.
- Cross-reference to companion CI vertical-conventions deliverable §3 (AI-lab CI substrate).

**DTC e-commerce (grade B):**
- "Google AI Overviews Now Appear on 14% of Shopping Queries" — ALM Corp. https://almcorp.com/blog/google-ai-overviews-shopping-queries/ — 14% share, 5.6× growth in 4 months, 42% better conversion vs paid search.
- "How D2C & E-commerce Brands Win AI Search" — Searchable. https://www.searchable.com/blog/d2c-ecommerce-ai-search-optimization-2026 — schema-rich product pages outranking household brands.
- "AI Shopping Assistant Guide 2026: Agentic Commerce Protocols" — Opascope. https://opascope.com/insights/ai-shopping-assistant-guide-2026-agentic-commerce-protocols/ — ACP (OpenAI/Stripe Sept 2025) + UCP (Google + Walmart/Target/Shopify/Etsy Jan 2026).
- "DTC Brands: AI Visibility Optimization Strategies" — Recomaze. https://recomaze.ai/dtc-brands-ai-visibility-optimization-strategies.
- "How Perplexity Picks Its Top 3 Product Recommendations" — Alhena. https://alhena.ai/blog/perplexity-product-recommendations-optimization/.

**Professional services / accounting / consulting (grade B):**
- "THE ACCOUNTING & FINANCE SOFTWARE AI VISIBILITY INDEX 2026" — 5W PR. https://www.5wpr.com/new/the-accounting-finance-software-ai-visibility-index-2026/ — Xero / NetSuite / Sage Intacct head-to-head editorial strategy.
- "We Scored 50 Enterprise Companies for AI Visibility" — GTM Signal Studio. https://www.gtmsignalstudio.com/blog/ai-visibility-benchmark-2026-findings — 44% of enterprise companies score 2/25 on Citation Presence.
- "CountingWorks PRO — The 2026 Visibility Playbook" — https://www.countingworkspro.com/blog/the-2026-visibility-playbook-how-to-future-proof-your-firm-for-ai-search.
- "AI Search Citation Analysis Q2 2026: Domains Ranked" — DigitalApplied. https://www.digitalapplied.com/blog/ai-search-citation-analysis-q2-2026-domains-ranked.

**Cross-vertical citation patterns (grade B):**
- "AI Platform Citation Patterns: ChatGPT, Google AI Overviews, Perplexity" — Profound. https://www.tryprofound.com/blog/ai-platform-citation-patterns.
- "AI Citation Patterns by Platform, Industry, and Intent" — ALM Corp. https://almcorp.com/blog/ai-citation-patterns-platform-industry-brand-strategy/.
- "[Research] Reddit Accounts for 21% of Third-Party Citations for Key B2B SaaS Prompts" — Foundation. https://foundationinc.co/lab/reddit-ai-citations — Reddit = #1 source in 6 of 7 verticals studied; 20.8% top-50 share.
- "The AI Platform Citation Source Index 2026" — Everything PR. https://everything-pr.com/ai-platform-citation-source-index-2026/.

**Companion deliverable (internal):**
- `docs/research/2026-05-15-judges-domain-geo.md` — generalist GEO synthesis (Aggarwal / Volpini / Shepard / Profound / Perplexity citation behavior / failure modes).
- `docs/research/2026-05-18-ci-vertical-conventions.md` — pattern reference for the three-anchor expansion + per-vertical Goodhart-collapse documentation + deferral of per-vertical sub-spec bifurcation. Same architecture; vertical findings differ.
