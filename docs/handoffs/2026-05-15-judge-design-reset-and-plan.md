---
date: 2026-05-15
type: reset + comprehensive plan (judge-design)
status: ready-to-execute post-compaction
supersedes: 2026-05-13-judge-rewrites-for-evolution-resume.md (handoff)
supersedes: 2026-05-13-judge-rewrites-retune-playbook.md (playbook)
supersedes: 2026-05-13-judge-retune-round-1.md (retune)
---

# Judge-design reset + comprehensive plan (2026-05-15)

## Why we're resetting

The 2026-05-13 judge-design work optimized rubric prose for σ widening on a 5-fixture sample. That was the wrong target:
- **Overfitting**: σ on small N is overfit to the test set, not generalizable
- **Wrong objective**: variance is a *property of selection signal*, not a design goal
- **Wrong methodology**: per `2ce99bb` (2026-05-08), prose tightening hits a ~2-point per-draft noise floor inherent to the LLM judge stack. Eliminating it via prose is empirically impossible.
- **Lost substance**: replaced human-readable quality-criterion prose with contract-style operational pedantry
- **Skipped domain research**: never investigated what makes excellent outputs per workflow

**Correct direction**: encode domain-expert quality criteria. Not statistical properties.

## Phase 1 — Surgical restoration (~30 min)

### What to restore

In `src/evaluation/rubrics.py`, replace 13 prose blocks with their pre-rewrite versions from git commit `204e9a6`:

| Block | Lane |
|---|---|
| `_MON_1` | monitoring |
| `_MON_3` | monitoring |
| `_MON_4` | monitoring |
| `_MON_5` | monitoring |
| `_MON_6` | monitoring |
| `_CI_1` | competitive |
| `_CI_5` | competitive |
| `_CI_6` | competitive |
| `_CI_7` | competitive |
| `_SB_1` | storyboard |
| `_SB_2` | storyboard |
| `_SB_3` | storyboard |
| `_SB_5` | storyboard |

Source: `git show 204e9a6:src/evaluation/rubrics.py | grep -A 30 "^_MON_1"` etc.

In variant files, restore same 13 CRITERIA dict entries to original brief prose:
- `autoresearch/archive/v006/workflows/session_eval_monitoring.py` (5 entries)
- `autoresearch/archive/v006/workflows/session_eval_competitive.py` (4 entries)
- `autoresearch/archive/v006/workflows/session_eval_storyboard.py` (4 entries)
- `autoresearch/archive/v160/workflows/session_eval_monitoring.py` (5 entries — operator-local)
- `autoresearch/archive/v018/workflows/session_eval_competitive.py` (4 entries — operator-local)

Source: same git revision. The brief-form prose in those files pre-dates my rewrites; iteration agent overwrote them with v2 content.

### What to KEEP (do NOT touch)

- **`_X_9` prose block** + RUBRICS entry + lane_registry inclusion → real deterministic value, domain-grounded
- **X-9 entries in variant CRITERIA dicts** (where iteration agent added them)
- **Substrate-level fixes** (commits `9b7e091` PR-A, `aa107e8` PR-B, `07fbb3f` PR-C, `c3f4a48` grace-mode strict, `fe7682a` axis-collapse escape hatch removal) — none of this is mine; none is variance-driven prose
- **Handoff docs** under `docs/handoffs/` (`2026-05-13-*` files) — keep as historical record
- **Iteration agent's substrate adaptations** (URL banning, Pre-Commit Self-Check, etc.) — variant-level, real progress

### Implementation steps

1. `git show 204e9a6:src/evaluation/rubrics.py > /tmp/rubrics_original.py`
2. Extract 13 prose blocks from that file
3. Surgical Edit calls on each `_MON_N`/`_CI_N`/`_SB_N` block in current `rubrics.py`
4. Same for the 5 variant files (use the brief prose from session memory or git history)
5. `python -c "from src.evaluation.rubrics import RUBRICS, RUBRIC_VERSION; print(len(RUBRICS), RUBRIC_VERSION)"` — verify 53 criteria, new hash
6. Single commit: `revert(rubrics): restore original substantive prose for 13 criteria; keep X-9 + substrate work`
7. Push to origin (rebase if needed; origin is now ahead by various non-conflicting commits)

