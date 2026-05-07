# Marketing audit v1 — provider connection checklist

Captured 2026-05-07. Companion to the master plan + deployment runbook.
Run `python scripts/audit_provider_check.py --human` to see live status.

This is the gating list for the §7.7 first-runnable acceptance run.
**Phase 1.5** in the master plan (§4.9) covers the full provider build
(~4-5 weeks of work). This doc lists what's needed for a single
end-to-end audit against a test prospect URL.

## Bare-minimum dry run (shape-only)

If you accept "deliverable shape correct, content mostly gap-flagged"
as the first-run bar:

- **Just need an LLM CLI** (`claude`/`codex`/`opencode`) on PATH —
  uses subscription auth, NOT API keys. Verified via
  `python scripts/audit_provider_check.py --human` (LLM CLI row).
- Run with no provider keys → audit completes, gap_report shows lots of
  unanswered lenses, but the 8-stage pipeline + 4 Stage-2 fan-out + 5
  synthesis files + report.html all materialize.

This is the **cheapest** way to validate end-to-end plumbing against a
real prospect URL. ~$200-400 in Opus calls. Most time is spent in
Stage 2 multi-turn agent runs.

## Full-signal dry run (paying-customer-quality bar)

To produce content quality that's editable to client-quality at the
ship gate (master plan §7.7), provision these in priority order:

### P0 — REQUIRED for full-signal run

| Provider | Env vars (canonical / alts) | Cost | Source |
|---|---|---|---|
| **DataForSEO** | `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD` | $0.0006-0.05/call, ~$5-15/audit | dataforseo.com |
| **PageSpeed Insights** | `PAGESPEED_API_KEY` | Free (25K/day) | Google Cloud Console → Credentials → API key |
| **Cloro** | `CLORO_API_KEY` or `MONITORING_CLORO_API_KEY` | $0.0012-0.0028/query, ~$2-5/audit | cloro.ai |
| **Apify** | `APIFY_TOKEN` | $0.25-1/audit (covers TikTok, Instagram, Facebook, LinkedIn, GoogleTrends, Reviews, SimilarWeb scraper) | apify.com |
| **Xpoz** | `MONITORING_XPOZ_API_KEY` or `XPOZ_API_KEY` | Per-call, ~$1-3/audit | xpoz |

**Estimated cost per audit: ~$200-400 LLM + ~$15-25 providers = ~$220-425.**

### P1 — Recommended (lens coverage + Phase-0 frames)

| Provider | Env vars | Cost | Lenses |
|---|---|---|---|
| Foreplay | `COMPETITIVE_FOREPLAY_API_KEY` | $49-99/mo subscription | Meta + TikTok + LinkedIn paid creative analysis (~10 lenses) |
| Adyntel | `COMPETITIVE_ADYNTEL_API_KEY`, `COMPETITIVE_ADYNTEL_EMAIL` | $0.006-0.009/page | Google Ads transparency (~6 lenses) |
| Brave Search | `BRAVE_API_KEY` | Free tier 2K/mo | Lens #157 Brave-citation prerequisite |
| SerpAPI | `SERPAPI_KEY` | $50/mo for 5K searches | Live fallback for Adyntel one-offs |
| NewsData | `MONITORING_NEWSDATA_API_KEY` | Free tier | News mention lenses |
| Pod Engine | `MONITORING_POD_ENGINE_API_KEY` | Subscription | Podcast guesting graph |
| GSC | `GSC_SERVICE_ACCOUNT_PATH` | Free, gated by R18 attach | Search Console clicks/impr/CTR |

### P2 — DEFERRED (only matters for specific prospect types)

Per JR review 2026-05-07: the Tier-2 free OAuth tokens divide into
"redundant" (DROPPED — covered by other providers or auth-free
endpoints) and "situational" (DEFERRED — sign up only when prospect
type warrants).

#### DROPPED — redundant, do not bother

