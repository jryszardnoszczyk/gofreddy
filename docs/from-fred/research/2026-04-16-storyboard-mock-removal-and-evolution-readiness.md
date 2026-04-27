# Storyboard Mock Removal + Evolution Readiness Audit

Date: 2026-04-16
Session: mock removal, wiring validation, fresh-mode validation, evolution blocker analysis

## Changes Made This Session

### 1. Mock mode removed from video_projects router
**File:** `src/api/routers/video_projects.py` (-141 lines)
- Deleted `_MOCK_STORYBOARD_CACHE` (shelve at `/tmp/freddy_mock.db`)
- Deleted 4 helpers: `_mock_storyboard_snapshot`, `_mock_mutate_snapshot`, `_mock_preview_payload`, `_mock_project_not_found`
- Deleted 6 mock branches in: `create_storyboard`, `get_video_project`, `update_video_project`, `update_video_project_scene`, `preview_video_project_anchor`, `preview_video_project_scenes`
- Removed `import shelve`
- Deleted `tests/test_api/test_video_projects_mock_stub.py` (103 lines)

**What was preserved (deliberately):**
- `TaskClientMode = Literal["cloud", "mock"]` + `MockTaskClient` in `src/jobs/task_client.py` — queue-dispatch only, ~30 test files depend on it
- `dependencies.py:1135` in-process generation dispatch — legitimate dev fallback when no Cloud Tasks

### 2. FakeImagePreviewService gate added
**Files:** `src/generation/config.py`, `src/api/dependencies.py`
- New field: `GenerationSettings.preview_mock_enabled: bool = False`
- Env var: `GENERATION_PREVIEW_MOCK_ENABLED=true`
- When true, wires `FakeImagePreviewService` even when `EXTERNALS_MODE=real`
- Uploads deterministic ~1KB PNG to real R2, skips FAL/Gemini image-gen call
- INFO log on startup confirms fake service is active
- Scorer reads `storyboards/*.json`, not rendered images — image credits during evolution optimization are waste

### 3. DB migration: 9 missing columns + 2 constraint relaxations
**File:** `supabase/migrations/20260415000001_video_projects_missing_columns.sql`
- `video_projects`: added `protagonist_description TEXT`, `target_emotion_arc TEXT`
- `video_project_scenes`: added `audio_direction`, `shot_type`, `camera_movement`, `beat`, `preview_scene_score`, `preview_style_score`, `preview_improvement_suggestion`
- Relaxed `video_projects_resolution_check`: `['480p','720p']` → `['480p','720p','1080p']` (FAL ltx-fast emits 1080p)
- Relaxed `video_project_scenes_duration_seconds_check`: `≤15` → `≤30` (FAL ltx-fast supports 20s clips)
- Applied to live local Supabase DB

### 4. Env var additions to `.env`
```
GENERATION_GENERATION_ENABLED=true          # enables real IdeaService (Gemini storyboard drafts)
GENERATION_PREVIEW_ENABLED=true             # already existed
GENERATION_PREVIEW_MOCK_ENABLED=true        # fake image previews for optimization
GENERATION_IDEA_MAX_TOTAL_DURATION=180      # was 120; Gossip.Goblin vids avg 122s
EVOLUTION_EVAL_BACKEND=codex                # evaluate_variant.py requires this
EVOLUTION_EVAL_MODEL=gpt-5.4
EVOLUTION_EVAL_REASONING_EFFORT=high
```

### 5. Storyboard stall_limit bumped
**File:** `autoresearch/archive/current_runtime/workflows/storyboard.py`
- `stall_limit`: 5 → 15 (120s interval × 15 = 30 min tolerance)
- Reason: agent's exploration/refinement loops don't commit to results.jsonl frequently enough; 10 min was insufficient

### 6. Backend restarted
- PID on port 8000, picks up new env + code changes
- Verified: `idea_service=IdeaService`, `creative_service=CreativePatternService`, `image_preview_service=FakeImagePreviewService`, `generation_enabled=True`, `preview_mock_enabled=True`