### Validation

Direct git diff after restoration:
- `git diff 204e9a6 HEAD -- src/evaluation/rubrics.py` should show ONLY: X-9 prose block + RUBRICS X-9 entry + assertion count bump (52→53) + lane_registry x_engine addition

If anything else differs, those changes need investigation before merge.

## Phase 2 — Per-lane domain knowledge audit + research (~3-4 hours wall, parallel agents)

### Question to answer per lane

**What does an industry expert actually look for in an excellent [lane output]?**

Not "what produces variance." Not "what catches all gaming." What domain practitioners — who've reviewed thousands of these artifacts — consider the difference between mediocre and great.

### Lanes in scope

User priorities: **GEO + competitive + monitoring** (definite). **Storyboard** (maybe — investigate whether current rubric already encodes creator-strategist depth).

### Pre-research investigation per lane (~5 min each)

Before spawning research agents, read current rubric for each lane (post-restoration). For each:
- Does the prose actually capture domain-expert criteria?
- Or is it generic / shallow / aspirational?

If lane judges look domain-grounded → skip deep research; document why current judges are adequate.
If lane judges look thin → spawn research agent.

### Research agent prompt template (per lane)

```
You are researching what makes excellent [LANE] outputs. The goal is producing
judge criteria grounded in domain expertise, not statistical properties.

Investigate these sources:
1. Industry exemplars — 5-10 real-world examples of "best-in-class" [lane] outputs.
   For [lane], specifically look at: [LANE-SPECIFIC SOURCES BELOW]
2. Practitioner heuristics — what do veteran [domain experts] actually evaluate
   when reviewing [lane] outputs?
3. Published frameworks — academic + industry frameworks (cite specific papers,
   books, methodologies)
4. Failure modes — what specific failure patterns separate mediocre from great?

DO NOT:
- Reference statistical properties (σ, variance, discrimination)
- Use abstract principles ("falsifiability," "anti-gaming," "substitution tests")
- Apply meta-patterns transferred from other domains

DO:
- Quote real exemplars
- Name specific practitioners + their heuristics
- Surface domain-specific terminology + frameworks
- Identify quality dimensions that domain experts genuinely use

Deliverable: ~2000-word synthesis with these sections:
1. What makes excellent [lane] outputs (5-7 quality dimensions, each grounded
   in named source)
2. What separates great from mediocre (specific failure modes from named sources)
3. Industry terminology + frameworks the rubric should use
4. 3-5 proposed judge criteria specs grounded in this research
5. Sources cited with links/references

Write the synthesis to docs/research/2026-05-15-judges-domain-[LANE].md
```

### Lane-specific sources

**GEO** (AI-search-optimized landing pages):
- Aggarwal et al. "GEO: Generative Engine Optimization" (arXiv 2311.09735, KDD 2024)
- Andrea Volpini's WordLift writing on AI search
- Cyrus Shepard on AI citation patterns
- Real exemplars: Wikipedia structured articles, Stack Overflow top answers, Mayo Clinic patient-info pages, government .gov resources that Perplexity/ChatGPT consistently cite
- Search Engine Journal AI-SEO column 2024-2026

**Competitive**:
- McKinsey/Bain/BCG published competitive teardowns (look for client-facing examples in their public archives)
- Hamilton Helmer "7 Powers" framework
- Andy Raskin's "strategic narrative" frameworks
- April Dunford on positioning + competitive context
- SCIP (Strategic and Competitive Intelligence Professionals) published methodologies
- Reach3 Insights, M-Brain, Wiser sample briefs

**Monitoring** (weekly brand-monitoring digest):
- Cision / Meltwater / Brandwatch sample reports (free public versions)
- Crisis-comms playbooks (Eric Dezenhall, Edelman Trust Barometer methodology)
- Media-monitoring trade publications (Bulldog Reporter, Cision blog)
- Real exemplars: financial-services regulatory monitoring digests, FAA aviation safety bulletins (different domain but excellent format)
- Practitioner perspective: ex-Edelman / ex-Weber Shandwick monitoring directors

**Storyboard** (creator video story plans) — investigate first, may not need:
- MrBeast's leaked production process documents
- Casey Neistat process videos
- Mark Manson's content frameworks
- Creator-strategist substacks (Colin & Samir, Jake Tran)
- Vidpros / Standard / Creators on creator workflow

