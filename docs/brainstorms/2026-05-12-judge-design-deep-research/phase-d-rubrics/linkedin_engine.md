---
date: 2026-05-12
phase: D
lane: linkedin_engine
status: spec — implementer-ready; LI-11 trigger-phrase content gated on Resolve-Before-Planning #2 (legal review per byline)
inputs:
  - phase-a-lane-purposes.md §7 (linkedin_engine; engagement formula reactions×1 + comments×3 + shares×5)
  - phase-b-research/linkedin_engine.md (3,893 words; 5 new criteria + LI-3 split + adaptor divergence)
  - phase-c-variant-ratings.md (no v189 LI fixtures in archive; proceed on Phase B research)
  - src/evaluation/rubrics.py:1187-1384 (current LI-1..6 prose)
optimization_target: ship-eligible draft rate + share/save trigger (engagement formula's heaviest lever)
---

# Phase D — `linkedin_engine` Rubric Spec

The lane produces `drafts/<id>.md` across **short_take** (500–900),
**thought_leader** (1,500–2,500), **case_study** (2,500–3,000) + upstream
`angles/<id>.json`. Two adaptors on one substrate: **operator profile** (JR
+ client-operators) with voice latitude, and **named-byline** (Dr. Maria
for Klinika Melitus; named DWF partners) bounded by Polish
medical-advertising rules (medical_pl) or bar advertising rules (legal_pl).

Phase B verdict: keep all six; strengthen four; **split LI-3** into LI-3a
(pre-fold yield) + LI-3b (post-fold payoff); **add five** — LI-7
(frameworkable artifact), LI-8 (B2B trust posture), LI-9 (insight density),
LI-10 (pre-fold stake-claim), LI-11 (compliance precondition). The split
addresses the 2026 algorithm's 60-min satisfaction window: a strong hook
with a collapsing body is a distinct failure from a weak hook, and the
single-criterion form silently averages them. LI-7 closes the *portability*
gap — saves weight 5× likes in 2026 and the existing six don't grade
forwardability. LI-11 carries **HARD FLOOR** on named-byline.

LI-11 trigger-phrase content is gated on Resolve-Before-Planning #2 (legal
review per byline). This spec defines *shape* + *evidence model*, not rule
text — same pattern as storyboard SB-12 / SB-15.

---

## Section 1 — Summary table

Tiers: **essential** (load-bearing; failure caps ship-eligibility),
**important** (drags when failed), **pitfall** (specific failure pattern
caps the score), **skip** (not assembled into rubric for that profile).

| ID    | Tier (operator) | Tier (named-byline) | ONE-quality summary                                                          | Disposition  |
|-------|-----------------|---------------------|------------------------------------------------------------------------------|--------------|
| LI-1  | essential       | essential           | LinkedIn voice — thoughtful authority, plain language, not Twitter-translated. | STRENGTHEN |
| LI-2  | essential       | essential           | Factual grounding — named entities for lived-work; ≥1 anchored specific / 300 chars. | STRENGTHEN |
| LI-3a | important       | important           | Pre-fold hook yield within 210 chars.                                          | SPLIT      |
| LI-3b | important       | important           | Post-fold payoff — hook's claim delivered within next 600 chars.               | SPLIT      |
| LI-4  | pitfall         | pitfall             | Zero AI / LinkedIn-AI tells.                                                   | STRENGTHEN |
| LI-5  | important       | important           | Bracket structure + 3–5 specific hashtags.                                     | STRENGTHEN |
| LI-6  | important       | important           | Cohort archetype + pillar diversity (cross-item).                              | KEEP       |
| LI-7  | important       | important           | Frameworkable artifact — named list / matrix / principle / checklist.          | NEW        |
| LI-8  | important       | **essential**       | B2B trust posture — buyer's-problem vs author's-growth memoir.                 | NEW        |
| LI-9  | important       | important           | Insight density — chunks/100 chars.                                            | NEW        |
| LI-10 | important       | important           | Pre-fold stake-claim — number OR named entity AND contrarian/falsifiable claim. | NEW       |
| LI-11 | **skip**        | **essential (HARD FLOOR)** | Compliance precondition — medical_pl or legal_pl.                       | NEW        |

