---
date: 2026-05-18
type: deep-research deliverable
status: complete
lane: site_engine
axis: CXL hero audit (the 5-second hero test, deepened)
parent_handoff: docs/handoffs/2026-05-18-judge-design-step1-site-engine.md
sibling_research: docs/research/2026-05-18-judges-domain-site-engine.md
guide: docs/rubrics/judge-design-guide.md
applies_to: SE-1 (human visitor commits to primary CTA) and the human-reader half of site_engine
scope: deepens the hero-section criterion specifically; deliberately stays off dual-audience, retirement, and vertical-overfit axes (covered by parallel dispatches)
---

# Site Engine — CXL Hero-Audit Deep Research

The handoff spec already carries a five-criterion rubric grounded in CXL / Dunford / Balfour / AEO. This deliverable deepens **one** axis: the hero section. Specifically, it asks what an excellent landing-page hero must accomplish in five seconds, what measurable signals distinguish strong from weak heroes in 2026, how those signals map to the SE-1 binary anchor, where the AI-generated convergence failure mode sits, and how SE-1 should behave across distinct page types (B2B SaaS, e-commerce, services, marketplace). The five SE-1..SE-5 criteria collectively cover dual audience; **SE-1 is the hero-section criterion** and is the focus here.

The deliverable conforms to the design guide: outcome questions over feature checks, binary anchors, reference-free, no framework names in proposed rubric prose, no anti-gaming clauses. Real-world heroes are named with URLs as **calibration anchors for the researcher**, not as model outputs the judge should pattern-match.

---

## TL;DR

The hero must accomplish four jobs in five seconds: (1) place the company in a category the reader recognizes, (2) name or unambiguously imply who it is for, (3) name a differentiator the reader can repeat to a colleague, (4) offer one primary action with low committed-cost. The CXL "five-second test" operationalizes this as: hide the page, show it for five seconds, ask the reader what the company does and who it is for; if they can't answer both, the hero failed. Marketing Examples teardown vocabulary names the recurring failure shapes: **throat-clearing** (hero talks about itself before answering "what is this"), **manifesto-lead** (brand narrative where declarative lead was needed), **feature dump** (capability list with no value), **logo-walled** (proof reduced to brand names), **claim inflation** (superlatives without backing). Dunford's frame adds a fifth-job test for B2B: the hero implies the **competitive alternative including "do nothing"**, not just named competitors.

Measurable signals that separate strong from weak heroes — drawn from CXL audits, Marketing Examples teardowns, Wynter user-testing data, and Profound/Yext AI-citation data: declarative register vs query-echo, concrete number vs hedged superlative, named customer with outcome vs logo wall, single visually-dominant CTA vs equal-weight CTA stack, persona named or unambiguously implied vs "for teams of all sizes." 2026 SOTA exemplars — Linear, Vercel, Stripe, Anthropic, Modal, Posthog, Cal.com — each clear the five-second test by different routes; none of them is a template.

The AI-generated-hero convergence failure is sharp and documented: every model defaults to **"We help [target] [verb] [outcome]"** ("We help engineering teams ship faster," "We help legal teams automate review"). This template passes feature-shaped criteria, fails the outcome test — the targeted reader cannot infer the differentiator and cannot quote one specific sentence to a peer. The judge must price this convergence as a Goodhart-collapse risk on SE-1, which is why the SE-1 score-1 anchor explicitly requires a **specific evidence element in the viewport** (named customer + outcome, dated stat, or founder name). Templated "X for Y because Z" without a viewport-evidence element gets 0, not 1.

For different page types, SE-1 stays a binary outcome test but the reader-decision shifts: B2B SaaS hero earns "book demo / start trial"; e-commerce hero earns "add to cart / view product"; services hero earns "book consult / view case studies"; marketplace hero earns "search / list / sign up." The hero criteria don't fork — the decision the reader commits to does.

---

## Key Questions Addressed

