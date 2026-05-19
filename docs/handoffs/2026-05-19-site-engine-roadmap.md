---
date: 2026-05-19
type: site_engine lane roadmap (extracted from judge-design v3 spec)
parent: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
scope: 3-phase deliverable list + modern-lever cuts/adds detail catalog + sibling-fork operational triggers
purpose: lane-program planning input for plan-002; NOT judge-design content
---

# Site Engine — Lane Roadmap (extracted from judge-design v3 spec)

This document holds the **lane-scope / program-roadmap material** extracted from `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` v3 per the 2026-05-19 spot-check finding ("two-jobs problem" — judge spec was carrying ~4,400 words of lane-roadmap material that warranted its own home).

The parent judge spec retains: (a) the SE-A..SE-E criterion prose and wrapper, (b) §1.5a Component A judge-artifact lock, (c) §1.5c shape-enforcement split, (d) §3c-d Component A failure modes, (e) §6b per-component Goodhart modes, (f) the modern-lever bias absorbed inline into score-1 anchors and §3 mediocre framing. **All content in this roadmap doc is lane-production / plan-002-input material, not judge criteria.**

Per the parent spec §1.5 Substrate-Readiness Gate clause: the 3-phase comprehensive site program described below is the COMPREHENSIVE workflow target. Phase 1 judge core (home + 2-3 primary landing pages) ships at substrate-current. Phase 2 + Phase 3 deliverables ship as substrate emission catches up — each requires its own workflow tooling. The site_engine lane itself has not been shipped to v006 (U15b unshipped per project memory) — even Phase 1 judging requires the lane scaffolding to land first.

---

## 1. 3-phase staged comprehensive site program — deliverable enumeration

The lane is **capable of producing** the following deliverables when engagement scope demands them. Not all engagements require all deliverables; substrate-readiness gates apply per deliverable. The 30/60/90 timing below is the SOTA-anchored comprehensive workflow target, NOT a hard delivery commitment against any specific client engagement.

### Phase 1 — Initial engagement (Days 0-30, ~10-12 deliverables, judge-tested core)

1. **Site audit (current-state across all dimensions)** — every URL crawled, every page categorized, every page scored against AEO + CRO + accessibility + performance + trust + freshness + entity-stability + crawled-by-AI status. Output: audit deck + scored heatmap + prioritized fix list.
2. **Information architecture recommendations** — sitemap + page-type taxonomy + URL structure + nav + footer + internal-linking strategy; persona-segmented entry paths AND passage-graph design for AI engines. Output: IA document + sitemap.xml + URL redirect map.
3. **Home page redesign (judge-tested Component A core)** — the artifact the parent spec's judge tests SE-A..SE-E on.
4. **2-3 primary landing pages (judge-tested Component A core)** — ICP / persona / campaign variants per the client's primary ICPs identified in positioning.
5. **Pricing page redesign** — tier transparency + comparison table + FAQ + named per-tier targeting (or services-firm rate-band / engagement-shape transparency).
6. **About / Team / Founders page** — named founder(s) with photos, named senior team with roles + bios, company-formation date and milestone narrative, named press / podcast / speaking appearances, investor names where applicable, named advisors where applicable, link-outs to founder LinkedIn + X + speaking-engagements + Substack / blog.
7. **First customer-story page** — named customer + outcome + dated context (per the v9 customer-story spec).
8. **Technical AEO infrastructure** — llms.txt at root + robots.txt with major-AI-engine user-agents in allow-list + sitemap.xml current and dated + Schema.org markup snippets per page-type (Organization on every page; Product on product pages; FAQPage where Q&A exists; BreadcrumbList on every non-home page; LocalBusiness / MedicalBusiness / LegalService / FinancialService where vertical applies; Article + Author on blog).
9. **Mobile UX recommendations** — mobile-first responsive design; primary CTA reachable within first viewport on mobile; touch targets ≥ 44px; click-to-call CTAs for services; App-Store badges for mobile-app products.
10. **Accessibility floor** — axe-core a11y check in CI on every PR; WCAG AA contrast on body, AAA on critical CTAs; semantic HTML; keyboard navigation; screen-reader markup; meaningful alt-text; form labels.
11. **Performance baseline** — Lighthouse FCP < 1.5s / CLS < 0.05 / TBT < 200ms / LCP < 2.5s / INP < 200ms; payload budget per page-type (home < 1.5MB; landing < 1MB; blog < 800KB); image optimization (WebP / AVIF / srcset); lazy loading; CDN; HTTP/3; preconnect / preload where load-bearing.
12. **Measurement layer setup** — GA4 + Plausible / PostHog + funnel definition + cohort comparison + dashboard live; page-level events captured (pageview + scroll-depth + CTA-click + form-submit + form-field-engagement).

