---
date: 2026-05-15
type: next-session brief (judge-design)
status: open for next dedicated session
supersedes: none (continues 2026-05-15-judge-design-phase4-synthesis.md, which is now historical context)
---

# Judge design — what the NEXT session should do (and what this session got wrong)

## TL;DR

The current judges (`src/evaluation/rubrics.py` HEAD = `f1d2599`) ARE THE PHASE-1-REVERTED STATE — the empirically-working human-refined `204e9a6` prose plus X-9 plus substrate fixes. Phase 4 prose was rolled back because it had a feature-checking pathology.

Next session does the work this session kept failing to do: **define an optimal output per workflow first; design judges that test for achievement of that output; don't tell the judge what frameworks/features to look for.**

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

### Step 1 — Per workflow, define what an OPTIMAL OUTPUT looks like

For each workflow (GEO, CI, MON, SB, MA, X, LI), write a spec that answers:

1. **Who is the reader?** (Comms director? Strategic decision-maker? Engineer? AI search engine? Viewer scrolling?)
2. **What does success look like for that reader?** Not "what frameworks are cited" — what does the reader DO differently after consuming the output?
3. **What does failure look like?** Not "missing framework X" — "the reader finished and didn't know what to do" / "the digest is information without intelligence" / "the page would be ignored by AI engines and forgotten by humans"
4. **What's the difference between a competent output and a world-class output?** Concrete examples of each, ideally drawn from real-world exemplars.

This is the work — slow, conceptual, requires JR's product judgment. Don't outsource to AI agents that will pattern-match to "what frameworks should we mention."

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

### Step 4 — Use methodology pieces (pairwise gate, PoLL panel, calibration) only AFTER the criteria specs are right

The methodology improvements (pairwise gate, Gemini Flash third judge, calibration set) are still on the table for FUTURE work. But they don't fix bad criteria — they help good criteria score more reliably. Get the criteria right first.

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

## Current state at end of this session

- HEAD: `f1d2599` revert (Phase 1 state, post-prose-rollback)
- 53 rubrics: GEO 8 / CI 8 / MON 8 / SB 8 / MA 8 / X 7 (incl. X-9) / LI 6
- RUBRIC_VERSION: `58549a2b9c40`
- 29/29 lane_registry tests pass
- Phase 4 prose work is reverted but commits `698e658` and `5a667c8` remain in git history for reference

## Resume prompt for next session

```
Resume judge-design work from `docs/handoffs/2026-05-15-judge-design-next-session-brief.md`.

State: judges are at Phase 1 baseline (commit f1d2599). 2026-05-15 Phase 4 prose
rewrite was reverted because it had a feature-checking pathology JR has been
calling out across multiple sessions.

CRITICAL — read these in order BEFORE doing anything:
1. This brief
2. The reset plan: docs/handoffs/2026-05-15-judge-design-reset-and-plan.md
3. The synthesis: docs/handoffs/2026-05-15-judge-design-phase4-synthesis.md
   (historical — shows what didn't work and why)
4. The 5 research docs under docs/research/2026-05-15-judges-*.md as reference
   material only, not as prose templates

Next action: do NOT write rubric prose. Work with JR to write optimal-output
specs per workflow — what does a world-class output achieve for its reader?
Start with one workflow (probably competitive or monitoring per JR's earlier
priority signal). One workflow per session at most. Each workflow gets:
- Reader spec (who is the reader? what do they do differently after?)
- Success spec (what does world-class look like, with examples)
- Failure spec (what does mediocre look like, with concrete failure modes)
- 5-8 criteria draft as OUTCOME questions, not feature checks

Only after all specs exist for the in-scope workflows: design rubric prose
with score-0 / score-1 behavioral anchors that test for achievement of the
specs. Keep criteria prose under ~150 words.

If you find yourself reaching for framework names to embed in rubric prose,
σ measurement, smoke tests, or calibration scripts — STOP. That's the wrong
direction. Re-read this brief.
```

## Memory pointer to update

After next session does Step 1, update memory entry to reflect new direction. Until then, current memory at `~/.claude/projects/.../memory/project-judge-design-deep-research-2026-05-12.md` reflects Phase 4 ship — needs correction to "Phase 4 reverted; next session: optimal-output-first design."
