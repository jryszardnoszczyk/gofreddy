---
title: Audit pipeline rubric + primitives deep research (F3.1-F3.4, F4.1-F4.3)
type: research
status: active
date: 2026-04-22
parent: 2026-04-22-004-pipeline-overengineering-deep-research.md
---

# Deep research: GoFreddy audit-pipeline plan, 7 over-engineering findings

## Executive summary

Of the 7 audit-plan findings, my read is **2 KEEP**, **3 SIMPLIFY**, **1 REDESIGN**, **1 DELETE**. The most consequential moves, in order:

1. **F3.2 DELETE** the `rubric_themes.yaml` pivot table. It's the load-bearing piece of structural ontology that makes all the other rubric/section machinery feel necessary. Pull it out and F3.1, F3.3, F3.4 all collapse with it.
2. **F3.1 SIMPLIFY** `gofreddy_health_score` to a synthesis-Opus output, not a deterministic Python rollup. The plan's own risk section says it's "directional, not strict benchmark, re-tuned after first 10 audits" — that's an admission that the determinism is theatrical.
3. **F3.3 SIMPLIFY** the Finding schema from 13 required fields to ~5 required + the rest optional. Most of the 13 only exist to feed the rollup or the pivot.
4. **F4.2 SIMPLIFY** the R18-R26 enrichments — ship 3 of 9 on day 1, defer the rest behind real demand evidence.
5. **F4.1 REDESIGN** primitives split — keep ~25 paid-API wrappers (Tier 1), give Stage 1b agent WebFetch + heuristics for the cheap web-check Tier-2s.
6. **F4.3 KEEP** the Stripe `payment_events` table — it's correctly-sized for the problem.
7. **F3.4 KEEP** the agent↔section decoupling concept (different from the pivot file) — but only because it survives F3.2's deletion as a one-line rule, not as machinery.

The unifying observation: the plan's `rubric_themes.yaml` is the *integration point* between three otherwise-independent decisions (score, schema fields, agent/section split). Pulling it removes the gravity that justifies the other complexity. Everything else is downstream.

---

## F3.1 — `gofreddy_health_score` deterministic weighted rollup

**Today (planned):** Stage 3 computes a 0-100 health score in deterministic Python after all LLM calls finish. Each of 9 lenses gets a fixed top-level weight (SEO 17%, brand/narrative 21%, GEO 9%, etc.); each lens rolls up its rubrics' `lens_weight_share` × per-primitive scores from `signal_breakdown`. Returns `{overall, per_lens, signal_breakdown, band: red|yellow|green}`. The Hero TL;DR template (lines 1294-1301, 1415) renders it as a giant Tailwind `text-9xl` numeral plus a 9-axis radar.

**Why it exists:** Two reasons in the plan. (a) Marketing-intuitive shareability — "the metric prospects will screenshot and share internally" (line 1415); patterned on Ahrefs / SEMrush Site Health which prospects already recognize. (b) Anchors the per-lens narrative — gives the deliverable a load-bearing visual hook above the fold.

**What's wrong:** Three failure modes visible in the spec.

1. **The weights are admitted-arbitrary.** Plan line 771: weights "deferred to implementation and re-tuned after first 10 audits." The risk section (line 1638) explicitly calls this out: "directional, not strict benchmark... weights are re-tuned after first 10 audits based on what predicts engagement close." If the weights aren't truth, the determinism isn't truth — it's procedural theater that *looks* objective.
2. **The rollup formula is enormous and fragile.** Line 771 specifies a flat sum with ~120+ named signals across 9 lenses. Every new primitive (and there are 80+) needs a weight assignment. The R2 expansion paragraph alone mentions 30+ new score contributions ("EEAT signals + crawl-budget-bloat + footer optimization + conversational-query optimization..."). This grows monotonically; nothing prunes it.
3. **The score recovers from nothing.** If Stage 1b doesn't run a primitive, that signal is missing — what does the rollup do? Plan doesn't say. The deterministic rollup creates a false-precision bug surface where a 73 is sometimes "we measured all 120 signals" and sometimes "we measured 40 and the missing 80 defaulted to neutral."

