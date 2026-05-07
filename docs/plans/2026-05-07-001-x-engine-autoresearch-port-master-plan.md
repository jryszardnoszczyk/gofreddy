# X Engine → Autoresearch Port — Master Plan

**Status:** v7 LOCKED 2026-05-07. Iterated through 4 review rounds; v7 trims plan-document over-engineering after JR pushback that v6's 919 lines exceeded the marketing-audit master plan (1,134 lines for a ~10× larger build). Architectural premises preserved; prose anchored to existing 4 lanes' reference implementations (`archive/v007/workflows/{geo,competitive,monitoring,storyboard}*` + `programs/geo-session.md`) rather than recapitulating the contract.

**Canonical references (NOT superseded):**
- `~/.claude/.../memory/project-autoresearch-evolution-fixes-pending.md` — autoresearch loop state (validated end-to-end)
- `~/.claude/.../memory/feedback-harness-evaluator-bias-and-verifier-roi.md` — judge-bias risk
- `~/.claude/.../memory/feedback-no-mid-build-pushes-on-agent-built-runs.md` — worktree discipline
- `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md` — structural template
- `autoresearch/lane_registry.py:22-46` — `LaneSpec` contract
- `autoresearch/archive/v007/workflows/specs.py:32-44` — `WorkflowSpec` contract
- `autoresearch/archive/v007/workflows/session_eval_common.py:17-25` — `SessionEvalSpec` contract
- `autoresearch/archive/v007/programs/geo-session.md` — concrete reference for the evolvable agent prompt
- `autoresearch/archive/v007/scripts/evaluate_session.py` — in-session evaluator pattern
- `judges/evolution/prompts/scorer.md` — final-scoring judge prompt + 0-10 scale
- `autoresearch/evaluate_variant.py:836-933` — agent subprocess invocation
- `autoresearch/evaluate_variant.py:1101-1184` — judge call shape

**Operator procedures + JR's decision gates** are in §7.11 (no separate companion file).

---

## §1 — Goals, Non-Goals, North Star

### 1.1 Thesis

x_engine v1 ships and works (5 ship-eligible drafts/run, 80–130s wall time, $0/run via codex). It cannot keep getting better without me/JR hand-tuning prompts. There is no held-out evaluation. There is no automatic regression detection.

Autoresearch already runs the kind of loop x_engine needs: subprocess-isolated agent reads an evolvable program prompt, uses CLI tools to produce deliverables, deliverables get scored by a judge service against per-domain criteria, holdout gates promotion. The loop is empirically validated end-to-end as of 2026-05-06 (v007 promoted on geo with proper holdout refusal on a regression). *[source: project-autoresearch-evolution-fixes-pending.md]*

