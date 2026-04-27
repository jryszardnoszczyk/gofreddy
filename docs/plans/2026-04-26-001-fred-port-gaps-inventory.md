# Fred → GoFreddy Port-Gaps Inventory

> ## ⚠ SUPERSEDED — research record only
>
> **Active reference:** `docs/plans/2026-04-27-001-fred-port-gaps-checklist.md`
>
> This 633-line inventory captures 5 rounds of parallel-agent surveys (2026-04-26) — useful as a durable map of the gap space. **Its framing is wrong**, however: it treated freddy's `src/orchestrator/` as a missing port (Bundle A) and shaped 4 rounds of triage around that premise.
>
> **Round-5 reframe (the corrections that matter):**
> 1. **GoFreddy's `autoresearch/` *is* the orchestration system.** Lanes, variants, evolution, programs-as-skills, judges. Not a peer of an "orchestrator" — *the* orchestrator.
> 2. **Path B is locked** in `docs/plans/2026-04-23-003-agency-integration-plan.md` Decision #1: "programs-only extension. gofreddy's programs-as-skills already beats freddy's orchestrator for autoresearch use case. Saves 6–8 weeks. Audit pipeline ships via program, not agent tool call." Re-evaluate gate: paying client demanding chat UI with capability pills.
> 3. **The 14 `tests/orchestrator/test_*.py` files are xfail-permanent**, not a port driver.
>
> Bundles A, J, N, W (orchestrator port + couplings) are dropped. Bundle S (frontend strategy) is removed (different scope). Bundle U (harness scorecard/convergence) is parked (no observed failure case). The active checklist is the 5-port + 2-chore-PR scope; the audit-engine implementation is a separate next branch following `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`.
>
> Preserved unchanged below for institutional record. Skim, don't action.

---

**Date:** 2026-04-26
**Branch:** `feat/fred-port-gaps`
**Source-of-truth:** `freddy` repo @ commit `50602a2` (`main`, last touched 2026-04-18)
**Target:** `gofreddy` `main` @ `feaacf7` (this branch is cut from there)

---

## Purpose

GoFreddy was forked from Freddy with a deliberate cut: the SaaS layer (FastAPI, Supabase, Stripe, Postgres, React frontend, accounts/billing/auth/jobs/preferences/workspace) was stripped in favor of a CLI-first, file-based, single-tenant agency tool. The gofreddy README claims "every provider integration is byte-identical to the source."

This inventory answers: **what got left behind that we actually want back?** It's a reference doc — the durable output of a one-shot survey across both repos. It documents *all* gaps we identified, not just the subset we ship on this branch. Future scope conversations should start here instead of re-surveying.

The inventory is **not a plan** and **not a design**. Both come later, scoped to a chosen subset.

---

## Methodology

**Round 1 (2026-04-26 morning):** Six parallel Explore agents covering module-level presence:

| Agent | Scope |
|---|---|
| 1 | `freddy/autoresearch/` dependency graph vs `gofreddy/autoresearch/` |
| 2 | Marketing-audit pipeline prereqs — read all `docs/plans/2026-04-2{0,3,4}-*` |
| 3 | External SDK / data-provider integration inventory |
| 4 | CLI commands present in `freddy/cli/freddy/commands/` and missing from gofreddy (13 files + `_generated/`) |
| 5 | `src/` modules present in freddy and missing from gofreddy (21 modules) |
| 6 | Agent-team / orchestration patterns (`src/orchestrator/`, `feedback_loop/`, `evolution/`, `optimization/`, `policies/`, `conversations/`) |

**Round 2 (2026-04-26 afternoon):** Six more parallel Explore agents covering what round 1 didn't reach — feature drift *within* shared modules and CLI commands, top-level dirs not yet opened, API-route business logic, ops/deployment surface, and single-file/test/doc miscellany:

| Agent | Scope |
|---|---|
| G1 | Within-module feature drift — files lost inside modules that exist in both repos |
| G2 | Within-CLI-command drift — subcommands and options lost inside shared CLI files |
| G3 | Untouched top-level dirs — `scripts/`, `configs/`, `skills/`, `experiments/`, `feedback_loop/`, `sessions/`, `harness/`, `docs/`, `supabase/` |
| G4 | API-route business logic — orchestration patterns embedded in FastAPI routes that are CLI-portable |
| G5 | Operational + dependency surface — `pyproject.toml`, `.env.example`, `Dockerfile`, `configs/` deltas |
| G6 | Single-file modules + tests + frontend + docs deltas |

**Round 3 (2026-04-26 evening):** Six more parallel Explore agents covering git history, broken imports, SDK usage drift inside byte-identical wrappers, prompt/config asset drift, frontend API contract, and recent-commits + observability:

| Agent | Scope |
|---|---|
| H1 | Git-history archaeology — what gofreddy DELETED post-fork vs what freddy ADDED post-fork |
| H2 | Broken-import + dead-reference scan inside gofreddy production + tests |
| H3 | SDK usage-pattern drift inside byte-identical wrappers (Gemini batches, OpenAI reasoning, etc.) |
| H4 | Prompt + config asset drift across `.md` / `.yaml` / `.json` files |
| H5 | Frontend API contract inventory — what the upcoming agency frontend will need |
| H6 | Recent freddy commits not pulled + observability/error-handling drift + CI/lint/dev-tool drift |

