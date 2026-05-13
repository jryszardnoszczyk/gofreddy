# Phase B research — `marketing_audit` lane

Calibration corpus for the MA-1..MA-8 judge stack. The gofreddy team has already produced 5,230 lines of prior research across four planning docs (lens catalog v2, lens ranking, audit pipeline research record, v1 master plan). This file does NOT re-derive that. It (1) confirms what is solid, (2) names the gaps a 9-tier judge needs that the existing rubric draft does not yet enforce, and (3) injects the 2026 emerging signals visible after the April 2026 freeze.

Current rubric draft (master plan §6.4): MA-1 strategic narrative coherence, MA-2 evidence traceability, MA-3 Phase-0 framing applied, MA-4 actionable + capability-mapped, MA-5 severity calibration, MA-6 polish + voice, MA-7 gap honesty, MA-8 engagement-fit. Aggregated by geometric mean. The lane scores `findings.md` (the 9-section primary deliverable), not the prose report.

---

## 1. What the existing research already covers well

**Lens catalog (149 always-on + 25 vertical + 10 geo + 5 segment + 9 Phase-0).** Stress-tested against Conversion Factory ($1K = 99 lenses); the 167→149 reduction (3 deletions + 14 merges) is defensible; SubSignal → ParentFinding aggregation (~25-32 parent findings against ~167-177 lens firings) is the right architecture. The judge does not need to second-guess coverage; "did we look at the right things" is answered.

**Phase-0 meta-frames are a real architectural innovation.** Traffic-mix, Balfour Four Fits, trajectory, Reforge growth-loops, Kotler/Forrester maturity, share-of-voice, geo, north-star-vs-vanity, engagement proxies — sitting these above tactical lenses and tagging which frames color each finding separates a senior-operator audit from a checklist. MA-3's draft is sound.

**The 9-section IA + 4-agent fan-out + strict rubric_coverage is the right shape.** Forcing every rubric_id to be keyed `covered` or `gap_flagged` is the cleanest mechanical defense against silent omission; MA-7 becomes verifiable. The 3-tier proposal (`fix_it`/`build_it`/`run_it`) anchored to `capability_registry` makes MA-4 + MA-8 mutually constraining.

**MA-5 severity + max-of-children rollup math** is unambiguous and mechanically verifiable. **MA-6's banned-vocab + em-dash density** catches >80% of LLM-tells in practice. Both drafts have the right instinct.

---

## 2. Top 9-tier signals NOT well-covered in existing research

The existing rubric drafts measure structure (does each section have a thesis?) and traceability (does every claim cite a lens_id + URL?). They under-measure five things that separate a 7-tier "clean deliverable" from a 9-tier "CMO emails it to the team Friday."

### 2.1 Decision-changing insight density — "delete this finding, does the action survive?"
- **Description:** Mentally delete a ParentFinding; re-derive the recommended action from the remaining 24-31 findings. If the action survives, the finding was decorative. 9-tier audit: ≥18/25 findings would change either the recommended action, its severity, or its tier.
- **Source:** Balfour 2026-02-10 (`https://x.com/bbalfour/status/2021254850722595016`) — "kill 9 out of 10 things you build." Audit analogue is observation debt; Balfour's product-debt framing (`https://x.com/bbalfour/status/2019513109854277819`) names "features few customers use but create massive costs."
- **Mechanism:** Audits fail by padding, not lying. Stage-3 pulls 90+ SubSignals into 25-32 ParentFindings; without a deletion test, low-information SubSignals get rolled into parents that read fine but move no line of the proposal. Brand-replace (2.4) catches generic findings; deletion catches specific-but-inert findings.
- **Judge test:** for each ParentFinding, hash the proposal recommendations, null the finding, recompute. If proposal does not move, finding is decorative. Bar for 9: ≥18/25 change proposal. NEW rubric MA-9.

