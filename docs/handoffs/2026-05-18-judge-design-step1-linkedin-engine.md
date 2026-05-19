---
date: 2026-05-19 v2
type: judge-design Step 1 — linkedin_engine optimal-output spec
status: DRAFT v2 — School B multi-component restructure (text-post locked at judge layer; broader program validated by structural_gate); awaiting pairwise redundancy check + fixture validation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
sibling_spec: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.4 gold-standard structure)
companions:
  - docs/research/2026-05-19-linkedin-engine-comprehensive-scope.md (Step 0 — full 2026 LinkedIn surface mapping, 25 activities × 5 layers)
  - docs/research/2026-05-18-judges-domain-linkedin-engine.md (generalist domain research)
  - docs/research/2026-05-18-linkedin-engine-van-der-blom-depth.md (Depth Score deepening)
  - docs/research/2026-05-18-linkedin-engine-ai-slop-li-specific.md (AI-slop axis deepening)
  - docs/research/2026-05-18-linkedin-engine-author-context-coherence.md (author-context axis deepening)
  - docs/research/2026-05-18-linkedin-engine-comment-seed-quality.md (comment-seed axis deepening)
revision_history:
  - 2026-05-18 v0 — initial draft, 5 criteria, before research deliverables consumed
  - 2026-05-18 v1 — research-synthesized: gestalt-stack reinforcement in LI-3, outcome-shaped anchor + 4 mechanism families + reply-ladder CoT in LI-4, 3 register-mismatch examples + structural_gate hoist in LI-5, §1.5 Artifact-shape LOCKED, §3 "looks like slop but isn't" defense, structural_gate routing block, Topic Authority signal awareness in §5 wrapper. 5 criteria — no 6th. AI-failure surfaces route to structural_gate, not a documented exception.
  - 2026-05-19 v2 — School B multi-component restructure per `docs/research/2026-05-19-linkedin-engine-comprehensive-scope.md`. Lane scope expanded from single text post to a multi-component LinkedIn program (Components A–H). Component A = text post is LOCKED at the judge layer (LI-1..LI-5 prose unchanged from v1; all 4 surgical-restoration folds preserved). Components B–H (profile audit + content strategy + comment strategy + DM templates + 30/60/90 + Topic Authority plan + cross-platform syndication) are validated by `structural_gate`, NOT by the judge. Sibling-lane forks (linkedin_carousel, linkedin_newsletter, linkedin_live, linkedin_profile, linkedin_comment_strategy) are deferred to §8 triggered expansion. Modern-lever bias (Topic Authority 78% distribution lift, comment-strategy as dominant audience-build) threaded throughout. §3 cuts (20 from 2018–2023 playbook) and §3 adds (15 modern levers) flow into score-1 / score-0 anchors only where they extend existing v1 anchors; LI-1..LI-5 prose itself is untouched. US-primary defaults; substitute readers broadened to SaaS / AI lab / agency / service firm / finance / e-commerce. Total spec body ≈ 8,500 words.
---

# LinkedIn Engine — Optimal-Output Spec (DRAFT v2 — School B multi-component restructure)

Conforms to `docs/rubrics/judge-design-guide.md`. Frameworks (Van Der Blom, Justin Welsh, Lara Acosta, Jasmin Alić, Tim Denning, Ben Meer, Daniel Murray, Sahil Bloom, Edelman/LinkedIn 2025 report, Berlo competence/dynamism, Cialdini authority, Pornpitakpan, Graham's hierarchy, WikiDisputes) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

LinkedIn is structurally different from X: longer-form professional posts, dwell-and-substantive-comment as the unit of success rather than viral re-share, and a 2026 algorithm (360Brew + Depth Score + Topic Authority) that has converted credibility-coherence and comment substance from soft signals into algorithmic gates. The spec encodes these as outcome questions, not as feature checklists — the Phase 4 rollback at `c76f051` (commit `698e658`) is the load-bearing prior incident the criteria are designed to resist re-creating.

**v2 architectural shift.** The v1 spec scoped a single text-post artifact. The Step 0 research at `docs/research/2026-05-19-linkedin-engine-comprehensive-scope.md` maps the full 2026 LinkedIn surface — roughly 25 distinct activities across five layers (profile foundation, content production, distribution & engagement, funnel mechanics, measurement & strategy) — and concludes that a real 2026 LinkedIn program for a small-to-medium tech-savvy client is a multi-part deliverable comparable in envelope to the marketing-audit lane, not a single post. v2 expands the **lane scope** to that multi-component deliverable (Components A–H below) while keeping the **judge scope** locked on Component A (the text post). Components B–H are validated deterministically by `structural_gate` — they have shape-checkable structure (profile field completeness, voice-substrate provenance, strategy-section presence, comment-target validity, DM-template shape, roadmap milestones, Topic Authority pillar specification, cross-platform rule presence) that does not require semantic judgment.

This is "School B" per JR's confirmation: keep v1 text-post atomic at the judge layer; broaden the program around it; defer sibling-lane forks (linkedin_carousel, linkedin_newsletter, linkedin_live, linkedin_profile, linkedin_comment_strategy) to triggered expansion in §8 once client demand crosses three.

The v1 surgical-restoration content from cross-check pass agent `a9a34cd5ea2d02315` is preserved verbatim at the judge layer: LI-1's live "thoughtful authority, not contrarian punch" lever survives as the LI-3 score-0 bait-y/Twitter-translated anchor; LI-2's live HARD FLOOR "lived-work claims REQUIRE the named entity in voice.md" survives as the LI-3 score-0 unanchored-lived-work-claim anchor; LI-3's live "contrarian hot-takes that work on X" survives as the LI-4 score-0 cross-platform reply-ladder collapse anchor; LI-5's live graduated hashtag-count scoring stays retired to `structural_gate`; LI-6 cross-cohort survives at the workflow level via `CrossItemCriterion`, not as a 6th judge criterion.

Each elaboration earns its length against a documented failure mode: §1.5 Component A LOCKED defends shape-drift Goodhart under 50-generation pressure at the judge layer; the "looks like slop but isn't" defense in §3 prevents false-positive over-suppression of legitimate operator voice; LI-3's gestalt-stack reinforcement defends against single-tell whack-a-mole; LI-4's mechanism-families + reply-ladder CoT defend against bolted-on bait; LI-5's register-mismatch focus + structural_gate hoist defend against the AI-loop-most-likely failure mode (authority-voice register one stage above or below the author's seat). The 5-criterion ceiling holds at the judge layer — all AI-failure surfaces and all Components B–H validation route to structural_gate, NOT to a documented 6th-criterion exception.

---

## 1. Reader (LOCKED 2026-05-18, US-primary defaults broadened 2026-05-19)

A LinkedIn power-user reading the feed during their morning scroll or between meetings. Specifically one of four primary audience types (preserved from v1):

- **Founder / decision-maker** at $1M–$50M ARR scanning for pattern-recognition from someone who solved the same problem; rewards specific numbers and named trade-offs; comments in 30–60-word ranges with a specific case
- **Mid-career B2B IC** (engineer, marketer, product, sales) looking for tactical insight to use in tomorrow's meeting; rewards step-by-step framing with concrete reproducible context; comments in 50–80-word ranges with implementation detail
- **Recruiter / talent** evaluating culture and trajectory signals; rewards consistent thought leadership over time; comments in 30–50-word ranges on cultural fit
- **Industry peer** wanting a take they can argue with or build on; rewards a contrarian-but-defensible claim; comments in 60–80-word ranges with stance-taking

The reader is recognizably professional. They will not engage with broetry / hero-story / janitor-wisdom posts (see §3 CUT-1, CUT-2, CUT-3). They will leave a 30–80-word comment if the post contains a debatable claim, a genuine question requiring their experience, a numbered list with empty-slot affordance, or an honest-disagreement signal (the four mechanism families in LI-4). They will not engage with AI-slop tells when the gestalt stack triggers (≥2 of: em-dash density >1.0/100 words, template-phrase opener, symmetrical-bullet rhythm, P.S.↓ closer, affective flatness).

**Secondary reader — the algorithm.** Per Van Der Blom 2025/26 *Algorithm InSights* and the 360Brew rewrite: 0–3s dwell gets 1.2% engagement and capped distribution; 61+s dwell gets 15.6% engagement and full second/third-degree fanout. Comments are weighted ~15× a like but only count when they exceed ~10 words (ideal band 30–80). 90-min golden-hour velocity determines ~70% of total reach. Engagement-bait CTAs are now actively suppressed (~60% distribution penalty once classifier triggers). **Topic Authority cross-references claimed expertise against published corpus; topic-consistent authors see up to 78% higher distribution on in-lane content** — this is the single largest 2026 distribution lever and the load-bearing reason the v2 lane scope extends to Components C (content strategy + pillars) and G (12-month Topic Authority compounding plan). The algorithm is reader, not target — the judge tests reader-effects, not algorithm-feature presence.

**Substitute readers the same post should also serve (US-primary defaults).** A B2B SaaS founder at any stage ($500K to $50M+ ARR); a researcher or applied-AI engineer at an AI lab or scientific organization; an agency principal at a small-to-mid services firm (brand, growth, content, ops); a partner at a small-to-mid B2B service firm (law, accounting, consulting, financial advisory); a finance operator (founder, CFO, fund GP/LP, growth-stage finance lead); an e-commerce operator (DTC founder, marketplace operator, retail owner-op); a mid-career B2B IC at a SaaS / AI / fintech / agency company. US is the primary geo default; international fixtures (current first-cohort includes Poland-based clients) are supported but the algorithm's behavior, comment-substance norms, and Topic Authority pillar conventions in this spec are anchored on US B2B reading windows (7:30–9:00 AM and 12:00–13:00 ET).

The Welsh / Acosta / Alić / Denning / Meer / Murray / Bloom creator-archetype reference set in this spec exists because those operators have published explicit playbooks the literature builds on. They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy founder / early-co clients across the six verticals above (gofreddy is a generic AI-native agency, not a creator-economy shop). First-cohort overfitting is an explicit risk to monitor (see §8).

NOT the reader: cringe-tagged engagement-farmers; spam accounts; the author's first-degree network alone (golden-hour seed, not the goal); engagement-pod participants (now algorithm-detected and downranked — see §3 CUT-14); AI-generated comment bots (now filtered by LinkedIn mid-2025+).

---

