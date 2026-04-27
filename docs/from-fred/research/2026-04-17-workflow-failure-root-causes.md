---
date: 2026-04-17
scope: autoresearch infrastructure — workflow completion failures
source-runs: 2026-04-16 validation (geo-semrush, competitive-figma, monitoring-shopify) + prior storyboard runs
status: investigation complete (4 passes); 31 root causes recorded; 3 fixed (A, G, U12), 6 infra bugs remaining (Q, V, N, W, R, Y), balance is agent behavior or external
---

# Autoresearch Workflow Failure Root-Cause Analysis

## Summary

Four successive investigation passes surfaced **31 distinct root causes** across the four lanes (geo, competitive, monitoring, storyboard). Three are fixed (A via U12 commit b37cbd7; G via U3/U6/U7). Six are real infrastructure bugs still blocking a clean evolution run (Q, V, N, W, R, Y — ~65 LOC of fixes). The remaining 22 are agent-behavior issues (plan-deferred), external dependencies, or cosmetic.

Each root cause below has its own section with file paths, line numbers, log evidence, consequence, and fix guidance. Sections are ordered A→EE alphabetically. The canonical 31-entry index is at the end of the document.

**Score impact recap:**

| Lane | Fixture | Score | Floor 0.2 | Structural | Root causes affecting it |
|------|---------|-------|-----------|------------|--------------------------|
| GEO | semrush | 0.208 | ✅ (barely) | ✅ | A, F |
| Competitive | figma | 0.434 | ✅ | ✅ | B, E |
| Monitoring | Shopify | 0.0 | ❌ | ❌ (no digest.md) | A |
| Storyboard | Gossip.Goblin | (+39% prior) | ✅ | ✅ | — |
| Storyboard | CookingDaily | n/a | — | — | D |
| Storyboard | TechReview | n/a | — | — | D |
| Storyboard | MrBeast | n/a | — | — | C |

---

### Root Cause A: `is_complete()` naive substring match triggers on instruction text

**Status:** Fixed in commit b37cbd7 (U12).

**Affected lanes:** geo-semrush, monitoring-shopify.

**Before-fix code** (`autoresearch/archive/v006/runtime/config.py:79-86`):

```python
def is_complete(session_dir: Path) -> bool:
    session_md = session_dir / "session.md"
    return session_md.exists() and "## Status: COMPLETE" in session_md.read_text()
```

The `in` check matches the substring anywhere in the file — including when the phrase appears inside an instruction block the agent wrote to itself about a *future* phase.

**Trigger mechanism:**

1. All four session programs (`programs/{geo,monitoring,competitive,storyboard}-session.md`) contain the exact phrase `Set \`## Status: COMPLETE\` in session.md when you have:` (line 149–155 across the four files). This phrase is the completion criterion description the agent reads.
2. During self-planning, the agent writes a "Next Phase" block to its own `session.md` copying this phrase verbatim — e.g. geo line 52: *"Begin REPORT. Create `report.md`, ..., and set `## Status: COMPLETE` only after report creation."*
3. U4 sync step (`_sync_agent_workspace`) copies current_runtime → v006.
4. At the next iteration's `is_complete(session_dir)` check, the substring matches the instruction text.
5. Harness breaks out of the iteration loop, printing "Session complete" — before the agent has actually done the next phase.

**Concrete evidence:**

- `autoresearch/archive/v006/sessions/geo/semrush/session.md` line 6 declares `## Status: OPTIMIZE` (mid-workflow). Line 52 contains the trigger phrase. Old `is_complete` returned True.
- `autoresearch/archive/current_runtime/sessions/monitoring/Shopify/session.md` line 73 contains *"append a `deliver` entry; set `## Status: COMPLETE` in `session.md`. Do not redo completed phases unless a file is missing."* Line 1 declares `## Status: IN_PROGRESS`. Old `is_complete` returned True.
- `/tmp/validation-logs/geo-semrush.log`: iters 1–4 all completed a phase each, iter 5 opened and immediately printed "Session complete" without spawning an agent subprocess.
- Same pattern in `/tmp/validation-logs/monitoring-shopify.log` at iter 8.

**Consequence:**

- GEO finished 3 of 5 phases (discover, competitive, seo_baseline) and wrote 4 optimized pages. Never ran `optimize` (refinement) or `report`. Two dimension zeros (GEO-4 voice-fit, GEO-7 directly-answers-queries) would likely have been addressed by a full-length session because rework passes on those pages are exactly the work the later phases drive.
- Monitoring finished 5 of 6 phases (select_mentions, cluster_stories, detect_anomalies, synthesize, recommend). Never ran `deliver`. **digest.md was never produced.** Structural gate failed.

**Fix** (commit b37cbd7):

```python
def _status_declared(session_dir: Path, status_token: str) -> bool:
    session_md = session_dir / "session.md"
    if not session_md.exists():
        return False
    marker = f"## Status: {status_token}"
    for raw in session_md.read_text().splitlines():
        if raw.lstrip().startswith(marker):
            return True
    return False
```

Real status declarations are always at line start. Instruction text containing the phrase inside backticks or prose is no longer matched.

**Why storyboard Gossip.Goblin didn't trip it:**

Checked `autoresearch/archive/current_runtime/sessions/storyboard/Gossip.Goblin/session.md` — zero occurrences of `## Status: COMPLETE` substring anywhere in the file. The agent never copied the completion phrase into its own `session.md`. Likely because the storyboard program's flow is more linear and the agent didn't write a forward-looking completion note.

---

### Root Cause B: Agent declares COMPLETE prematurely, skipping required phases

