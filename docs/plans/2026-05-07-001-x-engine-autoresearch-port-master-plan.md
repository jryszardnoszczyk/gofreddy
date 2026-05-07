# X + LinkedIn → Autoresearch Port — Master Plan

**Status:** v13 active 2026-05-07. Dual-platform lane port (X + LinkedIn). LinkedIn lane is sibling to x_engine; shares `pull.py` + `slop_gate.py` + voice substrate + scorer template + the v1 `angles` table; diverges at writer prompt + per-platform rubric + holdout + LinkedIn evidence cache + LinkedIn top-N command. Apify scrapers + Bright Data fallback per D11. **v13 = aggressive trim** on v11/v12: rubric anchor prose moved to companion file `2026-05-07-001-x-engine-rubric-anchors.md`; build-sequence work-items collapsed to layer summaries (overlap with §4.2 drift gate); D-decisions compressed to terse table; §3 verbose blocks pruned. Plan stays implementer-ready (concrete WorkflowConfig values + callable signatures + drift gate); rubric anchors stay JR-reviewable in companion file. Anchored to "how was the 5th/6th lane added?" precedent — terse spec + reference to existing patterns, NOT marketing-audit-master-plan-style multi-stage doc.

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

**Operator procedures + JR's decision gates** are in §7.9 (no separate companion file).

---

## §1 — Goals, Non-Goals, North Star

### 1.1 Thesis

x_engine v1 ships and works for X (5 ship-eligible drafts/run, 80–130s wall time, $0/run via codex). It cannot keep getting better without me/JR hand-tuning prompts; there is no held-out evaluation; no automatic regression detection. LinkedIn has no v1 baseline at all — JR currently posts manually if at all.

Autoresearch already runs the kind of loop both platforms need: subprocess-isolated agent reads an evolvable program prompt, uses CLI tools to produce deliverables, deliverables get scored by a judge service against per-domain criteria, holdout gates promotion. The loop is empirically validated end-to-end as of 2026-05-06 (v007 promoted on geo with proper holdout refusal on a regression). *[source: project-autoresearch-evolution-fixes-pending.md]*

