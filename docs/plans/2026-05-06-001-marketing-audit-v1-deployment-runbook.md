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

## Phase 0.5 — Autoresearch fixture env vars (when ready to evolve)

Required to rotate prompt variants via `autoresearch evolve --lane
marketing_audit` (NOT needed for first dry run; comes after first 3
paid audits give you anchor-quality test prospects).

`autoresearch/eval_suites/search-v1.json` declares 3 fixture slots
for `marketing_audit`. Fill them via `.env`:

```
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ANCHOR_1_CLIENT=<test-prospect-1-client-name>
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ANCHOR_1_CONTEXT=https://test-prospect-1.example
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ANCHOR_2_CLIENT=<test-prospect-2-client-name>
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ANCHOR_2_CONTEXT=https://test-prospect-2.example
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ROTATION_1_CLIENT=<test-prospect-3-client-name>
AUTORESEARCH_SEARCH_MARKETING_AUDIT_ROTATION_1_CONTEXT=https://test-prospect-3.example
```

The rotation strategy expects `anchors_per_domain: 2 + random_per_domain: 1`
per evolve cycle. Anchor fixtures stay constant across cycles (define
the comparison baseline); rotation fixture varies each cohort.

**Holdout fixtures** (the held-out test set used by `custom_promote`
gating): live out-of-repo at `~/.config/gofreddy/holdouts/holdout-v1.json`
(chmod 600). The schema is at `autoresearch/eval_suites/holdout-v1.json.example`
with a `marketing_audit` slot pre-added. Author 2-3 entries there
after you've shipped 3 paid audits worth dogfooding the variant
comparison against. **Until then, `LaneSpec.custom_promote=None`
gates the lane out of automated promotion** — search-v1 fixtures
above are sufficient for variant *evaluation*, not *promotion*.

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