**The right model — agentic / hybrid / deterministic:** **Hybrid, but Opus-led.** The synthesis Opus call already reads every Finding from every agent and writes the per-section narrative. It is the only entity that knows what was actually measured, with what evidence quality, and what's load-bearing for *this* prospect. Have it emit `{overall: int, per_lens: {<9>: int}, band: str, rationale: str}` as a JSON block in its output contract. Python validates ranges + maps band; nothing else.

**Concrete redesign:**
1. Drop the deterministic rollup function and the entire `signal_breakdown` field.
2. Add to `SYNTHESIS_MASTER_PROMPT` output contract: `gofreddy_health_score: { overall: 0-100, per_lens: {...}, band: red|yellow|green, rationale_120w: str }`.
3. Pydantic validates shape; Python derives band deterministically from `overall` (the one piece worth keeping deterministic — band thresholds are a brand decision, not an estimate).
4. Hero TL;DR template unchanged — same `{{ health_score.overall }}`, same color band, same radar from `per_lens`.
5. The "About This Audit" block already disclaims the score's directionality (line 1638 risk acknowledgement); add one sentence in the deliverable: "Score reflects the synthesis agent's holistic read of the findings; not a sum of subscores."

**Complexity removed:** The ~200-LOC weight specification paragraph at line 770-771 collapses to ~10 lines of prompt instructions. The `signal_breakdown` field disappears from `report.json`. The "weights re-tuned after first 10 audits" calibration burden disappears. The `lens_weight_share` field on every rubric (~40 entries) becomes irrelevant — which is half the justification for the rubric YAML existing at all.

**New risks:** (a) Score becomes less reproducible across re-runs of the same prospect — Opus may emit 71 vs 74. Acceptable for a "directional" number; the plan already accepts Stage 1b nondeterminism on the same grounds (line 1627). (b) Opus may anchor too high or too low without weights as scaffolding — mitigation is to feed it the band thresholds in the prompt and a one-shot example of a calibrated audit. (c) Eval harness (U9) needs a rubric criterion for "score consistency on rerun"; cheap to add.

**Verdict:** **SIMPLIFY.** Keep the score's role in the deliverable; replace the rollup machinery with synthesis-Opus output.

---

## F3.2 — `rubric_themes.yaml` pivot table

**Today (planned):** ~40 rubrics in a YAML file. Each rubric maps `id → agent → report_section → primitives[] → lens_weight_share`. Loaded with sum-to-1.0 validation per report section at module load. Drives three things: (a) Stage-2 prompt assembly (which rubrics each agent owns); (b) Stage-3 narrative routing (which findings go in which report section); (c) F3.1 health-score rollup weights. Three-way pivot.

**Why it exists:** The plan explicitly says (line 256, line 700) it "decouples 7 Stage-2 agent work-units from 9-section report narrative." 7 ≠ 9 because Findability merges SEO+GEO and Conversion-Lifecycle merges Conversion+Lifecycle. The pivot is the bookkeeping layer that lets agents emit findings tagged by `rubric_theme` and have them route correctly.

**What's wrong:** Four problems.

