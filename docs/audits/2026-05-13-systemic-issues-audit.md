# Autoresearch Systemic Issues Audit — 2026-05-13

Three parallel investigations, triggered by the Phase 3 post-mortem (5 of 7 lanes died from a single rate-limit cascade; geo's only successful child v196 was capped because the meta-agent never saw per-criterion judge feedback).

The same shape of issue — **agent-X has insufficient information to act well**, **retry policy can't survive an upstream window**, **single provider with no fallback** — appears in many places beyond what we just fixed. This document catalogues them with severity + fix effort so we can sequence the work.

## Executive summary

| Theme | Total findings | HIGH severity | Already fixed |
|---|---|---|---|
| Information gaps to agents | 10 | 4 | 1 (per-criterion → meta) |
| Retry / rate-limit fragility | 11 | 4 | 1 (`_post_with_retry` + `agent_retry`) |
| Single-data-provider failure modes | 10 | 4 | 0 |

**Cumulative fix effort for ALL highs: ~600 LOC across ~15 files** — meaningful but tractable. Sequencing matters: Theme-2 (rate-limit) fixes need to land first because they protect the whole evolution loop while we work the slower problems.

---

## Theme 1 — Information gaps to agents

The pattern: an agent makes decisions without context that already exists on disk or in another component. The just-fixed example: meta-agent only saw composite scores in `eval_digest.md` even though per-criterion judge feedback sat in `<variant>/sessions/<lane>/<client>/.last_eval_cache.json`.

| Severity | Agent | Missing context | Where it lives on disk | Fix LOC |
|---|---|---|---|---|
| ✅ FIXED | Meta-agent | Per-criterion judge failures | `.last_eval_cache.json` per fixture | ~30 |
| **HIGH** | Outer judge (`variant_scorer.score_variant`) | **Parent variant's deliverable** for the same fixture | `<archive_dir>/<parent_id>/sessions/<lane>/<fixture>/` | ~80 |
| **HIGH** | Render judge (`scripts/render_judge.py`) | **Source markdown** that the screenshot was rendered from | Sibling files of screenshot | ~40 |
| **HIGH** | Meta-agent | **`archived_sessions/`** — prior runs of the SAME fixture (REWORK→KEEP→outer-score lineage per client) | `<variant_dir>/archived_sessions/` (kept 30d) | ~120 |
| **HIGH** | Inner agent | **Critique reasoning text** from prior REWORK loops within the SAME session | `<session_dir>/eval_feedback.json` | ~60 |
| MEDIUM | Meta-agent | Per-fixture cost & wall-time | `scores.json` | ~25 |
| MEDIUM | Outer judge | Session-time judge feedback for the same deliverable (potential double-penalty silently) | `<session_dir>/.last_eval_cache.json` | ~50 |
| MEDIUM | Program-prescription critic | Eval_digest / per-criterion failures of parent variant | `<variant_dir>/eval_digest.md` | ~40 |
| MEDIUM | Session-time critique agent | Prior-run feedback for the same deliverable | `archived_sessions/<ts>-<lane>-<client>/.last_eval_cache.json` | ~70 |
| LOW | Review agent | `competitive_context` placeholder is never wired in production | competitive lane outputs | ~30 |
| LOW | Meta-agent | `critique_manifest.json` integrity status | `<variant_dir>/critique_manifest.json` | ~10 |

### HIGH-severity details

**1.1 Outer judge has no parent deliverable.** `judges/evolution/agents/variant_scorer.py:121-189` builds the prompt from `payload.get("artifacts", {})` only. The judge cannot tell whether a 6.5 score is a regression from 7.8 or improvement from 5.2 — it just emits an absolute number. **This is a structural source of high-variance scoring** (the "Rating Roulette α<0.8" memo). Fix: in `evaluate_variant.py` where the judge payload is built (~lines 2920–2940), resolve parent artifact paths via lineage in `<archive_dir>/index.json`, attach as `<parent_artifacts>` block, instruct the judge prompt to mention 1–2 specific deltas in `notes`.

**1.2 Render judge is content-blind.** `scripts/render_judge.py:55-117` sends only the PNG + rubric to Gemini. A rendered report that silently DROPS a section the source markdown contained scores fine on RND-1..5 (layout/typography/contrast). The bug class "renderer ate my evidence" is invisible. Fix: locate sibling `report.md`, inline a token-budgeted excerpt as a second `Part`, add RND-6 criterion "rendered output preserves all source claims/sections."

**1.3 Meta-agent never sees `archived_sessions/`.** `_collect_meta_template_context` in `evolve.py:1641-1643` only resolves `<parent_id>/sessions/`. But every fixture has rolling history under `archived_sessions/` (kept 30 days per `run.py:303-309`). The meta-agent therefore cannot detect "Shopify monitoring oscillates between 7.5 and 1.4 across last 5 runs — root cause is the data scrape, not the prompt" — exactly the contamination pattern that wasted v183 and v189 cycles. Fix: mirror the `_collect_per_criterion_failures` pattern, summarise per-fixture trajectory (last 5 scores + most recent failure feedback) into a new `## Per-Fixture History` section in `eval_digest.md`.

**1.4 Inner agent never sees its own critique reasoning.** `archive/v006/scripts/evaluate_session.py:360-371` builds rich per-criterion `feedback` strings, but `run.py` loop uses only the `decision` field to gate REWORK. The agent re-runs the same prompt blind to *why* it failed. **The gradient-feedback gap**. Fix: in `archive/v006/run.py` after REWORK, format failing-criteria `feedback` into `<session_dir>/.last_critique_summary.md` and add an opt-in include block to each `programs/<lane>-session.md` ("Read `.last_critique_summary.md` first before regenerating").

---

## Theme 2 — Retry / rate-limit fragility

The pattern: a transient upstream failure (Claude Max usage cap, codex per-window quota) causes the same collapse fixed in `_post_with_retry`. Fast retry policies (~40s budget) can't outlast a 12+ min Claude reset window.

We just shipped: `evaluate_variant._post_with_retry` (HTTP) + `agent_retry.is_rate_limit_failure`/`rate_limit_backoff_delay` + wired into `evolve.py:_run_meta_agent_once`. **5 OTHER call sites need the same treatment.**

| Severity | File:line | Pattern | Failure mode | Fix complexity |
|---|---|---|---|---|
| ✅ FIXED | `evaluate_variant._post_with_retry` | HTTP judge call | (was) lane-killer | shipped |
| ✅ FIXED | `evolve.py:_run_meta_agent_once` | Meta-agent subprocess | (was) lane-killer | shipped |
| **HIGH** | `autoresearch/harness/agent.py:166-206` | Fixture session spawn (claude/codex/opencode) | Claude-Max cap mid-fixture exhausts 3 attempts → fixture crashes → variant scoring corrupted | TRIVIAL ~10 LOC |
| **HIGH** | `autoresearch/program_prescription_critic.py:386-430` | Critic subprocess fires every variant | Rate-limit during evolution sweeps kills critic → variant rejected (`verdict=error`), wasted generation | TRIVIAL ~10 LOC |
| **HIGH** | `autoresearch/judges/promotion_judge.py:50-79` | **Single httpx.post, ZERO retries** | Any 502/timeout from judge service aborts the whole evolution generation | MODERATE ~30 LOC |
| **HIGH** | `autoresearch/judges/quality_judge.py:42-60` | **Single httpx.post, ZERO retries** | Saturation/drift/calibration verdicts fail mid-run; spurious lane halt | MODERATE ~30 LOC |
| MEDIUM | `judges/invoke_cli.py:253-272` | OpenCode CLI 3-attempt loop, no rate-limit promotion | Judge-service-side opencode call burns 3 attempts in <1min; raises RuntimeError → 500 | TRIVIAL ~10 LOC |
| MEDIUM | `src/evaluation/judges/openai.py:91-170` | 3-attempt expon. backoff (~7s max) | OpenAI org-level RPM limit → 3 fast retries fail → returns degenerate `raw_score=0` silently → calibration contaminated | MODERATE ~30 LOC |
| MEDIUM | `src/evaluation/judges/claude.py:97-137` | Same shape as OpenAI | Silent `raw_score=0` "Judge failed" result; same calibration contamination | MODERATE ~30 LOC |
| MEDIUM | `autoresearch/compute_metrics.py:336-355` | Alert-agent retry only when backend==opencode | If `AUTORESEARCH_ALERT_BACKEND=claude` and Max cap hits → silent metrics gap | TRIVIAL ~10 LOC |
| LOW | `cli/freddy/commands/evaluate.py:63,191` | Single httpx.post, no retry | Operator-facing only; per-fixture loss when invoked manually | skip |

### Suggested PR sequencing

**PR-A (~40 LOC):** wire `agent_retry.is_rate_limit_failure` + long-backoff into `harness/agent.py`, `program_prescription_critic.py`, `compute_metrics.py`, `judges/invoke_cli.py`. All four already import from `agent_retry`; just add the promotion block.

**PR-B (~60 LOC):** extract `_post_with_judge_retry(endpoint, payload, *, role)` helper, apply to `quality_judge.py` and `promotion_judge.py`. Mirror the `_JUDGE_RETRY_*` / `_JUDGE_RATE_LIMIT_*` env knobs from `evaluate_variant.py`.

**PR-C (~60 LOC):** tighten `src/evaluation/judges/{claude,openai}.py` to use `is_rate_limit_failure` long-backoff + use `is_transient_claude_failure` (already excludes "not logged in" terminal errors).

### Opposite problem (fail-fast where retry is happening)

- `agent_retry.is_terminal_codex_failure` covers cybersecurity-filter content moderation — good.
- **Gap:** `src/evaluation/judges/claude.py:113-119` treats every `SonnetAgentError` and bare `Exception` as transient — burns 3 attempts × 30s = 90s on auth bugs.
- `judges/invoke_cli.py:261` raises on non-zero exit but does NOT distinguish terminal codex failures (cybersecurity filter). Worth wiring `is_terminal_codex_failure` here too.

---

## Theme 3 — Single-data-provider failure modes

The pattern (user-flagged): when the inner agent's primary data fetch fails, it has NO alternative provider. It either crashes the session or fabricates content (the **GEO-2 root cause**: agent invents stats when no provider gives it real ones; judge punishes ungrounded claims; score capped).

| Severity | Lane | Data need | Current provider | Failure mode | Suggested fallback |
|---|---|---|---|---|---|
| **HIGH** | geo | Page HTML | `httpx` only via `src/geo/scraper.py` (`js_rendered=False` hardcoded) | 404/paywall/SPA → `success=False`; agent fabricates page facts → GEO-2 = 0 | Wire `src/audit/tools/rendered_fetcher.py` (Playwright already exists) as Tier-2; on still-empty → web.archive.org Wayback |
| **HIGH** | geo | Brand stats / market data (the v196 GEO-2 root cause) | **None** — no semrush/similarweb/ahrefs wired into geo session | Agent invents stats ("65% SOV across 20 keywords") → judge punishes ungrounded claims | Add `freddy stats <brand>` calling `src/audit/tools/apify_similarweb.py` (already exists, only audit lane uses it); update `geo-session.md:113` |
| **HIGH** | geo / competitive | Web search SERPs | None directly exposed; only Cloro AI engines + `freddy scrape` | When neither URL nor AI engine has the data, agent has no SERP path | Expose `src/audit/tools/brave_search.py` as `freddy search-web <q>`; add Google CSE as 2nd tier (~80 LOC new module) |
| **HIGH** | monitoring | Mention search across the web | `src/search/ic_backend.py` only (Insanity Collective single backend) | IC 5xx / circuit-open → `ICUnavailableError`, lane produces empty digest → MON judges score near-zero | Add Brave Search news + Reddit JSON API; tag `source` field so judges see provenance |
| MED | geo | AI engine citation analysis | Cloro multi-platform (already good fan-out internally) | If Cloro itself is down/credit-exhausted, no alternative gateway | Add direct provider clients (perplexity sonar, openai web-tool) as raw-API fallbacks behind same `QueryResult` shape |
| MED | competitive | Competitor page scrape | Same single-shot `freddy scrape` as geo | Bot-block / JS-only → session prompt L100 acknowledges absence but offers no recovery | Same Playwright + Wayback ladder; OR pivot to `freddy visibility`/`freddy search-ads` |
| MED | competitive | Ad intelligence | Foreplay + Adyntel via `src/competitive/service.py` (TWO providers, gracefully degrades) | Only fails when BOTH down | **Already good — keep** |
| MED | storyboard | Creator video catalog | Per-platform fetcher (YouTube/TikTok/Instagram) | If creator's primary platform missing → 404 → no patterns → near-zero SB-1/SB-7 | Cross-platform fallback: try alternates, tag derived patterns as cross-platform |
| LOW | marketing_audit | Search SERPs | `BraveSearchClient` returns `degraded=True` on every failure (partial signal preserved) | Real signal degraded silently when key missing | Already gracefully degraded; consider Google CSE as 2nd source |
| LOW | All | Cached fixture data | `try_read_cache` short-circuits before API call | Stale cache served if shape mismatch — caller can detect | **Working as intended** |

### HIGH-severity fix sketches

**3.1 geo scrape ladder.** `src/geo/scraper.py:43` calls `fetch_page_for_audit` once; on `success=False` the caller returns the error to the agent and the agent moves on. Fix: in `scrape_page`, on error or `word_count < 100`, escalate to `RenderedFetcher` from `src/audit/tools/rendered_fetcher.py:104` (already Playwright + network-idle, used today by audit lane only). On still-empty, attempt `https://web.archive.org/web/2025*/{url}` via `httpx` (~30 LOC new module). Return a `tier` field (`http`|`playwright`|`wayback`) so judges see provenance. Update `programs/geo-session.md:107` to document the tiering.

**3.2 geo factual-grounding providers (v196 GEO-2 root cause).** The geo session prompt advertises only sitemap/scrape/detect/visibility — none expose external brand stats. The agent therefore fabricates ("Semrush dominates pricing queries with 65% SOV"). `src/audit/tools/apify_similarweb.py` and `src/audit/tools/martech.py` exist but are gated behind `cli/freddy/commands/audit.py` only. Fix: add a thin `freddy stats <brand>` Typer command that calls `apify_similarweb.fetch_overview`, returns `{traffic_estimate, top_keywords, geos, source: "similarweb"}`. Add to geo-session.md "Tools Available" table and amend "Data Grounding" L166–171 to require: **"Any numeric claim about traffic/keywords/SOV must cite a `freddy stats` or `freddy visibility` JSON file in `pages/`. Unsourced numbers fail GEO-2."** This converts a hallucination problem into a missing-data problem (preferable — judges can detect the latter).

**3.3 monitoring SERP fallback.** `src/search/ic_backend.py:381` raises `ICUnavailableError` on 401/403/circuit-open with no alternative; `src/api/routers/monitoring.py` propagates as 5xx. The inner agent's `freddy monitor mentions` then returns empty and the agent submits a 1-sentence digest → MON-9 score collapse. Fix: introduce `src/search/aggregator.py` that fans out to `ic_backend` + Brave news + Reddit JSON; merge by URL dedup, tag `source`.

**3.4 Inner-loop verification gap.** No lane re-fetches its own evidence URLs to verify claims. Cheapest fix: add `freddy verify <claim_file>` that re-fetches every URL cited in `findings.md` and flags claims whose substring no longer appears in the rendered page. Drop into all four session prompts as a pre-`COMPLETE` checklist item. ~150 LOC; reuses existing `scraper.py` + new ladder above.

---

## Cross-cutting prioritization

If we can only ship ONE PR this week, do **PR-A from Theme 2** (rate-limit awareness in 4 already-importing-agent_retry sites, ~40 LOC, trivial). It protects every future evolution run from the failure mode that just killed Phase 3. Without this, every theme-1 / theme-3 fix sits behind "but the run will still die mid-way."

If we can ship TWO PRs:

1. **PR-A** (rate-limit ~40 LOC) — protect the loop
2. **PR-G** = Theme-1 finding 1.4 (inner-agent gradient feedback ~60 LOC) — biggest single quality lift per LOC; closes the "REWORK without knowing why" loop

If we can ship THREE PRs:

3. **PR-S** = Theme-3 finding 3.2 (`freddy stats <brand>` ~80 LOC + geo-session.md update) — closes the GEO-2 hallucination ceiling; converts undefined-behavior into measurable-missing-data

Everything else can sequence over the following 1-2 weeks without urgency.

## Memory references

- `project-evolution-redesign-plan-2026-05-13.md` — locked Phase 1+2 design
- `project-phase3-resume-state-2026-05-13.md` — what's currently dead and why
- `project-geo-regression-root-cause-2026-05-12.md` — codex cyber-filter on geo (now mitigated by lane override)
- This file (`docs/audits/2026-05-13-systemic-issues-audit.md`) — the systemic backlog

## Files referenced (all paths absolute from repo root)

Already-fixed retry sites (this session):
- `autoresearch/agent_retry.py`
- `autoresearch/evaluate_variant.py:1041-1162` (`_post_with_retry`)
- `autoresearch/evolve.py:1404-1490` (`_run_meta_agent_once`)

Theme 1 — information gaps:
- `autoresearch/evolve.py:1631-1691` (meta-agent context build)
- `autoresearch/archive/v006/meta.md` (meta-agent prompt template)
- `judges/evolution/agents/variant_scorer.py:121-189` (outer judge payload)
- `scripts/render_judge.py:55-117` (vision sub-judge)
- `autoresearch/archive/v006/run.py` + `archive/v006/scripts/evaluate_session.py:360-371` (inner-loop REWORK gradient gap)
- `autoresearch/program_prescription_critic.py:91-124`
- `judges/session/agents/{critique,review}_agent.py`

Theme 2 — retry fragility:
- `autoresearch/harness/agent.py:166-206`
- `autoresearch/program_prescription_critic.py:386-430`
- `autoresearch/judges/{promotion,quality}_judge.py`
- `judges/invoke_cli.py:253-272`
- `src/evaluation/judges/{claude,openai}.py`
- `autoresearch/compute_metrics.py:336-355`

Theme 3 — single-provider:
- `src/geo/scraper.py:43`, `src/geo/fetcher.py:172`
- `src/audit/tools/rendered_fetcher.py:104` (Playwright, already exists)
- `src/audit/tools/apify_similarweb.py` (already exists, audit-lane-only today)
- `src/audit/tools/brave_search.py` (already exists, marketing-audit-only today)
- `src/search/ic_backend.py:381`
- `src/api/routers/monitoring.py`
- `programs/geo-session.md:107,113,166-171` (would need to update + propagate to head variants)
