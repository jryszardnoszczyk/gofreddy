---
title: Audit pipeline implementation research (5 items — most already in R5)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-006-pipeline-overengineering-implementation-research.md
---

# Implementation research — 5 audit-pipeline simplifications (against R5 plan, 2026-04-22)

Plan under analysis: `docs/plans/2026-04-20-002-feat-automated-audit-pipeline-plan.md` (1529 lines, post-R5+R6).

Per-item status assessment against current plan text. Where R5 already applies the change, I note the residual gap (usually: decision documented in summary/architecture but not yet threaded into the Pydantic models, the prompt files, or the eval rubric). Where it is not applied, I design the fix.

---

## #7 — Opus-produced health score (instead of deterministic weighted rollup)

**Status in current R5 plan:** already-applied, with residual polish gaps. Lines 583–592 + 1118–1123 + 1238 + 1249 codify the move to Opus-produced health score with calibrated arithmetic anchor, and the template binds to `report.json:health_score` directly. The "9-lens weighted rollup" is explicitly retired (line 591: "No fixed per-section weights under R5").

**Summary:** Stage 3 runs one Opus call (`HEALTH_SCORE_PROMPT`) after sections + surprise critique land. Prompt carries an arithmetic anchor (start at 10, subtract 2 per severity=3, 1 per severity=2, 0.5 per severity=1, floor at 1) so same findings → same score modulo ≤±0.5 Opus variance. Deterministic Python rollup is gone; the Hero TL;DR binds to Opus output.

**Current state:** plan copy already specifies (lines 590–591):
- Shape: `{overall: 1-10, per_section: {9 sections}, signal_breakdown[], band: red|yellow|green, rationale}`.
- Arithmetic anchor lives inline in the prompt text.
- Per-section subscores are produced by the same arithmetic applied per `report_section` bucket.
- Band cutoffs: red 1–4, yellow 5–7, green 8–10.
- The Hero TL;DR template (line 1118) binds to `report.json:health_score` directly — radar via inline SVG, color classes bound to band.
- Cache-replay variance test spec already present (line 601): synthesis twice on same agent_outputs → ≤±0.5.

**Target state (gaps to close):**
1. Pydantic model for `HealthScore` is NOT yet in the plan — the shape is only in prose. Must be added to `src/audit/agent_models.py` alongside `Finding` + `AgentOutput`, and a top-level `AuditReport` that wraps everything.
2. `src/audit/prompts/health_score.md` is named in line 113 but the prompt body itself is not drafted — only described.
3. The arithmetic anchor has a copy bug: prose at line 590 says "Start at 10. Subtract 2 per critical" (scale 1–10), line 591 repeats same, but the 9-lens rationale paragraph earlier in the plan referenced a 0–100 scale. Plan needs one consistent scale call-out. Current R5 copy settles on **1–10**; keep that.
4. Rationale word cap: plan says "3-5 sentences"; production prompt should pin it at ~120 words max to render cleanly as a hero subtitle (template reads it as a subhead under the large numeral).