### Parallel agent dispatch

Once Phase 1 restoration done + Phase 2 pre-investigation complete:

```
[Launch in parallel — single message, multiple Agent tool calls]
- 1 agent for GEO
- 1 agent for competitive
- 1 agent for monitoring
- (1 agent for storyboard ONLY IF pre-investigation says current rubric is thin)
```

Each returns its 2000-word synthesis to `docs/research/2026-05-15-judges-domain-<lane>.md`.

Cost: ~$20-40 total. Wall time: ~30 min.

## Phase 3 — LLM judge methodology research (~1 hour, parallel with Phase 2)

### Question

What does the LLM-as-judge literature say works for evolution-loop scoring of long-form artifacts at small N? Specifically:
- Pairwise comparison vs absolute scoring
- Few-shot anchoring with real examples vs operational definitions
- Calibration sets and human-labeled ground truth
- Multi-sample / self-consistency
- Bias mitigations (position, verbosity, self-preference)
- Inter-rater agreement (Cohen's κ, Krippendorff's α)
- Intra-rater consistency (Policy Invariance, Rating Roulette)
- Evolution-loop-specific patterns (vs eval-suite patterns)

### Agent prompt

```
Survey LLM-as-judge literature 2023-2026. Focus on production deployment of
LLM judges for long-form artifact evaluation (not chatbot/MT-Bench style
pairwise tasks).

Specifically address:
1. Pairwise vs absolute scoring — when does each work, what does literature
   recommend for our use case (evolution-loop scoring of structured artifacts)?
2. Few-shot anchoring with concrete examples — effectiveness vs cost
3. Calibration sets — sizes, human-labeling protocols, drift detection
4. Multi-sample / self-consistency — when worth the cost
5. Bias mitigations that actually work in production
6. Failure modes of absolute-gradient scoring at small N (5-30 artifacts)
7. Production patterns from real deployments — Anthropic Constitutional AI
   evaluators, OpenAI Evals, LMSYS, Allen Institute, etc.
8. What's hype vs validated

Cite specific papers, posts, and production case studies. Synthesize into
a recommendation for our autoresearch evolution loop, which scores long-form
marketing artifacts (digests, briefs, story plans) at N=5-30 fixtures per
lane with single-judge absolute 0/0.5/1 scoring.

Deliverable: ~2500-word synthesis at docs/research/2026-05-15-judges-methodology.md

Sources to start from (not exhaustive):
- Zheng et al "Judging LLM-as-a-Judge" (MT-Bench, 2023)
- Liu et al "G-Eval" (2023)
- Wang et al "PandaLM"
- arXiv 2510.27106 "Rating Roulette" (intra-rater inconsistency, Krippendorff α<0.8)
- arXiv 2502.01534 "Preference Leakage"
- arXiv 2605.06161 "Policy Invariance"
- Anthropic Constitutional AI / RLAIF papers
- OpenAI Evals documentation + GitHub
- Recent arxiv on production judge deployment 2024-2026
```

Cost: ~$5-15. Wall time: ~15-30 min.

## Phase 4 — Synthesis + judge redesign (~2-3 hours, NO PROSE WRITING UNTIL DONE)

After Phase 2 + Phase 3 results land:

### Step 1: Cross-reference domain research × methodology
- For each lane, take the domain research synthesis
- Apply methodology research conclusions (probably: switch some to pairwise, add few-shot anchors, build small calibration set)
- Determine if judge paradigm itself should change for some lanes

### Step 2: Per-lane judge spec drafts
For each lane:
- 6-8 criteria grounded in domain research
- Format determined by methodology research (absolute / pairwise / hybrid)
- Anchored with REAL artifact examples (few-shot) when methodology supports
- Document failure modes per criterion from domain research

### Step 3: User review of specs before implementation
Don't write prose. Show the user: "for monitoring, here are 6 criteria derived from [Cision / Meltwater / Eric Dezenhall sources]; should we proceed with these?"

### Step 4: Only after spec approval → write prose for each criterion

### Step 5: Calibration set construction
Build small (15-25 artifacts per lane) human-labeled set BEFORE deployment. Use it as a frozen reference; periodically check rubric vs human judgment.

