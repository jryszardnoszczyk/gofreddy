# X + LinkedIn → Autoresearch Port — Master Plan

**Status:** v9 active 2026-05-07. Dual-platform lane port (X + LinkedIn) per JR direction. LinkedIn lane is sibling to x_engine; shares `pull.py` + `slop_gate.py` + `voice/about-me.md` substrate + a single shared scorer template, diverges at writer prompt + per-platform rubric + holdout + LinkedIn-specific evidence cache + LinkedIn-specific top-N command. Apify scrapers: `apimaestro/linkedin-posts-search-scraper-no-cookies` for keyword search; `harvestapi/linkedin-profile-posts` for per-creator pulls. **Bright Data pre-positioned in L1** (~2d feature-flagged-off scaffolding) so a joint Apify-actor failure is a 30-min env-var flip, not a 5-6d emergency. Architectural premises preserved from v7's 4-round review convergence; v9 (this revision) applied 4-reviewer triage on v8.2: trimmed three-template→two-template scorer, two→one shared voice substrate, dropped the speculative `pick-angles` shared upstream (lanes pull angles directly from v1 `angles` table), kept `top-tweets` + added separate `top-linkedin` instead of parameterizing.

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
5. Survive contact with the existing autoresearch contract — `WorkflowSpec` + `SessionEvalSpec` + 9 drift-gate surfaces (some per-lane, some shared across both lanes) enumerated in §4.2 that fail loud against each other.

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

### 1.5 Locked decisions (D1–D11) and open questions (Q1–Q3)

**Locked (lock confirmed by reading reference implementation, not a research summary):**

