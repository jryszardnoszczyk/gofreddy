# Autoresearch Substrate — Overengineering Audit + Architecture Proposals

**Status:** investigation — recording findings before any redesign.
**Date:** 2026-05-09
**Origin:** 18h × 7-lane parallel daemon run produced 0 net real promotions despite ~$200-300 estimated direct API spend + Max-plan rate-limit caps hit 6-7 times. JR asked: "is our entire process over-engineered?"

This doc records what the substrate IS today, what it's TRYING to do, where the over-engineering lives, and three concrete alternative architectures (with cost/capability tradeoffs).

## TL;DR

**Yes, the substrate is significantly over-engineered for what it actually delivers.** ~14,200 LOC of orchestration + 1,357 LOC harness + 13,400 LOC of per-lane workflow code = **~28,950 LOC for an evolution loop that produced zero genuine promotions in 18 hours of running.**

The essential work the loop performs can be expressed in **~1,000 LOC + 7 lane markdown files + 5 skill markdown files**, IF the orchestration shifts from bespoke Python to an agent-orchestrator pattern.

The bottleneck is NOT the meta-agent — it's the substrate complexity creating bug surface area faster than evolution produces wins. The judge isn't discriminating either, but that's a separate problem.

## What the substrate is supposed to do

1. **Maintain a per-lane head pointer** — current.json lists which variant is "best" per lane.
2. **Clone a parent variant** — copy the variant directory.
3. **Mutate the clone** — meta-agent (claude/opus) edits the lane's prompt files.
4. **Score the mutation** — run the prompt against ~3-12 fixtures, judge each output.
5. **Compare to parent** — if better on hidden holdout, update head pointer.
6. **Persist for resume** — save state so a crashed iter can pick up.

That's it. Six responsibilities. The first three are filesystem ops, the fourth is "subprocess + score", the fifth is a comparison, the sixth is checkpointing.

## What the substrate actually contains (LOC accounting)

| Component | LOC | What it does |
|---|---|---|
| `autoresearch/evolve.py` | 2,656 | Outer loop: parent select → clone → mutate → score → finalize → promote |
| `autoresearch/evaluate_variant.py` | 3,236 | Search-suite scoring + holdout finalize + private finalize cache |
| `autoresearch/evolve_ops.py` | 1,144 | Helper ops: load_search_config, promote_atomic, fixture iter |
| `autoresearch/program_prescription_critic.py` | 619 | Critic-mode prompt generation for inner critique |
| `autoresearch/archive_index.py` | 609 | Lineage append + sync_variant_workspace |
| `autoresearch/lane_registry.py` | 553 | LaneSpec dataclass + 7 lane definitions |
| `autoresearch/lane_runtime.py` | 250 | current_runtime materialization + sync_filtered |
| `autoresearch/concurrency.py` | ~300 | ConcurrencyController + parallel_for |
| Other modules | ~5,000 | compute_metrics, regen_program_docs, agent_calls, etc. |
| **Total orchestration** | **~14,237** | |
| `autoresearch/harness/*` | 1,357 | Shared agent-spawning helpers |
| `archive/v006/workflows/*.py` | ~3,200 | Per-lane WorkflowSpec callables (configure_env, snapshot_evaluations, completion_guard, list_deliverables, etc.) |
| `archive/v006/scripts/*.py` | ~3,500 | evaluate_session, render_report, allocate_gaps, format_report |
| `archive/v006/programs/*.md` | ~5,500 | Per-lane prompt files (the actual content being evolved) |
| `archive/v007-curated/...` | ~4,700 | Same shape, x_engine + linkedin_engine versions |
| `tests/autoresearch/*` | 12,386 | Tests |
| **Total** | **~44,880** | (excluding archive variants v007, v008, v009, v010, v011) |

For comparison: `gpt-5-codex` (the agent backend) is one binary. `claude-opus-4.7` is one model. The substrate orchestrating these two LLMs is ~30k LOC.

## Where the over-engineering lives

Identified by reading the code + watching it fail in tonight's runs:

### 1. Multi-layer judge architecture (~3,500 LOC across modules)

The substrate has THREE separate judge layers:
- **Inner-critique** — runs INSIDE the agent session via `evaluate_session.py`, calls a separate `session-judge` HTTP service (port 7100)
- **Outer-search-judge** — scores per-fixture outputs, calls `session-judge` again with different rubrics
- **Holdout finalize-judge** — separate `evolution-judge` HTTP service (port 7200) for the hidden holdout