### Step 6: Deploy + monitor → empirical iteration with real signal

## What we will NOT do

- **No more σ-widening as design target.** Variance is a downstream property, not a goal.
- **No more anti-gaming clauses, substitution tests, falsifiability requirements** as abstract design moves — these are valid concepts but only when grounded in specific domain-failure-mode evidence.
- **No more variant-side calibration iteration loops.** The 2ce99bb finding stands: noise floor is inherent.
- **No more pattern-application across lanes.** Each lane gets its own domain-grounded criteria.
- **No more prose work without literature backing.** Methodology research dictates paradigm before prose.

## References — what we know now

### From this session
- 2026-05-13 audit-findings: `docs/brainstorms/2026-05-12-judge-design-deep-research/audit-findings-2026-05-13.md`
- 2026-05-13 handoff (now superseded): `docs/handoffs/2026-05-13-judge-rewrites-for-evolution-resume.md`
- 2026-05-13 retune playbook (now superseded): `docs/handoffs/2026-05-13-judge-rewrites-retune-playbook.md`
- 2026-05-13 retune round 1 (cancelled): `docs/handoffs/2026-05-13-judge-retune-round-1.md`

### Prior judge work (was reverted)
- 2026-05-08 J1-J4 rewrites + revert: `2ce99bb revert + fix: roll back J1-J4 rubric rewrites, switch to avg-variance gate`
  - Empirical finding: prose tightening hits ~2-point noise floor; can't eliminate
  - Architectural solution: avg-variance gate (1.5) replaces max-variance gate
  - Calibration script: `scripts/calibrate_judge_stability.py`

### Current substrate state
- Axis-collapse fix: shipped 2026-05-11 (PR #60), escape hatch removed 2026-05-13 (`fe7682a`)
- PR-A rate-limit promotion: `9b7e091`
- PR-B failed-criteria feedback injection: `aa107e8`
- PR-C prompt nudges: `07fbb3f`
- Grace-mode strict: `c3f4a48`

### Parallel work streams (out of judge scope)
- Content engine v1: `docs/plans/2026-05-13-002-feat-content-engine-lanes-v1-plan.md`
- Site_engine 4th lane: `docs/plans/2026-05-14-001-feat-site-engine-rubric-plan.md` (merged at `4c240c3`)

## Resume-after-compaction prompt

```
Resume judge-design work per `docs/handoffs/2026-05-15-judge-design-reset-and-plan.md`.

State of play at compaction: Phase 1 surgical restoration not yet done.
Phase 2 + 3 + 4 follow.

CRITICAL CONTEXT YOU MUST INTERNALIZE BEFORE DOING ANYTHING:
1. Prior judge work (2026-05-13) optimized rubric prose for σ widening on
   5-fixture samples. That was WRONG — it was overfitting + chasing a noise
   floor the codebase already proved (commit 2ce99bb, 2026-05-08) cannot be
   eliminated by prose tightening.
2. The correct direction is domain-expert quality criteria, not statistical
   properties.
3. Variance is a property of selection signal, not a design goal.
4. NO PROSE WORK UNTIL DOMAIN RESEARCH + METHODOLOGY RESEARCH ARE DONE.

Next action: read this doc fully. Then execute Phase 1 (surgical restoration)
without spawning agents. Validate via git diff that nothing besides the 13
prose blocks changed. Commit + push.

After Phase 1 complete: do the Phase 2 pre-investigation per lane (~5 min
each), then spawn parallel research agents per the plan.

Phase 3 (methodology research) runs parallel to Phase 2 — separate agent.

Phase 4 synthesis waits until both return.

User has explicit direction: NO calibration scripts, NO discrimination analysis,
NO variance-driven prose work. Domain-first, methodology-grounded, then prose
last.

If you find yourself reaching for σ analysis or "let's calibrate first" — STOP.
That's the wrong direction. Reread this doc.
```

## Memory pointer to update

After committing this plan, update:
- `~/.claude/projects/-Users-jryszardnoszczyk-Documents-GitHub-gofreddy/memory/MEMORY.md` line 7
- Replace "Judge plan v3 LOCKED + audit corrected" entry with pointer to this doc + the reset framing
