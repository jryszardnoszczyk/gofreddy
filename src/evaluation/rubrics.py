"""Rubric templates for the 32-criteria evaluation system.

Each rubric is either:
- gradient: scored on a 1/3/5 scale with anchor descriptions
- checklist: 4 binary YES/NO sub-questions

Domains: geo (8), competitive (8), monitoring (8), storyboard (8)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RubricTemplate:
    criterion_id: str       # e.g. "GEO-1"
    domain: str             # "geo", "competitive", "monitoring", "storyboard"
    scoring_type: str       # "gradient" or "checklist"
    prompt: str             # The full rubric prompt text
    is_cross_item: bool = False  # True for GEO-6 and SB-8
    # Stream C C5 (RaR — arXiv 2507.17746): tier weight applied during
    # weighted-composite aggregation. Default ``important`` preserves
    # uniform behavior when all criteria share the default; mixing tiers
    # makes essential criteria dominate the score and optional ones recede.
    tier: str = "important"   # essential | important | optional | pitfall


# Stream C C5: RaR tier weights (verbatim from arXiv 2507.17746). Applied
# by ``weighted_composite`` and by ``evaluate_variant._apply_tier_weights``
# under ``AUTORESEARCH_RAR_TIER_WEIGHTS``.
TIER_WEIGHTS: dict[str, float] = {
    "essential": 1.0,
    "important": 0.7,
    "optional": 0.3,
    "pitfall": 0.8,
}


def weighted_composite(scores: list[float], tiers: list[str]) -> float:
    """Apply RaR tier-weighted aggregation to per-criterion scores.

    Returns ``Σ(w_i · score_i) / Σ(w_i)`` on the same scale as the inputs.
    Pitfall criteria score the same way as the others — a low score on a
    pitfall criterion means the pitfall was *violated* and that score
    contributes ``w · 0`` to the numerator (penalty), while a high score
    means the pitfall was *avoided* and contributes ``w · max`` (reward).
    The weight is part of the denominator either way.

    Returns ``0.0`` when inputs are empty, length-mismatched, or when the
    weight sum collapses to zero (so callers can detect the no-op case).
    """
    if not scores or len(scores) != len(tiers):
        return 0.0
    weights = [TIER_WEIGHTS.get(t, TIER_WEIGHTS["important"]) for t in tiers]
    weight_sum = sum(weights)
    if weight_sum == 0:
        return 0.0
    return sum(w * s for w, s in zip(weights, scores)) / weight_sum


# ---------------------------------------------------------------------------
# Domain prefix instructions
# ---------------------------------------------------------------------------

GEO_PREFIX = """\
Ignore the agent metadata in the file header: Strategy, Primary Angle,
Attempt number, Baseline scores, Writing style. These are internal
to the optimization process and not part of the content quality.
DO use the target queries declared in the header — those define what
the content should answer. Evaluate the content blocks: [INTRO],
[FILL], [FAQ], [HOWTO], [SCHEMA] sections."""

SB_PREFIX = """\
Ignore the why_this_works field entirely — it is the agent's
self-justification. Evaluate only: story_beats, voice_script,
scenes, emotional_map, protagonist, supporting_characters."""


# ---------------------------------------------------------------------------
# GEO — Generative Engine Optimization (8 rubrics)
# ---------------------------------------------------------------------------

_GEO_1 = """\
Evaluate this optimized page content for ONE quality:
Could an AI search engine extract any single content block and use
it as a complete answer — no meaning lost, no clicking required?

Score 1: Content blocks depend on surrounding context to make sense.
Paragraphs reference "as mentioned above" or assume prior reading.
An AI engine extracting a single block would deliver an incomplete
or confusing answer.

Score 3: Some blocks are self-contained, but others rely on context
from the page header or adjacent sections. A mixed result — an AI
engine would succeed with some extractions but fail with others.

Score 5: Every content block reads as a standalone answer to a real
question. Each contains its own context, specific claims, and a
complete thought. An AI engine could extract any paragraph and the
reader would understand it without visiting the page.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

_GEO_2 = """\
Evaluate this optimized page content for ONE quality:
Are the claims specific and concrete, with details a reader could
independently verify?

Score 1: Claims are generic, unverifiable, or outdated. The content
uses hedge-words and round numbers, such as "affordable pricing,"
"thousands of customers," or "industry-leading performance."
No specific figure could be fact-checked or confirmed as current.

Score 3: Some claims include specific numbers or named entities,
but specificity is inconsistent. Concrete details appear alongside
vague filler. A fact-checker could verify some claims but would
find others unsupported.

Score 5: Claims are consistently specific, current, and traceable.
The content provides details such as pricing tiers, feature counts,
named integrations, or dated benchmarks that a reader could
independently verify as accurate today. Specificity serves the
argument rather than padding word count.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

_GEO_3 = """\
Evaluate this optimized page content for ONE quality:
Does the content acknowledge where the client genuinely loses to
competitors?

AI search engines give higher citation weight to sources that
demonstrate balanced assessment. First-party content that only
praises the brand has a natural credibility ceiling.

Score 1: The content presents the client as superior in every
dimension. No competitor advantage is acknowledged. Comparison
tables show the client winning every row. The tone is promotional,
not analytical.

Score 3: The content acknowledges competitors exist and may note
a general area where alternatives have strengths, but avoids
naming specific advantages or quantifying where the client falls
short.

Score 5: The content explicitly names at least one area where a
specific competitor genuinely wins — and explains why. The honesty
is specific enough that a reader could verify or dispute it,
not a generic acknowledgment that "some competitors have
different strengths." This builds
credibility that makes the client's real advantages more citable.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

_GEO_4 = """\
Evaluate this optimized page content for ONE quality:
Does the new content read like it was always part of this page —
not bolted on?

Score 1: The content clashes with the page's existing voice, tone,
or structure. It introduces terminology, formatting, or a level
of detail inconsistent with the surrounding content. A reader
would notice the seam between original and added material.

Score 3: The content roughly matches the page's voice but has
minor inconsistencies — a shift in formality, a different heading
style, or an abrupt topic transition that reveals the addition.

Score 5: The content is indistinguishable from the original page
in voice, structure, and scope. Placement instructions are precise
enough for a developer to implement without interpretation. The
content addresses what this specific page can realistically
achieve, not generic improvements.

Compare the optimized content against the provided original page
content (pages/{{slug}}.json) to assess voice, tone, and structural
consistency.

Provide your reasoning, cite specific evidence from the content
and the original page, then give your score."""

_GEO_5 = """\
Evaluate this optimized page content for ONE quality:
Does the content include claims attributed to named first-party
sources — and is that attribution visible in the text?

Score 1: The content describes industry-general concepts or repeats
publicly available statistics. No claim is attributed to a
company-internal source (named methodology, internal data with stated
collection method, company-specific technical choices).

Score 3: Some content references first-party methodology or internal
data, but it is mixed with generic material and attribution is thin.
A reader sees first-party-flavored content but cannot confidently
point to which claims are company-sourced.

Score 5: The content explicitly attributes specific claims to
first-party sources — named proprietary methodology with a described
mechanism, internal data with a stated collection window or method,
technical decisions attributed to the company's engineering choices.
A reader can trace each first-party claim, from the content itself,
to a company-internal origin.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

_GEO_6 = """\
Evaluate the set of optimized pages below for ONE quality:
Does each page use a genuinely different primary angle, or do
pages repeat the same differentiators, statistics, and framing?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does each page lead with a different primary differentiator
   or competitive angle? (No two pages open with the same
   positioning claim.)

