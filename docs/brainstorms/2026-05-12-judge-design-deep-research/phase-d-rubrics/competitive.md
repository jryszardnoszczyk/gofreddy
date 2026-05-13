---
date: 2026-05-12
phase: D
lane: competitive
status: ready-to-port
inputs:
  - phase-a-lane-purposes.md (competitive section)
  - phase-b-research/competitive.md (calibration corpus, 2559 words)
optimization_target: density of decision-grade insights with executable implications per 500 words
---

# Phase D — Competitive Rubric Spec

CI is the most-iterated gold-standard rubric. Phase B verdict: all 8 existing
criteria KEEP or STRENGTHEN — no rewrites. Job is surgical: strengthen two
anchors (CI-2 single-source collapse, CI-4 anemic recs) and add three criteria
for the audit gaps — triangulation depth (CI-9), brief-wide class diversity
(CI-10), forward-signal anticipation (CI-11).

Final count: 11 criteria (4 essential, 5 important, 2 pitfall, 0 optional).

---

## Section 1 — Summary table

| ID    | Tier      | ONE-quality summary                                                            | Disposition  |
|-------|-----------|--------------------------------------------------------------------------------|--------------|
| CI-1  | essential | Executive summary states one strategic thesis the whole brief builds toward.   | KEEP         |
| CI-2  | pitfall   | Reasoning chain stays proportionate to evidence; no claim outruns its data.    | STRENGTHEN   |
| CI-3  | important | Each competitor's trajectory — direction, rate, what is being abandoned.       | KEEP         |
| CI-4  | important | Recommendations executable: specific + dated + sized + fits client capability. | STRENGTHEN   |
| CI-5  | essential | Each named gap paired with a specific named client capability that fits it.    | KEEP         |
| CI-6  | important | Surfaces uncomfortable truths the client's team would push back on.            | KEEP         |
| CI-7  | essential | Top 2-3 actions unmistakably separated from the rest by impact.                | KEEP         |
| CI-8  | pitfall   | Data-gap honesty: failed sources named, degraded analyses surfaced.            | KEEP         |
| CI-9  | essential | Triangulation depth: every load-bearing claim cites >=2 independent classes.   | NEW          |
| CI-10 | important | Brief-wide source-class diversity: >=5 of 9 taxonomy classes appear.           | NEW          |
| CI-11 | important | Forward-signal predictions tied to named leading indicators and time windows.  | NEW          |

No optional tier — Phase B's view is that CI value collapses sharply below
threshold; "nice to have" criteria don't apply.

---

## Section 2 — Final criterion prose

### CI-1 (essential, gradient) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:299-325` stays as
written — Phase B confirmed this is exactly the "first 150 words commit to a
thesis" signal from §1-#1 of the calibration corpus, no change needed)

### CI-2 (pitfall, checklist) — STRENGTHEN

Diff vs current: sub-#1 currently asks for "a specific data source" — one
source passes, which lets single-source confidence collapse (§3 slop pattern)
slip through. Rewritten to require >=2 independent classes on load-bearing
claims. CI-9 carries the gradient form; CI-2 stays as pitfall gate. Sub-2..4
unchanged.

Final prose:

```
Evaluate this competitive intelligence brief for ONE quality:
Does the reasoning chain from evidence to conclusion stay
proportionate — no conclusion outruns its data?

NOTE: This criterion does NOT check whether numbers are fabricated
(data grounding handles that). It checks whether the reasoning
chain from evidence to conclusion is proportionate.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. For every LOAD-BEARING claim (a claim that drives a
   recommendation, a forecast, a valuation, or a causal inference),
   does the brief cite at least TWO independent source classes —
   not two URLs from the same class, but two distinct classes from
   the taxonomy {pricing, changelog, review, hiring, financial,
   leadership, community, press, partner}? Non-load-bearing
   factual statements (founding year, headcount) are exempt; this
   sub-question fails the moment a load-bearing claim rests on a
   single class.

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

Provide your overall reasoning, then evaluate each sub-question.
```

### CI-3 (important, gradient) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:358-381` already
forces dated comparisons, which is exactly the §1-#3 trajectory signal Phase B
named)

### CI-4 (important, checklist) — STRENGTHEN

