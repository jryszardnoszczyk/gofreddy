# Fixture Program Execution Plan (Plan B of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the infrastructure from Plan A to author `holdout-v1` (16 adversarial fixtures, out-of-repo), modestly expand `search-v1` (6-8 new fixtures filling coverage gaps), migrate existing search-v1 fixtures onto the new infrastructure, validate the whole design with an overfit-canary experiment, and enable agent-delegated autonomous promotion with a wrong-lane-prevention invariant.

**Architecture:** Content-heavy work driven by a shared taxonomy matrix (6-axis grid of domain × language × geography × vertical × adversarial-axis × stressed-rubric-criteria). Every fixture lands in exactly one cell and exactly one pool. Holdout lives outside the repo at `~/.config/gofreddy/holdouts/holdout-v1.json`; search expansion lands in-repo at `autoresearch/eval_suites/search-v1.json` (version-bumped to 1.1). Promotion is agent-driven: `is_promotable` gathers the full scoring context (primary + secondary judges across all fixtures, holdout eligibility, first-of-lane baseline status, per-fixture win-rate) and delegates the promote/reject decision to the promotion agent. No hardcoded epsilon, no hardcoded win-rate cutoff, no fixed gate count — the agent reads the full picture and reasons.

**Tech Stack:** Plan A's `freddy fixture` CLI (`validate`, `list`, `envs`, `staleness`, `refresh`, `dry-run`, `discriminate`), Codex/gpt-5.4 judge via `freddy evaluate`, existing `evolve.sh`. No new runtime dependencies.

**Prerequisite:** Plan A Phases 1–8 must land before Plan B Phase 2 Steps 0–6; Plan A Phase 10 must land before Phase 2 Step 7 (uses `freddy fixture discriminate`). All Plan A Acceptance Criteria must pass before enabling autonomous promotion — the holdout cache-miss hard-fail, pool/suite_id match check, pool-dependent cache-read policy, and content-hash drift detection all live in Plan A and are verified by its acceptance tests. Phase 1 of this plan (taxonomy matrix) is pure design work and can be drafted in parallel with Plan A from day one.

## Post-Plan-A implementation notes (added 2026-04-23)

Plan A shipped on `feat/fixture-infrastructure` (17 commits since main). Four things affect Plan B's phase text:

**1. Refresh CLI-signature bug (HARD BLOCKER for Phase 2 + Phase 4 Step 1).** `cli/freddy/fixture/sources.json` passes `fixture.context` as a positional arg to every source command. This works for `freddy scrape <url>` + `freddy monitor {mentions,sentiment,sov} <uuid>` but breaks for `freddy visibility` (needs `--brand`), `freddy search-ads` (rejects plain names — needs valid domain), and `freddy search-content` (needs `--platform`). Follow-up fix plan: `docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md`. **Until this fix ships, Plan B Phase 2 fixtures must be restricted to geo-scrape + monitoring-UUID domains, OR the composition table's visibility / search-ads / search-content rows must wait.** Phase 4 Step 1 `--all-stale` batch refresh will error out on any visibility/ad/content source.

**2. Holdout loader guards — 1 of 3 already shipped.** Plan B Phase 2 Step 9e lists three `_load_holdout_manifest` guards: (a) in-repo-path refusal, (b) 600-perm check, (c) `is_redacted_example` sentinel. Plan A gap-closure commit `0892ec1` shipped (c). When executing Step 9e, **only add (a) and (b)** — the sentinel guard already exists.

**3. Content-drift plumbing already shipped.** Plan B Phase 4 Step 1 presents content-drift as work-to-do: extend `DataSourceRecord` with `content_sha1`, emit `kind="content_drift"` in `_run_source_fetch`. Both are done. `cli/freddy/fixture/cache.py::DataSourceRecord` has `content_sha1: str = ""`; `cli/freddy/fixture/refresh.py::_run_source_fetch` emits the event. The Phase 4 Step 1 code block is a **reference implementation for the prose** — not a patch to apply. Skip it; verify via `rg "kind=\"content_drift\"" cli/freddy/fixture/refresh.py`.

