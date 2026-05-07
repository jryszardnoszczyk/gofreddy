# Marketing audit v1 — deployment runbook

Captured 2026-05-07 alongside the completed code-side build on
`worktree-agent-aa72d5cb91f3d5528` (HEAD after pressure-test fixes).
Master plan: `2026-05-06-001-marketing-audit-v1-master-plan.md`.

This is the human-side checklist for the §7.7 acceptance run. All
code-side work is on the worktree branch. Nothing is on `main` yet.

## Phase 0 — Cloudflare account + DNS

1. Create Cloudflare zone `gofreddy.ai` (if not already).
2. Provision R2 buckets (separate buckets for prod vs preview):
   ```
   wrangler r2 bucket create gofreddy-scans
   wrangler r2 bucket create gofreddy-scans-preview
   wrangler r2 bucket create gofreddy-audits
   wrangler r2 bucket create gofreddy-audits-preview
   ```
3. DNS records:
   - `api.gofreddy.ai` → A/AAAA pointing at the Fly IP (proxied through CF)
   - `reports.gofreddy.ai` → managed by Worker routes (no A record needed,
     CF Workers attach to the route pattern)
4. GitHub repo secrets (for the matrix-deploy CI job):
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`

## Phase 0.5 — Autoresearch fixtures

`autoresearch/eval_suites/search-v1.json` declares 3 real
public-company fixtures for `marketing_audit`:

**Search-v1 (session loop, 3 fixtures, 2 anchors)**:

| Fixture | Type | Context | Stresses |
|---|---|---|---|
| `marketing-audit-anthropic` (anchor) | AI startup — horizontal foundation-model lab + API | https://www.anthropic.com | Canonical AI-startup ICP; meta-test Cloro 6-engine; B2B+API funnel; dev-docs ecosystem |
| `marketing-audit-dwf` (anchor) | Legal services — global LSE-listed firm w/ Warsaw office | https://dwfgroup.com | Traditional B2B services + sales-led GTM + multi-jurisdictional brand + IP-sensitive content |
| `marketing-audit-perplexity` (rotation) | AI startup — consumer + enterprise AI search | https://www.perplexity.ai | Same AI category as Anthropic, different positioning (search vs model lab) |

**Holdout-v1 (promotion gate, 4 fixtures, 2 anchors — pre-staged in `holdout-v1.json.example`)**:

| Fixture | Type | Context | Held-out from search-v1's |
|---|---|---|---|
| `holdout-marketing-audit-cursor` (anchor) | AI startup — vertical AI code editor | https://cursor.com | Anthropic (same AI category, different ICP — vertical IDE vs horizontal API) |
| `holdout-marketing-audit-ambroziak` (anchor) | Polish dermatology + plastic-surgery chain | https://www.klinikaambroziak.pl | All search-v1 fixtures (no counterpart — pure stress test for non-English / EU / regulated B2C-services) |
| `holdout-marketing-audit-harvey` (rotation) | Vertical AI — legal AI for BigLaw | https://www.harvey.ai | DWF (same legal vertical, opposite side: AI-disruption vs incumbent) |
| `holdout-marketing-audit-hippocratic` (rotation) | Vertical AI — healthcare clinical-ops AI | https://www.hippocraticai.com | Ambroziak (same healthcare vertical, opposite side: AI-disruption vs incumbent) |

**Picks justified**: per JR direction 2026-05-07, fixtures align to the marketing-audit ICP — well-funded AI startups (the active prospect pipeline) plus traditional legal + medical-aesthetic chains (the broader marketing-audit market). Diversity strategy across pools:

- **AI vs traditional pairings** for overfit detection: Anthropic (search-v1) ↔ Cursor (holdout); DWF traditional legal ↔ Harvey AI legal; Ambroziak traditional derm ↔ Hippocratic AI healthcare
- **International coverage**: Ambroziak (Polish-language EU site) tests non-English variant adaptability
- **Vertical AI subset**: Harvey + Hippocratic stress how variants handle AI-disruption positioning in regulated industries
- All 7 are public-presence brands with stable URLs + AI visibility for independently-verifiable findings
- Zero collision with geo/competitive/monitoring/storyboard fixtures (verified)

**Replace any anchor** by editing search-v1.json directly — the `_rationale` field documents what each pick is meant to stress so substitutions stay deliberate.

The rotation strategy expects `anchors_per_domain: 2 + random_per_domain: 1`
per evolve cycle. Anchor fixtures stay constant across cycles (define
the comparison baseline); rotation fixture varies each cohort. Marketing_audit
now meets the contract (2 anchors + 1 rotation).

**Activating holdout fixtures**: live out-of-repo at
`~/.config/gofreddy/holdouts/holdout-v1.json` (chmod 600). The schema
reference at `autoresearch/eval_suites/holdout-v1.json.example` now
contains 4 pre-staged real prospect entries for marketing_audit
(Cursor/Ambroziak/Harvey/Hippocratic — see table above). To activate:
copy the `marketing_audit` array from the .example file into your
real `~/.config/gofreddy/holdouts/holdout-v1.json` under the existing
`domains` block. Agent could not modify the chmod-600 file directly
(safety block); you'd merge it manually. Update suite description if
desired (e.g. "20-row composition" replacing "16-row").

**`LaneSpec.custom_promote=None`** still gates marketing_audit out of
automated promotion regardless of holdout fixtures landing — this
unblocks once first 3 paid audits give you ground-truth rubric scores
to anchor the promotion judgment against. Pre-staging the holdout
fixtures means the gate flips cleanly without re-authoring fixtures.

## Phase 1 — Fly API secrets

Run from a shell with `fly` authenticated:
```
fly secrets set \
  STRIPE_WEBHOOK_SECRET=whsec_... \
  FIREFLIES_WEBHOOK_SECRET=ff_... \
  RESEND_API_KEY=re_... \
  EMAIL_FROM='Freddy <noreply@gofreddy.ai>' \
  SLACK_WEBHOOK_LEADS=https://hooks.slack.com/... \
  SLACK_WEBHOOK_PAID=https://hooks.slack.com/... \
  SLACK_WEBHOOK_CALLS=https://hooks.slack.com/... \
  SLACK_WEBHOOK_COST=https://hooks.slack.com/... \
  R2_ACCESS_KEY_ID=... \
  R2_SECRET_ACCESS_KEY=... \
  R2_ACCOUNT_ID=... \
  R2_PUBLIC_BASE_URL=https://reports.gofreddy.ai