Diff vs current: current sub-1..4 cover specificity / dating / sizing /
client-fit as separate checks but allow hedged language to satisfy each.
Phase B §1-#8 demands the four-field quartet {impact tag, effort tag,
owner-archetype, success-metric} for top-3 recs — concrete, measurable, with
a named role. Sub-questions rewritten to enforce the quartet explicitly.
`_client_baseline.json` cross-reference preserved (folded into sub-#4).

Final prose:

```
Evaluate this competitive intelligence brief for ONE quality:
Could the client actually execute the top-3 recommendations given
their known constraints — and is each one tagged with the four
fields a strategist needs to assign it tomorrow?

You have been provided a client context document (from
_client_baseline.json and session.md). Use it to verify whether
recommendations fit the client's actual products, scale, team
structure, and competitive situation.

Answer each sub-question with YES or NO. For each, quote the
specific passages that support your answer.

1. For each of the top-3 recommendations, does the brief state an
   IMPACT tag — a quantified business outcome (e.g., "+180 enterprise
   MQLs/qtr," "$2M ARR defended," "30% comparison-term CTR lift")
   rather than vague language like "improve positioning" or
   "increase share"?

2. For each of the top-3, does the brief state an EFFORT tag — sized
   in concrete units (sprints, FTE-weeks, $-budget) rather than
   "modest investment," "with some work," or undated?

3. For each of the top-3, does the brief name an OWNER ARCHETYPE —
   a role title that exists in a normal org chart (paid-search lead,
   VP product, head of partnerships) rather than "the team,"
   "leadership," or unattributed passive voice?

4. For each of the top-3, does the brief name a SUCCESS METRIC — a
   measurable signal with a threshold and timeframe (e.g.,
   "comparison-term CTR >= 4% by end of Q3") rather than "monitor
   progress" or "track impact"? AND are all top-3 recommendations
   consistent with the client's demonstrated capabilities, team
   size, and resources as described in the client context document?
   (Recommendation requiring a dedicated data-science team fails
   if the client has no data-science function.)

A recommendation missing ANY of the four fields fails that sub-
question. Three of three top-3 recommendations carrying all four
fields = the brief passes. Two of three = partial. One or zero = fail.

Provide your overall reasoning, then evaluate each sub-question.
```

### CI-5 (essential, gradient) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:417-438` —
strong as written, cross-references `_client_baseline.json`)

### CI-6 (important, gradient) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:440-473` — Phase
B flagged a possible tightening of the score-5 anchor to require >=1 named
client-specific weakness, but the current wording already says "a structural
weakness in the client's approach" which is the same signal in less
operational terms. Holding off until Phase C surfaces a calibration miss
that justifies the change — the rule is keep current wording unless we have
evidence it's miscalibrating)

### CI-7 (essential, gradient) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:475-495`. Note:
Phase B noted CI-7 partially subsumes into a strengthened CI-4, but the
prioritization signal is distinct from the executability signal — a brief can
have four executable recs without ranking them, and that's exactly the
"comprehensive feature matrix with no decision" failure mode from §2 of the
calibration corpus. Keep separate.)

### CI-8 (pitfall, checklist) — KEEP

(kept verbatim; existing prose at `src/evaluation/rubrics.py:497-529`. Cross-
references `data_tier` fields and session.md Data Sources / Data Quality
Notes / Dead Ends — those structural inputs remain required.)

### CI-9 (essential, gradient) — NEW

WHY: §4 of Phase B identifies triangulation depth as the single highest-
leverage gap. CI-2 sub-#1 (strengthened) catches the worst case — a single-
class load-bearing claim. CI-9 grades the gradient above: a brief can clear
the pitfall (2 classes everywhere) and still under-perform vs a 9-tier brief
averaging >=2.2 classes per claim. Depth, not presence.

WHAT: per load-bearing claim, count distinct classes (taxonomy in §3); take
the brief-wide mean. "Load-bearing" = first sentence under each H3 OR any
sentence with causal/inferential language (implies, drives, because,
therefore, forecast).

