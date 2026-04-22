---
title: Cross-pipeline convergence deep research (F6.1-F6.3)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-004-pipeline-overengineering-deep-research.md
---

# Cross-Pipeline Convergence Research — Findings F6.1 / F6.2 / F6.3

## Executive Summary

After spot-checking the three pipelines (`harness/findings.py`, `harness/safety.py`, `harness/engine.py`, `harness/run.py`, `harness/review.py`; `autoresearch/report_base.py`, `autoresearch/evolve.py`, `autoresearch/evaluate_variant.py`; the audit plan at `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md`), **the matrix overstates convergence opportunity**. Of the six rows, only **two are clean wins** for consolidation, three are stratified-but-coordinated (same shape, different policy), and one (quality scoring) is genuinely divergent and should stay separate.

**Top convergence opportunities (do these):**
1. **Reporting/rendering** (`render_lib`) — `autoresearch/report_base.py` is already a shared-library shape; the harness's `review.compose` + the audit plan's Jinja2 deck overlap by ~70% (HTML scaffold, secret scrubbing, badge rendering, section partials, PDF via headless Chrome). One package saves ~400 LOC and gives the team a single visual language for runs/audits.
2. **Findings envelope + parser** (`finding_lib`) — One Pydantic model with two parser frontends (YAML-front-matter and `## Section / ### Title` markdown) consolidates `harness/findings.py` (107 LOC) and `autoresearch/report_base.py:parse_findings` (~70 LOC) and gives the audit plan an off-the-shelf envelope. Saves ~130 LOC and removes a class of regex bugs.

