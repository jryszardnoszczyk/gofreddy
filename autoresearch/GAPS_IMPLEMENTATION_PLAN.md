# Implementation Plan: Addressing 11 Autoresearch Gaps

## Guiding Principles

1. **Raw traces > summaries.** Meta-Harness ablation: raw traces score 56.7, scores-only 41.3, scores+summary 38.7. Summaries can actually hurt by compressing away diagnostic detail. Expose raw data AND provide a convenience digest.
2. **Occam's razor.** Simplest implementation that captures the value. ~625-800 LOC total across all 11 gaps (including helper functions, imports, dataclass extensions, and shell/template changes not shown in pseudocode). Gap 4 simplified to meta.md hint (data already in index.json); Gap 1 deferred to placeholder (no production data exists yet).
3. **Staged rollout.** Fix safety gates first (cheap, prevent damage), then feedback loops (high ROI), then efficiency (saves money), then intelligence (needs data).
4. **Paired evaluation.** Always compare variant against parent on the same fixtures. Paired comparison dramatically reduces variance.

## Dependency Graph

```
Phase 1 (before first evolution run)
  Gap 30 (L1 import check) ──┐
  Gap 6  (regression_floor) ──┼── Cluster A: Safety gates in evaluate_variant.py
                               │
  Gap 2  (eval traces) ───────┼── Cluster B: Meta agent visibility
  Gap 26 (failure analysis) ──┘   (shared eval_digest infrastructure)

Phase 2 (after first 5-10 runs)
  Gap 17 (staged eval) ───────┐
  Gap 18 (eval variance) ─────┼── Cluster C: Evaluation quality
  Gap 28 (eval caching) ──────┘   (all modify evaluate_search loop)

Phase 3 (after 15-20+ variants)
  Gap 3  (fixture expansion) ─┐
  Gap 4  (strategy extraction)┼── Cluster D: Meta agent intelligence
  Gap 7  (evaluator drift) ───┤
  Gap 1  (production intel) ──┘
```

**Key insight:** Gaps 17, 18, and 28 all modify the `evaluate_search()` loop in `evaluate_variant.py`. They should be designed together even if implemented incrementally.

## File Change Map

| File | Gaps touching it | Nature of changes |
|------|-----------------|-------------------|
| `evaluate_variant.py` | 2, 6, 17, 18, 28, 30 | Most-modified file. Safety gates, loop restructuring, digest generation |
| `archive_index.py` | 2, 26, 28 | Meta workspace enrichment |
| `evolve.sh` | 2, 1, 26 | Template substitutions, workspace prep calls |
| `meta.md` (template) | 2, 1, 4, 26 | New substitution variables, strategy hint |
| `eval_suites/search-v1.json` | 3 | Expand fixture pool, add rotation metadata |
| ~~`synthesize_production_intelligence.py`~~ | 1 | Deferred — placeholder in evolve.sh only until production data exists |

---

## Phase 1: Safety Gates + Feedback Loop

**Goal:** Prevent damage and make every mutation informed. Do before first `evolve.sh run`.

### Gap 30: L1 Import Check

**What:** Add `python3 -c "import run"` to `layer1_validate()` after syntax checks.

**Where:** `evaluate_variant.py:384-411`, after the shell syntax check block (line 404).

**Implementation:**
```python
# After existing bash -n check (line 404), add:
import_check = subprocess.run(
    ["python3", "-c", "import run"],
    capture_output=True, text=True, timeout=15,
    cwd=str(variant_dir),
    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
)
if import_check.returncode != 0:
    print(f"L1 FAIL: run.py import: {import_check.stderr.strip()}", file=sys.stderr)
    return False
```

**LOC:** ~10
**Risk:** False positives from dynamic imports. Mitigate with `timeout=15` and testing against v001.

---

### Gap 6: Regression Floor Enforcement

**What:** Compare per-fixture scores against parent. Block promotion if any fixture regresses beyond its `regression_floor`.

**Where:** `evaluate_variant.py`, as a **new standalone function** called from `evaluate_search()` after scoring, before the lineage entry is created.

**Note:** The existing `_search_promotion_summary()` uses keyword-only args `(*, variant_entry, baseline_entry, search_suite_manifest, policy)` — a completely different interface. Do NOT modify it. Instead, create a separate regression check that operates on scored_fixtures directly.