The port is **not** a 1-to-1 migration. v1 is roughly 8× the seed it needs to be. *[source: x_engine seed audit 2026-05-07]* The port keeps what evolution can't improve (data plumbing, deterministic policy gates, JR's identity), drops what evolution should improve (the agent's writing approach), and discards what existed only because v1 had no autoresearch lane to lean on (agentic mode, dual compose, 4-prompt split, 6-voice-file tower).

### 1.2 Goals (in priority order)

1. Add a workflow lane named `x_engine` to the autoresearch registry, producing ship-eligible draft posts on a per-fixture basis, scored on a 6-dimension rubric (X-1..X-6, 0–10 per criterion).
2. The seed is a single evolvable agent prompt (`programs/x_engine-session.md`, ~150–180 lines) plus a small static voice reference. Everything else is autoresearch infrastructure or `xeng` CLI tools that already exist.
3. Build the holdout signal first. Until JR has marked ≥25 drafts (ship/skip + structured reason), the lane runs blind. L1 is purely the prerequisite work; the lane scaffold doesn't land until L1 is provably populated.
4. Day-1 seed quality may be worse than v1. That is acceptable. Evolution earns the quality back. v1 stays running daily, in parallel, until the lane wins on holdout.
5. Survive contact with the existing autoresearch contract — `WorkflowSpec` + `SessionEvalSpec` + 6 lane-name registries that drift-gate against each other. v1 of the plan understated this; v2 enumerates every edit point.

### 1.3 Non-goals

- Auto-posting to X. Manual posting stays.
- Mutating `voice/about-me.md`, `voice/no-go-topics.md`, `pull.py`, `slop_gate.py`, or `sources.yaml` in v1 of the lane.
- Per-pillar lanes (one lane initially).
- Preserving v1's agentic (codex-spawn-codex) mode. It is dropped.
- Net-new judge agents. v1 of the lane uses the existing variant-scorer judge (`/invoke/score` → `scorer.md`). New judge agents are a v2 lever.
- Inline `call_llm()` in the lane runtime. Autoresearch does not call LLMs from `workflows/<lane>.py` — the agent (claude/codex/opencode subprocess) does all LLM work, driven by `programs/<lane>-session.md`.

### 1.4 North star

A daily run that produces 1–3 ship-eligible drafts using the latest evolved variant; JR ships 0–2; ship/skip decisions feed back into the holdout; quality is provably non-decreasing across promotions.

Quantitative success bar: **for 4 consecutive promotion cycles, the new variant must improve OR hold the holdout aggregate score over the prior baseline.** A regression triggers auto-rollback (existing autoresearch primitive). Score scale is the judge's 0–10 (per `scorer.md`).

### 1.5 Locked decisions (D1–D9) and open questions (Q1–Q2)

**Locked (lock confirmed by reading reference implementation, not a research summary):**

- **D1: Workflow lane, not core.** `is_workflow_lane=True`. Per-domain scoring: `_objective_score_from_scores(scores, "x_engine")` reads `scores["x_engine"]` (top-level). *[source: evaluate_variant.py:1538-1546]*
- **D2: Lane name = `x_engine`.**
- **D3: Rubric prefix = `X` → 6 IDs `X-1 … X-6`, hardcoded inline.** Plan §4.1 inlines the 6-tuple `("X-1","X-2","X-3","X-4","X-5","X-6")` rather than calling `_rubric_ids("X")` (the helper is hardcoded to range(1,9), produces 8 IDs). All other consumers of `len(rubric_ids)` audited at L0 (see §4.2).
- **D4: The single evolvable artifact is `programs/x_engine-session.md`.** No separate `writer_voice_block.md`. Static voice references live at `programs/references/x_engine-voice.md` (read-only excerpt of `voice/about-me.md` + `voice/no-go-topics.md`).
- **D5: Lane runtime is agent-driven via `python3 <variant>/run.py --domain x_engine <client> <context> <max_iter> <timeout>`** — same dispatcher path all 4 existing lanes use. The agent (claude/codex/opencode) uses `xeng` CLI tools as its tool layer; no `x_engine.pipeline.*` Python imports inside the variant subprocess. → Python surface in `archive/<v>/workflows/` is hooks only (~160 LOC: WorkflowSpec ~80 + SessionEvalSpec ~80). *[source: evaluate_variant.py:846-865; replaces v5's separate D5+D9 which were redundant]*
- **D6: Parallel-run for 7 days post-first-runnable; JR-preference qualitative gate.** JR reviews both v1 and lane outputs daily, logs preferred-source. Day-7 verdict: lane wins ≥3 of 7 days → switch primary daily output to lane. (No quantitative margin in v1 — v1 has no `/invoke/score` aggregate to compare against; quantitative comparator is v2 work.) Operator-side log file path + line format: see operator memory.
- **D7: Drop the writer-critic revise loop entirely in seed.** Evolution replaces revision; the agent writes one variant per angle, in-session evaluator scores it, slop gate filters, ship decision recorded.
- **D8: Backfill new lane only into the seed-baseline variant.** Older variants score 0.0 on this lane (default behavior on missing scores key). Frontier starts at seed-baseline. **L0 verification step:** confirm dispatch path: when search-v1 manifest's `domains.x_engine[]` routes a fixture to a non-seed variant's `run.py`, what happens? Plan v2 asserted "scores 0.0" — actually we need to verify whether `get_workflow_spec("x_engine")` raises `KeyError` (→ crash) or is gracefully skipped (→ 0.0). *[uncertainty source: feasibility/adversarial review F9 2026-05-07]*
- **D9: L1 day 0 = revive v1 cron.** v1's LaunchAgent is currently not loaded; `recent_posted` is empty. The 14-day dogfood clock cannot start until v1 produces drafts daily.

**Open (resolve before L0 starts):**

- **Q1: Holdout score granularity — binary (ship/skip) or 1–5 nuance?** Lean: binary, with `skip_reason` as structured enum. The 1–5 column is a v2 lever and does NOT ship in L1.
- **Q2: Seed-baseline variant — extend `archive/v007/` (Option A) vs branch fresh `archive/v007-curated/` (Option B)?** Lean: B. *Cross-lane contamination risk for both options surfaced in adversarial review F9 — see D8 verification step. Q2 is non-trivial; the L0 verification of D8 may surface evidence that flips the lean. JR sync at L0 day 0 should weigh this, not 30-min rubber-stamp.*

---

## §2 — Deliverable Shape

### 2.1 Per-fixture session output

The agent runs inside `<variant_dir>/sessions/x_engine/<client>/`. Layout mirrors geo's pattern *[shape source: archive/v007/programs/geo-session.md "Workspace" section]*:

```
sessions/x_engine/<client>/
├── session.md                # agent's state file, rewritten each iteration
├── results.jsonl             # phase event log (gather/draft/critique/log)
├── angles/<angle_id>.json    # ranked-evidence cache for each angle
├── drafts/<draft_id>.md      # the deliverable — one markdown file per draft
├── drafts/<draft_id>.eval.json   # in-session evaluator output (structural + judge critique)
├── findings.md               # cross-draft observations
└── report.md                 # final per-session summary
```

**Why `<client>` is `jr`** — for x_engine the only client is JR himself. The fixture's `client` field is `"jr"` for every fixture in this lane.

### 2.2 Draft markdown shape

Each `drafts/<draft_id>.md` is structured so the deterministic `structural_gate` can verify it without running an LLM. *[shape source: geo-session.md `[INTRO]` + `[FAQ]` blocks pattern]*

```markdown
---
draft_id: jr-2026-05-07-001
angle_id: angle-2026-05-07-001
length_bracket: build
char_count: 537
voice_pillar: harness-engineering
---

[BODY]
<post body — 250-1500 chars depending on length_bracket>
[/BODY]

[REPLY]
<optional reply with URL + frame>
[/REPLY]

[META]
hook: <first 8-12 words>
authority_anchor: "<JR's lived-work claim, exact phrase>"
specific_number: "<at least one number/$/% in body>"
attribution: "<named tool / @-mention / public datapoint / repo URL>"
[/META]
```

The structural_gate verifies: file exists, char_count within bracket range, `[BODY]` block non-empty, `[META]` block has all 4 keys, `specific_number` and `attribution` are non-empty strings, slop_gate regex passes against body text (delegated to existing `xeng slop-check` CLI).

### 2.3 Fixture context shape

Holdout fixture entry (per `eval_suites/SCHEMA.md:18-32`):

```json
{
  "fixture_id": "jr-2026-05-07-001",
  "client": "jr",
  "context": "42",
  "version": "1.0",
  "max_iter": 1,
  "timeout": 600,
  "anchor": true,
  "env": { "JR_GROUND_TRUTH": "ship", "SKIP_REASON": "" }
}
```

`context` is `str(angle_id)` — the string repr of `angles.angle_id` (INTEGER autoincrement primary key in `x_engine/pipeline/db.py`). The agent at session start runs `xeng angle-show <int_id>` to load the full angle (headline, claim, source_url, source_text, voice_pillar). State.db is the source of truth for angle records. Stable cache key per SCHEMA.md:26 ("session-side CLI commands must pass the same string for cache hits").

`anchor=true` when JR has marked the corresponding draft via `xeng mark-posted` (→ ship) or `xeng skip-draft` (→ skip with reason). Fixtures with `anchor=false` are search-suite-only.

`env.SKIP_REASON` is a structured enum (lookahead — see §5.3): one of `voice_off | factual_unverifiable | off_pillar | duplicate | no_time | other`. Empty when shipped. Holdout-export filters out `no_time` rows (operator-noise; not a quality signal). *[mitigation source: feasibility/adversarial review F2 2026-05-07]*

### 2.4 Search-suite vs holdout-suite split

| Suite | File | Lane domain entry | Purpose | Cache policy |
|---|---|---|---|---|
| Search | `autoresearch/eval_suites/search-v1.json` `domains.x_engine[]` | 5–10 fixtures (rotating; can include unmarked angles) | Cohort scoring during evolution | `live_fetch` |
| Holdout | `~/.config/gofreddy/holdouts/holdout-v1.json` `domains.x_engine[]` | 20–30 fixtures with `anchor=true` (JR-marked drafts) | Promotion-gate verdict | `hard_fail` |

### 2.5 Final scoring path

After the agent subprocess exits, `evaluate_variant.py` materializes all text artifacts under `session_dir` (cap 800KB total, 200KB per file; binary skipped) and POSTs to `EVOLUTION_JUDGE_URL/invoke/score`. The judge service applies `judges/evolution/prompts/scorer.md` (loaded by `judges/evolution/agents/variant_scorer.py:66-71`) and returns:

```json
{
  "fixture_id": "jr-2026-05-07-001",
  "per_criterion": [
    {"criterion": "X-1", "score": 7, "rationale": "..."},
    ...
  ],
  "aggregate_score": 7.4,
  "structural_passed": true,
  "grounding_passed": true,
  "notes": "..."
}
```

**Score scale is 0–10 in the judge output** (scorer.md:24). The rubric prose blocks in `src/evaluation/rubrics.py` use 1/3/5 anchor format; the judge interpolates 0–10 from the 1/3/5 anchors. `aggregate_score` is the per-fixture domain score; `_objective_score_from_scores` reads this from `scores["x_engine"]`.

**CRITICAL — judge prompt has NO `{criteria}` placeholder.** `scorer.md` line 3 hardcodes "score one variant's session artifacts against the 8-criteria rubric for the specified domain"; `variant_scorer.py:66-71` only formats `{domain, fixture, session_ref, artifacts}`. The judge LLM is told "score the rubric" without being told what the criteria are — it relies on its prior knowledge of `{domain}` (works for `geo`/`competitive`/`monitoring`/`storyboard` because those have public-domain priors). For `x_engine` (a JR-private lane), the LLM has no prior. First iteration would produce hallucinated noise.

**v5 fix — judge-prompt criteria injection (L0 prerequisite, see §7.2):**

Two prompt templates, not one. Existing 4 lanes preserve their baseline; x_engine gets criteria injection.

1. **Keep `judges/evolution/prompts/scorer.md` UNCHANGED** for the existing 4 lanes (line 3 still says "the 8-criteria rubric for the specified domain" — preserves their LLM-prior baseline). v4's rewrite would have broken them per Round-3 B7.
2. Author a NEW prompt `judges/evolution/prompts/scorer_x_engine.md` that explicitly includes `{criteria}` placeholder + 6-criteria scoring schema:
   ```
   You are a domain-quality scoring judge for the gofreddy evolution loop.
   Score one variant's session artifacts against the rubric below.

   <criteria>
   {criteria}
   </criteria>

   <domain>x_engine</domain>
   <fixture>{fixture}</fixture>
   <session_ref>{session_ref}</session_ref>
   <artifacts>{artifacts}</artifacts>

   Respond with a fenced JSON block (per_criterion 0-10, aggregate_score 0-10, structural_passed, grounding_passed)
   ```
3. Modify `judges/evolution/agents/variant_scorer.py:22-71`: branch on `payload["domain"]`. For x_engine → load `scorer_x_engine.md` + format with `criteria=_render_criteria_for_domain("x_engine")`. For other domains → load existing `scorer.md` unchanged. Net: ~10 LOC dispatch + ~10 LOC helper.
4. `_render_criteria_for_domain("x_engine")` filters `RUBRICS` by `domain="x_engine"` and concatenates the 1/3/5 prose blocks. **Curly-brace escape:** prose contains `{` and `}` literals; pre-escape via `text.replace("{","{{").replace("}","}}")` before `.format()`.
5. The criteria source is `src/evaluation/rubrics.py:RUBRICS` — the same file that gets 6 new `_X_N` blocks at §4.2 row 3.

Net: ~25 LOC of net-new infra (prompt + dispatch + helper). Out-of-scope for a "lane port" but unavoidable for x_engine. ~0.5 day. Lands at L0 before L1 dogfood begins. Two-template approach avoids regressing the existing 4 lanes' tuned baseline.

---

## §3 — Seed Architecture

### 3.1 Cull table (file-by-file decision)

*[source: x_engine seed audit 2026-05-07; condensed, with corrections from review]*

**KEEP-ESSENTIAL (sibling library, unchanged):** `pull.py` (457), `slop_gate.py` (134), `rank.py` (116), `db.py` (collapse to ~80), `sources.yaml` (frozen).

**KEEP-COLLAPSED (reduce surface to what the agent's CLI tools need):** `cli.py` → 10 subcommands (`pull-search`, `pull-user`, `pull-github`, `pull-rss`, `top-tweets`, `top-releases`, `top-rss`, `slop-check`, `mark-posted`, `skip-draft`, `feedback`, `holdout-export`, `angle-show`, `angle-list`, `info`). The agent uses these the way geo's agent uses `freddy`. Drop the rest.

**DROP (replaced by autoresearch + agent-driven model):** `agentic.py` + `agentic_master.md`, `prompts/topic_picker.md`, `prompts/writer.md`, `prompts/critic.md`, `prompts/slop_check.md`, `pipeline/topic_pick.py`, `pipeline/draft.py`, `pipeline/compose.py`, `bootstrap_from_cache.py`, `run.sh`.

**KEEP-MANUAL (JR-authored; never evolves):** `voice/about-me.md`, `voice/no-go-topics.md`, `voice/exemplars.md`. Excerpts copied into `archive/<seed-baseline>/programs/references/x_engine-voice.md` at L2 time, version-stamped, locked via `readonly_subprefixes` chmod 0444 + per-session re-chmod in `WorkflowSpec.configure_env()`.

**FOLD:** `voice/profile.md` + `voice/hooks.md` + `voice/anti-ai-writing-style.md` → fold into `archive/<seed-baseline>/programs/x_engine-session.md` (the evolvable agent prompt). Most of `anti-ai-writing-style.md` overlaps with `slop_gate.py` regex; the unique 20% (the meta-rules about voice tells) lands inline.

**KEEP:** `schemas/*.json` (used by `xeng` CLI commands that emit structured output).

**KEEP:** v1's `install_schedule.sh` + `.plist` (D6 parallel-run requires v1 cron loaded — D10).

### 3.2 Net LOC budget

| Tier | Before (v1) | After (seed) | Δ |
|---|---|---|---|
| `x_engine/` total (Python + tests + voice files + sources.yaml + prompts) | ~3,983 | ~1,200 | −70% |
| New under `archive/<seed-baseline>/programs/` (evolvable + references) | n/a | ~250 (session.md ~180 + references ~70) | net new |
| New under `archive/<seed-baseline>/workflows/` (Python) | n/a | ~160 (WorkflowSpec ~80 + SessionEvalSpec ~80) | net new |
| New under `archive/<seed-baseline>/templates/` | n/a | 0 (none needed at v1) | — |
| Other autoresearch edits (LANES, registries, EvaluateRequest, evaluate_session.py choices, rubrics.py) | n/a | ~30 | net new |

**Total net new code in autoresearch:** ~440 LOC. Total seed reduction in `x_engine/`: ~2,800 LOC. The lane code is ~10× smaller than v1 because most of v1's logic (writer pass, critic pass, revise pass, parallelism) collapses into "the agent reads the prompt and does the work."

### 3.3 The single evolvable artifact: `programs/x_engine-session.md`

**Target ~100 lines for v1 seed** (down from v2's 150-180). geo-session.md is 222 lines after ~7 generations; the seed should be deliberately smaller and let evolution grow it. Sections:

```
# X-Content Drafter — {client}                               (header, ~3 lines)

You are JR drafting an X/Twitter post...                     (agent identity, ~5 lines)
Voice substrate: programs/references/x_engine-voice.md       (1-line pointer)

## Quality Criteria — Your Fitness Function                  (~25 lines)
  X-1 Voice match (plain language is part of voice — see voice substrate)
  X-2 Factual specificity (SOURCE claims must verify; INTERPRETIVE claims framed as JR's view)
  X-3 Hook strength
  X-4 Slop freeness (deterministic gate enforces a floor)
  X-5 Structural richness (bracket-aware)
  X-6 Cross-draft diversity (cohort-level pillar balance + no two drafts share primary differentiator)

## Length brackets                                           (~15 lines)
  SHARP (250-300) / BUILD (500-900) / CASE-STUDY (1000-1500) ranges + when-to-use

## Workspace                                                 (~8 lines)
  sessions/x_engine/jr/ layout + first-action protocol

## Tools Available                                           (~12 lines)
  xeng angle-show <id>           load angle from state.db
  xeng top-tweets|releases|rss   inspect ranked evidence
  xeng slop-check <text>         deterministic policy gate (call before writing)
  python3 scripts/evaluate_session.py --domain x_engine --artifact ...

## Format Specifications                                     (~10 lines)
  Drafts must conform to the §2.2 markdown shape (frontmatter + [BODY] + [META])

## Hard Rules                                                (~12 lines)
  No git operations, no fabricated experience, no banned phrases (slop_gate),
  no fabricated JR-lived-experience claims (cross-check against voice substrate)

<!-- AUTOGEN:STRUCTURAL:START -->                            (autogen block — locked)
<!-- AUTOGEN:STRUCTURAL:END -->
```

**Cuts from v2's outline:** detailed plain-language rules (~25 lines) move into the voice substrate; agent reads it on every iteration. Hook bank + skeletons + 12-row swap table — drop from seed; evolution grows them. Progress-logging section folds into one bullet under Workspace.

**Mutation surface** — what evolution may change:
- Length-bracket char ranges + when-to-use guidance
- Quality-criteria phrasing (NOT the X-1..X-6 IDs)
- Hard rules ordering / phrasing
- Tool-list emphasis
- Workspace protocol details

**Mutation locks** (file-system enforced via `readonly_subprefixes`):
- `programs/references/x_engine-voice.md` — JR-authored voice substrate. `readonly_subprefixes` enforces chmod 0444 at variant materialization (`autoresearch/archive_index.py:280-356`); meta-agent edits trip `ScopeViolation` at `sync_variant_workspace`. No additional SHA check needed at session-time — chmod is the lock.
- The 6 rubric IDs and prose anchors (X-1..X-6) — defined in `session_eval_x_engine.py:CRITERIA` (in `readonly_subprefixes`).

There is no AUTOGEN block in `programs/x_engine-session.md` (the `structural_doc_facts=()`/`structural_gate_functions=()` empty pair removes it; structural facts live in the prompt's "Hard Rules" + "Format Specifications" sections directly).

### 3.4 The agent's CLI tool surface

The agent uses `xeng` exactly the way geo's agent uses `freddy`. Required CLI commands (most already exist in v1):

| Command | Purpose | New in v3? |
|---|---|---|
| `xeng angle-show <id>` | Load angle JSON (headline, claim, source_url, source_text, voice_pillar) | NEW |
| `xeng angle-list [--days N]` | List recent angles ordered by `picked_at DESC` (NOT resonance — resonance is on `tweets` table, not `angles`) | NEW |
| `xeng top-tweets [--days N]` | List ranked tweet evidence | exists |
| `xeng top-releases [--days N]` | List ranked GitHub releases | exists |
| `xeng top-rss [--days N]` | List ranked RSS items | exists |
| `xeng slop-check <text>` | Deterministic policy gate | exists |
| `xeng mark-posted <draft_id>` | Record JR's ship to `draft_decisions` table (NEW table; not the existing `recent_posted` which is engagement-only) | exists, expanded |
| `xeng skip-draft <draft_id> --reason <enum>` | Record JR's skip to `draft_decisions` with structured reason | NEW |
| `xeng holdout-export [--output]` | Convert `draft_decisions` → holdout fixtures (filters operator-noise `no_time` rows) | NEW |
| `xeng info` | Inventory CLI for debugging | exists |

**`xeng feedback` (1-5 score) is NOT in L1.** Q1 is locked-binary; the 1-5 column is a v2 lever. Drop from L1 work item list.

The agent does NOT have access to v1's `compose`, `draft-angle`, `write-vault`, `write-drafts`, `topic-pick` commands — those collapse into the agent prompt.

### 3.5 Parallel-run discipline (D6)

For 7 days post-first-runnable: v1 cron writes daily to `x_engine/drafts/YYYY-MM-DD.md`; lane runs daily on the same set of angles via fixtures sourced from the same evidence pool. JR reviews both per the §1.5 D6 protocol. Day-7: lane wins on JR-preference in ≥3 of 7 days → switch primary daily output to lane (v1 cron stays armed ≥30 more days as rollback). Trajectory positive but not 3-of-7 → extend 7 more days. Trajectory flat/negative → pause, diagnose. v1 cron file (`install_schedule.sh` + `.plist`) is NOT deleted in v1 of the lane.

---

## §4 — Lane Architecture

### 4.1 LaneSpec entry

Append to `LANES` dict at `autoresearch/lane_registry.py:73-184`:

```python
"x_engine": LaneSpec(
    name="x_engine",
    is_workflow_lane=True,
    rubric_ids=("X-1", "X-2", "X-3", "X-4", "X-5", "X-6"),   # inlined; do NOT use _rubric_ids("X")
                                                              # — helper hardcoded to range(1,9)
    path_prefixes=(
        "programs/x_engine-session.md",
        "programs/x_engine-evaluation-scope.yaml",
        "programs/references/x_engine-voice.md",
        "templates/x_engine",
        "workflows/x_engine.py",
        "workflows/session_eval_x_engine.py",
    ),
    readonly_subprefixes=(
        "workflows/x_engine.py",
        "workflows/session_eval_x_engine.py",
        "programs/references/x_engine-voice.md",
    ),
    session_md_filename="x_engine-session.md",
    deliverables=("drafts/*.md",),
    intermediate_artifacts=("angles/*.json", "drafts/*.eval.json"),
    structural_doc_facts=(),       # empty — see note below
    structural_gate_functions=(),  # empty — see note below
),
```

**Empty-on-both pair** signals "no AUTOGEN sync." `tests/autoresearch/test_structural_doc_facts.py:44-54` requires a 3-line `pytest.skip()` carve-out for lanes that opt out (mirrors `monitoring` carve-out at lines 117-120). Real runtime structural gating lives in `SessionEvalSpec.structural_gate` (§4.4).

### 4.2 Drift gate — 8 surfaces

| # | File | Edit | Estimate |
|---|---|---|---|
| 1 | `autoresearch/lane_registry.py:73-184` | Append `"x_engine": LaneSpec(...)` per §4.1 (inline rubric_ids tuple) | 0.1 day |
| 2 | `src/evaluation/models.py:160` | Add `"x_engine"` to `EvaluateRequest.domain` Literal **AND** audit `src/evaluation/` for switch-on-domain handlers. If x_engine flows through `/v1/evaluation/evaluate` route handlers, add x_engine branches; if scoring-only, document so. | 0.25 day |
| 3 | `src/evaluation/rubrics.py` | **REAL WORK:** author 6 new prose blocks `_X_1`..`_X_6` in 1/3/5 anchor format (~30-40 lines each, mirroring `_GEO_1`..`_GEO_8` pattern); add 6 entries to `RUBRICS` dict at line 949+ as `RubricTemplate("X-N", "x_engine", "gradient", _X_N, is_cross_item=...)`. **Per-criterion `scoring_type`:** X-1, X-2, X-3, X-5 = "gradient" (1/3/5 anchors). X-4 (slop_freeness, deterministic floor) and X-6 (cohort coherence) = "checklist" (4 binary YES/NO sub-questions per existing pattern at line 956 GEO-6). Mark X-6 with `is_cross_item=True`. Update `assert len(RUBRICS) == 32` at line 1001 to `38`. | **1 day** |
| 4 | `archive/<seed-baseline>/workflows/__init__.py:10-15` | Append `"x_engine": X_ENGINE_SPEC` to `WORKFLOW_SPECS` + import | 0.05 day |
| 5 | `archive/<seed-baseline>/workflows/session_eval_registry.py:10-15` | Append `"x_engine": X_ENGINE_SESSION_EVAL_SPEC` to `SESSION_EVAL_SPECS` + import | 0.05 day |
| 6 | `archive/<seed-baseline>/scripts/evaluate_session.py:402` | Update argparse `choices=[...]` list to include `"x_engine"` | 0.05 day |
| 7 | `judges/evolution/prompts/scorer_x_engine.md` (NEW file) | Author NEW prompt with `{criteria}` placeholder + per-criterion JSON output schema. **DO NOT modify the existing `scorer.md`** | 0.1 day |
| 8 | `judges/evolution/agents/variant_scorer.py:22-71` | Branch on `payload["domain"]`: for `x_engine` load `scorer_x_engine.md` and format with `criteria=_render_criteria_for_domain("x_engine")`; for other domains load existing `scorer.md` unchanged. Add `_render_criteria_for_domain` helper that filters `RUBRICS` by `domain="x_engine"` and concatenates curly-brace-escaped 1/3/5 prose blocks | 0.4 day |
| (folded into row 1) | Stale-doc surfaces in `eval_suites/SCHEMA.md` + `eval_suites/TAXONOMY.md` are documentation drift; update inline as part of row 1 LaneSpec edit, not a separate work item | — |

`_assert_models_literal_matches()` at `lane_registry.py:272-284` hard-fails on (1)+(2) drift. `rubrics.py:1001-1017` has THREE runtime assertions covering (1)+(3): `len(RUBRICS)==32` literal count, `_lane_rubric_ids ⊆ RUBRICS`, and `sum(rubric_ids per spec) == len(RUBRICS)`. Total assertion count makes (3) load-bearing — it's not a cosmetic registry update.

**Pre-L1 verification** (L0): rows 7 + 8 are out-of-scope for a "lane port" — they're the shared judge-service infrastructure. Verify at L0 day 0 with a curl test against the running judge service:

```bash
curl -fsS -H "Authorization: Bearer $EVOLUTION_INVOKE_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST $EVOLUTION_JUDGE_URL/invoke/score \
  -d '{"domain":"x_engine","fixture":{"fixture_id":"smoke"},"session_ref":"","artifacts":{}}'
```

If returns 200 with low aggregate (judge has no criteria → returns ~0): rows 7+8 work confirmed needed. If returns 4xx with "unknown domain": criteria store is also enforced server-side, may need separate judge-service-repo update. Run this 30-second test before committing to L1.

**Audit step at L0:** `grep -rn "range(1, 9)\|len(rubric_ids)" autoresearch/ src/` to enumerate any other consumers that hardcode 8-rubric-per-lane assumptions.

### 4.3 The WorkflowSpec — ~80 LOC, mostly mirroring geo

`archive/<seed-baseline>/workflows/x_engine.py` exports `SPEC = WorkflowSpec(...)`. **Follow `archive/v007/workflows/geo.py` shape end-to-end** — 8 hooks (`configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings`, `findings_promotion`), all required by `WorkflowSpec` dataclass at `archive/v007/workflows/specs.py:32-44`, most no-ops in v1.

**One x_engine-specific divergence:** `configure_env(_client)` re-applies `chmod 0444` to `programs/references/x_engine-voice.md` per session. The meta-agent boundary (`archive_index.py:280-356` chmod + sync ScopeViolation) only covers proposer mutations; at session-time the runtime agent has Write+Edit tools against the materialized variant tree. Per-session re-chmod closes the runtime boundary.

```python
def configure_env(_client: str) -> None:
    voice_path = Path(__file__).resolve().parent.parent / "programs" / "references" / "x_engine-voice.md"
    if voice_path.exists():
        os.chmod(voice_path, 0o444)
```

`list_deliverables` returns `drafts/*.md`. `count_findings` returns 0 in v1. `findings_promotion = FindingsPromotionConfig(title="X-Engine Patterns", confirmed_threshold=3, repeated_threshold=2)`. Other hooks: copy geo's no-op patterns.

**JR-side voice substrate update workflow:** `chmod +w` the file, edit, re-stamp at next variant generation. v1 treats the substrate as stamped-at-baseline-time.

### 4.4 The SessionEvalSpec — ~80 LOC, mostly mirroring geo

`archive/<seed-baseline>/workflows/session_eval_x_engine.py` exports `SPEC = SessionEvalSpec(...)`. **Follow `archive/v007/workflows/session_eval_geo.py` shape** — `domain`, `domain_name`, `criteria` dict, `structural_gate` callable, `load_source_data` callable, `cross_item_criteria` dict.

**Two x_engine-specific divergences from geo:**

1. **`load_source_data` reads voice substrate** so the judge can enforce X-2's hard-floor on lived-work claims. The voice file lives at `session_dir.parents[2] / "programs/references/x_engine-voice.md"` — outside `session_dir`, so not auto-included in the judge's artifacts payload (`evaluate_variant.py:1135` only walks session_dir). Concat into source_data alongside the angle JSON.

2. **`X-6` cross_item_criteria sized for prose drafts:** `CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)`. 400 (vs geo's 500) sized for CASE-STUDY drafts (1000-1500 chars ≈ 250-400 words) — at 200 the judge can't see the body's differentiator on long drafts.

`structural_gate` is per-artifact only (`evaluate_session.py:156-157` invokes with one artifact at a time). v1 checks: `[BODY]` block presence, `[META]` block presence, char_count within length_bracket range. Cohort-level checks (pillar diversity, etc.) move to `WorkflowSpec.completion_guard` or `snapshot_evaluations` if needed — not in v1.

**The 6 rubric anchors (`CRITERIA` dict, ships as judge prompt content via §2.5 two-template approach):**

| ID | Anchor (50-100 words each) |
|---|---|
| X-1 | JR's voice — first-person, opinionated, plain-language register accessible to a non-engineer founder/marketer. Jargon without inline plain-English context caps this dimension. AUTOMATIC ≤4 if 2+ unexplained technical terms; AUTOMATIC ≤6 if any jargon without plain-English follow-up. |
| X-2 | Factual specificity. SOURCE claims (numbers, names, quotes, features) must verify against source_text. INTERPRETIVE claims framed as JR's view ('my read', 'in our work') are OK. **HARD FLOOR: any first-person specific lived-work claim** ('when I built X for client Y') REQUIRES the named entity to appear in `programs/references/x_engine-voice.md` (loaded into source_data). Specific claims about unnamed clients/projects → score ≤3. |
| X-3 | Hook strength. SHARP brackets — first 8-12 words carry the punch. BUILD/CASE-STUDY — first 1-2 sentences earn line two (beat the show-more cutoff). Generic openers and rhetorical-question hooks score ≤4. |
| X-4 | Slop-freeness. Zero AI-tells. Banned phrases per `slop_gate.py` regex are a deterministic floor; this dimension judges what slips through. |
| X-5 | Structural richness. Bracket-aware: SHARP earns 10 with one sharp claim+support pair; BUILD earns 10 with prose intro + structural pivot + 3-5 substantive bullets + authority anchor + outcome metric; CASE-STUDY earns 10 with multi-paragraph narrative + sensory detail + numbers timeline + implication close. Pad-to-length = ≤4. |
| X-6 | Cross-item: across drafts in this cohort, no two use the same primary differentiator, source, or hook archetype. The variant should spread across `voice_pillars` listed in angle metadata. (geometric mean across `drafts/*.md`.) |

Score scale 0-10 (judge interpolates from 1/3/5 prose anchors per `scorer_x_engine.md` v5 two-template approach).

### 4.5 (DROPPED — no separate helper module)

v2's separate `_validate_x_engine.py` helper module is removed. `LaneSpec.structural_gate_functions` dotted strings are documentation metadata for `regen_program_docs.py`; placing real check functions there had no enforcement consumer.

v3 imagined moving SHA + fabrication checks inside `session_eval_x_engine.structural_gate()`. v4 dropped them as over-engineered; v5 keeps them dropped. Voice substrate runtime lock now lives in `WorkflowSpec.configure_env()` (§4.3 chmod 0444 hook). Fabrication enforcement lives in tightened X-2 + X-1 rubric anchors (see §4.4). Total `session_eval_x_engine.py` LOC: ~80, not v3's claimed ~110.

### 4.6 Variant backfill (D8)

Seed-baseline variant gets these new files:

```
archive/<seed-baseline>/
├── programs/
│   ├── x_engine-session.md            (NEW; ~100 lines — initial seed prompt; trimmed from v2's 180)
│   ├── x_engine-evaluation-scope.yaml (NEW; ~10 lines)
│   └── references/
│       └── x_engine-voice.md          (NEW; ~70 lines — copy from x_engine/voice/about-me.md
│                                       + voice/no-go-topics.md, version-stamped, treated read-only)
├── workflows/
│   ├── x_engine.py                    (NEW; ~80 LOC WorkflowSpec)
│   └── session_eval_x_engine.py       (NEW; ~80 LOC — SessionEvalSpec with criteria + structural_gate
│                                       (BODY/META/length only); voice substrate locked via configure_env
│                                       chmod (§4.3); fabrication enforcement via X-2 rubric anchor + voice
│                                       substrate in load_source_data)
└── scripts/
    └── evaluate_session.py            (1-line edit: choices=[...,"x_engine"])
```

(v2's `_validate_x_engine.py` is gone — its checks moved inside `session_eval_x_engine.structural_gate()`.)

Plus the registry edits in `workflows/__init__.py` (1 line) and `workflows/session_eval_registry.py` (1 line) within the seed-baseline.

`v001..v006` are NOT seeded. They will score 0.0 on x_engine (intended; pre-date the lane).

### 4.7 (DROPPED in v3) — `pool_policies.json` is suite-keyed, not domain-keyed

v2's proposed JSON edit (`{"x_engine": {"search_v1": ..., "holdout_v1": ...}}`) doesn't match the actual schema. The file at `cli/freddy/fixture/pool_policies.json` keys by suite name only (`"search-v1"`, `"holdout-v1"`, `"_default"`); the lookup at `cli/freddy/fixture/refresh.py:83-100` is `pool_on_miss(pool)` — pool is the suite, no domain dimension. Existing entries already cover x_engine's needs: `search-v1` → `live_fetch`, `holdout-v1` → `hard_fail`. **No edit needed.**

**Open question for L0:** what does `live_fetch` MEAN for x_engine? Existing lanes' live-fetch paths hit external APIs (twitterapi.io, freddy backend). For x_engine, "live fetch an angle by ID" requires reading from `state.db` — host-local, not behind an API. Either (a) `freddy fixture refresh` fails for unknown source descriptors and search-v1 fixtures must be pre-populated (tolerable), or (b) a custom source descriptor in `cli/freddy/fixture/sources.json` is needed. Verify behavior at L0 before L1: try `freddy fixture refresh --suite search-v1 --domain x_engine` against an empty cache, observe what happens. ~0.5 day if (b) is needed.

---

## §5 — Holdout Infrastructure (the prerequisite — L1)

### 5.1 The bar

≥25 marked drafts (`mark-posted` or `skip-draft`) in the past 30 days, all with structured reasons. v1 currently has zero. *[verified: launchctl list shows no x_engine LaunchAgent; sqlite3 state.db count(recent_posted) = 0]*

### 5.2 New CLI surface + new DB table (added to v1 `xeng` CLI before any L2 work)

```
xeng skip-draft <draft_id> --reason <enum>      # NEW — writes draft_decisions
xeng angle-show <id>                            # NEW — agent uses
xeng angle-list [--days N]                      # NEW — agent uses; ORDER BY picked_at DESC
xeng holdout-export [--output]                  # NEW — reads draft_decisions; emits domains.x_engine[]
```

(v2's `xeng feedback --score` is NOT in L1; deferred to v2 per Q1 lock.)

**Database schema work (NEW — bigger than v2 estimated):** v2 §5.3 read `for row in db.recent_posted(active=True)` and accessed `row.shipped`, `row.skip_reason`, `row.draft_seq`. Reality: `recent_posted` (`x_engine/pipeline/db.py:104-119`) is engagement-only — has `posted_id, text, posted_at, draft_id, angle_id, pillar, tweet_url, likes, retweets, replies, views, last_synced_at`. **Skipped drafts NEVER enter `recent_posted` under current schema.** Plan needs:

```sql
CREATE TABLE IF NOT EXISTS draft_decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id TEXT NOT NULL,
    angle_id INTEGER NOT NULL,
    outcome TEXT NOT NULL,             -- 'ship' | 'skip'
    skip_reason TEXT,                  -- enum value when outcome='skip', else NULL
    created_at TEXT NOT NULL,          -- ISO8601
    FOREIGN KEY (angle_id) REFERENCES angles(angle_id)
);
CREATE INDEX IF NOT EXISTS idx_draft_decisions_created ON draft_decisions(created_at);
-- v2 lever: feedback_score INTEGER + feedback_notes TEXT columns added via ALTER TABLE
-- when xeng feedback ships; not needed in L1 (Q1 is locked-binary).
```

`xeng mark-posted` writes here (in addition to existing `recent_posted` for engagement-sync); `xeng skip-draft` writes here only. `recent_posted` stays untouched — engagement-sync depends on it.

`--reason` enum: `voice_off | factual_unverifiable | off_pillar | duplicate | no_time | other`. `no_time` is operator-noise; holdout-export filters these rows.

### 5.3 Migration script

`xeng holdout-export` reads `draft_decisions`:

```python
for row in db.draft_decisions(active=True):
    if row.outcome == "skip" and row.skip_reason == "no_time":
        continue                     # operator-noise filter
    fixture = {
        "fixture_id": f"jr-{row.created_at[:10]}-{row.decision_id:03d}",
        "client": "jr",
        "context": str(row.angle_id),     # str(int); angles.angle_id is INTEGER autoincrement
        "version": "1.0",
        "max_iter": 1,
        "timeout": 600,
        "anchor": True,
        "env": {
            "JR_GROUND_TRUTH": row.outcome,
            "SKIP_REASON": row.skip_reason or "",
        },
    }
    yield fixture
```

Output destination is OUT-OF-REPO at `~/.config/gofreddy/holdouts/holdout-v1.json` `domains.x_engine[]` (chmod 600). Operator atomically merges via §7.9.3 procedure.

### 5.4 Dogfood window (14 days) with day-7 checkpoint

JR runs v1 daily, marks every draft. Reasons map to rubric dimensions (`voice_off` → X-1, `factual_unverifiable` → X-2, `off_pillar` → X-6, `duplicate` → not a quality signal, `no_time` → filtered).

**Day-7 intermediate checkpoint:**

```bash
# Pillar diversity — must have ≥4 distinct pillars across the trailing 7 days of marks
sqlite3 x_engine/state.db "SELECT COUNT(DISTINCT a.voice_pillar) FROM draft_decisions d JOIN angles a ON d.angle_id=a.angle_id WHERE d.created_at > date('now','-7 days')"

# Skip-reason distribution — `other` rate < 30%, no single reason > 50% (catches review fatigue)
sqlite3 x_engine/state.db "SELECT skip_reason, COUNT(*) FROM draft_decisions WHERE created_at > date('now','-7 days') AND outcome='skip' GROUP BY skip_reason"
```

Restated in marks-units: need ≥12 marks across ≥4 pillars in the trailing 7 days. If JR is missing days OR fatigue-marking everything as "other," this surfaces.

**Day-14 verify step:**
- `xeng holdout-export --output /tmp/check.json && jq 'length' /tmp/check.json` ≥ 25
- All `outcome='skip'` rows have non-null `skip_reason`

If < 25 at day 14: pause and diagnose with JR. (No auto-extend.)

### 5.5 Why holdout BEFORE lane scaffold

If L2 (lane scaffold) lands before L1 (holdout signal), the first evolution cycle has no signal — frontier picks parents at random; promotion verdicts trip `first_variant_holdout_zero_score` on every run. Compute and judge tokens spent on noise. Hard ordering: holdout first.

---

## §6 — Evolution Loop Wiring

Lane uses autoresearch defaults end-to-end: `scorer_x_engine.md` for per-fixture scoring (0–10), `decide/promotion` for cohort verdict (via `_holdout_eligibility` at `evaluate_variant.py:2719-2743`), `candidates_per_iteration=3`, default 4-cycle auto-rollback. No `custom_*` callables on the LaneSpec.

**Mutation surface** (all in `programs/x_engine-session.md`): length-bracket char ranges + when-to-use; quality-criteria phrasing (NOT IDs); hard-rules ordering; tool-list emphasis.

**Locks:** voice substrate + WorkflowSpec + SessionEvalSpec all in `readonly_subprefixes` (chmod + sync ScopeViolation at meta-agent boundary; per-session re-chmod at runtime boundary). `voice/about-me.md`, `voice/no-go-topics.md`, `slop_gate.py`, `pull.py`, `db.py`, `sources.yaml` are not in `path_prefixes` — meta-agent workspace excludes them.

---

## §7 — Build Sequence, First-Runnable, Risks

### 7.1 Layer overview

| Layer | Delivers | Depends on | Calendar shape |
|---|---|---|---|
| **L0** | Pre-prerequisite verification + judges/ infra: judge-service criteria-injection plumbing (two-template scorer + variant_scorer.py dispatch + rubrics.py prose blocks) + freddy fixture path verification + Q1/Q2 lock with JR | nothing | 1–2 days code + JR sync |
| L1 | Holdout signal + v1 cron revived (≥25 marked drafts) | L0 complete | 1.5 days code + 14 days dogfood |
| L2 | Seed cull + lane scaffold + fixtures + first iteration | L1 complete | 8–10 days |
| L3 | Parallel-run window + day-7 verdict (folded into L2 in v3 — but parallel-run is a calendar event, not a layer) | L2 complete | 0.5 day code + 7 days parallel-run |

**v3 NEW: L0 is the pre-prerequisite layer.** v2 buried judge-service criteria handling as an "L2 verification step" — adversarial review F4 + scope review showed this is on the critical path. If the judge-service infra work blocks for days, the lane scoring is broken from day-1 first-iteration. v3 promotes it to L0.

### 7.2 L0 — Pre-prerequisite

JR confirms Q1/Q2 leans before L0 starts (Q2 may need more discussion than 30 min — D8 cross-lane contamination evidence may flip the lean). Then:

| Work item | Source | Estimate |
|---|---|---|
| **L0 day 0 smoke (BEFORE any judge-service edits):** `curl POST $EVOLUTION_JUDGE_URL/invoke/score` with `{"domain":"x_engine",...}`. Expected: 200 with hallucinated low aggregate (no criteria → judge guesses from domain name). If 4xx "unknown domain": criteria store is server-side enforced — escalate to JR for judge-service repo update before proceeding. | §2.5 + §4.2 row 7 | 0.1 day |
| **Author NEW `judges/evolution/prompts/scorer_x_engine.md`** with `{criteria}` placeholder + per-criterion + aggregate JSON output schema. Mirror `scorer.md` shape but for 6-criteria + criteria-injection (per §2.5 two-template approach). **DO NOT modify existing scorer.md.** | §2.5 + §4.2 row 7 | 0.1 day |
| **Modify `judges/evolution/agents/variant_scorer.py:22-71` to branch on `payload["domain"]`:** for `x_engine` load `scorer_x_engine.md` and format with `criteria=_render_criteria_for_domain("x_engine")`; for other domains load existing `scorer.md` unchanged. Add `_render_criteria_for_domain(domain)` helper (~15 LOC) filtering `RUBRICS` by `domain="x_engine"` + curly-brace escape on prose. While there, grep `range(1, 9)\|len(rubric_ids)` to surface any other length-8 assumptions. | §2.5 + §4.2 row 8 | 0.4 day |
| Verify `freddy fixture refresh --suite search-v1 --domain x_engine` against an empty cache. If hard-fails on unknown source descriptor: add x_engine entry to `cli/freddy/fixture/sources.json` (~0.5 day). | §4.7 | 0.25–0.75 day |
| Regression: run `python3 -m autoresearch.evolve run --lane geo --iterations 1 --candidates 1` after the variant_scorer.py dispatch change; confirm geo aggregate score is within ±0.5 of historical. The two-template approach keeps geo's prompt unchanged (loads existing `scorer.md`); regression should be a no-op. If aggregate moves, the dispatch is wrong — debug before proceeding. | regression check | 0.25 day |

L0 ships when: judge service smoke responds, scorer accepts criteria for x_engine + empty for other domains, fixture refresh path is settled, and the geo regression run produces unchanged scores.

### 7.3 L1 — Holdout signal (the prerequisite)

| Work item | Source | Estimate |
|---|---|---|
| **L1 day 0: revive v1 cron** — `cd x_engine && ./install_schedule.sh && launchctl list com.jryszardnoszczyk.x-engine` (script already calls launchctl load; one command, not two). Verify a draft lands the next morning at 06:31 in `x_engine/logs/run.log`. | D10 | 0.1 day |
| Add `xeng skip-draft <draft_id> --reason <enum>` (structured enum) | §5.2 | 0.5 day |
| Add `xeng angle-show <id>` + `xeng angle-list [--days N]` (ORDER BY picked_at DESC) | §3.4 | 0.5 day |
| Add `xeng holdout-export [--output]` with operator-noise filter | §5.3 | 0.5 day |
| **Update `db.py` schema** — add `draft_decisions` table per §5.2 (CREATE TABLE + index + helper accessors). Modify `xeng mark-posted` to also write here. | §5.2 + feasibility M1 | 0.5 day |
| **Dogfood window** — JR runs v1 daily, marks ≥25 drafts | §5.4 | **14 days operator-side** |
| **Day-7 intermediate checkpoint** — pillar diversity ≥ 4 distinct, no single skip-reason > 50%, `other` rate < 30% | §5.4 | 0.1 day |
| Day-14 verify: `xeng holdout-export` produces ≥25 anchored fixtures with structured reasons; distribution healthy | §5.4 | 0.25 day |

L1 ships only when the day-14 verify step passes. Coding work is ~2 days; dogfood is the long pole.

### 7.4 L2 — Seed cull + lane scaffold + fixtures + first iteration + parallel-run

| Work item | Source | Estimate |
|---|---|---|
| Drop `agentic.py`, `agentic_master.md`, `bootstrap_from_cache.py`, `slop_check.md`, `run.sh`, `pipeline/topic_pick.py`, `pipeline/draft.py`, `pipeline/compose.py` | §3.1 DROP rows | 0.25 day |
| Collapse `cli.py` to 12 subcommands per §3.1; drop ~270 LOC | §3.1 | 0.5 day |
| Strip `db.py`, `llm.py`, tests per cull table | §3.1 | 0.5 day |
| **Author 6 prose blocks `_X_1`..`_X_6` in `src/evaluation/rubrics.py`** (1/3/5 anchor format, mirroring `_GEO_1`..`_GEO_8`); add to `RUBRICS` dict; bump `assert len(RUBRICS) == 32` → `38`; mark X-6 with `is_cross_item=True` | §4.2 row 3 | **1 day** |
| Author `archive/<seed-baseline>/programs/x_engine-session.md` (~100 lines per §3.3 — trimmed from v2's 180) | §3.3 | 0.75 day |
| Author `archive/<seed-baseline>/programs/references/x_engine-voice.md` (~70 lines, version-stamped, copied from voice/about-me.md + voice/no-go-topics.md) | §3.1 KEEP-MANUAL | 0.25 day |
| Author `archive/<seed-baseline>/programs/x_engine-evaluation-scope.yaml` (~10 lines) | §4.6 | 0.1 day |
| Author `archive/<seed-baseline>/workflows/x_engine.py` (~80 LOC WorkflowSpec) | §4.3 | 1 day |
| Author `archive/<seed-baseline>/workflows/session_eval_x_engine.py` (~80 LOC — SessionEvalSpec criteria + structural_gate with BODY/META/length checks only) | §4.4 | 1 day |
| Drift-gate: rows 1-6 + 9 of §4.2 (rows 7-8 already shipped at L0) | §4.2 | 0.5 day |
| Add `domains.x_engine: [...]` to `eval_suites/search-v1.json` (5–10 fixtures from state.db angles) | §2.4 | 0.5 day |
| Atomic-merge holdout fixtures into `~/.config/gofreddy/holdouts/holdout-v1.json` per §7.9.3 | §5.3 | 0.25 day |
| First iteration: `python3 -m autoresearch.evolve run --lane x_engine --iterations 1 --candidates 3` | §7.5 | 0.5 day (mostly waiting) |
| First-runnable verification per §7.5 | §7.5 | 0.5 day |
| Wire daily evolution cron — choose LaunchAgent (matches v1 pattern) | (collapsed from L3) | 0.5 day |
| Run v1 + lane in parallel for 7 days; JR reviews both daily | §3.5 + D6 | 7 days operator-side |
| Day-7 verdict: lane wins on JR-preference in ≥3 of 7 days → switch primary daily output (per D6) | §3.5 + D6 | 0.25 day |

**Total L2 coding work: ~8.5 days** (sum of work items above with v5's SessionEvalSpec at 1 day). Plus 7 days of operator-side parallel-run waiting.

### 7.5 First-runnable acceptance criteria

The lane is first-runnable when ALL pass:

| Criterion | How to verify |
|---|---|
| LaneSpec is registered + drift gate passes + rubrics.py assertions hold | `python3 -c "from autoresearch.lane_registry import _assert_models_literal_matches; _assert_models_literal_matches(); import src.evaluation.rubrics"` exits 0 (the rubrics import triggers all 3 assertions) |
| `evaluate_session.py` argparse accepts `--domain x_engine` | `python3 archive/<seed>/scripts/evaluate_session.py --domain x_engine --help` exits 0 |
| Search-v1 has fixtures | `jq '.domains.x_engine \| length' eval_suites/search-v1.json` ≥ 5 |
| Holdout has anchored fixtures | `jq '.domains.x_engine \| map(select(.anchor==true)) \| length' ~/.config/gofreddy/holdouts/holdout-v1.json` ≥ 25 |
| Variant subprocess launches | `python3 archive/<seed>/run.py --domain x_engine jr <int_angle_id> 1 600` runs to completion |
| At least one draft.md is produced + conforms to §2.2 shape | `ls archive/<seed>/sessions/x_engine/jr/drafts/*.md` non-empty AND `session_eval_x_engine.structural_gate(...)` returns `[]` on it |
| In-session evaluator runs | `python3 archive/<seed>/scripts/evaluate_session.py --domain x_engine --artifact <draft.md> --session-dir <session>` exits 0 with non-empty per-criterion feedback |
| Judge service responds with criteria-aware scoring | `evaluate_variant.py` post to `/invoke/score` returns 200 with `aggregate_score` 0–10 AND per-criterion entries reference X-1..X-6 (NOT hallucinated criteria names) |
| End-to-end | `python3 -m autoresearch.evolve run --lane x_engine --iterations 1 --candidates 3` exits 0 with 3 scored variants |

Quality bar at first-runnable is "the plumbing works" — NOT "drafts are great". Day-1 seed quality may be worse than v1; that's by design.

### 7.6 Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Dogfood window produces <25 marks in 14 days | Medium | High (L1 blocks) | L1 day-0 v1 cron revival explicit (D10); day-7 intermediate checkpoint catches bias before lockin (§5.4); operator-noise `no_time` filter prevents review fatigue from polluting holdout |
| R2 | Day-1 lane quality so much worse than v1 that JR stops marking lane outputs → review-fatigue starvation | Medium | High | Holdout fixtures use angle-IDs (§2.3), so ground truth is on angles already marked. Lane day-1 quality doesn't block holdout signal accumulation. Day-7 verdict (D6 with margin requirement) catches review fatigue if it appears |
| R3 | Judge-service criteria infrastructure has unexpected dependency on server-side state (e.g., domain whitelist) | **Low (after L0)** | Critical | Mostly pre-mitigated: L0 day-0 30-second curl smoke test surfaces this before any code is written. Two-template approach (v5) keeps existing 4 lanes' prompts unchanged. ~0.5 day code work in L0 if smoke succeeds; ~1-3 days if smoke surfaces server-side enforcement requiring out-of-band judge-service repo work |
| R4 | Cross-lane contamination if Q2 lands as Option B — older variants without x_engine WORKFLOW_SPEC raise `KeyError` on dispatch | Medium | High | L0 verification step under D8 confirms dispatch path. If `KeyError` surfaces: either (a) make seed-baseline THE current lane head (Q2=A pivot), or (b) add a try/except at dispatch site that silently 0.0s missing-lane variants. Decision at L0 with JR |
**Minor risks:** compute budget (per-iteration ~2.5–5 hr; daily total across 5 lanes ~12–20 hr — wires cron with autoresearch's existing serialization); sources curation drift (`sources.yaml` frozen v1+v2; JR hot-edit channel); narrow evolution surface (single prompt file — tradeoff: focused early progress, capped upside).

### 7.7 What's NOT in v1 of the lane

| Item | Where deferred | Trigger to revisit |
|---|---|---|
| Per-pillar lanes | v3 | Pillar-specific evolution shows divergent winners across 5+ generations |
| Auto-posting to X | v3+ | Manual posting validated; automation policy clear |
| `sources.yaml` mutation | v2+ | Pillar starvation across 3 generations |
| Specialized x_engine judge agent | v2 | Existing scorer judge under-enforces ≥1 rubric across 5 cycles |
| 1–5 nuanced holdout score | v2 | Binary signal saturates |
| Length-bracket simplification (drop CASE-STUDY) | v2 maybe | CASE-STUDY ships <5% across 50 generations |
| Net-new exemplars added to references | v2 | Signal exists for "this exemplar drove X-N lift" |
| Python script mutation surfaces (widen surface) | v2 | Single-prompt evolution saturates |

### 7.8 Timeline shape

Lower-bound: L0 ~1.5 days code + L1 ~2 days code + 14 days dogfood + L2 ~8.5 days code + 7 days parallel-run = **33 days**.

Realistic: **5–6 weeks** (account for ~1 day slip in L0 if judge-service smoke surfaces server-side dependency, ~1 day slip in L2 from cross-lane dispatch surprises, one parallel-run day-7 gate that doesn't pass and triggers extend).

L1 dogfood remains the long pole. L0 runs first because the judge-service infra change is shared and a bad fix would affect all 5 lanes; v5's two-template approach contains blast radius (existing 4 lanes' prompts unchanged).

### 7.9 JR's decision points

| Gate | When | What JR decides |
|---|---|---|
| **Q1, Q2** | L0 kickoff | Lock leans or override (§1.5). Q2 has cross-lane contamination implications (R4) |
| **L0 judge-service smoke verdict** | L0 day 0 | If 4xx "unknown domain": pick path (judge-service-side state vs criteria-in-payload) |
| **Day-7 parallel-run verdict** | L2 day-15 | Lane wins on JR-preference in ≥3 of 7 days → switch; trajectory positive but not 3-of-7 → extend 7 days; flat/negative → pause (per D6) |

**Holdout merge at L2:** `xeng holdout-export` → snapshot existing manifest → `jq --argfile` to merge into `domains.x_engine` → atomic mv → verify all 5 lanes still keyed + x_engine ≥25 + other lanes unchanged. 5-bash-command operator procedure; details in operator memory.

**Kill rules** (operator memory): `launchctl unload` for cron halt; `evolve_ops rollback --lane x_engine` for variant rollback; comment-out `LANES` entry + revert `models.py` Literal for full lane disable.

---

**End of master plan v7.**
