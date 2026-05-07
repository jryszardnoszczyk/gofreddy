---
title: X-1..X-6 + LI-1..LI-6 Rubric 1/3/5 Anchor Prose — DRAFTS for L2
type: rubric-prose-drafts
status: drafts-for-jr-review
date: 2026-05-08
seeded_from: docs/plans/2026-05-07-001-x-engine-rubric-anchors.md
will_land_in: src/evaluation/rubrics.py (at L2 start, after F4 review)
---

# X-1..X-6 + LI-1..LI-6 — 1/3/5 Anchor Prose Drafts

These are the 12 prose blocks that will land in `src/evaluation/rubrics.py`
at L2 start, expanded from the 1-paragraph seeds in
`docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`. Mirror the format
of `_GEO_1`..`_GEO_8` (rubrics.py:47-300+): "Evaluate ... for ONE quality:"
opener → Score 1 anchor → Score 3 anchor → Score 5 anchor → "Provide your
reasoning ... then give your score." closer.

**Status:** drafts. Not committed to `rubrics.py`. JR reviews during the
14-day X-dogfood window (gate #1 + #2). At L2 start the approved prose
blocks lift directly into `_X_1`..`_X_6` + `_LI_1`..`_LI_6` Python string
literals.

**Format note:** rubrics.py uses triple-quoted strings with explicit `\\\\\n`
line continuations. The drafts below are presented as plain prose; the L2
move-step adds the Python wrapping.

---

## X-1 — Voice (first-person, opinionated, plain-language)

Evaluate this draft for ONE quality:
Does it read like JR — first-person, opinionated, with a plain-language
register accessible to a non-engineer founder or marketer? Jargon
without inline plain-English context caps this dimension.

Score 1: The draft reads like generic content marketing or AI-generated
copy. The voice is third-person, hedged, or aggregated ("teams should...",
"organizations need...", "studies show..."). Or: jargon is present without
plain-English context — terms like "MCP", "tool-use", "context window",
"agent harness" appear unexplained. AUTOMATIC ≤4 if 2+ unexplained
technical terms; AUTOMATIC ≤6 if any jargon appears without a follow-up
plain-English phrase. The draft fails the "could a marketer read this and
nod" test.

Score 3: The voice is mostly first-person and opinionated, but slips into
generic register in places — passive constructions, "people often think",
or third-person aggregations break the JR voice in 1-2 spots. Jargon, when
present, is mostly explained but at least one term assumes prior knowledge.
The draft would read fine to a technical audience but loses non-engineer
readers in the dense sections.

Score 5: Every sentence carries JR's voice — first-person, specific to JR's
lived experience, opinionated. Plain language throughout: when a technical
term appears it gets an inline plain-English follow-up ("MCP servers — the
plumbing that lets Claude read your inbox"). A non-engineer founder reads
the whole draft without bouncing on jargon. The opinion is sharp, not
hedged ("most marketing teams overcomplicate this" not "some teams may
find it complex").

Provide your reasoning, cite specific evidence from the draft, then give
your score.

---

## X-2 — Factual specificity (lived-work hard floor)

Evaluate this draft for ONE quality:
Are factual claims grounded? SOURCE claims (statistics, quotes from
named sources, public datapoints) must be verifiable against the angle's
`source_text`. INTERPRETIVE claims framed as JR's view ("my read",
"in our work") are acceptable. Specific lived-work claims about clients
or projects ("when I built X for Y") are subject to a HARD FLOOR.

Score 1: The draft contains specific factual claims that contradict
`source_text`, or specific lived-work claims with named entities that do
NOT appear in `programs/references/voice.md` (the shared substrate
loaded into source_data). Examples: "when I built the agent stack for
[fictional client]" or "our team's deployment to 50 enterprises" without
the entity in voice.md. **HARD FLOOR:** any first-person specific
lived-work claim referencing an entity not in voice.md scores ≤3, no
matter how good the draft is otherwise.

Score 3: SOURCE claims are mostly verifiable; one or two are stretched
or unsupported. INTERPRETIVE claims are present but not always framed
as opinion — some sound declarative when they're really JR's read. No
HARD-FLOOR violation but specificity feels thin in places.

Score 5: SOURCE claims trace cleanly to `source_text` or named public
datapoints. INTERPRETIVE claims are explicitly framed as JR's view.
Lived-work claims either avoid named-entity specificity ("a recent
client engagement") or name entities present in voice.md. The draft
wears its specificity confidently — a fact-checker could trace every
claim or flag it as JR's opinion in under 2 minutes.

Provide your reasoning, cite specific evidence from the draft, then give
your score.

---

## X-3 — Hook strength (bracket-aware)

Evaluate this draft for ONE quality:
Does the opening earn the next line? On X, the first 8-12 words carry the
draft. SHARP brackets (250-300 chars) live or die on the punch in those
words. BUILD (500-900) and CASE-STUDY (1000-1500) drafts must beat the
"show more" cutoff with their first 1-2 sentences. The bracket declared
in frontmatter sets the bar.

Score 1: Generic opener — "Most people don't realize", rhetorical
question hooks ("Have you ever wondered?"), thread announcements ("a
🧵"), or pure topic statements ("AI marketing is changing"). For SHARP:
no punch line. For BUILD/CASE-STUDY: the first sentence reads like
table-of-contents prose, no specific claim or tension. The draft fails
to earn line two; a reader scrolls past.

Score 3: The hook works mechanically but feels formulaic — a "hot
take:" framing, a contrarian-but-bland opener ("Most teams get X
wrong:"), or a specific number without context ("3 things I learned").
For SHARP: it lands but barely. For BUILD/CASE-STUDY: the first 1-2
sentences declare what the post is about but don't pull the reader into
specific tension. A reader might read more out of genre habit, not
because the hook compelled it.

Score 5: The hook has compression and specificity. SHARP earns 5 with
one sharp claim+support pair in the first 12 words ("47 hours of agent
debugging led to one config change"). BUILD/CASE-STUDY earns 5 when
the first 1-2 sentences land a specific scenario, named tension, or
counter-intuitive specific number that makes the rest unavoidable to
read. No generic openers, no rhetorical-question crutches.

Provide your reasoning, cite specific evidence from the draft, then give
your score.

---

## X-4 — Slop-freeness (post deterministic gate)

Evaluate this draft for ONE quality:
Zero AI-tells. The deterministic regex floor in `slop_gate.py` is the
hard fail; this dimension judges what slips through. Even when no
banned phrase fires, the draft can still feel AI-generated through
parallel structures, formulaic transitions, or cadence patterns.

Score 1: Multiple AI-tell patterns slip through the regex. Examples:
parallel "It's not X. It's Y." structures, "Here's what I learned:"
listicle openers (caught downstream of the regex), em-dash-heavy
sentence rhythms, paragraph-paragraph transitions that read as
auto-generated ("Now,", "So,", "Furthermore,"). Or: hedged-confident
voice ("It might be worth considering that..."). The reader senses
the draft was machine-written even if no banned phrase fires.

Score 3: One or two patterns slip through — a parallel construction
in the middle of the draft, an "it's important to note" hedge, an
em-dash-rhythm sentence. The voice is mostly JR but slips into AI
patterns in 1-2 spots. A discerning reader would catch the seam.

Score 5: Zero AI-tells. Voice is consistent throughout. Sentence
rhythms vary naturally — not the rhythmic 3-clause cadence common in
LLM output. Transitions are JR's actual register ("but", "and so",
"which means") not the formal "Furthermore," "Moreover". The draft
reads like JR typed it.

Provide your reasoning, cite specific evidence from the draft, then give
your score.

---

## X-5 — Structural richness (bracket-aware)

Evaluate this draft for ONE quality:
Does the structure earn its length? The declared `length_bracket`
(SHARP / BUILD / CASE-STUDY) sets a different bar. SHARP rewards
compression; BUILD rewards structural pivot + substance; CASE-STUDY
rewards narrative depth.

Score 1: Pad-to-length writing. Filler sentences ("In this thread,
we'll explore..."), unnecessary reframings, or stretching a SHARP
idea into BUILD length. For SHARP: the punch is there but surrounded
by 50 chars of padding. For BUILD: 3-bullet listicle with no
authority anchor or outcome metric. For CASE-STUDY: monotonic
narrative without sensory detail or numbers timeline. Length feels
filled, not earned.

Score 3: The structure works for the bracket but doesn't elevate.
SHARP: one sharp claim, support is OK but generic. BUILD: prose
intro + 2-3 substantive bullets, but the bullets read flat without
specific numbers or named tools. CASE-STUDY: narrative with some
specifics but missing the implication close. The draft is solid but
forgettable.

Score 5: Bracket-aware structural mastery. SHARP (10 score in
companion): one sharp claim + tight support pair, every word earns
position. BUILD: prose intro + structural pivot + 3-5 substantive
bullets + authority anchor + outcome metric. CASE-STUDY:
multi-paragraph narrative + sensory detail + numbers timeline +
implication close. Structure serves the argument; cutting any
element would weaken it. Pad-to-length = ≤4 hard cap.

Provide your reasoning, cite specific evidence from the draft, then give
your score.

---

## X-6 — Cross-item (cohort diversity; cross-item)

Evaluate this DRAFT COHORT for ONE quality:
Across all drafts in this session's `drafts/` directory, do they spread
across distinct primary differentiators, sources, and hook archetypes?
Or do multiple drafts use the same opener pattern, cite the same
source_url, or lean on the same `voice_pillar`? This is a cross-item
dimension — score the cohort as a whole, not individual drafts. Use the
geometric mean of per-draft cohort-fit scores.

Score 1: Multiple drafts (3+) use the same primary differentiator,
same source_url, or same hook archetype. Pillar diversity collapses
to 1-2 pillars when the variant's `voice_pillars` metadata supports
4+. The cohort reads as variations of one draft rather than 5
distinct drafts.

Score 3: Some diversity — 2-3 drafts share a primary differentiator
or hook pattern, but the cohort spreads across 3-4 distinct angles.
A reader scanning the cohort would see breadth but also notice
concentrations.

Score 5: Each draft uses a distinct primary differentiator, source,
and hook archetype. The cohort spreads across the full range of
`voice_pillars` declared in angle metadata. No two drafts could be
swapped without losing variant value. Cross-item diversity feels
intentional, not accidental.

Provide your reasoning, cite specific evidence from the cohort, then
give your score.

---

## LI-1 — LinkedIn voice (story-led, professional register)

Evaluate this draft for ONE quality:
Does it read like JR's LinkedIn voice — first-person, story-led, with
a professional register accessible to B2B buyers, agency operators,
and C-suite? The lever is **thoughtful authority**, not contrarian
punch. Plain language is still required (jargon caps voice score),
but tone is noticeably less contrarian than X.

Score 1: The draft reads as bait-y, hot-take-y, or "Twitter-translated."
Contrarian openers ("Most marketers don't realize..."), aggressive
declaratives, or X-style sub-300-char sharps. AUTOMATIC ≤4 if the
draft reads as Twitter-translated; AUTOMATIC ≤6 if jargon appears
without a plain-English follow-up. LinkedIn buyers do not want hot
takes; they want patterns + framing they can use.

Score 3: The voice is mostly LinkedIn-appropriate but slips — a
contrarian declaration in paragraph 2, a sub-200-char aggressive
sentence amid otherwise story-led prose, or jargon-density that
buyers tolerate but don't enjoy. The draft would post but feels
slightly off-genre.

Score 5: Throughout: thoughtful authority. First-person, story-led,
specific lived-work register. Plain language — jargon, where present,
gets the inline plain-English follow-up. Tone is "I've spent a year
on this and here's what I noticed" not "you're doing this wrong." The
draft reads as a B2B-buyer-friendly version of the same insight that
might appear sharper on X.

Provide your reasoning, cite specific evidence from the draft, then
give your score.

---

## LI-2 — Factual specificity (LinkedIn audience punishes vague claims harder)

Evaluate this draft for ONE quality:
Are factual claims grounded? Same SOURCE/INTERPRETIVE split as X-2.
**HARD FLOOR:** lived-work claims REQUIRE the named entity to appear
in `programs/references/voice.md`. **LinkedIn-specific cap:** any
first-person specific claim ("we shipped X") that does not name the
client or project caps the dimension at 7 — LinkedIn audiences punish
vague specificity harder than X audiences do.

Score 1: Specific factual claims contradict `source_text`, or
lived-work claims name entities not in voice.md. **HARD FLOOR:** any
unnamed-entity lived-work claim scores ≤3. Same regex floor as X-2;
LinkedIn audience adds the additional "vague specific" penalty.

Score 3: SOURCE claims are mostly verifiable; INTERPRETIVE claims
are framed as opinion. Lived-work specifics hover near the cap-at-7
threshold — "we" or "our team" without a named entity, but no
HARD-FLOOR violation. Specificity is OK but the draft would benefit
from one more named anchor.

Score 5: SOURCE claims trace cleanly. INTERPRETIVE claims framed as
JR's view. Lived-work claims either name entities present in voice.md
or stay general ("a recent engagement"). LinkedIn buyers can
fact-check the draft in under 2 minutes and either verify or place
on JR's opinion side.

Provide your reasoning, cite specific evidence from the draft, then
give your score.

---

## LI-3 — Hook strength (story-led, NOT contrarian)

Evaluate this draft for ONE quality:
Does the opening earn the next line? LinkedIn rewards story-led openings
("Last quarter I learned X.") + concrete-result openings ("47 hours of
agent debugging led to one config change.") + before-the-fold tension.
The first 1-2 sentences must beat the show-more cutoff at ~210 chars on
web LinkedIn. **PUNISHES contrarian hot-takes that work on X** ("Most
marketers don't realize..." → ≤3 on LinkedIn even though it works on X).

Score 1: Contrarian declarative opener, aggressive sub-200-char hook
borrowed from X register, or generic LinkedIn bait ("Are you ready
for...", "Let's talk about..."). The first sentence reads as bait;
LinkedIn audience scrolls or hides. Engagement-bait closes ("Thoughts?
👇") amplify the bait register.

Score 3: The hook works but feels formulaic — a concrete-number
opener that lands but lacks story specificity, or a story-led
sentence that doesn't earn the show-more cutoff. The draft might
get scrolled past after the first 2-3 lines.

Score 5: Story-led opening with specific concrete grounding ("Last
quarter we rebuilt our agent stack and shipped 5 features in two
weeks. Here's the one decision that mattered."). The first 1-2
sentences earn line two; before-the-fold tension is real. The hook
identifies JR as someone the reader should listen to without
declaring it.

Provide your reasoning, cite specific evidence from the draft, then
give your score.

---

## LI-4 — Slop-freeness (LinkedIn-specific tells)

Evaluate this draft for ONE quality:
Zero AI-tells AND zero LinkedIn-AI-tells. The deterministic regex
floor in `slop_gate.py --platform linkedin` is the hard fail; this
dimension judges what slips through. LinkedIn-specific tells include
"Game-changer.", "Here's what I learned." (alone-line close),
"Thoughts? 👇", "Agree? 🤔", excessive line breaks for whitespace
inflation, fake "Hot take:" framings.

Score 1: Multiple LinkedIn-AI-tells slip through. Examples: "Here's
what I learned" alone-line close, engagement-bait emoji prompts,
4+ consecutive newlines for whitespace padding, fake hot-take
framings, "thought-leadership" cadence patterns ("Three takeaways:",
"What I've learned:"). The draft reads as LinkedIn-AI even if no
generic banned phrase fires.

Score 3: One or two LinkedIn-AI patterns slip through — a "thoughts?"
close, one whitespace-inflation paragraph break, or a single
formulaic transition ("And here's the thing:"). The voice is
mostly JR but the LinkedIn-AI rhythm bleeds in.

Score 5: Zero AI-tells, zero LinkedIn-AI-tells. Voice consistent.
Whitespace serves paragraph structure, not visual padding. Closes
land on JR's actual cadence, not an engagement prompt. The draft
reads like JR typed it on LinkedIn, not an AI optimizing for
LinkedIn's algorithm.

Provide your reasoning, cite specific evidence from the draft, then
give your score.

---

## LI-5 — Structural richness + hashtag-count quality

Evaluate this draft for ONE quality:
Does the structure earn its length, AND does the hashtag count fit the
LinkedIn distribution model? The declared `length_bracket` (SHORT_TAKE
/ THOUGHT_LEADER / CASE_STUDY) sets a structure bar. Hashtag count is
a separate component: 3-5 targeted hashtags = ideal (no penalty); 1-2
= suboptimal (cap dimension at 7); 0 = ≤4 (zero-tag posts get less
LinkedIn distribution). Spam guardrail (count > 5) is enforced
deterministically by structural_gate; never reaches this rubric.

Score 1: Pad-to-length OR zero hashtags. SHORT_TAKE (500-900) padded
to length with filler. THOUGHT_LEADER (1500-2500) with 3-bullet
listicle and no implication close. CASE_STUDY (2500-3000) without
named characters or numbers timeline. Or: 0 hashtags (LinkedIn
distribution penalty makes 0-tag drafts hard to ship). Or:
"motivational poster" generality — "I'm sharing this because..."
without specific lived-work substance.

Score 3: Structure works mechanically for the bracket. Hashtag count
in [1, 2] range — suboptimal but not zero. Bullets are present in
THOUGHT_LEADER format but lack specificity. CASE_STUDY narrative
hits beats but feels rote. Cap at 7 due to hashtag-count.

Score 5: Bracket-aware structural mastery + 3-5 targeted hashtags.
SHORT_TAKE: story-opening + 1 substantive paragraph + closing
thought + 3-5 hashtags. THOUGHT_LEADER: story → frame → 3-5
numbered points → implication close + 3-5 hashtags. CASE_STUDY:
multi-paragraph narrative + numbers timeline + named characters +
implication close + 3-5 hashtags. Hashtags map to JR's brand pillars,
not generic ("#marketing" alone = ≤4).

Provide your reasoning, cite specific evidence from the draft, then
give your score.

---

## LI-6 — Cross-item (narrative archetype variance; cross-item)

Evaluate this DRAFT COHORT for ONE quality:
Across all drafts in this session's `drafts/` directory, does the
narrative archetype vary (story-led vs lesson-led vs comparison vs
case-study)? Do the drafts spread across `voice_pillars` listed in
angle metadata? **PUNISHES same-tone-same-format streaks.** This is
a cross-item dimension — score the cohort as a whole using the
geometric mean of per-draft cohort-fit scores. **NOTE:** hashtag-set
diversity is NOT scored here; same-pillar drafts may legitimately
share signature 3-tag combos for brand consistency. Per-draft hashtag
count ∈ [3,5] is enforced deterministically by structural_gate.

Score 1: All drafts use the same narrative archetype (e.g., 3
"Last quarter I learned" story-led drafts back-to-back, or 3
listicle-style THOUGHT_LEADER drafts). Pillar diversity collapses
to 1-2 pillars when the variant's `voice_pillars` metadata supports
4+. Same-tone-same-format streak is obvious.

Score 3: Some archetype variation — 2 distinct archetypes across the
cohort (e.g., 1 story-led + 2 lesson-led + 0 comparison). Pillar
spread is partial. The cohort feels narrower than the metadata
allows.

Score 5: Each draft uses a distinct narrative archetype across the
4 LinkedIn-relevant categories (story-led, lesson-led, comparison,
case-study). Pillar spread matches the variant's `voice_pillars`
metadata. Cross-archetype variance feels intentional — a reader
scrolling the cohort experiences range, not repetition.

Provide your reasoning, cite specific evidence from the cohort, then
give your score.

---

## L2 move-step

When L2 starts and these prose blocks have JR's F4 sign-off:

1. Move each block above into `src/evaluation/rubrics.py` as Python
   string literals (`_X_1 = """..."""`, etc.).
2. Register in the `RUBRICS` dict:
   ```python
   "X-1": RubricTemplate("X-1", "x_engine", "gradient", _X_1),
   ...
   "X-6": RubricTemplate("X-6", "x_engine", "gradient", _X_6, is_cross_item=True),
   "LI-1": RubricTemplate("LI-1", "linkedin_engine", "gradient", _LI_1),
   ...
   "LI-6": RubricTemplate("LI-6", "linkedin_engine", "gradient", _LI_6, is_cross_item=True),
   ```
3. Bump `assert len(RUBRICS) == 32` → `assert len(RUBRICS) == 44`.
4. Add `_LANE_SPECS` entries for `x_engine` + `linkedin_engine` lookup
   (per the existing pattern at rubrics.py:949-1017).
5. Run `pytest tests/autoresearch/test_rubrics.py -q` to verify the
   load-bearing assertions still pass.

All 12 are `scoring_type='gradient'` per Round-7 Sub-2 (no checklist
sub-questions in v1; v2 lever for any dimension that proves better as
binary YES/NO).

X-6 + LI-6 set `is_cross_item=True` (mirroring GEO-6 + SB-8 pattern).

## Open questions for JR's F4 review

For each of X-1..X-6 + LI-1..LI-6, score against:
- 10-20 reference posts you'd want the lane to emulate (X for X-N;
  LinkedIn for LI-N)
- 5 external triangulation posts NOT in the emulation set (Round-6
  #18 single-rater bias check)

If any anchor scores ≤6 in either group: rewrite this draft before L2
prose-block authoring locks them. The companion file
`docs/plans/2026-05-07-001-x-engine-rubric-anchors.md` carries the
1-paragraph anchor seeds; this file expands to 1/3/5 format. Both should
stay aligned — substantive edits to one need a sweep through the other.
