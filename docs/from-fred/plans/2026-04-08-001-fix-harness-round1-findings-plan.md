---
date: 2026-04-08
status: active
type: fix
topic: harness-round1-findings
related:
  - docs/brainstorms/2026-04-08-harness-tier2-gotchas-fixpack-requirements.md
supersedes: (v1 of this file, rewritten after critical self-review)
---

# Fix Plan — Harness Round 1 Findings (trimmed)

## Problem Frame

Today's Phase 1 validation run (`PHASE=1 MAX_CYCLES=1`, attempts 1a/1b/1c) validated the **B-1 single-shot fix** (commit `82f948c`) and the **A-1 passthrough fix** (commits `29bc050` + `02351f9`). Final grade: pass=3, partial=3, fail=0, blocked=0. Zero product regressions.

Along the way the run surfaced 15 secondary issues. A first-draft plan tried to fix all of them and was over-engineered — parsers where description tweaks would do, managed subprocess lifecycles where smoke tests would do, 40-line prompt rubrics where 3 sentences would do, redundant belt-and-suspenders, and one premature implementation that got obsoleted by a single `claude --help` check (streaming logs → `--output-format stream-json` flag).

This is v2: a **sharp, minimum-viable plan**. Nine fixes. Every one directly prevents something that bit us today. Nothing speculative. Nothing deferred — the dropped items are either redundant (solved by another fix in this plan) or not worth the risk they'd introduce.

The acceptance target: a clean Round 2 run (`PHASE=1 MAX_CYCLES=3`) where the operator boots backend + supabase + vite per `harness/README.md`, runs one command, walks away, and inspects the scorecard. No `kill`-the-fixer. No false-positive PARTIALs. No cost-recorder log spam. No cross-run state leakage. No "logs are empty, is it even running?" moments.

## The nine fixes

Ordered by blast radius (smallest → largest) so early commits are easy to verify in isolation.

### Fix 1 — P2: Add `provider_cost_log` table to setup_test_db.sql

**Why**: Backend log today was 95% noise from `cost_record_failed` stack traces. Every Gemini call hits `UndefinedTableError` because the test schema is missing this production table. Made debugging A-1 painful.

**Change**: Append to `scripts/setup_test_db.sql` (after the existing cost/usage section — grep for `usage_periods` or `billable_events` to find the right spot):

```sql
CREATE TABLE IF NOT EXISTS provider_cost_log (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    operation TEXT NOT NULL,
    cost_usd DOUBLE PRECISION,
    tokens_in INT,
    tokens_out INT,
    model TEXT,
    metadata JSONB,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_provider_cost_log_created_at ON provider_cost_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_provider_cost_log_op_created ON provider_cost_log (operation, created_at DESC);
```

Column list verified against `src/common/cost_recorder.py:20-24` (`_INSERT_SQL`). If the production migration has extra columns (e.g. `org_id`), the test schema can diverge — this is a TEST schema, not production. Match columns used by code, nothing more.

**Verification**: `grep cost_record_failed /tmp/freddy-backend.log` returns zero hits after backend restart.

**Files**: `scripts/setup_test_db.sql` (+15 lines).

---

### Fix 2 — T2: Fix C-12 pass criteria (message count → action count)

**Why**: Test matrix says sessions cards must show "message count". The data model field is `action_count` (`src/sessions/models.py:27`, `repository.py:70`). The UI correctly displays "actions". The test is wrong, not the product.

**Change**: In `harness/test-matrix.md` C-12 row, replace `message count` with `action count`.

**Verification**: Round 2 C-12 grades PASS without any product code change.

**Files**: `harness/test-matrix.md` (1 line).

---

### Fix 3 — T1: Relax A-1 pass criteria (don't demand thumbnails)

**Why**: A-1 prompt is *"Search for TikTok cooking videos"*. `search` has no tiktok backend, so the model correctly falls back to twitter/instagram/reddit (all text platforms) and tells the user TikTok is unavailable. That's **correct behavior**, but the pass criteria demand *"video cards (thumbnail, title, platform icon)"* — unachievable because the fallback is text posts, which have no video thumbnails by definition.

Round 1c captured this plainly: *"Agent communicated the platform limitation in plaintext (honest affordance)"* — and still graded PARTIAL because of the thumbnail requirement.

**Current row** (verified at `harness/test-matrix.md:26`, single markdown table row):
```
| A1 | "Search for TikTok cooking videos" | `search` | `search` | 60s | Search results render with video cards (thumbnail, title, platform icon). At least 1 result. No console errors. |
```