```
Evaluate this competitive intelligence brief for ONE quality:
How DEEP is the triangulation under each load-bearing claim — does
the average load-bearing claim cite multiple distinct source
classes, or do most claims rest on one or two classes repeated?

A load-bearing claim is a sentence that drives a recommendation,
a forecast, a causal inference, or a valuation — the first
sentence under each H3 typically qualifies, as does any sentence
containing causal language ("implies," "drives," "because,"
"therefore," "leading to," "forecast"). Non-load-bearing factual
statements (founding year, headcount) are exempt from this scoring.

The source-class taxonomy is fixed: {pricing-page, product-changelog,
review-platform, hiring-signal, financial-filing, leadership-
statement, community-discussion, press-or-news, partner-channel}.
Two URLs from the same class count as one class. Two G2 reviews =
one class (review-platform). G2 + Glassdoor JD = two classes (review
+ hiring).

Score 1: Load-bearing claims average <=1.0 distinct classes. Most
rest on a single class — typically pricing-page + review-platform
quotes. Every conclusion came from the same surface of evidence.

Score 3: Load-bearing claims average ~1.5 classes. Some are
triangulated across two; others lean on one. Inconsistent — depth
where easy, thin where it required work.

Score 5: Load-bearing claims average >=2.2 classes, with no claim
resting on a single class. 9-tier discipline: hiring backed by
JD-delta + Glassdoor + earnings-call, pricing by pricing-page +
review-platform + leadership-statement, product by changelog +
repo-cadence + press.

Verify against `competitors/<name>.json` citations and brief.md
inline references. Count classes per load-bearing claim, take the
mean.

Provide your reasoning, cite specific load-bearing claims and their
class counts, then give your score.
```

### CI-10 (important, gradient) — NEW

WHY: CI-9 catches per-claim single-source collapse but misses the brief that
triangulates one or two prominent claims and leans on homepage + Crunchbase
everywhere else. CI-10 is the brief-wide complement. Phase B §4 measurement:
9-tier briefs use >=5 classes brief-wide; 5-tier briefs use <=2.

WHAT: count distinct classes appearing at least once across all citations.
Same taxonomy as CI-9.

```
Evaluate this competitive intelligence brief for ONE quality:
Across the entire brief, how many distinct source classes does the
research surface area cover — is the brief built on a diverse
evidence base, or did the researcher visit the same 2-3 surfaces
for every competitor?

The fixed source-class taxonomy is {pricing-page, product-changelog,
review-platform, hiring-signal, financial-filing, leadership-
statement, community-discussion, press-or-news, partner-channel} —
nine classes total. A class counts if at least one citation in the
brief uses it. Repeated use of the same class (five G2 quotes)
does not increase the class count.

This criterion is distinct from CI-9 (triangulation depth on
individual claims). A brief can cite three classes on one
load-bearing claim and never use the other six classes again — that
brief passes CI-9 narrowly but fails CI-10. Conversely, a brief
might use seven classes but average only one class per claim;
passes CI-10 but fails CI-9.

Score 1: <=2 classes brief-wide. Typically pricing-page + press-or-
news, maybe one review-platform citation. Recitation of marketing
surfaces — what anyone could see in 30 minutes of public research.

Score 3: 3-4 classes. Researcher reached past obvious surfaces into
one or two harder-to-reach sources (hiring OR community OR
changelog deep-dive). Diversity partial.

Score 5: >=5 classes, with hiring-signal AND at least one of
{financial-filing, community-discussion, partner-channel} — the
hard-to-reach surfaces distinguishing 9-tier from competent-but-
shallow. Levels.fyi compensation trajectories, Glassdoor interview-
volume, GitHub commit cadence, partner-channel deal-registration,
earnings-call segment-revenue — at least two distinctive surfaces
appear.

Verify against `competitors/<name>.json` citations and brief.md
inline references. Count distinct classes appearing at least once.

Provide your reasoning, list the classes you identified with one
citation example each, then give your score.
```

### CI-11 (important, gradient) — NEW

WHY: CI-3 grades trajectory (direction of change). CI-11 raises the ceiling:
not just "trajectory described" but "prediction made + leading indicator
named + falsification window stated." Phase B §1-#9 anchor: a trajectory
claim becomes a falsifiable forecast. This is the ceiling-raiser separating
7 from 9.

