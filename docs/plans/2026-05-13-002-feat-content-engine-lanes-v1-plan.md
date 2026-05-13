---
title: "Content Engine Lanes v1 — 4 New Lanes + Storyboard Extension + Shared Infra"
type: feat
status: active
date: 2026-05-13
origin: docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md
triage: 2026-05-13 (6 clusters resolved; 22 decisions applied; TD-26 judge-plan reconciliation; TD-27/28/29/30 site_engine integration)
---

## Triage Decisions Applied (2026-05-13)

Document review surfaced 32 findings (8 P0, 17 P1, 7 P2). 12 auto-fixes applied silently. The remaining 22 decisions were resolved through 6 cluster-batched triage prompts. Summary of decisions that change plan scope/shape — each is reflected in the relevant unit/decision section below; this list is the audit trail.

**Cluster 1 — Premise:** Hold full v1 scope **AND name 2 prospect archetypes** (revised 2026-05-13 post-reconsideration). The generic-factory premise is the agency's growth bet; ground the generalization in named pipeline rather than hypotheticals. See "Generalization Justification" section below for the 2 named prospects.

**Cluster 2 — Compliance flow gaps:**
- **TD-1.** Add pre-flight corpus pattern-scan to U18: scans voice corpus + style anchors against active rule-set patterns before ingest commits. Catches corpus-induced violation basin (D5 risk).
- **TD-2.** Add `weekly_publish_target` to R26 ClientConfig; lane stops emitting ship-candidates once target met. Size reviewer throughput in U18 launch runbook. **Revised 2026-05-13 to "Both":** also add `pre_publish_reviewer_secondary` (email + display_name) to R26 — secondary reviewer kicks in at 50% SLA if primary doesn't respond. Mitigates pre-publish chokepoint flywheel kill + vacation/unavailability dependency on primary reviewer.

**Cluster 3 — Security P0:**
- **TD-3.** HMAC signing key for U7 review URLs sourced from `GOFREDDY_REVIEW_HMAC_KEY` env var (never repo-checked-in); quarterly rotation runbook + dual-key overlap window; token TTL = per-client SLA; single-use via audit-log idempotency check.
- **TD-4.** Voice corpora protected: filesystem encryption (LUKS / FileVault / dm-crypt host-level); manual PII-scrubbing pass before ingestion; 7-year retention tied to legal traceability; documented GDPR Art. 17 erasure procedure with immutable hash-only chain if regulatory retention conflicts with erasure.
- **TD-5.** New `## Plan-level Threat Model` subsection added enumerating three exploits (HMAC key leak / CSRF / reviewer-email-swap-via-PR) with mitigations as explicit ship-gate items. Operationalize `.github/CODEOWNERS` on `clients/*/client.yaml` protected fields. Add SPF/DKIM/DMARC for sending domain.

**Cluster 4a — Test/regression discipline:**
- **TD-6.** D4 paired with `RUBRIC_VERSION_OVERRIDE` env var / commit-pinned baseline mode so 7 planned RUBRICS mutations don't invalidate all caches in lockstep.
- **TD-7.** D10 regression bar replaced with `max(5%, 2× measured std dev)` per-fixture. Pre-U11/U12 characterization spike: 5 repeated holdout passes per fixture in legacy mode to measure noise floor. Re-baseline criterion: 5 consecutive runs with composite mean within 1 std dev of legacy mean AND no fixture below legacy mean − 2 std dev.
- **TD-8.** D19 diff assertion strengthened: (a) new rule sets validate against `ComplianceRuleSet` with `model_config = ConfigDict(extra='forbid')`; (b) per-rule `prose` field length budget ≤500 chars; (c) `tests/` directory must also be unchanged in the diff assertion.
- **TD-9.** D14 SLA breach behavior changed from auto-reject to **auto-pause + operator notification**. Manual reviewer rejection stays terminal. SLA-breach now non-destructive; artifact stays in queue until explicit resume/escalate.

**Cluster 4b — Production posture:**
- **TD-10.** Stream A env-gated fixes graduate to unconditional before U1 (new U0 precondition). Conditional code paths removed. Resolves the load-bearing-flag concern across D10/D11/D19.
- **TD-11.** D12 replaced with **hybrid approach** (revised 2026-05-13 post-reconsideration): per-lane rubric IDs in `LaneSpec.rubric_ids` (preserves existing `rubrics.py:1529` bidirectional invariant, no substrate architecture change) PLUS shared `compliance_rules` prose registry that each lane's rubric resolves to at evaluation time. Same maintainability win (Art. 14 amendment = edit ONE prose location); lower architectural risk than introducing a cross-lane rubric primitive.
- **TD-12.** Phase per-client + decision gate added at end of Phase A: if partner consent + legal-review owner for at least one client are not resolved, pause Phase C for that client and reallocate to whichever is unblocked. Per-client phasing absorbs external risk.
- **TD-13.** U19 success bar adds operator-time measure: <1 working day onboarding clock from `client.yaml` first commit to first green pipeline run; zero-edit-to-shared-code count; "a person who did not author the substrate produced the stub config from the onboarding doc alone." Diff assertion stays as guard not bar.