**Status:** NOT fixed. Deferred per plan scope boundary ("Agent scope drift is NOT fixed here — let evolution pressure solve it").

**Affected lanes:** competitive-figma.

**Observed sequence** (verified from `results.jsonl` and log):

```
iter 1–7: gather × 7 competitors
iter 8–14: analyze × 7 competitors
iter 15: synthesize × 1 (brief.md produced)
<agent writes ## Status: COMPLETE to session.md>
iter 5 harness start: is_complete=True (legitimate, line-anchored match)
<harness breaks>
post_session: run evaluate_session.py → DISCARD (brief 3047 words > 2000 max)
post_session: downgrade_complete_status: text.replace("## Status: COMPLETE", "## Status: RUNNING", 1)
post_session: append "Completion Guard" note: "Final brief session evaluation is DISCARD; rerun VERIFY before marking COMPLETE."
```

Expected phases per `watchdog.py:TRACKED_PHASE_TYPES["competitive"]`: `{"gather", "analyze", "synthesize", "verify"}`. The agent ran 3 of 4; **verify never ran**.

**Why this happened:**

The fresh-mode override prompt (`runtime/config.py::render_prompt`) tells the agent: *"Complete exactly ONE phase, persist state to files, then stop. Do NOT continue automatically into the next phase after phase completion."* The agent interpreted "stop" after synthesize as "session done, mark COMPLETE" rather than "exit subprocess so the outer loop can spawn the next phase."

**Consequence:**

Even with U12 fix, competitive will still hit this. `is_complete` correctly detects a real COMPLETE declaration. The harness loop has already broken before the post-session evaluator gets a chance to say "rerun VERIFY." By the time `downgrade_complete_status` flips the marker back to RUNNING, no more iterations will run.

**Mitigation options (not applied):**

1. Move the completion evaluator check into the loop itself (architectural — touches plan §5.3 workspace/scorer separation).
2. Change `is_complete` to additionally require a phase-completion ledger in `results.jsonl` (e.g., every TRACKED_PHASE_TYPE must appear at least once). Simple, <10 LOC. Would have caught this.
3. Reword the fresh-mode override to explicitly say "do not mark Status: COMPLETE until all phases finished."

Option 2 is the least invasive; deferred per plan.

---

### Root Cause C: Backend API timeouts block phases

**Status:** External dependency failure. Not an infra bug in the autoresearch layer.

**Affected lanes:** storyboard-MrBeast.

**Observed sequence** (from `sessions/storyboard/MrBeast/results.jsonl`):

- iter 1: `select_videos` — `GET /v1/creators/youtube/MrBeast/videos?limit=50 timed out with no body after 60s; profile cache 404; lowercase videos endpoint timed out after 15s`. Fallback to `same_runtime_archive_fallback`.
- iter 2: `analyze_patterns` — recovered from pattern cache.
- iter 3: `plan_story` — 5 plans kept.
- iter 4: `ideate` — 2 storyboards produced; `"note":"backend returned readable mock storyboard snapshot with one scene"`.
- iter 5 onward (phase GENERATE_FRAMES): blocked — backend couldn't generate frames.
- Final session.md: `## Status: BLOCKED` `## Phase: GENERATE_FRAMES`.

**Consequence:**

Session marked BLOCKED. Artifacts from iter 1–4 remain but the lane can't complete without backend frame generation. This is a dependency on the video-intelligence frame-generation service which is not part of this plan's scope.

**Mitigation options:** None in this repo. Fix is in the video-intelligence backend.

---

### Root Cause D: Claude/Codex CLI rate limits

**Status:** External quota failure. Not a repo bug.

**Affected lanes:** storyboard-CookingDaily, possibly storyboard-TechReview.

**Evidence** (`sessions/storyboard/CookingDaily/logs/iteration_00*.log`):

```
You've hit your limit · resets 11pm (Europe/Warsaw)
```

All three iteration logs are 53 bytes — same message. The agent subprocess (Claude Code CLI in this case) was hitting a subscription rate limit.

**TechReview** iteration logs are 0 bytes each across iter 1–4. Agent subprocess failed to write ANY output. Possible causes: (a) same rate limit without printing a message, (b) codex binary crash at startup, (c) prompt/cwd error preventing subprocess start. Insufficient evidence to pinpoint further without a rerun.

**Consequence:**

- CookingDaily: 0 phases completed, `NOT_STARTED` status.
- TechReview: 1 phase result.jsonl entry total, stuck at `ANALYZE_PATTERNS` without completing anything.

**Mitigation options:** Rerun after quota reset, or switch backend via `AUTORESEARCH_SESSION_BACKEND`.

---

### Root Cause E: Agent ignores program's explicit quality constraints

**Status:** Agent-behavior; deferred.

**Affected lanes:** competitive-figma.

**Observed constraint violation:**

Program `programs/competitive-session.md` specifies a brief word budget. `results.jsonl` last entry:

```json
{"type": "structural_gate", "iteration": 15, "status": "fail",
 "failures": ["Brief is 3047 words (max 2000)"]}
```

Agent wrote a 3047-word brief despite the program explicitly saying 2000-word maximum. Post-session evaluator correctly flagged DISCARD, but the agent had already self-marked COMPLETE (Root Cause B).

**Same pattern risk on other lanes:**

- Monitoring digest target is ~2,500 words (program MON-8 criterion). If the agent runs long, no structural check catches word-count violations today.
- Geo pages have unstated length expectations. No structural gate enforces.

Word-count structural checks exist only for competitive brief. They are implemented ad-hoc, not systematically.

---

### Root Cause F: Agent scope drift — self-verification loops consume iteration budget

**Status:** Agent-behavior; deferred.

**Affected lanes:** geo-semrush.

