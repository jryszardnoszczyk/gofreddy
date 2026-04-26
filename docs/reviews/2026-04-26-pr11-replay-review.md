# Review — harness run-20260424-131621 (PR #11 replay)

Date: 2026-04-26
Reviewer: 5 parallel agents (correctness / maintainability / testing / api-contract / security) + synthesis
Source: PR #11 commits replayed as PR #21, then reverted from main as `1e10a3e`. Commits remain on `origin/harness/run-20260424-131621`.

## Bottom line

**Don't bulk-merge.** 5 P0 issues across the 23 fixes — three are arguably worse than the original defects. 6 P1 contract / docs issues. 7 of the 23 are clean keepers.

| Verdict | Count | What to do |
|---|---|---|
| **KEEP** | 7 | Cherry-pick to a fresh branch; ship as-is |
| **FIX-AND-KEEP** | 14 | Cherry-pick + apply listed fix before shipping |
| **DROP** | 0 | (none confirmed; some FIX-AND-KEEP could become DROP if you want to revert the underlying defect-introducing pattern) |
| **DEFER** | 2 | F-c-1-1 + F-c-3-2 — the PricingPage stack is product-decision-blocked (see §F-c-1-1) |

## Total accounting (33 actionable findings)

| Category | Count | Notes |
|---|---|---|
| Explicit fixer commits | 23 | Reviewed below |
| Cascade-resolved | 7 | Auto-fixed by 5 of the 23 — see cascade map |
| Harness-environment false positives | 2 | F-a-2-1, F-a-4-1 — verifier was hitting wrong backend; fixed by harness self-mod `a5a7dde` already on main |
| Manual fix already on main | 1 | F-a-3-1 → `f6a8b3e` (preserved through revert) |

## Cascade dependency map (matters for drop decisions)

| If you drop... | You also lose fixes for... |
|---|---|
| `6e47b38` F-b-1-3 | F-a-1-3, F-a-3-5, F-a-4-5 (4 total) |
| `7212efb` F-a-4-3 | F-a-3-3 (2 total) |
| `7eb6e0a` F-a-3-2 | F-a-4-2 (2 total) |
| `1203414` F-a-1-1 + `135b43b` F-a-4-4 | F-a-3-4 (3 total) |
| `ef25f8c` F-a-4-6 | F-a-3-6 (2 total) |

## P0 issues to fix before shipping any related commit

1. **F-b-2-2** dropped `max_length=512` on monitor keywords → unbounded payload DoS
2. **F-c-1-3** removed `loadCredits()` from mount effect → Credits card always empty
3. **F-b-1-1** existence check before access check on sessions → cross-org UUID enumeration
4. **F-c-4-1** left `frontend/src/lib/api.ts:307` reading `tier` field → frontend crashes on profile load
5. **F-a-1-1 + F-a-4-4** silent skip when `DATABASE_URL` unset → original disjoint-registry bug reproduces in prod CLI environments

---

# Per-fix review

## Track A — CLI fixes

### F-a-1-2 — `--human` flag silently ignored by `client` and `audit`
**Commit:** `194dce4` | **Diff:** +19/-11 | **Files:** `cli/freddy/commands/{audit,client}.py`

Defect: Top-level `--human` flag is silently ignored; these groups always emit JSON while peer groups honor it.

Reviewer findings: Maintainability flags 36 lazy `from ..main import get_state` call sites (pre-existing pattern, this fix amplified it). Testing: no new tests, but the change is mechanical (state lookup parameter).

**Verdict: KEEP** — clean fix.

### F-a-1-6 — `freddy visibility --brand X` without `--keywords` fails despite optional
**Commit:** `7b0f5d6` | **Diff:** +1/-1 | **Files:** `cli/freddy/commands/visibility.py`

Defect: CLI `--keywords` marked optional but body validator requires ≥1 item.

Reviewer findings: Correctness (low) — defaulting `keyword_list = [brand]` silently changes report semantics (single-keyword vs full saved-keyword list). User expecting "all my saved keywords" gets a one-keyword report.

**Verdict: KEEP** — defect is real; fallback is reasonable. Optional follow-up: surface the default in stdout (`default keyword: <brand>`) so callers know.