**Change**: In `harness/test-matrix.md:26`, replace ONLY the last cell (the pass-criteria cell). Prompt, expected tool, expected section, and timeout all stay unchanged:
```
| A1 | "Search for TikTok cooking videos" | `search` | `search` | 60s | Agent calls `search` and the search canvas section renders with at least 1 result. If the requested platform is unavailable, the agent must explain the limitation in chat text and suggest an alternative (e.g. `discover_creators` for TikTok). No console errors. |
```

Keep the prompt — the prompt correctly tests the affordance path fixed in commit `02351f9`. The pass criteria were simply demanding something the tool cannot provide when TikTok is requested.

**Verification**: Round 2 A-1 grades PASS. The agent behavior doesn't change; only what we grade against changes.

**Files**: `harness/test-matrix.md` (1 row replaced — single line).

---

### Fix 4 — H2: `EVAL_ONLY=true` gate around the fixer

**Why**: `MAX_CYCLES=1` runs eval→fix→exit, NOT eval→exit. For validation runs where we want pure evaluator signal (no fixer changing source code mid-session), there's no clean way to skip the fixer. I had to `kill` it three times this session.

**Change 1** — `harness/config.sh`, near the other gate controls:
```bash
EVAL_ONLY="${EVAL_ONLY:-false}"   # true = skip fixer, exit after evaluator cycle
```

**Change 2** — `scripts/eval_fix_harness.sh`, wrap lines 1712-1727 (the fixer block in the cycle loop):
```bash
if [ "${EVAL_ONLY:-false}" = "true" ]; then
    ok "EVAL_ONLY=true — skipping fixer. Cycle $cycle complete."
    EXIT_REASON="eval-only"
    break
fi
# ... existing fixer + backend restart block ...
```

**Verification**:
- `EVAL_ONLY=true PHASE=1 MAX_CYCLES=1 ./scripts/eval_fix_harness.sh` runs all evaluators, writes scorecards, exits with `EXIT_REASON=eval-only`. `ps aux | grep claude` returns zero fixer processes.
- Default `EVAL_ONLY=false` behaves exactly as today (no change for operators not setting it).

**Files**: `harness/config.sh` (+1 line), `scripts/eval_fix_harness.sh` (+5 lines).

---

### Fix 5 — H5: Stream evaluator logs via `claude --output-format stream-json`

**Why**: `eval-N-track-X.log` files are 0 bytes during a 3-minute track and only get flushed at the end. Impossible to see live progress or catch a hung track early. **Cause**: Claude CLI uses block buffering when stdout is redirected to a file.

**Found**: `claude --help` documents `--output-format stream-json` for "realtime streaming" in `--print` mode, and `--include-partial-messages` for partial-message chunks. Two flags total, no PTY wrapper, no portability shim.

**Change** — `scripts/eval_fix_harness.sh`, both `run_evaluator_claude` (line 970) and `run_fixer_claude` (line 1124):
```bash
# Add --output-format stream-json to the existing claude invocation
claude -p "$(cat "$prompt_file")" \
    --output-format stream-json \
    --include-partial-messages \
    $session_flag \
    --model "$EVAL_MODEL" \
    --allowedTools "$EVAL_ALLOWED_TOOLS" \
    --dangerously-skip-permissions \
    --max-turns "$MAX_TURNS_EVAL" \
    > "$logfile" 2>&1
```

**Subtle concern**: `claude_log_has_transient_api_error` at line 804 and `claude_log_has_resume_failure` at line 809 grep the log for specific strings (`API Error: 5`, `overloaded`, `session not found`). In stream-json mode these strings should still appear (as JSON values inside `{"type":"error","message":"..."}`) so grep still matches — but this needs to be verified BEFORE running a real evaluator track, not after. See the local pre-test in verification below.

**Verification** (in order — do steps 1-2 BEFORE running the harness):
1. **Local shape check** (no API spend): `claude -p "say hi" --output-format stream-json --include-partial-messages > /tmp/claude-stream-shape.json 2>&1` → inspect with `head /tmp/claude-stream-shape.json` to see whether claude emits one JSON object per line (newline-delimited) or pretty-printed across multiple lines. Newline-delimited is what `tail -f` and grep need.
2. **Parser sanity check**: construct a fake error log line and verify both parsers still match. E.g.:
   ```bash
   echo '{"type":"error","message":"API Error: 529 overloaded"}' | grep -q "API Error: 5\|API Error: 429\|overloaded\|Internal server error" && echo "transient parser OK"
   echo '{"type":"error","message":"session abc not found"}' | grep -qi "session.*not found\|invalid session\|no session" && echo "resume parser OK"
   ```
   If either fails, the fix is updating the grep patterns (e.g., `grep '"message":".*API Error: 5'`) BEFORE the harness runs against real claude.