```

All are graceful-degradation: missing keys mean that feature no-ops
rather than crashes (Slack pings skip, email skips, R2 upload skips).
The pipeline still runs end-to-end without them — useful for a dry
acceptance run before production secrets are in place.

## Phase 2 — Worker deploy

CI deploys on push to `main` touching `cloudflare-workers/**`, or
manual via `gh workflow run "Deploy Cloudflare Workers"`. Local one-shot:
```
cd cloudflare-workers
npm install
npx tsc --noEmit          # verify TS compiles
cd intake          && wrangler deploy
cd ../stripe-webhook && wrangler deploy
cd ../scan-hosting   && wrangler deploy
cd ../audit-hosting  && wrangler deploy
```

Per-worker secret (only intake + stripe-webhook need it; optional):
```
echo "<token>" | wrangler secret put FLY_API_TOKEN
```

## Phase 3 — Stripe Checkout setup

JR creates Stripe Checkout sessions manually (master plan §5.4 manual-fire
policy). Required `metadata.client_slug=<slug>` on each Checkout session
— the webhook uses this to look up the workspace.

Stripe Dashboard → Webhooks → endpoint:
```
https://api.gofreddy.ai/v1/audit/stripe/webhook
```
(or via CF worker proxy: `https://api.gofreddy.ai/stripe/webhook`).
Subscribe to: `checkout.session.completed`. Copy the signing secret
into `STRIPE_WEBHOOK_SECRET`.

## Phase 4 — §7.7 acceptance run

Pick a test prospect URL (NOT a paying customer for first run). Then:

```bash
# 1. Workspace init
freddy audit init test-prospect-1 --domain example.com

# 2. First run → halts at intake gate (Stage 0/1/1b/1c run)
freddy audit run test-prospect-1

# 3. Review brief.md + gaps.jsonl, then confirm intake gate
cat clients/test-prospect-1/audit/prediscovery/brief.md
freddy audit confirm-brief test-prospect-1

# 4. Second run → halts at payment gate
freddy audit run test-prospect-1

# 5. Skip Stripe for test — flip paid manually
freddy audit mark-paid test-prospect-1 --stripe-event-id manual-test

# 6. Third run → produces full deliverable (Stage 2/3/4/5)
freddy audit run test-prospect-1

# 7. Review deliverable/report.html locally, edit if needed
open clients/test-prospect-1/audit/deliverable/report.html

# 8. Publish → R2 upload + state flip
freddy audit publish test-prospect-1

# 9. (T+60d after walkthrough call) — close-engagement
freddy audit close-engagement test-prospect-1 --converted Y
```

§7.7 acceptance criteria all pass when:
- Every stage's artifacts exist on disk (auto-checked by smoke test)
- `cost_actual.json` shows realized cost > 0 per stage
- `events.jsonl` has cost_recorded entries
- `curl https://reports.gofreddy.ai/<ulid>/` returns 200
- Lineage row in `audits/lineage.jsonl`

## Known v1 deferrals (NOT bugs — explicit scope cuts)

These appear to "work" but produce placeholder content. Real synthesis
lands as separate PRs after first paid audit:

- **Free scan synthesis** (`src/api/routers/scan.py:_run_scan`) — writes a
  placeholder `synthesis.md`. Real Stage-0 + 1a-subset + Opus pass needs
  `prompts/scan_synthesis.md` + Opus orchestration wired.
- **Fireflies fit-signal extraction** — webhook persists raw
  `transcript.txt` but never produces `fit_signals.json`. Sonnet
  extraction prompt + agent pass needed.

## Merge gate

After the §7.7 acceptance run passes against a test prospect URL, ALL
worktree commits squash-merge to `main`. No mid-build pushes. The
worktree was always the staging area.