**Top stratification-don't-converge opportunities:**
3. **Quality scoring** is irreducibly different (binary verifier vs. weighted-rollup health-score vs. geometric-mean of LLM judges with 0.01 floor). Each scoring strategy is correct *for its question*. Forcing a shared abstraction here = product damage.
4. **Permissions/safety** is partially convergent (the audit plan's capability-restriction model is strictly stronger than harness regex-allowlist for read-only agents) but harness fixers MUST mutate code, so the unified model is **stratified by capability tier**, not unified.
5. **Runaway-loop backstop** is the same primitive (timeout + sentinel) under three names; can be a 30-LOC helper but not worth a library.

**Recommended phasing:**
- **Now (1-2 days):** Extract `render_lib` from `autoresearch/report_base.py` into `src/shared/reporting/`. Migrate harness `review.compose` + `pr_body` to it. The audit plan adopts it before Stage 5 (deliverable rendering) gets built — it's the cheapest win and the audit plan is the biggest beneficiary.
- **Soon (3-5 days, after audit plan U2 lands):** Extract `finding_lib` once the audit plan ships its Pydantic `Finding` envelope. Three pipelines normalize on that envelope; harness keeps YAML front-matter as one parser, autoresearch keeps the `## Section / ###` markdown as another, both produce the same Pydantic.
- **Defer / never:** Quality scoring (keep three separate; they answer three different questions). Permissions (stratify explicitly via `scoped_tools.py` for read-only agents; harness fixers stay on regex-allowlist + post-hoc scope check, that's the right floor for "agent must edit code I will then commit").
- **NOT NOW: don't generalize the orchestrator.** Three orchestrator loops look superficially similar but their state machines differ in important ways (harness drains queues per track; audit plan fans out 7 agents once; autoresearch evolves variants over generations). Premature orchestrator framework = the worst kind of over-engineering.

---

## F6.1 — Three-implementations-of-six-patterns matrix

### Row 1: Agent emits structured output

**Underlying need:** The agent must produce machine-readable output the orchestrator can route, without burning so many tokens on rigid JSON schemas that quality drops.

**Are the three implementations doing the same job?** **Yes, mostly.** All three produce an envelope — a typed wrapper around an array of items with `id / category / evidence / detail` fields. The differences are stylistic:
- Harness: YAML front-matter blocks with markdown body (`harness/findings.py:_BLOCK_RE`)
- Audit plan: Pydantic `Finding` + `AgentOutput` (per plan ~L703-704: `{id, agent, rubric_theme, report_section, title, severity(0-3), reach(0-3), feasibility(0-3), evidence_urls[], evidence_quotes[], recommendation, ...}`)
- Autoresearch: markdown sections (`## Confirmed / ## Disproved / ## Observations`) with `### Title` per finding

The audit plan has the richest envelope (10+ fields including severity/reach/feasibility scores); harness has 8 fields; autoresearch has 4. But all three encode the *same shape*: typed metadata + freeform evidence + freeform detail.

**What would a shared library look like?** A `src/shared/findings/` package:
```
class Finding(BaseModel):
    id: str
    category: str
    confidence: Literal["high","medium","low"] | None
    title: str
    evidence: str
    detail: str
    extra: dict[str, Any]   # pipeline-specific fields (track, severity, agent, etc.)

def parse_yaml_frontmatter(text: str) -> list[Finding]: ...
def parse_section_markdown(text: str) -> list[Finding]: ...
def serialize_yaml_frontmatter(findings: list[Finding]) -> str: ...
```

Pipelines pick whichever parser matches their agent's output convention. Pipeline-specific fields go in `extra`.

**Estimated LOC savings:** `harness/findings.py` 107 LOC → ~30 LOC of pipeline-specific glue; `autoresearch/report_base.py:parse_findings` ~70 LOC → ~30 LOC of glue; audit plan saves ~50 LOC of envelope plumbing it would otherwise write. **Total: ~150 LOC removed, plus prevents drift across two re-implementations of the same regex/state-machine bugs** (the autoresearch parser has a known bug where `### Title` in the wrong position resets state — fixed in one place).

**Verdict on this row: GO.** Do it after the audit plan ships its envelope, since the audit plan's envelope is the most thought-through one — let it set the schema, then back-port harness and autoresearch.

---

### Row 2: Findings parser

**Underlying need:** Convert agent's text output to typed objects; fail soft (one bad block must not lose all others).

**Are the three implementations doing the same job?** **Yes — they're literally the same job.** Harness uses regex + `yaml.safe_load` per block, with explicit "skip-not-raise" on malformed blocks (commit `ff2f2e4` fixed this last week). Autoresearch uses a line-by-line state machine. Pydantic auto-validates one block at a time. All three parse one envelope at a time and accumulate; the failure modes differ only in cosmetic detail.

**What would a shared library look like?** This row is downstream of Row 1 — if findings envelope is shared, parsers are 30-50 LOC apiece living next to it. Consider this row already absorbed by Row 1.

**Estimated LOC savings:** Already counted in Row 1.

**Verdict: SUBSUMED by Row 1.** Don't track this as a separate convergence; it's the same library.

---

### Row 3: Quality scoring

**Underlying need:** Convert agent output → a number (or pass/fail) that the orchestrator can route on.

**Are the three implementations doing the same job?** **NO. These are three genuinely different questions.**
- **Harness verifier verdict:** binary `verified: bool` + `reason` (per `harness/engine.py:Verdict`). Question: "did the fix actually solve the bug, or did it regress something?" Answer: yes/no. Anything other than binary is product damage — you can't half-commit a fix.
- **Audit plan health-score:** weighted 0–100 rollup across 9 lens subscores with per-rubric `lens_weight_share` weights (per plan ~L771; ~200 LOC of weight spec across SEO 17%, backlink 6%, AI visibility 9%, conversion 11%, etc.). Question: "how does this prospect score, expressed as a number a sales rep can show to a prospect?" Answer: a graded scalar with bands red/yellow/green.
- **Autoresearch geometric mean of LLM judges:** `_geometric_mean(scores, floor=0.01)` in `autoresearch/evaluate_variant.py:59`. Question: "is variant N better than variant N-1, where 'better' means strictly-dominant across multiple judge dimensions?" Geometric mean is the *correct* aggregation for this — arithmetic mean lets a variant win by being great at one dimension and terrible at others; geometric mean penalizes any near-zero score (floor at 0.01 prevents zero-collapse). This is selection-pressure machinery for evolution, not a quality grade.

These are not "three implementations of one pattern." They're three different math objects answering three different questions. A "shared scoring library" would either be (a) so abstract it's useless, or (b) force-fit the answers into one shape and break all three pipelines.

**What would a shared library look like?** It shouldn't.

**Estimated LOC savings if consolidated:** **Negative.** You'd add an abstraction layer and still need pipeline-specific scoring code beneath it.

**Verdict: KEEP DIVERGENT.** Each scoring strategy is correct for its question. The matrix's claim that these are "the same pattern" is wrong — they share the surface (`scores → number`) but the semantics are incommensurable.

---

### Row 4: Runaway-loop backstop

**Underlying need:** Bound the worst-case wall-clock for an agent invocation so a stuck/looping agent doesn't burn unbounded budget.

**Are the three implementations doing the same job?** **Yes, same job, three implementations of the obvious primitive.**
- Harness: `_AGENT_TIMEOUT = 1800` + `subprocess.run(..., timeout=_AGENT_TIMEOUT)` + `config.max_walltime` (4h default) at orchestrator level (`harness/engine.py:38`, `harness/run.py:104`).
- Audit plan: `max_turns=500/800/400` Claude SDK sentinel passed at session-open time (per plan ~L705).
- Autoresearch: `META_AGENT_TIMEOUT = 1800` + `signal.alarm(max_generation_seconds)` + `_terminate_process()` SIGTERM-then-SIGKILL helper (`autoresearch/evolve.py:34, 79-87`).

The shape is identical: a number + a kill mechanism. The differences are mechanical:
- **Sentinel granularity:** harness/autoresearch use seconds (subprocess timeout); audit plan uses turn-count (Claude SDK doesn't expose seconds-timeout cleanly because sessions are async and sub-tool-call slow).
- **Kill mechanism:** harness uses `subprocess.TimeoutExpired`; autoresearch uses `os.killpg(SIGTERM)` + grace + `SIGKILL`; audit plan uses Claude SDK session-close.

**What would a shared library look like?**
```python
# src/shared/timeouts.py — ~30 LOC
def graceful_kill(proc: Popen, reason: str, grace_s: int = 10) -> None:
    """SIGTERM → wait grace_s → SIGKILL. Process-group aware on Unix."""
def with_walltime(deadline_s: int, *, on_expire: Callable[[], None]) -> None: ...
```

But honestly: this is so small and so context-specific (the audit plan's sentinel is in turn-count, not seconds, and lives inside Claude SDK session config — it can't share a Python helper) that a library is overkill.

**Estimated LOC savings:** ~30 LOC if the harness and autoresearch share `graceful_kill`. The audit plan does not benefit because its sentinel is a Claude SDK config field.

**Verdict: PARTIAL — share the `graceful_kill` helper between harness and autoresearch (already a `_terminate_process` pattern in both); skip the audit plan.** This is too small for its own library; it belongs in a `src/shared/process.py` utility module if anything.

---

### Row 5: Permissions / safety model

**Underlying need:** Constrain what an autonomous agent can do, so a misbehaving agent can't (a) mutate state outside its remit, (b) leak secrets, (c) take irrecoverable actions, (d) DOS external services.

**Are the three implementations doing the same job?** **NO — and this is the most important "no" in the matrix.** The three pipelines have legitimately different threat models:
- **Harness fixer:** *MUST* mutate code; the whole point is to have the agent edit `cli/freddy/` files. Capability restriction is impossible — you can't take away `Write` and still have a fixer. Safety here is **post-hoc scope check** (`harness/safety.py:check_scope`: regex allowlist per track) + **post-hoc leak check** (`safety.py:check_no_leak`: was anything outside the worktree dirtied?) + **rollback-on-violation** in `run.py:_process_finding`. The model is "let it edit, then verify it stayed in lane, otherwise rollback." This is the right model for the threat. The 3-of-5 plan-2 correctness bugs in this code (commits `771027f`, `128b43a`, `ff2f2e4`, `b6f3a61`, `e3d7537` over the last week) are not fundamental — they are the cost of a young implementation, not evidence the model is wrong.
- **Audit-plan agents:** READ + emit findings only. They walk web pages with WebFetch/WebSearch, scrape, and emit a `Finding[]`. They do NOT need Bash/Write/Edit on the prospect's site. Capability restriction (per plan R4 ~L275: `build_demo_flow_toolbelt()` exposes `page.goto`, `locator.screenshot`, `locator.get_attribute` only; no `page.click`, no `page.fill`, no `page.evaluate`) **is strictly stronger than allowlists** because the destructive capability isn't in the toolbox at all. Plan explicitly notes URL-blocklist hooks were dropped because "blocklists are infinitely bypassable (URL encoding, nested paths, agent routes around via WebFetch)."
- **Autoresearch:** Calls Freddy backend via REST (`X-API-Key: ${FREDDY_API_KEY}` header — `evolve.py:46-50`); the agent invokes a CLI subprocess with auth credentials. Safety relies on (a) the backend's own API authorization, (b) agent prompts' "Hard Rules" (e.g., `competitive-session.md:191`: "Never touch git state — the harness owns commit/rollback; never edit evaluator scripts; never copy artifacts from `_archive/`"). This is **honor-system** — there's no enforcement, just instruction. It works because the autoresearch agent runs in a sandbox-like sealed variant directory with no path-write access to the rest of the repo (lane ownership in `lane_paths.py`).

The threat models are genuinely different: harness fixes code (post-hoc check), audit reads (capability restriction is feasible and superior), autoresearch evolves prompts (honor system + sandbox).

**What would a shared library look like?** A small `src/shared/safety/` with three explicit tiers, not one model:
```
TIER A — read-only (audit-plan): build_scoped_toolbelt(allowed_tools)
TIER B — sandboxed-write (autoresearch): variant_sandbox + lane_ownership_check
TIER C — repo-write-with-rollback (harness): scope_allowlist + post_hoc_check + rollback
```

Each pipeline picks its tier explicitly. Library publishes the three primitives; pipelines opt in. The "convergence" is **naming the tiers and writing them down**, not collapsing them into one mechanism.

**Estimated LOC savings:** Modest — maybe 50 LOC. The real win is conceptual: a future engineer looking at any of the three pipelines knows immediately *which tier* it's on, and the audit plan's `scoped_tools.py` becomes reusable when the harness eventually grows a read-only sub-agent (e.g., an inventory agent).

**Verdict: STRATIFY EXPLICITLY — name three tiers, share primitives, do NOT unify.** See F6.2 below for full analysis.

---

### Row 6: Reporting / rendering

**Underlying need:** Take pipeline output (findings, scores, narratives, logs) and render a human-consumable artifact (Markdown, HTML, PDF) with sections, badges, code blocks, secret scrubbing.

**Are the three implementations doing the same job?** **Yes — and `autoresearch/report_base.py` is already 80% of the shared library.** Look at it: `parse_findings`, `render_findings`, `render_session_log`, `render_logs_appendix`, `render_session_summary`, `build_html_document`, `BASE_CSS`, `BADGE_COLORS`, `find_chrome`, `html_to_pdf`, `common_argparse`. That's the shape of a reporting library, and the file's docstring says "Shared report generation infrastructure for all autoresearch workflows."

The harness's `review.compose` + `pr_body` (`harness/review.py`) is a tighter, markdown-only version of the same thing — section helpers, secret scrubbing (`_SECRET_PATTERNS` in `review.py:10-18`, more comprehensive than autoresearch has), find-format-emit. The audit plan (Stage 5) hasn't been built yet but plans Jinja2 + WeasyPrint + 9 partials + print CSS — exactly what `report_base.py` provides minus the Jinja2 layer.

The 70% overlap: HTML scaffold, badge rendering, section composition, secret scrubbing (harness has the better regex set), markdown→HTML, PDF via headless Chrome.

**What would a shared library look like?** Promote `autoresearch/report_base.py` to `src/shared/reporting/` (or `src/reporting/` at repo root). Add the harness's secret-scrubbing regex set. Keep the existing renderers (`render_findings`, `render_session_log`, `render_session_summary`). Add a Jinja2 entry point for the audit plan's per-section partials. Each pipeline gets a thin domain-specific generator (~50-100 LOC) that composes shared sections.

```
src/reporting/
  __init__.py
  parsers.py     # parse_findings (md sections + yaml-frontmatter)
  renderers.py   # render_findings, render_session_log, render_summary, ...
  scrub.py       # secret regexes (harness's set, expanded)
  scaffold.py    # build_html_document, BASE_CSS, badge tokens
  pdf.py         # find_chrome, html_to_pdf
  jinja.py       # template loader for audit plan's per-section partials
```

**Estimated LOC savings:**
- Harness `review.py` 109 LOC → ~40 LOC of pipeline glue. Saves ~70 LOC.
- Audit plan Stage 5 (not yet built; plan estimates 9 partials + Jinja2 layer + print CSS, easily 300+ LOC) → ~80 LOC of glue + section partials. Saves ~220 LOC of net-new code that won't have to be written.
- Autoresearch keeps `report_base.py` as the package origin; minimal change.
- **Total: ~290 LOC saved (~70 deleted from harness + ~220 not-written for audit plan).** Plus the audit plan ships faster because it doesn't have to re-design rendering primitives.

**Verdict: GO — top priority.** This is the cheapest, highest-leverage convergence in the matrix. Do it before audit plan U7 (Stage 5: Deliverable) gets built so the audit plan adopts the shared library natively instead of writing its own and being migrated later.

---

### F6.1 verdict — top convergence targets

**HIGHEST LEVERAGE (do these):**
1. **Reporting/rendering** (Row 6) — ~290 LOC saved + audit plan ships faster + visual consistency across all pipelines. Cheapest win.
2. **Findings envelope + parser** (Rows 1+2 together) — ~150 LOC saved, removes a class of regex bugs, gives audit plan an off-the-shelf envelope. Do this AFTER the audit plan ships its Pydantic envelope (let the most-thought-through schema set the shape).

**EXPLICITLY KEEP DIVERGENT:**
3. **Quality scoring** (Row 3) — three different math objects answering three different questions. Forcing convergence would damage all three.
4. **Permissions/safety** (Row 5) — stratify into three tiers, share the primitives (`build_scoped_toolbelt`, `variant_sandbox`, `scope_allowlist`+`rollback`), but do NOT unify behind one interface. Pipelines pick the tier that matches their threat model.

**TRIVIAL — SHARE A HELPER, NOT A LIBRARY:**
5. **Runaway-loop backstop** (Row 4) — extract `graceful_kill` to `src/shared/process.py` (~30 LOC); harness and autoresearch share it. Audit plan stays on Claude SDK sentinel.

**Matrix correction:** the matrix is structurally right that "three pipelines × six patterns" exists, but it overstates "would consolidation simplify a lot." The honest tally is **2 clean wins, 1 small helper, 2 stratify-don't-converge, 1 hard-no.**

---

## F6.2 — Permissions/safety model

### Why three exist (historical)

- **Autoresearch (oldest, copied from Freddy on 2026-04-18, commit `b69690a`)** inherited the honor-system model from a different codebase where it had been validated for months. The "Hard Rules" prompt sections (`competitive-session.md:191`, etc.) are the artifact of that. It works because autoresearch is sandboxed by `lane_paths.py` lane ownership — the agent literally cannot write outside its variant directory because the `lane_runtime.py` checks paths on every edit. Honor system + sandbox = enough.
- **Harness (re-greenfielded 2026-04-21, commit `5900b48` "greenfield rewrite — preservation-first free-roaming agents")** chose `--dangerously-skip-permissions` + regex scope allowlist + post-hoc check + rollback. This is the "let the agent edit anything, then verify it stayed in lane" model. It bought a lot of agent freedom (free-roaming over `cli/freddy/`, `src/`, `frontend/`) at the cost of a rollback-and-verify loop. The 3-of-5 plan-2 correctness bugs came from this loop's edge cases (peer tracks dirtying shared paths, harness-generated artifacts being misclassified as fixer changes, etc. — see commits `771027f` "exclude harness artifacts", `128b43a` "scope leak detection to fixer-reachable paths", `b6f3a61` "process findings before checking agent-signaled-done"). These bugs are real, but they're the cost of the model being correct in shape — none of them suggest the *model* is wrong, only that the implementation has rough edges that are getting smoothed.
- **Audit plan (designed 2026-04-20, R4 update 2026-04-22)** explicitly chose capability restriction *because* it watched the harness's safety bugs. The plan's R4 update at L275 says "URL-blocklist PreToolUse hooks (earlier plan) dropped because blocklists are infinitely bypassable." Capability restriction came from the realization that "what if the agent tries to do X" stops being load-bearing if X isn't in the toolbox at all.

The chronology matters: autoresearch's model is **inherited**, harness's is **chosen** (greenfield 4 days ago, still being smoothed), audit plan's is **designed in reaction** to seeing the harness's churn. Each model is *right for what it's doing*; none of them is the "best model" because they have different jobs.

### Are the requirements actually different across pipelines?

**Yes, fundamentally.** Three different threat models, three different agent capabilities:

| Pipeline | What the agent must do | Threat model | Right safety floor |
|---|---|---|---|
| Harness fixer | Edit code in `cli/freddy/`, `src/`, `frontend/`; commit | Fix touches files outside its track; secret leaks into commit; agent breaks unrelated functionality | Post-hoc scope check + leak check + rollback; secret regex scrub on emit |
| Audit-plan agent | Read prospect website via WebFetch/scrape; emit findings | Agent does irrecoverable action on prospect's site (form submit, link click); agent leaks credentials in transcripts | Capability restriction (no `page.click`, no `page.fill`); per-action human confirmation for destructive ops; OS-keychain credential storage |
| Autoresearch evolver | Modify variant prompts; never touch live system | Variant escape from sandboxed dir; agent modifies evaluator/judge code | Sandbox by `lane_paths.py` ownership + honor-system "Hard Rules" + harness owns git state |

**Capability restriction for the harness is impossible** because the harness's job is to mutate code. You can't take away `Write` and still have a fixer. The audit plan's R4 pattern works for read-only agents and is the strictly superior model when the agent doesn't need to mutate. It would not survive contact with an agent that has to edit code — the moment you re-add `Write`, you're back to "what if the agent writes outside its lane?" which is the question post-hoc-scope-check answers.

### Concrete proposal: stratified safety, named tiers

Don't unify — **name three tiers and write each one down** so future code consciously picks a tier.

```
TIER A — Read-only / scoped-toolbelt
  use case: audit-plan agents, future harness inventory agent
  mechanism: build_scoped_toolbelt() exposing only observation tools;
             per-action human confirmation for destructive ops
  enforcement: capability not in toolbox → impossible to call

TIER B — Sandboxed-write
  use case: autoresearch evolver, future "draft-only" agents
  mechanism: lane_paths.py ownership check on every edit;
             honor-system "Hard Rules" prompt section;
             external git state owned by orchestrator (agent never touches)
  enforcement: filesystem ownership check + prompt discipline + git lockout

TIER C — Repo-write with post-hoc verification
  use case: harness fixers (inherent — they MUST edit code)
  mechanism: regex scope allowlist per track;
             post-hoc scope check + leak check;
             rollback-on-violation; commit only if verified+clean
  enforcement: agent allowed to edit anything, but commits scrubbed and rolled back if out of scope
```

Each pipeline picks its tier in code (`safety_tier = "A"` style). The `src/shared/safety/` package publishes one helper per tier. New agents must declare their tier — no fourth ad-hoc model.

### Migration cost from current state

- **Audit plan:** zero — already designed for Tier A.
- **Autoresearch:** zero — already operating as Tier B (lane ownership + honor system are in place).
- **Harness:** zero — already operating as Tier C; just rename `safety.py` functions and add a `safety_tier = "C"` declaration in `config.py`.
- **Net new code:** ~50 LOC to extract the three primitives into `src/shared/safety/` and document tier semantics. ~20 LOC of test for each tier.

The migration is cheap because the three pipelines are *already* operating at the three tiers. The work is naming and extracting, not rewriting.

### Verdict

**STRATIFY-EXPLICITLY.** Name the three tiers, share the primitives in `src/shared/safety/`, document why each pipeline is on its tier. Do NOT unify — the harness fixer has a fundamentally different job than the audit-plan agent. The 3-of-5 plan-2 harness bugs are NOT evidence the harness's model is wrong; they're evidence the model is recently-implemented and being smoothed (which is what greenfield rewrites cost).

The capability-restriction model from the audit plan is **strictly stronger for read-only agents** and the harness should adopt it for any future read-only sub-agent (e.g., an inventory agent that just lists files). But the harness fixer stays on Tier C — that's the right floor for "agent must edit code I will then commit."

---

## F6.3 — Convergence path / cost analysis

### Cost of status quo

**Bug surface:** Three implementations × six patterns = six mostly-independent bug surfaces per pattern. The harness has shipped 5 correctness bug-fix commits in the last week (`ff2f2e4`, `771027f`, `128b43a`, `b6f3a61`, `e3d7537`) — most in the safety/scope code (3 of 5). The autoresearch findings parser has a known bug profile (line-by-line state machine, fragile on whitespace). The audit plan's reporting layer doesn't exist yet — when it ships, it will go through a comparable bug-discovery cycle if it doesn't reuse `report_base.py`.

Quantification: if you assume the audit plan's reporting layer + envelope parser would generate 3-5 bug-fix commits during its first month (matching harness's curve), that's 3-5 commits avoided per pattern × 2 patterns (envelope + reporting) = **6-10 commits avoided** by sharing those two patterns. The other four patterns (scoring, permissions, timeouts, parsers) either shouldn't share or are too small to matter.

**Onboarding cost:** Currently, a new contributor learning the codebase has to learn three different envelope conventions (YAML front-matter / Pydantic / markdown sections), three different reporting toolkits, three different safety models. That's real — but it's not 3× the cost; it's more like 2× (the patterns rhyme even when they differ). Convergence on rendering + envelope cuts the rhyming-but-different cost.

**Drift:** The biggest hidden cost. As three pipelines evolve, their copy-pasted-but-not-shared patterns drift apart. Example: harness's secret-scrubbing regex set (`review.py:10-18`) is more comprehensive than autoresearch has any equivalent of. If autoresearch ever needs secret scrubbing, it will write a new (probably weaker) set rather than discovering the harness's. Sharing prevents this.

**Divergent capabilities:** The audit plan plans WeasyPrint; autoresearch uses headless Chrome; harness produces only markdown. There's no "right answer" here that one library could enforce — but having one library would force the team to choose a default and let pipelines override, instead of three pipelines independently choosing.

### Cost of consolidation

- **Reporting (`render_lib`):** Promote `autoresearch/report_base.py` (577 LOC) to `src/reporting/`, add the harness's secret-scrubbing set, add a Jinja2 entry point for the audit plan. Migrate `harness/review.py` to use it. Audit plan adopts natively. **Estimate: 1-2 days of work**, ~290 LOC saved net, 3-5 audit-plan reporting bugs avoided.
- **Findings envelope (`finding_lib`):** WAIT for the audit plan to ship its Pydantic envelope (U2 in the plan). Then extract to `src/findings/`, write two parsers (yaml-frontmatter for harness, section-markdown for autoresearch). Migrate harness's `findings.py`. Autoresearch's `report_base.py:parse_findings` becomes one of the parsers. **Estimate: 2-3 days** after audit plan U2 lands, ~150 LOC saved.
- **Safety stratification:** Rename + extract, declare tier per pipeline. **Estimate: 1 day**, ~50 LOC saved + conceptual win.
- **`graceful_kill` helper:** Extract from autoresearch to `src/shared/process.py`, harness adopts. **Estimate: 2 hours**, ~30 LOC saved.

**Total consolidation cost: ~5 days work + ~520 LOC saved + 6-10 bug-fix commits avoided + audit plan ships ~1 week faster.**

### Right phasing

**Order matters because of dependency:** the audit plan's envelope is the schema reference for the convergence; if you converge before it ships, you're guessing.

1. **Week 1 (now):** **`render_lib`** (Reporting). This is independent of every other piece and is purely a refactor of existing code (autoresearch already has the library shape). Highest leverage per day. Audit plan adopts before its Stage 5 gets written.
2. **Week 1 (in parallel, since they're independent):** **`graceful_kill` helper**. 2 hours. Trivial.
3. **Week 1-2:** **Safety stratification** — rename + extract + document. No behavior change in any pipeline; just consolidation of primitives and naming the tiers.
4. **Week 2-4 (gated on audit plan U2):** **`finding_lib`** (Envelope). After audit plan ships its Pydantic `Finding` + `AgentOutput` models, harness and autoresearch back-port to use them.
5. **Never:** Quality scoring (Row 3) — keep three separate. Orchestrator framework — premature.

The reason `render_lib` is first: it's the only convergence where the harness AND autoresearch AND audit-plan-not-yet-built all benefit, and it has zero blocking dependencies. The reason `finding_lib` waits: the audit plan's envelope is the most thought-through; it should set the schema, not be retrofitted.

### When NOT to consolidate

Three places where divergence is correct and consolidation would cause harm:

1. **Quality scoring (Row 3):** binary verifier vs. weighted health-score vs. geometric-mean LLM judges are *three different math objects*. A "shared scoring library" abstraction would force these into a common shape and break the semantics of all three. Keep separate; document why.
2. **Orchestrator state machines:** harness drains per-track queues over multi-cycle iterations with rate-limit graceful-stop; audit plan fans out 7 agents once with `asyncio.gather`; autoresearch evolves variants over generations with `signal.alarm`. These look superficially similar (loop + concurrency + timeout) but the state they track is different (cycles vs. generations vs. one-shot fanout). A shared "agent orchestrator framework" would be the most expensive form of premature abstraction. Each pipeline's orchestrator is ~300 LOC; that's the right amount of code for what it does.
3. **Per-pipeline prompt conventions:** Don't try to unify "how the agent emits its sentinel" or "how the orchestrator signals graceful stop" across pipelines — the harness uses a sentinel file; autoresearch uses session.md status; audit plan uses Claude SDK ResultMessage. These are surface details that should match the agent SDK in use.

### Verdict

**GO on `render_lib` (this week). GO on `graceful_kill` helper (this week, trivial). GO on safety stratification (this week, naming exercise). GO-LATER on `finding_lib` (3-4 weeks out, after audit plan U2).** NO-GO on quality scoring, orchestrator framework, prompt conventions.

**Net:** ~5 days of consolidation work over a 4-week window saves ~520 LOC, prevents 6-10 bug-fix commits in the audit plan's first month, makes future read-only sub-agents (in any pipeline) have an obvious safety pattern to copy, and gives the team one visual language for run/audit reports. **It pays back, but only if you do the right two patterns and explicitly do NOT do the wrong four.** The matrix's "three implementations of six patterns" framing tempts a "do all six" answer that would over-consolidate and damage the three pipelines that are working. Two clean wins + one helper + one stratification = correct.

The biggest risk is *not* under-consolidating; it's over-consolidating. The orchestrators look the most "convergeable" of any pattern in the codebase and would be the worst thing to converge. Resist that temptation.
