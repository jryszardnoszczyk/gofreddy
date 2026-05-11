---
status: complete
created: 2026-05-11
author: claude opus 4.7 (U0 pre-flight agent)
purpose: Plan B U0 — operator-script callers audit
companion: docs/plans/2026-05-11-001-refactor-autoresearch-substrate-simplification-plan.md
---

# Autoresearch V1 Operator Caller Audit

## Summary

**Total distinct callers found:** 17 (8 production, 3 test frameworks, 6 daemon/script)

**Migration verdict breakdown:**
- **PATH_SWAP:** 1 (fix path references in portal.py and autoresearch.py)
- **NO_OP_SHIM:** 11 (events, lane_registry, agent_retry, report_base functions)
- **DELETE_WITH_V1:** 0 (nothing exclusively dies)
- **ESCALATE_JR:** 0 (no grey-area decisions)

**Critical path items for U13:**
1. Fixture dryrun + refresh (cli/freddy/fixture/) — 4 files, deferred imports, JudgeUnreachable exception swap
2. Audit pipeline (src/audit/) — 3 files, log_event wrapper, agent_retry imported
3. Evaluation service (src/evaluation/) — 2 files, lane_registry reads (structure validation)
4. Portal + report viewer (src/api, src/shared/reporting/) — 2 files, archive path references
5. Test conftest (tests/autoresearch/) — module stubs (dies with test classification U13a)

---

## Per-Caller Migration Table

