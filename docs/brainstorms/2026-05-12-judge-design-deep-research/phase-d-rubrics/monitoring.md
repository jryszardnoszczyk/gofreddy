---
date: 2026-05-12
phase: D
lane: monitoring
status: final rubric spec — drops into src/evaluation/rubrics.py
---

# Phase D — `monitoring` rubric

The monitoring digest is a decision-support artifact. The client opens it on Monday morning, spends ten minutes, and exits with two or three actions for the week. The judge optimization target inherited from Phase A is therefore narrow: **decision-affecting signal per unit reading time, with zero fabrication tolerance.** A hallucinated quote in a brand-monitoring digest is not a graded weakness — it destroys the contract. The client cannot fact-check forty mentions in ten minutes; they trust the synthesis or they stop reading.

Phase C confirmed the operator's prior assessment that the existing MON-1..8 set is the strongest rubric in the system. On the Lululemon empty-data v189 artifact, every existing criterion scored 1.0 with judge anchors that matched the operator's read within one tier. Two of Phase B's seven proposed additions (MON-14 forward hooks, MON-15 missing-expected-signal) turned out to duplicate existing checklist sub-questions inside MON-7 and MON-6 — they were dropped from this spec. The remaining five Phase B proposals address gaps the existing rubric genuinely does not cover: faithfulness with auto-cap, event-cluster canonicalization, author/source weighting, stance-tagging, and channel diversity.

Two existing criteria are reshaped rather than left alone. MON-3 is split into 3a (named) and 3b (prioritized) because Phase C surfaced the failure mode where every story is correctly named but the ranking is volume-driven — the existing single-criterion form lets this slip. MON-6's pitfall anchors are tightened so the "so what" demand has more bite at score-3 boundaries.

The final set: 11 criteria, count net +3 versus the existing 8.

---

## Section 1 — Summary table

| ID | Tier | One-quality summary | Disposition |
| --- | --- | --- | --- |
| MON-1 | essential checklist | Surfaces what is DIFFERENT vs prior periods or baseline expectations (cold-start aware) | KEEP |
| MON-2 | important gradient | Severity classifications defensible against the underlying mention data | KEEP |
| MON-3a | essential gradient | Top development is named with entity + dollar + timing within first paragraph | SPLIT (was MON-3) |
| MON-3b | essential gradient | Top development is prioritized against alternatives with explicit ranking rationale, decoupled from raw volume | SPLIT (was MON-3) |
| MON-4 | important checklist | Action items carry owner, timeframe, and consequence-of-inaction | KEEP |
| MON-5 | important gradient | Compound narratives — cross-story patterns with forward hypothesis | KEEP |
| MON-6 | pitfall checklist | Every number answers "so what"; expected-but-absent signals are flagged | STRENGTHEN |
| MON-7 | optional checklist | Arc of prior digests carried forward; forward hooks for next week (cold-start aware) | KEEP |
| MON-8 | pitfall gradient | Word count proportional to importance; editorial restraint visible | KEEP |
| MON-9 | essential pitfall (auto-cap) | Source faithfulness — every quoted span and named author traces to raw mention data; fabrication caps the digest at 1 | NEW |
| MON-10 | essential checklist | Event canonicalization — same event from N syndications collapses to one cluster with primary + secondaries | NEW |
| MON-11 | important gradient | Author/source weighting — top-3 items carry rationale combining authority and amplification, not engagement alone | NEW |
| MON-12 | important checklist | Stance-tagged contested stories — rumors marked, not laundered into fact | NEW |
| MON-13 | important checklist | Channel diversity — top-10 items collectively triangulate ≥4 distinct source classes | NEW |

Final composition: **5 essential** (MON-1, MON-3a, MON-3b, MON-9, MON-10), **5 important** (MON-2, MON-4, MON-5, MON-11, MON-12, MON-13 — six but MON-13 is important and MON-2 is important; counted here as the gradient-or-checklist tiered-as-important set), **1 optional** (MON-7), **3 pitfall** (MON-6, MON-8, MON-9 auto-cap behavior). MON-9 carries both essential weight and pitfall auto-cap semantics — counted once in essential for the composite, with auto-cap as a separate constraint.

