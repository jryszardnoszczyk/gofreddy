# Audit findings — adversarial validation results

Three validator agents drilled into the 12 HIGH findings from `2026-05-13-systemic-issues-audit.md` using REAL archive data + actual failure traces. Most "HIGH" claims didn't survive.

## Final ranking (Occam-pruned)

### ✅ TRULY HIGH — ship now

| # | Site | Evidence | Fix |
|---|---|---|---|
| **R1** | `autoresearch/harness/agent.py:166-206` (fixture session spawn) | Phase 3 geo log: 8 rate-limit markers cascading through this loop | ~15 LOC — mirror the `evolve.py:_run_meta_agent_once` promotion pattern |
| **R2** | `autoresearch/program_prescription_critic.py:386-430` (critic subprocess) | Historical evidence (v3-v9); same rate-limit collapse pattern | ~15 LOC — same template |
| **R3** | `autoresearch/compute_metrics.py:336-355` (alert agent) | **Geo log today**: 2 silent metric losses from 429s | ~10 LOC — same template |
| **R4** | Inner agent REWORK blind (`archive/v006/runtime/post_session.py:107-117` + `evaluate_session.py`) | Verified: agent told to read last 10 lines of `results.jsonl` which has only terse `rework_required` reason; `digest_eval.json` has rich per-criterion `feedback` but is NEVER referenced in the program | ~15 LOC — include `failed_criteria` array in the guard's results.jsonl entry |

Total: **~55 LOC across 4 sites**, all with same-day evidence in Phase 3 logs.

### ⚠️ MEDIUM — small prompt nudges (do after R1-R4)

| # | Site | Why downgraded | Fix |
|---|---|---|---|
| **M1** | Meta-agent never sees `archived_sessions/` | v196 winner DID inspect it — path already accessible, agent just needs reminder | ~10 LOC prompt edit in `meta.md` |
| **M2** | GEO-2 hallucination (no brand stats provider) | 75% of GEO-2 failures are knowledge-cutoff facts (acquisition dates, current rates), NOT stats. New tool addresses 5%. | 3-line prompt rule in `geo-session.md`: "never publish uncited numbers/dates" — measure FIRST before wiring `freddy stats` |
| **M3** | Monitoring single-backend | Actual issue: stale fixture cache pool, not backend redundancy. Brave/Reddit fallbacks would degrade signal not improve it | **Ops command**: `freddy fixture refresh monitoring-* --pool search-v1`. Zero code. Measure after. |

### ⚠️ MEDIUM but defer

| # | Site | Reasoning |
|---|---|---|
| **D1** | `judges/promotion_judge.py` ZERO retries | Fires once per generation; failure aborts only that gen; next gen retries naturally. No observed failures in Phase 3. |
| **D2** | `judges/quality_judge.py` ZERO retries | Same reasoning as D1. Advisory verdicts; failure causes "spurious lane halt" only if escalated. |

### ❌ FALSE ALARMS — drop from list

| # | Site | Why false |
|---|---|---|
| **F1** | Outer judge no parent deliverable | `judges/evolution/prompts/scorer.md:43` says "Score only what is in front of you" — judge is DESIGNED absolute. 2-family cross-judge mean (claude+codex via `variant_scorer.py:154-157`) already handles variance. Cohort rotation makes parent-comparison impossible on half the fixtures anyway. |
| **F2** | Render judge content-blind | 12 sampled reports: no observed content drops. Render score is 10% of composite — even if dropped, ~0.5 composite shift max. Theoretical attack vector, not real failure. |
| **F3** | Geo scrape ladder (no Playwright/Wayback) | v196 fixtures: 18/18 page fetches `status=200` with 200-3000+ words. Failures came from agent inventing facts, not from scraper missing content. None of geo's fixture sites (semrush.com, mayoclinic.org, kubernetes.io, etc.) are JS-only SPAs. |
| **F4** | Geo/competitive web SERP search not exposed | `geo-session.md:101-113` exposes `freddy visibility` (Cloro AI engines) + `freddy detect --full` (DataForSEO). DataForSEO IS a SERP backend. Two search paths exist already. |

---

## Recommended PR sequencing (revised)

### PR-A: Rate-limit awareness in 3 sites (~45 LOC)
Sites: `harness/agent.py`, `program_prescription_critic.py`, `compute_metrics.py:336`. All three import `agent_retry` already; mirror `evolve.py:_run_meta_agent_once` promotion block. **Same-day evidence in geo log.**

### PR-B: Inner-agent REWORK feedback (~15 LOC)
Modify `archive/v006/runtime/post_session.py:enforce_completion_guard` to include `failed_criteria` array (lifted from `digest_eval.json`) in the results.jsonl entry. The agent's existing "read last 10 lines of results.jsonl" picks it up automatically — NO prompt change needed.

### PR-C: Two prompt nudges (~13 LOC total)
1. `meta.md`: add "consult `archived_sessions/<lane>/<fixture>/` for last 3 REWORK→KEEP cycles when fixture score is low" (~10 LOC).
2. `geo-session.md` Hard Rules section: "Never publish numeric/dated claims without a traceable source in `pages/*.json`. Unsourced numbers fail GEO-2." (~3 lines).

### Ops, not code
3. Refresh monitoring fixture pool: `freddy fixture refresh monitoring-* --pool search-v1`.

### Future deferrals (after R1-R4 + M1-M3 measured impact)
- D1/D2 retry awareness in `promotion_judge` + `quality_judge` — share helper with `_post_with_retry`
- `freddy stats <brand>` IF M2 measurement shows the remaining 5% stats-shaped failures are still a ceiling

---

## What we learned from validation

1. **Theoretical "attack vectors" ≠ actual blockers.** Three FALSE ALARMS (F1, F2, F3) were defensible-looking but had zero archive evidence. Skepticism saved ~250 LOC of unnecessary work.

2. **The fix is often a prompt change, not a code change.** GEO-2 grounding (M2): 3-line prompt rule beats 80-LOC tool wire. Same for meta-agent archived_sessions hint (M1).

3. **Some "lane killers" are ops issues.** M3 (monitoring) is a stale cache, not architecture.

4. **The audit double-counted.** The "rate-limit + ZERO retries" items in `promotion_judge` / `quality_judge` LOOK scary on paper (zero retries!) but neither fired in Phase 3. Real evidence > pattern recognition.

5. **My own fix was wired** but the validator's grep ran in a stale worktree. Lesson: always verify path-bootstrapping when cross-referencing claims.

## Files referenced

- Confirmed sites: `autoresearch/harness/agent.py:166-206`, `autoresearch/program_prescription_critic.py:386-430`, `autoresearch/compute_metrics.py:336-355`, `autoresearch/archive/v006/runtime/post_session.py:107-117`
- Prompt nudges: `autoresearch/archive/v006/meta.md`, `autoresearch/archive/v006/programs/geo-session.md`
- Disproven via evidence: `judges/evolution/prompts/scorer.md:43`, `autoresearch/archive_geo/v196/sessions/geo/*/pages/*.json`, `autoresearch/archive_geo/v196/programs/geo-session.md:101-113`
- Already-shipped retry template: `autoresearch/agent_retry.py`, `autoresearch/evaluate_variant.py:1041-1183`, `autoresearch/evolve.py:1395-1490`
