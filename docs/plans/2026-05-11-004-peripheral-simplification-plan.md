---
title: "Peripheral simplification (Plan D) — non-substrate over-engineering cleanup"
type: refactor
status: draft
date: 2026-05-11
companion-plans:
  - docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md
  - docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md
  - docs/plans/2026-05-11-003-external-absorptions-plan.md
origin: 5-agent codebase scan on 2026-05-11 (judges/ + src/api/ + cli + tests + build/config)
---

# Peripheral simplification (Plan D) — non-substrate over-engineering cleanup

## 1. Goal

Cut ~3,800 LOC of pure-deletable over-engineering + relocate ~2,800 LOC out of CI scope, across 5 surfaces that Plan B explicitly leaves untouched: `judges/` internals, `src/api/` backend, CLI + scripts + hooks, `tests/` outside `tests/autoresearch/`, and build/config. Each unit is independently shippable; the plan is a workbench, not a sequenced campaign.

Plan B (substrate) stays focused on the autoresearch↔autoresearch seam. Plan D handles the cross-cutting hygiene Plan B's research-pass surfaced but explicitly de-scoped.

## 2. Non-goals (explicit out of scope)

- **Substrate simplification** → Plan B (`2026-05-11-001`)
- **Eval-pipeline bug fixes** → Plan A (`2026-05-11-002`, shipped as `3b97b3d`)
- **External research absorptions** (panel-of-3, UCB1, novelty judge, etc.) → Plan C (`2026-05-11-003`)
- **Judges algorithmic improvements** (panel composition, rubric rewriting) → Plan C
- **Frontend / generations / video pipeline** — separate concerns, no findings surfaced
- **AI-tool configs** (`.claude/`, `.cursor/`, etc.) — unrelated hygiene

## 3. Source — 5-agent scan on 2026-05-11

Each finding traces back to one of:
- **`judges/` internals** — 8 findings, ~250 LOC reducible (~25% of 950 LOC)
- **`src/api/`** — 6 findings, ~650 LOC reducible
- **CLI + scripts + hooks** — 8 findings, ~600 LOC reducible
- **`tests/` outside autoresearch** — 8 findings, ~3,300 LOC reducible + 2,800 LOC relocatable
- **Build + config** — 6 findings, ~1,800 LOC reducible

Total: ~6,600 LOC removable + ~2,800 LOC relocatable. No autoresearch substrate code touched.

## 4. Decisions (locked)

| ID | Decision | Rationale |
|---|---|---|
| DD1 | Plan D is independent of Plan B's U0–U10 critical path | No unit blocks substrate work; substrate work doesn't block any D unit |
| DD2 | Tier 1 units (D1-D5) ship anytime; Tier 2 after Plan B U10; Tier 3 after Plan B U14 | Risk concentration — backend touches wait for substrate stability |
| DD3 | One commit per unit; no unit bundles | Easier revert; easier review |
| DD4 | No new abstractions introduced — only consolidate existing duplication | Plan D is reduction, not architecture |
| DD5 | Each unit ships to `main` on its own; no feature branches | Per repo convention (see `feedback-stay-on-main-or-worktree.md`) |
| DD6 | `requirements.txt` deletion (D1) ships FIRST as the demo win | Lowest risk, highest LOC, ~1,200 lines in one commit |
| DD7 | judges/ refactors do NOT change endpoint behavior or wire formats | Plan B's U10 measurement assumes judges-as-shipped; D refactors must be observation-equivalent |

## 5. Units

### Tier 1 — cheap wins, no Plan B dependency (parallel with U0/U0a)

| ID | Title | LOC delta | Effort | Risk |
|---|---|---|---|---|
| D1 | Delete `requirements.txt` | -1,200 | 15 min | Low — CI update required |
| D2 | Consolidate 7 duplicate `.env.example` files | -400 | 30 min | Low |
| D3 | Delete deprecated `freddy digest check` command | -80 | 20 min | Low — already deprecated |
| D4 | Archive Phase 4/5 migration scripts | -150 | 30 min | Low — historical artifacts |
| D5 | judges/ common helper extraction | -80 net (-150 +70) | 1 hr | Low |

**Tier 1 total: ~1,910 LOC removed, ~3 hours of work.**

### Tier 2 — medium scope, after Plan B U10 hard gate passes

| ID | Title | LOC delta | Effort | Risk |
|---|---|---|---|---|
| D6 | judges/ decision-agent unification (promotion + rollback + canary) | -60 | 3 hr | Medium — touches 3 judge endpoints |
| D7 | CLI substrate-decoupling (audit + evaluate + fixture) | -180 net (moved, not deleted) | 6 hr | Medium-high — coordinates with Plan B U13 |
| D8 | `src/api` AppServices registry refactor (59 app.state → typed dataclass) | -150 | 4 hr | Medium — startup path |
| D9 | tests/ conftest consolidation + `_FakeResponse` factoring | -400 | 4 hr | Low |
| D10 | Move `tests/spikes/` → `validation-spikes/` (relocation only) | 0 (relocate 2,800) | 1 hr | Low — already CI-skipped |