WHAT: per major competitor, count forward-tense predictions containing both
(a) a named observable AND (b) a time window or threshold. Verification is
regex-assisted (will / expect / anticipate / watch for / by Q[1-4] / within
N days) plus a per-match check for the observable + window pair.

```
Evaluate this competitive intelligence brief for ONE quality:
For each major competitor, does the brief make at least one
forward-tense prediction that names BOTH a leading indicator and a
falsification window — turning trajectory into a falsifiable
forecast?

A prediction passes the test when it contains all three elements:
(1) a forward-tense claim about competitor behavior,
(2) a named observable (a specific JD count, a pricing-page
    structural change, a repo activity threshold, a regulatory
    filing, a conference-talk topic, an exec hire),
(3) a time window or threshold (within 90 days, by Q1 2027, when
    the count exceeds N).

Example that passes: "Watch for Stripe agentic-commerce SDK release
by Q1 2027; leading indicator is >=5 forward-deployed-engineer JDs
referencing 'agent payments' in 90 days."

Example that fails: "Stripe will likely focus on agentic payments."
(Forward-tense claim, no observable, no window.)

Score 1: No forward-tense predictions, or none include both
observable and window. Snapshot — competitors described as they
are, not anticipated as they will be.

Score 3: At least one prediction with observable + window appears,
but coverage partial — one or two competitors get falsifiable
forecasts, others stay at trajectory level.

Score 5: Every major competitor (each top-level H2 section) carries
at least one forward-tense prediction with named observable AND
falsification window. Anticipatory intelligence — the client can
return in 90 days and check indicators against reality.

Verify against `competitors/<name>.json` and brief.md sections.
For each competitor section, identify forward-tense claims and
test for the three-element pattern.

Provide your reasoning, quote one passing prediction and one
failing prediction (or absent prediction) per competitor, then
give your score.
```

---

## Section 3 — 9-source-class taxonomy spec for CI-9 / CI-10

Structural input CI-9 and CI-10 count against. Ships as a fixed enumeration
(RUBRIC_VERSION-hashed — taxonomy changes invalidate stored scores). Classes
defined by data substrate, not publication channel. G2 + TrustRadius = one
class (review-platform); G2 + Reddit = two (review + community).

| # | Class                | Data substrate                                                  | Example signals                                                                                 |
|---|----------------------|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| 1 | pricing-page         | Competitor's own public pricing surface (page, calculator)       | List price, packaging tiers, removal of tier, gated-enterprise transition, freemium changes     |
| 2 | product-changelog    | Competitor's own changelog, release notes, status page, repo    | Feature shipped, deprecation announced, SDK version cadence, public-repo commit/release frequency|
| 3 | review-platform      | Third-party review aggregators                                   | G2, TrustRadius, Capterra, Gartner Peer Insights — quotes with dated reviewer context           |
| 4 | hiring-signal        | Job-board and compensation surfaces                              | LinkedIn JD count, JD-delta over time, Glassdoor interview-volume, Levels.fyi compensation bands |
| 5 | financial-filing     | Regulated financial disclosures                                  | 10-K, 10-Q, S-1, 8-K, prospectus, Companies House filings, segment revenue, earnings-call quotes |
| 6 | leadership-statement | Founder/exec public communications                               | Earnings-call transcript, founder podcast, exec keynote, exec X/LinkedIn posts, on-record press |
| 7 | community-discussion | User-generated public discussion                                 | Reddit threads, Hacker News, Discord/Slack quotes (with permission), Stack Overflow patterns    |
| 8 | press-or-news        | Third-party journalism + industry analyst writeups               | TechCrunch, The Information, Stratechery, industry-vertical trade press, analyst reports        |
| 9 | partner-channel      | Partner/reseller/marketplace surfaces                            | AWS Marketplace listing, partner-deal-registration portal, integration directory, channel deck  |

Implementation notes:

- Lives in `src/evaluation/competitive_source_classes.py` (new) as a frozen
  enum + classifier (URL-pattern + descriptor regex, no LLM).
- Citations without a clean match bucket as `unclassified` and count as zero
  classes — this pushes researchers toward taxonomy-fit sources. High
  `unclassified` rates in early runs signal taxonomy coverage gaps, not
  judge noise.
