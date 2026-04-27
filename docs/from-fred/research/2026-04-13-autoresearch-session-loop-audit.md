# Autoresearch Session Loop Audit — 2026-04-13

## Context

After completing the evolve.sh → Python port and fixing monitoring/storyboard preflight issues, we launched 4 real session loops (one per workflow) to validate the end-to-end pipeline with a live freddy backend. This document captures every issue found in the sessions' output, logs, and transcripts.

**Session run parameters:**
- geo: semrush (https://www.semrush.com)
- competitive: figma
- monitoring: Shopify (monitor_id: ef702c19-9849-59bd-a2e4-74a25dba81d1)
- storyboard: MrBeast (youtube)

**Infrastructure state at launch:**
- freddy backend: healthy on port 8000 (PID 72445)
- 4 Supabase containers up
- `externals_mode: real`, `task_client_mode: mock`
- 90 mentions seeded for April 7-13
- weekly_digests table created
- yt-dlp installed
- All CLIs on PATH (freddy, claude, codex)

---

## Session Outcomes

| Workflow | Client | Status | Iterations | Evolution-ready |
|----------|--------|--------|------------|------------------|
| geo | semrush | **COMPLETE** | 10 | **Yes** — real evaluator scores |
| competitive | figma | **COMPLETE** | 6 | **Yes** — 40/40 evaluator score |
| monitoring | Shopify | **COMPLETE** (low-volume path) | 4 | Limited — skipped 3 phases |
| storyboard | MrBeast | **BLOCKED** at GENERATE_FRAMES | 9 (9 kept) | Partial — backend bug |

---

## 1. geo/semrush — Complete, High-quality signal

**Path:** `autoresearch/archive/current_runtime/sessions/geo/semrush/`

### Phase progression (correct order)

```
discover → competitive → seo_baseline → 6× optimize → report
```

### What worked (real measured data, unlike the earlier simulated run)

- `freddy sitemap https://www.semrush.com` — 11 sitemaps parsed, 10000 URLs found
- `freddy scrape` — all 6 priority pages successfully scraped (no curl fallback this time)
- `freddy detect` + `freddy detect --full` — all 6 pages with structured infrastructure audit
- **Gemini evaluator ran for real** — model `gemini-3.1-pro-preview` produced 6 per-page eval JSONs in `evals/optimized-*.json` with concrete rationale and quoted evidence
- All 6 pages received `decision: KEEP`
- GEO-5 (citability moat) and GEO-7 (gap targeting) scored 1.0 across all pages

### Score breakdown per page (Gemini evaluator)

| Page | Failed criteria | Delta (rubric) |
|------|----------------|-----------------|
| traffic-analytics | 0/8 | +0.41 |
| pricing | 1/8 (GEO-7 — needs real SSR pricing data) | +0.54 |
| site-audit | 1/8 (GEO-4 voice match — "Compared with Screaming Frog" forced) | +0.40 |
| home | 1/8 (GEO-4 voice match — forced "Compared with Ahrefs") | +0.32 |
| backlinks | 2/8 (GEO-1, GEO-4 — leaked meta-instruction) | +0.41 |
| keyword-research-toolkit | 2/8 (GEO-4, GEO-6 — cross-page reuse + leaked system note) | +0.44 |

### Critical score distinction

**The `before`/`after` citability+geo_quality floats in `results.jsonl` are RUBRIC-derived, NOT measured by the evaluator.** They come from the agent's internal scoring rubric applied against detect+scrape evidence. The session.md even acknowledges this ("pricing had the largest simulated delta because the baseline was weakest").

**The true measured signal is in `evals/optimized-*.json`** — per-criterion pass/fail + rationale from `gemini-3.1-pro-preview`. The frontier should sort on those, not the rubric floats.

### Infrastructure failures

1. **`freddy visibility` stalled indefinitely** — 6 queries, 0 bytes returned, process had to be killed. `competitors/visibility.json` shows `method: unavailable, status: partial, error.type: stalled_no_output` for all 6 queries.
2. **DataForSEO provider unavailable** — `seo_full.dataforseo_error: provider_unavailable` on all 6 detect-full runs. PageSpeed/Core Web Vitals data is null.
3. **Codex runtime error on subprocess kill** — log line 1306: `codex_core::tools::router: error=write_stdin failed: stdin is closed for this session; rerun exec_command with tty=true to keep stdin open`. Benign artifact of killing the stalled visibility subprocess.

### Content generation bugs (agent behavior, fixable via evolution)

1. **Meta-instruction leakage into publishable content**
   - `optimized/backlinks.md` leaked: `"Measurement note for implementers: citation data is unavailable, so keep this as a feature-only comparison and do not add citation-count claims."`
   - `optimized/keyword-research-toolkit.md` leaked: `"Citation data unavailable..."` in a text block
   - Gemini evaluator correctly flagged these as fourth-wall-breaking text that shouldn't ship
   - **Fix:** Program prompt should require fallback notes in evidence header, never in content blocks

2. **Forced "Compared with X" intro compulsion**
   - home.md: forced "Compared with Ahrefs" into first paragraph of homepage
   - site-audit.md: forced "Compared with Screaming Frog" into intro
   - keyword-research-toolkit.md: forced "Compared with Ahrefs" (reuse of home's competitor)
   - Evaluator: "entirely bolted on to satisfy a rubric requirement"
   - **Fix:** Prompt should forbid competitor mentions in INTRO blocks for top-level pages

3. **Cross-page differentiator reuse**
   - keyword-research-toolkit.md reused "workflow depth" differentiator already used on backlinks.md
   - home+pricing+keyword-research all use "Compared with Ahrefs"
   - **Fix:** Program should maintain cross-page differentiator uniqueness

### Key files

- `sessions/geo/semrush/session_summary.json` — COMPLETE, 10 iters, 9 productive, 0 failed
- `sessions/geo/semrush/evals/optimized-*.json` — 6 per-page real evaluator scores (THE signal)
- `sessions/geo/semrush/results.jsonl` — rubric-derived deltas (secondary)
- `sessions/geo/semrush/competitors/visibility.json` — documented visibility stall
- `sessions/geo/semrush/logs/multiturn_session.log` — full transcript

---

## 2. competitive/figma — Complete, 40/40 evaluator

**Path:** `autoresearch/archive/current_runtime/sessions/competitive/figma/`

### Phase progression

```
gather → analyze(canva) → analyze(sketch) → analyze(adobe) → synthesize → verify
```

6 iterations. Evaluator `KEEP` with 40/40 raw score, 8/8 criteria at full 5.0, `critical_pass: true`.

### What worked

- `freddy search-ads figma.com` — 2 community ads (baseline)
- `freddy search-ads canva.com` — 100 clean ads analyzed
- `freddy detect` — all 3 competitors (Canva, Sketch, Adobe) after adapting to full-URL requirement
- `freddy scrape` — Sketch home (744w) + pricing (2884w), Adobe home (111w) + plans (149w)
- Brief: 1830 words across 11 required sections, 4 recommendations with deadlines and competitive response models

### Per-competitor quality scores

| Competitor | Quality | Data tier | Notes |
|-----------|---------|-----------|-------|
| Canva | 18/20 | full | 100 clean ads, taxonomy well-built |
| Sketch | 17/20 | scrape_only | Ads contaminated, pivoted to scrape + pricing |
| Adobe | 16/20 | partial | XD scrape failed, ads provider down |

### Infrastructure failures

1. **`freddy search-ads sketch.com` ad-library contamination** — returned 32 ads ALL linked to `mangasketch.com`. Agent correctly excluded all 32 and marked sketch as scrape-only. This is a **Foreplay-side substring matching bug** — the provider is matching "sketch" as a substring instead of doing proper domain matching.
2. **Adobe `freddy search-ads adobe.com` → `AllProvidersUnavailableError`** — `adobe_ads_raw.json` is 0 bytes. Zero ad data for Adobe.
3. **`freddy search-content` → IC credits exhausted** — HTTP 400 `"You don't have enough credits - please refill"` for all 3 competitors. Kills creator channel analysis.
4. **AI visibility rate-limited / circuit-open** — All 3 platforms (ChatGPT, Perplexity, Gemini) returned rate-limit or circuit-open errors on every query for every competitor. Matches Run #5/#6 forensic findings — this is a recurring pattern.
5. **freddy CLI contract drift** — `freddy detect` initially rejected bare domains and `freddy visibility` required new `--brand`/`--keywords` flags. Agent had to probe `--help` at runtime to recover. These are silent CLI contract changes the prompt doesn't document.
6. **Canva home/enterprise scrape hit "Unsupported client" gate** — scraper got 54-word stub pages titled "Unsupported client – Canva". Browser/UA detection blocking freddy scrape.
7. **Adobe XD scrape `internal_error`** — single transient failure on `https://www.adobe.com/products/xd.html`, not retried.

### Harness bug

- **`session_summary.json findings_count: 0` is incorrect** — findings.md actually contains 4 confirmed findings + 3 observations. Counter bug in `session_summary.json` generation.

### Exceptional data-absence handling

The agent handled source failures with textbook honesty:
- Never claimed "no creator activity" when search-content failed
- Explicitly labeled ad gaps as "unmeasured" not "absent" throughout the brief
- CI-8 (data-absence handling) passed at 5.0 specifically on this point
- Added "API Search-Content Credit Gap" to findings.md as an Observation

### Key files

- `sessions/competitive/figma/brief.md` — 1830-word brief with 4 actionable recommendations
- `sessions/competitive/figma/analyses/{canva,sketch,adobe}.md` — per-competitor deep dives
- `sessions/competitive/figma/eval_feedback.json` — 40/40 evaluator output
- `sessions/competitive/figma/session_summary.json` — (has the findings_count bug)
- `sessions/competitive/figma/results.jsonl` — 6 phase entries

---

## 3. monitoring/Shopify — Complete (low-volume shortcut)

**Path:** `autoresearch/archive/current_runtime/sessions/monitoring/Shopify/`

### Phase progression (truncated)

```
select_mentions → low_volume_digest → digest_evaluation → persist_digest
```

4 iterations. Evaluator `KEEP` with 0 failed criteria. **Three phases skipped** per program rule: CLUSTER_STORIES, DETECT_ANOMALIES, SYNTHESIZE, RECOMMEND, DELIVER.

### What worked

- `freddy monitor mentions` — loaded 25 mentions for period 2026-04-06 to 2026-04-12
- `freddy monitor baseline` — generated commodity baseline (confirms earlier fixes worked)
- `freddy digest list` — returned empty array (correct, weekly_digests table created)
- `freddy digest persist` — successfully persisted digest `c39084b9-7edf-408c-8ab9-b0bd77b833bb`
- Sources identified: reddit 12 / twitter 8 / newsdata 5 (total engagement 7,808)
- Sentiment: 15 negative / 6 positive / 4 mixed
- 5 directional themes captured:
  1. AI tier pricing backlash (7 mentions, 3,586 engagement)
  2. Magic bulk description launch (6 mentions, 1,568 engagement)
  3. Shopify Payments dispute policy change (4 mentions, 1,385 engagement)
  4. Plus vs BigCommerce comparison (4 mentions, 709 engagement)
  5. Checkout extensibility bug (4 mentions, 560 engagement)

### Observations / issues

1. **Mention count discrepancy: 25 loaded out of 32 seeded** — 7 mentions lost somewhere. Observed timestamps: 2026-04-07T00:05:00Z to 2026-04-11T17:47:59Z. Agent noted: "Ingestion gap: no loaded mentions for 2026-04-06" and "every theme is concentrated on a single date." Possible causes: filter by `sentiment_score IS NOT NULL`, date range clipping April 13, or period boundary (`2026-04-06/2026-04-12` window misses April 13 entries).

2. **Low-volume shortcut bypassed 3 evolution-relevant phases** — per program rule, since mentions < threshold the agent skipped CLUSTER_STORIES, SYNTHESIZE, RECOMMEND. The digest was still produced but the clustering/synthesis logic wasn't exercised, which means evolution can only target the digest phase, not the full pipeline.

3. **Severity calls capped at MEDIUM** — agent explicitly noted: "Coverage gaps change confidence: all severity calls are MEDIUM at most because the loaded window starts one day late and every theme is concentrated on a single date."

### Key files

- `sessions/monitoring/Shopify/session.md` — COMPLETE status with low-volume summary
- `sessions/monitoring/Shopify/digest.md` — final digest
- `sessions/monitoring/Shopify/recommendations/{executive_summary,action_items,cross_story_patterns}.md`
- `sessions/monitoring/Shopify/synthesized/digest-meta.json`
- `sessions/monitoring/Shopify/results.jsonl` — 4 entries

---

## 4. storyboard/MrBeast — BLOCKED at GENERATE_FRAMES

**Path:** `autoresearch/archive/current_runtime/sessions/storyboard/MrBeast/`

### Phase progression

```
select_videos → analyze_patterns → plan_story → 5× ideate → [BLOCKED: generate_frames]
```

9 iterations completed. **Blocked** because the backend storyboard endpoint returns mock snapshots that don't persist.

### What worked (first 4 phases)

- `GET /v1/creators/youtube/MrBeast/videos` — 50 videos fetched, 17 selected
- `POST /v1/analyze/videos` — 17 videos analyzed
- `GET /v1/creative/{analysis_id}` — 17 creative pattern files extracted successfully
- Pattern analysis: top videos surfaced correctly:
  - "Subscribe for an iPhone" — 1.2B views
  - "Flip a Coin, Win $30,000" — 927M
  - "Answer The Call, Win $10,000" — 925M
- Derived story profile: 15/17 hooks are `shock_curiosity`, all 17 `fast_cut`, all 17 no background music, median 32s, mean scene ~5.6s
- 5 story plans produced, all passing evaluator on second pass:
  1. `0.json` — "The Dart Picks Your Rent" (scale reveal, 34s/6 scenes)
  2. `1.json` — "If The Principal Answers, Eli Chooses The Prize" (32s/6 scenes)
  3. `2.json` — "World's Fastest Lemonade Stand" (33s/6 scenes)
  4. `3.json` — "One Mascot Is The Fastest Man Alive" (32s/6 scenes)
  5. `4.json` — "I Made A Pancake With A Bulldozer" (36s/6 scenes)

### The blocking bug

**`POST /v1/video-projects/storyboard` returns valid project UUIDs but `GET /v1/video-projects/{id}` returns 404 on ALL 5 projects.**

Evidence from `frames/frame_generation_errors.json`:
```json
{
  "status": "blocked",
  "phase": "GENERATE_FRAMES",
  "reason": "Storyboard create endpoint returned valid mock snapshots, but returned project IDs were not persisted and all readback calls returned 404.",
  "checked_endpoint": "GET /v1/video-projects/{project_id}",
  "project_errors": [
    { "project_id": "0209104a-a92b-4916-9e3b-81461fd1fabb", "http_status": 404, ... },
    { "project_id": "1a2c065f-7e7d-4c6c-aba3-284263151ed3", "http_status": 404, ... },
    { "project_id": "1abba96f-1e28-484e-b28f-8d1b4ad926f3", "http_status": 404, ... },
    { "project_id": "1fb20b31-5d70-4c76-9b3d-944bf7c7573f", "http_status": 404, ... },
    { "project_id": "2e014a66-a16c-4b84-a04f-1640308e3bd2", "http_status": 404, ... }
  ]
}
```

**Root cause: `task_client_mode=mock`** — the storyboard endpoint is stubbed, returns fake project IDs, nothing persists. The session ran as far as it could and correctly diagnosed:

> "API mock storyboard snapshots are not persisted in this runtime; frame generation requires a backend mode that creates readable video-projects."

### Key files

- `sessions/storyboard/MrBeast/session.md` — BLOCKED, next action documented
- `sessions/storyboard/MrBeast/selected_videos.json` — 17 videos
- `sessions/storyboard/MrBeast/patterns/*.json` — 17 pattern files
- `sessions/storyboard/MrBeast/stories/*.json` — 5 story plans
- `sessions/storyboard/MrBeast/storyboards/*.json` — 5 mock snapshots (1 stub scene each)
- `sessions/storyboard/MrBeast/frames/frame_generation_errors.json` — block diagnosis

---

## Consolidated Infrastructure & Harness Issues

| # | Issue | Severity | Affected | Source |
|---|-------|----------|----------|--------|
| 1 | `freddy visibility` stalls indefinitely — no timeout, no output | **CRITICAL** | geo, competitive | geo session stall for all 6 queries |
| 2 | Storyboard backend persists nothing — `task_client_mode=mock` stubs | **CRITICAL** | storyboard | 5x 404 on video-projects readback |
| 3 | `freddy search-ads sketch.com` returns mangasketch.com contamination | **HIGH** | competitive | 32/32 contaminated ads |
| 4 | `freddy search-ads` AllProvidersUnavailableError (Adobe) — no retry | **HIGH** | competitive | Adobe ads 0 bytes |
| 5 | `freddy search-content` — IC/Influencers.club credits exhausted | **DEFERRED** | competitive | Intentionally deferred — credits too expensive for evolution runs. Competitive program fallback works (40/40 without it). |
| 6 | `session_summary.json findings_count: 0` bug (should be 7) | MEDIUM | competitive | Counter bug in summary gen |
| 7 | DataForSEO provider not configured | MEDIUM | geo | PageSpeed null |
| 8 | AI visibility providers rate-limited / circuit-open (ChatGPT, Perplexity, Gemini) | MEDIUM | geo, competitive | Recurring pattern from Run #5/#6 |
| 9 | `freddy detect` contract drift — rejects bare domains | MEDIUM | competitive | Agent had to probe --help |
| 10 | `freddy visibility` contract drift — requires --brand/--keywords | MEDIUM | geo, competitive | Agent had to probe --help |
| 11 | Monitoring loads 25/32 seeded mentions (7 missing) | MEDIUM | monitoring | Ingestion gap, date window |
| 12 | Canva scrape hits "Unsupported client" browser gate | LOW | competitive | 54-word stub pages |
| 13 | Adobe XD scrape `internal_error` | LOW | competitive | Single transient failure |
| 14 | Codex runtime `write_stdin failed` when killing stalled subprocess | LOW | geo | Benign cleanup artifact |

## Content Generation Issues (fixable via evolution)

| # | Issue | Source | Fix target |
|---|-------|--------|-----------|
| 1 | Meta-instruction leakage into published content blocks | geo/backlinks.md, geo/keyword-research-toolkit.md | Program prompt |
| 2 | Forced "Compared with X" competitor name-drop in INTROs | geo/home.md, geo/site-audit.md, geo/keyword-research-toolkit.md | Program prompt |
| 3 | Cross-page differentiator reuse (same "workflow depth" on 2 pages) | geo/backlinks.md + keyword-research-toolkit.md | Program prompt |
| 4 | Homepage stat claim hallucination flag (false positive) | geo/home.md GEO-8 | Evaluator tuning |

---

## Evolution Readiness Assessment

### Ready to evolve now

- **geo lane** — HIGH quality signal. Real per-criterion evaluator scores from Gemini. Content failure modes are directly actionable as prompt-engineering targets. Priority: fix meta-instruction leakage and competitor name-drop compulsion.
- **competitive lane** — HIGH quality signal. Evaluator at ceiling (40/40). Data-absence handling is textbook. Evolution can target brief assembly, taxonomy naming, and recommendation specificity.

### Ready with caveats

- **monitoring lane** — MEDIUM quality signal. Low-volume path means only 4 phases exercised. Can evolve digest phase and low-volume heuristic, but not full clustering/synthesis logic. To fully exercise the workflow, need more mentions (>threshold) or adjust the low-volume shortcut.

### Blocked

- **storyboard lane** — Cannot reach GENERATE_FRAMES phase while `task_client_mode=mock`. Evolution can target SELECT_VIDEOS, ANALYZE_PATTERNS, PLAN_STORY, IDEATE phases but the final frame generation is unreachable.

---

## Priority Fixes Before Next Run

1. **`freddy visibility` stall** — add hard timeout + fail-fast exit. Without measured citation counts, geo and competitive lanes can never score against AI-citation ground truth.
2. **Storyboard backend persistence** — either switch off mock mode for video-projects or implement mock-to-DB write path so `GET /v1/video-projects/{id}` can return the mock data.
3. **Foreplay domain matching bug** — fix substring matching that returns mangasketch.com for sketch.com queries.
4. **`session_summary.json findings_count`** — fix counter to read from findings.md actual content.
5. **Meta-instruction leakage guardrail** — update geo-session.md program to explicitly forbid implementer notes in content blocks.
6. **Competitor name-drop guardrail** — update geo-session.md to forbid competitor mentions in INTRO blocks for top-level pages.

## Reference

- Infrastructure baseline: `docs/research/2026-04-08-autoresearch-run5-forensic-analysis.md`
- Previous audit: `docs/research/2026-04-11-autoresearch-evaluation-infrastructure-audit.md`
- Plan for evolve.py port: `docs/plans/2026-04-11-005-refactor-evolve-bash-to-python-plan.md` (completed)

---

# Second Pass Forensic Audit — NEW Findings (2026-04-13)

Deep log-level analysis of the 4 session log files (141,389 total lines) found **27 new issues** not captured in the first pass. The methodology: read full multiturn_session.log per session, grep for errors/retries/timeouts, compare claimed behavior against log reality, check counters against source data.

## Session run context (previously unstated)

- All 4 sessions launched in **parallel** within a 23-second window at 12:20:41-12:21:04
- Session wall times: **geo 31.6m, storyboard 21.2m, competitive 16.3m, monitoring 11.25m**
- All 4 sessions competed for the same `gemini-3.1-pro-preview` evaluator rate limit — likely contributing to non-determinism
- Logs total 141,389 lines; geo alone is 6.3 MB / 95,367 lines
- **No telemetry/metrics/timings files exist** — only `session_summary.json` + `results.jsonl`. Per-phase duration requires log parsing
- **Watchdog never fired in any session** — no stall detection triggered. The 134-second visibility stall in geo did not trigger the 120-second watchdog (likely because agent's concurrent activity touched other files in the poll window)

---

## CRITICAL severity (new)

### N-1. Evaluator is non-deterministic — same criterion flips PASS ↔ FAIL across consecutive runs on near-identical content

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L7975, L10194, L13486 — 3 evaluator calls on `optimized/pricing.md`

| Call | Decision | Fail count | GEO-1 | GEO-2 | GEO-4 | GEO-7 |
|------|----------|------------|-------|-------|-------|-------|
| 1 | KEEP | 2/7 | 0.25 FAIL | 1.0 PASS | 0.0 FAIL | 1.0 PASS |
| 2 | REWORK | 3/7 | 1.0 PASS | 0.25 FAIL | 0.0 FAIL | 0.25 FAIL |
| 3 | KEEP | 2/7 | 1.0 PASS | 0.75 PASS | 0.0 FAIL | 0.25 FAIL |

GEO-1 flipped 0.25→1.0→1.0; GEO-2 flipped 1.0→0.25→0.75; GEO-7 flipped 1.0→0.25→0.25. **The evaluator cannot be treated as an oracle.** This invalidates "single source of truth = evaluator scores" for Goodhart-style selection unless measurements are averaged. Likely cause: parallel session load on `gemini-3.1-pro-preview`.

### N-2. `weekly_digests` table missing the unique constraint — UPSERT silently creates duplicate rows

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` L5545, L7220, L15958 — three distinct UUIDs persisted in one session

The UPSERT SQL at `src/monitoring/repository.py:1500-1526` declares `ON CONFLICT (monitor_id, week_ending) DO UPDATE` but the **unique constraint itself is absent from the runtime schema**. The table was created on the fly without the unique index. Result: every `freddy digest persist` call creates a NEW row. Three IDs in this session: `5ff65b86-...`, `1dfec582-...`, `c39084b9-...`. `results.jsonl` iteration 2 records `1dfec582`, iteration 4 records `c39084b9` — **two different values in the same session**.

**Fix:** `ALTER TABLE weekly_digests ADD CONSTRAINT weekly_digests_monitor_week_key UNIQUE (monitor_id, week_ending);`

### N-3. Atomic-write pattern wedges shell when producing command stalls with no output

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L1164-L1341, 134572ms total, exited -1

```sh
freddy visibility --brand semrush ... > competitors/visibility.json.tmp && mv visibility.json.tmp visibility.json
```

When `freddy visibility` wrote zero bytes, the shell blocked on the `>` redirection AND the subsequent `mv`. Even `kill PID` took ~2.25 minutes because zsh waits for the pipeline to finish before registering SIGTERM. **Every freddy command using this atomic-write pattern has the same failure mode.**

**Fix:** Add `timeout 60` prefix to every freddy CLI call in program prompts, OR add `--timeout N` flag to `freddy` itself.

### N-4. `FREDDY_API_KEY` is not propagated into the storyboard session environment

**Source:** `sessions/storyboard/MrBeast/logs/multiturn_session.log` L600-601, L1088-1524

The storyboard program uses direct `curl` to hit `/v1/creators/youtube/MrBeast/videos`. **First curl attempt returned `401 missing_credentials`**. The agent had to:
1. Search the repo for "FREDDY_API_KEY" references (L1093-1218)
2. Read `.env` and confirm it's absent (only `FREDDY_API_URL` is there)
3. Read `cli/freddy/config.py` to discover `~/.freddy/config.json` fallback
4. Read the config directly and inject the key into each curl call

**Cost: ~5 minutes on auth bootstrapping.** The other 3 sessions use `freddy` CLI wrappers which read from `~/.freddy/config.json`. Storyboard is the only program that uses raw curl.

**Fix:** Export `FREDDY_API_KEY` in the harness env before spawning the storyboard codex subprocess (the harness already exports `FREDDY_API_URL`).

### N-5. Agent over-optimizes on KEEP decisions — burns 4 eval cycles on monitoring digest

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` L8972, L10690, L12450, L14202, L15563

All 5 monitoring evaluator calls returned `decision: KEEP`. The first 4 had `reason: 1_of_7_evaluated_failed`, the 5th returned `0_of_7_evaluated_failed`. The agent kept rewriting `digest.md` trying to satisfy the remaining failed criterion **despite the evaluator explicitly KEEPing it each time**.

MON-1 went PASS 1.0 → FAIL 0.0 (after tightening) → PASS 1.0. MON-8 went FAIL 0.25 → PASS 1.0. The "0 failed criteria" final state is an **illusion of convergence** — eval 5 might just be the lucky draw given the evaluator non-determinism (N-1).

**Fix:** Program prompt should explicitly say "KEEP means STOP, do not iterate to reduce failed criteria count."

---

## HIGH severity (new)

### N-6. Competitive brief DISCARDED on structural gate — undocumented rework cycle

**Source:** `sessions/competitive/figma/logs/multiturn_session.log` L10890-10896

First eval returned:
```json
{
  "decision": "DISCARD",
  "reason": "structural_gate_failed",
  "gate_failures": ["Brief is 2089 words (max 2000)"],
  "results": []
}
```

Agent trimmed 89 words to get to 1830. Competitive session actually completed in **2 evaluator cycles** (DISCARD → KEEP), not 1 as first-pass implied. Structural gate DISCARDS are silent hard constraints — no LLM judgment, no per-criterion feedback.

### N-7. `findings_count` counter is broken across ALL 4 lanes, not just competitive

**Source:** `scripts/summarize_session.py:110` — `len(re.findall(r"^### \[", findings_file.read_text(), re.MULTILINE))`

Cross-lane regex mismatch:
- **geo/semrush**: `### [CONTENT] ...` → 8 matches ✓ (reported 8)
- **monitoring/Shopify**: `### [LOW_VOLUME] ...` → 4 matches ✓ (reported 4)
- **competitive/figma**: `### CONTENT Canva ...` (no brackets) → 0 matches ✗ (actual: 7)
- **storyboard/MrBeast**: `- CONTENT: MrBeast ...` (bullet) → 0 matches ✗ (actual: 7)

**Fix:** Either tolerate all three formats in the regex OR standardize findings.md templates across programs.

### N-8. `storyboard/MrBeast/session_summary.json` has `iterations.total=4, productive=8` — nonsensical

**Source:** `results.jsonl` has 8 entries where `iteration: 4` appears 5 times (once per storyboard ideation)

Productive cannot exceed total. The storyboard program writes **5 `ideate` phases as "iteration 4"** — all with the same iteration number, different `storyboard_id`. Summary dedupes by iteration then counts all entries.

**Fix:** Each ideate should be a distinct iteration (4, 5, 6, 7, 8), OR the summary should collapse them.

### N-9. apply_patch failures due to template drift and file confusion

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L22767 and `sessions/monitoring/Shopify/logs/multiturn_session.log` L661

Two apply_patch failures on findings.md:
1. **Template drift**: monitoring's findings.md uses `(empty)` sentinels from the program prompt while the actual scaffolding uses HTML comments. First apply_patch ALWAYS fails in monitoring.
2. **Wrong-file patch**: geo's patch "expected context" for findings.md contained results.jsonl JSON entries — codex conflated two files in the same turn.

**Fix:** Standardize findings.md templates across all 4 programs to use the same sentinel style.

### N-10. 401→400→400→400 cascade in first 16 seconds of competitive session

**Source:** `sessions/competitive/figma/logs/multiturn_session.log` L599-628

Within one iteration the agent hit: `validation_error` (search-content), `Missing option '--brand'` (visibility contract drift), 3× `ic_bad_request_400` credit exhaustion, and `internal_error reference: 434ab930` (adobe scrape 500). **First-pass missed the 500 reference code** — a backend 500 with a stable reference is an observability signal that should be surfaced to ops, not swallowed.

### N-11. Parallel codex processes hammer backend/Gemini concurrently

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L1328-1331 + session log mtimes

`ps -ef` output shows two concurrent codex exec processes at 12:20PM. Combined with 4 sessions launching within 23 seconds, this confirms **true parallel execution on one machine**. Implications:
- Gemini rate limiting contributes to evaluator non-determinism (N-1)
- freddy backend contention (4 concurrent search-ads, detect, visibility)
- Postgres contention (4 parallel scrape/digest/monitor writes)

**Fix:** Consider serializing sessions in the harness, OR pin each to a distinct Gemini quota.

---

## MEDIUM severity (new)

### N-12. Monitoring LOAD_CONTEXT read stale archived session data from 3 days ago

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` L2317-2354

The agent ran `sed` on `sessions/_archive/20260410-160051-monitoring-Shopify/session.md` and pulled in an **old session from monitor_id 2fedd1de, week ending 2026-03-22**. The archived session.md said:
> `Context load: freddy digest list --limit 4 failed with internal_error (ref f9273cc2), so prior-digest delta framing was unavailable.`

The **current** run's `freddy digest list` succeeded with `[]`. But the archived failure bled into current reasoning. **Cross-session context bleed** from `_archive/` directories.

**Fix:** Program prompts should require LOAD_CONTEXT to only read the current session directory, not globbed `_archive/*`.

### N-13. `freddy monitor baseline` was NEVER called — first-pass audit was wrong

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` — grep `freddy monitor baseline` returns zero exec invocations

First-pass claimed "generated commodity baseline." **This is incorrect.** The low-volume shortcut skipped it. No `baseline.json` exists in the session dir. The baseline command runs during preflight checks (where we confirmed it works), but the actual session never invoked it.

### N-14. `freddy search-ads figma.com` baseline returned only 2 ads — Foreplay coverage gap

**Source:** `sessions/competitive/figma/competitors/_client_baseline.json`

Canva returned 100 clean ads; Figma's own baseline is **50x less ad volume**. This skews analysis into overweighting perceived Canva threat. First-pass mentioned "2 community ads" without framing the scale mismatch as an issue.

### N-15. YouTube creator endpoint returns degenerate schema — all records null on posted_at AND duration

**Source:** `sessions/storyboard/MrBeast/selected_videos.json` + storyboard log L1526-1560

ALL 17 selected videos have `posted_at: null` AND `duration_seconds: null`. Only `play_count`, `title`, `video_id` populated. Agent forced to:
- Set `recency: unavailable_posted_at_null`
- Use play_count-only as ranking signal
- Heuristically filter by title keyword

**Fix:** Investigate the YouTube fetcher — likely hitting external quota and falling back to cached-only-basic-field path.

### N-16. Excessive log bloat — diff context of same few lines repeated 79× per session

**Source:** `grep -c "Record approaches that failed or regressed quality" *.log`

- geo: 79 repetitions
- monitoring: 35 repetitions
- competitive: 52 repetitions
- storyboard: 9 repetitions

Each codex exec tool call includes a git diff of the session directory, which re-prints findings.md's HTML comment on every turn. For geo's 87 exec calls, 91% re-print this context. **This is why geo's log is 6.3 MB.**

**Fix:** Disable diff-context inclusion for large files, or only include changed ranges.

### N-17. First-pass framing of "25/32 mentions loaded, 7 missing" is wrong

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` L406-408

Backend response returned `{"count": 25, "total": 25}`. **The backend's own `total` field is 25** — it's not filtering 25 out of 32. The DB only has 25 mentions for the queried window. This is a **seed-script off-by-one bug** (no mentions for 2026-04-06) not a fetch bug.

### N-18. Competitive gather phase fires 8 parallel freddy commands in a single codex turn

**Source:** `sessions/competitive/figma/logs/multiturn_session.log` L568-590

8 distinct `exec` calls (search-ads × 4 domains, detect × 3, visibility × 1) in ONE turn. Codex batched them. Adobe search-ads failure with `AllProvidersUnavailableError` at L577 **might be caused by** rate-limiting from sibling calls.

**Fix:** Serialize the gather phase to ≤2 concurrent calls if upstream providers are brittle.

### N-19. Storyboard plan_story required full rework on attempt 2 — first-pass was wrong

**Source:** `sessions/storyboard/MrBeast/logs/multiturn_session.log` L6125 "EVAL 3" REWORK 4/8

First-pass: "all passing evaluator on second pass." **Reality:** first pass got REWORK on plan 3 (SB-1 and SB-2 at 0.25 FAIL, 4/8 overall). Agent regenerated all 5 stories. Second pass: 0/8 fail. The sequence was `5 evals pass 1 → REWORK 1 plan → regenerate ALL 5 → 5 evals pass 2 → 0/8 fail`. `results.jsonl` records `attempt: 2` confirming this.

### N-20. Four evaluator invocations on geo/pricing.md, not three

**Source:** L3553, L6544, L8763, L11341 — four distinct eval calls for pricing.md

First-pass implied 3. L3553 is a pre-optimization baseline run. **4 × ~30-35s = ~2 minutes of pricing-only eval time.**

---

## LOW severity / observations

### N-21. jq command emits "Cannot index string with string" errors from zsh escape confusion

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L1147-1152 + `sessions/competitive/figma/logs/multiturn_session.log` L1452

6 jq errors in geo, 1 in competitive. Codex-generated shell commands have escape-sequence issues in zsh-wrapped subprocess. Agent recovered by reading files directly. Harmless but indicates **codex's complex shell-command generation has escape bugs**.

### N-22. `jq --rawfile md digest.md` failure due to cwd mismatch

**Source:** `sessions/monitoring/Shopify/logs/multiturn_session.log` L13192-13194

```
jq: Bad JSON in --rawfile md digest.md: Could not open digest.md: No such file or directory
```

Agent used relative path but actual cwd was `autoresearch/archive/v001` not the session dir. **cwd-relative path assumption fails** in codex-generated commands.

**Fix:** Program prompts should require absolute paths in all generated commands.

### N-23. Codex `write_stdin failed: stdin is closed` noise during subprocess cleanup

**Source:** `sessions/geo/semrush/logs/multiturn_session.log` L1306

Noted in first-pass as benign. It's from codex's internal tool-dispatcher trying to manage a shell subprocess that already died. Zero cost but adds log noise.

### N-24. Storyboard ideate entries report `eval_score: null`

**Source:** `sessions/storyboard/MrBeast/results.jsonl` lines 4-8

All 5 ideate records have `"eval_score": null`. Program prompt specifies `eval_score: N.N`. The backend mock mode returns no eval data, so the program should have a fallback. **Program oversight** — the IDEATE phase doesn't handle mock mode gracefully.

### N-25. Backend validation errors are generic — no field name, no hint

**Source:** L599-613 — three `{"error": {"code": "validation_error", "message": "Request validation failed"}}` responses back to back

No field name, no request body echo, no hint about WHICH validation failed. **Backend validation errors should include specific field or rule** so agents can self-correct in one cycle instead of probing `--help`.

### N-26. Geo apply_patch count (31) is 3× iteration count — heavy file thrashing

**Source:** `grep -c "^apply patch$"` per log

- geo: 31 patches / 10 iterations = 3.1/iter
- competitive: 11 / 6 = 1.8/iter
- monitoring: 9 / 4 = 2.25/iter
- storyboard: 16 / 9 = 1.8/iter

Geo's 3.1× patches/iter is from the 4× pricing.md eval retry loop. Evolution could target reducing iteration-internal apply_patch churn.

### N-27. Evaluator calls dominate ~15% of session wall time on average

Per-session eval time estimates:
- **geo**: ~350s eval / 1898s total = ~18%
- **storyboard**: ~205s / 1271s = ~16%
- **monitoring**: ~89s / 675s = ~13%
- **competitive**: ~34s / 978s = ~3%

Combined with repeated eval calls (N-5) and parallel Gemini contention, **per-call eval latency is ~2-3× what it should be**. Serializing sessions or distributing Gemini quota would recover most of this.

---

## Contradictions with first-pass audit (corrections)

1. **"freddy monitor baseline — generated commodity baseline"** → command was NEVER called (N-13)
2. **"25 mentions loaded out of 32 seeded — 7 mentions lost"** → DB only has 25 to begin with; seed fixture has a 2026-04-06 day gap (N-17)
3. **"5 story plans produced, all passing evaluator on second pass"** → first pass was REWORK 4/8; regeneration required (N-19)
4. **"Competitive phase progression 6 iterations"** correct count but hides DISCARD→KEEP rework in iteration 6 (N-6)
5. **"Monitoring 4 iterations"** correct by results.jsonl but hides 5 eval invocations and 3 distinct persisted digest IDs (N-2, N-5)

---

## Top priorities for fixes before next run

1. **Fix `weekly_digests` unique constraint** — migrate table to add `UNIQUE (monitor_id, week_ending)` (N-2)
2. **Propagate `FREDDY_API_KEY` into storyboard session env** via harness (N-4)
3. **Add `timeout 60` prefix to freddy commands** in program prompts, OR add `--timeout` flag to `freddy` CLI (N-3)
4. **Fix `summarize_session.py:110` regex** to handle all 4 lanes' findings.md formats (N-7)
5. **Remove diff-context inclusion for large files** — reduces log bloat ~85% in geo (N-16)
6. **Standardize findings.md sentinel style** across all 4 programs to fix apply_patch mismatches (N-9)
7. **Guard program prompts against over-optimizing on KEEP** — KEEP means STOP (N-5)
8. **Serialize sessions or pin to distinct Gemini quotas** to reduce evaluator non-determinism (N-1, N-11)
9. **Fix storyboard iteration numbering** — 5 ideate phases should be iterations 4-8 not all "4" (N-8)
10. **Require absolute paths in program-generated commands** (N-22)
11. **Forbid reading from `_archive/*` in LOAD_CONTEXT** (N-12)
12. **Investigate YouTube fetcher degenerate schema** (null posted_at + duration) (N-15)
