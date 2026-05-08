# Phase 4 — non-rubric plumbing gaps

Investigation of integration gaps that block running session/evolution loops cleanly, independent of rubric anchor stability. Each gap states **what's wrong**, **how I verified it**, **root cause**, **proposed fix** (mechanical or design-decision).

---

## Gap 1 — `search-v1.json` fixture context drift vs live `angles` table

**What's wrong.** `eval_suites/search-v1.json` has 5 fixtures per new lane with `context: "1".."5"`. The live `state.db` `angles` table currently holds IDs **120–127** (auto-increment continues from prior X-engine v1 work). Running a session with fixture `x_engine-angle-1` invokes `xeng angle-show 1` → `ERROR: angle 1 not found`, exit 2 → session fails the structural gate.

**How verified.**
- `python3 -c "import json; d=json.load(open('autoresearch/eval_suites/search-v1.json')); print([f['context'] for f in d['domains']['x_engine']])"` → `['1','2','3','4','5']`.
- `sqlite3 ~/.../gofreddy/x_engine/state.db "SELECT MIN(angle_id), MAX(angle_id) FROM angles"` → `120, 127`.
- Master plan §7.3 §A "Adjacent" specifies a `cli/freddy/fixture/sources.json` entry for `xeng-state` source; that exists and routes `xeng angle-show <context>` correctly. Verified: `cli/freddy/fixture/sources.json` `domains.x_engine[0].source = "xeng-state"`. So the fixture-refresh layer is wired but it does NOT remap contexts — it caches the result of `xeng angle-show <static-context>`.

**Root cause.** No mechanism keeps `search-v1.json` x_engine/linkedin_engine fixture contexts in sync with the rolling top-N of the `angles` table. The seed `["1","2","3","4","5"]` was a placeholder from the L2 K unit; master plan v13 §A mentioned `freddy fixture refresh --suite search-v1 --domain x_engine` but assumed pre-existing static fixture IDs. There is no "rotate to most-recent N" step anywhere in the build.

**Two paths to fix.**
- **A (recommended) — add a daily fixture-sync CLI.** New `xeng search-v1-sync` (or `freddy fixture sync-angles`) command: pick top N (default 5) from `angles ORDER BY picked_at DESC`, rewrite `search-v1.json` `domains.x_engine[]` and `domains.linkedin_engine[]`. Wire as a LaunchAgent that fires after `linkedin-pull-search` (so fresh angles → fresh fixtures → next evolve cycle picks them up). ~1.5 hr to write + test. Mechanical; no design decisions.
- **B — change fixture-context semantics.** Use `context: "most_recent:0"`, `context: "most_recent:1"`, etc.; resolve in run.py at session start by querying angles table. More invasive (touches autoresearch/run.py recovery branches), but eliminates the file-rewrite step.

**Recommendation:** A. It's lighter-touch, mirrors the existing daily-cron pattern, doesn't require run.py changes, and rolls forward gracefully if the angles table empties (sync just writes 0 fixtures, harness no-ops the lane).

---

## Gap 2 — `state.db` is path-pinned to the package install location

**What's wrong.** `x_engine/pipeline/db.py:9` declares `DB_PATH = Path(__file__).parent.parent / "state.db"`. With Python's import-resolution, the resolved DB depends on which copy of `x_engine` was imported, which depends on cwd + sys.path. Running `xeng` from the **main repo** hits `/main-repo/x_engine/state.db` (8 angles, populated). Running from this **worktree** would hit `/worktree/x_engine/state.db` — which doesn't exist.

**How verified.**
- `~/.../gofreddy/.venv/bin/python -c "import x_engine; print(x_engine.__file__)"` from worktree cwd → `/worktree/x_engine/__init__.py`, DB resolves to `/worktree/x_engine/state.db` → `OperationalError: no such table: angles`.
- Same Python from main-repo cwd → `/main-repo/x_engine/__init__.py`, DB resolves to `/main-repo/x_engine/state.db` → 8 angles.

**Root cause.** Hardcoded module-relative DB path; no env override. The pattern was fine when there was one checkout; with worktrees it breaks experiment isolation.

**Two paths to fix.**
- **A — env override.** Make `DB_PATH = Path(os.environ.get("X_ENGINE_DB_PATH", DEFAULT))`. Worktree experiments set `X_ENGINE_DB_PATH=/main-repo/x_engine/state.db`. Production cron is unaffected (no env var set). 5-line change in db.py + tests.
- **B — symlink stopgap.** `ln -s /main-repo/x_engine/state.db /worktree/x_engine/state.db`. Zero-code, but every new worktree needs the same symlink and it desyncs from the canonical path.

**Recommendation:** A. The env override is the production-correct primitive: future LaunchAgents can point at the right DB explicitly, and worktree experiments stop silently hitting empty DBs.

---

## Gap 3 — stratified rotation with 0 anchors

**What's wrong.** `search-v1.json` rotation = `{strategy: stratified, anchors_per_domain: 2, random_per_domain: 1, cohort_size: 3}`. Existing 4 lanes have 2-3 anchors each. New lanes have **0 anchors** (all 5 fixtures `anchor: false`). The rotator picks `anchors + n_random` per cohort = `0 + 1 = 1` fixture/cohort for the new lanes vs. `2 + 1 = 3` for existing lanes.

**How verified.** `_sample_fixtures()` at `autoresearch/evaluate_variant.py:374-441` reads `anchors = [f for f in fixtures if f.anchor]` and falls through cleanly when empty. No crash; just smaller sample.