**Tier 2 total: ~790 LOC removed + 2,800 LOC relocated, ~18 hours of work.**

### Tier 3 — bigger projects, after Plan B U14 decommission

| ID | Title | LOC delta | Effort | Risk |
|---|---|---|---|---|
| D11 | `src/api` storage abstraction unification (3 R2 classes → 1 base + thin subclasses) | -100 | 1 day | Medium — backend lifecycle |
| D12 | `src/api` 89-endpoint caller audit + portal/stripe/fireflies cleanup | -150 to -200 | 1 day | Medium — public API surface |
| D13 | 18 `BaseSettings` consolidation → 3-4 grouped Settings | -80 net | 1 day | Medium — env var loading |
| D14 | judges/ variant_scorer dual-prompt resolution (templated vs static) | -50 | 4 hr | Medium — baseline drift risk |
| D15 | judges/inner_critique architectural decision | TBD (architectural) | 4 hr | Low — decision only |
| D16 | invoke_cli retry asymmetry normalization (codex vs opencode) | -20 | 2 hr | Low |

**Tier 3 total: ~400-450 LOC removed + 1 architectural decision, ~4 days of work.**

### Grand totals

- **LOC removed:** ~3,100 across Tiers 1+2+3
- **LOC relocated (not deleted):** ~2,800 (`tests/spikes/`)
- **Effort:** ~6 working days spread across the post-Plan-B window
- **Risk profile:** front-loaded with cheap wins; heaviest changes wait for substrate stability

## 6. Unit detail

### D1 — Delete `requirements.txt`

**Why:** Auto-generated from `uv.lock` (header line 1 of the file confirms it). 1,215 lines of pure duplication. uv-based CI workflows already prefer `uv sync` or `uv pip install --requirements uv.lock`; `requirements.txt` is legacy PIP carryover.

**Files:**
- Delete: `requirements.txt`
- Modify: any GitHub workflow (`.github/workflows/*.yml`) that references `requirements.txt` — switch to `uv sync` or `uv pip install -r uv.lock`
- Modify: any Dockerfile referencing `requirements.txt`

**Approach:**
1. `grep -rn "requirements.txt" .github/ Dockerfile scripts/ 2>/dev/null` to find all CI/build callers
2. Replace each with `uv sync --frozen` (the uv-native pattern)
3. `git rm requirements.txt`
4. Verify: pull-request CI green; local `uv sync` produces same env

**Test scenarios:**
- Happy path: `uv sync` from clean checkout installs identical deps to pre-D1
- Edge case: a CI workflow that ran `pip install -r requirements.txt` now uses `uv sync`; verify it produces the same lockfile-resolved deps
- Regression: a developer with no `uv` installed gets a clear error (document in `README.md` setup)

**Verification:**
- CI green
- `uv tree | wc -l` shows the same dep count as before
- `python -c 'import freddy'` succeeds from a fresh venv synced with `uv sync`

**Rollback:** `git revert` the deletion commit. uv re-exports `requirements.txt` with `uv export --no-emit-project --no-dev > requirements.txt`.

---

### D2 — Consolidate 7 duplicate `.env.example` files

**Why:** 5-agent scan found 7 `.env.example` files across root + 4 worktrees + `.claude/worktrees/`, all containing the same ~70-line 2.4 KB template. Total duplication ≈ 400 lines. Worktrees inherit the root template but each `.env.example` got committed independently.