**Observed** (`results.jsonl` iter 3):

```
{"iteration":3,"type":"seo_baseline","status":"completed",...}
{"iteration":3,"type":"structural_gate","status":"fail"}
× 3 more
{"iteration":3,"type":"structural_gate","status":"pass"}
× 7 more
```

After completing `seo_baseline`, the agent ran 12 `structural_gate` self-checks within the same iteration — 4 fails then 8 passes. These entries consume wall-clock time and add results.jsonl entries but make no forward progress. `structural_gate` is not in `watchdog.py:TRACKED_PHASE_TYPES["geo"]`, so it doesn't count for phase-event detection. But my U5 stall counter sees new file counts in subdirs (optimized/*.md being rewritten) and correctly does NOT stall — so the agent spends budget on self-verification noise until the is_complete bug (Root Cause A) cuts it off early.

**Effect on score:**

Had the agent spent that wall-clock time on a proper `optimize` refinement pass driven by evaluator feedback, dimensions GEO-4 (voice fit) and GEO-7 (directly-answers-queries) might not have scored zero. This is speculation, but the dimension-level evaluator feedback would have surfaced exactly those deficiencies.

---

### Root Cause G: Stale session dirs left from earlier launches pollute fresh runs

**Status:** Fixed in commit 92eb9f3 (U3) + commit 159c6ff (U6/U7).

**Affected lanes:** storyboard (all), pre-validation runs.

**Evidence:**

- Before U3, `current_runtime/sessions/storyboard/{CookingDaily,TechReview,MrBeast}/` persisted across fresh runs. CookingDaily's session.md shows `## Status: NOT_STARTED` — template default — yet the dir existed with 3 empty iteration logs. Those logs were from an earlier session that never wrote through.
- MrBeast shows `iter=0` (no logs/iteration_*.log files) but 9 `results.jsonl` entries and 5 stories — artifacts from a prior run that persisted.

**Fix** (U3): on fresh start, `shutil.rmtree(current_runtime_session_dir, ignore_errors=True)` before any agent subprocess runs.

**Remaining gap:** U3 only cleans the current lane's dir. Other lanes' stale dirs persist. Acceptable because they don't affect the active lane's score.

---

---

## Deep-dive findings (added after broader sweep)

Second-pass investigation surfaced twelve additional root causes. Several are infrastructure bugs the first pass missed.

### Root Cause H: `apply_patch` verification fails against mid-iteration file state

**Status:** Agent behavior / tooling drift. Not fixed.

**Affected lanes:** geo-semrush (iter 4, two failures), competitive-figma (iter 1, one failure).

**Evidence** (`sessions/geo/semrush/logs/iteration_004.log:17873`):

```
2026-04-16T19:53:29Z ERROR codex_core::tools::router:
error=apply_patch verification failed: Failed to find expected lines in
/Users/jryszardnoszczyk/Documents/GitHub/freddy/autoresearch/archive/v006/sessions/geo/semrush/optimized/site-audit.md
```

