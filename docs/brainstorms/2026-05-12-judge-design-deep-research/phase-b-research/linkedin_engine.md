# linkedin_engine — Phase B calibration corpus

> Lane purpose: short-form LinkedIn posts produced as `drafts/<id>.md` across three brackets — **short_take** (500–900), **thought_leader** (1,500–2,500), **case_study** (2,500–3,000) — plus `angles/<id>.json` pre-fold hook candidates. Two adaptors: the operator profile (JR + clients, B2B trust + pipeline) and named-byline (Dr. Maria for Klinika Melitus; named partners for DWF Poland). Engagement formula: `(reactions×1 + comments×3 + shares×5) × exp(-days/14)`.
>
> Ceiling target (9-tier): a draft a senior B2B buyer DMs to a colleague. Frameworkable artifact present (list, decision matrix, named principle, checklist). Operationally specific (named clients, dated decisions, real numbers). Buyer's-problem-centric, not author-growth memoir. Pre-fold hook delivers a stake-claim that earns the "see more" tap.
>
> **Adaptor divergence:** the operator profile has voice latitude (sarcastic, contrarian, name-naming). Klinika/DWF are compliance-bounded — no specific clinical results, no comparative claims, no solicitation, no fee mentions, no identifiable client matters. A judge that doesn't branch will either green-light a non-compliant Maria draft or flunk a sharp operator draft for being "too aggressive."

---

## 1. Top 9-tier signals — what excellent LinkedIn content looks like in 2026

