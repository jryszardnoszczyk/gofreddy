"""Rubric templates for the 32-criteria evaluation system.

Each rubric is either:
- gradient: scored on a 1/3/5 scale with anchor descriptions
- checklist: 4 binary YES/NO sub-questions

Domains: geo (8), competitive (6 — v3.3), monitoring (6 — v3), storyboard (8)
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
# GEO — Generative Engine Optimization (8 rubrics — v3 outcome-question shape)
# ---------------------------------------------------------------------------
# v3 design lands the outcome-question + binary-anchor + structured-CoT shape
# from `docs/handoffs/2026-05-18-judge-design-step1-geo.md` (v3 surgical
# edits — Option D) verified at `docs/handoffs/2026-05-19-geo-v3-
# verification.md`. Each criterion is scored 0 / 0.5 / 1 with a 0.5
# "unknown" anchor that forces the judge to name the missing evidence. The
# 1/3/5 gradient shape (pre-v3) was retired because it was vulnerable to
# feature-check drift (Phase 4 pathology) and slot-fill mimicry.
#
# Scoping note: the v3 spec architecture defines 6 judge-level criteria
# (GEO-1..GEO-6) for the page-level core component; GEO-6 (cross-page
# diversity) lives at the workflow CrossItemCriterion level in
# `session_eval_geo.py` while spec GEO-6 (engine-side re-citation
# resilience) is propagated here as GEO-7 because the lane_registry
# declares 8 rubric_ids for the geo lane. GEO-7 (formerly query-answer
# fit) carries the v3 spec GEO-6 evidence-chain criterion; GEO-8
# (formerly technical-recommendation specificity, gradient pitfall)
# remains as the binary technical-recommendation-specificity pitfall.
# The v3 spec's GEO-5 score-0 anchor folds the technical-recommendation
# concrete-count discipline (which lives standalone here in GEO-8). The
# 6-criterion alignment with the spec architecture is a v4 candidate —
# requires `_rubric_ids("GEO", count=6)` in lane_registry which is out
# of scope for this rubrics.py-only surgical edit.
#
# Scoring is binary at the criterion level; the scorer_binary.md prompt
# template maps the per-criterion 0/0.5/1 values onto the 0-10
# aggregate_score envelope the substrate already consumes.

_GEO_1 = """\
Evaluate this optimized page content on ONE outcome question:

Does the page surface a primary claim — what the product / service
/ entity is, who it serves, what makes it different — in the
first 40-75 words of meaningful body content, in declarative-
document register (not query-echo register), AND does that
40-75-word passage carry a substantive claim a domain expert in
the page's target vertical would defend? Would an AI engine
extracting the top passage emit a complete, citable answer that a
sophisticated human reader would also accept as reference-grade?

Score 1 (yes) — First 40-75 words of the page (or the
recommended BLUF lead for the audited client page) contain BOTH
(a) a declarative entity definition + category placement + a
differentiation claim in retrieval-document register (no
interrogative opener, no brand storytelling preamble, no
deprecated keyword-density-targeted lede), AND (b) a substantive
claim that names the specific vertical / target reader /
non-generic differentiator that a domain expert would defend. An
AI engine could emit those 75 words verbatim AND a sophisticated
human reader would not classify the page as "generic AI content"
on the strength of the first passage alone. The passage works as
standalone AND fits the page's existing voice, structure, and
scope — content reads like it was always there, not bolted on.
Surgical-content-injection test: a developer reading the brief
could ship the passage without interpretation, and a returning
reader who knew the prior page voice would not perceive a
register break.

Illustrative example — B2B SaaS (do not optimize toward this
exact shape): "Linear is a project-management tool built for
software engineering teams that prefer keyboard-first interfaces,
fast issue triage, and Git integration. Used by 10,000+ teams
including Cash App, Vercel, and OpenAI; consistently rated 4.7+
on G2 across 800+ reviews."

Score 0 (no) — Opens with a question paraphrasing the query
("What is X?"); brand storytelling preamble; vague positioning
("the future of marketing," "the leading platform"); buries the
answer below the fold. OR the first-75-words structure is
declarative but the substance is generic — a templated answer
with vertical-specific terms swapped in that wouldn't survive a
domain-expert read. OR the recommendation reads as a
keyword-density-targeted holdover from the deprecated 2018 SEO
playbook.

Score 0.5 (unknown) — Answer exists in the first 75 words but is
hedged or genre-mixed (part declarative, part interrogative) such
that extracted standalone it would read as partial — OR the
substance side is ambiguous from the artifact alone. Emit 0.5 +
"unknown" + one sentence on what would clarify.

Required reasoning (work through these 3 steps in your rationale):
1. Extract the first 75 words of meaningful body content from the
   page (skip nav, hero-image alt text, cookie banners).
2. Test whether those 75 words contain a complete declarative
   answer to "what is this and who is it for?" in
   retrieval-document register AND whether the substance survives
   the domain-expert read (does it name vertical-specific
   differentiators, or is it a templated answer with terms
   swapped?).
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: visual design; page length beyond first 75 words;
presence of imagery; schema.org markup specifics. Those live in
structural_gate or are out-of-scope for this criterion."""

_GEO_2 = """\
Evaluate this optimized page content on ONE outcome question:

Does the page-level recommendation inject verifiable evidence —
quantitative figures with sources, direct quotations from
credibly-named third parties, inline citations to first-party
data or external authority — at a density that would let an AI
engine validate the claims independently, AND would a
sophisticated human researcher trust those sources as off-domain
and reference-grade? Does the evidence type match the page's
vertical (statistics dominate Law & Government / Opinion;
quotation dominates People & Society / History; fluency-driven
authority dominates Health and Business)?

Score 1 (yes) — Page recommendation contains at least 3 specific
claims paired with verifiable evidence BOTH (a) extractable /
inline-citable in form (named numeric figure with year + source;
direct quote with named attribution + role + employer + date;
inline citation to a specific document) AND (b) off-domain /
first-party-data-anchored in substance (the source is named off
the brand's own domain — not sibling-page self-citation; OR is
genuinely first-party original research the brand owns and others
can cite back). Each claim is checkable AND a domain expert in
the vertical would accept the source as appropriate (statute /
case citation in legal; clinical-guideline citation in healthcare;
G2 / Gartner / TrustRadius in B2B SaaS; SEC / FINRA / FCA in
fintech; arxiv / analyst-Substack in AI-lab). The teach-by-
contrast test for "specific": "$249/month for 2,000 tracked
keywords" passes; "affordable plans for every budget" fails —
concrete numbers, named competitors, dated claims; every data
point traces to something the client can verify before publishing
(do not optimize toward the specific dollar figure; the test is
the specificity discipline, not the example value). Off-domain
attribution also includes competitor wins where the client
genuinely loses on a dimension — first-party content has a
natural credibility ceiling with AI engines, and acknowledging
where competitors win is credibility-ceiling defense, not omission.

Illustrative example — competitor-winning acknowledgment (do not
optimize toward this; the test is the acknowledgment-of-genuine-
loss discipline, not the specific competitor named): "Linear's
GitHub integration is more mature than ours — Linear-to-GitHub
bidirectional sync ships out-of-the-box with PR auto-linking and
branch-naming-from-issue (per Linear changelog, 2025-11-12
release), while ours requires a manual webhook setup. Teams that
ship daily PRs will get faster setup with Linear today. We win on
issue-tracking customizability — our custom-field-on-issue +
saved-view + per-team-workflow stack supports 14 distinct workflow
templates out-of-the-box (per our pricing page, last reviewed
2026-04-30) vs Linear's 3 templates; teams operating multiple
methodologies across a single PM substrate will get more mileage
from ours. As of May 2026, GitHub-integration parity is on our Q3
roadmap (per roadmap.our-product.com, last updated 2026-05-10)."
This passes BOTH the extractable-form side (named competitor +
named feature + dated source + dated counter-claim) AND the
human-trust-survivable substance side (the loss is named with
specific feature attribution, not "competitor is better in some
ways"; the counter-claim is named with specific count attribution,
not "we have more flexibility"; the temporal framing is absolute).
Vendor-vacuum pages (zero competitor acknowledgment) ship a
marketing-not-reference signal AI engines de-rank; pages that name
where competitors win read as reference and earn citation parity.

