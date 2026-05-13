---
date: 2026-05-12
topic: content-engine-lanes-v1
---

# Content Engine Lanes v1 — Generic Multi-Client Content Factory

## Problem Frame

We are building a marketing-agency content factory that produces high-volume, voice-consistent, compliance-checked artifacts across every channel a client buys. The first two clients onboarding are **Klinika Melitus** (Warsaw aesthetic dermatology, family-owned by Dr. Maria Noszczyk) and **DWF Poland** (international law firm, ~90 lawyers, recognized RES/energy practice), but the product is designed for any client we onboard — AI startups, e-commerce, SaaS, financial services, B2B tech, B2C brands, pharma, real estate. Onboarding a new client must be a config-and-corpus operation, not a code change.

Existing autoresearch lanes (`geo`, `competitive`, `monitoring`, `storyboard`, `marketing_audit`, `x_engine`, `linkedin_engine`) don't cover the highest-volume content channels most clients buy:

- **Short-form video on TikTok / IG Reels / IG Stories** — `storyboard` is currently anchored to long-form YouTube creators with narrative rubrics that punish educational content
- **Long-form articles** (blog SEO + LinkedIn Article) — no lane covers this, but it's the compounding asset for any content-marketing client
- **Static visuals** (IG single, IG carousels, IG story slides, LinkedIn document carousels, hero images, ad statics) — no lane covers static composition
- **Paid ad creative** for Meta + LinkedIn in v1 build (Google Ads supported by architecture, build deferred to v1.5 when a client demands it)
- **Cross-channel voice consistency** — the same persona needs to render coherently across video, article, social, and ads, but each engine handles voice independently today
- **Cross-lane orchestration** — `geo` finds article topics, `monitoring` flags regulatory events, but downstream content lanes can't consume those findings as briefs
- **Per-client configuration** — there's no clean onboarding interface; each new client today would require scattered code changes

No human shoots — all video is AI-generated via the existing fal.ai I2V pipeline. Compliance is a **two-gate design** (R22): an in-loop fitness judge with **pluggable rule sets per client** drives evolution toward compliance-clean output, and a mandatory human pre-publish review gates every client artifact before delivery. v1 ships two rule sets (`medical_pl`, `legal_pl`) because the first two clients need them; the architecture takes N rule sets so client #3 (e.g., `ftc_consumer_us` for a DTC e-commerce client, `sec_us` for finance, `pharma_pl` for pharma) onboards by adding a rule set, not by re-architecting.

## Architecture

```
                  ┌───────────────────────────────────────────────────┐
                  │     v1 UPSTREAM "what to write" (2 pairs)         │
                  │                                                   │
                  │   geo         → geo-findings.md (Klinika SEO)     │
                  │   monitoring  → monitoring-findings.md (DWF regs) │
                  │                                                   │
                  │   (marketing_audit + competitive briefs: v1.5)    │
                  └─────────────────────────┬─────────────────────────┘
                                            │ findings-brief (R21)
                                            ▼
                  ┌───────────────────────────────────────────────────┐
                  │                  article_engine                   │
                  │                                                   │
                  │  consumes briefs → canonical long-form draft →    │
                  │  per-platform adaptors (blog | linkedin_article)  │
                  │  (x_article adaptor: v1.5)                        │
                  │  Spawn-brief emission: v1.5                       │
                  └───────────────────────────────────────────────────┘

   ┌───────────────────────────┬─────────────────────┬──────────────────────┐
   │                           │                     │                      │
   ▼                           ▼                     ▼                      ▼
storyboard (ext)        image_engine          linkedin_engine          x_engine
short-form video        static composition    (existing,               (existing,
(IG Reels / TikTok /    ig_carousel +         voice-persona-           voice-persona-
 youtube_short / long)  li_doc_carousel +     migrated in v1)          migrated in v1)
+ Klinika non-clinical  hero_banner +
+ format_modes:         ad_static (NEW)
narrative,
educational,
brand_authority

                  ┌───────────────────────────────────────────────────┐
                  │                    ad_engine                      │
                  │                                                   │
                  │  emits 3–5 variants per format:                   │
                  │    Klinika: Meta Reels + Meta image / carousel    │
                  │    DWF:     LinkedIn Sponsored Content            │
                  │  Per variant: creative + LP hero copy             │
                  │  (Google / LinkedIn Document Ads / targeting +    │
                  │   bid + budget recommendations: v1.5)             │
                  │  Evolves against Foreplay (Meta/TikTok/LinkedIn)  │
                  │  + Adyntel / SerpAPI (Google) + GSC               │
                  └───────────────────────────────────────────────────┘

   ┌───────────────────────────────────────────────────────────────────┐
   │  SHARED INFRA (used by all content lanes; per-client configured)  │
   │                                                                   │
   │  • Per-client config (R26) — primary onboarding interface:        │
   │      { voice_persona_ref, compliance_rule_sets[],                 │
   │        enabled_channels[], content_denylist[],                    │
   │        pre_publish_reviewer + SLA, brand_assets }                 │
   │                                                                   │
   │  • Voice persona framework (R20) — 3 fields per persona:          │
   │    corpus_path, voice_rules, style_anchors                        │
   │    Consumed by: storyboard, article_engine, linkedin_engine,      │
   │    x_engine (existing lanes migrated in v1)                       │
   │                                                                   │
   │  • Findings-brief contract (R21) — minimum field set locked       │
   │                                                                   │
   │  • Two-gate compliance (R22):                                     │
   │    1. Pluggable in-loop fitness judge — N rule sets;              │
   │       v1 ships: medical_pl + legal_pl                             │
   │       Future: ftc_consumer_us, sec_us, pharma_pl, gdpr_eu,        │
   │              fair_housing_us, ai_claims, ...                      │
   │    2. Mandatory human pre-publish review                          │
   │                                                                   │
   │  • Content denylist (per-client) — replaces hardcoded             │
   │    per-client narrowing (e.g., Klinika denies clinical_visuals;   │
   │    luxury brand denies discount_framing; SaaS denies              │
   │    unverified_benchmarks)                                         │
   └───────────────────────────────────────────────────────────────────┘
```

