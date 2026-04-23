# Plan B MVP — Execution Runbook

Last updated 2026-04-23. Use this when ready to actually run Plan B MVP end-to-end after the code-side work shipped in `feat/fixture-infrastructure`.

## What's already shipped (code-side, on branch `feat/fixture-infrastructure`)

- Plan A infrastructure (full).
- Plan B Phase 0b: `autoresearch/judges/` thin HTTP clients + tests.
- Plan B Phase 6 Steps 1-5: `is_promotable` promotion gate + tests.
- Plan B Phase 0: plumbing smoke-test folded into `tests/autoresearch/test_phase0_plumbing_smoke.py`.
- Plan B Phase 1: taxonomy matrix (`docs/plans/fixture-taxonomy-matrix.md` + `autoresearch/eval_suites/TAXONOMY.md`).
- Plan B Phase 2 MVP: `~/.config/gofreddy/holdouts/holdout-v1.json` with 4 geo fixtures (BMW i4 DE, Nubank BR PIX, Stripe docs Atlas, Rakuten JP travel).
- Plan B Phase 3: `search-v1` → v1.1 with 6 gap-fill fixtures (total 29 across 4 domains).
- Phase 4 / Phase 5 / Phase 6-Step-5 orchestration scripts (below).

All 280 tests green.

## What needs operator action before Plan B MVP is complete

1. **4 monitoring holdout fixtures** — blocked on xpoz monitor UUIDs from your portfolio. Add them to `~/.config/gofreddy/holdouts/holdout-v1.json` under `domains.monitoring`. Template (populate fields):
   ```json
   {
     "fixture_id": "monitoring-holdout-<slug>",
     "client": "<Client>",
     "context": "${AUTORESEARCH_HOLDOUT_MONITORING_<SLUG>_CONTEXT}",
     "version": "1.0",
     "max_iter": 20,
     "timeout": 1200,
     "anchor": true|false,
     "env": {"AUTORESEARCH_WEEK_RELATIVE": "most_recent_complete"}
   }
   ```
   Then export the referenced env var per fixture: `export AUTORESEARCH_HOLDOUT_MONITORING_<SLUG>_CONTEXT=<xpoz-monitor-uuid>`.

2. **Live-stack boot** (fresh shell):
   ```bash
   cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
   git checkout feat/fixture-infrastructure
   source .venv/bin/activate

   # supabase + backend
   supabase start
   nohup uvicorn src.api.main:app --host 127.0.0.1 --port 8000 > /tmp/gofreddy-api.log 2>&1 &

   # judge services
   JUDGE_MODE=session INVOKE_TOKEN=$(cat ~/.config/gofreddy/session-invoke-token) \
     nohup uvicorn judges.server:app --host 127.0.0.1 --port 7100 \
     > ~/.local/share/gofreddy-judges/logs/session.log 2>&1 &
   JUDGE_MODE=evolution INVOKE_TOKEN=$(cat ~/.config/gofreddy/evolution-invoke-token) \
     nohup uvicorn judges.server:app --host 127.0.0.1 --port 7200 \
     > ~/.local/share/gofreddy-judges/logs/evolution.log 2>&1 &
   sleep 2
   curl -sS -o /dev/null -w "s:%{http_code} " http://127.0.0.1:7100/docs
   curl -sS -o /dev/null -w "e:%{http_code}\n" http://127.0.0.1:7200/docs
   # expect: s:200 e:200

   # creds into shell
   source ~/.config/gofreddy/judges.env
   set -a && source .env && set +a
   ```

3. **Deliberately-overfit variant** for Phase 5 canary — Plan B Phase 5 Step 2.6: hand-craft a variant diff against an in-repo baseline that scores ≥0.15 higher on search-v1 than on holdout-v1. Commit as `vNNN_canary_overfit` in `autoresearch/archive/`.

## Execution order

### A. Phase 2 fixture population (if authoring more than the 4 geo fixtures)

For each new holdout fixture, add the entry to the manifest, set any required env vars, then:

```bash
# Dry-run against the new fixture to verify the judge returns verdict=healthy
freddy fixture dry-run <fixture_id> \
  --manifest ~/.config/gofreddy/holdouts/holdout-v1.json \
  --pool holdout-v1 \
  --seeds 3
```