### Phase 2 — Expansion (Days 31-60, ~12-15 cumulative deliverables, structural_gate validated)

13. **Comparison pages** — top 3 named competitors per the client's category ("X vs Y vs Z"; "alternative-to-X"; "best-of-category"). Per-named-competitor page; objective comparison table (feature, pricing, target user, integrations); honest acknowledgment of where competitor wins; named-customer-who-switched quote; category-aware CTA.
14. **Use-case pages (per ICP)** — outcome-led hero per job-to-be-done variant; before/after narrative; named-customer-with-outcome at top; walkthrough of the workflow; related-product internal linking; AEO-targeted Q&A in FAQ.
15. **Industry / vertical pages (per vertical served)** — vertical-specific named customer in viewport; vertical-specific regulatory or compliance context surfaced; vertical-specific use-case examples; vertical-specific CTA.
16. **Product / feature pages** — deep-link pages per product or major feature; in-viewport product surface (screenshot, video, interactive demo); specific capability claim with mechanism described; named customer using that specific feature; integrated FAQ; related-feature internal linking; schema.org Product markup.
17. **Customer / case-study / testimonial pages** — per-customer case study with named customer, named contact at customer (role + photo + LinkedIn), specific quantified outcome, dated context (when implemented, when measured), methodology of measurement, industry + size + use-case context, related-customer discovery; plus a customer-stories hub page that filters by vertical / use-case / size.
18. **Blog architecture (hub-and-spoke pillar)** — pillar hub per major topic-cluster, post-level pages with dated authorship + author bio + canonical entity name + Schema.org Article markup + internal linking to related pillars; weekly or biweekly publication cadence; named-author posts (not generic-brand authorship); 4 initial blog posts authored.
19. **Resource center / lead magnets** — ungated canonical resources (free templates, calculators, frameworks, checklists) for AEO citation share; gated high-value resources (whitepapers, benchmark reports, original research) for email capture; per-resource named author + date + outcome-led title; resource center skeleton + 2-3 initial resources.

### Phase 3 — Compounding (Days 61-90+, ongoing cadence, structural_gate validated + program-level outcomes)

20. **CRO test program (A/B framework, heatmap analysis)** — test backlog ranked by ICE (impact × confidence × effort); per-test hypothesis stated; per-test sample-size calculation; per-test ship-or-kill decision threshold; learnings repository accumulated; initial 2-3 tests running.
21. **Email capture + form optimization** — minimum-viable fields (email only for lead magnet; 3 fields for newsletter; 5 fields max for sales intake); progressive profiling; single-column layout; visible privacy statement; GDPR / CCPA-compliant; named-recipient where applicable; calendar alternative on sales forms.
22. **Live chat with human handoff** — conversational widget responsive (4-hour SLA at minimum; same-hour for high-intent); routes by intent (sales / support / partnerships); AI-first response for FAQ + human handoff for high-intent; surfaces named human responding once handoff completes.
23. **Cookie / privacy / GDPR / CCPA compliance** — cookie banner respecting consent; per-category cookie consent (necessary / analytics / marketing); cookie policy linked; privacy policy GDPR + CCPA + Polish RODO + applicable sectoral compliant; data-subject-access-request mechanism; data-portability mechanism; named DPO where required.
24. **Sticky CTA + scroll-aware CTA strategy** — one primary CTA per page (visually dominant, named-action verb); at most one secondary CTA (clearly demoted); scroll-aware CTA appearing after user passes hero + key sections; demo-direct (Cal.com / Calendly link in primary CTA path so high-intent buyers skip the form).
25. **Onboarding integration** — per-conversion-path follow-up (signup → onboarding email sequence; demo-request → calendar booking + prep email; form-submit → thank-you page with next-step CTA + resource list); analytics tracking through to product activation; named-human follow-up where applicable.
26. **Custom GPT / Claude Project integration** — where applicable for AI-native clients, surface a custom GPT or Claude Project as a product-discovery / support / sales-prep tool; AI-native engagement adds value with one more surface for prospect interaction.
27. **Knowledge Panel + Wikipedia + Wikidata strategy** — Wikipedia article exists (or strategy to earn one via notability); Wikidata entity created and maintained; LinkedIn company page populated; Crunchbase entry; Schema.org Organization declares canonical entity; consistent brand-name across all surfaces.
28. **Analytics measurement (ongoing)** — funnel measurement (home → product → pricing → demo → signup); cohort analysis (per-channel CVR comparison); revenue attribution where possible (e-commerce); privacy-respecting measurement (Plausible / PostHog over GA4 for privacy-first brands; GA4 + consent management for default); quarterly AEO citation audit (which AI engines cite which pages on which queries).