### 2.2 Contradiction surfacing — when sections disagree, the audit names it
- **Description:** Sections often disagree by implication. Findability says "organic up 22% YoY"; Brand & Narrative says "branded-search declining." Acquisition says "CAC efficient"; Lifecycle says "NRR <100%." 9-tier names tensions in a labeled "Contradictions" callout under State-of-the-Business; 5-tier lets them sit; 1-tier averages them into "mixed signals."
- **Source:** MA-1 judge asks "Are contradictions surfaced?" but treats it as a YES/NO sub-check, not a scored anchor. Emily Kramer 2026 on growth-marketing definitional disagreement (`https://x.com/emilykramer/status/1623837287615434752`) — senior operators name framework disagreement; mid-tier consultants paper over.
- **Mechanism:** Contradictions are the strongest evidence the audit was read holistically. 4-agent fan-out + Stage-3 synthesis is exactly the architecture that produces section-coherent + audit-incoherent failures.
- **Judge test:** State-of-the-Business + section opens contain ≥1 labeled contradiction with both sides cited + resolution. Bar for 9: present and resolved; for 7: named, unresolved; for ≤3: contradictions in evidence but unsurfaced. Strengthens MA-1.

### 2.3 Cross-section thread continuity — named entities recurring across ≥3 sections
- **Description:** 9-tier audit names 3-5 specific entities (competitor X, missing capability Y, buyer-persona Z) and threads them across ≥3 of 9 sections with different evidence each time. 5-tier names entities once in their owning section and abandons them.
- **Source:** Lenny 2026-05-11 Ries thread (`https://x.com/lennysan/status/2053965154845634615`) demonstrates the form — "financial gravity" threads through governance, PE acquisition, IPO, founder protection, PBC, Anthropic, Cloudflare. Same entity, different sections, different evidence. Audit analogue: a single competitive threat or missing capability appears in Findability + Brand & Narrative + Competitive + Proposal.
- **Mechanism:** 4-agent parallel synthesis tends to produce 4 disjoint mini-audits. Threading enforces Stage-3 cross-cutting actually crossed-cut.
- **Judge test:** NER over the deliverable; for top 5 named entities, count distinct sections each appears in. Bar for 9: ≥3 entities in ≥3 sections each. NEW rubric MA-11.

### 2.4 Brand-replace test — find-replace brand name, does the finding still read true?
- **Description:** Find-replace the prospect's brand with `<COMPETITOR>`. If the finding still reads true and actionable, it's boilerplate. 9-tier findings collapse: they cite specific URLs, specific page copy, specific competitors named on the prospect's actual /vs page, specific badges present or absent on the actual /security page.
- **Source:** Balfour 2026 (`https://x.com/bbalfour/status/2041290850500784138`) — "The bar just increases when everyone has access to the same tech." When everyone runs ChatGPT-generated audits, specificity is the differentiator. orr-consulting 2026 (`https://www.orr-consulting.com/post/2026-marketing-audit-checklist-10-revenue-leaks-most-teams-miss`) warns bad audits "only provide general recommendations without specific implementation steps."
- **Mechanism:** Structural defense against "ChatGPT did this audit in 90 seconds." `pricing page at /pricing has 7 tiers, top tier 'Enterprise' missing /security link` cannot survive brand-replace; `pricing page lacks clarity` survives anywhere.
- **Judge test:** sample 5 random ParentFindings; count brand-specific anchors per finding (prospect-domain URL paths, prospect-page copy quoted, prospect-named competitors with own-domain evidence URLs, prospect-specific badge/asset presence/absence). Bar for 9: every sampled finding has ≥2 anchors. NEW rubric MA-10.

### 2.5 Numeric specificity floor — counts, percentages, dollar figures, dates
- **Description:** 9-tier findings anchor to numbers: "trust signals fail on 3 of 5 surfaces; Tier-2 B2B SaaS norm is 4 of 5." 5-tier is qualitative ("trust signals weak"); 1-tier is adjectival ("robust", "comprehensive").
- **Source:** Lenny 2026-05-11 (`https://x.com/lennysan/status/2053590761804087307`) — Ries's claims work because numbered: "80% of founders fired within 3 years," "20% still CEO three years post-IPO," "$70B." Windmill 2026 Marketing Reality Check (`https://www.windmillstrategy.com/marketing-reality-check-agility-audits-alignment/`) emphasises baseline data + ROI projections.
- **Mechanism:** Numbers force evidence verification. A qualitative LLM finding survives weak evidence; a numeric finding cannot be sustained if the lens didn't fire with measured data. Forcing function on MA-2.
- **Judge test:** count numeric tokens per ParentFinding evidence_summary. Bar for 9: median ≥2; for 5: median 0-1; for 1: <30% of findings carry any number. Strengthens MA-2.

