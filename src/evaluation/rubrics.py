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

# GEO-1 / Passage Self-Containment — Volpini chunk-completeness; Profound 40-75w
# passage 3.1× citation rate; Search Engine Land "passage as unit of competition";
# Shepard #13 Self-Contained Passages (8.0).
_GEO_1 = """\
Evaluate this optimized page content for ONE quality:
Could an AI search engine extract any 40-75 word passage and use
it as a complete answer — with named entities, specific claims, and
no orphan pronouns or "as mentioned above" references?

AI engines retrieve and cite passages, not pages (per Search Engine
Land's 8,000-citation analysis). Profound's 10K-passage study found
40-75 word passages cited 3.1× more often than longer ones. The
unit of competition is the passage; Volpini's "chunk-completeness"
principle is the operational test.

Score 1: Passages depend on surrounding context to make sense.
Paragraphs reference "this," "the above," "as mentioned earlier."
Headings don't restate the entity; lists where items 2-5 require
item 1 for context. A reader extracting any single paragraph could
not understand it without prior reading.

Score 5: Every substantive passage stands alone. Each 40-75 word
block names the entity it discusses (no floating pronouns), contains
its own context, and delivers a complete thought. Headings restate
the entity. Lists are self-resolving. An AI engine could lift any
single block and the reader would understand it without visiting
the rest of the page.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

# GEO-2 / Evidence Density — Aggarwal et al. KDD 2024 top-three methods (Quotation
# Addition +28-40%, Statistics Addition +30-40%, Cite Sources +30-40%); Yext 17.2M-
# citation study (first-party data → 4.31× citation occurrences); Shepard #8 "Cites
# Sources" (8.0); rank-5 pages got +115% citation lift from Cite Sources vs -30% for
# rank-1 pages (Aggarwal §6.2 — these levers help weaker pages disproportionately,
# directly relevant to first-party landing pages).
_GEO_2 = """\
Evaluate this optimized page content for ONE quality:
Does the content inject verifiable evidence — quantitative figures
with sources, direct quotations from credible third parties, inline
citations to first-party data or external authority — at the density
that correlates with AI-engine citation lift?

Aggarwal et al. (KDD 2024) ran 9 optimization methods against
generative engines; the three with the largest visibility lift were
all evidence-injection: Quotation Addition (+28-40%), Statistics
Addition (+30-40%), Cite Sources (+30-40%). Yext's 17.2M-citation
analysis: sites with original first-party data get 4.31× more
citation occurrences per URL.

Score 1: Claims are vague qualitative marketing copy ("leading,"
"industry-best," "trusted by thousands"). Numbers appear without
attribution. Every linked source is a sibling page on the same
domain (no third-party citations). The content reads like sales
copy with no fact-checkable substance.

Score 5: Most substantive claims pair with verifiable evidence —
specific dated statistics with named sources, direct quotations
from named third parties, inline citations to external authorities
or first-party methodology with stated collection method. A
fact-checker could trace each material claim to a verifiable
source. Specificity serves the argument, not word count.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

# GEO-3 / Third-Party Validation and Competitive Acknowledgment — Forrester 2026
# (AI buyers validate vendor claims against external sources before trusting); Status
# Labs / ALM Corp "Citation Gap" research (vendor self-isolation fails to earn
# citations); The Verge documented Google AI Mode flagging vendor "best of" lists
# that placed their own products first; Ahrefs brand-mention correlation r=0.664 vs
# backlinks r=0.218 (mentions in external text drive citation more than link graph).
_GEO_3 = """\
Evaluate this optimized page content for ONE quality:
Does the content treat the competitive landscape as something that
exists — naming alternatives, citing third-party comparisons or
analyst coverage, quoting external voices — rather than presenting
itself in a vendor-vacuum?

Per Forrester's 2026 research, AI buyers validate vendor claims
against external sources before trusting them. The Verge documented
Google AI Mode discounting vendor-authored "best of" lists that
placed their own products first. Ahrefs' 75K-brand finding:
unlinked brand mentions in external text correlate with AI Overview
visibility 3× more strongly than backlinks (r=0.664 vs 0.218) —
which only happens when the brand engages a real ecosystem.

Score 1: Zero mention of alternatives or category. "Trusted by
[logo wall]" with no source for any logo. Self-comparison only
(us-vs-old-us). Cites zero external voices. Claims category
leadership without an analyst, journalist, or comparison-site
reference. Or acknowledges competitors only to attack them.

Score 5: The content names alternatives (including "do nothing"
options per Dunford-style competitive analysis), cites at least one
external voice (analyst report, journalist coverage, comparison
site, named customer quote) that exists outside the brand's
control, and acknowledges at least one specific area where a named
alternative genuinely wins — specific enough that a reader could
verify or dispute the acknowledgment.

Provide your reasoning, cite specific evidence from the content,
then give your score."""

