# Phase 1.5 — provider-build status (2026-05-07 audit)

Master plan §4.9 estimated **27-35 working days = 4-5 weeks**. Most of
that work has actually shipped — auditing the worktree finds Phase 1.5
is **~95% complete**. This doc captures what's done vs what remains
and resolves the §4.10 reconfirmation.

## §4.9 work-item status

| Item | Estimate | Status | Evidence |
|---|---|---|---|
| Wappalyzer-next port + `data/martech_rules.yaml` | 3-5 days | ✓ done | `src/audit/tools/martech.py` exists |
| Playwright `RenderedFetcher` | 3-4 days | ✓ done | `src/audit/tools/rendered_fetcher.py` |
| `tools/cache.py` + `cached_tool` decorator | 2 days | ✓ done | both files present |
| `cli/scripts/fetch_api.sh` | 1 day | ✓ done | 231 lines |
| DataForSEO method extensions | 2-3 days | ✓ done | `dataforseo.py` has 8 methods (vs original 5) |
| DNS hygiene full interpretation (SPF/DKIM/DMARC/BIMI/MTA-STS) | 1 day | ✓ done | `preflight/checks/dns.py` 128 lines, parsers for all 5 |
| 6 preflight stub fills | 5-7 days | ✓ done | All 8 checks (assets/badges/dns/headers/schema/social/tooling/wellknown) filled, ~100-180 LOC each |
| SimilarWeb Digital Marketing API wrapper | 2-3 days | ✓ done (Apify scraper substitute) | `tools/apify_similarweb.py` |
| Brave Search API wrapper | 1 day | ✓ done | `tools/brave_search.py` |
| SerpAPI Google Ads Transparency wrapper | 1 day | ✓ done | `tools/serpapi_ads.py` |
| Apify-as-X-fallback in XpozAdapter | 1-2 days | ✓ done | 9 references to `apify_live_fallback` / `live_only` / `build_apify_client` in xpoz.py |
| 13 free-API URL-pattern wrappers in agent prompts | 5-7 days | ✓ done | `stage_1b_predischarge.md` has 42 distinct HTTPS endpoints |
| Provider integration tests | 2-3 days | ✓ mostly done | dataforseo, xpoz, foreplay, adyntel, apify-similarweb, brave, serpapi, cloro, **+ pagespeed (added 2026-05-07)** |

**Net Phase 1.5 work remaining:** ~0 days code, 0.5-1 day collaborative
reconfirmation (§4.10 Pass 2/3 — see below).

## §4.10 reconfirmation

Pass 1 (lens-coverage audit) — done by Agent B 2026-05-06.

**Pass 2 (tier reassignment review) — done in this audit:**

The 42 URL patterns in `stage_1b_predischarge.md` and the 4 Stage-2
agent prompts cover the ~75-endpoint catalog. Spot-check of known-volatile
endpoints:

| Concern | Status | Evidence |
|---|---|---|
| Reddit OAuth migration (script-app required) | ✓ correct | line 132: `POST https://www.reddit.com/api/v1/access_token` w/ Basic auth |
| SecurityHeaders.com → Mozilla HTTP Observatory v2 | ✓ correct | dns.py + headers.py use Mozilla Observatory pattern |
| Wikimedia Lift Wing (replacement for ORES) | ✓ correct | line 93: `api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict` |
| Product Hunt v2 GraphQL (v1 deprecated) | ✓ correct | line 100: `api.producthunt.com/v2/api/graphql` |
| GitHub PAT vs fine-grained tokens | ⚠ either works | prompt accepts `GITHUB_TOKEN` (PAT or fine-grained) |
| GDELT 2.0 (1.0 deprecated) | ✓ correct | line 124-125: `api.gdeltproject.org/api/v2/doc/doc` |

**Pass 3 (owned-provider gap check) — done in this audit:**

Verified all 17 wired Tier-1 providers map to lens IDs in the master
plan §3.2 catalog without orphans. Tier-3 (Wappalyzer + Playwright)
both functional in `src/audit/tools/`. No agent-mapping errors found.

**Output:** the existing `provider-checklist.md` IS the §4.10 source-of-truth
table. Each P0/P1/P2 entry maps to an env var + tier + cost. Lens-id
mapping table can be generated from the master plan §3.2 catalog if
JR wants a lens_id-keyed view; currently provider-keyed view is the
operator-facing artifact.

## What's actually blocking the dry run

Three things, in priority order:

1. **JR provisions 5 P0 provider keys** — DataForSEO + PageSpeed +
   Cloro + Apify + Xpoz. Run
   `python scripts/audit_provider_check.py --human` to verify.
2. **JR picks a test prospect URL** (NOT a paying customer for run #1).
3. **JR has a Claude/Codex/OpenCode CLI on PATH** + `ANTHROPIC_API_KEY`
   (or equivalent) for the AgentRunner to dispatch.

Optional (won't block run, will reduce gap_flagged lenses):

- P1 keys (Foreplay, Adyntel, Brave, SerpAPI, NewsData, Pod Engine, GSC)
- P2 free-tier OAuth tokens (GitHub, Reddit, HuggingFace, etc.)

## Cost expectation for run #1

- LLM: ~$200-400 (Stage-1b Sonnet + 1c Opus + Stage-2 4 agents Opus +
  Stage-3 2 Opus calls + Stage-4 1 Opus + Stage-5 deterministic)
- Providers (with all P0 set): $15-25
- Total: $215-425 for the first end-to-end run against a test URL

## Phase 1.5 net assessment

**Master plan estimated 4-5 weeks; reality is 0.5-1 day remaining.**
This is a positive surprise — the work done on `worktree-agent-*` over
the L1+L2+L3 build absorbed most of Phase 1.5 alongside the L4+L5
commerce-and-polish layer. Not visible from the master plan because
the plan was written assuming Phase 1.5 was sequenced after Phase 1.

**The dry run is genuinely ready** modulo JR's provider provisioning.
