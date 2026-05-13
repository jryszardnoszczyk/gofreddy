---
date: 2026-05-12
phase: D
lane: x_engine
status: spec — implementer-ready; X-9 deterministic regex + X-4 2026 slop signature list gated on slop_gate.py edit
inputs:
  - phase-a-lane-purposes.md §6 (x_engine, ship-eligible draft rate)
  - phase-b-research/x_engine.md (2026 algorithm + AI-slop corpus, 4 new criteria + 2 strengthens)
  - phase-c-variant-ratings.md (3/3 archived drafts include external links in [REPLY] — X-9 empirically validated)
  - autoresearch/archive_marketing_audit/v192/workflows/session_eval_x_engine.py (current X-1..X-6 prose + structural gate)
  - src/evaluation/rubrics.py:984-1184 (current X-1..X-6 final-judge prose)
optimization_target: ship-eligible draft rate — would the operator publish this unedited and would it perform above their baseline
---

# Phase D — x_engine rubric spec (10 criteria, 3 length brackets)

The x_engine lane writes `drafts/<id>.md` files with `[BODY]` + `[META]` blocks and a length_bracket frontmatter field — `sharp` (250-300 chars), `build` (500-900), or `case_study` (1000-1500). The judge predicts ship-eligible rate. It is not grading "is this good content" abstractly; it is predicting "would JR publish this draft unedited, and would it perform above his baseline."

Phase B verdict: X-1..X-6 stay, four of them strengthen, and four new criteria (X-7 specificity density, X-8 reply-worthiness, X-9 algorithmic-citizenship, X-10 original perspective) close the gaps the current rubric leaves open. Phase C confirmed X-9 empirically — all three drafts in the 2026-05-12 archived session embed `https://openai.com/...` in their `[REPLY]` blocks, which triggers a 30-50% reach reduction per the March 2025 X link-penalty cutover (softened October 2025 but native-only still dominates). Phase C also confirmed X-6's current anchors are not demanding enough: three drafts on the same OpenAI source-frame should score 2, but the existing prose lets one-source-frame cohorts pass higher.

Final count: **10 criteria** — **3 essential** (X-1, X-2, X-9), **5 important** (X-3, X-5, X-6, X-7, X-8), **2 pitfall** (X-4, X-10). X-9 is essential-tier with a deterministic AUTOMATIC cap at 1 on URL match; X-1 retains its AUTOMATIC ≤4 on jargon; X-2 retains its HARD FLOOR ≤3 on unverifiable lived-work. X-6 stays cross-item over `drafts/*.md`. The slop_gate.py regex floor (LinkedIn-on-X, thread-baiter, generic-bro, hashtag-stuffer, growth-hack-template, rage-bait) fires deterministically in the structural gate BEFORE the judge sees the draft.

---

## Section 1 — Summary table

| ID    | Tier      | ONE-quality summary                                                                       | Disposition  |
|-------|-----------|-------------------------------------------------------------------------------------------|--------------|
| X-1   | essential | JR's first-person opinionated plain-language voice; jargon without follow-up caps it.     | STRENGTHEN   |
| X-2   | essential | SOURCE/INTERPRETIVE split; lived-work entity must appear in `voice.md` (HARD FLOOR).      | KEEP         |
| X-3   | important | Hook earns the next line; bracket-aware compression vs show-more cutoff.                  | KEEP         |
| X-4   | pitfall   | Zero 2026 AI-tells; sentence-length uniformity + opener vocabulary, not em-dashes.        | STRENGTHEN   |
| X-5   | important | Structure earns the declared length bracket (sharp / build / case_study).                 | KEEP         |
| X-6   | important | Cohort spreads across distinct source-frames, angles, and voice_pillars (cross-item).     | STRENGTHEN   |
| X-7   | important | Specificity density: proper-noun + numeric anchor count per 100 words.                    | NEW          |
| X-8   | important | Reply-worthiness: ending hands the reader a clean response surface.                       | NEW          |
| X-9   | essential | Algorithmic-citizenship: no external links in [BODY] or [REPLY] (AUTOMATIC cap at 1).     | NEW          |
| X-10  | pitfall   | Original perspective: would a competent generalist competitor have written this?          | NEW          |