All lane communication flows through findings-brief files. **The cross-lane brief contract is net-new infrastructure for v1**: the existing `findings_promotion` convention is intra-lane aggregation (per-fixture findings → "Global Findings: <Lane>" report inside that lane's archive) and does NOT pass briefs between lanes; monitoring's `digest-meta.json` is also lane-local. The new contract is inspired by these patterns but introduces actual cross-lane plumbing. Lanes stay independent — each evolves against its own rubric — but compose into pipelines by reading upstream findings.

## Requirements

**Storyboard lane extension**

- R1. The existing `storyboard` lane is extended with a `platform_target` parameter taking values: `youtube_long` (current default), `youtube_short`, `ig_reels`, `tiktok`, `ig_story`. Each value drives length brackets, pacing, hook timing, and default storyboard count (5 narrative, 10–15 short-form). Per-client `content_denylist` (from R26) gates which content types can be generated — Klinika's instance denies `clinical_visuals` and `before_after_imagery`, so v1 Klinika storyboards generate brand / lifestyle / educational content only; clinical procedure demos require real footage Klinika handles internally. The denylist mechanism applies generically: a luxury brand's instance might deny `discount_framing`; an AI startup's might deny `unverified_benchmarks` and `competitor_naming`; a pharma client's might deny `efficacy_implications`. Each client's denylist is enforced at variant generation and validated at the compliance gate.
- R2. The lane gains a `format_mode` parameter taking values: `narrative` (current), `educational`, `brand_authority`. `educational` relaxes SB-3 (earned emotional transitions) and SB-4 (recontextualizing turn) and adds an information-density check. `brand_authority` upweights SB-1 (creator authenticity) and SB-5 (performable voice script) and uses the shared voice persona corpus.
- R3. The lane accepts an optional voice-corpus input (via the shared voice persona abstraction in R20) so personas without rich video catalogs (Dr. Maria, DWF partners) can anchor SB-1 against their books / prior writing instead of needing a YouTube catalog.
- R4. Holdout fixtures are added for at least one Klinika-shaped short-form aesthetic creator (scored in `educational` mode per the Klinika demo) and one DWF-shaped LinkedIn legal creator (scored in `brand_authority` mode per the DWF demo). The existing `narrative` mode keeps its current fixtures. At least one fixture per `format_mode` must be sourced from real client prior content per the holdout-realism requirement in Success Criteria.

**article_engine (new lane)**

- R5. New lane `article_engine` registered in `autoresearch/lane_registry.py` produces long-form text articles. Inputs: topic, voice persona reference, voice corpus reference, source material, target platforms (csv subset of `blog | linkedin_article` — **x_article dropped from v1**, defer to v1.5), optional SEO keywords, optional upstream findings-brief path, length target (default ~1500 words, range 800–3500).
- R6. The lane runs as a **single parametrised workflow** — one session prompt with conditional per-platform adaptation sections — not separate scripts per platform. Same architectural pattern as the storyboard extension.
- R7. The lane generates one canonical platform-agnostic article body, then per-platform adaptors emit: blog markdown with SEO meta + schema.org/Article markup + image briefs (consumed by image_engine for hero/body images), and linkedin_article with first-200-char hook + LinkedIn paragraph rhythm + header image brief. (x_article adaptor deferred to v1.5 per scope cut.) **Note:** the canonical-then-adapt architecture is unverified — if blog and LinkedIn outputs require fundamentally different body structure, v1.5 may switch to platform-targeted drafts sharing inputs (topic, voice, sources) but not body text.
- R8. **Dropped from v1.** Derivative short-form spawn brief emission (article → LinkedIn posts / X threads / Reel scripts / IG carousels) deferred to v1.5. Since R24 made downstream consumption optional, emitting spawns with no required consumer would be dead infrastructure. Revisit in v1.5 with real client evidence of which derivatives pay off.
- R9. Rubric covers: hook strength, argument coherence, citation density + verifiability, voice fidelity, specificity, skimmability, SEO health (blog only), platform-adaptor compliance.
- R10. Holdout fixtures cover at least one Klinika procedure-page article and one DWF Polish-language regulatory explainer (e.g., KSeF 2026 or Polish Grid Act), each in the **two** target platform formats (blog + linkedin_article). At least one fixture must be sourced from real client prior content (Dr. Maria's books / Klinika site for Klinika; DWF published explainers for DWF) per the holdout-realism requirement in Success Criteria.

**image_engine (new lane)**

- R11. New lane `image_engine` registered in `autoresearch/lane_registry.py` produces static visual content end-to-end. Inputs: topic / message, brand style guide reference, reference imagery, format (`ig_single | ig_carousel | ig_story | li_doc_carousel | hero_banner | ad_static`), aspect ratios, slide count for carousels, optional findings-brief path. All six formats are in v1 build scope — `ig_single` is the most common static IG post type and is essentially free on top of `ig_carousel` (single is a 1-slide carousel); `ig_story` is universal for any IG-using client. Output gated by per-client `content_denylist` (R26).
- R12. The lane outputs **composed final images** — not just briefs. It calls fal.ai (or equivalent provider) via the existing `src/generation/fal_client.py` for image generation. **Static-image composition (text overlays, multi-slide carousel layout, brand stamping) is net-new infrastructure for v1** — existing `src/generation/composition.py` is an FFmpeg video pipeline (xfade, audio loudnorm, subtitle burn-in) and `caption_presets.py` defines ASS subtitle styles for video, not static-image overlays. A Pillow / Cairo / skia-based image composition module is required. Brief mode is not in v1 scope, but compose-mode quality must be validated against client brand standards before lane ship — see Resolve Before Planning.
- R13. The lane supports multi-slide carousel format with per-slide image prompt + text overlay + layout + alt-text + brand stamp, plus a hook slide that must pass a stop-scroll quality check.
- R14. Rubric covers: hook visual (first slide stop-scroll), brand consistency, info density / legibility, format compliance per platform, visual specificity, carousel arc, accessibility (alt-text), repurposability (one creative → multi-platform variants).
- R15. Holdout fixtures are organized by **client archetype** (B2B-regulated, B2B-tech, B2C-aesthetics, B2C-ecommerce, etc.). v1 instantiates two archetypes: B2C-aesthetics via Klinika (educational carousel, IG single brand post, IG story slide, hero image, ad static) and B2B-regulated via DWF (LinkedIn document carousel, hero image, ad static). Other archetypes (B2B-tech, B2C-ecommerce, etc.) are stub fixture slots filled when their first client onboards. At least one fixture per onboarded client must be sourced from real client prior content per the holdout-realism requirement in Success Criteria.

**ad_engine (new lane)**

- R16. New lane `ad_engine` registered in `autoresearch/lane_registry.py` produces multi-variant paid ad creative across Meta + Google + LinkedIn. Inputs: campaign goal (`awareness | consideration | conversion`), offer / topic, target audience description, brand voice persona, platform target, ad format per platform, optional competitor ad reference set (auto-populated via Foreplay/Adyntel for the client's domain).
- R17. Per campaign brief, the lane emits multi-variant creative (3–5 variants per format). **v1 build scope:** Meta Reels Ad scripts + Meta image / carousel ads + **LinkedIn Sponsored Content + LinkedIn Document Ads** (Document Ads share image_engine output with Sponsored Content — same effort, real winning B2B format). **Architecture supports but build deferred to v1.5:** Google RSA (15×4 headlines/descriptions) + Google display banners — add when first client (likely SaaS / AI / e-commerce) demands Google paid; the platform parameter exists in the lane spec from v1. **x_ads, tiktok_ads, reddit_ads** similarly: platform parameter supported, build deferred until client demand. Per variant: ad creative (copy + image-or-video brief) + landing-page hero copy matched to ad headline are **always emitted**. Audience targeting recommendation, bid strategy suggestion, daily budget recommendation are **optional outputs configured per-campaign** via a `full_bundle` flag — emitted when the client buys creative-only deliverable (running their own ads), suppressed when the client buys managed-ads service (we run them). Variant count reduced from 5–10 to 3–5 per format to keep judge-call cost bounded; per-campaign-brief cost estimate is required during planning (see Deferred to Planning).
- R18. The lane uses **existing data providers only** for its evolution signal in v1: Foreplay (competitor ad signal across Meta/TikTok/LinkedIn — verified in `src/competitive/providers/foreplay.py`), Adyntel + SerpAPI ads (competitor ad signal on **Google only** — both providers are Google-side per `src/competitive/providers/adyntel.py` and `src/audit/tools/serpapi_ads.py`; planning picks one as canonical), GSC (first-party SEO performance where applicable). First-party paid ad performance APIs (Meta Marketing API / Google Ads API / LinkedIn Marketing API for client ad accounts) are explicitly out of scope for v1 — see Scope Boundaries.
- R19. Rubric covers: hook strength, CTA clarity, offer specificity, platform-format compliance (character limits, image text-overlay ratios, healthcare-vertical word avoidance on Meta, LinkedIn copy rules — note: this is **platform policy**, distinct from R22 statutory compliance), variant diversity (3–5 ads should be 3–5 different bets, not 3–5 wordings of one bet), market-signal alignment (creative features correlated with competitor winners in Foreplay data; dimension dropped if the Foreplay-signal-reliability Resolve-Before-Planning item refutes the signal).

**Shared infrastructure**

- R20. A shared voice persona framework stores **three v1 sub-fields per persona**: `corpus_path` (pointer to ingested books / articles / prior writing for the persona), `voice_rules` (what to do / what to avoid, prose patterns), `style_anchors` (named voice anchors like `argumentative-medical-pedagogic` for article_engine vs `narrative-creator` for storyboard). Personas are referenced by name from any content lane. **v1 instantiations** for the first two clients: `dr_maria` (Klinika founder), `partner_jamka` (DWF partner), `brand_dwf`, `brand_klinika` — added as examples, not architectural commitments; every onboarded client defines their own persona names in their per-client config (R26). **v1 consumers (all 4 content lanes plus 2 existing lanes migrated):** storyboard (NEW: extended), article_engine (NEW), linkedin_engine (existing — migrated from per-lane voice reference in v1), x_engine (existing — migrated from per-lane voice reference in v1). Dropped from v1 (defer to v1.5): `allowed/disallowed_vocabulary`, `identity_facts` — no current consumer. The linkedin_engine + x_engine migration carries a backward-compat risk on those lanes' `readonly_subprefixes` constraints and structural assertions — mitigation deferred to planning.
- R21. A findings-brief contract defines the standardised format used by upstream lanes to emit work briefs that downstream content lanes consume. **Minimum field set locked in v1** (preventing 10-lane integration drift): `brief_id` (stable identifier), `source_lane` (emitter), `priority` (enum: high | medium | low), `topic` (short title + paragraph summary), `target_lanes` (list of consumer lanes), `target_formats` (per-consumer-lane format hint), `voice_persona_ref` (named persona, propagated downstream), `source_pointers` (list of corpus / research / regulatory source URIs or paths), `success_notes` (free-text guidance for the consumer). Field types, validation, and serialization format (JSON vs frontmatter+markdown) deferred to planning.
- R22. **Two-gate compliance design with pluggable rule sets:**
 1. **In-loop fitness judge** — compliance is a **pluggable framework** taking N rule sets. Each rule set is defined once (rule patterns, per-rule severity tier hard-block vs soft-warn) and activated per-client via R26 config. Compliance rubrics are **duplicated per-lane in v1** (each lane carries its own `<rule_set>_<lane>_*` rubric IDs in `LaneSpec.rubric_ids`) — uses the existing per-lane RUBRICS pattern; no new "cross-lane rubric" primitive in v1; no `assert len(RUBRICS) == N` invariant redesign. Heavier in line count, lighter in architectural risk. Extract to a cross-lane primitive in v1.5 once 4 lanes have proven the duplicated pattern.
 **v1 ships two rule sets** (the first two clients' needs): `medical_pl` (Polish medical advertising — Art. 14 *Ustawa o działalności leczniczej*: superlatives, prices, CTAs, encouragement-to-use; activated for Klinika) and `legal_pl` (Polish bar / radca advertising — solicitation, fee mentions, comparisons; activated for DWF). **Architecture supports adding without rewrite** — future rule sets likely include `ftc_consumer_us` (DTC e-commerce), `sec_us` (finance), `pharma_pl` / `pharma_us` (pharma — stricter than medical), `gdpr_eu` (EU data), `fair_housing_us` (real estate), `ai_claims` (AI startup capability claims), each shipped when a client demands it.
 Multiple rule sets can activate for one client (e.g., a Polish dermatology e-commerce store gets `medical_pl` + `ftc_consumer_us` + `gdpr_eu`).
 2. **Pre-publish human gate** — NO content with ANY compliance flag (severe OR borderline) ships to client without explicit human compliance sign-off. The fitness-judge's soft-warn path does not bypass this gate; it surfaces borderline issues for human review. Per-client reviewer + SLA defined in R26 config. **Compliance liability is the client's, not ours — the human gate is the load-bearing risk control.**

**Lane chain orchestration**

- R23. **v1 wires only 2 producer→consumer pairs end-to-end** (the demo edges): `geo → article_engine` (Klinika demo: SEO brief → procedure-page article) and `monitoring → article_engine` (DWF demo: regulatory event → sector explainer). `marketing_audit` and `competitive` brief-emission deferred to v1.5. `geo` and `monitoring` get a small additive extension to produce R21-compliant briefs alongside their existing artifacts; their core fitness functions are unchanged.
- R24. **Only `article_engine` consumes findings-briefs in v1** (from `geo` and `monitoring`). The other content lanes (`image_engine`, `ad_engine`, `storyboard`, `linkedin_engine`, `x_engine`) run standalone or from manual / hand-authored briefs in v1; their `briefs_path` parameter is reserved for v1.5 when the spawn brief pipeline (R8 / R25) lands and produces real upstream demand. Standalone operation (no upstream brief) is the default for every non-article lane in v1.
- R25. **Spawn brief pipeline deferred to v1.5** (R8 dropped from v1). In v1, downstream short-form lanes (`storyboard`, `image_engine`, `linkedin_engine`, `x_engine`) accept briefs from non-article sources (e.g., DWF KSeF deadline → LinkedIn post direct from monitoring brief, no article gate) and from manual / hand-authored briefs. article_engine is NOT a canonical thinking layer in v1 — it produces articles for direct client delivery, not as upstream input to other lanes. The "one research effort fans out to N artifacts" content-velocity pattern is a v1.5 capability with real client evidence informing the spawn-brief schema.

**Per-client onboarding**

- R26. **Per-client config object** is the product's primary onboarding interface. One config per onboarded client, capturing:
 - `voice_persona_ref` — pointer to the persona spec (R20) for this client (e.g., `dr_maria`, `partner_jamka`, `client_acme_founder`)
 - `compliance_rule_sets` — list of rule set names active for this client (e.g., `[medical_pl]`, `[legal_pl]`, `[ftc_consumer_us, gdpr_eu]`, `[sec_us]`); multiple rule sets can co-activate
 - `enabled_channels` — subset of `{storyboard, article_engine, image_engine, ad_engine, linkedin_engine, x_engine}`; the client pays for and runs only enabled channels
 - `enabled_platforms_per_channel` — per-channel platform allowlist (e.g., `storyboard: [ig_reels, tiktok]` for a B2C client; `[youtube_long, linkedin_video]` for a B2B client; `ad_engine: [meta]` for Klinika; `[linkedin, google]` for an SaaS client once Google ad build lands)
 - `content_denylist` — list of denied content types (e.g., `[clinical_visuals, before_after_imagery]` for Klinika; `[discount_framing]` for a luxury brand; `[unverified_benchmarks, competitor_naming]` for AI / SaaS clients; `[fee_mentions, comparisons]` for legal clients)
 - `pre_publish_reviewer` + `review_sla` — named human reviewer for the R22 gate-2 sign-off + target SLA
 - `brand_assets` — pointer to brand style guide, logo, palette, fonts, reference imagery
 - `archetype` — one of `{b2b_regulated, b2b_tech, b2c_aesthetics, b2c_ecommerce, ...}` — drives default fixture selection and rubric tuning
 
 **Onboarding a new client = filling out this config + ingesting voice corpus + (if needed) defining new compliance rule sets + naming a reviewer. No code changes required for clients sharing existing rule sets and channels.** v1 instantiates this config for Klinika (b2c_aesthetics archetype) and DWF (b2b_regulated archetype). Client #3 onboarding is the validation that the architecture actually delivers config-only onboarding.

## Success Criteria

v1 is **production-grade** — no demo-shortcuts. Every Success Criterion below must be met by output that's actually shippable to real clients on real channels, not by demo-fixture passes alone.

- **Holdout fixtures green per archetype:** each new lane (`article_engine`, `image_engine`, `ad_engine`) plus the extended `storyboard` lane passes its rubric on holdout fixtures organized by client archetype (R15). v1 must pass at least two archetypes (b2c_aesthetics via Klinika, b2b_regulated via DWF). **At least one fixture per onboarded-client archetype MUST be sourced from real client prior content** (books, published explainers, website articles, existing social posts); synthesized fixtures are supplementary. Prevents the closed evaluation loop where synthetic fixture + synthetic rubric + judge passes vacuously.
- **End-to-end demo per onboarded client, compliance-gated:**
 - Klinika walkthrough (b2c_aesthetics, `medical_pl` rule set, content denylist `[clinical_visuals, before_after_imagery]`): non-clinical short-form Reel + IG carousel + IG single brand post + procedure-page blog + Meta ad variants (3–5 variants) — flowing from a single geo-findings brief, all passing in-loop fitness judge AND human pre-publish gate.
 - DWF walkthrough (b2b_regulated, `legal_pl` rule set): partner-voiced video explainer + LinkedIn document carousel (KSeF timeline) + Polish-language sector article (partner byline) + LinkedIn Sponsored Content + LinkedIn Document Ad variants (3–5 variants each) — flowing from a single monitoring brief on the KSeF deadline, all passing in-loop fitness judge AND human pre-publish gate.
- **Per-client onboarding works config-only for client #3:** a third client (whichever archetype they fall into) can be onboarded purely by (a) filling out the R26 config object, (b) ingesting their voice corpus, (c) optionally adding a new compliance rule set, (d) naming a pre-publish reviewer — no code changes to lane internals, rubrics, or shared infra. **This is the architectural success bar that proves the generalization is real.** Demonstrated at v1 ship by running the full pipeline against a third archetype with synthetic / stub data (no real client #3 required for v1 ship).
- **Shared infra in use:** the same persona (e.g., `dr_maria`) is consumed unchanged by storyboard + article_engine + linkedin_engine + x_engine in its client's demo, demonstrating cross-lane voice consistency. The existing-lane migration (linkedin_engine + x_engine moved from per-lane voice references to the shared spec) must pass each lane's existing structural assertions and `readonly_subprefixes` constraints without regression.
- **Client-approved-and-published artifacts per onboarded client:** at least **5 pieces per onboarded client** approved by client decision-maker AND published to a real channel during the client's launch window. Forces the design to confront real-world failure modes (persona feels off, AI-gen uncanny, language wrong, brand voice misfires) that holdout fixtures don't surface. v1 measures this for Klinika + DWF; same bar applies to every future onboarded client.

## Scope Boundaries

The product is architecturally generic; the v1 *build* is scoped to what current clients need plus what's near-free to include for future clients. Boundaries below distinguish "v1 build" (what we ship in code) from "v1 architecture supports" (what the design accommodates with no code change).

**v1 build scope (what we ship)**

- **No human shoots.** All video output is AI-generated via the existing fal.ai I2V pipeline. We do not produce shot lists for real-camera shoots, recruit talent, or manage production.
- **No Google Ads variant generation in v1 build.** `ad_engine` platform parameter supports `google`, but the variant generator + rubric + fixtures for Google RSA / display banners are not built in v1. Build when first client (likely SaaS / AI / e-commerce) demands Google paid. Same holds for `x_ads`, `tiktok_ads`, `reddit_ads`.
- **No first-party platform Marketing API integration in v1.** Meta / Google / LinkedIn Marketing API for client ad accounts (i.e., ingesting our actual campaign CTR/CVR/CPA) deferred to v1.5. v1 evolution signal uses competitor-intelligence providers (Foreplay / Adyntel / SerpAPI ads) + GSC only.
- **No x_article adaptor in `article_engine`.** Genuinely niche audience (X Premium only). Defer to v1.5 if a client demands it.
- **No findings-brief integration beyond 2 demo pairs.** v1 wires `geo → article_engine` and `monitoring → article_engine` only. `marketing_audit → *` and `competitive → *` brief-emission deferred to v1.5. The shared contract (R21) is locked at minimum field set; full multi-lane integration crystallizes from real demand.
- **No article-engine spawn brief emission in v1.** R8 dropped; article_engine produces articles for direct client delivery only. Spawn brief pipeline (article → derivative short-form) deferred to v1.5 with schema informed by real client evidence.
- **No voice persona sub-fields beyond corpus_path / voice_rules / style_anchors.** `allowed/disallowed_vocabulary` and `identity_facts` deferred to v1.5 — no v1 consumer.
- **No cross-lane rubric primitive in v1.** Compliance rubrics duplicated per-lane in v1 using the existing `LaneSpec.rubric_ids` pattern. Cross-lane primitive extraction deferred to v1.5 once 4 lanes have proven the duplicated pattern.
- **No standalone longform / legal_alert / Chambers submission / personal_brand / shortform_video / reviews / CRO / deal_announcement lanes.** Subsumed: longform / legal_alert / Chambers prose collapses into `article_engine` outputs; personal_brand becomes the shared voice persona framework; shortform_video collapses into the `storyboard` extension; reviews / CRO / deal_announcement are not autoresearch-shaped (reviews is integration/ops, CRO is paid consulting, deal_announcement is subsumed by `article_engine` + optional downstream spawns).
- **No email / podcast / SMS / push-notification lanes in v1.** Add when a client demands.
- **No ad management ops automation.** v1 produces ad creative; campaign setup (Business Manager, pixels, conversion tracking), daily bid management, budget reconciliation, and performance reporting remain human ops. Ad management as a paid service is sold *on top* of `ad_engine`, not built into the lane.
- **No client billing / contract infrastructure** in this brainstorm. Out of scope.

**v1 architecture supports (no code change for future clients)**

- Onboarding a new client via R26 per-client config: voice persona + compliance rule sets + enabled channels + content denylist + reviewer + brand assets. Drop in, run, no code change required.
- N compliance rule sets, multiple rule sets active per client (e.g., `medical_pl` + `ftc_consumer_us` for a Polish dermatology DTC store).
- All platforms parameterized at the lane level (storyboard: 5 platform_targets; image_engine: 6 formats; ad_engine: platform parameter accepts meta / linkedin / google / x_ads / tiktok_ads / reddit_ads — though variant generators for google, x_ads, tiktok_ads, reddit_ads are not built in v1).
- Per-client content denylist mechanism (Klinika's `clinical_visuals` exclusion is one instance; arbitrary denied content types for future clients).
- Per-campaign `full_bundle` flag in `ad_engine` (creative-only deliverable vs creative + targeting + bid + budget for clients running their own ads).
- New client archetypes added to the holdout-fixture tree (b2b_tech, b2c_ecommerce, etc.) when their first client onboards.

## Key Decisions

- **Production-grade v1, no demo deadline (2026-05-13):** v1 ships production-quality output across all 4 lanes + shared infra. No demo-driven scope cuts. Realistic build window is 3–5 months sequential / 8–14 weeks with parallel workstreams. JR explicitly accepted the timeline rather than cut scope (ad_engine, image_engine compose mode, full platform coverage, pluggable compliance, per-client config all stay in v1).
- **No overengineering principle:** generalization is in (per-client config, pluggable compliance, voice persona framework, platform-parameterized lanes) — these add genuine value across the indefinite client roster. Speculative future features stay out (email/podcast/SMS lanes until a client demands; first-party Marketing APIs until client #3 needs them; cross-lane rubric primitive until 4 lanes prove the duplicate pattern; article spawn briefs until downstream consumption is demonstrated). The rule: if it adds value for the next 2–3 onboarded clients with reasonable confidence, include it; if it's defensive coding for hypothetical clients, defer it.
- **Generic multi-client architecture (R26):** Per-client config object is the product's primary onboarding interface. Onboarding new clients = filling out R26 config + ingesting voice corpus + (if needed) adding compliance rule sets + naming a reviewer. No code changes for clients reusing existing rule sets and channels. v1 instantiates 2 clients (Klinika b2c_aesthetics, DWF b2b_regulated); architecture supports indefinite clients.
- **Pluggable compliance with per-client rule set activation (R22):** In-loop fitness judge framework takes N rule sets. v1 ships 2 (`medical_pl`, `legal_pl`). Architecture supports adding rule sets without rewrite (e.g., `ftc_consumer_us` for DTC e-commerce, `sec_us` for finance, `pharma_pl` for pharma, `gdpr_eu`, `fair_housing_us`, `ai_claims`). Multiple rule sets can co-activate per client. Mandatory human pre-publish review gates every client artifact regardless of in-loop scoring. **Compliance liability is the client's, not ours — the human gate is the load-bearing risk control.**
- **No human shoots; per-client content denylist (R26):** All video AI-generated via fal.ai. Per-client `content_denylist` replaces hardcoded narrowing (Klinika's denies `clinical_visuals` and `before_after_imagery`; a luxury brand's might deny `discount_framing`; an AI startup's might deny `unverified_benchmarks`).
- **Single parametrised workflows over multi-script proliferation:** Both the storyboard extension and `article_engine` are single workflows parametrised by platform + format / persona, not separate scripts per platform. Same architectural pattern, half the maintenance.
- **All four lanes structurally, broad platform coverage by default:** storyboard supports 5 platform_targets (youtube_long, youtube_short, ig_reels, tiktok, ig_story) all in v1; image_engine supports 6 formats (ig_single, ig_carousel, ig_story, li_doc_carousel, hero_banner, ad_static) all in v1; article_engine ships blog + linkedin_article in v1 (x_article deferred — niche); ad_engine ships Meta (Reels + image/carousel) + LinkedIn (Sponsored Content + Document Ads) in v1, Google / x_ads / tiktok_ads / reddit_ads parameterized but variant generators built when first client demands.
- **ad_engine per-variant output — creative + LP copy by default, `full_bundle` flag for targeting + bid + budget:** Creative-only deliverable for clients we manage ads for; full bundle for clients running their own ads. Per-campaign config, not v1/v1.5 deferral.
- **Composed end-to-end image output (R12):** Use existing `src/generation/fal_client.py` for image generation. Note that `composition.py` + `caption_presets.py` are video-only (FFmpeg + ASS subtitles); static-image composition is net-new infrastructure in v1 (Pillow / Cairo / skia). Brief mode is not in v1 scope; clients without design teams must get ship-ready assets. Compose-mode acceptance validated by client sign-off on at least one Klinika sample (Resolve Before Planning).
- **Existing providers only for ad_engine perf loop (R18):** Foreplay (Meta/TikTok/LinkedIn) + Adyntel + SerpAPI ads (Google only) + GSC are already wired via `audit_provider_check.py`. First-party Marketing API integrations deferred to v1.5. Foreplay signal-reliability is a Resolve-Before-Planning item; if unreliable, ad_engine v1 drops to judge-only scoring and the "market-signal alignment" rubric dimension is removed.
- **Voice persona framework (R20):** 3 sub-fields per persona (corpus_path, voice_rules, style_anchors). Generic naming — `dr_maria` / `partner_jamka` are examples, not architectural commitments. Every onboarded client defines their own persona names in R26 config. linkedin_engine + x_engine migrate from per-lane voice references to the shared spec in v1 (JR override on v1.5-deferral recommendation); migration must pass each lane's `readonly_subprefixes` constraints and structural assertions.
- **Findings-brief contract specced + scoped (R21, R23, R24, R25):** Minimum field set locked in R21 to prevent interface drift. v1 wires 2 producer→consumer pairs (`geo → article_engine`, `monitoring → article_engine`). Other pairs deferred to v1.5. **article_engine is NOT a canonical thinking layer in v1** — it produces articles for direct client delivery. Spawn brief emission (R8) deferred to v1.5.
- **Compliance wiring — per-lane duplication (R22):** Each lane carries its own `<rule_set>_<lane>_*` rubric IDs. No new cross-lane rubric primitive; no `assert len(RUBRICS) == N` invariant redesign. Cross-lane primitive extraction deferred to v1.5.
- **Holdout fixtures organized by archetype (R15):** B2C-aesthetics, B2B-regulated instantiated in v1 via Klinika + DWF (real-content fixtures required). Other archetypes (B2B-tech, B2C-ecommerce, etc.) are empty fixture slots filled when their first client onboards. Architectural success bar: client #3 onboards config-only at v1 ship (validated against a third archetype with stub data).

## Dependencies / Assumptions

- **Existing fal.ai integration via `src/generation/fal_client.py` is production-stable** and handles both image generation (for `image_engine`) and image-to-video (for storyboard). Verified present; production stability assumed from existing storyboard usage.
- **Existing provider integration via `audit_provider_check.py`** covers Foreplay, Adyntel, SerpAPI ads, DataForSEO, GSC, PageSpeed, Cloro. Verified present in `src/competitive/providers/`, `src/seo/providers/`, `src/geo/providers/`, `src/audit/tools/`. `ad_engine` v1 perf loop assumes these are sufficient.
- **Dr. Maria's books and DWF partner prior writing are accessible in some machine-readable form.** Specific ingestion mechanism (PDF OCR, manual transcription, direct text) is deferred to planning. **Consent for corpus ingestion + AI-generated content under their byline is a pre-planning blocker** — see Resolve Before Planning.
- **No hard timeline pressure.** v1 is production-grade — every artifact ships to real clients on real channels, no demo-shortcuts. Sizing exercise (2026-05-13) confirmed realistic build is 3–5 months sequential, 8–14 weeks with aggressive parallel workstreams; JR accepted this timeline rather than cut scope. Build proceeds at the pace required to land production-quality output across all 4 lanes + shared infra; no demo-driven deadline forces partial features.

## Outstanding Questions

### Resolve Before Planning

- [Affects R3, R20, both Success Criteria demos][Needs verification] Confirm Dr. Maria and named DWF partner(s) consent to (a) corpus ingestion of their prior writing into a shared voice persona, and (b) AI-generated content publishing under their byline. Without this, R3 / R20 / both demos are not deliverable.
- [Affects R22, both Success Criteria demos][Needs verification] Identify named legal-review owner + budget for the Polish-language compliance pattern catalog (medical_pl Art. 14, legal_pl bar rules). Without legal sign-off, hard-block rules cannot ship; v1 may need to scope compliance judge to soft-warn-only with mandatory human-in-the-loop pre-publish review.
- [Affects R1, R12, Klinika demo][Needs verification] Produce one AI-generated short-form clip in the Klinika visual register AND one static image carousel in the Klinika brand register. Confirm both are Art. 14-acceptable AND brand-acceptable to Dr. Maria before locking "no human shoots" (R1) and "composed-only image output" (R12) as v1 decisions. Polish aesthetic-medicine clinical content has strict visual depiction rules that I2V output may not satisfy by default.
- [Affects R18][Needs research] Validate or refute Foreplay's "engagement" signal reliability as a fitness signal for ad creative evolution (1-day investigation). If unreliable, ad_engine v1 defaults to judge-only scoring and R19's "market-signal alignment" dimension is dropped.
- ~~[Affects all, Dependencies, Timeline assumption][Needs estimation] Per-lane LOC + commit + wall-time estimate~~ — **RESOLVED 2026-05-13.** Sizing memo confirmed realistic build is 3–5 months sequential / 8–14 weeks with parallel workstreams. JR accepted timeline rather than cut scope. Full v1 (all 4 lanes + shared infra) remains in scope.

### Deferred to Planning

- [Affects R21][Technical] Exact field schema for the findings-brief contract (id format, priority semantics, target-lane enum values, source-material pointer format). Spec minimum field set early to lock the interface before consumer lanes begin implementation.
- [Affects R20][Technical] Voice corpus ingestion mechanism — file format expectations, PDF OCR pipeline (Polish-language quality), persona-spec storage location and format, hot-reload semantics.
- [Affects R5–R10][Technical] `article_engine` workflow file layout (`workflows/article_engine.py` + session prompt template variables + structural gates for `articles/{platform}/{slug}.md`).
- [Affects R11–R15][Technical] `image_engine` workflow file layout. Production storage uses `R2GenerationStorage` (same as storyboard video previews), NOT `src/generation/local_dev_storage.py` (which is the dev shim). Downstream lane consumption needs durable R2 URIs, not file:// TMPDIR paths. Also: net-new static-image composition module (Pillow / Cairo / skia) per R12.
- [Affects R16–R19][Technical] `ad_engine` workflow file layout including per-platform variant-generation patterns, competitor-ad-reference auto-population from Foreplay, evolution signal aggregation from multiple provider sources. Add per-campaign-brief judge-call cost estimate (R17 variant count × R19 rubric dimensions × evolution generations).
- [Affects R1–R3][Technical] Storyboard extension implementation — env-var vs session-prompt template variables, fixture file layout per `(platform_target, format_mode)` combo, rubric reweighting via existing `custom_score` callable in `LaneSpec`.
- [Affects R22][Technical] Compliance judge rubric anchors — concrete trigger phrases / patterns per rule per severity tier. Boundary clarification: compliance judge = Polish **statutory** law (Art. 14, bar rules); ad_engine rubric R19 platform-policy = Meta / Google / LinkedIn **private** platform policy (healthcare-vertical word avoidance, LinkedIn copy/targeting limits). Two regimes, two enforcement paths.
- [Affects R5–R22][Technical] Atomic update of `src/evaluation/rubrics.py` (`assert len(RUBRICS) == 52`), `lane_registry.LaneSpec.rubric_ids` tuples, and the RUBRICS dict for every new lane. New IDs to enumerate: article_engine core (~8), image_engine core (~7), ad_engine core (~5 after R17 trim), plus **per-lane compliance duplication** per R22 (each of the 6 content lanes — article, image, ad, storyboard, linkedin, x — carries its own `medical_pl_*` + `legal_pl_*` IDs; estimate ~4–6 compliance rubric IDs per lane × 6 lanes ≈ 24–36 additional RUBRICS entries). Lockstep precedent: x_engine + linkedin_engine added X-1..X-6 + LI-1..LI-6 with count bumped 40 → 52.
- [Affects R23, R24][Technical] How existing lanes (`geo`, `monitoring`, `marketing_audit`, `competitive`) emit findings-briefs alongside their existing artifacts without disrupting their current fitness functions. Brief-consumption semantics: (a) what each consumer does if `briefs_path` set but brief is missing / empty / malformed; (b) whether briefs read from upstream's promoted-baseline archive or any candidate variant; (c) sync vs async coupling.

## Next Steps

**Brainstorm complete. Proceeding to `/ce:plan`.**

Sizing item (originally #5) resolved 2026-05-13 — timeline accepted. Four remaining real-world blockers are tracked as parallel-track tasks rather than planning blockers; engineering work can begin while they resolve:

1. **Partner consent** — talk to Dr. Maria + named DWF partner(s) about corpus + byline consent. Until this lands for a given client, that client's voice persona ingestion is held; other clients' work proceeds.
2. **Legal-review owner** — identify named legal reviewer + budget for the Polish-language compliance pattern catalogs (`medical_pl`, `legal_pl`). Until this lands, the compliance fitness judge ships with placeholder rules and the human pre-publish gate carries all the risk-control weight.
3. **AI-video Klinika validation spike** — produce one AI-generated Klinika clip + carousel; get Dr. Maria + Art. 14 reviewer sign-off. Until this lands, R1's non-clinical Klinika scope is honored as-is; if the spike fails, Klinika storyboard content stays in stylized/animated register only.
4. **Foreplay signal-reliability investigation** — 1-day analysis. Until this lands, ad_engine ships with judge-only scoring and R19's "market-signal alignment" dimension is a no-op; promoted to fitness signal if/when Foreplay validates.

All four are accepted as known risks per JR's "we'll debug anyway" posture; v1 build proceeds at full scope.

→ `/ce:plan` for structured implementation planning.
