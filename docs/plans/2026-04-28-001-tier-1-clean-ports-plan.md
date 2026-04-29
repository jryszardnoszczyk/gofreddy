# Tier-1 Clean Ports Plan

**Date:** 2026-04-28
**Branch:** `feat/tier-1-clean-ports` (cut from `main` @ `c61b2ee`)
**Source:** `freddy@50602a2`
**Estimate:** 1–2 working days, single PR

## Why this branch exists

Three clean ports remain after the comprehensive 3-reviewer audit (2026-04-28). Each is genuinely portable from freddy (no SaaS coupling), genuinely useful (real agency capability), and genuinely small (single file, < ½ day each). Single PR, no chore-PR splits.

## The three units

### T-1 — `autoresearch/geo_verify.py`
- **Source:** `freddy/autoresearch/geo_verify.py` (205 LOC, executable)
- **Plus:** `freddy/autoresearch/geo-verify.sh` (50 LOC shell wrapper) and `freddy/autoresearch/tests/test_geo_verify.py` (~265 LOC)
- **Target:** mirror paths in gofreddy
- **What it does:** re-runs visibility queries on a completed GEO/SEO session and diffs against baselines. Calls `freddy visibility` CLI via subprocess (already present at `cli/freddy/commands/visibility.py`). Pure stdlib + `.env` loader. Closes the audit→ship→verify loop.
- **Acceptance:**
  - `python autoresearch/geo_verify.py --help` parses
  - `pytest autoresearch/tests/test_geo_verify.py` passes
  - Verify imports work — no orchestrator/SaaS deps reach in

### T-2 — `src/brands/exposure.py`
- **Source:** `freddy/src/brands/exposure.py` (173 LOC)
- **Target:** `gofreddy/src/brands/exposure.py` (creates `src/brands/__init__.py`)
- **What it does:** brand-screen-time + multi-video aggregation math. Interval-merge analysis, source/sentiment/context breakdowns, multi-video campaign rollup. Pure functions over pre-existing schemas (`BrandAnalysis`, `BrandMention`, `BrandExposureSummary`, `MultiVideoBrandExposure` already in `src/schemas.py`).
- **Imports verified clean:** `mss_to_seconds` from `src/common/timestamps.py` (present); the 4 brand schemas (all present).
- **Acceptance:**
  - Module imports without error from gofreddy
  - Add 3-5 unit tests covering: single-brand interval-merge, multi-source dedup, multi-video aggregation, empty-input edge cases
  - `mypy --strict src/brands/exposure.py` clean (or matches existing project lint config)

### T-3 — `src/content_gen/output_models.py`
- **Source:** `freddy/src/content_gen/output_models.py` (64 LOC)
- **Target:** `gofreddy/src/content_gen/output_models.py` (creates `src/content_gen/__init__.py`)
- **What it does:** frozen Pydantic schemas for 5 content asset types (`SocialPost`, `NewsletterContent`, `VideoScript`, `AdCopyVariant`, `RewriteVariant`). Drop-in scaffolding for any future content-generation work; doesn't ship generation logic itself.
- **Acceptance:**
  - All 5 models load + JSON-roundtrip
  - Add a small `tests/test_content_gen_output_models.py` with one roundtrip test per model

## Out of scope (do not include)

- `content_gen/{config,exceptions}.py` — kept for whenever content-gen rewrite ships, not now
- Tier-2 GEO scripts (monthly_validation, monthly_comparison) — separate branch when monthly GEO becomes a real agency workflow
- Any `cli/freddy/commands/` additions — Tier-1 is library + autoresearch script only

## Sequencing

1. **T-3 first** (smallest, schema-only — warms up the test harness)
2. **T-2 second** (small, pure math, isolated tests)
3. **T-1 last** (largest, has its own test file to port verbatim)

## Branch hygiene

- Cut fresh from `main` @ `c61b2ee` (do not branch off the merged port-gaps branch)
- Single PR titled "feat: tier-1 clean ports — geo_verify + brands/exposure + content_gen/output_models"
- Each unit is its own commit; PR description cites this plan + links the audit summary
- Run `uv run --extra dev pytest tests/test_clients_models.py tests/deepfake/test_models.py tests/brands/ tests/test_content_gen_output_models.py autoresearch/tests/test_geo_verify.py -q` as the merge gate

## What this branch is NOT

- Not a re-port of the things already explicitly rejected in `docs/plans/2026-04-27-001-fred-port-gaps-checklist.md` decision log
- Not the audit-engine work (that's `feat/audit-engine-implementation`, separate)
- Not a content-generation engine — only the output-shape schemas

## Decision log

**2026-04-28:** Comprehensive 3-reviewer audit (full src/ scan + CLI/scripts/autoresearch sweep + utility/helpers walk) confirmed Tier-1 as the highest-leverage remaining clean ports. Three of the four "agency-capability" candidates from prior conversations (publish/media/rank CLIs) were withdrawn — verified as pure SaaS HTTP shells, no portable logic. The ~1.5–2 week estimate from the prior conversation was wrong; real Tier-1 surface is 1–2 days.

**Lesson:** read the actual file before estimating effort. Inventory descriptions of CLI commands didn't reveal that the entire body was `api_request(...)` calls until a reviewer opened them.