The composition rule is the minimum of the three essential criteria (X-1, X-2, X-9) compounded with the weighted mean of the importants (X-3, X-5, X-6, X-7, X-8) and the two pitfalls (X-4, X-10) as caps. Slop_gate.py regex hits drop the draft to 1 before the judge runs.

---

## Section 2 — Final criterion prose

### X-1 (essential, gradient) — STRENGTHEN

Diff vs current `_X_1` (rubrics.py:992-1024): expand the AUTOMATIC ≤4 list with the 2026 AI-slop opener vocabulary (Phase B §5.6) — `Absolutely`, `Picture this`, `Here's the thing`, `It's important to note`, `delve`, `navigate`. The ≤6 single-unexplained-term floor stays. Existing Score-1/3/5 prose intact; insert one new AUTOMATIC clause in Score-1:

```
Score 1: [...existing text...] Or: 2026 AI-slop opener vocabulary
fires — "Absolutely", "Picture this", "Here's the thing", "It's
important to note", "delve", "navigate". AUTOMATIC ≤4 if 2+
unexplained technical terms; AUTOMATIC ≤4 if any 2026 AI-slop
opener appears anywhere in [BODY]; AUTOMATIC ≤6 if any single
jargon term appears without a follow-up plain-English phrase.
```

Score-3 and Score-5 prose unchanged. Closing unchanged.

### X-2 (essential, gradient) — KEEP

Existing prose at `src/evaluation/rubrics.py:1026-1058` stays verbatim. Phase B confirmed the HARD FLOOR ≤3 on first-person specific lived-work claims referencing entities outside `programs/references/voice.md` is the right shape — the failure mode it catches (fabricated case studies, made-up client names) is binary, deterministic against the substrate, and not duplicated by X-7's density check. X-7 covers the orthogonal "vacuously generic but technically verifiable" gap.

### X-3 (important, gradient) — KEEP

Existing prose at `src/evaluation/rubrics.py:1060-1092` stays. Phase B §4.1 anchor — "first 100 chars must contain ≥1 concrete noun AND deliver enough payload that the reader could screenshot the first sentence as a thought" — is already encoded in the current Score-5 anchor ("one sharp claim+support pair in the first 12 words"). Phase B's bracket-aware split (sharp by 100 chars, build/case_study by 280) is also already present. No diff.

### X-4 (pitfall, gradient) — STRENGTHEN

Diff vs current `_X_4` (rubrics.py:1094-1121): GPT-5.1 and successors suppress em-dashes (Phase B §5.6); em-dash density is no longer the primary signal, and em-dash absence is no longer exonerating. The 2026 tells are sentence-length uniformity, paragraph-length uniformity, opener vocabulary, and the specificity-density vacuum paired with confident-declarative register. Slop_gate.py regex stays the deterministic catch BEFORE the judge runs; this dimension judges what slips through.

```
Evaluate this draft for ONE quality:
Zero AI-tells, 2026 signature. The deterministic regex floor in
slop_gate.py is the hard fail; this dimension judges what slips
through. Em-dash density is no longer load-bearing — GPT-5.1
suppresses it. The 2026 tells are stylistic fingerprints:
sentence-length uniformity, paragraph-length uniformity, opener
vocabulary, and the specificity-density vacuum paired with
confident-declarative register.

Score 1: Multiple 2026 AI-tell patterns slip through the regex.
Examples: sentence-length variance below ±1σ of JR's recent
posts; paragraph-length uniformity (3+ paragraphs within ±10% of
each other); opener vocabulary ("Absolutely", "Picture this",
"Here's the thing"); confident-declarative register without
proper nouns or numbers ("AI is reshaping marketing"); transition
vocabulary that reads auto-generated ("Furthermore,", "Moreover,",
"Now,", "So,"); parallel "It's not X. It's Y." structures.

Score 3: One or two patterns slip through — a parallel
construction in the middle of the draft, one opener-vocabulary
hit, one paragraph that rhythmically matches the one before it. A
ZeroSlop / ThatSlop browser-extension user would catch the seam.

Score 5: Zero AI-tells in the 2026 signature set. Sentence-length
distribution varies and matches JR's recent posts (±1σ).
Paragraph lengths vary. Transitions are JR's actual register
("but", "and so", "which means") not formal "Furthermore" /
"Moreover". Opener is concrete-noun-anchored, not opener-
vocabulary-template. Specificity density is high enough that the
confident-declarative voice has earned its register.

Provide your reasoning, cite specific evidence from the draft,
then give your score.
```