The agent read a file, composed a diff patch against remembered context, but by the time the patch was applied the file had changed (likely from the agent's own earlier write in the same iteration). Tool retries consume tokens and wall time.

**Important architectural side-effect:** the error message reveals the agent writes to **`v006/sessions/...`** via absolute-path diffs, NOT to its cwd `current_runtime/sessions/...`. See Root Cause T below for the full architectural finding.

### Root Cause I: Fresh-mode override prompt drives premature COMPLETE

**Status:** Architectural. Deferred.

**Affected lanes:** competitive-figma (direct), geo/monitoring (indirect via Root Cause A).

**Evidence** — actual prompt text sent to agent (`sessions/geo/semrush/logs/iteration_001.log`):

```
## Fresh Session Override

OVERRIDE: You are running in fresh-session mode for this invocation only.

- Complete exactly ONE phase, persist state to files, then stop.
- Do NOT continue automatically into the next phase after phase completion.
- Your conversation state will not be preserved after this process exits.
- Files remain the only state that survives to the next invocation.
```

The instruction "STOP" is ambiguous. The agent reads this while simultaneously reading the completion criteria ("Set `## Status: COMPLETE` when you have …") and — in competitive's case — declares the session complete after one phase produces a deliverable. Hyperagents §3 fresh-session semantics: `stop` means `exit subprocess`, not `mark session complete`.

**Mitigation suggestion:** reword the fresh-mode override to *"exit the subprocess cleanly so the harness can spawn the next phase — do not mark Status: COMPLETE until every phase under '## Completion' has run."*

### Root Cause J: Agent-side `structural_gate` loop burns iteration budget

**Status:** Agent behavior. Deferred.

**Affected lanes:** geo-semrush (25 self-structural_gate entries in single iteration).

**Evidence** — results type distribution:

```
geo/semrush: {'discover': 1, 'competitive': 1, 'seo_baseline': 1, 'structural_gate': 25}
competitive/figma: {'gather': 7, 'analyze': 7, 'synthesize': 1, 'structural_gate': 1}
monitoring/Shopify: {'select_mentions': 1, ..., 'recommend': 1, 'structural_gate': 7}
```

`structural_gate` shares its name with the harness-side validator (`src/evaluation/structural.py`). But these entries come from an agent-side self-validation pass the program encourages. The agent iterates its own structural check 25 times for geo — tons of wasted wall-clock work producing no progress event.

Naming collision note: two mechanisms both write `type=structural_gate` to results.jsonl; the harness never distinguishes them.

### Root Cause K: Agent dumps huge scraped content inline, not to files

**Status:** Agent behavior. Deferred.

**Affected lanes:** all GEO/competitive runs that used `freddy scrape`.

**Evidence** — single log lines of 12–16 KB containing raw scraped HTML (pricing pages, FAQ blocks, navigation text) pasted verbatim into the codex reasoning stream. Example: `sessions/geo/semrush/logs/iteration_001.log` contains the full Peec AI homepage as one giant JSON string field.

**Effect:** inflates iteration logs to 100–350 KB, pollutes context window, burns tokens the agent could spend on reasoning. Program should say "save scrape output to `pages/{slug}.json` and reference by filename."

### Root Cause L: Date CLI GNU/BSD incompatibility

**Status:** Agent-environment mismatch. Cosmetic.

**Evidence** — `sessions/geo/semrush/logs/iteration_001.log` contains `usage: date [-jnRu] [-I[date|hours|minutes|seconds|ns]]` — BSD date's help page printed because the agent issued a GNU `date -I` flag that BSD date rejects.

**Effect:** agent retries with different syntax. Burns a round trip. Not fatal.

### Root Cause M: External AI visibility services rate-limit or circuit-break

**Status:** External dependency. Can't fix in repo.

**Evidence** — 28 rate-limit hits from `freddy` CLI across the 3 sessions (`10 per 1 minute` message). Visibility clusters for ChatGPT, Perplexity, Gemini returned `rate_limited` or `circuit_open_timeout` on most attempted queries. Geo's `competitors/visibility.json` is marked `"measured": false` because no citation data could be fetched.

**Effect:** GEO-5 citability moat and GEO-2 verifiable facts dimensions score lower because the agent has less measured data to ground content in. This is real signal decay from external constraints, not an internal bug.

### Root Cause N: `session_summary.json` reports wrong productivity metrics

**Status:** Genuine infra bug. Not yet fixed (Unit 10 was dropped per user direction, but this is worse than cosmetic).

**Evidence** (`sessions/geo/semrush/session_summary.json`):

```json
{
  "iterations": {"total": 3, "productive": 0, "blocked": 0, "failed": 0,
                 "skipped": 0, "uncategorized": 3},
  "status": "COMPLETE",
  "exit_reason": "COMPLETE"
}
```

Actual state: 4 iteration logs exist, 15 results.jsonl entries, 4 optimized pages produced, `report.md` written. The summary says **0 productive** iterations and all **3 uncategorized**. Also claims total=3 while there are 4 iteration logs.

**Why this matters:** evolution machinery may read session_summary.json to decide whether a variant "did any work" when allocating compute. A falsely zero-productivity signal misdirects budget allocation.

### Root Cause O: `exit_reason: COMPLETE` lies when session.md never declared COMPLETE

**Status:** Reporting bug, part of Root Cause A's blast radius.

**Evidence:**

- `session_summary.json`: `"status": "COMPLETE", "exit_reason": "COMPLETE"`
- `session.md` (same session): `## Status: OPTIMIZE` (never flipped)

The summarizer reads the harness log ("Session complete") instead of session.md. The log message was produced by the false-positive is_complete match (Root Cause A). Fix for A eliminates this cascade effect, but worth noting the summarizer trusts the wrong signal.

### Root Cause P: Dimension scores returned as positional array with no name mapping

**Status:** Contract weakness. Not a blocker.

**Evidence:**

```json
{
  "domain_score": 0.208,
  "dimension_scores": [0.75, 0.5, 1.0, 0.0, 1.0, 0.125, 0.0, 0.75]
}
```

No `{"GEO-1": 0.75, ...}` mapping. Caller must know the fixed order. Typos or reordering will silently misinterpret results.

**Mitigation:** switch to `dict[str, float]` or add a `dimension_names` array alongside the scores. Non-urgent but fragile.

### Root Cause Q: `freddy evaluate variant` CLI path does NOT update lineage/frontier

**Status:** Real gap. U9 verification from first pass was incomplete.

**Affected workflows:** any ad-hoc scoring (which is how the user has been validating). My own validation scoring in this session produced domain_score values that are nowhere in `lineage.jsonl` or `frontier.json`.

**Current state** (verified 2026-04-17):

- `autoresearch/archive/lineage.jsonl` last entry: `{"id": "v006", "lane": "competitive", "scores": {"geo": 0.0, "competitive": 0.1162, "monitoring": 0.0}, "timestamp": "2026-04-16T12:00:00Z"}` — 10+ hours stale, pre-validation run.
- `autoresearch/archive/frontier.json` geo head = v002 (composite 0.3252), competitive/monitoring heads unset or stale.
- `autoresearch/archive/v006/scores.json`: shows old `composite: 0.1162`, active_domains only `["competitive"]`. Does not include my 0.208 or 0.434 scores.

**Why U9 verification missed this:**

First-pass reasoning: "`evaluate_search` in `evaluate_variant.py` calls `append_lineage_entries` unconditionally at line 1488, so lineage auto-updates."

This is true for the full pipeline path. But the CLI `freddy evaluate variant` takes a DIFFERENT path — it runs `evaluate_session.py` inside `_score_session`, returns a JSON score to stdout, and exits. It never touches `archive_index.append_lineage_entries` or `archive_index.refresh_archive_outputs`.

**Consequence:** evolution machinery cannot see the scores produced by ad-hoc validation. The user has to re-run through `evaluate_variant.py evaluate_search --search-suite=…` to get anything persisted. This is non-obvious and easy to forget.

**Mitigation options (not applied):**

1. Mirror lineage-append logic into the `freddy evaluate variant` CLI (10–15 LOC).
2. Add a post-hoc "promote ad-hoc score to lineage" script.
3. Document the requirement to use `evaluate_variant.py evaluate_search` for any score that should be visible to evolution.

### Root Cause R: Validator `sources` key vs agent `current_sources` mismatch

**Status:** Genuine contract bug. Not yet fixed.

**Evidence:**

- Structural validator (`src/evaluation/structural.py:206`):
  ```python
  raw_sources = select[-1].get("sources", 0)
  ```
- Agent's actual `select_mentions` entry (from `monitoring/Shopify/results.jsonl`):
  ```json
  {"type":"select_mentions", "current_sources":{"reddit":20,"twitter":17,"newsdata":10}}
  ```

The validator looks for key `sources`. The agent writes key `current_sources`. Validator returns 0 → `source_coverage` assertion fails → DQS drops from possibly-perfect to 0.714.

When `digest.md` exists the failure is masked by the `or has_digest` clause. Without digest.md (this run), the failure is visible.

**Mitigation (10 LOC):** validator should accept either `sources` or `current_sources` as the key, or the program should be updated to tell the agent to use `sources`.

### Root Cause S: Agent-mode architectural mismatch — writes go to v006 AND current_runtime

**Status:** Undocumented architectural quirk. Not a bug per se, but invalidates my original U4 design assumption.

**Evidence:**

- GEO/competitive agent subprocess uses `apply_patch` with repo-root relative diff paths (`a/autoresearch/archive/v006/sessions/…`). Writes land in `v006/sessions/…` directly, bypassing cwd. (Logged ERROR output in iter_004 confirms absolute v006 paths.)
- Monitoring agent uses the `freddy monitor mentions --output` CLI with paths relative to cwd (`sessions/monitoring/Shopify/mentions/...`). Writes land in `current_runtime/sessions/monitoring/Shopify/mentions/...`.

**Implication:**

My U4 sync step (`_sync_agent_workspace: current_runtime → v006`) is necessary ONLY for lanes where the agent uses relative-path tools like `freddy monitor`. For lanes using `apply_patch` (most GEO/competitive writes), the files are already in v006 and the sync is a no-op.

**Side-effect:** the sync's post-session pass still does the right thing (copies any straggler current_runtime files into v006). But the "each iteration commits to canonical" framing in my commit message was partially inaccurate — apply_patch already commits directly to canonical.

**Follow-up needed:** document the dual-write reality or enforce one convention. Without this, future changes to sync logic can easily cause file-collision bugs.

### Root Cause T: Stale session directories with empty `results.jsonl` pollute scorer inputs

**Status:** Related to Root Cause G, surfaced by the investigation sweep.

**Evidence** — `autoresearch/archive/v006/sessions/` has dirs for 9 fixtures (3 per lane), but only 3 were launched in this validation:

```
EMPTY: v006/sessions/competitive/canva/results.jsonl
EMPTY: v006/sessions/competitive/miro/results.jsonl
EMPTY: v006/sessions/geo/ahrefs/results.jsonl
EMPTY: v006/sessions/geo/moz/results.jsonl
EMPTY: v006/sessions/monitoring/Lululemon/results.jsonl
EMPTY: v006/sessions/monitoring/Notion/results.jsonl
```

These 6 empty sessions remain from earlier launches. `init_session` touched `results.jsonl` (creating empty files) but the sessions never ran. They will break scorer runs if anyone tries `freddy evaluate variant geo v006/sessions/geo/ahrefs` because structural will fail with zero results.

U3 cleanup only purges the lane under current launch. Other lanes' empty session dirs stick around until someone deletes them.

### Root Cause U: Agent scrape-only output is not persistable to canonical because current_runtime monitoring session wrote `.txt` siblings to `.json` artifacts

**Status:** Data hygiene issue.

**Evidence** (monitoring/Shopify/mentions/):

```
prior-digests.json          (latest, 21:37)
prior-digests.txt           (stale, 21:30, only in v006)
summary-2026-04-06_2026-04-13.json      (21:37)
summary-2026-04-06_2026-04-13.txt       (21:30, only in v006)
week-2026-03-30_2026-04-06.json         (21:30, stale prior week)
week-2026-04-06_2026-04-13.json         (21:37, current)
```

The `.txt` files are artifacts from an older agent attempt using a different file format. My sync only copies FROM current_runtime TO v006, so it couldn't remove these (they weren't in current_runtime during the validation run). Scorers ignoring non-JSON paths are fine, but structural validator's file-set assumptions may be affected.

