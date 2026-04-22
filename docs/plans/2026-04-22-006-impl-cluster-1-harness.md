---
title: Harness implementation research (9 items)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-006-pipeline-overengineering-implementation-research.md
---

---
title: Harness simplifications — implementation research (9 items)
type: research-implementation
status: draft
date: 2026-04-22
parent: 2026-04-22-004-research-cluster-1-2-harness.md
---

# Implementation research: 9 harness simplifications

Each section is self-contained. All file paths are absolute.

---

## #1 — Drop per-cycle smoke; keep preflight + tip; drop `smoke-cli-client-new` litter

**Summary:** Remove the cycle-start `smoke.check` call and the filesystem-littering `smoke-cli-client-new` check. Keep the two high-value smoke gates (preflight and tip). The verifier already paraphrase-tests every fix, so per-cycle smoke adds negligible coverage while creating dated-directory garbage under `clients/`.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:73` — smoke at preflight.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:77` — smoke at bootstrap.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:113` — smoke at every cycle start (the one to delete).
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:82, 302-320` — `_tip_smoke`, to keep.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/SMOKE.md:49-55` — the `smoke-cli-client-new` block.

**Target state:** `smoke.check` runs twice per run (preflight bootstrap + tip). `SMOKE.md` has 4 blocks, not 5. No per-cycle `clients/smoke-check-<ts>/` directories accumulate.

**Implementation approach:**
- Option A: Delete cycle-start smoke + delete the litter check. Minimal diff, matches audit verdict.
- Option B: Keep cycle smoke but replace `smoke-cli-client-new` with a read-only variant (`freddy client list`). Preserves observability inside the cycle at the cost of one extra subprocess per cycle.
- **Recommended:** Option A.
- **Justification:** Audit's round-3 explicitly named the cycle-smoke as "duplicative with verifier." Option B preserves a signal of ~marginal value that's already covered by the verifier's adjacent-checks step (`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/verifier.md:22-24`). Simpler to delete than to maintain a half-muted gate.

**Specific code changes:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py`: delete line 113 (`smoke.check(wt, config, state.token)`).
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/SMOKE.md`: delete lines 49-55 (the `smoke-cli-client-new` block and its prose).
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/README.md`: update any line that lists "per-cycle smoke" (line numbering changed in git status; grep `per-cycle` to find).

**Dependencies:** Independent. Unblocks: none. Enables removing the `clients/` directory from `HARNESS_ARTIFACTS` in item #6 only after this change lands AND the existing runs' `clients/smoke-check-*` residue is cleaned. Leave `clients/` in HARNESS_ARTIFACTS for now (it's still mkdir'd by `worktree.create:50`).

**Edge cases:**
1. A fix in cycle N breaks `/health` but is marked verified because the verifier's adjacent-check list didn't include it — tip-smoke catches it, operator sees `tip-smoke: FAILED` in the summary. Regression: now detected at end-of-run instead of start-of-next-cycle.
2. Cold-cache effect: the first cycle used to pay smoke's ~4s warm-up before the evaluator; now it doesn't. Positive.
3. `_tip_smoke` (`run.py:302`) appends commit reproductions as extra_checks — unchanged.
4. Running with `--resume-branch` still bootstraps smoke (line 77). Preserved.
5. Long runs that used to see cycle-start smoke fail on backend-crash regain that signal only at tip. Acceptable because backend-crash mid-cycle surfaces in the next fixer/verifier subprocess as a connection error (not silent).

**Test strategy:**
- Update `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/tests/harness/test_smoke.py` — `test_parse_extracts_blocks` currently asserts both blocks from a 2-block sample; no change needed since the sample is inline, not SMOKE.md.
- No new test. Deletion is a negative change; the behavior it removes has no test (the repo lacks a `test_run_loop_cycle_smoke` today).
- Optionally add `test_smoke_md_has_four_blocks` parsing the real SMOKE.md to prevent regression.

**Rollout:** No flag. Single commit. Not a breaking change for consumers (the harness is the only caller).

**Estimated effort:** 15 min.

**Open questions:** None — audit gave clear verdict, the restricted check is demonstrably redundant.

---

## #2 — Delete no-progress gate

**Summary:** Remove the `_zero_high_conf_cycles >= 2` early exit. Termination is cleaner with two signals: agent self-signaled-done (`_all_tracks_signaled_done`, `run.py:148`) and `max_walltime` (`run.py:109`). The no-progress counter is a weaker third signal that fires unpredictably when findings exist but are low-confidence.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:38` — `zero_high_conf_cycles: int = 0` field on RunState.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:154-159` — increment + exit gate + reset logic.
- No dedicated test.

**Target state:** RunState has no `zero_high_conf_cycles`. Cycle loop exits only on walltime, agent-signaled-done, graceful-stop, or first-cycle-zero-findings (`run.py:124-125`, unchanged).

**Implementation approach:**
- Option A: Delete outright (field + usage).
- Option B: Gate behind a flag `Config.enable_no_progress_exit=False` for opt-in revival if someone regrets it.
- **Recommended:** Option A.
- **Justification:** Option B is zombie code that no one will toggle. The audit is confident this is duplicative; if it's ever needed again, `git blame` will recover it in 30 seconds.