2. Are the statistics and data points used across pages distinct?
   (The same number or benchmark does not appear as a key claim
   on more than one page.)

3. Do the FAQ sections across pages ask genuinely different
   questions? (No FAQ question is repeated or trivially
   rephrased across pages.)

4. Would the pages reinforce each other as a site — each
   contributing a different facet of the company's value — rather
   than competing for the same queries?

Provide your overall reasoning, then evaluate each sub-question."""

_GEO_7 = """\
Evaluate this optimized page content for ONE quality:
If a user typed each declared target query into an AI search
engine, would this page provide a satisfying answer?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does the content contain a specific passage that directly and
   completely answers each target query declared in the page
   header? (Not tangentially related — directly and completely
   responsive.)

2. Does the content match the search intent behind each query?
   (Informational queries get explanations, commercial queries
   get comparisons, transactional queries get pricing and next
   steps.)

3. Is the answer to each target query findable within the first
   few paragraphs of the relevant content block — not buried
   deep in the page?

4. Would the answer satisfy the user without requiring them to
   click through to another page for the core information?

Provide your overall reasoning, then evaluate each sub-question."""

_GEO_8 = """\
Evaluate this optimized page content for ONE quality:
Do the technical recommendations reference actual problems found
on this specific page, with enough detail to act on?

Score 1: Recommendations are generic boilerplate that could apply
to any website. "Consider adding alt text to images" or "Improve
page speed" without referencing what is actually wrong on this
page. No specific elements, counts, or URLs are named.

Score 3: Some recommendations reference actual page elements (such
as a specific heading or section), but others are generic advice
not tied to observed problems. A developer could act on some items
but would need to investigate others.

Score 5: Every recommendation names a specific problem observed on
this page — with counts, element locations, or URLs that tie the
recommendation to evidence in the audit data. A developer could
implement each fix without additional investigation because the
problem, location, and fix are all specified.

Cross-reference the recommendations against the provided original
page content (pages/{{slug}}.json) to verify the problems actually
exist on this page. Specific-sounding recommendations that
reference fabricated problems should score low.

Provide your reasoning, cite specific evidence from the content
and the original page data, then give your score."""


# ---------------------------------------------------------------------------
# Competitive Intelligence (8 rubrics)
# ---------------------------------------------------------------------------

_CI_1 = """\
Evaluate this competitive intelligence brief for ONE quality:
Can a reader state the brief's central argument in one sentence
after reading only the executive summary?

A brief organized around a central thesis uses every section to
build, support, or qualify that argument. The reader finishes
knowing what the competitive landscape means for the client's
strategy — not just what competitors are doing.

Score 1: The executive summary lists observations about individual
competitors. Each section introduces its own topic without
connecting back to a shared argument. The reader finishes knowing
facts but no conclusion.

Score 3: The executive summary implies a direction but does not
state a crisp thesis. Sections are loosely related but the
organizing argument is not explicit. The reader could infer a
central point but would need to assemble it from pieces.

Score 5: The executive summary states a single strategic position.
Every subsequent section provides evidence for, against, or nuance
to that position. The reader finishes knowing exactly what the
competitive landscape demands of the client.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

_CI_2 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the reasoning chain from evidence to conclusion stay
proportionate — no conclusion outruns its data?

NOTE: This criterion does NOT check whether numbers are fabricated
(data grounding handles that). It checks whether the reasoning
chain from evidence to conclusion is proportionate.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every factual claim in the brief name a specific data
   source (such as a tool, API, publication, or URL) rather than
   generic references like "research shows" or "industry data"?

2. Does every factual claim carry an explicit confidence qualifier
   with a stated basis — rather than presenting all claims with
   equal certainty?

3. When a conclusion is drawn from limited data, does the brief
   acknowledge the limitation in a way that adjusts confidence
   proportionally — rather than presenting tentative findings with
   the same language as well-supported ones?

4. For the brief's key findings, does it consider at least one
   alternative explanation — or does it present each
   interpretation as the only possible reading of the data?

Provide your overall reasoning, then evaluate each sub-question."""

_CI_3 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief describe each competitor's direction of change —
what they are building toward, their rate of change, and what
they are abandoning?

Score 1: Competitors are described as static snapshots — current
products, current pricing, current positioning. No mention of
what has changed recently, what is being built, or what has been
abandoned. The brief reads like a catalog, not an intelligence
report.

Score 3: The brief mentions some directional signals (such as a
recent product launch or a pricing change) but does not synthesize
them into a trajectory. Direction is anecdotal, not systematic.

Score 5: Each competitor's trajectory is explicitly articulated —
what they are investing in, how fast they are moving, and what
they have deprioritized or abandoned. The brief helps the reader
anticipate what each competitor will do next, not just what they
are doing now.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

_CI_4 = """\
Evaluate this competitive intelligence brief for ONE quality:
Could the client actually execute these recommendations given
their known constraints?

You have been provided a client context document (from
_client_baseline.json and session.md). Use it to verify whether
recommendations fit the client's actual products, scale, team
structure, and competitive situation.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is every recommendation specific enough to act on without
   further interpretation — a clear action plus target rather than
   a "consider implementing" or "explore" direction?

2. Does every recommendation include a dated deadline or bounded
   timeframe rather than open-ended language ("soon," "as appropriate,"
   "when ready")?

3. Does each recommendation acknowledge the effort or resources
   required — sized in concrete engineering terms (hours, sprints,
   team composition) — not just what to do but how much it costs
   to do it?

4. Are the recommendations consistent with the client's
   demonstrated capabilities, team size, and resources as
   described in the client context document? (A recommendation
   requiring a dedicated data science team fails this check if
   the client has no data science function.)

Provide your overall reasoning, then evaluate each sub-question."""

_CI_5 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief name specific gaps and, for each, cite a specific
client capability that makes the gap a fit for THIS client in
particular?

Score 1: The brief identifies general market gaps without connecting
them to the client's specific capabilities. Opportunities are stated
as if any company in the category could pursue them.

Score 3: The brief identifies gaps and loosely connects them to the
client, but the connection is generic — no specific client capability,
data asset, team strength, or market position is named as the reason
this client fits this gap.

Score 5: For each named gap, the brief cites a specific client
capability — named technology component, named data asset, named team
expertise, or measurable market position — that makes this gap a fit
for THIS client in particular. The pairing is observable in the text.

Provide your reasoning, cite specific evidence from the brief and
the client context document, then give your score."""

_CI_6 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief contain findings that challenge the client's
current approach, reveal competitor advantages the client cannot
quickly close, or surface internal contradictions in its own data?

You have been provided a client context document (from
_client_baseline.json and session.md). Check the client's stated
positioning and known beliefs. If the brief only reinforces what
the client already believes about itself, it probably missed
something.

Score 1: The brief only reinforces the client's existing beliefs.
Every finding positions the client favorably. No competitor
advantage is presented as durable or difficult to overcome. No
finding contradicts any other finding. The brief is optimized to
make the client feel good.

