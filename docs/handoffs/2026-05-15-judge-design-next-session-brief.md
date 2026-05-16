---
date: 2026-05-15
type: next-session brief (judge-design)
status: open for next dedicated session
supersedes: none (continues 2026-05-15-judge-design-phase4-synthesis.md, which is now historical context)
---

# Judge design — what the NEXT session should do (and what this session got wrong)

## TL;DR

The current judges (`src/evaluation/rubrics.py` at HEAD `c76f051`) ARE THE PHASE-1-REVERTED STATE — the empirically-working human-refined `204e9a6` prose plus X-9 plus substrate fixes. Phase 4 prose was rolled back because it had a feature-checking pathology.

Next session does the work this session kept failing to do: **define an optimal output per workflow first; design judges that test for achievement of that output; don't tell the judge what frameworks/features to look for.**

**Full scope (per JR direction 2026-05-16):** ALL workflows in scope, not just one. GEO + CI + MON + SB + MA + X + LI + site_engine (8 workflows). Start with one lane as a proof-of-format to validate the approach, then propagate. **Plus** ONE shared agentic-LLM-judge methodology research pass (2026 cutting-edge) — separate from the May 15 methodology research, which was about single-shot judging.

## What this session did right

1. **Phase 1 surgical restoration (commit `f1d2599`)** — correctly reverted the 2026-05-13 σ-widening prose (commit `ca4a256`) back to `204e9a6` baseline. Kept X-9 (deterministic algorithmic-citizenship). Kept substrate fixes (axis-collapse, rate-limit promotion, per-criterion feedback, prompt nudges, grace-mode strict). This was the right move.

2. **Phase 2 + 3 research deliverables remain valid as INPUTS for next session:**
   - `docs/research/2026-05-15-judges-domain-geo.md` — Aggarwal KDD 2024, Volpini, Shepard, Profound, Ahrefs, Yext, Kalicube, Skywork Perplexity (named exemplars + frameworks)
   - `docs/research/2026-05-15-judges-domain-competitive.md` — Helmer 7 Powers, Porter Five Forces, Roger Martin Playing to Win, April Dunford, Andy Raskin, Christensen, Grove, Heuer & Pherson, BCG matrix, McKinsey war-games, CB Insights teardowns
   - `docs/research/2026-05-15-judges-domain-monitoring.md` — Cision React Score, Coombs SCCT, Benoit image-restoration, Edelman Trust Barometer ethics/competence decomposition, Sandman Risk = Hazard + Outrage, AMEC framework, Barcelona Principles, FAA AD format, PDB precedent, Dezenhall Glass Jaw
   - `docs/research/2026-05-15-judges-domain-storyboard.md` — MrBeast handbook, Pixar 22 rules, Save the Cat, Casey Neistat, Johnny Harris/Vox, Hormozi, Tom Scott
   - `docs/research/2026-05-15-judges-methodology.md` — Zheng MT-Bench, Liusie pairwise, Wang TrustJudge, Verga PoLL, Hopkins calibration, Pan ICRH, Zhang Evolution-without-Oracle

   These are reference material, not judge prose. Use them to inform optimal-output specs, not to embed in rubrics.

## What this session got wrong (Phase 4, reverted)

**Phase 4 prose (commit `698e658`, reverted in `f1d2599` HEAD) had a feature-checking pathology:**

- CI-4 told the judge "look for a Helmer power name + Benefit + Barrier explanation." A brief can name-drop "Process Power" and slot-fill the format without doing real analysis.
- MON-4 told the judge "look for FAA AD format: owner + compliance time + consequence." A digest can mechanically fill those slots regardless of whether the action is right.
- GEO-2 told the judge "look for Aggarwal's three methods: quotes + stats + citations at density." A page can cram three citations / stats / quotes per section regardless of whether they support a real argument.

**The Goodhart trap is automatic:** because judges drive workflow scripts, the workflows would have evolved to produce surface-feature compliance — Helmer-power-name-droppers, FAA-format-slot-fillers, citation-stuffers. Locking in a generation of variants optimized for feature markers instead of output quality.

Surface compliance + shit content = high score. That's exactly the failure JR has been pointing at across multiple sessions.