- **D1: Both lanes are workflow lanes, not core.** `is_workflow_lane=True` for each. Per-domain scoring reads `scores["x_engine"]` and `scores["linkedin_engine"]` independently (top-level). *[source: evaluate_variant.py:1538-1546]*
- **D2: Lane names = `x_engine` and `linkedin_engine`.**
- **D3: Per-lane rubric prefixes hardcoded inline.** `("X-1","X-2","X-3","X-4","X-5","X-6")` for x_engine; `("LI-1","LI-2","LI-3","LI-4","LI-5","LI-6")` for linkedin_engine. Do NOT call `_rubric_ids("X")` (helper hardcoded to range(1,9), produces 8 IDs). `len(rubric_ids)` audited at L0 (see §4.2).
- **D4: One evolvable artifact per lane.** `programs/x_engine-session.md` and `programs/linkedin_engine-session.md` (~100 lines each). **One shared static voice substrate** at `programs/references/voice.md` (per Round-6 #18 trim — JR-identity, hard-rule no-go topics, lived-work claims are JR's regardless of platform; per-platform register guidance lives in each lane's evolvable session.md where it can evolve). `LI-2` and `X-2` hard-floor read from this same file via `load_source_data`.
- **D5: Both lane runtimes agent-driven via `python3 <variant>/run.py --domain <lane> <client> <context> <max_iter> <timeout>`** — same dispatcher path all 4 existing lanes use. The agent uses `xeng` CLI tools (per-platform variants — `pull-linkedin-search` for keyword, `pull-linkedin-user` for per-creator, `top-linkedin` for ranked LinkedIn evidence; X agents continue to use `top-tweets`); no Python imports inside variant subprocess. Per-lane Python surface in `archive/<v>/workflows/` is ~160 LOC (WorkflowSpec ~80 + SessionEvalSpec ~80). With both lanes: ~320 LOC total. WorkflowSpec dataclass at `archive/v007/workflows/specs.py:32-44` requires 11 fields (3 metadata: `name`, `config`, `config_dir_name`; 7 callables: `configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings`; 1 struct: `findings_promotion`).
- **D6: Parallel-run only applies to x_engine (7 days post-first-runnable; JR-preference qualitative gate WITH holdout-aggregate cross-check).** JR reviews both v1-X and x_engine-lane outputs daily, logs preferred-source. Day-7 verdict requires BOTH: (a) x_engine wins ≥3 of 7 days on JR-preference, AND (b) x_engine holdout-aggregate score on the same day's fixtures is non-regressive vs v1-baseline. Disagreement between (a) and (b) is the actual signal — diagnose before flipping cron. (Round-6 #15 mitigation; single-rater unblinded preference alone is too noisy to flip primary.) **LinkedIn lane has no parallel-run** because there's no v1 LinkedIn baseline — the lane IS the first automated LinkedIn output. Adoption is immediate once first-runnable passes.
- **D7: Drop the writer-critic revise loop entirely in both seeds.** Evolution replaces revision; the agent writes one variant per angle per platform, in-session evaluator scores it, slop gate filters, ship decision recorded.
- **D8: Backfill both new lanes only into the seed-baseline variant.** Older variants pre-date the lanes; per-lane frontiers start at seed-baseline. **L0 verification per lane:** when search-v1 routes a fixture to a non-seed variant's `run.py`, does `get_workflow_spec("<lane>")` raise `KeyError` or gracefully 0.0? If `KeyError`: pivot Q2 to Option A or wrap dispatch with try/except.
- **D9: L1 day 0 = revive v1 X cron.** v1's LaunchAgent not loaded; `recent_posted` empty. The 14-day x_engine dogfood clock cannot start until v1 X produces drafts daily. **No equivalent revival for LinkedIn** — there's nothing to revive.
- **D10: Both lanes ship simultaneously in v1; LinkedIn does NOT wait for x_engine to validate.** Cost is +5 days L2 work over x_engine alone. Justification: shared upstream is genuinely shared; LinkedIn doesn't need x_engine's L1 dogfood prerequisite (it has no v1 to dogfood); pre-locking single-lane and adding LinkedIn later is more total work than dual-lane day 1. *[source: JR direction 2026-05-07 + cost analysis]*
- **D11: Apify scrapers selected for LinkedIn data, Bright Data pre-positioned as fallback.** `apimaestro/linkedin-posts-search-scraper-no-cookies` (8.5K MAU, 4.6/5, 35 reviews) for keyword search across LinkedIn — the load-bearing capability since LinkedIn has no commercial vendor with cheap+broad keyword search comparable to twitterapi.io's role for X. `harvestapi/linkedin-profile-posts` (11K MAU, 4.9/5, 24 reviews) for per-creator pulls. Both "no cookies" actors run against LinkedIn's unauthenticated web view (strongest anti-bot defenses; "no cookies" is convenience, NOT reliability). **Realistic cost $50-250/mo at v1 volume.** Per Round-6 #17: Bright Data LinkedIn Posts dataset (~$500-2K/mo, pre-indexed) is **pre-positioned in L1** — account created, integration adapter scaffolded feature-flagged off, normalizer skeleton authored. If a LinkedIn anti-scrape sweep zeros both Apify actors (R5 joint-failure mode), activation is a 30-min env-var flip not a 5-6d emergency response. *[source: vendor research 2026-05-07; Apify Store verification]*

**Resolved in v9 (per Round-6 triage):**

- **Q1 RESOLVED: Holdout score granularity = binary (ship/skip).** `skip_reason` structured enum; applies to BOTH lanes. The 1–5 column is a v2 lever.
- **Q3 RESOLVED: One shared voice substrate at `programs/references/voice.md`.** LinkedIn-specific register (story-led, less contrarian, hashtag-tolerant, longer-form) is encoded in `programs/linkedin_engine-session.md` (the evolvable surface where register can evolve as the lane tunes), not in a duplicate substrate file with ~70% overlap. Both lanes' `LI-2`/`X-2` hard-floor reads from the single shared voice file via `load_source_data`.

**Open (resolve at L0 day 0):**

- **Q2: Seed-baseline variant — extend `archive/v007/` (Option A) vs branch fresh `archive/v007-curated/` (Option B)?** Lean: B. Both options carry cross-lane contamination risk per D8. **Flip criteria:** if L0-day-0 dispatch verification (a non-seed variant routed to either lane via search-v1) raises `KeyError` rather than gracefully 0.0-ing → flip to Option A or wrap with try/except. JR sync at L0 day 0 weighs the L0 evidence, not rubber-stamps.

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
hashtags: "<3-5 targeted hashtags; LinkedIn rewards 3-5, penalises 0 or >5>"
[/META]
```

**Per-lane structural_gate divergences:**
- x_engine: `length_bracket ∈ {sharp, build, case_study}` with ranges 250-300 / 500-900 / 1000-1500
- linkedin_engine: `length_bracket ∈ {short_take, thought_leader, case_study}` with ranges 500-900 / 1500-2500 / 2500-3000
- linkedin_engine `[META]` requires `hashtags` field (3-5 targeted, comma-separated string); x_engine has no hashtags field (X penalises hashtag use)
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

### 3.2 Net LOC budget

`x_engine/` total: ~3,983 (v1) → ~1,200 (seed; +50 for LinkedIn-specific CLI extensions: `pull-linkedin-search`, `pull-linkedin-user`, `top-linkedin`, `sources_linkedin.yaml`), −70%.

New under `archive/<seed>/` for BOTH lanes:
- `programs/`: ~290 lines = (100 session.md + 10 scope.yaml) × 2 lanes + 70 shared `voice.md` (Round-6 #18: one substrate, not two; #20: no `pick-angles.md`)
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

**Shared NEW for L1 (used by both lanes' agents):** `angle-show <int_id>` (loads angle from v1 `angles` table for either lane's agent at session start; reads `headline, claim, source_url, source_text, voice_pillar` after the L1 ALTER per §5.2); `angle-list [--days N]` (ORDER BY `picked_at DESC`); `skip-draft <draft_id> --platform <x|linkedin> --reason <enum>` (per-platform marks); `holdout-export` (emits BOTH `domains.x_engine[]` AND `domains.linkedin_engine[]`, filtered for operator-noise `no_time` rows). Round-6 #20: NO `xeng pick-angles` command — both lanes pull angles directly from the v1 `angles` table populated by v1's existing per-pillar logic; if pillar starvation surfaces in v1.5, revisit.

**LinkedIn-specific NEW (Apify-backed, per D11):** `pull-linkedin-search <keyword> [--limit N]` (calls `apimaestro/linkedin-posts-search-scraper-no-cookies`, persists to state.db `linkedin_posts` table); `pull-linkedin-user <profile-url> [--limit N]` (calls `harvestapi/linkedin-profile-posts`); `top-linkedin [--days N]` (LinkedIn-engagement ranking on `linkedin_posts` table — separate command from `top-tweets`, NOT a parameterized rename, per Round-6 #25). Each top-N command does its own per-platform engagement scoring; no shared cross-platform normalization in `rank.py`.

**LinkedIn sources curation:** `sources_linkedin.yaml` (NEW; ~50 hand-curated LinkedIn creators in JR's niche + ~20 keyword queries — analogous to v1's `sources.yaml` for X). Frozen for v1+v2.

**Bright Data fallback adapter (NEW; feature-flagged off):** `xeng pull-linkedin-brightdata` scaffolded but disabled by default; activated by env-var `LINKEDIN_USE_BRIGHTDATA=1` if R5 fires. ~2d L1 scaffolding (account, integration adapter shell, normalizer skeleton). See §7.6 R5.

**Dropped from v1 (X engine):** `compose`, `draft-angle`, `write-vault`, `write-drafts`, `topic-pick` — collapsed into per-lane agent prompts. **Deferred to v2 of either lane:** `feedback --score 1-5` (Q1 locked binary for v1).

### 3.5 Parallel-run discipline (D6 — x_engine only)

For 7 days post-first-runnable: v1 cron writes daily to `x_engine/drafts/YYYY-MM-DD.md`; x_engine lane runs daily on the same set of angles via fixtures sourced from the same evidence pool. JR reviews both per §1.5 D6 protocol. **Day-7 verdict requires BOTH gates** (Round-6 #15 mitigation; single-rater unblinded preference alone is too noisy):
- (a) **JR-preference**: lane wins on JR-preference in ≥3 of 7 days
- (b) **Holdout-aggregate cross-check**: x_engine holdout-aggregate score on the same day's fixtures is non-regressive vs the v1-baseline aggregate (computed from the v1 cron's outputs scored against the same X-1..X-6 rubric)

If both gates pass → switch primary daily X output to lane (v1 cron stays armed ≥30 more days as rollback). If only (a) passes but (b) regresses → JR-preference and rubric-aggregate disagree; that disagreement is the actual signal — diagnose before flipping cron (likely indicates rubric mis-calibration OR JR-preference confirmation bias). Trajectory positive but not 3-of-7 → extend 7 more days. Trajectory flat/negative → pause, diagnose. v1 cron file (`install_schedule.sh` + `.plist`) is NOT deleted in v1 of either lane.

**LinkedIn lane has no parallel-run.** No v1 LinkedIn baseline exists; the lane IS the first automated LinkedIn output. Adoption is immediate at L2 first-runnable; JR starts marking lane-produced LinkedIn drafts daily, holdout grows from zero (per §5.4).

### 3.6 Upstream pipeline (lanes pull from v1 angles table)

Daily 06:30: `pull.py` (X via twitterapi.io → tweets/releases/rss_items in state.db) + `xeng pull-linkedin-*` (LinkedIn via Apify actors per D11 → `linkedin_posts` table). Then v1's existing per-pillar angle-write logic continues populating the v1 `angles` table from X evidence (no change to v1 behavior). Each lane's agent at session start consumes an `angle_id` from `angles` and reads `headline, claim, source_url, source_text, voice_pillar` via `xeng angle-show`.

**Per-platform engagement scoring is per-command, not shared:** `xeng top-tweets` ranks the X `tweets` table by X-engagement weights (likes/RT/replies, follower-baseline). `xeng top-linkedin` ranks the `linkedin_posts` table by LinkedIn-engagement weights (reactions/comments/shares). Each lane's agent calls the platform-appropriate top-N command from inside its session; no cross-platform normalization happens in shared `rank.py` because no consumer currently needs cross-platform comparison (each lane reads only its own platform's evidence).

**Round-6 #20 / Round-6 SG-2:** `xeng pick-angles` shared upstream LLM step was DROPPED from v9 (was new in v8). It existed only because dual-lane wanted "pick today's takes once, render twice" — a speculative abstraction with one consumer in X-only operation and an unproven coupling pattern in dual-lane (`programs/pick-angles.md` locked in BOTH lanes' `readonly_subprefixes` is novel for the existing 4-lane registry). v9 ships dual-lane WITHOUT this abstraction; if pillar starvation across both lanes surfaces in 5+ generations, revisit as a v1.5 lever.

**Critical property preserved:** the SAME `angle_id` from v1's `angles` table can appear in both lanes' search-v1 fixture lists. JR's daily X research populates angles; both lanes can execute against the same angle, rendering for different platforms. LinkedIn lane may also surface LinkedIn-only angles by hand or by future v1.5 LinkedIn-side angle-write logic — out of scope for v1.

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

Both lanes claim the same path `programs/references/voice.md` in path_prefixes — a novel pattern vs the existing 4-lane registry's disjoint ownership. **L0 verification:** confirm `archive_index.py` ScopeViolation enforcement does not collide on dual-claim. Expected behavior: meta-agent of either lane can read the shared file; neither lane's meta-agent can mutate it (chmod 0444 + readonly_subprefix lock). If collision surfaces at L0: pivot to one symlink + canonical owner (x_engine), or fold the substrate into per-lane prompt-references via `configure_env`.

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
| 3 | `src/evaluation/rubrics.py` | **~5-7d real work** (Round-6 #16 honest re-estimate; was 2d in v8.2): author 12 prose blocks (`_X_1`..`_X_6` for x_engine + `_LI_1`..`_LI_6` for linkedin_engine; 1/3/5 anchor format mirroring `_GEO_1`..`_GEO_8`, ~30-40 lines each — 12 × ~35 lines = ~420 lines of careful judge-prompt authoring; geo-rubric is the only existing reference and project from that, NOT from a generic prose-throughput rate). Includes JR review cycle (the F4 pre-L0 task pre-screens but doesn't replace the iteration loop). Add 12 `RubricTemplate(..., is_cross_item=...)` entries; per-criterion scoring types per §4.4; X-6 + LI-6 both `is_cross_item=True`; update `assert len(RUBRICS) == N` (verify N at L0 — current value reads from the existing _GEO_1..8 + _COMP_*..+ _MON_*.. + _STORY_* — count and adjust to N+12) | L2 |
| 4 | `archive/<seed>/workflows/__init__.py` | Append BOTH `X_ENGINE_SPEC` and `LINKEDIN_ENGINE_SPEC` to `WORKFLOW_SPECS` | L2 |
| 5 | `archive/<seed>/workflows/session_eval_registry.py` | Append BOTH to `SESSION_EVAL_SPECS` | L2 |
| 6 | `archive/<seed>/scripts/evaluate_session.py:402` | argparse `choices=[..., "x_engine", "linkedin_engine"]` | L2 |
| 7 | `judges/evolution/prompts/` (NEW) | Author **ONE** prompt: `scorer_templated.md` with `{criteria}` placeholder (Round-6 #11 trim — was two near-identical files in v8.2). **DO NOT modify existing `scorer.md`** | L0 |
| 8 | `judges/evolution/agents/variant_scorer.py` `score_variant()` (lines 58-98) | **Structural refactor of `score_variant()` body**, NOT a surgical edit at lines 22-71 (those are constants + `_load_prompt` helper). Replace the existing `_load_prompt().format(domain=...,fixture=...,session_ref=...,artifacts=...)` with: 2-way branch on `payload["domain"]` — for `x_engine`/`linkedin_engine` load `scorer_templated.md` + `.format(criteria=_render_criteria_for_domain(domain), domain=..., fixture=..., session_ref=..., artifacts=...)`; for other domains preserve existing path | L0 |
| 9 | `tests/autoresearch/test_structural_doc_facts.py:36-54` | Add NEW `pytest.skip()` carve-out at the top of `test_every_bullet_has_gate_function`: `if not bullets and not gates: pytest.skip(f"{domain} opts out of AUTOGEN structural sync (empty-on-both).")`. **There is no existing skip-precedent to mirror** — the monitoring pattern at lines 117-120 is in a DIFFERENT test (`test_every_gate_in_registry_has_assert_in_code`, set-difference filter, not pytest.skip). v9 introduces a new pattern, doesn't replicate one | L2 |

`rubrics.py:1001-1017` has 3 runtime assertions (`len(RUBRICS)==N`, lane-rubric-ids ⊆ RUBRICS, sum-equals-total) — row 3 is load-bearing, not cosmetic. The existing constant value (currently `32` per the `assert` literal but verify at L0) bumps by 12. `_assert_models_literal_matches()` at `lane_registry.py:272-284` hard-fails on (1)+(2) drift.

**L0 audit:** `grep -rn "range(1, 9)\|len(rubric_ids)" autoresearch/ src/` for other length-8 assumptions.

### 4.3 The WorkflowSpec — ~80 LOC per lane, mostly mirroring geo

`archive/<seed-baseline>/workflows/x_engine.py` and `archive/<seed-baseline>/workflows/linkedin_engine.py` each export `SPEC = WorkflowSpec(...)`. **Both follow `archive/v007/workflows/geo.py` shape end-to-end.** WorkflowSpec dataclass at `archive/v007/workflows/specs.py:32-44` requires **11 fields**:
- 3 metadata: `name` (str), `config` (WorkflowConfig nested struct), `config_dir_name` (str)
- 7 callables: `configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings`
- 1 struct: `findings_promotion` (FindingsPromotionConfig)

Most callables are no-ops in v1; `configure_env` is the load-bearing per-lane divergence.

**Per-lane divergence (identical pattern, different filename):** `configure_env(_client)` re-applies `chmod 0444` to the SHARED voice substrate per session. Meta-agent boundary (`archive_index.py:280-356` chmod + sync ScopeViolation) only covers proposer mutations; at session-time the runtime agent has Write+Edit tools — per-session re-chmod closes that boundary.

```python
def configure_env(_client: str) -> None:
    voice_path = Path(__file__).resolve().parent.parent / "programs" / "references" / "voice.md"
    if voice_path.exists():
        os.chmod(voice_path, 0o444)
```

Both lanes' `configure_env` re-chmod the SAME shared file — idempotent (chmod 0444 a second time is a no-op). Both use the identical implementation; differ only in `name` + `config` + `config_dir_name`.

For both lanes: `list_deliverables` returns `drafts/*.md`. `count_findings` returns 0 in v1. `findings_promotion = FindingsPromotionConfig(title="<Lane> Patterns", confirmed_threshold=3, repeated_threshold=2)` per lane. `name`, `config_dir_name` set to `"x_engine"` / `"linkedin_engine"`. `config` = lane-specific `WorkflowConfig` instance (copy geo's shape; lane-specific values for any required fields). Other callables: copy geo's no-op patterns.

**JR-side voice substrate update workflow:** `chmod +w` the shared file, edit, re-stamp at next variant generation. Updates apply to both lanes simultaneously (single-source-of-truth).

### 4.4 SessionEvalSpec — ~80 LOC per lane, platform-specific rubric anchors

`archive/<seed>/workflows/session_eval_x_engine.py` AND `archive/<seed>/workflows/session_eval_linkedin_engine.py` each export `SPEC = SessionEvalSpec(...)`. **Both follow `archive/v007/workflows/session_eval_geo.py` shape** — `domain`, `domain_name`, `criteria` dict, `structural_gate` callable, `load_source_data` callable, `cross_item_criteria` dict.

**Per-lane divergences (same shape, different content):**

1. **Both lanes' `load_source_data` reads the SHARED voice substrate** so the judge can enforce the lived-work-claim hard-floor (X-2 / LI-2). Voice file at `session_dir.parents[2] / "programs/references/voice.md"` — outside `session_dir`, not in artifacts payload by default. Concat into source_data alongside the angle JSON. **Identical path in both lanes' `load_source_data`** (Round-6 #18: one substrate, single source of truth for JR-identity + named lived-work entities).

2. **Cross-item criteria sized for platform's prose length:**
   - x_engine X-6: `CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)` — sized for CASE-STUDY drafts (1000-1500 chars ≈ 250-400 words)
   - linkedin_engine LI-6: `CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=600)` — sized for THOUGHT_LEADER + CASE-STUDY drafts (LinkedIn drafts are 2-3× longer than X)

`structural_gate` per lane is per-artifact only (`evaluate_session.py:156-157` invokes with one artifact at a time). v1 checks per-lane:
- x_engine: `[BODY]` block, `[META]` block has hook+authority_anchor+specific_number+attribution, char_count within {sharp, build, case_study} range
- linkedin_engine: `[BODY]` block, `[META]` block has hook+authority_anchor+specific_number+attribution+hashtags, char_count within {short_take, thought_leader, case_study} range, hashtag count ∈ [3,5]

**The X-1..X-6 rubric anchors (x_engine; rendered into `scorer_templated.md` via `_render_criteria_for_domain("x_engine")`):**

| ID | Anchor (50-100 words each) |
|---|---|
| X-1 | JR's voice — first-person, opinionated, plain-language register accessible to a non-engineer founder/marketer. Jargon without inline plain-English context caps this dimension. AUTOMATIC ≤4 if 2+ unexplained technical terms; AUTOMATIC ≤6 if any jargon without plain-English follow-up. |
| X-2 | Factual specificity. SOURCE claims must verify against source_text. INTERPRETIVE claims framed as JR's view ('my read', 'in our work') OK. **HARD FLOOR:** any first-person specific lived-work claim ('when I built X for client Y') REQUIRES the named entity to appear in `programs/references/voice.md` (shared substrate, loaded into source_data). Unnamed-client claims → ≤3. |
| X-3 | Hook strength. SHARP brackets — first 8-12 words carry the punch. BUILD/CASE-STUDY — first 1-2 sentences earn line two (beat the show-more cutoff). Generic openers and rhetorical-question hooks ≤4. |
| X-4 | Slop-freeness. Zero AI-tells. Banned phrases per `slop_gate.py` regex are a deterministic floor; this dimension judges what slips through. |
| X-5 | Structural richness. Bracket-aware: SHARP earns 10 with one sharp claim+support pair; BUILD earns 10 with prose intro + structural pivot + 3-5 substantive bullets + authority anchor + outcome metric; CASE-STUDY earns 10 with multi-paragraph narrative + sensory detail + numbers timeline + implication close. Pad-to-length = ≤4. |
| X-6 | Cross-item: across drafts in this cohort, no two use the same primary differentiator, source, or hook archetype. The variant should spread across `voice_pillars` listed in angle metadata. (geometric mean across `drafts/*.md`.) |

**The LI-1..LI-6 rubric anchors (linkedin_engine; rendered into `scorer_templated.md` via `_render_criteria_for_domain("linkedin_engine")`):**

| ID | Anchor (50-100 words each) |
|---|---|
| LI-1 | JR's LinkedIn voice — first-person, story-led, professional register accessible to B2B buyers + agency operators + C-suite. Plain language still required (jargon caps voice score) but tone is noticeably less contrarian than X. AUTOMATIC ≤4 if it reads as bait-y, hot-take-y, or "Twitter-translated"; AUTOMATIC ≤6 if jargon without plain-English follow. The lever is *thoughtful authority*, not *contrarian punch*. |
| LI-2 | Factual specificity. Same SOURCE/INTERPRETIVE split as X-2. **HARD FLOOR:** lived-work claims REQUIRE the named entity to appear in `programs/references/voice.md` (shared substrate, loaded via load_source_data). Specific claims about unnamed clients/projects → ≤3. LinkedIn audience punishes vague claims harder than X audience does — score ceiling capped at 7 for any first-person specific claim that doesn't name the entity. |
| LI-3 | Hook strength. LinkedIn rewards story-led openings ("Last quarter I learned X.") + concrete-result openings ("47 hours of agent debugging led to one config change.") + before-the-fold tension. PUNISHES contrarian hot-takes that work on X ("Most marketers don't realize..." → ≤3 on LinkedIn even though it works on X). First 1-2 sentences earn line two (beat the show-more cutoff at ~210 chars on web LinkedIn). Generic openers ≤4. |
| LI-4 | Slop-freeness. Zero AI-tells AND zero LinkedIn-AI-tells. Banned phrases include the deterministic regex floor (`slop_gate.py --platform linkedin`) PLUS LinkedIn-specific tells: "Game-changer.", "Here's what I learned." (alone), "Thoughts? 👇", "Agree? 🤔", excessive line breaks for whitespace inflation, fake "Hot take:" framings. This dimension judges what slips through the deterministic gate. |
| LI-5 | Structural richness. Bracket-aware: SHORT_TAKE (500-900) earns 10 with story-opening + 1 substantive paragraph + closing thought; THOUGHT_LEADER (1500-2500) earns 10 with story → frame → 3-5 numbered points → implication close; CASE_STUDY (2500-3000) earns 10 with multi-paragraph narrative + numbers timeline + named characters + implication close. Pad-to-length, "I'm sharing this because..." filler, motivational-poster generality = ≤4. |
| LI-6 | Cross-item: across drafts in this cohort, narrative archetype varies (story-led vs lesson-led vs comparison) and drafts spread across `voice_pillars`. PUNISHES same-tone-same-format streak. (geometric mean across `drafts/*.md`.) Note: hashtag-set diversity is NOT scored here — same-pillar drafts may legitimately share signature 3-tag combos for brand consistency; per-draft hashtag count ∈ [3,5] is enforced deterministically by structural_gate, not by judge. |

Score scale 0-10 for both lanes (judge interpolates from 1/3/5 prose anchors). Both lanes' criteria render into the shared parameterized `scorer_templated.md` per §2.5 (one template, dispatched on domain).

### 4.5 Variant backfill (D8) — both lanes

Seed-baseline variant gets these files for BOTH lanes:

**Per-lane (×2):** `programs/<lane>-session.md` (~100 lines), `programs/<lane>-evaluation-scope.yaml` (~10 lines), `workflows/<lane>.py` (~80 LOC WorkflowSpec per §4.3), `workflows/session_eval_<lane>.py` (~80 LOC SessionEvalSpec per §4.4).

**Shared (one file, both lanes):** `programs/references/voice.md` (~70 lines, version-stamped; locked in both lanes' `readonly_subprefixes`). Round-6 #20: NO `programs/pick-angles.md` — was in v8.2, dropped in v9.

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

(Round-6 #20: NO `xeng pick-angles` — angles read from v1 `angles` table populated by v1's existing per-pillar logic. Round-6 #25: `top-tweets` stays X-only and unchanged; `top-linkedin` is a separate command, NOT a parameterized `top-posts --platform` rename. `xeng feedback --score` is NOT in L1; deferred per Q1 binary lock.)

**Database schema work:** `recent_posted` (`x_engine/pipeline/db.py:104-119`) is engagement-only; skipped drafts NEVER enter it under current schema. v9 adds:

- **NEW `draft_decisions`** with platform tag — `(decision_id, draft_id, angle_id, platform ∈ {'x','linkedin'}, outcome ∈ {'ship','skip'}, skip_reason ∈ enum-or-null, created_at)` + index on `(platform, created_at)` for holdout-export partition. Both lanes' `mark-posted`/`skip-draft` write here. **Critical-path: `mark-posted` MUST accept `--platform <x|linkedin>` and dual-write to `draft_decisions` BEFORE day 1 of L1 X-dogfood window** (Round-6 P0 #4). Otherwise the 14-day mark stream lands only in `recent_posted` and `holdout-export` produces zero rows. See §7.3 critical-path note.
- **NEW `linkedin_posts`** — `(post_id PK, author_name, author_profile_url, post_text, reactions, comments, shares, posted_at, fetched_at, source_query)` for Apify evidence cache. `post_id` canonicalises to LinkedIn activity URN; falls back to URL if URN absent. Populated by `xeng pull-linkedin-*` commands.
- **NEW `hand_drafts`** (Round-6 P0 #4) — `(draft_id INTEGER PK AUTOINCREMENT, platform TEXT, body TEXT, angle_id INTEGER NULL, created_at)` — supports the L1 cold-start flow where JR hand-writes 10 LinkedIn drafts; `xeng mark-posted` checks both `drafts` AND `hand_drafts` for the draft_id. Without this, the cold-start fixtures cannot land in `draft_decisions`.
- **ALTER TABLE on existing v1 `angles`** — `ADD COLUMN source_text TEXT`. **NOT idempotent** in SQLite — running ALTER TABLE ADD COLUMN twice raises `sqlite3.OperationalError`. L1 migration script MUST guard with `PRAGMA table_info(angles)` and skip if `source_text` already present. **Also required:** update the embedded `SCHEMA` constant string in `x_engine/pipeline/db.py:123-130` (used by `init_db()` for fresh installs) — without this, fresh installs running `init_db()` produce an 11-col table without `source_text` and the agent's `xeng angle-show` projection fails. Agents read via `xeng angle-show` projecting `headline, claim, source_url, source_text, voice_pillar`. v1's existing per-pillar logic populates `source_text` going forward; backfill optional.

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
- **Shared lock (in BOTH lanes' readonly_subprefixes):** `programs/references/voice.md` — neither lane's meta-agent can mutate the shared voice substrate. JR-only manual update path. (Round-6 #20: NO shared `pick-angles.md` lock — was in v8.2, dropped.)
- Out of `path_prefixes` for both lanes (meta-agent workspace excludes): `voice/about-me.md`, `voice/no-go-topics.md`, `slop_gate.py`, `pull.py`, `db.py`, `sources.yaml`, `sources_linkedin.yaml`.

---

## §7 — Build Sequence, First-Runnable, Risks

### 7.1 Layer overview

3 layers: **L0** (~2d engineer-days) judge-service criteria infra for BOTH lanes + Q2 verification; **L1** (~6.5d engineer-days + 14d X-dogfood) X holdout signal + v1 X cron revival + Apify subscription/keys + LinkedIn-specific CLI work + Bright Data scaffold (Round-6 #17); **L2** (~16-18d engineer-days, ~25-30d calendar-days + 7d X-parallel-run + open-ended LinkedIn-bootstrap) seed cull + BOTH lane scaffolds + fixtures + first iterations + X day-7 verdict + LinkedIn lane-runs-and-marks-grow phase.

L0 runs first because the judge-service infra change is shared across all 6 lanes (the existing 4 + x_engine + linkedin_engine); the two-template approach (§2.5) keeps the existing 4 lanes' prompts unchanged so blast radius is contained.

**Engineer-days vs calendar-days** (Round-6 #19): the `~Nd` figures throughout §7 are engineer-days assuming serial work + no review latency. Realistic calendar wall-clock is ~1.8-2.2× because of JR review cycles on rubrics + voice substrate + fixture authoring + day-7 verdict + cross-lane debugging. §7.8 estimates the realistic calendar timeline.

### 7.2 L0 — Pre-prerequisite (both lanes' shared infra)

Q1 and Q3 are pre-resolved (§1.5). Q2 stays open with explicit flip criteria — JR sync at L0 day 0 weighs the L0-day-0 dispatch verification.

**Operator-side pre-L0 task (F4 rubric-validation gap):** JR picks 10-20 LinkedIn posts representing the standard he wants linkedin_engine drafts to hit (creators in JR's niche he'd want to emulate — Sahil Bloom / Justin Welsh / Lara Acosta archetype + agency-operator-specific peers). For each, mentally score against the LI-1..LI-6 anchors at §4.4. **External triangulation (Round-6 #18):** ALSO score 5 high-performing LinkedIn posts NOT in the emulation set (e.g., posts from JR's actual customer/buyer ICP, top posts in B2B-marketing tag from past 90 days). If the rubric scores them very differently than the emulation set, the rubric is mis-calibrated — single-rater bias check. If any of either group score ≤6 against the rubric, rewrite the offending anchor before L0 locks it via the L2 rubrics.py prose-block authoring (note: prose-block authoring is L2 work per §4.2 row 3, but rubric phrasing is locked at L0 conceptually so JR's review can land before code does). ~1.5 hours. Highest-ROI pre-L0 task; prevents months of wrong-rubric-locked evolution.

**Coding work (~2 days engineer-days):**
- L0 day 0 smoke (BEFORE editing): `curl POST $EVOLUTION_JUDGE_URL/invoke/score` with `{"domain":"x_engine",...}` then `{"domain":"linkedin_engine",...}`. Expected: 200 + hallucinated low aggregate for both. If 4xx "unknown domain": escalate to JR for judge-service repo update. — 0.1d
- L0 day 0 dispatch verification (Q2 flip criteria): construct a non-seed variant test that routes to either lane's `run.py`; observe whether dispatch raises `KeyError` or gracefully 0.0s. JR sync to lock Q2 (A vs B) based on observed behavior. — 0.1d
- Author NEW `judges/evolution/prompts/scorer_templated.md` with `{criteria}` placeholder. **Do NOT modify existing scorer.md.** — 0.15d
- Modify `judges/evolution/agents/variant_scorer.py` `score_variant()` (lines 58-98 — structural refactor, NOT a surgical edit at lines 22-71): 2-way branch on `payload["domain"]`: x_engine|linkedin_engine → `scorer_templated.md` rendered with `criteria=_render_criteria_for_domain(domain)`; other → unchanged `scorer.md` path. Add `_render_criteria_for_domain` helper (~10 LOC). Grep `range(1, 9)|len(rubric_ids)` for length-8 assumptions in `autoresearch/`. — 0.5d
- Verify `freddy fixture refresh --suite search-v1 --domain x_engine` AND `--domain linkedin_engine` against empty cache. If either hard-fails: add x_engine + linkedin_engine entries to `cli/freddy/fixture/sources.json` (~0.5d each). — 0.25–1.0d
- Regression: `python3 -m autoresearch.evolve run --lane geo --iterations 1 --candidates 1` after dispatch change; confirm geo aggregate within ±0.5 of historical. — 0.25d

L0 ships when: smoke responds for BOTH new domains, 2-way scorer dispatch correct, fixture refresh path settled per-domain, Q2 locked, geo regression unchanged.

### 7.3 L1 — Holdout signal + LinkedIn data infra (the prerequisite)

**Operator-side (parallel to coding):**
- JR signs up for Apify account, gets API token, sets `APIFY_TOKEN` env var. ~30 min.
- JR signs up for Bright Data account (free tier OK for scaffolding), captures credentials in `BRIGHTDATA_TOKEN` env var (Round-6 #17 pre-positioning). ~30 min.
- JR authors `sources_linkedin.yaml` — ~50 LinkedIn creators in niche + ~20 keyword queries; ~1-2 hours.
- JR authors the shared `programs/references/voice.md` substrate — JR-identity, hard-rule no-go topics, named lived-work entities. ~1-2 hours of editorial work. (Round-6 #18: one substrate, not two; per-platform register guidance lives in evolvable session.md authored at L2.)
- **L1 LinkedIn cold-start (R6 mitigation; Round-6 #12 honest re-estimate):** JR hand-writes 5 LinkedIn drafts he'd ship + 5 he'd skip, marks each with `anchor=true` + structured reason. Becomes the linkedin_engine holdout cold-start seed (10 fixtures with ground_truth). Solves two problems: (a) prevents 1-fixture-promotion-noise (autoresearch's gate fires on candidate>0 with no baseline; with 10 hand-graded fixtures, first promotion has a real comparison), (b) seeds R6 mitigation so the lane has signal day 1 of L2. **~5-10 hours total** over the 14-day dogfood window — realistic time for hand-writing 10 thought-leader drafts at JR's craft level (LinkedIn drafts are 500-3000 chars per §2.2; 30-60 min per draft is honest). **Recommended:** carve out one weekend block; running this in 30-min snippets across 14 days during a window already saturated with X-marking is a recipe for low-quality cold-start drafts. Alternative if bandwidth is impossible: drop the cold-start protocol; LinkedIn lane bootstraps with first promotion-eligible cycle landing at L2 day 30+ via organic marks alone.

**Coding work (~6.5 days engineer-days):**
- L1 day 0: revive v1 X cron via `cd x_engine && ./install_schedule.sh && launchctl list com.jryszardnoszczyk.x-engine`. Verify a draft lands at 06:31 next morning. — 0.1d
- **CRITICAL PATH (Round-6 P0 #4):** Modify `xeng mark-posted` to accept `--platform <x|linkedin>` and dual-write to `draft_decisions`; add `xeng skip-draft --platform <p> --reason <enum>` (Typer + `SkipReason` Enum import; values: `voice_off | factual_unverifiable | off_pillar | duplicate | no_time | other`). Build NEW `hand_drafts` table support for the cold-start flow (mark-posted checks both `drafts` and `hand_drafts` for draft_id). **MUST ship before day 1 of the 14-day X-dogfood window** — without this, marks land only in `recent_posted` and `holdout-export` produces zero rows. — ~0.75d
- Add shared CLI: `xeng angle-show` (reads from v1 `angles` table after the L1 ALTER), `xeng angle-list`, `xeng holdout-export` (filters operator-noise; emits both domain entries) — ~0.75d
- Add LinkedIn-specific CLI (Apify is async — POST run-ID, poll until SUCCEEDED, GET dataset items; per-actor result-shape parsing; cost-cap `--max-cu` flag): `xeng pull-linkedin-search` (apimaestro keyword search + JSON-shape normalizer), `xeng pull-linkedin-user` (harvestapi profile pulls + JSON-shape normalizer), `xeng top-linkedin` (LinkedIn-engagement ranking on `linkedin_posts`; separate command, NOT a parameterized rename of top-tweets), `xeng slop-check --platform <x|linkedin>` extension (LinkedIn-AI-tells additive, em-dash check kept cross-platform) — ~2.5d
- **Bright Data fallback adapter (Round-6 #17 pre-positioning, ~2d):** scaffold `xeng pull-linkedin-brightdata` feature-flagged off (gated on `LINKEDIN_USE_BRIGHTDATA=1`). Includes: account integration shell, normalizer skeleton projecting Bright Data result shape into the same `linkedin_posts` columns the Apify normalizers populate, smoke test path. Active path remains Apify; activation in <30 min if R5 fires (env-var flip + smoke). — ~2d
- DB schema work per §5.2: NEW `draft_decisions` (with `platform` column) + NEW `linkedin_posts` + NEW `hand_drafts` + ALTER TABLE on existing v1 `angles` to add `source_text` column (PRAGMA-guarded for idempotency; embedded SCHEMA constant in `db.py:123-130` updated in lockstep). — ~0.5d

**Then 14 days X-dogfood:** JR runs v1 X cron daily, marks every X draft. Day-7 intermediate checkpoint (pillar diversity ≥4 + skip-reason distribution per §5.4 — filtered to `platform='x'`). Day-14 X verify: `xeng holdout-export` for x_engine produces ≥25 anchored fixtures, all skip rows have `skip_reason`. If <25 at day 14: pause, diagnose with JR.

**During the X-dogfood window:** JR can ALSO start running `xeng pull-linkedin-search` + `xeng pull-linkedin-user` on a one-shot or daily basis to populate `linkedin_posts` table. This is data prep for L2 (LinkedIn lane needs LinkedIn evidence in cache before agents can call `xeng top-linkedin`). Not a hard L1 gate, just useful prep work.

### 7.4 L2 — Seed cull + BOTH lane scaffolds + fixtures + first iterations + X parallel-run + LinkedIn bootstrap

**Coding work (~16-18 engineer-days; ~25-30 calendar-days with JR review latency):**
- Apply §3.1 cull to `x_engine/` (drop agentic + obsolete prompts/pipeline; collapse cli.py to ~17 subcommands; strip tests) — ~1.25d
- Author 12 prose blocks in `src/evaluation/rubrics.py`: 6 `_X_N` (X-1..X-6 mirroring `_GEO_1`..`_GEO_8` 1/3/5 anchor format) + 6 `_LI_N` (LI-1..LI-6 with platform-specific anchors per §4.4); update `assert len(RUBRICS) == N` (verify and bump by 12 per §4.2 row 3); X-6 + LI-6 both `is_cross_item=True`. **~5-7d** (Round-6 #16 honest re-estimate; was 2d in v8.2). Includes JR review cycle: prose-block draft → JR scores against reference posts → revise on flagged anchors → re-review. The F4 pre-L0 task pre-screens anchor *direction* but doesn't replace the iteration loop on prose-anchor *language*. — ~5-7d
- Per-lane authoring (×2): `programs/<lane>-session.md` (~100 lines) + `<lane>-evaluation-scope.yaml` (~10 lines) — ~2d total. (Round-6 #18: shared `voice.md` is L1 work by JR, not L2 per-lane authoring.)
- Per-lane workflows (×2): `workflows/<lane>.py` (~80 LOC WorkflowSpec — 11 fields per §4.3, including `name`/`config`/`config_dir_name` metadata) + `session_eval_<lane>.py` (~80 LOC SessionEvalSpec; LinkedIn structural_gate adds hashtag-count check) — ~4d total
- Drift-gate edits per §4.2 (rows 1-6 + 9; rows 7-8 already shipped at L0; row 1 also touches `eval_suites/SCHEMA.md` + `TAXONOMY.md` lane-domain enumeration) — ~0.75d
- Add fixtures to `eval_suites/search-v1.json`: `domains.x_engine[]` (5-10) AND `domains.linkedin_engine[]` (5-10) sourced from v1 `angles` table — ~0.75d
- Atomic-merge holdout fixtures into `~/.config/gofreddy/holdouts/holdout-v1.json` per §7.9 — `domains.x_engine[]` from L1 dogfood (≥25), `domains.linkedin_engine[]` from L1 cold-start (10 hand-written fixtures per §7.3) — ~0.25d
- First iterations per lane: `python3 -m autoresearch.evolve run --lane <lane> --iterations 1 --candidates 3` ×2 lanes — ~1d (mostly waiting; lanes run independently)
- First-runnable verification per §7.5 (both lanes) — ~0.75d
- Wire daily evolution cron for BOTH lanes (one LaunchAgent per lane, scheduled to avoid concurrent compute spikes) — ~0.5d

**Then operator-side calendar:**
- 7 days x_engine parallel-run + day-7 verdict per §3.5 + D6 (X-only; verdict requires BOTH JR-preference AND holdout-aggregate cross-check per Round-6 #15)
- Open-ended LinkedIn bootstrap (lane runs daily; JR marks; holdout grows from 10 cold-start + organic; first promotion verdict possible after ≥10 organic marks accumulate on top of cold-start, typically 2-4 weeks)

### 7.5 First-runnable acceptance criteria (both lanes)

Each lane has its own first-runnable check. Both must pass before L2 is considered shipped.

**Shared (both lanes):**

| Criterion | How to verify |
|---|---|
| Both LaneSpecs registered + drift gate + rubrics.py assertions | `python3 -c "from autoresearch.lane_registry import _assert_models_literal_matches; _assert_models_literal_matches(); import src.evaluation.rubrics"` exits 0 (`rubrics.py` import triggers `len(RUBRICS) == N+12` + lane-rubric-ids ⊆ RUBRICS + sum-equals-total; verify N at L0) |
| Both LANES present in WORKFLOW_SPECS + SESSION_EVAL_SPECS | `python3 -c "from archive.<seed>.workflows import WORKFLOW_SPECS; from archive.<seed>.workflows.session_eval_registry import SESSION_EVAL_SPECS; assert {'x_engine','linkedin_engine'} <= set(WORKFLOW_SPECS) and {'x_engine','linkedin_engine'} <= set(SESSION_EVAL_SPECS)"` exits 0 |
| v1 `angles` table extended with `source_text` | `sqlite3 state.db 'PRAGMA table_info(angles)' | grep source_text` non-empty |

**Per-lane (each row × 2 lanes):**

| Criterion | How to verify (substitute `<lane>` ∈ {`x_engine`, `linkedin_engine`}) |
|---|---|
| `evaluate_session.py` accepts the lane | `python3 archive/<seed>/scripts/evaluate_session.py --domain <lane> --help` exits 0 |
| Search-v1 has fixtures | `jq '.domains.<lane> \| length' eval_suites/search-v1.json` ≥ 5 |
| Holdout has anchored fixtures | x_engine: `jq '.domains.x_engine \| map(select(.anchor==true)) \| length'` ≥ 25; linkedin_engine: `jq '.domains.linkedin_engine \| map(select(.anchor==true)) \| length'` ≥ 10 (cold-start fixtures from L1 per §7.3; hard gate IF cold-start protocol ran. If cold-start was skipped per the §7.3 alternative: ≥0 acceptable) |
| Variant subprocess launches | `python3 archive/<seed>/run.py --domain <lane> jr <int_angle_id> 1 600` runs to completion |
| At least one draft.md produced + conforms to §2.2 shape (per platform) | `ls archive/<seed>/sessions/<lane>/jr/drafts/*.md` non-empty AND lane's structural_gate returns `[]` on it |
| In-session evaluator runs | `python3 archive/<seed>/scripts/evaluate_session.py --domain <lane> --artifact <draft.md> --session-dir <session>` exits 0 with non-empty per-criterion feedback |
| Judge service responds with criteria-aware scoring | `evaluate_variant.py` post to `/invoke/score` returns 200 with `aggregate_score` 0–10 AND per-criterion entries reference X-1..X-6 (or LI-1..LI-6 for linkedin_engine) — NOT hallucinated criteria names |
| End-to-end | `python3 -m autoresearch.evolve run --lane <lane> --iterations 1 --candidates 3` exits 0 with 3 scored variants |

Quality bar at first-runnable is "the plumbing works for both lanes" — NOT "drafts are great". Day-1 seed quality may be worse than v1 (X) and worse-than-hand-written (LinkedIn); that's by design. Evolution earns it back per lane.

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

Engineer-day lower-bound: L0 ~2d + L1 ~6.5d + 14d X-dogfood (calendar) + L2 ~16-18d + 7d X-parallel-run (calendar) = **~46-48d engineer-days + 21d operator calendar**. But engineer-days don't run back-to-back without JR review latency, so the realistic calendar is materially longer.

**Realistic calendar timeline: 8-10 weeks for full dual-lane validation** (Round-6 #19 honest re-estimate; was "7-8 weeks" in v8.2). Realistic factors:
- L1 ~6.5 engineer-days → ~10-12 calendar-days with JR review on `voice.md` substrate + `sources_linkedin.yaml` + L1 cold-start writing-block coordination
- L2 ~16-18 engineer-days → ~25-30 calendar-days because rubrics.py 12 prose blocks (~5-7 engineer-days) are the largest single line item and require multiple JR review passes; per-lane authoring + first-runnable surface 2-3 cross-lane debugging issues each requiring a half-day JR coordination round-trip
- L0 ~2 engineer-days → ~3-4 calendar-days if judge-service smoke needs server-side state update (escalation to JR)
- X parallel-run 7d may extend 7 more days if day-7 verdict trajectory is positive but not 3-of-7 + holdout-aggregate non-regressive (Round-6 #15 dual-gate)
- LinkedIn bootstrap: open-ended; first promotion-eligible cycle typically lands 4 weeks after L2 first-runnable (NOT 2 weeks); cold-start floor of 10 fixtures unblocks first promotion attempt earlier than v8.2's zero-baseline

X-dogfood (L1) remains the long single pole during L1. L0 runs first because the judge-service infra change is shared across all 6 lanes; the two-template approach contains blast radius (existing 4 lanes' prompts unchanged). LinkedIn bootstrap is the long *open-ended* pole post-L2 — adoption velocity depends on JR's marking discipline.

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

**Holdout merge at L2:** `xeng holdout-export` → snapshot existing manifest → `jq --argfile` to merge BOTH `domains.x_engine[]` AND `domains.linkedin_engine[]` (LinkedIn entry may be empty initially per §5.4) → atomic mv → verify all 6 lanes still keyed + x_engine ≥25 + other lanes unchanged. 5-bash-command operator procedure; details in operator memory.

**Kill rules** (operator memory; per lane): `launchctl unload` for that lane's cron; `evolve_ops rollback --lane <lane>` for variant rollback; comment-out lane's `LANES` entry + revert `models.py` Literal for full lane disable. Each lane disabled independently.

---

**End of master plan v9.**