### X-5 (important, gradient) — KEEP

Existing prose at `src/evaluation/rubrics.py:1123-1154` stays. The bracket-aware split (sharp = compression, build = pivot + bullets + authority anchor + outcome metric, case_study = narrative + sensory detail + numbers timeline + implication close) already encodes Phase B §1.6's three-locked-beats test for case_study. Pad-to-length already caps at 4. No diff.

### X-6 (important, cross-item gradient) — STRENGTHEN

Diff vs current `_X_6` (rubrics.py:1156-1183): existing prose accepts "spread across 3-4 distinct angles" at Score-3, which read "wording variation" as "angle variation" in Phase C (3/3 OpenAI-source drafts scored above the cap). New prose locks the bar at distinct **source-frames** AND distinct **angles** AND distinct **voice_pillars**. Three drafts on one source = Score 1, no matter how the wording varies.

```
Evaluate this DRAFT COHORT for ONE quality:
Across all drafts in this session's drafts/ directory, do they
spread across distinct source-frames, angles, and voice_pillars?
Or do multiple drafts rest on the same underlying source, the
same interpretive bet, or the same voice_pillar with only surface
wording variation? Score the cohort as a whole.

A source-frame is the underlying piece of evidence the draft is
built around (a specific OpenAI announcement, a Vassallo post, an
autoresearch run). An angle is the interpretive bet on top of
that source-frame. A voice_pillar is declared in angle metadata.
Three drafts citing the same OpenAI URL with three different
rewordings of "AI agencies need to sell outcomes not tools" = ONE
source-frame, ONE angle, possibly ONE voice_pillar, and scores 1
regardless of individual draft quality.

Score 1: Multiple drafts (2+ of 3, or 3+ of 5) share the same
source-frame OR the same angle OR the same voice_pillar. The
cohort reads as wordings of one bet. Pillar diversity collapses
to 1-2 pillars when angle metadata supports 4+.

Score 3: Some source-frame variation (2-3 distinct sources) but
angles converge OR voice_pillars converge. Breadth on one axis,
concentration on another.

Score 5: Each draft uses a distinct source-frame AND a distinct
angle AND a distinct voice_pillar. If two drafts agree on the
same direction, at least one contradicts the other on a sub-
point. No two drafts could be swapped without losing variant
value. The cohort is 3-5 distinct bets, not 3-5 rewordings of one
bet.

Provide your reasoning, list the (source-frame, angle, voice_
pillar) tuple for each draft, then give your score.
```

### X-7 (important, gradient) — NEW

WHY: Phase B §4.2 names specificity density "the load-bearing signal X-2 currently underweights." X-2 catches false lived-work; X-7 catches vacuously generic but technically verifiable. A draft can pass X-2 by claiming nothing specific; X-7 forces something specific to be said. The 2026 Grok-Phoenix ranker scores content-level features at the ranking layer — specificity is a distribution lever, not just a reader-quality lever.

WHAT: count proper-noun tokens (NER on `[BODY]`) plus numeric tokens with referents; divide by body word count × 100. Bracket-aware target.