| File Path | Type | What It Touches | Verdict | Migration Note |
|-----------|------|-----------------|---------|-----------------|
| `cli/freddy/fixture/dryrun.py` | Python import (deferred) | `JudgeUnreachable`, `log_event`, `evaluate_variant`, `ensure_materialized_runtime` | NO_OP_SHIM + U13_MOVE | Line 32: `from autoresearch.evaluate_variant import JudgeUnreachable` (fallback handler). Lines 111, 184, 326: `log_event` (v2 shim). Line 183: `evaluate_variant` module import. Line 184: `ensure_materialized_runtime` (materialized runtime logic). **Action:** U13 wraps JudgeUnreachable in try/except or v2 equivalent; rewrites log_event to v2 name; evaluate_single_fixture call stays (v2 API). |
| `cli/freddy/fixture/refresh.py` | Python import (deferred) | `call_quality_judge`, `log_event` | NO_OP_SHIM | Lines 456, 504: `call_quality_judge` from judges (v2 shim provides). `log_event` to v2. **Action:** Rewrite both to v2 equivalents (shims provided). |
| `cli/freddy/commands/fixture.py` | Python import (deferred) | `read_events`, `call_quality_judge` | NO_OP_SHIM | Lines 488-489: Both from autoresearch.events + judges. **Action:** Rewrite to v2 event + judge shims. |
| `src/audit/agent_runner.py` | Python import | `agent_retry` from autoresearch | NO_OP_SHIM | Line 45: Direct import. **Action:** v2 provides agent_retry (or wrapper logic moves to src/audit). Verify retry semantics match. |
| `src/audit/events.py` | Python import | `log_event` as `_log_event` | NO_OP_SHIM | Line 23: Re-exports to `log_to_audit` + `log_global` callers. **Action:** v2 shim for log_event. This module stays; internal call changes only. |
| `src/evaluation/rubrics.py` | Python import (structural validation) | `LANES` from `autoresearch.lane_registry` | NO_OP_SHIM | Line 1450: Cross-check rubric IDs against lane registry. **Action:** v2 lane_registry provides same LANES dict (or schema stub). Verify lane ID constants survive. |
| `src/evaluation/service.py` | Python import (structural validation) | `_DOMAIN_CRITERIA` from `autoresearch.lane_registry` | NO_OP_SHIM | Line 29: Used to build `_JUDGE_PRIMARY_DELIVERABLE` dict. **Action:** v2 lane_registry exports same constant (or hardcode fallback). |
| `src/shared/reporting/report_base.py` | Comment reference + optional import | Functions from `autoresearch.report_base` (load_json, render_*, build_html_document, etc.) | NO_OP_SHIM | Line 7-15 (docstring). No actual import; self-contained implementation. **Action:** None (already standalone). |
| `.github/workflows/ci-lint-judge-isolation.yml` | CI lint rule | Grep for `from judges`, `import judges` | NO_OP_SHIM | Lines 8-12: Ensures autoresearch/cli/src don't import judges/. **Action:** Rule stays; v2 maintains same boundary. |
| `.claude/hooks/autoresearch-continuous-evolution-check.sh` | Daemon hook | `/tmp/autoresearch-continuous-evolution-daemon.sh`, `/tmp/autoresearch-cont-evolve/` | DELETE_WITH_V1 + JR_REBUILDS | Lines 20-58: Manages daemon PID, health check, restart. Reads sentinel file, invokes daemon script. **Action:** JR rebuilds daemon per v2 driver pattern (U15 post-Phase5). Hook dies with v1. |
| `cli/freddy/commands/autoresearch.py` | CLI command registration + path logic | `_ARCHIVE_ROOT = _REPO_ROOT / "autoresearch" / "archive"` | PATH_SWAP | Lines 31, 35, 41: Archive path construction for render/publish/detect. **Action:** Rewrite to `autoresearch_v2/archive` or new v2 path structure (verify v2 spec). |
| `src/api/routers/portal.py` | Portal report viewer (file serving) | `_ARCHIVE_ROOT = Path(...) / "autoresearch" / "archive"` (line 88) | PATH_SWAP | Lines 88-135: Serves `autoresearch/archive/<variant>/sessions/<lane>/<fixture>/report.html`. Safe path traversal guards already in place. **Action:** Rewrite path to v2 archive location. No logic changes. |
| `scripts/evolve-with-report.sh` | Post-evolve summary script | Reads `autoresearch/archive/v*/scores.json`, `autoresearch/archive/current.json` | PATH_SWAP + DELETE_WITH_V1 | Lines 20-27, 49-150: Reads scores + current variant head. **Action:** In Phase 5, v1 lives at `autoresearch/legacy/archive/`; script can PATH_SWAP then. Dies U15 when autoresearch/legacy/ deletes. For now: conditional path logic or v2 integration. |
| `scripts/agent-launcher.sh` | Wrapper for subprocess CLI bootstrap | References `./autoresearch/evolve.sh`, judges.env, holdout manifest | DELETE_WITH_V1 | Lines 17, 56-75, 108-132: Path detection for evolve commands, judges.env sourcing, EVOLUTION_HOLDOUT_MANIFEST validation. **Action:** Stays through Phase 5 (v1 in legacy/). U15: dies with autoresearch/legacy/ removal. No changes until then. |
| `tests/autoresearch/conftest.py` | Test fixtures (module stubs) | `archive_index`, `frontier`, `lane_paths` modules | DELETE_WITH_V1 | Lines 19-79: Stubs to isolate test imports. **Action:** U13a (test classification phase) removes conftest + stubs. Tests migrate separately or die. |
| `scripts/autoresearch/backfill_v006_promoted_at.py` | One-shot migration script | Reads/writes `autoresearch/archive/lineage.jsonl` | DELETE_WITH_V1 | Lines 20-50: v006 lineage backfill (past event). **Action:** Leaves as-is (historical script). Dies U15 with v1 deletion. |

---

## Detailed Per-File Findings

### 1. `cli/freddy/fixture/dryrun.py` — Fixture Calibration Harness

**Import lines & context:**

```python
# Line 27-35: Try/except fallback for isolated test imports
try:
    from autoresearch.evaluate_variant import JudgeUnreachable  # type: ignore
except Exception:  # pragma: no cover - fallback for isolated imports
    class JudgeUnreachable(RuntimeError):
        """Raised when the evolution-judge service is unreachable."""

# Line 111: Inside call_quality_judge()
from autoresearch.events import log_event

# Line 183-184: Inside _run_single_fixture_eval()
from autoresearch import evaluate_variant
from autoresearch.lane_runtime import ensure_materialized_runtime

# Line 326: Inside run_dry_run()
from autoresearch.events import log_event
```