# GEO-4 / Entity Consistency and Semantic Triples — Kalicube Entity SEO (Jason
# Barnard), derived from Bill Slawski patent analysis; Shepard #19 Entity Consistency
# (5.8); Volpini's argument that knowledge-graph-grounded retrieval produces stronger
# entity centering and cleaner narrative flow. Embeddings cluster name variants as
# separate entities — drift fragments citation signal across query variants.
_GEO_4 = """\
Evaluate this optimized page content for ONE quality:
Does the page present the brand/product/service as a stable entity
via consistent canonical naming and repeated subject-predicate-object
statements that a knowledge graph could ingest?

Kalicube's Entity SEO framework (derived from Bill Slawski's patent
analysis) holds that engines build entity models from repeated
"subject-predicate-object" triples ("Freddy is a content engine for
regulated B2B"). Embeddings cluster name variants as separate
entities — "Acme Pay," "AcmePay," "Acme's payment platform" all get
embedded as distinct things, fragmenting citation signal. Compare
the optimized content against the provided original page content
(pages/{{slug}}.json) for canonical naming consistency.

Score 1: The same product/brand is named differently across
sections (capitalization drift, spacing drift, paraphrased label
drift). No one-sentence entity definition near the top. No clear
category placement. Predicate drift — page describes the product
as multiple incompatible things ("a platform," then "a marketplace,"
then "a workflow tool"). A knowledge graph would record this as
multiple entities, not one.

Score 5: Canonical naming consistent everywhere — same string,
same capitalization, same spacing in every reference. A one-sentence
entity definition appears early ("X is an A for B who need C"). At
least 2-3 subject-predicate-object statements repeat the entity's
identity across sections ("X serves..." / "X provides..." / "X
differs from Y by..."). Predicate-level claims are mutually
consistent. A knowledge graph could ingest this as a single
coherent entity.

Provide your reasoning, cite specific evidence from the content
and the original page, then give your score."""

# GEO-5 / Answer-First Lead (BLUF compliance) — Perplexity 90/100w finding (Skywork
# 2025: 90% of top-cited Perplexity answers deliver the core question in the first
# 100 words); Volpini's "Matryoshka Paragraph" argument (Google's asymmetric
# embedding scheme front-loads early dimensions; pages leading with a query echo get
# discounted vs pages leading with a declarative definition); Profound's 10K-passage
# study (44% of AI citations come from the top third of pages); Norg / MintCopy /
# Claire Broadley BLUF (Bottom Line Up Front) research — BLUF-structured articles
# got 3.8× more citations.
_GEO_5 = """\
Evaluate this optimized page content for ONE quality:
Does the page's primary claim — what the product/service is, who
it serves, what makes it different — land in the first 40-75 words
of meaningful body content, in declarative-document register (not
query-echo register)?

Per Skywork's 2025 Perplexity analysis, 90% of top-cited answers
deliver the core question in the first 100 words. Profound's 10K-
passage study found 44% of AI citations come from the top third of
pages. Volpini's "Matryoshka Paragraph" argument: under Google's
asymmetric embedding scheme, pages that lead with a query echo
("What is X?") get discounted vs pages that lead with a declarative
definition ("X is an A for B who need C") — query-mirroring signals
"another query" not "an answer."

Score 1: Page opens with "What is X?" or paraphrases the likely
search query. Marketing throat-clearing precedes the definition.
The definitional sentence appears below brand storytelling or
below a hero image's caption. The first 40-75 words could belong
to any page in the category — no entity-specific claim is
present yet.

Score 5: The page's first 40-75 words of meaningful body content
land a declarative claim that names the entity, identifies its
category, names its primary differentiator, and names its target
audience — in document register, not question register. A reader
who reads only the first paragraph can describe what this is and
who it's for without further reading.

Provide your reasoning, cite the actual opening text, then give
your score."""

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

# GEO-7 / Search-Intent and Format Match — Shepard #5 Query-Answer Match (9.2);
# Shepard #6 Intent-Format Match (9.0); Profound's table-vs-prose finding (4.2×
# citation rate for tables on comparison content); Aggarwal et al. domain-specific
# finding (different methods win in different domains — Statistics Addition for Law
# & Government, Quotation Addition for People & Society, Fluency for Health).
_GEO_7 = """\
Evaluate this optimized page content for ONE quality:
Does the page's structure match the format AI engines prefer for
its declared target query class — and is each declared target
query directly answered by a specific passage on the page?

Per Shepard's meta-analysis of 54 experiments, Query-Answer Match
(factor #5, score 9.2) and Intent-Format Match (factor #6, score
9.0) are the two highest-correlated AI-citation factors. Profound's
10K-passage study found tables get cited 4.2× more often than
equivalent prose on comparison content. Aggarwal et al. (KDD 2024)
showed format-intent fit is domain-specific.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does the page declare its target queries explicitly (in the
   page header or a target_queries field)? A page that hedges
   across all queries excels at none.

2. For each declared target query, does the content contain a
   specific passage that directly and completely answers it —
   not tangentially related, but the responsive answer the AI
   engine would extract?

3. Does the page's structure match the query class? "Best X for Y"
   queries → comparison structure with at least one table or
   list. "How to X" → ordered stepwise structure. "X vs Y" →
   side-by-side table. "What is X" → definition lead + structured
   detail. Comparison content written as flowing prose without
   tables fails this sub-question.

4. Is each target-query answer findable within the first few
   paragraphs of the relevant content block — not buried below
   marketing material?

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

# GEO-9 / Freshness and Citable Specifics — Ahrefs 17M-citation freshness study (AI
# assistants prefer fresher content even when underlying facts haven't changed);
# Search Engine Land 8K-citation analysis (44% of AI Overview citations are from
# current-year content, 85% from the last few years); Skywork 2025 Perplexity finding
# (70% of top-cited Perplexity sources have a visible publication or update date
# within 12-18 months); Volpini's "verifiable citation triggers — concrete numbers,
# dates, standards, primary sources."
_GEO_9 = """\
Evaluate this optimized page content for ONE quality:
Does the page provide AI engines with the freshness signals they
preferentially weight — visible publication or update date, current-
year references in body content, dated data points, recent third-
party citations?

