---
date: 2026-05-18 v1
type: judge-design Step 1 — linkedin_engine optimal-output spec
status: DRAFT v1 — research-synthesized; awaiting pairwise redundancy check + fixture validation
parent: docs/handoffs/2026-05-15-judge-design-next-session-brief.md
guide: docs/rubrics/judge-design-guide.md
sibling_spec: docs/handoffs/2026-05-17-judge-design-step1-competitive.md (CI v3.3 gold-standard structure)
companions:
  - docs/research/2026-05-18-judges-domain-linkedin-engine.md (generalist domain research)
  - docs/research/2026-05-18-linkedin-engine-van-der-blom-depth.md (Depth Score deepening)
  - docs/research/2026-05-18-linkedin-engine-ai-slop-li-specific.md (AI-slop axis deepening)
  - docs/research/2026-05-18-linkedin-engine-author-context-coherence.md (author-context axis deepening)
  - docs/research/2026-05-18-linkedin-engine-comment-seed-quality.md (comment-seed axis deepening)
revision_history:
  - 2026-05-18 v0 — initial draft, 5 criteria, before research deliverables consumed
  - 2026-05-18 v1 — research-synthesized: gestalt-stack reinforcement in LI-3, outcome-shaped anchor + 4 mechanism families + reply-ladder CoT in LI-4, 3 register-mismatch examples + structural_gate hoist in LI-5, §1.5 Artifact-shape LOCKED, §3 "looks like slop but isn't" defense, structural_gate routing block, Topic Authority signal awareness in §5 wrapper. 5 criteria — no 6th. AI-failure surfaces route to structural_gate, not a documented exception.
---

# LinkedIn Engine — Optimal-Output Spec (DRAFT v1)

Conforms to `docs/rubrics/judge-design-guide.md`. Frameworks (Van Der Blom, Justin Welsh, Lara Acosta, Jasmin Alić, Tim Denning, Ben Meer, Daniel Murray, Edelman/LinkedIn 2025 report, Berlo competence/dynamism, Cialdini authority, Pornpitakpan, Graham's hierarchy, WikiDisputes) inform the reader/success/failure spec and are the judge's reasoning toolkit. They do NOT appear by name in criterion prose.

LinkedIn is structurally different from X: longer-form professional posts, dwell-and-substantive-comment as the unit of success rather than viral re-share, and a 2026 algorithm (360Brew + Depth Score + Topic Authority) that has converted credibility-coherence and comment substance from soft signals into algorithmic gates. The spec encodes these as outcome questions, not as feature checklists — the Phase 4 rollback at `c76f051` (commit `698e658`) is the load-bearing prior incident the criteria here are designed to resist re-creating.

This v1 synthesizes the v0 skeleton against four deep-research dispatches and one domain-research synthesis. Each elaboration earns its length against a documented failure mode: §1.5 LOCKED defends shape-drift Goodhart under 50-generation pressure; the "looks like slop but isn't" defense in §3 prevents false-positive over-suppression of legitimate operator broetry; LI-3's gestalt-stack reinforcement defends against single-tell whack-a-mole; LI-4's mechanism-families + reply-ladder CoT defend against bolted-on bait; LI-5's register-mismatch focus + structural_gate hoist defend against the AI-loop-most-likely failure mode (authority-voice register one stage above or below the author's seat). The 5-criterion ceiling holds — all AI-failure surfaces route to structural_gate, NOT to a documented 6th-criterion exception.

The v0 was structurally correct but under-anchored at multiple score-0 poles and under-specified at the structural_gate boundary. The v1 sharpens both without bloating: each criterion's body lands close to ~200 words, matching CI v3.3 depth. Looks-elaborate ≠ over-engineered.

---

## 1. Reader (LOCKED 2026-05-18)

A LinkedIn power-user reading the feed during their morning scroll or between meetings. Specifically one of four primary audience types:

- **Founder / decision-maker** at $1M–$50M ARR scanning for pattern-recognition from someone who solved the same problem; rewards specific numbers and named trade-offs; comments in 30–60-word ranges with a specific case
- **Mid-career B2B IC** (engineer, marketer, product, sales) looking for tactical insight to use in tomorrow's meeting; rewards step-by-step framing with concrete reproducible context; comments in 50–80-word ranges with implementation detail
- **Recruiter / talent** evaluating culture and trajectory signals; rewards consistent thought-leadership over time; comments in 30–50-word ranges on cultural fit
- **Industry peer** wanting a take they can argue with or build on; rewards a contrarian-but-defensible claim; comments in 60–80-word ranges with stance-taking

