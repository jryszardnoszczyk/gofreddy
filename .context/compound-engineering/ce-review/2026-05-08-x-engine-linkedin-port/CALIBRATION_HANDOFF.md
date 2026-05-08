# Post-compact handoff — judge stability calibration

You are continuing work on `feat/x-engine-linkedin-port` after a `/compact`.

## Branch state (as of this handoff, pre-compact)

- Worktree: `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/.worktrees/x-engine-linkedin-port`
- Branch: `feat/x-engine-linkedin-port` — 23 commits ahead of `main`, 0 pushed.
- Tests: 615 passed + 2 skipped (pytest.skip carve-outs for empty-on-both lanes) on `tests/autoresearch/ x_engine/tests/ tests/judges/ tests/freddy/fixture/test_refresh_*.py tests/freddy/fixture/test_staleness_*.py`. `tests/harness/` runs separately (conftest conflict; pre-existing) — 163 pass.
- Hard rule: do NOT push the branch. JR pushes + opens PR.
- Hard rule: do NOT compact further or re-review the master plan. v13 is locked + 2 review passes shipped.

## What's complete

- L0 (judge-service two-template scorer dispatch — shipped on main as `77f536d`).
- L1 (6 units): DB schema + migration + new tables; mark-posted/skip-draft critical-path; angle-show/list/holdout-export; slop_gate platform-aware; LinkedIn Apify pipeline + BrightData scaffold; LaunchAgents + batch CLI.
- L2 (14 units): §3.1 cull; rubrics.py 12 prose blocks + assert bump 32→44; lane_registry LaneSpec entries; models.py Literal; voice.md substrate scaffold; per-lane session.md + evaluation-scope.yaml; WorkflowSpec ×2 (mirror competitive.py); SessionEvalSpec ×2 (mirror session_eval_geo.py); workflow registries + evaluate_session.py argparse; pytest.skip carve-out; eval_suites/SCHEMA.md+TAXONOMY.md+search-v1.json; evolve LaunchAgents; structural completion (templates dirs, sources.json, fixture scaffolds).
- ce:review autofix (10 reviewers): 10 P0/P1/P2 fixes — UNIQUE constraint, atomicity, slop-check error handling, run.sh stub, session.md decision-tracking, etc. Run artifact: `.context/compound-engineering/ce-review/2026-05-08-x-engine-linkedin-port/findings.md`.
- document-review autofix (4 reviewers): 10 content fixes — hashtag mismatch, slop self-contamination, null source_text handling, cohort decision rule, structural-gate explanation, cold-start hand_drafts, em-dash policy. Run artifact: `.context/compound-engineering/ce-review/2026-05-08-x-engine-linkedin-port/document-review-findings.md`.

## Your task: author the judge stability calibration script

This is the pre-L2-evolution F4 gate. Engineering-only. JR runs it after.

### Spec

Build `scripts/calibrate_judge_stability.py` (new file).

**Inputs:**
- `--domain x_engine|linkedin_engine`
- `--drafts-dir <path>` (defaults to `tests/fixtures/calibration/<domain>/`)
- `--runs N` (default 2 — independent invocations per draft)
- `--output <path>` (markdown report; defaults to stdout)