Per Ahrefs' 17M-citation freshness study, AI assistants prefer
fresher content even when underlying facts are stable. Search Engine
Land's 8K-citation analysis found 44% of AI Overview citations come
from current-year content, 85% from the last few years. Skywork's
2025 Perplexity analysis: 70% of top-cited Perplexity sources have
a visible publication or update date within 12-18 months.

Score 1: No visible date anywhere on the page. Stats appear without
years ("studies show 80%..."). Generic evergreen tone where dated
specifics would land harder ("modern," "today's," "the latest").
Third-party citations are undated. A last-updated stamp from a
prior year sits on a page making current-state claims.

Score 5: A visible publication or update date appears near the
top, dated within the last 12-18 months. Body content contains
current-year references where relevant ("in 2026," "Q1 2026
data"). Statistics are time-stamped ("Aggarwal 2024," "per
Ahrefs' Q1 2026 75K-brand study"). Third-party citations include
dates. The content commits to a specific time horizon rather than
hedging with evergreen vagueness.

Provide your reasoning, cite specific evidence from the content,
then give your score."""


# ---------------------------------------------------------------------------
# Competitive Intelligence (8 rubrics)
# ---------------------------------------------------------------------------

# CI-1 / Has a Point of View, Not a Catalogue — Octopus Intelligence "your point of
# view should sit prominently at the very top of your document, captured succinctly
# in your headline"; Klue executive-briefing template (Headline → Rationale →
# Comparison → Implications → Recommendations); Competitive Intelligence Alliance
# names "no point of view" as the most common failure mode in CI newsletters. This
# is the dimension most CI directors test for first.
_CI_1 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief lead with a strategic claim (headline-as-claim), or
with description (headline-as-topic)?

Per Octopus Intelligence: "If it doesn't change how your company
thinks and acts, you've just created a data dump, not intelligence."
The Klue executive-briefing template — used by thousands of B2B CI
practitioners — hardcodes point-of-view-first structure: headline,
then rationale, then comparison, then implications, then
recommendations. The headline is a claim, not a topic.

Score 1: The executive summary catalogues competitor activity
without a strategic claim. The headline describes a topic ("Acme
launched a bundle on May 1") rather than committing to a position.
Sections introduce their own topics without a shared argument.
The reader finishes knowing facts but no conclusion.

Score 5: The executive summary leads with a single, client-specific
strategic claim a decision-maker could accept or reject ("Acme's
bundling strategy targets our SMB renewal base; if we don't respond
by Q3, we lose the discount-sensitive 30% of the cohort"). Every
subsequent section provides evidence for, against, or nuance to
that claim. The reader can state the brief's central argument in
one sentence after reading only the executive summary.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

# CI-2 / Evidence → Inference → Implication → Recommendation Chain — SCIP
# methodology; Octopus Intelligence's "so what" discipline ("every observation
# should be followed by an inference and a 'so what' that connects to a specific
# business or marketing decision"); Heuer & Pherson Structured Analytic Techniques
# tradition demands the analyst show their reasoning chain.
_CI_2 = """\
Evaluate this competitive intelligence brief for ONE quality:
For each finding, does the brief explicitly walk from observation,
to what it lets us infer, to what it implies for us, to what we
should do — forcing a "so what?" at every stage?

The Competitive Intelligence Alliance frames this as the discipline
that distinguishes intelligence from reporting. Heuer & Pherson's
analytic tradecraft demands the same chain — the analyst must show
their reasoning. McKinsey's war-gaming output is "strategic
guidance," never a fact dump.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every key observation in the brief name a specific data
   source (tool, API, publication, URL, dated filing) rather than
   generic references like "research shows" or "industry data"?

2. Does each observation lead to an explicit inference — what the
   observation lets the reader conclude — rather than presenting
   the observation as if its meaning were self-evident?

3. Does each inference lead to an explicit implication for the
   client — what does this mean for their decisions, their
   positioning, their priorities — rather than stopping at
   "Competitor X is doubling down on AI" with no so-what?

4. For each implication, is there a corresponding recommendation
   (or explicit "watch, no action yet" stance) so the reader knows
   what should happen next, rather than being left to assemble
   the decision themselves?

Provide your overall reasoning, then evaluate each sub-question."""

# CI-3 / Trajectory, Not Just Snapshot — CB Insights strategy-teardown structure
# ("WHAT it's DOING now → WHERE it's GOING next → WHY is this a priority?"), built
# from convergent signals across patents, M&A, earnings transcripts, headcount, and
# product launches; Andy Grove's 10X forces give the trajectory checklist
# (competition, technology, customers, suppliers, complementors, regulation);
# Wayne Gretzky aphorism — "skate to where the puck is going" — is the most-cited
# CI mantra for a reason.
_CI_3 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief reason about where each competitor is heading
(next 6-18 months) using convergent signals — patents, M&A,
headcount, earnings-call language, product roadmap — not just
where they are today?

CB Insights' strategy teardowns (Apple, Google, Amazon) impose a
standardised three-part structure on every priority area: WHAT
it's DOING now → WHERE it's GOING next → WHY is this a priority.
Grove's *Only the Paranoid Survive* names the same skill: spotting
a strategic inflection point requires reading the trajectory of
10X forces, not the current snapshot.

Score 1: Competitors are described as static snapshots — current
products, current pricing, current positioning. No mention of
what has changed recently, what is being built, or what has been
abandoned. The brief reads like a catalog, not an intelligence
report.

Score 5: Each competitor's trajectory is explicitly articulated
using at least 2-3 convergent signals (named patents, hiring data,
earnings-call quotes, product launches, M&A activity, abandoned
SKUs) that together imply a direction. The brief commits to a
forward projection — what each competitor will do in the next 6-18
months — specific enough that a reader could disagree by pointing
at the signals weighed incorrectly.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

# CI-4 / Identifies the Mechanism of Advantage — Helmer 7 Powers two-part test
# (every power requires a Benefit AND a Barrier); Porter "What Is Strategy?"
# operational-effectiveness vs strategic-positioning distinction; Roger Martin
# Can't/Won't Test (sustainable advantage requires a barrier competitors can't or
# won't replicate). The most rigorous published frame for separating real moats
# from claimed ones.
_CI_4 = """\
Evaluate this competitive intelligence brief for ONE quality:
When the brief claims a competitor has an advantage, does it
identify the mechanism — which of Helmer's 7 Powers (or which
Porter force) underlies it — and apply the Benefit AND Barrier
test, distinguishing operational effectiveness from strategic
positioning?