The reader is recognizably professional. They will not engage with broetry / hero-story / janitor-wisdom posts. They will leave a 30–80-word comment if the post contains a debatable claim, a genuine question requiring their experience, a numbered list with empty-slot affordance, or an honest-disagreement signal. They will not engage with AI-slop tells when the gestalt stack triggers (≥2 of: em-dash density >1.0/100 words, template-phrase opener, symmetrical-bullet rhythm, P.S.↓ closer, affective flatness).

**Secondary reader — the algorithm.** Per Van Der Blom 2025/26 *Algorithm InSights* and the 360Brew rewrite: 0–3s dwell gets 1.2% engagement and capped distribution; 61+s dwell gets 15.6% engagement and full second/third-degree fanout. Comments are weighted ~15× a like but only count when they exceed ~10 words (ideal band 30–80). 90-min golden-hour velocity determines ~70% of total reach. Engagement-bait CTAs are now actively suppressed (~60% distribution penalty once classifier triggers). Topic Authority cross-references claimed expertise against published corpus; topic-consistent authors see up to 78% higher distribution on in-lane content. The algorithm is reader, not target — the judge tests reader-effects, not algorithm-feature presence.

**Substitute readers the same post should also serve:** an early-stage founder at a DTC e-commerce or marketplaces business; a B2B SaaS operator at any stage; a fintech or regulated-finance operator posting compliance-or-product takes; a hospitality or retail owner-operator with a category POV; an agency principal at a small-to-mid services firm; an angel or VC sharing thesis updates; a senior researcher at an AI lab or scientific organization sharing one specific finding.

The Welsh / Acosta / Alić / Denning / Meer creator-archetype reference set in this spec exists because those operators have published explicit playbooks the literature builds on. They are **not** the architectural target — they are concrete anchors. The spec is designed to generalize to tech-savvy founder / early-co clients across verticals (gofreddy is a generic AI-native agency, not a creator-economy shop). First-cohort overfitting is an explicit risk to monitor (see §8).

NOT the reader: cringe-tagged engagement-farmers; spam accounts; the author's first-degree network alone (golden-hour seed, not the goal); engagement-pod participants; AI-generated comment bots (now filtered by LinkedIn mid-2025+).

---

## 1.5 Artifact shape (LOCKED 2026-05-18)

**The lane produces ONE post format: a LinkedIn text post, 600–2,000 characters, single-post or short-thread (2–3 connected posts max).** Locked because shape-drift Goodhart is a documented failure mode in evolution loops: under 50-generation selection pressure, the workflow learns that carousel-shaped outputs score well on LI-2 (insight delivery) because swipe-completion is easier to manufacture than scroll-completion, while video-shaped outputs score well on LI-3 (voice) because affect is harder to detect in spoken delivery, producing Frankenstein artifact mixes that don't serve any coherent reader. The lock prevents this.

**Form factor:**
- 600–2,000 characters total (text-post sweet spot per Socialinsider 2026; below 600 reads as throwaway, above 2,000 hits fatigue ceiling)
- Trailer at ~210 chars / first 3 lines, above the "...more" cut
- Single-post or short-thread (2–3 connected posts max), text-native
- Variable paragraph cadence (not symmetrical broetry, not blog-essay continuous prose)

**Out of scope shapes (the lane will NOT produce these):**
- Document carousel (different artifact; swipe-completion mechanics; ≥4 slides; handled by a future `linkedin_carousel` lane if scoped)
- Native video (different artifact; watch-completion mechanics; out of scope for v1)
- LinkedIn newsletter post (separated distribution surface; subscriber audience; Depth Score computed independently)
- LinkedIn article (long-form surface, different reader expectation)
- LinkedIn poll (different comment dynamics; ~4.0% engagement when options non-trivial; out of scope for v1)

**Why one shape:** the v1 Reader spec (B2B professional power-user) and Success spec (dwell + 30–80-word comment within 90-min golden hour) point unambiguously to text-post form factor. LI-1 (trailer earns the cut click) presumes a text-post above-the-cut trailer; LI-4 (substantive comment-seed) presumes the per-comment NLP classifier scoring text-post comment threads. Carousels and videos have different dwell mechanics, different reader behaviors, and would require different judge criteria.