```
Evaluate this draft for ONE quality:
How densely is the draft anchored in specific proper nouns and
numbers — and are those anchors load-bearing or decorative?

Proper nouns are named people, companies, products, places, dates,
events. Specific numbers are quantitative anchors with a referent
("$8,500 in sponsorship", "47 hours of debugging", "93% a month").
Decorative numbers ("3 things", "5 lessons") do not count. Load-
bearing means the central claim collapses without the anchor —
Vassallo's "$8,500 in sponsorship revenue" is load-bearing; "I
learned 5 things" is not.

Bracket-aware. Sharp (250-300 chars) earns 5 with ≥1 concrete
proper noun OR ≥1 load-bearing number — the format is compression.
Build (500-900) and case_study (1000-1500) need density.

Score 1: Zero proper nouns AND zero numbers in [BODY]. Pure
abstraction. Or: for build/case_study, ≤1 proper noun AND ≤1
number across the whole body — insufficient for the bracket. The
draft could have been written by anyone about anything.

Score 3: Meets minimum density for the bracket (sharp: ≥1 anchor;
build/case_study: ≥2 proper nouns + ≥1 number per 100 words) but
no anchor is load-bearing — the claim survives if you remove any
single specific. Anchors decorate; they don't carry the argument.

Score 5: Sharp earns 5 with ≥1 concrete proper noun OR ≥1 load-
bearing number in the punch. Build/case_study earns 5 with ≥3
proper nouns OR ≥2 specific numbers per 100 words AND ≥1 anchor
that is the central claim — remove it and the draft loses its
point. Dwarkesh-class density (David Reich + Ali Akbari +
"agricultural revolution" + "5,000 years" + "90%" in 200 words)
or Vassallo-class compression ($8,500 + 2 weeks + 35,000 players
in 30 words).

Verify against [BODY] only (META frontmatter does not count).
Cross-reference against the angle JSON to confirm anchors trace
to source_text or voice.md.

Provide your reasoning, list the anchors you counted with one
quoted phrase each and a (load-bearing | decorative) tag, then
give your score.
```

### X-8 (important, gradient) — NEW

WHY: Phase B §5.4 cites the 2026 X algorithm weights — reply×13.5, quote×20, author-reply×150 vs like×1. Reply rate is the second-largest distribution lever after specificity density. Phase B §1.8: ending hands the reader a clean response surface. Button-up endings ("That's the lesson," "Stay curious," "Build something") forfeit the lever.

WHAT: read the last sentence of `[BODY]` in isolation and imagine the peer reply. Generic affirmation = fail.

```
Evaluate this draft for ONE quality:
Does the closing hand the reader a clean response surface — an
open question whose answer is a specific example, a falsifiable
claim a peer would corroborate or correct, or a named-but-
incomplete observation that invites anchored disagreement?

Reply-worthiness is not "ends in a question mark" — generic open-
ended questions ("thoughts?", "agree?") earn no specific replies,
just generic affirmation. Read the last sentence of [BODY] in
isolation. Imagine what a peer in JR's audience would reply. If
that reply is "good point" / "agreed" / "great post", the close
failed. If the reply names a specific example, corrects a claim,
or extends the observation with anchored detail, the close
succeeded.

Score 1: Closes with a button-up moralism, summary statement, or
reciprocity-bait CTA ("if this resonated, follow for more"). The
draft tells the reader the conclusion and closes the loop.

Score 3: Closes with a generic open-ended question or soft hook
("thoughts?", "agree?", "what's your take?"). The reader could
reply but has nothing specific to respond to.

Score 5: Closing is a clean response surface JR's audience would
feel compelled to answer with their own example, correction, or
anchored disagreement. Either: (a) open question whose answer is
a specific lived example; (b) falsifiable claim a peer would
corroborate or correct ("the only agencies making money on AI
are doing data work, not creative work"); (c) named-but-
incomplete observation ("Anthropic's pricing implies a bet on
context length over throughput — I think they're wrong about
which one matters in 2027").

Provide your reasoning, quote the last sentence in isolation,
write the imagined-reply you predict, then give your score.
```

### X-9 (essential, gradient — AUTOMATIC cap at 1 on URL match) — NEW

WHY: Phase B §1.9 + §5.3 documents the March 2025 X external-link reach penalty (30-50% reach reduction; median engagement zero for non-Premium); October 2025 softened the policy but native-only still outperforms. Phase C empirically validated: all 3 drafts in the 2026-05-12 archived session embed `https://openai.com/index/introducing-b2b-signals` in their `[REPLY]` block. Existing X-1..X-6 does not catch this. Essential-tier with deterministic AUTOMATIC cap at 1 on URL match.

WHAT: regex check on `[BODY]` and `[REPLY]` substrings. Quote-tweet references declared in `[META] quote_tweet:` and image/video markers `[IMAGE: ...]` / `[VIDEO: ...]` are exempt. Everything else triggers the cap.