### F-a-2-2 — `freddy audit competitive` SecretStr crash
**Commit:** `c7513d9` | **Diff:** +5/-2 | **Files:** `cli/freddy/providers.py`

Defect: Foreplay/Adyntel providers typed `api_key: str` but received `SecretStr`; CLI buried `TypeError` under `foreplay_error`/`adyntel_error` with empty results.

Reviewer findings: None significant.

**Verdict: KEEP** — straightforward unwrap.

### F-a-3-2 — `freddy evaluate {review,critique,variant}` Bearer crash on unset token
**Commit:** `7eb6e0a` | **Diff:** +1/-1 | **Files:** `cli/freddy/commands/evaluate.py`

Defect: All three subcommands crashed with `Illegal header value b'Bearer '` when `SESSION_INVOKE_TOKEN`/`EVOLUTION_INVOKE_TOKEN` unset (the default). Cascade-provider for **F-a-4-2**.

Reviewer findings:
- **Security (low)**: when token unset, CLI now sends NO `Authorization` header → relies entirely on judge's strict 401 to fail closed. The crash was a useful fail-closed signal client-side.
- Testing: fixtures preset the env vars, so the regression is uncovered.

**Verdict: FIX-AND-KEEP**
- Required fix: in `evaluate.py`, add explicit `emit_error("missing_token", ...)` when `_session_token()` / `_evolution_token()` returns empty, before constructing the request. Fail closed in client.
- Required test: `test_review_with_unset_invoke_token_does_not_send_bearer` asserting non-zero exit before any HTTP call.

### F-a-4-3 — `freddy evaluate *` error shape inconsistency
**Commit:** `7212efb` | **Diff:** +29/-31 | **Files:** `cli/freddy/commands/evaluate.py`, `tests/test_cli_evaluate*.py`

Defect: `evaluate *` emitted `{"error": "<string>"}` while peer commands use `{"error": {"code", "message"}}`. Cascade-provider for **F-a-3-3**.

Reviewer findings:
- **API contract (medium)**: incomplete — `_handle_legacy_batch_critique` still emits old `{"error": "<str>", "body": "..."}` shape on lines 179, 193. Same command group, two error shapes.
- **Maintainability (high)**: `_post()` removed explicit `raise typer.Exit(1)` after each except branch on the implicit assumption `emit_error` raises. Today it does (`output.py:42` raises `SystemExit(1)`), but it's a fragile contract — UnboundLocalError risk if anyone weakens emit_error.
- Testing: weak — new assertions check `body['error']['code'] == 'judge_error'` but lose the body-suffix coverage.

**Verdict: FIX-AND-KEEP**
- Required fix: migrate the 2 `_handle_legacy_batch_critique` error sites to `emit_error("judge_unreachable"|"judge_error"|"invalid_json", ...)`.
- Recommended: type `emit_error` as `NoReturn` to formalize the contract.
- Required test: `test_review_judge_error_message_includes_response_body` covering the new `: {body}` suffix.

### F-a-4-6 — `freddy audit seo` hangs ~300s
**Commit:** `ef25f8c` | **Diff:** +49/-3 | **Files:** `cli/freddy/commands/audit.py`

Defect: SDK's `__getattr__` recursion caused 100% CPU thread; CLI hung. Replaced with direct `httpx` call. Cascade-provider for **F-a-3-6**.

Reviewer findings:
- **Correctness (low)**: missing `resp.raise_for_status()`. A DataForSEO 401/HTML error page bypasses the `>= 40000` checks and falls through to `result_data = {}` — CLI prints `{rank: null, backlinks_total: 0}` and exits 0, masking auth/network failures.
- **Maintainability (medium)**: `cli/freddy/providers.py:40-44` `get_provider("dataforseo")` factory branch + `DataForSeoProvider` class are now dead code (no callers). Inlined HTTP plumbing inside the CLI command.
- **Maintainability (low)**: defensive `if status_code and status_code >= 40000` redundant — `status_code` is always int.