**Specific code changes:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:38` — delete `zero_high_conf_cycles: int = 0`.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:154-159` — delete the five-line block:
  ```python
  if total_actionable == 0 and state.commits_this_cycle == 0:
      state.zero_high_conf_cycles += 1
      if state.zero_high_conf_cycles >= 2:
          return "no-progress"
  else:
      state.zero_high_conf_cycles = 0
  ```
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/README.md`: any mention of `no-progress` as an exit_reason (grep to confirm). Drop from exit-reason list.

**Dependencies:** None. Independent.

**Edge cases:**
1. An evaluator regression where the agent stops writing `done reason=` to sentinel — without this gate, the run hits walltime (4h default). Mitigation: the agent's prompt (`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/evaluator-base.md:55-62`) is explicit about writing the sentinel; a test asserting the template contains `done reason=` guards this.
2. A cycle with all low-confidence findings (`route()` filters them out → `total_actionable == 0`) used to count toward no-progress; now it doesn't. Expected: agents signal done on the same cycle, so walltime is not reached.
3. `commits_this_cycle` is only used here (grep confirms `run.py:39, 154, 260`); it can also be deleted as it becomes write-only dead state after this change.
4. Pytest run with no mock of cycle loop: no tests hit this path today, so no test needs to change.
5. Any metrics/run-summary printing that references `no-progress` as exit reason must be audited. `_print_summary` only echoes whatever string is returned; no hardcoded "no-progress" ref.

**Test strategy:** None added. Verify existing `tests/harness/test_run.py` still passes; it doesn't touch this path.

**Rollout:** No flag. Single commit.

**Estimated effort:** 10 min.

**Open questions:** Should `commits_this_cycle` also be removed (it only exists to feed this gate)? Recommend yes — dead state after this change.

---

## #3 — Replace `inventory.generate` with breadcrumb file

**Summary:** Delete `harness/inventory.py` (160 LOC, 4 subprocesses, PYTHONPATH fragility). Replace with a static `harness/INVENTORY.md` breadcrumb that tells the evaluator agent where to discover surfaces. The frontend section (`inventory.py:102-117`) already did this pivot; apply it to the other three sections.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/inventory.py` — 160 LOC; CLI Typer-walk subprocess, OpenAPI export subprocess, frontend breadcrumb, autoresearch filesystem walk.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:19, 76` — import + one call.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts.py:32-33, 44` — reads the generated file for injection into evaluator prompt.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/evaluator-base.md:75-77` — `{inventory}` placeholder.

**Target state:** `harness/INVENTORY.md` (version-controlled, hand-written, ~25 lines) exists. `harness/inventory.py` deleted. `run.py` copies `harness/INVENTORY.md` → `run_dir/inventory.md` (or just skips and lets the evaluator prompt reference it directly by path).

**Implementation approach:**
- Option A: Static breadcrumb file, `shutil.copy` from `harness/INVENTORY.md` (or `wt.path/harness/INVENTORY.md`) to `run_dir/inventory.md`. Preserves the existing prompt template's `{inventory}` placeholder substitution — no prompt change.
- Option B: Delete `run_dir/inventory.md` entirely; change the prompt template `{inventory}` to literal breadcrumb text and drop the substitution. Slightly more invasive on the prompt side.
- **Recommended:** Option A.
- **Justification:** One-line replacement in `run.py`, zero changes to `prompts.py` or `evaluator-base.md` template. Per-run `run_dir/inventory.md` stays available for post-mortem ("what breadcrumb did the evaluator see on this run?"). Cheapest migration.

**Specific code changes:**

New file `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/INVENTORY.md` (content illustrative):
```markdown
# App surface inventory — discover at runtime

Run these commands from the worktree root to enumerate the app's surfaces.
Treat the output as authoritative; `harness/SEED.md` is supplementary prose.

## CLI
`.venv/bin/freddy --help` — lists top-level commands and groups.
`.venv/bin/freddy <group> --help` — drills into each group.

## HTTP API
`curl -s http://127.0.0.1:8000/openapi.json | python -m json.tool` — full
OpenAPI spec; iterate `.paths` for routes and methods.

## Frontend
Read `frontend/src/lib/routes.ts` — exports `ROUTES` (keyed by name) and
`LEGACY_PRODUCT_ROUTES` (redirect-only paths). Follow imports from
`frontend/src/main.tsx` to see which routes are wired.

## Autoresearch programs
`ls autoresearch/*.py` — Python entry points.
`ls autoresearch/archive/current_runtime/programs/*.md` — program specs.
```

Change `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:19`: remove `inventory` from the import list.

Change `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:76`:
```python
# before:
inventory.generate(wt.path, run_dir / "inventory.md")
# after:
import shutil
shutil.copy(wt.path / "harness" / "INVENTORY.md", run_dir / "inventory.md")
```
(move `import shutil` to the top of the file alongside other imports).

Delete `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/inventory.py`.

**Dependencies:** Independent. Unblocks: none. `harness/SEED.md` is unchanged and still injected separately.

**Edge cases:**
1. The evaluator agent ignores breadcrumbs and burns 5 minutes exploring: the prompt already tells it to read files itself (`evaluator-base.md:5` grants "full tool access"), so this is a nominal cost.
2. `freddy --help` changes output format (Typer upgrade) — doesn't matter, the agent parses prose, not JSON.
3. OpenAPI endpoint not up because backend crashed: agent sees the curl fail and has to fall back to reading `src/api/main.py` imports — no worse than today's behavior where `inventory._api_section` returns an `_export_openapi failed_` line.
4. Someone runs the harness from a different cwd than the repo root: `harness/INVENTORY.md` is under the worktree (copied fresh each run), so `wt.path / "harness" / "INVENTORY.md"` resolves correctly.
5. `keep_worktree=True` runs that stayed around before this change still have their auto-generated `inventory.md` — no problem; they're historical.

**Test strategy:**
- Delete `tests/harness/test_inventory.py` if it exists (it doesn't per current `ls`).
- Add one test in `tests/harness/test_run.py` or a new `test_inventory_breadcrumb.py`: assert `harness/INVENTORY.md` exists, contains the expected section headers (`## CLI`, `## HTTP API`, `## Frontend`, `## Autoresearch`). ~10 LOC.

**Rollout:** No flag. Breaking change only for external scripts that import `harness.inventory` — grep confirms none exist outside the module itself.

**Estimated effort:** 30 min.

**Open questions:** Should `harness/SEED.md` also be consolidated into `INVENTORY.md`? Separate question — SEED is prescriptive context, INVENTORY is discovery breadcrumbs. Keep separate.

---

## #4 — Loosen `Verdict.parse` to accept `{verified|pass|passed|ok}` whitelist