### Per-phase size envelopes (capability framing, not delivery commitment)

- **Days 0-30 (Phase 1):** ~10-12 deliverables; 6-8 distinct page surfaces shipped; foundational AEO + measurement + audit baseline; **Component A judge-tested (home + 2-3 landing pages on SE-A..SE-E)**.
- **Days 0-60 (Phases 1+2 cumulative):** ~22-27 cumulative deliverables; 12-18 page surfaces; comparison-page program launched (3 competitors); CRO test program initialization; **structural_gate validates Phase 2 deliverables** against the 8 verifiables routing list.
- **Days 0-90 (all 3 phases cumulative):** ~30-35 cumulative deliverables; 20-25 page surfaces; compounding-content cadence active; retainer transition complete; **structural_gate validates Phase 3 deliverables**; AEO citation audit + freshness audit + entity-stability audit on quarterly cadence.
- **Beyond 90:** ongoing 8-12 deliverables/month (comparison + customer-story + blog + freshness + CRO + AEO audit).

---

## 2. Modern-lever cuts — the 14 patterns the lane removes (detail catalog)

Per research §2 (companion `docs/research/2026-05-19-site-engine-comprehensive-scope.md`), the 2026 modern lever bias cuts 14 patterns aggressively. Each is named with the failure mode and the modern replacement that takes its place in the lane's deliverables. The judge spec retains inline brief mentions; the full catalog with named-replacement framing lives here.

1. **Logo-wall social-proof theatre.** "Trusted by thousands" + 8 logos in a row, no quotes, no outcomes, no links. Theatre to humans; no extractable claim for AI engines. Replaced by: named-customer + named outcome + named role + dated quote + link to case study.
2. **Vague benefit copy.** "Save time," "increase productivity," "drive growth." Digital Applied 2026 2,000-page study: vague benefit copy underperforms specific outcome copy by 4–8% CVR. Replaced by: named outcome with mechanism ("Cut review time from 90 minutes to 9; agent drafts first pass + human review every output").
3. **Generic SaaS template hero.** "All-in-one platform for modern teams." True of GitHub, GitLab, Linear, Shortcut, Jira, Atlassian, Vercel, Render, Fly. Zero positioning value. Replaced by: named category + named target + named differentiator.
4. **AI-slop landing-page pattern.** Lime-and-purple gradient mesh hero + three-icon trio at 33% width each + "AI-powered platform for modern teams" / "We help [target] [verb] [outcome]" hero + six identical bordered cards + stock testimonial grid with circular placeholder avatars. Both Pencil Pages and Marketing Examples treat this as the dead giveaway. Replaced by: client-specific visual identity, in-viewport product surface (or product photo for e-commerce), named-human voice somewhere on the page, warmth signals (photographic / illustrative evidence of named team).
5. **Classical-SEO keyword stuffing.** Body copy written for organic-rank keyword density. Digital Applied 2026: -8% CVR on "delve / leverage / synergize" usage. Parses worse for AI engines than declarative-document register (Volpini asymmetric-retriever argument). Replaced by: AEO-native passage-shaped content with declarative register + entity-grounding + evidence injection.
6. **Freshness stickers without substance.** "Last updated YYYY-MM-DD" stamp on stale body copy. SE-E score-0. Replaced by: substantive current-year body content + visible date as the corroborating signal.
7. **Generic CTAs.** "Get Started" / "Learn More" without context. Replaced by: category-appropriate verb-phrase ("Start free" / "Book demo" / "Open account" / "Shop Wool Runners" / "Speak to a partner" / "Read the docs" / "Get API key" / "Download").
8. **Hidden pricing.** "Contact us for pricing" across all tiers. Reads as evasion (Dunford positioning failure); no semantic-triple data for AI engines. Replaced by: tier transparency with at least one anchor price-point; per-tier feature comparison; FAQ on pricing logic; services-firm rate-band or engagement-shape transparency where regulatorily possible.
9. **Junk FAQ.** "Q: Is your platform secure? A: Yes, security is our top priority." Junk Q-A pairs filling the FAQ-section template. No AEO citation value; humans skip past. Replaced by: FAQ-shaped answers to real category queries (questions humans actually ask + AI-engines actually receive), authored as substantive 40-75-word passages with FAQPage schema.
10. **Faceless brand.** No founder named, no team named, no human voice. 2026 trust expectation includes named-founder visibility. Replaced by: founder named + linked + active on LinkedIn / X / podcast / Substack.
11. **Defensive silence on competitors.** "We don't compare ourselves to others." Cedes the comparison-query AEO surface to competitors who DO publish comparison pages. Replaced by: comparison-page warfare; honest acknowledgment of where competitor wins; objective comparison table.
12. **Contact-form-only paths.** No demo-direct, no calendar link. High-intent buyers want to talk within hours; 3-day SLA loses the deal. Replaced by: Cal.com / Calendly direct-booking link as primary CTA path option; form-submit-with-named-recipient + stated SLA as secondary.
13. **Stock-photo team pages.** Illustrated avatars with first-names-only. Zero credibility to humans; zero entity-grounding to AI engines. Replaced by: named-founder + photos + bios + role + LinkedIn + provenance.
14. **One home page for all paid channels.** No UTM-based variant routing; no per-channel measurement; Wynter / CXL data: per-channel variants lift CVR 30–60% vs generic. Replaced by: per-channel landing variants tied to channel-appropriate register + CTA framing.