**Verdict: FIX-AND-KEEP**
- Required fix: add `resp.raise_for_status()` (or explicit `if resp.status_code != 200` check) before `resp.json()`.
- Required cleanup: delete `get_provider("dataforseo")` branch + `DataForSeoProvider` class. Move inline httpx into a tiny `dataforseo` client module.
- Required test: `test_audit_seo_surfaces_dataforseo_status_code_error` covering 401/HTML response.

### F-a-4-9 — `freddy fixture {list,envs,staleness}` plain-text default
**Commit:** `a73d257` | **Diff:** +31/-19 | **Files:** `cli/freddy/commands/fixture.py`, test

Defect: Fixture group defaulted to text-table while every peer CLI group defaulted to JSON.

Reviewer findings:
- **API contract (medium)**: breaking — any shell pipeline `awk`-parsing column output will break. Field types also changed (`yes`/`no` → boolean; `✓`/`✗` → `{set: bool}`).

**Verdict: KEEP** — consistency with peer CLI groups is correct. Just note the breaking change in changelog.

### F-a-1-1 — `freddy session start --client X` rejects clients created by `client new`
**Commit:** `1203414` | **Diff:** +54/-0 | **Files:** `cli/freddy/commands/client.py`

Defect: `client new X` succeeded but `session start --client X` returned `client_not_found`. Cascade-provider (with F-a-4-4) for **F-a-3-4**.

Reviewer findings (shared with F-a-4-4 below):
- **Correctness (medium / P0 in synthesis)**: `_register_client_in_db` returns silently when `DATABASE_URL` is unset. Most prod CLI environments have no direct DB access; the original disjoint-registry symptom reproduces verbatim there.
- **Maintainability (medium)**: `_RegistrationFailed` exception used at exactly one call site — a 1-call-site abstraction.
- Testing: no `tests/test_cli_client*.py` exists; both branches uncovered.

**Verdict: FIX-AND-KEEP** (P0)
- Required fix: when `DATABASE_URL` is unset, POST the client to a backend `/v1/clients` endpoint instead of silently skipping. Layering: CLI shouldn't write directly to DB.
- Acceptable interim: hard-error with `emit_error("database_unavailable", ...)` until the backend endpoint exists.
- Required test: `test_client_new_does_not_skip_when_DATABASE_URL_unset` asserting non-zero exit + clear error.

### F-a-4-4 — `client new/list/log/report` and `session start --client` disjoint registries
**Commit:** `135b43b` | **Diff:** +42/-8 | **Files:** `cli/freddy/commands/client.py`

Same defect family as F-a-1-1. Cascade-provider (with F-a-1-1) for **F-a-3-4**.

**Verdict: FIX-AND-KEEP** — see F-a-1-1.

## Track B — API fixes

### F-b-1-1 — POST /v1/sessions unknown client_id 500 → 404
**Commit:** `2f1c2bf` | **Diff:** +10/-0 | **Files:** `src/api/routers/sessions.py`

Defect: Unknown valid-UUID client_id raised FK 500; should be 404 `client_not_found` matching the slug branch.

Reviewer findings:
- **Correctness (high / P0)**: existence check (`SELECT FROM clients WHERE id = $1`) runs BEFORE access-scope check (line 169). Unauthenticated/cross-org user can enumerate UUID existence by observing 404 (unknown) vs 403 (exists but not yours). Original 500 was uglier but didn't leak existence.
- **API contract (low)**: 404 body shape consistent with peer 404s in the same handler. ✓
- Testing: no test covering the 404 path; no test for cross-org UUID returning 403.

**Verdict: FIX-AND-KEEP** (P0)
- Required fix: run scope check first; only emit existence-revealing 404 if `accessible` is set and `target_client_id IN accessible`. Or unify in single SQL: `WHERE id = $1 AND id = ANY($2)`.
- Required test: `test_create_session_other_org_uuid_returns_403_not_404`.

### F-b-1-2 — GET /v1/evaluation/campaign/{campaign_id} non-UUID 200 → 422
**Commit:** `3e799e3` | **Diff:** +2/-2 | **Files:** `src/api/routers/evaluation.py`

Defect: Path param typed `str`; non-UUID returned 200 [] while every peer UUID path param returned 422.