**Common pattern across all the wrong rounds:**
- Round 1 (J1-J4, commit `2ce99bb` 2026-05-08): σ-widening targets, anti-gaming clauses. Wrong.
- Round 2 (v2 spec + audit, commit `ca4a256` 2026-05-13): tighter contract-prose for variance widening. Wrong.
- Round 3 (Phase 4, commit `698e658` 2026-05-15): feature-checking against named frameworks. Wrong.

Three different surface manifestations of the same underlying error: writing rubrics that specify what to LOOK FOR instead of what to ACHIEVE.

## What the next session should do

### Step 0 — Agentic-LLM-judge methodology research (one shared pass, parallel to Step 1)

Dispatch ONE research agent to survey 2026-cutting-edge agentic LLM-as-judge practices. This is distinct from the May 15 methodology research (which covered single-shot pointwise/pairwise judging). The framing here is **agentic** — judges that can:
- Use tools during evaluation (retrieval, search, code exec, structured queries)
- Multi-step reasoning before scoring (plan → gather → reason → score)
- Self-refine / multi-agent debate
- Verify with code execution where the artifact has verifiable claims
- Use rubric-internal sub-agents (e.g., a "freshness checker" sub-agent for GEO)
- Constitutional / RLAIF-style judge training vs prompt-only
- Process supervision / step-level reward vs outcome-only

Sources to start from (find more):
- Anthropic's published agentic-eval work + Claude Sonnet 4.6/4.7 capability notes
- OpenAI Evals updates 2025-2026
- LMSYS Arena evolution (judge-the-judge work)
- Recent arxiv 2502-2606 on tool-using judges, agentic eval, judge agents
- DeepMind AlphaEvolve / FunSearch methodology updates
- "Judge agent" papers — multi-step judges with retrieval
- Hugging Face evaluate-judge agents

Deliverable: `docs/research/2026-05-16-agentic-judges-methodology.md`. ~2500 words. **Recommendation** on whether our judges should be upgraded from single-shot prompts to multi-step agentic judges (tool use, sub-agents, verification steps).

This research runs PARALLEL to Step 1 — no dependency. Cheaper to dispatch as one background agent than block on it.

### Step 1 — Per workflow, define what an OPTIMAL OUTPUT looks like (ALL 8 workflows)

For each workflow, write a spec that answers:

| Workflow | Reader | Output artifact |
|---|---|---|
| **GEO** | AI search engine + human researching a topic | Optimized landing-page content |
| **Competitive (CI)** | Strategic decision-maker (CEO / Head of Strategy / Corp Dev) | Competitive intelligence brief |
| **Monitoring (MON)** | Senior comms director / PR lead | Weekly brand-monitoring digest |
| **Storyboard (SB)** | Creator (MrBeast-style operator) preparing to shoot | Short-form video story plan |
| **Marketing Audit (MA)** | Founder / CMO of in-scope client | Marketing audit + remediation roadmap |
| **X Engine** | X (Twitter) audience + algorithm | X post drafts |
| **LinkedIn Engine (LI)** | LinkedIn audience (professional / B2B) | LinkedIn post drafts |
| **Site Engine** | Web visitor + AI search engine | Site landing-page surfaces |

For each workflow's spec, answer:

1. **Who is the reader?** Be specific. Not "marketers" — "a Series-B comms director at 9am Monday with 5 minutes before their leadership briefing."
2. **What does success look like for that reader?** Not "what frameworks are cited" — what does the reader DO differently after consuming the output? What decision do they make / action do they take / belief do they update?
3. **What does failure look like?** Not "missing framework X" — "the reader finished and didn't know what to do" / "the digest is information without intelligence" / "the page would be ignored by AI engines and forgotten by humans."
4. **What's the difference between a competent output and a world-class output?** Concrete examples of each, ideally drawn from real-world exemplars (named brands, named publications, named consultants whose work you'd recognize).
5. **Adversarial check: what does Goodhart failure look like?** Imagine a workflow optimized hard against this rubric for 50 generations — what surface-feature collapse mode does it have? Name it now so we can write criteria that resist it.

This is the work — slow, conceptual, requires JR's product judgment. Don't outsource to AI agents that will pattern-match to "what frameworks should we mention."