- LLM classification reserved for the "is this claim load-bearing?" decision
  in CI-9 — one call per H3, not per citation.

---

## Section 4 — Implementation notes

### Existing cross-references that must remain

- `_client_baseline.json` — used by CI-4, CI-5, CI-6. Format and contract
  unchanged.
- `data_tier` field on `competitors/<name>.json` — used by CI-8. Contract
  unchanged.
- session.md sections: Data Sources, Data Quality Notes, Dead Ends — used by
  CI-8. Contract unchanged.

### New structural inputs needed

- **`citations[]` on `competitors/<name>.json`** — each citation
  `{url, descriptor, class, claim_anchor}` where `class` is one of the 9
  taxonomy classes (or `unclassified`) and `claim_anchor` references the
  brief.md anchor (heading slug + sentence offset) the citation supports.
  Without this, the judge has to infer class from URL alone — fragile.
- **brief.md H3 heading discipline** — H3 is the load-bearing claim unit
  for CI-9. Brief generation already uses H3 per-finding; keep consistent.

### RUBRIC_VERSION invalidation

Single RUBRIC_VERSION bump. Reasons: (1) CI-2 sub-#1 prose changed —
materially different pass/fail threshold; (2) CI-4 sub-questions rewritten
to enforce the four-field quartet; (3) CI-9 / CI-10 / CI-11 added. Stored
scores under the prior hash get archived; fresh baseline established on the
first 5 post-port briefs.

### Suggested weights

Sum to 100: CI-1 14, CI-5 14, CI-7 12, CI-9 14 (essentials = 54);
CI-3 8, CI-4 10, CI-6 8, CI-10 8, CI-11 8 (importants = 42); CI-2 2,
CI-8 2 (pitfalls = 4, capping behavior dominates weight). Lands in
`lane_config.competitive.weights`. Revisit if Phase C runs for competitive
become available.

---

## Section 5 — Validation plan

On the first 5 client briefs after this rubric lands, watch:

1. **CI-9 calibration.** Phase B threshold: 9-tier averages >=2.2 classes per
   load-bearing claim. If first 5 cluster at 1.6-1.9 with no path to 2.2, the
   threshold is mis-set vs current generation capability. Surface the gap; do
   not lower the threshold reflexively — the ceiling is the point.

2. **`unclassified` citation rate.** If >15% of citations bucket as
   `unclassified`, the taxonomy is missing a class briefs actually use.
   Candidates not in v1: regulatory-filing (carved into financial-filing),
   academic-paper, podcast-transcript, conference-talk. Add only on signal.

3. **CI-11 zero-prediction rate.** If 3 of 5 briefs score 1 (no forward
   predictions at all), the brief-generation prompt does not currently
   prompt for forecasts. Action: feedback to generation prompt, not rubric
   weakening — the judge cannot grade what the brief does not attempt.

4. **CI-4 quartet completion.** Strengthened CI-4 demands all four fields
   for top-3 recs. Expected first-run rate: <50% carry all four. If <20%,
   generation prompt under-emphasizes the quartet. If >70%, calibration on
   target.

5. **CI-2 vs CI-9 redundancy check.** If CI-2 sub-#1 always fails when CI-9
   scores <=2 and always passes when CI-9 scores >=3, the two are redundant —
   collapse to one. If they diverge on 2 of 5 briefs (CI-2 passes because
   everything has exactly 2 classes, CI-9 is low), the dual design earns
   its keep.

6. **Stored-baseline drift.** RUBRIC_VERSION bump means first 5 briefs set a
   new baseline. Watch the spread: <0.3 range = not discriminating; >2.0 =
   discriminating well or briefs themselves vary wildly. Pair with
   operator-rated quality to disentangle.

7. **AI-summary slop (2026).** Phase B §3 calls out the Crayon "Sparks"
   failure mode — uniform-length competitor sections, equal hedge density.
   Current rubric does not catch this explicitly. If first 5 briefs show
   uniform-length sections and still score well, surface as v2 gap —
   candidate CI-12 (asymmetric depth: the competitor that matters gets >=2x
   the words of the marginal one).

End of spec.