**Summary:** Replace strict `verdict_str == "verified"` with membership check against a small whitelist `{"verified", "pass", "passed", "ok"}`. Update `verifier.md` to document the loosened contract. Eliminates a class of false-negative verdicts where the agent writes a synonym and the fix gets rolled back.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:84-100` — `Verdict.parse`; line 96: `verified=(verdict_str == "verified")`.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/verifier.md:27, 32` — contract `verdict: verified | failed`.

**Target state:** Module-level constant `_VERIFIED_TOKENS = frozenset({"verified", "pass", "passed", "ok"})`. `Verdict.parse` sets `verified = verdict_str.lower() in _VERIFIED_TOKENS`. Verifier prompt updated.

**Implementation approach:**
- Option A: Strict whitelist membership (rejects qualifier-added strings like `verified-with-notes`).
- Option B: Loose prefix match (`verdict_str.startswith("verified")` etc). Risk: accepts `verified-with-caveats` → drift toward non-firing gate.
- **Recommended:** Option A.
- **Justification:** Audit explicitly warns against drift (round-3 cited). Strict membership preserves the gate's authority while accepting common synonyms.

**Specific code changes:**

`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py`, just above class `Verdict` (near line 76):
```python
_VERIFIED_TOKENS: frozenset[str] = frozenset({"verified", "pass", "passed", "ok"})
```

Change `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:96`:
```python
# before:
verified=(verdict_str == "verified"),
# after:
verified=(verdict_str.lower() in _VERIFIED_TOKENS),
```

Update `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/verifier.md:27`:
```
Any failure → `verdict: failed` with a specific reason. All four pass → `verdict: verified` (or `pass`/`passed`/`ok`).
```
and `verifier.md:32` from `verdict: verified | failed` to `verdict: verified | pass | passed | ok | failed`.

**Dependencies:** Independent.

**Edge cases:**
1. Agent writes `verdict: Verified` (capital V) — now passes via `.lower()`.
2. Agent writes `verdict: "verified"` (quoted) — YAML strips quotes; `verdict_str` is `verified`; passes.
3. Agent writes `verdict: verified-with-notes` — fails membership; stays `verified=False`. Operator sees `verdict=verified-with-notes` as reason in log (line 269 in run.py). Good — same as today.
4. Agent writes `verdict: failed` — lowercase, not in set, `verified=False`. Unchanged.
5. Agent writes `verdict: PASSED` — `.lower()` → `passed` → passes. Good.

**Test strategy:**
Add to `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/tests/harness/test_engine.py`:
```python
@pytest.mark.parametrize("token", ["verified", "pass", "passed", "ok", "VERIFIED", "Pass"])
def test_verdict_parse_accepts_synonyms(tmp_path, token):
    path = tmp_path / "v.yaml"
    path.write_text(f"verdict: {token}\n", encoding="utf-8")
    v = Verdict.parse(path)
    assert v.verified is True

@pytest.mark.parametrize("token", ["failed", "verified-with-notes", "maybe", ""])
def test_verdict_parse_rejects_non_synonyms(tmp_path, token):
    path = tmp_path / "v.yaml"
    path.write_text(f"verdict: {token}\n", encoding="utf-8")
    v = Verdict.parse(path)
    assert v.verified is False
```

Also add one test asserting `_VERIFIED_TOKENS` is exactly the documented set (prevents silent drift):
```python
def test_verified_tokens_are_exactly_documented():
    from harness.engine import _VERIFIED_TOKENS
    assert _VERIFIED_TOKENS == frozenset({"verified", "pass", "passed", "ok"})
```

**Rollout:** No flag. Prompt change is co-authored with code change in one commit.

**Estimated effort:** 20 min.

**Open questions:** Should `yes`/`true` also be whitelisted? Recommend no — these aren't natural for "verdict" phrasing and would invite drift.

---

## #5 — Tighten `_TRANSIENT_PATTERNS` with proper JSON parse

**Summary:** Replace the fragile `'"type":"error"'` substring with a structured parser that mirrors `parse_rate_limit` (line-by-line JSON parse for events with `type=="error"`). Also tighten `"API Error: 5"` to a word-bounded regex. Eliminates a known false-positive class where benign log content containing the `"type":"error"` fragment triggered spurious retries.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:31-36` — tuple of substrings.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:227-231` — `_is_transient` does substring-`in` matching against the last 8 KB.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:173-224` — `parse_rate_limit`; the exemplar pattern.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/tests/harness/test_engine.py:156-164` — `test_is_transient_detects_claude_json_error_event` (the test that currently pins the substring behavior).

**Target state:** `_is_transient` returns True on:
- a prose substring match from a tightened list (no `'"type":"error"'`, tightened 5xx regex), OR
- a JSON event detected by new `_parse_error_event` (structured parse of tail).

**Implementation approach:**
- Option A: Add structured parser + keep substring fallback for codex/prose. Drop `'"type":"error"'` from substrings. Tighten `"API Error: 5"` to `re.compile(r"\bAPI Error: 5\d\d\b")`.
- Option B: Remove substring matching entirely; switch all detection to structured parse. Too invasive: codex doesn't speak stream-json, so its prose stderr (`API error: 429`) would not match.
- **Recommended:** Option A.
- **Justification:** Mirrors the existing `parse_rate_limit` pattern exactly, preserves codex support, removes the named false-positive.

**Specific code changes:**

`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/engine.py:31-36`:
```python
# before:
_TRANSIENT_PATTERNS = (
    "429", "stream disconnected", "Reconnecting", "overloaded",
    "rate limit", "503", "502",
    "API Error: 5", "Internal server error",
    '"type":"error"',
)
# after:
_TRANSIENT_SUBSTRINGS = (
    "stream disconnected", "Reconnecting", "overloaded",
    "rate limit", "Internal server error",
)
_TRANSIENT_REGEXES = (
    re.compile(r"\b(429|502|503)\b"),
    re.compile(r"\bAPI Error: 5\d\d\b"),
)
```