Reviewer findings:
- **API contract (high)**: breaking — clients with placeholder/non-UUID who treated 200 [] as "no results" will now fail with 422. FastAPI's default 422 body shape doesn't match peer 404 envelope shape.
- Testing: existing test covered CLI request capture, not the API path validator.

**Verdict: FIX-AND-KEEP**
- Required fix: ship as-is for behavior, but add a custom validation_exception_handler so 422 body shape matches `{code, message}` peer pattern.
- Required test: `test_get_campaign_evaluations_rejects_non_uuid_with_422`.
- Required: changelog entry — breaking change.

### F-b-1-3 — Unknown monitor_id sub-routes inconsistent
**Commit:** `6e47b38` | **Diff:** +30/-0 | **Files:** `src/api/routers/monitoring.py`

Defect: `/mentions /alerts /runs /alerts/history` returned 200 with empty data while `/sentiment /share-of-voice /trends-correlation /digests /changelog` returned 404. Cascade-provider for **F-a-1-3, F-a-3-5, F-a-4-5**.

Reviewer findings:
- **API contract (high)**: breaking — frontend dashboard polling these endpoints + treating 200-empty as steady state will start logging errors / showing banners.
- **Correctness (medium)**: each new `service.get_monitor()` precheck doubles DB roundtrips and introduces a TOCTOU window (monitor deleted between precheck and main query → 200 with empty).
- **Maintainability (low)**: identical 7-line try/except pattern duplicated across 4 endpoints.
- Testing: no test asserting 404 for any of the 4 fixed endpoints.

**Verdict: FIX-AND-KEEP** (high cascade value — fixes 4 findings total)
- Required: changelog entry — breaking change.
- Recommended fix: FastAPI dependency `monitor = Depends(get_monitor_or_404)` — eliminates duplication and TOCTOU. 28 lines → ~6.
- Required test: 4× `test_<endpoint>_unknown_monitor_returns_404`.

### F-b-2-1 — POST /v1/geo/audit DB CHECK violation
**Commit:** `c5418e9` | **Diff:** +8/-8 | **Files:** `src/geo/orchestrator.py`, test

Defect: Orchestrator wrote `status='running'` violating DB CHECK constraint. Fix changes enum values: `'running'→'processing'`, `'failed'→'error'`.

Reviewer findings:
- **API contract (medium)**: breaking — any consumer of `audits.status` switching on literal `'running'`/`'failed'` silently misses new values. No DB migration for in-flight rows. No frontend/dashboard audit.
- Residual risk: tests assert new enum on the ORM side, not the CHECK constraint itself.

**Verdict: FIX-AND-KEEP**
- Required: cross-codebase grep for old strings (`'running'`, `'failed'` in geo context) — frontend status badges, SQL reports, fixtures.
- Required: DB migration backfill — `UPDATE audits SET status='processing' WHERE status='running'; UPDATE ... SET status='error' WHERE status='failed'` (or accept that any pre-existing rows show as unknown statuses in UI).
- Required: changelog entry.

### F-b-2-2 — POST /v1/monitors keywords schema (str → list[str] | str)
**Commit:** `59016a8` | **Diff:** +35/-8 | **Files:** `src/api/routers/monitoring.py`, `src/api/schemas_monitoring.py`

Defect: POST schema required `keywords: str` (comma-split server-side) while GET responses returned `list[str]`. Round-trip required type coercion.

Reviewer findings:
- **Security (medium / P0)**: dropped `max_length=512`. New shape has NO bound on list length, NO per-item length, NO total-bytes ceiling. Authenticated user can POST `keywords: ["a"*5_000_000]*1000` — accepted, normalized, persisted.
- **Correctness (medium)**: also no `min_length` — POST `keywords: ""` or `keywords: []` both pass validation; downstream code assuming ≥1 keyword silently produces zero matches.
- **Maintainability (medium)**: polymorphic `list[str] | str` is permanent ambiguity in public schema. OpenAPI now documents two valid shapes for one field.