---

## Git Tracking Status

**Tracked (will survive git operations):**
- `src/api/routers/video_projects.py` — mock branch removal (-117 lines)
- `src/api/dependencies.py` — FakeImagePreviewService wiring gate (+7 lines)
- `src/generation/config.py` — `preview_mock_enabled` field (+11 lines)
- `tests/test_api/test_video_projects_mock_stub.py` — deleted (-102 lines)
- `docs/research/2026-04-16-storyboard-mock-removal-and-evolution-readiness.md` — this doc (new, untracked, needs `git add`)

**NOT tracked (live only on disk, will NOT survive git reset/fresh clone):**
- `.env` — `GENERATION_GENERATION_ENABLED`, `GENERATION_PREVIEW_MOCK_ENABLED`, `GENERATION_IDEA_MAX_TOTAL_DURATION`, `EVOLUTION_EVAL_BACKEND/MODEL/REASONING_EFFORT`
- `supabase/migrations/20260415000001_video_projects_missing_columns.sql` — new file, needs `git add`
- `autoresearch/archive/current_runtime/workflows/storyboard.py` — `stall_limit=15` (entire `current_runtime/` is NOT in git)
- `autoresearch/archive/current_runtime/` is a runtime working copy, not version-controlled. Changes here must be manually synced to archive variants for evolution.

**DB state (not in git at all):**
- 9 new columns on `video_projects` + `video_project_scenes`
- Relaxed CHECK constraints (resolution, duration_seconds)
- Exists only in the live local Supabase instance
- The migration SQL file captures the changes for replay after `supabase db reset`

---

## Validation Results

### Smoke test (HTTP endpoint chain)
All 6 steps green:
1. `POST /v1/conversations` → 201, real conversation in DB
2. Reused known-good analysis_ids (Gossip.Goblin prior patterns)
3. `GET /v1/creative/{aid}` → 200, cached creative patterns
4. `POST /v1/video-projects/storyboard` → 201, 7 real Gemini-generated scenes, evaluator scored 9.29/10
5. `POST /preview-anchor` → 200, FakeImagePreviewService → real R2 signed URL
6. `POST /preview-scenes` → 200, 7/7 scenes ready

### Multiturn session (single codex process, 37 turns, 32 min)
- 5 storyboards kept (2 discarded for "missing camera language", retried successfully)
- 30 frames, all approved with QA score 8
- Agent declared COMPLETE
- **Scorer: domain_score = 0.076**, dimension_scores = [0.5, 1.0, 0.0, 1.0, 0.0, 0.125, 0.0, 0.5]
- structural_passed = true, grounding_passed = true

### Fresh-mode session (per-iteration codex spawns, 7/15 iterations, ~35 min)
- 5 storyboards kept (0 discards — better than multiturn)
- 34 frames, all approved
- **Scorer: domain_score = 0.150**, dimension_scores = [0.5, 1.0, 0.0, 1.0, 0.0, 0.5, 0.375, 0.5]
- structural_passed = true, grounding_passed = true
- Scorer eval took 53s (within 400s budget)

Iteration breakdown:
| Iter | Phase | Duration | Notes |
|------|-------|----------|-------|
| 1 | SELECT_VIDEOS | ~5min | Catalog timeout at limit=50, recovered at limit=35 → 18 videos |
| 2 | ANALYZE_PATTERNS | ~7min | 18 patterns extracted (16/18 cache hits) |
| 3 | PLAN_STORY | ~13min | 5 plans + SB-6 refinement. **Barely fit 900s timeout** |
| 4 | IDEATE | ~5min | 5/5 kept, 0 discards |
| 5 | GENERATE_FRAMES | ~4min | 34 frames rendered+approved, one /verify 500 (non-blocking) |
| 6 | REPORT | ~2min | Finalization |
| 7 | (exit) | immediate | Session complete |