Re-count corrected: 5 essential, 6 important, 1 optional, 2 pitfall (MON-6, MON-8). MON-9's auto-cap is an essential-tier constraint, not a separate pitfall.

---

## Section 2 — Final criterion prose

### MON-1 (essential, checklist) — KEEP

```
Evaluate this monitoring digest for ONE quality:
Does the digest surface what is DIFFERENT — either compared to
prior periods, or compared to baseline expectations?

For first-week digests with no prior data, "different" means
deviations from what a naive observer would expect. Evaluate the
sub-questions accordingly — prior-period comparisons are replaced
by baseline/expectation comparisons for first digests.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does the digest quantify at least one metric with direction
   AND magnitude — either vs a prior period (before-and-after
   numbers) or vs a stated expectation (multiplier or percentile
   relative to a named baseline)?

2. Does the digest provide a comparison frame for its key data —
   whether a prior period, a stated baseline, an industry norm,
   or an explicit expectation?

3. For the most significant development reported, does the digest
   classify its trajectory — new, escalating, continuing, or
   anomalous relative to expectations?

4. Does the digest identify at least one data point that is
   surprising or noteworthy — not routine — and explain why it
   stands out from the expected pattern?

Provide your overall reasoning, then evaluate each sub-question.
Cite specific evidence from the digest and the raw mention data.
```

### MON-2 (important, gradient) — KEEP

Unchanged from existing prose. Sub-question text holds.

### MON-3a (essential, gradient) — SPLIT first half: "Named"

```
Evaluate this monitoring digest for ONE quality:
Within the first paragraph, does the reader know exactly what
the single highest-stakes development is — named with entity,
dollar amount or measurable magnitude, and timing?

Score 1: The digest opens with totals, sentiment percentages, or
a thematic summary. No single development is named in the lead.
The reader must read down to the third or fourth section to find
the top story. Or: the top story is referenced as a category
("regulatory shifts," "competitor moves") without naming the
specific event, the specific actor, or the specific number.

Score 3: The top development is named in the first paragraph
with one or two of the three required anchors (entity, dollar
or magnitude, timing) but at least one is missing or vague —
"Anthropic raised significant funding" with no number, or "a
competitor announced new pricing this week" with no name.

Score 5: Within the first paragraph the reader can answer three
questions without scrolling: who is the named entity, what is
the measurable magnitude (dollar amount, percentage move, head
count, user count), and when did it happen. If nothing
extraordinary happened this week, the digest says so plainly
in the first paragraph rather than inflating routine signals
to fill the slot.

Provide your reasoning, cite the opening paragraphs, then give
your score.
```

### MON-3b (essential, gradient) — SPLIT second half: "Prioritized"

```
Evaluate this monitoring digest for ONE quality:
Is the top development explicitly prioritized against alternatives
with a ranking rationale that is not reducible to raw mention
volume?

Score 1: The top story is the loudest story — highest mention
count, highest engagement, or highest follower-reach. No
rationale is given. Below-median-volume strategic signals
(founder tweet, regulator statement, single Bloomberg byline)
are buried below high-volume meme traffic.

Score 3: A ranking rationale is present but reduces to volume
or engagement when examined. The digest says "this matters
most because of widespread coverage" without separating
authority from amplification. At least one below-median-volume
strategic signal appears in top-3 but its placement is not
justified against the high-volume alternatives.

Score 5: The top development is explicitly weighed against the
next two or three candidates. The rationale names at least one
non-volume factor — author authority (named role, prior
verified reporting, founder/exec status), recency-of-first-
report, strategic consequence, or regulatory weight. At least
one top-3 story has below-median volume but above-median
strategic importance, and the digest names why that ranking is
correct. The reader can disagree with the specific call rather
than the entire prioritization apparatus.

Provide your reasoning, cite the ranking rationale (or its
absence), and compare against raw mention volumes. Then give
your score.
```

### MON-4 (important, checklist) — KEEP

Unchanged.

### MON-5 (important, gradient) — KEEP

