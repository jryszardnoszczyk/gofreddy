# Autoresearch layer-collapse plan (Phase 2)

**Predecessor:** `docs/plans/2026-05-08-001-autoresearch-pipeline-rigidity-investigation.md` — investigation report establishing the architectural shape.
**Date:** 2026-05-08
**Trigger:** JR's framing — "isn't it the case that we're maybe over-engineering it with too much Python code?" Five hypotheses (H1–H5) all surfaced the same pattern: **mediating layers between the agent and the work, each added for a reason, none deleted as the next accreted.**
**Phase 1** (quick wins, shipped on this branch) covered the immediate v009 fixes: visibility cache key, `tool_error_rate` metric, autogen STRUCTURAL block enumeration, sandbox-blocks-loopback warning. Phase 2 is the structural collapse.

## Why this plan exists

Phase 1 made v010 re-runnable. Phase 2 makes the *next* class of bugs harder to write. The investigation showed five separate failure modes, all rooted in the same shape: prompt vs validator vs cache vs scorer vs sandbox each have their own contract, none co-generated, drift surfaces as silent wrong answers.

The bet of this plan: **delete ~600 lines of mediating layer, strengthen ~200 lines of contract code, and the bugs in §3 of the investigation report stop being possible to write.**

## Scope

In scope:

1. SSRF guard scope-narrowing in `cli/freddy/commands/sitemap.py`.
2. `prompt_builder_entrypoint` allowlist replacement.
3. `summarize_session.py` extraction + bucketing simplification.
4. `regen_program_docs` reflection from variant workflow code.
5. Visibility cache shape_flags landed in `sources.json` + refresh tooling (full version of Phase 1 §3.2).
6. Test surface to keep the contracts honest.

Out of scope (separate plans):

- Per-claim provenance manifest (G3 from H5 — costs 2-3 weeks design + implementation).
- Restructuring the meta-agent's mutation surface (the pattern of variants owning their own `workflows/` and `scripts/` is load-bearing).
- Anything that touches the actual evolution loop's gradient signal (out of scope for "stop fighting the harness"; that's a separate "make scoring smarter" plan).

## Approach

Six work units. Each is a separate, independently-mergeable change. Order within phases is flexible; cross-phase dependencies are noted.

### Unit 1 — Sitemap SSRF guard: split error codes, fail-open on DNS

**File:** `cli/freddy/commands/sitemap.py`, `src/common/url_validation.py`.

The current guard at `sitemap.py:84-91` calls `resolve_and_validate(url)` which does `socket.getaddrinfo` plus IP-range checks, then re-raises every failure as `ValueError`. The sitemap command unconditionally maps any `ValueError` to `invalid_url`. The intent of the guard (per its comment) is to reject *private/blackhole IPs in <1s* — not to enforce reachability. Three fixes:

1. In `src/common/url_validation.py`, distinguish two failure modes via separate exception classes — `DNSResolutionFailed` (transient / sandboxed / no DNS) vs `BlockedIPRange` (resolved to a blocked CIDR). Keep the `resolve_and_validate` signature backward-compatible for callers that don't care, but expose the new types in the module.
2. In `sitemap.py`, catch only `BlockedIPRange` and emit `invalid_url`. Catch `DNSResolutionFailed` and let the call proceed to `SitemapParser.parse(url)` — that parser has its own httpx error handling and will surface a structured network error.
3. Add a new error code `dns_error` to the CLI's error envelope vocabulary so that *if* `SitemapParser` later decides DNS is the problem, it can surface it with a code distinct from `invalid_url` and `connection_error`.

**Test surface:**
- `test_sitemap_dns_failure_does_not_emit_invalid_url` — monkeypatch `resolve_and_validate` to raise `DNSResolutionFailed`; assert `sitemap_command` does not emit `invalid_url`.
- `test_sitemap_blocked_ip_emits_invalid_url` — monkeypatch to raise `BlockedIPRange`; assert `invalid_url` is emitted.
- `test_url_validation_distinguishes_dns_vs_blocked_ip` — the two error classes are surfaced and not collapsed.