**L1. Stake-claim hook in the first 210 characters that survives the mobile "see more" cutoff.**
- *Source:* RvdB May 2026: "LinkedIn's algorithm literally measures 'satisfaction' in the first 60 minutes. Low dwell time = buried before your network even sees it." ([tweet](https://x.com/RichardvdBlom/status/2052720165637230835)). Posts with 0–3s dwell achieve 1.2% engagement; 61s+ achieve 15.6% — 13× gap ([Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works), [Dataslayer 2026](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)).
- *Mechanism:* Mobile collapses at ~210 chars / ~3 lines. The visible portion has to earn the tap or the satisfaction score craters in the first 60 minutes and the post dies before reaching 2nd-degree.
- *Judge-able test:* Strip the post at char 210. Remaining text must contain (a) a specific number, named entity, or dated event AND (b) a falsifiable or contrarian claim. RvdB's "After researching 1.3 million LinkedIn posts, here's the finding that surprised me most: Carousels used to dominate. In 2026, they're declining fast." ([tweet](https://x.com/RichardvdBlom/status/2050551628109914154)) passes. "Thoughts on leadership..." fails.

**L2. Frameworkable artifact — a named list, principle, decision matrix, or checklist that survives copy-paste into Notion.**
- *Source:* RvdB on growth-curve formats by tier ([May 12 2026](https://x.com/RichardvdBlom/status/2054094218826535213)). Saves now carry 5× the algorithmic weight of a like and 2× the weight of a comment ([Linkboost 2026](https://blog.linkboost.co/linkedin-algorithm-changes-2026/)); LinkedIn confirmed in 2025 that save velocity is the strongest single distribution signal.
- *Mechanism:* The B2B buyer who DMs a post to a colleague is the highest-value reader on LinkedIn. They only forward content that is *forwardable* — a named principle, a 3-step framework, a checklist the recipient can act on without reading the whole post.
- *Judge-able test:* Extract every numbered/bulleted block. Does at least one name itself (Bloom's "New Opportunity Razor" — [tweet](https://x.com/SahilBloom/status/2051997395827798274)) or define an operational test (Welsh's "Three questions worth asking once a quarter" — [tweet](https://x.com/thejustinwelsh/status/2052012264811643162))? Generic "5 lessons I learned" fails.

**L3. Authority anchoring — named clients, dated decisions, real metrics; not vague "a client I worked with."**
- *Source:* RvdB anchors every claim: "We tracked 1.3 million posts." "After training 350,000 people on LinkedIn..." ([tweet](https://x.com/RichardvdBlom/status/2053807331310268761)). Same post names "Anthropic is hiring a 'Copywriting Lead' at $320k/year" — specific company, specific role, specific number.
- *Mechanism:* "I once worked with a SaaS company" is unfalsifiable filler. "When DWF advised on the 2024 Polish ESG carve-out for retail banks…" signals the author was in the room.
- *Judge-able test:* Count anchored specifics (named org / named person / dated decision / number-with-unit). Floor: ≥1 anchored specific per 300 chars in thought_leader and case_study.

**L4. B2B-buyer-problem framing — the post is about the buyer's *current week*, not the author's growth journey.**
- *Source:* RvdB May 3: "Nobody cares what you do. Post about what they need." ([tweet](https://x.com/RichardvdBlom/status/2050832729185403289)). 2026 B2B research: 60% of buyers discover brands through creator content before filling a form; 74% trust thought leadership over product marketing; 95% say strong thought leadership opens them to outreach ([LaGrowthMachine](https://lagrowthmachine.com/linkedin-marketing-strategy-2026/)).
- *Judge-able test:* Ratio first-person to buyer-diagnosis. Thought_leader floor: ≥40% of body describes buyer situation; ≤30% author. Inverts for case_study where the lesson is the unit.

**L5. Interest-graph topic consistency — the post slots into a pillar this profile is already known for.**
- *Source:* RvdB May 2026: "LinkedIn doesn't reward your network anymore. It rewards your Interest Graph." ([tweet](https://x.com/RichardvdBlom/status/2052644667536126394)). Average reach has reset from 15–20% of followers to 8–12% because Topic Authority displaced follower count ([Goodman](https://melaniegoodmanlinkedinconsultant.substack.com/p/linkedin-algorithm-2026-reach-topic-authority)).
- *Judge-able test:* Does the post belong to one of this profile's declared pillars? Operator gets a discretionary off-pillar slot per week. Named bylines cap-at-6 on off-pillar.

**L6. Save/share-trigger payoff — the post's core unit of value is portable.**
- *Source:* RvdB: "Most people optimize for likes. The algorithm optimizes for attention." ([tweet](https://x.com/RichardvdBlom/status/2049099622728028418)). 2026 weighting: comments 15× likes; saves 5× likes / 2× comments; document/PDF posts get 3× single-image engagement because they require active swiping ([Linkboost](https://blog.linkboost.co/linkedin-algorithm-changes-2026/), [Connectsafely](https://connectsafely.ai/articles/linkedin-document-posts-pdf-guide-2026)).
- *Mechanism:* Save = "I'll need this later." Share = "you need this now." Both fire only when the core is self-contained — quote-card-quality lines, named principles, decision tests.
- *Judge-able test:* Can the post's core be reduced to a screenshot-able quote-card? Bloom's "Major life hack: Don't complain, ever" ([May 9](https://x.com/SahilBloom/status/2053091119643181292)) — 16,644 likes / 5,791 bookmarks / 730K views — is the canonical example: the title-claim *is* the screenshot.

**L7. Anti-broetry cadence — paragraphs with internal structure, not single-sentence-per-line dramatics.**
- *Source:* Broetry originated as Josh Fechter's algorithmic gaming hack; LinkedIn updated and banned the originator ([Fenwick.media](https://fenwick.media/rewild/magazine/dead-broets-society-behind-the-strange-story), [BuzzFeed News](https://www.buzzfeednews.com/article/ryanmac/why-are-these-posts-taking-over-your-linkedin-feed-because)). By 2026 broetry triggers the "low-effort engagement bait" classifier alongside polls (0.07% engagement, "algorithmically dead" — [Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works)). The 9-tier B2B buyer reads broetry as a junior contractor or content farmer — both kill the trust window.
- *Judge-able test:* Paragraph-length histogram. >50% one-sentence paragraphs AND post >800 chars = flag broetry. Counter-evidence: Welsh's "Some tradeoffs to be honest about:" with hyphen-list ([tweet](https://x.com/thejustinwelsh/status/2051995925413863745)) is structured-list with prose surround — the list serves a thesis.

**L8. Dwell-engineered density — every paragraph adds new information.**
- *Source:* RvdB: "the algorithm now rewards depth over frequency. One strong post beats three mediocre ones." ([tweet](https://x.com/RichardvdBlom/status/2049739523727196628)). Click-bounce detection (tap "see more" → leave) actively deprioritises bait openers ([Linkboost](https://blog.linkboost.co/linkedin-algorithm-changes-2026/)).
- *Judge-able test:* Random-sample 3 paragraphs. Each must contain ≥1 specific (named entity, number, dated event, mechanism explanation) unpredictable from the previous paragraph. Welsh's X content (e.g. "Life hack 101: Become completely addicted to improving yourself.") FAILS this test if cross-posted to LinkedIn — exactly why LI-1 auto-≤4s Twitter-translated.

**L9. Compliance-clean surface (Klinika/DWF) — no specific clinical results, no comparative claims, no fee mentions.**
- *Source:* Polish + EU MDR/AESC aesthetic-medicine code; Polish Bar + DWF UK partner rules.
- *Mechanism:* A 9-tier-engaging post that violates compliance is automatically below 5-tier because legal/clinical risk exceeds engagement value. Compliance is a precondition, not a booster.
- *Judge-able test:* Per byline, run the compliance string-match list. Any hit caps score at 4.

**L10. Insight density > 0.40 chunks per 100 chars in thought_leader.**
- *Source:* Bloom's high-engagement long-form (["Money advice" May 6](https://x.com/SahilBloom/status/2052006655303340447) — 4,449 likes / 2,342 bookmarks / 226K views) averages 0.45–0.55 chunks/100 chars. His low-engagement long-form ([same day "New Opportunity Razor"](https://x.com/SahilBloom/status/2051997395827798274), 212 likes / 47 replies — weakest in his top-20) drops to ~0.28 because Hofstadter + Djokovic padding dilutes density.
- *Judge-able test:* Chunks (named orgs/people, numbers with unit, dated events, named principles, falsifiable predictions, mechanism explanations) / chars × 100. Floors: thought_leader 0.35, case_study 0.40, short_take 0.50.

**L11. Personal-profile distribution multiplier respected — no company-page voice.**
- *Source:* RvdB May 1: "Company pages make up 5.37% of the average LinkedIn feed. Personal profiles? 94.63%." ([tweet](https://x.com/RichardvdBlom/status/2050112484028092508)). Personal profiles 8× company-page engagement ([LaGrowthMachine](https://lagrowthmachine.com/linkedin-marketing-strategy-2026/)).
- *Judge-able test:* String-match opener anti-patterns: "We at...", "Today, we are excited to...", "I'm thrilled to share...". Any hit caps thought_leader / case_study at 5.

**L12. Pillar diversity across the week — same profile should not post 5 thought_leader posts in 7 days.**
- *Source:* RvdB growth-curve format mix ([May 12](https://x.com/RichardvdBlom/status/2054094218826535213)) implies blend across tiers. The interest graph weights topic consistency AND format diversity within that topic; 5× thought_leader in a week reads as a sprint or a panic.
- *Judge-able test:* The lane emits a 7-day pillar histogram. Judge caps the *evolution loop's* lane-level score if any bracket exceeds 60% of the week.

---

## 2. Top 5-tier signals — competent professional broetry middle

Posts that don't fail; they just don't earn forwarding. Likes from existing network; zero comments from strangers.

**M1. Generic platitude with mild authority signal.** Welsh's "Life hack 101: Become completely addicted to improving yourself." ([May 9](https://x.com/thejustinwelsh/status/2053083083587363187)) — 888 likes / 105 bookmarks on 575K followers. Underperforming for him; true but unforwardable; no artifact.

**M2. Reasonable list with no named anchor.** Welsh's "How to increase your luck: Read more, Write more, Build more, Meet more people, Introduce more people" ([May 4](https://x.com/thejustinwelsh/status/2051287490372194477)) — 1,016 likes / 254 bookmarks. List works; no named principle; reads as competent advice you've seen elsewhere.

**M3. Personal-philosophy quip with no operational handle.** Welsh's "My life's goal is to make an impact while defending my family, hobbies, and health." (172 likes). Consistent voice; no buyer-problem framing; no portable unit. 5-tier ceiling for operator; NOT acceptable on named-byline (Maria/DWF can't post personal-philosophy quips at all).

**M4. Long-form with one good paragraph buried in padding.** Bloom's "New Opportunity Razor" ([May 6](https://x.com/SahilBloom/status/2051997395827798274)) names a framework (L2 passes) but pads with Hofstadter + Djokovic + restatement. Density ~0.28 vs. his usual 0.45+.

**M5. Industry-observation lacking specificity.** RvdB May 3: "the platform rewards people who make other people stay longer. That's the entire algorithm in one sentence." ([tweet](https://x.com/RichardvdBlom/status/2050908227261362654)). True; well-phrased; zero specific number. Competes with every other "the algorithm is about X" claim — 51 views.

**M6. Story-led with a true-but-trite lesson.** Bloom's "default to praise of people who aren't in the room" ([May 7](https://x.com/SahilBloom/status/2052393729730785492)) — 2,253 likes / 1,020 bookmarks (high absolute but below his median). Real principle; no dated decision, no named situation, no decision matrix.

---

## 3. Slop patterns (1-tier — automatic cap)

**S1. Motivational poster ("Read that again. ↑").** Single-sentence post re-emphasising itself. 2017-Instagram inspiration leaking onto LinkedIn ([Workweek](https://workweek.com/2022/01/15/why-is-linkedin-so-cringe/), [Lying To Ourselves](https://lyingtoourselves.substack.com/p/how-not-to-be-a-linkedin-influencer)).

**S2. Uber-driver opener ("My Uber driver taught me..." / "An intern said something profound this morning...").** Codified meme because it introduces fabricated-or-embellished anecdotes serving corporate lessons. Triggers immediate cynicism; depresses dwell from sentence 1.

**S3. Fake-vulnerability with impossibly clean lesson.** "I cried in the bathroom at $1B exit. Here's what nobody tells you." Structural tell: emotional setup → clean 3-bullet "lesson learned." Real vulnerability rarely produces 3-bullet structure same-day. Broetry critique: the form "abstracts away details that a critic might interrogate" ([Fenwick](https://fenwick.media/rewild/magazine/dead-broets-society-behind-the-strange-story)).

**S4. Hashtag-stuffer (8+ generic tags).** `#leadership #motivation #success #entrepreneurship #business`. 2026 deprioritises generic-tag stuffing; 3–5 *specific* hashtags is the modern recommendation ([Dataslayer 2026](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)).

**S5. Single-sentence-per-line broetry cadence on >50% of paragraphs in posts >800 chars.** Originator banned; 2026 classifies this cadence as low-effort engagement bait ([Rosback](https://katherinerosback.com/cognitive-outsourcing-why-linkedins-broetry-writing-fad-is-simply-lazy-communication/)).

**S6. Credential-flex with no anchored claim.** "As a 3x exited founder, 2x TEDx speaker, and Forbes 30 Under 30..." with no specific lesson or buyer problem. Résumé-on-feed.

**S7. "Thoughts? 👇" engagement-bait close.** 2026 algorithm explicitly detects and penalises ("Comment YES if you agree", reaction polls — [Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works)). LinkedIn's Q3 2025 finding (60% of high-engagement posts used optimisation tactics while satisfaction declined) triggered the engagement-bait suppression rollout.

**S8. LinkedIn-AI-tells — "delve", "in today's fast-paced world", em-dash carpet, "It's not X, it's Y" three times in a row, "synergy", "leverage", "unpack" as filler verbs.** Tighter list than X version because LinkedIn-AI-tells skew corporate-pleasing.

---

## 4. What separates 9-tier from 5-tier

**4a. Hook 2-line yield.** 9-tier packs number + named entity + contrarian claim into ≤210 chars: "I researched 1.3 million LinkedIn posts. Here's the one finding no playbook covers: LinkedIn doesn't reward your network anymore." 5-tier delivers true-but-generic: "The platform rewards people who make other people stay longer."

**4b. Insight density.** 9-tier 0.40+ chunks/100 chars. 5-tier 0.25–0.35 (good ideas, padded with restatement). 1-tier <0.15.

**4c. Authority anchoring.** 9-tier names the client, date, decision: "When DWF advised on the 2024 ESG carve-out for retail banks…" 5-tier hides behind genre: "A client I worked with last year…" 1-tier flexes credentials with no anchor.

**4d. Voice authenticity vs. LinkedIn-generic.** 9-tier sounds like the actual person — Welsh's dry contrarianism ("A weird side effect of building a simple business is that people always assume you're hiding the complicated part." [May 4](https://x.com/thejustinwelsh/status/2051271131739406527)) is recognisably him. 5-tier sounds like any motivated professional. 1-tier sounds like ChatGPT-with-an-MBA.

**4e. Share/save trigger.** 9-tier: a Series-B founder could copy this into Notion and use it tomorrow. 5-tier: enjoyable to read; no portable unit. 1-tier: no unit at all — just affect.

**4f. B2B trust posture.** 9-tier diagnoses the buyer's current week ("reach has reset to 8–12% of followers — here's what that means for your cadence"). 5-tier is the author's transformation memoir. The transformation can be 9-tier IF the lesson translates immediately; otherwise it's 5-tier on operator and below 4 on named-byline.

---

## 5. The Klinika + DWF specifics

### Klinika Melitus — Dr. Maria Krawczyk, aesthetic-medicine physician (Polish/English)

**Works:**
- Procedure-mechanism explainers ("Why HA filler migrates and how injection plane choice prevents it") — frameworkable, compliance-safe (no result claims), anchors authority via mechanism not outcomes.
- Decision-aid checklists ("5 questions to ask before any cosmetic injectable") — checklist serves the patient, not the clinic.
- Regulatory/safety commentary ("What the 2024 EU MDR update means for non-CE marked devices") — translates regulation for clinic-owner peers.
- Bilingual cadence: Polish hook for LinkedIn-Polska-Aesthetic-Medicine pillar; English thought_leader when targeting Krakow/Warsaw international-clinic owners.

**5-tier / fails:**
- "I love what I do." — 4-tier no matter how prettily written.
- "We had an amazing transformation with a patient last week." — 1-tier (comparative result + patient context).
- Before/after framing as marketing rather than education.
- English-only when audience is Krakow patient-acquisition adjacent.

**Compliance hard floor:** No specific clinical-result numbers. No comparative claims ("better than X", "the best filler in Poland"). No solicitation ("DM me to book"). Patient stories only as anonymised mechanism-illustrations.

### DWF Poland — Named partner bylines (Polish regulatory-commentary lane)

**Works:**
- Polish-language regulatory-update explainers under the *named partner's* byline (not "DWF Poland posts"): "Co oznacza nowelizacja ustawy o przeciwdziałaniu praniu pieniędzy dla działów compliance w bankach detalicznych" — partner-bylined, dated, mechanism-led.
- Cross-jurisdictional UK↔PL comparative analysis on regulatory regimes — DWF is the bridge so this voice is differentiated.
- "What we're seeing in client matters" framed as macro-trend, never as case disclosure.
- Long-form case_study (2,500–3,000) outperforms short_take here because regulatory readers want depth; pre-fold hook still must earn "see more."

**5-tier / fails:**
- Generic "Top 5 GDPR mistakes" — junior-associate content for a partner byline.
- Solicitation ("Need ESG advice? Get in touch.") — solicitation rules apply.
- Discussing specific client matters even obliquely identifiable.
- English-only — Polish DWF pillar collapses without Polish content.

**Compliance hard floor (Polish Bar / DWF partner rules):** No solicitation. No fee mentions. No comparative claims against named competitors. No opposing-party criticism. No client identification, however oblique. Partner voice fidelity at long-form — must read as if dictated by the named partner, not produced by marketing.

---

## 6. 2026 emerging signals

**6a. Satisfaction score (60-minute window).** LinkedIn measures "satisfaction" via dwell time + engagement velocity + content completion in the first 60 minutes ([Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works), [Linkboost](https://blog.linkboost.co/linkedin-algorithm-changes-2026/)). Platform stated December 2025 that 60% of Q3 2025 high-engagement posts used optimisation tactics while satisfaction declined — triggering the ranking-change rollout. *Judge implication:* the rubric must value first-60-min readability proxies (hook strength, paragraph cadence, scroll-friendliness) — anything that fails the satisfaction window is dead regardless of long-tail merit.

**6b. Interest graph displaced relationship graph.** Topic Authority replaced follower count as primary distribution driver ([RvdB Algorithm Report 2026](https://richardvanderblom.com/), [Goodman](https://melaniegoodmanlinkedinconsultant.substack.com/p/linkedin-algorithm-2026-reach-topic-authority)). Average reach has reset from 15–20% of followers to 8–12% because the graph rewires around topic relevance. *Judge implication:* off-pillar posts on named bylines cap at 6 (L5); planner pillar-discipline is now a first-order quality input.

**6c. Document/PDF post boost (saves > likes).** Documents drive 3× single-image engagement (active swiping required); saves weight 5× likes / 2× comments ([Linkboost](https://blog.linkboost.co/linkedin-algorithm-changes-2026/), [Connectsafely](https://connectsafely.ai/articles/linkedin-document-posts-pdf-guide-2026), [Oktopost](https://www.oktopost.com/blog/linkedin-carousel-pdf-best-practices/)). 8–12 slides is the optimal range. *Judge implication:* the lane should emit `attachments/<id>.pdf` briefs for case_study when the artifact suits carousel form; reward portable-artifact-presence even when text-only.

**6d. Dwell-time weighting + click-bounce detection.** 0–3s dwell ≈ 1.2% engagement; 61s+ ≈ 15.6% — 13× gap ([Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works)). Click-bounce (tap "see more" → leave) now deprioritises bait openers. *Judge implication:* punish hooks that are intriguing-but-undelivered. L1 must check pre-fold yield AND post-fold payoff.

**6e. External-link reach drag (~18.8%–60%).** RvdB's 1.3M-post study: one in-body external link reduces median reach by 18.8% ([source](https://x.com/RichardvdBlom/status/2050551628109914154)). Other 2026 sources report 40–60% drops ([Linkboost](https://blog.linkboost.co/linkedin-algorithm-changes-2026/), [Gromming](https://gromming.com/blog/linkedin-external-links-penalty)). First-comment workaround now also penalised (–5% to –10%) but better than in-body. *Judge implication:* flag drafts with >1 in-body external link; route external references to a `comments_first_link` field rather than inline.

**6f. Personal-profile vs. company-page (94.63% vs. 5.37%).** Personal profiles 8× company-page engagement ([RvdB](https://x.com/RichardvdBlom/status/2050112484028092508), [LaGrowthMachine](https://lagrowthmachine.com/linkedin-marketing-strategy-2026/)). *Judge implication:* company-page voice ("We at...", "Our team is excited to...") in a personal-profile draft is structural error — cap at 5; the lane's named-byline mode must enforce first-person personal voice.

**6g. Polls algorithmically dead.** 0.07% engagement ([Ordinal](https://www.tryordinal.com/blog/how-linkedins-algorithm-works)) — LinkedIn AI classifies polls as low-effort bait. *Judge implication:* if the planner emits a poll draft, auto-1.

---

## 7. Implications for the judge — keep/strengthen/split LI-1..6 + new criteria

### Audit of existing rubric

**LI-1 (LinkedIn voice, auto-≤4 on Twitter-translated): KEEP + STRENGTHEN.** The X corpus confirms it — Welsh's high-engagement X content (100–300 char tweets) would fail dwell-engineering on LinkedIn because there's no paragraph cadence, no scannable structure, no portable artifact. Strengthen: add translation-detection (zero LinkedIn-native structural elements AND <300 chars in thought_leader = auto-4). Add company-page-voice trigger (L11) as a co-cap pattern.

**LI-2 (factual grounding, hard floor on unnamed lived-work, cap-at-7 on vague specificity): KEEP + STRENGTHEN.** Add named-anchor-count test: ≥1 anchored specific per 300 chars in thought_leader/case_study is the floor; below that, cap at 6. The 9-tier ceiling requires *operationally* specific anchors — named clients, dated decisions, real numbers.

**LI-3 (hook earns next line, story-led, punishes hot-takes): KEEP + SPLIT.** Split into:
- **LI-3a Pre-fold hook yield.** ≤210 chars contains specific number OR named entity OR contrarian claim.
- **LI-3b Post-fold payoff.** Hook's claim delivered within next 600 chars or post fails click-bounce. If the hook promises a specific number/named-thing, body must contain it before char 800.

**LI-4 (zero AI-tells + LinkedIn-AI-tells): KEEP + STRENGTHEN.** Tighter LinkedIn list: "delve" (auto), "in today's fast-paced world" (auto), "synergy/leverage/unpack" as filler verbs, em-dash carpet (>4 in <1,000 chars), "It's not X, it's Y" used >2× same post, "Read that again." self-reflexive, "Thoughts? 👇" close.

**LI-5 (structure + hashtag count): KEEP.** 3–5 specific hashtags. Add hashtag-specificity test: generic-tag stuffing caps at 6 even with correct count.

**LI-6 (cohort archetype diversity): KEEP.** Tie to L12 (week-level pillar diversity — no single bracket exceeds 60% of week's drafts). Enforced at *lane evolution* score, not individual draft.

### NEW criteria — known gaps

**LI-7 (NEW): Frameworkable-artifact presence. Important.**
- *Why:* Save-velocity-driven 2026 algorithm makes "portable artifact" the single highest-leverage feature. Likes 1×; saves 5× and growing.
- *Anchors:*
  - **1:** No portable unit. Pure affect or memoir.
  - **3:** A list/structure present but unnamed/generic ("5 lessons learned"); screenshot-quotable but wouldn't be.
  - **5:** A named artifact (named principle, decision matrix, checklist, framework) that survives copy-paste into a B2B buyer's Notion.
- *Ground-truth verification:* 30-day shadow run — correlate LI-7 scores against `bookmarkCount / impression`. Hypothesis: LI-7=5 produces ≥2× the save-rate of LI-7=3.

**LI-8 (NEW): B2B trust posture — buyer's-problem-centric vs. author's-growth memoir. Important on operator, ESSENTIAL on named-byline.**
- *Why:* 74% of B2B decision-makers trust thought leadership over product marketing only when it addresses *their* problem; lurking is the dominant pre-form behaviour and lurkers bail when content reads as memoir.
- *Anchors:*
  - **1:** Pure author-growth memoir. 80%+ first-person-singular, zero buyer diagnosis.
  - **3:** Story-led with a real but generic lesson; structurally about the author's transformation.
  - **5:** Author's experience is the vehicle; ≥40% of body diagnoses the buyer's current week or names a specific buyer-segment problem. Welsh's "weird side effect of building a simple business…" lands here — diagnostic about how investors/customers misread simple businesses.
- *Adaptor branch:* On Maria/DWF this is essential, not important — author-journey posts fail compliance posture even when string-match-compliant.

**LI-9 (NEW): Insight density — chunks per 100 chars. Important.**
- *Why:* Dwell time is the primary distribution gate; density is the proxy that lets a long post earn the dwell rather than burn the reader.
- *Definition:* Chunk = named org / named person / number-with-unit / dated event / named principle / falsifiable prediction / mechanism explanation.
- *Anchors:*
  - **1:** <0.15 chunks/100 chars. Motivational-poster slop or broetry padding.
  - **3:** 0.20–0.30. Competent but underweight.
  - **5:** ≥0.40 thought_leader, ≥0.50 short_take, ≥0.35 case_study. Bloom's "Money advice" at ~0.45 chunks/100 chars and 4,449 likes / 2,342 bookmarks is the calibration anchor.
- *Ground-truth verification:* Same 30-day shadow run. Hypothesis: LI-9 correlates with `(comments + 3×shares) / impression` at r>0.40 across operator + named-byline drafts.

**LI-10 (NEW): Pre-fold hook delivers stake-claim within 210 chars. Important (sharper sibling of LI-3a).**
- *Why:* The mobile "see more" cutoff is the single most-cited 2026 algorithm signal.
- *Anchors:*
  - **1:** Pre-fold 210 chars has no number, no named entity, no contrarian claim. Pure throat-clear or affect.
  - **3:** Specific element present but not load-bearing (names a topic without taking a position; or takes a position without an anchor).
  - **5:** Specific number OR named entity AND falsifiable/contrarian claim within 210 chars. RvdB's "I researched 1.3 million LinkedIn posts. Here's the finding that surprised me most: Carousels used to dominate. In 2026, they're declining fast." passes.
- *Ground-truth verification:* Direct — measure first-60-min CTR-to-expand against LI-10 score in shadow run.

**LI-11 (NEW): Compliance precondition. Essential, adaptor-gated (named-byline only), hard floor.**
- *Why:* A 9-tier post on Maria's profile that violates aesthetic-medicine compliance creates real risk; hard-floor rather than weight.
- *Anchors:*
  - **1:** Any compliance-list string-match hit. Maria: specific-result claims, comparative-claims, solicitation, identifiable patient detail. DWF: solicitation, fee discussion, comparative against named competitor, opposing-party criticism, identifiable client matter.
  - **5 (compliance pass):** Zero string-match hits AND the post's claims are mechanism/regulatory/educational rather than promotional.
  - Compliance is binary in scoring contribution: 1 caps overall post at 4 regardless of any other criterion; 5 adds zero (it's a precondition).
- *Adaptor branch:* Operator profile skips this entirely — its compliance surface (defamation, NDA, public-client confidentiality) is handled in a separate operator-compliance pre-check upstream.
- *Ground-truth verification:* Compliance string-match lists maintained per byline; audit by sampling 10 drafts per byline per month for compliance-officer review.

---

## Summary — judge-design diff vs. current LI-1..6

- **Keep:** LI-1..6 (all six well-founded; corpus + 2026 research validate each).
- **Strengthen:** LI-1 (translation-detection + company-page-voice triggers), LI-2 (named-anchor count), LI-4 (sharper LinkedIn-AI-tells), LI-5 (hashtag-specificity).
- **Split:** LI-3 → LI-3a (pre-fold yield) + LI-3b (post-fold payoff / click-bounce defence).
- **Add (5 new):** LI-7 (frameworkable artifact, important), LI-8 (B2B trust posture, important / essential on named-byline), LI-9 (insight density, important), LI-10 (sharper pre-fold stake-claim, important), LI-11 (compliance precondition, essential on named-byline, hard floor).

The headline gap in the current rubric is **portability** (LI-7). The 2026 algorithm rewards saves at 5× likes and shares at the heaviest weight in the lane's engagement formula, but the existing criteria don't directly measure whether a post is portable. Closing that gap is the single highest-expected-value rubric change for this lane.
