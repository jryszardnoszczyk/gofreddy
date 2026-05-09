---
status: handoff
created: 2026-05-09
author: claude opus 4.7 (continuation of session that surfaced findings #114, #115, #117, #118, #119, #120)
audience: fresh-session agent picking this up after /compact
goal: replace ~13.6k LOC autoresearch substrate with ~1k-2k LOC AI-first version, drawing on karpathy/autoresearch + pi-autoresearch + Anthropic "dreaming" patterns
predecessor-doc: docs/research/2026-05-09-001-autoresearch-overengineering-audit.md
predecessor-doc-2: docs/research/2026-05-09-002-autoresearch-substrate-simplification-handoff.md
---

# Autoresearch bare-bones rewrite — agent handoff

You are picking up where a previous session left off after the user (JR) asked **"why is the harness so many lines of code? Are all of the features really necessary?"** This document gives you everything you need to take an honest, AI-first second look at the autoresearch substrate, compare it to the canonical references, and produce a concrete plan + first-cut implementation for a leaner version.

The user has explicitly asked you to be **critical toward over-engineering** and to genuinely lean into the AI-first principle: *the agent is intelligent, trust it, give it tools not gates*.

---

## TL;DR: the gap is enormous

| Project | Substrate LOC | Tests | Gates / scope-checks | Files agent sees |
|---|---|---|---|---|
| **karpathy/autoresearch** (the canonical reference our naming comes from) | ~630 | n/a | 1 metric (val_bpb), 1 time budget (5 min) | 1 file (`train.py`) |
| **pi-autoresearch** (its generalization) | ~few hundred | n/a | benchmark exit code only | 2 files (`autoresearch.md`, `autoresearch.jsonl`) + optional shell hooks |
| **Anthropic "dreaming" pattern** (May 6 2026 launch) | n/a (built into Claude Managed Agents) | n/a | reference impls / test suites; `CLAUDE.md` + `CHANGELOG.md` | 2 files |
| **gofreddy autoresearch (us)** | **9,312 LOC top-level + 4,346 harness/scripts ≈ 13,658** | **~12,709** | scope enforcement, readonly subprefixes, structural gates, AUTOGEN regen, anti-drift floor, lineage append, holdout manifest, judges HTTP, concurrency semaphores, per-fixture session locks (now per-variant after #120), L1 validation, critique-prompt hash check, ... | full variant tree (every lane's session.md, all programs, all templates, all scripts, all workflows) |

We have **~22× more substrate code than karpathy** and **a multiple of his tests on top of that**. The features the substrate provides (anti-gradient-hacking, scope enforcement, multi-lane shared archive, multi-judge calibration, parallelism control) are real but the user's intuition is correct: most of them exist to defend against a problem that doesn't exist when you trust the agent and give it a small, focused surface.

The 5 days of debugging that just happened (#117 codex content-mod, #118 lineage drift, #119 runtime cascade, #114, #115, #120) were almost all caused by **interactions between substrate components**, not by the agent doing something genuinely wrong.

---

## The reference architectures, in detail

### 1. karpathy/autoresearch (the original)

Repo: <https://github.com/karpathy/autoresearch>

- **Total: ~630 LOC** across `prepare.py` (fixed) + `train.py` (agent-editable) + `program.md` (human-iterable instructions)
- **Single metric**: `val_bpb` (validation bits-per-byte; vocab-size-independent)
- **Single time budget**: 5 minutes per experiment
- **Single scope**: agent only edits `train.py`
- **Single mechanism**: agent reads `program.md`, edits `train.py`, runs 5-min training, measures `val_bpb`, decides keep-or-revert
- **Git is the lineage system** — kept changes get committed. No `lineage.jsonl`, no `frontier.json`, no `current.json`.
- Achieves ~12 experiments/hour on a single H100.

The philosophical claim is in plain text in his README: *the goal is to discover what the agent can do when you don't pre-tune the infrastructure for it.*

### 2. pi-autoresearch (its generalization)

Repo: <https://github.com/davebcn87/pi-autoresearch>

3 tools the agent calls at its discretion:
- `init_experiment(name, metric, unit, direction)` — create the session
- `run_experiment(cmd)` — execute any command, capture wall-clock + output
- `log_experiment(metric, status, description)` — append to log, auto-commit, update UI

2 persistent files survive restarts:
- `autoresearch.jsonl` — append-only experiment log
- `autoresearch.md` — living human-readable session doc (objective, attempted strategies, dead ends, wins)

Optional shell hooks: `autoresearch.sh` (benchmark), `autoresearch.checks.sh` (correctness — tests/types/lint), `autoresearch.hooks/before.sh` + `after.sh`.

Crucially: **failures only block commits**. Successes are logged whether they were useful or not. The agent decides what was useful. There is no scope-check, no readonly subprefix list, no anti-drift floor, no AUTOGEN regen, no critique-prompt hash. The benchmark exits zero or it doesn't.

### 3. Anthropic "dreaming" (Code with Claude, 2026-05-06)

The closest thing to what we're trying to build at production scale:
- Two files: `CLAUDE.md` (instructions) + `CHANGELOG.md` (portable long-term memory; "lab notes")
- "Ralph loop" — iteratively asks the agent if the task is really done
- Test oracle / reference impl as the only validation
- Anthropic's reported result: 6× completion rate vs. stateless agents — **purely from agents carrying institutional knowledge across sessions, no model change**

### 4. Broader 2026 landscape (for context)

- **GEPA** (reflective prompt evolution) — the prompt evolves, the agent doesn't write code
- **Darwin Gödel Machine** (ICLR 2026) — agents modify their own modification code; SWE-bench 20%→50%
- **EvoAgentX**, **Hermes**, **OpenAI's self-evolving agents cookbook** — all converge on the same pattern: tools + memory + metric, not gates + manifests + scope-enforcement

---

## What gofreddy's substrate has that the references don't

This is the honest accounting. Sized by best-guess LOC, status = "is this load-bearing or accidental?".

| Substrate component | LOC | Why it exists | AI-first verdict |
|---|---|---|---|
| **`evolve.py`** main orchestrator | 2,699 | candidate generation, parent selection, mutation, eval, gate, promote | mostly accidental — could be a 200-LOC `for gen in range(N): ...` loop |
| **`evaluate_variant.py`** scoring + holdout | 3,244 | search-v1 scoring, holdout-v1 hidden eval, judge HTTP, retry, fixture replay | **partially load-bearing** — judge HTTP retry + holdout isolation are real; the rest is fixture-replay-cache + lineage-append-update + manifest-decoration |
| **`evolve_ops.py`** | 1,144 | meta-workspace prep, lane-context, write-lane-context, atomic promote | accidental — workspace prep is to support scope enforcement (delete that, deletes most of this) |
| **`lane_registry.py`** + `LaneSpec` | 553 | declarative per-lane prefixes, readonly subprefixes, structural facts, gate functions, judge config | **mostly accidental** — replaces "agent reads the lane's session.md and figures out what to do" with structured machine-readable metadata *to drive substrate enforcement* |
| **`archive_index.py`** | 609 | `lineage.jsonl` accumulation, `frontier.json`, `index.json`, `prepare_meta_workspace`, `sync_variant_workspace`, `summarize_variant_diff` | accidental — git itself does most of this; `frontier.json` is a derived index that should just be `git log -- <lane>` |
| **`select_parent.py`** + `agent_calls.py` | 310 + 221 | LLM-driven parent picker with anti-drift floor + top-K + trajectory context | accidental — pi-autoresearch lets the agent read `autoresearch.md` and pick its own parent |
| **`concurrency.py`** + per-resource semaphores | 182 | claude=4, codex=2, opencode=8, judge_http=10, cloro_search=2; killswitch | partially load-bearing — Claude Max subscription cap is real; everything else is YAGNI |
| **`regen_program_docs.py`** | 304 | regenerate AUTOGEN block in session.md from `STRUCTURAL_DOC_FACTS` | accidental — the agent could just be told the structural facts in the prompt; the AUTOGEN-block-rewrite-on-clone caused #115 |
| **`lane_runtime.py`** + `current_runtime` materialization | 267 | rebuild `current_runtime/` from `current.json` heads on every evolve boot | accidental — symlinks (or just paths) replace this |
| **harness/** (agent.py, telemetry, stall, util, prompt_builder, opencode_jsonl, session_evaluator, backend) | ~1,500 | spawn agents, capture stalls, build prompts, route backends | partially load-bearing — backend abstraction is real; stall detection is a band-aid for agents that can't tell they're stuck |
| **archive/v006/run.py** + variant_dir copies | 1,500 (× ~30 variants on disk) | per-variant runtime entry point | accidental at scale — every variant has a near-identical `run.py`; the differences could be config |
| **archive/v006/scripts/render_report.py** + render scripts | 1,330 | HTML+PDF report rendering with codex enrichment | partially load-bearing — JR uses these reports; but they could be one tool the agent calls, not a substrate-mandatory pipeline |
| **L1 validation** (in `evaluate_variant.py`) | ~150 | py_compile every .py + bash -n every .sh + import check + program-file existence | accidental — the agent's first run will fail loud if the variant is broken; pre-flight L1 just hides it earlier |
| **Critique manifest** (SHA256 of critique prompts) | 114 | gradient-hacking defense from Pi v007 incident | **load-bearing** — keep this; it's the one anti-prompt-injection defense that earned its keep |
| **Scope enforcement** (`prepare_meta_workspace` + `sync_variant_workspace` chmod 0444 + hash diff) | ~300 | prevent meta-agent from editing readonly files | partially load-bearing — same lineage as the critique manifest, but expensive (caused #115 and weeks of "ScopeViolation" thrash) |
| **`compute_metrics.py`** + `events.py` | 517 + 103 | per-generation metric aggregation, event log | partially load-bearing — events are useful; per-generation aggregation is mostly informational |
| **5+ derived JSON files** (`current.json`, `index.json`, `frontier.json`, per-variant `scores.json`, per-variant `variant_manifest.json`) | n/a | denormalized indices over `lineage.jsonl` | accidental — pick ONE source of truth; the others are caches that drift (#114) |
| **Anti-drift floor** (just shipped 2026-05-09 commit `7469dcd`) | ~30 | filter parent candidates < 50% of best | accidental — symptom of `select_parent` being too clever; fix is to delete `select_parent` and let the agent pick |
| **Tests** | ~12,709 | test the substrate | proportional to substrate; shrinks with substrate |

**Honest summary**: of ~13,658 LOC, maybe 1,500-2,000 are actually load-bearing for the AI-first version (judges HTTP, critique manifest hash, fixture replay, backend abstraction, render pipeline as an *agent tool*). The other ~11,500 LOC exist to prop up an architecture where the substrate doesn't trust the agent.

---

## The 5 outstanding bugs and why they happen

(Lifted from the 2026-05-09-001 audit — useful as evidence that the architecture itself is the bug, not the implementations.)

| Bug | Cause | What it tells us |
|---|---|---|
| **#114** `variant_manifest.json` carries v001 identity (just fixed today, commit `cc6e21c`) | Manifest copied via `copytree` and never refreshed | We have **5 redundant indices** (`lineage.jsonl`, `index.json`, `frontier.json`, `scores.json`, `variant_manifest.json`) over the same data. Bug surface = O(redundancy). |
| **#115** x_engine/linkedin variants show phantom `programs/geo-session.md` edits in `changed_files` (just fixed today, commit `66a9567`) | `regen_program_docs.regen()` rewrote ALL lane session.mds on clone | AUTOGEN-block regen exists to keep machine-readable structural facts in sync with code; if we tell the agent the facts in plain English, this whole subsystem disappears. |
| **#117** codex content-moderation kills geo fixtures | "competitor analysis" prompts trigger codex's safety filter | Backend abstraction exists for exactly this; but our retry doesn't cleanly fall through to opencode/deepseek for safety-rejected prompts. |
| **#118** cascading lineage regression v007→v009→v071→v159 (just fixed today, commit `7469dcd`) | LLM parent-picker rationally picked unexplored low-scoring variants for "exploration" | The substrate chose to put parent-selection in front of the agent. If the agent ran the loop, it would just pick the highest-scoring parent. |
| **#119** runtime error cascade short-circuit (still open) | A single fixture session error propagates to abort the whole iter | Concurrency framework's exception handling. Wouldn't exist if each "experiment" was a single self-contained `run_experiment(cmd)`. |
| **#120** lock collision baseline + candidate same fixture (just fixed today, commit `07de6ed`) | `_lock_path` keyed only on (domain, client, fixture) | File-lock infrastructure is band-aid for trying to run multiple variants of the *same code* against the *same fixture* in the *same process tree*. pi-autoresearch sidesteps this by treating each experiment as an isolated `run_experiment` call. |

**Pattern**: every bug above is at a substrate↔substrate seam, not at a substrate↔agent seam. The architecture is fighting itself.

---

## What "AI-first bare-bones autoresearch" should look like

### Proposed architecture (~1,000-2,000 LOC target)

```
autoresearch_v2/
├── README.md                # objectives + how to run
├── autoresearch.md          # living session log (mirrors pi-autoresearch)
├── autoresearch.jsonl       # append-only experiment log
├── tools/                   # tools the agent invokes
│   ├── init_experiment.py   # ~50 LOC — create new attempt dir, log it
│   ├── run_experiment.py    # ~100 LOC — execute a session, capture deliverables, return path
│   ├── score_experiment.py  # ~150 LOC — call evolution-judge HTTP, return composite + reasoning
│   ├── log_experiment.py    # ~50 LOC — append jsonl, optional git commit
│   └── render_report.py     # ~200 LOC — keep this as a tool (JR uses the reports)
├── lanes/                   # one markdown per lane (was: ~5k LOC of LaneSpec + workflow.py + session.md)
│   ├── geo.md               # description + structural facts in plain English + example deliverables
│   ├── competitive.md
│   ├── monitoring.md
│   ├── storyboard.md
│   ├── marketing_audit.md
│   ├── x_engine.md
│   └── linkedin_engine.md
└── judges/                  # keep the HTTP judges; they earn their keep (~150 LOC of client + retry)
    └── ...
```

That's it. No lineage.jsonl→frontier.json→index.json→current.json fanout. No `prepare_meta_workspace` chmod 0444 dance. No `regen_program_docs` AUTOGEN rewrite. No `select_parent` LLM. No `lane_runtime` rebuild. No `evolve_ops.write_lane_context`. No anti-drift floor. No critique-prompt hash (well — keep it as a one-file `tools/critique_hash.py` that the agent calls if it wants).

### What the agent does (the AI-first part)

The driver is one short `program.md` that says, in plain English:

> Your job is to improve the geo lane's session.md so its judge composite score (measured on the 6 holdout fixtures) goes up. You can:
> 1. Read `lineage.jsonl` to see what's been tried and what scored what.
> 2. Read the current best `geo.md` (the lane prompt) and the current best deliverables (in `attempts/<best>/sessions/`).
> 3. Use `tools/run_experiment.py` to try a modified version. It will write to `attempts/<your_id>/`.
> 4. Use `tools/score_experiment.py` to score it on the 6 holdout fixtures.
> 5. Use `tools/log_experiment.py` to log the result. Commit if it improved.
> 6. Loop until told to stop or the score plateaus.
>
> Don't edit the lane prompts of other lanes. Don't edit the judge code or the structural fact list. Don't edit the holdout fixtures.

The "don't edit X" lines are **prompt-level guardrails, not chmod 0444 enforcement**. If the agent edits them anyway, the next experiment fails the judge and the agent learns. This is the AI-first principle: **trust the agent, log the failure, let it iterate**.

The 4 things gofreddy currently builds infrastructure for that AI-first replaces:

| gofreddy infrastructure | AI-first replacement |
|---|---|
| `LaneSpec.path_prefixes` + `prepare_meta_workspace` deleting non-lane files | Prompt: "your lane is geo; only edit files matching `geo*.md`" |
| `LaneSpec.readonly_subprefixes` + chmod 0444 + hash check | Prompt: "don't edit `workflows/geo.py` or `session_eval_geo.py`" |
| `regen_program_docs` AUTOGEN block rewrite | Prompt: "the structural facts you must satisfy: [list]" — and the judge's gate checks them |
| `select_parent` LLM agent | Prompt: "look at lineage.jsonl, pick whatever parent you think is best" |

Every replacement is **lower complexity AND more flexible**, because the agent can reason about edge cases (e.g., "the structural facts say X, but I see Y working in v009; let me try Y") that a hardcoded gate can't.

---

## What's actually load-bearing — the *do not delete* list

Be ruthless about deletion, but recognize the genuinely load-bearing parts:

1. **Holdout isolation**. The hidden eval set is operator-side at `~/.config/gofreddy/holdouts/`. It must NOT be in the agent's workspace. The agent must NOT see holdout fixture content (only get back a composite score). Keep this.

2. **Judges HTTP** (`session_judge:7100`, `evolution_judge:7200`). These are the actual measurement system; they're the analog of `val_bpb`. Keep them. The retry logic is ~50 LOC and earns its keep.

3. **Backend abstraction** for spawning sub-agents (claude / codex / opencode → openrouter/deepseek). Multi-provider failover for content-mod / rate-limit. Keep, but consolidate to ~200 LOC.

4. **Critique-prompt hash**. The Pi v007 gradient-hacking incident was real. A 50-LOC pre-flight hash check is cheap insurance.

5. **Render pipeline** (`render_report.py` produces HTML+PDF reports). JR uses these. Keep — but as a tool the agent calls when it wants to materialize results, not a mandatory substrate phase.

6. **Concurrency limit** for Claude Max subscription cap (4-concurrent limit). 30-LOC semaphore. Keep.

Everything else is on the table for deletion or radical simplification.

---

## Plan: how a fresh agent should approach this

### Step 1 — Verify the references (1 hour)

Read these in the order listed; you may need to clone them:

1. `git clone https://github.com/karpathy/autoresearch /tmp/karpathy-autoresearch && wc -l /tmp/karpathy-autoresearch/*.py` — measure the actual LOC; check the README; read `program.md` to see the prompt shape.
2. `git clone https://github.com/davebcn87/pi-autoresearch /tmp/pi-autoresearch && cat /tmp/pi-autoresearch/README.md` — read the tool signatures and how the autoresearch.md is structured.
3. <https://www.anthropic.com/research/long-running-Claude> — the dreaming pattern; what shape `CLAUDE.md` + `CHANGELOG.md` take.

Goal: independent confirmation of the LOC + tool counts above. If anything in this doc is wrong, fix it.

### Step 2 — Take a hard pass at gofreddy's substrate (1 hour)

Skim these files in this order, holding the question *"would a 2026 AI-first design include this?"*:
- `autoresearch/evolve.py` (2,699 LOC)
- `autoresearch/evaluate_variant.py` (3,244 LOC)
- `autoresearch/evolve_ops.py` (1,144 LOC)
- `autoresearch/select_parent.py` (310 LOC)
- `autoresearch/lane_registry.py` (553 LOC)
- `autoresearch/archive_index.py` (609 LOC)
- `autoresearch/regen_program_docs.py` (304 LOC)

For each, write down 3 lines: (a) what it does, (b) why it exists, (c) what the AI-first replacement is.

Useful pre-existing audits:
- `docs/research/2026-05-09-001-autoresearch-overengineering-audit.md` — section "What costs each component" is the start of the inventory above
- `docs/research/2026-05-09-002-autoresearch-substrate-simplification-handoff.md` — earlier handoff for a parallel agent (status uncertain)

### Step 3 — Spike one lane in ~500 LOC (1-2 dev days)

Pick **storyboard** (simplest workflow, has a working render pipeline) or **geo** (has a recently-validated holdout, just shipped v009 promotion).

Build `autoresearch_v2/` per the proposed architecture above. Wire up:
- `tools/init_experiment.py`
- `tools/run_experiment.py` (calls the existing v006 `run.py` for the lane — don't rewrite the lane runtime, just call it)
- `tools/score_experiment.py` (calls the existing judges HTTP — don't rewrite them)
- `tools/log_experiment.py`
- `lanes/<lane>.md` (port the current session.md to the AI-first prose form)
- `program.md` (the driver prompt)

Then run the loop: 5-10 iterations, manual loop (you push the agent through each iteration). Compare:
- Time per iter
- Cost per iter
- Holdout composite movement
- Bugs surfaced

If holdout composite moves comparably to recent runs at lower complexity and cost, **proceed to migration**. If it stalls or regresses, the substrate's complexity was actually load-bearing somewhere — figure out where.

### Step 4 — Migrate other lanes (1 dev day per lane × 6 = ~6 dev days)

For each of {competitive, monitoring, marketing_audit, x_engine, linkedin_engine, geo or storyboard (whichever you didn't spike)}, port the session.md to `lanes/<lane>.md` form. Run a 5-iter sweep. Confirm the loop works.

### Step 5 — Decommission the old substrate (1 dev day)

Once `autoresearch_v2/` is validated on all 7 lanes:
- Move `autoresearch/` to `autoresearch/legacy/` (don't delete yet)
- Move tests to `tests/legacy/`
- Update `CLAUDE.md`, `AGENTS.md`, top-level scripts to point at v2
- Run the full v2 sweep one more time end-to-end on operator-managed holdouts

Keep `autoresearch/legacy/` for one cycle (~1 month) before deletion.

### Total estimate: ~10-15 dev days, dropping ~10k+ LOC

That's the scope. The user (JR) is open to a multi-day rewrite if it eliminates the recurring substrate-bug class. **He has explicitly said "I'd bet a lot of the code is simply not needed."**

---

## Open questions for the fresh agent to answer

The previous session didn't have time to nail these down. They're decisions, not blockers:

1. **Q: Single repo `autoresearch_v2/` or full carve-out?** Lean toward in-repo with `autoresearch/legacy/` parallel — easier to roll back. JR has said "stay on main or worktree" (memory: `feedback-stay-on-main-or-worktree.md`). Probably worktree for the spike, then PR.

2. **Q: Keep `LaneSpec` registry or fully prose?** Recommendation: a small Python file per lane (~30 LOC) that holds {`name`, `holdout_fixtures`, `judge_endpoint`, `prompt_path`, `deliverable_glob`}. Everything else moves to the prompt. Total: ~7 × 30 = ~210 LOC instead of 553.

3. **Q: Keep multi-judge architecture (session-judge :7100 + evolution-judge :7200)?** Probably yes — they're already running and the API is stable. Just don't grow them.

4. **Q: Holdout manifest format — keep JSON or just a dir of fixtures?** Lean toward a dir + a 5-line `manifest.txt` instead of the current 5kB JSON-with-redaction-checks. Holdouts are operator-side; complexity should live there if anywhere.

5. **Q: Concurrency model — single sequential agent or parallel workers?** Lean sequential. The 18-hour 1,070-iter parallel sweep produced **0 net real promotions** (memory: `project-evolution-sweep-2026-05-08.md` and the audit). 800/1070 iters hit auth rate-limits. Sequential is simpler, cheaper, and proven (single-iter geo dry-run gave us the v009 holdout-passed promotion).

6. **Q: `current_runtime/` materialization — keep or symlink?** Almost certainly delete. The agent can read whichever variant directly.

7. **Q: What does the agent do when it wants to commit a kept change?** Recommendation: agent calls `tools/log_experiment.py(action='keep')` which does `git add lanes/<lane>.md attempts/<id>/ && git commit -m "evolve(<lane>): <agent-summary>"`. Mirrors pi-autoresearch.

8. **Q: How to surface "the agent is stuck"?** karpathy doesn't — the experiment just fails, the agent sees the failure, retries. Do the same. Delete `harness/stall.py`.

9. **Q: Anti-gradient-hacking?** Keep critique-prompt hash check, but make it a tool the agent runs explicitly (`tools/verify_critique_integrity.py`) rather than a substrate gate. Agents that don't call it just won't learn from a poisoned critique — same effect, much simpler implementation.

10. **Q: When does the v2 spike "win"?** Recommendation criteria: (a) one full lane (5-10 iters) producing holdout composite ≥ current baseline ± noise (b) substrate LOC < 1,500 (c) 0 bugs of the substrate↔substrate-seam class. If (a) fails, the complexity was earned.

---

## What the previous session shipped (don't re-do)

These all landed on origin/main today (2026-05-09) before the audit pivot:

| Commit | What |
|---|---|
| `7469dcd` | anti-drift floor in `select_parent` (Finding #118) |
| `0e5579e` | promote geo v009 (real holdout-passed @ 4.77) |
| `205cf64` | gate rejects zero-substrate promotions (Finding #113) |
| `07de6ed` | per-variant session lock (Finding #120) |
| `cc6e21c` | refresh `variant_manifest.json` at clone (Finding #114) |
| `66a9567` | scope `regen_program_docs` to current lane (Finding #115) |
| `a009055` | judges.env auto-source + image_preview_service wire (earlier in the day) |

If you decide to delete the substrate, all of these go away with it. **That's fine** — they were patches on the architecture that's about to be replaced. Reference them only as evidence that the substrate↔substrate seams are where bugs live.

---

## Memory references (already in user's auto-memory)

These are saved memories the user has from prior sessions; you can rely on them:

- `project-evolution-sweep-2026-05-08.md` — the 0-promotions sweep that triggered this audit
- `project-evolution-followup-fixes-shipped-2026-05-08.md` — the 4 substrate fixes from yesterday
- `project-self-improving-reports-shipped.md` — render pipeline shipped to v006
- `project-autoresearch-pipeline-state-2026-04-27.md` — earlier substrate state
- `feedback-trust-agent-drop-regex-guards.md` — JR has explicitly said before: don't add brittle regex/allowlist containment when prompt + architecture already keep agents in lane

The last one is **the founding principle** for this work. Read it.

---

## Sources / external references

- karpathy/autoresearch — <https://github.com/karpathy/autoresearch>
- pi-autoresearch — <https://github.com/davebcn87/pi-autoresearch>
- Anthropic long-running Claude — <https://www.anthropic.com/research/long-running-Claude>
- Anthropic dreaming announcement — <https://www.buildfastwithai.com/blogs/claude-managed-agents-dreaming-explained>
- Karpathy autoresearch deep-dive — <https://kenhuangus.substack.com/p/exploring-andrej-karpathys-autoresearch>
- Self-Evolving Agents survey — <https://arxiv.org/abs/2508.07407>
- EvoAgentX — <https://github.com/EvoAgentX/EvoAgentX>
- GEPA / Promptbreeder — referenced in the survey above
- OpenAI self-evolving agents cookbook — <https://developers.openai.com/cookbook/examples/partners/self_evolving_agents/autonomous_agent_retraining>

---

## How to start your fresh session

When the user gives you the green light, do this in order:

1. Read `docs/research/2026-05-09-001-autoresearch-overengineering-audit.md` (predecessor doc — has more bug-cause analysis)
2. Read THIS document
3. Read `feedback-trust-agent-drop-regex-guards.md` from auto-memory
4. Run Step 1 above (verify the references)
5. **Then** propose a concrete plan to JR with:
   - Which lane to spike first + why
   - Total estimated LOC for the v2 substrate
   - Total estimated dev days
   - Risks + rollback plan
6. Wait for JR's go before writing v2 code.

**Do not** start writing v2 code before steps 1-5. JR will course-correct on the plan, and writing code first will waste cycles.

**Do not** half-replace the substrate. Either it's small enough to be obviously simpler, or it's not worth doing.

**Do** be honest about LOC. If you find that v2 actually wants ~3,000 LOC instead of ~1,500, say so — the win is measured in *bug surface*, not in golf-coding LOC counts.

**Do** dogfood: use the existing `select_parent`'s anti-drift behavior, the geo v009 holdout-pass-criterion, and the working render pipeline as the *targets* for v2 to match. If v2 can match them at 1/10 the LOC, it's a real win.

Good luck. The user's intuition that "a lot of the code is simply not needed" is almost certainly right; the question is just which 1,500 LOC are the load-bearing ones.