```
Evaluate this draft for ONE quality:
Is the draft native to X — zero external links in [BODY] or
[REPLY], no thread-tease markers, no off-platform redirects?

Since March 2025, X has cut reach 30-50% for posts with external
links from non-Premium accounts. The algorithm wants users to
stay on platform; posts that pull users off-platform tank dwell-
time and reply-velocity in the critical first 30-minute window.
Not stylistic — a distribution requirement.

AUTOMATIC cap at 1 on URL match. The deterministic check matches
in [BODY] or [REPLY]:
  - http://...  https://...
  - bare domains (openai.com, github.com, gofreddy.com, etc.)
  - shorteners (t.co/, bit.ly/, buff.ly/, lnkd.in/)
  - thread-tease markers: 🧵 / 1/ / (thread) / ↓ / "read on" /
    "more in replies" / "bookmark for later"

EXEMPT:
  - native quote-tweet references declared in [META] as
    quote_tweet: <https://x.com/...>
  - image/video markers [IMAGE: <path>] / [VIDEO: <path>]
  - in-prose names without a URL ("OpenAI announced") pass

Score 1: [BODY] or [REPLY] contains at least one non-exempt URL,
shortener, naked domain, OR thread-tease marker. AUTOMATIC cap
fires; X-9 = 1 regardless of qualitative read; overall fixture
score capped at 2 (below ship-eligibility). The draft is
distribution-broken. The 2026-05-12 archived drafts (jr-2026-05-
08-121-001/002/003) all score 1 here — they embed openai.com in
[REPLY].

Score 3: No URL or thread-tease marker, but the draft is content-
shaped for a linked post — references a study or article without
a native quote-tweet alternative; prose creates the expectation
of a link that isn't there. Native-compliant but format-
mismatched.

Score 5: Zero URLs in [BODY] or [REPLY]. Zero thread-tease
markers. Substance lives in the post body. If a source is
referenced, it is named in prose AND the post stands alone
without the reader needing to leave platform. Optionally: a
native quote-tweet declared in [META] if the draft extends
another X post.

Verify by running the URL regex on [BODY] and [REPLY]. If any
non-exempt match fires, score = 1, evidence quotes the matched
substring.

Provide your reasoning, quote any matched URL or thread-tease
marker (or confirm none), then give your score.
```

### X-10 (pitfall, gradient) — NEW

WHY: Phase B §4.5 frames the adversarial test — "could the operator's competitor have published the same post?" — as the distinguisher between 9-tier and competent-consensus. Dwarkesh's Bronze-Age post inverts modal consensus on its topic; that's why it earns 1,254 likes / 51 replies at 859 chars. Pitfall tier (matching X-4): failure caps the score when the draft is competent-consensus.

WHAT: LLM-judged adversarial test against the angle JSON's `source_text` and the JR voice substrate at `programs/references/voice.md`.

```
Evaluate this draft for ONE quality:
Is the perspective original — a position, observation, or angle
that could only have come from JR's specific corpus of work,
conversations, measurements, or stack — or is it competent-
consensus that any informed generalist could have written?

Imagine a competent generalist writer in JR's domain (an AI-savvy
agency founder, a marketing operator who reads the same
Substacks, a builder who follows the same discourse) without
access to JR's autoresearch corpus, client engagements, or
specific build measurements. Could they have written this post?
If yes, substitutable — competent but ceiling-bound. If no,
identify what makes it non-substitutable.

Score 1: Verbatim restatement of consensus. "AI is reshaping
marketing." "Agencies need to focus on outcomes." "The future is
agentic." A competitor could publish the same post this week
without any inside knowledge.

Score 3: Post adds an angle but the angle is well-known in the
discourse — "agencies should sell systems not deliverables" /
"AI tools are commoditised, AI workflows are not" / "the moat is
the data" — with no specific lived-work tying it to JR. Generic-
POV. Recognisable as JR's by voice but not by substance.

Score 5: Position the modal post on the topic does not take, OR
observation that could only have come from JR's specific corpus
— a counter-intuitive autoresearch result with named lane + score
numbers + the specific patch that fixed it; a specific scene from
an agency engagement with verifiable detail; a build measurement
that contradicts discourse consensus. The competitor-could-have-
written test fails.

Cross-reference against `programs/references/voice.md` and the
angle JSON's source_text. Identify substrate-grounded specifics
in evidence, or name the consensus position the draft restates.

Provide your reasoning, name what makes the post substitutable or
non-substitutable (with evidence), then give your score.
```

