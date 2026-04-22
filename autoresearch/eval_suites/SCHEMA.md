# Fixture Schema

**Manifest shape & field contracts:** see `autoresearch/eval_suites/search-v1.json` (canonical example) and `cli/freddy/fixture/schema.py::parse_suite_manifest` (validator).

**Cache layout & arg-hash contract:** see `cli/freddy/fixture/cache.py` module docstring.

**Source descriptors & retention defaults:** see `cli/freddy/fixture/sources.json`.

**Pool isolation policy:** see `cli/freddy/fixture/pool_policies.json`. Unknown pool → `_default` → hard-fail on miss (default-deny).

**Holdout manifests:** live out-of-repo at `~/.config/gofreddy/holdouts/` (`chmod 600`), loaded via `EVOLUTION_HOLDOUT_MANIFEST`.

**Seed semantics:** `--seeds N` = N independent sessions with `AUTORESEARCH_SEED=<replicate-label>`. Variance comes from LLM nondeterminism; Plan B Phase 0 probe verifies MAD>0 on a known-healthy fixture.

**Threat boundary caveat:** pool separation is behavioral (chmod + refresh wrapper + cache-first-or-fail), NOT cryptographic. A same-UID process can read the credentials file. See Plan B header "Accepted risks".