3. `tail -f harness/runs/<ts>/eval-1-track-a.log` during a Round 2 run: shows line-by-line JSON events streaming, not a 3-minute silence.
4. `head -3 harness/runs/<ts>/eval-1-track-a.log` after a run: shows valid JSON events with `type` field.

**Files**: `scripts/eval_fix_harness.sh` (+2 lines in each of two functions).

---

### Fix 6 — H1a: Frontend bypass smoke test

**Why**: Round 1a wasted ~$1 of API credits because I booted vite with `VITE_E2E_BYPASS_ACCESS_TOKEN` set but `VITE_E2E_BYPASS_AUTH=1` missing. The harness's existing `check_stack_health` pings `http://127.0.0.1:3010` and gets HTTP 200 (vite is up), so it proceeds — but the bypass is inert and every evaluator track hits `/login` and grades BLOCKED.

This fix does **not** make the harness boot vite itself. That adds subprocess lifecycle complexity (cleanup traps, PID tracking, orphan process risk). Instead it adds a 5-second preflight check that fails loudly with a clear error when the operator's vite is misconfigured.

**Change 1** — new function in `scripts/eval_fix_harness.sh`, placed near `check_stack_health` (line 258):

```bash
# Verify the operator's frontend has the E2E auth bypass wired correctly.
# Without this check, misconfigured vite (missing VITE_E2E_BYPASS_AUTH=1) wastes
# an entire evaluator cycle on redirected-to-login BLOCKED findings.
verify_frontend_bypass() {
    local port_num
    port_num=$(echo "$FRONTEND_URL" | sed -E 's|.*://[^:]+:([0-9]+).*|\1|')
    local vite_pid
    vite_pid=$(lsof -ti "tcp:${port_num}" -sTCP:LISTEN 2>/dev/null | head -1)
    if [ -z "$vite_pid" ]; then
        fail "No process listening on ${FRONTEND_URL} (port ${port_num})"
        fail "Boot vite per harness/README.md before running the harness."
        return 1
    fi

    # Dump the vite process environment. macOS: ps -E; Linux: /proc/PID/environ.
    local env_dump
    if [ "$(uname -s)" = "Darwin" ]; then
        env_dump=$(ps -E -p "$vite_pid" -o command= 2>/dev/null | tr ' ' '\n')
    else
        env_dump=$(tr '\0' '\n' < "/proc/${vite_pid}/environ" 2>/dev/null)
    fi

    local required=(VITE_E2E_BYPASS_AUTH VITE_E2E_BYPASS_ACCESS_TOKEN VITE_E2E_BYPASS_USER_ID VITE_E2E_BYPASS_EMAIL)
    local missing=()
    for var in "${required[@]}"; do
        if ! printf '%s\n' "$env_dump" | grep -q "^${var}="; then
            missing+=("$var")
        fi
    done
    if [ "${#missing[@]}" -gt 0 ]; then
        fail "Vite (pid ${vite_pid}) is missing required E2E bypass env vars:"
        printf '    - %s\n' "${missing[@]}" >&2
        fail "Restart vite with all VITE_E2E_BYPASS_* vars set — see harness/README.md:80-95."
        return 1
    fi

    # Backend smoke test: hit a Pro-gated endpoint with the harness token.
    # This catches stale tokens, JWT-secret mismatches, and Pro-tier regressions.
    local backend_status
    backend_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $HARNESS_TOKEN" \
        "${BACKEND_URL}/v1/monitors")
    if [ "$backend_status" != "200" ]; then
        fail "Backend smoke test failed: GET ${BACKEND_URL}/v1/monitors with harness token returned $backend_status (expected 200)"
        fail "Check: (a) harness token is valid (b) backend is reading the correct JWT secret (c) Pro-tier user exists in the DB."
        return 1
    fi

    ok "Frontend bypass verified (vite pid ${vite_pid}); backend /v1/monitors smoke-test OK"
}
```

