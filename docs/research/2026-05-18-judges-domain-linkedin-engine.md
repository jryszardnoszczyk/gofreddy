---
date: 2026-05-18
type: research deliverable
status: complete
topic: domain research — linkedin_engine lane
parent: docs/rubrics/judge-design-guide.md
sibling: docs/research/2026-05-15-judges-domain-competitive.md
---

# Domain Research: What Makes an Excellent LinkedIn Post Draft (B2B, 2025–2026)

**Purpose:** Ground the `linkedin_engine` lane judge in published LinkedIn creator playbooks, the 2025–2026 algorithm literature, and named practitioner failure modes — not statistical properties or transferred meta-patterns from the X lane.
**Scope:** Synthesis of Richard Van Der Blom's *Algorithm InSights 2025/26* report, five named-creator frameworks (Justin Welsh, Lara Acosta, Jasmin Alić, Ben Meer, Tim Denning), the Edelman/LinkedIn *2025 B2B Thought Leadership Impact Report*, current format-performance benchmarks (Socialinsider, Authoredup, Metricool 2026 studies), and the practitioner literature on broetry / engagement-bait / humblebrag failure modes.

The LinkedIn surface is structurally distinct from X. The unit of success is not reach to a like-and-move-on audience — it is **dwell time and substantive comments from a self-selected professional reader**, which a 2026 algorithm called the "Depth Score" weighs above every other signal. Every other dimension of LinkedIn quality flows from this.

---

## 1. What Makes a LinkedIn Post Earn Dwell + Comment

The strongest convergence across the algorithm research and the named-practitioner playbooks is a single distinction: **a LinkedIn post that earns dwell and a substantive comment is one the reader recognises as having been written for a specific decision they face. A post that earns a like and a scroll is one the reader recognises as generic.** Justin Welsh's 5-12-3 rule (the hook works in 5 seconds, the value still holds at 12 months, the post repurposes across 3 platforms) and Tim Denning's "write like you talk; the point is connection, not polish" both encode the same prior. This is the foundational quality dimension. Every other dimension flows from it.

### Empirical patterns from posts that produced dwell + comment

**Pattern 1 — Dwell time is now the primary algorithmic signal.** Richard Van Der Blom's 2025/26 *Algorithm InSights* report measures the cliff directly: posts with 0–3 seconds of dwell time get a 1.2% engagement rate with limited distribution; posts with 61+ seconds get a 15.6% engagement rate with full distribution. The 2026 follow-up coverage (meet-lea, dataslayer, postiv) names this as the "Depth Score" — LinkedIn now ranks posts on how long readers actually engage, not whether they clicked or tapped. Comments are weighted 15× more than likes, but only comments **longer than 10 words and ideally 30–80 words** count for the Depth Score because shorter comments (e.g., "Great post!") provide zero semantic value to the NLP filter. The post must therefore earn extended attention from a real reader, not engineered surface reactions.

**Pattern 2 — The first three lines are the entire game.** Every practitioner converges on this. Justin Welsh: the trailer (everything above the "...more" cut) has two jobs — break scroll on line 1, make line 2/3 compelling enough to click "...more." Lara Acosta: hook is the first line at 8–10 words, second line is the **rehook** (her term) doing "bait-and-switch" to keep them past the cut. Jasmin Alić: hooks are 1-liners under 45 characters, and "if it isn't very specific, it's probably vague; specificity sells." The mechanism is identical to dwell-time optimisation: if the reader isn't past line three, the algorithm sees a 0–3 second dwell and downranks the post for everyone.

**Pattern 3 — Narrative-with-payoff outperforms framework-recitation.** Tim Denning's nine-sentence maximum with three sentences per paragraph + "stories outperform everything else" is the same prior the Edelman/LinkedIn *2025 B2B Thought Leadership Impact Report* arrives at from the buyer side: 73% of B2B decision-makers say thought leadership is more trustworthy than other marketing, and 7 in 10 are "very likely" to think more positively about organisations that consistently produce high-quality thought leadership. The post that earns dwell is one where the reader extracts a usable insight; the post that earns scroll is one that lists features of an insight without producing one.