**Also visible:** both the target-week file (`week-2026-04-06_2026-04-13.json`) AND the prior-week file (`week-2026-03-30_2026-04-06.json`) exist. Agent correctly pulled prior week for delta framing, but this wasn't my sync's doing — the agent wrote via `freddy monitor mentions --date-from` for both windows.

---

*(Intermediate root-cause indexes from earlier passes removed to avoid drift. See the Complete root cause index at the end of this document for the canonical 31-entry list.)*

**One-line summary:** besides the already-fixed is_complete bug (A), the three real infra bugs still blocking a clean evolution run are **Q (lineage not updated by CLI scoring), R (validator key mismatch on sources), and N (session_summary productivity metrics lie)**. Each is 5–15 LOC. The rest is agent behavior or external.

---

## Third-pass findings (metrics pipeline, post-session scripts)

### Root Cause V: Metrics written to `current_runtime/metrics/` but consumed from `v006/metrics/`

**Status:** **Major infra bug.** Blocks metrics-driven evolution signals.

**Evidence:**

- `summarize_session.py` is run via harness `_run_script()`, and `SCRIPT_DIR = harness.ARCHIVE_CURRENT_DIR` (= `current_runtime`). So `python3 current_runtime/scripts/summarize_session.py …` executes.
- Inside the script (line 149-152):
  ```python
  archive_root = Path(__file__).resolve().parent.parent
  metrics_dir = archive_root / "metrics"
  metrics_file = metrics_dir / f"{domain}.jsonl"
  ```