**Root cause / by-design assessment.** For x_engine + linkedin_engine, "anchor angle" semantics don't transfer — angle IDs auto-increment, so `angle 120` today won't be the same content as `angle 120` next week if the table re-seeds. Pinning anchors to specific IDs is meaningless. The 0-anchor state is **structurally correct**, but the master plan didn't document this as an explicit design choice → looks like an oversight.

**Consequences of 1 fixture/cohort.**
- Cross-cohort score comparability is weaker: each cohort's lane score is based on 1 random pick instead of 3 stratified picks. Variance in lane composite is higher.
- Promotion gate trips on noisier signal. Master plan §6.2 promotion thresholds were calibrated for 4-lane stratified rotation.

**Two paths to fix.**
- **A — accept by-design + raise `random_per_domain` for new lanes only.** Add per-lane override so x_engine + linkedin_engine sample `random_per_domain: 3` (3 random picks/cohort, no anchors). Touches `_sample_fixtures` to read per-domain rotation if present, falls through to suite-level rotation otherwise. ~30 min change.
- **B — make some fixtures `anchor: true` arbitrarily.** Defeats the structural argument above; anchor IDs would still drift as table re-seeds.

**Recommendation:** A. Document the design choice (no stable anchor angles; angles are dynamic) in the master plan + add per-lane `random_per_domain: 3` to bring sample size to parity with existing lanes.

---

## Gap 4 — empty `STRUCTURAL_DOC_FACTS` + AUTOGEN drift

**What's wrong.** `lane_registry.py:255, 282` — both new lanes declare `structural_doc_facts=()` + `structural_gate_functions=()`. The `regen_program_docs.py` AUTOGEN rendering at line 45-51 reads these and emits literal text:
```
_No structural gates defined for `x_engine`._
```
into `programs/x_engine-session.md`'s AUTOGEN block.

But the `SessionEvalSpec.structural_gate` callable (`workflows/session_eval_x_engine.py:72-163`) **does** enforce real per-artifact gates: frontmatter validation, `[BODY]/[META]` blocks, length-bracket char counts, `xeng slop-check`. The session-level doc contradicts the per-artifact reality. The pytest.skip carve-out at `tests/autoresearch/test_structural_doc_facts.py` hides the contradiction rather than fixes it.

**How verified.**
- `grep -A2 "AUTOGEN:STRUCTURAL:START" autoresearch/archive/v007-curated/programs/x_engine-session.md` → "_No structural gates defined for `x_engine`._"
- Tests skip carve-out at `tests/autoresearch/test_structural_doc_facts.py` checks `if not bullets and not gates: pytest.skip(...)`.

**Root cause.** Two parallel "structural" mechanisms exist:
1. `LaneSpec.structural_doc_facts + structural_gate_functions` (registry-level) → drives `STRUCTURAL_DOC_FACTS` → drives AUTOGEN block + drives `_validate_<domain>_artifacts` invocation in `evaluate_session.py:436-437`. Used by geo/competitive/monitoring/storyboard.
2. `SessionEvalSpec.structural_gate` (per-artifact callable) → invoked by `run_structural_gate(domain, ...)` at `evaluate_session.py:156-157`. Used by all 6 lanes.

The new lanes use mechanism 2 only; mechanism 1 has empty tuples. The AUTOGEN renderer reads mechanism 1, so it reports "no gates" while mechanism 2 is doing real work.

**Two paths to fix.**
- **A — backfill `STRUCTURAL_DOC_FACTS` for new lanes.** Add prose statements that describe what `structural_gate` actually checks: "Every `drafts/*.md` has `[BODY]` block with char_count fitting `length_bracket` ∈ {sharp, build, case_study}." + "Every `drafts/*.md` `[META]` has `hook`, `authority_anchor`, `specific_number`, `attribution`." + "`xeng slop-check --platform x` passes against `[BODY]`." Then `STRUCTURAL_GATE_FUNCTIONS` references the SessionEvalSpec callable. Drops the pytest.skip carve-out.
- **B — teach the AUTOGEN renderer to read `SessionEvalSpec.structural_gate`.** Walk the callable's source / its docstring at AUTOGEN time. More fragile.

**Recommendation:** A. The registry-level `STRUCTURAL_DOC_FACTS` is meant to be human-readable session-doc copy, not a programmatic check. Backfill it with the prose that describes what `structural_gate` enforces.

---

## Cross-cutting summary

| Gap | Root cause | Fix path | Effort | Mechanical or JR-decision |
|---|---|---|---|---|
| 1. Fixture/angle drift | No sync mechanism between rolling angles → static fixtures | Add `xeng search-v1-sync` daily cron | ~1.5h | mechanical |
| 2. `state.db` path-pinned | Hardcoded module-relative DB path | env override + tests | ~30m | mechanical |
| 3. 0-anchor rotation | Domain shape (dynamic angle IDs) ≠ stratified rotation assumption | Per-lane `random_per_domain: 3` override | ~30m + plan note | mechanical (+ doc) |
| 4. AUTOGEN drift | Two parallel structural mechanisms; new lanes use only one | Backfill `STRUCTURAL_DOC_FACTS` | ~20m | mechanical |

**None of these are JR-decisions.** All four can land mechanically without changing rubric anchor prose. They unblock running **a session loop** end-to-end (assuming rubric stability is solved separately by Phase 2/3).

Total effort: ~3 hours of code + ~30 min testing.