## 1.5 Artifact shape — multi-component LinkedIn program (RESTRUCTURED 2026-05-19)

The v2 lane produces a **multi-component LinkedIn program**, not a single text post. The judge scope and the lane scope diverge:

- **Judge scope: Component A only** — the LinkedIn text post (600–2,000 chars, single-post or short-thread). LI-1..LI-5 score this and only this.
- **Lane scope: Components A–H** — the broader deliverable that wraps the text post. Components B–H are validated deterministically by `structural_gate` (see §8 for the gate's structural checks).

This is School B per JR confirmation. Component A stays atomic at the judge layer (shape-drift Goodhart defense, v1 reasoning preserved). The program around it broadens because a single text post is the smallest atomic unit of value on LinkedIn — comparable to one tweet on the X surface — and a real 2026 program for a small-to-medium tech-savvy client spans roughly 25 activities across five layers per the Step 0 research. Components B–H are the load-bearing other 24.

### Component A — LinkedIn text post (JUDGE SCOPE, locked from v1)

**The judge scopes ONE post format: a LinkedIn text post, 600–2,000 characters, single-post or short-thread (2–3 connected posts max).** Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that carousel-shaped outputs score well on LI-2 (insight delivery) because swipe-completion is easier to manufacture than scroll-completion, while video-shaped outputs score well on LI-3 (voice) because affect is harder to detect in spoken delivery, producing Frankenstein artifact mixes that don't serve any coherent reader. The lock prevents this.

Form factor (unchanged from v1):
- 600–2,000 characters total (text-post sweet spot per Socialinsider 2026; below 600 reads as throwaway, above 2,000 hits fatigue ceiling)
- Trailer at ~210 chars / first 3 lines, above the "...more" cut
- Single-post or short-thread (2–3 connected posts max), text-native
- Variable paragraph cadence (not symmetrical broetry, not blog-essay continuous prose)

Out of scope shapes at the judge layer (handled by sibling lanes per §8 triggered expansion):
- Document carousel — 6.60% engagement / 39% more reach per Socialinsider 2026 (handled by future `linkedin_carousel` lane when client demand crosses 3+; carousels are highest-priority sibling-fork target per research §6)
- Native video — different watch-completion mechanics (handled by future `linkedin_live` lane when client demand crosses)
- LinkedIn newsletter — separated distribution surface, subscriber audience, Depth Score computed independently (handled by future `linkedin_newsletter` lane when client demand crosses)
- LinkedIn article — long-form surface, different reader expectation (handled inside `linkedin_newsletter` or as separate lane)
- LinkedIn poll — different comment dynamics (deferred; lower-priority sibling-fork target)

The Component A lock is what the judge tests. The lane delivers Components B–H around it.

### Component B — Profile audit + replacement copy (STRUCTURAL_GATE)

A complete profile rewrite covering the seven Layer 1 elements from the Step 0 research:
- Headline (≤220 chars, 2026 pattern: target audience + specific outcome + mechanism/proof)
- About paragraph (≤2,600 chars, first 250 above the cut, reader-problem-led, named work, concrete next step)
- Featured section (3 pinned items max: top recent content + primary off-platform asset + credibility anchor)
- Banner image spec (visual + headline-reinforcing copy + mobile-above-fold CTA)
- Custom URL recommendation (`/in/firstname-lastname` default)
- Top 5 skills (chosen to reinforce headline positioning, not enumerate)
- Recommendations strategy (5–10 from named ICP peers within 18 months; older decay)

Size envelope: ~800 words. Output is paste-ready copy plus operator action list. The `structural_gate` validates: each of the seven elements present, headline ≤220 chars, About ≤2,600 chars with cut-position trailer, Featured section names exactly 3 items, banner spec includes copy + CTA, custom URL specified, exactly 5 skills enumerated, recommendation-acquisition plan present with named ICP targets.

### Component C — Content strategy + pillars + cadence + voice substrate (STRUCTURAL_GATE)

The 12-month operating doc. Sub-sections:
- Topic pillars: 1–2 primary + 1–2 secondary, each with a named rationale (Topic Authority compounding requires 90+ days in-lane to register on 360Brew; the pillar choice is the highest-leverage decision in the program)
- Cadence by format: weekly counts for text / carousel / video / newsletter / poll / Live / collab
- Voice guidelines: tone register + phrase library + topics to avoid + level-of-self-disclosure
- Format-fit matrix: which topics fire as text vs carousel vs newsletter vs video
- 90-day content backlog: ~50 candidate post ideas tied to pillars

Size envelope: ~1,500 words. The voice substrate sub-doc populates `programs/references/voice.md` — load-bearing for LI-3 score-0's voice-substrate provenance check on first-person lived-work claims (the v1 surgical-restoration fold from CI's HARD FLOOR). The `structural_gate` validates: at least 2 primary pillars + 1 secondary pillar named with rationale; format-cadence weekly counts present; voice substrate populated at `programs/references/voice.md` and non-empty; ≥40 candidate post ideas in the backlog.

### Component D — Comment strategy + 10 target accounts (STRUCTURAL_GATE)