1. **The 7-vs-9 mismatch is a 4-line rule, not a YAML schema.** The actual splits are: Findability findings go to SEO or GEO (one bit per finding); Conversion-Lifecycle findings go to Conversion or Lifecycle (one bit per finding). That's a `report_section: enum[seo,geo,conversion,lifecycle,...]` field on the Finding, set by the agent at write time. No pivot needed.
2. **Per-section validation `sum=1.0` is meaningless if F3.1 simplifies.** The lens_weight_share field exists *only* to feed the rollup. If the rollup goes synthesis-Opus, this field has no consumer.
3. **40 rubric themes is more taxonomy than the agents need to think.** The Stage-2 prompts are described as "rubric-themed: walks the agent through the rubric themes it owns" (line 705). But the agents already have full `signals.json`, the primitive set, and the agent-specific reference doc. Adding "your rubrics are these 6, with these primitives, and this evaluation question" is over-specification of an already-instructed-enough agent.
4. **Sum-to-1.0 validation at load is brittle.** Every primitive add or rubric tweak risks breaking the sum. R2 expansion (line 771) lists 30+ new signals dropped into existing rubrics — keeping the math summing to 1.0 across this churn is an ongoing maintenance tax with zero customer-visible benefit.

**The right model — agentic / hybrid / deterministic:** **Deterministic, but minimal.** Replace the YAML with a flat `report_section: Literal[<9 values>]` field on `Finding`. Agent picks one when emitting. Stage 3 groups by that field. No pivot, no weight share, no validation.

**Concrete redesign:**
1. Delete `src/audit/rubric_themes.yaml`, `rubric_themes.py`, the `rubric_theme` field on Finding.
2. Each Stage-2 agent's system prompt names: (a) which report sections you contribute to (e.g., Findability: "SEO and GEO"), (b) which primitives feed you, (c) which reference doc to read. Agent picks `report_section` per finding.
3. Stage 3 groups findings by `Finding.report_section` directly (already in plan, line 767).
4. Cross-cut primitives feeding multiple agents stays in `signals.json` (line 640) — that's a load pattern, not a routing pattern, and the YAML pivot wasn't needed for it.

**Complexity removed:** Plan lines 644-697 (~55 lines), 736-745, the `rubric_themes.py` loader, the `rubric_theme` Finding field, the `lens_weight_share` per-rubric field, the sum-to-1.0 validation logic, and ~5-10 lines of prompt-assembly machinery per agent. The 9 reference files don't need to align to rubrics — they already align to agents. Net: ~80-100 plan lines + 1 module + ~150 LOC of code disappear.

**New risks:** (a) Two findings from different agents could hit the same report section with overlap (e.g., Findability and Brand/Narrative both flag EEAT). Mitigation: synthesis Opus call already merges per-section; deduplication is its job. The pivot didn't prevent overlap either. (b) An agent might mis-tag `report_section`. Pydantic enum validation catches the typo class; a wrong-but-valid choice (e.g., Findability tags SEO when it meant GEO) is the same risk the pivot has — agent has to pick a `rubric_theme` correctly there too.

**Verdict:** **DELETE.** The pivot is structural ontology that exists to support score weights and agent-section decoupling — both of which can be done flatter.

---

## F3.3 — `Finding` schema with 13 required fields

**Today (planned):** `{id, agent, rubric_theme, report_section, title, severity(0-3), reach(0-3), feasibility(0-3), evidence_urls[], evidence_quotes[], recommendation, proposal_tier_mapping, effort_band(S/M/L), confidence(H/M/L), category_tags[]}`. All 13 required (line 702). Pydantic enforces.

**Why it exists:** Two reasons. (a) The plan's "Envelope schemas, not content schemas" decision (line 277) — the envelope describes the shape downstream code consumes. (b) Specific consumers: `severity/reach/feasibility` for ranking (Stage 3), `proposal_tier_mapping` for the Recommended Next Steps section, `evidence_urls/quotes` for citation rendering, `effort_band` for proposal sizing, `category_tags` for filtering, `rubric_theme` for routing.

**What's wrong:** Three problems.