Unchanged. The existing prose already demands cross-story synthesis with conditional forward projection — no calibration change needed.

### MON-6 (pitfall, checklist) — STRENGTHEN

```
Evaluate this monitoring digest for ONE quality:
Does every number in the digest answer "so what?" — and does
the digest examine expected signals that are missing?

Pitfall criterion: failure here flags decision-support
inflation, not stylistic weakness. A digest that lists
percentages without consequence is a vendor count-table
disguised as analysis.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is every statistic in the digest accompanied by a
   decision-relevant interpretation — paired with a comparison,
   baseline, or stated implication that names what the client
   should do or watch? Raw numbers ("247 mentions, +34% WoW")
   without a "so what" clause attached fail this check. A
   statistic followed only by "this represents continued
   interest" or "sentiment remains positive" also fails — the
   so-what must be specific to the client's actions or watch
   set.

2. Is at least one statistic presented with a comparative
   frame that gives it meaning (versus prior period, versus
   competitors, versus industry baseline, versus stated
   expectation)? "Up from baseline" without naming the
   baseline value fails.

3. Does the digest flag at least one expected signal that is
   ABSENT — a campaign that generated no coverage, a
   competitor that went quiet, a response that never came,
   a scheduled launch that drew no community discussion?
   The absence must be named (specific topic, specific actor)
   with a stated expectation basis ("X had a launch Tuesday;
   absent from community channels — unusual"). Generic "didn't
   see much about pricing this week" fails.

4. When a number is cited, does the digest explain its
   implication for the client's actions — not just what the
   number is, but what the client should do, watch, or escalate
   because of it?

Provide your overall reasoning, then evaluate each
sub-question. Cite specific evidence from the digest and the
raw mention data. A digest scoring 0/4 or 1/4 should be read
as: the synthesizer aggregated rather than synthesized.
```

### MON-7 (optional, checklist) — KEEP

Unchanged. Phase C confirmed sub-question 4 ("forward hooks") already covers the watch-next-week behavior that Phase B initially proposed as a new MON-14.

### MON-8 (pitfall, gradient) — KEEP

Unchanged.

### MON-9 (essential, AUTO-CAP) — NEW

```
Evaluate this monitoring digest for ONE quality:
Do all quoted spans, named authors, and source attributions
trace verifiably to the raw mention data?

This criterion carries an AUTO-CAP. If ANY of the following
is confirmed, the digest's score for MON-9 is clamped at 1
regardless of other strengths, AND the overall composite
score is capped at 2.0:

  a. A quoted span ("...") attributed to a named author or
     outlet where the source corpus contains no such text.
  b. A named author/handle that does not appear in the source
     corpus and cannot be resolved to a real public account or
     byline.
  c. A named outlet ("TechFinance Weekly," "AI Insider Daily")
     that does not exist and has no public web presence.
  d. A numeric claim (percentage, dollar figure, follower
     count) presented as derived from a mention but absent
     from the cited mention data.

Score 1: At least one fabrication confirmed per above. The
digest is structurally unreliable; the auto-cap applies.

Score 3: All sampled quotes trace to a real author and outlet,
but at least one shows a mismatch — paraphrased text presented
as verbatim, engagement counts inflated, or timestamp wrong by
more than one day. No fabricated entities, but precision is
loose.

Score 5: A random sample of five quoted spans and three named
authors round-trips verbatim against the source corpus.
Verbatim text matches byte-exact (allowing for typographic
normalization of quote marks). Handles exist and are
resolvable. Timestamps and engagement counts match the
mention snapshot. Numeric claims have a clear in-corpus
origin.

Verification procedure:
  1. Sample five quoted spans from the digest body.
  2. For each, search the raw mention data (cross-referenced
     below) for the verbatim text or its closest paraphrase.
  3. For each named author or outlet appearing in the digest,
     confirm presence in the source corpus or resolvable
     public identity.
  4. For each numeric claim attributed to a source, confirm
     the underlying figure appears in the source data.

Cross-reference: the judge has access to the retrieved mention
corpus for the digest's week. If the corpus is empty (no
mentions retrieved), this criterion is N/A for the digest;
score it 5 and note "empty-corpus N/A" in reasoning. The
auto-cap does not fire on empty-corpus digests.

Provide your reasoning, cite the specific sampled quotes and
their cross-reference outcomes, then give your score. If the
auto-cap fires, state explicitly: "AUTO-CAP TRIGGERED —
fabrication confirmed at <quote/author/outlet>."
```