**Estimated cost:** ~30 LOC + tests, ~1-2 hours.

**Cross-cuts:** none.

### Unit 2 — prompt_builder_entrypoint allowlist replacement

**File:** `autoresearch/harness/prompt_builder_entrypoint.py`, `tests/autoresearch/test_prompt_builder_isolation.py`.

The current 80-prefix allowlist (`prompt_builder_entrypoint.py:58-91`) is layer 2 of 3 in the defense-in-depth chain. Layer 1 (`python3 -I`) does the actual security work; the allowlist is operational diagnostics that has caused at least one full-validation outage (commit `c120815`, 2026-05-07) when CPython 3.13's `runpy` started loading `urllib`/`ipaddress`. Replace with a single check that `autoresearch.__file__` resolves under `REPO_ROOT`:

```python
def _enforce_no_rogue_autoresearch() -> None:
    import autoresearch
    expected = os.environ.get("AUTORESEARCH_EXPECTED_REPO_ROOT")
    if expected and not autoresearch.__file__.startswith(expected):
        sys.stderr.write(...)
        raise SystemExit(2)
```

The threat model documented in the file's docstring is "a rogue package on PYTHONPATH that redefines `autoresearch.harness.session_evaluator.build_critique_prompt`". `python3 -I` already drops PYTHONPATH; the only residual risk is a same-named package smuggled in via the `-c` bootstrap's explicit `sys.path.insert(0, REPO_ROOT)` — which the new check catches by resolving `__file__` against `REPO_ROOT`.

Update the bootstrap in every `archive/v00N/scripts/evaluate_session.py` (and the live equivalent if/when extracted in Unit 3) to pass `AUTORESEARCH_EXPECTED_REPO_ROOT=<resolved-repo-root>` into the subprocess env.

Add a CI test that runs the entrypoint under Python 3.12, 3.13, 3.14 (via tox or a matrix) on a clean venv and asserts exit 0 — catches the next stdlib-drift regression mechanically before validation runs.

**Test surface:**
- Existing 5 tests stay: happy-path, polluted PYTHONPATH, polluted cwd, malformed stdin, missing criteria field.
- New: `test_rogue_autoresearch_resolves_to_wrong_path` — plant a `/tmp/rogue/autoresearch/__init__.py`, set `REPO_ROOT` env to the real repo, assert exit-2 with a diagnostic mentioning the rogue path.
- New: CI matrix snapshot — `test_no_module_loaded_outside_known_set` runs the entrypoint and asserts the post-bootstrap `sys.modules` set is a subset of an explicitly committed snapshot for each supported Python version.

**Estimated cost:** ~80 LOC removed, ~30 LOC added, ~2-4 hours.

**Cross-cuts:** the v007/v007-curated archives carry their own copies of the bootstrap — those need updating too if they're still active. Verify by listing `autoresearch/archive/*/scripts/evaluate_session.py` and patching each.

### Unit 3 — Extract `summarize_session.py` to live `autoresearch/scripts/`, simplify the bucket map

**Files:** new `autoresearch/scripts/summarize_session.py`; delete the per-archive `autoresearch/archive/v00N/scripts/summarize_session.py` copies; update `autoresearch/archive/v00N/run.py` to import from the live path.

Today the script is per-variant — every `archive/v00N/scripts/summarize_session.py` is a copy. Variants legitimately mutate prompts and workflows; they should not normally mutate utility scripts. The per-variant copy means H4 fixes have to be applied N times and a meta-agent could weaken the script by editing its own variant's copy.

Three concrete changes:

1. **Move** `archive/current_head/scripts/summarize_session.py` → `autoresearch/scripts/summarize_session.py`. (The Phase 1 fix already added `tool_error_rate`; carry it across.)
2. **Update** every active variant's `run.py` to import from the live module instead of running the per-archive script as a subprocess.
3. **Simplify** the status-bucket map. Today the H4 issue is that `completed_degraded` falls into `uncategorized` (silent). Two paths forward:
   - Drop the bucket map entirely and let the scorer read raw `results.jsonl`. The agent's `notes` field is richer than the buckets anyway.
   - Or: keep the bucket map but treat any `*_degraded` suffix as `failed` with an explicit warning. Less disruptive but only half the layer collapse.

   Recommend the first — drop the bucket map. The scorer is already an LLM; it can parse a JSON list of result rows. The bucket counters that downstream code reads (`session_summary.json:iterations.productive`) become a Phase 1 artifact for the dashboard digest, not a scorer input.

4. **Update** `judges/evolution/agents/variant_scorer.py` and `autoresearch/evaluate_variant.py` to ship the raw `results.jsonl` to the scorer prompt rather than the buckets. The scorer prompt at `judges/evolution/prompts/scorer.md` should be updated to make tool health one of the things it explicitly considers, OR add a multiplicative `tool_health_score` so the LLM doesn't have to (latter is the H4 option B fix).

**Test surface:**
- New: `test_summarize_session_in_live_module` — direct import + smoke run.
- New: `test_variant_run_imports_live_summarize_session` — assert no per-archive copy exists in active variants.
- Update `test_lane_registry_lifecycle_wraps.py` if it asserts archive-script presence.

**Estimated cost:** ~150 LOC moved (no net change), ~50 LOC removed (bucket map), ~3-5 hours.

**Cross-cuts:** Unit 6 below depends on this for the dashboard digest. May surface dependencies on the per-archive shape that aren't visible until tested.

### Unit 4 — `regen_program_docs` reflects the variant's actual gate, not just the live registry

**Files:** `autoresearch/regen_program_docs.py`, `autoresearch/lane_registry.py`, the per-variant `workflows/session_eval_<lane>.py`.

The Phase 1 fix updated `STRUCTURAL_DOC_FACTS["geo"]` to enumerate v006's gates. But v006's `workflows/session_eval_geo.py` is the variant's copy — a future variant might add a 7th gate, and the live registry won't know. Make the autogen mechanism walk the variant's actual gate function:

1. Add a `structural_gate_doc_facts(domain) -> list[str]` callable to each variant's `workflows/session_eval_<lane>.py`. The function returns the rendered bullet list. Default implementation reads the gate function source via `inspect.getsource` + a small AST visitor to find `failures.append("...")` calls and pull the message string.

2. Update `regen_program_docs._build_block(domain)` to call the variant's `structural_gate_doc_facts(domain)` first, then fall back to `STRUCTURAL_DOC_FACTS[domain]` for backward compatibility.

3. Tighten the existing `test_structural_doc_facts.test_monitoring_registry_matches_assert_names` to apply to all five lanes, not just monitoring. Generalizes the drift detection.

After this, a meta-agent that mutates `session_eval_<lane>.py` and adds a new gate gets the new bullet in the AUTOGEN block on the next clone, automatically. The prompt and validator stay in sync without operator intervention.

**Test surface:**
- New: `test_geo_doc_facts_match_session_eval_geo` — extract bullets from `workflows/session_eval_geo.py` source via the AST visitor, assert they match the rendered AUTOGEN block.
- New: `test_competitive_doc_facts_match_session_eval_competitive` — same for competitive.
- Generalize `test_monitoring_registry_matches_assert_names` to each lane.

**Estimated cost:** ~50 LOC + 20 LOC tests, ~3-4 hours. The AST extraction is the most fiddly part.

**Cross-cuts:** Unit 6 below ties this to the operator dashboard.

### Unit 5 — Visibility cache `shape_flags` landed in fixture-refresh tooling

**Files:** `cli/freddy/fixture/sources.json`, the fixture-refresh tooling that consumes `arg_for_cache_key`, related tests.