1. **Per Anthropic's directive-prompts guidance** (which the plan author cites at line 273), envelope schemas should constrain *shape*, not *content*. But severity, reach, feasibility, effort_band, confidence are all content judgments dressed as shape. Each forces the agent to commit a numeric/categorical assessment for *every* finding regardless of whether the agent has confident grounds. The harness Finding (per the audit context) uses 8 fields and is working; autoresearch uses looser markdown sections. The 13-field schema is the over-engineered outlier.
2. **`rubric_theme` and `report_section` collapse if F3.2 lands.** That's -2 fields immediately, and `agent` becomes derivable from session context (the orchestrator knows which agent emitted which finding) — -3 with no thought.
3. **`proposal_tier_mapping` is back-filled in Stage 3** (line 773) "after Stage 4 generates the tier plan." So at write time it's `null` and Pydantic-required-with-null-allowed is just decorative — the field is structurally optional. Same for `effort_band` and `category_tags` which are agent-discretion judgments that don't gate any downstream behavior; they only render as muted chips (line 1321).

**The right model — agentic / hybrid / deterministic:** **Hybrid, with a thin envelope.** Required = anything the deliverable cannot render without. Optional = anything the agent might or might not have grounds for. Severity is the ranking key; everything else is decoration or post-hoc.

**Concrete redesign:**
1. Required: `{id, title, severity(0-3), evidence_urls[], recommendation, report_section}`. (6 fields.)
2. Optional: `{evidence_quotes[], confidence(H/M/L), reach(0-3), feasibility(0-3), effort_band, category_tags[], proposal_tier_mapping}`. Default to `None` / `[]`.
3. Drop `rubric_theme` (gone with F3.2). Drop `agent` (the orchestrator records this in `state.sessions`, not on the finding itself — denormalized data is a bug magnet).
4. Renderer (line 1313-1321) handles `None` gracefully: render the pill if present, skip if not. PR-grade Jinja2 conditionals, not new ontology.
5. Stage 3 ranking uses `severity` desc, `confidence` desc when present, stable order otherwise. Plan currently uses an implicit composite of severity/reach/feasibility — formalize it as `sort_key = severity` and let the synthesis prose tell the rest.

**Complexity removed:** ~30% of Pydantic validation logic. The "agent decided X for severity but couldn't honestly score reach" failure mode (where the agent either lies or fails the schema). The proposal-tier back-fill dance becomes optional-field-set, which is what it always was semantically.

**New risks:** (a) Some agents will skip optional fields more aggressively than others — inconsistent rendering. Mitigation: prompt encourages filling them when honest; eval harness monitors fill rate per agent. (b) Synthesis Opus may want reach/feasibility to do better triage. Mitigation: keep them as recommended-but-optional; agent fills them when grounded.

**Verdict:** **SIMPLIFY.** Keep envelope discipline; demote 7 of 13 fields to optional.

---

## F3.4 — 9-section report decoupled from 7-agent execution via rubric pivot

**Today (planned):** 7 agents each produce findings tagged with `rubric_theme`; pivot routes to one of 9 report sections. Findability merges SEO+GEO (shared EEAT/robots/schema); Conversion-Lifecycle merges Conversion+Lifecycle (shared funnel signals).

**Why it exists:** Cohesion. Plan line 256 + line 630-638 table: SEO and GEO share enough underlying signals (EEAT, robots, schema, content authority) that splitting them across two agents would force both to re-read the same primitives and produce overlapping findings. Same for Conversion+Lifecycle. The 9-section report stays because that's how marketers read it (per-discipline).

**What's wrong:** The decoupling concept is right; the *implementation via pivot* is the over-engineering.

1. The mapping is one bit per finding, not a 40-row YAML.
2. The plan's own rationale — "different signals require different specialist work" — is solved by giving each agent its primitive set + reference doc, not by mediating through rubric themes.
3. Agents already write `report_section` directly under F3.2's redesign. The "decoupling" is a comment in the prompt: "you're the Findability agent; you write findings for SEO or GEO; pick the right one per finding."

**The right model — agentic / hybrid / deterministic:** **Agentic.** Trust the agent to pick `report_section` from a 2-element enum. This is the lowest-cognitive-load decision in the entire pipeline.