Score 3: The brief acknowledges some challenges but softens them
with immediate counters ("while Competitor X leads in this area,
the client's broader platform compensates"). The uncomfortable
facts are present but cushioned. Or: findings that contradict
each other are not acknowledged as contradictions.

Score 5: The brief states at least one finding that a client
stakeholder would push back on — a durable competitor advantage,
a structural weakness in the client's approach, or a market trend
that undermines the client's strategy. When findings contradict
each other or the client's stated positioning, the brief says so
explicitly. Uncomfortable truths are specific, evidence-based,
and not immediately neutralized.

Provide your reasoning, cite specific evidence from the brief
and the client context document, then give your score."""

_CI_7 = """\
Evaluate this competitive intelligence brief for ONE quality:
After reading the brief, does the reader know which 2-3 actions
drive disproportionate impact?

Score 1: All findings and recommendations receive equal treatment.
Everything is presented as important. The reader finishes with a
long list but no sense of what matters most. Priority language is
absent or applied to everything.

Score 3: The brief suggests some items are more important than
others, but the separation is soft. The reader could identify a
rough priority order but would need to re-read to confirm it.

Score 5: The 2-3 highest-impact actions are unmistakably separated
from secondary items — through explicit ranking, section
structure, or emphasis. The reader finishes knowing exactly what
to do first and why those actions outrank everything else.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

_CI_8 = """\
Evaluate this competitive intelligence brief for ONE quality:
When data sources failed or returned incomplete results, does the
brief recalibrate its analysis around what it actually has?

You have been provided the session's Data Sources, Data Quality
Notes, and Dead Ends sections (from session.md), plus raw
competitor data with data_tier fields. Cross-reference the brief's
gap acknowledgments against these actual records. A brief that
fabricates which data sources failed — or silently omits real
gaps — should score low.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does the brief accurately name which data sources failed or
   had limited coverage — matching the actual gaps documented in
   the session data quality notes and competitor data_tier fields?

2. Does the brief state which analyses became impossible or
   degraded due to missing data — rather than silently omitting
   those sections?

3. Are confidence levels and conclusions adjusted downward for
   competitors or findings affected by data gaps? (Check: does a
   competitor with "detect-only" data_tier get compared on equal
   footing with one that has "full" data? It should not.)

4. Does the brief treat the data gap itself as an intelligence
   finding — explaining what the absence of data might mean —
   rather than simply noting it and moving on?

Provide your overall reasoning, then evaluate each sub-question."""


# ---------------------------------------------------------------------------
# Monitoring Digest (8 rubrics)
# ---------------------------------------------------------------------------

_MON_1 = """\
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
Cite specific evidence from the digest and the raw mention data."""

_MON_2 = """\
Evaluate this monitoring digest for ONE quality:
Given the raw mention data, are the severity classifications
(crisis / opportunity / noise) defensible?

Score 1: Severity classifications bear little relationship to the
underlying data. Routine signals are labeled as crises, or genuine
risks are dismissed as noise. Confidence levels are missing or
detached from the evidence. The reader cannot trust the triage.

Score 3: Most classifications are reasonable and confidence levels
are stated, but basis is thin or missing for some. Coverage gaps
are acknowledged but their impact on severity is uneven — some
assessments are adjusted while others treat degraded data as
equivalent to full data.

Score 5: Every classification is defensible given the data.
Confidence levels are stated inline with a named basis — source
count, coverage duration, or other quantified evidence — not just
a bare HIGH/MEDIUM/LOW label. When classification is a judgment
call, the digest names the alternative reading. Coverage gaps
explicitly modify severity: a crisis call on single-source data
is flagged as provisional.

Provide your reasoning, cite specific evidence from the digest
and the raw mention data, then give your score."""

_MON_3 = """\
Evaluate this monitoring digest for ONE quality:
Before the detail, does the reader know the single highest-stakes
development this week and why it outranks everything else?

Score 1: The digest jumps into stories without signaling which one
matters most. All developments receive similar emphasis. The
reader must read the entire digest to determine what is most
important. Or: routine data is inflated to sound urgent.

Score 3: The digest implies a top priority through ordering or
emphasis, but does not explicitly name it as the single most
important development or explain why it outranks the others.

Score 5: Within the first few sentences, the reader knows exactly
what the one highest-stakes development is and why it matters more
than everything else this week. If nothing extraordinary happened,
the digest says that plainly rather than inflating routine signals.

Provide your reasoning, cite specific evidence from the digest,
then give your score."""

_MON_4 = """\
Evaluate this monitoring digest for ONE quality:
Does each action item specify who should act, by when, and what
happens if they don't?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every action item name a specific responsible party or
   team by function — not a generic "the team" or "you"?

2. Does every action item include a bounded timeframe — a dated
   deadline or a defined relative window — not open-ended language
   like "soon" or "as appropriate"?

3. Does each action item state a consequence of inaction — what
   gets worse, what opportunity is lost, or what escalation
   happens if the action is not taken by the stated deadline?

4. Are actions that cannot wait until next week explicitly
   separated from those that can — with different urgency
   markers, a distinct section, or explicit escalation triggers?

Provide your overall reasoning, then evaluate each sub-question."""

_MON_5 = """\
Evaluate this monitoring digest for ONE quality:
Does the digest surface connections between stories that are not
obvious from the individual mention data — and project where those
connections lead?

Score 1: Each story is presented in isolation. No cross-story
patterns are identified. The reader must connect the dots
themselves. The digest is a series of independent summaries.

Score 3: The digest notes some relationships between stories
(such as "these events occurred in the same period") but does
not synthesize what they mean together or project forward
implications.

Score 5: The digest surfaces compound narratives — where two or
more signals together reveal a risk or opportunity that neither
shows alone. It names upcoming catalysts, developing threats, or
competitor moves that will shape next week. Forward projections
are conditional and falsifiable, not vague.

Provide your reasoning, cite specific cross-story connections
(or note their absence), then give your score."""

_MON_6 = """\
Evaluate this monitoring digest for ONE quality:
Does every number in the digest answer "so what?" — and does the
digest examine missing expected signals?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is every statistic in the digest accompanied by interpretation
   — not stated as a raw number alone, but paired with a
   comparison, baseline, or implication?

2. Is at least one statistic presented with a comparative frame
   that gives it meaning (such as versus prior period, versus
   competitors, versus industry average)?

3. Does the digest flag at least one expected signal that is
   ABSENT — such as a campaign that generated no coverage, a
   competitor that went quiet, or a response that never came?

4. When a number is cited, does the digest explain its
   implications for the client's actions — not just what the
   number is but what the client should do about it?

Provide your overall reasoning, then evaluate each sub-question.
Cite specific evidence from the digest and the raw mention data."""

_MON_7 = """\
Evaluate this monitoring digest for ONE quality:
Does the digest connect to the arc of prior digests — or, for
first digests, establish baselines that create an arc going forward?

For first-week digests with no prior data, temporal coherence
means establishing named baselines with thresholds. Evaluate the
sub-questions accordingly.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does the digest explicitly reference prior context — either a
   prior digest's watchlist/findings, or (for first digests) a
   named baseline with defined escalation thresholds?

2. Does the digest track continuity — either following up on
   previously recommended actions (was it taken? effective?), or
   (for first digests) identifying which current signals are
   likely to recur and warrant tracking?

3. Does the digest classify signal trajectories — stating whether
   themes are new, escalating, stable, or declining — relative to
   prior periods or (for first digests) relative to expected norms?

4. Does the digest create forward hooks — specific items, metrics,
   or conditions that the next digest should check on, making it
   impossible for the next period to silently drop a signal?

Provide your overall reasoning, then evaluate each sub-question."""

_MON_8 = """\
Evaluate this monitoring digest for ONE quality:
Is word count proportional to importance — and is editorial
restraint visible?

Score 1: Every story gets equal treatment regardless of
significance. Low-importance items receive as many words as
high-importance ones. The digest feels exhaustive rather than
curated. Available data drives length, not importance.

Score 3: Important stories get somewhat more space, but the digest
still includes sections that add little value. Some restraint is
visible but the ratio of insight to total words is middling.

Score 5: The digest spends its space on what matters most and
compresses or omits what doesn't. Editorial restraint is visible —
some available data was deliberately left out, making the remaining
content sharper. The ratio of unique analytical insight to total
words is high. The structure serves the content, not the reverse —
sections exist because the content demands them, not because a
template requires them. The reader's attention is directed, not
diffused.

Provide your reasoning, cite specific evidence from the digest,
then give your score."""


# ---------------------------------------------------------------------------
# Storyboard — Video Story Plans (8 rubrics)
# ---------------------------------------------------------------------------

_SB_1 = """\
Evaluate this story plan for ONE quality:
Does the plan explicitly reference the creator's pattern data and
continue specific elements — voice, recurring thematic concerns,
characteristic surprise mechanisms — traceably?

Use the creator pattern data and session context (story bible,
thematic pillars, derived style) as the grounding source.

Score 1: The story could belong to any creator in the same genre.
Surface-style markers are not tied to this creator's specific
obsessions, vocabulary, worldview, or recurring thematic concerns
documented in the pattern data. Pattern elements are not referenced.

Score 3: The story references some pattern elements but others are
missing or generic. Some thematic pillars are continued; others drift
into generic genre conventions.

Score 5: For each major plan element (voice, thematic pillar, surprise
mechanism, recurring character type), the plan explicitly references
the corresponding pattern data — naming the specific obsession,
technique, or worldview element being continued. A reader with the
pattern data in hand can verify each correspondence from the text
of the plan itself.

Provide your reasoning, cite specific evidence from the plan and
pattern data, then give your score."""

_SB_2 = """\
Evaluate this story plan for ONE quality:
Is the hook specific enough that you could describe it to someone
in one sentence and they would want to see the video?

The hook must be concrete and irreplaceable — an image, line, or
concept that could not belong to any other story. The mechanism
may be an impossible concept, raw emotional vulnerability, absurd
juxtaposition, or visual impossibility. What matters is specificity
and irreplaceability, not which mechanism achieves them.

Score 1: The hook is a mood or genre setup. "In a world where..."
"Something felt wrong..." "Everything was about to change..."
Nothing specific enough to describe to a friend in one sentence.

Score 3: The hook has a specific element but lacks the arresting
quality that would stop someone scrolling. It is identifiable but
not compelling — you could describe it but the listener would not
urgently want to see it.

Score 5: The hook is immediately arresting and singular — through
any mechanism (impossible concept, vulnerability, juxtaposition,
visual impossibility, or something else entirely). You could text
it to a friend and they would reply "send me the link."

Evaluate only the opening beat and hook in story_beats and
voice_script.

Provide your reasoning, cite the actual hook from the plan,
then give your score."""

_SB_3 = """\
Evaluate this story plan for ONE quality:
Is every emotional transition in the emotional_map actually
produced by a specific story beat — not just declared?

The emotional_map is a CLAIM. The story_beats are the EVIDENCE.
Verify that the beats cause the emotions, not just that the plan
says they do.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. For each emotion listed in the emotional_map, is there a
   corresponding beat in story_beats that contains a specific
   revelation, action, or juxtaposition that would produce
   that emotion in a viewer?

2. Are the emotional transitions between beats motivated —
   does each shift happen because of what the viewer just
   learned or saw, not because the plan says "the viewer now
   feels X"?

3. Does the climactic emotional moment arise from the specific
   events of THIS story — not from a generic dramatic structure
   that any story could use?

4. Would a viewer following the story_beats in order experience
   the emotions in the emotional_map without being told what to
   feel? (The arc feels inevitable rather than imposed.)

Provide your overall reasoning, then evaluate each sub-question."""

_SB_4 = """\
Evaluate this story plan for ONE quality:
By the end, does the opening scene mean something different than
it appeared to mean?

Score 1: The story is a progression — events move forward but
nothing changes the meaning of what came before. The ending is a
conclusion, not a reframing. The viewer's understanding of the
opening is the same at the end as it was at the beginning.

Score 3: The ending adds context to the opening, but the change
in meaning is modest — more of a deepening than a reframing. The
viewer thinks "that makes sense" rather than "I need to re-see
the beginning."

Score 5: The climax or resolution recontextualizes the opening in
a way that forces the viewer to re-interpret it. The emotional arc
is not just a progression but a reframing — the opening acquires
new meaning that was invisible on first viewing.

Provide your reasoning, cite the specific opening and closing
beats, then give your score."""

_SB_5 = """\
Evaluate this story plan for ONE quality:
Could a voice actor pick up this voice_script and perform it cold
without asking "what does this mean?" — and does the audio design
use silence as a story element?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every line in the voice_script include delivery directions
   specific enough to perform (such as pace, emphasis, pauses,
   emotional register) — not just the words to say?

2. Does the audio design include deliberate silence, absence,
   processing, or contrast as a story-carrying element —
   specified with timing and purpose, named in engineering terms
   (duration, treatment, source) rather than undifferentiated
   "dramatic pause" or "suspenseful music"?

3. Does the voice_script specify vocal qualities (such as tone,
   pace, volume shifts) that vary across beats — not a single
   flat delivery instruction applied to the whole script?

4. Does the audio design (music, sound effects, silence) carry
   story information that the visuals and voice alone do not?
   (The audio is a story layer, not just accompaniment.)

Provide your overall reasoning, then evaluate each sub-question."""

_SB_6 = """\
Evaluate this story plan for ONE quality:
Does every scene prompt describe something current AI video models
can actually produce — with consistency anchors that would produce
coherent output?

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every scene prompt contain enough visual detail for an AI
   model to generate a recognizable image (subject, setting,
   lighting, camera angle) — not just a mood description like
   "a person in a room"?

2. Are the scene prompts free of demands that exceed current AI
   video capabilities (such as subtle micro-expressions, specific
   readable text, precise hand gestures, or complex multi-person
   interactions)?

3. Do the consistency anchors specify WHAT must stay identical
   across scenes (such as character appearance, color palette,
   lighting style), WHAT may vary, and WHY — not just restate
   the character description?

4. Could an operator follow these scene prompts sequentially and
   produce visually coherent output without guessing what elements
   should match between scenes?

Provide your overall reasoning, then evaluate each sub-question."""

_SB_7 = """\
Evaluate this story plan for ONE quality:
Are scene count, cut frequency, and duration target grounded in
how this creator's actual videos move — not in how a screenplay
reads?

Use the creator pattern data to understand this creator's typical
video structure, duration, and pacing.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is the duration_target_seconds within the range typical for
   this creator's existing videos (as shown in the pattern data),
   with the hook delivered within the first few seconds?

2. Does the scene count match the typical number of visual
   segments in this creator's videos — not a cinematic act
   structure?

3. Is the average time per scene (duration / scene_count)
   consistent with the cut frequency in this creator's real
   content?

4. Is the emotional arc compressed to fit the target duration —
   not a feature-length story structure squeezed into short-form?

Provide your overall reasoning, then evaluate each sub-question."""

_SB_8 = """\
Evaluate the set of 5 story plans below for ONE quality:
Are these genuinely different bets — different premises, emotional
registers, structural choices — while sharing a creative universe?

Score 1: The 5 plans are variations on the same idea. They share
the same premise, emotional register, and structural pattern. They
feel like five variations on the plan the AI found easiest to
generate — not five different stories from the same creator.

Score 3: The plans differ in surface details (setting, characters)
but share a common structural pattern or emotional register. There
is variety in content but not in approach. The portfolio explores
one creative direction with cosmetic variation.

Score 5: The 5 plans are genuinely different bets: different
premises, different emotional registers, different structural
choices. They share a creative universe (the creator's voice and
thematic concerns) but each is a distinct creative bet. A viewer
would experience five distinct stories.

Provide your reasoning, cite specific examples of similarity or
difference across the plans, then give your score."""


# ---------------------------------------------------------------------------
# X Engine — 6 rubrics (all gradient; X-6 cross-item)
# Per master plan v13 §4.4 + companion file
# docs/plans/2026-05-07-001-x-engine-rubric-anchors.md.
# Drafted in docs/plans/2026-05-07-001-x-engine-rubric-prose-drafts.md;
# JR's pre-L0 F4 review scores against 10-20 emulation posts + 5
# external triangulation posts (Round-6 #18 single-rater bias check).
# ---------------------------------------------------------------------------

_X_1 = """\
Evaluate this draft for ONE quality:
Does it read like JR — first-person, opinionated, with a plain-language
register accessible to a non-engineer founder or marketer? Jargon
without inline plain-English context caps this dimension.

Score 1: The draft reads like generic content marketing or
AI-generated copy. The voice is third-person, hedged, or aggregated
("teams should...", "organizations need...", "studies show..."). Or:
jargon is present without plain-English context — terms like "MCP",
"tool-use", "context window", "agent harness" appear unexplained.
AUTOMATIC ≤4 if 2+ unexplained technical terms; AUTOMATIC ≤6 if any
jargon appears without a follow-up plain-English phrase. The draft
fails the "could a marketer read this and nod" test.

Score 3: The voice is mostly first-person and opinionated, but slips
into generic register in places — passive constructions, "people
often think", or third-person aggregations break the JR voice in 1-2
spots. Jargon, when present, is mostly explained but at least one
term assumes prior knowledge. The draft would read fine to a
technical audience but loses non-engineer readers in the dense
sections.

Score 5: Every sentence carries JR's voice — first-person, specific
to JR's lived experience, opinionated. Plain language throughout:
when a technical term appears it gets an inline plain-English
follow-up ("MCP servers — the plumbing that lets Claude read your
inbox"). A non-engineer founder reads the whole draft without
bouncing on jargon. The opinion is sharp, not hedged ("most marketing
teams overcomplicate this" not "some teams may find it complex").

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_X_2 = """\
Evaluate this draft for ONE quality:
Are factual claims grounded? SOURCE claims (statistics, quotes from
named sources, public datapoints) must be verifiable against the
angle's source_text. INTERPRETIVE claims framed as JR's view ("my
read", "in our work") are acceptable. Specific lived-work claims
about clients or projects ("when I built X for Y") are subject to a
HARD FLOOR.

Score 1: The draft contains specific factual claims that contradict
source_text, or specific lived-work claims with named entities that
do NOT appear in programs/references/voice.md (the shared substrate
loaded into source_data). Examples: "when I built the agent stack
for [fictional client]" or "our team's deployment to 50 enterprises"
without the entity in voice.md. **HARD FLOOR:** any first-person
specific lived-work claim referencing an entity not in voice.md
scores ≤3, no matter how good the draft is otherwise.

Score 3: SOURCE claims are mostly verifiable; one or two are
stretched or unsupported. INTERPRETIVE claims are present but not
always framed as opinion — some sound declarative when they're
really JR's read. No HARD-FLOOR violation but specificity feels thin
in places.

Score 5: SOURCE claims trace cleanly to source_text or named public
datapoints. INTERPRETIVE claims are explicitly framed as JR's view.
Lived-work claims either avoid named-entity specificity ("a recent
client engagement") or name entities present in voice.md. The draft
wears its specificity confidently — a fact-checker could trace every
claim or flag it as JR's opinion in under 2 minutes.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_X_3 = """\
Evaluate this draft for ONE quality:
Does the opening earn the next line? On X, the first 8-12 words carry
the draft. SHARP brackets (250-300 chars) live or die on the punch
in those words. BUILD (500-900) and CASE-STUDY (1000-1500) drafts
must beat the "show more" cutoff with their first 1-2 sentences. The
bracket declared in frontmatter sets the bar.

Score 1: Generic opener — "Most people don't realize", rhetorical
question hooks ("Have you ever wondered?"), thread announcements
("a 🧵"), or pure topic statements ("AI marketing is changing"). For
SHARP: no punch line. For BUILD/CASE-STUDY: the first sentence reads
like table-of-contents prose, no specific claim or tension. The
draft fails to earn line two; a reader scrolls past.

Score 3: The hook works mechanically but feels formulaic — a "hot
take:" framing, a contrarian-but-bland opener ("Most teams get X
wrong:"), or a specific number without context ("3 things I
learned"). For SHARP: it lands but barely. For BUILD/CASE-STUDY: the
first 1-2 sentences declare what the post is about but don't pull
the reader into specific tension. A reader might read more out of
genre habit, not because the hook compelled it.

Score 5: The hook has compression and specificity. SHARP earns 5
with one sharp claim+support pair in the first 12 words ("47 hours
of agent debugging led to one config change"). BUILD/CASE-STUDY
earns 5 when the first 1-2 sentences land a specific scenario,
named tension, or counter-intuitive specific number that makes the
rest unavoidable to read. No generic openers, no rhetorical-question
crutches.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_X_4 = """\
Evaluate this draft for ONE quality:
Zero AI-tells. The deterministic regex floor in slop_gate.py is the
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
rhythms vary naturally — not the rhythmic 3-clause cadence common
in LLM output. Transitions are JR's actual register ("but", "and
so", "which means") not the formal "Furthermore," "Moreover". The
draft reads like JR typed it.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_X_5 = """\
Evaluate this draft for ONE quality:
Does the structure earn its length? The declared length_bracket
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

Score 5: Bracket-aware structural mastery. SHARP: one sharp claim +
tight support pair, every word earns position. BUILD: prose intro +
structural pivot + 3-5 substantive bullets + authority anchor +
outcome metric. CASE-STUDY: multi-paragraph narrative + sensory
detail + numbers timeline + implication close. Structure serves the
argument; cutting any element would weaken it. Pad-to-length = ≤4
hard cap.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_X_6 = """\
Evaluate this DRAFT COHORT for ONE quality:
Across all drafts in this session's drafts/ directory, do they
spread across distinct primary differentiators, sources, and hook
archetypes? Or do multiple drafts use the same opener pattern, cite
the same source_url, or lean on the same voice_pillar? This is a
cross-item dimension — score the cohort as a whole, not individual
drafts. Use the geometric mean of per-draft cohort-fit scores.

Score 1: Multiple drafts (3+) use the same primary differentiator,
same source_url, or same hook archetype. Pillar diversity collapses
to 1-2 pillars when the variant's voice_pillars metadata supports
4+. The cohort reads as variations of one draft rather than 5
distinct drafts.

Score 3: Some diversity — 2-3 drafts share a primary differentiator
or hook pattern, but the cohort spreads across 3-4 distinct angles.
A reader scanning the cohort would see breadth but also notice
concentrations.

Score 5: Each draft uses a distinct primary differentiator, source,
and hook archetype. The cohort spreads across the full range of
voice_pillars declared in angle metadata. No two drafts could be
swapped without losing variant value. Cross-item diversity feels
intentional, not accidental.

Provide your reasoning, cite specific evidence from the cohort,
then give your score."""


_X_9 = """\
Evaluate this X draft for ONE quality (algorithmic citizenship):
Does the draft avoid embedding external URLs in the [BODY] block
or any [REPLY] block?

X's recommendation algorithm penalizes posts containing external
links severely. Buffer's 2026 analysis of 18.8M posts across 71K
accounts shows median engagement collapsing to ~0% for non-Premium
accounts that include link posts since March 2025. The X open-source
algorithm code (TweetUrlMultiplier) applies a 30-50% multiplier
penalty even for Premium accounts. A draft that includes an external
URL in its primary post body is materially less likely to reach the
intended audience, regardless of how well-written the body is. This
is a structural failure — not a quality variance.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is the [BODY] block free of external URLs (http://, https://,
   or bare-domain forms like "example.com/path")? URLs to x.com /
   twitter.com themselves are exempt. Markdown link syntax that
   resolves to an external URL counts as a URL.

2. Are all [REPLY] blocks free of external URLs? Same exemption
   for x.com / twitter.com URLs.

3. If the draft cites a source (article, study, dataset), is the
   citation handled by naming the source inline ("per the 2024
   Buffer analysis") rather than embedding a link? Drafts that
   need to cite something can score YES here by naming the source
   without linking it.

4. Is the draft free of disguised external links (URL shorteners,
   QR-code-image references, "see bio" indirection that points
   at an external URL)? Anti-gaming: "link in bio" / "DM for the
   PDF" / shortened URLs / pasted reference codes all fail this
   sub-question — the substrate must not route the user off-platform
   indirectly.

Provide your overall reasoning, then evaluate each sub-question.
A draft that fails ANY of these sub-questions is structurally
algorithmically-penalized regardless of its body-text quality —
this is a pitfall criterion that should heavily weight the
composite when violated."""


# ---------------------------------------------------------------------------
# LinkedIn Engine — 6 rubrics (all gradient; LI-6 cross-item)
# Per master plan v13 §4.4 + companion file. LinkedIn audience punishes
# vague claims harder than X (LI-2 cap-at-7) and penalizes contrarian
# hot-takes that work on X (LI-3).
# ---------------------------------------------------------------------------

_LI_1 = """\
Evaluate this draft for ONE quality:
Does it read like JR's LinkedIn voice — first-person, story-led,
with a professional register accessible to B2B buyers, agency
operators, and C-suite? The lever is **thoughtful authority**, not
contrarian punch. Plain language is still required (jargon caps
voice score), but tone is noticeably less contrarian than X.

Score 1: The draft reads as bait-y, hot-take-y, or
"Twitter-translated." Contrarian openers ("Most marketers don't
realize..."), aggressive declaratives, or X-style sub-300-char
sharps. AUTOMATIC ≤4 if the draft reads as Twitter-translated;
AUTOMATIC ≤6 if jargon appears without a plain-English follow-up.
LinkedIn buyers do not want hot takes; they want patterns + framing
they can use.

Score 3: The voice is mostly LinkedIn-appropriate but slips — a
contrarian declaration in paragraph 2, a sub-200-char aggressive
sentence amid otherwise story-led prose, or jargon-density that
buyers tolerate but don't enjoy. The draft would post but feels
slightly off-genre.

Score 5: Throughout: thoughtful authority. First-person, story-led,
specific lived-work register. Plain language — jargon, where
present, gets the inline plain-English follow-up. Tone is "I've
spent a year on this and here's what I noticed" not "you're doing
this wrong." The draft reads as a B2B-buyer-friendly version of the
same insight that might appear sharper on X.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_LI_2 = """\
Evaluate this draft for ONE quality:
Are factual claims grounded? Same SOURCE/INTERPRETIVE split as X-2.
**HARD FLOOR:** lived-work claims REQUIRE the named entity to
appear in programs/references/voice.md. **LinkedIn-specific cap:**
any first-person specific claim ("we shipped X") that does not name
the client or project caps the dimension at 7 — LinkedIn audiences
punish vague specificity harder than X audiences do.

Score 1: Specific factual claims contradict source_text, or
lived-work claims name entities not in voice.md. **HARD FLOOR:** any
unnamed-entity lived-work claim scores ≤3. Same regex floor as X-2;
LinkedIn audience adds the additional "vague specific" penalty.

Score 3: SOURCE claims are mostly verifiable; INTERPRETIVE claims
are framed as opinion. Lived-work specifics hover near the cap-at-7
threshold — "we" or "our team" without a named entity, but no
HARD-FLOOR violation. Specificity is OK but the draft would benefit
from one more named anchor.

Score 5: SOURCE claims trace cleanly. INTERPRETIVE claims framed as
JR's view. Lived-work claims either name entities present in
voice.md or stay general ("a recent engagement"). LinkedIn buyers
can fact-check the draft in under 2 minutes and either verify or
place on JR's opinion side.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_LI_3 = """\
Evaluate this draft for ONE quality:
Does the opening earn the next line? LinkedIn rewards story-led
openings ("Last quarter I learned X.") + concrete-result openings
("47 hours of agent debugging led to one config change.") +
before-the-fold tension. The first 1-2 sentences must beat the
show-more cutoff at ~210 chars on web LinkedIn (mobile cutoff is
narrower; treat 210 as a desktop reference, not a fixed gate).
**PUNISHES contrarian hot-takes that work on X** — audience-surprise
openers without JR's lived-work anchor → ≤3 on LinkedIn even though
similar hooks work on X.

Score 1: Contrarian declarative opener, aggressive sub-200-char hook
borrowed from X register, or generic LinkedIn bait ("Are you ready
for...", "Let's talk about..."). The first sentence reads as bait;
LinkedIn audience scrolls or hides. Engagement-bait closes
("Thoughts? 👇") amplify the bait register.

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
give your score."""

_LI_4 = """\
Evaluate this draft for ONE quality:
Zero AI-tells AND zero LinkedIn-AI-tells. The deterministic regex
floor in `slop_gate.py --platform linkedin` is the hard fail; this
dimension judges what slips through. LinkedIn-specific tells include
"Game-changer.", "Here's what I learned." (alone-line close),
"Thoughts? 👇", "Agree? 🤔", excessive line breaks for whitespace
inflation, fake "Hot take:" framings.

Score 1: Multiple LinkedIn-AI-tells slip through. Examples: "Here's
what I learned" alone-line close, engagement-bait emoji prompts, 4+
consecutive newlines for whitespace padding, fake hot-take framings,
"thought-leadership" cadence patterns ("Three takeaways:", "What
I've learned:"). The draft reads as LinkedIn-AI even if no generic
banned phrase fires.

Score 3: One or two LinkedIn-AI patterns slip through — a
"thoughts?" close, one whitespace-inflation paragraph break, or a
single formulaic transition marker (the "here's the thing" pattern,
or similar). The voice is mostly JR but the LinkedIn-AI rhythm
bleeds in.

Score 5: Zero AI-tells, zero LinkedIn-AI-tells. Voice consistent.
Whitespace serves paragraph structure, not visual padding. Closes
land on JR's actual cadence, not an engagement prompt. The draft
reads like JR typed it on LinkedIn, not an AI optimizing for
LinkedIn's algorithm.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_LI_5 = """\
Evaluate this draft for ONE quality:
Does the structure earn its length, AND does the hashtag count fit
the LinkedIn distribution model? The declared length_bracket
(SHORT_TAKE / THOUGHT_LEADER / CASE_STUDY) sets a structure bar.
Hashtag count is a separate component: 3-5 targeted hashtags = ideal
(no penalty); 1-2 = suboptimal (cap dimension at 7); 0 = ≤4
(zero-tag posts get less LinkedIn distribution). Spam guardrail
(count > 5) is enforced deterministically by structural_gate; never
reaches this rubric.

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
implication close + 3-5 hashtags. Hashtags map to JR's brand
pillars, not generic ("#marketing" alone = ≤4).

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_LI_6 = """\
Evaluate this DRAFT COHORT for ONE quality:
Across all drafts in this session's drafts/ directory, does the
narrative archetype vary (story-led vs lesson-led vs comparison vs
case-study)? Do the drafts spread across voice_pillars listed in
angle metadata? **PUNISHES same-tone-same-format streaks.** This is
a cross-item dimension — score the cohort as a whole using the
geometric mean of per-draft cohort-fit scores. **NOTE:** hashtag-set
diversity is NOT scored here; same-pillar drafts may legitimately
share signature 3-tag combos for brand consistency. Per-draft
hashtag count ∈ [3,5] is enforced deterministically by
structural_gate.

Score 1: All drafts use the same narrative archetype (e.g., 3 "Last
quarter I learned" story-led drafts back-to-back, or 3
listicle-style THOUGHT_LEADER drafts). Pillar diversity collapses to
1-2 pillars when the variant's voice_pillars metadata supports 4+.
Same-tone-same-format streak is obvious.

Score 3: Some archetype variation — 2 distinct archetypes across
the cohort (e.g., 1 story-led + 2 lesson-led + 0 comparison).
Pillar spread is partial. The cohort feels narrower than the
metadata allows.

Score 5: Each draft uses a distinct narrative archetype across the
4 LinkedIn-relevant categories (story-led, lesson-led, comparison,
case-study). Pillar spread matches the variant's voice_pillars
metadata. Cross-archetype variance feels intentional — a reader
scrolling the cohort experiences range, not repetition.

Provide your reasoning, cite specific evidence from the cohort,
then give your score."""


# ---------------------------------------------------------------------------
# RUBRICS registry
# ---------------------------------------------------------------------------

RUBRICS: dict[str, RubricTemplate] = {
    # GEO — 8 rubrics (6 gradient, 2 checklist). Stream C C5 pilot: tier
    # assignments per the RaR scheme (essential carries the core GEO
    # promise; pitfall flags generic boilerplate). All other lanes default
    # to "important" until tagged.
    "GEO-1": RubricTemplate("GEO-1", "geo", "gradient", _GEO_1, tier="essential"),
    "GEO-2": RubricTemplate("GEO-2", "geo", "gradient", _GEO_2, tier="essential"),
    "GEO-3": RubricTemplate("GEO-3", "geo", "gradient", _GEO_3, tier="important"),
    "GEO-4": RubricTemplate("GEO-4", "geo", "gradient", _GEO_4, tier="optional"),
    "GEO-5": RubricTemplate("GEO-5", "geo", "gradient", _GEO_5, tier="important"),
    "GEO-6": RubricTemplate("GEO-6", "geo", "checklist", _GEO_6, is_cross_item=True, tier="important"),
    "GEO-7": RubricTemplate("GEO-7", "geo", "checklist", _GEO_7, tier="essential"),
    "GEO-8": RubricTemplate("GEO-8", "geo", "gradient", _GEO_8, tier="pitfall"),
    # Competitive Intelligence — 8 rubrics (5 gradient, 3 checklist)
    # Stream C C5 tiers (2026-05-12): essential = the brief's core
    # promises (central argument, fit gaps, prioritized actions);
    # pitfalls = "don't overclaim" and "don't pretend to data you lack".
    "CI-1": RubricTemplate("CI-1", "competitive", "gradient", _CI_1, tier="essential"),
    "CI-2": RubricTemplate("CI-2", "competitive", "checklist", _CI_2, tier="pitfall"),
    "CI-3": RubricTemplate("CI-3", "competitive", "gradient", _CI_3, tier="important"),
    "CI-4": RubricTemplate("CI-4", "competitive", "checklist", _CI_4, tier="important"),
    "CI-5": RubricTemplate("CI-5", "competitive", "gradient", _CI_5, tier="essential"),
    "CI-6": RubricTemplate("CI-6", "competitive", "gradient", _CI_6, tier="important"),
    "CI-7": RubricTemplate("CI-7", "competitive", "gradient", _CI_7, tier="essential"),
    "CI-8": RubricTemplate("CI-8", "competitive", "checklist", _CI_8, tier="pitfall"),
    # Monitoring Digest — 8 rubrics (4 gradient, 4 checklist)
    # Stream C C5 tiers (2026-05-12): essential = the digest's core
    # promises (what's different, top development); pitfalls = "don't
    # pad with so-what-less numbers" and "don't bloat".
    "MON-1": RubricTemplate("MON-1", "monitoring", "checklist", _MON_1, tier="essential"),
    "MON-2": RubricTemplate("MON-2", "monitoring", "gradient", _MON_2, tier="important"),
    "MON-3": RubricTemplate("MON-3", "monitoring", "gradient", _MON_3, tier="essential"),
    "MON-4": RubricTemplate("MON-4", "monitoring", "checklist", _MON_4, tier="important"),
    "MON-5": RubricTemplate("MON-5", "monitoring", "gradient", _MON_5, tier="important"),
    "MON-6": RubricTemplate("MON-6", "monitoring", "checklist", _MON_6, tier="pitfall"),
    "MON-7": RubricTemplate("MON-7", "monitoring", "checklist", _MON_7, tier="optional"),
    "MON-8": RubricTemplate("MON-8", "monitoring", "gradient", _MON_8, tier="pitfall"),
    # Storyboard — 8 rubrics (4 gradient, 4 checklist)
    # Stream C C5 tiers (2026-05-12): essential = the plan's core
    # promises (creator-pattern grounded, specific hook); pitfall =
    # "don't write screenplay rhythm into a creator's actual cadence".
    "SB-1": RubricTemplate("SB-1", "storyboard", "gradient", _SB_1, tier="essential"),
    "SB-2": RubricTemplate("SB-2", "storyboard", "gradient", _SB_2, tier="essential"),
    "SB-3": RubricTemplate("SB-3", "storyboard", "checklist", _SB_3, tier="important"),
    "SB-4": RubricTemplate("SB-4", "storyboard", "gradient", _SB_4, tier="optional"),
    "SB-5": RubricTemplate("SB-5", "storyboard", "checklist", _SB_5, tier="important"),
    "SB-6": RubricTemplate("SB-6", "storyboard", "checklist", _SB_6, tier="important"),
    "SB-7": RubricTemplate("SB-7", "storyboard", "checklist", _SB_7, tier="pitfall"),
    "SB-8": RubricTemplate("SB-8", "storyboard", "gradient", _SB_8, is_cross_item=True, tier="important"),
    # X Engine — 6 rubrics (all gradient; X-6 cross-item)
    # Stream C C5 tiers (2026-05-12): essential = JR voice + factual
    # grounding (the lived-work backbone); pitfall = "no AI-tells".
    "X-1": RubricTemplate("X-1", "x_engine", "gradient", _X_1, tier="essential"),
    "X-2": RubricTemplate("X-2", "x_engine", "gradient", _X_2, tier="essential"),
    "X-3": RubricTemplate("X-3", "x_engine", "gradient", _X_3, tier="important"),
    "X-4": RubricTemplate("X-4", "x_engine", "gradient", _X_4, tier="pitfall"),
    "X-5": RubricTemplate("X-5", "x_engine", "gradient", _X_5, tier="important"),
    "X-6": RubricTemplate("X-6", "x_engine", "gradient", _X_6, is_cross_item=True, tier="important"),
    "X-9": RubricTemplate("X-9", "x_engine", "checklist", _X_9, tier="pitfall"),
    # LinkedIn Engine — 6 rubrics (all gradient; LI-6 cross-item)
    # Stream C C5 tiers (2026-05-12): same shape as X — essential
    # voice + grounding, pitfall on AI/LinkedIn-tells.
    "LI-1": RubricTemplate("LI-1", "linkedin_engine", "gradient", _LI_1, tier="essential"),
    "LI-2": RubricTemplate("LI-2", "linkedin_engine", "gradient", _LI_2, tier="essential"),
    "LI-3": RubricTemplate("LI-3", "linkedin_engine", "gradient", _LI_3, tier="important"),
    "LI-4": RubricTemplate("LI-4", "linkedin_engine", "gradient", _LI_4, tier="pitfall"),
    "LI-5": RubricTemplate("LI-5", "linkedin_engine", "gradient", _LI_5, tier="important"),
    "LI-6": RubricTemplate("LI-6", "linkedin_engine", "gradient", _LI_6, is_cross_item=True, tier="important"),
}


# ---------------------------------------------------------------------------
# Marketing Audit — 8 rubrics, prompts loaded from judges/MA-N-judge.md.
# Master plan §6.4. All gradient (0-10 scale internal to the judge prompt;
# substrate treats them as gradient = numeric score). Loaded from disk so
# the source of truth stays in `programs/marketing_audit/prompts/judges/`
# without duplicating ~400 LOC of prompts inline.
# ---------------------------------------------------------------------------
import pathlib as _pathlib  # noqa: E402

_MA_JUDGE_DIR = (
    _pathlib.Path(__file__).resolve().parents[2]
    / "programs" / "marketing_audit" / "prompts" / "judges"
)
# Stream C C5 tiers (2026-05-12) for marketing_audit:
# - MA-1 narrative coherence, MA-2 evidence traceability, MA-4 actionable
#   recommendations: essential. These are the deliverable's reason to exist.
# - MA-3 phase-0 framing, MA-5 severity calibration, MA-8 engagement-fit:
#   important. Substantive support for the essentials.
# - MA-6 polish: optional. Cosmetic.
# - MA-7 gap honesty: pitfall. Hiding measurement gaps is the failure mode.
_MA_TIERS: dict[str, str] = {
    "MA-1": "essential",
    "MA-2": "essential",
    "MA-3": "important",
    "MA-4": "essential",
    "MA-5": "important",
    "MA-6": "optional",
    "MA-7": "pitfall",
    "MA-8": "important",
}
for _i in range(1, 9):
    _ma_path = _MA_JUDGE_DIR / f"MA-{_i}-judge.md"
    if not _ma_path.exists():
        raise RuntimeError(
            f"missing MA-{_i} judge prompt at {_ma_path} — required by lane registry"
        )
    _ma_id = f"MA-{_i}"
    RUBRICS[_ma_id] = RubricTemplate(
        _ma_id, "marketing_audit", "gradient",
        _ma_path.read_text(encoding="utf-8"),
        tier=_MA_TIERS[_ma_id],
    )


# ---------------------------------------------------------------------------
# Version hash — deterministic fingerprint of all prompt text
# ---------------------------------------------------------------------------

_concatenated = "".join(
    # Stream C C5: tier is part of the rubric identity — bumping a criterion
    # from ``important`` to ``essential`` must invalidate parent-score caches
    # (Stream C C4-lean part 3) the same way a prompt edit would.
    f"{r.tier}|{r.prompt}"
    for r in sorted(RUBRICS.values(), key=lambda r: r.criterion_id)
)
RUBRIC_VERSION: str = hashlib.sha256(_concatenated.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Verification — bidirectional invariant between RUBRICS and LaneSpec.rubric_ids
# ---------------------------------------------------------------------------
#
# The total rubric count is *derived* from the sum of every LaneSpec's
# rubric_ids tuple, not a hardcoded magic number. Per-lane rubric increments
# update the LaneSpec; the assertion follows. Catches drift in either
# direction (lane added without rubric prose, rubric prose without a lane).

from autoresearch.lane_registry import LANES as _LANE_SPECS  # noqa: E402

_expected_rubric_count = sum(len(spec.rubric_ids) for spec in _LANE_SPECS.values())
assert len(RUBRICS) == _expected_rubric_count, (
    f"Expected {_expected_rubric_count} rubrics (derived from "
    f"sum(len(spec.rubric_ids) for spec in LANES.values())), got {len(RUBRICS)}"
)

_lane_rubric_ids = {rid for spec in _LANE_SPECS.values() for rid in spec.rubric_ids}
_missing_in_rubrics = _lane_rubric_ids - set(RUBRICS)
assert not _missing_in_rubrics, (
    f"Lane registry declares rubric IDs not present in RUBRICS: {sorted(_missing_in_rubrics)}"
)
_orphaned_rubrics = set(RUBRICS) - _lane_rubric_ids
assert not _orphaned_rubrics, (
    f"RUBRICS contains IDs not claimed by any LaneSpec.rubric_ids: {sorted(_orphaned_rubrics)}"
)