**Per-profile totals.** Operator: 11 active (LI-11 skipped). Named-byline:
12 active (LI-11 fires; LI-8 tier shifts to essential). Operator's compliance
surface (defamation, NDA, public-client confidentiality) is handled upstream
— firing LI-11 on operator drafts would generate false-positives.

---

## Section 2 — Final criterion prose

### LI-1 — LinkedIn voice (essential) — STRENGTHEN

**Evaluate this draft for ONE quality:** Does it read in the declared
LinkedIn voice — first-person, story-led, professional register accessible
to B2B buyers and C-suite? The lever is **thoughtful authority**, not
contrarian punch. Plain language required; tone noticeably less contrarian
than X.

WHY: Interest-graph algorithm rewires distribution around topic authority
+ dwell. Twitter-translated drafts fail dwell — no paragraph cadence, no
scannable structure, no portable artifact. Company-page voice ("We at...",
"Our team is excited to...") triggers personal-profile-vs-page disadvantage
(94.63% vs 5.37% feed share).

- **Score 1:** Bait-y, hot-take-y, Twitter-translated. **AUTOMATIC ≤4**
  if Twitter-translated (zero LinkedIn-native structural elements AND
  <300 chars in thought_leader). **AUTOMATIC ≤6** if jargon without
  plain-English follow-up. **AUTOMATIC ≤5** on company-page-voice opener.
- **Score 3:** Mostly LinkedIn-appropriate but slips — contrarian
  declaration in paragraph 2, sub-200-char aggressive sentence, or jargon
  buyers tolerate but don't enjoy.
- **Score 5:** Throughout: thoughtful authority. First-person, story-led,
  specific lived-work register. Tone is "I've spent a year on this and
  here's what I noticed" not "you're doing this wrong."

**Adaptor branch.** Operator voice cross-referenced against
`programs/references/voice.md`. Named-byline against
`configs/voice_persona/<byline>/corpus_path`. Voice slipping into operator
register on named-byline = caps at 5.

**Closing.** Provide your reasoning, cite specific evidence, then give your score.

### LI-2 — Factual grounding (essential) — STRENGTHEN

**Evaluate this draft for ONE quality:** Are factual claims grounded? Same
SOURCE/INTERPRETIVE split as X-2. **HARD FLOOR:** lived-work claims REQUIRE
the named entity in `voice.md` (operator) or byline's corpus. **LinkedIn
cap:** first-person specific claim without named client/project caps at 7
— LinkedIn punishes vague specificity harder than X.

WHY: "I once worked with a SaaS company" is unfalsifiable filler. "When DWF
advised on the 2024 Polish ESG carve-out…" signals the author was in the
room. Ceiling requires ≥1 anchored specific per 300 chars in long-form.

- **Score 1:** Claims contradict source_text, or lived-work names entities
  absent from corpus. **HARD FLOOR:** unnamed-entity lived-work ≤3.
- **Score 3:** SOURCE claims verifiable; INTERPRETIVE framed as opinion.
  "We" or "our team" without named entity; density below 1 per 300 chars.
- **Score 5:** SOURCE traces cleanly. INTERPRETIVE framed as byline's view.
  Lived-work names corpus entities or stays general. Density ≥1 anchored
  specific per 300 chars. Fact-check in <2 minutes.

**Closing.** Provide your reasoning, cite specific evidence, then give your score.

### LI-3a — Pre-fold hook yield (important) — SPLIT

**Evaluate this draft for ONE quality:** Does the first 210 characters
earn the "see more" tap? Mobile LinkedIn collapses at ~210 chars; the
visible portion must deliver a stake-claim or the 60-minute satisfaction
score craters and the post dies before reaching 2nd-degree.

WHY: 0–3s dwell ≈ 1.2% engagement; 61s+ ≈ 15.6% — a 13× gap. The pre-fold
is the highest-leverage 210 chars in the draft.