These 14 cuts are removed at the lane level across all deliverables. The judge tests for the OUTCOMES that result from the removal (SE-A..SE-E catch the cut patterns on Component A); the cuts apply across the full deliverable program when scope demands them.

---

## 3. Modern levers added — the 15 net-new deliverables

Per research §3, beyond replacing the 14 cuts, the lane explicitly ADDS 15 modern levers as net-new deliverables when scope demands them.

1. **AEO-native architecture from the foundation.** Not retrofitted. Every page authored with dual-audience reading in mind. Declarative leads, passage-shaped sections, entity-stable naming, schema markup, llms.txt declaration, named third-party validation rendered on-page.
2. **Comparison-page warfare program.** Per-competitor pages with objective tables and honest acknowledgment of competitor wins. Single highest-leverage 2026 AEO surface in unregulated-vertical contexts.
3. **Demo-direct CTAs.** Cal.com / Calendly integration replacing contact-form-only paths. High-intent buyers book within minutes; sales pipeline accelerates.
4. **Founder visibility integration.** Named founder on home; LinkedIn + X + podcast appearance surface; founder-voiced about page; founder Substack / blog if exists. Per Cal.com / Plausible / Mercury / Cursor model.
5. **Named-customer-with-outcome program.** Per-customer case studies with named contact + dated outcome + measurable result. Replaces logo-wall. Drives both AEO citation AND human conversion.
6. **Per-vertical / per-ICP landing surface.** Persona-segmented landing pages (Anthropic For-developers vs For-enterprises pattern). Per-channel landing variants for paid acquisition.
7. **Pricing transparency.** Visible pricing with named tiers + per-tier targeting + comparison table + FAQ. Services: rate-band or engagement-shape transparency.
8. **llms.txt + Schema.org full coverage + robots.txt allow-list.** Discoverability for AI engines as first-class concern. Per Anthropic / Mintlify convention.
9. **Current-year cohort data + dated case studies + named-author blog cadence.** Substantive freshness that survives the SE-E "freshness reflects substantive current reality" test.
10. **Knowledge Panel + Wikipedia + Wikidata strategy.** Off-domain entity-grounding. Per Kalicube / Jason Barnard Entity SEO playbook. AI engines weight off-domain corroboration r=0.664 vs backlinks r=0.218 (Ahrefs 2026).
11. **CRO test program** — hypothesis-driven, statistical-significance discipline. Test backlog + ranking + sample sizing + learnings repository. Not button-color testing.
12. **Sticky / scroll-aware CTA strategy.** CTAs that follow the user without being intrusive. Scroll-aware visibility timing.
13. **Live chat with handoff.** AI-first triage + named-human handoff within hours. Modern chat that responds in seconds (AI) and routes to named human (sales / partnerships).
14. **Onboarding integration.** Post-conversion sequence: per-conversion-path follow-up; analytics tracking through to product activation; named-human follow-up where applicable. The website's job continues into the email sequence and product activation.
15. **Compounding cadence.** Monthly content cadence; quarterly entity-stability + AEO citation + freshness audits.