**Behavior:**
1. Read all `*.md` drafts from `drafts-dir`.
2. For each draft, call the judge service `--runs` times. Use the same call shape as `autoresearch/evaluate_variant.py:1101-1184` (POST `EVOLUTION_JUDGE_URL/invoke/score` with `{domain, session_ref, fixture_id, fixture, suite_id, campaign_id=None, variant_id=None, artifacts}`). Bearer-auth with `EVOLUTION_INVOKE_TOKEN`.
3. Parse each response per `judges/evolution/agents/variant_scorer.py:score_variant` shape — `{primary, secondary, aggregate}`. Use `aggregate.aggregate_score` and `primary.per_criterion[].score` for per-dimension scoring.
4. Compute per-dimension variance across the N runs. For N=2, variance = `abs(score_run1 - score_run2)` per criterion per draft.
5. Compute cohort-fit variance for X-6 / LI-6 (the cross-item dimension).
6. Compute judge-family agreement: `abs(primary.aggregate_score - secondary.aggregate_score)` per draft.
7. Output a markdown report with 3 tables:
   - **Per-dimension variance** (rows: X-1..X-6 or LI-1..LI-6; columns: avg variance, max variance, # drafts with ≥2 variance)
   - **Cohort-fit variance** (X-6 or LI-6 across the cohort)
   - **Judge-family agreement** (per draft: primary score, secondary score, abs diff)
8. **Pass/fail gating:** any dimension with max variance ≥ 2.0 → exit code 1 + report flags it. All dimensions ≤1.5 max → exit 0 + report says PASS.

**Out of scope:**
- Generating drafts (use the fixtures committed in `tests/fixtures/calibration/`).
- Running against a live judge service (JR runs the script after; you just author it).

### Sample fixtures to commit

Author 6 sample drafts under `tests/fixtures/calibration/`:

**`tests/fixtures/calibration/x_engine/`** — 3 drafts spanning the 3 X length brackets:
- `sharp.md` (250-300 chars, sharp claim+support, voice_pillar=harness-engineering)
- `build.md` (500-900 chars, prose intro + bullets + outcome metric, voice_pillar=marketing)
- `case-study.md` (1000-1500 chars, narrative + numbers + implication close, voice_pillar=harness-engineering)

**`tests/fixtures/calibration/linkedin_engine/`** — 3 drafts spanning the 3 LinkedIn brackets:
- `short_take.md` (500-900 chars, story-opening + paragraph + close, 3 hashtags, voice_pillar=B2B-marketing)
- `thought_leader.md` (1500-2500 chars, story → frame → bullets → close, 4 hashtags, voice_pillar=harness-engineering)
- `case_study.md` (2500-3000 chars, multi-paragraph narrative + numbers + named characters, 5 hashtags, voice_pillar=marketing)

Each draft must:
- Conform to the §2.2 frontmatter + [BODY] + [META] format.
- Reference only entities in `voice.md` Section 3 (gofreddy, autoresearch, x_engine, Hermes, etc.) — NO fictional clients.
- Pass the `xeng slop-check --platform <x|linkedin>` regex floor (test by running it manually before committing).
- Have varied hook archetypes within each domain so X-6 / LI-6 cohort-fit scoring isn't trivially gameable.

These are calibration drafts — they exist to test judge stability, not to be production-quality. JR can replace later with real drafts; the structure is what matters for variance testing.

### Tests

Add `tests/scripts/test_calibrate_judge_stability.py`:
- Mock the judge HTTP response with two payloads showing known variance.
- Verify the script computes variance correctly.
- Verify exit code 1 when any dimension ≥2 variance.
- Verify exit code 0 when all dimensions ≤1.5.
- Verify markdown report contains the 3 tables.

### Commit message convention

`feat(scripts): judge stability calibration script + sample fixtures (pre-L2 F4 gate)`

Per master plan v13 §7.3 + the document-review feasibility-reviewer P0 finding.

## What you should NOT do

- Do not push the branch. JR pushes when calibration passes + operator gates clear.
- Do not invoke the calibration against a live judge service. The script is engineering output; JR runs it.
- Do not modify the lane port code (rubrics.py, lane_registry.py, WorkflowSpec/SessionEvalSpec, session.md). Two review passes shipped; further changes are JR's design decisions per the residuals listed in the run artifacts.
- Do not re-review the lane port. The 14 reviewers (10 ce:review + 4 doc-review) covered it.
- Do not extend scope beyond the calibration script + fixtures + test.

## When you finish

1. Run `pytest tests/scripts/test_calibrate_judge_stability.py x_engine/tests/ tests/autoresearch/ -q` — must be green.
2. Commit per the convention above.
3. Surface to JR: "calibration script + 6 fixtures + tests shipped. Run via `python3 scripts/calibrate_judge_stability.py --domain x_engine` once `EVOLUTION_JUDGE_URL` + `EVOLUTION_INVOKE_TOKEN` are in env."
4. Stop. The branch is now ready for JR's calibration run + decision on residuals + push + PR.

## JR-side residuals to remember (NOT yours)

These are documented in the two run artifacts; JR decides post-calibration:

- **AUTOMATIC caps in `_X_1`/`_LI_1`** — feasibility + adversarial agreed they're under-specified. Choose: remove caps OR enumerate triggering term list.
- **`_X_6`/`_LI_6` simplification** — 3-reviewer agreement on dropping geometric-mean per-draft subscoring; rewrite as direct cohort gradient.
- **HARD FLOOR triggering criteria in `_X_2`/`_LI_2`** — enumerate 3-4 "specific lived-work claim" patterns.
- **JR exemplar tweets in voice.md Section 3** — 2-3 verified posts as judge calibration anchors.
- **Hashtag list per pillar** in `linkedin_engine-session.md`.

## Operator gates JR must clear before push

- Live state.db migration (`python3 -c "from x_engine.pipeline.db import migrate_state_db; migrate_state_db()"`)
- Apify + Bright Data subs + `APIFY_TOKEN` + `BRIGHTDATA_TOKEN` env
- `sources_linkedin.yaml` populated with ~50 creators + ~20 keywords
- `launchctl load com.jryszardnoszczyk.x-engine.plist` (start 14d dogfood clock)
- Cold-start LinkedIn drafts (5 ship + 5 skip) hand-written by JR
- 14d X-dogfood produces ≥25 marks (verified via `xeng holdout-export`)
