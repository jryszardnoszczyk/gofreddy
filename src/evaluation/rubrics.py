"""Rubric templates for the 32-criteria evaluation system.

Each rubric is either:
- gradient: scored on a 1/3/5 scale with anchor descriptions
- checklist: 4 binary YES/NO sub-questions

Domains: geo (8), competitive (8), monitoring (8), storyboard (8)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


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
    # Content Engine v1 U5 — TD-11 hybrid: when set, the rubric prose is
    # resolved at evaluation time from an external file. Two forms:
    #   "reviewer_assist/checklists/<name>.yaml#<rule_id>" → loads the
    #     named rule's prose from the YAML; lets one edit propagate to
    #     all lanes that consume the rule set.
    #   "docs/rubrics/<file>.md#<anchor>" → loads the markdown section
    #     beneath the named heading; lets substantial rubric prose live
    #     outside rubrics.py with independent versioning.
    # When None (default), evaluators fall back to the inline `prompt`.
    prose_ref: str | None = None


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
# Prose resolution (Content Engine v1 U5 / TD-11 hybrid)
# ---------------------------------------------------------------------------
#
# Per TD-56: the resolver lives inline here as a small free function rather
# than its own `src/evaluation/rubric_resolver.py` module. Two prose_ref
# shapes are supported:
#
#   "reviewer_assist/checklists/<name>.yaml#<rule_id>"
#       Loads the named rule's prose from the reviewer-assist YAML. Edits
#       to a single rule propagate to every lane that references it.
#
#   "docs/rubrics/<file>.md#<anchor>"
#       Loads the markdown section beneath the named heading (e.g.
#       "## SE-1: visual hierarchy"). Used by site_engine SE-1..SE-8
#       per TD-30.
#
# When `template.prose_ref` is None, callers fall back to `template.prompt`.


def resolve_prose(template: "RubricTemplate", registry_root: Path | None = None) -> str:
    """Resolve a RubricTemplate's prose, dispatching on `prose_ref` shape.

    Args:
        template: the rubric whose prose to load.
        registry_root: directory that anchors relative `prose_ref` paths.
            Defaults to the repo root (two parents up from this file).
    """
    if template.prose_ref is None:
        return template.prompt

    root = registry_root if registry_root is not None else Path(__file__).resolve().parents[2]
    ref = template.prose_ref
    if "#" not in ref:
        raise ValueError(
            f"prose_ref {ref!r} for {template.criterion_id} must include '#<anchor>'"
        )
    file_part, anchor = ref.split("#", 1)
    target = root / file_part
    # Per the 4-agent review (sec-5): defend against `..`-style traversal
    # by resolving the symlinks-collapsed real path and asserting it
    # stays inside the registry root. Without this, a prose_ref like
    # "../../../../etc/passwd.yaml#anything" would happily load anything
    # on disk with a matching extension.
    resolved_target = target.resolve()
    resolved_root = root.resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise ValueError(
            f"prose_ref {ref!r} for {template.criterion_id} resolves to "
            f"{resolved_target} which is outside the registry root "
            f"{resolved_root}."
        )
    if not target.is_file():
        raise FileNotFoundError(
            f"prose_ref {ref!r} for {template.criterion_id} resolves to "
            f"{target} which does not exist."
        )

    if file_part.endswith(".yaml") or file_part.endswith(".yml"):
        payload = yaml.safe_load(target.read_text()) or {}
        rules = payload.get("rules") or []
        for rule in rules:
            if isinstance(rule, dict) and rule.get("id") == anchor:
                prose = rule.get("prose")
                if not prose:
                    raise ValueError(
                        f"prose_ref {ref!r}: rule {anchor!r} has no `prose` field"
                    )
                return str(prose)
        raise KeyError(
            f"prose_ref {ref!r}: rule id {anchor!r} not found in {file_part}"
        )

    if file_part.endswith(".md"):
        # Match a markdown heading whose text starts with the anchor (case-
        # insensitive). Returns content from after that heading to the next
        # heading of the same-or-higher level.
        text = target.read_text()
        anchor_lower = anchor.lower()
        pattern = re.compile(
            r"^(#{1,6})\s+(.+?)\s*$", flags=re.MULTILINE,
        )
        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            heading_text = match.group(2).strip().lower()
            if not heading_text.startswith(anchor_lower):
                continue
            level = len(match.group(1))
            body_start = match.end()
            body_end = len(text)
            for nxt in matches[i + 1:]:
                if len(nxt.group(1)) <= level:
                    body_end = nxt.start()
                    break
            return text[body_start:body_end].strip()
        raise KeyError(
            f"prose_ref {ref!r}: no heading starting with {anchor!r} in {file_part}"
        )

    raise ValueError(
        f"prose_ref {ref!r} has unsupported file extension; supported: "
        f".yaml, .yml, .md"
    )


# ---------------------------------------------------------------------------
# Article Engine — 8 rubrics (all gradient; AE-8 cross-item)
# Per Content Engine Lanes v1 U13 + master plan §4.5 + TD-40 / TD-44.
# AE-3 carries the AE-3 citation verifier hard floor (TD-44): untraceable
# citation = structural fail. AE-4 mirrors the X-4 / LI-4 anti-slop pattern.
# AE-8 is the cross-cohort diversity criterion (mirrors X-6 / LI-6 shape).
# ---------------------------------------------------------------------------

_AE_1 = """\
Evaluate this article draft for ONE quality:
Does the opening earn the next line? The first 60 words (blog) or
first 210 chars (LinkedIn Article fold-safe region) must deliver at
least ONE of: (a) a falsifiable claim, (b) a named subject the reader
recognizes, or (c) a concrete result/number. The hook must also be
testable against the body's main claim — a hook that promises X but
the body delivers Y is bait.

