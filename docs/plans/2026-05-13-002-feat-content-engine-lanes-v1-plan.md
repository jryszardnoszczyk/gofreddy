---
title: "Content Engine Lanes v1 — 4 New Lanes + Storyboard Extension + Shared Infra"
type: feat
status: active
date: 2026-05-13
origin: docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md
triage: 2026-05-13 (6 clusters resolved; 22 decisions applied; TD-26 judge-plan reconciliation; TD-27/28/29/30 site_engine integration; TD-31 Pass-4 4-lens review + Pass-5 4-agent YAGNI/completeness/cohesion audit); 2026-05-15 (TD-32 substrate-finishing pass — verified 8 substrate claims against current code; 6 corrections applied); 2026-05-15 (TD-33..TD-39 cross-cutting content + data-provider decisions — generic-first generalization toward SaaS/AI primary client mix; 5-provider ad-intel signal aggregator; SerpAPI+GSC SERP/SEO; source material + brand asset directory conventions; fixture authoring strategy; cache TTL defaults); 2026-05-15 (TD-40..TD-44 per-lane qualitative design — article_engine + image_engine + ad_engine + site_engine internal loop design, anchor calibration drafts, anti-pattern enumeration; AE-3 citation verification builds in v1 — no deferral); 2026-05-16 (TD-45..TD-53 closing-gap decisions — video=scripts-only per JR direction; GDPR EU + AI disclosure rule sets BUILD in v1; voice persona authoring workflow with extract CLI; brief merging across source lanes; SaaS/AI onboarding runbook template; cross-locale lane handling; real_client fixture authoring scaling strategy; storyboard/ad_engine kept independent; 5 overfitting reframes); 2026-05-16 (TD-54 comprehensive generic-first reframe — JR 3rd pushback on overfitting — expanded archetype enum 7→11 incl creators/e-com/agencies/indie-hackers; new rule sets `ftc_endorsement_us` + `ecom_consumer_us`; per-archetype defaults reference table; Generalization Justification rewritten to lead with "internet-native businesses"; e-com/creator/agency synthetic fixtures added; Klinika+DWF demoted to "first-onboarded examples" throughout); 2026-05-18 (portal coordination pass — Edit 1: U7 audit emits via `events.log_event(kind="review_required"|"review_approve"|"review_reject"|"sla_breach", client_id=<slug>, ...)` to per-client wide log, no separate `audit.jsonl`; Edit 2: new shared-infra unit U6b extends `KNOWN_KINDS` + `CANONICAL_FIELDS` per portal R-Lane-2 + R-Schema-1..3; every Phase B/C lane MUST emit `session_start`/`deliverable_ready`/`session_completed` moments via direct `log_event(kind='moment', ...)` calls — verified by cross-lane integration test. The `emit_moment` wrapper helper from the original 2026-05-18 portal-coordination pass was DELETED in the same-day TD-56 binary-cuts pass below; mandate stays, wrapper goes); 2026-05-18 (post-compact coherence pass — F1 video-posture prose clarification in §Problem Frame; F5 U18 Goal reframed to flag Klinika+DWF as first-onboarded examples not design-center; F2/F3 rule-set count + TD-55 fixture additions superseded by TD-56 same-day binary-cuts pass below); 2026-05-18 (TD-56 binary-cuts pass — 4-agent over-engineering review applied "no deferrals, accept or reject" — REJECTED: TD-55 public-exemplar fixtures (10 of 12), 4 of 5 new reviewer-assist checklists (kept only gdpr_eu), voice extractor CLI, HTML/JSON corpus loaders, SaaS/AI onboarding runbook template, corpus_checksum, read_briefs_merged priority semantics, emit_moment wrapper, rubric_resolver module, 7 of 11 archetypes, U19 full-pipeline stub; RECLASSIFIED: all 3 reviewer-assist checklists labeled "reviewer-assist NOT legal-grade compliance" per new §Compliance Posture; ADDED: §Cost Envelope + §Rollback & Recall Procedure + §Parallel-Track Risks closing 3 silent gaps from adversarial review)
---

## Triage Decisions Applied

Compact 1-line audit trail. Each TD's actual content lives inlined in the relevant unit/decision section below; this list is the chronological index. Full prose available in git history (commits 2026-05-13 → 2026-05-18).

**Premise (2026-05-13):** Hold full v1 scope + name 2 prospect archetypes — generic-factory premise is the growth bet; see §Generalization Justification.

**TD-1..TD-25 (2026-05-13 cluster triage, 6 batches, 32 findings → 22 decisions):**
- TD-1: pre-flight corpus pattern-scan in U18 (D5 risk mitigation)
- TD-2: `weekly_publish_target` + `pre_publish_reviewer_secondary` on R26 (reviewer-chokepoint mitigation)
- TD-3: HMAC signing key from env var; quarterly rotation; canonical-event idempotency (U7)
- TD-4: voice corpora protected (filesystem encryption + PII scrub + 7yr retention + Art. 17 erasure)
- TD-5: new §Plan-level Threat Model (3 exploits + CODEOWNERS + SPF/DKIM/DMARC)
- TD-6: D4 + `RUBRIC_VERSION_OVERRIDE` env (cache invalidation defense)
- TD-7: D10 regression bar `max(5%, 2×std_dev)` per-fixture (characterization spike pre-U11/U12)
- TD-8: D19 diff assertion strengthened (`extra='forbid'`, prose ≤500 chars, `tests/` covered)
- TD-9: D14 SLA breach = auto-pause + operator notification (non-destructive)
- TD-10: Stream A env-gated fixes graduate to unconditional before U1 (new U0 precondition)
- TD-11: D12 hybrid — per-lane rubric IDs + shared prose registry (no substrate invariant change)
- TD-12: per-client external gate (consent + legal-review prerequisite — real-world dependency, not plan-side phase)
- TD-13: U19 success bar adds operator-time measure (<8h to first green pipeline)
- TD-14: audit log → external encrypted storage; 7yr retention; reviewer-email pseudonymization
- TD-15: R2 per-client key prefix + IAM-scoped credentials; private bucket + signed preview URLs
- TD-16: CODEOWNERS file + SPF/DKIM/DMARC + 24h email-change cooling-off (TD-5 details)
- TD-17: placeholder-rule-set production-launch posture (two-reviewer signoff + 3/week cap)
- TD-18: D6 multi-rule-set merge DROPPED — v1 single rule_set_name only
- TD-19: `voice_persona_source` toggle DROPPED — U11/U12 direct cutover
- TD-20: U7 collapsed to 1-2 modules + 1 test file (~150-200 LOC `src/review/service.py`)
- TD-21: ad_engine `full_bundle` flag DROPPED (v1 = creative + LP only)
- TD-22: ig_single + ig_story fixtures added to U14; all 6 image_engine formats kept
- TD-23: `market_signal_compatible: bool` on rule sets (R19 no-op for incompatible rule sets)
- TD-24: v1.5 backlog table at end of Scope Boundaries with trigger conditions
- TD-25: Substrate Window protocol CUT entirely per Pass-6

**TD-26..TD-31 (2026-05-13 reconciliation + review passes):**
- TD-26: Judge Plan reconciliation — plan renamed 001→002; §Substrate Consumed added; per-criterion `dimension_scores`; no AE/IE/AD-9 kernel rubrics
- TD-27..TD-30: site_engine integrated mid-plan as 4th lane (TD-27 bundling rationale; TD-28 section-only scope; TD-29 marketing_audit+geo briefs; TD-30 anchors at `docs/rubrics/site-quality.md`)
- TD-31: Pass-4 (4-lens 35 findings, 14 plan edits) + Pass-5 (4-agent YAGNI/completeness/cohesion — 5 P0 substrate gaps, 8 overengineering items, 10 cohesion fixes; cut U7c; cut TD-25)

**TD-32..TD-55 (2026-05-15 → 2026-05-18 content-design + closing-gap rounds):**
- TD-32: substrate-finishing pass — 6 corrections to plan substrate claims (verified vs main `bdc8068`)
- TD-33: generic-first reframe (SaaS/AI primary mix; archetype enum expanded; locale/consent/brand_strictness fields)
- TD-34: ad-creative data providers — Foreplay + Adyntel + Meta Ad Library parallel via `signal_merger.py`
- TD-35: SERP + first-party SEO — SerpAPI Starter + GSC (shared OAuth client + per-client refresh tokens)
- TD-36: article_engine source material at `clients/<slug>/source_material/` (markdown/PDF/HTML/URL formats)
- TD-37: brand asset directory `clients/<slug>/brand/`; `strict` default; Pydantic-validated `tokens.json`
- TD-38: fixture authoring strategy — real_client out-of-repo, synthetic in-repo; ~3hr/(archetype × lane)
- TD-39: cache TTL defaults per source (Foreplay 24h, Adyntel 24h, Meta 12h, SerpAPI 24h, GSC 24h)
- TD-40..TD-43: per-lane internal design — see U13/U14/U15/U15b Approach sections for full prose (article_engine top-K=3 hybrid + AE-1..8; image_engine format-dispatch + IE-1..8; ad_engine 4/4/4/3 + AD-1..8; site_engine 3-tier mutation whitelist + SE-1..8)
- TD-44: AE-3 citation verifier BUILDS in v1 (no deferral) — `src/verification/citation_verifier.py` ~150 LOC
- TD-45: video = scripts + prompts only; no automated fal.ai I2V in v1
- **TD-46 (revised 2026-05-18 by TD-56):** v1 ships 3 reviewer-assist checklists only — `gdpr_eu` + `medical_pl` + `legal_pl`. Other 4 rejected. Reclassified as reviewer-assist NOT legal-grade (see §Compliance Posture).
- TD-47: **REJECTED 2026-05-18 by TD-56** — voice extractor CLI deferred to first SaaS client
- TD-48: **REJECTED 2026-05-18 by TD-56** — N-lane brief merger deferred; v1 single-source reader only
- TD-49: **REJECTED 2026-05-18 by TD-56** — SaaS/AI runbook template deferred to first SaaS client
- TD-50: cross-locale lane handling — `requires_native_judge` flag for non-European languages
- TD-51: real_client fixture authoring at scale — v1 manual; v1.5 trigger client #4; v2 trigger client #8+
- TD-52: storyboard ↔ ad_engine independent in v1 (no handoff; both produce scripts-only)
- TD-53: 5 overfitting reframes (SaaS fixtures per lane; consent reframe; TD-12 reframe; locale lead; SLA defaults)
- TD-54: **partially REJECTED 2026-05-18 by TD-56** — 11-archetype enum cut to 4; new rule sets rejected

**TD-56 (2026-05-18 binary-cuts pass):** 4-agent over-engineering review; "no deferrals, accept or reject." Rejected TD-55 (10 of 12 fixtures), 4 of 5 new reviewer-assist checklists, voice extractor, runbook template, corpus_checksum, emit_moment wrapper, rubric_resolver module, 7 of 11 archetypes; right-sized U19 to CI diff assertion; reclassified all reviewer-assist YAMLs as NOT legal-grade compliance per new §Compliance Posture. Added §Cost Envelope + §Rollback & Recall + §Parallel-Track Risks closing 3 silent gaps.

The unit/decision sections below are the canonical reference; this index points to where each decision actually applies.

---

# Content Engine Lanes v1 — 4 New Lanes + Storyboard Extension + Shared Infra

## Overview

Add a generic multi-client content factory to the gofreddy autoresearch system. Ship **four** new lanes (`article_engine`, `image_engine`, `ad_engine`, `site_engine`) plus a substantial extension to the existing `storyboard` lane (5 platform_targets × 3 format_modes + voice corpus input), five existing-lane modifications (`geo` + `monitoring` + `marketing_audit` brief emission per U9/U10/U10b, `linkedin_engine` + `x_engine` voice persona migration), and **seven** shared infrastructure pieces (per-client config object, voice persona framework, findings-brief contract, static-image composition module, pluggable compliance framework, pre-publish human review service, **Playwright-based site render utility**). The original a11y + perf audit utility (U7c) was cut per Pass-5 YAGNI audit; SE-6/SE-7 hand-graded for v1.

The 4th lane (`site_engine`) was integrated mid-plan per TD-27 because it consumes the same foundational shared infra as the other three content lanes — bundling amortises that investment across 4 lanes instead of 3 and avoids parallel-defining the same client-config / voice / brief / compliance / reviewer primitives twice.

**Terminology:**
- **Onboarded client** — a real client with voice corpus consent obtained and ≥5 artifacts published to real channels during their launch window. v1 onboards Klinika Melitus and DWF Poland.
- **Demonstrated archetype** — a test-only client config instantiated to validate the config-only onboarding mechanism. Stub data acceptable; not subject to the "≥1 real-client fixture per archetype" requirement that applies to onboarded archetypes. U19's `b2b_tech` falls here.
- The D11 archetype-level CI assertion (≥1 real_client fixture) applies only to onboarded archetypes; `stub_allowed: true` archetypes are excluded.

First two clients onboarding: **Klinika Melitus** (Warsaw aesthetic dermatology, `b2c_aesthetics` archetype, `medical_pl` reviewer-assist checklist) and **DWF Poland** (international law firm, `b2b_regulated` archetype, `legal_pl` rule set). The architecture is designed for indefinite future clients — onboarding a new client must be a config-and-corpus operation, not a code change.

v1 is production-grade. No demo deadline. Every Success Criterion must be met by output that's actually shippable to real clients on real channels. Realistic build window: 3–5 months sequential / 8–14 weeks with parallel workstreams (JR accepted timeline 2026-05-13).

## Generalization Justification

**The design center is "internet-native businesses" broadly — not regulated B2B services.** gofreddy is a generic marketing agency for the digital-economy client mix: SaaS tools, AI companies, e-commerce brands, creators and influencers, marketing/dev agencies, indie hackers, online-service businesses. Klinika Melitus (Polish aesthetic clinic) and DWF Poland (international law firm) are the **first 2 onboarded clients — neither is representative of the expected client mix**. Designing the loops, rubrics, data providers, and defaults around Klinika+DWF specifics is overfitting; designing them around any single archetype is premature optimization. v1 design center = the generic internet-native business case; per-client config carries vertical adjustments.

**Expected client mix and onboarding readiness:**

| Archetype | Description | Default reviewer-assist checklists | Typical brand-asset maturity | Typical voice-corpus shape | v1.5+ priority |
|---|---|---|---|---|---|
| `b2b_saas` | SaaS tools, dev tools, AI-infra, vertical SaaS — gofreddy.ai canonical (site_engine SE-1..8 calibration target) | `gdpr_eu` (if EU-targeting; otherwise none in v1) | High (Figma design system, SVG logos, defined typography) | Public blog archives, founder Twitter/LinkedIn, customer interviews | v1 canonical |
| `b2c_aesthetics` | Aesthetic / wellness / dental / dermatology (Klinika family) — first onboarded example | `medical_pl` (placeholder) + `gdpr_eu` | Low-Medium (often only logo + photography library) | Often private (consent-required); fallback to `style_anchors`-only is degraded | First-onboarded |
| `b2b_regulated` | Law, finance, healthtech, fintech, public-sector consultancies (DWF family) — first onboarded example | `legal_pl` (placeholder) + `gdpr_eu` | Medium (logos + brand book; rarely a design system) | Mixed (some public partner content; mostly private) | First-onboarded |
| `b2b_tech` | Architectural-test stub (U19) — not onboarded; validates config-only onboarding | None (stub) | Stub | Stub | N/A (stub only) |

**Generic-first posture preserved:** the enum is cut to 4 v1 values, but the substrate (per-client config + voice + briefs + reviewer-assist) works generically for any archetype. When first client of `b2b_ai_first` / `b2c_ecommerce` / `creator_solo` / `creator_managed` / `b2b_agency` / `b2b_consultancy` / `indie_hacker` lands, adding that archetype is a 1-line Literal edit + 1 row in the per-archetype defaults table + 1-2 days operator authoring of relevant reviewer-assist checklist if needed. Per-archetype defaults for those v1.5+ archetypes live in `docs/runbooks/archetype-defaults-v1.5-prospects.md` (operator-authored on demand; not v1 plan deliverable).

**Why Klinika+DWF as first 2 onboarded:** they are EXISTING relationships (Klinika = Dr. Maria Noszczyk family connection; DWF = pre-existing professional channel) that enable v1 to ship with real-client validation. They are **opportunistic first-clients**, NOT design targets. The architecture must work equally well for the primary archetypes above without per-vertical code changes — that's the falsification gate (see below).

**Falsification gate (revised):** if 6 months post-v1-ship the onboarded client mix is still ONLY Klinika+DWF (no SaaS, no creator, no e-com, no agency), the generic-factory architecture has produced zero incremental value over a 2-lane purpose-built regulated-vertical build. Revisit at that gate.

**v1 reviewer-assist checklists (BUILD in v1 per TD-46 revised 2026-05-18):**
- `gdpr_eu` — baseline for EU-targeting clients; load-bearing for Klinika+DWF (both EU)
- `medical_pl` (placeholder) — first-onboarded `b2c_aesthetics` example (Klinika); legal-review pending
- `legal_pl` (placeholder) — first-onboarded `b2b_regulated` example (DWF); legal-review pending

**Posture:** these are reviewer-assist YAMLs that accelerate pre-publish-review pattern-matching. They are **NOT** legal-grade reviewer-assist gates. Pre-publish human review (U7) carries the actual safety weight. See §Compliance Posture for the engagement-letter implications.

**Architecture supports v1.5 candidates** (authored on first prospect, ~1-2 operator-days each from public regulatory text): `ai_disclosure_eu`, `ai_disclosure_us`, `ftc_endorsement_us`, `ecom_consumer_us`, `medical_de`/`medical_fr`, `legal_*` per-jurisdiction, `soc2_b2b`, `fintech_*`, `healthtech_*`, `dsa_eu`, `coppa`, `tcpa`, `casl`.

