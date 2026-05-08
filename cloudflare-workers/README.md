# Cloudflare Workers — gofreddy.ai marketing audit edge surface

Four workers + two R2 buckets back the public commerce + delivery
funnel. Master plan §5.5.

| Worker | Route | Backed by |
|---|---|---|
| `intake/` | `gofreddy.ai/api/scan-request` | Forwards form POST → Fly API `/v1/scan/request` |
| `stripe-webhook/` | `api.gofreddy.ai/stripe/webhook` | Forwards Stripe event → Fly API `/v1/audit/stripe/webhook` (signature stays on Fly) |
| `scan-hosting/` | `reports.gofreddy.ai/scan/<id>/` | Serves R2 bucket `gofreddy-scans` |
| `audit-hosting/` | `reports.gofreddy.ai/<ulid>/` | Serves R2 bucket `gofreddy-audits` |

## Deploy

```bash
cd cloudflare-workers/intake          && wrangler deploy
cd cloudflare-workers/stripe-webhook  && wrangler deploy
cd cloudflare-workers/scan-hosting    && wrangler deploy
cd cloudflare-workers/audit-hosting   && wrangler deploy
```

CI deploy via `.github/workflows/deploy-workers.yml` runs on pushes to
`main` that touch `cloudflare-workers/**`.

## Secrets per worker

- `intake`            — `FLY_API_TOKEN` (optional)
- `stripe-webhook`    — `FLY_API_TOKEN` (optional)
- `scan-hosting`      — none (R2 binding handles auth)
- `audit-hosting`     — none

Set with `wrangler secret put <NAME>` from each worker dir.

## R2 bucket setup

```bash
wrangler r2 bucket create gofreddy-scans
wrangler r2 bucket create gofreddy-audits
wrangler r2 bucket create gofreddy-scans-preview
wrangler r2 bucket create gofreddy-audits-preview
```

## DNS prerequisites (JR-coordinated)

- `gofreddy.ai` zone in Cloudflare
- `api.gofreddy.ai` → Fly API IPs (proxied through CF)
- `reports.gofreddy.ai` → managed by Worker routes (no A record needed)

## Local dev

```bash
cd cloudflare-workers/intake && wrangler dev
```