**Change 2** — call it from `main()` after the seed step (needs `HARNESS_TOKEN`). Insert after the existing "Pro test user seeded" log line:
```bash
log "Verifying frontend E2E bypass wiring..."
verify_frontend_bypass || exit 1
```

**Verification**:
- Boot vite WITHOUT `VITE_E2E_BYPASS_AUTH=1` → harness exits within 5 seconds with a clear missing-vars list.
- Boot vite correctly → smoke test passes and the run proceeds as today.
- Stop vite entirely → fails with "no process listening on port".

**Not doing**: the harness does not boot vite itself. Operator still runs `npm run dev` manually per README. H1a is preflight-only.

**Files**: `scripts/eval_fix_harness.sh` (+50 lines).

---

### Fix 7 — H4: Schema auto-apply (unconditional, idempotent)

**Why**: `scripts/setup_test_db.sql` is idempotent (`CREATE TABLE IF NOT EXISTS` everywhere) but the harness doesn't run it. A fresh `supabase start` gives you a database with auth tables but no freddy tables, and the first harness run fails with cryptic foreign-key errors. I hit this today when I had to manually `psql -f` the schema.

**Change** — new function in `scripts/eval_fix_harness.sh`, called from `main()` AFTER `RUN_DIR` is created (so the function can write to it) but BEFORE `check_stack_health` (since the backend depends on the schema being present):

```bash
ensure_db_schema() {
    # Match the seed step's URL fallback chain (main() line ~1552). Operator may
    # have set E2E_DB_URL only, DATABASE_URL only, or neither (default to local).
    local db_url="${E2E_DB_URL:-${DATABASE_URL:-postgresql://postgres:postgres@127.0.0.1:54522/postgres}}"
    if ! command -v psql >/dev/null 2>&1; then
        fail "psql not found in PATH. Install PostgreSQL client tools:"
        fail "  macOS:  brew install postgresql@17"
        fail "  Linux:  apt-get install postgresql-client"
        return 1
    fi
    local schema_file="$REPO_ROOT/scripts/setup_test_db.sql"
    log "Applying schema from $(basename "$schema_file") (idempotent)..."
    # RUN_DIR is set by main() before this function is called — see call site.
    local apply_log="$RUN_DIR/.schema-apply.log"
    if ! psql "$db_url" -v ON_ERROR_STOP=1 -f "$schema_file" > "$apply_log" 2>&1; then
        fail "Schema apply failed. See $apply_log"
        tail -20 "$apply_log" >&2
        return 1
    fi
    ok "Schema applied"
}
```