- **Score 1:** No number, no named entity, no contrarian/falsifiable
  claim. Throat-clear ("Some thoughts on leadership today") or
  motivational affect or generic bait ("Are you ready for..."). **AUTOMATIC
  ≤3** if pre-fold contains engagement-bait pattern.
- **Score 3:** Specific element present but not load-bearing — topic
  without position, or position without anchor.
- **Score 5:** Specific number OR named entity AND falsifiable/contrarian
  claim within 210 chars. RvdB's "I researched 1.3 million LinkedIn posts.
  Here's the finding that surprised me most: Carousels used to dominate.
  In 2026, they're declining fast." passes.

**Ground-truth verification.** Substrate strips body at char 210 before
the judge runs; LI-3a scores pre-fold in isolation so the judge cannot
inflate based on unseen body.

**Closing.** Quote pre-fold. Identify number / named entity / contrarian
claim. Score against the count.

### LI-3b — Post-fold payoff (important) — SPLIT

**Evaluate this draft for ONE quality:** Does the body deliver the hook's
claim within the next 600 chars, or does the reader bounce after tapping
"see more"?

WHY: 2026 click-bounce detection (tap "see more" → leave) actively
deprioritises bait openers. A 9-tier hook with a 1-tier body is the worst
outcome: post earns the tap, reader bounces <3s, satisfaction signal goes
*negative*, algorithm buries the profile's next post. LI-3a + LI-3b grade
hook-and-deliver as a system.

- **Score 1:** Hook promised specific number / named-thing / contrarian
  claim; next 600 chars do not deliver. Bait-and-restate. **AUTOMATIC ≤2**
  if hook makes a quantitative claim never appearing in the body at all.
- **Score 3:** Claim eventually delivered but buried past char 800 or
  split across paragraphs. Reader scans, gets impatient.
- **Score 5:** Hook's claim delivered in the first paragraph below the
  fold (char 210–600). The specific number / named entity from LI-3a is
  *operationalised* — explained, anchored, forwardable.

**Ground-truth verification.** Judge re-uses LI-3a's extracted pre-fold
claim and searches body chars 210–810 for delivery. Match found = ≥3
floor; match absent = ≤2 ceiling.

**Closing.** Quote pre-fold claim. Quote body delivery (or note absence).
Score against the gap.

### LI-4 — Zero AI / LinkedIn-AI tells (pitfall) — STRENGTHEN

**Evaluate this draft for ONE quality:** Zero AI-tells AND zero
LinkedIn-AI-tells. The deterministic regex floor in `slop_gate.py
--platform linkedin` is the hard fail; this dimension judges what slips
through. LinkedIn-AI tells skew corporate-pleasing — sharper surface than X.

**Slop archetypes** (single match caps at 3; two or more = 1):
- **delve** — AUTOMATIC ≤3.
- **"in today's fast-paced world"** — AUTOMATIC ≤2.
- **synergy / leverage / unpack** as filler verbs (≥2 per 1000 chars).
- **em-dash carpet** — >4 em-dashes in <1,000 chars.
- **"It's not X, it's Y"** repeated >2× same post.
- **"Read that again. ↑"** self-reflexive close.
- **"Thoughts? 👇" / "Agree? 🤔"** engagement-bait close.
- **broetry cascade** — >50% single-sentence paragraphs on posts >800 chars.
- **Uber-driver opener / fake vulnerability** — "My Uber driver taught
  me...", "I cried in the bathroom at $1B exit." AUTOMATIC ≤2.
- **credential-flex with no anchored claim** — résumé-on-feed. AUTOMATIC ≤3.
- **motivational poster** — single-sentence post re-emphasising itself.
  AUTOMATIC ≤2.

- **Score 1:** Multiple archetypes fire. Voice = ChatGPT-with-an-MBA.
- **Score 3:** One archetype or one borderline pattern.
- **Score 5:** Zero AI-tells, zero LinkedIn-AI-tells. Whitespace serves
  structure, not padding. Closes land on byline's actual cadence.

