---
date: 2026-05-12
phase: D
lane: geo
status: spec-ready, awaiting first-5-runs empirical validation
---

# Phase D — `geo` Rubric Spec

Final criterion list and prose for the GEO judge, grounded in Phase A
(optimization target: maximize likelihood AI engines cite the page +
faithfully extract its content), Phase B (calibration against the 2026
citation ceiling), Phase C (structural-gate prevented empirical
validation on v189/mayoclinic — criteria proceed on Phase B strength
alone and carry a first-5-runs validation flag).

Shape inherits monitoring's "gold standard": ONE quality per criterion,
gradient or checklist by natural fit, ground-truth cross-references
where anti-fabrication matters, CoT-before-score closing.

## 1. Summary table

| Code | Tier | One-quality summary | Disposition |
|---|---|---|---|
| GEO-1 | essential | Every H2/H3 section is a self-contained chunk (80–250 words, no anaphora, first-sentence-answer). | STRENGTHEN |
| GEO-2 | essential | Quantitative claims inline-cited to external primary sources, ≥1 per 150 words, ≥60% external-primary. | STRENGTHEN |
| GEO-3 | important | Page concedes ≥1 specific named-competitor advantage with price/duration/method anchor. | KEEP |
| GEO-4 | optional | New content reads as always-part-of-page (voice + structure fit vs `pages/<slug>.json`). | KEEP |
| GEO-5 | important | ≥2 proprietary numbers attributed to client's own data, each with N or 3-decimal precision + date. | STRENGTHEN |
| GEO-6 | important (cross-item) | Pages in set lead with distinct angles, statistics, fan-out coverage. | STRENGTHEN |
| GEO-7a | essential | Lede ≤60 words (before any subheading) is standalone answer to head query with keyword + numeric anchor. | SPLIT-FROM-GEO-7 |
| GEO-7b | essential (checklist) | Page covers declared fan-out matrix — ≥10 distinct sub-query sections, ≥120 words each, answer-first lead. | SPLIT-FROM-GEO-7 |
| GEO-8a | important | Schema is attribute-rich: strictest type, ≥2 typed entities, ≥6 attrs each, ≥4 external `sameAs`, `cost` as `MonetaryAmount`. | SPLIT-FROM-GEO-8 |
| GEO-8b | essential | Crawl-eligible to GPTBot/PerplexityBot/ClaudeBot/Google-Extended/Bingbot (200, robots.txt permits, TTFB ≤500ms, no CF challenge). | SPLIT-FROM-GEO-8 |
| GEO-9 | essential | ≥1 named individual quoted verbatim in `"..."` with role/credential + date within 18 months. | NEW |
| GEO-10 | important | Visible "Zaktualizowano:" within 90 days, ≥3 dated facts in body, `dateModified` matches visible date ±1 day. | NEW |
| GEO-11 | pitfall | Tech recs reference real elements/counts/URLs in `pages/<slug>.json`; no fabricated problems. | STRENGTHEN-FROM-GEO-8 |

Final count: 13 criteria — 6 essential (GEO-1, GEO-2, GEO-7a, GEO-7b,
GEO-8b, GEO-9), 5 important (GEO-3, GEO-5, GEO-6, GEO-8a, GEO-10), 1
optional (GEO-4), 1 pitfall (GEO-11). Old GEO-8 splits across GEO-8a
(schema as positive signal), GEO-8b (crawl eligibility precondition),
and GEO-11 (anti-fabrication retained as pitfall against audit data).

## 2. Final criterion prose

### GEO-1 — Chunk extractability (STRENGTHEN)

- **Diff:** current asks "could an AI engine extract any single block?"
  without quantitative anchors. Strengthened pins 9-tier at ≥80% of
  H2/H3 sections passing three sub-conditions (80–250 words, no
  anaphora, first-sentence-answer). Phase B signal 1.7: Wellows 120–
  180-word sections get 70% more ChatGPT citations; under 50 words =
  insufficient signal density.