**Concrete redesign:**
1. Findability agent prompt: "Tag each finding `report_section: 'seo' | 'geo'`. Use SEO for technical/on-page/backlinks/keywords; use GEO for AI-search citations and AI-crawler posture. Cross-cut findings (e.g., EEAT improving AI citation supply) — pick the section where the recommendation lives."
2. Same template for Conversion-Lifecycle.
3. Other 5 agents have a single `report_section` value (e.g., Brand/Narrative agent always tags `brand_narrative`); enum-validate at write time.
4. Stage 3 groups by `Finding.report_section`. Same as plan, no pivot lookup.

**Complexity removed:** The `rubric_theme → report_section` lookup table (which is the whole point of `rubric_themes.yaml` once `lens_weight_share` is gone) disappears. The "agent owns these rubrics, which map to these sections" prompt assembly (line 705) collapses to one line of agent-specific routing instruction.

**New risks:** (a) Findability agent might over- or under-tag `seo` vs `geo`. Synthesis Opus already merges and re-narrates per section; this is a soft routing decision, not a hard contract. (b) Loses the explicit "SEO has these 4 rubrics, GEO has these 2" inventory that helps agents structure their work. Mitigation: keep that structure as prose in the agent's reference doc (`findability-agent-references.md` already exists at line 575) — same information, no YAML schema.

**Verdict:** **KEEP** the decoupling concept; **DELETE** its current expression as YAML pivot. The 7-vs-9 mismatch is genuine; the pivot is not the way to express it.

---

## F4.1 — ~83 primitives as typed Python wrappers

**Today (planned):** ~83 primitives in `src/audit/primitives.py` (~80 collection + 3 reasoning). Each is a Python function returning a TypedDict with `partial: bool`. Stage 1a Python fan-out runs ~13 Tier-A primitives unconditionally; Stage 1b Sonnet discovery agent picks 20-40 of the remaining ~65-70 Tier-B/C primitives via `primitive_registry.yaml` tool exposure.

**Why it exists:** The plan's R4 restructure (line 274) splits primitives by *what kind of work they do*: Tier A is single-fetch API wrappers; Tier B/C is multi-source orchestrations with rot-prone heuristics. The TypedDict + `partial: bool` envelope ensures graceful degradation. Owned-provider-first discipline (R17) routes everything through the inventory.

**Sampling 5-10 to assess Tier-1 vs Tier-2:** From the U2 specs and provider inventory:

- **Tier-1 (paid API + cache + schema justified):** `analyze_backlinks` (DataForSEO Backlinks), `audit_page_speed` (PageSpeed API), `score_ai_visibility` (Cloro $0.01/q), `analyze_serp_features` (DataForSEO SERP), `audit_local_seo` (DataForSEO Business Data + local_pack), `gather_voc` (10 owned adapters with auth/rate-limits), `historical_rank_trends` (DataForSEO Historical), `keyword_gap_analysis` (DataForSEO Labs), `audit_aso` (Apify actors), `audit_youtube_channel` (YouTube Data API v3 quota). — ~20-25 functions where the wrapper carries cost-control + rate-limit + retry + auth complexity the agent shouldn't reinvent per call.

- **Tier-2 (cheap web checks where wrapper adds little):** `audit_directory_presence` (5 web fetches across G2/Capterra/AlternativeTo/PH/CWS — agent with WebFetch can do this), `audit_marketplace_listings` (Zapier/Slack/AppExchange path probes), `audit_launch_cadence` (PH history + changelog + GitHub releases — three free APIs, no orchestration), `audit_free_tools` (subdomain/path probes), `audit_corporate_responsibility` (ESG/B-Corp page probes), `audit_homepage_demo_video` (Wistia/Vimeo/YouTube embed detection on one page), `audit_trust_center` (SafeBase/Vanta/Drata fingerprint on one page), `audit_email_signature_marketing_indicators` (MEDIUM-LOW confidence triangulation explicitly), `audit_branded_serp` / `audit_branded_autosuggest` (Google query mining), `audit_help_center_docs` (path probes + Algolia DocSearch detection). — ~25-35 functions that are essentially `(url) → fetch → parse → return`. The Python wrapper buys schema and a `partial: bool` flag at the cost of a maintained function per check.

