# SEED — GoFreddy app surface inventory

This is **inventory, not specification**. No "should", "must", or "required" language. The evaluator uses it to know what exists and is worth exercising; it is never a source of truth for what the app is supposed to do.

The fixer never reads this file.

## Agency workflows

- `freddy client new <name>` — create a client workspace
- `freddy session start` / `freddy session list` — run and list agent sessions
- `freddy auth login` — local CLI auth
- `freddy save`, `freddy digest`, `freddy transcript` — session post-processing
- `freddy audit`, `freddy evaluate`, `freddy iteration` — audit and evaluation flows
- `freddy auto-draft`, `freddy monitor`, `freddy query-monitor` — automation wrappers

## Research & intelligence

- `autoresearch/evolve.py` — variant evolution entry point
- `autoresearch/evaluate_variant.py` — variant evaluation
- `autoresearch/archive/current_runtime/programs/<domain>/{meta.md,session.md}` — per-domain session programs (competitive, geo, monitoring, storyboard)
- `freddy competitive`, `freddy seo`, `freddy sitemap`, `freddy trends`, `freddy visibility`, `freddy search-*`, `freddy detect`, `freddy scrape` — research-specific CLI wrappers

## Platform

- FastAPI backend at `http://127.0.0.1:8000` (entry `src.api.main:app`)
- OpenAPI served at `/openapi.json`, health at `/health`
- Key routes under `/v1/` — sessions, clients, api-keys, monitors, evaluations, telemetry
- Supabase local stack (GoTrue at `/auth/v1/`, Postgres on 54322) — harness mints a JWT at preflight

## Client plane

- Vite + React frontend at `http://127.0.0.1:5173`
- Canonical routes defined in `frontend/src/lib/routes.ts` (`ROUTES` + `LEGACY_PRODUCT_ROUTES`)
- Dashboard tree: `/dashboard`, `/dashboard/sessions`, `/dashboard/settings`, `/dashboard/usage`, `/dashboard/library`, `/dashboard/monitoring`, `/dashboard/c/:conversationId`
- Landing/auth: `/`, `/pricing`, `/login`, `/auth/callback`
- Legacy surfaces still exposed under `LEGACY_PRODUCT_ROUTES`

## Known must-work-today exception

Live session telemetry on the dashboard is a product need but is currently absent or stubbed. This note exists so the first real harness run flags it correctly as a product defect rather than treating the stub as intentional.