**Cluster 5 — Security P1:**
- **TD-14.** Audit log moved to external storage (encrypted local disk OR R2 with per-client prefix); 7-year retention; reviewer email pseudonymized in long-term retention (hash + lookup table); GDPR Art. 17 erasure procedure with immutable hash-only chain if regulatory retention conflicts.
- **TD-15.** R2 storage uses per-client key prefix with IAM-scoped credentials (Klinika compromise can't read DWF assets). Bucket private by default; preview URLs are short-lived signed URLs (TTL = SLA window).
- **TD-16.** Email channel: `.github/CODEOWNERS` operationalized as actual file (TD-5 detail); SPF/DKIM/DMARC for sending domain (TD-5 detail); reviewer email change requires email confirmation to BOTH old and new address with 24h cooling-off.
- **TD-17.** Placeholder rule set production-launch posture: while `_placeholder_*` rule sets are active, (a) mandatory two-reviewer sign-off; (b) rate cap on published artifacts (≤3/week per client); (c) soft-warn or borderline auto-routes to second reviewer; (d) U7 HMAC key + audit-log retention decisions must be locked before placeholder regime ships to production.

**Cluster 6a — Scope cuts:**
- **TD-18.** D6 multi-rule-set merge logic **dropped**. v1 `evaluate_compliance` takes a single `rule_set_name`. List-API + merge logic + cross-rule-set-merge test deferred to first client onboarding with two rule sets.
- **TD-19.** `voice_persona_source legacy | shared` toggle **dropped**. U11/U12 direct cutover gated on regression CI (TD-7). No dual codepath; no v1.5 cleanup debt.
- **TD-20.** U7 collapsed to 1–2 modules + 1 test file. Single `src/review/service.py` (~150–200 LOC: signed-URL helper, submit, decision handler, JSONL audit log, SLA check) + `src/api/review_webhook.py` + single test file. Drop dedicated email module + storage module + SLA tiered-nag system.
- **TD-21.** ad_engine `full_bundle` flag **dropped**. Default to creative + LP copy only in v1. Reintroduce as v1.5 feature when a client contracts for targeting/bid/budget.

**Cluster 6b — Remaining:**
- **TD-22.** Add fixtures for ig_single + ig_story to U14 (~3 fixture JSONs). Keep all 6 image_engine formats.
- **TD-23.** Add `market_signal_compatible: bool` to rule-set definition. For `medical_pl` and `legal_pl`: false. ad_engine R19 market-signal dimension drops to no-op for any client whose active rule sets include a non-compatible one. Prevents adversarial objective in compliance-misaligned markets.
- **TD-24.** v1.5 backlog table added to end of Scope Boundaries with trigger conditions per deferred item. Commit to revisiting backlog at end of Phase D before any client #3 work begins.
- **TD-25.** Substrate Window protocol added per substrate-mutating unit (U11/U12 + RUBRICS PRs): the unit names which production lanes must be quiesced before merge. Operational discipline + documented in per-unit Approach.

**Cluster 7 — site_engine integration (added 2026-05-13 mid-plan):**
- **TD-27.** Add `site_engine` as the **4th new lane** in this plan rather than a separate plan. Rationale: site_engine consumes the same shared infra Phase A delivers (per-client config R26, voice persona framework R20, findings-brief contract R21, pre-publish reviewer R22 gate 2, compliance framework R22 gate 1). Bundling amortises the infra investment across 4 lanes instead of 3; splitting would build the same dependencies twice. Adds 2 Phase A shared-infra units (U7b Playwright render utility, U7c site audit utility) and 1 Phase C lane unit (U15b site_engine lane). Existing U16–U19 unchanged.
- **TD-28.** `site_engine` v1 scope = **section-level improvement only** (`hero`, `value_prop`, `social_proof`, `faq`, `cta`, `pricing`). No full-page rewrites; no design-system / component-library generation; no multi-breakpoint mutation; no React/SPA output. Full-page composition deferred to v1.5 with trigger condition: first client requests a from-scratch landing build AND existing section-level lane has shipped ≥3 sections per client across ≥2 clients.
- **TD-29.** `site_engine` brief sources in v1 = `marketing_audit` (primary) + `geo` (AI-search readiness signals). No `competitive` direct brief consumption in v1 (deferred — `competitive` already feeds `monitoring` which can re-emit if needed). Launch runbook prioritises clients with `marketing_audit` already run (Klinika and DWF both qualify per U18).
- **TD-30.** `site_engine` rubric anchors stored at **`docs/rubrics/site-quality.md`** (new top-level `docs/rubrics/` directory). Seeded from the 2026-05-13 gofreddy.ai landing-page session as v1 calibration data. Per the TD-11 hybrid pattern, `LaneSpec.rubric_ids = (SE-1..SE-8)` live in the substrate; the prose anchors live in the rubric file. The same file is consumed by the parallel `compound-engineering:site-improvement` Claude Code skill — single edit propagates to both surfaces. Sibling-file convention to the existing per-lane anchor docs (`docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`, `docs/plans/2026-05-13-002-AE-rubric-anchors.md`); the `docs/rubrics/` location is intentional because this rubric has dual consumers (lane + skill), unlike the per-plan anchor files which only the lane consumes.

**Reconciliation with parallel Judge Plan (2026-05-13):**
- **TD-26.** Three-agent investigation pass found the parallel `2026-05-13-001-judge-substrate-fix-and-kernel-plan.md` defines primitives this plan must consume rather than parallel-define. Resolution applied in two passes (2026-05-13). Complete edit manifest:

  **Pass 1 — reconciliation:**
  - **File rename** 001 → 002 (judge plan owns 001 by timestamp; same-day filename collision resolved).
  - **14 companion-doc filenames** bumped 001 → 002 for consistency (AE/IE/AD rubric anchors, klinika/dwf launch runbooks + artifacts JSON, noise-floor baselines, medical_pl rule-set notes, onboarding-time measurements, generic rule-set doc).
  - **Frontmatter triage line** updated to reflect TD-26 addition.
  - **U0 narrowed:** Stream A axis-collapse fix already graduated to default-on on main per `cli/freddy/commands/evaluate.py:215-248`. U0 is now escape-hatch removal + dead-conditional cleanup; no production behavior change.
  - **U1 baseline corrected:** `RUBRICS` count is **53 on main** (was 52 when this plan was first drafted), shifted by `896f366` (X-9) + `204e9a6` (MA tier-tags). Derived-count assertion approach unchanged. D4 rationale + Context-section RUBRICS reference also updated for consistency.
  - **New section "Substrate Consumed from Judge Plan"** added before Implementation Units listing 5 soft consumes (S1–S5: per-step model split, post-rewrite anchor design, RUBRICS=53 baseline, Stream A default-on, `custom_persist_judge_payload` hook) + 1 informational item (G1: judge plan U0.2 archive persistence; see Pass 2 reframe) + judge-plan explicit rejections (no LANE-9 kernel for new lanes; no inline Python trigger lists).
  - **U13/U14/U15 judge wiring specified:** each new lane gets explicit `inner_backend` + `inner_model` + outer judge backend + fallback policy per memory `judge-decisions-2026-05-11.md` (frontier-only, diverse from inner-loop). Codex/gpt-5.5 cyber-filter fallback to claude/sonnet pre-documented since geo + competitive already hit this.
  - **U5 anchor guidance added:** compliance YAML rule prose authors follow post-rewrite anchor design pattern from `896f366` to avoid the same ceiling-bound failure mode.
  - **Explicit rejections preserved:** no AE-9/IE-9/AD-9 kernel rubrics; 8-rubric-per-new-lane convention holds.

  **Pass 2 — post-amendment self-audit (4 issues caught):**
  - **G1 reframed from "conditional gate" to "informational, NOT a gate":** new lanes v1 use aggregate scoring (existing substrate handles it); judge plan U0.2 lands in parallel, no blocker. If it doesn't land, new lanes still ship. Backfill is later if needed. Removed G1 references from U13/U14/U15 dependency lines.
  - **D24 added:** image_engine vision sub-judge backend = Gemini 2.5 (was a buried U14 bullet; promoted to architectural decision with rationale). Used for visual rubrics (IE-1/2/3/5/6); text rubrics stay on claude/opus.
  - **D25 added:** compliance-judge backend = single claude/opus across all 7 lanes with compliance gates. Prevents per-lane drift in Art. 14 / legal_pl interpretation. (Was previously specified only inside U15.)
  - **Backend-wiring test scenarios added to U13/U14/U15:** LaneSpec override resolution + cyber-filter fallback fixture. Test_image_engine_substrate also verifies vision-sub-judge dispatch (visual rubric → Gemini, text rubric → claude/opus).
  - **U15 day-1 fallback:** ad_engine `inner_backend = claude/sonnet` from day 1 (not deferred to first rejection), since medical/legal-vertical regulated content likely trips codex cyber filter. Reversible behind flag after Phase D smoke.

  **Pass 3 — feasibility review caught 3 P0s + 2 P1s + 1 P2; all assumed non-existent primitives; all reverted to existing patterns:**
  - **P0-1 (D24 vision-judge primitive):** `image_preview_service.verify_preview()` is a fixed 2-axis preview QA tool, NOT a rubric-driven judge backend. D24 + U14 revised: vision judge is **built fresh in U14** as `src/evaluation/vision_judge.py` (~80 LOC) on the Gemini 2.5 SDK, sibling to the preview QA tool not a wrapper around it. U14 file list extended with the new file + its test.
  - **P0-2 (cyber-filter auto-fallback doesn't exist):** `ModerationBlockedError` is raised only by image/video/audio backends, never by text inner-session agents; geo + competitive use **static-pin** pattern (`lane_registry.py:174-175, 206-207`), not dynamic fallback. U13/U14 revised: static-pin from day 1; if codex hard-rejects on smoke, swap via LaneSpec edit + redeploy. U15 was already using static-pin correctly; just removed the misleading "fallback" framing.
  - **P0-3 (D25 single-backend needs a shared primitive):** `LaneSpec` has no compliance-judge-backend field. D25 + U5 revised: single backend lives in `ComplianceJudgeConfig` singleton at `src/compliance/judge_config.py` (~15 LOC) owned by U5, consumed transitively by all 6 lanes with compliance gates (geo dropped from D25's list — no compliance gate in this plan; was P2-2).
  - **P1-1 (G1 backfill cliff):** added author-side commitment to §Substrate Consumed — U13/U14/U15 judges request `dimension_scores` in payload from day 1 even though `evaluate_variant.py:1606,1722,1747` currently writes empty list. Costs ~0 LOC; prevents permanent backfill loss when U0.2 lands.
  - **P1-2 (U15 "reversible behind flag" implies a primitive that doesn't exist):** Replaced "behind flag" with "via LaneSpec edit + redeploy or per-invocation `--inner-backend` CLI override." No feature-flag mechanism exists; honest framing.
  - **All fallback test scenarios removed** from U13/U14/U15 verification lists (replaced by static-pin LaneSpec-value assertions); test stub for `ModerationBlockedError` not needed since the substrate doesn't fall back.

The unit/decision sections below were updated inline to reflect these decisions; this list is the canonical audit trail.

---

# Content Engine Lanes v1 — 4 New Lanes + Storyboard Extension + Shared Infra

## Overview

Add a generic multi-client content factory to the gofreddy autoresearch system. Ship **four** new lanes (`article_engine`, `image_engine`, `ad_engine`, `site_engine`) plus a substantial extension to the existing `storyboard` lane (5 platform_targets × 3 format_modes + voice corpus input), four existing-lane modifications (`geo` + `monitoring` brief emission, `linkedin_engine` + `x_engine` voice persona migration), and **eight** shared infrastructure pieces (per-client config object, voice persona framework, findings-brief contract, static-image composition module, pluggable compliance framework, pre-publish human review service, **Playwright-based site render utility**, **a11y + perf audit utility**).

The 4th lane (`site_engine`) was integrated mid-plan per TD-27 because it consumes the same Phase A shared infra as the other three content lanes — bundling amortises that investment across 4 lanes instead of 3 and avoids parallel-defining the same client-config / voice / brief / compliance / reviewer primitives twice.

**Terminology:**
- **Onboarded client** — a real client with voice corpus consent obtained and ≥5 artifacts published to real channels during their launch window. v1 onboards Klinika Melitus and DWF Poland.
- **Demonstrated archetype** — a test-only client config instantiated to validate the config-only onboarding mechanism. Stub data acceptable; not subject to the "≥1 real-client fixture per archetype" requirement that applies to onboarded archetypes. U19's `b2b_tech` falls here.
- The D11 archetype-level CI assertion (≥1 real_client fixture) applies only to onboarded archetypes; `stub_allowed: true` archetypes are excluded.

First two clients onboarding: **Klinika Melitus** (Warsaw aesthetic dermatology, `b2c_aesthetics` archetype, `medical_pl` compliance rule set) and **DWF Poland** (international law firm, `b2b_regulated` archetype, `legal_pl` rule set). The architecture is designed for indefinite future clients — onboarding a new client must be a config-and-corpus operation, not a code change.

v1 is production-grade. No demo deadline. Every Success Criterion must be met by output that's actually shippable to real clients on real channels. Realistic build window: 3–5 months sequential / 8–14 weeks with parallel workstreams (JR accepted timeline 2026-05-13).

## Generalization Justification

The generic-factory architecture is justified by a near-term client pipeline beyond the first 2 onboarded clients. Two named prospect archetypes are tracked to ground the generalization in real upcoming work rather than hypotheticals. Each names the archetype, expected compliance rule sets, and the trigger event that would move them into onboarded status:

| Prospect archetype | Compliance rule sets | Notes / trigger |
|---|---|---|
| **Polish B2C aesthetic / wellness adjacent** (e.g., another aesthetic clinic, dental practice, dermatology specialist) | `medical_pl` (reuses Klinika's rule set; zero net-new rule-set authoring) | Onboarded when a Warsaw/Krakow/Wrocław aesthetic-or-dental contact converts. The `medical_pl` reuse is the proof that the per-client config pattern works without code. Expected within 3 months of Klinika launch based on word-of-mouth referral channel. |
| **Polish B2B services** (consultancy, accounting firm, SaaS startup, or AI company) | `legal_pl` (lighter touch for non-lawyer professional services) OR `gdpr_eu` (data-handling) OR new `claims_pl` (general professional claims) | Onboarded when a Polish SaaS / consultancy / accounting-firm prospect signs. Validates that adding a new rule set (when needed) is genuinely config-only. Expected within 3–6 months of DWF launch. |

**If neither archetype materializes within 6 months of v1 ship,** the generic-factory architecture has produced zero incremental value over a 2-lane purpose-built build. That's the falsification gate: revisit the architecture decision at end of Klinika+DWF launch windows + 6 months.

If you're considering naming specific prospects rather than archetypes, this section can be updated to carry their slugs (placeholder `clients/<prospect-slug>/client.yaml` files with `status: prospect` for tracking) — useful for sales-pipeline accountability, optional for the architectural justification.

## Problem Frame

Existing autoresearch lanes (`geo`, `competitive`, `monitoring`, `storyboard`, `marketing_audit`, `x_engine`, `linkedin_engine`) don't cover the highest-volume content channels most clients buy:
- Short-form video on TikTok / IG Reels / IG Stories
- Long-form articles (blog SEO + LinkedIn Article)
- Static visuals (IG single, IG carousels, IG story slides, LinkedIn document carousels, hero images, ad statics)
- Paid ad creative (Meta + LinkedIn in v1 build; Google Ads architecture-supported, build deferred to v1.5)
- **Site improvement** — every client has a website that drips conversion. Section-level rewrites (hero / value-prop / social-proof / FAQ / CTA / pricing) currently happen as one-off engineering work, not as a lane with auto-research-driven mutation + AI judges + human review. The 2026-05-13 gofreddy.ai landing-page rebuild produced ~6 hours of high-quality calibration data (anti-slop signals, plain-English vs jargon, honest-claim anchors, interactive-element patterns) that becomes v1 training data for SE-1..SE-8.

Plus four cross-cutting gaps the brainstorm surfaced:
- Cross-channel voice consistency (each engine handles voice independently today)
- Cross-lane brief orchestration (no handoff from `geo`/`monitoring` to downstream content lanes today)
- Per-client configuration (each new client today would require scattered code changes)
- Compliance gating (no regulatory-content framework exists)

See origin: `docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md`.

## Requirements Trace

Mapped to origin doc R-numbers (R1–R26) plus site_engine additions (R27–R34, added 2026-05-13 per TD-27):

- **R1–R4** Storyboard lane extension — addressed by Unit U8
- **R5–R10** article_engine — addressed by Unit U13
- **R11–R15** image_engine — addressed by Units U6 (static composition module) + U14
- **R16–R19** ad_engine — addressed by Unit U15
- **R20** Voice persona framework — addressed by Unit U3
- **R21** Findings-brief contract — addressed by Unit U4
- **R22** Two-gate compliance (in-loop fitness judge + human pre-publish review) — addressed by Units U5 (rule-set primitive) + U7 (review service) + U16/U17 (rule-set authoring)
- **R23–R25** Lane chain orchestration — addressed by Units U9 (geo emission) + U10 (monitoring emission). R24 (only article_engine consumes briefs in v1) and R25 (spawn briefs deferred to v1.5) define scope boundaries; U13 wires article_engine brief consumption
- **R26** Per-client config object — addressed by Unit U2
- **R27** Section-level site rendering pipeline — addressed by Unit U7b (Playwright headless render, font-load wait, configurable viewport)
- **R28** Site a11y + perf audit — addressed by Unit U7c (axe-core a11y + Lighthouse-equivalent perf, returns structured JSON consumable by SE-6 + SE-7 judges)
- **R29** Site visual hierarchy + CTA prominence rubric (SE-1) — addressed by U15b via render judge consuming `docs/rubrics/site-quality.md`
- **R30** Site copy clarity + plain-English rubric (SE-2) + claim honesty + anti-overselling rubric (SE-3) — addressed by U15b via text judge consuming `docs/rubrics/site-quality.md`
- **R31** Site voice persona fit rubric (SE-4) — addressed by U15b consuming U3 voice persona framework unchanged
- **R32** Site brand-token + aesthetic-fit rubric (SE-5) — addressed by U15b consuming new `brand_tokens` field on R26 ClientConfig (U2)
- **R33** Site a11y + semantic structure rubric (SE-6) + performance rubric (SE-7) — addressed by U15b consuming U7c audit utility
- **R34** Site anti-slop rubric (SE-8) — addressed by U15b via render judge with anti-slop calibration prose seeded from 2026-05-13 landing-page session

Plus existing-lane voice migrations (R20): Unit U11 (`linkedin_engine`) + Unit U12 (`x_engine`).
Plus Klinika + DWF instantiation: Unit U18.
Plus client #3 architectural success bar: Unit U19.

Success Criteria from origin (production-grade, all must hold):
- Holdout fixtures green per archetype, with ≥1 real-client-content fixture per archetype
- End-to-end demo per onboarded client, both compliance gates passing
- Client #3 onboards config-only (validated against b2b_tech stub archetype)
- Cross-lane voice consistency: same persona consumed unchanged by 4 lanes
- ≥5 client-approved-and-published pieces per onboarded client during launch window

## Scope Boundaries

(Carry forward from origin doc Scope Boundaries section, restated for plan reviewers.)

**Not in v1 build:**
- No human shoots (all video via fal.ai I2V)
- No clinical Klinika visuals (per-client `content_denylist` enforced)
- No Google Ads variant generator (platform parameter supported, build deferred to v1.5 when first client demands)
- No first-party platform Marketing API integration (Meta/Google/LinkedIn ad account perf APIs deferred)
- No x_article adaptor in `article_engine` (niche audience)
- No findings-brief integration beyond 2 demo pairs (`geo → article_engine`, `monitoring → article_engine`)
- No article-engine spawn brief emission (R8 dropped — would be dead infra in v1)
- No targeting/bid/budget recommendations from ad_engine in v1 (per triage TD-21; `full_bundle` flag dropped). Reintroduce in v1.5 when a client contracts for full-bundle output.
- No voice persona sub-fields beyond `corpus_path`, `voice_rules`, `style_anchors`
- No cross-lane rubric primitive (hybrid per TD-11 revised: per-lane rubric IDs + shared prose registry. Single prose location for Art. 14 amendments, no substrate invariant change). True cross-lane primitive (one ID referenced by N lanes) deferred to v1.5 if/when needed.
- No standalone longform/legal_alert/Chambers submission/personal_brand/reviews/CRO/deal_announcement lanes
- No email/podcast/SMS/push-notification lanes
- No ad management ops automation
- No client billing / contract infrastructure
- **No full-page site composition in v1** (`site_engine` ships section-level only per TD-28; sections: hero, value_prop, social_proof, faq, cta, pricing). Full-page rewrites deferred to v1.5.
- **No design-system / component-library generation** (`site_engine` mutates within existing client brand_tokens; doesn't propose token changes)
- **No multi-breakpoint mutation** (`site_engine` mutates a single responsive output; doesn't optimise mobile/tablet variants separately in v1)
- **No React / Vue / SPA output from site_engine** (vanilla HTML+CSS+JS only)
- **No SEO meta-tag generation from site_engine** (consumes meta from briefs; doesn't generate)
- **No backend / form / payment integration from site_engine** (presentation layer only)

**Architecture supports but build deferred:**
- N compliance rule sets (architecture takes any; v1 ships 2)
- Google + x_ads + tiktok_ads + reddit_ads platforms (parameterized; variant generators not built)
- ~~Per-campaign `full_bundle` toggle in ad_engine~~ — dropped per triage TD-21. Targeting/bid/budget output is v1.5.
- New archetypes added to fixture tree (slots ready; filled on client onboarding)

## Context & Research

### Relevant Code and Patterns

**Lane registry & rubric infrastructure (foundational):**
- `autoresearch/lane_registry.py` — 605 LOC. `LaneSpec` dataclass (frozen) with **6 `custom_*` callable hooks** (`custom_mutate`, `custom_score`, `custom_validate`, `custom_promote`, `custom_objective_score_from_entry`, `custom_persist_judge_payload`), plus `rubric_ids`, `readonly_subprefixes`, `structural_doc_facts`, `structural_gate_functions`, `render_rubric_ids`, and per-lane `inner_backend` / `inner_model` overrides. 8 existing `LaneSpec` instantiations (`LANES` dict, lines 131–410). Helper `_rubric_ids(prefix)` for 8-rubric lanes; for 6-rubric lanes (x_engine, linkedin_engine) inline tuples are used.
- `src/evaluation/rubrics.py` — ~1700 LOC. `RubricTemplate` dataclass (line 16). `RUBRICS` dict assembled inline + from `programs/marketing_audit/prompts/judges/MA-*.md`. **Hard invariant on main (line 1700) is `assert len(RUBRICS) == 53` (32 base + 8 MA + 13 X/LI incl. X-9)** — shifted from the earlier 52 baseline by `896f366` (X-9 algorithmic-citizenship) and `204e9a6` (MA tier-tag completion). Bidirectional cross-check (~5 lines later): every `LaneSpec.rubric_ids` ID must exist in `RUBRICS`; sum of all `rubric_ids` lengths must equal `len(RUBRICS)`. `RUBRIC_VERSION` computed as SHA256 prefix nearby.
- `autoresearch/archive/v007-curated/workflows/specs.py` — `WorkflowSpec` + `WorkflowConfig` + `FindingsPromotionConfig` (intra-lane only). `WorkflowSpec` has **12 fields**: `name`, `config`, `config_dir_name`, `configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings`, `findings_promotion`, `render_report`.
- `autoresearch/archive/v007-curated/workflows/__init__.py` — `WORKFLOW_SPECS` dict registering **6 lane SPECs** (geo, competitive, monitoring, storyboard, x_engine, linkedin_engine) — marketing_audit is excluded from this canonical dict (it has its own per-archive registration). Per-lane archive dirs (`archive_<lane>/{current_runtime,v<NNN>}/workflows/`) each carry their own copy of every other lane's workflow file (10+ copies per file). **New lanes must be registered in BOTH the canonical v007-curated `__init__.py` AND propagated to every per-lane archive's `current_runtime/workflows/` and head-version `workflows/` directories** to avoid `ImportError` during cross-lane evolution runs. Confirm at implementation whether `evolve_ops.ensure_lane_heads` (or similar materialization tool) handles this automatically; if not, add a propagation step to each new-lane implementation unit.

**Content-lane precedent (mirror for `article_engine`):**
- `autoresearch/archive_x_engine/current_runtime/workflows/x_engine.py` — 211 LOC. `WorkflowSpec` SPEC + 8 callables (`configure_env`, `pre_summary_hooks`, `snapshot_evaluations`, `completion_guard`, `list_deliverables`, `augment_quality_metrics`, `count_findings` → 0 for content lanes). `FindingsPromotionConfig(title="Global Findings: X Engine", confirmed_threshold=2, repeated_threshold=2)`.
- `autoresearch/archive_x_engine/current_runtime/workflows/session_eval_x_engine.py` — 217 LOC. `SessionEvalSpec` with X-1..X-6 criteria, per-artifact `structural_gate` (frontmatter + length brackets + meta + slop-check subprocess), `load_source_data`, `cross_item_criteria={"X-6": CrossItemCriterion(glob="drafts/*.md", max_items=10, words_per_item=400)}`.
- `autoresearch/archive_x_engine/current_runtime/programs/x_engine-session.md` — 270 LOC. Agent prompt; reads `$X_ENGINE_ANGLE_ID` + `$X_ENGINE_SESSION_DIR` from harness.
- `autoresearch/archive_x_engine/current_runtime/programs/x_engine-evaluation-scope.yaml` — 12 LOC. `domain:`, `outputs:`, `source_data:`, `transient:`.
- `autoresearch/archive_x_engine/current_runtime/templates/x_engine/` — per-lane templates directory (currently README-only; placeholder for skeleton drafts).
- `tests/autoresearch/test_x_engine_substrate.py` — 125 LOC. Substrate-level tests using synthetic-package loader for relative imports.

**Storyboard precedent (mirror for `image_engine` and `ad_engine` deliverable shape):**
- `autoresearch/archive_storyboard/current_runtime/workflows/storyboard.py` — 96 LOC.
- `autoresearch/archive_storyboard/current_runtime/programs/storyboard-session.md` — 208 LOC. Hardcoded "5 production-ready storyboards" target; 8 SB-1..SB-8 rubrics; story plan JSON schema with hardcoded `camera_motion` enum (`static|pan|dolly|tracking|handheld|zoom`); `<!-- AUTOGEN:STRUCTURAL:START -->` block regenerated from lane registry on every variant clone.
- Note: `WorkflowConfig` is frozen — adding `platform_target` / `format_mode` parameters likely goes via `configure_env(client)` env-passing pattern (`$STORYBOARD_PLATFORM_TARGET`, `$STORYBOARD_FORMAT_MODE`) rather than new `WorkflowConfig` fields.

**Generation provider plumbing:**
- `src/generation/fal_client.py` — 348 LOC. `FalPlatformClient` with `generate_clip` (T2V/I2V via LTX-2.3, `_T2V_FALLBACK` map) and `generate_image` (FLUX.2 Pro). 3-failure circuit breaker (`_consecutive_failures`), cost recording via `cost_recorder.record("fal", "clip_gen"/"image_gen", ...)`. `ModerationBlockedError` is fatal (not breaker-counted). `_ALLOWED_DOMAINS = ("v3.fal.media", "fal.media", "fal.run", "storage.googleapis.com")`.
- `src/generation/composition.py` — 584 LOC. FFmpeg video composition with ASS subtitle burn-in. **Video-only. Static-image composition is net-new.**
- `src/generation/caption_presets.py` — 99 LOC. 6 video subtitle styles. **Video-only.**
- `src/generation/image_preview_service.py` — 567 LOC. `ImagePreviewService` with 4 backends (gemini/grok/imagen/fal); auto-fallback Gemini→fal on 429.
- `src/generation/storage.py` — 120 LOC. `R2GenerationStorage` with UUID-regex-enforced keys. Production storage.
- `src/generation/local_dev_storage.py` — 51 LOC. `LocalDevPreviewStorage` — dev shim only.
- `src/generation/providers.py` — 94 LOC. `GenerationProvider` Protocol.

**Existing data providers (reuse patterns for ad_engine signal):**
- `src/competitive/providers/foreplay.py` — 196 LOC. `ForeplayProvider` for Meta/TikTok/LinkedIn ad intelligence. `CircuitBreaker(failure_threshold=3, reset_timeout=60, name="foreplay")`, daily credit limit, cost recording.
- `src/competitive/providers/adyntel.py` — 127 LOC. `AdyntelProvider` for Google ads. `$0.0088 * pages_fetched` cost.
- `src/audit/tools/serpapi_ads.py` — 184 LOC. `SerpApiAdsClient`. Different pattern: graceful degradation (`degraded=True`), no circuit breaker.
- `src/seo/providers/gsc.py` — 218 LOC. `GSCClient` for Google Search Console. Service-account auth via `GSC_SERVICE_ACCOUNT_PATH`. Free.
- `src/common/circuit_breaker.py` — 58 LOC. `CircuitBreaker` with CLOSED → OPEN → HALF_OPEN → CLOSED.
- `src/common/cost_recorder.py` — 129 LOC. `cost_recorder.record(provider, operation, *, cost_usd, tokens_in, tokens_out, model, metadata)`. JSONL append.

**Findings promotion convention (intra-lane today, cross-lane net-new in v1):**
- `FindingsPromotionConfig` in `workflows/specs.py:25-29`. Every existing lane has one with `title="Global Findings: <Lane>"`, both thresholds = 2.
- `autoresearch/archive_x_engine/current_runtime/scripts/promote_findings.py` — canonical promotion tool. **Intra-lane aggregation only.**
- Cross-lane brief handoff is **net-new infrastructure** (R21 in origin).

**Concurrency (current state, post Plan B U9):**
- `autoresearch/concurrency.py` — single global `MAX_PARALLEL_AGENTS` cap (default 4). The 5 per-resource semaphores (claude=4, codex=2, opencode=8, judge_http=10, cloro_search=2) were collapsed by Plan B U9. The `resource=` kwarg on `parallel_for` is accepted-but-ignored.
- Cross-lane parallelism in `run_all_lanes` is intentionally NOT enabled (memory: "5 P0 thread-safety bugs in cmd_run").
- Operator dial-up: start at 2, bump to 4, revert when transient errors cluster.

**Test infrastructure:**
- `tests/autoresearch/test_lane_registry.py` — 293 LOC. LaneSpec accessors, `_assert_models_literal_matches`, manifest helpers (18 scenarios from lane-registry refactor).
- `tests/autoresearch/test_structural_doc_facts.py` — 145 LOC. **Bidirectional drift test:** every bullet in `STRUCTURAL_DOC_FACTS` ↔ gate function in `STRUCTURAL_GATE_FUNCTIONS` ↔ real callable in `_validate_<domain>`. New lanes must extend this test or follow x_engine's pattern of routing structural gates through `session_eval_<lane>.*` rather than `_validate_<lane>`.
- `tests/autoresearch/test_x_engine_substrate.py` — substrate-test template using synthetic-package loader.
- `autoresearch/test_lane_ownership.py` — 63 LOC. `path_owned_by_lane` ownership tests.

**Eval suites (holdout fixtures):**
- `autoresearch/eval_suites/search-v1.json` — daily evolution fixture set with `random_per_domain` + `anchors_per_domain` per lane. x_engine/linkedin_engine carry `0 anchors / 3 random` (dynamic IDs).
- `autoresearch/eval_suites/SCHEMA.md`, `TAXONOMY.md` — schema docs.
- Per-backend variants: `search-v1-claude-haiku.json`, `search-v1-claude-opus.json`, `search-v1-claude-sonnet.json`, `search-v1-deepseek.json`.

**Plan structure precedent:**
- `docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md` (Stream A) — Goal / Non-goals / Decisions (locked) table / Units table / Unit detail with Goal/Steps/Acceptance/Reversibility.
- `docs/plans/2026-05-11-003-external-absorptions-plan.md` (Stream C) — same shape + license-compliance subsections.
- `docs/plans/2026-05-11-004-peripheral-simplification-plan.md` (Plan D) — YAML frontmatter, Tier-organized units.

### Institutional Learnings

**marketing_audit shipping (75 commits, 11 production bugs surfaced during dry-run + deep-review) — patterns to prevent regression:**
1. **Fresh `session_id` per retry** — silent rc=1 retry collision broke `claude --session-id <uuid>` reuse. Every lane subprocess must allocate fresh session_id per attempt.
2. **`max_turns` budgets with empirical headroom** — Stage 1b ran out at 20, raised to 40; 1c/3/4 raised 4→8/12. Budget exhaustion is silent.
3. **Permissive Pydantic schemas** — start with `extra=allow` and no `min_length`; tighten after 3–5 real runs.
4. **Filesystem ground-truth for outputs** — `expected_output_files` on `AgentRunner.run()`; trust files-on-disk over subprocess exit code (Claude exits rc=1 silently after successful `Write` calls).
5. **`_safe_format` for `{}` escaping** — every prompt template with JSON examples MUST pre-escape curly braces before `.format()`.
6. **RUBRICS registration order** — rubric prose blocks land BEFORE the `LaneSpec` registers; bump assert; verify `python -c "from src.api.main import app"` after.
7. **Deploy scaffolds in same PR** — if Content Engine lanes need worker endpoints or pre-publish UI, ship deploy artifacts in the same diff.
8. **No mocking in dry-run validation** — real agent outputs surface schema mismatches that mocks miss.

**x_engine + linkedin_engine port (8–10wk for 2 lanes, master plan v13) — patterns to apply:**
- **Mirror `competitive.py` NOT `geo.py`** for `WorkflowSpec` shape (`geo.pre_summary_hooks` runs scripts that diverge from simple lane shape).
- **5 hardcoded `domain==X` branches in `run.py` / `runtime/` / `scripts/` fall through gracefully** for new lanes (verified Round-8 audit). No edits needed.
- **Cold-start failure mode:** linkedin_engine v040 produced 0/4 fixtures because the agent never produced structurally-valid drafts. Fix: prescriptive skeleton template + Pre-ship Checklist that maps 1:1 to the structural gate.
- **`count_findings → 0` for content lanes** — drafts ARE the deliverables; no `findings.md` is parsed. Wire `findings_promotion` for substrate compatibility.
- **Two-template scorer dispatch** — `judges/evolution/prompts/scorer_templated.md` with `{criteria}` placeholder; Content Engine lanes consume it (new lanes can't share existing lanes' tuned baseline).

**Lane registry refactor (2026-04-28) — patterns:**
- Every consumer (`for domain in DOMAINS`) derived from registry. Don't hardcode lane names anywhere.
- Default `custom_*=None` unless scoring genuinely diverges.
- `readonly_subprefixes` was introduced after Pi v007 meta-agent mutated `workflows/geo.py` to neuter `completion_guard`. Every new lane must lock `workflows/<lane>.py` + `session_eval_<lane>.py` + shared substrate.

**fal.ai stability (production-stable as of 2026-05-08):**
- 3-failure circuit breaker built in. Reuse pattern for new providers.
- `ModerationBlockedError` is fatal, not retried.
- Cost-per-second: 480p ~3¢, 720p ~5¢, 1080p ~8¢.
- Production = `R2GenerationStorage`; dev = `LocalDevPreviewStorage` shim writing `file://` URLs to `$TMPDIR/gofreddy-previews/`. **No mid-run fallback between them** — that would corrupt cross-lane consumption.

**Plan B archived 2026-05-13 (JR decision):**
- `autoresearch_v2/` will be archived. Content Engine lanes ship on existing `autoresearch/` substrate.
- No double-port concern.
- Stream A's env-gated fixes (`AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=on`, `AUTORESEARCH_EVAL_FIX_HOLDOUT=on`, `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES=on`) remain enabled for any holdout measurement.

**No prior solution docs in repo for:**
- Compliance / regulatory content generation gates (closest: x_engine factual-veto split + slop-gate)
- OAuth circuit breaker / provider-quota convoy mitigation
- Cross-lane voice consistency at N>2 lanes (x_engine/linkedin_engine shares only 2 lanes' voice substrate)
- Pre-publish human review workflow (closest: marketing audit ship-gate halt pattern)
- Per-client config object pattern

All four of these are net-new design in this plan.

### External References

Not used. Codebase has strong local patterns for everything except static-image composition (Pillow vs Cairo vs skia is punted to implementation; default Pillow). External research would have added time without new information.

## Key Technical Decisions

| ID | Decision | Rationale |
|---|---|---|
| D1 | Build on existing `autoresearch/` substrate; archive `autoresearch_v2/` | JR decision 2026-05-13. No double-port concern, simplifies sequencing. |
| D2 | Mirror x_engine/linkedin_engine pattern for `article_engine`, `image_engine`, `ad_engine` — including `count_findings → 0` and `findings_promotion` for substrate compatibility | x_engine port master plan v13 + linkedin_engine v040 cold-start fix established the content-lane pattern. |
| D3 | New rubric ID prefixes: **AE** (article_engine), **IE** (image_engine), **AD** (ad_engine). 8 rubrics each for the new lanes (per `_rubric_ids` helper); 6 each for x_engine/linkedin_engine stay unchanged | Avoid prefix collisions; 8-rubric default matches GEO/CMP/MON/SB/MA. Content lanes' rubric prose authoring is the long pole (~30–40 lines × 24 rubrics ≈ 720–960 lines). |
| D4 | Replace the hardcoded magic number (currently `53` on main, was `52` when this plan was first drafted) with derived `assert len(RUBRICS) == sum(len(spec.rubric_ids) for spec in LANES.values())` | Per spec-flow-analyzer P1-5: 6× bigger migration than X/LI port; manual lockstep on a single integer creates merge-bug risk. Derived count removes the entire class of bugs across all per-lane PRs. The recent jump from 52→53 via X-9 (`896f366`) is precisely the kind of drift this resolves. |
| D5 | Compliance hard-block = score 0 → standard frontier rejection. Soft-warn = score scaled down + flag persisted to per-fixture sidecar `compliance-meta.json`. **No in-session regen-with-feedback in v1.** | Existing `evaluate_variant.py` treats judge output as scalar score plumbed to the frontier. Adding regen-with-feedback is a substantial new primitive; not needed for v1 since frontier evolution is the regen mechanism. |
| D6 | **REVISED per triage TD-18:** v1 `evaluate_compliance` takes a **single `rule_set_name`** (not a list). `ComplianceRuleSet` schema still accepts a list field, but length is constrained to 1 in v1. Multi-rule-set merge logic + max-severity policy + cross-rule-set merge test deferred to first client onboarding that needs two rule sets. Klinika = `medical_pl`; DWF = `legal_pl`. | Per spec-flow-analyzer P0-2 (original) + triage TD-18 (revised). v1 has zero multi-rule-set consumers; YAGNI on merge logic until a real client demands it. ComplianceRuleSet schema stays unchanged so migration is additive. |
| D7 | Per-client config = versioned YAML in `clients/<slug>/client.yaml`. Loaded into a frozen Pydantic model at lane-start, snapshot recorded in run manifest. **No hot-reload in v1.** Mid-run config drift is fail-loud at finalize | Per spec-flow-analyzer P0-3. Lineage integrity across multi-hour autoresearch runs. |
| D8 | Findings-brief source = **promoted-baseline archive only**. Variant-emitted briefs are visible only inside that variant's evaluation; cross-lane consumption is post-promote | Per spec-flow-analyzer P0-4. Kills orphaned-brief problem; simplifies caching. |
| D9 | Findings-brief consumption = sync file-based; top-K-by-priority batch (default K=3, configurable per client); staleness check via `produced_at` + optional `valid_until`; missing/empty/malformed = lane degrades to standalone | Per spec-flow-analyzer P0-4. Mirrors existing `findings_promotion` file convention. |
| D10 | **REVISED per triage TD-7 + TD-19:** Voice persona migration is a **direct cutover** (no toggle). Pre-U11/U12 precondition: run 5 repeated holdout passes per fixture in `legacy` mode (current per-lane voice reference) to measure within-fixture composite std dev. Set per-fixture regression bar at **`max(5%, 2 × std_dev)`**. CI gate enforces. Merged code has only the `shared` path; if a fixture would regress, fix the persona or fixture before merging — don't merge a toggle. | Per spec-flow-analyzer P0-5 (original) + triage TD-7 + TD-19 (revised). Flat 5% bar was unfalsifiable on noisy fixtures; toggle was dual-codepath shim for a one-time migration. Direct cutover gated on noise-floor-calibrated bar is the production-grade choice. |
| D11 | Holdout fixture provenance: new `data_provenance: real_client \| synthetic \| stub` field in fixture metadata. Archetype-level CI assertion: ≥1 `real_client` fixture per onboarded archetype. `stub`-allowed archetypes flagged explicitly in R26 archetype config | Per spec-flow-analyzer P0-6. Without label, success criterion "real-content fixtures required" is unenforceable. |
| D12 | **REVISED per triage TD-11 (hybrid):** Lane-side `LaneSpec.rubric_ids` carries per-lane compliance rubric IDs (preserves existing per-lane RUBRICS pattern; no substrate invariant change). Rubric prose for compliance rules lives in a single shared `compliance_rules` registry per rule set (file: `compliance/rule_sets/<name>.yaml` per D20). Each lane's compliance rubric prose template resolves to the shared registry entry at evaluation time — so editing a single YAML rule updates all 6 lanes' interpretations. | Same maintainability win as cross-lane primitive (single prose location for Art. 14 amendments) without touching `rubrics.py:1529` invariant. ~50–100 LOC in U5 for the resolve-at-evaluation-time helper. Lower architectural risk than the cross-lane rubric primitive originally proposed. |
| D13 | Static-image composition module = **Pillow** by default. Multi-slide carousel = sequential slide-by-slide generation with brand-anchor passed slide-to-slide (no parallel) | Python-native, well-documented, sufficient for IG/LinkedIn document carousel needs. Sequential ensures brand consistency (slide 2 references slide 1's stamp position). Evaluate Cairo/skia only if Pillow performance becomes blocking. |
| D14 | **REVISED per triage TD-2-revised + TD-9 + TD-17:** Pre-publish human review = email-based, token-signed approve/reject URLs. **Per artifact: primary reviewer signs off; if no response at `escalate_at_pct_sla` (default 50%), parallel email to `pre_publish_reviewer_secondary` — either reviewer's click resolves; first-click wins; secondary's approval logged with `reviewer_role: secondary`.** SLA breach = nag at SLA target, then **auto-pause + operator notification at 2× SLA** (artifact stays in queue until explicit resume/escalate; not destroyed). Manual reviewer rejection IS terminal (artifact discarded, reason logged). Hard-block compliance flags cannot be approved; soft-warn flags MAY be approved (reviewer override logged). **While placeholder rule sets are active (TD-17): mandatory two-reviewer sign-off (both primary AND secondary) + weekly publish rate cap ≤3/client; soft-warn auto-routes to secondary.** **No in-engine edit-feedback loop in v1.** | Per spec-flow-analyzer P1-1 + triage TD-2-revised + TD-9 + TD-17. Auto-pause prevents reviewer-vacation cascade failure; secondary reviewer prevents single-person-dependency; two-reviewer sign-off compensates for placeholder rule sets. |
| D15 | ad_engine variant diversity enforcement = structural N-token-overlap check between hook slides (cheap, deterministic) + R19 rubric dimension. Threshold locked in compliance-judge-anchor work | Per spec-flow-analyzer P1-3. Pure rubric incentive is soft; structural gate forces real diversity. |
| D16 | Foreplay empty result for client domain = lane runs with empty ref set, logs degraded-signal warning, R19 "market-signal alignment" dimension drops to no-op for that variant | Per spec-flow-analyzer P1-3. Mirrors broader Foreplay-signal-reliability parallel-track risk. |
| D17 | Storyboard default `platform_target = youtube_long` when absent. `format_mode + content_denylist` intersection empty space = lane refuses to start with explicit error | Per spec-flow-analyzer P1-4. Fail-loud per CLAUDE.md Rule 12; never silent zero-output run. |
| D18 | Per-lane increments for RUBRICS bumps. Order: article_engine → image_engine → ad_engine → compliance-per-lane (6 sub-units, one per existing content lane). Each increment is a single PR that bumps the assert and adds rubric IDs + `LaneSpec` tuple in the same diff | Per spec-flow-analyzer P1-5. Atomic merge is too risky; per-lane increments are reviewable. D4's derived-count removes the manual lockstep risk. |
| D19 | **REVISED per triage TD-13:** Client #3 onboarding test = (a) structural diff assertion (zero code change in `src/{clients,voice,briefs,compliance,review,ads,generation}/` + `autoresearch/lane_registry.py` + `src/evaluation/rubrics.py` + `autoresearch/archive/v007-curated/workflows/__init__.py` + `tests/`), (b) end-to-end pipeline run against `b2b_tech` stub archetype with stub corpus + stub persona + stub reviewer (auto-approve), AND **(c) onboarding-time clock measured by a teammate/fresh-agent who did NOT author the substrate: timer starts at first `clients/_stub_b2b_tech/client.yaml` commit, ends at first green pipeline run; target <8 hours active.** Recorded in `docs/plans/2026-05-13-002-onboarding-time-measurements.md`. | Per spec-flow-analyzer P1-6 + triage TD-13. Structural diff alone is necessary-but-vacuous; operator-time proves config-only onboarding is actually operationally feasible, not just structurally permitted. |
| D20 | Compliance rule sets are **data-driven** (YAML in `compliance/rule_sets/<name>.yaml`), not Python code | Per spec-flow-analyzer P1-6. Required for the "config-only onboarding" success criterion to hold when client #3 needs a new rule set (e.g., `ftc_consumer_us`). |
| D21 | image_engine quality gate = **score-only, no regen**. First-usable image accepted from fal.ai; vision sub-judge scores it post-hoc as part of variant fitness. No mid-run R2-to-LocalDev storage fallback | Per spec-flow-analyzer P1-2. Avoids new regen primitive (consistent with D5). |
| D22 | image_engine storage backend selection is environment-driven, not lane-driven. Production runs use `R2GenerationStorage`; dev/test runs use `LocalDevPreviewStorage`. Configured via `GOFREDDY_STORAGE_BACKEND` env var read at app init | No mid-run fallback (D21). Matches storyboard's existing convention. |
| D23 | Add `fal_image=N` semaphore to `autoresearch/concurrency.py` before image_engine ships. N = whatever fal.ai's account-level concurrency allows (operator to confirm at implementation). | Per spec-flow-analyzer P2-3. image_engine + ad_engine both hit fal.ai heavily; current global `MAX_PARALLEL_AGENTS=4` can trip fal's 3-failure circuit breaker. **Note on Plan B U9 consistency:** Plan B U9 collapsed 5 per-resource semaphores to one global cap because the only production bottleneck was Claude Max throttling — which the single cap solves. fal.ai is a different shape: hard 3-strike circuit breaker (not throttle) + account-level concurrency limit (not request-rate limit). The new `fal_image` semaphore introduces ONE additional per-resource semaphore for this distinct shape, NOT a reversion of the Plan B U9 collapse. Alternative considered: bump `MAX_PARALLEL_AGENTS` instead and let fal's circuit breaker do the work — rejected because fal trips fatally (not throttled retries) and concurrent claude+codex+fal+judge work would saturate the single cap. |
| D24 | image_engine vision sub-judge backend = **Gemini 2.5**, built fresh in U14 on the Gemini 2.5 SDK as a rubric-driven judge (`src/evaluation/vision_judge.py`, ~80 LOC, new file). NOT a reuse of `image_preview_service.verify_preview()` — that is a fixed 2-axis preview QA (scene_score, style_score), a sibling utility not a base primitive. Used for visual rubrics (carousel arc, brand consistency, info-density legibility) that require multimodal evaluation; text rubrics (alt-text quality, accessibility) stay on claude/opus outer judge. | Visual rubrics can't be scored by a text-only judge. Gemini 2.5 is the same vendor already integrated in `image_preview_service.py` for preview QA, so vendor surface doesn't grow; the new judge primitive is rubric-driven (accepts arbitrary `rubric_id`, emits `dimension_scores`) and dispatched from `evaluate_variant.py` per-rubric. Alternatives: GPT-4V (new vendor surface), claude/opus vision (not currently wired). U14 file list extended with `src/evaluation/vision_judge.py`. |
| D25 | Compliance-judge backend (used by U5's `evaluate_compliance` for the LLM-judged portion of the compliance rubric) = **claude/opus**. Held in a singleton `ComplianceJudgeConfig` module owned by U5 (`src/compliance/judge_config.py`, ~15 LOC). Applies to the 6 lanes that carry compliance gates in v1 (storyboard, article_engine, image_engine, ad_engine, linkedin_engine, x_engine). Geo has no compliance gate in this plan. | Compliance correctness is the most-consequential judge call (false-negative = regulator-flagged published artifact). Frontier-class + diverse from inner-loop (codex/gpt-5.5) per `judge-decisions-2026-05-11.md`. Single shared backend prevents per-lane drift in Art. 14 / legal_pl interpretation. **Why U5-owned singleton instead of a per-lane `LaneSpec` field:** a 6-times-duplicated `LaneSpec.compliance_judge_backend` field would drift; U5 is already the single point of compliance invocation, so the singleton lives there. Operator override available via `COMPLIANCE_JUDGE_BACKEND` / `COMPLIANCE_JUDGE_MODEL` env vars (resolution mirrors `cc212c2` per-step-split conventions). |

## Open Questions

### Resolved During Planning

- **What's the substrate to build on?** v1 `autoresearch/` (D1; Plan B archived per JR 2026-05-13).
- **What's the content-lane pattern to mirror?** x_engine/linkedin_engine (D2).
- **How are new rubrics counted against the existing invariant?** Derived count, not magic number (D4).
- **What's the compliance regen behavior?** Hard-block = frontier rejection; no in-session regen (D5).
- **How do multi-rule-set conflicts resolve?** Don't apply in v1 — single rule set per client (D6 revised per TD-18). Merge policy deferred to first client onboarding with two rule sets.
- **Where does per-client config live?** Versioned YAML, snapshot at run-start, no hot-reload (D7).
- **What's the brief handoff semantics?** Promoted-baseline source; top-K-by-priority batch; degrade gracefully (D8, D9).
- **What's the voice migration safety bar?** Per-fixture `max(5%, 2 × std_dev)` regression tolerance after noise-floor characterization spike; direct cutover (no toggle) (D10 revised per TD-7 + TD-19).
- **How is fixture realism enforced?** `data_provenance` field + archetype CI assertion (D11).
- **What's the human review flow?** Email-based with secondary reviewer escalation at 50% SLA; auto-pause at 2× SLA; manual rejection terminal; two-reviewer sign-off required while placeholder rule sets are active (D14 revised per TD-2-revised + TD-9 + TD-17).
- **What's the diversity enforcement for ad variants?** Structural N-token check + rubric dimension (D15).

### Deferred to Implementation

- **Specific rubric prose content for AE-1..AE-8, IE-1..IE-8, AD-1..AD-8.** Authored alongside each lane unit; ~30–40 lines per rubric × 24 rubrics ≈ 720–960 lines total. Approach: mirror x_engine rubric anchor file shape (`docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`).
- **Polish-language compliance pattern catalogs (`medical_pl`, `legal_pl`).** Data-driven YAML; authoring gated on legal-review owner (parallel-track risk #2 from origin). Placeholder rule sets ship in v1 build; human gate carries risk-control weight until legal-reviewed catalogs land.
- **Exact rubric reweighting math for `storyboard` `format_mode` modes.** `custom_score` callable signature already exists on `LaneSpec`; specific weighting derived during implementation against test fixtures.
- **fal.ai semaphore N value (D23).** Confirmed at implementation by operator dial-up; start at 2, watch for circuit-breaker trips.
- **Per-client config schema final field set.** Implementation iterates with Klinika + DWF instantiation; expected fields enumerated in R26.
- **Compliance rule-set YAML schema.** Pydantic model defined during U5; iterates as rule-set authoring exposes shape needs.
- **Static-image composition module API surface.** Pillow function signatures, layout primitives, brand-stamp injection points — derived during U6 against carousel/hero/ad-static fixtures.

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

### Lane lineup after v1 ships

```
core              (existing infra)
geo               (existing) ← additive: emit findings-briefs
competitive       (existing)
monitoring        (existing) ← additive: emit findings-briefs
storyboard        (existing) ← extended: platform_target + format_mode + voice_corpus
marketing_audit   (existing)
x_engine          (existing) ← voice persona migration (direct cutover, no toggle)
linkedin_engine   (existing) ← voice persona migration (direct cutover, no toggle)
article_engine    ← NEW
image_engine      ← NEW
ad_engine         ← NEW
```

### Dependency graph

```
U0 (Stream A flag graduation — gates everything)
  │
  ▼
Phase A — Foundations
  U1 (RUBRICS derived count)
    │
    ├─→ U2 (Per-client config)
    │     │
    │     ├─→ U3 (Voice persona framework)
    │     │     │   ↳ noise-floor characterization spike (TD-7 precondition)
    │     │     │
    │     │     └─→ U11 (linkedin_engine voice migration — direct cutover, no toggle)
    │     │     └─→ U12 (x_engine voice migration — direct cutover, no toggle)
    │     │
    │     ├─→ U4 (Findings-brief contract)
    │     │     │
    │     │     ├─→ U9  (geo brief emission)
    │     │     └─→ U10 (monitoring brief emission)
    │     │
    │     ├─→ U5 (Compliance framework — single rule set per client v1; hybrid rubric structure)
    │     │     │
    │     │     ├─→ U16 (medical_pl rule set authoring)
    │     │     └─→ U17 (legal_pl rule set authoring)
    │     │
    │     ├─→ U6 (Static-image composition module — Pillow)
    │     │     │
    │     │     └─→ U14 (image_engine lane)
    │     │
    │     └─→ U7 (Pre-publish review service — single module + webhook, secondary reviewer escalation)
    │
    └─→ U8 (Storyboard extension)   ← can run in parallel with U2–U7 once U1 lands
    └─→ U13 (article_engine lane)    ← needs U2, U3, U4, U5
    └─→ U14 (image_engine lane)      ← needs U2, U3, U5, U6
    └─→ U15 (ad_engine lane)          ← needs U2, U3, U5
    │
    └─→ Decision gate (TD-12 per-client phasing): if partner consent + legal-review owner
        for at least one client are not resolved → pause Phase C for blocked client,
        reallocate to whichever is unblocked
    │
    └─→ U18 (Klinika + DWF instantiation)  ← needs U8, U13, U14, U15, U16, U17 + parallel-track
    │                                         risks resolved per affected client
    │
    └─→ U19 (Client #3 CI harness — structural diff + operator-time <8h clock per TD-13)
        ← needs U18
```

### Compliance gate flow (end-to-end)

```
[Variant generates artifact]
        │
        ▼
[In-loop fitness judge applies per-lane <rule_set>_<lane>_* rubrics]
        │
   ┌────┴────┐
   ▼         ▼
[any hard-block]  [soft-warn only or clean]
   │                │
   ▼                ▼
[score 0 →     [score scaled + flag → compliance-meta.json sidecar]
 frontier             │
 rejection]            ▼
                  [Variant promoted (if best-scoring)]
                       │
                       ▼
                  [Pre-publish human review service queues artifact]
                       │
                       ▼
                  [Email to per-client reviewer with token-signed approve/reject URLs]
                       │
                  ┌────┴────┐
                  ▼         ▼
              [Approve]   [Reject — terminal, reason logged]
                  │
                  ▼
              [Publish to channel]
```

### Per-client config shape (R26)

```yaml
# clients/klinika-melitus/client.yaml
slug: klinika-melitus
display_name: Klinika Melitus
archetype: b2c_aesthetics
voice_persona_ref: dr_maria
compliance_rule_sets:        # v1: single rule set per client (D6 revised per TD-18)
  - medical_pl
enabled_channels:
  - storyboard
  - article_engine
  - image_engine
  - ad_engine
  - linkedin_engine
  - x_engine
enabled_platforms_per_channel:
  storyboard: [ig_reels, tiktok, ig_story]
  ad_engine: [meta]
content_denylist:
  - clinical_visuals
  - before_after_imagery
pre_publish_reviewer:
  email: dr.maria@klinikamelitus.pl
  display_name: Dr. Maria Noszczyk
  sla: 48h_business_pl
pre_publish_reviewer_secondary:   # per TD-2 revised: vacation/unavailability fallback
  email: <named-secondary>@klinikamelitus.pl
  display_name: <Named Secondary Reviewer>
  escalate_at_pct_sla: 50         # secondary kicks in at 50% SLA elapsed
weekly_publish_target: 5           # per TD-2: lane stops emitting once met
brand_assets:
  style_guide: clients/klinika-melitus/brand/style-guide.md
  logo: clients/klinika-melitus/brand/logo.svg
  palette: clients/klinika-melitus/brand/palette.json
brief_consumption:
  top_k_per_run: 3
```

## Substrate Consumed from Judge Plan

Parallel plan: `docs/plans/2026-05-13-001-judge-substrate-fix-and-kernel-plan.md` (Judge Substrate Fix + Kernel). The judge plan **explicitly rejects** new lanes from its scope ("would be fresh builds with own design pass"); CE plan owns all new-lane judge wiring. But the judge plan defines primitives this plan consumes. Reconciliation pass landed 2026-05-13 (TD-26).

**Already shipped on main — soft consumes, no gate:**

| ID | Consumed primitive | Source | CE plan touchpoint |
|---|---|---|---|
| S1 | **Per-step model split** — `LaneSpec.inner_backend` + `inner_model` overrides; resolution priority `LaneSpec > CLI flag > EVOLUTION_INNER_* > EVOLUTION_EVAL_*` | `cc212c2` 2026-05-13; `autoresearch/lane_registry.py:69-77` | U13/U14/U15 each set `inner_backend` + `inner_model` per the frontier-only-diverse-from-inner-loop policy (memory: `judge-decisions-2026-05-11.md`) |
| S2 | **Post-rewrite anchor design pattern** — operational definitions + substitution tests + falsifiability requirements + named Score-3 failure modes + anti-gaming clauses | `896f366` 2026-05-13 (13 anchor rewrites: MON-1/3/4/5/6, CI-1/5/6/7, SB-1/2/3/5) | U13/U14/U15 author 24 new rubrics (AE-1..8, IE-1..8, AD-1..8) using this pattern. U5 compliance YAML prose authors follow same pattern. |
| S3 | **RUBRICS=53 baseline** (was 52 when this plan was first drafted) | `896f366` + `204e9a6` | U1 derived-count reference; D4 rationale updated. |
| S4 | **Stream A axis-collapse fix default-on** — escape hatch still exists but escape path is dead in production | `cli/freddy/commands/evaluate.py:215-248` (graduated post-`3b97b3d`) | U0 scope narrowed: removes escape hatch + dead conditionals; no production behavior change. |
| S5 | **`custom_persist_judge_payload` hook** — per-lane sidecar persistence (precedent: monitoring DQS) | `autoresearch/lane_registry.py:84-100, 224` | New lanes optionally wire this hook if they need lane-specific judge-side sidecars (none currently planned but available). |

**Open in judge plan — informational, NOT a gate (decided 2026-05-13):**

| ID | Open primitive | Judge-plan unit | CE plan dependency |
|---|---|---|---|
| **G1** | `dimension_scores` (per-criterion) + `rubric_version` persistence to `autoresearch/archive/*/scores.json`. Currently `dimension_scores: []` (empty) on main; `rubric_hash` is persisted but not the version string. | Judge plan U0.2 (OPEN) | **NOT a gate.** New lanes v1 use aggregate scoring (existing substrate handles it) — per-criterion archive writes are not in U13/U14/U15 scope. If judge plan U0.2 lands during CE plan build, new lanes automatically inherit the schema (same archive writer). If it doesn't, new lanes still ship. Re-evaluate only if a future judge-discrimination analysis requires retroactively populating dimension_scores for the new lanes — then it's a backfill task, not a v1 gate. **Author-side commitment to prevent permanent data loss:** U13/U14/U15 judge prompts request per-criterion `dimension_scores` in the response payload from day 1, even though `evaluate_variant.py` archive write currently drops them (writes empty list per `evaluate_variant.py:1606,1722,1747`). Cost is ~0 LOC in the prompts; benefit is that when U0.2 lands, the payload-side data is already correct and only the archive writer needs to change to start persisting. Otherwise the early-archive cliff (judges aren't re-run cheaply) would silently un-backfill these lanes. |

**Open in judge plan — informational, no gate:**

- Judge plan U0.3 documents 3-level grain (Score 1/3/5) — already implicit in rubric prose; CE plan's new rubrics author against this grain by default.
- Judge plan Phase 2 (validation: archive replay, negative-control fixtures, cross-family κ, Policy Invariance telemetry) — independent of CE plan; can run in parallel.

**Explicitly rejected by judge plan — DO NOT propose for new lanes:**

- **No LANE-9 kernel rubric pattern for new lanes.** Judge plan added X-9; MON-9/GEO-9/CI-9/MA-9 were rejected on 2026-05-13 because the 13 anchor rewrites covered the same failure modes more cheaply. CE plan **does not propose AE-9/IE-9/AD-9**; the 8-rubric-per-lane convention holds.
- **No inline Python module-level trigger lists for compliance** (`MEDICAL_PL_TRIGGERS` / `LEGAL_PL_TRIGGERS` mentioned in judge plan as the inline option). CE plan U5's shared YAML registry (`compliance/rule_sets/<name>.yaml`) is the uncontested authority since MON-9 (the only judge-plan unit that would have used inline triggers) was rejected.

**Resolution at integration time:** if the judge plan amends Phase 2 such that its validation work requires the new-lane archives to write per-criterion `dimension_scores`, that's a hard add to CE plan U13/U14/U15. Re-confirm before U13 starts.

---

## Implementation Units

### Phase A — Foundations (must land before all other phases)

- [ ] **U0: Stream A escape-hatch removal + dead-conditional cleanup**

**Goal:** Stream A axis-collapse fix is **already graduated to default-on on main** (`cli/freddy/commands/evaluate.py:215-248`; documented in the file itself). The escape-hatch env var (`AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=0|off|false|no`) and the legacy broadcast code path still exist for operator rollback. U0 removes both: deletes the escape-hatch branches in `cli/freddy/commands/evaluate.py` + any downstream `AUTORESEARCH_EVAL_FIX_*` conditionals, eliminates the load-bearing-flag concern across D10/D11/D19. **No behavior change in production** — only dead-code cleanup since the fix is already default-on.

**Requirements:** Per triage TD-10. Gates the entire build.

**Dependencies:** None on main; fix already shipped (`3b97b3d`, PR #60) and graduated.

**Files:**
- Modify: `cli/freddy/commands/evaluate.py` — remove `_axis_collapse_fix_enabled()` helper + escape-hatch conditional at lines 215–248; inline the per-criterion path.
- Modify: any other autoresearch call sites reading `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE` / `AUTORESEARCH_EVAL_FIX_HOLDOUT` / `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES` (greppable). Remove the conditional branches; keep the fixed-behavior path.
- Modify: any tests that set/unset these flags — drop the flag setup, keep the test assertions.
- Modify: documentation referencing the flags (search `docs/`) — note graduation.

**Approach:**
- `grep -rn "AUTORESEARCH_EVAL_FIX_" autoresearch/ cli/ src/ tests/ docs/` to enumerate call sites.
- Per call site: delete the conditional, keep the fixed path, delete the legacy path.
- Single PR; ship as a refactor before any Content Engine work begins.

**Execution note:** Test-first — every test that exercises a Stream-A-gated path must continue passing without the flag set. The fix has been default-on for several days, so green tests already prove this; the PR is mechanical cleanup.

**Patterns to follow:** Stream A's existing fix implementations (the flagged paths become the unconditional paths).

**Test scenarios:**
- *Happy path:* All existing tests pass without `AUTORESEARCH_EVAL_FIX_*` env vars set (already true on main; this PR shouldn't change that).
- *Regression:* Run a known fragile fixture (per memory: 6/7 fragile fixtures have min=0 from variant output failure) — behavior matches Stream A's fixed state.
- *Negative case:* Setting `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE=0` is no longer honored (escape hatch removed); test no longer asserts legacy behavior.

**Verification:**
- `grep -r "AUTORESEARCH_EVAL_FIX_" autoresearch/ cli/ src/ tests/` returns no hits (or only documentation references noting removal).
- Full test suite green without the env flags.

---

- [ ] **U1: RUBRICS derived-count refactor**

**Goal:** Replace the current hardcoded `assert len(RUBRICS) == 53` (baseline on main as of 2026-05-13 after `896f366` added X-9 and `204e9a6` settled MA tier-tags) with a derived assertion sourced from `LaneSpec.rubric_ids` tuples. Removes the merge-bug class across all per-lane PRs in this plan.

**Requirements:** Foundational — gates D18 (per-lane increments).

**Dependencies:** None.

**Files:**
- Modify: `src/evaluation/rubrics.py` (current invariant line is `assert len(RUBRICS) == 53, f"Expected 53 rubrics (32 base + 8 MA + 13 X/LI incl. X-9), got {len(RUBRICS)}"` per main; the prior plan reference to "52 / line 1523" is stale)
- Test: `tests/evaluation/test_rubrics_invariant.py` (create)

**Approach:**
- Replace the hardcoded `53` baseline with `sum(len(spec.rubric_ids) for spec in LANES.values())`. Keep the same fail-loud style. Keep the bidirectional cross-check (every `LaneSpec.rubric_ids` ID must exist in `RUBRICS`; sum equals `len(RUBRICS)`).
- Verify all existing tests still pass.

**Patterns to follow:**
- Existing assertion style in `src/evaluation/rubrics.py:1505-1516` (RUBRIC_VERSION derivation).
- CLAUDE.md Rule 12 (fail loud).

**Test scenarios:**
- *Happy path:* Module imports cleanly with no lane changes; assertion passes.
- *Happy path:* Adding a stub LaneSpec with rubric_ids that don't yet have rubric prose → assertion fails with a useful error message.
- *Edge case:* Empty `LANES` dict → assertion passes (no rubrics, no IDs).
- *Integration:* Run full `pytest tests/autoresearch/test_lane_registry.py` and `tests/evaluation/` — no regressions.

**Verification:**
- `python -c "from src.evaluation.rubrics import RUBRICS, RUBRIC_VERSION; print(len(RUBRICS), RUBRIC_VERSION)"` runs without assertion error.
- `pytest tests/evaluation/test_rubrics_invariant.py -v` passes.

---

- [ ] **U2: Per-client config object (R26)**

**Goal:** Land the per-client config schema, loader, and run-manifest snapshot. This is the product's primary onboarding interface.

**Requirements:** R26 (origin). Gates U3, U4, U5, U6, U7 (everything that reads client config).

**Dependencies:** U1.

**Files:**
- Create: `src/clients/config.py` — Pydantic model `ClientConfig` (frozen)
- Create: `src/clients/loader.py` — `load_client_config(slug: str) -> ClientConfig` + snapshot helper
- Create: `clients/klinika-melitus/client.yaml` — first instantiation (data file)
- Create: `clients/dwf-poland/client.yaml` — second instantiation
- Create: `clients/_stub_b2b_tech/client.yaml` — client #3 stub (data file)
- Modify: `autoresearch/run.sh` (or `autoresearch/run.py` if Python-driven) — read `$CLIENT_SLUG` env, load config at preflight
- Test: `tests/clients/test_config.py`

**Approach:**
- `ClientConfig` Pydantic model (frozen, `extra=allow` initially per marketing-audit lesson; tighten later). Fields per R26 high-level design above.
- **Relationship to existing `src/clients/models.py:Client`:** `Client` (existing) carries low-level workspace metadata (`slug`, `domain`, `status`, `created_at`); the new `ClientConfig` extends with content-engine-specific fields (voice_persona_ref, compliance_rule_sets, enabled_channels, content_denylist, pre_publish_reviewer, brand_assets, archetype, brief_consumption). Decision: **coexist with cross-reference.** `ClientConfig` references the existing `Client` by slug; existing `clients/<slug>/config.json` stays as-is for the audit pipeline workflows; new `clients/<slug>/client.yaml` carries Content Engine config. v1.5 can consolidate if the dual-file pattern becomes painful.
- **Archetype enum + stub_allowed flag:** `ClientConfig.archetype: Literal["b2b_regulated", "b2b_tech", "b2c_aesthetics", "b2c_ecommerce", ...]` (Literal extended as new archetypes are added). Optional `archetype_stub_allowed: bool = False` excludes the archetype from D11's CI assertion (≥1 real_client fixture per archetype). v1 sets `stub_allowed=True` only for `b2b_tech` in `_stub_b2b_tech/client.yaml` (U19); Klinika + DWF default to `stub_allowed=False`.
- Loader reads `clients/<slug>/client.yaml`, validates against schema, returns frozen `ClientConfig`.
- At lane-start, snapshot the config into the run manifest (`autoresearch/archive_<lane>/v<NNN>/client-config.snapshot.yaml`).
- At finalize, compare snapshot vs current config-on-disk; fail loud if changed (per D7).

**Execution note:** Test-first for the loader — config validation rules are easier to enforce when tests come first.

**Patterns to follow:**
- Pydantic `model_config = ConfigDict(frozen=True)` precedent (`src/seo/providers/gsc.py:PageSearchMetrics`).
- Run-manifest snapshot pattern (no existing precedent; design from scratch using simple file-write).

**Test scenarios:**
- *Happy path:* Load `clients/klinika-melitus/client.yaml` → valid `ClientConfig` with all expected fields populated.
- *Happy path:* Load `clients/dwf-poland/client.yaml` → valid `ClientConfig`.
- *Edge case:* Missing optional fields (e.g., no `enabled_platforms_per_channel`) → defaults apply.
- *Edge case:* Missing `pre_publish_reviewer_secondary` → loader accepts (secondary is optional in v1; absence triggers fall-back to SLA nag + auto-pause without secondary escalation).
- *Error path:* Missing required field (e.g., no `slug`) → ValidationError with field-specific message.
- *Error path:* Invalid `archetype` value → ValidationError.
- *Integration:* Snapshot config; modify YAML file mid-run; finalize step detects drift and fails loud.
- *Integration:* Two clients reference same `voice_persona_ref` → no error (allowed; provenance metadata logged).

**Verification:**
- `python -c "from src.clients.loader import load_client_config; c = load_client_config('klinika-melitus'); print(c.archetype)"` → `b2c_aesthetics`.
- `pytest tests/clients/test_config.py -v` passes.

---

- [ ] **U3: Voice persona framework (R20)**

**Goal:** Land the voice persona spec (3 fields: `corpus_path`, `voice_rules`, `style_anchors`) and the loader. Consumed by storyboard, article_engine, linkedin_engine, x_engine.

**Requirements:** R20 (origin).

**Dependencies:** U2 (config object references persona by name).

**Files:**
- Create: `src/voice/persona.py` — `VoicePersona` Pydantic model (frozen), loader `load_persona(persona_ref: str) -> VoicePersona`
- Create: `voice_personas/dr_maria.yaml` — Klinika instantiation
- Create: `voice_personas/partner_jamka.yaml` — DWF instantiation
- Create: `voice_personas/_stub_persona.yaml` — client #3 stub
- Test: `tests/voice/test_persona.py`

**Approach:**
- `VoicePersona` schema: `name: str`, `corpus_path: Path`, `voice_rules: list[str]`, `style_anchors: dict[str, str]` (mapping anchor name like `"argumentative-medical-pedagogic"` → prose description).
- Loader reads `voice_personas/<persona_ref>.yaml`, resolves `corpus_path` to an absolute path (validates file exists), returns frozen model.
- Style anchors are referenced by name in lane prompts (e.g., article_engine session.md says "use the `style_anchors.argumentative-medical-pedagogic` voice for blog content").

**Execution note:** Test-first.

**Patterns to follow:**
- `programs/references/voice.md` precedent (x_engine voice substrate, locked via `readonly_subprefixes`).

**Test scenarios:**
- *Happy path:* Load `dr_maria.yaml` → valid `VoicePersona`; `corpus_path` exists; style anchors keyed correctly.
- *Edge case:* Empty `voice_rules` list → loader returns valid persona (no rules enforced at load).
- *Edge case:* Empty `style_anchors` dict → persona is still loadable (lanes that need anchors fail at use, not at load).
- *Error path:* `corpus_path` points to nonexistent file → ValidationError at load.
- *Error path:* Unknown persona ref (file doesn't exist) → FileNotFoundError with helpful message.
- *Integration:* `ClientConfig.voice_persona_ref` resolves through loader to a valid `VoicePersona`.

**Verification:**
- `python -c "from src.voice.persona import load_persona; p = load_persona('dr_maria'); print(p.style_anchors)"` succeeds.
- `pytest tests/voice/test_persona.py -v` passes.

---

- [ ] **U4: Findings-brief contract (R21)**

**Goal:** Land the findings-brief schema (R21 minimum field set), emitter helper, reader helper. Wires into geo + monitoring (U9, U10) and article_engine (U13).

**Requirements:** R21, R23, R24 (origin).

**Dependencies:** U2.

**Files:**
- Create: `src/briefs/schema.py` — `FindingsBrief` Pydantic model (frozen)
- Create: `src/briefs/emitter.py` — `emit_brief(lane_name: str, brief: FindingsBrief, archive_root: Path) -> Path`
- Create: `src/briefs/reader.py` — `read_briefs(source_lane: str, archive_root: Path) -> list[FindingsBrief]`
- Test: `tests/briefs/test_emitter_reader.py`
- Test: `tests/briefs/test_brief_lifecycle.py` (integration — emit then read)

**Approach:**
- `FindingsBrief` fields per R21: `brief_id`, `source_lane`, `priority` (Literal["high", "medium", "low"]), `topic` (title + summary), `target_lanes` (list[str]), `target_formats` (dict[str, str]), `voice_persona_ref` (str), `source_pointers` (list[str | Path]), `success_notes` (str), `produced_at` (datetime), `valid_until` (datetime | None).
- Emitter writes brief as JSON to `autoresearch/archive_<source_lane>/v<NNN>/briefs/<brief_id>.json`. Promoted-baseline only (D8): emitter is called from the lane's promotion-time hook, not from variant evaluation.
- Reader walks `autoresearch/archive_<source_lane>/current_runtime/briefs/*.json`, parses each, returns sorted by priority. Stale briefs (`valid_until < now`) logged + skipped.
- Top-K filter applied by consumer (article_engine reads `ClientConfig.brief_consumption.top_k_per_run`).

**Execution note:** Test-first for the schema and lifecycle.

**Patterns to follow:**
- `FindingsPromotionConfig` precedent (`autoresearch/archive/v007-curated/workflows/specs.py:25-29`) for promote-time hook timing.
- JSONL append-only pattern (`src/common/cost_recorder.py`).

**Test scenarios:**
- *Happy path:* Emit brief → file exists in expected path → read returns identical brief.
- *Happy path:* Emit 5 briefs with mixed priorities → reader returns them sorted high→medium→low.
- *Edge case:* Empty brief directory → reader returns empty list.
- *Edge case:* `valid_until` past current time → reader skips with log warning.
- *Edge case:* Brief with no `valid_until` → never stales.
- *Error path:* Malformed JSON in brief file → reader skips with log warning (graceful degradation per D9).
- *Error path:* Brief with missing required field → reader skips with log warning.
- *Integration:* geo emits → article_engine reads top-K → top-K matches priority order.
- *Integration:* Two source lanes (geo + monitoring) both emit → article_engine reads from both, merges by priority.

**Verification:**
- `pytest tests/briefs/ -v` passes.
- Manual: emit a sample brief and `cat` the JSON to verify shape.

---

- [ ] **U5: Compliance framework primitive (R22 gate 1)**

**Goal:** Land the pluggable compliance rule-set primitive. Rule sets are data-driven YAML; the framework loads them, applies per-lane rubric duplication, and dispatches the in-loop fitness judge.

**Requirements:** R22 (origin), D6 revised (single rule set per client per TD-18), D12 revised (hybrid: per-lane rubric IDs + shared prose registry per TD-11), D20 (data-driven YAML).

**Dependencies:** U1, U2.

**Files:**
- Create: `src/compliance/schema.py` — `ComplianceRule` and `ComplianceRuleSet` Pydantic models (frozen)
- Create: `src/compliance/loader.py` — `load_rule_set(name: str) -> ComplianceRuleSet`
- Create: `src/compliance/judge.py` — `evaluate_compliance(artifact: str, active_rule_sets: list[str], lane: str) -> ComplianceResult`
- Create: `src/compliance/judge_config.py` (~15 LOC, per D25) — `ComplianceJudgeConfig` singleton holding the single backend (`claude/opus`) + model. Read via `get_compliance_judge_config()`; supports env override `COMPLIANCE_JUDGE_BACKEND` / `COMPLIANCE_JUDGE_MODEL`. Imported by `src/compliance/judge.py`; the 6 lanes with compliance gates consume it transitively.
- Create: `compliance/rule_sets/_placeholder_medical_pl.yaml` — placeholder rule set (real authoring in U16, gated on legal review)
- Create: `compliance/rule_sets/_placeholder_legal_pl.yaml` — placeholder rule set (real authoring in U17)
- Modify: `src/evaluation/rubrics.py` — register per-lane compliance rubric duplicates
- Modify: `autoresearch/lane_registry.py` — extend LaneSpec.rubric_ids of touched lanes (later units do the actual wiring)
- Test: `tests/compliance/test_rule_set_loader.py`
- Test: `tests/compliance/test_compliance_judge.py`
- Test: `tests/compliance/test_judge_config.py` — verifies singleton + env override resolution

**Approach:**
- `ComplianceRule`: `id: str`, `pattern: str | list[str]` (regex or pattern list), `severity: Literal["hard_block", "soft_warn"]`, `prose: str` (rubric-style description for judge).
- `ComplianceRuleSet`: `name: str`, `rules: list[ComplianceRule]`, `metadata: dict`.
- `evaluate_compliance(artifact, rule_set_name, lane) -> ComplianceResult` runs **the single active rule set** for the client against the artifact (v1: single rule_set per client per TD-18); returns `ComplianceResult` with overall verdict (`hard_block | soft_warn | clean`) and flag list. `ComplianceRuleSet` schema accepts a list field but v1 constrains length to 1; multi-rule-set merge logic deferred.
- **Hybrid rubric structure (D12 revised per TD-11):** Lane-side `LaneSpec.rubric_ids` carries per-lane compliance rubric IDs like `medical_pl_article_engine_compliance` (one per active rule set per lane, NOT one per individual rule). The per-rule prose lives in the shared `compliance/rule_sets/<name>.yaml` registry. Each lane's rubric prose template resolves to the shared registry entry at evaluation time — so editing one YAML rule updates all 6 lanes' interpretations without touching `LaneSpec.rubric_ids` or `rubrics.py` invariants.
- Rule-set authoring (U16, U17) writes real Polish-language patterns; v1 ships with placeholders so the framework can be tested.

**Execution note:** Test-first.

**Patterns to follow:**
- Slop-gate precedent (x_engine factual-veto split): deterministic regex check separate from LLM. Use this for rules with `pattern` defined.
- `RubricTemplate` shape (`src/evaluation/rubrics.py:16`) for the LLM-judged portion.
- **Post-rewrite anchor design (S2)** — `compliance/rule_sets/<name>.yaml` rule prose must follow `896f366`'s pattern: operational definitions ("a 'cure' claim is …") + substitution tests ("would replacing X with Y change the meaning?") + falsifiability requirements + named Score-3 failure modes + anti-gaming clauses. This makes the compliance judge robust against the same ceiling-bound failure that the 13 anchor rewrites resolved on MON/CI/SB rubrics.

**Test scenarios:**
- *Happy path:* Load `_placeholder_medical_pl.yaml` → valid `ComplianceRuleSet` with rules list.
- *Happy path:* Evaluate clean artifact → verdict `clean`, empty flag list.
- *Happy path:* Evaluate artifact with one hard-block hit → verdict `hard_block`, flag with provenance.
- *Edge case:* `compliance_rule_sets` list with >1 entry in v1 → ValidationError ("v1 supports single rule_set per client; multi-rule-set merge deferred per TD-18").
- *Edge case:* Empty `compliance_rule_sets` list → verdict `clean` (no rules to apply).
- *Error path:* Rule set file missing → `FileNotFoundError`.
- *Error path:* Malformed YAML → `ValidationError`.
- *Error path:* Invalid `severity` value → `ValidationError`.
- *Integration:* Load 2 rule sets simultaneously; both apply to artifact; merge produces deterministic outcome.

**Verification:**
- `pytest tests/compliance/ -v` passes.
- `python -c "from src.evaluation.rubrics import RUBRICS; print(len([r for r in RUBRICS if 'medical_pl' in r or 'legal_pl' in r]))"` shows expected count after rule-set registration.

---

- [ ] **U6: Static-image composition module**

**Goal:** Net-new Pillow-based module for multi-slide carousel layout, text overlays, brand stamping. Consumed by image_engine (U14) and potentially ad_engine (U15) for ad statics.

**Requirements:** R12, R13 (origin). Backs image_engine's composed-end-to-end output.

**Dependencies:** U2 (for brand_assets path resolution).

**Files:**
- Create: `src/generation/image_composer.py` — `ImageComposer` class with composition primitives
- Create: `src/generation/image_layout.py` — layout primitives (slide grid, text overlay positioning, brand stamp anchors)
- Create: `tests/generation/test_image_composer.py`
- Create: `tests/generation/test_image_layout.py`

**Approach:**
- `ImageComposer.compose_single(prompt_image_path: Path, text_overlay: str | None, brand_stamp: BrandStamp) -> Path` — generates a single composed image.
- `ImageComposer.compose_carousel(slides: list[CarouselSlide], brand: BrandSpec) -> list[Path]` — generates a multi-slide carousel; each slide receives the previous slide's brand-anchor metadata to ensure consistency (sequential per D13).
- `compose_doc_carousel(slides: list[DocSlide], brand: BrandSpec) -> list[Path]` — LinkedIn document-carousel variant (1:1 ratio, info-density-friendly text layout).
- Per-format dimensions: `ig_single` 1:1 1080×1080, `ig_carousel` 1:1 1080×1080, `ig_story` 9:16 1080×1920, `li_doc_carousel` 1:1 1080×1080, `hero_banner` configurable, `ad_static` per-platform spec.
- Brand stamp: logo + brand color stripe + typography defaults from `BrandSpec` (loaded from `clients/<slug>/brand/`).

**Execution note:** Test-first; image diff testing via reference PNGs in `tests/generation/fixtures/`.

**Patterns to follow:**
- `src/generation/composition.py` for FFmpeg subprocess wrapping conventions (but the actual composition is Pillow, not FFmpeg).
- `src/generation/caption_presets.py` for typography preset shape (but new presets are image-format-specific).

**Test scenarios:**
- *Happy path:* Compose single image with text overlay → output PNG exists, dimensions match format spec.
- *Happy path:* Compose 5-slide carousel → 5 PNGs produced, each with consistent brand stamp position.
- *Happy path:* Compose LinkedIn document carousel (8 slides) → all 8 PNGs produced, info-density layout applied.
- *Edge case:* Empty text overlay → image generated without overlay box.
- *Edge case:* Single-slide carousel → exactly 1 PNG.
- *Edge case:* Brand spec missing logo → fallback to text-only brand stamp.
- *Edge case:* Text overlay too long for slide → auto-wrap or truncate (locked at implementation).
- *Error path:* Source prompt-image file missing → clear error.
- *Error path:* Brand spec missing required field → ValidationError.
- *Integration:* Compose carousel; load first slide; verify brand stamp matches anchor metadata passed to second slide.

**Verification:**
- `pytest tests/generation/test_image_composer.py -v` passes.
- Manual: run `compose_carousel` against a sample brand; inspect output PNGs.

---

- [ ] **U7: Pre-publish human review service (R22 gate 2)**

**Goal:** Land the email-based human review flow. Token-signed approve/reject URLs; SLA-driven nag + auto-reject; terminal rejection; audit trail.

**Requirements:** R22 gate 2 (origin), D14.

**Dependencies:** U2.

**Files:**
- Create: `src/review/service.py` — single ~200-LOC module (per TD-20): `ReviewService` class with `submit_for_review`, `process_decision`, `check_sla`, signed-URL helper, audit-log JSONL append, simple email sender (reuses existing `src/api/` email infra if present, otherwise SMTP via existing config). Token signing logic inline via `hmac` stdlib.
- Create: `src/api/review_webhook.py` — webhook endpoint for approve/reject URL clicks (confirmation GET → POST with CSRF token per Plan-level Threat Model)
- Test: `tests/review/test_review_service.py` — single test file covering submit/approve/reject/SLA-breach/token-tamper/secondary-escalation scenarios

**Approach:**
- `submit_for_review(artifact, client_config) -> ReviewRequest`: writes artifact to review-queue dir, generates signed approve+reject URLs, sends email to `client_config.pre_publish_reviewer.email` via the configured email channel.
- `process_decision(token, decision, reason)`: verifies token signature, writes to audit log, updates artifact state.
- `check_sla()`: scheduled (cron or systemd timer) job that scans pending reviews; sends nag emails at 25/50/100% of SLA elapsed; auto-rejects at 2× SLA.
- Audit log fields: `artifact_id`, `artifact_hash`, `client_slug`, `reviewer_email`, `decision` (`approved | rejected | sla_breach`), `decision_timestamp`, `reason_text`, `sla_target`, `submitted_at`, `compliance_flags_at_submission` (from U5).
- Email template: artifact preview (link to viewer), approve button, reject button (with reason text field), SLA reminder. **Compliance flags from `compliance-meta.json` are rendered in the email body** with rule-set provenance and per-rule prose, so the reviewer always sees what triggered.
- **Soft-warn vs hard-block in review:** Hard-block flags cannot be approved (the approve URL refuses with a clear error). Soft-warn flags MAY be approved; the approve token captures a `reviewer_override: true` field in the audit log so soft-warn approvals are clearly distinguished from clean approvals. Per-rule severity comes from the rule-set definition (D6).
- **Secondary reviewer escalation (per TD-2 revised):** At `escalate_at_pct_sla` (default 50%) of SLA elapsed without primary-reviewer response, the service sends a parallel email to `pre_publish_reviewer_secondary.email` (when defined in R26 ClientConfig) with the same token URLs. Either reviewer's click resolves the artifact; whoever clicks first wins; subsequent clicks return "already decided". Secondary reviewer's approval is logged with `reviewer_role: secondary` for audit trail. Without a secondary defined, fall back to the SLA nag + auto-pause at 2× SLA.
- **Weekly publish target (per TD-2):** lane stops emitting new ship-candidates once `weekly_publish_target` from R26 ClientConfig is met for the week. Resets on Monday in client's timezone. Right-sizes engine throughput to reviewer capacity.
- **CSRF / email-prefetcher mitigation:** approve/reject URLs land on a confirmation page (safe GET); the actual state mutation is a POST with a fresh CSRF token. Mitigates corporate-email-scanner / antivirus auto-fires.
- **Single-use token enforcement:** server-side nonce table or audit-log idempotency check before state change. Tokens are constant-time-compared.
- **Token TTL:** matches the per-client SLA (cap at 7 days); expiry equivalent to "SLA breach + grace."
- **Reviewer email change protection:** any edit to `client.yaml:pre_publish_reviewer.email` requires CODEOWNERS review on the `clients/` path and an out-of-band confirmation step (e.g., emails to both old and new addresses).
- No in-engine edit-feedback loop (D14): rejection is terminal; reviewer manually re-uploads to get edits.

**Execution note:** Test-first for token signing and audit log; email delivery tested with `FakeEmailSender` in unit tests.

**Patterns to follow:**
- Marketing audit ship-gate halt pattern (closest precedent, but mostly net-new).
- `src/common/cost_recorder.py` JSONL append pattern for audit log.

**Test scenarios:**
- *Happy path:* Submit artifact → email sent with token-signed URLs → reviewer clicks approve → audit log records `approved` decision.
- *Happy path:* Submit artifact → reviewer clicks reject with reason → audit log records `rejected` with reason.
- *Edge case:* Reviewer clicks both approve and reject buttons (in sequence) → second click rejected as state-invalid (artifact already decided).
- *Edge case:* Reviewer clicks expired token → URL returns "token expired" error; nag email sent.
- *Edge case:* SLA = `48h_business_pl` → 25/50/100% nag emails sent at correct local-time intervals (mock time-of-day).
- *Error path:* Tampered token → signature verification fails → 403 response.
- *Error path:* Email send failure → submission retries with exponential backoff; after 3 failures, alert operator.
- *Integration:* End-to-end flow with mock email + real audit log → all expected entries written.
- *Integration:* SLA breach at 2× → auto-reject recorded; reviewer no longer able to approve.

**Verification:**
- `pytest tests/review/ -v` passes.
- Manual: submit a test artifact; verify email arrives; click approve; verify audit log.

---

- [ ] **U7b: Playwright site render utility (R27)**

**Goal:** Land the shared site-rendering utility that `site_engine` (U15b) and any future visual-eval lane consume. Headless Chromium via Playwright; configurable viewport; font-load wait; screenshot capture; section-snippet rendering (wraps a section's HTML+CSS+JS in a minimal host page with the client's brand tokens for accurate rendering).

**Requirements:** R27.

**Dependencies:** U2 (per-client config — reads `brand_tokens` for the host-page shell).

**Files:**
- Create: `src/generation/site_render.py` (~150 LOC). `SiteRenderer` class:
  - `__init__(self, viewports: list[ViewportSpec] = DEFAULT_VIEWPORTS)` — defaults to `[("desktop", 1440, 900), ("mobile", 375, 812)]`
  - `render_section(self, section_html: str, section_css: str, section_js: str, brand_tokens: BrandTokens) -> RenderResult` — wraps in a host page, launches headless Chromium, waits for `document.fonts.ready` + 300ms settle, captures screenshot + DOM snapshot
  - `RenderResult` dataclass: `screenshot_paths: dict[viewport_name, Path]`, `dom_snapshot: str`, `console_errors: list[str]`, `render_time_ms: int`
  - Cost recording via `cost_recorder.record("playwright", "render", cost_usd=0.0, ...)` (Playwright is local; cost recorded for time-budget accounting, not money)
  - Circuit breaker (`CircuitBreaker(failure_threshold=3, reset_timeout=60, name="site_render")`) wrapping the Chromium subprocess launch
- Create: `tests/generation/test_site_render.py` (~100 LOC). Tests cover: minimal section renders successfully; missing font does not hang (timeout enforced); console error from broken JS surfaces in `console_errors`; circuit breaker opens on 3 launch failures.
- Modify: `pyproject.toml` — add `playwright>=1.45` to `[dependency-groups.dev]` (Playwright is dev-tier — never invoked from production API path).
- Modify: `.github/workflows/test.yml` — add `playwright install chromium` step before pytest runs.

**Approach:**
- Headless Chromium only (Firefox / WebKit deferred — no client need in v1).
- Host page is minimal: HTML5 doctype, `<meta viewport>`, brand-token `<style>` block injected, then the section under `<main>`. No analytics, no third-party scripts.
- Screenshot is full-section (not full-page) via `page.locator('main > *').screenshot()`.
- DOM snapshot captures the *post-render* DOM (after JS executes) so the audit utility (U7c) can analyze the actual rendered tree, not just the source HTML.
- Console-error capture wires `page.on("console")` for severity ≥ warning.
- Font-load wait pattern mirrors `/tmp/pw-shoot/og-render.mjs` from the 2026-05-13 landing-page session (`await page.evaluate(() => document.fonts.ready)`).

**Patterns to follow:**
- `src/generation/fal_client.py` circuit-breaker pattern (3-failure threshold, ModerationBlockedError is fatal not breaker-counted — adapt: Chromium launch failure IS breaker-counted, but a section that renders with console errors is NOT a failure).
- `src/common/cost_recorder.py` JSONL append (cost=0.0 for local renders, kept for budget-accounting symmetry with other generators).
- `src/generation/composition.py` FFmpeg-subprocess pattern (clean shutdown on timeout, structured error surface).

**Test scenarios:**
- *Happy path:* Render a minimal hero section → screenshot file exists + DOM snapshot captured + zero console errors.
- *Happy path:* Render a section with custom font in brand_tokens → font loaded before screenshot.
- *Edge case:* Section JS throws → `console_errors` non-empty; screenshot still captured.
- *Edge case:* Section CSS references undefined token → render proceeds with browser-default; warning surfaced in console_errors.
- *Error path:* Chromium binary missing → clear error message ("run `playwright install chromium`").
- *Error path:* 3 consecutive launch failures → circuit breaker opens; subsequent calls fail fast.
- *Performance:* Single-section render ≤ 2.5s p95 on dev hardware.

**Verification:**
- `pytest tests/generation/test_site_render.py -v` passes.
- Manual: render a section from the 2026-05-13 landing page; compare screenshot to live page (pixel diff < 5%).

**Reversibility:** Fully reversible — module is additive. Removing it un-blocks only U7c and U15b (which depend on it).

---

- [ ] **U7c: Site a11y + perf audit utility (R28)**

**Goal:** Land the shared site-audit utility that returns structured a11y + perf JSON for any rendered section. Consumed by `site_engine` SE-6 (a11y) + SE-7 (perf) judges.

**Requirements:** R28.

**Dependencies:** U7b (audit operates on `RenderResult` from U7b).

**Files:**
- Create: `src/generation/site_audit.py` (~200 LOC).
  - `audit_a11y(dom_snapshot: str, screenshot_path: Path) -> A11yReport` — wraps axe-core CLI (`@axe-core/cli`) invocation against the rendered DOM; parses violations by severity (`minor`, `moderate`, `serious`, `critical`).
  - `audit_perf(render_result: RenderResult) -> PerfReport` — Lighthouse-equivalent metrics extracted from Playwright's `page.metrics()` plus a budget-check against per-section-type budgets (e.g., hero ≤ 80KB, faq ≤ 30KB, cta ≤ 20KB).
  - `A11yReport` dataclass: `violations: list[AxeViolation]`, `passes: int`, `incomplete: int`, `severity_counts: dict[str, int]`, `wcag_aa_pass: bool`.
  - `PerfReport` dataclass: `fcp_ms: int`, `cls: float`, `tbt_ms: int`, `payload_kb: int`, `budget_pass: bool`, `budget_breakdown: dict`.
- Create: `tests/generation/test_site_audit.py` (~120 LOC). Tests cover: clean section → zero violations; section with skipped heading level → moderate violation surfaces; section with low-contrast text → serious violation; perf budget enforcement.
- Modify: `pyproject.toml` — add `@axe-core/cli` to dev-dependencies (Node subprocess; installed via `npm install -g @axe-core/cli` in CI; document in onboarding).
- Modify: `.github/workflows/test.yml` — add Node setup + `npm install -g @axe-core/cli` step.

**Approach:**
- axe-core CLI invoked as subprocess; output is JSON; parsed via stdlib `json`.
- Severity bands map to rubric scores: 0 violations ≥ severity moderate → SE-6 ≥ 4; any ≥ moderate → SE-6 ≤ 3; any ≥ critical → SE-6 = 1 (structural fail).
- Perf budgets per section type live in `src/generation/site_audit.py:PERF_BUDGETS` dict; overridable per-client via `client.yaml:site_engine.perf_budget_override` if a client legitimately needs a heavier section type (e.g., interactive product configurator).
- Lighthouse-equivalent metrics computed from Playwright's `page.metrics()` + DOM size + transferred byte count. Full Lighthouse subprocess deferred to v1.5 (heavier toolchain; current Playwright metrics adequate for SE-7 calibration).

**Patterns to follow:**
- Subprocess + structured JSON output mirrors `src/audit/tools/serpapi_ads.py` graceful-degradation pattern (when subprocess fails, return `degraded=True` report with reason; do not crash the lane).
- Budget-with-override pattern mirrors how `compliance_rules` rule-sets carry per-client override paths (TD-11).

**Test scenarios:**
- *Happy path:* Clean section → 0 violations ≥ moderate; FCP < 1500ms; budget pass.
- *Happy path:* Section with proper semantic HTML + AA contrast → `wcag_aa_pass: true`.
- *Edge case:* Section with heading-skip → 1 moderate violation; SE-6 floor ≤ 3.
- *Edge case:* Section with 4.4:1 contrast on body text → 1 serious violation.
- *Edge case:* Section with `prefers-reduced-motion` honored → no motion-violation flag.
- *Error path:* axe-core CLI missing → clear error ("run `npm install -g @axe-core/cli`"); audit returns `degraded=true` with reason; site_engine treats SE-6 as `n/a` rather than failing the variant.
- *Error path:* Section payload > budget → `budget_pass: false`; SE-7 floor ≤ 3.

**Verification:**
- `pytest tests/generation/test_site_audit.py -v` passes.
- Manual: run audit on the 2026-05-13 landing-page hero section; compare violations against manual axe DevTools run.

**Reversibility:** Fully reversible — additive module. Removing it un-blocks only U15b's SE-6/SE-7 scoring; site_engine can still ship with those axes deferred or hand-graded if this utility regresses.

---

### Phase B — Storyboard Extension + Existing-Lane Touches

- [ ] **U8: Storyboard extension (R1–R4)**

**Goal:** Extend the existing `storyboard` lane with `platform_target` (5 values) + `format_mode` (3 values) + voice corpus input. Apply per-client content_denylist enforcement.

**Requirements:** R1, R2, R3, R4.

**Dependencies:** U2, U3, U5.

**Files:**
- Modify: `autoresearch/archive_storyboard/current_runtime/workflows/storyboard.py` — add `configure_env` env-passing for `STORYBOARD_PLATFORM_TARGET`, `STORYBOARD_FORMAT_MODE`
- Modify: `autoresearch/archive/v007-curated/workflows/storyboard.py` — same edits (the two copies have diverged on `stall_limit` 10 vs 5 and on `snapshot_evaluations` shape; reconcile to current_runtime as the source of truth, then propagate any additional differences as part of this unit)
- Modify: `autoresearch/run.sh` and/or the CLI parsing entrypoint (likely `autoresearch/run.py` Typer commands; confirm at implementation) — add `--platform_target` and `--format_mode` flags that set `STORYBOARD_PLATFORM_TARGET` / `STORYBOARD_FORMAT_MODE` env vars BEFORE `configure_env(client)` runs in the lane workflow
- Modify: `autoresearch/archive_storyboard/current_runtime/programs/storyboard-session.md` — parametrize via `{platform_target}`, `{format_mode}` template variables; conditional sections per mode
- Modify: `autoresearch/lane_registry.py` — extend storyboard `LaneSpec` with `custom_score` callable for `format_mode`-based rubric reweighting (D17 fail-loud on empty denylist+mode intersection)
- Create: `autoresearch/archive_storyboard/current_runtime/templates/storyboard/skeleton-narrative.md` — cold-start skeleton
- Create: `autoresearch/archive_storyboard/current_runtime/templates/storyboard/skeleton-educational.md`
- Create: `autoresearch/archive_storyboard/current_runtime/templates/storyboard/skeleton-brand_authority.md`
- Create: `autoresearch/eval_suites/storyboard_short_form_klinika.json` — Klinika short-form aesthetic creator fixture (educational mode)
- Create: `autoresearch/eval_suites/storyboard_long_form_dwf.json` — DWF LinkedIn legal partner fixture (brand_authority mode)
- Modify: `autoresearch/eval_suites/search-v1.json` — add new fixture references with `data_provenance` field (D11)
- Test: `tests/autoresearch/test_storyboard_extension.py`

**Approach:**
- Mirror x_engine `configure_env` pattern for new env vars (`$STORYBOARD_PLATFORM_TARGET`, `$STORYBOARD_FORMAT_MODE`, `$STORYBOARD_VOICE_PERSONA_REF`).
- Session.md gets conditional blocks per `format_mode`: `narrative` (current behavior), `educational` (relaxed SB-3/SB-4, info-density check), `brand_authority` (upweighted SB-1/SB-5, voice corpus anchoring).
- `custom_score` callable on `LaneSpec` reweights the SB-1..SB-8 axes per `format_mode`. Existing fixtures (narrative mode) unaffected.
- Per-client content_denylist consulted at agent prompt time (denied content types injected as hard constraints).
- D17: lane refuses to start when `format_mode + content_denylist` intersection is empty; explicit error message names the blocked content types.

**Execution note:** Characterization tests first — capture current storyboard behavior in `narrative` mode before adding new modes, ensuring no regression.

**Patterns to follow:**
- x_engine `configure_env` + env-passing (`autoresearch/archive_x_engine/current_runtime/workflows/x_engine.py:96-101`).
- linkedin_engine cold-start skeleton precedent (`templates/linkedin_engine/skeleton-short_take.md` per memory).
- `custom_score` callable signature on `LaneSpec` (`autoresearch/lane_registry.py:35`).

**Test scenarios:**
- *Happy path:* Run storyboard with `STORYBOARD_PLATFORM_TARGET=ig_reels`, `STORYBOARD_FORMAT_MODE=educational` → produces structurally-valid storyboard JSON.
- *Happy path:* Run with `brand_authority` mode + valid voice persona → SB-1/SB-5 axes upweighted in scoring.
- *Happy path:* Run with `narrative` mode (default) → identical scoring to pre-extension baseline (regression check).
- *Edge case:* `STORYBOARD_PLATFORM_TARGET` absent → defaults to `youtube_long` (D17).
- *Edge case:* `educational` mode + `content_denylist: [clinical_visuals]` for Klinika → lane runs, denied content types injected as hard constraints in prompt.
- *Error path:* `format_mode + content_denylist` empty space (e.g., a hypothetical mode that requires only-clinical and denylist denies clinical) → lane refuses with explicit error.
- *Error path:* Voice persona referenced in `brand_authority` mode but corpus is empty → lane fails loud with message naming the persona.
- *Integration:* Klinika short-form fixture passes structural gate with `educational` mode + Klinika denylist.
- *Integration:* DWF long-form fixture passes with `brand_authority` mode + Jamka voice persona.

**Verification:**
- `pytest tests/autoresearch/test_storyboard_extension.py -v` passes.
- Manual: run `autoresearch/run.sh storyboard --client klinika-melitus --platform_target ig_reels --format_mode educational` end-to-end; inspect output for clinical-visual absence.

---

- [ ] **U9: geo lane brief emission (additive)**

**Goal:** Extend `geo` lane to emit findings-briefs at promotion time. Briefs contain SEO topic identification + recommended target lanes.

**Requirements:** R23 (origin).

**Dependencies:** U4.

**Files:**
- Modify: `autoresearch/archive_geo/current_runtime/workflows/geo.py` — add brief emission in promotion hook (likely `custom_promote` callable on LaneSpec or session-end hook)
- Modify: `autoresearch/archive_geo/current_runtime/programs/geo-session.md` — agent prompt instructs writing brief-candidates to a side-channel file during session
- Test: `tests/autoresearch/test_geo_brief_emission.py`

**Approach:**
- Brief emission is **promote-time only** (D8). Hook into the existing promotion flow; on promote, walk the variant's session output for brief-candidates and serialize via `src/briefs/emitter.py`.
- Agent prompt change: storyboard-style hint that "if you identified a high-priority SEO topic during this run, write it to `session/brief_candidates.jsonl`".
- Briefs include `target_lanes=["article_engine"]` and `target_formats={"article_engine": "blog"}` by default; agent can override if topic better suits LinkedIn Article.

**Execution note:** Test-first.

**Patterns to follow:**
- Existing `findings_promotion` promote-time hook (`promote_findings.py`).
- Emitter helper from U4.

**Test scenarios:**
- *Happy path:* geo variant produces 3 brief-candidates → 3 briefs emitted to `autoresearch/archive_geo/v<NNN>/briefs/`.
- *Happy path:* Variant rejected by frontier → no briefs emitted (D8 promoted-baseline only).
- *Edge case:* Variant produces 0 brief-candidates → no briefs emitted, no error.
- *Edge case:* Malformed brief-candidate JSONL → skipped with log warning (don't fail the promotion).
- *Integration:* Article_engine reader picks up the emitted briefs in next run.

**Verification:**
- `pytest tests/autoresearch/test_geo_brief_emission.py -v` passes.
- Manual: promote a geo variant; verify briefs exist at the expected path.

---

- [ ] **U10: monitoring lane brief emission (additive)**

**Goal:** Extend `monitoring` lane to emit findings-briefs at promotion time. Briefs contain regulatory events / news triggers.

**Requirements:** R23 (origin).

**Dependencies:** U4.

**Files:**
- Modify: `autoresearch/archive_monitoring/current_runtime/workflows/monitoring.py` — promotion hook for brief emission
- Modify: `autoresearch/archive_monitoring/current_runtime/programs/monitoring-session.md` — agent prompt for brief-candidate writing
- Test: `tests/autoresearch/test_monitoring_brief_emission.py`

**Approach:** Mirror U9. Briefs from monitoring carry `target_lanes=["article_engine"]` (e.g., a KSeF deadline → Polish sector explainer for DWF) and may also target storyboard/linkedin_engine for short-form amplification (consumer choice).

**Execution note:** Test-first.

**Patterns to follow:** U9.

**Test scenarios:** Mirror U9 with monitoring-shaped brief content (regulatory events, news triggers).

**Verification:** `pytest tests/autoresearch/test_monitoring_brief_emission.py -v` passes.

---

- [ ] **U11: linkedin_engine voice persona migration**

**Goal:** Migrate `linkedin_engine` from per-lane voice references to the shared voice persona spec (R20). Honor 5% regression bar (D10).

**Requirements:** R20 (origin), D10.

**Dependencies:** U3.

**Files:**
- Modify: `autoresearch/archive_linkedin_engine/current_runtime/workflows/linkedin_engine.py` — `configure_env` reads `$LINKEDIN_ENGINE_VOICE_PERSONA_REF` from client config and resolves to the shared persona spec (replaces per-lane voice reference)
- Modify: `autoresearch/archive_linkedin_engine/current_runtime/programs/linkedin_engine-session.md` — voice-substrate sourced from shared persona spec only (legacy per-lane voice reference removed in same PR)
- Modify: `autoresearch/lane_registry.py` — extend linkedin_engine `LaneSpec` with `readonly_subprefixes` covering shared voice substrate
- Create: `docs/plans/2026-05-13-002-noise-floor-baselines.md` — pre-migration baselines + per-fixture regression bars (`max(5%, 2 × std_dev)` per fixture, per TD-7 precondition)
- Create: `tests/autoresearch/test_linkedin_engine_voice_migration.py`

**Approach:**
- **Direct cutover (no toggle) per TD-19:** linkedin_engine moves from its per-lane voice reference (`programs/references/voice.md`) to consuming the shared persona spec from `src/voice/persona.py` via the `LINKEDIN_ENGINE_VOICE_PERSONA_REF` env var resolved at lane start.
- Merged code has only the `shared` path. The legacy per-lane voice file is deleted in the same PR (or left as historical and routed-around — implementation decides).
- **CI gate (D10 revised per TD-7):** per-fixture regression bar at `max(5%, 2 × std_dev)`, calibrated by the noise-floor characterization spike (precondition above). Run the migrated lane against existing fixtures; merge blocked if any fixture exceeds the bar.

**Execution note:** **Characterization-first** — capture current per-fixture holdout scores in `legacy` mode before the migration code lands. Use the captured baselines as the regression-bar reference.

**Precondition (per TD-7, hard gate before U11/U12 begins):** run 5 repeated holdout passes on each linkedin_engine fixture in `legacy` mode to measure within-fixture composite variance. Compute per-fixture std dev. Set the regression bar for THIS fixture at `max(5%, 2 × std_dev)`. Record the baselines + per-fixture bars in `docs/plans/2026-05-13-002-noise-floor-baselines.md`. **Do not start the migration code until baselines are recorded.** If skipped, the regression bar falls back to flat 5% which is unfalsifiable per spec-flow-analyzer.

**Patterns to follow:**
- x_engine voice substrate convention (`programs/references/voice.md` locked via `readonly_subprefixes`).
- `voice.md` precedent + per-lane evolvable session.md content.

**Test scenarios:**
- *Happy path (pre-merge baseline run):* 5 repeated holdout passes with the original legacy voice → per-fixture std dev recorded in `noise-floor-baselines.md`.
- *Happy path (post-migration):* lane runs against shared persona, per-fixture composite within `max(5%, 2 × std_dev)` of legacy baseline.
- *Error path:* `LINKEDIN_ENGINE_VOICE_PERSONA_REF` resolves to a persona with no corpus → fail loud naming the persona.
- *Error path:* Merged migration regresses a fixture beyond per-fixture bar → CI fails, merge blocked; remediate persona or fixture before re-attempt.
- *Integration:* Run existing linkedin_engine holdout fixtures against shared persona; verify per-fixture bar met across all fixtures.
- *Integration:* `readonly_subprefixes` blocks meta-agent from editing shared voice substrate.

**Verification:**
- `pytest tests/autoresearch/test_linkedin_engine_voice_migration.py -v` passes.
- CI regression gate green: linkedin_engine fixtures in `shared` mode within 5% of `legacy` baseline.

---

- [ ] **U12: x_engine voice persona migration**

**Goal:** Migrate `x_engine` from per-lane voice references to shared voice persona spec. Same pattern as U11.

**Requirements:** R20 (origin), D10.

**Dependencies:** U3.

**Files:** Mirror U11 against `autoresearch/archive_x_engine/`.

**Approach:** Mirror U11.

**Execution note:** Characterization-first.

**Patterns to follow:** U11.

**Test scenarios:** Mirror U11.

**Verification:** Mirror U11.

---

### Phase C — New Lanes

- [ ] **U13: article_engine lane (R5–R10)**

**Goal:** Land the new `article_engine` lane. Produces blog + LinkedIn Article from topic + voice + source material + optional findings-brief.

**Requirements:** R5, R6, R7, R9, R10. R8 explicitly dropped per origin doc.

**Dependencies:** U2, U3, U4, U5. No judge-plan gate (G1 reclassified as informational per Substrate Consumed section); aggregate scoring sufficient for v1.

**Judge wiring (per Substrate-consumed S1 + S2):**
- `inner_backend = "codex"`, `inner_model = "gpt-5.5"` — frontier-only per memory `judge-decisions-2026-05-11.md`; diverse from any DeepSeek/Claude inner-loop. Set statically on `LaneSpec` per `cc212c2` priority (mirrors geo + competitive pattern at `lane_registry.py:174-175, 206-207`). **No automatic cyber-filter fallback exists in the substrate** — `ModerationBlockedError` is raised by image/video/audio backends only, never by text inner-session agents; codex cyber-flag rejection produces a session marker, not a runtime exception the harness can catch. If U13 Phase D smoke shows codex hard-rejects article content on known-clean Klinika/DWF topics, swap statically to `inner_backend = "claude"`, `inner_model = "sonnet"` via a one-line `LaneSpec` edit + redeploy. (A dynamic detector + auto-fallback wrapper would be a substrate primitive worth ~1 week of work and is **explicitly deferred to v1.5** if smoke shows we need it.)
- Outer judge backend: claude/opus (frontier, diverse from inner-loop). Critique backend: codex/gpt-5.5 via `CRITIQUE_BACKEND` env (existing default).
- Compliance-judge backend: per D25 (single `claude/opus` across all lanes with compliance gates, held in U5's `ComplianceJudgeConfig` singleton; no per-lane override).
- AE-1..AE-8 rubric anchors follow the post-rewrite design (S2): operational definitions + falsifiability + named Score-3 failure modes + anti-gaming clauses. **Do NOT propose AE-9 kernel rubric** (judge plan rejected the LANE-9 pattern for 4 of 5 lanes; 8-rubric convention holds).

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/article_engine.py` (~200 LOC, mirror x_engine.py)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_article_engine.py` (~250 LOC, mirror session_eval_x_engine.py)
- Create: `autoresearch/archive/v007-curated/programs/article_engine-session.md` (~300 LOC, agent prompt)
- Create: `autoresearch/archive/v007-curated/programs/article_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/article_engine/skeleton-blog.md` (cold-start)
- Create: `autoresearch/archive/v007-curated/templates/article_engine/skeleton-linkedin_article.md`
- Modify: `autoresearch/lane_registry.py` — add `article_engine` `LaneSpec` with `rubric_ids=("AE-1", ..., "AE-8")`, `readonly_subprefixes` for workflow + session_eval + shared voice/brief/compliance substrate
- Modify: `src/evaluation/rubrics.py` — add AE-1..AE-8 rubric prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py` — register `article_engine` SPEC
- Create: `autoresearch/eval_suites/article_engine_klinika_procedure.json` — Klinika procedure-page fixture (real client content per D11)
- Create: `autoresearch/eval_suites/article_engine_dwf_kse.json` — DWF KSeF regulatory explainer fixture (real client content)
- Modify: `autoresearch/eval_suites/search-v1.json` — add new fixtures
- Create: `tests/autoresearch/test_article_engine_substrate.py` (~125 LOC, mirror test_x_engine_substrate.py)
- Create: `docs/plans/2026-05-13-002-AE-rubric-anchors.md` — rubric prose anchor reference (mirror `2026-05-07-001-x-engine-rubric-anchors.md`)

**Approach:**
- Mirror x_engine `WorkflowSpec` shape; `count_findings → 0` (drafts are deliverables).
- Single parametrised workflow per R6: one session prompt with conditional per-platform adaptation sections (blog markdown + SEO meta + schema.org/Article + image briefs; LinkedIn Article with first-200-char hook + paragraph rhythm).
- `configure_env`: reads `$ARTICLE_ENGINE_TOPIC`, `$ARTICLE_ENGINE_VOICE_PERSONA_REF`, `$ARTICLE_ENGINE_SOURCE_MATERIAL_PATHS`, `$ARTICLE_ENGINE_TARGET_PLATFORMS` (csv: `blog | linkedin_article`), `$ARTICLE_ENGINE_BRIEFS_PATH` (optional).
- Brief consumption: if `$ARTICLE_ENGINE_BRIEFS_PATH` set, reads via U4 reader; top-K per client config; runs once per brief OR generates a single article on top-priority brief (lock per config).
- AE-1..AE-8 rubrics: hook strength, argument coherence, citation density + verifiability, voice fidelity, specificity, skimmability, SEO health (blog only), platform-adaptor compliance.
- Compliance gate (D5/D12): lane carries `<rule_set>_article_engine_*` rubric IDs in addition to AE-*; per active rule set in client config.
- Pre-publish review (U7): every promoted artifact enters review queue.

**Execution note:** Test-first for the workflow spec; characterization tests for the agent prompt (run a few seed fixtures, capture expected structural-gate outputs).

**Patterns to follow:**
- x_engine workflow (211 LOC) + session_eval (217 LOC) + session prompt (270 LOC) shape.
- linkedin_engine v040 cold-start fix: ship skeleton templates that the agent can `cp` as first draft.
- Marketing audit `_safe_format` precedent for `{}` escaping in JSON-example-bearing prompts.

**Test scenarios:**
- *Happy path:* Generate blog article from topic + voice + sources → structural gate passes; AE-1..AE-8 rubric scores > 0.
- *Happy path:* Generate LinkedIn Article → first 200 chars contain hook; paragraph rhythm matches LI algorithm.
- *Happy path:* Run with brief from geo → topic respected; voice persona applied.
- *Edge case:* Empty source material → article still generated, citation density low (rubric reflects).
- *Edge case:* Voice persona with empty corpus → article uses style anchors only.
- *Edge case:* Brief consumption with stale brief (`valid_until` passed) → skipped with log; lane runs standalone.
- *Error path:* Invalid `$ARTICLE_ENGINE_TARGET_PLATFORMS` → fail loud.
- *Error path:* Voice persona ref unknown → fail loud.
- *Error path:* Compliance hard-block triggered → variant scored 0; frontier rejects.
- *Integration:* Klinika procedure-page fixture passes both structural gate and AE rubrics + medical_pl compliance gate.
- *Integration:* DWF KSeF fixture passes both gates + legal_pl compliance.
- *Integration:* Promoted article enters pre-publish review queue → email arrives.
- *Integration:* `test_structural_doc_facts` covers article_engine via session_eval routing (mirror x_engine pattern).
- *Backend wiring:* `LaneSpec.inner_backend = "codex"` resolves correctly through the `cc212c2` priority chain (`LaneSpec > CLI flag > EVOLUTION_INNER_* > EVOLUTION_EVAL_*`); per-invocation CLI override `--inner-backend claude --inner-model sonnet` is honored. Assert via test_lane_registry expansion.

**Verification:**
- `pytest tests/autoresearch/test_article_engine_substrate.py -v` passes.
- `pytest tests/autoresearch/test_lane_registry.py -v` passes (new lane registered, backend override resolves correctly).
- Manual: run article_engine end-to-end with Klinika fixture; inspect output for blog + LinkedIn Article shape.

---

- [ ] **U14: image_engine lane (R11–R15)**

**Goal:** Land the new `image_engine` lane. Produces composed final images across 6 formats (`ig_single`, `ig_carousel`, `ig_story`, `li_doc_carousel`, `hero_banner`, `ad_static`).

**Requirements:** R11, R12, R13, R14, R15.

**Dependencies:** U2, U3, U5, U6. No judge-plan gate (G1 informational; aggregate scoring sufficient for v1).

**Judge wiring (per Substrate-consumed S1 + S2 + D24):**
- `inner_backend = "codex"`, `inner_model = "gpt-5.5"` for prompt-and-spec generation. Image generation itself goes through `FalPlatformClient` (D21 score-only; not a judge call). Static-pin pattern same as U13 — no automatic fallback substrate exists; swap via LaneSpec edit + redeploy if Phase D smoke shows codex hard-rejects.
- Vision sub-judge backend = **Gemini 2.5** per D24 — **built fresh in this unit** as `src/evaluation/vision_judge.py` (~80 LOC, rubric-driven, emits `dimension_scores`). NOT a wrapper around `image_preview_service.verify_preview()` (which is a fixed 2-axis preview QA tool). Used for visual rubrics that require multimodal evaluation (IE-1 hook visual, IE-2 brand consistency, IE-3 info-density, IE-5 visual specificity, IE-6 carousel arc).
- Outer composite judge: claude/opus for text dimensions (IE-4 format compliance, IE-7 alt-text/accessibility, IE-8 repurposability).
- Compliance-judge backend: per D25 (claude/opus via U5's `ComplianceJudgeConfig`).
- IE-1..IE-8 rubric anchors follow post-rewrite design (S2). **No IE-9 kernel rubric**; 8-rubric convention.

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/image_engine.py` (~220 LOC)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_image_engine.py` (~270 LOC)
- Create: `autoresearch/archive/v007-curated/programs/image_engine-session.md` (~280 LOC)
- Create: `autoresearch/archive/v007-curated/programs/image_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-ig_carousel.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-li_doc_carousel.md`
- Modify: `autoresearch/lane_registry.py` — `image_engine` `LaneSpec`, IE-1..IE-8 rubric IDs
- Modify: `src/evaluation/rubrics.py` — IE-1..IE-8 prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py`
- Modify: `autoresearch/concurrency.py` — add `fal_image=N` semaphore (D23)
- Create: `src/evaluation/vision_judge.py` (~80 LOC, per D24) — rubric-driven Gemini 2.5 vision judge. Accepts `rubric_id`, image path(s), context; returns `{score, rationale, dimension_scores}`. Invoked by `evaluate_variant.py` for visual rubric IDs (IE-1/2/3/5/6). Sibling to `image_preview_service.verify_preview()` (not a base).
- Create: `tests/evaluation/test_vision_judge.py` — unit tests for the new primitive.
- Create: `autoresearch/eval_suites/image_engine_klinika_carousel.json` — Klinika educational carousel fixture
- Create: `autoresearch/eval_suites/image_engine_dwf_doc_carousel.json` — DWF LinkedIn document carousel fixture (KSeF timeline)
- Create: `autoresearch/eval_suites/image_engine_hero_klinika.json`
- Create: `autoresearch/eval_suites/image_engine_ad_static_klinika.json`
- Create: `tests/autoresearch/test_image_engine_substrate.py`
- Create: `docs/plans/2026-05-13-002-IE-rubric-anchors.md`

**Approach:**
- Lane mirror x_engine shape. Workflow calls `ImageComposer` (U6) for composition; calls `FalPlatformClient.generate_image` for source imagery.
- Format dispatch: each `format` value produces a specific composition pipeline (carousel → multi-slide sequential; single → single image; etc.).
- D21: score-only quality gate (no regen); first-usable image accepted.
- D22: storage backend (`R2GenerationStorage` vs `LocalDevPreviewStorage`) selected from `GOFREDDY_STORAGE_BACKEND` env.
- IE-1..IE-8 rubrics: hook visual (first slide stop-scroll), brand consistency, info density / legibility, format compliance per platform, visual specificity, carousel arc, accessibility (alt-text quality), repurposability.
- Per-client `content_denylist` consulted at prompt time (Klinika denies `clinical_visuals` → image_engine refuses to compose clinical procedure visuals).
- fal.ai semaphore (D23) prevents account-level concurrency trip.

**Execution note:** Test-first for the workflow spec.

**Patterns to follow:**
- storyboard lane shape for preview-rendering tools.
- ImageComposer API from U6.

**Test scenarios:**
- *Happy path:* Compose `ig_carousel` with 5 slides → 5 composed PNGs uploaded to R2.
- *Happy path:* Compose `li_doc_carousel` (8 slides) → 8 PNGs with info-density layout.
- *Happy path:* Compose `hero_banner` → single banner image with brand stamp.
- *Edge case:* fal.ai returns moderation-blocked image → fatal error (no retry per D21); variant scored 0.
- *Edge case:* fal.ai circuit breaker tripped mid-carousel → lane fails fast; previous slides discarded.
- *Edge case:* R2 upload failure → variant fails (no LocalDev fallback in production).
- *Error path:* `content_denylist` includes a content type that the topic requires → lane refuses with explicit error.
- *Error path:* Brand assets missing → fail loud with name of missing asset.
- *Integration:* Klinika educational carousel fixture passes structural gate + IE rubrics + medical_pl compliance.
- *Integration:* DWF doc carousel fixture passes legal_pl compliance.
- *Integration:* fal_image semaphore prevents concurrent calls above N.
- *Backend wiring:* `LaneSpec.inner_backend` resolves correctly through the `cc212c2` priority chain (same as U13).
- *Vision sub-judge primitive:* `src/evaluation/vision_judge.py` (new per D24) emits `{score, rationale, dimension_scores}` for an image + rubric_id pair; integration test runs a visual rubric (IE-1 hook visual) and a text rubric (IE-7 alt-text) on the same composed carousel slide and asserts they dispatch to Gemini 2.5 + claude/opus respectively.

**Verification:**
- `pytest tests/autoresearch/test_image_engine_substrate.py -v` passes (including vision-sub-judge routing).
- Manual: run image_engine end-to-end for Klinika carousel; inspect output PNGs in R2.

---

- [ ] **U15: ad_engine lane (R16–R19)**

**Goal:** Land the new `ad_engine` lane. Produces 3–5 variants per format for Meta + LinkedIn ad creative.

**Requirements:** R16, R17, R18, R19.

**Dependencies:** U2, U3, U5. Soft dependency on U14 (image_engine produces ad statics) and U8 (storyboard produces ad Reels scripts). No judge-plan gate (G1 informational; aggregate scoring sufficient for v1).

**Judge wiring (per Substrate-consumed S1 + S2):**
- `inner_backend = "claude"`, `inner_model = "sonnet"` — **statically pinned from day 1** (not codex, not via fallback). Healthcare-vertical and regulated-legal ad vocabulary almost certainly trips codex's cyber filter (geo + competitive already hit this on similar content), and no automatic fallback substrate exists. Pinning sonnet from day 1 mirrors `lane_registry.py:174-175, 206-207` precedent. Reversible after Phase D smoke via LaneSpec edit + redeploy or per-invocation CLI override (`freddy autoresearch ... --inner-backend codex`); a runtime feature-flag mechanism for backend swapping does not exist and is not in v1 scope.
- Outer judge: claude/opus. Compliance-judge backend per D25 (via U5's `ComplianceJudgeConfig`).
- AD-1..AD-8 rubric anchors follow post-rewrite design (S2). **No AD-9 kernel rubric**; 8-rubric convention.

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/ad_engine.py` (~240 LOC)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_ad_engine.py` (~260 LOC)
- Create: `autoresearch/archive/v007-curated/programs/ad_engine-session.md` (~320 LOC)
- Create: `autoresearch/archive/v007-curated/programs/ad_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/ad_engine/skeleton-meta_reels.md`
- Create: `autoresearch/archive/v007-curated/templates/ad_engine/skeleton-meta_image.md`
- Create: `autoresearch/archive/v007-curated/templates/ad_engine/skeleton-linkedin_sponsored.md`
- Create: `autoresearch/archive/v007-curated/templates/ad_engine/skeleton-linkedin_doc_ad.md`
- Modify: `autoresearch/lane_registry.py` — `ad_engine` LaneSpec, AD-1..AD-8 rubric IDs
- Modify: `src/evaluation/rubrics.py` — AD-1..AD-8 prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py`
- Create: `src/ads/signal_aggregator.py` — combines Foreplay + Adyntel + SerpAPI + GSC signals
- Create: `autoresearch/eval_suites/ad_engine_klinika_meta.json` — Klinika Meta ad fixture
- Create: `autoresearch/eval_suites/ad_engine_dwf_linkedin.json` — DWF LinkedIn Sponsored Content fixture
- Create: `tests/autoresearch/test_ad_engine_substrate.py`
- Create: `tests/ads/test_signal_aggregator.py`
- Create: `docs/plans/2026-05-13-002-AD-rubric-anchors.md`

**Approach:**
- Workflow mirrors x_engine, with ad-specific structural gates (variant count, format compliance, hook diversity per D15).
- Signal aggregator pulls competitor ad signal from Foreplay (Meta/TikTok/LinkedIn), Adyntel + SerpAPI (Google — Adyntel canonical per repo research clarification), GSC (first-party SEO perf). On empty Foreplay result → degrade gracefully (D16).
- **Async-to-sync bridge:** `ForeplayProvider` and `AdyntelProvider` are async (`httpx.AsyncClient`); lane workflow callables are sync per `WorkflowSpec` contract. signal_aggregator exposes a sync `gather_signals(domain) -> SignalBundle` that wraps the async provider calls via `asyncio.run(...)`. Precedent: `autoresearch/archive_x_engine/current_runtime/scripts/evaluate_session.py` uses the same pattern.
- `configure_env`: `$AD_ENGINE_CAMPAIGN_GOAL`, `$AD_ENGINE_OFFER`, `$AD_ENGINE_TARGET_AUDIENCE`, `$AD_ENGINE_VOICE_PERSONA_REF`, `$AD_ENGINE_PLATFORM_TARGET` (csv: `meta | linkedin`), `$AD_ENGINE_AD_FORMAT_PER_PLATFORM`, `$AD_ENGINE_FULL_BUNDLE` (bool).
- Per platform-format combo: emits 3–5 ad creative variants + landing-page hero copy per variant. Targeting/bid/budget recommendations are **out of v1 scope** (triage TD-21).
- Diversity gate (D15): N-token-overlap structural check between variant hooks; fails variant if overlap > threshold.
- AD-1..AD-8 rubrics: hook strength, CTA clarity, offer specificity, platform-format compliance (character limits, image text-overlay ratios, healthcare-vertical word avoidance on Meta, LinkedIn copy rules), variant diversity (rubric-side; structural gate is separate per D15), market-signal alignment (no-op if Foreplay degraded per D16).
- Compliance gate: medical_pl for Klinika ads, legal_pl for DWF ads.
- Pre-publish review: every ad variant set enters review queue.

**Execution note:** Test-first for the structural diversity gate; characterization for ad creative quality.

**Patterns to follow:**
- x_engine workflow shape.
- Foreplay/Adyntel client patterns in `src/competitive/providers/`.
- `CircuitBreaker` and `cost_recorder` reuse from `src/common/`.

**Test scenarios:**
- *Happy path:* Generate 5 Meta Reels Ad variants → 5 distinct ad scripts pass diversity gate; AD rubric scores > 0.
- *Happy path:* Generate LinkedIn Sponsored Content + Document Ad variants → both formats produced.
- *Happy path:* variants emit creative + LP copy only (v1 scope per TD-21).
- *Edge case:* Foreplay returns no ads for client domain → R19 market-signal dimension no-ops; lane runs with degraded-signal warning.
- *Edge case:* All variants too similar (diversity gate) → variant rejected; agent re-prompted (within max_turns budget).
- *Edge case:* (removed — `full_bundle` dropped per TD-21)
- *Error path:* `AD_ENGINE_PLATFORM_TARGET` includes `google` (architecture-supported but build deferred) → fail loud with "v1.5" message.
- *Error path:* Compliance hard-block → variant scored 0.
- *Integration:* Klinika Meta ad fixture passes structural gate + AD rubrics + medical_pl compliance.
- *Integration:* DWF LinkedIn fixture passes legal_pl compliance.
- *Integration:* Signal aggregator handles Foreplay degraded + GSC available concurrently.
- *Backend wiring:* `LaneSpec.inner_backend` static-pins to `claude/sonnet` (the day-1 default per U15 prose); test asserts the LaneSpec value at module load. Reversibility note: swapping to codex requires LaneSpec edit + redeploy or per-invocation `--inner-backend codex` CLI override; no runtime flag exists.

**Verification:**
- `pytest tests/autoresearch/test_ad_engine_substrate.py -v` passes.
- `pytest tests/ads/ -v` passes.
- Manual: run ad_engine end-to-end for Klinika; inspect 5 Meta ad variants for diversity + compliance.

---

- [ ] **U15b: site_engine lane (R27–R34)**

**Goal:** Land the new `site_engine` lane. Mutates section-level site artifacts (hero, value_prop, social_proof, faq, cta, pricing) for a target client site; AI judges score against SE-1..SE-8 per `docs/rubrics/site-quality.md`; winners enter the pre-publish review queue (U7).

**Requirements:** R27–R34. Section-level only per TD-28; brief sources `marketing_audit` + `geo` per TD-29; rubric anchors at `docs/rubrics/site-quality.md` per TD-30.

**Dependencies:** U2 (per-client config — site_engine extends ClientConfig with `site_engine.target_url`, `site_engine.brand_tokens`, `site_engine.sections_in_scope`), U3 (voice persona consumed unchanged for SE-4), U4 (findings-brief contract — site_engine consumes briefs from marketing_audit + geo), U5 (compliance gate 1), U7 (pre-publish reviewer gate 2), U7b (Playwright render utility — required for SE-1/SE-5/SE-8 visual judges), U7c (a11y + perf audit — required for SE-6/SE-7 structural gates).

**Judge wiring (per Substrate-consumed S1 + S2 + D24 image_engine vision-sub-judge pattern):**
- **Text rubrics** (SE-2 copy clarity, SE-3 claim honesty, SE-4 voice persona fit): outer judge backend = **claude/opus** (frontier; diverse from inner-loop). Inner backend = **codex/gpt-5.5** by default, **claude/sonnet day-1 fallback** when client config has `site_engine.codex_fallback: true` (regulated-vertical clients should set this from day 1 — same pattern as U15 ad_engine day-1 fallback per Pass-2 self-audit).
- **Visual rubrics** (SE-1 hierarchy, SE-5 brand-token fit, SE-8 anti-slop): vision-sub-judge backend = **Gemini 2.5** (per D24 image_engine precedent). Receives `RenderResult.screenshot_paths` from U7b. Anti-slop calibration prose embedded in the judge template references the 2026-05-13 landing-page anchors.
- **Structural-gate axes** (SE-6 a11y, SE-7 perf): NOT scored by an LLM judge. Computed directly from U7c `A11yReport.severity_counts` and `PerfReport.budget_pass` per the rubric's falsifiability rules.
- **Compliance-judge backend** (per D25): single claude/opus across all lanes with compliance gates; site_engine inherits.

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/site_engine.py` (~220 LOC, mirror x_engine.py with section-scoped artifact handling)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_site_engine.py` (~280 LOC, mirror session_eval_x_engine.py with structural gate that calls U7b render + U7c audit before LLM scoring; structural fail conditions: render fails, console_errors contain "Error", a11y has severity ≥ critical, perf payload > 2× budget)
- Create: `autoresearch/archive/v007-curated/programs/site_engine-session.md` (~340 LOC, agent prompt; reads `$SITE_ENGINE_TARGET_URL`, `$SITE_ENGINE_SECTION`, `$SITE_ENGINE_BRAND_TOKENS_PATH`, `$SITE_ENGINE_VOICE_PERSONA_REF`, `$SITE_ENGINE_BRIEFS_PATH`, `$SITE_ENGINE_AUDIENCE`)
- Create: `autoresearch/archive/v007-curated/programs/site_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-hero.html` (cold-start)
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-value_prop.html`
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-social_proof.html`
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-faq.html`
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-cta.html`
- Create: `autoresearch/archive/v007-curated/templates/site_engine/skeleton-pricing.html`
- Modify: `autoresearch/lane_registry.py` — add `site_engine` LaneSpec with `rubric_ids=("SE-1","SE-2","SE-3","SE-4","SE-5","SE-6","SE-7","SE-8")`, `readonly_subprefixes` for site_render + site_audit shared utilities + voice/brief/compliance substrate
- Modify: `src/evaluation/rubrics.py` — register SE-1..SE-8 prose anchors **as references to `docs/rubrics/site-quality.md`** (not inline duplicates — single source of truth lives in the rubric file per TD-30). Use the existing prose-registry resolution pattern (TD-11): `RubricTemplate.prose_ref = "docs/rubrics/site-quality.md#se-1"` style.
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py` — register `site_engine` SPEC; bump `RUBRICS` count assertion from 53 → 61 (8 new SE rubrics)
- Modify: `autoresearch/eval_suites/search-v1.json` — add site_engine fixtures
- Create: `autoresearch/eval_suites/site_engine_klinika_hero.json` — Klinika hero-section fixture (real client URL + brand tokens per D11)
- Create: `autoresearch/eval_suites/site_engine_dwf_value_prop.json` — DWF value-prop section fixture
- Create: `autoresearch/eval_suites/site_engine_gofreddy_hero.json` — gofreddy.ai hero-section fixture (canonical training example from 2026-05-13 session)
- Create: `tests/autoresearch/test_site_engine_substrate.py` (~140 LOC, mirror test_x_engine_substrate.py + verify render + audit utility wiring + vision-sub-judge dispatch)
- Create: `clients/<slug>/site_engine/sections/` — per-client section archive (post-promotion artifacts)
- Modify: `clients/klinika-melitus/client.yaml` — add `site_engine: {target_url, brand_tokens, sections_in_scope, codex_fallback: true}`
- Modify: `clients/dwf-poland/client.yaml` — same
- Modify: `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` — add site_engine launch steps
- Modify: `docs/runbooks/2026-05-13-002-dwf-launch-runbook.md` — same

**Approach:**
- Mirror x_engine `WorkflowSpec` shape; `count_findings → 0` (section variants ARE the deliverables).
- Single parametrised workflow per section type: one session prompt with conditional per-section blocks (hero gets H1+lead+CTA; faq gets question pairs; pricing gets tier cards).
- `configure_env`: reads section + voice + brand + brief env vars; passes through to the agent prompt.
- **Brief consumption** (TD-29): if `$SITE_ENGINE_BRIEFS_PATH` set, reads via U4 reader; primary source = marketing_audit findings (the audit's 149-lens output names sections + problems); secondary = geo signals (AI-search readiness for the page). Top-K briefs per `client_config.site_engine.weekly_section_target`.
- **Mutation surface** = HTML + CSS + (optional minimal JS for hover/animation) section snippets. Agent edits `templates/site_engine/skeleton-<section>.html` to produce variants; brand tokens are READ-ONLY (mutation cannot change token values, only consume them).
- **Structural gate** runs U7b render + U7c audit BEFORE LLM scoring. Variant fails structurally if: render fails (Chromium can't load section); `console_errors` contains severity ≥ "error"; a11y has any violation of severity `critical`; perf payload exceeds 2× the section-type budget; HTML fails semantic-tag check.
- **SE-1/5/8 visual scoring** dispatches to the Gemini 2.5 vision sub-judge with screenshot + brand-tokens manifest + rubric anchor loaded from `docs/rubrics/site-quality.md` at eval time.
- **SE-2/3/4 text scoring** dispatches to claude/opus with the section text + voice persona + brief.
- **SE-6/7 scoring** computed directly from U7c output per rubric falsifiability rules (no LLM call).
- **Compliance gate** (D5/D12): site_engine carries `<rule_set>_site_engine_*` rubric IDs in addition to SE-*. For Klinika (`medical_pl`): no clinical photography in hero; claim language meets Polish health-advertising rules. For DWF (`legal_pl`): no outcome guarantees; jurisdiction language compliant.
- **Pre-publish review** (U7): every promoted section variant enters the review queue with screenshot preview rendered inline in the reviewer email.
- **Cross-cycle learning** (the loop diagrammed in the 2026-05-13 landing-page session): reviewer signals (accept / edit / reject + edit deltas) feed back into rubric anchor calibration via a quarterly cycle. Edit deltas surface concrete failure modes that get folded into Score-3 anchor prose. Manual operator step in v1; automation deferred to v1.5.

**Patterns to follow:**
- x_engine workflow (211 LOC) + session_eval (217 LOC) + session prompt (270 LOC) shape — directly applicable.
- linkedin_engine v040 cold-start fix: ship skeleton templates per section type that the agent can `cp` as first draft.
- article_engine codex-fallback policy (U13) — site_engine inherits the same `ModerationBlockedError` → claude/sonnet fallback pattern.
- image_engine vision-sub-judge dispatch (U14 / D24) — site_engine reuses the dispatch logic for SE-1/5/8.
- ad_engine compliance-rubric-ID composition (U15 + D6 single-rule-set mode per TD-18) — site_engine composes its SE-* IDs with `<rule_set>_site_engine_*` IDs identically.

**Test scenarios:**
- *Happy path:* Generate hero section for gofreddy.ai fixture → structural gate passes; SE-1..SE-8 scores > 0; visual judge returns rationale referencing render screenshot.
- *Happy path:* Generate FAQ section for Klinika fixture → renders with Klinika brand tokens; SE-4 (voice fit) ≥ 4 against Dr. Maria's voice corpus.
- *Happy path:* Generate value-prop for DWF fixture → SE-3 (claim honesty) ≥ 4; legal_pl compliance gate passes.
- *Edge case:* Section JS throws console error → structural gate fails; variant scored 0; not promoted.
- *Edge case:* Section uses off-brand color → SE-5 ≤ 3; rationale identifies the off-brand value.
- *Edge case:* Section has heading-level skip → SE-6 ≤ 3; axe violation logged.
- *Edge case:* Section payload > budget → SE-7 ≤ 3.
- *Edge case:* Section copy uses jargon ("autoresearch", "rubric") without translation → SE-2 ≤ 3.
- *Edge case:* Section copy includes "fully autonomous AI" language → SE-3 ≤ 3 (anti-overselling); SE-8 ≤ 3 (anti-slop).
- *Edge case:* Section uses three-icon trio with generic gradients → SE-8 ≤ 3 (anti-slop calibration anchor).
- *Edge case:* Empty voice corpus → SE-4 falls back to style_anchors only; documented in score rationale.
- *Edge case:* Section with full-page rewrite attempt (multiple semantic sections) → workflow rejects pre-render with clear error ("v1 is section-level only per TD-28; submit one section at a time").
- *Error path:* Invalid `$SITE_ENGINE_SECTION` (not in `{hero, value_prop, social_proof, faq, cta, pricing}`) → fail loud.
- *Error path:* `brand_tokens` missing from client config → fail loud with onboarding-doc reference.
- *Error path:* `target_url` not reachable for fixture capture → fail loud.
- *Error path:* Compliance hard-block triggered → variant scored 0; frontier rejects.
- *Integration:* Klinika hero fixture passes structural gate + SE-1..SE-8 + medical_pl compliance gate.
- *Integration:* DWF value-prop fixture passes both gates + legal_pl compliance.
- *Integration:* gofreddy.ai hero fixture (canonical 2026-05-13 calibration data) passes; SE-8 (anti-slop) returns ≥ 4.5 since this is the reference fixture.
- *Integration:* Promoted section enters pre-publish review queue → reviewer email arrives with inline screenshot preview.
- *Integration:* `test_structural_doc_facts` covers site_engine via session_eval routing.
- *Backend wiring:* setting `LaneSpec.inner_backend = "claude"` overrides `EVOLUTION_INNER_BACKEND=codex` env (mirror article_engine wiring test).
- *Backend fallback:* simulated codex `ModerationBlockedError` on hero-section fixture → harness falls through to claude/sonnet per the day-1 fallback policy.
- *Vision dispatch:* `test_site_engine_substrate` verifies SE-1 / SE-5 / SE-8 dispatch to Gemini 2.5 (vision); SE-2 / SE-3 / SE-4 dispatch to claude/opus (text); SE-6 / SE-7 dispatch to no LLM (structural).
- *Rubric prose resolution:* `RubricTemplate.prose_ref` resolution loads SE-1..SE-8 anchors from `docs/rubrics/site-quality.md` at eval time; test asserts the loaded prose matches the file's content.

**Execution note:** Test-first for the workflow spec and structural gate; characterization tests for the agent prompt (run a few seed fixtures, capture expected screenshot + audit JSON).

**Verification:**
- `pytest tests/autoresearch/test_site_engine_substrate.py -v` passes.
- `pytest tests/autoresearch/test_lane_registry.py -v` passes (new lane registered, backend override + vision-sub-judge dispatch resolve correctly).
- `pytest tests/autoresearch/test_structural_doc_facts.py -v` passes (site_engine routes through session_eval).
- `python -c "from src.api.main import app"` succeeds (RUBRICS count 61 assertion holds).
- Manual: run site_engine end-to-end against gofreddy.ai hero fixture; inspect produced variant for SE-1..SE-8 rationale completeness.
- Manual: run site_engine against Klinika hero; verify reviewer email arrives with rendered preview.

**Reversibility:** Reversible until first client artifact ships. After first ship, the section archive at `clients/<slug>/site_engine/sections/` becomes part of the client's site history — removal is a roll-back operation, not a code revert.

---

### Phase D — Compliance Rule Sets + Integration

- [ ] **U16: medical_pl rule set authoring**

**Goal:** Author the `medical_pl` compliance rule set with Polish-language patterns covering Art. 14 *Ustawa o działalności leczniczej*: superlatives, prices, CTAs, encouragement-to-use.

**Requirements:** R22 (origin). Gated on parallel-track risk #2 (legal-review owner identification).

**Dependencies:** U5.

**Files:**
- Modify: `compliance/rule_sets/_placeholder_medical_pl.yaml` → rename to `compliance/rule_sets/medical_pl.yaml` and replace placeholder content with legal-reviewed patterns
- Create: `docs/plans/2026-05-13-002-medical-pl-rule-set.md` — authoring notes (legal-review trail, pattern provenance)
- Test: `tests/compliance/test_medical_pl_rule_set.py` — rule-set integrity + sample-artifact evaluation

**Approach:**
- Rule set is data-driven YAML per D20. Each rule has `id`, `pattern` (regex/list), `severity` (`hard_block | soft_warn`), `prose` (judge rubric description).
- Patterns based on Art. 14 prohibited content categories: superlatives ("najlepszy", "najnowocześniejszy", "najtańszy"), price references (cennik, discounts, installments), CTAs ("zarezerwuj", "umów wizytę"), encouragement-to-use.
- ~30–50 rules expected. Authoring is a coordinated effort with the legal-review owner (parallel-track risk #2).
- Until legal review lands, `_placeholder_medical_pl.yaml` ships with conservative patterns; human gate (U7) carries the risk-control weight.

**Execution note:** Test-first for the YAML schema validity; authoring proceeds as legal review surfaces patterns.

**Patterns to follow:**
- Slop-gate `data/slop-phrases-banned.txt` precedent (deterministic regex bank).
- Marketing audit rubric prose authoring (`programs/marketing_audit/prompts/judges/MA-{i}-judge.md`).

**Test scenarios:**
- *Happy path:* Load `medical_pl.yaml` → valid `ComplianceRuleSet` with N rules.
- *Happy path:* Evaluate artifact containing "najlepszy" → hard_block flag fires.
- *Happy path:* Evaluate clean artifact → verdict `clean`.
- *Edge case:* Patterns case-insensitive vs case-sensitive (per rule definition).
- *Error path:* Pattern regex compile error → ValidationError at load.
- *Integration:* Run against Klinika fixture artifacts; flags align with manual review.

**Verification:**
- `pytest tests/compliance/test_medical_pl_rule_set.py -v` passes.
- Legal review sign-off on the pattern catalog (out-of-band).

---

- [ ] **U17: legal_pl rule set authoring**

**Goal:** Author the `legal_pl` compliance rule set for Polish bar / radca advertising rules.

**Requirements:** R22 (origin).

**Dependencies:** U5.

**Files:** Mirror U16 against `compliance/rule_sets/legal_pl.yaml`.

**Approach:** Mirror U16. Patterns based on Kodeks Etyki Radcy Prawnego + Zbiór Zasad Etyki Adwokackiej: no solicitation, no fee mentions, no comparisons.

**Test scenarios:** Mirror U16 with legal-flavored patterns.

**Verification:** Mirror U16.

---

- [ ] **U18: Klinika + DWF instantiation + demo orchestration**

**Goal:** Build the per-client configs for Klinika + DWF, ingest voice corpora, collect brand assets, run end-to-end demo pipelines.

**Requirements:** Success Criteria — end-to-end demo per onboarded client + ≥5 published artifacts.

**Dependencies:** U8, U13, U14, U15, U16, U17 (all lanes + rule sets must be functional).

**Files:**
- Modify: `clients/klinika-melitus/client.yaml` — complete config with all fields
- Modify: `clients/dwf-poland/client.yaml` — complete config
- Create: `clients/klinika-melitus/voice/corpus/medycyna-urody-ch01.txt` etc. — Dr. Maria book chapters (ingested per parallel-track risk #1)
- Create: `clients/klinika-melitus/brand/` — style guide, logo, palette, fonts, reference imagery
- Create: `clients/dwf-poland/voice/corpus/jamka-prior-articles/` — DWF partner articles
- Create: `clients/dwf-poland/brand/` — DWF brand assets
- Create: `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` — operational steps
- Create: `docs/runbooks/2026-05-13-002-dwf-launch-runbook.md` — operational steps
- Create: `docs/runbooks/2026-05-13-002-klinika-artifacts.json` — published-artifact tracking manifest
- Create: `docs/runbooks/2026-05-13-002-dwf-artifacts.json` — published-artifact tracking manifest
- Create: `clients/klinika-melitus/voice/CONSENT.md` — per-corpus license + scope + withdrawal record
- Create: `clients/dwf-poland/voice/CONSENT.md` — same
- Modify: `.gitignore` — exclude `clients/*/voice/corpus/` and `clients/*/brand/`

**Approach:**
- Voice corpus ingestion gated on parallel-track risk #1 (partner consent). Once consent lands, ingest via PDF OCR or direct text capture. **Voice corpora are NOT git-tracked** (copyright + GDPR + right-to-erasure considerations); store under `clients/<slug>/voice/corpus/` with `.gitignore` exclusion; per-corpus license/consent record persisted alongside the corpus directory at `clients/<slug>/voice/CONSENT.md` documenting scope of use + withdrawal procedure.
- **Secondary reviewer naming (per TD-2 + TD-17):** Klinika's per-client config (`clients/klinika-melitus/client.yaml`) names a `pre_publish_reviewer_secondary` — operationally: a senior staff member at Klinika (e.g., clinic manager, senior nurse, marketing coordinator) who can sign off when Dr. Maria is unavailable. DWF's config names a second partner or senior associate. Both secondaries must be confirmed during U18 launch-runbook prep (alongside primary reviewer onboarding) BEFORE production launch. **Mandatory for the placeholder rule-set regime per TD-17** (two-reviewer sign-off required while `medical_pl` and `legal_pl` are placeholder-only).
- Brand asset collection coordinated with each client. Brand assets stored locally (not in git for confidential client assets).
- Demo pipeline: pick a single geo brief (Klinika SEO topic) + a single monitoring brief (DWF KSeF event) → run through article_engine → article triggers downstream artifacts (manually for v1, since R8 spawn briefs dropped).
- Pre-publish review service goes live; reviewers (Dr. Maria, named DWF partner) sign off on demo artifacts.
- **Artifact publication manifest:** create `docs/runbooks/2026-05-13-002-klinika-artifacts.json` and `docs/runbooks/2026-05-13-002-dwf-artifacts.json` with entries `{artifact_id, lane, format, channel, published_url, approver_name, approval_timestamp, published_timestamp}`. Used to track the ≥5-published-per-client success criterion during the per-client launch window.
- **Launch window definition:** 30 calendar days from per-client production go-live (i.e., from the moment client's first artifact is approved-and-published). If <5 pieces are approved within the window, U18 is not signed off; root-cause is logged; one of D5 (regen-with-feedback) or D14 (auto-pause vs auto-reject) may be revisited.

**Patterns to follow:**
- Marketing audit operational runbook precedent (`docs/plans/2026-05-06-001-marketing-audit-v1-deployment-runbook.md`).

**Test scenarios:**
- *Test expectation: none — operational unit. Covered by integration scenarios in U13, U14, U15.*

**Verification:**
- Klinika and DWF configs load without error; voice corpora resolve; brand assets accessible.
- End-to-end demo run produces all 4 channel artifacts per client; all pass compliance gates; all approved by reviewers.
- ≥5 artifacts per client published to real channels during launch window.

---

- [ ] **U19: Client #3 onboarding CI harness (architectural success bar)**

**Goal:** Validate that a third client (third archetype) can onboard config-only — no code changes to lane internals, rubrics, or shared infra.

**Requirements:** Success Criteria — "Per-client onboarding works config-only for client #3".

**Dependencies:** U18 (all lanes operational with Klinika + DWF).

**Files:**
- Modify: `clients/_stub_b2b_tech/client.yaml` — complete stub config for a synthetic SaaS/AI client archetype
- Create: `clients/_stub_b2b_tech/voice/corpus/stub-articles/` — stub voice corpus (synthetic)
- Create: `clients/_stub_b2b_tech/brand/` — stub brand assets
- Create: `compliance/rule_sets/ai_claims.yaml` — placeholder rule set for AI capability claims (data-driven per D20; demonstrates "new rule set = config, not code")
- Create: `tests/onboarding/test_client_3_onboarding.py` — structural diff + pipeline run
- Modify: `autoresearch/eval_suites/search-v1.json` — stub fixtures for b2b_tech archetype (data_provenance: stub per D11)

**Approach:**
- Freeze repo state immediately before U19 begins; record file hashes for `src/{clients,voice,briefs,compliance,review,ads,generation}/`, `autoresearch/lane_registry.py`, `src/evaluation/rubrics.py`, `autoresearch/archive/v007-curated/workflows/__init__.py`.
- Add the b2b_tech stub config, corpus, brand, fixture, and new `ai_claims` rule set.
- CI test runs full end-to-end pipeline against stub client + stub reviewer (auto-approves).
- Final assertion: diff `git diff <pre-freeze-commit>..HEAD --stat -- src/clients src/voice src/briefs src/compliance src/review src/ads src/generation autoresearch/lane_registry.py src/evaluation/rubrics.py autoresearch/archive/v007-curated/workflows/__init__.py` shows zero changes; only `clients/_stub_b2b_tech/`, `compliance/rule_sets/ai_claims.yaml`, and `autoresearch/eval_suites/` differ.

**Execution note:** Test-first — the diff assertion is the load-bearing test of the architectural success bar.

**Patterns to follow:**
- Marketing audit acceptance test precedent (§7.7 dry-run).

**Test scenarios:**
- *Happy path:* Run pipeline for `_stub_b2b_tech` → all 4 channel artifacts produced; compliance gates pass; auto-approving stub reviewer approves; final published artifacts exist.
- *Happy path:* Diff assertion → only data files changed (no code in `src/` or lane workflows).
- *Edge case:* Stub corpus is empty → article_engine + storyboard use `style_anchors`-only voice; outputs structurally valid.
- *Error path:* Adding a rule set requires Python code → diff assertion fails, fails the test (catches D20 violation).
- *Integration:* All 6 enabled channels (storyboard, article_engine, image_engine, ad_engine, linkedin_engine, x_engine) produce artifacts for `_stub_b2b_tech` config.

**Verification:**
- `pytest tests/onboarding/test_client_3_onboarding.py -v` passes.
- Manual diff inspection confirms config-only onboarding.
- **Operator-time clock (per TD-13):** measured by a teammate or fresh agent who did NOT author the substrate. Timer **starts** at first commit to `clients/_stub_b2b_tech/client.yaml`; timer **ends** at first green run of `tests/onboarding/test_client_3_onboarding.py`. Target: **<1 working day** (≤8 hours active work, not wall-clock). The onboarding doc (`docs/onboarding/client-onboarding.md`, generated at U19 completion) is the only allowed reference. If onboarding exceeds 8 hours, the onboarding doc + R26 schema are not yet operator-ready — iterate before declaring U19 complete.
- Record observed onboarding time in `docs/plans/2026-05-13-002-onboarding-time-measurements.md` along with stuck-points so the onboarding doc can be improved.

---

## System-Wide Impact

- **Interaction graph:**
 - `autoresearch/lane_registry.py:LANES` mutated 6 times (3 new lanes + 3 LaneSpec mods for storyboard/linkedin_engine/x_engine extensions).
 - `src/evaluation/rubrics.py:RUBRICS` mutated 7 times (3 new lanes × 8 + 4 per-lane compliance duplications for 6 lanes); D4 derived count absorbs this without manual lockstep.
 - `autoresearch/archive/v007-curated/workflows/__init__.py:WORKFLOW_SPECS` mutated 3 times (new lanes register).
 - `autoresearch/eval_suites/search-v1.json` mutated multiple times (new fixtures per lane).
 - New module trees under `src/clients/`, `src/voice/`, `src/briefs/`, `src/compliance/`, `src/review/`, `src/ads/`, `src/generation/image_composer.py` + `image_layout.py`.
- **Error propagation:** All shared-infra modules (config loader, persona loader, brief reader, compliance judge, review service) fail loud at lane preflight per CLAUDE.md Rule 12. Lane-side errors (fal.ai circuit-broken, R2 upload failure, missing brand asset) fail the variant immediately rather than degrading silently.
- **State lifecycle risks:** Per-client config snapshot at run-start (D7) prevents mid-run config drift; finalize-time check fails loud on drift. Brief promotion is post-promote-only (D8) — variant-emitted briefs never escape their evaluation. Pre-publish review state machine is append-only (terminal decisions cannot be reversed); rollback requires fresh submission.
- **API surface parity:** 3 new lanes follow the existing 8-lane substrate contract (LaneSpec + WorkflowSpec + session.md + evaluation-scope.yaml). Promote-findings + render-report pipelines auto-pick up new lanes via `WORKFLOW_SPECS` dict.
- **Integration coverage:** Cross-lane brief handoff is net-new (geo→article, monitoring→article); end-to-end demo pipelines (U18) exercise it. Cross-lane voice consistency is net-new (4 lanes consume same `dr_maria` persona); U18 demo validates this for Klinika.
- **Unchanged invariants:**
 - The 4 oldest lanes (`geo`, `competitive`, `monitoring`, `storyboard`) retain `_rubric_ids("PREFIX")` helper-style 8-rubric tuples. The new lanes follow the same pattern.
 - `x_engine` + `linkedin_engine` keep their inline 6-rubric tuples and `count_findings → 0` precedent.
 - `marketing_audit`'s `custom_validate` lazy-binding stays as-is.
 - `monitoring`'s `custom_persist_judge_payload` (DQS sidecar) stays as-is.
 - `findings_promotion` remains intra-lane; cross-lane briefs are a separate file convention (`briefs/<brief_id>.json`).

## Plan-level Threat Model (per triage TD-5)

Three exploits could chain into end-to-end bypass of the compliance gate. Each is mitigated by an explicit ship-gate item; no compensating control is optional.

| Exploit | Chain | Mitigation (ship-gate item) |
|---|---|---|
| **HMAC key leak** (env var leak, repo accident, CI log exposure) | Attacker forges approve token → audit log records `reviewer_email` but signature was forged → unreviewed content publishes | TD-3: `GOFREDDY_REVIEW_HMAC_KEY` from env (never repo-checked-in); quarterly rotation; dual-key overlap; single-use enforcement via audit-log idempotency check |
| **Email-prefetcher / CSRF** (corporate mail-gateway URL-scanner auto-fires GET approve URL before human sees email) | Approve token used; audit log records auto-fire as reviewer click → content publishes without human review | U7 auto-fix: approve/reject URLs land on confirmation GET; state mutation is POST with fresh CSRF token; constant-time signature compare; single-use token |
| **Reviewer-email-swap via PR** (malicious or careless PR to `clients/<slug>/client.yaml` swaps `pre_publish_reviewer.email`) | All future approvals route to attacker → content publishes with attacker approval; no signing key needed; no audit alarm | TD-5 + TD-16: `.github/CODEOWNERS` requires security/ops review on changes to `clients/*/client.yaml` protected fields; email change to `pre_publish_reviewer.email` requires out-of-band confirmation to BOTH old and new address with 24h cooling-off; SPF/DKIM/DMARC on sending domain |

**Defense-in-depth chain:** all three must hold. A leaked HMAC key + a poisoned email scanner + a malicious PR can each defeat the gate independently if not all three are mitigated. Treat any unresolved mitigation as a v1 SHIP gate blocker.

## Risks & Dependencies

| Risk | Mitigation |
|---|---|
| Plan B retroactively un-archived; lanes need porting to autoresearch_v2/ | JR explicitly archived Plan B 2026-05-13. If reversed, port plan per Plan B Phase 3 U11-U12 conventions. |
| Voice migration regression on linkedin_engine + x_engine | D10 revised per TD-7 + TD-19: noise-floor characterization spike pre-U11/U12 → per-fixture regression bar at `max(5%, 2 × std_dev)`; direct cutover gated on bar (no toggle). Rollback = `git revert`. |
| RUBRICS count merge conflict during per-lane increments | D4 derived count eliminates the manual lockstep; PRs that touch `RUBRICS` and not `LaneSpec.rubric_ids` (or vice versa) fail CI by construction. |
| fal.ai account-level concurrency trip from image_engine + ad_engine load | D23 `fal_image=N` semaphore. Operator dial-up: start at 2, watch for circuit-breaker trips. |
| Compliance pattern catalogs not legally reviewed at v1 ship | Parallel-track risk #2; U16/U17 ship with placeholder rule sets initially. Human gate (U7) carries risk-control weight. v1 SHIP gate: legal review complete OR explicit acceptance of placeholder-only state. |
| Voice corpus consent not obtained at v1 ship | Parallel-track risk #1; affected lanes degrade to `style_anchors`-only voice. v1 SHIP gate: consent for ≥1 corpus per client OR explicit acceptance. |
| AI-generated Klinika clinical content fails Art. 14 review (silent fallout) | R1 narrowing + per-client `content_denylist` enforce non-clinical scope at variant generation. AI-video validation spike (parallel-track risk #3) confirms acceptable register before full pipeline build. |
| Foreplay signal unreliable for ad_engine evolution | Parallel-track risk #4; D16 degrades gracefully (R19 dimension no-ops). Lane runs judge-only on degraded signal. |
| New lanes' max_turns budgets exhausted silently | Marketing audit lesson #2: empirical budget headroom; `expected_output_files` enforces filesystem ground-truth. |
| Schema strictness blocks real agent outputs | Marketing audit lesson #3: ship `extra=allow` initially; tighten after 3–5 real runs. |
| Concurrent meta-agent edits to shared substrate (Pi v007-style) | All shared substrate locked via `readonly_subprefixes` in each lane's `LaneSpec`. Critique-prompt SHA256 manifest provides audit trail. |
| Image composition with Pillow underperforms at scale | D13 default Pillow; benchmark at U6 implementation; switch to Cairo/skia only if blocking. |
| Cross-lane voice migration breaks holdout fixture lineage | D10 revised per TD-7 + TD-19: noise-floor-calibrated per-fixture regression bar (`max(5%, 2 × std_dev)`) on direct-cutover PR; merge blocked if any fixture regresses beyond bar. Rollback = `git revert` the migration PR. |
| Pre-publish review SLA breaches due to reviewer unavailability | D14: 25/50/100% SLA nag emails; auto-reject at 2× SLA. Operator can extend SLA per artifact via config override (deferred to implementation). |
| Static-image storage bills run high | Cost recording via `cost_recorder.record("fal", "image_gen", ...)` provides telemetry; budget envelope locked at implementation against marketing-audit's $220-425/run precedent. |

## Documentation / Operational Notes

- **Per-client launch runbooks** (U18 deliverable) walk operator through: voice corpus ingestion, brand asset collection, reviewer onboarding (email setup, SLA confirmation), initial demo pipeline run, ≥5 artifact publication tracking.
- **Concurrency operator playbook:** `MAX_PARALLEL_AGENTS` default 4. `fal_image` semaphore default 2 → dial up watching for fal.ai circuit-breaker trips. Documented in `docs/architecture/concurrency.md` update.
- **Storage backend selection:** production `R2GenerationStorage` requires `GOFREDDY_R2_*` env vars + IAM credentials; dev/test use `LocalDevPreviewStorage` with `GOFREDDY_STORAGE_BACKEND=local`. Documented in deployment guide.
- **Onboarding doc** (auto-generated from R26 schema + this plan): step-by-step "how to add client N+1" guide. Add to `docs/onboarding/client-onboarding.md` at U19 completion.
- **Audit log retention:** `review_audit/<client_slug>/<YYYY-MM>/audit.jsonl` retained indefinitely per compliance posture. Periodic archival to cold storage at implementation discretion.
- **Compliance rule-set versioning:** YAML files in `compliance/rule_sets/` are git-tracked. Version is the git commit SHA; legal sign-off recorded in `docs/plans/2026-05-13-002-<rule_set>-rule-set.md` companion docs.

## Sources & References

- **Origin document:** [docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md](../brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md)
- **Sizing memo:** Inline at origin doc §"Dependencies / Assumptions" (sized 2026-05-13 — 3-5 months sequential / 8-14 weeks parallel)
- **Lane registry architecture:** `docs/architecture/lane-registry.md`
- **Concurrency architecture:** `docs/architecture/concurrency.md`
- **x_engine port master plan:** `docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md`
- **x_engine rubric anchors precedent:** `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`
- **Marketing audit master plan:** `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md`
- **Stream A eval-fixes (env-gated):** `docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`
- **Stream C external absorptions:** `docs/plans/2026-05-11-003-external-absorptions-plan.md` (relevant for Plan B archive note)
- **Memory: linkedin_engine cold-start fix (2026-05-08):** `~/.claude/.../memory/project-linkedin-engine-cold-start-2026-05-08.md`
- **Memory: marketing audit shipping (2026-05-08):** `~/.claude/.../memory/project-marketing-audit-master-plan-2026-05-06.md`
- **CLAUDE.md** (project root) — 12-rule template
