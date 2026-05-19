---
date: 2026-05-18
type: research deliverable
status: complete
topic: CI vertical-specific conventions (legal-services / AI-labs / healthcare)
parent: docs/handoffs/2026-05-17-judge-design-step1-competitive.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# Vertical-Specific Conventions in Competitive Intelligence
## Legal services / AI research labs / Aesthetic dermatology — what changes per vertical, what the CI v2 spec must accommodate

**Companion to:** `2026-05-15-judges-domain-competitive.md` (generalist Helmer/Porter/Martin/Klue/CB Insights synthesis). This pass goes vertical-specific so the CI lane's rubric does not silently optimize for a single archetype.

**Why this exists.** v2 of the CI optimal-output spec assumes one reader archetype: founder/VP of Strategy at a tech-savvy company. The fixture cohort the lane actually grades against — DWF, Anthropic, Perplexity, Klinika Melitus — is three structurally distinct verticals. A CI brief that earns 5/5 against DWF reader-intent could earn 2/5 against Anthropic reader-intent (and vice versa) for reasons that are evidence-source norms and decision-shape, not analytical quality. If the rubric doesn't see that, the evolution loop will overfit to whichever vertical happens to dominate the fixture set.

---

## 1. TL;DR (300 words)

### Top vertical-specific findings (3 per vertical)

**Legal services (DWF context):**
1. **CI is structurally a marketing/BD function, NOT a strategy function in most firms.** The Am Law 200 CI analyst sits in the BD or KM department. Their reader is a practice-group head or BD director preparing a pursuit, not a CEO setting strategy. The Law.com May-2026 review of the Am Law CI function explicitly identifies "weak strategic alignment" and "under-utilized intelligence teams" as the dominant internal pathology.
2. **Lateral-partner-moves are the dominant CI signal-class** — 3,009 lateral partner moves in 2025 (+10% YoY), with named platforms (Firmscape, Leopard BI, Firm Prospects, Pirical) functioning as the primary evidence substrate. Citi Hildebrandt's annual "Client Advisory" tracks lateral hire ROI: 74% of equity-promoted partners broke even at 5 years vs 63% for laterals. This is the comp-tier of "structural mechanism" in legal CI.
3. **Chambers/Legal 500/IFLR1000 directory rankings are CI-grade evidence** at a level no other vertical has — they are the only quasi-independent, longitudinally-comparable third-party assessment of practice-group strength. A brief that ignores tier-shifts in directories is missing the legal equivalent of a stock-price move.

**AI research labs (Anthropic/Perplexity context):**
1. **CI is founder-led or research-strategy-embedded, not a discrete function.** No frontier lab has a "CI team" in the corporate sense — strategic threat-reading happens in 1:1s between Dario/Sam/Demis and research/product leads, supplemented by 2–4 named external analysts (Lambert, Thompson, Wang, Benaich) read at the CEO level.
2. **Benchmark gaming is the dominant Goodhart-collapse mode of the source material itself.** Kimi K2 self-reported 50% on HLE, independent retesting found 29.4%. MMLU-Pro is saturated above 88%. A CI brief that ranks labs by aggregated benchmark scores has already failed the "what's actually changing" test.
3. **The CI evidence substrate is largely public-but-uncatalogued** — arxiv preprints, hiring patterns on Levels.fyi/LinkedIn, model-card diffs, API pricing teardowns, GitHub commit cadence, and a tier of analyst Substacks (Interconnects/Stratechery/Latent Space/State of AI). No paid CI vendor competes with this stack.

**Healthcare / aesthetic dermatology (Klinika context):**
1. **CI is the practice owner's job — done informally and on Saturday** — with industry-association reports (AmSpa State of the Industry, ASDS Consumer Survey) and consumer review platforms (RealSelf 10M unique monthly visitors, Healthgrades) as the only systematic evidence sources.
2. **Local-market-density beats national-market-trends as the load-bearing CI signal.** AmSpa: 81% of medical-spa operators are single-location; "competitive intensity heightens in suburban catchments." A brief that quotes the $23.29B → $42.43B market trajectory but misses the three competing injectors who opened within 2km in the last quarter has failed the practice-owner reader.
3. **Scope-of-practice and FDA off-label exposure are CI-grade legal/regulatory signals** unique to healthcare — a competitor running an off-label semaglutide protocol or operating in a no-supervision-required state is creating both a pricing advantage AND a regulatory liability the brief must distinguish.

### Strongest single recommendation for the CI v2 spec

**Add vertical-specific score-1 anchor examples to CI-1, CI-2, and CI-3** (one per vertical: legal, AI-lab, healthcare) — without naming the vertical in the rubric prose. Current spec has one DWF-style example on CI-1; that's legal-skew, and a 50-generation evolution loop against it will learn to produce "6-partner lateral pull" patterns regardless of fixture vertical. Three anchors per criterion (legal/AI-lab/healthcare) at the same rigor level disrupt the slot-fill while keeping the rubric reference-free.

---

## 2. Vertical A — B2B legal services (DWF context)

### 2.1 Who writes CI in BigLaw

CI as a discrete function appeared in Am Law firms only around 2010–2015 and remains under-developed. The May-2026 Law.com Pro feature "Inside the CI Function" (parent piece for the MLA Global / Acritas-co-produced *Evolution of Competitive Intelligence in Law Firms* study) surveys Am Law 200 CI directors and concludes: **the biggest threat to law firm CI is internal — siloed data, weak strategic alignment, under-utilized intelligence teams.**

Concretely, four placement patterns exist:

1. **BD/Marketing-embedded (most common).** CI sits under the CMO or BD director. Their work supports pitches, RFP responses, lateral-recruiting due-diligence, and client-team prep. They produce battlecards and pursuit memos, NOT strategy memos. Pinsent Masons, DLA Piper, Baker McKenzie all fit this pattern.
2. **Knowledge Management-embedded.** CI sits under the head of KM, blending with legal-research and precedent functions. Law360 Pulse's 2026 piece "How BigLaw Firms Shape Knowledge Teams" notes KM teams are being repositioned as "infrastructure, not support" with GenAI shifting the function. CI inherits the longer time-horizon and research orientation.
3. **Strategy Committee-direct (rare, premium firms).** Slaughter & May, Kirkland & Ellis, and the upper Magic Circle have small (1–3 person) strategy teams reporting to the managing partner or executive committee. Their output is closer to corporate strategy memos.
4. **External vendor / consortium.** Firms outsource to ALM Intelligence, MLA Global (which absorbed Acritas), Citi Hildebrandt's Law Firm Group (Citi Private Bank's law-firm advisory practice surveys 200+ firms annually), Pirical, or LAC Group. Citi Hildebrandt's annual "Client Advisory" is the single most-cited industry survey, with the 2025 edition framing "growth opportunities, technology investment, operational efficiency, and changes to lawyer leverage."

For DWF specifically (~90 lawyers, RES practice, mid-market UK/Polish): the in-house CI function is likely 0–2 people inside BD/Marketing. The reader of any CI brief is the managing partner, the senior RES practice partner (Maciej Jamka), or the executive committee — not a dedicated strategy lead.

### 2.2 Who reads it and what decisions they face

| Reader | Decision shape | Time budget |
|---|---|---|
| Managing partner | Lateral hire approval, practice-group investment, office-opening go/no-go | 10 minutes, often less |
| Practice-group head | Senior-associate retention, lateral defense, billing-rate posture | 15–30 minutes if action implied |
| BD director | Pursuit prioritization, pitch-team composition, directory-submission strategy | 30+ minutes (operational user) |
| Executive committee | Merger evaluation, strategic alliance, geographic expansion | 1+ hour, deck format |

The decision shapes differ structurally from tech-founder reader-intent in three load-bearing ways:

- **Partnership governance.** Decisions are committee-driven and consensus-mediated. A brief that recommends a single posture for a single decision-maker mis-fits the structure; the brief must arm the senior partner with arguments that survive an executive-committee meeting where competing partners hold equity-vote.
- **Partner-as-asset, not employee.** Lateral partners are economic units with portable books of business. A CI brief about a competitor that doesn't address the partner-flow question (who's leaving competitor X, who could we recruit, who's at risk on our side) is missing the dominant lever.
- **Practice-area silos.** "DWF" is not a single competitive unit — DWF-RES, DWF-Insurance, DWF-Corporate compete in distinct markets with distinct competitor sets. A firm-level CI brief that doesn't decompose by practice group is operationally useless.

### 2.3 Format conventions

The dominant format is **the BD memo** — typically 2–4 pages, sometimes embedded in a pitch-team briefing pack. Structure converges around:

1. Executive summary (3–5 bullets, named competitors)
2. Competitor profiles (partner counts, sector strength, recent wins/losses, lateral movement)
3. Directory positioning (Chambers/Legal 500 tier-by-tier comparison)
4. Lateral signals (who's left, who's joined, equity-share movement)
5. Pursuit/defensive recommendations

For strategy-committee consumption, the format escalates to a **board deck** — 10–20 slides, often with a comparative matrix (firms × practices × revenue/PEP/lateral-flux).

Length convention: shorter than tech CI briefs. The 10-minute managing-partner read is the binding constraint. Citation density is high (Chambers ranking citations, named partner-departure dates, named matter wins) — legal readers are trained on evidence chains and will dismiss an unsourced claim.

### 2.4 CI-grade evidence sources

| Source | What it provides | Comp-grade signal |
|---|---|---|
| **Chambers & Partners** (chambers.com) | Annual tier rankings (T1/T2/T3) by practice + jurisdiction, individual partner rankings | Tier-shift = ~stock-price-move; partner promotion to "Star Individual" = major positive signal |
| **The Legal 500** (legal500.com) | Parallel directory; client testimonials carry weight | Practice-tier movement; KPI Analysis Reports (paid product) benchmark client-satisfaction by competitor |
| **IFLR1000** | Financial/regulatory rankings — load-bearing for transactional practices | The third leg; cross-checks Chambers/Legal 500 |
| **Leopard BI / Firmscape** (leopardsolutions.com) | Real-time lateral-tracker, headcount-by-office data, partner-bio mining | Primary lateral-movement signal substrate |
| **Firm Prospects** (firmprospects.com) | Lateral hiring trends + practice-level movement aggregates | "Litigation led partner hiring at 26%, corporate 16%" — 2025 statistic |
| **Pirical** (pirical.com) | Workforce data science for law firms; diversity/retention benchmarks | Strategy-committee level analysis |
| **Citi Hildebrandt Client Advisory** | Annual law-firm financial-performance benchmark, 200+ firm anonymized dataset | Industry-wide PEP, RPL, leverage benchmarks |
| **Acritas (now part of MLA Global) Brand Index** | Global Elite Law Firm Brand Index built on Sharplegal survey (~834 interviews with $1B+ revenue GCs across 55 countries, conducted by phone in local languages) | The closest legal-industry analogue to NPS; brand-strength rank is a directional signal of GC mindshare |
| **ALM Intelligence** | Am Law 100/200 financial rankings; lawyer compensation data | Revenue-per-lawyer benchmark; PEP comparisons |
| **Above the Law / Law360 / Law.com Pro** | Lateral-move news, court-filing analytics | The "news ticker" tier; Above the Law publicizes lateral moves before firms announce |
| **Court-filing analytics (Lex Machina, Bloomberg Law Litigation Analytics)** | Win-rate, judge data, party data for litigation practices | Practice-specific; not all firms have litigation-led CI |

Directory citations are CI-grade in legal in a way they are not in any other vertical surveyed. The brief that says "Acme's Chambers Band 2 ranking in EMEA Construction held for the third year while DWF dropped from Band 3 to Band 4" has just made a comp-grade analytical claim using a third-party benchmark that the entire industry accepts.

### 2.5 Named exemplars

