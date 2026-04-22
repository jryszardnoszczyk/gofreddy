# App inventory — read these sources directly

Free-roaming agents can introspect the codebase faster than a regenerated
markdown can stay in sync. Use the breadcrumbs below; each is the
authoritative source for its surface.

## CLI

```
.venv/bin/freddy --help                           # top-level groups
.venv/bin/freddy <group> --help                   # subcommands per group
```

The Typer app lives at `cli/freddy/main.py` (`app` symbol). Walk
`registered_commands` and `registered_groups` if you need a programmatic
listing.

## API

```
curl -s http://127.0.0.1:8000/openapi.json | jq '.paths'
```

The schema is built by FastAPI at runtime. `scripts/export_openapi.py`
emits it to a file when offline.

## Frontend routes

`frontend/src/lib/routes.ts` — `ROUTES` (primary, keyed by name) and
`LEGACY_PRODUCT_ROUTES` (deprecated path list kept for redirects).
`frontend/src/main.tsx` shows which routes are wired into the router.

## Autoresearch

```
ls autoresearch/*.py                              # module surface
ls autoresearch/archive/current_runtime/programs  # per-domain prompts
```

Each `<domain>-session.md` and `meta.md` carries its own working stance.