---

## 3. Top 5-tier signals (common audit mediocrity)

These pass MA-1..MA-8 as drafted but read competent-not-impressive. The judge needs to demote, not just fail to credit.

- **Checklist-deliverable shape.** Uniform finding-count across the 9 sections. Detect via stdev/mean of per-section finding counts — uniform = checklist; varied = strategically prioritised.
- **Observation-only audits.** "Your homepage above-fold lacks clarity." No hypothesis about cause, no tier-mapped recommendation. Detect: ratio of recommendations matching stock phrases ("monitor closely" / "consider improving" / "evaluate options") to capability-registry-tier-mapped recommendations.
- **Lexical inflation by synonym substitution.** MA-6 catches "robust/holistic/leverage"; the 5-tier failure substitutes adjacent fillers ("strong/comprehensive/industry-leading/drive/improve") in the same semantic slot. Detect: banned-vocab adjacency cluster, not just keyword list.
- **Boilerplate that survives brand-replace.** See 2.4. 5-tier version: findings are somewhat specific but each section carries 1-2 generic "carrier" findings filling the count.
- **Phase-0 frames named once, never invoked.** State-of-the-Business says "trajectory: declining" but sections don't reference it. Detect: count of cross-references to phase0_meta.json from per-section ParentFinding evidence_summary.

---

## 4. Slop patterns (1-tier)

Judge must zero these out. They look like findings; they are not.

- **Wikipedia-rehash.** ParentFinding restates the prospect's About / homepage / pricing copy as if diagnostic. Detect: evidence_summary string-matches >40% with site's own copy.
- **Framework theater.** Full SWOT / Five Forces / RACE / AARRR section with nothing inferred from prospect-specific data. Detect: capitalised framework names without lens_id citations underneath.
- **Recommendation void.** "Monitor closely." "Consider evaluating options." "Conduct further research." Detect: recommendation <50 words OR matches stock-vapid-phrase regex.
- **False completeness.** 25 findings, no `gap_report.md`, every rubric "covered" with zero `gap_flagged`. Near-certain lie with 149 lenses and finite tools. Detect: empty gap_report → automatic MA-7 ≤3.
- **Anonymous competitive.** "Competitors do X." Detect: in `competitive` section, count distinct named competitors with ≥1 lens-evidence URL on their own domain.
- **Stale freshness.** Audit dated today, evidence URLs accessed 18+ months ago. Detect: latest-evidence-date >90 days behind audit.created_at.

---

## 5. 2026 emerging signals (post-April-2026)

The four planning docs predate or barely catch these. The judge should weight them.

### 5.1 AI Overviews as a co-equal section, not a subsection
Catalog has Area 1 lens #21 (AI search citation) but treats it as one of 28 Findability lenses. Post-April 2026, clients lead with "where am I in AI Overviews?" The 2pointagency 2026 guide recommends a "dual scoring system, combining the SEO Health Score and AI Citation Readiness Score" — `https://www.2pointagency.com/blog/content-audit/`. CXL's AI Overview Gap Analysis 2026 (`https://cxl.com/blog/ai-overview-gap-analysis/`) frames AIO presence as the new gap-analysis primitive. **Judge implication:** the GEO/AI Visibility section should carry ≥2 ParentFindings; if 0-1, demote MA-1 — the audit underweights the discontinuity.

### 5.2 The ChatGPT-amateur baseline raises the floor
Clients in May 2026 have seen ChatGPT generate a generic audit in 90 seconds. Derivatex 2026 (`https://derivatex.agency/blog/how-to-rank-in-chatgpt/`) calls out teams treating ChatGPT citation as "just add FAQ sections" as amateur-level. The bar for "$1-3K worth" is no longer "more findings than they could generate" but "findings their ChatGPT couldn't generate." This makes the brand-replace test (2.4) and numeric-specificity floor (2.5) operationally critical — they are the structural differentiators against the amateur baseline.