**Implementation approach:**
- **Option A (recommended):** Thin Pydantic model + directive prompt + post-call validator. Model shape exactly matches plan copy. Prompt is prose with the arithmetic anchor as a "Calibration checklist" section, followed by output JSON schema. Python validates ranges + band coherence (reject if band doesn't match overall: e.g. overall=6 but band="green") and re-asks Opus once on range violation before raising.
- **Option B:** LLM-as-judge with no arithmetic anchor. Rejected — drifts across prospects and breaks the "same findings in → same score out" invariant that plan asserts (line 590).

**Justification for A:** preserves the already-documented determinism target, keeps the Pydantic-first discipline used everywhere else in the audit, and the one-shot retry pattern is already used for `RubricCoverageIncomplete` (line 586). Zero new architectural primitives.

**Specific plan edits:**
- U1 `agent_models.py` list (line 118): append `HealthScore` model alongside `Finding` + `AgentOutput`:
  ```
  HealthScore: {overall: conint(ge=1, le=10), per_section: dict[Literal[9 sections], confloat(ge=1, le=10)],
                signal_breakdown: list[{section, findings_counted: int, arithmetic: str}],
                band: Literal["red","yellow","green"], rationale: constr(max_length=600)}
  ```
  Plus model-level validator: `band` must be `"red"` if `1 ≤ overall ≤ 4`, `"yellow"` if `5 ≤ overall ≤ 7`, `"green"` if `8 ≤ overall ≤ 10`.
- U5 (line 590) — change "3-5 sentences" to "3-5 sentences, ≤120 words" so template rendering is predictable.
- U5 approach step 6 — add one line: "On Pydantic validation failure, retry once with the error message appended to the prompt; on second failure raise `HealthScoreInvalid`."
- U5 test scenarios — add "Happy: HealthScore.band field matches overall via Pydantic validator" and "Edge: Opus returns overall=9 band='red' → retry fires; if still broken → raises."
- Draft the prompt body (`src/audit/prompts/health_score.md`) so it's not deferred to implementation; ~80 lines of markdown — inputs (findings list grouped by section), calibration arithmetic, rationale-writing guidance (3 bullets: which sections drove score, any systemic patterns, whether band is contested at boundary), output JSON contract.

**Dependencies:**
- Blocks: Hero TL;DR template partial (`_partials/hero.j2`) which already binds to `report.json:health_score`.
- Depends on: `Finding.severity` field being populated (already required per line 485); `Finding.report_section` enum populated (already required).

**Edge cases:**
1. All findings severity=0 (i.e. observations only) → arithmetic gives overall=10 green. Plan should note this is valid — a prospect with no real issues should score green, not be artificially suppressed.
2. One section has 0 findings (e.g. R23 attach-demo not granted → conversion thin) → `per_section["conversion"]=10.0` would misrepresent. Prompt must instruct: "If a section has 0 findings because no signal was gathered, omit from `per_section` and note in `rationale`."
3. `gap_flagged` rubrics do NOT count as findings and do NOT subtract from score. Prompt must call this out explicitly.
4. Opus returns `overall=4.3` (non-integer). Plan says 1–10 integer; Pydantic enforces `conint`. Allow Opus to produce float, round down Python-side to stay conservative (4.3 → 4 → red), or lift to `float` and re-band accordingly. Recommend: keep integer overall, float per_section.
5. Band boundary contests: overall=4.8 is "contested red/yellow." Anchor at integer + floor, rationale paragraph names it explicitly.

**Test strategy (tests/audit/test_synthesis.py + new test_health_score.py):**
- Unit: HealthScore model rejects band mismatch; retry fires on Pydantic error.
- Deterministic: same synthetic findings list → run health_score twice → overall identical, per_section within ±0.5.
- Fixture: dogfood prospect with known finding severity distribution → overall lands in expected band.
- Edge: all-zero-severity findings → green; all-critical findings → red with rationale naming top 3 sections.

**Rollout:** breaking for pre-R5 readers only if they were wiring `lens_weight_share` into a rollup function; plan already deleted that field. Plan version stays R5/R6.

**Estimated effort:** Plan edit 30 min. Implementation 4–6 hrs (model + prompt draft + retry + tests).

**Open questions:**
- Should `rationale` be explicitly Polish-styled for the Polish prospect base, or English-default with a locale flag? (JR decision, not for me.)
- Do we want a secondary "trending arrow" on Hero TL;DR (score vs. last audit of same prospect)? Out of v1 scope probably — no prior-audit lookup yet.

---

## #8 — Delete `rubric_themes.yaml` pivot; flat `report_section` enum on Finding

**Status in current R5 plan:** already-applied and thoroughly threaded. Lines 117–118 (`agent_models.py` rename, Finding carries `report_section: Literal[...]`), line 466 ("R5 2026-04-22: removed `rubric_themes.yaml` pivot table"), lines 480, 485, 515, 585 all specify flat-enum routing. No YAML pivot file exists in the plan's data catalog (line 132+).

**Summary:** Each Stage-2 agent's prompt names the rubrics it owns + the report_section each rubric maps to. Agent tags each Finding with `report_section: Literal[9 values]`. Stage 3 synthesis groups findings by that field directly.

**Current state (plan already specifies):**
- Enum values (line 485): `Literal["seo","geo","competitive","monitoring","conversion","distribution","lifecycle","martech_attribution","brand_narrative"]` — 9 values, flat.
- Stage 3 routing (line 585): "Groups all findings by `Finding.report_section` Literal enum directly — no pivot table, no rubric_themes.yaml mapping step."
- AgentOutput rubric coverage map (line 486, 516): `rubric_coverage: dict[str, Literal["covered","gap_flagged"]]` — required field; Stage 3 raises `RubricCoverageIncomplete` on missing keys.
- Agent → section mapping (lines 470–478 table): 7 agents produce the 9 sections; Findability splits SEO/GEO, Conversion-Lifecycle splits conversion/lifecycle — agent picks section per finding via the enum.

**Residual gaps to close:**
1. The 7 agent prompt markdown files (`agent_findability.md`, etc. — line 487) are NAMED but not drafted. Each needs its inline rubric-checklist block showing rubric_id → evaluation question → expected-finding-shape → `report_section` mapping.
2. No migration note for dev workstations that were on R3/R4 (pre-enum). Plan needs one line: "If a pre-R5 branch has `rubric_themes.yaml` or `lens_weight_share` field in `lens_models.py`, delete both — no data migration because no audit has shipped."
3. Pydantic rejection test not explicitly in plan — needs adding.

**Target state:** ship the 7 agent prompts with their rubric-checklist blocks fully written, each referencing the 9-value enum literal. Pydantic rejects invalid values at construction. Stage 3 groups by enum. Zero YAML pivot.

**Implementation approach:**
- **Recommended:** literal-typed Pydantic enum (as plan already says). No separate `Enum` class — just a `Literal[...]` type alias in `agent_models.py`:
  ```python
  ReportSection = Literal["seo", "geo", "competitive", "monitoring", "conversion",
                          "distribution", "lifecycle", "martech_attribution", "brand_narrative"]
  ```
  Pydantic v2 gives free validation, IDE autocomplete, JSON-schema export — no class hierarchy.
- Per-agent prompt rubric blocks (sample — Findability agent) live in `src/audit/prompts/agent_findability.md`:
  ```markdown
  ## Rubrics you MUST cover
  Emit ≥1 Finding per rubric, OR mark `gap_flagged` in rubric_coverage:
  - `tech_seo_health` → report_section="seo" — …
  - `link_authority` → report_section="seo" — …
  - `ai_search_visibility` → report_section="geo" — …
  - `international_local_accessibility` → report_section="seo" — …
  - `eeat_signals` → report_section="seo" — …
  - `ai_crawler_strategic_posture` → report_section="geo" — …
  ```

**Specific plan edits:**
- U4 Files (line 487) — change "Create 7 agent-specific prompts" to "Create 7 agent-specific prompts with inline rubric-checklist blocks (sample shown below); each rubric declares its `report_section` target." Then inline a ~15-line sample rubric block for ONE agent as a worked example (the other 6 follow the same pattern).
- Plan "Deferred to implementation" section (line 265-275) — add: "exact rubric_id strings per agent (7 × 5-10 strings) finalized at prompt-write time; plan sets the pattern, implementation fills strings from the coverage-reference catalog in U2."
- U4 test scenarios — add:
  - Pydantic rejects a Finding constructed with `report_section="onboarding"` (invalid) → ValidationError at construction, not at Stage 3 runtime.
  - Mocked AgentOutput with a Finding tagged `report_section="seo"` from the Conversion-Lifecycle agent is routed to the SEO bucket (agent-name does NOT gate section — Finding's own tag does). This is the whole point of the enum.
- One-line migration note in "Key decisions" section (line 237): "R5 deleted `rubric_themes.yaml` pivot and `lens_weight_share` field from `lens_models.py`. Pre-R5 branches: delete both; no data migration (no audit has shipped)."

**Dependencies:** unblocks #7 (HealthScore per_section keys must match the enum), #9 (Finding schema trim), #22 (critique runs per-rubric).

**Edge cases:**
1. Findability agent tags a Finding `report_section="competitive"` because the issue is competitor-relevant. Valid under enum but counterintuitive. Plan can either (a) let it through (current R5 stance — "soft routing decision, not a hard contract," per cluster-3-4 research doc) or (b) cross-check agent ownership at Stage 3 and warn. Recommend (a) — Opus synthesis re-narrates anyway.
2. A rubric maps to 2 sections (e.g. `audit_eeat_signals` feeds both SEO and GEO). Plan's current guidance: agent picks the section where the finding is *most actionable*; if truly cross-cutting, emit 2 findings (one per section). Spell this out in the shared `critique.md` prompt.
3. Agent emits 0 findings tagged for one of "its" sections (e.g. Findability emits only SEO findings, no GEO). Section renders as "no issues surfaced" placeholder (line 603) unless upstream agent flagged `not_applicable=true`. 
4. Spelling drift — agent emits `report_section="SEO"` (uppercase) or `"brand-narrative"` (hyphen). Pydantic rejects at construction. Good — catches the bug early.
5. Stage 3 gets 0 findings for a section that has `gap_flagged` rubrics only. Render: "We investigated X rubrics in this area but did not surface findings — possible evidence: [list of gap_flag reasons]." Explicit, not silent.

**Test strategy (tests/audit/test_agent_models.py):**
- Construction: valid enum accepted; invalid rejected.
- Routing: Stage 3 `_synthesize_sections()` groups a fixture of 20 findings across 4 agents into correct 9 buckets based on Finding.report_section only (ignores AgentOutput.agent_name for routing).
- Rubric coverage validation: AgentOutput with missing rubric_id raises `RubricCoverageIncomplete`.

**Rollout:** breaking only for anyone with `rubric_themes.yaml` or `lens_weight_share` still in their tree. Plan version unchanged (already R5).

**Estimated effort:** Plan edit 20 min. Implementation effort shifts to prompt-writing (covered under #22 critique work anyway).

**Open questions:**
- Should the 9 enum values be nouns (`"seo"`) or phrased as report-section titles (`"search_visibility"`)? Plan uses noun-aligned-to-lens-name. I'd keep it — it reads clean in code and template `{% if section == "seo" %}`.

---

## #9 — Trim Finding schema from 13 required fields to 6

**Status in current R5 plan:** already-applied (lines 485, 515). 6 required: `{id, title, evidence_urls[], recommendation, severity, confidence}` + required tagging field `report_section`. 6 optional: `{evidence_quotes[], reach, feasibility, effort_band, category_tags[], proposal_tier_mapping}`.

**Summary:** Agent is free to produce sparse findings — evidence URL list + one-line title + strategic recommendation + severity/confidence/section is the floor. Reach/feasibility/effort are nice-to-have but not blocking. Renderer handles missing optional fields via Jinja2 conditionals. Stage 3 ranking degrades gracefully when optional fields are missing. Stage 4 proposal back-fills `proposal_tier_mapping` regardless of whether agent populated it.

**Current state (plan specifies):**
- Exact required/optional split at line 485 + 515.
- Good-vs-bad `recommendation` examples in plan (line 515) — helpful calibration for agents.
- Plan line 593: "Stage 3 synthesis back-fills each Finding's `proposal_tier_mapping` field after Stage 4 generates the tier plan." So proposal_tier_mapping is always populated in the final render, agent's population is optional.
- Template `_partials/report_section.j2` (line 1136–1148): renders all finding fields, but no explicit `{% if field is defined %}` conditionals spelled out.

**Residual gaps to close:**
1. Pydantic model definition not fully shown in plan — only the field list. Must show required vs. Optional with defaults (`Optional[X] = None`, `list[X] = Field(default_factory=list)`).
2. Jinja2 template conditionals not explicit in plan. Line 1137 lists "evidence_quotes block (blockquote with cite-URL footer)" but doesn't say "only rendered if evidence_quotes is non-empty."
3. Stage 3 ranking algorithm when `reach`/`feasibility`/`effort_band` are missing — not specified. Current R5 plan uses Opus to narrate per section, so there's no deterministic ranking — but per-section ordering within a section still needs a rule.
4. Stage 4 proposal tier mapping back-fill logic is mentioned but not tested (line 593) — add test coverage.

**Target state:** Pydantic model + template conditionals + Stage 3 ordering rule + Stage 4 back-fill fully specified.

**Implementation approach:**
- **Recommended model (Pydantic v2):**
  ```python
  class Finding(BaseModel):
      id: str
      title: constr(min_length=5, max_length=120)
      severity: conint(ge=0, le=3)
      confidence: Literal["H", "M", "L"]
      evidence_urls: list[HttpUrl] = Field(min_length=1)  # at least 1 URL
      recommendation: constr(min_length=50)  # encodes "≥50 words" quality bar
      report_section: ReportSection
      # Optional
      evidence_quotes: list[str] = Field(default_factory=list)
      reach: Optional[conint(ge=0, le=3)] = None
      feasibility: Optional[conint(ge=0, le=3)] = None
      effort_band: Optional[Literal["S", "M", "L"]] = None
      category_tags: list[str] = Field(default_factory=list)
      proposal_tier_mapping: Optional[Literal["fix", "build", "run"]] = None
      agent: Optional[str] = None  # producing agent name, populated by Stage 2 writer
  ```
  `min_length=1` on `evidence_urls` and `min_length=50` on `recommendation` are quality floors — critique loop (#22) + eval harness (#9) catch regressions above that.
- **Renderer conditionals** in `_partials/report_section.j2`:
  ```jinja
  {% if finding.evidence_quotes %}
    <blockquote>…</blockquote>
  {% endif %}
  {% if finding.reach is not none and finding.feasibility is not none %}
    <span class="pill reach">R{{ finding.reach }}</span>
    <span class="pill feasibility">F{{ finding.feasibility }}</span>
  {% endif %}
  {% if finding.effort_band %}
    <span class="pill effort">{{ finding.effort_band }}</span>
  {% endif %}
  {% if finding.proposal_tier_mapping %}
    <span class="chip tier tier-{{ finding.proposal_tier_mapping }}">
      {{ {"fix": "Fix-it", "build": "Build-it", "run": "Run-it"}[finding.proposal_tier_mapping] }}
    </span>
  {% endif %}
  {% for tag in finding.category_tags %}<span class="chip muted">{{ tag }}</span>{% endfor %}
  ```
- **Stage 3 per-section ordering rule** (simple + robust to missing fields): sort findings within each report_section by `(severity desc, confidence_rank desc, has_reach desc, reach desc, title asc)` where `confidence_rank = {H:3, M:2, L:1}` and `has_reach = 1 if reach is not None else 0`. Findings without reach fall below findings with the same severity/confidence but with reach — mild pressure on agents to populate reach when they can, without forcing it.
- **Stage 4 back-fill logic** (already in plan at line 593): after proposal is generated, Stage 3 code iterates capability mappings and sets `finding.proposal_tier_mapping = capability.tier` for each finding a capability addresses. Findings not addressed by any capability keep `proposal_tier_mapping = None` and render without a tier chip (visible to reviewer as "not yet mapped" — a real signal for Stage 3 critique).

**Specific plan edits:**
- U4 approach (line 515) — append Pydantic model block as shown above so contract is unambiguous.
- U7 template (line 1136) — add the explicit `{% if … %}` conditional pattern for each optional field (as shown) so renderer work isn't deferred.
- U5 approach — add sorting rule explicit: "Within each report_section bucket, sort findings by `(severity desc, confidence_rank desc, has_reach desc, reach desc, title asc)`; optional fields missing → tie-break to title."
- U5 / U6 test scenarios — add:
  - Finding with minimum required fields only (no evidence_quotes, no reach, no tier_mapping) renders cleanly in HTML + PDF.
  - Stage 3 back-fill populates `proposal_tier_mapping` for findings addressed by proposal capabilities; leaves None for unaddressed.
- Risks section (line 1462) — already covers "6-required-fields Finding schema lowers the floor." Good; no edit needed.

**Dependencies:** unblocks #22 (critique reads `recommendation` field), depends on #8 (`report_section` enum).

**Edge cases:**
1. Agent emits Finding with empty `evidence_urls[]` — Pydantic rejects at construction. Good: evidence-free findings are noise.
2. Agent emits `recommendation` at 45 words (below 50 floor). Pydantic rejects. Critique loop (#22) should catch before construction, but floor is defensive.
3. Finding references a local file URL (`file:///...`) instead of `http://` — Pydantic `HttpUrl` rejects. Agent prompt must specify public URLs only. Add to `critique.md`.
4. Agent emits Finding with severity=3 but confidence="L" — valid by schema but semantically weak. Critique loop rejects. Keep schema permissive; enforce quality in critique.
5. Stage 3 back-fill: finding addresses 2 capabilities across 2 tiers (e.g. fix-it schema repair + run-it ongoing monitoring). Pick the lower tier (Fix-it) by default — the urgent action is fix-now, monitor-later is implied. Document rule in plan.

**Test strategy (tests/audit/test_agent_models.py + test_renderer.py):**
- Pydantic: minimum-field finding constructs; missing evidence_urls rejects; recommendation <50 chars rejects; invalid report_section rejects.
- Renderer: template renders minimum-field finding without blanks or broken HTML; full-field finding renders all pills/chips; PDF version passes WeasyPrint.
- Stage 3: ordering stable across runs with deterministic input; ties broken by title.
- Stage 4 back-fill: integration test feeds Stage 3 + Stage 4 and verifies proposal_tier_mapping populated post-synthesis.

**Rollout:** breaking for anyone still treating reach/feasibility as required. Plan already moved them to optional — no data migration because no audit has shipped.

**Estimated effort:** Plan edit 30 min. Implementation 2–3 hrs (model + template conditionals + sort rule + tests).

**Open questions:**
- Should `effort_band` be required for tier-mapped findings? (i.e. if `proposal_tier_mapping` is set, `effort_band` must be set too?) Leans yes — tier mapping implies we've thought about effort. Defer to JR after first 5 audits — premature constraint.
- Should we add a `severity_rationale: str` optional field so reviewers can audit why something got severity=3? Out of scope; critique handles via `evidence_urls` context.

---

## #11 — Cut ~30 Tier-2 primitive wrappers (keep ~25 Tier-1)

**Status in current R5 plan:** already-applied, MORE AGGRESSIVELY than the recommendation. Lines 328–376 restructure U2 from ~83 Python wrappers to **~2 local-only helpers + ~15 cache-backed SDK tool handlers + ~68 prompt-mention investigations**. The "Tier-1 vs Tier-2" split you're asking about has effectively been replaced by a **"owned-paid-provider vs free-public-API"** split, where free-public-API work moved entirely to agent prompt-mentions.

**Summary:** R5 preserves exactly the ~25 Tier-1 wrappers (owned DataForSEO/Cloro/CompetitiveAdService/monitoring adapters/GSC) as cache-backed SDK tool handlers under `src/audit/tools/`. The ~30+ Tier-2 checks (directory presence, marketplace listings, launch cadence, free tools, corporate responsibility, trust center, branded SERP/autosuggest, help-center docs, etc.) are reached by agents directly via WebFetch + `cli/scripts/fetch_api.sh` + URL patterns named in agent prompts. No Python wrapper exists for those 68 free-public-API sources.

**Current state (plan specifies):**
- Tier-1 wrappers (line 384, 332): DataForSEO (8 endpoints), Cloro.ai_visibility, CompetitiveAdService (Foreplay+Adyntel), 12 monitoring adapters (one tool dispatches to all), GSC conditional. ~15 cache-backed tool handlers in `src/audit/tools/` (R6 collapsed from 6 per-provider files into one `@cached_tool` decorator applied to allowlisted provider methods).
- Tier-2 (deleted as Python, moved to prompts): line 334 lists 68 free-public-API sources reached via WebFetch / shell fetcher — GitHub, Wikipedia/Lift Wing, SEC EDGAR, HuggingFace, Reddit OAuth, Product Hunt GraphQL, crt.sh, Firefox AMO, Atlassian Marketplace, MediaWiki, GDELT, Discord, Podchaser, APIs.guru, Mailinator, Mail-Tester, Mozilla HTTP Observatory, npm/PyPI, ATS public job boards, Wayback, Bluesky, axe-playwright. All via prompt-mention.
- Safety-bounded exceptions (line 335): 5 primitives (`audit_welcome_email_signup`, `audit_hiring_funnel_ux`, R23 `attach-demo`, R21 `attach-survey` PII, R22 `attach-assets` IP) keep Python wrappers via `scoped_tools.py` for capability restriction. Agent cannot bypass because the destructive capability is NOT in its toolbelt.
- Cache strategy (line 107, 385–386): `clients/<slug>/audit/cache/` per-audit; 24h TTL; key `f"{tool_name}_{sha256(json.dumps(args, sort_keys=True))[:12]}"`; `force=True` bypasses.
- Reference docs for agent-driven Tier-2 heuristics (line 491): 9 consolidated reference files at `src/audit/references/` — e.g. `findability-agent-references.md` carries "AI-crawler strategic posture (robots.txt allow vs block trajectory as future-citation-supply decision)." Agent reads these + `prompts/reference/fetch-api-patterns.md` (line 488 — single shared file for per-API auth/pace/pagination, not inlined × 7).
- Cost telemetry for agent WebFetch (line 1435, 1440): `PostToolUse` hook logs every tool call to `cost_log.jsonl` with `{tool_name, tool_input_hash, cumulative_cost_usd}`; per-agent token-spend alert fires at 3× rolling median (line 1435).

**Residual gaps to close:**
1. The "exact Tier-1 list" is spread across the data-provider inventory table (lines 162+) and U2.5 (line 384). Worth consolidating into a single "cache-backed SDK tool allowlist" block in U2.5 for clarity — currently readers must reconcile across sections.
2. "Agent reference docs live at `src/audit/references/<agent>-references.md`" is stated but the Tier-2 heuristic CHECKLISTS inside those files are described in prose — not drafted. For ship-quality, each reference file needs a per-rubric checklist block (same pattern as #22 critique needs).
3. Cost-tracking for agent-driven WebFetch: Anthropic Claude Agent SDK reports WebFetch as part of total tokens, not as a separate line item. The `cost_log.jsonl` row captures it but the per-source cost breakdown (GitHub vs Wikipedia vs crt.sh) is invisible. Acceptable for v1 — rolled into the agent's total. No gap, just worth documenting explicitly.

**Target state:** consolidated Tier-1 allowlist block in U2.5 + Tier-2 heuristic checklists drafted in the 9 reference files.

**Implementation approach:**
- **Recommended:** in U2.5, add a concrete allowlist block:
  ```
  Tier-1 cache-backed SDK tool handlers (~15, in register_audit_tools()):
  - dataforseo.{on_page, backlinks, historical_rank, keyword_gaps, serp_features, business_data_gbp, local_pack, serp_site_query}
  - cloro.ai_visibility
  - competitive.ads  (via CompetitiveAdService — Foreplay + Adyntel)
  - monitoring.{voc, press, podcasts, google_trends}  (dispatches to 12 adapters internally)
  - gsc.{search_analytics, url_inspection}  (conditional on state.enrichments.gsc.attached)
  ```
  Rationale per tool: paid-API or rate-limited, benefits from hash-dedup cache, benefits from eval-harness fixture substrate.
- **Tier-2 agent heuristics** live in the 9 `references/<agent>-references.md` files. Example slice for Findability:
  ```markdown
  ## Tier-2 investigations (agent-driven via WebFetch)
  - **EEAT signal audit** — probe /about, /team, /author/<slug> pages; look for Person schema, bios ≥100 words, credential links. Gap_flag if <50% of published authors have bios.
  - **AI crawler strategic posture** — fetch /robots.txt; grep for GPTBot, ClaudeBot, CCBot, PerplexityBot, Google-Extended, anthropic-ai (see ai_crawler_user_agents.yaml). Classify: allow-all / allow-some / block-all / silent.
  - **Help-center docs SEO** — probe /help, /docs, /support, /knowledge-base; detect Algolia DocSearch via HTML `<script>` tags. Evaluate doc count + last-update recency via sitemap.
  ```
  ~3–8 checklist items per agent × 7 agents = ~30-50 checklist items total. Replaces ~30 Python Tier-2 wrappers.
- **Caching for Tier-2 agent-driven calls:** R5 plan does NOT extend the `cache/` dir to WebFetch responses — only to cache-backed SDK tool handlers. Intentional: WebFetch responses can be captured by Claude Agent SDK's built-in transcript archive (PreCompact hook), re-readable via session resume. Per-run freshness. No persistent WebFetch cache directory across audits. For eval harness (U9), the `fixture_proxy.py` pattern (line 1333) monkey-patches WebFetch to return frozen responses from `src/audit/eval/fixtures/<slug>/webfetch/<url_hash>.json` — that's the eval substrate, not a production cache.
- **Cost telemetry for agent WebFetch:** already handled via PostToolUse telemetry + agent-total cost reported by ResultMessage + 3× rolling median alert. No new code needed.

**Specific plan edits:**
- U2.5 (line 379) — insert the allowlist block above right after "Files:" list so the 15 is concrete, not inferred.
- U4 Files (line 491–494) — append one bullet: "Each reference file contains a **Tier-2 investigations** section with a rubric-keyed checklist (URL patterns, pass/fail criteria, gap_flag conditions); 3-8 items per agent."
- U2.5 approach (line 391+) — clarify: "WebFetch responses for agent-driven Tier-2 calls are NOT cached in `clients/<slug>/audit/cache/`. Per-run freshness is intentional. Eval harness freezes WebFetch via fixture_proxy (U9)."
- Risks — confirm line 1458 ("cache-staleness") already covers Tier-1 cache staleness; no edit needed.

**Dependencies:** unblocks #22 (critique reads the reference-doc checklists to calibrate), depends on data-provider inventory staying stable (already locked by R5).

**Edge cases:**
1. Agent re-invents a Tier-2 check differently on each run → reproducibility drops. Plan accepts this (line 1459 risk mitigation: eval-harness coverage metric catches regressions). Reference-doc checklists reduce variance without forcing determinism.
2. Agent misses a check that a Python wrapper would have done unconditionally. Mitigation: `AgentOutput.rubric_coverage` enforcement (Stage 3 raises on missing keys); eval harness coverage metric flags missed rubrics before merge.
3. A Tier-2 source (e.g. Product Hunt GraphQL) starts rate-limiting. Agent gets 429; `fetch_api.sh` retries with backoff; if exhausted, agent emits `gap_flag`. Visible in `gap_report.md` at publish gate.
4. A source moves from free to paid (e.g. Reddit in 2023 — R5 plan already flags this: line 1511 requires OAuth env vars for Reddit). When that happens: add env-var check to agent prompt; if missing → gap_flag with "configure REDDIT_CLIENT_ID/SECRET" reason.
5. ToS clauses on Tier-2 sources (e.g. Product Hunt commercial-use gray area, line 1503). Documented in risks. Per-source, not per-code.

**Test strategy (tests/audit/test_tier_split.py):**
- Unit: `register_audit_tools()` returns exactly the 15 allowlisted tool handlers (asserts allowlist intent).
- Unit: each reference doc has ≥3 Tier-2 checklist items per agent role (prevents drift to empty checklists).
- Integration (in eval harness): agent run on a dogfood prospect probes ≥80% of Tier-2 checklist items via WebFetch (visible in PostToolUse telemetry); remaining 20% tolerated as prospect-specific gap_flags.
- Cost: aggregate agent-driven WebFetch tokens logged in cost_log.jsonl; per-audit Tier-2 cost rolls into agent total (acceptance: cost per Tier-2 rubric <$0.10 at steady state).

**Rollout:** breaking for anyone expecting `primitives.audit_directory_presence(url)` Python call. Plan already deleted this (line 363 — "deleted ~190 lines of per-primitive Python function signatures"). Plan version R5.

**Estimated effort:** Plan edit 45 min (allowlist block + reference-doc pattern). Implementation ~1 day to draft the 7 reference-doc Tier-2 checklists (~30-50 items total) — overlaps with #22 work.

**Open questions:**
- Does the WebFetch cost at 20 audits/mo × ~30 Tier-2 probes × ~500 tokens/probe = ~300K tokens/mo materially raise Stage 2 cost? Plan's #risks line 1460 flags 2-5× pre-R5 token spend — calibration cost tracking during first 5 audits confirms or forces rethink.
- When does a Tier-2 check graduate back to Tier-1? (i.e. if GitHub adds rate-limit enforcement that forces structured caching.) Rule: if the source moves to paid API OR agent emits the same `gap_flag` >3 audits in a row due to rate-limit, promote to cache-backed SDK tool. JR decision on trigger.

---

## #22 — Critique pass on `Finding.recommendation` to enforce "strategic, not tactical"

**Status in current R5 plan:** partially-applied. Per-agent evaluator-optimizer critique loop is already wired at U4 (lines 483, 489–490, 518): initial → critique → optional revision, capped at 3 iterations, using shared `critique.md` + `revision.md` prompts. A Stage-3-level synthesis critique is also wired (line 589 — `SURPRISE_QUALITY_CHECK_PROMPT` evaluator-optimizer pattern for surprises). What's NOT fully specified: **the critique prompt's tactical-vs-strategic criteria**, the concrete examples, and how per-finding critique results flow back.

**Summary:** Extend the existing per-agent critique loop (already wired) with an explicit "strategic, not tactical" rubric in the shared `critique.md` prompt. The critique runs per-agent (not per-finding individually); revises or retains the findings list as a whole. Budget: 0 new Opus calls per audit vs R5 baseline (critique pass is already counted in the ≤3-iteration loop). Concrete examples from plan line 515 are the seed.

**Current state (plan specifies):**
- Per-agent critique loop at Stage 2 (line 490 pseudocode): `output = sonnet_call(initial); critique = sonnet_call(critique_prompt, context=output); if critique.passes: return; else: output = sonnet_call(revision_prompt, context=output + critique); [up to 3 total]`.
- Critique prompt directive (line 518): "reject findings with tactical recommendations, weak evidence, severity/confidence mismatched to evidence, <50-word substance; verify every rubric is `covered` or `gap_flagged`."
- Strategic-vs-tactical examples in plan (line 515):
  - Good: *"Enterprise landing pages lack schema coverage, suppressing rich-result eligibility for 8 of 10 tracked enterprise queries."*
  - Bad (too tactical): *"Add Organization, Product, and FAQ schema with these JSON-LD snippets to /enterprise/."*
- Agent can refuse to revise (Line 518 + 1452 "no auto-override of agent output"): "if critique passes, ship; if critique flags issues, one revision pass, then ship (passes or not)." Agent revises once; second critique is informational, not forcing.
- Cost model: critique + revision = 2 extra Sonnet calls per agent × 7 agents = 14 extra Sonnet calls per audit (NOT 36-72 Opus; it's Sonnet, scoped per-agent, and critique+revision together cap at 2 extra calls). Worst case all 7 agents hit max 3 iterations = 7×3 = 21 Sonnet calls total vs. 7 baseline — 3× Stage 2 cost ceiling. Plan already accounts for this (risks line 1460 "token spend 2-5× pre-R5").

**Residual gaps to close:**
1. The shared `critique.md` and `revision.md` prompts (line 489) are NAMED but not drafted. Contents must specify:
   - The tactical-vs-strategic rubric with 3-5 worked examples.
   - The `<50-word substance` floor.
   - The severity/confidence/evidence consistency check.
   - Exit conditions (when critique "passes").
2. Decision: should critique fire at Stage 3 synthesis too (cross-agent)? Plan currently fires it only per-agent at Stage 2. Surprises get a separate quality-check pass at Stage 3 (line 589). Cross-agent recommendation critique is NOT wired — if findings bleed into tactical across different agents it's not caught. **Recommendation:** add a lightweight Stage-3 sweep as a secondary pass, bounded to 1 extra Opus call.
3. Test fixtures for the critique (known-tactical findings that should trigger revision) not yet specified.

**Target state:** draft `critique.md` + `revision.md` with explicit tactical-vs-strategic rubric + worked examples + 50-word floor + severity/confidence consistency check. Add optional Stage-3 cross-agent sweep. Eval harness has known-tactical fixtures.

**Implementation approach:**
- **Recommended — fire critique PER-AGENT only at Stage 2 (already wired), WITH a Stage-3 synthesis-level sweep:**
  - Per-agent critique (Stage 2): already budgeted. Draft the `critique.md` prompt to include the 4-criterion rubric:
    1. **Strategic, not tactical** — recommendation describes what to solve, not how. Reject DIY execution detail.
    2. **Evidence-grounded** — ≥1 evidence_url per finding; quotes where applicable; severity/confidence consistent with evidence strength.
    3. **Substance floor** — ≥50 words in recommendation; not boilerplate.
    4. **Rubric coverage** — every rubric in agent checklist is `covered` or `gap_flagged`; no silent skips.
  - Stage-3 sweep (1 extra Opus call, adds to synthesis stage): after all 7 agent outputs merge into section buckets, run `recommendation_critique_sweep.md` over the full findings list. Opus reads the consolidated list, flags any cross-agent tactical leakage or duplication, returns `{findings_flagged: [finding_id], critique: str}`. Synthesis re-reads flagged findings and either revises inline or annotates with `quality_warning=true` (same pattern as surprise critique, line 589).
- **Option B (rejected): per-finding critique loop.** 36-72 extra Opus calls (one per finding). Expensive, duplicates evidence the agent already has, redundant vs per-agent critique. Rejected.
- **Tactical-vs-strategic concrete examples** (draft for `critique.md`):
  - REJECT: *"Add `rel='canonical'` to /blog/<post>, update sitemap.xml to include lastmod, rebuild schema.org markup with FAQPage + BreadcrumbList."* → tactical; that's engagement work.
  - REJECT: *"Write 4 blog posts per month on topic X, Y, Z."* → tactical prescription.
  - ACCEPT: *"Blog coverage is concentrated in TOFU awareness content (22 of 28 posts); no BOFU or product-differentiated content to support late-funnel SEO intent. A content rebalancing engagement could close the gap, estimated at Build-it tier scope."* → strategic framing + engagement-tier mapping.
  - ACCEPT: *"Meta ad creative runs 120 days with declining CTR (evidenced by Foreplay running_duration + ad fatigue benchmarks); creative refresh is overdue. Run-it tier retainer handles the ongoing cadence."* → strategic + evidence-grounded + tier-mapped.
- **Refusal to revise:** critique prompt returns a structured response `{passes: bool, criticism: str, proposed_revisions: list[{finding_id, suggested_reframing}]}`. Revision prompt passes criticism + proposed_revisions back to agent, which decides per-finding whether to accept, partially accept, or keep as-is with `quality_warning=true`. No forced override (plan line 1452 — preserves agent autonomy).

**Specific plan edits:**
- U4 Files (line 489) — append: "Draft both markdown files with the 4-criterion rubric inline + 3-5 worked examples contrasting strategic vs. tactical framing (seeded from U4 approach line 515)."
- U5 approach (line 589 area) — add step 5b: "Cross-agent recommendation critique sweep — one Opus call reads the merged findings list and flags tactical leakage across agent boundaries; synthesis re-narrates or annotates flagged findings."
- U5 prompts (line 580) — add `recommendation_critique_sweep.md` to the markdown prompts list.
- U4 test scenarios — add:
  - Fixture: agent produces findings with tactical recommendations → critique loop fires revision → findings become strategic. `critique_iterations_used=2` logged.
  - Fixture: agent produces thin <50-word recommendations → critique rejects → revision produces ≥50-word recommendations.
  - Edge: agent refuses to revise → findings ship with `quality_warning=true`; JR reviews at publish gate.
- U5 test scenarios — add: cross-agent critique sweep flags a tactical finding from one agent; synthesis annotates; rendered template shows the annotation muted.
- Risks (line 1462) — already covers "finding-depth variance" with critique mitigation. Good; no edit needed.

**Dependencies:** depends on #9 (Finding schema with `recommendation` field), feeds #7 (health score counts findings post-critique, not pre).

**Edge cases:**
1. Agent produces a finding that's BOTH strategic AND includes a snippet for the reviewer's convenience. Critique rubric must distinguish "audit deliverable" from "reviewer's internal notes." Rule: `recommendation` field is deliverable-facing; snippets go in `evidence_quotes` or `category_tags`, not recommendation.
2. Critique rejects every finding (critique hallucinates or prompt is broken). Loop caps at 3 iterations — agent ships findings as-is with warning. `critique_iterations_used=3` logged; JR reviews in calibration mode.
3. Critique passes all findings on iteration 1 — normal case, `critique_iterations_used=1`, no wasted cost.
4. Some findings are genuinely mixed (strategic framing + one tactical sentence). Critique returns `partial_accept` with specific sentence flagged. Revision agent surgically rewrites that sentence.
5. Cross-agent sweep flags a finding that the per-agent critique already passed. Reviewer-signal: this is the value of the sweep — catches cross-boundary issues per-agent critique can't see. No conflict; synthesis re-narrates.

**Test strategy (tests/audit/test_critique_loop.py):**
- Unit: shared critique prompt applied to a fixture of 5 tactical findings → all 5 flagged; applied to 5 strategic findings → all 5 passed.
- Integration: Stage 2 agent pipeline with tactical fixture → revision fires → final output has `critique_iterations_used=2` and findings pass critique.
- Eval harness: track `tactical_flag_rate` per agent per run; regression gates: if tactical_flag_rate climbs >20% on a prompt change, block merge.
- Cost: average critique_iterations_used across audits ≤1.5 (most findings strong first-pass); alert if >2.0 at steady state.

**Rollout:** additive; no breaking changes. Plan version stays R5.

**Estimated effort:** Plan edit 45 min (critique + revision prompt drafts pointed to + Stage 3 sweep spec). Implementation 1 day (prompts drafted + `agent_runner.run_agent` loop + Stage 3 sweep + tests + fixtures).

**Open questions:**
- Should `quality_warning=true` findings be visually distinct in the deliverable (e.g. muted pill "reviewer note")? Plan does this for surprises (line 1156); same treatment for findings seems right — but that's a JR editorial-signal call.
- Does the Stage-3 cross-agent sweep justify a second revision pass (i.e. sweep flags → revise → re-sweep)? Current proposal caps at one sweep iteration. If first 5 audits show systemic tactical leakage, add a second pass.
- Does critique cost ever exceed the 3× rolling median alert threshold (line 1435) because of the extra Sonnet calls? Need to calibrate — the alert is per-agent cumulative, so a 3-iteration-all-agents audit will inflate per-agent cost by ~3×. Either tune the alert threshold post-calibration or accept that critique-heavy audits surface as "review me" signals (arguably the right semantic).