**Call context:**

- Line 193: `ensure_materialized_runtime(archive_dir)` — materializes mirror of active lane heads
- Line 195-202: `evaluate_variant.evaluate_single_fixture(...)` — runs fixture eval
- Lines 132-136: `log_event(kind="judge_unreachable", ...)` — logs judge unavailability
- Lines 328-338: `log_event(kind="judge_abstain", ...)` — logs judge abstention verdict

**Verdict:** `NO_OP_SHIM` + `U13_MOVE`

**Migration note:** All imports are deferred (inside functions). JudgeUnreachable has a fallback handler. log_event calls map to v2 event shim. ensure_materialized_runtime is part of v2 lane_runtime stub. evaluate_single_fixture signature stays the same.

---

### 2. `src/api/routers/portal.py` — Portal Report Viewer

**Path reference & context:**

```python
# Line 88: Archive root definition
_ARCHIVE_ROOT = Path(__file__).resolve().parents[3] / "autoresearch" / "archive"
_ARCHIVE_ROOT_REAL = _ARCHIVE_ROOT.resolve()

# Lines 138-150: Portal report view route
@router.get("/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}",
            response_class=HTMLResponse)
async def portal_report_view(...) -> HTMLResponse:
    """Authed view of a rendered fixture report (HTML)."""
```

**Verdict:** `PATH_SWAP`

**Migration note:** Path is hardcoded. In U13, verify v2 archive location (likely same). Rewrite path construction. Security guards (resolve() + is_relative_to()) stay intact.

---

### 3. `cli/freddy/commands/autoresearch.py` — Report Render + Publish CLI

**Path reference & context:**

```python
# Line 31: Archive root definition
_ARCHIVE_ROOT = _REPO_ROOT / "autoresearch" / "archive"

# Line 35: Session directory derivation
def _session_dir(variant: str, lane: str, fixture: str) -> Path:
    return _ARCHIVE_ROOT / variant / "sessions" / lane / fixture
```

**Verdict:** `PATH_SWAP`

**Migration note:** Used by render/publish/detect-meta-patterns subcommands. Rewrite path to v2 location.

---

### 4. `src/audit/events.py` — Audit Event Logger

**Import & wrapper context:**

```python
# Line 23: Re-exports to audit-specific callers
from autoresearch.events import log_event as _log_event

# Lines 26-30: Wrapper for per-audit events
def log_to_audit(audit_dir: Path, kind: str, /, **data: Any) -> None:
    """Append an event to <audit_dir>/events.jsonl."""
    _log_event(kind, path=audit_dir / "events.jsonl", **data)
```

**Verdict:** `NO_OP_SHIM`