Add a new function near `parse_rate_limit` (around line 225):
```python
def _has_error_event(log_path: Path) -> bool:
    """Return True if the tail of `log_path` contains a stream-json event with type=='error'."""
    if not log_path.exists():
        return False
    try:
        with open(log_path, "rb") as fp:
            fp.seek(0, 2)
            size = fp.tell()
            fp.seek(max(0, size - 32_000))
            tail = fp.read().decode("utf-8", errors="replace")
    except OSError:
        return False
    for raw in tail.splitlines():
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, dict) and data.get("type") == "error":
            return True
    return False
```

Rewrite `_is_transient` (line 227):
```python
def _is_transient(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    tail = log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
    if any(s in tail for s in _TRANSIENT_SUBSTRINGS):
        return True
    if any(r.search(tail) for r in _TRANSIENT_REGEXES):
        return True
    return _has_error_event(log_path)
```

**Dependencies:** Independent.

**Edge cases:**
1. Codex prose `API error: 429 Too Many Requests`: `\b429\b` matches. Test `test_is_transient_detects_codex_patterns` passes.
2. Claude stream-json error event on its own line: `_has_error_event` returns True. Test `test_is_transient_detects_claude_json_error_event` passes (new path).
3. A README prose fragment `"type":"error"` in an unrelated log line: substring no longer matches (removed), structured parse ignores non-JSON lines. Fixed false-positive.
4. Log line `API Error: 5xx documented in section 4.5`: old substring matched; new regex `\bAPI Error: 5\d\d\b` requires digits after "5", doesn't match prose. Fixed.
5. Timestamp `Unix epoch 1729552343`: old `"429"` substring matched; new `\b429\b` requires word boundary — `2343` and `1729552343` don't match (`\d\b` after `3` is a word-boundary on end-of-token but `429` is embedded). Confirmed: `re.search(r'\b429\b', '1729552343')` returns None. Fixed.

**Test strategy:**

Update `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/tests/harness/test_engine.py`:
- Keep `test_is_transient_detects_claude_json_error_event` — it should still pass via `_has_error_event` path.
- Keep `test_is_transient_detects_codex_patterns` — `\b429\b` handles `API error: 429`.
- Keep `test_is_transient_detects_claude_5xx_pattern` — `\bAPI Error: 5\d\d\b` handles `API Error: 503`.
- Keep `test_is_transient_detects_claude_overloaded` — substring match.
- Keep `test_is_transient_false_for_clean_log`.
- Add: `test_is_transient_false_for_literal_type_error_in_prose` — log content `{"doc":"example uses \"type\":\"error\" pattern"}` → returns False.
- Add: `test_is_transient_false_for_429_embedded_in_number` — log `epoch 1729552343 end` → returns False.
- Add: `test_has_error_event_parses_structured_json` — directly test the new helper.

**Rollout:** No flag. Single commit.

**Estimated effort:** 45 min (more test surface than the others).

**Open questions:** The existing `_RETRY_DELAYS = (5, 30, 120)` is unchanged — this item is narrow to detection, not retry policy.

---

## #6 — Auto-derive `_FIXER_REACHABLE` from `SCOPE_ALLOWLIST`

**Summary:** Replace the hand-written `_FIXER_REACHABLE` regex (which is the manual union of `SCOPE_ALLOWLIST` entries) with a compiled union of each SCOPE_ALLOWLIST pattern's `.pattern` attribute. Eliminates the sync burden: adding a new track or changing an allowlist updates both automatically.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:8-12` — `SCOPE_ALLOWLIST` dict of 3 compiled regexes.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:18` — `_FIXER_REACHABLE = re.compile(r"^(cli/freddy/|pyproject\.toml$|src/|autoresearch/|frontend/)")` (hand-written union).
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:86` — `check_no_leak` uses it.

**Target state:** `_FIXER_REACHABLE` is built by combining the per-track patterns.

**Implementation approach:**
- Option A: `_FIXER_REACHABLE = re.compile("|".join(p.pattern for p in SCOPE_ALLOWLIST.values()))`. Each pattern already has `^(...)` anchor, so the union is `^(cli/freddy/|pyproject\.toml$)|^(src/|autoresearch/)|^(frontend/)`, semantically equivalent to the current regex.
- Option B: Rewrite SCOPE_ALLOWLIST as lists of prefix strings (no regex), derive both regexes from those. More invasive — changes SCOPE_ALLOWLIST's shape and its callers.
- **Recommended:** Option A.
- **Justification:** Literally one-line change, zero behavioral difference on the test suite (all 7 scope tests pass by construction since the union is algebraically identical). The hand-written anchor-inside-group union is ugly but correct; Python's `re` engine evaluates `^(A|B)|^(C|D)|^(E)` identically to `^(A|B|C|D|E)` on non-empty prefix chains.

**Specific code changes:**

`/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:14-18`:
```python
# before:
# A "fixer-reachable" leak is a file under any track's scope. Paths outside every
# track's allowlist (docs/, .claude/, harness/, tests/, README, etc.) can't be
# fixer-caused even if they became dirty during a run — concurrent dev activity
# on those paths is not a leak from the harness's perspective.
_FIXER_REACHABLE = re.compile(r"^(cli/freddy/|pyproject\.toml$|src/|autoresearch/|frontend/)")