| Provider | Reason dropped |
|---|---|
| Reddit OAuth (`REDDIT_CLIENT_ID/SECRET`) | Xpoz already covers Reddit (indexed posts + subreddit metadata). Master plan §4.2 confirms Xpoz handles Twitter + Instagram + **Reddit**. |
| Wikimedia API key (`WIKIMEDIA_API_KEY`) | Base Wikipedia REST + MediaWiki APIs work auth-free. Lift Wing article-quality scoring is the only unique addition; not load-bearing for any v1 lens. |
| Mailinator paid token (`MAILINATOR_API_TOKEN`) | Public-inbox endpoint `api.mailinator.com/v2/domains/public/inboxes/<inbox>` works auth-free. Welcome-email DKIM/SPF signal works without paid tier. |

#### DEFERRED — sign up if prospect type warrants

| Provider | Env var | When it matters |
|---|---|---|
| GitHub | `GITHUB_TOKEN` | OSS / dev-tool / infra prospects (~3-5 lenses gap_flag without). Other prospect types: lens never fires. |
| HuggingFace | `HUGGINGFACE_TOKEN` | AI/ML company prospects only. Non-AI prospects: lens auto-skipped. |
| Product Hunt | `PRODUCT_HUNT_DEVELOPER_TOKEN` | SaaS/startup prospects with launch history. B2B services / local biz: lens never fires. |
| Podchaser | `PODCHASER_TOKEN` | Optional alt to Pod Engine for podcast-guesting graph. Skip both if podcast signal isn't relevant for prospect. |

### Commerce surface (only needed for production deploy)

Skip entirely for the local dry run; needed when wiring the full funnel:

- `RESEND_API_KEY` + `EMAIL_FROM` (default `Freddy <noreply@gofreddy.ai>`)
- `STRIPE_WEBHOOK_SECRET`
- `FIREFLIES_WEBHOOK_SECRET`
- `SLACK_WEBHOOK_{LEADS,PAID,CALLS,COST}`
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ACCOUNT_ID`

## Quick start

```bash
# 1. Provider keys live in <repo-root>/.env — the precheck auto-loads them.
#    Confirmed working as of 2026-05-07: 5 P0 + 6 P1-optional + LLM CLIs
#    + R2 keys all set.

# 2. Verify
python scripts/audit_provider_check.py --human
# Expect: REQUIRED-MISSING + REQUIRED-FAIL: 0

# 3. Pick a test prospect URL (NOT a paying customer for first run)

# 4. Run the §7.7 sequence (see deployment-runbook.md §4)
freddy audit init test-1 --domain example.com
freddy audit run test-1
# ... etc

# OR use the guided helper:
./scripts/audit_dry_run.sh test-1 example.com
```

## Provider reconfirmation TODO (master plan §4.10)

Pass 1 (lens-coverage audit) was done by Agent B 2026-05-06.
Passes 2 + 3 remain — JR + Claude collaborative ~0.5-1 day:

1. **Tier reassignment review** — walk the ~75 free-public-API list
   end-to-end. Confirm 2026-current URL patterns + auth requirements
   (Reddit OAuth recently changed; SecurityHeaders.com → Mozilla HTTP
   Observatory v2 already migrated).
2. **Owned-provider gap check** — confirm 17 wired providers cover the
   192-entry lens map without agent-mapping errors. Spot-check Tier-3
   lens assignments (Wappalyzer + Playwright) for execution feasibility.

Output of those passes: a flat `lens_id → primary_provider +
secondary_providers + tier + cost_per_call + auth_env_var` reference
table. Becomes the Phase 1.5 source-of-truth.

## Phase 1.5 work NOT done (for full Phase-2 readiness)

These don't block the dry run but do block confident production:

- **6 preflight stub fills** (assets/badges/headers/schema/social/tooling)
  — currently return `{"implemented": False}` (master plan §4.8)
- **DNS hygiene full SPF/DKIM/DMARC/BIMI/MTA-STS interpretation** (§4.8)
- **13 free-API URL-pattern wrappers** in agent prompts (§4.9)
- **Provider integration tests** (1 happy path per Tier-1, ~3 fixtures
  per Tier-2 category) — §4.9
- **Hidden-holdout fixtures** for marketing_audit lane (mirror geo /
  competitive / monitoring / storyboard pattern) — needed for
  autoresearch evolve-loop variant rotation, NOT for first dry run