The dominant audience-building lever for accounts under 10K followers per the Step 0 research (Activity 3.2). Sub-sections:
- 10 named target accounts: in-lane creators with 5K–50K followers, each with rationale (why they're a target + when they typically post + what kind of comment-mechanism-family to leave)
- Daily 15-minute commenting checklist
- Anti-pod-pattern instructions (deliberate avoidance per §3 CUT-14)
- Golden-hour timing playbook (first 90 minutes after their post; the algorithm rewards reciprocity)
- Voice-consistency across comments: the substantive 30–80-word band carries the same voice-substrate provenance constraint as the post itself

Size envelope: ~800 words. The `structural_gate` validates: exactly 10 target accounts named with LinkedIn URL + rationale; each rationale names a mechanism family (debatable claim / genuine question / enumerated frame / honest disagreement); daily-block scheduling present; anti-pod-pattern statement present.

### Component E — DM templates + connection-request strategy (STRUCTURAL_GATE)

The funnel-mechanics layer. Sub-sections:
- Cold-outbound DM template (3 variants matched to ICP's top 3 personas)
- Warm-outbound DM template (4 variants by engagement signal: commenter / liker / profile-viewer / re-poster)
- Inbound-response template (qualification arc: 2-message → 3-message → 4-message)
- Connection-request message templates (3 variants)
- Connection-acceptance follow-up arc
- ICP definition (titles + company-size + industry + geography)
- Weekly connection-request target (50–100/week from people who engaged with author's content within 7 days; cold outbound to ICP-fit strangers converts 1–3%, warm outbound at 15–30% per Lavender + 2025 Hubspot State of Outbound)

Size envelope: ~600 words DMs + ~600 words connection strategy = ~1,200 words. The `structural_gate` validates: cold-outbound DM has exactly 3 variants tied to named personas; warm-outbound DM has exactly 4 variants tied to engagement signals; inbound-response template has 2/3/4-message arc; ICP definition includes titles + company-size + industry + geography; weekly connection target is a number in [50, 100].

### Component F — 30/60/90 execution roadmap (STRUCTURAL_GATE)

Standard agency deliverable. Sub-sections:
- 30 days: profile foundation + content production startup + first 5–8 posts shipped
- 60 days: full content cadence live + comment strategy active + DM strategy live + 100 net new connections
- 90 days: first Topic Authority signal visible + newsletter launched + first measurable pipeline contribution

Size envelope: ~1,000 words. Includes risk-flags for the patterns that historically derail clients (volume burnout in week 4, no-results-yet anxiety in month 2, scope-expansion temptation in month 3). The `structural_gate` validates: 30/60/90 milestones each named explicitly; per-period operator actions enumerated; risk-flag section present.

### Component G — Topic Authority compounding plan (12-month arc) (STRUCTURAL_GATE)

The longer-arc strategy doc. Topic Authority compounds over 9–12 months per the Step 0 research; meaningful lift around month 4–6 (after ~50–80 in-lane posts), obvious compounding around month 9–12. Sub-sections:
- Quarterly milestones (Q1 / Q2 / Q3 / Q4)
- Expected compounding inflection points (month 4–6 first signal, month 9–12 visible compounding)
- Pillar-review checkpoints (quarterly)
- Semi-annual content-mix rebalance recommendations

Size envelope: ~800 words. The `structural_gate` validates: 4 quarterly milestones present; ≥2 inflection-point markers named; pillar-review cadence present; semi-annual rebalance language present.

### Component H — Cross-platform syndication rules (STRUCTURAL_GATE)

The agency-level documentation of how content moves across surfaces. Sub-sections:
- X → LI rule (de-compress contrarian punch into thoughtful authority; the X-shaped hook that produces DH3–DH5 substantive replies on X collapses to DH0–DH2 cheerleading/hostility on LinkedIn — see LI-4 score-0 anchor)
- Blog → LI rule (excerpt the strongest 800-word section, not the full piece; LI articles share the newsletter's distribution physics but lack subscriber stickiness)
- Podcast → LI rule (audiogram + transcript-derived text post + carousel slides + newsletter mention)

Size envelope: ~400 words. The `structural_gate` validates: X→LI rule named with register-translation move; blog→LI rule names the excerpt-band; podcast→LI rule names the 4-surface output set.

### Total program envelope

Components A through H together produce a single multi-part program deliverable of ~10,000–11,000 words, comparable to the marketing-audit lane's envelope. The judge scopes Component A; `structural_gate` validates B through H deterministically. Per the design guide §1.2 (Hard Rules → structural_gate, Principles → judge), the components that have shape-checkable structure (profile field completeness, voice substrate file existence, strategy section presence, comment-target count validity, DM-template variant count, roadmap milestone presence, Topic Authority pillar specification, cross-platform rule presence) belong in `structural_gate`. The component that requires semantic reader-effect prediction (Component A — does the post earn dwell + substantive comment + profile-click) belongs in the judge.

**Empirical validation scope.** The Component A text-post form factor is research-grounded against current first-cohort fixtures (small-to-mid B2B SaaS, AI labs, agency principals, legal services, healthcare practices). When fixtures from new verticals or new shapes appear (DTC e-commerce founder takes, fintech-compliance posts, hospitality owner-operator content), re-validate the form factor — different verticals may favor different mid-post structures (DTC may favor numbered-list-with-photo claims; fintech may favor compliance-context-then-claim). Components B–H are vertically-flexible by design (the format-fit matrix in Component C adapts per vertical), but the `structural_gate` checks are vertical-independent.

### Sibling-lane fork triggers (deferred to §8)

The Step 0 research recommends sibling-lane decomposition: `linkedin_carousel`, `linkedin_newsletter`, `linkedin_live`, `linkedin_profile`, `linkedin_comment_strategy`. Per JR confirmation, those are deferred to §8 triggered expansion. The v2 lane stays single-lane producing the full A–H program; sibling lanes fork only when client demand crosses three (see §8 for trigger specification).

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18, extended 2026-05-19)

### 2a. Component A success (the judge scopes this)

After ~3 seconds the relevant professional reader clicks "...more" past the trailer cut. After 30+ seconds of dwell they take ONE of three concrete actions: (a) leave a substantive 30–80-word comment, (b) save the post for later reference, or (c) DM the author (the highest-credibility signal — they thought it was worth a private follow-up). The post earns ≥3 substantive comments in the 90-min golden hour, triggering fanout to second- and third-degree readers via the Depth Score multiplier. Profile-click follow-through is the secondary credibility signal — the reader clicks the byline to read more from the same author.

The reader treats the post as credible thought leadership coherent with the author's visible professional context (Edelman/LinkedIn 2025: 73% of B2B decision-makers cite consistent thought leadership as a trust signal — the operative word is *consistent*). The post advances the reader's thinking — gives them pattern-recognition, framing, or a specific worked example they did not arrive with. The post passes the Tim Denning litmus: if the author's name were stripped, their closest professional contact could still recognize the post as theirs.

**Sleep test:** if the reader saw the post in the morning and slept on it overnight, they could still articulate the central insight to a colleague the next day — the substance survives 24h, not just the surface.

### 2b. Program-level success (Components B–H, validated by `structural_gate`)

For the broader program around Component A, the client (the author or their delegated agency operator) DOES the following concrete actions, not just receives a deliverable:

- **Component B success:** the client commits to producing the rewritten profile within 7 days of receiving the deliverable. Headline, About, Featured, banner, URL, skills are shipped; ≥3 named-ICP-peer recommendations requested.
- **Component C success:** the client commits to a documented 1–2 primary + 1–2 secondary topic-pillar strategy with a 90-day commit minimum. Voice substrate populated at `programs/references/voice.md`. Content backlog of ≥40 candidate post ideas ready.
- **Component D success:** the client executes the daily 15-minute commenting block for at least 60 of the first 90 days. 10 named target accounts engaged with ≥3 substantive 30–80-word comments per account per week (within their golden hour where possible).
- **Component E success:** the client sends the first cold-outbound batch (warm-outbound preferred per 15–30% conversion vs 1–3% cold) within 14 days; warm-outbound DMs go to recent commenters / likers / profile-viewers; the inbound qualification arc replaces ad-hoc DM responses.
- **Component F success:** the client hits the 30/60/90 milestones on schedule. Day-30 = profile complete + ≥5 posts shipped; Day-60 = full cadence + ≥4 net new ICP-fit connections per week; Day-90 = newsletter launched + first Topic Authority signal visible in 360Brew distribution metrics.
- **Component G success:** the client commits to the 12-month arc and runs quarterly pillar reviews. Most small-to-medium clients churn out of LinkedIn programs around month 3–4 because Topic Authority compounding inflection points (month 4–6 first signal, month 9–12 visible compounding) sit past their attention window — Component G's role is to bridge that window with documented checkpoints.
- **Component H success:** when the client publishes on X, blog, or podcast, the LinkedIn surface inherits the right register-translated derivative. The agency's content-share workflow is the implementation surface.

**Program-level sleep test:** if the client slept on the program deliverable overnight, they could still articulate (a) which topic pillars they're committing to, (b) which 10 target accounts they're engaging weekly, (c) what their 30-day milestone is, (d) what their 12-month bet is. Substance survives 24h at the program level too.

### World-class real-world exemplars

Used as quality anchors, NOT as templates to copy:

**Ceiling (cross-archetype):**
- **Trailer-meat-CTA discipline** (Welsh's published 2026 LinkedIn guide) — every line earns the next; trailer breaks scroll on line 1, the cut earns the click via line 2/3 specificity, the meat delivers ONE insight, the close is the strongest line not the weakest.
- **Specificity test** (Alić's 27 Proven LinkedIn Writing Tips) — if you swap one named entity, number, or moment for a generic placeholder and the post reads identically, it was too generic; the named anchor is load-bearing.
- **Honest-disagreement framing** (constructive-disagreement research, WikiDisputes / *I Beg to Differ*) — opener at DH4–DH5 (counter-argument with stated uncertainty), not DH0–DH2 (cheerleading, ad-hominem, tone) — the opener's stance sets the ceiling for the reply ladder.

**Achievable floor (practitioner-grade):**
- **Hook-rehook structure** (Acosta) — line 1 is the 8–10 word hook, line 2 is the bait-and-switch rehook that earns the cut, not a continuation.
- **Nine-sentence narrative** (Denning) — short paragraphs, three-sentences-per-paragraph cap, conversational cadence, one insight per post.
- **Four-story-types frame** (Meer) — Personal pivot / Business insight / Client win / Leadership belief — every strong post cleanly serves one of four shapes; ungrounded mixes read as opinion soup.

**Program-level exemplars (newly relevant in v2):**
- **Welsh "Saturday Solopreneur" funnel** — content → newsletter sub → DM → call → solo-product close. Documented mechanics; the agency's Component E + Component G playbook should map to this exemplar's logic without copying it.
- **Sahil Bloom "Curiosity Chronicle" newsletter funnel** — content → newsletter → trust-build → multiple monetization paths (book, course, paid newsletter). Documented mechanics; useful exemplar for finance-vertical and longer-arc trust-building.
- **Lara Acosta + Daniel Murray comment-built growth trajectories** — both built audiences substantially via deliberate high-leverage commenting on in-lane creators, not via posting volume alone. Useful exemplar for Component D.

What ties these together: a specific named entity or moment that anchors the claim; trailer-payoff coherence so the cut click is earned not tricked; a single insight delivered with author-specific evidence; an organic comment-seed that doesn't bolt on a CTA; author-context register that matches the seat the author actually occupies; and at the program level, a deliberate 12-month Topic Authority compounding bet with documented checkpoints.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18, extended 2026-05-19)

### 3a. Mediocre — 20 cuts from the 2018–2023 playbook (modern-lever bias)

The 2018–2023 LinkedIn playbook contains a substantial layer of tactics that no longer work in 2026 — either because the algorithm has actively suppressed them, because the audience has pattern-matched them as low-status, or because the AI-generation toolchain has flooded them past their useful lifespan. The judge discriminates against these at Component A's score-0 anchors; `structural_gate` deterministically blocks the regex-detectable subset; Component B–H validation prevents them from creeping back via the broader program. Per Step 0 research §2:

**CUT-1: Broetry as default format.** Single-sentence-per-line dramatic-pause posts engineered to game the read-more click. Cutting the structural overuse where every line is one sentence regardless of content (LI-3 broetry-line density ≥40% gestalt-stack signal). Welsh's single-line paragraphs stay legitimate — substance must compound across lines.

**CUT-2: The hero's journey post.** "$7 in my bank account → 7-figure business" closing on a course pitch. Audience tolerance has cratered; the 2026 replacement is specific tactical insight from the same journey, told as one moment not a complete arc.

**CUT-3: The janitor-wisdom / airport-story format.** "A janitor at LAX taught me everything I know about leadership." Almost always fabricated or composite. The 2026 audience flags this within 3 seconds.

**CUT-4: The humblebrag.** "I'm so humbled to announce…" — Sezer/Norton/Gino 2018: humblebraggers are perceived as less likeable, less competent, less influential than direct braggarts. The format inverts its own goal.

**CUT-5: Generic motivational quotes.** "Success is going from failure to failure without losing enthusiasm." — fails the Denning name-stripped test and scores 0 on LI-2.

**CUT-6: Generic "I X for Y years. Here's what I learned" listicle bloat.** The opener shape itself is legitimate (Denning uses close variants); the *generic-listicle-under-the-opener* version goes.

**CUT-7: AI-slop with em-dash density >1.0 per 100 words.** Plagiarism Today June 2025 dataset: GPT-4o median 0.6 per 100 words vs human median 0.05; the AI-baseline-overuse range (>1.0/100 words) is audience-detectable. Routes to `structural_gate` as a density check; ghostwriter edits down to human-stylist range (0.2–0.4 per 100 words).

**CUT-8: "Stop X. Start Y." parallel-list compression.** Legitimate as a single rhetorical move; kills the post when stretched into structural backbone.

**CUT-9: Engagement-bait CTAs.** "Comment YES if you agree," "Type 1 if you agree," "Tag a friend who needs this," "Like for Part 2," "Repost if you've felt this." LinkedIn's 2026 NLP classifier triggers ~60% distribution suppression once any of these fires regardless of account history. Routes to `structural_gate` as deterministic regex.

**CUT-10: P.S.↓ closers.** ~12% of GPT-4o LinkedIn outputs vs <1% of human posts (Plagiarism Today). Routes to `structural_gate` as deterministic regex.

**CUT-11: "Here are 7 lessons" listicle-bloat openers.** Numbers in {5, 7, 10, 12} dominate; the AI generation toolchain has converged on these so heavily the opener alone now reads as templated.

**CUT-12: Symmetrical bullet rhythm.** Every bullet identical length, identical syntactic shape (CV <0.15 = AI-shaped). Routes to `structural_gate` as density check.

**CUT-13: Template-phrase openers.** "Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y." Generation-model bridge tokens; deterministic AI-slop tells. Routes to `structural_gate`.

**CUT-14: Engagement pod participation.** LinkedIn detects pod patterns and downranks; AI-generated pod comments filtered as of mid-2025. Component D explicitly excludes pod-style coordination (anti-pod-pattern statement validated by `structural_gate`).

**CUT-15: Third-party-app video uploads.** Reach cut 50–70% per Van Der Blom 2025/26. Component H syndication rules explicitly cover native-upload-only.

**CUT-16: Generic "Open to work" badges as long-term profile state.** Useful when actually job-hunting; low-status when permanent. Component B headline rewrite replaces with current-value-creation framing.

**CUT-17: Profile bios in third-person.** "John is a passionate marketing leader…" reads as ghostwritten by a 2015 employer comms team. Component B About rewrite enforces first-person, problem-statement-led, conversion-driven copy.

**CUT-18: Posting daily without a topic pillar strategy.** Pre-2026 volume was a primary growth lever; post-360Brew Topic Authority, volume *without* topic-consistency penalizes distribution. Component C explicit pillar strategy is the structural defense.

**CUT-19: Posting from the company page as primary surface for founder content.** Personal profiles earn 5–10× the organic reach of company pages. Component C cadence + Component H syndication explicitly position founder personal profile as primary.

**CUT-20: "Repost if you agree" / naked reposts as engagement strategy.** Now near-zero algorithmic value. Component C cadence excludes naked reposts; replacement is collab posts (Activity 2.8) and earned reshares-with-commentary.

### 3b. AI-slop signal stack (gestalt, not single-tell)

Em-dash density >1.0 per 100 words (the empirically AI-shaped band per Plagiarism Today June 2025 dataset; legitimate stylists run 0.2–0.4); template-phrase openers ("Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y"); P.S.↓ closers (~12% of GPT-4o LinkedIn outputs vs <1% of human posts); symmetrical bullet rhythm (coefficient-of-variation <0.15 in bullet length); broetry-line density ≥40% of total lines; "Stop X. Start Y." parallel-list compression; "Here are 7 lessons" listicle bloat; affective flatness — no specific surprise, anger, delight, or stake. None of these alone is slop; the gestalt is.

The four LI-specific AI-slop families:

- **Broetry structural** — every line is one sentence; broetry-line density ≥40%; symmetrical bullet rhythm.
- **Surface signature** — em-dash density >1.0/100w; template-phrase opener stack; P.S.↓ closer; "Stop X. Start Y." parallel compression.
- **Affective flatness** — no specific surprise, anger, delight, regret, or stake; no internal self-correction; no named anchor in the body.
- **Algorithmic-affinity** — engagement-bait CTAs; "Here are N lessons" listicle bloat opener; bait-and-switch trailer-to-body mismatch where the trailer overpromises and the body underdelivers.

### 3c. Blog draft shoved into LinkedIn

1,500-word essay broken into LinkedIn paragraphs with no hook, no rehook, no payoff at the cut. Long-form belongs on the LinkedIn newsletter surface (Component G-adjacent), not the post surface — the algorithm reads the trailer to decide reach, so an essay opening loses dwell before the body even gets read.

### 3d. Motivational platitude / generic career advice

Posts that could have been written by any author in any industry — fails the Denning name-stripped test. Surface-engagement may be non-zero (cousins-and-coworkers like-clicks) but no fanout, no substantive comment, no profile-click compounding.

### 3e. Author-context register mismatch (the AI-loop-most-likely failure)

Series-A founder narrating Series-D scaling pain ("when you're scaling past 500 reps…"); VP-level confidence on IC-level topics (executive writing tactical subject-line detail with flattened seniority signal); junior IC writing CEO-stance market-positioning content without grounding. Pornpitakpan 2004 meta-analysis of 47 source-credibility studies: high-credibility sources are more persuasive than low-credibility, but the credibility–persuasion link **collapses when message content sits outside the source's expertise band**. The reader has been pattern-matching this for forty years; the AI optimizing for hook density and comment-seed strength will routinely violate it. This is the failure mode the Goodhart-collapse loop produces most readily.

### 3f. "Looks like slop but isn't" defense — false-positive over-suppression

Each broetry-family pattern has a legitimate-operator-voice analog the judge must NOT penalize. The slop signal is the gestalt stack, not any single tell.

- **Broetry one-sentence-per-line, used by real operators.** Justin Welsh's solopreneur posts use single-line paragraphs deliberately because his mobile-reading audience expects it and he's written 1,500+ posts in this register. The substance compounds across lines (each line earns the next); AI broetry restates (each line is a synonym for the previous).
- **Em-dash use from real operators.** English-prose stylists like Lara Acosta and Jasmin Alić use em-dashes at 0.2–0.4 per 100 words — well above human baseline, well below AI baseline. The em-dash on its own is a false-positive trap; threshold is >1.0/100 words.
- **"I X for Y years" used by real founders.** Tim Denning has built his audience on close variants of this opener with substantive author-specific content underneath. The shape alone is not slop; the test is whether LI-2 fires.
- **"Stop X. Start Y." used by real operators.** Direct, parallel, contrarian-positioning is a legitimate rhetorical mode. The test is whether X is a strawman or a real practice the reader is doing.
- **"Here are 7 lessons" used by real authors.** Numbered-list posts hit ~6.6% engagement per Socialinsider 2026. The test is whether the items are author-specific (each one a lived story) or interchangeable (each one a generic claim).
- **Algorithm-aware authors generally.** Welsh, Acosta, Alić, Denning, Meer openly publish hook + rehook + comment-seed + format-fit playbooks. The judge cannot penalize "algorithm-aware structure" as slop; it must penalize "algorithm-aware structure with no substance underneath."

### 3g. Goodhart-collapse — Phase 4 pathology + LI-specific AI-failure surfaces

**Phase 4 pathology (the historical Goodhart trap).** 50-generation evolution against a feature-checking judge produced exactly the pathology rolled back at `c76f051` (commit `698e658`). The workflow learns to slot-fill named surface markers — for LinkedIn this collapses to:

- Every post opens with a specific number or named-entity hook regardless of substance.
- Every post has a rehook in line 2 that bait-and-switches mechanically.
- Every post inserts a question at line 4 to "earn comments" — the question is grammatically a question but semantically a CTA.
- Every post replaces em-dashes with semicolons or single dashes (different surface tell, same gradeless prose).
- Every post namechecks a customer or anecdote whether load-bearing or pasted in.
- Every post has exactly 7–9 sentences (Denning's max) regardless of whether 4 or 12 would serve the insight.
- Every post closes with a numbered list with three items and one "open slot" for reader additions.

Result: a corpus that is structurally compliant, recognizable as templated within 3 seconds by a human reader, that the 2026 distinctiveness filter detects and downranks, and that the engagement-bait classifier suppresses regardless of account history. Posts score well on judge AND get muted on platform. The criteria below are designed to resist re-creating this AND to surface the new LI-specific AI-failure surfaces the rollback did not address.

**Per-component Goodhart modes (new in v2; route to structural_gate, NOT to a 6th criterion):**

- **Component B Goodhart:** workflow learns to generate plausible-sounding profile copy that hits the headline 220-char ceiling and About 2,600-char ceiling without aligning to the actual ICP. Defense: `structural_gate` checks for ICP-token match between Component B headline and Component E ICP definition; checks for Featured-section item recency against `programs/references/voice.md` author surface.
- **Component C Goodhart:** workflow learns to generate plausible topic-pillar names that don't compound on the author's actual expertise. Defense: `structural_gate` checks pillar-token overlap with author's voice substrate (Jaccard ≥0.2); checks that ≥40 candidate post ideas are populated and not duplicates of each other.
- **Component D Goodhart:** workflow learns to generate a list of 10 plausible-sounding LinkedIn URLs without checking they're in-lane creators. Defense: `structural_gate` validates URL resolves; rationale-token match against Component C pillar tokens.
- **Component E Goodhart:** workflow generates DM templates that look complete but lack persona-specific anchors. Defense: `structural_gate` checks named-persona match between DM template body and ICP definition.
- **Component F Goodhart:** workflow generates 30/60/90 milestones that are calendar-shaped but not capacity-sized to the client. Defense: `structural_gate` checks milestone count + risk-flag presence; semantic capacity-sizing flagged for re-validation if first-cohort fixtures show churn around month 3.
- **Component G Goodhart:** workflow generates a 12-month plan that paste-mirrors industry-standard pillar-review language without anchoring on the specific pillars from Component C. Defense: `structural_gate` checks Q1–Q4 milestones each reference a Component C pillar by name.
- **Component H Goodhart:** workflow generates syndication rules that name the surfaces (X, blog, podcast) without naming the register-translation move. Defense: `structural_gate` checks each rule contains a verb describing the translation move (de-compress, excerpt, audiogram, etc.).

**LI-specific AI-failure surfaces at the judge layer (route to structural_gate, NOT to a 6th criterion — unchanged from v1):**

- **Engagement-bait classifier suppression.** LinkedIn's 2026 NLP classifier flags posts with engagement-bait phrases (CUT-9 above); ~60% distribution suppression. ~10 regex patterns cover 90%+ of cases (per `x_engine/pipeline/slop_gate.py::LINKEDIN_BANNED_PHRASES`).
- **AI-slop deterministic floor.** P.S.↓ closer regex; "Stop X. Start Y." parallel; "I X for Y years" credential-opener; "Here are N lessons" listicle-bloat opener; template-phrase opener stack; whitespace inflation; em-dash density >1.0/100 words; broetry-line density ≥40%; bullet-rhythm CV <0.15.
- **Author-context determinable slice.** Role-Topic Token Overlap Gate; Employer-Mention Validity Check; Claim-vs-Recent-Activity Check. Together hoist ~40% of LI-5's surface and 100% of the engagement-bait/AI-slop deterministic surface out of the judge.

The judge sees the post only after `structural_gate` passes; what remains in the judge is the gestalt, the residual, the reader-effect prediction — which is irreducibly judge-side. **No 6th criterion is required**, because every LI-specific AI-failure surface either resolves to a deterministic check (route to structural_gate) or folds naturally into LI-3's voice-residual or LI-5's register-coherence outcome question.

Deterministic AI-detector classifier output (GPTZero / Originality.ai / Copyleaks) is NOT a hard gate — FPR 18–35% against authentic operator posts per Authoredup July 2025 makes detectors unfit as hard blocks. Surface classifier output as a soft signal in the judge rationale only if at all; do not block on it.

---

## 4. Criteria — outcome questions (5, UNCHANGED from v1)

The five criteria below score Component A (the LinkedIn text post) and ONLY Component A. Components B–H are validated by `structural_gate` per §1.5 and §8. Per JR confirmation, LI-1..LI-5 prose is locked from v1; only the score-1 anchors gain modern-lever-bias *additions* where the 15 modern levers from Step 0 research §3 extend rather than replace the existing v1 anchor language.

### LI-1 — Trailer earns the "...more" click

**Outcome question (binary):**
After reading only the trailer (everything above the "...more" cut, typically the first 3 lines / ~210 characters), would a relevant professional reader in the target context click "...more" — and once they do, does the body below the cut deliver on the trailer's implied promise rather than bait-and-switching them past the click?

**Score 1 (yes)** — Lines 1–3 contain a specific entity, number, claim, or counterintuitive framing tied to the post's professional context. The reader after line 3 has a clear sense of what payoff sits below the cut, and that payoff is coherent with the opener (no bait-and-switch where the body reads as unrelated to the trailer's promise).

Example (do not optimize toward this): "Hired a Gen-Z candidate without interviewing him. / Six months later, he's our highest-leverage IC. / Here's the one bet that paid off, and the two we're rolling back…" — trailer creates tension (no-interview hire, leverage outcome), line 2 doubles down with a specific result, line 3 promises a specific lessons-learned breakdown the body has to deliver.

**Score 0 (no)** — Opener is a generic platitude, a vague claim ("Leadership is hard"), a motivational quote out of context, or engagement-bait ("Agree?"). OR opener earns the click but the body below the cut is unrelated to the promise (trailer promises a specific tactical breakdown, body delivers generic platitude).

**Score 0.5 (unknown)** — Post is single-paragraph with no clear cut point visible from the artifact (e.g., the artifact does not encode the cut position and the judge cannot reconstruct where line 3 ends). OR the relevant professional reader cannot be inferred from the artifact + source_data. Emit 0.5 + "unknown" + one sentence on what's missing.

**Required CoT:**
- Step 1: Identify the trailer (everything above the "...more" cut, typically first 3 lines / ~210 chars). Test whether it contains a specific entity, number, claim, or counterintuitive framing.
- Step 2: Test whether the body below the cut delivers the trailer's promise — does the substance match the implied payoff, or does it bait-and-switch?
- Step 3: Emit verdict + one-sentence justification naming the specific trailer signal AND the specific payoff coherence (or its failure).

Do not score: trailer length exactness, presence of "..." or "[continue reading]" markers, line-break count in the trailer, broetry vs paragraph formatting (those live in structural_gate or do not matter).

### LI-2 — Delivers one non-obvious insight a real reader could use

**Outcome question (binary):**
After reading the full post, would a relevant professional reader leave with pattern-recognition, a framing, or a worked example they did not arrive with — and is the insight author-specific enough that swapping the author's name for a different operator would lose what makes the post valuable?

**Score 1 (yes)** — Post contains at least one specific claim, number, framing, or worked example that gives the reader pattern-recognition they did not arrive with. The insight is non-generic — the Alić specificity test holds: swap one named entity, number, or moment for a generic placeholder, and the post would read differently. The insight could plausibly only have come from this author's specific position, evidence, or experience.

Example (do not optimize toward this): "We A/B tested onboarding email length. 80-word emails outperformed 280-word by 40% on activation — *not* because shorter is better, but because the 280-word version asked for two decisions and the 80-word asked for one. The constraint is decisions, not words. We're rolling the rest of our email program against this." — specific test, specific numbers, specific mechanism (decisions ≠ words), specific next-action implication.

**Score 0 (no)** — Post recycles generic advice ("write shorter emails"), restates conventional wisdom without specific evidence, OR could have been written by any author in the field (fails the Denning name-stripped test). OR the insight is author-specific in surface but generic in substance — a customer name dropped but the underlying claim is a truism.

**Score 0.5 (unknown)** — Specific claim is present but the target reader's prior knowledge level cannot be inferred from the artifact + source_data (e.g., insight may be novel to a junior IC, obvious to a senior). Emit 0.5 + "unknown" + one sentence on what context would resolve it.

**Required CoT:**
- Step 1: Identify the central insight in the post (the one thing the reader is supposed to leave with).
- Step 2: Apply the specificity test — would swapping the author's name or the named entities/numbers produce a different post? Is the insight non-obvious for the identified target reader?
- Step 3: Emit verdict + one-sentence justification naming the specific evidence anchor (or its absence).

Do not score: insight controversy level, presence of named-customer references on their own, length of the supporting story, presence of numbered list or other format features.

### LI-3 — Voice is recognizably the author's, not the AI's

**Outcome question (binary):**
If a colleague who knows the author read this post anonymously, would they recognize it as the author's writing — and would a stranger NOT mistake it for AI-generated content? The test is the gestalt voice stack, not any single tell.

**Score 1 (yes)** — Post has specific voice markers (sentence cadence, turn of phrase, a moment of genuine surprise / anger / delight / shame / stake, an anecdote tied to the author's actual professional context, an internal self-correction or acknowledged limit). The AI-tell gestalt does not trigger: no co-occurring stack of em-dash density >1.0/100 words AND template-phrase opener AND symmetrical-bullet rhythm AND P.S.↓ closer AND affective flatness. OR — if a single weak signal triggers — at least one compensating voice marker is clearly present (named entity in body, marked affect, internal self-correction, specific anecdote).

Example (do not optimize toward this): a post where the author admits they were wrong about a hiring call from two years ago, names the specific moment they realized it (a Tuesday Slack thread, a specific candidate's first-month review), and ends on an open question about whether they would make the same call now — the affective marker (regret/uncertainty), the named anchor (Tuesday Slack), and the internal contradiction (they were wrong) together signal authored voice that an AI default register would not produce.

**Score 0 (no)** — Gestalt stack triggers: ≥2 co-occurring AI-tells from the list (em-dash density >1.0/100w, template-phrase opener stack, symmetrical-bullet rhythm with CV <0.15, P.S.↓ closer, broetry-line density ≥40%, affective flatness) AND no compensating voice markers. OR the post reads as affectively flat throughout — no specific surprise, no specific anger or delight, no specific stake, no internal self-correction, no named anchor. Cannot be distinguished from AI-default-neutral register. OR the post reads as bait-y or Twitter-translated (cross-platform import of contrarian-punch register that works on X but lands as bait on LinkedIn — the LinkedIn voice lever is *thoughtful authority, not contrarian punch*; posts that translate X-shaped rhetorical compression into the LinkedIn surface score 0 on this criterion even when individual AI-tell signals do not trigger). OR the post makes a first-person specific lived-work claim (named customer, named colleague, named project, named dollar/percentage outcome owned by the author) where the named entity does NOT appear in the author's voice substrate at `programs/references/voice.md` — lived-work claims REQUIRE voice-substrate provenance; unanchored first-person specifics are confabulation regardless of surface fluency.

**Score 0.5 (unknown)** — Single weak signal present (one em-dash in an otherwise human-cadenced post; one template-phrase opener with otherwise specific body) AND the artifact does not contain enough material to test for compensating voice markers. Emit 0.5 + "unknown" + the specific signal AND what compensating marker would have to be present to commit to 1.

**Required CoT:**
- Step 1a: Scan for the gestalt AI-tell stack — count how many of (em-dash density / template-phrase opener / symmetrical bullets / P.S.↓ closer / broetry-line density / affective flatness) trigger. Note: deterministic single-tell density gates have already run in structural_gate; the judge is scoring the residual.
- Step 1b: For each triggered signal, identify whether a compensating voice marker is present (named entity in body, marked affect, internal self-correction, specific anecdote tied to author's professional context).
- Step 1c: Test for bait-y / Twitter-translated register — does the post read as a contrarian-punch hot-take imported from X, where the rhetorical compression that lands on X (sharp-line aphorism, hostility-shaped opener, ratio-bait framing) lands as bait on the LinkedIn surface? The lever for LinkedIn voice is *thoughtful authority*; cross-platform contrarian-punch imports score 0 here.
- Step 1d: Voice-substrate provenance check on first-person specific lived-work claims. For each named entity (customer, colleague, project, dollar/percentage outcome the author claims to have owned), test whether the entity appears in the loaded voice substrate at `programs/references/voice.md`. Any unanchored lived-work specific is confabulation → score 0 even if the rest of the post is voice-coherent.
- Step 2: Apply the three-signal substance test: (i) specificity in the body (not just the opener); (ii) at least one marked affective valence in the body (specific irritation, surprise, regret, delight, stake); (iii) internal-contradiction tolerance (self-correction or acknowledged limit).
- Step 3: Emit verdict + one-sentence justification naming the dominant tell, the dominant compensating marker, the bait-y/Twitter-translated diagnosis, OR the unanchored lived-work claim (whichever is load-bearing for the verdict).

Do not score: total post length, paragraph count, presence of any single punctuation mark in isolation, output of any AI-detector classifier (FPR 18–35% against real operators — surface only as soft signal if at all).

### LI-4 — Gives a real reader something substantive to comment on

**Outcome question (binary):**
Would the relevant professional reader leave a substantive 30–80 word comment because the post offers them an organic entry point — a debatable defensible claim, a genuine question requiring their experience, an enumerated frame with empty-slot affordance, or an honest-disagreement signal — rather than because a bolted-on CTA prompted them to react?

The negative version of this question is the reader-effect anchor: **the relevant professional reader leaves no substantive 30–80 word comment because the post invites no genuine entry point.**

**Score 1 (yes)** — The post organically offers at least one of four mechanism families: (a) a *debatable defensible claim* where the author has visible standing and the claim is grounded in specific evidence (reader can extend with their own case or push back with a counter-case); (b) a *genuine question requiring the reader's specific experience to answer* (not a rhetorical question dressed as a survey — the question cannot be answered without the reader's specific position); (c) a *numbered or enumerated frame with empty-slot affordance* (the list signals incompleteness, the reader's mental affordance is to contribute item N+1); (d) an *honest-disagreement signal* ("I think X — here's where I might be wrong; what am I missing?" — Graham's hierarchy DH4–DH5 counter-argument with stated uncertainty, not DH0–DH2 cheerleading/hostility/tone).

Example (do not optimize toward this): a post that stakes a specific position on a hiring trade-off the author lived ("We hired for raw IQ over domain experience and it cost us nine months — here's the specific moment I realized the trade-off and where I'd push back on my own argument"). Reader's reply ladder ceiling: substantive case-comparison from their own experience, not "agree!" cheerleading or "wrong, here's why" hostility. Note: *taking a contrarian position without defensible standing fails this criterion* — the standing is what enables Graham DH4–DH5 replies instead of DH0–DH2 reactions.

**Score 0 (no)** — Post is a closed monologue with no entry point for substantive contribution; OR a list of generic tips that closes the enumeration (no empty-slot affordance); OR a pure announcement; OR contrarian-for-its-own-sake (opener at DH0–DH2 rebuttal level, no defensible standing — reply ladder ceiling is cheerleading/hostility, not substantive engagement); OR list-padding (numbered list where slots are non-substantive filler); OR bolted-on (generic post with a "what do you think?" or "agree?" closer tacked on, where the body itself invites no comment); OR cross-platform contrarian hot-take whose register works on X but mis-fires on LinkedIn (a hook that would plausibly score 1 on this criterion's X-lane sibling scores 0 here because the LinkedIn audience reads the same contrarian-punch register as bait, not as substantive stance-taking — the reply ladder ceiling on LinkedIn collapses to DH0–DH2 reactions where the X audience would have gone DH3–DH5).

**Score 0.5 (unknown)** — Post invites comment via one of the four mechanism families but the target reader's domain knowledge required to comment substantively cannot be inferred from the artifact + source_data. Emit 0.5 + "unknown" + the specific reader-context that would have to be present.

**Required CoT:**
- Step 1: Predict the reply-ladder ceiling. Given the post's opening stance and the way the substance lands, what reply distribution would it invite — DH3–DH5 substantive engagement (case-comparison, methodological pushback, framing extension), or DH0–DH2 cheerleading/hostility/contradiction? The ceiling is set by the opener; the judge cannot recover from a low-ladder opener.
- Step 2: Identify which (if any) of the four mechanism families is present *organically* in the post — debatable defensible claim, genuine question requiring reader experience, enumerated frame with empty-slot affordance, honest-disagreement signal. Test for organic-vs-bolted-on: is the comment-seed coherent with the post's central argument, or attached at the close?
- Step 3: Emit verdict + one-sentence justification naming the specific mechanism family (or its absence) and the implied reply-ladder ceiling.

Do not score: presence of CTA on its own, presence of question marks, presence of polls, presence of explicit "what do you think?" closers (those route to structural_gate as deterministic bait-string detection; the judge tests reader-effect, not surface markers), bait-string detection itself.

### LI-5 — Author-context coherence: credible thought leadership

**Outcome question (binary):**
Would a relevant decision-maker reader treat this post as credible thought leadership from this specific author — i.e., does the post's confidence level, scope of claim, and frame of reference match the author's visible professional seat (role, stage, employer, expertise)? The dominant failure mode the judge must catch is **authority-voice register mismatch under selection pressure** (Resolution B), not the obvious topic-mismatch which structural_gate already catches (Resolution A) or the temporal-claim mismatch structural_gate also catches (Resolution C).

**Score 1 (yes)** — The post's authority-voice register matches the author's seat. A founder-stage author writes about founder-stage problems they have plausibly encountered. An IC writes from IC vantage with the texture of having lived the work. An executive writes from executive vantage with the scope of decisions their seat actually owns. When the author makes a strong claim, the claim sits inside their plausible standing. A reader who knows the author's role would not pause on the post and think "that is not what someone in this seat would write."

Example (do not optimize toward this): a Series-A founder describing the specific moment they made a hiring trade-off between two early salespeople, with the texture of having lived it (a specific Slack thread, a specific 30-day review meeting, a specific dollar amount they bet on the call) — not a general "lessons from scaling sales orgs" piece that reads as one stage above their actual position.

**Score 0 (no)** — The post's register is one stage above or below the author's seat. Three concrete examples of the failure mode:

- **Stage-too-high:** Series-A founder narrating Series-D scaling pain ("when you're scaling past 500 reps, the comp ladder breaks at the senior IC tier…") — technically founder content from a founder, but the register implies post-Series-C operations the author has not lived.
- **Role-too-high:** VP-level confidence on IC-level topics — an IC writing VP-stance assertions about cross-functional strategy ("our team's playbook for aligning product and revenue org…") without the grounding of having owned that scope.
- **Role-too-low:** Junior IC writing as CEO — junior writer making market-positioning claims with executive scope ("here's how every founder should think about the category-defining moment…") without standing.

OR the post's topic sits entirely outside the author's plausible standing (motivational/spiritual content from a B2B SaaS founder unconnected to their professional surface; growth-marketing tactics from a CFO with no marketing surface in their work history — though most of these will already have been caught by structural_gate's Role-Topic Token Overlap Gate before reaching the judge).

**Score 0.5 (unknown)** — The author's professional context cannot be inferred from the artifact + source_data alone (cold-start author with no prior posts and no work-history surface; source_data.role is null or stage cannot be inferred to better than two adjacent registers). Emit 0.5 + "unknown" + the specific context that would have to be present to commit to 1 (e.g., "author's stage or employer not in source_data; cannot assess register coherence").

**Required CoT:**
- Step 1: Read the author's source_data block. Identify role (founder / IC / manager / executive), stage (early / mid / late), employer scope (early-stage / scaled), domain expertise. If source_data is null or insufficient to identify stage to within two adjacent registers, emit 0.5 + "unknown" with the specific missing context.
- Step 2: Read the post. Identify the *implied vantage* of the author from the substance — what stage / role / scope does the post's confidence level and frame of reference assume the author occupies? (Not from explicit prefix tokens like "as a founder" — those are gameable; from the substance.)
- Step 3: Compare. Is the implied vantage congruent with the author's actual seat? If gap > one register (founder→executive, IC→VP, junior→CEO, late-stage scope on early-stage seat), score 0 with the specific register signal named. If aligned within one register, score 1. Emit verdict + one-sentence justification naming the specific register signal (or its absence).

Do not score: topic-vs-role overlap (Role-Topic Token Overlap Gate, structural_gate); employer-mention validity (Employer-Mention Validity Check, structural_gate); temporal-claim-vs-recent-activity (Claim-vs-Recent-Activity Check, structural_gate); claim ambition level on its own (a junior IC with deep specialty can make strong claims in their specialty — only score 0 if the claim sits outside the specialty band).

---

## 5. Shared judge-prompt wrapper

```
You are scoring a LinkedIn text-post draft for a B2B professional
audience in 2026. The reader is one of: founder / decision-maker;
mid-career B2B IC (engineer, marketer, product, sales); recruiter
/ talent; industry peer. US is the primary geo default;
substitute readers include SaaS / AI lab / agency / service firm
/ finance / e-commerce operators.

The 2026 LinkedIn algorithm rewards dwell time (0–3s → 1.2%
engagement + capped distribution; 61s+ → 15.6% + full fanout) and
substantive comments (30–80 words, weighted ~15× a like via an NLP
classifier that reads each comment's semantic content). The 360Brew
ranker cross-references each author's claimed expertise against
their published content corpus — a "Topic Authority" score that
gives up to 78% higher distribution to topic-consistent authors and
restricts distribution for topic-dispersed authors. Engagement-bait
CTAs ("comment YES," "tag a friend," "type 1 if you agree") trigger
~60% distribution suppression regardless of account history. These
are platform physics, not soft credibility — the judge is testing
whether the post would produce the reader-effects that map onto
these algorithmic signals.

The post is the lane's locked Component A artifact shape: a
LinkedIn text post, 600–2,000 characters, single-post or short-
thread (2–3 connected posts max), with a trailer at ~210 chars /
first 3 lines above the "...more" cut. Carousels, videos,
newsletters, articles, and polls are out of scope at the judge
layer (they are deferred to sibling lanes per §8). The broader
LinkedIn program (Components B–H: profile audit, content strategy,
comment strategy, DM templates, 30/60/90 roadmap, Topic Authority
plan, cross-platform syndication) is validated by structural_gate,
not by the judge.

Score each of LI-1..LI-5 independently with 0, 0.5, or 1 plus a
one-sentence rationale that follows the per-criterion CoT steps.
Do not blend criteria. Do not infer criteria not stated. If a
criterion's condition is ambiguous from the artifact + source_data
alone, emit 0.5 + "unknown" + one sentence on what would have to be
present to commit to 1.

The reader has seen broetry / hero-stories / janitor-wisdom enough
to recognize the cringe stack within 3 seconds. They've also seen
AI-slop (em-dash density >1.0/100 words, "Let me explain why,"
P.S.↓ closers, symmetrical bullets) and recognize the gestalt
stack — not any single tell. Authentic operator broetry, em-dash
use within stylist range, and algorithm-aware structure are NOT
slop on their own. Score for whether the post would actually earn
dwell + substantive comment + profile-click from a real
professional reader — not for whether it contains specific hook
templates, named frameworks, or template fields.

Emit per-criterion JSON:
{"criterion_id": "LI-N", "rationale": "...", "score": 0 | 0.5 | 1}.
```

---

## 6. Goodhart-resistance verification

Each criterion resists a specific Goodhart-collapse mode named in §3:

- **LI-1**: "Templated specific number + dramatic claim trailer" doesn't pass — the body below the cut must deliver the trailer's promise, not bait-and-switch. The Goodhart move (workflow learns to slot-fill specific numbers + dramatic openers regardless of substance) is bounded by the payoff-coherence test in Step 2 of the CoT.
- **LI-2**: "Generic advice with one named-customer veneer" doesn't pass — the insight must be author-specific per the Alić specificity test. The Goodhart move (workflow learns to drop a customer name into the meat regardless of insight) is bounded by Step 2's swap-the-anchor test.
- **LI-3**: "Replace em-dashes with semicolons" or "swap one tell for another" doesn't pass — the judge tests the gestalt stack (≥2 co-occurring tells) AND the three-signal substance test (specificity in body, affective-marker presence, internal-contradiction tolerance), not single tells. Single-tell whack-a-mole is bounded by gestalt-stack scoring. Voice-substrate provenance check on first-person lived-work claims (Step 1d) bounds the unanchored-confabulation move regardless of surface fluency.
- **LI-4**: "Bolted-on 'what do you think?' closer" or "every post ends with a question" doesn't pass — the comment-seed must be organic to the post's central argument, and the judge predicts the reply-ladder ceiling from the opener's stance, not from surface tokens. Engagement-bait CTAs route to structural_gate as deterministic bait-string detection.
- **LI-5**: "Add 'as a founder' prefix to every post" or "name-drop the employer in every post" doesn't pass — the criterion tests the *implied vantage from the substance*, not from prefix tokens or name-drops. The Goodhart move (workflow learns to replicate the author's last-three-posts' register on every new post) is partially defended by reading for confidence calibration against the source_data seat; the residual defense is variance instrumentation per §11.5 of the design guide.

**Per-component Goodhart resistance (new in v2):**

- **Component B**: workflow that learns to generate profile copy hitting char ceilings without ICP alignment is bounded by `structural_gate` ICP-token overlap check against Component E.
- **Component C**: workflow that learns to name plausible-sounding pillars not anchored on author expertise is bounded by `structural_gate` Jaccard ≥0.2 check against voice substrate.
- **Component D**: workflow that learns to fabricate 10 LinkedIn URLs is bounded by `structural_gate` URL-resolves check + mechanism-family-presence check.
- **Component E**: workflow that learns to generate DM templates without persona anchors is bounded by `structural_gate` named-persona match against ICP.
- **Component F**: workflow that learns to generate calendar-shaped milestones without capacity sizing is partially bounded by `structural_gate` milestone-count + risk-flag check; remaining capacity-sizing risk flagged for first-cohort empirical re-validation.
- **Component G**: workflow that learns to paste-mirror industry-standard pillar-review language is bounded by `structural_gate` quarterly-milestone-references-Component-C-pillar check.
- **Component H**: workflow that learns to name surfaces without naming translation moves is bounded by `structural_gate` verb-presence check.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1 on Component A AND pass the deterministic structural checks on Components B–H. Slot-fill alone scores 0 at the judge layer and fails the gate at the program layer. The ensemble defense matters: LI-3 + LI-5 fire when LI-4 over-rotates toward bait-shaped posts; LI-2 + LI-5 fire when LI-1 over-rotates toward dramatic-but-empty trailers; `structural_gate` Components B–H validation fires when the program-level program structure degrades regardless of Component A scoring. No single criterion catches every over-optimization; the five-criterion judge plus the multi-component structural gate is the defense.

---

## 7. Verification — does the v2 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (with "do not optimize toward this" hedge per design guide §4) ✓
- §5 criterion count: **5 at the judge layer (within ≤5 ceiling, no documented exception)** — the v2 lane scope expansion to multi-component program does NOT add criteria at the judge layer; all 24 additional activities from Step 0 research route to Components B–H validated by `structural_gate`, not to additional judge criteria. The 5-criterion ceiling holds.
- §5 isolation: per-criterion rationale, no blending across criteria ✓
- §6 structured per-criterion CoT (3–4 steps each, evidence-before-score) ✓
- §7 reference-free: examples hedged with "do not optimize toward this"; no model-authored exemplars used as scoring anchors ✓
- §10 input sanitization: applied at the substrate layer per design guide §10, not encoded in rubric prose ✓
- §11 Goodhart-resistance verification (§6 above) — extended to include per-component Goodhart resistance ✓
- §13 specimen criterion template followed ✓

Length per criterion ≈ 200 words at the judge layer (matching CI v3.4's actual depth, which exceeds the design guide's 150-word target due to 3 examples / register-mismatch enumeration / four-mechanism-family enumeration — each elaboration absorbs against a documented failure mode). Total spec body ≈ 8,500 words including §1.5 multi-component expansion and §3 cut/add expansions. Matches CI v3.4 in depth at the judge layer; exceeds it at the §1.5/§3/§8 layers because the multi-component restructure adds Components B–H structural-gate documentation that has no CI analog.

---

## 8. Open questions + sibling-fork triggers (after research synthesis + v2 multi-component restructure)

Reader / Artifact-shape Components A + B–H scope / Success / Failure / 5 Criteria are LOCKED at v2. Remaining decisions:

### 8.1 Three-pair redundancy check (urgent)

Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating >0.7 with another. Three pairs to check:

- **LI-3 ↔ LI-5 (predict r = 0.4–0.6, keep both):** LI-3 tests human-vs-AI voice (gestalt AI-slop stack); LI-5 tests this-author's-seat-vs-some-other-seat (authority-voice register). A post can be high LI-3 (clearly human-written) and low LI-5 (human but in the wrong register for the author — junior ghosting a CEO badly). Conversely, a post can be low LI-3 (AI-slop) and high LI-5 (the AI happened to hit the right register). Dimensions are orthogonal under selection pressure even if correlated on current fixtures.
- **LI-4 ↔ LI-2 (potential absorption candidate):** Insight-bearing posts tend to be more comment-inviting; predict r = 0.4–0.6 but not above 0.7 because the reader-effects are structurally distinct (*learned-something* vs *have-something-to-say*). If r > 0.7, LI-4 may absorb into LI-2 — but the algorithm's 2026 NLP classifier treats comment substance as a promotion gate, not a boost, so the criterion may need to survive even partial redundancy. Flag for empirical resolution.
- **LI-3 ↔ LI-4 ↔ LI-5 covariance instrumentation:** under selection pressure, if LI-4 mean rises while LI-3 or LI-5 mean falls over 3 generations, the workflow is over-optimizing for comment-seed at the cost of voice or author-coherence (contrarian-for-its-own-sake, list-padding, register-pretending). That signal triggers redesign of the over-rotated criterion, not calibration. The covariance pattern across the three is the Goodhart early-warning per design guide §11.5.

### 8.2 Variance instrumentation — deferred until Path 1 validates the pattern on CI

Per design guide §11.5, track per-criterion variance per generation; flag any criterion whose variance grows monotonically over 3 generations or whose mean compresses toward the middle for redesign (not calibration). The Path 1 question (validate-CI-first vs Path 2 propagate-7-lanes-in-parallel) blocks live deployment of variance instrumentation for LI; do not instrument LI variance until the CI variance-monitoring pattern has been validated and the telemetry surface for the autoresearch loop has the pattern wired.

### 8.3 Cold-start handling for LI-3 + LI-5

When `source_data` lacks prior-author posts (new client, first post, no work-history surface), LI-3 and LI-5 lose their grounding anchor. Component C voice-substrate population at `programs/references/voice.md` and Component B profile rewrite provide the program-level mitigations (the voice substrate is the load-bearing input for LI-3's Step 1d; the profile rewrite populates the source_data the judge reads in LI-5). For the judge layer: pass a `source_data.author_context_known = false` flag that triggers LI-3 and LI-5 to emit 0.5 + "unknown" by default rather than scoring blind. Implementation deferred to lane wiring. The `linkedin_engine v040 cold-start mutation` memory provides a structural precedent (`templates/linkedin_engine/skeleton-short_take.md` plus pre-ship checklist).

### 8.4 `structural_gate` expansion (before spec ships to live workflows)

Wire `x_engine/pipeline/slop_gate.py::check_full(text, exemplars_path, platform="linkedin")` into the linkedin_engine `structural_gate` callable (~5 LOC integration; em-dash check already correctly skipped for `platform="linkedin"`). The v2 gate splits into two layers:

**Layer 1 — Component A (text-post) checks (~290 LOC total, ~95% from v1):**

- AI-slop deterministic floor (~40 LOC): P.S.↓ closer regex; "Stop X. Start Y." parallel; "I X for Y years" credential-opener; "Here are N lessons" listicle-bloat opener (additions to `LINKEDIN_BANNED_PHRASES`).
- Three density-based gates (~30 LOC): em-dash density >1.0/100 words flags; broetry-line density ≥40% flags; bullet-rhythm coefficient-of-variation <0.15 flags.
- Three author-context gates (~160 LOC): Role-Topic Token Overlap Gate; Employer-Mention Validity Check; Claim-vs-Recent-Activity Check. Together hoist ~40% of LI-5's surface out of the judge.
- Shape-conformance checks (~30 LOC): character-count band (600–2,000); trailer cut position at ~210 chars; line-break count cap (~15); format detection (text-post vs out-of-scope carousel/video/poll/article).
- 12-phrase engagement-bait blocklist (~30 LOC): "comment YES if you agree," "type 1 if you agree," "tag a friend who needs this," "like for Part 2," "repost if you've felt this," and 7 more covering 90%+ of detected cases (per `LINKEDIN_BANNED_PHRASES`).

**Layer 2 — Components B–H (program-level) checks (~400 LOC new in v2):**

- **Component B (profile, ~60 LOC):** seven elements present (headline ≤220 chars, About ≤2,600 chars with cut-position trailer, Featured = 3 items, banner spec includes copy + CTA, custom URL specified, exactly 5 skills, recommendation plan present); ICP-token overlap with Component E ≥0.2 Jaccard.
- **Component C (content strategy, ~80 LOC):** ≥2 primary pillars + ≥1 secondary pillar named with rationale; format-cadence weekly counts present (text / carousel / video / newsletter / poll); voice substrate populated at `programs/references/voice.md` and non-empty; ≥40 candidate post ideas in backlog with no >50% duplication (Levenshtein); pillar-token overlap with author voice substrate ≥0.2 Jaccard.
- **Component D (comment strategy, ~60 LOC):** exactly 10 target accounts named with LinkedIn URL; URLs resolve; each account has rationale naming a mechanism family from LI-4; daily 15-minute block scheduled; anti-pod-pattern statement present.
- **Component E (DM templates, ~50 LOC):** cold-outbound DM = 3 variants tied to named personas; warm-outbound = 4 variants tied to engagement signals; inbound-response template has 2/3/4-message arc; ICP definition includes titles + company-size + industry + geography; weekly connection target in [50, 100].
- **Component F (30/60/90 roadmap, ~40 LOC):** 30/60/90 milestones each named explicitly; per-period operator actions enumerated; risk-flag section present.
- **Component G (Topic Authority plan, ~40 LOC):** 4 quarterly milestones present; ≥2 inflection-point markers named; pillar-review cadence present; semi-annual rebalance language present; each Q-milestone references a Component C pillar by name.
- **Component H (cross-platform syndication, ~30 LOC):** X→LI rule + blog→LI rule + podcast→LI rule each present; each rule contains a verb describing the register-translation move (de-compress, excerpt, audiogram, etc.).
- **Cross-component coherence (~40 LOC):** Component B headline ICP overlaps with Component E ICP definition; Component C primary pillars referenced in Component G quarterly milestones; Component D target accounts overlap with Component E ICP titles/industry.

**Do NOT block on AI-detector classifier output:** FPR 18–35% against real operators (Authoredup July 2025); treat classifier output as soft signal in judge rationale if at all, never as hard gate.

### 8.5 Vertical fixture coverage and first-cohort overfitting watch

Currently have B2B SaaS / AI-lab / legal services / healthcare practice coverage in fixtures (Anthropic, DWF, Klinika, Perplexity). Build 2–3 fixtures per under-represented vertical (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces, agency principal, mid-career B2B IC) before locking the criteria via empirical redundancy check. Re-validation triggers:

- Any fixture from a vertical not in {B2B SaaS, AI-lab, legal services, healthcare practice} should prompt a quick re-validation pass on LI-2 (insight specificity may need vertical-specific anchors), LI-4 (comment-seed mechanism mix may differ — DTC may favor Mechanism C list-with-photos more heavily than B2B which favors Mechanism A debatable claims), and LI-5 (register conventions vary by vertical — fintech compliance posts have different authority-voice norms than B2B SaaS founder content).
- Any vertical reaching ≥3 active clients should trigger a vertical-specific Component C cadence + format-fit-matrix review (DTC: visual-heavy mix; AI-lab: lower volume + longer-form deeper; finance: newsletter-heavy).

### 8.6 Sibling-lane fork triggers (NEW in v2)

The Step 0 research recommends sibling-lane decomposition for the full 2026 LinkedIn surface. Per JR confirmation, sibling-lane forks are deferred to triggered expansion: a sibling lane stands up only when client demand crosses a measurable threshold. The triggers:

- **`linkedin_carousel` fork:** trigger when carousel demand crosses 3+ clients OR when ≥1 client has a documented Component C cadence calling for ≥1 carousel/week. **Highest-priority sibling-fork target** per Step 0 research §6 (6.60% engagement, 39% more reach than text). The fork inherits Component A's LI-1..LI-5 *shape* (5 outcome questions) but with carousel-specific criteria likely: trailer-slide-earns-swipe, framework-coherence-across-slides, last-slide-CTA-fit, visual-hierarchy, author-context-coherence. Carousel mechanics differ from text-post mechanics (swipe-completion ≠ scroll-completion), so the criteria are sibling-shaped, not identical-copy.
- **`linkedin_newsletter` fork:** trigger when newsletter demand crosses 3+ clients OR when ≥1 client launches a newsletter as part of Component G. Newsletter subscribers have separated distribution + different reader (subscribed, expecting depth) + different success conditions (read-through-rate, click-through-to-CTA, save-for-later); criteria likely: opening-earns-the-full-read, single-insight-clarity, voice-residual, subscribe-incentive-coherence, author-context-coherence. Newsletter long-form belongs in this sibling lane, not Component A.
- **`linkedin_live` fork:** trigger when LinkedIn Live + collab demand crosses 3+ clients. Lower-priority sibling-fork target per Step 0 research (most small-to-medium clients should run 1 Live event per quarter, not weekly). Sibling lane would scope: pre-Live promotion sequence + Live event format + post-Live companion content (clips, carousel, newsletter mention).
- **`linkedin_profile` fork:** trigger when profile-audit depth grows beyond Component B's current 800-word envelope OR when a vertical-specific profile pattern emerges that diverges from the B2B-SaaS-default in Component B (e.g., regulated finance partners need a different About-paragraph register; DTC e-commerce founders need a different Featured-section composition).
- **`linkedin_comment_strategy` fork:** trigger when multi-client coordination becomes a problem — specifically, when ≥3 clients have ≥3 overlapping target accounts in their Component D lists AND coordination of who-comments-when becomes an agency operational problem (e.g., to prevent comment-stacking on the same in-lane creator that might trigger LinkedIn's pod-detection algorithm). Until then, Component D inside the single `linkedin_engine` lane is sufficient.

**Sibling-fork posture:** the v2 lane stays single-lane producing Components A through H. Sibling lanes are not pre-emptively built; they fork only when their trigger fires. This preserves the v2 lane's tractability while preserving optionality for the longer-arc surface expansion.

### 8.7 Propagation order to remaining 6 lanes

Once LI v2 validates on real fixtures alongside CI v3.4, propagate the iterated pattern across the remaining 6 lanes: GEO → MON → MA → SB → X → site_engine. Each lane gets its own Step 1 spec + (optionally) lane-customized deep-research pattern — NOT a mechanical 4-question repeat. The LinkedIn-specific deep-research dispatches (Van Der Blom Depth, AI-slop LI-specific, author-context coherence, comment-seed quality, comprehensive scope) were chosen because they were the load-bearing per-axis failure modes + surface-mapping needs for LI; other lanes have different load-bearing axes and will need different per-axis dispatches.

The v2 multi-component pattern is a NEW propagation candidate: lanes whose deliverables are program-shaped rather than single-artifact-shaped (marketing_audit already is; potentially monitoring, site_engine) may benefit from the same school-B split (judge scopes the atomic-output element; structural_gate validates the broader program around it). Lanes whose deliverables are single-artifact-shaped (X engine, GEO, storyboard) stay single-artifact at both layers.

### 8.8 First-cohort overfitting watch (continued)

The substance tests across LI-2 / LI-3 / LI-4 / LI-5 are anchored on the Welsh / Acosta / Alić / Denning / Meer / Murray / Bloom creator-archetype reference set. gofreddy is a generic AI-native agency targeting tech-savvy founder / early-co clients across verticals, NOT a creator-economy shop. As clients onboard from other archetypes (DTC operators, fintech operators, regulated-finance professionals, hospitality owner-operators, scientific researchers), some anchor patterns may not generalize. The mechanism families in LI-4 are likely robust across archetypes (debatable claim / genuine question / enumerated frame / honest disagreement are platform-physics not creator-archetype-physics); the voice and author-context anchors in LI-3 / LI-5 are more archetype-anchored and may need adjustment. Re-validate when client #5+ onboards from an under-represented vertical.

The Component B–H program structure is more vertically-flexible by design (the format-fit matrix in Component C and the vertical adjustments in Step 0 research §4 cover six default verticals: B2B SaaS, AI-lab, agency, service firm, finance, e-commerce, plus mid-career B2B IC), but the `structural_gate` checks themselves are vertical-independent. If a vertical-specific Component B or Component E pattern emerges that diverges substantially from the default (e.g., regulated finance partners cannot publish specific dollar amounts due to confidentiality bounds, so Component E DM templates need a different qualification arc), that's a sibling-fork trigger per §8.6, not a re-architecture of the v2 lane.

### 8.9 Live-code restoration applied (preserved from v1 + extended in v2)

v1's surgical restoration from agent `a9a34cd5ea2d02315` is preserved in v2:

- **LI-1 live "thoughtful authority, not contrarian punch" lever** → preserved in v2 LI-3 score-0 anchor as the "bait-y or Twitter-translated" cross-platform register failure. The lever distinguishes LinkedIn voice from X voice and is load-bearing in LI-3's Step 1c CoT.
- **LI-1 live "AUTOMATIC ≤4 if bait-y or Twitter-translated"** → preserved in the 0/0.5/1 system as a score-0 anchor in LI-3 (the binary system has no "cap at 4" slot; the failure condition routes to score 0 with explicit "bait-y or Twitter-translated" prose).
- **LI-2 live HARD FLOOR "lived-work claims REQUIRE the named entity in voice.md"** → preserved as a score-0 anchor in LI-3 (voice criterion, where voice substrate is already loaded by `load_source_data`). The original "score capped at 7" semantic is re-expressed as a score-0 condition; the binary system collapses graduated caps to anchor conditions. LI-3 Step 1d CoT enforces the substrate provenance check on every first-person specific lived-work claim. **v2 extension:** Component C's voice substrate validation at `structural_gate` provides the program-level guarantee that the voice.md file exists and is non-empty before any post fixture runs through the judge.
- **LI-3 live "contrarian hot-takes that work on X (≤3 even when same hook scores 5 on X)"** → preserved in v2 LI-4 score-0 anchor as cross-platform reply-ladder collapse (the X-shaped hook that produces DH3–DH5 substantive replies on X collapses to DH0–DH2 cheerleading/hostility on LinkedIn). Re-expressed as a score-0 condition; the "cap at 3" slot does not exist in 0/0.5/1.
- **LI-5 live graduated hashtag-count scoring (3-5 ideal / 1-2 cap-at-7 / 0 cap-at-4)** → preserved as fully hoisted to `structural_gate` per §4 architecture decision. The live `structural_gate` already enforces hashtag count `[1, 5]` as hard bounds. The graduated 1-2-suboptimal-cap-at-7 / 0-cap-at-4 quality scoring has no equivalent in the 0/0.5/1 binary system and is therefore retired at the judge layer. This is an intentional reduction at v1 + v2; flagged for restoration via structural_gate quality-score side-channel if first-cohort fixtures show 1-2-tag posts under-performing 3-5-tag posts in production.

**LI-6 cross-cohort criterion is NOT restored as a 6th judge criterion** (per X-lane sibling decision, §5 ceiling, and v2 multi-component restructure). The live code's `cross_item_criteria={"LI-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=600)}` contract on `SPEC` at `session_eval_linkedin_engine.py` lines 219–225 survives at the workflow level: when the lane produces a multi-draft session, the cross-cohort narrative-archetype-variance + voice_pillar-spread check fires at the session aggregator, not as a per-draft 6th criterion. **v2 extension:** the cross-cohort signal now also flows through Component C's format-fit matrix and Component G's quarterly milestones — cross-draft consistency is a Component C / G concern, not a per-post LI-N concern.

**Items NOT restored (with reasoning, preserved from v1):**
- Bracket-aware structural richness (SHORT_TAKE 500–900 / THOUGHT_LEADER 1500–2500 / CASE_STUDY 2500–3000) — v2 §1.5 deliberately keeps a single 600–2,000 char text-post form factor per "shape-drift Goodhart" defense at the judge layer. The live three-bracket prescription is intentional re-architecture, not a restoration target. If the lane wires brackets back, §1.5 and the structural_gate char-band would need updating; flagged for future re-validation.
- JR's named target audiences ("B2B buyers + agency operators + C-suite") — v2 Reader spec (§1) generalizes to four primary audience types (founder/decision-maker, mid-career B2B IC, recruiter/talent, industry peer) that subsume the three named audiences. The generalization is intentional per the "don't overfit on a single client when designing the platform" project memory; gofreddy targets tech-savvy founder/early-co clients across verticals. **v2 extension:** the substitute-reader list now explicitly includes SaaS / AI lab / agency / service firm / finance / e-commerce per JR confirmation; US is primary geo default.
- Specific bait-string examples (`Thoughts? 👇`, `Agree? 🤔`, `Here's what I learned.` close) — survive as engagement-bait classifier-suppression in §3 + §8.4 structural_gate routing block. Not re-quoted in LI-3/LI-4 score-0 prose because bait-string detection routes to structural_gate as deterministic regex, not to judge-layer outcome scoring.