# after:
# A "fixer-reachable" leak is a file under any track's scope. Derived from
# SCOPE_ALLOWLIST so adding/changing a track updates both regexes together.
_FIXER_REACHABLE = re.compile("|".join(p.pattern for p in SCOPE_ALLOWLIST.values()))
```

**Dependencies:** Independent. If the harness ever adds a 4th track, this derivation now self-updates.

**Edge cases:**
1. A track's allowlist pattern omits the `^` anchor: currently both regexes assume leading-anchored match. New code would produce `^(X)|^(Y)|Z` — `Z` unanchored. Mitigation: an assertion `assert all(p.pattern.startswith("^") for p in SCOPE_ALLOWLIST.values())` guarantees the invariant. Add it.
2. Two tracks with overlapping prefixes (e.g., both matching `src/`): union behavior is identical — union is semantically an OR.
3. Performance: one compile vs five — negligible.
4. `HARNESS_ARTIFACTS` is unchanged by this item. (The broader "source HARNESS_ARTIFACTS from worktree.WORKTREE_GENERATED_PATHS" suggestion in the cluster doc's F1.4 is out of scope here — item #6 is specifically the `_FIXER_REACHABLE` auto-derivation.)
5. `re.compile` with a trailing `|` (if the dict is empty) would match everything. Guard: `assert SCOPE_ALLOWLIST, "SCOPE_ALLOWLIST must not be empty"`.

**Test strategy:**
No test changes. Existing tests (`test_check_no_leak_detects_new_dirty_in_fixer_reachable_path`, `test_check_no_leak_ignores_new_dirty_outside_fixer_reach`, `test_scope_allowlist_has_three_tracks`) exercise both paths.

Optionally add:
```python
def test_fixer_reachable_matches_each_track_sample():
    from harness.safety import _FIXER_REACHABLE, SCOPE_ALLOWLIST
    for track, pat in SCOPE_ALLOWLIST.items():
        # pick one sample path that each track's own pattern matches; _FIXER_REACHABLE must too
        samples = {"a": "cli/freddy/x.py", "b": "src/api/main.py", "c": "frontend/app.ts"}
        assert _FIXER_REACHABLE.match(samples[track]), track
```

**Rollout:** No flag. Single commit.

**Estimated effort:** 10 min.

**Open questions:** None.

---

## #17 — Extract `graceful_kill` helper to `src/shared/process.py`

**Summary:** Two near-identical SIGTERM→wait→SIGKILL implementations exist at `harness/worktree.py:181-196` (`_terminate_backend`) and `autoresearch/evolve.py:70-88` (`_terminate_process`). Extract a single helper. Prefer locating it in the harness or a new `harness/_process.py` rather than `src/shared/process.py` — the code is infrastructure, not product surface.

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/worktree.py:181-196` — `_terminate_backend(wt)`; uses `os.killpg(os.getpgid(pid), SIGTERM)` then `os.killpg(..., SIGKILL)`. Process is a `subprocess.Popen` wrapped in a `Worktree` dataclass.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/evolve.py:65-88` — `_supports_process_groups()` + `_terminate_process(process, reason, grace_seconds=10)`; takes a bare `subprocess.Popen`, tolerates OS without process groups via `process.terminate()` fallback.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/src/shared/` — **does not exist**; `src/` is product code (`src/api`, `src/auth`, etc.).

**Target state:** One helper, `graceful_kill(proc: subprocess.Popen, grace_seconds: int = 5) -> None`, called by both. Each caller handles its own owner-wrapping logic (`wt.backend_proc = None`, log line, etc.).