**Verdict: FIX-AND-KEEP** (P0)
- Required fix: re-add bounds — `Field(..., max_length=50)` on the list, `max_length=100` per item via validator, and `if not value: raise ValueError("at least one keyword required")` in `_normalize_keywords`.
- Optional cleanup: drop the polymorphism — make it `list[str]` only and update CLI/frontend to send a list. Cleaner long-term.
- Required test: `test_create_monitor_rejects_empty_keywords`, `test_create_monitor_rejects_oversized_keywords`.

### F-b-3-1 — Admin short-circuit returns 'admin' for any slug
**Commit:** `b720199` | **Diff:** +5/-1 | **Files:** `src/api/membership.py`

Defect: `resolve_client_access` returned `role='admin'` for ANY slug including non-existent ones; `/v1/portal/<bogus-slug>/summary` returned 200 for admin users.

Reviewer findings:
- **Security (residual)**: portal returns 403 `no_membership` uniformly for both nonexistent and unauthorized slugs (no existence-disclosure side channel). ✓
- **Testing (high)**: only existing admin test creates a real slug; no test exercises the actual bug (admin getting 'admin' on a bogus slug). Future refactor can revert silently.
- **API contract (medium)**: breaking for any internal admin tooling using ad-hoc slugs.

**Verdict: FIX-AND-KEEP**
- Required test: `test_admin_returns_none_for_nonexistent_slug` asserting `resolve_client_access(pool, user_id, 'ghost-slug-never-inserted')` returns `None`.
- Required test: `test_portal_admin_bogus_slug_returns_403` (integration).
- Required: changelog entry — security hardening.

### F-b-4-1 — POST /v1/geo/audit 500 → 400 for invalid URL
**Commit:** `73ebfaf` | **Diff:** +11/-0 | **Files:** `src/api/routers/geo.py`

Defect: Returned HTTP 500 for URLs the security policy rejects; peer `/v1/geo/detect` and `/v1/geo/scrape` correctly returned 400.

Reviewer findings:
- **Security (residual)**: error message is generic ("URL validation failed") and doesn't leak which rule failed. ✓
- Testing: `grep` returned 0 hits for `invalid_url` or `/v1/geo/audit` in tests — uncovered.

**Verdict: FIX-AND-KEEP**
- Required test: `test_run_audit_rejects_invalid_url_with_400` parameterized with the same URLs `/v1/geo/detect` rejects (parity proof).

## Track C — Frontend fixes

### F-c-1-1 — Pricing route + page (not wired in main.tsx)
**Commit:** `bd843bf` | **Diff:** +33/-1 | **Files:** `frontend/src/main.tsx`, `frontend/src/pages/PricingPage.tsx` (new)

Defect: SettingsPage + TierRequiredBanner linked to `ROUTES.pricing` but no `/pricing` route was wired.

Reviewer findings:
- **Maintainability (low)**: PricingPage is a 31-line placeholder ("Plan details are coming soon. Contact support to upgrade your tier."). Combined with F-c-4-1's hardcoded `canUseProFeatures: false`, the upstream "Upgrade to Pro" CTA is dead UX. Route exists only to satisfy the reverse direction of a feature that doesn't exist.

**Verdict: DEFER** — product decision required.
- Option A: keep — accept "coming soon" placeholder until Pro features ship.
- Option B: remove the upstream "Upgrade to Pro" CTAs in SettingsPage + TierRequiredBanner first; then this commit + F-c-3-2 + PricingPage all become dead and droppable.
- If A: ship as-is (KEEP). If B: drop this, drop F-c-3-2, delete PricingPage.

### F-c-1-2 — SettingsPage preferences card 404 → remove
**Commit:** `ba041eb` | **Diff:** +4/-146 | **Files:** `frontend/src/lib/api.ts`, `frontend/src/pages/SettingsPage.tsx`

Defect: `getPreferences` called `GET /v1/preferences` (404); model-picker card permanently showed "Failed to load preferences". Fix removes the call + the entire card.

Reviewer findings: None of significance.

**Verdict: KEEP** — clean removal of dead UI; the backend never served `/v1/preferences`.

### F-c-1-3 — SettingsPage credits card 404 handling
**Commit:** `dcb8058` | **Diff:** +6/-0 | **Files:** `frontend/src/pages/SettingsPage.tsx`

