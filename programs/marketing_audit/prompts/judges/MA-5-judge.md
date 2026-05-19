Evaluate this comprehensive marketing audit on ONE outcome question:

When the binding constraint is upstream of marketing (one of the 6
upstream classes: retention/PMF, ICP, positioning, pricing, sales
motion, marketing-internal), does the audit say so plainly — even
though saying so means the audit's own marketing recommendations
get smaller? Would the reader finish thinking "the bottleneck isn't
marketing" if that's what the evidence points at, AND are the
audit's marketing recommendations SEQUENCED behind the upstream fix
(explicitly deferred, paused, or scoped behind it) rather than
parallel-tracked alongside it? Does the audit treat positioning as
the load-bearing 6th upstream class, not as a marketing-internal
axis?

Score 1 (yes) — Where evidence in the audit suggests the constraint
is upstream — low retention / low PMF-survey scores (retention/PMF
class), ICP confusion ("how would you describe what we do"
responses cluster into 4+ different categories; win-loss interviews
surface "we thought you did X" as a recurring loss reason) (ICP
class), positioning–buyer-mental-model mismatch (category-of-one
collapses, competitive-alternatives unclear, category vocabulary
drifts) (positioning class — the 6th upstream class), pricing-
model misfit (value-metric mismatch, expansion <10% of new ARR)
(pricing class), sales-motion misalignment (MQL→SQL conversion
sub-median, AE ramp >9 months, pipeline coverage >4×) (sales motion
class) — the audit names it directly AND sequences marketing
recommendations behind the upstream fix. The audit is willing to
recommend pausing demand-gen spend, deferring channel
diversification, or running a PMF re-test / ICP re-anchor /
positioning re-anchor / pricing audit before scaling marketing. The
**6-class triage sequence** is walked in order — retention/PMF →
ICP → positioning → pricing → sales motion → marketing-internal —
stopping at the first binding constraint with evidence.

**Positioning treated as a load-bearing 6th upstream class.** When
positioning, ICP sharpness, category placement, customer-language
alignment, founder-narrative coherence, or counter-positioning are
the binding constraint, the audit names it directly AND sequences
marketing recommendations behind the positioning fix. Positioning
is NOT a marketing-internal channel-axis to be optimized; it is
upstream of everything downstream.

**Gap honesty integrated.** `gap_flagged` rubrics from per-agent
`rubric_coverage` maps must surface in `gap_report.md`; Phase-0
nulls and provider-blocked lenses are findings, not synthesis
material. Missing-data findings appear in `findings.md`, NOT
papered over with speculation. Invented signals — missing data
papered over with fabricated specifics — score 0.

Illustrative example — SaaS (do not optimize toward this exact
shape): "Your monthly churn is 6.4%; LTV at this churn rate means
CAC payback cannot work below an ACV 4× your current. The
constraint is retention, not acquisition. Pause the SEO investment
and the paid-LinkedIn pilot; the marketing budget should fund three
Wynter-style messaging tests to diagnose whether the issue is
positioning or product fit. Once churn closes to <3.5%, re-evaluate
SEO investment in Q3. Marketing recommendations explicitly
sequenced behind the retention fix — Day 0–30 is Wynter tests +
retention diagnostic; Day 31–60 is positioning re-anchor if Wynter
reveals positioning gap; Day 61–90 is SEO and paid re-engaged only
if churn closes."

Score 0 (no) — At least one of: audit always recommends more
marketing despite evidence pointing upstream; upstream classes
named but treated as out-of-scope when evidence engages them;
upstream section slot-filled with no diagnostic conviction (generic
mention without engaging the specific evidence — mechanical
rotation through PMF / ICP / pricing); upstream constraint named
but marketing recommendations PARALLEL-TRACKED rather than
sequenced behind the upstream fix (the Goodhart-resistant slot-fill
form: founder reads, defaults to concrete marketing actions because
those aren't deferred); positioning treated as a marketing-internal
channel to be optimized rather than as a load-bearing upstream
class; invented-signals failure — missing data papered over with
fabricated specifics; provider-blocked lenses presented as honest
findings rather than honest gaps; `gap_flagged` rubrics not
surfaced in `gap_report.md`; audit with no "the bottleneck is
upstream of marketing" branch by default — implying marketing is
always the answer.

Score 0.5 (unknown) — Audit engages upstream evidence but the
artifact lacks enough detail to determine whether the upstream
naming is supported, OR the sequencing of marketing recommendations
behind the upstream fix is partial (some sequenced, some parallel).
Emit 0.5 + "unknown" + one sentence on what is missing.

Required reasoning (work through these 3 steps in your rationale):
1. Identify upstream signals present in the audit's evidence across
   the 6 upstream classes (retention/PMF cohorts; ICP divergence;
   positioning–buyer-mental-model mismatch; pricing-model misfit;
   sales-motion friction; marketing-internal). Verify positioning
   is treated as the 6th upstream class, not as marketing-internal.
   Determine whether the audit (i) confirms marketing IS the
   constraint with evidence on the merits, OR (ii) names an
   upstream constraint AND sequences marketing behind it.
2. If (ii), verify the sequencing is real — marketing
   recommendations explicitly deferred, paused, or scoped behind
   the upstream fix, NOT parallel-tracked alongside it. Verify gap
   honesty — `gap_flagged` rubrics surface in `gap_report.md`;
   Phase-0 nulls and provider-blocked lenses are findings, not
   papered-over invented signals.
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: number of upstream classes discussed, presence of
"upstream constraints" section header, length of the upstream
discussion, depth of upstream remediation guidance (audit names the
constraint; audit does not need to solve it — that's product's /
pricing's / sales's job).
