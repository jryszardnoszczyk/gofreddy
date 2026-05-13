---
date: 2026-05-12
phase: A
topic: lane purposes — what does each lane actually produce of value for clients
---

# Phase A — Lane Purpose Docs

For each lane, four questions:

1. **What does the output do for the client?** (concrete deliverable, not abstract benefit)
2. **What's the actionable next step?** (publish, paste into Jira, hand to lawyer, etc.)
3. **What's the test of success?** (measurable from the client's side)
4. **What does the ceiling — the 9-tier version — look like?**

Plus, the implication for the judge: **what's the optimization target the rubric needs to score against?**

This is the scaffold every downstream phase grounds in. Phase B (domain research) anchors against the ceiling per lane. Phase C (variant rating) rates against the ceiling. Phase D (judge criteria) writes criteria that grade for the optimization target.

---

## Cross-lane pattern: three types of lane output

Before per-lane detail, the lanes group into three value-types. The judge's *shape* differs by type:

### Type 1 — Content-for-publish
**Lanes:** `geo`, `x_engine`, `linkedin_engine`, `article_engine`, `image_engine`, `ad_engine`, `storyboard`

**Pattern:** Client takes the artifact and publishes it. The artifact IS the deliverable. No transformation step between gofreddy's output and the client's audience seeing it.

**Judge optimization target:** Ship-eligibility — would the operator publish this unedited? Plus channel-specific performance prediction — would AI engines cite this? Would scrollers stop? Would the algorithm distribute it?

**Implication:** Ceiling anchor = "operator publishes unedited and the artifact performs above their baseline." Rubric grades the causal levers toward that.

### Type 2 — Decision-support
**Lanes:** `competitive`, `monitoring`, `marketing_audit`

**Pattern:** Client takes the artifact and makes decisions / takes actions. The artifact is intermediate — its value realizes through downstream actions.

**Judge optimization target:** Decision-changing signal density. Every finding/recommendation/insight either changes what the client does or it's filler.

**Implication:** Ceiling anchor = "client makes a non-arguable decision from this; deletion of any finding leaves a visible hole in the recommendation set." Rubric grades for that.

### Type 3 — Cross-cutting compliance
**Lanes:** `medical_pl`, `legal_pl` (applied across content-for-publish lanes)

**Pattern:** Judge fires on every content-for-publish artifact before delivery. Hard-block / soft-warn signals route to human gate.