Score 0 (no) — Vague qualitative claims only ("leading," "trusted
by thousands," "industry-best"); numbers without attribution;
self-citation only — every linked source is a sibling page on
the same domain; quotes from un-named "industry experts." OR
citation count is high but all sources sibling-domain (passes
surface-count, fails human-trust). OR evidence type is wrong for
the vertical (e.g., a healthcare page that cites only B2B-SaaS-
style review aggregators; a legal page that cites only blog posts
and not statute / case law). OR the recommendation perpetuates a
deprecated tactic (self-citation farm; PBN-sourced references;
mass directory references) without acknowledging the modern-lever
shift required.

Score 0.5 (unknown) — Specific claims exist but attribution is
ambiguous (e.g., "internal study," "based on customer data") such
that an AI engine couldn't independently verify AND a human
couldn't defend the source to a peer. Emit 0.5 + "unknown" + one
sentence on what attribution would resolve.

Required reasoning (work through these 4 steps in your rationale):
1. List every specific claim in the page recommendation (numbers,
   named quotes, dated facts).
2. For each, identify the attribution / source / verifiability
   path; flag sibling-domain citations as failing the off-domain
   test.
3. Test whether the evidence type matches the page's vertical
   (statistics for Law / Opinion; quotation for People & Society /
   History; fluency-driven authority for Health / Business).
4. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of citations as a count (routes to
structural_gate); link-density; presence of footnotes; URL HEAD
resolution; quote-grep verification (routes to structural_gate).

Required for full score-1 on dual-audience AI-engine-citation
surfaces: at least one competitor-acknowledgment where the client
genuinely loses on a dimension — symmetric framing where
competitor strengths are stated in equal or stronger language than
the client's, not omitted. Pages that read as vendor-vacuum
marketing (zero competitor acknowledgment) score down on the
human-trust side of the AND-conjunction even if evidence density
is mechanically met."""

_GEO_3 = """\
Evaluate this optimized page content on ONE outcome question:

If each substantive 40-75-word block on the sample page is
extracted standalone, does it read as a complete claim with named
entities — no floating pronouns, no "as mentioned above," no
orphan context — AND does each standalone passage carry
substantive content (a domain expert reading the passage in
isolation would learn something), not mechanical entity-
repetition? Would an AI engine retrieving that single passage be
able to use it directly in a citation-worthy answer?

Score 1 (yes) — At least 3 substantive passages in the sample
page work standalone BOTH (a) mechanically (headings restate the
entity, pronouns resolve within the passage, lists work item-by-
item without depending on item 1 for context) AND (b)
substantively (a domain expert reading the extracted passage
learns a non-trivial claim, not a repeated definition with
entity-name reinforcement).

Illustrative example — AI-lab (do not optimize toward this, but
the pattern): "Claude 4.7 supports 200K input tokens and 64K
output tokens per request, with prompt caching reducing repeated-
context cost by 90% on subsequent calls within a 5-minute TTL.
Tool use latency averages 1.2s for single-tool calls and 3.4s for
multi-tool agentic loops per Anthropic's Q1 2026 latency benchmark
(anthropic.com/news/q1-2026-perf, published 2026-02-15)."

Score 0 (no) — Passages depend on prior context. "This makes it…"
"The above shows…" Pronouns floating across paragraphs. Headings
that don't name the entity. Lists where items 2-5 need item 1 for
context. OR passages are mechanically self-contained via entity-
repetition but substantively empty — "Freddy ships content for
regulated B2B" repeated three times passes mechanical
self-containment, fails the substance check. OR the recommendation
perpetuates the deprecated "exactly-40-word answer-bait passage"
Goodhart slot-fill.

Score 0.5 (unknown) — Some passages stand alone, others don't,
and the failed passages are ones an AI engine is likely to
extract. Emit 0.5 + "unknown" + one sentence on which passages
fail.

Required reasoning (work through these 4 steps in your rationale):
1. Extract 3 substantive 40-75-word passages from the sample page
   (one near the top, one mid-page, one near the bottom).
2. For each, test mechanical standalone-coherence (pronouns,
   headings, lists).
3. For each, test substantive content (does a domain expert
   reading in isolation learn a non-trivial claim, or is it
   entity-repetition padding?).
4. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of headings; presence of TOC; page structure
beyond passages; word-count band (routes to structural_gate)."""

_GEO_4 = """\
Evaluate this optimized page content on ONE outcome question:

Does the page-level recommendation present the brand / product /
service as a stable entity via canonical naming AND survive a
basic cross-source authority check — naming alternatives, citing
third-party comparisons or analyst coverage, quoting external
voices — such that an AI engine would confidently associate this
page with one canonical entity AND a sophisticated human
researcher would accept its claims as off-domain-validated, not
vendor-vacuum marketing? Does the author / founder bio
architecture (where applicable) reinforce the entity-stability +
E-E-A-T construction?

Score 1 (yes) — BOTH (a) brand name canonically consistent across
the sample page (no entity drift; schema.org `sameAs` to at least
one canonical KG anchor — Wikidata / Crunchbase / SEC EDGAR /
LinkedIn Company / Google Business Profile / registry .gov,
tiered for SMB coverage; category placement explicit — "an X for
Y who need Z") AND (b) at least 2 external validations that are
off-domain, named, dated, and vertical-appropriate (analyst report
for B2B SaaS; clinical guideline + clinician byline for
healthcare; statute + case citation for legal; SEC / FINRA / FCA
filing for fintech; arxiv / analyst-Substack for AI-lab; Reddit /
community-review for DTC; named partner / principal byline for
professional services). Third-party validation also includes
proprietary methodology, category-specific technical depth, or
unique knowledge the client can credibly provide — the citability
moat. Surfaces where the client's page becomes the only credible
primary source (a disclosed proprietary methodology, a uniquely-
deep technical explanation, a first-party feature explanation
rooted in implementation rather than marketing) count as valid
third-party-equivalent validation because no off-domain source can
reproduce them. The bio architecture (where present in the
fixture) reinforces this with per-author Person schema + sameAs
anchors + credentials + dated history.

Illustrative example — citability moat without vendor-vacuum
framing (do not optimize toward this; the test is the
proprietary-methodology + concrete-technical-depth discipline that
earns third-party-equivalent validation WITHOUT collapsing into
"we are leaders / trust us" self-puffery): "gofreddy operates a
149-lens content audit methodology assembled from CXL's ResearchXL
framework (Peep Laja, 2014; cxl.com/blog/researchxl) layered with
Phase-0 9-meta-frame architecture (proprietary, documented at
gofreddy.ai/methodology, last reviewed 2026-05-12) — each audit
produces per-lens scores across funnel-stage / message-clarity /
evidence-density / format-intent / freshness / engine-citability /
passage-self-containment / entity-stability / disambiguation
dimensions, generating a 200-400-row spreadsheet per audited page.
Sample audit output published at gofreddy.ai/case-studies/dwf-
2026-q1 (DWF LLP, Restructuring & Insolvency landing page, May
2026 with client permission). The methodology is reproducible by
any team with the lens specification (open-source at
github.com/gofreddy/content-audit-lens-149, MIT licensed since
2026-04); the differentiation is depth of application, not access
to the framework." This passes the citability-moat test without
falling into vendor-vacuum framing because: (a) the methodology is
named with provenance (CXL ResearchXL + Phase-0 9-meta-frames),
not "our proprietary system" without attribution; (b) the specific
scope is named (149 lenses, 9 dimensions, 200-400 rows per audit),
not "comprehensive analysis"; (c) the output is reproducible /
published with a real client artifact link, not "trust us, we've
audited many sites"; (d) the framework itself is open-sourced —
the moat is depth-of-application not access-control, which an AI
engine can validate and a domain expert can trust. Contrast with
vendor-vacuum failure: "We deliver world-class audits using our
proprietary methodology" scores 0 — no named framework, no
attribution chain, no reproducible scope, no published example, no
off-domain validation path.

Score 0 (no) — Entity drift (multiple name variants across page).
No category placement. Zero external sources. "Trusted by [logo
wall]" without per-logo attribution or context. Self-comparison
only (us-vs-old-us). All cited sources are sibling-domain.
Vendor-vacuum framing. OR canonical name is consistent but
external validation is weak in vertical-appropriateness (e.g., a
legal page cites only marketing-platform reviews, not statute /
case / Chambers / Legal 500). OR bio architecture absent or
templated without per-author credentialing.

Score 0.5 (unknown) — Entity is consistent but external validation
is weak (one source, or all sources are sibling-domain, or
vertical-mismatched). Emit 0.5 + "unknown" + one sentence on what
would strengthen.

Required reasoning (work through these 5 steps in your rationale):
1. Note the canonical entity name + category placement + canonical
   KG anchor (if present).
2. Identify external validation sources (must be off-domain,
   named, dated, vertical-appropriate); flag sibling-domain
   validations as failing.
3. Test whether the validation type matches the page's vertical
   (Chambers / Legal 500 for legal; clinical-guideline + clinician
   byline for healthcare; G2 / Gartner / TrustRadius for B2B
   SaaS; SEC / FINRA / FCA for fintech; arxiv / analyst-Substack
   for AI-lab; Reddit / Yelp / community-review for DTC; named
   partner / principal byline for professional services).
4. Cross-check against bio architecture (if present in fixture) —
   per-author credentialing + sameAs anchors.
5. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: logo wall presence; social proof aesthetics;
testimonial volume; entity-existence Wikidata lookup (routes to
structural_gate); schema.org `sameAs` validity (routes to
structural_gate)."""

_GEO_5 = """\
Evaluate this optimized page content on ONE outcome question:

Does the page-level recommendation's structure match the format AI
engines prefer for its declared query class (comparison → table;
how-to → ordered steps; what-is → definition + structured detail;
listicle → ranked items with methodology) — visible from URL
slug, page title, or H1 — AND does it carry the freshness signals
AI engines weight at the vertical-appropriate cadence (substantive
currency in body content, not just date-stamp gaming)?

Score 1 (yes) — BOTH (a) page format matches its declared query
class — a `/best-X-for-Y` listicle page is structured as a ranked
list with at least one comparison table and disclosed methodology;
a `/how-to-X` page is structured as ordered steps with
prerequisites + verification + troubleshooting blocks; a
`/what-is-X` definition page leads with a declarative entity
definition; the page directly answers the target queries declared
on the brief — informational queries get explanations, commercial
queries get comparisons, transactional queries get pricing and
next steps. Intent-mismatch test (do not optimize toward the
specific brand; the test is the intent-class discipline): a page
optimized for "how much does Ahrefs cost" must surface pricing in
the first substantive passage, not company history; a
transactional-intent page that answers with informational-intent
prose fails regardless of structural quality. AND (b) freshness
signal is substantive at the vertical-appropriate cadence:
DTC pricing / shopping → current-week date stamp, pricing in
initial server-rendered HTML; fintech rates → current-month stamp,
rate / fee / APY data dated within 30 days; B2B SaaS feature /
comparison → current-quarter stamp, feature claims dated within
90 days; healthcare evidence-based → last-medically-reviewed
within 24 months on stable conditions, 90 days on emerging
treatments + named-guideline citation with current version; legal
statute / case → last-reviewed within 12 months, statute-version-
bound, case citation with current Shepard / KeyCite-equivalent
reliability check; AI-lab API / SDK → per-release stamp, version-
pinned code examples, dated changelog; evergreen explainer →
visible publication or update date within last 12-18 months.

Illustrative example — concrete-count technical recommendation (do
not optimize toward this; the test is the specificity discipline
applied to body-content recommendations): "Audit found 21 of 22
hero-image and product-shot images on /pricing lack alt text;
adding alt text per WCAG 1.1.1 will both close the a11y gap AND
add 22 indexable entity-attribute strings the AI engine can use
in retrieval. Specific fix list with current alt-text and proposed
alt-text in §L appendix." This passes specificity — concrete
count (21 of 22), specific page (/pricing), named
recommendation-evidence pair. Contrast with "consider adding alt
text to images" which scores 0 — no count, no page, no evidence
chain.

Score 0 (no) — Format mismatch (a comparison page written as
flowing narrative; a how-to page without ordered steps; a listicle
without disclosed methodology). No visible date anywhere. Stats
without years. OR "Last updated YYYY-MM-DD" current-year stamp on
body content with no current-year references, named-current-
version-citation, or substantive freshness signal (the workflow
has gamed the stamp). OR freshness window is wrong for the
vertical (a DTC pricing page with a 12-month stamp; a fintech
rate page with a quarterly stamp). OR when the page recommendation
carries technical guidance (audit-derived findings, fix lists), it
is vague boilerplate rather than concrete counts and named
specifics — "21 of 22 images lack alt text" is actionable;
"consider adding alt text to images" is decoration. Boilerplate
technical recommendations that don't reference real problems found
on the actual page fail. OR the recommendation perpetuates a
deprecated format-intent mismatch (generic FAQ page;
featured-snippet position-0 targeting; AMP page).

Score 0.5 (unknown) — Format matches but freshness signal is
ambiguous (e.g., date present but more than the vertical-
appropriate window stale on a page making current-state claims;
OR cadence ambiguous from the artifact alone). Emit 0.5 +
"unknown" + one sentence on which dimension is weak.

Required reasoning (work through these 5 steps in your rationale):
1. Identify the page's declared query class (from URL / title /
   H1 cross-checked against any fixture brief geo_format hint).
2. Verify format matches that declared class (comparison → table;
   how-to → ordered steps; listicle → ranked items + methodology;
   definition → declarative lead + structured detail).
3. Identify freshness signals (publication date, last-updated,
   current-year refs, dated third-party citations) and test
   against the vertical-appropriate cadence.
4. Test whether freshness is substantive (body content matches
   stamp) or stamped-only (gaming). For body-content technical
   recommendations, test concrete-count specificity vs vague
   boilerplate.
5. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: page-load speed; image-alt-text completeness as a
count (routes to structural_gate); structured-data schema markup
specifics; mobile responsiveness; a11y."""

_GEO_6 = """\
Evaluate the set of optimized pages on ONE outcome question:

Across all pages in this session, does each page lead with a
genuinely different primary differentiator, distinct statistics
and data points, and FAQ questions that aren't trivially rephrased
across pages — such that the cohort reads as a coherent site
where each page contributes a different facet of the company's
value, not multiple pages competing for the same queries with the
same framing?

Score 1 (yes) — Each page in the cohort opens with a different
primary positioning claim; the statistics and benchmarks used as
key claims are distinct across pages (no single number anchors
two pages); FAQ questions across the cohort are genuinely distinct
(not "What is X?" / "What does X do?" / "Why use X?" — those are
trivially rephrased); the pages reinforce each other as a site —
each contributing a different facet of the company's value (one
covers comparison-page warfare, one covers how-to depth, one
covers founder credibility, one covers a vertical use case) —
rather than competing for the same query intent with overlapping
framing.

Illustrative example (do not optimize toward this exact shape):
the cohort might include /vs/competitor (comparison-page warfare,
opens with named-competitor head-to-head + decision-matrix),
/how-to-X (how-to depth, opens with prerequisite + ordered-step
lead + verification-test), /about/founder-bio (E-E-A-T
construction, opens with credentialed bio + provenance chain),
and /for/{vertical} (vertical use case, opens with
vertical-specific problem framing + clinical-guideline or
analyst-report anchor). Each page anchors on a distinct primary
differentiator (decision-matrix vs ordered-step depth vs
credentialed-bio vs vertical-anchor); each page's hero numbers
are different (comparison scorecard vs latency benchmark vs
years-of-experience vs clinical-trial count); FAQ questions on
each page address different decision moments (which-to-pick vs
how-to-implement vs who-is-this-person vs does-this-fit-my-
vertical).

Score 0 (no) — Two or more pages open with the same primary
positioning claim (same hero, same headline framing, same
differentiator). OR the same statistic / benchmark / number
anchors two or more pages as a key claim. OR FAQ questions
repeat or trivially rephrase across pages ("What is X?" on page 1,
"What does X do?" on page 2 — same question). OR the cohort
reads as multiple pages chasing the same query intent with
overlapping framing rather than as a site where pages reinforce
each other.

Score 0.5 (unknown) — Cohort has some diversity but at least one
page substantively overlaps another (shared primary
differentiator OR shared key statistic OR FAQ overlap that's not
trivially rephrased but is substantively similar). Emit 0.5 +
"unknown" + one sentence on which pages overlap and on what
dimension.

Required reasoning (work through these 3 steps in your rationale):
1. For each page in the cohort, identify the primary
   differentiator (opening claim / hero framing), the key
   statistics or benchmarks used as load-bearing numbers, and
   the FAQ questions.
2. Compare across pages — flag any primary-differentiator
   repetition, statistic / number reuse as key claim, FAQ
   question repetition or trivial rephrasing.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification
   referencing the specific cross-page overlap (or its absence).

Do not score: cross-page word-count balance, page-count, presence
of cross-links between pages, identical brand-name usage (the
brand should be consistent — that's GEO-4, not a diversity
problem)."""

_GEO_7 = """\
Evaluate this optimized page content on ONE outcome question:

If an AI engine were to retrieve a passage from the sample page
and synthesize an answer with one or two of the documented LLM
failure modes — similar-name conflation, source-anchor
hallucination, partial-attribute corruption, recency-cutoff
distortion, or competitor-favorable reframing — would the brand
still come out correctly identified, correctly attributed,
correctly time-framed, and not out-framed by a competitor? Does
the page's structure FORCE the engine toward correct synthesis
rather than relying on the engine to figure it out? Are the
top-3 strategic claims on the page each backed by named signals,
verifiable sources, and acknowledged alternative interpretations?