Score 1: Generic opener — "In today's fast-paced landscape...",
restated topic title as the first sentence, or an unmotivated
rhetorical question. AUTOMATIC ≤3 if the first sentence is a
rhetorical question without a specific subject; AUTOMATIC ≤4 if the
opener restates the article topic without adding a falsifiable
claim. Reader scrolls past the fold.

Score 3: Hook works but is formulaic — a concrete-number opener
without specific entity, or a story-led sentence that doesn't earn
the show-more cutoff. Body delivers the hook's promise but the path
is mechanical.

Score 5: Hook delivers a falsifiable claim, a named subject, or a
concrete result within the first 60 words / 210 chars; that claim is
demonstrably the body's main thesis. The reader can quote the hook
in a tweet and the body delivers on that quote. Story-led + specific
+ testable.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_2 = """\
Evaluate this article draft for ONE quality:
Does the body advance at least one claim that could be proven wrong?
"X is important", "Y has many benefits", "Z is the future" are
unfalsifiable — every reasonable reader agrees, so the article
contributes nothing. The thesis must be specific enough that a
disagreeing operator could write a published rebuttal.

**HARD FLOOR (per TD-40):** the body must carry ≥3 concrete
numeric or named-entity claims per 1,000 words. Below the floor,
score ≤3 regardless of prose quality — citation density without
specificity is wallpaper.

Score 1: No falsifiable claim in the body. Vague benefits prose, or
a thesis whose negation no one would defend ("AI is changing
marketing"). Reader walks away without a single specific takeaway.

Score 3: Thesis is half-specific — names ONE entity or carries ONE
number, but the surrounding prose generalizes ("companies are
investing heavily in AI"). Below the 3-claims-per-1,000-words floor.

Score 5: Body advances at least one claim a thoughtful operator
could disagree with publicly — specific enough to argue with, named
enough to verify. Three or more concrete claims per 1,000 words
(numbers, named entities, dated events). The thesis would survive a
hostile reader looking for hedge-language to dismiss.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_3 = """\
Evaluate this article draft for ONE quality:
Citation density AND verification rate. Every numeric or attributive
claim must (a) carry an inline `[N]` reference, and (b) trace to a
named source — either `brief.source_id` from a consumed findings-
brief, an entity in `programs/references/voice.md`, or a URL that
the citation_verifier (TD-44) marked `verified: true`.

**HARD FLOOR (per TD-40 / TD-44):** ANY claim with an inline `[N]`
reference whose target URL is `degraded` (404, paywalled, JS-heavy)
caps the score at 4 — operator must fix or remove the citation
before ship. ANY numeric/attributive claim with NO citation at all
caps the score at 3 — "studies show", "experts say", "research
indicates" are anti-patterns. Untraceable citation = structural
fail (gate blocks ship before this rubric fires).

