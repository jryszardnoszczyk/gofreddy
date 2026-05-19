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
# Verification
# ---------------------------------------------------------------------------

assert len(RUBRICS) == 51, f"Expected 51 rubrics (30 base + 8 MA + 13 X/LI incl. X-9; CI dropped 8→6 in v3.3), got {len(RUBRICS)}"

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