Defect: `loadCredits` treated 404 from `/v1/billing/summary` as "billing not enabled" instead of user-facing error.

Reviewer findings:
- **Correctness (high / P0)**: cycle-3 sibling commit `7a5441f` (F-c-3-1) removed `void loadCredits()` from the mount effect entirely. `creditBalance` now only populates when user returns from a Stripe checkout (`?checkout=success`). Every other page mount, the Credits card is permanently empty even when backend supports billing — silent regression of the cycle-1 design.

**Verdict: FIX-AND-KEEP** (P0) — note: bug is in the cycle-3 *sibling* `7a5441f`, not directly in `dcb8058`.
- Required fix: in `7a5441f`, restore `void loadCredits()` in the mount effect; add a `silent: true` parameter to `loadCredits` if the goal is no console.error noise on 404.
- Required test (frontend baseline): mount SettingsPage with a billing-enabled fixture; assert Credits card populates without a Stripe redirect.

### F-c-1-4 — SettingsPage billing topups checkout 404
**Commit:** `1cb5bf8` | **Diff:** +0/-60 | **Files:** `frontend/src/lib/api.ts`, `frontend/src/pages/SettingsPage.tsx`

Defect: `handleBuyCredits → createTopupCheckout` called `POST /v1/billing/topups/checkout` (404); every pack's Buy button broken. Fix removes the buy buttons + helper.

Reviewer findings: None.

**Verdict: KEEP** — clean removal of dead-on-arrival CTAs.

### F-c-3-1 — Settings billing/summary console.error on every mount
**Commit:** `7a5441f` | **Diff:** +1/-2 | **Files:** `frontend/src/pages/SettingsPage.tsx`

Defect: Cycle-1 fix `dcb8058` hid the user-visible AlertBanner but left the failing fetch in place; console.error spammed on every mount.

Reviewer findings: **Same P0 as F-c-1-3** — removing `void loadCredits()` from mount effect kills the cycle-1 design.

**Verdict: FIX-AND-KEEP** (P0) — see F-c-1-3 fix.

### F-c-3-2 — Pricing route still missing in main.tsx (cycle 3)
**Commit:** `0ab3b95` | **Diff:** +1/-0 | **Files:** `frontend/src/main.tsx`

Defect: Cycle-1 finding F-c-1-1 remained unfixed in cycle-3 staging HEAD.

**Verdict: DEFER** — product decision tied to F-c-1-1.

### F-c-4-1 — Frontend AuthMeResponse type mismatch
**Commit:** `712d0af` | **Diff:** +18/-94 | **Files:** `frontend/src/components/AuthProvider.tsx`, `frontend/src/lib/generated/types.gen.ts`, `frontend/src/pages/SettingsPage.tsx`

Defect: Backend `/v1/auth/me` returns `{user_id, email, role, client_slugs}`; frontend `AuthMeResponse` expected `{user_id, email, org_id, role, subscription_status, tier: string (required)}`. Admin user saw "Current tier: Unknown" / "Starter workspace access".

Reviewer findings:
- **Correctness (high / P0)**: `canUseProFeatures: false` now hardcoded for ALL users including admins. Future Pro-gated UI ships disabled.
- **API contract (high / P0)**: `frontend/src/lib/api.ts:307` runtime guard still reads `value.tier !== 'string'` — will throw on the new payload. `hasProAccess` / `tier.ts` / `TierRequiredBanner` / `formatTierLabel` still in codebase reading a `tier` the API no longer returns.
- **Maintainability (medium)**: `tier: null, subscriptionStatus: null, canUseProFeatures: false` is unreachable-by-design state — the type pretends values can vary but they can't.

**Verdict: FIX-AND-KEEP** (P0)
- Required fix 1: update `frontend/src/lib/api.ts:307` runtime guard to match new shape (drop `tier` check; require `client_slugs: string[]`).
- Required fix 2: remove `tier`/`subscriptionStatus`/`canUseProFeatures` from `AuthContextValue` and from every consumer (`PricingPage`, `TierRequiredBanner`, `SettingsPage` "Current tier" line).
- Required: changelog entry — breaking external API consumers of `/v1/auth/me`.