**Implementation:**

New function `_check_regression_floors()`:

```python
def _check_regression_floors(
    scored_fixtures: dict[str, list[dict]],
    parent_scored_fixtures: dict[str, list[dict]] | None,
) -> list[dict]:
    """Return list of regressions if any fixture violates its floor, else empty list."""
    if not parent_scored_fixtures:
        return []

    regressions = []
    for domain, fixtures in scored_fixtures.items():
        parent_fixtures = parent_scored_fixtures.get(domain, [])
        parent_by_id = {pf["fixture_id"]: pf for pf in parent_fixtures}
        for fix in fixtures:
            parent_fix = parent_by_id.get(fix.get("fixture_id"))
            if not parent_fix:
                continue  # New fixture, no regression possible
            floor = fix.get("regression_floor", 0.0)
            delta = fix["score"] - parent_fix["score"]
            if delta < -floor:
                regressions.append({
                    "fixture": fix["fixture_id"],
                    "domain": domain,
                    "delta": round(delta, 4),
                    "floor": floor,
                })
    return regressions
```

Call from `evaluate_search()` after `_aggregate_suite_results()` and before creating the lineage entry. If regressions are found, include them in the promotion summary dict passed to `_search_promotion_summary()`.

**Data source for parent scores:** Load parent's `scores.json` from `archive/{parent_id}/scores.json` (the `domains` key contains per-fixture results). Parent ID available via `os.environ.get("EVOLUTION_PARENT_ID")`.

**LOC:** ~30
**Risk:** Could block legitimate improvements that trade off one fixture for another. Mitigate: the floor is small (0.02-0.03) — only blocks significant regressions.

---

### Gap 2: Eval Traces → Meta Agent + Gap 26: Failure Analysis

**What:** Stop hiding evaluation data from the meta agent. Expose raw session traces for the parent variant AND generate a structured eval digest.

**Key insight from Meta-Harness ablation:** Raw traces (56.7) >> scores+summary (38.7). The digest is a convenience index — the raw traces must also be accessible.

**Changes needed (4 locations):**

#### 1. Generate eval_digest.md after scoring (`evaluate_variant.py`)

New function after `_aggregate_suite_results()` (~line 1250):

```python
def _write_eval_digest(
    variant_dir: Path,
    scored_fixtures: dict[str, list[dict]],
    smoke_summary: dict,
    aggregated: dict,
) -> Path:
    """Write structured evaluation digest for meta agent consumption."""
    digest_path = variant_dir / "eval_digest.md"
    lines = [
        f"# Evaluation Digest for {variant_dir.name}\n",
        f"## Summary",
        f"- Composite: {aggregated['composite']:.3f}",
        f"- Fixtures with output: {smoke_summary.get('fixtures_with_output', '?')}/{smoke_summary.get('fixtures_total', '?')}",
        f"- Total time: {aggregated.get('wall_time_seconds', 0):.0f}s\n",
        "## Per-Fixture Results",
        "| Domain | Fixture | Score | Grounding | Structural | Rework | Time |",
        "|--------|---------|-------|-----------|------------|--------|------|",
    ]
    for domain, fixtures in scored_fixtures.items():
        for f in fixtures:
            lines.append(
                f"| {domain} | {f.get('fixture_id','')} | {f.get('score',0):.3f} "
                f"| {'Pass' if f.get('grounding_passed') else 'FAIL'} "
                f"| {'Pass' if f.get('structural_passed') else 'FAIL'} "
                f"| {f.get('rework_count', '?')} "
                f"| {f.get('wall_time_seconds',0):.0f}s |"
            )

    # Dimension score breakdown for failed fixtures
    lines.append("\n## Criterion Failures")
    for domain, fixtures in scored_fixtures.items():
        for f in fixtures:
            if f.get("score", 1) < 0.5:
                dims = f.get("dimension_scores", [])
                failed = [d for d in dims if d.get("score", 1) < 0.5]
                if failed:
                    lines.append(f"- **{f['fixture_id']}:** " + ", ".join(
                        f"[{d['name']}: {d.get('score',0):.2f}]" for d in failed
                    ))

    # Failure digest (Gap 26)
    lines.append("\n## Recent Failure Patterns")
    failures_log = variant_dir.parent / "failures.log"
    if failures_log.exists():
        recent = []
        for line in failures_log.read_text().strip().split("\n")[-20:]:
            try:
                recent.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        if recent:
            reason_counts = {}
            for entry in recent:
                r = entry.get("reason", "unknown")
                reason_counts[r] = reason_counts.get(r, 0) + 1
            for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
                lines.append(f"- {reason}: {count} variants in last {len(recent)}")
        else:
            lines.append("- No recent failures")
    else:
        lines.append("- No failure log found")

    digest_path.write_text("\n".join(lines))
    return digest_path
```