### 5.3 Distribution-as-moat reframing
Lenny 2026-05-07 "Distribution is the new moat" (609 likes, `https://x.com/lennysan/status/2052407320324518151`) and Balfour 2026-02-11 on Clay + data-first marketing (`https://x.com/bbalfour/status/2021658328955515163`) crystallise a 2026 framing the April catalog does not lead with: 2026 audits should diagnose *distribution capacity* (owned channels, growth loops, data foundation enabling AI personalisation) more than channel-tactics. **Judge implication:** if Distribution section reads as a list of advertising channels rather than scoring distribution-as-moat posture, demote MA-1 — the audit is using 2024 framing.

### 5.4 Walkthrough-aware ordering
PDF-only deliverable now reads 2023. The 90-day growth audit pattern (`https://www.searchenginejournal.com/how-we-use-ai-to-run-a-90-day-growth-audit/572458/`) bundles a 30/60/90-day roadmap; Demand Local's GEO Audit Walkthrough (`https://www.demandlocal.com/blog/geo-audit-agency-walkthrough/`) emphasises walkthrough as the delivered artifact. Master plan's walkthrough-call setup is aligned; what's missing in the rubric is a check that `findings.md` orders findings by walkthrough priority (highest-impact + most-arguable first within each section), not by lens_id. **Judge implication:** MA-1 adds ordering check.

### 5.5 Governance + persuasion-to-agents (minor)
Eric Ries via Lenny 2026-05-11 (240 likes, `https://x.com/lennysan/status/2053590761804087307`): public-benefit-corp + governance as a B2B differentiator. Balfour 2026-02-10 synthetic-users (133 likes, 283 bookmarks, `https://x.com/bbalfour/status/2021291284779106407`): does the site hold up under agent-persona reading? Both are nice-to-find signals for late-stage B2B prospects — not 9-tier requirements, but their presence in Brand & Narrative / Conversion sections is a positive surprise marker for MA-1.

---

## 6. Implications for the judge — keep/strengthen/add for MA-1..MA-8

### Keep as-is
- **MA-3 / MA-5 / MA-7 / MA-8.** Drafts are sound. Strengthen the *implementations* (judge computes the MA-5 rollup itself; empty gap_report auto-demotes MA-7 to ≤3) but no rubric redesign.

### Strengthen
- **MA-1.** Currently scores thesis-per-section. The 9-tier version is thesis + threading + named-contradictions. Sub-scoring: section thesis 0-3, within-section coherence 0-3, cross-section threading (§2.3) 0-2, ≥1 named contradiction with resolution (§2.2) 0-2. Total still 0-10; floor for 7 rises.
- **MA-2.** Add numeric-specificity floor (§2.5). Bar for 9: median ≥2 numeric tokens per evidence_summary. Mechanical.
- **MA-4.** "≥50-word strategic substance" is too easy to game with adjectival filler. Add: recommendation contains ≥1 numeric anchor (capacity, timeframe, expected delta) AND maps to a SPECIFIC `capability_registry` item (not just a tier).
- **MA-6.** Add lexical-inflation cluster detection (§3) — catches synonym substitution past the banned-vocab list.

### Add NEW rubrics

These three are the structural defenses against the 2026 amateur-baseline. Each is independently scoreable; adding them to the geometric mean is the load-bearing change.

**MA-9 — Decision-changing insight density.** Score 0-10. Anchors:
- **1:** <8 of 25 findings would change the proposal under deletion. Audit is observation theatre.
- **3:** 8-12 / 25 findings change proposal. Half the deliverable is decorative.
- **5:** 13-17 / 25 change proposal. Acceptable density; not impressive.
- **7:** 18-22 / 25 change proposal. Each finding earns its slot.
- **9:** ≥23 / 25 change proposal AND ≥3 findings would reframe a `build_it` or `run_it` tier item. Every finding is load-bearing.

Verification: rubric judge re-derives proposal recommendations with each ParentFinding nulled in turn; compares hashes. Computable, deterministic.