**Pattern 4 — Golden Hour (first 60–90 min) determines ~70% of total reach.** The algorithm uses early engagement velocity from the author's first-degree network to decide whether to fan out to second- and third-degree readers. This has two design implications for a *draft*: (a) the post must be written so that a relevant first-degree reader has something concrete to comment on within the first hour; (b) "comment YES if you agree"-style CTAs no longer work — LinkedIn actively deprioritises engagement-bait CTAs as of 2025. The draft instead needs a built-in conversation-opener: a contrarian claim, a question that requires the reader's specific experience, or a numbered list where readers add their own item.

**Pattern 5 — Format-fit matters, but voice-fit matters more.** Socialinsider and Metricool 2026 benchmarks: documents/carousels generate 39% more reach and ~6.60% engagement (the highest of any format) for B2B SaaS and consulting; text posts hit 4.2% engagement but produce the deepest comment threads when the angle is debatable; video reach dropped 36% year-over-year in 2026 but still converts at ~2× text for personal-brand creators. The judge cannot treat format as a quality signal in isolation — the test is whether the chosen format matches the post's *job* (frameworks → carousel; debatable angle → text; personality/credibility → video).

**Pattern 6 — Audience-types matter, and they're not interchangeable.** The named reader is one of: **founder / decision-maker** (wants pattern-recognition from someone who's solved the same problem; rewards specific numbers and named trade-offs); **mid-career B2B professional / IC** (wants tactical insight they can use in tomorrow's meeting; rewards step-by-step framing); **recruiter / talent** (wants signal about culture, growth trajectory, or stance); **industry peer** (wants a take they can argue with or build on; rewards a contrarian-but-defensible claim). A post optimised for one audience-type rarely earns dwell from another. Daniel Murray's Marketing Millennials playbook is explicit: "Make the content about your audience. Never post links to your company's website or anything about your company."

### Dimensions practitioners cite

Synthesising across Van Der Blom, Welsh, Acosta, Alić, Meer, Denning, the Edelman report, and Socialinsider/Authoredup/Metricool 2026 benchmarks, the dimensions that genuinely separate dwell-and-comment posts from like-and-scroll posts are:

1. **Hook earns the "...more" click** (specificity, tension, or counterintuitive opener — never a generic platitude)
2. **The middle delivers a non-obvious insight** (the reader leaves with something they didn't know or hadn't framed that way before)
3. **The post is written FROM a specific author context** (the writer's lived professional position is visible, not generically swappable)
4. **There is something for a real reader to comment on substantively** (a debatable claim, a question that needs the reader's experience, a numbered list with room for additions)
5. **Voice is recognisably human** (no AI-tell stack — see §2)
6. **Format matches job** (carousel for frameworks, text for debate, video for credibility — not the inverse)
7. **The post stands on its own without a CTA-sale** (Tim Denning: "sell occasionally, not constantly")

---

## 2. Great vs Mediocre — Named Failure Modes

Named practitioners identify specific, recurring failure modes — not abstract criticisms.

**The "broetry" trope and its descendants** are the most concretely named LinkedIn failure mode in the literature. The term was coined by BuzzFeed in December 2017 (Mac, Fechter, *et al.*) — one-line paragraphs about overcoming a personal tragedy, opening with clickbait and closing with a cliché lesson, designed to game the early "read more" click signal. LinkedIn pinged the format in 2018 and the originator was eventually banned. The 2025–2026 descendants the cringe-literature names explicitly (workweek, Medium "LinkedIn Lunatics," Content Marketing Institute):

- **The Hero's Journey post.** "I had $7 in my bank account. Today my business does 7 figures." Almost always closes with a course pitch. Engineered to extract emotion before the sale.
- **The Airport Story / The Janitor Wisdom post.** "A janitor at LAX taught me everything I know about leadership." Fabricated or composite encounters where a stranger delivers a "profound" lesson. Cringe-tagged in the practitioner literature as one of the most reliably AI-generated formats.
- **The Humblebrag.** "I'm so humbled to announce..." Research consistently shows humblebraggers are perceived as less likeable, less competent, and less influential than direct braggarts — the format inverts its own goal.
- **The "Comment YES if you agree" engagement-bait CTA.** Now actively penalised by the 2025 algorithm; the platform's deprioritisation is the most-documented recent change.
- **The Inspirational-Quote-Out-of-Context post.** Famous quotes detached from their source attached to a generic "motivational" image.

**The AI-slop signal stack** is the second-most-named failure mode and the one that's grown sharpest since 2024. The TechRadar "Blade Runners of LinkedIn" piece, Plagiarism Today, and Cybernews all converge on the same diagnostic set:

- **The em-dash tell.** AI models use em dashes at roughly 10× the rate of human writers. The em dash alone is not proof — but in combination with the rest of the stack, it's load-bearing.
- **Generic transition phrases.** "Let me explain why," "Here's the kicker," "Here's the thing," "It's not just X — it's Y."
- **The "P.S. ↓ + arrow emoji" closer.** A tell that the post was generated with a CTA-template injected at the end.
- **Symmetrical list rhythm.** Every bullet identical length, identical syntactic shape — humans rarely write with that level of metrical regularity.
- **Vocabulary that's clunky, oddly formal, or industry-jargon-dense in the wrong register.** "Leverage," "synergy," "best-in-class" used straight rather than ironically.
- **Writing that's "oddly flat."** Plagiarism Today's framing: punctuation alone is a terrible AI detector; the real giveaway is affective absence — no surprise, no specific anger, no specific delight, no specific shame.

**The "blog draft shoved into LinkedIn" failure mode.** Daniel Murray, Tim Denning, and Jasmin Alić all name this independently: a 1,500-word essay broken into LinkedIn paragraphs with no hook, no rehook, no payoff at the cut. The fix is structural, not stylistic — LinkedIn rewards the trailer-meat-CTA shape because the algorithm reads the trailer to decide reach. Long-form belongs on the LinkedIn newsletter surface, not the post surface.

**The motivational-platitude / generic-career-advice failure mode.** Posts that could have been written by any author in any industry. Tim Denning's litmus test: "If you took your name off the post, would your closest professional contact still know it was yours?" If no, the post is generic and the algorithm sees a low-distinctiveness signal.

**Author-context mismatch.** A junior IC writing as if they were a CEO; a CEO writing as if they were a junior IC explaining career advice; a B2B SaaS founder posting motivational fitness content unrelated to their professional surface. The Edelman report makes the buyer-side cost explicit: 73% of B2B decision-makers treat thought leadership as a trust signal — but only if the post's claim is coherent with the author's visible professional context. Mismatch destroys trust faster than it builds it.

---

## 3. Industry Frameworks (Judge's Reasoning Toolkit)

These are the frameworks LinkedIn practitioners and B2B content strategists actually use. **Do not embed these in rubric prose** (per §11 of `docs/rubrics/judge-design-guide.md` — feature-name embedding drives Goodhart drift). They are the judge's reasoning toolkit only — read once, then test for the *outcome* the framework predicts, never the framework's surface markers.

### Justin Welsh — Trailer / Meat / CTA + 5-12-3 Rule
Welsh's contribution is the **scroll-architecture frame**: every line must earn the next line. The trailer (above the "...more" cut) has two jobs — break the scroll and make the cut compelling. The meat delivers a single insight. The CTA is optional and never the post's job. The 5-12-3 rule is his evergreen test: the hook works in 5 seconds, the value still holds at 12 months, and the post is repurposable across at least 3 platforms. The diagnostic question for a judge: **would a real reader click "...more" after the first three lines, and if so, does what's below them earn that click?**

### Lara Acosta — Hook + Rehook + SLAY
Acosta's distinctive contribution is the **rehook**: the second line is not the continuation of line 1; it's the bait-and-switch that keeps the reader past the cut. Her SLAY structure (Story → Lesson → Actionable advice → Your turn) is her version of the SLAP frame. The diagnostic: a post that opens with a hook but has no rehook reads as setup-without-payoff and burns dwell time. The 8–10 word first-line rule is the surface marker — the judge's question is **does the second line earn the third?**

### Jasmin Alić — Specificity Test
Alić's contribution is the **specificity filter**: "if it isn't very specific, it's probably vague; if it's written for everyone, it's meant for no one." His writing technique — opening drafts with "Dear son," and closing with "Love, Dad," then deleting both — is the surface ritual; the load-bearing principle is that specificity is the dominant predictor of dwell. The diagnostic: **swap one named entity, number, or moment in the post for a generic placeholder. If the post still reads identically, it was too generic to begin with.**

### Tim Denning — Nine-Sentence Form + Audience Ownership
Denning's nine-sentence-maximum / three-sentences-per-paragraph rule is the structural anchor; his "write like you talk" + "stories outperform everything else" is the voice anchor. The audience-ownership principle (every bio and CTA pointing toward a newsletter) is the strategic layer outside the post draft itself. The diagnostic: **does the post read like a human spoke it out loud, or like a content marketer wrote it down?**

### Ben Meer — Four Story Types + Hook/Rehook/Line/CTA
Meer's "four story types" frame — Personal pivot, Business insight, Client win, Leadership belief — gives the judge a categorical test: every strong LinkedIn post is recognisably one of these four shapes. Posts that fit none of these shapes typically read as ungrounded opinion or generic advice. The diagnostic: **which of the four story types does this post serve, and does it serve that type cleanly?**

### Van Der Blom — Depth Score / Algorithm Alignment
Van Der Blom's *Algorithm InSights 2025/26* is the empirical anchor for the entire frame. The Depth Score (dwell time as primary signal; comments-30–80-words as secondary; 90-minute golden hour for fanout) gives the judge the underlying physics of distribution. The diagnostic: **would this post earn 60+ seconds of dwell from a real reader, and does it give a real reader something substantive to comment on in the first 90 minutes?**

### Edelman / LinkedIn 2025 B2B Thought Leadership Report
The trust-and-conversion data: 73% of decision-makers treat thought leadership as a more trustworthy signal than other marketing; 7 in 10 are "very likely" to think more positively about organisations that consistently produce high-quality thought leadership. The diagnostic: **does this post advance the author's professional credibility with a specific decision-maker audience, or does it merely seek attention?**

### Format-Fit (Socialinsider / Authoredup / Metricool 2026)
The format-performance benchmarks are not a rubric — they're a job-fit checker. Carousels for frameworks (6.60% engagement, B2B SaaS / consulting); text for debate (deepest comment threads when angle is debatable); video for personality and credibility (lower reach, ~2× conversion vs text); polls and documents as supplementary surfaces. The diagnostic: **does the format the post chose match the job the post is doing?**

---

## 4. Proposed Judge Criteria (5 Outcome Questions)

Each criterion follows the judge-design-guide.md template: outcome question, binary 0/1 + 0.5 unknown, behavioral anchors, structured CoT. None embed framework names; all test for outcomes. Five criteria — judge-design-guide.md §5 caps at five; live floor expected at 3–4 after redundancy check.

### LI-A — Does the trailer earn the "...more" click?
**Outcome question:** After reading only the first three lines, would a relevant LinkedIn reader in the target professional context click "...more" — and would that click be earned rather than tricked?
**Why this is what experts evaluate:** Welsh's trailer/meat/CTA frame, Acosta's hook+rehook, Alić's 1-liner specificity filter, and Van Der Blom's dwell-cliff data all converge here. The first three lines decide 0–3s vs 61s+ dwell, which decides everything else.
**Score 1 (yes):** Lines 1–3 contain a specific entity, number, claim, or counterintuitive framing tied to the post's professional context. The reader after line 3 has a clear sense of what payoff sits below the cut and that payoff is coherent with the opener (no bait-and-switch).
**Score 0 (no):** Opener is a generic platitude, vague claim, motivational quote, or engagement-bait ("agree?") that would not earn a relevant professional reader's click. OR opener earns the click but the body below the cut is unrelated to the promise.
**Score 0.5 (unknown):** Post is single-paragraph with no clear cut point, OR the relevant professional reader cannot be inferred from the artifact.

### LI-B — Does the post deliver one non-obvious insight a real reader could use?
**Outcome question:** After reading the full post, would a relevant professional reader (founder, mid-career IC, sales leader, recruiter, or peer) leave with something they didn't already know, or with a framing they hadn't previously applied to their own work?
**Why this is what experts evaluate:** Denning's "stories outperform everything else"; Edelman's finding that 73% of B2B decision-makers treat thought leadership as a trust signal *when it advances their thinking*; Daniel Murray's "make the content about the audience." The post's job is reader-progress, not author-credentialing.
**Score 1 (yes):** The post contains at least one specific claim, number, framing, or worked example that gives the reader pattern-recognition they did not arrive with. The insight is non-generic — swapping in another author's name would not produce the same post.
**Score 0 (no):** Post recycles generic advice, lists conventional wisdom, or restates a widely-known framework without adding the author's specific evidence. Could have been written by any author in the field.
**Score 0.5 (unknown):** Post contains specific detail but the target reader's prior knowledge level cannot be inferred from the artifact.

### LI-C — Is the voice recognisably the author's, not the AI's?
**Outcome question:** If a colleague who knows the author read this post anonymously, would they recognise it as the author's writing — and would a stranger NOT mistake it for AI-generated content?
**Why this is what experts evaluate:** Denning's "write like you talk"; Alić's "if it feels like writing, rewrite it"; the practitioner literature on AI-slop tells (em-dashes at 10× human rate, "Let me explain why," "Here's the kicker," P.S.↓ closers, symmetrical bullet rhythm, oddly-flat affect). LinkedIn's 2026 algorithm is documented to actively deprioritise AI-generated comments and increasingly probable AI-generated posts.
**Score 1 (yes):** Post has specific voice markers — a sentence cadence, a turn of phrase, a moment of genuine surprise/anger/delight, an anecdote tied to the author's actual professional context. No AI-tell stack triggers (no em-dash overuse, no template phrases, no symmetrical bullets, no P.S.↓ closer).
**Score 0 (no):** Post triggers two or more AI-tell signals from the stack, OR reads as affectively flat with no specific voice markers, OR opens with template phrases ("Let me explain why," "Here's the kicker," etc.).
**Score 0.5 (unknown):** Single weak signal present (e.g., one em-dash in an otherwise human-cadenced post) — emit 0.5 with the specific signal named.

### LI-D — Does the post give a real reader something substantive to comment on?
**Outcome question:** Would a relevant professional reader, after reading, have a specific 30–80-word comment they want to leave — a disagreement they want to register, an experience they want to add, or a question they want to ask the author?
**Why this is what experts evaluate:** Van Der Blom's Depth Score (comments 30–80 words count for ranking; "Great post" comments don't). The 90-minute golden hour mechanism: the post must seed substantive first-degree comments fast or it never fans out. Engagement-bait CTAs ("comment YES if you agree") are explicitly penalised by the 2025/2026 algorithm.
**Score 1 (yes):** Post contains a debatable claim, an open question that requires the reader's specific experience, a numbered list with obvious room for additions, OR a contrarian-but-defensible angle. A specific comment shape is invited without an engagement-bait CTA.
**Score 0 (no):** Post is a closed monologue, a list of generic tips, or a pure announcement with no entry point for a substantive reader contribution. OR post relies on engagement-bait CTAs.
**Score 0.5 (unknown):** Post invites comment, but the target reader's domain knowledge required to comment substantively cannot be inferred from the artifact.

### LI-E — Does the post sit coherently in the author's professional context?
**Outcome question:** Does the post's claim, voice, and angle match the author's visible professional surface (role, company, stage, expertise) — such that a decision-maker reader would treat it as credible thought leadership rather than mismatched content?
**Why this is what experts evaluate:** The Edelman/LinkedIn 2025 report's central finding — thought leadership builds trust only when claim-source coherence is intact. Ben Meer's four story types (Personal pivot / Business insight / Client win / Leadership belief) all require author-context fit. The practitioner literature's "junior IC writing as a CEO / CEO writing junior-level career advice" failure mode.
**Score 1 (yes):** The claim, angle, and tone are coherent with what the author plausibly has standing to say. A specific decision-maker reader would treat the post as credible thought leadership from this specific author.
**Score 0 (no):** Post makes claims outside the author's plausible standing (e.g., motivational/spiritual content from a B2B SaaS founder unconnected to their professional surface; CEO-stance content from a junior IC without grounding), OR tone is mismatched (over-formal corporate voice from a personal-brand creator, over-casual personal voice from an executive on a regulated-industry topic).
**Score 0.5 (unknown):** Author's professional context cannot be inferred from the artifact alone — emit 0.5 + "unknown" + the specific context that would have to be present.

---

## 5. Sources Cited

**Algorithm research (primary):**
- Van der Blom, Richard. *Algorithm InSights Report 2025 / 2025-26.* The Loner Recruiter (2025-10 PDF mirror): https://thelonerecruiter.com/wp-content/uploads/2025/10/Mastering-the-LinkedIn-Algorithm-in-202526-.pdf and LinkedIn post: https://www.linkedin.com/pulse/algorithm-insights-report-2025-here-xdooc
- Botdog. "Everything You Need To Know About LinkedIn's Algorithm In 2025." https://www.botdog.co/blog-posts/linkedin-algorithm-report
- Authoredup. "How the LinkedIn Algorithm Works in 2025 [Data-Backed Facts]." https://authoredup.com/blog/linkedin-algorithm
- Meet-Lea. "LinkedIn Algorithm Explained 2026: Dwell Time, Comments." https://meet-lea.com/en/blog/linkedin-algorithm-explained
- Dataslayer. "LinkedIn Algorithm 2026: What Works Now (Documents, Newsletters, Video)." https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now
- Postiv AI. "Your Definitive Guide to the LinkedIn Algorithm 2026." https://postiv.ai/blog/linkedin-algorithm-2026
- LinkBoost. "LinkedIn Algorithm Changes 2026: Beat the Depth Score." https://blog.linkboost.co/linkedin-algorithm-changes-2026/
- Hootsuite. "How the LinkedIn algorithm works in 2025." https://blog.hootsuite.com/linkedin-algorithm/

**Creator playbooks (primary):**
- Welsh, Justin. "How to Grow on LinkedIn in 2026." https://www.justinwelsh.me/article/linkedin-guide-2026 and "Leverage is the solopreneur cheat code." https://www.justinwelsh.me/newsletter/leverage
- Acosta, Lara. SLAY framework + hook patterns: https://buldrr.com/the-acosta-linkedin-model/ and https://magicpost.in/blog/how-to-write-like-lara-acosta ; cool-story breakdown: https://cool-story.beehiiv.com/p/lara-acosta-slay-framework
- Alić, Jasmin. *27 Proven LinkedIn Writing Tips:* https://www.scribd.com/document/701462598/27-Proven-LinkedIn-Writing-Tips-by-Jasmin-Alic-1706131277 and Hey-Jay resources: https://www.hey-jay.com/resources ; The Futur conversation: https://www.thefutur.com/content/2025-linkedin-strategies-that-create-real-growth-w-jasmin-alic
- Denning, Tim. "My Best Tip for LinkedIn Growth — LinkedIn Language." https://timdenning.com/linkedin-language/ and "Your Path to 100,000 LinkedIn Views (Part 1)." https://timdenning.com/linkedin-lessons-part-1/
- Meer, Ben. Growth-in-Reverse profile + Creator Method: https://growthinreverse.com/ben-meer/ ; LinkedIn growth post: https://www.linkedin.com/posts/benmeer_the-system-to-accelerate-your-linkedin-growth-activity-7110232863584727040-LI9u
- Murray, Daniel. *The Marketing Millennials* content philosophy: https://growthinreverse.com/daniel-murray/ ; Chili Piper interview: https://www.chilipiper.com/podcast/how-daniel-murray-grew-the-marketing-millennials
- Bloom, Sahil. *Curiosity Chronicle* newsletter philosophy (newsletter-surface, not post-draft surface): https://www.sahilbloom.com/newsletter ; Growth-in-Reverse: https://growthinreverse.com/sahil-bloom/
- Robertson, Dakota. Growth Ghost playbook: https://www.growthghost.com/main and Beehiiv archive: https://dakota.beehiiv.com/p/land-first-ghostwriting-client

**B2B trust + format performance:**
- Edelman & LinkedIn. *2025 B2B Thought Leadership Impact Report.* https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report
- Socialinsider. "LinkedIn Organic Benchmarks 2026." https://www.socialinsider.io/social-media-benchmarks/linkedin
- Metricool. "LinkedIn Trends: 6 Strategy Insights from Our 2026 Study." https://metricool.com/linkedin-trends/
- Grow with Ghost. "LinkedIn Post Formats Ranked 2026." https://www.growwithghost.io/blog/linkedin-post-formats-ranked-text-vs-carousel-vs-video-vs-polls-2026/
- ContentIn. "LinkedIn Algorithm 2026: Format Strategy That Actually Works." https://contentin.io/blog/linkedin-algorithm-2025-the-complete-content-format-strategy-guide/
- Authoredup. "Best Performing Content on LinkedIn in 2026." https://authoredup.com/blog/best-performing-content-on-linkedin

**Failure-mode literature:**
- Mac, Ryan. "Why Are These Posts Taking Over Your LinkedIn Feed? Because They're Pure Broetry." *BuzzFeed News.* https://www.buzzfeednews.com/article/ryanmac/why-are-these-posts-taking-over-your-linkedin-feed-because
- Fenwick Media. "Broetry: Why is everyone suddenly writing in single line sentences on LinkedIn?" https://fenwick.media/rewild/magazine/dead-broets-society-behind-the-strange-story
- Content Marketing Institute. "Why You Should Avoid the Broetry Writing Trend." https://contentmarketinginstitute.com/social-media-content/why-you-should-avoid-the-broetry-writing-trend
- Workweek. "Why is LinkedIn so cringe?" https://workweek.com/2022/01/15/why-is-linkedin-so-cringe/
- DeepDive Platform. "LinkedIn Influencer Cringe: The LinkedIn Lunatics Phenomenon." https://www.deepdiveplatform.com/blogs/linkedin-influencer-cringe-the-linkedin-lunatics-phenomenon
- TechRadar. "Blade Runners of LinkedIn are hunting for replicants — one em dash at a time." https://www.techradar.com/computing/artificial-intelligence/blade-runners-of-linkedin-are-hunting-for-replicants-one-em-dash-at-a-time
- Cybernews. "The em dash dilemma — AI tell or human flourish?" https://cybernews.com/editorial/linkedin-em-dash-ai/
- Plagiarism Today. "Em Dashes, Hyphens and Spotting AI Writing." https://www.plagiarismtoday.com/2025/06/26/em-dashes-hyphens-and-spotting-ai-writing/

---

## Notes for Rubric Authors

1. **LI-A through LI-E map to the existing surface but reground in outcome questions.** Specifically: LI-A subsumes "hook quality"; LI-B subsumes "insight density / non-obvious payoff"; LI-C subsumes "voice authenticity / AI-detection"; LI-D subsumes "comment-seed quality / engagement-design"; LI-E subsumes "author-context coherence / credibility fit." None of these are feature checks — each tests for an outcome the algorithm or reader produces.

2. **One discipline the current surface does not name but the algorithm rewards:** the **comment-seed test** (LI-D) — does the post invite a 30–80-word comment, not just a click? This is now the load-bearing algorithm signal alongside dwell, and it is the dimension judges most often miss because it isn't visible in the artifact's surface — it's predicted from the artifact's stance.

3. **What to deliberately not encode** (per `judge-design-guide.md` §11): no specific hook templates, no "must include a question," no "minimum word count," no "must have a CTA." Length and structural facts route to `structural_gate`. The judge tests the reader-effect, never the artifact-shape. If the rubric drifts toward "does the post have X feature" — that drift is the Phase 4 pathology the guide names; redesign, do not calibrate.

4. **Real exemplars to anchor judge prose later** (do-not-optimise-toward, per guide §4): Justin Welsh's `7137428886270709760` solopreneur thread for LI-A/LI-B; Lara Acosta's "Hired a Gen-Z candidate without interviewing him" hook for LI-A; Jasmin Alić's "27 Proven LinkedIn Writing Tips" thread for LI-A/LI-D; the Edelman/LinkedIn report itself as canonical thought-leadership credibility-signal text for LI-E.

5. **Cross-lane drift watch:** the X-engine lane's `slop_gate` already encodes platform-aware AI-detection signals (per `project-x-engine-port-l0-pickup.md` memory). LinkedIn-specific signals (em-dash overuse, template-phrase stack, P.S.↓ closers, symmetrical-bullet rhythm) should live in `structural_gate` for the LinkedIn lane if they can be deterministically detected. LI-C in the judge then tests the *residual* — affective flatness, voice mismatch, generic register — that determinism cannot catch.
