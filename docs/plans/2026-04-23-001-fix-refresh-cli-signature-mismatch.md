# Fix: `freddy fixture refresh` CLI signature mismatch

**STATUS: SHIPPED 2026-04-23** — see commit `39b8abe` on `feat/fixture-infrastructure`. Implementation + 16 tests.

**Discovered:** 2026-04-23, during Plan A Phase 8 Step 7 smoke test.

## Symptom

Refreshing `geo-semrush-pricing` against `search-v1.json` fails:

```
$ freddy fixture refresh geo-semrush-pricing --manifest ... --pool search-v1
error: fetch failed for freddy-visibility/visibility (arg=https://www.semrush.com):
Usage: freddy visibility [OPTIONS]
Missing option '--brand'.
```

## Root cause

`cli/freddy/fixture/sources.json` declares each source with `command` + `args_from`:

```json
{
  "source": "freddy-visibility",
  "data_type": "visibility",
  "command": ["freddy", "visibility"],
  "args_from": ["context"]
}
```

`cli/freddy/fixture/refresh.py::_run_source_fetch` passes `fixture.context` as a positional arg to the command. That works for `freddy scrape <url>` (positional URL) but breaks every CLI that expects flags:

| Source CLI | Actual signature | `args_from: ["context"]` result |
|---|---|---|
| `freddy scrape` | positional URL | ✅ works |
| `freddy visibility` | `--brand <name>` (required) | ❌ missing --brand |
| `freddy search-ads` | positional domain | ⚠️ `context` string must be a domain; existing values like `"figma"` fail validation |
| `freddy search-content` | `--platform youtube <query>` | ❌ context strings like `"youtube"` parsed as query, not platform |
| `freddy monitor mentions/sentiment/sov` | positional UUID | ✅ works (UUID is the positional) |

So of 7 wired sources, only **3 (scrape + 3× monitor)** work with current `args_from: ["context"]`. The other 4 (visibility, search-ads, search-content × no, actually visibility/search-ads/search-content) need CLI-flag-aware invocation.

## Impact

Refresh fails on any geo / competitive / storyboard fixture that hits visibility / search-ads / search-content. Monitoring fixtures refresh fine. Scrape works for geo. Not a blocker for Plan A code-completeness (Plan A implemented the architecture as specced), but a blocker for end-to-end operational use.

## Fix shape

Extend `sources.json` source descriptors with a richer arg-assembly contract — `args_template` that lists the CLI's actual signature:

```json
{
  "source": "freddy-visibility",
  "data_type": "visibility",
  "command": ["freddy", "visibility"],
  "args_template": [{"flag": "--brand", "from": "client"}, {"flag": "--keywords", "from": "env.AUTORESEARCH_VISIBILITY_KEYWORDS", "default": "semrush"}],
  "arg_for_cache_key": "context"
}
```

Keep `arg_for_cache_key` as the string used for `arg_hash(arg)` so cache-side-read still keys on the same value it would today. `_run_source_fetch` assembles CLI args per `args_template`; `try_read_cache` consults the `arg_for_cache_key` slot (staying backward-compatible).

This is a ~150-line change:
- `sources.json` schema extension
- `refresh.py::_run_source_fetch` arg assembly
- 4 call sites in the session-invoked commands: they must pass the *cache-key-arg* (currently `fixture.context`) to `try_read_cache`, NOT their own positional (`brand`, `query`, etc.) — otherwise cache hits/misses won't align.
- Tests: one per CLI-flag-shape source.

## Workaround until shipped

For Plan B's holdout-v1 authoring, restrict fixtures to sources that work today: monitoring + scrape. Defer visibility / search-ads / search-content holdout fixtures until this bug is fixed.

## Scope boundary

This is a refresh-side + session-side-arg-alignment bug. It does NOT invalidate:
- The cache layer (cache.py works correctly)
- The pool-policies + hard-fail guarantee (holdout isolation is sound)
- The 6 domain judges or evolution loop
- Plan B's autonomous-promotion architecture

## Evidence

- `docs/plans/phase-0-inventory.json` (2026-04-23) confirms `freddy scrape` returns dict shape on live call; `freddy visibility --brand <b> --keywords <k>` also returns dict shape.
- Phase 8 smoke test (Plan A Step 7) with a seeded cache confirmed `freddy scrape` reads cached data cleanly when `FREDDY_FIXTURE_*` env is set.
- Commit `ece2812` already has a harness fix (`F-a-1-5 — freddy visibility --brand without --keywords`) in the same area — prior unrelated knowledge of this CLI's flag requirement.