**Closing.** List every archetype match. Quote offending strings. Score
against count and severity.

### LI-5 — Bracket structure + hashtag count (important) — STRENGTHEN

**Evaluate this draft for ONE quality:** Does the structure earn its
length AND does the hashtag count + specificity fit the LinkedIn 2026
distribution model? **3–5 specific hashtags ideal**; **1–2 = cap at 7**;
**0 = ≤4**. Spam guardrail (>5) handled by structural_gate.

WHY: 2026 deprioritises generic-tag stuffing. Pillar-mapped tags pass;
generic (`#leadership #motivation #success`) trigger the engagement-bait
classifier even at correct count.

- **Score 1:** Pad-to-length OR zero hashtags. **AUTOMATIC ≤4** if hashtags
  exclusively generic.
- **Score 3:** Mechanically correct for bracket. Hashtag count 1–2. **Cap
  at 7**.
- **Score 5:** Bracket-aware structural mastery + 3–5 pillar-mapped
  hashtags. SHORT_TAKE: story-opening + substantive paragraph + close.
  THOUGHT_LEADER: story → frame → 3–5 numbered points → implication close.
  CASE_STUDY: narrative + numbers timeline + named characters + implication.

**Closing.** Provide your reasoning, cite specific evidence, then give your score.

### LI-6 — Cohort archetype + pillar diversity (important, cross-item) — KEEP

**Evaluate this DRAFT COHORT for ONE quality:** Across all drafts, does
the narrative archetype vary (story-led / lesson-led / comparison /
case-study)? Do drafts spread across `voice_pillars`? **PUNISHES
same-tone-same-format streaks.** Score via geometric mean of per-draft
cohort-fit scores.

- **Score 1:** Same archetype across all drafts. **AUTOMATIC ≤3** if any
  single length_bracket exceeds 60% of cohort (sprint, not portfolio).
- **Score 3:** 2 distinct archetypes; partial pillar spread.
- **Score 5:** Distinct archetype per draft across the 4 LinkedIn-relevant
  categories. Pillar spread matches voice_pillars metadata.

**Closing.** Provide your reasoning, cite specific evidence from the cohort,
then give your score.

### LI-7 — Frameworkable artifact (important) — NEW

**Evaluate this draft for ONE quality:** Does the draft contain a portable
artifact — named list, decision matrix, named principle, or checklist —
that a B2B buyer could copy-paste into Notion and use tomorrow?

WHY: Saves weight **5× likes** and **2× comments** in 2026; save velocity
is the strongest single distribution signal. The B2B buyer who DMs a post
is LinkedIn's highest-value reader, and they only forward *forwardable*
content. Closing this gap is the highest-expected-value rubric change for
this lane (Phase B §7).

**X-vs-LinkedIn divergence.** LI-7 is **not** the equivalent of X-3 (hook
earns next line) or X-8 (reply-worthy). X rewards comments and
quote-tweets; LinkedIn rewards *portability* — extraction from feed into
private knowledge store. A LinkedIn post can be reply-worthy + unportable
(motivational quip) or portable + reply-quiet (decision matrix bookmarked
by thousands with zero comments). LI-7 grades the second class.

- **Score 1:** No portable unit. Affect, memoir, motivational quip.
  **AUTOMATIC ≤2** on broetry cascade (abstracts away framework details).