---

## 4. Sibling-fork operational triggers (reordered per 2026-05-19 spot-check)

The lane-scope broadening is **incremental sibling-fork-ready, not multi-artifact-judge-in-one-lane.** Per parent spec's research §6 (Option A: sibling-fork), the site_engine lane continues to iterate on Component A (landing-page artifact); sibling lanes handle other deliverables when demand crosses operational triggers. This preserves the design-guide ≤5 criterion ceiling per lane and the AND-conjunction discipline on Component A.

**Priority reordered 2026-05-19** to account for the gofreddy first-cohort vertical mix (2 of 3 active first-cohort clients — Klinika regulated-medical and DWF regulated-legal — fit poorly with comparison_engine; site_audit_engine generalizes across all 3 verticals).

### Sibling-fork trigger 1 — `site_audit_engine` (HIGHEST PRIORITY)

Site audit is the input to all other lanes (per research §8 OQ1 explicit recommendation), generalizes across all 10 verticals (regulated services need an audit too; healthcare needs an audit; B2B SaaS needs an audit), and the gofreddy first-cohort has obvious cross-vertical audit demand (Klinika and DWF both need site audits as the first deliverable; gofreddy itself fits the pattern).

**Trigger: fork `site_audit_engine` when audit-as-deliverable demand crosses ≥3 clients OR ≥15% of agency-side site_engine revenue.** Its judge would test outcomes: would a senior auditor recognize the deliverable as professional-grade; does the audit surface specific gaps with prioritized fix ranking; does the prescription cite the right modern levers per vertical.

### Sibling-fork trigger 2 — `comparison_engine` (SECOND PRIORITY)

Comparison-page warfare is the single highest-leverage 2026 AEO surface for unregulated-vertical contexts (per research §6 EL2). The fit is vertical-conditional: B2B SaaS / AI lab / agency / dev-tool unregulated contexts benefit; regulated verticals (medical advertising, legal marketing) constrain or prohibit comparison-page form.

**Trigger: fork `comparison_engine` when comparison-page demand crosses ≥3 clients in unregulated-vertical contexts (B2B SaaS / AI lab / agency / dev-tool) OR ≥15% of agency-side site_engine revenue.** Its judge would test outcomes: would a hostile competitor's CMO running a teardown call the comparison honest; would AI engines retrieve this page on "[client] vs [competitor]" queries; would a buyer in evaluation use this page to make their decision.

### Sibling-fork trigger 3 — `cro_test_program` (THIRD PRIORITY)

CRO test program may fork as `cro_test_program` if testing volume becomes load-bearing for the broader engagement (e.g., when a single client runs 5+ concurrent tests requiring hypothesis-driven sample-sizing + statistical-significance discipline + ICE-ranked backlog management + learnings-repository accumulation as a deliverable surface separable from the page production).

**Trigger: fork `cro_test_program` when CRO testing volume across the cohort exceeds the threshold where it can be embedded in the site_engine retainer.** Defer until at least one Phase-3 retainer is running CRO at sustained cadence.

### Sibling-fork trigger 4 — `site_landing_variants` (FOURTH PRIORITY)

Per-ICP landing-page variants (research §B2 + §G3) may fork as `site_landing_variants` if per-ICP / per-channel variant production scales beyond what Component A's 2-3 primary variants can support.

**Trigger: fork `site_landing_variants` when the cohort requires 5+ ICP variants per client or when per-channel paid-acquisition variants become a separable deliverable surface from the home + primary landing pages.** Defer until at least one client requires per-ICP / per-channel variant cadence beyond the Phase-1 2-3 variants.

### Other sibling-fork candidates — DEFERRED beyond first-cohort

From research §8 OQ1: `customer_story_engine` (foundational trust signal; may absorb into site_engine for now), `aeo_audit_engine` (may fold into GEO lane), `founder_visibility_engine` (research §8 OQ6 recommends cross-cutting infrastructure: one `FounderProfile` per client; consumed by site_engine + linkedin_engine + x_engine + article_engine), `entity_grounding` Knowledge-Panel-Wikipedia-Wikidata lane (research §8 OQ11 recommends fold into GEO or own lane).