1. **What must a hero accomplish in 5 seconds?** (§1)
2. **What measurable signals separate strong from weak heroes?** (§2)
3. **2026 SOTA hero exemplars — named, with URLs and analysis** (§3)
4. **What's the "We help X do Y" convergence failure, and how does the judge defend against it?** (§4)
5. **How does SE-1 score across different page types — B2B SaaS, e-commerce, services, marketplace?** (§5)
6. **How does this fold into SE-1's binary anchor without inviting feature-checking?** (§6)
7. **Calibration set design for SE-1** — what fixtures and ground truth (§7)
8. **Open questions** (§8)

---

## §1 Synthesis: what the hero must accomplish in 5 seconds (~450 words)

CXL's five-second test (Peep Laja, operationalized in CXL teardowns and the CXL Institute conversion-research curriculum) asks: show a candidate hero for five seconds, hide it, ask the viewer two questions — **what does the company do**, and **who is it for**. If a representative target visitor cannot answer both, the hero has failed regardless of how it scores on any other dimension. The five-second window is not arbitrary: it tracks human attention budget on a cold web visit (Microsoft/Chartbeat scroll data 2024–2026 consistently shows median time-on-page below 15 seconds for paid traffic, with the first viewport carrying 60%+ of total reader attention).

Four jobs must happen inside that window. These are not a checklist — a hero that earns the score by passing four template slots is still a hero that has failed. These are the **outcomes** a strong hero produces in the reader's mind:

1. **Category placement.** The reader can name the category — "issue tracker," "code review," "billing infrastructure," "AI coding assistant," "headless CMS." If the reader has to invent a category ("some kind of AI platform thing?"), the hero failed. April Dunford's *Obviously Awesome* names this the "market category" element of positioning and treats it as load-bearing: every other element of the proposition is interpreted through the chosen category. A page that hides the category forces the reader to do positioning work the company should have done.
2. **Who-for clarity.** The reader can name the target audience — "modern software teams," "Series-A founders," "in-house legal at midsize firms," "indie iOS developers." This need not be a literal "for [persona]" sentence; it can be implied by the choice of category, the named customers visible in the viewport, the voice. The diagnostic is **who-it-is-NOT-for** — if the reader can't infer any group the page is excluding, the hero is averaging across all visitors.
3. **A differentiator the reader can repeat.** Not a brand-narrative line. One specific phrase, sentence, or number the reader could repeat to a colleague unprompted: "they're the one that gives every PR a preview environment," "they're the open-source Vercel," "they've got the 8-second checkout," "they're built on the legal-tech LLM that doesn't hallucinate citations." This is Harry Dry's repeated Marketing Examples principle: a hero earns its keep when **someone could rephrase it to a peer without looking at the page**.
4. **One primary action.** A single visually-dominant CTA the reader can take with a known cost — book demo (free, 30 min), start trial (free, sign up), view pricing (free, 0 seconds), browse products (free), request audit (free), view case studies (free). Visual dominance is established by contrast, position, color, and the absence of competing CTAs of equal weight. Wynter user-testing data: three CTAs of equal visual weight in the hero depress total CTA clicks by 20–35% versus a single primary with secondary clearly-secondary "View pricing" / "Sign in" weight.

These four jobs collapse to the SE-1 outcome question already in the handoff: **after ~10 seconds, would the targeted human persona click the primary CTA based on what's visible without scroll?**

---

## §2 Measurable signals — strong vs weak hero (~550 words)

The judge does not measure literal pixels, but it does scan for behavioral signals that correlate with strong heroes in CXL teardown corpora, Marketing Examples archives, and Wynter user-testing data. Eight signals recur:

**Signal 1: Register — declarative vs query-echo vs manifesto.**

- Strong: declarative-document register. "Linear is the modern issue tracker for high-performing software teams." "Stripe is a financial infrastructure platform for the internet." "Cal.com is the open-source scheduling infrastructure for everyone."
- Weak (query-echo): "What is X?" / "Why teams choose us." Hero reads as if the page is answering a SEO query, not introducing a product to a reader. AEO data (Profound 2025): query-echo headlines correlate negatively with AI citation versus declarative leads.
- Weak (manifesto): "We believe software should be simple." / "The world needs better X." Brand-narrative opener where a declarative lead was needed. Marketing Examples diagnostic: "throat-clearing" — the hero talks about itself before answering "what is this?"