Score 1 (yes) — Page recommendation contains ALL of:
(a) Disambiguation against similar-name confusables — explicit
disambiguation block early when the entity has a most-confusable
similar-name target ("Anthropic, the AI safety lab founded 2021 —
not Anthropic Communications LLC"; "Cursor, the AI-native IDE —
not Cursor Inc. the eye-tracking device"). Singleton canonical
name across H1 + schema.org `@id` + OpenGraph + BLUF.
(b) KG anchor for inverted-citation-attack prophylaxis —
schema.org `sameAs` to at least one canonical KG entry (Wikidata >
Crunchbase > LinkedIn Company > Google Business Profile >
registry .gov, tiered for SMB).
(c) Top-3 claims with named signals + verifiable sources +
acknowledged alternatives — the headline, the dominant-positioning
claim, and the strongest differentiation claim each (i) name the
specific signals they rest on, (ii) cite verifiable off-domain
sources, AND (iii) acknowledge at least one alternative
interpretation the evidence does NOT rule out. Confidence is
calibrated to evidence depth.
(d) Absolute-date framing for all temporal claims so engines
reasoning about "recent" don't conflate with training-cutoff
"recent" — no "recently," "in recent months," "today's,"
"the latest" without absolute-date qualifier.
(e) Comparison-claim symmetry where competitors are named — every
competitor claim (numeric, dated, quoted) backed by off-domain
citation; no asymmetry where brand claims are supported and
competitor claims are unsupported (or vice versa); no fabricated-
competitor-claim injection.

Illustrative example (do not optimize toward this): "Klinika
Melitus (Warsaw aesthetic dermatology, founded 2008 by Dr. Maria
Noszczyk MD — not Klinika Mielitus the unrelated Krakow practice;
sameAs: crunchbase.com/organization/klinika-melitus) is one of
three Warsaw clinics offering Daxxify (per RealSelf's Warsaw
provider directory, 2026-05-01; DermaCenter West and Beauty
Klinik are the comparable alternatives, also listed). Per AAD
2025 Clinical Practice Guideline, Daxxify shows ~24-week duration
vs onabotulinumtoxinA's ~16 weeks at equivalent doses; tradeoff
(per Revance phase-3 NCT04823300): higher cost per treatment,
similar efficacy. As of May 2026, our Daxxify membership pricing
is $1,200 / treatment; DermaCenter West's published rate (per
their pricing page, last reviewed 2026-04-15) is $1,150.
Alternative reading: pricing differential reflects operator-
experience premium more than treatment cost; we cannot yet
distinguish from 1 month of data."

Score 0 (no) — Any of: similar-name conflation surface exposed
(no disambiguation block when one is needed); no KG anchor; top-3
claims confident-toned but evidence chain breaks under inspection
(unnamed signals, fabricated sources, single-source extrapolation,
no disconfirming alternative); relative-date framing on current-
state claims; competitor-comparison framing asymmetry; OR brief
contains entity confabulations (competitors that don't exist,
fabricated quotes), source confabulations (404 URLs, unverifiable
cited reports), or recency-cutoff distortions (months-old "recent"
announcements, training-cutoff landscape projected into present).

Score 0.5 (unknown) — Page is structurally clean but the
disambiguation / anchoring / claim-backing is too thin to evaluate
engine resilience from the page alone. Emit 0.5 + "unknown" + one
sentence on what's missing.