---

## 5. Multi-deliverable evolution-loop architecture

The site_engine lane's evolution loop currently iterates on a single HTML landing-page artifact (Component A) and judges it with SE-A..SE-E (per parent spec). The lane-scope broadening adds 25+ deliverables across Phases 2-3 that are NOT judge-scored. Three architectural considerations carried from research §6:

- **EL1 — Single primary artifact + sibling lanes (Option A, RECOMMENDED).** The site_engine lane continues to iterate on Component A (judge: SE-A..SE-E); sibling lanes (`site_audit_engine`, `comparison_engine`, `cro_test_program`, `site_landing_variants` per triggers above) handle other deliverables. Each sibling lane has its own optimal-output spec + criteria. Phases 2-3 deliverables that have not yet sibling-forked are produced by site_engine as related outputs in the same engagement, validated by `structural_gate` deterministic conformance plus program-outcome telemetry.

- **EL3 — Per-page-type judge variants vs one site_engine judge (Path A sibling-fork RECOMMENDED).** The judge artifact is locked to Component A. If site_engine continues to deliver other page types (pricing, comparison, customer-story, about, blog) as a single lane without sibling-forking, the judge will eventually face fixtures from page types it wasn't designed for. Recommendation: sibling-fork per page type as triggers fire.

- **EL4 — Goodhart-resistance under multi-deliverable selection pressure.** If site_engine evolution is judged across 5 criteria (SE-A..SE-E) on Component A only, the workflow under 50-generation selection pressure converges on landing-page-template-fill (the Goodhart-collapse the v1 spec already defends against via outcome-questions + AND-conjunction + structural_gate routing). If the loop were judged across 30 deliverables in one lane, the workflow's Goodhart attack surface would multiply — every additional artifact + criterion is a slot the workflow can game. The defense is the same as v1: outcome-questions across every criterion + AND-conjunction across every dual-audience test + structural_gate routing for deterministic checks + per-criterion CoT + redundancy compression to live floor 3-4. **Adding lanes (sibling-fork per above) keeps each lane's criteria count low; growing one lane's criteria past 5 invites Goodhart.**

---

## 6. Cross-lane consistency enforcement

If `comparison_engine`, site_engine, and `customer_story_engine` (if it eventually sibling-forks) are sibling lanes serving the same client, they must enforce entity-stability across artifacts (canonical entity name; canonical positioning; canonical voice persona). Currently `ClientConfig.voice_persona` handles voice; what handles entity / positioning / canonical-customer-naming consistency across lanes?

**Decision required (plan-002 next iteration when first sibling-fork lands):** is `ClientConfig.entity_stability_anchor` a new infrastructure surface? Where do canonical claims live? Recommendation lean: cross-cutting `ClientConfig.entity_anchor` + canonical-claims registry; defer concrete design to plan-002 next iteration when first sibling-fork (`site_audit_engine` first per reorder above) lands.

---

## 7. Retainer-shape revenue model implications

The 30/60/90 → retainer transition (research §H1) implies gofreddy's revenue model includes ongoing retainer engagements, not one-shot rebuild deals. This is business-model commentary outside the lane's design scope but worth surfacing as a product question for plan-002 next iteration: how does the lane's deliverable cadence integrate with the retainer-shape pricing / packaging / sales surface?

Recommendation lean: lane produces deliverables; retainer-shape pricing is a separate business-design concern; the two interact at the SOW + measurement layer, not at the judge layer. **First-cohort retainer reality is unobserved as of 2026-05-19** — both Klinika and DWF are in plan-002 scope but neither has shipped a retainer engagement. The 30/60/90 cadence is SOTA-anchored from Stripe / Linear / Mercury / Anthropic exemplars, NOT first-cohort-validated. Phase 2-3 deliverable shipping is gated on (a) substrate readiness per parent spec's Substrate-Readiness Gate clause, AND (b) actual client engagement scope crossing the Phase-2 / Phase-3 surface.

---

**End of roadmap doc.** The parent judge spec (`docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` v3) holds the Component A judge design; this doc holds the lane-program roadmap that depends on substrate readiness + client engagement scope to actually ship.