**4. Operational dependencies not in original prereq list.** Plan B execution requires, in addition to the architectural prereqs:
- **gofreddy backend** running at `FREDDY_API_URL` (default `http://127.0.0.1:8000`). Boot: `uvicorn src.api.main:app --host 127.0.0.1 --port 8000`.
- **Supabase postgres** at `127.0.0.1:54322` (the backend's DB). Boot: `supabase start`.
- **Judge services** from Plan A Phase 0c. Boot: `source .venv/bin/activate && JUDGE_MODE=session INVOKE_TOKEN=$(cat ~/.config/gofreddy/session-invoke-token) uvicorn judges.server:app --host 127.0.0.1 --port 7100 &` + same for evolution on 7200. These don't survive terminal close with `nohup`; re-run on every fresh shell.
- **Provider credentials** in `.env`: `OPENAI_API_KEY`, `DATAFORSEO_LOGIN/PASSWORD`, xpoz + monitor UUIDs for monitoring fixtures. Same creds Plan A Phase 0 Step 4 needed.
- **Judge tokens + URLs** in `~/.config/gofreddy/judges.env`. Source via `source ~/.config/gofreddy/judges.env` in any shell that calls `freddy fixture dry-run` or the promotion/rollback path.

**5. Realistic wall-clock costs.** Each `freddy fixture dry-run --seeds 5` spawns 5 full variant sessions via `_run_fixture_session`. On `geo-semrush-pricing` with `max_iter=15, timeout=1200`, one session is minutes to hours. Phase 5 Step 3's `./autoresearch/evolve.sh run --iterations 20 --candidates-per-iteration 3` produces 60 candidate variants × ~N fixtures each — budget days of wall-clock, not hours.

**Security posture:**

- *Accepted:* monitoring content drift during canary (see Phase 5 timing constraint); upstream fixture URL compromise (content-hash drift detection warns on next refresh — see Phase 4 Step 1).
- *Mitigated:* provider-side telemetry and holdout credential exfiltration — holdout refresh runs on process-boundary-isolated infrastructure (GitHub Actions; see Phase 2 Step 9f). The evolution machine receives refreshed cache artifacts only via `gh run download`, never the credentials. Local-dev fallback (`--isolation local` + `~/.config/gofreddy/holdouts/.credentials`) exists as a documented trust-boundary shortcut; production runs using `local` must call it out in the commit message.

**Out of scope (separate initiatives, not postponed):** MAD confidence scoring, `lane_checks.sh` gates, lane scheduling rework, IRT benchmark-health dashboard, full MT-Bench-style judge-calibration harness, pinned-history snapshot cache (blocked by 30-90 day provider retention — holdout-v2 bump waits on snapshot-cache infrastructure that no provider currently offers).

---

## MVP carve-out (added 2026-04-23 after multi-persona plan review)

Four sub-systems in this plan were originally speccied as "in-scope for Plan B." Review surfaced that each either (a) ships in dry-run-only mode, (b) builds infrastructure for a failure mode that has not been observed, or (c) blocks MVP delivery behind multi-week operator work whose value isn't realized until after Plan B ships. These are now **deferred to named follow-up plans**; their original content remains in the phase text for reference but must NOT be implemented as part of Plan B.

| Deferred scope | Original location | Follow-up plan | Reason |
|---|---|---|---|
| **16-row holdout composition** — full matrix across geo + competitive + storyboard + monitoring | Phase 2 Step 0 composition table | [`docs/plans/2026-04-23-006-holdout-v1-composition-expansion.md`](2026-04-23-006-holdout-v1-composition-expansion.md) | 3 weeks of operator URL research conflicts with the 2-week Phase 2-5 timing constraint. MVP uses the 8-fixture alt path (2 anchor + 2 rotating, geo + monitoring only) — same discriminability check, sidesteps the refresh CLI bug. |
| **Automated rollback** (`check_and_rollback_regressions`, `ROLLBACK_DRY_RUN_UNTIL_ISO`, `ROLLBACK_COOLDOWN_CYCLES`, `head_score` event kind) | Phase 6 Step 6 | [`docs/plans/2026-04-23-003-automated-rollback.md`](2026-04-23-003-automated-rollback.md) | Plan itself admits rollback prompt is untuned at MVP and ships write-access-off until 2026-05-15. "Dry-run window" is calendar-gated, not audit-gated. Ships machinery without delivering a live safety rail. Start this follow-up once 1-2 real post-promotion regressions have been observed and logged. |
| **Judge calibration drift detection** (bi-directional cross-family, monthly cron, PR-gated baseline deploys) | Phase 4 Step 3b | [`docs/plans/2026-04-23-004-judge-calibration-drift.md`](2026-04-23-004-judge-calibration-drift.md) | Builds a drift-detection system before any drift has been observed. Keep log-only score-recording (record v001/v006/v020 monthly scores in `events.jsonl`) so data accumulates for the follow-up plan to reason about. |
| **Rotation-policy agent** (`mode=rotation_proposal`, monthly rotation-policy agent task) | Phase 2 Step 0b final paragraph + `docs/agent-tasks/rotation-policy.md` | [`docs/plans/2026-04-23-005-rotation-policy-agent.md`](2026-04-23-005-rotation-policy-agent.md) | Plan admits the agent is a 90-day no-op post-MVP (needs ≥3 months of saturation events before its output is useful). Static Phase 1 partition is authoritative until then. |

**Net:** MVP Plan B ships the autonomous promotion loop (`is_promotable` + promotion agent + canary validation + wrong-lane invariant) backed by 8 realistic holdout fixtures. The deferred sub-systems can be picked up once (a) the MVP is producing real trajectories, (b) the refresh CLI fix has shipped, and (c) enough time has elapsed for saturation/calibration data to accumulate.

**Execution-time rule:** if a phase step references deferred scope, skip it. Specifically:
- **Phase 2 Step 0** composition table: use the "Alternative: start with 8" note as the primary path, not the fallback.
- **Phase 2 Step 0b** rotation-policy agent paragraph + agent task spec: skip.
- **Phase 4 Step 3b** `judge_calibration.py`: skip; replace with a one-page log-only note that records v001/v006/v020 monthly scores.
- **Phase 6 Step 6** `check_and_rollback_regressions`: skip. Keep Steps 1-5 (`is_promotable` + wrong-lane invariant + promotion-judge wiring).

**Also deferred within Phase 6 (MVP simplification):** secondary per-fixture scoring on the promotion hot path (Phase 6 secondary-scoring setup). The promotion judge is already cross-family (Claude-based) w.r.t. the primary scorer (gpt-5.4). Doubling evaluation cost on every variant to preserve an additional cross-family invariant is not justified at MVP. Ship primary-only scoring; re-examine after the first month of autonomous promotion if single-judge gaming is observed.

**Phase 0 + Phase 0-A consolidation:** Phase 0 is a smoke-test of Plan A Phase 7 plumbing. Plan A Phase 7 already has its own acceptance tests. Fold Phase 0 into a small set of assertions inside Phase 2 Step A's first invocation instead of running it as a standalone phase. Phase 0-A ("golden fixtures") similarly overlaps with Phase 2 Step A's dry-run verdict check and is folded into it.

**Refresh CLI fix is a hard prerequisite** for the 16-row expansion follow-up but NOT for the MVP. MVP's 8-fixture alt path uses geo-scrape + monitoring-UUID sources only — both work with the current `args_from: ["context"]` signature.

---

## Pre-implementation operator inputs

Three things the operator provides before or during Plan B execution. These are NOT code; they can't be pre-filled in the plan. Each has a concrete slot in a specific phase. Budget ~4-5 weeks of semantic work total, woven through Plan B's execution.

| # | Input | Phase | Budget | What you produce |
|---|---|---|---|---|
| 1 | **Golden fixtures** (3-5 picks from real client work, representative-not-adversarial) | Phase 0-A Step 1 | ~half a day | 3-5 fixture specs tagged `"golden": true`, committed to `search-v1.json` |
| 2 | **8 holdout fixtures** (MVP default per carve-out: 2 anchor + 2 rotating per domain, geo + monitoring only). The 16-row composition is deferred to a follow-up plan. | Phase 2 Step 0 (fill the composition table) → Phase 2 Step A (authoring agent runs) | ~1.5 weeks | Populated `URL`, `Client`, `Env vars` columns for the 8 geo+monitoring rows; authoring agent handles formatting |
| 3 | **Holdout provider credentials** (register `HOLDOUT_`-prefixed accounts with xpoz, freddy scrape backend, OpenAI search; store keys) | Phase 2 Step 9f prereq | ~1 hour | Keys in `~/.config/gofreddy/holdouts/.credentials` (chmod 600) + `HOLDOUT_*_API_KEY` GitHub repo secrets |
| 4 | **6-8 search-v1 additions** (identified during Phase 3 Step 1 as you work the taxonomy gaps from Phase 1) | Phase 3 Step 1 | ~1-2 weeks | Scratch spec per fixture; existing primitives handle the rest |
| 5 | **Deliberately-overfit variant** for the Phase 5 canary | Phase 5 Step 2.6 | ~1 day | Prompt-diff against an in-repo variant that should score high on search-v1, low on holdout |

**These slot into the plan's execution — they're not separate work.** When you start Phase 0-A, Step 1 is "pick golden fixtures" — that's where the half-day goes. When you start Phase 2, Step 0 is "fill the composition table" — that's where the 3 weeks go. No phase starts without its input ready, and no input is gathered outside its phase.

**Why the plan doesn't pre-fill these:** agent-authored URLs would bake LLM biases into the benchmark the agent is being evaluated against. The fixtures must be grounded in your actual client work for the holdout pool to measure generalization rather than "what an LLM considers adversarial."

---

## File Structure

**New files (in repo):**
- `docs/plans/fixture-taxonomy-matrix.md` — 6-axis matrix with all fixtures placed
- `autoresearch/eval_suites/TAXONOMY.md` — concise living index pointing at the matrix
- `autoresearch/eval_suites/holdout-v1.json.example` — redacted reference copy of holdout manifest (NOT loaded)
- `docs/plans/overfit-canary-results.md` — experiment log from Phase 5
- `.github/workflows/holdout-refresh.yml` — CI-side holdout refresh (production primary; see Phase 2 Step 9f)
- `scripts/pre-commit-holdout-guard.sh` — pre-commit hook refusing `HOLDOUT_*_API_KEY` references outside the workflow file

**New files (out of repo, never committed):**
- `~/.config/gofreddy/holdouts/holdout-v1.json` — real holdout manifest (600 perms)
- `~/.local/share/gofreddy/fixture-cache/holdout-v1/...` — cache entries per holdout fixture
- `~/.local/share/gofreddy/fixture-cache/search-v1/...` — cache entries for all search fixtures (existing + expansion)
- `~/.local/share/gofreddy/holdout-runs/` — existing `EVOLUTION_PRIVATE_ARCHIVE_DIR`

**Modified files:**
- `autoresearch/eval_suites/search-v1.json` — append 6-8 new fixtures, bump manifest version to `1.1`
- `autoresearch/evolve_ops.py` — strengthen `is_promotable` to require holdout beat (Phase 6)
- `autoresearch/README.md` — document new agent-delegated promotion rule
- `autoresearch/GAPS.md` — mark Gaps 2, 3, 18 as partially addressed

---

## Phase 0: Phase 7 Plumbing Smoke-Test

> **⚠️ MVP CARVE-OUT (2026-04-23): FOLDED INTO PHASE 2.** The MVP review concluded this standalone phase is a belt-and-suspenders check on Plan A Phase 7 acceptance tests that have already shipped. Fold these assertions into `tests/autoresearch/test_evaluate_single_fixture_plumbing.py` (one pytest file, ~40 lines) and run it once before Phase 2 Step A begins. Do NOT create this as a separate numbered phase in execution tracking.

**Purpose:** Verify Plan A Phase 7's `--single-fixture` subprocess path works end-to-end: `evaluate_variant.py` accepts the flags, returns a `per_seed_scores` list of the requested length, sets `AUTORESEARCH_SEED` as a distinct per-replicate label, and produces non-null `cost_usd`. **Not a determinism test** — Plan B Phase 0b removed threshold-based noise statistics, so MAD magnitude is no longer load-bearing for anything. The agent-first architecture handles low-variance signal via `verdict=unclear` (abstain) at decision time; MAD>0 isn't a precondition.

**Prerequisite:** Plan A Phase 7 (adds `--single-fixture`, `--manifest`, `--seeds`, `--json-output`, `--baseline-variant` flags to `evaluate_variant.py` + `evaluate_single_fixture` entry point) and Plan A Phase 9 (creates `autoresearch/eval_suites/SCHEMA.md`) must both land before this probe runs.

**Files:**
- Create: `tests/autoresearch/test_judge_determinism_probe.py`
- Create: `docs/plans/judge-determinism-probe.md` (record results)
- Modify: `autoresearch/eval_suites/SCHEMA.md` (pin "seed" semantics; written by Plan A Phase 9 — add amendment here)

- [ ] **Step 1: Plumbing smoke-test**

Create `tests/autoresearch/test_evaluate_single_fixture_plumbing.py`:

```python
"""Phase 7 plumbing smoke-test.

Exercises the `evaluate_variant.py --single-fixture` subprocess end-to-end:
- correct flags are accepted
- JSON output has `per_seed_scores` list of requested length
- `cost_usd` present and numeric
- AUTORESEARCH_SEED is set to a distinct replicate label per invocation

Does NOT assert MAD > 0 — variance is optional and handled at decision time
by the quality-judge's `verdict=unclear` abstain path (Plan A Phase 7).
"""
import json
import subprocess
import sys
from pathlib import Path


def test_single_fixture_subprocess_returns_expected_shape():
    manifest_payload = json.loads(
        Path("autoresearch/eval_suites/search-v1.json").read_text()
    )
    geo = [fx for fx in manifest_payload["domains"]["geo"] if fx.get("anchor")]
    assert geo, "no anchor geo fixture available"
    fixture_id = geo[0]["fixture_id"]
    variants = sorted(
        d.name for d in Path("autoresearch/archive").iterdir()
        if d.is_dir() and d.name.startswith("v")
    )
    assert variants, "no variants in autoresearch/archive"
    variant = variants[len(variants) // 2]

    result = subprocess.run([
        sys.executable, "autoresearch/evaluate_variant.py",
        "--single-fixture", f"search-v1:{fixture_id}",
        "--manifest", "autoresearch/eval_suites/search-v1.json",
        "--seeds", "5", "--baseline-variant", variant, "--json-output",
    ], capture_output=True, text=True, check=True)

    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert len(payload["per_seed_scores"]) == 5, payload
    assert all(isinstance(s, (int, float)) for s in payload["per_seed_scores"])
    assert "cost_usd" in payload and isinstance(payload["cost_usd"], (int, float))
    # Optional diagnostic: if MAD=0, record it for visibility but don't fail.
    import statistics
    scores = payload["per_seed_scores"]
    med = statistics.median(scores)
    mad = statistics.median(abs(s - med) for s in scores)
    print(f"Diagnostic: MAD={mad:.4f} (not asserted — unclear verdict handles this)")
```

- [ ] **Step 2: Run smoke-test + record result**

Run: `pytest tests/autoresearch/test_evaluate_single_fixture_plumbing.py -v`

**Expected:** PASS. The diagnostic MAD line is informational only; the agent-first architecture handles low-variance signal via `verdict=unclear` (quality-judge abstains at the decision layer, not the plumbing layer).

- [ ] **Step 3: Pin seed semantics in SCHEMA.md**

Plan A Phase 9 creates `autoresearch/eval_suites/SCHEMA.md`. Append:

```markdown
## Seeds Semantics (Plan B Phase 0)

In this plan, `--seeds N` runs N independent sessions. `AUTORESEARCH_SEED`
is set per-session as a replicate label for log/artifact naming; the variant
sampler does not read it. Variance comes from inherent LLM nondeterminism
(batching, scheduling, sampling at temperature=0) in both variant and judge.

This is NOT "score the same artifact N times." The previous spec
("judge N times on one artifact") was abandoned because `freddy evaluate
critique` takes no seed/nonce and provider response caching would collapse
variance to zero.

If a future judge migration produces MAD=0 across 5 seeds on a known-healthy
fixture, the quality-judge will return `verdict=unclear` at decision time
and the operator reviews raw stats manually. No code-side threshold.
```

- [ ] **Step 4: Commit**

```bash
git add tests/autoresearch/test_evaluate_single_fixture_plumbing.py
git commit -m "test(autoresearch): Phase 7 plumbing smoke-test"
```

---

## Phase 0-A: Golden Fixture Calibration (Pre-Authoring Sanity)

> **⚠️ MVP CARVE-OUT (2026-04-23): FOLDED INTO PHASE 2 STEP A.** Review concluded Phase 0-A's judge-sanity check duplicates the same check that happens implicitly when Phase 2 Step A runs `freddy fixture dry-run` on its first holdout fixture. A buggy judge prompt surfaces within the first authoring run — no separate calibration phase is needed. The 3-5 "golden" search-v1 additions here also conflict with Phase 3's gap-fillers; pick the golden ones from Phase 3's candidates rather than authoring extras. Skip as a separate phase; if the first Phase 2 Step A dry-run returns `verdict != healthy`, halt and debug the judge prompt before continuing.

**Purpose:** Before authoring 16 holdout fixtures against an unverified judge prompt, hand-craft 3-5 **golden fixtures** from your best existing client work and confirm the quality-judge returns `verdict=healthy` on all of them. If the judge mislabels a known-good fixture as saturated/degenerate/unclear, the judge prompt needs fixing before it's trusted to gate 16 downstream authoring runs. Without this step, a buggy prompt silently rejects good fixtures for weeks before anyone notices.

**Prerequisite:** Plan A Phase 7 (dry-run) + Phase 0c (judge services) landed. This step calls `freddy fixture dry-run` against the live quality-judge.

**Files:**
- Create: `docs/plans/golden-fixture-calibration.md` — log the picks + verdicts
- Modify: `autoresearch/eval_suites/search-v1.json` — golden fixtures land here (they become search-v1 members, not holdout — their role is judge sanity, not adversarial eval)

- [ ] **Step 1: Pick 3-5 golden fixtures from real client work**

Criteria for a golden fixture:
- **Real:** drawn from your actual client engagements (not synthetic, not agent-authored)
- **Representative:** covers the middle of your distribution — common vertical, common domain, common language. NOT adversarial, NOT edge-case. The point is "if the judge can't say this is healthy, the judge is broken."
- **Discriminating:** you already know a "good variant" produces substantially different output from a "bad variant" on this fixture. Pick fixtures where the human-obvious winner is clear.

Pick ~1 per domain (geo + competitive + monitoring + storyboard = 4 golden fixtures), plus optionally one more in whichever domain is most central to your work. Document each pick in `docs/plans/golden-fixture-calibration.md` with the URL, client, domain, and a one-line "why this is golden."

- [ ] **Step 2: Author each golden fixture as a standard search-v1 entry**

For each golden fixture, run the standard Phase 3 authoring loop (validate → envs → refresh → dry-run), with one extra step before dry-run: manually inspect the refreshed cache. The content should look sensible (not empty, not paywalled, not rate-limited) before the judge ever sees it. If the cache looks wrong, the fixture spec is wrong — fix the URL/env before proceeding.

Each golden fixture gets committed to `autoresearch/eval_suites/search-v1.json` as a regular fixture. They're tagged with `"golden": true` in the spec so they can be filtered in later queries. ~1 hour per fixture.

- [ ] **Step 3: Run dry-run against each golden fixture at baseline v006**

```bash
for fx in $GOLDEN_FIXTURES; do
  freddy fixture dry-run "$fx" --baseline v006 --seeds 5
  echo "  → exit code: $?"
done
```

**Required outcome:** every golden fixture exits 0 (verdict=healthy). Log each `{fixture, verdict, reasoning, confidence, per_seed_scores}` in `docs/plans/golden-fixture-calibration.md`.

**If ANY golden fixture exits non-zero:**
- Exit 1 (saturated/degenerate/unstable/cost_excess/needs_revision): the judge is mislabeling a known-good fixture. Read `verdict.reasoning`. If the reasoning is defensible (e.g. judge flags a real quality issue you overlooked), the fixture wasn't actually golden — pick another. If the reasoning is nonsense, the judge prompt (`judges/evolution/prompts/quality.md`) has a bug. Fix the prompt, redeploy the judge-service (merge-to-main → `sudo -u judge-service bash judges/deploy/local-daemon.sh restart` per Plan A Phase 0c), re-run the golden check.
- Exit 2 (unclear): the judge abstained. If this happens on a clearly-healthy fixture, the judge's confidence threshold (agent-side, in the prompt) is miscalibrated — too cautious. Same fix path as above.

**Do not proceed to Phase 2 (holdout authoring) until all golden fixtures verdict=healthy.** The 3-4 hours spent calibrating the judge here saves weeks of authoring-agent verdicts against a buggy prompt.

- [ ] **Step 4: Commit golden fixture log**

```bash
git add autoresearch/eval_suites/search-v1.json docs/plans/golden-fixture-calibration.md
git commit -m "test(fixtures): golden fixture calibration — judge verdicts verified on 3-5 known-healthy fixtures"
```

---

## Phase 0a: Event Kinds Emitted by This Plan

`autoresearch/events.py` is created by **Plan A Phase 0d** — not here. Plan A is the first writer (`judge_unreachable` at Phase 0c, `judge_abstain` at Phase 7) and owns the module, its durability contract (flock + fsync + 100MB rotation), and the `log_event` / `read_events` helpers.

**Event kinds Plan B emits into the shared log:** `promotion_decision`, `regression_check`, `saturation_cycle`, `judge_drift`, `content_drift`, `head_score`, `judge_raw`. Each replaces a previously-separate JSONL file. Rollback (when shipped post-MVP) will filter `kind="head_score"` entries via the standard reader — no separate log, no custom parser.

**Event kinds Plan A emits (for reference):** `judge_unreachable`, `judge_abstain`. Plan B code paths may also emit `judge_unreachable` when the evolution-judge service is down (see Phase 6).

---

## Phase 0b: Decision-Judge Agent Roles

**Purpose:** Replace hardcoded quality/promotion thresholds (dry-run flags, saturation, judge drift, URL drift, promotion gates, rollback triggers, canary GO/FAIL) with AI agents that consume raw per-seed score distributions and raw trajectories directly — no pre-computed summary statistics designed to feed threshold decisions. Summary statistics (Wilcoxon p-value, Cliff's delta, Mann-Kendall tau) were invented to cross specific thresholds; dropping the thresholds means dropping the statistics that fed them. Agents see the raw numbers. Code keeps only genuine invariants (schema shapes, env-var presence, MAD>0 boolean), infrastructure (CLI plumbing, HTTP, CI), and cost-summation-style tallies that are facts rather than judgments. Human-facing markdown reports may still show median/MAD at a glance — that's a presentation concern, not an input to any judgment.

**Two role groups, two CLI commands (autoresearch-side):**

- `freddy evaluate quality-judge` — dispatches to the unified `system_health_agent` via role (saturation / content_drift / discriminability / fixture_quality / calibration_drift / noise_escalation). Advisory; low-stakes.
- `freddy evaluate promotion-judge` — dispatches to one of 3 dedicated decision agents (promotion / rollback / canary). Autonomous; high-stakes.

**Backing models:**

- `quality-judge` uses `claude-opus-4-7` (Anthropic). No cross-family requirement — it's advisory.
- `promotion-judge` uses `claude-opus-4-7` deliberately from a DIFFERENT family than the primary scoring judge (`gpt-5.4`). Preserves the cross-family-judge property from the earlier design: a variant that games the gpt-5.4 scorer still has to pass a Claude-based promotion decision, reducing single-family gaming risk.

**Files:**
- Create: `cli/freddy/commands/evaluate.py` additions — `quality_judge_command`, `promotion_judge_command`
- Create: `autoresearch/judges/quality_judge.py` — prompt template + invocation helper
- Create: `autoresearch/judges/promotion_judge.py` — prompt template + invocation helper
- Create: `tests/autoresearch/test_judges.py` — mocked-response tests (no live API)

- [ ] **Step 1: Write failing tests (mocked agent responses)**

Create `tests/autoresearch/test_judges.py`:

```python
"""Judge-agent interface tests. Mock httpx.post; test wiring + payload + response parsing.

Under the Phase 0c HTTP-client architecture, tests mock the HTTP transport
(httpx.post), not an in-process model-invocation function. This tests the
CLIENT's contract: does it POST to the right URL with the right bearer
token, and does it parse the response correctly?
"""
import json
from unittest.mock import patch, MagicMock

import pytest

from autoresearch.judges.quality_judge import call_quality_judge, QualityVerdict
from autoresearch.judges.promotion_judge import call_promotion_judge, PromotionVerdict


def _mock_http_response(body: str, status_code: int = 200) -> MagicMock:
    """Build a minimal httpx.Response stand-in that raise_for_status() + .json() work on."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=json.loads(body))
    resp.text = body
    return resp


def test_quality_judge_returns_verdict_with_reasoning():
    payload = {
        "role": "fixture_quality",
        "fixture_id": "geo-bmw-ev-de",
        "stats": {"median": 0.92, "mad": 0.03, "cost_usd": 0.12, "per_seed_scores": [0.90, 0.92, 0.93, 0.91, 0.94]},
    }
    mock_response = json.dumps({
        "verdict": "saturated",
        "reasoning": "Median 0.92 is near ceiling; low MAD means consistent ceiling. Fixture is too easy.",
        "confidence": 0.85,
        "recommended_action": "rotate_out_next_cycle",
    })
    with patch("httpx.post", return_value=_mock_http_response(mock_response)):
        result = call_quality_judge(payload)
    assert isinstance(result, QualityVerdict)
    assert result.verdict == "saturated"
    assert "ceiling" in result.reasoning.lower()
    assert 0.0 <= result.confidence <= 1.0


def test_promotion_judge_promote_when_signals_coherent():
    payload = {
        "role": "promotion",
        "candidate_id": "v007", "baseline_id": "v006", "lane": "geo",
        "public_scores": {"candidate": 0.72, "baseline": 0.65},
        "holdout_scores": {"candidate": 0.62, "baseline": 0.55},
        "per_fixture": {  # {fixture_id: {"candidate": float, "baseline": float}}
            "geo-a": {"candidate": 0.75, "baseline": 0.60},
            "geo-b": {"candidate": 0.70, "baseline": 0.65},
            # ... N fixtures
        },
        "secondary_public_scores": {"candidate": 0.70, "baseline": 0.64},
        "secondary_holdout_scores": {"candidate": 0.61, "baseline": 0.54},
    }
    mock = json.dumps({
        "decision": "promote",
        "reasoning": "Public +0.07, holdout +0.07, both judges agree direction and magnitude, per-fixture wins dominate.",
        "confidence": 0.88,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert isinstance(result, PromotionVerdict)
    assert result.decision == "promote"


def test_promotion_judge_rejects_on_single_judge_disagreement():
    payload = {
        "role": "promotion", "candidate_id": "v008", "baseline_id": "v006", "lane": "geo",
        "public_scores": {"candidate": 0.70, "baseline": 0.60},
        "holdout_scores": {"candidate": 0.58, "baseline": 0.55},
        "per_fixture": {"geo-a": {"candidate": 0.95, "baseline": 0.50}, "geo-b": {"candidate": 0.55, "baseline": 0.55}},
        "secondary_public_scores": {"candidate": 0.60, "baseline": 0.60},  # secondary says no improvement
        "secondary_holdout_scores": {"candidate": 0.55, "baseline": 0.55},
    }
    mock = json.dumps({
        "decision": "reject",
        "reasoning": "Primary and secondary judges disagree; single-fixture dominance suggests gaming.",
        "confidence": 0.82,
        "concerns": ["cross_family_disagreement", "uneven_per_fixture_wins"],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "reject"
    assert "cross_family_disagreement" in result.concerns


def test_promotion_judge_rollback_decision():
    payload = {
        "role": "rollback", "lane": "geo",
        "current_head": "v010", "prior_head": "v006",
        "head_scores_log": [  # recent events.jsonl kind="head_score" entries
            {"timestamp": "...", "head_id": "v006", "public_score": 0.65, "holdout_score": 0.55},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.58, "holdout_score": 0.49},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.55, "holdout_score": 0.48},
            {"timestamp": "...", "head_id": "v010", "public_score": 0.53, "holdout_score": 0.47},
        ],
    }
    mock = json.dumps({
        "decision": "rollback",
        "reasoning": "Three consecutive post-promotion scores regress below prior-head baseline; monotonic decline suggests bad promotion.",
        "confidence": 0.91,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "rollback"


def test_promotion_judge_canary_go_decision():
    payload = {
        "role": "canary", "mode": "go_fail", "lane": "geo",
        "checkpoints": [  # 10 entries, one per checkpoint
            {"iter": 2, "public_median": 0.50, "holdout_median": 0.45, "divergence": 0.05},
            # ... 10 rows
        ],
        "pre_canary_sanity": {"known_pair_delta": 0.12},
    }
    mock = json.dumps({
        "decision": "go",
        "reasoning": "Divergence trends up monotonically across all 10 checkpoints; holdout clearly slower than public. Pre-canary sanity passed.",
        "confidence": 0.93,
        "concerns": [],
    })
    with patch("httpx.post", return_value=_mock_http_response(mock)):
        result = call_promotion_judge(payload)
    assert result.decision == "go"
```

Run: expect FAIL (modules don't exist).

- [ ] **Step 2: Implement the two judge modules**

Create `autoresearch/judges/quality_judge.py`:

```python
"""Quality-judge agent: advisory decisions about fixture quality, saturation, drift."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityVerdict:
    verdict: str                 # fixture_quality: healthy|saturated|degenerate|unstable|cost_excess|unclear|needs_revision
                                 #   - healthy: proceed (exit 0)
                                 #   - saturated|degenerate|unstable|cost_excess: reject (exit 1)
                                 #   - unclear: agent cannot decide (low confidence / contradictory evidence) → abstain (exit 2, log_event kind=judge_abstain)
                                 #   - needs_revision: fixture is fixable, operator should revise the spec and retry (exit 1)
                                 # saturation: rotate_now|rotate_soon|fine
                                 # calibration_drift: stable|magnitude_drift|variance_drift|reasoning_drift|mixed
                                 # content_drift: material|cosmetic|unknown
                                 # discriminability: separable|not_separable|insufficient_data
                                 # noise_escalation: sufficient|bump_seeds|bump_iterations
    reasoning: str
    confidence: float  # [0, 1]
    recommended_action: str | None = None


# PROMPT TEMPLATES LIVE ON THE JUDGE-SERVICE (judges/evolution/prompts/quality.md)
# — NOT in autoresearch-side code. See Plan A Phase 0c for isolation rationale.
# This autoresearch-side module is a thin HTTP client; it knows nothing about
# how the judge decides, only how to ask it.


import httpx, os

EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_SYSTEM_HEALTH_ROLES = {
    "saturation", "content_drift", "discriminability",
    "fixture_quality", "calibration_drift", "noise_escalation",
}


def call_quality_judge(payload: dict[str, Any]) -> QualityVerdict:
    """POST to evolution-judge-service /invoke/system_health/{role} and parse verdict.

    Dispatches to the single unified `system_health_agent` on the judge service
    via role-in-URL routing. All advisory / meta concerns go through this client.
    """
    role = payload.get("role")
    if role not in _SYSTEM_HEALTH_ROLES:
        raise ValueError(f"invalid system_health role: {role!r}")
    r = httpx.post(
        f"{EVOLUTION_JUDGE_URL}/invoke/system_health/{role}", json=payload,
        headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return QualityVerdict(
        verdict=str(data["verdict"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        recommended_action=data.get("recommended_action"),
    )
```

Create `autoresearch/judges/promotion_judge.py`:

```python
"""Promotion-judge agent: autonomous decisions about promote, rollback, canary GO/FAIL.

Cross-family by design: uses claude-opus-4-7 (Anthropic) while the primary
scoring judge uses gpt-5.4 (OpenAI). A variant that games the scoring judge
still has to pass a Claude-based promotion decision.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromotionVerdict:
    decision: str                 # promotion: promote | reject
                                  # rollback: rollback | hold
                                  # canary: go | fail | revise
                                  #         (or checkpoint | skip | early_terminate_go
                                  #          | early_terminate_fail when mode=checkpoint_schedule)
    reasoning: str
    confidence: float             # [0, 1]
    concerns: list[str] = field(default_factory=list)


# PROMPT TEMPLATE LIVES ON THE JUDGE-SERVICE (judges/evolution/prompts/promotion.md)
# — NOT in autoresearch-side code. Cross-family role (Claude Opus 4.7) is
# enforced at the judge-service side via codex-vs-claude selection, not here.


import httpx, os

EVOLUTION_JUDGE_URL = os.environ.get("EVOLUTION_JUDGE_URL", "http://localhost:7200")
EVOLUTION_INVOKE_TOKEN = os.environ.get("EVOLUTION_INVOKE_TOKEN", "")


_DECISION_ROLES = {"promotion", "rollback", "canary"}


def call_promotion_judge(payload: dict[str, Any]) -> PromotionVerdict:
    """POST to evolution-judge-service /invoke/decide/{role} and parse verdict.

    Role routes to one of three decision agents wired by Plan A Phase 0c
    (all three are live routes on judges/server.py):
      - promotion → promotion_agent.py (promote | reject | abstain)
      - canary    → canary_agent.py    (go | fail | revise)
      - rollback  → rollback_agent.py  (rollback | skip | abstain)

    Note: the MVP carve-out of Plan B defers automated rollback invocation
    (the `role="rollback"` call site in Phase 6 Step 6) to a follow-up plan;
    the route itself still exists and is safe to hit manually.

    On service outage (connection error, 5xx, timeout, malformed response):
    emit kind="judge_unreachable" and raise JudgeUnreachable. Caller decides
    whether to halt the cycle or treat as an abstain. Matches Plan A Phase 0c:
    no threshold fallback, no silent retry.
    """
    from autoresearch.events import log_event

    role = payload.get("role", "promotion")
    if role not in _DECISION_ROLES:
        raise ValueError(f"invalid decision role: {role!r}")
    try:
        r = httpx.post(
            f"{EVOLUTION_JUDGE_URL}/invoke/decide/{role}", json=payload,
            headers={"Authorization": f"Bearer {EVOLUTION_INVOKE_TOKEN}"}, timeout=300,
        )
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        log_event(kind="judge_unreachable",
                  endpoint=f"/invoke/decide/{role}",
                  error_class=type(exc).__name__,
                  error=str(exc)[:500])
        raise JudgeUnreachable(f"evolution-judge unreachable: {exc}") from exc
    return PromotionVerdict(
        decision=str(data["decision"]),
        reasoning=str(data.get("reasoning", "")),
        confidence=float(data.get("confidence", 0.5)),
        concerns=list(data.get("concerns", [])),
    )


class JudgeUnreachable(RuntimeError):
    """Evolution-judge service did not return a parseable verdict. Halt + re-run."""
    pass
```

- [ ] **Step 3: Run tests and commit**

Judge invocation plumbing (CLI subcommands, HTTP services, prompt files) lives in Plan A Phase 0c; this step verifies the autoresearch-side clients call the right endpoints.

Run: `pytest tests/autoresearch/test_judges.py -v` — expect all PASS. Tests mock `httpx.post` (not an in-process `_invoke_model`) to verify `call_promotion_judge` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/decide/{promotion|rollback|canary}` and `call_quality_judge` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/system_health/{role}` with the right bearer token, and both parse responses correctly.

**Audit log lives on the judge-service side** (not on autoresearch host). Autoresearch-side `events.jsonl` still records `kind="promotion_decision"` etc. with the verdict but not the full reasoning — the full reasoning with prompt context lives on the judge-service's own events log, inaccessible to autoresearch processes. This is a feature: a worker agent can see "judge said promote" but can't exfiltrate "judge said promote because of <reasoning that would let me learn the rubric>."

```bash
git add autoresearch/judges/ tests/autoresearch/test_judges.py
git commit -m "feat(judges): autoresearch-side HTTP clients for quality + promotion judges (prompts live on judge-service per Plan A Phase 0c)"
```

**Cost / operational notes:**
- Quality-judge: ~30-40 calls/week. At ~$0.01-0.05 per Claude Opus 4.7 CLI invocation via subscription (amortized against fixed monthly fee), this is effectively free above the subscription.
- Promotion-judge: ~1-10 calls/day + ~1/week rollback + 1 canary GO/FAIL per holdout version. Same subscription-amortized cost.
- All judge calls go through `claude` CLI on the evolution-judge-service host. Autoresearch host has no Anthropic credentials (API key removed from env per Phase 0c). If the subscription is rate-limited, evolution loop pauses until the judge-service 503 clears — this is the deliberate no-fallback posture.

---

## Phase 1: Fixture Taxonomy Matrix (Design Artifact)

**Purpose:** Shared design document that drives fixture authoring for both pools. Maps the design space; every fixture placed on it. Can be drafted in parallel with Plan A.

**Files:**
- Create: `docs/plans/fixture-taxonomy-matrix.md`
- Create: `autoresearch/eval_suites/TAXONOMY.md`

- [ ] **Step 1: Define the 6 axes**

In `docs/plans/fixture-taxonomy-matrix.md`, document the axes:

1. **Domain**: geo / competitive / monitoring / storyboard
2. **Language**: en / de / fr / es / pt-BR / ja / zh / mixed
3. **Geography**: US / EU / LATAM / APAC / global
4. **Vertical**: SaaS-tech / ecommerce / CPG / finance / health / automotive / media / creator-economy / enterprise-b2b
5. **Adversarial condition**: standard / paywall / SPA / thin-content / thin-ads / regulatory / multi-segment / opaque / saturated-market / low-volume / non-verbal / cultural-distance / evolving-style
6. **Stressed rubric criteria** (per-domain subset): pick 1-3 of the 8 criteria in that domain's rubric that this fixture is specifically designed to stress

Each fixture gets one value on axes 1-5 and 1-3 criteria on axis 6.

- [ ] **Step 2: Place all 23 existing search-v1 fixtures on the matrix**

Go through `autoresearch/eval_suites/search-v1.json` fixture-by-fixture. For each, determine the axis values based on the fixture's actual content (look at the context URL, client, env vars).

Output: a markdown table in the matrix doc, one row per fixture:

```markdown
| Fixture ID | Pool | Domain | Lang | Geo | Vertical | Adversarial | Stressed Criteria |
|---|---|---|---|---|---|---|---|
| geo-semrush-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-5 |
| geo-ahrefs-pricing | search-v1 | geo | en | US | SaaS-tech | standard | GEO-1, GEO-7 |
| ... (23 rows) |
```

Expected finding: existing coverage is heavily concentrated in `(en, US, SaaS-tech, standard)`. Most cells are empty.

- [ ] **Step 3: Identify coverage gaps**

In the matrix doc, enumerate:
- **Empty cells** (combinations with zero fixtures)
- **Sparse cells** (only 1 fixture)
- **Rubric criteria covered by ≤1 fixture total** (high risk of un-tested criteria)

- [ ] **Step 4: Propose fills and pool assignments**

For each empty/sparse cell worth filling, propose a fixture and tag it `→ search-v1` or `→ holdout-v1` based on the heuristic:

- **search-v1**: "This represents realistic agency work we want the system to do well on." Variants will be evaluated on this fixture during evolution.
- **holdout-v1**: "This is an adversarial probe designed to catch overfitting that wouldn't show up on search-v1." Variants are never evaluated on this during proposer iteration.

Rule: no cell appears in both pools. One fixture per cell, assigned to exactly one pool.

Target: ~6-8 new search fixtures + 16 holdout fixtures proposed.

- [ ] **Step 5: Rubric-coverage matrix**

Separately, construct a (criterion × fixture) matrix across both pools. Each domain has 8 criteria; 8 × 4 = 32 criteria total. Verify every criterion is stressed by at least 2 fixtures in the combined pool. Where gaps remain, adjust fixture proposals to close them.

- [ ] **Step 6: Create TAXONOMY.md living index (search-v1 ONLY)**

Holdout rows live out-of-repo per the File Structure section above (proposer read path = in-repo). Create `autoresearch/eval_suites/TAXONOMY.md` (~100 lines) pointing at the in-repo matrix, summarizing current search-v1 coverage and latest matrix version. Note that holdout taxonomy lives at `~/.config/gofreddy/holdouts/holdout-v1-taxonomy.md` (600).

- [ ] **Step 7: Review and commit**

Sanity-check the search-v1 matrix: every existing fixture placed, proposed fills feasible, ≥2 stressors per criterion, pool assignments defensible. The out-of-repo holdout taxonomy is not committed.

```bash
git add docs/plans/fixture-taxonomy-matrix.md autoresearch/eval_suites/TAXONOMY.md
git commit -m "docs(fixture): add taxonomy matrix + rubric coverage matrix (search-v1; holdout rows out-of-repo)"
```

---

## Phase 2: Holdout-v1 Fixture Authoring (16 fixtures)

**Purpose:** Author the real holdout manifest. Uses Plan A's infrastructure end-to-end. Each fixture goes through the full per-fixture process before being committed to the manifest.

**Files:**
- Create: `~/.config/gofreddy/holdouts/holdout-v1.json` (out of repo)
- Create: `autoresearch/eval_suites/holdout-v1.json.example` (in repo, redacted reference)
- Populate: cache at `~/.local/share/gofreddy/fixture-cache/holdout-v1/...`

**16-fixture composition (axes from Phase 1 taxonomy; URLs + context YOU populate):**

The composition below names 16 rows by axis-stress intent. Each row is NOT yet authorable — the `URL`, `Client`, and `Env vars` columns must be filled by the operator from **real client work** before the authoring agent runs in Step A. Agent-authored URLs would bake LLM biases into the benchmark that's meant to evaluate the LLM.

| # | Fixture ID | Domain | Tier | Primary axes | URL (you fill) | Client (you fill) | Env vars (you fill) |
|---|---|---|---|---|---|---|---|
| 1 | geo-bmw-ev-de | geo | anchor | lang=de, vertical=auto, geo=EU | `<real DE automotive product page>` | e.g. "bmw" | — |
| 2 | geo-nubank-br-pix | geo | rotating | lang=pt-BR, vertical=fintech, geo=LATAM | `<real BR fintech page>` | | |
| 3 | geo-stripe-docs-gated | geo | rotating | adversarial=paywall | `<real gated-content page>` | | |
| 4 | geo-rakuten-travel-spa | geo | anchor | adversarial=SPA, lang=ja, geo=APAC | `<real JP SPA page>` | | |
| 5 | competitive-toyota-vs-byd-ev | competitive | rotating | vertical=auto, adversarial=thin-ads | `<competitor context>` | | |
| 6 | competitive-nubank-vs-latam-banks | competitive | rotating | lang=multi, geo=LATAM, vertical=fintech | | | |
| 7 | competitive-opaque-private-b2b | competitive | anchor | adversarial=opaque | | | |
| 8 | competitive-axios-vs-semafor | competitive | anchor | vertical=media, adversarial=saturated | | | |
| 9 | monitoring-unilever-cpg | monitoring | rotating | vertical=CPG | — (monitor_id) | | `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` |
| 10 | monitoring-deutsche-bank | monitoring | rotating | geo=EU, vertical=finance, regulatory | — (monitor_id) | | `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` |
| 11 | monitoring-twitch-low-volume | monitoring | anchor | adversarial=low-volume | — (monitor_id) | | `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` |
| 12 | monitoring-tsmc-apac | monitoring | anchor | lang=zh+en, geo=APAC, vertical=hardware | — (monitor_id) | | `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` |
| 13 | storyboard-tokyo-creative-ja | storyboard | anchor | lang=ja, adversarial=cultural-distance | `<real creator context>` | | |
| 14 | storyboard-amixem-fr | storyboard | rotating | lang=fr | `<real FR creator>` | | |
| 15 | storyboard-music-creator-nonverbal | storyboard | anchor | adversarial=non-verbal | `<non-verbal creator>` | | |
| 16 | storyboard-pivoting-creator | storyboard | rotating | adversarial=evolving-style | `<multi-phase creator>` | | |

**Human authoring budget:** ~1 day per fixture to identify a representative URL/context from real client work (~3 weeks total for 16). Plus ~30 min per fixture for the authoring agent to format, validate, refresh, dry-run, and discriminate (~1 day total). The agent is a **formatter**, not an author — you supply the semantic content, it handles the JSON plumbing and calibration calls.

**Alternative: start with 8, not 16.** If ~3 weeks of URL research is prohibitive for the MVP timeline, pick 8 rows from the table above (balance across the 4 domains: 2 anchor + 2 rotating per domain is a natural subset). Prove the pipeline with 8 — run the canary with 8, observe discrimination, then expand to 16 in a follow-up pass. Halves the upfront time at the cost of weaker initial coverage. Either choice is defensible; make it explicitly.

**Data-feasibility reminder from the data-dependency audit:** use `AUTORESEARCH_WEEK_RELATIVE=most_recent_complete` for ALL monitoring fixtures. Pinned historical fixtures are NOT viable — source retention is 30-90 days. Pinned-history support is blocked on a snapshot-cache infrastructure that doesn't currently exist in any provider; when that lands (separate initiative), holdout-v2 adds pinned fixtures. Not a decision to defer — an infrastructure limit.

**Per-fixture process:** run as a documented agent task (see Step A below). The 16-fixture loop becomes: bootstrap manifest (Step 0), dispatch an authoring agent 16 times (Step A), commit example (remaining steps). No new CLI command — the agent invokes the existing `freddy fixture {validate, envs, refresh, dry-run, discriminate}` primitives.

⚠️ **Refresh CLI-signature bug blocks most fixture domains.** Until `docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md` ships, Phase 2 authoring can only complete for fixtures whose sources pass a positional URL (geo-scrape) or a positional UUID (monitoring/{mentions,sentiment,sov}). The 16-row composition table above has rows spanning all 4 domains; competitive + storyboard fixtures and anything using visibility will fail at the authoring agent's refresh step. **Two options**:
1. **Ship the refresh CLI fix first** (~150 lines per the follow-up plan), then execute Phase 2 against all 4 domains.
2. **Start with the "8 fixtures" alternative**, picking rows that don't use visibility/search-ads/search-content. The natural 8-row subset: 2 anchor + 2 rotating of {geo, monitoring} = 8 fixtures (drop all 4 competitive + all 4 storyboard rows).

Pick explicitly before starting Phase 2. Option 1 is architecturally cleaner; Option 2 delivers faster signal.

- [ ] **Step 0: Bootstrap the empty holdout manifest (once, before the first fixture)**

Before iterating 16 times, create the empty shell of `~/.config/gofreddy/holdouts/holdout-v1.json` with suite-level metadata. Step 6's append-fixture operation assumes the file exists with the right shape.

```bash
mkdir -p ~/.config/gofreddy/holdouts
cat > ~/.config/gofreddy/holdouts/holdout-v1.json <<'EOF'
{
  "suite_id": "holdout-v1",
  "version": "1.0",
  "eval_target": {
    "backend": "codex",
    "model": "gpt-5.4",
    "reasoning_effort": "high"
  },
  "rotation": {
    "strategy": "stratified",
    "anchors_per_domain": 2,
    "random_per_domain": 1,
    "seed_source": "generation",
    "cohort_size": 3
  },
  "domains": {
    "geo": [],
    "competitive": [],
    "monitoring": [],
    "storyboard": []
  }
}
EOF
chmod 600 ~/.config/gofreddy/holdouts/holdout-v1.json
```

Then the per-fixture loop below appends into the appropriate `domains.<domain>` array during Step 6.

**Rotation math (per cycle, per variant):** 2 anchors + 1 random per domain × 4 domains = 12 fixtures (out of 16). Anchor set is fixed; rotating set cycles through the 8 rotating fixtures via deterministic PRF seeded on the current cycle's `EVOLUTION_COHORT_ID`. This cuts holdout wall-time by ~25% per variant while preserving the 8-anchor stability guarantee.

**Cross-cycle comparability via cohort pinning.** `seed_source="generation"` is the value `_sample_fixtures` (autoresearch/evaluate_variant.py:362-398) actually branches on — it causes the sampler to read `EVOLUTION_COHORT_ID` from the environment (set per decision cycle by `evolve.sh`). Within one cycle, baseline and candidate see the SAME cohort → SAME 12-fixture subset → like-for-like scores. Across cycles the subset rotates, but comparisons are always within-cycle pairs, so cross-cycle aggregation never compares different subsets. If `EVOLUTION_COHORT_ID` is absent, the sampler falls back to seeding on `variant_id` (the `else` branch), which silently breaks the cross-cycle comparability guarantee — treat an absent env var as a fatal configuration error, not a graceful fallback. `cohort_size: 3` is not read on the `"generation"` path; it is kept for documentation only.

> **⚠️ MVP CARVE-OUT (2026-04-23): ROTATION-POLICY AGENT DEFERRED.** Steps below verifying `_sample_fixtures` wiring and the `EVOLUTION_COHORT_ID` contract are IN-SCOPE for MVP. The **rotation-policy agent task spec** (monthly `mode=rotation_proposal` invocation, `docs/agent-tasks/rotation-policy.md`) described at the end of this step is DEFERRED to a follow-up plan — the agent is a 90-day no-op by its own admission. Skip creating `docs/agent-tasks/rotation-policy.md` and do not wire the `role=saturation, mode=rotation_proposal` invocation. The static Phase 1 taxonomy partition is authoritative for MVP.

- [ ] **Step 0b: Verify Plan A amendment landed + `_sample_fixtures` is wired**

Plan A Phase 7 Step 2.5 adds `_sample_fixtures` to `_run_holdout_suite`, gated on `suite_manifest.get("rotation")` truthy. Holdout-v1's manifest includes the rotation block → sampler runs. Verify:

```bash
rg -n 'rotation.*_sample_fixtures|if.*rotation' autoresearch/evaluate_variant.py
```

Expect: one guard site reading the rotation config. If missing, halt and fix in Plan A before proceeding.

Add a test `tests/autoresearch/test_holdout_manifest_guards.py::test_holdout_applies_rotation_when_configured`: construct a 16-fixture manifest with the rotation block, invoke `_run_holdout_suite` for two distinct variant_ids pinned to the SAME `EVOLUTION_COHORT_ID`, assert (a) each run evaluates 12 fixtures, (b) the anchor set is stable across runs, (c) the random set is IDENTICAL when cohort is pinned, DIFFERENT when cohort changes.

**Rotation partition is adaptive.** Initial partition (8 anchors + 8 rotating, from the Phase 1 taxonomy) is the bootstrap; after observation, the partition should respond to data. Monthly, an operator dispatches a lightweight agent task that reads per-fixture saturation history from `events.jsonl` (kind=`saturation_cycle`), reads per-fixture discriminability verdicts from prior `freddy fixture discriminate` runs, reads the current anchor/rotating partition, and POSTs to the existing `system_health_agent` (`role=saturation`, `mode=rotation_proposal`). The same agent we already use for per-fixture saturation verdicts produces the partition proposal — no new agent, no dedicated CLI command.

**Rotation-policy agent task spec** (`docs/agent-tasks/rotation-policy.md`):

```
GOAL: produce an updated anchor/rotating partition for a holdout pool, based
      on observed saturation and discriminability. Operator reviews + commits.

INPUTS: pool (e.g. holdout-v1), manifest_path

STEPS:
  1. Read per-fixture saturation-cycle events from ~/.local/share/gofreddy/events.jsonl
     (filter kind="saturation_cycle"; includes rotated segments per Plan A
     Phase 0d read_events contract).
  2. Read discriminability verdict history per holdout fixture from prior
     `freddy fixture discriminate` cache, if available.
  3. Read the current anchor/rotating partition from the manifest.
  4. POST to /invoke/system_health/saturation with body:
       {"role": "saturation", "mode": "rotation_proposal",
        "pool": <pool>, "cycle_events": <per-fixture>,
        "discriminability_history": <per-fixture>,
        "current_partition": <from manifest>}
  5. Print the agent's proposed partition + reasoning.
  6. If operator approves, rewrite the manifest's `rotation` block and commit
     the diff to docs/plans/rotation-policy-log.md (the manifest itself lives
     out of repo; the LOG of changes is committed so partition drift is auditable).

CADENCE: monthly. Runs as `claude --print --input-file rotation-policy.md
         --var pool=holdout-v1 --var manifest_path=~/.config/gofreddy/holdouts/holdout-v1.json`.

DATA MATURITY: the agent's output is only useful when ≥3 months of saturation
         events have accumulated. Before that, the initial Phase 1 taxonomy
         partition is authoritative — skip monthly runs for the first 90 days
         post-MVP.
```

Fixtures with consistently high discriminability and low MAD over 3+ months stabilize into the anchor set; saturated or low-signal fixtures rotate out. No specialized rotation agent and no new autoresearch Python beyond the existing `call_quality_judge` shim.

- [ ] **Step A: Dispatch a fixture-authoring agent per fixture (no new CLI command)**

Per-fixture authoring is an orchestration task, not a reusable CLI. An authoring agent reads the scratch spec, drives the existing `freddy fixture {validate, envs, refresh, dry-run, discriminate}` primitives, calls the system-health agent at the health-decision point, and atomically appends to the manifest on a `healthy` verdict. The agent handles edge cases (env-var gaps, partial refresh state, duplicate ids) via reasoning, not rigid branches.

**Authoring agent task spec** (`docs/agent-tasks/author-holdout-fixture.md`):

```
GOAL: author one holdout-v1 fixture end-to-end from a scratch spec JSON.
      Either append to the target manifest on `healthy` verdict, or halt
      with a revision recommendation.

INPUTS:
  - fixture_id (string)
  - spec_path (path to scratch one-fixture manifest)
  - pool=holdout-v1, manifest_path, baseline=v006, seeds=5
  - discriminate_against (two pinned variants, e.g. "v001,v020")

STEPS (use reasoning for recovery, not rigid branches):
  1. `freddy fixture validate <spec_path>` — fail fast on schema.
  2. `freddy fixture envs <spec_path> --missing` — refuse with clear
     diagnostic if any vars are unset.
  3. `freddy fixture refresh <id> --manifest <spec_path> --pool <pool> --dry-run`
     for cost; then actual refresh (same command without --dry-run).
  4. `freddy fixture dry-run <id> --manifest <spec_path> --pool <pool>
     --baseline <baseline> --seeds <seeds>` — collects per-seed scores + cost
     and calls `system_health.fixture_quality` for a verdict ∈ {healthy, saturated, degenerate, unstable, cost_excess, unclear, needs_revision}.
  5. `freddy fixture discriminate <id> --manifest <spec_path> --pool <pool>
     --variants <discriminate_against> --seeds 10` — emits raw per-variant
     per-seed score distributions and calls system_health.discriminability.
  6. POST to evolution-judge-service `/invoke/system_health/fixture_quality`
     with all evidence. Verdict ∈ {healthy, saturated, degenerate, unstable,
     cost_excess, unclear, needs_revision}.
  7. On `healthy`: atomically append spec to target manifest. On `unclear`:
     log `kind="judge_abstain"` and exit 2 — operator reviews raw stats.
     On `needs_revision`: print actionable diff guidance + exit 1 (operator
     revises spec and retries). Any other verdict: print reasoning + exit 1.

EDGE CASES TO RECOVER FROM (without human intervention unless truly stuck):
  - partial refresh state from a prior attempt → decide reuse vs re-fetch
    based on cache age + content hash (ask system_health `content_drift`)
  - mid-pipeline failure → leave manifest untouched, report state
  - duplicate fixture_id → refuse; require explicit operator override

IDEMPOTENCY: re-running against the same fixture_id is safe if the prior
  run left the manifest untouched. If the manifest already contains the id,
  refuse without an explicit overwrite flag in the prompt.
```

Per-fixture invocation:

```bash
cat > /tmp/fixture-draft.json <<'EOF'
{"suite_id": "holdout-v1", "version": "1.0", "domains": {"geo": [{
  "fixture_id": "geo-bmw-ev-de", "client": "bmw",
  "context": "https://www.bmw.de/.../elektromobilitaet.html",
  "version": "1.0", "max_iter": 15, "timeout": 1200,
  "anchor": true, "env": {}
}]}}
EOF

# Dispatch the authoring agent (claude --print with the task spec above
# and the per-fixture inputs). The agent orchestrates existing primitives;
# no new CLI command is required.
claude --print --input-file docs/agent-tasks/author-holdout-fixture.md \
  --var fixture_id=geo-bmw-ev-de \
  --var spec_path=/tmp/fixture-draft.json \
  --var pool=holdout-v1 \
  --var manifest_path=~/.config/gofreddy/holdouts/holdout-v1.json \
  --var baseline=v006 --var seeds=5 --var discriminate_against=v001,v020
```

Run 16 times, once per row in the 16-fixture composition table above. Anchor/rotating split is carried by the `anchor: true/false` field in each spec.

**Why agent task, not CLI:** the pipeline has recovery-worthy edge cases (stale partial cache, env-var gaps, mid-pipeline failure). An agent reasons about whether pre-existing cache is reusable; a CLI with `if`-branches can't. The pipeline also runs ~16 times total — the amortization argument for a reusable CLI doesn't hold.

- [ ] **Step 8: Create redacted example file**

After all 16 fixtures are in `holdout-v1.json`, create `autoresearch/eval_suites/holdout-v1.json.example` as a redacted copy (mask brand names and private URLs; include `"is_redacted_example": true` at the top level as the loader-refusal sentinel). Reference only — never loaded.

- [ ] **Step 9: Set env wiring, exclude holdout dirs from backup/sync, and enforce holdout safety in code**

**9a. Shell profile env wiring.** Add to your shell profile (`~/.zshrc` or equivalent):

```bash
export EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/holdouts/holdout-v1.json
export EVOLUTION_PRIVATE_ARCHIVE_DIR=~/.local/share/gofreddy/holdout-runs
```

**9b. File permissions on first create.**

```bash
chmod 600 ~/.config/gofreddy/holdouts/holdout-v1.json
chmod 700 ~/.config/gofreddy/holdouts/
chmod 700 ~/.local/share/gofreddy/holdout-runs/
chmod 700 ~/.local/share/gofreddy/fixture-cache/holdout-v1/  # created by first `freddy fixture refresh`
```

**9c. Exclude from backup/sync daemons.** 600 perms stop other local users, not backup/sync agents running as the same user. Add exclusions for each tool present on this machine:

```bash
# macOS Time Machine (immediate effect)
sudo tmutil addexclusion ~/.config/gofreddy/holdouts
sudo tmutil addexclusion ~/.local/share/gofreddy/holdout-runs
sudo tmutil addexclusion ~/.local/share/gofreddy/fixture-cache/holdout-v1

# Spotlight index (reduces search-leak surface)
touch ~/.config/gofreddy/holdouts/.metadata_never_index
touch ~/.local/share/gofreddy/holdout-runs/.metadata_never_index

# Generic cache-aware backup tools honor CACHEDIR.TAG
cat > ~/.local/share/gofreddy/fixture-cache/holdout-v1/CACHEDIR.TAG <<'EOF'
Signature: 8a477f597d28d172789f06886806bc55
# Tells CACHEDIR.TAG-aware backup tools (restic, borg, many cloud agents) to skip.
EOF
```

Also verify these paths are not inside iCloud / Dropbox / Syncthing / chezmoi sync roots, including the shell-profile file that exports `EVOLUTION_HOLDOUT_MANIFEST` (the export line itself reveals the path).

**9e. Enforce it in code so misconfiguration cannot silently leak holdout context.** Modify `autoresearch/evaluate_variant.py:_load_holdout_manifest` to add three guards before it returns a manifest. **Per the Post-Plan-A implementation notes above, guard (c) `is_redacted_example` is already shipped in Plan A gap-closure commit `0892ec1` — only add (a) and (b) below.** Verify via `grep -n "is_redacted_example" autoresearch/evaluate_variant.py` before editing:

```python
def _load_holdout_manifest(env: dict[str, str], lane: str = "core") -> dict[str, Any] | None:
    lane = normalize_lane(lane)
    manifest_path_str = env.get("EVOLUTION_HOLDOUT_MANIFEST", "").strip()
    if not manifest_path_str:
        return None

    # Resolve symlinks + relative parts before any check. Defeats
    # `~/holdout.json -> /repo/.../holdout-v1.json.example` symlink attacks.
    manifest_path = Path(manifest_path_str).expanduser().resolve(strict=False)

    # Guard 1: refuse the in-repo example file or any path resolving
    # inside the repo. Walks parents looking for a `.git` ancestor.
    if manifest_path.name.endswith(".example"):
        raise RuntimeError(
            f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
            "holdout must live outside the repo. Example files are reference-only."
        )
    for ancestor in manifest_path.parents:
        if (ancestor / ".git").exists():
            raise RuntimeError(
                f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
                "resolved path is inside a git repo. Holdout must live outside all repos."
            )

    # Guard 2: refuse if file permissions are looser than 600 (group or
    # world can read/write). Prevents accidental leaks via shared systems.
    if manifest_path.exists():
        import stat
        mode = manifest_path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(
                f"EVOLUTION_HOLDOUT_MANIFEST {manifest_path} has loose permissions "
                f"(mode {oct(mode & 0o777)}). Run: chmod 600 {manifest_path}"
            )

    payload = _load_manifest_from_path(str(manifest_path))
    if payload is None:
        return None

    # Guard 3: refuse any manifest carrying the redaction sentinel — that
    # field is set in the in-repo .json.example file and must never match
    # the real holdout manifest.
    if isinstance(payload, dict) and payload.get("is_redacted_example") is True:
        raise RuntimeError(
            f"EVOLUTION_HOLDOUT_MANIFEST refuses {manifest_path} — "
            "payload carries is_redacted_example: true. This is the example file."
        )

    return _normalize_suite_manifest(
        _project_suite_manifest_for_lane(payload, lane),
        env=env,
        source=f"holdout:{lane}",
    )
```

The `autoresearch/eval_suites/holdout-v1.json.example` file (created in Step 8) must therefore include `"is_redacted_example": true` at the top level as a sentinel. Add it.

Also add tests in `tests/autoresearch/test_holdout_manifest_guards.py`:

```python
import json
import stat
from pathlib import Path
import pytest

# Unprefixed import: autoresearch/ is on sys.path via conftest.py.
from evaluate_variant import _load_holdout_manifest


def _write_minimal_holdout(path: Path, *, redacted: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "suite_id": "holdout-v1", "version": "1.0",
        "eval_target": {"backend": "codex", "model": "gpt-5.4"},
        "domains": {"geo": [{"fixture_id": "x", "client": "c", "context": "ctx", "version": "1.0"}]},
    }
    if redacted:
        payload["is_redacted_example"] = True
    path.write_text(json.dumps(payload))
    path.chmod(0o600)


def _env(manifest_path: Path) -> dict[str, str]:
    return {
        "EVOLUTION_HOLDOUT_MANIFEST": str(manifest_path),
        "EVOLUTION_EVAL_BACKEND": "codex",
        "EVOLUTION_EVAL_MODEL": "gpt-5.4",
    }


def test_refuses_example_path(tmp_path):
    fake = tmp_path / "holdout-v1.json.example"
    _write_minimal_holdout(fake)
    with pytest.raises(RuntimeError, match="refuses"):
        _load_holdout_manifest(_env(fake))


def test_refuses_in_repo_path(tmp_path):
    # Simulate a repo by creating a .git marker
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    fake = repo_root / "autoresearch" / "eval_suites" / "holdout-v1.json"
    _write_minimal_holdout(fake)
    with pytest.raises(RuntimeError, match="inside a git repo"):
        _load_holdout_manifest(_env(fake))


def test_refuses_loose_permissions(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake)
    fake.chmod(0o644)
    with pytest.raises(RuntimeError, match="loose permissions"):
        _load_holdout_manifest(_env(fake))


def test_refuses_redaction_sentinel(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake, redacted=True)
    with pytest.raises(RuntimeError, match="is_redacted_example"):
        _load_holdout_manifest(_env(fake))


def test_loads_with_600_perms_and_no_sentinel(tmp_path):
    fake = tmp_path / "holdout-v1.json"
    _write_minimal_holdout(fake)
    result = _load_holdout_manifest(_env(fake))
    assert result is not None
    assert result["suite_id"] == "holdout-v1"
```

Run: `pytest tests/autoresearch/test_holdout_manifest_guards.py -v`
Expected: all 5 PASS.

Commit the guards (the real manifest content is never committed):

```bash
git add autoresearch/evaluate_variant.py tests/autoresearch/test_holdout_manifest_guards.py
git commit -m "feat(holdout): enforce out-of-repo path, 600 perms, and redaction sentinel at load time"
```

**9f. Process-boundary isolation for holdout refresh.**

Same-UID `chmod 600` doesn't stop an adversarial variant prompt from reading the creds file — the threat model must assume the proposer can read anything the evolution process can. Production isolation runs refresh on infrastructure the proposer never touches (GitHub Actions), with a local fallback for dev sessions. Both modes ship.

**GitHub Actions workflow (primary for production runs):**

1. Provision `HOLDOUT_`-prefixed provider keys as GitHub repo secrets: `HOLDOUT_FREDDY_API_KEY`, `HOLDOUT_XPOZ_API_KEY`, `HOLDOUT_OPENAI_API_KEY`, plus `HOLDOUT_MANIFEST_CONTENT_B64` (base64-encoded manifest body — base64 encoding sidesteps the `echo` / variable-expansion fragility that raw JSON multi-line secrets hit).

2. Add `.github/workflows/holdout-refresh.yml`:

```yaml
name: holdout-refresh
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly, Mon 02:00 UTC
  workflow_dispatch:
    inputs:
      fixture_id:
        description: 'Fixture id to refresh (empty = --all-aging)'
        required: false
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -e .
      - name: Materialize holdout manifest from secret
        env:
          HOLDOUT_MANIFEST_CONTENT_B64: ${{ secrets.HOLDOUT_MANIFEST_CONTENT_B64 }}
        run: |
          printf '%s' "$HOLDOUT_MANIFEST_CONTENT_B64" | base64 -d > /tmp/holdout-v1.json
          chmod 600 /tmp/holdout-v1.json
          jq -e '.suite_id == "holdout-v1"' /tmp/holdout-v1.json > /dev/null
      - name: Refresh holdout cache
        env:
          FREDDY_API_KEY: ${{ secrets.HOLDOUT_FREDDY_API_KEY }}
          XPOZ_API_KEY: ${{ secrets.HOLDOUT_XPOZ_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.HOLDOUT_OPENAI_API_KEY }}
        run: |
          # PREREQUISITE: this step requires the refresh CLI-signature fix in
          # docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md to
          # have shipped. Without it, competitive / storyboard / visibility /
          # search-ads / search-content fixtures fail refresh because
          # sources.json declares `args_from: ["context"]` and those CLIs
          # require flags (--brand, --platform, etc.). Until that fix ships,
          # restrict holdout-v1 authoring to geo-scrape + monitoring-UUID
          # sources only (see the MVP "8 fixtures" carve-out in Phase 2).
          FIXTURE="${{ github.event.inputs.fixture_id }}"
          if [ -z "$FIXTURE" ]; then
            freddy fixture refresh --manifest /tmp/holdout-v1.json --pool holdout-v1 --all-aging --isolation ci
          else
            freddy fixture refresh "$FIXTURE" --manifest /tmp/holdout-v1.json --pool holdout-v1 --isolation ci
          fi
      - name: Upload cache artifacts
        uses: actions/upload-artifact@v4
        with:
          name: holdout-cache
          path: ~/.local/share/gofreddy/fixture-cache/holdout-v1/
          retention-days: 90
```

3. Operator fetches refreshed cache onto the evolution machine via `gh run download <run-id>`. The evolution machine never has the holdout credentials, only the resulting cache artifacts.

4. Guardrail: a pre-commit hook refuses any commit containing `HOLDOUT_FREDDY_API_KEY` / `HOLDOUT_XPOZ_API_KEY` / `HOLDOUT_OPENAI_API_KEY` strings outside `.github/workflows/holdout-refresh.yml`, preventing accidental leakage of credential references into proposer-visible files. Implement as a ~10-line `scripts/pre-commit-holdout-guard.sh` wired into `.git/hooks/pre-commit`.

**Local-dev fallback:** for sessions where CI is overkill (e.g. rapid iteration on a single fixture's spec), source credentials from `~/.config/gofreddy/holdouts/.credentials` (chmod 600) and invoke `freddy fixture refresh ... --isolation local`. The proposer runs as the same OS user and CAN read `.credentials` if instructed — this is a documented trust-boundary shortcut. Commit messages for production runs using `--isolation local` must explicitly call it out.

**9g. `--isolation {ci|local}` flag on `freddy fixture refresh`.**

The isolation check runs as a precondition inside `freddy fixture refresh` whenever `--pool holdout-v1` (or any pool with `on_miss: hard_fail`). The operator declares intent explicitly; refresh validates the env matches and refuses on mismatch. No auto-detection heuristic, no judge fallback — four boolean env checks.

```python
# cli/freddy/commands/fixture.py — refresh_cmd gains --isolation {ci,local}

def _require_isolation(mode: str) -> None:
    """Validate the env matches the declared isolation mode; raise otherwise.

    Four boolean checks, no heuristics. Operator knows which mode they're
    running; the flag makes intent explicit and the validator enforces it.
    """
    if mode == "ci":
        missing = [k for k in ("GITHUB_ACTIONS", "HOLDOUT_FREDDY_API_KEY",
                               "HOLDOUT_XPOZ_API_KEY") if k not in os.environ]
        if missing:
            raise typer.BadParameter(
                f"--isolation ci requires env vars {missing} — refusing refresh"
            )
        return
    if mode == "local":
        creds = Path("~/.config/gofreddy/holdouts/.credentials").expanduser()
        if not creds.exists():
            raise typer.BadParameter(
                "--isolation local requires ~/.config/gofreddy/holdouts/.credentials"
            )
        return
    raise typer.BadParameter(f"--isolation must be 'ci' or 'local', got {mode!r}")
```

Tests `tests/freddy/fixture/test_refresh_isolation.py`:
- `test_ci_passes_with_env_set` — sets GITHUB_ACTIONS+HOLDOUT_*, refresh proceeds
- `test_ci_fails_with_missing_secrets` — sets GITHUB_ACTIONS only, refuses
- `test_local_passes_with_credentials_file` — creates tmp credentials file, passes
- `test_local_fails_without_credentials_file` — absent file, refuses

Commit:
```bash
git add cli/freddy/commands/fixture.py tests/freddy/fixture/test_refresh_isolation.py \
        .github/workflows/holdout-refresh.yml scripts/pre-commit-holdout-guard.sh
git commit -m "feat(holdout): --isolation {ci|local} + GitHub Actions workflow + pre-commit creds guard"
```

- [ ] **Step 10: Verify holdout loads end-to-end**

Run from the repo root (the `autoresearch/` directory is not a Python package, so add it to `sys.path` explicitly — or `cd autoresearch && python -c "..."`):

```bash
python -c "import sys; sys.path.insert(0, 'autoresearch'); from evaluate_variant import _load_holdout_manifest; import os; m = _load_holdout_manifest(dict(os.environ)); print(m['suite_id'], sum(len(m['domains'].get(d, [])) for d in ['geo','competitive','monitoring','storyboard']))"
```
Expected: `holdout-v1 16`

Note: this command requires `EVOLUTION_HOLDOUT_MANIFEST`, `EVOLUTION_EVAL_BACKEND`, and `EVOLUTION_EVAL_MODEL` env vars to be set in the current shell. If any are missing, `_load_holdout_manifest` / its manifest-normalization helper will raise — which is itself useful validation.

- [ ] **Step 11: Commit the example file (real manifest NEVER committed)**

```bash
git add autoresearch/eval_suites/holdout-v1.json.example
git commit -m "feat(holdout-v1): add redacted example holdout manifest"
```

---

## Phase 3: Search-v1 Modest Expansion (6-8 fixtures)

**Purpose:** Fill search-v1 coverage gaps from Phase 1 with fixtures representing realistic agency work (NOT adversarial probes — those are in holdout).

**Files:**
- Modify: `autoresearch/eval_suites/search-v1.json` (append new fixtures, bump manifest version 1.0 → 1.1)

**Suggested targets** (exact fill depends on Phase 1 taxonomy output):

| Candidate | Domain | Gap filled |
|---|---|---|
| geo-airbnb-es | geo | lang=es, vertical=travel |
| geo-tesla-model-y-us | geo | vertical=auto (US version — pairs with holdout German BMW) |
| competitive-wise-vs-remitly | competitive | vertical=fintech, global money transfer |
| competitive-hellofresh-vs-home-chef | competitive | vertical=CPG/DTC |
| monitoring-netflix | monitoring | vertical=media, US but non-SaaS |
| monitoring-maersk | monitoring | vertical=shipping, geo=EU |
| storyboard-dude-perfect | storyboard | sports creator, underrepresented genre |
| storyboard-kurzgesagt-de | storyboard | educational, lang=de |

Pick 6-8 from this list (or equivalents identified in Phase 1). Each must fill a genuine gap on the taxonomy matrix.

**Per-fixture process** (lightweight inline loop — search-v1 fixtures have no privacy concerns, so no agent-orchestrated pipeline is needed; the operator drives the primitives directly):

- [ ] **Step 1: Per-fixture authoring loop**

For each of the 6-8 search expansion fixtures, run:

1. Write fixture spec to a scratch manifest
2. `freddy fixture validate <scratch>`
3. `freddy fixture envs <scratch> --missing`
4. `freddy fixture refresh <fixture_id> --dry-run` then without dry-run
5. `freddy fixture dry-run <fixture_id> --baseline v006 --seeds 5`. Exit codes per Plan A Phase 7:
   - **0 (healthy)**: proceed to step 6
   - **1 (saturated / degenerate / unstable / cost_excess / needs_revision)**: revise the spec and retry
   - **2 (unclear)**: quality-judge abstained; manually review the raw stats + reasoning before deciding to retry or drop the fixture — do NOT treat as automatic rejection
6. Append to `autoresearch/eval_suites/search-v1.json` (NOT holdout-v1.json)
7. `freddy fixture discriminate <fixture_id> --variants v_low,v_high` (optional; anchor-style search fixtures benefit from a discriminability check)

Substitute `--pool search-v1` everywhere and commit to the in-repo manifest. Holdout fixtures use the authoring-agent task instead (Phase 2 Step A) because the 16-fixture pipeline needs recovery-worthy edge-case handling; public-suite fixtures don't.

One commit per fixture is fine — small commits make review easier:

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): add geo-airbnb-es fixture (lang=es, vertical=travel)"
```

- [ ] **Step 9: Set manifest version to 1.1**

After all new fixtures are added, set the suite-level `version` field in `autoresearch/eval_suites/search-v1.json` to `"1.1"`.

**Precondition:** Plan A Phase 1 (schema backfill) is expected to have already added `"version": "1.0"` at the suite level and stamped each existing fixture with `"version": "1.0"`. If the field is still absent when you open the file, that backfill has not landed yet — stop and resolve ordering before continuing.

Verify by reading the file:

```bash
python -c "import json; print(json.load(open('autoresearch/eval_suites/search-v1.json')).get('version'))"
```
Expected: `1.0` (before this step) → `1.1` (after this step).

Then apply the edit. Run:

```bash
freddy fixture validate autoresearch/eval_suites/search-v1.json
```
Expected: PASS with `search-v1@1.1: N fixture(s)` where N = 23 + (number added).

- [ ] **Step 10: Commit version bump**

```bash
git add autoresearch/eval_suites/search-v1.json
git commit -m "feat(search-v1): bump manifest version to 1.1 (v1.0 scores not comparable; rescore in Phase 4)"
```

---

## Phase 4: Migration — Existing search-v1 Onto New Infrastructure

**Purpose:** Every existing search-v1 fixture needs a cache entry and a baseline dry-run record. This is mechanical work but must happen before Phase 5 (canary) can run with cache-backed evaluation.

**Files:**
- Populate: `~/.local/share/gofreddy/fixture-cache/search-v1/...` for all ~30 fixtures
- Create: `docs/plans/search-v1-migration-scores.md` — table of baseline scores per fixture

- [ ] **Step 1: Batch refresh all search-v1 fixtures (with content-hash baseline)**

⚠️ **Blocked until `docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md` ships.** The current refresh path passes `fixture.context` as a positional arg to every source command. This works for geo (scrape) and monitoring (monitor/{mentions,sentiment,sov}) fixtures, but **errors out for competitive (search-ads), storyboard (search-content), and the visibility source**. A `--all-stale` batch will abort on the first non-scrape/non-monitor fixture.

**Workaround until the fix lands**: refresh only the scrape + monitoring fixtures via explicit per-fixture calls:

```bash
# Works today
for fx in geo-semrush-pricing geo-ahrefs-pricing geo-moz-homepage geo-bluehost-shared-hosting geo-mayoclinic-atrial-fibrillation geo-patagonia-nano-puff-pdp; do
  freddy fixture refresh "$fx" --manifest autoresearch/eval_suites/search-v1.json --pool search-v1
done
# Errors until refresh CLI fix: every competitive-* fixture, every storyboard-* fixture, any fixture using freddy-visibility
```

**After the refresh CLI fix ships**, the original batch command works:

```bash
freddy fixture refresh --all-stale --manifest autoresearch/eval_suites/search-v1.json --pool search-v1 --cache-root ~/.local/share/gofreddy/fixture-cache
```

Since no cache exists yet, all fixtures will be refreshed. Log total cost; this is a one-time upfront cost (~$50-150 depending on TikTok monitoring quantity).

Expected: all ~30 cache entries created.

Verify: `freddy fixture staleness --pool search-v1`
Expected: every fixture shows `fresh`.

**Content-hash drift detection (already shipped in Plan A — reference implementation below).** Plan A Phase 4 added `content_sha1: str = ""` to `DataSourceRecord`; Plan A Phase 6 wired `_run_source_fetch` to compute the sha1 on each fetch and emit `log_event(kind="content_drift", ...)` when it changes vs. the prior manifest's record. Verify via `rg 'kind="content_drift"' cli/freddy/fixture/refresh.py`. The code block below is the plan's original reference shape — **do NOT re-apply; it's documentation for the mechanism, not a patch**. If the grep hits, skip forward to Step 2:

```python
# In Plan A's _run_source_fetch, after writing the cache artifact:
new_hash = hashlib.sha1(result.stdout.encode()).hexdigest()
old_record = existing_manifest.lookup(source, data_type, arg)
if old_record and old_record.content_sha1 != new_hash:
    from autoresearch.judges.quality_judge import call_quality_judge
    old_content = (cache_dir / old_record.cached_artifact).read_text()
    verdict = call_quality_judge({
        "role": "content_drift",
        "fixture_id": fixture_id,
        "anchor": bool(fixture.anchor),
        "source": source, "data_type": data_type, "arg": arg,
        "old_content_preview": old_content[:2048],
        "new_content_preview": result.stdout[:2048],
        "old_content_length": len(old_content),
        "new_content_length": len(result.stdout),
    })
    if verdict.verdict == "material":
        from events import log_event
        log_event(kind="content_drift",
                  fixture_id=fixture_id, source=source, data_type=data_type, arg=arg,
                  verdict=verdict.verdict,
                  reasoning=verdict.reasoning, confidence=verdict.confidence)
        sys.stderr.write(
            f"⚠️  fixture {fixture_id} material content drift ({source}/{data_type}): "
            f"{verdict.reasoning}; review before next canary run.\n"
        )
```

Rationale: if a fixture's upstream URL is CDN-hijacked or the brand page is rewritten overnight, fetched content becomes attacker-controlled. Character-level diff ratios alone misfire on ad carousels and timestamps; the system-health agent sees the actual content and reasons about whether the change matters. Applies to both anchor AND rotating fixtures (the agent can factor `anchor` into its reasoning). Wire this into Plan A's `_run_source_fetch` as an additional step before Phase 4 Step 1 runs. SHA1 comparison is a cheap cache-invalidation optimization (skip the agent call when nothing changed); the judgment about material vs cosmetic belongs entirely to the agent.

- [ ] **Step 2: Dispatch a migration-sweep agent across `search-v1` (no new CLI command)**

The 30-fixture sweep happens once. An orchestration agent enumerates the manifest, invokes `freddy fixture dry-run` per fixture, collects raw per-seed scores + cost, POSTs the batch to `system_health.fixture_quality` for verdicts, and writes the markdown report. Handles edge cases (skipped fixtures, stale-during-sweep, mid-run failure) via reasoning rather than rigid branches.

**Migration-sweep agent task spec** (`docs/agent-tasks/migrate-search-pool.md`):

```
GOAL: migrate every fixture in a pool's manifest onto the new fixture
      infrastructure. Produce a markdown report with per-fixture verdicts.
      Exit non-zero if any fixture is not `healthy`.

INPUTS:
  - manifest_path (e.g. autoresearch/eval_suites/search-v1.json)
  - pool (e.g. search-v1)
  - baseline (e.g. v006)
  - seeds (default 5)
  - output_path (e.g. docs/plans/search-v1-migration-scores.md)

STEPS:
  1. Parse the manifest via `freddy fixture validate --manifest <path>`.
  2. Record sweep_started_at.
  3. For each (domain, fixture) in the manifest:
       a. `freddy fixture dry-run <fixture> --manifest <manifest_path>
          --pool <pool> --baseline <baseline> --seeds <seeds>` — the command
          internally calls system_health.fixture_quality and returns the
          verdict + raw per-seed scores + cost.
       b. Collect the output row.
  4. Render the markdown table from the collected rows.
  5. Check for fixtures that aged during the sweep (cache mtime older than
     sweep_started_at minus one cycle). For any stale, re-dry-run + re-verdict.
  6. Render markdown atomically (build in memory, single write).
  7. Exit non-zero if any verdict is not `healthy`.

EDGE CASES TO RECOVER FROM:
  - per-fixture dry-run failure → record error row, continue sweep
  - cache aging during sweep → re-refresh + re-verdict, note in report
  - mid-run interruption → leave output file untouched (atomic write only)

IDEMPOTENCY: re-running is safe; the dry-run command does not mutate shared
  state. The markdown file is overwritten each run.
```

Per-pool invocation:

```bash
claude --print --input-file docs/agent-tasks/migrate-search-pool.md \
  --var manifest_path=autoresearch/eval_suites/search-v1.json \
  --var pool=search-v1 --var baseline=v006 --var seeds=5 \
  --var output_path=docs/plans/search-v1-migration-scores.md
```

Output: `docs/plans/search-v1-migration-scores.md` with per-fixture rows (fixture_id / domain / median / MAD / cost / verdict / reasoning). Median / MAD are computed in the dry-run command *for the human-facing report only* — the `system_health.fixture_quality` verdict is produced by the agent reading raw per-seed scores, not summary statistics.

**Why agent task, not CLI:** same reasoning as Phase 2 Step A — recovery-worthy edge cases, one-shot execution, and composition over new Python.

- [ ] **Step 2a: Emit per-cycle saturation events into the unified events log**

No `saturation_log.py` module, no aggregator, no beat-rate summarizer, no threshold. At the end of `evaluate_variant.py::evaluate_search`, after per-fixture scores + baseline comparison are known, emit one event per public-suite fixture:

```python
# autoresearch/evaluate_variant.py — end of evaluate_search
from events import log_event  # Phase 0a unified log

for fixture_id, fixture_score, baseline_score in per_fixture_results:
    log_event(kind="saturation_cycle",
              cycle_id=cycle_id_from_variant(variant_id),
              fixture_id=fixture_id,
              candidate_score=fixture_score,
              baseline_score=baseline_score,
              baseline_beat=(fixture_score > baseline_score))
```

That's the whole write path — ~8 lines inside the existing finalize loop. No new module.

- [ ] **Step 2b: `freddy fixture staleness` surfaces saturation verdicts via the system-health agent**

Extend Plan A's `freddy fixture staleness` to call `system_health.saturation` in a single batched request. The agent reads `events.jsonl` directly (on the judge-service side, via the payload) and decides per-fixture whether to rotate. No code-side aggregation.

```python
# cli/freddy/commands/fixture.py::staleness_cmd — additional block
from autoresearch.judges.quality_judge import call_quality_judge

# Gather per-fixture cycle events from the unified log.
events_log = Path.home() / ".local/share/gofreddy/events.jsonl"
per_fixture_events: dict[str, list[dict]] = {}
if events_log.exists():
    for line in events_log.read_text().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("kind") != "saturation_cycle":
            continue
        fid = entry.get("fixture_id")
        if fid:
            per_fixture_events.setdefault(fid, []).append(entry)

# One batched call; agent returns a per-fixture verdict.
batch_items = [
    {"fixture_id": fid, "cycle_events": events}
    for fid, events in per_fixture_events.items()
    if len(events) >= 5  # cost guard: don't ask about fixtures with <5 data points
]
verdicts = {}
if batch_items:
    result = call_quality_judge({"role": "saturation", "items": batch_items})
    verdicts = {v["fixture_id"]: v for v in result.get("items", [])}

# In per-row render:
v = verdicts.get(row["fixture_id"])
if v and v.get("verdict") == "rotate_now":
    row["status"] = f"{row['status']} SATURATED"
```

The agent receives the **raw** cycle-event stream per fixture (candidate_score, baseline_score, baseline_beat flag) and decides. No recent_beat_rates() helper, no "how many beats out of how many cycles" summary statistic, no threshold. The agent's prompt knows saturation patterns (high beat rate sustained, vs. high-quality fixture on a strong proposer) and reasons from the raw history.

The `len(events) >= 5` skip is **not a judgment threshold** — it's a cost guard. Asking the agent to verdict a fixture with 2 cycles is paying for a judge call that can only return "insufficient data."

Tests: `tests/freddy/fixture/test_staleness_saturation.py` writes a fake `events.jsonl` with saturation_cycle entries across two fixtures, mocks `call_quality_judge` to return `[{"fixture_id": "geo-a", "verdict": "rotate_now"}, {"fixture_id": "geo-b", "verdict": "fine"}]`, invokes staleness, asserts `SATURATED` appears only on the geo-a row.

Commit:

```bash
git add autoresearch/evaluate_variant.py \
        cli/freddy/commands/fixture.py \
        tests/freddy/fixture/test_staleness_saturation.py
git commit -m "feat(fixture): emit saturation_cycle events; staleness surfaces agent verdict (no aggregator, no threshold)"
```

- [ ] **Step 3: Run autoresearch test suite**

Run: `pytest tests/autoresearch/ -x -q`
Expected: all pass. (Any canary-dependent tests should have been updated in Plan A Phase 11.)

- [ ] **Step 3b: Judge calibration anchor + drift detection**

> **⚠️ MVP CARVE-OUT (2026-04-23): DEFERRED to [`docs/plans/2026-04-23-004-judge-calibration-drift.md`](2026-04-23-004-judge-calibration-drift.md).** The full bi-directional cross-family drift-detection system (`judge_calibration.py`, monthly cron, PR-gated baseline deploys) builds infrastructure for drift that has not been observed. MVP replacement: once per month, run the 3-5 calibration variants × 3-5 search-v1 fixtures through `evaluate_variant.py` and append each score as a `kind="calibration_score"` event in `events.jsonl`. No automated drift verdict, no cron, no bi-directional aggregation. Data accumulates; the follow-up plan can reason about it later. **Execute the log-only note below; skip the full Step 3b code.**

Single-judge systems drift over time: model updates, provider rerankings, subtle prompt changes can all shift score distributions. Without a calibration anchor, we have no way to detect when "v007 scored 0.65 last month" means something different this month.

(i) Pick 3-5 **calibration variants** — historically stable variants with known-stable behavior, e.g., `v001`, `v006`, `v020`. Pick a **calibration fixture subset** (3-5 search-v1 fixtures spanning the 4 domains, no anchors).

(ii) Create `autoresearch/judge_calibration.py`:

```python
"""Judge calibration anchor — cross-family drift detection.

Monthly: `python autoresearch/judge_calibration.py --check`. Rescores a fixed
set of (variant, fixture) pairs with BOTH families and delegates the drift
decision to the system-health agent — Claude reads Codex's baseline+current
traces to judge Codex's drift, and vice-versa. Cross-family removes the
self-bias that would plague a same-family drift check.

Baseline lives on the judge-service filesystem (see Plan A Phase 0c isolation)
and stores both families' scores AND reasoning traces per pair. Deploys to
the baseline go through PR-gated `deploy-evolution-judge.yml` — no runtime
mutation API on evolution-judge-service. Rebaseline on any judge model
migration; record the CLI versions used.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Baseline lives on judge-service side (Phase 0c boundary). The autoresearch-
# side client calls /invoke/system_health/calibration_drift with the pair
# identifiers; the judge service loads the stored baseline + current traces,
# dispatches Claude-judging-Codex and Codex-judging-Claude, and returns an
# aggregated verdict. Autoresearch never sees the baseline contents.


def check() -> int:
    """Monthly drift check — single HTTP call, aggregated cross-family verdict.

    Pair identifiers live in .config/gofreddy/calibration-pairs.json (PR-gated
    on the judge-service side). Autoresearch holds only the identifiers —
    scoring and drift-detection logic live judge-side.
    """
    from autoresearch.judges.quality_judge import call_quality_judge
    cfg_path = Path(".config/gofreddy/calibration-pairs.json")
    if not cfg_path.exists():
        print("ERROR: no calibration-pairs config; deploy one via PR before --check.", file=sys.stderr)
        return 2
    pairs = json.loads(cfg_path.read_text())["pairs"]
    verdict = call_quality_judge({
        "role": "calibration_drift",
        "pairs": pairs,  # identifiers only; judge-service loads baselines
        "check_timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Judge-service emits kind="judge_drift" on its own events log with full
    # baseline+reasoning comparisons (Phase 0c boundary). Autoresearch just
    # mirrors the top-line verdict for its own lineage.
    from events import log_event
    log_event(kind="judge_drift",
              verdict=verdict.verdict,
              reasoning=verdict.reasoning,
              confidence=verdict.confidence)
    if verdict.verdict == "stable":
        print(f"judge calibration clean: {verdict.reasoning}")
        return 0
    print(f"⚠️  judge drift: {verdict.verdict} — {verdict.reasoning}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--check":
        sys.exit(check())
    print(f"Usage: {sys.argv[0]} --check  (rebaselining is a PR-gated judge-service operation)", file=sys.stderr)
    sys.exit(2)
```

**Cross-family drift detection (judge-service side, bi-directional).** The agent prompt for `role="calibration_drift"` routes each pair through four fresh CLI invocations:

1. Codex (gpt-5.4) scores the pair with current prompts → get current Codex trace
2. Claude (Opus 4.7) scores the pair with current prompts → get current Claude trace
3. Load baseline (both families' scores + reasoning traces stored judge-side from a one-time file-based anchor)
4. Invoke Claude with `"be maximally skeptical; compare baseline trace to current trace; superficial phrasing changes are NOT drift; changes in which criteria get weighted ARE drift"` → Claude reads Codex's baseline + current traces, returns a per-pair verdict on Codex drift
5. Invoke Codex with the same skeptical framing → Codex reads Claude's baseline + current traces, returns a per-pair verdict on Claude drift
6. Aggregate: if either family flags any pair as `reasoning_drift` / `variance_drift` / `magnitude_drift`, overall verdict is drifted; otherwise `stable`

Neither family self-judges. Baseline storage + PR-gated judge-service prompt deploy (via Plan A Phase 0c's merge-to-main → local-daemon.sh restart) prevents runtime tampering. Skeptical prompt framing fights the "same-ish" default.

**Why bi-directional:** one-direction would miss correlated drift — if Claude *also* drifts in the same direction as Codex (both services update underlying model versions in the same week), Claude reading Codex's traces may look "stable" while both have shifted together. Bi-directional catches this: correlated drift would show up as both families flagging each other. When either judge family lands a major version update, also invalidate the baseline and re-record from scratch — that's the one failure mode bi-directional can't detect on its own.

(iii) Record the baseline now (one-time, after Phase 4 Step 2 migration scores exist):

```bash
python autoresearch/judge_calibration.py --check  # baselines are PR-gated deploys to judge-service; --record-baseline is not a runtime op
```

(iv) Add a monthly cron / manual-reminder entry in `autoresearch/README.md` "Operational notes":

> **Judge drift check:** run `python autoresearch/judge_calibration.py --check` monthly. Non-zero exit indicates the quality-judge has determined the scoring distribution has materially drifted; investigate before trusting new scores in promotion decisions. The judge sees the full baseline and current distributions and decides — no fixed 2×MAD threshold.

(v) Add a test `tests/autoresearch/test_judge_calibration.py` that mocks both `_score` and `call_quality_judge`, writes a synthetic baseline, verifies `check()` returns 0 when the mocked judge says `stable` and 1 when it says any drift verdict (`magnitude_drift`, `variance_drift`, `reasoning_drift`, or `mixed`).

Commit:

```bash
git add autoresearch/judge_calibration.py tests/autoresearch/test_judge_calibration.py autoresearch/README.md
git commit -m "feat(autoresearch): judge calibration anchor + monthly drift-detection check"
```

- [ ] **Step 4: Run one full evolution iteration against v006 end-to-end — and pin the lane head so Phase 5 starts from a known baseline**

`evolve.sh score-current` is deprecated (removed per `autoresearch/evolve.py:102-106`; scoring now runs as the pre-flight step of `evolve.sh run`). Use a single `run` iteration instead, which exercises the pre-flight scoring against cache:

```bash
# Pin the lane head BEFORE the migration check so we can detect if the
# check auto-promoted a candidate and moved the baseline Phase 5 depends on.
CORE_HEAD_BEFORE=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
echo "core lane head before migration check: $CORE_HEAD_BEFORE" >&2

./autoresearch/evolve.sh run --iterations 1 --candidates-per-iteration 1 --lane core

# Assert the lane head did not move. If it did, the one-iteration check
# auto-promoted a candidate and the Phase 5 canary would no longer be
# starting from v006. Roll back.
CORE_HEAD_AFTER=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
if [ "$CORE_HEAD_AFTER" != "$CORE_HEAD_BEFORE" ]; then
    echo "ERROR: migration check auto-promoted $CORE_HEAD_AFTER over $CORE_HEAD_BEFORE" >&2
    echo "Rolling back: ./autoresearch/evolve.sh promote --undo --lane core" >&2
    ./autoresearch/evolve.sh promote --undo --lane core
    # Re-verify
    CORE_HEAD_AFTER=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['core'])")
    [ "$CORE_HEAD_AFTER" = "$CORE_HEAD_BEFORE" ] || { echo "Rollback failed"; exit 1; }
fi
echo "core lane head pinned: $CORE_HEAD_AFTER"
```

Expected: pre-flight re-scores v006 on `search-v1@1.1` with cache-first behavior, then produces one new candidate variant. The pre-flight-recorded v006 score should be in the same ballpark as v006's pre-migration score (± judge noise). The lane head ends at `$CORE_HEAD_BEFORE` regardless of whether the new candidate was promotion-eligible.

If score drifts significantly: investigate cache integration (Plan A Phase 8) before proceeding.

- [ ] **Step 5: Commit migration record**

```bash
git add docs/plans/search-v1-migration-scores.md autoresearch/GAPS.md
git commit -m "chore(migration): search-v1 fully onboarded to fixture infrastructure (GAPS 2/3/18 partial)"
```

---

## Phase 5: Overfit Canary Experiment

**Purpose:** Validate that holdout actually catches overfitting before enabling autonomous promotion. This is the go/no-go experiment.

**Timing constraint:** Execute Phases 2–5 within ~2 weeks. Monitoring fixtures drift weekly (`most_recent_complete`). If longer, re-run Phase 4 Step 2 before Phase 5 Step 3.

**Files:**
- Create: `docs/plans/overfit-canary-results.md`

- [ ] **Step 1: Freeze both suites**

Record: `search-v1@1.1`, `holdout-v1@1.0`. No fixture changes during the experiment.

- [ ] **Step 2: Select lane**

Pick `geo` (highest OOD coverage in holdout-v1 per the taxonomy).

- [ ] **Step 2.5: Pre-canary sanity — holdout must discriminate + anchor variants must be representative**

This step combines two sanity checks that together prevent the three most likely "canary runs but verdict is meaningless" failure modes.

**(a) Holdout must discriminate a known-different variant pair.** Score `(v001, v020)` on holdout before burning a 20-iteration canary:

```bash
EVOLUTION_HOLDOUT_MANIFEST=~/.config/gofreddy/holdouts/holdout-v1.json \
python autoresearch/evaluate_variant.py autoresearch/archive/v001 autoresearch/archive \
    --search-suite autoresearch/eval_suites/search-v1.json \
    --mode holdout --lane geo
# Repeat for v020
```

Required outcome: `|holdout_score(v020) − holdout_score(v001)| ≥ 0.10`. If under 0.10, holdout can't distinguish overfit-proposer from too-hard-fixtures — abort the canary and revise holdout to include fixtures the known-good pair moves on.

**(b) Anchor variants must still be representative.** `v001`, `v006`, and `v020` are load-bearing in multiple places: `v006` is the baseline for every holdout fixture's authoring dry-run (Phase 2 Step A), `v001` and `v020` are the discriminate-against pair for each new holdout fixture (Phase 2 Step A) and the pre-canary sanity pair above, and all three are the calibration-variant set for judge drift checks (Phase 4 Step 3b). A silent regression in any of them — via upstream model updates, content drift, or a latent bug — would make every holdout fixture look "healthy" and every canary verdict suspect. Re-validate:

```bash
# (b1) v006 still scores healthy on a known-good anchor fixture
freddy fixture dry-run geo-bmw-ev-de \
    --manifest ~/.config/gofreddy/holdouts/holdout-v1.json \
    --pool holdout-v1 --baseline v006 --seeds 5
# Expect: exit code 0 (verdict=healthy). Exit 2 (unclear) → manual review
# before proceeding. Exit 1 (saturated/degenerate/unstable/cost_excess) →
# v006 has drifted; halt Phase 5 and investigate.

# (b2) v001 and v020 are still separable on the anchor
freddy fixture discriminate geo-bmw-ev-de \
    --manifest ~/.config/gofreddy/holdouts/holdout-v1.json \
    --pool holdout-v1 --variants v001,v020 --seeds 5
# Expect: verdict=separable. If not_separable, one of v001/v020 has drifted.
```

If either (b1) or (b2) fails, the canary cannot be trusted — the baselines it uses to define "normal" aren't representative anymore. Halt and investigate before running Phase 5 Step 3.

Document pair scores and anchor-guard results in `docs/plans/overfit-canary-results.md` as Section 1.

- [ ] **Step 2.6: Construct a deliberately-bad variant for the canary to catch**

Without a known-bad variant, the canary can't distinguish "holdout catches overfit" from "holdout was never stressed." If 20 iterations of the natural proposer don't produce enough overfit to trigger divergence, the canary returns GO by default — a null result looks identical to success.

Create `autoresearch/archive/v_canary_overfit/` as a **deliberately-overfit variant** — copy an in-repo variant (e.g. `v006`) and modify its scoring or reasoning prompt so it should score artificially high on search-v1 but fail on holdout. Concrete examples (pick one or combine):

- **Hardcoded rubric cheat:** inject "always emphasize 'comprehensive technical SEO audit' in conclusions" into the variant's reasoning prompt — an in-distribution pattern the search-v1 fixtures reward, but one that shouldn't help on holdout's adversarial fixtures
- **Domain-specific heuristic:** add a hardcoded rule that says "if the URL contains 'saas' or 'pricing', boost GEO-1 score by +0.2" — lifts search-v1 (SaaS-heavy) artificially; no-op or harmful on holdout's non-SaaS verticals
- **Template collapse:** force all outputs into a fixed structural template tuned for search-v1's most common question shape — loses flexibility needed for holdout's non-verbal/cultural-distance fixtures

Run the deliberately-bad variant through ONE canary checkpoint before the 20-iteration run:

```bash
# Score v_canary_overfit on public + holdout at 10 seeds each
for seed in 1 2 3 4 5 6 7 8 9 10; do
  AUTORESEARCH_SEED=$seed python autoresearch/evaluate_variant.py \
    --single-fixture search-v1:geo-semrush-pricing \
    --manifest autoresearch/eval_suites/search-v1.json \
    --seeds 1 --baseline-variant v_canary_overfit --json-output \
    >> /tmp/canary-bad-public.jsonl
  AUTORESEARCH_SEED=$seed python autoresearch/evaluate_variant.py \
    --single-fixture holdout-v1:geo-bmw-ev-de \
    --manifest ~/.config/gofreddy/holdouts/holdout-v1.json \
    --seeds 1 --baseline-variant v_canary_overfit --json-output \
    >> /tmp/canary-bad-holdout.jsonl
done
```

Required outcome: public median − holdout median ≥ 0.15 (a meaningfully wider gap than the natural-proposer pair's 0.10 threshold from Step 2.5a). If under 0.15, either (a) the deliberately-overfit variant isn't actually overfit enough — tune it harder, or (b) holdout is too-similar to public — revise holdout. Don't run the 20-iteration canary until the bad variant demonstrates divergence.

Document the variant's construction (exact prompt diff from its parent) and the public-vs-holdout gap in `docs/plans/overfit-canary-results.md` as Section 2.

- [ ] **Step 3: Run 20 evolution iterations on geo lane**

Run: `./autoresearch/evolve.sh run --lane geo --iterations 20 --candidates-per-iteration 3`

(Note: `run` is an explicit subcommand of `evolve.sh`. Flags on `run`: `--iterations`, `--candidates-per-iteration`, `--lane`, `--archive-dir`, `--backend`, `--model`, `--max-turns`. See `autoresearch/evolve.py:128-183`.)

Expected: ~60 new candidate variants produced (20 × 3), with promoted lane heads updated after each iteration's finalize step. Watch for divergence in evolve.sh output. Total wall-clock: many hours to days depending on session timeouts.

- [ ] **Step 4: Score checkpoints at a fixed cadence**

This is a one-shot go/no-go experiment, not a production workload. Adaptive cadence + noise-escalation agent + primes-seed scheme are deferred — they're a "system for running canaries" when the actual goal is "run THIS canary, once." Fixed cadence delivers the same verdict with none of the judge/prompt wiring.

At each of the checkpoints `{2, 4, 6, 8, 10, 12, 14, 16, 18, 20}`, after `evolve.sh run` finishes that iteration's candidates and finalizes the new lane head:

```bash
# checkpoint iterations: 2 4 6 8 10 12 14 16 18 20
for iter_num in 2 4 6 8 10 12 14 16 18 20; do
  head_id=$(python -c "import json; print(json.load(open('autoresearch/archive/current.json'))['geo'])")
  for seed in 1 2 3 4 5 6 7 8 9 10; do
    AUTORESEARCH_SEED=$seed python autoresearch/evaluate_variant.py \
      --single-fixture search-v1:geo-bmw-ix-de \
      --manifest autoresearch/eval_suites/search-v1.json \
      --seeds 1 --baseline-variant "$head_id" --json-output \
      >> /tmp/canary-public-${iter_num}.jsonl
    AUTORESEARCH_SEED=$seed python autoresearch/evaluate_variant.py \
      --single-fixture holdout-v1:geo-bmw-ev-de \
      --manifest ~/.config/gofreddy/holdouts/holdout-v1.json \
      --seeds 1 --baseline-variant "$head_id" --json-output \
      >> /tmp/canary-holdout-${iter_num}.jsonl
  done
done
```

Each checkpoint produces 10 scores for public + 10 for holdout → median + IQR per series. All 10 × 10 × 2 = 200 evaluations run once, during the canary, and never again.

If the fixed schedule later wastes compute on a real recurring workload, an adaptive scheduler is a legitimate follow-up. Not now.


- [ ] **Step 5: Construct divergence table (raw trajectory, no trend statistics)**

Build the table in `docs/plans/overfit-canary-results.md` with median + IQR per checkpoint:

```markdown
| Iter | Variant | Public median (IQR) | Holdout median (IQR) | Divergence |
|---|---|---|---|---|
| 2  | v007 | 0.50 (0.04) | 0.45 (0.06) | 0.05 |
| 4  | v009 | 0.54 (0.05) | 0.46 (0.07) | 0.08 |
| ... | (10 rows) |
| 20 | v028 | 0.75 (0.04) | 0.48 (0.05) | 0.27 |
```

That's it — the raw trajectory is the input to the canary agent in the next step. No Kendall's tau, no p-value, no scipy. Summary trend statistics were designed to feed threshold decisions ("is tau > 0.7?"); we're not thresholding. The agent reads the 10-row trajectory directly and reasons about monotonicity, noise, and inversion from the raw numbers.

- [ ] **Step 6: Canary agent decides GO / FAIL / REVISE (reads raw trajectory)**

The canary decision — "did the holdout prove that the proposer generalizes, and can we enable autonomous promotion?" — is too context-dependent for a bucket-table classifier. Hand the raw trajectory to the canary agent (role: `canary`, `mode: "go_fail"`):

```python
from autoresearch.judges.promotion_judge import call_promotion_judge

verdict = call_promotion_judge({
    "role": "canary",
    "mode": "go_fail",
    "lane": "geo",
    "holdout_version": "v1.0",
    "checkpoints": [
        {"iter": 2,  "public_median": 0.50, "public_iqr": 0.04,
         "holdout_median": 0.45, "holdout_iqr": 0.06, "divergence": 0.05},
        # ... 10 rows (raw per-checkpoint medians + IQRs; no trend stats)
    ],
    "pre_canary_sanity": {"known_pair_delta": 0.12},  # from Step 2.5
    "prior_canary_verdicts": [],  # list of previous canary attempts on this holdout
})
# verdict.decision ∈ {"go", "fail", "revise"}; verdict.reasoning has the "why".
```

The agent sees the full raw trajectory and reasons about whether divergence is real, whether public is genuinely climbing (not flat), whether pre-canary sanity held, whether holdout appears inverted (public flat + holdout climbing = broken), and whether noise levels permit a confident call. It returns one of:

- `go` — enable autonomous promotion. Record verdict, commit results doc, ship.
- `fail` — holdout not doing its job. Revise rotating holdout fixtures, bump holdout-v1 → v1.1, rerun canary.
- `revise` — signal is present but weak/ambiguous. Judge's reasoning will specify what to do (extend checkpoints, pilot on one lane, revise specific fixtures).

**NO-GO termination rule:** if two consecutive canary runs both return `fail` or `revise`, pause Plan B. The judge's reasoning tells you whether to (a) escalate to the separate MAD-confidence-scoring initiative, (b) ship without autonomous promotion (keep `is_promotable` as operator-triggered), or (c) accept that holdout can't be authored against this proposer. The choice is still human — but the judge tells you why.

Pass `prior_canary_verdicts` on subsequent attempts so the judge can reason about persistent failure modes ("same rotation-tracks-public failure as last attempt → probably not a fixture problem").

- [ ] **Step 7: Document verdict**

Append to `docs/plans/overfit-canary-results.md`:

```markdown
## Verdict

**Status:** [GO | NO-GO]

**Reasoning:** [Free-form paragraph describing what the divergence pattern showed.]

**Next step:** [If GO: proceed to Phase 6 and enable agent-delegated autonomous promotion. If NO-GO: revise holdout and rerun canary.]
```

- [ ] **Step 8: Commit** (fill in verdict before committing)

```bash
git add docs/plans/overfit-canary-results.md
git commit -m "docs(validation): overfit canary <GO|NO-GO> — <one-sentence finding>"
```

If NO-GO, stop here. Return to Phase 2 with holdout-v1.1 revisions, then rerun Phase 5 (subject to Step 6's termination rule).

---

## Phase 6: Enable Autonomous Promotion (Agent-Delegated)

**Purpose:** With holdout validated, turn on autonomous promotion. `is_promotable` becomes a thin context-gathering shim: it collects primary + secondary judge scores across all fixtures, holdout composite scores, first-of-lane baseline state, and per-fixture scores, then POSTs to the promotion agent (`/invoke/decide/promotion`) and returns `promote` / `reject` / `abstain`. One programmatic invariant (wrong-lane short-circuit). The agent reasons about magnitude, consistency across fixtures, cross-family agreement, and regime context together. No hardcoded thresholds.

**Files:**
- Modify: `autoresearch/evolve_ops.py` — strengthen `is_promotable`
- Modify: `autoresearch/README.md` — document new rule
- Create: `tests/autoresearch/test_promotion_rule.py`

- [ ] **Step 1: Write judge-mock tests for promotion rule**

Create `tests/autoresearch/test_promotion_rule.py`. Tests mock `call_promotion_judge` to return specific verdicts and assert `is_promotable` propagates them.

```python
from pathlib import Path
from unittest.mock import patch

# Unprefixed imports: autoresearch/ is on sys.path via conftest.py
from evolve_ops import is_promotable
from autoresearch.judges.promotion_judge import PromotionVerdict


def _entry(variant_id, public_score, *, secondary_public=None):
    """Minimum lineage entry shape for is_promotable.

    scores['composite'] and scores['<lane>'] are read by _objective_score_from_scores
    (see evaluate_variant.py:849). Per-fixture scores live under search_metrics.
    """
    entry = {
        "id": variant_id, "lane": "geo",
        "scores": {"composite": public_score, "geo": public_score},
        "search_metrics": {
            "suite_id": "search-v1", "composite": public_score,
            "domains": {"geo": {"score": public_score, "active": True,
                                "fixtures": {"geo-a": {"score": public_score}}}},
        },
        "promotion_summary": {"eligible_for_promotion": True, "holdout_composite": public_score - 0.05},
    }
    if secondary_public is not None:
        entry["secondary_scores"] = {"composite": secondary_public, "geo": secondary_public}
        entry["promotion_summary"]["secondary_holdout_composite"] = secondary_public - 0.05
        entry["search_metrics"]["domains"]["geo"]["fixtures"]["geo-a"]["secondary_score"] = secondary_public
    return entry


def _mock_verdict(decision: str, reasoning: str = "mock", confidence: float = 0.9):
    return PromotionVerdict(decision=decision, reasoning=reasoning, confidence=confidence, concerns=[])


def _patch_lineage_and_baseline(lineage_dict, baseline_entry):
    def _fake_lineage(_archive_dir):
        return lineage_dict
    return (
        patch("evolve_ops._load_latest_lineage", side_effect=_fake_lineage),
        patch("evaluate_variant._promotion_baseline", return_value=baseline_entry),
    )


def _run(lineage, baseline, variant_id, tmp_path, *, mock_decision="promote"):
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict(mock_decision),
    ):
        return is_promotable(tmp_path, variant_id, "geo")


def test_promotes_when_judge_says_promote(tmp_path):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="promote") is True


def test_rejects_when_judge_says_reject(tmp_path):
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    assert _run(lineage, baseline, "v007", tmp_path, mock_decision="reject") is False


def test_wrong_lane_short_circuits_judge(tmp_path):
    """Wrong-lane is an invariant guard, not a judgment call — judge never invoked."""
    candidate = dict(_entry("v007", 0.65), lane="core")
    lineage = {"v007": candidate}
    lin_patch, _ = _patch_lineage_and_baseline(lineage, None)
    with lin_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
    ) as mock_judge:
        result = is_promotable(tmp_path, "v007", "geo")
    assert result is False
    mock_judge.assert_not_called()


def test_payload_contains_primary_and_secondary_scores(tmp_path):
    """Verify the judge receives complete cross-family data."""
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("promote"),
    ) as mock_judge:
        is_promotable(tmp_path, "v007", "geo")
    payload = mock_judge.call_args[0][0]
    assert payload["role"] == "promotion"
    assert payload["candidate"]["secondary_public_score"] is not None
    assert payload["baseline"]["secondary_public_score"] is not None
    assert "geo-a" in payload["candidate"]["per_fixture_primary"]
    assert "geo-a" in payload["candidate"]["per_fixture_secondary"]


def test_decision_logged_with_reasoning(tmp_path, monkeypatch):
    """Every judge call is persisted into the unified events log with reasoning trace."""
    events_path = tmp_path / "events.jsonl"
    monkeypatch.setattr("events.EVENTS_LOG", events_path)
    baseline = _entry("v006", 0.60, secondary_public=0.58)
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v006": baseline, "v007": candidate}
    lin_patch, base_patch = _patch_lineage_and_baseline(lineage, baseline)
    with lin_patch, base_patch, patch(
        "autoresearch.judges.promotion_judge.call_promotion_judge",
        return_value=_mock_verdict("reject", reasoning="insufficient holdout signal"),
    ):
        is_promotable(tmp_path, "v007", "geo")
    from events import read_events
    records = read_events(kind="promotion_decision", path=events_path)
    assert len(records) == 1
    assert records[0]["decision"] == "reject"
    assert "insufficient holdout signal" in records[0]["reasoning"]


def test_promotes_first_of_lane_when_judge_approves(tmp_path):
    """No baseline; judge still sees the candidate scores and decides."""
    candidate = _entry("v007", 0.65, secondary_public=0.63)
    lineage = {"v007": candidate}
    assert _run(lineage, baseline=None, variant_id="v007", tmp_path=tmp_path, mock_decision="promote") is True


def test_rejects_first_of_lane_when_judge_rejects(tmp_path):
    """No baseline; judge sees a junk first variant and rejects."""
    candidate = _entry("v007", 0.15, secondary_public=0.13)
    lineage = {"v007": candidate}
    assert _run(lineage, baseline=None, variant_id="v007", tmp_path=tmp_path, mock_decision="reject") is False
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: FAIL — existing `is_promotable` at `evolve_ops.py:241` only checks `eligible_for_promotion`; it doesn't call the promotion-judge.

- [ ] **Step 3: Promotion-judge drives `is_promotable`**

Replace the current threshold-driven `is_promotable` with a thin shim that gathers all measurements (primary scores, secondary scores, per-fixture breakdowns, holdout composites) and delegates the decision to the `promotion-judge` agent (Plan B Phase 0b). No magic numbers; the judge reasons about the full picture.

**Secondary-judge scoring infrastructure (lives on the evolution-judge-service per Plan A Phase 0c):**

Both primary (`codex` CLI → gpt-5.4) and secondary (`claude` CLI → claude-opus-4-7) scoring run on the **evolution-judge-service host**, not on the autoresearch host. `evaluate_search` / `evaluate_holdout` on the autoresearch side POST session artifacts (or artifact references) to the service via `/invoke/score`; the service executes BOTH CLI invocations and returns combined per-fixture + aggregate scores from both judges.

Lineage schema (unchanged — fields are populated from the service response):

- `entry["scores"]` — primary aggregate scores
- `entry["secondary_scores"]` — secondary aggregate scores
- `entry["search_metrics"]["domains"][domain]["fixtures"][fixture_id]["score"]` — primary per-fixture
- `entry["search_metrics"]["domains"][domain]["fixtures"][fixture_id]["secondary_score"]` — secondary per-fixture
- `entry["promotion_summary"]["holdout_composite"]` — primary holdout composite
- `entry["promotion_summary"]["secondary_holdout_composite"]` — secondary holdout composite

`evaluate_variant.py::_score_session` POSTs to `${EVOLUTION_JUDGE_URL}/invoke/score` with `{session_dir_ref, fixture, domain, lane, seeds}` and receives both primary+secondary score sets in one response. No separate `_score_session_secondary` function on the autoresearch side — the judge-service orchestrates both CLI invocations internally (parallelizable up to pool-of-3 per CLI). Extend `_aggregate_suite_results` to preserve both primary and secondary per-fixture scores in the lineage payload.

**Credential isolation:** no provider API keys on the autoresearch host — see Plan A Phase 0c. Autoresearch holds only `EVOLUTION_JUDGE_URL` and `EVOLUTION_INVOKE_TOKEN`.

**`is_promotable` becomes a data-gather + judge-delegate shim:**

```python
# Module-level constants at top of evolve_ops.py:
# Promotion decisions, rollback checks, and other events use the unified
# events log from Phase 0a (`autoresearch/events.py::log_event`).


def _holdout_composite(entry: dict | None, *, key: str = "holdout_composite") -> float | None:
    if not isinstance(entry, dict):
        return None
    summary = entry.get("promotion_summary") or {}
    val = summary.get(key)
    return float(val) if isinstance(val, (int, float)) else None


def _per_fixture_scores(entry: dict | None, *, key: str = "score") -> dict[str, float]:
    """Extract per-fixture scores (primary by key='score', secondary by key='secondary_score')."""
    out: dict[str, float] = {}
    if not isinstance(entry, dict):
        return out
    sm = entry.get("search_metrics") or {}
    for _domain, payload in (sm.get("domains") or {}).items():
        if not isinstance(payload, dict):
            continue
        for fixture_id, record in (payload.get("fixtures") or {}).items():
            if not isinstance(record, dict):
                continue
            score = record.get(key)
            if isinstance(score, (int, float)):
                out[str(fixture_id)] = float(score)
    return out


def is_promotable(archive_dir: str | Path, variant_id: str, lane: str) -> bool:
    """Gather full scoring context, ask promotion-judge whether to promote.

    No hardcoded thresholds. The judge sees candidate + baseline scores from
    both primary and secondary judges (aggregate and per-fixture), holdout
    composites, and the lane's prior promotion history, then returns
    decision ∈ {promote, reject} with reasoning.

    Hard invariant kept programmatic: wrong-lane short-circuit (the judge
    should never be asked to decide about a lane-mismatched variant — that's
    a data bug, not a judgment call).
    """
    import evaluate_variant
    from autoresearch.judges.promotion_judge import call_promotion_judge, JudgeUnreachable
    from autoresearch.events import log_event

    latest = _load_latest_lineage(archive_dir)
    entry = latest.get(variant_id)
    base_record = {"variant_id": variant_id, "lane": lane}

    # Invariant (not judgment): the promotion check should only ever be called
    # for a variant whose lane matches. If not, data bug upstream.
    if str((entry or {}).get("lane") or "").strip().lower() != lane:
        log_event(kind="promotion_decision",
                  **base_record, decision="reject", reason="wrong_lane",
                  source="invariant_guard")
        return False

    archive_root = Path(archive_dir).resolve()
    baseline_entry = evaluate_variant._promotion_baseline(archive_root, variant_id, lane)

    # Re-score baseline on monitoring fixtures (content-drift-contaminated fixtures).
    # The 4 monitoring fixtures use AUTORESEARCH_WEEK_RELATIVE=most_recent_complete
    # and target different content every week. baseline_entry's stored scores were
    # computed on whatever content was current when the baseline was last promoted
    # (possibly weeks ago). Comparing fresh candidate scores against stale baseline
    # scores on these fixtures silently biases the promotion decision toward
    # whichever direction monitoring content shifted. Re-score the baseline on
    # THIS cycle's content so both sides see the same week's world.
    if baseline_entry is not None:
        baseline_entry = evaluate_variant._refresh_monitoring_scores_for_baseline(
            baseline_entry, lane, archive_root,
        )

    # Gather the full measurement stack for the judge.
    payload = {
        "role": "promotion",
        "candidate_id": variant_id, "lane": lane,
        "baseline_id": str(baseline_entry.get("id")) if baseline_entry else None,
        "candidate": {
            "public_score": evaluate_variant._objective_score_from_scores(
                entry.get("scores") if isinstance(entry, dict) else None, lane),
            "holdout_score": _holdout_composite(entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                entry.get("secondary_scores") if isinstance(entry, dict) else None, lane),
            "secondary_holdout_score": _holdout_composite(entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(entry, key="secondary_score"),
            "eligible_for_promotion_flag": bool(((entry or {}).get("promotion_summary") or {}).get("eligible_for_promotion")),
        },
        "baseline": None if baseline_entry is None else {
            "public_score": evaluate_variant._objective_score_from_scores(baseline_entry.get("scores"), lane),
            "holdout_score": _holdout_composite(baseline_entry),
            "secondary_public_score": evaluate_variant._objective_score_from_scores(
                baseline_entry.get("secondary_scores"), lane),
            "secondary_holdout_score": _holdout_composite(baseline_entry, key="secondary_holdout_composite"),
            "per_fixture_primary": _per_fixture_scores(baseline_entry, key="score"),
            "per_fixture_secondary": _per_fixture_scores(baseline_entry, key="secondary_score"),
        },
    }

    try:
        verdict = call_promotion_judge(payload)
    except JudgeUnreachable as exc:
        # judge_unreachable already logged by call_promotion_judge. Treat as reject
        # (don't promote on missing evidence). Matches Plan A Phase 0c stance:
        # no threshold fallback; operator re-runs the cycle once the judge is back.
        log_event(kind="promotion_decision",
                  **base_record, decision="reject", reason="judge_unreachable",
                  error=str(exc)[:200], source="service_outage")
        print(f"is_promotable: {variant_id} REJECT (judge unreachable) — {exc}",
              file=sys.stderr)
        return False

    # Abstain path: agent returned a non-promote/reject decision (e.g. "abstain")
    # OR concerns include a blocking-severity flag. Belt AND suspenders: teach
    # the prompt to return decision="abstain" when confidence is low, AND gate
    # on concerns[*].severity == "blocking" to catch agents that rationalize
    # a confident-looking verdict despite flagging the issue.
    blocking_concerns = [
        c for c in verdict.concerns
        if isinstance(c, dict) and str(c.get("severity", "")).lower() == "blocking"
    ]
    if verdict.decision not in {"promote", "reject"} or blocking_concerns:
        log_event(kind="judge_abstain",
                  **base_record,
                  decision=verdict.decision,
                  reasoning=verdict.reasoning,
                  confidence=verdict.confidence,
                  concerns=verdict.concerns,
                  blocking_concerns=blocking_concerns)
        print(f"is_promotable: {variant_id} ABSTAIN "
              f"(decision={verdict.decision!r}, blocking_concerns={len(blocking_concerns)}) "
              f"— {verdict.reasoning}",
              file=sys.stderr)
        return False  # Reject on abstain — don't promote on incomplete signal.

    decision = verdict.decision == "promote"
    log_event(kind="promotion_decision",
              **base_record,
              decision=verdict.decision,
              reasoning=verdict.reasoning,
              confidence=verdict.confidence,
              concerns=verdict.concerns,
              payload_summary={
                  "cand_public": payload["candidate"]["public_score"],
                  "cand_holdout": payload["candidate"]["holdout_score"],
                  "cand_sec_public": payload["candidate"]["secondary_public_score"],
                  "cand_sec_holdout": payload["candidate"]["secondary_holdout_score"],
                  "base_id": payload["baseline_id"],
              })
    print(
        f"is_promotable: {variant_id} {verdict.decision.upper()} — {verdict.reasoning}",
        file=sys.stderr,
    )
    return decision
```

**Abstain contract (agent-side):** the promotion-judge prompt (on the judge-service, `judges/evolution/prompts/promotion.md`) instructs the agent to return `decision="abstain"` when it cannot reach a confident verdict — weak signal, contradictory evidence, insufficient fixture coverage. `concerns` may carry a list of `{severity: "blocking"|"advisory", description: "..."}` — a `blocking` severity on any concern auto-converts to abstain regardless of decision string. This belt-and-suspenders gate catches agents that rationalize a confident `promote` while also flagging the issue.

**Prerequisite (unchanged):** `evaluate_search` + `evaluate_holdout` must preserve per-fixture scores (primary AND secondary) in the lineage entry at `search_metrics.domains.<domain>.fixtures.<fixture_id>.{score,secondary_score}`. If the current aggregation step discards them, extend `_aggregate_suite_results` to keep them. Add a test `test_lineage_preserves_per_fixture_scores` asserting the shape is present after finalize.

**Audit log** — promotion decisions land in the unified events log via `log_event(kind="promotion_decision", ...)`. Query via `jq 'select(.kind=="promotion_decision")' ~/.local/share/gofreddy/events.jsonl`. Each record carries `{timestamp, kind, variant_id, lane, decision, reasoning, confidence, concerns, payload_summary}`. Spot-check weekly for reasoning quality / drift.

- [ ] **Step 4: Verify tests pass**

Run: `pytest tests/autoresearch/test_promotion_rule.py -v`
Expected: all 7 PASS.

Run: `pytest tests/autoresearch/ tests/freddy/ -x -q`
Expected: full suite still passes. In particular, `finalize_candidate_ids` and `write_finalized_shortlist` (which call `_promotion_baseline` directly) remain unchanged; the only new caller is `is_promotable`.

- [ ] **Step 5: Manual verification on geo lane**

`evolve.sh finalize` is deprecated (removed per `autoresearch/evolve.py:95-100`; finalize now runs automatically at the end of each `evolve.sh run` cycle when holdout is configured). Trigger it by running one iteration:

```bash
./autoresearch/evolve.sh run --iterations 1 --candidates-per-iteration 1 --lane geo
```

Expected: command completes without error. Either promotes the new candidate (per the promotion agent's verdict) or reports no promotion (with the agent's reasoning logged to `events.jsonl`).

Spot-check the output manually: is the promotion decision defensible given the scores? If yes, ship. If no, investigate before enabling on other lanes.

- [ ] **Step 6: Record head-score events + wire the rollback_agent**

> **⚠️ MVP CARVE-OUT (2026-04-23): DEFERRED to [`docs/plans/2026-04-23-003-automated-rollback.md`](2026-04-23-003-automated-rollback.md).** The plan admits the rollback prompt is untuned against real data at MVP and ships write-access-off until 2026-05-15. Calendar-gated write access is not an audit-gated safety rail. Chain-of-failure analysis (see review Chain 1: judge-unreachable + cooldown counted in post-promotion events = rollback silently disabled during outages) confirms this is not ready to ship. **Skip this step entirely.** Retain Steps 1-5 (`is_promotable`, wrong-lane invariant, promotion-judge wiring, secondary-scoring sanity). Start the follow-up plan once 1-2 real post-promotion regressions have been observed and manually handled via `evolve.sh promote --undo --lane <lane>`; the observed trajectories are then the tuning data the rollback agent prompt needs.

Autonomous promotion without rollback can compound bad promotions. Full rollback ships here — agent-driven trajectory analysis + `evolve.sh promote --undo` wiring + cooldown + dry-run-mode + first-week audit behavior. No hardcoded regression threshold; the `rollback_agent` role on the evolution-judge-service decides whether the current lane head's post-promotion trajectory warrants reverting. Caveat: the rollback prompt is not tuned against observed bad-promotion data at MVP; expect to refine the prompt after the first 1-2 observed rollbacks (PR-gated judge-service deploy).

Add to `autoresearch/evolve_ops.py`:

```python
from autoresearch.events import log_event, read_events
from autoresearch.judges.promotion_judge import (
    call_promotion_judge, JudgeUnreachable,
)

ROLLBACK_COOLDOWN_CYCLES = 3  # invariant, not judgment: prevent rollback thrash
                              # by requiring ≥3 post-promotion cycles between
                              # two consecutive rollback actions on the same lane.
ROLLBACK_DRY_RUN_UNTIL_ISO = "2026-05-15T00:00:00Z"  # first-week observation mode:
                              # before this date, rollback decisions are LOGGED
                              # but the --undo command is NOT executed. Gives
                              # the operator a dry-run window to audit the
                              # rollback_agent's judgment against real trajectories
                              # before the agent gets write access.


def record_head_score(
    *, lane: str, head_id: str, public_score: float,
    holdout_score: float | None, promoted_at: str,
) -> None:
    """Emit kind="head_score" after each promotion — feeds the rollback agent."""
    log_event(kind="head_score",
              lane=lane, head_id=str(head_id), promoted_at=promoted_at,
              public_score=float(public_score),
              holdout_score=float(holdout_score) if holdout_score is not None else None)


def check_and_rollback_regressions(archive_dir: str | Path, lane: str) -> bool:
    """Ask rollback_agent whether to revert the current lane head. Agent reads
    raw pre+post trajectory from the unified events log. No delta threshold,
    no window count — agent decides.

    Invariants (not judgment):
    - wrong-lane short-circuit: only check the requested lane
    - cooldown: ≥ROLLBACK_COOLDOWN_CYCLES post-promotion samples since the last rollback
    - need prior head + ≥2 post-promotion samples on the current head
    """
    import datetime as _dt
    from autoresearch.events import log_event

    records = [r for r in read_events(kind="head_score") if r.get("lane") == lane]
    if not records:
        return False
    current_head = records[-1]["head_id"]
    post = [r for r in records if r["head_id"] == current_head]
    pre = [r for r in records if r["head_id"] != current_head]
    if not pre or len(post) < 2:
        return False

    # Cooldown: last rollback on this lane emitted kind="regression_check"
    # with decision="rollback"; require ≥ROLLBACK_COOLDOWN_CYCLES head_score
    # entries since.
    prior_rollbacks = [
        r for r in read_events(kind="regression_check")
        if r.get("lane") == lane and r.get("decision") == "rollback"
    ]
    if prior_rollbacks:
        last_rollback_ts = prior_rollbacks[-1].get("timestamp", "")
        post_since_rollback = [
            r for r in records if r.get("timestamp", "") > last_rollback_ts
        ]
        if len(post_since_rollback) < ROLLBACK_COOLDOWN_CYCLES:
            return False  # cooldown active

    # Ask the agent.
    try:
        verdict = call_promotion_judge({
            "role": "rollback", "lane": lane,
            "current_head": current_head,
            "prior_head": pre[-1]["head_id"],
            "post_promotion_trajectory": post,
            "pre_promotion_trajectory": pre[-5:],
        })
    except JudgeUnreachable as exc:
        log_event(kind="regression_check",
                  lane=lane, current_head=current_head,
                  decision="skip", reason="judge_unreachable",
                  error=str(exc)[:200])
        return False

    log_event(kind="regression_check",
              lane=lane, current_head=current_head,
              prior_head=pre[-1]["head_id"],
              decision=verdict.decision, reasoning=verdict.reasoning,
              confidence=verdict.confidence, concerns=verdict.concerns)

    if verdict.decision != "rollback":
        return False

    # Dry-run window: log the decision but do NOT execute the --undo.
    now_iso = _dt.datetime.utcnow().isoformat() + "Z"
    if now_iso < ROLLBACK_DRY_RUN_UNTIL_ISO:
        log_event(kind="regression_check",
                  lane=lane, current_head=current_head,
                  decision="rollback_dry_run",
                  reasoning=f"would rollback but in dry-run window (until {ROLLBACK_DRY_RUN_UNTIL_ISO})",
                  original_agent_reasoning=verdict.reasoning)
        print(f"⚠️  AUTO-ROLLBACK (DRY-RUN): would revert {current_head} → "
              f"{pre[-1]['head_id']}: {verdict.reasoning}", file=sys.stderr)
        return False

    # Live rollback.
    print(f"⚠️  AUTO-ROLLBACK: {current_head} → {pre[-1]['head_id']}: {verdict.reasoning}",
          file=sys.stderr)
    subprocess.run(["./autoresearch/evolve.sh", "promote", "--undo", "--lane", lane],
                   check=True)
    return True
```

**Wiring** in `autoresearch/evolve.py`, at the end of each run iteration, post-finalize:

```python
# After the existing finalize logic has decided on a new head and recorded it:
if newly_promoted_head_id is not None:
    record_head_score(
        lane=lane,
        head_id=newly_promoted_head_id,
        public_score=float(promotion_payload["candidate"]["public_score"]),
        holdout_score=promotion_payload["candidate"].get("holdout_score"),
        promoted_at=datetime.now(timezone.utc).isoformat(),
    )
check_and_rollback_regressions(archive_dir, lane)  # always runs; no-ops when
                                                    # insufficient data or
                                                    # cooldown active.
```

Tests `tests/autoresearch/test_regression_rollback.py` (seed `events.jsonl` inline via `tmp_path`, patch `call_promotion_judge` + `subprocess.run`):

```python
def test_no_rollback_when_no_events(tmp_path, monkeypatch): ...
def test_no_rollback_when_only_one_prior_entry(tmp_path, monkeypatch): ...
def test_rollback_when_agent_says_rollback_post_dry_run_window(tmp_path, monkeypatch):
    # Patch ROLLBACK_DRY_RUN_UNTIL_ISO to a past date; expect subprocess.run called.
    ...
def test_dry_run_logs_but_does_not_execute(tmp_path, monkeypatch):
    # Default ROLLBACK_DRY_RUN_UNTIL_ISO is future; expect subprocess NOT called
    # and kind="regression_check" with decision="rollback_dry_run".
    ...
def test_no_rollback_when_agent_says_hold(tmp_path, monkeypatch): ...
def test_cooldown_prevents_consecutive_rollbacks(tmp_path, monkeypatch):
    # Seed a prior kind="regression_check" decision=rollback; only 1 post-rollback
    # head_score entry; expect no new rollback.
    ...
def test_judge_unreachable_skips_rollback(tmp_path, monkeypatch): ...
def test_agent_receives_full_pre_and_post_trajectory(tmp_path, monkeypatch): ...
```

- [ ] **Step 7: Document new rule + audit log**

Update `autoresearch/README.md` "Evolution Loop" section:
- Document the agent-driven promotion rule: `is_promotable` gathers primary + secondary judge scores across all fixtures + holdout composites and delegates the promote/reject decision to the promotion agent. One programmatic invariant (wrong-lane short-circuit). `verdict="abstain"` or any `concerns[].severity == "blocking"` logs `kind="judge_abstain"` and treats as reject.
- Document auto-rollback: after each promotion, `check_and_rollback_regressions` asks the `rollback_agent` whether the current head's post-promotion trajectory warrants reverting. No hardcoded delta threshold. Cooldown invariant: ≥3 post-promotion cycles between two consecutive rollbacks on the same lane. Dry-run window: rollback decisions before `ROLLBACK_DRY_RUN_UNTIL_ISO` are logged as `rollback_dry_run` but NOT executed — operator audits the agent's judgment before it gets write access. After the window closes, rollbacks run live.
- Document the unified events log at `~/.local/share/gofreddy/events.jsonl` (kinds: `promotion_decision`, `regression_check`, `head_score`, `judge_abstain`, `judge_unreachable`, `saturation_cycle`, `judge_drift`, `content_drift`). Provide sample `jq` queries: `jq 'select(.kind=="promotion_decision")' events.jsonl` and `jq 'select(.kind=="regression_check" and .decision=="rollback")' events.jsonl`.
- Note that MAD confidence scoring and IRT dashboard are separate initiatives (not part of this plan).

- [ ] **Step 8: Commit**

```bash
git add autoresearch/evolve_ops.py autoresearch/evolve.py autoresearch/README.md \
        tests/autoresearch/test_promotion_rule.py \
        tests/autoresearch/test_regression_rollback.py
git commit -m "feat(evolve): agent-driven promotion + auto-rollback (cooldown + dry-run window)"
```

---


## Acceptance Criteria (done = all hold)

- `docs/plans/fixture-taxonomy-matrix.md` (in-repo) contains search-v1 only (~30 entries); `~/.config/gofreddy/holdouts/holdout-v1-taxonomy.md` (out-of-repo, 600) contains the 16 holdout entries.
- `~/.config/gofreddy/holdouts/holdout-v1.json` exists with 16 fixtures, permissions `600`
- `autoresearch/eval_suites/holdout-v1.json.example` exists in-repo, redacted, carries `"is_redacted_example": true` at the top level
- `autoresearch/eval_suites/search-v1.json` bumped to version `1.1` with 6-8 new fixtures
- `freddy fixture staleness --pool holdout-v1` shows all 16 as `fresh`
- `freddy fixture staleness --pool search-v1` shows all ~30 as `fresh`
- `docs/plans/search-v1-migration-scores.md` has baseline dry-run scores for every search-v1 fixture
- `docs/plans/overfit-canary-results.md` exists with pre-canary sanity result + 20-iteration checkpoints (5 seeds each) + pattern-based verdict
- If GO: one iteration of `./autoresearch/evolve.sh run --lane geo --iterations 1 --candidates-per-iteration 1` invokes the agent-delegated promotion gate (with the wrong-lane invariant short-circuit); `is_promotable` unit tests pass
- If NO-GO after one revision cycle: plan pauses at Phase 5 per the termination rule in Step 6; next step is the separate MAD-confidence-scoring initiative, NOT a third holdout revision
- No in-repo file (TAXONOMY.md, fixture-taxonomy-matrix.md, lineage artifacts committed to git) names any holdout fixture_id

**Production hardening:**

- Holdout refresh runs on process-boundary-isolated infrastructure: `.github/workflows/holdout-refresh.yml` exists and succeeds on `workflow_dispatch`; cache artifacts reach the evolution machine via `gh run download`. Evolution runs do NOT have access to holdout credentials (verifiable: `env | grep -i holdout` during `./autoresearch/evolve.sh run` returns nothing). Refresh commands declare isolation mode via `--isolation {ci|local}`; the `local` mode is a documented shortcut for dev sessions and requires an explicit commit-message call-out on production runs. The pre-commit hook `scripts/pre-commit-holdout-guard.sh` refuses any commit containing `HOLDOUT_*_API_KEY` strings outside the workflow file.
- Post-finalize emits `log_event(kind="saturation_cycle", fixture_id=..., candidate_score=..., baseline_score=..., baseline_beat=...)` per public fixture into the unified `events.jsonl` (no standalone `saturation_log.py` module, no aggregator); `freddy fixture staleness` batches the per-fixture cycle events to the `system_health.saturation` agent and tags fixtures the agent returns as `rotate_now`. No hardcoded beat-rate threshold.
- `autoresearch/judge_calibration.py` exists; PR-gated baseline is deployed on the judge-service side; `--check` returns 0 on a `stable` verdict and 1 on any drift verdict (`magnitude_drift` / `variance_drift` / `reasoning_drift` / `mixed`) produced by the cross-family calibration agent. No 2×MAD threshold in code.
- `events.jsonl` records every `is_promotable` decision as `kind="promotion_decision"` and every rollback check as `kind="regression_check"`
- `check_and_rollback_regressions` runs after each `evolve.sh run` finalize; auto-rollback test suite passes
- Anchor fixtures' refresh flow stores `content_sha1`; quality-judge verdict of `material` writes `kind="content_drift"` to events.jsonl and stderr

---

## Execution Options

Prerequisite and phase sequencing are in the top-of-doc header. Recommended hybrid: subagent-driven for Phases 2–3 (fixture authoring benefits from per-phase review); inline for Phases 1/4/5/6.

**After Plan B lands:** the separate initiatives covering MAD confidence scoring, `lane_checks.sh` correctness gates, lane scheduling rework, and the IRT benchmark-health dashboard can proceed. None is required for the agent-delegated promotion rule this plan ships.