**MA-10 — Brand-specificity floor (brand-replace test).** Score 0-10. Anchors:
- **1:** find-replace brand name; ≥18/25 findings still read true. Generic-B2B-SaaS audit.
- **3:** 13-17/25 still read true. Mostly generic.
- **5:** 8-12/25 still read true. Mixed.
- **7:** 3-7/25 still read true. Mostly brand-specific.
- **9:** ≤2/25 still read true. Findings are deeply anchored to THIS prospect's URLs, copy, competitors, pricing.

Verification: sample 5 random ParentFindings, count brand-specific anchors per finding (prospect-domain URL paths quoted, prospect-page copy quoted, prospect-named competitors with own-domain evidence URLs, prospect-specific badge/asset presence/absence). Bar for 9: every sampled finding has ≥2 brand-specific anchors. Strict numeric check.

**MA-11 — Cross-section thread continuity.** Score 0-10. Anchors:
- **1:** no named entity appears in >1 section. Four parallel mini-audits.
- **3:** top entity appears in 2 sections; no other entity threads.
- **5:** 1-2 entities thread across ≥3 sections.
- **7:** 3 entities thread across ≥3 sections.
- **9:** ≥3 entities thread across ≥3 sections AND State-of-the-Business explicitly references the threaded entities by name.

Verification: NER over the deliverable, count distinct sections per entity, threshold-compare. Computable.

### Rubric stack + verification
MA-1..MA-8 kept (MA-1/2/4/6 strengthened internally) + MA-9/10/11 added. Geometric mean across 11. The geometric-mean property — single-rubric-floor kills overall — means the anti-slop rubrics are mandatory defenses, not optional credit. An audit scoring 9-9-9-9-9-9-9-9 on MA-1..8 but 2 on MA-10 (boilerplate survives brand-replace) drops geomean to 5.9, correctly demoting competent-but-generic. MA-8 feeds back T+60d via lineage.jsonl; MA-9/10/11 are mechanically computable at judging time; MA-2/5/7 are mechanically verifiable; MA-1/3/4/6 remain LLM-judged. ~6 of 11 become mechanical or semi-mechanical — healthy variance reduction for the evolve loop.

Sources for the 2026 deltas:
- [2pointagency 2026 Content Audit Guide](https://www.2pointagency.com/blog/content-audit/)
- [CXL AI Overview Gap Analysis 2026](https://cxl.com/blog/ai-overview-gap-analysis/)
- [Demand Local GEO Audit Agency Walkthrough 2026](https://www.demandlocal.com/blog/geo-audit-agency-walkthrough/)
- [orr-consulting 2026 Marketing Audit Checklist](https://www.orr-consulting.com/post/2026-marketing-audit-checklist-10-revenue-leaks-most-teams-miss)
- [Windmill Marketing Reality Check 2026](https://www.windmillstrategy.com/marketing-reality-check-agility-audits-alignment/)
- [Derivatex How To Rank In ChatGPT B2B SaaS Playbook 2026](https://derivatex.agency/blog/how-to-rank-in-chatgpt/)
- [Search Engine Journal 90-day Growth Audit With AI](https://www.searchenginejournal.com/how-we-use-ai-to-run-a-90-day-growth-audit/572458/)
- [Balfour on AI access raising the bar](https://x.com/bbalfour/status/2041290850500784138)
- [Balfour on data-first marketing + Clay](https://x.com/bbalfour/status/2021658328955515163)
- [Balfour on killing 9 of 10 features](https://x.com/bbalfour/status/2021254850722595016)
- [Balfour on product debt](https://x.com/bbalfour/status/2019513109854277819)
- [Balfour on synthetic users for strategic feedback](https://x.com/bbalfour/status/2021291284779106407)
- [Lenny on Distribution is the new moat](https://x.com/lennysan/status/2052407320324518151)
- [Lenny on Eric Ries Incorruptible thread (governance)](https://x.com/lennysan/status/2053965154845634615)
- [Lenny Incorruptible launch post](https://x.com/lennysan/status/2053590761804087307)
- [Emily Kramer on growth-marketing definitional disagreement](https://x.com/emilykramer/status/1623837287615434752)