Each layer has its own:
- Auth probe at preflight
- Token threading (`SESSION_INVOKE_TOKEN`, `EVOLUTION_INVOKE_TOKEN`)
- Retry logic with backoff
- Cache (`.last_eval_cache.json`, `.render_synthesis_cache/`)
- Failure modes (judge unreachable / 401 / 5xx / timeout)

**Why this exists:** "to keep the holdout token away from the inner-critic so the agent can't game it." Real concern but solvable with a single judge service + lane-tagged tokens.

**What it costs:** Tonight's auth-probe failures (75% of iterations) traced to multi-backend probing. Each iter probes 3 endpoints + 2 backend CLIs = 5 auth checks before any work.

### 2. Per-variant materialization + sync (~1,000 LOC)

`current_runtime/` is a working directory that's clone-from-head, edit, sync-back. Includes:
- `ensure_materialized_runtime()` walks current.json, copies from each lane's head into current_runtime
- `_sync_filtered()` does the actual filesystem copy with `_is_protected_runtime_path` exceptions
- `sync_meta_workspace()` runs scope-violation detection comparing meta workspace against lane's owned tree
- `chmod 0444` on readonly substrate files (tonight's P0 #104 + chmod-writable fix #93ced01)

**Why this exists:** Meta-agent gets a sandbox to mutate without polluting the canonical archive.

**What it costs:** Tonight's chmod race condition broke ALL 7 workers when they ran in parallel. Without this layer, the meta-agent could just write directly to a worktree.

### 3. Lane registry with callable hooks (~550 LOC + 7 hook implementations × 7 lanes)

`LaneSpec` has 7 callable hooks (`configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings`) plus 5 optional ones (`custom_mutate`, `custom_score`, `custom_validate`, `custom_promote`, `custom_persist_judge_payload`).

Each lane (geo, competitive, monitoring, storyboard, marketing_audit, x_engine, linkedin_engine) implements ~80-200 LOC of these hooks.

**Why this exists:** Different lanes have different artifact shapes (findings.md vs digest.md vs drafts/*.md vs storyboards/*.json). Hooks let lanes customize behavior.

**What it costs:** A new lane requires ~7 hook functions to be written. Most of them are no-ops or copy-pasted. The lane abstraction exists to avoid `if domain == "monitoring"` branches in the orchestrator — but the orchestrator still has 7 such branches anyway (search shows `if lane == "all"`, `if lane == "core"`, etc.).

### 4. Resume infrastructure (~600 LOC)

Mid-meta-agent resume via `claude --resume`, viable_resume_id checks, `.session_ids.json` checkpoint, `--resume-variant` / `--resume-fixture` / `--fixtures-only` CLI modes, mid-evaluator-fixture skip-if-already-complete logic.

**Why this exists:** A crashed evolution iter is expensive to redo from scratch.

**What it costs:** Per-fixture state files, complex iter-level recovery, multiple resume paths to test. Tonight's `--resume` driver fix (commit 9aadbd0) was needed because the marketing_audit driver wasn't using the existing resume infrastructure.

### 5. Concurrency framework (~300 LOC)

`ConcurrencyController`, `parallel_for`, per-resource semaphores (claude=4, codex=2, opencode=8, judge_http=10, cloro_search=2). Ships with kill switch `AUTORESEARCH_CONCURRENCY=serial`.

**Why this exists:** Meta-agent invocations + judge HTTP calls + fixture session spawning all need to coordinate to avoid swamping subscriptions.

**What it costs:** Cross-lane parallelism (unit 3 of PR #44) was reverted after 5 P0 thread-safety bugs. Per-lane parallelism still has tonight's claude/opus rate-limit issue. Most users never reach the gnarly cases this code handles.

### 6. Per-variant manifests + lineage append (~1,200 LOC)

Every variant gets:
- A directory (full v006 copy + mutations)
- `variant_manifest.json` (metadata)
- A line in `lineage.jsonl` (search_metrics, holdout_metrics, promotion_summary)
- An `index.json` entry (summary)
- A `frontier.json` entry (per-lane best)

Tonight's P0 #114 found that `variant_manifest.json` gets corrupted (3 promoted variants had stale v001 manifests). The lineage entry IS the source of truth — the manifest is redundant.

### 7. Meta-prompt + scope enforcement infrastructure (~800 LOC)

`write_lane_context()` generates `lane-context.md` with editable scope. `prepare_meta_workspace()` chmod 0444's readonly files. `sync_meta_workspace()` raises `ScopeViolation` if meta-agent edits readonly files. Tonight's P1 #107 fix improved the meta-prompt to surface readonly_subprefixes BEFORE the agent starts, reducing wasted mutations.

**Why this exists:** Meta-agent shouldn't be able to neuter the inner-critic by editing the rubric files.

**What it costs:** This is genuinely valuable — it's the gradient-hacking defense from Pi v007 (where a meta-agent disabled completion_guard). Keep this.

## Findings from tonight's failed runs

### Hard data
- **18 hours runtime** (2026-05-08 21:29 → 2026-05-09 15:29)
- **1,070 worker iterations attempted**
- **800 (75%) hit AUTH_RATE_LIMIT** — claude/opus subscription cap blocked them
- **180 (17%) hit other errors** (materialization, scope violations, L1 failures)
- **91 (8.5%) executed real work**
- **3 promotions logged** — 2 spurious (rolled back via gate fix #205cf64), 1 real-but-regression
- **~$180-310 estimated direct OpenAI API spend** + 6-7 Claude Max rate-window burns
- **0 net genuine promotions**

### Bugs found AND fixed tonight (14 commits, on origin/main)
- L1 cross-lane false positive (4c62d58)
- Render timeout 120→360 (1d24f3d)
- load_json silent on empty files (975c5b8)
- voice.md materialization P0 #104 (d1a85e0)
- AUTORESEARCH_SESSION_DIR sandbox path (5bab5fa)
- search-v1 placeholder angles (6d9dcb5)
- Taxonomy doc refresh (5e35aa0)
- readonly_subprefixes in lane-context P1 #107 (41b3400)
- Driver --resume preserves state (9aadbd0)
- Storyboard camera_motion enum P1 #112 (4958917)
- x_engine + linkedin session_eval_specs in v006 P1 #109 (c470cfa)
- chmod target writable in _sync_filtered (93ced01)
- Gate rejects zero-substrate promotions P0 #113 (205cf64)

### Bugs identified, NOT yet fixed
- **#113** variant_manifest.json corruption (P0)
- **#114** cross-lane meta-agent edits geo-session.md from x_engine/linkedin lanes (P1)
- **#110** x_engine + linkedin sessions don't emit results.jsonl events (P2)
- **#115** judge isn't discriminating: 33 of 58 sample iters scored 0.0 despite running real sessions
- **#116** cache replay reports as fresh: many iter logs show `walltime=0.0s + composite=7.5378` (cached v006 baseline replayed)

The "judge isn't discriminating" finding (#115) is the **actual bottleneck**. Even a sharper meta-agent + a simpler substrate won't promote variants if the judge returns same-as-parent for genuinely different prompts.

## The architecture options

### Option A: Status quo — keep iterating on the bespoke substrate

**What:** Keep ~30k LOC, fix the 5 outstanding bugs (variant_manifest, cross-lane edits, results.jsonl, judge discrimination, cache replay), tune meta-prompt.

**Pro:**
- 14 commits of substrate fixes already shipped
- Lane registry abstraction works (mostly)
- Test suite (12k LOC) covers the substrate
- Resume + scope enforcement are real wins

**Con:**
- 1 P0/day surface area when stressed
- Each new lane = ~500 LOC of bespoke hooks + program docs + spec files
- Multi-judge architecture causes 75% iter failure rate on rate limits
- Materialization + sync layer was responsible for 4 P0s tonight alone
- ROI vs spend is currently negative

**Cost to maintain:** ~1 dev-week/month minimum to keep up with bug surface.
**Token cost per promotion:** ~$50-100 + many false starts (judge issue) = hard to drive below $200/promotion.

### Option B: Skill-based agent orchestrator (the option JR raised)

**What:** Replace the bespoke substrate with:

1. **5-7 markdown skill files** (~50-150 lines each):
   - `evolve-lane.md` — orchestrate one evolution iter for a lane
   - `mutate-prompt.md` — call meta-agent to draft a mutation
   - `score-variant.md` — run fixtures + collect scores
   - `decide-promotion.md` — compare and update head
   - `score-fixture-session.md` — invoke judges on one fixture
   - `resume-iter.md` — pick up a crashed iter

2. **7 lane markdown files** (~30-80 lines each):
   - `lanes/geo.md` — fixtures, rubrics, artifact shape
   - 6 more for each lane
   - Plus the existing `programs/<lane>-session.md` files (the actual content being evolved)

3. **~500-800 LOC of Python tools** that the agent calls:
   - `tools/spawn_session(prompt, fixture) → artifacts`
   - `tools/score(artifacts, rubric) → score`
   - `tools/append_lineage(entry) → None`
   - `tools/promote(lane, variant_id) → None`
   - File I/O helpers, judge HTTP wrapper

4. **An orchestrator agent** (claude/opus or gpt-5.5) that reads the skill files at runtime and decides what to do.

The agent IS the orchestrator. It reads `evolve-lane.md`, plans the iteration, calls tools, handles errors, decides promote/reject. No bespoke control flow.

**Pro:**
- ~1,000 LOC total vs 30,000 (30× reduction)
- Adding a new lane = 1 markdown file + maybe 1 prompt file (vs 7 hook implementations)
- Resume = "ask the agent what state was at last checkpoint" (LLM does the diff reasoning)
- Bug surface area collapses dramatically — tools are simple, agent reasons about composition
- Markdown skills are reviewable in 30 minutes vs 30k LOC code review

**Con:**
- Each evolution iter spends MORE tokens on the orchestrator agent (it has to read skills + plan, not just execute hardcoded flow)
- Determinism drops — same input may produce different orchestration paths
- Concurrency control becomes "ask the agent to manage" — fragile under load
- Test surface shifts from unit tests to "did the orchestrator do the right thing"
- Migration cost: rewrite + validate same outcomes against current substrate

**Cost to maintain:** ~1 dev-day/week — most fixes are in markdown.
**Token cost per evolution iter:** ~2-3× current (orchestrator overhead) but **success rate likely 5-10× higher** because no substrate-level crashes. Net ROI improves.

### Option C: LangGraph-based architecture

**What:** Use LangGraph (or similar — LangChain Expression Language, OpenAI Swarm, Anthropic's MCP, etc.) as the orchestration framework:

1. **Define evolution loop as a graph** with nodes:
   - `parent_select` → `mutate` → `score_parent` + `score_candidate` (parallel) → `decide` → `promote_or_reject`
2. **Resume via LangGraph's native checkpoint** — graph persistence is a one-liner (`MemorySaver()` or `SqliteSaver`)
3. **Parallel fan-out via LangGraph's Send API** — fixture scoring naturally parallel
4. **Tools** are LangChain `@tool`-decorated Python functions
5. **Lanes** are graph instances or graph parameters

**Pro:**
- Battle-tested orchestration (LangGraph used at scale at LangChain, IBM, etc.)
- Native checkpointing (resume comes free)
- Native parallel fan-out (concurrency comes free)
- Visualizable graph (vs reading 14k LOC)
- Strong ecosystem (LangSmith for tracing, etc.)
- Reduces Python surface to ~1,500 LOC of node implementations + ~300 LOC of graph definition
- Tools become reusable across other agentic work in the project

**Con:**
- Adds LangChain/LangGraph dependency tree (substantial — pulls langchain-core, langchain, langgraph, etc.)
- LangGraph has its own learning curve + version churn
- Locks orchestration to one framework (vs portable Python)
- Some current substrate features (scope enforcement, lane-context.md generation) need re-implementation
- Migration is non-trivial: the existing tests don't translate directly

**Cost to maintain:** ~1 dev-day/week + LangGraph version updates ~1/quarter.
**Token cost per iter:** similar to Option B but with better cache reuse via LangGraph's caching layer.

### Option D: Hybrid — Skills for orchestration, current Python for tools

**What:** The smallest move with the most win. Keep tonight's substrate fixes. Strip out:
- The bespoke evolve.py outer loop (replace with markdown skill)
- The lane registry callable hooks (replace with lane markdown files + hardcoded behavior in the 6-8 lanes today)
- The complex resume infrastructure (replace with simple "agent reads last lineage entry, decides what to do next")

Keep:
- `evaluate_variant.py` core scoring (ports cleanly)
- `harness/` agent invocation helpers (still useful as tools)
- `lane_paths.py` + scope enforcement (this is the gradient-hacking defense)
- All 14 commits' substrate fixes

Result: ~5,000 LOC instead of 30,000. Tools call current code, orchestrator agent reads markdown.

## Recommendation

**Don't decide tonight.** This is a 1-2 week migration if done right, with real risk of breaking the few things that DO work (Stripe pipeline, monitoring v011 lineage, x_engine + linkedin substrate).

But the data is clear that the current architecture isn't paying back its complexity. Three concrete next steps:

1. **Investigate the judge first (P0 #115).** If the judge can't discriminate "better" from "same," NO architecture change helps. Do a 1-hour test: take v006's geo prompt, manually edit it to be deliberately worse, run both through the judge, see if the score differs. If it doesn't, stop everything and fix the judge.

2. **Spike Option B for ONE lane.** Pick the simplest lane (storyboard or x_engine), build the skills + tools to evolve it end-to-end in ~500 LOC. Run 5 iters serially. Compare against current substrate's behavior. Estimated work: 2-3 dev days. If it works AND produces real promotions, plan migration of other lanes.

3. **Don't build LangGraph version yet.** Option C is plausible but premature. Validate Option B's premise (skills + tools is enough) before adding framework complexity. LangGraph's value is at higher complexity than what we need.

## NEW FINDINGS (post-doc deep-dive on geo v159 0-composite iter)

Reading one 12KB log of a 0-composite "real iter" end-to-end revealed the
ACTUAL bottleneck:

### Finding #117 (P0 — bigger than #115 judge issue): codex content-moderation kills fixture sessions

Every geo fixture in v159 died with:
```
Session BLOCKED: terminal agent marker detected on iter 3
(content-moderation / cyber-flag).
Same prompt → same flag; rotate fixture or rephrase prescription.
```

This is **codex/gpt-5.5 refusing to scrape public websites**
(bmw.de, semrush.com, mayoclinic.org). The cybersecurity guardrail
flags the agent's curl commands as suspicious. 3/3 fixtures fail
identically. The substrate then scores 0.0 because there's no deliverable.

**No amount of meta-prompt mutation, judge fixing, or substrate
simplification fixes this.** The agent backend itself is refusing
to do the work the lane requires (scraping public marketing pages).

This is the dominant failure mode tonight. Many of the 33/58
"composite=0.0" iters are likely this same content-moderation refusal,
not judge-discrimination problems.

**Possible fixes:**
1. Switch eval backend from codex/gpt-5.5 to claude/sonnet for fixtures
   that involve web scraping (Anthropic has different guardrails for
   public-page reads).
2. Use direct freddy CLI / playwright tools for scraping, not the
   inline agent shell.
3. Request approval to use codex with `--dangerous-bypass-content-policy`
   or equivalent.

### Finding #118 (P0): cascading lineage regression

The geo lineage has been monotonically degrading over generations:
- v007 = 5.9194 (frontier)
- v009 = 5.9018
- v071 = 0.0 (parent of v159, a regression)
- v159 = 0.0 (clone of v071)

The meta-agent in v159 explicitly said: "v071 hit 0.000 across 3/3
fixtures. The rational response is to repair the substrate, not iterate
further on it." It correctly diagnosed the regression and reverted to
v007 verbatim — but the iter still failed (because Finding #117 prevented
sessions from completing).

This means: without an explicit "promote-best-from-history" mechanism,
random mutation drift produces cascading regressions. The current
gate accepts a bad variant if no better candidate exists, then mutates
FROM the bad variant in the next iter. Each generation can only get
worse from the worst-promoted parent.

**Fix:** parent selection should always include the historical best
(not just the current head) as a candidate. This was probably the
original intent of `frontier.json` but it isn't being respected.

### Finding #119 (P1): runtime errors compound

Visible in v159's log:
- `You've hit your limit · resets 6:50pm`
- `Error: Session ID 9033021c-04a8-42de-9b00-38b4ac841a54 is already in use.`
- `judge HTTP 500 for geo-mayoclinic-atrial-fibrillation (attempt 1/4)`
- `WARN: geo-nubank-br-conta exited cleanly but produced no deliverables (1780.0s)`
- `terminal agent marker detected on iter 4`

Three independent failure layers stacked: rate limit → session ID
collision on retry → judge 5xx → content-moderation. The substrate's
retry logic correctly retries each, but the cascade burns 30+ minutes
per iter producing nothing.

## Open questions for JR

1. Is `claude/opus` the right meta-agent for prompt mutation, or would a smaller sharper model do equivalent work for 10× less cost?
2. Are we evolving the right thing? (Programs/<lane>-session.md prompts vs the structural validators vs the judge rubrics)
3. What's the success metric? (Composite score lift? Holdout pass rate? Operator-judged quality?)
4. Should evolution be daemon-style (continuous) or kickoff-style (operator triggers, runs once, reviews)?

The daemon model burned compute to no end. Kickoff-style with operator-in-the-loop reviewing each iter would yield 10× better signal-per-dollar.
