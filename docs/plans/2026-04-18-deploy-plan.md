# Gofreddy Deploy Plan

**Date:** 2026-04-18
**Scope:** Ship the agency visibility dashboard to production — backend on Google Cloud Run, frontend on Vercel, DNS via Cloudflare.
**Prerequisite:** All code changes from `docs/plans/2026-04-17-agency-visibility-plan.md` are on `main` (M1–M4 implemented, 9 commits landed, 22/22 tests green, end-to-end CLI round-trip verified locally).
**Reuse doctrine:** Everything shared with freddy — GCP project, Secret Manager secrets, Supabase project, R2 buckets, Cloudflare account. Gofreddy gets its own Cloud Run service + its own Vercel project + its own subdomains. **No new infrastructure is provisioned.**

---

## Identifiers (captured from freddy's production setup)

| What | Value |
|---|---|
| GCP project | same as freddy's (`gcloud config get-value project` to confirm) |
| Region | `us-central1` |
| Supabase project ref | `kpbzyhqqtvihkxzdeptk` |
| Supabase cloud URL | `https://kpbzyhqqtvihkxzdeptk.supabase.co` |
| R2 bucket (prod) | `video-intelligence` (already provisioned; referenced via `r2-bucket-name` secret) |
| R2 bucket (test) | `video-intelligence-test` |
| Cloud Run service name | `gofreddy-api` (new — `freddy-api` keeps running untouched) |
| Vercel project | `gofreddy-app` (new) |
| Backend domain | `api.gofreddy.ai` |
| Frontend domain | `app.gofreddy.ai` |

**Secret Manager entries reused verbatim from freddy** (no new secrets to create):
`database-url`, `supabase-jwt-secret`, `supabase-anon-key`, `r2-account-id`, `r2-access-key-id`, `r2-secret-access-key`, `r2-bucket-name`.

---

## Phase A — Preflight verification (5 min)

```bash
cd /Users/jryszardnoszczyk/Documents/GitHub/gofreddy

# 1. On main, clean tree
git status --short                               # expect empty
git log --oneline -3                             # expect cb9aee6 / 8638a11 / ed13b80 at top

# 2. Tests still green
uv run pytest tests/test_api/ -q                 # expect 22 passed

# 3. Toolchain logged in
gcloud auth list                                 # confirm identity
gcloud config get-value project                  # confirm freddy project
supabase --version                               # 2.75+
vercel --version                                 # 32+ (any recent is fine)

# 4. Confirm the Secret Manager entries exist (read-only list, no values printed)
gcloud secrets list --filter="name~'^(database-url|supabase-jwt-secret|supabase-anon-key|r2-account-id|r2-access-key-id|r2-secret-access-key|r2-bucket-name)$'" --format="value(name)"
# expect all 7 entries printed
```

If any preflight fails: fix before proceeding. Most likely failure = gcloud auth expired (`gcloud auth login`).

---

## Phase B — Apply schema to cloud Supabase (2 min)

```bash
supabase link --project-ref kpbzyhqqtvihkxzdeptk
supabase db push
```