**Files:**
- Keep: root `.env.example` as the canonical template
- Delete: 6 duplicates in `.worktrees/*/`, `.claude/worktrees/*/`, `frontend/` (if frontend's is truly identical — verify first)
- Add: `docs/setup/env-vars.md` documenting how to copy root template into a new worktree

**Approach:**
1. `find . -name ".env.example" -not -path "*/node_modules/*" -not -path "*/.venv/*"` — list all 7
2. `diff` each against root — confirm identical or note differences
3. If any worktree's `.env.example` has worktree-specific additions, fold them into root with a section comment
4. Delete duplicates; add a note to `CLAUDE.md` / `AGENTS.md` that worktree setup includes `cp .env.example .env`

**Test scenarios:**
- Happy path: a new worktree checkout uses `cp .env.example .env` and works
- Edge case: a worktree previously had branch-specific env vars not in root — surface during diff

**Verification:**
- Single `.env.example` at root
- `grep -rln "\.env\.example" docs/ CLAUDE.md AGENTS.md` finds the setup doc
- `find . -name ".env.example"` returns only the root path (+ `frontend/` if intentionally retained)

**Rollback:** Trivial — `git revert` restores duplicates.

---

### D3 — Delete deprecated `freddy digest check` command

**Why:** `cli/freddy/commands/digest.py` already labels its `check` subcommand `@app.command(deprecated=True)` with an error message redirecting to `freddy evaluate variant monitoring`. Yet the command is still routed in `cli/freddy/main.py` (`app.add_typer(digest.app, name="digest")`). Users get an error instead of removed surface; the file is ~80 LOC of dead-end code.

**Files:**
- Delete: `cli/freddy/commands/digest.py`
- Modify: `cli/freddy/main.py` — remove the `app.add_typer(digest.app, ...)` line
- Modify: `CLAUDE.md` / `AGENTS.md` — remove any reference to `freddy digest`
- Modify: tests that import `digest.py` (likely none, but grep)

**Approach:**
1. `grep -rn "freddy digest\|cli.freddy.commands.digest\|from.*digest" cli/ tests/ docs/ CLAUDE.md AGENTS.md`
2. For each match: delete or update reference
3. `git rm cli/freddy/commands/digest.py`

**Test scenarios:**
- Happy path: `freddy --help` no longer lists `digest` as a command
- Happy path: `freddy evaluate variant monitoring` still works
- Edge case: a script calls `freddy digest check` — surface during U0 (Plan B's audit) or D3-internal grep

**Verification:**
- `freddy digest` returns "no such command"
- `pytest tests/cli/` green (no removed-import errors)

**Rollback:** `git revert` restores the file.

---

### D4 — Archive Phase 4/5 migration scripts

**Why:** `autoresearch/scripts/phase4-migration-check.sh` (61 LOC) and `phase5-canary.sh` (88 LOC) are one-shot scripts from earlier Plan B phases. Comments confirm: "Plan B Phase 4 Step 4 — migration-check…run one full evolution iteration…asserts lane head did not move." Phase 4/5 are closed (v006+ stable, promotion stable). Also: `scripts/autoresearch/backfill_v006_promoted_at.py` ("Run once after Unit 2 predicate fix lands"). 150 LOC of historical migration code in active script paths.

**Files:**
- Create: `autoresearch/archive/v006-migration/scripts/` directory
- Move (git mv): `autoresearch/scripts/phase4-migration-check.sh`, `phase5-canary.sh`, `scripts/autoresearch/backfill_v006_promoted_at.py` → `autoresearch/archive/v006-migration/scripts/`
- Add: `autoresearch/archive/v006-migration/scripts/README.md` documenting "what these scripts did, when they ran, why they're archived"

**Approach:**
1. `grep -rn "phase4-migration-check\|phase5-canary\|backfill_v006_promoted_at" . --include="*.yml" --include="*.sh" --include="*.md"` to find any callers
2. If a CI workflow still references them, decide: (a) cron/CI was abandoned with the phase → delete the workflow stanza, or (b) script is still load-bearing → keep, surface to JR
3. `git mv` to archive location
4. README explains purpose + decommission date

**Test scenarios:**
- Happy path: no caller references the moved paths (verify with grep)
- Edge case: a `.github/workflows/holdout-refresh.yml` references `phase5-canary` — surface and decide

**Verification:**
- `find autoresearch/scripts -name "phase4*" -o -name "phase5*"` returns empty
- CI green after the move

**Rollback:** `git mv` back to original locations.

---

### D5 — judges/ common helper extraction

**Why:** 7 separate `_extract_json()` definitions across `judges/session/agents/*.py` + `judges/evolution/agents/*.py` — all identical regex (`re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)`) + identical error handling. Same for `_load_prompt()` (7 copies of `Path(prompt_file).read_text()`). Pure boilerplate; ~150 LOC of duplication for ~70 LOC of new shared module. Net -80 LOC.

**Files:**
- Create: `judges/common.py` (~70 LOC)
  - `extract_json(text: str, *, source: str) -> dict | None` — single canonical JSON-block extractor with optional `source` arg for error context
  - `load_prompt(prompt_path: str) -> str` — single canonical prompt loader
  - `_JSON_BLOCK` regex as module-level constant
- Modify: 7 agent files (`judges/session/agents/critique_agent.py`, `review_agent.py`, `judges/evolution/agents/{variant_scorer,promotion_agent,rollback_agent,canary_agent,system_health_agent}.py`) — replace local helpers with `from judges.common import extract_json, load_prompt`
- Create: `tests/judges/test_common.py` — covers extract_json (valid JSON, malformed JSON, missing block, multiple blocks), load_prompt

**Approach:**
1. Read one canonical implementation (probably `judges/evolution/agents/variant_scorer.py`) to confirm the shape
2. Diff the 7 copies — verify they're identical (or note differences that need preservation)
3. Write `judges/common.py` with the union-of-behavior
4. Replace each agent's local helpers with the import; delete the local definitions
5. Run `pytest tests/judges/ tests/autoresearch/` to verify no behavior change

**Test scenarios:**
- Happy path: valid JSON-block extraction matches all 7 prior local implementations on a corpus of real judge responses
- Edge case: malformed JSON (truncated by token limit) → returns None, no exception
- Edge case: multiple JSON blocks in one response → returns the first (current behavior of all 7 copies)
- Regression: Plan B's U6 references `judges/evolution/agents/variant_scorer.py` patterns — verify variant_scorer's behavior is unchanged after refactor

**Verification:**
- All judges-side tests green
- A single fixture run through evolution-judge produces identical scores pre/post D5
- `grep -c "def _extract_json" judges/` returns 0 (was 7); `grep -c "from judges.common import" judges/` returns ≥ 7

**Rollback:** `git revert`. Local helpers restored automatically.

**Dependency note:** Plan B's U0a deliberate-but-stale audit should run BEFORE D5 to catch any non-obvious differences across the 7 copies (e.g., one might have a comment "TODO: tighten error handling" that signals real divergence). Defer D5 until U0a confirms the 7 are truly identical.

---

### D6 — judges/ decision-agent unification (promotion + rollback + canary)

**Why:** `judges/evolution/agents/{promotion_agent,rollback_agent,canary_agent}.py` are 46 + 46 + 45 LOC each, all following the identical pattern: `load_prompt() → extract_json() → format payload → invoke_claude(prompt) → validate decision against _ALLOWED set → return normalized dict`. Only the decision enum differs (promote/reject, rollback/hold, go/fail/revise). One parameterized factory or single `decide_variant(role, decision_enum, payload)` function reduces 3 files to 1 + 3 thin role-config files.

**Files:**
- Refactor: 3 files → 1 base (`judges/evolution/agents/decision.py`, ~60 LOC) + 3 thin role configs (~10 LOC each = 30 LOC total)
- Net: 137 LOC (current) → ~90 LOC (refactored) → **-47 LOC**

**Approach:**
1. Read all 3 files; verify decision-set is the only behavioral difference
2. Design the base function: `async def decide(role: str, allowed: set[str], payload: dict, prompt_path: Path) -> dict`
3. Each role file (`promotion.py`, `rollback.py`, `canary.py`) is a 10-line wrapper: `from .decision import decide; ALLOWED = {"promote", "reject"}; PROMPT = Path(...); async def promote(payload): return await decide("promote", ALLOWED, payload, PROMPT)`
4. Update `judges/server.py` routes to import the role-specific wrappers (no API change)
5. Tests stay at the role granularity (test promotion contract, rollback contract, canary contract separately)

**Test scenarios:**
- Happy path: each role's decide function produces the same output as the current per-file implementation on a fixture set
- Edge case: a role returns a decision outside its `_ALLOWED` set → raises with identical error message to current behavior
- Contract test: HTTP shape of `/v1/decide/promotion`, `/v1/decide/rollback`, `/v1/decide/canary` is byte-identical before/after

**Verification:**
- All judges-side tests green
- A live promotion / rollback / canary run produces identical JSON output pre/post D6

**Rollback:** `git revert`. Per-role files restored.

**Dependency:** D5 (common helpers); Plan B U10 hard gate passed (judges are observation-stable).

---

### D7 — CLI substrate-decoupling (audit + evaluate + fixture)

**Why:** `cli/freddy/commands/audit.py` imports `src.audit.state`, `src.audit.agent_runner`, `src.seo.config`, `src.audit.r2_publish`, `src.audit.tools.brave_search` (10+ imports across 500 LOC). `cli/freddy/commands/fixture.py` imports `autoresearch.judges.quality_judge`, `autoresearch.events`, `cli.freddy.fixture.*`. `evaluate.py` (306 LOC) imports `autoresearch.evaluate_variant`. These CLI commands contain substrate business logic, not just argument parsing. When substrate refactors land (Plan B U13), CLI breaks unless every import is hand-migrated.

**Files:**
- Create: `src/api/cli_surface.py` (or `autoresearch_v2/cli_surface.py` after Plan B U14) — a thin API layer exposing what the CLI needs as named functions returning JSON-serializable dicts
- Refactor: `cli/freddy/commands/audit.py`, `evaluate.py`, `fixture.py` — replace deep substrate imports with calls to `cli_surface`
- Tests: existing CLI tests stay green; substrate tests are unchanged

**Approach:**
1. Map current substrate imports per command file (already done by 5-agent scan; expand into spec)
2. Define `cli_surface` API: e.g., `run_audit(client: str, ...) -> AuditResult`, `evaluate_variant(...) -> EvalResult`, `refresh_fixture(...) -> FixtureManifest`
3. Move business logic from CLI to substrate where it belongs; CLI becomes pure arg parsing + dispatch
4. Ship incrementally per command (audit first, then evaluate, then fixture)

**Test scenarios:**
- Happy path: `freddy audit start <client>` produces identical output before/after refactor
- Happy path: `freddy evaluate variant geo` produces identical JSON
- Regression: `cli/freddy/fixture/dryrun.py` (Plan B U13 hidden consumer) still imports work; the cli_surface API is its v2 home

**Verification:**
- All CLI tests green
- Substrate tests green
- A live `freddy audit start` run produces identical artifacts

**Rollback:** Per-command revert; each ships independently.

**Dependency:** Plan B U13 (operator script migration) — D7 lands AFTER U13 so the substrate surface is stable.

---

### D8 — `src/api` AppServices registry refactor

**Why:** `src/api/main.py` has 59 `app.state.*` properties assigned across lifespan startup (lines 60-620) with ad-hoc init + fallback logic. No invariants enforced; routers fail at request-time with 503 if any property is None. Inconsistent naming (e.g., `r2_storage` vs `video_storage` alias added at line 103). A typed `AppServices` dataclass with required fields + fail-fast startup eliminates the 503 surface.

**Files:**
- Create: `src/api/app_services.py` (~50 LOC) — `@dataclass` with typed fields for the 12 production-critical services
- Modify: `src/api/main.py` — replace 59 `app.state.X = ...` assignments with `app.state.services = AppServices(...)`; update lifespan teardown
- Modify: routers in `src/api/routers/*.py` that read `app.state.X` — update to `app.state.services.X`

**Approach:**
1. Inventory the 59 properties; classify into (a) critical (12-15), (b) optional/feature-flagged (rest), (c) dead (zero readers)
2. Design `AppServices` with only critical fields; optional/feature-flagged stay on `app.state.*` with explicit None handling
3. Migrate readers one router at a time

**Test scenarios:**
- Happy path: backend starts cleanly with all env vars set
- Failure path: missing env var → startup fails with clear error (was 503 at request time, now CRITICAL log + exit at startup)
- Regression: every existing route still resolves its services correctly

**Verification:**
- `pytest tests/api/` green
- Local backend boot succeeds; intentional broken-env test fails fast

**Rollback:** `git revert`. Original `app.state.*` pattern restored.

**Dependency:** Plan B U10 hard gate passed (so substrate doesn't surface backend-startup bugs during measurement).

---

### D9 — tests/ conftest consolidation + `_FakeResponse` factoring

**Why:** 8 conftest.py files (710 LOC total) with overlapping fixtures. `_FakeResponse` class duplicated across `tests/test_cli_evaluate.py`, `tests/test_cli_monitor.py`, `tests/test_cli_monitor_summarizer.py` etc. (10+ autouse fixtures set the same env vars). One shared pytest plugin + one canonical `_FakeResponse` removes ~400 LOC.

**Files:**
- Create: `tests/_pytest_plugin/` package with `env_fixtures.py` (autouse env setup) + `http_doubles.py` (FakeResponse, FakeAsyncClient)
- Modify: existing conftest.py files — remove duplicated content, import from the plugin
- Modify: test files that define local `_FakeResponse` — import from `tests._pytest_plugin.http_doubles`

**Approach:**
1. Diff the 8 conftest.py files; identify shared patterns
2. Move common patterns to plugin; leave file-specific fixtures local
3. Standardize the FakeResponse shape; migrate users

**Test scenarios:**
- Happy path: full test suite green
- Edge case: a test that monkey-patched a local _FakeResponse subclass still works (or is migrated to use the canonical version)

**Verification:**
- `pytest tests/` green
- `grep -c "class _FakeResponse" tests/` drops from 5+ to 1

**Rollback:** Per-file revert.

**Dependency:** Plan B U13a (tests classification audit) — D9 runs in parallel or after U13a to avoid duplicated work.

---

### D10 — Move `tests/spikes/` → `validation-spikes/`

**Why:** `tests/spikes/` (13 files, ~2,800 LOC) are NOT unit tests — they're ad-hoc validation runs with `@pytest.mark.external_api`, `@pytest.mark.spike` markers, env-flag-gated skips, `time.sleep(2.0)` rate limiting, subprocess calls. CI already skips them. Mixed with real tests, they inflate `tests/` size and confuse maintainers about test policy.

**Files:**
- Move (git mv): `tests/spikes/` → `validation-spikes/`
- Modify: `pytest.ini` or `pyproject.toml[tool.pytest]` — remove `tests/spikes/` from `testpaths` if listed
- Modify: any documentation referencing `tests/spikes/`
- Add: `validation-spikes/README.md` documenting purpose + run instructions

**Approach:**
1. `git mv tests/spikes/ validation-spikes/`
2. Remove from `testpaths` (verify pytest discovery still excludes them)
3. README explains: "these are manual validation runs against external APIs, run with `RUN_LIVE_EXTERNAL=1 pytest validation-spikes/`"

**Test scenarios:**
- Happy path: `pytest tests/` no longer discovers spike tests
- Happy path: `pytest validation-spikes/ --co` lists the spike tests (collection-only)
- Manual: `RUN_LIVE_EXTERNAL=1 pytest validation-spikes/spike_creative_patterns/` still runs

**Verification:**
- `pytest tests/ --co -q | grep -c "spike" == 0`
- CI runtime unchanged (spikes were already skipped)

**Rollback:** `git mv` back.

---

### D11 — `src/api` storage abstraction unification

**Why:** `R2VideoStorage` + `R2MediaStorage` + `R2SessionLogStorage` — 3 classes solving the same S3-key-storage problem with different APIs. `R2SessionLogStorage.__init__` composes a `R2VideoStorage` instance (composition, not inversion). Client lifecycle (`_get_client`, `__aenter__`, `__aexit__`) duplicated across modules. ~300 LOC across 3 files; unified to 1 base + 3 thin subclasses ≈ 200 LOC.

**Files:**
- Create: `src/storage/r2_base.py` — `S3Storage` base with client lifecycle, retry, key validation
- Refactor: `src/storage/r2_storage.py`, `r2_media_storage.py`, `src/sessions/log_storage.py` — derive from base, only implement key-path mapping

**Approach:**
1. Read all 3 implementations; extract common patterns
2. Define base API: `async def upload(key, data) / download(key) -> bytes / delete(key)`
3. Each subclass overrides `_key_for(...)` to derive its naming scheme
4. Verify identical behavior via integration tests

**Test scenarios:**
- Happy path: video upload + retrieval byte-identical pre/post
- Happy path: session log upload + retrieval byte-identical
- Happy path: media upload presigned URL byte-identical

**Verification:**
- `pytest tests/api/storage/` green
- Live backend upload + download smoke succeeds

**Rollback:** `git revert`.

**Dependency:** D8 (AppServices registry) — easier to refactor once `app.state.services` is in place.

---

### D12 — `src/api` 89-endpoint caller audit + portal/stripe/fireflies cleanup

**Why:** `src/api/routers/` has 18 routers exposing 89 endpoints. No inventory of which are called by frontend / CLI / autoresearch / external clients. `stripe.py` (86 LOC, 1 endpoint), `fireflies.py` (139 LOC, 2 endpoints), and `portal.py` 5 routes are unaudited; some may be POC endpoints never graduated to production.

**Files:**
- Create: `docs/research/2026-XX-XX-backend-endpoint-callers.md` — per-endpoint caller table
- Delete: any router classified as "0 callers, no plans to use"
- Modify: `src/api/main.py` — remove deleted routers from `app.include_router(...)` calls

**Approach:**
1. For each of 89 endpoints: `grep -rn '<path>' cli/ src/web/ tests/ autoresearch/ docs/`
2. Classify: (a) production, (b) experimental, (c) orphan
3. Surface (c) to JR for delete decision; defer (b) to feature-flag namespace

**Test scenarios:**
- Happy path: every retained endpoint still resolves
- Regression: removed endpoint surfaces in a smoke test → revert that specific delete

**Verification:**
- Audit doc reviewed
- 0 orphan endpoints
- `pytest tests/api/` green

**Rollback:** Per-router revert.

**Dependency:** Plan B U13 (so we know which endpoints autoresearch actually uses).

---

### D13 — 18 `BaseSettings` consolidation

**Why:** 18 `pydantic_settings.BaseSettings` subclasses scattered across `src/*/config.py` files. Each independently reads `.env`. No central registry; env-var conflicts and defaults are scattered. No single source of truth for "what env vars must be set."

**Files:**
- Create: `src/config/__init__.py` — `AppConfig` aggregator that constructs all 18 sub-settings at startup
- Refactor: 18 `config.py` files — keep the BaseSettings class definitions but consume them via `AppConfig`
- Modify: services that read config — inject `AppConfig` instead of constructing their own

**Approach:**
1. Inventory all 18 (already done by 5-agent scan)
2. Group into 3-4 domains (storage, auth, analysis, scoring)
3. `AppConfig` is the new entry point; each sub-config still exists for testability but isn't constructed elsewhere

**Test scenarios:**
- Happy path: `AppConfig.from_env()` loads all 18 sub-settings without error
- Failure path: missing required env var → startup fails with a clear "missing X in domain Y" error
- Regression: a service that previously read `GeoSettings().endpoint` now reads `config.storage.geo.endpoint` (or similar) and gets the same value

**Verification:**
- Backend boots
- All env-related tests green

**Rollback:** `git revert`.

**Dependency:** D8 (AppServices registry) — D13 nests into the same `app.state.services` pattern.

---

### D14 — judges/ variant_scorer dual-prompt resolution

**Why:** `judges/evolution/agents/variant_scorer.py:22-35, 103-126` has dual-prompt system (`scorer.md` for `geo/competitive/monitoring/storyboard`, `scorer_templated.md` for `x_engine/linkedin_engine`). Comment at line 30-33: *"Existing 4 lanes…have a public-domain prior…switching them silently degrades baselines."* Comment further says *"Round-6 #11 trim: ONE parameterized template for all templated domains, not per-domain prompt files."* **This is exactly the deliberate-but-stale pattern Plan B's U0a was designed to catch.** Resolve: measure baseline drift on each lane; if drift acceptable, consolidate to one template.

**Files:**
- Modify: `judges/evolution/prompts/scorer.md` + `scorer_templated.md` → merge into `scorer.md` with conditional prose
- Modify: `judges/evolution/agents/variant_scorer.py` — remove `_TEMPLATED_DOMAINS` branch
- Create: `docs/research/2026-XX-XX-variant-scorer-baseline-drift.md` — measurement methodology + per-lane drift numbers

**Approach:**
1. Run 5 evaluations on each lane (35 total) under BOTH prompts; compute per-axis delta
2. If max delta per axis ≤ 0.3 (within judge noise floor), consolidate
3. If delta > 0.3 on any axis, keep dual system AND document why ("locked in by R3 baseline preservation")
4. Either outcome: remove the stale "Round-6 #11 trim" comment

**Test scenarios:**
- Happy path: measurement shows acceptable drift, consolidation lands, all lanes produce composite within ±10% of pre-consolidation baseline
- Decision path: measurement shows unacceptable drift, dual system stays, comment updated to reflect lock decision

**Verification:**
- Measurement doc committed
- Either: consolidation diff lands AND post-consolidation eval matches v006 baseline within tolerance, OR dual system stays AND comment is updated

**Rollback:** Per-prompt revert.

**Dependency:** Plan B's U0a finds this; D14 is the resolution. U0a runs the measurement; D14 implements the chosen outcome.

---

### D15 — judges/inner_critique architectural decision

**Why:** Plan B's R3 mentions "inner-critique subprocess" as one of the 4 distinct judge services. The 5-agent scan found that `judges/inner_critique/` **does not exist as a module** — inner-critique is a subprocess-only invocation from inside `autoresearch/evaluate_variant.py`. The `judges/` directory implies parallel architecture (session-judge + evolution-judge + inner-critique + promotion-judge as 4 HTTP services), but inner-critique isn't HTTP. Either: (a) build the module to match the architecture, or (b) update R3 and Plan B docs to say "3 HTTP judges + 1 subprocess judge."

**Files:**
- Modify: Plan B `2026-05-11-001` R3 wording (if option b)
- Modify: this Plan D + relevant memory entries
- Or: Create `judges/inner_critique/` with the subprocess-only judge skeleton (if option a)

**Approach:**
1. JR decision: should inner-critique stay subprocess-only, or be promoted to a 5th HTTP service?
2. Option (a) — promote to HTTP: spec out the endpoint, but this is a Plan C concern (judge composition), not Plan D simplification
3. Option (b) — document subprocess-only status: update R3 to read "3 HTTP judges + inner-critique subprocess" and remove implications of architectural symmetry

**Recommendation:** Option (b). Inner-critique is intentionally subprocess (cheap, per-iteration, no API surface needed); promoting to HTTP is over-engineering for a working pattern. This is a "decide and document" unit, not a code unit.

**Test scenarios:** N/A — documentation-only.

**Verification:** Plan B R3 wording matches actual architecture; no implicit "5th judge" reference.

**Rollback:** Trivial.

**Dependency:** None.

---

### D16 — invoke_cli retry asymmetry normalization

**Why:** `judges/invoke_cli.py` has asymmetric retry behavior:
- `invoke_codex` (44 LOC, lines 110-154): no retry; detects credits-exhausted via stderr but doesn't retry transient failures
- `invoke_opencode` (73 LOC, lines 210-282): retry-3 with transient-error detection via `stdout_has_transient_error()`

Comment in codex: *"Mid-run credit exhaustion: codex exits 0 + emits null/empty… Surface this specifically so the operator sees actionable text."* Comment in opencode: *"On transient OpenRouter upstream errors we retry."* Suggests incomplete refactoring; either both should retry or neither should.

**Files:**
- Modify: `judges/invoke_cli.py` — normalize retry shape (recommend: extract common retry helper, apply to both codex + opencode; codex retries are no-op for credit-exhausted because it's a hard failure not a transient one)

**Approach:**
1. Audit: in the last 30 days of judge logs, how often did `invoke_codex` fail with a transient error that retry would have caught?
2. If frequency > 0.1%: add retry to codex
3. If frequency = 0: leave codex no-retry, but normalize via a helper that both call (codex passes retry=0)
4. Document the asymmetry rationale in the helper

**Test scenarios:**
- Happy path: an `invoke_codex` transient failure (mock) is retried if retry-policy applies
- Happy path: `invoke_opencode` retry-3 behavior unchanged

**Verification:**
- `pytest tests/judges/` green
- Live judge calls observe-equivalent

**Rollback:** `git revert`.

**Dependency:** D5 (common helpers, if retry helper lives in `judges/common.py`).

## 7. Phases

| Phase | Units | Wall time | Gate |
|---|---|---|---|
| **P1 — Cheap wins (parallel with Plan B U0/U0a)** | D1, D2, D3, D4 | 2 hours | None — anytime |
| **P2 — judges hygiene (parallel with Plan B U1-U10)** | D5, D14 | 1 day | Plan B U0a complete (D5 + D14 depend on U0a findings) |
| **P3 — Post-spike** | D6, D8, D9, D10 | 3-4 days | Plan B U10 hard gate passed |
| **P4 — Post-decommission** | D7, D11, D12, D13 | 4-5 days | Plan B U14 complete |
| **Backlog** | D15, D16 | 1 day | Anytime; D15 is decision-only |

**Total Plan D wall time: ~10 working days, mostly serial (small parallel windows possible within each phase).**

## 8. Hard gates

- **DG1 — Pre-P3:** Plan B U10 geo spike passes (search-v1 ≥ 7.0 AND holdout-v1 ≥ 4.5). Without this, judges-internal changes (D6) risk muddying U10's signal.
- **DG2 — Pre-P4:** Plan B U14 decommissioning complete. D7 (CLI substrate-decoupling) needs substrate paths stable.
- **DG3 — Pre-D5/D14:** Plan B U0a deliberate-but-stale audit complete. U0a's findings include the variant_scorer dual-prompt (D14) and confirm the 7 `_extract_json` copies are truly identical (D5).

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| D1 (requirements.txt) breaks a CI workflow not surfaced by grep | Medium | First CI run after delete catches it; revert if needed |
| D5 (judges common helpers) silently changes JSON extraction behavior | Low | Fixture-based pre/post diff on a corpus of real judge responses |
| D6 (decision-agent unification) changes HTTP response shape | Low | Contract tests assert byte-identical responses |
| D7 (CLI decoupling) collides with Plan B U13 | Medium | D7 explicitly gated on U13 completion |
| D8 (AppServices registry) surfaces latent backend startup bugs | Medium | Run in dev for 1 week before prod; staged rollout |
| D14 (variant_scorer dual-prompt) measurement shows unacceptable drift | Medium | Option to keep dual system; unit converts to "lock decision" rather than "consolidate" |
| Total Plan D LOC reduction undershoots the ~3,800 estimate | Medium | Each unit has independent value; partial completion is fine |

## 10. Reversibility per unit

| Unit | Revert path |
|---|---|
| D1 | `git revert`; `uv export` regenerates `requirements.txt` |
| D2 | `git revert`; duplicates restored |
| D3 | `git revert`; deprecated command restored (still emits error) |
| D4 | `git mv` archive back to original location |
| D5 | `git revert`; agent local helpers restored |
| D6 | `git revert`; 3 per-role files restored |
| D7 | Per-command revert |
| D8 | `git revert`; `app.state.*` direct assignments restored |
| D9 | Per-file revert |
| D10 | `git mv` back |
| D11 | `git revert`; 3 R2 classes restored |
| D12 | Per-router revert |
| D13 | `git revert`; 18 sub-Settings standalone again |
| D14 | Per-prompt revert |
| D15 | Documentation-only; trivial |
| D16 | `git revert` |

## 11. Success metrics

- **LOC removed:** ≥ 2,500 across all tiers (estimate is 3,100; budget for partial completion)
- **LOC relocated:** ~2,800 (`tests/spikes/`)
- **Zero substrate↔substrate seam bugs introduced** (Plan B's success metric extends here)
- **No production endpoint breakage** during D8 + D11 + D12
- **No judge response shape change** during D5 + D6 (byte-identical HTTP responses pre/post)

## 12. Open questions

- **JR sign-off needed on D15:** keep inner_critique subprocess-only, or promote to HTTP? Recommended: subprocess-only (documentation update, not code work).
- **D12 endpoint audit may surface portal/stripe/fireflies as load-bearing for some workflow not visible from grep.** If so, defer those route deletions to a separate decision.
- **D14 baseline-drift measurement budget:** ~$10-20 in judge calls. Acceptable?

## 13. Sources & references

- 5-agent codebase scan results (2026-05-11) — judges, src/api, CLI, tests, build/config
- Plan B: `docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md`
- Stream A merge: commit `3b97b3d` (PR #60)
- Memory: `~/.claude/projects/.../memory/project-stream-a-c-plans-drafted-2026-05-11.md`