**Starting order recommendation:** start with ONE workflow as proof-of-format. JR's earlier priority signal was competitive or monitoring — recommend competitive (most generic strategy-consulting overlap, easiest to test the framing against a known-good real-world brief). Once spec format is validated on one lane, replicate across the other 7.

### Step 2 — Per criterion, design questions that test for ACHIEVEMENT

For each output dimension, the judge's question is "did the output achieve THIS effect for THIS reader" — not "did the output mention X / follow format Y / cite source Z."

Examples of the right framing:

**Competitive brief — bad (Phase 4):**
> Does the brief identify a Helmer power (Scale / Network / Counter-Positioning / Switching Costs / Branding / Cornered Resource / Process Power) AND apply both halves of the Benefit + Barrier test?

**Competitive brief — right framing:**
> If a strategic decision-maker reads this brief, do they finish with enough clarity to commit to a posture (attack / defend / flank / cooperate / ignore) on a specific competitive threat — including knowing what they'd give up by committing? If they slept on it and re-read tomorrow, would they make the same call or have second thoughts about the analysis?

The framework knowledge (Helmer, Porter, Martin) is the JUDGE'S reasoning toolkit, not a checklist embedded in the rubric.

**Monitoring digest — bad (Phase 4):**
> Do action items follow FAA Airworthiness Directive structure: (a) specific named owner, (b) compliance time, (c) consequence?

**Monitoring digest — right framing:**
> If a senior comms director reads this on Monday morning at 8:55am before their 9am leadership call, do they know what they personally need to do this week and what gets worse if they don't? Would they later regret not acting on something this digest surfaced — or alternatively, would they have wasted their time chasing noise this digest flagged as crisis?

### Step 3 — Per criterion, the rubric prose is short

The methodology research was right that extreme-only anchors work. The PHASE 4 prose was wrong to bloat to 250-400 words per criterion just to embed framework references. A good rubric criterion is:

- One question (what does success look like)
- Two anchors: score 0 (what failure achieves) + score 1 (what success achieves) — outcome-based, not feature-based
- Optional: a brief reasoning prompt for the judge ("think about whether a real comms director would actually find this useful")

Total ~80-150 words per criterion. Compare to Phase 4's 250-400.

### Step 4 — Synthesize: Step 0 (agentic methodology) × Step 1 (per-workflow specs)

After both Step 0 research returns and Step 1 specs exist for the 8 workflows, synthesize:

- Does the methodology research suggest some judges should be **agentic / multi-step** (e.g., GEO judge that retrieves real AI-engine citation patterns; site_engine judge that runs the page in a browser; MA judge that pulls live SEMrush data) vs **single-shot prompt** (e.g., SB judge that just reads the story plan)?
- Which lanes benefit most from tool-using judges?
- Which lanes are fine with the current single-shot pattern?
- Does the agentic-judge research surface failure modes we should design against?

This is where the May 15 methodology research (single-shot judges: pairwise vs pointwise, PoLL panel, calibration) and the new agentic methodology research come together.

### Step 5 — Use methodology pieces (pairwise gate, PoLL panel, calibration, agentic upgrades) only AFTER the criteria specs are right

The methodology improvements (pairwise gate, Gemini Flash third judge, calibration set, agentic judge upgrades) are still on the table for FUTURE work. But they don't fix bad criteria — they help good criteria score more reliably. Get the criteria right first.

## What to do with this session's research deliverables

The 5 research documents under `docs/research/2026-05-15-judges-*.md` are NOT prose templates. They are reference material. Next session should:

- Read them as background on what's been written about each domain
- Use them to INFORM JR's optimal-output specs (Step 1) — e.g., "Cision's React Score is one published model for severity tiering; do we like its two-axis structure or want something different?"
- NOT embed framework names verbatim into rubric prose

## What NOT to do next session

Repeating these from the parent reset plan (still applies):

