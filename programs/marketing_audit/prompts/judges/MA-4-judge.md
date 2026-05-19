Evaluate this comprehensive marketing audit on ONE outcome question:

Does the audit name the company's current stage with at least one
observable vertical-appropriate anchor, refuse to recommend best
practices that are wrong for the stage, AND integrate the Phase-0
9-meta-frame measurements into the diagnostic? Would the reader
finish the audit knowing why a generically-correct recommendation
was deliberately omitted?

Score 1 (yes) — Audit names the company's stage with at least one
observable anchor — ARR band (SaaS), retention cohort signal,
channel-fit signal, capacity utilization (local services), location
count, regulatory licensing state, contribution margin per cohort
(DTC), pipeline composition (regulated B2B), or other vertical-
specific stage signal. At least one recommendation is explicitly
refused or sequenced on stage grounds. The stage diagnostic
incorporates Phase-0 measurements from `phase0_meta.json` (the 9
meta-frames: traffic mix / channel-model fit / traffic trajectory /
growth-loops inventory / maturity tier / share-of-voice / geo mix /
north-star vs vanity / engagement-tier proxies); per-section
findings color by relevant Phase-0 frames where applicable; Phase-0
measurements that came back null surface as findings (gap-honesty),
NOT papered over.

Illustrative example — SaaS (do not optimize toward this exact
shape): "You are mid-traction (post-PMF, pre-scale) at $2.4M ARR
with 91% NRR, traffic-mix 62% organic / 18% direct / 12% paid / 8%
referral (Phase-0 traffic-mix), channel-model fit medium (self-
serve + outbound is the structural mismatch the audit names in
Axis 2). The instinct to hire a paid-acquisition manager is wrong
for this stage; the upstream constraint is sales-motion clarity,
and paid spend at current LTV:CAC of 1.8 will worsen unit
economics. Defer the ABM-tooling investment by two quarters until
the SDR motion stabilises. Phase-0 share-of-voice came back null
because no Profound/Peec instrumentation exists yet — surface as
finding in Axis 3, not papered over."

Score 0 (no) — Same playbook regardless of stage. Recommendations
include late-stage best practices (ABM tooling, full marketing-ops
stack, demand-gen programmes) without checking foundations. Audit
would land identically for a $500k-ARR and $20M-ARR company.
Phase-0 measurements ignored or papered over. Stage label
mechanically applied without observable anchor.

Score 0.5 (unknown) — Stage named but recommendations don't visibly
tailor to it, OR Phase-0 measurements partially integrated (some
axes color by Phase-0, others don't). Emit 0.5 + "unknown" + one
sentence on which recommendation is stage-mismatched or which
dimension is off.

Required reasoning (work through these 3 steps in your rationale):
1. Identify the company stage named + the observable vertical-
   appropriate anchor supporting it. Verify at least one
   recommendation is explicitly refused or sequenced on stage
   grounds.
2. Verify Phase-0 measurements integrated into the diagnostic
   (state-of-business opener pulls from `phase0_meta.json`; per-
   section findings color by Phase-0 frames; nulls surface as
   findings).
3. Emit verdict (0 / 0.5 / 1) + one-sentence justification.

Do not score: vocabulary used for stage labels, presence of stage-
map diagram, number of stages discussed, exact page count,
commissioning context (DROPPED in v3 as judge-imagined
classification — do not check whether the prescription's emphasis
matches a personnel / operational / strategic commissioning shape
the fixture does not state).