**Per-client adjustments (NOT architectural changes):**
- `client.yaml.locale = {gl, hl, google_domain, country, city, requires_diacritic_normalization, requires_native_judge}` — defaults `en-US`; Klinika+DWF override to Polish
- `client.yaml.brand_strictness = "strict" | "permissive"` — defaults `"strict"`; `"permissive"` for archetypes with weaker brand-asset maturity (creators, indie hackers, Klinika)
- `client.yaml.archetype` — drives rubric softening defaults + content_denylist defaults + voice_corpus_consent_required defaults + reviewer SLA defaults per archetype-defaults reference table (§Operational Notes)
- Per-client rubric overrides — e.g., SE-8 anti-slop anchors soften for `b2c_aesthetics` (medical photography is legitimate); SE-1 CTA prominence softens for `b2b_regulated` (legal firms don't want screaming CTAs); SE-4 voice fidelity calibration shifts for `creator_*` (much stronger personal voice signal in corpus)

If you're considering naming specific prospects rather than archetypes, this section can be updated to carry their slugs (placeholder `clients/<prospect-slug>/client.yaml` files with `status: prospect` for tracking) — useful for sales-pipeline accountability, optional for the architectural justification.

## Problem Frame

Existing autoresearch lanes (`geo`, `competitive`, `monitoring`, `storyboard`, `marketing_audit`, `x_engine`, `linkedin_engine`) don't cover the highest-volume content channels most clients buy:
- Short-form video on TikTok / IG Reels / IG Stories (v1 produces script + scene-by-scene plan + image briefs for keyframes only; operator runs fal.ai I2V manually post-promotion per TD-45 — no automated video binary generation)
- Long-form articles (blog SEO + LinkedIn Article)
- Static visuals (IG single, IG carousels, IG story slides, LinkedIn document carousels, hero images, ad statics)
- Paid ad creative (Meta + LinkedIn in v1 build; Google Ads not built in v1 — re-evaluate only if a client onboards with Google Ads as primary channel)
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
- **R23–R25** Lane chain orchestration — addressed by Units U9 (geo emission) + U10 (monitoring emission). R24 (only article_engine consumes briefs in v1) and R25 (spawn briefs not built — rejected) define scope boundaries; U13 wires article_engine brief consumption
- **R26** Per-client config object — addressed by Unit U2
- **R27** Section-level site rendering pipeline — addressed by Unit U7b (Playwright headless render, font-load wait, configurable viewport)
- **R28** Site a11y + perf audit — **not built** per Pass-5 YAGNI audit; SE-6 + SE-7 become operator-hand-graded for v1 against U7b's screenshot + console output. Re-evaluate only if a11y regression observed in production OR operator-grading >5 min per section.
- **R29** Site visual hierarchy + CTA prominence rubric (SE-1) — addressed by U15b via render judge consuming `docs/rubrics/site-quality.md`
- **R30** Site copy clarity + plain-English rubric (SE-2) + claim honesty + anti-overselling rubric (SE-3) — addressed by U15b via text judge consuming `docs/rubrics/site-quality.md`
- **R31** Site voice persona fit rubric (SE-4) — addressed by U15b consuming U3 voice persona framework unchanged
- **R32** Site brand-token + aesthetic-fit rubric (SE-5) — addressed by U15b consuming new `brand_tokens` field on R26 ClientConfig (U2)
- **R33** Site a11y + semantic structure rubric (SE-6) + performance rubric (SE-7) — addressed by U15b via operator-hand-grading against U7b screenshot + console output per Pass-5 audit (U7c cut for v1)
- **R34** Site anti-slop rubric (SE-8) — addressed by U15b via render judge with anti-slop calibration prose seeded from 2026-05-13 landing-page session

Plus existing-lane voice migrations (R20): Unit U11 (`linkedin_engine`) + Unit U12 (`x_engine`).
Plus Klinika + DWF instantiation: Unit U18.
Plus client #3 architectural success bar: Unit U19.

Success Criteria from origin (production-grade, all must hold):
- Holdout fixtures green per archetype, with ≥1 real-client-content fixture per archetype
- End-to-end demo per onboarded client, both reviewer-assist gates passing
- Client #3 onboards config-only (validated against b2b_tech stub archetype)
- Cross-lane voice consistency: same persona consumed unchanged by 4 lanes
- ≥5 client-approved-and-published pieces per onboarded client during launch window

## Scope Boundaries

(Carry forward from origin doc Scope Boundaries section, restated for plan reviewers.)

**Not in v1 build:**
- No human shoots (all video via fal.ai I2V at operator's discretion)
- **No automated fal.ai I2V in v1 (per TD-45 + JR direction 2026-05-16):** lanes produce video PLANS (scripts + scene-by-scene prompts + image briefs for keyframes + voiceover scripts + on-screen text overlays + CTA copy). Operator runs fal.ai I2V manually using the produced plan. Rationale: video generation at ~$0.30-1.50 per 5-10s clip × evolution-loop iteration counts is cost-prohibitive in v1; manual generation post-promotion bounds video cost to ~$10-50/onboarded-client/month vs $1000s for fully-automated. Applies to: ad_engine Reels Ad output (U15), storyboard educational/explainer output (U8). v1.5 reconsiders only if a client contracts for high-volume video output that justifies the spend.
- No clinical Klinika visuals (per-client `content_denylist` enforced)
- No Google Ads variant generator (platform parameter supported but not built; re-evaluate only if a client onboards with Google Ads as primary channel)
- No first-party platform Marketing API integration (Meta/Google/LinkedIn ad account perf APIs deferred)
- No x_article adaptor in `article_engine` (niche audience)
- No findings-brief integration beyond 2 demo pairs (`geo → article_engine`, `monitoring → article_engine`)
- No article-engine spawn brief emission (R8 dropped — would be dead infra in v1)
- No targeting/bid/budget recommendations from ad_engine in v1 (per triage TD-21; `full_bundle` flag dropped). Reintroduce in v1.5 when a client contracts for full-bundle output.
- No voice persona sub-fields beyond `corpus_path`, `voice_rules`, `style_anchors`
- No cross-lane rubric primitive (hybrid per TD-11 revised: per-lane rubric IDs + shared prose registry. Single prose location for Art. 14 amendments, no substrate invariant change). True cross-lane primitive (one ID referenced by N lanes) **rejected** — adds substrate complexity for no demonstrated need.
- No standalone longform/legal_alert/Chambers submission/personal_brand/reviews/CRO/deal_announcement lanes
- No email/podcast/SMS/push-notification lanes
- No ad management ops automation
- No client billing / contract infrastructure
- **No full-page site composition** (`site_engine` ships section-level only per TD-28; sections: hero, value_prop, social_proof, faq, cta, pricing). Full-page rewrites not built; re-evaluate only if a client requests a from-scratch landing build.
- **No design-system / component-library generation** (`site_engine` mutates within existing client brand_tokens; doesn't propose token changes)
- **No multi-breakpoint mutation** (`site_engine` mutates a single responsive output; doesn't optimise mobile/tablet variants separately in v1)
- **No React / Vue / SPA output from site_engine** (vanilla HTML+CSS+JS only)
- **No SEO meta-tag generation from site_engine** (consumes meta from briefs; doesn't generate)
- **No backend / form / payment integration from site_engine** (presentation layer only)

**Architecture supports but build deferred:**
- N reviewer-assist checklists (architecture takes any; **v1 ships 3 checklists** per TD-46 revised 2026-05-18: `medical_pl` (Klinika placeholder), `legal_pl` (DWF placeholder), `gdpr_eu` (load-bearing for Klinika+DWF as EU clients)). **Posture:** these are reviewer-assist YAMLs, NOT legal-grade reviewer-assist gates — pre-publish human review (U7) is the safety mechanism; the YAML accelerates reviewer pattern-matching. Engagement-letter language disclaims compliance opinion (parallel-track risk, JR-owned). **v1.5 candidates** (authored on first prospect of each archetype, ~1-2 operator-days each from public regulatory text): `ai_disclosure_eu`, `ai_disclosure_us`, `ftc_endorsement_us`, `ecom_consumer_us`, `soc2_b2b`, `fintech_*`, `healthtech_*`, `medical_de`/`medical_fr`, `legal_*` per-jurisdiction. **Default checklist assignment per archetype:** `b2c_aesthetics` = `medical_*` + `gdpr_eu`; `b2b_regulated` = `legal_*` + `gdpr_eu`; `b2b_saas` (gofreddy canonical) = `gdpr_eu` (if EU-targeting; otherwise none in v1).
- Google + x_ads + tiktok_ads + reddit_ads platforms (parameterized; variant generators not built)
- ~~Per-campaign `full_bundle` toggle in ad_engine~~ — dropped per triage TD-21. Targeting/bid/budget output is v1.5.
- New archetypes added to fixture tree (slots ready; filled on client onboarding)
- **Locale config beyond Polish + English defaults** (architecture supports any `gl/hl/google_domain` triple; Polish-specific diacritic normalization is opt-in via `locale.requires_diacritic_normalization` flag; v1 ships defaults for `en-US` + `pl-PL`, additional locales added per-client as needed)
- **Voice corpus consent posture per archetype** — Klinika-style `consent_required: true` is per-client config, not architecture-default. SaaS/AI archetype defaults `consent_required: false` (public content), `b2c_aesthetics` defaults `consent_required: true` (consent load-bearing per parallel-track risk #1)

## Compliance Posture

**Reclassified 2026-05-18 per adversarial review ADV-2 + JR direction:** The YAMLs under `reviewer_assist/checklists/<name>.yaml` are **reviewer-assist checklists, NOT legal-grade compliance gates**. This distinction is load-bearing for liability management and client communications:

- **What they are:** structured YAMLs that accelerate pre-publish reviewer pattern-matching against known regulatory surfaces (GDPR articles, medical-claim conventions, legal-claim conventions). They flag candidate concerns; a human reviewer (U7) makes the actual ship/no-ship call.
- **What they are NOT:** legal-grade compliance gates authored by qualified counsel. v1 ships `gdpr_eu` + `medical_pl` (placeholder) + `legal_pl` (placeholder), all authored by JR/operator from public regulatory text without outside-counsel review.
- **Safety mechanism:** pre-publish human review (U7) is the actual safety net. The reviewer-assist YAMLs reduce per-artifact reviewer time by ~30-50% (pattern-matching speedup) but DO NOT substitute for reviewer judgment.
- **Client engagement-letter language (JR-owned, parallel-track risk):** must explicitly disclaim that gofreddy provides any compliance opinion. Reviewer-assist output is descriptive (flags concerns) not prescriptive (declares compliance). Engagement letter states "client retains responsibility for compliance with applicable regulations; gofreddy's pre-publish checks are operational quality controls, not legal opinions."
- **Why the distinction matters:** non-lawyer-authored YAMLs called "compliance gates" create false confidence that masks regulatory tail-risk (Polish GDPR fines €20K-€100K small enterprise; FTC enforcement actions). The reclassification keeps the same code + workflow but stops representing it as something it isn't.
- **Internal code naming:** The engineering term "compliance" persists in module names (`src/compliance/judge.py`, `evaluate_compliance()`, `COMPLIANCE_JUDGE`) as shorthand for "YAML-driven pre-publish check." This is internal-only nomenclature; all external/client-facing language uses "reviewer-assist."
- **First-author trigger for new checklists:** when a client of a new archetype enters the onboarding pipeline (e.g., first SaaS/AI client → `ai_disclosure_*`; first e-com → `ecom_consumer_us`; first creator → `ftc_endorsement_us`), the operator authors the checklist from public regulatory text in ~1-2 days. No substrate change required (D20: YAML-only additions). The checklist ships with the same reviewer-assist posture, not as a legal-grade gate.

This posture applies to all reviewer-assist artifacts referenced elsewhere in the plan (TD-46, U5, U7, U16/U17, D12, D20, D25, §Risks). When prose says "reviewer-assist gate" or "reviewer-assist checklist," read it through this section's framing.

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

**Landing-page rebuild session (2026-05-13, ~6h pair-iteration on gofreddy.ai) — patterns site_engine inherits:**
1. **Anti-slop calibration data is perishable.** SE-8 anchors reference 2025-26 generic-AI signals ("lime + purple + dark gradient", three-icon trios with generic gradients, "We help you..." copy openings). These will date as templates evolve. Quarterly review cadence on `docs/rubrics/site-quality.md` baked into Documentation/Operational Notes.
2. **Plain-English bar is falsifiable.** SE-2 "non-domain reader can paraphrase the offering after one read" beats abstract "jargon-free" claims. Site_engine judges use this exact test.
3. **Honest-claims discipline beats hedge language.** The session repeatedly cut "up to N×", "designed to", "leading", and anthropomorphized agent capability ("autonomous", "intelligent"). SE-3 anchors codify this — every numeric / comparative claim must be defensible inside 24h.
4. **Interactive over passive.** Hover-detail panels on the §01 SVG diagram landed better than static cards. SE-8 anti-slop includes "hand-touch signals" as a Score-5 anchor.
5. **Section overflow is silent.** Subline text overflowed the bubble at the 4th iteration even though earlier sublines fit. Render-judge with explicit screenshot comparison catches what hand-review misses.
6. **Iteration speed matters.** "1-2 day max for quality work" framing pairs with section-level v1 scope (TD-28). Full-page rewrites would slow this iteration loop.
7. **Cut redundant sections rather than rewriting them.** The §05 "Built for" audience-shapes section was cut after one challenge because §01 + §04 already did the work. Site_engine doesn't auto-cut sections in v1, but reviewer signals that mark a section as "redundant with another section" should feed back into the next cycle's anti-slop calibration.

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

**Static-image composition (U6):** Codebase has strong local patterns; Pillow vs Cairo vs skia is punted to implementation (default Pillow). No external research dependency.

**Site rendering (U7b only, added per TD-27; U7c audit utility cut per Pass-5 YAGNI audit):** Playwright is the one net-new dev-tier dependency. Mature, well-documented, standard for its purpose:

| Tool | Purpose | Upstream | Version pin |
|---|---|---|---|
| `playwright` (Python) | Headless Chromium render for site sections in U7b. Captures screenshots + DOM snapshot + console errors at configurable viewport with font-load wait. | https://playwright.dev/python | `>=1.45` (added to `[dependency-groups.dev]`) |
| ~~`@axe-core/cli`~~ | ~~a11y audit subprocess in U7c~~ — **cut per Pass-5 YAGNI audit; SE-6/7 hand-graded for v1.** | — | — |

Both are dev-tier only — never invoked from production API path. CI workflow (`.github/workflows/test.yml`) installs both before pytest. Operator onboarding doc names both as prereqs.

**No deeper external research on site-quality evaluation.** Calibration prose at `docs/rubrics/site-quality.md` is derived from the 2026-05-13 gofreddy.ai landing-page session (~6h of opinionated review captured as Score-3 failure modes + anti-gaming clauses). External academic references on landing-page conversion / heuristic evaluation deliberately not pulled in — that literature drifts faster than the session calibration tracks anti-slop patterns specific to 2025-26 generic-AI defaults.

## Key Technical Decisions

| ID | Decision | Rationale |
|---|---|---|
| D1 | Build on existing `autoresearch/` substrate; archive `autoresearch_v2/` | JR decision 2026-05-13. No double-port concern, simplifies sequencing. |
| D2 | Mirror x_engine/linkedin_engine pattern for `article_engine`, `image_engine`, `ad_engine`, **`site_engine`** — including `count_findings → 0` and `findings_promotion` for substrate compatibility. site_engine adds a structural pre-render gate (U7b render output → sanitizer + lane-source console-error check) BEFORE LLM scoring; SE-6/SE-7 hand-graded per Pass-5 audit (U7c cut). | x_engine port master plan v13 + linkedin_engine v040 cold-start fix established the content-lane pattern. site_engine's pre-render gate is the same shape as x_engine's slop-check subprocess — additive substrate, no invariant change. |
| D3 | New rubric ID prefixes: **AE** (article_engine), **IE** (image_engine), **AD** (ad_engine), **SE** (site_engine). 8 rubrics each for the four new lanes (per `_rubric_ids` helper); 6 each for x_engine/linkedin_engine stay unchanged. SE-1..SE-8 prose lives in `docs/rubrics/site-quality.md` per TD-30 (top-level rubric file); AE/IE/AD prose lives inline in `rubrics.py` per the original convention. | Avoid prefix collisions; 8-rubric default matches GEO/CMP/MON/SB/MA. Content lanes' rubric prose authoring is the long pole (~30–40 lines × 32 rubrics ≈ 960–1280 lines; site_engine's SE-1..SE-8 already authored in `docs/rubrics/site-quality.md` — saves ~250 lines). |
| D4 | Replace the hardcoded magic number (currently `53` on main, was `52` when this plan was first drafted) with derived `assert len(RUBRICS) == sum(len(spec.rubric_ids) for spec in LANES.values())` | Per spec-flow-analyzer P1-5: 6× bigger migration than X/LI port; manual lockstep on a single integer creates merge-bug risk. Derived count removes the entire class of bugs across all per-lane PRs. The recent jump from 52→53 via X-9 (`896f366`) is precisely the kind of drift this resolves. |
| D5 | Compliance hard-block = score 0 → standard frontier rejection. Soft-warn = score scaled down + flag persisted to per-fixture sidecar `compliance-meta.json`. **No in-session regen-with-feedback in v1.** | Existing `evaluate_variant.py` treats judge output as scalar score plumbed to the frontier. Adding regen-with-feedback is a substantial new primitive; not needed for v1 since frontier evolution is the regen mechanism. |
| D6 | **REVISED per triage TD-18:** v1 `evaluate_compliance` takes a **single `rule_set_name`** (not a list). `ComplianceRuleSet` schema still accepts a list field, but length is constrained to 1 in v1. Multi-rule-set merge logic + max-severity policy + cross-rule-set merge test deferred to first client onboarding that needs two rule sets. Klinika = `medical_pl`; DWF = `legal_pl`. | Per spec-flow-analyzer P0-2 (original) + triage TD-18 (revised). v1 has zero multi-rule-set consumers; YAGNI on merge logic until a real client demands it. ComplianceRuleSet schema stays unchanged so migration is additive. |
| D7 | Per-client config = versioned YAML in `clients/<slug>/client.yaml`. Loaded into a frozen Pydantic model at lane-start, snapshot recorded in run manifest. **No hot-reload in v1.** Mid-run config drift is fail-loud at finalize **on lineage-affecting fields only**; reviewer-routing fields are carve-outs. Lineage-affecting fields (any change fails the run): `voice_persona_ref`, `reviewer_assist_checklists`, `enabled_channels`, `content_denylist`, `brand_tokens` path/contents, `site_engine.target_url`, `site_engine.sections_in_scope`, `archetype`. **Reviewer-routing carve-outs** (mid-run change does NOT fail finalize; logged + new-value picked up on next dispatch): `pre_publish_reviewer.email`, `pre_publish_reviewer_secondary.email`, `pre_publish_reviewer.display_name`, `weekly_publish_target`. Rationale: reviewer absence (vacation, illness, departure) is a real-world ops event that can happen during a multi-hour evolution run; destroying the run because the clinic admin emailed "route to Anna this week" is unacceptable. Email-change still requires the TD-16 24h cooling-off confirmation flow — the run-manifest carve-out only governs whether finalize fails, not whether the change itself is honored. | Per spec-flow-analyzer P0-3 + Pass-4 reliability-cascade audit. Lineage integrity matters for scoring substrate; reviewer routing is operational metadata that should not invalidate hours of evolution work. |
| D8 | Findings-brief source = **promoted-baseline archive only**. Variant-emitted briefs are visible only inside that variant's evaluation; cross-lane consumption is post-promote | Per spec-flow-analyzer P0-4. Kills orphaned-brief problem; simplifies caching. |
| D9 | Findings-brief consumption = sync file-based; top-K-by-priority batch (default K=3, configurable per client); staleness check via `produced_at` + optional `valid_until`; missing/empty/malformed = lane degrades to standalone | Per spec-flow-analyzer P0-4. Mirrors existing `findings_promotion` file convention. |
| D10 | **REVISED per triage TD-7 + TD-19:** Voice persona migration is a **direct cutover** (no toggle). Pre-U11/U12 precondition: run 5 repeated holdout passes per fixture in `legacy` mode (current per-lane voice reference) to measure within-fixture composite std dev. Set per-fixture regression bar at **`max(5%, 2 × std_dev)`**. CI gate enforces. Merged code has only the `shared` path; if a fixture would regress, fix the persona or fixture before merging — don't merge a toggle. | Per spec-flow-analyzer P0-5 (original) + triage TD-7 + TD-19 (revised). Flat 5% bar was unfalsifiable on noisy fixtures; toggle was dual-codepath shim for a one-time migration. Direct cutover gated on noise-floor-calibrated bar is the production-grade choice. |
| D11 | Holdout fixture provenance: new `data_provenance: real_client \| synthetic \| stub` field in fixture metadata. Archetype-level CI assertion: ≥1 `real_client` fixture per onboarded archetype. `stub`-allowed archetypes flagged explicitly in R26 archetype config | Per spec-flow-analyzer P0-6. Without label, success criterion "real-content fixtures required" is unenforceable. |
| D12 | **REVISED per triage TD-11 (hybrid):** Lane-side `LaneSpec.rubric_ids` carries per-lane compliance rubric IDs (preserves existing per-lane RUBRICS pattern; no substrate invariant change). Rubric prose for compliance rules lives in a single shared `compliance_rules` registry per rule set (file: `reviewer_assist/checklists/<name>.yaml` per D20). Each lane's compliance rubric prose template resolves to the shared registry entry at evaluation time — so editing a single YAML rule updates all 7 lanes' interpretations. | Same maintainability win as cross-lane primitive (single prose location for Art. 14 amendments) without touching `rubrics.py:1529` invariant. ~50–100 LOC in U5 for the resolve-at-evaluation-time helper. Lower architectural risk than the cross-lane rubric primitive originally proposed. |
| D13 | Static-image composition module = **Pillow** by default. Multi-slide carousel = sequential slide-by-slide generation with brand-anchor passed slide-to-slide (no parallel) | Python-native, well-documented, sufficient for IG/LinkedIn document carousel needs. Sequential ensures brand consistency (slide 2 references slide 1's stamp position). Evaluate Cairo/skia only if Pillow performance becomes blocking. |
| D14 | **REVISED per triage TD-2-revised + TD-9 + TD-17:** Pre-publish human review = email-based, token-signed approve/reject URLs. **Per artifact: primary reviewer signs off; if no response at `escalate_at_pct_sla` (default 50%), parallel email to `pre_publish_reviewer_secondary` — either reviewer's click resolves; first-click wins; secondary's approval logged with `reviewer_role: secondary`.** SLA breach = nag at SLA target, then **auto-pause + operator notification at 2× SLA** (artifact stays in queue until explicit resume/escalate; not destroyed). Manual reviewer rejection IS terminal (artifact discarded, reason logged). Hard-block compliance flags cannot be approved; soft-warn flags MAY be approved (reviewer override logged). **While placeholder rule sets are active (TD-17): mandatory two-reviewer sign-off (both primary AND secondary must explicitly approve before publish) + weekly publish rate cap ≤3/client. Soft-warn flags additionally trigger a parallel email to the secondary reviewer at submission time (not after 50% SLA) so two reviewers see the soft-warn together — this is distinct from the secondary-escalation flow which fires only on primary-unresponsive at 50% SLA.** **No in-engine edit-feedback loop in v1.** | Per spec-flow-analyzer P1-1 + triage TD-2-revised + TD-9 + TD-17. Auto-pause prevents reviewer-vacation cascade failure; secondary reviewer prevents single-person-dependency; two-reviewer sign-off compensates for placeholder rule sets. |
| D15 | ad_engine variant diversity enforcement = structural N-token-overlap check between hook slides (cheap, deterministic) + R19 rubric dimension. Threshold locked in compliance-judge-anchor work | Per spec-flow-analyzer P1-3. Pure rubric incentive is soft; structural gate forces real diversity. |
| D16 | Foreplay empty result for client domain = lane runs with empty ref set, logs degraded-signal warning, R19 "market-signal alignment" dimension drops to no-op for that variant | Per spec-flow-analyzer P1-3. Mirrors broader Foreplay-signal-reliability parallel-track risk. |
| D17 | Storyboard default `platform_target = youtube_long` when absent. `format_mode + content_denylist` intersection empty space = lane refuses to start with explicit error | Per spec-flow-analyzer P1-4. Fail-loud per CLAUDE.md Rule 12; never silent zero-output run. |
| D18 | Per-lane increments for RUBRICS bumps. Order: article_engine → image_engine → ad_engine → **site_engine** → compliance-per-lane (7 sub-units, one per content lane carrying reviewer-assist gates). Each increment is a single PR that bumps the assert and adds rubric IDs + `LaneSpec` tuple in the same diff. site_engine increment is +8 (53 + 24 AE/IE/AD + 8 SE = 85 lane rubrics, +7 compliance IDs single-rule-set-per-client = **92 total** per §New-lane Substrate Wiring Checklist Item 5). | Per spec-flow-analyzer P1-5. Atomic merge is too risky; per-lane increments are reviewable. D4's derived-count removes the manual lockstep risk. site_engine lands AFTER ad_engine because U15b depends on U7b — site_engine merges in lane order (article → image → ad → site_engine). |
| D19 | **REVISED per triage TD-13:** Client #3 onboarding test = (a) structural diff assertion (zero code change in `src/{clients,voice,briefs,compliance,review,ads,generation}/` + `autoresearch/lane_registry.py` + `src/evaluation/rubrics.py` + `autoresearch/archive/v007-curated/workflows/__init__.py` + `tests/`), (b) end-to-end pipeline run against `b2b_tech` stub archetype with stub corpus + stub persona + stub reviewer (auto-approve), AND **(c) onboarding-time clock measured by a teammate/fresh-agent who did NOT author the substrate: timer starts at first `clients/_stub_b2b_tech/client.yaml` commit, ends at first green pipeline run; target <8 hours active.** Recorded in `docs/plans/2026-05-13-002-onboarding-time-measurements.md`. | Per spec-flow-analyzer P1-6 + triage TD-13. Structural diff alone is necessary-but-vacuous; operator-time proves config-only onboarding is actually operationally feasible, not just structurally permitted. |
| D20 | Compliance rule sets are **data-driven** (YAML in `reviewer_assist/checklists/<name>.yaml`), not Python code | Per spec-flow-analyzer P1-6. Required for the "config-only onboarding" success criterion to hold when client #3 needs a new rule set (e.g., `ftc_consumer_us`). |
| D21 | image_engine quality gate = **score-only, no regen**. First-usable image accepted from fal.ai; vision sub-judge scores it post-hoc as part of variant fitness. No mid-run R2-to-LocalDev storage fallback | Per spec-flow-analyzer P1-2. Avoids new regen primitive (consistent with D5). |
| D22 | image_engine storage backend selection is environment-driven, not lane-driven. Production runs use `R2GenerationStorage`; dev/test runs use `LocalDevPreviewStorage`. Configured via `GOFREDDY_STORAGE_BACKEND` env var read at app init | No mid-run fallback (D21). Matches storyboard's existing convention. |
| D23 | Add `fal_image=N` semaphore to `autoresearch/concurrency.py` before image_engine ships. N = whatever fal.ai's account-level concurrency allows (operator to confirm at implementation). | Per spec-flow-analyzer P2-3. image_engine + ad_engine both hit fal.ai heavily; current global `MAX_PARALLEL_AGENTS=4` can trip fal's 3-failure circuit breaker. **Note on Plan B U9 consistency:** Plan B U9 collapsed 5 per-resource semaphores to one global cap because the only production bottleneck was Claude Max throttling — which the single cap solves. fal.ai is a different shape: hard 3-strike circuit breaker (not throttle) + account-level concurrency limit (not request-rate limit). The new `fal_image` semaphore introduces ONE additional per-resource semaphore for this distinct shape, NOT a reversion of the Plan B U9 collapse. Alternative considered: bump `MAX_PARALLEL_AGENTS` instead and let fal's circuit breaker do the work — rejected because fal trips fatally (not throttled retries) and concurrent claude+codex+fal+judge work would saturate the single cap. |
| D24 | image_engine vision sub-judge backend = **Gemini 2.5**, built fresh in U14 on the Gemini 2.5 SDK as a rubric-driven judge (`src/evaluation/vision_judge.py`, ~80 LOC, new file). NOT a reuse of `image_preview_service.verify_preview()` — that is a fixed 2-axis preview QA (scene_score, style_score), a sibling utility not a base primitive. Used for visual rubrics (carousel arc, brand consistency, info-density legibility) that require multimodal evaluation; text rubrics (alt-text quality, accessibility) stay on claude/opus outer judge. | Visual rubrics can't be scored by a text-only judge. Gemini 2.5 is the same vendor already integrated in `image_preview_service.py` for preview QA, so vendor surface doesn't grow; the new judge primitive is rubric-driven (accepts arbitrary `rubric_id`, emits `dimension_scores`) and dispatched from `evaluate_variant.py` per-rubric. Alternatives: GPT-4V (new vendor surface), claude/opus vision (not currently wired). U14 file list extended with `src/evaluation/vision_judge.py`. |
| D25 | Compliance-judge backend (used by U5's `evaluate_compliance` for the LLM-judged portion of the compliance rubric) = **`claude/opus`** (default). Stored as a module-level 2-tuple constant in `src/compliance/judge.py`: `COMPLIANCE_JUDGE = ("claude", "opus")`. Operator override via `COMPLIANCE_JUDGE_BACKEND` / `COMPLIANCE_JUDGE_MODEL` env vars read at call time. Applies to the **7 compliance-gated lanes** in v1 (storyboard, article_engine, image_engine, ad_engine, **site_engine**, linkedin_engine, x_engine). Geo has no reviewer-assist gate. | Compliance correctness is the most-consequential judge call (false-negative = regulator-flagged published artifact). Frontier-class + diverse from inner-loop (codex/gpt-5.5) per `judge-decisions-2026-05-11.md`. **Why 2-tuple constant instead of singleton class:** a singleton abstraction over a 2-tuple is wasted ceremony; constant + env-var override is the simpler shape and matches `cc212c2` per-step-split conventions. (D25 simplified per Pass-5 audit.) |
| D26 | site_engine **vision-sub-judge dispatch** mirrors D24 image_engine pattern. Visual rubrics SE-1 (hierarchy), SE-5 (brand-token fit), SE-8 (anti-slop) dispatch to **Gemini 2.5** via `src/evaluation/vision_judge.py` (the D24-introduced rubric-driven judge primitive). Text rubrics SE-2 (copy clarity), SE-3 (claim honesty), SE-4 (voice fit) dispatch to **claude/opus** (text outer judge). Structural rubrics SE-6 (a11y), SE-7 (perf) are **not LLM-scored** — operator hand-graded against U7b's screenshot + console output per Pass-5 audit (U7c cut); reviewer applies a brief checklist (semantic-HTML basics, WCAG AA contrast, payload reasonable for section type) at pre-publish review. | Same multimodal split as image_engine; visual axes can't be scored text-only; SE-6/7 hand-grading is cheaper than axe-core toolchain for v1. Reuses the D24 vision-judge primitive without growing vendor surface. Verified by `test_site_engine_substrate.py` per-axis dispatch test (U15b). |
| D27 | site_engine rubric prose lives at `docs/rubrics/site-quality.md` (frontmatter `version: v1`, content: SE-1..SE-8 with operational-definition + falsifiability + Score-3-failure-modes + anti-gaming clauses per S2 anchor-design pattern). `RubricTemplate.prose_ref` in `rubrics.py` resolves to this file at evaluation time. | Substantial rubric prose (~350 lines) earns dedicated placement and independent versioning. Dual-consumer rationale (claimed for the parallel `compound-engineering:site-improvement` skill) dropped per Pass-5 audit — that skill is unconfirmed; reinstate the rationale if the skill ships. Adds zero substrate complexity: `prose_ref` is the same resolution mechanism `compliance_rules` uses per TD-11. |

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
- **Should site_engine be a separate plan or bundled with this one?** Bundled — site_engine consumes every foundational shared infra piece (TD-27). Splitting would parallel-define the same dependencies.
- **What's site_engine v1 scope?** Section-level only (`hero / value_prop / social_proof / faq / cta / pricing`); full-page rewrites not built (TD-28).
- **Where do site_engine briefs come from?** `marketing_audit` (primary, audit findings → section-level briefs) + `geo` (AI-search readiness signals); no `competitive` direct input in v1 (TD-29).
- **Where do SE-1..SE-8 rubric anchors live?** `docs/rubrics/site-quality.md` — top-level dedicated rubric file (TD-30 location rationale: ~350 lines of substantial prose earns top-level placement + independent `version:` field); seeded from 2026-05-13 landing-page calibration session.
- **How does site_engine handle visual vs text vs structural scoring?** Visual axes (SE-1/5/8) → Gemini 2.5 vision sub-judge; text axes (SE-2/3/4) → claude/opus; structural axes (SE-6/7) → operator hand-graded at pre-publish review against U7b screenshot + console output (D26; U7c cut for v1).

### Deferred to Implementation

- **Specific rubric prose content for AE-1..AE-8, IE-1..IE-8, AD-1..AD-8.** Authored alongside each lane unit; ~30–40 lines per rubric × 24 rubrics ≈ 720–960 lines total. Approach: mirror x_engine rubric anchor file shape (`docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`).
- **SE-1..SE-8 (site_engine) rubric prose is ALREADY authored** at `docs/rubrics/site-quality.md` (346 lines, v1, seeded from the 2026-05-13 landing-page calibration session). U15b's only authoring task is registering `RubricTemplate.prose_ref` entries pointing at the file. The prose itself does not need to be re-derived during implementation; it can be tuned per client as fixtures expose calibration drift.
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
site_engine       ← NEW (per TD-27 bundling; section-level v1 per TD-28)
```

### Dependency graph

```
U0 (Stream A flag graduation — gates everything)
  │
  ▼
Foundations (dependency-ordered; no phase gate)
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
    │     ├─→ U7 (Pre-publish review service — single module + webhook, secondary reviewer escalation)
    │     │
    │     ├─→ U7b (Playwright site-render utility — shared)              ← per TD-27, needs U2 for brand_tokens
    │     │     │
    │     │     [U7c a11y + perf audit utility cut per Pass-5 audit]    ← SE-6/7 hand-graded for v1
    │     │            │
    │     │            └─→ U15b (site_engine lane)
    │
    └─→ U8 (Storyboard extension)   ← can run in parallel with U2–U7 once U1 lands
    └─→ U13 (article_engine lane)    ← needs U2, U3, U4, U5
    └─→ U14 (image_engine lane)      ← needs U2, U3, U5, U6
    └─→ U15 (ad_engine lane)          ← needs U2, U3, U5
    └─→ U15b (site_engine lane)       ← needs U2, U3, U4, U5, U7, U7b, U10b
    │
    └─→ External-gate check (TD-12 per-client): if partner consent + legal-review owner
        for at least one client are not resolved → that client's U18 instantiation waits;
        proceed with whichever client is unblocked (external constraint, not plan-side phase)
    │
    └─→ U18 (Klinika + DWF instantiation)  ← needs U8, U13, U14, U15, U15b, U16, U17 + parallel-track
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
[site_engine ONLY: U7b render → sanitizer Pass 1 + lane-source console check Pass 2]   ← structural-fail conditions; SE-6/7 hand-graded post-promote
        │                                                (render fails / console
        │                                                errors / a11y critical /
   ┌────┴────┐                                          perf >2× budget) → variant
   ▼         ▼                                           scored 0, not promoted
[pre-gate fail]   [pre-gate pass — flow continues for all lanes ▼]
[score 0 →
 frontier
 rejection]            │
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
reviewer_assist_checklists:        # v1: single rule set per client (D6 revised per TD-18)
  - medical_pl
enabled_channels:
  - storyboard
  - article_engine
  - image_engine
  - ad_engine
  - linkedin_engine
  - x_engine
  - site_engine                     # per TD-27: 4th content lane
enabled_platforms_per_channel:
  storyboard: [ig_reels, tiktok, ig_story]
  ad_engine: [meta]
content_denylist:
  - clinical_visuals
  - before_after_imagery
site_engine:                        # per TD-28: section-level v1 scope
  target_url: https://klinikamelitus.pl
  sections_in_scope: [hero, value_prop, social_proof, faq, cta, pricing]
  brand_tokens: clients/klinika-melitus/brand/tokens.json   # colors / typefaces / spacing / motion
  codex_fallback: true              # regulated-vertical day-1 fallback to claude/sonnet
  weekly_section_target: 2          # site_engine has lower throughput than article/x/linkedin
  # perf_budget_override: removed; SE-7 hand-graded for v1 per Pass-5 audit (U7c cut)
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
| S1 | **Per-step model split** — `LaneSpec.inner_backend` + `inner_model` overrides; resolution priority `LaneSpec > CLI flag > EVOLUTION_INNER_* > EVOLUTION_EVAL_*` | `cc212c2` 2026-05-13; `autoresearch/lane_registry.py:69-77` | U13/U14/U15/**U15b** each set `inner_backend` + `inner_model` per the frontier-only-diverse-from-inner-loop policy (memory: `judge-decisions-2026-05-11.md`). U15b adds the vision-sub-judge dispatch case per D26 — visual SE axes route to Gemini 2.5; text SE axes route to claude/opus; structural SE axes bypass LLM entirely. |
| S2 | **Post-rewrite anchor design pattern** — operational definitions + substitution tests + falsifiability requirements + named Score-3 failure modes + anti-gaming clauses | `896f366` 2026-05-13 (13 anchor rewrites: MON-1/3/4/5/6, CI-1/5/6/7, SB-1/2/3/5) | U13/U14/U15 author 24 new rubrics (AE-1..8, IE-1..8, AD-1..8) using this pattern. **U15b's SE-1..SE-8 are already authored using this pattern in `docs/rubrics/site-quality.md`** (operational def + falsifiability + Score-3 failure modes + anti-gaming clauses per axis). U5 compliance YAML prose authors follow same pattern. |
| S3 | **RUBRICS=53 baseline** (was 52 when this plan was first drafted) | `896f366` + `204e9a6` | U1 derived-count reference; D4 rationale updated. |
| S4 | **Stream A axis-collapse fix default-on** — escape hatch still exists but escape path is dead in production | `cli/freddy/commands/evaluate.py:215-248` (graduated post-`3b97b3d`) | U0 scope narrowed: removes escape hatch + dead conditionals; no production behavior change. |
| S5 | **`custom_persist_judge_payload` hook** — per-lane sidecar persistence (precedent: monitoring DQS) | `autoresearch/lane_registry.py:84-100, 224` | New lanes optionally wire this hook if they need lane-specific judge-side sidecars (none currently planned but available). |

**Open in judge plan — informational, NOT a gate (decided 2026-05-13):**

| ID | Open primitive | Judge-plan unit | CE plan dependency |
|---|---|---|---|
| **G1** | `dimension_scores` (per-criterion) + `rubric_version` persistence to `autoresearch/archive/*/scores.json`. Currently `dimension_scores: []` (empty) on main; `rubric_hash` is persisted but not the version string. | Judge plan U0.2 (OPEN) | **NOT a gate.** New lanes v1 use aggregate scoring (existing substrate handles it) — per-criterion archive writes are not in U13/U14/U15/U15b scope. If judge plan U0.2 lands during CE plan build, new lanes automatically inherit the schema (same archive writer). If it doesn't, new lanes still ship. Re-evaluate only if a future judge-discrimination analysis requires retroactively populating dimension_scores for the new lanes — then it's a backfill task, not a v1 gate. **Author-side commitment to prevent permanent data loss:** **U13/U14/U15/U15b** judge prompts request per-criterion `dimension_scores` in the response payload from day 1, even though `evaluate_variant.py` archive write currently drops them (writes empty list per `evaluate_variant.py:1606,1722,1747`). Cost is ~0 LOC in the prompts; benefit is that when U0.2 lands, the payload-side data is already correct and only the archive writer needs to change to start persisting. Otherwise the early-archive cliff (judges aren't re-run cheaply) would silently un-backfill these lanes. **site_engine extra commitment:** U15b additionally persists `rubric_version` from `docs/rubrics/site-quality.md` frontmatter into each score payload so SE-* scores remain attributable across rubric revisions. |

**Open in judge plan — informational, no gate:**

- Judge plan U0.3 documents 3-level grain (Score 1/3/5) — already implicit in rubric prose; CE plan's new rubrics author against this grain by default.
- Judge plan Phase 2 (validation: archive replay, negative-control fixtures, cross-family κ, Policy Invariance telemetry) — independent of CE plan; can run in parallel.

**Explicitly rejected by judge plan — DO NOT propose for new lanes:**

- **No LANE-9 kernel rubric pattern for new lanes.** Judge plan added X-9; MON-9/GEO-9/CI-9/MA-9 were rejected on 2026-05-13 because the 13 anchor rewrites covered the same failure modes more cheaply. CE plan **does not propose AE-9/IE-9/AD-9**; the 8-rubric-per-lane convention holds.
- **No inline Python module-level trigger lists for compliance** (`MEDICAL_PL_TRIGGERS` / `LEGAL_PL_TRIGGERS` mentioned in judge plan as the inline option). CE plan U5's shared YAML registry (`reviewer_assist/checklists/<name>.yaml`) is the uncontested authority since MON-9 (the only judge-plan unit that would have used inline triggers) was rejected.

**Resolution at integration time:** if the judge plan amends Phase 2 such that its validation work requires the new-lane archives to write per-criterion `dimension_scores`, that's a hard add to CE plan U13/U14/U15. Re-confirm before U13 starts.

---

## New-lane Substrate Wiring Checklist

Every new lane (U13 article_engine, U14 image_engine, U15 ad_engine, U15b site_engine) must touch the following substrate points in addition to its own per-lane files. Implementer walks this list per lane; omissions surface as runtime errors at first execution.

| # | File / location | Edit | Failure if omitted |
|---|---|---|---|
| 1 | `autoresearch/lane_registry.py` | Add `LaneSpec` entry to `LANES` dict with `rubric_ids` (per-lane + `<rule_set>_<lane>_*` compliance IDs per D12-hybrid; see Item 5), `readonly_subprefixes`, `structural_doc_facts`, `structural_gate_functions`, `render_rubric_ids` (set to the existing 5-tuple `RND-*` IDs to enable self-improving report rendering; empty tuple disables — pick explicitly), `findings_promotion = FindingsPromotionConfig(title="Global Findings: <Lane>", confirmed_threshold=2, repeated_threshold=2)`, `count_findings → 0` per D2 for content lanes, `custom_*` hooks as needed, `inner_backend`/`inner_model` static pin per D24/U13/U14/U15/U15b wiring rows. | New lane never executes. |
| 2 | `autoresearch/archive/v007-curated/workflows/__init__.py` | `from .<lane> import SPEC as <LANE>_SPEC` + `WORKFLOW_SPECS["<lane>"] = <LANE>_SPEC`. | Central registry can't dispatch. |
| 3 | `autoresearch/archive/v007-curated/workflows/session_eval_registry.py` (SESSION_EVAL_SPECS dict) | `from .session_eval_<lane> import SPEC as <LANE>_SESSION_EVAL_SPEC` + `SESSION_EVAL_SPECS["<lane>"] = <LANE>_SESSION_EVAL_SPEC`. | `get_session_eval_spec("<lane>")` raises `KeyError` on first eval. |
| 4 | `src/evaluation/models.py:160` `EvaluateRequest.domain: Literal[...]` | Add new lane string to the Literal alternatives. | `_assert_models_literal_matches()` (lane_registry.py:584-596) raises — **invoked at evolve startup** (`autoresearch/evolve.py:2922-2923`) and from `tests/autoresearch/test_lane_registry.py:159` + `tests/audit/test_marketing_audit_l1.py:217`. NOT module-load (the function explicitly avoids module-load to prevent circular import — see docstring `lane_registry.py:586`). Backend boots OK; evolve runs fail. |
| 5 | `src/evaluation/rubrics.py` | Register per-lane rubric prose for `<LANE_PREFIX>-1..8` (AE/IE/AD inline; SE via `RubricTemplate.prose_ref → docs/rubrics/site-quality.md` per TD-30). **`RubricTemplate.prose_ref` field does NOT yet exist on the dataclass** (current fields: `criterion_id`, `domain`, `scoring_type`, `prompt`, `is_cross_item`, `tier` — verified 2026-05-15 substrate audit on `src/evaluation/rubrics.py:16-27`). U5 owns the substrate addition (`prose_ref: str | None = None` + resolver helper that reads `reviewer_assist/checklists/<name>.yaml` AND file-anchor refs like `docs/rubrics/site-quality.md#se-N`); U13/U14/U15 add inline AE/IE/AD prose without using `prose_ref`; U15b consumes the U5-added field. **Compliance rubric IDs per D12-hybrid:** the lane's `LaneSpec.rubric_ids` carries the per-lane compliance ID (e.g., `medical_pl_article_engine_compliance` — one entry per active rule set per lane, NOT one per individual rule). That ID exists in `RUBRICS` as a `RubricTemplate` whose prose is a resolve-at-eval-time reference to `reviewer_assist/checklists/<rule_set>.yaml` via `prose_ref`. The derived `len(RUBRICS) == sum(len(spec.rubric_ids) for spec in LANES.values())` assertion (D4) covers both per-lane + compliance IDs automatically — no separate count. **`render_rubric_ids` (RND-1..5) are NOT in `RUBRICS`** — they're parallel rubrics owned by `render_judge.py` scripts per-archive (inline `CRITERIA = ["RND-1", ..., "RND-5"]`) and so are NOT counted against the derived sum. Final v1 count = 53 baseline + 32 new-lane (4 × 8) + 7 compliance IDs (one per compliance-gated lane × single-rule-set-per-client D6/TD-18) = **92 total**. | RUBRICS assertion fails on lane load; or — if `prose_ref` not added in U5 — U15b's SE-* anchor resolution raises `AttributeError` at first eval. |
| 6 | **Cross-archive workflow propagation** | After adding `workflows/<lane>.py` + `workflows/session_eval_<lane>.py` to `autoresearch/archive/v007-curated/workflows/`, propagate them into every per-lane archive's `current_runtime/workflows/` AND `v007-curated/workflows/` directories. **Verified target count (2026-05-15 substrate audit):** 14 propagation targets — 7 per-lane archives (`archive_geo`, `archive_competitive`, `archive_monitoring`, `archive_storyboard`, `archive_marketing_audit`, `archive_x_engine`, `archive_linkedin_engine`) × 2 dirs each (`current_runtime` + `v007-curated`), plus the central `autoresearch/archive/current_runtime/workflows/` (the `autoresearch/archive/v007-curated/workflows/` is the source). Historical version snapshots (`v<NNN>/`) do NOT need new-lane files — they're frozen baselines. **`evolve_ops.ensure_lane_heads` does NOT copy workflow files** — it's a thin wrapper around `lane_runtime.initialize_current_heads(archive_dir)` which only writes a per-lane head manifest (`current.json`). Add propagation helper `scripts/propagate_workflow_to_archives.py` (~40 LOC) in U13 (the first new lane); subsequent lanes invoke it via Make target or pre-commit. | First cross-lane evolution run `ImportError` on the missing module. |
| 7 | `autoresearch/eval_suites/search-v1.json` | Add `domains.<lane>` block with fixture IDs + `rotation.per_domain.<lane>` (anchor/random counts). Content lanes (article/x/linkedin) typically use `0 anchors / 3 random` since artifact IDs are dynamic. | Lane has no holdout coverage in daily evolution. |
| 8 | `tests/autoresearch/test_lane_registry.py` | Add lane to expected count + rubric-ID coverage assertions; verify `_assert_models_literal_matches()` passes. | CI fails on registry-invariant test. |
| 9 | `tests/autoresearch/test_structural_doc_facts.py` | Auto-runs parametrized over `workflow_lane_names()`; no explicit code change required AS LONG AS the new lane provides `structural_doc_facts` + `structural_gate_functions` 1:1 mapping in its LaneSpec AND routes structural gates through `session_eval_<lane>.structural_gate()` rather than `src/evaluation/structural._validate_<lane>` (the new-lane convention — see x_engine precedent). | Bidirectional drift test fails on lane load. |
| 10 | `tests/autoresearch/test_<lane>_substrate.py` (NEW) | Substrate-level smoke tests using the synthetic-package loader (mirror `test_x_engine_substrate.py`, ~125 LOC). | No regression coverage for the lane's structural gates. |
| 11 | **Codex terminal-failure telemetry** | Wire each new lane's variant execution to emit a generations.jsonl row when `agent_retry.is_terminal_codex_failure(returncode, stdout, stderr)` (`autoresearch/agent_retry.py:156`) returns True. Use the existing `compute_metrics.append_generation_row(row: dict)` helper (`autoresearch/compute_metrics.py:138-141`); row schema: `{"lane": <lane>, "gen_id": <variant_id>, "terminal_failure": True, "marker_patterns": [...matched _CODEX_TERMINAL_MARKERS...], "ts": <unix>}`. This replaces the earlier metaphorical "session_marker_count" prose — the actual detection mechanism is stdout/stderr pattern-matching against `_CODEX_TERMINAL_MARKERS` (`agent_retry.py:144-153`: `"cybersecurity risk"`, `"content was flagged"`, `"flagged for possible"`), not a session-marker file. | Operator has no signal that codex's cyber filter is rejecting content on the new lanes; mute regression goes undetected until a U18 smoke run. |

**Convention enforcement** (per registry comments + memory): mirror `competitive.py` not `geo.py` for `WorkflowSpec` shape; new structural gates route through `session_eval_<lane>.*` not `src/evaluation/structural._validate_<lane>`; `_safe_format` for `{}` escaping in JSON-example-bearing prompts; cold-start skeleton templates in `templates/<lane>/`; fresh `session_id` per retry; `count_findings → 0` for content lanes.

This checklist replaces ~150 lines of per-lane repetition that would otherwise occur in U13/U14/U15/U15b Files lists. Each new-lane unit's Files list states "Plus: items 1–10 in §New-lane Substrate Wiring Checklist applied per this lane" + only enumerates the lane-specific files.

---

## Implementation Units

**Execution posture (revised 2026-05-18 per JR direction):** plan ships as ONE coherent build, not phased. Units below are listed in dependency order (foundations first, lanes second, instantiation last) — but there are no phase boundaries, no intermediate ship gates, no "Phase A done → review → Phase B start" ceremony. The AI agent works through the dependency graph and the whole content engine ships as a single coherent system. Cross-cutting requirements (moment emission via U6b contract) apply to ALL applicable units uniformly. External constraints that can't be edited away by plan restructuring: parallel-track risks #1 (Klinika corpus consent), #2 (outside-counsel review for medical_pl/legal_pl), #12 (engagement-letter language) gate U16/U17/U18 regardless of plan structure — these are real-world dependencies, not plan-side phases.

**Reconnaissance correction (Pass-6, 2026-05-13):** Pre-implementation grep verified that **only `AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE` is default-on in code** (`cli/freddy/commands/evaluate.py:247` → `default="on"`). `AUTORESEARCH_EVAL_FIX_HOLDOUT` (`autoresearch/evaluate_variant.py:3703`) and `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES` (`autoresearch/lane_registry.py:519`) are both still **default-OFF** in code — operators export them ON during evolution runs, but flipping their defaults is a real behavior change, not cleanup. The original "U0: all three flags" was split into U0 (AXIS_COLLAPSE cleanup) + U0a (HOLDOUT + FRAGILE_FIXTURES graduation, two-step).

- [ ] **U0: Remove AXIS_COLLAPSE escape hatch (cleanup-only; no behavior change)**

**Goal:** The Stream A axis-collapse fix is already default-on in `cli/freddy/commands/evaluate.py:247`. U0 removes the now-unreachable escape-hatch helper + legacy broadcast branch + the `=off` test case. Pure dead-code cleanup; no production behavior change.

**Requirements:** Per triage TD-10. Gates the entire build.

**Dependencies:** None on main; fix already shipped (`3b97b3d`, PR #60) and default-on.

**Files:**
- Modify: `cli/freddy/commands/evaluate.py` — remove `_axis_collapse_fix_enabled()` helper + escape-hatch conditional (lines ~215–248); inline the per-criterion-results call.
- Modify: `tests/test_cli_evaluate.py` — delete the `test_..._when_fix_disabled` test case (no longer reachable); drop env-var setup from the remaining 3 axis-collapse tests.
- Modify: `tests/test_axis_distinctness.py` — update docstring to remove flag reference; behavior unchanged.

**Approach:**
- Inline the call (`_per_criterion_results(verdict, criterion_ids)` directly, no conditional).
- Delete the helper function + its docstring + the `else` legacy branch.
- Single PR; ship as a refactor before any Content Engine work begins.

**Patterns to follow:** Stream A's fix implementation (the flagged path becomes the unconditional path).

**Test scenarios:**
- *Happy path:* All existing axis-collapse tests pass without env-var setup.
- *Verification:* `grep -r "AUTORESEARCH_EVAL_FIX_AXIS_COLLAPSE\|_axis_collapse_fix_enabled" cli/ src/ autoresearch/ tests/` returns no hits.

**Verification:**
- `pytest tests/test_cli_evaluate.py tests/test_axis_distinctness.py -v` passes (validated 2026-05-13: 12 passed, 1 skipped).
- Full test suite green.

---

- [ ] **U0a: HOLDOUT + FRAGILE_FIXTURES escape-hatch graduation (split per Pass-6 reconnaissance)**

**Goal:** Graduate `AUTORESEARCH_EVAL_FIX_HOLDOUT` and `AUTORESEARCH_EVAL_FIX_FRAGILE_FIXTURES` from default-OFF to default-ON, then remove their escape hatches. Two-step: (1) flip default in code → operate under default-on for a validation period, (2) remove escape hatch + legacy code path once safety confirmed.

**Requirements:** Per triage TD-10. Gates the entire build alongside U0.

**Dependencies:** Validation evidence that operators have been exporting both flags ON consistently for ≥7 days during evolution runs without incident — read `autoresearch/metrics/` or recent run manifests for confirmation.

**Files:**
- Modify: `autoresearch/evaluate_variant.py:3667-3703` — HOLDOUT env reader + its use sites.
- Modify: `autoresearch/lane_registry.py:496-519` — FRAGILE_FIXTURES env reader.
- Modify: `autoresearch/evaluate_variant.py:1836` — FRAGILE_FIXTURES use site.
- Modify: `tests/autoresearch/test_holdout_lineage_invariant.py` (3 parametrized cases including off) — delete the off cases.
- Modify: `tests/autoresearch/test_fragile_fixtures.py` (5 tests, one asserts off-behavior) — delete the off case.

**Approach:**
- **Step 1 (PR A):** flip both defaults to `"on"` (analogous to AXIS_COLLAPSE pattern); keep escape hatches; operators continue exporting; observe ≥7 days.
- **Step 2 (PR B):** if no incidents, remove escape hatches + off-case tests + helper functions (mirror U0).

**Why split from U0:** flipping defaults is a real behavior change, not cleanup. Operators currently export both flags ON, but the code-side default-off means any non-evolution caller (test, ad-hoc CLI run, future code path) silently gets the legacy buggy behavior. The flip needs validation before the cleanup.

**Test scenarios:**
- *Step 1 happy path:* After flip, all existing tests pass with no env-var setup (operators already export ON, matching new default).
- *Step 1 regression:* Operator script that explicitly sets `AUTORESEARCH_EVAL_FIX_HOLDOUT=off` still works (escape hatch intact).
- *Step 2 happy path:* After 7+ days at default-on with no incidents, escape hatch removal is dead-code cleanup like U0 was for AXIS_COLLAPSE.

**Verification:** Same `grep` pattern as U0, scoped to HOLDOUT + FRAGILE_FIXTURES.

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
- `ClientConfig` Pydantic model (frozen, `extra=allow` initially per marketing-audit lesson; tighten later). Fields per R26 high-level design above + the per-client adjustments added under §Generalization Justification.
- **Relationship to existing `src/clients/models.py:Client`:** `Client` (existing) carries low-level workspace metadata (`slug`, `domain`, `status`, `created_at`); the new `ClientConfig` extends with content-engine-specific fields (voice_persona_ref, reviewer_assist_checklists, enabled_channels, content_denylist, pre_publish_reviewer, brand_assets, archetype, brief_consumption, **locale, brand_strictness, source_material_paths**). Decision: **coexist with cross-reference.** `ClientConfig` references the existing `Client` by slug; existing `clients/<slug>/config.json` stays as-is for the audit pipeline workflows; new `clients/<slug>/client.yaml` carries Content Engine config. v1.5 can consolidate if the dual-file pattern becomes painful.
- **Archetype enum + stub_allowed flag (revised 2026-05-18 — cut from 11 to 4 values; new archetypes are 1-line Literal edits when their first client onboards):** `ClientConfig.archetype: Literal["b2b_saas", "b2c_aesthetics", "b2b_regulated", "b2b_tech"]`. **v1 archetype roster:** `b2b_saas` (gofreddy.ai canonical — site_engine SE-1..8 calibration target), `b2c_aesthetics` (Klinika, first onboarded), `b2b_regulated` (DWF, first onboarded), `b2b_tech` (U19 architectural-validation stub). **Why only 4:** the original 11-archetype enum included `b2b_ai_first`/`b2c_ecommerce`/`creator_solo`/`creator_managed`/`b2b_agency`/`b2b_consultancy`/`indie_hacker` — none of which have a v1 client. Per the adversarial review (and JR's "no deferrals" framing), speculative enum values accumulate false test-coverage signal without earning their place; deferred to first-client-onboarding for each (the substrate supports any string at runtime; Literal addition is a 1-line edit). The architecture is still generic (config-driven onboarding works for any archetype string given a client.yaml + voice corpus + brand assets) — only the Literal type narrows to what's actually exercised in v1. Optional `archetype_stub_allowed: bool = False` excludes the archetype from D11's CI assertion (≥1 real_client fixture per archetype). v1 sets `stub_allowed=True` only for `b2b_tech` in `_stub_b2b_tech/client.yaml` (U19). Per-archetype defaults documented in §Operational Notes archetype-defaults reference table (also revised to 4 rows).
- **NEW `ClientConfig.locale` field (per TD-33):** `locale: LocaleConfig` (nested model) — `{gl: str, hl: str, google_domain: str, country: str, city: str, requires_diacritic_normalization: bool}`. Default = `{gl: "en", hl: "en", google_domain: "google.com", country: "US", city: "San Francisco,CA,US", requires_diacritic_normalization: false}` (SaaS/AI default). Klinika + DWF override to Polish equivalents: `{gl: "pl", hl: "pl", google_domain: "google.pl", country: "PL", city: "Warsaw,Mazowieckie,Poland", requires_diacritic_normalization: true}`. Consumed by U15 `signal_aggregator` for SerpAPI + GSC calls.
- **NEW `ClientConfig.brand_strictness` field (per TD-37):** `brand_strictness: Literal["strict", "permissive"] = "strict"`. Defaults `strict` (SVG logo + WOFF2 fonts required; preflight fails on miss). `permissive` for verticals without mature brand assets (warns instead of fails; allows PNG logo + system-font fallback). Klinika+DWF may set `permissive` at onboarding if brand assets are immature.
- **NEW `ClientConfig.voice_corpus_consent_required` field (per TD-33):** `voice_corpus_consent_required: bool` — defaults derived from archetype: `b2b_saas` defaults `false` (public content corpus, no consent friction); `b2c_aesthetics` defaults `true` (Klinika's medycyna-urody corpus is private/proprietary); `b2b_regulated` defaults `true` (partner content); `b2b_tech` stub `false`. v1.5+ archetypes inherit defaults from the closest analog when added. Parallel-track risk #1 reframed: consent is a per-client property, not a default risk.
- **NEW `ClientConfig.source_material_paths` field (per TD-36):** `source_material_paths: list[Path] | None` — optional csv of file paths relative to `clients/<slug>/source_material/` directory. Consumed by article_engine (U13) for blog + LinkedIn Article generation. Operator-curated handoff folder; format: markdown preferred, PDF via existing `src/audit/pdf_to_markdown.py`, URL list via existing `src/competitive/providers/` patterns.
- Loader reads `clients/<slug>/client.yaml`, validates against schema, returns frozen `ClientConfig`.
- At lane-start, snapshot the config into the run manifest (`autoresearch/archive_<lane>/v<NNN>/client-config.snapshot.yaml`).
- At finalize, compare snapshot vs current config-on-disk; fail loud if changed (per D7 lineage-affecting fields; reviewer-routing carve-outs apply).

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
- Create: `src/voice/persona.py` — `VoicePersona` Pydantic model (frozen), loader `load_persona(persona_ref: str) -> VoicePersona`, **`compute_persona_checksum(persona: VoicePersona) -> str`** (SHA256 over canonical-serialized persona fields + corpus content). Exposed for run-manifest snapshotting.
- Create: `voice_personas/dr_maria.yaml` — Klinika instantiation
- Create: `voice_personas/partner_jamka.yaml` — DWF instantiation
- Create: `voice_personas/_stub_persona.yaml` — client #3 stub
- Test: `tests/voice/test_persona.py`
- (Sanity-sentence corpus + `test_persona_sanity.py` tripwire — **cut per Pass-6 YAGNI audit.** Persona checksum below covers file-level corruption deterministically; the curated known-good/known-bad sentence corpus required real operator labor before any signal. Re-add as v1.5 trigger when: real voice drift observed in production (artifact rejected by reviewer with "voice doesn't sound like Dr. Maria" reason) OR when ≥3 personas are active and a regression test bench becomes load-bearing.)

**Approach:**
- `VoicePersona` schema: `name: str`, `corpus_path: Path`, `voice_rules: list[str]`, `style_anchors: dict[str, str]` (mapping anchor name like `"argumentative-medical-pedagogic"` → prose description).
- **Corpus loader handles 4 formats (per TD-33 SaaS/AI-first generalization):** HTML (most common for SaaS — blog post archives via `BeautifulSoup`), markdown (preferred when client controls source format), JSON (Twitter/LinkedIn data exports — common for SaaS founder content), PDF (legacy / regulated verticals — via existing `src/audit/pdf_to_markdown.py`). Format dispatch by file extension. Mixed-format corpora supported (a single `corpus_path` directory can contain `.md` + `.html` + `.json` files; loader walks + dispatches).
- Loader reads `voice_personas/<persona_ref>.yaml`, resolves `corpus_path` to an absolute path (validates file exists), returns frozen model.
- (Per-persona sanity test cut per Pass-6 audit — see Files list note.)
- Style anchors are referenced by name in lane prompts (e.g., article_engine session.md says "use the `style_anchors.argumentative-medical-pedagogic` voice for blog content").

**Execution note:** Test-first.

**Patterns to follow:**
- `programs/references/voice.md` precedent (x_engine voice substrate, locked via `readonly_subprefixes`).

**Test scenarios:**
- *Happy path:* Load `dr_maria.yaml` → valid `VoicePersona`; `corpus_path` exists; style anchors keyed correctly.
- *Edge case:* Empty `voice_rules` list → loader returns valid persona (no rules enforced at load).
- *Edge case:* Empty `style_anchors` dict → persona is still loadable (lanes that need anchors fail at use, not at load).
- *Corruption path:* Manually edit one byte of `dr_maria` corpus file mid-run → finalize detects checksum mismatch; run fails loud (no silent corruption across 4 lanes).
- *Error path:* `corpus_path` points to nonexistent file → ValidationError at load.
- *Error path:* Unknown persona ref (file doesn't exist) → FileNotFoundError with helpful message.
- *Integration:* `ClientConfig.voice_persona_ref` resolves through loader to a valid `VoicePersona`.

**Verification:**
- `python -c "from src.voice.persona import load_persona; p = load_persona('dr_maria'); print(p.style_anchors)"` succeeds.
- `pytest tests/voice/test_persona.py -v` passes.
- (Sanity-sentence tripwire test cut per Pass-6; checksum mismatch at module load is the v1 corruption detector.)

---

- [ ] **U4: Findings-brief contract (R21)**

**Goal:** Land the findings-brief schema (R21 minimum field set), emitter helper, reader helper. Wires into geo + monitoring (U9, U10) and article_engine (U13).

**Requirements:** R21, R23, R24 (origin).

**Dependencies:** U2.

**Files:**
- Create: `src/briefs/schema.py` — `FindingsBrief` Pydantic model (frozen)
- Create: `src/briefs/emitter.py` — `emit_brief(lane_name: str, brief: FindingsBrief, archive_root: Path) -> Path`
- Create: `src/briefs/reader.py` — `read_briefs(source_lane: str, archive_root: Path) -> list[FindingsBrief]`. Single-source reader; when a consumer needs >1 source lane (U15b site_engine wants marketing_audit + geo briefs), it calls `read_briefs()` twice and unions the result — ~5 lines in U15b, no shared-infra API surface.
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
- Create: `src/compliance/judge.py:COMPLIANCE_JUDGE constant` (~15 LOC, per D25) — `COMPLIANCE_JUDGE constant` singleton holding the single backend (`claude/opus`) + model. Read via `get_compliance_judge_config()`; supports env override `COMPLIANCE_JUDGE_BACKEND` / `COMPLIANCE_JUDGE_MODEL`. Imported by `src/compliance/judge.py`; the 7 lanes with reviewer-assist gates consume it transitively.
- Create: `reviewer_assist/checklists/_placeholder_medical_pl.yaml` — placeholder rule set (real authoring in U16, gated on legal review)
- Create: `reviewer_assist/checklists/_placeholder_legal_pl.yaml` — placeholder rule set (real authoring in U17)
- **Create: `reviewer_assist/checklists/gdpr_eu.yaml` (per TD-46 revised 2026-05-18)** — baseline reviewer-assist checklist for EU-targeting clients; load-bearing for Klinika + DWF (both EU). ~80-150 rules from public GDPR articles: data-handling claims, cookie disclosures, retention representations, right-to-erasure, lawful basis representations, data subject rights, cross-border transfers (post-Schrems II). Authored in U16b; no legal-review blocker since public text + posture is reviewer-assist not legal-grade compliance gate (see §Compliance Posture).
- **Modify: `src/evaluation/rubrics.py:16-27` — add `prose_ref: str | None = None` to `RubricTemplate` dataclass (new field).** This is the substrate addition that the TD-11 hybrid-rubric pattern and TD-30 SE-* anchor resolution depend on. Verified 2026-05-15 substrate audit: the field does not currently exist. Adding it is non-breaking (defaults to `None`; existing inline-prose rubrics continue to use the `prompt` field directly).
- Add free function `resolve_prose(template: RubricTemplate, registry_root: Path) -> str` in `src/evaluation/rubrics.py` (~15 LOC). Dispatches on `prose_ref` shape: `reviewer_assist/checklists/<name>.yaml#<rule_id>` → loads YAML rule prose; `docs/rubrics/<file>.md#<anchor>` → loads markdown section by `## <anchor>` heading; falls back to `template.prompt` when `prose_ref is None`. Consumed by `evaluate_variant.py` and `src/compliance/judge.py:evaluate_compliance`.
- Modify: `src/evaluation/rubrics.py` — register per-lane compliance rubric duplicates as `RubricTemplate(criterion_id=..., domain=..., scoring_type="gradient", prompt="", prose_ref="reviewer_assist/checklists/<rule_set>.yaml#<lane>_compliance", ...)`.
- Modify: `autoresearch/lane_registry.py` — extend LaneSpec.rubric_ids of touched lanes (later units do the actual wiring)
- Test: `tests/compliance/test_rule_set_loader.py`
- Test: `tests/compliance/test_compliance_judge.py`
- Test: `tests/compliance/test_judge_config.py` — verifies singleton + env override resolution
- Test: in existing `tests/evaluation/test_rubrics.py`, add test cases for `resolve_prose()` — verifies prose_ref resolution for both YAML checklist refs and markdown anchor refs; verifies fallback to inline `prompt` when `prose_ref is None`.

**Approach:**
- `ComplianceRule`: `id: str`, `pattern: str | list[str]` (regex or pattern list), `severity: Literal["hard_block", "soft_warn"]`, `prose: str` (rubric-style description for judge).
- `ComplianceRuleSet`: `name: str`, `rules: list[ComplianceRule]`, `metadata: dict`.
- `evaluate_compliance(artifact, rule_set_name, lane) -> ComplianceResult` runs **the single active rule set** for the client against the artifact (v1: single rule_set per client per TD-18); returns `ComplianceResult` with overall verdict (`hard_block | soft_warn | clean`) and flag list. `ComplianceRuleSet` schema accepts a list field but v1 constrains length to 1; multi-rule-set merge logic deferred.
- **Hybrid rubric structure (D12 revised per TD-11):** Lane-side `LaneSpec.rubric_ids` carries per-lane compliance rubric IDs like `medical_pl_article_engine_compliance` (one per active rule set per lane, NOT one per individual rule). The per-rule prose lives in the shared `reviewer_assist/checklists/<name>.yaml` registry. Each lane's rubric prose template resolves to the shared registry entry at evaluation time — so editing one YAML rule updates all 7 lanes' interpretations without touching `LaneSpec.rubric_ids` or `rubrics.py` invariants.
- Rule-set authoring (U16, U17) writes real Polish-language patterns; v1 ships with placeholders so the framework can be tested.

**Execution note:** Test-first.

**Patterns to follow:**
- Slop-gate precedent (x_engine factual-veto split): deterministic regex check separate from LLM. Use this for rules with `pattern` defined.
- `RubricTemplate` shape (`src/evaluation/rubrics.py:16`) for the LLM-judged portion.
- **Post-rewrite anchor design (S2)** — `reviewer_assist/checklists/<name>.yaml` rule prose must follow `896f366`'s pattern: operational definitions ("a 'cure' claim is …") + substitution tests ("would replacing X with Y change the meaning?") + falsifiability requirements + named Score-3 failure modes + anti-gaming clauses. This makes the compliance judge robust against the same ceiling-bound failure that the 13 anchor rewrites resolved on MON/CI/SB rubrics.

**Test scenarios:**
- *Happy path:* Load `_placeholder_medical_pl.yaml` → valid `ComplianceRuleSet` with rules list.
- *Happy path:* Evaluate clean artifact → verdict `clean`, empty flag list.
- *Happy path:* Evaluate artifact with one hard-block hit → verdict `hard_block`, flag with provenance.
- *Edge case:* `reviewer_assist_checklists` list with >1 entry in v1 → ValidationError ("v1 supports single rule_set per client; multi-rule-set merge deferred per TD-18").
- *Edge case:* Empty `reviewer_assist_checklists` list → verdict `clean` (no rules to apply).
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
- Create: `src/generation/image_composer.py` — single module with 4 composition functions + lightweight dicts for slide content. No separate `image_layout.py`; no `BrandStamp`/`CarouselSlide`/`DocSlide` dataclasses (Pass-5 simplification).
- Create: `tests/generation/test_image_composer.py`

**Approach:**
- `compose_single(prompt_image_path: Path, text_overlay: str | None, brand: dict) -> Path` — generates a single composed image.
- `compose_carousel(slides: list[dict], brand: dict) -> list[Path]` — generates a multi-slide carousel; each slide receives the previous slide's brand-anchor metadata to ensure consistency (sequential per D13).
- `compose_doc_carousel(slides: list[dict], brand: dict) -> list[Path]` — LinkedIn document-carousel variant (1:1 ratio, info-density-friendly text layout).
- `compose_hero(prompt_image_path: Path, brand: dict, dimensions: tuple[int, int]) -> Path` — hero/banner variant.
- Per-format dimensions: `ig_single` 1:1 1080×1080, `ig_carousel` 1:1 1080×1080, `ig_story` 9:16 1080×1920, `li_doc_carousel` 1:1 1080×1080, `hero_banner` configurable, `ad_static` per-platform spec.
- Brand stamp: logo + brand color stripe + typography defaults from `brand` dict (loaded from `clients/<slug>/brand/`).
- Slide dicts have `text_overlay`, `prompt_image_path`, `brand_anchor` keys; no separate dataclass per slide type (Pillow accepts dict-shaped configs natively). If shape complexity grows post-launch, promote to dataclasses in v1.5.

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

- [ ] **U6b: Canonical event-schema extension for portal moments (no helper wrapper)**

**Goal:** Extend `KNOWN_KINDS` + `CANONICAL_FIELDS` in `autoresearch/events.py` so every new lane + U7 can emit moment events via direct `log_event(...)` calls at meaningful checkpoints. The client portal's moments timeline surfaces what each lane is doing for a client. Coordination point with the portal-moments redesign at `docs/brainstorms/2026-05-15-portal-moments-redesign-requirements.md` (R-Lane-2, R-Schema-1..3).

**Requirements:** portal-redesign R-Lane-2 (minimum emission kinds), R-Schema-1..3 (`KNOWN_KINDS` + `CANONICAL_FIELDS` extensions). Lane authors call `log_event(...)` directly with `kind='moment'` and relevant `metadata` fields — no wrapper helper.

**Dependencies:** none new (uses existing `autoresearch.events.log_event` + `client_events_path` from PR #61 P1).

**Files:**
- Schema extensions (`KNOWN_KINDS` + `CANONICAL_FIELDS`) ship via the portal-moments redesign at `docs/plans/2026-05-18-001-feat-portal-moments-redesign-plan.md` (Unit 1). plan-002 U6b is contract-only: it defines the moment-emission mandate that lanes must follow.
- Modify: `tests/autoresearch/test_events.py` — drift tests cover new kinds + canonical fields (the assertion update lands with Unit 1 of the portal-moments plan; this line stays here so plan-002 readers see the test surface).

**Minimum moment kinds every new lane MUST emit (R-Lane-2) — via direct `log_event(kind='moment', client_id=<slug>, metadata={'moment_kind': '<kind>', 'title': '<title>', ...})` calls:**
- `session_start` — emitted by the lane's `run()` entry when it begins for a client
- `deliverable_ready` — emitted when an artifact (draft, audit, brief, post, section) is ready for review or publication
- `session_completed` — emitted when the lane finishes its work for the fixture (success or terminal failure)

**Additional moment kinds emitted by specific units:**
- **U7** emits `review_required` (when handing off to a reviewer) via `log_event(kind="review_required", ...)` (top-level kind, not a moment subtype). U7's `review_approve`/`review_reject`/`sla_breach` continue via `log_event(kind=...)` per the Edit-1 changes below.
- **Optional, lane-author discretion:** `decision_logged` (rationale for non-obvious agent decisions), `error_recovered` (after a lane recovers from a known failure mode).

**Title convention (enforced via reviewer + drift test, not wrapper):** moment titles ≤120 chars in operator-readable English. Drift test asserts no logged moment exceeds 120 chars.

**Test scenarios:**
- *Drift test:* `KNOWN_KINDS` removal of `moment` or `review_required` is caught by the existing pinning test in `tests/autoresearch/test_events.py`.
- *Drift test:* `CANONICAL_FIELDS` removal of `moment_kind` / `source_event_ids` / `title` / `body` is caught likewise.
- *Cross-lane integration test:* runs each new lane against a fixture and asserts at least one `session_start` + one `deliverable_ready` + one `session_completed` moment lands in `clients/<slug>/audit/events.jsonl`.

**Verification:**
- `pytest tests/autoresearch/test_events.py -v` passes.
- All new content lanes (U13/U14/U15/U15b) + modified lanes (U8 storyboard, U10b marketing_audit brief) + U7 call `log_event(kind='moment', ...)` at the required checkpoints (verified per the New-lane Substrate Wiring Checklist item added in this pass + cross-lane integration test).

**Reversibility:** Fully reversible. Schema extensions are additive; existing lanes ignore the new kinds; removing them un-blocks only the portal's moments timeline.

---

- [ ] **U7: Pre-publish human review service (R22 gate 2)**

**Goal:** Land the email-based human review flow. Token-signed approve/reject URLs; SLA-driven nag + **auto-pause + operator notification** at 2× SLA (per TD-9; non-destructive); terminal manual rejection; audit trail.

**Requirements:** R22 gate 2 (origin), D14.

**Dependencies:** U2.

**Files:**
- Create: `src/review/service.py` — single ~200-LOC module (per TD-20): `ReviewService` class with `submit_for_review`, `process_decision`, `check_sla`, signed-URL helper, **audit emission via `events.log_event(kind=..., client_id=...)` to the per-client wide log resolved by `client_events_path(<slug>)` — NOT a separate `audit.jsonl`**, simple email sender (reuses existing `src/api/` email infra if present, otherwise SMTP via existing config). Token signing logic inline via `hmac` stdlib.
- Create: `src/api/review_webhook.py` — webhook endpoint for approve/reject URL clicks (confirmation GET → POST with CSRF token per Plan-level Threat Model)
- Test: `tests/review/test_review_service.py` — single test file covering submit/approve/reject/SLA-breach/token-tamper/secondary-escalation scenarios

**Approach:**
- `submit_for_review(artifact, client_config) -> ReviewRequest`: writes artifact to review-queue dir, generates signed approve+reject URLs, sends email to `client_config.pre_publish_reviewer.email` via the configured email channel. **Emits `events.log_event(kind="review_required", client_id=<slug>, action="submit_for_review", metadata={artifact_id, sla_target, submitted_at})` so the client portal surfaces the pending review with a warm-accent badge.** `review_required` is added to `KNOWN_KINDS` per U6b.
- `process_decision(token, decision, reason)`: verifies token signature, **emits the audit event via `events.log_event(kind="review_approve"|"review_reject", client_id=<slug>, actor="human", metadata={artifact_id, reviewer_email, reason_text, reviewer_note, reviewer_role, reviewer_override, ...})`** (replacing the prior JSONL append), updates artifact state.
- `check_sla()`: scheduled (cron or systemd timer) job that scans pending reviews; sends nag emails at 25/50/100% of SLA elapsed; **auto-pauses (NOT auto-rejects)** at 2× SLA per TD-9 with operator notification; emits `events.log_event(kind="sla_breach", client_id=<slug>, metadata={artifact_id, sla_target, breached_at, ...})` for portal visibility; artifact stays in queue until explicit resume/escalate, not destroyed.
- **Paused-N-days operator override** — cut per Pass-5 YAGNI audit. With 2 clients × 2 reviewers = 4 reviewer slots in v1, the both-reviewers-unavailable-for-7-days case is rare enough that manual JSON-audit-file edit covers it. Re-add as `freddy autoresearch review override` CLI (~30 LOC + audit-log idempotency) when first observed in production OR when client #3 ships and the reviewer pool expands.
- Audit fields land in the canonical event's `metadata` (the event itself carries `kind` + `client_id` + `timestamp` + `actor` at top level): `artifact_id`, `artifact_hash`, `reviewer_email`, `reason_text`, `sla_target`, `submitted_at`, `compliance_flags_at_submission` (from U5), **`reviewer_note: str` (≥1 sentence required for `edit` + `reject` decisions; optional for clean `approve`; per TD-43 site_engine cross-cycle learning data substrate — empty notes log CI warning, don't block publish).** `decision` is encoded by the `kind` itself (`review_approve` | `review_reject` | `sla_breach`); `decision_timestamp` is the event's canonical `timestamp` field.
- Email template: artifact preview (link to viewer), approve button, reject button (with reason text field), SLA reminder. **Compliance flags from `compliance-meta.json` are rendered in the email body** with rule-set provenance and per-rule prose, so the reviewer always sees what triggered.
- **Soft-warn vs hard-block in review:** Hard-block flags cannot be approved (the approve URL refuses with a clear error). Soft-warn flags MAY be approved; the approve token captures a `reviewer_override: true` field in the `review_approve` event's `metadata` so soft-warn approvals are clearly distinguished from clean approvals. Per-rule severity comes from the rule-set definition (D6).
- **Secondary reviewer escalation (per TD-2 revised):** At `escalate_at_pct_sla` (default 50%) of SLA elapsed without primary-reviewer response, the service sends a parallel email to `pre_publish_reviewer_secondary.email` (when defined in R26 ClientConfig) with the same token URLs. Either reviewer's click resolves the artifact; whoever clicks first wins; subsequent clicks return "already decided". Secondary reviewer's approval is logged with `reviewer_role: secondary` in the `review_approve` event's `metadata` for audit trail. Without a secondary defined, fall back to the SLA nag + auto-pause at 2× SLA.
- **Weekly publish target (per TD-2):** lane stops emitting new ship-candidates once `weekly_publish_target` from R26 ClientConfig is met for the week. Resets on Monday in client's timezone. Right-sizes engine throughput to reviewer capacity.
- **CSRF / email-prefetcher mitigation:** approve/reject URLs land on a confirmation page (safe GET); the actual state mutation is a POST with a fresh CSRF token. Mitigates corporate-email-scanner / antivirus auto-fires.
- **Single-use token enforcement:** server-side nonce table or canonical-event idempotency check (search `clients/<slug>/audit/events.jsonl` for an existing `review_approve` / `review_reject` event with matching `event_id` / `nonce` in metadata) before state change. Tokens are constant-time-compared.
- **Token TTL:** matches the per-client SLA (cap at 7 days); expiry equivalent to "SLA breach + grace."
- **Reviewer email change protection:** any edit to `client.yaml:pre_publish_reviewer.email` requires CODEOWNERS review on the `clients/` path and an out-of-band confirmation step (e.g., emails to both old and new addresses).
- No in-engine edit-feedback loop (D14): rejection is terminal; reviewer manually re-uploads to get edits.

**Execution note:** Test-first for token signing and audit log; email delivery tested with `FakeEmailSender` in unit tests.

**Patterns to follow:**
- Marketing audit ship-gate halt pattern (closest precedent, but mostly net-new).
- `src/common/cost_recorder.py` — already mirrors `kind="cost"` events into the canonical log via `log_event(...)`. U7 follows the same pattern with its four kinds (`review_required`, `review_approve`, `review_reject`, `sla_breach`).

**Test scenarios:**
- *Happy path:* Submit artifact → email sent with token-signed URLs → `events.log_event(kind="review_required", ...)` emitted to the per-client log → reviewer clicks approve → `kind="review_approve"` event recorded.
- *Happy path:* Submit artifact → reviewer clicks reject with reason → `kind="review_reject"` event recorded with `reason_text` in metadata.
- *Edge case:* Reviewer clicks both approve and reject buttons (in sequence) → second click rejected as state-invalid (artifact already decided).
- *Edge case:* Reviewer clicks expired token → URL returns "token expired" error; nag email sent.
- *Edge case:* SLA = `48h_business_pl` → 25/50/100% nag emails sent at correct local-time intervals (mock time-of-day).
- *Error path:* Tampered token → signature verification fails → 403 response.
- *Error path:* Email send failure → submission retries with exponential backoff; after 3 failures, alert operator.
- *Integration:* End-to-end flow with mock email + real per-client events log → all four kinds (`review_required` on submit, then one of `review_approve`/`review_reject`/`sla_breach`) land in `clients/<slug>/audit/events.jsonl`.
- *Integration:* SLA breach at 2× → **auto-pause** recorded; operator notified; artifact stays in queue (per TD-9, not auto-reject).
- *Integration:* Pause persists ≥ 7 days → operator notification still firing; manual JSON-edit override path documented in launch runbook. CLI override not built per Pass-5 audit; manual JSON-edit covers the rare both-reviewers-unavailable case.

**Verification:**
- `pytest tests/review/ -v` passes.
- Manual: submit a test artifact; verify email arrives; click approve; verify `kind="review_approve"` event in `clients/<slug>/audit/events.jsonl`.

---

- [ ] **U7b: Playwright site render utility (R27)**

**Goal:** Land the shared site-rendering utility that `site_engine` (U15b) and any future visual-eval lane consume. Headless Chromium via Playwright; configurable viewport; font-load wait; screenshot capture; section-snippet rendering (wraps a section's HTML+CSS+JS in a minimal host page with the client's brand tokens for accurate rendering).

**Requirements:** R27.

**Dependencies:** U2 (per-client config — reads `brand_tokens` for the host-page shell).

**Files:**
- Create: `src/generation/site_render.py` (~180 LOC, increased from 150 to account for network-block + classifier + sandbox refusal). `SiteRenderer` class:
  - `__init__(self, viewports: list[ViewportSpec] = DEFAULT_VIEWPORTS)` — defaults to `[("desktop", 1440, 900), ("mobile", 375, 812)]`. **Raises `UnsafeRenderEnvironmentError` at construction if `platform.system() != "Linux"` AND `os.environ.get("GOFREDDY_U7B_ALLOW_UNSANDBOXED") != "1"`.**
  - `render_section(self, section_html: str, section_css: str, section_js: str, brand_tokens: BrandTokens) -> RenderResult` — wraps in a host page, launches headless Chromium with **network-block flags** (see Approach), waits for `document.fonts.ready` + 300ms settle, captures screenshot + DOM snapshot
  - `RenderResult` dataclass: `screenshot_paths: dict[viewport_name, Path]`, `dom_snapshot: str`, `console_errors: list[ConsoleMessage]`, `network_blocked: list[BlockedRequest]`, `render_time_ms: int`, `degraded: bool`, `degraded_reason: str | None`
  - `ConsoleMessage` dataclass with `severity: Literal["error", "warning", "info"]`, `text: str`, `source: Literal["lane-html", "lane-css", "lane-js", "external", "unknown"]` (source classification distinguishes "broken JS we wrote" from "blocked external font triggered a warning" — the structural gate consumes only `severity == "error" AND source.startswith("lane-")`)
  - Cost recording via `cost_recorder.record("playwright", "render", cost_usd=0.0, ...)` (Playwright is local; cost recorded for time-budget accounting, not money)
  - Circuit breaker (`CircuitBreaker(failure_threshold=3, reset_timeout=60, name="site_render")`) wrapping the Chromium subprocess launch
- Create: `tests/generation/test_site_render.py` (~140 LOC, increased to cover network-block negative tests). Tests: minimal section renders successfully; missing font does not hang (timeout enforced); console error from broken JS surfaces with correct `source` classification; circuit breaker opens on 3 launch failures; **negative network tests** — attempts to fetch `169.254.169.254`, `10.0.0.1`, `localhost`, RFC1918 ranges all return `degraded=true` with `network_blocked` populated; **production-only refusal** — on macOS without `GOFREDDY_U7B_ALLOW_UNSANDBOXED=1`, raises `UnsafeRenderEnvironmentError`.
- Modify: `pyproject.toml` — add `playwright>=1.45` to `[dependency-groups.dev]` (Playwright is dev-tier — never invoked from production API path).
- Modify: `.github/workflows/test.yml` — add `playwright install chromium` step before pytest runs; CI runs on Linux only so the sandboxing check passes naturally.

**Approach:**
- Headless Chromium only (Firefox / WebKit deferred — no client need in v1).
- Host page is minimal: HTML5 doctype, `<meta viewport>`, brand-token `<style>` block injected, then the section under `<main>`. No analytics, no third-party scripts.
- Screenshot is full-section (not full-page) via `page.locator('main > *').screenshot()`.
- DOM snapshot captures the *post-render* DOM (after JS executes) so the structural gate can analyze the actual rendered tree, not just the source HTML.
- **Network blocking (per Threat Model render-pipeline SSRF row):** Chromium launched with `--host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"` + `--disable-features=NetworkService,DnsOverHttps,WebRTC` + `--disable-background-networking`. Additionally `page.route("**/*", route.abort)` for any URL not matching `data:` or relative-to-host-page. Combined with brand_tokens "fonts 100% local" rule (no external font CDN), this blocks the SSRF surface entirely. `page.on("request")` records every blocked request into `RenderResult.network_blocked`.
- **Console-error classification:** `page.on("console")` captures all messages. A classifier maps each to a source tag (`lane-html` / `lane-css` / `lane-js` / `external` / `unknown`) by matching message text + stack source against the host-page's content-derived URL pattern. The structural gate (U15b) consumes only `severity == "error" AND source.startswith("lane-")` — external-asset warnings (blocked CDN font, broken `<link>`) do NOT trip the gate; they show up as `degraded=true` with reason. Prevents false-positive failures from the network-block layer.
- **Sandboxing posture (per Threat Model):** `SiteRenderer.__init__` raises `UnsafeRenderEnvironmentError` if `platform.system() != "Linux"` AND `os.environ.get("GOFREDDY_U7B_ALLOW_UNSANDBOXED") != "1"`. Production deployment target = Linux container with seccomp + user namespace. macOS dev gets the explicit env-var escape hatch with logged warning.
- Font-load wait pattern mirrors `/tmp/pw-shoot/og-render.mjs` from the 2026-05-13 landing-page session (`await page.evaluate(() => document.fonts.ready)`).

**Patterns to follow:**
- `src/generation/fal_client.py` circuit-breaker pattern (3-failure threshold, ModerationBlockedError is fatal not breaker-counted — adapt: Chromium launch failure IS breaker-counted, but a section that renders with console errors is NOT a failure).
- `src/common/cost_recorder.py` JSONL append (cost=0.0 for local renders, kept for budget-accounting symmetry with other generators).
- `src/generation/composition.py` FFmpeg-subprocess pattern (clean shutdown on timeout, structured error surface).

**Test scenarios:**
- *Happy path:* Render a minimal hero section → screenshot exists + DOM snapshot captured + zero console errors AND zero blocked requests.
- *Happy path:* Render a section with local font in brand_tokens → font loaded before screenshot.
- *Edge case:* Section JS throws → `console_errors` contains entry with `severity="error"` AND `source="lane-js"`; screenshot still captured.
- *Edge case:* Section CSS references undefined token → render proceeds with browser-default; warning surfaced with `source="lane-css"` (does NOT trip structural gate per source classification).
- *Edge case:* Section attempts external font load → blocked at network layer; `degraded=true`; `network_blocked` populated; `console_errors` has external-source warning (does NOT trip structural gate).
- *Security path (negative network):* Section HTML includes `<img src="http://169.254.169.254/metadata">` → request blocked; `network_blocked` records it; `degraded=true`.
- *Security path:* Section includes `<img src="http://10.0.0.1/...">` (RFC1918) → blocked; `degraded=true`.
- *Security path:* Section includes WebRTC ICE candidate exfiltration JS → WebRTC disabled at Chromium flag level; harmless.
- *Sandboxing path:* On macOS without `GOFREDDY_U7B_ALLOW_UNSANDBOXED=1` → `UnsafeRenderEnvironmentError` raised; lane fails fast with operator message.
- *Sandboxing path:* On macOS with `GOFREDDY_U7B_ALLOW_UNSANDBOXED=1` → render proceeds with logged warning; dev workflow not blocked.
- *Error path:* Chromium binary missing → clear error message ("run `playwright install chromium`").
- *Error path:* 3 consecutive launch failures → circuit breaker opens; subsequent calls fail fast.
- *Performance:* Single-section render ≤ 2.5s p95 on dev hardware.

**Verification:**
- `pytest tests/generation/test_site_render.py -v` passes (all happy + security + sandboxing tests).
- Manual: render a section from the 2026-05-13 landing page; compare screenshot to live page (pixel diff < 5%).
- Manual security check: craft a hostile section HTML with metadata-endpoint URL + WebRTC exfiltration + external CDN font; render returns `degraded=true` with all three blocks recorded; no real network egress observed (verify via `tcpdump` on render host).

**Reversibility:** Fully reversible — module is additive. Removing it un-blocks only U15b (which depends on it).

---

**U7c (removed per YAGNI audit 2026-05-13):** axe-core + Lighthouse-equivalent audit utility cut for v1. SE-6 (a11y) + SE-7 (perf) become **operator-hand-graded** for v1 — reviewer inspects the rendered screenshot + console log from U7b (which already returns those) against a brief checklist (semantic-HTML basics, WCAG AA contrast, payload reasonable for section type) when approving a section. Quarterly: collect rejected/edited cases and update SE-6/SE-7 rubric prose in `docs/rubrics/site-quality.md`. **Re-introduce U7c (v1.5 trigger) when:** ≥1 onboarded client reports a published section with a real a11y regression, OR operator-grading time exceeds 5 min per section, OR client #3+ archetypes need different perf budget defaults than the v1 hand-checklist. Saves ~200 LOC + Node toolchain dep + CI step; removes 1 unit.

---


- [ ] **U8: Storyboard extension (R1–R4)**

**Goal:** Extend the existing `storyboard` lane with `platform_target` (5 values) + `format_mode` (3 values) + voice corpus input. Apply per-client content_denylist enforcement.

**Requirements:** R1, R2, R3, R4.

**Dependencies:** U2, U3, U5. **Note on U5 dependency:** storyboard is one of the 7 compliance-gated lanes per D25 — this is a NEW gate added in v1 (pre-existing storyboard outputs were unregulated; v1 brings all 7 content lanes to parity on compliance review). U8's implementation must register `<rule_set>_storyboard_compliance` rubric IDs alongside the existing SB-1..SB-8.

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

- [ ] **U10b: marketing_audit lane brief emission (additive, required by TD-29)**

**Goal:** Extend `marketing_audit` lane to emit findings-briefs at promotion time. site_engine (U15b) consumes these as its primary brief source per TD-29. Mirrors U9 (geo) + U10 (monitoring) emission shape.

**Requirements:** TD-29 (marketing_audit is the named primary brief source for site_engine; without this unit, U15b consumes briefs that aren't produced).

**Dependencies:** U4 (findings-brief schema + emitter). marketing_audit lane already shipped (PR #45, commit `0543d7b`, on origin/main); this unit is additive.

**Files:**
- Modify: `autoresearch/archive_marketing_audit/current_runtime/workflows/marketing_audit.py` — add brief-emission hook to the promotion flow (same shape as U9 in geo).
- Test: `tests/autoresearch/test_marketing_audit_brief_emission.py` (~80 LOC, mirror U9 test).
- Modify: `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` + `dwf-launch-runbook.md` — note that marketing_audit must run before site_engine for brief consumption to be populated.

**Approach:**
- Brief emission is promote-time only (D8). Hook into marketing_audit's promotion flow; on promote, walk the audit session output for ship-eligible findings (section-level recommendations: which page sections to improve, why, expected impact) and serialize via `src/briefs/emitter.py`.
- Source pointer = audit report path + finding ID. Target lanes = `["site_engine"]` (primary). Voice persona = inherited from client_config. Priority = mapped from audit severity (`high → "high"`, `medium → "medium"`, `low → "low"`).
- `valid_until` = 30 days post-promotion (marketing audits stale faster than geo signals).

**Execution note:** Test-first.

**Patterns to follow:** U9 geo emission shape; marketing_audit `_safe_format` precedent for any prompt-embedded JSON.

**Test scenarios:**
- *Happy path:* Klinika marketing audit promotes → ≥1 brief emitted per section-level finding → site_engine reads via U4 reader.
- *Edge case:* Audit completes with zero ship-eligible findings → no briefs emitted; lane logs the absence.
- *Edge case:* Stale brief (`valid_until` passed) → skipped at consumer per D9.

**Verification:** `pytest tests/autoresearch/test_marketing_audit_brief_emission.py -v` passes. Manual: run Klinika marketing audit; verify briefs land in `autoresearch/archive_marketing_audit/current_runtime/briefs/`; verify site_engine reads them.

**Reversibility:** Fully reversible — additive emission hook. Removing it un-blocks only U15b's primary brief source (U15b degrades to geo-briefs-only).

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

**Cross-cutting moment-emission requirement (applies to ALL lanes built or modified in this plan):** every lane MUST call `log_event(kind='moment', client_id=<slug>, metadata={'moment_kind': ..., 'title': ...})` per the U6b contract at minimum the three checkpoints in R-Lane-2: `session_start`, `deliverable_ready`, `session_completed`. Verified by cross-lane integration test in U6b. Optional checkpoints (`decision_logged`, `error_recovered`) are lane-author discretion. Lane authors compose moment titles in operator-readable English ("Article draft v3 ready for review — 'AI agents in marketing'") so the client portal's timeline reads cleanly without further transformation.

- [ ] **U13: article_engine lane (R5–R10)**

**Goal:** Land the new `article_engine` lane. Produces blog + LinkedIn Article from topic + voice + source material + optional findings-brief.

**Requirements:** R5, R6, R7, R9, R10. R8 explicitly dropped per origin doc.

**Dependencies:** U2, U3, U4, U5. No judge-plan gate (G1 reclassified as informational per Substrate Consumed section); aggregate scoring sufficient for v1.

**Judge wiring (per Substrate-consumed S1 + S2):**
- `inner_backend = "codex"`, `inner_model = "gpt-5.5"` — frontier-only per memory `judge-decisions-2026-05-11.md`; diverse from any DeepSeek/Claude inner-loop. Set statically on `LaneSpec` per `cc212c2` priority (mirrors geo + competitive pattern at `lane_registry.py:174-175, 206-207`). **No automatic cyber-filter fallback exists in the substrate** — `ModerationBlockedError` is raised by image/video/audio backends only, never by text inner-session agents; codex cyber-flag rejection produces a session marker, not a runtime exception the harness can catch. If U18 smoke shows codex hard-rejects article content on known-clean Klinika/DWF topics, swap statically to `inner_backend = "claude"`, `inner_model = "sonnet"` via a one-line `LaneSpec` edit + redeploy. (Dynamic detector + auto-fallback wrapper is **rejected as substrate complexity** — static-pin via LaneSpec edit + redeploy is sufficient. If U18 smoke shows hard-rejects, swap statically; that's the permanent answer, not a v1 deferral.)
- **Cyber-filter terminal-failure telemetry (per Pass-4 reliability audit + 2026-05-15 substrate audit, simplified + concretized):** the actual detection mechanism is **stdout/stderr pattern-matching** by `agent_retry.is_terminal_codex_failure(returncode, stdout, stderr)` (`autoresearch/agent_retry.py:156`) against `_CODEX_TERMINAL_MARKERS = ("cybersecurity risk", "content was flagged", "flagged for possible")` (`agent_retry.py:144-153`). NOT a session-marker file — the term "session marker" in earlier prose referred colloquially to the stdout log line `"Session BLOCKED: terminal agent marker detected (content-moderation / cyber-flag)"` (see `lane_registry.py:202-204` comment for the in-tree reference). U13/U14/U15/U15b wrap their variant execution such that any `True` return from `is_terminal_codex_failure` emits a row via `compute_metrics.append_generation_row({"lane": <lane>, "gen_id": <variant_id>, "terminal_failure": True, "marker_patterns": [...matched markers...], "ts": <unix>})` (the helper already exists at `autoresearch/compute_metrics.py:138-141`). **Alerting deferred** — no cron, no threshold; operator reviews the metrics file during weekly check-in (or `freddy autoresearch metrics summary` ad-hoc). Build the alerting layer only if U18 smoke shows real signal. **Reflected in §New-lane Substrate Wiring Checklist Item 11.** Applies to U13/U14/U15/U15b identically.
- Outer judge backend: claude/opus (frontier, diverse from inner-loop). Critique backend: codex/gpt-5.5 via `CRITIQUE_BACKEND` env (existing default).
- Compliance-judge backend: per D25 (single `claude/opus` across all lanes with reviewer-assist gates, held in U5's `COMPLIANCE_JUDGE constant` singleton; no per-lane override).
- AE-1..AE-8 rubric anchors follow the post-rewrite design (S2): operational definitions + falsifiability + named Score-3 failure modes + anti-gaming clauses. **Do NOT propose AE-9 kernel rubric** (judge plan rejected the LANE-9 pattern for 4 of 5 lanes; 8-rubric convention holds).

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/article_engine.py` (~200 LOC, mirror x_engine.py)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_article_engine.py` (~250 LOC, mirror session_eval_x_engine.py)
- Create: `autoresearch/archive/v007-curated/programs/article_engine-session.md` (~300 LOC, agent prompt)
- Create: `autoresearch/archive/v007-curated/programs/article_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/article_engine/skeleton-blog.md` (cold-start; see TD-40 prose for envelope shape)
- Create: `autoresearch/archive/v007-curated/templates/article_engine/skeleton-linkedin_article.md`
- Create: `autoresearch/archive/v007-curated/templates/article_engine/skeleton-deep_dive.md` (for `length_bracket: deep_dive` per TD-40, technical case studies 2,200-3,500 words)
- Create: `autoresearch/archive/v007-curated/templates/article_engine/anti_patterns.yml` (12 anti-patterns per TD-40 — deny-regex banned phrase list)
- Modify: `autoresearch/lane_registry.py` — add `article_engine` `LaneSpec` with `rubric_ids=("AE-1", ..., "AE-8")`, `readonly_subprefixes` for workflow + session_eval + shared voice/brief/compliance substrate
- Modify: `src/evaluation/rubrics.py` — add AE-1..AE-8 rubric prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py` — register `article_engine` SPEC
- **Create: `src/verification/citation_verifier.py` (~150 LOC per TD-44)** — fetches URL via `httpx.AsyncClient` → extracts main content via BeautifulSoup → claude/opus call "does this URL substantiate claim X" → returns `{verified: bool, confidence: float, rationale: str}`. Fires on claims with URL citations only; claims without URLs = hard structural fail.
- **Create: `src/verification/citation_cache.py` (~40 LOC per TD-44)** — caches verified `claim+URL` pair indefinitely; `--fresh` CLI flag busts cache.
- **Create: `tests/verification/test_citation_verifier.py` + `tests/verification/test_citation_cache.py`** (unit tests for new primitives)
- Create: `autoresearch/eval_suites/article_engine_klinika_procedure.json` — Klinika procedure-page fixture (regulated B2C-aesthetics archetype coverage per D11)
- Create: `autoresearch/eval_suites/article_engine_dwf_kse.json` — DWF KSeF regulatory explainer fixture (regulated B2B-regulated archetype coverage)
- **Create: `autoresearch/eval_suites/article_engine_saas_thought_leadership.json` (per TD-53 #1)** — SaaS B2B thought-leadership fixture (`b2b_saas` archetype coverage; first-party from gofreddy.ai blog archive or analogous AI-infra/dev-tools content — Linear/Vercel/Replicate blog style).
- Modify: `autoresearch/eval_suites/search-v1.json` — add new fixtures
- Create: `tests/autoresearch/test_article_engine_substrate.py` (~125 LOC, mirror test_x_engine_substrate.py)
- Create: `docs/plans/2026-05-13-002-AE-rubric-anchors.md` — rubric prose anchor reference (mirror `2026-05-07-001-x-engine-rubric-anchors.md`); TD-40 specifies the 8-axis structure with operational defs + falsifiability + Score-3 failure modes + anti-gaming clauses per axis

**Approach:**
- Mirror x_engine `WorkflowSpec` shape; `count_findings → 0` (drafts are deliverables).
- Single parametrised workflow per R6: one session prompt with conditional per-platform adaptation sections (blog markdown + SEO meta + schema.org/Article + image briefs; LinkedIn Article with first-200-char hook + paragraph rhythm).
- `configure_env`: reads `$ARTICLE_ENGINE_TOPIC`, `$ARTICLE_ENGINE_VOICE_PERSONA_REF`, `$ARTICLE_ENGINE_SOURCE_MATERIAL_PATHS`, `$ARTICLE_ENGINE_TARGET_PLATFORMS` (csv: `blog | linkedin_article`), `$ARTICLE_ENGINE_BRIEFS_PATH` (optional).
- **Source material acquisition (per TD-36):** operator-curated files in `clients/<slug>/source_material/`; paths referenced from `ClientConfig.source_material_paths` (U2). Formats supported: markdown preferred; PDF via existing `src/audit/pdf_to_markdown.py`; HTML via BeautifulSoup; URL list via existing `src/competitive/providers/` patterns. Loader reads + concatenates source content into the session prompt context. Existing `session_eval_<lane>.load_source_data(mode, artifact, session_dir)` primitive applies (see geo/monitoring/storyboard/competitive precedent at `archive/v038/workflows/session_eval_*.py`).
- **Brief consumption — top-K=3 hybrid (per TD-40):** if `$ARTICLE_ENGINE_BRIEFS_PATH` set, reads via U4 reader, top-3 briefs by priority. **ONE designated `primary_brief`** (drives thesis + voice register + hook) + **2 `evidence_briefs`** (mined for stats, counter-examples, named entities). Session prompt forces "every numeric claim must trace to a `brief.source_id`" — preserves citation density without merging stances. Mode is per-call: SaaS thought-leadership uses synthesis (`brief_consumption_mode: hybrid`); medical_pl + legal_pl clients default to K=1 (`brief_consumption_mode: primary_only`) to keep compliance audit trail clean. Configurable per client.
- **Length conventions (per TD-40):** SaaS/AI blog 1,500-2,500 words target 1,800 (industry benchmark: Bluehost/Orbit Media 2025 data; 39% of marketers publishing 2,000+ report strong vs 21% baseline); `length_bracket: deep_dive` 2,200-3,500 words (technical case studies — Anthropic/Stripe/OpenAI engineering-blog shape). LinkedIn Article 1,200-1,800 words target 1,500 ("7x posts" multiplier dies past 2,000 unless thought-leader status). **Hard caps:** blog 800 min / 4,000 max; LinkedIn Article 600 min / 2,200 max → out-of-bounds = structural fail (no judge cycle wasted).
- **Mutation surface (per TD-40):** mutable = `programs/article_engine-session.md` (primary mutation surface — x_engine precedent) + `templates/article_engine/skeleton-*.md` (per-platform skeletons — linkedin_engine v040 cold-start fix precedent) + decomposed `programs/article_engine/prompts/stage_1_outline.md` + `stage_2_draft.md` if pipeline decomposed (stage-decomposed prompts are higher-leverage than monolithic). Read-only: `workflows/article_engine.py` (substrate; blast radius into judge wiring), `judges/session/prompts/article_engine/*` rubric prose (Goodharting prevention), `programs/references/voice.md` (shared substrate), `programs/article_engine/compliance/*.yaml` (operator-curated).
- **AE-1..AE-8 anchor draft (refined per TD-40 — operationalized with falsifiability):** AE-1 hook strength (first 60 words blog / first 210 chars LinkedIn fold deliver falsifiable claim, named subject, or concrete result; Score-3: "in today's landscape" / restated topic / unmotivated rhetorical question; hook must be testable against body's main claim) / AE-2 thesis specificity & falsifiability (body advances at least one claim that could be proven wrong; Score-3: "X is important" / "Y has many benefits" unfalsifiable; hard floor: ≥3 concrete numeric/named-entity claims per 1,000 words) / AE-3 citation density & verifiability (counts `[N]` refs per 1,000 words AND verification rate per TD-44 — every numeric/attributive claim traces to `brief.source_id` OR `voice.md` AND verifier returns `verified: true`; Score-3: "studies show"/"experts say" without inline link + named source; hard floor: untraceable citation = structural fail) / AE-4 voice fidelity (first-person register, lived-work entities from `voice.md`, no slop register words from deny-regex; Score-3: corporate-passive / hedge stack / generic AI register) / AE-5 argument coherence & structure (visible problem → mechanism → evidence → implication arc; Score-3: paragraphs reorderable without meaning loss = listicle disguise) / AE-6 skimmability & rhythm (subhead every 200-300 words; paragraph length ≤4 sentences blog / ≤3 LinkedIn; one TL;DR or summary callout; Score-3: wall-of-text >400 words without break) / AE-7 platform-adapter compliance (blog: H1 + meta description 140-160 chars + schema.org Article JSON validates `headline/author/datePublished/image` + ≥1 hero + ≥1 inline image brief; LinkedIn Article: 210-char fold-safe hook + 3-5 hashtags + no markdown headers (LI strips them — bold + line breaks instead); Score-3: schema validation fails OR fold-cutoff hook truncates mid-claim) / AE-8 cross-cohort diversity & novelty (geometric-mean across cohort; Score-3: ≥2 articles share opening pattern; mirrors X-6/LI-6).
- **AE-3 citation verification implementation (per TD-44 — builds in v1):** verifier fires post-generation on claims with URL citations. Per-claim flow: fetch URL → extract main content (BeautifulSoup) → claude/opus call "does this URL's content substantiate claim X" → returns `{verified: bool, confidence: float, rationale: str}`. Cache verified pairs indefinitely. Failure modes (404/paywalled/JS-heavy): mark `citation_verification_degraded` on variant + flag for human reviewer. AE-3 rubric scores BOTH density AND verification rate.
- **Anti-patterns enforcement (per TD-40 — BOTH layers):** deterministic structural pre-check (regex + token match against `templates/article_engine/anti_patterns.yml`) runs BEFORE judge dispatch; hit caps AE-1 score at 4 (penalty, not auto-reject). 12 enforced patterns: "In today's fast-paced world" opener; listicle-as-default; "studies show" without inline source; self-promoting "best of" comparisons (Google Dec 2025 update specifically targets); AI register vocab (seamlessly, robust, holistic, leverage, optimize, streamline, cutting-edge, game-changing, revolutionary, transform); hedge stack within 3 sentences (potentially/likely/generally/it may be/could be argued); academic transitions density (Moreover/Furthermore/In addition appearing >2× per 1K words); padded intro before the point (first 150 words don't reach falsifiable claim); unmotivated rhetorical question opener; footnoted-but-untrue citations; bait-y CTA close ("Want to learn more? Schedule a demo!"); restated-thesis conclusion (final paragraph re-summarises without adding implication).
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
- *Integration:* Klinika procedure-page fixture passes both structural gate and AE rubrics + medical_pl reviewer-assist gate.
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
- `inner_backend = "codex"`, `inner_model = "gpt-5.5"` for prompt-and-spec generation. Image generation itself goes through `FalPlatformClient` (D21 score-only; not a judge call). Static-pin pattern same as U13 — no automatic fallback substrate exists; swap via LaneSpec edit + redeploy if U18 smoke shows codex hard-rejects.
- Vision sub-judge backend = **Gemini 2.5** per D24 — **built fresh in this unit** as `src/evaluation/vision_judge.py` (~80 LOC, rubric-driven, emits `dimension_scores`). NOT a wrapper around `image_preview_service.verify_preview()` (which is a fixed 2-axis preview QA tool). Used for visual rubrics that require multimodal evaluation (IE-1 hook visual, IE-2 brand consistency, IE-3 info-density, IE-5 visual specificity, IE-6 carousel arc).
- Outer composite judge: claude/opus for text dimensions (IE-4 format compliance, IE-7 alt-text/accessibility, IE-8 repurposability).
- Compliance-judge backend: per D25 (claude/opus via U5's `COMPLIANCE_JUDGE constant`).
- IE-1..IE-8 rubric anchors follow post-rewrite design (S2). **No IE-9 kernel rubric**; 8-rubric convention.

**Files:**
- Create: `autoresearch/archive/v007-curated/workflows/image_engine.py` (~220 LOC)
- Create: `autoresearch/archive/v007-curated/workflows/session_eval_image_engine.py` (~270 LOC)
- Create: `autoresearch/archive/v007-curated/programs/image_engine-session.md` (~280 LOC)
- Create: `autoresearch/archive/v007-curated/programs/image_engine-evaluation-scope.yaml`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-ig_carousel.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-li_doc_carousel.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-ig_single.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-ig_story.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-hero_banner.md`
- Create: `autoresearch/archive/v007-curated/templates/image_engine/skeleton-ad_static.md`
- **Create: `autoresearch/archive/v007-curated/templates/image_engine/fal_prompts/<format>/<archetype>.md` (per TD-41)** — per-format anchored prompt template library, the highest-leverage mutation surface. Each is a Jinja-style skeleton with `{subject}`, `{action}`, `{brand_palette_hex}`, `{lighting}` slots. Initial library: `ig_single/product-spotlight.md`, `ig_single/data-callout.md`, `ig_carousel/listicle.md`, `ig_carousel/before-after.md`, `li_doc_carousel/data-callout.md`, `li_doc_carousel/case-study.md`, `hero_banner/product-shot.md`, `hero_banner/abstract-brand-anchor.md`, `ad_static/value-prop.md`, `ad_static/offer-pull.md`. Grows over time via meta-agent evolution.
- **Create: `autoresearch/archive/v007-curated/templates/image_engine/anti_patterns.yml` (per TD-41)** — 15 anti-patterns catalogued; vision-judge consumes as context for `failure_modes_observed` field.
- Modify: `autoresearch/lane_registry.py` — `image_engine` `LaneSpec`, IE-1..IE-8 rubric IDs
- Modify: `src/evaluation/rubrics.py` — IE-1..IE-8 prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py`
- Modify: `autoresearch/concurrency.py` — add `fal_image=N` semaphore (D23)
- Create: `src/evaluation/vision_judge.py` (~80 LOC, per D24) — rubric-driven Gemini 2.5 vision judge. Accepts `rubric_id`, image path(s), context; returns `{score, rationale, dimension_scores}`. Invoked by `evaluate_variant.py` for visual rubric IDs (IE-1/2/3/5/6). Sibling to `image_preview_service.verify_preview()` (not a base).
- Create: `tests/evaluation/test_vision_judge.py` — unit tests for the new primitive.
- Create: `autoresearch/eval_suites/image_engine_klinika_carousel.json` — Klinika educational carousel fixture (regulated B2C archetype coverage)
- Create: `autoresearch/eval_suites/image_engine_dwf_doc_carousel.json` — DWF LinkedIn document carousel fixture (KSeF timeline; regulated B2B coverage)
- Create: `autoresearch/eval_suites/image_engine_hero_klinika.json`
- Create: `autoresearch/eval_suites/image_engine_ad_static_klinika.json`
- **Create: `autoresearch/eval_suites/image_engine_saas_carousel.json` (per TD-53 #1)** — LinkedIn document carousel for AI-infra/dev-tools company (`b2b_saas` archetype coverage).
- Create: `tests/autoresearch/test_image_engine_substrate.py`
- Create: `docs/plans/2026-05-13-002-IE-rubric-anchors.md`

**Approach:**
- **Workflow shape (per TD-41) — single workflow with format-dispatch.** 6 formats share ~70% of pipeline (topic → angle → fal source generation → brand-stamp → alt-text → caption → judge); what diverges is composition strategy + skeleton template + rubric weights. `composition.py` exports `compose(format, slides, brand_tokens) -> [PNG]` and dispatches internally. Mirror `competitive.py` per-domain branches inside one lane (NOT `geo.py`'s custom hooks). Six separate lanes would 6× the meta-agent mutation surface for ~3 surfaces of real divergence + block cross-format learning (e.g., a brand-stamp improvement found via `ig_single` should propagate to `hero_banner` for free).
- Workflow calls `image_composer` (U6) for composition; calls `FalPlatformClient.generate_image` for source imagery.
- `configure_env`: reads `$IMAGE_ENGINE_TOPIC`, `$IMAGE_ENGINE_FORMAT` (one of `ig_single | ig_carousel | ig_story | li_doc_carousel | hero_banner | ad_static`), `$IMAGE_ENGINE_VOICE_PERSONA_REF` (for alt-text + caption voice — SE-4 equivalent IE-7 axis), `$IMAGE_ENGINE_BRAND_TOKENS_PATH`, `$IMAGE_ENGINE_BRIEFS_PATH` (optional).
- Format dispatch: each `$IMAGE_ENGINE_FORMAT` value produces a specific composition pipeline (carousel → multi-slide sequential; single → single image; etc.).
- **fal.ai prompt-iteration loop (per TD-41) — anchored templates + 1-shot critique pass (hybrid).** Maintain `templates/image_engine/fal_prompts/<format>/<archetype>.md` (e.g., `ig_single/product-spotlight.md`, `li_doc_carousel/data-callout.md`); each a Jinja-style skeleton with `{subject}`, `{action}`, `{brand_palette_hex}`, `{lighting}` slots. Agent picks template via archetype-classification on the brief → fills slots from `voice_persona` + `brand_tokens` → runs **one** internal critique pass against stripped 3-rubric subset (IE-1/IE-2/IE-5) → sends to fal. **Hard cap: 1 critique pass, no image regeneration** (D21). If post-fal image fails full vision judge, route to human review. The templates library is the highest-leverage mutation surface.
- **Carousel storytelling architecture (per TD-41) — two-step outline-then-prompts with previous-slide visual-context echoed.** For `ig_carousel` (5-10) and `li_doc_carousel` (8-12): (1) **outline pass** (claude/opus) emits `[{slide_n, role, headline, key_visual_concept}]` where `role ∈ {cover, problem, stakes, insight_1..n, proof, payoff, cta}`. Force PSR structure for `li_doc_carousel`; hook-stakes-value(×4)-proof-cta for `ig_carousel`. (2) **Per-slide fal-prompt pass** (parallel inside batches of 3): each prompt receives `{slide_n, role, headline, previous_slide_visual_summary, brand_tokens, palette}`. The `previous_slide_visual_summary` is a 1-sentence factual recap from the outline (not the image), so palette/composition stays coherent without serial blocking. (3) **Cover slide gets dedicated archetype template** (bold-claim + data-point + swipe-indicator). Slide-count enforcement: hard-fail `li_doc_carousel <7 or >12` and `ig_carousel <5 or >10` at L1 structural.
- **Brand-stamp baked-in vs composited (per TD-41) — hybrid.** Palette + lighting register + typography style hint baked into fal prompt via hex codes (Flux 2 handles this — "Use HEX codes for exact brand colors" per fal docs); exact logo PNG + exact-text headlines + CTA button + slide number + swipe-indicator arrow Pillow-composited after. Never let fal render: client brand wordmark, URL, phone number, legal disclaimer (hallucination produces extra-fingers-in-logo failure modes). IE-2 (brand consistency) checks both: palette via vision-judge on fal output; logo presence via deterministic Pillow assertion (logo bounding box detectable by alpha mask).
- **Vision-judge prompt architecture (per TD-41) — multi-dimensional rubric prompt with hex-coded brand tokens (not swatch images), tight context payload, per-rubric dimensions enumerated.** Prompt template includes SYSTEM section (scoring instructions) + BRAND TOKENS (palette hex + typography family + logo position) + CONTEXT (topic, voice persona excerpt, format + dims, slide N of M for carousels) + RUBRIC IE-{n} anchor prose + DIMENSIONS list (per-rubric subdimensions). Per-rubric dimensions: IE-1 `stop_scroll_strength / focal_clarity / thumbnail_legibility`; IE-2 `palette_fidelity / typography_consistency / logo_treatment / iconography_register`; IE-3 `legibility_at_thumbnail / whitespace_balance / hierarchy_clarity`; IE-5 `concept_concreteness / absence_of_generic_filler / metaphor_strength`; IE-6 `cover_hook / slide_pacing / payoff_strength / cta_clarity` (carousel only). Output JSON: `{score, dimension_scores: {...}, rationale, failure_modes_observed: [...]}`. Vision-judge fires per-image; carousel rolls up via `mean(dimension_scores) + min(score) gate` so one weak slide drags the carousel score.
- **Per-format visual conventions (per TD-41 refined):** `ig_single` 1080×1080 ONE focal subject, hook-text ≤7 words if overlaid, mobile-thumbnail-test (legible at 120px), no carousel-style "1/N", palette ≤3 colors, no logos larger than 8% of frame. `ig_carousel` 5-10×1080×1080 cover stops scroll in <2s, slide-2/3 raise stakes, slides 4-7 deliver, slide N-1 proof, last slide CTA; visual continuity = shared palette + recurring structural anchor. `ig_story` 1080×1920 vertical 3-zone hierarchy (top brand strip, middle focal subject, bottom CTA + swipe-up affordance); safe-zone respect (top 250px + bottom 250px reserved for IG UI). `li_doc_carousel` 8-12×1080×1080 (or 1080×1350 portrait) ≤60 words/slide ≥24pt body, B2B aesthetic (restrained palette + Söhne/Inter/Geist-class typography + data visualizations preferred over decorative imagery), PSR arc, designer-y not casual (no emoji, no meme-format). `hero_banner` 1600×900 baseline single-glance comprehension <1s, hierarchy = headline > subhead > CTA > visual, CTA in top-right or center-low (F-pattern), ≤2 typefaces, ≥4.5:1 contrast on text per WCAG 2.2. `ad_static` platform-specific: Meta text-overlay penalty soft-enforced; LinkedIn billboard rule (≤7 words overlay), text-overlay <20% area; hard fail >15% pixel area is text.
- **D21 score-only quality gate** (no image regen); first-usable image accepted.
- **D22 storage backend** (`R2GenerationStorage` vs `LocalDevPreviewStorage`) selected from `GOFREDDY_STORAGE_BACKEND` env.
- **IE-1..IE-8 anchor draft (refined per TD-41 — operational defs + falsifiability + Score-3):** IE-1 hook visual / IE-2 brand consistency / IE-3 info density legibility / IE-4 format compliance / IE-5 visual specificity / IE-6 carousel arc / IE-7 alt-text + voice-consistent caption / IE-8 repurposability. Per-axis dimensions enumerated above in vision-judge prompt template.
- **Mutation surface (per TD-41):** mutable = `programs/session/image_engine.md` + `templates/image_engine/skeletons/<format>.md` + `templates/image_engine/fal_prompts/<format>/<archetype>.md` (highest-leverage — most evolution wins land here) + `scripts/image_composer.py` composition functions + `templates/image_engine/anti_patterns.yml`. Read-only: `brand_tokens` per client (client-controlled, immutable per-run), rubric anchor prose (versioned via `rubric_version`, not per-run mutation), hard format specs (1080×1080 etc — substrate-level), vision-judge prompt structure (judge surface, separate evolution).
- **Anti-patterns enforcement (per TD-41 — BOTH layers):** vision-judge gets `anti_patterns.yml` as context and reports `failure_modes_observed: [pattern_id, ...]` — non-empty list at IE-5 caps score at 4. 15 enforced patterns (catalogued from 2025 research; persisted as `templates/image_engine/anti_patterns.yml`): lime+purple+dark gradient generic-AI palette; three-icon trio with generic gradients (ported from SE-8); floating 3D shapes (blobs/spheres/isometric cubes); stock open-concept office workers around laptop; glassmorphism/neumorphism cards as decorative filler; hallucinated logos/wordmarks (any fal-rendered brand text → always Pillow-composite); hand artifacts (extra fingers, fused hands; vision-judge auto-fail if anatomy off); garbled image-internal text (any fal-rendered marketing copy banned); cover-identical-to-interior carousel; wall-of-text slide (>60 words on `li_doc_carousel` / >15% pixel-area text on ad); generic abstract metaphor ("data as flowing river", "AI as glowing brain") when topic is specific; Inter-default typography when brand specifies otherwise; hero diverse-group-laughing-at-laptop B2B stock cliché; emoji-in-B2B (`li_doc_carousel`, enterprise `hero_banner` — hard fail); off-palette accent colors (ΔE >15 from brand tokens not topic-justified).
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

**Dependencies:** U2, U3, U5. Soft dependency on U14 (image_engine produces ad statics for keyframes). **Storyboard soft dependency REMOVED per TD-52:** ad_engine produces self-contained "Reels Ad plan" output (hook copy + scene-by-scene script + image briefs + voiceover script + on-screen text overlays + CTA) per TD-45; no handoff to storyboard lane in v1. No judge-plan gate (G1 informational; aggregate scoring sufficient for v1).

**Judge wiring (per Substrate-consumed S1 + S2):**
- `inner_backend = "claude"`, `inner_model = "sonnet"` — **statically pinned from day 1** (not codex, not via fallback). Healthcare-vertical and regulated-legal ad vocabulary almost certainly trips codex's cyber filter (geo + competitive already hit this on similar content), and no automatic fallback substrate exists. Pinning sonnet from day 1 mirrors `lane_registry.py:174-175, 206-207` precedent. Reversible after U18 smoke via LaneSpec edit + redeploy or per-invocation CLI override (`freddy autoresearch ... --inner-backend codex`); a runtime feature-flag mechanism for backend swapping does not exist and is not in v1 scope.
- Outer judge: claude/opus. Compliance-judge backend per D25 (via U5's `COMPLIANCE_JUDGE constant`).
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
- **Create: `src/ads/signal_aggregator/weights.yaml` (per TD-42)** — source confidence weights from TD-34 (Meta Ad Library 1.0 / Adyntel 0.85 / Foreplay 0.75 / cross-validation bonus / freshness floor / top-N cutoff); mutable by meta-agent during evolution.
- **Create: `src/ads/signal_aggregator/brief_prompt.md` (per TD-42)** — LLM summarization prompt for the final creative-brief synthesis step; mutable by meta-agent.
- **Create: `src/ads/compliance/anti_patterns.py` (per TD-42)** — deterministic structural pre-check (regex + token match) for 14 SaaS/AI ad anti-patterns; runs before judge dispatch; hit caps AD-1 at 4 + AD-6 at 3.
- **Create: `src/ads/compliance/banned_terms.yaml` (per TD-42)** — hard-gate word lists (Meta health-vertical: `cure|treat|heal|fix|diagnose|symptoms`; LinkedIn: `guaranteed ROI|secret hack|instant hire|spam|aggressive`; "Guaranteed [N]% results"); mutable by meta-agent for tightening/expansion.
- Modify: `autoresearch/lane_registry.py` — `ad_engine` LaneSpec, AD-1..AD-8 rubric IDs
- Modify: `src/evaluation/rubrics.py` — AD-1..AD-8 prose
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py`
- Create: `src/ads/signal_aggregator.py` — combines **5 providers (per TD-34/TD-35)**: Foreplay (Meta/IG/TikTok/LinkedIn crowdsourced ad library — existing subscription), Adyntel (Meta/LinkedIn/Google transparency-pull by domain — existing subscription), **Meta Ad Library API** (free, EU-DSA-favored — NEW for v1), SerpAPI Starter ($25/mo for SERP signal), GSC (free, first-party SEO via Search Analytics API). Auth: `FOREPLAY_API_KEY` + `ADYNTEL_API_KEY` + `META_AD_LIBRARY_TOKEN` + `SERPAPI_API_KEY` + per-client GSC OAuth refresh tokens (shared OAuth client). Locale-aware (reads `ClientConfig.locale` per TD-33).
- Create: `src/ads/signal_merger.py` — dedupe + source-weighted confidence + freshness-tiered prioritization across 3 Meta-side providers (Foreplay+Adyntel+Meta Ad Library API)
- Create: `autoresearch/eval_suites/ad_engine_klinika_meta.json` — Klinika Meta ad fixture (regulated B2C archetype coverage)
- Create: `autoresearch/eval_suites/ad_engine_dwf_linkedin.json` — DWF LinkedIn Sponsored Content fixture (regulated B2B archetype coverage)
- **Create: `autoresearch/eval_suites/ad_engine_saas_linkedin.json` (per TD-53 #1)** — LinkedIn Sponsored Content + Document Ad for B2B SaaS (`b2b_saas` archetype coverage).
- Create: `tests/autoresearch/test_ad_engine_substrate.py`
- Create: `tests/ads/test_signal_aggregator.py`
- Create: `docs/plans/2026-05-13-002-AD-rubric-anchors.md`

**Approach:**
- Workflow mirrors x_engine, with ad-specific structural gates (variant count, format compliance, hook diversity per D15).
- **5-provider signal aggregator (per TD-34/TD-35).** Foreplay + Adyntel + Meta Ad Library API for Meta/IG/LinkedIn ad creative (existing Foreplay+Adyntel subscriptions); SerpAPI for SERP signal; GSC for first-party SEO. Locale-aware (reads `ClientConfig.locale` for SerpAPI gl/hl/google_domain + GSC property selection). On any single-provider failure → degrade gracefully (D16); R19 market-signal dimension no-ops only when ALL Meta-side providers fail simultaneously (which is much less likely given 3 redundant sources).
- **Provider merger logic (per Decision 1 research) in `signal_merger.py`:**
  - **Dedupe key:** `ad_id` where present (Meta Ad Library API has stable IDs); otherwise `sha256(advertiser_id + normalize(creative_text) + format)`. Same underlying ad often has different IDs across Foreplay/Adyntel.
  - **Source confidence weights** (multiplicative on rank score): Meta Ad Library API 1.0 (authoritative, EU-coverage gold-standard); Adyntel 0.85 (transparency-pull, broad geo, 24-72h lag); Foreplay 0.75 (crowdsourced, US-DTC-skewed, archive depth weak >3mo).
  - **Cross-validation bonus:** ads observed in ≥2 sources get `× 1.3` confidence.
  - **Freshness floor:** discard ads `last_seen_active > 90 days` ago (mitigates Foreplay's archive-depth weakness).
  - **Geo gating:** filter by `target_audience.geo` from client config; Meta Ad Library leads for EU clients (per EU-DSA enhanced disclosure), Adyntel for global, Foreplay for US-DTC.
  - **Format match:** prefer ads whose format matches the target platform-format being generated.
- **Async-to-sync bridge:** `ForeplayProvider`, `AdyntelProvider`, `MetaAdLibraryProvider`, `GscProvider` are async (`httpx.AsyncClient`); lane workflow callables are sync per `WorkflowSpec` contract. signal_aggregator exposes a sync `gather_signals(domain, locale) -> SignalBundle` that wraps the async provider calls via `asyncio.run(...)`. Precedent verified 2026-05-15: `autoresearch/archive_x_engine/current_runtime/scripts/evaluate_session.py:497` uses `asyncio.run(evaluate_all_criteria(...))`.
- `configure_env`: `$AD_ENGINE_CAMPAIGN_GOAL`, `$AD_ENGINE_OFFER`, `$AD_ENGINE_TARGET_AUDIENCE`, `$AD_ENGINE_VOICE_PERSONA_REF`, `$AD_ENGINE_PLATFORM_TARGET` (csv: `meta | linkedin`), `$AD_ENGINE_AD_FORMAT_PER_PLATFORM`, `$AD_ENGINE_LOCALE_GL` / `$AD_ENGINE_LOCALE_HL` (from ClientConfig.locale).
- **Variant generation: hybrid parallel-skeleton + sequential-body (per TD-42).** Parallel skeleton pass (one cheap call: "produce 5 distinct angles — hook archetype ∈ {statistic, pain, contrarian, demo-tease, pattern-break} + promise sentence + single proof noun") forces angle-diversity at lowest token cost. Sequential body pass (one call per variant in N=4 loop, each conditioned on assigned skeleton + prior variants' full text + explicit "do not reuse opening N-gram, structural cadence, or proof noun of variants {1..K-1}"). Matches Andromeda + Motion 2025 findings: **angle diversity > wording diversity.**
- **Platform-format variant matrix LOCKED 4/4/4/3 with per-format override via client.yaml (per TD-42):** Meta Reels Ad **4 variants** (vertical 9:16 1080×1920, 9-15s, hook in first 0.8-1.2s, ≤8-word on-screen hook overlay, voiceover 15-30 words, 3-shot storyboard hook/demo/CTA, ≤125 char primary text, ≤27 char headline; **diversity dim = hook archetype** — no two variants share the same); Meta Image Ad **4 variants** (1:1 1080×1080 primary + 4:5 1080×1350 secondary, ≤125 char primary text front-loaded in first 80, ≤27 char headline, ≤30 char description, no text-in-image >20% of frame; **diversity dim = promise type** {outcome / status / efficiency / risk-reduction}); LinkedIn Sponsored Content **4 variants** (≤150 char intro front-loaded, 1-2 line headline, ≤150 char body recommended, first-person voice — LI's own data shows outperforms "we", no stock photos — 0% of top-2%-CTR LinkedIn ads use stock; **diversity dim = insight angle** {observation / framework / contrarian-take / numbered-list}); LinkedIn Document Ad **3 variants — fewer because heavier** (3-10 slides sweet spot 5-7, cover slide must work as standalone, body slides one idea per slide ≤30 words, CTA slide; **diversity dim = content shape** {case-study / framework / mistake-list / data-visualization}).
- **Diversity gate behavior (per TD-42):** reject + regen failing slot with budget=2 retries; on retry, prompt names offending overlapping n-grams explicitly ("your draft shared `tired of broken workflows` with variant 2; pick a different opening"). After 2 failures, persist `variant_k = null` + `failure_reason = "diversity_gate"` (gives meta-agent measurable failure to optimize against). Per-format minimum: if fewer than `ceil(N/2)` variants survive, fail the whole platform-format and surface meta-failure.
- **Signal consumption pattern (Option D hybrid per TD-42).** `signal_aggregator` runs as a deterministic pre-step (pure Python — Rule 5 territory, code not LLM — except for ONE final summarization call). Emits structured `creative_brief.json`: `top_competitor_ads` (top-8 ranked by `longevity_days × cross_source_confidence × format_match_to_target`; each `{hook_text, body_excerpt, format, days_running, sources[]}`) + `recurring_hook_archetypes` (clustered with frequency counts) + `serp_signal` (top-5 for offer keywords + intent classification) + `gsc_signal` (top-10 queries with impressions+CTR+position deltas from prior 28d) + `competitor_voice_anti_examples` (3-5 verbatim hooks the variant should NOT mimic — prevents regurgitation of competitor library). PLUS one LLM summarization call (claude/opus) converting above into 6-10 bullet "what's working / what's saturated / what's an opening" prose. **Main ad-generation agent consumes structured brief + prose summary only; raw signal annex stays available for citation but NOT in default context window.** Token budget control + prevents agent from averaging across competitor corpus.
- **Compliance enforcement TIERED (per TD-42).** Hard structural gate for platform-policy violations that WILL get rejected by Meta/LinkedIn (variant fails compile, regenerate or drop): Meta health-vertical word avoidance `cure|treat|heal|fix|diagnose|symptoms` for any client with `vertical=health|wellness|aesthetic_medicine` (the Klinika case — actual Meta moderation rejects); before/after imagery brief mention for health verticals; LinkedIn `guaranteed ROI|secret hack|instant hire|spam|aggressive`; "Guaranteed [N]% results" (Meta post-2025 enforcement); health-vertical URL paths `therapy|anxiety|depression|counseling` for Meta. Soft rubric (lower score on AD-4; doesn't block): LinkedIn B2B sponsored reading consumer-y for `archetype=b2b_*`; headline > recommended length (40 chars Meta, 70 chars LinkedIn); >20% text-on-image. Rationale: hard gates protect against actual ad-rejection (real loss); soft rubric drives gradient pressure during evolution without blocking shipping when soft violation is intentional.
- **Creative + LP copy linkage: same-agent single-pass (per TD-42).** Both produced in one variant artifact: `variant {ad_creative: {hook, body, cta, image_brief, ...}, lp_hero: {headline, subhead, primary_cta, proof_point}}`. **Hard structural gate (message-match):** `jaccard(tokenize(ad.hook), tokenize(lp.headline)) ≥ 0.4` after stopword removal (research: 2.3% conversion lift per 1% headline alignment; top advertisers see 25% lift). LP `cta.verb == ad.cta.verb` enforced exactly. `ad.body.proof_noun ∈ lp.proof_point`. If site_engine has produced a hero for this campaign already, surface as `prior_lp_hero` for continuity but allow per-variant override.
- Per platform-format combo: emits 4 (or 3 for LI Document Ad) ad creative variants + landing-page hero copy per variant. Targeting/bid/budget recommendations are **out of v1 scope** (triage TD-21).
- Diversity gate (D15): N-token-overlap structural check between variant hooks; fails variant if overlap > threshold; gate behavior per TD-42 above.
- **AD-1..AD-8 anchor draft (operationalized per TD-42):** AD-1 hook strength (first 8 words / first frame must pause SaaS/AI buyer; Score-3 = generic opening "Are you tired of"/"Meet"/"Introducing"; falsifiable: must contain ≥1 of {concrete number, named competitor/category, contrarian claim, specific workflow noun}) / AD-2 CTA clarity (viewer knows what happens on click in ≤4 words; Score-3 = "Learn More"/"Discover the Power of"; falsifiable: CTA verb on platform-native action enum OR specific outcome verb with object) / AD-3 offer specificity (can competitor steal this offer? if yes, specific; Score-3 = "Better analytics"/"Smarter workflows"; falsifiable: offer includes {price OR duration OR quantity OR named deliverable}) / AD-4 platform-format compliance (would Meta/LinkedIn auto-approve? Score-3 = hard-gate hit OR character-limit overrun; falsifiable: deterministic check against platform spec dict) / AD-5 variant diversity (do N variants test distinct hypotheses? Score-3 = variants share archetype OR opening 3-gram OR proof noun = paraphrases not tests; falsifiable: pairwise Jaccard on hook+opening-8-token ≤0.3; archetype enum values all distinct) / AD-6 voice fidelity (sounds like client's other channels? Score-3 = agent house-style with AI-tells; falsifiable: zero presence of banned-word list; voice_persona phrasebook overlap ≥ threshold) / AD-7 market-signal alignment (does variant either ride or counter-position against competitor library? Score-3 = structurally identical to top-saturated competitor archetype without differentiation lever; R19 no-op when `signal_aggregator.degraded == true` for ALL Meta-side providers; falsifiable: agent must cite `brief.recurring_hook_archetypes` either counter or amplify with new angle) / AD-8 conversion-readiness (friction-free creative → LP → action? Score-3 = LP hero contradicts ad promise; falsifiable: structural — ad.hook ∩ lp.headline keywords ≥ 0.4, ad.cta.verb == lp.primary_cta.verb, ad.body.proof_noun ∈ lp.proof_point).
- **Mutation surface (per TD-42):** mutable = `prompts/session/ad_engine.md` (main agent + diversity-pass + brief-synthesizer prompts) + `templates/ad_engine/skeleton-*.md` per format (per-format scaffolds — higher leverage than session prompt, per linkedin_engine v040 cold-start fix precedent) + `src/ads/signal_aggregator/weights.yaml` (source confidence weights from TD-34 — Meta Ad Library 1.0 / Adyntel 0.85 / Foreplay 0.75 / cross-validation bonus / freshness floor / top-N cutoff) + `src/ads/signal_aggregator/brief_prompt.md` (LLM summarization call) + `compliance/banned_terms.yaml` (hard-gate word lists — meta can tighten or expand). Read-only: `workflow.py` (substrate), `signal_aggregator/*.py` deterministic logic (dedupe/hash/geo gating — Rule 5 territory), rubric anchor prose (calibration ground truth).
- **Anti-patterns enforcement (per TD-42 — BOTH layers).** Deterministic structural pre-check (regex + token match in `src/ads/compliance/anti_patterns.py`, no LLM) called before judge dispatch; anti-pattern hit caps AD-1 at 4 (per occurrence) + AD-6 at 3 (voice slipped into AI house-style). Cap mechanism (not auto-reject) preserves meta-agent's ability to discover legitimate uses; creates evolutionary pressure to avoid by default. 14 enforced patterns: "Tired of X? Meet Y" PAS-formula opener; "Unlock [outcome]"; "Harness the power of [tech]"; "Revolutionize your [vertical]"; "AI-powered" without specific capability noun in same sentence (88% of B2B buyers tune out per cited research); "Leverage [thing]"; "Seamlessly integrate"; "Game-changer / next-generation / cutting-edge"; generic `Learn More` CTA (0% of top-2%-CTR LinkedIn ads use it); stock photo office worker at laptop OR people-shaking-hands (0% of top-2%-CTR use stock); founder studio-shot photo with "the future of X" (candid phone-selfies outperform by 45% engagement); three-icon trio (already enforced in SE-8 — propagate to ad image_brief); "Built for modern teams" / "built for the way [role] works" (vague target without firmographic specificity); headline >12 words (Meta=40/LinkedIn=70 chars hard-capped but soft-cap at 12 words for clarity).
- Reviewer-assist gate: per-client `reviewer_assist_checklists` (Klinika `medical_pl` softens Meta health-vertical word avoidance; DWF `legal_pl`; SaaS clients default `gdpr_eu` only in v1 — `ai_disclosure_*` / `ftc_endorsement_us` / `ecom_consumer_us` deferred to first prospect of those archetypes per TD-46 revised 2026-05-18).
- Pre-publish review: every ad variant set enters review queue.
- **Cache TTLs (per TD-39 cache table in §Operational Notes):** Foreplay 24h live / 7d historical; Adyntel 24h live / 7d historical; Meta Ad Library 12h; SerpAPI 24h; GSC 24h with daily 06:00 UTC refresh per client. `--fresh` CLI flag bypasses cache.

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

**Dependencies:** U2 (per-client config — site_engine extends ClientConfig with `site_engine.target_url`, `site_engine.brand_tokens`, `site_engine.sections_in_scope`), U3 (voice persona consumed unchanged for SE-4), U4 (findings-brief contract — site_engine consumes briefs from marketing_audit + geo), U5 (reviewer-assist gate 1), U7 (pre-publish reviewer gate 2), U7b (Playwright render utility — required for SE-1/SE-5/SE-8 visual judges + SE-6/SE-7 hand-grading inputs). U10b (marketing_audit brief emission — TD-29 primary brief source). U7c was cut per Pass-5 YAGNI audit; SE-6/SE-7 hand-graded.

**Judge wiring (per Substrate-consumed S1 + S2 + D24 image_engine vision-sub-judge pattern):**
- **Text rubrics** (SE-2 copy clarity, SE-3 claim honesty, SE-4 voice persona fit): outer judge backend = **claude/opus** (frontier; diverse from inner-loop). Inner backend = **codex/gpt-5.5** by default; **static pin to claude/sonnet at LaneSpec.inner_backend** when client config has `site_engine.codex_fallback: true` (resolved from client config at lane-start, NOT a runtime exception handler — same static-pin pattern as U15 ad_engine per Pass-3 audit). Per U13: no automatic runtime fallback exists in the substrate; the field name "codex_fallback" reflects the policy intent (route around codex's cyber filter) but the mechanism is configuration-time pin.
- **Visual rubrics** (SE-1 hierarchy, SE-5 brand-token fit, SE-8 anti-slop): vision-sub-judge backend = **Gemini 2.5** (per D24 image_engine precedent). Receives `RenderResult.screenshot_paths` from U7b. Anti-slop calibration prose embedded in the judge template references the 2026-05-13 landing-page anchors.
- **Structural-gate axes** (SE-6 a11y, SE-7 perf): NOT scored by an LLM judge. **Operator hand-graded** at pre-publish review against U7b's screenshot + console output, using a brief checklist (semantic-HTML basics, WCAG AA contrast, payload reasonable for section type per `docs/rubrics/site-quality.md` SE-6 + SE-7 anchors). U7c cut per Pass-5 YAGNI audit; re-add trigger documented in §Site rendering Context section.
- **Compliance-judge backend** (per D25): single claude/opus across all lanes with reviewer-assist gates; site_engine inherits.

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
- Modify: `autoresearch/lane_registry.py` — add `site_engine` LaneSpec with `rubric_ids=("SE-1","SE-2","SE-3","SE-4","SE-5","SE-6","SE-7","SE-8")` + per-rule-set compliance ID per Item 5 of §New-lane Substrate Wiring Checklist, `readonly_subprefixes` for site_render utility + voice/brief/compliance substrate, `render_rubric_ids = ("RND-1","RND-2","RND-3","RND-4","RND-5")` per Item 1, `findings_promotion` per Item 1, `count_findings → 0`.
- Modify: `src/evaluation/rubrics.py` — register SE-1..SE-8 prose anchors **as references to `docs/rubrics/site-quality.md`** (not inline duplicates — single source of truth lives in the rubric file per TD-30). Use the existing prose-registry resolution pattern (TD-11): `RubricTemplate.prose_ref = "docs/rubrics/site-quality.md#se-1"` style.
- Modify: `autoresearch/archive/v007-curated/workflows/__init__.py` — register `site_engine` SPEC; bump `RUBRICS` count assertion from 53 → 61 (8 new SE rubrics)
- Modify: `autoresearch/eval_suites/search-v1.json` — add site_engine fixtures
- Create: `autoresearch/eval_suites/site_engine_klinika_hero.json` — Klinika hero-section fixture (first-onboarded regulated B2C example per D11)
- Create: `autoresearch/eval_suites/site_engine_dwf_value_prop.json` — DWF value-prop section fixture (first-onboarded regulated B2B example)
- Create: `autoresearch/eval_suites/site_engine_gofreddy_hero.json` — gofreddy.ai hero-section fixture (canonical training example from 2026-05-13 session). **Snapshot-pinned, not re-fetched:** the fixture bundle includes captured `hero.html` + `hero.css` + `hero-desktop.png` + `hero-mobile.png` + `dom-snapshot.txt` checked into the repo at `autoresearch/eval_suites/fixtures/site_engine_gofreddy_hero/`. The fixture JSON references these by path, NOT by URL. **Why pinned:** gofreddy.ai is a live site that may be edited during the 3-5 month build window; live fetch would invalidate SE-8 anti-slop calibration cross-run reproducibility. **Refresh procedure:** operator one-liner — `npx playwright screenshot --full-page <url> hero-desktop.png` + manual HTML/CSS save into the fixture dir + commit. Not a tracked module per Pass-5 audit.
- Fixture snapshot capture is an operator one-liner via Playwright CLI (refresh procedure documented inline above + in §Operational Notes); not a tracked Python module per Pass-5 audit.
- Bleach/nh3 maintain their own bypass test corpora at the library level — no separate OWASP corpus test maintained here per Pass-5 audit. `test_site_engine_substrate.py` includes 3-4 representative round-trip assertions (`<script>`, `<iframe srcdoc>`, `javascript:` URL) to verify the sanitizer is wired correctly; vector exhaustiveness is the library's responsibility.
- Create: `tests/autoresearch/test_site_engine_substrate.py` (~140 LOC, mirror test_x_engine_substrate.py + verify render + audit utility wiring + vision-sub-judge dispatch)
- Create: `clients/<slug>/site_engine/sections/` — per-client section archive (post-promotion artifacts)
- Modify: `clients/klinika-melitus/client.yaml` — add `site_engine: {target_url, brand_tokens, sections_in_scope, codex_fallback: true}`
- Modify: `clients/dwf-poland/client.yaml` — same
- Modify: `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` — add site_engine launch steps
- Modify: `docs/runbooks/2026-05-13-002-dwf-launch-runbook.md` — same
- **Create: `src/site_engine/reviewer_diff_capture.py` (~80 LOC per TD-43)** — nightly diff job that runs textual + DOM diff on `(approved_html, lane_output_html)` pair on review acceptance; tags edit categories per the predefined enum; persists to `reviewer_diffs/<client_slug>/<YYYY-MM>/diffs.jsonl`.
- **Create: `docs/rubrics/site-quality-calibration-log.md` (per TD-43)** — append-only audit trail per anchor change in quarterly reviews. Each entry: date + axis + edit-cluster trigger + prose-before + prose-after + Spearman delta on calibration smoke.
- **Modify: U7 pre-publish review service (existing) to require `reviewer_note: str` field (≥1 sentence)** per TD-43 free-form capture; empty notes log CI warning but don't block publish.
- **Modify: `src/review/service.py` — add reviewer_note field to ReviewResponse schema** + persist alongside accept/edit/reject decision in audit log.
- **Create: `src/site_engine/edit_category_clusterer.py` (~40 LOC, deferred-but-scaffolded for v1.3)** — placeholder for v1.3 LLM-clustered edit-category surfacing. v1 just imports the schema; clusterer logic lands at trigger.

**Approach:**
- Mirror x_engine `WorkflowSpec` shape; `count_findings → 0` (section variants ARE the deliverables).
- Single parametrised workflow per section type: one session prompt with conditional per-section blocks (hero gets H1+lead+CTA; faq gets question pairs; pricing gets tier cards).
- `configure_env`: reads section + voice + brand + brief env vars; passes through to the agent prompt.
- **Brief consumption (per TD-29 + TD-43): 1 finding → N=4 variants.** If `$SITE_ENGINE_BRIEFS_PATH` set, reads via U4 reader; primary source = marketing_audit findings (the audit's 149-lens output names sections + problems); secondary = geo signals (AI-search readiness for the page). Each variant uses a **different `mutation_strategy`** from fixed enum: `{copy_rewrite, hierarchy_reweight, layout_swap, sub_element_add, sub_element_remove}`. Diversity-in-strategy avoids 4 variants that all just rewrite the headline. **Variant count: 4 per section per finding, hard cap 12 total per run** (reviewer triage ~3min/variant set = ~9min/run fits daily pre-publish queue). Per-section `max_variants_per_run` override in client.yaml allows budget-constrained clients to drop to 2. **Multi-brief synthesis = v1.5** — if 3 findings all target `hero`, run 3 independent passes; let judge pick winner. Synthesis is known coupling failure mode.
- **Canonical sub-elements per section (per TD-43)** — agent-visible fields (what the LLM can name/mutate/add/remove). Structural gate fails if required absent. `hero` req `{h1, subhead, primary_cta}` + opt `{eyebrow, secondary_cta, visual, trust_strip, friction_reducer}`; `value_prop` req `{section_heading, body}` + opt one of `{three_card_grid, feature_bullets, alternating_feature_blocks}` (**SaaS/AI clients prefer `alternating_feature_blocks` Linear/Stripe pattern; three-card grid is a slop signal**) + opt `{subhead, inline_visual}`; `social_proof` req one of `{logo_wall, testimonial_cards, metric_callouts, rating_badge}` (combinations allowed); `faq` req `{section_heading, qa_pairs (5-10), accordion_default_open_first: bool}` (default `<details>` native accordion + JSON-LD FAQ schema by default for SEO); `cta` req `{heading, primary_cta}` + opt `{body, secondary_cta, friction_reducer, inline_avatar_proof}`; `pricing` req `{tier_cards (2-4 ideally 3, one with recommended: true — pages without highlighted tier convert ~22% worse), billing_toggle_default}` + opt `{feature_comparison_table, enterprise_callout, disclaimer, recommended_tier_index}`. Tier card sub-elements: `{tier_name, price, price_unit, description, feature_list (5-9 bullets), cta, optional badge}`.
- **Mutation surface — 3-tier whitelist (per TD-43)** declared in `LaneSpec.mutation_surface`. **Tier-A always allowed (~85% of useful evolution):** all text content within any sub-element; add/remove **optional** sub-elements declared per section; swap variant within `{accept-one-of}` group (logo_wall ↔ testimonial_cards ↔ metric_callouts); CSS values *resolved through brand_tokens* (pick different spacing token `--space-4 → --space-6`, different palette role `bg.surface → bg.surface-elevated`, different type-scale step); component-count tweaks within sane bounds (3-card → 4-card grid; 5 → 7 FAQ items; pricing 2 → 3 tiers). **Tier-B allowed with structural-gate scrutiny:** layout structure swap from declared `layout_recipes` list per section (e.g., hero gets 3 named layouts: left-text/right-image ↔ centered ↔ split-screen). Free-form layout invention is out. **Tier-C forbidden v1:** token-value mutation (no inventing new colors/fonts/spacing — brand_tokens READ-ONLY per existing constraint); new `<script>` outside allowlist; cross-section composition (hero changing what's in pricing); required sub-element removal. Mutation surface in code: agent edits `templates/site_engine/skeleton-<section>.html` to produce variants; brand tokens are READ-ONLY (mutation cannot change token values, only consume them).
- **Structural gate (two-pass)** runs BEFORE LLM scoring:
  - **Pass 1 — HTML allowlist sanitizer.** Section HTML goes through `bleach` (or `nh3`) with the section-scoped allowlist (tags `{p, h1-h6, ul, ol, li, a, img, span, div, strong, em, button, section, header, footer, nav, picture, source}` + per-tag attribute lists + URL-scheme allowlist `{https, data:image/*, relative}`). Sanitized output is compared against input; **any difference fails the variant** with reason "non-allowlisted construct stripped: <delta>". Allowlist is the defense; OWASP XSS filter-evasion corpus is the test bench. CSP `script-src 'none'; object-src 'none'; base-uri 'none'` emitted on publish-wrapper for defense-in-depth.
  - **Pass 2 — render + console check.** U7b render; capture `console_errors`. Fail if: render fails (Chromium can't load section); `console_errors` contains entry with `severity == "error" AND source.startswith("lane-")` (per U7b classifier — external warnings excluded); HTML fails semantic-tag check. SE-6 (a11y) and SE-7 (perf) are NOT in the structural gate — they're hand-graded post-promote per Pass-5 audit.
- **Publish-pipeline sanitizer (defense-in-depth):** same allowlist sanitizer that runs in Pass 1 runs again before write to `clients/<slug>/site_engine/sections/`. Two-pass enforcement (lane + publish) means a single-stage bypass doesn't reach production.
- **SE-1/5/8 visual scoring** dispatches **after render completion** to the Gemini 2.5 vision sub-judge with screenshot + brand-tokens manifest + rubric anchor loaded from `docs/rubrics/site-quality.md` at eval time. Invocation timing: post-render (structural gate passes) → outer judge dispatch (text + visual axes in parallel) → score aggregation. Not part of the variant-generation loop.
- **SE-2/3/4 text scoring** dispatches to claude/opus with the section text + voice persona + brief.
- **SE-6/7 scoring** operator hand-graded at pre-publish review against U7b's screenshot + console output, using the SE-6/SE-7 checklists in `docs/rubrics/site-quality.md` (U7c cut per Pass-5 audit; re-add trigger documented in §Site rendering Context section).
- **Compliance gate** (D5/D12): site_engine carries `<rule_set>_site_engine_*` rubric IDs in addition to SE-*. For Klinika (`medical_pl`): no clinical photography in hero; claim language meets Polish health-advertising rules. For DWF (`legal_pl`): no outcome guarantees; jurisdiction language compliant.
- **Pre-publish review** (U7): every promoted section variant enters the review queue with screenshot preview rendered inline in the reviewer email.
- **Cross-cycle learning (per TD-43) — reviewer-feedback capture wired NOW so v1.3 automation has data substrate.** BOTH structured + free-form capture. **Structured** = nightly diff job runs textual + DOM diff on `(approved_html, lane_output_html)` pair and tags edit categories: `copy_change`, `tone_change`, `sub_element_added`, `sub_element_removed`, `layout_swap`, `token_role_swap` (categories predefined; uncategorized → `manual_review` bucket). **Free-form** = required `reviewer_note` field (≥1 sentence) explaining why edit was needed — this is the calibration gold; empty notes → CI warning but doesn't block publish. **Quarterly review session (2-hour operator workflow):** 15min read auto-generated digest (accept/edit/reject rate per SE-axis + top 10 edit categories + top 5 LLM-clustered reviewer-note themes) → 45min anchor walk for SE-axes with edit-rate >30% OR judge-vs-reviewer disagreement >1.0 points → 30min author revisions to `docs/rubrics/site-quality.md` (material changes bump `version`) → 30min calibration smoke (re-score 10 historical fixtures; if Spearman correlation with reviewer ground truth doesn't improve, revert). **Artifacts produced:** versioned `site-quality.md` v1→v2, append-only `docs/rubrics/site-quality-calibration-log.md` (audit trail per anchor change), refreshed `fixtures/site_engine/calibration/` set. **Ad-hoc trigger conditions** (don't wait for quarterly): new client onboarded with materially different vertical; reject rate on any lane >50% for 2-week window; 3 consecutive weekly digests flag same edit category; material judge model swap. **v1.3+ automation roadmap:** primitive 1 (edit-diff capture) lands NOW; primitive 2 (LLM-clustered edit categories surfacing top-N to operator nightly) at ~50 reviewed sections/quarter across ≥3 clients (estimated ~6 months post-launch); primitive 3 (rubric-prose revision suggester) at 12+ months. A/B-tested anchor variants = v1.5.
- **SE-1..SE-8 authority CONFIRMED for SaaS/AI mix (per TD-43)** — anchors at `docs/rubrics/site-quality.md` are calibrated from gofreddy.ai, which IS an AI-first SaaS company. Aligned with Linear/Vercel/Stripe/Resend conventions: outcome-first hero, restraint in color, hierarchy via size+weight+contrast, anti-slop catching three-icon trios and purple-blue gradients. **Per-client softening pattern for non-tech verticals** (in `client.yaml`): `rubric_overrides: site_engine: SE-1: {cta_prominence_target: "restrained"}` (legal B2B doesn't want screaming CTAs — DWF); `SE-2: {domain_vocabulary: ["thread lift", "hyaluronic"], jargon_threshold_words: 12}` (Klinika medical clarity ≠ tech clarity); `SE-3: {claim_compliance_ruleset: "medical_pl", numeric_claim_backing_required: true}`; `SE-8: {slop_signatures: ["stock_lab_coat_photo", "rose_gold_gradient"]}`. Overrides surface in judge prompts via templating; default = no override = SE-* anchors as-written.
- **10 additional SaaS/AI-specific anti-patterns to fold into SE-8 v2** (per TD-43, beyond currently authored): "Build the future of X" / "All-in-one platform for X" headline patterns (distributional convergence; the LLM-generated headline tell); Inter font on everything with no second typeface choice (the typography slop signal); **colored left-border accent card** (3-4px stripe in purple/blue/gradient — single most reliable AI-design tell); "Powered by AI" / "AI-first" badge without specification of what AI does (also fails SE-3); anthropomorphic agent language ("autonomous", "intelligent", "thinking", "understands", "knows", "decides" — cross-reference SE-3 Score-3 modes); founder selfie as hero illustration; generic dashboard screenshot with placeholder data ("$1,234,567 MRR", "John Doe"); bento-grid feature layout when features don't actually vary in importance (2025 Apple-aesthetic copy); 16px uniform border-radius on every element (AI-generated consistency tell; intentional designs vary radius by element role); centered everything with no asymmetry (symmetric composition without intent = safe-AI-output signature). These land in `docs/rubrics/site-quality.md` v2 alongside existing SE-8 anchors at next quarterly review.

**Patterns to follow:**
- x_engine workflow (211 LOC) + session_eval (217 LOC) + session prompt (270 LOC) shape — directly applicable.
- linkedin_engine v040 cold-start fix: ship skeleton templates per section type that the agent can `cp` as first draft.
- article_engine codex-fallback policy (U13) — site_engine inherits the same `ModerationBlockedError` → claude/sonnet fallback pattern.
- image_engine vision-sub-judge dispatch (U14 / D24) — site_engine reuses the dispatch logic for SE-1/5/8.
- ad_engine compliance-rubric-ID composition (U15 + D6 single-rule-set mode per TD-18) — site_engine composes its SE-* IDs with `<rule_set>_site_engine_*` IDs identically.

**Test scenarios:**
- *Happy path:* Generate hero section for gofreddy.ai fixture → structural gate passes; SE-1..SE-8 scores > 0; visual judge returns rationale referencing render screenshot.
- *Happy path:* Generate FAQ section for Klinika fixture → renders with Klinika brand tokens; SE-4 (voice fit) ≥ 4 against Dr. Maria's voice corpus.
- *Happy path:* Generate value-prop for DWF fixture → SE-3 (claim honesty) ≥ 4; legal_pl reviewer-assist gate passes.
- *Sanitizer path:* Section HTML includes `<script>alert(1)</script>` → Pass 1 strips it; sanitized != input; variant fails with reason naming the stripped element.
- *Sanitizer path:* Section HTML includes `<svg><use href="data:..." />` → Pass 1 strips `<use>`; fails.
- *Sanitizer path:* Section HTML includes `<iframe srcdoc=...>` → Pass 1 strips iframe; fails.
- *Sanitizer path:* Section HTML uses `<a href="javascript:void(0)">` → URL-scheme allowlist rejects; href stripped; variant fails.
- *Sanitizer corpus:* feed `tests/autoresearch/test_site_engine_sanitizer.py` OWASP XSS filter-evasion vectors; all must either fail-to-round-trip or strip to inert.
- *Edge case:* Section JS throws console error from lane-authored JS → Pass 2 fails with `source="lane-js"` AND `severity="error"`; variant scored 0; not promoted.
- *Edge case:* Section attempts external font load → Pass 2 records `network_blocked` entry; classified `source="external"`; does NOT trip structural gate; `degraded=true` logged.
- *Edge case:* Section uses off-brand color → SE-5 ≤ 3; rationale identifies the off-brand value.
- *Edge case:* Section has heading-level skip → axe reports `severity ≤ moderate` (not `critical`) → SE-6 scored softly ≤ 3 with rationale; variant proceeds. Heading-skip is NOT a hard-fail per the SE-6 falsifiability rule; **only `severity == "critical"` a11y violations trip the Pass 2 hard fail** (per Approach line 1485). The distinction: critical = blocking accessibility (e.g., missing alt-text on actionable button, contrast below WCAG AA threshold) → hard fail; moderate = scoring penalty (heading-order, optional ARIA labels) → SE-6 ≤ 3.
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
- *Integration:* Klinika hero fixture passes structural gate + SE-1..SE-8 + medical_pl reviewer-assist gate.
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


- [ ] **U16: medical_pl rule set authoring**

**Goal:** Author the `medical_pl` reviewer-assist checklist with Polish-language patterns covering Art. 14 *Ustawa o działalności leczniczej*: superlatives, prices, CTAs, encouragement-to-use.

**Requirements:** R22 (origin). Gated on parallel-track risk #2 (legal-review owner identification).

**Dependencies:** U5.

**Files:**
- Modify: `reviewer_assist/checklists/_placeholder_medical_pl.yaml` → rename to `reviewer_assist/checklists/medical_pl.yaml` and replace placeholder content with legal-reviewed patterns
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

**Goal:** Author the `legal_pl` reviewer-assist checklist for Polish bar / radca advertising rules.

**Requirements:** R22 (origin).

**Dependencies:** U5.

**Files:** Mirror U16 against `reviewer_assist/checklists/legal_pl.yaml`.

**Approach:** Mirror U16. Patterns based on Kodeks Etyki Radcy Prawnego + Zbiór Zasad Etyki Adwokackiej: no solicitation, no fee mentions, no comparisons.

**Test scenarios:** Mirror U16 with legal-flavored patterns.

**Verification:** Mirror U16.

---

- [ ] **U18: Klinika + DWF instantiation + demo orchestration**

**Goal:** Onboard Klinika + DWF as v1's first two real clients (existing relationships, **not design-center cases per TD-54** — design center = SaaS / AI / e-com / creator). Build per-client configs, ingest voice corpora, collect brand assets, run end-to-end demo pipelines. Klinika proves compliance gating + consent friction for regulated B2C; DWF proves same for regulated B2B. Architectural success (config-only onboarding without code changes) is validated by U19's `b2b_tech` stub against a synthetic primary archetype, not by U18 itself.

**Requirements:** Success Criteria — end-to-end demo per onboarded client + ≥5 published artifacts.

**Dependencies:** U8, U13, U14, U15, **U15b**, U16, U17 (all lanes + rule sets must be functional).

**Files:**
- Modify: `clients/klinika-melitus/client.yaml` — complete config with all fields **including the `site_engine:` block per TD-28 (target_url, sections_in_scope, brand_tokens, codex_fallback, weekly_section_target)**
- Modify: `clients/dwf-poland/client.yaml` — complete config with `site_engine:` block
- Create: `clients/klinika-melitus/voice/corpus/medycyna-urody-ch01.txt` etc. — Dr. Maria book chapters (ingested per parallel-track risk #1)
- Create: `clients/klinika-melitus/brand/` — style guide, logo, palette, fonts, reference imagery
- **Create: `clients/klinika-melitus/brand/tokens.json` — site_engine brand_tokens (colors, typefaces, spacing grid, motion). Extracted from `brand/style-guide.md` + `brand/palette.json` during U18 setup. Schema enforced by Pydantic per Threat-Model brand_tokens-swap mitigation.**
- Create: `clients/dwf-poland/voice/corpus/jamka-prior-articles/` — DWF partner articles
- Create: `clients/dwf-poland/brand/` — DWF brand assets
- **Create: `clients/dwf-poland/brand/tokens.json` — site_engine brand_tokens for DWF.**
- Create: `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` — operational steps **including site_engine onboarding: capture klinikamelitus.pl current snapshot, set sections_in_scope (start: hero + faq; add cta + value_prop after first review cycle); first dry-run on hero section**
- Create: `docs/runbooks/2026-05-13-002-dwf-launch-runbook.md` — operational steps **including site_engine onboarding for dwfpoland.pl**
- Create: `docs/runbooks/2026-05-13-002-klinika-artifacts.json` — published-artifact tracking manifest **(site_engine sections count toward the ≥5-per-client target)**
- Create: `docs/runbooks/2026-05-13-002-dwf-artifacts.json` — published-artifact tracking manifest
- Create: `clients/klinika-melitus/voice/CONSENT.md` — per-corpus license + scope + withdrawal record
- Create: `clients/dwf-poland/voice/CONSENT.md` — same
- Modify: `.gitignore` — exclude `clients/*/voice/corpus/` and `clients/*/brand/`

**Approach:**
- Voice corpus ingestion gated on parallel-track risk #1 (partner consent). Once consent lands, ingest via PDF OCR or direct text capture. **Voice corpora are NOT git-tracked** (copyright + GDPR + right-to-erasure considerations); store under `clients/<slug>/voice/corpus/` with `.gitignore` exclusion; per-corpus license/consent record persisted alongside the corpus directory at `clients/<slug>/voice/CONSENT.md` documenting scope of use + withdrawal procedure.
- **Secondary reviewer naming (per TD-2 + TD-17):** Klinika's per-client config (`clients/klinika-melitus/client.yaml`) names a `pre_publish_reviewer_secondary` — operationally: a senior staff member at Klinika (e.g., clinic manager, senior nurse, marketing coordinator) who can sign off when Dr. Maria is unavailable. DWF's config names a second partner or senior associate. Both secondaries must be confirmed during U18 launch-runbook prep (alongside primary reviewer onboarding) BEFORE production launch. **Mandatory for the placeholder rule-set regime per TD-17** (two-reviewer sign-off required while `medical_pl` and `legal_pl` are placeholder-only).
- Brand asset collection coordinated with each client. Brand assets stored locally (not in git for confidential client assets).
- Demo pipeline: pick a single geo brief (Klinika SEO topic) + a single monitoring brief (DWF KSeF event) → run through article_engine → article triggers downstream artifacts (manually for v1, since R8 spawn briefs dropped). **site_engine demo:** for each client, run hero-section variant generation against the marketing_audit brief; produce 3 variants; reviewer (Dr. Maria / DWF partner) picks one to publish to the live site as a section-level swap.
- Pre-publish review service goes live; reviewers (Dr. Maria, named DWF partner) sign off on demo artifacts. **Site_engine reviewer email includes the rendered section screenshot inline** — reviewers see what will be published before approving, not raw HTML.
- **Artifact publication manifest:** create `docs/runbooks/2026-05-13-002-klinika-artifacts.json` and `docs/runbooks/2026-05-13-002-dwf-artifacts.json` with entries `{artifact_id, lane, format, channel, published_url, approver_name, approval_timestamp, published_timestamp}`. Used to track the ≥5-published-per-client success criterion during the per-client launch window.
- **Launch window definition:** 30 calendar days from per-client production go-live (i.e., from the moment client's first artifact is approved-and-published). If <5 pieces are approved within the window, U18 is not signed off; root-cause is logged; one of D5 (regen-with-feedback) or D14 (auto-pause vs auto-reject) may be revisited.

**Patterns to follow:**
- Marketing audit operational runbook precedent (`docs/plans/2026-05-06-001-marketing-audit-v1-deployment-runbook.md`).

**Test scenarios:**
- *Test expectation: none — operational unit. Covered by integration scenarios in U13, U14, U15.*

**Verification:**
- Klinika and DWF configs load without error; voice corpora resolve; brand assets accessible; **`brand/tokens.json` validates against the Pydantic schema** (no external URLs in typefaces, per Threat-Model mitigation).
- End-to-end demo run produces all **5 channel artifacts** per client (article, image, ad, **site-section**, plus storyboard); all pass reviewer-assist gates; all approved by reviewers.
- ≥5 artifacts per client published to real channels during launch window; **site_engine sections that go live count toward this** (a single hero-section swap counts as one published artifact).

---

- [ ] **U19: Architectural success-bar CI diff assertion (right-sized 2026-05-18)**

**Goal:** Validate that a third client (third archetype) can onboard config-only — no code changes to lane internals, rubrics, or shared infra.

**Requirements:** Success Criteria — "Per-client onboarding works config-only for client #3".

**Dependencies:** U18 (all lanes operational with Klinika + DWF).

**Files:**
- Create: `clients/_stub_b2b_tech/client.yaml` — minimal valid ClientConfig for `b2b_tech` archetype (loadable; not executed end-to-end). Includes `archetype: "b2b_tech"`, `archetype_stub_allowed: true`, stub voice_persona_ref, stub brand_tokens path, empty reviewer_assist_checklists, stub reviewer pattern.
- Create: `tests/onboarding/test_client_3_onboarding.py` — **CI diff assertion only** (~50 LOC).

**Approach:**
The CI test does ONE thing: assert that committing a `b2b_tech` archetype + new client.yaml + (optionally) a new reviewer-assist checklist YAML does not require touching any code under `src/` or in the lane-registration substrate.
- Test loads `_stub_b2b_tech/client.yaml` via the production `ClientConfig` loader. If the load succeeds without raising and no `src/` file was added/modified between two designated commits, the architectural bar holds.
- `git diff <baseline_commit>..HEAD --stat -- src/clients src/voice src/briefs src/compliance src/review src/ads src/generation autoresearch/lane_registry.py src/evaluation/rubrics.py autoresearch/archive/v007-curated/workflows/__init__.py` is empty. Only `clients/_stub_b2b_tech/` (and optionally `reviewer_assist/checklists/<new>.yaml` + `autoresearch/eval_suites/` for stub fixtures) may differ.
- **DELETED per cut:** full end-to-end pipeline run against stub, 7-lane synthetic fixtures, stub reviewer + auto-approve flow, operator-time clock measurement, fresh-agent recruitment. These don't validate the architectural bar — they validate that synthetic data flows through synthetic code, which is theater.

**Execution note:** Test-first — the diff assertion is the load-bearing test.

**Patterns to follow:**
- Marketing audit acceptance test precedent (§7.7 dry-run) — but adapted to *structural assertion only*, no pipeline execution.

**Test scenarios:**
- *Happy path:* `ClientConfig.load("_stub_b2b_tech")` returns a frozen model without raising.
- *Happy path:* Diff assertion → only `clients/_stub_b2b_tech/` (+ optional new checklist YAML) changed; no `src/` or lane-registration code.
- *Error path:* Adding a new archetype to the Literal does not require `src/` code — only `src/clients/models.py` Literal edit (1 line) + 1 row in `docs/runbooks/archetype-defaults-v1.5-prospects.md`. (Caught by diff scope.)
- *Error path:* Adding a new reviewer-assist checklist requires only the YAML file — no Python code. (D20 architectural invariant.)

**Verification:**
- `pytest tests/onboarding/test_client_3_onboarding.py -v` passes.
- Manual diff inspection confirms config-only onboarding.
- **Operator-time validation deferred to first real client #3 onboarding** (v1.5+). The first real client of any new archetype (SaaS / AI / e-com / creator / etc.) produces the real-operational signal U19's synthetic clock can't: real corpus shape, real reviewer SLA, real GSC verification, real fair-use questions. Record observed onboarding time at that point in `docs/plans/2026-05-13-002-onboarding-time-measurements.md`.

---

## System-Wide Impact

- **Interaction graph:**
 - `autoresearch/lane_registry.py:LANES` mutated **7 times** (4 new lanes + 3 LaneSpec mods for storyboard/linkedin_engine/x_engine extensions).
 - `src/evaluation/rubrics.py:RUBRICS` mutated **8 times** (4 new lanes × 8 = 32 new IDs + per-lane compliance duplications for 7 compliance-gated lanes); D4 derived count absorbs this without manual lockstep.
 - `autoresearch/archive/v007-curated/workflows/__init__.py:WORKFLOW_SPECS` mutated **4 times** (new lanes register).
 - `autoresearch/eval_suites/search-v1.json` mutated multiple times (new fixtures per lane, including 3 new site_engine fixtures: gofreddy_hero canonical + klinika_hero + dwf_value_prop).
 - New module trees under `src/clients/`, `src/voice/`, `src/briefs/`, `src/compliance/`, `src/review/`, `src/ads/`, `src/generation/image_composer.py`, **`src/generation/site_render.py`** (new shared render utility for site_engine; the original `site_audit.py` was cut per Pass-5 audit).
 - **New top-level doc directory `docs/rubrics/`** introduced for substantial rubric prose with independent versioning (site-quality.md is its first inhabitant; pattern available for any future rubric file that outgrows the inline per-plan anchor convention).
- **Error propagation:** All shared-infra modules (config loader, persona loader, brief reader, compliance judge, review service, **site renderer**) fail loud at lane preflight per CLAUDE.md Rule 12. Lane-side errors (fal.ai circuit-broken, R2 upload failure, missing brand asset, **Chromium binary missing**) fail the variant immediately rather than degrading silently.
- **State lifecycle risks:** Per-client config snapshot at run-start (D7) prevents mid-run config drift; finalize-time check fails loud on drift. Brief promotion is post-promote-only (D8) — variant-emitted briefs never escape their evaluation. Pre-publish review state machine is append-only (terminal decisions cannot be reversed); rollback requires fresh submission. **Site_engine sections post-promotion live under `clients/<slug>/site_engine/sections/` as the client's site history** — removal of a promoted section is a rollback operation (re-submit a corrective variant), not a code revert.
- **API surface parity:** **4 new lanes** follow the existing 8-lane substrate contract (LaneSpec + WorkflowSpec + session.md + evaluation-scope.yaml). Promote-findings + render-report pipelines auto-pick up new lanes via `WORKFLOW_SPECS` dict. **Site_engine additionally registers structural-gate functions for the U7b render + sanitizer Pass-1 pre-checks** — same shape as x_engine's slop-check subprocess registration, no substrate contract change.
- **Integration coverage:** Cross-lane brief handoff is net-new (geo→article, monitoring→article, **geo→site_engine for AI-search readiness signals, marketing_audit→site_engine for the audit's section-level findings**); end-to-end demo pipelines (U18) exercise it. Cross-lane voice consistency is net-new (**5 lanes consume same `dr_maria` persona — article, linkedin, x, ad, site**); U18 demo validates this for Klinika.
- **Unchanged invariants:**
 - The 4 oldest lanes (`geo`, `competitive`, `monitoring`, `storyboard`) retain `_rubric_ids("PREFIX")` helper-style 8-rubric tuples. The new lanes follow the same pattern.
 - `x_engine` + `linkedin_engine` keep their inline 6-rubric tuples and `count_findings → 0` precedent.
 - `marketing_audit`'s `custom_validate` lazy-binding stays as-is.
 - `monitoring`'s `custom_persist_judge_payload` (DQS sidecar) stays as-is.
 - `findings_promotion` remains intra-lane; cross-lane briefs are a separate file convention (`briefs/<brief_id>.json`).

## Cost Envelope

Per-lane per-iteration cost at v1 production settings (precedent: 2026-05-12 evolution postmortem, $2521/75min). Monthly ceiling **$3000** (alert at $2000; halt at $3000); per-iteration halt at $500. Tracked via `cost_recorder.py` hooks.

| Lane | Variants × judges | Est. $/iteration (Klinika fixture) |
|---|---|---|
| `article_engine` | 4 × top-K=3 briefs × (claude/opus + AE-3 verifier + AE-7 voice) | $15-40 |
| `image_engine` | 4 × format × (Gemini 2.5 vision + fal-prompt critique) | $10-30 |
| `ad_engine` | 15 × 6 platform-formats × claude/opus | $40-100 |
| `site_engine` | 4 × ~6 sections × (Gemini 2.5 vision + claude/opus + Pillow sanitizer) | $25-80 |
| `storyboard` ext | 5 × 3 × claude/opus | $20-50 |

**Cost-control levers (descending effect):** reduce variant count (4→2 drops AD ~50%); swap inner to codex/gpt-5.5 ([[project-evolution-redesign-plan-2026-05-13]]); reduce iterations (3→1); defer image+ad evolution to v1.1.

## Rollback & Recall Procedure

Triggered by client report, regulator contact, reviewer-assist false-negative, or QA finding. Recalled variants marked invalid in per-lane archive (`current.json` rolls to previous); reviewer-assist checklist updated based on recall cause; citation added to verifier blocklist if applicable. Existing `events.py` handles `kind="recall"` events; no new substrate. Tabletop validation during U18 before first published artifact.

| Channel | Recall mechanism | SLA (compliance / accuracy) |
|---|---|---|
| Client blog (CMS) | Client admin unpublishes; gofreddy notifies | 4h / 24h |
| Meta Ads | API pause + delete (gofreddy ops creds) | 1h / 4h |
| LinkedIn | Manual delete via UI (no API for organic) | 4h |
| X | API delete (gofreddy ops creds) | 1h |
| gofreddy.ai or client site (site_engine) | git revert + redeploy PR | 4h / 24h |

Recall completion documented in `clients/<slug>/recalls/<date>.md` + surfaces in client portal. Compliance recalls (regulator-initiated): 1-hour acknowledgment SLA. Engagement letter defines responsibility split.

## Parallel-Track Risks (Externally Tracked)

JR-managed offline. Implementing agents check with JR before starting units listed in "Blocker for."

| # | Risk | Status | Blocker for |
|---|---|---|---|
| 1 | Klinika corpus consent (Dr. Maria signoff) | In-progress; family-channel | U18 Klinika SHIP gate |
| 2 | Outside counsel for `medical_pl` + `legal_pl` review | Identifying | U16/U17 promotion |
| 3 | AI-video Klinika validation spike | Deferred v1.5+ | None |
| 4 | Foreplay signal-reliability (3-provider redundancy in place) | Mitigated | None |
| 5 | CI Chromium install for site_engine | Approved | U7b CI integration |
| 6 | During-build new-client onboarding policy | In-progress | U18 sequencing |
| 7 | Klinika family-relationship case-study language | Policy needed | U18 comms |
| 8 | Telemetry/portal v1 vs v1.5 | In-progress; brainstorm shipped | U6b checkpoint emission |
| 9 | site_engine vs Webflow/Framer positioning | Strategic decision pending | None |
| 10 | Steady-state operator-hours (floor ~20h/client × 4 lanes per TD-51) | Will measure at Klinika | None |
| 11 | gofreddy.ai canonical fixture refresh trigger criteria | Operator one-liner exists | None |
| 12 | Engagement-letter language (disclaims compliance opinion + recall SLA + reviewer-assist posture) | Outside counsel draft needed | U18 first onboard |

## Plan-level Threat Model (per triage TD-5)

**Six exploits, each independently sufficient for end-to-end bypass of the reviewer-assist gate.** Three original (HMAC key leak, CSRF/email-prefetcher, reviewer-email-swap) plus three site_engine-specific (XSS/script-injection, brand_tokens-swap, render-pipeline SSRF). The "must all hold" framing in earlier drafts was misleading — each mitigation is independently load-bearing because defeating any single one in isolation is enough to publish a hostile artifact. Site_engine adds the latter three because it's the first lane that produces directly-executable artifacts (HTML+CSS+JS) rather than text or images.

| Exploit | Chain | Mitigation (ship-gate item) |
|---|---|---|
| **HMAC key leak** (env var leak, repo accident, CI log exposure) | Attacker forges approve token → audit log records `reviewer_email` but signature was forged → unreviewed content publishes | TD-3: `GOFREDDY_REVIEW_HMAC_KEY` from env (never repo-checked-in); quarterly rotation; dual-key overlap; single-use enforcement via audit-log idempotency check |
| **Email-prefetcher / CSRF** (corporate mail-gateway URL-scanner auto-fires GET approve URL before human sees email) | Approve token used; audit log records auto-fire as reviewer click → content publishes without human review | U7 auto-fix: approve/reject URLs land on confirmation GET; state mutation is POST with fresh CSRF token; constant-time signature compare; single-use token |
| **Reviewer-email-swap via PR** (malicious or careless PR to `clients/<slug>/client.yaml` swaps `pre_publish_reviewer.email`) | All future approvals route to attacker → content publishes with attacker approval; no signing key needed; no audit alarm | TD-5 + TD-16: `.github/CODEOWNERS` requires security/ops review on changes to `clients/*/client.yaml` protected fields; email change to `pre_publish_reviewer.email` requires out-of-band confirmation to BOTH old and new address with 24h cooling-off; SPF/DKIM/DMARC on sending domain |
| **site_engine: XSS / script-injection in section variant HTML** (variant generates `<script>` tag, SVG `<use href=>`, `<iframe srcdoc=>`, `<object>/<embed>`, `<base>` hijack, MathML event handler, mutation-XSS, `<form action="javascript:">`, namespaced SVG `xlink:href="javascript:"`, CSS `expression()` / `-moz-binding`, dangling-markup, or any other XSS vector that doesn't execute in U7b headless render but DOES execute in production) | Approved section published with embedded XSS; visitor sessions hijacked or analytics tampered | **Allowlist sanitizer (NOT denylist).** `session_eval_site_engine` runs section HTML through `bleach` (Python) or `nh3` (Rust-backed, stricter) with a small section-scoped tag/attribute allowlist: tags `{p, h1-h6, ul, ol, li, a, img, span, div, strong, em, button, section, header, footer, nav, picture, source}`; attributes per-tag (e.g., `a: href + rel`, `img: src + alt + width + height + loading`, `button: type + aria-*`); URL-scheme allowlist `{https, data:image/*, relative refs only}`. **Anything outside the allowlist is stripped, not flagged.** Variants where the sanitized HTML differs from input fail the structural gate with reason naming the stripped construct. Test corpus = OWASP XSS filter-evasion vectors; assertion = none survive sanitization. Defense in depth: production publish pipeline emits CSP `script-src 'none'; object-src 'none'; base-uri 'none'` on the publish wrapper; same sanitizer runs again before write to `clients/<slug>/site_engine/sections/` (two-pass enforcement: lane + publish). Reviewer email preview escapes section HTML in the inline screenshot — preview is the render output, not raw HTML. |
| **site_engine: brand_tokens-swap via PR** (malicious or careless PR to `clients/<slug>/client.yaml` or `clients/<slug>/brand/tokens.json` swaps colors / typefaces / asset refs) | Future site_engine variants score against attacker-controlled brand_tokens; SE-5 brand-fit becomes a no-op; rendered sections may exfiltrate visitor metadata via any external asset reference | TD-5 + new: CODEOWNERS protects `clients/*/client.yaml` AND `clients/*/brand/tokens.json`. **Fonts and asset refs in brand_tokens MUST be 100% local — no external CDN allowlist.** Pydantic validator on `tokens.json` rejects any value matching `https?://` or `//` (protocol-relative) anywhere in the file. **Input bounds (DoS mitigation):** max file size 64 KB, max nesting depth 8, max string length 1024 (rejects JSON-bomb / parser-DoS PRs alongside semantic checks). Operator alert on brand_tokens diff in audit log (similar to reviewer-email change protection). Trade-off accepted: no external font CDN means brand_tokens cannot reference Google Fonts / Adobe Fonts at the schema level; teams that need a specific external font self-host the WOFF2 in the client's repo. |
| **site_engine: render-pipeline SSRF** (variant section HTML includes a remote `<img src="http://internal-service/...">`, `<link href="...">`, `<iframe>`, prefetch hint, or any other fetch surface that U7b's headless Chromium would attempt against the operator's internal network during render) | Operator infrastructure probed via the render subprocess; internal endpoints (e.g., `169.254.169.254`, RFC1918 ranges, localhost) leak to operator-visible logs / screenshots | **Real network blocking — NOT `--proxy-server="direct://"`** (which is a common mistake; that flag tells Chromium to bypass any proxy and go DIRECT, which is the OPPOSITE of blocking). Correct posture: launch Chromium with `--host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"` (forces all DNS resolution except localhost to NXDOMAIN), `--disable-features=NetworkService,DnsOverHttps,WebRTC` (disables service workers + WebRTC + DoH side-channels), `--disable-background-networking`, leave Chromium's sandbox on. Combined with Playwright's `page.route("**/*", route.abort)` for any URL not matching `data:` or relative-to-host-page. Negative test in U7b: attempt to fetch `169.254.169.254` (AWS/GCP metadata IP) + RFC1918 addresses + `localhost` from inside the render — all must return `degraded=true` with reason. Since fonts are 100% local per brand_tokens-swap mitigation, no CDN allowlist exists to re-open the channel. **Sandboxing posture (hardened, not "where available"):** U7b production deployment target = Linux container with seccomp + user namespace OR disposable VM (gVisor / Firecracker / Docker rootless). macOS dev paths run U7b but production hard-fails if `platform.system() != "Linux"` (operator override via `GOFREDDY_U7B_ALLOW_UNSANDBOXED=1` for explicit dev escape hatch; default fail-loud). |

**Defense-in-depth:** each row is independently P0; defeat of any single mitigation is enough to publish hostile content. Treat any unresolved mitigation as a v1 SHIP gate blocker. Also v1 SHIP gates (additive to the table):
- **Publish-pipeline sanitizer:** the same allowlist sanitizer that runs in `session_eval_site_engine` runs again before write to `clients/<slug>/site_engine/sections/`. Two-pass enforcement (lane + publish) means a single-stage bypass doesn't reach production.
- **GDPR data-handling posture for site_engine outputs:** published sections must not embed tracking pixels, third-party analytics snippets, or any external resource that logs visitor IPs (covered by the brand_tokens "fonts 100% local" rule above). Klinika-specific: routes through privacy review before publish given medical-adjacent visitor-data sensitivity. Data-controller boundary documented in `docs/runbooks/2026-05-13-002-klinika-launch-runbook.md` per TD-14 retention pattern.
- **Production deployment target named:** Linux container with seccomp + user namespace; not "where available." macOS dev paths explicitly dev-only.

Site_engine adds three new exploit classes (XSS, brand_tokens-swap, render-SSRF) because it's the first lane that produces directly-executable artifacts (HTML+CSS+JS) rather than text or images.

## Risks & Dependencies

| Risk | Mitigation |
|---|---|
| Plan B retroactively un-archived; lanes need porting to autoresearch_v2/ | JR explicitly archived Plan B 2026-05-13. If reversed, port plan per Plan B Phase 3 U11-U12 conventions. |
| Voice migration regression on linkedin_engine + x_engine | D10 revised per TD-7 + TD-19: noise-floor characterization spike pre-U11/U12 → per-fixture regression bar at `max(5%, 2 × std_dev)`; direct cutover gated on bar (no toggle). Rollback = `git revert`. |
| RUBRICS count merge conflict during per-lane increments | D4 derived count eliminates the manual lockstep; PRs that touch `RUBRICS` and not `LaneSpec.rubric_ids` (or vice versa) fail CI by construction. |
| fal.ai account-level concurrency trip from image_engine + ad_engine load | D23 `fal_image=N` semaphore. Operator dial-up: start at 2, watch for circuit-breaker trips. |
| Compliance pattern catalogs not legally reviewed at v1 ship | Parallel-track risk #2; U16/U17 ship with placeholder rule sets initially. Human gate (U7) carries risk-control weight. v1 SHIP gate: legal review complete OR explicit acceptance of placeholder-only state. |
| Voice corpus consent (per-client property per TD-33 + TD-54) | **Near-zero friction for the expected client mix** (`b2b_saas`/`b2b_ai_first`/`b2c_ecommerce`/`creator_*`/`b2b_agency`/`indie_hacker` — all have public-corpus default; `voice_corpus_consent_required: false`). Public content (blog archives, tweets, video transcripts, newsletter archives, product descriptions, case studies) is abundant for internet-native businesses and requires no consent gate. **Load-bearing only for `b2c_aesthetics` + `b2b_regulated` archetypes** where corpus is private/proprietary. Klinika SHIP gate (consent OR de-tuned rubric posture) and DWF SHIP gate (consent OR style_anchors-only acceptance) are **first-onboarded-client-specific gates**, not v1 architectural risks. SaaS/e-com/creator/agency clients onboarding mid-build or post-v1 have no SHIP gate dependency on consent. |
| AI-generated content fails compliance review (silent fallout) | Per-client `content_denylist` enforces vertical-specific exclusions at variant generation. **Examples across archetypes:** SaaS clients deny `customer_pii` + `unreleased_feature_references`; first-onboarded `b2c_aesthetics` (Klinika) denies `clinical_visuals` + `before_after_imagery`. v1 reviewer-assist stack (per TD-46 revised 2026-05-18): `gdpr_eu` (baseline for EU clients) + `medical_pl` (Klinika) + `legal_pl` (DWF). **Pre-publish human review (U7) IS the safety net** — reviewer-assist checklists accelerate pattern-matching but do not carry legal-grade compliance weight. See §Compliance Posture. |
| **Adyntel + Foreplay + Meta Ad Library all down simultaneously** (R19 market-signal full degradation, per TD-34) | D16 degrades gracefully — R19 dimension no-ops when ALL Meta-side providers fail. **3-provider redundancy** (Foreplay + Adyntel + Meta Ad Library API) means single-provider outage is absorbed automatically; full Meta-side blackout (all 3 down concurrently) would be a coincidental provider-side incident. Mitigations: cross-validation bonus + freshness floor + format-match prioritization ensure best-available signal even on partial degradation. v1.5 hedge if real outage observed: add SocialPeta as 4th source. |
| **GSC OAuth verification timeline (2-6 weeks)** blocks new-client onboarding (per TD-35) | Submit Google verification request at FIRST client onboarding (not later). `webmasters.readonly` is a sensitive scope; Google review takes 2-6 weeks. While in "Testing" status, refresh tokens expire in 7 days — production launch must wait for verified status. Operator runbook: verification submission is a precondition for U18 (first client launch). |
| **Client has no GSC set up** (common for small B2B SaaS, AI startups, professional services, aesthetic clinics) | Operator-assisted DNS-verified Domain property step adds 1-2 hours per client at onboarding (per TD-35). v1 launch runbook (U18) includes this step. Trigger: pre-U18 inventory of which prospective clients have/don't have GSC; budget the 1-2h per missing case. Without GSC, ad_engine R19 first-party SEO signal degrades to no-op for that client (still works on competitive SERP signal). |
| Foreplay/Adyntel API outage or pricing change (per TD-34) | Provider redundancy mitigates outage. Pricing-change risk: Adyntel `$44/mo (5K credits)` is the line item; if Adyntel doubles pricing, evaluate switch to alternative or absorb. Foreplay subscription pre-existing. SerpAPI Starter `$25/mo` similarly small line item. Total ad-data stack ~$70-100/mo at v1; pricing-change impact is low absolute risk. |
| New lanes' max_turns budgets exhausted silently | Marketing audit lesson #2: empirical budget headroom; `expected_output_files` enforces filesystem ground-truth. |
| Schema strictness blocks real agent outputs | Marketing audit lesson #3: ship `extra=allow` initially; tighten after 3–5 real runs. |
| Concurrent meta-agent edits to shared substrate (Pi v007-style) | All shared substrate locked via `readonly_subprefixes` in each lane's `LaneSpec`. Critique-prompt SHA256 manifest provides audit trail. |
| Image composition with Pillow underperforms at scale | D13 default Pillow; benchmark at U6 implementation; switch to Cairo/skia only if blocking. |
| Cross-lane voice migration breaks holdout fixture lineage | D10 revised per TD-7 + TD-19: noise-floor-calibrated per-fixture regression bar (`max(5%, 2 × std_dev)`) on direct-cutover PR; merge blocked if any fixture regresses beyond bar. Rollback = `git revert` the migration PR. |
| Pre-publish review SLA breaches due to reviewer unavailability | D14 + TD-9: 25/50/100% SLA nag emails; **auto-pause + operator notification** at 2× SLA (not auto-reject; non-destructive). Both-reviewers-unavailable-for-7-days case covered by manual JSON-audit-file edit per launch runbook; CLI override not built per Pass-5 audit; manual JSON-edit covers the rare both-reviewers-unavailable case. |
| Static-image storage bills run high | Cost recording via `cost_recorder.record("fal", "image_gen", ...)` provides telemetry; budget envelope locked at implementation against marketing-audit's $220-425/run precedent. |
| Playwright + Chromium binary not installed in CI / on operator machines | U7b documents the install step (`playwright install chromium`); CI workflow file (`.github/workflows/test.yml`) adds the step before pytest. Operator onboarding doc names the prereq. site_render module fails loud with a clear "run `playwright install chromium`" message if the binary is missing. |
| site_engine SE-6/7 hand-grading time becomes operationally burdensome | U7c cut per Pass-5 YAGNI audit. Re-add trigger: operator-grading time >5 min/section OR ≥1 a11y regression in production. Document grading time in launch runbook; revisit at end of launch window. |
| site_engine scope creep — clients asking for full-page rewrites instead of section-level | TD-28 explicitly defers full-page composition to v1.5 with documented trigger condition (first client request AND ≥3 sections shipped across ≥2 clients). U15b's workflow rejects multi-section submissions pre-render with a clear error message naming TD-28. |
| site_engine brand_tokens drift — client updates brand mid-cycle, mid-cycle variants score against stale tokens | Per-client config snapshot at run-start (D7) applies to site_engine too. Mid-run drift fails loud at finalize-time. Brand-token edits should follow the same TD-5 CODEOWNERS pattern as reviewer-email edits — proposed for U15b client.yaml schema sign-off but not yet a hard ship-gate (operator discipline + audit log catches mistakes). |
| site_engine SE-8 anti-slop calibration drifts as 2026 generic-AI templates evolve | `docs/rubrics/site-quality.md` versioned (`version: v1`); quarterly review cadence to refresh Score-3 failure modes (e.g., the "lime + purple + dark gradient" anchor reflects 2025-AI-default palettes and will date). When v2 ships, scored variants retain attribution to v1 anchors via the `rubric_version` field in score payload. |
| site_engine cross-cycle learning manual in v1 | Reviewer signals (accept / edit / reject + edit deltas) feed back to rubric anchor calibration via a quarterly operator review (not automated). Automation rejected — meaningful only after ≥1 quarter of production data accumulates; revisit only if reviewer-signal volume justifies. |

## Documentation / Operational Notes

### Cache / freshness defaults per source (TD-39)

| Source | TTL | Refresh cadence | Notes |
|---|---|---|---|
| Foreplay ad-creative (live) | 24h | On-demand | Crowdsourced; coverage gaps for non-US-DTC verticals |
| Foreplay ad-creative (historical) | 7d | On-demand | Archive depth weak >3mo; freshness floor 90d in `signal_merger.py` |
| Adyntel ad-creative (live) | 24h | On-demand | Transparency-pull; 24-72h ingestion lag |
| Adyntel ad-creative (historical) | 7d | On-demand | |
| Meta Ad Library API | 12h | On-demand | Authoritative for EU advertisers; 200 calls/user-token/hour rate limit |
| SerpAPI SERP | 24h | On-demand | SerpAPI's own free cache is 1h; our 24h is for cross-run reuse. `--fresh` bypasses |
| GSC Search Analytics | 24h | Daily 06:00 UTC per client | GSC has 2-3 day intrinsic lag; pulling more often is waste |
| Findings briefs (marketing_audit) | 7d default `valid_until` | Per-brief operator override | D9 contract |
| Findings briefs (monitoring real-time) | 24h | Per-brief operator override | |
| Findings briefs (geo) | 14d | Per-brief operator override | Geo rarely changes hour-to-hour |
| Voice corpus checksum | Run-start snapshot; fail-loud on drift | N/A (D7) | Catches silent corruption |
| Brand tokens | Run-start snapshot; fail-loud on drift | N/A (D7) | |
| gofreddy.ai site_engine fixture | Repo-pinned (TD-30) | Manual operator refresh | Avoids live-fetch drift over build window |

Per-provider TTL constants land in `src/ads/signal_aggregator.py` (5 provider clients) + `src/briefs/reader.py` (brief reader). `--fresh` CLI flag bypasses provider-level cache for ad-hoc reruns.

### Locale handling (TD-33 generic-first)

Locale moves from Polish-hardcoded to per-client config (`ClientConfig.locale`). Defaults SaaS/AI-first (`gl=en/hl=en/google_domain=google.com/country=US/city="San Francisco,CA,US"/requires_diacritic_normalization=false`). Klinika + DWF override to Polish (`gl=pl/hl=pl/google_domain=google.pl/country=PL/city="Warsaw,Mazowieckie,Poland"/requires_diacritic_normalization=true`).

SerpAPI calls (in `signal_aggregator`) must always pass all three locale params (`gl`, `hl`, `google_domain`) — `gl` alone is insufficient per SerpAPI's documented gotcha. Polish-locale clients additionally set SerpAPI `location="Warsaw,Mazowieckie,Poland"` for client-specific competitive views (Polish Google heavily localizes to Warsaw geo). Diacritic-normalization (NFKD strip) is opt-in via `locale.requires_diacritic_normalization` flag; applies to GSC query grouping for Polish/German/Czech where Google folds variants but GSC reports user-typed form.

### GSC OAuth onboarding flow (TD-35)

**Shared OAuth client** = one gofreddy Google Cloud project + per-client refresh tokens stored encrypted, scoped to `client_id`. NOT per-client Cloud project.

**Per-client onboarding step** (operator-led, ~1-2 hours):
1. Client clicks "Connect Google Search Console" in gofreddy portal
2. Browser redirects to Google consent screen with scope `https://www.googleapis.com/auth/webmasters.readonly`, `access_type=offline`, `prompt=consent`
3. Client logs in with the Google account that already has Owner/Full User on their GSC property
4. Callback returns auth code → exchange for access token (1hr) + refresh token (long-lived). Persist encrypted, scoped to `client_id`
5. **If client doesn't have GSC at all** (common for small B2B SaaS, early-stage AI companies, aesthetic clinics, professional services): operator-assisted DNS verification step adds 1-2 hours; recommend Domain property over URL-prefix property

**Critical gotchas:**
- OAuth consent screen verification (2-6 weeks) — `webmasters.readonly` is a **sensitive scope**, requires Google review before exceeding 100 users. Submit at FIRST client onboarding, not later.
- Refresh tokens expire after **6 months unused** — run weekly cron refresh, not lazy refresh.
- "Testing" status = **7-day refresh tokens** — verification must complete BEFORE first production client.

### Per-archetype defaults reference table (TD-54)

Operator instantiates `clients/<slug>/client.yaml` by selecting an archetype and inheriting these defaults; per-client overrides on top.

| Archetype | Voice corpus | Brand assets | Default compliance | Reviewer pattern | SLA default | Source material | brand_strictness |
|---|---|---|---|---|---|---|---|
| `b2b_saas` (gofreddy canonical) | Public blog + LinkedIn + customer interviews | Figma design system → tokens.json | `gdpr_eu` (if EU-targeting) | Product-marketing-manager primary; design-lead secondary | `24h_business` | Blog archive + product docs + customer transcripts | `strict` |
| `b2c_aesthetics` (first-onboarded — Klinika) | Private corpus (consent-required); fallback degraded | Photography library + style guide | `medical_pl` (placeholder) + `gdpr_eu` | Clinic owner/doctor primary; clinic manager secondary | `48h_business_pl` | Procedure docs + patient education materials | `permissive` |
| `b2b_regulated` (first-onboarded — DWF) | Partner articles + research notes | Brand book | `legal_pl` (placeholder) + `gdpr_eu` | Partner primary; senior associate secondary | `72h_business` | Partner publications + regulatory primers + case-law summaries | `strict` |
| `b2b_tech` (U19 stub) | Stub | Stub | None | Stub | Stub | Stub | `strict` |

Per-client overrides on `client.yaml` displace archetype defaults; defaults apply when fields are unset.

### Per-client launch runbooks

- **Per-client launch runbooks** (U18 deliverable) walk operator through: voice corpus ingestion, brand asset collection, reviewer onboarding (email setup, SLA confirmation), GSC OAuth setup (per above), initial demo pipeline run, ≥5 artifact publication tracking. **site_engine onboarding steps include: capture target_url snapshot, author brand_tokens.json from client style guide, pick initial sections_in_scope subset, run first hero-section variant in dry-run mode and review.**
- **Concurrency operator playbook:** `MAX_PARALLEL_AGENTS` default 4. `fal_image` semaphore default 2 → dial up watching for fal.ai circuit-breaker trips. **`site_render` (Playwright Chromium subprocess) has its own 3-failure circuit breaker per U7b; no global semaphore added — section renders are fast (≤ 2.5s p95) and not concurrency-bottlenecked at v1 throughput.** Documented in `docs/architecture/concurrency.md` update.
- **Storage backend selection:** production `R2GenerationStorage` requires `GOFREDDY_R2_*` env vars + IAM credentials; dev/test use `LocalDevPreviewStorage` with `GOFREDDY_STORAGE_BACKEND=local`. **Site_engine section screenshots persist alongside other generated artifacts under the same R2/local backend selection — no separate storage layer.** Documented in deployment guide.
- **Onboarding doc** (auto-generated from R26 schema + this plan): step-by-step "how to add client N+1" guide. Add to `docs/onboarding/client-onboarding.md` at U19 completion. **Includes a site_engine section: how to author `brand_tokens.json`, how to pick `sections_in_scope`, how to set `codex_fallback` for regulated verticals.**
- **Audit log retention:** `review_audit/<client_slug>/<YYYY-MM>/audit.jsonl` retained indefinitely per compliance posture. Periodic archival to cold storage at implementation discretion.
- **Compliance rule-set versioning:** YAML files in `reviewer_assist/checklists/` are git-tracked. Version is the git commit SHA; legal sign-off recorded in `docs/plans/2026-05-13-002-<rule_set>-rule-set.md` companion docs.
- **Site quality rubric versioning:** `docs/rubrics/site-quality.md` carries a `version` field in its frontmatter. Material anchor changes bump the version; scored variants retain attribution to their original anchors via the `rubric_version` field in score payload (per the rubric file's "Revision policy" section). Quarterly review cadence to refresh Score-3 anti-slop failure modes as generic-AI templates evolve.
- **Playwright prereq:** new operator machines and CI runners need `playwright install chromium` (one-time, ~150MB Chromium download). Documented in the project README's "Onboarding" section after U7b lands. Failure to install is non-silent: site_render reports the missing binary clearly. (`@axe-core/cli` was a prereq for the original U7c audit utility; U7c was cut per Pass-5 YAGNI audit, so axe-core is not installed in v1.)
- **Rubric file ownership:** `docs/rubrics/site-quality.md` is consumed by the `site_engine` autoresearch lane via `RubricTemplate.prose_ref` resolution. Document owner is the autoresearch maintainer. Material anchor revisions bump the `version:` field per the file's own "Revision policy" section.

## Sources & References

- **Origin document:** [docs/brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md](../brainstorms/2026-05-12-content-engine-lanes-v1-requirements.md)
- **Sizing memo:** Inline at origin doc §"Dependencies / Assumptions" (sized 2026-05-13 — 3-5 months sequential / 8-14 weeks parallel)
- **Lane registry architecture:** `docs/architecture/lane-registry.md`
- **Concurrency architecture:** `docs/architecture/concurrency.md`
- **x_engine port master plan:** `docs/plans/2026-05-07-001-x-engine-autoresearch-port-master-plan.md`
- **x_engine rubric anchors precedent:** `docs/plans/2026-05-07-001-x-engine-rubric-anchors.md`
- **site_engine rubric anchors:** `docs/rubrics/site-quality.md` — SE-1..SE-8 prose, calibrated from 2026-05-13 gofreddy.ai landing-page session
- **Marketing audit master plan:** `docs/plans/2026-05-06-001-marketing-audit-v1-master-plan.md`
- **Stream A eval-fixes (env-gated):** `docs/plans/2026-05-11-002-eval-pipeline-bug-fixes-plan.md`
- **Stream C external absorptions:** `docs/plans/2026-05-11-003-external-absorptions-plan.md` (relevant for Plan B archive note)
- **Memory: linkedin_engine cold-start fix (2026-05-08):** `~/.claude/.../memory/project-linkedin-engine-cold-start-2026-05-08.md`
- **Memory: marketing audit shipping (2026-05-08):** `~/.claude/.../memory/project-marketing-audit-master-plan-2026-05-06.md`
- **Memory: landing page Q2-2026 shipped (2026-05-13):** `~/.claude/.../memory/project-landing-page-shipped-2026-05-13.md` — source of site_engine calibration data
- **External: Playwright** — https://playwright.dev/python (U7b dependency)
- ~~**External: axe-core CLI**~~ — cut for v1 along with U7c per Pass-5 YAGNI audit; SE-6/SE-7 hand-graded against U7b screenshot + console output.
- **External (TD-34 ad-intel providers):**
  - Adyntel API — https://www.adyntel.com/ ($44/mo Starter, 5K credits; Meta + LinkedIn + Google endpoints; bearer token auth)
  - Foreplay API — https://www.foreplay.co/api ($59-459/mo per tier; existing subscription; Meta/TikTok/LinkedIn ad library)
  - Meta Ad Library API — https://www.facebook.com/ads/library/api (free, EU-DSA-favored, 200 calls/user-token/hour, OAuth + ID verification)
- **External (TD-35 SERP + SEO providers):**
  - SerpAPI — https://serpapi.com/pricing ($25/mo Starter, 1K queries; gl/hl/google_domain locale params)
  - Google Search Console API — https://developers.google.com/webmaster-tools (free; OAuth 2.0 sensitive scope `webmasters.readonly`; 6-month refresh-token expiry; shared OAuth client architecture)
  - Alternatives at scale: Serper.dev ($0.30-1.00/1K), DataForSEO Standard ($0.60/1K) — switch trigger >5K queries/mo
- **CLAUDE.md** (project root) — 12-rule template