**Shape enforcement lives in `structural_gate`, NOT in the judge criteria.** The judge tests outcomes (LI-1..LI-5 below); the workflow's structural_gate tests artifact-shape conformance (character-count band, trailer cut position, line-break density cap, format detection). Per design guide §11.1, this preserves the outcome-question-not-feature-check discipline at the judge layer while still defending against shape-drift.

**Empirical validation scope.** The text-post form factor is research-grounded against current first-cohort fixtures (small-to-mid B2B SaaS, AI labs, legal services, healthcare practices). When fixtures from new verticals or new shapes appear (DTC e-commerce founder takes, fintech-compliance posts, hospitality owner-operator content), re-validate the form factor — different verticals may favor different mid-post structures (DTC may favor numbered-list-with-photo claims; fintech may favor compliance-context-then-claim). The §1.5 lock is the text-post default; lane scope may expand or sibling-fork (carousel, video, newsletter) as the client mix evolves.

---

## 2. Success — what the reader DOES (LOCKED 2026-05-18)

After ~3 seconds the relevant professional reader clicks "...more" past the trailer cut. After 30+ seconds of dwell they take ONE of three concrete actions: (a) leave a substantive 30–80-word comment, (b) save the post for later reference, or (c) DM the author (the highest-credibility signal — they thought it was worth a private follow-up). The post earns ≥3 substantive comments in the 90-min golden hour, triggering fanout to second- and third-degree readers via the Depth Score multiplier. Profile-click follow-through is the secondary credibility signal — the reader clicks the byline to read more from the same author.

The reader treats the post as credible thought leadership coherent with the author's visible professional context (Edelman/LinkedIn 2025: 73% of B2B decision-makers cite consistent thought leadership as a trust signal — the operative word is *consistent*). The post advances the reader's thinking — gives them pattern-recognition, framing, or a specific worked example they did not arrive with. The post passes the Tim Denning litmus: if the author's name were stripped, their closest professional contact could still recognize the post as theirs.

**Sleep test:** if the reader saw the post in the morning and slept on it overnight, they could still articulate the central insight to a colleague the next day — the substance survives 24h, not just the surface.

World-class real-world exemplars — used as quality anchors, NOT as templates to copy:

**Ceiling (cross-archetype):**
- **Trailer-meat-CTA discipline** (Welsh's published 2026 LinkedIn guide) — every line earns the next; trailer breaks scroll on line 1, the cut earns the click via line 2/3 specificity, the meat delivers ONE insight, the close is the strongest line not the weakest.
- **Specificity test** (Alić's 27 Proven LinkedIn Writing Tips) — if you swap one named entity, number, or moment for a generic placeholder and the post reads identically, it was too generic; the named anchor is load-bearing.
- **Honest-disagreement framing** (constructive-disagreement research, WikiDisputes / *I Beg to Differ*) — opener at DH4–DH5 (counter-argument with stated uncertainty), not DH0–DH2 (cheerleading, ad-hominem, tone) — the opener's stance sets the ceiling for the reply ladder.

**Achievable floor (practitioner-grade):**
- **Hook-rehook structure** (Acosta) — line 1 is the 8–10 word hook, line 2 is the bait-and-switch rehook that earns the cut, not a continuation.
- **Nine-sentence narrative** (Denning) — short paragraphs, three-sentences-per-paragraph cap, conversational cadence, one insight per post.
- **Four-story-types frame** (Meer) — Personal pivot / Business insight / Client win / Leadership belief — every strong post cleanly serves one of four shapes; ungrounded mixes read as opinion soup.

What ties these together: a specific named entity or moment that anchors the claim; trailer-payoff coherence so the cut click is earned not tricked; a single insight delivered with author-specific evidence; an organic comment-seed that doesn't bolt on a CTA; author-context register that matches the seat the author actually occupies.

---

## 3. Failure — mediocre and Goodhart-collapse (LOCKED 2026-05-18)

### 3a. Mediocre — five failure modes the judge must discriminate against

**Broetry and descendants.** Hero's-journey ("$7 in my bank account → 7-figure business" closing on a course pitch); airport-story / janitor-wisdom (fabricated stranger delivering a "profound" lesson, one of the most reliably AI-generated formats per cringe-literature surveys); humblebrag ("I'm so humbled to announce…" — Sezer/Norton/Gino 2018: humblebraggers are perceived as less likeable, less competent, less influential than direct braggarts); "I X for Y years. Here's what I learned" credential-opener-plus-generic-listicle. Engineered to extract emotion before a sale; the substance is interchangeable across authors.

**AI-slop signal stack** (gestalt, not single-tell). Em-dash density >1.0 per 100 words (the empirically AI-shaped band per Plagiarism Today June 2025 dataset; legitimate stylists run 0.2–0.4); template-phrase openers ("Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y"); P.S.↓ closers (~12% of GPT-4o LinkedIn outputs vs <1% of human posts); symmetrical bullet rhythm (coefficient-of-variation <0.15 in bullet length); broetry-line density ≥40% of total lines; "Stop X. Start Y." parallel-list compression; "Here are 7 lessons" listicle bloat; affective flatness — no specific surprise, anger, delight, or stake. None of these alone is slop; the gestalt is.

**Blog draft shoved into LinkedIn.** 1,500-word essay broken into LinkedIn paragraphs with no hook, no rehook, no payoff at the cut. Long-form belongs on the LinkedIn newsletter surface, not the post surface — the algorithm reads the trailer to decide reach, so an essay opening loses dwell before the body even gets read.

**Motivational platitude / generic career advice.** Posts that could have been written by any author in any industry — fails the Denning name-stripped test. Surface-engagement may be non-zero (cousins-and-coworkers like-clicks) but no fanout, no substantive comment, no profile-click compounding.

**Author-context register mismatch (the AI-loop-most-likely failure).** Series-A founder narrating Series-D scaling pain ("when you're scaling past 500 reps…"); VP-level confidence on IC-level topics (executive writing tactical subject-line detail with flattened seniority signal); junior IC writing CEO-stance market-positioning content without grounding. Pornpitakpan 2004 meta-analysis of 47 source-credibility studies: high-credibility sources are more persuasive than low-credibility, but the credibility–persuasion link **collapses when message content sits outside the source's expertise band**. The reader has been pattern-matching this for forty years; the AI optimizing for hook density and comment-seed strength will routinely violate it. This is the failure mode the Goodhart-collapse loop produces most readily.

### 3b. "Looks like slop but isn't" defense — false-positive over-suppression

Each broetry-family pattern has a legitimate-operator-voice analog the judge must NOT penalize. The slop signal is the gestalt stack, not any single tell.

- **Broetry one-sentence-per-line, used by real operators.** Justin Welsh's solopreneur posts use single-line paragraphs deliberately because his mobile-reading audience expects it and he's written 1,500+ posts in this register. The substance compounds across lines (each line earns the next); AI broetry restates (each line is a synonym for the previous).
- **Em-dash use from real operators.** English-prose stylists like Lara Acosta and Jasmin Alić use em-dashes at 0.2–0.4 per 100 words — well above human baseline, well below AI baseline. The em-dash on its own is a false-positive trap; threshold is >1.0/100 words.
- **"I X for Y years" used by real founders.** Tim Denning has built his audience on close variants of this opener with substantive author-specific content underneath. The shape alone is not slop; the test is whether LI-2 fires.
- **"Stop X. Start Y." used by real operators.** Direct, parallel, contrarian-positioning is a legitimate rhetorical mode. The test is whether X is a strawman or a real practice the reader is doing.
- **"Here are 7 lessons" used by real authors.** Numbered-list posts hit ~6.6% engagement per Socialinsider 2026. The test is whether the items are author-specific (each one a lived story) or interchangeable (each one a generic claim).
- **Algorithm-aware authors generally.** Welsh, Acosta, Alić, Denning, Meer openly publish hook + rehook + comment-seed + format-fit playbooks. The judge cannot penalize "algorithm-aware structure" as slop; it must penalize "algorithm-aware structure with no substance underneath."

### 3c. Goodhart-collapse — Phase 4 pathology + LI-specific AI-failure surfaces

**Phase 4 pathology (the historical Goodhart trap).** 50-generation evolution against a feature-checking judge produced exactly the pathology rolled back at `c76f051` (commit `698e658`). The workflow learns to slot-fill named surface markers — for LinkedIn this collapses to:

- Every post opens with a specific number or named-entity hook regardless of substance.
- Every post has a rehook in line 2 that bait-and-switches mechanically.
- Every post inserts a question at line 4 to "earn comments" — the question is grammatically a question but semantically a CTA.
- Every post replaces em-dashes with semicolons or single dashes (different surface tell, same gradeless prose).
- Every post namechecks a customer or anecdote whether load-bearing or pasted in.
- Every post has exactly 7–9 sentences (Denning's max) regardless of whether 4 or 12 would serve the insight.
- Every post closes with a numbered list with three items and one "open slot" for reader additions.

Result: a corpus that is structurally compliant, recognizable as templated within 3 seconds by a human reader, that the 2026 distinctiveness filter detects and downranks, and that the engagement-bait classifier suppresses regardless of account history. Posts score well on judge AND get muted on platform. The criteria below are designed to resist re-creating this AND to surface the new LI-specific AI-failure surfaces the rollback did not address.

**LI-specific AI-failure surfaces (route to structural_gate, NOT to a 6th criterion):**

- **Engagement-bait classifier suppression.** LinkedIn's 2026 NLP classifier flags posts with "comment YES if you agree," "type 1 if you agree," "tag a friend who needs this," "like for Part 2," "repost if you've felt this" — distribution suppression ~60% regardless of account history. ~10 regex patterns cover 90%+ of cases (per `x_engine/pipeline/slop_gate.py::LINKEDIN_BANNED_PHRASES`).
- **AI-slop deterministic floor.** P.S.↓ closer regex; "Stop X. Start Y." parallel; "I X for Y years" credential-opener; "Here are N lessons" listicle-bloat opener; template-phrase opener stack ("Let me explain why," etc.); whitespace inflation (4+ consecutive newlines); em-dash density >1.0/100 words; broetry-line density ≥40%; bullet-rhythm CV <0.15.
- **Author-context determinable slice.** Role-Topic Token Overlap Gate (~50 LOC, Jaccard or TF-IDF between author profile-surface tokens and post topic tokens; threshold ~0.2); Employer-Mention Validity Check (~30 LOC, "we"/"our team" / employer-name match against author's current employer field); Claim-vs-Recent-Activity Check (~80 LOC, temporal claim "I just launched X" / "We closed Y" must match author's last-30-day post history or activity).

These checks hoist ~40% of LI-5's surface and 100% of the engagement-bait/AI-slop deterministic surface out of the judge per OpenRubrics §1.2 (Hard Rules → structural_gate, Principles → judge). The judge sees the post only after structural_gate passes; what remains in the judge is the gestalt, the residual, the reader-effect prediction — which is irreducibly judge-side. **No 6th criterion is required**, because every LI-specific AI-failure surface either resolves to a deterministic check (route to structural_gate) or folds naturally into LI-3's voice-residual or LI-5's register-coherence outcome question.

Deterministic AI-detector classifier output (GPTZero / Originality.ai / Copyleaks) is NOT a hard gate — FPR 18–35% against authentic operator posts per Authoredup July 2025 makes detectors unfit as hard blocks. Surface classifier output as a soft signal in the judge rationale only if at all; do not block on it.

---

## 4. Criteria — outcome questions (5)

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

**Score 0 (no)** — Gestalt stack triggers: ≥2 co-occurring AI-tells from the list (em-dash density >1.0/100w, template-phrase opener stack, symmetrical-bullet rhythm with CV <0.15, P.S.↓ closer, broetry-line density ≥40%, affective flatness) AND no compensating voice markers. OR the post reads as affectively flat throughout — no specific surprise, no specific anger or delight, no specific stake, no internal self-correction, no named anchor. Cannot be distinguished from AI-default-neutral register.

**Score 0.5 (unknown)** — Single weak signal present (one em-dash in an otherwise human-cadenced post; one template-phrase opener with otherwise specific body) AND the artifact does not contain enough material to test for compensating voice markers. Emit 0.5 + "unknown" + the specific signal AND what compensating marker would have to be present to commit to 1.

**Required CoT:**
- Step 1a: Scan for the gestalt AI-tell stack — count how many of (em-dash density / template-phrase opener / symmetrical bullets / P.S.↓ closer / broetry-line density / affective flatness) trigger. Note: deterministic single-tell density gates have already run in structural_gate; the judge is scoring the residual.
- Step 1b: For each triggered signal, identify whether a compensating voice marker is present (named entity in body, marked affect, internal self-correction, specific anecdote tied to author's professional context).
- Step 2: Apply the three-signal substance test: (i) specificity in the body (not just the opener); (ii) at least one marked affective valence in the body (specific irritation, surprise, regret, delight, stake); (iii) internal-contradiction tolerance (self-correction or acknowledged limit).
- Step 3: Emit verdict + one-sentence justification naming the dominant tell or the dominant compensating marker.

Do not score: total post length, paragraph count, presence of any single punctuation mark in isolation, output of any AI-detector classifier (FPR 18–35% against real operators — surface only as soft signal if at all).

### LI-4 — Gives a real reader something substantive to comment on

**Outcome question (binary):**
Would the relevant professional reader leave a substantive 30–80 word comment because the post offers them an organic entry point — a debatable defensible claim, a genuine question requiring their experience, an enumerated frame with empty-slot affordance, or an honest-disagreement signal — rather than because a bolted-on CTA prompted them to react?

The negative version of this question is the reader-effect anchor: **the relevant professional reader leaves no substantive 30–80 word comment because the post invites no genuine entry point.**

**Score 1 (yes)** — The post organically offers at least one of four mechanism families: (a) a *debatable defensible claim* where the author has visible standing and the claim is grounded in specific evidence (reader can extend with their own case or push back with a counter-case); (b) a *genuine question requiring the reader's specific experience to answer* (not a rhetorical question dressed as a survey — the question cannot be answered without the reader's specific position); (c) a *numbered or enumerated frame with empty-slot affordance* (the list signals incompleteness, the reader's mental affordance is to contribute item N+1); (d) an *honest-disagreement signal* ("I think X — here's where I might be wrong; what am I missing?" — Graham's hierarchy DH4–DH5 counter-argument with stated uncertainty, not DH0–DH2 cheerleading/hostility/tone).

Example (do not optimize toward this): a post that stakes a specific position on a hiring trade-off the author lived ("We hired for raw IQ over domain experience and it cost us nine months — here's the specific moment I realized the trade-off and where I'd push back on my own argument"). Reader's reply ladder ceiling: substantive case-comparison from their own experience, not "agree!" cheerleading or "wrong, here's why" hostility. Note: *taking a contrarian position without defensible standing fails this criterion* — the standing is what enables Graham DH4–DH5 replies instead of DH0–DH2 reactions.

**Score 0 (no)** — Post is a closed monologue with no entry point for substantive contribution; OR a list of generic tips that closes the enumeration (no empty-slot affordance); OR a pure announcement; OR contrarian-for-its-own-sake (opener at DH0–DH2 rebuttal level, no defensible standing — reply ladder ceiling is cheerleading/hostility, not substantive engagement); OR list-padding (numbered list where slots are non-substantive filler); OR bolted-on (generic post with a "what do you think?" or "agree?" closer tacked on, where the body itself invites no comment).

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
/ talent; industry peer.

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

The post is the lane's locked artifact shape: a LinkedIn text post,
600–2,000 characters, single-post or short-thread (2–3 connected
posts max), with a trailer at ~210 chars / first 3 lines above the
"...more" cut. Carousels, videos, newsletters, articles, and polls
are out of scope.

Score each criterion independently with 0, 0.5, or 1 plus a
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
- **LI-3**: "Replace em-dashes with semicolons" or "swap one tell for another" doesn't pass — the judge tests the gestalt stack (≥2 co-occurring tells) AND the three-signal substance test (specificity in body, affective-marker presence, internal-contradiction tolerance), not single tells. Single-tell whack-a-mole is bounded by gestalt-stack scoring.
- **LI-4**: "Bolted-on 'what do you think?' closer" or "every post ends with a question" doesn't pass — the comment-seed must be organic to the post's central argument, and the judge predicts the reply-ladder ceiling from the opener's stance, not from surface tokens. Engagement-bait CTAs route to structural_gate as deterministic bait-string detection.
- **LI-5**: "Add 'as a founder' prefix to every post" or "name-drop the employer in every post" doesn't pass — the criterion tests the *implied vantage from the substance*, not from prefix tokens or name-drops. The Goodhart move (workflow learns to replicate the author's last-three-posts' register on every new post) is partially defended by reading for confidence calibration against the source_data seat; the residual defense is variance instrumentation per §11.5 of the design guide.

Workflow that learns to slot-fill each criterion still has to produce content with the right outcome to score 1. Slot-fill alone scores 0. The ensemble defense matters: LI-3 + LI-5 fire when LI-4 over-rotates toward bait-shaped posts; LI-2 + LI-5 fire when LI-1 over-rotates toward dramatic-but-empty trailers. No single criterion catches every over-optimization; the five-criterion set is the defense.

---

## 7. Verification — does the v1 spec conform to the design guide?

- §3 anchor format: binary 0/1 + 0.5 = unknown ✓
- §4 criterion shape: outcome question + behavioral score-0 + behavioral score-1 + hedged examples (with "do not optimize toward this" hedge per design guide §4) ✓
- §5 criterion count: **5 (within ≤5 ceiling, no documented exception)** — all LI-specific AI-failure surfaces (engagement-bait classifier, AI-slop deterministic floor, author-context determinable slice) route to structural_gate, not to a 6th criterion. No literature-documented LLM-specific failure surface in the LinkedIn lane requires a 6th criterion the other 5 cannot catch.
- §5 isolation: per-criterion rationale, no blending across criteria ✓
- §6 structured per-criterion CoT (3–4 steps each, evidence-before-score) ✓
- §7 reference-free: examples hedged with "do not optimize toward this"; no model-authored exemplars used as scoring anchors ✓
- §10 input sanitization: applied at the substrate layer per design guide §10, not encoded in rubric prose ✓
- §11 Goodhart-resistance verification (§6 above) ✓
- §13 specimen criterion template followed ✓

Length per criterion ≈ 200 words (matching CI v3.3's actual depth, which exceeds the design guide's 150-word target due to 3 examples / register-mismatch enumeration / four-mechanism-family enumeration — each elaboration absorbs against a documented failure mode). Total spec body ≈ 4700 words including §1.5 and §3 expansions. Matches CI v3.3 depth, does not exceed it.

---

## 8. Open questions (after research synthesis)

Reader / Artifact-shape / Success / Failure / 5 Criteria are LOCKED at v1. Remaining decisions:

1. **Three-pair redundancy check (urgent).** Per design guide §5, run pairwise correlation across re-runs of 5 fixtures × 5 criteria × 3 panel models = ~75 calls (~$30). Drop any criterion correlating >0.7 with another. Three pairs to check:
   - **LI-3 ↔ LI-5 (predict r = 0.4–0.6, keep both):** LI-3 tests human-vs-AI voice (gestalt AI-slop stack); LI-5 tests this-author's-seat-vs-some-other-seat (authority-voice register). A post can be high LI-3 (clearly human-written) and low LI-5 (human but in the wrong register for the author — junior ghosting a CEO badly). Conversely, a post can be low LI-3 (AI-slop) and high LI-5 (the AI happened to hit the right register). Dimensions are orthogonal under selection pressure even if correlated on current fixtures.
   - **LI-4 ↔ LI-2 (potential absorption candidate):** Insight-bearing posts tend to be more comment-inviting; predict r = 0.4–0.6 but not above 0.7 because the reader-effects are structurally distinct (*learned-something* vs *have-something-to-say*). If r > 0.7, LI-4 may absorb into LI-2 — but the algorithm's 2026 NLP classifier treats comment substance as a promotion gate, not a boost, so the criterion may need to survive even partial redundancy. Flag for empirical resolution.
   - **LI-3 ↔ LI-4 ↔ LI-5 covariance instrumentation:** under selection pressure, if LI-4 mean rises while LI-3 or LI-5 mean falls over 3 generations, the workflow is over-optimizing for comment-seed at the cost of voice or author-coherence (contrarian-for-its-own-sake, list-padding, register-pretending). That signal triggers redesign of the over-rotated criterion, not calibration. The covariance pattern across the three is the Goodhart early-warning per design guide §11.5.

2. **Variance instrumentation: deferred until Path 1 validates the pattern on CI.** Per design guide §11.5, track per-criterion variance per generation; flag any criterion whose variance grows monotonically over 3 generations or whose mean compresses toward the middle for redesign (not calibration). The Path 1 question (validate-CI-first vs Path 2 propagate-7-lanes-in-parallel) blocks live deployment of variance instrumentation for LI; do not instrument LI variance until the CI variance-monitoring pattern has been validated and the telemetry surface for the autoresearch loop has the pattern wired.

3. **Cold-start handling for LI-3 + LI-5.** When `source_data` lacks prior-author posts (new client, first post, no work-history surface), LI-3 and LI-5 lose their grounding anchor — LI-3 cannot test for compensating voice markers because there's no baseline author register; LI-5 cannot infer the author's seat. The `linkedin_engine v040 cold-start mutation` memory provides a structural precedent (`templates/linkedin_engine/skeleton-short_take.md` plus pre-ship checklist). The judge-side handling: pass a `source_data.author_context_known = false` flag to the judge that triggers LI-3 and LI-5 to emit 0.5 + "unknown" by default rather than scoring blind. Implementation deferred to lane wiring.

4. **`structural_gate` expansion (before spec ships to live workflows):** wire `x_engine/pipeline/slop_gate.py::check_full(text, exemplars_path, platform="linkedin")` into the linkedin_engine `structural_gate` callable (~5 LOC integration; em-dash check already correctly skipped for `platform="linkedin"`). Add:
   - **AI-slop deterministic floor (~40 LOC):** P.S.↓ closer regex; "Stop X. Start Y." parallel; "I X for Y years" credential-opener; "Here are N lessons" listicle-bloat opener (additions to `LINKEDIN_BANNED_PHRASES`).
   - **Three density-based gates (~30 LOC):** em-dash density >1.0/100 words flags; broetry-line density ≥40% flags; bullet-rhythm coefficient-of-variation <0.15 flags.
   - **Three author-context gates (~160 LOC):** Role-Topic Token Overlap Gate; Employer-Mention Validity Check; Claim-vs-Recent-Activity Check. Together hoist ~40% of LI-5's surface out of the judge.
   - **Shape-conformance checks (~30 LOC):** character-count band (600–2,000); trailer cut position at ~210 chars; line-break count cap (~15); format detection (text-post vs out-of-scope carousel/video/poll/article).
   - **Do NOT block on AI-detector classifier output:** FPR 18–35% against real operators (Authoredup July 2025); treat classifier output as soft signal in judge rationale if at all, never as hard gate.

5. **Vertical fixture coverage and first-cohort overfitting watch.** Currently have B2B SaaS / AI-lab / legal services / healthcare practice coverage in fixtures (Anthropic, DWF, Klinika, Perplexity). Build 2–3 fixtures per under-represented vertical (DTC e-commerce, fintech, hospitality, regulated finance, marketplaces, agency) before locking the criteria via empirical redundancy check. Re-validation trigger: any fixture from a vertical not in {B2B SaaS, AI-lab, legal services, healthcare practice} should prompt a quick re-validation pass on LI-2 (insight specificity may need vertical-specific anchors), LI-4 (comment-seed mechanism mix may differ — DTC may favor Mechanism C list-with-photos more heavily than B2B which favors Mechanism A debatable claims), and LI-5 (register conventions vary by vertical — fintech compliance posts have different authority-voice norms than B2B SaaS founder content).

6. **Propagation order to remaining 6 lanes.** Once LI v1 validates on real fixtures alongside CI v3.3, propagate the iterated pattern across the remaining 6 lanes: GEO → MON → MA → SB → X → site_engine. Each lane gets its own Step 1 spec + (optionally) lane-customized deep-research pattern — NOT a mechanical 4-question repeat. The LinkedIn-specific deep-research dispatches (Van Der Blom Depth, AI-slop LI-specific, author-context coherence, comment-seed quality) were chosen because they were the load-bearing per-axis failure modes for LI; other lanes have different load-bearing axes and will need different per-axis dispatches.

7. **First-cohort overfitting watch (continued).** The substance tests across LI-2 / LI-3 / LI-4 / LI-5 are anchored on the Welsh / Acosta / Alić / Denning / Meer / Murray / Bloom creator-archetype reference set. gofreddy is a generic AI-native agency targeting tech-savvy founder / early-co clients across verticals, NOT a creator-economy shop. As clients onboard from other archetypes (DTC operators, fintech operators, regulated-finance professionals, hospitality owner-operators, scientific researchers), some anchor patterns may not generalize. The mechanism families in LI-4 are likely robust across archetypes (debatable claim / genuine question / enumerated frame / honest disagreement are platform-physics not creator-archetype-physics); the voice and author-context anchors in LI-3 / LI-5 are more archetype-anchored and may need adjustment. Re-validate when client #5+ onboards from an under-represented vertical.