---

# Cascade-resolved findings (7) — fixed transitively

These have no commits but the verifier confirmed defect gone via earlier commits. **All depend on commits in the table above being kept.**

| ID | Defect | Resolved by | If you keep |
|---|---|---|---|
| F-a-1-3 | search-mentions monitor_not_found inconsistency | `6e47b38` (F-b-1-3) | ✓ |
| F-a-3-3 | duplicate of F-a-4-3 | `7212efb` (F-a-4-3) | ✓ |
| F-a-3-4 | client/session registry mismatch (cycle 3 re-find) | `1203414`+`135b43b` (F-a-1-1+F-a-4-4) | ✓ |
| F-a-3-5 | monitor mentions/sentiment/sov 404 inconsistency (cycle 3 re-find) | `6e47b38` (F-b-1-3) | ✓ |
| F-a-3-6 | `freddy audit seo` hang (cycle 3 re-find) | `ef25f8c` (F-a-4-6) | ✓ |
| F-a-4-2 | duplicate of F-a-3-2 (cycle 4 re-find) | `7eb6e0a` (F-a-3-2) | ✓ |
| F-a-4-5 | monitor mentions cycle-4 re-find | `6e47b38` (F-b-1-3) | ✓ |

---

# Harness-environment false positives (2) — drop

| ID | Why false positive |
|---|---|
| F-a-2-1 | Verifier's "failed" verdict was due to subprocess hitting wrong backend port (operator's :8000 instead of worker's :8002). Fixed by harness self-mod `a5a7dde` (FREDDY_API_URL inject) — already on main. No product defect. |
| F-a-4-1 | Same root cause as F-a-2-1. Already resolved by `a5a7dde`. |

---

# Already on main (1) — preserved

| ID | Commit | Notes |
|---|---|---|
| F-a-3-1 | `f6a8b3e` | Manual fix (geo router status code mapping). Shipped from JR's other Claude Code session, preserved through PR #21 revert. Verifier marked the harness's automated attempt "failed" — manual fix superseded it. |

---

# Decision template

Copy this into your reply with `K`/`F`/`D`/`?` per row, then I'll cherry-pick + apply fixes accordingly:

```
F-a-1-2  KEEP             [ ]
F-a-1-6  KEEP             [ ]
F-a-2-2  KEEP             [ ]
F-a-3-2  FIX-AND-KEEP     [ ]
F-a-4-3  FIX-AND-KEEP     [ ]
F-a-4-6  FIX-AND-KEEP     [ ]
F-a-4-9  KEEP             [ ]
F-a-1-1  FIX-AND-KEEP P0  [ ]
F-a-4-4  FIX-AND-KEEP P0  [ ] (paired with F-a-1-1)
F-b-1-1  FIX-AND-KEEP P0  [ ]
F-b-1-2  FIX-AND-KEEP     [ ]
F-b-1-3  FIX-AND-KEEP     [ ] (cascade-provider for 3 findings)
F-b-2-1  FIX-AND-KEEP     [ ]
F-b-2-2  FIX-AND-KEEP P0  [ ]
F-b-3-1  FIX-AND-KEEP     [ ]
F-b-4-1  FIX-AND-KEEP     [ ]
F-c-1-1  DEFER            [ ] (product decision: keep PricingPage shim or kill upstream CTAs)
F-c-1-2  KEEP             [ ]
F-c-1-3  FIX-AND-KEEP P0  [ ] (paired with F-c-3-1)
F-c-1-4  KEEP             [ ]
F-c-3-1  FIX-AND-KEEP P0  [ ] (paired with F-c-1-3)
F-c-3-2  DEFER            [ ] (paired with F-c-1-1)
F-c-4-1  FIX-AND-KEEP P0  [ ]
```

After your decisions land, the workflow:
1. New branch off current main (`harness-pr11-curated`)
2. Cherry-pick approved commits
3. Apply required fixes per FIX-AND-KEEP entries (each as a follow-up commit on top, attributed to me, not the harness)
4. Add the required regression tests
5. Run full test suite
6. Open PR with link to this review doc
7. You squash-merge after a final glance