---

## Section 3 — Implementation notes

### X-9 AUTOMATIC cap — deterministic regex check

X-9's cap is deterministic. A pre-judge structural pass runs the URL regex on `[BODY]` and `[REPLY]` substrings. On match, the substrate writes `x9_cap_fired: true` + the matched substring into the judge's evidence context, and the final composer applies the score floor regardless of what the judge returns.

Regex source pattern (final form lands in `src/evaluation/slop_gate.py`):

```python
X9_URL_PATTERN = re.compile(
    r"(?P<url>https?://\S+|"
    r"\b(?:t\.co|bit\.ly|buff\.ly|lnkd\.in)/\S+|"
    r"\b[a-z0-9-]+\.(?:com|net|org|io|ai|co|app|dev)\b/?\S*)",
    re.IGNORECASE,
)
X9_TEASE_PATTERN = re.compile(
    r"🧵|^\s*1/\s|\(thread\)|↓|read on|more in replies|bookmark for later",
    re.IGNORECASE | re.MULTILINE,
)
X9_EXEMPT_QUOTE_TWEET = re.compile(
    r"^\s*quote_tweet:\s*https?://(?:www\.)?x\.com/", re.MULTILINE
)
X9_EXEMPT_MEDIA = re.compile(r"\[(?:IMAGE|VIDEO):\s*[^\]]+\]")
```

Verification order: (1) extract `[BODY]` and `[REPLY]`; (2) strip `X9_EXEMPT_MEDIA` matches; (3) strip URLs declared in `[META]` via `X9_EXEMPT_QUOTE_TWEET`; (4) run `X9_URL_PATTERN` and `X9_TEASE_PATTERN`; (5) on match, cap fires; overall fixture capped at 2 (below ship-eligible floor). The loop regenerates capped drafts automatically.

### X-6 cohort batching — cross-item over drafts/*.md

X-6 stays cross-item per the existing `SessionEvalSpec` (`session_eval_x_engine.py:210-216`). The substrate batches `drafts/*.md` (max_items=10, words_per_item=400) and passes the concatenated cohort to the judge as one evidence blob. Judge evidence lists the (source_frame, angle, voice_pillar) tuple for each draft before scoring. Source_frame = `[META] source_url:`; angle = `angles/<draft_id>.json` `interpretive_bet`; voice_pillar = `[META] voice_pillar:`. Per-draft X-6 is not separately graded.

### voice_persona corpus cross-reference

X-1 (voice register), X-2 (lived-work HARD FLOOR), and X-10 (substrate-grounded specifics) all depend on the JR voice substrate at `programs/references/voice.md`, loaded by `load_source_data()` (`session_eval_x_engine.py:166-201`). READ-ONLY for the session; judge reads it as `## Voice substrate (programs/references/voice.md)`. For post-L2 multi-operator expansion, generalises to `programs/references/voice/<operator_slug>.md` declared per-fixture as `voice_persona: <slug>` in frontmatter (same pattern Phase D storyboard.md §5 uses).

### slop_gate.py deterministic floor vs X-4 judge-graded AI tells

The slop_gate.py regex catches the 6 1-tier slop archetypes from Phase B §3 BEFORE the judge sees the draft: **LinkedIn-on-X** (≥2 of {leverage, unlock, journey, mindset, ecosystem, relentless, hustle} + emotional-arc structure + closing imperative); **thread-baiter** (`🧵 1/`, `(thread)`, `↓`); **generic-bro** (`drop a`, `like if`, `follow for more` + declarative percentage with no source); **hashtag-stuffer** (≥2 hashtags or any `#growthhacking` / `#mindset` / `#hustle`); **growth-hack-template** (`I did [activity] for [N] days. Here's what happened:` openers); **rage-bait** (universalising quantifier + negative emotional adjective + identity group + no anchor).

On any slop_gate hit, the structural gate returns a failure from `session_eval_x_engine.py:structural_gate()` and the draft never reaches the judge. X-4 grades what slips through — the **AI-laundered insight** archetype (Phase B §3.7) that regex cannot catch without false positives: sentence-length variance, paragraph-length uniformity, opener vocabulary, specificity-density vacuum.