If `verdict != healthy`, halt — either the fixture isn't representative or the judge prompt needs tuning. Plan A Phase 0-A calibration fixtures are what surface this.

### B. Phase 4: migration check

Pins the `core` lane head and confirms the pre-flight scoring doesn't auto-promote. Runs one evolution iteration.

```bash
./autoresearch/scripts/phase4-migration-check.sh
```

Exit 0 = safe to proceed. Exit 1 = head moved + rollback attempted (inspect events.jsonl).

### C. Phase 5: overfit canary

Requires the overfit variant to exist in the archive.

```bash
# ~days of wall-clock. Do not run casually.
./autoresearch/scripts/phase5-canary.sh
```

Produces `/tmp/canary-{public,holdout}-<iter>.jsonl` for all 10 checkpoints.

After the run completes, invoke the canary agent manually to get the GO | FAIL | REVISE verdict:

```python
from autoresearch.judges.promotion_judge import call_promotion_judge
import json, glob

checkpoints = []
for iter_num in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20):
    pub = [json.loads(l) for l in open(f"/tmp/canary-public-{iter_num}.jsonl")]
    hol = [json.loads(l) for l in open(f"/tmp/canary-holdout-{iter_num}.jsonl")]
    # Extract per-seed scores + compute median + IQR (see Plan B Phase 5 Step 5
    # for the full divergence-table shape the agent expects).
    checkpoints.append({"iter": iter_num, "public_seeds": pub, "holdout_seeds": hol})

verdict = call_promotion_judge({
    "role": "canary",
    "mode": "go_fail",
    "lane": "geo",
    "checkpoints": checkpoints,
    "pre_canary_sanity": {"known_pair_delta": 0.12},  # from Step 2.5a
})
print(verdict.decision, verdict.reasoning)
```

Commit the verdict + reasoning + raw checkpoint JSONL to `docs/plans/overfit-canary-results.md`.

### D. Phase 6 Step 5: manual verification on geo lane

With the canary returning `go`, turn on autonomous promotion on a single lane and watch one iteration.

```bash
# Fresh shell, all creds + judges running
./autoresearch/evolve.sh run --iterations 1 --candidates-per-iteration 1 --lane geo
```

Expected output:
- Subprocess completes without error.
- `events.jsonl` gains one `kind="promotion_decision"` record with `reasoning` and `confidence`.
- Either the new candidate promotes (and `autoresearch/archive/current.json.geo` updates) or it's rejected (with the agent's reasoning logged).

Spot-check the decision: is it defensible given the candidate vs baseline scores in the `payload_summary` field of the event? If yes, repeat on other lanes. If no, halt and inspect.

```bash
# Read the latest promotion decision
jq 'select(.kind == "promotion_decision")' ~/.local/share/gofreddy/events.jsonl | tail -1
```

## Fastest live-verification of Plan B MVP (proved working 2026-04-23)