---

## DB State Confirmed

Harness user `62d4c815-3a46-40cc-a997-6d683d3336fc`:
- User row: exists (`harness@test.local`)
- Subscription: `tier=pro, status=active`
- API keys: 2 seeded (`autoresearch-seed-2026-04-08`, `autoresearch-fixpack-test`)

Video analysis cache:
- 18/18 Gossip.Goblin videos cached in `video_analysis`
- 16/18 have `creative_patterns` rows (2 have error payloads from failed Gemini extraction)
- Cache hits make ANALYZE_PATTERNS nearly free for repeated variants

Creator catalog:
- Gossip.Goblin: **cached** (200)
- TechReview: **NOT ingested** (404, needs `POST /v1/analyze/creator`)
- MrBeast: **NOT ingested** (404, needs `POST /v1/analyze/creator`)

---

## Findings to Triage (ordered by severity for evolution)

### BLOCKER-1: Variants clone from archive/v005, not current_runtime
**Impact:** Every new variant misses ALL our fixes (stall_limit=15, workflow changes, program updates).
**Evidence:** `diff -rq current_runtime/workflows/ v005/workflows/` shows many files differ. `v005/workflows/storyboard.py` has `stall_limit=5`.
**Fix:** Create v006 from current_runtime and register as frontier parent. Or sync current_runtime changes into v005.
**Effort:** ~15 min

### BLOCKER-2: PLAN_STORY barely fits 900s per-iteration timeout
**Impact:** Fresh-mode iteration 3 (PLAN_STORY) took ~13/15 min. Evolution variants that do deeper refinement or hit slower Gemini responses WILL time out. When the iteration times out, uncommitted work is lost.
**Evidence:** Fresh-mode iteration 3 log was 1.7MB, 13 min wall time.
**Fix options:**
- (a) Bump fixture timeout from 900 to 1200 or 1800 in `eval_suites/search-v1.json`
- (b) Split PLAN_STORY across 2 iterations (the agent can save partial state to session.md)
- (c) Reduce story count from 5 to 3 (fewer plans = faster eval)
**Effort:** 5 min for (a), ~30 min for (b), trivial for (c)

### BLOCKER-3: TechReview + MrBeast creators not in catalog
**Impact:** 2 of 3 storyboard fixtures will spend ~5-10 min on cold ingestion in iteration 1 (POST /analyze/creator). Reduces effective iteration budget.
**Evidence:** Both return 404 from `/v1/creators/youtube/{handle}`.
**Fix:** Pre-ingest via `curl -X POST /v1/analyze/creator` for both handles before launching evolution.
**Effort:** ~10 min (run two curl commands, wait for ingestion)

### WARN-4: eval_suites/search-v1.json says claude/sonnet but we validated with codex/gpt-5.4
**Impact:** We set `EVOLUTION_EVAL_BACKEND=codex` + `EVOLUTION_EVAL_MODEL=gpt-5.4` in .env, which overrides the suite. This works but means the suite config is misleading. If someone removes the env override, variants will use claude/sonnet which is unvalidated.
**Evidence:** Suite file line 4-8: `"eval_target": {"backend": "claude", "model": "sonnet"}`. Our .env overrides this.
**Fix options:**
- (a) Update suite JSON to match env (codex/gpt-5.4)
- (b) Leave env override in place, document
- (c) Validate with claude/sonnet separately
**Effort:** 5 min for (a), 0 for (b), ~40 min for (c)