`supabase db push` applies both migrations in order:
1. `20260417000001_init.sql` — creates `users`, `clients`, `user_client_memberships`, `api_keys` (if the cloud DB doesn't have them from gofreddy Phase 1, they get created now).
2. `20260418000001_sessions.sql` — idempotent: `CREATE TABLE IF NOT EXISTS agent_sessions` is a no-op against freddy's pre-existing table, and the follow-up `ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS client_id ...` adds the new tenant column. `CREATE INDEX IF NOT EXISTS` and `CREATE UNIQUE INDEX IF NOT EXISTS` are all no-ops if the indexes already exist.

Verify:
```bash
supabase db remote diff                          # expect "Remote database is up to date"
```

If remote diff surfaces unexpected drift: inspect `supabase/migrations/` vs remote; **do not** blindly overwrite — freddy may have applied its own migrations out-of-band that we don't know about.

---

## Phase C — Deploy backend to Cloud Run (5 min)

Source deploy (no Docker; buildpacks read `Procfile` + `pyproject.toml` + `requirements.txt`).

```bash
gcloud run deploy gofreddy-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 0 --max-instances 5 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production,CORS_ALLOWED_ORIGINS=https://app.gofreddy.ai,GOFREDDY_CLIENTS_DIR=/tmp/clients,SUPABASE_URL=https://kpbzyhqqtvihkxzdeptk.supabase.co \
  --set-secrets DATABASE_URL=database-url:latest,SUPABASE_JWT_SECRET=supabase-jwt-secret:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,R2_ACCOUNT_ID=r2-account-id:latest,R2_ACCESS_KEY_ID=r2-access-key-id:latest,R2_SECRET_ACCESS_KEY=r2-secret-access-key:latest,R2_BUCKET_NAME=r2-bucket-name:latest
```

After deploy, capture the service URL (e.g. `https://gofreddy-api-xxxxx-uc.a.run.app`):

```bash
SERVICE_URL=$(gcloud run services describe gofreddy-api --region us-central1 --format='value(status.url)')
echo "$SERVICE_URL"
```

Smoke tests:
```bash
curl -sS $SERVICE_URL/health                     # expect {"status":"ok"}
curl -sS -I $SERVICE_URL/v1/sessions             # expect HTTP/2 401 (auth required, not 500)
curl -sS $SERVICE_URL/openapi.json | jq '.paths | keys'
# expect 13 paths: /health, /login, /portal/{slug}, /v1/api-keys, /v1/api-keys/{key_id},
#   /v1/auth/logout, /v1/auth/me, /v1/portal/{slug}/summary, /v1/sessions,
#   /v1/sessions/{session_id} and 3 sub-resources (actions, iterations, transcript)
```

### If the buildpack rejects Python 3.13

Gofreddy pins `requires-python = ">=3.13,<3.14"`. If Cloud Run's buildpack hasn't caught up, fall back to a minimal Dockerfile (copy of `freddy/Dockerfile` with the WeasyPrint apt block removed and `CMD` changed to plain `app`). Add it, re-run `gcloud run deploy --source .` — buildpacks auto-detect Dockerfile when present.

---

## Phase D — Deploy frontend to Vercel (5 min)

```bash
cd frontend

# First-time link only:
vercel link                                      # create new project: gofreddy-app

# Env vars (all three required, all scoped to "production"):
vercel env add VITE_SUPABASE_URL production       # paste: https://kpbzyhqqtvihkxzdeptk.supabase.co
vercel env add VITE_SUPABASE_ANON_KEY production  # paste cloud anon key (same one freddy uses)
vercel env add VITE_API_URL production            # paste $SERVICE_URL from Phase C (provisional — swap to api.gofreddy.ai after Phase E)

# Regenerate types from the live backend (now reachable):
VITE_API_URL=$SERVICE_URL npm run api:generate

vercel --prod
# Capture the vercel URL (e.g. gofreddy-app.vercel.app)
```

Smoke test: open `https://gofreddy-app.vercel.app/login` — should render the login page.

---

## Phase E — DNS wiring (10 min, 15 min propagation)

### E.1 — `api.gofreddy.ai` → Cloud Run

```bash
gcloud run domain-mappings create \
  --service=gofreddy-api \
  --domain=api.gofreddy.ai \
  --region=us-central1
```

Google returns one or more DNS records to add. Copy them into Cloudflare for `api.gofreddy.ai` (usually a CNAME to `ghs.googlehosted.com` or specific A/AAAA records).

### E.2 — `app.gofreddy.ai` → Vercel

```bash
# In the frontend/ dir (still vercel-linked to gofreddy-app)
vercel domains add app.gofreddy.ai
```

Vercel returns a CNAME target (usually `cname.vercel-dns.com`). Add that CNAME in Cloudflare.

### E.3 — Wait + verify

```bash
# When dig succeeds from two different resolvers, propagation is done.
dig api.gofreddy.ai +short
dig app.gofreddy.ai +short

curl -sS https://api.gofreddy.ai/health          # expect {"status":"ok"}
curl -sS -I https://app.gofreddy.ai              # expect 200
```

### E.4 — Swap frontend to the real API URL

Once `api.gofreddy.ai` resolves:
```bash
cd frontend
vercel env rm VITE_API_URL production --yes
vercel env add VITE_API_URL production           # paste: https://api.gofreddy.ai
vercel --prod                                    # redeploy with the correct env
```

---

## Phase F — Seed + end-to-end verification (10 min)

### F.1 — Create the first client + membership

In the Supabase SQL editor (production project):
```sql
INSERT INTO clients (slug, name)
VALUES ('demo-clinic', 'Demo Clinic')
ON CONFLICT (slug) DO NOTHING;
```

### F.2 — Sign in once to auto-create your user row

Open `https://app.gofreddy.ai/login`, log in with Google (or email/password). This triggers backend's `_resolve_user_from_jwt` to insert your row into `users`.

### F.3 — Grant yourself admin

Back in the Supabase SQL editor:
```sql
INSERT INTO user_client_memberships (user_id, client_id, role)
SELECT u.id, c.id, 'admin'
  FROM users u, clients c
 WHERE u.email = 'jryszardn@gmail.com' AND c.slug = 'demo-clinic'
ON CONFLICT DO NOTHING;
```

### F.4 — Generate a production API key

Browser: `https://app.gofreddy.ai/dashboard/settings` → API Keys → **Create key** → copy the `vi_sk_…` value (shown once). This exercises the `POST /v1/api-keys` path.

### F.5 — Full pipeline end-to-end

On JR's laptop:
```bash
freddy auth login --api-key vi_sk_<paste> --base-url https://api.gofreddy.ai
freddy auth whoami                               # expect {"user":{...}}
freddy session start --client demo-clinic --purpose prod-smoke-test
freddy iteration push --number 1 --type DISCOVER --status success
freddy session end --summary "prod smoke test ok"
```

Browser: `https://app.gofreddy.ai/dashboard/sessions` → refresh → the session should appear with `action_count` / status=completed / summary shown.

**This is the deploy acceptance gate.** If the session doesn't show up in the dashboard within 60s, something in the stack is misaligned — do not declare the deploy done until it works.

---

## Rollback

### Backend
`gcloud run services update-traffic gofreddy-api --to-revisions=<previous-revision>=100 --region=us-central1`
(list revisions with `gcloud run revisions list --service=gofreddy-api --region=us-central1`)

### Frontend
`vercel rollback` (or use the Vercel dashboard's "Promote" button on the previous deployment).

### Schema
Supabase migrations are forward-only on shared infra. Destructive rollback = drop the added column:
```sql
ALTER TABLE agent_sessions DROP COLUMN IF EXISTS client_id;
DROP INDEX IF EXISTS idx_sessions_client_tenant;
```
Only do this if freddy-production breaks. Gofreddy's code handles `client_id IS NULL` for legacy rows; freddy doesn't read the new column at all.

---

## Known limitations (intentional; not deploy blockers)

1. **`/portal/<slug>` on the backend reads from filesystem** (`GOFREDDY_CLIENTS_DIR=/tmp/clients` on Cloud Run — ephemeral). Anyone hitting `api.gofreddy.ai/portal/<slug>` directly will get 500-class errors. The user flow is `app.gofreddy.ai/portal/<slug>` → frontend redirects to `/dashboard/sessions?client=<slug>` (client-side), which works. Fix when needed: refactor portal to read sessions from Postgres, or remove the backend portal route entirely.

2. **Generated OpenAPI client in `frontend/src/lib/generated/`** carries types for endpoints that no longer exist (search, analyze, trends). Build still passes because the dead types are imported but unused. Phase D step already includes `npm run api:generate` to regenerate against the live backend; after that runs, the dead types disappear.

3. **Invite-only signup.** Gofreddy has no admin UI for inviting clients. Workflow is: JR inserts a row in `clients` + `user_client_memberships` via Supabase SQL editor before the client tries to log in. Revisit if > 10 clients; build a `POST /v1/admin/clients` endpoint then.

4. **Token blocklist is in-memory per Cloud Run instance.** With `--max-instances 5`, a logout on one instance doesn't revoke the token on others. Acceptable for < 1000 users; escalate to Redis or a `revoked_tokens` table if concurrent sessions grow.

---

## Post-deploy checklist (low-priority, nice-to-have)

- [ ] Cloud Run alert policy on 5xx rate (uptime + error budget)
- [ ] Cloudflare cache purge on frontend deploy (vercel handles this automatically)
- [ ] Document the `freddy auth login` + `freddy session start` flow in an internal runbook
- [ ] Add a monitoring tag to Cloud Run service for cost attribution

---

## Critical files in the repo (already committed)

- `Procfile` — Cloud Run buildpack entry point
- `requirements.txt` — pip-installable dep set (uv.lock fallback)
- `.gcloudignore` — excludes autoresearch/, tests/, docs/, frontend/, secrets from source upload
- `supabase/migrations/20260418000001_sessions.sql` — idempotent DB migration
- `src/api/main.py` — CORS + lifespan wiring
- `docs/plans/2026-04-17-agency-visibility-plan.md` — implementation plan (M1–M4 detail)

**Estimated total deploy time: 35–45 min** (including DNS propagation wait).