**What's wrong:**

1. **Wrapper count grows monotonically with audit ambition.** R1 added 17, R2 added 32 + ~24 deepening extensions. By R3 we'll hit 120+. Each is a function + test + registry entry + cost row + reference doc snippet.
2. **The `primitive_registry.yaml` is itself becoming a bug surface** (plan risk line 1625): "registry validated at load time against actual primitives.py signatures... quarterly review flagged." The tool-exposure layer for the Stage 1b agent has its own staleness risk distinct from the primitive layer.
3. **Tier-2 wrappers leak the shape of their underlying web checks into the audit's vocabulary.** "Audit homepage demo video" as a discrete primitive forces a finding to be about *that*; an agent given WebFetch + the brief "look for video assets and judge them" can produce a richer finding cross-referencing pricing-page videos, blog embeds, etc.

**The right model — agentic / hybrid / deterministic:** **Hybrid: keep Tier-1 wrappers, replace Tier-2 wrappers with agent + WebFetch + a ~3-line heuristic each in the agent's reference doc.**

**Concrete redesign:**
1. Triage `primitives.py` by Tier-1 (auth/cache/cost-control matters) vs Tier-2 (web fetch + parse).
2. Keep ~25 Tier-1 wrappers; they earn their schema.
3. Delete the ~30+ Tier-2 wrappers from `primitives.py`. Move the "what to look for" into the agent reference doc as a heuristic checklist (e.g., "Directory presence: probe G2, Capterra, AlternativeTo, PH, CWS — record present/absent + listing claim status if visible").
4. Stage 1b agent gets WebFetch + the Tier-1 wrapper set + the heuristics from reference docs.
5. `primitive_registry.yaml` shrinks to Tier-1 only. Staleness-risk surface area drops by ~70%.
6. Per-primitive cost tracking still works for Tier-1 (where cost matters); Tier-2 cost is rolled into the agent's `total_cost_usd` from `ResultMessage`.

**Complexity removed:** ~30 functions × ~50 LOC + their tests + registry entries. The "audit-coverage research expansion" rounds become reference-doc edits, not primitive-add PRs. The primitive-vs-registry consistency check (line 1625) shrinks proportionally.

**New risks:** (a) Tier-2 reproducibility drops — agent might check different directory sites on different runs. Plan already accepts this (line 1627 "some nondeterminism is the trade for adaptability"). (b) Agent might miss a check the wrapper would have done unconditionally. Mitigation: agent reference doc has explicit checklists; eval harness fixtures check coverage on dogfood prospects. (c) Some Tier-2 has hidden cost (paid Apify actors for G2 scraping, line 1658) — those are actually Tier-1 by the auth/cost test; recategorize, don't delete.

**Verdict:** **REDESIGN.** This is the second-most-impactful simplification after F3.2. ~30 fewer Python functions to maintain.

---

## F4.2 — 9 conditional enrichments R18-R26

**Today (planned):** 9 attach-X CLI commands (`freddy audit attach-{gsc,esp,ads,survey,assets,demo,budget,crm,winloss}`). Each gets a state-schema slot under `state.enrichments.X`, per-vendor adapter directory (R19 ESP has 7 vendors; R20 ads has 4), validation logic, idempotency contract, retention rules. R23 attach-demo has 9 listed safety mitigations including the scoped toolbelt machinery in `scoped_tools.py`. Plan ships all 9 on day 1.