- `__file__.parent.parent` when executing `current_runtime/scripts/summarize_session.py` → `current_runtime`. So metrics land in `current_runtime/metrics/geo.jsonl`.
- But `archive_index.py:198-200` reads metrics from `variant_dir/metrics/`. `variant_dir = v006` during evaluation. So the reader looks at `v006/metrics/*.jsonl` — a completely different location.

**Consequence:** Metrics accumulate in `current_runtime/metrics/` but no downstream consumer reads from there. `v006/metrics/` is stale (last entry 2026-04-14, before my runs). Variant traces surfaced to meta-agent prompts via `prepare_meta_workspace` include the `v006/metrics/*.jsonl` files, but those files don't reflect recent runs.

**Verified:**

```
current_runtime/metrics/geo.jsonl       Apr 16 22:01  (has today's geo entry, iterations_productive=0)
v006/metrics/geo.jsonl                  Apr 16 13:09  (stale, last entry 2026-04-14)
```

**Fix (10 LOC):** either write metrics to `v006/metrics/` explicitly (resolve via harness `PARENT_VARIANT_DIR` or equivalent), or add `metrics/` to the `_sync_agent_workspace` copy list so current_runtime → v006 mirroring also covers metrics.

### Root Cause W: `summarize_session.py` status-bucket map misses `completed`, `fail`, `pass`

**Status:** Reporting bug. Misreports productivity.

**Evidence** (`summarize_session.py:91-95`):

```python
bucket = ("productive" if s in ("complete", "kept", "done")
          else "blocked" if s == "blocked"
          else "failed" if s in ("failed", "error")
          else "skipped" if s == "skipped"
          else "uncategorized")
```

The map accepts `complete` but NOT `completed` (past participle). Agent writes:

- geo: 3× `status: completed` → all bucket as `uncategorized` → `productive=0`
- competitive: all `status: done` → `productive=15`
- monitoring: no `iteration` field at all (different bug path) → `productive=0`
- Also `structural_gate` entries with `status: pass` or `status: fail` → uncategorized

**Consequence:** geo's session_summary reports `iterations_productive: 0` even though every iteration completed its phase successfully. Downstream consumers (metrics JSONL, evolution prompts) see zero productivity and may wrongly penalize the variant.

**Fix (5 LOC):** add `completed` to the productive set. Consider normalizing status values at logging time (e.g., agent always writes `done`) or at summarization time (strip `-ed` suffix).

### Root Cause X: `generate_report.py` referenced but doesn't exist

**Status:** Dead code path. Guarded by `if script.exists()`, so non-fatal.

**Evidence** (`runtime/post_session.py:130-132`):

```python
report_script = script_dir.parent.parent / "configs" / config_dir_name(domain) / "scripts" / "generate_report.py"
if report_script.exists():
    run_subprocess(["python3", str(report_script), str(session_dir), "--skip-pdf"])
```

`ls autoresearch/archive/v006/configs/*/scripts/generate_report.py` → no matches. The `configs/` directory structure doesn't have `generate_report.py` anywhere.

