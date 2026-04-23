# Fixture Schema

Authoritative reference for fixture manifests, fixture entries, and the supporting cache / pool / loader contracts. Code is the source of truth; this file documents the contract for humans and agents.

## Suite manifest

Top-level JSON shape. Canonical example: `autoresearch/eval_suites/search-v1.json`. Validator: `cli.freddy.fixture.schema.parse_suite_manifest`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `suite_id` | string | yes | Pool identifier. Must equal the `--pool` argument of every refresh/dry-run/discriminate invocation (enforced by `assert_pool_matches`). |
| `version` | string (semver) | yes | Suite-level semver — `1.0`, `1.2.3`. Matched by `^\d+\.\d+(\.\d+)?$`. |
| `description` | string | no | Free-form. |
| `eval_target` | object | no | `{backend, model, reasoning_effort}` — drives subprocess env for fixture sessions. |
| `rotation` | object | no | Rotation config, consumed by `_sample_fixtures`. `{strategy, anchors_per_domain, random_per_domain, seed_source, cohort_size}`. Omit or set `strategy="none"` to evaluate all fixtures. |
| `domains` | object | yes | Maps domain name (`geo` / `competitive` / `monitoring` / `storyboard`) → list of fixture entries. |

## Fixture entry

One entry per fixture inside `domains.<domain>`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `fixture_id` | string | yes | Unique per suite. Duplicates rejected by `validate`. |
| `client` | string | yes | Human label; non-empty. |
| `context` | string | yes | Primary arg. Refresh passes this as positional arg to the source command; session-side CLI commands must pass the same string for cache hits. Supports `${ENV_VAR}` substitution. |
| `version` | string (semver) | yes | Per-fixture semver. Backfilled to `1.0` on `search-v1`. |
| `max_iter` | int | no | Default `3`. Variant session max iterations. |
| `timeout` | int | no | Default `300` (seconds). |
| `anchor` | bool | no | Default `false`. Anchor fixtures are always included by rotation sampling. |
| `env` | object | no | `{STRING: STRING}`. Exposed to the variant's session subprocess. |
| `retention_days` | int | no | **Per-fixture override** for the source's default retention. Rare; use only when a specific fixture has tighter or looser freshness requirements than the source-level default in `sources.json`. |

## Semver policy

`^\d+\.\d+(\.\d+)?$` — `1.0`, `2.1`, `1.2.3` all valid. `v1`, `latest`, empty, non-numeric rejected. Bump the fixture's `version` whenever a refresh should produce distinct cache entries rather than overwriting (archival still happens on overwrite, but a bump avoids any chance of cross-version cache reuse). Suite-level `version` is independent of any fixture version.

## Env-var reference syntax

`${NAME}` — all uppercase, digits, underscores. Matched by `\$\{([A-Z0-9_]+)\}`. `freddy fixture envs <manifest>` lists every referenced var and marks each as set (`✓`) or unset (`✗`). `--missing` filters to unset-only. `${lowercase}` and `$NAME` (no braces) are NOT substituted.

## Cache semantics

Cache root: `~/.local/share/gofreddy/fixture-cache/<pool>/<fixture_id>/v<version>/`. One dir per fixture version; refresh archives the existing dir to `v<version>.archive-<YYYYMMDDTHHMMSSZ>/` before rewriting.

Artifact filename: `<source>_<data_type>__<arg_hash>.json` where `arg_hash = sha1("|".join([arg, *sorted(shape_flags.items())])).hexdigest()[:12]`. Shape flags (e.g. `{"format": "summary"}`) that affect output shape participate in the key so `--format summary` and `--format full` don't collide.

**Cache-hit contract:** `try_read_cache(source, data_type, arg, shape_flags=None)` returns the cached JSON only when `source`, `data_type`, AND the full `arg` string (not just its truncated hash) all match an entry in the manifest. This guards against sha1-truncation collisions.

**Cache miss — pool-dependent (see `pool_policies.json`):**
- `search-v1` → `on_miss=live_fetch` → returns `None`; caller proceeds with live provider call.
- `holdout-v1` → `on_miss=hard_fail` → raises `RuntimeError` with a remediation message (`freddy fixture refresh <fixture_id> --pool <pool> ...`).
- unknown pool → `_default` → `hard_fail` (default-deny; a future pool rename does not silently downgrade isolation).

Staleness: three tiers from `shortest_retention_days` across the fixture's sources:
- `age < 50%` → `fresh`
- `50% ≤ age < 100%` → `aging` (stderr warning on reads; no auto-refetch)
- `age ≥ 100%` → `stale` (stderr warning on reads; no auto-refetch)

Refresh is manual only. Cache is never auto-populated.

## Per-fixture retention override

The default retention window comes from `cli/freddy/fixture/sources.json` (per-domain, per-data-type). A fixture may override it via its own `retention_days` field:

```json
{
  "fixture_id": "geo-fastmoving-page",
  "client": "example",
  "context": "https://example.com/daily-feed",
  "version": "1.0",
  "retention_days": 7
}
```

Refresh reads the fixture-level value first, falls back to `sources.json` defaults. Use sparingly — the source-level default should be correct for most fixtures in the same domain.

## Holdout manifests

Holdout suites live **out-of-repo** at `~/.config/gofreddy/holdouts/` with `chmod 600`. Loaded via the `EVOLUTION_HOLDOUT_MANIFEST` env var (absolute path to JSON) or `EVOLUTION_HOLDOUT_JSON` (inline). A redacted, in-repo stub at `autoresearch/eval_suites/holdout-v1.json.example` demonstrates shape for reviewers.

**Sentinel guard:** the example file carries `"is_redacted_example": true`. The autoresearch-side loader refuses any manifest with this field set to `true`, regardless of location — an accidentally-pointed-at example file fails-loud rather than silently running holdout sessions against stub URLs.

## Threat boundary caveat

Pool separation is **behavioral**, not cryptographic:
- `chmod 600` on the credentials file (`~/.config/gofreddy/holdouts/.credentials`)
- The `freddy fixture refresh --isolation ci` wrapper
- The `try_read_cache` hard-fail on holdout-pool misses
- `_score_env()` scrubbing of `EVOLUTION_INVOKE_TOKEN` + provider API keys before spawning untrusted variant subprocesses

A same-UID process can read the credentials file. The guarantee is "an honest variant cannot accidentally leak holdout identity to a provider log"; a malicious same-UID attacker is out of scope for Plan A. See Plan B header "Accepted risks" for the complete threat model.

## Related references

- `cli/freddy/fixture/schema.py` — parsers + `assert_pool_matches` guard
- `cli/freddy/fixture/cache.py` — cache manifest format + IO + arg-hash + staleness
- `cli/freddy/fixture/sources.json` — per-domain source descriptors + retention defaults
- `cli/freddy/fixture/pool_policies.json` — pool → miss-semantics map
- `autoresearch/events.py` — unified events log (`content_drift`, `judge_abstain`, `judge_unreachable` kinds)
- `autoresearch/eval_suites/search-v1.json` — canonical in-repo manifest example
- `autoresearch/eval_suites/holdout-v1.json.example` — redacted holdout shape reference