- **No σ-widening** as design target. Variance is downstream, not a goal.
- **No anti-gaming clauses** as abstract design moves.
- **No calibration scripts.** Noise floor is inherent per `2ce99bb`.
- **No prose work without literature backing.** But ALSO — no prose work that name-drops the literature.
- **No feature-checking.** No "does the brief mention X." Outcome-evaluation only.
- **No "smoke testing the prose."** That's variance-adjacent measure-and-tune.
- **No variant-side calibration loops.**
- **No partial scope.** All 8 workflows are in scope. Don't ship rubric prose for one lane while others are still stale.
- **No skipping Step 1 for any lane.** Even if a lane "feels solved" (e.g., storyboard's existing prose was deemed creator-strategist-grounded by the May 15 pre-investigation) — write the explicit reader / success / failure / examples spec anyway. The act of writing it surfaces gaps; trusting "it's already good" was part of how we got here.

## Current state at end of this session

- HEAD: `c76f051` revert (Phase 1 state, post-prose-rollback)
- 53 rubrics: GEO 8 / CI 8 / MON 8 / SB 8 / MA 8 / X 7 (incl. X-9) / LI 6
- RUBRIC_VERSION: `58549a2b9c40`
- 29/29 lane_registry tests pass
- Phase 4 prose work is reverted but commits `698e658` and `5a667c8` remain in git history for reference

## Resume prompt for next session

```
Resume judge-design work from `docs/handoffs/2026-05-15-judge-design-next-session-brief.md`.

State: judges are at Phase 1 baseline (commit c76f051). 2026-05-15 Phase 4 prose
rewrite was reverted because it had a feature-checking pathology JR has been
calling out across multiple sessions.

CRITICAL — read these in order BEFORE doing anything:
1. This brief (next-session brief, updated 2026-05-16 to expand scope to all 8
   workflows + add agentic-judge methodology research pass)
2. The reset plan: docs/handoffs/2026-05-15-judge-design-reset-and-plan.md
3. The Phase 4 synthesis: docs/handoffs/2026-05-15-judge-design-phase4-synthesis.md
   (historical — shows what didn't work and why)
4. The 5 research docs under docs/research/2026-05-15-judges-*.md as reference
   material only, not as prose templates

FULL SCOPE: All 8 workflows in scope — GEO + CI + MON + SB + MA + X + LI +
site_engine. Start with one (recommend CI) as a proof-of-format, then propagate.

PARALLEL DISPATCH on session start: ONE background research agent for
agentic-LLM-judge methodology (2026 cutting-edge — tool-using judges, multi-step
reasoning, verification steps, sub-agents, multi-agent debate). Distinct from
May 15 single-shot judge methodology research. Deliverable:
docs/research/2026-05-16-agentic-judges-methodology.md.

Next action AFTER dispatching the agentic-judge agent: do NOT write rubric
prose. Work with JR to write optimal-output specs per workflow — what does a
world-class output achieve for its reader? Each workflow gets:
- Reader spec (who, when, with what context, what do they do after?)
- Success spec (what does world-class look like, with named real-world exemplars)
- Failure spec (what does mediocre/Goodhart-collapsed look like)
- Adversarial check (if a workflow optimised hard against this for 50 generations,
  what surface-feature collapse emerges? Name it now.)
- 5-8 criteria draft as OUTCOME questions, not feature checks

After Step 0 (agentic methodology research) + Step 1 (specs for all 8 workflows)
both complete: synthesize. Some lanes may want agentic / multi-step / tool-using
judges; others may stay single-shot. Decide per lane.

Only after specs + agentic-vs-single-shot decisions exist: design rubric prose
with score-0 / score-1 behavioral anchors that test for achievement of the
specs. Keep criteria prose under ~150 words.

If you find yourself reaching for framework names to embed in rubric prose,
σ measurement, smoke tests, calibration scripts, or "feels good let's ship" —
STOP. That's the wrong direction. Re-read this brief.
```

## Memory pointer to update

After next session does Step 0 + Step 1 for the first workflow, update memory
entry to reflect progress. Until then, current memory at
`~/.claude/projects/.../memory/project-judge-design-deep-research-2026-05-12.md`
reflects "Phase 4 reverted; next session: optimal-output-first across all 8
workflows + agentic methodology research."

Also note: the 2026-05-16 compact-handoff memory entry references commit
`fc99d64` for the live rubric — that's a typo. The actual HEAD at end of this
session is `c76f051`. Fix on first memory edit next session.