### WARN-5: SB-3 and SB-5 are stuck at 0.0 in both runs
**Impact:** Two criteria consistently score zero across runs. This limits the score ceiling — even perfect SB-1/2/4/6/7/8 with zeros in SB-3/5 produces a geometric mean of 0 (or near-0 with smoothing). Evolution is optimizing against a ceiling set by these two criteria.
**Evidence:** Both multiturn (0.076) and fresh (0.150) had SB-3=0.0, SB-5=0.0.
**Fix:** Need to understand WHAT SB-3 and SB-5 measure. If they're measuring something the agent can't control (e.g., real video rendering quality), they should be removed or reweighted. If they're measuring something fixable, the program prompt needs adjustment.
**Effort:** ~30 min to diagnose criteria definitions + decide on fix
**Criteria definitions location:** `autoresearch/archive/current_runtime/workflows/session_eval_storyboard.py` (SB-1 through SB-8 CRITERIA dict)

### WARN-6: Unit 3.6 `source_analysis_ids_identical_likely_replay` false positive
**Impact:** Fires on every storyboard session (all storyboards cite the same creator's pattern pool). Does NOT block session-level scoring (backend `_validate_storyboard` doesn't check it). DOES trigger `session_evaluator_guard: rework_required` which makes the agent see warnings. Burns refinement cycles.
**Evidence:** Both multiturn and fresh runs had 5× structural_gate fail with this check.
**Location:** `autoresearch/archive/current_runtime/scripts/evaluate_session.py:263`
**Fix:** Delete the check or scope it to cross-session (not within-session) comparison. The check was designed to detect replay attacks but fires on legitimate single-creator storyboard sessions where all storyboards naturally share the same source patterns.
**Effort:** 5 min

### WARN-7: session_summary.json status = "IN_PROGRESS" after COMPLETE
**Impact:** Both multiturn and fresh runs show `"status": "IN_PROGRESS"` in session_summary.json despite the agent declaring COMPLETE and the runner exiting cleanly. Evolution selection may misinterpret this.
**Evidence:** `cat sessions/storyboard/Gossip.Goblin/session_summary.json` → `"status": "IN_PROGRESS"`, `"exit_reason": "IN_PROGRESS"`
**Fix:** The runner's `summarize_session` post-hook needs to read session.md's `## Status` field and propagate to session_summary.json.
**Effort:** ~15 min

### WARN-8: /verify endpoint returns 500 for some scenes
**Impact:** One scene in the fresh-mode run got 500 from the verify endpoint twice. Agent fell back to using backend QA score (8). Non-blocking but loses scene_score/style_score detail.
**Evidence:** `results.jsonl` entry: `"http_status":500,"message":"/verify returned internal_error twice"`
**Fix:** Check backend log for the verify error. May be FakeImagePreviewService.verify_preview raising unexpectedly, or a route mismatch.
**Effort:** ~15 min to diagnose