```
Evaluate this optimized page content for ONE quality:
Does every H2/H3 section read as a standalone extractable answer —
80–250 words, no back-references, first sentence is the answer?

Vector retrieval operates on 256–512-token chunks and the boundary
almost always falls at an H2. A section that opens with "as
mentioned above" or runs under 50 words loses to a self-contained
competitor section in the rerank.

Score 1: Sections routinely depend on surrounding context. Anaphora
("as discussed above", "see below") appears frequently. Many
sections under 50 words or over 250 with no internal structure.
Extracting any block delivers an incomplete answer.

Score 3: Some sections are self-contained but a meaningful minority
fail one or more conditions — anaphora survives, sections run too
short, or first-sentence-answer is inconsistent. An AI engine
succeeds extracting some, fails on others.

Score 5: At least 80% of H2/H3 sections pass all three: (a) 80–250
words, (b) no anaphoric back-references, (c) first sentence is a
complete answer that quotes well as a standalone chunk. The
remaining ≤20% are short or long by intent (glossary entry,
single-procedure walkthrough) and still read standalone.

Provide your reasoning, cite specific sections (by H2/H3 heading),
then give your score.
```

### GEO-2 — Inline citation density to primary sources (STRENGTHEN)

- **Diff:** current asks for "specific and verifiable" without a
  density bar. Strengthened pins 9-tier at ≥1 inline external-primary
  citation per 150 words, ≥60% external-primary domain ratio. Phase B
  signal 1.2: KDD 2024 +30%; Aleyda e-commerce Pattern 3 (source mix
  shifts by evidence type).

```
Evaluate this optimized page content for ONE quality:
Are quantitative claims hyperlinked to external primary sources
at the sentence — not bunched at the bottom — at ≥1 inline
external-primary citation per 150 words?

AI engines reweight chunks by source-link entropy. A page with no
inline links collapses to "marketing copy" in the rerank. Self-
domain links do not count toward external-primary.

Score 1: Numeric and factual claims appear without inline links.
References (if any) are bunched at the bottom or exclusively self-
domain. External-primary ratio below 0.1 per 150 words.

Score 3: Some claims carry inline citations but density is uneven
— opening sections cite, back half asserts without linking.
External-primary ratio 0.3–0.5, or inline links mostly self-domain.

Score 5: Every quantitative claim (zł/%/min/mg/N/percentages) is
hyperlinked at the sentence to a primary source (peer-reviewed
paper, UpToDate/ClinicalTrials.gov/EMA/MedDRA/URPL for medical,
regulator or first-party registry otherwise). Density ≥1 inline
citation per 150 words, ≥60% external-primary. Bunched bottom-of-
page reference lists do not satisfy this criterion.

Provide your reasoning, cite the specific links (quote the claim +
the link target), then give your score.
```

### GEO-3 — Honest competitive positioning (KEEP)