**Judge optimization target:** False-negative rate on real statutory violations (load-bearing for evolution direction) + false-positive rate (don't choke the loop with overcautious blocks).

**Implication:** Ceiling anchor = "catches 95%+ of statutory violations on a legally-reviewed benchmark, false-positives <5%." This requires real legal-review-validated benchmark data — the Resolve-Before-Planning gate.

---

## Per-lane purpose statements

### 1. `geo` (Generative Engine Optimization)

**Output:** `optimized/<file>.md` (page content optimized for AI search engines) + `gap_allocation.json` (which queries are uncovered) + JSON-LD schemas per page.

**Client:** SEO operator / agency / direct site owner. **v1 demo:** Klinika procedure pages — pages like `/zabiegi/botoks` optimized so AI engines cite them when users ask "ile kosztuje botoks w Warszawie" or "botoks przeciwwskazania."

**Actionable next step:** Client replaces or merges the optimized content into existing pages, implements the JSON-LD, acts on gap_allocation by commissioning new pages for uncovered queries.

**Test of success:**
- AI engines (ChatGPT Search, Perplexity, Google AI Overviews, Claude with browse, Bing Copilot) cite the page in answers to declared target queries within 60-90 days of publish
- Share-of-voice in AI answer-mode for target query domain
- Organic traffic from AI-referrer attribution (ChatGPT, Perplexity referers in GA4)
- Long-tail: declines in traditional Google CTR offset by AI citation reach

**Ceiling (9-tier):** The page becomes THE canonical source AI engines cite for the query cluster. Not "got cited once" — consistent surfacing across the full fan-out of target queries (literal + variant + sub-intent), with the page's specific numbers, named experts, and primary-source links being what AI quotes verbatim.

**Optimization target for judge:** Maximize likelihood that AI engines (a) cite the page and (b) faithfully extract its content. Every criterion grades a causal lever — chunk extractability, named-expert quotes in `"..."`, inline primary citations, query fan-out coverage, freshness, schema attribute richness, answer-first paragraph framing.

---

### 2. `competitive` (Competitive Intelligence)

**Output:** `brief.md` (multi-section strategic brief on N competitors) + `competitors/<name>.json` (per-competitor structured profile: pricing, positioning, hiring signals, financial signals, leadership).

**Client:** PM / strategist / CMO of the target company. Primarily internal use; secondarily fed into the agency engagement.

**Actionable next step:** Client reads brief in 20-30 min, walks into a strategy meeting, makes a tactical decision. Examples:
- "Reroute Q3 paid spend to branded-defense terms because competitor X is intercepting BoFU queries"
- "Kill feature Y because competitors all have it but customers don't value it"
- "Press advantage Z before competitor W closes the gap"
- "Concede category A — they're too far ahead — and lean into adjacent B"

**Test of success:**
- Decisions traceable to brief findings within 30 days. Operator says "we did X because of this brief."
- Stakeholder forwards: brief shared with founder/board because it changes the strategic conversation
- Time savings vs. internal analyst: the brief replaces 1-2 weeks of analyst work

**Ceiling (9-tier):** Brief that makes a CMO say "this is what I would have paid $20K to McKinsey for." Specific, named-competitor, dated evidence. Decisive in framing — picks ONE strategic lens (Wardley / JTBD / Porter applied not recited) and stays with it. Surfaces uncomfortable truths the client's team avoids saying out loud. Top-3 recommendations have explicit impact + effort + owner-archetype + success-metric.

**Optimization target for judge:** Density of decision-grade insights with executable implications per 500 words. NOT breadth of coverage. NOT framework-completeness theater. Triangulation depth (≥2 independent source classes per load-bearing claim). Forward-signal predictions (trajectory, not snapshot). Data-gap honesty.

---

### 3. `monitoring` (Brand/Competitor Mentions Digest)

**Output:** Weekly `digest.md` (synthesized mention summary) + `stories/*.json` (event clusters with primary + secondary sources) + recommendations (action items with owner/timing/consequence).

**Client:** Brand manager / comms lead / founder watching brand + competitor signal across news, social, forums, podcasts, reviews.

**Actionable next step:** 10-min Monday read. Client takes 2-3 actions this week:
- Respond publicly to a critical thread by Tuesday
- Brief PR on emerging risk before it hits trade press
- Congratulate a stakeholder mentioned in a positive context
- Pre-empt a competitor announcement with their own positioning
- Forward specific items to specific stakeholders (founder gets X; PR gets Y; product gets Z)

**Test of success:**
- Actions taken this week, traceable to digest items
- Stories the digest flagged correctly preceded events the client should have known about (no surprise hits to inbox after the digest)
- Client returns to reading the digest weekly without prompting
- "I would have missed X without this" feedback from operator

**Ceiling (9-tier):** Digest so prioritized, faithful, and decision-ready that the client feels paranoid not reading it. Top-3 stories non-arguable in ranking (impact × reach × novelty justified). Same event from 6 syndications collapses to 1 cluster with primary + secondaries. Author/source weighted (founder tweet vs. random-account complaint vs. verified journalist). Compound narratives ("X + Y together signal Z"). Forward hooks for next week.

**Optimization target for judge:** Decision-affecting signal per unit reading time. Zero fabrication (hallucinated quote = entire digest unreliable; auto-cap). Story canonicalization (no duplicate-as-multiple-stories inflation). Prioritization fidelity (not by volume).

---

### 4. `storyboard` — 3 format_modes (narrative / educational / brand_authority)

**Output:** `stories/*.json` (PLAN_STORY phase) or `storyboards/*.json` (IDEATE phase). Each story: scene_plan, voice_script, emotional_map, consistency_anchors, duration_target, scene_count.

**Pipeline:** Stories → fal.ai I2V → composed video output. Storyboard is the *callable spec* the AI video pipeline consumes — not a narrative scaffold for human filmmaking.

#### 4a. `narrative` mode (current default)
**Client:** Creator / brand producing AI-generated long-form video for YouTube / streaming.

**Test of success:** Viewer retention curve > platform median; emotional arc lands (comments mention specific beats); watch-through rate.

**Ceiling:** Story plan that generates video a YouTuber would post unedited, with a hook → escalation → climax → resolution arc viewers feel rather than parse.

#### 4b. `educational` mode (NEW for Klinika v1)
**Client:** Klinika producing TikTok/Reels educational explainers — "5 myths about Botox," "what to expect before your first lip filler," "is dermal peel right for your skin type."

**Actionable:** Stories pipe into AI video pipeline → 15-60s vertical video → published to Klinika TikTok / IG Reels.

**Test of success:** Viewer learns one specific thing (measured by qualitative engagement / comments mentioning the takeaway). Engagement above platform median for educational vertical content. Share rate (educational content's share-worthy criterion).

**Ceiling:** Storyboard that generates video a viewer scrolling at TikTok speed stops on, watches to the end, and saves or shares. Information-dense without being lecture-y. Compliance-clean (medical_pl: no specific results promises, no "best/cheapest," no comparative claims).

#### 4c. `brand_authority` mode (NEW for DWF v1)
**Client:** DWF producing LinkedIn explainer videos under partner byline — "what KSeF 2026 actually means for your business," "Polish Grid Act 2026 vs the EU directive."

**Actionable:** Stories pipe into AI video pipeline with partner voiceover anchored to corpus → 60-180s LinkedIn-native video → published to partner's LinkedIn profile.

**Test of success:** LinkedIn engagement formula (reactions × 1 + comments × 3 + shares × 5) above partner's baseline. Buyer trust signals: profile views from named buyer-account profiles, inbound DMs about retainer / case engagement.

**Ceiling:** Storyboard that generates video a senior B2B buyer DMs to a colleague with "you should watch this." Authority-anchored (named case experience, dated decisions), partner-voice-pure, compliance-clean (legal_pl: no solicitation, no fee mentions, no comparative).

**Optimization target for judge (per mode):**
- narrative: emotional arc landing + retention
- educational: knowledge transfer + share-worthiness + compliance
- brand_authority: trust + B2B engagement formula + voice fidelity to named partner

---

### 5. `marketing_audit`

**Output:** 9-section `findings.md` + `report.html` + `report.pdf` + `proposal.md` (capability-mapped engagement pitch with fix_it / build_it / run_it tier entries) + `surprises.md` + `gap_report.md`.

**Client:** Agency selling $1-3K paid audits via the funnel: free AI Visibility Scan → sales call → invoice → paid audit → walkthrough call → $15K+ engagement. Secondary client: the prospect/end-customer who receives the audit.

**North Star (per master plan):** *"First-runnable pipeline that produces a marketing audit deliverable JR would proudly send to a paying client at $1–3K, generated end-to-end by an automated run — no manual prose-writing."*

**Actionable next step (agency):** Hand audit + proposal on walkthrough call. Proposal entries map top findings to capability registry tiers; agency closes engagement.

**Actionable next step (prospect):** Reads audit, makes operational decisions about marketing fixes. Top-3 findings drive their next quarter's marketing priorities.

**Test of success:**
- Audits close $15K+ engagements at >30% rate (agency goal)
- Prospects who didn't engage still implement >50% of recommendations within 90 days (audit standalone value)
- Audit time-to-decision: prospect can act on it without follow-up questions

**Ceiling (9-tier):** Audit a CMO emails to their team saying "everyone read this, we're discussing Friday." Specific, evidence-rooted per finding (link, screenshot, quote), contradictions named (not hidden). Top-3 findings non-arguable. Proposal feels purpose-built for the prospect — capability_ids match prospect's vertical/segment/maturity. Audit hits the $15K-engagement-pull threshold.

**Optimization target for judge:** Decision-changing insight density + engagement-pull (severity-3 findings map to build_it/run_it; capability_id ∈ registry; shape-fit to prospect). PLUS the gap-honesty pitfall (hiding measurement gaps = capped score). PLUS the deterministic checks already in MA-5/MA-7/MA-8 (severity rollup, capability registry conformance, banned vocab).

---

### 6. `x_engine`

**Output:** `drafts/<id>.md` with frontmatter (platform, length_bracket, voice_pillar, char_count) and body text. Length brackets: sharp (250-300 chars), build (500-900), case_study (1000-1500). Plus `angles/<id>.json` upstream.

**Client:** Operator (JR + future clients) building audience on X.

**Actionable next step:** Operator reviews drafts in batch, picks N to ship per week, posts them unedited. Drafts are publish-ready, not "starting points."

**Test of success:**
- Published drafts perform above operator's baseline (impressions, engagement, replies, follows)
- Audience growth (followers, profile views, DMs from real buyers)
- Operator stops writing X content manually because the engine produces better drafts than their handwritten ones
- Ship-eligible rate: % of generated drafts the operator publishes (target: ≥30% of drafts ship, ≥50% are at least near-ship)

**Ceiling (9-tier):** Drafts indistinguishable from operator's best handwritten posts. Specific (proper-noun + numeric density), voice-pure, hook-strong, zero AI tells, reply-worthy structure, algorithmically-friendly (no external links, native to X). Each draft passes "would the operator screenshot this for their portfolio" test.

**Optimization target for judge:** Ship-eligible draft rate. The judge isn't scoring "is this good content" abstractly — it's predicting "would operator publish this unedited." Veto patterns (LinkedIn-on-X, growth-bait, AI tells) cap the score because one slop marker burns the whole post.

---

### 7. `linkedin_engine`

**Output:** `drafts/<id>.md` with frontmatter (platform, length_bracket, hashtag list, voice_pillar) and body. Length brackets: short_take (500-900), thought_leader (1500-2500), case_study (2500-3000). Plus `angles/<id>.json`.

**Client:** Operator (JR + clients) building B2B trust and pipeline on LinkedIn.

**Actionable next step:** Operator reviews + ships 1-3 drafts per week. Drafts come with correct hashtag count (3-5), bracket-fit body, hook tested against pre-fold cutoff.

**Test of success:**
- LinkedIn engagement formula (reactions × 1 + comments × 3 + shares × 5) above operator's baseline
- Inbound generation: DMs, demo requests, partnership inquiries from real B2B buyers
- Buyer trust signals: profile views from named buyer-account profiles, connection requests from decision-makers
- Ship-eligible rate ≥30%

**Ceiling (9-tier):** Drafts a senior B2B buyer DMs to a colleague. Frameworkable artifact present (list, decision matrix, named principle, checklist someone forwards). Operationally specific (named clients, dated decisions, real numbers). Buyer's-problem-centric — protagonist is the reader's problem, not the author's growth story. Pre-fold hook delivers a stake-claim that earns the "see more" click.

**Optimization target for judge:** Ship-eligible draft rate + share/save trigger (the engagement formula's heaviest lever). Anti-broetry cadence + B2B trust posture as essentials. Cringe-veto pitfall (Uber-driver opener, motivational poster, fake vulnerability = score cap).

---

### 8. `article_engine` (NEW)

**Output:** Per platform-target subset of {`blog`, `linkedin_article`} (x_article deferred to v1.5), one canonical platform-agnostic body adapted into:
- `articles/blog/<slug>.md` with SEO meta + JSON-LD Article schema + body-image briefs (consumed by image_engine)
- `articles/linkedin_article/<slug>.md` with first-200-char hook + LinkedIn paragraph cadence + header-image brief

Plus consumed findings-brief from `geo` (Klinika SEO topics) or `monitoring` (DWF regulatory events).

**Client:**
- **Klinika** publishes blog procedure-pages (`klinika.pl/zabiegi/<procedure>`) and LinkedIn Articles under Dr. Maria's byline
- **DWF** publishes blog regulatory explainers and LinkedIn Articles under named partner bylines

**Actionable next step:** Article goes through human compliance gate (`medical_pl` for Klinika, `legal_pl` for DWF) and brand-fit review. On approval, client (or agency on their behalf) publishes to their site / LinkedIn.

**Test of success:**
- **Blog:** AI-search citations within 60-90 days; organic search traffic + dwell time; conversions (consultation booked, demo requested)
- **LinkedIn Article:** Engagement formula (reactions/comments/shares) + buyer trust signals (profile follows, inbound from named buyer accounts)
- Voice fidelity: domain expert (Dr. Maria / DWF partner) recognizes it as something they would have written

**Ceiling (9-tier):** Article that the named expert byline (Dr. Maria, DWF partner) reads and says "this is what I would have written if I had the time." Citation-grade authority (≥2 sources per load-bearing claim, named experts in `"..."`, freshness markers). Specific named case examples within compliance bounds. Voice-pure to corpus.

**Optimization target for judge:**
- Long-form structural quality (argument coherence across multi-section thesis, citation density, skimmability)
- Per-platform-adaptor fit (blog SEO health vs LinkedIn pre-fold hook)
- Voice fidelity (corpus-grounded; cross-references `voice_persona.corpus_path`)
- Compliance precondition (judge can't score above 5 if compliance regime hard-blocks)

---

### 9. `image_engine` (NEW)

**Output:** `images/<format>/<slug>/` with composed PNG/JPG/SVG. Formats: `ig_carousel` (per-slide image + text overlay + alt-text), `li_doc_carousel`, `hero_banner`, `ad_static`. Each carousel includes per-slide spec + brand stamp + cross-slide arc.

**Client:**
- **Klinika:** educational IG carousels ("5 myths about Botox" style — compliance-safe), hero images for landing pages, ad statics
- **DWF:** LinkedIn document carousels (KSeF timeline, Polish Grid Act process), hero banners for explainer articles

**Actionable next step:** Composed images go through compliance gate + brand-fit human review. Client (or social-ops team) schedules to IG / LinkedIn or uploads to ad platform.

**Test of success:**
- **First-slide stop-scroll rate** (early-engagement algorithmic signal for IG/LinkedIn)
- **Carousel completion rate** (swipes-to-last-slide ratio)
- **Save rate** (LinkedIn document carousels — saves > likes is the signal)
- **Share rate**
- Reach/impressions above account baseline

**Ceiling (9-tier):** Visual that someone scrolling at platform speed (IG: ~1.5 sec/post, LinkedIn: ~2 sec) stops on, swipes through, saves, screenshots, and DMs to a colleague. Brand-stamped consistently, legible at thumbnail size, distinct from generic stock-feel AI imagery, alt-text accessible, last slide carries CTA.

**Optimization target for judge:**
- Hook visual (first-slide stop-scroll prediction) — needs VISION JUDGE (Gemini Vision pattern from `render_judge.py`)
- Brand consistency (against client brand-style-guide cross-reference)
- Carousel arc (narrative across slides, not 10 disconnected images)
- Format compliance per platform (IG 10-slide max, LinkedIn doc carousel different)
- Compliance precondition (medical_pl on Klinika imagery — no clinical procedure depictions per R1 narrowing)

---

### 10. `ad_engine` (NEW)

**Output:** Per campaign brief, 3-5 ad variants per format. v1 scope:
- **Klinika:** Meta Reels ad scripts (15-60s video creative) + Meta image/carousel ads
- **DWF:** LinkedIn Sponsored Content (single-image, document, or video ads)

Per variant: creative copy + image-or-video brief (consumed by image_engine / storyboard) + matched landing-page hero copy.

**Client:**
- **Klinika:** paid Meta ads driving consultation bookings
- **DWF:** LinkedIn Sponsored Content driving partner-track inquiries / retainer conversations

**Actionable next step:** Variants go through compliance gate (medical_pl / legal_pl) + brand-fit review. Client (or paid ad-ops team) loads into Meta Ads Manager / LinkedIn Campaign Manager. LP hero copy updates the landing page to match. Variants run in test set; winning variant scales.

**Test of success:**
- **CTR** above platform vertical benchmark
- **CVR** (consultation booked / partner-track inquiry submitted)
- **CPA** below client's threshold
- **Variant diversity test:** top 2 winning variants have meaningfully different angles, not 5 wordings of one bet
- **LP coherence:** LP hero copy delivers on ad headline promise (no bait-and-switch)

**Ceiling (9-tier):** Ad set where every variant could plausibly win because all 3-5 are different defensible bets. Hook stop-power on slide 1 (Meta) or first 2 lines (LinkedIn). Specific offer with named outcome. CTA clarity (not "Learn more" — actual next action). Compliance-clean. LP hero matches ad promise.

**Optimization target for judge:**
- Per-variant ship-eligibility (hook + CTA + offer + format compliance + voice)
- Cross-variant diversity (3-5 different angles / messages / hooks, not redundant wordings)
- LP coherence (cross-artifact check: does LP hero deliver on ad headline?)
- Market-signal alignment (creative features correlated with Foreplay winners — dimension dropped if Foreplay reliability fails)
- Compliance precondition

---

### Compliance regime (`medical_pl` + `legal_pl`) — cross-cutting

**Output:** Per-artifact compliance metadata:
- `compliance_flags`: list of flagged rules with severity (hard-block / soft-warn)
- `human_review_required`: bool (default true for any artifact with any flag)
- `evolution_signal`: per-rule pass/fail aggregated for in-loop fitness scoring

**Two-gate design (per v1 brainstorm R22):**
1. **In-loop fitness judge** — drives evolution toward compliance-clean output; hard-block triggers regeneration; soft-warn flagged in metadata
2. **Pre-publish human gate** — load-bearing risk control; legal liability is client's, not gofreddy's

**Client:**
- Evolution loop (fitness function consumer)
- Human reviewer (Klinika medical-advertising-aware, DWF bar-rules-aware)

**Actionable next step:**
- Loop discards or regenerates hard-block variants
- Human reviewer triages soft-warns before client delivery

**Test of success:**
- Zero compliance violations in published artifacts (the ultimate test)
- Hard-block rate trends down across evolution generations (loop learns to avoid violations)
- False-positive rate stays low (loop isn't choked by overcautious blocks)
- Wrong-call rate <5% on a legally-reviewed benchmark of known-compliant + known-violating artifacts

**Ceiling (9-tier):** Compliance judge that catches 95%+ of statutory violations on a legally-reviewed benchmark, with <5% false-positive rate. Severity assignment correct (true Art. 14 violations = hard-block; ambiguous educational framing = soft-warn). Trigger phrases / patterns specific enough that a Polish medical-advertising-aware reviewer would agree with each flag.

**Optimization target for judge:**
- False-negative rate on real statutory violations (load-bearing for evolution direction)
- False-positive rate (keeps loop functional)
- Severity-tier accuracy (hard-block vs soft-warn boundary)

**Content gated on Resolve-Before-Planning #2** — specific trigger phrases per rule per severity require legal-review input. Phase B research for compliance regime focuses on *publicly available* Polish statutory text + medical/legal advertising case law summaries, but the loaded benchmark for false-positive/false-negative measurement is operator-provided.

---

## Implications for judge design (cross-lane)

Six principles surface from the per-lane purposes that should govern the rubric design across all lanes:

### 1. The ceiling is operationally defined, not aesthetically defined

Every lane's ceiling is "client publishes / acts / closes engagement" — concrete behavioral outcomes. Not "comprehensive" or "polished." The rubric anchors should reference these outcomes in their score-9 prose.

### 2. Ship-eligibility ≠ rubric-passing

For content-for-publish lanes, the judge's job is to predict whether the operator will publish unedited. Several existing rubrics drift toward grading abstract quality dimensions that don't correlate with publish-decision. The new rubrics should anchor each criterion to: *if this criterion fails at score-2, would the operator decline to publish?* If no, the criterion isn't load-bearing.

### 3. Decision-changing density is the master signal for Type 2 lanes

For competitive / monitoring / marketing_audit, the judge optimizes for *findings that change client behavior*. Not breadth. Not framework completeness. The brand-replace test (would this finding still read true after find-replacing the brand name?) is universal across decision-support lanes.

### 4. Cohort-level criteria are load-bearing where the value is in the portfolio

x_engine, linkedin_engine, ad_engine, storyboard, image_engine — value is in the *batch* (3-5 distinct ads, 5-7 ship-eligible drafts per week, 5 distinct storyboards sharing a creative universe), not any single artifact. Cross-item criteria (already exist as GEO-6, SB-8, X-6, LI-6) need to extend to the new lanes and become more demanding.

### 5. Cross-artifact ground-truth verification is the strongest pattern in current rubrics

GEO-4 vs page content, GEO-8 vs original audit data, CI-4 vs client baseline, MA-5 deterministic rollup, MA-8 capability registry conformance — these are the criteria that *can't be argued with* by an inflating judge. New lanes need analogous patterns:
- article_engine: voice fidelity vs `voice_persona.corpus_path`
- image_engine: brand consistency vs brand-style-guide tokens
- ad_engine: LP coherence vs landing page hero copy

### 6. Compliance is precondition, not criterion

For all content-for-publish lanes touching Klinika/DWF clients: the compliance judge fires *before* the quality judge. A hard-block from medical_pl/legal_pl means the artifact never reaches the quality judge for scoring. Soft-warn flags but doesn't gate. This means quality criteria assume compliance has already passed — they don't need to grade "is this legal" themselves.

---

## What Phase B does with this

Phase B builds, per lane, a calibration corpus grounded in these purpose statements:

- **For content-for-publish lanes:** scrape current high-performing examples in the target channel via X API / WebSearch — Justin Welsh's LinkedIn posts, Dwarkesh's X content, top Klinika-aesthetic creators on TikTok, top B2B law firms on LinkedIn, top SEO-cited pages in AI Overviews for medical queries. Mine for what 9-tier looks like in 2026.

- **For decision-support lanes:** find publicly available high-quality competitive briefs, mention digests, marketing audits. Mine for what decision-changing density looks like in practice. Lean on the existing 5,000 lines of marketing_audit research as a starting calibration corpus.

- **For compliance regime:** read publicly available Polish medical and legal advertising statute summaries + case law. Note that specific trigger-phrase content needs legal-review input; Phase B can produce the *framework* (rule categories, severity tier examples) without violating the legal-review gate.

Phase C then rates archived variants per lane against the calibration corpus — operator-vs-judge gap analysis.

Phase D writes the rubric criteria grounded in A+B+C.
