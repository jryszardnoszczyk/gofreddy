---
title: Autoresearch pass-1 implementation research (6 items)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-006-pipeline-overengineering-implementation-research.md
---

# Autoresearch Hardening Pass-1 — Implementation Research

Repo-anchored recommendations for 6 items (#12, #13, #14, #15, #24, #25). All line refs point to `HEAD` (commit `ff2f2e4`).

---

## #12 — Auto-regenerate program "Structural Validator Requirements" sections

**Summary:** Programs currently lie to agents about structural gates (say "≥100 chars + 3 headers"; actual gate is "≥500 chars + parseable competitors/*.json"). Replace the hand-maintained prose with a generated section, driven by parsing `src/evaluation/structural.py`, that re-renders at variant-clone time so no variant ever ships drift.

**Current state:**
- Truth source: `src/evaluation/structural.py:82-134` (competitive needs ≥500 chars, ≥3 headers, at least one parseable competitors/*.json excluding `_` prefix), `:140-289` (monitoring 13-14 assertions + digest-meta grounding), `:50-76` (geo: ≥1 `optimized/*.md|html`, JSON-LD parses), `:295-395` (storyboard: stories/*.json or storyboards/*.json + scene structure).
- Lie sites: `autoresearch/archive/current_runtime/programs/competitive-session.md:138-144` (off by 5× on char count; doesn't mention competitors/*.json). Monitoring's summary at `monitoring-session.md:77-79` is roughly right but handwaves; geo (L130) and storyboard (L141) mention the validator inline, not in a named section.

**Target state:** Each `programs/<domain>-session.md` has a `## Structural Validator Requirements (auto-generated — do not edit)` block whose body is a bullet list rendered from the real assertions. The meta-agent is told this block is machine-written and will be overwritten on next clone, so attempts to "tune" it via mutation lose the next cycle.

**Implementation approach:**
- **Option A — AST parse of `structural.py`:** walk each `_validate_<domain>` function with `ast.parse`, hunt for `failures.append(...)` calls, and try to extract string literals. Fragile: many failures are formatted strings or conditional branches (e.g. monitoring's `_assert` helper).
- **Option B — hand-maintained dict + test that the dict matches the code:** define a `STRUCTURAL_DOC_FACTS: dict[str, list[str]]` at the bottom of `structural.py` with one bullet per assertion; add a unit test that instantiates a family of fixtures (good + each failure mode) and asserts that each bullet has a corresponding observable failure. The dict is trivial markdown, but the test guarantees it tracks the code.
- **Recommended: Option B.** AST parsing monitoring's 14-assertion branch nightmare is 100+ lines of brittle walker code; Option B is ~30 LOC of dict + ~60 LOC of pytest fixtures, uses the structural gate as its own oracle, and fails loudly in CI the moment a dev changes a check without touching the doc source. Keep it where the truth is.

**Specific code changes:**
1. Add to `src/evaluation/structural.py`:
   ```python
   STRUCTURAL_DOC_FACTS: dict[str, list[str]] = {
       "competitive": [
           "A file with 'brief' in the name ending in `.md` exists",
           "Brief content is at least 500 characters (not 100 — outdated prompts lie about this)",
           "Brief has at least 3 markdown section headers",
           "At least one `competitors/*.json` (excluding `_`-prefixed baseline files) parses as JSON",
       ],
       # ... geo, monitoring, storyboard
   }
   ```
2. New script `autoresearch/regen_program_docs.py` (~40 LOC): imports `STRUCTURAL_DOC_FACTS`, reads each `programs/<domain>-session.md`, locates the `## Structural Validator Requirements` H2 (regex on `^## Structural Validator Requirements`), replaces through the next `^## ` (or EOF) with the auto-generated block wrapped in a `<!-- autogen:structural-reqs start -->` / `<!-- autogen:structural-reqs end -->` pair.
3. In `autoresearch/evolve.py:875` (right after `shutil.copytree(str(parent), str(variant_dir))` and the `sessions/` reset), call `regen_program_docs.regenerate(variant_dir / "programs", DOMAINS)`.
4. Also run it once in `autoresearch/runtime_bootstrap.py` so `current_runtime/` stays in sync between evolve cycles.

**Dependencies:** None — independent. Unblocks trust in inner-critique feedback for #14 (no point measuring inner-vs-outer correlation while the inner-loop program doc is wrong about the gate).

**Edge cases:**
1. Meta-agent edits the auto-gen block during a mutation pass — next clone overwrites. Good. But if the meta-agent deletes the H2 entirely, the regex finds no anchor. Mitigation: if block absent, append it at end of file with a WARN.
2. A domain is added without updating `STRUCTURAL_DOC_FACTS` — regen loops over `DOMAINS`; add a guard that raises if any domain is missing from the facts dict.
3. Geo's `optimized/*.md|html` matches both `.md` and `.html`; make sure the bullet reflects both paths (the code at `structural.py:55` does).
4. Storyboard accepts *either* `stories/*.json` *or* `storyboards/*.json`; bullet must disjunction, not require both.
5. Monitoring has 14 assertions with complex low-volume escape hatches (many pass when `digest.md` exists). The bullet list should state the *user-visible* preconditions (no `digest.md` absent AND no `select_mentions` entry = fail), not 14 literal asserts.

**Test strategy:**
- Add `tests/autoresearch/test_structural_doc_facts.py`: for each domain, build a minimal outputs dict that passes, then for each bullet in `STRUCTURAL_DOC_FACTS[domain]` produce a mutated copy that should violate it, and assert `structural_gate(...)` returns `passed=False` with a failure mentioning a keyword from the bullet.
- Add `tests/autoresearch/test_regen_program_docs.py`: in a tmpdir, seed `programs/*.md` with stale bullets, run `regenerate(...)`, assert files now contain the new block and the autogen markers are intact.

**Rollout:** Existing variants keep their old (lying) docs until next clone; next evolution cycle automatically refreshes. No data-migration step. One-time manual call `python3 -m autoresearch.regen_program_docs autoresearch/archive/current_runtime/programs` to fix `current_runtime` today.

**Estimated effort:** 3-4 hours.

**Open questions:** Should the doc include the `StructuralResult.dqs_score` concept for monitoring (so agents know which assertions scale the DQS)? Leaning yes — one short paragraph under the bullet list.

---

## #13 — SHA256 hash check on `build_critique_prompt` + `GRADIENT_CRITIQUE_TEMPLATE`

**Summary:** Convert the honor-system note in `meta.md:70` into an L1 validation gate. The variant can freely evolve everything else, but if it tries to override the critique-prompt construction, L1 fails and the variant is discarded before it ever runs.

**Current state:**
- `autoresearch/harness/session_evaluator.py:31-85` defines the frozen template + `build_critique_prompt`. These live *outside* the variant workspace (the `harness/` prefix is excluded from every lane at `autoresearch/lane_paths.py:13-15`).
- Variant imports: `autoresearch/archive/current_runtime/scripts/evaluate_session.py:35-42` pulls `GRADIENT_CRITIQUE_TEMPLATE` + `build_critique_prompt` from `harness.session_evaluator`.
- Attack vector: the meta-agent (core lane) is free to edit `scripts/evaluate_session.py`. It could add a local override: `def build_critique_prompt(...): return "be lenient..."` and drop the harness import; or wrap the imported call. `meta.md:52` explicitly invites edits to the file ("`scripts/evaluate_session.py` is a legitimate evolution target"). The frozen-interface discipline sits in L70 but is unenforced.

**Target state:** L1 validation computes the SHA256 of the literal bytes of (a) the `GRADIENT_CRITIQUE_TEMPLATE` string value and (b) the `build_critique_prompt` function source, as imported by the variant's `scripts/evaluate_session.py` in an isolated subprocess. The expected hashes are baked into the variant at clone time via a `critique_manifest.json`. L1 fails if hashes drift or the import itself is redirected.

**Implementation approach:**
- **Option A — byte-hash the variant's local `scripts/evaluate_session.py`:** simple but brittle — any legitimate edit to that file (reordering functions, adding a comment) fails L1. Too noisy.
- **Option B — runtime introspection:** in a subprocess, `cd variant_dir && python3 -c "from scripts.evaluate_session import build_critique_prompt, GRADIENT_CRITIQUE_TEMPLATE; import inspect, hashlib; print(hashlib.sha256(inspect.getsource(build_critique_prompt).encode()).hexdigest()); print(hashlib.sha256(GRADIENT_CRITIQUE_TEMPLATE.encode()).hexdigest())"`. Compare against manifest.
- **Recommended: Option B.** It checks the *effective* prompt the variant would actually send, regardless of whether the override came from a local shadow, a monkeypatch in a shared helper, a different import path, or a string mutation. It gracefully allows benign refactors of `evaluate_session.py` (e.g. renaming a helper, adding a comment) as long as the two inspected values remain the frozen bytes.

**Specific code changes:**
1. New `autoresearch/critique_manifest.py`:
   ```python
   def compute_expected_hashes() -> dict[str, str]:
       from harness.session_evaluator import build_critique_prompt, GRADIENT_CRITIQUE_TEMPLATE
       import inspect, hashlib
       return {
           "build_critique_prompt": hashlib.sha256(inspect.getsource(build_critique_prompt).encode()).hexdigest(),
           "GRADIENT_CRITIQUE_TEMPLATE": hashlib.sha256(GRADIENT_CRITIQUE_TEMPLATE.encode()).hexdigest(),
       }
   ```
2. In `autoresearch/evolve.py:875` (right after the clone), write `(variant_dir / "critique_manifest.json")` with `{"hashes": compute_expected_hashes(), "generated_at": ...}`.
3. In `autoresearch/evaluate_variant.py:413` (`layer1_validate`), add a block before the `for domain in DOMAINS:` program-file check:
   ```python
   manifest = load_json(variant_dir / "critique_manifest.json", default=None)
   if manifest is None:
       print("L1 FAIL: missing critique_manifest.json", file=sys.stderr); return False
   expected = manifest["hashes"]
   observed_raw = subprocess.run(
       ["python3", "-I", "-c", _INTROSPECTION_SNIPPET],
       capture_output=True, text=True, cwd=variant_dir,
       env={**os.environ, "PYTHONPATH": str(_repo_root() / "autoresearch")},
       timeout=10,
   )
   observed = json.loads(observed_raw.stdout)
   for key, want in expected.items():
       if observed.get(key) != want:
           print(f"L1 FAIL: critique {key} hash drift: {observed.get(key)} != {want}", file=sys.stderr)
           return False
   ```
4. Escape valve: new path `scripts/experimental_critique/` (explicitly listed in `_WORKFLOW_PREFIXES["core"]` via exclusion helper). Agents wanting to prototype a critique variant put it there and invoke it from a separate `--mode experimental` flag on `evaluate_session.py`. L1 hash check only runs against the frozen pair.

**Dependencies:** Enables #24 (subprocess isolation protects the *other* half — the invocation environment). #15's critique agent could also consume the manifest to verify variants didn't quietly delete the guarantee.

**Edge cases:**
1. Variant adds `sys.path.insert(0, ...)` to prepend a sibling module named `harness` — the import resolves to the shadow. Running with `python3 -I` (isolated) and a tight `PYTHONPATH` neutralizes this.
2. Variant replaces the template via class-level monkeypatch (`harness.session_evaluator.GRADIENT_CRITIQUE_TEMPLATE = "..."` at import). Our introspection re-imports fresh in a new process; mutation doesn't survive.
3. Upstream-harness refactor legitimately changes `build_critique_prompt`. Regenerate manifests via a one-time `evolve.py manifest-rebuild` sub-command; record the new hash; mark old variants' manifests stale.
4. Windows line-ending drift on `inspect.getsource`. Standardize: `.replace("\r\n", "\n").encode("utf-8")` in `compute_expected_hashes` and in the introspection snippet.
5. `freezetime`/`mock.patch` during tests — introspection runs in a clean subprocess, unaffected.

**Test strategy:**
- `tests/autoresearch/test_critique_manifest.py`: asserts `compute_expected_hashes()` produces stable hashes given fixture source; tampering with a copy of `session_evaluator.py` changes the hash.
- `tests/autoresearch/test_layer1_validate.py`: simulate a tampered variant (write local `build_critique_prompt` override into `scripts/evaluate_session.py`), assert `layer1_validate` returns `False` with the expected stderr message.

**Rollout:** Backfill existing variants with manifests generated from *current* frozen source. Grandfather any variant whose manifest is missing with a one-time pass. Breaking change only for variants that have *already* tampered — they fail L1 and get discarded; forensic log entry flags the drift.

**Estimated effort:** 4-6 hours (including tests + backfill script).

**Open questions:** Should the manifest also hash `HARD_FAIL_THRESHOLD`, `DEFAULT_PASS_THRESHOLD`, and `compute_decision_threshold`? Probably yes — same attack surface (bias failures low → sessions end early). Mild scope creep; JR decision.

---

## #14 — Inner-vs-outer evaluator correlation telemetry

**Summary:** Measure the disagreement between the variant's *in-session* critique decisions (KEEP/REWORK/DISCARD in `results.jsonl`) and the *outer* per-dimension fixture scores. Surface the mean delta on `index.json`. A persistent large delta is the load-bearing signal that the inner critique has been gamed or drifted.

**Current state:**
- Inner decisions: `sessions/<domain>/<client>/results.jsonl` contains agent-authored entries. Actual shape is heterogeneous (`sample`: `status: "kept"`, `quality_score: "17/20"`, `"latest_evaluator_summary": {...: "KEEP"}`), not a strict `decision` key. Some domains log structured, some freeform.
- Outer scoring: in `autoresearch/evaluate_variant.py:564-684` (`_score_session`) the returned dict has `dimension_scores: list[float]`, `score: float`, `structural_passed: bool`.
- Aggregation: `_aggregate_suite_results` at `evaluate_variant.py:687-738`. `_write_scores_file` at L813-846 already has an `inner_metrics` slot (unused).
- No side-by-side comparison anywhere.

**Target state:** In `_score_session`, parse `results.jsonl` after the run, compute `inner_pass_rate` as (# entries with kept/KEEP/pass signal) / (# entries with a decision signal). Compute `outer_pass_rate` as the fraction of `dimension_scores >= 0.5`. Return `inner_pass_rate`, `outer_pass_rate`, `pass_rate_delta` per fixture. Aggregate `mean_pass_rate_delta` per domain in `_aggregate_suite_results`. Persist under `scores.json → inner_metrics.{domain}`. Bubble up to `index.json` via `public_entry_summary`. Log WARN when `|delta| > 0.1`.

**Implementation approach:**
- **Option A — strict schema:** require agents to log a `{"type": "session_eval", "decision": "KEEP|REWORK|DISCARD"}` entry. Brittle, requires updating 4 programs, and existing sessions lack it.
- **Option B — fuzzy signal extraction:** look for keys `status ∈ {"kept", "pass"} → KEEP`, `{"discarded", "fail"} → DISCARD`, `{"rework"} → REWORK`; also pattern-match `decision` / `passes` keys when present. Handle the free-text `latest_evaluator_summary` block with a simple keyword heuristic.
- **Recommended: Option B.** Nothing to change in programs; extracts a signal from whatever the agent logs today. Wrong classifications on edge cases just shift the delta by a few points — noise, not a failure. Over time, we can tighten the extractor.

**Specific code changes:**
1. New helper `_extract_inner_pass_rate(session_dir: Path) -> float | None`:
   ```python
   KEEP_TOKENS = {"kept", "KEEP", "pass", "PASS", "done"}
   REWORK_TOKENS = {"rework", "REWORK", "fail", "discarded", "DISCARD"}
   def _extract_inner_pass_rate(session_dir: Path) -> float | None:
       rf = session_dir / "results.jsonl"
       if not rf.exists(): return None
       keeps, total = 0, 0
       for line in rf.read_text().splitlines():
           try: entry = json.loads(line)
           except json.JSONDecodeError: continue
           status = str(entry.get("status", "")).strip()
           decision = str(entry.get("decision", "")).strip()
           signal = decision or status
           if not signal: continue
           total += 1
           if signal in KEEP_TOKENS: keeps += 1
       return keeps / total if total else None
   ```
2. In `_score_session` (`evaluate_variant.py:667-684`), before `return {...}`:
   ```python
   outer_pass_rate = (sum(1 for s in dims if s >= 0.5) / len(dims)) if dims else None
   inner_pass_rate = _extract_inner_pass_rate(run.session_dir)
   delta = (inner_pass_rate - outer_pass_rate) if (inner_pass_rate is not None and outer_pass_rate is not None) else None
   if delta is not None and abs(delta) > 0.1:
       print(f"  WARN: {run.fixture.fixture_id} inner/outer pass-rate delta {delta:+.2f}", file=sys.stderr)
   ```
   Thread the three values into the returned dict.
3. In `_aggregate_suite_results` (`evaluate_variant.py:699-737`), compute per-domain `mean_pass_rate_delta = mean(...)` ignoring `None`s; include in `domain_metrics[domain]["inner_vs_outer"]`.
4. `_write_scores_file` already takes `inner_metrics`; wire it through from the caller.
5. `archive_index.public_entry_summary` (`archive_index.py:297-310`): add `mean_pass_rate_delta` to the per-variant summary so `index.json` carries it.

**Dependencies:** #12 helps — once the structural-gate prose is honest, inner KEEP decisions are actually measuring the same gate the outer scorer sees, so the delta is cleaner signal.

**Edge cases:**
1. Empty `results.jsonl` (structural-fail before agent logged anything) → inner=None → delta=None; aggregate ignores.
2. Low fixture counts (e.g. 3 fixtures with deltas 0.3, -0.4, 0.1) — `mean` averages to ~0 but every fixture is misaligned. Surface `max_pass_rate_delta` alongside `mean_pass_rate_delta` so the dashboard catches this.
3. Agent logs only `{"type": "gather", "status": "done"}` 8 times (all "pass" signal) and then `{"type": "synthesize", "status": "done"}` → inner pass rate = 1.0 (meaningless). Mitigate by restricting the counter to entries where `type ∈ {"analyze", "synthesize", "verify", "session_eval", "evaluate"}` — phases that imply a quality decision.
4. `dimension_scores` occasionally empty (evaluator failed) → outer=None; whole fixture skipped in aggregate.
5. Delta of `-1.0` (inner says all fail, outer says all pass) — legitimate: critique agent is honest, system is fine. Delta of `+1.0` is the actual gaming signal.

**Test strategy:**
- `tests/autoresearch/test_inner_vs_outer.py`: synthetic `results.jsonl` variants covering empty, all-keep, mixed, and malformed entries; assert extractor returns expected rates.
- Extend an existing `evaluate_variant` integration test (if present) with a canned session dir + expected `mean_pass_rate_delta` on the aggregate output.

**Rollout:** Pure addition to `scores.json` and `index.json`. Existing dashboards keep working; new field appears when next cycle runs. No backfill required (old variants have no hash to compare; field stays null).

**Estimated effort:** 3-4 hours.

**Open questions:** Is 0.1 the right WARN threshold? Probably conservative — for an 8-dimension rubric one flipped dimension = 0.125. Suggest starting at 0.15 and tightening once we have distribution data. Also: should the WARN include the fixture ID + delta in the final report, not just stderr? Yes — append to `eval_digest.md` so the meta-agent next pass sees it.

---

## #15 — Program length cap ~80 lines + Pareto constraint via critique agent

**Summary:** Add a critique LLM call inside the meta-agent mutation loop that reads the (old, new) pair of `programs/<lane>-session.md` and judges whether the mutation added net prescription (rules, blocklists, edit-order mandates) vs deletions. A prescription-increasing mutation is rejected or requires explicit human review — so program length can't ratchet upward across generations.

**Current state:**
- Program sizes: `competitive-session.md` 197L, `geo` 192L, `monitoring` 165L, `storyboard` 187L (`wc -l` on `archive/current_runtime/programs/*`). Heavy prescription: bullet-list AI-tell blocklists, em-dash heuristic (">1/page = rewrite"), edit-order rules, buyer-stage audit, cost-of-delay framing mandates. Declarative bullets masquerading as heuristics.
- No length or prescription gate. Meta-agent's "Simplicity Criterion" (`meta.md:58-66`) is honor-only.
- Mutation integration points: `evolve.py:926-931` runs the meta agent; `evolve_ops.sync_meta_workspace` (`evolve.py:937`) copies edits back into `variant_dir`.

**Target state:** After `sync_meta_workspace` and before `_score_variant_search`, run a `program_prescription_critic` over each changed program file. It returns `{verdict: "accept|reject|review", reasoning, added_prescriptions, removed_prescriptions}`. On `reject`, roll the file back to parent, log a lineage `mutation_rejected` entry, and continue. On `review`, keep the change but flag for operator in `eval_digest.md`.

**Critique agent design:**

**Prompt skeleton (~400 tokens):**
```
You are a program-mutation critic evaluating a change to an LLM agent's
session program. The program tells a research agent how to work — it should
describe *what good looks like* and *what the structural gate requires*, NOT
dictate *how* to work.

PRESCRIPTION = a rule the agent must follow, a banned word list, an edit-order
mandate, a fixed heuristic ("em-dash > 1/page = rewrite"), a forced taxonomy.
DESCRIPTION = a quality criterion, a data grounding expectation, a structural
requirement imposed by the gate.

Read OLD_PROGRAM and NEW_PROGRAM. Output JSON:
{
  "added_prescriptions": [{"quote": "...", "why_prescriptive": "..."}],
  "removed_prescriptions": [{"quote": "...", "from": "..."}],
  "net_prescription_delta": <int>,  // added - removed
  "length_delta": <new_lines - old_lines>,
  "verdict": "accept" | "reject" | "review",
  "reasoning": "...",
}

Rules:
- net_prescription_delta > 0 AND length_delta > 0 → verdict=reject
- net_prescription_delta > 0 AND length_delta <= 0 → verdict=review (prescription
  density rising even while file shrinks)
- net_prescription_delta <= 0 → verdict=accept
- If new program > 100 lines AND length_delta > 0 → verdict=reject regardless
```

**Where it fires:**
- In `evolve.py` between lines 938 (post-sync) and 944 (score_variant). Only runs on files where `git diff parent new -- programs/*-session.md` is non-empty. If any lane's program is rejected, revert *just that file* via `shutil.copy2(parent / "programs" / name, variant_dir / "programs" / name)`, then continue scoring — still useful: everything else the meta-agent changed survives.

**Escape valve:**
- Environment var `EVOLVE_SKIP_PRESCRIPTION_CRITIC=1` for operator override during intentional "add new structural requirement" cycles.
- `critique_manifest.json` can carry an explicit `allowed_prescription_addition: "reason"` string the operator writes by hand before a mutation cycle; the critic, on seeing it, allows one matching addition.

**Why a critique agent and not a token counter:**
- The memory note (JR: "rules-by-another-name in declarative bullets") is the crux. A token/line counter rewards compression (turning 20 bullets into 3 dense paragraphs = same prescription, passes the counter). An LLM critique reads semantics — "stripped AI-tell vocabulary (`utilize/leverage/facilitate...`)" is recognized as a banned word list regardless of formatting.

**Specific code changes:**
1. New `autoresearch/program_prescription_critic.py`: loads old/new content, builds the prompt, calls `freddy evaluate critique` (re-using the existing critique plumbing), parses the JSON response.
2. In `evolve.py:938`, after `sync_meta_workspace`:
   ```python
   from program_prescription_critic import critique_all_programs
   critic_result = critique_all_programs(parent_dir=parent, new_dir=variant_dir,
                                         lane=config.lane, env=os.environ)
   for domain, verdict in critic_result.items():
       if verdict["verdict"] == "reject":
           shutil.copy2(parent / "programs" / f"{domain}-session.md",
                        variant_dir / "programs" / f"{domain}-session.md")
           print(f"Rejected program mutation for {domain}: {verdict['reasoning']}")
       elif verdict["verdict"] == "review":
           (variant_dir / "critic_reviews.md").write_text(...)
   ```
3. Persist `critic_result` to `variant_dir / "prescription_critic.json"` for lineage forensics.

**Dependencies:** Depends on #12 (the structural-reqs block is autogen → shouldn't count as prescription drift when it legitimately grows to track real gate bullets). Also depends on the outer scorer being the real judge (`meta.md:30-38`) — if scorer gameability survives, this critic is cosmetic.

**Edge cases:**
1. Critique agent itself hallucinates a "prescription" in description text. Mitigate with low-temperature sampling + explicit quote extraction (the agent must cite verbatim lines from the diff). Reject verdicts that quote non-existent text.
2. Critic is unavailable (timeout, API error). Default to `verdict=review` — never silently accept (that recreates the honor-system flaw) and never silently reject (blocks useful runs on infra issues).
3. Program file deleted entirely (e.g. variant drops a domain). length_delta is massively negative; treat as accept but log a lineage entry.
4. Meta agent adds prescription via `programs/references/*.md` to bypass the critic (prose-hygiene.md etc). Extend the critic to also read referenced files, or at minimum snapshot the references dir size and gate on growth.
5. Critic's own cost: 4 programs × ~4KB each = ~32KB per generation, minor. But if runs at every generation on every lane, adds up — cache on file-hash, skip when unchanged.

**Test strategy:**
- `tests/autoresearch/test_prescription_critic.py`: golden fixtures for (a) a prescription-adding diff (banned word list) — expect `reject`; (b) a description-preserving refactor — expect `accept`; (c) a compression that drops 5 bullets into 1 paragraph without losing rules — expect `review`. Mock the LLM call; assert the call payload includes both old and new program text verbatim.

**Rollout:** Guard behind env flag initially (`EVOLVE_PRESCRIPTION_CRITIC=1`) for 3-5 cycles in shadow mode — compute verdict, log to JSON, never act. Once JR agrees the verdicts look right, flip to enforcing.

**Estimated effort:** 1-1.5 days (agent prompt tuning + cautious rollout scaffolding is real work).

**Open questions:**
- JR hasn't decided: is "program length cap ~80 lines" a hard cap or a soft target? Current proposal uses soft target via `review` + hard cap at 100. Different values need a call.
- Should the critic also evaluate the *parent* for established prescription, or only the diff? Diff-only is simpler; parent-context-aware catches drift that was smuggled past a previous gate. Start with diff-only, escalate if needed.
- Does rollback to parent for a rejected mutation risk dropping a correlated useful change (e.g. meta-agent added a prescription AND fixed a real bug in the same file)? Yes. Mitigation: only reject if `length_delta > 0`; on `length_delta <= 0` we trust it.

---

## #24 — Subprocess-isolate inner critique invocation (`python -I` + module allowlist)

**Summary:** Run the inner critique call in a clean subprocess with Python's isolated mode and a wrapper that enforces a module allowlist. Closes the gap that #13 alone doesn't cover — #13 protects the template bytes, this protects the invocation context (imports, monkeypatches, shadowed modules).

**Current state:**
- `autoresearch/archive/current_runtime/scripts/evaluate_session.py:112-126` shells out to `freddy evaluate critique` already — so the *critique itself* is already in a subprocess. Good.
- But the subprocess inherits the parent's Python environment: `sys.path`, installed monkeypatches, and any locally defined helpers that shadow the imported `build_critique_prompt`. Line 183 calls `build_critique_prompt(...)` *before* the subprocess shell-out — so any in-process override of that function (e.g. meta-agent imports a local copy in `scripts/evaluate_session.py` before the frozen import) changes the rubric_prompt that gets sent.
- Attack: variant rewrites `scripts/evaluate_session.py` so at the top it does `from scripts.lenient_critique import build_critique_prompt as _lenient; build_critique_prompt = _lenient` — that shadow wins, the frozen import is shadowed, the prompt sent is lenient. The shell-out to `freddy evaluate critique` doesn't care, it just formats whatever prompt it received.

**Target state:** The rubric-prompt construction runs in a dedicated subprocess with `python -I` (isolated mode ignores PYTHONPATH, ignores user site-packages, ignores `.pth` files) and an explicit `PYTHONPATH` set to exactly `<repo>/autoresearch`. A thin wrapper imports *only* `harness.session_evaluator`, calls `build_critique_prompt`, prints the resulting prompt as JSON to stdout. The caller pipes that prompt into the `freddy evaluate critique` subprocess. No agent-defined Python runs between frozen-prompt construction and the critique API call.

**Implementation approach:**
- **Option A — keep the current in-process construction, add defensive runtime assertions** (`assert build_critique_prompt.__module__ == "harness.session_evaluator"`). Works only if the agent doesn't also patch `__module__` — easy to defeat.
- **Option B — full subprocess wrapper.** One extra fork per critique call (~50ms overhead). Isolation guaranteed.
- **Recommended: Option B.** Composes cleanly with #13 (hash check + subprocess isolation = belt + suspenders). Perf cost is trivial next to the LLM call downstream (30-90s).

**Specific code changes:**
1. New `autoresearch/harness/prompt_builder_entrypoint.py`:
   ```python
   """Isolated-mode entrypoint for frozen critique prompt construction.
   Invoked as: python -I -m harness.prompt_builder_entrypoint <json_criteria>
   """
   import json, sys
   from harness.session_evaluator import build_critique_prompt
   criteria = json.loads(sys.stdin.read())
   prompts = [
       {**c, "rubric_prompt": build_critique_prompt(
           c["domain_name"], c["criterion_id"], c["criterion_def"], c.get("cross_ctx"),
       )}
       for c in criteria
   ]
   json.dump(prompts, sys.stdout)
   ```
2. In `autoresearch/archive/current_runtime/scripts/evaluate_session.py:170-195`, replace the in-process `build_critique_prompt(...)` call with:
   ```python
   frozen_proc = subprocess.run(
       ["python3", "-I", "-m", "harness.prompt_builder_entrypoint"],
       input=json.dumps(criteria_payload),
       capture_output=True, text=True, timeout=10,
       env={"PATH": os.environ["PATH"], "PYTHONPATH": str(AUTORESEARCH_ROOT)},
       # NOTE: no PYTHONPATH from parent env; no user site-packages; -I excludes .pth
   )
   critique_requests = json.loads(frozen_proc.stdout)
   ```
3. Add a `_module_allowlist` guard in `prompt_builder_entrypoint.py`: after imports, walk `sys.modules` and `assert` the set is a subset of `{"builtins", "sys", "json", "hashlib", "re", "pathlib", "harness.session_evaluator", "harness"}`. A module outside the allowlist means something weird happened.

**Dependencies:** #13 computes and stores the expected hashes. #24 ensures the variant can't reach into the moment of prompt construction. Together: frozen bytes + frozen invocation. #15's critique agent could consume the same wrapper pattern.

**Edge cases:**
1. `-I` disables `PYTHONSTARTUP`, `PYTHONPATH` env, and `sys.path[0]` injection. But it honors explicit `-c PYTHONPATH` inherit? No — `-I` implies `-E` and `-s`. We must pass `PYTHONPATH` explicitly in the env dict we hand to the subprocess (code snippet above does this).
2. Variant adds a `sitecustomize.py` somewhere on `sys.path`. `-I` skips user site-packages but NOT `sys.path[0]` when set via `-m`. The `-m` mode still adds cwd to `sys.path` — explicitly `cwd=<controlled_dir>` in `subprocess.run` (e.g. `/tmp/autoresearch-frozen-<rand>`) avoids picking up variant-local shadows.
3. `harness` package on repo-wide `sys.path` has multiple entries (e.g. runtime_bootstrap copies it to a different dir). Canonicalize the import path via the explicit `PYTHONPATH` env we set.
4. Subprocess timeout — 10s is generous for local imports; if hit, return `_critique_unavailable("prompt_builder_timeout")` (fits the existing error-handling pattern at `evaluate_session.py:199-205`).
5. Windows: `python -I` is supported. `os.setsid` isn't; fallback to parent's process-group handling as in existing runner (`evolve.py:78-88`).

**Test strategy:**
- `tests/autoresearch/test_prompt_builder_isolation.py`: verify the entrypoint produces the correct `rubric_prompt` for representative inputs. Spawn with a polluted `PYTHONPATH` containing a fake `harness/session_evaluator.py` that would override `build_critique_prompt`; assert the subprocess output still uses the frozen original.
- Add a fixture that injects a `sitecustomize.py` on the parent path; assert `-I` keeps the child clean.

**Rollout:** Non-breaking for benign variants. Breaking for any that already depend on in-process helpers — none in current archive, verified. One-shot update to `scripts/evaluate_session.py` + propagate to next-cloned variants.

**Estimated effort:** 0.5 day.

**Open questions:** Should the same subprocess-isolation pattern extend to `freddy evaluate variant` (the outer scorer)? Probably yes eventually — but that's a separate architectural question outside this pass's scope.

---

## #25 — Replace `report_base.parse_findings` with mistune AST traversal

**Summary:** The current regex-and-state-machine parser at `autoresearch/report_base.py:82-149` is brittle (silently flushes findings when a state transition line is also the next section's first bullet; handles `## Confirmed` but not `## Confirmed Findings` exactly; couples to exact `- **Evidence:**` string). Replace with a mistune AST walk — ~40 LOC, robust to whitespace and formatting variants.

**Current state:**
- Parser: `report_base.py:82-149`. State machine fields: `current_category`, `current_finding`. Regex `^###\s+(?:\[(\w+)\]\s+)?(.+)$`. Only two patterns recognized per finding (`**Evidence:**`, `**Detail:**`).
- `mistune` is already a dependency (`report_base.py:28`, `_md_renderer` on L172).
- Callers (`configs/{monitoring,competitive,storyboard,seo}/scripts/generate_report.py` — ~4 files) pass `findings.md` content → expect `{"confirmed": [...], "disproved": [...], "observations": [...]}` shape.

**Target state:** AST walk: mistune renders to a token tree; walk looking for `heading level=2` tokens whose inline text starts with `Confirmed`, `Disproved`, or `Observations`. Within each h2's range, collect `heading level=3` children — each h3 becomes a finding. Walk the block children between h3 and next h3 to extract evidence/detail from `paragraph > strong` nodes.

**Implementation approach:**
- **Option A — mistune AST via `create_markdown(renderer="ast")`:** returns a token list; walk it with a simple for-loop.
- **Option B — markdown-it-py:** lighter AST API but adds a new dep.
- **Recommended: Option A.** Zero new deps; mistune is already configured. The AST renderer is stable across mistune 2.x / 3.x.

**Specific code changes:**

Replace `report_base.py:82-149` with:

```python
_ast_md = mistune.create_markdown(renderer="ast", plugins=["table", "strikethrough"])

CATEGORY_MAP = {
    "confirmed": "confirmed",
    "disproved": "disproved",
    "observations": "observations",
}

def _inline_text(node: dict) -> str:
    """Recursively collect raw text from a mistune AST inline node."""
    if node.get("type") == "text": return node.get("raw") or ""
    if node.get("type") == "codespan": return node.get("raw") or ""
    return "".join(_inline_text(c) for c in node.get("children", []) if isinstance(c, dict))

def _category_from_h2(heading_node: dict) -> str | None:
    text = _inline_text(heading_node).strip().lower()
    for key, category in CATEGORY_MAP.items():
        if text.startswith(key): return category
    return None

def _parse_h3_finding(heading_node: dict) -> dict:
    text = _inline_text(heading_node).strip()
    m = re.match(r"^\[(\w+)\]\s+(.+)$", text)
    if m:
        return {"tag": m.group(1), "title": m.group(2).strip(), "evidence": "", "detail": ""}
    return {"tag": None, "title": text, "evidence": "", "detail": ""}

def _extract_kv(para_node: dict) -> tuple[str, str] | None:
    """Return ('evidence'|'detail', value) for a paragraph like '**Evidence:** text'."""
    children = para_node.get("children") or []
    if not children: return None
    first = children[0]
    if first.get("type") != "strong": return None
    key = _inline_text(first).rstrip(":").strip().lower()
    if key not in ("evidence", "detail"): return None
    rest_nodes = children[1:]
    value = "".join(_inline_text(n) for n in rest_nodes).lstrip(": ").strip()
    return (key, value)

def parse_findings(md: str) -> dict[str, list[dict]]:
    result = {"confirmed": [], "disproved": [], "observations": []}
    if not md: return result
    tokens = _ast_md(md)
    current_category: str | None = None
    current_finding: dict | None = None
    for tok in tokens:
        ttype = tok.get("type")
        if ttype == "heading" and tok.get("attrs", {}).get("level") == 2:
            if current_finding and current_category:
                result[current_category].append(current_finding)
                current_finding = None
            current_category = _category_from_h2(tok)
        elif ttype == "heading" and tok.get("attrs", {}).get("level") == 3 and current_category:
            if current_finding:
                result[current_category].append(current_finding)
            current_finding = _parse_h3_finding(tok)
        elif ttype in ("paragraph", "block_quote") and current_finding:
            kv = _extract_kv(tok)
            if kv:
                current_finding[kv[0]] = kv[1]
        # list_item handled same way (bullets containing strong+text)
        elif ttype == "list" and current_finding:
            for li in tok.get("children", []) or []:
                for child in li.get("children", []) or []:
                    if child.get("type") == "block_text":
                        kv = _extract_kv(child)
                        if kv: current_finding[kv[0]] = kv[1]
    if current_finding and current_category:
        result[current_category].append(current_finding)
    return result
```

**Dependencies:** None. Self-contained; same API surface → callers unchanged.

**Edge cases:**
1. `## Confirmed Findings` vs `## Confirmed (2 new)` — `_category_from_h2` does `startswith`, both match. Current regex already does this.
2. Findings under an unrecognized h2 (`## Summary`) — skipped gracefully (`current_category` stays None).
3. Nested finding content: `### Title\n\nSome narrative.\n\n- **Evidence:** ...` — list handling branch picks up `block_text` bullets.
4. Agents occasionally write `**Evidence**:` (colon outside bold). `_extract_kv` uses `.rstrip(":")` on the strong text — handles it. If colon is *inside* the bold (`**Evidence:**`), still fine.
5. Tables between findings — mistune AST emits a `table` token, we ignore it. Prior parser would flush and lose the finding.

**Test strategy:**
- `tests/autoresearch/test_parse_findings.py`: golden fixtures for (a) the canonical format used across configs (copy from an actual `findings.md` in `archive/current_runtime/sessions/`), (b) malformed whitespace, (c) category-section with no findings, (d) finding with no evidence/detail, (e) `### [TAG] Title` vs `### Title`. Migrate 5+ real-world findings.md files into the fixture set and assert the new parser returns identical shape to the old one (tree-equality test).

**Rollout:** Internal API; zero external breakage. Run the existing report generators against 3-5 archived sessions before and after, diff the HTML. Expect identical output on well-formed files, richer output on the previously-silent-drops.

**Estimated effort:** 3-4 hours (most of the time is fixture collection and parity assertions).

**Open questions:** Should the new parser also emit a diagnostic log line when it encounters an unrecognized h2 inside the findings file? Probably yes — helps author feedback loops. Default to `WARN` with the h2 text, ungated.