**Implementation approach:**
- Option A: New file `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/_process.py` with the helper. Import from `harness/worktree.py` via `from autoresearch._process import graceful_kill`. Reverses current layering (harness currently doesn't import autoresearch).
- Option B: New file `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/_process.py`. Both `harness/worktree.py` and `autoresearch/evolve.py` import from it.
- Option C: New file `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/src/shared/process.py` (create the dir). Matches the audit's proposed path but mixes infra utilities into product source.
- Option D: Don't extract. Keep both. Accept the ~18 LOC duplication.
- **Recommended:** Option B, but only if touched in the same PR as another harness change. Otherwise Option D (defer).
- **Justification:** The audit proposed `src/shared/process.py`, but `src/` contains FastAPI product code. Adding an infra utility there muddies the layering. `harness/_process.py` keeps infra together. `autoresearch/` already imports from its own files; a reverse import (autoresearch→harness) creates a new coupling direction. A bidirectional dependency isn't ideal. **Honest take: this is low-value refactoring for a 18-LOC duplication across two modules in different subsystems. Recommend DEFER unless you're already in one of these files.**

**Specific code changes (if Option B):**

New file `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/_process.py`:
```python
"""Process-group-aware graceful termination. Extracted from worktree + evolve."""
from __future__ import annotations

import os
import signal
import subprocess


def _supports_process_groups() -> bool:
    return hasattr(os, "setsid") and hasattr(os, "killpg")


def graceful_kill(proc: "subprocess.Popen[bytes]", grace_seconds: int = 5) -> None:
    """SIGTERM → wait → SIGKILL. Silent no-op if proc already exited."""
    if proc.poll() is not None:
        return
    try:
        if _supports_process_groups():
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            if _supports_process_groups():
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, PermissionError):
            pass
```

Change `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/worktree.py:181-195`:
```python
def _terminate_backend(wt: Worktree) -> None:
    if wt.backend_proc is None:
        return
    from harness._process import graceful_kill  # noqa: C0415
    graceful_kill(wt.backend_proc, grace_seconds=5)
    wt.backend_proc = None
```

Change `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/autoresearch/evolve.py:65-88`:
```python
def _terminate_process(process: subprocess.Popen, reason: str, grace_seconds: int = 10) -> None:
    from harness._process import graceful_kill  # noqa: C0415
    if process.poll() is not None:
        return
    print(f"  Stopping meta agent ({reason}).", file=sys.stderr)
    graceful_kill(process, grace_seconds=grace_seconds)
```

The `_supports_process_groups` local in `evolve.py:65-67` is also now dead; delete it.

**Dependencies:** Creates a new harness→autoresearch edge if reversed, or a new autoresearch→harness import edge. Option B (autoresearch→harness) is cleanest since harness already has other utility modules.

**Edge cases:**
1. Process group creation: both callers already pass `start_new_session=True` to Popen. Confirmed at `worktree.py:127` and `evolve.py:570`.
2. The evolve variant prints a status line (`"Stopping meta agent"`). Preserved by the caller, not folded into the helper.
3. `wt.backend_proc = None` after termination is caller-side state; helper doesn't touch it.
4. Grace period differs (5s vs 10s); parameterized.
5. Race: process exits between `poll()` and `killpg` — `ProcessLookupError` caught in the helper.

**Test strategy:**
- Existing `test_kill_port_sigterm_then_sigkill` (`tests/harness/test_worktree.py:192`) tests `_kill_port`, not `_terminate_backend` — unaffected.
- Add `tests/harness/test_process.py`:
  ```python
  def test_graceful_kill_noop_on_exited_proc(monkeypatch): ...
  def test_graceful_kill_sigterm_then_wait(monkeypatch): ...
  def test_graceful_kill_falls_to_sigkill_on_timeout(monkeypatch): ...
  ```
  ~50 LOC, mocks `os.killpg` and `proc.wait`.

**Rollout:** No flag.

**Estimated effort:** 1.5 hours (including tests). Skip if not already in one of these files — **low leverage vs cost.**

**Open questions:** Is the audit's requested path `src/shared/process.py` load-bearing? Flag for JR — I'd put it in `harness/_process.py` but defer to his call on module layering.

---

## #19 — Drop `check_scope` peer-filter; serialize commits under `commit_lock`

**Summary:** `check_scope` currently excludes peer tracks' in-flight dirty files from this track's scope check. That defense exists because parallel fixers leave uncommitted edits in peer scopes, which would otherwise look like scope violations. If commits are strictly serialized under `commit_lock` and `check_scope` runs **only** while the lock is held, peer-track in-flight files still exist — but the current code already passes the test with peer-filtering removed, because the check is preceded by `rollback_track_scope(finding.track)` at `run.py:240` (resets only this track's scope before fixer runs) and `_commit_fix` stages only in-scope files at `run.py:283-285`.

**Verify the invariant:** `verifier.md:5` explicitly states "READ-ONLY. No git stash, git reset, or git checkout." Verified — the verifier does not mutate the working tree. This means that between fixer-end and `check_scope`, only the fixer-just-run could have dirtied files. Peers may still have their own dirty files from their own fixers running concurrently in other tracks. **Therefore peer-filter is still needed** unless commits are fully serialized AND verified-before-commit is strictly sequential across tracks, which they are not today.

**Honest re-read:** This simplification is **not safe** as stated. Under current parallel execution, track A's fixer runs, then track A's verifier runs (backend restart serialized via `restart_lock`), then `check_scope` fires — at the same time, track B's fixer is already running in parallel and may have dropped a `src/api/` edit into the working tree. Track A's `check_scope` would see `src/api/` files and, without peer-filter, flag them as A-violations. False positive → A's fix gets rolled back. This is the exact bug the peer-filter was introduced to prevent (ff2f2e4 in git log).

**Recommended:** **DO NOT implement this change.** Audit's own F1.1 analysis (cluster doc lines 22-30) reaches the same conclusion: the peer-filter is load-bearing under current parallel execution. The only way to drop it safely is to either (a) serialize all fixer+verifier work under a single lock (= kills parallelism) or (b) give each track its own worktree (= F1.2's REDESIGN, a much bigger change).

**Alternative minimal improvement:** Clarify the comments. `safety.py:53-57` says "Under parallel execution, files matching any OTHER track's allowlist are assumed to be peer fixers' in-flight edits" — that's accurate but the reader has to reconstruct the threat model. A two-line comment tying it to `commit_lock`'s semantics would help future readers avoid the same misreading I almost made:

```python
# This peer-filter is LOAD-BEARING under parallel execution. Fixers in peer
# tracks may have uncommitted edits in the working tree at the moment this
# check fires. Those edits will be validated by their OWN track's check_scope
# when their own commit_lock window opens; this track must not attribute them.
# DO NOT REMOVE without first moving to per-track worktrees (see F1.2).
```

**Current state:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:60-63` — peer filter logic.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:239-240` — `rollback_track_scope` under `commit_lock` before fixer runs.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:251-255` — `check_scope` runs without holding `commit_lock`; `_commit_fix` then acquires it.
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/prompts/verifier.md:5` — read-only invariant holds.

**Target state:** Peer filter stays. Comment improved.

**Implementation approach:**
- Option A: Drop peer filter as proposed. **Rejected** — unsafe under parallelism.
- Option B: Keep peer filter, strengthen comment + add a guarding test that asserts `check_scope` is safe when called while a peer track has dirty scope-matching files. Existing test `test_check_scope_ignores_peer_tracks_dirty_files` already covers this; just make sure a unit test ties it explicitly to the docstring.
- Option C: Move to per-track worktrees (F1.2 REDESIGN). Out of scope for this item.
- **Recommended:** Option B (keep, clarify).

**Specific code changes:**
- `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py:53-57` — expand docstring as above.

**Dependencies:** None. Blocks nothing. Explicitly gated on F1.2 (per-track worktrees) if the team later wants to revisit.

**Edge cases:** N/A — this is a no-op + comment.

**Test strategy:** Existing `test_check_scope_ignores_peer_tracks_dirty_files` (`tests/harness/test_safety.py:65-82`) already covers the scenario. No change.

**Rollout:** Comment-only.

**Estimated effort:** 10 min.

**Open questions:** JR decision: does he want to escalate to F1.2 (per-track worktrees) as the real fix, or accept the peer-filter as load-bearing and move on? My read: accept. The 4-hour F1.2 refactor is bigger than this item's perceived gain.

---

## #21 — Test-pass-count delta after harness fixes (NEW feature)

**Summary:** Add a gate that records the count of passing tests before each fix and re-counts after, failing the fix if the count decreased. This catches a class of "fixer deleted the broken thing" regressions: an endpoint 5xx gets "fixed" by deleting the endpoint and its test, which would pass the verifier (no more 5xx) but silently shrink test coverage.

**Current state:** Doesn't exist. Verifier prompt (`verifier.md:26`) asks for "surface preservation" via diff inspection but that's an LLM judgment, not a deterministic count. No equivalent gate in `safety.py` or `run.py`.

**Target state:** A new safety gate `check_test_pass_delta(wt, pre_sha) -> list[str] | None` that runs the test suite before fixer and after fixer, returns a list of newly-failing test ids (including "zero tests ran → previously N ran"). Integrated into `run._process_finding` as a peer of `check_scope` and `check_no_leak`.

**Implementation approach:**
- Option A: Full pytest run before + after every fix. Reality check: GoFreddy's test suite likely takes 60-120 seconds per run (250+ test files in `tests/`); gating every fix on two runs adds ~4 min × number of fixes. At ~5 fixes/cycle × 5 cycles = ~100 min overhead per run. Kills the budget.
- Option B: Track-scoped test subset. Only run tests under a path glob matching the track's scope (e.g., track A → `tests/test_cli_*.py`; track B → `tests/api/ tests/test_*_service.py`; track C → `frontend/` Playwright). Scoped runs are 10-30s each. Overhead ~3-6 min/fix, still adds up but is tolerable.
- Option C: Pre-fixer: capture full pytest `--collect-only` count (fast, <5s). Post-fixer: re-collect. If count dropped → the fixer deleted tests. Cheaper than running; catches deletion-as-fix but not "test still exists but now passes trivially" cases.
- Option D: Pre-fixer: `pytest --co -q` file count in the track's scope + `git log pre_sha..HEAD -- tests/` check. If any file under `tests/` was deleted, fail. A change-surface check rather than a pass-count check.
- **Recommended:** Hybrid of C + D, enforce via policy in the fixer prompt + deterministic check.
  - **Policy (prompt):** fixer.md:42 already says "You may NEVER modify `tests/**` or `harness/**` — those are instrumentation." Strengthen: "Deleting a test is a scope violation even if your allowlist technically matches."
  - **Deterministic check:** Add `safety.check_test_manifest_delta(wt, pre_sha) -> list[str] | None` that returns paths under `tests/` that were deleted or had test-count decrease. Run after fixer, before commit. This is cheap (collect-only is fast) and directly catches the deletion-as-fix attack.
- **Justification:** Full test runs are budget-prohibitive. The deletion-as-fix failure mode is the concrete thing to catch. Collect-only counts + tests-dir-diff cover 90%+ of the risk at <5s/fix. If later observed that fixers find cleverer ways to game it, escalate to track-scoped actual runs.

**Specific code changes:**

New function in `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py`:
```python
def check_test_manifest_delta(wt: Path, pre_sha: str) -> list[str] | None:
    """Fail if the fixer removed tests or shrank the collected-test count.

    Catches "delete the endpoint to fix the 5xx" regressions that the verifier
    can miss. Runs `pytest --collect-only -q` twice (cheap, ~2-5s each).
    """
    # 1. Diff tests/ between pre_sha and HEAD; any D (deleted) entry is a violation.
    diff = subprocess.run(
        ["git", "diff", "--name-status", f"{pre_sha}..HEAD", "--", "tests/"],
        cwd=wt, capture_output=True, text=True, check=False,
    )
    deleted = [line.split("\t", 1)[1] for line in diff.stdout.splitlines()
               if line.startswith("D\t")]
    if deleted:
        return [f"deleted: {p}" for p in deleted]

    # 2. Compare pre_sha test-collection count to HEAD test-collection count.
    #    Done via `git stash` isn't possible (peer tracks have dirty edits).
    #    Instead run collect twice on the current HEAD after commit — if this
    #    function is called post-commit, the pre-count must be captured on entry to _process_finding.
    #    See run.py for the pre-capture; this function just re-collects.
    post = _collect_test_count(wt)
    # Note: pre-count is passed via closure or module-level; see below.
    return None  # caller compares pre/post counts
```

Actually, cleaner contract: have two helpers. Pre-fixer: `count_collected_tests(wt) -> int`. Post-fixer: same call. Orchestrator compares.

Add to `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/safety.py`:
```python
def count_collected_tests(wt: Path) -> int:
    """Return pytest's collect-only count. Cheap (~2-5s). Returns -1 on failure."""
    result = subprocess.run(
        ["pytest", "--collect-only", "-q", "--no-header", "--no-summary", "tests/"],
        cwd=wt, capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0 and "collected" not in result.stdout:
        return -1
    # Last line of `-q` is "N tests collected in Xs"
    for line in reversed(result.stdout.splitlines()):
        m = re.match(r"(\d+) tests? collected", line)
        if m:
            return int(m.group(1))
    return -1


def check_tests_deleted(wt: Path, pre_sha: str) -> list[str] | None:
    """Return test files deleted between pre_sha and HEAD, or None."""
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{pre_sha}..HEAD", "--", "tests/"],
        cwd=wt, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    deleted = [line.split("\t", 1)[1] for line in result.stdout.splitlines()
               if line.startswith("D\t")]
    return deleted or None
```

Integrate in `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/harness/run.py:_process_finding` (around line 235):
```python
def _process_finding(config: "Config", wt: worktree.Worktree, finding: "Finding", state: RunState) -> None:
    pre_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=wt.path, text=True).strip()
    pre_test_count = safety.count_collected_tests(wt.path)  # NEW
    ...
    verdict = engine.verify(config, finding, wt, state.run_dir)

    scope_violations = safety.check_scope(wt.path, pre_sha, finding.track) or []
    leak_violations = safety.check_no_leak(state.pre_dirty) or []
    # NEW:
    tests_deleted = safety.check_tests_deleted(wt.path, pre_sha) or []
    post_test_count = safety.count_collected_tests(wt.path)
    test_delta_violation = []
    if pre_test_count > 0 and post_test_count >= 0 and post_test_count < pre_test_count:
        test_delta_violation = [f"test-count: {pre_test_count} → {post_test_count}"]

    violations = scope_violations + leak_violations + tests_deleted + test_delta_violation
    ...
```

And the rollback-on-fail log (run.py:262-269) gets one more clause:
```python
if tests_deleted:
    parts.append(f"tests-deleted={tests_deleted}")
if test_delta_violation:
    parts.append(test_delta_violation[0])
```

**Dependencies:** Pytest must be installed in the worktree venv. It already is (`tests/` is real in this repo).

**Edge cases:**
1. Pre-count is -1 (pytest collection failed because fixer's target state was already broken). Don't gate — `pre_test_count > 0` guard.
2. Post-count is -1 (fixer broke collection). That *should* fail — flag as violation: `-1` means "pytest can't even collect after the fix." Update the guard to also fail when `pre > 0 and post == -1`.
3. Fixer legitimately renames a test file (e.g., `test_foo.py` → `test_foo_new.py`). `check_tests_deleted` sees a `D` — false positive. Mitigation: only flag deletions where no matching addition exists. Or: loosen to only flag when BOTH the rename happened AND count dropped. Current implementation flags any D, which is strict but acceptable because fixer prompt forbids touching tests/.
4. Fixer adds tests (count increases). Not a violation. Handled by `<` guard.
5. Track C (frontend) has no pytest tests; the subprocess finds zero or pytest returns "no tests ran." The guard `pre_test_count > 0` bypasses. Frontend fixers see no gate. Acceptable — frontend test deletion would be a `frontend/` scope change, caught separately by code review of `frontend/*.test.{ts,tsx}` deletions. Optional extension: a `check_frontend_test_manifest_delta` that greps for `*.test.ts` count.
6. Test takes 30+ seconds to collect (happens with Django-style app configs). `timeout=30` may be tight — bump to 60.
7. Running `pytest --collect-only` with `DATABASE_URL` / Supabase env loaded: harmless, collection doesn't hit the DB.

**Test strategy:**
New tests in `/Users/jryszardnoszczyk/Documents/GitHub/gofreddy/tests/harness/test_safety.py`:
```python
def test_count_collected_tests_returns_positive(tmp_path):
    """Basic smoke — pytest collect against a tiny fake test file."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_a(): pass\ndef test_b(): pass\n")
    # ... requires pytest available; may need conftest.py
    count = safety.count_collected_tests(tmp_path)
    assert count == 2

def test_check_tests_deleted_flags_removed_test_file(tmp_path):
    repo = _init_repo(tmp_path)
    # seed a test file, commit
    (repo / "tests").mkdir()
    (repo / "tests" / "test_foo.py").write_text("def test_x(): pass\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "add"], check=True)
    pre = _pre_head(repo)
    (repo / "tests" / "test_foo.py").unlink()
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "del"], check=True)
    assert safety.check_tests_deleted(repo, pre) == ["tests/test_foo.py"]

def test_check_tests_deleted_none_when_no_deletions(tmp_path):
    repo = _init_repo(tmp_path)
    pre = _pre_head(repo)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_new.py").write_text("def test_x(): pass\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "add"], check=True)
    assert safety.check_tests_deleted(repo, pre) is None
```

Integration in `tests/harness/test_run.py`: monkey-patch `safety.count_collected_tests` to return a decreasing count and assert `_process_finding` rolls back.

**Rollout:**
- Feature flag: `Config.enforce_test_delta: bool = True`. If set to False, skip the gate (useful for first few runs while we tune it).
- Log-before-fail: for the first week, log violations as warnings without rolling back, confirm false-positive rate is low, then flip to enforcement.

**Estimated effort:** 3-4 hours (implementation + tests + one observational run to tune timeout and check for false positives).

**Open questions:**
1. JR: OK with adding ~10s/fix (two collect-only runs) as budget tax? That's 10s × 5 fixes × 5 cycles = ~4 min per run. Acceptable.
2. Should failures be fatal (rollback + don't commit) or advisory (commit but warn)? Recommend fatal; the point is to prevent ship. But advisory for the first few runs.
3. Should this apply to Track C (frontend)? Probably needs a parallel frontend-test-count check using `ls frontend/**/*.test.{ts,tsx}` or `vitest --reporter=json --run --collect`. Separate follow-up; start with Python tests.
4. Do we trust the fixer to not rename-to-dodge? The deletion-check catches raw delete. Rename-to-dodge (test_foo.py → _skipped_foo.py) bypasses deletion-check but is caught by count-decrease check (renamed file has no `test_` prefix so pytest skips it). Good coverage.

---

## Cross-item summary

| Item | Effort | Risk | Leverage | Recommendation |
|------|--------|------|----------|----------------|
| #1 drop per-cycle smoke | 15m | Low | High | **Ship** |
| #2 delete no-progress gate | 10m | Low | Medium | **Ship** |
| #3 inventory breadcrumb | 30m | Low | High | **Ship** |
| #4 Verdict synonyms | 20m | Low | Medium | **Ship** |
| #5 tighten transient patterns | 45m | Low | Medium | **Ship** |
| #6 auto-derive _FIXER_REACHABLE | 10m | Very low | Low | **Ship (mechanical)** |
| #17 graceful_kill helper | 90m | Low | Low | **Defer unless in file** |
| #19 drop peer-filter | n/a | **Unsafe as stated** | n/a | **Reject; strengthen comment instead** |
| #21 test-pass-count delta | 3-4h | Medium | High | **Ship (flagged rollout)** |

**Bundle candidates:** #1, #2, #4, #6 are a single ~1h commit. #3 is standalone. #5 is standalone. #21 is its own PR. #17 defer. #19 reject (audit's analysis in F1.1 already reaches the same conclusion — the peer-filter is load-bearing).

**Main open question for JR:** #19 — I'm flagging that the audit's own F1.1 analysis argues against dropping peer-filter without first moving to per-track worktrees. The cluster doc says "fold peer-filter into the lock" as part of a broader redesign; the simple "drop the filter" interpretation breaks parallelism. Want your read before implementing.