**Vendors/consultancies producing CI artifacts the industry treats as benchmarks:**
- **MLA Global** (legal management consultancy; absorbed Acritas's research practice 2020) — published the May-2026 *Evolution of Competitive Intelligence in Law Firms* report referenced above.
- **Citi Hildebrandt** — annual Client Advisory (2024, 2025 editions widely cited); Law Firm Leaders Survey of ~57 large firms; Confidence Index from 136 firms. The format is a 30–40 page PDF with charts and a one-page executive summary.
- **Leopard Solutions** — Firmscape platform; "the Bloomberg terminal for legal lateral tracking." Their reports treat lateral movement as a continuous time series.
- **LAC Group** — "Law Firm CMO's Guide to Competitive Intelligence" — practitioner-focused playbook.

**In-house CI practices identified by name in industry coverage:**
- Pinsent Masons (referenced in DWF context — May 2026 6-partner RES pull from CMS/Dentons/DLA/GT)
- Kirkland & Ellis (London expansion via lateral pull; CI heavy on associate-comp signals)
- Baker McKenzie (Acritas Global Elite Brand Index #1 multiple years — they CI their own brand position rigorously)

### 2.6 Failure modes specific to legal CI

- **Directory-rank theater.** Brief cites Chambers tier without explaining what drove the tier movement. A tier change is the OUTPUT of underlying matter-mix, partner reputation, and client-feedback movement; citing the rank without the driver is data-not-intelligence.
- **Single-firm framing of multi-practice competitors.** "DWF vs Pinsent Masons" is meaningless at the firm level — they compete in 4–6 practice groups with different intensities. A brief that doesn't decompose by practice is structurally wrong.
- **PEP-as-strategy.** Profit-per-Equity-Partner is a lagging output of practice-mix decisions, not a strategic input. A brief that recommends "match Kirkland's PEP" without identifying the practice-mix that produced it has confused output for strategy.
- **Lateral-defense myopia.** Briefs over-index on outgoing-lateral risk (defensive) and under-index on incoming-lateral opportunity (offensive). The Citi 74%/63% statistic shows promoted partners outperform laterals — yet CI workflow over-weights lateral threat-monitoring because it's the easier signal to track.
- **Client-confidentiality dance.** Legal CI cannot openly cite the client/matter/win-loss data the analyst actually has. Briefs hedge to anonymity in a way that strips analytical force; the failure is over-hedging.
- **Compliance-paralysis on competitor data.** Solicitors' Regulation Authority (UK) and bar-association rules prohibit certain competitive-intelligence gathering techniques (pretexting, false-flag candidate interviewing) routine in other verticals. A CI shop that's narrowed its toolkit too aggressively to comply produces a thinner brief than a tech-CI shop.

---

## 3. Vertical B — AI research labs / dev-tools (Anthropic, Perplexity context)

### 3.1 Who does CI at frontier AI labs

**There is no dedicated CI function at any frontier AI lab.** Strategic threat-reading is distributed across:

- **Founders.** Dario and Daniela Amodei at Anthropic; Sam Altman at OpenAI; Aravind Srinivas at Perplexity. The hybrid structure at Anthropic (Creately/Clay org charts) shows research, product, engineering, and policy leaders reporting directly to the CEO with no intermediate CI layer. Daniela Amodei "drives strategic direction and operational excellence" — strategy is a founder responsibility, not a delegated function.
- **Research strategy / Anthropic Institute-equivalent groups.** Long-horizon scenario planning; "what does the next 18 months of capability look like" reasoning.
- **GTM/Applied AI leadership.** Daniela's "scaling the commercial engine" function — the Applied AI team that puts Claude into enterprises is the closest analog to a market-positioning team, but their CI focus is on customer-facing competitor encounters (Claude vs GPT-5 in evaluations) rather than corporate strategy.
- **External analyst stack consumed at exec level.** This is structurally different from any other vertical: the CEO of an AI lab reads ~4 named outsiders almost daily.

The Stanford Daily May-2026 piece on Daniela's Stanford talk reinforces the founder-as-strategy-engine pattern — "combine innovation with responsibility" is delivered as personal philosophy, not as an output of a strategy team.

### 3.2 Who reads it and what decisions they face

| Reader | Decision shape | Cadence |
|---|---|---|
| Founder/CEO | Model-roadmap priority, compute-allocation, GTM partnership go/no-go | Daily-to-weekly |
| Head of Research | Research-direction posture, hiring priority, paper-publication strategy | Weekly |
| Head of Product / Applied AI | Feature parity, pricing tier, enterprise positioning | Weekly-to-monthly |
| Board / lead investors | Round timing, narrative positioning, geopolitical posture | Monthly-to-quarterly |
| Policy team | Regulatory positioning, frontier-AI policy stance | Continuous |

Two structurally distinct features from the tech-startup CI archetype:

- **Capability-trajectory dominates positioning.** The single most consequential strategic question is "is Anthropic's Claude Opus 5.x better or worse than GPT-5.5/Gemini-3-Pro on the dimension that matters to the enterprise customer who's evaluating right now?" — and the answer changes in 6–12 week cycles. A monthly brief is too slow.
- **Talent flow is a primary signal.** Hires and departures at frontier labs are publicly tracked (Levels.fyi, AccessAI's "Talent Density Index" at paraform.com, LinkedIn, Air Street Press's annual State of AI report). Air Street's 2025 report explicitly notes "the pack has closed in fast" using a hiring/release-cadence frame.

### 3.3 Format conventions

There is no standard format. Empirically observed:

- **Long-form internal memo (the Stratechery style).** Internal Anthropic/OpenAI memos leaked or referenced in journalism tend to be 1500–4000 word reasoned arguments rather than templated briefs. The Ben Thompson "Aggregation Theory" or "Tech Philosophy and AI Opportunity" essay format is widely emulated internally.
- **Slack-channel running-thread.** Continuous low-friction signal capture; periodic synthesis posts.
- **Notion / Linear strategic-doc.** Living documents with comment-threads; "competitive landscape" pages that get updated rather than rewritten.
- **Twitter/X thread.** Surprisingly: Aravind Srinivas, Sam Altman, Dario Amodei post strategic positioning publicly. This IS competitive intelligence, both in production and consumption — competitors read each other's tweets carefully.
- **Quarterly board narrative.** Closer to a Stratechery essay than a McKinsey deck.

Length convention is bimodal: tweet-thread (~250 words, daily) or essay (~2000 words, weekly/monthly). The "5-page memo" format common in tech-startup CI is rare.

### 3.4 CI-grade evidence sources

| Source | What it provides | Comp-grade signal |
|---|---|---|
| **arxiv.org tracking** (often via paperswithcode.com or rss) | Pre-publication research signals; cross-lab citation patterns | Where attention is moving; named-author trajectories |
| **Epoch AI** (epoch.ai) — Benchmarking Hub + Capabilities Index (ECI) + compute estimates | "Independent evaluation authority" — results added day-of-release; ECI weights benchmarks by difficulty | Compute-allocation tracking + capability-trajectory; widely cited in compliance / procurement / governance |
| **Artificial Analysis** (artificialanalysis.ai) | 356 models tracked across speed × cost × capability simultaneously | Pricing teardown substrate |
| **LMSYS Chatbot Arena (Arena Elo)** | Blind A/B Elo ratings from >1M battles | Single-number aggregate; competitive ranking by user preference. As of March 2026: Anthropic 1503, xAI 1495, Google 1494, OpenAI 1481 |
| **HELM** (Stanford CRFM) | Holistic Evaluation of Language Models — academic benchmark framework | Independent evaluation layer |
| **Hugging Face Open LLM Leaderboard** | Open-model trajectory | Where China/open-source is closing the gap |
| **Levels.fyi + AccessAI Talent Density Index** (paraform.com) | Hiring patterns; researcher compensation; team-density-by-lab | Talent-flow signal; "who's pulling from whom" |
| **Stratechery** (stratechery.com — Ben Thompson) | Strategic interpretation, aggregation theory applied to AI | The single most-cited analyst at the CEO level |
| **Latent Space** (latent.space — Shawn Wang/swyx, Alessio Fanelli) | Practitioner-focused, founder-interview format | Distribution channel for "what the labs are actually building" |
| **Interconnects** (interconnects.ai — Nathan Lambert, ex-Allen Institute) | Post-training methods, open-model trajectory, frontier-lab strategy. 60K+ subscribers | The deepest technical/strategic AI newsletter |
| **State of AI Report** (stateof.ai — Nathan Benaich, Air Street Capital, published since 2018) | Annual 200+ slide deck; covers research / industry / politics / safety; 1,200-practitioner survey | The single closest analog to a McKinsey industry report for AI |
| **MindStudio AI Lab Power Rankings** | 9-category weighted scorecard (compute, enterprise, platform, consumer reach, model quality, momentum, narrative, wedge, x-factor) | 2026 ranking: Google 74, OpenAI 74, Anthropic 70 — useful structured comparable |
| **GitHub commit cadence** (public on most labs' open-source repos) | Release-velocity, where eng-attention is | Often-overlooked structural signal |
| **API pricing pages + model-card diffs** | Pricing teardowns, capability claims | High-information; pages change weekly |
| **Earnings calls / 10-Qs (for Google/Microsoft/Amazon-funded labs)** | Capex disclosure (compute spend), enterprise revenue mix | Compute spend = scale-economies signal |

### 3.5 Named exemplars

**External analysts whose work IS the competitive-intel artifact:**
- **Nathan Lambert's Interconnects** — operating playbook for Anthropic-vs-OpenAI vs open-model strategic positioning. The "Chinese frontier lab" interview series is unmatched as competitive-intel-on-Chinese-labs.
- **Ben Thompson's Stratechery** — strategy synthesis at the platform-economics level. "Owning the AI Pareto Frontier" (Jeff Dean interview) on Latent Space is the canonical capability-trajectory artifact.
- **Air Street's State of AI Report** (2018–2025 published, 2026 forthcoming) — annual industry-report tier; openly cited by lab founders.
- **MindStudio's 2026 AI Lab Power Rankings** — 9-category scorecard methodology; closest thing to a Big-4 industry analyst report.

**Internal CI artifacts (referenced in journalism but not public):**
- Anthropic's reported competitive-positioning memos around the Claude vs GPT-5 launch
- OpenAI's reported "frontier compute" planning artifacts (Axios/TechCrunch 2026 coverage of the compute-strategy divergence)
- DeepMind's internal "AGI safety" framing memos (referenced in Demis Hassabis interviews)

### 3.6 Failure modes specific to AI-lab CI

- **Benchmark-table-as-strategy.** Ranking labs by MMLU/HumanEval/GSM8K aggregate scores is the dominant failure. MMLU-Pro saturated >88%, MMLU-Pro saturated at 89%+ for top tier (per techjacksolutions.com 2026 review). The differences at the top are statistically meaningless. A brief leading with a benchmark table has telegraphed analytical weakness.
- **Self-reported-score-trust.** Kimi K2 reported 50% on Humanity's Last Exam (HLE); independent retesting found 29.4% — a 70% relative overstatement. Air Street, Epoch AI, and Artificial Analysis exist BECAUSE labs systematically inflate. A CI brief that cites a lab's own benchmark claim without independent corroboration is failure mode 1.
- **Capability-cliff projection.** Linear extrapolation from o3 → o4 → o5 misses that frontier capability gains are NOT monotonic on a fixed benchmark — capability moves to new evaluations (ARC-AGI 3 dropped all frontier models to 0). The trajectory frame must be axis-mobile.
- **Hype-cycle distortion.** GPT-5 landed after "months of AGI-level hype" and the industry verdict was "model router over an aging stack." A brief that adopts public hype framing rather than independent capability assessment has been captured.
- **Narrative-rank vs technical-rank confusion.** MindStudio's 2026 ranking: Google/OpenAI tied on raw scorecard but OpenAI 10/10 on momentum vs Google 3/10. A brief that conflates "leading on paper" with "winning the narrative race" mis-reads the actual competitive position.
- **Geopolitical blindness.** China's DeepSeek, Qwen, Kimi sit "within a few points" of OpenAI on reasoning/coding (Air Street State of AI 2025). A frontier-lab CI brief that doesn't engage Chinese labs as primary competitors is structurally incomplete.
- **Compute-strategy underweighting.** OpenAI all-in on GPUs; Anthropic on partnerships + efficiency. Per Axios April 2026, "Anthropic, OpenAI enter compute wars." Compute strategy IS competitive strategy at this layer; a brief that treats it as plumbing has missed the load-bearing variable.

---

## 4. Vertical C — Healthcare / aesthetic dermatology (Klinika context)

### 4.1 Who does CI in small-to-mid healthcare practices

The honest answer: **CI is the practice owner's job, done informally and unsystematically.** AmSpa's 2024 State of the Industry data: 81% of medical-spa operators are single-location, and the median practice generates $1.39M annually (with 60% of practices generating under $500K per Growth99 research). At that scale, there is no in-house CI function. CI happens through:

1. **Practice owner / medical director** — typically the founding physician (Dr. Maria Noszczyk at Klinika Melitus) — reads industry-association reports, attends conferences (ASDS Annual Meeting, AmSpa AMS conference), and informally surveys local competitors.
2. **Marketing manager or fractional marketing consultant** — runs local-pricing audits, competitor-Instagram monitoring, RealSelf-profile audits.
3. **Industry associations as CI distributor:**
   - **American Society for Dermatologic Surgery (ASDS)** publishes annual Consumer Survey on Cosmetic Dermatologic Procedures
   - **American Med Spa Association (AmSpa)** publishes annual *Medical Spa State of the Industry Report* + the 2025 *State of Aesthetic and Elective Wellness Marketing Report* (100+ practice leaders surveyed; finding: 77% struggle with differentiation)
   - **American Academy of Dermatology (AAD)** — practice-management content
4. **Vendor-driven CI** — device manufacturers (Allergan/AbbVie for Botox, Galderma for Restylane, Cynosure for lasers, Cutera, etc.) push competitive-positioning content to drive product adoption. Bias is heavy but evidence is real.
5. **Specialist consultancies** — boutique aesthetic-practice consultants (Growth99, Modern Aesthetics trade publications, Practical Dermatology) produce benchmark surveys.
6. **At scale (corporate chains)** — LaserAway, Ideal Image, Skin Laundry, Schweiger Dermatology, Pinnacle Dermatology, Epiphany Dermatology (39 acquisitions over 5 years per FOCUS dermatology valuation benchmarks). These run corporate-grade CI but at the franchise/PE level, not the practice level.

For Klinika Melitus — a single-location Warsaw aesthetic dermatology practice — the CI shop is effectively Dr. Noszczyk plus a part-time marketing function. There is no analyst.

### 4.2 Who reads it and what decisions they face

| Reader | Decision shape | Time budget |
|---|---|---|
| Practice owner / medical director | Treatment-mix expansion, device-purchase, pricing posture, hiring | 30 minutes evening/weekend |
| Operations lead (if practice >5 staff) | Scheduling, capacity, referral pathways | 30 minutes |
| Marketing manager | Channel mix, RealSelf-profile investment, content cadence | Continuous (operational) |

The reader is operationally close to the work. Decisions are immediate-quarter:
- "Should I add semaglutide to my menu next month?"
- "Acme Aesthetics opened 2km away — should I match their $499 Botox bundle?"
- "My RealSelf rating dropped to 4.6 — what changed?"

This is structurally distinct from BigLaw and AI-lab CI. The decision-shape is **operational-immediate** with high frequency, low stake-per-decision, but high cumulative consequence.

### 4.3 Format conventions

The format conventions are far less developed than legal or AI-lab CI. Practical formats:

- **Single-page competitor-pricing scan** (Google-Sheet style; updated quarterly)
- **RealSelf-profile competitive review** (screenshots + 1-paragraph notes)
- **Vendor-supplied competitive-positioning sheet** (e.g., Allergan's brochure comparing Botox to Dysport — biased but real)
- **Industry-association report excerpts** — the AmSpa State of the Industry as 1-page take-aways
- **Conference take-aways** — informal post-ASDS / post-AMS notes
- **Local-market map** — Google Maps screenshot with competitor pins (the geography-as-CI artifact unique to local healthcare)

Length convention: short. Practice owners don't read 5-page briefs. The marketing-agency norm (Intrepy, Cardinal Digital Marketing, and others targeting derm practices) is one-page dashboards with 3–5 KPIs.

### 4.4 CI-grade evidence sources

| Source | What it provides | Comp-grade signal |
|---|---|---|
| **RealSelf** (realself.com) | 10M unique monthly visitors, 50M photos viewed, 500K direct provider contacts/mo — the consumer review and provider-comparison platform | Competitive review density, before/after photo volume, Q&A activity. The single most-trafficked aesthetic-CI source |
| **Healthgrades** | Patient reviews, provider directories | Patient-acquisition signal — reviews drive search ranking |
| **Google Maps / Google Business Profile** | Local competitor density, review volume + sentiment, hours, photo refresh cadence | The "competitive map" — load-bearing for local CI |
| **ASDS Consumer Survey on Cosmetic Dermatologic Procedures** (asds.net) | Annual: which procedures consumers are seeking, demographics, motivations | Industry-level demand signal |
| **AmSpa Medical Spa State of the Industry Report** (americanmedspa.org) | Annual; 2024 edition: $17B industry, +$1B/yr; 10,488 US med spas in 2023 up from 8,899 in 2022 | Industry-density and trajectory |
| **AmSpa 2025 State of Aesthetic and Elective Wellness Marketing Report** | 100+ practice leaders surveyed; 77% struggle with differentiation; avg 7% revenue → marketing (range 2–15%) | Marketing-spend benchmark |
| **Growth99 benchmarking survey** | Practice-level revenue/marketing benchmarks; the under-$500K vs $1.39M gap | Performance-distribution signal |
| **FOCUS Bankers / Scope Research / TUSK Practice Sales** | Dermatology practice valuation multiples (3–5x EBITDA single, 7–10x mid, 12x+ regional platforms) | M&A signal — strategic alternative pricing |
| **FTI Consulting "Dermatology: Looking Good"** | Industry-level analyst report from Big-4-adjacent consultancy | Sector-trajectory benchmark |
| **FDA approval news + state medical board rule updates** | New device clearances, scope-of-practice rule changes | Regulatory signal; e.g., Colorado Rule 800 on cosmetic injectables |
| **Modern Aesthetics, Practical Dermatology, Dermatology Times** | Trade journals; clinical + practice-management content | Treatment-mix trajectory |
| **Vendor sales-rep intelligence** | Allergan/AbbVie/Galderma/Cynosure reps know who in your market is buying what device, at what volume | The single highest-info-density informal channel — unique to healthcare |
| **Instagram / TikTok competitor profiles** | Patient-acquisition channel; before/after volume; reel cadence; engagement metrics | Brand-strength signal for aesthetic-derm specifically |

The vendor-rep channel deserves emphasis: Allergan/Galderma/AbbVie reps see every practice's device-purchase and injectable-order volume in a regional territory. A practice owner who has a strong relationship with their Allergan rep has access to local competitive data no other vertical has an analog for. CI in legal services or AI labs has no equivalent of "your supplier knows what your competitors are buying."

### 4.5 Named exemplars

- **AmSpa State of the Industry Report** — the canonical annual benchmark, distributed to 5,000+ practices
- **ASDS Consumer Survey on Cosmetic Dermatologic Procedures** — annual consumer-side companion
- **RealSelf Insights Center** — practice-marketing playbooks distilled from RealSelf platform data
- **FOCUS Bankers Dermatology Practice Valuation 2025 Benchmarks** — the M&A-context CI artifact
- **Growth99 / AmSpa 2025 marketing report** — marketing-spend benchmark, named ROI gaps
- **Industry-consolidator competitive-intel:** Epiphany Dermatology, Schweiger, Pinnacle, DermCare — these PE-backed roll-ups run corporate CI that informs their acquisition pipeline; their methodology shows up in FTI Consulting and Scope Research reports

### 4.6 Failure modes specific to healthcare CI

- **National-market for a local-market decision.** Quoting "$23.29B → $42.43B market growth, 12.74% CAGR" is irrelevant to a practice owner deciding whether to match Acme's $499 Botox bundle. The CI brief that opens with national market-size has signaled it doesn't understand the decision shape.
- **Regulatory blind spots.** A competitor offering an off-label semaglutide protocol in a state with permissive scope-of-practice rules is creating a pricing edge AND a regulatory exposure that's invisible to standard competitive scans. State medical board rules vary 50 ways (Colorado Rule 800 differs from Texas differs from California). A brief that doesn't distinguish "Acme is cheaper" from "Acme is cheaper because they're running a compliance shortcut you can't legally match" has failed.
- **Patient-acquisition-cost ignorance.** The brief that recommends "compete on price" without calculating the CAC delta for the recommended channel (RealSelf vs Google Ads vs Instagram vs referral) is recommending in the abstract. Aesthetic-derm CAC ranges from $200 (referral) to $800+ (paid digital cold-acquisition).
- **Treatment-mix-as-feature-comparison.** The Christensen JTBD failure mode is acute in aesthetic-derm: patients aren't buying "Botox," they're buying "I want to look less tired." A brief that compares Botox-vs-Daxxify pricing without engaging the underlying JTBD is missing the actual competitive surface.
- **Vendor-rep-bias importation.** The Allergan rep is the most-informed local-CI source AND is selling you product. A CI brief that absorbs vendor-rep framing without disclosing has inherited a bias the reader can't audit.
- **Review-rating obsession at the wrong tier.** RealSelf rating moves of 0.1 are noise; rating moves of 0.5+ are signal. Brief that over-indexes on Google-review-of-the-week misses the structural trajectory.
- **Consolidator-blindness.** 81% single-location operators don't see Pinnacle/Schweiger/Epiphany as a competitive threat until they're being acquired by them. A CI brief that doesn't engage the roll-up trajectory is missing the strategic-inflection-point that may end the practice's independence.

---

## 5. Cross-vertical synthesis (500 words)

### What's universal across all three verticals

Three patterns hold across legal/AI-lab/healthcare CI:

1. **Point-of-view at the top.** All three reader archetypes are time-poor and skim. A brief that leads with synthesis (claim + implication) beats a brief that leads with method or background. This is the strongest of the May-15 generalist findings and survives the vertical-cut.
2. **Evidence chain.** Legal demands court-rank citations; AI-labs demand independent-evaluation citations; healthcare demands association-survey citations. The evidence sources differ wildly, but the principle is invariant: every claim is sourced or the reader rejects it.
3. **Hard prioritization.** The brief must have 3–5 findings, not 10. Klue's "kill your darlings" discipline holds equally in BigLaw BD memos, founder-CEO Stratechery-style essays, and AmSpa state-of-the-industry summaries.

### What's vertical-specific and load-bearing

Six dimensions vary structurally enough that a single-spec rubric is at risk of vertical-overfit:

1. **Reader-decision shape.** Legal = committee-mediated, partnership-governed, often defensive (lateral-flight risk). AI-lab = founder-direct, capability-trajectory, often offensive (compute/talent grab). Healthcare = practice-owner-immediate, local-operational, often defensive (CAC and roll-up exposure). The CI v2 spec's "founder/VP of Strategy" reader maps cleanly onto AI-lab, partially onto legal (managing-partner-as-CEO), poorly onto healthcare (the operational time-horizon is wrong).
2. **Time horizon.** Legal: 12–24 months (partnership investment cycle). AI-lab: 6–18 weeks (model-release cadence). Healthcare: 4–12 weeks (treatment-cycle, season, referral-source). The "trajectory 6–18 months out" anchor in CI-2 fits legal best, fits AI-lab decently, and is wrong for healthcare.
3. **Evidence-substrate.** Legal: directories + lateral-tracker + matter-wins. AI-lab: benchmarks (with independent-corroboration filter) + hiring + GitHub + analyst-Substacks. Healthcare: RealSelf + Google Maps + AmSpa surveys + vendor-rep informal. Almost zero overlap.
4. **Structural-mechanism flavor.** Legal: practice-group strength, partner-book portability, directory reputation. AI-lab: compute, talent density, model capability, ecosystem partnerships. Healthcare: location, treatment-mix margin, referral pathways, regulatory positioning. The Helmer 7 Powers framing applies to all three but the load-bearing power differs (Cornered Resource for AI-lab talent; Process Power / Switching Costs for legal client relationships; Scale Economies at the consolidator tier for healthcare).
5. **Goodhart-collapse target.** Legal: directory-rank theater + PEP-as-strategy. AI-lab: benchmark tables + self-reported scores. Healthcare: national-market-size citation + treatment-mix-as-feature-comparison. The CI v2 spec's Goodhart-resistance section currently anchors on Phase-4 framework-name-checking — relevant primarily to AI-lab and consulting-coded outputs, not to legal or healthcare.
6. **Cost-of-action.** Legal: $1–2M (equity-vesting acceleration, lateral defense). AI-lab: $10–100M (compute commitment, talent grab). Healthcare: $5–50K (device purchase, marketing channel reallocation). CI-5's trade-off criterion ("the cost is specific enough to be uncomfortable") needs to recognize that "uncomfortable" is scale-relative.

### Single most important takeaway

The current v2 spec's Reader section says it explicitly: "Substitute readers the same brief should also serve... senior partner at a professional-services firm... clinic operations lead." That gesture is correct; what it lacks is **calibration** — the rubric criteria don't yet have score-1 anchor examples that demonstrate what excellence looks like in each substituted vertical. A 50-generation evolution loop with one DWF-style score-1 example will learn to produce DWF-style outputs across all fixtures.

---

## 6. Implications for CI v2 spec (400 words)

### Concrete recommendations

**1. Add per-vertical score-1 anchor examples to CI-1, CI-2, CI-3, CI-5.** (CI-4 — uncomfortable truth — appears vertical-invariant.) Spec currently has one DWF-style example on CI-1 only. Recommendation: three anchors per criterion, one per vertical (legal/AI-lab/healthcare), at the same rigor level. Do NOT name the vertical in the rubric prose — anchors are illustrative of behavior, not categorical hints. Worked example for CI-1:

> Example A (do not optimize toward): "The 6-partner Pinsent Masons RES lateral pull is the dominant Q3 retention risk; defend by accelerating the senior-associate equity-vesting conversation we already deferred. Cost: ~$1.4M ahead of plan; we lose the option to use that capital on the Birmingham office plan."
>
> Example B: "DeepSeek's V3.5 architecture (MLA + DeepSeekMoE) closed the cost-per-token gap to within 8% of Sonnet 4 at comparable reasoning on AIME. Commission a 2-week compute-efficiency teardown of MLA before deciding whether to pre-empt with a price cut or hold pricing and accelerate the Opus-5-Mini distillation."
>
> Example C: "Acme Aesthetics opened 2.3km away, undercut Botox by 18%, and is running a $1500 semaglutide protocol that's off-label in this state. Defend the senior-injector tier by training Dr. K on the new energy-device launch (8-week ramp) rather than match price; cost: defer the second-room buildout by one quarter."

**2. Generalize CI-2's time horizon language.** Current spec says "6–18 months." Replace with "the time horizon over which the reader's next 1–2 decisions will be made (typically 6–18 months for B2B, can be 6–18 weeks for fast-moving categories like frontier AI or seasonally-driven local services)." Keeps the trajectory-not-snapshot spirit; removes the legal-cycle skew.

**3. Add a vertical-evidence-substrate sentence to the judge-prompt wrapper.** Current wrapper says "test for whether the brief would actually change a decision they make Monday morning." Add: "Evidence sources vary by vertical — directory rankings and lateral data in legal services, independent benchmarks and hiring patterns in AI labs, association surveys and local-market signals in healthcare. Do not penalize evidence sources because they're unfamiliar."

**4. Expand the Goodhart-collapse modes (§3b).** Currently anchored on framework-name-checking (Helmer/ACH/Hard-Prioritization). Add vertical-specific collapse modes:
- Directory-rank theater (legal)
- Benchmark-table-as-strategy + self-reported-score-trust (AI-lab)
- National-market-size citation + treatment-mix-as-feature-comparison (healthcare)

**5. Defer the "Reader sub-persona" question to fixture validation.** Don't bifurcate the Reader section yet. Run the 5 existing CI fixtures (Anthropic / DWF / Perplexity outputs already on hand) through the v2 criteria with the three vertical anchor examples. If the judge produces vertical-discriminating rationales, single-spec + diverse-anchors is sufficient. If it produces single-vertical-skewed rationales, escalate to per-vertical sub-specs.

**6. The Goodhart-collapse mode does differ per vertical.** A workflow that learns to score against DWF fixtures will produce Pinsent-Masons-shaped outputs across all fixtures. The fix is the three-anchor expansion in recommendation 1.

---

## 7. Sources

### Legal services
- [Inside the CI Function: Why Law Firms' Biggest Competitive Threat Comes From Within](https://www.law.com/pro/2026/05/07/inside-the-ci-function-why-law-firms-biggest-competitive-threat-comes-from-within-/) — Law.com Pro May 2026
- [The Maturation of Competitive Intelligence in Law Firms](https://www.mlaglobal.com/en/insights/articles/the-maturation-of-competitive-intelligence-in-law-firms) — MLA Global (Acritas successor)
- [Citi Hildebrandt 2025 Client Advisory](https://www.citiglobalwealth.com/content/dam/cpb/internet/www-citiglobalwealth-com/wealth-at-work/docs/2025-Citi-Hildebrandt-Client-Advisory.pdf.coredownload.pdf)
- [Acritas Global Elite Law Firm Brand Index 2016 (methodology document)](https://www.bakermckenzie.com/-/media/files/newsroom/2016/10/acritas-global-elite-law-firm-brand-index-2016.pdf)
- [Chambers Legal Intelligence — data to decisions](https://chambers.com/topics/legal-intelligence-data-law-firm-growth)
- [The Legal 500 rankings + KPI analysis](https://www.legal500.com/)
- [Leopard Solutions / Firmscape](https://www.leopardsolutions.com/firmscape/)
- [Firm Prospects — 2025 Lateral Hiring Trends](https://www.firmprospects.com/blog/fresh-data-5-lateral-hiring-trends-shaping-the-legal-market)
- [Pirical](https://www.pirical.com/)
- [LAC Group — Law Firm CMO's Guide to Competitive Intelligence](https://lac-group.com/reports-and-case-studies/law-firm-cmo-guide-competitive-intelligence/)
- [Competitive Intelligence 101: Law firm edition (Diligent)](https://www.diligent.com/resources/blog/competitive-intelligence-law-firms)
- [How BigLaw Firms Shape Knowledge Teams In The Age Of AI](https://www.law360.com/pulse/articles/1891037/how-biglaw-firms-shape-knowledge-teams-in-the-age-of-ai)
- [Pinsent Masons Hires DLA Piper M&A Partner](https://www.law.com/international-edition/2024/10/16/pinsent-masons-hires-dla-piper-ma-partner-as-part-of-growth-strategy/)

### AI research labs
- [Stratechery — Ben Thompson](https://stratechery.com/)
- [Interconnects — Nathan Lambert](https://www.interconnects.ai/)
- [Latent Space — Shawn Wang / Alessio Fanelli](https://www.latent.space/)
- [State of AI Report 2025 — Nathan Benaich / Air Street](https://www.stateof.ai/)
- [State of AI April 2026 newsletter](https://nathanbenaich.substack.com/p/state-of-ai-april-2026-newsletter)
- [Epoch AI Benchmarking Hub](https://epoch.ai/benchmarks)
- [Epoch Capabilities Index](https://epoch.ai/eci)
- [LMSYS Chatbot Arena](https://lmarena.ai/)
- [Artificial Analysis](https://artificialanalysis.ai/)
- [Paraform Talent Density Index](https://www.paraform.com/talent-density-index)
- [Google vs OpenAI vs Anthropic Momentum in 2026](https://www.mindstudio.ai/blog/google-vs-openai-vs-anthropic-momentum-2026-narrative)
- [2026 AI Lab Power Rankings: 9-Category Scorecard](https://www.mindstudio.ai/blog/2026-ai-lab-power-rankings-9-category-scorecard)
- [OpenAI vs Anthropic on Compute Strategy](https://www.mindstudio.ai/blog/openai-vs-anthropic-compute-strategy)
- [Anthropic, OpenAI enter compute wars — Axios April 2026](https://www.axios.com/2026/04/02/anthropic-usage-limits-openai)
- [What Is Benchmark Gaming in AI](https://www.mindstudio.ai/blog/benchmark-gaming-ai-inflated-scores-explained)
- [The Benchmark Ceiling: Why Standard AI Evals Are Failing Frontier Models](https://techjacksolutions.com/ai-brief/the-benchmark-ceiling-why-standard-ai-evals-are-failing-fron/)
- [Stanford HAI 2026 AI Index — Technical Performance](https://hai.stanford.edu/ai-index/2026-ai-index-report/technical-performance)
- [Anthropic Organizational Structure — Creately](https://creately.com/org-chart/major-startups/anthropic/)
- [Anthropic Executives — Clay](https://www.clay.com/dossier/anthropic-executives)
- [Daniela Amodei urges students to combine innovation with responsibility (Stanford Daily, May 2026)](https://stanforddaily.com/2026/05/08/anthropic-co-founder-daniela-amodei-urges-students-to-combine-innovation-with-responsibility/)

### Healthcare / aesthetic dermatology
- [AmSpa Medical Spa State of the Industry Report](https://americanmedspa.org/resources/med-spa-statistics)
- [AmSpa 2025 State of Aesthetic and Elective Wellness Marketing Report](https://americanmedspa.org/blog/new-research-reveals-critical-gaps-in-aesthetic-practice-marketing-strategy-77-of-practices-struggle-with-differentiation)
- [ASDS Consumer Survey on Cosmetic Dermatologic Procedures](https://www.asds.net/medical-professionals/practice-resources/consumer-survey-on-cosmetic-dermatologic-procedures)
- [RealSelf Insights Center — Dermatologists Seeking Web Marketing ROI](https://insightscenter.realself.com/social-dermatology-3-takeaways-from-the-asds-annual-meeting/)
- [Medical Spa Market Size (Mordor Intelligence)](https://www.mordorintelligence.com/industry-reports/medical-spa-market)
- [FOCUS Bankers — Dermatology Practice Valuation 2025 Benchmarks](https://focusbankers.com/dermatology-practice-valuation/)
- [Scope Research — Dermatology Valuation Multiples and M&A Trends 2025](https://www.scoperesearch.co/post/dermatology-physician-practice-valuation-multiples-and-m-a-trends)
- [FTI Consulting — Dermatology: Looking Good](https://www.fticonsulting.com/insights/articles/dermatology-looking-good)
- [Legal Language in Aesthetic Practices: Botox and Fillers — Prospyr](https://www.prospyrmed.com/blog/post/legal-language-in-aesthetic-practices-botox-and-fillers)
- [FDA Regulating Medical Aesthetic Services — EMMA International](https://emmainternational.com/how-the-fda-is-regulating-medical-aesthetic-services/)
- [Who Can Perform Injectable Neuromodulators and Fillers — Nextech](https://www.nextech.com/blog/who-can-perform-injectable-neuromodulators-and-derm-fillers)
- [State by State Scope of Practice Laws — Dermascope](https://www.dermascope.com/what-s-the-scope-understanding-state-by-state-scope-of-practice-laws/)
- [FDA Approval News for Aesthetics 2026 — Portrait Care](https://www.portraitcare.com/post/fda-approval-news-for-aesthetics-what-to-know-for-2026)