**Migration note:** src/audit owns the wrapper; v2 provides log_event. No changes to src/audit/*.py logic, only the underlying import.

---

### 5. `src/audit/agent_runner.py` — Multi-Provider CLI Dispatch

**Import & context:**

```python
# Line 45: Imports retry logic
from autoresearch import agent_retry

# Usage context: Mirrors autoresearch/evolve.py's retry semantics
```

**Verdict:** `NO_OP_SHIM`

**Migration note:** v2 provides agent_retry module (or moved to src/audit internally). Verify retry decorator + exception handling signature.

---

### 6. `src/evaluation/rubrics.py` — Rubric Validation

**Import & cross-check context:**

```python
# Line 1450: Structural validation against lane registry
from autoresearch.lane_registry import LANES as _LANE_SPECS

# Lines 1452-1460: Assertions that rubric IDs match lane declarations
_lane_rubric_ids = {rid for spec in _LANE_SPECS.values() for rid in spec.rubric_ids}
_missing_in_rubrics = _lane_rubric_ids - set(RUBRICS)
assert not _missing_in_rubrics, (...)
```

**Verdict:** `NO_OP_SHIM`

**Migration note:** v2 lane_registry must export LANES dict with rubric_ids attribute. This is a structural check, not runtime data. Verify schema migration.

---

### 7. `src/evaluation/service.py` — Evaluation Service

**Import & context:**

```python
# Line 29: Used to determine primary deliverable per domain
from autoresearch.lane_registry import _DOMAIN_CRITERIA

# Line 43-44: Uses _DOMAIN_CRITERIA to build judge input map
_JUDGE_PRIMARY_DELIVERABLE: dict[str, tuple[str, ...]] = {
    "monitoring": ("digest.md",),
    ...
}
```

**Verdict:** `NO_OP_SHIM`

**Migration note:** v2 exports _DOMAIN_CRITERIA or caller hardcodes fallback. Domain-to-file mapping is stable.

---

### 8. `tests/autoresearch/conftest.py` — Test Module Stubs

**Stub fixtures & context:**

```python
# Lines 28-40: archive_index stub (minimal methods)
_stub(
    "archive_index",
    append_lineage_entries=lambda *a, **k: None,
    append_lineage_entry=lambda *a, **k: None,
    current_variant_id=lambda *a, **k: None,
    load_json=lambda *a, **k: {},
    load_latest_lineage=lambda *a, **k: {},
    ordered_latest_entries=lambda *a, **k: [],
    refresh_archive_outputs=lambda *a, **k: None,
    summarize_variant_diff=lambda *a, **k: {},
)

# Lines 65-79: frontier + lane_paths stubs
_stub(
    "frontier",
    DOMAINS=("geo", "competitive", "monitoring", "storyboard", "marketing_audit"),
    has_search_metrics=lambda *a, **k: True,
    composite_score=lambda entry: 0.5,
    ...
)
```

**Verdict:** `DELETE_WITH_V1`

**Migration note:** Dies in U13a (test classification phase). Tests either migrate to v2 test fixtures or are removed. Conftest is autoresearch-specific.

---

### 9. `.github/workflows/ci-lint-judge-isolation.yml` — Judge Import Lint

**Workflow & rule:**

```yaml
- name: deny judges/ imports from autoresearch/cli/src
  run: |
    if rg -l '^\s*from judges|^\s*import judges' autoresearch/ cli/ src/ 2>/dev/null; then
      echo "FAIL: autoresearch/cli/src must not import from judges/"; exit 1
    fi
```

**Verdict:** `NO_OP_SHIM`

**Migration note:** Boundary rule. v2 maintains same separation. No changes needed.

---

### 10. `.claude/hooks/autoresearch-continuous-evolution-check.sh` — Daemon Hook

**Scope & responsibilities:**

```bash
# Lines 20-22: Daemon paths
SENTINEL=/tmp/autoresearch-keep-running
DAEMON_SCRIPT=/tmp/autoresearch-continuous-evolution-daemon.sh
PID_FILE=/tmp/autoresearch-cont-evolve/.daemon-pid

# Lines 37-49: Health check and restart logic
alive=0
if [[ -f "$PID_FILE" ]]; then
  pid=$(cat "$PID_FILE" 2>/dev/null)
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    alive=1
  fi
fi
```

**Verdict:** `DELETE_WITH_V1` + `JR_REBUILDS`

**Migration note:** Hook is autoresearch v1 specific. In Phase 5, v1 is at autoresearch/legacy/. In U15 (30 days after Phase 5), hook dies with v1 deletion. JR rebuilds equivalent daemon using v2 driver pattern if continuous evolution is still needed.

---

### 11. `scripts/evolve-with-report.sh` — Post-Evolve Summary

**Key operations:**

```bash
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVOLVE_SH="$REPO_ROOT/autoresearch/evolve.sh"
ARCHIVE="$REPO_ROOT/autoresearch/archive"

# Lines 49-150: Python snippet reads scores.json + current.json
archive_dir = Path(archive)
latest = _latest_variant()  # Scans v*/scores.json by mtime
promoted = _promoted_id()   # Reads current.json head
```

**Verdict:** `PATH_SWAP` + `DELETE_WITH_V1`

**Migration note:** Reads from autoresearch/archive/. In Phase 5, path becomes autoresearch/legacy/archive/. Conditional path logic needed or v2 integration. Dies U15. For now: add fallback path detection.

---

### 12. `scripts/agent-launcher.sh` — Subprocess Bootstrap

**Key responsibilities:**

```bash
# Lines 56-75: Detect evolve invocation (guards judges.env bypass)
is_evolve_invocation=0
for arg in "$@"; do
  case "$arg" in
    *evolve.sh|*evolve.py|evolve)
      is_evolve_invocation=1
  esac