- **Score 3:** List/structure present but unnamed/generic ("5 lessons I
  learned"). Screenshot-quotable but wouldn't be — no handle a forwarder
  can name when sharing.
- **Score 5:** A named artifact — Bloom's "New Opportunity Razor," Welsh's
  "Three questions worth asking once a quarter," a decision matrix with
  named axes, an operationally-specific checklist — that survives copy-paste
  into Notion. Forwarder can quote the artifact's *name* in a DM without
  quoting the whole post.

**Ground-truth verification.** 30-day shadow: correlate LI-7 against
`bookmarkCount / impression` from `linkedin_post` table (following
`x_engine.tweet` pattern). Target: LI-7 = 5 produces ≥2× save-rate of
LI-7 = 3. Drift <1.5× = grading prose presence rather than forwardability.

**Closing.** Identify the artifact. Test forwardability: can its name be
quoted in a DM without the whole post? Score against the answer.

### LI-8 — B2B trust posture (important on operator / essential on named-byline) — NEW

**Evaluate this draft for ONE quality:** Is the protagonist the **reader's
problem** or the **author's growth story**? Does ≥40% of body diagnose
the buyer's current week or name a specific buyer-segment problem?

WHY: 74% of B2B decision-makers trust thought leadership over product
marketing *only when it addresses their problem*; 95% say strong thought
leadership opens them to outreach but they bail on memoir. RvdB: "Nobody
cares what you do. Post about what they need."

**X-vs-LinkedIn divergence.** X-3 grades hook strength irrespective of
posture; LinkedIn punishes growth-memoir framing in a way X does not. A
Welsh-style "I exited my agency and here's what I learned" performs on X
(X consumes memoir as content). On LinkedIn the same draft fails LI-8 —
LinkedIn's B2B-trust frame demands the post be *about the reader*.

- **Score 1:** Pure author-growth memoir. 80%+ first-person-singular; zero
  buyer diagnosis. **AUTOMATIC ≤2** if credential-flex-shaped per LI-4.
- **Score 3:** Story-led with a real but generic lesson; structurally
  about author transformation. 5-tier ceiling for operator.
- **Score 5:** Author's experience is the *vehicle*; ≥40% body diagnoses
  buyer's current week. Welsh's "weird side effect of building a simple
  business — investors and customers misread simple as hiding the
  complicated part" lands here.

**Adaptor branch — substrate dispatch.** Operator: LI-8 **important**.
Named-byline (Dr. Maria / DWF partner): LI-8 **essential** — author-journey
posts fail compliance *posture* even when string-match-compliant. Dr. Maria
posting "I love what I do" is 4-tier; DWF partner posting "my journey from
associate to partner" misreads the byline's job (regulatory authority for
buyer firms, not personal-brand narrative). Judge prose is *identical*
across profiles; substrate flags `essential` vs `important` in the
assembled rubric. Splitting prose per profile would silently fork the
calibration corpus.

**Closing.** Identify the protagonist. Quote the diagnostic passage if
present. Score against the answer; substrate applies the tier shift.

### LI-9 — Insight density (important) — NEW

**Evaluate this draft for ONE quality:** Does the draft deliver ≥0.40
chunks per 100 chars in thought_leader, ≥0.35 in case_study, ≥0.50 in
short_take? **Chunk** = named org / named person / number-with-unit /
dated event / named principle / falsifiable prediction / mechanism explanation.

WHY: Dwell time is the primary 2026 distribution gate; density is the
proxy that lets a long post earn the dwell rather than burn the reader.
Bloom's high-engagement long-form averages 0.45–0.55; his "New Opportunity
Razor" drops to ~0.28 because Hofstadter + Djokovic padding dilutes density.

- **Score 1:** <0.15 chunks/100 chars. **AUTOMATIC ≤2** if draft >800
  chars AND chunk count ≤3.
- **Score 3:** 0.20–0.30. Competent but underweight. Reader finishes but
  doesn't forward.
- **Score 5:** ≥0.40 thought_leader, ≥0.50 short_take, ≥0.35 case_study.
  Each paragraph adds new information. Bloom's "Money advice" at ~0.45
  chunks/100 chars (4,449 likes / 2,342 bookmarks) is the calibration anchor.

**Ground-truth verification.** Judge numbers every chunk in evidence;
count must match the score's band. 30-day shadow correlation target: r
> 0.40 between LI-9 and `(comments + 3×shares) / impression`.

**Closing.** Number every chunk in evidence. Compute density. Score
against the band.

### LI-10 — Pre-fold stake-claim (important) — NEW

**Evaluate this draft for ONE quality:** Does the pre-fold (chars 0–210)
contain a specific number OR named entity AND a falsifiable/contrarian
claim?