**Why it exists:** Coverage. Plan line 268 frames it as "~99.5% with all 9 conditional enrichments granted." Each enrichment turns a public-signal finding into a real-data finding (e.g., Lifecycle pivots from "we detect a popup" to "your welcome series converts 8% vs benchmark"). Each is opt-in additive — absence doesn't block.

**What's wrong:**

1. **Plan's own adoption forecast is brutally low** (line 1649): R18 GSC 30-60%, R19 ESP 20-40%, R20 ads 10-25%, R21 surveys 10-20%, R22 assets 20-40%, R23 demo 15-30%, R24 budget 30-50%, R25 CRM 25-45%, R26 win-loss 10-15%. The bottom 5 are below 25% expected adoption. Building, testing, and maintaining 9 code paths where 5 likely fire <1-in-4 times is premature optimization.
2. **R23 attach-demo carries 9 listed safety mitigations** (line 1653). For an enrichment expected to fire ~15-30% of the time. The scoped-toolbelt machinery in `scoped_tools.py` is real engineering — Playwright observation-only mode, per-action human confirmation, ToS pre-flight, OS-keychain credential storage, isolated browser context, trace recording, 15-min hard timeout. This is an entire safety-critical subsystem for a single conditional code path.
3. **R19 ESP has 7 per-vendor adapters** (Klaviyo, Mailchimp, Customer.io, HubSpot, Braze, Iterable, ActiveCampaign). Plan acknowledges (line 1650): "deprecate low-adoption adapters after 12 months if fewer than 2 audits used them." So you build 7, expect to delete 4. That's the loop the plan is already in.
4. **R25 attach-crm v1 only ships HubSpot CSV path** (line 1462), explicitly defers the other 4 — proving the per-vendor-on-day-1 instinct doesn't survive contact with calibration.
5. **R26 attach-winloss embeds + clusters** with text-embedding-3-small + HDBSCAN for an enrichment expected at 10-15%. Plus PII-redaction Sonnet pass + Klue 31-questions methodology. Plan acknowledges <10 interviews = "directional only" — the enrichment doesn't hit the rigor it's engineered for at the prospect's typical sample size.

**The right model — agentic / hybrid / deterministic:** **Hybrid by enrichment.** Some are deterministic (CSV parse + benchmark lookup — R24 budget, R25 CRM), some need agent judgment (R26 win-loss themes, R22 brand assets), some are mostly safety surface (R23 demo). Ship the cheap-and-likely first; agent-handle the rest if any prospect actually wants them.

**Concrete redesign — ship 3 of 9 day 1:**
1. **R18 GSC** (highest predicted adoption 30-60%, free API, no PII complexity, real audit lift): KEEP day 1.
2. **R24 attach-budget** (CSV parse + YAML benchmark lookup; lowest engineering risk; clear value): KEEP day 1.
3. **R22 attach-assets** (high signal-to-engineering ratio: PDF/PPTX parse + cross-asset Opus pass; PII isolated to workspace; 20-40% adoption): KEEP day 1.
4. **Defer R19/R20/R21/R25/R26**: don't build adapters until first 5 audits show prospect-side demand. CLI command exists with stub `not_implemented` error pointing to "request as engagement add-on."
5. **Defer R23 attach-demo**: highest safety surface, novel risk, 15-30% adoption. The 9-mitigation safety stack should land *after* the audit has shipped a few times and the demo-flow value-prop is proven on willing prospects (engagement-scope work).

**Complexity removed:** The `enrichments/` subtree shrinks from 9 modules + 11 vendor adapters to 3 modules + 0 vendor adapters. `scoped_tools.py`, `build_demo_flow_toolbelt`, `build_welcome_email_toolbelt` machinery defers. The R23/R27 safety risk paragraphs (lines 1653, 1670) defer. The state schema enrichments slot stays full-shape (forward-compat); only the orchestrator wiring shrinks.