### MON-10 (essential, checklist) — NEW

```
Evaluate this monitoring digest for ONE quality:
Do same-event mentions across multiple syndicating sources
collapse to one canonical story with a named primary source,
or does the digest inflate distinct-story count by treating
syndications as independent events?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. For each top-5 story, is there exactly ONE primary source
   named (the originating reporter, the first-publishing
   outlet, the originating account)? Stories that cite
   "Bloomberg, Verge, TechCrunch, Wired" without distinguishing
   which one broke the story fail this check.

2. Are secondary sources listed separately from the primary,
   ranked by author authority rather than by repost count?
   A list of seven outlets all paraphrasing the same Bloomberg
   piece, presented as seven independent corroborations,
   fails — the digest is laundering duplication as breadth.

3. Are there zero URL or near-duplicate-headline overlaps
   between top-5 stories? If the same article URL or near-
   identical headline appears in two of the top-5 entries,
   the canonicalization failed: one event has been counted
   twice.

4. If the digest reports raw mention volume, does the
   distinct-story count make sense against it? A digest
   citing "247 mentions this week" should resolve to fewer
   than ~30% of that as distinct stories (the documented
   syndication ratio in commercial monitoring tools). A
   digest claiming "247 mentions, 198 stories" indicates
   no dedup occurred.

Provide your overall reasoning, then evaluate each
sub-question. Cite specific evidence from the digest and
the raw mention data. If the digest is empty-corpus or
explicitly states "no significant events this week," this
criterion is N/A and should score 5 with the explicit note.
```

### MON-11 (important, gradient) — NEW

```
Evaluate this monitoring digest for ONE quality:
Do the top stories carry weighting rationale that combines
author authority and amplification separately, rather than
collapsing both into raw engagement?

Score 1: Stories are ordered by engagement, mention count,
or follower-reach. No rationale is given for why this
ordering reflects strategic importance. A 50K-like anonymous
meme outranks a founder tweet at 200 likes.

Score 3: Each top-3 story carries a numeric strength score
or qualitative tag, but inspection shows it reduces to
engagement. The digest says "high evidence strength: 5K
retweets" — engagement laundered as authority. No named
author role appears in the rationale.

Score 5: Each top-3 story has a one-or-two-sentence
weighting rationale that names BOTH dimensions explicitly:
  - Author authority: role (founder / CMO / verified
    journalist / regulator / first-time-observed account),
    prior verified reporting record, public-identity
    resolvability.
  - Amplification: reach, engagement, secondary pickups,
    cross-platform spread.
These dimensions are presented as separate inputs to the
weighting decision, not as a single conflated number. At
least one top-3 story has below-median amplification but is
ranked high based on authority weight; the rationale names
this trade-off explicitly.

Provide your reasoning, cite the specific weighting
rationales (or their absence), and compare against raw
mention engagement data. Then give your score.

If the digest is empty-corpus, this criterion is N/A — score
5 with the explicit note.
```

### MON-12 (important, checklist) — NEW