Phase 1 added `shape_flags` to the runtime side of `cli/freddy/commands/visibility.py` so the agent's `--keywords` calls don't silently hit the brand-only cache. But the refresh side (`sources.json`) still keys on brand only, so the runtime path always misses cache when keywords are passed and falls through to live fetch.

The complete fix:

1. Extend the `arg_for_cache_key` schema in `cli/freddy/fixture/sources.json` to support `shape_flags`. The visibility entry becomes:
   ```json
   {
     "source": "freddy-visibility",
     "data_type": "visibility",
     "command": ["freddy", "visibility"],
     "args_template": [...],
     "arg_for_cache_key": {"from": "client"},
     "shape_flags_for_cache_key": [
       {"name": "keywords", "from": "env.AUTORESEARCH_VISIBILITY_KEYWORDS"},
       {"name": "country", "from": "env.AUTORESEARCH_GEO_COUNTRY", "default": "US"}
     ]
   }
   ```
2. Update the fixture-refresh tooling that builds the cache filename to include shape_flags.
3. Re-prime the existing visibility fixtures with their declared shape_flags.
4. Drop the Phase 1 interim guard in `visibility.py` once the refresh side is wired.

**Test surface:**
- New: `test_assemble_flag_visibility_uses_shape_flags` — refresh tooling reads shape_flags from sources.json and builds cache filename including them.
- New: `test_visibility_runtime_hits_shape_flagged_cache` — primed fixture with shape_flags=country=BR matches a `--country BR` invocation but not the default.
- Update the existing `test_assemble_flag_visibility_uses_client_as_brand` to assert shape_flags participate in the key.

**Estimated cost:** ~80 LOC + 60 LOC tests + fixture re-prime, ~4-6 hours.

**Cross-cuts:** the Phase 1 interim guard stays until this lands. Once Unit 5 ships, simplify `visibility.py` to use `shape_flags` unconditionally and delete the guard.

### Unit 6 — Operator dashboard surfaces `tool_error_rate`

**Files:** wherever the per-variant dashboard digest is rendered (likely `autoresearch/compute_metrics.py` or a downstream script that reads `metrics/<domain>.jsonl`).

Phase 1 added `tool_error_rate` to `metrics/<domain>.jsonl`. Make it visible in the operator's view. Specifically:

1. Surface `tool_error_rate` in any per-variant dashboard or report.
2. Add a 3-tier color/label scheme: `clean` (rate < 0.1), `degraded` (0.1–0.5), `unusable` (≥0.5).
3. When archive_index runs, surface the most recent `tool_error_rate` per fixture per variant so it appears next to score in the operator-facing table.

After this lands, the operator can spot a degraded run before reading `findings.md`. The H4 gate / multiplier work (option B/C from the investigation report) is a separate decision once empirical thresholds are established.

**Test surface:**
- New: `test_dashboard_renders_tool_error_rate` — variant with degraded fixtures shows the badge.
- New: `test_archive_index_includes_tool_error_rate` — index entry has the field.

**Estimated cost:** ~40 LOC + 30 LOC tests, ~2-3 hours. Depends on Unit 3.

**Cross-cuts:** Unit 3 (extracted summarize_session.py).

## Sequencing

Suggested order, smallest blast radius first:

1. **Unit 1** (sitemap SSRF) — small, no dependencies, ships immediately.
2. **Unit 2** (allowlist replacement) — small, depends only on a CI worker matrix.
3. **Unit 5** (visibility shape_flags) — small, contained to freddy CLI surface.
4. **Unit 4** (regen reflection) — medium, depends on having existing `STRUCTURAL_DOC_FACTS` to fall back to; after Phase 1, that exists.
5. **Unit 3** (summarize_session extraction) — medium, touches the most files but each touch is mechanical.
6. **Unit 6** (operator dashboard) — small, depends on Unit 3.

If sequenced this way, the risk profile descends linearly. Each unit can ship as its own commit on this branch; nothing forces a single PR. Recommend:

- Units 1+2+5 in one PR (small, mechanical, low risk).
- Unit 4 in its own PR (the AST extraction needs review).
- Units 3+6 in one PR (extraction + dashboard land together because Unit 6 depends on Unit 3).

Total: 3 PRs, ~16-22 hours of work, ~600 net deletion + ~250 net addition.

## Acceptance criteria

The plan is complete when all of the following hold:

1. v010 GEO run produces zero `invalid_url` errors on valid URLs even with `~/.codex/config.toml` missing `network_access` (because Unit 1 fixed the sitemap fail-closed).
2. The 80-prefix allowlist no longer exists; replaced by file-origin check (Unit 2).
3. `summarize_session.py` exists once in `autoresearch/scripts/`, not N times in archives (Unit 3).
4. Adding a new `failures.append(...)` to any `session_eval_<lane>.py` causes the next variant clone's AUTOGEN block to include it without operator intervention (Unit 4).
5. The visibility fixture for `nubank --keywords X --country BR` is keyed on `(brand, keywords, country)` triple (Unit 5).
6. Operator dashboard surfaces `tool_error_rate` as a first-class column (Unit 6).
7. `make test` (or the equivalent project test command) is green.

## Risks and mitigations

- **Per-variant `summarize_session.py` was load-bearing for some variant we don't know about.** Mitigation: Unit 3 keeps the per-archive copies during transition; only the active head variant points at the live module. After two evolution cycles with no regressions, delete the archive copies. (I.e., feature-flag the import via env var for the first 1-2 weeks.)
- **AST extraction in Unit 4 misses gate-function patterns we haven't seen yet.** Mitigation: keep `STRUCTURAL_DOC_FACTS` as a fallback. The reflection enriches; it doesn't replace. If the AST returns empty bullets, the registry's curated bullets still render.
- **Phase 1 already rebuilt the visibility cache key on the runtime side.** Unit 5 changes the refresh side. Risk: existing primed fixtures become stale (read-side keys don't match). Mitigation: schedule a `freddy fixture refresh` after Unit 5 lands; document the operator step in the unit's PR.
- **Removing the bucket map (Unit 3) might break downstream archive consumers.** Mitigation: grep for `iterations.productive` / `iterations.failed` consumers before deletion; preserve as a derived view if anything depends on the bucket integers. Most likely safe — the buckets are operator-facing, not gradient-facing.
- **CI matrix in Unit 2 needs Python 3.12/3.13/3.14 workers.** Mitigation: if only one Python version is in scope, the matrix test is overkill — the file-origin check alone is sufficient. Make the matrix optional.

## Why not bigger

Three temptations to resist:

1. **"Delete freddy CLI entirely; let the agent call APIs directly."** Rejected. Freddy mediates paid AI engine APIs (Cloro, DataForSEO, PageSpeed) — rate limits, cost caps, provider rotation. Removing it means re-engineering fixture provisioning. The investigation's H1 verdict was "partially true" precisely because freddy is value-add infrastructure, not a guard rail.
2. **"Per-claim provenance manifest (G3 from H5)."** Defer. It's the strongest fabrication guarantee but costs 2-3 weeks of design + implementation. Phase 1's autogen fix + Unit 4's reflection close most of the prompt-vs-validator drift without it; Phase 2 closes the rest. If empirical evidence shows fabrication is still slipping through, escalate to G3 in a separate plan.
3. **"Restructure the meta-agent's mutation surface."** Out of scope. The pattern of variants owning their own `workflows/` and `scripts/` is load-bearing — it's how meta-agents experiment. The plan keeps that surface intact and just makes the contracts visible across it.

## Status

- **Phase 1 (in scope of branch `fix/autoresearch-rigidity-phase-1`):** shipped on this worktree. Visibility cache-key guard, `tool_error_rate` metric, autogen STRUCTURAL block enumeration, sandbox-blocks-loopback warning. Awaits review.
- **Phase 2 (this plan):** described, not started. Recommended order in §Sequencing. Estimated 16-22 hours total; can land as 3 PRs.