Key choices:
- **Unconditional apply on every run**: the script is idempotent. No marker-table probe, no `HARNESS_FORCE_SCHEMA_APPLY` flag. Simpler = fewer code paths.
- **`-v ON_ERROR_STOP=1`**: psql aborts on the first real error instead of continuing past it. The existing NOTICE spam about "relation already exists" is not an error (it's a NOTICE), so this flag doesn't suppress the idempotent path — it only catches real errors.
- **Log redirect to `.schema-apply.log`**: the NOTICE spam is dumped to a file instead of polluting the harness console. On failure, `tail -20` shows the last lines.
- **Require psql in PATH**: no binary auto-discovery. Operators install the standard client.

**Call site** in `main()` — must come AFTER `RUN_DIR` is created (the function writes its log there) and BEFORE `check_stack_health` (the backend's `/ready` endpoint queries tables that need to exist):
```bash
validate_safety_guards || exit 1
validate_engine_prereqs || exit 1
validate_env_vars || exit 1

RUN_TS="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$REPO_ROOT/harness/runs/$RUN_TS"
mkdir -p "$RUN_DIR"

ensure_db_schema || exit 1     # ← NEW (after RUN_DIR exists)

initialize_session_ids
# ... existing log lines, then check_stack_health ...
```

**Verification**:
- `supabase stop && supabase start && ./scripts/eval_fix_harness.sh` → harness applies schema, proceeds. No manual `psql` needed.
- Second run in a row: schema reapplied silently (idempotent), `apply_log` contains NOTICE lines but no errors, harness continues.
- `PATH="" ./scripts/eval_fix_harness.sh` → fails fast with "psql not found".
- Break the schema file temporarily (add `SELECT 1/0;` at the top) → harness aborts with the actual psql error in the tail.

**Files**: `scripts/eval_fix_harness.sh` (+30 lines).

---

### Fix 8 — H3: Minimal DB cleanup between runs (two tables)

**Why**: Round 1b's monitor leaked into round 1c's database. The monitoring page showed "Monitors: 2" because there were genuinely 2 rows — one per run. The evaluator interpreted this as a B-1 double-call bug and graded PARTIAL. False positive, real confusion.

The full brainstorm had me listing 9 tables in FK-delete order. That's brittle — any new table with a `user_id` FK becomes a silent leakage risk the moment it's added. Instead: start narrow. Clean the two tables that demonstrably caused trouble today (`monitors` and `conversations`). Let FK cascades handle children. Add more tables to the cleanup list if (and only if) a future run proves a new leakage source.

**Change 1** — new function in `scripts/eval_fix_harness.sh`, called from `main()` after the seed step (needs `harness_user_id`):

```bash
# Narrow per-run state cleanup. Only tables that demonstrably caused cross-run
# confusion in round 1 (monitors, conversations). Expand this list if a future
# run produces a false-positive finding traceable to leftover state from a
# prior run — do NOT preemptively add tables "just in case".
cleanup_harness_state() {
    if [ "${HARNESS_KEEP_STATE:-false}" = "true" ]; then
        log "HARNESS_KEEP_STATE=true — skipping state cleanup"
        return 0
    fi
    # Replicate the seed step's URL fallback chain so this function works
    # whether the operator set DATABASE_URL, E2E_DB_URL, or neither (defaults
    # to local supabase). Must match the resolution in main() at line ~1552.
    local db_url="${E2E_DB_URL:-${DATABASE_URL:-postgresql://postgres:postgres@127.0.0.1:54522/postgres}}"
    # harness_user_id is the JSON key emitted by scripts/e2e_seed_auth_tokens.py
    # at line 189 (verified). It's the UUID of the seeded Pro test user row.
    local user_id
    user_id=$(printf '%s' "$seed_output" | "$venv_python" -c \
        "import sys,json; print(json.load(sys.stdin).get('harness_user_id',''))" 2>/dev/null)
    if [ -z "$user_id" ]; then
        warn "Could not parse harness_user_id from seed output — skipping state cleanup"
        return 0
    fi
    log "Cleaning harness state for user $user_id (monitors + conversations)..."
    if ! psql "$db_url" -v ON_ERROR_STOP=1 -c "
        DELETE FROM monitors WHERE user_id = '$user_id';
        DELETE FROM conversations WHERE user_id = '$user_id';
    " > "$RUN_DIR/.cleanup.log" 2>&1; then
        warn "State cleanup failed — see $RUN_DIR/.cleanup.log"
        tail -10 "$RUN_DIR/.cleanup.log" >&2
        # Don't fail the run — cleanup is best-effort. Evaluator will see stale
        # state and the operator can triage.
        return 0
    fi
    ok "Harness state cleaned"
}
```

**Change 2** — `harness/config.sh`:
```bash
HARNESS_KEEP_STATE="${HARNESS_KEEP_STATE:-false}"   # true = skip per-run DB cleanup (useful for manual triage)
```

**Call site** in `main()`, after `verify_frontend_bypass`:
```bash
log "Verifying frontend E2E bypass wiring..."
verify_frontend_bypass || exit 1
cleanup_harness_state    # ← NEW
```

**Safety notes**:
- The existing `validate_safety_guards` already refuses non-localhost `DATABASE_URL`. The DELETE can only touch a local test database.
- Cleanup is **best-effort** (doesn't abort the run on failure). If a schema change breaks the DELETE, the operator sees a warning but the run proceeds.
- SQL uses literal interpolation of `$user_id`. This is safe because `harness_user_id` is a UUID generated by the seed script (not user-supplied), but out of caution the plan uses `-v ON_ERROR_STOP=1` to catch any malformed value immediately.

**Verification**:
- Run twice back-to-back: second run's B-1 shows exactly 1 monitor on the page, not 2.
- `HARNESS_KEEP_STATE=true ./scripts/eval_fix_harness.sh` → skips cleanup, preserves state for triage.
- Manually `INSERT INTO monitors (user_id, name, ...) VALUES ('<wrong_user>', ...)` before a run → the cleanup does NOT touch that row (scoped to harness user only).

**Files**: `scripts/eval_fix_harness.sh` (+25 lines), `harness/config.sh` (+1 line).

---

### Fix 9 — E1: Evaluator rubric — short bullet about multi-call patterns

**Why**: The same B-1 retry pattern was graded PASS in round 1b and PARTIAL in round 1c by different evaluator sessions. The source of the non-determinism: the existing `harness/prompts/evaluator-base.md:199` CRITICAL rule (*"When in doubt between PASS and PARTIAL, choose PARTIAL. If you notice something wrong, DO NOT rationalize it away"*) biases the evaluator to flag any unusual telemetry — including legitimate retry-on-validation-error.

The first-draft plan proposed a 40-line rubric with a 4-category taxonomy (retry-on-error / progressive refinement / duplicate-success / thrash) and a Python recipe for querying `conversation_messages`. That's over-engineered: round 1b's evaluator already graded this correctly without any rule at all. A gentle 3-sentence clarification gives the evaluator permission to interpret multi-calls sensibly without forcing it through a new procedural framework.

**Change** — add to `harness/prompts/evaluator-base.md` as a new bullet inside the existing "Grading Rules (STRICT)" section, BEFORE the CRITICAL rules at line 199:

```markdown
- **Multi-call patterns**: when the same tool is invoked more than once in a
  single assistant turn, grade based on whether the user's request was
  fulfilled by the final state, NOT the number of calls. Retrying after a
  validation error (e.g. tool rejected the first call with "missing parameter",
  the second call succeeded) is normal behavior and should not be down-graded.
  Progressive refinement (the model narrows a query across multiple calls, each
  informed by the previous result) is also normal. Only grade down if the final
  state is wrong or if identical successful calls produced duplicate persisted
  rows.
```

No DB query recipe, no taxonomy, no Bash one-liner for postgres. The evaluator has Bash access and can choose to dig deeper on its own if it wants confirmation; the rule tells it WHAT to grade on, not HOW to investigate.

**Will this fully eliminate non-determinism?** No — LLM evaluators have inherent variance. The rule reduces the width of the variance and eliminates the specific round 1b vs 1c failure mode. Full determinism would require mechanical grading of a fixture suite, which is out of scope.

**Verification** (single, realistic):
- Round 2's B-1 grades PASS. The retry pattern will still occur (we're not doing P1) so this is the test of whether the rubric closes the loophole. If Round 2 also grades B-1 PARTIAL with the same "double-call" reasoning, the rubric needs to be sharper — not the product code.
- (Stretch, not required to ship the fix): once a fixture-based evaluator-replay rig exists, replay round 1c's B-1 evidence through it 3+ times and check that grades converge. No such rig exists today; this is a future hardening, not a Fix 9 acceptance criterion.

**Files**: `harness/prompts/evaluator-base.md` (+8 lines).

---

## What I dropped and why (honest)

Every item below was in the first draft of this plan. Each was dropped for a specific, checkable reason.

| Dropped | Reason |
|---|---|
| **P1 (manage_monitor keywords/boolean_query auto-derive)** | The model already retries correctly and creates exactly one monitor per request. "Wasted tool call" is ~$0.005 per create — not material. The PARTIAL grade it caused is fixed by Fix 9 (rubric) without touching product code. The proposed regex parser (`r'"([^"]+)"'`) was fragile (missed unquoted terms, hashtags, nested parens) and had real risk of creating monitors with wrong keywords. Not worth it. |
| **P3 (cost_recorder self-disable on missing table)** | Pure redundancy with Fix 1 (P2). Once the table exists, there's nothing to self-disable. P3 was "what if someone runs without the table" — we are not that someone. |
| **H1b (managed vite subprocess lifecycle)** | The subprocess management (nohup + PID file + cleanup trap + signal handling in bash) is a bug farm. The failure modes (orphan processes, killing the wrong PID, trap not firing on SIGKILL, vite's child process vs npm's parent process) are worse than the problem it solves. Fix 6 (H1a smoke test) catches the specific round 1a failure mode in 5 seconds with 50 lines of bash. Managed vite added 80 more lines for marginal convenience. |
| **T3 (rubric rule: cross-run leakage → BLOCKED)** | Subsumed by Fix 8 (H3). If state is clean every run, the evaluator never encounters leakage to misinterpret. No new rubric rule needed. |
| **H6 (skip seed when HARNESS_TOKEN already set)** | Already deferred in the first draft. Stays dropped. Marginal optimization; doesn't fix anything that bit us. |

## Implementation order

Each fix is independent and can land as its own commit. Recommended order (smallest blast radius first, so any problem is easy to isolate):

1. **Fix 1 — P2**: schema add. Pure SQL addition. Cannot break anything.
2. **Fix 2 — T2**: one-line markdown. Cannot break anything.
3. **Fix 3 — T1**: ~3 line markdown. Cannot break anything.
4. **Fix 4 — H2**: `EVAL_ONLY` gate. Opt-in env var with safe default. Cannot break existing runs.
5. **Fix 5 — H5**: add `--output-format stream-json` flag to two claude invocations. Might need parser adjustments (see verification); minor risk.
6. **Fix 6 — H1a**: `verify_frontend_bypass` function + call site. New preflight step — adds one failure mode (clean error), can't make success worse.
7. **Fix 7 — H4**: `ensure_db_schema` function + call site. Adds `psql` as a required tool; unconditional idempotent apply.
8. **Fix 8 — H3**: `cleanup_harness_state` function + call site + `HARNESS_KEEP_STATE` env var. Narrow (two tables). Best-effort.
9. **Fix 9 — E1**: evaluator prompt addition (8 lines).

All 9 can land in a single work session. Estimated total churn: ~150 lines added across 5 files, 0 lines deleted.

## Round 2 acceptance gate

After all 9 fixes are committed, run **Round 2**: `PHASE=1 MAX_CYCLES=3 ./scripts/eval_fix_harness.sh`. Operator pre-boots Supabase + backend + vite per README (with the full VITE_E2E_BYPASS_* env vars). Operator does not apply the schema manually. Operator does not clean the DB manually.

**Expected pass conditions:**
1. Harness applies schema automatically (Fix 7).
2. Preflight `verify_frontend_bypass` passes (Fix 6).
3. Per-run state cleanup runs (Fix 8), leaving the harness user with 0 monitors / 0 conversations at cycle start.
4. Cycle 1 evaluator logs stream line-by-line to `eval-1-track-X.log` during the run (Fix 5). `tail -f` shows live progress.
5. Backend log (`/tmp/freddy-backend.log`) has zero `cost_record_failed` lines (Fix 1).
6. Scorecard results: pass=5-6, partial=0-1, fail=0, blocked=0.
   - **B-1 grades PASS** (Fix 9 rubric closes the round 1c loophole).
   - **A-1 grades PASS** (Fix 3 relaxed pass criteria).
   - **C-12 grades PASS** (Fix 2 corrected test data).
7. If any cycle 1 finding is FAIL or PARTIAL, the fixer runs in cycle 2 and the harness either converges or hits MAX_CYCLES=3.

**Negative tests** (run separately to prove the safety nets):
- Boot vite without `VITE_E2E_BYPASS_AUTH=1` → harness exits within 5s with a clear error (Fix 6).
- Run `EVAL_ONLY=true PHASE=1 MAX_CYCLES=1 ./scripts/eval_fix_harness.sh` → evaluators run, fixer does NOT run (Fix 4).
- Run twice back-to-back (no `HARNESS_KEEP_STATE`) → second run starts with 0 monitors in the harness user (Fix 8).
- `supabase stop && supabase start && ./scripts/eval_fix_harness.sh` → schema auto-applies, run proceeds (Fix 7).

### If Round 2 doesn't pass cleanly

The harness has nine new safeguards; one or more might still fail in production. Triage flow:

1. **Harness aborts during preflight** (safety guards, env vars, schema apply, frontend smoke test): the failure message points at the specific check. Fix the environment per the error and retry. Do NOT touch code yet — preflight is supposed to fail loudly and early.
2. **Cycle 1 grades a finding FAIL or PARTIAL that wasn't anticipated**:
   - Read the scorecard's `Detailed Findings` section. The evaluator should now be quoting actual `conversation_messages.metadata` reasoning (Fix 9 effect) rather than DOM-only impressions.
   - Check whether the finding describes a NEW product behavior vs reuses one of the round 1 misinterpretations (B-1 double-call, A-1 retry-after-known-limit). If the latter, **the rubric isn't sharp enough yet** — Fix 9 needs another iteration, not the product code.
   - If it's a genuine new product bug, let the cycle 2 fixer attempt it. The MAX_FIX_ATTEMPTS=2 cap (already in the harness) prevents thrashing.
3. **Cycle 1 evaluator grades everything BLOCKED**: the auth bypass smoke test passed but real evaluator traffic is failing. Likely cause: the JWT expired between seed and first eval (>1h elapsed), or vite restarted mid-run. Re-mint the token, restart vite, retry.
4. **Backend log floods with NEW noise** (not `cost_record_failed`): Fix 1 only addressed the known `provider_cost_log` source. Other missing-table errors would require either adding more tables to `setup_test_db.sql` or extending Fix 3 (cost_recorder's resilience pattern) to other recorders. Triage on a per-error basis.
5. **Eval logs are still empty during the run**: Fix 5's `--output-format stream-json` flag didn't take effect. Check that the flag actually landed in both `run_evaluator_claude` AND `run_fixer_claude` (the flag must be added in two places). If both are correct, run the local pre-test from Fix 5's verification steps to confirm claude itself streams correctly.
6. **State cleanup fails with FK error**: Fix 8 starts narrow (monitors + conversations). If Round 2 surfaces a NEW table that accumulates state and confuses the evaluator, add it to the cleanup list — but only after confirming it actually caused a finding, not preemptively.

The plan is **not** to keep iterating on this fixpack until Round 2 is perfect. If Round 2 surfaces 1-2 small issues, fix them in place. If it surfaces 5+ new issues, stop, write a Round 3 fixpack plan, and repeat the brainstorm→plan→commit→run loop. Don't let this fixpack grow into v3 by accretion.

## Risks (honest)

| Risk | Probability | Mitigation |
|---|---|---|
| Fix 5 log parsers (`claude_log_has_transient_api_error`) break because stream-json wraps error strings in JSON | Medium | Verify by inspection on first run. If broken, one-line fix to the grep patterns. Bounded exposure. |
| Fix 6 `lsof -ti tcp:$port` syntax differs across lsof versions | Low | Tested on macOS today in this session. If it breaks on Linux, fallback to `ss -ltnp` or `netstat -ltnp`. |
| Fix 6 `ps -E` (macOS) / `/proc/pid/environ` (Linux) requires read permission on the target process | Low | The operator owns both the harness and the vite process → same uid → no permission issue. |
| Fix 7 `ON_ERROR_STOP=1` flags a new real error in a CI environment that was previously silent | Low | Desired behavior. If it happens, fix the schema. |
| Fix 8 hits a new FK we didn't anticipate (e.g. a future table with `monitor_id` that lacks `ON DELETE CASCADE`) | Medium | Cleanup is best-effort; failure warns but doesn't abort. Operator notices, adds the table to the cleanup list. |
| Fix 9 rubric rule is misapplied by the evaluator (grades REAL duplicate-success bugs as PASS) | Low | The rule explicitly says *"only grade down if the final state is wrong or identical successful calls produced duplicate persisted rows"* — which is exactly the duplicate-success case. Evaluator has to correctly identify whether calls were identical/successful, which is what it's already supposed to do. |
| `HARNESS_KEEP_STATE=true` becomes an operator foot-gun that gets left on between runs | Low | Env var with safe default (`false`). Warn line in cleanup function reminds operator when it's set. |

## Files touched

| File | Changes |
|---|---|
| `scripts/setup_test_db.sql` | Append `provider_cost_log` table (+15 lines) |
| `harness/test-matrix.md` | A-1 pass criteria (~3 lines), C-12 pass criteria (1 line) |
| `scripts/eval_fix_harness.sh` | New functions: `verify_frontend_bypass`, `ensure_db_schema`, `cleanup_harness_state`. `EVAL_ONLY` gate in cycle loop. `--output-format stream-json --include-partial-messages` flags on both claude invocations. Call sites in `main()`. (~110 lines added) |
| `harness/config.sh` | `EVAL_ONLY`, `HARNESS_KEEP_STATE` declarations (+2 lines) |
| `harness/prompts/evaluator-base.md` | Multi-call patterns bullet (+8 lines) |

**Total**: ~140 lines added across 5 files. Zero product code changes.

## Open question (single, must resolve during implementation)

**Q**: Do `claude_log_has_transient_api_error` and `claude_log_has_resume_failure` still match correctly when the log is JSON-formatted (Fix 5)?

**Resolution plan**: After Fix 5 lands, run one real harness cycle. Inspect `head harness/runs/<ts>/eval-1-track-a.log` to see the JSON structure claude emits. Verify both parser functions still fire on real errors — if not, adjust the grep patterns to match JSON field shapes. This is a 5-minute verification step during Phase 5, not a risk to the rest of the plan.

## Next step

Land Fix 1 (P2) as the first commit. Validate schema apply locally (`psql -f scripts/setup_test_db.sql`). Then proceed sequentially through Fixes 2-9. After Fix 9, run Round 2.