WHY: LI-10 is the sharper sibling of LI-3a. LI-3a grades pre-fold *yield*
broadly; LI-10 grades the *specific elements* deterministically. The two
together prevent inflation on a hook that earns the tap on style without
carrying a stake-claim.

**X-vs-LinkedIn divergence.** X-3's "hook earns next line" is single-stage
because X has no fold cutoff. LinkedIn's mobile 210-char cutoff makes the
pre-fold a distinct artifact with its own quality signature.

- **Score 1:** No number, no named entity, no contrarian/falsifiable
  claim. **AUTOMATIC ≤2** on motivational-poster pre-fold.
- **Score 3:** Specific element present but not load-bearing — topic
  without position, position without anchor, generic number ("3 things").
- **Score 5:** Specific number OR named entity AND falsifiable/contrarian
  claim within 210 chars. RvdB's 1.3M-post hook passes. Hook is itself a
  quote-card-quality stake-claim.

**Ground-truth verification.** Direct — measure first-60-min
CTR-to-expand against LI-10 score. LI-10 = 5 should produce ≥1.5× the
expand-rate of LI-10 = 3.

**Closing.** Quote pre-fold. Identify number, named entity, falsifiable
claim. Score against the count.

### LI-11 — Compliance precondition (essential / HARD FLOOR on named-byline; skip on operator) — NEW

**Fires when** the draft's frontmatter declares `compliance_regime:
medical_pl` (Klinika Dr. Maria) or `compliance_regime: legal_pl` (DWF
partner). **Skips entirely** when `compliance_regime: null` (operator).

**Evaluate this draft for ONE quality:** Is the content informational /
educational / mechanism-led while staying inside the Polish
medical-advertising rule set (medical_pl) or Polish bar advertising
rules (legal_pl)?

WHY: A 9-tier-engaging draft on Dr. Maria's profile violating
aesthetic-medicine rules creates real legal/clinical risk for Klinika; a
DWF partner draft soliciting or mentioning fees creates regulatory
liability for the firm. Compliance is a **precondition**, not a quality
booster — violation caps the draft *below ship-eligibility*. The judge
catches violations in the loop so the human gate doesn't have to.

**Cross-reference** (gated on Resolve-Before-Planning #2). Rule list at
`configs/compliance/<regime>/rules.yaml` — path is normative; content is
operator-loaded after legal review per byline. Same files referenced by
storyboard SB-12 / SB-15 and article_engine / image_engine / ad_engine
compliance criteria — single source of truth across content-for-publish
lanes.

**Rule categories — medical_pl (Klinika Dr. Maria):**
- (a) **POM-name blocklist** — Botox, Dysport, Vistabel, Azzalure
  (prescription-only medicines, cannot appear in advertising per Polish
  pharma statute).
- (b) **Result-promise patterns** — "guaranteed results," specific outcomes.
- (c) **Comparative claims** — "best in [city]," "the leading clinic."
- (d) **Solicitation** — "DM me to book," direct booking CTAs.
- (e) **Identifiable patient detail** — patient stories with identifiable features.
- (f) **Body-image exploitation** — "finally feel beautiful," appearance-shame framing.

**Rule categories — legal_pl (DWF partner):**
- (a) **Solicitation verbs** — "contact us today," "skontaktuj się z nami."
- (b) **Fee mentions** — "our fees," "competitive rates."
- (c) **Comparative claims** — named-competitor comparisons.
- (d) **Client-result promises** — "we win cases," "guaranteed outcomes."
- (e) **Testimonials without consent metadata.**
- (f) **Identifiable client matter** — named client, identifiable docket.
- (g) **Opposing-party criticism.**

**When the HARD FLOOR fires.** Confirmed regex match against any rule
category triggers **auto-cap at 2** for LI-11 AND **caps overall draft
score at 4**. Deterministic — match triggers cap regardless of qualitative read.

**Verifiable evidence.** Judge must quote the violating string and
identify the rule category. Vague evidence does not trigger auto-cap —
the cap requires concrete evidence the human reviewer could verify in 5
seconds.

- **Score 1:** Confirmed violation quoted. Auto-cap fires; overall capped at 4.
- **Score 3:** No explicit violation but content so cautious it loses
  informational value ("we can't talk about specific brands" said three
  times). Fails the byline's educational/authority job.
- **Score 5:** Useful, specific, compliance-clean. **medical_pl:** names
  what *can* be named (filler chemistry, hyaluronic acid, post-procedure
  timelines). Avoids what cannot. **legal_pl:** informational throughout;
  closing is a buyer-side question, not a CTA; no fee/phone/email
  references. Avoidance doesn't show.

**Closing.** Scan against each rule category for the firing regime. If
any match, quote the violating string, identify the rule category,
trigger the auto-cap. Only then assess the qualitative dimension.

---

## Section 3 — Adaptor dispatch (operator vs named-byline)

Substrate reads the draft's frontmatter and assembles the per-profile
rubric. Same pattern as storyboard mode dispatch.

**Frontmatter schema:**

```yaml
---
profile: operator | named_byline
voice_persona: jr | klinika/dr-maria | dwf/partners/<slug>
compliance_regime: null | medical_pl | legal_pl
---
```

**Operator (JR or client-operator):** LI-1, LI-2, LI-3a, LI-3b, LI-4,
LI-5, LI-6, LI-7, LI-8 (*important*), LI-9, LI-10. **LI-11 skipped.**
Total: 11 active.

**Klinika Dr. Maria (medical_pl):** 11 above + LI-11 (essential / HARD
FLOOR, medical_pl rule set). LI-8 tier shifts **essential**. Total: 12.

**DWF partner (legal_pl):** 11 above + LI-11 (essential / HARD FLOOR,
legal_pl rule set). LI-8 tier shifts **essential**. Total: 12.

**Default.** Frontmatter absent → `profile: operator`, `compliance_regime:
null`. Preserves backward compatibility with v007-curated LI corpus.

**Tier shift mechanics.** LI-8's tier change is the only load-bearing
dispatch on prose-shared criteria. Judge prose is *identical* across
profiles; substrate flags `essential` (named-byline) vs `important`
(operator) in the assembled rubric and the aggregator weights accordingly.
Splitting prose per profile would silently fork the calibration corpus.

---

## Section 4 — Implementation notes

**LI-3 split — substrate counts hook chars deterministically.** Before
the judge runs:

```python
def split_pre_post_fold(body: str) -> tuple[str, str]:
    pre_fold = body[:210]
    post_fold = body[210:810]   # next 600 chars for click-bounce window
    return pre_fold, post_fold
