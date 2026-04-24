---
title: Bundle 0 status + Bundle A handoff
date: 2026-04-24
status: active
source_plans:
  - docs/plans/2026-04-23-003-agency-integration-plan.md § 3 (Bundle 0)
  - docs/plans/2026-04-24-003-audit-engine-implementation-design.md § 4 (Bundle A)
purpose: Single source of truth for Bundle A execution. Records Bundle 0 shipment, corrects design §4's "22 new files" with what's already on feat/fixture-infrastructure, gives executor a de-duplicated work list.
---

# Bundle 0 status + Bundle A handoff

## Bundle 0 — status: substantially shipped

Verified 2026-04-24 by running `pytest --collect-only` against the current working tree.

| Item (bulk plan §3) | Status | Evidence |
|---|---|---|
| §3.1 orphaned tests handled | ✅ Done | `tests/conftest.py` uses `collect_ignore` list (~45 files, grouped by bundle) |
| §3.2 root `tests/conftest.py` exists | ✅ Done | 96 lines; docstring explains scope = "tell pytest which files to skip"; shared fixtures live in per-directory conftests |
| §3.3 `mistune>=3.0.0` | ✅ Present | `pyproject.toml` |
| §3.3 `weasyprint>=62.0` | ✅ Present | `pyproject.toml` |
| §3.3 `nh3>=0.2.14` | ✅ Present | `pyproject.toml` |
| §3.3 `jinja2>=3.1.0` | ✅ Present | `pyproject.toml` |
| §3.3 `resend>=2.0,<3.0` | ❌ Missing | Only Bundle 0 gap. Resend is Bundle 3 digest delivery — defer until Bundle 3 starts |
| §3.4 `db` pytest marker | ✅ Defined | `pyproject.toml [tool.pytest.ini_options] markers` |
| §3.5 done: collect-only zero errors | ✅ Passes | 2,187 tests, 0 errors |
| §3.5 done: `-m "not db"` runs | ✅ Passes | 2,147 tests collected, 40 db-marked deselected |

Shipped via commit `b46c731` (`fix(tests): pre-flight — restore honest CI (0 collection errors)`).

**Implementation diff from plan:** conftest uses `collect_ignore` (pytest-native) instead of per-file `pytestmark = pytest.mark.xfail`. Same outcome, simpler mechanism.

**Outstanding (non-blocking):**
- Add `resend>=2.0,<3.0` to `[project.dependencies]` when Bundle 3 starts — not urgent since Bundle 3 is deferred per agency-integration plan.

**No Bundle 0 work needed before Bundle A.**

## Bundle A — execution handoff

### Source

`docs/plans/2026-04-24-003-audit-engine-implementation-design.md` §4 (lines 266–543). Locked decisions in §2. Module map in §3. File list in §12.

### Dependencies

None. Bundle A builds from `harness/` + `autoresearch/` primitives (borrow patterns, no imports). Does not depend on port Bundles 1, 2, or 3 of the agency-integration plan — those are independent agency-ops work.

### Goal

Every primitive the stages (Bundle B) will rely on. No audit logic yet; foundation only.

Done signal:
- `freddy audit run --client fixture --domain example.com --preflight-only` prints clean pass/fail matrix
- State file writes atomically; concurrent writes from two test threads don't corrupt
- SIGTERM to running audit sets `graceful_stop_requested`; process exits 0 within 5s
- Events file rotates at 100 MB; flock prevents concurrent-writer corruption

### What's already shipped on `feat/fixture-infrastructure`

Verified 2026-04-24 by `git ls-tree -r origin/feat/fixture-infrastructure -- src/audit/`. The v1-scaffold commits (`251f31d`, `d546160`, `19fbd76`, `60cf919`, `e0556c6`, `087b6eb`, `0a9df0b`) that PR #8 reverted from `main` are **still on feat** and formed a partial foundation. Bundle A completes that foundation rather than starting from scratch.

Also shipped this session (commits `357afb5`, `e763d5f` on `origin/feat/fixture-infrastructure`):
- Design doc `2026-04-24-003`
- Superseded notice on `2026-04-23-003`
- Research record `2026-04-24-001` (cherry-picked from `fix/priming-agent`)