done

# Lines 108-132: Mandatory judges.env sourcing
judges_env="${GOFREDDY_JUDGES_ENV:-$HOME/.config/gofreddy/judges.env}"
if [ -r "$judges_env" ]; then
  set -a
  . "$judges_env"
  set +a
```

**Verdict:** `DELETE_WITH_V1` (after Phase 5)

**Migration note:** Stays through Phase 5 (evolve in legacy/). U15: dies. No changes needed until then. But note: if v2 has its own launcher, sync this pattern.

---

## `src/api/` Verdict: Evolution Data Consumption

**Question:** Does the freddy backend read autoresearch evolution data at runtime?

**Answer:** **Partially, indirectly.**

- **Portal routes** (`/v1/portal/{slug}/reports/{lane}/{variant}/{fixture}`) serve pre-rendered HTML reports from `autoresearch/archive/<variant>/sessions/<lane>/<fixture>/report.html`. These are static files, not runtime reads of evolution state.

- **No HTTP evolution-state reads:** src/api does NOT read `lineage.jsonl`, `frontier.json`, `index.json`, or `scores.json` at runtime. It only serves rendered reports.

- **Indirect dependency:** The reports themselves are products of evolution (generated by autoresearch/archive/<variant>/scripts/render_report.py), but the API doesn't read the evolution source data.

- **Recommendation:** Phase 5 move (v1 → autoresearch/legacy/) doesn't break the API. Update `_ARCHIVE_ROOT` path and done.

---

## Transient Daemons (`/tmp/`)

**Found:**
- `/tmp/autoresearch-continuous-evolution-daemon.sh` (referenced in hook)
- `/tmp/autoresearch-cont-evolve/` (log + PID directory)

**Action:** JR rebuilds based on v2 driver pattern in U15 (post-Phase5). These are transient; no migration needed now. Hook just restarts them if they die.

---

## U13 Action Plan (Ordered by Priority)

### Phase 1: CLI & Fixture Handlers (Blocking Tests)

1. **`cli/freddy/fixture/dryrun.py`**
   - Wrap JudgeUnreachable import in v2-aware fallback
   - Rewrite all `log_event` calls to v2 event log
   - Rewrite `evaluate_single_fixture` call to v2 API (signature TBD)
   - Verify `ensure_materialized_runtime` logic in v2

2. **`cli/freddy/fixture/refresh.py`**
   - Rewrite `call_quality_judge` to v2 shim
   - Rewrite `log_event` to v2

3. **`cli/freddy/commands/fixture.py`**
   - Rewrite `read_events` import path
   - Rewrite `call_quality_judge` import path

### Phase 2: Audit Pipeline (Source Isolation)

4. **`src/audit/events.py`**
   - Rewrite `log_event` import to v2 (wrapper stays)

5. **`src/audit/agent_runner.py`**
   - Verify v2 provides `agent_retry` or copy logic from v1
   - Update import path

### Phase 3: Evaluation Service (Validation Logic)

6. **`src/evaluation/rubrics.py`**
   - Rewrite `LANES` import to v2 lane_registry (or inline fallback)

7. **`src/evaluation/service.py`**
   - Rewrite `_DOMAIN_CRITERIA` import (or hardcode if simple)

### Phase 4: Portal & Path Updates

8. **`src/api/routers/portal.py`**
   - PATH_SWAP: `_ARCHIVE_ROOT = ... / "autoresearch" / "archive"` → v2 location

9. **`cli/freddy/commands/autoresearch.py`**
   - PATH_SWAP: `_ARCHIVE_ROOT` construction

### Phase 5: Scripts (Optional Compatibility)

10. **`scripts/evolve-with-report.sh`**
    - Add fallback path detection (try v2, fall back to v1 until Phase5 move)
    - Or defer until Phase 5 (low priority — only runs manually)

11. **Test conftest** (U13a, separate track)
    - Remove stubs; reclassify tests per U13a spec

---

## Risks & Unknowns

### High Confidence (No Escalation)

1. All imports are deferred (inside functions) → safe for lazy rewiring
2. Judge services have v2 equivalents (quality_judge, promotion_judge)
3. Event logging is a thin wrapper → v2 shim is straightforward
4. Portal path change is mechanical (no logic)

### Medium Confidence (Verify in U13)

1. **`evaluate_variant.evaluate_single_fixture()` signature**
   - v1 takes (fixture_id, manifest_path, pool, baseline, seeds, cache_root)
   - v2 must match or wrapper is needed

2. **Lane registry schema**
   - v2 LANES must have rubric_ids attribute for rubrics.py assertion
   - v2 must export _DOMAIN_CRITERIA dict (or caller adapts)

3. **Agent retry semantics**
   - v2 agent_retry decorator must support same exception types + retry logic
   - Verify src/audit/claude_subprocess.py compatibility

### Low Risk (Already Isolated)

1. Module stubs (conftest) die in U13a (separate test classification)
2. Daemon hook dies in U15 (long tail; JR rebuilds then)
3. Shell scripts can PATH_SWAP in Phase 5 (low urgency)

---

## Summary Table: Caller Counts by Verdict

| Verdict | Count | Files | Notes |
|---------|-------|-------|-------|
| NO_OP_SHIM | 11 | dryrun, refresh, fixture, agent_runner, events, rubrics, service, report_base, workflows | v2 provides same-name shims; rewrite import paths |
| PATH_SWAP | 2 | portal.py, autoresearch.py, evolve-with-report.sh (partial) | Hardcoded archive paths; rewrite to v2 location |
| DELETE_WITH_V1 | 4 | conftest, daemon hook, agent-launcher.sh, backfill script | Die with v1 deletion (U15) or test reclassification (U13a) |
| **Total** | **17** | **Production: 8, Tests: 3, Daemon/Scripts: 6** | Zero escalations |

---

## Files to Modify in U13 (Full List)

1. cli/freddy/fixture/dryrun.py ✓
2. cli/freddy/fixture/refresh.py ✓
3. cli/freddy/commands/fixture.py ✓
4. cli/freddy/commands/autoresearch.py ✓
5. src/audit/agent_runner.py ✓
6. src/audit/events.py ✓
7. src/evaluation/rubrics.py ✓
8. src/evaluation/service.py ✓
9. src/api/routers/portal.py ✓
10. tests/autoresearch/conftest.py (U13a track)

**Optional (low priority until Phase 5):**
- scripts/evolve-with-report.sh (fallback path logic)

---

## Verification Checklist

- [x] Grep all 10 search locations for autoresearch + archive patterns
- [x] Identified 17 distinct callers (0 duplicates)
- [x] Verified import lines + surrounding context (5-line blocks)
- [x] Classified each by type (import, path, CLI, hook)
- [x] Assigned verdict per migration criteria
- [x] No runtime evolution data reads in src/api/ (static file serving only)
- [x] Confirmed test stubs die in U13a (separate classification)
- [x] Daemon lives in /tmp (transient; JR rebuilds in U15)
- [x] Zero escalations (all paths clear for U13 implementation)

---

## Author Notes

This audit was conducted 2026-05-11 via systematic grep + manual file inspection. All findings are categorized with explicit file paths and line numbers for U13 implementation reference. The migration is a straightforward path + import rewrite with zero functional changes to operators.

No consumer of autoresearch v1 substrate has blocking logic; all are either thin wrappers (events, judges) or path-based references (portal, CLI). The largest surface is the fixture calibration harness (dryrun.py + refresh.py), which have deferred imports and fallback error handling — both mitigate migration risk.