**Signal 2: Specificity of language.**

- Strong: concrete nouns, verbs the reader can picture. "Issue tracker." "Preview environments." "Per-seat billing." "Inbox triage."
- Weak: abstract decorators. "Platform." "Solution." "Suite." "Infrastructure" used without qualifying noun. "AI-powered" used as the only differentiator.

**Signal 3: Concrete number or named entity in viewport.**

- Strong: at least one specific number, dated stat, or named customer visible without scroll. "Used by 8 of the top 10 cloud platforms." "149 lenses across 9 dimensions." "Live demo of 8-second checkout." "Built by the team behind X."
- Weak: zero specifics in viewport, all specifics deferred to below-fold.

**Signal 4: Named outcome (what the reader actually gets).**

- Strong: an outcome the reader can picture happening to them. "Ship features in days, not weeks." "Cut review time from 90 minutes to 9." "Send your first invoice in 4 minutes."
- Weak: vague benefit ("save time," "increase productivity," "drive growth"). "Save time" benchmarks below the median CTR in 7 of 7 Marketing Examples teardowns reviewing 2024–2025 SaaS heroes.

**Signal 5: Proof element with context.**

- Strong: a named customer with one specific outcome ("Ramp shipped 12 features per week after switching") OR an industry-recognized credibility marker with context ("YC W21," "Built by ex-Stripe engineers"). Animalz's distillation: the proof that converts says *what was tried before, why it failed, what changed, and what the result was*.
- Weak: logo wall with no context. Unattributed quote ("This product changed our team!" — no name). Generic "trusted by leading companies."

**Signal 6: Social proof above the fold.**

- Strong: at least one customer name, quote, review snippet, or external validation in the hero viewport. Pencil Pages: "social proof above the fold" appears in 28 of 34 audited high-converting heroes (2024–2025 corpus).
- Weak: social proof entirely below fold. Reader has to commit attention before earning any reason to trust.

**Signal 7: Single visually-dominant CTA.**

- Strong: one CTA in a contrasting color, larger size, prime position, with a low-cost action verb ("Start free," "Book demo," "Try it"). Secondary actions clearly demoted ("View pricing" / "Watch demo" as text links or low-contrast buttons).
- Weak: three CTAs of equal visual weight ("Sign up" / "Talk to sales" / "View demo" all same size, same color). Wynter user-testing: this depresses primary CTA clicks 20–35%.

**Signal 8: Visual product surface.**

- Strong: the hero shows the product. Linear shows the issue tracker. Stripe shows the dashboard. Vercel shows the deployment surface. Cursor shows the editor. The reader sees what they'll use.
- Weak: hero is illustration-only or abstract-graphic-only. The reader cannot picture the product. Particularly common in AI-tool launches where the hero is a gradient mesh + three-icon trio. Marketing Examples 2025 corpus: 60%+ of "AI-powered platform" heroes show no product surface.

Note on what is **not** a hero signal: page-load speed (structural), schema markup (structural), CSS contrast ratio (structural a11y), exact word count (structural length-band). These are routed to `structural_gate` per the design guide §2.

---

## §3 2026 SOTA hero exemplars (~600 words)

Seven exemplars worth the judge's calibration. Named with URLs. **These are calibration anchors for the human researcher, not pattern-match targets for the judge** — per design guide §7 reference-free, any score-1 anchor with a concrete example must carry "do not optimize toward this." The exemplars are diverse enough that no template emerges from the set.