**Already present — leave alone or extend in place:**
```
src/audit/__init__.py                            # module docstring, 11 lines
src/audit/checkpointing.py                       # write_atomic helper (lower layer for state.py)
src/audit/agent_models.py                        # Pydantic: SubSignal / ParentFinding / Judgment
src/audit/preflight/__init__.py
src/audit/preflight/runner.py                    # 136-line orchestrator scaffold — needs audit_preflight-level context wrapping
src/audit/preflight/checks/__init__.py
src/audit/preflight/checks/dns.py                # 128 lines, real dnspython resolver — functional
src/audit/preflight/checks/wellknown.py          # 154 lines — functional
src/audit/preflight/checks/assets.py             # 43 lines, stub returning {"implemented": False}
src/audit/preflight/checks/badges.py             # 31 lines, stub
src/audit/preflight/checks/headers.py            # 29 lines, stub
src/audit/preflight/checks/schema.py             # 25 lines, stub (= design's json_ld)
src/audit/preflight/checks/social.py             # 34 lines, stub
src/audit/preflight/checks/tooling.py            # 43 lines, stub
tests/audit/__init__.py
tests/audit/test_agent_models.py
tests/audit/test_checkpointing.py
```

**Naming reconciliation:** the existing preflight check filenames differ from design §4. We keep the shorter existing names (no rename) and update the design's references as a follow-up.

| Existing (keep) | Design §4 name (drop) |
|---|---|
| `checks/dns.py` | `dns_email_security.py` |
| `checks/wellknown.py` | `well_known.py` |
| `checks/schema.py` | `json_ld.py` |
| `checks/badges.py` | `trust_badges.py` |
| `checks/headers.py` | `security_headers.py` |
| `checks/social.py` | `social_meta.py` |
| `checks/assets.py` | `brand_assets.py` |
| `checks/tooling.py` | `tooling_fingerprint.py` |

The design's `preflight/audit_preflight.py` orchestrator is already landed as `preflight/runner.py` (same function). Keep `runner.py`.

### Files to create (11 new + 4 tests)

```
src/audit/state.py                    # AuditState Pydantic model wrapping checkpointing.py (port harness/sessions.py:56-102)
src/audit/sessions.py                 # SessionsFile per-role session_id tracking (port harness/sessions.py)
src/audit/cost_ledger.py              # per-call max_budget + per-stage soft warn + total hard breaker (NET-NEW primitive, research §4 gap #1)
src/audit/graceful_stop.py            # atomic flag + SIGTERM handler (port harness/run.py:344-350)
src/audit/agent_runner.py             # ClaudeSDKClient wrapper: cost capture, session persist, tenacity retries, fallback_model
src/audit/resume.py                   # _viable_resume_id + skip-completed-lenses (port harness/run.py:78-101)
src/audit/cleanup.py                  # atexit + SIGTERM handlers w/ signal.alarm(5) cap (port harness/worktree.py:236-254)
src/audit/events.py                   # per-audit events.jsonl + optional global append (port autoresearch/events.py)
src/audit/prompts_loader.py           # loads stage prompts from autoresearch/archive/current_runtime/programs/marketing_audit/prompts/
src/audit/concurrency.py              # evolve_lock + active_run lock primitives
src/audit/exceptions.py               # CostBreakerExceeded, RateLimitHit, EngineExhausted, WalltimeExceeded, CostCeilingReached, ViableResumeFailed, MalformedSubSignalError
```

### Files to retrofit with network I/O (6 stub check modules)

Extend `assets.py`, `badges.py`, `headers.py`, `schema.py`, `social.py`, `tooling.py` with real HTTP fetch + parse. Pattern already established in `dns.py` and `wellknown.py`. Not greenfield — read the existing docstrings + _SIGNAL_SHAPE declarations before writing.

### Tests to add

```
tests/audit/test_state.py             # atomic persist, concurrent safety
tests/audit/test_cost_ledger.py       # soft warn, hard breaker, scan mode
tests/audit/test_graceful_stop.py     # flag propagation on SIGTERM
tests/audit/test_resume.py            # viable_resume_id + skip-completed
```