Score 1: Numeric claims float free ("studies show 80% of marketers
use AI"), citations are sparse or absent, OR multiple citations
resolve to degraded URLs the verifier rejected. Reader cannot
verify a single claim in under 2 minutes.

Score 3: Some citations are inline + named; others are vague
attributive cover ("according to recent research") without a
verifier-checkable URL. Density below 4 citations per 1,000 words on
a claim-heavy section.

Score 5: Every numeric or attributive claim carries an inline `[N]`
citation; every citation traces to a named source or
verifier-checked URL; verification rate ≥0.9 across all URL
citations. Reader can audit the article in one pass through the
reference list.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_4 = """\
Evaluate this article draft for ONE quality:
Voice fidelity. The prose reads as first-person operator voice with
lived-work specifics drawn from `programs/references/voice.md` — NOT
generic AI register, NOT corporate-passive hedge stack, NOT
"thought-leader" template prose.

**Anti-patterns (deny-regex; any hit caps at 4):** "seamlessly",
"robust", "holistic", "leverage", "optimize", "streamline",
"cutting-edge", "game-changing", "revolutionary", "transform", and
"transformative" as adjectival filler. Hedge stack ("potentially" +
"likely" + "generally" + "it may be" within 3 sentences) is the
same anti-pattern with a different surface form.

**HARD FLOOR (mirrors X-2 / LI-2):** lived-work claims ("when I
shipped X", "our team built Y") REQUIRE the named entity to appear
in voice.md. Unnamed lived-work claims score ≤3.

Score 1: Generic AI register — "leverages cutting-edge AI to
seamlessly transform marketing workflows". Hedge stack present.
Lived-work claims name entities not in voice.md.

Score 3: Voice register is mostly operator-first-person but slips —
2-3 anti-pattern words or one hedge stack in an otherwise-specific
section. Lived-work claims hover near the cap-at-7 threshold ("we",
"our team" without named entity).

Score 5: Throughout: first-person operator voice. Plain language —
no anti-pattern words. Lived-work claims either name voice.md
entities cleanly or stay general ("a recent engagement"). The
article reads as if JR (or the assigned persona) actually wrote it
about work they actually did.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_5 = """\
Evaluate this article draft for ONE quality:
Argument coherence and structure. The body must trace a visible
problem → mechanism → evidence → implication arc. Paragraphs that
support the same step belong adjacent; paragraphs from different
steps belong separated. The reader should be able to outline the
article's argument in 4-5 bullets after one read.

**Listicle-disguise anti-pattern:** if the article's paragraphs are
freely reorderable without meaning loss, it's a listicle pretending
to be analysis. Caps at 3.

Score 1: No visible arc. Paragraphs are interchangeable; each
restates the same vague point with different framing. The reader
cannot reconstruct an argument because there isn't one — the article
is a topic survey, not an analysis. Listicle-disguise pattern.

Score 3: An arc exists but is muddled. Problem and mechanism are
clear; evidence is thin or the implication paragraph repeats the
introduction. Reader can outline the article but the outline is
generic.

Score 5: Problem → mechanism → evidence → implication arc is
visible from skim alone. Each section advances the argument; cutting
any single section would damage the case. The reader can quote the
core mechanism and the supporting evidence verbatim after one read.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_6 = """\
Evaluate this article draft for ONE quality:
Skimmability and rhythm. Articles must respect the reading device:
- Subheads every 200-300 words (blog) / 150-250 words (LinkedIn).
- Paragraphs ≤4 sentences (blog) / ≤3 sentences (LinkedIn).
- At least ONE TL;DR, summary callout, or bullet-list landmark.

Walls of text (>400 words without a paragraph break) violate the
rhythm; lists of single-sentence paragraphs violate the rhythm in
the other direction (no prose density to engage with).

Score 1: Wall-of-text shape — multiple paragraphs over 6 sentences,
or 600+ words without a subhead. Reader bounces. OR: every paragraph
is one sentence, formatted as a list — no prose density.

Score 3: Subhead density is acceptable but inconsistent — three
subheads in the first half, none in the second; one wall-of-text
paragraph in an otherwise-rhythmic article. Reader skims but loses
the thread mid-article.

Score 5: Subheads land every 200-300 words; paragraphs are 2-4
sentences; one explicit TL;DR or summary callout. Reader can skim
the structure in 30 seconds and read the full article in 8 minutes
without losing the argument.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_7 = """\
Evaluate this article draft for ONE quality:
Platform-adapter compliance. Blog and LinkedIn Article have
distinct formatting requirements; the draft must match the
platform declared in the front matter.

**Blog requirements (structural gate enforces these; rubric scores
qualitative fit):**
- H1 present (the article title);
- meta description 140-160 chars;
- schema.org Article JSON with `headline`, `author`,
  `datePublished`, `image`;
- ≥1 hero image brief;
- ≥1 inline image brief.

**LinkedIn Article requirements:**
- First 210 chars deliver fold-safe hook (no markdown header on
  line 1; LI strips them);
- 3-5 hashtags;
- Bold + line breaks instead of markdown `#` headers;
- No image carousels (LI Articles aren't carousels).

Score 1: Wrong platform shape — markdown headers in a LinkedIn
Article (LI strips them, leaving formatting garbage), or blog
missing the schema.org JSON entirely, or hook truncates mid-claim
at the 210-char fold. Structural gate fail.

Score 3: Platform shape is mostly correct but one or two elements
miss — blog meta description outside 140-160 chars, or LinkedIn
Article uses one `#` header. Structural gate passes; rubric notes
the slip.

Score 5: Every platform-specific element lands cleanly. Blog
schema.org validates with all four required keys; meta description
is 140-160 chars; hero + inline image briefs present. LinkedIn
Article hook holds in 210 chars; 3-5 hashtags; bold + line breaks
where markdown would go.

Provide your reasoning, cite specific evidence from the draft, then
give your score."""

_AE_8 = """\
Evaluate this BATCH of article drafts for ONE quality:
Cross-cohort diversity and novelty. When multiple drafts ship in a
weekly batch, they must not share opening patterns, thesis shapes,
or named-entity invocations. The reader's perception of the lane is
shaped by the BATCH, not the individual draft.

This is a CROSS-ITEM rubric — score the BATCH, not any single draft.

Score 1: ≥2 drafts share the opening pattern verbatim (e.g., both
open with "Last quarter I..." or both lead with the same concrete
number). OR: ≥2 drafts thesis-restate ("X is changing", "Y is
disrupted"). The batch reads as one article in three voices.

Score 3: Opening patterns are mostly distinct but thesis shapes
cluster — two drafts argue the same underlying point with different
surface examples. Reader notices the homogeneity but each draft
stands alone.

Score 5: Every draft opens differently, advances a distinct thesis,
references distinct lived-work entities. The batch reads as three
operators on three topics, not one operator on three angles.
Geometric-mean across drafts within cohort is high.

Provide your reasoning, cite specific evidence from the batch, then
give your score."""


# ---------------------------------------------------------------------------
# Image Engine — 8 rubrics (all gradient; IE-6 cross-item, IE-1/2/3/5/6
# routed through vision_judge.py with Gemini 3 Flash Preview multimodal
# backend per JR's 2026-05-19 U14 model update; IE-4/7/8 stay on the
# text-only outer judge service).
# Per Content Engine Lanes v1 U14 + master plan §4.6 + TD-41.
# ---------------------------------------------------------------------------

_IE_1 = """\
Evaluate this image (or carousel cover slide) for ONE quality:
Hook visual — does it earn the next interaction within 2 seconds of
thumbnail-scale viewing? The visual must deliver at least ONE of: (a)
a clear focal subject the eye lands on without ambiguity, (b) a
text-overlay claim ≤7 words readable at thumbnail (120px) scale, or
(c) a concrete sensory anchor (number, object, named entity) that
gives the viewer a reason to stop scrolling.

Sub-dimensions (vision_judge scores each):
- stop_scroll_strength
- focal_clarity
- thumbnail_legibility

Score 1: Cluttered composition — multiple focal candidates competing,
text-overlay >7 words that becomes illegible at 120px, or no concrete
anchor. The viewer's eye wanders; thumbnail reads as visual noise.
AUTOMATIC ≤4 if text-overlay exceeds 7 words; AUTOMATIC ≤3 if no clear
focal subject identifiable at thumbnail scale.

Score 3: Focal subject exists but the hook lacks specificity — generic
"businessperson at laptop" or stock-photo cliche, OR text-overlay
clear but unmotivated rhetorical ("Are you ready?"). The viewer stops
briefly but has no reason to continue.

Score 5: One unambiguous focal subject; text-overlay (if present)
delivers a falsifiable claim, named entity, or concrete result in ≤7
words; image reads cleanly at thumbnail. The viewer can identify the
visual's subject + claim in <2 seconds with no prior context.

Provide your reasoning and the dimension scores."""

_IE_2 = """\
Evaluate this image for ONE quality:
Brand consistency. The composition must match the client's brand
tokens — palette, typography, logo treatment, iconography register.
Per TD-41: palette + typography hint baked into fal prompt via hex
codes; exact logo PNG + headlines Pillow-composited after. The image
must read as on-brand to a designer who knows the brand.

Sub-dimensions (vision_judge scores each):
- palette_fidelity         (ΔE ≤15 across all accent colors)
- typography_consistency   (matches client font family or analogous)
- logo_treatment           (correct placement, scale ≤8% frame, not fal-rendered)
- iconography_register     (B2B-restrained vs consumer-warm matches archetype)

Score 1: Off-palette colors (ΔE >15 from brand tokens not topic-
justified), generic system typography in place of brand font, OR
fal-rendered logo/wordmark (anti-pattern — always Pillow-composite
brand wordmarks). AUTOMATIC ≤2 if any brand wordmark is fal-rendered
(hallucination produces extra-fingers-in-logo failure mode).

Score 3: Palette mostly matches but one accent color drifts; typeface
in the right family but wrong specific weight; logo present but
oversized or misaligned. Designer would request a revision.

Score 5: Every accent color within ΔE ≤15 of brand tokens; typography
matches brand family + weight; logo Pillow-composited at correct
scale + position; iconography register matches archetype (B2B
restrained for legal_pl / b2b_regulated; consumer-warm for
b2c_aesthetics). Image passes a designer's "looks like the brand"
check.

Provide your reasoning and the dimension scores."""

_IE_3 = """\
Evaluate this image for ONE quality:
Information density + legibility. The image must respect both the
thumbnail-scale reading and the full-view reading. Subheads and body
text must remain legible at 120px (thumbnail) and at 1080px (full
view); whitespace must balance the content; visual hierarchy must
guide the eye.

Sub-dimensions (vision_judge scores each):
- legibility_at_thumbnail   (text readable at 120px)
- whitespace_balance        (no walls of text; no empty desert)
- hierarchy_clarity         (headline > subhead > body order visible)

Score 1: Wall-of-text slide (>60 words on `li_doc_carousel`, >15%
pixel-area text on ad), OR illegible-at-thumbnail body, OR no visible
hierarchy (all text same size + weight). AUTOMATIC ≤3 if a
`li_doc_carousel` slide exceeds 60 words.

Score 3: Hierarchy clear at full-view but body text fails at
thumbnail; OR whitespace balance off (too cramped or too sparse).
Image works in one context but not both.

Score 5: Body text legible at 120px AND 1080px; whitespace balance
guides without distracting; headline > subhead > body order
unambiguous; hierarchy clarity passes the squint test (close one eye
and the focal hierarchy still reads).

Provide your reasoning and the dimension scores."""

_IE_4 = """\
Evaluate this image (or carousel) for ONE quality:
Format compliance. The output must match the platform format
declared in the brief — exact pixel dimensions, slide count (for
carousels), safe-zone respect (for stories), text-overlay ratio (for
ads). This is the structural lane — the gate enforces most checks
deterministically; this rubric judges QUALITATIVE FIT within
compliance.

Per-format specs (structural gate enforces):
- ig_single: 1080×1080
- ig_carousel: 5-10×1080×1080
- ig_story: 1080×1920, 3-zone hierarchy, top/bottom 250px safe-zones
- li_doc_carousel: 8-12×1080×1080 (or 1080×1350 portrait)
- hero_banner: 1600×900, ≥4.5:1 WCAG 2.2 text contrast
- ad_static: text-overlay <20% pixel area; LinkedIn billboard ≤7 words

Score 1: Wrong dimensions, wrong slide count (carousel <5 or >10
ig_carousel; <8 or >12 li_doc_carousel), text in IG story safe-zone,
or hero text contrast <4.5:1. Structural gate would fail this; the
rubric reflects.

Score 3: Within structural gate but qualitative slip — ad text-overlay
17-20% (within gate but tight), or li_doc_carousel slide at 60-word
limit. Operator would adjust before ship.

Score 5: Comfortably within all format specs; text-overlay well below
caps; hierarchy + safe-zones respected with margin. Operator can
ship without revision.

Provide your reasoning and the dimension scores."""

_IE_5 = """\
Evaluate this image for ONE quality:
Visual specificity. The composition must commit to a concrete
subject + scene; generic AI register (floating 3D shapes, abstract
gradients, "data as flowing river" metaphor) caps the score. Per
TD-41: vision-judge consumes `anti_patterns.yml` and reports
`failure_modes_observed` — non-empty list caps this rubric at 4.

Sub-dimensions (vision_judge scores each):
- concept_concreteness          (named object/scene, not abstract)
- absence_of_generic_filler     (no lime+purple AI gradients, no
                                 floating blob spheres, no
                                 isometric-cube clip-art)
- metaphor_strength             (if metaphor used, IS it apt to topic)

Score 1: Generic AI tells dominate — lime+purple+dark gradient, three
floating spheres, "abstract data flow" with no concrete subject, OR
stock-photo cliche (diverse-group-laughing-at-laptop, glassmorphism
filler). AUTOMATIC ≤2 if `failure_modes_observed` includes any
substrate-banned pattern (extra fingers, garbled in-image text,
hallucinated logos).

Score 3: Composition has a concrete subject but the metaphor is weak
or the surrounding scene is generic ("AI as glowing brain" for a
specific KSeF article). Anti-patterns YAML hit caps at 4 per TD-41.

Score 5: One concrete, topic-specific subject; the scene specifies a
moment, place, or named entity; no generic AI tells present; if
metaphor used it's apt to the topic and not cliched. The image could
not be reused for an unrelated article without becoming weird.

Provide your reasoning, dimension scores, and any anti-pattern IDs
observed."""

_IE_6 = """\
Evaluate this CAROUSEL for ONE quality:
Carousel arc. Per TD-41 PSR structure (li_doc_carousel) or
hook-stakes-value(×4)-proof-cta (ig_carousel): the cover slide must
stop the scroll within 2 seconds, slides 2-3 must raise stakes,
middle slides must deliver value, slide N-1 must offer proof, last
slide must close with a CTA. Continuity = shared palette + recurring
structural anchor across slides.

Sub-dimensions (vision_judge rolls up per-slide):
- cover_hook            (stops scroll <2s)
- slide_pacing          (each slide advances the arc; no filler)
- payoff_strength       (slide N-1 proof lands)
- cta_clarity           (last slide CTA explicit)

This is a CROSS-ITEM rubric — score the CAROUSEL, not any single
slide. Per TD-41 rollup: mean(dimension_scores) + min(score) gate —
one weak slide drags the whole carousel score.

Score 1: Cover identical to interior slides; no visible PSR arc;
middle slides reorderable without meaning loss; no closing CTA.
Reader swipes once, then leaves. AUTOMATIC ≤3 if any slide
duplicates the cover pattern.

Score 3: Cover stops scroll; middle slides have value but pacing is
uneven; CTA exists but mechanical ("Want to learn more? Schedule a
demo"). Arc is visible but not compelling.

Score 5: Cover delivers fold-safe hook; stakes-raising in slides 2-3;
value delivery in middle slides without filler; payoff in slide N-1;
specific CTA in last slide. Reader who only swipes once gets the
hook; reader who completes the carousel gets the proof; reader who
acts has a clear next step.

Provide your reasoning and the per-slide rollup dimension scores."""

_IE_7 = """\
Evaluate this image's META (alt-text + caption) for ONE quality:
Alt-text accessibility + caption voice consistency. Every shipped
image must carry alt-text that a screen reader can use; the caption
(when present) must match the assigned voice persona — same fidelity
bar as the article_engine + linkedin_engine voice rubrics.

NOT a visual rubric — this fires on TEXT (alt-text + caption) and
routes through the text-only outer judge service.

Score 1: Alt-text missing, OR alt-text is "image" / "picture" / a
literal pixel-description ("photo of a hand"), OR caption uses AI
register words (seamlessly, robust, holistic, leverage). Screen-
reader users get nothing; sighted users see voice drift.

Score 3: Alt-text describes the image but generically; caption is
mostly voice-consistent but slips into corporate-passive register in
one spot. Accessible but not on-brand.

Score 5: Alt-text describes the image's KEY INFORMATION (the
falsifiable claim, the named subject, the concrete result) in ≤120
chars; caption matches the persona's voice rules + style anchors;
caption respects the platform's register (informal for ig_single,
B2B-restrained for li_doc_carousel).

Provide your reasoning, cite specific alt-text + caption excerpts,
then give your score."""

_IE_8 = """\
Evaluate this image for ONE quality:
Repurposability. A v1 image_engine output should be usable across at
LEAST two platforms with at MOST a minor crop or text-resize. An
image that works only at 1080×1080 ad_static and would need a full
re-shoot for ig_story is single-use; the substrate produces those at
non-trivial cost.

Optional rubric — scores informational, not gating. The lane prefers
images with hero-banner-and-instagram bones over hyper-specialized
shots.

Score 1: Single-platform shot; reuse requires re-generation. Composition
hard-anchored to one aspect ratio; subject placement breaks if
cropped to story or square.

Score 3: Reusable with manual intervention — operator can crop the
1080×1080 to ig_story by adjusting the safe-zone, but it's not
designed for it.

Score 5: Composition respects multiple aspect-ratio cuts; subject +
text-overlay land within the safe-zones of ≥2 formats; operator
could repurpose with a 5-minute Pillow script, no re-generation.

Provide your reasoning and the dimension scores."""


# ---------------------------------------------------------------------------
# Ad Engine — 8 rubrics (all gradient). Per Content Engine Lanes v1 U15 +
# master plan §4.7 + TD-42. Inner-loop statically pinned to claude/sonnet
# (NOT codex — healthcare + regulated-legal ad vocabulary trips codex's
# cyber filter; pinning sonnet from day 1).
# ---------------------------------------------------------------------------

_AD_1 = """\
Evaluate this ad creative for ONE quality:
Hook strength. The first 8 words (text ads) or first frame (Reels)
must pause the SaaS/AI buyer. The hook is testable against the body
— a hook that promises X but the body delivers Y is bait.

Falsifiable floor: the hook MUST contain at least ONE of:
- a concrete number ("47 of our 50 enterprise clients...")
- a named competitor or category ("most marketing teams...")
- a contrarian claim ("the productivity stack is bigger than your CRM")
- a specific workflow noun ("monthly close", "campaign reconciliation")

Anti-pattern caps (per src/ads/compliance/anti_patterns.py):
- "Tired of X? Meet Y" PAS-formula opener → cap at 4
- "Unlock [outcome]" generic promise → cap at 4
- "AI-powered" without specific capability noun → cap at 4
- Per hit count: cap at max(2, 4 - 0.5 × (hits - 1))

Score 1: Generic SaaS opener — "Are you tired of broken workflows?",
"Meet the future of work", or "Are you ready for...". Reader scrolls
past. AUTOMATIC ≤3 if the opener uses any PAS-formula construction;
AUTOMATIC ≤4 if the opener uses banned anti-pattern words.

Score 3: Hook works but is formulaic — concrete-number opener
without specific entity, OR contrarian claim that's too vague to
test.

Score 5: Falsifiable claim, named subject, or concrete result in
the first 8 words / first frame. Hook would survive a thoughtful
buyer asking "how do you know?". Body delivers on the hook's promise.

Provide your reasoning and the score."""

_AD_2 = """\
Evaluate this ad creative for ONE quality:
CTA clarity. The viewer must know what happens on click in ≤4 words.
Generic CTAs ("Learn More", "Discover the Power of") cap at 3.

Falsifiable floor: CTA verb must be ONE of:
- a platform-native action verb (Meta: "Shop Now", "Get Quote",
  "Book Now"; LinkedIn: "Apply", "Download", "Sign Up")
- a specific outcome verb + object ("See pricing", "Read case
  study", "Book a 15-min demo")

Score 1: "Learn More" / "Discover" / "Find out how" — generic
filler. 0% of top-2%-CTR LinkedIn ads use these (per cited research).
AUTOMATIC ≤3 if CTA is "Learn More".

Score 3: CTA is platform-native but anchored on a vague verb
("Explore", "Sign Up" without context).

Score 5: CTA verb is platform-native AND specific. Reader knows
what will happen on click in ≤4 words. Tied to a specific outcome.

Provide your reasoning and the score."""

_AD_3 = """\
Evaluate this ad creative for ONE quality:
Offer specificity. Can a competitor steal this offer? If yes, it's
specific. If "Better analytics" — every analytics company offers
that. The offer must include at least ONE of: price, duration,
quantity, or named deliverable.

Score 1: Vague benefit prose — "Save time", "Grow faster", "Smarter
workflows". Any competitor in the category could ship the same ad.

Score 3: Offer names ONE of {price, duration, quantity, named
deliverable} but doesn't anchor the claim ("Get our 14-day trial"
without saying what's in the trial).

Score 5: Offer is specific enough to be stealable. "$49/mo
unlimited seats", "15-min implementation call with a Salesforce-
certified engineer", "Free import of your last 6 months of
HubSpot data" — competitor couldn't ship the same ad without
delivering the same offer.

Provide your reasoning and the score."""

_AD_4 = """\
Evaluate this ad creative for ONE quality:
Platform-format compliance. Would Meta or LinkedIn auto-approve
this? The structural gate catches hard violations
(banned terms, character-limit overruns); this rubric scores
qualitative fit.

Hard caps (structural gate enforces):
- Meta: 125 char primary text, 27 char headline, 30 char description,
  no text-in-image >20% of frame.
- LinkedIn Sponsored: ≤150 char intro front-loaded, 1-2 line
  headline, ≤150 char body recommended.
- LinkedIn Document Ad: 3-10 slides (sweet spot 5-7), cover slide
  works as standalone.
- Reels Ad: 9-15s, vertical 9:16, hook in first 0.8-1.2s.

Banned terms (Meta health-vertical, LinkedIn aggressive promotional,
"guaranteed N% results") trigger hard reject.

Score 1: Hard violation — banned term present, character limit
overrun, wrong aspect ratio. Auto-rejected on submit.

Score 3: Within structural gate but soft slip — Meta headline at
24-27 chars (close to cap), LinkedIn body slightly over recommended.

Score 5: Comfortably within all platform specs. Headline tight,
body front-loaded, CTA platform-native, no banned terms.

Provide your reasoning and the score."""

_AD_5 = """\
Evaluate this BATCH of ad creative variants for ONE quality:
Variant diversity. The 3-5 variants must test distinct hypotheses —
not paraphrases of the same angle. Cross-cohort matters because
A/B testing depends on variants being meaningfully different.

Falsifiable floor:
- Pairwise Jaccard on hook+opening-8-token ≤0.3
- Archetype enum values all distinct (no two variants share
  hook_archetype ∈ {statistic, pain, contrarian, demo-tease, pattern-break})
- No two variants share the same proof noun

Per-format diversity dim (per TD-42):
- Meta Reels: hook archetype
- Meta Image: promise type {outcome, status, efficiency, risk-reduction}
- LinkedIn Sponsored: insight angle {observation, framework, contrarian, list}
- LinkedIn Document: content shape {case-study, framework, mistake-list, data-viz}

Score 1: ≥2 variants share archetype OR opening 3-gram OR proof
noun. Variants are paraphrases not tests; an A/B test would yield
no signal.

Score 3: Archetypes distinct but body cadence drifts toward shared
rhythm; one proof noun repeats across 2 variants.

Score 5: Every variant tests a distinct hypothesis on its format's
diversity dim. Pairwise Jaccard well below 0.3. No two variants share
opening 8-token or proof noun.

Provide your reasoning and the score."""

_AD_6 = """\
Evaluate this ad creative for ONE quality:
Voice fidelity. The variant must sound like the client's other
channels — not the agent's house-style AI register.

Anti-pattern caps (per src/ads/compliance/anti_patterns.py):
- Any anti-pattern hit → cap at 3 (voice slipped into AI house-style)
- "AI-powered" / "Seamlessly" / "Game-changer" / "Cutting-edge" /
  "Built for modern teams" → all hits

Falsifiable floor:
- Zero presence of banned-word list (Meta health-vertical for
  health clients; LinkedIn aggressive for LI ads)
- voice_persona phrasebook overlap ≥ threshold (operator-set per client)

Score 1: Generic SaaS register throughout — "AI-powered seamlessly
integrating cutting-edge holistic solutions". Anti-pattern caps
fire. Variant could ship for any client; nothing client-specific.

Score 3: Voice register matches client's vertical but slips into
agent house-style for 1-2 sentences. Anti-pattern hit caps the score.

Score 5: Voice is unmistakably the client's. Phrasebook overlap
matches their organic content. No anti-pattern hits. Reader couldn't
tell this from a hand-written ad by the client team.

Provide your reasoning and the score."""

_AD_7 = """\
Evaluate this ad creative for ONE quality:
Market-signal alignment. Does the variant ride competitor saturation
patterns OR counter-position against them? Per the signal aggregator
brief: `recurring_hook_archetypes` shows what's saturated; the
variant should pick a stance (amplify or counter) — NOT silently
mimic.

R19 NO-OP CLAUSE: when `signal_aggregator.all_meta_sources_degraded ==
True`, this rubric scores N/A (defaults to 5). The rubric depends
on signal availability; missing signal is operational, not the
variant's fault.

Falsifiable floor: the agent must cite `brief.recurring_hook_archetypes`
EITHER as counter (variant's hook explicitly differs from saturated
archetype) OR as amplify (variant rides the archetype with a new
angle that the brief identifies as an opening).

Score 1: Variant is structurally identical to top-saturated
competitor archetype without differentiation lever. Reader sees
"oh, another one of these".

Score 3: Variant rides a saturated archetype with mild
differentiation (different proof noun) but no clear counter or
amplify stance.

Score 5: Variant explicitly counter-positions against the most-
saturated competitor archetype OR rides an archetype with a new
angle that the brief identifies as an opening.

Provide your reasoning and the score."""

_AD_8 = """\
Evaluate this ad+LP variant pair for ONE quality:
Conversion-readiness. Per TD-42 single-pass: each ad creative
ships with paired landing-page hero copy in one variant artifact.
The LP must satisfy:

Hard structural gates (computed in session_eval):
- `jaccard(tokenize(ad.hook), tokenize(lp.headline)) ≥ 0.4` after
  stopword removal — message-match drives 2.3% conversion lift per 1%
  alignment (top advertisers: 25% lift).
- `ad.cta.verb == lp.primary_cta.verb` (exact match)
- `ad.body.proof_noun ∈ lp.proof_point`

Score 1: LP hero contradicts ad promise. Message-match gate fails.
CTA verb mismatch (ad says "Book a demo" but LP CTA says "Sign up").
Reader feels bait-and-switch.

Score 3: Message-match gate passes at minimum threshold (Jaccard
0.4-0.5) but LP feels disconnected from ad's specific framing.

Score 5: Ad hook + LP headline share core promise + proof noun;
CTA verb exact-matches; conversion-readiness is real. Reader who
clicks lands on a page that affirms what the ad promised.

Provide your reasoning and the score."""


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
    # Article Engine — 8 rubrics (all gradient; AE-8 cross-item)
    # Per Content Engine v1 U13 + TD-40 / TD-44. Essential: thesis
    # falsifiability + citation verifiability + voice fidelity (the
    # lane's reason to exist). Pitfall: cross-cohort diversity is
    # actually important here (gating against batch homogeneity);
    # voice anti-patterns are baked into AE-4 essential because slop
    # register on a 1,500-word piece is fatal in a way it isn't on a
    # 280-char tweet.
    "AE-1": RubricTemplate("AE-1", "article_engine", "gradient", _AE_1, tier="important"),
    "AE-2": RubricTemplate("AE-2", "article_engine", "gradient", _AE_2, tier="essential"),
    "AE-3": RubricTemplate("AE-3", "article_engine", "gradient", _AE_3, tier="essential"),
    "AE-4": RubricTemplate("AE-4", "article_engine", "gradient", _AE_4, tier="essential"),
    "AE-5": RubricTemplate("AE-5", "article_engine", "gradient", _AE_5, tier="important"),
    "AE-6": RubricTemplate("AE-6", "article_engine", "gradient", _AE_6, tier="optional"),
    "AE-7": RubricTemplate("AE-7", "article_engine", "gradient", _AE_7, tier="important"),
    "AE-8": RubricTemplate("AE-8", "article_engine", "gradient", _AE_8, is_cross_item=True, tier="important"),
    # Image Engine — 8 rubrics (all gradient; IE-6 cross-item for carousels).
    # Per U14: IE-1/2/3/5/6 route through vision_judge (Gemini 3 Flash Preview
    # multimodal — per JR's 2026-05-19 update; D24 originally specified 2.5);
    # IE-4 (format), IE-7 (alt-text + caption voice), IE-8 (repurposability)
    # stay on the text-only outer judge service.
    # Tiers: essential = hook + brand + format + visual specificity (the four
    # that fail an image fully); important = info density + carousel arc +
    # alt-text/caption voice; optional = repurposability.
    "IE-1": RubricTemplate("IE-1", "image_engine", "gradient", _IE_1, tier="essential"),
    "IE-2": RubricTemplate("IE-2", "image_engine", "gradient", _IE_2, tier="essential"),
    "IE-3": RubricTemplate("IE-3", "image_engine", "gradient", _IE_3, tier="important"),
    "IE-4": RubricTemplate("IE-4", "image_engine", "gradient", _IE_4, tier="essential"),
    "IE-5": RubricTemplate("IE-5", "image_engine", "gradient", _IE_5, tier="essential"),
    "IE-6": RubricTemplate("IE-6", "image_engine", "gradient", _IE_6, is_cross_item=True, tier="important"),
    "IE-7": RubricTemplate("IE-7", "image_engine", "gradient", _IE_7, tier="important"),
    "IE-8": RubricTemplate("IE-8", "image_engine", "gradient", _IE_8, tier="optional"),
    # Ad Engine — 8 rubrics (all gradient; AD-5 cross-item). Per U15 +
    # TD-42. Tiers: essential = AD-1/AD-4/AD-8 (hook + platform compliance
    # + LP message-match); important = AD-2/AD-3/AD-5/AD-7 (CTA / offer
    # specificity / variant diversity / market-signal alignment);
    # pitfall = AD-6 (voice fidelity anti-patterns cap).
    "AD-1": RubricTemplate("AD-1", "ad_engine", "gradient", _AD_1, tier="essential"),
    "AD-2": RubricTemplate("AD-2", "ad_engine", "gradient", _AD_2, tier="important"),
    "AD-3": RubricTemplate("AD-3", "ad_engine", "gradient", _AD_3, tier="important"),
    "AD-4": RubricTemplate("AD-4", "ad_engine", "gradient", _AD_4, tier="essential"),
    "AD-5": RubricTemplate("AD-5", "ad_engine", "gradient", _AD_5, is_cross_item=True, tier="important"),
    "AD-6": RubricTemplate("AD-6", "ad_engine", "gradient", _AD_6, tier="pitfall"),
    "AD-7": RubricTemplate("AD-7", "ad_engine", "gradient", _AD_7, tier="important"),
    "AD-8": RubricTemplate("AD-8", "ad_engine", "gradient", _AD_8, tier="essential"),
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
# Content Engine v1 — reviewer-assist compliance rubric IDs (U8 + U13+).
#
# Per D12-hybrid + TD-11: lane-side LaneSpec.rubric_ids carries the per-
# lane compliance ID for each active rule set. The rubric prose lives in
# the shared reviewer_assist YAML registry — `prose_ref` resolves at
# evaluation time so editing a single rule propagates across all
# lanes that consume the rule set. The inline `prompt` is a stub that
# evaluators don't see when prose_ref is set; we keep it short for the
# tier-weighting hash without diluting the version fingerprint.
# ---------------------------------------------------------------------------

# Content engine lanes that carry per-rule-set compliance rubric IDs.
# U8 added storyboard (3 IDs); U13 added article_engine (3 IDs); U14
# adds image_engine (3 IDs). U15b (site_engine) extends this list with
# its own `<rule_set>_<lane>_compliance` entries via the same pattern.
_COMPLIANCE_LANES_V1: tuple[str, ...] = (
    "storyboard", "article_engine", "image_engine", "ad_engine",
)
_COMPLIANCE_RULE_SETS_V1: tuple[str, ...] = ("gdpr_eu", "medical_pl", "legal_pl")
for _lane in _COMPLIANCE_LANES_V1:
    for _rs in _COMPLIANCE_RULE_SETS_V1:
        _compliance_id = f"{_rs}_{_lane}_compliance"
        RUBRICS[_compliance_id] = RubricTemplate(
            criterion_id=_compliance_id,
            domain=_lane,
            scoring_type="gradient",
            prompt=(
                f"Reviewer-assist {_rs} pre-check for {_lane}. Prose resolves "
                f"at evaluation time via reviewer_assist/checklists/{_rs}.yaml."
            ),
            tier="essential",  # reviewer-assist gates are essential weight
            prose_ref=f"reviewer_assist/checklists/{_rs}.yaml#{_lane}_compliance",
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