```
Evaluate this monitoring digest for ONE quality:
Are contested, rumor-flavoured, or single-source stories
explicitly tagged with a verification status, rather than
laundered into fact?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. For any story whose evidence rests on a single source, an
   anonymous account, or unverified speculation, does the
   digest tag it explicitly — "unverified," "rumor," "single
   source," or "pending confirmation"? Stories asserted in
   declarative voice when the underlying evidence is a single
   speculative tweet fail this check.

2. For breaking events where mentions show a mix of support
   and denial, does the digest signal the contestation
   ("mixed reception," "denied by [named party]," "company
   has not commented")? A breaking-event story presented with
   only the supporting mentions, omitting the denials present
   in the source corpus, fails.

3. When the digest cites a stakeholder response or absence of
   response, is the response-state explicit ("X declined to
   comment," "X has not yet responded," "X confirmed via Y")?
   Generic "the company is reportedly considering..." without
   sourcing the report fails.

4. Are forward projections derived from rumor-flagged stories
   themselves flagged as conditional? A "next week watch"
   item built on an unverified rumor must inherit the
   uncertainty tag.

The criterion does NOT require the digest to have rumor-
flagged stories. A digest that explicitly states "no
rumor-flavoured or single-source stories this week — all
top items cross-confirmed by ≥2 independent outlets" passes
trivially with YES on all four sub-questions.

Provide your overall reasoning, then evaluate each
sub-question. Cite specific evidence from the digest and the
raw mention data.
```

### MON-13 (important, checklist) — NEW

```
Evaluate this monitoring digest for ONE quality:
Do the top-10 items in the digest collectively triangulate
across distinct source-class channels, or does the digest
echo a single-platform conversation?

Source classes (distinct platform-types, not distinct
accounts): X / Reddit / news outlets / LinkedIn / podcasts /
trade press / forums / industry blogs / review platforms /
private community (Substack, Discord, Slack) / regulatory
filings / company-direct (blog, press release).

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Do the top-10 items collectively cite mentions from at
   least 4 distinct source classes? A top-10 that is 9 X
   posts plus one Reddit thread fails. A top-10 spanning
   X + Reddit + Bloomberg + LinkedIn + a podcast clip
   passes.

2. Is no single source class responsible for more than 60%
   of the top-10 items? Heavy X-skew is the most common
   failure mode — the synthesizer used the X API and called
   it monitoring.

3. For at least one top-3 story, is the triangulation
   explicit — the same event corroborated across ≥2 distinct
   source classes (e.g., X founder tweet + Bloomberg byline,
   not X + X-repost)?

4. Where the raw mention corpus shows multi-channel signal
   but the digest only surfaces one channel, is this gap
   acknowledged ("most signal this week came from X; note
   we have weaker coverage of trade press this week")?

If the corpus is empty or single-channel by design (e.g., a
brand whose monitoring scope is intentionally X-only), the
digest should state this explicitly — and the criterion
passes if the gap is named. A digest that silently single-
channels without acknowledgment fails.

Provide your overall reasoning, then evaluate each
sub-question. Cite specific evidence.
```

---

## Section 3 — Implementation notes

### MON-9 auto-cap mechanism

The auto-cap is enforced in two layers:

1. **Judge prompt** (above): the prompt itself instructs the model to set score=1 and to print the string `AUTO-CAP TRIGGERED — fabrication confirmed at <span>` when any of the four trigger conditions are met. The prompt is anchored by the existing pitfall-criterion pattern in MON-6 and MON-8, so the judge has prior pattern-evidence that a single failure mode collapses the score.

2. **Post-judge composite clamp**: after the judge returns its per-criterion score set, the composite-aggregation step in `score_variant.py` checks whether MON-9 returned a score of 1. If yes, the overall composite for the digest is clamped at 2.0 regardless of other criterion scores. This prevents an otherwise-strong digest with a fabricated quote from scoring 7+ on composite while showing a 1 on MON-9 — the composite must reflect the structural unreliability.

The clamp is mechanical, not judgmental. Implementation: add an `auto_cap_rules` dict to the monitoring `RubricTemplate` set, keyed by criterion ID, with value `{"trigger_score": 1, "composite_max": 2.0}`. The composite calculator reads this dict before averaging.

### MON-9 cross-reference to raw mention data

The judge needs access to the source mention corpus for the digest's week. The existing monitoring lane already passes `monitoring.json` (or the per-week equivalent file with raw retrieved mentions) into the judge context — confirmed by the existing MON-1 and MON-6 prompts both referring to "the raw mention data" in their cite-evidence lines.

For MON-9 verification, the judge:

1. Receives the digest body + the raw mention corpus (JSON of all retrieved mentions for the week — text, author handle, URL, timestamp, engagement snapshot).
2. Samples five quoted spans from the digest.
3. For each, performs a substring match against the corpus mention text (after normalizing curly quotes to straight, collapsing whitespace).
4. If no match within 90% token overlap, flags the span as unverifiable.
5. Independently confirms named authors against the corpus author-handle list.

