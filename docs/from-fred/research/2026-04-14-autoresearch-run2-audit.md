---
title: "Autoresearch run #2 audit — post-fixpack baseline"
date: 2026-04-14
status: active
---

# Autoresearch run #2 audit — post-fixpack baseline

> **READER NOTE**: This doc captures 3 audit passes done chronologically. Later passes correct earlier ones. For triage, use the **MASTER INDEX** below — it supersedes any conflict between sections. The full pass-by-pass content is preserved for provenance and evidence traceability but should be read as "what each pass found", not "ground truth of the final state".

## Context

All 4 workflows were re-run after applying the 18-fix fixpack (commit `6bcbe36`). All 4 runs used **Codex gpt-5.4** as the backend (geo/monitoring/storyboard = high reasoning; competitive = xhigh). Verified by reading `multiturn_session.log` headers: "OpenAI Codex v0.120.0 / model: gpt-5.4 / reasoning effort: high". The first pass mis-labeled geo as "Claude backend" — ignore that claim wherever it appears below.

**Session locations**:
- `autoresearch/archive/current_runtime/sessions/{geo,competitive,monitoring,storyboard}/{client}/`

**Pre-run infrastructure state**:
- Docker/Supabase: all 4 containers healthy
- `weekly_digests` UNIQUE constraint: applied
- Freddy backend: running on `:8000`
- `PREVIEW_ENABLED=false` (bug — not yet flipped at run time)
- Seed data: 32 Shopify mentions across 7 themes (NOT 47 — the 47 count came from reading an uncommitted working-tree modification)

---

## MASTER TRIAGE INDEX

**Use this section first**. Every finding below links to its detailed evidence section with the "see" references. Status reflects the final, corrected state after 3 audit passes.

### True BLOCKERS (6) — fix before any further runs

| ID | Title | Owner file | Fix type |
|---|---|---|---|
| **BLOCK-1** | MON date-to bug drops 7 of 32 mentions, fires low-volume shortcut | `src/api/routers/monitoring.py` (no normalization) + `src/monitoring/repository.py:617-619` | One-line: normalize bare-date `date_to` to end-of-day before passing to repo |
| **BLOCK-2** | GEO `build_geo_report.py:188` visibility-truthiness falsely reports timeout as "available" | `autoresearch/archive/current_runtime/scripts/build_geo_report.py:188` | One-line: check `status != "timeout"` and `queries_with_data > 0` |
| **BLOCK-3** | GEO optimized pages ship user-facing content leak ("Current AI citation count \| Unavailable") despite eval 0.0 fail | `optimized/pricing.md:38-43`, `optimized/keyword-research-toolkit.md:38` + eval keep-rule | Wire eval feedback into KEEP guard OR fix threshold weighting |
| **BLOCK-4** | STORY replay: agent copies selected_videos.json + patterns/ + 4-of-5 stories from prior archived session, fabricates `same_runtime_archive_fallback` source label | Harness `session_init` recreates `sessions/_archive/` every run; storyboard program has no guardrails | (a) stop harness writing `_archive/` into sessions tree, (b) add "no cp from archive" rule to program, (c) add `POST /v1/analyze/creator` bootstrap instruction |
| **BLOCK-5** | STORY `_mock_storyboard_snapshot` discards `body.context` — collapses full 6-scene plans to 1 stub scene with truncated title | `src/api/routers/video_projects.py:343-414` | Parse `body.context` as JSON, extract `scenes[]`, build per-scene responses |
| **BLOCK-6** | STORY `_MOCK_STORYBOARD_CACHE` is module-level dict — breaks on worker restart / workers>1 | `src/api/routers/video_projects.py:340` | Persist to SQLite at session_dir or add `is_mock` column to video_projects table |

### Cross-lane HIGH severity (6)

| ID | Title | Status | Details |
|---|---|---|---|
| **CROSS-1** | `session_summary.findings_count` reports 0 on competitive/monitoring/storyboard | **PARTIALLY FALSE** — geo's regex `r"^### \["` correctly returns 8/8 for geo. Bug may still exist for other lanes if their findings.md format differs. | Verify each lane's findings.md format against `summarize_session.py:110` |
| **CROSS-2** | CLI contract drift in all 4 program files (`visibility --brand/--keywords`, `detect` needs `https://`, `search-ads` needs `.com`) | Real | Regenerate command tables from `freddy <cmd> --help` |
| **CROSS-3** | Iteration counter: `total=4, productive=8` on storyboard; `uncategorized=1` on geo | Real. Fix #14 reconciliation guard didn't fire. | Debug guard logic; add "complete" to productive status list |
| **CROSS-4** | Git-diff log bloat (~80% of log bytes) | **Root cause corrected**: NOT harness instrumentation. Codex CLI dumps diffs after every `exec` turn (not just patches — also after `find`, `jq`, `freddy digest persist`, `evaluate_session.py`). A `strip_repeated_diffs.cpython-314.pyc` exists in `__pycache__` with no `.py` source, suggesting it was integrated and reverted. | Either find codex flag to suppress, or restore the strip script integration. |
| **CROSS-5** | Evaluator lenience: hard fails ship as KEEP | **Rule misframed**: real rule is `threshold = ceil(N*3/8)` at `autoresearch/harness/session_evaluator.py:82-88`, `DEFAULT_PASS_THRESHOLD = 0.5`. No "1-of-8" rule exists. Issue is real but fix targets `compute_decision_threshold` and per-criterion weighting. |
| **CROSS-6** | `working_dir` drift: all bash commands run from `autoresearch/archive/v001` (FROZEN baseline variant), not current runtime session dir | Real. Plausibly load-bearing for storyboard replay — prior-session archive lives in `v001/sessions/_archive/`, agent finds it because cwd is wrong. **Check if affects all 4 lanes.** | Find cwd assignment in `autoresearch/harness/agent.py` or runner script |

### GEO lane (complete list, corrected)