Existing `test_agent_models.py` + `test_checkpointing.py` stay; don't duplicate.

### Locked decisions relevant to Bundle A

From design §2:
- #1 asyncio + Semaphore(7) for Stage 2 (relevant to agent_runner contract)
- #2 per-lens checkpoint granularity (relevant to state.py schema)
- #3 no worktree per audit (simpler cleanup)
- #4 single-worker per audit in v1 (active_run lock per slug; simpler concurrency)
- #5 SDK (Claude) for all agent roles; `max_budget_usd` per role
- #9 `evolve_lock` mutex (relevant to concurrency.py)

### Open JR decisions (§11) — NOT blockers for Bundle A

None of these block Bundle A. They become blockers at later bundles:
1. Lens YAML transcription → blocks Bundle B
2. Free-scan subdomain `audits.gofreddy.com` → blocks Bundle C
3. Capability registry content → blocks Bundle B
4. R2 + Cloudflare Worker creds → blocks Bundle C
5. Resend API key → only if manual-invoice-via-email in Bundle C
6. Autoresearch pin commit → blocks Bundle E

### Out of scope for Bundle A

- Stage logic (Bundle B)
- Render + publish (Bundle C)
- MA-1..MA-8 evaluation (Bundle D)
- Lane registration + evolve_lock enforcement (Bundle E)
- Lens YAML transcription
- CLI `audit.py` (lives in Bundle C file list)

### How to execute

Option A — sequentially in this session (post-compaction):
1. Read design doc §2, §3, §4, §12 (this doc links them).
2. Create files per §12 Bundle A list in order.
3. Port patterns from `harness/sessions.py`, `harness/run.py:78-101`, `harness/run.py:344-350`, `harness/worktree.py:236-254`, `harness/preflight.py:40-280`, `autoresearch/events.py`.
4. Write tests per design §12 test coverage targets.
5. Run `freddy audit run --preflight-only` against fixture to hit done signal.

Option B — dispatch to a coding sub-agent:
- Brief: "Execute Bundle A per docs/plans/2026-04-24-003 §4 + §12. Handoff context in docs/plans/2026-04-24-004. Start with state.py + sessions.py + exceptions.py since others depend on them."
- Verify after: commit should add exactly the files in §12 Bundle A, tests pass, done signal met.

### Handoff invariants

- `src/audit/` has partial content already — see "What's already shipped" above. Extend in place, don't rewrite.
- Do not touch `src/` modules outside `src/audit/`. Bundle A is `src/audit/` only.
- Do not transcribe lenses.yaml in Bundle A — that's Bundle B (§3.5 of design).
- Do not wire `autoresearch/` lane — that's Bundle E.
- Commit per-subsystem rather than one monolithic commit; easier to review. Cadence:
  1. **Core state + exceptions** — `state.py` + `exceptions.py` + `test_state.py`. Everything else imports from these.
  2. **Cost + safety** — `cost_ledger.py` + `graceful_stop.py` + `test_cost_ledger.py` + `test_graceful_stop.py`.
  3. **Sessions + agent wrapper** — `sessions.py` + `agent_runner.py`.
  4. **Preflight retrofit** — 6 stub check modules get real network I/O. Follow `dns.py` / `wellknown.py` pattern.
  5. **Lifecycle** — `events.py` + `cleanup.py` + `resume.py` + `test_resume.py`.
  6. **Prompts + concurrency** — `prompts_loader.py` + `concurrency.py`.
  7. **Verify done signal** — `freddy audit run --preflight-only` against fixture domain.

## Related artifacts on disk

- `docs/plans/2026-04-24-002-port-only-extraction-checklist.md` — preparation notes for a port-only doc (no longer needed; bulk plan §6+§7 are superseded, rest is port content)
- `docs/plans/2026-04-24-001-audit-pipeline-research-record.md` — authoritative for primitives being borrowed (harness + autoresearch)
- Memory: `project-audit-engine-design-state.md` — tracks design doc status