The slop_gate.py regex set lands updated for 2026: drop em-dash density as primary signal (GPT-5.1 suppresses it); add the 2026 opener vocabulary (`Absolutely`, `Picture this`, `Here's the thing`, `It's important to note`, `delve`, `navigate`) as deterministic catches. Phase B §5.6 cites the source corpus.

### RUBRIC_VERSION hash invalidation

Single RUBRIC_VERSION bump on this spec land. Stored scores under the prior hash get archived; fresh baseline established on the first 5 post-port sessions. Reasons: (1) X-1 prose updated — AUTOMATIC ≤4 list expanded with 2026 AI-slop opener vocabulary; (2) X-4 prose rewritten — 2026 signature set replaces 2023 set; (3) X-6 prose rewritten — source-frame + angle + voice_pillar triple; (4) X-7 / X-8 / X-9 / X-10 added; (5) slop_gate.py regex set updated for 2026. The hash also invalidates on changes to `programs/references/voice.md` (X-1, X-2, X-10 cross-reference) and on changes to the slop_gate.py archetype set.

### Suggested weights

Sum to 100. Essentials = 42 (X-1 14, X-2 14, X-9 14); importants = 50 (X-3 10, X-5 10, X-6 10, X-7 12, X-8 8); pitfalls = 8 (X-4 4, X-10 4 — capping behaviour dominates weight). X-7 carries the highest important-tier weight because Phase B §4.2 names it the single highest gap in the current rubric and §5.1 elevates specificity to a ranking-layer feature in the 2026 Grok-Phoenix architecture. X-8 carries less than X-3/X-5 because reply-worthiness partly tracks structural close — double-counting risks inflation. Lands in `lane_config.x_engine.weights`. Revisit after first 10 sessions.

---

## Section 4 — Validation plan

On the first 5 x_engine sessions after this rubric lands:

**V1. X-9 catches the archived-draft external-link pattern.** Rerun the rubric against the 3 archived drafts in the 2026-05-12 v007-curated session (`jr-2026-05-08-121-001/002/003`); all three embed `https://openai.com/index/introducing-b2b-signals` in `[REPLY]`. Expected: X-9 = 1 on all three; overall fixture capped at 2; judge evidence quotes the matched URL. If any score above 2, the X-9 regex or cap-application logic is broken — investigate before running new sessions. **Binding regression test for the X-9 implementation.**

**V2. X-6 sharpened anchors penalize source-frame redundancy.** Same three-draft cohort: identical OpenAI source_url, identical interpretive bet, single voice_pillar. Expected: X-6 = 1; judge evidence lists three identical (source_frame, angle, voice_pillar) tuples. If X-6 scores ≥3, the new prose still reads wording variation as angle variation — add a deterministic source_url collision check in the substrate before the judge runs.

**V3. X-10 distinguishes contrarian vs consensus.** Generate 5 drafts on one source-frame with varied bets: consensus restatement, well-known angle, contrarian inversion grounded in JR's autoresearch corpus, named-client observation, no-anchor abstraction. Expected: consensus and no-anchor score 1; well-known angle scores 3; corpus-grounded inversion and named-client observation score 5. If the contrarian inversion does not separate from the well-known angle, X-10's adversarial prompt needs the cross-reference to voice.md to fire deterministically (substrate match → ≥4 floor).

**V4. X-7 specificity density calibration.** Rate JR's last 10 organic non-RT posts against X-7. Expected: ≥30% score ≥4. If <20%, the build/case_study density bar (≥3 proper nouns OR ≥2 numbers per 100 words) is mis-calibrated for JR's voice — do NOT lower reflexively; first check whether JR's recent posts are drifting toward abstraction. The ceiling is the point.

**V5. Ship-eligible rate calibration.** On the first 5 sessions (3-5 drafts each), JR rates each draft (ship / near-ship / skip) blind to the judge score. Expected: judge's ≥7 floor matches JR's "ship" rate at ≥70% agreement; ≥6 floor matches "ship + near-ship" at ≥70%; Phase B §6 target ≥30% ship-eligible / ≥50% near-ship. If judge ships <15%, over-strict — likely over-penalising X-7. If judge ships >50% with JR rejecting half, under-strict on slop vetos — likely missing X-4 AI-laundered signatures or X-9 native-format mismatches.

End of spec.
