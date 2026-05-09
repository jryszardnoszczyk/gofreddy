# Autoresearch Substrate Simplification — Hand-Off Brief for Parallel Agent

**Audience:** another Claude Code / Codex / opencode agent that will work in parallel on substrate simplification.
**Working dir:** suggest a worktree at `.worktrees/autoresearch-simplification/` off `origin/main` HEAD.
**Sister track:** the agent in the main checkout is concurrently fixing core runtime issues (lineage drift, content-moderation backend, cache replay). Coordinate through git but stay in your worktree.

## Context to load first

Read these in order:
1. `docs/research/2026-05-09-001-autoresearch-overengineering-audit.md` — the full audit with hard data, 7 over-engineered surfaces, 4 architecture options, and 3 critical findings (#117/#118/#119) from a deep-dive on one 12KB iter log.
2. `docs/plans/2026-04-22-006-impl-cluster-3-autoresearch.md` — the original autoresearch implementation plan from April. Establishes the design intent.
3. `autoresearch/lane_registry.py` — read in full. Single source of truth for what a "lane" is.
4. `autoresearch/evolve.py:cmd_run` — the outer loop. Read in full (it's 200 LOC of the function body within a 2,656-LOC file).
5. `autoresearch/evaluate_variant.py` lines 622-680 (`layer1_validate`) and 2901-2978 (`evaluate_holdout`) — these two functions plus the `_holdout_eligibility` predicate at line 2874 are the entire scoring + promotion gate. The other ~3,150 LOC is helpers.

## Your charter

The autoresearch evolution loop is doing 6 things (clone → mutate → score → compare → checkpoint → promote). It currently does this in ~30,000 LOC across `autoresearch/`, `harness/`, and `archive/v00*/workflows/`. Tonight's 18-hour run produced 0 net real promotions while burning ~$200-300 in API spend and hitting Max-plan rate-limit caps 6-7 times.

**Your job: design and prototype a simpler substrate that delivers the same 6 capabilities at ~1/15 the LOC.**

The audit lays out 4 architectural options:
- **A.** Keep substrate, fix bugs (rejected — bug surface area is the problem)
- **B.** Skill-based agent orchestrator (5-7 markdown skill files + 7 lane markdown files + ~500-800 LOC of Python tools, agent reads markdown at runtime and orchestrates)
- **C.** LangGraph-based (graph nodes + checkpointing + Send API for parallel)
- **D.** Hybrid — strip outer loop + lane registry, keep evaluate_variant + harness, agent orchestrates the kept Python via skills

Recommended target: **Option B**, validated on ONE lane (storyboard or x_engine, the simplest).

## Phase 0 — Validate the premise (Day 1, ~4-6 hours)

Before writing any new code, prove the simplification can match capability. Pick storyboard lane (simplest artifact shape) and:

1. **Read the lane's full surface:**
   - `autoresearch/archive/v006/workflows/storyboard.py` (~200 LOC)
   - `autoresearch/archive/v006/workflows/session_eval_storyboard.py` (~180 LOC)
   - `autoresearch/archive/v006/programs/storyboard-session.md` (~250 LOC, the actual prompt)
   - `autoresearch/archive/v006/programs/storyboard-evaluation-scope.yaml` (~50 LOC)
   - `autoresearch/lane_registry.py` storyboard LaneSpec entry (~30 LOC)

2. **Write a single markdown skill that does ONE evolution iter for storyboard.** Format:
   ```markdown
   # storyboard-evolve.md
   When: operator triggers `evolve storyboard`.
   Steps:
     1. Read current head from autoresearch/archive/current.json["storyboard"]
     2. Pick best historical variant from frontier.json["storyboard"] (anchor against drift)
     3. Mutate: ask claude/opus to edit programs/storyboard-session.md based on parent's
        last critic_reviews.md
     4. Score: for each fixture in search-v1.json["storyboard"]:
        - run codex agent with the new prompt against the fixture
        - send the resulting session_dir/stories/*.json + frames/*.json + report.md to the judge
        - collect per-rubric scores
     5. Decide: if mean(candidate scores) > mean(parent scores) by 0.5 absolute, promote
     6. Write: append to lineage.jsonl, update current.json head if promoted
   ```

3. **List the Python tools the skill needs.** They should be small, single-purpose. Hypothesis:
   - `mutate_prompt(lane: str, parent_prompt: str, critic_review: str) -> str` (~30 LOC, calls claude)
   - `run_session(lane: str, fixture: dict, prompt: str) -> Path` (~50 LOC, spawns codex)
   - `score_session(lane: str, session_dir: Path, rubrics: list) -> dict` (~50 LOC, calls judge)
   - `append_lineage(entry: dict) -> None` (~10 LOC, file append)
   - `promote(lane: str, variant_id: str) -> None` (~10 LOC, current.json update + atomic rename)

4. **Estimate total LOC.** If under 800 for the simplest lane, proceed. If over 1500, the abstraction is wrong — stop and re-design.

## Phase 1 — Build the storyboard slice (Days 2-3)

Implement the skill + tools end-to-end. Constraints:

- **NO Python control flow for orchestration.** The agent reads the skill and decides what to do. Tools are pure functions.
- **NO new framework dependencies** in this phase (no LangGraph, no LangChain). Just stdlib + existing autoresearch helpers.
- **Reuse existing scoring infrastructure** where possible — don't rewrite the judge HTTP service or the evaluate_session.py rubric loader.
- **Write 3 happy-path tests** plus 2 failure-mode tests (rate limit, judge unreachable).

## Phase 2 — Run head-to-head against current substrate (Day 4)

Pick ONE storyboard fixture (TechReview is the only one with completed real sessions today). Run:

- 3 evolution iters using your simplified substrate
- 3 evolution iters using the current substrate (now stopped — restart daemon for this lane only)

Compare:
- LOC touched per iter (your version vs current evolve.py call graph)
- Wall time per iter
- API spend per iter
- Did either produce a real promotion vs same parent?

If your version is comparable or better on all four, ship Option B for one lane. If not, escalate findings — maybe Option D (hybrid) is the right move.

## What NOT to touch

- **`autoresearch/lane_paths.py`** — scope enforcement is a real win (gradient-hacking defense). Reuse it.
- **`autoresearch/harness/`** — agent invocation helpers are mature and battle-tested. Reuse.
- **The judge HTTP services** (ports 7100/7200) — these are fine, just call them.
- **The PROMOTED variants in `archive/`** — read-only history. Append to `lineage.jsonl`, never modify.
- **Tests in `tests/autoresearch/`** — your new code adds tests, doesn't replace existing ones.

## Critical bugs the main-checkout agent is fixing in parallel

DO NOT duplicate this work. The main agent is fixing:
- **Finding #117** — codex content-moderation refuses to scrape; switching to opencode/deepseek-v4-flash for eval
- **Finding #118** — lineage drift; parent selection will anchor to frontier.json best
- **Finding #119** — runtime error cascade short-circuits

Your simplified substrate should INHERIT these fixes by reading current code, not re-implement them.

## Communication protocol

- **Sync via git, not chat.** Commit small, push to a branch, the main agent will fetch periodically.
- **Branch name suggestion:** `feat/autoresearch-simplification-spike`.
- **Don't merge to main without operator review.** This is a spike; if it works, the operator decides on the migration plan.
- **If you find a bug in the current substrate that affects your work**, file it as a task with `P? NEW: ...` description. Don't try to fix it in your branch — that creates merge conflicts with the main-checkout agent.

## Success criteria for Phase 0-2

You succeed if:
1. Storyboard lane evolves in <800 LOC of new code (skills + tools combined)
2. One full iter completes in <30 min wall time (current substrate: 60-90 min)
3. One full iter spends <$5 in API tokens (current substrate: ~$10-30/iter)
4. Either matches or beats current substrate on the head-to-head test
5. The skill files are reviewable in 30 minutes by an operator unfamiliar with the substrate

You fail if:
- The simplified version's bug surface is comparable to the current
- Skill files end up >300 lines each (means the abstraction is wrong)
- Tools get re-implemented from scratch instead of wrapping existing helpers
- The agent has to do too much reasoning per iter (means costs go up, not down)

## Timebox

- Phase 0: 1 day (validate premise)
- Phase 1: 2-3 days (build storyboard slice)
- Phase 2: 1 day (head-to-head)
- **Total: 1 week**. If you're not done in a week, the abstraction is wrong — escalate.

## Open questions you'll need answered

Note these as you encounter them and surface to operator:
1. Which model for the orchestrator agent — claude/opus, gpt-5.5, deepseek-v4-flash?
2. How does resume work in skill-based architecture? (Lineage.jsonl is append-only; agent can read last entry and decide what's next — but is that enough?)
3. Should skills be stored in `.claude/skills/` or in `autoresearch/skills/`? (Project-scoping vs portability tradeoff.)
4. Concurrency: should multiple lanes evolve in parallel skill-based, or strictly serial? (Tonight's parallel was the source of most rate-limit pain.)

Good luck.