If you want to confirm Plan B's promotion gate actually talks to the running judge services without waiting hours for a full session, this one-liner hits the narrowest live path:

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy
set -a && source ~/.config/gofreddy/judges.env && set +a
set -a && source .env && set +a
source .venv/bin/activate
python3 -c "
import sys; sys.path.insert(0, 'autoresearch')
from autoresearch.evolve_ops import is_promotable
print('is_promotable(v006, competitive) =', is_promotable('autoresearch/archive', 'v006', 'competitive'))
"
```

Expect: the script returns `False` (because the real lineage has no per-fixture detail — the judge correctly reasons "insufficient evidence"). What this proves:
- judges.env exports propagate to the subprocess (via `set -a`)
- The evolution-judge-service on :7200 accepts the bearer token
- `call_promotion_judge` POSTs, receives a verdict, parses it
- `is_promotable` calls `_refresh_monitoring_scores_for_baseline` + `_promotion_baseline` without errors
- `events.jsonl` gains a `kind="promotion_decision"` record with reasoning + confidence + concerns

Inspect the just-written event:
```bash
jq 'select(.kind == "promotion_decision")' ~/.local/share/gofreddy/events.jsonl | tail -1
```

**If this works, Plan B MVP's code-side is live-verified.** The remaining untested path is the full session → scoring → lineage-write cycle (inherited from Plan A infrastructure, not introduced by Plan B).

## Discovered during the 2026-04-23 live-attempt

A live `freddy fixture dry-run geo-semrush-pricing --seeds 1 --baseline v006` was run against the MVP-shipped infrastructure. Findings:

**Plumbing works end-to-end** — `freddy fixture dry-run` → `evaluate_single_fixture` → `_run_fixture_session` → session subprocess spawn → codex `gpt-5.4` orchestration → `results.jsonl` append → events-log emission. The MVP code is wired correctly.

**Session budget required is hours, not minutes.** The dry-run ran for ~15 minutes (the ad-hoc timeout) and completed only iterations 1 and 2 (discover + competitive) out of a full discover → competitive → seo_baseline → optimize(×N pages) → report sequence. A full one-fixture one-seed session requires **30–60 minutes of wall-clock minimum**; a canary (20 iterations × 10 seeds × 2 surfaces × multiple fixtures) runs for **days**. Before running `phase5-canary.sh`, raise any per-session timeout and budget days of wall-clock — this is what Plan B's original "days of wall-clock, not hours" warning was describing.

**`freddy scrape` / `freddy visibility` subprocess `connection_error` is latent.** Inside the spawned session subprocess, `freddy scrape <url>` and `freddy visibility --brand <brand>` returned `{"code":"connection_error"}`. The session has a `curl` fallback path that worked, but this env-propagation issue will bite any fixture that depends on real-freddy-backend calls from inside a session. **Diagnose before canary**: grep the session subprocess for which env vars it inherits vs. which the CLI needs; likely `FREDDY_API_URL` or an auth token is stripped on fork.

**Runaway-process containment works.** Killing the outer `freddy` process cleanly tears down the codex subprocess tree. The `timeout N` wrapper is good hygiene but the N must be generous.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not connect to API server` | Backend not running | Step 2 above (uvicorn) |
| `judge_unreachable` event fires on every variant | Judge service down or token wrong | Re-run judge daemon boot; verify `curl ${EVOLUTION_JUDGE_URL}/docs` returns 200; verify `${EVOLUTION_INVOKE_TOKEN}` matches `~/.config/gofreddy/evolution-invoke-token` |
| Variant subprocess hangs at 0% CPU | External dependency timing out silently | Kill subprocess; inspect `variant_dir/run.py` for external calls; add a timeout in the variant or skip this fixture for now |
| `holdout-v1 cache miss` hard-fail during dry-run | Fixture has never been refreshed + pool policy is `hard_fail` | Run `freddy fixture refresh <fixture_id> --manifest ~/.config/gofreddy/holdouts/holdout-v1.json --pool holdout-v1` (requires operator creds via `--isolation local` OR running through the CI workflow) |
| `fixture refresh` fails on `visibility` / `search-ads` / `search-content` | Known refresh CLI-signature bug | See `docs/plans/2026-04-23-001-fix-refresh-cli-signature-mismatch.md`. MVP 8-fixture set avoids these sources. |

## What happens if the canary returns FAIL or REVISE

Per Plan B termination rule (Phase 5 Step 6): two consecutive `fail` or `revise` → pause Plan B; don't retry. The follow-up is a separate initiative (not a third holdout revision). One `fail` → bump holdout-v1 to v1.1 with revised fixtures, rerun canary.

## What happens if Phase 6 Step 5 shows a defensibly-wrong promotion

1. Roll back immediately: `./autoresearch/evolve.sh promote --undo --lane geo`
2. Inspect `events.jsonl` for the `promotion_decision` payload + reasoning.
3. If the issue is in the agent's reasoning, update the judge-side prompt (`judges/evolution/prompts/promotion.md`) via PR-gated deploy.
4. If the issue is in the scoring data the agent saw, re-check `_promotion_baseline` + `_refresh_monitoring_scores_for_baseline` wiring.
5. Do NOT enable autonomous promotion on other lanes until the root cause is fixed.