Phase B signal 1.9 confirms well-calibrated: Aleyda Pattern 6 ("even
category leaders hold a minority share of citations about themselves")
reinforces the 9-anchor of "name a specific competitor advantage and
explain why." Existing anti-pattern ("client wins every row") is the
exact 5-tier fail Phase B documents.

(kept verbatim — see `src/evaluation/rubrics.py` `_GEO_3`)

### GEO-4 — Voice and structure fit (KEEP)

Cross-reference against `pages/<slug>.json` is the load-bearing
anti-fabrication pattern (Phase A §5). Tier stays optional — voice fit
is not a citation-causal lever, but it is the publish-eligibility
precondition for the operator to merge content into the page.

(kept verbatim — see `src/evaluation/rubrics.py` `_GEO_4`)

### GEO-5 — Citability moat: proprietary numbers (STRENGTHEN)

- **Diff:** current asks for "first-party attribution" without a bar.
  Strengthened requires ≥2 distinct quantitative claims attributed to
  client's own data, each with N or ≥3-decimal precision + date window.
  Phase B signal 1.8: Cyrus Shepard's Spearman 0.357 on Proprietary
  Assets; commodity numbers collapse to industry aggregators.

```
Evaluate this optimized page content for ONE quality:
Does the page publish ≥2 distinct quantitative claims only this
client could publish — proprietary outcome data, internal retention
rates, complication frequency from own register, effect duration
from own follow-ups — each with sample size or three-decimal
precision + date window?

When AI engines synthesise from multiple sources, the chunk with a
number no competitor can replicate is the chunk that gets quoted.
Commodity numbers ("botoks działa około 3–4 miesięcy") collapse to
the industry aggregator (UpToDate, NHS) and the client's page is
skipped.

Score 1: All quantitative claims are publicly available statistics
or generic ranges. No number is attributable to the client's own
operational data. Page is a reskinning of category-average content.

Score 3: One proprietary claim exists but missing sample size,
missing date window, or rounded so it reads as a generic estimate
("about 80% of our patients return"). Reader cannot distinguish
first-party data from industry averages.

Score 5: At least two distinct proprietary quantitative claims, each
with (a) sample size N or precision to three decimals, (b) date
range or "as of YYYY-MM", (c) explicit attribution to the client's
internal data ("nasza obserwacja N=1,247, marzec 2024–luty 2025").
Claims are ones a competitor could not publish without parallel
internal data.

Provide your reasoning, cite the proprietary claims verbatim, then
give your score.
```

### GEO-6 — Cross-page diversity (STRENGTHEN, cross-item)

- **Diff:** Phase C §5 flagged that the cross-lane 5-tier failure is
  "3–5 wordings of one bet" passing as cohort diversity. Sub-question
  #4 is strengthened to require distinct fan-out coverage across pages,
  not vague "different facets."

```
Evaluate the set of optimized pages for ONE quality:
Does each page pursue a different primary angle, target distinct
sub-queries, contribute non-overlapping evidence — or do pages
restate the same differentiators, numbers, fan-out coverage with
different wording?

Answer each sub-question with YES or NO. Quote supporting passages.

1. Does each page lead with a different primary differentiator?
   (No two pages open with the same positioning claim or restate
   the same value proposition.)

2. Are proprietary statistics and named-expert quotes across pages
   distinct? (The same number or Dr-Name-quote does not appear as
   load-bearing chunk on more than one page.)

3. Do FAQ/H2 sections across pages map to distinct fan-out sub-
   queries? (No sub-query — "ile kosztuje", "czy bezpieczne",
   "jak długo trwa" — answered as primary H2 on more than one page.)

4. Do pages collectively cover a larger fan-out matrix than any
   single page? (Pages are siblings filling distinct sub-query
   nodes, not competitors collapsing onto the same citation surface.)

Provide your overall reasoning, then evaluate each sub-question.
```

### GEO-7a — Answer-first head-query lede (SPLIT-FROM-GEO-7)

- **Diff:** current GEO-7 conflates head-query satisfaction with
  sub-query coverage. Phase B 1.3: Wellows answer-first +40% citations;
  ChatGPT 5.2 narrows retrieval window. Lede becomes a distinct
  load-bearing signal — fan-out narrowing collapses the candidate pool
  to whichever page's first extractable chunk wins.

```
Evaluate this optimized page content for ONE quality:
Is the opening paragraph — before any subheading — a complete
standalone answer to the page's primary declared query, in ≤60
words, containing the query keyword and a numeric anchor?

ChatGPT 5.2 and AI Mode generate longer-tail queries with minimal
fan-out. The first extractable chunk that fully answers the
rewritten query wins the citation slot. Pages that bury the answer
below an "Introduction" or a definition lose to competitors whose
ledes carry the answer.

Score 1: Opening paragraph is a definition, brand statement, or
generic introduction. No head-query keyword, no numeric anchor,
not a complete answer. Actual answer appears below H2, if at all.

Score 3: Lede gestures at the answer but fails one of: (a) contains
the head-query keyword, (b) includes a numeric anchor (zł/%/min/
mg/N), (c) reads as a complete standalone clause. Either the answer
requires reading paragraph 2, or the lede is generic enough that
95% of competitor pages could use the same opening.

Score 5: Opening paragraph is ≤60 words, contains the primary query
keyword, includes ≥1 numeric anchor (price, count, duration, dose),
reads as a complete standalone answer that extracts cleanly as an
AI citation. A quoted fragment would satisfy a user typing the head
query into ChatGPT or Perplexity without further reading.

Provide your reasoning, quote the lede verbatim, identify the
declared primary query from the page header, then give your score.
```

### GEO-7b — Fan-out coverage matrix (SPLIT-FROM-GEO-7)

- **Diff:** second half of split. Phase B 1.4: iPullRank Qforia +
  Ekamoira — 1,000 KW Planner searches = 15,600 retrieval events at AI
  Mode. Coverage compounds the citation surface; pages covering 3/12
  sub-queries are eligible on 3/12, not 12/12. Cross-references against
  `gap_allocation.json`.

```
Evaluate this optimized page content for ONE quality:
Does the page cover the declared fan-out matrix of sub-queries —
at least ten distinct sibling sub-queries, each as its own H2/H3
section ≥120 words opening with an answer-first sentence?

Answer each sub-question with YES or NO. For each, quote the
specific H2/H3 headings and opening sentences.

1. Does the page contain ≥10 distinct H2/H3 sections that each map
   to a documented fan-out sub-query? (For `/zabiegi/botoks` the
   matrix includes cena, przeciwwskazania, skutki uboczne, czas
   trwania efektu, ból, lekarz, alternatywy, ciąża, opinie, przed/
   po, regeneracja, powikłania.)

2. Does each fan-out section run ≥120 words and open with a
   sentence that directly answers the sub-query — not a definition,
   setup, or transition?

3. Are the fan-out sections present as actual H2/H3 prose — not
   buried inside FAQPage schema only? (Schema-only coverage is
   invisible to chunk-level retrieval.)

4. Does the set of covered sub-queries match the declared target
   queries in the page header / `gap_allocation.json`? (Coverage
   of arbitrary sub-questions that aren't in the target matrix
   doesn't count.)

Cross-reference against `pages/<slug>.json` and `gap_allocation.json`
to verify which sub-queries the page was supposed to cover.

Provide your overall reasoning, then evaluate each sub-question.
```

### GEO-8a — Attribute-rich schema and entity IDs (SPLIT-FROM-GEO-8)

- **Diff:** old GEO-8 was anti-fabrication on tech recommendations
  (now GEO-11). Schema was ungraded. GEO-8a makes attribute-rich schema
  a positive signal. Phase B 1.6: Ahrefs 1885-page cohort — generic
  schema 0 lift, attribute-rich +61.7%. Phase B 1.12: Wellows 15+
  connected entities = 4.8× boost; Perplexity L3 filters entity-
  ambiguous pages.

```
Evaluate this optimized page content for ONE quality:
Does the page's JSON-LD schema use the strictest applicable type
with attribute-rich coverage and external entity identifiers — not
generic Service/Article with required-only fields?

Generic schema is noise: every page has it. Attribute-rich schema
with `sameAs` identifiers gives the indexer layer (Knowledge Graph,
Bing grounding) discriminating signal at index time. Pages with
ambiguous entity strings are filtered by Perplexity's L3 quality
gate before entering the candidate pool.

Score 1: Schema is generic (`@type: Article` or `@type: Service`
with `name` + `provider` only). No typed nested entities, no
external `sameAs`, no `cost` as `MonetaryAmount`. Validates but
contributes zero signal to the grounding index.

Score 3: Schema uses an applicable specific type (e.g.
`MedicalProcedure`) but attribute coverage is uneven — fewer than
six populated attributes per entity, or zero external `sameAs`,
or `cost` as free-text rather than `MonetaryAmount`. Some signal,
not load-bearing.

Score 5: Strictest applicable type with ≥2 distinct typed entities
(`MedicalProcedure` + `Physician` + `MedicalCondition`), each with
≥6 populated attributes, ≥4 external `sameAs` identifiers across
the graph (Wikidata QID for organization, ORCID/PWZ for doctors,
ICD-10 or SNOMED for conditions, ChEMBL or DrugBank for drugs),
`cost` as `MonetaryAmount` with currency and value, entity nesting
that reflects the real relationship between procedure, practitioner,
condition.

Cross-reference against the original schema in `pages/<slug>.json`
to verify the optimized schema is genuinely richer. Schema that
validates but adds no discriminating attributes scores low.

Provide your reasoning, quote optimized schema fragments by
attribute, then give your score.
```

### GEO-8b — Crawl eligibility for AI fetchers (NEW, SPLIT)

- **Diff:** new criterion; current rubric does not grade fetchability.
  Phase B 1.11: Zyppy 2026 — URL accessibility 9.5/10 is the #1 of 23
  factors. Mike King 700K-page Profound study documents the
  undocumented status code making content invisible to ChatGPT/
  Perplexity. Cloudflare verified-bot challenges block AI agents
  before content-quality signals matter.

```
Evaluate this optimized page content for ONE quality:
Is the page crawl-eligible to AI fetchers — does the artifact
document that GPTBot, PerplexityBot, ClaudeBot, Google-Extended,
and Bingbot return 200 with TTFB ≤500ms, robots.txt permits each,
and no Cloudflare verified-bot challenge fires?

Answer each sub-question with YES or NO. For each, quote the
audit data or recommendation that supports your answer.

1. Does the artifact include or reference a `robots.txt` audit
   showing GPTBot, PerplexityBot, ClaudeBot, Google-Extended, and
   Bingbot are explicitly permitted (not denied by `User-Agent: *`
   disallow)?

2. Does the artifact include a per-agent probe (200, body length,
   content-type) for at least the five named AI fetchers? A
   Cloudflare 403/503 challenge counts as fail, not pass.

3. Does the artifact document TTFB ≤500ms (and ≤1500ms for the LCP
   element)? Slow pages time out the agent before chunk extraction.

4. If any agent fails the probe, does the recommendation block name
   a specific remediation (allowlist entry, Cloudflare rule, CDN
   config) — not generic "improve crawl eligibility"?

Cross-reference against the crawl-eligibility audit section in
`pages/<slug>.json` to verify probes were actually run, not
fabricated.

Provide your overall reasoning, then evaluate each sub-question.
```

### GEO-9 — Named-expert quoted attribution (NEW)

Phase B 1.1: KDD 2024 +41% citation lift (single largest experimental
effect in the Phase B research base); Zyppy 2.1× lift on pages with
≥1 named-source citation; Aleyda 2026-05-07 names "Factual fidelity,
Source attribution quality" as new Bing grounding-index signals.
Quotation marks + named anchor = high-confidence pass-through signal
for RAG.

```
Evaluate this optimized page content for ONE quality:
Does the page contain ≥1 verbatim quoted passage of ≥15 words,
enclosed in quotation marks, attributed to a named individual with
stated role/credential, dated within the last 18 months?

AI engines use quoted spans with named proper-noun attribution as
high-confidence pass-through citations — they quote the chunk
verbatim rather than paraphrasing. Editorial assertions ("experts
say", "studies show") without a named source are paraphrased or
skipped. This is the single largest experimental effect in 2024–
2026 GEO research (KDD 2024 +41% lift; Zyppy 2.1× on named-source).

Score 1: Claims via editorial voice with no named individual
quoted. "Experts agree", "studies show", "industry consensus" in
place of attribution. No quotation marks enclose a multi-sentence
span attributed to a specific person.

Score 3: One named-source attribution exists but fails one or more
conditions: quote under 15 words, attribution missing role/
credential, or date older than 18 months. Quote present but does
not carry the full pass-through signal.

Score 5: ≥1 quoted passage of ≥15 words in proper quotation marks,
attributed to a named individual with role + credential ("Dr Anna
Kowalska, dermatolog z 12-letnim stażem"), dated within the last
18 months (interview or publication date stated). Quote carries a
substantive factual claim — number, procedural detail, clinical
observation — not a generic endorsement.

Provide your reasoning, quote the named-attribution passage(s)
verbatim, identify the attributed individual and their credential,
then give your score.
```

### GEO-10 — Freshness coherence (NEW)

Phase B 1.5: Bing grounding-index team (Aleyda 2026-05-07) names
freshness as one of five new index signals; Authority Tech: Perplexity
cites content under 30 days old at 82% rate; Aleyda 2026-05-08 warns
against gaming `dateModified` without refresh. Mechanism is
contradiction-detection — stated date contradicting body data dates
triggers "stale dressed as fresh" demotion.

```
Evaluate this optimized page content for ONE quality:
Is the page's freshness signal coherent across visible date, body
data dates, and JSON-LD `dateModified` — visible "Zaktualizowano:"
within 90 days, ≥3 dated facts in body, schema `dateModified`
matching visible date within ±1 day?

The 2026 grounding index detects ornamental freshness: nightly
`dateModified` bumps without body refresh, "updated 2026" banners
over 18-month-old data, schema dates contradicting visible dates.
Pages with date-contradictions are demoted from the freshness-
sensitive citation pool (pricing, regulation, clinical queries).

Score 1: No visible "Zaktualizowano:" or equivalent. Body data is
undated or older than 12 months. `dateModified` in schema (if
present) contradicts nothing because nothing visible exists to
contradict — the page is opaque about freshness.

Score 3: Visible date stamp present but signals inconsistent —
visible date recent but body data 12–18 months old, or
`dateModified` bumped without visible-date update, or fewer than
three dated facts in body. Some signal but contradiction-detection
would catch it.

Score 5: Three conditions hold: (a) visible "Zaktualizowano:
[YYYY-MM-DD]" within 90 days, (b) ≥3 quantitative or factual
claims in body carry their own data date ("stan na marzec 2026",
"URPL Q1 2026", "obserwacja 2025"), (c) JSON-LD `dateModified`
matches visible date within ±1 day. Reader can verify the page is
genuinely fresh, not ornamentally redated.

Provide your reasoning, quote the visible date, body data dates,
and schema `dateModified`, then give your score.
```

### GEO-11 — Tech recommendations grounded in actual page (STRENGTHEN-FROM-GEO-8)

- **Diff:** anti-fabrication portion of old GEO-8 retained as the GEO
  pitfall, separated from schema (GEO-8a) and crawl eligibility
  (GEO-8b). Ground-truth cross-reference against `pages/<slug>.json`
  is Phase A §5's load-bearing pattern.

```
Evaluate this optimized page content for ONE quality:
Do tech recommendations reference real problems observed on this
specific page, with element-level locations, counts, or URLs that
tie each fix to evidence in the audit data — or are recommendations
generic boilerplate or fabricated against problems that don't exist?

Score 1: Recommendations are generic boilerplate ("add alt text",
"improve page speed", "add internal links") with no reference to
what is actually missing on this page. Or worse: recommendations
name specific problems that, when cross-referenced against
`pages/<slug>.json`, do not exist (fabricated counts, hallucinated
headings, URLs that don't render).

Score 3: Some recommendations reference real page elements (a
named H2, a specific image), others are generic or loosely worded
enough that a developer would need to investigate. Mixed grounding
— partly real, partly boilerplate.

Score 5: Every tech recommendation names a specific problem on
this page with (a) element-level location (CSS selector, H2 text,
image filename), (b) count or measurement from audit data ("17
images missing alt text", "LCP at 4.2s on mobile"), (c) fix
expressed precisely enough that a developer could implement without
follow-up. All named problems verifiable against `pages/<slug>.json`.

Cross-reference each recommendation against `pages/<slug>.json` to
verify the named problem actually exists. Specific-sounding
recommendations referencing fabricated counts, missing elements
that aren't missing, or URLs that don't match the page structure
should score low — fabrication is the dominant failure mode here.

Provide your reasoning, quote each recommendation with the
corresponding evidence (or absence of evidence) from
`pages/<slug>.json`, then give your score.
```

## 3. Implementation notes

### RUBRIC_VERSION hash invalidation

Adds 5 new criterion IDs (GEO-7a/7b, 8a/8b, 9, 10, 11; old GEO-8
removed) and rewrites prose for GEO-1, GEO-2, GEO-5, GEO-6, GEO-7,
GEO-8. When this lands, rubric_hash changes. Per `score_holdout.py:
245-266`, holdout cache invalidates on mismatch — all v189 and prior
geo holdout scores become incomparable. Recompute frontier scores in
`autoresearch/archive/frontier.json` after a clean baseline run.

### Structural-gate changes

Phase C: v189 geo had every artifact rejected ("No FAQ / No [INTRO]").
New GEO-7a grades the answer-first lede before any subheading — the
literal `[INTRO]` marker is the substrate's forcing function, not what
AI engines read.

**Recommendation: keep the gate as-is for the first 5 real runs** to
validate new criteria on artifacts that already pass. Revisit in a
substrate ticket if the gate over-prunes the candidate pool.

### Cross-reference paths required

- **GEO-4, GEO-7b, GEO-8a, GEO-11:** `pages/<slug>.json` provides
  voice baseline, target queries, original schema, audit-data ground
  truth.
- **GEO-7b:** `gap_allocation.json` provides the fan-out matrix.
- **GEO-8b:** requires a per-agent crawl-eligibility audit section in
  `pages/<slug>.json` or sidecar. **Substrate-side requirement** —
  if `src/lanes/geo/optimize.py` doesn't run AI-agent probes, GEO-8b
  collapses to "no evidence — score 1" every run.

First-5-runs validation must confirm `pages/<slug>.json` carries page
content, target queries, original schema, crawl audit. If any section
missing, mask the criterion or fix substrate before scoring.

### Compliance regime interaction

Geo has no direct compliance gate (Phase A: operator-merged, not
client-facing). But **Klinika v1** interacts with `medical_pl`: GEO-5
(proprietary numbers) and GEO-9 (named-expert quotes) can produce
results-promise patterns ("Dr Kowalska: 'botoks działa 3,4 miesiąca
u 82% naszych pacjentów'") that medical_pl flags. Per Phase A §6,
compliance fires before quality. No GEO rubric change needed — the
two-judge pipeline handles routing.

## 4. Validation plan

What to test on the first 5 real geo runs after landing.

### Failure modes to watch for

1. **GEO-9 floored by missing expert corpus.** If substrate cannot
   produce a named-expert `"..."` quote (no operator-provided expert
   corpus for Klinika v1), GEO-9 scores 1 on every artifact and floors
   composite. 5/5 at GEO-9=1 = substrate ticket, not rubric ticket.

2. **GEO-8b floored by missing probe data.** If substrate omits
   AI-agent crawl probes, no audit section exists and GEO-8b scores 1
   across the board. 5/5 at GEO-8b=1 with otherwise strong artifacts =
   substrate is missing the crawl-eligibility step.

3. **GEO-7a vs structural-gate interaction.** If the literal `[INTRO]`
   gate rejects artifacts whose first paragraph satisfies answer-first,
   the judge never grades real strong ledes. Sample 10 pre-gate
   outputs and check overlap.

4. **GEO-10 over-rewards ornamental freshness.** Failure mode is
   "Zaktualizowano: today" + one data-date tag without body refresh.
   Diff body v_n vs v_n+1 — if `dateModified` changes but body diff
   is empty, GEO-10 needs an anti-gaming sub-condition.

5. **GEO-11 collapse on empty recommendations.** If substrate stops
   producing tech recs, GEO-11 has nothing to grade. Confirm
   recommendations present 5/5; if not, add explicit "no
   recommendations = score 1" anchor.

### Success patterns to confirm

1. **GEO-9 separates 9-tier from 5-tier.** Real Dr-quote artifact
   ≥4 on GEO-9, ≥6 composite; "experts agree" editorial =1 / ≤4. <3
   composite-point spread = weight is wrong (KDD +41% should not
   collapse).

2. **GEO-7a + GEO-7b discriminate.** Strong-lede / 4-sub-query = 5/2;
   weak-lede / 12-sub-query = 2/5. Composite must differentiate, not
   collapse.

3. **GEO-8a vs GEO-11 don't bleed.** Correlation >0.7 across 5 runs
   means the split was unnecessary and we should re-merge.

4. **GEO-6 cross-page diversity sharpens.** Run 3 pages (botoks, kwas
   hialuronowy, mezoterapia). Strengthened #4 must distinguish "3 pages
   × 4 distinct sub-queries from 12-node tree" (5) from "3 pages ×
   same 4 sub-queries" (1).

5. **Rubric-hash invalidation fires.** First post-landing run shows
   prior holdout scores as stale; frontier recompute produces clean
   baseline. If invalidation doesn't fire, it's a `score_holdout.py`
   bug.

If failure modes 1 or 2 surface, the rubric is ahead of the substrate
— substrate fix takes precedence over relaxing rubric. If 3–5 fire,
revise rubric in a Phase D pass after evidence accumulates.