**Consequence:** the intended per-domain report generation step is silently skipped for every session. The `--skip-pdf` flag suggests there was PDF-generation logic that got removed but the hook kept. No `report.md` artifact is produced by this path (the agent's own REPORT phase produces `report.md` separately for geo).

**Fix:** either restore the script or remove the dead hook call.

---

*(Stale intermediate index from third pass removed. Canonical list is the Complete root cause index at the end of this document.)*

---

## Fourth-pass findings

### Root Cause Y: Multiturn mode's stall detection still uses OLD progress semantics

**Status:** Regression from U5 scope. Multiturn bypasses the fix.

**Affected lanes:** any lane run with `--strategy multiturn` (default for some code paths).

**Evidence:**

- U5 (commit 6ccfe49) updated `autoresearch/harness/stall.py:state_changed` with the "new phase type or file growth only" semantics.
- But multiturn mode uses `autoresearch/archive/v006/scripts/watchdog.py::take_progress_snapshot` + `ProgressSnapshot.changed_from`, which still checks `results_lines: int, subdir_counts: tuple`:

  ```python
  @dataclass(frozen=True)
  class ProgressSnapshot:
      results_lines: int
      subdir_counts: tuple[int, ...]
      def changed_from(self, other) -> bool:
          return other is None or self != other
  ```

  Any new line in `results.jsonl` (even structural_gate noise) or any file count change resets stall. Exactly the bug U5 was meant to kill.

**Consequence:** multiturn sessions still burn budget on verification loops that fresh mode now escapes.

**Fix (10 LOC):** port the `_read_phase_types`+ strict-growth logic from `harness/stall.py` into `ProgressSnapshot`, or have multiturn call `state_changed()` instead of `changed_from()`.

### Root Cause Z: Agent writes narrative text claiming actions it never executed

**Status:** Agent behavior. Telemetry pollution.

**Affected lanes:** monitoring-Shopify.

**Evidence:** `sessions/monitoring/Shopify/session.md` and `findings.md` contain the literal text:

```
- Digest persisted via `freddy digest persist ef702c19-9849-59bd-a2e4-74a25dba81d1 --file synthesized/digest-meta.json`
```

This appears 5 times across the monitoring session. BUT: the actual command was never run. `digest-meta.json` doesn't exist. `freddy digest list` backend query would return no new entry for this session.

The agent was hallucinating a past action in its own state file. When a later iteration reads session.md, it sees "Digest persisted" and believes the phase is done — skipping the actual `deliver` phase. Compounds Root Cause B.

**No simple fix** — this is LLM hallucination in plain English, indistinguishable from real completion without cross-checking the filesystem.

**Mitigation suggestion:** structural validator could reject session.md content mentioning "Digest persisted" unless `digest-meta.json` file exists. Domain-specific, ~5 LOC.

### Root Cause AA: Lock file not explicitly released

**Status:** Minor hygiene issue. Relies on OS cleanup.

**Evidence** (`autoresearch/harness/util.py:acquire_lock`):

```python
fd = os.open(str(lock_path), os.O_CREAT | os.O_WRONLY)
fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
return fd
```

`lock_fd` is stored in `run_domain_fresh`/`run_domain_multiturn` locals. When function returns, Python GC closes the fd, releasing the lock. No explicit `fcntl.LOCK_UN` or `os.close(lock_fd)`.

**Observed behavior:** no lock files left in `/tmp/*.lock` after validation runs (verified). Works in practice.

**Risk:** if a process is paused via SIGSTOP or if the Python interpreter delays GC (long-lived parent process, reference cycles), the lock could persist across the logical session boundary.

**Fix (5 LOC):** add `fcntl.flock(lock_fd, fcntl.LOCK_UN); os.close(lock_fd)` in a `try/finally` block around the session body.

### Root Cause BB: Subprocess stdout gets buffered, empty logs on kill

**Status:** Logging hygiene bug. Masks agent output when sessions abort.

**Evidence** (`sessions/storyboard/TechReview/logs/iteration_00{1-4}.log`):

All four iteration logs are 0 bytes. The agent process ran but wrote nothing visible — buffered in stdout, never flushed to disk because the subprocess was killed or crashed before the final flush.

**Contrast:** CookingDaily's logs are 53 bytes each — small but present, contain the Claude rate-limit message. So logging DOES work when the subprocess gets a normal line of output.

**Likely cause:** codex CLI subprocess had buffered output that wasn't flushed when the process ended abnormally. The harness captures stdout via `subprocess.Popen(stdout=log_file)` — no `bufsize=0` or PYTHONUNBUFFERED.

**Consequence:** for any session that crashes or is force-killed mid-flight, we lose all diagnostic output. Makes post-hoc investigation of "why did it fail" impossible.

**Fix (2 LOC):** add `bufsize=0` to `subprocess.Popen` calls in `harness/agent.py`, or export `PYTHONUNBUFFERED=1` in the subprocess env.

### Root Cause CC: No global archived_sessions cleanup

**Status:** Storage growth. Will eventually fill disk.

**Evidence:**

- `autoresearch/archive/v006/archived_sessions/` has 3 entries totaling 9.5 MB from today alone.
- No retention policy. Every fresh-mode launch archives the previous session, creating a new dir.
- Over an evolution run of 50 variants × 4 lanes × 3 fixtures = ~600 archived session dirs potentially.

**Current state:** fine, but would saturate a 100GB disk after ~50k archived sessions.

**Mitigation:** add retention policy (keep last N or keep <30 days) to the fresh-cleanup logic in `init_session`.

### Root Cause DD: `AUTORESEARCH_FIXTURE_ID` env var only set by `evaluate_variant.py`, not by bare `run.py` invocations

**Status:** Lock-key fragmentation. Parallel same-domain runs collide.

**Evidence:**

- `evaluate_variant.py:385`: `env["AUTORESEARCH_FIXTURE_ID"] = fixture.fixture_id` — sets the fixture ID so `acquire_lock` can key per-fixture.
- `autoresearch/archive/v006/run.py`: never sets `AUTORESEARCH_FIXTURE_ID`.

**Consequence:** if a user launches two `run.py --domain geo <client>` invocations for different clients simultaneously (e.g., semrush and ahrefs in parallel), the lock keys would use `domain-session-{client}.lock`. Different clients get different locks (safe). BUT: if somehow two runs of the SAME client happen (e.g., a stuck process + a user retry), the lock would only use `domain-session-{client}.lock`, blocking the retry correctly.

Actually this case is handled — per-client lock IS the fallback. The fixture_id keying is just an optimization for evolution. Not a real bug, but worth noting that the code paths use different key strategies.

**Fix (optional, 3 LOC):** standardize lock key strategy or document the difference.

### Root Cause EE: Session.md template variables rendered only on first iteration

**Status:** Documentation gap.

**Evidence** (`run.py:init_session` line 223-230):

```python
if not session_md.exists():
    template = SCRIPT_DIR / "templates" / domain / "session.md"
    if template.exists():
        ...
        session_md.write_text(text)
```

Template is only rendered when session.md is absent (first iteration after fresh-archive). On subsequent iterations, existing session.md is preserved. If the agent corrupts or truncates session.md, there's no mechanism to restore it from template.

**Consequence:** in theory low-severity because the agent is supposed to maintain session.md. In practice: if a crash interrupts a write, session.md could be empty/truncated, and next iteration proceeds with no template.

**Fix:** non-blocking; consider a repair step if session.md is <100 bytes.

---

## Complete root cause index (31 total — canonical)

| # | Cause | Status | Severity | Affected lanes |
|---|-------|--------|----------|----------------|
| A | `is_complete` substring match on instruction text | ✅ Fixed (U12) | Critical | geo, monitoring |
| B | Agent self-declares COMPLETE early, skipping phases | Deferred | High | competitive |
| C | Backend frame-gen API timeouts | External | Medium | storyboard-MrBeast |
| D | CLI rate limits (Claude quota) | External | Medium | storyboard-CookingDaily |
| E | Agent ignores program word budgets | Deferred | Low | competitive |
| F | Agent scope drift: self-verification loops | Deferred | Medium | geo |
| G | Stale session dirs on fresh start | ✅ Fixed (U3/U6/U7) | Medium | all pre-validation |
| H | apply_patch verification failures mid-iteration | Deferred | Low | geo, competitive |
| I | Fresh-mode prompt drives premature COMPLETE | Deferred | High | competitive direct, others indirect |
| J | Agent-side structural_gate loop burns iteration budget | Deferred | Medium | geo |
| K | Agent dumps scraped content inline in logs | Deferred | Medium | geo, competitive |
| L | Date CLI GNU/BSD mismatch | Cosmetic | Low | geo |
| M | External AI visibility rate-limits (ChatGPT/Perplexity/Gemini) | External | High | geo, competitive |
| N | `session_summary.json` wrong productivity counts | ⚠️ Fix needed | High | all |
| O | `exit_reason: COMPLETE` lies when session wasn't | Cascaded from A | Low | geo |
| P | Dimension scores as positional array, no name map | Low | Low | scoring API |
| Q | `freddy evaluate variant` CLI doesn't update lineage | ⚠️ **Fix needed** | **Critical** | all ad-hoc scoring |
| R | Validator `sources` vs agent `current_sources` key | ⚠️ Fix needed | High | monitoring |
| S | Writes split v006/current_runtime by tool type | Architectural | Low | mixed |
| T | Empty `results.jsonl` in 6 stale session dirs | Partial G fix | Medium | all 4 lanes |
| U | `.txt` legacy siblings in monitoring mentions/ | Data hygiene | Low | monitoring |
| V | Metrics written to current_runtime but read from v006 | ⚠️ **Fix needed** | **Critical** | all |
| W | `summarize_session.py` status bucket misses `completed` | ⚠️ Fix needed | High | geo primarily |
| X | `generate_report.py` referenced but file doesn't exist | Dead code | Low | all |
| Y | Multiturn watchdog still uses old stall semantics | ⚠️ Fix needed | Medium | any multiturn run |
| Z | Agent hallucinates narrative actions never executed | Deferred | High | monitoring |
| AA | Lock file not explicitly released (relies on GC) | Hygiene | Low | all |
| BB | Subprocess stdout buffered, logs empty on kill | Logging gap | Medium | storyboard-TechReview |
| CC | No `archived_sessions/` retention policy | Storage growth | Low | all |
| DD | `AUTORESEARCH_FIXTURE_ID` keying difference between `run.py` and `evaluate_variant.py` | Minor | Low | parallel runs |
| EE | Session.md template rendered only on first iteration | Documentation | Low | all |

All 31 issues have a detailed section earlier in this document (search for `### Root Cause <ID>:`) with evidence, consequence, and fix guidance.

## Consolidated fix plan

### Priority 1: Critical infra bugs blocking evolution visibility (~25 LOC)

- **Q**: Make `freddy evaluate variant` CLI call `archive_index.append_lineage_entries` + `refresh_archive_outputs` after scoring succeeds. OR document that the CLI path must be followed by `evaluate_variant.py evaluate_search` to persist.
- **V**: Resolve metrics directory to `v006/metrics/` (the variant dir, not current_runtime). Simplest fix: pass `variant_dir` as arg to `summarize_session.py` and have it write there.

### Priority 2: Signal correctness (~25 LOC)

- **N+W**: Accept `completed` and other past-tense statuses in `summarize_session.py` bucket map. Normalize at log time or summarize time.
- **R**: Validator accepts both `sources` and `current_sources` keys for monitoring source_coverage.
- **Y**: Port U5 stall-semantics fix into multiturn's `ProgressSnapshot`.

### Priority 3: Cleanup (~15 LOC)

- **T**: Extend U3 fresh-cleanup to sweep ALL lanes' empty session dirs, not just the active lane's.
- **X**: Remove the `generate_report.py` hook from post_session_hooks.
- **AA**: Explicit `fcntl.flock(LOCK_UN)` + `os.close` on lock fd in try/finally.
- **BB**: `bufsize=0` or `PYTHONUNBUFFERED=1` for agent subprocess.

### Priority 4: Agent behavior (plan-deferred)

B, E, F, H, I, J, K, Z — all require either prompt engineering, architectural changes to COMPLETE detection, or additional structural validators. The plan says evolution pressure will drive these down over time.

### Priority 5: External dependencies

C (frame-gen API), D (CLI rate limits), M (AI visibility rate-limits) — can't fix in repo. Workarounds: switch to codex backend, scale back external API calls, wait for quota reset.

### Priority 6: Won't fix

L (date CLI), O (cascaded from A), P (dimension array), S (architectural quirk), U (legacy .txt), CC (storage), DD (lock keying), EE (template).

**Total P1-P3 fix budget: ~65 LOC across 3 commits.**

**Rerun recommendation:** Rerun geo + monitoring with the U12 fix. Both should now run their full iteration budget, and monitoring should produce digest.md. Competitive will still exit early via Root Cause B — expect a similar ~0.4 score but structural pass. Storyboard fixtures need separate handling (rate-limit reset for CookingDaily; backend fix for MrBeast).

---

## References

- Plan document: `docs/plans/2026-04-16-002-fix-autoresearch-infrastructure-bugs-plan.md`
- Validation logs: `/tmp/validation-logs/{geo-semrush,competitive-figma,monitoring-shopify}.log`
- Related prior research: `docs/research/2026-04-16-storyboard-mock-removal-and-evolution-readiness.md`
- Hyperagents paper: https://arxiv.org/pdf/2603.19461
- Meta-Harness paper: https://arxiv.org/pdf/2603.28052