Required reasoning (work through these 6 steps in your rationale):
1. Identify entity disambiguations the page EXPLICITLY STATES
   (e.g., "this product is not to be confused with X" / "distinct
   from Y because Z" / "Anthropic the AI safety lab — not
   Anthropic Communications LLC the unrelated PR firm"). Score
   the disambiguation sub-requirement (a) ONLY against what the
   page explicitly disambiguates against. If the page does not
   explicitly disambiguate, the disambiguation sub-requirement
   does not apply and the judge emits 0.5 + "unknown" + "page
   does not name what it's disambiguating against" for that
   sub-requirement (the overall criterion score still rolls up
   from sub-requirements b/c/d/e and the other CoT steps). Do
   NOT imagine confusables the page could have addressed but
   didn't — that's judge-imagined and unfalsifiable from the
   artifact alone. The JUDGE scores disambiguation only when the
   page explicitly does the disambiguation work, not when the
   judge can imagine a confusable.
2. Identify the top 3 strategic claims on the page (headline +
   dominant-positioning + key differentiation); for each, walk
   the evidence chain — signals named, sources verifiable +
   off-domain, disconfirming alternative acknowledged.
3. For any competitor comparison, check claim-citation symmetry
   (no brand-supported-competitor-unsupported asymmetry); flag
   any fabricated-competitor-claim injection.
4. Check temporal framing — absolute-date for all current-state
   claims; flag relative-date drift.
5. Flag any entity confabulation (made-up entity, conflated
   similar-name), source confabulation (cited URL/paper/quote
   that doesn't exist), or recency distortion (months-old
   "recent" claim, post-cutoff event missed).
6. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: URL HEAD resolution; quote-grep cosine similarity;
schema.org JSON-LD validity; Wikidata-entity-existence lookup;
date-stamp presence (all route to structural_gate)."""

_GEO_8 = """\
Evaluate this optimized page content on ONE outcome question:

Do the technical recommendations on this page reference actual
problems found on this specific page — with concrete counts,
element locations, or URLs that tie each recommendation to
evidence in the audit — such that a developer could implement
each fix without additional investigation? Or are the
recommendations generic boilerplate that could apply to any
website?

Score 1 (yes) — Every technical recommendation names a specific
problem observed on THIS page with concrete counts, named
elements, or URLs that tie the recommendation to evidence in the
audit data. A developer could implement each fix without
additional investigation because the problem, location, and fix
are all specified. The concrete-count discipline applied: "21 of
22 hero-image and product-shot images on /pricing lack alt text"
passes; "consider adding alt text to images" fails. "H2 on line
47 of /vs/competitor reads 'Why us is better' (missing entity
name + comparative framing); rewrite as '[Brand] vs [Competitor]:
which fits which team shape'" passes; "improve H2 clarity" fails.
Specific-sounding recommendations that reference fabricated
problems (claims the page has X when it doesn't) also fail — the
recommendation must trace to real audit evidence.

Score 0 (no) — Recommendations are generic boilerplate that could
apply to any website. "Consider adding alt text to images" or
"Improve page speed" without referencing what is actually wrong
on this page. No specific elements, counts, or URLs are named.
OR recommendations name specific problems that don't actually
exist on this page (fabricated audit findings). OR the
recommendations are valid in form but the count / element /
URL is decorative — same recommendation would apply identically
to a different page in the same template family without changing
a single word.

Score 0.5 (unknown) — Some recommendations reference actual page
elements (such as a specific heading or section), but others are
generic advice not tied to observed problems. A developer could
act on some items but would need to investigate others. Emit 0.5
+ "unknown" + one sentence on which recommendations are concrete
vs which are boilerplate.

Required reasoning (work through these 3 steps in your rationale):
1. For each technical recommendation in the page-level work,
   identify whether it names a specific count, element location,
   or URL that ties to evidence on THIS page.
2. Cross-reference against any provided original page content to
   verify the named problem actually exists on this page (flag
   fabricated audit findings as score 0).
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification
   referencing the most-concrete and least-concrete recommendation
   in the cohort.

Do not score: a11y compliance level as a target metric; SEO
ranking projection; page-load-speed numeric target; structured-
data schema specifics (all route to structural_gate)."""


# ---------------------------------------------------------------------------
# Competitive Intelligence (6 rubrics — v3.3 outcome-question shape)
# ---------------------------------------------------------------------------
# v3.3 design lands the outcome-question + binary-anchor + 3-step-CoT shape
# from `docs/handoffs/2026-05-17-judge-design-step1-competitive.md`. Each
# criterion is scored 0 / 0.5 / 1 with a 0.5 "unknown" anchor that forces
# the judge to name the missing evidence. The 8-criteria 1/3/5 gradient
# shape (pre-v3.3) was retired because it was vulnerable to feature-check
# drift (Phase 4 pathology) and slot-fill mimicry.
#
# Scoring is binary at the criterion level; the scorer_binary.md prompt
# template (in `judges/evolution/prompts/`) maps the per-criterion 0/0.5/1
# values onto the 0-10 ``aggregate_score`` envelope the substrate already
# consumes (sum × 10 / 6), keeping the composite math unchanged.

_CI_1 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

After reading, would the reader commit to a single specific concrete
action — a competitive posture, budget reallocation, roadmap change,
outreach call, hiring move, or follow-up intel ask — on the most
consequential development surfaced by the brief? Could they walk into
their next leadership meeting and assign this action by the next
decision-shape-appropriate gate?

Score 1 (yes) — Brief makes the single most-consequential call so
concretely that disagreeing requires a counter-argument, not a shrug.
The recommended action names BOTH a specific action type AND a
specific target: posture toward a named competitor, budget shift in
a named category, roadmap change to a named initiative, outreach to
a named person, hiring move for a named role, or intel ask on a
named question. The reader could commit by the next
decision-shape-appropriate gate (next week for reactive, next
quarter-end for evaluate-class, next vendor-cycle for healthcare-style).

Illustrative example (do not optimize toward this exact shape):
"DermaCenter West opened a 2-injector medspa within 0.8 miles of
our location and is offering $30K-off membership pricing through
April; defend our top-decile Botox cohort by escalating the
loyalty-program-V2 launch from Q3 to next month and offering
matching $30K bundles to the 47 highest-LTV patients we'd most
lose. Costs: ~$94K margin against current Q1 spend; defer the
laser-skin-resurfacing investment by one quarter."

Capacity-sized recommendation note. A score-1 recommendation is
also sized to the client's actual capacity to act. "Deploy
llms.txt by Mar 26" is good. "Deploy llms.txt by Mar 26, your
dev can do this in a half-day" is better. Recommendations the
client can't execute — because the named timeline, headcount,
or budget envelope doesn't fit their actual operating reality
— are decoration, not action.

Prioritization discipline. When the brief surfaces multiple
findings, not everything is Priority 1. A score-1 brief makes
the hard call about which 2–3 actions drive disproportionate
impact and which findings are interesting but not urgent. The
single most-consequential call still anchors the brief;
secondary priorities, where present, are explicitly de-ranked
rather than presented as parallel.

Asymmetric-opportunity test. Where the brief identifies an
opportunity rather than a defensive move, the named target
reflects an asymmetry — not just a gap in the landscape, but
a gap this specific client is uniquely positioned to own (a
strength, channel, relationship, dataset, or capability the
competition can't or won't bring). Generic "no one is doing X"
gaps that any competent operator could fill are not asymmetric
and do not earn score 1 on their own.

Score 0 (no) — Brief gives a competitor activity update. No implied
next move. Or recommendation is one level too abstract ("strengthen
positioning," "explore the segment"). Or recommendation is
wrong-timeline-shape for the decision (recommends "by next week"
for an acquisition evaluation that has a 12-week horizon, or vice
versa). Or recommendation is not sized to the client's actual
capacity to act. Or everything is Priority 1 with no hard call
about which 2–3 actions drive disproportionate impact. Reader
finishes informed but uncommitted.

Score 0.5 (unknown) — Brief makes a concrete call but the reader
could not commit without one additional piece of information
explicitly named in the brief as missing. Emit 0.5 + "unknown" +
one sentence on what's missing.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the single most consequential development the brief
   surfaces.
2. Find the brief's recommended action on that development; verify
   it names BOTH a specific action type AND a specific target the
   reader could act on by the decision-shape-appropriate gate.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: word count, presence of framework headers,
executive-summary structure. Those live in structural_gate or do
not matter for this criterion."""

_CI_2 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

Does the analysis project where the competitive threat is heading
6–18 months out using more than one independent signal, or does it
describe where it is today? If the reader re-read this brief in 90
days, would they see most of its forward calls starting to
materialize?

Score 1 (yes) — At least one falsifiable claim about where the
competitor is heading, backed by 2–3 convergent INDEPENDENT signals
(M&A, hiring, product roadmap, earnings language, partnership
pattern, regulatory positioning, lateral hires, model-card
improvements, location density, vendor relationships). Reader could
check in 90 days whether the call held.

Illustrative example (do not optimize toward this exact shape):
"Stripe's last 3 product launches all target vertical-SaaS
platforms (Connect Embedded, Issuing-for-platforms,
Tax-as-a-service) + their Q3 earnings call emphasized 'embedded
fintech' 11 times + their reseller-network growth doubled YoY —
they're moving up-market into vertical-SaaS-platform PSP
positioning through 2026, away from the original developer-API
base."

Score 0 (no) — Descriptive snapshot only. Or forward call by linear
extrapolation from one signal ("they raised $40M, so they're going
up-market").

Score 0.5 (unknown) — Forward call exists but the supporting
signals are ambiguous or unverifiable from the brief alone. Emit
0.5 + "unknown" + one sentence on what would have to be in the
brief to commit to 1.

Required reasoning (work through these 3 steps in your rationale):
1. List every forward-looking claim in the brief.
2. For each, identify the supporting signals (must be 2+
   independent for score 1).
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of competitors covered, presence of trajectory
headers, exhaustiveness."""

_CI_3 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

When the brief attributes an advantage to a competitor, does it
identify the specific structural mechanism that advantage rests on
— and pass the test that a competitor can't or won't replicate it?
Could the reader explain to their CTO / managing partner / medical
director in one sentence why this threat is structurally durable,
or specifically why it isn't?

Score 1 (yes) — For at least one competitor advantage named, the
brief identifies the source of the advantage AND the structural
reason it's hard to copy. Or — equally valuable — explicitly
rejects an apparent advantage as replicable operational
effectiveness rather than sustainable positioning.

Illustrative example (do not optimize toward this exact shape):
"Anthropic's tool-use advantage looks like model architecture, but
it's actually a curated training-data moat from their
constitutional-AI work + a documented red-team-prompt corpus — not
replicable without 18+ months of safety-research investment we
won't make."

Illustrative rejection example (do not optimize toward this exact
shape): "The competing AI lab's apparent first-mover advantage on
agentic tool use is replicable operational effectiveness, not
sustainable positioning. OpenAI matched the capability in March;
Google followed in April. No curated training-data moat, no
proprietary RLHF corpus on tool use, no compute or distribution
lock-in we can't reach. Treat as a non-durable lead, not a
defensible moat; reallocate the planned counter-positioning spend
to a surface where the structural-mechanism case is still open."

Score 0 (no) — Asserts an advantage ("they have scale," "their
brand is strong") without the structural reason it's hard to copy.
Or the named mechanism doesn't fit what the brief describes.

Score 0.5 (unknown) — Mechanism named but evidence in the brief is
insufficient to confirm whether the advantage is sustainable or
replicable. Emit 0.5 + "unknown" + one sentence on what would
resolve it.

Required reasoning (work through these 3 steps in your rationale):
1. List every advantage attributed to a competitor.
2. For each, identify the brief's claim about the underlying
   mechanism + whether it passes the "can't or won't replicate"
   test.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of frameworks invoked, presence of "Mechanism
of Advantage" section header."""

_CI_4 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

Does the brief surface at least one finding the reader's
organization probably doesn't want to hear — and stand by it with
enough evidence to defend in a leadership meeting? If the reader
read this aloud at their next leadership offsite, would at least
one person be visibly uncomfortable?

Score 1 (yes) — At least one finding pushes against a prior the
brief EXPLICITLY NAMES as belonging to the reader's organization —
e.g., "leadership currently believes X," "our prior assumption was
Y," "we have been hedging on Z," "the company narrative is W." The
finding contradicts that explicitly-stated prior with supporting
evidence. The prior cannot be imagined or inferred by the judge —
it must be on the page. The finding earns its weight with evidence,
not provocation.

Illustrative example (do not optimize toward this exact shape):
"Our 'enterprise readiness' is the prior most likely to be wrong.
The Pinsent move signals the senior-RES tier — our claimed
strength — is the actual lateral-flight risk, not the junior tier
we've been hedging on." (The brief names "enterprise readiness" as
the prior AND "the junior tier we've been hedging on" as the
related assumption being contradicted; the prior is on the page.)

Score 0 (no) — All findings confirm the reader's existing
narrative. No disconfirming evidence engaged. OR the brief makes no
finding that contradicts the company's evident strategic posture
(i.e., it is not surfacing an uncomfortable truth at all) — CI-4
does not apply and scores 0, not 0.5. The 0-vs-0.5 distinction
matters: a brief that simply isn't doing the uncomfortable-truth
work scores 0 (criterion not satisfied), preserving the criterion's
discriminative range; the 0.5 anchor is reserved for the case where
the brief IS doing the work but with the prior implicit rather than
named.

Score 0.5 (unknown) — The brief surfaces a finding that contradicts
an inferable prior of the reader's organization, but does not quote
or paraphrase the prior explicitly — so the uncomfortable-truth
work is happening on the page but the prior is implicit rather than
named. Emit 0.5 + "unknown" + one sentence on what prior the brief
appears to be contradicting AND what evidence in the finding is too
thin to defend in a leadership meeting.

Required reasoning (work through these 3 steps in your rationale):
1. Identify priors the brief EXPLICITLY STATES it is challenging
   (e.g., "leadership currently believes X" / "our prior assumption
   was Y" / "we have been hedging on Z" / "the company narrative is
   W"). If the brief does not name a prior AND makes no finding
   that contradicts the company's evident strategic posture (no
   uncomfortable-truth work is being attempted), score 0 (criterion
   does not apply — not 0.5). If the brief surfaces a finding
   contradicting an inferable prior but does not quote or
   paraphrase the prior explicitly, emit 0.5 + "unknown" + one
   sentence on the implicit prior + what evidence is thin. Do not
   impute priors the brief leaves implicit at score 1; score 1
   requires the prior on the page.
2. For each brief-stated prior identified in Step 1, find the
   finding in the brief that contradicts it. Verify the finding
   carries supporting evidence (named signal, dated event, cited
   source) sufficient to defend in a leadership meeting.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification. The
   justification must quote or paraphrase the brief's own statement
   of the prior; if no quoted/paraphrased prior is available, the
   score is not 1.

Do not score: confrontational tone, presence of "uncomfortable
truths" section header, number of priors challenged. Do not impute
priors the brief does not state."""

_CI_5 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

Does the recommended action name what the company gives up by
committing — the budget, scope, market, capability, or initiative
that has to be sacrificed? Real strategy always costs something; a
recommendation that's free is a wish.

Score 1 (yes) — 1–3 specific recommendations, each pairing the bet
with the explicit thing being sacrificed. The reader could explain
to their CFO / partnership / medical director what budget line
moves, what initiative pauses, what segment de-prioritizes. The
cost is specific enough to be uncomfortable.

Illustrative example (do not optimize toward this exact shape):
"Defend our 50-employee SMB tier from BambooHR's compliance-bundle
expansion by accelerating SOC2-prep-as-a-service launch from Q4 to
next month. Cost: 4 engineering weeks pulled from custom-roles
work, which means deferring that feature by one quarter."

Score 0 (no) — Recommendation is a wish ("improve," "double down
on," "explore"). Or pairs gains with no costs. Or 5+
recommendations of equal weight with no acknowledged trade-off.

Score 0.5 (unknown) — Trade-off named but quantification absent,
leaving the CFO unable to evaluate the cost. Emit 0.5 + "unknown"
+ one sentence on what would need quantifying.

Required reasoning (work through these 3 steps in your rationale):
1. List every recommendation in the brief.
2. For each, identify the explicit cost / sacrifice named.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification (must
   reference the largest-stakes recommendation).

Do not score: number of recommendations, presence of "Trade-offs"
section header, quantification precision (a CFO-recognizable cost
is enough, exact ROI is not required)."""

_CI_6 = """\
Evaluate this competitive intelligence brief on ONE outcome question:

For each major strategic claim in the brief, does the evidence
chain survive tracing — i.e., are the underlying signals named,
the cited sources verifiable, and disconfirming alternatives
engaged? Or does the brief collapse into plausible-tone synthesis
where confident-sounding strategic claims rest on no traceable
chain?

Score 1 (yes) — At least the top-3 strategic claims in the brief
(the headline, the dominant-threat trajectory call, the
structural-mechanism diagnosis) each (a) name the specific signals
they rest on, (b) cite verifiable sources (named entity / dated
event / specific document / quoted attribution), AND (c)
acknowledge at least one alternative interpretation the evidence
does NOT rule out. Confidence is calibrated to evidence depth —
strong claims have multi-source backing; tentative claims are
flagged as tentative. When data sources failed or returned partial
coverage, the brief recalibrates rather than speculates: it names
what is missing, what analysis became impossible, and how the
remaining data changes what can be concluded — the gap itself is
treated as an intelligence finding, not silently omitted or
papered over with inferred data presented at unearned confidence.

Illustrative example (do not optimize toward this exact shape):
"Pinsent's senior-RES expansion (per their Sept 23
partner-promotion announcement + Chambers Tier-2 → Tier-1 RES
shift in 2026 + 3 lateral RES partner moves in Q3 per ALM lateral
tracker) suggests they're rebuilding RES practice depth.
Alternative reading: this is a 1-year build, not a 3-year
strategic shift — we can't yet distinguish from one round of
opportunistic hiring. Confidence: medium, will firm up if Q1 2027
promotions also skew RES."

Score 0 (no) — Claims are confident-toned but evidence chain
breaks under inspection: unnamed signals, fabricated sources,
single-source extrapolation presented as multi-signal, no
disconfirming alternative engaged. OR brief contains entity
confabulations (competitors that don't exist, fabricated quotes,
conflated similarly-named entities), source confabulations (404
URLs, unverifiable cited reports), or recency-cutoff distortions
(months-old "recent" announcements, training-cutoff landscape
projected into present).

Score 0.5 (unknown) — Evidence chain partially traces, but one of
the top-3 claims has insufficient supporting detail in the brief
itself to evaluate verifiability. Emit 0.5 + "unknown" + one
sentence on which claim's evidence chain is unclear.

Required reasoning (work through these 4 steps in your rationale):
1. Identify the top 3 strategic claims in the brief (headline +
   dominant-threat trajectory + structural-mechanism diagnosis).
2. For each, walk the evidence chain: are signals named? Are
   sources verifiable (named-entity / dated-event /
   specific-document / quoted-attribution)? Is at least one
   disconfirming alternative acknowledged?
3. Flag any INTERNALLY-INCONSISTENT claims within the brief
   itself: date contradictions (one section says "last quarter,"
   another says "3 months ago" for the same event); named-entity
   mismatches within the brief (one section says "Pinsent Masons,"
   another says "Pinsents"; one section says "Anthropic," another
   says "Anthropic Communications" for the same referent);
   self-contradicting trajectory claims (one section says "moving
   up-market," another says "doubling down on the developer-API
   base" without reconciliation). Entity/source/recency
   confabulation against external reality (does the cited URL
   resolve? does the named competitor exist? is the dated event
   within 90 days?) is verified by `structural_gate` (§8
   anti-hallucination checks), NOT this criterion — the judge
   does not have source-corpus access and cannot perform those
   checks reliably.
4. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: citation count or footnote density (those route to
structural_gate at Component A AND Component F), presence of
"Sources" or "Evidence" section header, comprehensiveness of
citation lists."""


# ---------------------------------------------------------------------------
# Monitoring Digest (6 rubrics — v3 binary 0/0.5/1 + outcome-question shape)
#
# v3 propagation per docs/handoffs/2026-05-18-judge-design-step1-monitoring.md.
# MON-1..MON-6 prose carries v1.1 surgical restorations and v3 documented
# exceptions (MON-5 ABSENCE + MON-6 COMPOUND breach the ≤5 ceiling — load-bearing
# AI-failure-surface defenses, NOT over-engineering). v0 MON-7 watchlist-arc
# folded into MON-6 score-1 anchor; v0 MON-8 editorial-restraint folded into
# the §5 wrapper (not a standalone criterion).
# ---------------------------------------------------------------------------

_MON_1 = """\
Evaluate this monitoring digest on ONE outcome question:

Does the digest express period-over-period developments as deltas
from a defined baseline (prior week, 4-week trailing average, peer
set, expected-given-event, regulator-clock-anchored expectation),
not as absolute counts? If the reader stopped reading after the
first 200 words, would they know what *changed* versus what's just
current state?

Score 1 (yes) — Every quantitative claim is framed as a delta with
an explicit comparator. Volume reported as "X vs Y-week average."
Sentiment reported as "X% vs baseline Y%." Material events
benchmarked against historical precedent or regulator-clock
expectation. The baseline source is named, not implied.

Illustrative example (do not optimize toward this exact shape):
"Brand mention volume 47% above 4-week baseline driven entirely by
the Pinsent partner-pull aftermath; brand sentiment 12pt softer
(62%→50%) — concentrated on legacy-firm-loyalty narrative, not on
Pinsent's positioning. Comparable: when CMS pulled 6 partners from
Dentons in 2024, sentiment softened 8pt over 3 weeks."

Score 0 (no) — Numbers reported as absolute values with no
comparator. "230 mentions this week." "Sentiment was 62% positive."
Or comparator is named but vibe-anchored not corpus-anchored
("higher than usual" without specifying usual).

Score 0.5 (unknown) — Some metrics are baseline-framed, others are
not, and the un-framed metrics include one that's load-bearing for
the period's lede. Emit 0.5 + "unknown" + one sentence on which
framing is missing.

Required reasoning (work through these 3 steps in your rationale):
1. List every quantitative claim in the first 400 words.
2. For each, identify whether a baseline / comparator / delta is
   named with its source.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification,
   referencing the load-bearing metric.

Do not score: precision of the baseline math, choice of baseline
window (vendor-default OK if named), formatting of the comparator,
baseline-source verifiability (routed to `structural_gate`)."""

_MON_2 = """\
Evaluate this monitoring digest on ONE outcome question:

Is each surfaced development explicitly classified by severity
(crisis / opportunity / watch / noise — or equivalent) with
reasoning the reader can interrogate, anchored on at least one
orthogonal axis pair? Would the reader's CEO / managing partner /
Chief Compliance Officer, challenging the classification, find the
underlying logic defensible — not vibes, not sycophantic confidence?

Score 1 (yes) — Top 3–5 items each carry an explicit severity
classification with reasoning that names at least one orthogonal
dimension pair (harm potential AND emotional charge; competence
exposure AND ethics exposure; materiality AND velocity; hazard AND
outrage). Coverage gaps modify classification (a "crisis" call on
single-source data is flagged as provisional). When classification
is a judgment call, the digest names the alternative reading the
reader could hold and why the call lands where it does. For
event-driven readers, materiality thresholds (SEC SAB 99-style
"would a reasonable investor consider this important") inform the
call.

Illustrative example (do not optimize toward this exact shape):
"Pinsent partner-pull — CRISIS (high harm to senior RES retention;
moderate emotionality; alt-hypothesis 'isolated incident, no
retention contagion' contradicted by 4-firm Q3 lateral-flight
pattern; tier elevated despite below-average mention volume because
lateral signal is the leading indicator). Provisional pending
Friday's confirmed-versus-rumored Above the Law count."

Score 0 (no) — Every item presented at the same emphasis.
"Concerning" used as a tier with no anchor. Classification implied
by ordering but not stated. Single-axis sentiment driving severity
(high outrage = high crisis, regardless of hazard). Confident-tone
orthogonal-axis prose generated to defend a foregone classification
(sycophancy tell). Severity reasoning padded with vague forward
projections ("this could escalate," "expect continued volatility")
in lieu of falsifiable conditionals — decorative forward projection
is not severity reasoning.

Score 0.5 (unknown) — Classification given but the reasoning
collapses to a single axis when an orthogonal axis is load-bearing.
Emit 0.5 + "unknown" + one sentence on what dimension is missing.

Required reasoning (work through these 3 steps in your rationale):
1. List the top 3–5 items in the digest.
2. For each, identify the severity classification + the
   orthogonal-dimension reasoning + whether the reasoning is
   anchored on observable signal vs. confident-tone defense.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of severity tiers used, vocabulary choice,
presence of color-coding, tier-distribution floor (routed to
`structural_gate`)."""

_MON_3 = """\
Evaluate this monitoring digest on ONE outcome question:

Does the development with the largest expected impact on the
reader's strategic interests open the digest, with structural
emphasis (length, headline weight, position) proportional to stakes
— not to volume, novelty, or sentiment extremity? If the reader
stops after position one, do they have the most-consequential
information? If nothing extraordinary happened, does the digest say
so plainly in position one?

Score 1 (yes) — The first substantive item in the digest is the
highest-stakes development of the period, with the largest word
allocation. Routine high-volume chatter is deprioritized or
omitted. Lede selection demonstrates Sandman-style discrimination
(low-hazard-high-outrage vs high-hazard-low-outrage; the latter
wins position one when both are present). For event-driven readers,
materiality drives lede placement. For low-volume periods, position
one explicitly states "nothing extraordinary happened — here's what
we tracked and why none of it warrants leadership escalation."

Score 0 (no) — Position one driven by volume or sentiment
extremity rather than stakes. Highest-stakes development buried at
item 4+ because something else was louder. Visual emphasis
(callout, bold) given to most-surprising rather than
most-consequential. Pager-style "URGENT" framing on a routine item
to satisfy the lede requirement cosmetically.

Score 0.5 (unknown) — Position one is reasonable but a second
item later in the digest has comparable or higher stakes and was
poorly placed. Emit 0.5 + "unknown" + one sentence on the
misplaced item.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the highest-stakes development of the period (largest
   expected impact on reader's strategic interests, by materiality
   / hazard / customer-revenue-exposure / regulator-clock-proximity).
2. Check whether it opens the digest with proportional weight, OR
   whether the digest correctly reports a low-volume period with
   explicit reasoning.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: section-ordering conventions, presence of
executive-summary block, hierarchical headings, word count of lede
(routed to `structural_gate`)."""

_MON_4 = """\
Evaluate this monitoring digest on ONE outcome question:

Does the digest end with 1–3 action items each naming a specific
owner (named person or role, not "the team"), a specific deadline
(date or window appropriate to the decision_shape), and the
consequence of inaction (what gets worse)? Could the reader walk
into the leadership-cadence-appropriate context and assign these
without further interpretation?

Score 1 (yes) — 1–3 specific action items. Each names owner +
deadline + consequence. The owner is concrete (CEO, Head of Comms,
Head of Legal, Chief Compliance Officer, IR lead, founder
themselves, named agency contact, regulator-relations lead — not
"the team"). The deadline is specific and decision-shape-appropriate
(this week / by Friday / same-day for event-driven /
sub-1hr-escalation-trigger for incident-driven — not "ongoing").
The consequence is operationalized ("widens SoV gap to 2-week-low,"
"loses defensibility on partner-RES narrative," "creates
Reg-FD-disclosure exposure if internal action precedes external
statement" — not "could affect reputation").

Illustrative example A (do not optimize toward this exact shape)
[standard cadence]: "Head of Comms drafts named-partner-context
briefing by Wednesday 3pm; offer to Bloomberg reporter before
Friday's analyst-call coverage cycle locks in. Otherwise,
legacy-firm-loyalty narrative hardens for Q3 trade press."

Illustrative example B (do not optimize toward this exact shape)
[event-driven]: "CFO + IR Head review the Hindenburg short report
this morning; commit to Reg-FD-compliant response posture (engage
/ decline / delay) by 2pm market close. Otherwise, the silence
increases probability of an analyst-downgrade in Friday's note
cycle."

Illustrative example C (do not optimize toward this exact shape)
[founder-led]: "Founder DMs the Latent Space podcast host within
24 hours to engage on the developer-tools comparison; otherwise,
the framing locks in for next week's episode, which is the
highest-distribution channel in our category right now."

Score 0 (no) — Recommendations are "continue to monitor," "the
team should consider," "we should think about" — observations, not
action items. No deadline. Consequence reduced to "reputational
damage" or absent. Owner is "the team" / "leadership" / unnamed.

Score 0.5 (unknown) — Action items present but one or more of
owner/deadline/consequence is too vague to act on. Emit 0.5 +
"unknown" + one sentence on which dimension is missing.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the action items at the end of the digest.
2. For each, verify owner is concrete + deadline is
   decision-shape-appropriate + consequence is operationalized.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of action items beyond the 1–3 range,
formatting (bullets vs prose), use of imperatives."""

_MON_5 = """\
Evaluate this monitoring digest on ONE outcome question:

Did the digest flag at least one specific expected signal that did
not materialize this period — naming the missing signal, the
baseline expectation with source (prior-period digest, public
calendar, industry cadence, named precedent), and the strategic
implication? Or, when no flagged absence exists, did the digest
correctly report "all expected signals materialized — no anomalous
silences this period" with reasoning?

Score 1 (yes) — At least one named missing signal + named baseline
expectation with corpus source + named strategic implication. OR
digest correctly reports "no flagged absences — all expected
signals materialized" with reasoning. The baseline is
corpus-anchored (prior-period digest, public earnings calendar,
FDA Warning Letter cadence, NRC event-reporting window, named
historical pattern), not vibe-anchored.

Illustrative example A (do not optimize toward this exact shape)
[standard cadence]: "Expected tier-1 trade-press coverage of
competitor's Q3 launch did not materialize. Baseline: their Q1/Q2
launches each generated 8+ tier-1 mentions within 5 business days
per the analyst-tracker corpus; this week's count is 1.
Implication: under-resourced GTM, internal disagreement, or
strategic abstention — each changes our flanking-vs-defending
posture."

Illustrative example B (do not optimize toward this exact shape)
[event-driven]: "Competitor CFO absent from Tuesday earnings call.
Baseline: she has attended every quarterly call since 2024 per
public transcripts; no pre-announced absence in the Q3 IR calendar.
Implication: health, legal exposure, internal power shift, or
impending departure — track if she's absent from the next off-cycle
update."

The named-absence shape: the campaign that generated no coverage;
the competitor that went quiet; the regulator who didn't respond
on the expected window. Silence is often the most important data
point — but only when the baseline expectation is corpus-anchored
and the strategic implication is named.

Score 0 (no) — Generic "we'll keep watching"; OR specific absence
without corpus-anchored baseline (apophenia risk); OR fabricated
absence ("competitor did not announce a Mars program") with no
baseline; OR digest claims comprehensive silence-coverage in a
high-volume period without identifying any anomalous-silence
candidate.

Score 0.5 (unknown) — Absence flagged but the baseline expectation
is implicit or the strategic implication too generic. Emit 0.5 +
"unknown" + one sentence on what's missing.

Required reasoning (work through these 4 steps in your rationale):
1. List flagged absences.
2. For each, verify (a) named missing signal, (b) corpus-anchored
   baseline expectation, (c) named strategic implication.
3. For each, verify the absence is NOT a required-silence phase
   (FDA pre-approval / SEC quiet period / NRC classified
   investigation / Joint Commission sentinel-event confidential
   phase / DoD classified). Required silence is not a missed signal;
   recommending response during required-silence is a rule-violation.
4. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of absences beyond 1+ (weak absences are
penalty), framework-name in baseline prose, citation-format of
baseline source (verifiability routed to `structural_gate`).

Note on the ≤5 ceiling: MON-5 is the first of two documented
exceptions to the design-guide ≤5 criteria ceiling, justified by
the apophenia / absence-fabrication AI-failure surface (BrokenMath
arxiv 2510.04721 measured rate; Conrad/Shermer patternicity
literature; Tetlock superforecaster calibration). MON-1..MON-4 +
MON-6 cannot catch fabricated absences — they test present-signal
interpretation, not missing-signal reasoning. Predicted: MON-5 most
likely to absorb into MON-1 (both require named-baseline reasoning)
once the redundancy check fires."""

_MON_6 = """\
Evaluate this monitoring digest on ONE outcome question:

For each cross-story compound and multi-week pattern in the digest,
does the evidence chain survive tracing — components named with
dated signals across **distinct time-points**, connective tissue
source-grounded (not generated), and at least one disconfirming
reading engaged? Would the reader walk into the leadership briefing
with a multi-week narrative their team probably didn't connect
themselves, anchored in 3+ named signals across distinct time-points
converging on a single underlying claim?

Score 1 (yes) — At least one cross-story compound anchored in 3+
signals across **distinct time-points** (e.g., week-1 signal A,
week-2 signal B, week-4 signal C — not one week's signal restated
three ways), converging on a single underlying claim, with at least
one disconfirming reading explicitly engaged at weight comparable
to the favored reading. Connective tissue ("led to," "in response
to," "driven by") is source-grounded — components share a named
entity or cited source. Confidence calibrated to evidence depth.
When prior-period digests are in scope, the compound connects to
the arc of prior digests — last period's watchlist items are
tracked as escalated, stayed flat, or resolved; previously-
recommended actions are followed up on (was it taken, was it
effective, or was it silently dropped). OR digest correctly reports
"no compound thread this period — all developments stand alone"
with reasoning.

Illustrative example (do not optimize toward this exact shape):
"Pinsent's senior-RES expansion (Sept 23 partner-promotion
announcement) + Slaughter & May's October FS-regulatory lateral
cluster (4 partners Q3 per ALM tracker) + the Sept 30 CMS comment
letter on FS-regulatory disclosure form a compound: top-tier London
firms are rebuilding FS-regulatory depth ahead of MiFID III
enforcement. Three signals dated to distinct weeks across three
named source-corpora. Alternative: opportunistic hiring tied to a
single bonus-cycle window, not strategic shift — can't yet
distinguish from one quarter of lateral data. Confidence: medium;
firms up if Q1 2027 promotions also skew FS-regulatory."

Score 0 (no) — Compound rests on signals from a single week
restated three ways. OR distinct-time signals but no single
underlying claim (decorative not analytic). OR connective tissue is
generated, not source-grounded (no shared entity / no causal
mechanism). OR strawman alternative-reading (visibly weaker than
favored). OR digest contains compound-claim fabrications (real
events stitched with invented connective tissue), entity/source
confabulations, or recency distortions.

Score 0.5 (unknown) — Compound partially traces but one required
component (distinct time-points / single claim / engaged
disconfirming reading / source-grounded connective tissue) is too
thin to evaluate. Emit 0.5 + "unknown" + one sentence on which is
unclear.

Required reasoning (work through these 4 steps in your rationale):
1. Identify cross-story compounds and multi-week patterns.
2. For each, walk the evidence chain — 3+ signals across distinct
   time-points? Single underlying claim? Source-grounded connective
   tissue (shared entity / shared source / named causal mechanism)?
   Disconfirming reading engaged at weight comparable to favored?
3. Flag any event confabulation, recency distortion, or
   compound-claim fabrication — force score 0 if `structural_gate`
   has not already gated them.
4. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of compounds beyond 1+, citation density
(routed to `structural_gate`), section-header presence.

Note on the ≤5 ceiling: MON-6 is the second documented exception,
justified by the compound-claim fabrication AI-failure surface
(FactSet 2025 59% forecast-error inflation on AI-assisted equity
reports; TrustJudge arxiv 2509.21117; Structural Hallucination
arxiv 2603.01341). MON-1..MON-5 cannot catch this — MON-5 rewards
absence-as-signal; without MON-6, cross-period
compound-fabrication surface is unprotected. Predicted: MON-5 ↔
MON-6 stay separate (absence and compound are structurally
distinct)."""


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
# X Engine — 7 rubrics (X-1..X-5 outcome-question binary; X-6 cross-item;
# X-9 algorithmic-citizenship checklist)
# ---------------------------------------------------------------------------
# v3.1 design lands the outcome-question + binary-anchor + structured-CoT
# shape from `docs/handoffs/2026-05-18-judge-design-step1-x-engine.md`. X-1
# through X-5 score Component A only (single X post ≤280 chars or 3-12-unit
# thread); Components B-L of the bundle are validated by structural_gate.
# Each criterion is scored 0 / 0.5 / 1 with a 0.5 "unknown" anchor that
# forces the judge to name the missing context. The 1/3/5 gradient shape
# (pre-v3.1) was retired because it was vulnerable to feature-check drift
# (Phase 4 pathology) and slot-fill mimicry.
#
# v1 surgical restorations preserved: X-2 voice.md HARD FLOOR (substrate
# provenance gate via load_source_data parents[2]); X-5 jargon-gloss rule
# (accessibility floor: non-engineer founder/marketer reader anchor).
# v3 surgical edit: X-2 cold-start PRE-REQ gate — if voice.md absent,
# X-2 abstains at 0.5 ("voice substrate not provisioned") rather than
# defaulting to HARD FLOOR; closes the cold-start chicken-and-egg.
#
# X-6 (cross-cohort diversity) and X-9 (algorithmic-citizenship URL
# avoidance) preserved verbatim from prior live code.

_X_1 = """\
Evaluate this draft on ONE outcome question:

Would a relevant X power-user — scrolling For-You at 0.5s/post,
first-fixation commitment in 400-700ms — stop on this post and tap
to expand, reply, repost, bookmark, or pause for dwell? And does
the body deliver the specific gap the opening promised, rather
than over-promising and producing the bounce-after-hook cliff?

Score 1 (yes) — The opening (first 1-2 sentences for a single
post; opening tweet for a thread) opens a specific, bounded,
finitely-closeable information gap the reader's brain commits to
closing. It anchors first-fixation via at least one named entity,
specific number, concrete noun, or schema-violating juxtaposition
— and does NOT instantiate the topic-statement anti-pattern
("Today I want to talk about X") or the throat-clearing anti-pattern
("I've been thinking lately about Y"). The body delivers the gap:
for single post, gap closes within the post; for thread, opening
promises a trajectory and each subsequent unit instantiates one
beat.

Illustrative example (do not optimize toward this exact shape):
"Seek wealth, not money or status." Six words; three named
referents; forward-vector is the bounded question "what's the
difference?" Body delivers by re-defining wealth as "assets that
earn while you sleep" — gap closes specifically.

Score 0 (no) — Opening instantiates topic-statement, throat-clearing,
vague-promise ("Here's something that changed my life"), or cliché
closed-loop ("Most people don't realize how important consistency
is"). OR opening anchors first-fixation correctly but body fails
to deliver the promised gap: hollow superlative (ordinary advice
underneath), fake-revelation tease (contrarian framing was a
vehicle for conventional content), numbered-list inflation (items
4-7 are restatements), cliffhanger-that-doesn't-pay, vulnerability
bait. Bounce-after-hook gap fires.

Score 0.5 (unknown) — Opening framing depends on context not in
the artifact (reply to unseen post, quote-tweet of unseen context).
Emit 0.5 + "unknown" + one sentence on what context would resolve
it.

Required reasoning (work through these 3 axes in your rationale):
1. Axis B (first-fixation-survivable opening): Identify the opening
   (first ~7 words ±2 for single post; opening tweet for thread).
   Tag tokens as first-fixation-survivable (named entity, specific
   number, concrete noun, mid-narrative action verb, schema-violating
   juxtaposition) or abstract (motivational noun, hedge,
   topic-statement framing, throat-clearing). Flag topic-statement
   and throat-clearing anti-patterns.
2. Axis A (forward-vector presence): Determine whether sentence two
   / tweet two is (a) predictable from the opening (cliché — fail),
   (b) unconstrained (vague promise — fail), or (c)
   bounded-but-unresolved (working hook — pass). Gap must be
   specific, bounded, finitely closeable (~3-15 words of resolution).
3. Axis C (hook-body alignment): Identify what specific gap the
   opening promised. For single post, does the body close that
   specific gap? For thread, do subsequent units instantiate the
   promised trajectory? Flag clickbait: hollow superlative, fake
   revelation, numbered-list inflation, cliffhanger that doesn't
   pay, vulnerability bait. Emit verdict + one-sentence justification.
   Score 1 only if all three axes pass.

Do not score: hashtag count, emoji, formatting, exact character
count (those live in structural_gate). Do not score literal
first-7-words as a threshold — it is a working approximation the
CoT applies as private reasoning."""

_X_2 = """\
Evaluate this draft on ONE outcome question:

Would a relevant practitioner reading this post recognize it as
written by someone with lived experience — not summarized from
secondary sources, not regenerable from public-internet
summarization?

Score 1 (yes) — Contains at least one specific detail (named
person, dated event, specific number with provenance, unique
anecdote, named project, specific failure with named context,
dollar amount with attribution) demonstrating the author was
present for the underlying experience. Claim cannot be regenerated
by an LLM reading the public internet — required first-hand
exposure.

Illustrative example (do not optimize toward this exact shape):
"When I rolled out our SOC2 prep flow last quarter, 7 of the 12
customers said 'finally — the BambooHR compliance bundle requires
us to do this manually'." Named entity + specific number +
first-person observation.

Score 0 (no) — Every claim could appear in any productivity-niche
post. No named entities the author was present for; no dated
specifics; no first-person details. Generic platitude framed as
wisdom. OR specific-looking details that are confabulated:
fabricated quotes, made-up "Stanford 2023 study," conflated
entities, dated events that don't exist (documented LLM failure
mode). **HARD FLOOR (substrate-provenance gate):** any first-person
specific lived-work claim REQUIRES the named entity (person,
project, client, dated event, specific number's source) to appear
in the voice substrate at programs/references/voice.md loaded into
source_data. Lived-work claim with a named entity that does not
trace to the voice.md substrate scores 0 even if the claim is
plausible — provenance must be in-substrate, not LLM-generated.
This is a JR-iterated substrate gate carried over from live code
(load_source_data loads programs/references/voice.md as parents[2]
of session_dir specifically so this check can fire judge-side).

Score 0.5 (unknown) — Single-line aphorism where the
lived-experience claim is ambiguous (could be quote-tweet, could
be generic platitude, could be earned reframing). Emit 0.5 +
"unknown" + one sentence. **Voice substrate not provisioned
(cold-start PRE-REQ gate):** if programs/references/voice.md is
absent from source_data or empty, emit 0.5 + "unknown" + "voice
substrate not provisioned — judge cannot score lived-experience
claims against ground truth." This closes the cold-start
chicken-and-egg: the voice substrate is a PREREQUISITE for
first-engagement judging at X-2; if the substrate does not exist,
X-2 abstains rather than scoring 0 by default (which would force
the workflow to strip lived-work specifics) or scoring 1 without
verification (which would invite confabulation). The bundle's
internal ordering is: voice substrate populates first
(operator-provided substrate authoring), THEN sample posts are
judged against the populated substrate.

Required reasoning (work through these 3 steps in your rationale):
1. List every specific entity, number, date, named project, or
   first-person anecdote.
2. For each, test whether the claim is non-regenerable from
   public-internet summarization. Flag specific-looking details
   reading as confabulated (no attribution, no resolvable
   provenance, conflated entities, non-existent dated events).
3. For any first-person specific lived-work claim, verify the
   named entity appears in the voice substrate
   (programs/references/voice.md segment of source_data). PRE-REQ
   check: if voice.md is absent or empty in source_data, emit 0.5
   + "unknown" + "voice substrate not provisioned — judge cannot
   score lived-experience claims against ground truth" for the
   whole criterion; do NOT apply HARD FLOOR in this state. If
   voice.md is populated AND a lived-work claim names an entity
   that is NOT in the voice substrate, score 0 — HARD FLOOR fires
   regardless of whether the claim is plausible elsewhere. Emit
   verdict + one-sentence justification.

Do not score: total word count, presence of "I" pronouns, claim
accuracy (judge cannot verify; confabulation flagging is pattern
recognition, not fact-checking)."""

_X_3 = """\
Evaluate this draft on ONE outcome question:

Could a thoughtful peer in this niche say "I disagree, and here's
why" — substantively, not stylistically? Is the claim wrong in at
least one knowable way a peer could articulate?

Score 1 (yes) — Position contradicts at least one widely-held
belief in its niche, OR claims a specific causal relationship the
reader could test against their own experience, OR makes a
falsifiable forward prediction. Claim is wrong in at least one
knowable way — peer could write a substantive counter-thread, not
just a stylistic complaint. Disagreement would be about substance
(causal model, empirical claim, strategic prescription), not
surface (tone, formatting, example choice).

Illustrative example (do not optimize toward this exact shape):
"Most B2B newsletters that hit 1,000 subscribers got there by
reposting LinkedIn content to email, not by building from
email-first." Specific causal claim; peer could disagree by citing
email-first newsletters that grew without LinkedIn repurposing.

Score 0 (no) — Unfalsifiable: tautology, generic platitude, claim
so hedged no one could substantively disagree, manufactured
controversy where the "disagreement" invited is stylistic. Earns
likes, earns no substantive replies. Triggers high mute rate among
readers who recognize provocation without substance.

Score 0.5 (unknown) — Falsifiability cannot be evaluated without
knowing the account's prior positions (claim might be radical for
this author and conventional for others); OR post is reply /
quote-tweet where the parent context carries the load. Emit 0.5 +
"unknown" + one sentence.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the central claim.
2. Test whether a thoughtful peer could substantively disagree on
   substance — not stylistically, not on tone, not by criticizing
   example choice, but by arguing the underlying causal model or
   empirical claim is wrong.
3. Emit verdict + one-sentence justification.

Do not score: claim controversy level, "controversial opinion"
markers, presence of "what do you think?" CTA (engagement-bait
CTAs route to structural_gate), whether the claim is actually
true."""

_X_4 = """\
Evaluate this draft on ONE outcome question:

Does the post's structure (single post vs thread) match the
density of its claim? Does each unit earn its place — would
removing any unit degrade the post?

Score 1 (yes) — Either (a) a single post under ~280 chars
containing exactly one coherent claim that resolves within the
post, OR (b) a thread of 3-12 tweets where each tweet reveals
something the prior tweet did not (Rate of Revelation per unit).
Removing any unit would degrade the post or break the promised
trajectory.

Illustrative example (do not optimize toward this exact shape):
A 6-word Naval-style declarative reframing that condenses a
5000-word essay; single-post form earned because expansion would
dilute.

Score 0 (no) — Either (a) single dense post burying a multi-claim
argument no scroller will parse — wall-of-text without 1-3-1
rhythm; OR (b) thread padding one insight across 8+ tweets with
restated points and connective tweets that reveal nothing
(promise-inflation). Padded threads produce the dwell-completion
drop documented by engagement-arbitrage detectors.

Score 0.5 (unknown) — Intended distribution (single post vs
thread, X-native vs cross-post) ambiguous from artifact. Emit 0.5
+ "unknown" + one sentence.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the post's form (single post / thread of N units).
2. For single posts, test whether claim density fits 280 chars (no
   buried multi-claim argument). For threads, walk each unit and
   test whether it reveals something the prior unit did not — Rate
   of Revelation applied per-unit, not as a sum.
3. Emit verdict + one-sentence justification.

Do not score: specific unit-count as target (always-5, always-7
templating fails this), exact character count, thread-length
conventions."""

_X_5 = """\
Evaluate this draft on ONE outcome question:

If the avatar and handle were stripped, would a regular reader of
this account — encountering the post in their feed — recognize it
as the author's voice and attribute it to this account specifically
(not "some founder")? Or does it read as machine-finished prose
anchored in the generic-niche-attractor cadence — the centroid of
"founder X voice" belonging to no specific person?

Score 1 (yes) — In data-rich regime (≥30 prior posts in
source_data): voice consistent with the account's established
empirical register (cadence, vocabulary mode, posture,
joke-to-seriousness ratio, signature rhetorical moves) AND no
AI-slop signature stack triggers (no 3+ co-occurring Tier-1/2
tells — em-dash density past account baseline + signature
transitions + reflexive tricolons + "Stop X. Start Y." + listicle
parallelism + false-vulnerability shape). Draft reads as
in-the-X-conversation (peer-to-peer, in-the-moment, punchy) rather
than imported from a different register (LinkedIn broadcast, blog
narrative, "lesson-extracting" conclusive tone). Post would be
screenshottable with author's name re-attributed and still read as
theirs.

In cold-start regime (<30 prior posts): prose is not recognizable
as machine-finished to an AI-aware reader (no centroid-voice
cadence collapse, no slop-stack triggers) AND draft is consistent
with the account's stated positioning in source_data (bio, declared
niche, stated topic focus). Slop-absence + positioning-consistency
replaces empirical voice-match.

"Looks like slop but isn't" defense. Real operators legitimately
use the surface markers that AI-slop detection enumerates. The
slop signal is the *stack* — 3+ Tier-1/2 tells co-occurring — NOT
any single tell in isolation. A post with one em-dash, one
antithesis, and one substantive claim is not slop; a post with
em-dash-every-line + "Stop X. Start Y." + reflexive tricolons +
"moreover" + parallel-listicle is slop. Judge tests gestalt, not
feature presence.

Illustrative example (do not optimize toward this exact shape):
Naval's 6-word openings where rhythm + lexical mode + posture
(declarative-reframing, lower-status, peer-not-mentor) all match
across 200+ posts. New draft in that pattern with substantive
content scores 1.

Score 0 (no) — Voice mismatches account's prior register (sober
technical account posting Hormozi-style heat); reads as
LinkedIn-shape imported to X (authority-positioned, narrative,
"the lesson is X" conclusive framing rather than peer-not-broadcast,
punchy-not-narrative); OR reads as machine-finished
(generic-niche-attractor cadence, 18-24-word sentence-length
plateau, no specific person's idiolect surface); OR triggers 3+
AI-slop signature stack tells co-occurring; OR opens with template
phrases anchoring a known LLM register ("Here's the thing nobody
tells you about," "Most people get this wrong," "Stop X. Start Y."
rhythm); OR uses jargon without inline plain-English context.
**Jargon-gloss rule (JR-iterated accessibility floor, carried over
from live code):** technical jargon (acronyms, niche terminology,
insider shorthand) appearing without inline plain-English gloss
caps this dimension — the JR voice anchor is "accessible to a
non-engineer founder/marketer," and unglossed jargon breaks that
contract regardless of whether the rest of the voice register
matches. A post can mention SOC2, ARR, ICP, MEDDIC, or RAG, but
the first use must carry enough surrounding context that a
non-engineer founder/marketer reading the screenshot understands
what is being claimed.

Score 0.5 (unknown) — Data-rich: voice consistency borderline and
slop-absence ambiguous from artifact alone. Cold-start: stated
positioning itself absent from source_data AND prose is borderline.
Emit 0.5 + "unknown" + one sentence.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the account's register from prior posts in source_data
   (cadence, vocabulary mode, posture, signature rhetorical moves).
   If <30 prior posts, switch to cold-start: identify stated
   positioning from source_data bio/niche/topic-focus. Form a
   one-sentence private description; do NOT enumerate features as
   a checklist.
2. Test whether the draft reads as in-the-X-conversation
   (peer-to-peer, in-the-moment, punchy, contrarian-not-conclusive)
   versus imported from a different register (LinkedIn broadcast,
   blog narrative, "lesson-extracting" mentor tone). Also apply
   the jargon-gloss check: identify any technical jargon (acronyms,
   niche terminology, insider shorthand); for each first use,
   verify inline plain-English context exists. Unglossed jargon
   caps this dimension — JR's voice anchor is
   accessible-to-non-engineer-founder/marketer, and unglossed
   jargon breaks that contract.
3. Test the draft for AI-slop signature *stack* — ≥3 of the named
   tells (em-dash density past account baseline, signature
   transition phrases, reflexive three-element parallel rhythm,
   "Stop X. Start Y." imperative-pair, false-vulnerability shape,
   listicle syntactic parallelism, cadence collapse toward
   18-24-word plateau) co-occurring. NOT presence-of-any-single-tell.
   Apply "looks like slop but isn't" defense — sparse use of
   em-dashes / antithesis / tricolons is rhetoric. Emit verdict +
   one-sentence justification.

Do not score: emoji in isolation, formal vs casual register on
its own, any specific punctuation in isolation, AI-detector
classifier output (not integrated)."""

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
# LinkedIn Engine — 6 rubrics (LI-1..LI-5 v3 binary outcome-question shape;
# LI-6 cross-item, gradient-form retained)
# ---------------------------------------------------------------------------
# v3 design lands the outcome-question + binary-anchor + 3-step-CoT shape
# per `docs/handoffs/2026-05-18-judge-design-step1-linkedin-engine.md` (v3,
# 2026-05-19). LI-1..LI-5 score 0 / 0.5 / 1 with a 0.5 "unknown" anchor that
# forces the judge to name the missing context. The 1/3/5 gradient shape
# (pre-v3) was retired for the same reasons CI moved off it: feature-check
# drift (Phase 4 pathology) + slot-fill mimicry.
#
# Surgical-restoration folds from v1 (ae34597) preserved verbatim in v3:
# - LI-1 "thoughtful authority, not contrarian punch" → LI-3 score-0 anchor
# - LI-1 "AUTOMATIC ≤4 bait-y / Twitter-translated" → LI-3 score-0 anchor
# - LI-2 HARD FLOOR "lived-work claims REQUIRE voice.md" → LI-3 score-0 +
#   CoT Step 1(c) voice-substrate provenance check
# - LI-3 cross-platform contrarian hot-take cap → LI-4 score-0
#   (cross-platform reply-ladder collapse: DH3-DH5 on X → DH0-DH2 on LI)
# - LI-5 hashtag-graduated scoring intentionally retired (hoisted to
#   structural_gate `[1, 5]` hard bounds; quality-scoring not in rubric)
#
# v3 changes vs v1:
# - LI-2 Step 3 softened to audience-existence-test (verdict 1 if insight
#   is non-obvious for AT LEAST ONE of the four primary audiences;
#   audience must be inferable, not named).
# - LI-3 CoT collapsed from effective 6 sub-steps to 3-step structure;
#   cold-start interaction with voice-substrate provenance spelled out
#   at score-0 prose, a dedicated cold-start paragraph, and inline in
#   CoT Step 1(c).
# - LI-1 / LI-4 / LI-5 prose preserved from v1.
#
# LI-6 cross-cohort stays at workflow CrossItemCriterion level per spec
# §8.9; retained here in 1/3/5 gradient form to preserve lane_registry
# rubric_ids tuple ("LI-1".."LI-6"). Migration of LI-6 to binary is a
# separate concern (touches lane_registry + cross-item aggregation
# math).

_LI_1 = """\
Evaluate this LinkedIn text post on ONE outcome question:

After reading only the trailer (everything above the "...more" cut,
typically the first 3 lines / ~210 characters), would a relevant
professional reader in the target context click "...more" — and once
they do, does the body below the cut deliver on the trailer's
implied promise rather than bait-and-switching them past the click?

Score 1 (yes) — Lines 1–3 contain a specific entity, number, claim,
or counterintuitive framing tied to the post's professional context.
The reader after line 3 has a clear sense of what payoff sits below
the cut, and that payoff is coherent with the opener (no
bait-and-switch where the body reads as unrelated to the trailer's
promise).

Illustrative example (do not optimize toward this exact shape):
"Hired a Gen-Z candidate without interviewing him. / Six months
later, he's our highest-leverage IC. / Here's the one bet that paid
off, and the two we're rolling back…" — trailer creates tension
(no-interview hire, leverage outcome), line 2 doubles down with a
specific result, line 3 promises a specific lessons-learned
breakdown the body has to deliver.

Score 0 (no) — Opener is a generic platitude, a vague claim
("Leadership is hard"), a motivational quote out of context, or
engagement-bait ("Agree?"). OR opener earns the click but the body
below the cut is unrelated to the promise (trailer promises a
specific tactical breakdown, body delivers generic platitude).

Score 0.5 (unknown) — Post is single-paragraph with no clear cut
point visible from the artifact (e.g., the artifact does not encode
the cut position and the judge cannot reconstruct where line 3
ends). OR the relevant professional reader cannot be inferred from
the artifact + source_data. Emit 0.5 + "unknown" + one sentence on
what's missing.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the trailer (everything above the "...more" cut,
   typically first 3 lines / ~210 chars). Test whether it contains a
   specific entity, number, claim, or counterintuitive framing.
2. Test whether the body below the cut delivers the trailer's
   promise — does the substance match the implied payoff, or does
   it bait-and-switch?
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification naming
   the specific trailer signal AND the specific payoff coherence
   (or its failure).

Do not score: trailer length exactness, presence of "..." or
"[continue reading]" markers, line-break count in the trailer,
broetry vs paragraph formatting (those live in structural_gate or
do not matter)."""

_LI_2 = """\
Evaluate this LinkedIn text post on ONE outcome question:

After reading the full post, would a relevant professional reader
leave with pattern-recognition, a framing, or a worked example they
did not arrive with — and is the insight author-specific enough that
swapping the author's name for a different operator would lose what
makes the post valuable?

Score 1 (yes) — Post contains at least one specific claim, number,
framing, or worked example that gives the reader pattern-recognition
they did not arrive with. The insight is non-generic — the Alić
specificity test holds: swap one named entity, number, or moment for
a generic placeholder, and the post would read differently. The
insight could plausibly only have come from this author's specific
position, evidence, or experience.

Illustrative example (do not optimize toward this exact shape):
"We A/B tested onboarding email length. 80-word emails outperformed
280-word by 40% on activation — *not* because shorter is better,
but because the 280-word version asked for two decisions and the
80-word asked for one. The constraint is decisions, not words.
We're rolling the rest of our email program against this." —
specific test, specific numbers, specific mechanism (decisions ≠
words), specific next-action implication.

Score 0 (no) — Post recycles generic advice ("write shorter
emails"), restates conventional wisdom without specific evidence,
OR could have been written by any author in the field (fails the
Denning name-stripped test). OR the insight is author-specific in
surface but generic in substance — a customer name dropped but the
underlying claim is a truism.

Score 0.5 (unknown) — Specific claim is present but the target
reader's prior knowledge level cannot be inferred from the artifact
+ source_data (e.g., insight may be novel to a junior IC, obvious
to a senior). Emit 0.5 + "unknown" + one sentence on what context
would resolve it.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the central insight in the post (the one thing the
   reader is supposed to leave with).
2. Apply the specificity test — would swapping the author's name or
   the named entities/numbers produce a different post? Is the
   insight non-obvious for at least one plausible target reader?
3. Verify that an inferable target audience exists (the post implies
   who would use this insight, even if the audience identity is not
   named explicitly in the post; the audience must be inferable from
   the substance). The audience does not need to be one specific
   named segment — verdict 1 if the insight is non-obvious for AT
   LEAST ONE of the four primary audiences (founder/decision-maker,
   mid-career B2B IC, recruiter/talent, industry peer). If no
   inferable audience, emit 0.5 + "unknown" + "cannot infer target
   audience." Emit verdict (0 / 0.5 / 1) + one-sentence
   justification naming the specific evidence anchor (or its
   absence) and the inferred audience (or its absence).

Do not score: insight controversy level, presence of named-customer
references on their own, length of the supporting story, presence
of numbered list or other format features."""

_LI_3 = """\
Evaluate this LinkedIn text post on ONE outcome question:

If a colleague who knows the author read this post anonymously,
would they recognize it as the author's writing — and would a
stranger NOT mistake it for AI-generated content? The test is the
gestalt voice stack, not any single tell.

Score 1 (yes) — Post has specific voice markers (sentence cadence,
turn of phrase, a moment of genuine surprise / anger / delight /
shame / stake, an anecdote tied to the author's actual professional
context, an internal self-correction or acknowledged limit). The
AI-tell gestalt does not trigger: no co-occurring stack of em-dash
density >1.0/100 words AND template-phrase opener AND
symmetrical-bullet rhythm AND P.S.↓ closer AND affective flatness.
OR — if a single weak signal triggers — at least one compensating
voice marker is clearly present (named entity in body, marked
affect, internal self-correction, specific anecdote).

Illustrative example (do not optimize toward this exact shape): a
post where the author admits they were wrong about a hiring call
from two years ago, names the specific moment they realized it (a
Tuesday Slack thread, a specific candidate's first-month review),
and ends on an open question about whether they would make the same
call now — the affective marker (regret/uncertainty), the named
anchor (Tuesday Slack), and the internal contradiction (they were
wrong) together signal authored voice that an AI default register
would not produce.

Score 0 (no) — Gestalt stack triggers: ≥2 co-occurring AI-tells from
the list (em-dash density >1.0/100w, template-phrase opener stack,
symmetrical-bullet rhythm with CV <0.15, P.S.↓ closer, broetry-line
density ≥40%, affective flatness) AND no compensating voice markers.
OR the post reads as affectively flat throughout — no specific
surprise, no specific anger or delight, no specific stake, no
internal self-correction, no named anchor. Cannot be distinguished
from AI-default-neutral register. OR the post reads as bait-y or
Twitter-translated (cross-platform import of contrarian-punch
register that works on X but lands as bait on LinkedIn — the
LinkedIn voice lever is *thoughtful authority, not contrarian
punch*; posts that translate X-shaped rhetorical compression into
the LinkedIn surface score 0 on this criterion even when individual
AI-tell signals do not trigger). OR the post makes a first-person
specific lived-work claim (named customer, named colleague, named
project, named dollar/percentage outcome owned by the author) where
the named entity does NOT appear in the author's voice substrate at
`programs/references/voice.md` — lived-work claims REQUIRE
voice-substrate provenance; unanchored first-person specifics are
confabulation regardless of surface fluency. (The cold-start
handling exception below applies.)

Cold-start interaction. In cold-start
(`pattern_data_density="cold"`, `voice.md` not provisioned, or
`source_data.author_context_known=false`), LI-3's substrate-
provenance check on first-person lived-work claims defers to 0.5 +
"unknown" + "voice substrate not provisioned — cannot verify
provenance of lived-work claims." The gestalt AI-slop stack check
still applies in cold-start; only the voice-substrate provenance
check defers. This prevents systematically penalizing cold-start
clients (no prior posts, no populated voice substrate) for naming
real customers / colleagues that the judge has no substrate to
validate against. When voice substrate is populated with ≥3
author-surface anchors AND `source_data.author_context_known=true`,
the substrate-provenance check fires normally and unanchored
lived-work specifics score 0.

Score 0.5 (unknown) — Single weak signal present (one em-dash in an
otherwise human-cadenced post; one template-phrase opener with
otherwise specific body) AND the artifact does not contain enough
material to test for compensating voice markers. Emit 0.5 +
"unknown" + the specific signal AND what compensating marker would
have to be present to commit to 1.

Required reasoning (work through these 3 steps in your rationale):
1. Apply the four gestalt / register / cross-platform / substrate
   checks together and emit per-check findings. (a) Scan for the
   gestalt AI-tell stack — count how many of (em-dash density /
   template-phrase opener / symmetrical bullets / P.S.↓ closer /
   broetry-line density / affective flatness) trigger (deterministic
   single-tell density gates have already run in `structural_gate`;
   the judge is scoring the residual). (b) Test for bait-y /
   Twitter-translated register — does the post read as a
   contrarian-punch hot-take imported from X, where the rhetorical
   compression that lands on X (sharp-line aphorism,
   hostility-shaped opener, ratio-bait framing) lands as bait on
   the LinkedIn surface? The LinkedIn voice lever is *thoughtful
   authority*, not contrarian punch. (c) Voice-substrate provenance
   check on first-person specific lived-work claims — for each
   named entity (customer, colleague, project, dollar/percentage
   outcome the author claims to have owned), test whether the
   entity appears in the loaded voice substrate at
   `programs/references/voice.md`. Unanchored lived-work specifics
   are confabulation. Cold-start handling: in cold-start (per
   score-0 prose above), this substrate-provenance sub-check defers
   to 0.5 + "unknown"; the gestalt and register sub-checks (a) and
   (b) still apply.
2. Identify compensating voice markers AND apply the three-signal
   substance test. For each gestalt signal that triggered in Step
   1(a), test whether a compensating voice marker is present (named
   entity in body, marked affect, internal self-correction, specific
   anecdote tied to author's professional context). Then apply the
   three-signal substance test: (i) specificity in the body (not
   just the opener); (ii) at least one marked affective valence in
   the body (specific irritation, surprise, regret, delight, stake);
   (iii) internal-contradiction tolerance (self-correction or
   acknowledged limit).
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification naming
   the dominant tell, the dominant compensating marker, the bait-y
   / Twitter-translated diagnosis, OR the unanchored lived-work
   claim (whichever is load-bearing for the verdict).

Do not score: total post length, paragraph count, presence of any
single punctuation mark in isolation, output of any AI-detector
classifier (FPR 18–35% against real operators — surface only as
soft signal if at all)."""

_LI_4 = """\
Evaluate this LinkedIn text post on ONE outcome question:

Would the relevant professional reader leave a substantive 30–80
word comment because the post offers them an organic entry point —
a debatable defensible claim, a genuine question requiring their
experience, an enumerated frame with empty-slot affordance, or an
honest-disagreement signal — rather than because a bolted-on CTA
prompted them to react?

The negative version of this question is the reader-effect anchor:
the relevant professional reader leaves no substantive 30–80 word
comment because the post invites no genuine entry point.

Score 1 (yes) — The post organically offers at least one of four
mechanism families: (a) a *debatable defensible claim* where the
author has visible standing and the claim is grounded in specific
evidence (reader can extend with their own case or push back with a
counter-case); (b) a *genuine question requiring the reader's
specific experience to answer* (not a rhetorical question dressed as
a survey — the question cannot be answered without the reader's
specific position); (c) a *numbered or enumerated frame with
empty-slot affordance* (the list signals incompleteness, the
reader's mental affordance is to contribute item N+1); (d) an
*honest-disagreement signal* ("I think X — here's where I might be
wrong; what am I missing?" — Graham's hierarchy DH4–DH5
counter-argument with stated uncertainty, not DH0–DH2
cheerleading/hostility/tone).

Illustrative example (do not optimize toward this exact shape): a
post that stakes a specific position on a hiring trade-off the
author lived ("We hired for raw IQ over domain experience and it
cost us nine months — here's the specific moment I realized the
trade-off and where I'd push back on my own argument"). Reader's
reply ladder ceiling: substantive case-comparison from their own
experience, not "agree!" cheerleading or "wrong, here's why"
hostility. Note: *taking a contrarian position without defensible
standing fails this criterion* — the standing is what enables
Graham DH4–DH5 replies instead of DH0–DH2 reactions.

Score 0 (no) — Post is a closed monologue with no entry point for
substantive contribution; OR a list of generic tips that closes the
enumeration (no empty-slot affordance); OR a pure announcement; OR
contrarian-for-its-own-sake (opener at DH0–DH2 rebuttal level, no
defensible standing — reply ladder ceiling is
cheerleading/hostility, not substantive engagement); OR
list-padding (numbered list where slots are non-substantive filler);
OR bolted-on (generic post with a "what do you think?" or "agree?"
closer tacked on, where the body itself invites no comment); OR
cross-platform contrarian hot-take whose register works on X but
mis-fires on LinkedIn (a hook that would plausibly score 1 on this
criterion's X-lane sibling scores 0 here because the LinkedIn
audience reads the same contrarian-punch register as bait, not as
substantive stance-taking — the reply ladder ceiling on LinkedIn
collapses to DH0–DH2 reactions where the X audience would have
gone DH3–DH5).

Score 0.5 (unknown) — Post invites comment via one of the four
mechanism families but the target reader's domain knowledge required
to comment substantively cannot be inferred from the artifact +
source_data. Emit 0.5 + "unknown" + the specific reader-context that
would have to be present.

Required reasoning (work through these 3 steps in your rationale):
1. Predict the reply-ladder ceiling. Given the post's opening stance
   and the way the substance lands, what reply distribution would it
   invite — DH3–DH5 substantive engagement (case-comparison,
   methodological pushback, framing extension), or DH0–DH2
   cheerleading/hostility/contradiction? The ceiling is set by the
   opener; the judge cannot recover from a low-ladder opener.
2. Identify which (if any) of the four mechanism families is present
   *organically* in the post — debatable defensible claim, genuine
   question requiring reader experience, enumerated frame with
   empty-slot affordance, honest-disagreement signal. Test for
   organic-vs-bolted-on: is the comment-seed coherent with the
   post's central argument, or attached at the close?
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification naming
   the specific mechanism family (or its absence) and the implied
   reply-ladder ceiling.

Do not score: presence of CTA on its own, presence of question
marks, presence of polls, presence of explicit "what do you think?"
closers (those route to structural_gate as deterministic
bait-string detection; the judge tests reader-effect, not surface
markers), bait-string detection itself."""

_LI_5 = """\
Evaluate this LinkedIn text post on ONE outcome question:

Would a relevant decision-maker reader treat this post as credible
thought leadership from this specific author — i.e., does the
post's confidence level, scope of claim, and frame of reference
match the author's visible professional seat (role, stage, employer,
expertise)? The dominant failure mode the judge must catch is
**authority-voice register mismatch under selection pressure**
(Resolution B), not the obvious topic-mismatch which structural_gate
already catches (Resolution A) or the temporal-claim mismatch
structural_gate also catches (Resolution C).

Score 1 (yes) — The post's authority-voice register matches the
author's seat. A founder-stage author writes about founder-stage
problems they have plausibly encountered. An IC writes from IC
vantage with the texture of having lived the work. An executive
writes from executive vantage with the scope of decisions their
seat actually owns. When the author makes a strong claim, the claim
sits inside their plausible standing. A reader who knows the
author's role would not pause on the post and think "that is not
what someone in this seat would write."

Illustrative example (do not optimize toward this exact shape): a
Series-A founder describing the specific moment they made a hiring
trade-off between two early salespeople, with the texture of having
lived it (a specific Slack thread, a specific 30-day review
meeting, a specific dollar amount they bet on the call) — not a
general "lessons from scaling sales orgs" piece that reads as one
stage above their actual position.

Score 0 (no) — The post's register is one stage above or below the
author's seat. Three concrete examples of the failure mode:

- Stage-too-high: Series-A founder narrating Series-D scaling pain
  ("when you're scaling past 500 reps, the comp ladder breaks at
  the senior IC tier…") — technically founder content from a
  founder, but the register implies post-Series-C operations the
  author has not lived.
- Role-too-high: VP-level confidence on IC-level topics — an IC
  writing VP-stance assertions about cross-functional strategy
  ("our team's playbook for aligning product and revenue org…")
  without the grounding of having owned that scope.
- Role-too-low: Junior IC writing as CEO — junior writer making
  market-positioning claims with executive scope ("here's how every
  founder should think about the category-defining moment…")
  without standing.

OR the post's topic sits entirely outside the author's plausible
standing (motivational/spiritual content from a B2B SaaS founder
unconnected to their professional surface; growth-marketing tactics
from a CFO with no marketing surface in their work history — though
most of these will already have been caught by structural_gate's
Role-Topic Token Overlap Gate before reaching the judge).

Score 0.5 (unknown) — The author's professional context cannot be
inferred from the artifact + source_data alone (cold-start author
with no prior posts and no work-history surface; source_data.role
is null or stage cannot be inferred to better than two adjacent
registers). Emit 0.5 + "unknown" + the specific context that would
have to be present to commit to 1 (e.g., "author's stage or
employer not in source_data; cannot assess register coherence").

Required reasoning (work through these 3 steps in your rationale):
1. Read the author's source_data block. Identify role (founder / IC
   / manager / executive), stage (early / mid / late), employer
   scope (early-stage / scaled), domain expertise. If source_data
   is null or insufficient to identify stage to within two adjacent
   registers, emit 0.5 + "unknown" with the specific missing
   context.
2. Read the post. Identify the *implied vantage* of the author from
   the substance — what stage / role / scope does the post's
   confidence level and frame of reference assume the author
   occupies? (Not from explicit prefix tokens like "as a founder"
   — those are gameable; from the substance.)
3. Compare. Is the implied vantage congruent with the author's
   actual seat? If gap > one register (founder→executive, IC→VP,
   junior→CEO, late-stage scope on early-stage seat), score 0 with
   the specific register signal named. If aligned within one
   register, score 1. Emit verdict (0 / 0.5 / 1) + one-sentence
   justification naming the specific register signal (or its
   absence).

Do not score: topic-vs-role overlap (Role-Topic Token Overlap Gate,
structural_gate); employer-mention validity (Employer-Mention
Validity Check, structural_gate); temporal-claim-vs-recent-activity
(Claim-vs-Recent-Activity Check, structural_gate); claim ambition
level on its own (a junior IC with deep specialty can make strong
claims in their specialty — only score 0 if the claim sits outside
the specialty band)."""

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
    # GEO — 8 rubrics (v3 outcome-question shape; binary 0/0.5/1 scoring
    # across all 8). Stream C C5 pilot: tier assignments per the RaR scheme
    # (essential carries the core GEO promise; pitfall flags generic
    # boilerplate). All other lanes default to "important" until tagged.
    # GEO-6 retains is_cross_item=True for cross-page diversity per
    # session_eval_geo.py CrossItemCriterion wiring; the v3 spec's GEO-6
    # (engine-side re-citation resilience) lives at GEO-7 in this 8-slot
    # registry — see header comment above.
    "GEO-1": RubricTemplate("GEO-1", "geo", "gradient", _GEO_1, tier="essential"),
    "GEO-2": RubricTemplate("GEO-2", "geo", "gradient", _GEO_2, tier="essential"),
    "GEO-3": RubricTemplate("GEO-3", "geo", "gradient", _GEO_3, tier="important"),
    "GEO-4": RubricTemplate("GEO-4", "geo", "gradient", _GEO_4, tier="optional"),
    "GEO-5": RubricTemplate("GEO-5", "geo", "gradient", _GEO_5, tier="important"),
    "GEO-6": RubricTemplate("GEO-6", "geo", "checklist", _GEO_6, is_cross_item=True, tier="important"),
    "GEO-7": RubricTemplate("GEO-7", "geo", "checklist", _GEO_7, tier="essential"),
    "GEO-8": RubricTemplate("GEO-8", "geo", "gradient", _GEO_8, tier="pitfall"),
    # Competitive Intelligence — 6 rubrics (v3.3 outcome-question shape, all
    # scored 0/0.5/1 by the judge; scorer_binary.md maps onto the 0-10
    # aggregate envelope). Tiers (2026-05-18 v3.3):
    # - essential: CI-1 forces a concrete action, CI-5 names the trade-off
    #   — the brief's core reasons to exist.
    # - important: CI-2 trajectory, CI-3 structural mechanism, CI-6
    #   evidence chain — substantively support the essentials.
    # - pitfall: CI-4 uncomfortable truth — discriminates against the
    #   feel-good slop failure mode (Phase 3 §3a "mediocre" mode).
    # rubric_type stays "gradient" because the prompt prose drives the
    # 0/0.5/1 scoring; the type field is a hint for downstream aggregation
    # which still consumes the 0-10 aggregate_score envelope unchanged.
    "CI-1": RubricTemplate("CI-1", "competitive", "gradient", _CI_1, tier="essential"),
    "CI-2": RubricTemplate("CI-2", "competitive", "gradient", _CI_2, tier="important"),
    "CI-3": RubricTemplate("CI-3", "competitive", "gradient", _CI_3, tier="important"),
    "CI-4": RubricTemplate("CI-4", "competitive", "gradient", _CI_4, tier="pitfall"),
    "CI-5": RubricTemplate("CI-5", "competitive", "gradient", _CI_5, tier="essential"),
    "CI-6": RubricTemplate("CI-6", "competitive", "gradient", _CI_6, tier="important"),
    # Monitoring Digest — 6 rubrics (v3 outcome-question shape, all scored
    # 0/0.5/1 by the judge; scorer_binary.md maps onto the 0-10 aggregate
    # envelope). MON-7 watchlist-arc folded into MON-6 score-1 anchor; MON-8
    # editorial-restraint folded into §5 wrapper. Tiers (2026-05-19 v3):
    # - essential: MON-3 highest-stakes lede, MON-4 owner+deadline+consequence
    #   action items — the digest's reason to exist.
    # - important: MON-1 baseline-relative framing, MON-2 severity reasoning,
    #   MON-6 compound evidence chain — substantively support the essentials.
    # - pitfall: MON-5 absence-as-signal — discriminates against apophenia /
    #   absence-fabrication AI-failure surface (documented exception #1).
    # MON-5 + MON-6 are TWO documented exceptions to the ≤5 criteria ceiling
    # per docs/handoffs/2026-05-18-judge-design-step1-monitoring.md §7.
    # rubric_type stays "gradient" because the prompt prose drives the
    # 0/0.5/1 scoring; the type field is a hint for downstream aggregation
    # which still consumes the 0-10 aggregate_score envelope unchanged.
    "MON-1": RubricTemplate("MON-1", "monitoring", "gradient", _MON_1, tier="important"),
    "MON-2": RubricTemplate("MON-2", "monitoring", "gradient", _MON_2, tier="important"),
    "MON-3": RubricTemplate("MON-3", "monitoring", "gradient", _MON_3, tier="essential"),
    "MON-4": RubricTemplate("MON-4", "monitoring", "gradient", _MON_4, tier="essential"),
    "MON-5": RubricTemplate("MON-5", "monitoring", "gradient", _MON_5, tier="pitfall"),
    "MON-6": RubricTemplate("MON-6", "monitoring", "gradient", _MON_6, tier="important"),
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

assert len(RUBRICS) == 49, f"Expected 49 rubrics (28 base + 8 MA + 13 X/LI incl. X-9; CI dropped 8→6 in v3.3, MON dropped 8→6 in v3), got {len(RUBRICS)}"

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