Call this after `_aggregate_suite_results()` in `evaluate_search()`.

#### 2. Ensure meta agent knows where session traces are (`archive_index.py` / `evolve.sh`)

**Important:** `prepare_meta_workspace()` uses `shutil.copytree()` at line 226 with NO `ignore` parameter — session directories are **already physically copied** to the meta workspace for all archived variants. The `IGNORED_DIRS` set only affects `_variant_file_map()` (used for diff computation and lane-scoping), not the copytree call. No IGNORED_DIRS change is needed.

The actual fix is simpler:
- Ensure `eval_digest.md` and `scores.json` are present in the parent variant's archive directory (they are, after step 1 above).
- Update `meta.md` to tell the meta agent where to find session traces (they're already in the workspace at `{archive_path}/{parent_id}/sessions/`).
- The meta agent can already `grep` and `cat` these files since it has filesystem tools.

**Note:** `scores.json` is in `IGNORED_FILES` which affects `_variant_file_map` (used by `summarize_variant_diff` for change tracking), not `copytree`. The file IS physically present in the workspace — the meta agent can read it. If needed for diff tracking, remove it from `IGNORED_FILES`.

#### 3. Add eval_digest to meta.md template (`evolve.sh` + `meta.md`)

In `evolve.sh` around line 1030, after scoring completes, copy `eval_digest.md` to the meta workspace root. Add `{eval_digest_path}` substitution to `meta.md`:

```markdown
## Evaluation Evidence

The parent variant's most recent evaluation data is at `{eval_digest_path}`.
Raw session traces are in `{parent_sessions_path}` — grep these for detailed
failure analysis. The digest is a summary; the traces are ground truth.
```

#### 4. Enhance failure logging (`evaluate_variant.py`)

Modify `_ensure_failure_logged()` (line 1176) to accept detail:

```python
def _ensure_failure_logged(
    archive_dir: Path, variant_id: str, reason: str,
    detail: dict | None = None,
) -> None:
    record = {
        "id": variant_id,
        "status": "discarded",
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if detail:
        record["detail"] = detail
    # ... append to failures.log
```

At L1 failure sites, pass the validation error as detail.

**Total LOC for Gaps 2+26:** ~120
**Risk:** Session traces for all archived variants are already in the meta workspace (via copytree). This makes the workspace larger but the meta agent selectively reads via grep/cat, matching Meta-Harness's approach. No additional workspace size increase from these changes — we're just making the meta agent aware of data that's already there.

---

## Phase 2: Evaluation Quality + Efficiency

**Goal:** Make scores reliable and evaluation cost-effective. Do after first 5-10 evolution runs give you baseline data.

**Phase ordering note:** GAPS.md lists Gap 18 (variance) as "before first evolution run" and Gap 17 (staged eval) as "as evolution matures." This plan reorders them because: (a) Gap 17 must come before Gap 18 to offset the 3x cost increase, (b) the first 5-10 runs with single-run scores establish baseline variance data needed to calibrate EVAL_REPEATS, and (c) Gap 18 without baseline data risks committing to 3 runs when 2 might suffice. The tradeoff: early runs use noisier scores, but Phase 1's regression_floor check provides a safety net.

### Gap 17: Staged Evaluation (implement first — reduces cost before Gap 18 adds it back)

**What:** Two-stage evaluation. Stage 1: run 1 canary fixture per domain (4 total). If canary score < threshold, skip remaining fixtures.

**Where:** `evaluate_variant.py`, the fixture iteration loop in `evaluate_search()` (lines 1209-1248).

**Implementation:**

Restructure the loop:

```python
# Stage 1: Canary fixtures (1 per domain, ~15 min)
canary_runs = {}
canary_scores = {}
for domain in DOMAINS:
    canary = fixtures_by_domain[domain][0]  # First fixture is canary
    run = _run_fixture_session(variant_dir, canary, eval_target)
    canary_runs[domain] = run
    if run.produced_output:
        result = _score_session(run, variant_id=variant_id, campaign_id=search_campaign_id)
        canary_scores[domain] = result.get("score", 0.0)
    else:
        canary_scores[domain] = 0.0

# Gate: abort if canaries indicate catastrophic failure
canary_pass_rate = sum(1 for s in canary_scores.values() if s > 0.0) / len(DOMAINS)
if canary_pass_rate < 0.5:  # Less than half of domains produced any output
    print(f"Staged eval: canary pass rate {canary_pass_rate:.0%}, aborting full eval")
    # Write zero scores, return early
    ...

# Stage 2: Remaining fixtures for surviving variant
for domain in DOMAINS:
    remaining = fixtures_by_domain[domain][1:]  # Skip canary
    for fixture in remaining:
        run = _run_fixture_session(variant_dir, fixture, eval_target)
        ...
```

**Canary selection:** First fixture per domain in the manifest. Mark canary fixtures in `search-v1.json` with `"canary": true` for clarity.

**Threshold:** < 50% of domains produce any output = abort. This is conservative — only catches variants that are completely broken, not borderline ones. Hyperagents uses even lower thresholds (succeed on at least 1 task).

**LOC:** ~40
**Compute savings:** ~50-70% for broken variants (skip 8 of 12 fixtures).

---

### Gap 18: Evaluation Variance

**What:** Run each fixture 3 times, take median score per fixture. Use paired comparison for promotion decisions.

**Where:** `evaluate_variant.py`, the fixture iteration loop and `_aggregate_suite_results()`.

**Implementation:**

Best practices research recommends: 3 runs minimum, median for 3 runs. Adaptive approach: 1 run at canary stage (Gap 17), 3 runs at full evaluation stage.

```python
EVAL_REPEATS = 3  # Configurable

# In Stage 2 (after canary passes):
for domain in DOMAINS:
    for fixture in fixtures_by_domain[domain]:
        fixture_runs = []
        for repeat_idx in range(EVAL_REPEATS):
            run = _run_fixture_session(variant_dir, fixture, eval_target)
            if run.produced_output:
                result = _score_session(run, variant_id=variant_id, campaign_id=search_campaign_id)
                fixture_runs.append(result)
            # Move session output before next run (see "Handling session output paths" below)
            src = variant_dir / "sessions" / fixture.domain / fixture.client
            dst = variant_dir / "sessions" / fixture.domain / f"{fixture.client}_run_{repeat_idx}"
            if src.exists():
                shutil.move(str(src), str(dst))

        # Median aggregation
        if fixture_runs:
            scores = sorted(r["score"] for r in fixture_runs)
            median_score = scores[len(scores) // 2]  # Median of 3
            median_result = next(r for r in fixture_runs if r["score"] == median_score)
        else:
            median_result = {"score": 0.0}

        scored_fixtures[domain].append(median_result)
```

**Modify `_aggregate_suite_results()`:** No change needed — it already averages per-fixture scores. The median is computed per-fixture before aggregation.

**Handling session output paths:** `run.py` hardcodes session output to `sessions/{domain}/{client}/`. It cannot be redirected via parameter (run.py is evolvable code inside the variant — adding CLI args creates coupling). The solution is shown in the pseudocode above: after each run completes, `shutil.move` the session directory to an indexed subdirectory (`{client}_run_{i}`) before the next run starts. This avoids modifying run.py and works with any variant's session output convention.

**Cost impact:** 3x evaluation cost for full suite. But combined with Gap 17 (staged eval), broken variants cost 1 canary run only. Net cost increase for good variants: 3x. For a 12-fixture suite at ~5 min/fixture, this goes from ~60 min to ~180 min per variant.

**Cost mitigation:** Only run 3 repeats for Stage 2 fixtures. Canary fixtures (Stage 1) run once — they're just a gate.

**LOC:** ~50
**Risk:** 3x cost. Mitigate with staged eval (Gap 17) and eval caching (Gap 28).

---

### Gap 28: Evaluation Caching for Unchanged Domains

**What:** When a workflow-lane mutation changes only one domain's code, skip evaluation for unchanged domains and reuse parent scores.

**Where:** `evaluate_variant.py` at the start of `evaluate_search()`, plus `archive_index.py` for changed_files computation.

**Implementation:**

```python
# At start of evaluate_search(), before fixture loop:

# 1. Compute what changed
parent_id = (os.environ.get("EVOLUTION_PARENT_ID") or "").strip() or None
if parent_id:
    changed_files, _ = summarize_variant_diff(archive_dir, variant_id, parent_id)
else:
    changed_files = None  # No parent = evaluate everything

# 2. Determine affected domains
if changed_files is not None:
    affected_domains = set()
    for f in changed_files:
        for domain in WORKFLOW_LANES:
            if path_owned_by_lane(f, domain):
                affected_domains.add(domain)
        # If a core file changed, all domains are affected
        if not any(path_owned_by_lane(f, lane) for lane in WORKFLOW_LANES):
            affected_domains = set(DOMAINS)
            break
else:
    affected_domains = set(DOMAINS)

# 3. Load parent scores for unchanged domains
parent_scores = _load_parent_scores(archive_dir, parent_id) if parent_id else None

# 4. In fixture loop, skip unchanged domains:
for domain in DOMAINS:
    if domain not in affected_domains and parent_scores and domain in parent_scores:
        scored_fixtures[domain] = parent_scores[domain]
        print(f"  {domain}: cached from parent {parent_id}")
    else:
        # Run evaluation as normal
        for fixture in fixtures_by_domain[domain]:
            ...
```

**Cache invalidation rules (from best practices research):**
- If ANY core file changed → evaluate all domains (core affects everything)
- If a workflow-lane file changed → evaluate only that domain
- **Protocol compatibility:** Only reuse parent scores if they were computed with the same `EVAL_REPEATS` count. Store `eval_repeats` in `scores.json` alongside results. If parent used 1 run (pre-Gap 18) and current uses 3-run median, invalidate cache and re-evaluate. This prevents mixing measurement protocols in the same comparison.
- Max cache inheritance: 3-5 generations (implement when cache staleness is observed; start without this constraint).

**How to load parent scores:** Read parent's `scores.json` from `archive/{parent_id}/scores.json`. The `domains` key contains per-fixture results.

**LOC:** ~60
**Risk:** Hidden dependencies between domains (shared utility code). Mitigate: if ANY file outside workflow-lane prefixes changes, invalidate all caches. `lane_paths.py` already defines ownership boundaries precisely.

---

## Phase 3: Meta Agent Intelligence

**Goal:** Give the meta agent strategic insight. Do after 15-20+ variants exist in lineage.

### Gap 3: Fixture Pool Expansion

**What:** Expand from 12 fixtures to 20-30, with stratified sampling (2 anchors + 1-2 random per domain per evaluation).

**Where:** `eval_suites/search-v1.json` (content), `evaluate_variant.py` (sampling logic).

**Implementation:**

Extend the manifest format:

```json
{
  "suite_id": "search-v2",
  "rotation": {
    "strategy": "stratified",
    "anchors_per_domain": 2,
    "random_per_domain": 1,
    "seed_source": "variant_id"
  },
  "domains": {
    "geo": [
      {"fixture_id": "geo-semrush-pricing", "anchor": true, ...},
      {"fixture_id": "geo-ahrefs-pricing", "anchor": true, ...},
      {"fixture_id": "geo-moz-homepage", ...},
      {"fixture_id": "geo-hubspot-pricing", ...},
      {"fixture_id": "geo-datadog-pricing", ...},
      ...
    ]
  }
}
```

New function in `evaluate_variant.py`:

```python
def _sample_fixtures(
    fixtures_by_domain: dict[str, list[Fixture]],
    rotation_config: dict,
    variant_id: str,
) -> dict[str, list[Fixture]]:
    """Stratified sampling: anchors + random per domain."""
    rng = random.Random(variant_id)  # Deterministic per variant
    sampled = {}
    for domain, fixtures in fixtures_by_domain.items():
        anchors = [f for f in fixtures if f.anchor]
        pool = [f for f in fixtures if not f.anchor]
        n_random = rotation_config.get("random_per_domain", 1)
        random_picks = rng.sample(pool, min(n_random, len(pool)))
        sampled[domain] = anchors + random_picks
    return sampled
```

**Fixture creation work:** This gap requires creating 15-20 new fixtures (clients/contexts per domain). This is domain work, not code work. Prioritize diversity: different industries, page structures, competitive landscapes, mention volumes.

**LOC:** ~30 (code) + fixture creation effort
**Risk:** Scores become less comparable across variants (different fixtures). Mitigate: anchor fixtures provide consistent signal; aggregate using only anchors for trend tracking.

---

### Gap 4: Cross-Variant Strategy Extraction

**What:** Enable the meta agent to correlate file changes with score improvements across the lineage.

**Where:** `meta.md` template only. No new Python code.

**Implementation:**

The data needed for strategy extraction already exists in the meta workspace:
- `index.json` contains `changed_files`, `diffstat`, and `search_summary` (composite + per-domain scores) for every variant
- `scores.json` per variant contains per-fixture breakdown
- The meta agent has filesystem tools (grep, cat) and can read these files directly

This matches the Meta-Harness pattern: the proposer reads 82 files per iteration and forms its own causal hypotheses about what worked and why. No extraction script needed — the LLM meta agent can do this analysis itself.

Add to `meta.md` template:

```markdown
## Historical Patterns

The archive index at `{archive_path}/index.json` contains `changed_files` and
`search_summary` for every prior variant. Use this to identify which types of
file changes have historically improved or regressed scores. Compare parent-child
pairs to build hypotheses about productive mutation strategies.
```

**LOC:** ~3 (template lines)
**Risk:** The meta agent might not spontaneously perform this analysis. If after 20+ variants the meta agent demonstrably fails to learn from history (repeats unsuccessful mutation patterns), build the extraction script then.

**Fallback:** If needed later, the script design from the original plan (correlating changed_files with score deltas, classifying by file category) remains the right approach at ~80 LOC.

---

### Gap 7: Evaluator Drift Protection

**What:** Monitor the internal evaluator (`evaluate_session.py`) for drift. Track rework rates as a sentinel metric.

**Where:** `evaluate_variant.py`, new check before evaluation.

**Implementation:**

Rather than blocking evaluator changes (which meta.md explicitly encourages), monitor their effect:

```python
def _evaluator_drift_check(variant_dir: Path) -> dict:
    """Detect evaluator changes and compute drift indicators."""
    eval_script = variant_dir / "scripts" / "evaluate_session.py"
    if not eval_script.exists():
        return {"changed": False}

    content = eval_script.read_text()
    indicators = {
        "changed": True,  # Compare hash vs parent
        "pass_threshold": _extract_value(content, r"DEFAULT_PASS_THRESHOLD\s*=\s*([\d.]+)"),
        "rework_fraction": _extract_value(content, r"evaluated_count\s*\*\s*(\d+)\s*/\s*(\d+)"),
    }

    # Flag suspicious changes
    if indicators.get("pass_threshold") and float(indicators["pass_threshold"]) < 0.3:
        indicators["warning"] = "pass_threshold suspiciously low"
    
    return indicators
```

Include drift indicators in the eval_digest.md. After a few evolution campaigns, if you see variants with low rework rates AND low external scores, that's drift in action — tighten the check.

**LOC:** ~30
**Risk:** Over-constraining legitimate evaluator improvements. Mitigate: monitor and warn, don't block.

---

### Gap 1: Production Intelligence → Evolution

**What:** Feed production session insights into the evolution loop.

**Where:** `evolve.sh` (placeholder), with full script deferred until production sessions exist.

**Implementation (placeholder only):**

No production sessions exist yet (system is on v001). The session schema is unvalidated through real usage. Building a 100 LOC synthesis script now risks building to the wrong schema.

Add to `evolve.sh`, before `prepare_meta_workspace()`:

```bash
# TODO: When production sessions exist and schema is validated,
# replace this with synthesize_production_intelligence.py
# Design intent: aggregate last 30 production sessions into
# production_intelligence.md with rework rates, stall patterns,
# common evaluation failures, and cross-domain observations.
PRODUCTION_SESSIONS_DIR="${PRODUCTION_SESSIONS_DIR:-}"
if [ -n "$PRODUCTION_SESSIONS_DIR" ] && [ -d "$PRODUCTION_SESSIONS_DIR" ]; then
    echo "Production intelligence: found sessions at $PRODUCTION_SESSIONS_DIR (synthesis not yet implemented)" >&2
fi
```

**When to build the full script:** After 10+ production sessions exist across at least 2 domains. At that point, validate the session schema (results.jsonl structure, session_summary.json fields) against real data, then implement synthesis. The script design should:
- Scan last N sessions, aggregate per-domain: rework rates, stall counts, avg deltas, common failure criteria
- Handle corrupt JSONL gracefully (try/except per session, skip bad entries)
- Require minimum 5 sessions before generating output
- Write `production_intelligence.md` to meta workspace

**LOC:** ~5 (placeholder) + ~100 later when data exists
**Risk:** None — placeholder is a no-op.

---

## Implementation Summary

| Phase | Gap | Score | LOC | Effort | Key File |
|-------|-----|-------|-----|--------|----------|
| 1 | 30 | 5 | 10 | Trivial | evaluate_variant.py |
| 1 | 6 | 7 | 30 | Low | evaluate_variant.py |
| 1 | 2+26 | 9+5 | 120 | Medium | evaluate_variant.py, archive_index.py, evolve.sh |
| 2 | 17 | 6 | 40 | Low | evaluate_variant.py |
| 2 | 18 | 7 | 50 | Medium | evaluate_variant.py |
| 2 | 28 | 5 | 60 | Medium | evaluate_variant.py, archive_index.py |
| 3 | 3 | 8 | 30 + fixtures | High (content) | eval_suites/, evaluate_variant.py |
| 3 | 4 | 6 | 3 | Trivial | meta.md template only |
| 3 | 7 | 6 | 30 | Low | evaluate_variant.py |
| 3 | 1 | 8 | 5 | Trivial (placeholder) | evolve.sh |

**Total code: ~625-800 LOC** (pseudocode shown is ~375 LOC; remaining ~250-425 covers helper functions like `_load_parent_scores()`, import additions, `Fixture` dataclass extension with `anchor` field, `evolve.sh` template substitution changes, and error handling. Gap 4 reduced to 3 template lines; Gap 1 deferred to placeholder.)
**Total effort: ~2-3 focused implementation sessions for Phase 1+2, plus ongoing fixture creation for Phase 3**

## Testing Strategy

1. **Before any changes:** Manually patch `archive/v001/meta.md` to add the new template variables (`{eval_digest_path}`, `{parent_sessions_path}`, `{production_intelligence}`) — new variants clone from v001, so these must exist in the seed before the first evolution run. Then run `evolve.sh score-current` to establish baseline scores for v001. Save these as the regression reference.
2. **After Phase 1:** Run `evolve.sh score-current` again. Verify: (a) L1 import check passes for v001, (b) regression_floor check passes for v001 (no parent = no regression), (c) eval_digest.md is generated in variant dir, (d) meta workspace includes session traces for parent.
3. **After Phase 2:** Run `evolve.sh run --iterations 1 --candidates-per-iteration 1`. Verify: (a) staged eval triggers correctly for broken variants, (b) 3 runs per fixture produces median scores, (c) unchanged domains use cached parent scores.
4. **After Phase 3:** Run `evolve.sh run --iterations 3 --candidates-per-iteration 3`. Verify: (a) fixture rotation produces different samples per variant, (b) strategy_analysis.md is generated, (c) evaluator drift indicators appear in digest.

## Key Design Decisions

1. **Raw traces over summaries** — Meta-Harness ablation is definitive. We expose raw sessions AND provide a digest.
2. **Regression floor as automated gate** — Unlike Meta-Harness (which relies on proposer reasoning), we enforce the defined-but-ignored field. The floor values (0.02-0.03) are already calibrated.
3. **3 runs, median** — Best practices research confirms this as the minimum viable variance reduction. Adaptive (1 run canary, 3 runs full) keeps cost manageable.
4. **Domain-level caching, not fixture-level** — Simpler, matches lane_paths.py ownership. Core file change invalidates all caches.
5. **Staged eval threshold at 50% domain output** — Conservative. Only catches completely broken variants. Better to over-evaluate than miss a good mutation.
6. **Strategy extraction as narrative, not algorithm** — The meta agent is an LLM. A readable narrative of "what worked" is more useful than raw correlation tables.
7. **Evaluator drift: monitor, don't block** — meta.md explicitly encourages evaluator evolution. Blocking it would contradict the design intent. Monitor rework rates instead.