Helmer's framework: every power requires both a Benefit (materially
augmented cash flow via price, cost, or reduced investment) AND a
Barrier ("an obstacle that makes copying it unattractive"). The
seven powers are Scale Economies, Network Economies, Counter-
Positioning, Switching Costs, Branding, Cornered Resource, Process
Power. Porter's "What Is Strategy?" distinction: doing the same
things better than rivals (operational effectiveness, replicable)
is not strategy; doing different things or doing things differently
(strategic positioning, sustainable trade-offs) is.

Score 1: The brief asserts competitor advantages without naming a
mechanism. "Acme has scale economies" with no cost-curve evidence;
"Acme has network effects" without winner-take-all dynamics
identified; "Acme has brand strength" without examining whether
brand creates a barrier or just a benefit. Operational effectiveness
("they ship faster") is conflated with strategic positioning
("they made trade-offs we can't").

Score 5: Each named competitor advantage identifies a specific
Helmer power or Porter force AND applies both halves of the test —
the Benefit mechanism (where the cash flow comes from) AND the
Barrier mechanism (what makes it costly or impossible to copy).
The brief distinguishes operational effectiveness from strategic
positioning explicitly, and where counter-positioning is at play,
locates incumbents on Helmer's Denial→Ridicule→Fear→Anger→
Capitulation curve.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

# CI-5 / Names Strategic Posture and the Hard Trade-Off — Roger Martin Playing to
# Win Strategy Choice Cascade (Winning Aspiration → Where to Play → How to Win →
# Capabilities → Management Systems; where-to-play and how-to-win are inseparable);
# offensive/defensive/cooperative posture taxonomy from strategic-posture literature;
# "real strategy always costs something" — recommendations that require no trade-off
# are red flags.
_CI_5 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief recommend a specific strategic posture (attack /
defend / flank / cooperate / ignore) and surface the hard trade-off
the recommendation requires the client to accept?

Per Roger Martin's Playing to Win: strategy is a set of choices,
and where-to-play and how-to-win are inseparable. A recommendation
that names "how to win" without naming "where to play" — or vice
versa — has not yet earned the strategic claim. Real strategy
always costs something: recommendations that require no trade-off
indicate the brief is making product wishes, not strategic choices.