### INFO-9: Creator catalog hangs at limit>10 for Gossip.Goblin
**Impact:** Every session's SELECT_VIDEOS phase retries multiple curl calls before falling back to limit=35 or yt-dlp. Adds ~2-5 min per variant. Not a blocker but wastes iteration budget.
**Evidence:** All 3 sessions (multiturn #1, multiturn #2, fresh) hit this.
**Fix:** Backend investigation of why the catalog endpoint hangs for this creator at higher limits. Or pre-cache the video list.
**Effort:** Unknown

### INFO-10: Backend is a shared singleton with no auto-restart
**Impact:** If uvicorn crashes during a multi-hour evolution run, all in-flight variants fail.
**Fix:** Wrap in a supervisor (e.g., `while true; do uvicorn ...; sleep 1; done`) or use systemd/launchd.
**Effort:** 5 min

### INFO-11: GENERATION_* env vars not in evolve_ops._ALLOWED_ENV_KEYS
**Impact:** These env vars don't propagate through the evolution harness to variant runners. This is FINE because the backend (not the runner) reads them. But if the backend restarts without them, variant behavior changes silently.
**Evidence:** `grep GENERATION autoresearch/evolve_ops.py` returns nothing.
**Fix:** Not strictly needed (backend reads .env directly). Document that backend must be running with correct env before evolution starts.
**Effort:** 0 (documentation only)

---

## Architecture Notes for Next Session

### Two evaluator paths (critical to understand)
1. **Per-story agent-time evaluator**: `autoresearch/archive/current_runtime/scripts/evaluate_session.py` — runs during PLAN_STORY phase, checks SB-1 through SB-8 criteria + Unit 3.6 `_validate_storyboard_artifacts`. Produces KEEP/DISCARD/REWORK per story.
2. **Session-level scorer**: `freddy evaluate variant storyboard <session_dir>` → `src/evaluation/service.py:evaluate_domain()` → `src/evaluation/structural.py:_validate_storyboard()` + 8 LLM judges. Produces `domain_score` for evolution fitness. Does NOT contain Unit 3.6 check.

### Evolution execution model
- `evaluate_variant.py` runs variants with `--strategy fresh` (not multiturn)
- Each variant is `shutil.copytree(parent, variant_dir)` then sessions/ cleared
- Each fixture gets `max_iter` iterations of fresh codex spawns (100 turns, 900s each)
- `_run_fixture_session` subprocess timeout = `fixture.timeout × fixture.max_iter + 180`
- Scorer timeout: 400s per `freddy evaluate variant` subprocess call

### Parent selection for storyboard (frontier is null)
- `frontier.json` shows `"storyboard": null` — no storyboard evolution has ever run
- `select_parent.py` falls back to the earliest entry in `lineage.jsonl` with search_metrics, or the absolute earliest entry
- First storyboard variant will clone from v001 or v002/v003 (geo/competitive frontiers)
- Our `current_runtime` fixes need to land in the archive before evolution runs

### Scorer output shape
```json
{
  "domain_score": 0.150,           // geometric mean of normalized dimension_scores × length_factor
  "dimension_scores": [0.5, 1.0, 0.0, 1.0, 0.0, 0.5, 0.375, 0.5],  // SB-1 through SB-8
  "grounding_passed": true,
  "structural_passed": true,       // backend _validate_storyboard (NOT Unit 3.6)
  "evaluation_id": "uuid",
  "dqs_score": null
}
```

### Service wiring verified
| Service | Implementation | Env dependency |
|---------|---------------|----------------|
| idea_service | IdeaService (real Gemini) | GENERATION_GENERATION_ENABLED=true + GEMINI_API_KEY |
| creative_service | CreativePatternService | GEMINI_API_KEY + DB pool |
| image_preview_service | FakeImagePreviewService | GENERATION_PREVIEW_MOCK_ENABLED=true |
| video_project_service | VideoProjectService | All above + DB pool |
| task_client | MockTaskClient (queue only) | Default dev mode |

### Fresh-mode execution model
- `evaluate_variant.py:427` passes `--strategy fresh` (NOT multiturn)
- `run_domain_fresh` loops `for i in range(1, max_iter + 1)`, spawning codex per iteration
- Each iteration: `FRESH_MAX_TURNS=100` (from `runtime/config.py:18`), timeout=fixture.timeout (900s)
- Outer subprocess timeout: `fixture.timeout × fixture.max_iter + 180` = 900×15+180 = 13,860s
- `max_iter` in fixture is ONLY used in fresh mode (ignored in multiturn)
- Agent reads `session.md` at start of each iteration, runs one or more phases, exits
- The iteration timeout (900s) is the real constraint — PLAN_STORY used 13/15 min

### Cost per variant (estimated)
- SELECT_VIDEOS: ~$0 (catalog + curl, no Gemini)
- ANALYZE_PATTERNS: ~$0-2 (cache hits for known creators, $2 for cold)
- PLAN_STORY: ~$1-3 (Gemini story generation + 8-criterion judge ensemble × 5 stories)
- IDEATE: ~$1-2 (Gemini IdeaService × 5 drafts + storyboard evaluator)
- GENERATE_FRAMES: ~$0 (FakeImagePreviewService)
- Scorer: ~$1-2 (8 LLM judges, 53s)
- **Total: ~$3-9 per variant** (heavily dependent on cache hit rate)