**Linear (https://linear.app)** — the canonical 2026 SaaS hero. Hero reads: "Linear is a purpose-built tool for planning and building products." Single visible CTA: "Start building." Named customer logos directly below (OpenAI, Ramp, Vercel, Cash App, Scale, Mercury). Visible product surface (issue tracker UI) renders in a contained frame. Five-second test passes: category = "tool for planning and building products"; who-for = product teams (implied by named customers); differentiator = "purpose-built" + visible UI craft; primary action = "Start building." What it does well: the hero refuses to inflate. There is no "10× faster" or "AI-powered." The differentiator is craft, demonstrated through the product surface in viewport.

**Vercel (https://vercel.com)** — developer-platform hero done declaratively. Hero reads (rotates): "Build and deploy on the AI Cloud." Below: "Vercel provides the developer tools and cloud infrastructure to build, scale, and secure a faster, more personalized web." Single primary CTA: "Start Deploying" with a clearly-secondary "Get a Demo." Named customer carousel (Under Armour, eBay, Sonos, Adobe, Notion, Stripe) directly below. What it does well: passage self-containment. The first 100 words of the page is itself a quotable AI-citation passage — answers "what is Vercel" in declarative document register with a named-customer evidence band.

**Stripe (https://stripe.com)** — the financial-infrastructure category-definer. Hero reads: "Financial infrastructure to grow your revenue." Single CTA: "Start now." Named customer line below: "Millions of companies of all sizes use Stripe online and in person to accept payments, send payouts, automate financial processes, and grow their revenue." The hero shows a product surface (dashboard mockup). What it does well: category placement is unambiguous ("financial infrastructure"), the proof shape ("millions of companies") is hedged but immediately concretized by named-customer logos below. Stripe's hero has been remarkably stable across years — a calibration anchor for durability.

**Anthropic (https://anthropic.com)** — persona-separated landing surfaces. The main page makes the safety-research position visible above the fold. Sub-surfaces ("For developers," "For enterprises," "For consumers") are explicit and don't average across each other. What it does well: Dunford's persona-commitment test passes — Anthropic does not pretend to be one thing to everyone. The /api page reads for developers; the /enterprise page reads for enterprise buyers.

**Modal (https://modal.com)** — concrete-number hero. Hero reads "High-performance AI infrastructure." Within the hero viewport: a code sample showing `@modal.function()` decorators. Specific signals: "Sub-second container starts" stated as a concrete capability. What it does well: it shows a code sample as the visual proof. Developers see the product surface (code) before scrolling.

**PostHog (https://posthog.com)** — feature-density done well. Hero reads "How developers build successful products." Below: a stack of product surfaces (analytics dashboard, session replay, feature flags). The hero risks "feature dump" failure but escapes it by naming a clear who-for ("developers") and the *what they're trying to do* ("build successful products"). What it does well: the named-customer carousel below the hero ("Trusted by 47,000+ companies") is paired with specific brand names. PostHog reads as a calibration data point for "more is more, done with craft."

**Cal.com (https://cal.com)** — open-source positioning. Hero reads "Scheduling infrastructure for everyone." Differentiator: "open source" is one of the first visible phrases. Named customers visible. Single CTA: "Get Started." What it does well: the open-source positioning is the differentiator and it appears in the first three lines of body copy. The Dunford competitive-alternative test passes — the implicit alternative is Calendly, and "open source" is the explicit dimension of difference.

**Diversity check across the seven.** Different categories (dev tools, payments, AI safety, scheduling, analytics, infra), different who-fors (engineering teams, founders, enterprise, developers), different proof shapes (named-customer logo wall, dashboard mockup, code sample, persona-separated surface). No template emerges. The judge calibrated on these seven cannot pattern-match — it must reason about outcomes.

**Anti-exemplar (deliberately included).** A representative AI-generated landing page hero, 2024–2026 vintage: "We help [target] [verb] [outcome] with AI." Lime-purple gradient mesh. Three-icon trio at 33% width. Logo wall with circular placeholder avatars below. Two CTAs of equal weight ("Get Started" / "Book Demo"). No product surface visible. No named customer with context. No specific number. Five-second test fails: reader can name "AI tool" but not category, cannot name who-for, cannot name differentiator. This is the convergence target the judge must price.

---

## §4 The "We help X do Y" convergence failure (~350 words)

AI-generated landing-page heroes converge sharply to the template **"We help [target] [verb] [outcome]"** — sometimes prefixed "Built for," "Trusted by," "The platform for." Examples that recur across model outputs (Claude, GPT-4/5, Gemini) when asked to draft landing copy:

- "We help engineering teams ship faster."
- "We help legal teams automate document review."
- "The platform for modern marketing teams."
- "Built for founders who want to focus on building."
- "Trusted by ambitious B2B companies."

The convergence is structural, not stylistic. The template passes a feature-shaped check ("Does the hero state who it's for and what it does?") with a yes — but it fails the outcome test in three named ways:

**Failure 1: The reader cannot name a differentiator.** "We help engineering teams ship faster" is true of GitHub, GitLab, Linear, Shortcut, Jira, Atlassian, Vercel, Render, Fly, Coolify, and approximately every developer tool. The reader cannot infer the named alternative (Dunford's competitive-alternative test fails) and cannot quote one specific sentence to a peer (Marketing Examples test fails).

**Failure 2: The hero has no in-viewport evidence element.** The template fits in the hero block with no room for a named customer, a concrete number, or a visible product surface. Templates are dense — they fill the viewport with positioning and leave no room for proof.

**Failure 3: The hero invites template stacking.** Pages with "We help X do Y" hero almost always have a "Features," "How it works," "Pricing," "FAQ" structure beneath that is equally templatized. The whole page reads like a Notion template rather than a real product surface.

**Defense in SE-1.** The handoff's SE-1 score-1 anchor already requires "at least one specific evidence element in the viewport (named customer + outcome, dated stat, founder name)." This is the load-bearing structural defense against the convergence failure. The "We help X do Y" template passes the persona-stated and category-stated tests but fails the evidence-element-in-viewport test. Score 0.

**Why this matters under selection pressure.** Per design guide §11, the judge IS the selection signal. If SE-1 rewarded "states what the page does + states who it's for," the workflow would generate exactly the convergence template every time. The evidence-element-in-viewport requirement is the structural feature that keeps SE-1 outcome-shaped rather than feature-shaped. Without it, SE-1 becomes a feature checklist and the Phase 4 rollback pathology repeats.

---

## §5 SE-1 across different page types (~400 words)

The handoff treats site_engine as broad (full-site surface, dual audience). The hero criterion SE-1 must work for several page types. Five page types appear in plausible fixtures: B2B SaaS landing, e-commerce product page, services landing (agencies, consultancies, freelance), marketplace landing (two-sided platforms), and content/media landing (publications, newsletters).

**B2B SaaS landing** — the default. SE-1 as currently written fits cleanly. Primary CTA is "book demo" / "start trial" / "view pricing." Strong: Linear, Vercel, Stripe, Modal. The five-second test asks for category + who-for + differentiator + action. Score 1 requires viewport evidence (named customer / dated stat / founder name).

**E-commerce product page** — the hero is the product image + product name + price + add-to-cart. Primary CTA is "Add to cart." Category is the product category. Who-for is implied by the product. Differentiator is implied by the product detail (material, sizing, dimensions, reviews-with-count). Evidence is the product photography (substitute for "product surface") plus reviews-count-and-rating. Score 1 requires: product visible in viewport + price visible + reviews count or rating visible + single primary CTA dominant. Score 0: hero opens with a brand-narrative video, the product is below fold, price is hidden, multiple CTAs ("Buy now" + "Add to wishlist" + "Compare" all same weight).

**Services landing** (agency, law firm, consultancy) — the hero answers "what service" + "for whom" + "credibility." Primary CTA is "book consult" / "view case studies" / "request proposal." Differentiator is often the founder name, the specific named client list, or the specific named outcome from a case study. Evidence-in-viewport: founder name OR named client with context OR named case-study outcome. Score 0: generic agency copy ("We're a strategy and design partner for forward-thinking brands"), no named clients in viewport, hero opens with a manifesto reel.

**Marketplace landing** (two-sided platforms — Airbnb, Etsy, Uber-class). The hero must commit to **one side** of the marketplace first (host/guest, buyer/seller, rider/driver). Single CTA reflects that side's primary action (Airbnb: "Search destinations" for guests; "Become a host" link visible but clearly secondary). Score 1 requires: which side the hero serves is unambiguous + the primary action for that side is single-dominant + at least one specific number or named entity in viewport (count of listings, count of cities, named partner). Score 0: hero averages across both sides ("Connect with great X"), CTA stack ("Buy" / "Sell" / "Browse" same weight), no concrete numbers.

**Content/media landing** (newsletter, publication, podcast). Hero answers "what content" + "by whom" + "for whom" + "how often." Primary CTA is "subscribe" / "read latest" / "browse archive." Evidence is named author + named topics + recent dated piece. Score 1: hero shows recent dated content + author name + subscriber count or "as featured in" credibility marker + single subscribe CTA. Score 0: hero is brand-narrative ("Smart writing for smart people"), no named author, no recent dated content visible, multiple CTAs.

**Across all five page types, SE-1's binary anchor structure doesn't fork.** What changes is the *operationalization* of the four jobs (category, who-for, differentiator, action) and the *operationalization* of "specific evidence element in viewport." The CoT step 2 in the handoff (walk visible hero block, identify which of {value prop, category placement, differentiator, evidence element} are present) naturally accommodates each page type — the elements are the same; their realization differs.

---

## §6 Folding into SE-1's binary anchor without inviting feature-checking (~250 words)

The risk in deepening SE-1 is that the deepening becomes a checklist. "Did the hero pass the five-second test?" + "Did it have signal 1?" + "Did it have signal 2?" + ... is exactly the feature-shaped pathology that drove the Phase 4 rollback at `c76f051`. The defense is to keep the criterion **outcome-shaped** — the four jobs and eight signals are the **judge's reasoning toolkit**, not enumerated requirements in rubric prose.

The handoff's current SE-1 prose stays intact. The deepening lives in:

1. **The CoT Step 2** — already present: "Walk the visible hero block, identify which of {value proposition, category placement, differentiator, evidence element} are present." The four jobs from §1 map here.
2. **The CoT Step 3** — already present: "Emit verdict + one-sentence justification." The judge commits based on the four jobs holistically; it does not tally.
3. **The score-1 anchor's "at least one specific evidence element in the viewport"** — already present: this is the load-bearing structural defense against the "We help X do Y" convergence failure (§4).
4. **The hedged example** — current example is Linear; should rotate across generations to avoid the workflow learning Linear specifically. Suggest rotation: Linear → Stripe → Cal.com → Vercel → Modal across 5 generations. Hedging stays "do not optimize toward this."

**What NOT to do.** Do not enumerate the eight signals in the rubric prose. Do not list the five page types and their decisions. The judge needs to reason about the reader; the four jobs and eight signals live in this research doc and in the calibration set, not in the rubric.

---

## §7 Calibration set design for SE-1 (~250 words)

Per design guide §15, a calibration set of ~100 fixtures per lane is the production-ready floor. SE-1 specifically needs fixtures that stratify across:

1. **Page type** (5 types from §5): ~20 fixtures per type for 100 total.
2. **Quality level** (3 levels per type): strong / mediocre / weak. ~6–7 per quality level per type.
3. **Failure mode** (8 from the parent domain research): each major failure mode represented at least 3× in the score-0 cohort.

**Concrete fixture sources.**

- **Strong score-1 fixtures.** Real heroes from §3: Linear, Vercel, Stripe, Anthropic, Modal, Posthog, Cal.com. Plus additional category-leaders: Shopify, Notion, Figma, Sentry, Datadog, Cloudflare, Mercury, Brex, Ramp, Pulley.
- **Mediocre score-0 fixtures.** Recent-vintage AI-tool launches that exhibit the "We help X do Y" convergence. Scrape from Y Combinator launches, Product Hunt top-10s, and the lower-quartile of B2B SaaS landing pages indexed by Wynter and Marketing Examples teardowns.
- **Weak score-0 fixtures.** AI-generated landing pages — fixtures synthesized by asking Claude/GPT/Gemini to produce a landing page given only a one-line product description. These will reliably converge to the gradient-mesh + three-icon-trio + "We help X" failure shape and serve as anchor score-0 examples.
- **0.5 unknown fixtures.** Section-only renders where CTA / above-fold context cannot be inferred. ~5–10 fixtures.

**JR labeling.** Binary score per fixture. One-sentence rationale per score, naming which of the four jobs failed (or all passed). Stratification across types + quality + failure mode.

**Weekly probe.** Per design guide §15, run the 100-fixture calibration set through the panel weekly; alarm if SE-1's rolling mean drops 2–5% from baseline.

---

## §8 Recommendations

1. **Keep SE-1 prose as drafted in the handoff.** The deepening from this research feeds the CoT Step 2 implicitly and the calibration set explicitly. Do not enumerate the eight signals or four jobs in rubric prose — that turns SE-1 into a checklist and re-introduces the Phase 4 feature-checking pathology.

2. **Rotate the hedged example across generations.** Linear → Stripe → Cal.com → Vercel → Modal across the first 5 generations. Same hedging: "do not optimize toward this." Rationale: rotation reduces the workflow's ability to overfit to one anchor example. (Design guide §8 prescribes panel-model rotation; this is the same pattern applied to example anchors.)

3. **Treat the "We help X do Y" convergence as the primary Goodhart attack on SE-1.** Track its prevalence in score-1 outputs across generations. If the workflow's score-1 outputs trend toward this template, it's a leading indicator of feature-shaping drift even if mean scores look stable. Variance instrumentation per design guide §11.5 catches this lagging; convergence-template prevalence catches it leading.

4. **Build the SE-1 calibration set with stratification across the five page types from §5.** Not just B2B SaaS. The handoff's site_engine fixtures may include e-commerce, services, marketplace, content — the calibration set should cover all five to keep SE-1 from overfitting to B2B SaaS conventions.

5. **The eight signals from §2 belong in the operator-facing scoring guide (this research doc + the handoff), not the rubric.** When the judge produces a score-0 verdict, its one-sentence justification will naturally pick from the eight signals ("hero opens with manifesto," "no specific evidence element in viewport") — but the judge should not be reading "did the hero pass signal 6?" The reasoning is implicit; the criterion is outcome-shaped.

6. **Reconfirm SE-1 vs SE-4 (persona commitment) redundancy after calibration.** The handoff's §9 open question 4 notes potential SE-1/SE-4 correlation. This research deepens SE-1 specifically; SE-4 is about full-page persona commitment, not hero-section commitment. Empirical correlation across the 100-fixture set will confirm whether the criteria are independent in practice.

7. **Resist verticalization.** The handoff was caught earlier in the session on the dual-audience axis from over-indexing on Klinika (medical_pl) and DWF (legal_pl) personas. SE-1 must work across categories (dev tools, payments, AI safety, e-commerce, services, marketplace). The diverse seven exemplars in §3 are a deliberate breadth signal.

---

## §9 Open Questions

1. **Above-fold viewport definition under responsive layout.** "Visible without scroll" is mobile-screen-dependent. Does the judge see a desktop screenshot, a mobile screenshot, or both? If both, does it score the worse of the two or the mean? Suggests structural_gate captures both viewports and the judge sees the desktop hero; the structural_gate validates that mobile hero satisfies the same outcome via separate verifiable check.

2. **Hero rotation / animation handling.** Heroes with rotating headlines (Vercel rotates "Build and deploy" / "Ship faster" / etc.). Does the judge see one frame, all frames, or the static fallback? Suggests structural_gate captures the first rendered frame as the canonical hero artifact.

3. **Video-hero handling.** Some heroes are an autoplaying product video as the dominant visual element. The "product surface visible" signal is satisfied by video, but the judge cannot view video. Suggests structural_gate extracts the video poster frame as the visual element the judge scores.

4. **Localized hero handling.** Klinika's hero is in Polish. The judge needs to evaluate hero outcome quality in Polish, which raises calibration questions — is the panel reliably scoring non-English heroes? Suggests the calibration set includes ~10 non-English fixtures and JR labels them.

5. **A/B-test fixture variants.** Real landing pages run A/B tests of hero copy. A site_engine fixture may render version A while the canonical site shows version B. Boundary unclear. Suggests structural_gate freezes the fixture-rendered hero as the canonical artifact and does not attempt to reconcile with the live site.

6. **Five-second test calibration with synthetic judges.** The CXL test is operationalized via human user-testing. Synthetic LLM judges have no five-second budget — they see the full artifact. Does the judge artifically constrain itself to "what's in the viewport in the first 5 seconds"? Suggests the structural_gate marks the above-fold HTML region explicitly, and the judge sees that region distinguished from below-fold, so the CoT Step 2 "walk the visible hero block" is operationalizable.

7. **SE-1 calibration on AI-generated landing pages.** Easy to synthesize via "Claude, write me a landing page hero for [one-line product description]." Should the calibration set deliberately include 10–20 synthesized AI hero fixtures (as worst-case anchor examples) plus 10–20 real AI-generated B2B SaaS landing pages from the wild, to measure the judge's ability to catch the convergence template?

---

## §10 Citations

**Frameworks and practitioner work (named here for the human researcher; NOT in rubric prose).**

- Peep Laja / CXL — Hero audit framework, five-second test, six diagnostic questions. CXL conversion-research curriculum and public CXL Institute teardown corpus.
- April Dunford — *Obviously Awesome* (2019) and *Sales Pitch* (2023). Five positioning elements; competitive-alternative including "do nothing."
- Brian Balfour — positioning-first growth model; reframe of "positioning → product → market → model → channel."
- Harry Dry — Marketing Examples teardown corpus. Diagnostic vocabulary: throat-clearing, manifesto-lead, feature dump, logo-walled, claim inflation.
- Julian Shapiro — landing-page CRO writing; form-field cost rule (~10% completion drop per required field).
- Animalz — content-strategy / B2B distillation work; the "what was tried before, why it failed, what changed, what result" testimonial frame.
- Wynter — user-testing pattern library; CTA-count → click-rate empirical data.
- Pencil Pages — B2B teardown corpus; "social proof above the fold" empirical observation across 34 audited heroes.
- Aggarwal et al. (KDD 2024) — "GEO: Generative Engine Optimization" arXiv:2311.09735. Evidence-injection methods (quotes, stats, citations) at +28–40% visibility lift. (Relevant for hero passages that double as AI-citation passages.)
- Profound 10K-passage study (2025) — passage citation rates for 40–75-word self-contained blocks at 3.1× and tables at 4.2×.
- Yext 17.2M-citation analysis (2025) — entity-stability and citation-shape signals.
- Cyrus Shepard / Zyppy meta-analysis (2025) — 54 ranking-factor experiments for AEO/GEO.
- Ahrefs Q1 2026 — 12% AI-citation overlap with Google top-10 (citation diverges from ranking).
- Search Engine Land 8K-citation study — 44% of AI Overview citations from current-year content.
- Forrester 2026 — AI-buyer-validation research.

**Real-world hero exemplars cited with URLs.**

- https://linear.app
- https://vercel.com
- https://stripe.com
- https://anthropic.com
- https://modal.com
- https://posthog.com
- https://cal.com

**Project incidents referenced.**

- `c76f051` — Phase 4 rollback; feature-checking pathology in CI / MON judges that this deliverable's §6 explicitly designs around.
- `698e658` — the rolled-back Phase 4 prose.
- Handoff `docs/handoffs/2026-05-18-judge-design-step1-site-engine.md` — parent spec.
- Research `docs/research/2026-05-18-judges-domain-site-engine.md` — sibling dual-audience research; this deliverable deepens only the hero-axis half.

---

## Verification — conforms to design guide?

- §3 binary + 0.5 unknown: SE-1 stays binary; this research does not introduce intermediate scoring. ✓
- §4 outcome question + behavioral anchors + hedged examples: §6 explicitly preserves SE-1's outcome-shape. ✓
- §5 ≤5 criteria: this deliverable deepens one of the existing 5 criteria; does not add a criterion. ✓
- §6 structured CoT per criterion: existing SE-1 CoT preserved; deepening feeds Step 2 implicitly via calibration. ✓
- §7 reference-free: example anchors hedged "do not optimize toward this"; rotation of exemplar across generations recommended (§8 rec 2). ✓
- §11 Goodhart-resistance: §4 explicitly addresses the "We help X do Y" convergence as the primary Goodhart attack on SE-1; §8 rec 3 prescribes convergence-template prevalence as a leading indicator. ✓
- §12 anti-patterns: no framework names in proposed rubric prose; no anti-gaming clauses; no feature-checking enumeration in rubric prose (§6 explicitly defends against). ✓

---

## Word count

~3,200 words excluding frontmatter and verification section.
