# Marketing Audit v1 — Human Prerequisites

**Companion to** `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md`.

**Purpose:** the master plan is implemented by a coding agent in a single continuous run. This doc lists the work that genuinely requires JR (human) input — credentials, commercial outreach, review gates, account access — and cannot be done by the coding agent alone.

**Status:** Active 2026-05-06.

---

## 1. Vendor credentials + account access

Provide these via `.env` before kicking off the agent build. The agent CAN write integration code without keys, but cannot create accounts or sign contracts. Items marked **NEW** are not currently wired and need account creation:

| Item | What to provide | Notes |
|---|---|---|
| DataForSEO | `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD` | Already wired (`src/seo/providers/dataforseo.py`) |
| Cloro | API key in `CLORO_API_KEY` | Already wired (`src/geo/providers/cloro.py`); $0.0012–0.0028/query |
| Foreplay | API key + active subscription | Already wired; $49–99/mo |
| Adyntel | API key in `ADYNTEL_API_KEY` | Already wired; $0.006–0.009/page |
| GSC service account | OAuth credentials | Conditional — only when `--attach-gsc` is used |
| GitHub | `GITHUB_TOKEN` (PAT) | Free; 5K req/hr |
| Wikimedia / Lift Wing | optional `WIKIMEDIA_API_KEY` | Free |
| Product Hunt | OAuth client-credentials | Free with confirmation from `hello@producthunt.com` for commercial use |
| Reddit OAuth | `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | Free; one-time ~30min OAuth app setup |
| HuggingFace | optional `HUGGINGFACE_TOKEN` | Free |
| Mailinator | optional `MAILINATOR_API_TOKEN` | Free public / $99/mo private |
| **NEW: Apify** | API key (`APIFY_TOKEN`) | Pay-per-call (~$1-5/audit for SimilarWeb scraper); no contract. Replaces dropped SimilarWeb enterprise subscription per 2026-05-06 vendor swap. Apify substrate already used by 5 monitoring adapters in repo |
| **NEW: Brave Search** | API key (free tier 2K/mo) | Free; just sign up for an API key |
| **NEW: SerpAPI** | API key | Pay-per-call; live fallback for Adyntel |
| Stripe | Secret key + webhook signing secret | Create webhook endpoint in Stripe dashboard pointing to `gofreddy.ai/api/stripe-webhook` |
| Email service | Resend / Postmark / SES API key | Pick one + set `EMAIL_PROVIDER` env var |
| Slack | `SLACK_WEBHOOK_LEADS` + `SLACK_WEBHOOK_PAID` URLs | Slack workspace → Incoming Webhooks; create 2 channels (`#gofreddy-leads`, `#gofreddy-paid`) |
| Fireflies | Webhook signing secret + 2 webhook endpoints | Fireflies workspace API; sales-call + walkthrough-call separate endpoints |
| Cloudflare account | Account access + DNS for `reports.gofreddy.ai` | Bind custom domain to Pages + Worker routes; agent writes wrangler.toml but cannot configure DNS |
| Fly.io | Already exists per `fly.toml` (app: `gofreddy-api`) | No action |

**Action timing:** all 3 NEW items are pay-per-call API-key signups (Apify + Brave + SerpAPI) — no contracts, no procurement. Sign up + drop keys in `.env` before the agent reaches L2 wiring. **No vendor-quote gate in v1** (SimilarWeb subscription dropped 2026-05-06 in favor of Apify scraper actor — same data customers can self-verify on similarweb.com, ~$1-5/audit pay-per-call, no $24K annual commit).

---

## 2. MA-1..MA-8 rubric review + manifest freeze

The coding agent drafts MA-1..MA-8 rubric prompts + 8 judge prompts as part of the build (per §6.4 working titles). JR review gate fires AFTER agent ships drafts but BEFORE manifest freeze:

1. Read drafts in `programs/marketing_audit/prompts/rubrics/MA-*.md`
2. Read drafts in `programs/marketing_audit/prompts/judges/MA-*-judge.md`
3. Iterate against 1-2 hand-built example `findings.md` files (drafts → corrections → re-drafts)
4. When satisfied, run `python autoresearch/scripts/regen_marketing_audit_manifest.py` to freeze
5. Manifest written to `marketing_audit_manifest.json`; from this point, `custom_validate` rejects any variant that mutates the frozen files

**Why agent can't fully self-author:** rubrics encode JR's editorial judgment about what makes a good marketing-audit deliverable. Agent drafts are starting points, not final authority. v1.5 can refine if first audits expose miscalibration.

---

## 3. Funnel validation (parallel commercial track)

While the coding agent is building, JR runs the commercial validation in parallel:

1. **Pick 1-2 prospects from JR's network** (vertical/segment/geo mix preferred; B2B SaaS + DTC is one good pair)
2. **Hand-build audits** with Claude assist (no pipeline needed yet — audit JR's own thinking + research; this is pre-pipeline)
3. **Charge $1K** (real or friends-and-family rate; what matters is whether the deliverable feels like $1K of value)
4. **Walkthrough call** — present findings, pitch $15K+ engagement
5. **Track at T+60d** — did they convert to a $15K+ engagement?

**Falsification signal:** if 0/2 convert at T+60d, halt + retune the commercial thesis BEFORE the rest of v1 ships. The R10 kill rule (master plan §5.9) is downstream of this; pre-validating saves 12-16 weeks of wasted infrastructure.

**Held-loosely:** this is the highest-EV action available. Don't over-formalize — the goal is signal on "do paying customers convert because of the audit?" not a controlled experiment.

---

## 4. Per-audit ship-gate review (mandatory by design)

For every paid audit, JR reviews `deliverable/report.html` locally + edits as needed BEFORE running `freddy audit publish`. Locked in master plan §3.11 as one of three permanent gates — independent of who built the pipeline.

**Per-audit JR time:** ~10-30 min (intake review + ship-gate edits). At >5 audits/month, this becomes the bandwidth bottleneck (R10 in master plan risk register's minor risks; v2 considers automated quality gates).

---

## 5. Engagement T+60d closure

After each walkthrough call ships, JR runs `freddy audit close-engagement <slug> --converted=Y/N` based on whether the prospect signed for a $15K+ engagement within 60 days. This updates `audits/lineage.jsonl`; next variant scoring picks up the engagement bonus.

**Why agent can't self-close:** engagement conversion requires JR's commercial knowledge (deals signed, money received, contract terms).

---

## 6. Operational unblock — judge services on :7100/:7200

Autoresearch substrate fixes shipped 2026-05-06, but post-fix dry-run is blocked on judge services not running. Before the coding agent's first marketing_audit variant rotation:

1. Start judge services on `:7100` (promotion judge) + `:7200` (quality judge) via `./scripts/run_backend.sh` or equivalent
2. Run autoresearch dry-run to verify post-fix loop economics (no longer burning $240–680/run with 0 promotions)
3. Confirm green before kicking off marketing_audit variant generation

Agent can register the LaneSpec + run live audits without judge services; the operational unblock only gates evolve-loop variant rotation, not the customer-facing pipeline.

---

## 7. Sales operations

| Task | What JR does |
|---|---|
| Sales call | After scan delivery, JR books + runs the call (Fireflies-captured); pitches $1K audit |
| Stripe Checkout link | JR generates link in Stripe dashboard, sends to prospect manually |
| Walkthrough call | After audit ships, JR books + runs the call (Fireflies-captured); pitches $15K+ engagement |
| Engagement close | T+60d signal closure (see §5 above) |

Coding agent can't run sales calls, negotiate engagement contracts, or send invoices.

---

## 8. R10 kill-rule monitoring

If first 10 paid audits don't yield ≥2/10 conversion to $15K+ engagements within 60 days, JR halts new audit ingestion + retunes (master plan §5.9). This is the v1 commercial test — not mitigatable by infrastructure changes. Manual halt: `freddy audit pause-ingestion` (CLI surface ships in agent build) + Slack notification suppression.

---

## What the coding agent does instead (NOT JR's work)

The agent autonomously builds: LaneSpec wiring, agent_models.py additions, all cherry-picks from snapshot tag, preflight runner + 6 stub fills, src/audit/score.py + validate.py, programs/marketing_audit-session.md, structural validators, manifest operator script, LFS rule, all of stages.py + agent_runner.py, all 4 Stage-2 agent prompts, Stage 1b/1c/3/4 prompts, capability_registry.yaml, Stage 5 Jinja2 + WeasyPrint, all rubric YAMLs, MA-1..MA-8 rubric drafts, 8 judge prompt drafts, the Cloudflare Worker + Pages config, Stripe webhook handler, free scan worker, email integration, Slack notifications, Fireflies webhooks, the 7-verb `freddy audit` CLI, Wappalyzer-next port, Playwright RenderedFetcher, cache layer, fetch_api.sh, DataForSEO method extensions, Apify SimilarWeb actor wiring + Brave + SerpAPI + Apify-X-fallback wrappers, all 13 free-API URL-pattern wrappers in agent prompts, cost observability, resume-by-session-id, deterministic HealthScore, events.jsonl sink, first-runnable end-to-end test, all test files.

The agent is the sole implementer. JR's role is the items above + per-audit operations once the pipeline ships.