**Round 4 (2026-04-26 night):** Six more parallel Explore agents covering harness internals, autoresearch internals (gofreddy is 4× larger than freddy's), end-to-end workflow call-graphs, runtime configuration drift, utility/validator drift, and `.claude/` agent surface:

| Agent | Scope |
|---|---|
| I1 | Harness internals deep-dive — file-by-file capability comparison + gain/loss matrix |
| I2 | Autoresearch internals — what's in gofreddy's 4× expansion, and what freddy has gofreddy lost |
| I3 | End-to-end workflow call-graphs for `freddy detect`, `audit competitive`, `evaluate variant` — branch points and capability leaves |
| I4 | Configuration + runtime params — model selection, retry, rate-limit, cache TTL, cost budgets, feature flags |
| I5 | Utility patterns + validator drift — `src/common/`, `src/shared/`, helpers, gates beyond `evaluation/structural.py` |
| I6 | `.claude/` agents/skills/commands/hooks/settings inventory |

Each agent returned a structured row per item: name, purpose, deps, SaaS-coupling (none/partial/hard), agency-CLI value (HIGH/MED/LOW), port effort (S < 1d / M 1–3d / L > 3d), notes/blockers.

Rough sizing: gofreddy `src/` is **42.2K LOC** vs freddy's **90.3K** — a ~53% reduction. The cut was deliberate; this inventory identifies which of the missing 48K LOC we want to selectively recover.

### Survey-quality caveats

- **Agent #1 (autoresearch deps) framed too narrowly.** It only checked what gofreddy's autoresearch *currently imports*, concluded "no SaaS-critical gaps; gofreddy is more autonomous than freddy," and missed real gaps (broken `tests/test_tool_catalog.py` import of `src.orchestrator.tool_catalog`, lost `monitoring/intelligence/post_ingestion.py`, etc.). Agent #6 caught the orchestrator gap independently. Treat Agent #1's "no gaps" framing with skepticism — it answered "is autoresearch broken?" not "is autoresearch as capable as it could be?"
- **Round 1 missed within-module drift entirely.** It only checked which modules existed; it didn't check what was *inside* them. Round 2 Agent G1 caught that ~6 critical service files (`src/search/service.py`, `src/seo/service.py`, `src/competitive/brief.py`, `src/fraud/service.py`, `src/deepfake/service.py`, `src/publishing/service.py`) are MISSING from gofreddy even though their parent modules exist. This is the largest blind spot in round 1.
- **Provider-SDK byte-identity claim is partially true.** Wrappers (DataForSEO, Foreplay, Adyntel, Apify, fal, Grok, Gemini, GSC) are byte-identical. Service/orchestration layers wrapping them have diverged — see "Sanity check" below.
- **Round 1 said "skip `feedback_loop/`."** Round 2 Agent G3 disagreed — it's a Gemini-powered self-improving loop with substantial logic. Reconciled below: moved from skip-list to deferred Bundle N.
- **Round 3 reassuring finding:** No live broken imports in gofreddy production code. All imports of missing modules in `src/` are `TYPE_CHECKING`-guarded or `try/except`-wrapped. Only test files have visible breakage (already known). The port was surgically clean.
- **Round 3 SDK-level reframe:** "Byte-identical providers" remain byte-identical, but **caller-level usage** has narrowed. Gemini Batches API + context caching are wired up in gofreddy but only `gemini_analyzer.py` exercises them — the rest of the codebase doesn't reach those APIs. This is a feature-exposure gap, not a wrapper gap.
- **Round 3 confirmed `1e10a3e` revert was intentional,** not a mistake. Memory entry "Review precedes merge" documented the cause: PR #21 was wrongly merged and reverted after parallel reviewers found 5 P0 bugs. Not a port-gap issue.
- **Round 4 reclassified `archive_cli.py`.** Round 1 Agent 1 originally listed it as low-value skip; round 4 I2 found it has substantial operator-inspection value (frontier/topk/show/diff/regressions/stats). Moved from skip-list to Bundle V.
- **Round 4 surfaced harness regressions, not just gofreddy-ahead gains.** Bundle K (was "harness convergence improvements, deferred") gets concrete: gofreddy's harness rewrite *lost* convergence detection, escalation tracking, and protected-file backup/restore — these are real safety regressions, not philosophy choices. Upgraded to Bundle U.
- **Round 4 confirmed gofreddy-ahead capabilities should be documented explicitly.** New `§Gofreddy-ahead capabilities` section below catalogues these so future contributors don't accidentally regress them.

---

## Consolidated gap inventory

Bundles are roughly ranked by leverage. Bundles A and B are the **active scope** for this branch (per recommended Approach 2). Bundles C–F are deferred to follow-up branches.

---

### Bundle A — Orchestrator foundation **[ACTIVE]**

The "agent teams" capability the user explicitly named. Today gofreddy's CLI commands invoke agents *ad hoc* (each command rolls its own loop). Freddy has a unified orchestration layer that: registers tools centrally, builds dynamic system prompts based on available tools, runs ReAct loops with stuck-detection / cost-budgets / circuit-breakers, and exposes 30+ tool-chain strategies.

| Item | Freddy path | Purpose | Deps | SaaS-coupling | Effort | Confidence |
|---|---|---|---|---|---|---|
| Tool catalog | `src/orchestrator/tool_catalog/` | Single source of truth for ~20 tool specs. Schema validation, duplicate detection, JSON-schema export. `gofreddy/tests/test_tool_catalog.py` already imports `all_specs`, `get_spec`, `to_json_schema` and **fails at collection** — this is a known broken import. | ToolSpec, JSON schema | none | S | HIGH |
| ToolRegistry | `src/orchestrator/tools.py` | Builds system prompts from registered tools, validates parameter schemas, converts to ADK format. ~25 tool handlers. | tool_catalog | none | S | HIGH |
| ReAct agent loop | `src/orchestrator/agent.py` (`VideoIntelligenceAgent`) | Multi-turn Gemini reason→act→observe loop. Stuck detection, error sanitization (70+ allowed error codes), cost tracking with pre-call budget filtering, tool-result filtering to prevent token bloat. | Gemini SDK, CostTracker | partial (Gemini-specific) | M | HIGH |
| Dynamic prompt builder + strategies | `src/orchestrator/prompts.py` + `src/orchestrator/strategies/` (search.py, monitoring.py, studio.py) | ~3K lines of prompt + tool-chain strategies. Defines valid multi-tool workflows the agent can compose. Driven by which tools are registered. | ToolRegistry | none | M | HIGH |
| Cost tracker | `agent.py:CostTracker` | Per-request token budget (split input/output), downstream cost aggregation, pre-execution budget filtering via `_TOOL_COST_ESTIMATES`. | none | none | S | HIGH |
| Stuck-loop detection | `agent.py:_STUCK_DETECTION_EXEMPT` + circuit breaker | Detects agent repeating same tool calls; exempts harmless tools (e.g. "think"). Prevents runaway loops. | none | none | S | HIGH |
| Tool-result filter (`_prepare_for_llm`) | `agent.py` | Strips heavy payloads (large blobs, UUID serialization issues) before sending tool results back to LLM. Defense against token bloat. | none | none | S | MED |
| Tool name migration map | `agent.py:TOOL_NAME_MIGRATION_MAP` | Backward-compat: maps legacy tool names to current registry. ~50 entries. | none | none | S | LOW |
| Error code allowlist | `agent.py:_PASSTHROUGH_ERROR_CODES` | 70+ structured error codes allowed to surface to LLM (vs blocked as unsafe). Prevents silent failures. | none | none | S | LOW |

**SKIPPED inside this bundle:**
- `src/orchestrator/adk_agent.py` (`AdkAgentWrapper`) — Google ADK SDK wrapper. Heavyweight dep (`google-adk==1.27.2`). The hand-rolled ReAct is sufficient.
- `feedback_loop/aggregation.py` + `models.py` — Gemini + Supabase pipeline for product learning. SaaS-coupled. Not needed for CLI.
- `src/evolution/` (creator-trajectory) — domain-specific (creator risk/topic trends). Doesn't apply to gofreddy's flows.
- `src/optimization/` (DSPy MIPROv2) — offline prompt optimizer. Optional, post-MVP.
- `src/policies/` — brand-safety policy engine. Useful eventually but not orchestrator-foundation.

**Open design questions for this bundle (locked during brainstorming):**
- Decouple from `Tier`/`Workspace`/`Billing` type-hints during port (they're injected, not load-bearing) — keep the port slim.
- Where in `gofreddy/` does this live? `gofreddy/src/orchestrator/` is the obvious mirror; confirm.

---

### Bundle B — Marketing-audit port-only prereqs **[ACTIVE]**

Already cited by name in `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md` and `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`. These are the prerequisites the upcoming pipeline lists in its "ports from Freddy" section.

| Item | Action | Source | Effort | Cited in plan |
|---|---|---|---|---|
| MA-1..MA-8 evaluation domain | Extend `gofreddy/src/evaluation/` in place | `freddy/src/evaluation/{service,rubrics,models}.py` patterns + design §7.3 sketches | S (~200 LOC, transcribed from sketches) | `2026-04-24-003` §7.1, §7.3 |
| Marketing-audit structural validator | Add `_validate_marketing_audit()` to `gofreddy/src/evaluation/structural.py` | freddy structural patterns | S (~50 LOC) | `2026-04-24-003` §7.1 |
| Marketing-audit judges | Add to `gofreddy/src/evaluation/judges/` (parallel to `openai.py`, `promotion_judge.py` etc.) | design §v2 sketches | M | `2026-04-23-002` §v2 |
| Content extractor | Port `freddy/src/extraction/content_extractor.py` → `gofreddy/src/audit/enrichments/assets.py` | freddy direct | S (~30 LOC wrapper around `pdfplumber` + `python-pptx`) | `2026-04-20-002` R22 |
| `clients/` schema (audit-only subset) | Port `Client` model fields *minus* billing/subscription/membership *plus* audit-specific optional fields (enrichments, fit_signals) | `freddy/src/clients/models.py` | S (~100 LOC) | `2026-04-20-002` §4 ("4 ports from Freddy") |
| Autoresearch `marketing_audit` lane | Register in `gofreddy/autoresearch/{lane_runtime,lane_paths,evolve,evaluate_variant,critique_manifest}.py` | gofreddy boilerplate, no freddy port | M | `2026-04-23-002` §v3 |
| `autoresearch/programs/marketing_audit/` prompts | Create new directory: 4 agent prompts (Findability/Narrative/Acquisition/Experience) + Stage-1a/1b/1c/3/4 synthesis prompts + critique manifest + evaluation scope YAML | catalog `005` + ranking `006` lens defs + plan `002` R3 | M (~6KB content) | `2026-04-24-003` §2 decision #7 |

**Open design questions:**
- MA-1..MA-8 rubric prose: transcribe sketches as-is and refine in v1 dogfood, or wait for full spec pass? (Plan 003 §7.3 left them sketched.)
- Pin autoresearch lane to a tagged commit (e.g. `autoresearch-v1-baseline`) before audit ships, to insulate from churn.
- Variant prompt mutation scope: design §7.1 says 4 agent roles, plan 002 says 7. Reconcile before structuring `programs/marketing_audit/`.

---

### Bundle C — Content generation + multi-source extraction **[DEFERRED]**

| Item | Source | Purpose | Effort | Notes |
|---|---|---|---|---|
| `src/content_gen/` | freddy direct | 8 LLM-driven generation actions: ads, emails, scripts, headlines, captions, rewrites, etc. Pure Gemini, no SaaS coupling. | M | Drop the asyncpg history-storage; keep pure generation. Gofreddy's `freddy auto-draft` is the closest current analog and is much narrower. |
| `src/extraction/` (full) | freddy direct | Multi-source content extractor (URLs, PDFs, video transcripts via `XpozAdapter`). Bundle B ports only the assets-helper slice; full module is broader. | M | Useful beyond audit (digest enrichment, monitoring deepening). |

**Why deferred:** Distribution-engineering CLI without content-gen is incomplete, but content-gen isn't a prerequisite for autoresearch or the audit pipeline. Ship after foundation lands.

---

### Bundle D — Publishing + media pipeline **[DEFERRED]**

| Item | Source | Action | Effort | Notes |
|---|---|---|---|---|
| `cli/publish.py` | `freddy/cli/freddy/commands/publish.py` | Port (refactor away `api_request`; use file-based queue under `clients/<name>/publish/`) | M | Surprisingly portable — no multi-tenant deps. Maps to `clients/<name>/publish_queue.jsonl`. Subcommands: list, approve, schedule, dispatch, delete, tag, set-thumbnail. |
| `cli/media.py` | `freddy/cli/freddy/commands/media.py` | Port (file-based per-client asset library) | M | upload, list, search, delete, url. Foundational for agency client asset workflows. |
| `cli/rank.py` | `freddy/cli/freddy/commands/rank.py` | Port (wraps DataForSEO like existing `freddy audit seo`) | S | snapshot, history. Trivial port; complements existing SEO audit. |
| `cli/_generated/seo_audit.py` | freddy `_generated/` | Port (richer than existing `audit seo`: speed, structure, mobile, backlinks) | M | Reuses DataForSEO. Note: `_generated/` files are otherwise mostly stubs (`TODO: implement`). |

**Why deferred:** Net-new agency capability, valuable, but additive — not a foundation prereq.

---

### Bundle E — Brand & monitoring intelligence **[DEFERRED]**

| Item | Source | Action | Effort | Notes |
|---|---|---|---|---|
| `src/brands/` | freddy direct | Port (drop asyncpg; keep Gemini analyzer) | M | Brand exposure scoring + sentiment from video. Pure analysis. |
| `src/monitoring/intelligence/post_ingestion.py` | freddy direct | Port (single 335-LOC module, pure Gemini) | S | Real-time intent/sentiment classification on ingested social mentions. Currently gofreddy's monitoring **discards** this enrichment. |
| `src/monitoring/comments/` (subset) | `sync.py` + `intelligence`, **drop** `repository.py` | Port refactored (file-based instead of Postgres) | M | Comment monitoring + reply generation + engagement tracking. |

**Why deferred:** Deepens `freddy audit monitor`. High value but additive. Bundle E commands aren't prerequisites for autoresearch or audit.

---

### Bundle F — Generation service layer **[DEFERRED]**

| Item | Source | Action | Effort | Notes |
|---|---|---|---|---|
| `src/generation/service.py` + `worker.py` | freddy direct | Port refactored (drop Postgres `repository.py`; replace with file-based) | M | Service-level orchestration for fal/Grok/TTS/avatar/music. SDK wrappers are already byte-identical in gofreddy; this is the missing layer above them. |

**Why deferred:** Lowest confidence rating from surveys. Useful but only if the agency starts batching video-asset generation, which isn't on the immediate roadmap.

---

### Bundle G — Service-layer orchestration drift **[HIGH PRIORITY — DEFERRED to next branch after A+B]**

This is the largest finding from round 2. Modules `src/search/`, `src/seo/`, `src/competitive/`, `src/fraud/`, `src/deepfake/`, `src/publishing/` all exist in gofreddy with their provider adapters intact, but their **orchestration service files are missing**. The provider SDK wrappers (DataForSEO, Foreplay, RealityDefender, etc.) are byte-identical; the service layers that compose them are gone. Round 1 missed this because it only checked module-level presence.

| Item | Source path | LOC | Purpose | Why critical | Effort | Notes |
|---|---|---|---|---|---|---|
| `src/search/service.py` | freddy direct | ~1277 | Multi-platform creator search; query parsing (Gemini), platform fallbacks, IC integration with circuit breaker, cache, confidence scoring | Without this, gofreddy's CLI cannot run cross-platform creator searches even though `src/search/ic_backend.py` and other adapters exist | M (no Postgres needed if we drop search-cache repo) | Most-impactful single port in round 2. |
| `src/seo/service.py` | freddy direct | M-class | Orchestrates technical/keyword/backlink/performance audits via DataForSEO + GSC | Powers `freddy audit seo`'s richer modes; gofreddy currently has narrow audit only | M | Drop Postgres repos; in-memory results to file. |
| `src/competitive/brief.py` | freddy direct | ~280 | Multi-section competitive intelligence synthesis (SOV, sentiment, ads, partnerships) using Gemini | Bundle B's marketing-audit Competitive lens needs this; Bundle B currently has no source for "synthesize competitive findings" logic | L | Could be partially scoped into Bundle B if needed; otherwise next branch. |
| `src/fraud/service.py` | freddy direct | ~408 | Gemini bot-detection + engagement/follower anomaly scoring orchestration | Vetting creators for bot fraud; provider adapters present in gofreddy but no orchestrator | M | Pure Gemini, no SaaS coupling beyond the Postgres repo (which we drop). |
| `src/deepfake/service.py` | freddy direct | ~167 | Orchestrates RealityDefender + LipInc deepfake analysis with fallback logic | Safety validation; adapters present | M | Smallest service, easiest port. |
| `src/publishing/service.py` + `dispatcher.py` | freddy direct | M-class | Multi-platform publishing (TikTok, YT, LinkedIn) | Distribution pipeline closure; adapters present | M | Drop Cloud Tasks dispatcher path; replace with synchronous CLI invocation. |

**Why deferred from this branch:** Bundle G is conceptually adjacent to Bundle A (orchestrator) but it's an additional ~3K LOC of port work. Stuffing it in would push branch size from ~3-4 weeks to ~5-7 weeks and dilute review quality. Recommended sequence: A+B (this branch) → G (next branch) → C/D/E/F (later).

**Connection to Bundle A:** Once Bundle A's `AgentLoop` exists, Bundle G's services should consider whether they call it (replacing their hand-rolled async orchestration) or remain standalone. Likely answer: standalone — these are deterministic data pipelines, not agent loops. AgentLoop is for agent-driven flows (audit, evaluate); services in Bundle G are for direct-call workflows.

---

### Bundle H — Test coverage parity **[SMALL — fold into A+B branch where it touches]**

Round 2 G6 found 72 test files in freddy missing from gofreddy. Most are expected (test files for stripped modules). The real gaps are:

| Item | Module status in gofreddy | Action | Effort |
|---|---|---|---|
| `tests/deepfake/{test_service.py, test_models.py, test_router.py}` | Module present, **zero tests** | Port `test_service.py` + `test_models.py` only; skip `test_router.py` (FastAPI) | S |
| `tests/analysis/test_service.py` | Module present, undertested | Port | S |
| `tests/search/test_vector_search.py` | Module present, undertested | Port (relevant if Bundle G ports `src/search/service.py`) | S |
| `tests/fraud/*` extensions | Module present, undertested | Port relevant ones | S |
| `tests/test_schemas.py` enum-validation patterns | `src/schemas.py` already byte-identical | Port (cheap insurance) | S |

**Recommendation:** During Bundle A+B work on this branch, port the `tests/deepfake/test_service.py` (relevant once Bundle G lands but cheap to add now since `src/deepfake/` exists in gofreddy) and `tests/test_schemas.py`. The rest should ride with the modules they cover (search tests with Bundle G search-service port).

---

### Bundle I — Within-CLI capability restoration **[DEFERRED — small QoL]**

| Item | Loss | Effort | Notes |
|---|---|---|---|
| `evaluate:variant` domain file discovery | Lost `_read_files()` + `_DOMAIN_FILE_PATTERNS` (~160 LOC of pre-judge gate logic) | S | Pure file-system operations; no SaaS coupling. Gofreddy's HTTP-only `evaluate variant` skips structural validation that freddy did locally. |
| `evaluate:review --offline` | Lost local-Gemini fallback when judge-service is down | S | Add `--offline` flag; if `GEMINI_API_KEY` set, use local; else HTTP. ~60 LOC. |
| `monitor:mentions --no-summarize` | Cannot get raw mentions; gofreddy always Sonnet-summarizes | S | Add flag. ~15 LOC. |
| `setup --interactive` | Lost interactive onboarding flow | S | Optional; pure UX. |

**Why deferred:** all are <1d each but additive QoL, not foundation. Any future operator who hits a judge-service outage will want `--offline`; we'll port reactively.

---

### Bundle J — Tool catalog scaffolding (`scripts/build_tool_artifacts.py`) **[CO-SHIP WITH BUNDLE A]**

Round 2 G3 found `freddy/scripts/build_tool_artifacts.py` — auto-generates `SKILL.md` + CLI stubs from `orchestrator.tool_catalog`. This **directly co-ships with Bundle A** because the tool catalog is the input. Adding to Bundle A as unit A.9 in the design doc.

---

### Bundle K — Harness convergence improvements **[DEFERRED]**

Round 2 G3 found freddy's `harness/` has features gofreddy's lacks: escalation tracking, frozen-judge backup/restore, convergence logic, and additional evaluator/fixer/verifier prompts. ~M effort to backport. Defer — gofreddy's harness has been actively iterated since the fork (per recent commits like PR #21 / #22 / #23) and may have intentionally diverged. Re-evaluate after current harness work stabilizes.

---

### Bundle L — Knowledge preservation: `docs/from-fred/` **[CO-SHIP WITH BUNDLE B — small]**

Round 2 G3 + G6 identified ~10 high-value research/plans docs in `freddy/docs/research/` and `freddy/docs/plans/` not present in gofreddy. These are forensic audits, root-cause analyses, and design rationales — not reusable code, but institutional knowledge. Cheap to preserve.

| Source path | Why |
|---|---|
| `docs/research/2026-04-17-workflow-failure-root-causes.md` | 31 documented failure root causes with line numbers and fixes — directly applicable to autoresearch debugging |
| `docs/research/2026-04-13-autoresearch-session-loop-audit.md` | Session-loop stability audit |
| `docs/research/2026-04-11-autoresearch-evaluation-infrastructure-audit.md` | Evaluator harness deep-dive |
| `docs/research/2026-04-11-autoresearch-prompt-audit.md` | Prompt token inventory + 2 HIGH-severity findings |
| `docs/research/2026-04-14-autoresearch-run2-audit.md` | Run-2 agent behavior patterns |
| `docs/research/2026-04-16-storyboard-mock-removal-and-evolution-readiness.md` | Pre-evolution assessment |
| `docs/plans/2026-04-18-001-migrate-autoresearch-to-gofreddy-plan.md` | Explicit Freddy→GoFreddy migration plan (likely the most directly relevant) |
| `docs/plans/2026-04-14-004-refactor-harness-unconstrained-loop-plan.md` | Harness redesign rationale |
| `docs/plans/2026-04-08-001-fix-harness-round1-findings-plan.md` | Harness bug-fix backlog |
| `docs/superpowers/specs/2026-04-16-freddy-distribution-engineering-agency-design.md` | Distribution-engineering-agency design |

**Action:** Copy these into `gofreddy/docs/from-fred/` (new directory) with a top-level README explaining they're frozen reference material from `freddy@50602a2`, not actively maintained. Add as design unit B.7.

---

### Bundle M — Ops hygiene **[DEFERRED — separate cleanup pass]**

Round 2 G5 found:

1. **25+ env vars used in gofreddy `autoresearch/` but NOT documented in `.env.example`** (HIGH severity — silent ops bug). Vars: `AR_CODEX_SANDBOX`, `AUTORESEARCH_SESSION_*` (7), `CODEX_*` (3), `EVAL_*` (5), `EVOLUTION_*` (8), `FREDDY_FIXTURE_*` (~2), `SESSION_INVOKE_TOKEN`, `SESSION_JUDGE_URL`, `EVOLVE_SKIP_PRESCRIPTION_CRITIC`.
2. **2 unused env vars** in gofreddy `.env.example` to remove: `ENABLE_SEO`, `ENABLE_GEO`.
3. **Dockerfile gaps:** no health check, runs as root, single-stage build.

**Why deferred from this branch:** This is gofreddy hygiene cleanup, not "porting from freddy." Should be a separate small PR. The autoresearch lane registration in B.5 of the active design will *touch* the env-var surface — at that point we may opportunistically document the registered lane's vars, but the comprehensive 25+ pass is a separate effort.

---

### Bundle N — `feedback_loop/` self-improving loop **[DEFERRED — re-evaluate later]**

Round 2 G3 disagreed with round 1's "skip" call on `freddy/feedback_loop/` (top-level dir, separate from `src/feedback.py`). It's a Gemini-powered signal aggregation + spec-generation pipeline. Substantial value if gofreddy wants autonomous capability improvement.

**Reconciliation:** Moved from skip-list to deferred. Two reasons it's not in the active scope:
1. Gemini + (likely) Postgres-coupled — port effort is L.
2. Gofreddy's `judges/` + `events.py` + `agent_calls.py` (round 1 noted these as gofreddy *gains*) may already cover much of the same ground; port may produce duplicate machinery.

**Action:** Re-evaluate after Bundle G ships. If gofreddy's existing autoresearch + judges layer doesn't close the feedback loop, port at that point.

---

### Bundle P — Backport recent freddy fixes **[HIGH-VALUE, SMALL — separate `chore/freddy-fix-backport` PR]**

Round 3 H1 + H6 surfaced ~14 small fixes freddy has shipped since the fork that gofreddy hasn't pulled. Each is S effort; cleanly cherry-pickable. Not a port — these are the same files in both repos with bugs fixed in freddy.

**Evaluation hardening (~6 commits):**
- `49e87a2` — exclude underscore-prefixed competitor files from structural count
- `92f6e3a` — competitive structural hardening + route brief.md only to judges
- `0a1283d` — retry judge ensemble once on all-fail before hard-zeroing
- `6e3c7e8` — split structural inputs from judge output_text
- `d2ba273` — return full SHA256 hash (drop 16-char truncation)
- `85929b6` — wrap startup generation-job reap in try/except (missing table)

**Autoresearch pipeline repair (~8 commits):**
- `dc9b836` — evaluate hash dedup + adhoc scores file + lock release + sync logging
- `58bca87` — findings pipeline repair (workflow-spec callback + variant-dir anchor + bullet parser)
- `c1e8b0d` — results.jsonl schema normalizer (inject iteration, warn on missing keys)
- `6058ec6` — parent stdout buffering + split codex stderr + archive retention
- `6b9f2e7` — evaluate_session.py hygiene (no-op passes, no iteration hardcode, no absolute paths)
- `ee01c74` — metrics land in variant dir, status bucket accepts completed/done/pass
- `3a650e3` — validator current_sources key, multiturn stall semantics, digest hallucination guard
- `c199a5d` — add numbered gather loop to competitive program text

**Action:** Cherry-pick each commit, resolve any conflicts, run tests. Some may already be obviated by gofreddy's own fixes — check before applying. Aggregate effort: M (one PR, ~14 cherry-picks).

**Why a separate PR (not this branch):** They're additive bug fixes orthogonal to the port. Bundling them would dilute review.

---

### Bundle Q — Harness prompt scope decision **[NEEDS USER INPUT]**

Round 3 H1 + H4 found:
- Three `harness/prompts/evaluator-track-{d,e,f}.md` files were intentionally deleted in commit `2359c7c` (gofreddy reduced harness scope from 6 tracks to 3).
- `harness/prompts/{evaluator-base,fixer,verifier}.md` were significantly simplified (e.g., evaluator-base: 252 → 81 lines). The shift is intentional: "hostile QA" → "preservation-first."

**Open question for the user:** Was the track 6→3 reduction permanent, or staged? If staged, port tracks D/E/F when needed. If permanent, document the reduced scope explicitly in `harness/README.md` to prevent confusion.

**Recommendation:** Document the reduction explicitly. The simplification is well-rationalised in commit messages; surface that to readers.

**Effort:** S (one paragraph in `harness/README.md`).

---

### Bundle R — Caller-level SDK feature exposure **[DEFERRED — performance pass]**

Round 3 H3 found that Gemini Batches API + context caching are imported in gofreddy's wrappers but not reached from most callers. Same for `reasoning_effort` (OpenAI judges) and per-service httpx connection-pool tuning.

| SDK feature | Where to expose | Workflow benefit |
|---|---|---|
| Gemini Batches API | Bulk video / monitoring batch operations | ~50% cost reduction on non-urgent workloads |
| Gemini context caching | Repeated same-system-prompt calls (judges, evaluation) | ~90% token savings on repeated calls |
| OpenAI `reasoning_effort=high\|low` | Per-criterion judge configuration | Cost/latency tradeoff for complex rubrics |
| httpx `limits=` per-service | Heavy-concurrency callers (Foreplay, fal.ai, Gemini) | Fewer connection-reset errors under load |

**Action:** A separate "performance pass" branch after Bundle G. Each individual fix is S; aggregate is M.

---

### Bundle S — Agency frontend API contract scaffold **[DEFERRED — needs user decision first]**

Round 3 H5 catalogued 13 routes the freddy frontend consumes that the agency frontend will likely need:
- **Monitor telemetry:** `GET /monitors`, `GET /monitors/{id}/mentions`, `GET /monitors/{id}/changelog`, approve/reject endpoints
- **Session audit:** `GET /sessions`, `GET /sessions/{id}/actions`
- **Async job status:** `GET /analysis/jobs/{id}`, `GET /batch/{batch_id}`
- **Real-time progress (SSE):** `POST /agent/chat/stream`, `GET /batch/{batch_id}/progress`
- **Historical results:** `GET /analysis/{id}`, `GET /trends`

10 TypeScript type contracts also worth preserving as the agency-frontend's source-of-truth (MonitorSummary, MentionItem, AgentSession, ActionLogEntry, BatchStatus, BatchProgressEvent, AnalysisStatusResponse, ChangelogEntry, TrendResponse, GenerationJobStatus).

**Open decision for the user — agency-frontend deployment model:**
- **Option A (recommended):** CLI-managed local FastAPI server + file-based reads from agency workspaces. Offline-first, zero auth. Best fit for the agency's "results communication via telemetry" mandate.
- **Option B:** Persistent gofreddy backend (simpler than freddy's full SaaS, but still requires hosting + auth).
- **Option C:** Hybrid — static JSON exports for snapshots + minimal local server for SSE streams only.

**Why deferred from this branch:** entirely separate concern from CLI-foundation work. Land Bundle A+B first, then design the agency frontend's backend contract once the user confirms a deployment model.

---

### Bundle U — Harness scorecard / convergence / escalation back-port **[HIGH-VALUE — replaces Bundle K]**

Round 4 I1 specified what Bundle K's "harness convergence improvements" actually means. Gofreddy's harness rewrite (commit `5900b48`) was architecturally a win (per-worker pool, session-resume, surface-check), **but it lost three load-bearing safety mechanisms from freddy's harness:**

| Item | Source | What it does | Why losing it matters |
|---|---|---|---|
| `harness/scorecard.py` (~532 LOC) | freddy direct | Finding/Scorecard YAML parsing, scorecard r/w, report composition | Audit trail for cycle outputs; without it, harness reports are markdown-only with no machine-readable scorecard |
| `check_convergence()` | freddy `harness/scorecard.py` | Compares prev/curr grades excluding Flow4+escalated; gates cycle exit | Without it, gofreddy's harness has no "run until stable" semantics — cycles run for fixed N iterations or until walltime, not until the system actually converged |
| `count_finding_attempts()` + `compute_escalated_findings()` + `.escalation-exempt-N.txt` sidecars | freddy `harness/scorecard.py` | Tracks per-finding fix attempts; escalates after N retries; exempt sidecars for rolled-back attempts | Without it, gofreddy's harness can infinite-loop on hard-to-fix findings (waste agent calls, hit walltime) |
| `worktree.snapshot_protected_files()` + `verify_and_restore_protected_files()` | freddy `harness/worktree.py` | Tar-snapshot of judge infra + tests + scripts every cycle; restore on tampering | Frozen-judge safety net; per-worker isolation reduces but doesn't eliminate risk of operator/agent corrupting shared infra |

**Effort:** M (port files + integrate with gofreddy's per-worker model). Worktree.snapshot can either compose with per-worker isolation or replace its safety guarantees.

**Why a separate branch (`feat/harness-safety-restoration`):** This is real harness work, not a port. Should stabilise gofreddy's current harness rewrite first (PRs #21–#23 still settling). Re-evaluate after 2-3 stable cycles.

---

### Bundle V — `archive_cli.py` operator inspection CLI **[MED-priority — DEFERRED separate small PR]**

Round 4 I2 found `freddy/autoresearch/archive_cli.py` is missing in gofreddy. Originally classified low-value (round 1) — re-evaluated in round 4 as substantial operator ergonomics: `frontier`, `topk`, `show`, `diff`, `regressions`, `stats` subcommands. Self-contained file, S effort.

**Decision:** port to `gofreddy/autoresearch/archive_cli.py` after Bundle G ships (the service-layer ports may shape what stats commands look like).

---

### Bundle W — Orchestrator tool-handler helpers (`_helpers.py`) **[CO-SHIP WITH BUNDLE A — fold as A.10]**

Round 4 I5 found `freddy/src/orchestrator/tool_handlers/_helpers.py` (296 LOC) — regex validators (username, video ID, request parsing), namespace UUID, severity ordering, sanitization wrappers. Bundle A's existing scope ports the ~25 tool handlers but didn't itemise this helpers file. Fold into Bundle A as new unit A.10.

**Effort:** S.

---

### Bundle X — Cost hard-cap enforcement **[CO-SHIP WITH BUNDLE A — extend A.4]**

Round 4 I4 found a real production risk: **neither repo enforces a cost hard-cap**. Both track cost via `cost_recorder` but never halt a run when budget is exceeded. The `budget_usd` field is logged but not gated.

**Action:** Extend Bundle A's `CostTracker` (A.4) to enforce a hard cap. Today's behavior is: `if cost > budget: log warning, continue`. New behavior: `if cost > budget: raise CostCapExceeded, halt`.

**Effort:** S (extends existing CostTracker code).

**Why fold into Bundle A:** Bundle A is the only place CostTracker lives in this branch. Adding the cap there is one-edit. Without it, the failure mode is "agent loops burn through budget silently." With it, the failure mode is loud and catchable.

---

### Bundle T — Stale comments cleanup in `src/api/main.py` **[TINY — opportunistic]**

Round 3 H2 found three stale comments in `src/api/main.py` referencing skipped-port modules:
- Line 217: `# Skipped per migration plan: MonitorWorker, WorkspaceBridge, AlertEvaluator`
- Line 357: `# (WorkspaceBridge not ported — only used for workspace feature autoresearch doesn't touch).`
- Line 365: `# AlertEvaluator/WebhookDelivery wiring skipped`

These are informational, not bugs. They can be tightened ("permanently skipped — see inventory") or left as-is. Trivial; ride with any future PR touching that file.

---

### Bundle O — API-route business logic extraction **[DEFERRED — incremental]**

Round 2 G4 surveyed `freddy/src/api/` and found ~65% of business logic is already in service files; the remaining 35% is embedded in route handlers. The most valuable extractions:

| Source | What | Where it should live | Effort |
|---|---|---|---|
| `routers/agent.py:_build_per_request_agent` (267 LOC) | Tier-aware agent registry build, recipe-matching, cost-budget overrides | **Reference for Bundle A's `AgentLoop` port** — adapt logic to gofreddy's no-tier model | (already in Bundle A scope) |
| `routers/fraud.py:_fetch_ic_engagement` (~30 LOC) | IC enrichment with 15s timeout + graceful parsing fallback | Extract to `src/common/resilience.py` as `timeout_with_fallback()` | S |
| `routers/discover.py` tier-based source limiting | Source-count and daily-quota gating | `src/monitoring/tier_gates.py` (no-op tier in gofreddy) | S |
| `routers/reports.py` depth-aware timeout | Brief-generation timeout differs by depth (600s deep / 180s snapshot) | `src/competitive/timeout_config.py` | S |
| `routers/monitoring.py` query-backfill trigger | Conditional re-trigger on `{keywords, boolean_query, sources}` change | `src/monitoring/triggers.py` | S |

**Action:** Note these in Bundle A.7's port-source table (`_build_per_request_agent` is the most relevant). The rest are deferred to follow-up branches that touch those specific surfaces.

---

## Gofreddy-ahead capabilities (do NOT regress)

Across all 4 rounds, several capabilities have surfaced where **gofreddy is ahead of freddy**. These are not gaps in this inventory's "freddy → gofreddy port" direction — they're the opposite: things gofreddy has *added* or *fixed* that freddy lacks. Documented here so future contributors don't accidentally regress them when working from old freddy patterns:

**Architecture / orchestration:**
- **Per-worker harness pool** — `harness/run.py:_WorkerPool` + `harness/worktree.py` per-worker backend/frontend ports. Eliminates shared-worktree race conditions; scales fix/verify across findings concurrently. Not present in freddy.
- **Session-resume via session-id** — `harness/sessions.py` (156 LOC). Tracks agent_key → (session_id, status, timestamps). Engine respects `--resume <session_id>` for conversation continuity. Freddy has no equivalent.
- **Finding routing by confidence** — `harness/findings.py:route()`. Splits actionable defects (crash, 5xx, console-error, self-inconsistency, dead-ref) from review-required (doc-drift, low-confidence). Replaces freddy's escalation-only model with a more nuanced two-track approach.
- **Static surface-check** — `harness/safety.py:surface_check()`. ~10ms regex-based static analysis replaces freddy's 100s agent-call probe. Saves ~37K preamble tokens per cycle.
- **Smoke test framework** — `harness/smoke.py` (146 LOC). YAML-block parser for SMOKE.md + http/shell/playwright runners. Fail-loud pre/post-fix health checks. Not in freddy.
- **Review composition** — `harness/review.py` (228 LOC). Composes `review.md` + `pr-body.md`; tracks cherry-pick conflicts; scrubs secrets. Not in freddy (composition was implicit).
- **Codex engine support** — `harness/engine.py` dual-engine dispatch (Claude vs Codex). Freddy's harness is Claude-only.
- **Transient error classification** — `engine._is_transient()` with fuzzy prose + numeric regex + retry-delay tiers. More robust than freddy's basic retry.

**Autoresearch judge-service architecture:**
- **Judge-service HTTP clients** — `judges/quality_judge.py` + `judges/promotion_judge.py`. Decouples evaluation from CLI; cross-family judges (Claude / GPT-5.4) routed via service. Freddy has stateless in-process judges only.
- **Critique manifest hash validation** — `autoresearch/critique_manifest.py`. SHA256 manifest of frozen symbols (build_critique_prompt, thresholds) prevents Layer-2 self-tampering during variant mutations.
- **Events log** — `autoresearch/events.py`. Append-only audit trail at `~/.local/share/gofreddy/events.jsonl` with rotation + POSIX flock. Freddy has no equivalent.
- **Compute-metrics aggregation** — `autoresearch/compute_metrics.py`. Generation-level Pearson correlation, fixture-SD drift, optional alert agent.
- **Prescription critic** — `autoresearch/program_prescription_critic.py`. Soft-review of mutations distinguishing PRESCRIPTION (banned) from DESCRIPTION (allowed). Advisory-only, never blocks evolution.
- **Agent-driven parent selection** — `autoresearch/select_parent.py` (232 LOC vs freddy's 88 LOC). Replaces freddy's hand-tuned sigmoid with AsyncOpenAI call; agent picks from top-8 candidates with trajectory context.
- **Sonnet paraphrase + calibration judges** — `judges/sonnet_agent.py` (R-#32, #33). Per-domain paraphrase calibration via Claude CLI. Freddy lacks equivalent.

**Validators (gofreddy ahead — do not back-port to freddy's older version):**
- `src/evaluation/structural.py:_validate_competitive()` — relaxed 500-char + 3-header gate to 50-char floor (R-#35: gradient judges handle quality, not structural).
- `src/evaluation/structural.py:_validate_monitoring()` — replaced regex-based digest hallucination heuristics with async `verify_claims_async()` agent call (R-#37).
- `src/evaluation/structural_agent.py` — claim-grounding agent for monitoring validator. Not in freddy.

**CLI / fixture:**
- **Fixture cache + holdout isolation** — `cli/freddy/fixture/cache_integration.py`. Per-pool `on_miss` policy (search-pool falls through to live; holdout-pool hard-fails). Prevents holdout credentials leaking to provider logs.
- **Direct provider SDKs in `audit.py`** — Bypasses backend API; calls Foreplay/Adyntel/Xpoz/DataForSEO directly with cost-recorder. Enables offline audits.
- **Sonnet-based mention summarization** — `monitor:mentions --format=summary` calls `call_sonnet_json()` with prompt caching, staleness warnings, fallback to aggregates. Freddy uses simple `_build_summary()` aggregates only.
- **Async parse-judge correctness** — `parse_judge_response()` is correctly awaited in gofreddy's evaluate.py:124 + gemini.py:185. Freddy's callsites lack the await (likely a freddy bug; gofreddy is correct).

**Common / shared:**
- `src/common/circuit_breaker.py` (synced now), `src/shared/safety/tier_*.py` (scoped Claude SDK toolbelt builders), `src/shared/reporting/scrub.py` (centralized secret-pattern regex), `src/shared/reporting/report_base.py` (HTML/PDF + JSONL/markdown loaders).

**Dev hygiene:**
- 3 GitHub Actions workflows (CI lint enforcing judges/src import isolation; holdout refresh automation; pages deploy). Freddy has 0 workflows.
- Python 3.13 target (mypy + ruff). Freddy on 3.12.
- `.claude/hooks/harness-iterate-check.sh` — Stop-hook iteration-gating pattern for autonomous re-entry loops. Freddy lacks any hooks.

**Reverse-direction port observations:** Several gofreddy-ahead items would benefit freddy if freddy ever runs unattended (per-worker pool, session-resume, surface-check, smoke framework, harness-iterate hook, judge-service architecture). Out of scope for this freddy → gofreddy inventory; flagged here for completeness.

---

## Skip-list (do NOT port)

Surveyed and explicitly excluded. Rationale grouped.

**SaaS infra (intentional cut):**
- `src/billing/` — Stripe subscription tier system. Multi-tenant credit/usage tracking baked in.
- `src/workspace/` + `src/preferences/` + `src/clients/` (multi-tenant version) — replaced by gofreddy's file-based per-client `clients/<name>/` workspaces.
- `src/jobs/` — Google Cloud Tasks + Postgres job queue. Use `cron` or APScheduler if scheduling is ever needed.
- `src/auth/` — already minimal in gofreddy (CLI doesn't need OAuth flows).
- `cli/accounts.py`, `cli/analytics.py`, `cli/calendar.py`, `cli/usage.py` — all SaaS-account-coupled.
- `cli/_generated/manage_client.py`, `_generated/generate_content.py`, `_generated/think.py`, `_generated/competitor_ads.py`, `_generated/creator_profile.py` — mostly `TODO: implement` stubs scaffolded for SaaS.
- `src/feedback.py` (68 LOC) + `src/feedback_loop_config.py` (45 LOC) — fire-and-forget Supabase signal recorder + domain config for the SaaS feedback loop. **Note:** the *top-level* `freddy/feedback_loop/` library is now Bundle N (deferred, not skipped — round 2 reconciled this).
- All SaaS background workers and Cloud Tasks dispatchers across modules: `monitoring/dispatcher.py`, `monitoring/worker.py`, `generation/worker.py`, `batch/worker.py`, `publishing/dispatcher.py`, `publishing/rss_monitor.py`. CLI is synchronous; no job queue.
- All Postgres `repository.py` files in shared modules (`seo/repository.py`, `competitive/repository.py`, `fraud/repository.py`, `deepfake/repository.py`, `monitoring/repository_analytics.py`, `publishing/repository.py`, `analysis/repository.py`, `batch/repository.py`, `video_projects/repository.py`, `monitoring/comments/repository.py`, `monitoring/crm/repository.py`). Where Bundle G ports the corresponding service, persistence is replaced with file-based or in-memory.
- `routers/*` (`src/api/routers/`) — all FastAPI route files. Business logic worth extracting is itemised in Bundle O.
- `frontend/src/content/marketing.ts` — the only frontend delta vs gofreddy's frontend. Pure marketing copy, not agency-relevant.
- `supabase/seed.sql` — SaaS bootstrap data (workspaces, organizations, billing).

**Domain-specific / low value for this agency:**
- `src/stories/` — Cloudflare R2-coupled ephemeral content (Instagram Stories). Not used.
- `src/newsletter/` + `cli/newsletter.py` — Resend + subscriber DB. Not in agency scope.
- `src/evolution/` — creator risk/topic trajectory. Narrow domain, gofreddy doesn't run that flow.
- `src/optimization/` — DSPy MIPROv2 prompt optimizer. Optional, post-MVP if at all.
- `src/policies/` — brand-safety policy engine. Useful eventually; not orchestrator-foundation.
- `src/conversations/` — multi-turn agent state with Postgres + tier gating. Lightweight session state already exists in gofreddy.
- `src/demographics/` — audience segmentation. Niche.
- `src/orchestrator/adk_agent.py` — Google ADK wrapper. Heavyweight dep; ReAct is enough.
- `cli/creator.py` — overlaps existing `search_content` + `detect`. Marginal.
- `cli/video.py` — partially portable; defer until creator/video is on the roadmap.
- `cli/write.py` — overlaps existing flows. Defer.
- `cli/articles.py` — SaaS storage + multi-tenant performance tracking.
- `monitoring/comments/` (3 files) and `monitoring/crm/` (2 files) — comment moderation + HubSpot/Salesforce sync. SaaS-tied.
- `monitoring/workspace_bridge.py` — saves mentions to SaaS canvas collections.
- `monitoring/analytics_service.py` + `repository_analytics.py` — account-level metrics tied to user workspace.
- `skills/` (top-level in freddy) — Claude Code skill definitions for the Freddy SaaS platform. Not applicable to gofreddy.
- `experiments/` (top-level in freddy) — separate from `experiments/benchmark/` listed in Bundle K. The benchmark suite is deferred (Bundle K); other experiments are skip.

**Provider SDKs not in either repo (no port needed; these were never used):**
Brave, Exa, Tavily, Firecrawl, Scrapfly, Brightdata, Oxylabs, Ahrefs, Semrush, NewsData (the package, even though "NewsData" is referenced as a *brand* somewhere — no SDK import found), Tweepy, atproto (Bluesky), instagrapi, Brevo, SendGrid, Postmark, Twilio, Slack SDK, `youtube_transcript_api`, Replicate, Perplexity, Google Cloud Tasks.

**Cleanly-removed deps (correctly stripped from gofreddy `pyproject.toml`):**
- `google-cloud-tasks` — async job queue.
- `stripe[async]` — billing.
- `redis` — cache/session.
- `supabase` SDK (removed import; config fields kept for future).
- `dspy` — prompt-optimizer framework, post-MVP.
- `resend` — email service.
- `sse-starlette` — server-sent events (note: removal may bite if any future API needs streaming — Bundle O `routers/agent.py` uses SSE; if we ever extract that, sse-starlette returns).

---

## Sanity check on the README claim

The gofreddy README says: "every provider integration is **byte-identical** to the source."

**Partially true.** Provider *SDK wrappers* are byte-identical:
- `src/seo/providers/dataforseo.py`, `src/competitive/providers/{foreplay,adyntel}.py`, `src/monitoring/adapters/xpoz.py`, `src/generation/{fal_client,grok_client}.py`, `src/seo/providers/gsc.py`, `yt-dlp` integrations — all match.

**Service/orchestration layers around them have diverged or been cut:**
- `src/competitive/service.py`: freddy 222 LOC → gofreddy 407 LOC. Gofreddy added Sonnet entity-disambiguation logic.
- `src/monitoring/intelligence/`: freddy has 12 modules; gofreddy has 11 — `post_ingestion.py` missing.
- `src/generation/`: freddy 27 files; gofreddy 23 — `service.py`, `repository.py`, `worker.py` missing (Bundle F).
- `src/orchestrator/`: freddy comprehensive; gofreddy entirely absent (Bundle A).
- `cli/freddy/commands/evaluate.py`: freddy is thick (owns model calls); gofreddy is a thin HTTP client to judge-service.
- `autoresearch/evaluate_variant.py`: freddy calls `freddy evaluate variant` CLI subprocess; gofreddy POSTs to judge-service.

**Verdict:** The README claim should be narrowed to "every provider SDK wrapper is byte-identical." Service-layer divergence is intentional (file-based + judge-service architecture) and not a regression — but the README oversells.

**Action:** Update gofreddy README during Bundle A or Bundle B work, when other documentation pass happens.

---

## Recommended sequencing

**This branch (`feat/fred-port-gaps`):** Bundle A → Bundle B (+ co-shipped J + L + W + X; opportunistic H deepfake-tests).
- A first because B's marketing-audit judges depend on the orchestration foundation (registered tools, ReAct loop, cost tracker).
- Bundle J's `scripts/build_tool_artifacts.py` co-ships with Bundle A — its only input is the tool catalog.
- Bundle L's `docs/from-fred/` snapshot co-ships with Bundle B — small, preserves institutional context once and never again.
- Bundle H's `tests/deepfake/test_service.py` is a cheap fold-in (module already exists in gofreddy with zero coverage).
- Bundle W's `tool_handlers/_helpers.py` (296 LOC) folds into Bundle A as A.10 — round 4 found these aren't covered by existing A.3.
- Bundle X (cost hard-cap enforcement) folds into Bundle A.4 — extends CostTracker behavior.
- A + B + J + L + H + W + X ≈ 3–4 weeks total.

**Next branch (recommended):** Bundle G — service-layer orchestration drift. **The largest finding from round 2.** ~3K LOC of work; 6 critical service files (`search`, `seo`, `competitive`, `fraud`, `deepfake`, `publishing`). `feat/service-layer-port`.

**Soonest follow-ups (small, mostly chore-style, parallelizable):**
- `chore/freddy-fix-backport` (Bundle P — ~14 small cherry-picks of freddy fixes since fork; M aggregate)
- `chore/ops-hygiene` (Bundle M — env-var documentation + Dockerfile hardening)
- `docs/harness-scope-clarification` (Bundle Q — document the deliberate 6→3 track reduction)
- `feat/archive-cli-port` (Bundle V — port `autoresearch/archive_cli.py` operator inspection CLI; S effort)

**Subsequent feature branches (each its own brainstorm → spec → plan cycle):**
- `feat/content-gen-extraction` (Bundle C)
- `feat/publish-media-pipeline` (Bundle D, includes any Bundle G `publishing/` follow-ups)
- `feat/brand-monitoring-intelligence` (Bundle E)
- `feat/generation-service-layer` (Bundle F)
- `feat/within-cli-restoration` (Bundle I — small QoL)
- `feat/sdk-feature-exposure-pass` (Bundle R — Gemini batches/caching, OpenAI reasoning, httpx tuning)
- `feat/agency-frontend-backend` (Bundle S — depends on user's deployment-model decision)
- `feat/harness-safety-restoration` (Bundle U — restore convergence detection + escalation tracking + protected-file backup; **upgraded from Bundle K** with concrete file inventory)
- `feat/feedback-loop-port` (Bundle N — re-evaluate after Bundle G ships)
- `feat/route-logic-extraction` (Bundle O — incremental, ride with whichever follow-up touches each surface)

**Trivial/opportunistic:**
- Bundle T (3-line stale-comment cleanup in `src/api/main.py`) — ride with any future PR touching that file.

The skip-list above is durable across all of them — re-litigate only if scope changes.

---

## Open decisions (still to lock with user)

**Decisions resolved during 2026-04-26 brainstorming** (recorded for traceability):

1. ~~MA-1..MA-8 rubric prose~~ → **Transcribe sketches now**, refine in v1 dogfood.
2. ~~Autoresearch lane pin~~ → **Yes**, mark cut-point at end of Bundle A; tag on `main` at merge.
3. ~~Variant prompt mutation scope~~ → **4 agents** (already locked in `2026-04-23-002` §54).
4. ~~Orchestrator landing path~~ → **`gofreddy/src/orchestrator/`** (mirror).
5. ~~Stuck-detection severity~~ → **Full circuit-breaker port**.
6. ~~Tool catalog scope~~ → **All ~20 specs**.

**Still open (for future scope-locking):**

- **Bundle G ordering** (highest-priority deferred): service-layer ports — which service first? Recommend `src/search/service.py` (most-impactful single port) or `src/deepfake/service.py` (smallest, fastest win for momentum). Not a blocker for the active branch.
- **Bundle N reconsideration** (`feedback_loop/` top-level): defer until Bundle G lands and we can see whether gofreddy's existing `judges/` + `events.py` + `agent_calls.py` already covers the same ground.
- **Bundle M timing** (ops-hygiene env-var documentation): bundle as one PR or split per autoresearch sub-system? Lean: one PR, all 25+ vars at once, since they're all in the same `.env.example`.
- **Bundle G's port destination for repositories**: services need persistence — adopt the pattern gofreddy already uses for autoresearch (file-based JSONL under `~/.local/share/gofreddy/`) or stand up a per-service file pattern? Decision can ride with whichever Bundle G service ships first.
- **Bundle P timing** (recent freddy fix backport): land before, alongside, or after Bundle A+B? Lean: parallel small PR (chore branch), independent of A+B. Cherry-picks risk no merge conflict against this branch.
- **Bundle Q resolution** (harness track scope): is the 6→3 reduction permanent? If permanent, document it in `harness/README.md` (Bundle Q). If staged, restore tracks D/E/F when needed.
- **Bundle S — agency-frontend deployment model:** A (CLI-served local FastAPI + workspace files), B (persistent backend), or C (hybrid)? **Recommended: A.** Shapes Bundle S, decides whether `sse-starlette` and FastAPI return as deps. **Most strategic open decision in this inventory.**

---

## References

- Source survey commit: `freddy` @ `50602a2`
- Target base: `gofreddy/main` @ `feaacf7`
- Related plans:
  - `docs/plans/2026-04-20-002-*` (audit pipeline R3, R22, ports list)
  - `docs/plans/2026-04-23-002-marketing-audit-lhr-design.md`
  - `docs/plans/2026-04-24-002-port-only-extraction-checklist.md`
  - `docs/plans/2026-04-24-003-audit-engine-implementation-design.md`
  - `docs/plans/2026-04-24-004-bundle-0-status-and-bundle-a-handoff.md`
- Memory entries that this inventory affects:
  - `project-marketing-audit-lhr-design-shipped.md`
  - `project-audit-engine-plan-state-2026-04-24.md`
  - `project-port-only-extraction-state.md`