```

LI-3a + LI-10 receive `pre_fold` only. LI-3b receives `pre_fold` (for
hook-claim reference) + `post_fold` (for delivery check). Prevents
inflation based on body content unseen by the user pre-tap.

**LI-11 compliance regime integration.** Trigger phrases live in
`configs/compliance/{medical_pl,legal_pl}/rules.yaml` — same files
referenced by storyboard SB-12 / SB-15 and article/image/ad_engine
compliance criteria. Single source of truth across content-for-publish
lanes. Until rule files are populated (Resolve-Before-Planning #2), LI-11
fires in **shape-only mode**: judge confirms cross-reference path exists,
declares "not yet scoring," abstains. Fail-loud rather than silently
scoring against an empty rule list.

**voice_persona corpus cross-reference.** LI-1 (operator) references
`programs/references/voice.md`. LI-1 + LI-2 (named-byline) reference
`configs/voice_persona/<byline>/corpus_path` — declares the byline's
published-work corpus + named entities the byline can claim lived-work
authority on. Naming an absent entity = LI-2 HARD-FLOOR failure.

**LI-7 ground-truth via bookmarkCount.** 30-day shadow on first 5 sessions
per profile. Route via `linkedin_post` table following `x_engine.tweet`
pattern (`bookmark_count`, `impression_count`, `share_count`,
`comment_count`). Target: LI-7 = 5 → ≥2× save-rate of LI-7 = 3. Drift
<1.5× = revise anchors.

**LI-9 ground-truth.** Same shadow. Target: r > 0.40 between LI-9 and
`(comments + 3×shares) / impression`. The engagement formula's heaviest
weights are on the right side; LI-9 should correlate with share+comment,
not likes.

**RUBRIC_VERSION hash invalidates on:** (1) LI-1..11 criterion text;
(2) firing table; (3) `medical_pl/rules.yaml` content hash; (4)
`legal_pl/rules.yaml` content hash; (5) voice_persona corpus files; (6)
`programs/references/voice.md`. Without (3)–(6), score cache could
return stale "no violation" or voice-off verdicts after updates and ship
violating content.

**Deterministic pre-checks in slop_gate.** `slop_gate.py --platform
linkedin` handles AI-banned regex floor, hashtag count > 5 guardrail,
broetry cadence detection, engagement-bait close-patterns, poll auto-reject.
Discards pre-rubric. LI-4 grades what slips through.

**LI-6 cross-item.** Unchanged: glob `drafts/*.md`, scored once per
cohort. Profile-agnostic.

---

## Section 5 — Validation plan

First 5 sessions per profile type validate dispatch + new criteria
end-to-end before committing the spec to substrate.

**V1. LI-3a vs LI-3b discrimination.** 5 fixtures with mismatched
hook-and-body: (1) strong pre-fold + weak body (philosophy, no
follow-through on quantitative hook); (2) weak pre-fold + strong body;
(3) matched strong; (4) matched weak; (5) strong pre-fold, body delivers
past char 800. Expected: F1 → LI-3a=5, LI-3b≤2 (hook-and-bait); F2 →
LI-3a=1, LI-3b=5; F3 both 5; F4 both 1; F5 → LI-3a=5, LI-3b=3. Scores
move independently — conflation = split is broken.

**V2. LI-8 tier shift on named-byline.** Same author-memoir draft scored
twice — operator and Klinika Dr. Maria. Draft: "Last quarter I learned
three things about myself as a clinician…" Expected: operator LI-8 = 3
(drags but doesn't cap); named-byline LI-8 = 2 (essential tier; below
ship-eligibility). Gap ≥1.0 = tier shift working; <0.5 = dispatch broken.

**V3. LI-7 frameworkable artifact correlation.** 30-day shadow on first
20 published drafts. Target: LI-7 = 5 cohort produces ≥2× save-rate of
LI-7 = 3 cohort. Drift <1.5× = tighten "named artifact" anchor (Bloom's
"New Opportunity Razor" is calibration ceiling).

**V4. Compliance auto-fire on synthetic violating drafts.**
- *medical_pl:* inject "After Botox treatments my patients see guaranteed
  10-year reversal — better than any clinic in Warsaw." Expected: LI-11 =
  1; capped at 4; evidence quotes "Botox" (a), "guaranteed 10-year reversal"
  (b), "better than any clinic" (c).
- *legal_pl:* inject "If your team has questions about KSeF, our competitive
  fees make us the leading partner — contact us today." Expected: LI-11 =
  1; capped at 4; evidence quotes "contact us today" (a), "competitive
  fees" (b), "leading partner" (c).

Violating fixture scoring above the cap = auto-cap logic not wired
correctly. Cap must be deterministic, not judgment-driven.

**V5. Dispatch correctness.** Score one fixture three times — operator,
named_byline + medical_pl, named_byline + legal_pl — on the same body.
Expected: three different rubric assemblies, three different score sets.
LI-11 fires only on passes 2 and 3 with regime-specific rule categories.
LI-8 tier shifts between pass 1 and passes 2/3. Same firing across all
three = dispatch broken.

**V6. Operator regression.** Run existing v007-curated LI corpus on the
updated rubric (default operator). Expected: LI-1..6 within ±0.2 of
v007-curated baseline; LI-7 + LI-8 + LI-9 + LI-10 fire additively and
lower scores on drafts lacking portability / B2B trust posture / density
/ pre-fold stake-claim. Drift >0.5 on LI-1..6 = strengthen passes silently
changed calibration; inspect diff.