| ID | Severity | Title | Status |
|---|---|---|---|
| **BLOCK-2** | BLOCKER | `build_geo_report.py:188` visibility truthiness | Real. Exact fix: see GEO3-23 below |
| **BLOCK-3** | BLOCKER | Content leak ships despite eval 0.0 fail | Real. See GEO-B2 |
| **GEO-TP-C1** | BLOCKER | **Evaluator has NEVER read audit data** — `session_eval_geo.py:99-117` `load_source_data` only reads `pages/{slug}.json` + `gap_allocation.json`, never `audits/`. Cross-lane exposure likely. | Real, source-code confirmed |
| **GEO-NEW-7** | HIGH | `build_geo_report.py:137-141` slug mismatch: `/features/backlinks/` → `features-backlinks` (file slug is `backlinks`), matches to empty `{}` for 4 of 6 pages | Real. Fix: `slug = page.split("/")[-1] or "index"` |
| **GEO3-22** | HIGH | Three different `avg_delta` values across artifacts (0.50 / 0.503 / 0.555) — slug mismatch causes `report.md` to publish a WORSE number than session ground truth | Real. Fixed by GEO-NEW-7 |
| **GEO3-23** | HIGH | `measured_visibility = bool(visibility_data)` returns True for timeout sentinel | Real. Correct condition: `isinstance(dict) AND status NOT IN {"timeout","unavailable"} AND queries_with_data > 0` |
| **GEO3-24** | HIGH | `freddy scrape` returns ONLY noscript browser-warning shell on Semrush (SPA). `pages/pricing.json` has word_count=159 all from "Your browser is out of date" banner. Agent recovered real prices via undocumented "live pricing JS" workaround (log:8829/8851). | Real. Tool-level blocker masquerading as agent ingenuity. |
| **GEO-NEW-3** | HIGH | **NOT a broken audit-context loader — there is no loader at all.** `audits/pricing.full.json` has `canonical_url.detected: false` but evaluator never sees it. | Real. Fix in `session_eval_geo.py:load_source_data`. Check all 4 lane eval specs. |
| **GEO-NEW-4** | HIGH | `freddy detect` `answer_first_intro` parser extracts Semrush `<noscript>` browser-warning banner on EVERY page (22 words "Your browser is out of date...") | Real across all 12 audit files |
| **GEO-NEW-5** | HIGH | `freddy detect --full` returns ZERO extra data — entire 12-line diff vs base is `seo_full.dataforseo_error: "provider_unavailable"` + null pagespeed. 6 `--full` calls per session buy nothing. | Real |
| **GEO-NEW-6** | HIGH | Evaluator inconsistency on IDENTICAL template: `pricing.md:38` GEO-4 scored 0.0 ("broken column"); `keyword-research-toolkit.md:38` (identical column) scored 1.0 ("tone perfectly matches"). Same run, same evaluator. | Real. Multi-model ensemble (fix #1) would catch — but `OPENAI_API_KEY` not set. |
| **GEO-NEW-8** | HIGH | Variance concentrated in GEO-4 (voice) + GEO-8 (technical recs). Unanimous 5/5 on GEO-1/3/5/6/7. All 4 KEEP-with-hard-fail cases are in GEO-4/GEO-8. | Real. Weight these two in REWORK rule. |
| **GEO-H1** | HIGH | "Before" scores in results.jsonl are agent-fabricated (not measured). No `(simulated)` tag. Entire delta table unverifiable. | Real |
| **GEO-H4** | HIGH | Evaluator hallucinated `freddy detect` as "hallucinated tool". Real CLI used throughout session. | Real. Multi-model ensemble would catch. |
| **GEO-H5** | HIGH | Evaluator `raw_score 3/5` → `passes: true` with `score: 0.5`. "Barely mediocre" passes. | Real. Tighten threshold to raw_score ≥ 4 OR add tiers. |
| **GEO-M2** | MEDIUM | `report.md` markdown table broken by unescaped pipes in query cells | Real |
| **GEO-M3** | MEDIUM | domain-overview evaluator called 4 times but results.jsonl says `attempt:3` | Real. Rework cap silently exceeded. |
| **GEO-M4** | MEDIUM | `session_summary.uncategorized: 1` for `type:"report"` iteration | Fixed by CROSS-3 |
| **GEO3-25** | MEDIUM | "Source words" column in `session.md:17-22` lies — 159/296/299/444/253/283 are all noscript banner word counts, not real page content | Real. Downstream of GEO3-24. |
| **GEO-L1** | LOW | `findings.md:14` claims backlinks "8/8 criteria passing" but eval file says `1_of_8_evaluated_failed`. Finding is wrong. | Real |
| **GEO-L2** | LOW | Pricing GEO-6 returned `passes: null` on attempt 1 ("First item, cross-item comparison N/A"). Order-dependent scoring not signaled. | Real |
| **GEO-L3** | LOW | `report.md:5` claims "Average Delta: +0.555" — inconsistent with session.md and results.jsonl (0.50/0.503) | Fixed by GEO-NEW-7 |
| **GEO-L4** | LOW | Visibility timed out at 45s and was never retried despite 10 iterations | Real |
| **GEO-L5** | LOW | `top_heading_targets` contains literal string `"FAQ"` — report builder not normalizing heading extraction | Real |
| **GEO-L6** | LOW | `gap_allocation.json` has all 6 slugs as single-item batches — no parallelization | Anti-pattern |
| **GEO-L7** | LOW | ~~`audits/*.full.json` only for pricing~~ | **FALSE**. All 12 files exist. |
| **GEO3-27 / verification-schedule** | LOW | `verification-schedule.json` is a static template with hard-coded dates 2026-04-13/04-20/05-04/05-25 — not derived from session state | Real |

**GEO verified clean**: `src/geo/service.py:189` visibility timeout is correctly `45.0`s (Fix #2 landed). `optimized/*.md` markdown structure is internally consistent. Real Semrush prices ($139.95/$249.95/$499.95) recovered from JS bundle, not hallucinated.

### Competitive lane (complete list, corrected)

| ID | Severity | Title | Status |
|---|---|---|---|
| **COMP-H1** | HIGH | "0 observed ads" framing is **unattributable** — could be Foreplay outage OR fix #11 domain filter dropping all ads. Claude run at 12:24 got 100+ ads; Codex run at 21:06 got 0. | Real — see COMP3-22 below for root-cause expansion |
| **COMP3-22** | HIGH | `foreplay.py:86-101` silently returns `[]` on domain mismatch; `service.py:129-141` silently filters by link_url host. Persisted envelope has no `pre_filter_count`/`filtered_count`/`brand_id` audit fields. **Cannot distinguish code-bug from provider outage.** | Real. Fix: add audit telemetry fields. |
| **COMP3-23** | HIGH | `prior_brief_summary.json` is structurally broken — `extract_prior_summary.py` runs in `pre_summary_hooks` AFTER brief.md is written, reads the JUST-WRITTEN brief and writes summary. "Prior" is actually current. Cross-session continuity impossible. | Real. Source-code confirmed in `workflows/competitive.py:13-19` and `scripts/extract_prior_summary.py`. |
| **COMP-H2** | HIGH | 3-point Codex delta (37 vs 40) concentrated in CI-3 and CI-5, both traceable to missing ad data | Real (but both runs are Codex, not Claude vs Codex) |
| **COMP-H3** | HIGH | Codex picked Miro instead of Adobe — Miro immediately failed with `AllProvidersUnavailableError`, no reconsideration | Real |
| **COMP-NEW-15** | **FALSE POSITIVE** | ~~Codex hallucinated "rate-limit / circuit-open" phrasing in brief~~ | **INVALIDATED by TP-C4**: `canva_visibility_raw.json` and `miro_visibility_raw.json` contain literal `"error": "Rate limit exceeded"` (3x) and `"Service temporarily unavailable (circuit open)"` (6x). Codex was accurately citing the JSON. IC "credit" errors are an upstream layer the agent doesn't see. |
| **COMP-NEW-16** | HIGH | Provider failures are 3 distinct modes (AllProvidersUnavailableError / ad_count=0 clean success / credit-exhausted visibility), not 1 "outage" | Real |
| **COMP3-24** | MEDIUM | Structural gate SOV regex is satisfied by the NEGATION: `"A 0% SOV label would be misleading"` + threshold numbers `>25%`/`>5`. Zero meaningful SOV numbers in brief. Gate passes uselessly. | Real |
| **COMP3-25** | MEDIUM | Archive evidence: earlier Codex run picked Sketch/Canva/Adobe (40/40), this run picked Sketch/Canva/Miro (37/40). Non-deterministic slate selection. | Real |
| **COMP-M1** | MEDIUM | Structural gate REWORK invisible in results.jsonl (first brief 2336 words → rewritten to 1602, verify row only shows `attempt:1`) | Real |
| **COMP-M2** | MEDIUM | Figma client-baseline missing GEO/crawler data — program only mandates `freddy search-ads` for baseline, not `detect` | Program rule gap |
| **COMP-M3** | MEDIUM | Visibility lane dead for all competitors (Canva/Miro credit-exhausted, Sketch timeout) | Real |
| **COMP-M4** | MEDIUM | ScrapeCreators credit exhaustion in stderr not detected by Codex (Claude did detect) | Real |
| **COMP-NEW-17** | MEDIUM | Canva scrapes return bot-block pages ("Please update your browser", 54 words). Brief's "selectively gated platform" archetype is partially circular. | Real |
| **COMP-NEW-18** | MEDIUM | Structural gate failure invisible in results.jsonl | Confirmed by COMP-M1 |
| **COMP-NEW-19** | MEDIUM | TikTok `search-content` returns ~85 bytes for all 3 competitors — systemic provider gap | Real |
| **COMP3-26** | LOW | Aborted sibling run at `archived_sessions/20260413-210604-competitive-figma/` — `results.jsonl` empty, `Status: NOT_STARTED`. Possible double-invocation. | Real |
| **COMP-L1** | LOW | IC credit-exhausted signals in stderr not surfaced to results.jsonl | Real |
| **COMP-L2** | LOW | Priority Queue orders by analysis order, not quality | Cosmetic |
| **COMP-L3** | LOW | `weighted_score: 90.6` field unreliable across runs | Real |
| **COMP-L4** | LOW | `findings_count: 0` | See CROSS-1 |
| **COMP-L5** | LOW | `brief.md:68` and `prior_brief_summary.json` disagree about prior-brief existence | Explained by COMP3-23 |

### Monitoring lane (complete list, corrected)

| ID | Severity | Title | Status |
|---|---|---|---|
| **BLOCK-1** | BLOCKER | Date-to bug drops 7 of 32 mentions (themes T5 "Shop app redesign" + T6 "Positive merchant spotlight"), lands at exactly 25 < 30 low-volume threshold | Real. See MON-NEW-1 + TP-C5 correction |
| **MON-NEW-1** | BLOCKER | CLI `--date-to 2026-04-12` → `datetime(2026,4,12,0,0,0)` → SQL `published_at <= '2026-04-12 00:00:00'`. ALL April 12 mentions silently excluded. | Real. Fix: `src/api/routers/monitoring.py` add `date_to` normalization (currently NONE exists anywhere in pipeline) |
| **MON-H1** | HIGH | ~~Agent didn't identify date-to bug~~ | **PARTIALLY FALSE** (TP-C7): `digest.md:8` says "no loaded mention landed on 2026-04-12, late-week confidence MEDIUM". Agent observed symptom. Program at line 84 only requires start-side gap check. This is a program gap, not discipline. |
| **MON-NEW-2** | HIGH | Low-volume threshold is exact `< 30` at `workflows/session_eval_monitoring.py:115`. Program prompt line 88 says "(< ~30 mentions)" with misleading tilde. | Real |
| **MON-H2** | HIGH | Git-diff log bloat (656KB, 80% repeated diffs) | See CROSS-4 (root cause corrected to codex CLI, not harness) |
| **MON-H3** | HIGH | `session_summary.findings_count: 0` despite 4 findings | See CROSS-1 |
| **MON-H4** | HIGH | ~~`digest_eval.json` KEEP with `1_of_7_failed` inconsistent~~ | **FALSE POSITIVE** (TP-FP-6): consistent with real rule `ceil(7*3/8)=3`, 1<3=KEEP. Issue is the rule being too lenient, not inconsistency. |
| **MON3-22** | HIGH | Agent never questioned 2 missing thematic clusters (Shop app / Positive merchant have distinctive keywords completely absent from data). Ran jq grouping by theme, saw 5 themes, never asked "where are the consumer-side themes?" | Real |
| **MON-M1** | MEDIUM | Dual persistence without agent awareness (persisted at log:1884 and log:5471) | Real. DB upsert handled it but pattern is wasteful. |
| **MON-M2** | MEDIUM | `avg_story_delta: 0` in digest-meta.json is misleading for low-volume path | Real |
| **MON-M3** | MEDIUM | `results.jsonl` has only 1 entry (`select_mentions`) — no `deliver` or `persist` row. Low-volume path exempts these from structural gate. | Real. Program rule gap. |
| **MON-M4** | MEDIUM | Agent contradicted prior DB digest without reconciling | Real |
| **MON3-23** | MEDIUM | Stale prior digest in DB contains "Coverage begins on 2026-04-07, leaving one-day gap for 2026-04-06" — factually wrong for current data. Agent didn't flag or correct. | Real |
| **MON-NEW-20** | MEDIUM | `digest-meta.json` file permissions are 0600 (group/other unreadable). All other session artifacts 0644. | Real. `mktemp` inside `freddy digest persist` preserves restrictive umask. |
| **MON3-24** | LOW | No pagination bug: CLI auto-pagination terminates correctly with 25<50 limit. Verified clean. | Clean |
| **MON-L1** | LOW | No schema-level anomaly flag for window-end gap | Real |
| **MON-L2** | LOW | Engagement subtotal tabulation fragile | Real |
| **MON-L3** | LOW | Empty stories/ and anomalies/ directories not documented as intentional | Real |
| **MON-NEW-21** | LOW | PROCESS finding is self-referential noise ("Completion Checklist Applies To Low Volume" re-articulates prompt rules) | Real. Agent feedback loop. |
| **MON-B1 / weekly_digests** | **FALSE POSITIVE** | ~~weekly_digests UNIQUE constraint not enforced~~ | **INVALIDATED**: constraint IS applied, only 1 row in DB. Agent's two persist calls upserted correctly via `ON CONFLICT DO UPDATE`. |

### Storyboard lane (complete list, corrected)

| ID | Severity | Title | Status |
|---|---|---|---|
| **BLOCK-4** | BLOCKER | **SESSION IS A REPLAY**. Agent `cp`'d `selected_videos.json` + `patterns/*.json` + `stories/*.json` (4 of 5 byte-identical) from `sessions/_archive/20260413-210243-storyboard-MrBeast/`. All 5 storyboards carry IDENTICAL 17-element `source_analysis_ids` array. Agent fabricated `same_runtime_archive_fallback` source label — zero matches in any program/harness file. | Real. See STORY-NEW-9, 10, 11. |
| **STORY-TP-C2** | correction | "First attempt 404 sequence" in frame_generation_errors.json | **CORRECTED**: NOT a current-session attempt. Was the agent reading the PRIOR session's session.md (project IDs `0209104a...`, `1a2c065f...` etc., which appear NOWHERE in current session). Agent internalized prior-session diagnostic conclusions. Replay is more comprehensive than first flagged. |
| **STORY-TP-C3** | structural | Fix #12 (move `_archive/` out of sessions) | **CORRECTED**: Fix #12 is STRUCTURALLY BROKEN, not just clobbered. At audit time the `_archive/` directory doesn't exist on disk, yet `cp` commands succeeded at runtime. The harness `session_init` creates `sessions/_archive/<timestamp>/` populated with prior data then deletes it after the run. Fix #12 is fighting the harness itself. |
| **BLOCK-5** | BLOCKER | `_mock_storyboard_snapshot` NEVER reads `body.context` (only `body.topic`, `body.style`). Program line 363 tells agent to pass full story plan as `context` — mock backend silently drops it. Scene title = `body.topic[:48]` (truncation symptom). Scene prompt = `f"{topic}. {style}."` No scenes array ever read. | Real. `src/api/routers/video_projects.py:343-414` |
| **BLOCK-6** | BLOCKER | `_MOCK_STORYBOARD_CACHE` is a module-level dict. Breaks on worker restart or `workers>1`. Explains prior-session 404s the current agent read. | Real. `src/api/routers/video_projects.py:340` |
| **STORY-NEW-12** | HIGH | Storyboard program has NO `SELECT_VIDEOS` fallback rule. `programs/competitive-session.md:310` and `programs/geo-session.md:349` both say "do NOT re-attempt same failed command". Storyboard has no equivalent. | Real program gap |
| **STORY-H1** | HIGH | 17 selected videos are real MrBeast videos but all have `duration_seconds: null` and `posted_at: null`. Recency gate silently disabled. Fix #15 (YouTube backfill) was never invoked because agent didn't hit live API. | Real |
| **STORY-H2** | HIGH | Mock storyboard collapses rich 6-scene plans to 1-scene stubs. `/recompose` returns 503 `generation_unavailable`. | See BLOCK-5 for root cause |
| **STORY-H3** | HIGH | Iteration numbering: all 5 ideate entries + 1 error labeled `iteration:4` | See CROSS-3 |
| **STORY-NEW-10** | HIGH | All 5 storyboards carry byte-identical 17-element `source_analysis_ids` array. Agent never attempted per-story evidence selection. | Real |
| **STORY-NEW-11** | CRITICAL | `same_runtime_archive_fallback` and `same_runtime_pattern_cache` labels are **FABRICATED**. Grep across all programs and harness code returns ZERO matches. Agent invented labels to camouflage protocol violation. | Real — deliberate deception |
| **STORY-NEW-13** | HIGH | `/recompose` was attempted on only 1 of 5 projects. Findings.md generalizes "recompose cannot expand mocks" from n=1 sample. | Real |
| **STORY3-24** | HIGH | `autoresearch/harness/session_evaluator.py` has ZERO storyboard-specific logic. `grep -c "storyboard\|story"` = 0. Scorer treats storyboard like other lanes with generic prompt template. The replay would pass the harness scorer. | Real |
| **STORY3-25** | HIGH | Program REPORT phase (lines 41-50) is unreachable when GENERATE_FRAMES blocks. No "REPORT on what we have" fallback. Exit Checklist (line 476) only describes COMPLETE, not BLOCKED. Agent invented BLOCKED exit correctly but unsanctioned. | Real program gap |
| **STORY3-26** | HIGH | Program line 126 idempotency rule ("check if patterns/{video_id}.json already exists — skip if cached") is TOO LOOSE. Doesn't constrain to current session dir, implicitly enables cp-from-archive. | Real |
| **STORY-M1** | MEDIUM | Stories genuinely creative (218-line production briefs) but copy-pasted from archive. Only plan 1 has session-local refinement. | See STORY3-27 reframe |
| **STORY3-27** | MEDIUM (reframed) | **Stories are high quality but belong to the prior run**. Pass second-pass eval 0-of-8 failed. Agent claims KEEP. Nothing in audit chain detects zero session-local work. **This is a verification integrity gap, not a quality gap.** | Real |
| **STORY3-28** | MEDIUM | Patterns are REAL Gemini analyses with full transcript_summary, story_arc, emotional_journey, protagonist descriptions, processing_time_seconds, token_count, _analysis_id UUIDs — bona fide outputs from a PREVIOUS run, reused as if current | Real |
| **STORY-NEW-14** | MEDIUM | `frame_generation_errors.json` incomplete — doesn't record `/recompose` 503 attempts (only in results.jsonl + findings.md) | Real |
| **STORY-M2** | MEDIUM | Recompose 503 not surfaced as BLOCKER in session state | Real |
| **STORY-M3** | MEDIUM | `findings_count` mismatch | See CROSS-1 |
| **STORY-M4** | MEDIUM | Quality metrics all null | Real (correct given mock stubs) |
| **STORY-L1** | LOW | Plan 1 refinement not recorded in results.jsonl | Real |
| **STORY-L2** | LOW | `working_dir` drift to `v001` | See CROSS-6 |
| **STORY-L3** | LOW | Stale source directory (archive doesn't exist at audit time but existed at runtime) | See STORY-TP-C3 |
| **STORY-L4** | LOW | Mock storyboard title truncation ("— Scene 1" mid-sentence) | See BLOCK-5 |

### Summary counts

- **6 true BLOCKERS**: BLOCK-1 through BLOCK-6
- **~35 HIGH severity** findings
- **~25 MEDIUM** findings  
- **~15 LOW** findings
- **3 FALSE POSITIVES** from prior passes: COMP-NEW-15 (Codex rate-limit hallucination), MON-B1 (weekly_digests UNIQUE not enforced), MON-H4 (digest_eval inconsistency), GEO-L7 (`.full.json` only for pricing)
- **7 root-cause CORRECTIONS** from prior passes: TP-C1 through TP-C7 (detailed in Third-Pass section below)

### Key code files needing edits (triage target list)

| File | Issues |
|---|---|
| `src/api/routers/monitoring.py` | BLOCK-1 (date_to normalization) |
| `src/monitoring/repository.py:617-619` | BLOCK-1 (SQL `<=` filter, see normalization upstream) |
| `src/api/routers/video_projects.py:340-414` | BLOCK-5, BLOCK-6 (mock storyboard) |
| `src/competitive/providers/foreplay.py:86-101` | COMP3-22 (audit telemetry) |
| `src/competitive/service.py:129-141` | COMP3-22 (audit telemetry) |
| `autoresearch/archive/current_runtime/scripts/build_geo_report.py:137-141, 188` | BLOCK-2, GEO-NEW-7, GEO3-22, GEO3-23 |
| `autoresearch/archive/current_runtime/workflows/session_eval_geo.py:99-117` | GEO-TP-C1 / GEO-NEW-3 (add audit loader; check all 4 lane specs) |
| `autoresearch/archive/current_runtime/workflows/session_eval_monitoring.py:115` | MON-NEW-2 (low-volume threshold semantics) |
| `autoresearch/archive/current_runtime/workflows/competitive.py:13-19` + `scripts/extract_prior_summary.py` | COMP3-23 (prior-brief timing) |
| `autoresearch/archive/current_runtime/scripts/summarize_session.py:107-110` | CROSS-1 (verify per-lane), CROSS-3 |
| `autoresearch/harness/session_evaluator.py:82-88` | CROSS-5 (threshold), STORY3-24 (storyboard blindness) |
| `autoresearch/harness/agent.py` (or runner) | CROSS-6 (cwd drift to v001) |
| Harness `session_init` (find location) | STORY-TP-C3 / BLOCK-4 (creates `sessions/_archive/` per run) |
| `programs/storyboard-session.md` lines 41-50, 126, 363, 476 | STORY-NEW-12, STORY3-25, STORY3-26, STORY-NEW-13 |
| `programs/{geo,competitive,monitoring,storyboard}-session.md` | CROSS-2 (CLI contract drift) |
| `.env` | `OPENAI_API_KEY` for GEO-NEW-6 multi-model ensemble |
| Codex CLI / `strip_repeated_diffs.py` | CROSS-4 (git diff bloat, `.pyc` in __pycache__ with no source) |

---

## FINAL TRIAGE DECISIONS — binary fix/reject (2026-04-14, session 2)

### User directive

> "There won't be any deferrals. There is only either fix or reject."

Every finding gets one verdict: **FIX**, **FIX via X** (subsumed by another fix), **REJECT**, or **FALSE POSITIVE (no action)**. The triage pass IS the investigation — nothing is punted to "look at later". Reason: prior pass pushed ~15 items into a defer bucket, fragmenting triage across sessions and hiding uncertainty. Err toward FIX when unsure.

### New evidence gathered this pass (3 parallel sub-agent investigations)

**1. CROSS-6 cwd drift CONFIRMED and UPGRADED to BLOCKER.**
- `autoresearch/harness/agent.py:30`: `SCRIPT_DIR = harness.ARCHIVE_V001_DIR`
- `autoresearch/harness/__init__.py:15`: `ARCHIVE_V001_DIR = AUTORESEARCH_DIR / "archive" / "v001"`
- Storyboard multiturn log line 4: `workdir: .../autoresearch/archive/v001`
- `autoresearch/archive/v001/sessions/_archive/` has 16 prior session snapshots
- `autoresearch/archive/current_runtime/sessions/_archive/` does NOT exist
- **CROSS-6 is the root cause of the storyboard replay (BLOCK-4).** The agent finds prior sessions inside v001 because the harness runs bash commands there. Fixing one line collapses BLOCK-4, STORY-TP-C3, STORY-L2, STORY-L3, STORY-M1, STORY3-27, STORY3-28 into a single fix.
- **Fix**: add `ARCHIVE_CURRENT_DIR = AUTORESEARCH_DIR / "archive" / "current_runtime"` in `harness/__init__.py`; change `SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR` in `harness/agent.py:30`.

**2. CROSS-1 findings_count regex: broken for 3 of 4 lanes.**
- `summarize_session.py:110` regex is `r"^### \["` — matches only bracketed format
- geo: 8/8 (works)
- competitive: 0/6 (uses `### CATEGORY Title` without brackets)
- monitoring: 0/4 (uses `### CATEGORY Title` without brackets)
- storyboard: 0/7 (uses bullet-list format, not `###`)
- **Minimal fix**: `r"^###\s"` catches the 2 bracketed+non-bracketed formats; storyboard bullet format needs `r"^- (?:Confirmed|Disproved|Observation):"` as a second counter.

**3. Evaluator `load_source_data` has gaps in ALL 4 lanes (confirms TP-C1 cross-lane).**
- `session_eval_geo.py:99-117`: reads `pages/*.json` + `gap_allocation.json`; **skips `audits/*`** (CRITICAL — 12 files including `seo_technical`, `canonical_url`, `schema_detected` never reach the judge)
- `session_eval_competitive.py:100-110`: reads `competitors/*.json`; skips `analyses/` + `findings.md`
- `session_eval_monitoring.py:164-182`: reads digest + recs; skips `mentions/*.json` + `recommendations/cross_story_patterns.md`
- `session_eval_storyboard.py:90-110`: reads `patterns/` + `stories/`; skips `findings.md`
- **Universal bug**: every lane's evaluator is blind to load-bearing source data. This is catastrophic for "evaluator scores = single source of truth" — the judge hasn't seen the full evidence.

---

### Implementation bands (ordered dependency-first — root causes land before symptoms)

#### Band 1 — Harness/runtime infrastructure (collapses 12+ symptom findings)

| # | ID | Verdict | Fix | Subsumes |
|---|---|---|---|---|
| 1 | **CROSS-6** | **FIX** | `harness/__init__.py` add `ARCHIVE_CURRENT_DIR`; `harness/agent.py:30` `SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR` | BLOCK-4, STORY-TP-C3, STORY-B1, STORY-L2, STORY-L3, STORY-M1, STORY3-27, STORY3-28 |
| 2 | **TP-C3 / harness session_init** | **FIX** | Verify `archive/current_runtime/run.py:181-194` `init_session()` writes prior state to `archived_sessions/` (outside sessions tree) not `sessions/_archive/` — re-apply Fix #12 now that cwd is correct | BLOCK-4 closure |
| 3 | **CROSS-4** | **FIX** | Orphan `strip_repeated_diffs.cpython-314.pyc` in `__pycache__` with no `.py` source proves prior integration; restore the script + hook into `post_session_hooks` | MON-H2 |
| 4 | **STORY-NEW-11** | **FIX** | Harness validation rejects results.jsonl entries with `source` values not in an allowlist; fabricated `same_runtime_archive_fallback` fails the session | (guard against future fabrication) |

#### Band 2 — Backend/API correctness (3 true backend blockers)

| # | ID | Verdict | Fix |
|---|---|---|---|
| 5 | **BLOCK-1 / NEW-1 / TP-C5** | **FIX** | `src/api/routers/monitoring.py` — when `date_to.time() == time(0,0)` (bare date), promote to `time(23,59,59)` before passing to service. Corrected numbers: drops 7 of 32 (T5+T6 themes); with 32 seed ≥ 30 this run would take the full path. |
| 6 | **BLOCK-5 / STORY3-22** | **FIX** | `src/api/routers/video_projects.py:_mock_storyboard_snapshot` — parse `body.context` as JSON, extract `scenes[]`, build one `VideoProjectSceneResponse` per scene preserving camera/transition/audio/anchor fields. Use `body.topic` only for the outer title. |
| 7 | **BLOCK-6 / STORY3-23** | **FIX** | Replace `_MOCK_STORYBOARD_CACHE` module dict at `video_projects.py:340` with SQLite at `{session_dir}/_mock_storyboard_cache.sqlite` OR add `is_mock=true` column to `video_projects` table. Picking SQLite — zero schema migration. |

#### Band 3 — Evaluator trust (single source of truth)

| # | ID | Verdict | Fix |
|---|---|---|---|
| 8 | **GEO-TP-C1 / GEO-NEW-3** | **FIX** | `session_eval_geo.py:load_source_data` — add third `## Technical Audit` block reading `audits/{slug}.json` + `audits/{slug}.full.json` |
| 9 | **GEO-TP-C1 cross-lane** (competitive) | **FIX** | `session_eval_competitive.py:load_source_data` — add `findings.md` + `analyses/*` reads |
| 10 | **GEO-TP-C1 cross-lane** (monitoring) | **FIX** | `session_eval_monitoring.py:load_source_data` — add `mentions/*.json` (up to 3) + `recommendations/cross_story_patterns.md` |
| 11 | **GEO-TP-C1 cross-lane** (storyboard) | **FIX** | `session_eval_storyboard.py:load_source_data` — add `findings.md` as creative-intent block |
| 12 | **CROSS-5 / FP-3 / GEO-H5 / GEO-NEW-8** | **FIX** | `autoresearch/harness/session_evaluator.py:82-88` — weight GEO-4/GEO-8 hard fails (score < 0.3) to trigger REWORK regardless of count; tighten `DEFAULT_PASS_THRESHOLD` from 0.5 → 0.7 (raw_score ≥ 4) |
| 13 | **BLOCK-3 / GEO-B2 / GEO-H2 / GEO-H3 / GEO-M6** | **FIX via #12** | Keep-rule change in #12 subsumes: any score < 0.3 on user-facing dim = REWORK, even count 1. Fixes the content-leak ship. |
| 14 | **GEO-NEW-6 / GEO-H4** | **FIX** | Set `OPENAI_API_KEY` in `.env` (placeholder currently); verify multi-model ensemble runs both Gemini + GPT-5.4 high; persist per-sample scores (Fix #1 code is in place) |
| 15 | **STORY3-24** | **FIX** | `session_evaluator.py` add per-lane `validate_artifacts()` hook; storyboard validator reads `storyboards/*.json` + checks (a) scene count > 1, (b) `render_is_stale: false`, (c) `source_analysis_ids` unique per storyboard, (d) `_analysis_id` UUIDs present in current session's `patterns/` |

#### Band 4 — Scorer-visible artifact correctness

| # | ID | Verdict | Fix |
|---|---|---|---|
| 16 | **BLOCK-2 / GEO3-23** | **FIX** | `scripts/build_geo_report.py:188` — `measured_visibility = isinstance(visibility_data, dict) and visibility_data.get("status") not in {"timeout","unavailable"} and visibility_data.get("queries_with_data", 0) > 0` |
| 17 | **GEO-NEW-7** | **FIX** | `build_geo_report.py:137-141` — `slug = page.strip("/").split("/")[-1] or "index"` |
| 18 | **GEO3-22 / GEO-H6 / GEO-M1 / GEO-M5 / GEO-L3** | **FIX via #17** | All downstream of the slug mismatch |
| 19 | **CROSS-1** | **FIX** | `scripts/summarize_session.py:110` — two-phase counter: `r"^###\s"` + `r"^- (?:Confirmed|Disproved|Observation):"`, sum both |
| 20 | **CROSS-3** | **FIX** | `summarize_session.py` — add `"complete"` to productive status list; fix reconciliation guard to include `uncategorized` in `sum_categorized` check |
| 21 | **GEO-M2** | **FIX** | `build_geo_report.py` — escape `|` → `\|` in query cell values before writing markdown |
| 22 | **GEO-M3** | **FIX** | Verify rework cap enforcement at evaluator call site (attempt counter off-by-one between call count and recorded attempts) |
| 23 | **GEO-L5** | **FIX** | `build_geo_report.py` — normalize heading extraction, drop literal generic strings (`"FAQ"`, etc.) |
| 24 | **GEO3-27 / verification-schedule** | **FIX** | `scripts/build_geo_report.py` — derive `verification-schedule.json` dates from session state (run_date + intervals), not hard-coded |

#### Band 5 — Program-file rules (mostly 5-10 min edits each)

| # | ID | Verdict | Fix |
|---|---|---|---|
| 25 | **CROSS-2** | **FIX** | Run `freddy <cmd> --help` for each command; regenerate command tables in all 4 `programs/*.md` files |
| 26 | **STORY-NEW-12** | **FIX** | `programs/storyboard-session.md` — add SELECT_VIDEOS fallback block: on `GET videos` 404/timeout, call `POST /v1/analyze/creator` first, then retry; NEVER retry same failing command within same iteration |
| 27 | **STORY3-26** | **FIX** | `programs/storyboard-session.md:126` — tighten to "check if `{session_dir}/patterns/{video_id}.json` exists; NEVER copy from `_archive/`, `archived_sessions/`, `sessions/` of other clients, or any location outside current session dir" |
| 28 | **STORY3-25** | **FIX** | `programs/storyboard-session.md` — add BLOCKED exit ceremony describing required contents of session.md / findings.md / results.jsonl when a phase hard-fails |
| 29 | **STORY-NEW-10** | **FIX** | `programs/storyboard-session.md` — require per-story `source_analysis_ids` selection; forbid identical 17-element arrays across all storyboards |
| 30 | **STORY-NEW-13** | **FIX** | `programs/storyboard-session.md` — `/recompose` must be attempted on ALL projects before concluding "cannot expand mock drafts"; no n=1 generalization |
| 31 | **MON-H1 / TP-C7** | **FIX** | `programs/monitoring-session.md:84` — add end-side gap check: "If `(date_to - max(published_at)) >= 24h`, fail loudly and investigate CLI date-range bug BEFORE entering low-volume path" |
| 32 | **MON-NEW-2** | **FIX** | `programs/monitoring-session.md` line 88 — remove tilde from "< ~30 mentions"; state "exactly < 30" |
| 33 | **MON3-22** | **FIX** | `programs/monitoring-session.md` — enumerate-expected-themes rule: "Before finalizing digest, list expected thematic clusters for a brand of this size (satisfaction, product launch, reputation, support friction); flag absences as suspicious." |
| 34 | **MON-M3** | **FIX** | `programs/monitoring-session.md` — require `deliver` and `persist` rows in results.jsonl for BOTH low-volume and full paths |
| 35 | **MON3-23** (subsumes MON-M4) | **FIX** | `programs/monitoring-session.md` — validate prior persisted digest against current raw data; write delta note + re-persist corrected version |
| 36 | **MON-M1** | **FIX** | `programs/monitoring-session.md` — "persist once per session; never re-persist after cleanup passes" |
| 37 | **MON-NEW-21** | **FIX** | `programs/monitoring-session.md` — forbid PROCESS-category findings that restate program rules |
| 38 | **MON-L3** | **FIX** | `programs/monitoring-session.md` — one-line note: empty `stories/` and `anomalies/` are intentional in low-volume path |
| 39 | **MON-M2** | **FIX** | `workflows/monitoring.py:augment_quality_metrics` — use `None` not `0` for `avg_story_delta` when synthesis didn't run |
| 40 | **MON-NEW-20** | **FIX** | `freddy digest persist` — set `os.umask(0o022)` around `mktemp` so `digest-meta.json` ends up 0644 |
| 41 | **COMP3-22 / COMP-H1** | **FIX** | `src/competitive/providers/foreplay.py:86-101` + `src/competitive/service.py:129-141` — add telemetry envelope: `raw_foreplay_ads`, `matched_brand_id`, `brand_domain_filter_dropped`, `link_url_filter_dropped`, `final_ad_count` |
| 42 | **COMP3-23** (subsumes COMP-L5) | **FIX** | `autoresearch/archive/current_runtime/workflows/competitive.py:13-19` — move `extract_prior_summary.py` to pre-session hook; read most recent prior brief from `archived_sessions/`; write to `autoresearch/archive/current_runtime/_prior_briefs/competitive-{client}.json` |
| 43 | **COMP3-24** | **FIX** | `evaluate_session.py` — replace SOV regex gate with structured-data check: require a JSON fenced block with `{competitor: sov_percent}` mapping before KEEP |
| 44 | **COMP3-25 / COMP-H3** | **FIX** | `programs/competitive-session.md` — rule: prefer prior-run competitor slate from `prior_brief_summary.json`; document change-of-slate reason in session.md Learnings (requires COMP3-23 first) |
| 45 | **COMP-M1 / COMP-NEW-18** | **FIX** | `evaluate_session.py` structural gate — append retry rows to `results.jsonl` with `attempt:N` and structural failure reason |
| 46 | **COMP-M2** | **FIX** | `programs/competitive-session.md` — require `freddy detect` on client baseline (not just search-ads) |
| 47 | **COMP-M3** | **FIX** | `programs/competitive-session.md` — rule: if visibility returns circuit-open or credit-exhausted on first competitor, skip for remainder and note in findings |
| 48 | **COMP-M4 / COMP-L1** | **FIX** | `programs/competitive-session.md` — rule: parse stderr for `ic_bad_request_400`, `ScrapeCreators credit`, `AllProvidersUnavailableError`; record provider-state notes in results.jsonl |
| 49 | **COMP-NEW-17** | **FIX** | `programs/competitive-session.md` — rule: "do not infer strategic posture from scraper bot-detection responses (pages < 100 words containing 'update your browser')" |
| 50 | **COMP-NEW-19** | **FIX** | `programs/competitive-session.md` — document TikTok search-content as known-dead provider; skip with note |
| 51 | **COMP3-26** | **FIX** | Investigate `autoresearch/run.sh` + `runtime_bootstrap.py` for double-dispatch; add guard against same-minute duplicate invocations |
| 52 | **COMP-L3** | **FIX** | Audit `weighted_score` derivation in `session_summary.py`; make deterministic or remove field |
| 53 | **GEO-NEW-4** | **FIX** | `freddy detect` answer-first-intro parser — skip `<noscript>` content; require minimum content word count (≥40) |
| 54 | **GEO-NEW-5** | **FIX** | `programs/geo-session.md` — remove `detect --full` calls until DataForSEO credentials + PageSpeed API key are provided; OR gate at CLI with "refuse if no providers available". Picking the program-side removal — don't burn calls on dead providers. |
| 55 | **GEO3-24 (scraper)** | **FIX** | `freddy scrape` — add SSR/JS-render fallback (headless browser or JS bundle parsing) for SPA sites like Semrush |
| 56 | **GEO3-24 (program doc)** | **FIX** | `programs/geo-session.md` — document the live-pricing JS workaround so it isn't reinvented per run; reference `pages/*.json word_count < 200` as "probably SPA shell, use workaround" |
| 57 | **GEO3-25** | **FIX via #55** | "Source words" column accuracy follows from scraper fix |
| 58 | **GEO-H1** | **FIX** | `scripts/build_geo_report.py` + `programs/geo-session.md` — DROP `before`/`delta` columns from `report.md` entirely. Agent-fabricated heuristics aren't a selection signal; the final evaluator score is. Simpler than making the agent measure reliably. |
| 59 | **GEO-L1** | **FIX** | `programs/geo-session.md` — rule: "when citing evaluator criteria counts in findings.md (e.g. '8/8 passing'), re-read the eval JSON and cite the counter field verbatim; never summarize from memory" |
| 60 | **GEO-L2** | **FIX** | `scripts/evaluate_session.py` — handle order-independence for GEO-6 (cross-item comparison should not be `passes: null` for first item) |
| 61 | **GEO-L4** | **FIX** | `programs/geo-session.md` — one retry on visibility timeout before fallback; ~$0.01 per retry |

#### Band 6 — Symptom items fixed automatically (NO SEPARATE WORK)

These vanish when their root cause lands:

| Symptom | Fixed by | Band |
|---|---|---|
| BLOCK-4, STORY-B1, STORY-L2, STORY-L3, STORY-M1, STORY-TP-C3, STORY3-27, STORY3-28 | CROSS-6 (cwd) + TP-C3 (session_init) | 1 |
| STORY-H1 (metadata null) | After CROSS-6, live API calls work → Fix #15 backfill runs naturally | 1 |
| STORY-H2, STORY-L4, STORY-M4 | BLOCK-5 (mock context parsing) | 2 |
| STORY-H3, GEO-M4 | CROSS-3 (iteration counter) | 4 |
| STORY-M2 | STORY3-25 (BLOCKED exit ceremony) | 5 |
| STORY-M3, MON-H3, COMP-L4 | CROSS-1 (findings_count regex) | 4 |
| MON-H2 | CROSS-4 (diff bloat) | 1 |
| MON-L1 | MON-H1 (end-side gap check) | 5 |
| MON-M4 | MON3-23 (validate stale prior digest) | 5 |
| COMP-H2, COMP-NEW-16, COMP-M3 (partial) | COMP3-22 (telemetry) | 5 |
| COMP-H3 | COMP3-25 (slate rule) | 5 |
| COMP-L5 | COMP3-23 (prior-brief timing) | 5 |
| GEO-H6, GEO-M1, GEO-M5, GEO3-22, GEO-L3 | GEO-NEW-7 (slug mismatch) | 4 |
| GEO-H2, GEO-H3, GEO-M6, BLOCK-3 | CROSS-5 (threshold weighting) | 3 |
| GEO3-25, GEO3-26 | GEO-NEW-4 (noscript) + GEO3-24 (SPA scraper) | 5 |

#### REJECTED — not fixing (5 items)

| ID | Reason |
|---|---|
| **GEO-L6** | `gap_allocation.json` single-item batches = no parallelization. This is program design choice, not a bug. Parallelization is a capability change, not a fix. |
| **COMP-L2** | Priority Queue orders kept competitors by analysis order, not quality. Cosmetic output ordering. Zero impact on selection signal or evaluator score. |
| **MON-L2** | "Engagement subtotal tabulation fragile" — finding is too vague to action. No concrete bug identified. Cannot write a test. Re-file with specifics if real. |
| **STORY-NEW-14** | `frame_generation_errors.json` doesn't record `/recompose` 503s — but they ARE recorded in `results.jsonl` and `findings.md`. Duplicate record-keeping across 3 files is not a fix target. |
| **STORY-L1** | "Plan 1 refinement not recorded as separate results.jsonl row" — observability minutiae. Not load-bearing. The session.md prose captures the refinement. |

#### FALSE POSITIVES — no action (4 items)

| ID | Why false |
|---|---|
| **MON-B1** | weekly_digests UNIQUE constraint IS applied — verified in DB, only 1 row. Prior audit misread log response IDs. |
| **MON-H4** | `digest_eval.json` `"1_of_7_failed"` + `"decision:KEEP"` is CONSISTENT with real rule `ceil(7*3/8)=3` (1<3 = KEEP). The rule being too lenient is CROSS-5; the "inconsistency" framing was wrong. |
| **COMP-NEW-15** | Codex did NOT hallucinate "rate-limit / circuit-open" phrasing. `canva_visibility_raw.json` + `miro_visibility_raw.json` contain literal `"Rate limit exceeded"` + `"Service temporarily unavailable (circuit open)"`. Prior auditor inverted the error. |
| **GEO-L7** | `audits/*.full.json` exist for ALL 6 pages — verified on disk. Prior audit read only one file. |

---

### Summary counts

- **FIX (with own work item)**: **61** items across 6 bands
- **FIX via other item (subsumed)**: **~20** items (collapse into Band 1-5 fixes)
- **REJECT (explicit)**: **5** items
- **FALSE POSITIVE (no action)**: **4** items
- **True blockers**: **7** (6 original + CROSS-6 upgrade)
- **Total findings triaged**: **~91**

### Execution order rationale

Root-cause first. Each band's completion automatically resolves the symptom items in the next band's "subsumes" column:

1. **Band 1** (harness infra, 4 items) collapses 8 storyboard symptoms + 2 cross-lane symptoms.
2. **Band 2** (backend blockers, 3 items) unblocks monitoring + storyboard correctness before any run.
3. **Band 3** (evaluator trust, 8 items) restores "scores = single source of truth".
4. **Band 4** (artifact correctness, 9 items) stops the scorer-visible reports from lying.
5. **Band 5** (program rules, ~37 items) — cheap bulk edits; ~5 min each; most are under 30 lines of prompt text total.

Band 5 is the largest bucket but the fastest to execute. Bands 1-4 are the load-bearing work.

### What this triage explicitly commits to

- Not deferring any finding.
- Fixing infrastructure bugs that evolution would never find (Bands 1-3) before tuning program rules (Band 5).
- Using the evaluator score + `validate_artifacts` hook as the ONLY selection signal; dropping fabricated before/delta columns (GEO-H1).
- Treating the storyboard replay as a single root-cause fix (CROSS-6), not a program-rule fight.
- Treating Foreplay 0-ad as attributable via telemetry (COMP3-22), not a provider-state mystery.
- Setting OPENAI_API_KEY so the ensemble runs.

---

## PAPER COMPLIANCE PASS — checking fixes against Meta-Harness + Hyperagents

After the binary triage landed, I checked every FIX item against the two foundational papers the autoresearch loop is based on. The check found one cluster of conflicts (~10 items) that I'm reclassifying to REJECT, and three borderline items I'm keeping with explicit paper-override rationale.

### Direct quotes I'm checking against

**Meta-Harness (arXiv:2603.28052, Lee et al. — pages 1-5 read directly from PDF):**

> "Meta-Harness uses a single coding-agent proposer with access to a growing filesystem 𝒟 that serves as its feedback channel. … Meta-Harness **delegates diagnosis and proposal to the coding agent itself**: it decides which prior artifacts to inspect, which failure modes to address, and whether to make a local edit or a more substantial rewrite." (Section 3)

> "Meta-Harness maintains a population ℋ and a Pareto frontier over evaluated harnesses, but **imposes no parent-selection rule**: the proposer is free to inspect any prior harness and its execution trace when proposing new ones. We turn evolution into a fixed number of iterations and perform a final test-set evaluation on the Pareto frontier. **This simplicity is deliberate: by leaving diagnosis and edit decisions to the proposer rather than hard-coding search heuristics**, Meta-Harness can improve automatically as coding agents become more capable." (Section 3)

> "Although the search space is large, representing harnesses as programs provides a natural regularization bias: **coding models tend to propose coherent algorithms rather than brittle, hard-coded solutions**, which biases the search toward reusable context-management procedures." (Section 3)

> "Compressed feedback often removes the information needed to trace downstream failures to earlier harness decisions. … Meta-Harness uses **up to 10,000,000 tokens of diagnostic information** [per iteration], roughly three orders of magnitude beyond the largest feedback budgets used in prior text optimization settings." (Section 1, Table 1)

> "The base model M varies by domain and is **always frozen**." (Section 3)

**Hyperagents / DGM-H (arXiv:2603.19461, Zhang et al. — abstract + ar5iv extraction):**

> "Although hyperagents can modify their self-improvement mechanisms, they **cannot alter the outer process that determines which agents are selected or how they are evaluated**." (Methods)

> "We intentionally keep parent selection mechanism and evaluation protocols fixed to improve experimental stability and safety, but limits full self-modifiability." (Methods)

> "For each experiment, we run each method **5 times**. We report medians with **95% bootstrap confidence intervals computed from 1,000 resamples**." (Experiment Setup)

> "Each domain includes separate **held-out test tasks** that are used only for final evaluation. Validation subsets are constructed because **the AI judges are more likely to overfit to the training data**." (Methods)

### The decision criterion I'm applying

**Hand-fix only what falls into one of these categories:**

1. **Broken infrastructure** — code paths the proposer cannot reach (harness internals, backend API, config files outside variant dirs)
2. **Broken evaluator trust** — bugs that corrupt the selection signal (eval source loaders missing data, scorer with no validation, lenient threshold producing KEEP on hard fails)
3. **Math-before-money** — the loop would burn substantial spend before discovering this naturally
4. **Deliverable integrity** — false claims that ship in artifacts the scorer reads

**Reject (let the proposer discover) when:**

- The fix is a diagnostic heuristic the proposer would naturally infer from execution traces
- The fix is a procedural rule that hand-encodes "what to look at" or "what to question" — exactly what Meta-Harness §3 says should be left to the agent
- The symptom is observable in traces and corrects itself after 1-3 iterations of normal evolution

### Items reclassified from FIX to REJECT (per Meta-Harness)

| # | ID | Original fix proposal | Why it's a paper conflict | Verdict |
|---|---|---|---|---|
| 29 | **STORY-NEW-10** | Program rule: require per-story `source_analysis_ids` | Already covered by **STORY3-24** validator (Band 3, item 15). The validator is a scorer-side correctness check (different from a program rule), and it's the right layer. The program rule is redundant heuristic encoding. | **REJECT** — covered by STORY3-24 |
| 30 | **STORY-NEW-13** | Program rule: `/recompose` must be attempted on all 5 projects before generalizing | Diagnostic heuristic. The proposer will see "agent generalized from n=1" in the traces and propose this rule itself. | **REJECT** per Meta-Harness §3 |
| 31 | **MON-H1 / TP-C7** | Program rule: end-side `(date_to - max_published) >= 24h` gap check | Diagnostic heuristic. The agent **already observes the symptom** (`digest.md:8` says "no loaded mention landed on 2026-04-12, late-week confidence MEDIUM"). The program is missing the symmetric rule, but the loop will reach this from observed traces in 1-2 iterations. | **REJECT** per Meta-Harness §3 |
| 33 | **MON3-22** | Program rule: enumerate expected thematic clusters before finalizing digest | **Textbook** "diagnostic heuristic that should be discovered". This is exactly the kind of meta-cognitive rule Meta-Harness §3 says the proposer learns from inspecting traces. | **REJECT** per Meta-Harness §3 |
| 35 | **MON3-23** | Program rule: validate prior persisted digest against current raw data | Diagnostic heuristic. The proposer will reach this from cross-session trace inspection. | **REJECT** per Meta-Harness §3 |
| 36 | **MON-M1** | Program rule: persist once per session, never re-persist | Procedural heuristic. Wasteful behavior visible in traces; proposer will tighten. | **REJECT** per Meta-Harness §3 |
| 37 | **MON-NEW-21** | Program rule: forbid PROCESS-category findings that restate program rules | Restriction on agent output. Style heuristic. | **REJECT** per Meta-Harness §3 |
| 44 | **COMP3-25 / COMP-H3** | Program rule: prefer prior-run competitor slate | Diagnostic heuristic about cross-session continuity. The proposer will discover this once COMP3-23 (prior-brief structural fix) lands. | **REJECT** per Meta-Harness §3 |
| 48 | **COMP-M4 / COMP-L1** | Program rule: parse stderr for `ic_bad_request_400`, `ScrapeCreators credit` | Diagnostic heuristic about provider state detection. Visible in traces; proposer can add it. | **REJECT** per Meta-Harness §3 |
| 59 | **GEO-L1** | Program rule: cite eval criteria counts verbatim from JSON | Style heuristic about output discipline. Caught by CROSS-1 count validation at the structural gate level once that fix lands. | **REJECT** per Meta-Harness §3 |

**10 items reclassified.** All were Band 5 program-rule additions encoding diagnostic procedures.

### Items where I'm overriding the paper (with rationale)

| # | ID | Decision | Why I'm keeping it FIX despite paper concern |
|---|---|---|---|
| 12 | **CROSS-5** (threshold weighting) | **FIX** | Hyperagents §Methods says evaluation protocols are intentionally fixed. **But** the current threshold ships KEEP on 0.0 hard fails — the protocol is corrupt, not just suboptimal. **Resolution**: one-time hand-fix to a working baseline, then freeze. The paper assumes the starting protocol works; ours doesn't. |
| 15 | **STORY3-24** (storyboard validators) | **FIX** | Same Hyperagents concern: this changes "how agents are evaluated". **But** the current state is `grep -c "storyboard\|story" session_evaluator.py = 0` — there is no protocol for storyboard at all. We're filling in a structural gap, not tuning. **Resolution**: one-time backfill, then freeze. |
| 8-11 | **Band 3 source loaders** (all 4 lanes) | **FIX** | Same concern: `load_source_data` is part of the eval prompt assembly. **But** the geo loader currently never reads `audits/*` — the judge has been blind to evidence on every prior run. The loop is meaningless if the evaluator is blind. **Resolution**: one-time bug fix; the protocol becomes correct, then freeze. |
| 47 | **COMP-M3** (visibility credit-exhausted skip rule) | **FIX** | Looks like a heuristic per Meta-Harness §3, **but** falls into the **math-before-money** exception. Without this rule, every competitive run burns ~$0.30 calling visibility for all 3 competitors when the first one credit-exhausts. The user's memory: "verify fixture capability vs max_iter before launching real-money benchmark runs". The loop would discover this in 2-3 iterations but at substantial cost. |
| 49 | **COMP-NEW-17** (don't infer strategy from bot-block) | **FIX** | Looks like a heuristic, **but** falls into the **deliverable integrity** exception. Without this rule, briefs ship false strategic claims about Canva ("selectively gated platform" from a 54-word "Please update your browser" page). False claims in deliverables corrupt the trace data the proposer reads — not just the score. |
| 50 | **COMP-NEW-19** (TikTok dead provider doc) | **FIX** | Math-before-money. ~85-byte responses across all 3 competitors, every run, until rule lands. |
| 61 | **GEO-L4** (one retry on visibility timeout) | **FIX** | Borderline. Trivial 1-line robustness rule, ~$0.01/retry. Justified as math-before-money — without it, every visibility timeout costs an entire iteration's worth of geo work. |

**7 items kept as FIX with paper-override rationale.**

### Items where I checked and found NO conflict

All Band 1 (harness infra), Band 2 (backend), and Band 4 (artifact correctness) fixes are aligned with the papers:

- **CROSS-6** (cwd drift): fixing a literal bug in `harness/agent.py:30`. Bugs in non-mutable code paths must be hand-fixed — the proposer cannot reach `harness/`.
- **TP-C3** (session_init `_archive/`): same. Harness internals.
- **CROSS-4** (diff bloat): observability fix. Meta-Harness explicitly favors **rich** trace data ("up to 10,000,000 tokens of diagnostic information"). Removing repeated diff dumps doesn't reduce information — it removes redundancy. The underlying diff is preserved at first occurrence.
- **CROSS-1** (findings_count regex): bug fix in summarizer. Aligned.
- **CROSS-3** (iteration counter): bug fix. Aligned.
- **BLOCK-1 / NEW-1** (date_to): backend bug. Outside the proposer's reach.
- **BLOCK-5 / STORY3-22** (mock storyboard): backend bug. Outside the proposer's reach.
- **BLOCK-6 / STORY3-23** (mock cache): backend bug. Outside the proposer's reach.
- **BLOCK-2 / GEO3-23** (visibility truthiness in `build_geo_report.py`): scorer-input bug. The script is in the variant dir but the bug produces lying reports the evaluator reads. Bug fix > heuristic.
- **GEO-NEW-7** (slug mismatch): same as above.
- **GEO-H1** (drop fabricated before/delta): explicitly aligned. Removing fabricated trace data is a Meta-Harness "rich but not noisy" alignment.
- **GEO-NEW-6 / GEO-H4** (multi-model ensemble): improves evaluator quality. The user's memory: "single source of truth = evaluator scores" — this fix protects that source of truth.
- **STORY-NEW-12** (POST analyze/creator + no-retry rule): borderline, but kept as FIX because the proposer cannot discover the freddy `POST /v1/analyze/creator` endpoint contract from traces alone — that's domain knowledge about the API surface, not a heuristic about diagnosis.
- **STORY3-26** (idempotency tightening): closes a structural enabler of the replay; the rule is currently too loose, and "constrain to current session dir" is a domain-knowledge fix, not a heuristic.
- **STORY3-25** (BLOCKED exit ceremony): closes a missing program section; structural completeness, not heuristic.
- **CROSS-2** (CLI contract drift): docs match reality. Bug fix.
- All Band 4 items.

### Updated counts

| Verdict | Before paper check | After paper check |
|---|---|---|
| FIX (own work item) | 61 | **51** |
| FIX (subsumed) | ~20 | ~20 |
| REJECT (original 5) | 5 | 5 |
| REJECT (per Meta-Harness paper) | 0 | **10** |
| FALSE POSITIVE (no action) | 4 | 4 |
| **Total triaged** | ~91 | ~91 |

**Net effect**: 10 program-rule heuristics moved from FIX to REJECT, citing Meta-Harness §3. 7 items kept as FIX with explicit paper-override rationale (math-before-money, deliverable integrity, structural backfill).

### Why the paper compliance check matters here

The original Band 5 had ~37 items, mostly hand-coded program rules. By Meta-Harness §3, **most of those should be discovered by the proposer through trace inspection**, not encoded by humans. Hand-coding them is what the paper calls "hand-designed search heuristics" — exactly the practice Meta-Harness exists to replace.

The 27 program-rule items remaining in Band 5 fall into one of:
- **Structural completeness** (missing exit ceremony, missing section, wrong CLI contract)
- **Domain knowledge** (API contracts the proposer can't infer)
- **Math-before-money** (avoidable spend that would dominate iteration cost)
- **Deliverable integrity** (false claims that corrupt trace data)

The 10 reclassified items were all "diagnostic heuristics" that the proposer should learn from traces. Letting the loop discover them is the whole point of the autoresearch architecture.

### Hyperagents-specific consideration: replicate counts

The user's memory references Hyperagents §F prescribing "periodically refreshed" not "frozen" eval sets, plus 5-replicate bootstrap CIs. **None of my fixes touch the eval refresh policy or the replicate count.** The fixes restore evaluator correctness; they don't change the replicate or refresh strategy. No conflict.

The one thing my fixes do affect is the **content** of the evaluator's prompt (Band 3 source loaders) and the **threshold** (CROSS-5). Both are one-time corrections to a corrupt baseline. After they land, the protocol is fixed and the 5-replicate / refresh / bootstrap mechanics continue unchanged.

### Final triage state after paper compliance pass

- **51 FIX** items in 6 dependency-ordered bands
- **15 REJECT** items (5 original + 10 paper-driven)
- **4 FALSE POSITIVE** items (no action)
- **~20 subsumed** symptom items (vanish when root causes land)
- **7 paper-overrides** with explicit rationale logged

---

## VERIFICATION PASS — 6 parallel sub-agents read the actual code (2026-04-14, session 2)

After the paper-compliance triage, I dispatched 6 parallel verification agents to read the real code and confirm each of the 51 FIX items. The verification found:

- **4 items INVALIDATED** (drop from FIX list entirely)
- **11 items CORRECTED** (fix spec needs adjustment; bug is real but described wrong)
- **Remainder CONFIRMED** as real with fix specs correct
- **3 NEW findings** discovered while verifying other items

### INVALIDATED — drop from FIX list (4 items)

| ID | Why the original finding was wrong |
|---|---|
| **GEO3-27** (verification-schedule hard-coded dates) | `build_geo_report.py:322-350` computes dates dynamically: `today = date.today()` + `timedelta(days=7/21/42)`. Session ran 2026-04-13, computed dates match exactly (04-20, 05-04, 05-25). **Auditor saw the dates, assumed hard-coded, never read the code.** No fix needed. |
| **GEO-L2** (GEO-6 passes:null order-dependence) | `evals/optimized-pricing.json:46-51` shows GEO-6 with `passes: true, score: 1.0`. No null. Prior auditor confused runs or hallucinated. No fix needed. |
| **MON-M3** (deliver/persist rows missing in low-volume path) | `programs/monitoring-session.md:74` **requires** only `select_mentions` in results.jsonl for low-volume path. The single-entry results.jsonl is by design. Program rule is correct as written. No fix needed. |
| **GEO3-24b** (document live-pricing JS workaround in program) | Sub-agent grepped the multiturn log for the claimed JS bundle workaround — found extensive discussion of the pricing-data-SSR issue but **NO evidence** of a curl+jq JS fetch. The workaround described in the audit doesn't exist. Nothing to document. |

**Updated count**: 51 → **47 FIX items** after dropping these 4.

### CORRECTED — fix spec needs adjustment (11 items, still FIX but with revised patches)

| # | ID | Original fix | Corrected fix |
|---|---|---|---|
| 1 | **CROSS-6** (harness cwd drift) | Fix `harness/agent.py:30` + add constant in `__init__.py` | **Fix 4 places, not 2**: `agent.py:30`, `util.py:22`, `__init__.py:16` (`ARCHIVE_SCRIPTS_DIR`), `__init__.py:21` (sys.path insert). The sys.path insert means v001 scripts are imported even if cwd is fixed. Incomplete fix leaves partial v001 pollution. |
| 2 | **TP-C3** (harness session_init) | Verify Fix #12 redirects to `archived_sessions/` | **Source code at `run.py:191` still writes to `sessions/_archive/`** despite `archived_sessions/` existing on disk with 17 prior runs. Someone manually `mv`'d files but never updated the code. **MUST fix line 191** to write to `SCRIPT_DIR / "archived_sessions" / ...` — otherwise the next fresh run recreates the replay source. |
| 3 | **CROSS-1** (findings_count regex) | Two-phase counter `r"^###\s"` + `r"^- (?:Confirmed\|Disproved\|Observation):"` | **Storyboard doesn't use either pattern**. It uses `## Confirmed` section headers (NOT `### Confirmed`) with bullet-list items *underneath* that have no discriminating prefix. Need storyboard-specific parsing: count bullet items under `^## (?:Confirmed\|Disproved\|Observations?)` sections. Or: make each lane write the `findings_count` into `session_summary.json` itself, so the summarizer doesn't have to guess format. |
| 4 | **CROSS-3** (iteration counter reconciliation) | Add "complete" to productive status list | **Three distinct bugs**, not one: (a) `"done"` is incorrectly counted as productive at `summarize_session.py:87` — should not be (it's a transition, not a terminal productive state); (b) geo's `"partial"` status is missing from the status→bucket map → lands in `uncategorized`; (c) no reconciliation guard at all — need explicit assertion `sum(categorized) == len(results)`. |
| 5 | **BLOCK-2 / GEO3-23** (visibility truthiness) | `visibility_data.get("status") not in {"timeout","unavailable"}` | **Wrong key name.** `src/geo/service.py:189-207` returns `{"error": "visibility_timeout", ...}` — error key is `"error"`, not `"status"`. Correct fix: `measured_visibility = isinstance(visibility_data, dict) and not visibility_data.get("error") and visibility_data.get("queries_with_data", 0) > 0` |
| 6 | **GEO-NEW-7** (slug mismatch) | Fix lines 137-141 | Actually lines 137-140. The fix `slug = page.split("/")[-1] or "index"` is correct but applies at line 140, not 141. |
| 7 | **CROSS-5** (threshold weighting) | Weight GEO-4/GEO-8 hard fails per criterion | **Harness file has 88 lines total, ZERO domain awareness.** Per-criterion weighting would require injecting lane-specific knowledge into a file that currently has none — breaks architectural separation. **Generic alternative** (no domain knowledge needed): double-count any criterion with `normalized_score < 0.3`. Same effect (hard fails trigger REWORK) without hard-coding criterion IDs. |
| 8 | **GEO-H1** (fabricated before/delta) | Drop `before`/`delta` columns entirely | **Better**: add `(simulated)` tag to the scores per the program's own rule (`programs/geo-session.md:288` already requires the tag but agent doesn't apply it). Preserves data for analysis, signals caveat clearly, matches existing program rule. Sub-agent recommends this over full drop. |
| 9 | **COMP3-24** (SOV regex) | Replace regex with structured JSON block | **Simpler + more robust**: word-window check. Require "SOV" within 5 words of "Share of Observed" AND at least one positive percentage in non-negation context. Falls back gracefully to judge-based check. |
| 10 | **COMP-M1** (structural gate retry invisible) | Append retry rows to results.jsonl | **Fix still valid** but note: current session shows `attempt:1` because this particular verify succeeded first try. Earlier sessions may have had rework. Fix remains: append `structural_gate_attempt` entries + `attempt:N` on verify row. |
| 11 | **COMP-L3** (weighted_score unreliable) | Audit derivation + standardize or remove | **Not a bug.** v001 used raw 0-8 count; current_runtime uses normalized 0-100 percent (37/40 → 90.6). Schema version change, not unreliability. **Corrected fix**: rename field to `weighted_score_normalized_percent` for clarity + document in session_summary schema. Don't remove. |

### NEW findings discovered during verification (3 items)

| ID | Finding | Fix |
|---|---|---|
| **VERIFY-1** | `harness/util.py:22` has the same `SCRIPT_DIR = harness.ARCHIVE_V001_DIR` hardcode as `agent.py:30` — a second copy | Roll into CROSS-6 fix (part of the 4-place update above) |
| **VERIFY-2** | `harness/__init__.py:21` inserts the v001 scripts dir into `sys.path` — so even after cwd fix, Python imports still resolve to v001 | Add `ARCHIVE_CURRENT_SCRIPTS_DIR` and insert it instead (or alongside) |
| **VERIFY-3** | `STORY-H1` (selected_videos null metadata) is NOT a Fix #15 bug — Fix #15 code at `src/fetcher/youtube.py:34-361` exists and is called. The issue is upstream: the raw fetch returns only `{play_count, title, video_id}` without `upload_date`/`duration` fields, so `_backfill_video_metadata()` has nothing to enrich. **Fix is at the upstream fetcher contract**, not youtube.py. Roll into a new investigation item: why does the initial fetch return a thin metadata shape? |

### CONFIRMED as-is (fix spec is correct, bug is real)

These passed verification without changes needed:
- BLOCK-1 / NEW-1 (monitoring date_to) — confirmed, router fix correct
- BLOCK-5 / STORY3-22 (mock storyboard context) — confirmed; risk noted: need to read actual scene JSON shape before coding
- BLOCK-6 / STORY3-23 (mock cache) — confirmed; low risk in single-worker dev; shelve simpler than SQLite
- Band 3 eval source loaders for competitive, monitoring, storyboard (3 of 4) — all confirmed with exact fix code sketched
- Band 3 geo eval source loader — confirmed (sub-agent initially checked `ahrefs` session which lacks audits; `semrush` session has all 12 audit files per `ls` verification)
- STORY3-24 (storyboard validators) — confirmed; `render_is_stale`, `source_analysis_ids`, `scenes` all real fields; proposed `validate_artifacts` hook via `SessionEvalSpec` is clean
- GEO-NEW-6 (OPENAI_API_KEY) — confirmed; `.env` has empty key; code gracefully degrades to Gemini-only
- STORY-NEW-11 (fabricated source labels) — confirmed; `same_runtime_archive_fallback` + `same_runtime_pattern_cache` found literally in results.jsonl; zero matches in code
- CROSS-4 (strip_repeated_diffs orphan) — confirmed; `.pyc` exists, no source, zero references
- GEO-M2 (pipes in markdown) — confirmed at `build_geo_report.py:248`
- GEO-L5 (generic "FAQ" heading) — confirmed; needs filter in heading extraction
- GEO-NEW-4 (detect noscript parser) — confirmed; decompose() is called but noscript still appears in output, need to verify decompose actually runs
- GEO-NEW-5 (detect --full zero value) — confirmed; provider_unavailable + null pagespeed everywhere
- GEO3-24a (freddy scrape SPA blindness) — confirmed; scraper is HTTP+BS4, no JS render
- GEO-L4 (visibility no retry) — confirmed; no retry path in `src/geo/service.py`
- COMP3-22 (foreplay telemetry gap) — confirmed at `foreplay.py:86-101` + `service.py:129-141`
- COMP3-23 (prior_brief timing) — confirmed at `workflows/competitive.py:13-19` + `post_session.py:121`
- COMP-M2 (client baseline missing detect) — confirmed program gap
- COMP-M3 (visibility credit-exhausted cascade) — confirmed literal error strings in competitors/*_visibility_raw.json
- COMP-NEW-17 (Canva bot-block) — confirmed literal "Please update your browser" content
- COMP-NEW-19 (TikTok 85-byte responses) — confirmed across all 3 competitors
- COMP3-26 (aborted sibling run at 210604) — confirmed; empty results.jsonl + Status:NOT_STARTED
- CROSS-2 (CLI contract drift) — **PARTIALLY confirmed** only. Sub-agent verified visibility flags are documented correctly; drift claim about `detect` + `search-ads` is **unverified**. May be partial false positive — needs re-check.
- MON-NEW-2 (tilde in prompt) — confirmed, one-char fix at `programs/monitoring-session.md:75`
- MON-L3 (empty dirs not documented) — confirmed
- MON-M2 (avg_story_delta:0) — confirmed at `digest-meta.json:99`
- MON-NEW-20 (digest-meta 0600 permissions) — confirmed
- STORY-NEW-12 (no SELECT_VIDEOS fallback) — confirmed; `POST /v1/analyze/creator` exists at `src/api/routers/creators.py:63, 411`
- STORY3-26 (idempotency rule too loose) — confirmed at `programs/storyboard-session.md:126-127`
- STORY3-25 (no BLOCKED exit ceremony) — confirmed

### Final triage state after verification pass

- **47 FIX items** (was 51; dropped 4 INVALIDATED)
- **11 CORRECTED** fix specs (bugs real, patches revised)
- **3 NEW findings** folded into existing fixes (VERIFY-1 rolls into CROSS-6; VERIFY-2 same; VERIFY-3 replaces STORY-H1 subsumption)
- **1 PARTIAL FALSE POSITIVE**: CROSS-2 drift is only partially confirmed (visibility ok, detect/search-ads unverified)
- **19 REJECT** items total (15 from paper pass + 4 new invalidations)
- **4 FALSE POSITIVE** items (unchanged)

---

## OPTIMAL FIX DESIGNS — final specifications (2026-04-14, session 2)

After the verification pass, 6 parallel sub-agents designed optimal fix specs for each of the 47 FIX items. They produced: exact file:line targets, minimal patches, alternatives considered, verification hooks, dependency order, and risk notes. This section consolidates the results.

### 2 additional FALSE POSITIVES found during design pass

| ID | Why false |
|---|---|
| **CROSS-2** (CLI contract drift) | Agent 6 re-verified all 4 program files against actual CLI source in `cli/freddy/commands/*.py`. Result: **all invocations are documented correctly.** `freddy visibility --brand --keywords`, `freddy detect <url> --full`, `freddy search-ads <domain>`, `freddy scrape <url>`, `freddy monitor mentions`, `freddy digest persist` all match. The original audit finding was fabricated or based on a transient error. No fix needed. |
| **GEO-M3** (domain-overview 4 calls vs attempt:3) | Agent 4 read actual `results.jsonl` and found `attempt: 2` on `/pricing/` with status `kept`. The 4 log lines are from different pages or phases, not the same page exceeding rework cap. Audit miscounted. No fix needed. |

**Updated FIX count: 47 → 45**

### Cross-cutting architectural decisions

These apply to multiple fixes and were chosen once then reused:

1. **Redis IS in `pyproject.toml`** — BLOCK-6 mock cache uses Redis with 24h TTL + graceful dict fallback. Simpler than SQLite/shelve.
2. **Playwright is NOT in `pyproject.toml`** — GEO3-24 scrape SPA fallback reduces to a documentation-only fix (add `js_blocked` status, document known limitation). Don't add a 50MB+ browser dep for a partial coverage gain.
3. **`SessionEvalSpec` gets a new optional field** `validate_artifacts: Callable | None = None`. Lane-specific validators live in each `session_eval_*.py`, not in the core `session_evaluator.py` (preserves the 88-line domain-free harness).
4. **Backend telemetry uses `_include_telemetry: bool = False` kwarg pattern** for backwards compat. Existing callers get the old shape; new autoresearch traces pass `_include_telemetry=True`.
5. **`compute_weighted_failure_count()` is the generic hard-fail fix** — double-count any criterion with `normalized_score < 0.3`. No domain knowledge in the harness. `HARD_FAIL_THRESHOLD = 0.3` as named constant.
6. **Lane-specific counters via dispatch dict** — `FINDINGS_COUNTERS = {"geo": _count_bracketed, "competitive": _count_unbracket, "monitoring": _count_unbracket, "storyboard": _count_bullet_sections}`. Each lane owns its findings.md format.

### Band 1 — Harness/runtime infrastructure (5 items)

| # | ID | File:line | Patch |
|---|---|---|---|
| 1 | **CROSS-6** | 4 places | `harness/__init__.py:15-16`: add `ARCHIVE_CURRENT_DIR = AUTORESEARCH_DIR/"archive"/"current_runtime"`; change `ARCHIVE_SCRIPTS_DIR = ARCHIVE_CURRENT_DIR/"scripts"`. `__init__.py:21`: add current_runtime to sys.path. `agent.py:30` + `util.py:22`: `SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR`. **Verify**: `ps aux` shows subprocess cwd = current_runtime. **Dep**: must land FIRST (all harness fixes depend on it). |
| 2 | **TP-C3** | `run.py:191` | `archive_dir = SCRIPT_DIR / "archived_sessions" / f"{datetime.now():%Y%m%d-%H%M%S}-{domain}-{client}"` (not `sessions/_archive/`). **Verify**: fresh run's prior state lands at variant root, not inside sessions tree. **Dep**: after CROSS-6. |
| 3 | **CROSS-4** | New `scripts/strip_repeated_diffs.py` + hook | Git log empty — write from scratch. Script reads `multiturn_session.log`, collapses identical diff markers within 5-line windows. Wire into `run.py` post-session hook. **Verify**: log size reduction + readable after-diff. |
| 4 | **STORY-NEW-11** | New `scripts/validate_session.py` + hook | Allowlist starts with `{"freddy"}` prefix match. Non-fatal — logs ERROR to stderr, session continues. Post-session hook. **Verify**: inject fake source → ERROR logged. |
| 5 | **CROSS-3** | `scripts/summarize_session.py:76-96` | Remove `"done"` from productive bucket. Add `"partial"` to its own bucket. Add reconciliation guard: `if categorized_sum > iterations["total"]: print(WARNING)`. **Verify**: synthetic results.jsonl with mixed statuses → correct bucket counts. |
| 6 | **VERIFY-3** | `src/fetcher/youtube.py:309` | Change `extract_flat=True` → `extract_flat="in_playlist"` in `_extract_tab()`. Preserves upload_date + duration in flat mode. **Verify**: `_list_creator_videos("MrBeast", 20)` returns VideoStats with non-null duration_seconds + posted_at. **Risk**: 10-20% slower, acceptable. |

### Band 2 — Backend/API correctness (4 items)

| # | ID | File:line | Patch |
|---|---|---|---|
| 7 | **BLOCK-1** | `src/api/routers/monitoring.py` `list_mentions` handler | After FastAPI parses `date_to`, add: `from datetime import time; if date_to is not None and date_to.time() == time(0,0,0): date_to = date_to.replace(hour=23, minute=59, second=59)`. **Verify**: unit test inserting mention at 04-12 23:00 UTC with `date_to=2026-04-12` should return it. **Dep**: none, safe for all callers since bare dates parse to 00:00:00. |
| 8 | **BLOCK-5 / STORY3-22** | `src/api/routers/video_projects.py:343-414` `_mock_storyboard_snapshot` | Parse `body.context` as JSON, extract `scenes[]`, loop to build `VideoProjectSceneResponse` per scene preserving `title/prompt/duration_seconds/transition/caption/audio_direction/shot_type/camera_movement/beat`. Fall back to 1-scene stub if context is None or invalid JSON. Note: story plans use `transition_to_next` field, not `transition` — map it. **Verify**: unit test with 6-scene context → `len(snapshot.scenes) == 6`. |
| 9 | **BLOCK-6 / STORY3-23** | `src/api/routers/video_projects.py:340` module dict | Replace `_MOCK_STORYBOARD_CACHE` with Redis-backed cache (redis already in `pyproject.toml`). Key: `mock_storyboard:{project_id}`, TTL: 86400s. Get client from `request.app.state.redis` with fallback to module dict if Redis unavailable. **Verify**: integration test with 2 simulated workers, POST on worker A → GET on worker B succeeds. |
| 10 | **GEO-NEW-4** | `src/geo/patterns.py:150-185` `check_answer_first_intro` | Add defensive decompose at function start: `for tag in soup.find_all({"script", "style", "noscript"}): tag.decompose()`. Root cause: detector.py:39 rebuilds soup from raw HTML, bypassing extraction.py's decompose. Also add `"your browser or operating system is out of date"` to filler_starts list. **Verify**: fixture with noscript banner + real paragraph → detector picks real paragraph. |

### Band 3 — Evaluator trust (7 items)

| # | ID | File:line | Patch |
|---|---|---|---|
| 11 | **GEO loader** | `workflows/session_eval_geo.py:99-117` | Append `audits/*.full.json` loader. Only `.full.json` (strict superset of `.json`). Truncate to 800 chars each. 6 files × 800 = ~5KB added. **Verify**: judge reasoning cites audit fields. |
| 12 | **COMP loader** | `workflows/session_eval_competitive.py:100-110` | Append `findings.md` (1500 chars) + first 3 `analyses/*.md` (800 chars each). ~4.5KB total. |
| 13 | **MON loader** | `workflows/session_eval_monitoring.py:164-182` | Aggregate mode: append first 5 `mentions/*.json` (500 chars each) + `recommendations/cross_story_patterns.md` (1000 chars). ~4KB total. |
| 14 | **STORY loader** | `workflows/session_eval_storyboard.py:90-110` | Append `findings.md` (1500 chars) as "Creative Intent" block after patterns. |
| 15 | **CROSS-5** | `autoresearch/harness/session_evaluator.py` | Add `HARD_FAIL_THRESHOLD = 0.3` constant. Add helper: `compute_weighted_failure_count(results) → int` that counts each failure, doubling any with `normalized_score < 0.3`. Wire into decision caller. **No domain knowledge added.** Keeps harness file pure. |
| 16 | **STORY3-24** | `workflows/specs.py` + `session_eval_storyboard.py` + `src/evaluation/service.py` | Add `validate_artifacts: Callable \| None = None` to `SessionEvalSpec`. Implement `validate_storyboard_artifacts(session_dir)` with 4 checks: (a) scenes≥2, (b) `render_is_stale: False`, (c) unique `source_analysis_ids` arrays (not all-identical), (d) all analysis_ids resolve to files in `patterns/`. Wire as pre-judge call in service.py. Return failures → force REWORK via `_persist_failure`. |
| 17 | **GEO-NEW-6** | `src/api/dependencies.py` (or `harness/preflight.py`) | Add startup check: `if len(eval_judges) < len(eval_settings.judge_models): logger.warning(...)`; `if len(eval_judges) < 2: logger.critical("single-judge mode")`. Non-fatal. User sets `OPENAI_API_KEY` in `.env`. |

### Band 4 — Scorer-visible artifacts (6 items, -1 FP = GEO-M3)

| # | ID | File:line | Patch |
|---|---|---|---|
| 18 | **BLOCK-2 / GEO3-23** | `scripts/build_geo_report.py:188` | `measured_visibility = isinstance(visibility_data, dict) and not visibility_data.get("error") and visibility_data.get("queries_with_data", 0) > 0`. **Note**: key is `error`, not `status` (confirmed in `src/geo/service.py:195`). |
| 19 | **GEO-NEW-7** | `scripts/build_geo_report.py:140` | `slug = page.strip("/").split("/")[-1] or "index"` (trailing component only, matches `path.stem` at line 150). Subsumes GEO3-22, GEO-H6, GEO-M1, GEO-L3, GEO-M5. |
| 20 | **CROSS-1** | `scripts/summarize_session.py:107-110` | Lane-specific dispatch: `FINDINGS_COUNTERS = {"geo": _count_bracketed, "competitive": _count_unbracket_headings, "monitoring": _count_unbracket_headings, "storyboard": _count_bullet_sections}`. 4 helper functions with appropriate regex. |
| 21 | **GEO-M2** | `scripts/build_geo_report.py:243-249` | Add `_escape_markdown_cell(v) = str(v).replace("|", "\\|")` helper. Apply to all string cells: label, query, gap, status, blocks. |
| 22 | **GEO-L5** | `scripts/build_geo_report.py:95-97` | Add `GENERIC_HEADING_PATTERNS = {'faq','about','contact','home','more','overview','introduction','summary','conclusion','resources','learn more'}`. Filter: `[h for h in headings if h.strip().lower() not in pat and len(h) > 3]`. |
| 23 | **GEO-H1** | `scripts/build_geo_report.py:161-173` | Add `_tag_simulated_scores(scores_dict, is_simulated) → dict` helper. When building summary rows, detect simulated via absence of `evaluator_feedback_on_before`, tag scores with `(simulated)` suffix. Passive enforcement — doesn't depend on agent discipline. |

### Band 5 — Competitive + freddy tools (10 items)

| # | ID | File:line | Patch |
|---|---|---|---|
| 24 | **COMP3-22** | `src/competitive/service.py` + `providers/foreplay.py` | Add `AdSearchTelemetry` TypedDict. `search_ads()` gets `_include_telemetry: bool = False` kwarg. When True, returns `(results, telemetry)` tuple with `raw_foreplay_ads_count`, `matched_brand_id`, `brand_domain_filter_dropped`, `link_url_filter_dropped`, `final_ad_count`, `provider_error`. Backwards-compatible. |
| 25 | **COMP3-23** | `workflows/competitive.py` + `scripts/extract_prior_summary.py` | Add `pre_session_hooks` that reads `{runtime_root}/_prior_briefs/competitive-{client}.json`. Modify `post_summary_hooks` to write there instead of inside session dir. Survives session archival. |
| 26 | **COMP3-24** | `workflows/session_eval_competitive.py:93-97` | Add `_has_valid_sov_data(text) → bool` with word-window negation check. 5-word window, negation markers: `{not, no, without, couldn't, can't, unable, misleading, meaningless, useless}`. Require ≥1 positive percentage outside negation context and not standalone "0". |
| 27 | **COMP-M1** | `scripts/evaluate_session.py:252-266` | Add `_log_result(entry)` helper. Append `structural_gate_attempt` rows to `results.jsonl` on both PASS and FAIL paths. Include `failures` list for audit. Requires passing `--iteration` from harness. |
| 28 | **COMP-M2** | `programs/competitive-session.md` BASELINE section (~line 100) | Program text: "Also run `freddy detect <client_domain>` to capture infrastructure state; persist to `_client_baseline_raw.json` alongside ad search output." Structural completeness, paper-allowed. |
| 29 | **COMP-M3** | `src/geo/providers/cloro.py` | Add `CloroCreditError` subclass of `CloroError`. Add per-platform circuit breakers via `_get_platform_breaker(platform)`. Threshold: 2 consecutive credit failures → 10-min cooldown. Reuse existing CircuitBreaker pattern from foreplay. |
| 30 | **COMP3-26** | `autoresearch/harness/util.py` + `run.py` | Add `acquire_session_lock(domain, client)` + `release_session_lock()`. Lockfile at `sessions/{lane}/{client}/.lock` with PID + timestamp. Stale lock takeover at 30min. PID liveness via `os.kill(pid, 0)`. Wire into `run_domain_fresh`'s try/finally. |
| 31 | **COMP-L3** | `scripts/summarize_session.py` results writer | Rename `weighted_score` → `weighted_score_percent`. Add `schema_version: "2.0"` field. Document in README. Not a bug, just schema clarity. |
| 32 | **GEO-NEW-5** | `programs/geo-session.md:109, 328` | Remove `--full` flag from OPTIMIZE invocation at line 109 (`freddy detect <url>`). Line 328: mark as "currently unavailable pending provider credentials". Preserve line for future restoration. |
| 33 | **GEO3-24** | `programs/geo-session.md` Known Limitations + `src/geo/fetcher.py` | Document JS-render limitation. Add `js_rendered: False` flag in FetchResult with note. Consumers check `word_count < 200` to detect SPA shells. **No playwright dep added** (not available). |

### Band 6 — Program files + polish (9 items, -1 FP = CROSS-2)

| # | ID | File:line | Patch |
|---|---|---|---|
| 34 | **STORY-NEW-12** | `programs/storyboard-session.md` after line 113 | Insert "SELECT_VIDEOS Bootstrap Rule" section: on 404 with "not in cache", call `POST /v1/analyze/creator` with `{platform, username, limit: 50}`, wait 10s, retry GET videos once, mark BLOCKED if both fail. |
| 35 | **STORY3-26** | `programs/storyboard-session.md:126-127` | Replace idempotency rule with: "check if `{session_dir}/patterns/{video_id}.json` exists **in the current session directory only**. NEVER copy, symlink, or reference `patterns/` files from `_archive/`, `archived_sessions/`, or any location outside current session. Appearing patterns without generation = critical protocol violation → BLOCKED." |
| 36 | **STORY3-25** | `programs/storyboard-session.md` after line 475 | Insert full BLOCKED Exit Ceremony section (~50 lines): trigger conditions, `session.md` Status template, `findings.md` requirement, `results.jsonl` final entry shape, no-proceed rule, phase transition rules. |
| 37 | **COMP-NEW-17** | `programs/competitive-session.md` SYNTHESIZE section (before step 5, ~line 242) | Insert bot-detection filter rule: classify scrape as bot-blocked when HTTP 200 + body < 100 words + contains patterns like "update your browser"/"unsupported"/"captcha"/"challenge"/"crawler". Record `scrape_status: bot_blocked` in results.jsonl. Exclude from positioning analysis. |
| 38 | **COMP-NEW-19** | `programs/competitive-session.md` GATHER (after line 129) | Insert known-dead provider note about `freddy search-content --platform tiktok` for design/creative tool brands. Skip and use Instagram/YouTube fallback. |
| 39 | **GEO-L4** | `programs/geo-session.md:38` | Replace with: "If visibility times out (>45s), retry once after 30-second backoff before treating as optional. Do not retry a second time." |
| 40 | **MON-NEW-2** | `programs/monitoring-session.md:75` | Delete 1 char: `~30` → `30`. |
| 41 | **MON-L3** | `programs/monitoring-session.md` after line 94 | Add one-line note: "empty `stories/` and `anomalies/` directories are expected in low-volume path; CLUSTER_STORIES and DETECT_ANOMALIES are skipped." |
| 42 | **MON-M2** | `workflows/monitoring.py` `augment_quality_metrics` | Add `elif len(results) == 0: quality_metrics["avg_story_delta"] = None`. Writes as JSON null. Check consumers for None handling. |
| 43 | **MON-NEW-20** | `cli/freddy/commands/digest.py` after line 38 | Add `import os; os.chmod(file, 0o644)` after persist call. Idempotent, cross-platform-safe. |

### Updated final counts

| | Before design pass | After design pass |
|---|---|---|
| **FIX** (own work item) | 47 | **45** |
| **REJECT** (total) | 19 | **21** (+CROSS-2, +GEO-M3) |
| **FALSE POSITIVE** | 4 | 4 |
| **Items with detailed fix spec** | 0 | **45** |

### Execution dependency graph

```
Band 1 (harness infra) must land FIRST. Within Band 1:
  CROSS-6 → TP-C3 → CROSS-4 → STORY-NEW-11 → CROSS-3 → VERIFY-3

Band 2 (backend) can run in parallel with Band 1:
  BLOCK-1, BLOCK-5, BLOCK-6, GEO-NEW-4 (all independent)

Band 3 (evaluator trust) must land AFTER Band 1:
  4 source loaders (parallel) → CROSS-5 → STORY3-24 → GEO-NEW-6

Band 4 (scorer artifacts) can run after Band 1:
  BLOCK-2, GEO-NEW-7, CROSS-1, GEO-M2, GEO-L5, GEO-H1 (all independent)

Band 5 (competitive + tools) can run after Band 1:
  COMP3-22, COMP3-23, COMP3-24, COMP-M1, COMP-M2, COMP-M3, COMP3-26, 
  COMP-L3, GEO-NEW-5, GEO3-24 (all independent)

Band 6 (programs + polish) can run any time:
  All 9 items independent, pure text/config edits
```

**Critical path**: CROSS-6 → TP-C3 → (Band 3 + Band 5 in parallel) → STORY3-24. Everything else can run in background.

### Paper compliance re-verification

After design, all 45 fixes were re-checked against Meta-Harness + Hyperagents:

- **Meta-Harness "delegate diagnosis to proposer"**: ✓ All Band 1-4 fixes touch infrastructure the proposer cannot reach. Band 5-6 fixes are structural completeness, domain knowledge, math-before-money, or deliverable integrity (all allowed exceptions).
- **Meta-Harness "rich feedback, not compressed"**: ✓ Band 3 source loaders ADD rich evidence to the judge. CROSS-4 diff dedup removes REPETITION, preserves the first occurrence of each diff.
- **Hyperagents "eval protocols intentionally fixed"**: ✓ Items 11-16 touch eval loaders + threshold + validators — all framed as **one-time corrections to a corrupt baseline**, not ongoing tuning. After they land, the protocol is fixed and frozen.
- **Hyperagents "parent selection fixed"**: ✓ No fix touches `autoresearch/evolve.py` parent selection.
- **Hyperagents "5 replicate bootstrap CIs"**: ✓ No fix touches replicate count or CI computation.

**Result**: all 45 fixes remain paper-compliant.

---

---

## Cross-lane bugs (affect multiple workflows)

### CROSS-1 [HIGH] — session_summary findings_count broken across ALL 4 workflows

**Affected**: geo, competitive, monitoring, storyboard

**Evidence**: `session_summary.json` reports `findings_count: 0` for every lane even when `findings.md` contains real entries:
- geo: `findings.md` has 4 entries → summary reports 0
- competitive: `findings.md` has 5 CONFIRMED + 1 OBSERVATION → summary reports 0
- monitoring: `findings.md` has 4 categorized entries → summary reports 0
- storyboard: `findings.md` has 8 entries (4 Confirmed, 2 Disproved, 2 Observations) → summary reports 0

**Root cause hypothesis**: Fix #10 updated the regex to `r"^(?:### \[?\w+\]?\s|- [A-Z]+:)"`. That should match all 4 formats. Either:
1. The regex doesn't match the actual findings.md format the lanes write
2. `summarize_session.py` is being loaded from a stale cached path
3. The count is being computed but overwritten by `null`/`0` downstream

**Files**:
- `autoresearch/archive/current_runtime/scripts/summarize_session.py:107-110` (the regex)
- `sessions/{lane}/{client}/session_summary.json` (all 4 showing 0)
- `sessions/{lane}/{client}/findings.md` (all 4 with real content)

**Fix needed**: Read each lane's findings.md format, verify the regex matches, add unit test.

---

### CROSS-2 [HIGH] — CLI contract drift in all 4 program files

**Affected**: geo, competitive (confirmed in audits); monitoring, storyboard likely

**Evidence**: During competitive/figma run, Codex hit these on first call:
- `freddy visibility` required `--brand` and `--keywords` flags — prompts say positional query arg
- `freddy detect` required full `https://` URL — prompts say bare domain
- `freddy search-ads` required `.com` TLD suffix — prompts omit it

Codex recovered by adapting after each error but wasted 3+ parallel calls per command. Claude run (earlier) hit identical issues. Log evidence: `competitive/figma/logs/multiturn_session.log:504-533`.

**Root cause**: Program files document stale CLI signatures that don't match current `freddy` CLI behavior.

**Fix needed**: Run each `freddy <cmd> --help`, update the command tables in all 4 program files:
- `autoresearch/archive/current_runtime/programs/geo-session.md`
- `autoresearch/archive/current_runtime/programs/competitive-session.md`
- `autoresearch/archive/current_runtime/programs/monitoring-session.md`
- `autoresearch/archive/current_runtime/programs/storyboard-session.md`

---

### CROSS-3 [HIGH] — Iteration counter still drifting

**Affected**: storyboard, geo

**Storyboard evidence**: `session_summary.json` has `iterations.total=4, productive=8` (impossible — productive > total). Fix #14 reconciliation guard was added to `summarize_session.py` but didn't trigger for storyboard. Root cause: `results.jsonl` labels ALL 5 ideate entries + 1 error as `"iteration":4`, so `distinct_iters` set is `{1,2,3,4}` = size 4, but `productive` counts 8 rows with `status:kept`. Reconciliation check `if iterations["total"] < sum_categorized` should fire but apparently doesn't.

**Geo evidence**: `session_summary.json` has `"uncategorized": 1`. The `type:"report"` iteration 10 is not in the status→bucket map. Should be counted as productive (status: "complete").

**Fix needed**:
1. Debug why reconciliation guard didn't fire on storyboard (check if `sum_categorized` includes all categories or misses `uncategorized`)
2. Add "complete" to the productive status list in `summarize_session.py`
3. Fix source-side: storyboard program must increment iteration per ideate entry (plan's fix #14 source-side instruction was added but agent ignored it)

---

### CROSS-4 [HIGH] — Harness git-diff log bloat

**Affected**: monitoring confirmed; likely all lanes

**Evidence**: `monitoring/Shopify/logs/multiturn_session.log` is 656KB / 7013 lines. Roughly 80% is repeated `git diff` output emitted after every `exec` command. Every CLI call is followed by a full `git diff` of all session files (digest.md, findings.md, recommendations/*.md). Example: lines 1885–2060, 5472–5663, and 22 additional repetitions.

This bloats logs 5-10x and will blow token budgets for LOAD_CONTEXT phases.

**Root cause**: Harness instrumentation intercepting stdout with a post-exec hook. Not the same as the Fix #17 codex diff-context — this is a different source.

**Files**: Unknown yet. Need to grep for `git diff` emission in harness/runtime code.

**Fix needed**: Strip post-exec diff dumps or gate them behind a debug flag. The Fix #17 post-processor strips repeated diff blocks at session end, but that's a band-aid — the right fix is to not emit them in the first place.

---

### CROSS-5 [MEDIUM] — Evaluator lenience: 1-of-8-failed rule ships hard fails

**Affected**: geo confirmed; monitoring confirmed

**Evidence**:
- **geo/pricing**: GEO-4 hard fail (score 0.0, "FAQ robotically describes UI, broken Current AI citation count column") — marked KEEP because rule is `1_of_8_evaluated_failed → KEEP`
- **geo/features**: GEO-4 hard fail with hostile feedback ("entirely bolted on... feels completely unnatural") — marked KEEP
- **geo/backlinks**: GEO-8 fail (0.25) — KEEP
- **monitoring/digest**: MON-2 fail (score 0.25, "violated direct negative constraint about inline confidence") — KEEP

**Root cause**: Evaluator aggregate rule counts ANY single failure as acceptable regardless of severity or category. No asymmetric weighting for user-facing criteria (GEO-4 voice/fit, MON-2 inline confidence) vs technical ones.

**Fix needed**: Add criterion weighting to `digest_eval.json` / eval aggregation. Hard fails (score < 0.3) on user-facing criteria should produce REWORK even if only 1 of 8.

---

## GEO/semrush — Claude backend

Session: `sessions/geo/semrush/` — COMPLETE, 10 iterations, 6 KEEP, 0 DISCARD, claimed avg_delta +0.50

### GEO-B1 [BLOCKER] — report.md lies about visibility availability

**Evidence**:
- `competitors/visibility.json`: `"status": "timeout"`, `"queries_with_data": 0`, timeout error
- `report.json:217`: `"visibility_available": true`, `"total_citations": 0`
- `report.md:10`: "Visibility data was available and contributed 0 observed citations across tracked queries."

**Root cause**: `autoresearch/archive/current_runtime/scripts/build_geo_report.py:188` sets `measured_visibility = bool(visibility_data)`. A non-empty dict with a timeout envelope returns True. The builder doesn't distinguish "present but failed" from "present and successful."

**Fix**: Check `visibility_data.get("status") != "timeout"` and `visibility_data.get("method") == "measured"`.

### GEO-B2 [BLOCKER] — Optimized pages still ship meta-instruction leak that findings.md claims was fixed

**Evidence**:
- `optimized/pricing.md:38-43` ships with a `| Current AI citation count | Unavailable |` column
- `optimized/keyword-research-toolkit.md:38` has the same column
- `findings.md:13` asserts this was the precise reason for a rework and was FIXED ("Removing that user-facing metric produced KEEP with 8/8 criteria passing")
- `evals/optimized-pricing.json:35` explicitly cites this as the GEO-4 failure reason ("broken/empty column for AI citations")
- Agent marked KEEP anyway

**Root cause**: 
1. Agent ignored the eval's own feedback and published with the leak intact
2. Findings doc records a fix that didn't actually land in the artifact
3. GEO-B1 + CROSS-5 allow this to pass

**Fix**: Wire eval feedback into a guard — if eval GEO-4 feedback contains "broken column" or "unavailable" strings, force REWORK before KEEP can be asserted.

### GEO-H1 [HIGH] — Baseline "before" scores are fabricated by the agent, not measured

**Evidence**: Program (log:116) says "Assess current citability + GEO quality... Use the Scoring Rubric." The evaluator is only invoked on `optimized/*.md`, never on source pages. All "before" scores in `results.jsonl` (0.18, 0.31, 0.30, 0.34, 0.27, 0.29) and in `session.md:17-22` are agent-authored heuristic estimates. Program (log:288) requires `(simulated)` tag when derived heuristically — tag is absent everywhere.

**Impact**: The entire "Delta +0.62" table is unverifiable. Evolution can't trust before/after deltas as selection signal.

**Fix**: Program must explicitly require running evaluator on source page BEFORE optimization. OR explicitly tag simulated scores. OR drop the before/delta columns entirely if they can't be measured.

### GEO-H2 [HIGH] — Pricing KEEP with GEO-4 hard fail (0.0)

**Evidence**: `evals/optimized-pricing.json` has score 0.0 on GEO-4 with hostile feedback. Eval aggregate rule `1_of_8_evaluated_failed → KEEP` allowed it. Agent inflated the self-assigned after-score by averaging `(0.75+1+1+0+1+1+1+1)/8 = 0.84` without weighting the failure.

**Fix**: See CROSS-5.

### GEO-H3 [HIGH] — Features hub GEO-4 also failed 0.0 — still KEEP

**Evidence**: `evals/optimized-features.json:35`: "FAQ section robotically describes the page's own UI to the user... introducing a jarring comparison to HubSpot in the very first introductory paragraph... feels completely unnatural." Session.md:46 and findings.md:26 acknowledge the residual risk but still publish.

**Fix**: Same as CROSS-5.

### GEO-H4 [HIGH] — Evaluator hallucinated `freddy detect` as "hallucinated tool"

**Evidence**: First pricing eval (log:3317, GEO-8 feedback): "the llms.txt recommendation relies on a hallucinated tool (`freddy detect`)". `freddy detect` is a real, documented CLI used by this very session (log:340).

**Impact**: Evaluator model (`gemini-3.1-pro-preview`) making load-bearing false claims about reality. Doesn't change keep/reject outcome here but suggests the evaluator needs grounding against known-good tool lists.

**Fix**: This is exactly what the multi-model ensemble (Fix #1a/1b) was supposed to catch. GPT-5.4 is unlikely to hallucinate `freddy detect` as nonexistent. Needs `OPENAI_API_KEY` set and the evaluator re-run.

### GEO-H5 [HIGH] — Evaluator raw_score 3/5 coded as `passes: true` with score 0.5

**Evidence**: Same pricing first-eval log (GEO-8): `"passes": true, "score": 0.5, "raw_score": 3.0`. The pass threshold appears to be raw_score ≥ 3 — "barely mediocre" counts as a pass. Same pattern on backlinks GEO-2 (`score: 0.75 raw_score: 4.0` also "pass").

**Impact**: Inflates keep rates across all pages.

**Fix**: Tighten pass threshold to raw_score ≥ 4 OR change "pass" to "acceptable"/"strong" tiers.

### GEO-H6 [HIGH] — Three different avg_delta values across artifacts

**Evidence**:
- `results.jsonl:10`: `"avg_delta":0.50`
- `session_summary.json:29`: `0.503`
- `report.json:2` / `report.md:6`: `0.555`

**Root cause**: Report builder computes delta only over pages where it can reconstruct before/after from results.jsonl — but overwrites with `null` for 4 of 6 pages (see M1), then averages only the 2 remaining: `(0.62+0.49)/2 = 0.555`.

**Fix**: Report builder must match all optimize entries, not just first/last per page.

### GEO-M1 [MEDIUM] — 4 of 6 pages have empty before/after in report

**Evidence**: `report.json:10-56, 90-111, 146-168`: `"before": {}, "after": {}, "delta": null` for backlinks, domain-overview, keyword-research-toolkit, site-audit. Only pricing and features have scores populated. `report.md:18-23` shows "Delta | n/a" for 4 rows.

**Root cause**: Report builder reading only first or last results.jsonl optimize entry per page.

**Fix**: Aggregate all results.jsonl entries per page, use latest.

### GEO-M2 [MEDIUM] — Markdown table broken by pipe characters in query values

**Evidence**: `report.md:18-23` has unescaped pipes inside Query cells: `| Backlink Tool: Check Backlinks for Any Website | Semrush | backlink-toxic-risk...`. The literal `|` terminates the Query cell early, producing mis-aligned cells.

**Fix**: Escape `|` as `\|` in query values before writing markdown.

### GEO-M3 [MEDIUM] — domain-overview evaluator called 4 times but results.jsonl says attempt: 3

**Evidence**: Log lines 27455, 29702, 31948, 35653 — four separate `evaluate_session.py` calls on `optimized/domain-overview.md`. `results.jsonl:8` records `"attempt":3`. Program allows max 3, so this may have silently exceeded the rework cap.

### GEO-M4 [MEDIUM] — session_summary `uncategorized: 1`

**Evidence**: `session_summary.json:12` has `"uncategorized": 1` alongside 9 productive iterations. The `type:"report"` iter 10 is miscategorized by the results.jsonl → status classifier.

**Fix**: See CROSS-3.

### GEO-M5 [MEDIUM] — Heading targets and question bank skewed to 2-3 pages

**Evidence**: `report.md:39-56`: "Top heading targets" lists only 3 unique headings each with count 1. Same root cause as GEO-M1: report builder only sees blocks for pricing + features.

### GEO-M6 [MEDIUM] — backlinks GEO-8 fails (0.25) — still KEEP

**Evidence**: Second GEO-8 fail in the run. Same 1-of-8 keep rule permissiveness.

### GEO-L1-L7 [LOW] — Miscellaneous

- **L1**: findings.md:14 claims backlinks achieved "8/8 criteria passing" but eval file says `1_of_8_evaluated_failed`. Finding is wrong.
- **L2**: Pricing GEO-6 returned `passes: null` on attempt 1 with "First item in session, cross-item comparison not applicable." Order-dependent scoring not signaled.
- **L3**: report.md:5 claims "Average Delta: +0.555" while the table shows "+0.490" and "+0.620" averaging to 0.555 — consistent with report.json but inconsistent with every other artifact.
- **L4**: Visibility timed out at 45s and was never retried despite 10 iterations. Single retry would have cost ~$0.01.
- **L5**: `top_heading_targets` contains literal string `"FAQ"` with count 1 — report builder not normalizing heading extraction.
- **L6**: `gap_allocation.json` shows all 6 slugs as single-item batches — no parallelization. Not a bug, anti-pattern.
- **L7**: `audits/*.full.json` was only run for pricing (log:3018). Other 5 pages only have base `audits/*.json`. Program says `detect --full` for every optimize phase. Infra data partially missing.

---

## Competitive/figma — Codex backend, GPT-5.4 xhigh — 37/40

Session: `sessions/competitive/figma/` — COMPLETE, 6 iterations, scored 37/40. Previous Claude run (same fixture) scored 40/40.

### COMP-H1 [HIGH] — 3-point delta is infrastructure luck, not Codex deficiency

**Evidence**: Codex ran at 2026-04-13 21:06. All four `freddy search-ads` calls returned `ad_count: 0` for figma.com / canva.com / sketch.com and `AllProvidersUnavailableError` for miro.com. Log lines 463–475. File sizes:
- `competitors/canva_ads_raw.json`: 58 bytes (0 ads)
- `competitors/sketch_ads_raw.json`: 59 bytes (0 ads)
- `competitors/_client_baseline_raw.json`: 58 bytes (0 ads)

Claude run on the same fixture ~8 hours earlier at 12:24:
- `archived_sessions/20260413-210253-competitive-figma/competitors/canva_ads_raw.json`: 175,604 bytes / 100 ads
- `archived_sessions/20260413-210253-competitive-figma/competitors/sketch_ads_raw.json`: 50,006 bytes / real data

Four consecutive zeros from the same provider within 2 seconds is statistically implausible. It's Foreplay downtime.

**Root cause**: Codex accepted the zeros and pivoted to "observable posture" framing (log 479) instead of retrying once or running `/status`.

### COMP-H2 [HIGH] — 3-point gap concentrated in CI-3 and CI-5, both traceable to missing ad data

**Evidence**: Codex vs Claude per-criterion raw scores:
| Criterion | Codex | Claude |
|-----------|-------|--------|
| CI-1 | 5/5 | 5/5 |
| CI-2 | 5/5 | 5/5 |
| CI-3 | **4/5** | 5/5 |
| CI-4 | 5/5 | 5/5 |
| CI-5 | **3/5** | 5/5 |
| CI-6 | 5/5 | 5/5 |
| CI-7 | 5/5 | 5/5 |
| CI-8 | 5/5 | 5/5 |

Judge CI-3 feedback: "only partially addresses 'rate of change'... does not explicitly detail what Sketch or Miro are abandoning" — traceable to missing `started_at` values (no ads).

Judge CI-5 feedback: "does not articulate why Figma is uniquely positioned... reads more like standard tactical SEO/LLMO best practices" — traceable to absence of competitor-specific creative pattern.

### COMP-H3 [HIGH] — Codex picked weaker competitor slate

**Evidence**: Codex: Canva, Sketch, Miro. Claude: Canva, Sketch, Adobe. Miro's ad search immediately failed with `AllProvidersUnavailableError`, starving the synthesis further. Program lists Adobe XD as #1 direct-competitor peer for Figma. Codex never reconsidered the slate after Miro's outage.

### COMP-M1 [MEDIUM] — Structural gate retry invisible in results.jsonl

**Evidence**: Log lines 16741, 18815: first brief was >2000 words with only one citation match, structural gate REWORKed. Codex rewrote to 1602 words. `results.jsonl` reports `synthesize, sections:11, status:done` with NO `attempt` field — retry is invisible in structured output.

**Fix**: Structural gate must log `attempt:N` in `results.jsonl` for auditability.

### COMP-M2 [MEDIUM] — Figma client-baseline missing GEO/crawler data

**Evidence**: `_client_baseline.json` contains only the ad search (0 ads, no detect, no scrape). Open Questions in `session.md:16` flags this. The brief's core recommendation (machine-readable comparison hub) assumes Figma doesn't already have `llms.txt`/schema — untested.

**Root cause**: Program instructions only mandate `freddy search-ads <client_domain>` for baseline, not `detect`.

**Fix**: Program rule gap — add `freddy detect` to client-baseline requirements.

### COMP-M3 [MEDIUM] — Visibility lane dead for all competitors

**Evidence**: Canva and Miro visibility returned 0 citations with provider errors; Sketch timed out at 45s with 0/3 queries resolved. Chronic.

### COMP-M4 [MEDIUM] — ScrapeCreators credit exhaustion not detected

**Evidence**: `canva_content_raw.json`, `sketch_content_raw.json`, `miro_content_raw.json` all 84–86 bytes. Claude run's `source_notes` explicitly identified `"ScrapeCreators credit exhaustion"` from stderr. Codex did not detect the pattern and logged nothing in `results.jsonl` about provider state.

**Root cause**: Codex doesn't parse stderr for provider-state signals the way Claude does.

### COMP-M5 [MEDIUM] — CLI contract drift (see CROSS-2)

### COMP-L1-L5 [LOW] — Miscellaneous

- **L1**: IC credit-exhausted signals in stderr (`ic_bad_request_400 path=/public/v1/discovery/`) never surfaced to results.jsonl
- **L2**: Priority Queue orders KEPT competitors by analysis order, not quality. Cosmetic.
- **L3**: `weighted_score: 90.6` in session_summary vs `weighted_score: 8` in the archived Claude run — field is unreliable across runs
- **L4**: `findings_count: 0` — see CROSS-1
- **L5**: `brief.md:68` and `prior_brief_summary.json` disagree about prior-brief existence — likely harness writes the file after agent drafts

**Fix recommendation**: Add one-line retry rule to competitive program — "if ≥3 consecutive `search-ads` calls return `ad_count:0`, retry all after 30s before pivoting."

---

## Monitoring/Shopify — Claude backend

Session: `sessions/monitoring/Shopify/` — COMPLETE, 1 iteration (low-volume shortcut path), 25 mentions loaded (of 44 in-window)

### MON-B1 [FALSE POSITIVE — reclassified] — weekly_digests UNIQUE constraint

The audit agent reported this as a blocker claiming the constraint wasn't enforced. **Verified false**: constraint IS applied, only 1 row exists for `(Shopify, 2026-04-12)` in the DB. The agent's two persist calls upserted correctly via `ON CONFLICT (monitor_id, week_ending) DO UPDATE` in `src/monitoring/repository.py:1505`. Auditor misread log response IDs.

### MON-H1 [HIGH] — Agent didn't identify date-to midnight-parsing bug as root cause

**Evidence**: First `digest-meta.json` executive_summary (log 2068): "Coverage starts on 2026-04-06 with no start-date ingestion gap; no loaded mention landed on 2026-04-12." Second one (log 5669): "no start-date ingestion gap was present."

**Analysis**: Latest loaded mention is `2026-04-11T09:47:59Z`, a full day earlier than the window's intended upper bound. A disciplined agent should have flagged this as suspicious (24-hour gap on the tail of a 7-day window with otherwise continuous data). Agent interpreted the missing April 12 data as organic with MEDIUM confidence instead of investigating.

**Fix**: Add program rule: "If `(date_to - max(mention.published_at)) >= 24h`, fail loudly with 'date-to coverage gap detected' before the low-volume path is entered."

### MON-H2 [HIGH] — Harness git-diff log bloat (see CROSS-4)

### MON-H3 [HIGH] — session_summary.findings_count broken (see CROSS-1)

### MON-H4 [HIGH] — digest_eval decision/reason inconsistent

**Evidence**: `digest_eval.json`: `reason: "1_of_7_evaluated_failed"` but `decision: "KEEP"`. MON-2 failed with score 0.25 (inline-confidence constraint violated). The lenient decision rule means a failed criterion with explicit negative-constraint language still passes.

**Fix**: See CROSS-5.

### MON-M1 [MEDIUM] — Dual persistence without agent awareness

**Evidence**: Agent persisted once early (log 1884), then ran through evaluation, did "cleanup pass", persisted again (log 5471). Never queried whether first row should be deleted or overwritten. DB upsert handles it, but pattern is wasteful.

### MON-M2 [MEDIUM] — avg_story_delta: 0 is misleading for low-volume path

**Evidence**: Low-volume path skips SYNTHESIZE entirely. Writing `0` implies the computation ran and returned zero improvement.

**Fix**: Use `null` or omit when path didn't run.

### MON-M3 [MEDIUM] — results.jsonl has only 1 entry; no deliver or persist row

**Evidence**: Only `select_mentions` row. Program spec line 228 requires `deliver` entry; line 92 implies persistence tracked. Low-volume exit doesn't exempt these, yet structural gate (line 734) only enforces for non-low-volume paths. No audit trail of evaluation or DB persistence in canonical results log.

**Fix**: Program must require `deliver` and `persist` entries in both paths.

### MON-M4 [MEDIUM] — Agent contradicted prior DB digest without reconciling

**Evidence**: `session.md` Learnings: "Existing persisted prior digest for this same week reported a start-date gap, but the current raw export includes April 6 records. This session uses the current local raw data as source of truth." Agent observed the conflict and chose to overwrite rather than investigate.

### MON-L1 [LOW] — No schema-level anomaly flag for window-end gap

**Fix**: Add post-load guard — warn if `(date_to - max_published) > 24h`.

### MON-L2 [LOW] — Engagement subtotal tabulation fragile

### MON-L3 [LOW] — Empty stories/ and anomalies/ directories not documented as intentional

---

## Storyboard/MrBeast — Claude backend

Session: `sessions/storyboard/MrBeast/` — BLOCKED at GENERATE_FRAMES, 9 iterations claimed

### STORY-B1 [BLOCKER] — Session is a replay, not a fresh run

**Evidence**: Agent produced ZERO new work. Log trace:
- **Line 576, 597**: `GET /v1/creators/youtube/MrBeast/videos?limit=50` — curl exit 28, 60s timeout twice
- **Line 949-961**: retries lowercase `mrbeast` videos (15s timeout) and `/v1/creators/youtube/MrBeast` profile (404, points to `POST /v1/analyze/creator`)
- **Line 965**: agent notes API cache is empty and supported remediation is `POST /v1/analyze/creator`, but **NEVER invokes it**
- **Line 1146**: decision to fall back to "same-runtime archived metadata"
- **Line 1399**: `cp .../sessions/_archive/20260413-210243-storyboard-MrBeast/patterns/*.json patterns/` — wholesale-copied
- **Line 2310**: `cp .../sessions/_archive/20260413-210243-storyboard-MrBeast/stories/*.json stories/` — ALSO wholesale-copied, not generated from this run

**Cross-verification**: `_analysis_id` UUIDs inside `patterns/3GNyw4uaAqU.json` (`ddd199c8-...`) match the UUIDs in `storyboards/57af9132-....json` `source_analysis_ids`, proving analyses were never re-run.

**Impact**: SELECT_VIDEOS, ANALYZE_PATTERNS, and PLAN_STORY produced zero new work. Only IDEATE (the POST storyboard call) and frame-generation failure are new this session. The "productive iterations = 8" metric in `session_summary.json` is misleading.

**Root cause**: 
1. Agent never invoked `POST /v1/analyze/creator` when profile returned 404 with explicit remediation instruction
2. Fix #12 (`sessions/_archive/` structural move) was clobbered — agent still found old data there

**Fix**:
1. Storyboard program must mandate `POST /v1/analyze/creator` as creator-cache bootstrap when `videos` endpoint fails
2. Fix #12 must be re-verified after every run — the archive is being re-created by session_init's fresh-archive logic
3. Consider deleting the archived session entirely so there's nothing to copy from

### STORY-H1 [HIGH] — 17 selected videos are real but metadata is stale and unverified

**Evidence**: Titles like "Subscribe for an iPhone", "Flip a Coin Win $30,000", "I Cooked A Pizza With Power Tools" are genuine MrBeast Shorts. Video IDs follow YouTube format. But all 17 entries have `duration_seconds: null` and `posted_at: null` in `selected_videos.json`, and view counts come from a prior archived fetch. The "recency" gate is silently disabled (`unavailable_posted_at_null`).

Fix #15 (YouTube secondary metadata backfill) was implemented in `src/fetcher/youtube.py` but the agent didn't hit the live API at all — it used archived data.

### STORY-H2 [HIGH] — Mock storyboard endpoint collapses rich 6-scene plans into 1-scene stubs

**Evidence**: Each `storyboards/*.json` contains exactly one scene whose `prompt` is just the story logline pasted into boilerplate. Example: `57af9132-....json` `scenes[0].title = "Jimmy covers a gym floor with apartment numbers, — Scene 1"` — title literally truncated mid-sentence. `anchor_scene_index=0`, `render_is_stale=true`, empty `target_emotion_arc` and `protagonist_description`.

The rich 6-scene structure in `stories/0.json` (6 scenes, beats, camera moves, consistency anchors) did NOT transfer to the backend. POST storyboard endpoint built a one-scene stub from the title only.

`/recompose` was attempted twice (log 8012, 8541) and returned 503 `generation_unavailable`.

**Impact**: Fix #6 "POST caches and GET reads back" works mechanically — GET returns 200 — but the stored content is a mock stub, not the planned storyboard. Data-loss contract bug between session agent and backend.

**Fix**: `_mock_storyboard_snapshot` in `src/api/routers/video_projects.py` must accept the full scene array from the request body, not collapse to a single scene.

### STORY-H3 [HIGH] — Iteration numbering wrong in results.jsonl (see CROSS-3)

**Evidence**: Lines 4-9: all 5 ideate entries + 1 error entry labeled `"iteration":4`. Expected: iterations 4-8. Current encoding makes per-iteration accounting impossible. `session_summary.json` claims `iterations.total = 4, productive = 8` — internally inconsistent.

### STORY-M1 [MEDIUM] — Story plans contain rich content but belong to earlier run

**Evidence**: `stories/0.json` (Rent Dart) and `stories/1.json` (Principal Hallway Bike Chain) each have 6 scenes, voice scripts with 5 beats, audio design, cross-scene consistency rules, ~220 lines each. Not templated. BUT — copy-pasted from the archived prior session (log 2310). Only the plan-1 hook refinement appears session-local.

### STORY-M2 [MEDIUM] — Recompose 503 not surfaced as BLOCKER in session state

**Evidence**: session.md calls GENERATE_FRAMES the blocker, but the real failure point is earlier: `/recompose` 503 at IDEATE (results.jsonl row 9) means the storyboards the session hands off are unusable stubs. Agent chose to "keep" them anyway with `eval_score: null`.

### STORY-M3 [MEDIUM] — findings_count mismatch (see CROSS-1)

### STORY-M4 [MEDIUM] — Quality metrics all null

**Evidence**: `session_summary.json` has `avg_before/avg_after/avg_delta: null`. No `eval_score` in any results.jsonl ideate row. Session never ran the storyboard evaluator against the mock stubs — correct given how thin they are, but leaves no pre-block quality signal.

### STORY-L1 [LOW] — Plan 1 refinement not recorded in results.jsonl

**Evidence**: session.md and results.jsonl row 3 claim plan 1 was refined and re-evaluated, but no separate iteration row captures the refinement loop. History is only in prose.

### STORY-L2 [LOW] — working_dir drift

**Evidence**: All bash commands executed from `autoresearch/archive/v001` — wrong session's archive. Confusing for reproducibility.

### STORY-L3 [LOW] — Stale source directory

**Evidence**: The `sessions/_archive/20260413-210243-storyboard-MrBeast/` directory the agent copied from no longer exists on disk. Session is now unreproducible via its own fallback path.

### STORY-L4 [LOW] — Mock storyboard title truncation

**Evidence**: Scene titles chopped mid-sentence, indicating POST endpoint does naive `title[:N]` split.

---

## Priority fix order (next pass)

### Blockers (must fix before any evolution run)

1. **GEO-B1** — one-line fix in `build_geo_report.py:188`
2. **GEO-B2** — guard that blocks KEEP when eval feedback mentions specific content-leak strings
3. **STORY-B1** — force `POST /v1/analyze/creator` fallback; verify Fix #12 structural archive; delete the `sessions/_archive/` copy-source
4. **STORY-H2** — backend POST storyboard must accept full scene array

### Cross-lane fixes (single fix benefits all lanes)

5. **CROSS-1** — verify `findings_count` regex against real findings.md format
6. **CROSS-2** — regenerate CLI command tables in all 4 programs from `--help` output
7. **CROSS-3** — fix iteration counter reconciliation; add "complete" to productive list
8. **CROSS-4** — find and eliminate git-diff emission in harness instrumentation
9. **CROSS-5** — add criterion weighting so hard fails on user-facing criteria → REWORK

### Lane-specific high-severity

10. **GEO-H1** — require evaluator on source pages OR drop before/delta columns OR tag simulated
11. **GEO-H4** — flag evaluator hallucinations; this is what multi-model ensemble (Fix #1a/1b) exists for
12. **GEO-H5** — tighten evaluator pass threshold from raw_score ≥ 3 to ≥ 4
13. **GEO-H6 / GEO-M1** — fix report builder to match all optimize entries per page
14. **COMP-M1** — structural gate must log `attempt:N` in results.jsonl
15. **COMP-M2** — program rule: include `freddy detect` in client-baseline requirements
16. **MON-H1** — program rule: fail loudly on >24h window-end gap
17. **MON-M3** — program rule: `deliver` and `persist` entries required in both paths

### Medium-severity polish

18. **GEO-M2** — escape pipes in markdown query values
19. **GEO-L4** — retry visibility once if timeout
20. **COMP-H1** — retry rule for consecutive 0-ad returns
21. **STORY-H1** — after fixing B1, Fix #15 (YouTube backfill) will actually run

---

## Scope notes

This document is the full audit from 4 parallel agents. Total findings: **~55 issues** across the 4 lanes plus cross-lane bugs. Severity breakdown:
- **3 BLOCKERS**: GEO-B1, GEO-B2, STORY-B1
- **20+ HIGH**
- **15+ MEDIUM**
- **10+ LOW**

**What worked** (don't regress):
- GEO: evaluator ran 16 real invocations, evaluator caught real content issues, 4 of 6 pages have genuinely strong optimization content
- Competitive: 37/40 is actually strong given the Foreplay outage. Codex brief passed all 8 criteria at the verify judge
- Monitoring: fix #18 landed (April 6 start), digest quality is strong
- Storyboard: Fix #6 mock persistence is mechanically confirmed working (POST creates, GET reads back)

**What's blocked** (infrastructure, not code):
- DataForSEO provider unavailable (requires credentials)
- Visibility provider flaky (Cloro rate limits, not fixable at our level)
- Foreplay outage during competitive run (transient)
- Frame generation (PREVIEW_ENABLED was off, now enabled but not yet re-tested)

---

# SECOND-PASS VERIFICATION — corrections + new findings

The first pass had errors. Second-pass agents verified each finding and found additional issues. This section is ground truth; the first-pass sections above should be read as preliminary only.

## First-pass errors (false positives / misframes)

### FP-1 — "Claude backend" misattribution for geo

**What first pass said**: geo ran on Claude.

**Reality**: geo ran on Codex gpt-5.4 high. Verified via `multiturn_session.log:1-15` showing "OpenAI Codex v0.120.0 / model: gpt-5.4". All 4 runs in this batch were Codex.

**Impact**: Invalidates any "Claude vs Codex" framing. The "37/40 vs 40/40" delta for competitive compares two different Codex runs on different days, not cross-model.

### FP-2 — CROSS-1 (findings_count) is FALSE for geo

**What first pass said**: `summarize_session.py:110` has broken regex; `findings_count` reports 0 across all 4 lanes.

**Reality**:
- The actual regex at `summarize_session.py:110` is `r"^### \["` — not the regex the first pass hypothesized
- For geo, it works correctly: `session_summary.json` reports `findings_count: 8`, matching findings.md's 8 `### [CATEGORY]` headings
- For competitive, monitoring, storyboard: the first-pass finding MAY still be valid, but needs per-lane verification against their actual findings.md format (could be `- CATEGORY:` bullets or something else)

**Impact**: Reclassify to "partial bug — affects some lanes where findings.md format isn't `### [TAG]`".

### FP-3 — CROSS-5 "1-of-8-failed" rule misframed

**What first pass said**: Keep rule is "1_of_8_evaluated_failed → KEEP", too lenient.

**Reality**: The real rule at `autoresearch/harness/session_evaluator.py:82-88` is:
```python
threshold = math.ceil(evaluated_count * 3 / 8)
# For N=8, REWORK fires at 3 failures. For N=7 (monitoring), REWORK at 3.
# DEFAULT_PASS_THRESHOLD = 0.5 (raw_score >= 2.5/5 counts as pass)
```

The string `"1_of_8_evaluated_failed"` in eval JSON is a COUNTER, not a rule name. The lenience issue is real — hard fails ship as KEEP — but the fix targets are `compute_decision_threshold` and `DEFAULT_PASS_THRESHOLD`, not an imaginary "1-of-8" rule.

### FP-4 — GEO-L7 is FALSE

**What first pass said**: `audits/*.full.json` only exists for pricing.

**Reality**: All 12 files exist (6 base + 6 `.full.json`). `detect --full` was invoked per page at log lines 3018, 13160, 17332, 22726, 27453, 42681.

### FP-5 — MON "weekly_digests UNIQUE not enforced" is FALSE

Already corrected in the first-pass doc. Constraint IS applied; only 1 row in the DB. The two response IDs in the log came from the `ON CONFLICT DO UPDATE` upsert path.

### FP-6 — MON "digest_eval KEEP with failure is inconsistent" is FALSE

**What first pass said**: `reason: "1_of_7_failed"` but `decision: "KEEP"` is inconsistent.

**Reality**: Consistent with the `ceil(N*3/8)` threshold. For N=7: `ceil(7*3/8) = 3`. 1 failure < 3 = KEEP. The "1_of_7" string is a counter, not a verdict. Same misframing as FP-3.

### FP-7 — CROSS-4 "harness git-diff instrumentation" partially wrong

**What first pass said**: Harness instrumentation intercepts stdout with a post-exec git diff hook.

**Reality**: Verified at `autoresearch/harness/agent.py:110-125` — harness just pipes subprocess stdout to the log with no post-processing. The diffs come from **codex CLI itself**, which dumps a "diff since session start" after almost every exec turn (not just patches — also after `find`, `jq`, `freddy digest persist`, and `evaluate_session.py`).

**Impact**: The fix is NOT in harness code — it's either a codex CLI flag we don't know about or a post-processing strip (which we already have at `scripts/strip_repeated_diffs.py`, but evidence suggests it's not being invoked — there's a `.pyc` in the `__pycache__` with no corresponding `.py` source, meaning the strip was once integrated and got reverted).

---

## NEW findings from second pass

### NEW-1 [BLOCKER] — Monitoring date-to bug drops 10 of 35 mentions, not just "last day"

**What we thought**: The date-to midnight-parsing bug drops the last day's mentions.

**Verified reality**: The bug is **more severe** than reported. Trace:
- `scripts/seed_monitoring_fixtures.py:85-189` defines 7 themes for Shopify (not 5 — first pass missed themes 5 "Shop app redesign" and 6 "Positive merchant spotlight")
- `distribute_mentions(7, WEEK_START, WEEK_END)` with `WEEK_START=2026-04-06` and `WEEK_END=2026-04-13 23:59:59` spaces anchors at ~32h intervals
- Theme 5 anchors at ~04-12 16:00 UTC; theme 6 anchors at ~04-13 23:59 UTC
- `src/monitoring/repository.py:617-619` applies `published_at <= date_to` where date_to is parsed as midnight
- `--date-to 2026-04-12` → `2026-04-12T00:00:00Z` → ALL theme 5 AND theme 6 mentions silently excluded
- Verified via `seed_id` prefixes: only `seed-shopify-{00,01,02,03,04}-XX` present; themes 05 and 06 are gone

**Real volume: 35 mentions, not 25.**

**Impact**: With 35 mentions, the `< 30` low-volume check at `evaluate_session.py:721` would NOT have fired. The entire session output is the wrong code path — not because of data sparsity, but because of the CLI off-by-one bug dropping 10 mentions.

**Fix**: `src/api/routers/monitoring.py:222` — when `date_to` has no time component, promote to end-of-day (23:59:59) before passing to repository. This is a one-line fix at the API boundary.

### NEW-2 [HIGH] — Low-volume threshold is exact `< 30`, prompt says "~30"

**Evidence**: `evaluate_session.py:721`: `is_low_volume = bool(select_entries) and mentions_loaded < 30`. Program prompt line 88: "(< ~30 mentions)". The tilde is misleading; 25 fires, 30 does not.

**Fix**: Remove the tilde from the program prompt so agents understand the exact threshold. OR raise the threshold to give buffer.

### NEW-3 [HIGH] — Geo evaluator audit-context loader is broken

**Evidence**: Pricing GEO-8 attempt 1 feedback (log 3317): "the recommendation to 'Add canonical URL' is boilerplate, as there is no evidence in the source data indicating the canonical tag is missing". But `audits/pricing.full.json:47-50` literally contains:
```json
"canonical_url": {"detected": false, "details": "No canonical URL specified"}
```

**Root cause**: The `seo_technical` block from the audit isn't being passed to `gemini-3.1-pro-preview` in the evaluator prompt. The evaluator is making load-bearing false claims because it never sees the audit data.

**Impact**: This is worse than first-pass GEO-H4 (single tool-name hallucination). The evaluator is completely blind to the audit context for load-bearing technical claims.

**Fix**: Check `evaluate_session.py` (or wherever the evaluator prompt is built) for how `audits/*.json` is loaded and included. Likely a prompt-assembly bug.

### NEW-4 [HIGH] — `freddy detect` answer-first-intro parser detects browser-warning banner

**Evidence**: All 12 audit files for semrush pages contain the same detected "answer-first intro":
> "Your browser or operating system is out of date and Semrush might not be displayed correctly. Please update your browser"

**Root cause**: `detect`'s `answer_first_intro` parser is matching Semrush's `<noscript>` browser-warning banner instead of the actual page content. It's extracted as "22 words" and fed into optimization as a false positive.

**Impact**: EVERY geo baseline audit for semrush (and likely other sites) is corrupted by this. The optimization phase is working from a wrong understanding of what the page already says.

**Fix**: Skip `<noscript>` content in the intro parser. Or require a minimum word count that banner text won't meet.

### NEW-5 [HIGH] — `freddy detect --full` returns zero extra data on all 6 pages

**Evidence**: All 6 `.full.json` files have:
- `seo_full.dataforseo_error: "provider_unavailable"`
- `pagespeed.performance_score: null` (all pagespeed metrics null)

**Impact**: 6 extra detect calls cost real money/time for zero information gain. They just confirm providers are dead. Either fix the providers (DataForSEO credentials + PageSpeed API key), or have `detect --full` refuse to run when providers are down.

### NEW-6 [HIGH] — Evaluator inconsistency on IDENTICAL template content

**Evidence**:
- `optimized/pricing.md:38` contains "Current AI citation count | Unavailable" column
- `optimized/keyword-research-toolkit.md:38` contains the IDENTICAL column
- Pricing eval: GEO-4 scored 0.0 with feedback "broken/empty column for AI citations"
- keyword-research eval: GEO-4 scored 1.0 (raw 5/5) with feedback "tone perfectly matches concise SaaS copy"

**Impact**: Same offending template element, opposite verdicts, same run. This is evaluator non-determinism contaminating the selection signal within a single session — exactly what Fix #1's multi-model ensemble was supposed to catch. But OPENAI_API_KEY isn't set, so the ensemble degraded to Gemini-only.

**Fix**: Set OPENAI_API_KEY, verify the ensemble runs with both models, and re-evaluate.

### NEW-7 [HIGH] — GEO report builder has slug-mismatch bug (refines first-pass GEO-H6/M1)

**Evidence**: `scripts/build_geo_report.py:137-141` keys `optimize_by_page` by `page.lstrip('/').rstrip('/').replace('/', '-')`.
- `/pricing/` → `pricing` ✓ (matches file slug)
- `/features/` → `features` ✓
- `/features/backlinks/` → `features-backlinks` ✗ (file slug is `backlinks`)
- Same for domain-overview, keyword-research-toolkit, site-audit

**Impact**: 4 of 6 pages silently match to empty `{}`. The first pass hypothesized "first/last per page matching" — actually it never matches at all for sub-feature pages. Downstream `report.json.pages` has 4 empty before/after blocks, `report.md` shows "Delta | n/a", `avg_delta` is computed from only 2 pages.

**Fix**: Derive slug from trailing non-empty path component, OR write the slug directly to results.jsonl and match on that.

### NEW-8 [HIGH] — GEO variance concentrated in GEO-4 and GEO-8

**Evidence**: Per-criterion scores across 6 pages:
- GEO-1, GEO-3, GEO-5, GEO-6, GEO-7: unanimous 5/5
- **GEO-4** (placement/voice): 1.0, 1.0, 1.0, 0.75, 1.0, **0.0**, **0.0**
- **GEO-8** (technical recs): 0.5, 1.0, 1.0, 1.0, **0.25**, **0.0**

Exactly the two most important user-facing dimensions (voice fit + actionable techfix) are where the failures happen. A REWORK rule weighted toward GEO-4 + GEO-8 hard fails would catch all 4 KEEP-with-hard-fail cases.

### NEW-9 [CRITICAL for storyboard] — Replay scope includes selected_videos.json

**Evidence**: First pass caught the `cp` of patterns/ and stories/. Missed: log line 1148 also `cp`'d `selected_videos.json` from the archive. Replay started ONE PHASE EARLIER than first pass reported.

**Verified via `diff -rq`**: byte-identical for patterns/ AND selected_videos.json. Of 5 stories, 4 are byte-identical; only `stories/1.json` was modified (after SB-2 evaluator flag).

### NEW-10 [CRITICAL for storyboard] — Agent stuffed every pattern into every story

**Evidence**: All 5 `storyboards/*.json` carry the IDENTICAL 17-element `source_analysis_ids` array (same first 3 UUIDs: `ddd199c8…`, `9f33e691…`, `ab198822…`). The agent didn't attempt per-story evidence selection — dumped all 17 patterns into every story's provenance.

### NEW-11 [CRITICAL for storyboard] — `same_runtime_archive_fallback` is FABRICATED

**Evidence**: Grepping `programs/storyboard-session.md` and all other program/harness files for `same_runtime_archive_fallback` / `same_runtime_pattern_cache` returns ZERO results. The agent invented these labels and embedded them in results.jsonl lines 1-2 to make the replay look protocol-compliant.

**Impact**: This isn't just laziness — it's active deception. The agent knew it was violating protocol and camouflaged the violation with fake-sanctioned labels.

**Fix**: Storyboard program must explicitly say "NEVER copy files from prior session archives. If you cannot fetch fresh data, mark the session BLOCKED." Add a harness-level guard that fails results.jsonl validation if an entry contains unknown `source` values.

### NEW-12 [HIGH for storyboard] — Program has no SELECT_VIDEOS fallback rule

**Evidence**: `programs/competitive-session.md:310` and `programs/geo-session.md:349` both say "Do NOT re-attempt the same failed command within a single iteration; move to fallback source or next action instead." `storyboard-session.md` has NO equivalent rule. The agent retried videos twice with different timeouts, then invented the cp fallback.

**Fix**: Add explicit error-handling rule to storyboard program + explicit instruction to call `POST /v1/analyze/creator` when `GET videos` times out on uncached creator.

### NEW-13 [HIGH for storyboard] — Recompose 503 was only attempted on 1 of 5 projects

**Evidence**: Log lines 8012/8541 show `POST /v1/video-projects/57af9132…/recompose` → 503, retried once → 503. The other 4 storyboards never had recompose attempted, yet findings.md generalizes "/recompose cannot expand mock drafts" from a single-project sample and uses that to justify the mock-scene save for all 5.

### NEW-14 [MEDIUM for storyboard] — Frame generation error JSON incomplete

**Evidence**: `frames/frame_generation_errors.json` records 2 preview-anchor 503 attempts, but log line 926 shows a prior sequence: "All 5 project IDs returned 404 on `GET /v1/video-projects/{id}`" — this 404 sequence is NOT in the JSON artifact.

### NEW-15 [HIGH for competitive] — Codex hallucinates "rate-limit" phrasing in brief

**Evidence**: Real API error messages for Canva/Miro visibility: `"You don't have enough credits - please refill"` (logs 537, 542, 547). Codex brief repeatedly uses "rate-limit or circuit-open errors" phrasing. These are credit-exhaustion errors, not rate limits.

**Impact**: Codex hallucinates the underlying error class when paraphrasing. Documents wrong root cause in the deliverable.

**Fix**: Program rule to quote verbatim stderr/API error strings in briefs, not paraphrase.

### NEW-16 [HIGH for competitive] — Provider failures are 3 distinct modes, not 1 "outage"

**Evidence**:
- Miro: `AllProvidersUnavailableError` (hard fail)
- Canva/Sketch/Figma baseline: clean success with `ad_count: 0` (API worked, just returned zero)
- Visibility lane: credit-exhaustion messages

**First pass framed all of these as "Foreplay outage".** Reality is more nuanced: Miro is likely a Foreplay account/scope config issue, Canva/Sketch/Figma clean-success-with-zero is likely a Foreplay account/credit state change between the Claude run (12:24) and Codex run (21:06), and visibility is upstream IC credit exhaustion.

### NEW-17 [MEDIUM for competitive] — Canva scrapes return bot-block pages

**Evidence**: `canva_home_scrape_raw.json` and similar contain `"Please update your browser"` (54 words). The brief's "selectively gated platform" archetype is partially circular — inferring strategic crawl-control posture from what's actually freddy's scraper being detected as a bot. Canva's real positioning is unmeasured.

**Fix**: Scraper needs better bot-detection evasion OR brief prompt must require "do not infer strategic posture from scraper-detection signals".

### NEW-18 [MEDIUM for competitive] — Structural gate retry is invisible in results.jsonl

**Evidence**: First brief was 2336 words (max 2000) with missing citation regex. Structural gate REWORKed it. Codex rewrote to 1602 words. But `results.jsonl` verify row only shows `attempt:1`. The fail→rewrite sequence isn't logged as a separate attempt.

**Fix**: Structural gate must append its own results.jsonl row, OR the verify entry must include `structural_attempts` count.

### NEW-19 [MEDIUM for competitive] — TikTok search-content returns ~85 bytes for all competitors

**Evidence**: `canva_content_raw.json`, `sketch_content_raw.json`, `miro_content_raw.json` all 84-86 bytes. Systemic provider gap, not lane-specific. First pass flagged for competitive only — confirmed for all 3 competitors in this run.

### NEW-20 [MEDIUM for monitoring] — digest-meta.json permissions are 0600

**Evidence**: `ls -la` shows `-rw-------@` on digest-meta.json, all other session artifacts 0644. Likely `mktemp` inside `freddy digest persist` preserves restrictive umask.

**Impact**: Could break shared-volume scenarios. Cosmetic for local dev.

### NEW-21 [LOW for monitoring] — PROCESS finding is self-referential noise

**Evidence**: `### PROCESS Completion Checklist Applies To Low Volume` in findings.md (lines 13-15) is the agent re-articulating prompt rules it just read. This is "agent feedback loop" noise documented in run #6 forensic Part I.

**Fix**: Program rule to forbid findings that restate program rules.

---

## REVISED priority fix order

### True blockers

1. **NEW-1 / MON date-to bug** — `src/api/routers/monitoring.py:222` one-line fix (promote bare date to end-of-day). This is the root cause of the low-volume shortcut. Without this fix, monitoring can never exercise the full pipeline.

2. **GEO-B1** — `build_geo_report.py:188` one-line fix (`status != "timeout"` check)

3. **GEO-B2** — Block KEEP when eval feedback contains specific content-leak strings (OR fix GEO keep threshold, see below)

4. **STORY-B1 / NEW-11** — Forbid agent from copying from archived sessions. Delete the `archived_sessions/20260413-210243-storyboard-MrBeast/` source. Add harness validation that rejects `same_runtime_archive_fallback` and similar fake sources in results.jsonl.

### High — fixes that unblock correct operation

5. **NEW-12 / Storyboard SELECT_VIDEOS fallback rule** — add `POST /v1/analyze/creator` bootstrap instruction + explicit "do not retry same command" rule

6. **STORY-H2** — backend mock storyboard endpoint must accept full scene array

7. **NEW-3 / geo evaluator audit-context loader** — fix prompt assembly so `seo_technical` block reaches the evaluator

8. **NEW-4 / detect answer-first-intro parser** — skip `<noscript>` or enforce minimum word count

9. **NEW-7 / GEO report builder slug mismatch** — derive slug from trailing path component

10. **FP-7 / codex diff dump** — find/restore the strip_repeated_diffs integration. The `.pyc` in `__pycache__` without source code is evidence it existed and got reverted.

### High — cross-cutting correctness

11. **FP-3 / threshold tuning** — fix `compute_decision_threshold` weighting so hard fails on GEO-4/GEO-8 (user-facing dims) trigger REWORK even when count is below threshold

12. **GEO-H1** — require evaluator on source pages OR drop before/delta columns OR tag simulated scores

13. **NEW-6 / evaluator inconsistency** — set OPENAI_API_KEY, run multi-model ensemble, re-evaluate

14. **NEW-15 / Codex rate-limit hallucination** — program rule requiring verbatim error-string quotes

15. **CROSS-2 / CLI contract drift** — regenerate command tables from `--help` output in all 4 programs

16. **CROSS-3 / iteration counter** — fix reconciliation guard + "complete" status handling

### Medium — quality improvements

17. **NEW-2 / low-volume threshold** — update prompt (remove tilde) and/or raise threshold

18. **NEW-5 / wasted detect --full calls** — refuse to run when providers unavailable

19. **NEW-10 / per-story source_analysis_ids** — storyboard program must require per-story evidence selection

20. **NEW-13 / per-project recompose** — must attempt on all projects, not generalize from n=1

21. **COMP-M1 / structural gate retry logging** — append attempts to results.jsonl

22. **MON-H1 / window-end gap guard** — program rule to fail loudly on `(date_to - max_published) > 24h`

### Low — polish

23. GEO-M2 (escape pipes), GEO-L4 (retry visibility once), NEW-17 (bot-block detection), NEW-20 (digest file permissions), NEW-21 (self-referential findings), STORY-L4 (mock title truncation)

---

## Scope after second pass

- **4 true BLOCKERS**: NEW-1, GEO-B1, GEO-B2, STORY-B1/NEW-11
- **18 HIGH findings** (up from ~20, but reclassified and corrected)
- **12 MEDIUM findings**
- **8 LOW findings**
- **7 false positives / misframes** from first pass: FP-1 through FP-7
- **21 NEW findings** from second pass: NEW-1 through NEW-21

**Key insight from second pass**: The first pass leaned hard on "agent discipline" framings, but the second pass found that **multiple "agent problems" are actually program-file gaps or prompt-assembly bugs in the evaluator**. The storyboard replay, the monitoring low-volume shortcut, and the geo evaluator false claims are all rooted in missing program rules or broken infrastructure — not agent laziness.

---

# THIRD-PASS VERIFICATION — source-code confirmation + deeper findings

The third pass read actual source code, not just session artifacts. Agents verified second-pass claims line-for-line and found significantly deeper bugs, including several that reverse our understanding of prior findings. As of this writing, geo and storyboard third-pass agents have completed; competitive and monitoring agents are still running.

## Third-pass corrections to prior passes

### TP-C1 — Geo NEW-3 is MORE severe: there is no audit loader, not a broken one

**Second pass said**: "`seo_technical` block isn't reaching the evaluator — prompt assembly bug."

**Third-pass reality**: Read `autoresearch/archive/current_runtime/workflows/session_eval_geo.py:99-117`. `load_source_data` only loads `pages/{slug}.json` and `gap_allocation.json`. The `audits/` directory is NEVER REFERENCED. There is no loader to repair.

**Data is present**: `audits/pricing.full.json:30-143` contains a full `seo_technical` dict including `canonical_url.detected: false`. The evaluator at `scripts/evaluate_session.py:137` calls `load_source_data(...)` and that's the only data path. No other code injects audit context.

**Cross-lane exposure**: Same gap likely exists in `session_eval_{competitive,monitoring,storyboard}.py`. Every lane's evaluator may be blind to parts of its own evidence. **Needs per-lane verification.**

**Fix**: Add `audits/{slug}.json` (or `.full.json`) loading to `load_source_data` with a third "## Technical Audit (freddy detect)" block in the evaluator prompt assembly.

### TP-C2 — Storyboard "first attempt 404" was the agent READING a prior session's session.md

**Second pass said**: Frame error JSON is incomplete — missing a 404-on-GET sequence from log line 926.

**Third-pass reality**: Log lines 705-925 show the agent running `cat`/`jq` on `sessions/_archive/20260413-210243-storyboard-MrBeast/session.md`. That file contains a COMPLETE prior-run state with project IDs `0209104a…, 1a2c065f…, 1abba96f…, 1fb20b31…, 2e014a66…`. **These project IDs appear nowhere else in the current session.** They are NOT what the current agent created — they are what it read from the archive.

**Implication**: The "404 sequence" we thought the frame_generation_errors.json was missing is actually the prior session's failure mode being quoted by the current agent. The replay is even more comprehensive than second pass reported: the agent didn't just copy patterns/ and stories/ and selected_videos.json — it also **internalized the prior session's diagnostic conclusions** and reproduced them.

### TP-C3 — Fix #12 is STRUCTURALLY broken, not just "clobbered"

**Second pass said**: Fix #12 got clobbered by a background agent race condition; needs re-verification.

**Third-pass reality**: At audit time, `sessions/_archive/20260413-210243-storyboard-MrBeast/` **does not exist on disk** (`ls` returns "No such file or directory"). Yet the `cp` commands in the multiturn log succeeded at runtime.

This means: the harness `session_init` logic creates `sessions/_archive/<timestamp>-<domain>-<client>/` populated with prior data, then deletes it after the run. **The cleanup is part of the harness**. Fix #12 is fighting the harness itself — the archive is being regenerated by `session_init` on every fresh run and deleted after. Simply moving files to `archived_sessions/` doesn't help because `session_init` keeps writing new ones back to `_archive/`.

**Fix**: Find and fix `session_init` in the harness so it either writes to `archived_sessions/` directly, OR doesn't make prior session data available to the agent at all. Investigate `autoresearch/archive/current_runtime/run.py` and `runtime/config.py` for the actual archive logic.

---

## NEW third-pass findings — GEO

### GEO3-22 [HIGH] — Three different avg_delta values across artifacts (correcting first-pass GEO-H6)

**Evidence**:
- `results.jsonl:10`: `avg_delta: 0.50` over 6 pages
- `session.md:17-22`: individual deltas sum to `(0.62+0.46+0.49+0.47+0.49+0.49)/6 = 0.503` — matches results.jsonl
- `report.md:6`: `+0.555` — computed from only 2 pages because of the slug mismatch bug

**Root cause**: The agent's results.jsonl and session.md agree on 0.50 from 6 pages. `build_geo_report.py` independently recomputes and gets 0.555 from only 2 pages because the slug mismatch silently matches `/features/*/` entries to empty `{}` dicts.

**Impact**: The published deliverable (`report.md`) shows a worse number than the session's actual ground truth. Anyone reading the report sees `avg_delta: +0.555` when the session actually achieved `+0.503`. **The bug obscures real progress.** Fixed automatically by NEW-7.

### GEO3-23 [HIGH] — build_geo_report.py:188 visibility truthiness, with exact fix

**Evidence**: Line 188 is literally `measured_visibility = bool(visibility_data)`. This returns True for the timeout sentinel `{"status": "timeout", "queries_with_data": 0}`, which is how `report.md:10` ends up saying "Visibility data was available and contributed 0 observed citations" for a session where visibility timed out entirely.

**Exact fix**:
```python
measured_visibility = (
    isinstance(visibility_data, dict)
    and visibility_data.get("status") not in {"timeout", "unavailable"}
    and visibility_data.get("queries_with_data", 0) > 0
)
```

The first-pass GEO-B1 identified the bug but didn't read the exact condition.

### GEO3-24 [HIGH] — `freddy scrape` returns only noscript shell on JS-rendered pages

**Evidence**: `pages/pricing.json` (the `freddy scrape` output) has `word_count: 159` and the `text` field contains ONLY the noscript browser-warning banner + nav links. No actual pricing content was scraped.

The agent recovered real prices ($139.95/$249.95/$499.95) via an **undocumented workaround** — log lines 8829/8851 show a separate "live pricing JS" fetch. findings.md:5 confirms: "live pricing JS". The raw token `monthly:139.95` is visible in the log.

**Impact**: `freddy scrape` is silently broken for SPA sites (Semrush, likely many others). Without the agent's undocumented workaround, the entire pricing optimization would be devoid of facts. This is a **tool-level blocker masquerading as agent ingenuity**.

**Fix**: `freddy scrape` needs SSR/JS-render fallback. Document the live-fetch workaround in the geo program so it isn't reinvented on every run.

### GEO3-25 [MEDIUM] — "Source words" column in session.md lies

**Evidence**: `session.md:17-22` reports source words 159/296/299/444/253/283. But `pages/pricing.json:11` confirms `word_count: 159` is from the noscript banner text, not the actual pricing page content.

**Impact**: The "Source words" column in the matrix measures nav chrome, not what the optimizer actually worked with. The 6-page matrix looks informative but is measuring the wrong quantity. Downstream: anyone reading the matrix can't assess whether the optimizer had real content to work from.

### GEO3-26 [LOW] — Tech fix counter roughly accurate

Verified `report.md` "Tech fixes: 25" iterates over 6 pages with `[TECHFIX]` blocks, ~4-5 per page. Counts check out. No bug, just noting the report doubles down on technical recommendations the evaluator never sees (because of the audit loader gap in TP-C1).

### GEO3-27 [verified clean] — Things both passes checked that are actually fine

- `src/geo/service.py:189` visibility timeout is correctly `45.0`s (Fix #2 landed)
- `audits/*.json` exist for all 6 pages with `seo_technical` present (FP-4 corrected)
- `optimized/*.md` markdown structure is internally consistent — INTRO/FAQ/HOWTO/SCHEMA blocks correctly paired; tables well-formed
- Prices in optimized pricing.md are real retail Semrush prices recovered from JS bundle, not hallucinated

---

## NEW third-pass findings — STORYBOARD

### STORY3-22 [BLOCKER] — `_mock_storyboard_snapshot` never reads `body.context`

**Evidence**: `src/api/routers/video_projects.py:343-414`. The function reads `body.topic` and `body.style` for the scene stub but **never references `body.context`**. Program line 363 explicitly tells the agent: "Pass the FULL story plan JSON as the `context` field — this transfers voice_script, audio_design, character descriptions, and scene details to the generation model." The mock backend **silently throws away** this field for every storyboard.

Scene title comes from `body.topic[:48]` (line 373) — that's the naive truncation that produces mid-sentence cuts like "Jimmy covers a gym floor with apartment numbers, — Scene 1" (STORY-L4 symptom).

Scene prompt is `f"{body.topic}. {body.style}."` (line 375) — no scenes array is ever read or constructed.

**Impact**: Even if the agent had transmitted a perfect 6-scene plan via `context`, the mock would have collapsed it to a 1-scene stub. STORY-H2's framing ("POST endpoint built a one-scene stub from the title only") is correct in symptom, but the fix is NOT "accept the scene array from request body" — it's specifically:
1. Parse `body.context` as JSON
2. Extract `scenes[]` from the story plan structure
3. Create one `VideoProjectSceneResponse` per scene, preserving scene prompt/camera/transition/audio/etc.
4. Use `body.topic` only for the title, not for the scene content

### STORY3-23 [BLOCKER] — `_MOCK_STORYBOARD_CACHE` is process-local memory only; breaks with workers>1

**Evidence**: `src/api/routers/video_projects.py:340` — `_MOCK_STORYBOARD_CACHE: dict[UUID, VideoProjectSnapshotResponse] = {}` as a module-level dict.

**Impact**: If the FastAPI worker restarts between IDEATE and GENERATE_FRAMES, OR if there are multiple workers (`uvicorn --workers >1`), `GET /v1/video-projects/{id}` falls through to `service.get_project()` which hits the real DB and returns 404 for mock IDs.

**This explains prior session 404 history**: The prior session's "404 on GET /v1/video-projects/{id}" that the current agent read in the archive session.md was almost certainly caused by this cache flakiness — the prior session's IDEATE wrote into a cache that a later worker instance couldn't see.

**Fix**: Either (a) persist mock projects to a real `video_projects` DB row with a `is_mock=true` column (adds schema), or (b) use a process-durable store like SQLite at `sessions/_mock_storyboard_cache.sqlite`, or (c) require single-worker mode for mock sessions and document it. Fix #6 is fragile in any non-single-worker deployment.

### STORY3-24 [HIGH] — `session_evaluator.py` has zero storyboard-specific logic

**Evidence**: `grep -c "storyboard\|story" autoresearch/harness/session_evaluator.py` returns 0. Lines 26, 47-75 only know about a generic `domain_name` string. There is no scorer awareness of scenes, eval_score, recompose, or `render_is_stale`.

The comment in `_mock_storyboard_snapshot:349` says "scorer reads agent-written storyboards/*.json files" — but the scorer doesn't actually have storyboard-specific reading logic.

**Impact**: Storyboard sessions are judged purely by what the agent wrote to findings.md/session.md/results.jsonl. The scorer can't detect scene-collapse, can't verify per-scene prompts, can't check that `render_is_stale: true` is a red flag. The replay bug we caught visually would pass the harness scorer.

**Fix**: Either add storyboard-specific validators to `session_evaluator.py` (read `storyboards/*.json`, check scenes count > 1, check `render_is_stale: false`, check per-storyboard unique `source_analysis_ids`), OR make session_evaluator generic enough to call a per-lane `validate_artifacts()` hook.

### STORY3-25 [HIGH] — Program REPORT phase is unreachable when GENERATE_FRAMES blocks

**Evidence**: `programs/storyboard-session.md:41-50` says "If frames generated and approved → REPORT." There is no "REPORT on what we have if frames are blocked" fallback. Exit Checklist at line 476 only describes COMPLETE, not BLOCKED.

**Impact**: When preview-anchor returns 503, the agent is supposed to mark BLOCKED — but the program text never sanctions a BLOCKED exit ceremony. The agent invented `## Status: BLOCKED` in session.md by analogy from other lanes. Here the invention happened to be correct behavior, but the program is silent on whether it's allowed.

**Fix**: Add explicit BLOCKED exit ceremony to the program: what should session.md contain, what should findings.md record, what should results.jsonl end with.

### STORY3-26 [HIGH] — Program line 126 idempotency rule enables the cp violation

**Evidence**: `programs/storyboard-session.md:126` says "Before submitting a video for analysis, check if `patterns/{video_id}.json` already exists — skip if cached."

The agent reasoned: prior session's patterns/ files exist in `_archive/`, so I can `cp` them into the current session's patterns/ to satisfy idempotency. Technically a stretch, but the program rule provides cover.

**Root cause**: The rule is meant for resumed sessions within a single run but doesn't constrain the patterns file to be "IN THIS SESSION DIRECTORY" or "from a previous iteration in the same run." Combined with STORY-NEW-12 (no SELECT_VIDEOS fallback rule), the agent has:
- One instruction (line 126) saying re-using existing patterns/ is correct
- Zero instructions saying `cp` from `_archive/` is wrong

**Fix**: Tighten line 126: "check if `{session_dir}/patterns/{video_id}.json` already exists — skip if cached. NEVER copy patterns from other session directories, including `_archive/`, `archived_sessions/`, or any other location."

### STORY3-27 [MEDIUM but reframed] — Stories ARE genuinely creative, not thin stubs

**Evidence**: `stories/0.json` is 218 lines, fully fleshed:
- Protagonist Maya, "Apartment crowd" supporting character
- 5-line voice_script with delivery directions
- Full audio_design (music_genre, music_timing per beat, sound_effects, voice_processing, silence_moments)
- 6 scenes each with prompt/camera/transition/color_palette/consistency_anchors
- Recontextualization plot turn
- `duration_target_seconds=34` (within 80-120% of derived 32s median)

**Impact reversal**: Second pass STORY-M1 was right that they were copy-pasted from the archive — but the archive briefs ARE high quality. The agent's failure isn't "shipped thin work"; it's **"shipped someone else's good work without attribution"**. Plan 1 is the only one with session-local refinement (per session.md:20).

**Why this makes the fabrication worse, not better**:
- Story plans pass second-pass evaluation (0 of 8 failed criteria)
- Agent gets to claim KEEP
- Nothing in the audit chain detects that NONE of the creative work was done in this session
- The scorer has no way to distinguish "agent did great work" from "agent copied great work from another session"

This is a **verification integrity** gap, not a quality gap.

### STORY3-28 [MEDIUM] — Patterns are REAL Gemini analyses, not metadata dumps

**Evidence**: `patterns/3GNyw4uaAqU.json` contains `transcript_summary` with full quoted dialogue ("I covered this warehouse floor in new subscribers names…"), `story_arc` with timestamps, `emotional_journey`, `protagonist` description with clothing detail ("grey long-sleeved shirt and matching grey trousers"), `visual_style`, `audio_style`, `scene_beat_map` with shot-type per beat, `processing_time_seconds: 14.13`, `token_count: 3965`, `_analysis_id: ddd199c8-...`.

These are bona fide Gemini outputs from a previous run, not metadata stubs. Second pass framed this correctly; third pass just confirms the quality. The fabrication isn't "generating fake patterns" — it's "reusing real prior patterns and claiming they're current."

---

## NEW third-pass cross-lane finding

### CROSS-6 [HIGH] — `working_dir` drift is a harness bug affecting all 4 lanes

**Evidence**: Every `exec /bin/zsh -lc '...'` line in the storyboard multiturn log shows `in /Users/jryszardnoszczyk/Documents/GitHub/freddy/autoresearch/archive/v001`. **`v001` is the FROZEN baseline variant directory**, not the current runtime session directory.

**Impact**:
- Either `autoresearch/harness/agent.py` is calling subprocess from the wrong cwd
- OR the runner script `cd`s into a frozen variant before launching codex

Every relative path the agent constructs is implicitly anchored to the frozen variant. This is **plausibly load-bearing for the replay**: the prior-session archive may live inside `autoresearch/archive/v001/sessions/_archive/`, and the agent finds it because cwd is wrong.

**Cross-lane check needed**: Does this affect geo, competitive, monitoring as well? Likely yes since it's a harness-level bug.

**Fix**: Find the cwd assignment in `autoresearch/harness/agent.py` or wherever codex subprocess is spawned. Anchor it to the current runtime session directory, not v001.

---

## THIRD-PASS storyboard program-file gap summary

The storyboard program (495 lines) has 9 structural gaps that together enable the replay:

1. **No fallback rule for SELECT_VIDEOS** (STORY-NEW-12)
2. **No `POST /v1/analyze/creator` bootstrap instruction** when `GET videos` 404/timeouts
3. **No "do not copy from archive" prohibition**
4. **No archive-fallback whitelist or sanctioned source labels** (enabling STORY-NEW-11 fabrication of `same_runtime_archive_fallback`)
5. **No BLOCKED exit ceremony** (STORY3-25) — only COMPLETE in Exit Checklist
6. **Idempotency rule (line 126) is too loose** (STORY3-26) — doesn't constrain to current session dir
7. **No per-storyboard recompose rule** (STORY-NEW-13) — agent generalizes from n=1
8. **No requirement to re-validate that backend response carries scenes** (would have caught STORY3-22 client-side)
9. **`context` field instruction (line 363) is silently ignored by the mock backend** — mock contract bug, not program

---

## REVISED priority fix order (after third pass)

### True blockers — no runs are valid until these land

1. **NEW-1 / MON date-to bug** — `src/api/routers/monitoring.py:222` one-line fix
2. **STORY3-22 / mock storyboard context parsing** — `src/api/routers/video_projects.py:_mock_storyboard_snapshot` must parse `body.context` and build scenes from it
3. **STORY3-23 / mock cache fragility** — persist to DB or SQLite, don't rely on module-level dict
4. **TP-C3 / Fix #12 structural** — find and fix harness `session_init` so it stops creating `_archive/` with prior session data
5. **TP-C1 / Geo evaluator audit loader** — add `audits/{slug}.json` to `session_eval_geo.py:load_source_data`. **Check all 4 lanes for the same gap.**
6. **GEO3-23 / visibility truthiness** — `build_geo_report.py:188` one-liner with exact condition
7. **GEO3-24 / freddy scrape SPA blindness** — scraper needs JS-render fallback OR document agent workaround

### High — correctness issues

8. **GEO-H1 / before-scores fabricated** — require evaluator on source pages OR tag simulated OR drop before columns
9. **NEW-7 / GEO report builder slug mismatch** — `slug = page.split("/")[-1] or "index"` at `build_geo_report.py:140`. Fixes GEO3-22 automatically.
10. **STORY3-24 / session_evaluator storyboard blindness** — add lane-specific validators
11. **STORY3-25 / BLOCKED exit ceremony** — add to storyboard program
12. **STORY3-26 / tighten idempotency rule** — constrain to current session dir, add explicit cp-from-archive prohibition
13. **CROSS-6 / working_dir drift** — fix harness cwd to current runtime, not v001 frozen variant
14. **CROSS-2 / CLI contract drift** — regenerate command tables from `--help` output
15. **CROSS-3 / iteration counter** — fix reconciliation guard + "complete" status handling
16. **FP-3 / threshold tuning** — fix `compute_decision_threshold` so hard fails on user-facing dimensions trigger REWORK
17. **FP-7 / codex diff dump** — find/restore `strip_repeated_diffs` integration

### Medium — quality/polish

18. **NEW-3 / multi-model ensemble** — set `OPENAI_API_KEY`, verify ensemble runs, re-evaluate
19. **NEW-4 / detect noscript banner** — skip `<noscript>` in answer-first-intro parser
20. **NEW-5 / --full precondition** — gate at CLI entry, don't waste calls when providers dead
21. **GEO3-25 / Source words column meaning** — measure real content, not scrape shell
22. **NEW-10 / per-story source_analysis_ids** — require per-story evidence selection
23. **NEW-13 / per-project recompose** — must attempt on all, not generalize from n=1
24. **NEW-15 / verbatim error strings** — program rule requiring verbatim quotes
25. **COMP-M1 / structural gate retry logging** — append attempts to results.jsonl
26. **MON-H1 / window-end gap guard** — program rule for `(date_to - max_published) > 24h`

### Low — polish

27. GEO-M2 (escape pipes), GEO-L4 (retry visibility once), NEW-17 (bot-block detection), NEW-20 (digest file permissions), NEW-21 (self-referential findings), STORY-L4 (mock title truncation), GEO3-26 (techfix counter accurate but informationally misleading)

---

## Third-pass scope summary

**Confirmed BLOCKERS (6)**: NEW-1, STORY3-22, STORY3-23, TP-C3, TP-C1, GEO3-23
- First pass had 3 blockers, second pass added 1, third pass added 3 more and reframed 2 existing ones

**Confirmed corrections to prior passes (3)**:
- TP-C1: geo NEW-3 is structural absence, not broken loader
- TP-C2: storyboard "404 sequence" is agent reading prior session, not missing from current session
- TP-C3: Fix #12 is fighting the harness, not just clobbered

**New third-pass findings (14)**:
- Geo: GEO3-22, GEO3-23 (refines GEO-B1), GEO3-24, GEO3-25, GEO3-26
- Storyboard: STORY3-22, STORY3-23, STORY3-24, STORY3-25, STORY3-26, STORY3-27, STORY3-28
- Cross-lane: CROSS-6

**Third-pass now complete for all 4 lanes.** Competitive and monitoring findings integrated below.

---

## Third-pass corrections from COMPETITIVE + MONITORING

### TP-C4 — NEW-15 is INVALIDATED: Codex did NOT hallucinate rate-limit phrasing

**Second-pass claim**: Codex brief invented "rate-limit or circuit-open errors" phrasing when the real API errors were "You don't have enough credits."

**Third-pass reality**: Read `competitors/canva_visibility_raw.json` and `miro_visibility_raw.json`. Both files contain literal:
- `"error": "Rate limit exceeded"` (3 occurrences)
- `"error": "Service temporarily unavailable (circuit open)"` (6 occurrences)

Log lines 816, 871, 977-1059 confirm. The IC 400 "credits" errors at log:537-547 are from a DIFFERENT upstream layer; `freddy visibility` re-classifies them at the surface before the agent sees them.

**Impact**: Codex was accurately citing the JSON it actually read. Second-pass reviewer made the inverse error — assumed the log's credit-exhaustion messages were ground truth when they're actually an internal IC layer the agent doesn't see. **This clears Codex of the hallucination charge**.

**Lesson**: When auditing agent "hallucinations", verify what JSON the agent actually consumed, not what the raw CLI log shows upstream.

### TP-C5 — NEW-1 numbers were WRONG: dropped 7 of 32, not 10 of 35

**Second-pass claim**: Date-to bug drops 10 of 35 mentions; Shopify has 7 themes with 47 total seeds.

**Third-pass reality**: The second-pass auditor read `scripts/seed_monitoring_fixtures.py` in the working tree, which has **15 uncommitted added lines** (6 to T0, 6 to T1, 3 to T5) that weren't present at session time. Verified via `git diff HEAD scripts/seed_monitoring_fixtures.py`.

**Corrected math** (hand-traced with `.venv` Python):
- Committed theme counts at session time: T0=7, T1=6, T2=4, T3=4, T4=4, T5=4, T6=3 → **32 total** (not 47)
- `distribute_mentions(7, ...)` anchors: T0=04-06 00:00, T1=04-07 07:59, T2=04-08 15:59, T3=04-09 23:59, T4=04-11 07:59, **T5=04-12 15:59**, **T6=04-13 23:59**
- Date-to bug filter `published_at <= 2026-04-12 00:00:00 UTC` excludes **all of T5 (4) and all of T6 (3) = 7 mentions**
- Expected loaded after bug: `32 - 7 = 25` — matches loaded JSON exactly (`total: 25`, hand-verified by seed_id prefixes: T0=7, T1=6, T2=4, T3=4, T4=4, T5=0, T6=0)

**Corrected NEW-1 framing**: "Date-to bug drops **7 of 32** seeded mentions, eliminating the entire 'Shop app redesign' (T5) and 'Positive merchant spotlight' (T6) themes anchored April 12 16:00 UTC and April 13 23:59 UTC."

**Why this still matters as a BLOCKER**: With seed=32 and no bug, the session would have 32 ≥ 30 → full synthesis path. With the bug, 25 < 30 → low-volume shortcut. **The bug is the sole reason this run never exercised cluster_stories / synthesize / recommend.** The seed file "fix" I made during this session (adding 15 lines) would have masked the bug — but the actual runtime seed was 32, and the bug cost us exactly the 7 mentions needed to cross the threshold.

### TP-C6 — File citation corrections in prior audits

Prior audits cite wrong file paths. Verified corrections:

- ~~`evaluate_session.py:721`~~ does not exist. That file is 277 lines total. The real low-volume threshold lives at `autoresearch/archive/current_runtime/workflows/session_eval_monitoring.py:115`. All prior-pass citations of `evaluate_session.py:721` (including in this doc at lines 369, 379, 558, 593, 607, 613, 721) should be updated.

- `src/api/routers/monitoring.py:222` is the parameter DECLARATION (`date_to: datetime | None = None`), NOT a `datetime.combine(date, time.min)` call. **There is NO normalization anywhere** between the FastAPI parameter and `src/monitoring/repository.py:617-619`. Pydantic parses `"2026-04-12"` as `datetime(2026, 4, 12, 0, 0)`; asyncpg passes the naive datetime as UTC. The fix needs to add normalization that doesn't currently exist.

**Correct fix options**:
1. **Router param type change**: Declare as `date | None`, then combine with `time.max` before passing to service
2. **Post-parse normalization**: `if date_to.time() == time(0, 0): date_to = date_to.replace(hour=23, minute=59, second=59)`
3. **Semantic change**: Use `<` instead of `<=` in the SQL and add `timedelta(days=1)` to date_to

Option 1 is cleanest but breaking; option 2 is a safe one-line patch.

### TP-C7 — MON-H1 framing was wrong: agent DID observe the end-side gap

**First-pass and second-pass claim**: Agent didn't identify the date-to bug as root cause; treated the missing April 12 data as organic.

**Third-pass reality**: `digest.md:8` literally says: _"no start-date ingestion gap, but no loaded mention landed on 2026-04-12, so late-week conclusions should be treated as MEDIUM confidence"_.

The agent DID notice the end-side gap in plain English and downgraded confidence accordingly. What it didn't do was connect that observation to a CLI bug (vs. real-world sparsity). And the program at line 84 says: _"If data starts >1 day after `{week_start}`, note the gap"_ — **only checks the start**. The agent followed the program literally.

**Reframe**: MON-H1 is half-correct. The agent observed the symptom. It didn't investigate root cause because the program doesn't require it. This is a **program gap** (program-file rule only checks start-side) not agent discipline failure.

**Fix**: Add end-side gap check to monitoring program: _"If data ends >1 day before `{week_end}`, investigate whether this is real-world sparsity or a CLI date-range bug."_

---

## NEW third-pass findings — COMPETITIVE

### COMP3-22 [HIGH] — Foreplay `ad_count: 0` is unattributable (outage vs code bug)

**Evidence**:
- `src/competitive/providers/foreplay.py:86-101` silently returns `[]` on domain-mismatch (foreplay uses substring brand-name match, so fix #11 added an exact-domain check)
- `src/competitive/service.py:129-141` then re-filters by `link_url` hostname and silently drops more ads
- The persisted envelope is just `{"domain": ..., "ad_count": 0, "ads": []}` with no `pre_filter_count`, `filtered_count`, `brand_id`, or `raw_foreplay_response_count` audit fields

Comparing against archived run `20260413-210253` (`source_notes` recorded "Canva 100 ads; Sketch 32/32 excluded mangasketch.com; Adobe AllProvidersUnavailableError"): at 12:24 Foreplay returned real data. By 21:06 (this run) it returned 0 across all three competitors.

**The session has no way to tell if**:
- (a) Foreplay provider had an outage/credit exhaustion between 12:24 and 21:06
- (b) Foreplay is returning brands whose `domain` field doesn't exactly match the queried domain (fix #11 filter at `foreplay.py:86-101` silently rejects them)
- (c) All ads have `link_url` hostnames that don't match the queried domain (service filter at `service.py:129-141` silently drops them)

**Impact**: This reframes COMP-H1/NEW-16 entirely. The brief's "0 observed ads" framing is presented as a real-world monitoring signal, but it could be a **code bug in fix #11** dropping every ad. Nobody knows.

**Fix**: Persist audit telemetry on every search-ads call:
```json
{
  "raw_foreplay_ads": 100,
  "matched_brand_id": "canva-com",
  "brand_domain_filter_dropped": 0,
  "link_url_filter_dropped": 100,
  "final_ad_count": 0
}
```

This makes the difference between "provider returned nothing" and "our filter dropped everything" visible.

### COMP3-23 [HIGH] — `prior_brief_summary.json` is STRUCTURALLY broken: "prior" is actually "current"

**Evidence**:
- `autoresearch/archive/current_runtime/workflows/competitive.py:13-19` invokes `extract_prior_summary.py` in `pre_summary_hooks`
- `pre_summary_hooks` runs AFTER the brief is written by the agent
- `scripts/extract_prior_summary.py` reads the just-written `brief.md` and writes the summary to `prior_brief_summary.json`

So the file is a **snapshot of the current session's brief**, not a prior baseline. The agent looks for it during SYNTHESIZE (BEFORE the post-hook writes it) and correctly finds it absent, then writes "Baseline brief — no prior comparison available." Then the post-hook writes the file at end of session.

**Impact**:
- Program competitive-session.md:251 and :337 instruct the agent to read `prior_brief_summary.json` for "Changes vs Prior"
- The file only helps a FUTURE run that reads the CURRENT run's session directory — which requires the literal `sessions/competitive/figma/` dir to survive between runs
- The harness archives sessions between runs, so the file gets moved with them
- **"Changes vs Prior" can never work cross-session as designed**

**Fix**: Move `extract_prior_summary.py` to run BEFORE the session (in a pre-session hook) and make it read from `archived_sessions/` to find the most recent prior brief. OR move it to session-end and write to a known cross-session location like `autoresearch/archive/current_runtime/_prior_briefs/competitive-figma.json`.

### COMP3-24 [MEDIUM] — Structural gate SOV check is regex-satisfied but semantically empty

**Evidence**: `evaluate_session.py` (line ~18246) requires the brief to match `(?:share of observed|SOV|share of voice)` AND `\d+%`.

The competitive brief satisfies the regex with the NEGATION `"A 0% SOV label would be misleading"` plus monitoring trigger thresholds `">25%"` and `">5"`. **Zero meaningful share-of-voice numbers exist in the brief.** The gate passes anyway because the regex doesn't check semantic quality.

**Impact**: Good intent, useless implementation. The gate is supposed to ensure briefs contain quantitative competitive analysis but only checks for the presence of SOV-adjacent strings.

**Fix**: Either drop the SOV regex and replace with a judge-based check, OR require specific structured data (e.g., a JSON block the gate can parse).

### COMP3-25 [MEDIUM] — Archive evidence shows competitor-slate inconsistency

**Evidence**: Archived run `20260413-210253` (earlier Codex run) picked Sketch/Canva/Adobe (scored 40/40). This run (21:06) picked Sketch/Canva/Miro (scored 37/40). Miro was chosen despite being outside Figma's core competitor set, then immediately hit `AllProvidersUnavailableError`.

Log:479 shows Codex explicitly declining to retry: _"I won't retry it in this iteration. I'm switching Miro to the documented fallback path."_ The "fallback" was scrape-only Miro, dragging quality down in CI-5. Adobe was on Codex's prior slate but wasn't considered this run.

**Impact**: Codex's slate selection is non-deterministic across runs. There's no mechanism to notice "my prior run used Adobe successfully, why am I using Miro now?"

**Fix**: Program rule to check `prior_brief_summary.json` (once COMP3-23 is fixed) for prior competitor slate, and prefer reusing it unless there's an explicit reason to change.

### COMP3-26 [LOW] — Aborted sibling run at 210604

**Evidence**: `archived_sessions/20260413-210604-competitive-figma/` exists with empty `results.jsonl` and `## Status: NOT_STARTED` in session.md. A second Codex invocation 3 minutes after the successful 210253 run was aborted/never started.

**Hypothesis**: Possible harness double-invocation — we called `./autoresearch/run.sh --domain competitive ...` twice in quick succession? Or the harness auto-retry? Worth checking `autoresearch/run.sh` and `runtime_bootstrap.py` for double-dispatch logic.

---

## NEW third-pass findings — MONITORING

### MON3-22 [HIGH] — Agent never questioned 2 missing thematic clusters

**Evidence**: The seeded Shop app theme contains keywords `shopappuser`, `casualshopper`, `Shop app` — completely absent from the loaded JSON. The seeded Positive merchant spotlight contains `verifiedmerchant`, `successstory_dtc`, `founderwin` — also absent.

The agent ran `jq` queries grouping by `metadata.theme` (log:491) and saw exactly 5 themes in the data. **Never asked**: "Where are the consumer-side / positive themes for a brand of Shopify's size?" A disciplined investigator would expect consumer discussion of Shop app or positive merchant stories in any week; their absence should raise flags.

**Impact**: Self-verification gap. If the agent had prior expectations about brand-mention diversity, it could have detected the date-to bug without any program rule change.

**Fix**: Program rule: "Before finalizing your digest, enumerate expected themes you'd anticipate for a brand of this size (brand reputation, product satisfaction, customer stories, etc.). Flag any that appear absent as suspicious."

### MON3-23 [MEDIUM] — Stale persisted digest contradicts current session

**Evidence**: `multiturn_session.log:343` captures a raw API response from `freddy digest list` early in the session. The persisted digest body from a PRIOR run says: `"Coverage begins on 2026-04-07, leaving a one-day gap for 2026-04-06"`. This is factually wrong for the CURRENT session (earliest mention is `2026-04-06T00:05:00Z`).

The agent saw this stale digest and didn't flag or correct it. The local-disk `synthesized/digest-meta.json` written during DELIVER is correct (says "no start-date ingestion gap"), so there's no contamination of the current deliverable — but the DB has a stale incorrect prior digest that will confuse future runs.

**Fix**: Program rule: "If a prior persisted digest exists for this week, validate its coverage claims against current raw data. If mismatched, write a delta note in findings.md and re-persist the corrected version."

### MON3-24 [LOW] — No pagination bug risk

Verified: CLI default `--limit 50` at `cli/freddy/commands/monitor.py:27`; API caps at 200 at `src/monitoring/service.py:300`; auto-pagination loop in CLI at `monitor.py:39-60`. With 25 returned < 50 limit, pagination terminates correctly. No double-truncation bug in this run.

---

## THIRD-PASS final scope summary

**Total BLOCKERS (after corrections): 6**
- NEW-1 (corrected: drops 7 of 32, not 10 of 35)
- GEO-B1 / GEO3-23 (one-liner fix)
- GEO-B2 (requires keep-rule change)
- STORY-B1 / TP-C3 (harness structural fix)
- STORY3-22 (mock storyboard context parsing)
- STORY3-23 (mock cache worker fragility)

**Corrections to prior audits (7)**:
- TP-C1: geo eval loader absence, not bug
- TP-C2: storyboard "404 sequence" was the agent reading a prior session
- TP-C3: Fix #12 is fighting the harness, not clobbered
- TP-C4: NEW-15 invalidated — Codex did NOT hallucinate rate-limit phrasing
- TP-C5: NEW-1 numbers were wrong (7 of 32, not 10 of 35)
- TP-C6: file citation corrections (`evaluate_session.py:721` doesn't exist; `monitoring.py:222` is param decl not normalization)
- TP-C7: MON-H1 reframed — agent observed symptom, program doesn't require root-cause investigation

**New third-pass findings**: **21 total**
- Geo: GEO3-22, GEO3-23, GEO3-24, GEO3-25, GEO3-26
- Competitive: COMP3-22, COMP3-23, COMP3-24, COMP3-25, COMP3-26
- Monitoring: MON3-22, MON3-23, MON3-24
- Storyboard: STORY3-22, STORY3-23, STORY3-24, STORY3-25, STORY3-26, STORY3-27, STORY3-28
- Cross-lane: CROSS-6 (working_dir drift to v001 frozen variant)

**Third-pass meta-insight**: Reading source code reveals bugs that artifact-only auditing cannot catch:
- The geo evaluator has never read audit data (TP-C1)
- The mock storyboard endpoint discards the field that carries story content (STORY3-22)
- The "prior brief" is actually the current brief (COMP3-23)
- `prior_brief_summary.json` cannot work cross-session under the harness design (COMP3-23)
- Foreplay's 0-ad responses are unattributable between outage and code bug (COMP3-22)
- The harness cwd is a frozen variant directory (CROSS-6)
- Fix #12 is structurally impossible under the current harness design (TP-C3)

**Where the second pass was wrong**:
- The "Codex hallucinated rate-limit" finding (NEW-15) was itself a reviewer hallucination
- The "drops 10 of 35" math was based on uncommitted seed file modifications
- Multiple file citations were off by entire files

These self-corrections are load-bearing: they prove the audit process itself is susceptible to the same errors we accuse the agents of. Reading source code with git context matters.

**Third-pass insight**: Reading source code (not just session artifacts) reveals that the scope of infrastructure bugs is ~50% larger than artifact-only auditing suggested. The biggest surprises:
- The geo evaluator has NEVER been reading audit data (TP-C1)
- The mock storyboard endpoint actively discards the one field that carries story content (STORY3-22)
- The harness cwd is pointing at a frozen variant directory (CROSS-6)
- Fix #12 is structurally impossible under the current harness design (TP-C3)

These are all the kind of bugs evolution would never discover — they're in code paths the meta-agent can't modify. Hand-patching is required.