Score 1: Recommendations are presented as a flat list of priorities
with no chosen posture. Multiple recommendations of equal weight
with no priority. Recommendations that require no trade-off (do X
AND Y AND Z, with no acknowledgment of what's lost). Or
recommendations that name "how to win" without specifying "where
to play" (or the inverse).

Score 5: The brief commits to a specific posture for the client
in this competitive context — attack on this front, defend on that
front, flank here, cooperate there, deliberately ignore the rest.
For the recommended posture, the brief names the where-to-play
choice AND the how-to-win choice AND the explicit trade-off being
accepted ("if we win this segment we cannot also win that segment;
here's why this segment matters more"). A stakeholder could rebut
the trade-off framing — that's the test that real strategic choice
is on the table.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

# CI-6 / Surfaces Uncomfortable Truths and Considers Alternative Hypotheses —
# Heuer & Pherson Structured Analytic Techniques (Analysis of Competing Hypotheses,
# Key Assumptions Check, What-If? analysis); Competitive Intelligence Alliance
# names "bias — leaders may dismiss insights contradicting their market assumptions"
# as a top-five failure mode; Klue's "kill your darlings" discipline is what
# separates CI that lands from CI that placates.
_CI_6 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief surface uncomfortable truths the client would push
back on, consider at least one plausible alternative hypothesis
(ACH-style) for the competitor's behavior, and name its key
assumptions explicitly?

You have been provided a client context document (from
_client_baseline.json and session.md). Check the client's stated
positioning and known beliefs. The Heuer & Pherson analytic
tradecraft demands the analyst surface assumptions and consider
alternatives. The Competitive Intelligence Alliance's phrasing:
"executives tend to be surrounded by human filters whose job seems
to be to keep those executives isolated from reality" — so a CI
brief is one of the rare channels that *should* carry uncomfortable
truths upward.

Score 1: The brief only reinforces the client's existing beliefs.
Every finding positions the client favorably. No competitor
advantage is presented as durable or difficult to overcome. No
alternative hypothesis is considered for any major finding. Key
assumptions are unstated. Or: uncomfortable findings are present
but immediately neutralized with hedge sentences ("while X, the
client's broader platform compensates").

Score 5: The brief states at least one finding a stakeholder would
push back on — a durable competitor advantage the client cannot
quickly close, a structural weakness in the client's approach, or
a market trend undermining the client's strategy — and the finding
is specific enough that a stakeholder could plausibly veto its
inclusion ("we shouldn't say this"). For at least one major
finding, the brief considers a plausible alternative hypothesis
(ACH-style: "the data could mean X, or it could mean Y; here's
why X is more supported"). Key assumptions are named explicitly.

Provide your reasoning, cite specific evidence from the brief
and the client context document, then give your score."""

# CI-7 / Hard Prioritisation: Top 2-3 Actions, Time-Bound — Klue's top 3-5 findings
# / 2-3 recommendations rule; Competitive Intelligence Alliance standard
# ("specific, actionable, tied to business impact"); Product Marketing Alliance
# rejection of "vague statements like 'increase productivity'"; executive failure
# mode is "information overload" — the discipline is editing.
_CI_7 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief end with a small number (ideally 2-3) of time-bound,
specific recommendations, with the rest cut or explicitly
deprioritised — and are recommendations concrete enough to commit
to ("invest in X by Q3" / "ship feature Y by Oct 15") rather than
vague ("explore," "consider," "evaluate")?

Per the Competitive Intelligence Alliance, "executives tend to be
surrounded by human filters" — they will not consume the eighth
finding. Klue's published guidance: 3-5 findings, 2-3
recommendations per cycle. Product Marketing Alliance rejects
"vague statements like 'increase productivity'"; recommendations
must be "specific and measurable."

Score 1: 8+ recommendations of equal weight. Everything is "high
impact." No deadlines, or deadlines like "soon" / "next quarter."
Verbs are explore / consider / evaluate / monitor (no commitment).
The reader finishes with a long list and no sense of where to start.

Score 5: Exactly 2-3 top-tier recommendations clearly separated
from secondary items through structure or explicit ranking. Each
top recommendation includes (a) a specific action, not a verb-of-
interest; (b) a dated deadline ("by Q3 2026" / "by Oct 15"); (c)
the consequence of inaction or the priority rationale (what's
gained by doing this first, what's lost by sequencing it later).
The brief explicitly names what is being deprioritised, not just
what is prioritised.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""

# CI-8 / Industry-Structure Context — BCG Advantage Matrix (Volume / Stalemate /
# Fragmented / Specialisation — different industries reward different strategies);
# Porter's Five Forces (rivalry, supplier power, buyer power, substitutes, new
# entrants — industry profitability is shaped by five forces, not one). A strategic
# recommendation tuned to a Volume industry is wrong for a Stalemate one. Per Porter,
# strategists "define competition too narrowly, as if it occurred only among
# today's direct competitors."
_CI_8 = """\
Evaluate this competitive intelligence brief for ONE quality:
Does the brief locate its competitive analysis inside the
industry's structural context — naming where the industry sits on
the BCG Advantage Matrix (Volume / Stalemate / Fragmented /
Specialisation) and accounting for at least three of Porter's five
forces beyond direct rivalry?

The BCG Advantage Matrix classifies industries by (a) number of
viable approaches to competitive advantage and (b) size of that
advantage when achieved. Volume industries (few approaches, big
advantage) reward scale; Specialisation industries (many
approaches, big advantage) reward differentiation; Stalemate
industries reward defensive operational excellence; Fragmented
industries reward niche dominance. A strategic recommendation
that ignores this structure is recommending in the abstract.
Porter's contention is that focusing only on direct rivals misses
80% of the structural pressure.

Score 1: The brief analyses only direct rivals. No statement about
industry structure, no positioning on the BCG matrix, no
consideration of suppliers, buyers, substitutes, or new entrants.
Strategic recommendations follow as if competition were a two-
player game in a vacuum. The brief does not distinguish a Volume
recommendation from a Specialisation recommendation.

Score 5: The brief explicitly locates the industry on the BCG
Advantage Matrix (Volume / Stalemate / Fragmented / Specialisation)
with named-evidence reasoning. At least three of Porter's five
forces are accounted for beyond direct rivalry — supplier power
(named suppliers + leverage), buyer power (named buyer concentration
or switching cost dynamics), threat of substitutes (named non-
direct alternatives), or threat of new entrants (named barrier
height + recent entrant activity). The strategic recommendation
is consistent with this structural picture.

Provide your reasoning, cite specific evidence from the brief,
then give your score."""


# ---------------------------------------------------------------------------
# Monitoring Digest (6 rubrics)
# ---------------------------------------------------------------------------

# MON-1 / Baseline-Relative Framing of "What Changed" — Brandwatch crisis-alert
# guidance ("establish benchmarks that define what a normal level of negativity
# online looks like for their brand"); Sprout Social Share-of-Voice practice; ESOV
# (Excess Share of Voice — the gap between SoV and market share is the
# practitioner-standard interpretation rule). Without a baseline, a number is not
# a signal.
_MON_1 = """\
Evaluate this monitoring digest for ONE quality:
Does the digest express developments as deltas from a defined
baseline (prior week, 4-week trailing average, peer set), not as
absolute counts?

Per Brandwatch's published crisis-alert methodology, the unit of
analysis must be delta from baseline. "230 mentions this week" with
no comparator is not a signal. The five named warning indicators
Brandwatch publishes are all delta-form: (1) sustained volume rise,
(2) sudden spike, (3) sharp sentiment shift, (4) traditional-media
amplification, (5) high-profile-individual mention. For first-week
digests with no prior data, baseline means deviation from what a
naive observer would expect.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is at least one key metric quantified with direction AND
   magnitude vs a named baseline (specific prior period with a
   date, rolling-average with stated window, named industry
   benchmark, or stated expectation)?

2. Does the digest provide a comparison frame for its key data
   rather than reporting raw counts? Competitor volume reported
   without the focal-brand counterpart fails; sentiment reported
   as "62% positive" without "vs 78% baseline" fails.

3. For the most significant development reported, does the digest
   classify its trajectory (new / escalating / continuing /
   anomalous) relative to the baseline or stated expectations?

4. Where an obvious event-driven inflection point exists (campaign
   launch, regulatory letter, crisis), does the digest state the
   pre-vs-post-event delta rather than treating "post" data in
   isolation?

Provide your overall reasoning, then evaluate each sub-question.
Cite specific evidence from the digest and the raw mention data."""

# MON-2 / Severity Tiering with Defensible Classification — Cision React Score
# two-axis severity model (Harm + Emotionality on Plutchik primary emotions);
# Coombs Situational Crisis Communication Theory (SCCT) clusters (Victim /
# Accidental / Intentional-Preventable, mapping to response toolkit Deny / Diminish
# / Rebuild / Bolster); FAA Airworthiness Directive makes severity a structural
# required field. A digest that doesn't tier forces the reader to do the tiering.
_MON_2 = """\
Evaluate this monitoring digest for ONE quality:
Are surfaced developments explicitly tiered with a defensible
classification — anchored in a model the reader can interrogate,
not vibes — including orthogonal axes (harm + emotionality) and
SCCT cluster where attribution matters?

Cision's React Score tiers content into high/medium/low risk by
scoring two orthogonal dimensions: Harm (racism, hate speech,
insult, threat, toxicity) and Emotionality (Plutchik's 8 primary
emotions). A competitor announcement may be emotionally charged
without being harmful; a regulator's quiet enforcement letter may
carry zero outrage but high harm potential. Single-dimension
sentiment misses both. Coombs SCCT clusters (Victim / Accidental /
Intentional) determine which response toolkit applies — a digest
classifying a development as "crisis" should implicitly answer
which cluster.

Score 1: Items are presented at the same emphasis level with no
explicit tiering. Or "concerning" / "notable" / "significant"
used as if they were tiers without operational definition.
Severity implied by ordering alone. Coverage gaps not reflected
in confidence (a crisis call on single-source data treated equal
to one on multi-source corroboration). No SCCT-cluster framing
when attribution to client/competitor materially changes response
options.

Score 5: Each material development is explicitly tiered (crisis /
opportunity / watch / noise or similar), with the classification
defended by named evidence — source count, coverage duration,
harm-axis severity, emotionality-axis severity. When the call is
a judgment, the digest names the alternative reading. SCCT cluster
is stated where attribution matters. Coverage gaps explicitly
modify severity: a crisis call on single-source data is flagged
as provisional.

Provide your reasoning, cite specific evidence from the digest
and the raw mention data, then give your score."""

# MON-3 / Highest-Stakes Lede in Position One — FullIntel executive-briefing
# template ("lead with the most important fact" / "Long briefings don't signal
# thoroughness — they signal poor judgment"); President's Daily Brief format
# precedent (highest-stakes item first, not loudest); SVB (ISOC case study) + US
# Secret Service Butler-rally response (PRNews) both diagnose "ceding the
# narrative" via buried-lede framing as the defining failure mode. The unit of
# emphasis is stakes, not volume or sentiment-extremity.
_MON_3 = """\
Evaluate this monitoring digest for ONE quality:
Does the development with the largest expected impact on the
client's strategic interests open the digest, with structural
emphasis (length, headline weight, position) proportional to
stakes — not to volume, novelty, or sentiment extremity?

Per FullIntel's executive-briefing template: 200-400 words total,
4-6 sentences per item, lede placement explicit. The PDB historical
format opens with the highest-stakes item, never the loudest. The
SVB collapse + US Secret Service post-mortems both name buried-lede
framing as the defining communication failure: "delayed and sparse
statements at the peak of the crisis created conditions for
conspiracy theories and confusion."

Score 1: Routine product chatter sits at the top because it had
the highest volume. A regulatory letter or material competitor
move appears at item 4-6 because it was quiet. Visual emphasis
(bold, callout) given to the most surprising item rather than the
most consequential. Word count tracks drama, not stakes. The
reader must read the whole digest to find out what matters.

Score 5: The highest-stakes development opens the digest in
position one and is explicitly framed as such ("This week's lede:
[X], because [stakes-rationale]"). Structural emphasis — position,
length, headline weight — is proportional to stakes, not volume.
If nothing extraordinary happened, the digest says so plainly
rather than inflating routine signals. The reader can identify
the top development from the first 100 words.

Provide your reasoning, cite specific evidence from the digest,
then give your score."""

# MON-4 / Action Items with Named Owner + Deadline + Consequence (FAA-Style) —
# FAA Airworthiness Directive format (14 CFR Part 39): every directive specifies
# unsafe condition, applicability, required action, compliance time, and
# alternative methods. FullIntel's "recommended action or watch status — one
# sentence" imports the structure into PR briefings. The 1982 Tylenol response is
# the gold-standard precedent (J&J CEO James Burke direct-contacted network heads
# immediately, recall within hours — owner + deadline + consequence specified to
# the minute). "Continue to monitor" is not an action item.
_MON_4 = """\
Evaluate this monitoring digest for ONE quality:
Do action items follow the FAA-directive structure — (a) specific
named owner, (b) compliance time (specific date or window), (c)
consequence of inaction?

Per 14 CFR Part 39 (FAA Airworthiness Directive format), every
directive specifies an unsafe condition, applicability, required
action, compliance time, and alternative methods. FullIntel
imports this structure into PR briefings via one-sentence
"recommended action or watch status." A recommendation without
all three (owner + deadline + consequence) is not an action item;
it's an observation.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Does every action item name a specific responsible individual
   or role (named role with single decision-making authority, not
   "the team" / "you" / "Brand team")?

2. Does every action item include a bounded timeframe — a dated
   deadline or defined relative window with an explicit terminating
   condition ("by Friday 17:00 OR escalate to comms director"),
   not open-ended language ("soon," "as appropriate")?

3. Does each action item state a specific consequence of inaction
   the responsible party would want to avoid ("continued silence
   leads Reuters to publish without our quote"), not generic
   "negative impact"?

4. Are actions that cannot wait until next week explicitly
   separated from those that can — with different urgency markers,
   a distinct section, or explicit escalation triggers?

Provide your overall reasoning, then evaluate each sub-question."""

# MON-5 / Cross-Story Compound Narrative + Forward Projection — Harvard Law School
# "Narrative Contradictions" framework (cross-issue coherence as board-level
# governance failure when missed); Ansoff weak-signal theory (Strategic Early
# Warning Systems); PRovoke Media Crisis Review repeatedly diagnoses missed
# compounds as proximate cause of escalation; Dezenhall's *Glass Jaw* iceberg
# metaphor ("controversies are like icebergs — the small top above the water is
# all that the world sees").
_MON_5 = """\
Evaluate this monitoring digest for ONE quality:
Does the digest surface compound narratives where two or more
developments interact to carry an implication neither shows alone,
and project forward (next 1-2 weeks) rather than only describing
the present?

Per Dezenhall's Glass Jaw: "controversies are like icebergs — the
small top above the water is all that the world sees, but most of
what's really happening is happening in a place that few people
see." Cross-issue coherence is named at Harvard Law as a board-
level governance failure when missed. Ansoff weak-signal theory
defines the practitioner's job as detecting signals BEFORE they
crystalize. Corporate Foresight Initiative finds firms with formal
weak-signal scanning are 33% more likely to outperform peers
financially.

Score 1: Each story stands alone with no connecting analysis.
"Competitor launched X" and "regulator commented on category Y"
sit in separate sections with no acknowledgment they're the same
narrative. No "what to watch next" section, or that section is
filled with platitudes ("we'll continue monitoring"). Zero forward
projection beyond the current week.

Score 5: The digest surfaces at least one compound narrative
where the joint signal across stories carries an implication
neither shows alone — a causal chain, trend amplification, or
structural risk visible only at the cross-story level. At least
one compound narrative includes a forward projection with a
specific next-period condition that would confirm or refute it
("if signal X appears by date Y, the projection holds; otherwise
the alternative reading wins"). Projections are conditional and
falsifiable, not vague ("this could escalate").

Provide your reasoning, cite specific cross-story connections
(or note their absence), then give your score."""

# MON-6 / "So What" Interpretation Including Absent Expected Signals — FullIntel
# "the 'so what' that turns information into intelligence is exactly what
# separates a briefing from a clip dump"; AMEC Integrated Evaluation Framework
# (outputs → out-takes → outcomes → impact; Barcelona Principles outcomes-over-
# outputs); Wells Fargo (2002 board warnings) + BP Deepwater Horizon (cement-
# test results) + Boeing 737 MAX (engineer flags) all show absence-of-expected-
# signal is the canonical weak-signal pattern institutional monitoring misses;
# PDB precedent of "Canada — [blank page]" as analytic comment is direct
# precedent for flagging silence as content; Edelman ethics-vs-competence
# decomposition (~76% trust capital from ethics dimensions); Sandman Risk = Hazard
# + Outrage framework.
_MON_6 = """\
Evaluate this monitoring digest for ONE quality:
Are numbers interpreted (not just reported) — and does the digest
flag what should have been there but wasn't?

Per FullIntel: "the so what separates a briefing from a clip
dump." AMEC's outcomes-over-outputs principle holds that volume +
reach + AVE alone fail the basic professional standard. The
Wells Fargo / BP / Boeing 737 MAX trio show that absence-of-
expected-signal is the canonical weak-signal pattern monitoring
tends to miss — the PDB convention of "Canada — [blank page]" as
analytic comment is direct precedent for flagging silence as
content.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. Is every key statistic in the digest paired with interpretation
   that names a specific client decision or implication it would
   change — not restated description ("32% increase represents
   significant growth" fails)?

2. Does at least one statistic pre-empt a reader's likely
   alternative interpretation, naming what someone might wrongly
   conclude and why that reading fails ("up 32% — but watch out,
   this is from a near-zero baseline, so absolute volume is still
   small")?

3. Does the digest flag at least one absent expected signal —
   the campaign that generated no coverage, the competitor that
   went quiet, the response that never materialised — and
   interpret what the absence might mean ("Competitor X went
   quiet, consistent with either Y or Z, and we'll know which
   by next period")?

4. Where sentiment-axis or stakeholder-trust data appears, does
   the digest distinguish ethics-axis exposure (which drives ~76%
   of trust capital per Edelman) from competence-axis exposure
   (~24%), and outrage-driven from hazard-driven framing (per
   Sandman) — rather than collapsing both into a single sentiment
   score?

Provide your overall reasoning, then evaluate each sub-question.
Cite specific evidence from the digest and the raw mention data."""

# MON-7 (temporal arc) DROPPED 2026-05-15 per Phase 4 synthesis — flagged as
# lowest-confidence by domain agent; risk of rewarding cosmetic "previously on…"
# recaps that aren't load-bearing.
# MON-8 (word count proportional to importance) FOLDED 2026-05-15 into MON-3's
# structural emphasis dimension (lede placement + emphasis proportional to stakes).


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

# SB-7 / Creator-Specific Pacing — SHARPENED 2026-05-15 to require a NAMED reset
# beat for plans over ~45s. Reference: MrBeast handbook's "minute-3 and minute-6"
# rhythm convention (re-engagement beats that recover attention mid-video are a
# distinct craft act, not implicit in cadence). Current cadence-only framing
# allowed plans to pass with implied resets the plan never named.
_SB_7 = """\
Evaluate this story plan for ONE quality:
Are scene count, cut frequency, and duration target grounded in
how this creator's actual videos move — and, for plans over ~45
seconds, does the plan name where the re-engagement / reset beat
happens?

Use the creator pattern data to understand this creator's typical
video structure, duration, and pacing. Per the MrBeast handbook's
"minute-3 and minute-6" convention, retention-driven creators
deliberately place named reset beats at attention-decline points;
these are a craft act, not implicit in average pacing.

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

4. For plans over ~45 seconds, does the plan explicitly name AT
   LEAST ONE re-engagement / reset beat with placement (which beat,
   what timestamp or beat number) — not just "the pacing keeps
   attention" but a specific named act, image, or revelation that
   recovers attention mid-plan? For plans under 45 seconds, this
   sub-question is N/A and should be scored YES.

5. Is the emotional arc compressed to fit the target duration —
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
    "GEO-9": RubricTemplate("GEO-9", "geo", "gradient", _GEO_9, tier="important"),
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
    "CI-8": RubricTemplate("CI-8", "competitive", "gradient", _CI_8, tier="important"),
    # Monitoring Digest — 6 rubrics (Phase 4 redesign 2026-05-15; MON-7 temporal
    # arc dropped, MON-8 word-count-proportional folded into MON-3 structural
    # emphasis). All grounded in named PR-measurement methodologies.
    "MON-1": RubricTemplate("MON-1", "monitoring", "checklist", _MON_1, tier="essential"),
    "MON-2": RubricTemplate("MON-2", "monitoring", "gradient", _MON_2, tier="important"),
    "MON-3": RubricTemplate("MON-3", "monitoring", "gradient", _MON_3, tier="essential"),
    "MON-4": RubricTemplate("MON-4", "monitoring", "checklist", _MON_4, tier="important"),
    "MON-5": RubricTemplate("MON-5", "monitoring", "gradient", _MON_5, tier="important"),
    "MON-6": RubricTemplate("MON-6", "monitoring", "checklist", _MON_6, tier="pitfall"),
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
# Verification
# ---------------------------------------------------------------------------

assert len(RUBRICS) == 52, f"Expected 52 rubrics (GEO 9 + CI 8 + MON 6 + SB 8 + MA 8 + X 7 incl. X-9 + LI 6), got {len(RUBRICS)}"

# Cross-check against the lane registry: every rubric ID declared on a LaneSpec
# must exist in RUBRICS, and the totals must agree. Catches the case where a
# new lane is added with rubric IDs that nobody wired into RUBRICS, or where
# RUBRICS gains a new criterion that no lane claims.
from autoresearch.lane_registry import LANES as _LANE_SPECS  # noqa: E402

_lane_rubric_ids = {rid for spec in _LANE_SPECS.values() for rid in spec.rubric_ids}
_missing_in_rubrics = _lane_rubric_ids - set(RUBRICS)
assert not _missing_in_rubrics, (
    f"Lane registry declares rubric IDs not present in RUBRICS: {sorted(_missing_in_rubrics)}"
)
assert sum(len(spec.rubric_ids) for spec in _LANE_SPECS.values()) == len(RUBRICS), (
    f"Lane-registry rubric_id total {sum(len(spec.rubric_ids) for spec in _LANE_SPECS.values())} "
    f"!= RUBRICS total {len(RUBRICS)}"
)