Cross-reference path convention: the monitoring lane writes raw retrieval to `<run_dir>/mentions/<week>.json` (e.g., `runs/v189/monitoring/lululemon/mentions/2026-W19.json`). The judge harness passes this file's contents into the judge prompt alongside `digest.md`. If the file is absent or empty, MON-9 returns the empty-corpus N/A path.

### MON-10 canonicalization counting mechanism

The judge counts events, not source citations. Concretely:

1. For each top-5 story in the digest, extract the cited URLs and the primary-source claim (the outlet/author named as "originating" or first).
2. Build a URL set across top-5 stories. The set should contain at most one entry per article URL — duplicate URLs across stories indicate dedup failure.
3. For near-duplicate detection beyond URL match, the judge compares headlines and primary content; MinHash similarity ≥0.85 between two stories' primary-source content is the threshold for "this is the same event."

The judge does not need to compute MinHash itself. The Phase B research notes that MinHash LSH at 0.85 is the industry baseline; the judge applies the principle qualitatively — "if these two stories describe the same underlying event with the same primary actor and the same triggering action, they should have been one story."

### MON-11 / MON-12 / MON-13 raw-data cross-reference

All three of these criteria reference the raw mention corpus the same way MON-1, MON-6, and MON-9 do. The judge prompt explicitly instructs the model to "cite specific evidence from the digest and the raw mention data" — preserving the existing rubric's strongest pattern (cross-artifact ground-truth verification, identified in Phase A as the most defensible criterion shape).

For MON-13 in particular: the raw mention corpus already carries `source_type` or `platform` metadata per mention (X / Reddit / news / etc.). The judge tallies source classes across top-10 items by reading the digest's per-story source field, then optionally cross-checking against the corpus's source distribution.

### Existing cross-references preserved

- MON-1, MON-6, MON-9, MON-10, MON-11, MON-12, MON-13 all reference the raw mention corpus.
- MON-7 references prior digests — already implemented via the digest's `prior_digest_ref` field per existing monitoring lane convention.
- No new file dependencies are added beyond `mentions/<week>.json` which already exists.

### RUBRIC_VERSION hash invalidation

This spec changes the monitoring rubric set materially. The `RUBRIC_VERSION` constant in `src/evaluation/rubrics.py` must be bumped on landing. Specifically:

- MON-3 prose changes (split into 3a and 3b — two distinct templates).
- MON-6 prose strengthens with sharper sub-question 1 and 3 anchors.
- MON-9, MON-10, MON-11, MON-12, MON-13 are new templates.
- The `MONITORING_RUBRICS` registry expands from 8 to 13 entries.

Per the existing cache-invalidation convention, bumping `RUBRIC_VERSION` invalidates all cached monitoring scores. The evolution loop's first generation post-landing will re-score every variant against the new rubric — this is the intended behavior. Old composite scores from the prior rubric are not directly comparable to new composites; the lineage tracker should flag the version boundary.

### Tier weight convention

Tier weights inherit the existing monitoring lane convention (essential criteria weighted ~1.5x, important ~1.0x, optional ~0.5x, pitfall ~1.0x with binary or capped failure mode). The auto-cap on MON-9 supersedes the tier-weight composite calculation when triggered — clamp first, then weight-average otherwise.

---

## Section 4 — Validation plan

The new rubric requires validation on real client digests before being trusted for evolution-loop fitness. Phase C could not validate MON-9 through MON-13 on the Lululemon v189 archive because Lululemon's digest was empty-corpus — no quotes, no events to canonicalize, no sources to weight.

### First-five-client-digest validation

After landing, run the new rubric against the first five monitoring digests that have non-empty mention corpora. For each:

1. **Score each digest with the full MON-1..13 set.** Capture per-criterion scores plus composite.
2. **Hand-rate the same digest** (operator-graded baseline using the same anchor prose). Compare hand-grade vs judge-grade per criterion. Flag any criterion where the gap exceeds 1 tier.
3. **Specifically inspect MON-10 and MON-13** outputs. These are the criteria most likely to under-fire (judge accepts inflation as breadth) or over-fire (judge penalizes legitimate single-source stories). Calibrate anchors if gap appears.

### Synthetic-fabrication test for MON-9

Because MON-9 is the most consequential new criterion (it triggers the composite auto-cap), it needs a targeted deliberate-failure test:

1. Take one passing digest from the first-five batch with a non-empty corpus and a 5-tier MON-9 score (all quotes round-trip cleanly).
2. Synthetically inject a fabricated quote into the digest. Concretely: insert a quoted line attributed to a named author who appears nowhere in the mention corpus, with quote text that has no substring match in any retrieved mention.
3. Re-run MON-9 on the modified digest. **Expected outcome:** the judge returns score=1, prints the `AUTO-CAP TRIGGERED` marker, and the composite clamp engages — composite returns ≤2.0 regardless of other criterion scores.
4. If the judge does not detect the fabrication, the auto-cap prompt language is insufficiently specific — strengthen the verification-procedure section of the prompt before deploying.

Three variations of the test should be run:
- **Variation A:** quote text is fabricated, author is real (exists in corpus).
- **Variation B:** quote text is plausible-looking but attributed to a non-existent handle.
- **Variation C:** outlet is fabricated ("AI Insider Daily" type), quote text plausible.

All three should trigger the auto-cap. If any escapes, the prompt language for that variation is the calibration target.

### Cold-start digest validation

A specific test for first-week digests with no prior data: confirm that MON-1, MON-7, and MON-9 all handle the cold-start path correctly. The Lululemon case (v189) is the existing precedent for this — empty corpus, first-week framing, all four cold-start-aware criteria scored 5/5 with no false-positive penalties. Re-run after the rubric expansion to confirm the cold-start path still holds with MON-9 through MON-13 added.

### Failure-mode hostility checks

Beyond the synthetic-fabrication test, the validation pass should deliberately try to break each new criterion:

- **MON-10:** present a digest where the same Bloomberg article is cited under three different top-5 stories using paraphrased headlines but the same URL. Expected: dedup failure flagged, score ≤2.
- **MON-11:** present a digest where every top-3 weighting rationale reduces to "high engagement." Expected: judge identifies engagement-laundering, score ≤3.
- **MON-12:** present a digest that asserts a rumored acquisition in declarative voice with no verification tag, despite the source corpus showing it as a single anonymous tweet with denials elsewhere. Expected: score ≤2 on sub-questions 1 and 2.
- **MON-13:** present a 9-of-10-from-X digest with no acknowledgment of the channel skew. Expected: score ≤2.

Each hostility test confirms the rubric catches the failure mode the operator and Phase B research identified. If any criterion fails its hostility test, the prompt's anchor prose needs to be tightened before that criterion is trusted for evolution-loop fitness scoring.

### Re-validation cadence

After initial validation against the first five real-corpus digests + synthetic + hostility tests, the rubric should be re-validated once per quarter or after any of:

- Major change to retrieval pipeline (new source classes added).
- Major change to digest generation prompt structure.
- Operator-observed drift between judge scores and operator hand-grades on shipped digests.

The monitoring rubric is the system's gold standard per the Phase C verdict. The validation cadence preserves that status as both the rubric and the lane evolve.

---

Wrote phase-d-rubrics/monitoring.md. Final count: 13 criteria (5 essential, 6 important, 1 optional, 2 pitfall — with MON-9 carrying an additional essential-tier auto-cap constraint that clamps the composite to ≤2.0 when fabrication is confirmed). Key change vs current MON-1..8: adds the missing fabrication check as a composite-clamping auto-cap (MON-9), adds event canonicalization (MON-10), splits MON-3 into named+prioritized to catch the volume-driven-ranking failure mode Phase C surfaced, and adds three important-tier criteria (MON-11 author/source weighting, MON-12 stance-tagging, MON-13 channel diversity) that close the source-faithfulness and triangulation gaps Phase B's industry research documented.
