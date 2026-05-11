---
status: handoff (revised 2026-05-11 after evidence-based pressure-test)
created: 2026-05-09
last-revised: 2026-05-11
author: claude opus 4.7 (continuation of session that surfaced findings #114, #115, #117, #118, #119, #120)
audience: fresh-session agent picking this up after /compact
goal: replace ~13.6k LOC autoresearch substrate with ~2.5k LOC AI-first version, drawing on karpathy/autoresearch + pi-autoresearch + Anthropic "dreaming" patterns
predecessor-doc: docs/research/2026-05-09-001-autoresearch-overengineering-audit.md
predecessor-doc-2: docs/research/2026-05-09-002-autoresearch-substrate-simplification-handoff.md
companion-doc: docs/research/2026-05-11-001-substrate-feature-audit-evidence-based.md
---

> **2026-05-11 revision note:** original draft said "22× karpathy" gap and ~1,500 LOC target. Evidence-based pressure-test (`2026-05-11-001-substrate-feature-audit-evidence-based.md`) reclassified 4 items from REJECT → KEEP (anti-drift floor, alert agent, archive_cli.py, events.py + telemetry + SessionsFile). Honest gap is **~5× karpathy + pi**, honest v2 target is **~2,500 LOC**. The thesis (most of substrate is over-engineered) holds; the magnitudes were overstated. This doc has been updated; see the companion doc for the per-feature evidence trail.

# Autoresearch bare-bones rewrite — agent handoff

You are picking up where a previous session left off after the user (JR) asked **"why is the harness so many lines of code? Are all of the features really necessary?"** This document gives you everything you need to take an honest, AI-first second look at the autoresearch substrate, compare it to the canonical references, and produce a concrete plan + first-cut implementation for a leaner version.

The user has explicitly asked you to be **critical toward over-engineering** and to genuinely lean into the AI-first principle: *the agent is intelligent, trust it, give it tools not gates*.

---

## TL;DR: the gap is real, but smaller than first claimed

| Project | Substrate LOC (verified) | Tests | Gates / scope-checks | Files agent sees |
|---|---|---|---|---|
| **karpathy/autoresearch** (the canonical reference our naming comes from) | **1,225** (`prepare.py` 389 + `train.py` 630 + `program.md` 114 + `README.md` 92) | n/a | 1 metric (val_bpb), 1 time budget (5 min) | 1 file (`train.py`) |
| **pi-autoresearch** (its generalization) | **~3,800 LOC of TS extension** (index.ts 3038, plus jsonl/compaction/shortcuts/hooks ~700) + skills/finalize ~600 | tests/ ~1k | benchmark exit code + optional checks script | 2 files (`autoresearch.md`, `autoresearch.jsonl`) + optional shell hooks |
| **Anthropic "dreaming" pattern** (May 6 2026 launch) | n/a (built into Claude Managed Agents) | n/a | reference impls / test suites; `CLAUDE.md` + `CHANGELOG.md` | 2 files |
| **gofreddy autoresearch (us)** | **9,312 LOC top-level + 4,346 harness/scripts ≈ 13,658** | **~12,709** | scope enforcement, readonly subprefixes, structural gates, AUTOGEN regen, anti-drift floor, lineage append, holdout manifest, judges HTTP, concurrency semaphores, per-fixture session locks (now per-variant after #120), L1 validation, critique-prompt hash check, ... | full variant tree (every lane's session.md, all programs, all templates, all scripts, all workflows) |

Honest gap: **~5× karpathy+pi combined** (down from "22×" in the original draft — that was karpathy-only and misstated pi). The features the substrate provides (anti-gradient-hacking, scope enforcement, multi-lane shared archive, multi-judge calibration, parallelism control) are real — but per the 2026-05-11 evidence audit, **most are theatre rather than load-bearing**: 0 ScopeViolations in lineage, 0 L1 FAILs, 0 `--resume-variant` invocations, 0 session-lock collisions, 1 dead-code `evolve_lock.py`. The features that DID earn their keep (anti-drift floor caught v071 regression, alert agent caught v176/v177 collapse) stay in v2.

The 5 days of debugging that just happened (#117 codex content-mod, #118 lineage drift, #119 runtime cascade, #114, #115, #120) were almost all caused by **interactions between substrate components**, not by the agent doing something genuinely wrong.

---

## The reference architectures, in detail

### 1. karpathy/autoresearch (the original)

Repo: <https://github.com/karpathy/autoresearch>

- **Total: 1,225 LOC verified** (`prepare.py` 389 LOC fixed + `train.py` 630 LOC agent-editable + `program.md` 114 LOC instructions + `README.md` 92 LOC)
- **Single metric**: `val_bpb` (validation bits-per-byte; vocab-size-independent)
- **Single time budget**: 5 minutes per experiment
- **Single scope**: agent only edits `train.py`
- **Single mechanism**: agent reads `program.md`, edits `train.py`, runs 5-min training, measures `val_bpb`, decides keep-or-revert
- **Git is the lineage system** — kept changes get committed. No `lineage.jsonl`, no `frontier.json`, no `current.json`. `results.tsv` (5 cols: commit, val_bpb, memory_gb, status, description) is the only ledger.
- Achieves ~12 experiments/hour on a single H100.
- `program.md` explicitly says "**LOOP FOREVER. Never ask 'should I continue?'**" — autonomy is encoded in the prompt, not the substrate.

The philosophical claim is in plain text in his README: *the goal is to discover what the agent can do when you don't pre-tune the infrastructure for it.*

### 2. pi-autoresearch (its generalization)

Repo: <https://github.com/davebcn87/pi-autoresearch>

**Verified scale**: ~3,800 LOC of TypeScript extension code (`index.ts` 3038 + `compaction.ts` 247 + `jsonl.ts` 192 + `hooks.ts` 185 + `shortcuts.ts` 105) + ~600 LOC of skill files + ~1,000 LOC of tests. Bigger than I claimed in v1 of this doc. **The core loop is still small** — the bloat is dashboard UI, confidence scoring, idea backlog, hooks.

3 tools the agent calls at its discretion:
- `init_experiment(name, metric, unit, direction)` — create the session
- `run_experiment(cmd)` — execute any command, parse `METRIC name=value` lines from stdout
- `log_experiment(status, description, asi)` — append to log; `keep` auto-commits, `discard`/`crash`/`checks_failed` auto-reverts code (autoresearch files preserved)

2 persistent files survive restarts:
- `autoresearch.jsonl` — append-only experiment log
- `autoresearch.md` — living human-readable session doc (objective, attempted strategies, dead ends, wins)

Optional: `autoresearch.sh` (benchmark), `autoresearch.checks.sh` (correctness — tests/types/lint), `autoresearch.hooks/before.sh` + `after.sh`, `autoresearch.ideas.md` (backlog), `autoresearch.config.json`.

Crucially: **failures only block commits**. Successes are logged whether they were useful or not. The agent decides what was useful. There is no scope-check, no readonly subprefix list, no AUTOGEN regen, no critique-prompt hash. The benchmark exits zero or it doesn't.

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

This is the honest accounting. **Verdicts revised 2026-05-11 based on lineage.jsonl + archived-log grep evidence** (see companion doc).

| Substrate component | LOC | Why it exists | Evidence-based verdict |
|---|---|---|---|
| **`evolve.py`** main orchestrator | 2,699 | candidate generation, parent selection, mutation, eval, gate, promote | mostly accidental — could be a 300-LOC `for gen in range(N): ...` loop |
| **`evaluate_variant.py`** scoring + holdout | 3,244 | search-v1 scoring, holdout-v1 hidden eval, judge HTTP, retry, fixture replay | **partially load-bearing** — judge HTTP retry + holdout isolation are real; the rest is fixture-replay-cache + lineage-append-update + manifest-decoration |
| **`evolve_ops.py`** | 1,144 | meta-workspace prep, lane-context, write-lane-context, atomic promote | mostly accidental — workspace prep is to support scope enforcement (delete that, deletes most of this) |
| **`lane_registry.py`** + `LaneSpec` | 553 | declarative per-lane prefixes, readonly subprefixes, structural facts, gate functions, judge config | **mostly accidental** — replaces "agent reads the lane's session.md and figures out what to do" with structured machine-readable metadata *to drive substrate enforcement* |
| **`archive_index.py`** | 609 | `lineage.jsonl` accumulation, `frontier.json`, `index.json`, `prepare_meta_workspace`, `sync_variant_workspace`, `summarize_variant_diff` | accidental — git itself does most of this; `frontier.json` is a derived index that should just be `git log -- <lane>` |
| **`select_parent.py`** + `agent_calls.py` | 310 + 221 | LLM-driven parent picker with anti-drift floor + top-K + trajectory context | accidental as substrate — replace with prompt instruction. **BUT** the anti-drift floor is provably load-bearing (see below). |
| **Anti-drift floor** (commit `7469dcd`, 2026-05-09) | ~30 | filter parent candidates < 50% of best | **🟢 KEEP (as prompt)** — v071 picked once → regression cascade. After fix, v175/v176/v177 all picked v007 with "exploitation pressure" rationale. Provably effective. v2 keeps it as 1 sentence in `autoresearch.md`, not as 30 LOC. |
| **`concurrency.py`** + per-resource semaphores | 182 | claude=4, codex=2, opencode=8, judge_http=10, cloro_search=2; killswitch | **🟢 KEEP** — Claude Max cap is real (800/1070 auth-rate-limit hits on 2026-05-08). Simplify to 1 env var `MAX_PARALLEL_AGENTS=4`. ~20 LOC. |
| **`regen_program_docs.py`** | 304 | regenerate AUTOGEN block in session.md from `STRUCTURAL_DOC_FACTS` | **🔴 REJECT confirmed** — caused #115 today. Static facts go in the prompt, no regen needed. |
| **`lane_runtime.py`** + `current_runtime` materialization | 267 | rebuild `current_runtime/` from `current.json` heads on every evolve boot | **🔴 REJECT confirmed** — symlinks (or direct paths) replace this. |
| **harness/agent.py + backend.py + opencode_jsonl.py** | ~570 | spawn agents, backend abstraction (claude/codex/opencode), transient-error detection | **🟢 KEEP** — backend abstraction earned its keep on #117 codex content-mod. Slim to ~200 LOC. |
| **harness/stall.py** | 165 | results.jsonl event + dir-growth stall detection | **🔴 REJECT (tentative)** — wall-clock `timeout 1200 ./autoresearch.sh` simpler. Karpathy doesn't detect stalls; experiment times out, agent retries. |
| **harness/util.py** per-fixture session lock | ~70 | mutex same-fixture concurrent runs | **🔴 REJECT confirmed** — 0 archived collisions ever. Today's #120 was a *false positive* the lock created. Sequential v2 has nothing to lock. |
| **harness/telemetry.py** | 187 | push session/iteration events to freddy backend (for web UI) | **🟢 KEEP (slim)** — JR's web UI consumer is real. Slim to ~80 LOC. |
| **`SessionsFile` + sessions.py** | 201 | claude session JSONL recovery, forensic in-flight tracking | **🟡 PARTIAL KEEP** — `viable_resume_id` is real (backend retry uses it). Forensic in-flight tracking can go (0 production resumes). ~50 LOC kept. |
| **`evolve_lock.py`** (live-vs-evolve mutex) | 106 | prevent overlapping evolution runs | **🔴 REJECT (dead code)** — only imports itself. Never acquired anywhere. 106 LOC of pure dead code. |
| **archive/v006/run.py** + variant_dir copies | 1,500 × ~30 variants | per-variant runtime entry point | accidental at scale — every variant has a near-identical `run.py`; v2 uses one `run.py` and git commits |
| **archive/v006/scripts/render_report.py** + render scripts | 1,330 | HTML+PDF report rendering with codex enrichment | **🟢 KEEP (as tool)** — JR uses the reports. Becomes `tools/render_report.py`, agent calls when wanted. |
| **L1 validation** (in `evaluate_variant.py`) | ~150 | py_compile + bash -n + import check + critique-manifest-hash check + program-file existence | **🟡 PARTIAL KEEP** — 0 `L1 FAIL` lines in archive ≠ useless. The critique-manifest portion is the Pi v007 defense (deterrent works). Keep only that ~50 LOC; drop the py_compile/bash-n preflight (agent's first run fails loud anyway). |
| **Critique manifest** (SHA256 of critique prompts) | 114 | gradient-hacking defense from Pi v007 incident | **🟢 KEEP (as tool)** — `tools/verify_critique_integrity.py`. ~50 LOC. |
| **Scope enforcement** (`prepare_meta_workspace` + `sync_variant_workspace` chmod 0444 + hash diff) | ~300 | prevent meta-agent from editing readonly files | **🔴 REJECT confirmed** — 0 ScopeViolation raises in lineage. All 8 archive mentions are agent prompt WARNINGS, not actual rejections. Deterrence works; enforcement is theatre. v2 puts "don't edit X" in the prompt. |
| **`compute_metrics.py`** + alert agent + `alerts.jsonl` | 517 | per-generation aggregation, LLM alert agent flags regressions | **🟢 KEEP (slim alert agent only)** — 2 alerts in alerts.jsonl, BOTH flagged the v176/v177 collapse I rolled back today. Real catches. Slim to ~200 LOC, drop trajectory aggregation. |
| **`events.py`** (append-only audit log) | 103 | flock + fsync + 100MB rotation; 7 consumers including judges | **🟢 KEEP** — load-bearing for judges. |
| **`archive_cli.py`** Typer commands (frontier, topk, show, diff, regressions, traces, failures) | 182 | JR-facing state inspection | **🟢 KEEP (slim)** — JR uses these. Reimplement against `results.tsv` + git log. ~80 LOC. |
| **5+ derived JSON files** (`current.json`, `index.json`, `frontier.json`, per-variant `scores.json`, per-variant `variant_manifest.json`) | n/a | denormalized indices over `lineage.jsonl` | **🔴 REJECT confirmed** — caused #114 today. Pick ONE source of truth (`results.tsv` + git); derive others. |
| **`--resume-variant`** machinery + `_unsealed_variant_dir` cleanup | ~60 in evolve.py | mid-run kill recovery | **🔴 REJECT confirmed** — 0 invocations across 147 archived variants. Has never been used. |
| **Per-variant directories `v001..v177` on disk** | 1.1 GB | per-variant snapshot | **🔴 REJECT confirmed** — 147 dirs, mostly duplicates of v006. Git commits replace. |
| **Tests** | ~12,709 | test the substrate | proportional to substrate; shrinks with substrate |

**Honest summary**: of ~13,658 LOC, after the evidence audit **~2,500 LOC are actually load-bearing** for the AI-first version. That's:
- Judges HTTP retry + holdout isolation (~300 LOC)
- Backend abstraction + opencode_jsonl (~200 LOC)
- Concurrency (1 env var) + telemetry (~80 LOC)
- Critique-manifest hash tool (~50 LOC)
- Alert agent (~200 LOC)
- archive_cli slim (~80 LOC)
- Render pipeline as tool (~200 LOC)
- Tool wrappers: run_experiment + log_experiment + score_holdout + verify_critique + init_experiment (~250 LOC)
- Per-lane prompt files (~7 × ~150 LOC = ~1,050 LOC of prose, not code)
- `autoresearch.md` driver prompts (~100 LOC each lane = ~700 LOC of prose)

The other ~11,000+ LOC exist to prop up an architecture where the substrate doesn't trust the agent.

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

### Proposed architecture (~2,500 LOC target — revised 2026-05-11)

```
autoresearch_v2/
├── README.md                       # objectives + how to run
├── autoresearch.md                 # living session log (mirrors pi-autoresearch)
├── results.tsv                     # append-only TSV (mirrors karpathy: commit, composite, status, description)
├── tools/                          # tools the agent invokes
│   ├── init_experiment.py          # ~50 LOC — create new attempt dir, log it
│   ├── run_experiment.py           # ~100 LOC — execute a session, capture deliverables, return path
│   ├── score_experiment.py         # ~150 LOC — single-fixture sniff via evolution-judge HTTP
│   ├── score_holdout.py            # ~100 LOC — 6-fixture holdout average for keep-decisions
│   ├── log_experiment.py           # ~60 LOC — append tsv, git commit (keep) or git reset (discard)
│   ├── verify_critique_integrity.py # ~50 LOC — Pi v007 defense as explicit tool
│   ├── render_report.py            # ~200 LOC — HTML+PDF (slimmed from 1,330)
│   ├── alert_check.py              # ~200 LOC — alert agent (slimmed from compute_metrics.py)
│   └── inspect.py                  # ~80 LOC — replaces archive_cli (frontier/topk/show/diff)
├── lanes/                          # one markdown per lane (was: ~5k LOC of LaneSpec + workflow.py)
│   ├── geo.md                      # description + structural facts in prose + example deliverables
│   ├── competitive.md
│   ├── monitoring.md
│   ├── storyboard.md
│   ├── marketing_audit.md
│   ├── x_engine.md
│   └── linkedin_engine.md
├── harness/                        # kept-but-slimmed runtime
│   ├── backend.py                  # ~80 LOC — claude/codex/opencode router + retry
│   ├── opencode_jsonl.py           # ~50 LOC — transient-error detection
│   ├── telemetry.py                # ~80 LOC — push to freddy backend UI
│   ├── sessions.py                 # ~50 LOC — viable_resume_id only
│   └── events.py                   # ~100 LOC — append-only audit log (judges consume)
└── judges/                         # HTTP services — UNCHANGED (already at ~150 LOC of client)
```

What's GONE: lineage.jsonl→frontier.json→index.json→current.json fanout. `prepare_meta_workspace` chmod 0444 dance. `regen_program_docs` AUTOGEN rewrite. `select_parent` LLM (replaced by prompt). `lane_runtime` rebuild. `evolve_ops.write_lane_context`. Per-fixture session lock. `evolve_lock.py` dead code. `--resume-variant` machinery. 147 per-variant directories on disk.

What's KEPT (revised after pressure-test): critique-manifest hash as tool. Anti-drift floor as 1 prompt sentence. Alert agent (real catches). archive_cli inspection (JR uses). events.py audit log (judges depend on). telemetry to freddy backend (JR's web UI). Backend abstraction (real value for #117). Concurrency limit (1 env var for Claude Max).

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

The 5 things gofreddy currently builds infrastructure for that AI-first replaces:

| gofreddy infrastructure | AI-first replacement |
|---|---|
| `LaneSpec.path_prefixes` + `prepare_meta_workspace` deleting non-lane files | One dir per lane (`autoresearch/<lane>/`). Filesystem separation. No scope-check code. |
| `LaneSpec.readonly_subprefixes` + chmod 0444 + hash check | Prompt: "don't edit `workflows/geo.py` or `session_eval_geo.py`" (deterrence works — 0 actual rejections in lineage, 8 prompt warnings prevented attempts) |
| `regen_program_docs` AUTOGEN block rewrite | Prompt: "the structural facts you must satisfy: [list]" — and the judge's gate checks them |
| `select_parent` LLM agent | Prompt: "look at `results.tsv`, pick the highest-scoring parent unless you have a specific reason to explore (anti-drift principle)" |
| 5 redundant indices (`current.json`/`index.json`/`frontier.json`/`scores.json`/`variant_manifest.json`) | Single `results.tsv` + `git log` |

Every replacement is **lower complexity AND more flexible**, because the agent can reason about edge cases (e.g., "the structural facts say X, but I see Y working in v009; let me try Y") that a hardcoded gate can't.

---

## What's actually load-bearing — the *do not delete* list (revised 2026-05-11)

Be ruthless about deletion, but recognize the genuinely load-bearing parts. **All items below have evidence in `lineage.jsonl`, archived logs, `alerts.jsonl`, or active code consumers.**

1. **Holdout isolation**. Hidden eval set at `~/.config/gofreddy/holdouts/`. Agent must NOT see holdout fixture content (only composite score back).

2. **Judges HTTP** (`session_judge:7100`, `evolution_judge:7200`). The analog of `val_bpb`. Retry logic + holdout pipeline kept.

3. **Backend abstraction** for sub-agents (claude / codex / opencode → openrouter/deepseek). Multi-provider failover for content-mod (#117) + rate-limit. Consolidate to ~80 LOC.

4. **Critique-prompt hash** — Pi v007 gradient-hacking defense. As explicit tool, ~50 LOC.

5. **Render pipeline** — JR uses HTML+PDF reports. Tool the agent calls, ~200 LOC (slimmed from 1,330).

6. **Concurrency limit** for Claude Max cap. 1 env var (`MAX_PARALLEL_AGENTS=4`).

7. **Anti-drift floor (as prompt instruction)** — provably effective (v071 → v159 cascade stopped after fix). NOT 30 LOC of code; 1 sentence in `autoresearch.md`.

8. **Alert agent** — caught v176/v177 collapse (2 real alerts in `alerts.jsonl`). Slim to ~200 LOC.

9. **`archive_cli` Typer commands** — JR uses for state inspection. Reimplement against `results.tsv` + git log, ~80 LOC.

10. **`events.py` audit log** — 7 active consumers including judges. Keep ~100 LOC.

11. **`harness/telemetry.py`** — pushes to freddy backend for JR's web UI. Slim to ~80 LOC.

12. **`SessionsFile.viable_resume_id`** — claude session JSONL recovery (used by backend retry). Keep ~50 LOC.

Everything else is on the table for deletion or radical simplification. See `docs/research/2026-05-11-001-substrate-feature-audit-evidence-based.md` for the per-feature evidence trail.

---

## Plan: how a fresh agent should approach this

### Step 1 — Verify the references (DONE 2026-05-11)

✅ **Completed.** Numbers verified:
- karpathy/autoresearch: **1,225 LOC** (`prepare.py` 389 + `train.py` 630 + `program.md` 114 + `README.md` 92)
- pi-autoresearch: **~3,800 LOC** of TypeScript extension + ~600 LOC skills + ~1k LOC tests
- karpathy's `program.md` confirmed: "LOOP FOREVER. Never ask 'should I continue?'" + 5-min budget + `results.tsv` (5 cols)
- pi-autoresearch tools: `init_experiment`, `run_experiment`, `log_experiment` (with `keep`/`discard`/`crash`/`checks_failed` auto-commit/revert)
- Anthropic "dreaming": `CLAUDE.md` + `CHANGELOG.md` + Ralph loop, 6× completion-rate gain from memory carrying across sessions

Clone commands for re-verification:
```
git clone --depth 1 https://github.com/karpathy/autoresearch /tmp/karpathy-autoresearch
git clone --depth 1 https://github.com/davebcn87/pi-autoresearch /tmp/pi-autoresearch
```

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

10. **Q: When does the v2 spike "win"?** Recommendation criteria: (a) one full lane (5-10 iters) producing holdout composite ≥ current baseline ± noise (b) substrate LOC < 2,500 (c) 0 bugs of the substrate↔substrate-seam class. If (a) fails, the complexity was earned.

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
3. Read `docs/research/2026-05-11-001-substrate-feature-audit-evidence-based.md` (the per-feature evidence trail — this is the *authoritative verdict source*)
4. Read `feedback-trust-agent-drop-regex-guards.md` from auto-memory
5. Step 1 (verify references) is DONE — skip
6. **Then** propose a concrete plan to JR with:
   - Which lane to spike first + why (geo is recommended — fresh holdout, just shipped v009 @ 4.77)
   - Total estimated LOC for the v2 substrate (target: ~2,500)
   - Total estimated dev days (~10-15)
   - Risks + rollback plan
7. Wait for JR's go before writing v2 code.

**Do not** start writing v2 code before steps 1-6. JR will course-correct on the plan, and writing code first will waste cycles.

**Do not** half-replace the substrate. Either it's small enough to be obviously simpler, or it's not worth doing.

**Do** be honest about LOC. The 2026-05-11 pressure-test moved the target from ~1,500 to ~2,500 LOC because 4 features I'd swept into REJECT turned out to be load-bearing. If you find v2 actually wants ~3,000 LOC, say so — the win is measured in *bug surface*, not in golf-coding LOC counts.

**Do** dogfood: use the existing anti-drift behavior, the geo v009 holdout-pass-criterion, and the working render pipeline as the *targets* for v2 to match. If v2 can match them at ~1/5 the LOC, it's a real win.

Good luck. The user's intuition that "a lot of the code is simply not needed" is right; the question is just which ~2,500 LOC are the load-bearing ones — and the companion doc nails most of that down.