**New risks:** (a) Sales call loses the "we can ingest your CRM/ESP/ad-platform data" pitch line. Real, but: most prospects on a $1K audit won't grant API access on a first sales call regardless. The free-scan → sales-call → $1K-audit funnel doesn't depend on enrichment breadth. (b) Plan's "near-100% coverage" claim shrinks. Acceptable — that claim was always asymptotic. (c) Defer-then-add cost is real if a prospect *does* request a deferred enrichment. Mitigation: deferred items carry a 2-day "add to v1.1" estimate vs day-1 inclusion.

**Verdict:** **SIMPLIFY.** Ship 3 of 9; CLI stubs the rest with `not_implemented`; revisit at audit #5.

---

## F4.3 — Stripe `payment_events` Postgres table for webhook idempotency

**Today (planned):** Dedicated Supabase table (line 1535) with `event_id` unique key. Stripe webhook handler (line 1546) verifies signature, dedupes via `payment_events`, loads audit state by `metadata.audit_slug`, records payment, Slack-pings JR.

**Why it exists:** Stripe webhook delivery is at-least-once. Same `event_id` may arrive twice; you must not double-mark-paid. The table is the canonical idempotency record.

**What's wrong:** Honestly, very little. The audit-context note suggests "Replace Stripe `payment_events` table with single `last_processed_event_id` field." Let me steelman that and then push back.

The steelman: at $1K × ~20 audits/month = ~20 webhook events/month, a one-row-per-event table is overkill compared to a `state.payment.last_event_id` field with a "skip if already-processed" check.

The pushback: Stripe webhooks fire for many event types per checkout (`checkout.session.completed`, `payment_intent.succeeded`, refunds later, disputes later). A single `last_event_id` field can't dedupe across event types — `checkout.session.completed` and `payment_intent.succeeded` for the same checkout are *both* legitimate-and-distinct events. You need a multi-row dedup, which is what a table is. Single-field-on-state collapses the moment you add a refund webhook or chargeback handling.

Also: the table is an audit log of all payment-related events, useful for post-hoc reconciliation when prospects email "did my payment go through" and JR needs to point at the timestamp. A table per audit's payment field doesn't replicate this.

**The right model — agentic / hybrid / deterministic:** **Deterministic.** Webhook idempotency is exactly the kind of problem where you want a single source of truth, not LLM judgment.

**Concrete redesign:** No change. The table is correctly-sized for the problem.

If anything, *strengthen* it slightly: add `event_type` column (already implicit in Stripe events) and a `processed_at` timestamp so the audit log is queryable by what-and-when, not just by event ID.

**Complexity removed:** None.

**New risks:** None.

**Verdict:** **KEEP AS-IS.** This was a bad call to flag as over-engineering — it's actually correctly-sized infrastructure for at-least-once webhook semantics, and it costs one Supabase migration + ~15 LOC of insert logic. The pattern is standard; there's no leverage to gain from cutting it. (Honest withdrawal of the original audit-context flag here — the `last_processed_event_id` alternative doesn't survive the multi-event-type case.)

---

## Cross-cutting note

The 7 findings cluster around one structural fact: the plan's `rubric_themes.yaml` is the *integration point* between the score, the schema, the agent split, and the section split. Pull it (F3.2 DELETE) and:
- F3.1 SIMPLIFY becomes natural — no `lens_weight_share` to roll up.
- F3.3 SIMPLIFY shrinks 2 fields immediately.
- F3.4 KEEP becomes a one-line prompt rule, not machinery.

F4.1 (primitive triage) and F4.2 (enrichment defer) are independent simplifications worth ~30 fewer functions and ~6 fewer code paths respectively.

F4.3 stays as-is.

Net: if all SIMPLIFY/REDESIGN/DELETE land, the plan loses ~200-300 lines of spec, ~1 module (`rubric_themes.py`), ~30 primitive functions, ~6 enrichment subdirectories, and the score-calibration burden. The Hero TL;DR template, the 9-section report, the agent-section decoupling concept, and the deliverable arc all survive intact.