The port is **not** a 1-to-1 migration of x_engine v1. v1 is roughly 8× the seed it needs to be. *[source: x_engine seed audit 2026-05-07]* The port keeps what evolution can't improve (data plumbing, deterministic policy gates, JR's identity), drops what evolution should improve (the agent's writing approach), and discards what existed only because v1 had no autoresearch lane to lean on (agentic mode, dual compose, 4-prompt split, 6-voice-file tower).

**Why dual-lane from the start:** product-driven (cross-platform consistency: ship similar takes on both platforms) per JR direction. Sibling lanes share `pull.py` + voice substrate (`programs/references/voice.md`) + `slop_gate.py` + the v1 `angles` table; they diverge at the writer prompt + per-platform rubric + per-platform top-N command + LinkedIn-specific evidence cache. **`pick-angles` shared upstream was DROPPED in v9** (Round-6 scope-guardian + adversarial review): each lane pulls angles directly from the v1 `angles` table populated by v1's existing per-pillar logic; per-platform engagement normalization happens at the per-platform top-N command, not in shared `rank.py`. Adding LinkedIn = ~5-7d code on top of x_engine; the +5d "shared upstream is genuinely shared" justification was speculative.

### 1.2 Goals (in priority order)

1. Add **two** sibling workflow lanes (`x_engine`, `linkedin_engine`) to the autoresearch registry, both producing ship-eligible draft posts on a per-fixture basis, scored on per-platform 6-dimension rubrics (X-1..X-6 and LI-1..LI-6, 0–10 per criterion).
2. Each lane has its own evolvable agent prompt (`programs/<lane>-session.md`, ~100 lines each) and SessionEvalSpec rubric. Both lanes pull angles from the v1 `angles` table populated by `pull.py` + `rank.py`; per-platform top-N is exposed via separate `xeng top-tweets` (X) and `xeng top-linkedin` (LinkedIn) commands. Same input table, two platform-specific top-N reads.
3. **Build the X-lane holdout signal first via 14-day dogfood.** LinkedIn lane bootstraps differently — JR has no v1 LinkedIn outputs to dogfood, so the LinkedIn holdout grows organically as the lane produces drafts in L2 and JR marks them. The two lanes' holdout signals are independent.
4. Day-1 seed quality may be worse than v1 (X) or worse-than-hand-written (LinkedIn). That is acceptable. Evolution earns the quality back. v1 X cron stays running daily, in parallel, until x_engine lane wins on holdout. LinkedIn has no v1 baseline; the lane is the first automated LinkedIn output.
5. Survive contact with the existing autoresearch contract — `WorkflowSpec` + `SessionEvalSpec` + 9 drift-gate surfaces enumerated in §4.2 that fail loud against each other.

### 1.3 Non-goals

- Auto-posting to X or LinkedIn. Manual posting stays for both platforms.
- Mutating `voice/about-me.md`, `voice/no-go-topics.md`, `pull.py`, `slop_gate.py`, or `sources.yaml` in v1 of either lane.
- Per-pillar sub-lanes (one lane per platform; not split by content pillar).
- Other text-based platforms (Threads, Bluesky, Substack Notes) — deferred to v2+; X + LinkedIn are the load-bearing two for B2B/agency marketing.
- Preserving v1's agentic (codex-spawn-codex) mode. It is dropped.
- Net-new judge agents. v1 of the lanes uses the existing variant-scorer judge with two new prompt templates (per §2.5). New judge agents are a v2 lever.
- Inline `call_llm()` in the lane runtime. Autoresearch does not call LLMs from `workflows/<lane>.py` — the agent (claude/codex/opencode subprocess) does all LLM work, driven by `programs/<lane>-session.md`.
- Custom LinkedIn scraping infrastructure. Apify actors handle this (`apimaestro/linkedin-posts-search-scraper-no-cookies` for keyword search; `harvestapi/linkedin-profile-posts` for per-creator pulls).

### 1.4 North star

A daily run that produces 1–3 ship-eligible X drafts AND 1–2 LinkedIn drafts (LinkedIn cadence is naturally lower, ~2-3 ships/week is normal vs X ~5/day), all from the latest evolved variant of each lane. JR ships some, marks the rest; ship/skip decisions per platform feed back into the per-platform holdout; quality is provably non-decreasing across promotions per lane.

Quantitative success bar: **for 4 consecutive promotion cycles per lane, the new variant must improve OR hold the holdout aggregate score over the prior baseline.** A regression triggers auto-rollback (existing autoresearch primitive). Score scale is the judge's 0–10. Each lane has its own promotion track — they don't gate each other.

### 1.5 Locked decisions (D1–D13) and open questions (Q2)

| # | Decision | Rationale (only when non-obvious) |
|---|----------|------------------------------------|
| D1 | `is_workflow_lane=True` for both lanes | Per-domain scoring reads `scores["x_engine"]` and `scores["linkedin_engine"]` independently |
| D2 | Lane names: `x_engine`, `linkedin_engine` | — |
| D3 | rubric_ids inline 6-tuples (`"X-1".."X-6"`, `"LI-1".."LI-6"`) | `_rubric_ids("X")` helper is hardcoded `range(1,9)` = 8 IDs; would over-shoot |
| D4 | ONE shared voice substrate at `programs/references/voice.md`; lock in both lanes' readonly_subprefixes | Per-platform register guidance lives in each lane's evolvable session.md where it can evolve. JR-identity + lived-work entities are platform-agnostic |
| D5 | Both lane runtimes agent-driven via `python3 <variant>/run.py --domain <lane>` | Same dispatcher all 4 existing lanes use; no Python imports inside variant subprocess |
| D6 | x_engine parallel-run 7 days; verdict = (a) JR-preference ≥3-of-7 AND (b) holdout-aggregate non-regressive | Single-rater unblinded preference alone is too noisy. LinkedIn has no parallel-run (no v1 baseline) |
| D7 | Drop writer-critic revise loop in both seeds | Evolution replaces revision |
| D8 | Backfill new lanes only into seed-baseline variant | Older variants pre-date lanes; per-lane frontiers start at seed-baseline. Q2 verifies dispatch behavior |
| D9 | L1 day-0 = revive v1 X cron (`launchctl load` the existing .plist) | 14-day dogfood clock can't start until X drafts produce daily |
| D10 | Both lanes ship simultaneously in v1 | Cross-platform consistency motivation per JR direction; cost +5d L2 |
| D11 | Apify primary (apimaestro keyword + harvestapi per-creator); Bright Data pre-positioned in L1 (~2d feature-flagged off) | Realistic cost $50-250/mo. Joint Apify failure (correlated by anti-scrape sweep) → 30-min env-var flip not 5-6d emergency |
| D12 | LinkedIn ROI threshold: ≥3 ship-eligible/week + judge ≥6.5 by L2 week-8; pause by week-12 if not met | Falsification criterion for the dual-lane bet itself |
| D13 | LinkedIn lane consumes X-derived angles in v1; agent uses `xeng top-linkedin` for surface examples | Matches cross-platform-consistency motivation. v1.5 lever for LinkedIn-side angle-write if pillar starvation surfaces |

**Resolved:** Q1 = binary holdout (ship/skip + structured `skip_reason`); Q3 = one shared voice substrate (subsumed into D4).

**Open (L0 day-0 verification):** Q2 = seed-baseline variant — extend `archive/v007/` (Option A) vs branch fresh `archive/v007-curated/` (Option B). Lean: B. Flip to A if L2-day-0 dispatch verification (non-seed variant routed to either lane) raises `KeyError`.

---

## §2 — Deliverable Shape

### 2.1 Per-fixture session output

Each lane runs its agent inside `<variant_dir>/sessions/<lane>/<client>/` — `sessions/x_engine/jr/` and `sessions/linkedin_engine/jr/`. Both layouts mirror geo's pattern *[shape source: archive/v007/programs/geo-session.md "Workspace" section]*:

```
sessions/<lane>/<client>/
├── session.md                # agent's state file, rewritten each iteration
├── results.jsonl             # phase event log (gather/draft/critique/log)
├── angles/<angle_id>.json    # angle data cached at session start (shared schema across lanes)
├── drafts/<draft_id>.md      # the deliverable — one markdown file per draft
├── drafts/<draft_id>.eval.json   # in-session evaluator output (structural + judge critique)
├── findings.md               # cross-draft observations
└── report.md                 # final per-session summary
```

**Why `<client>` is `jr`** — for both lanes the only client is JR himself. The fixture's `client` field is `"jr"` for every fixture in either lane.

**Critical: the `angles/<angle_id>.json` cache shape is identical across lanes.** Both lanes consume angles from `xeng angle-show` (which queries the v1 `angles` table in state.db, populated by v1's existing per-pillar angle-write logic — see §3.6). One angle, two formats.

### 2.2 Draft markdown shape (per-platform)

Both lanes' `drafts/<draft_id>.md` files share frontmatter + `[BODY]/[META]` block structure so deterministic `structural_gate` checks work without LLM calls. Per-platform divergences are noted below.

**X (`x_engine`):**

```markdown
---
draft_id: jr-2026-05-07-001
angle_id: 42
platform: x
length_bracket: build           # sharp | build | case_study
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

**LinkedIn (`linkedin_engine`):**

```markdown
---
draft_id: jr-2026-05-07-001
angle_id: 42
platform: linkedin
length_bracket: thought_leader   # short_take | thought_leader | case_study
char_count: 1840
voice_pillar: harness-engineering
---

[BODY]
<post body — 500-3000 chars; longer than X; line-break-rich>
[/BODY]

[META]
hook: <first 1-2 sentences; LinkedIn rewards story-opening over contrarian-take>
authority_anchor: "<JR's lived-work claim, exact phrase>"
specific_number: "<at least one number/$/% in body>"
attribution: "<named tool / company / public datapoint / repo URL>"
hashtags: "<comma-separated targeted hashtags; spam guardrail = ≤5; LI-5 rubric scores 3-5 ideal vs 1-2 suboptimal vs 0 ≤4>"
[/META]
```

**Per-lane structural_gate divergences:**
- x_engine: `length_bracket ∈ {sharp, build, case_study}` with ranges 250-300 / 500-900 / 1000-1500
- linkedin_engine: `length_bracket ∈ {short_take, thought_leader, case_study}` with ranges 500-900 / 1500-2500 / 2500-3000
- linkedin_engine `[META]` requires `hashtags` field (comma-separated; spam guardrail ≤5 enforced by structural_gate; LI-5 rubric scores quality on 3-5 ideal); x_engine has no hashtags field (X penalises hashtag use)
- Both: `[BODY]` non-empty, all `[META]` keys present and non-empty (except where lane-specific), `xeng slop-check` (platform-aware variant) passes

The structural_gate verifies: file exists, char_count within bracket range, `[BODY]` block non-empty, `[META]` block has all required keys for the platform, slop_gate regex passes against body text (delegated to platform-aware `xeng slop-check --platform <x|linkedin>`).

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

`env.SKIP_REASON` is a structured enum (lookahead — see §5.3): one of `voice_off | factual_unverifiable | off_pillar | duplicate | no_time | other`. Empty when shipped. Holdout-export filters out `no_time` rows (operator-noise; not a quality signal).

### 2.4 Search-suite vs holdout-suite split (both lanes)

| Suite | File | Lane domain entries | Purpose | Cache policy |
|---|---|---|---|---|
| Search | `autoresearch/eval_suites/search-v1.json` | `domains.x_engine[]` (5–10 fixtures) AND `domains.linkedin_engine[]` (5–10 fixtures); both can include unmarked angles | Per-lane cohort scoring during evolution | `live_fetch` |
| Holdout | `~/.config/gofreddy/holdouts/holdout-v1.json` | `domains.x_engine[]` (20–30 marked) AND `domains.linkedin_engine[]` (≥0, grows organically — see §5.4) | Per-lane promotion-gate verdict | `hard_fail` |

Lanes share fixture context shape (angle_id) but maintain independent cohorts/holdouts. A single angle can appear in both `domains.x_engine[]` and `domains.linkedin_engine[]` — same input, two platform-specific draft outputs.

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

**Score scale is 0–10 in the judge output** (scorer.md:24). The rubric prose blocks in `src/evaluation/rubrics.py` use 1/3/5 anchor format; the judge interpolates 0–10 from the 1/3/5 anchors. `aggregate_score` is the per-fixture domain score; `_objective_score_from_scores` reads this from `scores["x_engine"]` for x_engine and `scores["linkedin_engine"]` for linkedin_engine. Each lane's promotion gate uses its own top-level score key independently.

**CRITICAL — judge prompt has NO `{criteria}` placeholder.** `scorer.md` line 3 hardcodes "score one variant's session artifacts against the 8-criteria rubric for the specified domain"; the existing scorer-load logic only formats `{domain, fixture, session_ref, artifacts}`. The judge LLM is told "score the rubric" without being told what the criteria are — it relies on its prior knowledge of `{domain}` (works for `geo`/`competitive`/`monitoring`/`storyboard` because those have public-domain priors). For `x_engine` (a JR-private lane), the LLM has no prior. First iteration would produce hallucinated noise.

**Two-template approach for criteria injection (L0 prerequisite, see §7.2):**

Existing 4 lanes preserve their baseline; x_engine and linkedin_engine both consume a single new parameterized template (Round-6 #11 trim — was three-template in v8.2; near-identical duplication consolidated to one parameterized template).

1. **Keep `judges/evolution/prompts/scorer.md` UNCHANGED** for the existing 4 lanes (line 3 still says "the 8-criteria rubric for the specified domain" — preserves their LLM-prior baseline). A single-template rewrite would silently degrade the existing lanes.
2. Author **ONE NEW** prompt `judges/evolution/prompts/scorer_templated.md` with `{criteria}` placeholder. Shape:
   ```
   You are a domain-quality scoring judge for the gofreddy evolution loop.
   Score one variant's session artifacts against the rubric below.

   <criteria>
   {criteria}
   </criteria>

   <domain>{domain}</domain>
   <fixture>{fixture}</fixture>
   <session_ref>{session_ref}</session_ref>
   <artifacts>{artifacts}</artifacts>

   Respond with a fenced JSON block (per_criterion 0-10, aggregate_score 0-10, structural_passed, grounding_passed)
   ```
3. Modify `judges/evolution/agents/variant_scorer.py` `score_variant()` (lines 58-98 — the function that currently does `prompt = _load_prompt().format(...)`): replace the single `_load_prompt().format()` call with a 2-way template choice based on `payload["domain"]`. For `x_engine` or `linkedin_engine` → load `scorer_templated.md` and `.format(criteria=_render_criteria_for_domain(domain), domain=..., fixture=..., session_ref=..., artifacts=...)`. For other domains → preserve existing path: load `scorer.md` and `.format(domain=..., fixture=..., session_ref=..., artifacts=...)`. **Note:** this is a structural refactor of `score_variant()`, not a surgical edit at `:22-71` (those lines are constants + `_load_prompt` helper). Net: ~10 LOC dispatch + ~10 LOC helper.
4. `_render_criteria_for_domain(domain)` filters `RUBRICS` by `domain=domain` and concatenates the 1/3/5 prose blocks. **Curly-brace escape:** prose contains `{` and `}` literals; pre-escape via `text.replace("{","{{").replace("}","}}")` before `.format()`.
5. The criteria source is `src/evaluation/rubrics.py:RUBRICS` — the same file that gets 6 new `_X_N` blocks AND 6 new `_LI_N` blocks at §4.2 row 3 (12 total new prose blocks).

Net: ~30 LOC of net-new infra (1 prompt template + 2-way dispatch + helper). Out-of-scope for a "lane port" but unavoidable for x_engine and linkedin_engine. ~0.5 day. Lands at L0 before L1 dogfood begins. Two-template approach avoids regressing the existing 4 lanes' tuned baseline AND avoids near-identical file duplication that would compound at every future lane port.

---

## §3 — Seed Architecture

### 3.1 Cull (file-by-file decision; same for both lanes' shared infra)

- **KEEP verbatim (shared by both lanes via `xeng` CLI):** `pull.py` (457), `slop_gate.py` (134; extended to be platform-aware via `--platform x|linkedin` flag), `rank.py` (116; X-engagement scoring stays as-is — per-platform normalization moves into the per-platform top-N command, not shared `rank.py`), `sources.yaml` (frozen for X; LinkedIn equivalent in `sources_linkedin.yaml` — see §3.4), `schemas/*.json`, `install_schedule.sh` + `.plist` (X-only; D6 parallel-run for x_engine).
- **COLLAPSE:** `db.py` → ~80 LOC + new `draft_decisions` table per §5.2 + new `linkedin_posts` table + ALTER on existing v1 `angles` to add `source_text` column; `cli.py` → ~17 subcommands (X commands as before; new shared `skip-draft`, `holdout-export`; new LinkedIn-specific `pull-linkedin-search`, `pull-linkedin-user`, `top-linkedin`).
- **DROP entirely:** `agentic.py` + `agentic_master.md`, `prompts/{topic_picker,writer,critic,slop_check}.md`, `pipeline/{topic_pick,draft,compose}.py`, `bootstrap_from_cache.py`, `run.sh`.
- **KEEP manual (JR-authored, never evolves; shared by both lanes):** `voice/about-me.md`, `voice/no-go-topics.md`, `voice/exemplars.md`. Excerpts copied into ONE shared reference file at L2 time (Round-6 #18 trim — was two lane-specific files in v8.2):
  - `archive/<seed>/programs/references/voice.md` — JR-identity, hard-rule no-go topics, named lived-work entities (read by `LI-2` and `X-2` hard-floor via `load_source_data`).
  - Per-platform register guidance (X operator-with-hot-takes vs LinkedIn thought-leader-story-led) lives in each lane's evolvable `<lane>-session.md` where it can evolve as the lane tunes — NOT in a locked substrate file.
  - Single substrate version-stamped, locked via `readonly_subprefixes` (in BOTH lanes, same path) + `configure_env` re-chmod (per lane).
- **FOLD into per-lane `programs/<lane>-session.md`:** `voice/profile.md` + `voice/hooks.md` + `voice/anti-ai-writing-style.md` + per-platform register guidance (most of anti-ai-writing-style overlaps with `slop_gate.py` regex; only the unique 20% — meta-rules about voice tells — lands inline; some tells are platform-specific so the inline content diverges between the two session prompts).

**NOT created in v1:** `runtime/<lane>.py` (only competitive needs salvage logic), new files in `scripts/` (shared scripts cover both lanes via variant directory), new `eval_cache.py` infra (both lanes import existing shared helper).

### 3.2 Net LOC budget

`x_engine/` total: ~3,983 (v1) → ~1,200 (seed; +50 for LinkedIn-specific CLI extensions: `pull-linkedin-search`, `pull-linkedin-user`, `top-linkedin`, `sources_linkedin.yaml`), −70%.

New under `archive/<seed>/` for BOTH lanes:
- `programs/`: ~290 lines = (100 session.md + 10 scope.yaml) × 2 lanes + 70 shared `voice.md`
- `workflows/`: ~320 LOC = (80 WorkflowSpec + 80 SessionEvalSpec) × 2 lanes
- `src/evaluation/rubrics.py` 12 new prose blocks (X-1..X-6 + LI-1..LI-6 at ~30-40 lines each): ~420 lines (this is content authoring, lives as Python string literals)
- Other autoresearch edits (LANES with two entries + Literal + 2-way scorer dispatch + 1 new scorer template + test exemption + Bright Data adapter scaffold): ~120 LOC

**Total net new in autoresearch: ~1,150 lines** (~290 programs/ + ~320 workflows/ + ~420 rubrics.py prose-block content + ~120 other plumbing). The rubrics.py 420 is content authoring (Python string literals carrying judge-prompt prose), not architectural LOC; the structural code is closer to ~730. Per-lane code is ~10× smaller than v1's x_engine because v1's writer/critic/revise passes collapse into "agent reads the prompt and does the work." Adding LinkedIn reuses pull.py + slop_gate (platform-aware extension) + voice substrate (shared); diverges at writer prompt + rubric + per-platform top-N + Apify cache table.

### 3.3 Per-lane evolvable agent prompts

Each lane's `programs/<lane>-session.md` is its own evolvable artifact. **Target ~100 lines per lane for v1 seed** (`geo-session.md` is 222 lines after ~7 generations; seeds are deliberately smaller, evolution grows them). Both follow `archive/v007/programs/geo-session.md` shape: header + agent identity + voice-substrate pointer (~10 lines) → quality criteria (~25 lines) → length brackets + when-to-use (~15 lines) → workspace + tools (~20 lines) → format spec + hard rules (~22 lines).

**Platform divergences:**
- x_engine: SHARP (250-300) / BUILD (500-900) / CASE-STUDY (1000-1500); tools `xeng angle-show|top-tweets|slop-check --platform x`; format §2.2 X-shape; per-platform register guidance in session.md = "operator-with-hot-takes, contrarian, sub-300-char sharps OK"
- linkedin_engine: SHORT_TAKE (500-900) / THOUGHT_LEADER (1500-2500) / CASE-STUDY (2500-3000); tools `xeng angle-show|pull-linkedin-search|pull-linkedin-user|top-linkedin|slop-check --platform linkedin`; format §2.2 LinkedIn-shape; hashtag policy (3-5 targeted) in hard rules; "story → lesson → CTA" template hint vs X's "contrarian-hook + bullet-list" (LI-3 penalises bald hot-takes that score on X); per-platform register guidance in session.md = "thought-leader, story-led, longer-form, hashtag-aware"

v1's plain-language rules → shared voice substrate. Per-platform register guidance lives in each lane's evolvable session.md (not the locked substrate) so register can evolve as the lane tunes. Hook bank + skeletons → dropped from seeds; evolution grows them.

**Per-lane mutation surface:** length-bracket ranges, quality-criteria phrasing (NOT IDs), hard-rules ordering, tool-list emphasis, hashtag policy (LinkedIn only), per-platform register guidance. **Locks** in `readonly_subprefixes` per lane: shared voice substrate (single file, locked in both lanes) + WorkflowSpec + SessionEvalSpec + 6 rubric prose anchors. No AUTOGEN block in either session.md (both `structural_doc_facts=()` + `structural_gate_functions=()` empty per lane). Real runtime structural gating lives in each lane's `SessionEvalSpec.structural_gate` (§4.4), not in AUTOGEN sync.

### 3.4 The agent's CLI tool surface (extended for both lanes)

Both lanes' agents use `xeng` like geo's agent uses `freddy`. Three command categories:

**Shared X data (existing v1 + extensions):** `pull-{search,user,github,rss}` (twitterapi.io for X data), `top-{tweets,releases,rss}` (rank queries on state.db; X-engagement-only — unchanged from v1), `slop-check --platform <x|linkedin>` (platform-aware regex floor; LinkedIn version drops em-dash check OR adjusts; X version unchanged), `mark-posted <draft_id> --platform <x|linkedin>` (dual-writes to `draft_decisions`; **MUST ship before day 1 of L1 X-dogfood window — see §7.3 critical-path note**), `info`.

**Shared NEW for L1 (used by both lanes' agents):** `angle-show <int_id>` (loads angle from v1 `angles` table for either lane's agent at session start; reads `headline, claim, source_url, source_text, voice_pillar` after the L1 ALTER per §5.2); `angle-list [--days N]` (ORDER BY `picked_at DESC`); `skip-draft <draft_id> --platform <x|linkedin> --reason <enum>` (per-platform marks); `holdout-export` (emits BOTH `domains.x_engine[]` AND `domains.linkedin_engine[]`, filtered for operator-noise `no_time` rows). NO `xeng pick-angles` — both lanes consume X-derived angles per D13 (§3.6).

**LinkedIn-specific NEW (Apify-backed, per D11):**
- `pull-linkedin-search <keyword> [--limit N] [--max-cu 50]` (calls `apimaestro/linkedin-posts-search-scraper-no-cookies`, persists to `linkedin_posts`). Default cost-cap `--max-cu 50` (apimaestro typical 20-50 cu per query). Cap fires `--exit-with-error` so daily total is bounded.
- `pull-linkedin-user <profile-url> [--limit N] [--max-cu 200]` (calls `harvestapi/linkedin-profile-posts`). Default cost-cap `--max-cu 200` (harvestapi typical 5-15 cu per profile).
- `top-linkedin [--days N]` — LinkedIn-engagement ranking on `linkedin_posts`, separate from `top-tweets` (Round-6 #25). **Engagement formula (Round-7 Gap B):** `score = (reactions × 1.0 + comments × 3.0 + shares × 5.0) × exp(-days_since_posted / 14)`. No follower-baseline normalization in v1 (`linkedin_posts` schema has no `author_followers` column); if heavy-follower outliers dominate the picker pool over 3+ generations, v1.5 lever adds harvestapi follower fetch + normalization.

Each top-N command does its own per-platform engagement scoring; no shared cross-platform normalization in `rank.py`.

**LinkedIn sources curation:** `sources_linkedin.yaml` (NEW; ~50 hand-curated LinkedIn creators in JR's niche + ~20 keyword queries — analogous to v1's `sources.yaml` for X). Frozen for v1+v2.

**Bright Data fallback adapter (NEW; feature-flagged off):** `xeng pull-linkedin-brightdata` scaffolded but disabled by default; activated by env-var `LINKEDIN_USE_BRIGHTDATA=1` if R5 fires. ~2d L1 scaffolding (account, integration adapter shell, normalizer skeleton). See §7.6 R5.

**Dropped from v1 (X engine):** `compose`, `draft-angle`, `write-vault`, `write-drafts`, `topic-pick` — collapsed into per-lane agent prompts. **Deferred to v2 of either lane:** `feedback --score 1-5` (Q1 locked binary for v1).

### 3.5 Parallel-run discipline (D6 — x_engine only)

7 days post-first-runnable: v1 cron + x_engine lane run daily on the same fixtures; JR reviews both. Day-7 verdict per D6 (BOTH JR-preference ≥3-of-7 AND holdout-aggregate non-regressive). If both pass → switch primary; v1 cron stays armed ≥30 more days as rollback. Trajectory positive but not 3-of-7 → extend 7 days. Flat/negative → pause, diagnose. v1 cron file is NOT deleted in v1.

LinkedIn lane has no parallel-run (no v1 baseline); adoption is immediate at L2 first-runnable; holdout grows from cold-start + organic marks.

### 3.6 Upstream pipeline — X-derived angles, both lanes consume

Per D13, **LinkedIn lane consumes X-derived angles in v1.** This is intentional and matches the cross-platform-consistency motivation for dual-lane day-1.

**Daily flow:** Daily 06:30 LaunchAgent runs `pull.py` (X via twitterapi.io → `tweets/releases/rss_items`) + `xeng pull-linkedin-search` across `sources_linkedin.yaml` keywords (cost-capped per §3.4). Weekly Sunday 07:00: `xeng pull-linkedin-user` across `sources_linkedin.yaml` creators (per-creator content updates slowly; weekly is cost-controlled). v1's existing per-pillar angle-write logic continues populating the `angles` table from X evidence (unchanged). Each lane's agent at session start reads `angle_id` from this shared table via `xeng angle-show` projecting `headline, claim, source_url, source_text, voice_pillar`.

**Per-lane angle handling (Round-7 Gap A clarified):**
- **x_engine agent**: gets X-derived angle → renders X draft using `xeng top-tweets` for supporting evidence + voice tells.
- **linkedin_engine agent**: gets the SAME X-derived angle → renders LinkedIn draft adapted for LinkedIn register; uses `xeng top-linkedin` to find LinkedIn-specific examples / supporting posts that resonate with LinkedIn audience around the same intention. The angle is the X-resonant intention; LinkedIn examples are the surface treatment.

**Per-platform engagement scoring is per-command:** `xeng top-tweets` (X-engagement weights, `rank.py:resonance_score` unchanged from v1). `xeng top-linkedin` (LinkedIn-engagement formula in §3.4). No cross-platform normalization in shared `rank.py`.

**Critical property:** the SAME `angle_id` appears in both lanes' search-v1 fixture lists — same input, two platform-specific draft outputs, matches "post similar takes on both platforms." LinkedIn lane may surface LinkedIn-only angles by hand at L2+ (operator-driven; insert row into `angles` with `voice_pillar` + LinkedIn-side `source_url`). Automated LinkedIn-side angle-write is a v1.5 lever per D13.

---

## §4 — Lane Architecture

### 4.1 LaneSpec entries (two new lanes)

Append BOTH to `LANES` dict at `autoresearch/lane_registry.py:73-184`. The x_engine entry, with linkedin_engine as a delta:

```python
"x_engine": LaneSpec(
    name="x_engine",
    is_workflow_lane=True,
    rubric_ids=("X-1", "X-2", "X-3", "X-4", "X-5", "X-6"),   # inlined; do NOT use _rubric_ids("X")
    path_prefixes=(
        "programs/x_engine-session.md",
        "programs/x_engine-evaluation-scope.yaml",
        "programs/references/voice.md",                       # SHARED voice substrate; in both lanes
        "templates/x_engine",
        "workflows/x_engine.py",
        "workflows/session_eval_x_engine.py",
    ),
    readonly_subprefixes=(
        "workflows/x_engine.py",
        "workflows/session_eval_x_engine.py",
        "programs/references/voice.md",                       # shared, locked in both lanes
    ),
    session_md_filename="x_engine-session.md",
    deliverables=("drafts/*.md",),
    intermediate_artifacts=("angles/*.json", "drafts/*.eval.json"),
    structural_doc_facts=(),
    structural_gate_functions=(),
),
```

**`linkedin_engine` LaneSpec — same shape; substitute `x_engine` → `linkedin_engine` in: `name`, 3 path_prefixes filenames (session.md, evaluation-scope.yaml, templates/<lane>), 2 readonly_subprefixes filenames (workflows/<lane>.py, workflows/session_eval_<lane>.py), session_md_filename. KEEP `programs/references/voice.md` in BOTH lanes' path_prefixes + readonly_subprefixes (shared substrate, single file).** Change `rubric_ids` to `("LI-1", "LI-2", "LI-3", "LI-4", "LI-5", "LI-6")`.

Both lanes claim the same path `programs/references/voice.md` in path_prefixes + readonly_subprefixes. **Verified safe** (Round-7 housekeeping): `path_is_readonly(rel_path, lane_name)` at `lane_registry.py:237-254` is a per-lane lookup against `LANES[lane_name].readonly_subprefixes` ∪ `SHARED_WORKFLOW_READONLY` — no uniqueness constraint across lanes. `WORKFLOW_PREFIXES = {n: s.path_prefixes for n, s in LANES.items() if s.is_workflow_lane}` is a per-lane dict; doesn't enforce disjoint ownership. Meta-agent of either lane reads the shared file, neither mutates (chmod 0444 + readonly check). Dual-claim is a clean pattern, not a novel risk.

**Empty-on-both pair** signals "no AUTOGEN sync." `tests/autoresearch/test_structural_doc_facts.py:36-54` parametrizes `test_every_bullet_has_gate_function` over `workflow_lane_names()` and asserts both lists non-empty per workflow lane (lines 48-49). With both new lanes empty-on-both, this test fails for both. **No existing skip-pattern mirrors this case** — the `monitoring` carve-out at lines 117-120 is in `test_every_gate_in_registry_has_assert_in_code` (a different test for gate-name reconciliation, not empty-tuple). v8 needs to add a NEW skip pattern at the top of `test_every_bullet_has_gate_function`:

```python
# Skip lanes that opt out of AUTOGEN structural sync (both fields empty).
# General form supports any future lane adopting the runtime-only structural-gate pattern.
if not bullets and not gates:
    pytest.skip(f"{domain} opts out of AUTOGEN structural sync (empty-on-both).")
```

Real runtime structural gating lives in each lane's `SessionEvalSpec.structural_gate` (§4.4).

### 4.2 Drift gate — 9 surfaces (both lanes)

| # | File | Edit | Layer |
|---|---|---|---|
| 1 | `autoresearch/lane_registry.py` | Append BOTH `"x_engine"` and `"linkedin_engine"` LaneSpec entries per §4.1. Also append both lane names to: `eval_suites/SCHEMA.md` lane-domain enumeration (search the file for the existing geo/competitive/monitoring/storyboard list) AND `TAXONOMY.md` lane reference table | L2 |
| 2 | `src/evaluation/models.py:160` | Add `"x_engine"` AND `"linkedin_engine"` to `EvaluateRequest.domain` Literal + audit `src/evaluation/` for any switch-on-domain handlers | L2 |
| 3 | `src/evaluation/rubrics.py` | **~5-7d real work** (1/3/5 anchor authoring + JR review cycle): author 12 prose blocks `_X_1`..`_X_6` + `_LI_1`..`_LI_6`, ~30-40 lines each, mirroring `_GEO_1`..`_GEO_8`. Add 12 `RubricTemplate(criterion_id, domain, scoring_type, prompt, is_cross_item=False)` entries — **all 12 are `scoring_type='gradient'`** (Round-7 Sub-2; v1 has no checklist sub-questions for X/LinkedIn; checklist style is a v2 lever if a dimension proves better as binary YES/NO). X-6 + LI-6 are `is_cross_item=True` (mirroring GEO-6 + SB-8 cross-item pattern). Update `assert len(RUBRICS) == 32` → `== 44` (verified during Round-7 audit: current count is exactly 32 = 4 lanes × 8 rubrics each) | L2 |
| 4 | `archive/<seed>/workflows/__init__.py` | Append BOTH `X_ENGINE_SPEC` and `LINKEDIN_ENGINE_SPEC` to `WORKFLOW_SPECS` | L2 |
| 5 | `archive/<seed>/workflows/session_eval_registry.py` | Append BOTH to `SESSION_EVAL_SPECS` | L2 |
| 6 | `archive/<seed>/scripts/evaluate_session.py:402` | argparse `choices=[..., "x_engine", "linkedin_engine"]` | L2 |
| 7 | `judges/evolution/prompts/` (NEW) | Author **ONE** prompt: `scorer_templated.md` with `{criteria}` placeholder (Round-6 #11 trim — was two near-identical files in v8.2). **DO NOT modify existing `scorer.md`** | L0 |
| 8 | `judges/evolution/agents/variant_scorer.py` `score_variant()` (lines 58-98) | **Structural refactor of `score_variant()` body**, NOT a surgical edit at lines 22-71 (those are constants + `_load_prompt` helper). Replace the existing `_load_prompt().format(domain=...,fixture=...,session_ref=...,artifacts=...)` with: 2-way branch on `payload["domain"]` — for `x_engine`/`linkedin_engine` load `scorer_templated.md` + `.format(criteria=_render_criteria_for_domain(domain), domain=..., fixture=..., session_ref=..., artifacts=...)`; for other domains preserve existing path | L0 |
| 9 | `tests/autoresearch/test_structural_doc_facts.py:36-54` | Add NEW `pytest.skip()` carve-out at the top of `test_every_bullet_has_gate_function`: `if not bullets and not gates: pytest.skip(f"{domain} opts out of AUTOGEN structural sync (empty-on-both).")`. **There is no existing skip-precedent to mirror** — the monitoring pattern at lines 117-120 is in a DIFFERENT test (`test_every_gate_in_registry_has_assert_in_code`, set-difference filter, not pytest.skip). v9 introduces a new pattern, doesn't replicate one | L2 |

**Adjacent (not drift-gate but required L1/L2 work):**
- `cli/freddy/fixture/sources.json` (domain-keyed): add x_engine + linkedin_engine entries. Both lanes' context is `angle_id` in state.db (no external fetch). Shape: `"x_engine": [{"source": "xeng-state", "data_type": "angle", "retention_days": 30, "command": ["xeng", "angle-show"], "args_template": [{"kind":"positional","from":"context"}], "arg_for_cache_key": {"from":"context"}}]`. L1.
- LaunchAgent `.plist` files in `~/Library/LaunchAgents/`: clone `x_engine/com.jryszardnoszczyk.x-engine.plist` for 4 new agents — `linkedin-pull-search` (daily 06:35), `linkedin-pull-user` (weekly Sun 07:00), `evolve-x-engine` (daily 02:00), `evolve-linkedin-engine` (daily 04:00). L1 (pulls) + L2 (evolves).

`rubrics.py:1001-1017` has 3 runtime assertions (`len(RUBRICS)==N`, lane-rubric-ids ⊆ RUBRICS, sum-equals-total) — row 3 is load-bearing, not cosmetic. The existing constant value (currently `32` per the `assert` literal but verify at L0) bumps by 12. `_assert_models_literal_matches()` at `lane_registry.py:272-284` hard-fails on (1)+(2) drift.

**L0 audit:** `grep -rn "range(1, 9)\|len(rubric_ids)" autoresearch/ src/` for other length-8 assumptions.

### 4.3 The WorkflowSpec — ~80 LOC per lane

**Pattern source: `archive/v007/workflows/competitive.py`.** Each lane copies competitive's shape (no-op `pre_summary_hooks`; KEEP-or-RUNNING `completion_guard`; cached single-deliverable `snapshot_evaluations`), substituting per-lane fields below. Do NOT mirror geo's `pre_summary_hooks` — geo runs `allocate_gaps.py` + `build_geo_report.py` which neither new lane needs.

WorkflowSpec (`specs.py:32-44`) requires 11 fields: 3 metadata (`name`, `config`, `config_dir_name`) + 7 callables + 1 struct (`findings_promotion`).

**Per-lane WorkflowConfig values** (`specs.py:13-22`; both lanes identical except as noted):

| Field | Value |
|-------|-------|
| `subdirs` | `["angles", "drafts"]` |
| `default_timeout` | `1800` |
| `multiturn_timeout` | `7200` |
| `stall_limit` | `5` |
| `default_client` | `"jr"` |
| `default_context` | `""` (fixture context is angle_id) |
| `multiturn_max_turns` | `2500` |

**Per-lane top-level WorkflowSpec values:**

| Field | x_engine | linkedin_engine |
|-------|----------|-----------------|
| `name` | `"x_engine"` | `"linkedin_engine"` |
| `config_dir_name` | `"x_engine"` | `"linkedin_engine"` |
| `findings_promotion.title` | `"Global Findings: X Engine"` | `"Global Findings: LinkedIn Engine"` |
| `findings_promotion.{confirmed,repeated}_threshold` | `(2, 2)` | `(2, 2)` |

**Per-lane callable divergences from competitive's pattern:**
- `configure_env(_client)` — re-`chmod 0444` the shared voice substrate at `Path(__file__).resolve().parent.parent / "programs/references/voice.md"`. Idempotent; both lanes re-chmod the SAME file. (Competitive's is no-op.)
- `pre_summary_hooks` — no-op (matches competitive).
- `snapshot_evaluations` — iterate `drafts/*.md` (instead of competitive's single `brief.md`), run `run_session_evaluator(<lane>, artifact, session_dir, eval_path, "full")` per draft (use `read_cached_eval_if_fresh` for freshness, mirroring competitive). Return `{"draft_decisions": [{"artifact", "decision"}, ...]}`.
- `completion_guard` — return `(None, None)` if any `draft_decisions[*].decision == "KEEP"`; else `("RUNNING", "no ship-eligible drafts produced; downgrading")`.
- `list_deliverables` — return `[f"drafts/{p.name}" for p in (session_dir/"drafts").iterdir() if p.is_file()]`.
- `augment_quality_metrics` — no-op v1 (mirror geo's pattern).
- `count_findings` — return `0` v1 (drafts ARE the deliverables; no findings.md to parse).

`linkedin_engine.py` is identical to `x_engine.py` except for the `run_session_evaluator` domain string + the per-lane top-level values above.

**JR-side voice substrate update:** `chmod +w` the shared file, edit, re-stamp at next variant generation. Updates apply to both lanes (single-source-of-truth).

### 4.4 SessionEvalSpec — ~80 LOC per lane, platform-specific rubric anchors

`archive/<seed>/workflows/session_eval_x_engine.py` AND `archive/<seed>/workflows/session_eval_linkedin_engine.py` each export `SPEC = SessionEvalSpec(...)`. **Both follow `archive/v007/workflows/session_eval_geo.py` shape** — concrete fields (Round-8 explicit):

| Field | Type | x_engine | linkedin_engine |
|-------|------|----------|-----------------|
| `domain` | str | `"x_engine"` | `"linkedin_engine"` |
| `domain_name` | str | `"X Engine"` | `"LinkedIn Engine"` |
| `criteria` | `dict[str, str]` | `{"X-1": "<50-100 word display description>", "X-2": "...", ..., "X-6": "..."}` (mirrors `session_eval_geo.py:CRITERIA` shape — display strings, not the rubrics.py 1/3/5 anchor prose; same 6 keys as `rubric_ids` in §4.1) | Same shape with `"LI-1".."LI-6"` |
| `structural_gate` | `Callable[[str, Path, Path], list[str]]` | function (signature below) | function (signature below) |
| `load_source_data` | `Callable[[str, Path, Path], str]` | function (signature below) | function (signature below) |
| `per_story_criteria` | `tuple[str, ...]` | `()` (no per-mode subset) | `()` |
| `cross_item_criteria` | `dict[str, CrossItemCriterion]` | `{"X-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)}` | `{"LI-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=600)}` |

**`structural_gate(_mode, artifact, session_dir) -> list[str]`** — returns list of failure strings (empty list = pass); per-artifact only (`evaluate_session.py:156-157` invokes with one artifact at a time). v1 checks per-lane:
- **x_engine**: artifact exists + non-empty; `[BODY]` block present; `[META]` block has all required keys (`hook`, `authority_anchor`, `specific_number`, `attribution`); char_count within bracket range for declared `length_bracket` ∈ {sharp 250-300, build 500-900, case_study 1000-1500}; `xeng slop-check --platform x` passes
- **linkedin_engine**: same as x_engine PLUS `hashtags` key in `[META]`; char_count within {short_take 500-900, thought_leader 1500-2500, case_study 2500-3000}; hashtag count ≤ 5 (spam guardrail; quality scoring on count happens in LI-5); `xeng slop-check --platform linkedin` passes

**`load_source_data(_mode, artifact, session_dir) -> str`** — concatenates source-text string the judge sees (alongside the artifact). For both lanes:
- Read `session_dir / "angles" / f"{angle_id}.json"` (cached at session start by the agent)
- Read `session_dir.parents[2] / "programs/references/voice.md"` (shared voice substrate — outside `session_dir`, not in artifacts payload by default; loaded explicitly so X-2 / LI-2 hard-floor can verify lived-work claims)
- Return concatenated string with `<angle>` and `<voice_substrate>` section markers

Identical path in both lanes' `load_source_data` (Round-7 #18: one substrate, single source of truth for JR-identity + named lived-work entities).

**Rubric anchor prose** (X-1..X-6 + LI-1..LI-6, ~140 lines of 1/3/5-anchor descriptions): see companion file `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`. Authored at L2 in `src/evaluation/rubrics.py`. JR's pre-L0 F4 task scores anchors against 10-20 reference posts + 5 external triangulation posts; reviews/revisions land in the companion file before L2 prose-block authoring locks them.

Score scale 0-10 for both lanes (judge interpolates from 1/3/5 prose anchors). Both lanes' criteria render into the shared parameterized `scorer_templated.md` per §2.5.

### 4.5 Variant backfill (D8) — both lanes

Seed-baseline variant gets these files for BOTH lanes:

**Per-lane (×2):** `programs/<lane>-session.md` (~100 lines), `programs/<lane>-evaluation-scope.yaml` (~10 lines, schema below), `workflows/<lane>.py` (~80 LOC WorkflowSpec per §4.3), `workflows/session_eval_<lane>.py` (~80 LOC SessionEvalSpec per §4.4).

**`<lane>-evaluation-scope.yaml` schema** (mirrors `archive/v007/programs/geo-evaluation-scope.yaml`):

```yaml
# x_engine-evaluation-scope.yaml
domain: x_engine
outputs:
  - "drafts/*.md"
source_data:
  - "angles/*.json"
transient:
  - "session.md"
  - "results.jsonl"
  - "logs/**/*"
notes: "x_engine session outputs live under drafts/; angles cached at session start in angles/. Scratch state (session.md, logs) is not part of the scored artifact set."
```

Same shape for `linkedin_engine-evaluation-scope.yaml` with `domain: linkedin_engine`.

**Shared (one file, both lanes):** `programs/references/voice.md` (~70 lines, version-stamped; locked in both lanes' `readonly_subprefixes`).

**Registry edits in seed-baseline:** 2-line edit each to `workflows/__init__.py` (registers BOTH `X_ENGINE_SPEC` and `LINKEDIN_ENGINE_SPEC` in `WORKFLOW_SPECS`) + `session_eval_registry.py` (both `SESSION_EVAL_SPECS` entries) + `scripts/evaluate_session.py` argparse choices (`["geo", "competitive", "monitoring", "storyboard", "x_engine", "linkedin_engine"]`).

`v001..v006` are NOT seeded — they pre-date both lanes and score 0.0 on each (intended; verify D8 dispatch path at L0 — single verification covers both lanes since the dispatch surface is the same).

### 4.6 Fixture pool policies

`pool_policies.json` is suite-keyed, not domain-keyed; existing `search-v1` (`live_fetch`) + `holdout-v1` (`hard_fail`) entries cover BOTH x_engine and linkedin_engine — **no edit needed to pool_policies.** **L0 open (per lane):** what does `live_fetch` mean when angles live in host-local state.db (not external API)? Verify `freddy fixture refresh --suite search-v1 --domain x_engine` AND `--domain linkedin_engine` against empty cache; if either hard-fails on unknown source descriptor, add x_engine + linkedin_engine entries to `cli/freddy/fixture/sources.json` (~0.5d each).

---

## §5 — Holdout Infrastructure (the prerequisite — L1)

### 5.1 The bar (per lane; bars differ)

**x_engine bar:** ≥25 marked drafts (`mark-posted` or `skip-draft`) in the past 30 days with structured reasons. v1 currently has zero (LaunchAgent not loaded; `recent_posted` empty). This is the **L1 dogfood prerequisite** — x_engine lane scaffold doesn't land in L2 until this is met.

**linkedin_engine bar:** ≥0 at L2-start; grows organically. JR has no v1 LinkedIn baseline to mark. The lane bootstraps in L2 by producing drafts day 1 → JR marks them daily as they appear → holdout grows from zero. The first 2-4 weeks of L2 will see LinkedIn promotion verdicts trip `first_variant_holdout_zero_score` (lane keeps producing; promotion just doesn't fire). Once ≥1 marked draft exists, that's the new comparison baseline; once ≥10 marked drafts exist, holdout signal becomes meaningful for promotion gating.

### 5.2 New CLI surface + new DB tables (added to v1 `xeng` CLI before any L2 work)

```
# Shared (used by both lanes):
xeng skip-draft <draft_id> --platform <x|linkedin> --reason <enum>   # NEW — writes draft_decisions, platform-tagged
xeng angle-show <id>                            # NEW — agent reads from v1 angles table (both lanes)
xeng angle-list [--days N]                      # NEW — ORDER BY picked_at DESC
xeng holdout-export [--output]                  # NEW — reads draft_decisions; emits BOTH domains.x_engine[] + domains.linkedin_engine[]

# LinkedIn-specific (Apify-backed, per D11):
xeng pull-linkedin-search <keyword> [--limit N] # NEW — apimaestro/linkedin-posts-search-scraper-no-cookies
xeng pull-linkedin-user <profile-url> [--limit N] # NEW — harvestapi/linkedin-profile-posts
xeng top-linkedin [--days N]                    # NEW — LinkedIn-engagement ranking on linkedin_posts (separate from top-tweets)
xeng pull-linkedin-brightdata <keyword>         # NEW (scaffolded, feature-flagged off via LINKEDIN_USE_BRIGHTDATA=1)
```

(`top-tweets` X-only + `top-linkedin` LinkedIn-only — separate commands, no parameterization. `xeng feedback --score` deferred per Q1 binary lock.)

**Database schema work:** `recent_posted` (`x_engine/pipeline/db.py:104-119`) is engagement-only; skipped drafts NEVER enter it under current schema. v9 adds:

- **NEW `draft_decisions`** with platform tag — `(decision_id, draft_id, angle_id, platform ∈ {'x','linkedin'}, outcome ∈ {'ship','skip'}, skip_reason ∈ enum-or-null, created_at)` + index on `(platform, created_at)` for holdout-export partition. Both lanes' `mark-posted`/`skip-draft` write here. **Critical-path: `mark-posted` MUST accept `--platform <x|linkedin>` and dual-write to `draft_decisions` BEFORE day 1 of L1 X-dogfood window** (Round-6 P0 #4). Otherwise the 14-day mark stream lands only in `recent_posted` and `holdout-export` produces zero rows. See §7.3 critical-path note.
- **NEW `linkedin_posts`** — `(post_id PK, author_name, author_profile_url, post_text, reactions, comments, shares, posted_at, fetched_at, source_query)` for Apify evidence cache. `post_id` canonicalises to LinkedIn activity URN; falls back to URL if URN absent. Populated by `xeng pull-linkedin-*` commands.
- **NEW `hand_drafts`** (Round-6 P0 #4) — `(draft_id INTEGER PK AUTOINCREMENT, platform TEXT, body TEXT, angle_id INTEGER NULL, created_at)` — supports the L1 cold-start flow where JR hand-writes 10 LinkedIn drafts; `xeng mark-posted` checks both `drafts` AND `hand_drafts` for the draft_id. Without this, the cold-start fixtures cannot land in `draft_decisions`.
- **ALTER TABLE on existing v1 `angles`** — `ADD COLUMN source_text TEXT`. **NOT idempotent** in SQLite — running ALTER TABLE ADD COLUMN twice raises `sqlite3.OperationalError`. L1 migration script MUST guard with `PRAGMA table_info(angles)` and skip if `source_text` already present. **Also required:** update the embedded `SCHEMA` constant string in `x_engine/pipeline/db.py:123-130` (used by `init_db()` for fresh installs) — without this, fresh installs running `init_db()` produce an 11-col table without `source_text` and the agent's `xeng angle-show` projection fails. **`source_text` population (Round-7 Sub-3):** v1's existing per-pillar angle-write logic predates the column and won't auto-populate it; rows pre-dating the ALTER TABLE remain null; new rows written by v1 logic are also null in v1 (v1 doesn't capture source body text). Agent's `xeng angle-show` returns the column as null when absent; agent prompts MUST tolerate null `source_text` and fall back to `source_url + headline` for source grounding. Backfill is a v1.5 lever: re-fetch source URLs for high-confidence existing angles + populate column. Out of scope for v1.

DDL ships in the L1 migration script (full statements there, not duplicated in this plan). v2 lever: `ALTER TABLE draft_decisions ADD COLUMN feedback_score INTEGER, feedback_notes TEXT` when `xeng feedback` ships.

`xeng mark-posted --platform <p>` writes to `draft_decisions` (X-side ALSO writes existing `recent_posted` for engagement-sync). LinkedIn engagement-sync deferred to v2.

`--reason` enum: `voice_off | factual_unverifiable | off_pillar | duplicate | no_time | other`. `no_time` is operator-noise; holdout-export filters these rows for both platforms.

### 5.3 Migration script

`xeng holdout-export` reads `draft_decisions`, filters `no_time` operator-noise rows, partitions by `platform` column. Emits TWO domain entries with shape `{fixture_id, client="jr", context=str(angle_id), anchor=True, env={JR_GROUND_TRUTH, SKIP_REASON, PLATFORM}}` per §2.3:
- Rows with `platform='x'` → `~/.config/gofreddy/holdouts/holdout-v1.json` `domains.x_engine[]`
- Rows with `platform='linkedin'` → same file, `domains.linkedin_engine[]`

Output file (chmod 600); operator atomically merges via the procedure in §7.9. The merge step is one operation that updates both lane domain entries in the same JSON file.

### 5.4 Dogfood + bootstrap windows

**X dogfood window (14 days, L1):** JR runs v1 X cron daily, marks every X draft. Reasons map to rubric dims (`voice_off` → X-1, `factual_unverifiable` → X-2, `off_pillar` → X-6, `duplicate` → no signal, `no_time` → filtered).

**Day-7 checkpoint** (catches bias before day-14 lockin): SQL on `draft_decisions WHERE platform='x'` for the trailing 7 days. Need ≥12 marks across ≥4 distinct pillars, with `other` < 30% and no single reason > 50% (catches review fatigue). If unhealthy: pause, diagnose with JR.

**Day-14 X verify:** `xeng holdout-export` for x_engine produces ≥25 anchored fixtures; all skip rows have non-null `skip_reason`. If <25: pause, diagnose with JR. No auto-extend.

**LinkedIn bootstrap (begins at L2 first-runnable):** the linkedin_engine lane produces drafts day 1 of L2. JR marks them daily as they appear (mark-posted / skip-draft with `--platform linkedin`). LinkedIn holdout enters L2 with **10 cold-start fixtures** (5 ship + 5 skip, hand-written + hand-marked by JR during the L1 X-dogfood window per §7.3 — Round-6 #12 honest re-estimate: ~5-10 hours over the 14 days, ideally one weekend block, NOT 30 minutes total as v8.2 claimed). Promotion verdicts have a real comparison from L2 day 1; subsequent organic marks accumulate as JR marks lane-produced drafts. Once ≥10 marked LinkedIn drafts exist (cold-start + organic), holdout signal becomes meaningful for promotion gating. **No 14-day waiting period for LinkedIn — work begins day 1 of L2.**

### 5.5 Why X holdout BEFORE lane scaffold (LinkedIn skips this)

L2 before L1 (X side) = first x_engine evolution cycle has no signal; frontier picks parents at random; promotion verdicts trip `first_variant_holdout_zero_score`; compute and judge tokens spent on noise. Hard ordering for x_engine.

LinkedIn side has no equivalent prerequisite because there's no v1 to dogfood. Accept that LinkedIn's first ~2-4 weeks of L2 produce drafts without meaningful promotion gating — that's the cost of bootstrapping a platform with no baseline. JR's daily marks during this window are what eventually unlock promotion.

---

## §6 — Evolution Loop Wiring (per lane; independent tracks)

Both lanes use autoresearch defaults end-to-end: shared parameterized scorer prompt (`scorer_templated.md` per §2.5) dispatched on domain to render per-lane criteria, per-fixture scoring (0–10), `decide/promotion` for cohort verdict (via `_holdout_eligibility` at `evaluate_variant.py:2719-2743`), `candidates_per_iteration=3` per lane, default 4-cycle auto-rollback. No `custom_*` callables on either LaneSpec. **Lanes evolve independently** — promotion in one doesn't gate or trigger the other.

**Per-lane mutation surfaces** (all in that lane's `programs/<lane>-session.md`):
- x_engine: length-bracket char ranges + when-to-use; X-1..X-6 criteria phrasing (NOT IDs); hard-rules ordering; tool-list emphasis; X-register guidance
- linkedin_engine: same shape but LI-1..LI-6 phrasing; hashtag policy (3-5 targeted); story-led-vs-lesson-led template emphasis; LinkedIn-register guidance

**Locks** (per lane):
- Lane-specific: WorkflowSpec (`workflows/<lane>.py`) + SessionEvalSpec (`workflows/session_eval_<lane>.py`) — both in that lane's `readonly_subprefixes` (chmod + sync ScopeViolation at meta-agent boundary; per-session re-chmod at runtime boundary).
- **Shared lock (in BOTH lanes' readonly_subprefixes):** `programs/references/voice.md` — neither lane's meta-agent can mutate the shared voice substrate. JR-only manual update path.
- Out of `path_prefixes` for both lanes (meta-agent workspace excludes): `voice/about-me.md`, `voice/no-go-topics.md`, `slop_gate.py`, `pull.py`, `db.py`, `sources.yaml`, `sources_linkedin.yaml`.

---

## §7 — Build Sequence, First-Runnable, Risks

### 7.1 Layer overview

3 layers: **L0** (~2d engineer-days) judge-service criteria infra for BOTH lanes; **L1** (~6.75d engineer-days + 14d X-dogfood) X holdout signal + v1 X cron revival + Apify subscription/keys + LinkedIn-specific CLI + LinkedIn pull cadence wiring (Gap C) + Bright Data fallback scaffold; **L2** (~16-18d engineer-days, ~25-30d calendar-days + 7d X-parallel-run + open-ended LinkedIn-bootstrap) seed cull + BOTH lane scaffolds + Q2 dispatch verification + fixtures + first iterations + X day-7 verdict + LinkedIn drift checks (Gap D) + D12 ROI verdict at week-8/12.

L0 runs first because the judge-service infra change is shared across all 6 lanes (the existing 4 + x_engine + linkedin_engine); the two-template approach (§2.5) keeps the existing 4 lanes' prompts unchanged so blast radius is contained.

**Engineer-days vs calendar-days** (Round-6 #19): the `~Nd` figures throughout §7 are engineer-days assuming serial work + no review latency. Realistic calendar wall-clock is ~1.8-2.2× because of JR review cycles on rubrics + voice substrate + fixture authoring + day-7 verdict + cross-lane debugging. §7.8 estimates the realistic calendar timeline.

### 7.2 L0 — judge-service criteria infra (~2 engineer-days)

**Pre-L0 operator task (F4 rubric validation, ~1.5 hr):** JR scores 10-20 LinkedIn posts (emulation set) + 5 external triangulation posts (customer/buyer ICP, top B2B-marketing posts last 90d) against the LI-1..LI-6 anchors in the companion file. If any score ≤6, rewrite the anchor before L2 prose-block authoring locks it.

**Coding work:**
- L0 day-0 smoke: `curl POST $EVOLUTION_JUDGE_URL/invoke/score` with both new domains; expect 200 + low aggregate. 4xx → escalate to JR. — 0.1d
- Author `judges/evolution/prompts/scorer_templated.md`. **Do NOT modify existing scorer.md.** — 0.15d
- Refactor `judges/evolution/agents/variant_scorer.py` `score_variant()` (lines 58-98): 2-way branch — new lanes load `scorer_templated.md` rendered with `_render_criteria_for_domain(domain)`; other lanes preserve existing path. Audit `range(1, 9)|len(rubric_ids)` in `autoresearch/`. — 0.5d
- Verify `freddy fixture refresh` for both new domains; add `cli/freddy/fixture/sources.json` entries if hard-fails (~0.5d each). — 0.25–1.0d
- Regression: `python3 -m autoresearch.evolve run --lane geo --iterations 1 --candidates 1`; geo aggregate within ±0.5 of historical. — 0.25d

**Ships when:** smoke responds for both new domains, 2-way dispatch correct, geo regression unchanged.

**Q2 dispatch verification deferred to L2-day-0** (lanes don't exist in registry until §4.2 rows 4+5 ship). Hardcoded `domain == "X"` branches in shared code (run.py + runtime/config.py + scripts/evaluate_session.py) verified to fall through gracefully; no edits needed.

### 7.3 L1 — Holdout signal + LinkedIn data infra (~6.75 engineer-days + 14d X-dogfood)

**Operator-side** (~3-12 hr total over 14 days; carve weekend block for cold-start):
- Apify + Bright Data account signups; install `APIFY_TOKEN` + `BRIGHTDATA_TOKEN` env vars
- Author `sources_linkedin.yaml` (~50 creators + ~20 keywords)
- Author shared `programs/references/voice.md` substrate
- **LinkedIn cold-start (R6 mitigation):** hand-write 5 ship + 5 skip LinkedIn drafts, mark with `anchor=true` + structured reason. ~5-10 hr (30-60 min per thought-leader draft). Fallback if bandwidth impossible: skip; LinkedIn lane bootstraps day-30+ via organic marks.

**Coding work:**
- **CRITICAL PATH:** `xeng mark-posted --platform` + `xeng skip-draft` + new `hand_drafts` table for cold-start draft_id flow. **MUST ship before day 1 of dogfood** — without, marks land in `recent_posted` only and `holdout-export` produces zero rows. — ~0.75d
- L1 day-0: revive v1 X cron (`launchctl load` existing .plist); verify 06:31 draft. — 0.1d
- Shared CLI: `xeng angle-show`, `xeng angle-list`, `xeng holdout-export`. — ~0.75d
- LinkedIn CLI: `xeng pull-linkedin-search` + `pull-linkedin-user` (Apify async actors; per-actor JSON normalizers; `--max-cu` cost-caps), `xeng top-linkedin` (engagement formula in §3.4), `xeng slop-check --platform linkedin` extension. — ~2.5d
- Bright Data fallback adapter: `xeng pull-linkedin-brightdata` feature-flagged off (`LINKEDIN_USE_BRIGHTDATA=1` activates); normalizer skeleton projects to `linkedin_posts` columns. — ~2d
- DB schema: NEW `draft_decisions` + `linkedin_posts` + `hand_drafts` + ALTER `angles` add `source_text` (PRAGMA-guarded; update embedded SCHEMA in `db.py:123-130` lockstep). — ~0.5d
- LinkedIn pull-cadence LaunchAgents: `linkedin-pull-search` daily 06:35 (`--max-cu 50`); `linkedin-pull-user` weekly Sun 07:00 (`--max-cu 200`); smoke-test single manual run. — ~0.25d

**Then 14d X-dogfood:** JR marks every X draft. Day-7 intermediate (pillar diversity ≥4 + skip-reason distribution; review-fatigue check). Day-14 verify `holdout-export` produces ≥25 anchored x_engine fixtures with non-null `skip_reason`. If <25: pause, diagnose.

### 7.4 L2 — Lane scaffolds + fixtures + first iterations (~16-18 engineer-days; ~25-30 calendar-days)

**Coding work** (drift-gate rows 1-6 + 9; rows 7-8 shipped at L0):
- Apply §3.1 cull to `x_engine/`. — ~1.25d
- Author 12 rubrics.py prose blocks (`_X_1`..`_X_6` + `_LI_1`..`_LI_6`) + bump `assert len(RUBRICS) == 32` → `44`; iterate against JR review. — ~5-7d
- Per-lane authoring ×2: `<lane>-session.md` + `<lane>-evaluation-scope.yaml`. — ~2d
- Per-lane workflows ×2: `workflows/<lane>.py` (§4.3) + `session_eval_<lane>.py` (§4.4; LinkedIn structural_gate adds hashtag count ≤5). — ~4d
- Drift-gate rows 1-6 + 9 (registry, models.py, rubrics imports, workflows __init__, session_eval_registry, evaluate_session.py argparse, test_structural_doc_facts pytest.skip). Row 1 also touches `eval_suites/SCHEMA.md` + `TAXONOMY.md`. — ~0.75d
- search-v1 fixtures (5-10 per lane) + holdout merge (x_engine ≥25 from dogfood, linkedin_engine 10 cold-start). — ~1d
- **L2-day-0 dispatch verification (Q2 lock):** after rows 4-5 ship, route a fixture to a non-`v007-curated` variant's `run.py`. `KeyError` → flip Q2 to Option A; graceful 0.0 → Option B holds. — ~0.1d
- First iterations per lane: `python3 -m autoresearch.evolve run --lane <lane> --iterations 1 --candidates 3`. — ~1d (mostly wait)
- First-runnable verification per §7.5. — ~0.75d
- Daily evolution LaunchAgents: `evolve-x-engine` 02:00, `evolve-linkedin-engine` 04:00 (offset to spread compute). — ~0.5d

**Then operator-side calendar:**
- 7d x_engine parallel-run + D6 day-7 verdict
- Open-ended LinkedIn bootstrap (cold-start + organic marks; first promotion-eligible cycle typically 2-4 weeks after L2)

### 7.5 First-runnable acceptance criteria (both lanes)

Each lane has its own first-runnable check. Both must pass before L2 is considered shipped.

**Shared (both lanes):**

| Criterion | How to verify |
|---|---|
| Both LaneSpecs registered + drift gate + rubrics.py assertions | `python3 -c "from autoresearch.lane_registry import _assert_models_literal_matches; _assert_models_literal_matches(); import src.evaluation.rubrics"` exits 0 (`rubrics.py` import triggers `len(RUBRICS) == N+12` + lane-rubric-ids ⊆ RUBRICS + sum-equals-total; verify N at L0) |
| Both LANES present in WORKFLOW_SPECS + SESSION_EVAL_SPECS | `python3 -c "from archive.<seed>.workflows import WORKFLOW_SPECS; from archive.<seed>.workflows.session_eval_registry import SESSION_EVAL_SPECS; assert {'x_engine','linkedin_engine'} <= set(WORKFLOW_SPECS) and {'x_engine','linkedin_engine'} <= set(SESSION_EVAL_SPECS)"` exits 0 |
| v1 `angles` table extended with `source_text` | `sqlite3 state.db 'PRAGMA table_info(angles)' | grep source_text` non-empty |
| LinkedIn evidence cache populated | `sqlite3 state.db 'SELECT COUNT(*) FROM linkedin_posts'` ≥ 50 (from L1 daily search + weekly creator pulls); `xeng top-linkedin --days 14` returns ≥10 ranked posts |
| Existing autoresearch test suite still green (Round-8) | `pytest tests/autoresearch/ -q` exits 0 — catches regressions in `test_lane_registry.py`, `test_lane_registry_lifecycle_wraps.py`, `test_evaluate_variant_target.py`, `test_judges.py`, `test_holdout_pythonpath.py` from the new LANES entries. Lane-shape assertions auto-pick up new lanes via `LANES` registry import; this verifies no existing parametrized test silently fails |

**Per-lane (each row × 2 lanes):**

| Criterion | How to verify (substitute `<lane>` ∈ {`x_engine`, `linkedin_engine`}) |
|---|---|
| `evaluate_session.py` accepts the lane | `python3 archive/<seed>/scripts/evaluate_session.py --domain <lane> --help` exits 0 |
| Search-v1 has fixtures | `jq '.domains.<lane> \| length' eval_suites/search-v1.json` ≥ 5 |
| Holdout has anchored fixtures | x_engine: `jq '.domains.x_engine \| map(select(.anchor==true)) \| length'` ≥ 25; linkedin_engine: `jq '.domains.linkedin_engine \| map(select(.anchor==true)) \| length'` ≥ 10 (cold-start fixtures from L1 per §7.3; hard gate IF cold-start protocol ran. If cold-start was skipped per the §7.3 alternative: ≥0 acceptable — see cold-start skip semantics below) |
| Variant subprocess launches | `python3 archive/<seed>/run.py --domain <lane> jr <int_angle_id> 1 600` runs to completion |
| At least one draft.md produced + conforms to §2.2 shape (per platform) | `ls archive/<seed>/sessions/<lane>/jr/drafts/*.md` non-empty AND lane's structural_gate returns `[]` on it |
| In-session evaluator runs | `python3 archive/<seed>/scripts/evaluate_session.py --domain <lane> --artifact <draft.md> --session-dir <session>` exits 0 with non-empty per-criterion feedback |
| Judge service responds with criteria-aware scoring | `evaluate_variant.py` post to `/invoke/score` returns 200 with `aggregate_score` 0–10 AND per-criterion entries reference X-1..X-6 (or LI-1..LI-6 for linkedin_engine) — NOT hallucinated criteria names |
| End-to-end | `python3 -m autoresearch.evolve run --lane <lane> --iterations 1 --candidates 3` exits 0 with 3 scored variants |

Quality bar at first-runnable is "the plumbing works for both lanes" — NOT "drafts are great". Day-1 seed quality may be worse than v1 (X) and worse-than-hand-written (LinkedIn); that's by design. Evolution earns it back per lane.

**Cold-start skip semantics (Round-7 Sub-4):** if you take the §7.3 fallback (drop the LinkedIn cold-start), L2 first-runnable still passes for linkedin_engine on the structural+plumbing dimensions. **L2 day-1 evolution attempts will trip `first_variant_holdout_zero_score` for linkedin_engine** until the first organic mark lands. Lane keeps producing drafts; cron does NOT pause; this is the EXPECTED state during organic bootstrap. Genuine first-runnable failure for linkedin_engine looks like: `structural_gate` raises on lane outputs, OR `xeng angle-show` fails for linkedin_engine fixtures, OR in-session evaluator returns empty per-criterion list. Those would block code-side ship. `first_variant_holdout_zero_score` does not.

### 7.6 Risk register (extended for dual-lane)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | X-dogfood window produces <25 marks in 14 days | Medium | High (L1 X-side blocks; LinkedIn lane can still proceed in L2) | L1 day-0 v1 X cron revival explicit (D9); day-7 intermediate checkpoint catches bias (§5.4); operator-noise `no_time` filter |
| R2 | Day-1 lane quality so bad that JR stops marking → review-fatigue starvation (per platform) | Medium | High | x_engine: holdout uses angle-IDs (§2.3) so ground truth is on angles already marked; lane day-1 quality doesn't block signal. linkedin_engine: bootstrap accepts initial low-quality drafts as the cost of having no v1 baseline; risk that JR finds lane outputs unusable for a sustained period and stops marking is real → see R6 contingency |
| R3 | Judge-service criteria infrastructure has unexpected server-side dependency | **Low (after L0)** | Critical | L0 day-0 curl smoke surfaces this for BOTH new domains; two-template approach (§2.5) keeps existing 4 lanes unchanged; ~0.5d if smoke succeeds, ~1-3d if server-side update needed |
| R4 | Cross-lane contamination if Q2=B — older variants raise `KeyError` on dispatch when search-v1 routes a fixture to a non-seed variant for either x_engine or linkedin_engine | Medium | High | L0 verification under D8 covers both lanes (single dispatch surface check). Mitigations: (a) seed-baseline pivot to Option A, (b) try/except at dispatch silently 0.0s missing lanes. Decision at L0 |
| R5 | **Apify LinkedIn actors break** — community-maintained; LinkedIn anti-scraping updates can degrade or zero specific actors mid-week. Both `apimaestro` and `harvestapi` are "no cookies" actors against LinkedIn's *unauthenticated* web view (strongest anti-bot defenses). **Round-6 #17:** the two actors' failure modes are NOT independent — a LinkedIn anti-scrape sweep targeting unauthenticated views typically hits ALL no-cookies actors simultaneously. Mitigation framing in v8.2 assumed independence; v9 treats joint-failure as the design point | Medium-High | High (LinkedIn lane data flow halts) | **Bright Data pre-positioned in L1** (Round-6 #17): account created, integration adapter scaffolded feature-flagged off, normalizer skeleton authored. Activation = `LINKEDIN_USE_BRIGHTDATA=1` env-var flip + smoke test (~30 min). NOT a 5-6d emergency response. Both Apify actors continue to cover orthogonal use cases (apimaestro=keyword-search, harvestapi=profile-only) so degraded-single-actor modes still apply; joint-failure flips to Bright Data |
| R6 | LinkedIn lane bootstrap stalls — JR marks <10 lane-produced drafts in first 4 weeks of L2 | **Low (after L1 cold-start)** | Medium | Pre-empted by L1 cold-start: per §7.3, JR hand-writes 5 ship + 5 skip LinkedIn drafts during the L1 X-dogfood window (~5-10 hours over 14 days, ideally one weekend block — Round-6 #12 honest re-estimate; was "30 min total" in v8.2, which was not realistic). Marks with `anchor=true` → linkedin_engine holdout starts L2 with 10 anchored fixtures (not zero). Lane has signal day 1 of L2; promotion gate has real comparison; subsequent organic marks add to the seed. **Fallback if cold-start bandwidth doesn't materialize:** drop the cold-start protocol; LinkedIn lane bootstraps with first promotion-eligible cycle landing at L2 day 30+ via organic marks alone. The plan ships either way |

**Minor risks:** compute budget (per-iteration ~2.5–5 hr per lane; daily total across 6 lanes ~15–25 hr); **Apify cost realistic $50-250/mo** (~50 creators × daily harvestapi × ~50 results = 75K/mo at $0.50-2 per 1K = $37-150/mo for profile pulls alone + ~20 keyword queries × daily × 50 results = $15-60/mo apimaestro; combined realistic $50-250/mo); Apify-actor maintenance ~0.5-1d/quarter steady state for normalizer updates; sources curation drift (frozen v1+v2; JR hot-edit channel); narrow evolution surface per lane (one prompt file each — focused early progress, capped upside); CrossItemCriterion truncation at words_per_item=600 must preserve [META] block — verify at L2 first-runnable; `xeng` access depends on PATH inheritance from variant subprocess — verify at L0 first-runnable on clean tmp workspace.

### 7.7 What's NOT in v1 of either lane

| Item | Where deferred | Trigger to revisit |
|---|---|---|
| Auto-posting to X or LinkedIn | v3+ | Manual posting validated for both platforms; automation policy + LinkedIn TOS-compatible API access |
| Other text platforms (Threads, Bluesky, Substack Notes) | v2+ | x_engine + linkedin_engine validated; clear ROI signal; "another platform like LinkedIn" sibling-lane add costs ~5d code |
| Per-pillar sub-lanes | v3+ | Pillar-specific evolution shows divergent winners across 5+ generations on either lane |
| `sources.yaml` / `sources_linkedin.yaml` mutation | v2+ | Pillar starvation across 3 generations on either lane |
| Specialized lane-specific judge agents (replacing scorer prompt templates) | v2+ | Three-template scorer approach proves under-enforces a rubric across 5 cycles |
| 1–5 nuanced holdout score | v2+ | Binary signal saturates on either lane |
| Length-bracket simplification | v2+ maybe | If a bracket ships <5% across 50 generations on either lane |
| Net-new exemplars added to references (per lane) | v2+ | Signal exists for "this exemplar drove X-N or LI-N lift" |
| Python script mutation surfaces (widen evolvable surface) | v2+ | Single-prompt evolution saturates per lane |
| LinkedIn engagement-sync (mirror of `recent_posted` for LinkedIn) | v2 | Need engagement signal for LinkedIn — would inform `feedback --score` rubric |
| Bright Data activation as primary LinkedIn data path | v1 (pre-positioned, feature-flagged off) | `LINKEDIN_USE_BRIGHTDATA=1` env-var flip if both Apify actors zero in same anti-scrape sweep; OR if keyword search coverage proves too thin in JR's niche after 4 weeks of L2 LinkedIn bootstrap |

### 7.8 Timeline shape

Engineer-day lower-bound: L0 ~2d + L1 ~6.75d + 14d X-dogfood (calendar) + L2 ~16-18d + 7d X-parallel-run (calendar) = **~46-48d engineer-days + 21d operator calendar**. Engineer-days don't run back-to-back without JR review latency; realistic calendar is materially longer.

**Realistic calendar timeline: 8-10 weeks for full dual-lane validation.** Realistic factors:
- L1 ~6.75 engineer-days → ~10-12 calendar-days with JR review on `voice.md` substrate + `sources_linkedin.yaml` + L1 cold-start writing-block coordination + LinkedIn-pull cron smoke
- L2 ~16-18 engineer-days → ~25-30 calendar-days because rubrics.py 12 prose blocks (~5-7 engineer-days) is the largest line item and requires multiple JR review passes; per-lane authoring + first-runnable surface 2-3 cross-lane debugging issues each needing a half-day JR coordination round-trip
- L0 ~2 engineer-days → ~3-4 calendar-days if judge-service smoke needs server-side state update
- X parallel-run 7d may extend 7 more if day-7 dual-gate verdict (D6) is positive but not 3-of-7
- LinkedIn bootstrap: open-ended post-L2; first promotion-eligible cycle typically lands 4 weeks after L2 first-runnable (cold-start floor of 10 fixtures unblocks first promotion attempt earlier than zero-baseline); D12 verdict at week-8/12 (per §7.9)

X-dogfood (L1) is the long pole during L1. LinkedIn bootstrap is the long *open-ended* pole post-L2 — adoption velocity depends on JR's marking discipline. D12 ROI threshold is the falsification gate at week-8/12 if LinkedIn lane underperforms.

### 7.9 JR's decision points

| Gate | When | What JR decides |
|---|---|---|
| **Q2** | L0 day 0 | Q1 + Q3 pre-resolved in §1.5. Q2 stays open until L0-day-0 dispatch verification — flip to Option A if non-seed variants raise `KeyError`; otherwise keep lean B |
| **L0 judge-service smoke verdict** | L0 day 0 | If 4xx "unknown domain" for either domain: pick path (judge-service-side state vs criteria-in-payload) |
| **Apify + Bright Data subscriptions + keys** | L1 day 0 | JR creates Apify account (active path) AND Bright Data account (pre-positioned fallback per Round-6 #17), installs `APIFY_TOKEN` + `BRIGHTDATA_TOKEN`. Required before LinkedIn CLI commands work / before joint-Apify-failure flip is available |
| **L1 voice substrate review** | After JR drafts shared `programs/references/voice.md` | JR self-reviews the shared substrate — does it capture JR-identity + named lived-work entities correctly? Per-platform register guidance does NOT live in this file (lives in evolvable session.md) |
| **L1 cold-start window check** | L1 day-7 | JR has authored ≥5 of the 10 LinkedIn cold-start drafts. If 0: pivot to "drop cold-start, accept 4-week LinkedIn bootstrap delay" per §7.3 alternative |
| **Day-7 X parallel-run verdict** | L2 day-15 | Both gates required (Round-6 #15): (a) x_engine wins JR-preference in ≥3 of 7 days, AND (b) holdout-aggregate non-regressive vs v1. Both pass → switch primary; (a) only with (b) regression → diagnose disagreement; trajectory positive but not 3-of-7 → extend 7 days; flat/negative → pause (per D6) |
| **LinkedIn bootstrap progress check** | L2 day-30 | ≥20 marked LinkedIn drafts (10 cold-start + 10 organic) → linkedin_engine has signal, evolution can promote; <20 → diagnose marking discipline; consider Bright Data flip if data flow is the bottleneck |
| **LinkedIn quality drift check** (Round-7 Gap D) | L2 day-30 / day-60 / day-90 | Compute trailing-30-day ship rate `(marked='ship' / total marked)` for `platform='linkedin'`. **<30% sustained for 30 days → pause + diagnose** (lane producing low-quality drafts; evolution may be optimizing for the wrong rubric anchors). **<50% sustained at day-90 → escalate to D12 ROI threshold check.** This is the ONLY quality gate for LinkedIn (no v1 baseline → no D6-equivalent dual-gate). Without it, lane could promote endlessly while producing drafts JR consistently skips |
| **D12 ROI verdict (LinkedIn lane fitness for v1)** | L2 week-8 / week-12 | Per D12: by week-8, lane produces ≥3 ship-eligible LinkedIn drafts/week with judge holdout aggregate ≥6.5. By week-12 if not met → lane paused (cron unloaded, code stays), reassessed for v2-port fit. Below-threshold ≠ port failure; means dual-lane wasn't ready |

**Holdout merge at L2:** `xeng holdout-export` → snapshot existing manifest → `jq --argfile` to merge BOTH `domains.x_engine[]` AND `domains.linkedin_engine[]` (LinkedIn entry may be empty initially per §5.4) → atomic mv → verify all 6 lanes still keyed + x_engine ≥25 + other lanes unchanged. 5-bash-command operator procedure; details in operator memory.

**Kill rules** (operator memory; per lane): `launchctl unload` for that lane's cron; `evolve_ops rollback --lane <lane>` for variant rollback; comment-out lane's `LANES` entry + revert `models.py` Literal for full lane disable. Each lane disabled independently.

---

**End of master plan v13.**
